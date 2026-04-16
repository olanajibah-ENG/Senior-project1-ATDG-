import re
import logging
from typing import Dict, Any
from .schemas import DocType

logger = logging.getLogger(__name__)

class DocNormalizer:
    """يقوم بتطبيع وتنظيف التوثيق وتصنيفه (High/Low Level)"""

    @staticmethod
    def normalize(raw_doc: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Starting document normalization...")
        
        # تحويل كامل المحتوى لنص للتحليل
        raw_text = str(raw_doc)
        
        # 1. كشف نوع التوثيق (Improvement #1)
        doc_type = DocNormalizer._detect_doc_type(raw_text)

        normalized = {
            "doc_type": doc_type,
            "description": DocNormalizer._clean_text(raw_doc.get("description", "")),
            "methods": [],
            "attributes": []
        }

        # 2. توحيد أسماء الدوال (Improvement #1)
        for method in raw_doc.get("methods", []):
            name = method.get("name", "")
            
            # تصحيح الأخطاء الشائعة في الأسماء
            if name.strip("_") == "init":
                name = "__init__"
            
            normalized["methods"].append({
                "name": name,
                "description": DocNormalizer._clean_text(method.get("description", ""))
            })

        logger.info(f"Normalization complete. Detected type: {doc_type}")
        return normalized

    @staticmethod
    def _detect_doc_type(text: str) -> DocType:
        """كشف نوع التوثيق بناءً على الكلمات المفتاحية"""
        text_lower = text.lower()
        
        low_level_keywords = ["parameter", "return", "logic flow", "constructor", "init", "exception"]
        high_level_keywords = ["responsibility", "purpose", "overview", "architecture", "class diagram"]
        
        if any(keyword in text_lower for keyword in low_level_keywords):
            return DocType.LOW_LEVEL
        elif any(keyword in text_lower for keyword in high_level_keywords):
            return DocType.HIGH_LEVEL
            
        return DocType.UNKNOWN

    @staticmethod
    def _clean_text(text: str) -> str:
        """تنظيف النص من الضوضاء والرموز الزائدة"""
        if not text:
            return ""
        # إزالة الرموز الخاصة وتحويل لـ lowercase
        text = re.sub(r'[^\w\s]', '', text)
        return text.lower().strip()