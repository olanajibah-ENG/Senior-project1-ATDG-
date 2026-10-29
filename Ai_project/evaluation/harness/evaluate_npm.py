# evaluation/harness/evaluate_npm.py
"""
قياس Code vs Code (النسخة القديمة والحالية) على بيانات ورقة NPM (Zenodo 13857646، v3).

    cd Ai_project
    python -m evaluation.harness.evaluate_npm --split dev  --stage "baseline"
    python -m evaluation.harness.evaluate_npm --split test --stage "baseline"
    python -m evaluation.harness.evaluate_npm --split dev --limit 25 --model poolside/laguna-s-2.1:free

الوحدة = التعديل (commit) كله، لأنه وسم الورقة على مستوى التعديل مش الملف:
- بيكسر  (positive): التعديلات يلي وسمها مؤلفين الورقة (external/npm_code).
- سليم   (negative): تعديلات عادية من نفس المشاريع (external/npm_code_neg، من fetch_npm_negatives.py).
  **مش موسومة من مؤلفين الورقة** — "سليمة على الأرجح".
- لكل ملف كود معدّل (قبل وبعد موجودين)، منشغّل run_code_vs_code. ملفات الاختبارات والأمثلة
  والتوثيق منتجاهلها بالجهتين (ما بتأثر على المستخدم)، ومنتجاهل الملفات المضافة أو المحذوفة كلها.
- التعديل "منبَّه عليه" إذا أي ملف فيه طلّع تغيير نوعه breaking_change أو renamed أو
  behavior_change أو logic_change. (new_feature و refactoring ما بينحسبوا تنبيه.)
- التعديل يلي ما ضل فيه ولا ملف ينفحص بينحسب "ما انفحص" وبيطلع من المقاييس.

التقسيم (seed = 42، ثابت بـ paper_sets/npm_split.csv): 20% تطوير (منفتح أخطاءه) و 80% اختبار (أرقام بس)،
بنفس نسبة بيكسر / سليم.
بدون --model: offline، يعني الفحص البنيوي بس (التحليل الدلالي بيفشل وبينسجّل).
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from evaluation.harness import snapshot
from evaluation.harness.evaluate import (
    Recorder, _enable_replay_cache, _route_production_llm_through_recorder, run_current_sample,
)
from evaluation.harness.run_baseline import run_sample as run_legacy_sample

ROOT = Path(__file__).resolve().parent.parent
EXTERNAL = ROOT / "external"
POS_DIR, NEG_DIR = EXTERNAL / "npm_code", EXTERNAL / "npm_code_neg"
LABELS_CSV = EXTERNAL / "npm_v3" / "rq2-3-4" / "analyzed_breaking_changes.csv"
PAPER_SETS = ROOT / "paper_sets"
SPLIT_CSV = PAPER_SETS / "npm_split.csv"
RESULTS = PAPER_SETS / "results"

FLAG_TYPES = {"breaking_change", "renamed", "behavior_change", "logic_change"}
LANG_BY_EXT = {".ts": "typescript", ".mts": "typescript", ".cts": "typescript", ".tsx": "typescript",
               ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript", ".cjs": "javascript"}
NOT_API = re.compile(r'(^|/)(tests?|__tests__|spec|specs|e2e|examples?|docs?|demo|fixtures?|benchmarks?|scripts)/'
                     r'|\.(test|spec|stories|e2e)\.[cm]?[jt]sx?$', re.I)
DEV_SHARE, SEED = 0.2, 42


# ─────────────────────────────────────────────────────────────────────
# التعديلات والوسوم
# ─────────────────────────────────────────────────────────────────────

def _categories() -> Dict[str, List[str]]:
    out = defaultdict(list)
    for r in csv.DictReader(open(LABELS_CSV, encoding="utf-8")):
        out[r["commit_id"].strip()].append(r["category"].strip())
    return out


def load_commits() -> List[Dict[str, Any]]:
    cats = _categories()
    commits = []
    for label, base in (("breaking", POS_DIR), ("clean", NEG_DIR)):
        for mpath in sorted(base.glob("*/*/meta.json")):
            meta = json.loads(mpath.read_text(encoding="utf-8"))
            if meta.get("status") != "ok":
                continue
            commits.append({"id": f"{meta['project']}@{meta['sha'][:10]}", "label": label,
                            "project": meta["project"], "sha": meta["sha"], "dir": mpath.parent,
                            "files": meta["files"], "categories": cats.get(meta["sha"], [])})
    return commits


def split_of(commits: List[Dict[str, Any]]) -> Dict[str, str]:
    """التقسيم بينكتب مرة وحدة وبيضل ثابت (حتى لو زادت التعديلات السليمة بعدين)."""
    split = {}
    if SPLIT_CSV.exists():
        split = {r["id"]: r["split"] for r in csv.DictReader(open(SPLIT_CSV, encoding="utf-8"))}
    new = [c for c in commits if c["id"] not in split]
    if new:
        rng = random.Random(SEED)
        for label in ("breaking", "clean"):
            group = sorted(c["id"] for c in new if c["label"] == label)
            rng.shuffle(group)
            n_dev = round(len(group) * DEV_SHARE)
            split.update({cid: ("dev" if i < n_dev else "test") for i, cid in enumerate(group)})
        with open(SPLIT_CSV, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["id", "label", "split"])
            labels = {c["id"]: c["label"] for c in commits}
            for cid in sorted(split):
                w.writerow([cid, labels.get(cid, ""), split[cid]])
    return split


def file_pairs(commit: Dict[str, Any]) -> List[Dict[str, Any]]:
    pairs = []
    for f in commit["files"]:
        lang = LANG_BY_EXT.get(Path(f["filename"]).suffix.lower())
        before, after = f.get("before"), f.get("after")
        if (not lang or NOT_API.search(f["filename"]) or not before or not after or before.startswith("unavailable") or after.startswith("unavailable")):
            continue
        a = (commit["dir"] / before).read_text(encoding="utf-8", errors="replace")
        b = (commit["dir"] / after).read_text(encoding="utf-8", errors="replace")
        if a != b:
            pairs.append({"id": f"{commit['id']}:{f['filename']}", "language": lang, "code_a": a, "code_b": b})
    return pairs


# ─────────────────────────────────────────────────────────────────────
# التشغيل والمقاييس
# ─────────────────────────────────────────────────────────────────────

def _brief(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [{k: i.get(k) for k in ("type", "category", "severity", "class_name", "member")} for i in items]


def run_commit(system: str, commit: Dict[str, Any]) -> Dict[str, Any]:
    runner = run_legacy_sample if system == "legacy" else run_current_sample
    files, llm_calls = [], 0
    for p in file_pairs(commit):
        r = runner("code_vs_code", p)
        items = (r.get("structural_conflicts") or []) + (r.get("semantic_conflicts") or [])
        llm_calls += r.get("llm_call_count", 0)
        files.append({"file": p["id"].split(":", 1)[1], "status": r["status"], "error": r.get("error"),
                      "conflicts": _brief(items),
                      "flagged": any(i.get("type") in FLAG_TYPES for i in items)})
    ok = [f for f in files if f["status"] == "ok"]
    return {"id": commit["id"], "label": commit["label"], "categories": commit["categories"],
            "files_checked": len(ok), "files_error": len(files) - len(ok), "llm_calls": llm_calls,
            "checked": bool(ok), "flagged": any(f["flagged"] for f in ok), "files": files}


def score(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    checked = [r for r in results if r["checked"]]
    pos = [r for r in checked if r["label"] == "breaking"]
    neg = [r for r in checked if r["label"] == "clean"]
    tp = sum(r["flagged"] for r in pos); fn = len(pos) - tp
    fp = sum(r["flagged"] for r in neg); tn = len(neg) - fp
    div = lambda a, b: round(a / b, 3) if b else None
    p, rc = div(tp, tp + fp), div(tp, tp + fn)
    by_cat = defaultdict(lambda: [0, 0])                    # [انكشف، المجموع] لكل نوع من أنواع الورقة
    for r in pos:
        for c in set(r["categories"]):
            by_cat[c][1] += 1
            by_cat[c][0] += r["flagged"]
    group = lambda r: "behavioral" if set(r["categories"]) <= {"change_behavior"} else "structural"
    by_group = {g: [sum(r["flagged"] for r in pos if group(r) == g), sum(group(r) == g for r in pos)]
                for g in ("structural", "behavioral")}
    return {"commits": len(results), "checked": len(checked), "not_checked": len(results) - len(checked),
            "positives": len(pos), "negatives": len(neg), "TP": tp, "FP": fp, "FN": fn, "TN": tn,
            "precision": p, "recall": rc, "f1": div(2 * p * rc, p + rc) if p and rc else None,
            "specificity": div(tn, tn + fp), "flag_rate": div(tp + fp, len(checked)),
            "recall_by_group": {g: {"found": a, "total": b, "recall": div(a, b)} for g, (a, b) in by_group.items()},
            "recall_by_category": {c: {"found": a, "total": b, "recall": div(a, b)}
                                   for c, (a, b) in sorted(by_cat.items(), key=lambda x: -x[1][1])},
            "file_errors": sum(r["files_error"] for r in results),
            "llm_calls": sum(r["llm_calls"] for r in results)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "test", "all"], default="dev")
    ap.add_argument("--systems", default="legacy,current")
    ap.add_argument("--model", help="بدونه: offline (الفحص البنيوي بس)")
    ap.add_argument("--limit", type=int, help="أول N تعديل بس (بعد ترتيب ثابت) — لقياس الـ LLM بحد الطلبات")
    ap.add_argument("--max-files", type=int, default=0, help="مع --limit: تعديلات فيها هالعدد ملفات أو أقل")
    ap.add_argument("--stage", default="")
    ap.add_argument("--no-replay", action="store_true")
    args = ap.parse_args()

    commits = load_commits()
    split = split_of(commits)
    commits = [c for c in commits if args.split == "all" or split.get(c["id"]) == args.split]
    if args.max_files:
        commits = [c for c in commits if 0 < len(file_pairs(c)) <= args.max_files]
    if args.limit:
        rng = random.Random(SEED)
        pos = [c for c in commits if c["label"] == "breaking"]; neg = [c for c in commits if c["label"] == "clean"]
        rng.shuffle(pos); rng.shuffle(neg)
        n_neg = max(1, round(args.limit * len(neg) / max(1, len(commits)))) if neg else 0
        commits = pos[:args.limit - n_neg] + neg[:n_neg]
    print(f"{len(commits)} commits ({Counter(c['label'] for c in commits)})", flush=True)

    legacy_hash = snapshot.verify()
    if args.model:
        Recorder.configure(model=args.model, seed=42)
    else:
        Recorder.configure(model=None, offline=True)
    if not args.no_replay:
        _enable_replay_cache()
    _route_production_llm_through_recorder()

    RESULTS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    set_name = f"npm_{args.split}" + (f"_limit{args.limit}" if args.limit else "")
    rows = []
    for system in args.systems.split(","):
        results = []
        for i, c in enumerate(commits, 1):
            results.append(run_commit(system, c))
            if i % 50 == 0:
                print(f"  [{system} {i}/{len(commits)}]", flush=True)
        report = score(results)
        out = RESULTS / f"{set_name}__{system}__{stamp}.json"
        out.write_text(json.dumps({"set": set_name, "system": system, "stage": args.stage,
                                   "model": args.model or "offline", "legacy_snapshot": legacy_hash,
                                   "metrics": report, "results": results},
                                  ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        rows.append({"stage": args.stage, "set": set_name, "system": system, "model": args.model or "offline",
                     **{k: report[k] for k in ("checked", "TP", "FP", "FN", "TN", "precision", "recall",
                                               "specificity", "flag_rate", "llm_calls")},
                     "recall_structural": report["recall_by_group"]["structural"]["recall"],
                     "recall_behavioral": report["recall_by_group"]["behavioral"]["recall"], "utc": stamp})
        print(json.dumps({"system": system, **{k: v for k, v in report.items() if k != "recall_by_category"}},
                         ensure_ascii=False), flush=True)
    prog = RESULTS / "progress_npm.csv"
    new = not prog.exists()
    with open(prog, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        if new:
            w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
