"""
Auto-trigger evaluation system for AI explanations
Automatically evaluates explanations when they are generated
"""

from threading import Thread
import logging

logger = logging.getLogger(__name__)


def trigger_evaluation_background(explanation_id: str):
    """
    Trigger evaluation in a background daemon thread.
    Call this function immediately after saving an explanation to MongoDB.

    Args:
        explanation_id: MongoDB _id of saved explanation (as string)
    """
    def _run():
        try:
            from core_ai.services.evaluation_service import ExplanationEvaluator
            evaluator = ExplanationEvaluator()
            evaluator.evaluate_explanation(explanation_id)
            logger.info(f"[AUTO-EVAL] Completed for explanation {explanation_id}")
        except Exception as e:
            logger.error(f"[AUTO-EVAL] Failed for explanation {explanation_id}: {str(e)}")

    thread = Thread(target=_run, daemon=True)
    thread.start()


class EvaluationTrigger:
    """Manual trigger for evaluations"""

    @staticmethod
    def trigger_evaluation(explanation_id: str) -> dict:
        from core_ai.services.evaluation_service import ExplanationEvaluator
        evaluator = ExplanationEvaluator()
        return evaluator.evaluate_explanation(explanation_id)

    @staticmethod
    def batch_evaluate(explanation_ids: list) -> list:
        results = []
        for explanation_id in explanation_ids:
            try:
                result = EvaluationTrigger.trigger_evaluation(explanation_id)
                results.append({
                    "explanation_id": explanation_id,
                    "status": "success",
                    "result": result
                })
            except Exception as e:
                results.append({
                    "explanation_id": explanation_id,
                    "status": "error",
                    "error": str(e)
                })
        return results
