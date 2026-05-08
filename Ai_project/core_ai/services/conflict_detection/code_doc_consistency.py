# core_ai/services/conflict_detection/code_doc_consistency.py
from typing import Dict, Any, List, Tuple
from .schemas import ConflictItem, UnifiedClassDiagram, ChangeType, SeverityLevel, DocType


class CodeDocConsistencyChecker:
    """
    مقارنة الكود الحالي مع التوثيق (High-Level أو Low-Level)
    """

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

        for cls in current_diagram.classes:
            class_name       = cls.name
            class_documented = class_name.lower() in explanation_text.lower()
            total_elements  += 1

            # حساب الدوال الموثقة في هذا الكلاس
            methods_total      = len(cls.methods)
            methods_documented = sum(
                1 for m in cls.methods
                if m.name.lower() in explanation_text.lower()
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
                if method.name.lower() not in explanation_text.lower():
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
                    if c.name.lower() not in explanation_text.lower()
                ],
                "undocumented_methods": [
                    {"class": cls.name, "method": m.name}
                    for cls in current_diagram.classes
                    for m in cls.methods
                    if m.name.lower() not in explanation_text.lower()
                ]
            }
        ))

        return conflicts