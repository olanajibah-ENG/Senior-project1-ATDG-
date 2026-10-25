# تقرير اختبارات الخطوة 1: استخراج جسم الدالة ومعلوماتها

**التاريخ:** 2026-10-25
**الـ commit:** `84e5ac5`
**ملف الاختبارات:** [`core_ai/tests/test_method_details.py`](../test_method_details.py)
**البيئة:** حاوية `ai_web` (Python 3.10.20، tree-sitter 0.20.4، tree-sitter-languages 1.6.1)

## الهدف من الخطوة
المسارين (الكود مقابل الكود، والكود مقابل التوثيق) بيحتاجوا يعرفوا **شو بتعمل الدالة فعلياً**، مش بس توقيعها. قبل هالخطوة، النظام كان يحفظ لكل دالة الاسم والتوقيع كنص بس. فضفنا لكل دالة هالحقول:

| الحقل | شو فيه |
|---|---|
| `body` | جسم الدالة بدون تعليقات وبدون docstring |
| `body_hash` | بصمة للجسم. التعليقات والمسافات ما بتغيّرها، وتغيير المنطق بيغيّرها |
| `parameters` | لكل معامل: الاسم، والنوع، والقيمة الافتراضية، والنوع (عادي، بالاسم بس، `*args`، `**kwargs`) |
| `return_type` | نوع الإرجاع المكتوب |
| `decorators` | متل `@staticmethod` أو `@Override` |
| `docstring` | التوثيق المكتوب جوا الكود |
| `is_async` | إذا الدالة async |

وصلّحنا كمان شغلتين: دوال الـ `async` بالبايثون كانت تضيع من المخطط، والـ constructors بالجافا كانت مستثناة منه.

## كيف شغّلنا الاختبارات
```bash
MSYS_NO_PATHCONV=1 docker compose run --rm --no-deps -T --entrypoint sh ai_web -c "pip install -q pytest; python -m pytest core_ai/tests/test_method_details.py -v"
```
- `--rm` يعني الحاوية بتنمسح لحالها لما تخلص.
- `--no-deps` يعني ما بنشغّل قواعد البيانات.
- `--entrypoint` بيتجاوز سكربت التشغيل يلي بينتظر MongoDB.
- pytest بينزل جوا الحاوية المؤقتة بس، والصورة نفسها ما بتتغيّر.

## الاختبارات ونتائجها: 12 من 12 نجحت

### بايثون
| الاختبار | شو بيفحص | النتيجة |
|---|---|---|
| `test_python_signature_unchanged` | حقل `signature` القديم طالع **حرف بحرف** متل قبل، لأنه الواجهة و`FingerprintBuilder` بيعتمدوا عليه | ✅ |
| `test_python_parameters` | `force=False` بتنقرأ قيمتها الافتراضية `False`، و`*extra` بيطلع `var_positional`، و`**opts` بيطلع `var_keyword`، و`strict` (بعد `*`) بيطلع `keyword_only` | ✅ |
| `test_python_docstring_and_body` | الـ docstring بينفصل لحاله، والـ body بيطلع `return self.store.get(uid)` بدون التعليق ولا الـ docstring | ✅ |
| `test_python_async_methods_now_included` | دالة `async def fetch` صارت تظهر بالمخطط مع `is_async=True`. **قبل كانت تضيع كلياً** | ✅ |
| `test_python_hash_ignores_comments_whitespace_and_docstring` | غيّرنا التعليق والمسافات والـ docstring، والبصمة **ما تغيّرت** | ✅ |
| `test_python_hash_changes_on_logic_change` | غيّرنا `self.store.get(uid)` لـ `self.store[uid]`، يعني صارت بترمي خطأ بدل ما ترجّع None. البصمة **تغيّرت** | ✅ |

### جافا
| الاختبار | شو بيفحص | النتيجة |
|---|---|---|
| `test_java_constructor_now_included` | الـ constructor صار يظهر بالمخطط مع `is_constructor=True` ومع الـ Javadoc تبعه | ✅ |
| `test_java_parameters_arrays_and_varargs` | `int[]` بتنقرأ صح (قبل كانت تطلع `Object`)، و`String... names` بيطلع `var_positional` (قبل كان يختفي)، و`@Override` بينقرأ | ✅ |
| `test_java_hash_ignores_comments_but_not_logic` | شلنا التعليقات فما تغيّرت البصمة، وغيّرنا `return a` لـ `return null` فتغيّرت | ✅ |

### التوافق مع باقي النظام
| الاختبار | شو بيفحص | النتيجة |
|---|---|---|
| `test_unifier_passes_new_fields` | `ASTUnifier` بيمرّر الحقول الجديدة لـ `MethodDetail` | ✅ |
| `test_old_stored_analysis_still_works` | تحليل محفوظ بـ Mongo **قبل** الخطوة 1 (ما فيه body ولا parameters) بيضل يشتغل، و`StructuralDiff` ما بيوقع عليه | ✅ |
| `test_prompt_fields_unchanged` | البيانات يلي بتنبعت للذكاء الاصطناعي فيها بس الحقول القديمة الستة، يعني الـ prompt ما تغيّر | ✅ |

## فحوصات إضافية (برّا ملف الاختبارات)

### مقارنة النسخة القديمة مع الجديدة على ملفات حقيقية
شغّلنا المعالج القديم (من `legacy_baseline`) والجديد على نفس الملفات، وقارنّا كل حقل قديم:

| اللغة | العينة | النتيجة |
|---|---|---|
| بايثون | 147 ملف حقيقي من المشروع، فيهم 581 دالة | كل الحقول القديمة متطابقة 100%، والكلاسات والعلاقات متطابقة |
| جافا | مثال فيه generics و interface و inner class و varargs و overloaded constructors | كل الحقول القديمة متطابقة، والفرق الوحيد إنه انضافوا 4 constructors |
| JavaScript | كلاس فيه constructor و async ودالة بقيمة افتراضية و `...rest` | متطابق |
| TypeScript | service فيه `private repo` بالـ constructor، و`Promise<User>`، ومعامل اختياري | متطابق |
| C# | `Zoo<T> where T : Animal, new()` مع `async Task` و `///` | متطابق |

### نواقص كشفها الفحص بالـ Docker وانصلحت
هدول ما بيبيّنوا على جهاز التطوير، لأنه نسخة tree-sitter عليه أحدث من يلي بالـ Docker:
1. معاملات الـ JavaScript كانت تطلع فاضية، صارت `['a', 'b', 'rest']`.
2. الـ `async` بالـ C# ما كان ينكشف، صار ينكشف.
3. توثيق الـ C# (`///`) ما كان ينقرأ، صار ينقرأ.

### النسخة المجمّدة
`python -m evaluation.harness.snapshot` طلّع `ok: a8649b22…`، يعني النسخة القديمة ما انلمست.

## ملاحظات
- **على جهاز التطوير (Windows)، معالج الجافا ما بيشتغل**، حتى النسخة القديمة منه، لأنه tree-sitter هناك نسخة 0.25 والمشروع مثبّت على 0.20. لهيك أي تقييم على عينات جافا (متل Cascade) لازم ينعمل بالـ Docker.
- **الحقول الجديدة صارت موجودة بس لسا ما حدا عم يقارنها.** جرّبنا نغيّر `force=False` لـ `force` ونغيّر سطر منطقي، والكود مقابل الكود طلّع **صفر تغييرات**. هاد شغل الخطوتين 7 و8.
- التحليلات المحفوظة قبل هالخطوة ما فيها body لحد ما ينعاد تحليل الملفات.
