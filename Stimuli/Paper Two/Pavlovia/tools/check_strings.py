#!/usr/bin/env python3
"""Compare every participant-facing string of a study's config.js with its source.

    python3 tools/check_strings.py [--study B1]
    python3 tools/check_strings.py --study A1

Strings are extracted from <study>/config.js by tools/dump_config.js (node).
Sources:
  registration   Docs/Paper Two/_source/Prereg_<study>.md (study text, items, options, labels)
  prompt bank    Docs/Paper Two/Paper_Two_Prompt_Bank.md (B1: plans, version 1;
                 A1: the current Set A rows of added elements, reserves included)
  consent        Docs/IRB/V2_CONSENT FORM_Survey.docx (the IRB-approved form)
  Paper One      Paper One's Study 1 survey file (.qsf) and Docs/IRB/V1_DebriefandDemographicQuestions.docx
  template       the genre-study template's experiment.js (screen furniture)
A string passes when it occurs verbatim in its source (after stripping HTML tags
and collapsing white space). Registered forms that the registration writes in
running text (lists separated by " / ", "... " continuations of a stem, scale
labels written "1 No effort involved", anchors in parentheses) are matched in
that form and reported as such. The debriefing, which the registration
describes rather than quotes, is compared word by word and every difference is
listed. Every string is also checked for em and en dashes. Exit status 1 if any
string fails.

A1 also: each scene's three added elements must equal the bank's current row
for that scene and amount; every statement shown must equal the
registration's sentence frame (its SA01 medium example) with the bank's
phrase put in, the large amount naming the medium element and the two further
ones (the bank's SA01 large example), and the no-change sentence; titles,
image labels, the rule, the introductory pages and lines must occur in the
registration. Since the page revision of 1 November 2026
(Docs/Paper Two/_internal_notes/A1_page_revision_2026-11-01.md), A1's text is
one sentence per line: each line of a question, note, page or statement is
checked as its own string, a statement must also split into the same lines as
the registration's example, and the bold words of the titles and statements
(<strong> in config.js, ** in the registration) must be the same. The
addition creativity item, whose {phrase} names each trial's added elements,
is matched with the registration's example phrase (scene SA01, medium). The
lines quoting the participant's decision above the written reason (on every
trial since config 1.4.0), which the registration describes rather than
quotes, pass when the registration names their openings ("You chose:", "Left
out:"); their exact form is the change specification's (section 14). The debriefing passes sentence by sentence where the
registration quotes it (A1) and is otherwise compared word by word (B1).
"""
import argparse
import difflib
import html
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent          # .../Stimuli/Paper Two/Pavlovia
ROOT = HERE.parents[2]                                  # the project root
TEMPLATE = ROOT.parent / "DGK Lab - Scene A Faire Computational" / "Experiment" / "Study 1" / "experiment.js"
QSF = ROOT / "Analysis" / "R Analysis Pipeline" / "Study 1" / "qualtrics" / "Final_-_AI_Copyright_-_Study_1.qsf"
CONSENT = ROOT / "Docs" / "IRB" / "V2_CONSENT FORM_Survey.docx"
IRB_DEBRIEF = ROOT / "Docs" / "IRB" / "V1_DebriefandDemographicQuestions.docx"
BANK = ROOT / "Docs" / "Paper Two" / "Paper_Two_Prompt_Bank.md"


def norm(s):
    s = html.unescape(re.sub(r"<[^>]+>", "", s))
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", s).strip()


def md_norm(s):
    s = s.replace("*", "")
    return norm(s)


def docx_text(path):
    x = zipfile.ZipFile(path).read("word/document.xml").decode("utf8")
    paras = []
    for p in re.findall(r"<w:p[ >].*?</w:p>", x, flags=re.S):
        t = "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", p, flags=re.S))
        if t.strip():
            paras.append(norm(t))
    return "\n".join(paras)


def qsf_text(path):
    q = json.loads(path.read_text(encoding="utf-8"))
    parts = []
    for e in q["SurveyElements"]:
        if e.get("Element") != "SQ":
            continue
        p = e["Payload"]
        parts.append(norm(p.get("QuestionText") or ""))
        for c in (p.get("Choices") or {}).values():
            if isinstance(c, dict) and c.get("Display"):
                parts.append(norm(c["Display"]))
    return "\n".join(parts)


def bank_plans(path):
    plans, scene = {}, None
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"### (SB-[PNR]\d)\.", line)
        if m:
            scene = m.group(1)
        m = re.match(r"\| Plan, version 1 \| (.*) \|$", line)
        if m and scene:
            plans[scene] = norm(m.group(1))
    return plans


def bank_set_a(path):
    """Current Set A rows: {scene: {small, medium, large}} (reserves included)."""
    rows, scene = {}, None
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"### (SA-?R?\d+)\.", line)
        if m:
            scene = m.group(1)
            rows[scene] = {}
            continue
        if line.startswith("## Set B"):
            scene = None
        m = re.match(r"\| (Small|Medium|Large, added to the medium file) \| (.*) \|$", line)
        if m and scene:
            rows[scene][{"Small": "small", "Medium": "medium"}.get(m.group(1), "large")] = norm(m.group(2))
    return rows


def word_count(s):
    return len(re.findall(r"[A-Za-z0-9']+", norm(s)))


def soft(s):
    """White space and quotation marks evened out; tags kept (for bold checks)."""
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", s).strip()


def bold_html(s):
    """Markdown bold (**...**) written as the page writes it (<strong>...</strong>)."""
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--study", default="B1")
    a = ap.parse_args()
    reg_path = ROOT / "Docs" / "Paper Two" / "_source" / f"Prereg_{a.study}.md"
    reg_text = reg_path.read_text(encoding="utf-8")
    reg = md_norm(reg_text)
    reg_lower = reg.lower()
    reg_html = soft(bold_html(reg_text))          # bold kept, as <strong>
    dump = json.loads(subprocess.check_output(["node", str(HERE / "tools" / "dump_config.js"), str(HERE / a.study / "config.js")]))
    strings = dump["strings"]
    consent = docx_text(CONSENT)
    paper_one = qsf_text(QSF) + "\n" + docx_text(IRB_DEBRIEF)
    template = TEMPLATE.read_text(encoding="utf-8") if TEMPLATE.exists() else ""
    template_raw = re.sub(r"\s+", " ", template.replace("\\'", "'"))
    plans = bank_plans(BANK)
    set_a = bank_set_a(BANK)
    bank_text = md_norm(BANK.read_text(encoding="utf-8"))
    creativity_def = "Creativity is defined as the presence of at least a minimal original, intellectual contribution to the creation of the work."

    results = []          # (status, source, path, text, note)

    def res(ok, source, s, note=""):
        results.append(("PASS" if ok else "FAIL", source, s["path"], s["text"], note))

    stem = "How believable were the stories about images" if a.study == "B1" else "How believable were the descriptions of images"
    for s in strings:
        t = norm(s["text"])
        k = s["kind"]
        if k == "plan":
            ok = plans.get(s["scene"]) == t
            note = "plan version 1 in the prompt bank"
            if s["scene"] == "SB-P1":
                ok = ok and t in reg
                note += "; also quoted in the registration"
            res(ok, "prompt bank", s, note)
        elif k in ("plan_heading", "statement", "primer", "story", "grid_row", "reminder", "caption", "block_text", "note", "intro"):
            res(t in reg, "registration", s)
        elif k == "title":
            # The words, and the bold words, as the registration writes them
            ok_words = t in reg
            ok_bold = soft(s["text"]) in reg_html
            res(ok_words and ok_bold, "registration", s, "bold words as in the registration" if ok_words else "")
            if ok_words and not ok_bold:
                results[-1] = ("FAIL", "registration", s["path"], s["text"], "words match; bold words differ from the registration")
        elif k == "reason_quote":
            opening = norm(s["text"]).split('"')[0].strip()
            ok = f'"{opening}"' in reg or f"after {opening}" in reg or f'after "{opening}"' in reg
            res(ok, "registration", s, f'described, not quoted: the registration names the opening "{opening}"; '
                                       "the exact form is the change specification's")
        elif k == "phrase":
            res(set_a.get(s["scene"], {}).get(s["amount"]) == t, "prompt bank", s, f"current Set A row, {s['scene']} {s['amount']}")
        elif k == "a1_statement":
            frame_m = re.search(r'Scene SA01 at the medium amount reads: "(.*?)"', reg)
            frame_md = re.search(r'Scene SA01 at the medium amount reads: "(.*?)"', soft(reg_text))
            none_m = re.search(r'No-change trials read: "(.*?)"', reg)
            row = set_a.get(s["scene"], {})
            lines = [soft(x) for x in s.get("lines", [s["text"]])]
            if s["amount"] == "none":
                res(none_m is not None and t == none_m.group(1) and len(lines) == 1, "registration", s, "the no-change sentence")
            else:
                phrase = row.get("medium", "") + ", " + row.get("large", "") if s["amount"] == "large" else row.get(s["amount"], "")
                expected = frame_m.group(1).replace(set_a["SA01"]["medium"], phrase) if frame_m else None
                ok = expected is not None and t == expected
                note = "registration's frame with the bank's phrase"
                if frame_md and "**" in frame_md.group(1):
                    # One line per sentence, the added elements in bold, as in the registration's example
                    exp_lines = re.split(r"(?<=\.) (?=[A-Z])", bold_html(frame_md.group(1).replace(set_a["SA01"]["medium"], phrase)))
                    ok = ok and lines == exp_lines
                    note += ", one sentence per line, the elements in bold"
                if s["scene"] == "SA01" and s["amount"] == "medium":
                    ok = ok and t in reg
                    note += "; quoted in the registration"
                if s["scene"] == "SA01" and s["amount"] == "large":
                    ok = ok and t.split(". ", 1)[1] in bank_text
                    note += "; the bank's large example"
                res(ok, "registration and prompt bank", s, note)
        elif k == "comprehension":
            res(f'"{t}" ({s["key"]})' in reg, "registration", s, f'with its key ({s["key"]})')
        elif k == "tf_option":
            res(re.search(r"true[- ]or[- ]false", reg_lower) is not None, "registration", s, 'derived from "true or false"')
        elif k == "grid_column":
            if t in ("Yes", "No", "Not sure"):
                res("Yes, No or Not sure" in reg, "registration", s, 'from "answered Yes, No or Not sure"')
            else:   # A1's end scales: each answer label named in the registration's item
                res(t in reg, "registration", s, "answer label of an agreement grid")
        elif k == "scale_label":
            res(f'{s["value"]} {t}' in reg, "registration", s, f'written "{s["value"]} {t}"')
        elif k == "slider_anchor":
            res(f"({t})" in reg, "registration", s, f'written "({t})"')
        elif k == "anchor":
            n = 1 if s["end"] == "low" else s["points"]
            res(f"{n} ({t})" in reg or f"{n} {t}" in reg, "registration", s, f'written "{n} ({t})" or "{n} {t}"')
        elif k == "instructed":
            core = t.rstrip(".,")
            res(core in reg, "registration", s, "registration's running text ends the quoted item with a comma; shown with a period")
        elif k == "instructed_option":
            res(t.lower() in reg_lower, "registration", s, "registration lists the options in lower case; shown in sentence case")
        elif k in ("item", "option", "option_list"):
            path = s["path"]
            if path.startswith(("demographics.", "final.")):
                if k == "option_list":
                    ok = all(norm(x) in paper_one for x in s["labels"])
                else:
                    ok = t in paper_one
                res(ok, "Paper One", s, "Paper One Study 1 survey / IRB debriefing form")
                continue
            if k == "option_list":
                labels = [norm(x) for x in s["labels"]]
                slash = " / ".join(labels)
                if slash in reg:
                    res(True, "registration", s, "list written with slashes")
                elif all(f'"{x}"' in reg for x in labels):
                    res(True, "registration", s, "each option quoted")
                elif labels in (["Yes", "No"], ["True", "False"]) or set(labels) == {"True", "False"}:
                    res(re.search(r"true[- ]or[- ]false", reg_lower) is not None or "True" in reg, "registration", s, "true-or-false items")
                elif set(labels) == {"Yes", "No", "Not sure"}:
                    res("Yes, No or Not sure" in reg, "registration", s)
                else:
                    res(False, "registration", s, "option list not found")
                continue
            if t in reg:
                res(True, "registration", s)
            elif "{phrase}" in t and t.replace("{phrase}", set_a["SA01"]["medium"]) in reg:
                res(True, "registration", s, "{phrase} is each trial's added elements; the registration quotes the item with scene SA01's medium phrase")
            elif t.endswith(creativity_def) and t[: -len(creativity_def)].strip() in reg and creativity_def.rstrip(".") in reg:
                res(True, "registration", s, "stem and Paper One's definition, quoted separately in the registration")
            elif t.startswith(stem) and f'"... {t[len(stem) + 1:]}"' in reg and stem in reg:
                res(True, "registration", s, 'stem plus the registration\'s "..." continuation')
            elif k == "option" and t.rstrip(".") in reg:
                res(True, "registration", s)
            else:
                res(False, "registration", s, "not found verbatim")
        elif k == "consent":
            res(t in consent, "consent form", s)
        elif k == "consent_intro":
            res(t in paper_one, "Paper One", s, "Paper One's consent intro line")
        elif k == "debrief":
            if t in reg:
                res(True, "registration", s, "debriefing sentence quoted in the registration")
            else:
                results.append(("DEBRIEF", "registration (described, not quoted)", s["path"], s["text"], "compared word by word below"))
        elif k == "ui":
            raw = re.sub(r"\s+", " ", s["text"])
            pieces = [x.strip() for x in re.split(r"\{\w+\}|(?<=[.;])\s", raw) if len(x.strip()) > 3]
            if raw in template_raw:
                res(True, "template", s)
            elif pieces and all(x in template_raw for x in pieces):
                res(True, "template", s, "template builds it from these same pieces")
            elif t in paper_one:
                res(True, "Paper One", s)
            else:
                results.append(("NEW", "written for the engine", s["path"], s["text"], "not in any source"))
        elif k == "ui_new":
            results.append(("NEW", "written for the engine", s["path"], s["text"], "not in any source"))
        else:
            res(False, "?", s, "unknown kind " + k)

    # Debriefing: word-level comparison with the registration's paragraph.
    m = re.search(r"The debriefing, the same in every Paper A and Paper B study, (.*?)\n\n", reg_path.read_text(encoding="utf-8"), flags=re.S)
    reg_deb = md_norm(m.group(1)) if m else ""
    deb_quoted = all(r[0] != "DEBRIEF" for r in results)
    cfg_deb = " ".join(norm(s["text"]) for s in strings if s["kind"] == "debrief") if not deb_quoted else ""
    sm = difflib.SequenceMatcher(None, reg_deb.split(), cfg_deb.split(), autojunk=False)
    deb_diffs = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op != "equal":
            deb_diffs.append((op, " ".join(reg_deb.split()[i1:i2]), " ".join(cfg_deb.split()[j1:j2])))

    # Dashes
    dash_hits = [(s["path"], s["text"]) for s in strings if re.search("[–—]", s["text"])]

    # Statement word counts (B1 registration: o 54, a 49, r 51, b 53, c 56, d 59)
    wc_m = re.search(r"differ by at most five words \((.*?)\)", reg)
    reg_counts = dict(re.findall(r"\b([oarbcd]) (\d\d)\b", wc_m.group(1))) if wc_m else {}
    wc = {s["cell"]: word_count(s["text"]) for s in strings if s["kind"] == "statement"}
    a1_wc = {}
    for s in strings:
        if s["kind"] == "a1_statement":
            a1_wc.setdefault(s["amount"], []).append(word_count(s["text"]))

    # Report
    by = {}
    for st, src, path, text, note in results:
        by.setdefault((st, src), []).append((path, text, note))
    print(f"String check for {a.study}: {len(strings)} strings from {a.study}/config.js\n")
    for (st, src), items in sorted(by.items(), key=lambda kv: (kv[0][0] != "FAIL", kv[0])):
        if st == "PASS":
            print(f"{st:4s}  {len(items):3d}  source: {src}")
    for (st, src), items in sorted(by.items()):
        if st in ("FAIL", "NEW") or (st == "PASS" and any(n for _, _, n in items)):
            print(f"\n{st} ({src}):" if st != "PASS" else f"\nPASS with a note ({src}):")
            for path, text, note in items:
                if st == "PASS" and not note:
                    continue
                print(f"  - {path}: {text[:110]!r}" + (f"  [{note}]" if note else ""))
    if deb_quoted:
        print("\nDebriefing: every sentence is quoted in the registration (checked above).")
    else:
        print("\nDebriefing: the registration describes it; differences from its wording (registration -> page):")
        for op, r_, c_ in deb_diffs:
            print(f"  {op:8s} {r_!r} -> {c_!r}")
    if wc:
        print("\nStatement word counts (page / registration): " + ", ".join(
            f"{c} {wc.get(c)}/{reg_counts.get(c)}" for c in "oarbcd"))
        wc_ok = all(str(wc.get(c)) == reg_counts.get(c) for c in "oarbcd")
    else:
        wc_ok = True
    if a1_wc:
        print("\nStatement word counts by amount (the same under both stories by construction): " + "; ".join(
            f"{a} {min(v)} to {max(v)}" for a, v in a1_wc.items()))
    print("Em or en dashes in participant-facing strings: " + ("none" if not dash_hits else str(dash_hits)))
    n_fail = sum(1 for r in results if r[0] == "FAIL")
    print(f"\nSummary: {sum(1 for r in results if r[0] == 'PASS')} pass, {n_fail} fail, "
          f"{sum(1 for r in results if r[0] == 'NEW')} new screen strings, word counts {'match' if wc_ok else 'DIFFER'}.")
    sys.exit(1 if (n_fail or dash_hits or not wc_ok) else 0)


if __name__ == "__main__":
    main()
