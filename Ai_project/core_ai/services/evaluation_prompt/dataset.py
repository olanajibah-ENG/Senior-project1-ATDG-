# core_ai/ai_engine/dataset.py
from typing import List, Dict
from core_ai.mongo_utils import get_mongo_db

class EvaluationDataset:

    @staticmethod
    def get_manual_cases() -> List[Dict]:
        """12 حالة أولية يدوية"""
        return [
            {"id": "manual_001", "exp_type": "high_level", "is_project": False, "note": "Simple User Model"},
            {"id": "manual_002", "exp_type": "low_level",  "is_project": False, "note": "Service with business logic"},
            {"id": "manual_003", "exp_type": "low_level",  "is_project": False, "note": "Complex logic + error handling"},
            {"id": "manual_004", "exp_type": "high_level", "is_project": True,  "note": "Small Project"},
            {"id": "manual_005", "exp_type": "low_level",  "is_project": True,  "note": "Project with inheritance"},
            # أكمل الباقي حسب الحاجة
        ]

    @staticmethod
    def get_auto_from_db(limit: int = 20):
        db = get_mongo_db()
        return list(db["ai_explanations"].aggregate([
            {"$sample": {"size": limit}},
            {"$project": {"_id": 1, "exp_type": 1, "content": 1, "is_project": 1}}
        ]))