"""
github_service.py
=================
يتعامل مع GitHub API لجلب الكود من الـ public repos.

التعديلات:
- ThreadPoolExecutor لجلب الملفات بالتوازي (10 threads)
- فلترة الملفات الأكبر من 500KB
- timeouts مرفوعة لكل العمليات
- [جديد] معالجة truncated tree للـ repos الكبيرة
  → لما tree?recursive=1 يرجع truncated:true
  → ننتقل لـ Contents API ونمشي على المجلدات recursively
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
    '.py':   'python',
    '.java': 'java',
    '.js':   'javascript',
    '.ts':   'typescript',
    '.cs':   'csharp',
    '.cpp':  'cpp',
    '.c':    'c',
    '.rb':   'ruby',
    '.go':   'go',
    '.kt':   'kotlin',
}

GITHUB_API = 'https://api.github.com'

MAX_FILE_SIZE_BYTES = 500 * 1024   # 500 KB
MAX_WORKERS        = 10
REQUEST_TIMEOUT    = 60
TREE_TIMEOUT       = 60


class GitHubService:

    def __init__(self, token: str = None):
        self.session = requests.Session()
        self.session.verify = False
        if token:
            self.session.headers['Authorization'] = f'token {token}'
        self.session.headers['Accept'] = 'application/vnd.github.v3+json'

    # ──────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────

    def get_latest_commit_sha(self, repo_url: str, branch: str) -> str:
        owner, repo = self._parse_repo_url(repo_url)
        url = f"{GITHUB_API}/repos/{owner}/{repo}/commits/{branch}"
        try:
            r = self.session.get(url, timeout=REQUEST_TIMEOUT, verify=False)
            r.raise_for_status()
            return r.json()['sha']
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get latest commit from GitHub: {str(e)}")

    def get_all_files(self, repo_url: str, branch: str) -> List[Tuple[str, str, str]]:
        """
        يجيب كل الملفات المدعومة من الـ repo.

        الاستراتيجية:
        1. جرّب Tree API (request واحد سريع)
        2. لو الـ tree رجع truncated=True → انتقل لـ Contents API
           (تمشي على المجلدات recursively)
        3. جلب المحتوى بالتوازي عبر ThreadPoolExecutor

        Returns:
            List of (filepath, content, file_type)
        """
        owner, repo = self._parse_repo_url(repo_url)
        logger.info(f"[GITHUB] Fetching all files from {owner}/{repo} branch={branch}")

        # ── المحاولة الأولى: Tree API ──────────────────────────────────────
        tree_items, truncated = self._fetch_tree(owner, repo, branch)

        if truncated:
            # ── الـ repo كبير جداً — ننتقل لـ Contents API ─────────────────
            logger.warning(
                f"[GITHUB] Tree API returned truncated=True for {owner}/{repo}. "
                "Falling back to Contents API (recursive directory walk)."
            )
            tree_items = self._fetch_all_blobs_via_contents(owner, repo, branch)

        # ── فلترة الملفات المدعومة وتجاهل الكبيرة ─────────────────────────
        candidates  = []
        skipped_ext = 0
        skipped_big = 0

        for item in tree_items:
            filepath = item['path']
            ext      = self._get_extension(filepath)

            if ext not in EXTENSION_MAP:
                skipped_ext += 1
                continue

            file_size = item.get('size', 0)
            if file_size > MAX_FILE_SIZE_BYTES:
                logger.info(
                    f"[GITHUB] Skipping large file: {filepath} "
                    f"({file_size / 1024:.1f} KB)"
                )
                skipped_big += 1
                continue

            candidates.append({
                'filepath':  filepath,
                'blob_url':  item.get('url', ''),
                'raw_url':   f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{filepath}",
                'file_type': EXTENSION_MAP[ext],
            })

        logger.info(
            f"[GITHUB] Candidates: {len(candidates)} files "
            f"(skipped {skipped_ext} unsupported, {skipped_big} too large)"
        )

        if not candidates:
            return []

        return self._fetch_contents_parallel(candidates)

    def get_changed_files(
        self,
        repo_url: str,
        branch: str,
        old_sha: str,
        new_sha: str,
    ) -> List[Tuple[str, str, str]]:
        """
        يجيب الملفات اللي تغيّرت بين commitين.
        يجلب المحتوى بالتوازي.
        """
        owner, repo = self._parse_repo_url(repo_url)
        logger.info(f"[GITHUB] Changed files {old_sha[:7]}...{new_sha[:7]}")

        url = f"{GITHUB_API}/repos/{owner}/{repo}/compare/{old_sha}...{new_sha}"
        try:
            r = self.session.get(url, timeout=REQUEST_TIMEOUT, verify=False)
            r.raise_for_status()
            files = r.json().get('files', [])
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to compare commits: {str(e)}")

        candidates = []
        for file_info in files:
            if file_info.get('status') == 'removed':
                continue
            filepath = file_info.get('filename', '')
            ext      = self._get_extension(filepath)
            if ext not in EXTENSION_MAP:
                continue
            candidates.append({
                'filepath':  filepath,
                'blob_url':  '',
                'raw_url':   f"https://raw.githubusercontent.com/{owner}/{repo}/{new_sha}/{filepath}",
                'file_type': EXTENSION_MAP[ext],
            })

        if not candidates:
            return []

        return self._fetch_contents_parallel(candidates)

    # ──────────────────────────────────────────────────────────────────────
    # Tree fetching
    # ──────────────────────────────────────────────────────────────────────

    def _fetch_tree(self, owner: str, repo: str, branch: str) -> Tuple[list, bool]:
        """
        يجيب الـ git tree كاملاً.
        يرجع (items, truncated).
        """
        url = f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        try:
            r = self.session.get(url, timeout=TREE_TIMEOUT, verify=False)
            r.raise_for_status()
            data      = r.json()
            tree      = data.get('tree', [])
            truncated = data.get('truncated', False)
            logger.info(f"[GITHUB] Tree API: {len(tree)} items, truncated={truncated}")
            return tree, truncated
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch repo tree: {str(e)}")

    def _fetch_all_blobs_via_contents(
        self, owner: str, repo: str, branch: str
    ) -> List[dict]:
        """
        Fallback للـ repos الكبيرة (truncated=True).

        يمشي على المجلدات recursively عبر Contents API
        ويجمع كل الـ blobs (الملفات).

        Returns:
            List of dicts بنفس شكل tree items:
            {'path': ..., 'type': 'blob', 'size': ..., 'url': ...}
        """
        logger.info(f"[GITHUB] Starting recursive Contents API walk for {owner}/{repo}")

        all_blobs  = []
        dirs_queue = ['']     # ابدأ من الـ root
        visited    = set()

        while dirs_queue:
            current_dir = dirs_queue.pop(0)

            if current_dir in visited:
                continue
            visited.add(current_dir)

            items = self._list_contents(owner, repo, branch, current_dir)

            for item in items:
                item_type = item.get('type')
                item_path = item.get('path', '')

                if item_type == 'file':
                    all_blobs.append({
                        'path': item_path,
                        'type': 'blob',
                        'size': item.get('size', 0),
                        'url':  item.get('url', ''),
                    })

                elif item_type == 'dir':
                    if item_path not in visited:
                        dirs_queue.append(item_path)

                # symlinks → تجاهل

        logger.info(
            f"[GITHUB] Contents API walk complete: {len(all_blobs)} blobs, "
            f"{len(visited)} directories scanned"
        )
        return all_blobs

    def _list_contents(
        self, owner: str, repo: str, branch: str, path: str
    ) -> List[dict]:
        """
        يجيب محتويات مجلد واحد عبر Contents API.
        يرجع list فارغة لو صار أي خطأ.
        """
        if path:
            url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}?ref={branch}"
        else:
            url = f"{GITHUB_API}/repos/{owner}/{repo}/contents?ref={branch}"

        try:
            r = self.session.get(url, timeout=REQUEST_TIMEOUT, verify=False)
            if r.status_code == 404:
                return []
            r.raise_for_status()
            data = r.json()
            return data if isinstance(data, list) else [data]
        except Exception as e:
            logger.warning(f"[GITHUB] Failed to list contents of '{path}': {e}")
            return []

    # ──────────────────────────────────────────────────────────────────────
    # Parallel content fetching
    # ──────────────────────────────────────────────────────────────────────

    def _fetch_contents_parallel(
        self, candidates: List[dict]
    ) -> List[Tuple[str, str, str]]:
        """
        يجيب محتوى الملفات بالتوازي.
        يجرّب raw_url أولاً (أسرع)، ويرجع لـ blob_url كـ fallback.
        """
        result = []

        def fetch_one(info: dict) -> Optional[Tuple[str, str, str]]:
            content = self._fetch_raw(info['raw_url'])
            if content is None and info.get('blob_url'):
                content = self._fetch_blob(info['blob_url'])
            if content:
                return (info['filepath'], content, info['file_type'])
            return None

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(fetch_one, c): c['filepath']
                for c in candidates
            }
            for future in as_completed(futures):
                filepath = futures[future]
                try:
                    res = future.result()
                    if res:
                        result.append(res)
                except Exception as e:
                    logger.warning(f"[GITHUB] Failed to fetch {filepath}: {e}")

        logger.info(f"[GITHUB] Fetched {len(result)}/{len(candidates)} files successfully")
        return result

    # ──────────────────────────────────────────────────────────────────────
    # Low-level fetchers
    # ──────────────────────────────────────────────────────────────────────

    def _fetch_raw(self, url: str) -> Optional[str]:
        """يجيب محتوى ملف من raw URL."""
        try:
            r = self.session.get(url, timeout=REQUEST_TIMEOUT, verify=False)
            r.raise_for_status()
            return r.text
        except Exception:
            return None

    def _fetch_blob(self, blob_url: str) -> Optional[str]:
        """يجيب محتوى ملف من blob URL (base64 encoded)."""
        try:
            r = self.session.get(blob_url, timeout=REQUEST_TIMEOUT, verify=False)
            r.raise_for_status()
            data        = r.json()
            content_b64 = data.get('content', '').replace('\n', '')
            return base64.b64decode(content_b64).decode('utf-8', errors='ignore')
        except Exception:
            return None

    # ──────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────

    def _parse_repo_url(self, repo_url: str) -> Tuple[str, str]:
        url = repo_url.rstrip('/')
        if url.endswith('.git'):
            url = url[:-4]
        parts = url.split('/')
        if len(parts) < 2:
            raise ValueError(f"Invalid GitHub URL: {repo_url}")
        return parts[-2], parts[-1]

    def _get_extension(self, filepath: str) -> str:
        return os.path.splitext(filepath)[1].lower()