from typing import Dict, Any, List
from .schemas import ConflictItem, UnifiedClassDiagram

class CodeDocConsistencyChecker:
    """
    مقارنة الكود الحالي مع التوثيق (High-Level أو Low-Level)
    """

    @staticmethod
    def compare(current_diagram: UnifiedClassDiagram, old_explanation: Dict[str, Any]) -> List[ConflictItem]:
        conflicts = []
        
        # استخراج النص والنوع
        explanation_text = old_explanation.get('content', '') or \
                          old_explanation.get('explanation', '') or \
                          str(old_explanation)
        
        exp_type = old_explanation.get('explanation_type', '') or \
                   old_explanation.get('exp_type', 'high_level')
        
        is_high_level = 'high' in exp_type.lower()

        # 1. كشف الكلاسات غير الموثقة
        for cls in current_diagram.classes:
            class_name = cls.name
            
            if class_name.lower() not in explanation_text.lower():
                conflicts.append(ConflictItem(
                    type="missing_documentation",
                    severity="medium",
                    class_name=class_name,
                    member=None,
                    description=f"الكلاس '{class_name}' موجود في الكود الحالي لكن غير موثق في التوثيق القديم",
                    old_value=None,
                    new_value=class_name,
                    recommendation="إضافة توثيق لهذا الكلاس",
                    doc_level="high_level" if is_high_level else "low_level"
                ))

            # 2. كشف الدوال غير الموثقة (أهم في Low-Level)
            for method in cls.methods:
                if method.name.lower() not in explanation_text.lower():
                    severity = "high" if not is_high_level else "medium"
                    conflicts.append(ConflictItem(
                        type="outdated_documentation",
                        severity=severity,
                        class_name=class_name,
                        member=method.name,
                        description=f"الدالة '{method.name}' موجودة في الكود لكن غير موثقة في التوثيق القديم",
                        old_value=None,
                        new_value=method.signature,
                        recommendation="تحديث التوثيق ليشمل هذه الدالة",
                        doc_level="high_level" if is_high_level else "low_level"
                    ))

        # 3. حساب نسبة التوافق
        total_classes = len(current_diagram.classes)
        documented_classes = sum(1 for cls in current_diagram.classes 
                               if cls.name.lower() in explanation_text.lower())
        
        compatibility_score = round((documented_classes / total_classes * 100), 1) if total_classes > 0 else 0.0

        # إضافة عنصر الـ score
        conflicts.append(ConflictItem(
            type="compatibility_score",
            severity="info",
            class_name="Overall",
            member=None,
            description=f"نسبة توافق التوثيق مع الكود الحالي: {compatibility_score}%",
            old_value=None,
            new_value=f"{compatibility_score}%",
            recommendation="يُفضل إعادة توليد التوثيق" if compatibility_score < 75 else "التوثيق جيد نسبياً",
            doc_level="high_level" if is_high_level else "low_level"
        ))

        return conflicts