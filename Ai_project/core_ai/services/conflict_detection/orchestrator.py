# core_ai/services/conflict_detection/orchestrator.py
from typing import Dict, Any, Optional
from .schemas import ConflictAnalysisResult
from .ast_unifier import ASTUnifier
from .structural_diff import StructuralDiff
from .semantic_analyzer import SemanticAnalyzer
from .code_doc_consistency import CodeDocConsistencyChecker
from .report_generator import ReportGenerator


class ConflictOrchestrator:
    """المنسق الرئيسي - يدير كل عمليات كشف التناقض"""

    @staticmethod
    def run_code_vs_code(
        analysis_a: Dict[str, Any],
        analysis_b: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConflictAnalysisResult:

        diagram_a = ASTUnifier.from_tree_sitter(analysis_a)
        diagram_b = ASTUnifier.from_tree_sitter(analysis_b)

        structural = StructuralDiff.compare(diagram_a, diagram_b)
        semantic   = SemanticAnalyzer().analyze(
            diagram_a.model_dump(), diagram_b.model_dump()
        )

        version_a = str(analysis_a.get("_id", "version_a"))
        version_b = str(analysis_b.get("_id", "version_b"))

        return ReportGenerator.generate(
            analysis_type="code_vs_code",
            version_a=version_a,
            version_b=version_b,
            diagram_a=diagram_a,
            diagram_b=diagram_b,
            structural_changes=structural,
            semantic_conflicts=semantic,
            metadata=metadata
        )

    @staticmethod
    def run_code_vs_doc(
        analysis: Dict[str, Any],
        explanation: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConflictAnalysisResult:

        diagram      = ASTUnifier.from_tree_sitter(analysis)
        doc_conflicts = CodeDocConsistencyChecker.compare(diagram, explanation)

        version_a = str(analysis.get("_id", "current"))

        return ReportGenerator.generate(
            analysis_type="code_vs_doc",
            version_a=version_a,
            diagram_a=diagram,
            doc_conflicts=doc_conflicts,
            metadata=metadata
        )

    @staticmethod
    def run_full_analysis(
        analysis_a:  Dict[str, Any],
        analysis_b:  Dict[str, Any],
        explanation: Optional[Dict[str, Any]] = None,
        metadata:    Optional[Dict[str, Any]] = None
    ) -> ConflictAnalysisResult:
        """Full Analysis = Code vs Code + Code vs Doc (إذا وُجد التوثيق)"""

        code_result = ConflictOrchestrator.run_code_vs_code(
            analysis_a, analysis_b, metadata
        )

        if explanation:
            doc_result = ConflictOrchestrator.run_code_vs_doc(
                analysis_b, explanation, metadata
            )
            return ReportGenerator.merge_results(code_result, doc_result, metadata)

        return code_result
