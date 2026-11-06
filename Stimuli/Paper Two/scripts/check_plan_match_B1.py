"""Check every sentence of each Set B plan (version 1) against the 24 accepted B1 images.

B1 tells participants that each image matches Alex's plan, so every sentence of plan
version 1 (subject, arrangement, light, colors) should hold in both compositions, V1 and I2,
not only the feature sentence the acceptance rule checks. The description model answers one
fixed yes-or-no question per sentence and image. Writes setB/plan_match_check.csv.

Run from a shell that has loaded ~/.zshrc:
    python3 check_plan_match_B1.py                               # all 24 files
    python3 check_plan_match_B1.py --files SB-P6_I2,SB-N4_I2     # only these files; other rows are kept
"""

import argparse
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from api_ledger import Ledger  # noqa: E402
from auto_checks import ask_yes_no  # noqa: E402
from generate_setB_B1 import b1_scenes, read_bank  # noqa: E402

HERE = Path(__file__).resolve().parent
SETB = HERE.parent / "setB"
OUT = SETB / "plan_match_check.csv"


def sentences(plan):
    return [s.strip() for s in re.split(r"(?<=\.)\s+", plan) if s.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--files", default="", help="comma-separated stems such as SB-P6_I2; default all 24")
    only = {f for f in ap.parse_args().files.split(",") if f}
    scenes, _bank_hash = read_bank()
    ledger = Ledger("check_plan_match_B1", soft_cap_usd=1.0)
    rows = []
    for code in b1_scenes():  # the twelve B1 scenes, with any reserve in use in its scene's place
        scene = scenes[code]
        for version in ("V1", "I2"):
            if only and f"{code}_{version}" not in only:
                continue
            path = SETB / f"{code}_{version}.png"
            for i, sent in enumerate(sentences(scene["plan_v1"]), start=1):
                q = f'Does this photograph fit the following description: "{sent}"?'
                r = ask_yes_no(ledger, path, q, scene=code, file=path.name, purpose="plan sentence check")
                rows.append({"scene": code, "file": path.name, "sentence_no": i, "sentence": sent,
                             "question": q, "answer": r["answer"]})
                print(code, version, i, r["answer"], sent, flush=True)
    if only and OUT.exists():  # keep the rows of the files not re-checked, in their original order
        kept = [r for r in csv.DictReader(open(OUT, encoding="utf-8")) if r["file"].removesuffix(".png") not in only]
        new = {r["file"]: [] for r in rows}
        for r in rows:
            new[r["file"]].append(r)
        order = [r["file"] for r in csv.DictReader(open(OUT, encoding="utf-8"))]
        by_file = {}
        for r in kept + rows:
            by_file.setdefault(r["file"], []).append(r)
        rows = [r for f in dict.fromkeys(order + list(new)) for r in by_file.get(f, [])]
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    bad = [r for r in rows if r["answer"] != "yes"]
    print(f"\n{len(rows)} checks, {len(bad)} not yes")
    for r in bad:
        print("NOT YES:", r["file"], r["sentence_no"], r["sentence"], r["answer"])


if __name__ == "__main__":
    main()
