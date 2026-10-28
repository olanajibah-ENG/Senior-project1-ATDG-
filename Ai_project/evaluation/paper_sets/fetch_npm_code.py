"""
بيجيب الكود قبل وبعد لكل commit ببيانات ورقة NPM (Zenodo 13857646، النسخة v3 المفتوحة).

    python -m evaluation.paper_sets.fetch_npm_code            (بيكمّل من وين وقف)

المدخل : evaluation/external/npm_v3/rq2-3-4/analyzed_breaking_changes.csv
المخرج : evaluation/external/npm_code/<owner>__<repo>/<sha>/
            meta.json          — الملفات المتغيرة، الـ parent، والـ patch لكل ملف
            before/<path>      — الملف قبل الـ commit (من الـ parent)
            after/<path>       — الملف بعد الـ commit
بيقرأ GITHUB_TOKEN من متغيرات البيئة أو من ملف .env بجذر المشروع.

الملفات يلي منجيبها: .js .jsx .mjs .cjs .ts .tsx .mts .cts (بما فيها .d.ts)، ومنتجاهل
node_modules و dist و build و الملفات الأكبر من MAX_BYTES. الـ commit يلي فيه أكتر من
MAX_FILES ملف كود بيتسجّل بس بدون تنزيل (ضخم، غالباً إعادة هيكلة أو build).
"""
import csv
import json
import os
import re
import sys
import time
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
EXTERNAL = HERE.parent / "external"
SRC = EXTERNAL / "npm_v3" / "rq2-3-4" / "analyzed_breaking_changes.csv"
OUT = EXTERNAL / "npm_code"
CODE_EXT = (".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts")
SKIP_DIRS = re.compile(r'(^|/)(node_modules|dist|build|coverage|vendor)/')
MAX_BYTES = 300_000
MAX_FILES = 60


def _token() -> str:
    tok = os.environ.get("GITHUB_TOKEN")
    if not tok:
        env = HERE.parents[2] / ".env"
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith("GITHUB_TOKEN="):
                tok = line.split("=", 1)[1].strip().strip('"')
    if not tok:
        sys.exit("GITHUB_TOKEN مش موجود")
    return tok


class GitHub:
    def __init__(self, token: str):
        self.s = requests.Session()
        self.s.headers.update({"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                               "X-GitHub-Api-Version": "2022-11-28"})

    def get(self, url: str, raw: bool = False):
        for attempt in range(6):
            try:
                r = self.s.get(url, timeout=60, headers={"Accept": "application/vnd.github.raw"} if raw else None)
            except requests.RequestException:
                time.sleep(10 * (attempt + 1)); continue
            if r.status_code in (403, 429) and r.headers.get("X-RateLimit-Remaining") == "0":
                wait = int(r.headers.get("X-RateLimit-Reset", time.time() + 60)) - time.time() + 5
                print(f"  rate limit → waiting {int(wait)}s", flush=True)
                time.sleep(max(wait, 5)); continue
            if r.status_code >= 500:
                time.sleep(10 * (attempt + 1)); continue
            return r
        return None


def is_code(path: str) -> bool:
    return path.endswith(CODE_EXT) and not SKIP_DIRS.search(path)


def fetch_commit(gh: GitHub, project: str, sha: str) -> dict:
    owner_repo = project.strip()
    r = gh.get(f"https://api.github.com/repos/{owner_repo}/commits/{sha}")
    if r is None or r.status_code != 200:
        return {"status": "commit_not_found", "http": getattr(r, "status_code", None)}
    c = r.json()
    parent = c["parents"][0]["sha"] if c.get("parents") else None
    files = [f for f in c.get("files", []) if is_code(f["filename"])]
    meta = {"status": "ok", "project": owner_repo, "sha": sha, "parent": parent,
            "message": c["commit"]["message"][:2000], "files": []}
    if len(c.get("files", [])) >= 300:
        meta["note"] = "GitHub returns max 300 files per commit; list may be truncated"
    if len(files) > MAX_FILES:
        meta["status"] = "too_many_files"
        meta["files"] = [{"filename": f["filename"], "status": f["status"]} for f in files]
        return meta

    base = OUT / owner_repo.replace("/", "__") / sha
    for f in files:
        entry = {"filename": f["filename"], "previous_filename": f.get("previous_filename"),
                 "status": f["status"], "additions": f.get("additions"), "deletions": f.get("deletions"),
                 "patch": f.get("patch")}
        for side, ref, path in (("before", parent, f.get("previous_filename") or f["filename"]),
                                ("after", sha, f["filename"])):
            if (side == "before" and f["status"] == "added") or (side == "after" and f["status"] == "removed") or not ref:
                entry[side] = None; continue
            rr = gh.get(f"https://api.github.com/repos/{owner_repo}/contents/{path}?ref={ref}", raw=True)
            if rr is None or rr.status_code != 200 or len(rr.content) > MAX_BYTES:
                entry[side] = f"unavailable ({getattr(rr, 'status_code', None)}, {len(rr.content) if rr is not None else 0} bytes)"
                continue
            dest = base / side / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(rr.content)
            entry[side] = f"{side}/{path}"
        meta["files"].append(entry)
    return meta


def main() -> None:
    gh = GitHub(_token())
    rows = list(csv.DictReader(open(SRC, encoding="utf-8")))
    commits = sorted({(r["project"].strip(), r["commit_id"].strip()) for r in rows})
    print(f"{len(commits)} unique commits", flush=True)
    stats = {}
    for i, (project, sha) in enumerate(commits, 1):
        mpath = OUT / project.replace("/", "__") / sha / "meta.json"
        if mpath.exists():
            stats["cached"] = stats.get("cached", 0) + 1
            continue
        meta = fetch_commit(gh, project, sha)
        mpath.parent.mkdir(parents=True, exist_ok=True)
        mpath.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        stats[meta["status"]] = stats.get(meta["status"], 0) + 1
        if i % 25 == 0:
            print(f"[{i}/{len(commits)}] {stats}", flush=True)
    print("done", stats, flush=True)


if __name__ == "__main__":
    main()
