"""
github_service.py
=================
يتعامل مع GitHub API لجلب الكود من الـ public repos.
يستخدم curl عبر subprocess لتجنب مشاكل SSL في Python.
"""

import json
import logging
import base64
import subprocess
import os
from typing import List, Tuple, Optional
import requests


logger = logging.getLogger(__name__)

# امتدادات الملفات المدعومة
EXTENSION_MAP = {
    '.py': 'python',
    '.java': 'java',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.cs': 'csharp',
    '.cpp': 'cpp',
    '.c': 'c',
    '.rb': 'ruby',
    '.go': 'go',
    '.kt': 'kotlin',
}

GITHUB_API = 'https://api.github.com'


class GitHubService:

    def __init__(self, token: str = None):
        self.token = token

    def _curl_get(self, url: str) -> dict:
        """يستخدم curl لجلب البيانات من GitHub API."""
        cmd = ['curl', '-s', '--max-time', '30', '-L']
        if self.token:
            cmd += ['-H', f'Authorization: token {self.token}']
        cmd += ['-H', 'Accept: application/vnd.github.v3+json']
        cmd.append(url)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
            if result.returncode != 0:
                raise Exception(f"curl failed: {result.stderr}")
            return json.loads(result.stdout)
        except subprocess.TimeoutExpired:
            raise Exception("GitHub API request timed out")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response: {str(e)}")

    def _curl_get_raw(self, url: str) -> str:
        """يجيب محتوى raw من URL."""
        cmd = ['curl', '-s', '--max-time', '30', '-L']
        if self.token:
            cmd += ['-H', f'Authorization: token {self.token}']
        cmd.append(url)

        try:
            result = subprocess.run(cmd, capture_output=True, timeout=35)
            if result.returncode != 0:
                return None
            return result.stdout.decode('utf-8', errors='ignore')
        except subprocess.TimeoutExpired:
            return None

    def _parse_repo_url(self, repo_url: str) -> Tuple[str, str]:
        url = repo_url.rstrip('/')
        if url.endswith('.git'):
            url = url[:-4]
        parts = url.split('/')
        if len(parts) < 2:
            raise ValueError(f"Invalid GitHub URL: {repo_url}")
        return parts[-2], parts[-1]

    def get_latest_commit_sha(self, repo_url: str, branch: str) -> str:
        owner, repo = self._parse_repo_url(repo_url)
        url = f"{GITHUB_API}/repos/{owner}/{repo}/commits/{branch}"
        data = self._curl_get(url)
        if 'sha' not in data:
            raise Exception(data.get('message', 'Failed to get commit SHA'))
        return data['sha']

    def get_all_files(self, repo_url: str, branch: str) -> List[Tuple[str, str, str]]:
        owner, repo = self._parse_repo_url(repo_url)
        logger.info(f"[GITHUB] Fetching all files from {owner}/{repo} branch: {branch}")

        url = f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        data = self._curl_get(url)
        tree = data.get('tree', [])

        supported_files = []
        for item in tree:
            if item['type'] != 'blob':
                continue
            filepath = item['path']
            ext = os.path.splitext(filepath)[1].lower()
            if ext not in EXTENSION_MAP:
                continue
            supported_files.append((filepath, EXTENSION_MAP[ext]))

        logger.info(f"[GITHUB] Found {len(supported_files)} supported files")

        result = []
        for filepath, file_type in supported_files:
            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{filepath}"
            content = self._curl_get_raw(raw_url)
            if content:
                result.append((filepath, content, file_type))

        return result

    def get_changed_files(
        self, repo_url: str, branch: str,
        old_sha: str, new_sha: str
    ) -> List[Tuple[str, str, str]]:
        owner, repo = self._parse_repo_url(repo_url)
        logger.info(f"[GITHUB] Fetching changed files between {old_sha[:7]}...{new_sha[:7]}")

        url = f"{GITHUB_API}/repos/{owner}/{repo}/compare/{old_sha}...{new_sha}"
        data = self._curl_get(url)
        files = data.get('files', [])

        result = []
        for file_info in files:
            if file_info.get('status') == 'removed':
                continue
            filepath = file_info.get('filename', '')
            ext = os.path.splitext(filepath)[1].lower()
            if ext not in EXTENSION_MAP:
                continue
            file_type = EXTENSION_MAP[ext]
            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{new_sha}/{filepath}"
            content = self._curl_get_raw(raw_url)
            if content:
                result.append((filepath, content, file_type))

        logger.info(f"[GITHUB] Found {len(result)} changed files")
        return result


# امتدادات الملفات المدعومة
EXTENSION_MAP = {
    '.py': 'python',
    '.java': 'java',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.cs': 'csharp',
    '.cpp': 'cpp',
    '.c': 'c',
    '.rb': 'ruby',
    '.go': 'go',
    '.kt': 'kotlin',
}

GITHUB_API = 'https://api.github.com'


class GitHubService:
    """
    يتعامل مع GitHub API.
    يدعم الـ public repos بدون token وبمعه.
    """

    def __init__(self, token: str = None):
        self.session = requests.Session()
        self.session.verify = False
        if token:
            self.session.headers['Authorization'] = f'token {token}'
        self.headers = self.session.headers

    def _parse_repo_url(self, repo_url: str) -> Tuple[str, str]:
        """
        يحوّل رابط الـ repo لـ owner/repo_name.
        مثال: https://github.com/user/repo → ('user', 'repo')
        """
        # إزالة trailing slash
        url = repo_url.rstrip('/')
        # إزالة .git إذا موجود
        if url.endswith('.git'):
            url = url[:-4]
        # استخراج owner/repo
        parts = url.split('/')
        if len(parts) < 2:
            raise ValueError(f"Invalid GitHub URL: {repo_url}")
        return parts[-2], parts[-1]

    def get_latest_commit_sha(self, repo_url: str, branch: str) -> str:
        """
        يجيب آخر commit SHA للـ branch.
        """
        owner, repo = self._parse_repo_url(repo_url)
        url = f"{GITHUB_API}/repos/{owner}/{repo}/commits/{branch}"

        try:
            response = self.session.get(url, headers=self.headers, timeout=30, verify=False)
            response.raise_for_status()
            return response.json()['sha']
        except requests.exceptions.RequestException as e:
            logger.error(f"[GITHUB] Error getting latest commit: {e}")
            raise Exception(f"Failed to get latest commit from GitHub: {str(e)}")

    def get_all_files(self, repo_url: str, branch: str) -> List[Tuple[str, str, str]]:
        """
        يجيب كل الملفات المدعومة من الـ repo.

        Returns:
            List of (filepath, content, file_type)
        """
        owner, repo = self._parse_repo_url(repo_url)
        logger.info(f"[GITHUB] Fetching all files from {owner}/{repo} branch: {branch}")

        # جلب الـ tree كاملاً
        url = f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        try:
            response = self.session.get(url, headers=self.headers, timeout=30, verify=False)
            response.raise_for_status()
            tree = response.json().get('tree', [])
        except requests.exceptions.RequestException as e:
            logger.error(f"[GITHUB] Error fetching tree: {e}")
            raise Exception(f"Failed to fetch repo tree: {str(e)}")

        # فلترة الملفات المدعومة فقط
        supported_files = []
        for item in tree:
            if item['type'] != 'blob':
                continue
            filepath = item['path']
            ext = self._get_extension(filepath)
            if ext not in EXTENSION_MAP:
                continue
            supported_files.append((filepath, item['url'], EXTENSION_MAP[ext]))

        logger.info(f"[GITHUB] Found {len(supported_files)} supported files")

        # جلب محتوى كل ملف
        result = []
        for filepath, blob_url, file_type in supported_files:
            content = self._fetch_file_content(blob_url)
            if content:
                result.append((filepath, content, file_type))

        return result

    def get_changed_files(
        self, repo_url: str, branch: str,
        old_sha: str, new_sha: str
    ) -> List[Tuple[str, str, str]]:
        """
        يجيب الملفات اللي تغيّرت بين commitين.

        Returns:
            List of (filepath, content, file_type)
        """
        owner, repo = self._parse_repo_url(repo_url)
        logger.info(f"[GITHUB] Fetching changed files between {old_sha[:7]}...{new_sha[:7]}")

        # مقارنة الـ commits
        url = f"{GITHUB_API}/repos/{owner}/{repo}/compare/{old_sha}...{new_sha}"
        try:
            response = self.session.get(url, timeout=30, verify=False)
            response.raise_for_status()
            files = response.json().get('files', [])
        except requests.exceptions.RequestException as e:
            logger.error(f"[GITHUB] Error comparing commits: {e}")
            raise Exception(f"Failed to compare commits: {str(e)}")

        # فلترة الملفات المدعومة المضافة أو المعدّلة
        result = []
        for file_info in files:
            status = file_info.get('status')
            if status == 'removed':
                continue  # تجاهل الملفات المحذوفة

            filepath = file_info.get('filename', '')
            ext = self._get_extension(filepath)
            if ext not in EXTENSION_MAP:
                continue

            file_type = EXTENSION_MAP[ext]
            blob_url = file_info.get('contents_url', '')
            content = self._fetch_file_content_by_raw(
                owner, repo, new_sha, filepath
            )
            if content:
                result.append((filepath, content, file_type))

        logger.info(f"[GITHUB] Found {len(result)} changed files")
        return result

    def _fetch_file_content(self, blob_url: str) -> Optional[str]:
        """يجيب محتوى ملف من blob URL."""
        try:
            response = self.session.get(blob_url, headers=self.headers, timeout=30, verify=False)
            response.raise_for_status()
            data = response.json()
            content_b64 = data.get('content', '')
            # GitHub يرجع المحتوى بـ base64
            content = base64.b64decode(content_b64).decode('utf-8', errors='ignore')
            return content
        except Exception as e:
            logger.warning(f"[GITHUB] Failed to fetch file: {e}")
            return None

    def _fetch_file_content_by_raw(
        self, owner: str, repo: str, sha: str, filepath: str
    ) -> Optional[str]:
        """يجيب محتوى ملف من raw URL."""
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/{sha}/{filepath}"
        try:
            response = self.session.get(url, timeout=30, verify=False)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.warning(f"[GITHUB] Failed to fetch raw file {filepath}: {e}")
            return None

    def _get_extension(self, filepath: str) -> str:
        """يستخرج امتداد الملف."""
        import os
        return os.path.splitext(filepath)[1].lower()