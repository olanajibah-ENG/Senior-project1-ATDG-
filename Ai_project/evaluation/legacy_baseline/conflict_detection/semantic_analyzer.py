import logging
import json
import re
from typing import List, Dict, Any

from evaluation.harness.llm_recorder import LLMClient  # [snapshot] كان core_ai.ai_engine.llm_client — الشي الوحيد المعدَّل بالنسخة المجمّدة
from .schemas import ConflictItem, ChangeType, SeverityLevel
from .prompts.conflict_prompts import SEMANTIC_PROMPT

logger = logging.getLogger(__name__)
def prune_diagram(d: dict) -> dict:
    classes = sorted(d.get("classes", []), key=lambda c: c.get("name", ""))
    for cls in classes:
        methods = cls.get("methods", [])
        cls["methods"] = sorted(methods, key=lambda m: m.get("name", "") if isinstance(m, dict) else str(m))
        for field in ("relationships", "constraints", "attributes"):
            if not cls.get(field):
                cls.pop(field, None)
    return {"classes": classes, "language": d.get("language", "")}

class SemanticAnalyzer:
    def __init__(self):
        # True إذا فشلت كل المحاولات (شبكة/رد فاضي/JSON مكسور) — بيميّز الفشل التقني
        # عن حالة "الموديل ردّ صح بس ما لقى تناقض"
        self.last_call_failed = False

    def analyze(self, diagram_a: Dict[str, Any], diagram_b: Dict[str, Any], max_attempts: int = 3, use_cache: bool = True) -> List[ConflictItem]:
        """
        تحليل دلالي باستخدام LLM.

        max_attempts: عدد المحاولات قبل ما نستسلم ونرجع قائمة فاضية.
        السبب: بعض الموديلات المجانية (خصوصاً وراء راوتر زي openrouter/free)
        ممكن ترجع أحياناً رد فاضي (None)، رد رفض (Safety refusal)، أو JSON
        مكسور — هاي مش بالضرورة يعني "ما في تناقض"، هاي فشل بالاستدعاء نفسو.
        """
        prompt = SEMANTIC_PROMPT.replace("{diagram_a}", json.dumps(prune_diagram(diagram_a), ensure_ascii=False, indent=2))\
                   .replace("{diagram_b}", json.dumps(prune_diagram(diagram_b), ensure_ascii=False, indent=2))

        self.last_call_failed = False
        last_error: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                response = LLMClient.call_model(
                    system_prompt="You are a senior software architect. Respond with valid JSON only, no markdown.",
                    user_prompt=prompt,
                    temperature=0.0,
                    # على أول محاولة منسمح بالكاش (أسرع، وممكن يكون فيه رد
                    # صحيح محفوظ من قبل). على أي محاولة إعادة، لازم نعطل
                    # الكاش، وإلا رح يرجعلنا نفس الرد الفاشل يلي تخزن.
                    use_cache=(attempt == 1 and use_cache),
                )

                if not response or not isinstance(response, str) or not response.strip():
                    raise ValueError(f"Empty/None response from LLM (attempt {attempt}/{max_attempts})")

                # تنظيف الـ response من markdown
                clean = response.strip()
                clean = re.sub(r'^```(?:json)?\s*', '', clean)
                clean = re.sub(r'\s*```$', '', clean)

                match = re.search(r'\{.*\}', clean, re.DOTALL)
                if not match:
                    raise ValueError(f"No JSON found: {clean[:200]}")
                data = json.loads(match.group())

                conflicts = []
                for item in data.get("conflicts", []):
                    try:
                        change_type = ChangeType(item.get("type", "behavior_change"))
                    except ValueError:
                        change_type = ChangeType.BEHAVIOR_CHANGE

                    try:
                        severity = SeverityLevel(item.get("severity", "medium"))
                    except ValueError:
                        severity = SeverityLevel.MEDIUM

                    raw_conf = item.get("confidence", 0.85)
                    ai_confidence = raw_conf / 100.0 if raw_conf > 1.0 else float(raw_conf)

                    conflicts.append(ConflictItem(
                        type=change_type,
                        severity=severity,
                        class_name=item.get("class_name", "unknown"),
                        member=item.get("member"),
                        description=item.get("description", ""),
                        old_value=item.get("old_value"),
                        new_value=item.get("new_value"),
                        recommendation=item.get("recommendation"),
                        ai_confidence=ai_confidence
                    ))

                if attempt > 1:
                    logger.info(f"SemanticAnalyzer: نجحت المحاولة {attempt}/{max_attempts} بعد فشل سابق")
                logger.info(f"SemanticAnalyzer: {len(conflicts)} conflicts found")
                return conflicts

            except Exception as e:
                last_error = e
                logger.warning(f"SemanticAnalyzer: فشلت المحاولة {attempt}/{max_attempts} — {e}")
                continue

        logger.error(f"SemanticAnalyzer: فشلت كل المحاولات ({max_attempts}). آخر خطأ: {last_error}", exc_info=False)
        self.last_call_failed = True
        return []   # قائمة فارغة بدل ConflictItem وهمي