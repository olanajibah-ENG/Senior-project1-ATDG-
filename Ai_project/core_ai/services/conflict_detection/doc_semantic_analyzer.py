# core_ai/services/conflict_detection/doc_semantic_analyzer.py
"""
DocSemanticAnalyzer — الخطوة 5: إرسال طلبات الكود مقابل التوثيق للـ LLM، قراءة الجواب، والفلترة.

منهجية DocPrism (LCEF):
  Local Categorization  — الطلب (الخطوة 4): كل دالة مع توثيقها هي بس، 3 أسئلة.
  External Filtering    — هون، بالبرمجة بعد جواب الموديل:
    1. Under_Promise بينحفظ بس ما بينعرض (is_flagged=False).
    2. الجملة المنسوخة من التوثيق لازم تكون موجودة فعلاً بتوثيق البند، وإلا بتنرمى (اختراع).
    3. السطر المنسوخ من الكود وأرقام الأسطر لازم يكونوا من الكود يلي انعرض، وإلا بتنرمى.
    4. عتبة ثقة (METAMON): تحت العتبة بينحفظ بس ما بينعرض.
    5. نتيجة وحدة لكل (بند، تصنيف) — الأعلى ثقة.

Fallback: إذا فشلت كل محاولات طلب (شبكة / رد فاضي / JSON مكسور)، الكلاس بينسجّل إنه ما انفحص
دلالياً، والنظام بيكمّل (الفحوصات الحتمية القديمة بتضل شغّالة) — ما في crash.
"""
import json
import logging
import re
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from core_ai.ai_engine.llm_client import LLMClient
from .doc_prompt_builder import CodeDocItem, CodeDocRequest
from .schemas import ChangeType, ConflictItem, DocConsistencyLabel, DocType, SeverityLevel

logger = logging.getLogger(__name__)

DEFAULT_THRESHOLD = 0.7

# سؤال الـ prompt ← (تصنيف DocPrism، الخطورة يلي بتلوّن فيها الواجهة)
_QUESTIONS = {
    "conflicting":     (DocConsistencyLabel.DIRECT_MISMATCH, SeverityLevel.HIGH),
    "not_implemented": (DocConsistencyLabel.OVER_PROMISE,    SeverityLevel.MEDIUM),
    "undocumented":    (DocConsistencyLabel.UNDER_PROMISE,   SeverityLevel.LOW),
}


class DocAnalysisStats(BaseModel):
    requests:            int = 0
    failed_requests:     int = 0
    failed_classes:      List[str] = Field(default_factory=list)
    findings:            int = 0      # كل يلي رجّعه الموديل
    dropped_doc_quote:   int = 0      # الجملة مش موجودة بالتوثيق
    dropped_code_quote:  int = 0      # السطر/الأسطر مش من الكود المعروض
    duplicates:          int = 0
    under_promise:       int = 0      # محفوظة بس مش معروضة
    below_threshold:     int = 0      # محفوظة بس مش معروضة
    flagged:             int = 0      # يلي بتوصل للمستخدم
    unknown_item_ids:    int = 0


# ─────────────────────────────────────────────────────────────────────
# مطابقة النص المنسوخ
# ─────────────────────────────────────────────────────────────────────

def _norm(text: str) -> str:
    text = re.sub(r"[*`]", "", text or "")
    return re.sub(r"\s+", " ", text).strip().lower()


def quote_found(quote: str, source: str) -> bool:
    """النسخ لازم يكون حرفي — مع تساهل بالمسافات، علامات markdown، وحالة الأحرف.
    إذا الموديل اختصر بـ '...'، كل قطعة لازم تكون موجودة."""
    src = _norm(source)
    parts = [p for p in (_norm(x) for x in re.split(r"\.\.\.|…", quote or "")) if p]
    return bool(parts) and all(p in src for p in parts)


def _strip_line_numbers(snippet: str) -> str:
    """أحياناً الموديل بينسخ 'NN | code' متل ما انعرض"""
    return "\n".join(re.sub(r"^\s*\d+\s*\|\s?", "", l) for l in (snippet or "").splitlines())


def code_quote_ok(snippet: Optional[str], lines: Optional[list], item: CodeDocItem) -> bool:
    if not item.code_lines:                       # بند الكلاس: ما في كود
        return True
    if lines:
        try:
            if any(int(n) not in item.code_lines for n in lines):
                return False
        except (TypeError, ValueError):
            return False
    if snippet:
        return quote_found(_strip_line_numbers(snippet), "\n".join(item.code_lines.values()))
    return True


# ─────────────────────────────────────────────────────────────────────
# قراءة الجواب
# ─────────────────────────────────────────────────────────────────────

def parse_response(raw: Optional[str]) -> Dict:
    if not raw or not isinstance(raw, str) or not raw.strip():
        raise ValueError("empty response")
    clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
    match = re.search(r"\{.*\}", clean, re.DOTALL)
    if not match:
        raise ValueError(f"no JSON object in response: {clean[:120]}")
    data = json.loads(match.group())
    if not isinstance(data.get("results"), list):
        raise ValueError("JSON has no 'results' list")
    return data


def _confidence(value) -> float:
    try:
        c = float(value)
    except (TypeError, ValueError):
        return 0.5
    return c / 100.0 if c > 1.0 else max(0.0, min(c, 1.0))


class DocSemanticAnalyzer:
    def __init__(self, threshold: float = DEFAULT_THRESHOLD, max_attempts: int = 3):
        self.threshold = threshold
        self.max_attempts = max_attempts
        self.stats = DocAnalysisStats()

    # ─────────────────────────────────────────────────────────────────
    def analyze(self, requests: List[CodeDocRequest],
                doc_type: Optional[DocType] = None) -> List[ConflictItem]:
        best: Dict[Tuple[str, str], ConflictItem] = {}
        for req in requests:
            self.stats.requests += 1
            data = self._call(req)
            if data is None:
                self.stats.failed_requests += 1
                self.stats.failed_classes.append(req.class_name)
                continue
            items = {i.id: i for i in req.items}
            for result in data["results"]:
                item = items.get(str(result.get("id", "")))
                if item is None:
                    self.stats.unknown_item_ids += 1
                    continue
                for conflict in self._findings(result, item, doc_type):
                    key = (item.id, conflict.doc_label)
                    if key in best:
                        self.stats.duplicates += 1
                        if conflict.ai_confidence <= best[key].ai_confidence:
                            continue
                    best[key] = conflict

        out = list(best.values())
        self.stats.under_promise = sum(c.doc_label == DocConsistencyLabel.UNDER_PROMISE for c in out)
        self.stats.below_threshold = sum(c.doc_label != DocConsistencyLabel.UNDER_PROMISE
                                         and c.ai_confidence < self.threshold for c in out)
        self.stats.flagged = sum(bool(c.is_flagged) for c in out)
        return out

    # ─────────────────────────────────────────────────────────────────
    def _call(self, req: CodeDocRequest) -> Optional[Dict]:
        for attempt in range(1, self.max_attempts + 1):
            try:
                raw = LLMClient.call_model(
                    system_prompt=req.system, user_prompt=req.user, temperature=0.0,
                    # إعادة المحاولة لازم تتجاوز الكاش، وإلا بيرجع نفس الرد الفاشل
                    use_cache=(attempt == 1),
                )
                return parse_response(raw)
            except Exception as e:
                logger.warning(f"DocSemanticAnalyzer: {req.class_name} attempt {attempt}/{self.max_attempts} failed — {e}")
        logger.error(f"DocSemanticAnalyzer: {req.class_name} — all attempts failed; falling back to deterministic checks")
        return None

    def _findings(self, result: Dict, item: CodeDocItem, doc_type: Optional[DocType]) -> List[ConflictItem]:
        out = []
        for question, (label, severity) in _QUESTIONS.items():
            for f in result.get(question) or []:
                if not isinstance(f, dict):
                    continue
                self.stats.findings += 1
                doc_snippet, code_snippet = f.get("doc_snippet"), f.get("code_snippet")
                lines = f.get("code_lines") or []
                if not isinstance(lines, list):
                    lines = [lines]
                lines = [n for n in lines if n not in (0, "0", None)]   # 0 = قيمة القالب، مش سطر

                # (2) الجملة من التوثيق — لازمة لـ Direct و Over
                if label != DocConsistencyLabel.UNDER_PROMISE:
                    if not doc_snippet or not quote_found(doc_snippet, item.doc_text):
                        self.stats.dropped_doc_quote += 1
                        continue
                # (3) السطر من الكود — لازم لـ Direct و Under (Over ما إله كود بالتعريف)
                if label != DocConsistencyLabel.OVER_PROMISE and not code_quote_ok(code_snippet, lines, item):
                    self.stats.dropped_code_quote += 1
                    continue

                confidence = _confidence(f.get("confidence"))
                flagged = label != DocConsistencyLabel.UNDER_PROMISE and confidence >= self.threshold
                evidence = " | ".join(x for x in (
                    f'doc: "{doc_snippet}"' if doc_snippet else "",
                    f"code L{','.join(map(str, lines))}: \"{code_snippet}\"" if code_snippet else "") if x)
                out.append(ConflictItem(
                    type=ChangeType.DOC_DRIFT,
                    severity=severity,
                    category=label.value.lower(),
                    class_name=item.class_name,
                    member=item.member,
                    line_number=int(lines[0]) if lines and str(lines[0]).isdigit() else None,
                    description=f.get("explanation") or f"{label.value}: {doc_snippet or code_snippet}",
                    doc_value=doc_snippet,
                    code_value=code_snippet,
                    recommendation="حدّث التوثيق أو الكود لحتى يتطابقوا" if label != DocConsistencyLabel.UNDER_PROMISE
                                   else "وثّق هالسلوك إذا المستدعي لازم يعرفه",
                    doc_type=doc_type,
                    ai_confidence=confidence,
                    doc_label=label,
                    is_flagged=flagged,
                    evidence=evidence or None,
                ))
        return out
