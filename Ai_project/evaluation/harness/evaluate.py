# evaluation/harness/evaluate.py
"""
قياس النظام القديم (legacy_baseline) والحالي (core_ai) على مجموعة التطوير وحساب الـ metrics.

    cd Ai_project
    python -m evaluation.harness.evaluate code_vs_doc  --stage "after step 3"
    python -m evaluation.harness.evaluate code_vs_code --stage "after step 3" --model poolside/laguna-s-2.1:free

بيانات الأوراق (evaluation/paper_sets، من build_paper_sets.py):
    python -m evaluation.harness.evaluate code_vs_doc --set docprism_ablation --stage "after step 3"
    python -m evaluation.harness.evaluate code_vs_doc --set cascade_balanced  --stage "after step 3"

الافتراضي: --samples evaluation/dev_set/<mode>  --labels evaluation/dev_set/labels_<mode>.csv

- كل استدعاءات الـ LLM (بالنسختين) بتمرق من evaluation.harness.llm_recorder: temperature 0،
  seed ثابت، موديل مثبّت.
- replay cache (evaluation/llm_cache/): نفس الموديل + نفس الـ seed + نفس الـ prompt حرفياً → بيرجع
  الرد المسجّل بدل طلب جديد (الرد كان رح يطلع نفسه، وبيوفّر من حد الـ free tier).
  --no-replay بيجبر طلبات جديدة. كل استدعاء بينسجّل إذا كان replayed.
- نتيجة النسخة القديمة بتنحفظ مرة وحدة وبيعاد استعمالها (هي مجمّدة) طالما العينات والموديل ما تغيّروا.
  --rerun-legacy بيجبر إعادة التشغيل.
- المخرجات: <set>/../results/<set>__<system>__<UTC>.json + سطر بـ progress_<set>.csv
- إذا ملف الوسم فيه pair_id (CASCADE): بينحسب PFP = من المتناقضة يلي انكشفت صح، نسبة يلي
  نسختها المصلّحة ما انبّه عليها.

تعريف التنبؤ (prediction) — بيعتمد على مخرجات النظام بس، مش على آليته:
  code_vs_doc : العنصر "منبَّه عليه" إذا في ConflictItem عليه (غير Overall) و is_flagged مش False.
                الصح (positive) = Direct_Mismatch أو Over_Promise (حسب DocPrism: Under_Promise ما بيتعرض).
  code_vs_code: Q1 = في تغيير بنيوي معلن على العنصر، Q2 = في تغيير سلوكي معلن، Q3 = معلن breaking.
أي تنبيه على عنصر مش موجود بملف الوسم بينحسب إنذار كاذب (unlabeled flag).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from evaluation.harness import snapshot
from evaluation.harness.llm_recorder import LLMClient as Recorder
from evaluation.harness.run_baseline import doc_from_python_docstrings, run_sample as run_legacy_sample

ROOT = Path(__file__).resolve().parent.parent          # evaluation/
DEV = ROOT / "dev_set"
PAPER_SETS = ROOT / "paper_sets"
LLM_CACHE = ROOT / "llm_cache"

# Inconsistent = وسم ثنائي من بيانات الأوراق (DocPrism / CASCADE)
POSITIVE_DOC_LABELS = {"Direct_Mismatch", "Over_Promise", "Inconsistent"}
STRUCTURAL_TYPES = {"renamed", "refactoring", "new_feature"}
BEHAVIORAL_TYPES = {"behavior_change", "logic_change"}


# ─────────────────────────────────────────────────────────────────────
# تشغيل النسخة الحالية (core_ai) بنفس شروط النسخة القديمة
# ─────────────────────────────────────────────────────────────────────

def _route_production_llm_through_recorder() -> None:
    """أي LLMClient.call_model بكود الإنتاج بيمرق من الـ recorder الحتمي."""
    from core_ai.ai_engine import llm_client as prod
    prod.LLMClient.call_model = Recorder.call_model


def _enable_replay_cache() -> None:
    """نفس (موديل، seed، system، user) → الرد المسجّل. بيلفّ Recorder.call_model للنسختين."""
    original = Recorder.call_model
    LLM_CACHE.mkdir(exist_ok=True)

    def call_model(system_prompt: str, user_prompt: str, **kwargs):
        key = hashlib.sha256(json.dumps([Recorder.model, Recorder.seed, system_prompt, user_prompt],
                                        ensure_ascii=False).encode()).hexdigest()
        path = LLM_CACHE / f"{key}.json"
        if path.exists() and not Recorder.offline:
            cached = json.loads(path.read_text(encoding="utf-8"))
            Recorder._calls.append({"sample_id": Recorder._current_sample, "requested_model": Recorder.model,
                                    "ok": True, "replayed": True, "served_model": cached.get("served_model"),
                                    "raw_response": cached["response"], "cache_key": key})
            return cached["response"]
        response = original(system_prompt, user_prompt, **kwargs)
        last = Recorder._calls[-1] if Recorder._calls else {}
        if response and last.get("ok"):
            path.write_text(json.dumps({"model": Recorder.model, "seed": Recorder.seed,
                                        "served_model": last.get("served_model"), "response": response},
                                       ensure_ascii=False), encoding="utf-8")
        return response

    Recorder.call_model = staticmethod(call_model)


def _analyze_current(code: str, language: str) -> Dict[str, Any]:
    from core_ai.language_processors.processor_factory import ProcessorFactory
    proc = ProcessorFactory.get(language)
    ast_data = proc.parse_source_code(code)
    if ast_data.get("error"):
        raise RuntimeError(f"parse failed: {ast_data['error']}")
    features = proc.extract_features(ast_data)
    diagram = proc.generate_class_diagram_data(ast_data, features)
    features.setdefault("language", language)
    return {"class_diagram_data": diagram, "extracted_features": features}


def run_current_sample(mode: str, s: Dict[str, Any]) -> Dict[str, Any]:
    from core_ai.services.conflict_detection.orchestrator import ConflictOrchestrator
    Recorder.start_sample(s["id"])
    out: Dict[str, Any] = {"id": s["id"], "language": s["language"]}
    dump = lambda items: [i.model_dump(mode="json") for i in items]
    try:
        if mode == "code_vs_doc":
            doc = s.get("doc") or doc_from_python_docstrings(s["code"])
            res = ConflictOrchestrator.run_code_vs_doc(_analyze_current(s["code"], s["language"]), doc)
            out["doc_conflicts"] = dump(res.doc_conflicts)
        else:
            res = ConflictOrchestrator.run_code_vs_code(
                _analyze_current(s["code_a"], s["language"]), _analyze_current(s["code_b"], s["language"]))
            out["structural_conflicts"] = dump(res.structural_conflicts)
            out["semantic_conflicts"] = dump(res.semantic_conflicts)
        out["status"] = "ok"
    except Exception as exc:
        out["status"] = "error"
        out["error"] = f"{type(exc).__name__}: {exc}"
    calls = Recorder.pop_sample_calls()
    out["llm_calls"] = calls
    out["llm_call_count"] = len(calls)
    out["semantic_failed"] = bool(calls) and not any(c.get("ok") for c in calls)
    return out


# ─────────────────────────────────────────────────────────────────────
# metrics
# ─────────────────────────────────────────────────────────────────────

def _key(c: Dict[str, Any]) -> str:
    cls, member = c.get("class_name") or "", c.get("member")
    return (f"{cls}.{member}" if member else cls).lower()


def _prf(tp: int, fp: int, fn: int, tn: int) -> Dict[str, Any]:
    p = tp / (tp + fp) if tp + fp else None
    r = tp / (tp + fn) if tp + fn else None
    f1 = 2 * p * r / (p + r) if p and r else (0.0 if p is not None and r is not None else None)
    spec = tn / (tn + fp) if tn + fp else None
    rnd = lambda x: None if x is None else round(x, 3)
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": rnd(p), "recall": rnd(r), "f1": rnd(f1), "specificity": rnd(spec)}


def load_labels(path: Path) -> Dict[str, Dict[str, Dict[str, str]]]:
    by_sample: Dict[str, Dict[str, Dict[str, str]]] = defaultdict(dict)
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            by_sample[row["sample_id"]][row["element"].lower()] = row
    return by_sample


def score_code_vs_doc(results: List[Dict[str, Any]], labels) -> Dict[str, Any]:
    rows, unlabeled = [], []
    for r in results:
        conflicts = [c for c in r.get("doc_conflicts", []) if c.get("class_name") != "Overall"]
        flagged = {_key(c) for c in conflicts if c.get("is_flagged") is not False}
        predicted_label = {_key(c): c.get("doc_label") for c in conflicts if c.get("doc_label")}
        sample_labels = labels.get(r["id"], {})
        for el, row in sample_labels.items():
            rows.append({"sample": r["id"], "element": row["element"], "label": row["label"],
                         "pair_id": row.get("pair_id") or "",
                         "flagged": el in flagged, "predicted_label": predicted_label.get(el)})
        unlabeled += [{"sample": r["id"], "element": k} for k in sorted(flagged - set(sample_labels))]

    def binary(subset, extra_fp):
        tp = sum(x["flagged"] and x["label"] in POSITIVE_DOC_LABELS for x in subset)
        fn = sum(not x["flagged"] and x["label"] in POSITIVE_DOC_LABELS for x in subset)
        fp = sum(x["flagged"] and x["label"] not in POSITIVE_DOC_LABELS for x in subset) + extra_fp
        tn = sum(not x["flagged"] and x["label"] not in POSITIVE_DOC_LABELS for x in subset)
        m = _prf(tp, fp, fn, tn)
        m["flag_rate"] = round((tp + fp) / (len(subset) + extra_fp), 3) if subset else None
        return m

    by_label = {}
    for lab in sorted({x["label"] for x in rows}):
        sub = [x for x in rows if x["label"] == lab]
        by_label[lab] = {"n": len(sub), "flagged": sum(x["flagged"] for x in sub)}

    # PFP: من المتناقضة يلي انكشفت صح، قديش منها نسختها المصلّحة (نفس pair_id) ما انبّه عليها
    pfp = None
    pairs = defaultdict(dict)
    for x in rows:
        if x["pair_id"]:
            pairs[x["pair_id"]]["pos" if x["label"] in POSITIVE_DOC_LABELS else "neg"] = x
    detected = [p for p in pairs.values() if "pos" in p and "neg" in p and p["pos"]["flagged"]]
    if pairs:
        clean_fix = sum(not p["neg"]["flagged"] for p in detected)
        pfp = {"value": round(clean_fix / len(detected), 3) if detected else None,
               "fixed_left_clean": clean_fix, "detected_pairs": len(detected), "pairs": len(pairs)}

    with_label = [x for x in rows if x["predicted_label"] and x["label"] != "skip"]
    return {
        "elements": len(rows),
        "all": binary(rows, len(unlabeled)),
        "documented_only": binary([x for x in rows if x["label"] != "skip"], len(unlabeled)),
        "flags_by_true_label": by_label,
        "pfp": pfp,
        "label_accuracy": (round(sum(x["predicted_label"] == x["label"] for x in with_label) / len(with_label), 3)
                           if with_label else None),
        "unlabeled_flags": unlabeled,
        "rows": rows,
    }


def score_code_vs_code(results: List[Dict[str, Any]], labels) -> Dict[str, Any]:
    rows, unlabeled = [], []
    for r in results:
        pred: Dict[str, Dict[str, bool]] = defaultdict(lambda: {"any": False, "Q1": False, "Q2": False, "Q3": False})
        for source in ("structural_conflicts", "semantic_conflicts"):
            for c in r.get(source, []):
                p = pred[_key(c)]
                p["any"] = True
                typ, decision = c.get("type"), c.get("decision")
                if source == "structural_conflicts" or typ in STRUCTURAL_TYPES \
                        or decision in ("structural_only", "structural_and_behavioral"):
                    p["Q1"] = True
                if typ in BEHAVIORAL_TYPES or decision in ("behavioral_candidate", "structural_and_behavioral"):
                    p["Q2"] = True
                if typ == "breaking_change" or c.get("severity") in ("critical", "high") \
                        or c.get("risk_level") == "critical":
                    p["Q3"] = True
        sample_labels = labels.get(r["id"], {})
        for el, row in sample_labels.items():
            p = pred.get(el, {"any": False, "Q1": False, "Q2": False, "Q3": False})
            rows.append({"sample": r["id"], "element": row["element"],
                         **{q: row[q] == "1" for q in ("Q1", "Q2", "Q3")},
                         **{f"pred_{q}": p[q] for q in ("any", "Q1", "Q2", "Q3")}})
        unlabeled += [{"sample": r["id"], "element": k} for k in sorted(set(pred) - set(sample_labels))]

    def per_q(q):
        tp = sum(x[q] and x[f"pred_{q}"] for x in rows)
        fp = sum(not x[q] and x[f"pred_{q}"] for x in rows)
        fn = sum(x[q] and not x[f"pred_{q}"] for x in rows)
        tn = sum(not x[q] and not x[f"pred_{q}"] for x in rows)
        return _prf(tp, fp, fn, tn)

    real = lambda x: x["Q1"] or x["Q2"]
    tp = sum(real(x) and x["pred_any"] for x in rows)
    fn = sum(real(x) and not x["pred_any"] for x in rows)
    fp = sum(not real(x) and x["pred_any"] for x in rows) + len(unlabeled)
    tn = sum(not real(x) and not x["pred_any"] for x in rows)
    return {
        "elements": len(rows),
        "change_detection": _prf(tp, fp, fn, tn),
        "Q1_interface": per_q("Q1"),
        "Q2_behavior": per_q("Q2"),
        "Q3_breaking": per_q("Q3"),
        "unlabeled_flags": unlabeled,
        "rows": rows,
    }


# ─────────────────────────────────────────────────────────────────────
# main
# ─────────────────────────────────────────────────────────────────────

def _hash_files(paths) -> str:
    h = hashlib.sha256()
    for p in sorted(paths):
        h.update(p.as_posix().encode())
        h.update(p.read_bytes().replace(b"\r\n", b"\n"))
    return h.hexdigest()


def current_code_hash() -> str:
    core = ROOT.parent / "core_ai"
    return _hash_files(list((core / "services" / "conflict_detection").rglob("*.py"))
                       + list((core / "language_processors").glob("*.py")))


def run_system(system: str, mode: str, samples, model: Optional[str]) -> List[Dict[str, Any]]:
    runner = run_legacy_sample if system == "legacy" else run_current_sample
    out = []
    for i, s in enumerate(samples, 1):
        print(f"  [{system} {i}/{len(samples)}] {s['id']}", flush=True)
        out.append(runner(mode, s))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["code_vs_doc", "code_vs_code"])
    ap.add_argument("--set", help="مجموعة من evaluation/paper_sets (مثلاً docprism_ablation، cascade_balanced)")
    ap.add_argument("--samples")
    ap.add_argument("--labels")
    ap.add_argument("--systems", default="legacy,current")
    ap.add_argument("--model", help="موديل OpenRouter مثبّت (إذا ما انعطى: offline، وأي استدعاء LLM بيفشل وبينسجّل)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--stage", default="", help="اسم المرحلة لجدول التقدّم، مثلاً 'after step 3'")
    ap.add_argument("--rerun-legacy", action="store_true")
    ap.add_argument("--no-replay", action="store_true", help="ما تستعمل ردود LLM مسجّلة")
    args = ap.parse_args()

    if args.set:
        samples_dir = PAPER_SETS / args.set
        labels_path = PAPER_SETS / f"labels_{args.set}.csv"
        results_dir, set_name = PAPER_SETS / "results", args.set
    else:
        samples_dir = Path(args.samples) if args.samples else DEV / args.mode
        labels_path = Path(args.labels) if args.labels else DEV / f"labels_{args.mode}.csv"
        results_dir, set_name = DEV / "results", args.mode
    samples = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(samples_dir.glob("*.json"))]
    if not samples:
        sys.exit(f"ما في عينات بـ {samples_dir}")
    labels = load_labels(labels_path)

    legacy_hash = snapshot.verify()
    if args.model:
        Recorder.configure(model=args.model, seed=args.seed)
    else:
        Recorder.configure(model=None, offline=True)
    if not args.no_replay:
        _enable_replay_cache()
    _route_production_llm_through_recorder()

    samples_hash = hashlib.sha256(json.dumps(samples, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    results_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    scorer = score_code_vs_doc if args.mode == "code_vs_doc" else score_code_vs_code
    model_tag = (args.model or "offline").replace("/", "_").replace(":", "_")

    summary_rows = []
    for system in [s.strip() for s in args.systems.split(",") if s.strip()]:
        cache = results_dir / f"legacy__{set_name}__{samples_hash[:12]}__{model_tag}.json"
        if system == "legacy" and cache.exists() and not args.rerun_legacy:
            print(f"legacy: reusing {cache.name}")
            results = json.loads(cache.read_text(encoding="utf-8"))["results"]
        else:
            print(f"{system}: running {len(samples)} samples")
            results = run_system(system, args.mode, samples, args.model)
            if system == "legacy":
                cache.write_text(json.dumps({"snapshot_hash": legacy_hash, "results": results},
                                            ensure_ascii=False, indent=1), encoding="utf-8")

        metrics = scorer(results, labels)
        calls = [c for r in results for c in r.get("llm_calls", [])]
        report = {
            "mode": args.mode, "set": set_name, "system": system, "stage": args.stage,
            "run_at": datetime.now(timezone.utc).isoformat(),
            "code_hash": legacy_hash if system == "legacy" else current_code_hash(),
            "samples_hash": samples_hash, "labels_file": labels_path.name,
            "llm": {"model": args.model, "model_info": Recorder.model_info, "seed": args.seed,
                    "calls": len(calls), "replayed": sum(bool(c.get("replayed")) for c in calls),
                    "failed_samples": sum(r.get("semantic_failed", False) for r in results)},
            "errors": [{"id": r["id"], "error": r.get("error")} for r in results if r.get("status") == "error"],
            "metrics": metrics,
            "results": results,
        }
        out = results_dir / f"{set_name}__{system}__{stamp}.json"
        out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        summary_rows.append(_progress_row(args, system, report))
        print(f"  -> {out.relative_to(ROOT.parent)}")

    _append_progress(results_dir / f"progress_{set_name}.csv", summary_rows)
    _print_table(args.mode, summary_rows)


def _progress_row(args, system, report) -> Dict[str, Any]:
    m = report["metrics"]
    main_m = m["all"] if args.mode == "code_vs_doc" else m["change_detection"]
    row = {"stage": args.stage, "system": system, "run_at": report["run_at"][:19],
           "code_hash": report["code_hash"][:12], "model": args.model or "offline",
           "elements": m["elements"], **{k: main_m[k] for k in ("precision", "recall", "f1", "specificity", "tp", "fp", "fn", "tn")},
           "unlabeled_flags": len(m["unlabeled_flags"]), "llm_calls": report["llm"]["calls"],
           "llm_replayed": report["llm"]["replayed"],
           "llm_failed_samples": report["llm"]["failed_samples"], "errors": len(report["errors"])}
    if args.mode == "code_vs_doc":
        row["flag_rate"] = main_m["flag_rate"]
        row["label_accuracy"] = m["label_accuracy"]
        row["pfp"] = (m.get("pfp") or {}).get("value")
    else:
        for q in ("Q1_interface", "Q2_behavior", "Q3_breaking"):
            row[f"{q}_f1"] = m[q]["f1"]
    return row


def _append_progress(path: Path, rows: List[Dict[str, Any]]) -> None:
    new = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        if new:
            w.writeheader()
        w.writerows(rows)


def _print_table(mode: str, rows: List[Dict[str, Any]]) -> None:
    cols = [c for c in rows[0] if c not in ("run_at", "code_hash", "model")]
    print("\n| " + " | ".join(cols) + " |")
    print("|" + "---|" * len(cols))
    for r in rows:
        print("| " + " | ".join("—" if r[c] is None else str(r[c]) for c in cols) + " |")


if __name__ == "__main__":
    main()
