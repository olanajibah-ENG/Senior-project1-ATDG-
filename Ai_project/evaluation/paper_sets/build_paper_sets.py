"""
بيحوّل بيانات الأوراق البحثية لصيغة عينات run_baseline / evaluate، مع ملف وسم لكل مجموعة.

    python -m evaluation.paper_sets.build_paper_sets

المصادر (لازم تكون منزّلة بـ evaluation/external/ — مستثناة من git):
  docprism_main.zip  — github.com/SnowPhoebe/DocPrism (MIT)
  cascade_dataset.zip — github.com/TobiasKiecker/CASCADE, FSE26/PaperEvaluation/dataset.zip

المجموعات الناتجة (evaluation/paper_sets/<name>/):
  docprism_ablation  — 52 دالة Python معنونة (6 متناقضة)             ← مسموح نفتح الأخطاء
  cascade_balanced   — 71 متناقضة + نسختهم المصلّحة (142، Java)        ← أرقام بس
  cascade_realistic  — 71 متناقضة + 639 متوافقة (seed 42) = 10/90      ← أرقام بس
  cascade_dev        — 25 زوج من cascade_balanced (50 حالة)            ← مسموح نفتح الأخطاء
  cascade_test       — الـ 46 زوج الباقيين (92 حالة)                   ← أرقام بس، بالمحطات

كل حالة بالمصدر = دالة وحدة + توثيقها. التحويل:
  الكود    → ملف فيه الدالة (جوا كلاس إذا كانت method)
  التوثيق → نفس شكل AIExplanation: "## Class: X" / "### Method: name(...)" + نص التوثيق
            (الدالة المستقلة: "### Function: name" بدون كلاس)
  الوسم    → Inconsistent / Consistent على العنصر "Class.method" أو "<module>.function"
"""
import csv
import json
import random
import re
import textwrap
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXTERNAL = HERE.parent / "external"
MODULE = "<module>"
DEV_PAIRS = 25          # CASCADE: 25 زوج للتطوير، والباقي (46) للاختبار


def _write_set(name: str, samples: list, labels: list) -> None:
    out = HERE / name
    out.mkdir(exist_ok=True)
    for old in out.glob("*.json"):
        old.unlink()
    for s in samples:
        (out / f"{s['id']}.json").write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(HERE / f"labels_{name}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["sample_id", "element", "label", "pair_id", "source", "notes"])
        w.writeheader()
        w.writerows(labels)
    pos = sum(l["label"] == "Inconsistent" for l in labels)
    print(f"{name}: {len(samples)} samples, {pos} inconsistent / {len(labels) - pos} consistent")


# ─────────────────────────────────────────────────────────────────────
# DocPrism (Python)
# ─────────────────────────────────────────────────────────────────────

# أول def بالكود (ممكن يكون قبلها decorators)
_METHOD_RE = re.compile(r'^\s*(?:async\s+)?def\s+(\w+)\s*\(\s*(self|cls)\b', re.M)
_DEF_RE = re.compile(r'^\s*(?:async\s+)?def\s+(\w+)', re.M)


def _clean_docstring(doc: str) -> str:
    doc = doc.strip()
    for q in ('"""', "'''"):
        if doc.startswith(q) and doc.endswith(q) and len(doc) >= 6:
            doc = doc[3:-3]
    lines = doc.strip("\n").splitlines()
    if len(lines) > 1:   # السطر الأول ما إله indentation؛ الباقي بيتوحّد
        lines = [lines[0].strip()] + textwrap.dedent("\n".join(lines[1:])).splitlines()
    return "\n".join(lines).strip()


def _repair_indentation(code: str) -> tuple:
    """
    بعض كود DocPrism فيه indentation مكسور من شيل الـ docstring عند المصدر:
      (1) decorator و def مش بنفس المستوى   (2) أول سطر بالجسم أعمق من الباقي.
    منصلّح هالحالتين بس، والباقي بيضل متل ما هو. بيرجّع (code, repaired?).
    """
    import ast
    try:
        ast.parse(code)
        return code, False
    except SyntaxError:
        pass
    lines = code.splitlines()
    indent = lambda l: len(l) - len(l.lstrip())
    def_idx = next(i for i, l in enumerate(lines) if _DEF_RE.match(l))
    # (1) الـ decorators بياخدوا indentation الـ def
    for i in range(def_idx):
        if lines[i].strip().startswith("@"):
            lines[i] = " " * indent(lines[def_idx]) + lines[i].strip()
    # (2) نهاية التوقيع = أول سطر بعد الـ def بينتهي بـ ":" (بيدعم توقيع على كذا سطر)
    sig_end = next(i for i in range(def_idx, len(lines)) if lines[i].rstrip().endswith(":"))
    body = [i for i in range(sig_end + 1, len(lines)) if lines[i].strip()]
    if len(body) >= 2:
        base = min(indent(lines[i]) for i in body[1:])   # المستوى الأساسي للجسم
        lines[body[0]] = " " * base + lines[body[0]].lstrip()
    fixed = textwrap.dedent("\n".join(lines)) + "\n"
    try:
        ast.parse(fixed)
        return fixed, True
    except SyntaxError:
        return code, False


def build_docprism() -> None:
    z = zipfile.ZipFile(EXTERNAL / "docprism_main.zip")
    samples, labels = [], []
    for project in ("pandas", "requests"):
        for x in json.loads(z.read(f"DocPrism-main/datasets/ablation_dataset/{project}_labeled.json")):
            code = textwrap.dedent(x["code"]).strip("\n") + "\n"
            code, repaired = _repair_indentation(code)
            first_def = _DEF_RE.search(code)
            name = first_def.group(1)
            doc = _clean_docstring(x["doc"])
            sid = f"docprism_{project}_{x['id']:03d}"
            m = _METHOD_RE.search(code)
            if m and m.start() == first_def.start():
                cls = "DocPrismCase"
                code = f"class {cls}:\n" + textwrap.indent(code, "    ")
                content = f"## Class: {cls}\n\n### Method: {name}\n{doc}\n"
                element = f"{cls}.{name}"
            else:
                content = f"### Function: {name}\n{doc}\n"
                element = f"{MODULE}.{name}"
            samples.append({"id": sid, "language": "python", "code": code,
                            "doc": {"content": content, "explanation_type": "low_level"},
                            "source": f"DocPrism ablation_dataset/{project}_labeled.json id={x['id']}"})
            labels.append({"sample_id": sid, "element": element,
                           "label": "Inconsistent" if x["label"] == "inconsistent" else "Consistent",
                           "pair_id": "", "source": "DocPrism (2 authors, consensus)",
                           "notes": "; ".join(n for n in (
                               "top-level function" if element.startswith(MODULE) else "",
                               "indentation repaired (source artifact)" if repaired else "") if n)})
    _write_set("docprism_ablation", samples, labels)


# ─────────────────────────────────────────────────────────────────────
# CASCADE (Java)
# ─────────────────────────────────────────────────────────────────────

def _clean_javadoc(doc: str) -> str:
    doc = doc.strip()
    doc = re.sub(r'^/\*\*', '', doc)
    doc = re.sub(r'\*/$', '', doc)
    return "\n".join(re.sub(r'^\s*\*\s?', '', l) for l in doc.splitlines()).strip()


def _java_sample(z, path: str):
    e = json.loads(z.read(f"java/{path}/analyzed.json"))[0]
    s, parent = e["signature"], e["parent"]
    cls = parent["name"]
    generics = f"<{', '.join(s['generics'])}> " if s.get("generics") else ""
    mods = "".join(s.get("modifier") or [])
    annotations = "".join(a.strip() + "\n    " for a in s.get("annotations") or [])
    throws = f" throws {', '.join(s['exceptions'])}" if s.get("exceptions") else ""
    params = ", ".join(s.get("params") or [])
    body = textwrap.indent(e["code"].strip(), "    ").lstrip()
    code = (f"package {e['package']};\n\npublic class {cls} {{\n"
            f"    {annotations}{mods}{generics}{s['returns']} {s['name']}({params}){throws} {body}\n}}\n")
    content = f"## Class: {cls}\n\n### Method: {s['name']}({params})\n{_clean_javadoc(e['doc'])}\n"
    sid = "cascade__" + path.replace("/", "__")
    return {"id": sid, "language": "java", "code": code,
            "doc": {"content": content, "explanation_type": "low_level"},
            "source": f"CASCADE dataset.zip java/{path}"}, f"{cls}.{s['name']}"


def build_cascade() -> None:
    z = zipfile.ZipFile(EXTERNAL / "cascade_dataset.zip")
    pairs = re.findall(r'"([^"]+)": "([^"]+)"', z.read("dataset_mapping_dict.py").decode())
    inconsistent = {inco: fixed for fixed, inco in pairs}
    fixed_set = set(inconsistent.values())
    txt = {n[len("java/"):].rsplit("/", 1)[0]: z.read(n).decode().strip()
           for n in z.namelist() if n.endswith("inconsistency.txt")}
    others = sorted(p for p in txt if p not in inconsistent and p not in fixed_set)

    def label_row(path, element, label, pair, note=""):
        return {"sample_id": "cascade__" + path.replace("/", "__"), "element": element, "label": label,
                "pair_id": pair, "source": "CASCADE (manually verified doc-fix commits)", "notes": note}

    def build(name, paths_with_labels):
        samples, labels = [], []
        for path, label, pair, note in paths_with_labels:
            s, element = _java_sample(z, path)
            samples.append(s)
            labels.append(label_row(path, element, label, pair, note))
        _write_set(name, samples, labels)

    inco_rows = []
    for i, (inco, fixed) in enumerate(sorted(inconsistent.items())):
        note = "inconsistency.txt says False; mapping + dataset_info.xlsx say True" if txt.get(inco) != "True" else ""
        inco_rows.append((inco, "Inconsistent", f"p{i:02d}", note))
        inco_rows.append((fixed, "Consistent", f"p{i:02d}", "fixed version"))
    build("cascade_balanced", inco_rows)

    # تقسيم تطوير / اختبار — أزواج كاملة، موزّعة على المشاريع بنسبة حجمها، seed ثابت
    by_project = {}
    for i in range(0, len(inco_rows), 2):
        project = "/".join(inco_rows[i][0].split("/")[:2])
        by_project.setdefault(project, []).append(inco_rows[i:i + 2])
    rnd_split = random.Random(42)
    total_pairs = sum(len(v) for v in by_project.values())
    quota = {p: len(v) * DEV_PAIRS / total_pairs for p, v in by_project.items()}
    take = {p: int(q) for p, q in quota.items()}
    # التقريب: الباقي بيروح للمشاريع يلي إلها أكبر كسور
    for p in sorted(quota, key=lambda p: quota[p] - take[p], reverse=True)[:DEV_PAIRS - sum(take.values())]:
        take[p] += 1
    dev_rows, test_rows = [], []
    for p in sorted(by_project):
        pairs_p = by_project[p][:]
        rnd_split.shuffle(pairs_p)
        for pair in pairs_p[:take[p]]:
            dev_rows += pair
        for pair in pairs_p[take[p]:]:
            test_rows += pair
    build("cascade_dev", dev_rows)
    build("cascade_test", test_rows)

    rnd = random.Random(42)
    extra = rnd.sample(others, 639)
    build("cascade_realistic", [r for r in inco_rows if r[1] == "Inconsistent"]
          + [(p, "Consistent", "", "") for p in sorted(extra)])


if __name__ == "__main__":
    build_docprism()
    build_cascade()
