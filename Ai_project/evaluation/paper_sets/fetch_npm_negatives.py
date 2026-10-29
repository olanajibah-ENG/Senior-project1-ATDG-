"""
بيجيب تعديلات "عادية" (على الأرجح ما بتكسر الكود) من نفس مشاريع ورقة NPM، لحتى نقدر نقيس الإنذارات الكاذبة.
داتا الورقة فيها بس تعديلات بتكسر الكود، فهالأمثلة السليمة **مش موسومة من مؤلفين الورقة**.

    python -m evaluation.paper_sets.fetch_npm_negatives          (بيكمّل من وين وقف)

طريقة الاختيار (seed = 42):
- لكل مشروع، عدد الأمثلة السليمة بيتناسب مع عدد تعديلاته يلي بتكسر (المجموع حوالي TARGET).
- منمشي على التاريخ قبل تعديل بيكسر من نفس المشروع (نفس الفترة الزمنية)، ومناخد تعديل:
  مش من تعديلات الورقة، مش merge، رسالته ما فيها إشارة لكسر (BREAKING، breaking، "!:")،
  ومش release/version bump، وبيغيّر ملف كود واحد على الأقل.
المخرج: evaluation/external/npm_code_neg/<owner>__<repo>/<sha>/ (نفس شكل npm_code) + negatives.csv
"""
import csv
import json
import random
import re

from .fetch_npm_code import EXTERNAL, SRC, GitHub, _token, fetch_commit, is_code

OUT = EXTERNAL / "npm_code_neg"
INDEX = OUT / "negatives.csv"
TARGET = 300
SEED = 42
BREAKING_MSG = re.compile(r'breaking|^\w+(\([^)]*\))?!:', re.I | re.M)
SKIP_MSG = re.compile(r'^(chore\(release\)|release|bump|v?\d+\.\d+\.\d+|publish|merge)', re.I)


def _quota(rows) -> dict:
    per_project = {}
    for project, sha in rows:
        per_project.setdefault(project, []).append(sha)
    total = sum(len(v) for v in per_project.values())
    return {p: max(1, round(len(v) * TARGET / total)) for p, v in per_project.items()}, per_project


def main() -> None:
    gh = GitHub(_token())
    rows = list(csv.DictReader(open(SRC, encoding="utf-8")))
    breaking = sorted({(r["project"].strip(), r["commit_id"].strip()) for r in rows})
    breaking_shas = {s for _, s in breaking}
    quota, per_project = _quota(breaking)
    rng = random.Random(SEED)

    done = {}
    if INDEX.exists():
        for r in csv.DictReader(open(INDEX, encoding="utf-8")):
            done.setdefault(r["project"], []).append(r["sha"])
    OUT.mkdir(parents=True, exist_ok=True)
    new_file = not INDEX.exists()
    index = open(INDEX, "a", encoding="utf-8", newline="")
    w = csv.writer(index)
    if new_file:
        w.writerow(["project", "sha", "anchor_breaking_sha", "files"])

    stats = {"ok": 0, "skipped_projects": 0}
    for pi, (project, shas) in enumerate(sorted(per_project.items()), 1):
        need = quota[project] - len(done.get(project, []))
        if need <= 0:
            continue
        anchors = shas[:]
        rng.shuffle(anchors)
        taken = set(done.get(project, []))
        for anchor in anchors:
            if need <= 0:
                break
            r = gh.get(f"https://api.github.com/repos/{project}/commits?sha={anchor}&per_page=40")
            if r is None or r.status_code != 200:
                continue
            candidates = r.json()[1:]                      # [0] هو التعديل يلي بيكسر نفسه
            rng.shuffle(candidates)
            for c in candidates:
                sha, msg = c["sha"], c["commit"]["message"]
                if (sha in breaking_shas or sha in taken or len(c.get("parents", [])) != 1
                        or BREAKING_MSG.search(msg) or SKIP_MSG.match(msg.strip())):
                    continue
                meta = fetch_commit(gh, project, sha, out=OUT)
                code_files = [f for f in meta.get("files", []) if is_code(f["filename"])]
                if meta["status"] != "ok" or not code_files:
                    continue
                meta["anchor_breaking_sha"] = anchor
                mpath = OUT / project.replace("/", "__") / sha / "meta.json"
                mpath.parent.mkdir(parents=True, exist_ok=True)
                mpath.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
                w.writerow([project, sha, anchor, len(code_files)]); index.flush()
                taken.add(sha); need -= 1; stats["ok"] += 1
                break                                      # تعديل واحد لكل نقطة بداية، لحتى يتوزّعوا بالزمن
        if need > 0:
            stats["skipped_projects"] += 1
        if pi % 10 == 0:
            print(f"[{pi}/{len(per_project)}] {stats}", flush=True)
    index.close()
    print("done", stats, flush=True)


if __name__ == "__main__":
    main()
