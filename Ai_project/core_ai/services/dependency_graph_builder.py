import graphlib
from typing import List, Dict, Any
import logging

try:
    from core_ai.language_processors.python_processor import PythonProcessor
    from core_ai.language_processors.java_processor import JavaProcessor
except ImportError:
    pass

logger = logging.getLogger(__name__)

class DependencyGraphBuilder:
    """
    مهمة علا رقم 2: بناء الشجرة والترتيب الطبولوجي بناءً على ورقة CodePlan
    """
    def __init__(self):
        try:
            self.processors = {
                'python': PythonProcessor(),
                'java': JavaProcessor()
            }
        except NameError:
            self.processors = {}
            logger.warning("Language processors could not be imported.")

    def process_and_sort(self, files_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        تأخذ قائمة بالملفات المرفوعة: [{'filename': '...', 'content': '...', 'file_type': 'python'}, ...]
        وتقوم بتوليد المخطط الطبولوجي (التسلسل المعتمد لترتيب تحليل الملفات).
        ترجع: {'ordered': [...], 'graph': {...}}
        """
        graph = {}
        project_filenames = {f['filename'] for f in files_list}

        for f in files_list:
            filename = f['filename']
            
            # If dependencies are already extracted (from ProjectAnalysisService)
            if 'dependencies' in f:
                all_imports = f['dependencies']
            else:
                # Otherwise, parse missing content (from dependency_graph_view)
                content = f.get('content', '')
                file_type = f.get('file_type', '').lower()

                processor = self.processors.get(file_type)
                if not processor:
                    logger.info(f"No processor for {file_type}. Marking {filename} as independent.")
                    graph[filename] = []
                    continue

                try:
                    ast_data = processor.parse_source_code(content)
                    all_imports = processor.extract_dependencies(ast_data)
                except Exception as e:
                    logger.error(f"Failed to process dependencies for {filename}: {e}")
                    all_imports = []

            # Resolve valid local imports against project filenames
            valid_imports = []
            for imp in all_imports:
                for pf in project_filenames:
                    # لا تضيف الملف لنفسه
                    if pf == filename:
                        continue
                    # استخرج اسم الملف بدون امتداد للمقارنة
                    pf_base = pf.rsplit('.', 1)[0]  # "User.java" → "User"
                    if imp == pf_base or imp == pf:
                        valid_imports.append(pf)

            graph[filename] = list(set(valid_imports))

        # الترتيب الطبولوجي
        ts = graphlib.TopologicalSorter(graph)
        try:
            ordered = list(ts.static_order())
        except graphlib.CycleError as e:
            logger.warning(f"Circular dependency detected! Falling back to flat list. Error: {e}")
            ordered = [f['filename'] for f in files_list]

        return {'ordered': ordered, 'graph': graph}
