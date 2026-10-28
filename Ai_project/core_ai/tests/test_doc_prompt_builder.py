"""
اختبارات الخطوة 4: تجهيز طلبات الـ LLM للكود مقابل التوثيق (بدون استدعاء LLM).

    python -m pytest core_ai/tests/test_doc_prompt_builder.py -q
"""
import json
import re

import pytest

from core_ai.language_processors.python_processor import PythonProcessor
from core_ai.services.conflict_detection import doc_prompt_builder as dpb
from core_ai.services.conflict_detection.ast_unifier import ASTUnifier
from core_ai.services.conflict_detection.doc_splitter import DocSplitter
from core_ai.services.conflict_detection.prompts.conflict_prompts import CODE_DOC_PROMPT
from core_ai.services.conflict_detection.schemas import MODULE_CLASS


def diagram(code: str):
    p = PythonProcessor()
    a = p.parse_source_code(code)
    return ASTUnifier.from_tree_sitter({"class_diagram_data": p.generate_class_diagram_data(a, p.extract_features(a))})


def requests_for(code: str, doc: str, **kw):
    d = diagram(code)
    mapping = DocSplitter.match(DocSplitter.split({"content": doc}), d, doc)
    return dpb.build_code_doc_requests(mapping, d, language="python", **kw)


CODE = '''
class Cache:
    """Cache."""

    def get(self, key: str, default=None):
        if key in self.d:
            return self.d[key]
        return default

    def put(self, key, value, *, ttl: int = 60, **meta):
        self.d[key] = value

    @staticmethod
    def make():
        return Cache()

def helper(x, *rest):
    return x
'''

DOC = '''## Executive Summary
A small cache that stores values.

## Class: Cache
**Purpose:** In-memory cache with expiry.

### Method: get
Returns the cached value, or raises KeyError if missing.

### Method: put
Stores the value for ttl seconds.

### Function: helper
Returns its first argument.
'''


# ─────────────────────────────────────────────────────────────────────
# 1. شكل الطلب
# ─────────────────────────────────────────────────────────────────────

def test_one_request_per_class():
    reqs = requests_for(CODE, DOC)
    assert [r.class_name for r in reqs] == ["Cache", MODULE_CLASS]
    assert [i.id for i in reqs[0].items] == ["Cache", "Cache.get", "Cache.put"]
    assert [i.id for i in reqs[1].items] == [f"{MODULE_CLASS}.helper"]


def test_each_method_gets_only_its_own_doc():
    req = requests_for(CODE, DOC)[0]
    items = re.split(r"\nITEM id=", "\n" + req.user.split("For EACH item")[0])
    get_item = next(t for t in items if t.startswith("Cache.get"))
    assert "raises KeyError" in get_item
    assert "ttl seconds" not in get_item            # توثيق put ما تسرّب لـ get
    assert req.items[1].doc_text.startswith("Returns the cached value")


def test_class_item_has_members_and_general_doc():
    req = requests_for(CODE, DOC)[0]
    class_item = req.user.split("ITEM id=Cache  (the class itself)")[1].split("ITEM id=")[0]
    assert "- get(key: str, default: Any): Any" in class_item
    assert "A small cache that stores values." in class_item     # القسم العام للملف
    assert "In-memory cache with expiry." in class_item


def test_prompt_has_three_questions_and_valid_json_template():
    req = requests_for(CODE, DOC)[0]
    for key in ("not_implemented", "conflicting", "undocumented"):
        assert key in req.user
    template = req.user[req.user.index("Return ONLY this JSON:") + len("Return ONLY this JSON:"):]
    assert json.loads(template.strip())["results"][0]["id"] == "<item id>"
    assert "{{" not in req.user


def test_no_few_shot_examples():
    # متل DocPrism: ما في أمثلة محلولة (لحتى ما يتعلّم الموديل حالات من بيانات القياس).
    # كلمة "example" بتطلع بس كنوع تناقض (مثال بالتوثيق ما بيشتغل)، مش كمثال محلول.
    low = CODE_DOC_PROMPT.lower()
    assert not re.search(r"example\s*\d|few-shot|expected output|input:", low)
    assert low.count("item id=") == 0                      # البنود بتنحط بس بـ {items}


# ─────────────────────────────────────────────────────────────────────
# 2. كود الدالة
# ─────────────────────────────────────────────────────────────────────

def test_reconstructed_python_signature():
    d = diagram(CODE)
    cache = next(c for c in d.classes if c.name == "Cache")
    put = next(m for m in cache.methods if m.name == "put")
    text = dpb.method_code(put, "python")
    assert "   1 | def put(self, key, value, *, ttl: int = 60, **meta):" in text
    assert "   2 |     self.d[key] = value" in text
    make = next(m for m in cache.methods if m.name == "make")
    assert "def make():" in dpb.method_code(make, "python")             # staticmethod: بدون self


def test_module_function_has_no_self():
    req = requests_for(CODE, DOC)[1]
    assert "def helper(x, *rest):" in req.user
    assert "self" not in req.user.split("[CODE]")[1].split("[/CODE]")[0]


def test_original_source_lines_used_when_given():
    code = CODE.strip() + "\n"
    req = requests_for(code, DOC, source_code=code)[0]
    get_code = req.user.split("ITEM id=Cache.get")[1].split("[/CODE]")[0]
    assert "   4 |     def get(self, key: str, default=None):" in get_code      # رقم السطر الحقيقي
    assert "   7 |         return default" in get_code


def test_java_like_reconstruction():
    from core_ai.services.conflict_detection.schemas import MethodDetail, ParameterDetail
    m = MethodDetail(name="value", signature="+ value(v: double): double", return_type="double",
                     parameters=[ParameterDetail(name="v", type="double")],
                     body="{\n    return v * 2;\n}", decorators=["@Override"])
    text = dpb.method_code(m, "java")
    assert "   1 | @Override" in text and "   2 | double value(double v) {" in text


# ─────────────────────────────────────────────────────────────────────
# 3. حالات خاصة
# ─────────────────────────────────────────────────────────────────────

def test_large_class_is_split(monkeypatch):
    monkeypatch.setattr(dpb, "MAX_REQUEST_CHARS", 400)
    reqs = requests_for(CODE, DOC)
    cache_reqs = [r for r in reqs if r.class_name == "Cache"]
    assert len(cache_reqs) >= 2
    assert cache_reqs[0].items[0].id == "Cache"                       # بند الكلاس أول شي
    all_ids = [i.id for r in cache_reqs for i in r.items]
    assert sorted(all_ids) == ["Cache", "Cache.get", "Cache.put"]     # ولا بند ضاع أو تكرر


def test_undocumented_methods_not_sent():
    req = requests_for(CODE, DOC)[0]
    assert "ITEM id=Cache.make" not in req.user                      # make ما إلها توثيق → تغطية بس


def test_no_doc_no_requests():
    assert requests_for(CODE, "") == []


def test_long_body_truncated(monkeypatch):
    monkeypatch.setattr(dpb, "MAX_ITEM_CODE_LINES", 3)
    d = diagram(CODE)
    get = next(m for c in d.classes for m in c.methods if m.name == "get")
    assert dpb.method_code(get, "python").endswith("... (code truncated)")
