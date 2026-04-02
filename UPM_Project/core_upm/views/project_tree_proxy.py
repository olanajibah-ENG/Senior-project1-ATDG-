"""
views/project_tree_proxy.py  ← جديد
============================
ملف جديد كلياً — proxy في UPM يستدعي الـ AI service لجلب:

    1. GET /api/upm/projects/<project_id>/tree/
       شجرة المجلدات والملفات للمشروع (من AI/MongoDB)
       يدعم ?version=N لجلب إصدار محدد

    2. GET /api/upm/projects/<project_id>/files/<file_id>/content/
       محتوى ملف كود واحد (من GridFS عبر AI)

لماذا proxy في UPM؟
    - لأن الـ Auth والـ permission check يصير هنا في UPM
    - الفرونت ما يحتاج يعرف عن AI service
    - كل شي يمشي من نقطة واحدة /api/upm/
"""

import requests
import logging
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from core_upm.models.project import Project

logger = logging.getLogger(__name__)

AI_BASE_URL = 'http://ai_django_app:8000/api/analysis'


@method_decorator(csrf_exempt, name='dispatch')
class ProjectTreeProxyView(APIView):
    """
    GET /api/upm/projects/<project_id>/tree/
    GET /api/upm/projects/<project_id>/tree/?version=2

    يتحقق من ملكية المشروع ثم يجيب شجرة الملفات من AI service.

    Response (نفس response الـ AI):
    {
        "project_id"    : "uuid",
        "project_name"  : "my_project",
        "version_number": 2,
        "tree"          : { ... },   ← شجرة متداخلة للفرونت
        "flat_files"    : [ ... ]    ← قائمة مسطّحة للملفات
    }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        # التحقق من ملكية المشروع
        project = get_object_or_404(Project, project_id=project_id)
        if project.user != request.user:
            return Response({"error": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        # بناء الـ URL للـ AI service
        ai_url = f"{AI_BASE_URL}/project-tree/{str(project_id)}/"
        params = {}
        if request.query_params.get('version'):
            params['version'] = request.query_params.get('version')

        try:
            headers = {'Host': 'localhost'}
            ai_response = requests.get(ai_url, params=params, headers=headers, timeout=30)
            ai_response.raise_for_status()
            return Response(ai_response.json(), status=ai_response.status_code)

        except requests.exceptions.ConnectionError:
            return Response({"error": "AI service is unavailable."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except requests.exceptions.HTTPError as e:
            if ai_response.status_code == 404:
                return Response(
                    {"error": f"No files found for project {project_id}. Did you upload any files?"},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"[TREE-PROXY] Error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class FileContentProxyView(APIView):
    """
    GET /api/upm/projects/<project_id>/files/<file_id>/content/

    يتحقق من ملكية المشروع ثم يجيب محتوى الملف من GridFS عبر AI service.

    Response:
    {
        "file_id"  : "mongo_id",
        "filename" : "utils.py",
        "filepath" : "my_project/src/utils.py",
        "file_type": "python",
        "content"  : "def hello():\n    print('hello')\n"
    }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id, file_id):
        # التحقق من ملكية المشروع
        project = get_object_or_404(Project, project_id=project_id)
        if project.user != request.user:
            return Response({"error": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        ai_url = f"{AI_BASE_URL}/file-content/{file_id}/"

        try:
            headers = {'Host': 'localhost'}
            ai_response = requests.get(ai_url, headers=headers, timeout=30)
            ai_response.raise_for_status()
            return Response(ai_response.json(), status=ai_response.status_code)

        except requests.exceptions.ConnectionError:
            return Response({"error": "AI service is unavailable."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except requests.exceptions.HTTPError as e:
            if ai_response.status_code == 404:
                return Response({"error": "File not found."}, status=status.HTTP_404_NOT_FOUND)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"[FILE-CONTENT-PROXY] Error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)