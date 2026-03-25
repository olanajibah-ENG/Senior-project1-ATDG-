import ast
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class CrossFileContextBuilder:
    """
    مهمة علا رقم 2.5: استخراج التواقيع وتقليص السياق للـ LLM بناءً على ورقة RepoBench
    """
    
    def extract_signatures(self, code_content: str, file_type: str = 'python') -> str:
        """
        تبسيط ملفات الكود لاستخراج تواقيع الدوال والكلاسات فقط بتشذيب أي تنفيذ داخلي.
        """
        signatures = []
        file_type = file_type.lower()

        if file_type == 'python':
            try:
                tree = ast.parse(code_content)
                for node in tree.body:
                    # صيد الكلاسات
                    if isinstance(node, ast.ClassDef):
                        signatures.append(f"class {node.name}:")
                        doc = ast.get_docstring(node)
                        if doc: signatures.append(f'    """{doc}"""')
                        
                    # صيد الدوال العادية وغير المتزامنة
                    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        args = [arg.arg for arg in node.args.args]
                        args_str = ", ".join(args)
                        
                        returns = ""
                        if getattr(node, 'returns', None):
                            if isinstance(node.returns, ast.Name):
                                returns = f" -> {node.returns.id}"
                                
                        signatures.append(f"def {node.name}({args_str}){returns}: ...")
                        doc = ast.get_docstring(node)
                        if doc: signatures.append(f'    """{doc}"""')
            except SyntaxError:
                pass

        elif file_type in ('java', 'javascript', 'typescript', 'js', 'ts'):
            signatures.extend(self._extract_js_java_signatures(code_content, file_type=file_type))

        return "\n".join(signatures)

    def _extract_js_java_signatures(self, code_content: str, file_type: str) -> list:
        import re
        sigs = []
        lines = code_content.split('\n')

        for line in lines:
            stripped = line.strip()

            # class definitions (Java/JS/TS)
            if re.match(r'^(public\s+)?class\s+\w+', stripped):
                part = stripped.split('{')[0].strip()
                sigs.append(part + ' { ... }')
                continue

            # JS/TS function declarations
            if re.match(r'^(export\s+)?function\s+\w+', stripped):
                part = stripped.split('{')[0].strip()
                sigs.append(part + ' { ... }')
                continue

            # JS/TS arrow function declarations
            m = re.match(r'^(export\s+)?(const|let|var)\s+(\w+)\s*=\s*\(?[^=]*\)?\s*=>', stripped)
            if m:
                fn_name = m.group(3)
                sigs.append(f"function {fn_name}(...) {{ ... }}")
                continue

            # Java-like method declarations
            if file_type in ('java',) and re.match(r'^(public|private|protected|static|final)\s+', stripped):
                if '(' in stripped and ')' in stripped and '{' in stripped and not stripped.endswith(';'):
                    sigs.append(stripped.split('{')[0].strip() + ' { ... }')

        return sigs

    def build_llm_context(self, dependencies_content_dict: Dict[str, str]) -> str:
        """
        استلام محتوى ملفات التبعيات، وتحويلها لـ Text مسطح مركزّ جداً لتغذيته للـ LLM.
        """
        context_blocks = []
        for filename, content in dependencies_content_dict.items():
            context_blocks.append(f"\n--- Context from Dependency: {filename} ---")
            
            file_type = 'python' if filename.endswith('.py') else 'java' if filename.endswith('.java') else 'unknown'
            sigs = self.extract_signatures(content, file_type=file_type)
            
            if sigs:
                context_blocks.append(sigs)
            else:
                context_blocks.append("No signatures extracted or file type not supported for signature extraction.")
            
        return "\n".join(context_blocks)
