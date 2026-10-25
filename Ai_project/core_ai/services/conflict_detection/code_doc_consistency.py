# core_ai/services/conflict_detection/code_doc_consistency.py
import re
from typing import Dict, Any, List, Tuple
from .schemas import ConflictItem, UnifiedClassDiagram, ChangeType, SeverityLevel, DocType
from .doc_splitter import DocSplitter


class CodeDocConsistencyChecker:
    """
    مقارنة الكود الحالي مع التوثيق (High-Level أو Low-Level)
    """

    @staticmethod
    def _extract_documented_entities(text: str) -> dict:
        """استخراج الكلاسات والدوال من نص الشرح الهرمي"""
        classes = set()
        methods = set()  # format: "ClassName.method_name"

        # أنماط العناوين الشائعة
        class_patterns = [
            r'###\s*Class:\s*(\w+)',
            r'##\s*Class:\s*(\w+)',
            r'\*\*Class:\s*(\w+)\*\*',
            r'Class:\s*(\w+)',
        ]
        method_patterns = [
            r'###\s*Method:\s*(\w+)',
            r'##\s*Method:\s*(\w+)',
            r'\*\*Method:\s*(\w+)\*\*',
            r'Method:\s*(\w+)',
        ]

        for pat in class_patterns:
            classes.update(re.findall(pat, text, re.IGNORECASE))

        current_class = None
        for line in text.splitlines():
            for pat in class_patterns:
                m = re.search(pat, line, re.IGNORECASE)
                if m:
                    current_class = m.group(1)
                    classes.add(current_class)
            for pat in method_patterns:
                m = re.search(pat, line, re.IGNORECASE)
                if m:
                    method_name = m.group(1)
                    if current_class:
                        methods.add(f"{current_class}.{method_name}")
                    else:
                        methods.add(method_name)

        return {"classes": classes, "methods": methods}

    # ─────────────────────────────────────────────────────────────────────
    # توثيق بصيغة قاموس (structured):
    #   {"Class.method": {"signature": ..., "description": ..., "raises": [...]}}
    # بدون LLM — فحوصات حتمية على الـ signature والاستثناءات.
    # ─────────────────────────────────────────────────────────────────────
    _DOC_KEYS = {"signature", "description", "raises", "returns"}

    @staticmethod
    def _extract_structured_docs(old_explanation: Dict[str, Any]) -> dict:
        classes, methods, details = set(), set(), {}
        for key, val in (old_explanation or {}).items():
            if not isinstance(key, str) or not isinstance(val, dict):
                continue
            if not (CodeDocConsistencyChecker._DOC_KEYS & set(val.keys())):
                continue
            parts = key.split(".")
            if len(parts) >= 2:
                cls_name, meth = parts[0], parts[-1]
                classes.add(cls_name)
                methods.add(f"{cls_name}.{meth}")
                details[f"{cls_name}.{meth}".lower()] = dict(val)
            else:
                classes.add(key)
        return {"classes": classes, "methods": methods, "details": details}

    @staticmethod
    def _split_top_level(text: str) -> List[str]:
        """تقسيم على الفواصل خارج الأقواس (عشان Dict[str, int] ما تنقسم)."""
        parts, depth, cur = [], 0, []
        for ch in text:
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
            if ch == "," and depth == 0:
                parts.append("".join(cur))
                cur = []
            else:
                cur.append(ch)
        if "".join(cur).strip():
            parts.append("".join(cur))
        return parts

    @staticmethod
    def _parse_signature(sig: str):
        """'f(self, a: int, b=1) -> X'  →  (['a', 'b'], 'X')  أو None إذا ما انفهم."""
        m = re.match(r'\s*[\w.]+\s*\((.*)\)\s*(?:->\s*(.+?))?\s*$', sig or "", re.S)
        if not m:
            return None
        names = []
        for p in CodeDocConsistencyChecker._split_top_level(m.group(1)):
            name = re.split(r'[:=]', p, 1)[0].strip().lstrip("*")
            if name and name not in ("self", "cls"):
                names.append(name)
        return names, (m.group(2) or "").strip()

    @staticmethod
    def _may_return_none(ret: str) -> bool:
        r = (ret or "").replace(" ", "")
        return bool(
            re.match(r'Optional\[', r)
            or re.search(r'(^|\|)None($|\|)', r) and r != "None"
            or re.match(r'Union\[.*\bNone\b.*\]', r)
        )

    @staticmethod
    def _documented_raises(detail: Dict[str, Any]) -> List[str]:
        raises = detail.get("raises") or []
        if isinstance(raises, str):
            raises = [raises]
        raises = [r for r in raises if r]
        if not raises:
            raises = re.findall(r'\braises?\s+(\w+)', detail.get("description", "") or "", re.IGNORECASE)
        return raises

    @staticmethod
    def _check_structured_method(class_name, method, detail, doc_type_value) -> List[ConflictItem]:
        """تناقضات حقيقية (مو مجرد تغطية) بين توثيق قاموس وتوقيع الكود."""
        out: List[ConflictItem] = []
        code_sig = CodeDocConsistencyChecker._parse_signature(method.signature)
        doc_sig = CodeDocConsistencyChecker._parse_signature(detail.get("signature", ""))
        code_ret = code_sig[1] if code_sig else ""
        doc_ret = doc_sig[1] if doc_sig else ""

        def item(severity, description, old, new, rec, conf):
            return ConflictItem(
                type=ChangeType.DOC_DRIFT, severity=severity,
                class_name=class_name, member=method.name,
                description=description, old_value=old, new_value=new,
                suggestion=rec, recommendation=rec,
                doc_type=doc_type_value, ai_confidence=conf,
            )

        # 1) التوثيق بيقول يرمي استثناء، والكود بيرجّع Optional/None
        raises = CodeDocConsistencyChecker._documented_raises(detail)
        raised_flagged = False
        if raises and CodeDocConsistencyChecker._may_return_none(code_ret) \
                and not CodeDocConsistencyChecker._may_return_none(doc_ret):
            exc = raises[0]
            raised_flagged = True
            out.append(item(
                SeverityLevel.HIGH,
                f"تناقض: التوثيق يقول إن '{method.name}' يرمي {exc}، لكن توقيع الكود "
                f"({code_ret}) يرجّع None بدل رمي استثناء — raises {exc} vs returns None",
                f"Documentation: raises {exc}",
                f"Code: returns {code_ret} (may return None)",
                "حدّثي التوثيق ليذكر إن الدالة ترجّع None، أو عدّلي الكود ليرمي الاستثناء الموثّق",
                0.9,
            ))

        if doc_sig and code_sig:
            # 2) اختلاف أسماء/عدد الـ parameters
            if doc_sig[0] != code_sig[0]:
                out.append(item(
                    SeverityLevel.MEDIUM,
                    f"Signature mismatch: doc params {doc_sig[0]} vs code params {code_sig[0]}",
                    detail.get("signature"), method.signature,
                    "تحديث التوثيق ليتوافق مع التوقيع الحالي", 0.85,
                ))
            # 3) اختلاف نوع الإرجاع (إلا إذا انحكى عنه بالبند 1 — نفس السبب الجذري)
            norm = lambda t: re.sub(r'\s+', '', t or "").lower()
            if not raised_flagged and doc_ret and code_ret and norm(doc_ret) != norm(code_ret):
                out.append(item(
                    SeverityLevel.MEDIUM,
                    f"Return type mismatch: doc says '{doc_ret}', code returns '{code_ret}'",
                    doc_ret, code_ret,
                    "تحديث التوثيق ليتوافق مع نوع الإرجاع الحالي", 0.8,
                ))
        return out

    @staticmethod
    def compare(current_diagram: UnifiedClassDiagram, old_explanation: Dict[str, Any]) -> List[ConflictItem]:
        conflicts = []

        explanation_text = (
            old_explanation.get("content", "")
            or old_explanation.get("explanation", "")
            or str(old_explanation)
        )

        exp_type = (
            old_explanation.get("explanation_type", "")
            or old_explanation.get("exp_type", "high_level")
        )

        is_high_level = "high" in exp_type.lower()
        doc_type_value = DocType.HIGH_LEVEL if is_high_level else DocType.LOW_LEVEL

        documented_classes  = 0
        partially_documented = 0
        undocumented_classes = 0
        total_elements       = 0
        fully_doc_elements   = 0
        partial_doc_elements = 0
        undoc_elements       = 0

        entities = CodeDocConsistencyChecker._extract_documented_entities(explanation_text)
        structured = CodeDocConsistencyChecker._extract_structured_docs(old_explanation)
        entities["classes"] |= structured["classes"]
        entities["methods"] |= structured["methods"]
        documented_class_names = {c.lower() for c in entities["classes"]}
        documented_methods = {m.lower() for m in entities["methods"]}

        # DocSplitter بيفهم Constructor: وأشكال العناوين المختلفة (public Book(...)، Book(...)، ...).
        # منضيف نتيجته فوق الـ regex القديم (union) — ما منشيل شي كان موثّق قبل.
        mapping = DocSplitter.match(DocSplitter.split(old_explanation), current_diagram, explanation_text)
        splitter_keys = mapping.documented_keys()
        documented_class_names |= splitter_keys["classes"]
        documented_methods |= splitter_keys["methods"]

        for cls in current_diagram.classes:
            class_name       = cls.name
            class_documented = class_name.lower() in documented_class_names
            total_elements  += 1

            # حساب الدوال الموثقة في هذا الكلاس
            methods_total      = len(cls.methods)
            methods_documented = sum(
                1 for m in cls.methods
                if (f"{class_name}.{m.name}").lower() in documented_methods or m.name.lower() in documented_methods
            )
            total_elements += methods_total

            if class_documented:
                documented_classes += 1
                if methods_total == 0 or methods_documented == methods_total:
                    fully_doc_elements += 1 + methods_total
                elif methods_documented > 0:
                    partially_documented += 1
                    partial_doc_elements += 1
                    fully_doc_elements   += methods_documented
                    undoc_elements       += methods_total - methods_documented
                else:
                    partially_documented += 1
                    partial_doc_elements += 1
                    undoc_elements       += methods_total
            else:
                undocumented_classes += 1
                undoc_elements       += 1 + methods_total
                conflicts.append(ConflictItem(
                    type=ChangeType.DOC_DRIFT,
                    severity=SeverityLevel.MEDIUM,
                    class_name=class_name,
                    member=None,
                    description=f"الكلاس '{class_name}' موجود في الكود الحالي لكن غير موثق في التوثيق القديم",
                    old_value=None,
                    new_value=class_name,
                    suggestion="إضافة توثيق لهذا الكلاس",
                    recommendation="إضافة توثيق لهذا الكلاس",
                    doc_type=doc_type_value,
                    ai_confidence=0.85
                ))

            # كشف الدوال غير الموثقة
            for method in cls.methods:
                method_key = f"{class_name}.{method.name}".lower()
                if method_key not in documented_methods and method.name.lower() not in documented_methods:
                    severity = SeverityLevel.HIGH if not is_high_level else SeverityLevel.MEDIUM
                    conflicts.append(ConflictItem(
                        type=ChangeType.DOC_DRIFT,
                        severity=severity,
                        class_name=class_name,
                        member=method.name,
                        description=f"الدالة '{method.name}' موجودة في الكود لكن غير موثقة في التوثيق القديم",
                        old_value=None,
                        new_value=method.signature,
                        suggestion="تحديث التوثيق ليشمل هذه الدالة",
                        recommendation="تحديث التوثيق ليشمل هذه الدالة",
                        doc_type=doc_type_value,
                        ai_confidence=0.80
                    ))

            # فحص توافق الـ signature للدوال الموثقة
            for m in cls.methods:
                method_key = f"{class_name}.{m.name}".lower()
                method_documented = method_key in documented_methods or m.name.lower() in documented_methods
                if method_documented:
                    detail = structured["details"].get(method_key)
                    if detail:
                        conflicts.extend(CodeDocConsistencyChecker._check_structured_method(
                            class_name, m, detail, doc_type_value))
                        continue
                    # حاول استخراج عدد الـ params من نص الشرح حول اسم الدالة
                    sig_match = re.search(
                        rf'{re.escape(m.name)}\s*\(([^)]*)\)',
                        explanation_text,
                        re.IGNORECASE
                    )
                    if sig_match:
                        params_in_doc = [p.strip() for p in sig_match.group(1).split(",") if p.strip()]
                        # MethodDetail ما فيه حقل parameters — منستخرجها من الـ signature
                        # (قبل: كانت دايماً [] فكل دالة موثقة بـ params انحسبت mismatch غلط)
                        parsed = CodeDocConsistencyChecker._parse_signature(m.signature)
                        params_in_code = parsed[0] if parsed else (getattr(m, "parameters", []) or [])
                        params_in_doc = [p for p in params_in_doc if p.split(":")[0].strip() not in ("self", "cls")]
                        if len(params_in_doc) != len(params_in_code):
                            conflicts.append(ConflictItem(
                                type=ChangeType.DOC_DRIFT,
                                severity=SeverityLevel.MEDIUM,
                                class_name=class_name,
                                member=m.name,
                                description=f"Signature mismatch: doc mentions {len(params_in_doc)} params, code has {len(params_in_code)}",
                                recommendation="تحديث التوثيق ليتوافق مع التوقيع الحالي",
                                doc_type=doc_type_value,
                                ai_confidence=0.75
                            ))


        total_classes        = len(current_diagram.classes)
        compatibility_score  = round((documented_classes / total_classes * 100), 1) if total_classes > 0 else 0.0
        coverage_percentage  = round((fully_doc_elements / total_elements * 100), 1) if total_elements > 0 else 0.0
        critical_conflicts   = sum(1 for c in conflicts if c.severity == SeverityLevel.CRITICAL)

        # حفظ الإحصائيات في الـ Overall item عشان conflict_tasks يقدر يقرأها
        conflicts.append(ConflictItem(
            type=ChangeType.DOC_DRIFT,
            severity=SeverityLevel.INFO,
            class_name="Overall",
            member=None,
            description=f"نسبة توافق التوثيق مع الكود الحالي: {compatibility_score}%",
            old_value=None,
            new_value=f"{compatibility_score}%",
            suggestion="التوثيق جيد نسبياً" if compatibility_score >= 75 else "يُفضل إعادة توليد التوثيق",
            recommendation="التوثيق جيد نسبياً" if compatibility_score >= 75 else "يُفضل إعادة توليد التوثيق",
            doc_type=doc_type_value,
            ai_confidence=compatibility_score / 100,
            # نخزن الإحصائيات في element
            element={
                "compatibility_score":   compatibility_score,
                "coverage_percentage":   coverage_percentage,
                "total_elements":        total_elements,
                "fully_documented":      fully_doc_elements,
                "partially_documented":  partial_doc_elements,
                "undocumented":          undoc_elements,
                "critical_conflicts":    critical_conflicts,
                "undocumented_classes":  [
                    c.name for c in current_diagram.classes
                    if c.name.lower() not in documented_class_names
                ],
                "undocumented_methods": [
                    {"class": cls.name, "method": m.name}
                    for cls in current_diagram.classes
                    for m in cls.methods
                    if (f"{cls.name}.{m.name}").lower() not in documented_methods and m.name.lower() not in documented_methods
                ]
            }
        ))

        return conflicts