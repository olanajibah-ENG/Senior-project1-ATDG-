"""
views/context_view.py
=====================
POST /cross-file-context/
Body: { "project_id": "...", "filename": "main.py" }

يجلب dependencies الملف المطلوب من نتائج التحليل
ويرجع signatures فقط من class_diagram_data لكل ملف مرتبط.
"""
import logging
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from bson import ObjectId

from core_ai.mongo_utils import get_mongo_db

logger = logging.getLogger(__name__)


def _get_signatures_from_diagram(class_diagram_data: dict) -> list:
    """استخراج signatures من class_diagram_data الموجودة في نتيجة التحليل."""
    if not class_diagram_data or not isinstance(class_diagram_data, dict):
        return []

    sigs = []
    for cls in class_diagram_data.get('classes', []):
        sigs.append(f"class {cls['name']}:")
        for m in cls.get('methods', []):
            sig = m.get('signature', '')
            if sig:
                sigs.append(f"  {sig}")
    return sigs


@api_view(['POST'])
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([AllowAny])
def cross_file_context_view(request):
    """
    POST /cross-file-context/
    Body: { "project_id": "...", "filename": "main.py" }
    """
    project_id = request.data.get('project_id')
    filename   = request.data.get('filename')

    if not project_id or not filename:
        return Response(
            {"error": "project_id and filename are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    db = get_mongo_db()
    if db is None:
        return Response({"error": "Database connection failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    code_files_col    = db[settings.CODE_FILES_COLLECTION]
    analysis_results_col = db[settings.ANALYSIS_RESULTS_COLLECTION]

    # ① جيبي كل ملفات المشروع المكتملة
    code_files = list(code_files_col.find({
        "source_project_id": project_id,
        "analysis_status"  : "COMPLETED"
    }))

    if not code_files:
        return Response(
            {"error": f"No completed files found for project {project_id}"},
            status=status.HTTP_404_NOT_FOUND
        )

    # ② ابني map: filename → { dependencies, class_diagram_data }
    all_files = {}
    project_filenames = {cf['filename'] for cf in code_files}

    for cf in code_files:
        result = analysis_results_col.find_one({
            "code_file_id": cf['_id'],
            "status"      : "COMPLETED"
        })
        if result:
            all_files[cf['filename']] = {
                "dependencies"      : result.get('dependencies', []),
                "class_diagram_data": result.get('class_diagram_data', {})
            }

    # ③ تحقق من وجود الملف المطلوب
    if filename not in all_files:
        return Response(
            {"error": f"File '{filename}' not found or not analyzed yet"},
            status=status.HTTP_404_NOT_FOUND
        )

    # ④ جيبي dependencies الخاصة بالملف المطلوب وفلتري المحلية فقط
    raw_deps   = all_files[filename].get('dependencies', [])
    local_deps = []
    for dep in raw_deps:
        # جربي المطابقة المباشرة أولاً
        if dep in project_filenames:
            local_deps.append(dep)
            continue
        # جربي مع إضافة الامتداد (.py أو .java)
        for ext in ['.py', '.java', '.js', '.ts']:
            dep_with_ext = dep + ext
            if dep_with_ext in project_filenames:
                local_deps.append(dep_with_ext)
                break

    # ⑤ استخرجي signatures من كل ملف مرتبط
    context = {}
    for dep_filename in local_deps:
        if dep_filename in all_files:
            sigs = _get_signatures_from_diagram(
                all_files[dep_filename].get('class_diagram_data', {})
            )
            if sigs:
                context[dep_filename] = sigs

    return Response({
        "project_id"  : project_id,
        "filename"    : filename,
        "dependencies": local_deps,
        "context"     : context
    }, status=status.HTTP_200_OK)
