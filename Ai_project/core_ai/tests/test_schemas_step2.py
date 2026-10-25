"""
اختبارات الخطوة 2: إصلاح category، نوع RENAMED، والحقول الجديدة بـ ConflictItem.

    python -m pytest core_ai/tests/test_schemas_step2.py -q
"""
from core_ai.services.conflict_detection import orchestrator as orch
from core_ai.services.conflict_detection.ast_unifier import ASTUnifier
from core_ai.services.conflict_detection.schemas import (
    ChangeDecision, ChangeType, ConflictItem, DocConsistencyLabel, RiskLevel, SeverityLevel,
)
from core_ai.services.conflict_detection.semantic_analyzer import SemanticAnalyzer
from core_ai.services.conflict_detection.structural_diff import StructuralDiff


def diagram(classes):
    return ASTUnifier.from_tree_sitter({"class_diagram_data": {"classes": classes}})


def cls(name, methods=(), attributes=()):
    return {"name": name,
            "methods": [{"name": n, "signature": s} for n, s in methods],
            "attributes": [{"name": a, "type": t} for a, t in attributes]}


# ─────────────────────────────────────────────────────────────────────
# 1. إصلاح category: أي تغيير هيكلي كان يوقّع المسار
# ─────────────────────────────────────────────────────────────────────

def test_method_removed_no_longer_crashes():
    a = diagram([cls("A", [("a", "a(): int"), ("b", "b(x: str): str")])])
    b = diagram([cls("A", [("a", "a(): int")])])
    conflicts = StructuralDiff.compare(a, b)   # قبل: ValidationError
    removed = [c for c in conflicts if c.category == "method_removed"]
    assert removed and removed[0].member == "b"


def test_every_structural_pattern_runs():
    a = diagram([
        cls("Keep", [("run", "run(x: int): int"), ("old", "old(): void")], [("size", "int"), ("gone", "str")]),
        cls("Removed", [("f", "f(): void")]),
    ])
    b = diagram([
        cls("Keep", [("run", "run(x: int, y: int): int"), ("fresh", "fresh(a: str, b: str): bool")],
            [("size", "long"), ("extra", "str")]),
        cls("Added", [("g", "g(): void")]),
    ])
    categories = {c.category for c in StructuralDiff.compare(a, b)}
    for expected in ("class_removed", "class_added", "method_removed", "method_added",
                     "method_signature_changed", "attribute_removed", "attribute_added",
                     "attribute_type_changed"):
        assert expected in categories, expected


def test_full_code_vs_code_pipeline_succeeds(monkeypatch):
    monkeypatch.setattr(SemanticAnalyzer, "analyze", lambda self, a, b, **k: [])   # بدون شبكة
    a = {"_id": "v1", "class_diagram_data": {"classes": [cls("A", [("a", "a(): int"), ("b", "b(): int")])]}}
    b = {"_id": "v2", "class_diagram_data": {"classes": [cls("A", [("a", "a(): int")])]}}
    result = orch.ConflictOrchestrator.run_code_vs_code(a, b)
    assert result.status == "success"
    assert any(c.category == "method_removed" for c in result.structural_conflicts)


# ─────────────────────────────────────────────────────────────────────
# 2. RENAMED
# ─────────────────────────────────────────────────────────────────────

def test_rename_detector_now_reports_renamed_type():
    a = diagram([cls("A", [("fetch_user", "fetch_user(uid: int): User")])])
    b = diagram([cls("A", [("get_user", "get_user(uid: int): User")])])
    types = {c.type for c in StructuralDiff.compare(a, b)}
    assert ChangeType.RENAMED in types
    assert ChangeType.BEHAVIOR_CHANGE not in types     # قبل: إعادة التسمية كانت تنحسب behavior_change


# ─────────────────────────────────────────────────────────────────────
# 3. الحقول الجديدة + التوافق مع التقارير القديمة
# ─────────────────────────────────────────────────────────────────────

OLD_REPORT_ITEM = {
    "type": "documentation_drift", "severity": "medium", "class_name": "Repo", "member": "get",
    "description": "...", "ai_confidence": 0.8, "doc_type": "low", "category": None,
}


def test_old_stored_item_still_loads():
    item = ConflictItem.model_validate(OLD_REPORT_ITEM)
    assert item.doc_label is None and item.is_flagged is None and item.evidence is None
    assert item.decision is None and item.risk_level is None


def test_old_category_values_still_accepted():
    assert ConflictItem.model_validate({**OLD_REPORT_ITEM, "category": "syntactic"}).category == "syntactic"


def test_new_fields_roundtrip_as_plain_strings():
    item = ConflictItem(
        type=ChangeType.DOC_DRIFT, severity=SeverityLevel.HIGH, class_name="Repo", member="get",
        description="doc says raises KeyError, code returns None",
        ai_confidence=0.9,
        doc_label=DocConsistencyLabel.DIRECT_MISMATCH, is_flagged=True,
        evidence="doc: 'Raises KeyError' | code: 'return self.store.get(uid)'",
        decision=ChangeDecision.BEHAVIORAL_CANDIDATE, risk_level=RiskLevel.CRITICAL,
    )
    dumped = item.model_dump(mode="json")
    assert dumped["doc_label"] == "Direct_Mismatch"
    assert dumped["decision"] == "behavioral_candidate"
    assert dumped["risk_level"] == "critical"
    assert ConflictItem.model_validate(dumped) == item


def test_severity_values_unchanged_for_frontend():
    # الواجهة بتلوّن حسب هالقيم بالزبط — ممنوع تتغيّر
    assert [s.value for s in SeverityLevel] == ["critical", "high", "medium", "low", "info"]


def test_docprism_labels_match_labeling_guide():
    assert {l.value for l in DocConsistencyLabel} == {
        "Consistent", "Direct_Mismatch", "Over_Promise", "Under_Promise"}
