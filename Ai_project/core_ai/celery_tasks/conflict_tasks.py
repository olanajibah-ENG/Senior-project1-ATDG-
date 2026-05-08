# core_ai/celery_tasks/conflict_tasks.py
import logging
from celery import shared_task
from bson import ObjectId
from datetime import datetime
from typing import Optional, Dict, Any

from core_ai.services.conflict_detection.orchestrator import ConflictOrchestrator
from core_ai.mongo_utils import get_mongo_db, save_conflict_report, update_conflict_report
from django.conf import settings

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _get_analysis(analysis_id: str) -> dict:
    db = get_mongo_db()
    if db is None:
        raise Exception("MongoDB connection failed")
    result = db[settings.ANALYSIS_RESULTS_COLLECTION].find_one({"_id": ObjectId(analysis_id)})
    if not result:
        raise Exception(f"AnalysisResult not found: {analysis_id}")
    result["_id"] = str(result["_id"])
    return result


def _get_explanation(explanation_id: str) -> dict:
    db = get_mongo_db()
    if db is None:
        raise Exception("MongoDB connection failed")
    result = db[settings.AI_EXPLANATIONS_COLLECTION].find_one({"_id": ObjectId(explanation_id)})
    if not result:
        raise Exception(f"AIExplanation not found: {explanation_id}")
    result["_id"] = str(result["_id"])
    return result


def _get_codefile(file_id: str) -> dict:
    """يجلب CodeFile من MongoDB"""
    db = get_mongo_db()
    if db is None:
        return {}
    try:
        result = db[settings.CODE_FILES_COLLECTION].find_one({"_id": ObjectId(file_id)})
        if result:
            result["_id"] = str(result["_id"])
            return result
    except Exception:
        pass
    return {}


def _get_classes_from_analysis(analysis: dict) -> dict:
    """يستخرج الكلاسات من class_diagram_data"""
    diagram = analysis.get("class_diagram_data", {})
    if isinstance(diagram, dict):
        classes_list = diagram.get("classes", [])
    else:
        classes_list = []
    return {c["name"]: c for c in classes_list if isinstance(c, dict) and "name" in c}


def _calculate_stats(analysis_a: dict, analysis_b: dict) -> dict:
    """يحسب إحصائيات الفروق بين النسختين"""
    try:
        classes_a = _get_classes_from_analysis(analysis_a)
        classes_b = _get_classes_from_analysis(analysis_b)

        classes_added   = len(set(classes_b) - set(classes_a))
        classes_removed = len(set(classes_a) - set(classes_b))

        methods_a = set()
        methods_b = set()
        for name, cls in classes_a.items():
            for m in cls.get("methods", []):
                methods_a.add(f"{name}.{m.get('name','')}")
        for name, cls in classes_b.items():
            for m in cls.get("methods", []):
                methods_b.add(f"{name}.{m.get('name','')}")

        methods_added   = len(methods_b - methods_a)
        methods_removed = len(methods_a - methods_b)
        methods_common  = methods_a & methods_b

        # similarity
        total = len(methods_a | methods_b)
        similarity = round((len(methods_common) / total * 100), 1) if total > 0 else 100.0

        return {
            "similarity_percentage": similarity,
            "classes_added":    classes_added,
            "classes_removed":  classes_removed,
            "methods_added":    methods_added,
            "methods_removed":  methods_removed,
            "methods_modified": 0,
            "lines_added":      methods_added * 3,
            "lines_deleted":    methods_removed * 3,
            "lines_modified":   0,
        }
    except Exception as e:
        logger.warning(f"Stats calculation failed: {e}")
        return {
            "similarity_percentage": 0.0,
            "classes_added": 0, "classes_removed": 0,
            "methods_added": 0, "methods_removed": 0, "methods_modified": 0,
            "lines_added": 0,   "lines_deleted": 0,   "lines_modified": 0,
        }


def _build_class_diagram_changes(analysis_a: dict, analysis_b: dict) -> dict:
    """يبني class_diagram_changes"""
    try:
        classes_a = _get_classes_from_analysis(analysis_a)
        classes_b = _get_classes_from_analysis(analysis_b)

        classes_added = []
        for name in set(classes_b) - set(classes_a):
            cls = classes_b[name]
            classes_added.append({
                "class_name": name,
                "attributes": [a.get("name", "") for a in cls.get("attributes", [])],
                "methods":    [f"{m.get('name','')}()" for m in cls.get("methods", [])]
            })

        classes_removed = []
        for name in set(classes_a) - set(classes_b):
            classes_removed.append({"class_name": name})

        classes_modified = []
        for name in set(classes_a) & set(classes_b):
            cls_a = classes_a[name]
            cls_b = classes_b[name]
            methods_a = {m.get("name") for m in cls_a.get("methods", [])}
            methods_b = {m.get("name") for m in cls_b.get("methods", [])}
            added   = list(methods_b - methods_a)
            removed = list(methods_a - methods_b)
            if added or removed:
                entry = {"class_name": name}
                if added:   entry["methods_added"]   = added
                if removed: entry["methods_removed"] = removed
                classes_modified.append(entry)

        return {
            "classes_added":    classes_added,
            "classes_removed":  classes_removed,
            "classes_modified": classes_modified,
            "relationships_changed": []
        }
    except Exception as e:
        logger.warning(f"Class diagram changes failed: {e}")
        return {"classes_added": [], "classes_removed": [], "classes_modified": [], "relationships_changed": []}


def _build_mermaid(class_diagram_changes: dict) -> str:
    """يبني Mermaid class diagram"""
    lines = ["classDiagram"]
    for cls in class_diagram_changes.get("classes_added", []):
        lines.append(f"    class {cls['class_name']} {{")
        for m in cls.get("methods", []):
            lines.append(f"        +{m}")
        lines.append("    }")
    for cls in class_diagram_changes.get("classes_modified", []):
        lines.append(f"    class {cls['class_name']} {{")
        for m in cls.get("methods_added", []):
            lines.append(f"        +{m}() [added]")
        for m in cls.get("methods_removed", []):
            lines.append(f"        -{m}() [removed]")
        lines.append("    }")
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# Celery Task
# ──────────────────────────────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=3)
def detect_conflict_task(
    self,
    analysis_type: str = "code_vs_code",
    analysis_a_id: Optional[str] = None,
    analysis_b_id: Optional[str] = None,
    explanation_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    metadata = metadata or {}

    report_id = save_conflict_report({
        "analysis_type":  analysis_type,
        "analysis_a_id":  analysis_a_id,
        "analysis_b_id":  analysis_b_id,
        "explanation_id": explanation_id,
        "project_id":     metadata.get("project_id"),
        "file_id":        metadata.get("file_id"),
        "version_a_id":   metadata.get("version_a_id"),
        "version_b_id":   metadata.get("version_b_id"),
        "doc_version_id": metadata.get("doc_version_id"),
        "status":         "pending",
        "created_at":     datetime.utcnow(),
        "task_id":        self.request.id,
    })

    try:
        start_time = datetime.utcnow()

        # ── CODE VS CODE ──────────────────────────────────
        if analysis_type == "code_vs_code":
            if not analysis_a_id or not analysis_b_id:
                raise ValueError("analysis_a_id و analysis_b_id مطلوبان لـ code_vs_code")
            analysis_a = _get_analysis(analysis_a_id)
            analysis_b = _get_analysis(analysis_b_id)
            result = ConflictOrchestrator.run_code_vs_code(analysis_a, analysis_b, metadata)

        # ── CODE VS DOC ───────────────────────────────────
        elif analysis_type == "code_vs_doc":
            if not analysis_a_id:
                raise ValueError("analysis_a_id مطلوب لـ code_vs_doc")
            if not explanation_id:
                raise ValueError("explanation_id مطلوب لـ code_vs_doc")
            analysis_a = _get_analysis(analysis_a_id)
            analysis_b = {}
            explanation = _get_explanation(explanation_id)
            result = ConflictOrchestrator.run_code_vs_doc(analysis_a, explanation, metadata)

        # ── FULL ANALYSIS ─────────────────────────────────
        elif analysis_type == "full_analysis":
            if not analysis_a_id or not analysis_b_id:
                raise ValueError("analysis_a_id و analysis_b_id مطلوبان لـ full_analysis")
            analysis_a  = _get_analysis(analysis_a_id)
            analysis_b  = _get_analysis(analysis_b_id)
            explanation = _get_explanation(explanation_id) if explanation_id else None
            result = ConflictOrchestrator.run_full_analysis(analysis_a, analysis_b, explanation, metadata)

        else:
            raise ValueError(f"analysis_type غير معروف: {analysis_type}")

        execution_time = (datetime.utcnow() - start_time).total_seconds()

        # ── جلب بيانات الملف ──────────────────────────────
        file_id   = metadata.get("file_id", "")
        codefile  = _get_codefile(file_id) if file_id else {}
        file_name = codefile.get("filename") or codefile.get("file_name") or "Unknown File"
        file_path = codefile.get("filepath") or codefile.get("file_path") or ""
        project_name = codefile.get("project_name") or "Unknown Project"

        # ── حساب الإحصائيات ──────────────────────────────
        analysis_b_data = analysis_b if analysis_type != "code_vs_doc" else {}
        stats = _calculate_stats(analysis_a, analysis_b_data)
        class_diagram_changes = _build_class_diagram_changes(analysis_a, analysis_b_data)
        mermaid_code = _build_mermaid(class_diagram_changes)

        all_conflicts = (
            getattr(result, 'structural_conflicts', []) +
            getattr(result, 'semantic_conflicts', []) +
            getattr(result, 'doc_conflicts', [])
        )

        # ── بناء الـ metadata الكامل ──────────────────────
        full_metadata = {
            "project": {
                "project_id":   metadata.get("project_id", ""),
                "project_name": project_name,
            },
            "file": {
                "file_id":   file_id,
                "file_name": file_name,
                "file_path": file_path,
            },
            "versions": {
                "version_a": {
                    "version_id":     metadata.get("version_a_id", ""),
                    "version_number": "v1",
                    "role": "reference"
                },
                "version_b": {
                    "version_id":     metadata.get("version_b_id", ""),
                    "version_number": "v2",
                    "role": "comparison"
                },
            } if metadata.get("version_b_id") else None
        }

        # ── بناء summary الكامل ──────────────────────────
        total_conflicts   = getattr(result, 'total_conflicts', 0)
        breaking_count    = getattr(result, 'breaking_changes_count', 0)
        full_summary = {
            "similarity_percentage": stats["similarity_percentage"],
            "total_changes":         len(getattr(result, 'structural_conflicts', [])),
            "total_conflicts":       total_conflicts,
            "breaking_changes":      breaking_count,
            "grade":                 getattr(result, 'grade', 'B'),
            "stats": {
                "lines_added":      stats["lines_added"],
                "lines_deleted":    stats["lines_deleted"],
                "lines_modified":   stats["lines_modified"],
                "classes_added":    stats["classes_added"],
                "classes_removed":  stats["classes_removed"],
                "methods_added":    stats["methods_added"],
                "methods_removed":  stats["methods_removed"],
                "methods_modified": stats["methods_modified"],
            }
        }

        # ── بناء changes ─────────────────────────────────
        changes = {
            "diffs": [
                {
                    "diff_id":     f"diff_{i+1:03d}",
                    "type":        c.type.value if hasattr(c.type, 'value') else str(c.type),
                    "category":    c.category or "",
                    "class_name":  c.class_name,
                    "member":      c.member or "",
                    "old_value":   c.old_value or "",
                    "new_value":   c.new_value or "",
                    "explanation": c.description,
                }
                for i, c in enumerate(getattr(result, 'structural_conflicts', []))
            ],
            "class_diagram_changes": class_diagram_changes,
        }

        # ── حفظ النتيجة الكاملة ──────────────────────────
        # ── استخراج إحصائيات code_vs_doc ─────────────────
        doc_stats = {}
        undocumented_elements = []
        if analysis_type == "code_vs_doc":
            overall_item = next(
                (c for c in getattr(result, 'doc_conflicts', []) if c.class_name == "Overall"),
                None
            )
            if overall_item and overall_item.element:
                el = overall_item.element
                doc_stats = {
                    "compatibility_score":  el.get("compatibility_score", 0),
                    "coverage_percentage":  el.get("coverage_percentage", 0),
                    "total_elements_analyzed": el.get("total_elements", 0),
                    "fully_documented":     el.get("fully_documented", 0),
                    "partially_documented": el.get("partially_documented", 0),
                    "undocumented":         el.get("undocumented", 0),
                    "critical_conflicts":   el.get("critical_conflicts", 0),
                }
                for cls_name in el.get("undocumented_classes", []):
                    undocumented_elements.append({
                        "type": "class", "name": cls_name,
                        "class_name": cls_name, "priority": "high",
                        "suggestion": f"إضافة توثيق كامل للكلاس {cls_name}"
                    })
                for item in el.get("undocumented_methods", []):
                    undocumented_elements.append({
                        "type": "method", "name": item["method"],
                        "class_name": item["class"], "priority": "medium",
                        "suggestion": f"إضافة توثيق للدالة {item['method']}"
                    })

        # ── بناء metadata الكامل لـ code_vs_doc و full_analysis ──────────
        if analysis_type in ("code_vs_doc", "full_analysis") and metadata.get("doc_version_id"):
            full_metadata["documentation"] = {
                "doc_id":            metadata.get("doc_version_id", ""),
                "doc_version_id":    metadata.get("doc_version_id", ""),
                "file_name":         "AI Generated Documentation",
                "type":              "high_level",
                "linked_to_version": "v1",
                "auto_fetched":      metadata.get("doc_auto_fetched", False),
            }
        if analysis_type == "code_vs_doc":
            full_metadata["code"] = {
                "file_id":        file_id,
                "file_name":      file_name,
                "version_id":     metadata.get("version_id", ""),
                "version_number": "v1",
            }

        # ── بناء cross_reference_analysis لـ full_analysis ──────────
        cross_reference = None
        migration_guide = None
        if analysis_type == "full_analysis":
            doc_conflicts = getattr(result, 'doc_conflicts', [])
            undoc_methods = [
                c for c in doc_conflicts
                if c.class_name != "Overall" and c.member
            ]
            cross_reference = {
                "changes_affecting_documentation": [
                    {
                        "change":                f"{c.member} in {c.class_name} changed",
                        "documentation_impact":   c.description,
                        "action_required":        c.suggestion or "تحديث التوثيق"
                    }
                    for c in getattr(result, 'structural_conflicts', [])[:3]
                    if c.type.value in ("breaking_change",) if hasattr(c.type, 'value')
                ],
                "undocumented_new_features": [
                    {
                        "feature":     f"{c.member} in {c.class_name}",
                        "description": c.description,
                        "priority":    c.severity.value if hasattr(c.severity, 'value') else "medium"
                    }
                    for c in undoc_methods[:5]
                ]
            }
            # بناء migration guide من الـ structural conflicts
            breaking = [c for c in getattr(result, 'structural_conflicts', [])
                        if hasattr(c.type, 'value') and c.type.value == "breaking_change"]
            if breaking:
                steps = []
                for i, c in enumerate(breaking[:5]):
                    steps.append({
                        "step":     i + 1,
                        "action":   c.suggestion or c.description,
                        "old_value": c.old_value or "",
                        "new_value": c.new_value or "",
                        "breaking": True
                    })
                migration_guide = {
                    "available":    True,
                    "from_version": "v1",
                    "to_version":   "v2",
                    "steps":        steps
                }

        update_conflict_report(report_id, {
            "status":                 "completed",
            "structural_conflicts":   [c.model_dump() for c in getattr(result, 'structural_conflicts', [])],
            "semantic_conflicts":     [c.model_dump() for c in getattr(result, 'semantic_conflicts', [])],
            "doc_conflicts":          [c.model_dump() for c in getattr(result, 'doc_conflicts', [])],
            "summary":                getattr(result, 'summary', ''),
            "breaking_changes_count": breaking_count,
            "compatibility_score":    doc_stats.get("compatibility_score") or getattr(result, 'compatibility_score', None),
            "total_conflicts":        total_conflicts,
            "grade":                  getattr(result, 'grade', 'B'),
            "suggestions":            getattr(result, 'suggestions', []),
            "completed_at":           datetime.utcnow(),
            "execution_time_seconds": execution_time,
            # ── حقول جديدة ──
            "metadata":               full_metadata,
            "summary_detail":         {**full_summary, **doc_stats},
            "changes":                changes,
            "undocumented_elements":  undocumented_elements,
            "export_formats":         ["pdf", "markdown", "html", "json"],
            "cross_reference_analysis": cross_reference,
            "migration_guide":          migration_guide,
            "visual_representation": {
                "mermaid_code": mermaid_code,
                "svg_url":      f"/api/analysis/diagrams/{report_id}.svg"
            },
        })

        logger.info(
            f"✅ Conflict detection done. type={analysis_type} "
            f"report_id={report_id} time={execution_time:.1f}s "
            f"conflicts={total_conflicts}"
        )

        return {
            "status":          "completed",
            "report_id":       report_id,
            "total_conflicts": total_conflicts,
            "grade":           getattr(result, 'grade', 'B'),
        }

    except Exception as exc:
        logger.error(f"❌ Conflict task failed: {exc}")
        update_conflict_report(report_id, {
            "status": "failed",
            "error":  str(exc)
        })
        raise self.retry(exc=exc, countdown=10)