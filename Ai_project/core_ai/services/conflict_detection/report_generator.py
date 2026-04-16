from typing import List, Optional
from .schemas import ConflictAnalysisResult, ConflictItem, UnifiedClassDiagram

class ReportGenerator:
    """
    يولد التقرير النهائي + Mermaid Diagram + Summary
    """

    @staticmethod
    def generate(
        analysis_type: str,
        version_a: str,
        diagram_a: UnifiedClassDiagram,
        version_b: Optional[str] = None,
        diagram_b: Optional[UnifiedClassDiagram] = None,
        conflicts: List[ConflictItem] = None,
        compatibility_score: Optional[float] = None,
        summary: str = ""
    ) -> ConflictAnalysisResult:
        
        conflicts = conflicts or []

        # حساب عدد الـ breaking changes
        breaking_count = sum(1 for c in conflicts if c.severity == "high")

        # بناء الملخص الذكي
        if not summary:
            if analysis_type == "code_vs_code":
                summary = f"تم اكتشاف {len(conflicts)} تناقض بين النسختين، {breaking_count} منها breaking changes."
            elif analysis_type == "code_vs_doc":
                score = compatibility_score or 0
                summary = f"نسبة توافق التوثيق مع الكود الحالي: {score:.1f}%"
            else:
                summary = "تم إجراء تحليل شامل للكود والتوثيق."

        return ConflictAnalysisResult(
            analysis_type=analysis_type,
            version_a=version_a,
            version_b=version_b,
            diagram_a=diagram_a,
            diagram_b=diagram_b,
            conflicts=conflicts,
            summary=summary,
            breaking_changes_count=breaking_count,
            compatibility_score=compatibility_score
        )

    @staticmethod
    def merge(code_vs_code: ConflictAnalysisResult, code_vs_doc: ConflictAnalysisResult) -> ConflictAnalysisResult:
        """دمج نتيجة Code vs Code مع Code vs Doc"""
        all_conflicts = code_vs_code.conflicts + code_vs_doc.conflicts

        return ConflictAnalysisResult(
            analysis_type="full_analysis",
            version_a=code_vs_code.version_a,
            version_b=code_vs_code.version_b,
            diagram_a=code_vs_code.diagram_a,
            diagram_b=code_vs_code.diagram_b,
            conflicts=all_conflicts,
            summary=f"{code_vs_code.summary} | {code_vs_doc.summary}",
            breaking_changes_count=code_vs_code.breaking_changes_count,
            compatibility_score=code_vs_doc.compatibility_score
        )