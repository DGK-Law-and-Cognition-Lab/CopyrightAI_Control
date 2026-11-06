#!/usr/bin/env python3
"""Estimate B1's session length by the design record's timing rule (1.13).

    python3 tools/session_length_B1.py

Rule: reading at 4 words per second; minimum viewing times overlap with what
is read on the same screen; 8 s per slider or single-choice answer; 16 s for
the registration decision with its confidence item (no follow-up in B1); 5 s
per aspect row; 45 s per written reason; fixed parts of 2.5 min for consent,
primer and comprehension, 0.5 min for the story, 3 to 4 min for the end items
and 1.5 min for the debriefing; about 1 min for the six believability items
(design record 12.5). Words are counted from B1/config.js. B1's pages since
the revision of 1 November 2026
(Docs/Paper Two/_internal_notes/B1_page_revision_2026-11-01.md):
  * every trial: the prompt page (who wrote it and the prompt, at least 5 s,
    the reading overlapping it); the page of what was done with the image
    (at least 8 s from image load, the reading overlapping it); the question
    page beside the image (what was done is not read again); the written
    reason (45 s, the quoted answer counted within it);
  * story recall right after the last trial (one answer, 8 s, and its line);
  * the "would" block: its introductory page, then two trials, each one page
    with the line, the "would" item and confidence (16 s); the high end reads
    what was done again;
  * end items: the rule's 3 to 4 minutes and the believability minute, plus
    the two scales (reading their instructions or stem, 8 s per item), less
    the single attitude item they replace.
"""
import json
import re
import statistics
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
WPS = 4.0


def words(s):
    return len(re.findall(r"[A-Za-z0-9']+", re.sub(r"<[^>]+>", "", s)))


def main():
    d = json.loads(subprocess.check_output(["node", str(HERE / "tools" / "dump_config.js"), str(HERE / "B1" / "config.js")]))
    S = d["strings"]
    plans = [words(s["text"]) for s in S if s["kind"] == "plan"]
    stmts = {s["cell"]: words(s["text"]) for s in S if s["kind"] == "statement"}
    leads = {s["path"].split(".")[1]: words(s["text"]) for s in S if s["kind"] == "plan_heading" and s["path"].endswith(".lead")}
    plan_mean = statistics.mean(plans)
    prompt_page = statistics.mean(max(5.0, (leads[c] + plan_mean) / WPS) for c in stmts)          # 2 trials per cell
    done_page = statistics.mean(max(8.0, stmts[c] / WPS) for c in stmts)
    answers = 16 + 8 + 8 + 3 * 5 + 8 + 8                     # decision+confidence, share, control, 3 aspects, effort, creativity
    reason = 45
    trial = prompt_page + done_page + answers + reason
    recall_line = sum(words(s["text"]) for s in S if s["path"].startswith("recall.lines"))
    recall_s = recall_line / WPS + 8
    would_intro = sum(words(s["text"]) for s in S if s["path"].startswith("would.intro"))
    would_note = sum(words(s["text"]) for s in S if s["kind"] == "note" and ":would_note." in s["path"])
    would_lo = would_intro / WPS + 2 * (would_note / WPS + 16)
    would_hi = would_lo + 2 * statistics.mean(stmts.values()) / WPS
    gaais_instr = sum(words(s["text"]) for s in S if ":gaais_instructions." in s["path"])
    gaais_n = sum(1 for s in S if s["kind"] == "grid_row" and ":gaais." in s["path"])
    acb_stem = sum(words(s["text"]) for s in S if s["kind"] == "item" and ":acb." in s["path"])
    acb_n = sum(1 for s in S if s["kind"] == "grid_row" and ":acb." in s["path"])
    scales_s = gaais_instr / WPS + 8 * gaais_n + acb_stem / WPS + 8 * acb_n - 8
    fixed_lo = (2.5 + 0.5 + 3.0 + 1.0 + 1.5) * 60 + scales_s + 8          # with the instructed-response item
    fixed_hi = (2.5 + 0.5 + 4.0 + 1.0 + 1.5) * 60 + scales_s + 8
    trials_s = 12 * trial
    lo = (trials_s + recall_s + would_lo + fixed_lo) / 60
    hi = (trials_s + recall_s + would_hi + fixed_hi) / 60
    print(f"Prompts: mean {plan_mean:.1f} words (range {min(plans)} to {max(plans)}); what was done: "
          + ", ".join(f"{c} {n}" for c, n in stmts.items()) + " words.")
    print(f"One trial: prompt page {prompt_page:.1f} s + what was done {done_page:.1f} s + questions {answers} s + written reason {reason} s = {trial:.1f} s.")
    print(f"Twelve trials: {trials_s / 60:.1f} min; story recall {recall_s:.0f} s; 'would' block {would_lo:.0f} to {would_hi:.0f} s.")
    print(f"Fixed parts: consent, primer and comprehension 2.5; story 0.5; end items 3 to 4; believability 1; debriefing 1.5 min; "
          f"the two scales {scales_s:.0f} s; instructed-response item 8 s: {fixed_lo / 60:.1f} to {fixed_hi / 60:.1f} min.")
    print(f"Estimated session: {lo:.1f} to {hi:.1f} min (midpoint {(lo + hi) / 2:.1f}): twelve trials {trials_s / 60:.1f}; "
          f"recall and 'would' block {(recall_s + (would_lo + would_hi) / 2) / 60:.1f}; fixed parts {(fixed_lo + fixed_hi) / 120:.1f} (midpoints).")
    print("Not in the rule: device check, full-screen page and captcha, about 0.3 min more.")


if __name__ == "__main__":
    main()
