# core_ai/services/conflict_detection/rename_detector.py
from typing import List, Dict, Any
from .fingerprint_builder import FingerprintBuilder


class RenameDetector:
    """
    يكشف الدوال التي تغير اسمها فقط (rename) مقابل تغيير المنطق (logic change).
    يعتمد على FingerprintBuilder للمقارنة.
    """

    @staticmethod
    def detect(methods_a: List[Dict], methods_b: List[Dict]) -> Dict[str, Any]:
        renames = []
        logic_changes = []

        # بناء بصمات (fingerprints) لكل دالة
        fps_a = {FingerprintBuilder.build(m): m for m in methods_a}
        fps_b = {FingerprintBuilder.build(m): m for m in methods_b}

        # كشف Rename (بصمة متطابقة + اسم مختلف)
        for fp, method_a in fps_a.items():
            if fp in fps_b:
                method_b = fps_b[fp]
                if method_a.get("name") != method_b.get("name"):
                    renames.append({
                        "old_name": method_a.get("name"),
                        "new_name": method_b.get("name"),
                        "confidence": 0.92,
                        "class_name": method_a.get("class_name", "unknown")
                    })

        # كشف Logic Changes (نفس الاسم + بصمة مختلفة)
        for name in {m.get("name") for m in methods_a}:
            method_a = next((m for m in methods_a if m.get("name") == name), None)
            method_b = next((m for m in methods_b if m.get("name") == name), None)

            if method_a and method_b:
                fp_a = FingerprintBuilder.build(method_a)
                fp_b = FingerprintBuilder.build(method_b)

                if fp_a != fp_b:
                    logic_changes.append({
                        "method_name": name,
                        "class_name": method_a.get("class_name", "unknown"),
                        "description": "تغير المنطق داخل الدالة (signature أو behavior)",
                        "confidence": 0.88
                    })

        return {
            "renames": renames,
            "logic_changes": logic_changes
        }