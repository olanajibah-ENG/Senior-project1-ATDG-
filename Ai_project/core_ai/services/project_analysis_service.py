import logging
from datetime import datetime
from bson import ObjectId
from django.conf import settings
from core_ai.mongo_utils import get_mongo_db
from core_ai.services.dependency_graph_builder import DependencyGraphBuilder
from core_ai.services.context_builder import CrossFileContextBuilder

logger = logging.getLogger(__name__)


class ProjectAnalysisService:

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.db         = get_mongo_db()

    # ① جيبي الملفات المكتملة من MongoDB
    def get_project_files(self) -> list:
        completed = list(
            self.db[settings.CODE_FILES_COLLECTION].find({
                "source_project_id": self.project_id,
                "analysis_status":   "COMPLETED"
            })
        )

        project_files = []
        for cf in completed:
            result = self.db[settings.ANALYSIS_RESULTS_COLLECTION].find_one({
                "code_file_id": cf['_id'],
                "status":       "COMPLETED"
            })
            if result:
                project_files.append({
                    "file_id":            str(cf['_id']),
                    "filename":           cf['filename'],
                    "filepath":           cf.get('filepath', cf['filename']),
                    "file_type":          cf.get('file_type', 'python'),
                    "dependencies":       result.get('dependencies', []),
                    "class_diagram_data": result.get('class_diagram_data', {}),
                    "extracted_features": result.get('extracted_features', {}),
                    "semantic_analysis_data": result.get('semantic_analysis_data', {}),
                    "ast_structure":      result.get('ast_structure', {}),
                    "analysis_id":        str(result['_id'])
                })
        return project_files

    # ② بناء الـ Graph
    def build_graph(self, files: list) -> dict:
        return DependencyGraphBuilder().process_and_sort(files)

    # ③ بناء الـ Contexts
    def build_contexts(self, files: list, ordered: list) -> dict:
        # ابني map: filename → file_data
        file_map = {f['filename']: f for f in files}
        contexts = {}

        for filename in ordered:
            if filename not in file_map:
                continue
            current = file_map[filename]
            raw_deps = current.get('dependencies', [])

            context_blocks = []
            for dep in raw_deps:
                matched = None
                
                # 1. المطابقة المباشرة
                if dep in file_map:
                    matched = dep
                else:
                    # 2. المطابقة مع امتدادات الملفات
                    for ext in ['.py', '.java', '.js', '.ts']:
                        if dep + ext in file_map:
                            matched = dep + ext
                            break
                            
                # 3. المطابقة بجزء الاسم الأخير (مثال: core.product -> product)
                if not matched:
                    last_part = dep.split('.')[-1]
                    for ext in ['.py', '.java', '.js', '.ts', '']:
                        if last_part + ext in file_map:
                            matched = last_part + ext
                            break
                            
                # 4. مطابقة جزئية Endswith
                if not matched:
                    for f_name in file_map.keys():
                        base = f_name.split('/')[-1] if '/' in f_name else f_name
                        if base.startswith(dep.split('.')[-1]) or f_name.endswith(dep):
                            matched = f_name
                            break

                if matched:
                    diagram = file_map[matched].get('class_diagram_data', {})
                    sigs = self._diagram_to_signatures(diagram)
                    if sigs:
                        # تنسيق واضح وصريح كما طُلب
                        context_blocks.append(f"--- Context from: {matched} ---\n{sigs}")

            # إذا وجدنا أي signatures، نضيفها للملف
            if context_blocks:
                contexts[filename] = "\n\n".join(context_blocks)

        return contexts

    def _diagram_to_signatures(self, diagram: dict) -> str:
        """تحويل class_diagram_data إلى نص signatures."""
        if not diagram or not isinstance(diagram, dict):
            return ""
        lines = []
        for cls in diagram.get('classes', []):
            lines.append(f"class {cls.get('name', '')}:")
            for m in cls.get('methods', []):
                sig = m.get('signature', '')
                if sig:
                    lines.append(f"  {sig}")
        return "\n".join(lines)

    def _build_project_summary(self, graph_data: dict, contexts: dict) -> str:
        """إنشاء ملخص مبدئي من graph + contexts لعرض سريع في الـ UI أو الـ LLM."""
        ordered = graph_data.get('ordered', [])
        graph = graph_data.get('graph', {})

        summary = [f"Project analysis summary for {self.project_id}"]
        summary.append(f"Files order: {len(ordered)} files")
        summary.append(f"Dependencies: {sum(len(v) for v in graph.values())} edges")

        if contexts:
            summary.append(f"Built context for {len(contexts)} files")
        else:
            summary.append("No contexts built (missing class diagram data or dependencies)")

        return "\n".join(summary)

    def aggregate_project_data(self, files: list, graph_data: dict) -> dict:
        total_loc = 0
        total_classes = 0
        total_functions = 0
        total_async_functions = 0
        total_complexity = 0
        all_warnings = []
        all_issues = []
        
        unified_classes = []
        unified_relationships = []
        seen_classes = set()
        
        all_potential_relationships = []
        
        all_ast_bodies = []
        all_code_content = []
        all_original_code = []
        all_normalization_fixes = []
        was_auto_fixed = False

        for f in files:
            # Aggregate features
            features = f.get('extracted_features', {})
            total_loc += features.get('lines_of_code', 0)
            total_classes += features.get('num_classes', 0)
            total_functions += features.get('num_functions', 0)
            total_async_functions += features.get('num_async_functions', 0)
            total_complexity += features.get('complexity_score', 0)

            # Aggregate semantic analysis
            semantic = f.get('semantic_analysis_data', {})
            if isinstance(semantic, dict):
                for w in semantic.get('warnings', []):
                    all_warnings.append(f"[{f['filename']}] {w}")
                for i in semantic.get('issues', []):
                    all_issues.append(f"[{f['filename']}] {i}")
            
            # Aggregate class diagram
            diagram = f.get('class_diagram_data', {})
            if isinstance(diagram, dict):
                for cls in diagram.get('classes', []):
                    cls_name = cls.get('name', '')
                    if cls_name and cls_name not in seen_classes:
                        cls_copy = dict(cls)
                        if 'filepath' not in cls_copy:
                            cls_copy['filepath'] = f['filepath']
                        unified_classes.append(cls_copy)
                        seen_classes.add(cls_name)

                for rel in diagram.get('relationships', []):
                    all_potential_relationships.append(rel)

            # Aggregate AST structure
            ast = f.get('ast_structure', {})
            if isinstance(ast, dict):
                tree = ast.get('ast_tree', {})
                if isinstance(tree, dict) and 'body' in tree:
                    all_ast_bodies.extend(tree['body'])
                
                content = ast.get('code_content', '')
                if content:
                    all_code_content.append(f"# --- {f['filename']} ---\n{content}")
                
                original = ast.get('original_code', '')
                if original:
                    all_original_code.append(f"# --- {f['filename']} ---\n{original}")
                
                fixes = ast.get('normalization_fixes', [])
                if fixes:
                    all_normalization_fixes.extend([f"[{f['filename']}] {fix}" for fix in fixes])
                
                if ast.get('was_auto_fixed'):
                    was_auto_fixed = True

        # Filter relationships to keep only those within seen_classes or standard types
        for rel in all_potential_relationships:
            target = rel.get('to', '')
            if target in seen_classes or target in ['ABC', 'object', 'Exception']:
                if rel not in unified_relationships:
                    unified_relationships.append(rel)

        # Calculate average quality score (simplistic aggregation)
        avg_quality = 100.0
        if all_issues:
            avg_quality -= len(all_issues) * 5
        if all_warnings:
            avg_quality -= len(all_warnings) * 1
        avg_quality = max(0.0, min(100.0, avg_quality))

        # Reformat dependency graph from graph_data['graph'] which is {filename: [deps]}
        # to {nodes: [...], edges: [...]} so it matches single file output
        dep_nodes = []
        dep_edges = []
        for f in files:
            dep_nodes.append({
                "id": f['filename'],
                "label": f['filename'],
                "type": "module"
            })
        
        graph_dict = graph_data.get('graph', {})
        for node, edges in graph_dict.items():
            for target in edges:
                dep_edges.append({
                    "from": node,
                    "to": target,
                    "label": "imports",
                    "arrow": "→"
                })

        project_ast = {
            "ast_tree": {
                "body": all_ast_bodies,
                "type_ignores": [],
                "node_type": "Module"
            },
            "code_content": "\n".join(all_code_content),
            "original_code": "\n".join(all_original_code),
            "normalization_fixes": all_normalization_fixes,
            "was_auto_fixed": was_auto_fixed
        }

        return {
            "extracted_features": {
                "lines_of_code": total_loc,
                "num_classes": total_classes,
                "num_functions": total_functions,
                "num_async_functions": total_async_functions,
                "complexity_score": total_complexity,
                "was_code_modified": False
            },
            "class_diagram_data": {
                "classes": unified_classes,
                "relationships": unified_relationships
            },
            "semantic_analysis_data": {
                "quality_score": avg_quality,
                "issues": all_issues,
                "warnings": all_warnings,
                "complexity": total_complexity
            },
            "dependency_graph": {
                "nodes": dep_nodes,
                "edges": dep_edges
            },
            "ast_structure": project_ast
        }

    # ④ احفظي النتيجة
    def save_result(self, project_files: list, graph_data: dict, contexts: dict, analysis_ids: list, existing_record_id: str = None) -> str:
        project_summary = self._build_project_summary(graph_data, contexts)
        aggregated_data = self.aggregate_project_data(project_files, graph_data)

        doc = {
            "project_id":       self.project_id,
            "status":           "COMPLETED",
            "message":          "Analysis completed successfully",
            
            "extracted_features":       aggregated_data['extracted_features'],
            "class_diagram_data":       aggregated_data['class_diagram_data'],
            "semantic_analysis_data":   aggregated_data['semantic_analysis_data'],
            "dependency_graph":         aggregated_data['dependency_graph'],
            "ast_structure":            aggregated_data['ast_structure'],
            
            "dependency_order": graph_data['ordered'],
            "contexts":         contexts,
            "analysis_ids":     analysis_ids,
            "project_summary":  project_summary,
            "completed_at":     datetime.utcnow(),
            "created_at":       datetime.utcnow(),
            "updated_at":       datetime.utcnow()
        }

        if existing_record_id:
            try:
                oid = ObjectId(existing_record_id)
                self.db['project_analysis_results'].update_one(
                    {"_id": oid},
                    {"$set": doc}
                )
                return existing_record_id
            except Exception as e:
                logger.error(f"[PROJECT-ANALYSIS-SERVICE] Failed to update existing result: {e}")

        result = self.db['project_analysis_results'].insert_one(doc)
        return str(result.inserted_id)

    def set_analysis_status(self, record_id: str, status: str, message: str = None):
        try:
            oid = ObjectId(record_id)
            update = {"status": status, "updated_at": datetime.utcnow()}
            if message is not None:
                update["message"] = message
            self.db['project_analysis_results'].update_one({"_id": oid}, {"$set": update})
        except Exception as e:
            logger.error(f"[PROJECT-ANALYSIS-SERVICE] set_analysis_status failed: {e}")