"""
TreeSitterProcessor - Final Fixed Version
"""

import logging
from typing import Dict, Any, List, Optional

from .base_processor import ILanguageProcessorStrategy

logger = logging.getLogger(__name__)

try:
    from tree_sitter import Parser
    TREE_SITTER_CORE = True
except ImportError:
    TREE_SITTER_CORE = False
    logger.error("[TreeSitterProcessor] tree-sitter core not installed")

try:
    from tree_sitter_languages import get_language as _tsl_get
    TREE_SITTER_LANGUAGES = True
except ImportError:
    TREE_SITTER_LANGUAGES = False


def _load_language(ts_name: str, file_type: str):
    if TREE_SITTER_LANGUAGES:
        try:
            return _tsl_get(ts_name)
        except Exception:
            pass

    STANDALONE = {
        "javascript":  ("tree_sitter_javascript",  "language"),
        "typescript":  ("tree_sitter_typescript",  "language"),
        "python":      ("tree_sitter_python",       "language"),
        "java":        ("tree_sitter_java",         "language"),
        "go":          ("tree_sitter_go",           "language"),
        "rust":        ("tree_sitter_rust",         "language"),
        "c":           ("tree_sitter_c",            "language"),
        "cpp":         ("tree_sitter_cpp",          "language"),
        "c_sharp":     ("tree_sitter_c_sharp",      "language"),
        "kotlin":      ("tree_sitter_kotlin",       "language"),
        "ruby":        ("tree_sitter_ruby",         "language"),
        "php":         ("tree_sitter_php",          "language_php"),
    }

    if ts_name in STANDALONE:
        pkg_name, attr = STANDALONE[ts_name]
        try:
            import importlib
            mod = importlib.import_module(pkg_name)
            fn = getattr(mod, attr)
            return fn()
        except Exception as e:
            logger.debug(f"[_load_language] standalone {pkg_name} failed: {e}")

    raise ImportError(f"Cannot load tree-sitter grammar for '{ts_name}'")


LANGUAGE_CONFIG: Dict[str, Dict[str, Any]] = {
    "javascript": {
        "ts_name":         "javascript",
        "function_types":  ["function_declaration", "arrow_function", "function_expression",
                            "generator_function_declaration", "method_definition"],
        "class_types":     ["class_declaration", "class_expression"],
        "import_types":    ["import_statement"],
        "comment_types":   ["comment"],
        "complexity_types":["if_statement", "for_statement", "while_statement",
                            "switch_statement", "catch_clause", "ternary_expression"],
    },
    "typescript": {
        "ts_name":         "typescript",
        "function_types":  ["function_declaration", "arrow_function", "function_expression",
                            "method_definition", "method_signature"],
        "class_types":     ["class_declaration", "abstract_class_declaration",
                            "interface_declaration", "type_alias_declaration", "enum_declaration"],
        "import_types":    ["import_statement"],
        "comment_types":   ["comment"],
        "complexity_types":["if_statement", "for_statement", "while_statement",
                            "switch_statement", "catch_clause", "ternary_expression"],
    },
    "go": {
        "ts_name": "go", "function_types": ["function_declaration", "method_declaration"],
        "class_types": ["type_declaration"], "import_types": ["import_declaration", "import_spec"],
        "comment_types": ["comment"], "complexity_types": ["if_statement", "for_statement", "switch_statement"],
    },
    "rust": {
        "ts_name": "rust", "function_types": ["function_item"],
        "class_types": ["struct_item", "enum_item", "trait_item", "impl_item"],
        "import_types": ["use_declaration"], "comment_types": ["line_comment", "block_comment"],
        "complexity_types": ["if_expression", "for_expression", "while_expression", "match_expression"],
    },
    "kotlin": {
        "ts_name": "kotlin", "function_types": ["function_declaration", "anonymous_function"],
        "class_types": ["class_declaration", "object_declaration", "interface_declaration"],
        "import_types": ["import_header"], "comment_types": ["multiline_comment", "line_comment"],
        "complexity_types": ["if_expression", "when_expression", "for_statement", "while_statement"],
    },
    "ruby": {
        "ts_name": "ruby", "function_types": ["method", "singleton_method"],
        "class_types": ["class", "module"], "import_types": ["call"],
        "comment_types": ["comment"], "complexity_types": ["if", "unless", "while", "for", "case"],
    },
    "php": {
        "ts_name": "php", "function_types": ["function_definition", "method_declaration"],
        "class_types": ["class_declaration", "interface_declaration", "trait_declaration"],
        "import_types": ["namespace_use_declaration"], "comment_types": ["comment"],
        "complexity_types": ["if_statement", "for_statement", "foreach_statement", "while_statement"],
    },
    "c": {
        "ts_name": "c", "function_types": ["function_definition"],
        "class_types": ["struct_specifier", "enum_specifier"], "import_types": ["preproc_include"],
        "comment_types": ["comment"], "complexity_types": ["if_statement", "for_statement", "while_statement"],
    },
    "cpp": {
        "ts_name": "cpp", "function_types": ["function_definition"],
        "class_types": ["class_specifier", "struct_specifier", "enum_specifier"],
        "import_types": ["preproc_include"], "comment_types": ["comment"],
        "complexity_types": ["if_statement", "for_statement", "while_statement", "try_statement"],
    },
    "csharp": {
        "ts_name": "c_sharp",
        "function_types": ["method_declaration", "constructor_declaration", "local_function_statement"],
        "class_types": ["class_declaration", "interface_declaration", "struct_declaration", "record_declaration"],
        "import_types": ["using_directive"], "comment_types": ["comment"],
        "complexity_types": ["if_statement", "for_statement", "for_each_statement", "while_statement"],
    },
}

SUPPORTED_LANGUAGES = set(LANGUAGE_CONFIG.keys())

_INHERITANCE_NODE_TYPES = {
    "base_class_clause", "superclass", "base_list", "base_clause",
    "extends_clause", "implements_clause",
}

_BODY_CONTAINERS = {
    "field_declaration_list", "declaration_list", "class_body",
    "interface_body", "enum_body", "struct_body", "block",
}

# ✅ إضافة public_field_definition
_FIELD_NODE_TYPES = {
    "field_declaration", "variable_declarator", "property_declaration",
    "public_field_definition", "field_definition",
    "val_declaration", "var_declaration", "instance_variable", "member_declaration",
}


class TreeSitterProcessor(ILanguageProcessorStrategy):

    def __init__(self, file_type: str):
        self.file_type = file_type
        self._config = LANGUAGE_CONFIG.get(file_type, {})
        self._parser: Optional[object] = None
        self._ready = False
        self._init_parser()

    def _init_parser(self):
        if not TREE_SITTER_CORE or not self._config:
            return
        try:
            ts_name = self._config["ts_name"]
            language = _load_language(ts_name, self.file_type)
            self._parser = Parser()
            self._parser.set_language(language)
            self._ready = True
        except Exception as e:
            logger.error(f"[TreeSitterProcessor] Init failed: {e}")

    def parse_source_code(self, code_content: str) -> Dict[str, Any]:
        if not code_content or not code_content.strip():
            return {"ast_tree": None, "code_content": "", "language": self.file_type, "error": "Empty file"}
        if not self._ready:
            return {"ast_tree": None, "code_content": code_content, "language": self.file_type,
                    "error": f"Parser not ready"}
        try:
            tree = self._parser.parse(code_content.replace("\r\n", "\n").encode("utf-8"))
            return {"ast_tree": tree, "code_content": code_content, "language": self.file_type}
        except Exception as e:
            return {"ast_tree": None, "code_content": code_content, "language": self.file_type, "error": str(e)}

    def extract_features(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        tree = ast_data.get("ast_tree")
        code_content = ast_data.get("code_content", "")
        cfg = self._config

        if not tree or not tree.root_node:
            return self._empty_features(code_content)

        function_types = set(cfg.get("function_types", []))
        class_types = set(cfg.get("class_types", []))
        comment_types = set(cfg.get("comment_types", []))
        complexity_types = set(cfg.get("complexity_types", []))

        functions, classes = [], []
        comments, complexity, inheritances = 0, 1, 0

        for node in self._walk(tree):
            ntype = node.type
            if ntype in function_types:
                name = self._get_name(node)
                if name:
                    parent = self._find_parent_class_name_safe(node)
                    functions.append({"name": name, "line": node.start_point[0] + 1, "class": parent or "Global"})
            elif ntype in class_types:
                name = self._get_name(node)
                if name:
                    classes.append({"name": name, "line": node.start_point[0] + 1})
            elif ntype in comment_types:
                comments += 1
            elif ntype in _INHERITANCE_NODE_TYPES:
                inheritances += 1

            if ntype in complexity_types or ntype in {"else_clause", "case", "default", "try_statement"}:
                complexity += 1

        complexity = min(complexity, 100)  
        lines = code_content.splitlines()
        total_lines = len(lines)
        blank_lines = sum(1 for l in lines if not l.strip())
        code_lines = max(0, total_lines - comments - blank_lines)
        ratio = round(comments / total_lines, 2) if total_lines > 0 else 0.0

        return {
            "language": self.file_type, "lines_of_code": code_lines, "total_lines": total_lines,
            "comment_lines": comments, "blank_lines": blank_lines, "comment_ratio": ratio,
            "num_functions": len(functions), "num_classes": len(classes),
            "complexity_score": complexity, "num_inheritances": inheritances,
            "num_async_functions": 0, "functions": [f["name"] for f in functions],
            "classes": [c["name"] for c in classes], "function_details": functions,
        }

    def extract_dependencies(self, ast_data: Dict[str, Any]) -> List[str]:
        tree = ast_data.get("ast_tree")
        if not tree or not tree.root_node:
            return []
        import_types = set(self._config.get("import_types", []))
        deps = []
        for node in self._walk(tree):
            if node.type in import_types:
                text = self._node_text(node)
                if text and text not in deps:
                    deps.append(text)
        return deps

    def perform_semantic_analysis(self, ast_data: Dict[str, Any], features: Dict[str, Any]) -> Dict[str, Any]:
        tree = ast_data.get("ast_tree")
        if not tree:
            return {"quality_score": 0, "issues": ["Parse failed"], "warnings": [], "complexity": 0}

        issues, warnings = [], []
        loc = features.get("lines_of_code", 0)
        complexity = features.get("complexity_score", 0)
        ratio = features.get("comment_ratio", 0.0)

        if ratio < 0.05 and loc > 50:
            warnings.append("Low comment coverage (< 5%).")
        if complexity > 30:
            issues.append(f"High complexity ({complexity}).")

        # ✅ كشف private access
        if self.file_type in ["typescript", "javascript"]:
            for v in self._check_private_access(tree):
                issues.append(f"Private access: '{v['member']}' of {v['class']} at {v['access_location']}")

        penalty = (len(issues) * 8) + (len(warnings) * 3) + (complexity * 0.2)
        quality = round(max(0.0, 100.0 - penalty), 2)

        return {"quality_score": quality, "issues": issues, "warnings": warnings, "complexity": complexity}

    def generate_class_diagram_data(self, ast_data: Dict[str, Any], features: Dict[str, Any]) -> Dict[str, Any]:
        tree = ast_data.get("ast_tree")
        if not tree or not tree.root_node:
            return {"classes": [], "relationships": []}

        class_types = set(self._config.get("class_types", []))
        classes = []
        all_relationships = []

        for node in self._walk(tree):
            if node.type not in class_types:
                continue

            name = self._get_name(node)
            if not name:
                continue

            methods       = self._extract_detailed_methods(node)
            attributes    = self._extract_detailed_attributes(node)
            relationships = self._extract_relationships_in_node(node, name)

            is_generic  = "<" in name or self._has_type_parameters(node)
            is_abstract = self._is_abstract_class(node)

            class_entry = {
                "name":          name,
                "type":          "generic_class" if is_generic else node.type,
                "methods":       methods,
                "attributes":    attributes,
                "relationships": relationships,
                "is_generic":    is_generic,
                "is_abstract":   is_abstract,
                "is_interface":  node.type == "interface_declaration",
            }

            classes.append(class_entry)
            all_relationships.extend(relationships)

        return {"classes": classes, "relationships": all_relationships}

    def generate_dependency_graph_data(self, ast_data: Dict[str, Any], features: Dict[str, Any]) -> Dict[str, Any]:
        deps = self.extract_dependencies(ast_data)
        nodes = [{"id": "main", "label": f"[{self.file_type}] module", "type": "module"}]
        edges = []
        for i, dep in enumerate(deps):
            nid = f"dep_{i}"
            nodes.append({"id": nid, "label": dep, "type": "dependency"})
            edges.append({"from": "main", "to": nid, "label": "imports", "arrow": "=>"})
        return {"nodes": nodes, "edges": edges}

    # ═══════════════════════════════════════════════════════════════
    # HELPERS - الإصلاحات الرئيسية هنا
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def _walk(tree):
        cursor = tree.walk()
        reached_root = False
        while not reached_root:
            yield cursor.node
            if cursor.goto_first_child():
                continue
            if cursor.goto_next_sibling():
                continue
            while cursor.goto_parent():
                if cursor.goto_next_sibling():
                    break
            else:
                reached_root = True

    @staticmethod
    def _get_name(node) -> Optional[str]:
        # Skip anonymous arrow functions
        if node.type == "arrow_function":
            if node.parent and node.parent.type == "variable_declarator":
                nc = node.parent.child_by_field_name("name")
                if nc and nc.text:
                    return nc.text.decode("utf-8", errors="replace").strip()
            return None

        # Try name field first
        name_child = node.child_by_field_name("name")
        if name_child and name_child.text:
            base = name_child.text.decode("utf-8", errors="replace").strip()
            tp = node.child_by_field_name("type_parameters") or node.child_by_field_name("type_parameter_list")
            if tp and tp.text:
                return f"{base}{tp.text.decode('utf-8', errors='replace').strip()}"
            return base

        # ✅ إصلاح: إضافة property_identifier لـ method_signature في interfaces
        for child in node.children:
            if child.type in ("identifier", "property_identifier") and child.text:
                base = child.text.decode("utf-8", errors="replace").strip()
                for sib in node.children:
                    if sib.type in ("type_parameters", "type_parameter_list") and sib.text:
                        return f"{base}{sib.text.decode('utf-8', errors='replace').strip()}"
                return base
        return None

    @staticmethod
    def _node_text(node) -> Optional[str]:
        try:
            return node.text.decode("utf-8", errors="replace").strip() if node.text else None
        except Exception:
            return None

    def _find_parent_class_name_safe(self, node) -> Optional[str]:
        if not node:
            return None
        current = node.parent
        class_types = set(self._config.get("class_types", []))
        while current:
            if current.type in class_types:
                name = self._get_name(current)
                if name:
                    return name
            current = getattr(current, 'parent', None)
        return None

    def _extract_detailed_methods(self, class_node) -> List[Dict]:
        """استخراج الدوال مع تفاصيل غنية مشابهة لمعالج Python"""
        function_types = set(self._config.get("function_types", []))
        methods = []

        def _scan(node, depth=0):
            if depth > 5:
                return
            for child in node.children:
                if child.type in function_types:
                    name = self._get_name(child)
                    if not name:
                        continue

                    methods.append({
                        "name": name,
                        "signature": self._build_method_signature(child, name),
                        "is_abstract": self._is_abstract_method(child) or child.type == "method_signature",
                        "is_constructor": name in ("__init__", "constructor") or child.type == "constructor_declaration",
                        "visibility": self._get_visibility(child),
                        "is_override": self._has_modifier(child, "override"),
                    })

                elif child.type in _BODY_CONTAINERS or child.type in {"block", "declaration_list"}:
                    _scan(child, depth + 1)

        _scan(class_node)
        return methods

    def _extract_detailed_attributes(self, class_node) -> List[str]:
        attributes = []

        def _scan(node):
            for child in node.children:
                # ✅ إضافة public_field_definition
                if child.type in _FIELD_NODE_TYPES:
                    attributes.extend(self._get_field_names(child))
                elif child.type in _BODY_CONTAINERS:
                    _scan(child)

        _scan(class_node)

        # ✅ إصلاح: استخراج الحقول من constructor parameters (TypeScript feature)
        if self.file_type == "typescript":
            attributes.extend(self._extract_constructor_properties(class_node))

        return list(set(attributes))  # إزالة التكرار

    def _extract_constructor_properties(self, class_node) -> List[str]:
        """Extract properties defined in constructor parameters"""
        props = []
        # Find class_body first for TypeScript
        class_body = next(
            (c for c in class_node.children if c.type == "class_body"), 
            None
        )
        search_in = class_body.children if class_body else class_node.children
        
        for child in search_in:
            if child.type == "method_definition" and self._get_name(child) == "constructor":
                params = child.child_by_field_name("parameters")
                if params:
                    for param in params.children:
                        if param.type in ("required_parameter", "optional_parameter"):
                            # Check for accessibility modifier
                            for sub in param.children:
                                if sub.type in ("accessibility_modifier", "readonly_modifier"):
                                    name = self._get_name(param)
                                    if name:
                                        props.append(name)
                                    break
        return props

    def _build_method_signature(self, method_node, name: str) -> str:
        params = self._extract_parameters(method_node)
        return_type = self._extract_return_type(method_node)
        param_str = ", ".join(params) if params else ""

        if name in ("constructor", "__init__"):
            return f"constructor({param_str})"
        
        sig = f"{name}({param_str})"
        if return_type and return_type.lower() not in ("any", "void", ""):
            sig += f": {return_type}"
        return sig

    def _extract_parameters(self, method_node) -> List[str]:
        params = []
        param_list = (method_node.child_by_field_name("parameters") or
                      method_node.child_by_field_name("formal_parameters") or
                      method_node.child_by_field_name("parameter_list"))

        if param_list:
            for child in param_list.children:
                if child.type in {"parameter", "formal_parameter", "required_parameter", "optional_parameter"}:
                    p_name = self._get_name(child)
                    p_type = self._get_parameter_type(child)
                    if p_name:
                        if p_type and p_type.lower() != "any":
                            params.append(f"{p_name}: {p_type}")
                        else:
                            params.append(p_name)
        return params

    def _get_parameter_type(self, param_node) -> str:
        for child in param_node.children:
            if child.type in (":", "colon", "punctuation", 
                          "accessibility_modifier", "readonly_modifier"):
                continue
            if child.type in ("type_identifier", "predefined_type", 
                          "union_type", "generic_type") and child.text:
                return child.text.decode("utf-8", errors="replace").strip().lstrip(":").strip()
        return "any"

    def _extract_return_type(self, method_node) -> str:
        # ✅ TypeScript uses return_type field
        return_type_node = method_node.child_by_field_name("return_type")
        if return_type_node:
            # Check for type_annotation wrapper
            for child in return_type_node.children:
                if child.type == "type_annotation":
                    for gc in child.children:
                        if gc.type in ("type_identifier", "predefined_type", "void_type") and gc.text:
                            return gc.text.decode("utf-8", errors="replace").strip()
                elif child.type in (":", "punctuation"):
                    continue
                elif child.type in ("type_identifier", "predefined_type", "void_type") and child.text:
                    return child.text.decode("utf-8", errors="replace").strip()
            # Fallback: get text and strip colon
            if return_type_node.text:
                return return_type_node.text.decode("utf-8", errors="replace").strip().lstrip(":").strip()
        return ""

    def _is_abstract_method(self, method_node) -> bool:
        return self._has_modifier(method_node, "abstract")

    # ✅ إصلاح: كشف modifiers بشكل صحيح
    def _has_modifier(self, node, modifier: str) -> bool:
        for child in node.children:
            # الموديفاير قد يكون نوعه نفس الاسم أو "modifier"
            if child.type == modifier:
                return True
            if child.type == "modifier" and child.text:
                if modifier.lower() == child.text.decode("utf-8", errors="replace").strip().lower():
                    return True
            if child.type == "accessibility_modifier" and child.text:
                if modifier.lower() == child.text.decode("utf-8", errors="replace").strip().lower():
                    return True
        return False

    def _get_visibility(self, node) -> str:
        for child in node.children:
            if child.type == "accessibility_modifier" and child.text:
                text = child.text.decode("utf-8", errors="replace").strip().lower()
                if text in ("public", "private", "protected"):
                    return text
        return "public"

    def _is_abstract_class(self, class_node) -> bool:
        return (self._has_modifier(class_node, "abstract") or
                class_node.type == "interface_declaration")

    # ✅ إصلاح: كشف private access مع public_field_definition
    def _check_private_access(self, tree) -> List[Dict[str, Any]]:
        violations = []
        private_members = {}

        for node in self._walk(tree):
            if node.type not in self._config.get("class_types", []):
                continue
            class_name = self._get_name(node)
            if not class_name:
                continue

            private_members[class_name] = set()
            
            # ✅ Find class_body first for TypeScript
            class_body = None
            for child in node.children:
                if child.type in ("class_body", "interface_body", "block"):
                    class_body = child
                    break
            
            # Search in class_body if found, otherwise in direct children
            search_children = class_body.children if class_body else node.children
            
            for child in search_children:
                is_private = False
                member_name = None

                # ✅ إضافة public_field_definition
                if child.type in ("public_field_definition", "field_definition"):
                    for sub in child.children:
                        if sub.type == "accessibility_modifier" and sub.text:
                            if "private" in sub.text.decode("utf-8", errors="replace").lower():
                                is_private = True
                        elif sub.type in ("property_identifier", "identifier") and sub.text:
                            member_name = sub.text.decode("utf-8", errors="replace").strip()

                elif child.type in ("property_declaration", "method_definition"):
                    if self._get_visibility(child) == "private":
                        is_private = True
                        member_name = self._get_name(child)

                if is_private and member_name:
                    private_members[class_name].add(member_name)

        # Check access
        for node in self._walk(tree):
            if node.type != "member_expression":
                continue
            prop_node = node.child_by_field_name("property")
            if not prop_node:
                continue
            prop_name = self._node_text(prop_node)
            if not prop_name:
                continue

            for class_name, priv_set in private_members.items():
                if prop_name in priv_set:
                    current_class = self._find_parent_class_name_safe(node)
                    if current_class != class_name:
                        violations.append({
                            "member": prop_name,
                            "class": class_name,
                            "access_location": f"line {node.start_point[0] + 1}",
                            "accessed_from": current_class or "global scope"
                        })
                        break

        return violations

    def _extract_relationships_in_node(self, class_node, class_name: str) -> List[dict]:
        INHERITANCE_CONTAINERS = {
            "base_class_clause", "superclass", "class_heritage",
            "extends_clause", "implements_clause", "base_clause", "base_list",
        }
        relationships = []
        for child in class_node.children:
            if child.type not in INHERITANCE_CONTAINERS:
                continue
            rel_type = "implements" if "implement" in child.type else "inherits"
            for gc in child.children:
                if gc.type in ("type_identifier", "identifier") and gc.text:
                    parent = gc.text.decode("utf-8", errors="replace").strip()
                    if parent not in ("public", "protected", "private", ":", ","):
                        relationships.append({"type": rel_type, "from": class_name, "to": parent})
                elif gc.type in INHERITANCE_CONTAINERS:
                    for ggc in gc.children:
                        if ggc.type in ("type_identifier", "identifier") and ggc.text:
                            parent = ggc.text.decode("utf-8", errors="replace").strip()
                            relationships.append({"type": "implements" if "implement" in gc.type else "inherits",
                                                  "from": class_name, "to": parent})
        return relationships

    @staticmethod
    def _get_field_names(field_node) -> List[str]:
        names = []
        for child in field_node.children:
            ct = child.type
            # ✅ إضافة property_identifier
            if ct in ("field_identifier", "property_identifier") and child.text:
                names.append(child.text.decode("utf-8", errors="replace").strip())
            elif ct in ("variable_declarator", "field_declarator"):
                for gc in child.children:
                    if gc.type in ("identifier", "field_identifier", "property_identifier") and gc.text:
                        names.append(gc.text.decode("utf-8", errors="replace").strip())
            elif ct == "identifier" and child.text and not names:
                names.append(child.text.decode("utf-8", errors="replace").strip())
        if not names:
            nc = field_node.child_by_field_name("name")
            if nc and nc.text:
                names.append(nc.text.decode("utf-8", errors="replace").strip())
        return names

    @staticmethod
    def _has_type_parameters(class_node) -> bool:
        return any(c.type in ("type_parameters", "type_parameter_list") for c in class_node.children)

    def _count_errors(self, tree) -> int:
        return sum(1 for n in self._walk(tree) if n.type == "ERROR" or n.is_missing)

    def _empty_features(self, code_content: str) -> Dict[str, Any]:
        lines = (code_content or "").splitlines()
        return {
            "language": self.file_type, "lines_of_code": len(lines), "total_lines": len(lines),
            "comment_lines": 0, "blank_lines": 0, "comment_ratio": 0.0,
            "num_functions": 0, "num_classes": 0, "complexity_score": 0,
            "num_inheritances": 0, "num_async_functions": 0,
            "functions": [], "classes": [], "function_details": [],
        }