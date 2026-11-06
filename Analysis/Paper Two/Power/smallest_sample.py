"""Find each study's smallest sample that meets the criteria (design record 12.12).

Runs sim_<STUDY>.R at every candidate sample with only the main settings (main0, main1), reads
the support rates, and applies the rule: the target is the smallest candidate at which every
family has its generating accounts supported at least .80 of the time at main0 and .70 at main1,
and no rival supported more than .05 of the time in either setting. A family that cannot reach
.70 at main1 at any candidate (because variation across scenes sets a ceiling) meets its part at
the smallest candidate whose main1 rate is within .02 of its rate at the largest candidate. The
fallback is the next candidate below the target. Writes results/<STUDY>_search.csv and .md.

Usage:
    python3 smallest_sample.py B1 72 96 120 144 [--reps 500] [--cores 11] [--min 96]
"""

import argparse
import csv
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def run(study, n, reps, cores):
    tag = f"search{n}"
    out = RESULTS / f"{study}_sim_{tag}.csv"
    if out.exists():
        print(f"{study} n {n}: reusing {out.name}", flush=True)
        return out
    env = dict(os.environ, VECLIB_MAXIMUM_THREADS="1", OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1",
               DEVELOPER_DIR="/Library/Developer/CommandLineTools")
    cmd = ["Rscript", f"sim_{study}.R", "--n_target", str(n), "--n_fallback", str(n), "--only", "main0,main1",
           "--reps", str(reps), "--reps_small", str(reps), "--cores", str(cores), "--tag", tag]
    print(f"{study} n {n}: running", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=HERE, env=env, check=True)
    return out


def rates(path):
    fam = {}
    with open(path, newline="") as fh:
        for r in csv.DictReader(fh):
            if r["setting"] not in ("main0", "main1"):
                continue
            f = fam.setdefault(r["family"], {"main0": [], "main1": [], "rival": []})
            f[r["setting"]].append(float(r["own_rate"]))
            if r.get("max_rival_rate") not in (None, "", "NA"):
                f["rival"].append(float(r["max_rival_rate"]))
    return {k: {"m0": min(v["main0"]), "m1": min(v["main1"]), "rival": max(v["rival"]) if v["rival"] else 0.0}
            for k, v in fam.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("study")
    ap.add_argument("grid", nargs="+", type=int)
    ap.add_argument("--reps", type=int, default=500)
    ap.add_argument("--cores", type=int, default=max(1, os.cpu_count() - 1))
    ap.add_argument("--min", type=int, default=0, help="smallest allowed target (4 per list)")
    a = ap.parse_args()
    grid = sorted(a.grid)
    table = {n: rates(run(a.study, n, a.reps, a.cores)) for n in grid}
    families = sorted(table[grid[0]])
    largest = grid[-1]
    ok = {}
    notes = []
    for f in families:
        ceiling = all(table[n][f]["m1"] < .70 for n in grid)
        if ceiling:
            plateau = table[largest][f]["m1"]
            notes.append(f"{f}: main1 rate below .70 at every candidate (ceiling); its part is met where main1 "
                         f"is within .02 of {plateau:.2f}, the rate at {largest}.")
        for n in grid:
            r = table[n][f]
            a_ok = r["m0"] >= .80 and (r["m1"] >= .70 or (ceiling and r["m1"] >= table[largest][f]["m1"] - .02))
            ok[(f, n)] = a_ok and r["rival"] <= .05
    passing = [n for n in grid if n >= a.min and all(ok[(f, n)] for f in families)]
    target = passing[0] if passing else None
    below = [n for n in grid if target and n < target]
    fallback = below[-1] if below else None

    rows = []
    for n in grid:
        for f in families:
            r = table[n][f]
            rows.append({"study": a.study, "n": n, "family": f, "own_main0": f"{r['m0']:.3f}",
                         "own_main1": f"{r['m1']:.3f}", "max_rival": f"{r['rival']:.3f}",
                         "meets": "yes" if ok[(f, n)] else "no"})
    with open(RESULTS / f"{a.study}_search.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    md = [f"# {a.study}: smallest sample meeting the criteria",
          "",
          f"Run {date.today().isoformat()} with {a.reps} datasets per setting (main0 and main1 only), "
          f"candidates {', '.join(map(str, grid))}, smallest allowed target {a.min or grid[0]}.",
          "",
          "| N | Family | Lowest own rate, main0 | Lowest own rate, main1 | Highest rival rate | Meets |",
          "|---|---|---|---|---|---|"]
    md += [f"| {r['n']} | {r['family']} | {r['own_main0']} | {r['own_main1']} | {r['max_rival']} | {r['meets']} |"
           for r in rows]
    md += ["", f"**Target:** {target if target else 'none of the candidates meets the criteria'}. "
           f"**Fallback:** {fallback if fallback else 'none below the target'}."]
    md += [""] + [f"- {x}" for x in notes]
    (RESULTS / f"{a.study}_search.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    if target is None:
        sys.exit(2)


if __name__ == "__main__":
    main()
