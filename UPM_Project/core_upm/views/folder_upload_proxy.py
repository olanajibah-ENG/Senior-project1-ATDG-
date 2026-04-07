"""
folder_upload_proxy.py  ← معدّل بالكامل لـ Message Broker
======================
الفرق عن النسخة القديمة:
    قبل: UPM يبعث HTTP لـ AI وينتظر حتى يخلص (300 ثانية timeout)
    بعد: UPM يقرأ الملفات → يحطها في Redis كرسالة → يرجع task_id فوراً
         AI Celery worker يشيل الرسالة ويشتغل في الخلفية

شو اتحذف؟
    - كل كود requests.post() للـ AI
    - _save_to_mysql() من هون — انتقل لـ InternalUploadCompleteView
    - timeout المشاكل

شو أُضيف؟
    - قراءة محتوى الملفات وتحويلها لـ list قابل للتخزين في Redis
    - استدعاء process_upload_task.delay() بدل HTTP
    - رجوع task_id فوراً للفرونت
"""

import os
import logging
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from core_upm.permissions import IsDeveloperRole
from core_upm.models.project import Project
from core_upm.celery_tasks.upload_tasks import process_upload_task

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = (
    '.py', '.java', '.js', '.ts', '.cs',
    '.cpp', '.c', '.rb', '.go', '.kt',
)


@method_decorator(csrf_exempt, name='dispatch')
class FolderUploadProxyView(APIView):
    """
    POST /api/upm/projects/<project_id>/folder-upload/

    قبل: كان ينتظر AI يخلص → timeout خطر
    بعد: يرجع task_id فوراً → AI يشتغل في الخلفية

    Body (multipart/form-data):
        files : File[] — ملفات متعددة
        file  : File   — ملف واحد أو ZIP

    Response (فوري):
        {
            "task_id"     : "celery-task-uuid",
            "status"      : "processing",
            "message"     : "3 files queued for processing",
            "project_id"  : "uuid",
            "check_status": "/api/upm/tasks/celery-task-uuid/"
        }
    """
    permission_classes = [IsAuthenticated, IsDeveloperRole]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, project_id):
        logger.info(f"[FOLDER-UPLOAD] Request from:{request.user.username}, project:{project_id}")

        # 1. التحقق من المشروع والملكية
        project = get_object_or_404(Project, project_id=project_id)
        if project.user != request.user:
            return Response({"error": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        # 2. قراءة الملفات وتحويلها لـ list يتخزن في Redis
        # ليش نحول؟ لأن Celery يخزن الرسائل كـ JSON — الملفات الثنائية ما تنمشي كـ JSON
        # الحل: نقرأ محتوى كل ملف كـ text ونخزنه كـ string
        files_data = []

        for f in request.FILES.getlist('files'):
            file_info = self._read_file(f)
            if file_info:
                files_data.append(file_info)

        single = request.FILES.get('file')
        if single:
            file_info = self._read_file(single)
            if file_info:
                files_data.append(file_info)

        if not files_data:
            return Response(
                {"error": "No supported files. Supported: .py .java .js .ts .cs .cpp .rb .go .kt"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. بعث الرسالة لـ Redis — هاد السطر هو جوهر Message Broker
        # .delay() = ضع الرسالة في Redis وارجع فوراً بدون انتظار
        task = process_upload_task.delay(
            project_id   = str(project_id),
            project_name = project.project_name,
            user_email   = request.user.email,
            files_data   = files_data,
        )

        logger.info(f"[FOLDER-UPLOAD] Queued — task_id:{task.id}, files:{len(files_data)}")

        # 4. رجوع فوري بـ task_id — الفرونت يتابع الحالة منه
        return Response({
            "task_id":      task.id,
            "status":       "processing",
            "message":      f"{len(files_data)} file(s) queued for processing",
            "project_id":   str(project_id),
            "check_status": f"/api/upm/tasks/{task.id}/",
        }, status=status.HTTP_202_ACCEPTED)

    def _read_file(self, uploaded_file):
        """
        يقرأ محتوى ملف واحد ويرجعه كـ dict.
        يتجاهل الملفات غير المدعومة.
        """
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            return None
        try:
            content = uploaded_file.read().decode('utf-8', errors='ignore')
            return {
                'filename':     uploaded_file.name,
                'content':      content,
                'content_type': uploaded_file.content_type or 'text/plain',
            }
        except Exception as e:
            logger.warning(f"[FOLDER-UPLOAD] Failed to read {uploaded_file.name}: {e}")
            return None