"""
github_views.py  ← معدّل لـ Message Broker
===============
الفرق عن النسخة القديمة:
    قبل: _sync_files_to_ai() كانت تبعث HTTP لـ AI وتنتظر (timeout خطر على repos الكبيرة)
    بعد: نقرأ الملفات من GitHub → نحطها في Redis كرسالة → نرجع فوراً
         AI Celery worker يشيل الرسالة ويحفظ الملفات بالخلفية

شو اتحذف؟
    - _sync_files_to_ai() كاملة (HTTP + _save_to_mysql)
    - AI_FOLDER_UPLOAD_URL
    - BATCH_SIZE loop

شو أُضيف؟
    - _files_to_data() تحوّل tuples لـ list قابل للتخزين في Redis
    - process_github_sync_task.delay() بدل HTTP
"""

import logging
import threading
import os
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from core_upm.permissions import IsDeveloperRole
from core_upm.models.project import Project
from core_upm.models.repository import Repository
from core_upm.services.github_service import GitHubService
from core_upm.celery_tasks.upload_tasks import process_github_sync_task

logger = logging.getLogger(__name__)

SHA_THREAD_TIMEOUT   = 60
FILES_THREAD_TIMEOUT = 600

import os
GITHUB_MAX_FILES = int(os.environ.get('GITHUB_MAX_FILES', 0)) or None


@method_decorator(csrf_exempt, name='dispatch')
class GitHubConnectView(APIView):
    """
    POST /projects/<project_id>/github/connect/

    يربط repo ويجيب كل الملفات → يحطها في Redis → يرجع task_id فوراً.
    قبل كان ينتظر حتى يخلص — الحين يرجع فوراً.

    Body:
        {"repo_url": "https://github.com/user/repo", "branch": "main", "github_token": "..."}

    Response (فوري):
        {
            "task_id"     : "celery-uuid",
            "status"      : "processing",
            "repo_id"     : "uuid",
            "check_status": "/api/upm/tasks/celery-uuid/"
        }
    """
    permission_classes = [IsAuthenticated, IsDeveloperRole]

    def post(self, request, project_id):
        project = get_object_or_404(Project, project_id=project_id)
        if project.user != request.user:
            return Response({"error": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        repo_url     = request.data.get('repo_url', '').strip()
        branch       = request.data.get('branch', 'main').strip()
        github_token = request.data.get('github_token', '').strip() or None

        if not repo_url:
            return Response({"error": "repo_url is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not repo_url.startswith('https://github.com/'):
            return Response({"error": "Only GitHub repos are supported."}, status=status.HTTP_400_BAD_REQUEST)

        github = GitHubService(token=github_token)

        # جلب آخر SHA
        sha_result = {'sha': None, 'error': None}
        def fetch_sha():
            try:
                sha_result['sha'] = github.get_latest_commit_sha(repo_url, branch)
            except Exception as e:
                sha_result['error'] = str(e)

        t = threading.Thread(target=fetch_sha)
        t.start()
        t.join(timeout=SHA_THREAD_TIMEOUT)

        if sha_result['error']:
            return Response({"error": sha_result['error']}, status=status.HTTP_400_BAD_REQUEST)
        if not sha_result['sha']:
            return Response({"error": "Timeout connecting to GitHub."}, status=status.HTTP_504_GATEWAY_TIMEOUT)

        latest_sha = sha_result['sha']

        # حفظ Repository في MySQL
        repo_name = repo_url.rstrip('/').split('/')[-1]
        repo, _ = Repository.objects.update_or_create(
            project=project,
            repo_url=repo_url,
            defaults={
                'repo_name':       repo_name,
                'branch':          branch,
                'last_commit_sha': latest_sha,
                'source_type':     'github',
            },
        )

        # جلب الملفات من GitHub
        files_result = {'files': None, 'error': None}
        def fetch_files():
            try:
                files_result['files'] = github.get_all_files(repo_url, branch)
            except Exception as e:
                files_result['error'] = str(e)

        t2 = threading.Thread(target=fetch_files)
        t2.start()
        t2.join(timeout=FILES_THREAD_TIMEOUT)

        if files_result['error']:
            return Response({"error": files_result['error']}, status=status.HTTP_400_BAD_REQUEST)
        if files_result['files'] is None:
            return Response({"error": "Timeout fetching files from GitHub."}, status=status.HTTP_504_GATEWAY_TIMEOUT)

        files = files_result['files']
        if not files:
            return Response({"error": "No supported files found."}, status=status.HTTP_400_BAD_REQUEST)

        if GITHUB_MAX_FILES and len(files) > GITHUB_MAX_FILES:
            files = files[:GITHUB_MAX_FILES]

        # تحويل الملفات لـ format قابل لـ Redis
        files_data = self._files_to_data(files)

        # بعث الرسالة لـ Redis — يرجع فوراً
        task = process_github_sync_task.delay(
            project_id   = str(project_id),
            project_name = project.project_name,
            user_email   = request.user.email,
            files_data   = files_data,
            repo_id      = str(repo.repo_id),
            new_sha      = latest_sha,
        )

        logger.info(f"[GITHUB-CONNECT] Queued — task:{task.id}, files:{len(files_data)}")

        return Response({
            "task_id":      task.id,
            "status":       "processing",
            "repo_id":      str(repo.repo_id),
            "files_queued": len(files_data),
            "check_status": f"/api/upm/tasks/{task.id}/",
        }, status=status.HTTP_202_ACCEPTED)

    def _files_to_data(self, files):
        """
        يحوّل List of (filepath, content, file_type) لـ List of dicts.
        ليش؟ لأن Celery يخزن الرسائل كـ JSON — tuples ما تنمشي.
        """
        result = []
        for filepath, content, file_type in files:
            result.append({
                'filename':     filepath,
                'content':      content,
                'content_type': 'text/plain',
            })
        return result


@method_decorator(csrf_exempt, name='dispatch')
class GitHubSyncView(APIView):
    """
    POST /projects/<project_id>/github/sync/

    مزامنة يدوية — يجيب الملفات المتغيرة فقط → Redis → task_id فوراً.
    """
    permission_classes = [IsAuthenticated, IsDeveloperRole]

    def post(self, request, project_id):
        project = get_object_or_404(Project, project_id=project_id)
        if project.user != request.user:
            return Response({"error": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        repo = Repository.objects.filter(project=project, source_type='github').first()
        if not repo:
            return Response(
                {"error": "No GitHub repo connected. Use /github/connect/ first."},
                status=status.HTTP_404_NOT_FOUND
            )

        github = GitHubService()

        try:
            new_sha = github.get_latest_commit_sha(repo.repo_url, repo.branch)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if new_sha == repo.last_commit_sha:
            return Response({"message": "Already up to date.", "commit_sha": new_sha})

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
            return Response({"message": "No supported files changed.", "commit_sha": new_sha})

        files_data = self._files_to_data(changed_files)

        task = process_github_sync_task.delay(
            project_id   = str(project_id),
            project_name = project.project_name,
            user_email   = request.user.email,
            files_data   = files_data,
            repo_id      = str(repo.repo_id),
            new_sha      = new_sha,
        )

        logger.info(f"[GITHUB-SYNC] Queued — task:{task.id}, files:{len(files_data)}")

        return Response({
            "task_id":        task.id,
            "status":         "processing",
            "new_sha":        new_sha,
            "files_queued":   len(files_data),
            "check_status":   f"/api/upm/tasks/{task.id}/",
        }, status=status.HTTP_202_ACCEPTED)

    def _files_to_data(self, files):
        return [
            {'filename': fp, 'content': content, 'content_type': 'text/plain'}
            for fp, content, ft in files
        ]


@method_decorator(csrf_exempt, name='dispatch')
class GitHubWebhookView(APIView):
    """
    POST /projects/<project_id>/github/webhook/

    يستقبل push event من GitHub تلقائياً.
    لا يحتاج auth — GitHub هو اللي بيبعت.
    الحين بدل ما ينتظر AI يخلص → يحط رسالة في Redis ويرد لـ GitHub فوراً.
    """
    permission_classes = [AllowAny]

    def post(self, request, project_id):
        project = get_object_or_404(Project, project_id=project_id)
        repo = Repository.objects.filter(project=project, source_type='github').first()
        if not repo:
            return Response({"error": "No GitHub repo connected."}, status=status.HTTP_404_NOT_FOUND)

        event = request.headers.get('X-GitHub-Event', '')
        if event != 'push':
            return Response({"message": f"Event '{event}' ignored."})

        payload       = request.data
        new_sha       = payload.get('after', '')
        pushed_branch = payload.get('ref', '').replace('refs/heads/', '')

        if pushed_branch != repo.branch:
            return Response({"message": f"Push on '{pushed_branch}' ignored."})

        if not new_sha or new_sha == repo.last_commit_sha:
            return Response({"message": "No new changes."})

        logger.info(f"[WEBHOOK] New push — SHA:{new_sha[:7]}, repo:{repo.repo_url}")

        github = GitHubService()
        try:
            changed_files = github.get_changed_files(
                repo.repo_url, repo.branch,
                repo.last_commit_sha, new_sha,
            )
        except Exception as e:
            logger.error(f"[WEBHOOK] get_changed_files error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not changed_files:
            repo.last_commit_sha = new_sha
            repo.save()
            return Response({"message": "No supported files changed."})

        files_data = [
            {'filename': fp, 'content': content, 'content_type': 'text/plain'}
            for fp, content, ft in changed_files
        ]

        # يحط الرسالة في Redis ويرد لـ GitHub فوراً
        # GitHub بيتوقع رد خلال 10 ثواني — الحين ما في خوف من timeout
        task = process_github_sync_task.delay(
            project_id   = str(project_id),
            project_name = project.project_name,
            user_email   = project.user.email if project.user else '',
            files_data   = files_data,
            repo_id      = str(repo.repo_id),
            new_sha      = new_sha,
        )

        logger.info(f"[WEBHOOK] Queued — task:{task.id}, files:{len(files_data)}")

        return Response({
            "message":      "Webhook received. Processing in background.",
            "task_id":      task.id,
            "files_queued": len(files_data),
        })