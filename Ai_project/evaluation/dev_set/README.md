# مجموعة التطوير (dev set)

مجموعة عينات صغيرة **معروف جوابها الصح**، منقيس عليها النظام القديم والجديد **بعد كل خطوة**، لحتى نعرف إذا النتيجة عم تتحسن أو تخرب.

> ⚠️ **هاي مش مجموعة الاختبار النهائية.** هي صغيرة ونحنا وسمناها، فبتعطي مؤشر على الاتجاه بس.
> الدليل النهائي للتقرير هو DocPrism و Cascade (`evaluation/samples/`)، ويلي **ما منجرّب عليهم خلال التطوير**، لحتى ما نفصّل النظام على عينات الاختبار.

## المحتوى

| الملف | المحتوى |
|---|---|
| `build_samples.py` | بيولّد العينات كملفات JSON. العينات مكتوبة جواته كنص لحتى تنقرأ بسهولة |
| `code_vs_doc/` | 10 عينات (7 مكتوبة + 3 توثيقات حقيقية من Mongo)، فيهم **46 عنصر موسوم** |
| `code_vs_code/` | 17 عينة (15 Python + 2 Java)، فيهم **20 عنصر موسوم** |
| `labels_code_vs_doc.csv` | الوسم حسب `labeling/guide_code_vs_doc.md` |
| `labels_code_vs_code.csv` | الوسم حسب `labeling/guide_code_vs_code.md` (Q1 / Q2 / Q3) |
| `results/` | نتائج كل تشغيل (JSON) و `progress_<mode>.csv` |
| `PROGRESS.md` | جدول التقدّم مع شرح النتائج |

### توزيع الوسم

**Code vs Doc (46 عنصر):** Consistent 26، Direct_Mismatch 6، Over_Promise 8، Under_Promise 2، skip 4

**Code vs Code (20 عنصر):**

| التركيبة (Q1 Q2 Q3) | العدد | أمثلة |
|---|---|---|
| 1 0 x (بنيوي بس) | 10 | rename، حذف دالة، إضافة parameter، دالة → property |
| 0 1 1 (سلوكي بس، الأخطر) | 4 | `None` بدل `raise`، `get(k, -1)` بدل `d[k]`، شيل فحص الرصيد |
| 1 1 1 (بنيوي + سلوكي) | 2 | تغيير القيمة الافتراضية، تغيير نوع الإرجاع |
| 0 0 0 (ما في تغيير حقيقي) | 4 | تعليقات بس، refactor مكافئ، `Math.max` |

## ⚠️ الوسم لسا مسودة
كل سطر بالوسم مكتوب بعمود `notes` إنه `draft:claude`. **لازم شخصين من الفريق يراجعوه** متل ما بيطلب دليل الوسم. بعد المراجعة، منشيل `draft:claude` ومنعيد القياس.

## التشغيل
بالـ Docker، لأنه معالج الجافا ما بيشتغل على جهاز التطوير:
```bash
# Code vs Doc (حالياً ما في LLM بالنسختين)
MSYS_NO_PATHCONV=1 docker compose run --rm --no-deps -T --entrypoint python ai_web \
  -m evaluation.harness.evaluate code_vs_doc --stage "after step N"

# Code vs Code (بيحتاج LLM)
MSYS_NO_PATHCONV=1 docker compose run --rm --no-deps -T --entrypoint python ai_web \
  -m evaluation.harness.evaluate code_vs_code --stage "after step N" --model poolside/laguna-s-2.1:free
```
- النسخة القديمة بتنحسب **مرة وحدة** وبتنحفظ بـ `results/legacy__*.json`، وبعدها بيعاد استعمال النتيجة، لأنه الكود مجمّد. هيك منوفّر استدعاءات LLM.
- إذا تعدّلت العينات بـ `build_samples.py`: `python -m evaluation.dev_set.build_samples`، والنسخة القديمة بتنحسب من جديد لحالها لأنه البصمة تغيّرت.

## الموديل
`poolside/laguna-s-2.1:free`: انختار بـ 2026-10-25. موديلات المشروع الأصلية (`llama-3.3-70b:free` وغيرها) ما عادت موجودة بـ OpenRouter.
- من بين 6 موديلات مجانية جرّبناها، 4 جاوبوا صح على حالة "Raises KeyError مقابل return None". هاد كان **الأسرع (5 ثواني) والأقل tokens (186)**.
- **البديل:** `cohere/north-mini-code:free`.
- الحساب على الـ free tier، وفي حد يومي للاستدعاءات.
