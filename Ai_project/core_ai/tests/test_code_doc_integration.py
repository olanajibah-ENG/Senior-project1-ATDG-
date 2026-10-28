"""
اختبارات الخطوة 6: ربط التحليل الدلالي بـ CodeDocConsistencyChecker.compare.
الـ LLM مزيّف (أجوبة مكتوبة بإيدنا).

    python -m pytest core_ai/tests/test_code_doc_integration.py -q
"""
import json

from core_ai.services.conflict_detection import doc_semantic_analyzer as dsa
from core_ai.services.conflict_detection.code_doc_consistency import CodeDocConsistencyChecker
from core_ai.services.conflict_detection.orchestrator import ConflictOrchestrator
from core_ai.services.conflict_detection.schemas import DocConsistencyLabel
from core_ai.tests.test_doc_prompt_builder import CODE, DOC, diagram
from core_ai.tests.test_doc_semantic_analyzer import GOOD, fake_llm

EXPLANATION = {"content": DOC, "explanation_type": "low_level"}


def overall(out):
    return next(c for c in out if c.class_name == "Overall").element


def shown(out):
    return [c for c in out if c.class_name != "Overall"]


# ─────────────────────────────────────────────────────────────────────
# 1. التحليل الدلالي جوا compare
# ─────────────────────────────────────────────────────────────────────

def test_contradictions_come_from_semantic_analysis(monkeypatch):
    fake_llm(monkeypatch, GOOD, {"results": []})                 # طلب Cache، بعدين طلب <module>
    out = CodeDocConsistencyChecker.compare(diagram(CODE), EXPLANATION, use_llm=True)
    labels = sorted((c.member or c.class_name, c.doc_label.value) for c in shown(out))
    assert labels == [("Cache", "Over_Promise"), ("get", "Direct_Mismatch"), ("put", "Over_Promise")]
    assert all(c.is_flagged for c in shown(out))
    stats = overall(out)
    assert stats["contradictions"] == 3
    assert stats["semantic_analysis"]["flagged"] == 3 and stats["semantic_analysis"]["requests"] == 2
    assert stats["hidden_findings"] == [{"class": "Cache", "member": "get", "label": "Under_Promise",
                                         "confidence": 0.9}]


def test_undocumented_is_coverage_not_alert(monkeypatch):
    fake_llm(monkeypatch, {"results": []})
    out = CodeDocConsistencyChecker.compare(diagram(CODE), EXPLANATION, use_llm=True)
    assert shown(out) == []                                         # ولا "غير موثّق" بقائمة المشاكل
    assert {"class": "Cache", "method": "make"} in overall(out)["undocumented_methods"]


def test_original_code_lines_sent_when_available(monkeypatch):
    seen = []
    def call_model(system_prompt, user_prompt, **kw):
        seen.append(user_prompt)
        return json.dumps({"results": []})
    monkeypatch.setattr(dsa.LLMClient, "call_model", staticmethod(call_model))
    code = CODE.strip() + "\n"
    CodeDocConsistencyChecker.compare(diagram(code), {**EXPLANATION, "code_content": code}, use_llm=True)
    assert "   4 |     def get(self, key: str, default=None):" in seen[0]


# ─────────────────────────────────────────────────────────────────────
# 2. التشغيل والإيقاف
# ─────────────────────────────────────────────────────────────────────

def test_llm_disabled_makes_no_calls(monkeypatch):
    calls = fake_llm(monkeypatch, AssertionError("LLM must not be called"))
    out = CodeDocConsistencyChecker.compare(diagram(CODE), EXPLANATION, use_llm=False)
    assert calls == [] and overall(out)["semantic_analysis"] is None


def test_env_switch_and_threshold(monkeypatch):
    low = {"results": [{"id": "Cache.put", "not_implemented": [
        {"doc_snippet": "Stores the value for ttl seconds.", "confidence": 0.6}]}]}
    fake_llm(monkeypatch, low, {"results": []})
    monkeypatch.setenv("CODE_DOC_LLM_ENABLED", "1")
    monkeypatch.setenv("CODE_DOC_CONFIDENCE_THRESHOLD", "0.5")
    out = CodeDocConsistencyChecker.compare(diagram(CODE), EXPLANATION)
    assert [c.member for c in shown(out)] == ["put"]               # 0.6 ≥ 0.5 → معروض


# ─────────────────────────────────────────────────────────────────────
# 3. يلي انشال، ويلي ضل
# ─────────────────────────────────────────────────────────────────────

def test_old_signature_regex_check_removed():
    # المثال بالتوثيق فيه فواصل جوا القوس — الفحص القديم كان يعدّ 4 معاملات بدل 2
    code = "def cast(arr, dtype):\n    return arr\n"
    doc = "### Function: cast\nCast an array.\n>>> cast([1, 2, 3.5], dtype='int64')\n"
    out = CodeDocConsistencyChecker.compare(diagram(code), {"content": doc}, use_llm=False)
    assert shown(out) == []


def test_structured_deterministic_check_still_works_and_survives_llm_failure(monkeypatch):
    fake_llm(monkeypatch, ConnectionError("network down"))
    code = "class Repo:\n    def get(self, uid: int) -> Optional[dict]:\n        return self.d.get(uid)\n"
    doc = {"Repo.get": {"signature": "get(self, uid: int) -> dict", "description": "Get user.",
                        "raises": ["KeyError"]}}
    out = CodeDocConsistencyChecker.compare(diagram(code), doc, use_llm=True)
    found = shown(out)
    assert len(found) == 1 and "raises KeyError vs returns None" in found[0].description
    assert found[0].doc_label == DocConsistencyLabel.DIRECT_MISMATCH and found[0].is_flagged
    assert overall(out)["semantic_analysis"]["failed_classes"] == ["Repo"]     # ما في crash


def test_java_diagram_signature_now_parsed():
    sig = CodeDocConsistencyChecker._parse_signature("+ setAvailable(available: boolean): void")
    assert sig == (["available"], "void")
    assert CodeDocConsistencyChecker._parse_signature("scale(k: float): Any") == (["k"], "Any")


def test_unknown_python_return_type_not_compared():
    # "Any" بالمخطط = نوع مستنتج غير معروف → ما منقارنه بالتوثيق
    code = "class A:\n    def f(self, x):\n        return x\n"
    doc = {"A.f": {"signature": "f(self, x) -> int", "description": "Returns x."}}
    out = CodeDocConsistencyChecker.compare(diagram(code), doc, use_llm=False)
    assert shown(out) == []


# ─────────────────────────────────────────────────────────────────────
# 4. المسار الكامل
# ─────────────────────────────────────────────────────────────────────

def test_orchestrator_report(monkeypatch):
    fake_llm(monkeypatch, GOOD, {"results": []})
    monkeypatch.setenv("CODE_DOC_LLM_ENABLED", "1")
    from core_ai.language_processors.python_processor import PythonProcessor
    p = PythonProcessor(); a = p.parse_source_code(CODE)
    analysis = {"_id": "v1", "class_diagram_data": p.generate_class_diagram_data(a, p.extract_features(a)),
                "extracted_features": {"language": "python"}}
    report = ConflictOrchestrator.run_code_vs_doc(analysis, EXPLANATION)
    assert report.status == "success"
    assert sum(c.doc_label is not None for c in report.doc_conflicts) == 3
    assert report.compatibility_score is not None
