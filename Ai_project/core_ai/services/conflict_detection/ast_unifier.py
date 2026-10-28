from typing import Dict, Any, List
from .schemas import UnifiedClassDiagram, ClassDetail, MethodDetail, AttributeDetail, MODULE_CLASS


class ASTUnifier:
    """يوحد ناتج أي Processor إلى UnifiedClassDiagram"""

    @staticmethod
    def _methods(cls: Dict[str, Any]) -> List[MethodDetail]:
        return [
            MethodDetail(
                name=m.get("name", ""),
                signature=m.get("signature", ""),
                is_abstract=m.get("is_abstract", False),
                is_constructor=m.get("is_constructor", False),
                visibility=m.get("visibility", "public"),
                is_override=m.get("is_override", False),
                # حقول الخطوة 1 — بتكون None بالتحليلات القديمة
                parameters=m.get("parameters"),
                return_type=m.get("return_type"),
                decorators=m.get("decorators") or [],
                docstring=m.get("docstring"),
                is_async=m.get("is_async", False),
                body=m.get("body"),
                body_hash=m.get("body_hash"),
                body_truncated=m.get("body_truncated", False),
                line_start=m.get("line_start"),
                line_end=m.get("line_end"),
            )
            for m in cls.get("methods", [])
            if isinstance(m, dict)
        ]

    @staticmethod
    def from_tree_sitter(result: Dict[str, Any]) -> UnifiedClassDiagram:
        classes = []

        for cls in result.get("class_diagram_data", {}).get("classes", []):
            if "name" not in cls:
                continue

            methods = ASTUnifier._methods(cls)

            attributes = [
                AttributeDetail(
                    name=a if isinstance(a, str) else a.get("name", ""),
                    type="any" if isinstance(a, str) else a.get("type", "any"),
                    visibility="public" if isinstance(a, str) else a.get("visibility", "public")
                )
                for a in cls.get("attributes", [])
            ]

            # ── استخراج الـ generic constraints ──────────────────────
            # الـ language processor يحفظها إما في "constraints" (list of str)
            # أو مدمجة في اسم الكلاس مثل "Zoo<T> where T : Animal, new()"
            constraints = ASTUnifier._extract_constraints(cls)

            classes.append(ClassDetail(
                name=cls["name"],
                type=cls.get("type", ""),
                methods=methods,
                attributes=attributes,
                relationships=cls.get("relationships", []),
                is_generic=cls.get("is_generic", False),
                is_abstract=cls.get("is_abstract", False),
                is_interface=cls.get("is_interface", False),
                constraints=constraints
            ))

        # الدوال المستقلة → كلاس وهمي واحد
        module_functions = result.get("class_diagram_data", {}).get("module_functions") or []
        if module_functions:
            classes.append(ClassDetail(
                name=MODULE_CLASS,
                type="module",
                methods=ASTUnifier._methods({"methods": module_functions}),
            ))

        return UnifiedClassDiagram(
            classes=classes,
            relationships=result.get("class_diagram_data", {}).get("relationships", []),
            language=result.get("extracted_features", {}).get("language", ""),
            project_id=result.get("project_id")
        )

    @staticmethod
    def _extract_constraints(cls: Dict[str, Any]) -> List[str]:
        """
        يستخرج الـ generic constraints من بيانات الكلاس.

        يدعم ثلاثة مصادر:
        1. حقل "constraints" مباشرة من الـ processor: ["new()", "IDisposable"]
        2. حقل "type_constraints" أو "where_clause"
        3. Parse من اسم الكلاس إذا كان يحتوي على "where"
           مثال: "Zoo<T> where T : Animal, new()"
        """
        # 1. حقل مباشر
        if cls.get("constraints"):
            raw = cls["constraints"]
            if isinstance(raw, list):
                return [str(c).strip() for c in raw if c]
            if isinstance(raw, str) and raw.strip():
                return [c.strip() for c in raw.split(",") if c.strip()]

        # 2. حقل بديل
        for key in ("type_constraints", "where_clause", "generic_constraints"):
            if cls.get(key):
                raw = cls[key]
                if isinstance(raw, list):
                    return [str(c).strip() for c in raw if c]
                if isinstance(raw, str) and raw.strip():
                    return [c.strip() for c in raw.split(",") if c.strip()]

        # 3. Parse من الاسم: "Zoo<T> where T : Animal, new()"
        name = cls.get("name", "")
        if "where" in name:
            try:
                after_where = name.split("where", 1)[1]
                # نأخذ ما بعد الـ colon: "T : Animal, new()"
                if ":" in after_where:
                    after_colon = after_where.split(":", 1)[1]
                    parts = [p.strip() for p in after_colon.split(",")]
                    return [p for p in parts if p]
            except (IndexError, AttributeError):
                pass

        return []
