"""
folder_upload_proxy.py
======================
يستقبل طلبات رفع المجلدات من المستخدم:
1. يجيب المشروع تلقائياً من الـ URL
2. يرسل الملفات لـ AI service للحفظ في MongoDB
3. يحفظ البيانات في MySQL (Folder + Version + CodeArtifact)

endpoint: POST /projects/<project_id>/folder-upload/
Gateway:  POST http://localhost/api/upm/projects/<project_id>/folder-upload/
"""

import os
import requests
import logging
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from core_upm.models.project import Project
from core_upm.models.folder import Folder
from core_upm.models.version import Version
from core_upm.models.artifact import CodeArtifact

logger = logging.getLogger(__name__)

AI_FOLDER_UPLOAD_URL = 'http://ai_django_app:8000/folder-upload/'


@method_decorator(csrf_exempt, name='dispatch')
class FolderUploadProxyView(APIView):
    """
    POST /projects/<project_id>/folder-upload/

    Body (multipart/form-data):
        files : File[] — ملفات متعددة
        file  : File   — ملف ZIP

    Response:
        {
            "project_id"    : "uuid",
            "project_name"  : "my_project",
            "version_number": 1,
            "file_count"    : 5,
            "files"         : [...],
            "skipped"       : 0,
            "mysql_saved"   : { "version": 1, "folders": 2, "artifacts": 5 }
        }
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, project_id):
        logger.info(f"[FOLDER-UPLOAD] Request from: {request.user.username}, project: {project_id}")

        # 1. جلب المشروع تلقائياً من الـ URL والتحقق من الملكية
        project = get_object_or_404(Project, project_id=project_id)
        if project.user != request.user:
            return Response({"error": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        # 2. تجميع الملفات
        files_to_forward = []
        for f in request.FILES.getlist('files'):
            files_to_forward.append(('files', (f.name, f.read(), f.content_type)))
        single_file = request.FILES.get('file')
        if single_file:
            files_to_forward.append(('file', (single_file.name, single_file.read(), single_file.content_type)))

        if not files_to_forward:
            return Response(
                {"error": "No files received. Send 'files' (multiple) or 'file' (ZIP)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. إرسال الملفات لـ AI service
        try:
            ai_response = requests.post(
                AI_FOLDER_UPLOAD_URL,
                data={
                    'project_name': project.project_name,
                    'user_email': request.user.email,
                },
                files=files_to_forward,
                timeout=300
            )
            ai_response.raise_for_status()
            ai_data = ai_response.json()
            logger.info(f"[FOLDER-UPLOAD] AI responded OK — files: {ai_data.get('file_count', 0)}")

        except requests.exceptions.ConnectionError:
            return Response({"error": "AI service is unavailable."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except requests.exceptions.Timeout:
            return Response({"error": "AI service timed out."}, status=status.HTTP_504_GATEWAY_TIMEOUT)
        except Exception as e:
            logger.error(f"[FOLDER-UPLOAD] AI error: {e}")
            return Response({"error": f"AI service error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 4. حفظ في MySQL مرتبط بالمشروع تلقائياً
        try:
            mysql_result = self._save_to_mysql(project, ai_data)
            ai_data['mysql_saved'] = mysql_result
        except Exception as e:
            logger.error(f"[FOLDER-UPLOAD] MySQL error: {e}")
            ai_data['mysql_error'] = str(e)

        return Response(ai_data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def _save_to_mysql(self, project, ai_data):
        files = ai_data.get('files', [])
        version_number = ai_data.get('version_number', 1)

        # إنشاء Version
        version, _ = Version.objects.get_or_create(
            project=project,
            version_number=version_number,
            defaults={'description': 'Uploaded via folder upload'}
        )

        folders_created = 0
        artifacts_created = 0
        folder_cache = {}

        for file_info in files:
            filepath = file_info.get('filepath', file_info.get('filename', ''))
            filename = file_info.get('filename', os.path.basename(filepath))
            file_type = file_info.get('file_type', 'unknown')
            file_id = file_info.get('file_id', '')

            # تحديد مسار المجلد من الـ filepath
            folder_path = os.path.dirname(filepath) or project.project_name
            folder_name = os.path.basename(folder_path) or project.project_name

            # جلب أو إنشاء Folder مرتبط بالمشروع
            if folder_path not in folder_cache:
                folder, created = Folder.objects.get_or_create(
                    project=project,
                    folder_path=folder_path,
                    defaults={'folder_name': folder_name, 'repo': None, 'parent_folder': None}
                )
                folder_cache[folder_path] = folder
                if created:
                    folders_created += 1
            else:
                folder = folder_cache[folder_path]

            # إنشاء CodeArtifact
            _, created = CodeArtifact.objects.get_or_create(
                storage_reference=file_id,
                defaults={
                    'project': project,
                    'folder': folder,
                    'version': version,
                    'file_name': filename,
                    'code_language': file_type,
                }
            )
            if created:
                artifacts_created += 1

        logger.info(f"[FOLDER-UPLOAD] MySQL saved — folders: {folders_created}, artifacts: {artifacts_created}")
        return {'version': version_number, 'folders': folders_created, 'artifacts': artifacts_created}