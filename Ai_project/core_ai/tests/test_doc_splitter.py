"""
اختبارات الخطوة 3: DocSplitter (تقسيم التوثيق وربطه بالكود).

    python -m pytest core_ai/tests/test_doc_splitter.py -q

العينات الحقيقية (fixtures/real_docs_book.json): 3 توثيقات مولّدة من النظام ومحفوظة بـ Mongo
لكلاس Book بالجافا (high_level ×2، low_level ×1) مع الكود تبعها.
"""
import json
from pathlib import Path

import pytest

from core_ai.language_processors.python_processor import PythonProcessor
from core_ai.services.conflict_detection.ast_unifier import ASTUnifier
from core_ai.services.conflict_detection.code_doc_consistency import CodeDocConsistencyChecker
from core_ai.services.conflict_detection.doc_splitter import DocSplitter, parse_member_header

REAL_DOCS = json.loads((Path(__file__).parent / "fixtures" / "real_docs_book.json").read_text(encoding="utf-8"))


# ─────────────────────────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────────────────────────

def java_diagram(code: str):
    from core_ai.language_processors.java_processor import JavaProcessor
    p = JavaProcessor()
    if p._internal_java_parser is None:   # جهاز التطوير (tree-sitter 0.25)
        try:
            from tree_sitter import Language, Parser
            import tree_sitter_java
            lang = Language(tree_sitter_java.language())
            p._java_language, p._internal_java_parser = lang, Parser(lang)
        except Exception as e:  # pragma: no cover
            pytest.skip(f"Java tree-sitter غير متاح: {e}")
    a = p.parse_source_code(code)
    return ASTUnifier.from_tree_sitter({"class_diagram_data": p.generate_class_diagram_data(a, p.extract_features(a))})


def py_diagram(code: str):
    p = PythonProcessor()
    a = p.parse_source_code(code)
    return ASTUnifier.from_tree_sitter({"class_diagram_data": p.generate_class_diagram_data(a, p.extract_features(a))})


def real(doc_id_suffix: str) -> dict:
    return next(d for d in REAL_DOCS if d["id"].endswith(doc_id_suffix))


def undocumented_flags(doc: dict, diagram) -> list:
    out = CodeDocConsistencyChecker.compare(diagram, {"content": doc["content"], "explanation_type": doc["explanation_type"]})
    return sorted(c.member or c.class_name for c in out if c.class_name != "Overall" and "غير موثق" in c.description)


# ─────────────────────────────────────────────────────────────────────
# 1. قراءة العناوين بأشكالها المختلفة
# ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("header, name, count", [
    ("public Book(String title, String author, String isbn)", "Book", 3),
    ("Book(String title, String author, String isbn)", "Book", 3),
    ("Book", "Book", None),
    ("setAvailable(self, available: boolean)", "setAvailable", 1),   # الموديل كتب self لكود جافا
    ("getTitle()", "getTitle", 0),
    ("`place_order(self, item_id, qty)`", "place_order", 2),
    ("public static <R> R convert(Object o, Class<R> k)", "convert", 2),
    ("__init__(self, db)", "__init__", 1),
    ("charge(amount: float, card_token: str) -> bool", "charge", 2),
    ("get(Map<String, Integer> m, int x)", "get", 2),   # فاصلة جوا generics ما بتنحسب
])
def test_member_header_variants(header, name, count):
    h = parse_member_header(header)
    assert h["name"] == name
    assert h["param_count"] == count


# ─────────────────────────────────────────────────────────────────────
# 2. التقسيم على التوثيقات الحقيقية
# ─────────────────────────────────────────────────────────────────────

def test_real_high_level_split_structure():
    snippets = DocSplitter.split({"content": real("65dc3c")["content"]})
    scopes = [(s.scope, s.class_name, s.member) for s in snippets]
    assert scopes == [
        ("file", None, None),
        ("class", "Book", None),
        ("method", "Book", "Book"),
        ("method", "Book", "getTitle"),
        ("method", "Book", "getIsbn"),
        ("method", "Book", "isAvailable"),
        ("method", "Book", "setAvailable"),
    ]
    ctor = snippets[2]
    assert ctor.is_constructor and ctor.header_param_count == 3
    assert "Sets availability to true by default" in ctor.text


def test_real_low_level_sections_go_to_their_method():
    snippets = DocSplitter.split({"content": real("43cd4b")["content"]})
    by_member = {s.member: s for s in snippets if s.scope == "method"}
    assert set(by_member) == {"Book", "getTitle", "getIsbn", "isAvailable", "setAvailable"}
    set_av = by_member["setAvailable"].text
    assert "**Returns:** void" in set_av and "**Parameters:**" in set_av
    assert "getTitle" not in set_av            # ما في تسريب من القسم يلي قبله


def test_file_level_claims_are_kept():
    """'Retrieve the book's title, author, and ISBN' — تناقض حقيقي (ما في getAuthor) بالقسم العام."""
    snippets = DocSplitter.split({"content": real("43cd3c")["content"]})
    file_snip = next(s for s in snippets if s.scope == "file")
    assert "author" in file_snip.text and "Key Capabilities" in file_snip.text


# ─────────────────────────────────────────────────────────────────────
# 3. الربط بالكود
# ─────────────────────────────────────────────────────────────────────

def test_real_docs_match_constructor_and_methods():
    for doc in REAL_DOCS:
        diagram = java_diagram(doc["code"])
        mapping = DocSplitter.match(DocSplitter.split({"content": doc["content"]}), diagram, doc["content"])
        ctor = next(m for m in mapping.matched if m.snippet.is_constructor)
        assert ctor.methods[0].is_constructor, doc["id"]
        assert mapping.unmatched == [], doc["id"]


def test_real_partial_doc_reports_coverage_not_errors():
    diagram = java_diagram(real("43cd3c")["code"])
    mapping = DocSplitter.match(DocSplitter.split({"content": real("43cd3c")["content"]}), diagram)
    assert sorted(m["method"] for m in mapping.undocumented_methods) == ["getIsbn", "getTitle", "isAvailable"]


def test_documented_method_missing_from_code_is_unmatched():
    doc = real("65dc3c")["content"] + "\n### Method: getAuthor()\nLogic Flow:\n1. Returns the author\n"
    diagram = java_diagram(real("65dc3c")["code"])
    mapping = DocSplitter.match(DocSplitter.split({"content": doc}), diagram)
    assert [s.member for s in mapping.unmatched] == ["getAuthor"]


def test_overloads_resolved_by_param_count():
    code = '''
public class Repo {
  public Repo() { }
  public Repo(String url) { this.url = url; }
}'''
    doc = "## Class: Repo\n### Constructor: Repo(String url)\nConnects to url.\n"
    mapping = DocSplitter.match(DocSplitter.split(doc), java_diagram(code))
    methods = mapping.matched[-1].methods
    assert len(methods) == 1 and methods[0].signature == "+ Repo(url: String)"
    assert mapping.undocumented_methods == [{"class": "Repo", "method": "Repo"}]   # الـ overload التاني


# ─────────────────────────────────────────────────────────────────────
# 4. أشكال توثيق تانية
# ─────────────────────────────────────────────────────────────────────

PY_CODE = '''
class OrderService:
    def __init__(self, db):
        self.db = db
    def place_order(self, item_id, qty):
        return self.db.save(item_id, qty)
class Invoice:
    def total(self):
        return 0
'''

PROJECT_DOC = '''File: Shop

## Executive Summary
A small shop backend.

## File: services.py
**File Purpose:** Order handling.

### Class: OrderService
**Purpose:** Places orders.

### Constructor: __init__
**Description:** Stores db.

### Method: place_order
**Description:** Saves an order.

## File: billing.py

### Class: Invoice
### Method: total
**Returns:** 0

## Global Architectural Recommendations
Add logging.
'''


def test_project_doc_with_file_sections():
    snippets = DocSplitter.split(PROJECT_DOC)
    files = [(s.scope, s.file_name, s.class_name, s.member) for s in snippets]
    assert ("method", "services.py", "OrderService", "place_order") in files
    assert ("method", "billing.py", "Invoice", "total") in files
    recs = [s for s in snippets if "Add logging" in s.text]
    assert len(recs) == 1 and recs[0].scope == "file"       # رجع لمستوى الملف بعد الكلاس

    mapping = DocSplitter.match(snippets, py_diagram(PY_CODE))
    assert mapping.unmatched == [] and mapping.undocumented_methods == []


def test_structured_dict_doc():
    doc = {"OrderService.place_order": {"signature": "place_order(self, item_id, qty)",
                                        "description": "Places an order", "raises": ["ValueError"]}}
    snippets = DocSplitter.split(doc)
    assert snippets[0].source == "structured" and snippets[0].header_param_count == 2
    assert "raises: ['ValueError']" in snippets[0].text
    mapping = DocSplitter.match(snippets, py_diagram(PY_CODE))
    assert mapping.matched[0].methods[0].name == "place_order"


def test_doc_without_headings_uses_keyword_fallback():
    text = "The service exposes place_order to create orders.\n\nInvoices are computed elsewhere."
    mapping = DocSplitter.match(DocSplitter.split(text), py_diagram(PY_CODE), text)
    matched = {(m.class_name, m.methods[0].name) for m in mapping.matched}
    assert matched == {("OrderService", "place_order")}
    assert mapping.matched[0].snippet.source == "keyword"


def test_empty_doc():
    mapping = DocSplitter.match(DocSplitter.split({"content": ""}), py_diagram(PY_CODE))
    assert mapping.matched == [] and len(mapping.undocumented_methods) == 3


# ─────────────────────────────────────────────────────────────────────
# 5. أثره على الـ checker الحالي (قبل / بعد)
# ─────────────────────────────────────────────────────────────────────

def test_checker_no_longer_flags_documented_constructor():
    # قبل: 'Book' كانت تنحسب غير موثّقة بالتوثيقات الثلاثة (الـ regex ما بيعرف Constructor:)
    for doc in REAL_DOCS:
        assert "Book" not in undocumented_flags(doc, java_diagram(doc["code"])), doc["id"]


def test_checker_partial_doc_still_reports_coverage_gaps():
    # تنبيهات "غير موثّقة" لسا موجودة (بتنتقل لإحصائيات التغطية بالخطوة 6)
    doc = real("43cd3c")
    assert undocumented_flags(doc, java_diagram(doc["code"])) == ["getIsbn", "getTitle", "isAvailable"]
