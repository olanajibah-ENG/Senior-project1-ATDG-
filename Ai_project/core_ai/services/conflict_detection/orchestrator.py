import logging
from typing import Dict, Any, Optional
from .schemas import ConflictAnalysisResult, ChangeType, SeverityLevel
from .ast_unifier import ASTUnifier
#from .structural_diff import StructuralDiff
#from .semantic_analyzer import SemanticAnalyzer
#from .code_doc_consistency import CodeDocConsistencyChecker
from .doc_normalizer import DocNormalizer
from .report_generator import ReportGenerator

logger = logging.getLogger(__name__)

class ConflictOrchestrator:

    @staticmethod
    def run_code_vs_code(analysis_a: Dict[str, Any], analysis_b: Dict[str, Any]) -> ConflictAnalysisResult:
        logger.info("Starting [Code vs Code] Analysis...")
        
        diagram_a = ASTUnifier.from_tree_sitter(analysis_a)
        diagram_b = ASTUnifier.from_tree_sitter(analysis_b)

        # ✅ تحسين: Error Handling (or []) لمنع الـ Crash
        structural = StructuralDiff.compare(diagram_a, diagram_b) or []
        semantic = SemanticAnalyzer.analyze(diagram_a, diagram_b) or []

        # تصنيف التغييرات
        structural = ConflictOrchestrator._classify_changes(structural)
        semantic = ConflictOrchestrator._classify_changes(semantic)

        return ReportGenerator.generate(
            analysis_type="code_vs_code",
            version_a=analysis_a.get("version"),
            version_b=analysis_b.get("version"),
            diagram_a=diagram_a,
            diagram_b=diagram_b,
            structural_conflicts=structural,
            semantic_conflicts=semantic
        )

    @staticmethod
    def run_code_vs_doc(analysis: Dict[str, Any], explanation: Dict[str, Any]) -> ConflictAnalysisResult:
        logger.info("Starting [Code vs Doc] Analysis...")
        
        diagram = ASTUnifier.from_tree_sitter(analysis)

        # تطبيع التوثيق واستخراج النوع
        normalized_doc = DocNormalizer.normalize(explanation)

        # تمرير الـ doc_type للمقارن
        doc_conflicts, score = CodeDocConsistencyChecker.compare(
            current_diagram=diagram,
            old_explanation=normalized_doc,
            doc_type=normalized_doc.get("doc_type")
        )

        return ReportGenerator.generate(
            analysis_type="code_vs_doc",
            version_a=analysis.get("version"),
            diagram_a=diagram,
            doc_conflicts=doc_conflicts or [],
            compatibility_score=score
        )

    @staticmethod
    def run_full_analysis(analysis_a, analysis_b, explanation=None):
        logger.info("Starting [Full Analysis]...")
        code_vs_code = ConflictOrchestrator.run_code_vs_code(analysis_a, analysis_b)

        if explanation:
            code_vs_doc = ConflictOrchestrator.run_code_vs_doc(analysis_b, explanation)
            return ReportGenerator.merge(code_vs_code, code_vs_doc)

        return code_vs_code

    @staticmethod
    def _classify_changes(conflicts: list) -> list:
        """تصنيف التناقضات حسب الخطورة والنوع"""
        for item in conflicts:
            # منطق بسيط للتصنيف
            if "deleted" in item.description.lower() or "missing" in item.description.lower():
                item.type = ChangeType.BREAKING_CHANGE
                item.severity = SeverityLevel.HIGH
                item.confidence = 0.95
            else:
                item.type = ChangeType.REFACTORING
                item.severity = SeverityLevel.MEDIUM
                item.confidence = 0.80
        return conflicts