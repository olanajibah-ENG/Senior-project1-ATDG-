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
        'Callable', 'Iterable', 'Iterator', 'Generator'
    }
    
    TECHNICAL_BASE_CLASSES = {
        'ABC', 'object', 'Object', 'Enum', 'IntEnum',
        'Exception', 'BaseException', 'NamedTuple'
    }
    
    def _normalize_python_code(self, code_content: str) -> Dict[str, Any]:
        original_code = code_content
        normalized_code = code_content
        fixes_applied = []
        
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
        """Parse source code and return minimal required data"""
        try:
            tree = ast.parse(code_content)
            return {"parsed": True,
                    "code_content": code_content  # ← أضف هذا فقط
                   }
        except SyntaxError as e:
            return {"parsed": False, "error": str(e)}

    def extract_features(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features from AST data"""
        code = ast_data.get("code_content", "")
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {
                "lines_of_code": 0,
                "num_classes": 0,
                "num_functions": 0,
                "num_async_functions": 0,
                "complexity_score": 0,
                "class_names": [],
                "function_names": [],
                "routes": [],
                "validation_blocks": []
            }

        features = {
            "lines_of_code": len(code.splitlines()),
            "num_classes": 0,
            "num_functions": 0,
            "num_async_functions": 0,
            "complexity_score": 0,
            "class_names": [],
            "function_names": [],
            "routes": [],
            "validation_blocks": []
        }

        class FeatureVisitor(ast.NodeVisitor):
            def __init__(self):
                self.complexity = 0
                self.current_function = None
                self._inside_class = False
            
            def visit_If(self, node):
                self.complexity += 1
                self.generic_visit(node)
            
            def visit_For(self, node):
                self.complexity += 1
                self.generic_visit(node)
            
            def visit_While(self, node):
                self.complexity += 1
                self.generic_visit(node)
            
            def visit_Try(self, node):
                self.complexity += 1
                self.generic_visit(node)
            
            def visit_ExceptHandler(self, node):
                self.complexity += 1
                self.generic_visit(node)
            
            def visit_ClassDef(self, node):
                features["num_classes"] += 1
                features["class_names"].append(node.name)
                
                # Extract methods from class
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        features["function_names"].append(item.name)
                
                prev = self._inside_class
                self._inside_class = True
                self.generic_visit(node)
                self._inside_class = prev
            
            def visit_FunctionDef(self, node):
                features["num_functions"] += 1
                if not self._inside_class:
                    features["function_names"].append(node.name)
                self.current_function = node.name
                
                # Check for validation blocks
                self._check_validation_blocks(node)
                
                self.generic_visit(node)
            
            def visit_AsyncFunctionDef(self, node):
                features["num_async_functions"] += 1
                features["function_names"].append(node.name)
                self.current_function = node.name
                
                # Check for validation blocks
                self._check_validation_blocks(node)
                
                self.generic_visit(node)
            
            def _check_validation_blocks(self, node):
                """Check for validation patterns in function"""
                for stmt in ast.walk(node):
                    if isinstance(stmt, ast.If):
                        # Look for validation patterns
                        for test_node in ast.walk(stmt.test):
                            if isinstance(test_node, ast.Compare):
                                # Check if this returns an error response
                                for inner_stmt in stmt.body:
                                    if isinstance(inner_stmt, ast.Return):
                                        if isinstance(inner_stmt.value, ast.Call):
                                            func = inner_stmt.value.func
                                            if isinstance(func, ast.Attribute):
                                                if func.attr in ['jsonify', 'abort', 'make_response']:
                                                    error_msg = "Validation error response"
                                                    if isinstance(inner_stmt.value.args, list) and inner_stmt.value.args:
                                                        error_msg = str(inner_stmt.value.args[0])
                                                    
                                                    features["validation_blocks"].append({
                                                        "function": self.current_function,
                                                        "condition": "Input validation check",
                                                        "error_response": error_msg
                                                    })
        
        visitor = FeatureVisitor()
        visitor.visit(tree)
        
        features["complexity_score"] = visitor.complexity
        
        # Extract routes
        features["routes"] = self._extract_routes_from_code(tree)
        
        return features
    
    def _extract_routes_from_code(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract Flask/Django routes from AST"""
        routes = []
        
        class RouteVisitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                # Check for Flask decorators
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call):
                        func = decorator.func
                        if isinstance(func, ast.Attribute):
                            if func.attr == "route":
                                # Extract path
                                if decorator.args:
                                    path = ast.literal_eval(decorator.args[0])
                                else:
                                    path = "/"
                                
                                # Extract methods
                                methods = ["GET"]
                                for keyword in decorator.keywords:
                                    if keyword.arg == "methods":
                                        methods = ast.literal_eval(keyword.value)
                                
                                routes.append({
                                    "path": path,
                                    "methods": methods,
                                    "handler": node.name
                                })
                
                self.generic_visit(node)
        
        visitor = RouteVisitor()
        visitor.visit(tree)
        
        return routes

    def extract_dependencies(self, ast_data: Dict[str, Any]) -> List[str]:
        """Extract imported dependencies"""
        code = ast_data.get("code_content", "")
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
        
        dependencies = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dependencies.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    dependencies.add(node.module.split('.')[0])
        
        return list(dependencies)
        
    def perform_semantic_analysis(self, ast_data: Dict[str, Any], features: Dict[str, Any]) -> Dict[str, Any]:
        """Perform semantic analysis"""
        code = ast_data.get("code_content", "")
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"quality_score": 0, "issues": ["Invalid syntax"], "warnings": [], "complexity": 0}

        quality_score = 100
        issues = []
        warnings = []
        
        class SemanticVisitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                nonlocal quality_score
                has_validation = False
                for stmt in node.body:
                    if isinstance(stmt, ast.If):
                        if "request" in ast.dump(stmt) or "input" in ast.dump(stmt):
                            has_validation = True
                            break
                
                if not has_validation and any(param.arg in ['request', 'data', 'input'] for param in node.args.args):
                    quality_score -= 5
                    issues.append(f"Missing input validation in function '{node.name}'")
                
                has_error_handling = any(isinstance(stmt, ast.Try) for stmt in node.body)
                
                if not has_error_handling:
                    quality_score -= 3
                    issues.append(f"Missing error handling in function '{node.name}'")
                
                self.generic_visit(node)
            
            def visit_Call(self, node):
                nonlocal quality_score
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr == "get" and isinstance(node.func.value, ast.Name):
                        if node.func.value.id in ["Query", "session"]:
                            quality_score -= 5
                            issues.append("Using deprecated Query.get() pattern")
                
                self.generic_visit(node)
        
        visitor = SemanticVisitor()
        visitor.visit(tree)
        
        complexity = sum(1 for _ in ast.walk(tree) if isinstance(_, (ast.If, ast.For, ast.While, ast.Try, ast.ExceptHandler)))
        
        return {
            "quality_score": max(0, quality_score),
            "issues": issues,
            "warnings": warnings,
            "complexity": complexity
        }

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
            elif unwrapped in all_class_names:
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
                if called in all_class_names:
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
                if not isinstance(stmt, ast.Assign):
                    continue
                for target in stmt.targets:
                    if not (isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self'):
                        continue

                    attr_name = target.attr
                    attr_info = self._infer_attribute_type(attr_name, stmt.value, {}, all_class_names)

                    if attr_info["type"] == "Any":
                        continue

                    if isinstance(stmt.value, ast.Call) and isinstance(stmt.value.func, ast.Name):
                        called = stmt.value.func.id
                        if called in all_class_names and not self._is_primitive_type(called):
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

                    if attr_info["is_collection"] and attr_info["inner_type"] in all_class_names:
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

                    if attr_info["type"] in all_class_names and not attr_info["is_collection"]:
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

            return rels

    def _extract_all_dependencies(self, tree, all_class_names, existing):
        deps = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                called = node.func.id
                if called in all_class_names and not self._is_primitive_type(called):
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
        if name.endswith('s'):
            singular = attr_name[:-1].capitalize()
            if singular in all_class_names:
                return singular
        if name.endswith(('_list', '_set')):
            base = attr_name[:-5].capitalize()
            if base in all_class_names:
                return base
        if name.endswith('_members'):
            base = attr_name[:-8].replace('_', ' ').title().replace(' ', '')
            if base in all_class_names:
                return base
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

    def generate_uml_diagram(self, ast_data: dict) -> dict:
        """Generate class diagram data from AST"""
        classes = []
        
        def walk(node):
            if isinstance(node, dict):
                if node.get("node_type") == "ClassDef":
                    methods = []
                    for item in node.get("body", []):
                        if isinstance(item, dict) and item.get("node_type") == "FunctionDef":
                            method_name = item.get("name", "")
                            args = item.get("args", {}).get("args", [])
                            params = [a.get("arg", "") for a in args if a.get("arg") != "self"]
                            methods.append({
                                "name": method_name,
                                "signature": f"{method_name}({', '.join(params)}): Any",
                                "is_abstract": False,
                                "visibility": "public",
                                "is_constructor": method_name == "__init__"
                            })
                    
                    base_classes = []
                    for base in node.get("bases", []):
                        if isinstance(base, dict):
                            base_name = base.get("id") or base.get("attr", "")
                            if base_name:
                                base_classes.append(base_name)
                    
                    classes.append({
                        "name": node.get("name", ""),
                        "attributes": [],
                        "methods": methods,
                        "base_classes": base_classes,
                        "is_abstract": False,
                        "is_interface": False
                    })
                
                for value in node.values():
                    if isinstance(value, (dict, list)):
                        walk(value)
            elif isinstance(node, list):
                for item in node:
                    walk(item)
        
        walk(ast_data)
        
        return {
            "classes": classes,
            "relationships": []
        }

    def generate_class_diagram_data(self, ast_data: Dict[str, Any], features: Dict[str, Any]) -> Dict[str, Any]:
        code = ast_data.get("code_content", "")
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"classes": [], "relationships": []}

        classes = []

        class ClassVisitor(ast.NodeVisitor):
            def visit_ClassDef(self, node):
                class_info = {
                    "name": node.name,
                    "attributes": [],
                    "methods": [],
                    "base_classes": [base.id if isinstance(base, ast.Name)
                                    else f"{base.value.id}.{base.attr}" if isinstance(base, ast.Attribute)
                                    else ""
                                    for base in node.bases
                                    ],
                    "is_abstract": False,
                    "is_interface": False
                }

                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                class_info["attributes"].append({
                                    "name": target.id,
                                    "type": None
                                })
                    elif isinstance(item, ast.FunctionDef):
                        params = [arg.arg for arg in item.args.args if arg.arg != "self"]
                        method_info = {
                            "name": item.name,
                            "signature": f"{item.name}({', '.join(params)}): Any",
                            "is_abstract": False,
                            "visibility": "public",
                            "is_constructor": item.name == "__init__"
                        }
                        class_info["methods"].append(method_info)

                classes.append(class_info)
                self.generic_visit(node)

        ClassVisitor().visit(tree)
        return {"classes": classes, "relationships": []}

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