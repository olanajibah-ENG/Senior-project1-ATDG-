"""
views/project_tree_view.py  ← معدّل
==========================
التغييرات عن النسخة القديمة:
    1. أُضيف ProjectVersionsView — يرجع كل الإصدارات الموجودة للمشروع
       قبل ما المستخدم يختار إصدار ويطلب شجرته
    2. ProjectTreeView بقي كما هو (يرجع شجرة إصدار محدد أو آخر إصدار)
    3. FileContentView بقي كما هو
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
class ProjectVersionsView(APIView):
    """
    GET /api/analysis/project-versions/<upm_project_id>/

    يرجع كل الإصدارات الموجودة للمشروع مرتبة من الأحدث للأقدم.
    الفرونت يعرضها للمستخدم يختار منها قبل ما يطلب الشجرة.

    Response:
    {
        "project_id"  : "uuid",
        "project_name": "MyProject",
        "versions": [
            {
                "version_number": 3,
                "total_files"   : 12,
                "created_at"    : "2024-01-15T10:30:00Z"
            },
            {
                "version_number": 2,
                "total_files"   : 8,
                "created_at"    : "2024-01-10T09:00:00Z"
            },
            {
                "version_number": 1,
                "total_files"   : 5,
                "created_at"    : "2024-01-05T08:00:00Z"
            }
        ]
    }
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [AllowAny]

    def get(self, request, upm_project_id):
        db = get_mongo_db()
        if db is None:
            return Response(
                {"error": "Database connection failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        versions_collection = db['project_versions']

        version_docs = list(versions_collection.find(
            {"project_id": upm_project_id},
            sort=[("version_number", -1)]
        ))

        if not version_docs:
            return Response(
                {"error": f"No versions found for project {upm_project_id}"},
                status=status.HTTP_404_NOT_FOUND
            )

        project_name = version_docs[0].get("project_name", "")

        versions = []
        for doc in version_docs:
            created_at = doc.get("created_at")
            versions.append({
                "version_number": doc["version_number"],
                "total_files":    doc.get("total_files", len(doc.get("file_ids", []))),
                "created_at":     created_at.isoformat() if created_at else None,
            })

        return Response({
            "project_id":   upm_project_id,
            "project_name": project_name,
            "versions":     versions,
        })


@method_decorator(csrf_exempt, name='dispatch')
class ProjectTreeView(APIView):
    """
    GET /api/analysis/project-tree/<upm_project_id>/
    GET /api/analysis/project-tree/<upm_project_id>/?version=2

    يرجع شجرة الملفات والمجلدات لإصدار محدد.
    لو ما ذُكر version → يرجع آخر إصدار.

    Response:
    {
        "project_id"    : "uuid",
        "project_name"  : "MyProject",
        "version_number": 2,
        "tree": {
            "MyProject": {
                "type": "folder",
                "children": {
                    "src": {
                        "type": "folder",
                        "children": {
                            "utils.py": {
                                "type"    : "file",
                                "file_id" : "mongo_id",
                                "file_type": "python",
                                "filepath": "MyProject/src/utils.py"
                            }
                        }
                    }
                }
            }
        },
        "flat_files": [
            {"file_id": "...", "filename": "utils.py", "filepath": "...", "file_type": "python"},
            ...
        ]
    }
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [AllowAny]

    def get(self, request, upm_project_id):
        db = get_mongo_db()
        if db is None:
            return Response(
                {"error": "Database connection failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        collection = db[settings.CODE_FILES_COLLECTION]
        versions_collection = db['project_versions']

        requested_version = request.query_params.get('version')

        if requested_version:
            try:
                requested_version = int(requested_version)
            except ValueError:
                return Response(
                    {"error": "version must be an integer"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            version_doc = versions_collection.find_one({
                "project_id":     upm_project_id,
                "version_number": requested_version,
            })
        else:
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
        project_name   = version_doc.get("project_name", "")
        file_ids       = version_doc.get("file_ids", [])

        object_ids = []
        for fid in file_ids:
            try:
                object_ids.append(ObjectId(fid))
            except Exception:
                pass

        files = list(collection.find({"_id": {"$in": object_ids}}))

        if not files:
            files = list(collection.find({
                "source_project_id": upm_project_id,
                "version_number":    version_number,
            }))

        flat_files = []
        for f in files:
            filepath = f.get('filepath', f.get('filename', ''))
            flat_files.append({
                "file_id":   str(f['_id']),
                "filename":  f.get('filename', ''),
                "filepath":  filepath,
                "file_type": f.get('file_type', 'unknown'),
            })

        tree = self._build_tree(flat_files)

        return Response({
            "project_id":     upm_project_id,
            "project_name":   project_name,
            "version_number": version_number,
            "tree":           tree,
            "flat_files":     flat_files,
        })

    def _build_tree(self, flat_files):
        tree = {}
        for file_info in flat_files:
            filepath = file_info.get('filepath', file_info.get('filename', ''))
            parts    = filepath.replace('\\', '/').split('/')
            current  = tree

            for i, part in enumerate(parts):
                if not part:
                    continue
                is_last = (i == len(parts) - 1)

                if is_last:
                    current[part] = {
                        "type":      "file",
                        "file_id":   file_info["file_id"],
                        "file_type": file_info["file_type"],
                        "filepath":  filepath,
                    }
                else:
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

    يرجع محتوى ملف واحد من GridFS.

    Response:
    {
        "file_id"  : "mongo_id",
        "filename" : "utils.py",
        "filepath" : "MyProject/src/utils.py",
        "file_type": "python",
        "content"  : "def hello(): ..."
    }
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [AllowAny]

    def get(self, request, file_id):
        db = get_mongo_db()
        if db is None:
            return Response(
                {"error": "Database connection failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        collection = db[settings.CODE_FILES_COLLECTION]

        try:
            file_doc = collection.find_one({"_id": ObjectId(file_id)})
        except Exception:
            return Response(
                {"error": "Invalid file_id format"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not file_doc:
            return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)

        gridfs_id = file_doc.get('gridfs_id')

        if gridfs_id:
            try:
                content = read_from_gridfs(gridfs_id)
            except Exception as e:
                logger.error(f"[FILE-CONTENT] GridFS read error for {file_id}: {e}")
                content = file_doc.get('content', '')
                if not content:
                    return Response(
                        {"error": "Could not retrieve file content from storage"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
        else:
            content = file_doc.get('content', '')
            if not content:
                return Response(
                    {"error": "File has no content"},
                    status=status.HTTP_404_NOT_FOUND
                )

        return Response({
            "file_id":   file_id,
            "filename":  file_doc.get('filename', ''),
            "filepath":  file_doc.get('filepath', file_doc.get('filename', '')),
            "file_type": file_doc.get('file_type', 'unknown'),
            "content":   content,
        })