"""
Project Analyzer Service - خدمة تحليل المشاريع

هذه الخدمة مسؤولة عن منطق تحليل الكود التجارية.
تستخدم Strategy Pattern لدعم لغات برمجة متعددة.

المسؤوليات:
- تنسيق عملية تحليل الكود الكاملة
- إدارة تدفق البيانات بين مختلف خطوات التحليل
- دعم متعدد اللغات من خلال Language Processors
- تجميع وتنظيم نتائج التحليل

الخطوات التي ينفذها:
1. تحليل بنية الكود (AST)
2. استخراج المميزات (Features)
3. تحليل التبعيات (Dependencies)
4. تحليل دليل الصنف (Class Diagram)
5. تحليل المعالجة الدلالية (Semantic Analysis)

لا تحتوي على database operations - هي business logic نقية.
"""

from core_ai.language_processors.base_processor import ILanguageProcessorStrategy
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class ProjectAnalyzer:
    def __init__(self, processor: ILanguageProcessorStrategy):
        self._processor = processor


    def analyze_code(self, code_content: str) -> Dict[str, Any]:
        if not self._processor:
            raise ValueError("No language processor set for analysis.")

        logger.info(f"Starting analysis with {self._processor.__class__.__name__}")

        ast_structure = self._processor.parse_source_code(code_content)
        if ast_structure.get("error"):
            raise Exception(f"Parsing failed: {ast_structure.get('error')}")

        features = self._processor.extract_features(ast_structure)
        dependencies_list = self._processor.extract_dependencies(ast_structure)
        semantic_analysis_output = self._processor.perform_semantic_analysis(ast_structure, features)
        class_diagram_data = self._processor.generate_class_diagram_data(ast_structure, features)
        dependency_graph_data = self._processor.generate_dependency_graph_data(ast_structure, features) 

        return {
            "ast_structure": ast_structure,
            "features_extracted": features,
            "dependency_graph": dependency_graph_data,
            "semantic_analysis_output": semantic_analysis_output,
            "class_diagram_data": class_diagram_data,
            "dependencies": dependencies_list
        }                                    



