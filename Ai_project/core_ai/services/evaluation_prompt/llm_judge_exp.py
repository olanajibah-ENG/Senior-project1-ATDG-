# core_ai/ai_engine/llm_judge.py
import json
import re
from pathlib import Path
from typing import Dict, Any
import logging

from core_ai.ai_engine.llm_client import LLMClient

logger = logging.getLogger(__name__)

class LLMExplanationJudge:
    """Layer 3: LLM-as-a-Judge"""

    PROMPT_PATH = Path("core_ai/services/evaluation_prompt/prompts/judge_explanation.txt")
    
    # موديل قوي مجاني مخصص للتقييم
    JUDGE_MODEL = "meta-llama/llama-3.3-70b-instruct:free"

    @staticmethod
    def load_prompt() -> str:
        try:
            return LLMExplanationJudge.PROMPT_PATH.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to load judge prompt: {e}")
            return "Evaluate the code explanation and return valid JSON only."

    @staticmethod
    def evaluate(explanation: str, context: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[LLM Judge] Starting evaluation")
        
        prompt_template = LLMExplanationJudge.load_prompt()
        logger.info(f"[LLM Judge] Prompt loaded successfully")

        try:
            user_prompt = prompt_template.format(
                exp_type=context.get("exp_type", "unknown"),
                is_project=context.get("is_project", False),
                classes=", ".join(context.get("classes", [])),
                methods=", ".join(context.get("methods", [])[:15]),
                routes=context.get("routes", []),
                loc=context.get("lines_of_code", context.get("loc", "N/A")),
                explanation=explanation[:9000]
            )
            logger.info(f"[LLM Judge] User prompt formatted, length: {len(user_prompt)}")
        except Exception as e:
            logger.error(f"[LLM Judge] Prompt formatting error: {e}")
            logger.error(f"[LLM Judge] Context: {context}")
            template_keys = re.findall(r'\{([^}]+)\}', prompt_template)
            logger.error(f"[LLM Judge] Available keys in template: {template_keys}")
            raise

        logger.info(f"[LLM Judge] About to call LLM client...")

        result = None
        try:
            result = LLMClient.call_model(
                system_prompt="You are a strict, fair, and highly accurate technical documentation evaluator. Return only valid JSON.",
                user_prompt=user_prompt,
                model=LLMExplanationJudge.JUDGE_MODEL
            )

            logger.info(f"[LLM Judge] Raw response: {result[:500]}...")

            start = result.find("{")
            end = result.rfind("}") + 1
            if start != -1 and end > start:
                json_str = result[start:end]
                logger.info(f"[LLM Judge] Extracted JSON: {json_str}")
                parsed = json.loads(json_str)
                return parsed
            else:
                logger.error(f"[LLM Judge] No valid JSON found in response: {result}")

        except json.JSONDecodeError as e:
            logger.error(f"[LLM Judge] JSON decode error: {e}")
            if result:
                logger.error(f"[LLM Judge] Response that failed: {result}")
        except Exception as e:
            logger.error(f"[LLM Judge] General error: {e}")
            if result:
                logger.error(f"[LLM Judge] Response: {result}")

        return {
            "structure_adherence": 6.0, "factual_accuracy": 5.5,
            "logic_flow_quality": 6.0, "completeness": 6.5,
            "clarity": 7.0, "overall_score": 6.2,
            "strengths": [], "weaknesses": ["Judge fallback mode"],
            "detailed_feedback": "LLM evaluation failed",
            "suggestions_for_prompt": "Improve main agent prompt"
        }