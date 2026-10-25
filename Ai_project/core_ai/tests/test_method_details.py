"""
اختبارات الخطوة 1: body / body_hash / parameters / docstring / async / constructors.

    python -m pytest core_ai/tests/test_method_details.py -q
"""
import pytest

from core_ai.language_processors.python_processor import PythonProcessor
from core_ai.language_processors.java_processor import JavaProcessor
from core_ai.services.conflict_detection.ast_unifier import ASTUnifier
from core_ai.services.conflict_detection.semantic_analyzer import prune_diagram
from core_ai.services.conflict_detection.structural_diff import StructuralDiff


# ─────────────────────────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────────────────────────

def py_methods(code: str) -> dict:
    p = PythonProcessor()
    ast_data = p.parse_source_code(code)
    diagram = p.generate_class_diagram_data(ast_data, p.extract_features(ast_data))
    return {m["name"]: m for c in diagram["classes"] for m in c["methods"]}


def java_processor() -> JavaProcessor:
    p = JavaProcessor()
    if p._internal_java_parser is None:
        # tree-sitter المحلي أحدث من المثبّت بـ requirements.txt (0.20)، فـ set_language
        # مش موجودة. واجهة الـ nodes نفسها بالنسختين، فمنبني الـ parser بالطريقة الجديدة.
        try:
            from tree_sitter import Language, Parser
            import tree_sitter_java
            lang = Language(tree_sitter_java.language())
            p._java_language = lang
            p._internal_java_parser = Parser(lang)
        except Exception as e:  # pragma: no cover
            pytest.skip(f"Java tree-sitter غير متاح: {e}")
    return p


def java_methods(code: str) -> dict:
    p = java_processor()
    ast_data = p.parse_source_code(code)
    diagram = p.generate_class_diagram_data(ast_data, p.extract_features(ast_data))
    return {m["name"]: m for c in diagram["classes"] for m in c["methods"]}


PY_BASE = '''
class Repo:
    def __init__(self, store: dict):
        self.store = store

    def get(self, uid: int, *, strict: bool = False) -> "Optional[User]":
        """Return the user. Raises KeyError if missing."""
        # lookup
        return self.store.get(uid)

    def add(self, u, force=False, *extra, **opts):
        self.store[u.id] = u

    async def fetch(self, uid):
        return await self.client.get(uid)
'''


# ─────────────────────────────────────────────────────────────────────
# Python
# ─────────────────────────────────────────────────────────────────────

def test_python_signature_unchanged():
    m = py_methods(PY_BASE)
    # نفس الصيغة القديمة حرف بحرف (الواجهة و FingerprintBuilder بيعتمدوا عليها)
    assert m["get"]["signature"] == "get(uid: int): Optional[User]"
    assert m["add"]["signature"] == "add(u: Any, force: Any): Any"
    assert m["__init__"]["signature"] == "+ __init__(store: dict)"


def test_python_parameters():
    params = {p["name"]: p for p in py_methods(PY_BASE)["add"]["parameters"]}
    assert list(params) == ["u", "force", "extra", "opts"]
    assert params["force"]["default"] == "False"
    assert params["extra"]["kind"] == "var_positional"
    assert params["opts"]["kind"] == "var_keyword"

    get_params = {p["name"]: p for p in py_methods(PY_BASE)["get"]["parameters"]}
    assert get_params["strict"] == {"name": "strict", "type": "bool", "default": "False", "kind": "keyword_only"}


def test_python_docstring_and_body():
    get = py_methods(PY_BASE)["get"]
    assert get["docstring"] == "Return the user. Raises KeyError if missing."
    assert get["body"] == "return self.store.get(uid)"   # بدون docstring وبدون تعليق
    assert get["return_type"] == "Optional[User]"
    assert get["body_hash"]


def test_python_async_methods_now_included():
    fetch = py_methods(PY_BASE)["fetch"]
    assert fetch["is_async"] is True
    assert "await" in fetch["body"]


def test_python_hash_ignores_comments_whitespace_and_docstring():
    changed = PY_BASE.replace(
        "        # lookup\n        return self.store.get(uid)",
        "        # a different comment\n\n        return   self.store.get( uid )  # trailing",
    ).replace("Return the user.", "Fetch the user.")
    assert py_methods(PY_BASE)["get"]["body_hash"] == py_methods(changed)["get"]["body_hash"]


def test_python_hash_changes_on_logic_change():
    changed = PY_BASE.replace("return self.store.get(uid)", "return self.store[uid]")
    assert py_methods(PY_BASE)["get"]["body_hash"] != py_methods(changed)["get"]["body_hash"]


# ─────────────────────────────────────────────────────────────────────
# Java
# ─────────────────────────────────────────────────────────────────────

JAVA_BASE = '''
public class A {
  private int x;
  /** Creates A. */
  public A(int x, String... names) { this.x = x; }
  /** Gets it. */
  @Override
  public int[] get(final int[] a, java.util.List<String> b) { // c
     return a; /* z */ }
}
'''


def test_java_constructor_now_included():
    m = java_methods(JAVA_BASE)
    assert m["A"]["is_constructor"] is True
    assert m["A"]["docstring"] == "/** Creates A. */"
    assert m["A"]["body_hash"]


def test_java_parameters_arrays_and_varargs():
    m = java_methods(JAVA_BASE)
    get_params = m["get"]["parameters"]
    assert [(p["name"], p["type"]) for p in get_params] == [("a", "int[]"), ("b", "java.util.List<String>")]
    ctor_params = m["A"]["parameters"]
    assert ctor_params[-1] == {"name": "names", "type": "String...", "default": None, "kind": "var_positional"}
    assert m["get"]["return_type"] == "int[]"
    assert m["get"]["decorators"] == ["@Override"]


def test_java_hash_ignores_comments_but_not_logic():
    base = java_methods(JAVA_BASE)["get"]["body_hash"]
    no_comments = JAVA_BASE.replace("// c", "").replace("/* z */", "// other")
    assert java_methods(no_comments)["get"]["body_hash"] == base
    changed = JAVA_BASE.replace("return a;", "return null;")
    assert java_methods(changed)["get"]["body_hash"] != base


# ─────────────────────────────────────────────────────────────────────
# Unifier / التوافق مع التحليلات القديمة
# ─────────────────────────────────────────────────────────────────────

def _analysis(classes):
    return {"class_diagram_data": {"classes": classes}, "extracted_features": {"language": "python"}}


def test_unifier_passes_new_fields():
    p = PythonProcessor()
    ast_data = p.parse_source_code(PY_BASE)
    diagram = p.generate_class_diagram_data(ast_data, p.extract_features(ast_data))
    unified = ASTUnifier.from_tree_sitter(_analysis(diagram["classes"]))
    get = next(m for m in unified.classes[0].methods if m.name == "get")
    assert get.body_hash and get.docstring and get.parameters[0].name == "uid"


def test_old_stored_analysis_still_works():
    # تحليل محفوظ قبل الخطوة 1: ما فيه body ولا parameters
    old = _analysis([{"name": "Repo", "methods": [
        {"name": "get", "signature": "get(uid: int): Any", "visibility": "public"}]}])
    unified = ASTUnifier.from_tree_sitter(old)
    m = unified.classes[0].methods[0]
    assert m.body_hash is None and m.parameters is None
    # StructuralDiff كان رح يوقع على parameters=None
    StructuralDiff.compare(unified, unified)


def test_prompt_fields_unchanged():
    p = PythonProcessor()
    ast_data = p.parse_source_code(PY_BASE)
    diagram = p.generate_class_diagram_data(ast_data, p.extract_features(ast_data))
    unified = ASTUnifier.from_tree_sitter(_analysis(diagram["classes"]))
    pruned = prune_diagram(unified.model_dump())
    for m in pruned["classes"][0]["methods"]:
        assert set(m) <= {"name", "signature", "is_abstract", "is_constructor", "visibility", "is_override"}
