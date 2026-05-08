
import logging
import json
import re
from typing import List, Dict, Any

from core_ai.ai_engine.llm_client import LLMClient
from .schemas import ConflictItem, ChangeType, SeverityLevel
from .prompts.conflict_prompts import SEMANTIC_PROMPT

logger = logging.getLogger(__name__)


class SemanticAnalyzer:
    def __init__(self):
        pass  # LLMClient uses static methods only

    def analyze(self, diagram_a: Dict[str, Any], diagram_b: Dict[str, Any]) -> List[ConflictItem]:
        """تحليل دلالي باستخدام LLM"""
        try:
            prompt = SEMANTIC_PROMPT.format(
                diagram_a=str(diagram_a),
                diagram_b=str(diagram_b)
            )

            response = LLMClient.call_model(
                system_prompt="You are a senior software architect. Respond with valid JSON only, no markdown.",
                user_prompt=prompt
            )

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

                conflicts.append(ConflictItem(
                    type=change_type,
                    severity=severity,
                    class_name=item.get("class_name", "unknown"),
                    member=item.get("member"),
                    description=item.get("description", ""),
                    old_value=item.get("old_value"),
                    new_value=item.get("new_value"),
                    recommendation=item.get("recommendation"),
                    ai_confidence=item.get("confidence", 0.85)
                ))

            logger.info(f"SemanticAnalyzer: {len(conflicts)} conflicts found")
            return conflicts

        except Exception as e:
            logger.error(f"SemanticAnalyzer error: {e}", exc_info=True)
            return [ConflictItem(
                type=ChangeType.BEHAVIOR_CHANGE,
                severity=SeverityLevel.MEDIUM,
                class_name="unknown",
                description="فشل التحليل الدلالي - يرجى التحقق يدوياً",
                recommendation="يرجى التحقق من الـ LLM أو الـ prompt",
                ai_confidence=0.4
            )]