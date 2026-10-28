"""
اختبارات الخطوة 5: DocSemanticAnalyzer — الإرسال، قراءة الجواب، والفلترة الخارجية.
الأجوبة مكتوبة بإيدنا (fake LLM) لحتى ما نصرف من حد الطلبات.

    python -m pytest core_ai/tests/test_doc_semantic_analyzer.py -q
"""
import json

import pytest

from core_ai.services.conflict_detection import doc_semantic_analyzer as dsa
from core_ai.services.conflict_detection.schemas import DocConsistencyLabel, SeverityLevel
from core_ai.tests.test_doc_prompt_builder import CODE, DOC, requests_for

DIRECT, OVER, UNDER = (DocConsistencyLabel.DIRECT_MISMATCH, DocConsistencyLabel.OVER_PROMISE,
                       DocConsistencyLabel.UNDER_PROMISE)


def cache_request():
    return [r for r in requests_for(CODE, DOC) if r.class_name == "Cache"]


def fake_llm(monkeypatch, *responses):
    """كل استدعاء بياخد الجواب يلي بعده؛ Exception = فشل الطلب. بيرجّع سجل الاستدعاءات."""
    calls = []
    seq = list(responses)

    def call_model(system_prompt, user_prompt, temperature=0.0, use_cache=True, **kw):
        calls.append({"use_cache": use_cache})
        r = seq.pop(0) if len(seq) > 1 else seq[0]
        if isinstance(r, Exception):
            raise r
        return r if isinstance(r, str) else json.dumps(r)
    monkeypatch.setattr(dsa.LLMClient, "call_model", staticmethod(call_model))
    return calls


def result(item_id, **questions):
    return {"id": item_id, "documentation_summary": "", "code_summary": "",
            "not_implemented": [], "conflicting": [], "undocumented": [], **questions}


GOOD = {"results": [
    result("Cache", not_implemented=[{"doc_snippet": "In-memory cache with expiry.", "explanation": "no expiry",
                                      "confidence": 0.9}]),
    result("Cache.get",
           conflicting=[{"doc_snippet": "Returns the cached value, or raises KeyError if missing.",
                         "code_snippet": "return default", "code_lines": [4], "explanation": "returns default",
                         "confidence": 1.0}],
           undocumented=[{"code_snippet": "return default", "code_lines": [4], "explanation": "default value",
                          "confidence": 0.9}]),
    result("Cache.put", not_implemented=[{"doc_snippet": "Stores the value for ttl seconds.",
                                          "explanation": "ttl unused", "confidence": 1.0}]),
]}


def run(monkeypatch, *responses, **kw):
    fake_llm(monkeypatch, *responses)
    analyzer = dsa.DocSemanticAnalyzer(**kw)
    return analyzer, analyzer.analyze(cache_request())


def by(items, member, label):
    return next(c for c in items if c.member == member and c.doc_label == label)


# ─────────────────────────────────────────────────────────────────────
# 1. الجواب السليم
# ─────────────────────────────────────────────────────────────────────

def test_good_response_becomes_flagged_conflicts(monkeypatch):
    analyzer, out = run(monkeypatch, GOOD)
    get = by(out, "get", DIRECT)
    assert get.is_flagged and get.severity == SeverityLevel.HIGH and get.ai_confidence == 1.0
    assert get.line_number == 4 and 'doc: "Returns the cached value' in get.evidence
    put = by(out, "put", OVER)
    assert put.is_flagged and put.severity == SeverityLevel.MEDIUM
    cls = by(out, None, OVER)                              # بند الكلاس نفسه
    assert cls.class_name == "Cache" and cls.is_flagged
    assert analyzer.stats.flagged == 3


def test_under_promise_kept_but_not_shown(monkeypatch):
    analyzer, out = run(monkeypatch, GOOD)
    under = by(out, "get", UNDER)
    assert under.is_flagged is False and under.severity == SeverityLevel.LOW
    assert analyzer.stats.under_promise == 1


# ─────────────────────────────────────────────────────────────────────
# 2. الفلترة
# ─────────────────────────────────────────────────────────────────────

def test_invented_doc_quote_dropped(monkeypatch):
    bad = {"results": [result("Cache.put", not_implemented=[
        {"doc_snippet": "Values are encrypted at rest.", "confidence": 1.0}])]}
    analyzer, out = run(monkeypatch, bad)
    assert out == [] and analyzer.stats.dropped_doc_quote == 1


def test_quote_from_another_method_doc_dropped(monkeypatch):
    # جملة موجودة بتوثيق put، بس الموديل نسبها لـ get
    bad = {"results": [result("Cache.get", conflicting=[
        {"doc_snippet": "Stores the value for ttl seconds.", "code_snippet": "return default",
         "code_lines": [4], "confidence": 1.0}])]}
    analyzer, out = run(monkeypatch, bad)
    assert out == [] and analyzer.stats.dropped_doc_quote == 1


@pytest.mark.parametrize("snippet, lines", [
    ("raise KeyError(key)", [4]),          # سطر مش موجود بالكود
    ("return default", [99]),              # رقم سطر برّا الدالة
])
def test_invented_code_quote_dropped(monkeypatch, snippet, lines):
    bad = {"results": [result("Cache.get", conflicting=[
        {"doc_snippet": "raises KeyError if missing", "code_snippet": snippet, "code_lines": lines,
         "confidence": 1.0}])]}
    analyzer, out = run(monkeypatch, bad)
    assert out == [] and analyzer.stats.dropped_code_quote == 1


def test_quote_tolerances(monkeypatch):
    ok = {"results": [result("Cache.get", conflicting=[
        {"doc_snippet": "Returns the **cached value**, or ... KeyError if missing",   # markdown + اختصار
         "code_snippet": "   4 |         return default",                                 # مع رقم السطر
         "code_lines": [4], "confidence": 0.95}])]}
    _, out = run(monkeypatch, ok)
    assert by(out, "get", DIRECT).is_flagged


def test_threshold(monkeypatch):
    low = {"results": [result("Cache.put", not_implemented=[
        {"doc_snippet": "Stores the value for ttl seconds.", "confidence": 0.6}])]}
    analyzer, out = run(monkeypatch, low)
    assert by(out, "put", OVER).is_flagged is False and analyzer.stats.below_threshold == 1
    _, out = run(monkeypatch, low, threshold=0.5)
    assert by(out, "put", OVER).is_flagged is True


def test_confidence_percent_normalized(monkeypatch):
    pct = {"results": [result("Cache.put", not_implemented=[
        {"doc_snippet": "Stores the value for ttl seconds.", "confidence": 85}])]}
    _, out = run(monkeypatch, pct)
    assert by(out, "put", OVER).ai_confidence == 0.85


def test_duplicates_keep_highest_confidence(monkeypatch):
    dup = {"results": [result("Cache.put", not_implemented=[
        {"doc_snippet": "Stores the value for ttl seconds.", "confidence": 0.75},
        {"doc_snippet": "ttl seconds", "confidence": 0.95}])]}
    analyzer, out = run(monkeypatch, dup)
    assert len(out) == 1 and out[0].ai_confidence == 0.95 and analyzer.stats.duplicates == 1


def test_unknown_item_id_ignored(monkeypatch):
    analyzer, out = run(monkeypatch, {"results": [result("Cache.delete", conflicting=[
        {"doc_snippet": "x", "code_snippet": "y", "confidence": 1}])]})
    assert out == [] and analyzer.stats.unknown_item_ids == 1


# ─────────────────────────────────────────────────────────────────────
# 3. الأعطال والـ Fallback
# ─────────────────────────────────────────────────────────────────────

def test_markdown_fenced_json_accepted(monkeypatch):
    _, out = run(monkeypatch, "```json\n" + json.dumps(GOOD) + "\n```")
    assert by(out, "get", DIRECT).is_flagged


def test_broken_json_retries_without_cache(monkeypatch):
    calls = fake_llm(monkeypatch, "{not json", GOOD)
    out = dsa.DocSemanticAnalyzer().analyze(cache_request())
    assert by(out, "get", DIRECT).is_flagged
    assert [c["use_cache"] for c in calls] == [True, False]     # إعادة المحاولة بتتجاوز الكاش


def test_all_attempts_fail_no_crash(monkeypatch):
    calls = fake_llm(monkeypatch, ConnectionError("network down"))
    analyzer = dsa.DocSemanticAnalyzer(max_attempts=3)
    out = analyzer.analyze(cache_request())
    assert out == [] and len(calls) == 3
    assert analyzer.stats.failed_requests == 1 and analyzer.stats.failed_classes == ["Cache"]


@pytest.mark.parametrize("raw", ["", None, "Sorry, I cannot help with that.", '{"answer": 1}'])
def test_bad_responses_count_as_failure(monkeypatch, raw):
    fake_llm(monkeypatch, raw if raw is not None else "")
    analyzer = dsa.DocSemanticAnalyzer(max_attempts=2)
    assert analyzer.analyze(cache_request()) == [] and analyzer.stats.failed_requests == 1
