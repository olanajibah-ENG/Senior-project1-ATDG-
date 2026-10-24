"""
java_processor.py
=================
معالج Java المحسّن باستخدام Tree-sitter.

✅ تحليل شامل: Features + Dependencies + Semantic + UML
✅ يعتمد على code_content مباشرة (لا يحفظ AST ضخم)
✅ معالجة Generic Types: List<Employee>, Set<Book>
✅ استخراج العلاقات من Fields + Constructors
✅ دمج العلاقات بالأولوية (composition > aggregation > ...)
✅ كشف العلاقات ثنائية الاتجاه
✅ دعم Abstract Classes و Interfaces
✅ توافق كامل مع ILanguageProcessorStrategy
"""

from .base_processor import ILanguageProcessorStrategy
from typing import Dict, Any, List, Set
import logging
import re
from tree_sitter import Parser

try:
    import tree_sitter_java
    USE_DIRECT_IMPORT = True
except ImportError:
    USE_DIRECT_IMPORT = False

try:
    from tree_sitter_languages import get_language
    USE_LANGUAGES_LIB = True
except ImportError:
    USE_LANGUAGES_LIB = False

logger = logging.getLogger(__name__)


class JavaProcessor(ILanguageProcessorStrategy):
    """
    معالج Java محسّن مع جميع ميزات معالج Python
    ✅ تصفية الأنواع البدائية
    ✅ دمج العلاقات (الأولوية للأقوى)
    ✅ معالجة الموروثات التقنية
    ✅ تحديد الأنواع من Collections
    ✅ إخفاء Constructors من Methods
    ✅ دعم Abstract Classes و Interfaces
    ✅ استنتاج ذكي للأنواع
    ✅ علاقات ثنائية الاتجاه
    """
    
    # ═══════════════════════════════════════════════════════
    # 🔧 PRIMITIVE TYPES - لتصفية الأنواع البدائية
    # ═══════════════════════════════════════════════════════
    PRIMITIVE_TYPES = {
        'int', 'long', 'short', 'byte', 'float', 'double', 'char', 'boolean',
        'String', 'Integer', 'Long', 'Short', 'Byte', 'Float', 'Double',
        'Character', 'Boolean', 'void', 'Void',
        # Collections (generic types - will be filtered)
        'List', 'ArrayList', 'LinkedList', 'Set', 'HashSet', 'TreeSet',
        'Map', 'HashMap', 'TreeMap', 'Queue', 'Deque', 'Collection',
        'Vector', 'Stack', 'PriorityQueue', 'LinkedHashSet', 'LinkedHashMap',
        'Properties', 'Hashtable', 'BitSet', 'EnumSet', 'EnumMap'
    }
    
    # ═══════════════════════════════════════════════════════
    # 🔧 TECHNICAL BASE CLASSES - الكلاسات التقنية للتجاهل
    # ═══════════════════════════════════════════════════════
    TECHNICAL_BASE_CLASSES = {
        'Object', 'Serializable', 'Cloneable', 'Comparable',
        'Iterable', 'AutoCloseable', 'Runnable', 'Callable',
        'Observer', 'Observable', 'EventListener'
    }

    def __init__(self):
        self.init()

    def init(self):
        try:
            if USE_LANGUAGES_LIB:
                logger.info("Using tree-sitter-languages for Java")
                self._java_language = get_language('java')
                logger.info("Java language loaded successfully via tree-sitter-languages")
            elif USE_DIRECT_IMPORT:
                logger.info("Using direct tree-sitter-java import")
                self._java_language = tree_sitter_java.language()
                logger.info("Java language loaded directly from tree_sitter_java.language()")
            else:
                raise ImportError("Neither tree-sitter-languages nor tree-sitter-java available")
            
            self._internal_java_parser = Parser()
            self._internal_java_parser.set_language(self._java_language)
            logger.info("Java Tree-sitter language loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Java Tree-sitter language: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            self._java_language = None
            self._internal_java_parser = None
    
    def analyze_code(self, code_content: str) -> Dict[str, Any]:
        """
        تحليل شامل للكود Java وإرجاع جميع النتائج في قاموس واحد
        يشبه طريقة عمل معالج Python
        
        Args:
            code_content: الكود المراد تحليله
            
        Returns:
            قاموس يحتوي على جميع نتائج التحليل:
            - ast_structure: البنية التركيبية للكود
            - extracted_features: الميزات المستخرجة (عدد الأسطر، الدوال، الكلاسات، إلخ)
            - dependencies: قائمة الاعتماديات
            - dependency_graph: رسم الاعتماديات
            - semantic_analysis_data: التحليل الدلالي (جودة الكود، المشاكل، التحذيرات)
            - class_diagram_data: بيانات مخطط الكلاسات (UML)
        """
        logger.info("Starting comprehensive Java code analysis...")
        
        # 1. Parse source code
        ast_data = self.parse_source_code(code_content)
        
        # 2. Extract features
        features = self.extract_features(ast_data)
        
        # 3. Extract dependencies
        dependencies = self.extract_dependencies(ast_data)
        
        # 4. Generate dependency graph
        dependency_graph = self.generate_dependency_graph_data(ast_data, features)
        
        # 5. Perform semantic analysis
        semantic_data = self.perform_semantic_analysis(ast_data, features)
        
        # 6. Generate class diagram (UML)
        class_diagram_data = self.generate_class_diagram_data(ast_data, features)
        
        # إرجاع جميع النتائج في قاموس واحد منظم
        return {
            "ast_structure": {
                "code_content": ast_data.get("code_content"),
                "error": ast_data.get("error")
                # ❌ لا نحفظ ast_tree و ast_structure - غير ضروري
            },
            "extracted_features": features,
            "dependencies": dependencies,
            "dependency_graph": dependency_graph,
            "semantic_analysis_data": semantic_data,
            "class_diagram_data": class_diagram_data
        }
        
    def parse_source_code(self, code_content: str) -> Dict[str, Any]:
        """تحليل الكود Java وإرجاع شجرة AST"""
        logger.info("Parsing Java source code...")
        if not self._java_language or not self._internal_java_parser:
            return {"ast_tree": None, "error": "Java parser not initialized (Tree-sitter language file missing)"}
        
        try:
            tree = self._internal_java_parser.parse(code_content.encode('utf8'))
            
            # ✅ لا نحفظ ast_structure - غير ضروري ويسبب بيانات ضخمة
            # كل التحليلات تتم من code_content مباشرة (مثل معالج Python)
            
            return {
                "ast_tree": None,  # للاستخدام الداخلي في المعالجة
                "ast_structure": None,  # ❌ لا نحفظه - يسبب ناتج ضخم
                "code_content": code_content
            }
        except Exception as e:
            logger.error(f"Failed to parse Java code: {e}")
            return {"ast_tree": None, "ast_structure": None, "error": str(e)}

    def extract_features(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """استخراج ميزات الكود مثل عدد الأسطر والدوال والكلاسات"""
        logger.info("Extracting Java features...")
        
        # ✅ الحل: نعمل re-parse للكود زي Python تماماً!
        code_content = ast_data.get("code_content", "")
        
        if not code_content:
            return {"lines_of_code": 0, "functions": 0}
        
        # ✅ إعادة parse من الكود مباشرة
        if not self._java_language or not self._internal_java_parser:
            return {"lines_of_code": 0, "functions": 0}
        
        try:
            tree = self._internal_java_parser.parse(code_content.encode('utf8'))
        except Exception as e:
            logger.error(f"Failed to parse code in extract_features: {e}")
            return {"lines_of_code": 0, "functions": 0}
        
        if not tree or not tree.root_node:
            return {"lines_of_code": 0, "functions": 0}
        
        loc = len(code_content.splitlines()) if code_content else 0
        num_methods = 0
        num_classes = 0
        num_constructors = 0
        num_interfaces = 0
        num_abstract_classes = 0
        function_details = []
       
        cursor = tree.walk()
        reached_root = False
        
        while not reached_root:
            node = cursor.node
            
            if node.type == 'method_declaration':
                num_methods += 1
                method_name = self._extract_method_name(node)
                function_details.append({
                    'name': method_name,
                    'line': node.start_point[0] + 1,
                    'is_method': True,
                    'is_async': False
                })
            
            elif node.type == 'constructor_declaration':
                num_constructors += 1
                constructor_name = "constructor"
                for child in node.children:
                    if child.type == 'identifier':
                        constructor_name = child.text.decode('utf-8')
                        break
                function_details.append({
                    'name': constructor_name,
                    'line': node.start_point[0] + 1,
                    'is_method': True,
                    'is_constructor': True,
                    'is_async': False
                })
            
            elif node.type == 'class_declaration':
                num_classes += 1
                # Check if abstract
                for child in node.children:
                    if child.type == 'modifiers':
                        for modifier in child.children:
                            if modifier.type == 'abstract':
                                num_abstract_classes += 1
                                break
            
            elif node.type == 'interface_declaration':
                num_interfaces += 1
            
            if cursor.goto_first_child():
                continue
            if cursor.goto_next_sibling():
                continue
            while cursor.goto_parent():
                if cursor.goto_next_sibling():
                    break
            else:
                reached_root = True
        
        total_functions = num_methods + num_constructors
        
        return {
            "lines_of_code": loc,
            "functions": total_functions,
            "standalone_functions": 0,
            "methods": num_methods,
            "constructors": num_constructors,
            "classes": num_classes,
            "interfaces": num_interfaces,
            "abstract_classes": num_abstract_classes,
            "function_details": function_details
        }

    def _extract_method_name(self, method_node) -> str:
        """استخراج اسم الطريقة من عقدة method_declaration"""
        for child in method_node.children:
            if child.type == 'identifier':
                return child.text.decode('utf-8')
        return "unknown_method"

    def extract_dependencies(self, ast_data: Dict[str, Any]) -> List[str]:
        """استخراج الاعتماديات (imports) من الكود"""
        logger.info("Extracting Java dependencies...")
        
        # ✅ إعادة parse من الكود
        code_content = ast_data.get("code_content", "")
        
        if not code_content or not self._java_language or not self._internal_java_parser:
            return []
        
        try:
            tree = self._internal_java_parser.parse(code_content.encode('utf8'))
        except Exception as e:
            logger.error(f"Failed to parse code in extract_dependencies: {e}")
            return []
        
        if not tree or not tree.root_node:
            return []
        
        dependencies = []
        cursor = tree.walk()
        reached_root = False
        
        while not reached_root:
            node = cursor.node
            
            if node.type == 'import_declaration':
                import_parts = []
                has_asterisk = False
                
                for child in node.children:
                    if child.type == 'identifier':
                        import_parts.append(child.text.decode('utf-8'))
                    elif child.type == 'scoped_identifier':
                        scoped_text = child.text.decode('utf-8')
                        scoped_parts = scoped_text.split('.')
                        import_parts.extend(scoped_parts)
                    elif child.type == 'asterisk':
                        has_asterisk = True
                
                if import_parts:
                    import_text = '.'.join(import_parts)
                    if has_asterisk:
                        import_text += ".*"
                    if import_text not in dependencies:
                        dependencies.append(import_text)
            
            if cursor.goto_first_child():
                continue
            if cursor.goto_next_sibling():
                continue
            while cursor.goto_parent():
                if cursor.goto_next_sibling():
                    break
            else:
                reached_root = True
        
        # Fallback: استخراج من النص مباشرة
        if not dependencies and code_content:
            lines = code_content.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('import '):
                    import_stmt = line[7:].strip()
                    if import_stmt.endswith(';'):
                        import_stmt = import_stmt[:-1]
                    if import_stmt and import_stmt not in dependencies:
                        dependencies.append(import_stmt)
        
        return dependencies

    def perform_semantic_analysis(self, ast_data: Dict[str, Any], features: Dict[str, Any]) -> Dict[str, Any]:
        """
        تحليل دلالي للكود وتقييم الجودة
        ✅ يعمل من code_content مباشرة (بدون الحاجة لـ ast_tree)
        """
        logger.info("Performing Java semantic analysis...")
        code_content = ast_data.get("code_content", "")
        
        if not code_content:
            return {
                "quality_score": 0,
                "issues": ["Cannot analyze empty code"],
                "warnings": [],
                "complexity": 0
            }
        
        # ✅ إعادة parse من الكود
        if not self._java_language or not self._internal_java_parser:
            return {
                "quality_score": 0,
                "issues": ["Parser not initialized"],
                "warnings": [],
                "complexity": 0
            }
        
        try:
            tree = self._internal_java_parser.parse(code_content.encode('utf8'))
        except Exception as e:
            logger.error(f"Failed to parse code in semantic_analysis: {e}")
            return {
                "quality_score": 0,
                "issues": [f"Parse error: {str(e)}"],
                "warnings": [],
                "complexity": 0
            }
        
        if not tree or not tree.root_node:
            return {
                "quality_score": 0,
                "issues": ["Invalid syntax tree"],
                "warnings": [],
                "complexity": 0
            }
        
        issues = []
        warnings = []
        
        # حساب التعقيد من features
        complexity = features.get("lines_of_code", 0) + \
                    features.get("functions", 0) * 2 + \
                    features.get("classes", 0) * 3
        
        # تقييم الجودة بناءً على معايير مختلفة
        quality_score = 100
        
        # 1. التحقق من طول الكود (الكود الطويل جداً يقلل من الجودة)
        loc = features.get("lines_of_code", 0)
        if loc > 500:
            quality_score -= 5
            warnings.append(f"⚠️ Large file size: {loc} lines (consider splitting)")
        elif loc > 1000:
            quality_score -= 10
            issues.append(f"❌ Very large file: {loc} lines (maintenance risk)")
        
        # 2. التحقق من عدد الكلاسات في ملف واحد
        num_classes = features.get("classes", 0)
        if num_classes > 5:
            quality_score -= 5
            warnings.append(f"⚠️ Multiple classes in one file: {num_classes} classes")
        
        # 3. التحقق من النسبة بين Methods والClasses
        num_methods = features.get("methods", 0)
        if num_classes > 0:
            methods_per_class = num_methods / num_classes
            if methods_per_class > 15:
                quality_score -= 5
                warnings.append(f"⚠️ High method density: {methods_per_class:.1f} methods per class")
        
        # 4. التحقق من وجود interfaces أو abstract classes (علامة على تصميم جيد)
        num_interfaces = features.get("interfaces", 0)
        num_abstract = features.get("abstract_classes", 0)
        if (num_interfaces + num_abstract) > 0 and num_classes > 3:
            quality_score += 5
        
        # الحد الأدنى للجودة هو 0
        quality_score = max(0, quality_score)
        
        return {
            "quality_score": quality_score,
            "issues": issues,
            "warnings": warnings,
            "complexity": complexity
        }

    # ═══════════════════════════════════════════════════════
    # 🔥 ENHANCED: Generate UML Diagram (مثل Python)
    # ═══════════════════════════════════════════════════════
    def generate_uml_diagram(self, ast_data: Dict[str, Any], features: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        توليد مخطط UML محسّن بنفس مستوى Python:
        ✅ 1. تصفية الأنواع البدائية
        ✅ 2. دمج العلاقات (الأولوية للأقوى)
        ✅ 3. معالجة الموروثات التقنية
        ✅ 4. تحديد الأنواع من Collections
        ✅ 5. إخفاء Constructors من Methods
        ✅ 6. دعم Abstract و Interfaces
        ✅ 7. علاقات ثنائية الاتجاه
        """
        logger.info("Generating enhanced Java UML diagram...")
        
        # ✅ إعادة parse من الكود
        code_content = ast_data.get("code_content", "")
        
        if not code_content or not self._java_language or not self._internal_java_parser:
            return {"classes": [], "relationships": []}
        
        try:
            tree = self._internal_java_parser.parse(code_content.encode('utf8'))
        except Exception as e:
            logger.error(f"Failed to parse code in generate_uml_diagram: {e}")
            return {"classes": [], "relationships": []}
        
        if not tree or not tree.root_node:
            return {"classes": [], "relationships": []}
        
        # ═════ المرحلة 1: جمع أسماء الكلاسات والواجهات ═════
        all_class_names = set()
        all_interface_names = set()
        
        cursor = tree.walk()
        reached_root = False
        
        while not reached_root:
            node = cursor.node
            
            if node.type == 'class_declaration':
                class_name = self._get_identifier(node)
                if class_name:
                    all_class_names.add(class_name)
            
            elif node.type == 'interface_declaration':
                interface_name = self._get_identifier(node)
                if interface_name:
                    all_interface_names.add(interface_name)
                    all_class_names.add(interface_name)  # للعلاقات
            
            if cursor.goto_first_child():
                continue
            if cursor.goto_next_sibling():
                continue
            while cursor.goto_parent():
                if cursor.goto_next_sibling():
                    break
            else:
                reached_root = True
        
        logger.info(f"[JavaProcessor] Found {len(all_class_names)} classes/interfaces: {all_class_names}")
        
        # ═════ المرحلة 2: استخراج التفاصيل والعلاقات ═════
        classes_list = []
        all_relationships = []
        
        cursor = tree.walk()
        reached_root = False
        
        while not reached_root:
            node = cursor.node
            
            if node.type == 'class_declaration':
                class_info = self._extract_class_info_enhanced(node, all_class_names)
                classes_list.append(class_info)
                all_relationships.extend(self._get_class_relationships(node, all_class_names))
            
            elif node.type == 'interface_declaration':
                interface_info = self._extract_interface_info_enhanced(node, all_class_names)
                classes_list.append(interface_info)
                all_relationships.extend(self._get_interface_relationships(node, all_class_names))
            
            if cursor.goto_first_child():
                continue
            if cursor.goto_next_sibling():
                continue
            while cursor.goto_parent():
                if cursor.goto_next_sibling():
                    break
            else:
                reached_root = True
        
        # ═════ المرحلة 3: توليد العلاقات من الـ Attributes (نهج موثوق) ═════
        # هذا النهج أكثر موثوقية من الـ AST مباشرة لأنه يستخدم البيانات المستخرجة مسبقاً
        for cls in classes_list:
            cls_name = cls.get('name', '')
            for attr in cls.get('attributes', []):
                attr_type = attr.get('type', '')
                attr_name = attr.get('name', '')
                if not attr_type:
                    continue

                # معالجة الأنواع الـ generic مثل List<Loan>, Set<Book>
                generic_match = re.search(r'<([A-Z][A-Za-z0-9]*)>', attr_type)
                if generic_match:
                    inner = generic_match.group(1)
                    if not self._is_primitive_type_java(inner):
                        all_relationships.append({
                            'from': cls_name, 'to': inner,
                            'type': 'aggregation',
                            'label': attr_name, 'multiplicity': '0..*',
                            'arrow': '→', 'directed': True
                        })
                # معالجة الأنواع البسيطة مثل BookService, Loan, Customer
                elif (attr_type and attr_type[0].isupper()
                        and not self._is_primitive_type_java(attr_type)):
                    all_relationships.append({
                        'from': cls_name, 'to': attr_type,
                        'type': 'association',
                        'label': attr_name, 'multiplicity': '1',
                        'arrow': '→', 'directed': True
                    })

        # ═════ المرحلة 4: دمج العلاقات ═════
        merged_relationships = self._merge_relationships_enhanced(all_relationships)
        
        # ═════ المرحلة 5: كشف العلاقات ثنائية الاتجاه ═════
        final_relationships = self._detect_bidirectionals(merged_relationships)
        
        # ═════ المرحلة 6: تنظيف الأتريبيوتس المكررة ═════
        cleaned_classes = self._clean_duplicate_attributes(classes_list, final_relationships)
        
        result = {"classes": cleaned_classes, "relationships": final_relationships}
        logger.info(f"[JavaProcessor] UML done — classes={len(cleaned_classes)}, relationships={len(final_relationships)}")
        return result

    # ═══════════════════════════════════════════════════════
    # 🔥 استخراج معلومات الكلاس (محسّن)
    # ═══════════════════════════════════════════════════════
    def _extract_class_info_enhanced(self, class_node, all_class_names) -> Dict[str, Any]:
        """استخراج معلومات الكلاس مع دعم Abstract"""
        class_name = self._get_identifier(class_node)
        attributes = []
        methods = []
        base_classes = []
        is_abstract = False
        
        # فحص Modifiers
        for child in class_node.children:
            if child.type == 'modifiers':
                for modifier in child.children:
                    if modifier.type == 'abstract':
                        is_abstract = True
        
        # استخراج الوراثة والواجهات
        for child in class_node.children:
            if child.type == 'superclass':
                base_class = self._extract_superclass(child)
                if base_class and base_class not in self.TECHNICAL_BASE_CLASSES:
                    base_classes.append(base_class)
            
            elif child.type == 'super_interfaces':
                interfaces = self._extract_super_interfaces(child)
                for interface in interfaces:
                    if interface not in self.TECHNICAL_BASE_CLASSES:
                        base_classes.append(interface)
        
        # استخراج Body
        for child in class_node.children:
            if child.type == 'class_body':
                for body_item in child.children:
                    # Fields
                    if body_item.type == 'field_declaration':
                        field_attrs = self._extract_field_attributes(body_item)
                        attributes.extend(field_attrs)
                    
                    # Methods (بدون Constructors)
                    elif body_item.type == 'method_declaration':
                        method_info = self._extract_method_info_enhanced(body_item)
                        if method_info:
                            methods.append(method_info)
        
        return {
            "name": class_name,
            "attributes": attributes,
            "methods": methods,
            "base_classes": base_classes,
            "is_abstract": is_abstract,
            "is_interface": False
        }

    # ═══════════════════════════════════════════════════════
    # 🔥 استخراج معلومات Interface
    # ═══════════════════════════════════════════════════════
    def _extract_interface_info_enhanced(self, interface_node, all_class_names) -> Dict[str, Any]:
        """استخراج معلومات Interface"""
        interface_name = self._get_identifier(interface_node)
        methods = []
        base_interfaces = []
        
        # استخراج extends
        for child in interface_node.children:
            if child.type == 'extends_interfaces':
                interfaces = self._extract_extends_interfaces(child)
                for intf in interfaces:
                    if intf not in self.TECHNICAL_BASE_CLASSES:
                        base_interfaces.append(intf)
        
        # استخراج Methods
        for child in interface_node.children:
            if child.type == 'interface_body':
                for body_item in child.children:
                    if body_item.type == 'method_declaration':
                        method_info = self._extract_method_info_enhanced(body_item)
                        if method_info:
                            # كل methods في interface هي abstract
                            method_info['is_abstract'] = True
                            methods.append(method_info)
        
        return {
            "name": interface_name,
            "attributes": [],
            "methods": methods,
            "base_classes": base_interfaces,
            "is_abstract": False,
            "is_interface": True
        }

    # ═══════════════════════════════════════════════════════
    # 🔥 استخراج علاقات الكلاس
    # ═══════════════════════════════════════════════════════
    def _get_class_relationships(self, class_node, all_class_names) -> List[Dict]:
        """استخراج جميع علاقات الكلاس"""
        class_name = self._get_identifier(class_node)
        relationships = []
        
        # 1. Inheritance
        for child in class_node.children:
            if child.type == 'superclass':
                base_class = self._extract_superclass(child)
                if base_class and base_class not in self.TECHNICAL_BASE_CLASSES:
                    relationships.append({
                        "from": class_name,
                        "to": base_class,
                        "type": "inheritance",
                        "label": "extends",
                        "arrow": "→",
                        "directed": True
                    })
        
        # 2. Realization (implements)
        for child in class_node.children:
            if child.type == 'super_interfaces':
                interfaces = self._extract_super_interfaces(child)
                for interface in interfaces:
                    if interface not in self.TECHNICAL_BASE_CLASSES:
                        relationships.append({
                            "from": class_name,
                            "to": interface,
                            "type": "realization",
                            "label": "implements",
                            "arrow": "→",
                            "dashed": True,
                            "directed": True
                        })
        
        # 3. Composition, Aggregation, Association
        composition_targets = set()
        
        for child in class_node.children:
            if child.type == 'class_body':
                for body_item in child.children:
                    # من Fields
                    if body_item.type == 'field_declaration':
                        field_rels = self._extract_field_relationships(body_item, all_class_names)
                        relationships.extend(field_rels)
                    
                    # من Constructors
                    elif body_item.type == 'constructor_declaration':
                        constructor_rels = self._extract_constructor_relationships(
                            body_item, all_class_names
                        )
                        for rel in constructor_rels:
                            composition_targets.add(rel['to'])
                        relationships.extend(constructor_rels)
        
        # إضافة from للعلاقات
        for rel in relationships:
            if 'from' not in rel:
                rel['from'] = class_name
        
        return relationships

    # ═══════════════════════════════════════════════════════
    # 🔥 استخراج علاقات Interface
    # ═══════════════════════════════════════════════════════
    def _get_interface_relationships(self, interface_node, all_class_names) -> List[Dict]:
        """استخراج علاقات Interface (extends فقط)"""
        interface_name = self._get_identifier(interface_node)
        relationships = []
        
        for child in interface_node.children:
            if child.type == 'extends_interfaces':
                interfaces = self._extract_extends_interfaces(child)
                for intf in interfaces:
                    if intf not in self.TECHNICAL_BASE_CLASSES:
                        relationships.append({
                            "from": interface_name,
                            "to": intf,
                            "type": "inheritance",
                            "label": "extends",
                            "arrow": "→",
                            "directed": True
                        })
        
        return relationships

    # ═══════════════════════════════════════════════════════
    # 🔥 استخراج Field Attributes
    # ═══════════════════════════════════════════════════════
    def _extract_field_attributes(self, field_node) -> List[Dict]:
        """استخراج attributes من field"""
        attributes = []
        field_type = ""
        visibility = "private"
        
        # استخراج visibility و type
        for child in field_node.children:
            if child.type == 'modifiers':
                for modifier in child.children:
                    if modifier.type in ['public', 'private', 'protected']:
                        visibility = modifier.text.decode('utf-8')
            
            elif child.type == 'type_identifier':
                field_type = child.text.decode('utf-8')
            
            elif child.type == 'generic_type':
                field_type = child.text.decode('utf-8')
            
            elif child.type == 'integral_type':
                field_type = child.text.decode('utf-8')
            
            elif child.type == 'floating_point_type':
                field_type = child.text.decode('utf-8')
            
            elif child.type == 'boolean_type':
                field_type = "boolean"
        
        # استخراج names
        for child in field_node.children:
            if child.type == 'variable_declarator':
                field_name = self._get_identifier(child)
                if field_name:
                    attributes.append({
                        "name": field_name,
                        "type": field_type or "Object",
                        "visibility": visibility
                    })
        
        return attributes

    # ═══════════════════════════════════════════════════════
    # 🔥 استخراج Field Relationships
    # ═══════════════════════════════════════════════════════
    def _extract_field_relationships(self, field_node, all_class_names) -> List[Dict]:
        """استخراج علاقات من Fields"""
        relationships = []
        field_type = ""
        field_name = ""
        is_collection = False
        inner_type = None
        
        # استخراج Type
        for child in field_node.children:
            if child.type == 'type_identifier':
                field_type = child.text.decode('utf-8')
            
            elif child.type == 'generic_type':
                # معالجة List<Employee>, Set<Car>, etc.
                base_type, inner = self._parse_generic_type(child)
                field_type = base_type
                inner_type = inner
                is_collection = True
        
        # استخراج Name
        for child in field_node.children:
            if child.type == 'variable_declarator':
                field_name = self._get_identifier(child)
        
        if not field_name:
            return relationships
        
        # تحديد نوع العلاقة
        if is_collection and inner_type:
            # Aggregation
            if not self._is_primitive_type_java(inner_type) and inner_type in all_class_names:
                relationships.append({
                    "to": inner_type,
                    "type": "aggregation",
                    "label": field_name,
                    "multiplicity": "0..*",
                    "arrow": "→",
                    "directed": True
                })
        
        elif field_type:
            # Association
            if not self._is_primitive_type_java(field_type) and field_type in all_class_names:
                relationships.append({
                    "to": field_type,
                    "type": "association",
                    "label": field_name,
                    "multiplicity": "1",
                    "arrow": "→",
                    "directed": True
                })
        
        return relationships

    # ═══════════════════════════════════════════════════════
    # 🔥 استخراج Constructor Relationships
    # ═══════════════════════════════════════════════════════
    def _extract_constructor_relationships(self, constructor_node, all_class_names) -> List[Dict]:
        """استخراج علاقات Composition من Constructor"""
        relationships = []
        
        # البحث عن constructor body
        for child in constructor_node.children:
            if child.type == 'constructor_body':
                for stmt in child.children:
                    if stmt.type == 'expression_statement':
                        comp_rel = self._extract_composition_from_statement(stmt, all_class_names)
                        if comp_rel:
                            relationships.append(comp_rel)
        
        return relationships

    def _extract_composition_from_statement(self, stmt_node, all_class_names) -> Dict | None:
        """استخراج Composition من statement (this.x = new Y())"""
        field_name = None
        target_class = None
        
        for child in stmt_node.children:
            if child.type == 'assignment_expression':
                # Left side: this.fieldName
                for assign_child in child.children:
                    if assign_child.type == 'field_access':
                        field_name = self._extract_field_access_name(assign_child)
                
                # Right side: new ClassName()
                for assign_child in child.children:
                    if assign_child.type == 'object_creation_expression':
                        target_class = self._extract_created_class(assign_child)
        
        if field_name and target_class:
            if not self._is_primitive_type_java(target_class) and target_class in all_class_names:
                return {
                    "to": target_class,
                    "type": "composition",
                    "label": field_name,
                    "multiplicity": "1",
                    "arrow": "→",
                    "directed": True
                }
        
        return None

    # ═══════════════════════════════════════════════════════
    # 🔥 استخراج Method Info (محسّن)
    # ═══════════════════════════════════════════════════════
    def _extract_method_info_enhanced(self, method_node) -> Dict | None:
        """استخراج معلومات Method بتفاصيل كاملة"""
        method_name = ""
        visibility = "public"
        return_type = "void"
        parameters = []
        is_abstract = False
        
        # Modifiers
        for child in method_node.children:
            if child.type == 'modifiers':
                for modifier in child.children:
                    if modifier.type in ['public', 'private', 'protected']:
                        visibility = modifier.text.decode('utf-8')
                    elif modifier.type == 'abstract':
                        is_abstract = True
        
        # Return type
        for child in method_node.children:
            if child.type == 'type_identifier':
                return_type = child.text.decode('utf-8')
            elif child.type == 'void_type':
                return_type = "void"
            elif child.type == 'generic_type':
                return_type = child.text.decode('utf-8')
            elif child.type == 'integral_type':
                return_type = child.text.decode('utf-8')
            elif child.type == 'floating_point_type':
                return_type = child.text.decode('utf-8')
            elif child.type == 'boolean_type':
                return_type = "boolean"
        
        # Name
        method_name = self._get_identifier(method_node)
        
        # Parameters
        for child in method_node.children:
            if child.type == 'formal_parameters':
                parameters = self._extract_method_parameters(child)
        
        if not method_name:
            return None
        
        # بناء Signature
        param_strs = []
        for param in parameters:
            param_strs.append(f"{param['name']}: {param['type']}")
        
        signature = f"{method_name}({', '.join(param_strs)}): {return_type}"
        
        # إضافة visibility symbol
        vis_symbol = "+"
        if visibility == "private":
            vis_symbol = "-"
        elif visibility == "protected":
            vis_symbol = "#"
        
        return {
            "name": method_name,
            "signature": f"{vis_symbol} {signature}",
            "is_abstract": is_abstract,
            "visibility": visibility,
            "is_constructor": False
        }

    def _extract_method_parameters(self, formal_params_node) -> List[Dict]:
        """استخراج معاملات Method"""
        parameters = []
        
        for child in formal_params_node.children:
            if child.type == 'formal_parameter':
                param_name = ""
                param_type = "Object"
                
                for param_child in child.children:
                    if param_child.type == 'type_identifier':
                        param_type = param_child.text.decode('utf-8')
                    elif param_child.type == 'generic_type':
                        param_type = param_child.text.decode('utf-8')
                    elif param_child.type == 'integral_type':
                        param_type = param_child.text.decode('utf-8')
                    elif param_child.type == 'floating_point_type':
                        param_type = param_child.text.decode('utf-8')
                    elif param_child.type == 'boolean_type':
                        param_type = "boolean"
                    elif param_child.type == 'identifier':
                        param_name = param_child.text.decode('utf-8')
                
                if param_name:
                    parameters.append({
                        "name": param_name,
                        "type": param_type
                    })
        
        return parameters

    # ═══════════════════════════════════════════════════════
    # 🔥 دمج العلاقات (مثل Python)
    # ═══════════════════════════════════════════════════════
    def _merge_relationships_enhanced(self, relationships: List[Dict]) -> List[Dict]:
        """
        دمج العلاقات المكررة - الأولوية للأقوى
        
        ترتيب الأولوية:
        1. composition (الأقوى)
        2. aggregation
        3. inheritance
        4. realization
        5. association
        6. dependency (الأضعف)
        """
        priority_order = {
            "composition": 1,
            "aggregation": 2,
            "inheritance": 3,
            "realization": 4,
            "association": 5,
            "dependency": 6
        }
        
        merged = {}
        
        for rel in relationships:
            key = (rel["from"], rel["to"])
            
            if key not in merged:
                merged[key] = rel
            else:
                current_priority = priority_order.get(merged[key]["type"], 999)
                new_priority = priority_order.get(rel["type"], 999)
                
                # نحتفظ بالعلاقة الأقوى
                if new_priority < current_priority:
                    logger.debug(f"[JavaProcessor] Merge: {rel['from']}→{rel['to']}: {merged[key]['type']} → {rel['type']}")
                    merged[key] = rel
        
        return list(merged.values())

    # ═══════════════════════════════════════════════════════
    # 🔥 كشف العلاقات ثنائية الاتجاه (مثل Python)
    # ═══════════════════════════════════════════════════════
    def _detect_bidirectionals(self, relationships: List[Dict]) -> List[Dict]:
        """كشف وتمييز العلاقات ثنائية الاتجاه"""
        enhanced = []
        seen = {}
        
        for rel in relationships:
            key = (rel["from"], rel["to"])
            rev_key = (rel["to"], rel["from"])
            
            if rev_key in seen:
                # علاقة ثنائية الاتجاه
                seen[rev_key]["arrow"] = "—"
                seen[rev_key]["directed"] = False
                seen[rev_key]["bidirectional"] = True
                
                rel["arrow"] = "—"
                rel["directed"] = False
                rel["bidirectional"] = True
                
                logger.debug(f"[JavaProcessor] Bidirectional: {rel['from']} ↔ {rel['to']}")
            
            seen[key] = rel
            enhanced.append(rel)
        
        return enhanced

    # ═══════════════════════════════════════════════════════
    # 🔥 تنظيف Attributes المكررة (مثل Python)
    # ═══════════════════════════════════════════════════════
    def _clean_duplicate_attributes(self, classes: List[Dict], relationships: List[Dict]) -> List[Dict]:
        """
        إزالة Attributes التي لها علاقات
        (لتجنب التكرار بين attributes و relationships)
        """
        cleaned_classes = []
        
        for class_data in classes:
            class_name = class_data.get('name')
            
            # جمع أسماء المتغيرات التي لها علاقات
            relationship_attributes = set()
            for rel in relationships:
                if rel.get('from') == class_name:
                    label = rel.get('label')
                    if label:
                        relationship_attributes.add(label)
            
            # تصفية الأتريبيوتس
            original_attributes = class_data.get('attributes', [])
            filtered_attributes = []
            
            for attr in original_attributes:
                attr_name = attr.get('name')
                
                if attr_name not in relationship_attributes:
                    filtered_attributes.append(attr)
                else:
                    logger.debug(f"[JavaProcessor] Removed duplicate attr '{attr_name}' from '{class_name}'")
            
            cleaned_class = class_data.copy()
            cleaned_class['attributes'] = filtered_attributes
            cleaned_classes.append(cleaned_class)
        
        return cleaned_classes

    # ═══════════════════════════════════════════════════════
    # 🔧 Helper Methods
    # ═══════════════════════════════════════════════════════
    def _is_primitive_type_java(self, type_name: str) -> bool:
        """فحص إذا كان النوع بدائي"""
        if not type_name:
            return True
        
        base_type = type_name.split('<')[0].strip()
        return base_type in self.PRIMITIVE_TYPES

    def _get_identifier(self, node) -> str:
        """استخراج اسم Identifier من Node"""
        for child in node.children:
            if child.type == 'identifier':
                return child.text.decode('utf-8')
        return ""

    def _extract_superclass(self, superclass_node) -> str:
        """استخراج اسم الكلاس الأب"""
        for child in superclass_node.children:
            if child.type == 'type_identifier':
                return child.text.decode('utf-8')
        return ""

    def _extract_super_interfaces(self, super_interfaces_node) -> List[str]:
        """استخراج أسماء الواجهات"""
        interfaces = []
        for child in super_interfaces_node.children:
            if child.type == 'type_list':
                for type_node in child.children:
                    if type_node.type == 'type_identifier':
                        interfaces.append(type_node.text.decode('utf-8'))
        return interfaces

    def _extract_extends_interfaces(self, extends_node) -> List[str]:
        """استخراج extends للـ interface"""
        interfaces = []
        for child in extends_node.children:
            if child.type == 'type_list':
                for type_node in child.children:
                    if type_node.type == 'type_identifier':
                        interfaces.append(type_node.text.decode('utf-8'))
        return interfaces

    def _parse_generic_type(self, generic_node) -> tuple:
        """
        تحليل Generic Type مثل List<Employee>
        يستخدم النص المباشر كـ fallback إذا لم يجد type_identifier داخل type_arguments
        هذا ضروري لأن بعض إصدارات tree-sitter-java لا تعرض type_identifier مباشرة
        """
        base_type = ""
        inner_type = None
        
        for child in generic_node.children:
            if child.type == 'type_identifier':
                base_type = child.text.decode('utf-8')
            elif child.type == 'type_arguments':
                # محاولة 1: البحث عن type_identifier مباشرة
                for type_arg in child.children:
                    if type_arg.type == 'type_identifier':
                        inner_type = type_arg.text.decode('utf-8')
                        break
                
                # محاولة 2: Fallback - قراءة النص مباشرة من <Type> أو <Type, Type>
                if not inner_type:
                    raw = child.text.decode('utf-8')  # e.g. "<Loan>" or "<K, V>"
                    raw = raw.strip('<>').strip()
                    # خذ أول نوع فقط (قبل أي فاصلة)
                    first_type = raw.split(',')[0].strip()
                    # تنظيف أي wildcards أو extends
                    first_type = first_type.replace('? extends ', '').replace('? super ', '').strip()
                    if first_type and first_type[0].isupper():
                        inner_type = first_type
        
        # Fallback نهائي: قراءة النص الكامل للـ node مثل "List<Loan>"
        if not inner_type and not base_type:
            full_text = generic_node.text.decode('utf-8') if generic_node.text else ""
            if '<' in full_text and '>' in full_text:
                base_type = full_text[:full_text.index('<')].strip()
                inner_raw = full_text[full_text.index('<')+1:full_text.rindex('>')].strip()
                first_type = inner_raw.split(',')[0].strip()
                if first_type and first_type[0].isupper():
                    inner_type = first_type
        
        return base_type, inner_type

    def _extract_field_access_name(self, field_access_node) -> str:
        """استخراج اسم Field من field_access (this.fieldName)"""
        for child in field_access_node.children:
            if child.type == 'identifier':
                return child.text.decode('utf-8')
        return ""

    def _extract_created_class(self, creation_node) -> str:
        """استخراج اسم الكلاس من object_creation_expression"""
        for child in creation_node.children:
            if child.type == 'type_identifier':
                return child.text.decode('utf-8')
        return ""

    # ═══════════════════════════════════════════════════════
    # 🔧 Class Diagram Generation (Alias for UML)
    # ═══════════════════════════════════════════════════════
    def generate_class_diagram_data(self, ast_data: Dict[str, Any], features: Dict[str, Any]) -> Dict[str, Any]:
        """
        توليد بيانات Class Diagram (نفس UML)
        هذه الطريقة مطلوبة من الـ interface
        """
        logger.info("Generating Java class diagram data...")
        return self.generate_uml_diagram(ast_data, features)
    
    # ═══════════════════════════════════════════════════════
    # 🔧 Dependency Graph Generation
    # ═══════════════════════════════════════════════════════
    def generate_dependency_graph_data(self, ast_data: Dict[str, Any], features: Dict[str, Any]) -> Dict[str, Any]:
        """
        توليد بيانات رسم الاعتماديات
        ✅ يتتبع الاستخدام الفعلي للـ dependencies داخل كل class
        """
        logger.info("Generating Java dependency graph data...")
        
        # ✅ إعادة parse من الكود
        code_content = ast_data.get("code_content", "")
        
        if not code_content or not self._java_language or not self._internal_java_parser:
            return {"nodes": [], "edges": []}
        
        try:
            tree = self._internal_java_parser.parse(code_content.encode('utf8'))
        except Exception as e:
            logger.error(f"Failed to parse code in generate_dependency_graph_data: {e}")
            return {"nodes": [], "edges": []}
        
        if not tree or not tree.root_node:
            return {"nodes": [], "edges": []}
        
        nodes = []
        edges = []
        classes_found = set()
        imports_found = set()
        class_dependencies = {}  # ✅ تتبع dependencies لكل class
        
        # جمع الكلاسات وتتبع استخدامهم للـ types
        cursor = tree.walk()
        reached_root = False
        current_class = None
        
        while not reached_root:
            node = cursor.node
            
            # تتبع الكلاس الحالي
            if node.type in ['class_declaration', 'interface_declaration']:
                class_name = self._get_identifier(node)
                if class_name and class_name not in classes_found:
                    classes_found.add(class_name)
                    current_class = class_name
                    class_dependencies[class_name] = set()
                    nodes.append({
                        "id": class_name,
                        "label": class_name,
                        "type": "class",
                        "local": True
                    })
            
            # تتبع استخدام الـ types داخل كل class
            if current_class and node.type == 'type_identifier':
                type_name = node.text.decode('utf-8') if node.text else ""
                # تحقق إذا كان Type من الـ imports
                for dep in self.extract_dependencies(ast_data):
                    # مثلاً: إذا استخدمنا ArrayList وعندنا java.util.ArrayList
                    if dep.endswith('.' + type_name) or dep == type_name:
                        class_dependencies[current_class].add(dep)
            
            # تتبع object_creation (new ArrayList())
            if current_class and node.type == 'object_creation_expression':
                for child in node.children:
                    if child.type == 'type_identifier':
                        type_name = child.text.decode('utf-8') if child.text else ""
                        for dep in self.extract_dependencies(ast_data):
                            if dep.endswith('.' + type_name) or dep == type_name:
                                class_dependencies[current_class].add(dep)
            
            if cursor.goto_first_child():
                continue
            if cursor.goto_next_sibling():
                continue
            
            # عند الخروج من class، نصفّر current_class
            while cursor.goto_parent():
                if cursor.node.type in ['class_declaration', 'interface_declaration']:
                    current_class = None
                if cursor.goto_next_sibling():
                    break
            else:
                reached_root = True
        
        # جمع الاعتماديات
        dependencies = self.extract_dependencies(ast_data)
        
        for dep in dependencies:
            if dep not in imports_found:
                imports_found.add(dep)
                nodes.append({
                    "id": dep,
                    "label": dep,
                    "type": "module",
                    "local": False
                })
        
        # ✅ إنشاء Edges بناءً على الاستخدام الفعلي فقط
        for class_name, used_deps in class_dependencies.items():
            for dep in used_deps:
                edges.append({
                    "source": class_name,
                    "target": dep,
                    "type": "dependency"
                })
        
        # ✅ إذا لم نجد أي استخدام فعلي، نضيف edge واحد فقط للـ imports المستخدمة
        if not edges and dependencies:
            # على الأقل نربط الـ imports بكلاس واحد (مثلاً أول class)
            if classes_found:
                first_class = list(classes_found)[0]
                for dep in dependencies:
                    edges.append({
                        "source": first_class,
                        "target": dep,
                        "type": "dependency"
                    })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "statistics": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "local_classes": len([n for n in nodes if n.get('local', False)]),
                "external_modules": len([n for n in nodes if not n.get('local', True)])
            }
        }