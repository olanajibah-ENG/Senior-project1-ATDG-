# core_ai/services/conflict_detection/fingerprint_builder.py
from typing import Dict, Any


class FingerprintBuilder:
    """
    يبني بصمة (fingerprint) لكل دالة لكشف الـ rename vs logic change.

    المنطق:
    - إذا تطابقت البصمة بين دالتين بأسماء مختلفة → rename
    - إذا اختلفت البصمة لدالتين بنفس الاسم     → logic/signature change

    البصمة تعتمد على:
    - عدد الباراميترات
    - أنواع الباراميترات (يمنع false rename بين دوال لها نفس العدد لكن أنواع مختلفة)
    - نوع الإرجاع (void/Task/int/...) — يمنع false rename بين دوال مختلفة الـ return
    - is_abstract / is_constructor / visibility
    """

    @staticmethod
    def build(method: Dict[str, Any]) -> str:
        sig = method.get("signature", "")

        param_count = FingerprintBuilder._count_params(sig)
        param_types = FingerprintBuilder._extract_param_types(sig)
        return_type = FingerprintBuilder._extract_return_type(sig)

        return (
            f"params:{param_count}"
            f"|ptypes:{param_types}"
            f"|return:{return_type}"
            f"|abstract:{method.get('is_abstract', False)}"
            f"|constructor:{method.get('is_constructor', False)}"
            f"|visibility:{method.get('visibility', 'public')}"
        )

    @staticmethod
    def _count_params(signature: str) -> int:
        """يحسب عدد الباراميترات مع دعم الأقواس المتداخلة (generics)"""
        try:
            start = signature.index("(")
            end   = signature.rindex(")")
            inner = signature[start + 1:end].strip()
            if not inner:
                return 0
            depth  = 0
            commas = 0
            for ch in inner:
                if ch in "(<[{":
                    depth += 1
                elif ch in ")>]}":
                    depth -= 1
                elif ch == "," and depth == 0:
                    commas += 1
            return commas + 1
        except (ValueError, IndexError):
            return 0

    @staticmethod
    def _extract_param_types(signature: str) -> str:
        """
        يستخرج أنواع الباراميترات مرتبة كـ string للمقارنة.
        مثال: add(a: int, b: float): int  →  "int,float"
        مثال: login(email: str, password: str, remember: bool = False)  →  "str,str,bool"
        """
        try:
            start = signature.index("(")
            end   = signature.rindex(")")
            inner = signature[start + 1:end].strip()
            if not inner:
                return ""

            # نقسم الباراميترات مع احترام الأقواس المتداخلة
            parts  = []
            depth  = 0
            current = []
            for ch in inner:
                if ch in "(<[{":
                    depth += 1
                    current.append(ch)
                elif ch in ")>]}":
                    depth -= 1
                    current.append(ch)
                elif ch == "," and depth == 0:
                    parts.append("".join(current).strip())
                    current = []
                else:
                    current.append(ch)
            if current:
                parts.append("".join(current).strip())

            types = []
            for p in parts:
                p = p.strip()
                if not p:
                    continue
                # "name: Type" (Python/TS/C#)
                if ":" in p:
                    t = p.split(":")[-1].strip()
                # "Type name" (Java/C#)
                elif " " in p:
                    t = p.split()[0].strip()
                else:
                    t = p

                # نزيل default values مثل "= false" أو "= None"
                t = t.split("=")[0].strip()
                # نحوّل للأحرف الصغيرة ونزيل الـ ? (optional)
                t = t.rstrip("?").lower()
                types.append(t or "any")

            return ",".join(types)
        except (ValueError, IndexError):
            return ""

    @staticmethod
    def _extract_return_type(signature: str) -> str:
        """
        يستخرج نوع الإرجاع من الـ signature بصرف النظر عن لغة البرمجة.
        يدعم:
          - Python/TS arrow:   "method() -> ReturnType"
          - Colon after paren: "method(): ReturnType"
          - C#/Java prefix:    "ReturnType method(...)"  (fallback)
        """
        # Python/TS: "method() -> Type"
        if "->" in signature:
            return signature.split("->")[-1].strip().lower()

        # Colon after closing paren: "method(): Type"  أو  "method(): async"
        try:
            close_paren = signature.rindex(")")
            after = signature[close_paren + 1:].strip()
            if after.startswith(":"):
                return after[1:].strip().lower()
        except (ValueError, IndexError):
            pass

        return "void"

    @staticmethod
    def similarity(fp_a: str, fp_b: str) -> float:
        """
        يرجع نسبة التشابه بين بصمتين (0.0 → 1.0).
        مفيد للـ fuzzy matching مستقبلاً.
        """
        if fp_a == fp_b:
            return 1.0
        parts_a = set(fp_a.split("|"))
        parts_b = set(fp_b.split("|"))
        common  = len(parts_a & parts_b)
        total   = len(parts_a | parts_b)
        return common / total if total else 0.0
