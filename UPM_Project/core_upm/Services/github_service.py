"""
github_service.py  ← معدّل
=================
التغييرات عن النسخة القديمة:
    1. أُضيفت دالة get_latest_commit_sha() — كانت مستخدمة في github_views لكن غير موجودة
    2. أُضيفت دالة get_changed_files()     — كانت مستخدمة في github_views لكن غير موجودة
    3. عُدّل توقيع get_all_files() ليقبل repo_url كاملاً (مثل https://github.com/user/repo)
       بدل owner و repo منفصلين — لأن github_views بيمرر repo_url مباشرة
    4. أُضيفت دالة مساعدة _parse_repo_url() تحلّل الـ URL لـ owner و repo
"""

import logging
import base64
import os
from typing import List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

EXTENSION_MAP = {
    '.py':    'python',
    '.java':  'java',
    '.js':    'javascript',
    '.ts':    'typescript',
    '.cpp':   'cpp',
    '.c':     'c',
    '.h':     'c',
    '.hpp':   'cpp',
    '.cs':    'csharp',
    '.php':   'php',
    '.rb':    'ruby',
    '.go':    'go',
    '.rs':    'rust',
    '.swift': 'swift',
    '.kt':    'kotlin',
    '.scala': 'scala',
    '.html':  'html',
    '.css':   'css',
    '.sql':   'sql',
    '.sh':    'shell',
    '.json':  'json',
    '.xml':   'xml',
    '.yaml':  'yaml',
    '.yml':   'yaml',
    '.md':    'markdown',
    '.txt':   'text',
}

IGNORED_DIRS = (
    'node_modules/', '.git/', '__pycache__/',
    '.vscode/', '.idea/', 'venv/', 'env/',
    'dist/', 'build/', '.pytest_cache/',
)

IGNORED_EXTENSIONS = (
    '.pyc', '.pyo', '.pyd',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp',
    '.mp3', '.wav', '.mp4', '.avi',
    '.zip', '.tar', '.gz', '.rar',
    '.exe', '.dll', '.so', '.dylib',
)

MAX_FILE_SIZE = 500 * 1024  # 500 KB


class GitHubService:
    """خدمة للتعامل مع GitHub API"""

    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.session = requests.Session()
        if self.token:
            self.session.headers.update({'Authorization': f'token {self.token}'})
        self.session.headers.update({
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Code-Analyzer-App/1.0',
        })

    # ── دالة مساعدة ────────────────────────────────────────────────────────────
    def _parse_repo_url(self, repo_url: str) -> Tuple[str, str]:
        """
        يحلّل repo_url الكامل ويرجع (owner, repo).
        مثال: 'https://github.com/octocat/Hello-World' → ('octocat', 'Hello-World')
        """
        clean = repo_url.rstrip('/').replace('https://github.com/', '')
        parts = clean.split('/')
        if len(parts) < 2:
            raise ValueError(f"Invalid GitHub repo URL: {repo_url}")
        return parts[0], parts[1]

    # ── 1. آخر commit SHA ──────────────────────────────────────────────────────
    def get_latest_commit_sha(self, repo_url: str, branch: str = 'main') -> str:
        """
        يرجع SHA لآخر commit على الـ branch المحدد.
        مُضافة جديداً — كانت مستخدمة في github_views لكن غير موجودة.
        """
        owner, repo = self._parse_repo_url(repo_url)
        url = f'https://api.github.com/repos/{owner}/{repo}/commits/{branch}'
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            sha = response.json().get('sha', '')
            if not sha:
                raise ValueError("Could not retrieve commit SHA from GitHub.")
            logger.info(f"[GITHUB] Latest SHA for {repo_url}@{branch}: {sha[:7]}")
            return sha
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                raise ValueError(f"Branch '{branch}' not found in repo '{repo_url}'.")
            raise ValueError(f"GitHub API error: {str(e)}")
        except Exception as e:
            logger.error(f"[GITHUB] get_latest_commit_sha error: {e}")
            raise

    # ── 2. الملفات المتغيرة بين commitين ───────────────────────────────────────
    def get_changed_files(
        self,
        repo_url: str,
        branch: str,
        old_sha: str,
        new_sha: str,
    ) -> List[Tuple[str, str, str]]:
        """
        يرجع الملفات المتغيرة بين old_sha و new_sha.
        يرجع: List of (filepath, content, file_type)
        مُضافة جديداً — كانت مستخدمة في github_views لكن غير موجودة.
        """
        owner, repo = self._parse_repo_url(repo_url)

        # لو ما في old_sha (أول مرة) → رجع كل الملفات
        if not old_sha:
            logger.info(f"[GITHUB] No old SHA — fetching all files")
            return self.get_all_files(repo_url, branch)

        # جلب الـ diff بين الـ SHAين
        url = f'https://api.github.com/repos/{owner}/{repo}/compare/{old_sha}...{new_sha}'
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            compare_data = response.json()
        except Exception as e:
            logger.error(f"[GITHUB] get_changed_files compare error: {e}")
            raise ValueError(f"Failed to compare commits: {str(e)}")

        changed = compare_data.get('files', [])
        if not changed:
            logger.info(f"[GITHUB] No changed files between {old_sha[:7]} and {new_sha[:7]}")
            return []

        # فلترة الملفات المحذوفة + غير المدعومة + الكبيرة
        files_to_fetch = []
        for f in changed:
            filepath = f.get('filename', '')
            file_status = f.get('status', '')
            if file_status == 'removed':
                continue
            if not self._should_include_file(filepath):
                continue
            if f.get('size', 0) > MAX_FILE_SIZE:
                continue
            files_to_fetch.append(filepath)

        if not files_to_fetch:
            return []

        logger.info(f"[GITHUB] {len(files_to_fetch)} changed files to fetch")

        # جلب محتوى كل ملف بالتوازي
        results = []

        def fetch_one(filepath):
            content = self._get_file_content(owner, repo, filepath, new_sha)
            if content:
                ext = os.path.splitext(filepath)[1].lower()
                file_type = EXTENSION_MAP.get(ext, 'text')
                return (filepath, content, file_type)
            return None

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(fetch_one, fp): fp for fp in files_to_fetch}
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=60)
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.warning(f"[GITHUB] Failed to fetch {futures[future]}: {e}")

        logger.info(f"[GITHUB] get_changed_files done — {len(results)} files")
        return results

    # ── 3. كل ملفات الـ repo ───────────────────────────────────────────────────
    def get_all_files(self, repo_url: str, branch: str = 'main') -> List[Tuple[str, str, str]]:
        """
        يجيب كل الملفات من الـ repo.
        يرجع: List of (filepath, content, file_type)

        التغيير: يقبل الآن repo_url كامل (https://github.com/user/repo)
        بدل owner و repo منفصلين — لأن github_views بيمرره هيك.
        """
        owner, repo = self._parse_repo_url(repo_url)

        logger.info(f"[GITHUB] Fetching all files from {owner}/{repo}@{branch}")

        # أولاً: جرب Git Trees API (أسرع للـ repos الكبيرة)
        tree_files = self._get_files_via_tree_api(owner, repo, branch)

        if tree_files is not None:
            logger.info(f"[GITHUB] Tree API returned {len(tree_files)} files")
            return self._download_files(owner, repo, tree_files, branch)

        # fallback: Contents API (للـ repos اللي tree مشانها truncated)
        logger.info(f"[GITHUB] Tree API truncated — falling back to Contents API")
        return self._get_files_via_contents_api(owner, repo, branch)

    def _get_files_via_tree_api(
        self, owner: str, repo: str, branch: str
    ) -> Optional[List[str]]:
        """
        يجيب قائمة الـ filepaths عبر Git Trees API.
        يرجع None لو كان الـ tree مـ truncated (repo كبير جداً).
        """
        url = f'https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1'
        try:
            response = self.session.get(url, timeout=60)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.error(f"[GITHUB] Tree API error: {e}")
            return None

        if data.get('truncated'):
            return None

        filepaths = []
        for item in data.get('tree', []):
            if item.get('type') != 'blob':
                continue
            filepath = item.get('path', '')
            size = item.get('size', 0)
            if size > MAX_FILE_SIZE:
                continue
            if not self._should_include_file(filepath):
                continue
            filepaths.append(filepath)

        return filepaths

    def _get_files_via_contents_api(
        self, owner: str, repo: str, branch: str, path: str = ''
    ) -> List[Tuple[str, str, str]]:
        """يمشي على المجلدات recursively عبر Contents API."""
        results = []
        processed = set()

        def process_dir(dir_path):
            if dir_path in processed:
                return
            processed.add(dir_path)

            url = f'https://api.github.com/repos/{owner}/{repo}/contents/{dir_path}'
            params = {'ref': branch}
            try:
                r = self.session.get(url, params=params, timeout=30)
                r.raise_for_status()
                items = r.json()
                if not isinstance(items, list):
                    return
            except Exception as e:
                logger.warning(f"[GITHUB] Contents API error at {dir_path}: {e}")
                return

            for item in items:
                if item['type'] == 'file':
                    fp = item['path']
                    if item.get('size', 0) > MAX_FILE_SIZE:
                        continue
                    if self._should_include_file(fp):
                        content = self._get_file_content(owner, repo, fp, branch)
                        if content:
                            ext = os.path.splitext(fp)[1].lower()
                            results.append((fp, content, EXTENSION_MAP.get(ext, 'text')))
                elif item['type'] == 'dir':
                    process_dir(item['path'])

        process_dir(path)
        return results

    def _download_files(
        self, owner: str, repo: str, filepaths: List[str], ref: str
    ) -> List[Tuple[str, str, str]]:
        """يحمّل محتوى قائمة ملفات بالتوازي."""
        results = []

        def fetch(fp):
            content = self._get_file_content(owner, repo, fp, ref)
            if content:
                ext = os.path.splitext(fp)[1].lower()
                return (fp, content, EXTENSION_MAP.get(ext, 'text'))
            return None

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(fetch, fp): fp for fp in filepaths}
            for future in as_completed(futures):
                try:
                    r = future.result(timeout=60)
                    if r:
                        results.append(r)
                except Exception as e:
                    logger.warning(f"[GITHUB] Download error {futures[future]}: {e}")

        logger.info(f"[GITHUB] Downloaded {len(results)}/{len(filepaths)} files")
        return results

    # ── دوال مساعدة ────────────────────────────────────────────────────────────
    def _get_file_content(
        self, owner: str, repo: str, path: str, ref: str = 'main'
    ) -> Optional[str]:
        """يجيب محتوى ملف واحد من GitHub."""
        url = f'https://api.github.com/repos/{owner}/{repo}/contents/{path}'
        try:
            r = self.session.get(url, params={'ref': ref}, timeout=30)
            r.raise_for_status()
            data = r.json()
            if data.get('encoding') == 'base64':
                return base64.b64decode(data['content']).decode('utf-8', errors='ignore')
            return data.get('content', '')
        except Exception as e:
            logger.warning(f"[GITHUB] _get_file_content error {path}: {e}")
            return None

    def _should_include_file(self, filepath: str) -> bool:
        """يتحقق إذا الملف يجب تضمينه بناءً على المسار والامتداد."""
        lower = filepath.lower()
        for d in IGNORED_DIRS:
            if d in lower:
                return False
        ext = os.path.splitext(lower)[1]
        if ext in IGNORED_EXTENSIONS:
            return False
        return True
    