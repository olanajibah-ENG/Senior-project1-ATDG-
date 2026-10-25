# تقرير اختبارات الخطوة 2: تحديث الـ schemas

**التاريخ:** 2026-10-25
**ملف الاختبارات:** [`core_ai/tests/test_schemas_step2.py`](../test_schemas_step2.py)
**البيئة:** حاوية `ai_web` (Python 3.10.20)

## الهدف من الخطوة
1. **إصلاح خطأ بكود الإنتاج:** أي تغيير هيكلي (حذف دالة، إضافة دالة، تغيير توقيع...) كان يوقّع مسار الكود مقابل الكود كله.
2. **إضافة نوع `RENAMED`** لحتى إعادة التسمية ما تنحسب "تغيير بالسلوك".
3. **تجهيز حقول جديدة** رح تحتاجها الخطوات الجاية، بدون ما نغيّر سلوك النظام.

## شو تغيّر بالكود

| الملف | التغيير |
|---|---|
| `schemas.py` | حقل `category` صار نص حر بدل enum فيه 3 قيم بس |
| `schemas.py` | `ChangeType.RENAMED` |
| `schemas.py` | تصنيف DocPrism الجديد `DocConsistencyLabel`: `Consistent` و`Direct_Mismatch` و`Over_Promise` و`Under_Promise` |
| `schemas.py` | قرار الـ ChangeClassifier `ChangeDecision`: `structural_only` و`structural_and_behavioral` و`behavioral_candidate` و`no_change` |
| `schemas.py` | مستوى الخطورة حسب AexPy `RiskLevel`: `critical` و`warning` و`informational` |
| `schemas.py` | حقول جديدة على `ConflictItem`، كلها اختيارية: `doc_label` و`is_flagged` و`evidence` و`decision` و`risk_level` |
| `structural_diff.py` | صار يستعمل `ChangeType.RENAMED` مباشرة بدل `hasattr` |

**ما تغيّر:** حقل `severity` وقيمه (`critical` و`high` و`medium` و`low` و`info`)، لأنه الواجهة الأمامية بتلوّن فيها صفحات الكود مقابل الكود والكود مقابل التوثيق.

## الاختبارات ونتائجها: 9 من 9 نجحت
ومع اختبارات الخطوة 1، المجموع **21 من 21**.

| الاختبار | شو بيفحص | قبل الخطوة 2 | بعدها |
|---|---|---|---|
| `test_method_removed_no_longer_crashes` | كلاس انحذفت منه دالة | ❌ `ValidationError` | ✅ بيطلع `method_removed` |
| `test_every_structural_pattern_runs` | 8 أنماط تغيير هيكلي بنفس الوقت: حذف وإضافة كلاس، حذف وإضافة دالة، تغيير توقيع، حذف وإضافة وتغيير نوع attribute | ❌ بيوقع عند أول تغيير | ✅ الأنماط الثمانية كلها طلعت |
| `test_full_code_vs_code_pipeline_succeeds` | المسار الكامل عبر `ConflictOrchestrator` (مع تعطيل الذكاء الاصطناعي) | ❌ بيوقع | ✅ `status = success` |
| `test_rename_detector_now_reports_renamed_type` | `fetch_user` صارت `get_user` | ❌ بيوقع، ولو ما وقع كان النوع رح يطلع `behavior_change` | ✅ النوع `renamed` |
| `test_old_stored_item_still_loads` | تقرير محفوظ قبل الخطوة 2 (ما فيه الحقول الجديدة) بينقرأ عادي | ✅ | ✅ الحقول الجديدة `None` |
| `test_old_category_values_still_accepted` | القيمة القديمة `syntactic` لسا مقبولة | ✅ | ✅ |
| `test_new_fields_roundtrip_as_plain_strings` | الحقول الجديدة بتتحوّل لنص عادي لما تنحفظ (`"Direct_Mismatch"` و`"critical"`) وبترجع تنقرأ متل ما هي | لا ينطبق | ✅ |
| `test_severity_values_unchanged_for_frontend` | قيم `severity` ما تغيّرت، لحتى ما تخرب ألوان الواجهة | ✅ | ✅ |
| `test_docprism_labels_match_labeling_guide` | أسماء التصنيفات الأربعة مطابقة لدليل الوسم `evaluation/labeling/guide_code_vs_doc.md` | لا ينطبق | ✅ |

### كيف عرفنا عمود "قبل"
شغّلنا نفس الحالات على كود الـ commit السابق (`84e5ac5`):
```
method removed : ValidationError
rename         : ValidationError
```
يعني **قبل هالخطوة، مسار الكود مقابل الكود بالإنتاج كان بيفشل مع أي ملف فيه تغيير هيكلي واحد على الأقل.** المسار كان يطلّع نتيجة بس إذا الملفين ما فيهم أي تغيير هيكلي.

## النسخة المجمّدة
`python -m evaluation.harness.snapshot` طلّع `ok: a8649b22…`، يعني ما انلمست.

## مشاكل انكشفت (مش من هالخطوة، رح تنحل بالخطوة 7)
بعد ما وقف الـ crash، صار ممكن نشوف شو بيطلّع `StructuralDiff` فعلياً. ولقينا مشكلتين بـ `RenameDetector`:

**1. إعادة التسمية بتنعرض مرتين:**
```
fetch_user → get_user:
  ('refactoring', 'method_renamed', 'fetch_user', 'get_user')   ← من _compare_methods
  ('renamed',     None,             'fetch_user', 'get_user')   ← من RenameDetector
```

**2. إعادة تسمية وهمية (false positive):** ضفنا دالة جديدة `b()` والدالة القديمة `a()` لسا موجودة. النظام طلّع:
```
('new_feature', 'method_added', 'b')    ← صح
('renamed',     None, 'a' → 'b')        ← غلط: a ما انحذفت
```
السبب إنه `RenameDetector` بيقارن البصمات بين كل الدوال، والبصمة مبنية على شكل التوقيع بس (عدد المعاملات وأنواعها ونوع الإرجاع). فأي دالتين إلهم نفس الشكل بينحسبوا إعادة تسمية، حتى لو الدالة القديمة لسا موجودة.

**ليش هالشي مهم للتقييم:** هاد بيرفع الإنذارات الكاذبة وبينزّل الـ Precision. والنسخة المجمّدة (الـ baseline) فيها نفس المشكلتين، لأنه إصلاح `category` انطبق عليها كتعديل موثّق، فهي كمان بتوصل لهون. الفرق الوحيد إنها بتسمّي النوع `behavior_change` بدل `renamed`. بالخطوة 7 (`SignatureComparer`) منعتمد على مقارنة الـ body والأسماء الموجودة بالنسختين، ومنمنع التكرار.
