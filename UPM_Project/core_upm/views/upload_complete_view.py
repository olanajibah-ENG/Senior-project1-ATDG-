"""
views/upload_complete_view.py  ← جديد كلياً
=============================
ليش هاد الملف موجود؟
    قبل: _save_to_mysql() كانت تتستدعى مباشرة بعد رد AI
    بعد: AI بيشتغل في الخلفية — لما يخلص يبعث نتيجته لـ UPM على هاد الـ endpoint
         UPM يحفظها في MySQL

من يكلم هاد الـ endpoint؟
    Celery task (upload_tasks.py) بعد ما يخلص من AI
    مش الفرونت — هاد endpoint داخلي فقط

الأمان:
    X-Internal-Key header — مفتاح سري بين UPM وCelery
    الفرونت ما يعرفه ولا يقدر يستدعيه
"""

import os
import logging
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.conf import settings

from core_upm.models.project import Project
from core_upm.models.folder import Folder
from core_upm.models.version import Version
from core_upm.models.artifact import CodeArtifact
from core_upm.models.repository import Repository

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class InternalUploadCompleteView(APIView):
    """
    POST /api/upm/internal/upload-complete/

    يستقبل نتيجة الرفع من Celery task ويحفظها في MySQL.
    داخلي فقط — محمي بـ X-Internal-Key.

    Body (JSON):
        {
            "project_id": "uuid",
            "ai_data"   : { ... نتيجة AI ... },
            "task_id"   : "celery-task-uuid",
            "repo_id"   : "uuid" (اختياري — لو جاي من GitHub sync),
            "new_sha"   : "abc123" (اختياري — لو جاي من GitHub sync)
        }
    """
    permission_classes = [AllowAny]  # الأمان عبر X-Internal-Key

    def post(self, request):
        # التحقق من الـ Internal Key
        internal_key = request.headers.get('X-Internal-Key', '')
        if internal_key != settings.INTERNAL_SERVICE_KEY:
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        project_id = request.data.get('project_id')
        ai_data    = request.data.get('ai_data', {})
        repo_id    = request.data.get('repo_id')
        new_sha    = request.data.get('new_sha')

        if not project_id or not ai_data:
            return Response({"error": "project_id and ai_data required"}, status=status.HTTP_400_BAD_REQUEST)

        project = get_object_or_404(Project, project_id=project_id)

        # جلب الـ repo لو كانت GitHub sync
        repo = None
        if repo_id:
            try:
                repo = Repository.objects.get(repo_id=repo_id)
            except Repository.DoesNotExist:
                pass

        try:
            result = self._save_to_mysql(project, ai_data, repo)

            # تحديث last_commit_sha لو كانت GitHub sync
            if repo and new_sha:
                repo.last_commit_sha = new_sha
                repo.save()
                logger.info(f"[UPLOAD-COMPLETE] Updated SHA: {new_sha[:7]}")

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"[UPLOAD-COMPLETE] MySQL save failed: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @transaction.atomic
    def _save_to_mysql(self, project, ai_data, repo=None):
        """يحفظ Version + Folders + CodeArtifacts في MySQL."""
        files          = ai_data.get('files', [])
        version_number = ai_data.get('version_number', 1)

        version, _ = Version.objects.get_or_create(
            project=project,
            version_number=version_number,
            defaults={'description': 'Uploaded via async task'}
        )

        folders_created   = 0
        artifacts_created = 0
        folder_cache      = {}

        for file_info in files:
            filepath    = file_info.get('filepath', file_info.get('filename', ''))
            filename    = file_info.get('filename', os.path.basename(filepath))
            file_type   = file_info.get('file_type', 'unknown')
            file_id     = file_info.get('file_id', '')

            folder_path = os.path.dirname(filepath) or project.project_name
            folder_name = os.path.basename(folder_path) or project.project_name

            if folder_path not in folder_cache:
                folder, created = Folder.objects.get_or_create(
                    project=project,
                    folder_path=folder_path,
                    defaults={
                        'folder_name': folder_name,
                        'repo':        repo,
                        'parent_folder': None,
                    }
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
                }
            )
            if created:
                artifacts_created += 1

        logger.info(
            f"[UPLOAD-COMPLETE] MySQL saved — "
            f"version:{version_number}, folders:{folders_created}, artifacts:{artifacts_created}"
        )
        return {
            'version':   version_number,
            'folders':   folders_created,
            'artifacts': artifacts_created,
        }