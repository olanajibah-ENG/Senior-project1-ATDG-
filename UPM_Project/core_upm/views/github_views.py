"""
github_views.py
===============
Endpoints لربط المشروع بـ GitHub repo.

الـ endpoints:
    POST /projects/<id>/github/connect/  — ربط repo جديد
    POST /projects/<id>/github/sync/     — مزامنة يدوية
    POST /projects/<id>/github/webhook/  — استقبال GitHub webhook

التعديلات:
- رفع thread.join timeout من 60 → 600 ثانية (connect)
- رفع sha_thread.join timeout من 30 → 60 ثانية
- رفع AI service timeout من 300 → 600 ثانية
- إضافة GITHUB_MAX_FILES للتحكم بعدد الملفات (اختياري للتحكم بالـ testing)
"""

import requests
import logging
import threading
import os
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from core_upm.permissions import IsDeveloperRole
from core_upm.models.project import Project
from core_upm.models.repository import Repository
from core_upm.models.folder import Folder
from core_upm.models.version import Version
from core_upm.models.artifact import CodeArtifact
from core_upm.services.github_service import GitHubService

logger = logging.getLogger(__name__)

AI_FOLDER_UPLOAD_URL = 'http://ai_django_app:8000/api/analysis/upload-folder/'


# ── التعديل 1: Timeouts مرفوعة ─────────────────────────────────────────────
SHA_THREAD_TIMEOUT   = 60    # ثانية — كان 30
FILES_THREAD_TIMEOUT = 600   # ثانية — كان 60  (10 دقائق للـ repos الكبيرة)
AI_SERVICE_TIMEOUT   = 600   # ثانية — كان 300 (10 دقائق لإرسال الملفات للـ AI)

# ── التعديل 2: حد أقصى للملفات (اختياري) ─────────────────────────────────
# اتركيه None لجلب كل الملفات، أو حديه بـ env variable للتجربة
# مثال: GITHUB_MAX_FILES=100 لجلب أول 100 ملف بس
GITHUB_MAX_FILES = int(os.environ.get('GITHUB_MAX_FILES', 0)) or None


@method_decorator(csrf_exempt, name='dispatch')
class GitHubConnectView(APIView):
    """
    POST /projects/<project_id>/github/connect/

    يربط مشروع بـ GitHub repo ويجيب الكود مباشرة.

    Body (JSON):
        {
            "repo_url": "https://github.com/user/repo",
            "branch": "main",
            "github_token": "ghp_..." (اختياري)
        }

    Response:
        {
            "repo_id": "uuid",
            "repo_url": "...",
            "branch": "main",
            "last_commit_sha": "abc123",
            "files_synced": 5,
            "version_number": 1
        }
    """
    permission_classes = [IsAuthenticated,IsDeveloperRole]

    def post(self, request, project_id):
        # 1. جلب المشروع والتحقق من الملكية
        project = get_object_or_404(Project, project_id=project_id)
        if project.user != request.user:
            return Response({"error": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        # 2. التحقق من البيانات
        repo_url     = request.data.get('repo_url', '').strip()
        branch       = request.data.get('branch', 'main').strip()
        github_token = request.data.get('github_token', '').strip() or None

        if not repo_url:
            return Response({"error": "repo_url is required."}, status=status.HTTP_400_BAD_REQUEST)

        if not repo_url.startswith('https://github.com/'):
            return Response(
                {"error": "Only GitHub public repos are supported."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        github = GitHubService(token=github_token)

        # 3. جلب آخر commit SHA
        sha_container = {'sha': None, 'error': None}

        def fetch_sha():
            try:
                sha_container['sha'] = github.get_latest_commit_sha(repo_url, branch)
            except Exception as e:
                sha_container['error'] = str(e)

        sha_thread = threading.Thread(target=fetch_sha)
        sha_thread.start()
        # ── التعديل 3: timeout مرفوع من 30 → 60 ──────────────────────────
        sha_thread.join(timeout=SHA_THREAD_TIMEOUT)

        if sha_container['error']:
            return Response({"error": sha_container['error']}, status=status.HTTP_400_BAD_REQUEST)
        if sha_container['sha'] is None:
            return Response(
                {"error": "Timeout connecting to GitHub. Try again or use a token."},
                status=status.HTTP_504_GATEWAY_TIMEOUT,
            )

        latest_sha = sha_container['sha']

        # 4. إنشاء أو تحديث Repository في MySQL
        repo_name = repo_url.rstrip('/').split('/')[-1]
        repo, created = Repository.objects.update_or_create(
            project=project,
            repo_url=repo_url,
            defaults={
                'repo_name':       repo_name,
                'branch':          branch,
                'last_commit_sha': latest_sha,
                'source_type':     'github',
            },
        )

        # 5. جلب كل الملفات من GitHub
        result_container = {'files': None, 'error': None}

        def fetch_files():
            try:
                result_container['files'] = github.get_all_files(repo_url, branch)
            except Exception as e:
                result_container['error'] = str(e)

        thread = threading.Thread(target=fetch_files)
        thread.start()
        # ── التعديل 4: timeout مرفوع من 60 → 600 ─────────────────────────
        thread.join(timeout=FILES_THREAD_TIMEOUT)

        if result_container['error']:
            return Response({"error": result_container['error']}, status=status.HTTP_400_BAD_REQUEST)

        if result_container['files'] is None:
            return Response(
                {"error": "Timeout fetching files from GitHub. The repo may be too large — try a smaller branch or use GITHUB_MAX_FILES."},
                status=status.HTTP_504_GATEWAY_TIMEOUT,
            )

        files = result_container['files']

        if not files:
            return Response(
                {"error": "No supported files found in repo."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── التعديل 5: تقليص عدد الملفات اختيارياً ───────────────────────
        if GITHUB_MAX_FILES and len(files) > GITHUB_MAX_FILES:
            logger.info(f"[GITHUB-CONNECT] Limiting files from {len(files)} → {GITHUB_MAX_FILES}")
            files = files[:GITHUB_MAX_FILES]

        # 6. إرسال الملفات للـ AI service وحفظها في MySQL
        try:
            result = self._sync_files_to_ai(project, files, repo)
        except Exception as e:
            logger.error(f"[GITHUB-CONNECT] Sync error: {e}")
            return Response(
                {"error": f"Failed to sync files: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "repo_id":          str(repo.repo_id),
                "repo_url":         repo_url,
                "branch":           branch,
                "last_commit_sha":  latest_sha,
                "files_synced":     result['artifacts'],
                "version_number":   result['version'],
            },
            status=status.HTTP_201_CREATED,
        )

    def _sync_files_to_ai(self, project, files, repo):
        """
        يرسل الملفات للـ AI service ويحفظ في MySQL.
        يرسل على دفعات (BATCH_SIZE ملف) لتجنب IncompleteRead على الـ repos الكبيرة.
        """
        BATCH_SIZE = 50  # عدد الملفات في كل دفعة

        all_files_data  = []
        version_number  = None

        # ── تقسيم الملفات لدفعات ──────────────────────────────────────────
        batches = [files[i:i + BATCH_SIZE] for i in range(0, len(files), BATCH_SIZE)]
        logger.info(f"[GITHUB-SYNC] Sending {len(files)} files in {len(batches)} batches")

        for batch_idx, batch in enumerate(batches):
            logger.info(f"[GITHUB-SYNC] Batch {batch_idx + 1}/{len(batches)} — {len(batch)} files")

            files_to_forward = [
                ('files', (filepath, content.encode('utf-8'), 'text/plain'))
                for filepath, content, file_type in batch
            ]

            try:
                ai_response = requests.post(
                    AI_FOLDER_UPLOAD_URL,
                    data={'project_name': project.project_name},
                    files=files_to_forward,
                    headers={'Host': 'localhost'},
                    timeout=AI_SERVICE_TIMEOUT,
                )
                ai_response.raise_for_status()
                ai_data = ai_response.json()

                # احفظي الـ version_number من أول دفعة
                if version_number is None:
                    version_number = ai_data.get('version_number', 1)

                # اجمعي الملفات من كل الدفعات
                all_files_data.extend(ai_data.get('files', []))

            except requests.exceptions.ConnectionError:
                raise Exception("AI service is unavailable.")
            except requests.exceptions.Timeout:
                raise Exception(
                    f"AI service timed out on batch {batch_idx + 1}. "
                    f"Try reducing BATCH_SIZE."
                )
            except Exception as e:
                raise Exception(f"AI service error on batch {batch_idx + 1}: {str(e)}")

        logger.info(f"[GITHUB-SYNC] All batches done — {len(all_files_data)} files total")

        # ── احفظي كل الملفات المجموعة في MySQL ───────────────────────────
        combined_ai_data = {
            'files':          all_files_data,
            'version_number': version_number or 1,
        }
        return self._save_to_mysql(project, combined_ai_data, repo)

    @transaction.atomic
    def _save_to_mysql(self, project, ai_data, repo):
        """يحفظ Folder + Version + CodeArtifact في MySQL."""
        files          = ai_data.get('files', [])
        version_number = ai_data.get('version_number', 1)

        version, _ = Version.objects.get_or_create(
            project=project,
            version_number=version_number,
            defaults={'description': f'GitHub sync from {repo.repo_url}'},
        )

        folders_created   = 0
        artifacts_created = 0
        folder_cache      = {}

        for file_info in files:
            filepath  = file_info.get('filepath', file_info.get('filename', ''))
            filename  = file_info.get('filename', os.path.basename(filepath))
            file_type = file_info.get('file_type', 'unknown')
            file_id   = file_info.get('file_id', '')

            folder_path = os.path.dirname(filepath) or project.project_name
            folder_name = os.path.basename(folder_path) or project.project_name

            if folder_path not in folder_cache:
                folder, created = Folder.objects.get_or_create(
                    project=project,
                    folder_path=folder_path,
                    defaults={'folder_name': folder_name, 'repo': repo, 'parent_folder': None},
                )
                folder_cache[folder_path] = folder
                if created:
                    folders_created += 1
            else:
                folder = folder_cache[folder_path]

            _, created = CodeArtifact.objects.get_or_create(
                storage_reference=file_id,
                defaults={
                    'project':       project,
                    'folder':        folder,
                    'version':       version,
                    'file_name':     filename,
                    'code_language': file_type,
                },
            )
            if created:
                artifacts_created += 1

        return {'version': version_number, 'folders': folders_created, 'artifacts': artifacts_created}


@method_decorator(csrf_exempt, name='dispatch')
class GitHubSyncView(APIView):
    """
    POST /projects/<project_id>/github/sync/

    مزامنة يدوية — يجيب آخر التغييرات من GitHub.

    Response:
        {
            "new_commit_sha": "xyz999",
            "files_changed": 2,
            "version_number": 2
        }
    """
    permission_classes = [IsAuthenticated,IsDeveloperRole]

    def post(self, request, project_id):
        project = get_object_or_404(Project, project_id=project_id)
        if project.user != request.user:
            return Response({"error": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        repo = Repository.objects.filter(
            project=project, source_type='github'
        ).first()

        if not repo:
            return Response(
                {"error": "No GitHub repo connected to this project. Use /github/connect/ first."},
                status=status.HTTP_404_NOT_FOUND,
            )

        github = GitHubService()

        try:
            new_sha = github.get_latest_commit_sha(repo.repo_url, repo.branch)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if new_sha == repo.last_commit_sha:
            return Response({
                "message":      "Already up to date.",
                "commit_sha":   new_sha,
                "files_changed": 0,
            })

        try:
            changed_files = github.get_changed_files(
                repo.repo_url, repo.branch,
                repo.last_commit_sha, new_sha,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if not changed_files:
            repo.last_commit_sha = new_sha
            repo.save()
            return Response({
                "message":      "No supported files changed.",
                "commit_sha":   new_sha,
                "files_changed": 0,
            })

        try:
            connect_view = GitHubConnectView()
            result = connect_view._sync_files_to_ai(project, changed_files, repo)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        repo.last_commit_sha = new_sha
        repo.save()

        return Response({
            "new_commit_sha": new_sha,
            "files_changed":  result['artifacts'],
            "version_number": result['version'],
        })


@method_decorator(csrf_exempt, name='dispatch')
class GitHubWebhookView(APIView):
    """
    POST /projects/<project_id>/github/webhook/

    يستقبل GitHub webhook تلقائياً عند كل push.
    لا يحتاج authentication — GitHub هو اللي بيبعت.

    GitHub Webhook Settings:
        URL: http://your-server/api/upm/projects/<id>/github/webhook/
        Content type: application/json
        Events: Just the push event
    """
    permission_classes = [AllowAny]

    def post(self, request, project_id):
        project = get_object_or_404(Project, project_id=project_id)

        repo = Repository.objects.filter(
            project=project, source_type='github'
        ).first()

        if not repo:
            return Response({"error": "No GitHub repo connected."}, status=status.HTTP_404_NOT_FOUND)

        event = request.headers.get('X-GitHub-Event', '')
        if event != 'push':
            return Response({"message": f"Event '{event}' ignored."})

        payload     = request.data
        new_sha     = payload.get('after', '')
        ref         = payload.get('ref', '')
        pushed_branch = ref.replace('refs/heads/', '')

        if pushed_branch != repo.branch:
            return Response({
                "message": f"Push on '{pushed_branch}' ignored (watching '{repo.branch}')."
            })

        if not new_sha or new_sha == repo.last_commit_sha:
            return Response({"message": "No new changes."})

        logger.info(f"[WEBHOOK] New push on {repo.repo_url} — SHA: {new_sha[:7]}")

        github = GitHubService()

        try:
            changed_files = github.get_changed_files(
                repo.repo_url, repo.branch,
                repo.last_commit_sha, new_sha,
            )
        except Exception as e:
            logger.error(f"[WEBHOOK] Error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if changed_files:
            try:
                connect_view = GitHubConnectView()
                connect_view._sync_files_to_ai(project, changed_files, repo)
            except Exception as e:
                logger.error(f"[WEBHOOK] Sync error: {e}")
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        repo.last_commit_sha = new_sha
        repo.save()

        return Response({
            "message":      "Webhook processed.",
            "files_changed": len(changed_files),
        })