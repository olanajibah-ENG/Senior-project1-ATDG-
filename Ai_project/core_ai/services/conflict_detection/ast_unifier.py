from typing import Dict, Any
from .schemas import UnifiedClassDiagram, ClassDetail, MethodDetail, AttributeDetail

class ASTUnifier:
    """يوحد ناتج أي Processor إلى UnifiedClassDiagram"""

    @staticmethod
    def from_tree_sitter(result: Dict[str, Any]) -> UnifiedClassDiagram:
        classes = []

        for cls in result.get("class_diagram_data", {}).get("classes", []):
            # ✅ تحسين: Validation للتأكد من وجود الاسم
            if "name" not in cls:
                continue

            methods = [
                MethodDetail(
                    name=m.get("name", ""),
                    signature=m.get("signature", ""),
                    is_abstract=m.get("is_abstract", False),
                    is_constructor=m.get("is_constructor", False),
                    visibility=m.get("visibility", "public"),
                    is_override=m.get("is_override", False)
                )
                for m in cls.get("methods", [])
            ]

            attributes = [
                AttributeDetail(
                    name=a if isinstance(a, str) else a.get("name", ""),
                    type="any" if isinstance(a, str) else a.get("type", "any"),
                    visibility="public" if isinstance(a, str) else a.get("visibility", "public")
                )
                for a in cls.get("attributes", [])
            ]

            classes.append(ClassDetail(
                name=cls["name"],
                type=cls.get("type", ""),
                methods=methods,
                attributes=attributes,
                relationships=cls.get("relationships", []),
                is_generic=cls.get("is_generic", False),
                is_abstract=cls.get("is_abstract", False),
                is_interface=cls.get("is_interface", False)
            ))

        return UnifiedClassDiagram(
            classes=classes,
            relationships=result.get("class_diagram_data", {}).get("relationships", []),
            language=result.get("extracted_features", {}).get("language", ""),
            project_id=result.get("project_id")
        )