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
    '.cpp':  'cpp',
    '.c':    'c',
    '.h':    'c',
    '.hpp':  'cpp',
    '.cs':   'csharp',
    '.php':  'php',
    '.rb':   'ruby',
    '.go':   'go',
    '.rs':   'rust',
    '.swift': 'swift',
    '.kt':   'kotlin',
    '.scala': 'scala',
    '.html': 'html',
    '.css':  'css',
    '.sql':  'sql',
    '.sh':   'shell',
    '.json': 'json',
    '.xml':  'xml',
    '.yaml': 'yaml',
    '.yml':  'yaml',
    '.md':   'markdown',
    '.txt':  'text',
}

class GitHubService:
    """خدمة للتعامل مع GitHub API وجلب الكود"""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.session = requests.Session()
        if self.token:
            self.session.headers.update({'Authorization': f'token {self.token}'})
        self.session.headers.update({
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Code-Analyzer-App/1.0'
        })
    
    def get_repo_info(self, owner: str, repo: str) -> dict:
        """جلب معلومات الأساسية عن الريبو"""
        url = f'https://api.github.com/repos/{owner}/{repo}'
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching repo info: {e}")
            return {}
    
    def get_all_files(self, owner: str, repo: str, path: str = '', max_files: int = 100) -> List[dict]:
        """
        جلب كل الملفات من الريبو بشكل متكرر
        يدعم معالجة الريPOS الكبيرة اللي تسبب truncated tree
        """
        all_files = []
        processed_paths = set()
        
        def process_directory(path: str):
            """معالجة مجلد واحد وجلب محتوياته"""
            if path in processed_paths:
                return []
            
            processed_paths.add(path)
            files_in_dir = []
            
            try:
                # جلب محتويات المجلد
                url = f'https://api.github.com/repos/{owner}/{repo}/contents/{path}'
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                items = response.json()
                
                if not isinstance(items, list):
                    return []
                
                for item in items:
                    if item.get('type') == 'file':
                        # فلترة الملفات حسب الحجم والنوع
                        if item.get('size', 0) > 500 * 1024:  # 500KB
                            continue
                        
                        file_path = item.get('path', '')
                        if self._should_include_file(file_path):
                            files_in_dir.append(item)
                    
                    elif item.get('type') == 'dir':
                        # معالجة المجلدات الفرعية بشكل متوازي
                        sub_path = item.get('path', '')
                        if len(all_files) + len(files_in_dir) < max_files:
                            sub_files = process_directory(sub_path)
                            files_in_dir.extend(sub_files)
                
                return files_in_dir
                
            except Exception as e:
                logger.error(f"Error processing directory {path}: {e}")
                return []
        
        # استخدام ThreadPoolExecutor للمعالجة المتوازية
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_path = {executor.submit(process_directory, ''): ''}
            
            for future in as_completed(future_to_path):
                try:
                    files = future.result(timeout=60)
                    all_files.extend(files)
                    if len(all_files) >= max_files:
                        break
                except Exception as e:
                    logger.error(f"Error in parallel processing: {e}")
        
        return all_files[:max_files]
    
    def _should_include_file(self, file_path: str) -> bool:
        """تحديد ما إذا كان يجب تضمين الملف"""
        # استبعاد الملفات والمجلدات غير المرغوبة
        exclude_patterns = [
            'node_modules/', '.git/', '__pycache__/', 
            '.vscode/', '.idea/', 'venv/', 'env/',
            'dist/', 'build/', '.pytest_cache/',
            '*.pyc', '*.pyo', '*.pyd',
            '*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp',
            '*.mp3', '*.wav', '*.mp4', '*.avi',
            '*.zip', '*.tar', '*.gz', '*.rar',
            '*.exe', '*.dll', '*.so', '*.dylib'
        ]
        
        file_path_lower = file_path.lower()
        for pattern in exclude_patterns:
            if pattern in file_path_lower or file_path_lower.endswith(pattern.replace('*', '')):
                return False
        
        return True
    
    def get_file_content(self, owner: str, repo: str, path: str) -> Optional[str]:
        """جلب محتوى ملف معين"""
        url = f'https://api.github.com/repos/{owner}/{repo}/contents/{path}'
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get('encoding') == 'base64':
                content = base64.b64decode(data.get('content', '')).decode('utf-8', errors='ignore')
                return content
            else:
                return data.get('content', '')
                
        except Exception as e:
            logger.error(f"Error fetching file content for {path}: {e}")
            return None
    
    def get_file_type(self, filename: str) -> str:
        """تحديد نوع الملف من الامتداد"""
        _, ext = os.path.splitext(filename.lower())
        return EXTENSION_MAP.get(ext, 'text')
    
    def download_files_parallel(self, owner: str, repo: str, files: List[dict]) -> List[Tuple[str, str, str]]:
        """
        تحميل الملفات بشكل متوازي
        Returns: List of (file_path, file_content, file_type)
        """
        results = []
        
        def download_file(file_info):
            file_path = file_info.get('path', '')
            content = self.get_file_content(owner, repo, file_path)
            if content:
                file_type = self.get_file_type(file_path)
                return (file_path, content, file_type)
            return None
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_file = {executor.submit(download_file, file_info): file_info for file_info in files}
            
            for future in as_completed(future_to_file):
                try:
                    result = future.result(timeout=60)
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.error(f"Error downloading file: {e}")
        
        return results
