# core_ai/views/file_version_view.py
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from bson import ObjectId
from django.conf import settings
from core_ai.mongo_utils import get_mongo_db

logger = logging.getLogger(__name__)


class FileVersionsView(APIView):
    """
    جلب تاريخ النسخ (Versions) لملف واحد
    
    GET /api/analysis/file-versions/<file_id>/
    أو
    GET /api/analysis/file-versions/by-path/?project_id=UUID&filepath=path/to/file.py
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [AllowAny]

    def get(self, request, file_id=None):
        db = get_mongo_db()
        if db is None:
            return Response({"error": "Database connection failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        project_id = request.query_params.get('project_id')
        filepath = request.query_params.get('filepath')

        # ====================== البحث عن الملف ======================
        if file_id:
            try:
                file_obj = db[settings.CODE_FILES_COLLECTION].find_one({"_id": ObjectId(file_id)})
            except:
                file_obj = None
        elif project_id and filepath:
            file_obj = db[settings.CODE_FILES_COLLECTION].find_one({
                "source_project_id": project_id,
                "filepath": filepath
            })
            # محاولة ثانية باسم الملف فقط
            if not file_obj:
                file_obj = db[settings.CODE_FILES_COLLECTION].find_one({
                    "source_project_id": project_id,
                    "filename": filepath.split('/')[-1]
                })
        else:
            return Response({
                "error": "يجب إرسال file_id أو (project_id + filepath)"
            }, status=status.HTTP_400_BAD_REQUEST)

        if not file_obj:
            return Response({"error": "الملف غير موجود"}, status=status.HTTP_404_NOT_FOUND)

        file_id_str = str(file_obj['_id'])
        project_id = file_obj.get('source_project_id') or project_id
        filepath = file_obj.get('filepath') or file_obj.get('filename')

        # ====================== جلب النسخ ======================
        versions = list(db['project_versions'].find(
            {"project_id": project_id},
            sort=[("version_number", -1)]
        ))

        history = []

        for ver in versions:
            version_number = ver["version_number"]
            version_id = str(ver["_id"])  # ✅ أخذ version_id من النسخة
            file_changes = ver.get("file_changes", [])

            found = False
            for change in file_changes:
                if str(change.get("file_id")) == file_id_str or change.get("filepath") == filepath:
                    history.append({
                        "version_number": version_number,
                        "version_id": version_id,  # ✅ بدل file_id
                        "status": change.get("status", "unknown"),
                        "filename": change.get("filename"),
                        "filepath": change.get("filepath"),
                        "created_at": ver.get("created_at").isoformat() if ver.get("created_at") else None,
                    })
                    found = True
                    break

            if not found:
                # ملف موجود لكنه unchanged
                if any(str(fid) == file_id_str for fid in ver.get("file_ids", [])):
                    history.append({
                        "version_number": version_number,
                        "version_id": version_id,  # ✅ بدل file_id
                        "status": "unchanged",
                        "filename": file_obj.get("filename"),
                        "filepath": filepath,
                        "created_at": ver.get("created_at").isoformat() if ver.get("created_at") else None,
                    })

        return Response({
            "success": True,
            "file_id": file_id_str,  # ✅ تصحيح الاسم هنا (كان version_id خطأ)
            "filename": file_obj.get("filename"),
            "filepath": filepath,
            "project_id": project_id,
            "total_versions": len(history),
            "history": history
        })


# ══════════════════════════════════════════════════════════════════════════════
# جلب ملفات التوثيق المرتبطة بملف كود — لاستخدامها في كشف التناقض (code-doc)
# GET /api/analysis/file-docs/<file_id>/
# ══════════════════════════════════════════════════════════════════════════════

class FileDocsView(APIView):
    """
    يرجع جميع ملفات التوثيق (AI Explanations) المرتبطة بملف كود معين.

    الهدف: يستخدمها الـ frontend لعرض قائمة التوثيقات المتاحة
    عند اختيار نوع كشف التناقض code-doc، ليختار المستخدم
    أي نسخة توثيق يريد مقارنتها مع الكود.

    GET /api/analysis/file-docs/<file_id>/
    Response:
    {
        "success": true,
        "file_id": "...",
        "filename": "...",
        "total_docs": 2,
        "docs": [
            {
                "doc_id": "...",           ← explanation_id (يُرسل كـ doc_version_id في كشف التناقض)
                "explanation_type": "high_level" | "low_level" | "technical_report",
                "analysis_id": "...",
                "created_at": "...",
                "content_preview": "..."   ← أول 200 حرف من المحتوى
            },
            ...
        ]
    }
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [AllowAny]

    def get(self, request, file_id: str):
        db = get_mongo_db()
        if db is None:
            return Response({"error": "Database connection failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # ── 1. التحقق من وجود الملف ───────────────────────────────────────
        try:
            file_obj = db[settings.CODE_FILES_COLLECTION].find_one({"_id": ObjectId(file_id)})
        except Exception:
            return Response({"error": "معرّف الملف غير صالح"}, status=status.HTTP_400_BAD_REQUEST)

        if not file_obj:
            return Response({"error": "الملف غير موجود"}, status=status.HTTP_404_NOT_FOUND)

        # ── 2. جلب جميع نتائج التحليل لهذا الملف ────────────────────────
        analysis_collection = db[settings.ANALYSIS_RESULTS_COLLECTION]
        analyses = list(analysis_collection.find(
            {"code_file_id": ObjectId(file_id), "status": "COMPLETED"},
            {"_id": 1},
            sort=[("created_at", -1)]
        ))
        analysis_ids = [a["_id"] for a in analyses]

        if not analysis_ids:
            return Response({
                "success": True,
                "file_id": file_id,
                "filename": file_obj.get("filename"),
                "total_docs": 0,
                "docs": [],
                "message": "لا يوجد توثيق مرتبط بهذا الملف — تأكد من تشغيل التحليل أولاً"
            })

        # ── 3. جلب التوثيقات من ai_explanations ─────────────────────────
        explanations_collection = db[getattr(settings, 'AI_EXPLANATIONS_COLLECTION', 'ai_explanations')]
        explanations = list(explanations_collection.find(
            {"analysis_id": {"$in": analysis_ids}},
            sort=[("created_at", -1)]
        ))

        docs = []
        for exp in explanations:
            content = exp.get("content") or exp.get("explanation") or ""
            docs.append({
                "doc_id":           str(exp["_id"]),          # يُرسل كـ doc_version_id
                "explanation_type": exp.get("explanation_type") or exp.get("exp_type", "high_level"),
                "analysis_id":      str(exp["analysis_id"]) if exp.get("analysis_id") else None,
                "created_at":       exp["created_at"].isoformat() if exp.get("created_at") else None,
                "content_preview":  content[:200] if content else None,
            })

        return Response({
            "success":    True,
            "file_id":    file_id,
            "filename":   file_obj.get("filename"),
            "filepath":   file_obj.get("filepath"),
            "total_docs": len(docs),
            "docs":       docs,
        })