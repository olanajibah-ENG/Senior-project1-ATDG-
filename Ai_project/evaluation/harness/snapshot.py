# evaluation/harness/snapshot.py
"""
بصمة النسخة المجمّدة (legacy_baseline).

المشروع ما عليه git، فبدل commit hash منحسب sha256 لكل ملف بالنسخة المجمّدة،
وبصمة إجمالية منهن. الـ runner بيرفض يشتغل إذا البصمة الحالية ما طابقت
MANIFEST.json — يعني إذا حدا عدّل النسخة المجمّدة بالغلط.

    python -m evaluation.harness.snapshot --write    # مرة وحدة وقت التجميد
    python -m evaluation.harness.snapshot            # تحقق
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SNAPSHOT_DIR = Path(__file__).resolve().parent.parent / "legacy_baseline"
MANIFEST = SNAPSHOT_DIR / "MANIFEST.json"


def file_hashes() -> dict:
    out = {}
    for p in sorted(SNAPSHOT_DIR.rglob("*.py")):
        if "__pycache__" in p.parts:
            continue
        # نوحّد نهايات الأسطر عشان البصمة ما تتغير بين Windows و Linux
        data = p.read_bytes().replace(b"\r\n", b"\n")
        out[p.relative_to(SNAPSHOT_DIR).as_posix()] = hashlib.sha256(data).hexdigest()
    return out


def combined_hash(hashes: dict) -> str:
    h = hashlib.sha256()
    for name, digest in sorted(hashes.items()):
        h.update(f"{name}:{digest}\n".encode())
    return h.hexdigest()


def verify() -> str:
    """بيرجع البصمة الإجمالية، أو بيرمي إذا النسخة المجمّدة تغيّرت."""
    if not MANIFEST.exists():
        raise RuntimeError("MANIFEST.json مش موجود — شغّل snapshot --write أول")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    current = file_hashes()
    if current != manifest["files"]:
        changed = sorted(
            set(current) ^ set(manifest["files"])
            | {k for k in current.keys() & manifest["files"].keys() if current[k] != manifest["files"][k]}
        )
        raise RuntimeError(f"النسخة المجمّدة تغيّرت بعد التجميد: {changed}")
    return manifest["snapshot_hash"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--amend", metavar="REASON",
                    help="إعادة تجميد بعد تعديل موثّق — بيضيف السبب والملفات المتغيرة للـ MANIFEST")
    args = ap.parse_args()
    if args.amend:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        hashes = file_hashes()
        changed = sorted(k for k in hashes.keys() | manifest["files"].keys()
                         if hashes.get(k) != manifest["files"].get(k))
        if not changed:
            sys.exit("ما في ملفات متغيرة — ما في شي لتوثيقه")
        manifest.setdefault("amendments", []).append({
            "at": datetime.now(timezone.utc).isoformat(),
            "reason": args.amend,
            "files": changed,
            "previous_hash": manifest["snapshot_hash"],
        })
        manifest["files"] = hashes
        manifest["snapshot_hash"] = combined_hash(hashes)
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print("amended:", manifest["snapshot_hash"], changed)
    elif args.write:
        if MANIFEST.exists():
            sys.exit("MANIFEST.json موجود — النسخة مجمّدة أصلاً، ما رح أكتب فوقه")
        hashes = file_hashes()
        MANIFEST.write_text(json.dumps({
            "frozen_at": datetime.now(timezone.utc).isoformat(),
            "source": "core_ai/services/conflict_detection + core_ai/language_processors",
            "modifications": [
                "conflict_detection/semantic_analyzer.py: import LLMClient من "
                "evaluation.harness.llm_recorder بدل core_ai.ai_engine.llm_client "
                "(temperature 0، بدون cache، موديل مثبّت). باقي المنطق بدون أي تعديل."
            ],
            "snapshot_hash": combined_hash(hashes),
            "files": hashes,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print("frozen:", combined_hash(hashes))
    else:
        print("ok:", verify())


if __name__ == "__main__":
    main()
