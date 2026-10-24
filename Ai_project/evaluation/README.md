# evaluation — المرحلة 0 من خطة الإثبات

| المجلد | المحتوى |
|---|---|
| `legacy_baseline/` | نسخة مجمّدة من `conflict_detection` و `language_processors` كما كانت قبل أي تحسين. بصمتها بـ `MANIFEST.json`. **ممنوع التعديل.** |
| `harness/llm_recorder.py` | LLM client حتمي: temperature 0، seed ثابت، بدون cache، موديل مثبّت بدون rotation، وبيسجّل الرد الخام والموديل اللي فعلياً ردّ |
| `harness/run_baseline.py` | بيشغّل النسخة المجمّدة على العينات وبيكتب مخرجات خام read-only بـ `baseline_outputs/` |
| `harness/snapshot.py` | التحقق من بصمة النسخة المجمّدة |
| `samples/` | العينات (فاضي لحد ما نختارها) |
| `labeling/` | دليلَي الوسم، قوالب CSV، و `kappa.py` |

```
python -m evaluation.harness.snapshot
python -m evaluation.harness.run_baseline code_vs_doc  --samples evaluation/samples/code_vs_doc
python -m evaluation.harness.run_baseline code_vs_code --samples evaluation/samples/code_vs_code --model <pinned-model>
python -m evaluation.labeling.kappa a.csv b.csv --column label
```
