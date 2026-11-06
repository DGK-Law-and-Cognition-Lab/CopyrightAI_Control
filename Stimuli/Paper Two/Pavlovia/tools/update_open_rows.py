#!/usr/bin/env python3
"""Count analyzable participants per row and rewrite open_rows.json.

Run once a day during data collection (design record 1.1; each study's
registration, Randomization and Stopping rule). It reads a Pavlovia data
export, applies the registered exclusions, counts analyzable participants per
row (a row is a list), and rewrites the study's open_rows.json so that full
rows close. It prints only counts, so no one reads any participant's answers.

    python3 tools/update_open_rows.py --study B1 --data PATH [--data PATH2 ...]
            [--prior-codes FILE] [--dropped-pilot-codes FILE] [--target N] [--dry-run]
    python3 tools/update_open_rows.py --study A1 --init     # all rows open

PATH is a folder of CSV files (the data/ folder of the Pavlovia repository, or
an unzipped "Download results"), a .zip of them, or a single CSV. Only files
whose study_code matches the study are read; test sessions (test mode, or a
participant id beginning PILOT or TEST) are ignored, and so is any session
without a numeric SONA survey code (a link opened without one), since every
SONA participant arrives with one.

Exclusions applied (registration, Exclusions; the same rules in B1 and A1), each counted:
  * comprehension items failed twice   (excl_comprehension, saved by the page)
  * captcha trap failed                (excl_captcha)
  * instructed-response item failed    (excl_instructed)
  * story-recall item wrong            (excl_recall; "I don't remember" is wrong)
  * finished in less than one third of the median completion time, the median
    taken over all complete non-test sessions in the export on the day of the run
  * earlier participation: a code listed in --prior-codes (Paper One, Paper A
    and B studies, Prompt Position), or a code that already started an earlier
    session of this study
Incomplete sessions are not analyzable (registration, Missing data).

Rows close when they reach the target (B1: 4 per row, 96 analyzable; A1: 14
per list, 140). If the number of recruited sessions (every non-test session
that consented) reaches the cap (B1 119, A1 174), every row closes and the
script says to close the SONA listing. After the end date, run with the
fallback as --target (B1: 3, 72 analyzable; A1: 12, 120) so that rows below it
stay open.

Internal pilot (registration, Data collection). B1: once 40 participants are
analyzable, belief and timing on those 40 and story recall on every complete
session so far that meets the other exclusions. A1: the pilot is every session
run until 40 participants are analyzable; the listing then pauses, and four
gates are computed on every complete pilot session whatever its exclusion
status: belief "Yes" or "Partly" at least 70 percent; story recall correct at
least 80 percent; "Yes" to the first rule-recall item at least 70 percent;
median session at most 45 minutes, A1's posted length since 1 November 2026
(design record 12.27). If a gate other than timing fails, the
pilot participants are dropped and barred: list their codes in a file and pass
it as --dropped-pilot-codes, so their sessions are excluded and do not count
against the cap.
"""
import argparse
import csv
import io
import json
import statistics
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent

STUDIES = {
    "B1": {"study_code": "PB_B1", "n_rows": 24, "target": 4, "fallback": 3, "cap": 119,
           "pilot_n": 40, "pilot_belief": 0.70, "pilot_recall": 0.80, "pilot_minutes": 45.0,   # posted as 45 minutes (Prereg_B1.md, 1 November 2026)
           "pilot_pool": "b1"},
    # A1: 10 lists, target 14 per list (140), fallback 12 per list (120), cap 174
    # recruited (Prereg_A1.md, Sample size and Stopping rule; design record 12.23).
    "A1": {"study_code": "PA_A1", "n_rows": 10, "target": 14, "fallback": 12, "cap": 174,
           "pilot_n": 40, "pilot_belief": 0.70, "pilot_recall": 0.80, "pilot_rule_recall": 0.70,
           "pilot_minutes": 45.0, "pilot_pool": "all_complete"},   # posted as 45 minutes (Prereg_A1.md, Data collection)
}

TRUE = {"true", "1", "yes"}


def truthy(v):
    return str(v).strip().lower() in TRUE


def read_sessions(paths, study_code):
    """Yield (source name, list of row dicts) for each CSV file of this study."""
    def from_text(name, text):
        rows = list(csv.DictReader(io.StringIO(text)))
        if rows and rows[0].get("study_code") == study_code:
            yield name, rows

    for p in paths:
        p = Path(p)
        if p.is_dir():
            for f in sorted(p.rglob("*.csv")):
                yield from from_text(f.name, f.read_text(encoding="utf-8", errors="replace"))
        elif p.suffix.lower() == ".zip":
            with zipfile.ZipFile(p) as z:
                for n in sorted(z.namelist()):
                    if n.lower().endswith(".csv"):
                        yield from from_text(n, z.read(n).decode("utf-8", errors="replace"))
        elif p.suffix.lower() == ".csv":
            yield from from_text(p.name, p.read_text(encoding="utf-8", errors="replace"))
        else:
            print(f"Skipping {p}: not a folder, .zip or .csv", file=sys.stderr)


def load_prior_codes(path):
    if not path:
        return set()
    codes = set()
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        for tok in line.replace(",", " ").split():
            if tok.isdigit():
                codes.add(int(tok))
    return codes


def analyse(sessions, cfg, prior_codes, target, dropped_pilot=frozenset()):
    people = []
    for name, rows in sessions:
        r0 = rows[0]
        pid = r0.get("participant_id", "")
        if truthy(r0.get("is_test")) or truthy(r0.get("test_mode")) or pid.upper().startswith(("PILOT", "TEST")):
            continue
        code = int(r0["code"]) if str(r0.get("code", "")).isdigit() else None
        if code is None:      # not a SONA session: every SONA participant arrives with a numeric survey code
            continue
        complete = truthy(r0.get("session_complete"))
        n_trials = sum(1 for r in rows if r.get("trial_position", "") != "")
        people.append({
            "file": name, "code": code, "start": r0.get("start_time", ""),
            "row": int(r0["row"]) if str(r0.get("row", "")).isdigit() else None,
            "complete": complete and n_trials == int(r0.get("n_trials") or 0),
            "consented": r0.get("consent") == "agreed",
            "dur": float(r0["total_duration_ms"]) if r0.get("total_duration_ms") not in (None, "") else None,
            "excl_comprehension": truthy(r0.get("excl_comprehension")),
            "excl_captcha": truthy(r0.get("excl_captcha")),
            "excl_instructed": truthy(r0.get("excl_instructed")),
            "excl_recall": truthy(r0.get("excl_recall")),
            "belief": r0.get("belief", ""),
            "recall_correct": truthy(r0.get("recall_correct")),
            "rule_recall1": r0.get("rule_recall1", ""),
        })
    people.sort(key=lambda p: p["start"])

    durations = [p["dur"] for p in people if p["complete"] and p["dur"] is not None]
    median_ms = statistics.median(durations) if durations else None

    seen = set()
    for p in people:
        p["excl_repeat"] = p["code"] is not None and p["code"] in seen
        if p["code"] is not None:
            seen.add(p["code"])
        p["excl_prior"] = p["code"] is not None and (p["code"] in prior_codes or p["code"] in dropped_pilot)
        p["dropped_pilot"] = p["code"] is not None and p["code"] in dropped_pilot
        p["excl_fast"] = (p["complete"] and median_ms is not None and p["dur"] is not None
                          and p["dur"] < median_ms / 3)
        p["analyzable"] = (p["complete"] and p["row"] is not None and not any(
            p[k] for k in ["excl_comprehension", "excl_captcha", "excl_instructed", "excl_recall",
                           "excl_fast", "excl_prior", "excl_repeat"]))

    counts = {k: 0 for k in range(cfg["n_rows"])}
    for p in people:
        if p["analyzable"]:
            counts[p["row"]] += 1
    # Pilot participants dropped after a failed gate do not count against the cap.
    recruited = sum(1 for p in people if p["consented"] and not p["dropped_pilot"])
    return people, counts, recruited, median_ms


def pilot_gates(people, cfg):
    """Internal-pilot gates (registration, Data collection). B1: computed on the
    first pilot_n analyzable participants; recall over every complete session
    so far that meets the other exclusion rules. A1 (pilot_pool "all_complete"):
    every gate on every complete session up to the one that brought the
    analyzable count to pilot_n, whatever its exclusion status."""
    analyzable = [p for p in people if p["analyzable"]][: cfg["pilot_n"]]
    if len(analyzable) < cfg["pilot_n"]:
        return None
    last_start = analyzable[-1]["start"]
    if cfg.get("pilot_pool") == "all_complete":
        pool = [p for p in people if p["complete"] and p["start"] <= last_start and not p["dropped_pilot"]]
        n = len(pool)
        belief = sum(1 for p in pool if p["belief"] in ("Yes", "Partly")) / n
        recall = sum(1 for p in pool if p["recall_correct"]) / n
        rule = sum(1 for p in pool if p["rule_recall1"] == "Yes") / n
        med_min = statistics.median([p["dur"] for p in pool]) / 60000
        return {
            "pool": n,
            "belief": (belief, belief >= cfg["pilot_belief"]),
            "recall": (recall, recall >= cfg["pilot_recall"], n),
            "rule_recall": (rule, rule >= cfg["pilot_rule_recall"]),
            "timing": (med_min, med_min <= cfg["pilot_minutes"]),
        }
    pool = [p for p in people if p["complete"] and p["start"] <= last_start and not any(
        p[k] for k in ["excl_comprehension", "excl_captcha", "excl_instructed", "excl_fast", "excl_prior", "excl_repeat"])]
    belief = sum(1 for p in analyzable if p["belief"] in ("Yes", "Partly")) / len(analyzable)
    recall = sum(1 for p in pool if p["recall_correct"]) / len(pool) if pool else float("nan")
    med_min = statistics.median([p["dur"] for p in analyzable]) / 60000
    return {
        "belief": (belief, belief >= cfg["pilot_belief"]),
        "recall": (recall, recall >= cfg["pilot_recall"], len(pool)),
        "timing": (med_min, med_min <= cfg["pilot_minutes"]),
    }


def write_open_rows(path, study, cfg, open_rows, counts, recruited, target, note):
    data = {
        "study": study,
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "n_rows": cfg["n_rows"],
        "target_per_row": target,
        "cap_recruited": cfg["cap"],
        "recruited_sessions": recruited,
        "analyzable_per_row": {str(k): v for k, v in counts.items()},
        "open_rows": open_rows,
        "note": note,
    }
    path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--study", default="B1", choices=sorted(STUDIES))
    ap.add_argument("--data", action="append", default=[], help="folder, .zip or .csv (repeatable)")
    ap.add_argument("--prior-codes", help="text or CSV file of earlier participants' SONA codes")
    ap.add_argument("--dropped-pilot-codes", help="codes of internal-pilot participants dropped after a failed gate "
                                                  "(excluded, and not counted against the cap)")
    ap.add_argument("--target", type=int, help="analyzable participants per row (default: the registered target)")
    ap.add_argument("--out", help="open_rows.json to write (default: <study>/open_rows.json)")
    ap.add_argument("--init", action="store_true", help="write a file with every row open and stop")
    ap.add_argument("--dry-run", action="store_true", help="print the counts, write nothing")
    a = ap.parse_args()

    cfg = STUDIES[a.study]
    target = a.target or cfg["target"]
    out = Path(a.out) if a.out else HERE / a.study / "open_rows.json"

    if a.init:
        write_open_rows(out, a.study, cfg, list(range(cfg["n_rows"])), {k: 0 for k in range(cfg["n_rows"])}, 0, target,
                        "Initial file: every row open.")
        print(f"Wrote {out} with all {cfg['n_rows']} rows open.")
        return

    if not a.data:
        ap.error("--data is required (or use --init)")

    sessions = list(read_sessions(a.data, cfg["study_code"]))
    dropped = frozenset(load_prior_codes(a.dropped_pilot_codes))
    people, counts, recruited, median_ms = analyse(sessions, cfg, load_prior_codes(a.prior_codes), target, dropped)

    if recruited >= cfg["cap"]:
        open_rows = []
        note = f"Cap of {cfg['cap']} recruited sessions reached: every row closed. Close the SONA listing."
    else:
        open_rows = [k for k in range(cfg["n_rows"]) if counts[k] < target]
        note = "Rows with fewer than the target of analyzable participants stay open."
        if not open_rows:
            note = "Every row has reached its target. Close the SONA listing."

    excl_names = ["excl_comprehension", "excl_captcha", "excl_instructed", "excl_recall", "excl_fast",
                  "excl_prior", "excl_repeat"]
    if dropped:
        print(f"Dropped pilot participants (excluded, not counted against the cap): {sum(p['dropped_pilot'] for p in people)} sessions.")
    print(f"Study {a.study}: {len(people)} non-test sessions read; {recruited} consented (cap {cfg['cap']}).")
    print(f"Complete sessions: {sum(p['complete'] for p in people)}; analyzable: {sum(p['analyzable'] for p in people)}.")
    if median_ms is not None:
        print(f"Median completion time of complete sessions: {median_ms / 60000:.1f} min "
              f"(fast cutoff {median_ms / 180000:.1f} min).")
    print("Exclusions (a session can have more than one): " + ", ".join(
        f"{k[5:]} {sum(p[k] for p in people)}" for k in excl_names))
    print(f"Analyzable per row (target {target}):")
    for k in range(cfg["n_rows"]):
        print(f"  row {k:2d}: {counts[k]:3d}  {'open' if k in open_rows else 'CLOSED'}")
    print(f"Open rows: {len(open_rows)} of {cfg['n_rows']}.  {note}")

    gates = pilot_gates(people, cfg)
    if gates is None:
        print(f"Internal pilot: fewer than {cfg['pilot_n']} analyzable participants so far; gates not yet computed.")
    elif "pool" in gates:
        b, r, rr, t = gates["belief"], gates["recall"], gates["rule_recall"], gates["timing"]
        print(f"Internal pilot reached ({cfg['pilot_n']} analyzable). Pause the SONA listing until these gates are read.")
        print(f"Gates on all {gates['pool']} complete pilot sessions, whatever their exclusion status:")
        print(f"  belief       'Yes' or 'Partly' {b[0]:.0%} (needs {cfg['pilot_belief']:.0%}): {'PASS' if b[1] else 'FAIL'}")
        print(f"  story recall correct {r[0]:.0%} (needs {cfg['pilot_recall']:.0%}): {'PASS' if r[1] else 'FAIL'}")
        print(f"  rule recall  item 1 'Yes' {rr[0]:.0%} (needs {cfg['pilot_rule_recall']:.0%}): {'PASS' if rr[1] else 'FAIL'}")
        print(f"  timing       median {t[0]:.1f} min (needs at most {cfg['pilot_minutes']:.0f}): {'PASS' if t[1] else 'FAIL'}")
    else:
        b, r, t = gates["belief"], gates["recall"], gates["timing"]
        print(f"Internal pilot gates (first {cfg['pilot_n']} analyzable):")
        print(f"  belief  'Yes' or 'Partly' {b[0]:.0%} (needs {cfg['pilot_belief']:.0%}): {'PASS' if b[1] else 'FAIL'}")
        print(f"  recall  correct {r[0]:.0%} of {r[2]} complete sessions (needs {cfg['pilot_recall']:.0%}): {'PASS' if r[1] else 'FAIL'}")
        print(f"  timing  median {t[0]:.1f} min (needs at most {cfg['pilot_minutes']:.0f}): {'PASS' if t[1] else 'FAIL'}")

    if a.dry_run:
        print("Dry run: nothing written.")
        return
    write_open_rows(out, a.study, cfg, open_rows, counts, recruited, target, note)
    log = (HERE / "tools" / "logs" if not a.out else out.parent) / f"{a.study}_open_rows_log.csv"
    log.parent.mkdir(exist_ok=True)
    new = not log.exists()
    with log.open("a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["run_utc", "target", "sessions", "consented", "complete", "analyzable", "open_rows"]
                       + [f"row_{k}" for k in range(cfg["n_rows"])])
        w.writerow([datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), target, len(people), recruited,
                    sum(p["complete"] for p in people), sum(p["analyzable"] for p in people),
                    ";".join(map(str, open_rows))] + [counts[k] for k in range(cfg["n_rows"])])
    print(f"Wrote {out}. Push it to Pavlovia (deploy script, or tools/daily_update.sh) for it to take effect.")


if __name__ == "__main__":
    main()
