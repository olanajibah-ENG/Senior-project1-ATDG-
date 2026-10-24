# core_ai/services/conflict_detection/report_generator.py
from typing import List, Optional, Dict, Any
from datetime import datetime
from .schemas import (
    ConflictAnalysisResult, ConflictItem, UnifiedClassDiagram,
    AnalysisType, SeverityLevel, ConflictMetadata,
    ProjectMetadata, FileMetadata, VersionMetadata, DocMetadata
)


class ReportGenerator:
    """يولد التقرير النهائي من نتائج التحليل"""

    @staticmethod
    def generate(
        analysis_type: str,
        version_a: str,
        diagram_a: UnifiedClassDiagram,
        version_b: Optional[str] = None,
        diagram_b: Optional[UnifiedClassDiagram] = None,
        structural_changes: Optional[List[ConflictItem]] = None,
        semantic_conflicts: Optional[List[ConflictItem]] = None,
        doc_conflicts: Optional[List[ConflictItem]] = None,
        compatibility_score: Optional[float] = None,
        summary: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConflictAnalysisResult:

        structural_changes = structural_changes or []
        semantic_conflicts = semantic_conflicts or []
        doc_conflicts      = doc_conflicts      or []

        all_conflicts = structural_changes + semantic_conflicts + doc_conflicts

        # حساب breaking changes (CRITICAL + HIGH)
        breaking_count = sum(
            1 for c in all_conflicts
            if c.severity in (SeverityLevel.CRITICAL, SeverityLevel.HIGH)
        )

        # حساب compatibility_score تلقائياً من doc_conflicts
        if compatibility_score is None and doc_conflicts:
            score_item = next(
                (c for c in doc_conflicts if c.class_name == "Overall"), None
            )
            if score_item and score_item.new_value:
                try:
                    compatibility_score = float(
                        score_item.new_value.replace("%", "")
                    )
                except (ValueError, AttributeError):
                    compatibility_score = 0.0

        # بناء الملخص
        if not summary:
            total = len(all_conflicts)
            if analysis_type == "code_vs_code":
                summary = (
                    f"تم اكتشاف {total} تناقض بين النسختين، "
                    f"{breaking_count} منها breaking changes."
                )
            elif analysis_type == "code_vs_doc":
                score   = compatibility_score or 0
                summary = f"نسبة توافق التوثيق مع الكود الحالي: {score:.1f}%"
            else:
                summary = (
                    f"تحليل شامل: {total} تناقض إجمالي، "
                    f"{breaking_count} breaking changes."
                )

        conflict_metadata = ReportGenerator._build_metadata(metadata) if metadata else None
        grade             = ReportGenerator._calculate_grade(len(all_conflicts), breaking_count)
        suggestions       = ReportGenerator._build_suggestions(all_conflicts)

        return ConflictAnalysisResult(
            analysis_type=analysis_type,
            version_a=version_a,
            version_b=version_b,
            diagram_a=diagram_a,
            diagram_b=diagram_b,
            structural_conflicts=structural_changes,
            semantic_conflicts=semantic_conflicts,
            doc_conflicts=doc_conflicts,
            conflicts={
                "structural":    structural_changes,
                "semantic":      semantic_conflicts,
                "documentation": doc_conflicts,
            },
            summary=summary,
            breaking_changes_count=breaking_count,
            compatibility_score=compatibility_score,
            metadata=conflict_metadata,
            total_changes=len(structural_changes),
            total_conflicts=len(all_conflicts),
            grade=grade,
            suggestions=suggestions,
            completed_at=datetime.utcnow(),
            message=f"تم تحليل {analysis_type} بنجاح"
        )

    @staticmethod
    def merge_results(
        code_vs_code: ConflictAnalysisResult,
        code_vs_doc:  ConflictAnalysisResult,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConflictAnalysisResult:
        """دمج نتيجة Code vs Code مع Code vs Doc في Full Analysis"""

        all_conflicts = (
            code_vs_code.structural_conflicts
            + code_vs_code.semantic_conflicts
            + code_vs_doc.doc_conflicts
        )

        conflict_metadata = ReportGenerator._build_metadata(metadata) if metadata else None
        grade = ReportGenerator._calculate_grade(
            len(all_conflicts), code_vs_code.breaking_changes_count
        )

        return ConflictAnalysisResult(
            analysis_type=AnalysisType.FULL,
            version_a=code_vs_code.version_a,
            version_b=code_vs_code.version_b,
            diagram_a=code_vs_code.diagram_a,
            diagram_b=code_vs_code.diagram_b,
            structural_conflicts=code_vs_code.structural_conflicts,
            semantic_conflicts=code_vs_code.semantic_conflicts,
            doc_conflicts=code_vs_doc.doc_conflicts,
            conflicts={
                "structural":    code_vs_code.structural_conflicts,
                "semantic":      code_vs_code.semantic_conflicts,
                "documentation": code_vs_doc.doc_conflicts,
            },
            summary=f"{code_vs_code.summary} | {code_vs_doc.summary}",
            breaking_changes_count=code_vs_code.breaking_changes_count,
            compatibility_score=code_vs_doc.compatibility_score,
            metadata=conflict_metadata,
            total_conflicts=len(all_conflicts),
            grade=grade,
            suggestions=ReportGenerator._build_suggestions(all_conflicts),
            completed_at=datetime.utcnow(),
            message="تم التحليل الشامل بنجاح"
        )

    # ──────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────

    @staticmethod
    def _build_metadata(raw: Dict[str, Any]) -> ConflictMetadata:
        """يبني كائن ConflictMetadata من الـ raw dict"""

        versions = None
        if raw.get("version_b_id"):
            versions = {
                "version_a": VersionMetadata(
                    version_id=raw.get("version_a_id", ""),
                    version_number=raw.get("version_a_number", ""),
                    role="reference"
                ),
                "version_b": VersionMetadata(
                    version_id=raw.get("version_b_id", ""),
                    version_number=raw.get("version_b_number", ""),
                    role="comparison"
                ),
            }

        doc_meta = None
        if raw.get("doc_version_id"):
            doc_meta = DocMetadata(
                doc_id=raw.get("doc_version_id", ""),
                doc_version_id=raw.get("doc_version_id", ""),
                file_name=raw.get("doc_name", ""),
                type=raw.get("doc_type", "high_level"),
                auto_fetched=raw.get("doc_auto_fetched", False)
            )

        return ConflictMetadata(
            project=ProjectMetadata(
                project_id=raw.get("project_id", ""),
                project_name=raw.get("project_name", "Unknown Project")
            ),
            file=FileMetadata(
                file_id=raw.get("file_id", ""),
                file_name=raw.get("file_name", "Unknown File"),
                file_path=raw.get("file_path", "")
            ),
            versions=versions,
            documentation=doc_meta
        )

    @staticmethod
    def _calculate_grade(total_conflicts: int, breaking_changes: int) -> str:
        if breaking_changes >= 5:
            return "F"
        elif breaking_changes >= 3:
            return "D"
        elif total_conflicts >= 10:
            return "C"
        elif total_conflicts >= 5:
            return "B"
        else:
            return "A"

    @staticmethod
    def _build_suggestions(conflicts: List[ConflictItem]) -> List[Dict[str, Any]]:
        """
        يبني قائمة الاقتراحات من أهم 5 تناقضات.
        يضيف affected_files من ConflictItem إذا كانت موجودة.
        """
        order = {
            "critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4
        }
        sorted_conflicts = sorted(
            conflicts,
            key=lambda c: order.get(
                c.severity.value if hasattr(c.severity, "value") else str(c.severity),
                5
            )
        )

        effort_map = {
            "critical": "30 دقيقة",
            "high":     "20 دقيقة",
            "medium":   "15 دقيقة",
            "low":      "5 دقائق",
            "info":     "5 دقائق",
        }

        suggestions = []
        for i, conflict in enumerate(sorted_conflicts[:5]):
            sev_val = (
                conflict.severity.value
                if hasattr(conflict.severity, "value")
                else str(conflict.severity)
            )
            type_val = (
                conflict.type.value
                if hasattr(conflict.type, "value")
                else str(conflict.type)
            )
            suggestions.append({
                "suggestion_id":      f"sug_{i + 1:03d}",
                "priority":           sev_val,
                "title":              f"معالجة {type_val}",
                "description":        conflict.suggestion or conflict.description,
                "affected_files":     conflict.affected_files or [],   # ← جديد
                "estimated_effort":   effort_map.get(sev_val, "15 دقيقة"),  # ← جديد
                "auto_fix_available": conflict.auto_fix_available,
            })

        return suggestions