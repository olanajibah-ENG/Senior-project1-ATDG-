import pytest


@pytest.fixture(autouse=True)
def _no_real_llm_in_tests(monkeypatch):
    """الاختبارات ما بتستدعي الـ LLM الحقيقي. يلي بدو يختبر التحليل الدلالي بيمرّر use_llm=True
    مع أجوبة مكتوبة بإيده (monkeypatch لـ LLMClient.call_model)."""
    monkeypatch.setenv("CODE_DOC_LLM_ENABLED", "0")
