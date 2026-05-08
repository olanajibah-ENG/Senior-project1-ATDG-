# core_ai/services/conflict_detection/structural_diff.py
from typing import List, Dict
from .schemas import (
    UnifiedClassDiagram, ClassDetail, ConflictItem,
    ChangeType, SeverityLevel
)
from .fingerprint_builder import FingerprintBuilder
import logging

logger = logging.getLogger(__name__)


class StructuralDiff:
    """
    يقارن بين مخططين هيكلياً ويكتشف التناقضات.

    المميزات:
    - كشف الكلاسات المحذوفة / الجديدة مع تفاصيل الـ members
    - كشف إعادة تسمية الدوال (Rename Detection) عبر FingerprintBuilder المحسّن
    - كشف تغيير الـ signature
    - كشف تغيير الـ constructor
    - كشف تغيير الـ generic constraints
    - مقارنة الخصائص والعلاقات
    """

    @staticmethod
    def compare(
        diagram_a: UnifiedClassDiagram,
        diagram_b: UnifiedClassDiagram
    ) -> List[ConflictItem]:

        logger.info("🔍 Starting structural comparison...")
        conflicts: List[ConflictItem] = []

        classes_a = {c.name: c for c in diagram_a.classes}
        classes_b = {c.name: c for c in diagram_b.classes}

        names_a = set(classes_a)
        names_b = set(classes_b)

        # ──────────────────────────────────────────────────────────────
        # 1. كلاسات محذوفة — CRITICAL مع ذكر الـ methods المفقودة
        # ──────────────────────────────────────────────────────────────
        for name in names_a - names_b:
            cls = classes_a[name]
            pub_methods = [m.name for m in cls.methods if m.visibility == "public"]
            methods_preview = ", ".join(pub_methods[:5])
            if len(pub_methods) > 5:
                methods_preview += f" (+{len(pub_methods) - 5} more)"

            conflicts.append(ConflictItem(
                type=ChangeType.BREAKING_CHANGE,
                severity=SeverityLevel.CRITICAL,
                category="class_removed",
                class_name=name,
                description=f"تم حذف الكلاس '{name}' بالكامل ({len(pub_methods)} public methods)",
                old_value=f"class {name}" + (f" [{methods_preview}]" if methods_preview else ""),
                new_value=None,
                impact="Breaking Change - جميع الاستخدامات ستفشل فوراً",
                suggestion=(
                    f"تحقق: هل تمت إعادة تسمية '{name}'؟ "
                    "هل توجد كلاس بديلة؟ تأكد من تحديث كل الاستدعاءات"
                ),
                auto_fix_available=False,
                ai_confidence=1.0
            ))

        # ──────────────────────────────────────────────────────────────
        # 2. كلاسات جديدة — مع ذكر الـ members الجديدة
        # ──────────────────────────────────────────────────────────────
        for name in names_b - names_a:
            cls = classes_b[name]
            pub_methods = [m.name for m in cls.methods if m.visibility == "public"]
            methods_preview = ", ".join(pub_methods[:5])
            if len(pub_methods) > 5:
                methods_preview += f" (+{len(pub_methods) - 5} more)"

            conflicts.append(ConflictItem(
                type=ChangeType.NEW_FEATURE,
                severity=SeverityLevel.INFO,
                category="class_added",
                class_name=name,
                description=f"تمت إضافة كلاس جديد '{name}' ({len(pub_methods)} public methods)",
                old_value=None,
                new_value=f"class {name}" + (f" [{methods_preview}]" if methods_preview else ""),
                impact="ميزة جديدة — تأكد من توثيقها وكتابة الاختبارات",
                suggestion="وثّق الكلاس الجديد وأضف unit tests",
                auto_fix_available=False,
                ai_confidence=1.0
            ))

        # ──────────────────────────────────────────────────────────────
        # 3. مقارنة الكلاسات المشتركة
        # ──────────────────────────────────────────────────────────────
        for name in names_a & names_b:
            cls_a = classes_a[name]
            cls_b = classes_b[name]

            conflicts.extend(StructuralDiff._compare_methods(cls_a, cls_b))
            conflicts.extend(StructuralDiff._compare_attributes(cls_a, cls_b))
            conflicts.extend(StructuralDiff._compare_relationships(cls_a, cls_b))
            conflicts.extend(StructuralDiff._compare_constraints(cls_a, cls_b))

        logger.info(f"✅ Structural comparison done: {len(conflicts)} items")
        return conflicts

    # ──────────────────────────────────────────────────────────────────
    # مقارنة الدوال مع Rename Detection محسّن
    # ──────────────────────────────────────────────────────────────────
    @staticmethod
    def _compare_methods(
        class_a: ClassDetail,
        class_b: ClassDetail
    ) -> List[ConflictItem]:

        conflicts: List[ConflictItem] = []

        methods_a = {m.name: m for m in class_a.methods}
        methods_b = {m.name: m for m in class_b.methods}

        deleted = set(methods_a) - set(methods_b)
        added   = set(methods_b) - set(methods_a)
        common  = set(methods_a) & set(methods_b)

        # ── Rename Detection — يعتمد على FingerprintBuilder المحسّن ──
        real_deletions = set(deleted)
        real_additions = set(added)

        for old_name in list(deleted):
            old_fp = FingerprintBuilder.build(methods_a[old_name].model_dump())

            best_match = None
            best_sim   = 0.0

            for new_name in list(real_additions):
                new_fp  = FingerprintBuilder.build(methods_b[new_name].model_dump())
                # مطابقة تامة للبصمة → rename مؤكد
                if old_fp == new_fp:
                    best_match = new_name
                    best_sim   = 1.0
                    break
                # مطابقة جزئية (> 0.8) → rename محتمل
                sim = FingerprintBuilder.similarity(old_fp, new_fp)
                if sim > best_sim and sim >= 0.8:
                    best_sim   = sim
                    best_match = new_name

            if best_match:
                conflicts.append(ConflictItem(
                    type=ChangeType.REFACTORING,
                    severity=SeverityLevel.LOW,
                    category="method_renamed",
                    class_name=class_a.name,
                    member=old_name,
                    description=f"تمت إعادة تسمية '{old_name}' إلى '{best_match}'",
                    old_value=old_name,
                    new_value=best_match,
                    impact="Refactoring - يجب تحديث الاستدعاءات",
                    suggestion=f"استخدم Find & Replace لتحديث '{old_name}' → '{best_match}'",
                    auto_fix_available=True,
                    ai_confidence=round(best_sim, 2)
                ))
                real_deletions.discard(old_name)
                real_additions.discard(best_match)

        # ── حذف حقيقي ─────────────────────────────────────────────────
        for name in real_deletions:
            m = methods_a[name]
            conflicts.append(ConflictItem(
                type=ChangeType.BREAKING_CHANGE,
                severity=SeverityLevel.HIGH,
                category="method_removed",
                class_name=class_a.name,
                member=name,
                description=f"تم حذف الدالة '{name}' من '{class_a.name}'",
                old_value=m.signature,
                new_value=None,
                impact="Breaking Change - الاستدعاءات ستفشل",
                suggestion="أعد الدالة أو حدّث كل الاستدعاءات",
                auto_fix_available=False,
                ai_confidence=1.0
            ))

        # ── إضافة حقيقية ───────────────────────────────────────────────
        for name in real_additions:
            m = methods_b[name]
            # إذا كانت الكلاس interface → إضافة method إجبارية = breaking
            is_interface = class_b.is_interface
            conflicts.append(ConflictItem(
                type=ChangeType.BREAKING_CHANGE if is_interface else ChangeType.NEW_FEATURE,
                severity=SeverityLevel.HIGH if is_interface else SeverityLevel.INFO,
                category="method_added",
                class_name=class_b.name,
                member=name,
                description=(
                    f"تمت إضافة دالة إجبارية '{name}' إلى interface '{class_b.name}' — "
                    "جميع الكلاسات المنفِّذة يجب أن تُنفِّذها"
                    if is_interface else
                    f"تمت إضافة دالة جديدة '{name}'"
                ),
                old_value=None,
                new_value=m.signature,
                impact=(
                    "Breaking Change - كل class تنفِّذ هذا الـ interface يجب أن تضيف التنفيذ"
                    if is_interface else None
                ),
                suggestion=(
                    f"أضف تنفيذاً لـ '{name}' في كل class تنفِّذ '{class_b.name}'"
                    if is_interface else
                    "وثّق الدالة الجديدة"
                ),
                auto_fix_available=False,
                ai_confidence=1.0
            ))

        # ── دوال معدّلة (تغيّرت الـ signature) ───────────────────────
        for name in common:
            ma = methods_a[name]
            mb = methods_b[name]
            if ma.signature == mb.signature:
                continue

            is_breaking = StructuralDiff._is_breaking_signature_change(ma, mb)
            severity    = SeverityLevel.CRITICAL if is_breaking else SeverityLevel.MEDIUM

            conflicts.append(ConflictItem(
                type=ChangeType.BREAKING_CHANGE if is_breaking else ChangeType.REFACTORING,
                severity=severity,
                category="method_signature_changed",
                class_name=class_a.name,
                member=name,
                description=f"تغيّرت signature الدالة '{name}' في '{class_a.name}'",
                old_value=ma.signature,
                new_value=mb.signature,
                impact="Breaking change - الاستدعاءات ستفشل" if is_breaking else "تغيير داخلي",
                suggestion="حدّث جميع الاستدعاءات أو أنشئ wrapper للتوافق",
                auto_fix_available=True,
                ai_confidence=0.95
            ))

        return conflicts

    # ──────────────────────────────────────────────────────────────────
    # مقارنة الخصائص
    # ──────────────────────────────────────────────────────────────────
    @staticmethod
    def _compare_attributes(
        class_a: ClassDetail,
        class_b: ClassDetail
    ) -> List[ConflictItem]:

        conflicts: List[ConflictItem] = []

        attrs_a = {a.name: a for a in class_a.attributes}
        attrs_b = {a.name: a for a in class_b.attributes}

        for name in set(attrs_a) - set(attrs_b):
            conflicts.append(ConflictItem(
                type=ChangeType.BREAKING_CHANGE,
                severity=SeverityLevel.MEDIUM,
                category="attribute_removed",
                class_name=class_a.name,
                member=name,
                description=f"تم حذف الخاصية '{name}' من '{class_a.name}'",
                old_value=attrs_a[name].type,
                new_value=None,
                suggestion="تحقق من كل مكان يستخدم هذه الخاصية",
                auto_fix_available=False,
                ai_confidence=1.0
            ))

        for name in set(attrs_b) - set(attrs_a):
            conflicts.append(ConflictItem(
                type=ChangeType.NEW_FEATURE,
                severity=SeverityLevel.INFO,
                category="attribute_added",
                class_name=class_b.name,
                member=name,
                description=f"تمت إضافة خاصية جديدة '{name}'",
                old_value=None,
                new_value=attrs_b[name].type,
                suggestion="وثّق الخاصية الجديدة",
                auto_fix_available=False,
                ai_confidence=1.0
            ))

        for name in set(attrs_a) & set(attrs_b):
            if attrs_a[name].type != attrs_b[name].type:
                conflicts.append(ConflictItem(
                    type=ChangeType.BEHAVIOR_CHANGE,
                    severity=SeverityLevel.MEDIUM,
                    category="attribute_type_changed",
                    class_name=class_a.name,
                    member=name,
                    description=f"تغيّر نوع الخاصية '{name}'",
                    old_value=attrs_a[name].type,
                    new_value=attrs_b[name].type,
                    suggestion="تحقق من توافق النوع الجديد مع الاستخدامات الموجودة",
                    auto_fix_available=False,
                    ai_confidence=0.90
                ))

        return conflicts

    # ──────────────────────────────────────────────────────────────────
    # مقارنة العلاقات
    # ──────────────────────────────────────────────────────────────────
    @staticmethod
    def _compare_relationships(
        class_a: ClassDetail,
        class_b: ClassDetail
    ) -> List[ConflictItem]:

        conflicts: List[ConflictItem] = []

        rel_a = {r.get("to", "") for r in class_a.relationships}
        rel_b = {r.get("to", "") for r in class_b.relationships}

        for rel in rel_b - rel_a:
            conflicts.append(ConflictItem(
                type=ChangeType.REFACTORING,
                severity=SeverityLevel.MEDIUM,
                category="relationship_added",
                class_name=class_a.name,
                member=rel,
                description=f"علاقة جديدة من '{class_a.name}' إلى '{rel}'",
                old_value=None,
                new_value=rel,
                suggestion="تأكد من توثيق العلاقة الجديدة",
                auto_fix_available=False,
                ai_confidence=0.85
            ))

        for rel in rel_a - rel_b:
            conflicts.append(ConflictItem(
                type=ChangeType.BREAKING_CHANGE,
                severity=SeverityLevel.MEDIUM,
                category="relationship_removed",
                class_name=class_a.name,
                member=rel,
                description=f"تم حذف العلاقة من '{class_a.name}' إلى '{rel}'",
                old_value=rel,
                new_value=None,
                suggestion="تحقق من أثر حذف هذه العلاقة",
                auto_fix_available=False,
                ai_confidence=0.85
            ))

        return conflicts

    # ──────────────────────────────────────────────────────────────────
    # مقارنة الـ Generic Constraints  ← جديد
    # ──────────────────────────────────────────────────────────────────
    @staticmethod
    def _compare_constraints(
        class_a: ClassDetail,
        class_b: ClassDetail
    ) -> List[ConflictItem]:
        """
        يكتشف تغييرات الـ generic constraints مثل إضافة new() أو IDisposable.
        يقرأ constraints من class_a.constraints و class_b.constraints
        (يجب أن يوفّرها الـ language processor — راجع ast_unifier.py).
        """
        conflicts: List[ConflictItem] = []

        # نقرأ من extra_data أو من constraints field إذا أضفناها
        constraints_a = set(getattr(class_a, "constraints", None) or [])
        constraints_b = set(getattr(class_b, "constraints", None) or [])

        if constraints_a == constraints_b:
            return conflicts

        added_c   = constraints_b - constraints_a
        removed_c = constraints_a - constraints_b

        if added_c:
            conflicts.append(ConflictItem(
                type=ChangeType.BREAKING_CHANGE,
                severity=SeverityLevel.HIGH,
                category="generic_constraint_added",
                class_name=class_a.name,
                member=None,
                description=(
                    f"أُضيفت قيود جديدة على الـ generic '{class_a.name}': "
                    f"{', '.join(sorted(added_c))}"
                ),
                old_value=str(sorted(constraints_a)) if constraints_a else "none",
                new_value=str(sorted(constraints_b)),
                impact=(
                    "Breaking Change - الكلاسات المستخدَمة كـ type argument "
                    "يجب أن تحقق القيود الجديدة"
                ),
                suggestion=(
                    f"تأكد أن كل type argument يحقق: {', '.join(sorted(added_c))}. "
                    "مثلاً: إضافة new() تعني أن الكلاس يجب أن يملك default constructor"
                ),
                auto_fix_available=False,
                ai_confidence=0.95
            ))

        if removed_c:
            conflicts.append(ConflictItem(
                type=ChangeType.REFACTORING,
                severity=SeverityLevel.MEDIUM,
                category="generic_constraint_removed",
                class_name=class_a.name,
                member=None,
                description=(
                    f"تمت إزالة قيود من الـ generic '{class_a.name}': "
                    f"{', '.join(sorted(removed_c))}"
                ),
                old_value=str(sorted(constraints_a)),
                new_value=str(sorted(constraints_b)) if constraints_b else "none",
                impact="تخفيف قيود — قد يسمح باستخدام types لم تكن مسموحاً بها",
                suggestion="تحقق من أن إزالة القيد لا تؤثر على منطق الكلاس الداخلي",
                auto_fix_available=False,
                ai_confidence=0.85
            ))

        return conflicts

    # ──────────────────────────────────────────────────────────────────
    # Helper
    # ──────────────────────────────────────────────────────────────────
    @staticmethod
    def _is_breaking_signature_change(method_a, method_b) -> bool:
        """
        يحدد إذا كان تغيير الـ signature يُعدّ Breaking Change.
        يعتمد على FingerprintBuilder المحسّن الذي يقارن:
        - عدد الباراميترات
        - أنواع الباراميترات
        - نوع الإرجاع
        """
        fp_a = FingerprintBuilder.build(method_a.model_dump())
        fp_b = FingerprintBuilder.build(method_b.model_dump())
        return fp_a != fp_b
