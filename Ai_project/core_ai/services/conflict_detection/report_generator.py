from .schemas import ConflictAnalysisResult, DocType

class ReportGenerator:

    @staticmethod
    def generate(
        analysis_type: str,
        version_a: str,
        diagram_a,
        version_b: str = None,
        diagram_b=None,
        structural_conflicts=None,
        semantic_conflicts=None,
        doc_conflicts=None,
        compatibility_score=None
    ) -> ConflictAnalysisResult:

        structural_conflicts = structural_conflicts or []
        semantic_conflicts = semantic_conflicts or []
        doc_conflicts = doc_conflicts or []

        # حساب الـ Breaking Changes
        breaking_count = sum(1 for c in structural_conflicts + semantic_conflicts if c.severity == "high")

        # بناء الملخص
        summary = f"{len(structural_conflicts)} structural, {len(semantic_conflicts)} semantic."
        
        # ✅ تحسين: فصل High/Low Level في الملخص
        if doc_conflicts:
            high_issues = sum(1 for c in doc_conflicts if c.doc_type == DocType.HIGH_LEVEL)
            low_issues = sum(1 for c in doc_conflicts if c.doc_type == DocType.LOW_LEVEL)
            summary += f" Doc: {high_issues} high-level, {low_issues} low-level issues."

        return ConflictAnalysisResult(
            analysis_type=analysis_type,
            version_a=version_a,
            version_b=version_b,
            diagram_a=diagram_a,
            diagram_b=diagram_b,
            structural_conflicts=structural_conflicts,
            semantic_conflicts=semantic_conflicts,
            doc_conflicts=doc_conflicts,
            summary=summary,
            breaking_changes_count=breaking_count,
            compatibility_score=compatibility_score
        )

    @staticmethod
    def merge(code_vs_code: ConflictAnalysisResult, code_vs_doc: ConflictAnalysisResult):
        return ConflictAnalysisResult(
            analysis_type="full_analysis",
            version_a=code_vs_code.version_a,
            version_b=code_vs_code.version_b,
            diagram_a=code_vs_code.diagram_a,
            diagram_b=code_vs_code.diagram_b,
            structural_conflicts=code_vs_code.structural_conflicts,
            semantic_conflicts=code_vs_code.semantic_conflicts,
            doc_conflicts=code_vs_doc.doc_conflicts,
            summary=code_vs_code.summary + " | " + code_vs_doc.summary,
            breaking_changes_count=code_vs_code.breaking_changes_count,
            compatibility_score=code_vs_doc.compatibility_score
        )