"""
views/project_tree_view.py  ← جديد
==========================
ملف جديد كلياً — يوفر endpointين:

    1. GET /api/analysis/project-tree/<upm_project_id>/
       يرجع شجرة المجلدات والملفات للمشروع لرسمها في الفرونت
       (شبيه بالـ sidebar في VS Code)

    2. GET /api/analysis/file-content/<file_id>/
       يرجع محتوى ملف كود واحد من GridFS
       (شبيه بفتح ملف في VS Code)
"""

import logging
from bson import ObjectId
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from core_ai.mongo_utils import get_mongo_db, read_from_gridfs

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class ProjectTreeView(APIView):
    """
    GET /api/analysis/project-tree/<upm_project_id>/

    Query params (اختياري):
        version : int — رقم الإصدار المطلوب (لو ما ذُكر يرجع آخر إصدار)

    Response:
    {
        "project_id"    : "uuid",
        "project_name"  : "my_project",
        "version_number": 2,
        "tree"          : {
            "my_project": {
                "type": "folder",
                "children": {
                    "src": {
                        "type": "folder",
                        "children": {
                            "utils.py": {
                                "type": "file",
                                "file_id": "mongo_id",
                                "file_type": "python",
                                "filepath": "my_project/src/utils.py"
                            }
                        }
                    },
                    "main.py": {
                        "type": "file",
                        "file_id": "mongo_id",
                        "file_type": "python",
                        "filepath": "my_project/main.py"
                    }
                }
            }
        },
        "flat_files": [
            {
                "file_id"  : "mongo_id",
                "filename" : "utils.py",
                "filepath" : "my_project/src/utils.py",
                "file_type": "python"
            },
            ...
        ]
    }
    """

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [AllowAny]

    def get(self, request, upm_project_id):
        db = get_mongo_db()
        if db is None:
            return Response({"error": "Database connection failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        collection = db[settings.CODE_FILES_COLLECTION]
        versions_collection = db['project_versions']

        # تحديد الإصدار المطلوب
        requested_version = request.query_params.get('version')

        if requested_version:
            try:
                requested_version = int(requested_version)
            except ValueError:
                return Response({"error": "version must be an integer"}, status=status.HTTP_400_BAD_REQUEST)
            version_doc = versions_collection.find_one({
                "project_id": upm_project_id,
                "version_number": requested_version
            })
        else:
            # آخر إصدار
            version_doc = versions_collection.find_one(
                {"project_id": upm_project_id},
                sort=[("version_number", -1)]
            )

        if not version_doc:
            return Response(
                {"error": f"No versions found for project {upm_project_id}"},
                status=status.HTTP_404_NOT_FOUND
            )

        version_number = version_doc["version_number"]
        project_name = version_doc.get("project_name", "")
        file_ids = version_doc.get("file_ids", [])

        # جلب الملفات بالـ file_ids المخزنة في الإصدار
        object_ids = []
        for fid in file_ids:
            try:
                object_ids.append(ObjectId(fid))
            except Exception:
                pass

        files_cursor = collection.find({"_id": {"$in": object_ids}})
        files = list(files_cursor)

        if not files:
            # fallback: ابحث بـ source_project_id و version_number
            files = list(collection.find({
                "source_project_id": upm_project_id,
                "version_number": version_number
            }))

        # بناء الـ flat_files list
        flat_files = []
        for f in files:
            filepath = f.get('filepath', f.get('filename', ''))
            flat_files.append({
                "file_id":   str(f['_id']),
                "filename":  f.get('filename', ''),
                "filepath":  filepath,
                "file_type": f.get('file_type', 'unknown'),
            })

        # بناء شجرة المجلدات
        tree = self._build_tree(flat_files)

        return Response({
            "project_id":     upm_project_id,
            "project_name":   project_name,
            "version_number": version_number,
            "tree":           tree,
            "flat_files":     flat_files,
        })

    def _build_tree(self, flat_files):
        """
        يحول قائمة الملفات المسطّحة لشجرة متداخلة.
        مثال:
            flat: [{"filepath": "proj/src/utils.py", "file_id": "abc"}, ...]
            tree: {"proj": {"type": "folder", "children": {"src": {"type": "folder", "children": {"utils.py": {"type": "file", ...}}}}}}
        """
        tree = {}

        for file_info in flat_files:
            filepath = file_info.get('filepath', file_info.get('filename', ''))
            parts = filepath.replace('\\', '/').split('/')

            current = tree
            for i, part in enumerate(parts):
                if not part:
                    continue
                is_last = (i == len(parts) - 1)

                if is_last:
                    # ملف
                    current[part] = {
                        "type":      "file",
                        "file_id":   file_info["file_id"],
                        "file_type": file_info["file_type"],
                        "filepath":  filepath,
                    }
                else:
                    # مجلد
                    if part not in current:
                        current[part] = {"type": "folder", "children": {}}
                    elif current[part].get("type") != "folder":
                        current[part] = {"type": "folder", "children": {}}
                    current = current[part]["children"]

        return tree


@method_decorator(csrf_exempt, name='dispatch')
class FileContentView(APIView):
    """
    GET /api/analysis/file-content/<file_id>/

    يرجع محتوى ملف كود واحد من GridFS.

    Response:
    {
        "file_id"  : "mongo_id",
        "filename" : "utils.py",
        "filepath" : "my_project/src/utils.py",
        "file_type": "python",
        "content"  : "def hello():\n    print('hello')\n"
    }
    """

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [AllowAny]

    def get(self, request, file_id):
        db = get_mongo_db()
        if db is None:
            return Response({"error": "Database connection failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        collection = db[settings.CODE_FILES_COLLECTION]

        # جلب معلومات الملف من MongoDB
        try:
            file_doc = collection.find_one({"_id": ObjectId(file_id)})
        except Exception:
            return Response({"error": "Invalid file_id format"}, status=status.HTTP_400_BAD_REQUEST)

        if not file_doc:
            return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)

        gridfs_id = file_doc.get('gridfs_id')

        # جلب المحتوى من GridFS
        if gridfs_id:
            try:
                content = read_from_gridfs(gridfs_id)
            except Exception as e:
                logger.error(f"[FILE-CONTENT] GridFS read error for {file_id}: {e}")
                # fallback: لو في content مخزن مباشرة في الـ document (الطريقة القديمة)
                content = file_doc.get('content', '')
                if not content:
                    return Response(
                        {"error": "Could not retrieve file content from storage"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
        else:
            # الطريقة القديمة — المحتوى مخزن مباشرة في MongoDB
            content = file_doc.get('content', '')
            if not content:
                return Response(
                    {"error": "File has no content (no gridfs_id and no inline content)"},
                    status=status.HTTP_404_NOT_FOUND
                )

        return Response({
            "file_id":   file_id,
            "filename":  file_doc.get('filename', ''),
            "filepath":  file_doc.get('filepath', file_doc.get('filename', '')),
            "file_type": file_doc.get('file_type', 'unknown'),
            "content":   content,
        })