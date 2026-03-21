"""
views/dependency_graph_view.py
==============================
POST /api/dependency-graph/
Body: { "project_id": "proj-123" }

يجلب ملفات المشروع المحللة من MongoDB + GridFS
ويمررها لـ DependencyGraphBuilder لبناء الـ graph والترتيب الطبولوجي.
"""

import logging
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

from core_ai.mongo_utils import get_mongo_db, read_from_gridfs
from core_ai.services.dependency_graph_builder import DependencyGraphBuilder

logger = logging.getLogger(__name__)


@api_view(['POST'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([AllowAny])
def dependency_graph_view(request):
    """
    POST /api/dependency-graph/
    Body: { "project_id": "proj-123" }
    """
    project_id = request.data.get('project_id')
    if not project_id:
        return Response({"error": "project_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    db = get_mongo_db()
    if db is None:
        return Response({"error": "Database connection failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    code_files_collection = db[settings.CODE_FILES_COLLECTION]
    all_files = list(code_files_collection.find({"source_project_id": project_id}))

    if not all_files:
        return Response({"error": f"No files found for project {project_id}"}, status=status.HTTP_404_NOT_FOUND)

    # فصل الملفات المكتملة عن الـ pending
    completed_files = [f for f in all_files if f.get('analysis_status') == 'COMPLETED']
    pending_files   = [f for f in all_files if f.get('analysis_status') != 'COMPLETED']

    # بناء قائمة الملفات مع محتواها من GridFS
    files_list = []
    for f in completed_files:
        try:
            content = read_from_gridfs(f['gridfs_id']) if f.get('gridfs_id') else ''
        except Exception as e:
            logger.warning(f"Could not read GridFS content for {f.get('filename')}: {e}")
            content = ''
        files_list.append({
            'filename':  f.get('filename', ''),
            'content':   content,
            'file_type': f.get('file_type', ''),
        })

    builder = DependencyGraphBuilder()
    result  = builder.process_and_sort(files_list)

    response = {
        "project_id":  project_id,
        "total_files": len(all_files),
        "ordered":     result['ordered'],
        "graph":       result['graph'],
    }

    if pending_files:
        response["pending_files"] = [f.get('filename') for f in pending_files]
        response["message"] = "Not all files analyzed yet"

    return Response(response, status=status.HTTP_200_OK)
