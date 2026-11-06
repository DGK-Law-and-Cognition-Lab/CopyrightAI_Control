#!/usr/bin/env python3
"""Estimate A1's session length by the design record's timing rule (1.13).

    python3 tools/session_length_A1.py

Rule: reading at 4 words per second; minimum viewing times overlap with what
is read on the same screen; 8 s per slider or single-choice answer; 20 s for
the registration decision with its follow-up and confidence; 45 s per written
reason; fixed parts of 2.5 min for consent, primer and comprehension, 0.5 min
for the story, 3 to 4 min for end items and 1.5 min for the debriefing (the
practice trial is dropped, design record 12.1). Words are counted from
A1/config.js. A1's pages since the revision of 1 November 2026
(Docs/Paper Two/_internal_notes/A1_page_revision_2026-11-01.md, with its
section 13, the follow-up section, section 14, a written reason on every
trial, and section 15, the walk-through of each trial and the end scales):
  * every trial: the story page (at least 3 s, the reading overlapping it),
    the first image alone (5 s), the change page (title, statement and image
    pair, at least 10 s, the reading overlapping the minimum), then the
    question page with
    no minimum (the title and statement are not read again), then the written
    reason (45 s, the quoted answer counted within it);
  * no-change trials: one creativity item, decision, share;
  * change trials: two creativity items, decision, share, jury item (the
    per-trial belief check is gone); block-2 trials add reading the rule
    reminder above the decision;
  * the instructed-response item;
  * the follow-up section after block 1: its introductory page, then slots 6
    and 7, each on two pages: the "would" line and item with follow-up and
    confidence (20 s); then stop-others items 1 to 3 on both trials and item 4
    on the AI trial (seven answers); the low end does not reread the title and
    statement, the high end reads them once per trial;
  * the rule (four lines) and its two recall items between the blocks;
  * end items: the rule's 3 to 4 minutes; the high end also adds the purpose
    probe and the ownership item on top, as the earlier estimate did (the
    believability items and stop-others item 4 have left the end items); both
    ends add the two scales (reading their instructions or stem, 8 s per
    item: ten Short GAAIS-10 items and five beliefs items) and drop the single
    attitude item they replace.
"""
import json
import re
import statistics
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
WPS = 4.0
REASON_S = 45


def words(s):
    return len(re.findall(r"[A-Za-z0-9']+", re.sub(r"<[^>]+>", "", s)))


def main():
    d = json.loads(subprocess.check_output(["node", str(HERE / "tools" / "dump_config.js"), str(HERE / "A1" / "config.js")]))
    S = d["strings"]
    stmt = {}
    for s in S:
        if s["kind"] == "a1_statement":
            stmt.setdefault(s["amount"], []).append(words(s["text"]))
    mean = {a: statistics.mean(v) for a, v in stmt.items()}
    title = statistics.mean(words(s["text"]) for s in S if s["kind"] == "title")
    rule = sum(words(s["text"]) for s in S if s["kind"] == "block_text" and ".rule[" in s["path"])
    follow_intro = sum(words(s["text"]) for s in S if s["kind"] == "block_text" and ".follow_up_intro[" in s["path"])
    would_note = sum(words(s["text"]) for s in S if s["kind"] == "note" and ":would_note." in s["path"])
    reminder = sum(words(s["text"]) for s in S if s["kind"] == "note" and ":rule_reminder." in s["path"])
    story_words = {st: sum(words(s["text"]) for s in S if s["path"].startswith("trialStory." + st)) for st in ("ai", "hand")}
    story_s = statistics.mean(max(3.0, w / WPS) for w in story_words.values())       # the 3-s minimum overlaps the reading
    first_image_s = 5.0
    gaais_instr = sum(words(s["text"]) for s in S if ":gaais_instructions." in s["path"])
    gaais_n = sum(1 for s in S if s["kind"] == "grid_row" and ":gaais." in s["path"])
    acb_stem = sum(words(s["text"]) for s in S if s["kind"] == "item" and ":acb." in s["path"])
    acb_n = sum(1 for s in S if s["kind"] == "grid_row" and ":acb." in s["path"])
    scales_s = gaais_instr / WPS + 8 * gaais_n + acb_stem / WPS + 8 * acb_n - 8      # less the attitude item they replace

    def change_page(amount):
        return max(10.0, (title + mean[amount]) / WPS)              # 10-s minimum overlaps the reading

    def questions(amount, block):
        answers = (8 if amount == "none" else 16) + 20 + 8 + (0 if amount == "none" else 8)
        return answers + (reminder / WPS if block == 2 else 0) + REASON_S     # the written reason on every trial

    # Per participant: block 1 has two trials per amount; block 2 two large trials.
    cells = [("none", 1)] * 2 + [("small", 1)] * 2 + [("medium", 1)] * 2 + [("large", 1)] * 2 + [("large", 2)] * 2
    trial_s = [story_s + first_image_s + change_page(a) + questions(a, b) for a, b in cells]
    trials_s = sum(trial_s)
    change_mean = statistics.mean(t for (a, _), t in zip(cells, trial_s) if a != "none")
    none_mean = statistics.mean(t for (a, _), t in zip(cells, trial_s) if a == "none")

    would_s = 2 * (would_note / WPS + 20)                                            # line, decision with follow-up and confidence
    stop_s = 7 * 8                                                                   # items 1 to 3 twice, item 4 once
    rs_lo = follow_intro / WPS + would_s + stop_s
    rs_hi = rs_lo + 2 * (title + mean["large"]) / WPS                                # title and statement read again, once per trial
    instructed_s = 8
    rule_s = max(5.0, rule / WPS) + 2 * 8
    extras = 8 + 8                                                                   # purpose probe and ownership
    fixed_lo = (2.5 + 0.5 + 3.0 + 1.5) * 60 + instructed_s + rule_s + scales_s
    fixed_hi = (2.5 + 0.5 + 4.0 + 1.5) * 60 + extras + instructed_s + rule_s + scales_s
    lo = (trials_s + rs_lo + fixed_lo) / 60
    hi = (trials_s + rs_hi + fixed_hi) / 60
    mid = (lo + hi) / 2

    print("Statements, mean words: " + ", ".join(f"{a} {mean[a]:.1f}" for a in ("none", "small", "medium", "large"))
          + f"; title {title:.1f}; rule {rule}; rule reminder {reminder}; follow-up introduction {follow_intro}; "
          f"'would' line {would_note}; story pages {story_words}; Short GAAIS-10 instructions {gaais_instr} words, "
          f"{gaais_n} items; beliefs stem {acb_stem} words, {acb_n} items.")
    print(f"Each trial also has its story page ({story_s:.1f} s) and the first image alone ({first_image_s:.0f} s).")
    for a in ("none", "small", "medium", "large"):
        extra = f" (block 2: {change_page(a) + questions(a, 2):.1f} s)" if a == "large" else ""
        print(f"  {a:6s} trial: change page {change_page(a):.1f} s + question and reason pages {questions(a, 1):.0f} s = "
              f"{change_page(a) + questions(a, 1):.1f} s{extra}")
    print(f"Ten trials: {trials_s / 60:.1f} min (eight change trials averaging {change_mean:.0f} s, "
          f"two no-change trials of {none_mean:.0f} s).")
    print(f"Follow-up section: introduction, 'would' items {would_s:.0f} s, stop-others "
          f"{stop_s} s (seven answers); {rs_lo / 60:.1f} to {rs_hi / 60:.1f} min without or with rereading.")
    print(f"Instructed-response item {instructed_s} s; rule and recall items {rule_s:.0f} s.")
    print(f"Fixed parts: consent, primer and comprehension 2.5; story 0.5; end items 3 to 4; debriefing 1.5 min; "
          f"high end adds {extras} s for the purpose probe and ownership; the two scales add {scales_s:.0f} s; with the "
          f"instructed-response item and rule: {fixed_lo / 60:.1f} to {fixed_hi / 60:.1f} min.")
    print(f"Estimated session: {lo:.1f} to {hi:.1f} min (midpoint {mid:.1f}): ten trials {trials_s / 60:.1f}; "
          f"follow-up section {(rs_lo + rs_hi) / 120:.1f}; fixed parts {(fixed_lo + fixed_hi) / 120:.1f} (midpoints).")
    print("Not in the rule: device check, full-screen page and captcha, about 0.3 min more.")


if __name__ == "__main__":
    main()
