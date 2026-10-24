# core_ai/views/conflict_views.py
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from bson import ObjectId
from typing import Optional
from celery.result import AsyncResult
from django.conf import settings

from core_ai.mongo_utils import get_mongo_db, get_conflict_reports_collection
from core_ai.celery_tasks.conflict_tasks import detect_conflict_task

logger = logging.getLogger(__name__)

AI_EXPLANATIONS_COLLECTION = getattr(settings, 'AI_EXPLANATIONS_COLLECTION', 'ai_explanations')


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

def _resolve_analysis_id(db, file_id: str) -> Optional[str]:
    """يجلب آخر analysis مكتمل لـ file_id."""
    try:
        result = db[settings.ANALYSIS_RESULTS_COLLECTION].find_one(
            {"code_file_id": ObjectId(file_id), "status": "COMPLETED"},
            sort=[("created_at", -1)]
        )
        return str(result["_id"]) if result else None
    except Exception:
        return None


def _resolve_doc_id(db, file_id: str) -> Optional[str]:
    """يجلب آخر توثيق مرتبط بـ file_id (عبر analysis)."""
    try:
        analysis = db[settings.ANALYSIS_RESULTS_COLLECTION].find_one(
            {"code_file_id": ObjectId(file_id), "status": "COMPLETED"},
            sort=[("created_at", -1)]
        )
        if not analysis:
            return None
        doc = db[AI_EXPLANATIONS_COLLECTION].find_one(
            {"analysis_id": analysis["_id"]},
            sort=[("created_at", -1)]
        )
        return str(doc["_id"]) if doc else None
    except Exception:
        return None


def _extract_file_id_from_version(version: dict, filepath: Optional[str]) -> Optional[str]:
    """يستخرج file_id من project_version بناءً على filepath أو أول ملف متغيّر."""
    changes = version.get("file_changes", [])
    if filepath:
        match = next(
            (c for c in changes if c.get("filepath") == filepath or c.get("filename") == filepath),
            None
        )
    else:
        match = (
            next((c for c in changes if c.get("status") != "unchanged"), None)
            or (changes[0] if changes else None)
        )
    return str(match["file_id"]) if match and match.get("file_id") else None


# ══════════════════════════════════════════════════════════════════════════════
# Unified Conflict Detection
# POST /api/analysis/detect-conflict/
#
# Body:
# {
#   "analysis_type": "code_vs_code" | "code_vs_doc" | "full_analysis",
#   "project_id": "...",
#
#   // طريقة 1: project_versions
#   "version_id_1": "...",
#   "version_id_2": "...",   (code_vs_code / full_analysis)
#   "filepath": "...",       (اختياري)
#
#   // طريقة 2: file_id مباشرة
#   "file_id": "...",
#   "version_a_id": "...",   (code_vs_code / full_analysis)
#   "version_b_id": "...",   (code_vs_code / full_analysis)
#   "version_id": "...",     (code_vs_doc فقط)
#
#   // التوثيق — يعمل مع الطريقتين
#   "doc_version_id": "..."  (اختياري — يُجلب تلقائياً إذا غاب)
# }
# ══════════════════════════════════════════════════════════════════════════════

class ConflictDetectionView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        db = get_mongo_db()
        if db is None:
            return Response({"error": "Database connection failed"}, status=500)

        data          = request.data
        analysis_type = data.get("analysis_type", "code_vs_code")
        project_id    = data.get("project_id", "")

        if analysis_type not in ("code_vs_code", "code_vs_doc", "full_analysis"):
            return Response(
                {"error": f"analysis_type غير صالح: '{analysis_type}'. "
                          "القيم المقبولة: code_vs_code, code_vs_doc, full_analysis"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if data.get("version_id_1"):
            return self._handle_via_project_versions(db, data, analysis_type, project_id)
        else:
            return self._handle_via_file_id(db, data, analysis_type, project_id)

    # ──────────────────────────────────────────────────────────────────────────
    # الطريقة 1: project_versions
    # ──────────────────────────────────────────────────────────────────────────
    def _handle_via_project_versions(self, db, data, analysis_type, project_id):
        version_id_1   = data.get("version_id_1")
        version_id_2   = data.get("version_id_2")
        filepath       = data.get("filepath")
        doc_version_id = data.get("doc_version_id")

        if analysis_type in ("code_vs_code", "full_analysis") and not version_id_2:
            return Response(
                {"error": "version_id_2 مطلوب لـ code_vs_code و full_analysis"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # جلب النسخ
        try:
            version_1 = db["project_versions"].find_one({"_id": ObjectId(version_id_1)})
        except Exception as e:
            return Response({"error": f"version_id_1 غير صالح: {e}"}, status=400)
        if not version_1:
            return Response({"error": "النسخة الأولى غير موجودة"}, status=404)

        project_id = project_id or version_1.get("project_id", "")

        version_2 = None
        if version_id_2:
            try:
                version_2 = db["project_versions"].find_one({"_id": ObjectId(version_id_2)})
            except Exception as e:
                return Response({"error": f"version_id_2 غير صالح: {e}"}, status=400)
            if not version_2:
                return Response({"error": "النسخة الثانية غير موجودة"}, status=404)
            if version_1.get("project_id") != version_2.get("project_id"):
                return Response({"error": "النسختان تنتميان لمشروعين مختلفين"}, status=400)

        # استخراج file_ids
        file_id_a = _extract_file_id_from_version(version_1, filepath)
        if not file_id_a:
            return Response({"error": "لم يتم العثور على ملف في النسخة الأولى"}, status=404)

        file_id_b = _extract_file_id_from_version(version_2, filepath) if version_2 else None
        if analysis_type in ("code_vs_code", "full_analysis") and not file_id_b:
            return Response({"error": "لم يتم العثور على ملف في النسخة الثانية"}, status=404)

        # resolve analysis IDs
        analysis_a_id = _resolve_analysis_id(db, file_id_a)
        if not analysis_a_id:
            return Response(
                {"error": f"لا يوجد تحليل مكتمل للنسخة الأولى (file_id: {file_id_a})"},
                status=404
            )

        analysis_b_id = None
        if file_id_b:
            analysis_b_id = _resolve_analysis_id(db, file_id_b)
            if not analysis_b_id:
                return Response(
                    {"error": f"لا يوجد تحليل مكتمل للنسخة الثانية (file_id: {file_id_b})"},
                    status=404
                )

        # resolve doc
        explanation_id = None
        if analysis_type in ("code_vs_doc", "full_analysis"):
            explanation_id = doc_version_id or _resolve_doc_id(db, file_id_a)
            if analysis_type == "code_vs_doc" and not explanation_id:
                return Response(
                    {"error": "لم يتم العثور على توثيق — أرسل doc_version_id أو تأكد من وجود توثيق للملف"},
                    status=404
                )

        task = detect_conflict_task.delay(
            analysis_type=analysis_type,
            analysis_a_id=analysis_a_id,
            analysis_b_id=analysis_b_id,
            explanation_id=explanation_id,
            metadata={
                "project_id":      project_id,
                "file_id":         file_id_a,
                "version_a_id":    file_id_a,
                "version_b_id":    file_id_b,
                "version_id_1":    version_id_1,
                "version_id_2":    version_id_2,
                "filepath":        filepath,
                "doc_version_id":  explanation_id,
                "doc_auto_fetched": not bool(doc_version_id) and bool(explanation_id),
            }
        )

        resp = {
            "task_id":       task.id,
            "message":       "تم بدء كشف التناقض",
            "status":        "PROCESSING",
            "analysis_type": analysis_type,
            "version_id_1":  version_id_1,
            "file_id_a":     file_id_a,
        }
        if version_id_2:
            resp["version_id_2"] = version_id_2
            resp["file_id_b"]    = file_id_b
        if explanation_id:
            resp["doc_version_id"] = explanation_id

        return Response(resp, status=status.HTTP_202_ACCEPTED)

    # ──────────────────────────────────────────────────────────────────────────
    # الطريقة 2: file_id مباشرة
    # ──────────────────────────────────────────────────────────────────────────
    def _handle_via_file_id(self, db, data, analysis_type, project_id):
        file_id        = data.get("file_id")
        version_a_id   = data.get("version_a_id")
        version_b_id   = data.get("version_b_id")
        version_id     = data.get("version_id")
        doc_version_id = data.get("doc_version_id")

        if not file_id:
            return Response(
                {"error": "يجب إرسال file_id أو version_id_1"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if analysis_type in ("code_vs_code", "full_analysis") and not (version_a_id and version_b_id):
            return Response(
                {"error": "version_a_id و version_b_id مطلوبان لـ code_vs_code و full_analysis"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if analysis_type == "code_vs_doc" and not version_id:
            return Response(
                {"error": "version_id مطلوب لـ code_vs_doc"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # resolve analysis IDs
        primary_file = version_a_id or version_id
        analysis_a_id = _resolve_analysis_id(db, primary_file)
        if not analysis_a_id:
            return Response({"error": "لم يتم العثور على تحليل مكتمل للنسخة الأولى"}, status=404)

        analysis_b_id = None
        if version_b_id:
            analysis_b_id = _resolve_analysis_id(db, version_b_id)
            if not analysis_b_id:
                return Response({"error": "لم يتم العثور على تحليل مكتمل للنسخة الثانية"}, status=404)

        # resolve doc
        explanation_id = None
        if analysis_type in ("code_vs_doc", "full_analysis"):
            explanation_id = doc_version_id or _resolve_doc_id(db, version_id or version_a_id)
            if analysis_type == "code_vs_doc" and not explanation_id:
                return Response(
                    {"error": "لم يتم العثور على توثيق — أرسل doc_version_id أو تأكد من وجود توثيق"},
                    status=404
                )

        task = detect_conflict_task.delay(
            analysis_type=analysis_type,
            analysis_a_id=analysis_a_id,
            analysis_b_id=analysis_b_id,
            explanation_id=explanation_id,
            metadata={
                "project_id":      project_id,
                "file_id":         file_id,
                "version_a_id":    version_a_id,
                "version_b_id":    version_b_id,
                "version_id":      version_id,
                "doc_version_id":  explanation_id,
                "doc_auto_fetched": not bool(doc_version_id) and bool(explanation_id),
            }
        )

        resp = {
            "task_id":       task.id,
            "message":       "تم بدء كشف التناقض",
            "status":        "PROCESSING",
            "analysis_type": analysis_type,
            "file_id":       file_id,
        }
        if analysis_b_id:
            resp["version_b_id"] = version_b_id
        if explanation_id:
            resp["doc_version_id"] = explanation_id

        return Response(resp, status=status.HTTP_202_ACCEPTED)


# ══════════════════════════════════════════════════════════════════════════════
# Status
# GET /api/analysis/conflict-status/<task_id>/
# GET /api/analysis/conflict-status/?task_id=...
# ══════════════════════════════════════════════════════════════════════════════

class ConflictStatusView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [AllowAny]

    def get(self, request, task_id=None):
        tid = task_id or request.query_params.get("task_id")
        if not tid:
            return Response({"error": "task_id مطلوب"}, status=400)

        result   = AsyncResult(tid)
        response = {"task_id": tid, "state": result.state}
        if result.state == "SUCCESS":
            response["report_id"] = result.result.get("report_id") if isinstance(result.result, dict) else None
        elif result.state == "FAILURE":
            response["error"] = str(result.result)
        return Response(response)


# ══════════════════════════════════════════════════════════════════════════════
# Result
# GET /api/analysis/conflict-result/<report_id>/
# ══════════════════════════════════════════════════════════════════════════════

class ConflictResultView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [AllowAny]

    def get(self, request, analysis_id: str):
        db = get_mongo_db()
        if db is None:
            return Response({"error": "Database connection failed"}, status=500)

        try:
            report = get_conflict_reports_collection().find_one({"_id": ObjectId(analysis_id)})
        except Exception:
            report = None

        if not report:
            return Response({"error": "التقرير غير موجود"}, status=404)

        return self._format_report(report)

    def _format_report(self, report):
        report["_id"]  = str(report["_id"])
        summary_detail = report.pop("summary_detail", {}) or {}
        analysis_type  = report.get("analysis_type", "")

        summary = {
            "similarity_percentage": summary_detail.get("similarity_percentage", 0.0),
            "total_changes":         summary_detail.get("total_changes", 0),
            "total_conflicts":       report.get("total_conflicts", 0),
            "breaking_changes":      report.get("breaking_changes_count", 0),
            "grade":                 report.get("grade", "B"),
            "stats":                 summary_detail.get("stats", {}),
        }

        if analysis_type == "code_vs_doc":
            summary.update({
                "compatibility_score":     summary_detail.get("compatibility_score", report.get("compatibility_score")),
                "coverage_percentage":     summary_detail.get("coverage_percentage", 0.0),
                "total_elements_analyzed": summary_detail.get("total_elements_analyzed", 0),
                "fully_documented":        summary_detail.get("fully_documented", 0),
                "partially_documented":    summary_detail.get("partially_documented", 0),
                "undocumented":            summary_detail.get("undocumented", 0),
                "critical_conflicts":      summary_detail.get("critical_conflicts", 0),
            })

        if analysis_type == "full_analysis":
            if report.get("compatibility_score"):
                summary["compatibility_score"] = report.get("compatibility_score")
            all_c = (
                report.get("structural_conflicts", []) +
                report.get("semantic_conflicts", []) +
                report.get("doc_conflicts", [])
            )
            summary["critical_conflicts"] = sum(
                1 for c in all_c if c.get("severity") in ("critical", "high")
            )

        doc_conflicts = report.get("doc_conflicts", [])
        conflicts = {
            "structural":    report.get("structural_conflicts", []),
            "semantic":      report.get("semantic_conflicts", []),
            "documentation": [c for c in doc_conflicts if c.get("class_name") != "Overall"],
        }

        response = {
            "status":                 "success",
            "message":                report.get("message") or f"تم تحليل {analysis_type} بنجاح",
            "analysis_id":            report["_id"],
            "analysis_type":          analysis_type,
            "completed_at":           str(report.get("completed_at", "")),
            "execution_time_seconds": report.get("execution_time_seconds"),
            "task_id":                report.get("task_id"),
            "metadata":               report.get("metadata"),
            "summary":                summary,
            "conflicts":              conflicts,
            "changes":                report.get("changes", {}),
            "suggestions":            report.get("suggestions", []),
            "visual_representation":  report.get("visual_representation", {}),
            "summary_text":           report.get("summary", ""),
            "compatibility_score":    report.get("compatibility_score"),
        }

        if analysis_type in ("code_vs_doc", "full_analysis"):
            response["export_formats"] = report.get("export_formats", ["pdf", "markdown", "html", "json"])

        if analysis_type == "code_vs_doc":
            response["undocumented_elements"] = report.get("undocumented_elements", [])

        if analysis_type == "full_analysis":
            if report.get("cross_reference_analysis"):
                response["cross_reference_analysis"] = report.get("cross_reference_analysis")
            if report.get("migration_guide"):
                response["migration_guide"] = report.get("migration_guide")

        return Response(response)


# ══════════════════════════════════════════════════════════════════════════════
# History
# GET /api/analysis/conflict-history/?project_id=...
# GET /api/analysis/conflict-history/?file_id=...
# GET /api/analysis/conflict-history/?version_id=...
# ══════════════════════════════════════════════════════════════════════════════

class ConflictHistoryView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [AllowAny]

    def get(self, request):
        db = get_mongo_db()
        if db is None:
            return Response({"error": "Database connection failed"}, status=500)

        project_id = request.query_params.get("project_id")
        file_id    = request.query_params.get("file_id")
        version_id = request.query_params.get("version_id")

        if not any([project_id, file_id, version_id]):
            return Response(
                {"error": "يجب توفير project_id أو file_id أو version_id"},
                status=400
            )

        try:
            collection = get_conflict_reports_collection()
            query = {}
            if project_id:
                query["project_id"] = project_id
            if file_id:
                query["file_id"] = file_id
            if version_id:
                query["$or"] = [
                    {"version_a_id": version_id},
                    {"version_b_id": version_id},
                    {"metadata.versions.version_a.version_id": version_id},
                    {"metadata.versions.version_b.version_id": version_id},
                ]

            cursor  = collection.find(query).sort("completed_at", -1)
            reports = list(cursor)
            for r in reports:
                r["_id"] = str(r["_id"])

            return Response({"count": len(reports), "results": reports})
        except Exception as e:
            return Response({"error": str(e)}, status=500)
