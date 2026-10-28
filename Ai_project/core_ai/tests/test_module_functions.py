"""
اختبارات خطوة الدوال المستقلة (برّا أي كلاس): بتظهر بـ module_functions، وبتتحوّل لكلاس وهمي
<module>، وبتنفحص بالكود مقابل التوثيق وبالكود مقابل الكود.

    python -m pytest core_ai/tests/test_module_functions.py -q
"""
import pytest

from core_ai.language_processors.python_processor import PythonProcessor
from core_ai.services.conflict_detection.ast_unifier import ASTUnifier
from core_ai.services.conflict_detection.code_doc_consistency import CodeDocConsistencyChecker
from core_ai.services.conflict_detection.schemas import MODULE_CLASS
from core_ai.services.conflict_detection.structural_diff import StructuralDiff

PY = '''
import os

def load(path: str, strict: bool = False) -> dict:
    """Load a file."""
    return {}

async def fetch(url):
    return await get(url)

def _helper(x):
    return x

class Store:
    def get(self, k):
        return self.d[k]
'''


def py_data(code):
    p = PythonProcessor()
    a = p.parse_source_code(code)
    return p.generate_class_diagram_data(a, p.extract_features(a))


def unified(code):
    return ASTUnifier.from_tree_sitter({"class_diagram_data": py_data(code)})


def ts_data(code, lang):
    from core_ai.language_processors.tree_sitter_processor import TreeSitterProcessor
    p = TreeSitterProcessor(lang)
    if not p._ready:
        pytest.skip(f"tree-sitter {lang} غير متاح بهالبيئة (بيشتغل بالـ Docker)")
    a = p.parse_source_code(code)
    return p.generate_class_diagram_data(a, p.extract_features(a))


# ─────────────────────────────────────────────────────────────────────
# 1. الاستخراج
# ─────────────────────────────────────────────────────────────────────

def test_python_module_functions_extracted():
    data = py_data(PY)
    funcs = {f["name"]: f for f in data["module_functions"]}
    assert set(funcs) == {"load", "fetch", "_helper"}
    assert funcs["load"]["signature"] == "load(path: str, strict: bool): dict"
    assert funcs["load"]["parameters"][1]["default"] == "False"
    assert funcs["load"]["docstring"] == "Load a file."
    assert funcs["fetch"]["is_async"] is True
    assert funcs["_helper"]["visibility"] == "protected"


def test_class_diagram_unchanged_for_frontend():
    # الدوال المستقلة بمفتاح منفصل؛ "classes" نفسها ما تغيّرت
    data = py_data(PY)
    assert [c["name"] for c in data["classes"]] == ["Store"]
    assert "module_functions" not in py_data("class A:\n    def f(self):\n        return 1\n")


def test_unifier_adds_module_class_last():
    names = [c.name for c in unified(PY).classes]
    assert names == ["Store", MODULE_CLASS]
    module = unified(PY).classes[-1]
    assert {m.name for m in module.methods} == {"load", "fetch", "_helper"}


def test_old_analysis_without_module_functions():
    old = {"class_diagram_data": {"classes": [{"name": "A", "methods": []}]}}
    assert [c.name for c in ASTUnifier.from_tree_sitter(old).classes] == ["A"]


# ─────────────────────────────────────────────────────────────────────
# 2. الكود مقابل التوثيق
# ─────────────────────────────────────────────────────────────────────

def _flags(code, doc):
    out = CodeDocConsistencyChecker.compare(unified(code), {"content": doc, "explanation_type": "low_level"})
    return out, [(c.class_name, c.member) for c in out if c.class_name != "Overall"]


def test_documented_function_is_matched():
    doc = "### Function: load\nLoads a file.\n### Function: fetch\nFetches.\n### Function: _helper\nHelps.\n" \
          "## Class: Store\n### Method: get\nGets.\n"
    out, flags = _flags(PY, doc)
    assert flags == []
    overall = next(c for c in out if c.class_name == "Overall").element
    assert overall["coverage_percentage"] == 100.0


def test_no_undocumented_class_alert_for_module():
    doc = "## Class: Store\n### Method: get\nGets.\n"
    out, flags = _flags(PY, doc)
    assert flags == []                                             # من الخطوة 6: "غير موثّق" مش تنبيه
    overall = next(c for c in out if c.class_name == "Overall").element
    assert MODULE_CLASS not in overall["undocumented_classes"]     # ما في "الكلاس <module> غير موثّق"
    assert sorted(u["method"] for u in overall["undocumented_methods"] if u["class"] == MODULE_CLASS) \
        == ["_helper", "fetch", "load"]


def test_module_not_counted_as_class_in_score():
    doc = "## Class: Store\n### Method: get\nGets.\n"
    out, _ = _flags(PY, doc)
    overall = next(c for c in out if c.class_name == "Overall").element
    assert overall["compatibility_score"] == 100.0                 # الكلاس الحقيقي الوحيد موثّق
    assert MODULE_CLASS not in overall["undocumented_classes"]


# ─────────────────────────────────────────────────────────────────────
# 3. الكود مقابل الكود
# ─────────────────────────────────────────────────────────────────────

def test_function_removed_reported_as_method_not_class():
    before = "def a(x):\n    return x\n\ndef b(y):\n    return y\n"
    after = "def a(x):\n    return x\n"
    cats = [(c.category, c.class_name, c.member) for c in StructuralDiff.compare(unified(before), unified(after))]
    assert ("method_removed", MODULE_CLASS, "b") in cats
    assert not any(c[0] in ("class_removed", "class_added") for c in cats)


def test_first_function_added_is_not_class_added():
    before = "class A:\n    def f(self):\n        return 1\n"
    after = before + "\ndef util(z):\n    return z\n"
    cats = [(c.category, c.class_name, c.member) for c in StructuralDiff.compare(unified(before), unified(after))]
    assert ("method_added", MODULE_CLASS, "util") in cats
    assert not any(c[0] == "class_added" for c in cats)


def test_function_signature_change_detected():
    before = "def connect(host, port):\n    return 1\n"
    after = "def connect(host):\n    return 1\n"
    cats = [c.category for c in StructuralDiff.compare(unified(before), unified(after))]
    assert "method_signature_changed" in cats


# ─────────────────────────────────────────────────────────────────────
# 4. JavaScript / TypeScript
# ─────────────────────────────────────────────────────────────────────

JS = '''
import x from "y";
function plain(a, b = 2) { return a + b; }
export function exported(opts) { return opts; }
export default function main() { return 0; }
const arrow = (u) => u * 2;
export const exportedArrow = async (v) => { return v; };
let notAFunction = 5;
class Box { open() { return 1; } }
'''


def test_js_module_functions():
    data = ts_data(JS, "javascript")
    names = [f["name"] for f in data["module_functions"]]
    assert names == ["plain", "exported", "main", "arrow", "exportedArrow"]
    plain = data["module_functions"][0]
    assert [p["name"] for p in plain["parameters"]] == ["a", "b"]
    assert plain["parameters"][1]["default"] == "2"
    assert data["module_functions"][-1]["is_async"] is True
    assert [c["name"] for c in data["classes"]] == ["Box"]


def test_ts_module_functions():
    ts = ("export function parse(input: string, strict?: boolean): number { return 1; }\n"
          "export function useRetry<T = any>(fn: () => T): T { return fn(); }\n")
    data = ts_data(ts, "typescript")
    f = data["module_functions"][0]
    assert f["name"] == "parse"
    assert [p["name"] for p in f["parameters"]] == ["input", "strict"]
    assert data["module_functions"][1]["name"] == "useRetry"     # بدون <T = any>>
