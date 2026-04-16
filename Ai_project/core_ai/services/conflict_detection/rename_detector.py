from typing import List, Dict, Any
from .fingerprint_builder import FingerprintBuilder

class RenameDetector:
    """
    يكشف الدوال اللي تغير اسمها فقط (rename) مقابل اللي تغير منطقها
    """

    @staticmethod
    def detect(methods_a: List[Dict], methods_b: List[Dict]) -> Dict[str, Any]:
        renames = []
        logic_changes = []

        fp_a = {FingerprintBuilder.build(m)["signature"]: m for m in methods_a}
        fp_b = {FingerprintBuilder.build(m)["signature"]: m for m in methods_b}

        # كشف rename
        for sig, method_a in fp_a.items():
            if sig in fp_b:
                method_b = fp_b[sig]
                if method_a["name"] != method_b["name"]:
                    renames.append({
                        "old_name": method_a["name"],
                        "new_name": method_b["name"],
                        "confidence": 0.9
                    })

        return {
            "renames": renames,
            "logic_changes": logic_changes
        }