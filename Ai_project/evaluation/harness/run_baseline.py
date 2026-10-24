# evaluation/harness/run_baseline.py
"""
تشغيل النسخة المجمّدة (legacy_baseline) على العينات وحفظ المخرجات الخام كملف مجمّد.

    cd Ai_project
    set OPENROUTER_API_KEY=...
    python -m evaluation.harness.run_baseline code_vs_doc  --samples evaluation/samples/code_vs_doc
    python -m evaluation.harness.run_baseline code_vs_code --samples evaluation/samples/code_vs_code \
        --model meta-llama/llama-3.3-70b-instruct:free

صيغة العينات (ملف JSON لكل عينة):
  code_vs_doc : {"id", "language", "code", "doc": {...}}             ← توثيق جاهز بصيغة AIExplanation
                {"id", "language", "code", "doc_source": "python_docstrings"}
  code_vs_code: {"id", "language", "code_a", "code_b"}

code_vs_doc بالنسخة القديمة حتمي (String Matching، بدون LLM) فما بيحتاج --model.
code_vs_code بيستدعي الـ LLM فلازم --model مثبّت.

المخرجات: evaluation/baseline_outputs/<mode>__<UTC>.json — read-only بعد الكتابة.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import platform
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from evaluation.harness import snapshot
from evaluation.harness.llm_recorder import LLMClient
from evaluation.legacy_baseline.conflict_detection.orchestrator import ConflictOrchestrator
from evaluation.legacy_baseline.language_processors.processor_factory import ProcessorFactory

OUT_DIR = Path(__file__).resolve().parent.parent / "baseline_outputs"


# ── نفس مسار ProjectAnalyzer.analyze_code بالإنتاج، بس بالمعالجات المجمّدة ──
def analyze(code: str, language: str) -> Dict[str, Any]:
    proc = ProcessorFactory.get(language)
    ast_data = proc.parse_source_code(code)
    if ast_data.get("error"):
        raise RuntimeError(f"parse failed: {ast_data['error']}")
    features = proc.extract_features(ast_data)
    diagram = proc.generate_class_diagram_data(ast_data, features)
    features.setdefault("language", language)
    return {"class_diagram_data": diagram, "extracted_features": features}


def doc_from_python_docstrings(code: str) -> Dict[str, Any]:
    """
    محوّل docstrings → توثيق نصي بنفس شكل AIExplanation (عناوين Class:/Method:)،
    يعني نفس المدخل يلي بتشوفه الطريقة القديمة بالإنتاج.
    """
    tree = ast.parse(code)
    lines: List[str] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            lines.append(f"### Class: {node.name}")
            if ast.get_docstring(node):
                lines.append(ast.get_docstring(node))
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and ast.get_docstring(item):
                    lines.append(f"### Method: {item.name}")
                    lines.append(ast.get_docstring(item))
    return {"content": "\n".join(lines), "explanation_type": "low_level"}


def sha256_of(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def dump_items(items) -> List[Dict[str, Any]]:
    return [i.model_dump(mode="json") for i in items]


def run_sample(mode: str, s: Dict[str, Any]) -> Dict[str, Any]:
    LLMClient.start_sample(s["id"])
    out: Dict[str, Any] = {"id": s["id"], "language": s["language"]}
    try:
        if mode == "code_vs_doc":
            doc = s.get("doc")
            if doc is None and s.get("doc_source") == "python_docstrings":
                doc = doc_from_python_docstrings(s["code"])
            if doc is None:
                raise ValueError("العينة ناقصها doc أو doc_source")
            res = ConflictOrchestrator.run_code_vs_doc(analyze(s["code"], s["language"]), doc)
            out["doc_input"] = doc
            out["doc_conflicts"] = dump_items(res.doc_conflicts)
        else:
            res = ConflictOrchestrator.run_code_vs_code(
                analyze(s["code_a"], s["language"]), analyze(s["code_b"], s["language"])
            )
            out["structural_conflicts"] = dump_items(res.structural_conflicts)
            out["semantic_conflicts"] = dump_items(res.semantic_conflicts)
        out["status"] = "ok"
    except Exception as exc:
        out["status"] = "error"
        out["error"] = f"{type(exc).__name__}: {exc}"

    calls = LLMClient.pop_sample_calls()
    out["llm_calls"] = calls
    out["llm_call_count"] = len(calls)
    # الـ SemanticAnalyzer القديم بيرجّع [] بصمت إذا فشل — هون منسجّل الفشل صراحة
    out["semantic_failed"] = bool(calls) and not any(c.get("ok") for c in calls)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["code_vs_doc", "code_vs_code"])
    ap.add_argument("--samples", required=True)
    ap.add_argument("--model", help="موديل OpenRouter مثبّت (مطلوب لـ code_vs_code)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--label", default="", help="وسم اختياري لاسم الملف")
    args = ap.parse_args()

    snapshot_hash = snapshot.verify()

    if args.mode == "code_vs_code":
        if not args.model:
            sys.exit("code_vs_code بيستدعي LLM — لازم --model مثبّت")
        LLMClient.configure(model=args.model, seed=args.seed)
    else:
        # الطريقة القديمة لـ code_vs_doc ما بتستدعي LLM؛ أي استدعاء بيفشل ومنعرف فيه
        LLMClient.configure(model=None, offline=True)

    files = sorted(Path(args.samples).glob("*.json"))
    if not files:
        sys.exit(f"ما في عينات بـ {args.samples}")
    samples = [json.loads(f.read_text(encoding="utf-8")) for f in files]

    results = []
    for i, s in enumerate(samples, 1):
        print(f"[{i}/{len(samples)}] {s['id']}", flush=True)
        results.append(run_sample(args.mode, s))

    total_calls = sum(r["llm_call_count"] for r in results)
    report = {
        "mode": args.mode,
        "run_at": datetime.now(timezone.utc).isoformat(),
        "snapshot_hash": snapshot_hash,
        "samples_hash": sha256_of(samples),
        "samples_dir": str(Path(args.samples).as_posix()),
        "llm": {"model": LLMClient.model, "model_info": LLMClient.model_info,
                "temperature": 0.0, "seed": args.seed, "cache": False, "model_rotation": False,
                "provider_fallbacks": False} if args.mode == "code_vs_code" else None,
        "env": {"python": platform.python_version(), "platform": platform.platform()},
        "summary": {
            "samples": len(results),
            "errors": sum(r["status"] == "error" for r in results),
            "llm_calls_total": total_calls,
            "llm_calls_per_sample": round(total_calls / len(results), 3),
            "semantic_failed_samples": sum(r["semantic_failed"] for r in results),
            "served_models": sorted({c.get("served_model") for r in results
                                     for c in r["llm_calls"] if c.get("served_model")}),
        },
        "results": results,
    }

    OUT_DIR.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    name = f"{args.mode}__{args.label + '__' if args.label else ''}{stamp}.json"
    path = OUT_DIR / name
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    os.chmod(path, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)  # مجمّد
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    print("->", path)


if __name__ == "__main__":
    main()
