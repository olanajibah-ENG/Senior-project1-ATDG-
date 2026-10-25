# تقرير اختبارات الخطوة 3: تقسيم التوثيق (DocSplitter)

**التاريخ:** 2026-10-25
**ملف الاختبارات:** [`core_ai/tests/test_doc_splitter.py`](../test_doc_splitter.py)
**العينات الحقيقية:** [`core_ai/tests/fixtures/real_docs_book.json`](../fixtures/real_docs_book.json)
**البيئة:** حاوية `ai_web` (Python 3.10.20، tree-sitter 0.20.4)

## الهدف من الخطوة
فكرة DocPrism الأساسية (Local Context): بدل ما نتعامل مع التوثيق كنص واحد كبير، منقسّمه لأجزاء، ومنربط كل جزء **بالعنصر يلي بيحكي عنه بالكود**. بالخطوة 5، كل دالة رح تنبعت للذكاء الاصطناعي مع التوثيق تبعها بس.

## قبل التصميم: شو لقينا بالتوثيقات الحقيقية
فحصنا 3 توثيقات مولّدة من النظام ومحفوظة بـ Mongo، لكلاس `Book` بالجافا:

1. **الموديل ما بيلتزم بشكل العناوين.** نفس الـ constructor انكتب بثلاث أشكال: `public Book(String title, ...)` و`Book(String title, ...)` و`Book`. وبتوثيق كود جافا، الموديل كتب `setAvailable(self, available: boolean)` بصيغة بايثون.
2. **في تناقضات حقيقية بالأقسام العامة**، مش تحت الدوال. مثال: التوثيق #2 بيقول بقسم Key Capabilities "Retrieve the book's title, **author**, and ISBN"، والكود ما فيه `getAuthor`.
3. `doc_normalizer.py` موجود بس ما حدا بيستعمله.

## شو تغيّر بالكود

| الملف | التغيير |
|---|---|
| `doc_splitter.py` (جديد) | `split()` بتقسّم التوثيق لأجزاء `file` و`class` و`method`. و`match()` بتربط الأجزاء بالكود وبتطلّع 3 قوائم: `matched` و`unmatched` و`undocumented` |
| `code_doc_consistency.py` | صار يستعمل الـ splitter ليعرف "شو الموثّق"، **فوق** الـ regex القديم (union). يعني ما بينشال شي كان موثّق قبل |
| `tests/fixtures/real_docs_book.json` (جديد) | التوثيقات الحقيقية الثلاثة مع الكود تبعها، كعينات اختبار |

### قواعد التقسيم
- **الأقسام العامة** (قبل أول كلاس، أو عنوان بنفس مستوى الكلاس بعده متل `## Global Recommendations`) بتصير جزء على مستوى الملف، ومنحتفظ فيها لأنها ممكن يكون فيها تناقضات.
- `## Class:` بيبلّش جزء للكلاس، و`### Method:` و`### Constructor:` و`Function:` بيبلّشوا جزء للدالة.
- `## File: x.py` (توثيق المشروع) بيحدّد لأي ملف تابعة الأقسام يلي تحته.
- **اسم الدالة من العنوان:** منشيل `public` و`static` و`def` وغيرهم، ومناخد آخر اسم قبل `(`، ومنعدّ المعاملات بدون `self` و`cls`. والفواصل جوا `Map<String, Integer>` ما بتنحسب.
- **التوثيق المنظّم** (`{"Class.method": {...}}`) بيتحوّل لأجزاء مباشرة.
- **إذا ما في عناوين أبداً،** منرجع لبحث بأسماء الدوال بالنص: كل فقرة فيها اسم الدالة بتصير جزء إلها.

### قواعد الربط
- الكلاس بالاسم، بدون حساسية لحالة الأحرف وبدون generics (`Zoo<T>` بتصير `zoo`).
- الـ constructor بينربط بأي دالة `is_constructor` بالكلاس. يعني `Book` بالجافا، و`__init__` بالبايثون، و`constructor` بالـ JS.
- **overloads:** إذا في كذا دالة بنفس الاسم، منختار حسب عدد المعاملات بالعنوان.

## كيف شغّلنا الاختبارات
```bash
MSYS_NO_PATHCONV=1 docker compose run --rm --no-deps -T --entrypoint sh ai_web -c "pip install -q pytest; python -m pytest core_ai/tests -q; python -m evaluation.harness.snapshot"
```

## الاختبارات ونتائجها: 23 من 23 نجحت
ومع اختبارات الخطوتين 1 و2، المجموع **44 من 44**.

### 1. قراءة العناوين (10 حالات)
| العنوان | الاسم | عدد المعاملات |
|---|---|---|
| `public Book(String title, String author, String isbn)` | Book | 3 ✅ |
| `Book(String title, String author, String isbn)` | Book | 3 ✅ |
| `Book` | Book | غير معروف ✅ |
| `setAvailable(self, available: boolean)` | setAvailable | 1 ✅ (`self` ما انحسب) |
| `getTitle()` | getTitle | 0 ✅ |
| `` `place_order(self, item_id, qty)` `` | place_order | 2 ✅ |
| `public static <R> R convert(Object o, Class<R> k)` | convert | 2 ✅ |
| `__init__(self, db)` | `__init__` | 1 ✅ |
| `charge(amount: float, card_token: str) -> bool` | charge | 2 ✅ |
| `get(Map<String, Integer> m, int x)` | get | 2 ✅ |

### 2. التقسيم على التوثيقات الحقيقية
| الاختبار | شو بيفحص | النتيجة |
|---|---|---|
| `test_real_high_level_split_structure` | التوثيق #1 بيتقسّم لـ 7 أجزاء بالترتيب: ملف، كلاس، constructor، و4 دوال. والـ constructor فيه 3 معاملات ونص "Sets availability to true" | ✅ |
| `test_real_low_level_sections_go_to_their_method` | بالتوثيق التفصيلي، Parameters وReturns وغيرهم بيروحوا للدالة الصح، وما في تسريب من القسم يلي قبلها | ✅ |
| `test_file_level_claims_are_kept` | جملة "title, **author**, and ISBN" محفوظة بجزء الملف، لحتى نقدر نكشفها كتناقض بالخطوة 5 | ✅ |

### 3. الربط بالكود
| الاختبار | شو بيفحص | النتيجة |
|---|---|---|
| `test_real_docs_match_constructor_and_methods` | بالتوثيقات الثلاثة، الـ constructor بينربط بالـ constructor الحقيقي بالكود، وما في ولا جزء ما انربط | ✅ |
| `test_real_partial_doc_reports_coverage_not_errors` | التوثيق المختصر #2 بيطلّع `getIsbn` و`getTitle` و`isAvailable` كـ "غير موثّقة"، بقائمة منفصلة عن التناقضات | ✅ |
| `test_documented_method_missing_from_code_is_unmatched` | إذا التوثيق بيحكي عن `getAuthor()` والكود ما فيه ياها، بتطلع بقائمة `unmatched`. **هاد مؤشر جديد ما كان النظام يشوفه** | ✅ |
| `test_overloads_resolved_by_param_count` | `Repo()` و`Repo(String url)`: التوثيق بيحكي عن `Repo(String url)`، فبينربط بالـ overload الصح، والتاني بيطلع غير موثّق | ✅ |

### 4. أشكال توثيق تانية
| الاختبار | شو بيفحص | النتيجة |
|---|---|---|
| `test_project_doc_with_file_sections` | توثيق مشروع فيه `## File:` لملفين: كل دالة بتنربط بملفها وكلاسها، و`## Global Architectural Recommendations` بيرجع لمستوى الملف | ✅ |
| `test_structured_dict_doc` | التوثيق المنظّم كقاموس بيتحوّل لجزء، وفيه عدد المعاملات والـ raises | ✅ |
| `test_doc_without_headings_uses_keyword_fallback` | توثيق نص عادي بدون عناوين: `place_order` المذكورة بالنص بتنربط | ✅ |
| `test_empty_doc` | توثيق فاضي: ما بيوقع، والدوال الثلاثة غير موثّقة | ✅ |

### 5. أثره على الـ checker الحالي
| الاختبار | شو بيفحص | النتيجة |
|---|---|---|
| `test_checker_no_longer_flags_documented_constructor` | `Book` ما عادت تنحسب "غير موثّقة" بأي من التوثيقات الثلاثة | ✅ |
| `test_checker_partial_doc_still_reports_coverage_gaps` | تنبيهات "غير موثّقة" الحقيقية لسا موجودة. شيلها من التناقضات هو شغل الخطوة 6 | ✅ |

## قبل وبعد على التوثيقات الحقيقية
شغّلنا الـ checker على التوثيقات الثلاثة بثلاث نسخ: النسخة المجمّدة، والكود بعد الخطوتين 1 و2 (`722d170`)، والكود بعد الخطوة 3.

| التوثيق | النسخة المجمّدة (الأصلية) | بعد الخطوتين 1 و2 | بعد الخطوة 3 |
|---|---|---|---|
| high-level #1 | `setAvailable` ❌ | `Book` ❌ | **ولا تنبيه** ✅ |
| high-level #2 | `getTitle`، `getIsbn`، `isAvailable`، `setAvailable` ❌ | `Book`، `getTitle`، `getIsbn`، `isAvailable` | `getTitle`، `getIsbn`، `isAvailable` |
| low-level | ولا تنبيه | `Book` ❌ | **ولا تنبيه** ✅ |
| **مجموع التنبيهات الغلط** | **2** (`setAvailable` ×2) | **3** (`Book` ×3) | **0** |

تنبيهات `getTitle` و`getIsbn` و`isAvailable` مش غلط تقنياً، لأنه التوثيق المختصر فعلاً ما ذكرهم. بس هي **تغطية، مش تناقض**، ورح تنتقل للإحصائيات بالخطوة 6.

### من وين إجا كل تنبيه غلط
- **`setAvailable` بالنسخة الأصلية:** توقيعات الجافا بتبلّش بـ `+ ` (مثلاً `+ setAvailable(available: boolean): void`)، والدالة القديمة `_parse_signature` ما بتفهم هالشكل، فكانت تعتبر عدد المعاملات صفر. التوثيق فيه معامل واحد، فكان يطلع "Signature mismatch: doc mentions 1 params, code has 0". **الخطوة 1 صلّحت هالشي بالصدفة**، لأنه صار في حقل `parameters` بيعطي العدد الصحيح.
- **`Book` بعد الخطوتين 1 و2:** الخطوة 1 خلّت constructors الجافا تظهر بالمخطط، بس الـ regex القديم بيدوّر على `Method:` بس وما بيعرف `Constructor:`. **هاد خطأ سببته الخطوة 1، وانصلح بهالخطوة.**

## النسخة المجمّدة
`python -m evaluation.harness.snapshot` طلّع `ok: a8649b22…`، يعني ما انلمست.

## شو لسا ما انحل (مقصود، للخطوات الجاية)
| المشكلة | متى بتنحل |
|---|---|
| التناقض الحقيقي "author" بالتوثيق #2 لسا ما بينكشف. الـ splitter بيحفظه بجزء الملف، بس كشفه بدو تحليل دلالي | الخطوتين 4 و5 |
| التوثيق يلي بيحكي عن دالة مش موجودة (`unmatched`) لسا ما بيطلع كتنبيه | الخطوة 6 |
| تنبيهات "غير موثّقة" لسا بتنحسب تناقضات | الخطوة 6 |
| `_parse_signature` لسا ما بتفهم `+ ` بأول التوقيع. هالشي بيأثر بس على التحليلات المحفوظة قبل الخطوة 1 (يلي ما فيها `parameters`) | الخطوة 6 |
| البحث بالأسماء (fallback) بسيط: بياخد كل فقرة فيها اسم الدالة، حتى لو الاسم انذكر عرضاً | مقبول كـ fallback |
