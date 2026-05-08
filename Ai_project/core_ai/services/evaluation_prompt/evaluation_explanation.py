from typing import Dict, Any
from datetime import datetime
from bson import ObjectId
import logging

from core_ai.mongo_utils import get_mongo_db
from .llm_judge_exp import LLMExplanationJudge

logger = logging.getLogger(__name__)

class ExplanationEvaluator:
    """نظام تقييم 4 طبقات محسن"""

    def __init__(self):
        self.db = get_mongo_db()

    def evaluate(self, explanation_id: str, force_reevaluate: bool = False) -> Dict[str, Any]:
        logger.info(f"[Evaluation] Starting evaluation for {explanation_id}")
        
        explanation, analysis = self._load_data(explanation_id)
        logger.info(f"[Evaluation] Data loaded successfully")

        layer1 = self._layer1_factual_accuracy(explanation, analysis)
        logger.info(f"[Evaluation] Layer1 completed: {layer1}")
        
        layer2 = self._layer2_completeness(explanation, analysis)
        logger.info(f"[Evaluation] Layer2 completed: {layer2}")
        
        layer3 = self._layer3_llm_judge(explanation, analysis)
        logger.info(f"[Evaluation] Layer3 completed: {layer3}")
        
        layer4 = self._layer4_human_review(explanation)
        logger.info(f"[Evaluation] Layer4 completed: {layer4}")

        final_score = self._calculate_final_score(layer1, layer2, layer3, layer4)
        logger.info(f"[Evaluation] Final score calculated: {final_score}")

        result = {
            "explanation_id": str(explanation_id),
            "exp_type": explanation.get("exp_type"),
            "is_project": explanation.get("is_project", False),
            "final_score": round(final_score, 3),
            "final_percentage": round(final_score * 100, 1),
            "verdict": self._get_verdict(final_score),
            "layer1": layer1,
            "layer2": layer2,
            "layer3": layer3,
            "layer4": layer4,
            "evaluated_at": datetime.utcnow()
        }

        self._save_evaluation(result)
        return result
    
    def _load_data(self, explanation_id: str):
        explanation = self.db["ai_explanations"].find_one({"_id": ObjectId(explanation_id)})
        analysis = self.db["analysis_results"].find_one({"_id": ObjectId(explanation["analysis_id"])})
        return explanation, analysis

    def _layer1_factual_accuracy(self, explanation, analysis):
        text = explanation.get("content", "").lower()
        summary = self._build_summary(analysis)
        
        # Ensure we have lists to work with
        classes = summary.get("classes", [])
        methods = summary.get("methods", [])
        
        if not isinstance(classes, list):
            classes = []
        if not isinstance(methods, list):
            methods = []
        
        total = len(classes) + len(methods)
        verified = sum(1 for c in classes if isinstance(c, str) and c.lower() in text) + \
                   sum(1 for m in methods if isinstance(m, str) and m.lower() in text)
        score = verified / total if total > 0 else 0.65
        return {"score": round(score, 3), "verified": verified, "total": total}

    def _layer2_completeness(self, explanation, analysis):
        text = explanation.get("content", "").lower()
        summary = self._build_summary(analysis)
        
        # Ensure we have lists to work with
        classes = summary.get("classes", [])
        methods = summary.get("methods", [])
        
        if not isinstance(classes, list):
            classes = []
        if not isinstance(methods, list):
            methods = []
        
        covered = sum(1 for c in classes if isinstance(c, str) and c.lower() in text) + \
                  sum(1 for m in methods if isinstance(m, str) and m.lower() in text)
        total = len(classes) + len(methods) + 1
        return {"score": round(covered / total, 3)}

    def _layer3_llm_judge(self, explanation, analysis):
        context = self._build_summary(analysis)
        context["exp_type"] = explanation.get("exp_type")
        context["is_project"] = explanation.get("is_project", False)
        logger.info(f"[Evaluation] Context for LLM: {context}")
        logger.info(f"[Evaluation] Explanation content length: {len(explanation.get('content', ''))}")
        return LLMExplanationJudge.evaluate(explanation.get("content", ""), context)

    def _layer4_human_review(self, explanation):
        feedbacks = list(self.db["human_feedback"].find({"explanation_id": str(explanation.get("_id"))}))
        if not feedbacks:
            return {"human_score": None, "count": 0}
        
        scores = [f.get("score") for f in feedbacks if f.get("score") is not None]
        avg = sum(scores) / len(scores) if scores else None
        return {"human_score": avg, "count": len(feedbacks)}

    def _build_summary(self, analysis):
        features = analysis.get("extracted_features", {})
        classes = analysis.get("class_diagram_data", {}).get("classes", [])
        
        # Ensure classes is a list
        if not isinstance(classes, list):
            classes = []
        
        # Extract class names safely
        class_names = [c.get("name") for c in classes if isinstance(c, dict) and c.get("name")]
        
        # Get methods safely - ensure it's a list
        methods = features.get("function_names", []) or features.get("methods", [])
        if not isinstance(methods, list):
            methods = []
        
        # Get routes safely - ensure it's a list
        routes = features.get("routes", [])
        if not isinstance(routes, list):
            routes = []
        
        return {
            "classes": class_names,
            "methods": methods,
            "routes": routes,
            "lines_of_code": features.get("lines_of_code", 0)
        }

    def _calculate_final_score(self, l1, l2, l3, l4):
        human = l4["human_score"]
        if human is not None:
            return (l1["score"] * 0.30) + (l2["score"] * 0.20) + (l3.get("overall_score", 0.6) * 0.30) + (human * 0.20)
        return (l1["score"] * 0.35) + (l2["score"] * 0.25) + (l3.get("overall_score", 0.6) * 0.40)

    def _get_verdict(self, score: float) -> str:
        if score >= 0.85: return "EXCELLENT"
        elif score >= 0.70: return "GOOD"
        elif score >= 0.55: return "ACCEPTABLE"
        return "NEEDS_IMPROVEMENT"

    def _save_evaluation(self, result):
        self.db["explanation_evaluations"].insert_one(result)