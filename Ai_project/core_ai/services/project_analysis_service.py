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
                    "analysis_id":        str(result['_id'])
                })
        return project_files

    # ② بناء الـ Graph
    def build_graph(self, files: list) -> dict:
        return DependencyGraphBuilder().process_and_sort(files)

    # ③ بناء الـ Contexts
    def build_contexts(self, files: list, ordered: list) -> dict:
        # ابني map: filename → class_diagram_data
        file_map = {f['filename']: f for f in files}
        contexts = {}

        for filename in ordered:
            if filename not in file_map:
                continue
            current = file_map[filename]
            raw_deps = current.get('dependencies', [])

            # جيبي محتوى التبعيات من class_diagram_data
            dep_content = {}
            for dep in raw_deps:
                # جرب المطابقة المباشرة أو مع امتداد
                matched = None
                if dep in file_map:
                    matched = dep
                else:
                    for ext in ['.py', '.java', '.js', '.ts']:
                        if dep + ext in file_map:
                            matched = dep + ext
                            break
                if matched:
                    diagram = file_map[matched].get('class_diagram_data', {})
                    # حوّل class_diagram_data لنص signatures
                    sigs = self._diagram_to_signatures(diagram)
                    if sigs:
                        dep_content[matched] = sigs

            if dep_content:
                builder = CrossFileContextBuilder()
                ctx = builder.build_llm_context(dep_content)
                if ctx:
                    contexts[filename] = ctx

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

    # ④ احفظي النتيجة
    def save_result(self, graph_data: dict, contexts: dict, analysis_ids: list, existing_record_id: str = None) -> str:
        project_summary = self._build_project_summary(graph_data, contexts)

        doc = {
            "project_id":       self.project_id,
            "dependency_order": graph_data['ordered'],
            "dependency_graph": graph_data['graph'],
            "contexts":         contexts,
            "analysis_ids":     analysis_ids,
            "project_summary":  project_summary,
            "status":           "COMPLETED",
            "completed_at":     datetime.utcnow(),
            "created_at":       datetime.utcnow()
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
