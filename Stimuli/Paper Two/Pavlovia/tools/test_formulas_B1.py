#!/usr/bin/env python3
"""Check B1's lists and per-participant formulas against the registration.

    python3 tools/test_formulas_B1.py [--csv-dir DIR]

Part 1 recomputes, independently of the page code, what the registration
fixes (Design; Randomization) and compares it with config.js run under node:
  * list k: rotation k mod 12; composition V1 if k < 12, else I2;
    position j shows scene (j + q) mod 12 of SB-P1, SB-N1, ..., SB-N6;
    cell i (o, a, r, b, c, d) at positions 2i and 2i + 1;
  * option order floor(code / 24) mod 3 -> whole/part/refuse, part/refuse/whole, refuse/whole/part;
  * a written reason on every trial (B1 config 1.1.0, 1 November 2026);
  * the "would" block on the trials at position 2i for i = k mod 6 and (k + 3) mod 6;
  * the balance claims: each cell once on a scene with a person and once
    without; every scene in every cell four times over the 24 lists; each cell
    shown again in the "would" block in 8 lists;
  * the walk-through settings: the prompt page (who wrote the prompt, then
    the plan in a box, at least 5 s), the page of what was done with the image
    (at least 8 s), the question page beside the image; story recall about the
    last trial, right after it, with one answer per cell.
Part 2 (with --csv-dir) checks every saved session in DIR: the row is
open_rows[code mod n_open] (or the forced row), every trial's scene, cell and
file, its four pages in order, option order and displayed positions, the
written reason with its quoted decision on every trial, the "would" trials,
the recall trial (the last one shown) and its key, trial order, the
instructed-response item after the third trial, item orders, the two end
scales and their scores, exclusion flags and required answers.
Part 3 (with --csv-dir) checks that every column documented in B1/README.md
is in every saved CSV (complete and early-exit sessions alike) and that no
CSV has an undocumented column.
"""
import argparse
import csv
import io
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SCENES = ["SB-P1", "SB-N1", "SB-P2", "SB-N2", "SB-P3", "SB-R2", "SB-P4",  # SB-R2 replaces SB-N3 (27 Oct 2026)
           "SB-N4", "SB-P5", "SB-N5", "SB-P6", "SB-N6"]
CELLS = "oarbcd"
ORDERS = ["whole;part;refuse", "part;refuse;whole", "refuse;whole;part"]
FAILS = []


def check(cond, msg):
    if not cond:
        FAILS.append(msg)
    return cond


def expected_list(k):
    q, comp = k % 12, ("V1" if k < 12 else "I2")
    trials = []
    for j in range(12):
        s = SCENES[(j + q) % 12]
        trials.append({"list_position": j, "scene": s, "cell": CELLS[j // 2], "file": f"{s}_{comp}.jpg", "person": "-P" in s})
    would = sorted([k % 6, (k + 3) % 6])
    return {"rotation": q, "composition": comp, "trials": trials,
            "would_positions": [2 * i for i in would], "would_cells": [CELLS[i] for i in would]}


def node_dump():
    js = r"""
const fs=require('fs'),vm=require('vm');const ctx={window:{}};vm.createContext(ctx);
vm.runInContext(fs.readFileSync(process.argv[1],'utf8'),ctx);const C=ctx.window.STUDY_CONFIG;
const rows=[];for(let k=0;k<C.nRows;k++){const r=C.buildRow(k);const d=C.derive(1000+k,r,()=>0);rows.push({row:r,derived:d});}
const opt={};for(let code=0;code<24*9;code+=7){opt[code]=C.derive(code,C.buildRow(code%24),()=>0).option_order.join(';');}
const t0=C.buildRow(0).trials;const stories={};t0.forEach(t=>{stories[t.cell+'|'+t.scene]={story:C.trialStory(t),content:C.trialContent(t),plan:C.scenes.find(s=>s.id===t.scene).plan,
  recall:C.recall.content(t),recallFields:C.recall.fromTrial(t)};});
process.stdout.write(JSON.stringify({rows,opt,stories,cells:C.cells,settings:{minView:C.minViewSeconds,viewPage:!!C.viewPage,pairLayout:C.pairLayout||null,
  questionLayout:C.questionLayout||null,pairTextBelow:!!C.pairTextBelow,statementUnder:!!C.sideTextUnderImage,viewShowsPlan:C.viewPageShowsPlan,recall:{lastTrial:!!C.recall.lastTrial,afterTrials:!!C.recall.afterTrials,
  options:C.recall.options.map(o=>o.value)},wouldIntro:C.would.intro||null,reasonQuote:C.reasonQuote||null,endIds:C.endPages.map(p=>p.id)}}));"""
    out = subprocess.check_output(["node", "-e", js, str(HERE / "B1" / "config.js")])
    return json.loads(out)


def part1():
    d = node_dump()
    scene_cell = Counter()
    would_cell = Counter()
    for k in range(24):
        e = expected_list(k)
        got = d["rows"][k]["row"]
        der = d["rows"][k]["derived"]
        check(got["rotation"] == e["rotation"] and got["composition"] == e["composition"], f"list {k}: rotation/composition")
        for gt, et in zip(got["trials"], e["trials"]):
            check(gt["list_position"] == et["list_position"] and gt["scene"] == et["scene"] and gt["cell"] == et["cell"]
                  and gt["file"] == et["file"] and gt["scene_has_person"] == et["person"],
                  f"list {k} position {et['list_position']}: got {gt}, expected {et}")
        check(der["reason_positions"] == list(range(12)), f"list {k}: written reason not on every trial {der['reason_positions']}")
        check(der["would_positions"] == e["would_positions"] and der["would_cells"] == e["would_cells"],
              f"list {k}: would positions {der['would_positions']} vs {e['would_positions']}")
        check(all(der[x] == "" for x in ("recall_cell", "recall_position", "recall_scene", "recall_file")), f"list {k}: recall fixed by the code")
        for c in CELLS:
            kinds = sorted(t["person"] for t in e["trials"] if t["cell"] == c)
            check(kinds == [False, True], f"list {k}: cell {c} not once with and once without a person")
        for t in e["trials"]:
            scene_cell[(t["scene"], t["cell"])] += 1
        for c in e["would_cells"]:
            would_cell[c] += 1
    check(all(scene_cell[(s, c)] == 4 for s in SCENES for c in CELLS), "not every scene in every cell four times")
    check(all(would_cell[c] == 8 for c in CELLS), f"'would' trials per cell: {dict(would_cell)}")
    for code, order in d["opt"].items():
        check(order == ORDERS[(int(code) // 24) % 3], f"code {code}: option order {order}")
    # Walk-through: the prompt page names who wrote the prompt and shows the plan in a box (at least 5 s);
    # what was done and the image (at least 8 s); the question page beside the image.
    st = d["settings"]
    check(st["minView"] == 8 and st["viewPage"] and st["pairLayout"] == "top" and st["questionLayout"] == "side" and not st["pairTextBelow"]
          and st["statementUnder"] and st["viewShowsPlan"] is False, f"page settings {st}")
    for key, v in d["stories"].items():
        cell = key.split("|")[0]
        lead = ("<strong>Another artist</strong>" if cell == "o" else "<strong>Alex</strong>") + " wrote this prompt for the next image:"
        check(v["story"]["paragraphs"] == [lead, '<span class="plan">' + v["plan"] + "</span>"] and v["story"]["minSeconds"] == 5, f"prompt page {key}: {v['story']}")
        stmt = next(c["statement"] for c in d["cells"] if c["id"] == cell)
        heading = "The prompt another artist wrote:" if cell == "o" else "The prompt Alex wrote:"
        check(v["content"]["statement"] == stmt and v["content"]["images"][0]["caption"] == "The image Alex kept"
              and v["content"].get("plan") == v["plan"] and v["content"].get("heading") == heading,
              f"what-was-done content {key}: {v['content']}")
        check(v["recall"]["images"][0]["file"] == v["content"]["images"][0]["file"] and v["recall"]["lines"] == ["One more question about the image you just saw."],
              f"recall page {key}")
    check(st["recall"]["lastTrial"] and st["recall"]["afterTrials"] and st["recall"]["options"] == list(CELLS) + ["dont_remember"],
          f"recall settings {st['recall']}")
    check(st["wouldIntro"] and st["wouldIntro"]["paragraphs"] == ["Here are two images you saw earlier.", "We have one more question about each."],
          f"would introduction {st['wouldIntro']}")
    check(st["reasonQuote"] == {"chosen": "You chose: “{label}.”"}, f"quoted decision {st['reasonQuote']}")
    check(st["endIds"] == ["belief", "purpose", "believability", "experience", "gaais", "creativity_beliefs", "knowledge"], f"end pages {st['endIds']}")
    print(f"Part 1: 24 lists and {len(d['opt'])} option-order codes recomputed; "
          f"scene x cell counts all 4: {all(v == 4 for v in scene_cell.values())}; "
          f"'would' trials per cell {dict(would_cell)}; {len(d['stories'])} prompt and what-was-done pages checked.")


def part2(csv_dir):
    files = sorted(Path(csv_dir).glob("*.csv"))
    summary = Counter()
    rows_hit, opts_hit = set(), set()
    for f in files:
        rows = list(csv.DictReader(io.StringIO(f.read_text(encoding="utf-8"))))
        r0 = rows[0]
        tag = f.name
        code = int(r0["code"]) if r0["code"].isdigit() else None
        open_rows = [int(x) for x in r0["open_rows"].split(";")]
        k = int(r0["row"])
        if r0["assignment_source"] == "code_mod_open_rows":
            check(k == open_rows[code % len(open_rows)], f"{tag}: row {k} != open_rows[code mod n] = {open_rows[code % len(open_rows)]}")
            check(int(r0["open_rows_index"]) == code % len(open_rows), f"{tag}: open_rows_index")
        elif r0["assignment_source"] == "url_row":
            pass
        else:
            check(r0["assignment_source"] == "random_no_numeric_code" and code is None, f"{tag}: assignment source {r0['assignment_source']}")
        e = expected_list(k)
        check(int(r0["list"]) == k and int(r0["rotation"]) == e["rotation"] and r0["composition"] == e["composition"], f"{tag}: list fields")
        if code is not None:
            check(r0["option_order"] == ORDERS[(code // 24) % 3], f"{tag}: option order {r0['option_order']}")
            check(int(r0["option_order_index"]) == (code // 24) % 3, f"{tag}: option order index")
        check(r0["would_positions"] == ";".join(map(str, e["would_positions"])), f"{tag}: would positions")
        check("attitude" not in r0, f"{tag}: the removed attitude column is still saved")
        rows_hit.add(k)
        opts_hit.add(r0["option_order"])
        reason = r0["exit_reason"]
        summary[reason] += 1
        if reason != "complete":
            check(r0["session_complete"] == "false" and r0["trial_position"] == "", f"{tag}: early exit has trial rows")
            if reason == "comprehension_failed":
                check(r0["comp_failed_twice"] == "true" and r0["excl_comprehension"] == "true", f"{tag}: comprehension flags")
                check(r0["comp_attempt1_pass"] == "false" and r0["comp_attempt2_pass"] == "false", f"{tag}: comprehension attempts")
            if reason == "captcha_failed":
                check(r0["excl_captcha"] == "true" and r0["captcha_pass"] == "false", f"{tag}: captcha flags")
            continue
        check(len(rows) == 12, f"{tag}: {len(rows)} trial rows")
        order = [int(x) for x in r0["trial_order"].split(";")]
        check(sorted(order) == list(range(12)), f"{tag}: trial order not a permutation")
        last = order[-1]
        last_cell = next(t["cell"] for t in e["trials"] if t["list_position"] == last)
        check(int(r0["recall_position"]) == last and r0["recall_cell"] == last_cell, f"{tag}: recall not about the last trial ({r0['recall_position']}, {r0['recall_cell']})")
        pages = [p["id"] for p in json.loads(r0["page_timestamps"])]
        labels = {"whole": "Register the whole image as Alex's work", "part": "Register only part of the image as Alex's work, and leave out the rest",
                  "refuse": "Refuse to register it"}
        by_pos = {int(r["list_position"]): r for r in rows}
        cells = Counter()
        for t in e["trials"]:
            r = by_pos[t["list_position"]]
            j = t["list_position"]
            check(r["scene"] == t["scene"] and r["cell"] == t["cell"] and r["file"] == t["file"], f"{tag} pos {j}: scene/cell/file")
            check(int(r["trial_position"]) == order.index(j) + 1, f"{tag} pos {j}: trial_position")
            check(r["decision"] in ("whole", "part", "refuse"), f"{tag} pos {j}: decision")
            check(int(r["decision_display_pos"]) == r0["option_order"].split(";").index(r["decision"]) + 1, f"{tag} pos {j}: displayed position of decision")
            dropped = r0["dropped_items"].split(";")
            for s in ("confidence", "share", "control"):
                if s in dropped:
                    check(r[s] == "", f"{tag} pos {j}: {s} was dropped but has an answer")
                    continue
                check(r[s] != "" and 0 <= int(r[s]) <= 100 and r[s + "_rt_ms"] != "", f"{tag} pos {j}: {s}")
            for a in ("aspect_placement", "aspect_color_light", "aspect_subject"):
                check(r[a] in ("Yes", "No", "Not sure") and r[a + "_rt_ms"] != "", f"{tag} pos {j}: {a}")
            for s in ("effort", "creativity"):
                check(r[s] in "12345" and r[s] != "", f"{tag} pos {j}: {s}")
            check(r["has_reason"] == "true" and r["written_reason"] != "" and r["written_reason_page_ms"] != "", f"{tag} pos {j}: written reason")
            check(r["written_reason_quote"] == "You chose: “" + labels[r["decision"]] + ".”", f"{tag} pos {j}: quoted decision {r['written_reason_quote']!r}")
            is_would = j in e["would_positions"]
            check((r["would_shown"] == "true") == (is_would and r0["would_block_shown"] == "true"), f"{tag} pos {j}: would_shown")
            i = order.index(j) + 1
            seq = [f"story_{i}", f"view_{i}", f"trial_{i}", f"reason_{i}"]
            at = pages.index(f"story_{i}")
            check(pages[at:at + 4] == seq, f"{tag} pos {j}: pages {pages[at:at + 4]} != {seq}")
            check(r["story_page_ms"] != "" and r["view_page_ms"] != "" and r["question_page_ms"] != "" and r["min_view_ms"] == "8000",
                  f"{tag} pos {j}: page times")
            if r["would_shown"] == "true":
                check(int(r["would_display_pos"] if "would_display_pos" in r else r["would_decision_display_pos"])
                      == r0["option_order"].split(";").index(r["would_decision"]) + 1, f"{tag} pos {j}: would option position")
            check((r["is_recall_trial"] == "true") == (j == last), f"{tag} pos {j}: recall trial")
            check(int(r["view_page_ms"]) >= int(r["min_view_ms"]) or r0["test_mode"] == "true", f"{tag} pos {j}: what-was-done page shorter than the minimum viewing time")
            cells[t["cell"]] += 1
        check(all(cells[c] == 2 for c in CELLS), f"{tag}: cells per session {dict(cells)}")
        if r0["would_block_shown"] == "true":
            would = sorted((int(r["would_order"]), int(r["trial_position"])) for r in rows if r["would_shown"] == "true")
            check([w[0] for w in would] == [1, 2] and would[0][1] < would[1][1], f"{tag}: would order {would}")
        check(r0["recall_correct_answer"] == last_cell, f"{tag}: recall key")
        check((r0["recall_correct"] == "true") == (r0["recall"] == last_cell), f"{tag}: recall_correct")
        # Story recall right after the last trial's written reason, then the "would" block (or the end items)
        ri = pages.index("recall")
        check(pages[ri - 1] == "reason_12" and pages[ri + 1] == ("would_intro" if r0["would_block_shown"] == "true" else "belief"),
              f"{tag}: recall placed at {pages[ri - 1:ri + 2]}")
        tail = [p for p in pages[ri:] if not p.startswith("would")]
        check(tail == ["recall", "belief", "purpose", "believability", "experience", "gaais", "creativity_beliefs", "knowledge",
                       "demographics", "final", "debriefing"], f"{tag}: end pages {tail}")
        gp = [int(r0["gaais_" + x]) for x in ("pos7", "pos11", "pos12", "pos17", "pos18")]
        gn = [6 - int(r0["gaais_" + x]) for x in ("neg8", "neg9", "neg10", "neg15", "neg19")]
        ab = [int(r0["acb_" + x]) for x in ("uniquely_human", "differentiate", "essence", "core", "only_humans")]
        for col, vals in (("gaais_positive", gp), ("gaais_negative", gn), ("acb_score", ab)):
            check(abs(float(r0[col]) - sum(vals) / len(vals)) < 0.0006, f"{tag}: {col} {r0[col]} != {sum(vals) / len(vals):.3f}")
        check((r0["excl_recall"] == "true") == (r0["recall_correct"] == "false"), f"{tag}: excl_recall")
        check((r0["instructed_pass"] == "true") == (r0["instructed"] == "Somewhat disagree"), f"{tag}: instructed_pass")
        check((r0["excl_instructed"] == "true") == (r0["instructed_pass"] == "false"), f"{tag}: excl_instructed")
        ii = pages.index("instructed")
        check(pages.index("reason_3") < ii < pages.index("story_4"), f"{tag}: instructed item not between trials 3 and 4")
        po = r0["purpose_order"].split(";")
        check(sorted(po) == sorted(["way_made", "quality_liking", "tell_ai_photo", "longer_plans", "something_else"]) and po[-1] == "something_else",
              f"{tag}: purpose order {po}")
        bo = r0["believability_order"].split(";")
        check(sorted(bo) == sorted("believe_" + c for c in CELLS), f"{tag}: believability order {bo}")
        for c in CELLS:
            check(r0["believe_" + c] in "1234567" and r0["believe_" + c] != "", f"{tag}: believe_{c}")
        keys = {"know1": "False", "know2": "False", "know3": "False", "know4": "True", "know5": "False"}
        score = sum(r0[q] == v for q, v in keys.items())
        check(int(r0["knowledge_score"]) == score, f"{tag}: knowledge score")
        check((r0["purpose_chose_true"] == "true") == (r0["purpose"] == "way_made"), f"{tag}: purpose_chose_true")
        any_in = any(r0[x] == "true" for x in ("excl_comprehension", "excl_captcha", "excl_instructed", "excl_recall"))
        check((r0["excl_any_in_page"] == "true") == any_in, f"{tag}: excl_any_in_page")
    print(f"Part 2: {len(files)} saved sessions checked; exit reasons {dict(summary)}; "
          f"rows hit {sorted(rows_hit)} ({len(rows_hit)} of 24); option orders hit {sorted(opts_hit)}.")


def part3(csv_dir):
    """Every column documented in B1/README.md is in every saved CSV, and vice versa."""
    import re
    text = (HERE / "B1" / "README.md").read_text(encoding="utf-8")
    section = text.split("## Data columns", 1)[1]
    documented = re.findall(r"^\| `([a-z0-9_]+)` \|", section, flags=re.M)
    check(len(documented) == len(set(documented)), "README documents a column twice")
    for f in sorted(Path(csv_dir).glob("*.csv")):
        header = next(csv.reader(io.StringIO(f.read_text(encoding="utf-8"))))
        missing = [c for c in documented if c not in header]
        extra = [c for c in header if c not in documented]
        check(not missing, f"{f.name}: documented columns missing from the CSV: {missing}")
        check(not extra, f"{f.name}: CSV columns not documented in the README: {extra}")
    print(f"Part 3: {len(documented)} documented columns compared with the header of every saved CSV.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv-dir")
    a = ap.parse_args()
    part1()
    if a.csv_dir:
        part2(a.csv_dir)
        part3(a.csv_dir)
    if FAILS:
        print(f"\n{len(FAILS)} FAILURES:")
        for m in FAILS[:60]:
            print("  -", m)
        sys.exit(1)
    print("All formula checks passed.")


if __name__ == "__main__":
    main()
