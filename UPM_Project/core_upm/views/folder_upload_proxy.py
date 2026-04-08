"""
folder_upload_proxy.py ← تعديل إضافي: إصلاح ZIP
إضافة _read_zip() — يفك الـ ZIP ويقرأ محتوياته كـ text files
"""

import os
import io
import zipfile
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

IGNORED_PREFIXES = ('__MACOSX', '.', '__pycache__')
IGNORED_EXTENSIONS = ('.pyc', '.class', '.exe', '.dll', '.so', '.o')


@method_decorator(csrf_exempt, name='dispatch')
class FolderUploadProxyView(APIView):
    """
    POST /api/upm/projects/<project_id>/folder-upload/
    يقبل: ملف واحد / ملفات متعددة / ZIP
    يرجع: task_id فوراً
    """
    permission_classes = [IsAuthenticated, IsDeveloperRole]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, project_id):
        logger.info(f"[FOLDER-UPLOAD] Request from:{request.user.username}, project:{project_id}")

        project = get_object_or_404(Project, project_id=project_id)
        if project.user != request.user:
            return Response({"error": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        files_data = []

        # ملفات متعددة
        for f in request.FILES.getlist('files'):
            files_data.extend(self._process_uploaded_file(f))

        # ملف واحد (أو ZIP)
        single = request.FILES.get('file')
        if single:
            files_data.extend(self._process_uploaded_file(single))

        if not files_data:
            return Response(
                {"error": "No supported files found. Supported: .py .java .js .ts .cs .cpp .rb .go .kt"},
                status=status.HTTP_400_BAD_REQUEST
            )

        task = process_upload_task.delay(
            project_id   = str(project_id),
            project_name = project.project_name,
            user_email   = request.user.email,
            files_data   = files_data,
        )

        logger.info(f"[FOLDER-UPLOAD] Queued — task_id:{task.id}, files:{len(files_data)}")

        return Response({
            "task_id":      task.id,
            "status":       "processing",
            "message":      f"{len(files_data)} file(s) queued for processing",
            "project_id":   str(project_id),
            "check_status": f"/api/upm/tasks/{task.id}/",
        }, status=status.HTTP_202_ACCEPTED)

    def _process_uploaded_file(self, uploaded_file):
        """
        يحدد نوع الملف ويعالجه:
        - ZIP → يفكه ويرجع كل الملفات داخله
        - ملف عادي مدعوم → يقرأه مباشرة
        - ملف غير مدعوم → يتجاهله
        """
        if uploaded_file.name.lower().endswith('.zip'):
            return self._read_zip(uploaded_file)
        else:
            result = self._read_file(uploaded_file)
            return [result] if result else []

    def _read_zip(self, uploaded_file):
        """
        يفك الـ ZIP ويرجع list من dicts لكل ملف مدعوم.
        ZIP هو ملف binary — ما ينقرأ كـ text مباشرة.
        نقرأه كـ bytes ثم نفكه بـ zipfile ونقرأ محتوى كل ملف.
        """
        results = []
        try:
            raw = uploaded_file.read()
            with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                for entry in zf.namelist():
                    # تجاهل المجلدات
                    if entry.endswith('/'):
                        continue
                    basename = os.path.basename(entry)
                    # تجاهل الملفات المخفية و __MACOSX
                    if not basename or any(basename.startswith(p) for p in IGNORED_PREFIXES):
                        continue
                    ext = os.path.splitext(entry)[1].lower()
                    # تجاهل الامتدادات غير المدعومة
                    if ext in IGNORED_EXTENSIONS or ext not in SUPPORTED_EXTENSIONS:
                        continue
                    try:
                        content = zf.read(entry).decode('utf-8', errors='ignore')
                        results.append({
                            'filename':     entry,   # نحتفظ بالمسار الكامل داخل الـ ZIP
                            'content':      content,
                            'content_type': 'text/plain',
                        })
                    except Exception as e:
                        logger.warning(f"[FOLDER-UPLOAD] Skipping ZIP entry {entry}: {e}")

            logger.info(f"[FOLDER-UPLOAD] Extracted {len(results)} files from ZIP: {uploaded_file.name}")
        except zipfile.BadZipFile:
            logger.error(f"[FOLDER-UPLOAD] Invalid ZIP: {uploaded_file.name}")
        except Exception as e:
            logger.error(f"[FOLDER-UPLOAD] ZIP read error {uploaded_file.name}: {e}")

        return results

    def _read_file(self, uploaded_file):
        """يقرأ ملف واحد عادي ويرجعه كـ dict."""
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