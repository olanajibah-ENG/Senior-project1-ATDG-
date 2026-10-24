# evaluation/labeling/kappa.py
"""
اتفاق بين شخصين بيوسموا (Cohen's κ) لكل عمود لحاله.

    python -m evaluation.labeling.kappa a.csv b.csv --column label
    python -m evaluation.labeling.kappa a.csv b.csv --column Q1 --column Q2 --column Q3

- المطابقة على (sample_id, element).
- الأسطر الموسومة skip عند أي واحد منهن بتنشال.
- لعمود label بيطلع كمان κ الثنائي (flagged = أي شي غير Consistent).
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from typing import Dict, List, Tuple

Key = Tuple[str, str]


def load(path: str) -> Dict[Key, Dict[str, str]]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    out = {}
    for r in rows:
        key = (r["sample_id"].strip(), r["element"].strip())
        if key in out:
            sys.exit(f"{path}: سطر مكرر {key}")
        out[key] = {k: (v or "").strip() for k, v in r.items()}
    return out


def cohen_kappa(a: List[str], b: List[str]) -> float:
    n = len(a)
    if n == 0:
        return float("nan")
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[c] * cb[c] for c in set(ca) | set(cb)) / (n * n)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def interpret(k: float) -> str:
    # Landis & Koch (1977)
    for limit, name in ((0.0, "poor"), (0.20, "slight"), (0.40, "fair"),
                        (0.60, "moderate"), (0.80, "substantial")):
        if k <= limit:
            return name
    return "almost perfect"


def report(name: str, a: List[str], b: List[str], keys: List[Key]) -> None:
    k = cohen_kappa(a, b)
    agree = sum(x == y for x, y in zip(a, b))
    print(f"\n=== {name}: κ = {k:.3f} ({interpret(k)}) — اتفاق {agree}/{len(a)}"
          f"{'  ✓' if k >= 0.60 else '  ✗ تحت الهدف 0.60'}")
    labels = sorted(set(a) | set(b))
    print("confusion (صف = A، عمود = B):")
    print(" " * 18 + "".join(f"{l[:14]:>16}" for l in labels))
    for la in labels:
        print(f"{la[:16]:>18}" + "".join(
            f"{sum(1 for x, y in zip(a, b) if x == la and y == lb):>16}" for lb in labels))
    diffs = [(key, x, y) for key, x, y in zip(keys, a, b) if x != y]
    if diffs:
        print("خلافات:")
        for (sid, el), x, y in diffs:
            print(f"  {sid} | {el}: {x} ≠ {y}")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--column", action="append", required=True)
    args = ap.parse_args()

    A, B = load(args.a), load(args.b)
    only_a, only_b = set(A) - set(B), set(B) - set(A)
    if only_a or only_b:
        print(f"تحذير: {len(only_a)} سطر بـ A بس، {len(only_b)} سطر بـ B بس — منقارن المشترك بس")

    keys = sorted(k for k in set(A) & set(B)
                  if A[k].get("label") != "skip" and B[k].get("label") != "skip")
    print(f"أسطر مشتركة للمقارنة: {len(keys)}")

    for col in args.column:
        a = [A[k][col] for k in keys]
        b = [B[k][col] for k in keys]
        report(col, a, b, keys)
        if col == "label":
            fa = ["flagged" if x != "Consistent" else "consistent" for x in a]
            fb = ["flagged" if x != "Consistent" else "consistent" for x in b]
            report("label (binary flagged)", fa, fb, keys)


if __name__ == "__main__":
    main()
