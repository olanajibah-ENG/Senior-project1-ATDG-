"""

ProcessorFactory

================

مكان واحد يقرر أي processor يستخدم.



Python  → PythonProcessor         (Python ast — أدق)

Java    → JavaProcessor           (tree-sitter Java — أدق)

باقي اللغات المدعومة → TreeSitterProcessor(file_type)

لغة مجهولة → GenericProcessor(file_type)   (Regex fallback)



إضافة لغة جديدة:

  - لو tree-sitter يدعمها: أضف entry في LANGUAGE_CONFIG بـ tree_sitter_processor.py فقط

  - لو تريد معالج خاص أدق: أضف سطر في _DEDICATED هنا

"""



import logging

from typing import Type, Dict



from .base_processor import ILanguageProcessorStrategy

from .python_processor import PythonProcessor

from .java_processor import JavaProcessor

from .tree_sitter_processor import TreeSitterProcessor, SUPPORTED_LANGUAGES

from .generic_processor import GenericProcessor



logger = logging.getLogger(__name__)





class ProcessorFactory:



    # معالجات متخصصة — أولوية على tree-sitter لأنها أدق

    _DEDICATED: Dict[str, Type[ILanguageProcessorStrategy]] = {

        "python": PythonProcessor,

        "java":   JavaProcessor,

    }



    @classmethod

    def get(cls, file_type: str) -> ILanguageProcessorStrategy:

        ft = (file_type or "unknown").lower().strip()



        # 1. معالج خاص متخصص

        if ft in cls._DEDICATED:

            proc = cls._DEDICATED[ft]()

            logger.info(f"[ProcessorFactory] {proc.__class__.__name__} → '{ft}'")

            return proc



        # 2. tree-sitter عام

        if ft in SUPPORTED_LANGUAGES:

            logger.info(f"[ProcessorFactory] TreeSitterProcessor → '{ft}'")

            return TreeSitterProcessor(ft)



        # 3. Regex fallback للغات غير المدعومة

        logger.info(f"[ProcessorFactory] GenericProcessor (regex fallback) → '{ft}'")

        return GenericProcessor(ft)



    @classmethod

    def register(cls, file_type: str, processor_class: Type[ILanguageProcessorStrategy]) -> None:

        """تسجيل معالج متخصص جديد."""

        cls._DEDICATED[file_type.lower()] = processor_class

        logger.info(f"[ProcessorFactory] Registered '{file_type}' → {processor_class.__name__}")



    @classmethod

    def supported_languages(cls) -> dict:

        return {

            "dedicated":   list(cls._DEDICATED.keys()),

            "tree_sitter": sorted(SUPPORTED_LANGUAGES),

            "fallback":    "regex (any other language)",

        }

