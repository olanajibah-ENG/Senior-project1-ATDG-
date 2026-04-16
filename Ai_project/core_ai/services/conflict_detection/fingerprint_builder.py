from typing import Dict, Any

class FingerprintBuilder:
    """
    يبني بصمة (fingerprint) لكل دالة لكشف الـ rename vs logic change
    """

    @staticmethod
    def build(method: Dict[str, Any]) -> Dict[str, Any]:
        """
        يرجع بصمة تحتوي على معلومات دلالية عن الدالة
        """
        return {
            "name": method.get("name"),
            "signature": method.get("signature"),
            "param_count": len(method.get("signature", "").split(",")) if method.get("signature") else 0,
            "is_abstract": method.get("is_abstract", False),
            "is_constructor": method.get("is_constructor", False),
            "visibility": method.get("visibility", "public")
        }