#!/usr/bin/env python3
"""Check A1's lists and per-participant formulas against the registration.

    python3 tools/test_formulas_A1.py [--csv-dir DIR]

Part 1 rebuilds, from the registration and the prompt bank and not from the
page code, what they fix, and compares it with A1/config.js run under node:
  * the interleaved scene order, read from the registration's Randomization
    paragraph; which scenes have a person, read from the bank's headings;
  * the slots, read from the same paragraph: amount by slot pair, the AI and
    hand-made slots of block 1, slots 8 and 9 in block 2;
  * list k: slot j shows the scene at position (j + k) mod 10; the files;
  * every statement, built from the registration's sentence frame (its SA01
    medium example, one sentence per line, the added elements in bold, and its
    no-change sentence) and the bank's current Set A phrases, with the large
    amount naming the medium element and the two further ones; statements
    never depend on the story;
  * the title of every page that shows a trial (the registration's reminder
    lines, with their bold words) and the image labels, from the registration;
  * option order floor(code / 10) mod 3, creativity-item order floor(code / 30)
    mod 2, story-recall trial floor(code / 60) mod 2 (slot 0 or 1), for codes
    0 to 1199;
  * each trial's pages (config 1.5.0): the story page (the registration's two
    sentences per story, at least 3 s), the first image alone (at least 5 s),
    the change page (title and statement above the pair, at least 10 s), the
    question page (the pair in a column beside the questions), the written
    reason;
  * the items of each trial's question page: the creativity items in the
    participant's order, each with Paper One's definition below its question;
    the addition item (naming the trial's added elements) and the jury item on
    change trials only; the rule reminder (its heading and the rule's two sentences, from
    the rule page) above the decision in block 2 only; no per-trial belief
    check; the written reason on every trial (config 1.4.0), on its own third
    page, below the quoted decision;
  * the follow-up section between the blocks (since 1.3.0): its introductory
    page, then slots 6 and 7 again, each on two pages: the "would" line and
    item (with the decision's options, follow-up and confidence, all in the
    'would_block' drop group); then the stop-others stem, items 1 to 3 each
    with its own question, and item 4 on the AI page only; no "would" block at
    the end; the story-recall page's line;
  * the balance the registration claims: within a list, each story in block 1
    on two scenes with a person and two without, each amount on one of each,
    the follow-up trials (slots 6 and 7) on one of each; across the ten lists
    every scene in every slot once. Also checked: any 120 consecutive codes
    give every combination of list, option order, item order and recall trial
    exactly once.
The registration names the openings of the lines that quote the participant's
decision ("You chose:" and "Left out:"); their exact form (the label in curly
quotation marks, the period inside) is taken from the change specification,
Docs/Paper Two/_internal_notes/A1_page_revision_2026-11-01.md, section 14.
Part 2 (with --csv-dir) checks every saved session in DIR field by field,
including each trial's five pages (story; first image, at least 5 s; change
page, at least 10 s; question page; written reason below the quoted
decision), the two end scales and their scores, the follow-up answers on the
rows of slots 6 and 7 ("would" item, stop-others items, item 4 on slot 7 only;
the "would" item absent when the timing-gate remedy drops it), and the absence
of the removed columns (per-trial belief check, believability ratings,
first-image page, "would" block).
Part 3 (with --csv-dir) checks that every column documented in A1/README.md
is in every saved CSV and that no CSV has an undocumented column.
"""
import argparse
import csv
import io
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent           # .../Stimuli/Paper Two/Pavlovia
ROOT = HERE.parents[2]
REG = ROOT / "Docs" / "Paper Two" / "_source" / "Prereg_A1.md"
BANK = ROOT / "Docs" / "Paper Two" / "Paper_Two_Prompt_Bank.md"
SPEC = ROOT / "Docs" / "Paper Two" / "_internal_notes" / "A1_page_revision_2026-11-01.md"
ORDERS = ["whole;part;refuse", "part;refuse;whole", "refuse;whole;part"]
FAILS = []


def check(cond, msg):
    if not cond:
        FAILS.append(msg)
    return cond


def flat(s):
    return re.sub(r"\s+", " ", s.replace("*", "")).strip()


def bold_html(s):
    """Markdown bold (**...**) as the page writes it (<strong>...</strong>)."""
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)


def plain(s):
    return re.sub(r"<[^>]+>", "", s)


# ---------- What the registration and the bank fix ----------

def registration():
    raw = re.sub(r"\s+", " ", REG.read_text(encoding="utf-8"))
    reg = flat(raw)
    m = re.search(r"interleaved order ((?:SA[-0-9R]+, )+SA[-0-9R]+),", reg)
    order = [x.strip() for x in m.group(1).split(",")]
    amounts = {}
    m = re.search(r"slots (\d) and (\d) carry no change, (\d) and (\d) the small addition, (\d) and (\d) the medium, and (\d) and (\d) the large", reg)
    g = [int(x) for x in m.groups()]
    for i, amt in enumerate(["none", "small", "medium", "large"]):
        amounts[g[2 * i]] = amt
        amounts[g[2 * i + 1]] = amt
    m = re.search(r"the AI story takes slots (\d), (\d), (\d) and (\d), and the hand-made story slots (\d), (\d), (\d) and (\d)", reg)
    g = [int(x) for x in m.groups()]
    story = {j: "ai" for j in g[:4]}
    story.update({j: "hand" for j in g[4:]})
    m = re.search(r"Slot (\d) carries the AI story and slot (\d) the hand-made story, both at the large addition, in block 2", reg)
    s8, s9 = int(m.group(1)), int(m.group(2))
    story[s8], story[s9] = "ai", "hand"
    amounts[s8] = amounts[s9] = "large"
    m = re.search(r"as do the two trials of the follow-up section \(slots (\d) and (\d)\)", reg)
    follow_slots = [int(m.group(1)), int(m.group(2))]
    # The rule paragraph, and the reminder's heading and the span of it the reminder repeats
    rule = re.search(r"recall items \(item \d+\): > (.*?) Measured, in order of presentation", reg).group(1).strip()
    rm = re.search(r'a box above it shows the heading "(.*?)" and the rule paragraph\'s two sentences that state the rule, from "(.*?)" to "(.*?)"', reg)
    span = rule[rule.index(rm.group(2)):rule.index(rm.group(3)) + len(rm.group(3))]
    reminder = ["<strong>" + rm.group(1) + "</strong>"] + re.split(r"(?<=\.) (?=[A-Z])", span)
    # The SA01 medium statement, with its bold words, and the no-change sentence
    frame_md = re.search(r'Scene SA01 at the medium amount reads: "(.*?)"', raw).group(1)
    none = re.search(r'No-change trials read: "(.*?)"', reg).group(1)
    titles = re.search(r'\("(First image: [^"]*)" or "(First image: [^"]*)"\)', raw)
    # No-change trials: the one image under a reminder line without "First image" (2 November 2026)
    titles_one = re.search(r'reminder line without "First image" \("(.*?)" or "(.*?)"\)', raw)
    one_item = re.search(r'the other reads "(How much creativity went into making this image\?)"', reg).group(1)
    captions = re.search(r'labeled "([^"]*)" and "([^"]*?),?"', reg)
    story_m = re.search(r'for an AI-made first image, "(.*?)" and, for Alex\'s painting, "(.*?)"', raw)
    trial_story = {k: re.split(r"(?<=\.) (?=[A-Z])", bold_html(story_m.group(i))) for k, i in (("ai", 1), ("hand", 2))}
    mins = re.search(r"The first, the story page, says in two sentences how Alex made the first image \(Manipulated\) and stays on screen "
                     r"for at least (\d+) seconds\. The second shows the first image alone, labeled \"First image,\" for at least (\d+) seconds", reg)
    gaais = re.search(r"The instructions read: \"(.*?)\" The items, each answered (.*?) \(coded 1 to 5\), are, (.*?) Scored as", reg)
    acb = re.search(r'on its own page: "(To what extent .*?\?)" (.*?) Each is answered (.*?), the wording and scale', reg)
    stop = re.search(r'the stem "(.*?)" and then each scenario with its own question, "(.*?)"', reg)
    scen = re.search(r'\(1\) "(.*?)" \(2\) "(.*?)" \(3\) "(.*?)" The page of the AI-made first image adds \(4\) "(.*?)"', reg)
    deci = re.search(r"What should the Office do\? > - (.*?) > - (.*?) > - (Refuse to register it)", reg)
    # No-change trials show one image and word the decision about "this image" (2 November 2026)
    deci_one = re.search(r"which show one image, it reads: > .*?What should the Office do\? > - (.*?) > - (.*?) > - (Refuse to register it)", reg)
    fu = re.search(r'"Which part should be left out of the registration\?" \((.*?)\)', reg).group(1).split(" / ")
    return {
        "order": order, "amount": amounts, "story": story, "block2": [s8, s9],
        "follow_slots": sorted(follow_slots), "rule": rule,
        "frame_md": frame_md, "frame": flat(frame_md), "none": none,
        "title": {"ai": bold_html(titles.group(1)), "hand": bold_html(titles.group(2))},
        "title_one": {"ai": bold_html(titles_one.group(1)), "hand": bold_html(titles_one.group(2))},
        "creativity_item_one": one_item,
        "captions": [captions.group(1), captions.group(2).rstrip(",")],
        "stop_stem": stop.group(1), "stop_question": stop.group(2), "stop_items": list(scen.groups()),
        "follow_intro": re.search(r'An introductory page reads "(.*?)"', reg).group(1),
        "would_note": re.search(r'"Would" item, below the line "(.*?)",', reg).group(1),
        "would_item": re.search(r"its confidence item: > (.*?\?)", reg).group(1),
        "reason_question": re.search(r'quotation marks\. The question reads "(.*?)" Free text', reg).group(1),
        "quote_openings": re.search(r'quotes the participant\'s registration decision on that trial, "(.*?)" followed by .*?"(Left out:)" followed by', reg).groups(),
        "reason_every_trial": "Written reason, last on its trial, on its own page right after the question page" in reg
                              and "Every trial has these five pages and no others." in reg,
        "recall_line": re.search(r'a page headed "(.*?)"', reg).group(1),
        "creativity_def": re.search(r'shown below each item\'s question, as in Paper One: "(.*?)"', reg).group(1),
        "trial_story": trial_story, "story_min": int(mins.group(1)), "first_image_min": int(mins.group(2)),
        "gaais_instructions": re.split(r"(?<=[.]) (?=[A-Z])", gaais.group(1)),
        "gaais_labels": [x.strip() for x in re.split(r", | or ", gaais.group(2))],
        "gaais_items": [(k.lower(), t) for k, t in re.findall(r'(Positive|Negative): "(.*?)"', gaais.group(3))],
        "acb_stem": acb.group(1), "acb_items": re.findall(r'"(.*?)"', acb.group(2)),
        "acb_labels": re.findall(r"\d ([A-Z][a-z]+(?: [a-z]+)*?)(?=,| \d|$)", acb.group(3)),
        "creativity_items": re.search(r'The items are "(.*?)" and "(.*?)"', reg).groups(),
        "rule_reminder": reminder,
        # Labels by the page's option values, in the order the registration lists them
        "decision_labels": dict(zip(["whole", "part", "refuse"], deci.groups())),
        "decision_labels_one": dict(zip(["whole", "part", "refuse"], deci_one.groups())),
        "followup_labels": dict(zip(["first_image", "added", "something_else", "not_sure"], fu)),
        "text": reg,
    }


def spec_quote_forms():
    """The lines quoting the participant's decision above the written reason, from
    the change specification (section 14)."""
    t = SPEC.read_text(encoding="utf-8").split("## 14.", 1)[1]
    chosen = re.search(r'"(You chose: “)\{decision label\}(\.”)"', t)
    left = re.search(r'"(Left out: “)\{follow-up label\}(\.”)"', t)
    return {"chosen": chosen.group(1) + "{label}" + chosen.group(2), "followUp": left.group(1) + "{label}" + left.group(2)}


def bank():
    """Current Set A phrases and person flags from the bank's scene sections."""
    scenes, cur = {}, None
    for line in BANK.read_text(encoding="utf-8").splitlines():
        m = re.match(r"### (SA-?R?\d+)\. .*\((person|people|no person)[,)]", line)
        if m:
            cur = m.group(1)
            scenes[cur] = {"person": m.group(2) in ("person", "people")}
            continue
        if line.startswith("## Set B"):
            cur = None
        if cur:
            m = re.match(r"\| (Small|Medium|Large, added to the medium file) \| (.*) \|$", line)
            if m:
                key = {"Small": "small", "Medium": "medium"}.get(m.group(1), "large")
                scenes[cur][key] = m.group(2).strip()
    return scenes


def phrase_of(B, scene, amount):
    return B[scene]["medium"] + ", " + B[scene]["large"] if amount == "large" else B[scene][amount]


def expected_statement(R, B, scene, amount):
    """The statement's lines as the page writes them: one sentence per line,
    the added elements in bold (the registration's SA01 medium example)."""
    if amount == "none":
        return [R["none"]]
    sa01_medium = B["SA01"]["medium"]
    assert f"**{sa01_medium}**" in R["frame_md"], "the registration's SA01 example no longer names the bank's SA01 medium phrase in bold"
    frame = bold_html(R["frame_md"].replace(sa01_medium, phrase_of(B, scene, amount)))
    return re.split(r"(?<=\.) (?=[A-Z])", frame)


def expected_list(R, B, k):
    trials = []
    for j in range(10):
        s = R["order"][(j + k) % 10]
        amt = R["amount"][j]
        trials.append({
            "slot": j, "block": 2 if j in R["block2"] else 1, "story": R["story"][j], "amount": amt,
            "cell": f"{R['story'][j]}_{amt}", "scene": s, "scene_position": (j + k) % 10,
            "scene_has_person": B[s]["person"], "source_file": f"{s}_source.jpg",
            "second_file": f"{s}_{'source' if amt == 'none' else amt}.jpg",
            "has_addition": amt != "none", "has_follow_up": j in R["follow_slots"],
            "statement": expected_statement(R, B, s, amt),
            "phrase": phrase_of(B, s, amt) if amt != "none" else "",
        })
    return trials


def expected_items(t, item_order):
    if not t["has_addition"]:
        qs = ["creativity_whole"]
    else:
        qs = ["creativity_whole", "creativity_addition"] if item_order == 0 else ["creativity_addition", "creativity_whole"]
    qs += ["decision", "confidence", "share"]
    if t["has_addition"]:
        qs += ["jury"]
    return qs


def expected_quote(R, Q, decision, followup, one_image=False):
    """The quoted decision as saved: the lines joined by a space, without tags. A no-change
    trial quotes its own wording ("the image") and has no follow-up."""
    out = Q["chosen"].replace("{label}", R["decision_labels_one" if one_image else "decision_labels"][decision])
    if decision == "part" and not one_image:
        out += " " + Q["followUp"].replace("{label}", R["followup_labels"][followup])
    return plain(out)


def derive(code):
    return {"option": (code // 10) % 3, "item": (code // 30) % 2, "recall": (code // 60) % 2}


CONFIG = HERE / "A1" / "config.js"


def node_dump():
    js = r"""
const fs=require('fs'),vm=require('vm');const ctx={window:{}};vm.createContext(ctx);
vm.runInContext(fs.readFileSync(process.argv[1],'utf8'),ctx);const C=ctx.window.STUDY_CONFIG;
const fillv=(x,v)=>(Array.isArray(x)?x:[x]).map(l=>String(l).replace(/\{(\w+)\}/g,(m,k)=>v&&v[k]!==undefined?v[k]:m));
const revisit=[].concat(...C.blocks.map(b=>(b.before||[]).filter(p=>p.revisit)));
const rows=[];
for(let k=0;k<C.nRows;k++){
  const r=C.buildRow(k);
  const trials=r.trials.map(t=>{
    const c=C.trialContent(t), rc=C.recall.content(t);
    const qs=io=>C.trialQuestionsFor(t,{item_order:io});
    const items=[0,1].map(io=>qs(io).filter(q=>q.type!=='note').map(q=>q.id));
    const notes=qs(0).filter(q=>q.type==='note').map(q=>({id:q.id,text:q.text,cls:q.className||''}));
    const firstIsNote=qs(0)[0].type==='note';
    const texts={};qs(0).forEach(q=>{if(q.text)texts[q.id]=fillv(q.text,c.vars);});
    const rv=revisit.filter(sp=>sp.revisit(t,{})).map(sp=>({id:sp.id,pages:(sp.pages||[sp]).map(pg=>{const sq=pg.questionsFor?pg.questionsFor(t,{}):pg.questions;
      const nn=sq.filter(q=>q.type!=='note');
      return {id:pg.id,quoteBefore:pg.quoteBefore||null,items:nn.map(q=>q.id),notes:sq.filter(q=>q.type==='note').map(q=>({text:q.text,cls:q.className||'',group:q.dropGroup||null})),
        texts:nn.map(q=>q.text),types:nn.map(q=>q.type),groups:nn.map(q=>q.dropGroup||null),anchors:nn.map(q=>q.anchors||null),
        points:nn.map(q=>q.points?q.points.length:null),options:nn.map(q=>q.type==='decision'?q.options:null),
        followUp:nn.map(q=>q.followUp?{text:q.followUp.text,labels:q.followUp.options.map(o=>o.label),showIf:q.followUp.showIf}:null),
        firstIsNote:sq[0].type==='note'};})}));
    return Object.assign({},t,{content:c,recallContent:rc,items,notes,firstIsNote,texts,revisit:rv,recallKey:C.recall.correct(t)});
  });
  rows.push({row:r.row,list:r.list,trials:trials});
}
const der={};for(let code=0;code<1200;code++){const k=code%10;const d=C.derive(code,C.buildRow(k),()=>{throw new Error('rnd used with a numeric code')});
  der[code]={option:d.option_order_index,order:d.option_order.join(';'),item:d.item_order,recall:d.recall_index,recall_position:d.recall_position,
    recall_story:d.recall_story,follow:d.follow_up_positions.join(';'),reason:d.reason_positions.join(';')};}
const dq=C.trialQuestions.filter(q=>q.type==='decision')[0];
const t0=C.buildRow(0).trials[2];
const ends={};C.endPages.forEach(p=>{ends[p.id]={wide:!!p.wide,items:p.items.map(q=>({id:q.id,type:q.type,text:q.text||null,cls:q.className||'',
  rows:q.rows?q.rows.map(r=>[r.id,r.label]):null,columns:q.columns?q.columns.map(c=>[c.value,c.label]):null}))};});
process.stdout.write(JSON.stringify({rows,der,minView:C.minViewSeconds,viewPage:!!C.viewPage,preScreen:!!C.preScreen,
  hasWould:!!C.would,reasonQuestion:C.reasonQuestion||null,reasonQuote:C.reasonQuote,
  story:{ai:C.trialStory({story:'ai'}),hand:C.trialStory({story:'hand'})},
  pre:{min:C.preScreen.minViewSeconds,content:C.preScreen.content(t0),file:t0.source_file},
  questionLayout:C.questionLayout||null,pairTextBelow:!!C.pairTextBelow,ends:ends,endIds:C.endPages.map(p=>p.id),
  decisionOptions:dq.options,decisionFollowUp:{text:dq.followUp.text,labels:dq.followUp.options.map(o=>o.label),showIf:dq.followUp.showIf},
  afterTrialScreens:(C.afterTrialScreens||[]).length,
  blocks:C.blocks.map(b=>({id:b.id,before:(b.before||[]).map(p=>p.id),beforeText:(b.before||[]).filter(p=>p.paragraphs).map(p=>({id:p.id,paragraphs:p.paragraphs,min:p.minSeconds||0}))}))}));"""
    return json.loads(subprocess.check_output(["node", "-e", js, str(CONFIG)]))


def part1(R, B):
    d = node_dump()
    check(len(R["order"]) == 10 and len(set(R["order"])) == 10, f"registration order: {R['order']}")
    check(all(B[s]["person"] == (i % 2 == 0) for i, s in enumerate(R["order"])),
          "registration claim: even positions hold scenes with a person (bank headings)")
    check(sorted(R["amount"]) == list(range(10)) and sorted(R["story"]) == list(range(10)), "slots 0 to 9 not all fixed by the registration")
    scene_slot = Counter()
    for k in range(10):
        exp = expected_list(R, B, k)
        got = d["rows"][k]["trials"]
        check(len(got) == 10, f"list {k}: {len(got)} trials")
        for g, e in zip(got, exp):
            j = e["slot"]
            for key in ["slot", "block", "story", "amount", "cell", "scene", "scene_position", "scene_has_person",
                        "source_file", "second_file", "has_addition", "has_follow_up"]:
                check(g[key] == e[key], f"list {k} slot {j}: {key} {g[key]!r} != {e[key]!r}")
            check(g["list_position"] == j, f"list {k} slot {j}: list_position")
            check(g["content"]["statement"] == e["statement"], f"list {k} slot {j}: statement {g['content']['statement']!r} != {e['statement']!r}")
            imgs = g["content"]["images"]
            # A no-change trial shows the one image, unlabeled, under its own title (2 November 2026)
            one = not e["has_addition"]
            exp_files = [e["source_file"]] if one else [e["source_file"], e["second_file"]]
            exp_caps = [None] if one else R["captions"]
            exp_title = R["title_one" if one else "title"][e["story"]]
            check([i["file"] for i in imgs] == exp_files, f"list {k} slot {j}: image files")
            check([i.get("caption") for i in imgs] == exp_caps, f"list {k} slot {j}: captions {[i.get('caption') for i in imgs]}")
            check(g["content"].get("title") == exp_title and not g["content"].get("lines"),
                  f"list {k} slot {j}: title {g['content'].get('title')!r} != {exp_title!r}")
            check([i["file"] for i in g["recallContent"]["images"]] == [e["source_file"]] and g["recallContent"].get("lines") == [R["recall_line"]],
                  f"list {k} slot {j}: recall page")
            check(g["recallKey"] == e["story"], f"list {k} slot {j}: recall key")
            for io_ in (0, 1):
                check(g["items"][io_] == expected_items(e, io_), f"list {k} slot {j} item order {io_}: items {g['items'][io_]}")
            # Notes: only the rule reminder, in block 2 (the definition is inside each creativity item)
            exp_notes = [("rule_reminder", R["rule_reminder"], "boxed")] if e["block"] == 2 else []
            check([(n["id"], n["text"], n["cls"]) for n in g["notes"]] == exp_notes and not g["firstIsNote"], f"list {k} slot {j}: notes {g['notes']}")
            # Item texts: the question, then Paper One's definition below it; the addition item names this trial's added elements
            cw, ca = R["creativity_items"]
            dfn = '<span class="q-def">' + R["creativity_def"] + '</span>'
            check(g["texts"]["creativity_whole"] == [R["creativity_item_one"] if one else cw, dfn], f"list {k} slot {j}: whole-image item {g['texts']['creativity_whole']}")
            if e["has_addition"]:
                exp_ca = ca.replace(B["SA01"]["medium"], e["phrase"])
                check(g["texts"]["creativity_addition"] == [exp_ca, dfn], f"list {k} slot {j}: addition item {g['texts']['creativity_addition']} != {exp_ca!r}")
            check(plain(" ".join(g["texts"]["decision"])) in R["text"] and len(g["texts"]["decision"]) == 3, f"list {k} slot {j}: decision text {g['texts']['decision']}")
            # Follow-up section: slots 6 and 7 only, each on two pages; item 4 on the AI page only
            if e["has_follow_up"]:
                rv = g["revisit"]
                ok = len(rv) == 1 and rv[0]["id"] == "follow_up" and [p["id"] for p in rv[0]["pages"]] == ["follow_up_would", "follow_up_stop"]
                check(ok, f"list {k} slot {j}: follow-up pages {rv}")
                if ok:
                    po, ps = rv[0]["pages"]
                    ok_o = (po["items"] == ["would_decision", "would_confidence"] and po["firstIsNote"]
                            and po["notes"] == [{"text": R["would_note"], "cls": "plain", "group": "would_block"}]
                            and po["texts"][0] == R["would_item"]
                            and po["types"] == ["decision", "slider"] and po["groups"] == ["would_block", "would_block"]
                            and po["options"][0] == d["decisionOptions"] and po["followUp"][0] == d["decisionFollowUp"]
                            and po["quoteBefore"] is None)
                    check(ok_o, f"list {k} slot {j}: first follow-up page {po}")
                    exp_items = ["stop1", "stop2", "stop3"] + (["stop4"] if e["story"] == "ai" else [])
                    scen = R["stop_items"][:len(exp_items)]
                    ok_s = (ps["items"] == exp_items and [n["text"] for n in ps["notes"]] == [R["stop_stem"]] and ps["firstIsNote"]
                            and ps["texts"] == [[x, R["stop_question"]] for x in scen] and ps["quoteBefore"] is None
                            and all(a == ["definitely not", "definitely yes"] for a in ps["anchors"]) and all(p == 7 for p in ps["points"])
                            and all(gr is None for gr in ps["groups"]))
                    check(ok_s, f"list {k} slot {j}: stop-others page {ps}")
            else:
                check(g["revisit"] == [], f"list {k} slot {j}: follow-up pages on a trial outside the follow-up section")
            scene_slot[(e["scene"], j)] += 1
        # Balance within the list (registration, Randomization)
        b1 = [t for t in exp if t["block"] == 1]
        for st in ("ai", "hand"):
            kinds = Counter(t["scene_has_person"] for t in b1 if t["story"] == st)
            check(kinds == Counter({True: 2, False: 2}), f"list {k}: story {st} in block 1 on {dict(kinds)}")
        for amt in ("none", "small", "medium", "large"):
            kinds = sorted(t["scene_has_person"] for t in b1 if t["amount"] == amt)
            check(kinds == [False, True], f"list {k}: amount {amt} in block 1 not one of each kind")
        for name, slots in (("follow-up", R["follow_slots"]), ("block 2", R["block2"])):
            kinds = sorted(exp[j]["scene_has_person"] for j in slots)
            check(kinds == [False, True], f"list {k}: {name} trials not one of each kind")
        check(len({t["cell"] for t in b1}) == 8, f"list {k}: block 1 does not cover the eight cells")
        check(len({t["scene"] for t in exp}) == 10, f"list {k}: a scene twice")
    check(all(scene_slot[(s, j)] == 1 for s in R["order"] for j in range(10)), "across lists, not every scene in every slot once")
    # The two follow-up slots are the block-1 large-addition cells, one under each story: the cells G compares.
    check(sorted(R["story"][j] + "_" + R["amount"][j] for j in R["follow_slots"]) == ["ai_large", "hand_large"]
          and all(j not in R["block2"] for j in R["follow_slots"]), "follow-up slots")
    # Derivations
    combos = Counter()
    for code_s, g in d["der"].items():
        code = int(code_s)
        e = derive(code)
        check(g["option"] == e["option"] and g["order"] == ORDERS[e["option"]], f"code {code}: option order {g['order']}")
        check(g["item"] == e["item"], f"code {code}: item order {g['item']}")
        check(g["recall"] == e["recall"] and g["recall_position"] == e["recall"], f"code {code}: recall trial")
        check(g["recall_story"] == R["story"][e["recall"]] and R["amount"][e["recall"]] == "none", f"code {code}: recall story")
        check(g["follow"] == ";".join(map(str, R["follow_slots"])), f"code {code}: follow-up slots")
        check(g["reason"] == ";".join(map(str, range(10))), f"code {code}: written reason not on every trial")
        combos[(code // 120, code % 10, e["option"], e["item"], e["recall"])] += 1
    per_block = Counter(key[0] for key in combos)
    check(all(v == 1 for v in combos.values()) and all(v == 120 for v in per_block.values()),
          "120 consecutive codes do not give every combination once")
    rq = d["reasonQuestion"] or {}
    check(d["minView"] == 10 and d["viewPage"] and d["preScreen"] and d["afterTrialScreens"] == 0 and not d["hasWould"]
          and d["questionLayout"] == "side" and not d["pairTextBelow"],
          f"pages and minimum times: change page {d['minView']} s, viewPage {d['viewPage']}, first-image page {d['preScreen']}, "
          f"after-trial screens {d['afterTrialScreens']}, 'would' block {d['hasWould']}, layout {d['questionLayout']}, text below {d['pairTextBelow']}")
    for st in ("ai", "hand"):
        check(d["story"][st]["paragraphs"] == R["trial_story"][st] and d["story"][st]["minSeconds"] == R["story_min"],
              f"story page ({st}) {d['story'][st]} != registration {R['trial_story'][st]}, {R['story_min']} s")
    check(d["pre"]["min"] == R["first_image_min"] and d["pre"]["content"] == {"lines": [], "images": [{"file": d["pre"]["file"], "caption": R["captions"][0]}]},
          f"first-image page {d['pre']}")
    # End scales: the Short GAAIS-10 page and the beliefs page, between experience and knowledge, on wide pages
    E = d["ends"]
    check(d["endIds"] == ["belief", "purpose", "ownership", "experience", "gaais", "creativity_beliefs", "knowledge"], f"end pages {d['endIds']}")
    check(all(q["id"] != "attitude" for q in E["experience"]["items"]), "the single attitude item is still on the experience page")
    gi = E["gaais"]["items"]
    check(E["gaais"]["wide"] and len(gi) == 2 and gi[0]["type"] == "note" and gi[0]["text"] == R["gaais_instructions"] and gi[0]["cls"] == "plain"
          and gi[1]["type"] == "grid" and gi[1]["text"] is None
          and [lab for _, lab in gi[1]["rows"]] == [t for _, t in R["gaais_items"]]
          and all(rid.startswith(kind[:3]) for (rid, _), (kind, _) in zip(gi[1]["rows"], R["gaais_items"]))
          and gi[1]["columns"] == [[i + 1, lab] for i, lab in enumerate(R["gaais_labels"])],
          f"Short GAAIS-10 page {gi} against the registration")
    ai = E["creativity_beliefs"]["items"]
    check(E["creativity_beliefs"]["wide"] and len(ai) == 1 and ai[0]["type"] == "grid" and ai[0]["text"] == R["acb_stem"]
          and [lab for _, lab in ai[0]["rows"]] == R["acb_items"] and ai[0]["columns"] == [[i + 1, lab] for i, lab in enumerate(R["acb_labels"])],
          f"beliefs page {ai} against the registration")
    check(R["reason_every_trial"] and rq.get("id") == "written_reason" and rq.get("type") == "text" and rq.get("text") == R["reason_question"],
          f"written reason {rq} against the registration")
    check([b["id"] for b in d["blocks"]] == [1, 2] and d["blocks"][0]["before"] == []
          and d["blocks"][1]["before"] == ["follow_up_intro", "follow_up", "rule", "rule_recall"], f"blocks {d['blocks']}")
    texts = {p["id"]: p for p in d["blocks"][1]["beforeText"]}
    check(" ".join(texts["follow_up_intro"]["paragraphs"]) == R["follow_intro"] and len(texts["follow_up_intro"]["paragraphs"]) == 2,
          f"follow-up introduction {texts['follow_up_intro']['paragraphs']}")
    check(" ".join(texts["rule"]["paragraphs"]) == R["rule"] and len(texts["rule"]["paragraphs"]) == 4 and texts["rule"]["min"] == 5,
          f"rule page {texts['rule']}")
    check(R["rule_reminder"][1:] == texts["rule"]["paragraphs"][1:3], f"rule reminder lines {R['rule_reminder']} are not the rule page's")
    Q = spec_quote_forms()
    check(d["reasonQuote"] == Q, f"quoted-answer lines {d['reasonQuote']} != specification {Q}")
    check(plain(Q["chosen"]).startswith(R["quote_openings"][0]) and Q["followUp"].startswith(R["quote_openings"][1]),
          f"quoted-answer openings {Q} != registration {R['quote_openings']}")
    print(f"Part 1: 10 lists and 1,200 codes recomputed from the registration and the bank. Order {', '.join(R['order'])}; "
          f"every scene in every slot once: {all(scene_slot[(s, j)] == 1 for s in R['order'] for j in range(10))}; "
          f"40 statements checked; combinations per 120 codes: {len(combos) // len(per_block)} of 120.")
    return d


REMOVED_COLUMNS = ["trial_belief", "believe_ai", "believe_hand", "would_pre_page_ms", "trial_page_ms", "stop4_stem", "attitude",
                   # since 1.3.0: no in-trial written reason, no "would" block, no stop-others section of its own
                   "would_shown", "would_order", "would_page_ms", "would_block_shown",
                   "would_intro_page_ms", "reason_positions", "stop_positions", "has_stop_items", "stop_others_order",
                   "stop_others_page_ms", "stop_others_intro_page_ms", "follow_up_office_page_ms"]


def part2(R, B, csv_dir):
    files = sorted(Path(csv_dir).glob("*.csv"))
    summary, rows_hit, opts_hit, items_hit, recall_hit = Counter(), set(), set(), set(), set()
    n_followups = n_quotes = n_quotes_divided = n_stop_rows = n_would = 0
    Q = spec_quote_forms()
    for f in files:
        rows = list(csv.DictReader(io.StringIO(f.read_text(encoding="utf-8"))))
        r0 = rows[0]
        tag = f.name
        present = [c for c in REMOVED_COLUMNS if c in r0]
        check(not present, f"{tag}: removed columns still in the file: {present}")
        code = int(r0["code"]) if r0["code"].isdigit() else None
        open_rows = [int(x) for x in r0["open_rows"].split(";")]
        k = int(r0["row"])
        src = r0["assignment_source"]
        if src == "code_mod_open_rows":
            check(k == open_rows[code % len(open_rows)], f"{tag}: row {k} != open_rows[code mod n]")
            check(int(r0["open_rows_index"]) == code % len(open_rows), f"{tag}: open_rows_index")
        elif src == "url_row":
            check("row" in tag or "forced" in tag, f"{tag}: forced row without ?row=")
        else:
            check(src == "random_no_numeric_code" and code is None, f"{tag}: assignment source {src}")
        check(int(r0["list"]) == k and r0["n_rows"] == "10", f"{tag}: list fields")
        if code is not None:
            e = derive(code)
            check(r0["option_order"] == ORDERS[e["option"]] and int(r0["option_order_index"]) == e["option"], f"{tag}: option order")
            check(int(r0["item_order"]) == e["item"] and r0["item_order_label"] == ["whole_first", "addition_first"][e["item"]], f"{tag}: item order")
            check(int(r0["recall_index"]) == e["recall"] and int(r0["recall_position"]) == e["recall"], f"{tag}: recall trial")
            for col, val in (("option_order_source", "floor(code/10) mod 3"), ("item_order_source", "floor(code/30) mod 2"),
                             ("recall_index_source", "floor(code/60) mod 2")):
                check(r0[col] == val, f"{tag}: {col}")
        else:
            for col in ("option_order_source", "item_order_source", "recall_index_source"):
                check(r0[col] == "random_no_numeric_code", f"{tag}: {col}")
        exp = expected_list(R, B, k)
        rp = int(r0["recall_position"])
        check(r0["recall_story"] == exp[rp]["story"] and r0["recall_scene"] == exp[rp]["scene"] and r0["recall_file"] == exp[rp]["source_file"],
              f"{tag}: recall trial fields")
        check(r0["follow_up_positions"] == ";".join(map(str, R["follow_slots"])), f"{tag}: follow-up positions")
        rows_hit.add(k)
        opts_hit.add(r0["option_order"])
        items_hit.add(r0["item_order"])
        recall_hit.add(r0["recall_position"])
        reason = r0["exit_reason"]
        summary[reason] += 1
        pages = [p["id"] for p in json.loads(r0["page_timestamps"])]
        if reason != "complete":
            check(r0["session_complete"] == "false" and r0["trial_position"] == "" and len(rows) == 1, f"{tag}: early exit has trial rows")
            if reason == "comprehension_failed":
                check(r0["comp_failed_twice"] == "true" and r0["excl_comprehension"] == "true", f"{tag}: comprehension flags")
                check(r0["comp_attempt1_pass"] == "false" and r0["comp_attempt2_pass"] == "false", f"{tag}: comprehension attempts")
                check("story" not in pages, f"{tag}: story shown after two failures")
            elif reason == "captcha_failed":
                check(r0["excl_captcha"] == "true" and r0["captcha_pass"] == "false", f"{tag}: captcha flags")
                check("primer_1" not in pages, f"{tag}: primer shown after the captcha failed")
            else:
                check(False, f"{tag}: unexpected exit reason {reason}")
            continue
        check(r0["session_complete"] == "true" and len(rows) == 10 and r0["n_trials"] == "10", f"{tag}: {len(rows)} trial rows")
        order = [int(x) for x in r0["trial_order"].split(";")]
        check(sorted(order[:8]) == list(range(8)) and sorted(order[8:]) == [8, 9], f"{tag}: trial order {order} breaks the blocks")
        by_pos = {int(r["list_position"]): r for r in rows}
        check([int(r["list_position"]) for r in rows] == order, f"{tag}: rows not in the order shown")
        dropped_would = "would_block" in r0["dropped_items"].split(";")
        item_order = int(r0["item_order"])
        oo = r0["option_order"].split(";")
        for e in exp:
            j = e["slot"]
            r = by_pos[j]
            for key in ["slot", "block", "story", "amount", "cell", "scene", "scene_place", "source_file", "second_file"]:
                if key == "scene_place":
                    check(r[key] == {"SA-R1": "SA05", "SA-R2": "SA08"}.get(e["scene"], e["scene"]), f"{tag} slot {j}: scene_place")
                else:
                    check(str(r[key]) == str(e[key]), f"{tag} slot {j}: {key} {r[key]!r} != {e[key]!r}")
            for key in ["scene_has_person", "has_addition", "has_follow_up"]:
                check(r[key] == str(e[key]).lower(), f"{tag} slot {j}: {key}")
            check(int(r["scene_position"]) == e["scene_position"], f"{tag} slot {j}: scene_position")
            check(int(r["trial_position"]) == order.index(j) + 1, f"{tag} slot {j}: trial_position")
            items = expected_items(e, item_order)
            check(r["trial_items"] == ";".join(items), f"{tag} slot {j}: trial_items {r['trial_items']}")
            # Answers present exactly where the item was asked, in range
            check(r["creativity_whole"] in list("12345"), f"{tag} slot {j}: creativity_whole")
            check((r["creativity_addition"] in list("12345")) if e["has_addition"] else r["creativity_addition"] == "", f"{tag} slot {j}: creativity_addition")
            if e["has_addition"]:
                check(r["creativity_whole_rt_ms"] != "" and r["creativity_addition_rt_ms"] != "", f"{tag} slot {j}: creativity times")
            check(r["decision"] in ("whole", "part", "refuse"), f"{tag} slot {j}: decision")
            check(int(r["decision_display_pos"]) == oo.index(r["decision"]) + 1, f"{tag} slot {j}: displayed position of decision")
            if r["decision"] == "part" and e["has_addition"]:
                n_followups += 1
                check(r["followup"] in ("first_image", "added", "something_else", "not_sure") and r["followup_rt_ms"] != "", f"{tag} slot {j}: follow-up missing")
            else:
                check(r["followup"] == "", f"{tag} slot {j}: follow-up answered without the divided option, or on a no-change trial")
            for s in ("confidence", "share"):
                check(r[s] != "" and 0 <= int(r[s]) <= 100, f"{tag} slot {j}: {s}")
            check((r["jury"] in ("Yes", "No")) if e["has_addition"] else r["jury"] == "", f"{tag} slot {j}: jury")
            # Follow-up answers on the rows of slots 6 and 7: the "would" item (unless dropped), the written
            # reason below the quoted decision, stop-others items 1 to 3 and, on the AI row (slot 7), item 4
            fu = e["has_follow_up"]
            for s in ("stop1", "stop2", "stop3", "stop4"):
                asked = fu and (s != "stop4" or e["story"] == "ai")
                check((r[s] in list("1234567") and r[s + "_rt_ms"] != "" and r[s + "_n_changes"] != "") if asked
                      else (r[s] == "" and r[s + "_rt_ms"] == ""), f"{tag} slot {j}: {s} {r[s]!r}")
            check((r["follow_up_would_page_ms"] != "") == (fu and not dropped_would) and (r["follow_up_stop_page_ms"] != "") == fu
                  and (r["follow_up_order"] in ("1", "2")) == fu, f"{tag} slot {j}: follow-up page times or order")
            n_stop_rows += fu
            # The written reason on every trial, below the quoted decision (and the follow-up after the divided option)
            check(r["has_reason"] == "true" and r["written_reason"] != "" and r["written_reason_rt_ms"] != "" and r["written_reason_page_ms"] != "",
                  f"{tag} slot {j}: written reason")
            exp_q = expected_quote(R, Q, r["decision"], r["followup"], one_image=not e["has_addition"])
            check(r["written_reason_quote"] == exp_q, f"{tag} slot {j}: quoted answer {r['written_reason_quote']!r} != {exp_q!r}")
            check(r["written_reason_chars"] == str(len(r["written_reason"])) and r["written_reason_paste_attempts"] == "0",
                  f"{tag} slot {j}: written-reason length or paste count")
            n_quotes += 1
            n_quotes_divided += r["decision"] == "part"
            if fu and not dropped_would:
                n_would += 1
                check(r["would_decision"] in ("whole", "part", "refuse") and int(r["would_decision_display_pos"]) == oo.index(r["would_decision"]) + 1,
                      f"{tag} slot {j}: would option or its position")
                check((r["would_followup"] != "") == (r["would_decision"] == "part"), f"{tag} slot {j}: would follow-up")
                check(r["would_confidence"] != "" and 0 <= int(r["would_confidence"]) <= 100, f"{tag} slot {j}: would confidence")
            else:
                check(r["would_decision"] == "" and r["would_followup"] == "" and r["would_confidence"] == "",
                      f"{tag} slot {j}: would answers on a row not asked")
            check((r["is_recall_trial"] == "true") == (j == rp), f"{tag} slot {j}: is_recall_trial")
            # Two pages: the change page (at least 10 s from image load), then the question page (no minimum)
            check(r["view_page_ms"] != "" and r["question_page_ms"] != "" and r["min_view_ms"] == "10000" and r["trial_shown_at_ms"] != "",
                  f"{tag} slot {j}: page times")
            check(r["image_error"] == "false" and r["image_load_ms"] != "", f"{tag} slot {j}: image error or load time")
            check(int(r["view_page_ms"]) >= 10000 or r0["test_mode"] == "true", f"{tag} slot {j}: change page shorter than 10 s")
            # Every trial: the story page, the first image alone, the change page, the question page, the written reason.
            i = order.index(j) + 1
            seq = [f"story_{i}", f"pre_{i}", f"view_{i}", f"trial_{i}", f"reason_{i}"]
            at = pages.index(f"story_{i}")
            check(pages[at:at + len(seq)] == seq, f"{tag} slot {j}: pages of the trial {pages[at:at + 5]} != {seq}")
            check(r["story_page_ms"] != "" and r["pre_page_ms"] != "" and r["pre_min_view_ms"] == str(R["first_image_min"] * 1000)
                  and r["pre_image_error"] == "false" and r["pre_image_load_ms"] != "", f"{tag} slot {j}: story or first-image page fields")
        # Follow-up section: after the last block-1 trial, before the rule; slots 6 and 7 in the order first seen,
        # both pages of one trial before the next trial's
        fu_rows = sorted((int(r["follow_up_order"]), int(r["trial_position"]), int(r["slot"])) for r in rows if r["follow_up_order"])
        check([x[0] for x in fu_rows] == [1, 2] and fu_rows[0][1] < fu_rows[1][1] and sorted(x[2] for x in fu_rows) == R["follow_slots"],
              f"{tag}: follow-up trials not slots 6 and 7 in the order first seen {fu_rows}")
        sec = (["follow_up_intro", "follow_up_stop_1", "follow_up_stop_2"] if dropped_would else
               ["follow_up_intro", "follow_up_would_1", "follow_up_stop_1", "follow_up_would_2", "follow_up_stop_2"]) + ["rule", "rule_recall", "story_9"]
        at = pages.index("follow_up_intro")
        check(pages[at:at + len(sec)] == sec and all(pages.index(f"trial_{n}") < at for n in range(1, 9)),
              f"{tag}: follow-up section {pages[at:at + len(sec)]}")
        check(r0["follow_up_intro_page_ms"] != "", f"{tag}: follow-up introduction page time")
        check(not any(p.startswith(("would", "stop_others", "follow_up_office")) for p in pages), f"{tag}: pages of the removed layout")
        # Page order: instructed after block-1 trial 3; end items in order
        ii = pages.index("instructed")
        check(pages.index("reason_3") < ii < pages.index("story_4"), f"{tag}: instructed item not after the third trial")
        tail = [p for p in pages[pages.index("trial_10"):] if not p.startswith(("trial", "view", "reason"))]
        check(tail == ["recall", "belief", "purpose", "ownership", "experience", "gaais", "creativity_beliefs", "knowledge",
                       "demographics", "final", "debriefing"], f"{tag}: end pages {tail}")
        # Scale scores: Short GAAIS-10 Positive and Negative (reverse-scored) means; beliefs mean
        gp = [int(r0["gaais_" + k]) for k in ("pos7", "pos11", "pos12", "pos17", "pos18")]
        gn = [6 - int(r0["gaais_" + k]) for k in ("neg8", "neg9", "neg10", "neg15", "neg19")]
        ab = [int(r0["acb_" + k]) for k in ("uniquely_human", "differentiate", "essence", "core", "only_humans")]
        check(all(1 <= x <= 5 for x in gp + gn) and all(1 <= x <= 7 for x in ab), f"{tag}: scale answers out of range")
        for col, vals in (("gaais_positive", gp), ("gaais_negative", gn), ("acb_score", ab)):
            check(abs(float(r0[col]) - sum(vals) / len(vals)) < 0.0006, f"{tag}: {col} {r0[col]} != {sum(vals) / len(vals):.3f}")
        check(r0["rule_recall1"] in ("Yes", "No", "Not sure") and r0["rule_recall2"] in ("Yes", "No", "Not sure"), f"{tag}: rule recall")
        check(r0["rule_page_ms"] != "", f"{tag}: rule page time")
        # Recall
        check(r0["recall_correct_answer"] == exp[rp]["story"], f"{tag}: recall key")
        check((r0["recall_correct"] == "true") == (r0["recall"] == exp[rp]["story"]), f"{tag}: recall_correct")
        check((r0["excl_recall"] == "true") == (r0["recall_correct"] == "false"), f"{tag}: excl_recall")
        check((r0["instructed_pass"] == "true") == (r0["instructed"] == "Somewhat disagree"), f"{tag}: instructed_pass")
        check((r0["excl_instructed"] == "true") == (r0["instructed_pass"] == "false") and r0["instructed_after_trial"] == "3", f"{tag}: excl_instructed")
        po = r0["purpose_order"].split(";")
        check(sorted(po) == sorted(["split", "quality_liking", "tell_ai_painting", "description_length", "something_else"]) and po[-1] == "something_else",
              f"{tag}: purpose order {po}")
        check(r0["belief"] in ("Yes", "Partly", "No"), f"{tag}: belief")
        check(r0["ownership"] in ("alex", "company", "artists", "no_one", "not_sure"), f"{tag}: ownership")
        keys = {"know1": "False", "know2": "False", "know3": "False", "know4": "True", "know5": "False"}
        check(int(r0["knowledge_score"]) == sum(r0[q] == v for q, v in keys.items()), f"{tag}: knowledge score")
        check((r0["purpose_chose_true"] == "true") == (r0["purpose"] == "split"), f"{tag}: purpose_chose_true")
        any_in = any(r0[x] == "true" for x in ("excl_comprehension", "excl_captcha", "excl_instructed", "excl_recall"))
        check((r0["excl_any_in_page"] == "true") == any_in, f"{tag}: excl_any_in_page")
        if "fail_instructed" in tag:
            check(r0["excl_instructed"] == "true", f"{tag}: instructed failure not flagged")
        if "fail_recall" in tag:
            check(r0["excl_recall"] == "true" and r0["recall"] == "dont_remember", f"{tag}: recall failure not flagged")
        if "fail_comp1" in tag:
            check(r0["comp_attempt1_pass"] == "false" and r0["comp_attempt2_pass"] == "true" and "primer_2" in pages, f"{tag}: retry")
    print(f"Part 2: {len(files)} saved sessions checked; exit reasons {dict(summary)}; lists hit {sorted(rows_hit)} ({len(rows_hit)} of 10); "
          f"option orders hit {len(opts_hit)} of 3; item orders hit {sorted(items_hit)}; recall slots hit {sorted(recall_hit)}; "
          f"{n_followups} divided answers with their follow-up; {n_stop_rows} follow-up rows, {n_would} with the 'would' item; "
          f"{n_quotes} written reasons below their quoted decisions ({n_quotes_divided} with the part left out).")


def part3(csv_dir):
    text = (HERE / "A1" / "README.md").read_text(encoding="utf-8")
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
    ap.add_argument("--config", help="another copy of A1/config.js to check (default: A1/config.js)")
    a = ap.parse_args()
    global CONFIG
    if a.config:
        CONFIG = Path(a.config)
    R, B = registration(), bank()
    part1(R, B)
    if a.csv_dir:
        part2(R, B, a.csv_dir)
        part3(a.csv_dir)
    if FAILS:
        print(f"\n{len(FAILS)} FAILURES:")
        for m in FAILS[:80]:
            print("  -", m)
        sys.exit(1)
    print("All formula checks passed.")


if __name__ == "__main__":
    main()
