"""
python_processor.py
===================
معالج Python المحسّن باستخدام Python AST المدمج.

✅ تحليل شامل: AST + Features + Dependencies + Semantic + UML
✅ تصحيح تلقائي للكود (auto-fix) قبل التحليل
✅ استخراج دقيق للعلاقات (Composition / Aggregation / Association / Dependency)
✅ دعم Abstract Classes و Interfaces (ABC / Protocol)
✅ دمج العلاقات بالأولوية (composition > aggregation > ...)
✅ كشف العلاقات ثنائية الاتجاه
"""

import ast
import logging
import re
from typing import Dict, Any, List, Set
from .base_processor import ILanguageProcessorStrategy

logger = logging.getLogger(__name__)


def serialize_ast(node):
    if isinstance(node, ast.AST):
        fields = {}
        for field in node._fields:
            if hasattr(node, field):
                value = getattr(node, field)
                fields[field] = serialize_ast(value)
        fields['node_type'] = node.__class__.__name__
        return fields
    elif isinstance(node, list):
        return [serialize_ast(item) for item in node]
    elif isinstance(node, (str, int, float, bool, type(None))):
        return node
    else:
        return str(node)


class PythonProcessor(ILanguageProcessorStrategy):
    
    PRIMITIVE_TYPES = {
        'str', 'int', 'float', 'bool', 'bytes', 'bytearray',
        'list', 'dict', 'set', 'tuple', 'frozenset',
        'String', 'Integer', 'Float', 'Boolean',
        'List', 'Dict', 'Set', 'Tuple', 'FrozenSet',
        'Any', 'None', 'Optional', 'Union',
        'Callable', 'Iterable', 'Iterator', 'Generator', 'super'
    }
    
    TECHNICAL_BASE_CLASSES = {
        'ABC', 'object', 'Object', 'Enum', 'IntEnum',
        'Exception', 'BaseException', 'NamedTuple'
    }
    
    def _normalize_python_code(self, code_content: str) -> Dict[str, Any]:
        original_code = code_content
        normalized_code = code_content
        fixes_applied = []
        
        class_pattern = r'(class\s+\w+.*?:.*?)(def\s+init\s*\(self)'
        def fix_init(match):
            fixes_applied.append(f"Fixed 'init' → '__init__' in line")
            return match.group(1) + 'def __init__(self'
        
        normalized_code = re.sub(class_pattern, fix_init, normalized_code, flags=re.DOTALL | re.MULTILINE)
        
        super_pattern = r'super\(\)\.init\('
        if re.search(super_pattern, normalized_code):
            normalized_code = re.sub(super_pattern, 'super().__init__(', normalized_code)
            fixes_applied.append("Fixed 'super().init()' → 'super().__init__()'")
        
        weird_underscores = ['\u2013\u2013', '\u2014\u2014', '––', '__']
        for weird in weird_underscores:
            if weird in normalized_code:
                normalized_code = normalized_code.replace(weird, '__')
                fixes_applied.append(f"Fixed weird underscores: {repr(weird)} → '__'")
        
        normalized_code = re.sub(r'[ \t]+\n', '\n', normalized_code)
        normalized_code = re.sub(r'\n{3,}', '\n\n', normalized_code)
        
        return {
            "normalized_code": normalized_code,
            "original_code": original_code,
            "fixes_applied": fixes_applied,
            "was_modified": len(fixes_applied) > 0
        }

    def parse_source_code(self, code_content: str) -> Dict[str, Any]:
        logger.info("[PythonProcessor] Parsing source code...")
        normalization_result = self._normalize_python_code(code_content)
        code_to_parse = normalization_result["normalized_code"]

        if normalization_result["was_modified"]:
            logger.info(f"[PythonProcessor] Auto-fixed {len(normalization_result['fixes_applied'])} issue(s): {normalization_result['fixes_applied']}")

        try:
            tree = ast.parse(code_to_parse)
            serialized_tree = serialize_ast(tree) if tree else None
            logger.info("[PythonProcessor] Parsing successful.")
            return {
                "ast_tree": serialized_tree,
                "code_content": code_to_parse,
                "original_code": normalization_result["original_code"],
                "normalization_fixes": normalization_result["fixes_applied"],
                "was_auto_fixed": normalization_result["was_modified"]
            }
        except SyntaxError as e:
            logger.error(f"[PythonProcessor] SyntaxError: {e}")
            return {
                "ast_tree": None,
                "error": str(e),
                "original_code": normalization_result["original_code"],
                "normalization_fixes": normalization_result["fixes_applied"]
            }

    def extract_features(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("[PythonProcessor] Extracting features...")
        code = ast_data.get("code_content", "")
        try:
            tree = ast.parse(code)
        except SyntaxError:
            logger.warning("[PythonProcessor] Cannot extract features — invalid syntax.")
            return {"lines_of_code": 0, "error": "Invalid AST"}

        num_functions = 0
        num_inheritances = 0
        num_classes = 0
        num_async_functions = 0

        class ComplexityVisitor(ast.NodeVisitor):
            def __init__(self):
                self.current_nesting_level = 0
                self.conditional_complexity = 0

            def visit_If(self, node):
                self.conditional_complexity += (self.current_nesting_level + 1)
                self.current_nesting_level += 1
                self.generic_visit(node)
                self.current_nesting_level -= 1

            def visit_For(self, node):
                self.conditional_complexity += (self.current_nesting_level + 1)
                self.current_nesting_level += 1
                self.generic_visit(node)
                self.current_nesting_level -= 1

            def visit_While(self, node):
                self.conditional_complexity += (self.current_nesting_level + 1)
                self.current_nesting_level += 1
                self.generic_visit(node)
                self.current_nesting_level -= 1

            def visit_With(self, node):
                self.conditional_complexity += (self.current_nesting_level + 1)
                self.current_nesting_level += 1
                self.generic_visit(node)
                self.current_nesting_level -= 1

            def visit_ExceptHandler(self, node):
                self.conditional_complexity += (self.current_nesting_level + 1)
                self.current_nesting_level += 1
                self.generic_visit(node)
                self.current_nesting_level -= 1

        complexity_visitor = ComplexityVisitor()
        complexity_visitor.visit(tree)
        conditional_complexity = complexity_visitor.conditional_complexity

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                num_classes += 1
                num_inheritances += len(node.bases)
            elif isinstance(node, ast.FunctionDef):
                num_functions += 1
            elif isinstance(node, ast.AsyncFunctionDef):
                num_async_functions += 1

        stats = {
            "lines_of_code": len(code.splitlines()),
            "num_classes": num_classes,
            "num_functions": num_functions,
            "num_async_functions": num_async_functions,
            "complexity_score": (num_functions * 2) + (num_inheritances * 3) + conditional_complexity,
            "auto_fixes_applied": ast_data.get("normalization_fixes", []),
            "was_code_modified": ast_data.get("was_auto_fixed", False)
        }

        logger.info(f"[PythonProcessor] Features: classes={num_classes}, functions={num_functions}, async={num_async_functions}, complexity={stats['complexity_score']}")
        return stats

    def extract_dependencies(self, ast_data: Dict[str, Any]) -> List[str]:
        logger.info("[PythonProcessor] Extracting dependencies...")
        code = ast_data.get("code_content", "")
        try:
            tree = ast.parse(code)
        except SyntaxError:
            logger.warning("[PythonProcessor] Cannot extract dependencies — invalid syntax.")
            return []
        
        dependencies = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dependencies.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    dependencies.add(node.module.split('.')[0])
        
        result = list(dependencies)
        logger.info(f"[PythonProcessor] Found {len(result)} dependencies.")
        return result

    def perform_semantic_analysis(self, ast_data: Dict[str, Any], features: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("[PythonProcessor] Performing semantic analysis...")
        code = ast_data.get("code_content", "")
        try:
            tree = ast.parse(code)
        except SyntaxError:
            logger.warning("[PythonProcessor] Cannot perform semantic analysis — invalid syntax.")
            return {"quality_score": 0, "issues": ["Cannot analyze invalid code"]}

        issues = []
        warnings = []
        
        if ast_data.get("was_auto_fixed", False):
            auto_fixes = ast_data.get("normalization_fixes", [])
            for fix in auto_fixes:
                warnings.append(f"⚠️ AUTO-FIXED: {fix}")
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if len(node.body) > 50:
                    issues.append(f"Function '{node.name}' is too long ({len(node.body)} lines)")
                if len(node.args.args) > 5:
                    issues.append(f"Function '{node.name}' has too many parameters ({len(node.args.args)})")
            
            elif isinstance(node, ast.ClassDef):
                if len(node.body) > 100:
                    warnings.append(f"Class '{node.name}' is very large ({len(node.body)} statements)")

        complexity = features.get("complexity_score", 0)
        quality_score = max(0, 100 - (len(issues) * 5) - (len(warnings) * 2) - (complexity * 0.1))

        result = {
            "quality_score": round(quality_score, 2),
            "issues": issues,
            "warnings": warnings,
            "complexity": complexity
        }
        logger.info(f"[PythonProcessor] Semantic analysis done — quality={result['quality_score']}, issues={len(issues)}, warnings={len(warnings)}")
        return result

    def generate_uml_diagram(self, ast_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        logger.info("[PythonProcessor] Generating UML diagram...")
        code = ast_data.get("code_content", "")
        try:
            tree = ast.parse(code)
        except SyntaxError:
            logger.warning("[PythonProcessor] Cannot generate UML — invalid syntax.")
            return {"classes": [], "relationships": []}

        all_class_names = {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}

        classes = []
        all_relationships = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = self._extract_class_info_enhanced(node, all_class_names, ast_data)
                classes.append(class_info)
                all_relationships.extend(self._get_relationships_enhanced(node, all_class_names))

        all_relationships.extend(self._extract_all_dependencies(tree, all_class_names, all_relationships))

        # في البداية نقوم بفلترة الأولية للأنواع البدائية فقط
        filtered = [r for r in all_relationships if not self._is_primitive_type(r.get('to', ''))]
        
        # ملاحظة: نحن لا نفلتر هنا بناءً على all_class_names المحلية فقط 
        # لكي نسمح لخدمة المشروع (Project Service) بربط العلاقات بين الملفات لاحقاً
        final_relationships = self._merge_relationships(filtered)
        final_relationships = self._detect_bidirectionals(final_relationships)

        cleaned_classes = self._clean_duplicate_attributes(classes, final_relationships)

        for cls in cleaned_classes:
            for m in cls.get("methods", []):
                if m.get("is_constructor") and not m["signature"].startswith(('+', '-')):
                    m["signature"] = "+ " + m["signature"]

        result = {"classes": cleaned_classes, "relationships": final_relationships}
        logger.info(f"[PythonProcessor] UML done — classes={len(cleaned_classes)}, relationships={len(final_relationships)}")
        return result

    def _extract_class_info_enhanced(self, class_node, all_class_names, ast_data):
        base_classes = []
        is_abstract = False
        is_interface = False
        
        for base in class_node.bases:
            if isinstance(base, ast.Name):
                base_name = base.id
                if base_name in self.TECHNICAL_BASE_CLASSES:
                    if base_name == 'ABC':
                        is_interface = True
                    continue
                base_classes.append(base_name)
            elif isinstance(base, ast.Attribute):
                if isinstance(base.value, ast.Name) and base.value.id == 'abc' and base.attr == 'ABC':
                    is_interface = True
                    continue

        methods = []
        param_types = {}
        
        for item in class_node.body:
            if isinstance(item, ast.FunctionDef):
                if item.name == "__init__":
                    for arg in item.args.args:
                        if arg.arg != 'self' and arg.annotation:
                            param_types[arg.arg] = self._get_annotation_type(arg.annotation)
                    
                    constructor_params = []
                    for arg in item.args.args:
                        if arg.arg != 'self':
                            ptype = self._get_annotation_type(arg.annotation) or "Any"
                            constructor_params.append(f"{arg.arg}: {ptype}")
                    
                    methods.append({
                        "name": "__init__",
                        "signature": f"+ __init__({', '.join(constructor_params)})",
                        "is_abstract": False,
                        "visibility": "public",
                        "is_constructor": True
                    })
                    continue
                
                is_abstract_method = any(
                    (isinstance(d, ast.Name) and d.id == 'abstractmethod') or
                    (isinstance(d, ast.Attribute) and d.attr == 'abstractmethod')
                    for d in item.decorator_list
                )
                if is_abstract_method:
                    is_abstract = True
                
                params = []
                for arg in item.args.args:
                    if arg.arg != 'self':
                        param_type = self._get_annotation_type(arg.annotation) or "Any"
                        params.append(f"{arg.arg}: {param_type}")
                
                return_type = self._infer_return_type(item)
                
                method_signature = f"{item.name}({', '.join(params)}): {return_type}"
                visibility = self._get_visibility(item.name)

                methods.append({
                    "name": item.name,
                    "signature": method_signature,
                    "is_abstract": is_abstract_method,
                    "visibility": visibility,
                    "is_constructor": False
                })

        attributes = []
        for item in class_node.body:
            if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                for stmt in item.body:
                    if isinstance(stmt, ast.Assign):
                        for target in stmt.targets:
                            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                                attr_name = target.attr
                                attr_info = self._infer_attribute_type(attr_name, stmt.value, param_types, all_class_names)
                                attributes.append({
                                    "name": attr_name,
                                    "type": attr_info["type"],
                                    "visibility": self._get_visibility(attr_name)
                                })

        for item in class_node.body:
            if isinstance(item, ast.AnnAssign):
                if isinstance(item.target, ast.Name):
                    attr_name = item.target.id
                    attr_type = self._get_annotation_type(item.annotation)
                    attributes.append({
                        "name": attr_name,
                        "type": attr_type,
                        "visibility": self._get_visibility(attr_name)
                    })

        detect = self._detect_interface_or_abstract(class_node, ast_data)
        return {
            "name": class_node.name,
            "attributes": attributes,
            "methods": methods,
            "base_classes": base_classes,
            "is_abstract": detect["is_abstract"],
            "is_interface": detect["is_interface"]
        }

    def _infer_attribute_type(self, attr_name: str, value_node: Any, param_types: Dict, all_class_names: Set[str]) -> Dict:
        result = {
            "type": "Any",
            "is_collection": False,
            "inner_type": None,
            "multiplicity": None
        }

        # 1. إذا كان القيمة اسم معامل موجود في __init__ → خذ نوعه مباشرة
        if isinstance(value_node, ast.Name) and value_node.id in param_types:
            param_type = param_types[value_node.id]
            unwrapped = self._unwrap_complex_type(param_type)

            if param_type.startswith(('List[', 'list[')):
                result["type"] = param_type
                result["is_collection"] = True
                result["inner_type"] = unwrapped
                result["multiplicity"] = "0..*"
            elif param_type.startswith(('Set[', 'set[')):
                result["type"] = param_type
                result["is_collection"] = True
                result["inner_type"] = unwrapped
                result["multiplicity"] = "0..*"
            elif param_type.startswith('Optional['):
                result["type"] = param_type
                result["multiplicity"] = "0..1"
            elif not self._is_primitive_type(unwrapped):
                result["type"] = unwrapped
                result["multiplicity"] = "1"
            else:
                # لو الـ param_type مش معقد، خذه مباشرة
                result["type"] = param_type if param_type != "Any" else result["type"]

            if result["type"] != "Any":
                return result

        # 2. إنشاء كائن → composition
        if isinstance(value_node, ast.Call):
            if isinstance(value_node.func, ast.Name):
                called = value_node.func.id
                if not self._is_primitive_type(called):
                    return {
                        "type": called,
                        "is_collection": False,
                        "inner_type": None,
                        "multiplicity": "1"
                    }

        # 3. قيمة ثابتة
        if isinstance(value_node, ast.Constant):
            val = value_node.value
            if val is None:
                result["type"] = "Optional[Any]"
                result["multiplicity"] = "0..1"
            elif isinstance(val, bool):
                result["type"] = "bool"
            elif isinstance(val, int):
                result["type"] = "int"
            elif isinstance(val, float):
                result["type"] = "float"
            elif isinstance(val, str):
                result["type"] = "str"

        # 4. قوائم/مجموعات فارغة
        if isinstance(value_node, (ast.List, ast.Set)):
            container = "List" if isinstance(value_node, ast.List) else "Set"
            inner = self._infer_class_from_plural_name(attr_name, all_class_names)
            # نحن نفضل وجود inner_type حتى لو لم يكن معروفاً محلياً
            result["type"] = f"{container}[{inner}]" if inner else container
            result["is_collection"] = True
            result["inner_type"] = inner
            result["multiplicity"] = "0..*"

        # 5. استنتاج ذكي من اسم الـ attribute (fallback قوي)
        attr_lower = attr_name.lower()
        common_name_to_type = {
            'id': 'int', 'count': 'int', 'age': 'int', 'year': 'int', 'size': 'int',
            'price': 'float', 'cost': 'float', 'weight': 'float', 'height': 'float',
            'speed': 'int', 'horsepower': 'int', 'wheels': 'int', 'rpm': 'int',
            'name': 'str', 'title': 'str', 'color': 'str', 'brand': 'str',
            'model': 'str', 'status': 'str', 'description': 'str',
            'active': 'bool', 'enabled': 'bool', 'is_': 'bool'
        }

        for key, typ in common_name_to_type.items():
            if key in attr_lower or attr_name.lower().startswith(key):
                result["type"] = typ
                break

        # 6. مجموعات عامة من الاسم
        if any(s in attr_lower for s in ['list', 'items', 'collection', 'children', 'members', '_set', 'array']):
            inner = self._infer_class_from_plural_name(attr_name, all_class_names)
            if inner:
                result["type"] = f"List[{inner}]"
                result["is_collection"] = True
                result["inner_type"] = inner
                result["multiplicity"] = "0..*"

        return result

    def _get_relationships_enhanced(self, class_node, all_class_names):
            rels = []
            composition_targets = set()

            # Inheritance & Realization
            for base in class_node.bases:
                if isinstance(base, ast.Name):
                    base_name = base.id
                    if base_name in self.TECHNICAL_BASE_CLASSES:
                        if base_name == 'ABC':
                            rels.append({
                                "from": class_node.name,
                                "to": base_name,
                                "type": "realization",
                                "label": "implements",
                                "arrow": "→",
                                "dashed": True,
                                "directed": True
                            })
                        continue
                    if self._is_primitive_type(base_name):
                        continue
                    rels.append({
                        "from": class_node.name,
                        "to": base_name,
                        "type": "inheritance",
                        "label": "extends",
                        "arrow": "→",
                        "directed": True
                    })

            # Composition, Aggregation, Association (من __init__ ومن instance vars خارجها)
            for stmt in ast.walk(class_node):
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if not (isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self'):
                            continue

                        attr_name = target.attr
                        attr_info = self._infer_attribute_type(attr_name, stmt.value, {}, all_class_names)

                        if attr_info["type"] == "Any":
                            continue

                        if isinstance(stmt.value, ast.Call) and isinstance(stmt.value.func, ast.Name):
                            called = stmt.value.func.id
                            if not self._is_primitive_type(called):
                                rels.append({
                                    "from": class_node.name,
                                    "to": called,
                                    "type": "composition",
                                    "label": attr_name,
                                    "multiplicity": "1",
                                    "arrow": "→",
                                    "directed": True
                                })
                                composition_targets.add(called)
                                continue

                        if attr_info["is_collection"] and attr_info["inner_type"]:
                            rels.append({
                                "from": class_node.name,
                                "to": attr_info["inner_type"],
                                "type": "aggregation",
                                "label": attr_name,
                                "multiplicity": attr_info.get("multiplicity", "0..*"),
                                "arrow": "→",
                                "directed": True
                            })
                            continue

                        if attr_info["type"] and not self._is_primitive_type(attr_info["type"]) and not attr_info["is_collection"]:
                            mult = attr_info.get("multiplicity", "1")
                            rels.append({
                                "from": class_node.name,
                                "to": attr_info["type"],
                                "type": "association",
                                "label": f"{attr_name} ({mult})",
                                "multiplicity": mult,
                                "arrow": "→",
                                "directed": True
                            })
                            
                elif isinstance(stmt, ast.AnnAssign):
                    target = stmt.target
                    attr_name = None
                    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                        attr_name = target.attr
                    elif isinstance(target, ast.Name):
                        attr_name = target.id
                        
                    if attr_name and stmt.annotation:
                        attr_type = self._get_annotation_type(stmt.annotation)
                        unwrapped = self._unwrap_complex_type(attr_type)
                        
                        if unwrapped and unwrapped != "Any" and unwrapped != "None" and not self._is_primitive_type(unwrapped):
                            is_coll = any(c in attr_type for c in ["List[", "Set[", "Tuple[", "Dict["])
                            rel_type = "aggregation" if is_coll else "association"
                            mult = "0..*" if is_coll else ("0..1" if "Optional[" in attr_type else "1")
                            
                            rels.append({
                                "from": class_node.name,
                                "to": unwrapped,
                                "type": rel_type,
                                "label": attr_name,
                                "multiplicity": mult,
                                "arrow": "→",
                                "directed": True
                            })

            # استخراج الاعتماديات (Dependencies) من المعاملات والأنواع المعادة في الدوال
            for node in class_node.body:
                if isinstance(node, ast.FunctionDef):
                    # تجنب المُنشئ لأنه تمت معالجته كسمات (attributes)
                    if node.name != "__init__":
                        # معاملات الدالة
                        for arg in node.args.args:
                            if arg.arg != 'self' and arg.annotation:
                                arg_type = self._get_annotation_type(arg.annotation)
                                unwrapped = self._unwrap_complex_type(arg_type)
                                if unwrapped and unwrapped != "Any" and not self._is_primitive_type(unwrapped):
                                    rels.append({
                                        "from": class_node.name,
                                        "to": unwrapped,
                                        "type": "dependency",
                                        "label": "uses",
                                        "arrow": "→",
                                        "directed": True
                                    })
                        
                        # النوع المعاد
                        if node.returns:
                            ret_type = self._get_annotation_type(node.returns)
                            unwrapped = self._unwrap_complex_type(ret_type)
                            if unwrapped and unwrapped != "Any" and unwrapped != "None" and not self._is_primitive_type(unwrapped):
                                rels.append({
                                    "from": class_node.name,
                                    "to": unwrapped,
                                    "type": "dependency",
                                    "label": "returns",
                                    "arrow": "→",
                                    "directed": True
                                })

            # تنظيف العلاقات المكررة محلياً
            unique_rels = []
            seen_rels = set()
            for r in rels:
                key = (r['from'], r['to'], r['type'])
                if key not in seen_rels:
                    seen_rels.add(key)
                    unique_rels.append(r)

            return unique_rels

    def _extract_all_dependencies(self, tree, all_class_names, existing):
        deps = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                called = node.func.id
                if not self._is_primitive_type(called):
                    parent_class = None
                    for ancestor in ast.walk(tree):
                        if isinstance(ancestor, ast.ClassDef) and node in ast.walk(ancestor):
                            parent_class = ancestor.name
                            break
                    if parent_class and not any(
                        r['from'] == parent_class and r['to'] == called and 
                        r['type'] in ['composition','aggregation','inheritance','association'] 
                        for r in existing
                    ):
                        deps.append({
                            "from": parent_class,
                            "to": called,
                            "type": "dependency",
                            "label": "uses",
                            "arrow": "→",
                            "directed": True
                        })
        return deps

    def _detect_bidirectionals(self, relationships):
        enhanced = []
        seen = {}
        for r in relationships:
            key = (r["from"], r["to"])
            rev_key = (r["to"], r["from"])
            if rev_key in seen:
                seen[rev_key]["arrow"] = "—"
                seen[rev_key]["directed"] = False
                seen[rev_key]["bidirectional"] = True
                r["arrow"] = "—"
                r["directed"] = False
                r["bidirectional"] = True
            seen[key] = r
            enhanced.append(r)
        return enhanced

    def _detect_interface_or_abstract(self, class_node, ast_data):
        is_interface = any(
            isinstance(b, ast.Name) and b.id in ('ABC', 'Protocol') or
            isinstance(b, ast.Attribute) and b.attr in ('ABC', 'Protocol')
            for b in class_node.bases
        )

        all_abstract = True
        has_any_method = False
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef):
                has_any_method = True
                is_abs = any(
                    (isinstance(d, ast.Name) and d.id == 'abstractmethod') or
                    (isinstance(d, ast.Attribute) and d.attr == 'abstractmethod')
                    for d in node.decorator_list
                )
                if not is_abs:
                    all_abstract = False

        if is_interface or (has_any_method and all_abstract):
            return {"is_interface": True, "is_abstract": False}
        elif any(
            isinstance(n, ast.FunctionDef) and any(
                (isinstance(d, ast.Name) and d.id == 'abstractmethod') or
                (isinstance(d, ast.Attribute) and d.attr == 'abstractmethod')
                for d in n.decorator_list
            ) for n in ast.walk(class_node)
        ):
            return {"is_interface": False, "is_abstract": True}
        
        return {"is_interface": False, "is_abstract": False}

    def _merge_relationships(self, relationships):
        priority_order = {
            "composition": 1,
            "aggregation": 2,
            "inheritance": 3,
            "association": 4,
            "dependency": 5,
            "realization": 6
        }

        merged = {}
        for rel in relationships:
            key = (rel["from"], rel["to"])
            if key not in merged:
                merged[key] = rel
            else:
                current_priority = priority_order.get(merged[key]["type"], 999)
                new_priority = priority_order.get(rel["type"], 999)
                if new_priority < current_priority:
                    merged[key] = rel

        return list(merged.values())

    def _clean_duplicate_attributes(self, classes: List[Dict], relationships: List[Dict]) -> List[Dict]:
        cleaned_classes = []
        
        for class_data in classes:
            class_name = class_data.get('name')
            relationship_attributes = {rel.get('label') for rel in relationships if rel.get('from') == class_name and rel.get('label')}
            
            original_attributes = class_data.get('attributes', [])
            filtered_attributes = [attr for attr in original_attributes if attr.get('name') not in relationship_attributes]
            
            cleaned_class = class_data.copy()
            cleaned_class['attributes'] = filtered_attributes
            cleaned_classes.append(cleaned_class)
        
        return cleaned_classes

    def _is_primitive_type(self, type_name: str) -> bool:
        if not type_name:
            return True
        type_name = type_name.strip()
        if type_name in self.PRIMITIVE_TYPES:
            return True
        base_type = type_name.split('[')[0].strip()
        return base_type in self.PRIMITIVE_TYPES

    def _infer_class_from_plural_name(self, attr_name: str, all_class_names: Set[str]) -> str | None:
        name = attr_name.lower()
        singular = None
        
        if name.endswith('s'):
            singular = attr_name[:-1].capitalize()
        elif name.endswith(('_list', '_set')):
            singular = attr_name[:-5].capitalize()
        elif name.endswith('_members'):
            singular = attr_name[:-8].replace('_', ' ').title().replace(' ', '')
            
        # تجنب التخمين العشوائي (False Positives) للقوائم بدون Type Hints
        # نعيد الاسم فقط إذا كان الكلاس موجوداً، أو إذا لم نكن نملك all_class_names (في حالات معينة)
        if singular:
            if all_class_names and singular not in all_class_names:
                return None
            return singular
            
        return None

    def _unwrap_complex_type(self, type_str: str) -> str:
        for prefix in ['List[', 'Set[', 'Tuple[', 'Optional[', 'Dict[']:
            if type_str.startswith(prefix) and type_str.endswith(']'):
                inner = type_str[len(prefix):-1].strip()
                if ',' in inner:
                    return inner.split(',')[-1].strip()
                return inner
        return type_str

    def _infer_return_type(self, func_node: ast.FunctionDef) -> str:
        if func_node.returns is not None:
            return self._get_annotation_type(func_node.returns)

        for node in ast.walk(func_node):
            if isinstance(node, ast.Return) and node.value is not None:
                if isinstance(node.value, ast.Constant):
                    val = node.value.value
                    if isinstance(val, str):   return "str"
                    if isinstance(val, bool):  return "bool"
                    if isinstance(val, int):   return "int"
                    if isinstance(val, float): return "float"
                elif isinstance(node.value, (ast.JoinedStr, ast.FormattedValue)):
                    return "str"
        return "Any"

    def _get_visibility(self, name: str) -> str:
        if name.startswith('__') and not name.endswith('__'):
            return "private"
        elif name.startswith('_'):
            return "protected"
        return "public"

    def _get_annotation_type(self, ann: Any) -> str:
        if ann is None:
            return "Any"
        try:
            return ast.unparse(ann).replace("'", "").replace('"', "")
        except Exception:
            return "Any"

    def generate_class_diagram_data(self, ast_data: Dict[str, Any], features: Dict[str, Any]) -> Dict[str, Any]:
        return self.generate_uml_diagram(ast_data)

    def generate_dependency_graph_data(self, ast_data: Dict[str, Any], features: Dict[str, Any]) -> Dict[str, Any]:
        code = ast_data.get("code_content", "")
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"nodes": [], "edges": []}
        
        dependencies = self.extract_dependencies(ast_data)
        nodes = [{"id": "main", "label": "Main Module", "type": "module"}]
        edges = []
        
        for i, dep in enumerate(dependencies):
            nodes.append({"id": f"dep_{i}", "label": dep, "type": "dependency"})
            edges.append({"from": "main", "to": f"dep_{i}", "label": "imports", "arrow": "→"})

        return {"nodes": nodes, "edges": edges}