"""
views/project_tree_proxy.py  ← معدّل
============================
التغييرات عن النسخة القديمة:
    1. أُضيف ProjectVersionsProxyView — يجيب كل الإصدارات الموجودة
       الفرونت يستدعيه أولاً قبل طلب الشجرة
    2. ProjectTreeProxyView و FileContentProxyView بقيا كما هما
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
class ProjectVersionsProxyView(APIView):
    """
    GET /api/upm/projects/<project_id>/versions/

    يرجع كل الإصدارات المتاحة للمشروع.
    الفرونت يعرضها في قائمة dropdown أو timeline قبل ما يطلب الشجرة.

    Response:
    {
        "project_id"  : "uuid",
        "project_name": "MyProject",
        "versions": [
            {"version_number": 3, "total_files": 12, "created_at": "2024-01-15T10:30:00Z"},
            {"version_number": 2, "total_files": 8,  "created_at": "2024-01-10T09:00:00Z"},
            {"version_number": 1, "total_files": 5,  "created_at": "2024-01-05T08:00:00Z"}
        ]
    }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        project = get_object_or_404(Project, project_id=project_id)
        if project.user != request.user:
            return Response({"error": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        ai_url = f"{AI_BASE_URL}/project-versions/{str(project_id)}/"
        try:
            ai_response = requests.get(ai_url, headers={'Host': 'localhost'}, timeout=30)
            ai_response.raise_for_status()
            return Response(ai_response.json(), status=ai_response.status_code)

        except requests.exceptions.ConnectionError:
            return Response({"error": "AI service is unavailable."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except requests.exceptions.HTTPError:
            if ai_response.status_code == 404:
                return Response(
                    {"error": "No versions found. Did you upload any files?"},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response({"error": "AI service error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"[VERSIONS-PROXY] Error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class ProjectTreeProxyView(APIView):
    """
    GET /api/upm/projects/<project_id>/tree/
    GET /api/upm/projects/<project_id>/tree/?version=2

    يرجع شجرة الملفات والمجلدات للإصدار المحدد (أو آخر إصدار).
    الفرونت يستخدمها لرسم الـ sidebar مثل VS Code.

    Response:
    {
        "project_id"    : "uuid",
        "project_name"  : "MyProject",
        "version_number": 2,
        "tree"          : { ... شجرة متداخلة ... },
        "flat_files"    : [ ... قائمة مسطّحة ... ]
    }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        project = get_object_or_404(Project, project_id=project_id)
        if project.user != request.user:
            return Response({"error": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        ai_url = f"{AI_BASE_URL}/project-tree/{str(project_id)}/"
        params = {}
        if request.query_params.get('version'):
            params['version'] = request.query_params.get('version')

        try:
            ai_response = requests.get(
                ai_url, params=params,
                headers={'Host': 'localhost'}, timeout=30
            )
            ai_response.raise_for_status()
            return Response(ai_response.json(), status=ai_response.status_code)

        except requests.exceptions.ConnectionError:
            return Response({"error": "AI service is unavailable."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except requests.exceptions.HTTPError:
            if ai_response.status_code == 404:
                return Response(
                    {"error": "No files found for this project/version."},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response({"error": "AI service error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"[TREE-PROXY] Error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class FileContentProxyView(APIView):
    """
    GET /api/upm/projects/<project_id>/files/<file_id>/content/

    يرجع محتوى ملف كود واحد من GridFS.
    الـ file_id تاخذه من flat_files في response الشجرة.

    Response:
    {
        "file_id"  : "mongo_id",
        "filename" : "utils.py",
        "filepath" : "MyProject/src/utils.py",
        "file_type": "python",
        "content"  : "def hello(): ..."
    }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id, file_id):
        project = get_object_or_404(Project, project_id=project_id)
        if project.user != request.user:
            return Response({"error": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        ai_url = f"{AI_BASE_URL}/file-content/{file_id}/"
        try:
            ai_response = requests.get(
                ai_url, headers={'Host': 'localhost'}, timeout=30
            )
            ai_response.raise_for_status()
            return Response(ai_response.json(), status=ai_response.status_code)

        except requests.exceptions.ConnectionError:
            return Response({"error": "AI service is unavailable."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except requests.exceptions.HTTPError:
            if ai_response.status_code == 404:
                return Response({"error": "File not found."}, status=status.HTTP_404_NOT_FOUND)
            return Response({"error": "AI service error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"[FILE-CONTENT-PROXY] Error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)