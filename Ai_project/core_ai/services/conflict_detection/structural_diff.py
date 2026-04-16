from typing import Dict, List, Any
from .schemas import UnifiedClassDiagram, ConflictItem

class StructuralDiff:
    """
    يقارن بين نسختين من Class Diagram (Structural Diff)
    يعتمد على HyperDiff methodology
    """

    @staticmethod
    def compare(diagram_a: UnifiedClassDiagram, diagram_b: UnifiedClassDiagram) -> List[ConflictItem]:
        conflicts = []

        # 1. مقارنة الكلاسات
        classes_a = {c.name: c for c in diagram_a.classes}
        classes_b = {c.name: c for c in diagram_b.classes}

        # كلاسات محذوفة
        for name in set(classes_a.keys()) - set(classes_b.keys()):
            conflicts.append(ConflictItem(
                type="class_removed",
                severity="high",
                class_name=name,
                description=f"Class '{name}' was removed in version B",
                old_value=name,
                new_value=None,
                recommendation="Check if this class is still needed"
            ))

        # كلاسات جديدة
        for name in set(classes_b.keys()) - set(classes_a.keys()):
            conflicts.append(ConflictItem(
                type="class_added",
                severity="medium",
                class_name=name,
                description=f"New class '{name}' was added",
                old_value=None,
                new_value=name,
                recommendation="Document the new class"
            ))

        # مقارنة الدوال والعلاقات داخل الكلاسات المشتركة
        for name, cls_a in classes_a.items():
            if name in classes_b:
                cls_b = classes_b[name]
                # هنا يمكن إضافة مقارنة أكثر تفصيلاً (methods, attributes, relationships)
                # حالياً نركز على الـ relationships
                rel_a = {r["to"] for r in cls_a.relationships}
                rel_b = {r["to"] for r in cls_b.relationships}
                added_rel = rel_b - rel_a
                removed_rel = rel_a - rel_b

                for rel in added_rel:
                    conflicts.append(ConflictItem(
                        type="relationship_added",
                        severity="medium",
                        class_name=name,
                        member=rel,
                        description=f"New relationship from {name} to {rel}",
                        old_value=None,
                        new_value=rel
                    ))

        return conflicts