"""Make and accept the 24 participant images of Paper B Study 1 (B1).

For each of the twelve photographic scenes of Set B (SB-P1 to SB-P6 with a
person, SB-N1 to SB-N6 without), this script makes the first composition (V1)
and the second composition (I2) with the Set B model named in the prompt bank
and keeps, for each file, the first candidate that passes the automatic checks.
No person picks an image. Everything follows Docs/Paper Two/Paper_Two_Prompt_Bank.md,
which the script reads directly: the model, the Set B realism line, the closing
sentence, the no-text question and the seed rule ("Generation settings"), and
the plans, feature phrases, placement sentences and reserves ("Set B").

Since 27 October 2026 the Set B model is Nano Banana Pro (gemini-3-pro-image)
with the Set B realism line. An earlier run of this script with GPT Image 2.5
Flare and the line "Color photograph, natural light balance, sharp focus." is
kept in Stimuli/Paper Two/setB_superseded_flare_2026-10-27/.

Prompts (bank, "How each prompt is sent")
- V1: plan version 1, then the Set B realism line, then "No text, watermark,
  or border."
- I2: plan version 1, then the scene's placement sentence, then the same two
  sentences. The placement sentence is built from the accepted V1 by the
  bank's rule (other side of the frame, other scale).
Settings: aspect ratio 3:2 at the model's own output size; candidate n is
requested with seed 1000 + n, and if the model refuses a seed the call is
repeated without one and the record says so.

Checks (auto_checks.py) and acceptance: see ACCEPTANCE_RULE below, which is
also written into every manifest row. Thresholds are set from the first
candidate of V1 of each of the twelve scenes by the rule in thresholds.json,
written before any image is made and frozen before any acceptance decision.

Order of work
1. Write the threshold rule to setB/thresholds.json (only if it is not there).
2. First batch: candidate 1 of V1 for each of the twelve scenes, checked.
3. Freeze the thresholds from the first batch (never changed afterwards).
4. For each scene (three scenes at a time, each scene one request at a time):
   V1 candidates in order until one passes, then I2 candidates in order until
   one passes. Twenty failed candidates for a file give one prompt revision
   (REVISION_RULE); twenty more failures replace the scene by its reserve of
   the same kind (SB-R1 with a person, SB-R2 without).
5. Copy the accepted files to setB/, make web copies, the manifest and the
   contact sheet.

Every paid call goes through the cost ledger (api_ledger.py): it stops before
any call that could take both ledgers together past $100, or this run's own
spending (ledger label SCRIPT) past the soft cap (default $25).

Run from a shell that has loaded ~/.zshrc (GEMINI_API_KEY_AICOPYRIGHT for the
images, OPENAI_API_KEY_AICOPYRIGHT for the description model):
    python3 generate_setB_B1.py              # make, check, accept, write outputs
    python3 generate_setB_B1.py --outputs    # rebuild outputs from saved candidates only (no API calls)
Rerunning is safe: saved candidates and their check results are reused, never
remade, so a rerun continues where the last one stopped.
"""

import argparse
import base64
import csv
import hashlib
import io
import json
import os
import re
import shutil
import statistics
import sys
import textwrap
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from api_ledger import (GEMINI_IMAGE_MAX_USD, GEMINI_RATES, HARD_CAP_USD, BudgetStop, Ledger,  # noqa: E402
                        gemini_image_cost, other_ledger_total)
import auto_checks as ac  # noqa: E402

HERE = Path(__file__).resolve().parent
STIM = HERE.parent
PROJECT = STIM.parent.parent
BANK = PROJECT / "Docs" / "Paper Two" / "Paper_Two_Prompt_Bank.md"
OUT = STIM / "setB"
CAND = OUT / "candidates"
WEB = OUT / "web"
THRESH = OUT / "thresholds.json"
MANIFEST = OUT / "manifest.csv"
SHEET = OUT / "contact_sheet_B1.png"
REPLACED_DIR = OUT / "superseded_SB-N3_replaced_by_SB-R2"

# The bank's Set B generation settings, as clearly named constants. read_generation_settings() reads
# the same values from the bank and stops if any differs, so the bank stays the single source.
BANK_SET_B_MODEL = "gemini-3-pro-image"
BANK_SET_B_REALISM_LINE = (
    "An unretouched documentary photograph taken with an ordinary digital camera in available light: "
    "true-to-life, slightly muted colors, fine sensor noise, natural imperfections and everyday clutter. "
    "Not cinematic, not HDR, no dramatic lighting, no glossy commercial look.")
BANK_SET_B_CLOSING = "No text, watermark, or border."
BANK_NO_TEXT_QUESTION = "Is the image free of any visible text, letters, numbers, signatures or watermarks?"
BANK_SEED_BASE = 1000  # candidate n is requested with seed 1000 + n
BANK_ASPECT = "3:2"  # at the model's own output size

IMAGE_MODEL = BANK_SET_B_MODEL
STYLE_LINE = BANK_SET_B_REALISM_LINE
CLOSING = BANK_SET_B_CLOSING
TEXT_QUESTION = BANK_NO_TEXT_QUESTION
SCRIPT = f"generate_setB_B1.py [{IMAGE_MODEL}]"  # ledger label (the superseded Flare run is 'generate_setB_B1.py')
IMAGE_CONFIG = {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": BANK_ASPECT}}
SETTINGS_TEXT = (f"generationConfig responseModalities IMAGE, imageConfig aspectRatio {BANK_ASPECT} (no size "
                 f"requested: the model's own output size); seed {BANK_SEED_BASE} + candidate number")
WRITTEN_PLACEMENT_TAIL = " on the right side of the frame, small, seen from farther away."

MAIN_SCENES = ["SB-P1", "SB-P2", "SB-P3", "SB-P4", "SB-P5", "SB-P6",
               "SB-N1", "SB-N2", "SB-N3", "SB-N4", "SB-N5", "SB-N6"]
RESERVE_OF_KIND = {True: "SB-R1", False: "SB-R2"}  # with a person -> SB-R1; without -> SB-R2
# Scenes replaced by their reserve under the bank's rescue rule. The reserve takes the replaced scene's
# position in the scene order of every list. SB-N3 was replaced on 27 October 2026, after its I2 failed
# all 40 tries (c23 to c62) under the rescue rule; its files are kept in REPLACED_DIR.
REPLACED_SCENES = {"SB-N3": "SB-R2"}
REPLACEMENT_NOTE = {
    "SB-N3": ("scene replaced by its no-person reserve SB-R2 on 27 October 2026: SB-N3 I2 had no passing candidate "
              "after the bank's rescue rule ran in full (c23 to c62 under the placement sentence of V1 c23, with the "
              "recorded revision; every candidate failed the no-text check, and most also placement and plan sentence 2)"),
    "SB-R2": "reserve scene, in use: replaces SB-N3 (no person) and takes its position in the scene order of every list"}
TRIES_PER_PROMPT = 20
WORKERS = 3
API_ATTEMPTS = 6

# Fixed before any image existed (also written into thresholds.json).
DECOYS = ["a giraffe", "an elephant", "a zebra", "a kangaroo", "a camel"]
SAME_OBJECT_IOU = 0.30
SAME_OBJECT_INSIDE = 0.70
SIDE_BOUNDARY = 0.5
PLAN_FIT_TEMPLATE = 'Does this photograph fit the following description: "{}"?'
PLAN_FIT_SENTENCES = 3  # subject, arrangement, light; the fourth (colors) is a recorded diagnostic only
RULE_VERSION = "2026-10-27 plan-faithfulness amendment"

ACCEPTANCE_RULE = (
    "Every file (V1 and I2) must pass the no-text check: the description model answers yes to 'Is the image free "
    "of any visible text, letters, numbers, signatures or watermarks?'. "
    "Every file must also pass the plan-faithfulness condition (amendment of 27 October 2026, decided before any "
    "participant data): the description model answers yes to 'Does this photograph fit the following description: "
    "\"<sentence>\"?' for each of plan version 1's first three sentences (subject, arrangement, light); the fourth "
    "(colors) is excluded as too vague to judge and is recorded only by the plan-sentence diagnostic. "
    "V1 is accepted when it passes the no-text check and (1) the detector finds every main element (the elements "
    "the scene's placement sentence names) with a box scoring at or above the score cut, and (2) the description "
    "model answers yes to 'Does the "
    "image show ' + the feature phrase of plan version 1 + '?', and (3) for animal and passer-by scenes the detector "
    "also confirms the feature: the animal's best box scores at or above the cut (SB-P2 a dog, SB-N2 a cat, SB-N4 a "
    "sparrow, SB-R1 a hen); SB-P6, a box for 'a jogger' at or above the cut that is not the same object as the "
    "girl's box; SB-P4 (the chef alone), no box for 'a person' at or above the cut that is not the same object as the "
    "chef's box. For weather and light scenes (SB-P1, SB-P3, SB-N1, SB-N5, SB-R2; SB-P5, SB-N3, SB-N6) the feature "
    "(rain on glass, the sky, fog, sun, a light on) is not an object a detector can find, so the detector confirms "
    "the main elements and the description model confirms the feature. I2 is accepted when it passes the same checks "
    "and the main-element box lies on the side the placement sentence names (centre left of half the width for "
    "'left', right of it for 'right') and at the scale it names (box area below the scale cut for 'small', at or "
    "above it for 'large'). The main-element box is the smallest box enclosing the best box of each main element "
    "(for SB-N6, the two best distinct 'a table' boxes, or the one if only one is found). Two boxes are the same "
    "object when their intersection over union is at least 0.30 or at least 70 percent of the smaller box lies "
    "inside the larger.")
REVISION_RULE = (
    "After 20 failed candidates for a file, the prompt gets one added sentence, placed just before the realism line: "
    "for the check that failed most often among those 20 (ties broken in the order feature, main elements, "
    "placement, text, plan fit), 'The photograph clearly shows ' + X + '.', where X is the feature phrase of plan version 1; "
    "the subject of the placement sentence in lower case; or, for I2 placement, that subject followed by 'on the "
    "<side> side of the frame, <scale phrase>' as in the placement sentence; or, for the no-text check, the sentence "
    "'The photograph shows no visible text, letters, numbers, signatures or watermarks.'; or, for the plan-fit "
    "check (amendment of 27 October 2026), the plan sentence among the first three that failed most often among "
    "those 20, repeated unchanged (ties: the earlier sentence). Candidate numbers continue "
    "(and so do their seeds), and 20 more tries follow. A file that still fails replaces its scene with the reserve "
    "of the same kind.")
PLACEMENT_RULE = (
    "The placement sentence is the bank's written form ('... on the right side of the frame, small, seen from "
    "farther away.'). If the centre of V1's main-element box lies right of half the width, 'right' becomes 'left'. "
    "If that box covers less of the frame than the scale cut, 'small, seen from farther away' becomes 'large, seen "
    "from close by'.")

QUERY_CORRECTION = (
    "Head-noun query rule: the main-element query drops an 'of ...' complement, so SB-N4's query is 'a bowl', not "
    "'a bowl of lemons'. Adopted on 27 October 2026 after the superseded GPT Image 2.5 Flare run, where the longer "
    "query put the detector's best box on a single lemon; in place from the start of this run.")

THRESHOLD_RULE = {
    "written_before": "any image of this run was generated; values are filled from the first batch and frozen before any acceptance decision",
    "first_batch": "Candidate 1 of V1 for each of the twelve main scenes SB-P1 to SB-P6 and SB-N1 to SB-N6, generated from plan version 1 with no revision. Reserve scenes use the same frozen values.",
    "detector_score_cut": "The midpoint, rounded to two decimals, between (a) the median, over the twelve first-batch images, of the best detector score for each main-element query of the image's scene (one value per query and image; the main elements are those its placement sentence names), and (b) the highest best score that any first-batch image gives to any of five decoy queries naming animals absent from every plan: a giraffe, an elephant, a zebra, a kangaroo, a camel. A query counts as found when a box scores at or above the cut.",
    "scale_cut": "The median, rounded to two decimals, of the share of the frame covered by the main-element box (the smallest box enclosing the best box of each main element; for SB-N6 the two best distinct table boxes), over the first-batch images whose main elements are all found at the score cut.",
    "fixed_constants_set_before_any_image": {
        "same_object": "two boxes are the same object when intersection over union >= 0.30 or >= 70 percent of the smaller box lies inside the larger",
        "side_boundary": "half the image width (centre x share 0.5): left means < 0.5, right means > 0.5",
        "record_floor": "boxes scoring >= 0.05 are recorded (the best box of each query is always recorded); recording only",
        "decoys": DECOYS,
        "main_element_queries": "the placement sentence's subject, 'The/her' replaced by 'a/an', one query per noun joined by 'and', head noun only (an 'of ...' complement dropped: SB-N4 'a bowl'); 'The two tables': 'a table', two best distinct boxes",
    },
}

PRINT_LOCK = threading.Lock()
DETECT_LOCK = threading.Lock()
STOP = threading.Event()
STOP_REASON = []


def log(*a):
    with PRINT_LOCK:
        print(datetime.now().strftime("%H:%M:%S"), *a, flush=True)


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ------------------------------------------------------------------ the bank

def read_bank():
    text = BANK.read_text(encoding="utf-8")
    scenes = {}
    pattern = r"^### (SB-[PNR]\d)\. (.+?) \((person|no person)(, reserve)?\)\n(.*?)(?=^### |^---|\Z)"
    for m in re.finditer(pattern, text, flags=re.M | re.S):
        code, title, who, reserve, body = m.groups()
        rows = dict(re.findall(r"^\| ([^|]+?) \| (.+?) \|$", body, flags=re.M))
        placement = rows["Placement sentence (I2)"]
        assert placement.endswith(WRITTEN_PLACEMENT_TAIL), placement
        subject = re.sub(r" (is|are)$", "", placement[: -len(WRITTEN_PLACEMENT_TAIL)])
        if subject == "The two tables":
            main, main_count = ["a table"], 2
        else:
            main, main_count = [], 1
            for part in subject.split(" and "):
                noun = re.sub(r"^(The|the|her) ", "", part)
                noun = re.sub(r" of .+$", "", noun)  # head noun only: "bowl of lemons" -> "bowl" (QUERY_CORRECTION)
                main.append(("an " if noun[0] in "aeiou" else "a ") + noun)
        kind = rows["Kind of feature"]
        phrase = rows["Feature phrase, version 1"]
        feature_det = None
        if kind in ("Animal", "Passer-by"):
            if phrase.startswith("a "):
                q = " ".join(phrase.split()[:2])
                feature_det = ("present", q) if kind == "Animal" else ("present_apart", q)
            else:  # "the chef alone in the room": nobody else may be found
                feature_det = ("none_apart", "a person")
        scenes[code] = {
            "scene": code, "title": title, "person": who == "person", "reserve": bool(reserve), "kind": kind,
            "plan_v1": rows["Plan, version 1"], "plan_v2": rows["Plan, version 2"],
            "plan_v1_words": len(rows["Plan, version 1"].split()), "plan_v2_words": len(rows["Plan, version 2"].split()),
            "feature_phrase_v1": phrase, "feature_question": f"Does the image show {phrase}?",
            "placement_written": placement, "subject": subject, "main": main, "main_count": main_count,
            "feature_det": feature_det,
            "plan_sentences": [x.strip() for x in re.split(r"(?<=\.)\s+", rows["Plan, version 1"]) if x.strip()]}
        assert len(scenes[code]["plan_sentences"]) == 4, (code, scenes[code]["plan_sentences"])
    expected = MAIN_SCENES + ["SB-R1", "SB-R2"]
    assert sorted(scenes) == sorted(expected), sorted(scenes)
    return scenes, hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_generation_settings():
    """Read the Set B model, realism line, closing sentence, no-text question, seed rule and aspect ratio
    from the bank's "Generation settings" and check them against the named constants."""
    text = BANK.read_text(encoding="utf-8")
    sec = text.split("## Generation settings", 1)[1].split("## Edit instructions", 1)[0]
    found = {
        "model": re.search(r"\*\*Set B \(photographs, Paper B\):\*\* [^(]*\(`([^`]+)`\)", sec).group(1),
        "realism": re.search(r'\*\*Set B, first composition \(V1\):\*\* plan version 1, then the Set B realism '
                             r'line, "(.+?)", then "(.+?)"', sec).group(1),
        "closing": re.search(r'\*\*Set B, first composition \(V1\):\*\* plan version 1, then the Set B realism '
                             r'line, "(.+?)", then "(.+?)"', sec).group(2),
        "i2": bool(re.search(r"\*\*Set B, second composition \(I2\):\*\* plan version 1, then the scene's "
                             r"placement sentence, then the same realism line and closing sentence\.", sec)),
        "no_text": re.search(r'answers yes to "(Is the image free of any visible text[^"]*)"', sec).group(1),
        "seed_base": int(re.search(r"Candidate n is requested with seed (\d+) \+ n", sec).group(1)),
        "aspect": re.search(r"Set B \(Nano Banana Pro\): (\d+:\d+) landscape at the model's own output size", sec).group(1),
    }
    expected = {"model": BANK_SET_B_MODEL, "realism": BANK_SET_B_REALISM_LINE, "closing": BANK_SET_B_CLOSING,
                "i2": True, "no_text": BANK_NO_TEXT_QUESTION, "seed_base": BANK_SEED_BASE, "aspect": BANK_ASPECT}
    for k, v in expected.items():
        if found[k] != v:
            raise SystemExit(f"Prompt bank and script disagree on '{k}': bank {found[k]!r}, script {v!r}")
    return found


# --------------------------------------------------------------- thresholds

def load_thresholds():
    return json.loads(THRESH.read_text(encoding="utf-8"))


def write_rule(bank_sha):
    if THRESH.exists():
        return
    THRESH.write_text(json.dumps({"rule": THRESHOLD_RULE, "rule_written_utc": now(), "bank_sha256": bank_sha,
                                  "image_model": IMAGE_MODEL, "values": None}, indent=2), encoding="utf-8")
    log("threshold rule written to", THRESH.name)


def main_box(scene, det, score_cut):
    """(box or None, list of per-element records) for the scene's main elements."""
    parts, boxes, found = [], [], True
    if scene["main_count"] == 2:
        q = scene["main"][0]
        d = ac.distinct_boxes(det[q], score_cut, SAME_OBJECT_IOU, SAME_OBJECT_INSIDE)[:2]
        parts.append({"query": q, "boxes_used": d, "found": bool(d)})
        boxes = [b["box"] for b in d]
        found = bool(d)
    else:
        for q in scene["main"]:
            top = det[q][0]
            ok = top["score"] >= score_cut
            parts.append({"query": q, "best": top, "found": ok})
            boxes.append(top["box"])
            found = found and ok
    return (ac.union_box(boxes) if found else None), parts


def round2_half_up(x):
    """Round once, half-up, to two decimals (the threshold rule's 'rounded to two decimals')."""
    from decimal import ROUND_HALF_UP, Decimal
    return float(Decimal(repr(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def freeze_thresholds(scenes, first):
    th = load_thresholds()
    if th.get("values"):
        return th
    named, decoy = [], []
    for code in MAIN_SCENES:
        det = first[code]["detector"]["boxes"]
        for q in dict.fromkeys(scenes[code]["main"]):
            named.append(det[q][0]["score"])
        for q in DECOYS:
            decoy.append(det[q][0]["score"])
    t_med, d_max = statistics.median(named), max(decoy)
    score_cut = round2_half_up((t_med + d_max) / 2)
    areas = {}
    for code in MAIN_SCENES:
        box, _ = main_box(scenes[code], first[code]["detector"]["boxes"], score_cut)
        if box:
            areas[code] = ac.area(box)  # unrounded: the median is rounded once, below
    scale_cut = round2_half_up(statistics.median(areas.values()))
    th["values"] = {"detector_score_cut": score_cut, "scale_cut": scale_cut}
    th["inputs"] = {"median_main_element_best_score": round(t_med, 4), "max_decoy_best_score": round(d_max, 4),
                    "n_main_element_scores": len(named), "n_decoy_scores": len(decoy),
                    "first_batch_main_box_areas": {k: round(v, 8) for k, v in areas.items()},
                    "first_batch_files": {c: first[c]["file"] for c in MAIN_SCENES}}
    th["frozen_utc"] = now()
    THRESH.write_text(json.dumps(th, indent=2), encoding="utf-8")
    log(f"thresholds frozen: score cut {score_cut}, scale cut {scale_cut}")
    return th


# ------------------------------------------------------------- generation

class ApiFailure(Exception):
    pass


def generate_image(ledger, prompt, scene, label, seed):
    """One Nano Banana Pro call. Returns (PNG bytes, record). A refused seed is dropped and the call repeated
    without one; a reply without an image is not a candidate and is retried. Any other repeated failure stops."""
    key = os.environ["GEMINI_API_KEY_AICOPYRIGHT"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{IMAGE_MODEL}:generateContent"
    use_seed, seed_note, last = seed, f"seed {seed}", ""
    for attempt in range(API_ATTEMPTS):
        if STOP.is_set():
            raise BudgetStop("stop already requested")
        cfg = dict(IMAGE_CONFIG)
        if use_seed is not None:
            cfg["seed"] = use_seed
        body = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": cfg}
        res = ledger.authorize(GEMINI_IMAGE_MAX_USD)
        t = time.time()
        try:
            r = requests.post(url, json=body, headers={"x-goog-api-key": key}, timeout=300)
            d = r.json()
        except Exception as e:
            ledger.record(res, IMAGE_MODEL, "Set B image", scene, label, GEMINI_IMAGE_MAX_USD,
                          "no reply; charged the assumed maximum", f"no reply: {type(e).__name__}", image_count=1)
            last = f"no reply: {type(e).__name__}"
            log(f"{label}: {last}; retrying")
            time.sleep(20 * (attempt + 1))
            continue
        if "error" in d:
            msg = str(d["error"].get("message", d["error"]))[:300]
            ledger.record(res, IMAGE_MODEL, "Set B image", scene, label, 0.0, "API error; not billed",
                          f"error {r.status_code}: {msg[:120]}")
            last = f"API error {r.status_code}: {msg}"
            log(f"{label}: {last}")
            if use_seed is not None and "seed" in msg.lower():
                use_seed, seed_note = None, f"seed {seed} refused by the model; repeated without a seed"
                continue
            if r.status_code in (400, 401, 403, 404):
                raise ApiFailure(last)  # model name, key or request rejected: stop, do not switch models
            time.sleep(30 * (attempt + 1))
            continue
        usage = d.get("usageMetadata") or {}
        cands = d.get("candidates") or []
        parts = ((cands[0].get("content") or {}).get("parts") or []) if cands else []
        images = [p for p in parts if "inlineData" in p and not p.get("thought")]
        finish = cands[0].get("finishReason", "") if cands else str(d.get("promptFeedback", ""))[:120]
        if not images:
            by_tokens = ((usage.get("promptTokenCount", 0) or 0) * GEMINI_RATES["in"]
                         + ((usage.get("candidatesTokenCount", 0) or 0) + (usage.get("thoughtsTokenCount", 0) or 0))
                         * GEMINI_RATES["text_out"]) / 1e6
            ledger.record(res, IMAGE_MODEL, "Set B image (no image returned)", scene, label, by_tokens,
                          "no image returned; returned usage at published text rates", f"no image: {finish}",
                          usage.get("promptTokenCount", ""), usage.get("candidatesTokenCount", ""), 0)
            last = f"no image returned (finishReason {finish})"
            log(f"{label}: {last}; retrying")
            time.sleep(10 * (attempt + 1))
            continue
        usd, basis = gemini_image_cost(usage)
        ledger.record(res, d.get("modelVersion", IMAGE_MODEL), "Set B image", scene, label, usd, basis, "ok",
                      usage.get("promptTokenCount", ""), usage.get("candidatesTokenCount", ""), 1)
        inline = images[-1]["inlineData"]
        raw = base64.b64decode(inline["data"])
        mime = inline.get("mimeType", "")
        if mime == "image/png":
            data, stored = raw, "PNG exactly as returned"
        else:  # store a lossless PNG of the decoded pixels
            buf = io.BytesIO()
            Image.open(io.BytesIO(raw)).save(buf, "PNG")
            data, stored = buf.getvalue(), f"returned as {mime}; stored as a lossless PNG of the decoded pixels"
        meta = {"model_requested": IMAGE_MODEL, "model_reported": d.get("modelVersion", ""), "usage": usage,
                "usd_estimate": round(usd, 5), "price_basis": basis, "seconds": round(time.time() - t, 1),
                "seed_requested": seed, "seed_used": use_seed, "seed_note": seed_note, "finish_reason": finish,
                "mime_returned": mime, "stored_as": stored, "returned_sha256": hashlib.sha256(raw).hexdigest(),
                "text_parts": " ".join(p.get("text", "") for p in parts if "text" in p and not p.get("thought"))[:500]}
        return data, meta
    raise ApiFailure(f"{label}: {API_ATTEMPTS} attempts failed; last: {last}")


def cand_stem(code, kind, n):
    return f"{code}_{kind}_c{n:02d}"


def save_json(path, obj):
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    tmp.replace(path)


def run_checks(ctx, scene, rec, png):
    queries = list(dict.fromkeys(scene["main"] + ([scene["feature_det"][1]] if scene["feature_det"] else [])
                                 + DECOYS))
    if "detector" in rec and rec["detector"]["queries"] != queries:
        # The query rule changed after this record was made (QUERY_CORRECTION): keep the old result, detect again.
        rec.setdefault("detector_superseded", []).append({**rec.pop("detector"), "note": QUERY_CORRECTION})
        if "evaluation" in rec:
            rec.setdefault("evaluation_superseded", []).append(rec.pop("evaluation"))
    if "detector" not in rec:
        with DETECT_LOCK:
            boxes = ctx["detector"].detect(Image.open(png), queries)
        rec["detector"] = {"model": ctx["detector"].name, "queries": queries, "boxes": boxes}
        save_json(png.with_suffix(".json"), rec)
    if "description" not in rec:
        b64 = ac.image_b64_jpeg(png)
        feat = ac.ask_yes_no(ctx["ledger"], png, scene["feature_question"], scene["scene"], png.name,
                             "Set B feature check", b64=b64)
        text = ac.ask_yes_no(ctx["ledger"], png, TEXT_QUESTION, scene["scene"], png.name,
                             "Set B no-text check", b64=b64)
        rec["description"] = {"model": ac.DESCRIBER_MODEL, "settings": ac.DESCRIBER_SETTINGS,
                              "instruction": ac.DESCRIBER_INSTRUCTION, "feature": feat, "text_free": text}
        save_json(png.with_suffix(".json"), rec)
    return rec


def ensure_plan_fit(ctx, scene, rec, png):
    """Ask the plan-fit question for each of plan version 1's first three sentences that has no answer yet."""
    desc = rec["description"]
    have = {a["sentence_no"] for a in desc.get("plan_fit", [])}
    b64 = None
    for i, sent in enumerate(scene["plan_sentences"][:PLAN_FIT_SENTENCES], start=1):
        if i in have:
            continue
        b64 = b64 or ac.image_b64_jpeg(png)
        r = ac.ask_yes_no(ctx["ledger"], png, PLAN_FIT_TEMPLATE.format(sent), scene["scene"], png.name,
                          "Set B plan-fit check", b64=b64)
        desc.setdefault("plan_fit", []).append({"sentence_no": i, "sentence": sent, "question": r["question"],
                                                "answer": r["answer"], "raw": r["raw"], "source": "asked for this candidate"})
    desc["plan_fit"].sort(key=lambda a: a["sentence_no"])
    save_json(png.with_suffix(".json"), rec)
    return rec


def make_candidate(ctx, scene, kind, n, prompt, revision, placement, revision_sentence):
    """Load candidate n if it exists (it must have the same prompt), else make it; then check it."""
    stem = cand_stem(scene["scene"], kind, n)
    png, js = CAND / f"{stem}.png", CAND / f"{stem}.json"
    if js.exists() and png.exists():
        rec = json.loads(js.read_text(encoding="utf-8"))
        if rec["prompt"] != prompt:
            raise RuntimeError(f"{stem}: saved prompt differs from the prompt the rules give now")
    else:
        data, meta = generate_image(ctx["ledger"], prompt, scene["scene"], stem, BANK_SEED_BASE + n)
        png.write_bytes(data)
        img = Image.open(io.BytesIO(data))
        rec = {"scene": scene["scene"], "file_kind": kind, "candidate": n, "prompt_revision": revision,
               "file": f"candidates/{png.name}", "prompt": prompt, "placement_sentence": placement or "",
               "revision_sentence": revision_sentence or "", "settings": SETTINGS_TEXT, "created_utc": now(),
               "sha256": hashlib.sha256(data).hexdigest(), "width": img.width, "height": img.height, **meta}
        save_json(js, rec)
        log(f"{stem}: made ({meta['seconds']} s, ${meta['usd_estimate']:.2f})")
        rec = run_checks(ctx, scene, rec, png)
        return ensure_plan_fit(ctx, scene, rec, png)  # every new candidate gets the three plan-fit questions
    return run_checks(ctx, scene, rec, png)


def evaluate(scene, rec, th, placement=None):
    """Apply ACCEPTANCE_RULE with the frozen thresholds. Returns the evaluation dict."""
    cut, scale_cut = th["values"]["detector_score_cut"], th["values"]["scale_cut"]
    det = rec["detector"]["boxes"]
    mbox, parts = main_box(scene, det, cut)
    ev = {"score_cut": cut, "scale_cut": scale_cut, "main_elements": parts, "main_found": mbox is not None,
          "main_box": [round(v, 4) for v in mbox] if mbox else None,
          "main_center_x": round(ac.center_x(mbox), 4) if mbox else None,
          "main_area": round(ac.area(mbox), 4) if mbox else None,
          "main_area_exact": ac.area(mbox) if mbox else None}
    fd = scene["feature_det"]
    if fd is None:
        ev["feature_detector"] = "not applicable (weather or light: description model only)"
        ev["feature_detector_ok"] = None
    else:
        mode, q = fd
        if mode == "present":
            top = det[q][0]
            ev["feature_detector"] = f"best '{q}' box {top['score']} vs cut {cut}"
            ev["feature_detector_ok"] = top["score"] >= cut
        else:
            ref = det[scene["main"][0]][0]["box"]
            others = [b for b in det[q] if b["score"] >= cut
                      and not ac.same_object(b["box"], ref, SAME_OBJECT_IOU, SAME_OBJECT_INSIDE)]
            if mode == "present_apart":
                ev["feature_detector"] = f"'{q}' boxes at or above cut, apart from '{scene['main'][0]}': {len(others)}"
                ev["feature_detector_ok"] = len(others) >= 1
            else:
                ev["feature_detector"] = f"'{q}' boxes at or above cut, apart from '{scene['main'][0]}': {len(others)} (must be 0)"
                ev["feature_detector_ok"] = len(others) == 0
            ev["feature_detector_boxes_apart"] = others
    ev["feature_description"] = rec["description"]["feature"]["answer"]
    ev["feature_description_ok"] = ev["feature_description"] == "yes"
    feature_ok = ev["feature_description_ok"] and ev["feature_detector_ok"] is not False
    ev["text_free"] = rec["description"]["text_free"]["answer"]
    ev["text_free_ok"] = ev["text_free"] == "yes"
    ok = ev["main_found"] and feature_ok and ev["text_free_ok"]
    reasons = []
    if not ev["main_found"]:
        reasons.append("main elements")
    if not feature_ok:
        reasons.append("feature")
    if not ev["text_free_ok"]:
        reasons.append("text")
    pf = rec["description"].get("plan_fit")
    ev["rule_version"] = RULE_VERSION
    if pf is None:
        ev["plan_fit"], ev["plan_fit_ok"], ev["plan_fit_failed"] = "not asked", None, []
    else:
        ev["plan_fit"] = {a["sentence_no"]: a["answer"] for a in pf}
        ev["plan_fit_failed"] = [a["sentence_no"] for a in pf if a["answer"] != "yes"]
        ev["plan_fit_ok"] = len(pf) >= PLAN_FIT_SENTENCES and not ev["plan_fit_failed"]
        if not ev["plan_fit_ok"]:
            reasons.append("plan fit")
    if placement is not None:
        side = "left" if " on the left side " in placement else "right"
        scale = "large" if "large, seen from close by" in placement else "small"
        ev["required_side"], ev["required_scale"] = side, scale
        if mbox:
            cx, a = ac.center_x(mbox), ac.area(mbox)
            ev["side_ok"] = cx < SIDE_BOUNDARY if side == "left" else cx > SIDE_BOUNDARY
            ev["scale_ok"] = a < scale_cut if scale == "small" else a >= scale_cut
        else:
            ev["side_ok"] = ev["scale_ok"] = False
        if not (ev["side_ok"] and ev["scale_ok"]):
            reasons.append("placement")
        ok = ok and ev["side_ok"] and ev["scale_ok"]
    if ev["plan_fit_ok"] is None and ok:
        reasons.append("plan fit not asked")  # the search asks, then judges again
    ok = ok and ev["plan_fit_ok"] is True
    ev["accepted"] = bool(ok)
    ev["failed_checks"] = reasons
    return ev


def placement_sentence(scene, v1_ev):
    s = scene["placement_written"]
    if v1_ev["main_center_x"] > SIDE_BOUNDARY:
        s = s.replace(" on the right side ", " on the left side ")
    if v1_ev.get("main_area_exact", v1_ev["main_area"]) < v1_ev["scale_cut"]:
        s = s.replace("small, seen from farther away", "large, seen from close by")
    return s


def revision_sentence(scene, failures, placement, evs=()):
    order = ("feature", "main elements", "placement", "text", "plan fit")
    counts = {k: sum(k in f for f in failures) for k in order}
    top = max(counts.values())
    which = next(k for k in order if counts[k] == top)
    subject = scene["subject"][0].lower() + scene["subject"][1:]
    if which == "text":
        return "The photograph shows no visible text, letters, numbers, signatures or watermarks.", which
    if which == "plan fit":
        per = {i: sum(i in e.get("plan_fit_failed", []) for e in evs) for i in range(1, PLAN_FIT_SENTENCES + 1)}
        worst = max(per, key=lambda i: (per[i], -i))
        return scene["plan_sentences"][worst - 1], which
    if which == "feature":
        x = scene["feature_phrase_v1"]
    elif which == "main elements":
        x = subject
    else:  # "<subject> is/are on the <side> side of the frame, <scale phrase>." -> "<subject> on the ..."
        x = subject + re.sub(r"^ (is|are) ", " ", placement[len(scene["subject"]):]).rstrip(".")
    return f"The photograph clearly shows {x}.", which


def build_prompt(scene, placement=None, rev=None):
    parts = [scene["plan_v1"]] + ([placement] if placement else []) + ([rev] if rev else []) + [STYLE_LINE, CLOSING]
    return " ".join(parts)


def superseded_note(rec, placement):
    return (f"superseded: made under the placement sentence '{rec.get('placement_sentence', '')}', which was "
            f"replaced by '{placement}' on 27 October 2026 (scale-cut correction, or a V1 replaced under the "
            f"plan-faithfulness amendment); not a candidate for it")


def search(ctx, scene, kind, placement=None):
    """Candidates in order until one passes. Returns (accepted record or None, status).
    An existing candidate made under a different placement sentence (before the scale-cut correction) is
    marked superseded and skipped; numbering and seeds continue after it."""
    th = ctx["th"]
    n, failures, evs = 0, [], []
    for revision in (0, 1):
        rev = None
        if revision == 1:
            rev, which = revision_sentence(scene, failures[:TRIES_PER_PROMPT], placement, evs[:TRIES_PER_PROMPT])
            log(f"{scene['scene']} {kind}: 20 failures; prompt revision ({which}): {rev}")
        prompt = build_prompt(scene, placement, rev)
        for _ in range(TRIES_PER_PROMPT):
            if STOP.is_set():
                return None, "stopped"
            n += 1
            js = CAND / f"{cand_stem(scene['scene'], kind, n)}.json"
            while kind == "I2" and js.exists() and \
                    json.loads(js.read_text(encoding="utf-8")).get("placement_sentence") != placement:
                old = json.loads(js.read_text(encoding="utf-8"))
                if not old.get("superseded"):
                    old["superseded"] = superseded_note(old, placement)
                    save_json(js, old)
                    log(f"{scene['scene']} {kind} c{n:02d}: superseded (made under the old placement sentence)")
                n += 1
                js = CAND / f"{cand_stem(scene['scene'], kind, n)}.json"
            if ctx.get("max_candidate") and n > ctx["max_candidate"]:
                log(f"{scene['scene']} {kind}: reached the candidate cap ({ctx['max_candidate']}); stopping this file")
                return None, "capped"
            try:
                rec = make_candidate(ctx, scene, kind, n, prompt, revision, placement, rev)
            except BudgetStop as e:
                STOP.set()
                STOP_REASON.append(str(e))
                log(f"STOP: {e}")
                return None, "stopped"
            ev = evaluate(scene, rec, th, placement if kind == "I2" else None)
            if "plan fit not asked" in ev["failed_checks"]:
                rec = ensure_plan_fit(ctx, scene, rec, CAND / f"{cand_stem(scene['scene'], kind, n)}.png")
                ev = evaluate(scene, rec, th, placement if kind == "I2" else None)
            keep_superseded_evaluation(rec, ev)
            rec["evaluation"] = ev
            rec["acceptance_rule"] = ACCEPTANCE_RULE
            save_json(CAND / f"{cand_stem(scene['scene'], kind, n)}.json", rec)
            log(f"{scene['scene']} {kind} c{n:02d}: {'ACCEPTED' if ev['accepted'] else 'rejected'} "
                f"{ev['failed_checks'] or ''} main_area={ev['main_area']} cx={ev['main_center_x']} "
                f"desc={ev['feature_description']} det={ev['feature_detector_ok']}")
            if ev["accepted"]:
                return rec, "accepted"
            failures.append(ev["failed_checks"])
            evs.append(ev)
    return None, "failed"


def keep_superseded_evaluation(rec, ev):
    """Before a decision is replaced under a corrected threshold, keep the old one in the record."""
    old = rec.get("evaluation")
    if old and old.get("scale_cut") != ev.get("scale_cut"):
        old = dict(old, note=f"decision at scale cut {old.get('scale_cut')}, superseded by the 27 October 2026 correction")
        rec.setdefault("evaluation_superseded", []).append(old)
    elif old and old.get("accepted") and not ev.get("accepted") and old.get("rule_version") != ev.get("rule_version"):
        old = dict(old, note="accepted before the plan-faithfulness amendment of 27 October 2026; fails it")
        rec.setdefault("evaluation_superseded", []).append(old)


def run_scene(ctx, code):
    scene = ctx["scenes"][code]
    try:
        v1, status = search(ctx, scene, "V1")
        if not v1:
            return code, status, None, None
        place = placement_sentence(scene, v1["evaluation"])
        log(f"{code}: V1 accepted (c{v1['candidate']:02d}); placement sentence: {place}")
        i2, status = search(ctx, scene, "I2", place)
        return code, status, v1, i2
    except ApiFailure as e:
        STOP.set()
        STOP_REASON.append(f"API failure: {e}")
        log(f"STOP (API failure): {e}")
        return code, "api_failure", None, None
    except Exception as e:
        STOP.set()
        STOP_REASON.append(f"error in {code}: {e}")
        log(f"STOP (error in {code}): {traceback.format_exc()}")
        return code, "error", None, None


def complete_records(ctx):
    """Check and evaluate any saved candidate the search did not reach (made before a correction, or made
    but not checked when a run was stopped), so every candidate in the manifest carries a decision under the
    current rules. Candidates numbered after their file's accepted candidate are marked as not used."""
    recs = all_candidates()
    first_ok = {}
    for r in recs:
        if (r.get("evaluation") or {}).get("accepted") and not r.get("superseded"):
            k = (r["scene"], r["file_kind"])
            first_ok[k] = min(first_ok.get(k, 10 ** 6), r["candidate"])
    for r in recs:
        if r["scene"] in REPLACED_SCENES:
            continue  # the scene was replaced by its reserve; its records are kept as they were judged
        scene = ctx["scenes"][r["scene"]]
        png = CAND / Path(r["file"]).name
        r = run_checks(ctx, scene, r, png)
        ev = evaluate(scene, r, ctx["th"], r["placement_sentence"] if r["file_kind"] == "I2" else None)
        if "plan fit not asked" in ev["failed_checks"] and not r.get("superseded"):
            r = ensure_plan_fit(ctx, scene, r, png)
            ev = evaluate(scene, r, ctx["th"], r["placement_sentence"] if r["file_kind"] == "I2" else None)
        keep_superseded_evaluation(r, ev)
        r["evaluation"] = ev
        r["acceptance_rule"] = ACCEPTANCE_RULE
        k = (r["scene"], r["file_kind"])
        if k in first_ok and r["candidate"] > first_ok[k] and not r.get("superseded"):
            r["record_note"] = (f"numbered after candidate {first_ok[k]}, the first of its file to pass; not used")
        save_json(png.with_suffix(".json"), r)


# --------------------------------------------------------------- outputs

def b1_scenes():
    """The twelve scenes B1 uses, in the bank's order, with any replaced scene's reserve in its place."""
    return [REPLACED_SCENES.get(c, c) for c in MAIN_SCENES]


def all_candidates():
    recs = []
    for js in sorted(CAND.glob("*.json")) + sorted((REPLACED_DIR / "candidates").glob("*.json")):
        recs.append(json.loads(js.read_text(encoding="utf-8")))
    return recs


def web_copy(src, dst):
    """JPEG at the model's own size (never resized), quality 85, or the highest quality below 85 that keeps the
    file at or under 400,000 bytes."""
    img = Image.open(src).convert("RGB")
    for q in range(85, 69, -1):
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=q, optimize=True, progressive=True)
        if buf.tell() <= 400_000:
            break
    dst.write_bytes(buf.getvalue())
    return q, buf.tell()


def font(size):
    for name in ("/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def contact_sheet(rows, scenes):
    tw, th_, label_w, pad = 540, 360, 380, 10
    order = [r for r in rows]
    sheet = Image.new("RGB", (label_w + 2 * (tw + pad) + pad, 60 + len(order) * (th_ + pad) + pad), "white")
    draw = ImageDraw.Draw(sheet)
    big, small = font(24), font(16)
    draw.text((label_w + pad, 18), "V1 (first composition)", fill="black", font=big)
    draw.text((label_w + 2 * pad + tw, 18), "I2 (second composition)", fill="black", font=big)
    for i, r in enumerate(order):
        y = 60 + i * (th_ + pad)
        sc = scenes[r["scene"]]
        draw.text((pad, y + 6), f"{r['scene']}  {sc['title']}", fill="black", font=big)
        lines = [f"{sc['kind']}; V1 c{r['V1']['candidate']:02d}, I2 c{r['I2']['candidate']:02d}" if r.get("I2")
                 else f"{sc['kind']}; V1 c{r['V1']['candidate']:02d}; I2 missing"]
        if r.get("I2"):
            lines += textwrap.wrap("I2: " + r["I2"]["placement_sentence"], 44)
        for j, line in enumerate(lines):
            draw.text((pad, y + 42 + j * 22), line, fill="black", font=small)
        for k, kind in enumerate(("V1", "I2")):
            x = label_w + pad + k * (tw + pad)
            if not r.get(kind):
                draw.rectangle([x, y, x + tw, y + th_], outline="gray")
                continue
            img = Image.open(OUT / f"{r['scene']}_{kind}.png").convert("RGB")
            img.thumbnail((tw, th_))
            sheet.paste(img, (x, y))
            ev = r[kind]["evaluation"]
            if ev.get("main_box"):
                b = ev["main_box"]
                draw.rectangle([x + b[0] * img.width, y + b[1] * img.height, x + b[2] * img.width,
                                y + b[3] * img.height], outline=(255, 60, 60), width=2)
    sheet.save(SHEET, optimize=True)


MANIFEST_FIELDS = [
    "row_type", "scene", "scene_title", "with_person", "kind_of_feature", "reserve_scene", "file_kind", "candidate",
    "prompt_revision", "file", "web_file", "web_jpeg_quality", "web_bytes", "accepted", "failed_checks",
    "prompt", "placement_sentence", "revision_sentence", "plan_v1", "plan_v1_words", "plan_v2_words",
    "model_requested", "model_reported", "settings", "created_utc", "seconds", "width", "height", "sha256",
    "seed_requested", "seed_used", "seed_note", "finish_reason", "mime_returned", "stored_as",
    "image_input_tokens", "image_output_tokens", "image_thought_tokens", "image_usage_json", "image_usd_estimate",
    "price_basis",
    "detector", "detector_queries", "detector_boxes_json", "score_cut", "scale_cut", "main_elements_json",
    "main_found", "main_box", "main_center_x", "main_area", "required_side", "side_ok", "required_scale", "scale_ok",
    "feature_detector_rule", "feature_detector", "feature_detector_ok",
    "description_model", "description_model_reported", "description_settings", "description_instruction",
    "feature_question", "feature_answer", "feature_raw_replies", "text_question", "text_answer", "text_free_ok",
    "plan_fit_1", "plan_fit_2", "plan_fit_3", "plan_fit_ok", "plan_fit_source", "rule_version",
    "record_note", "superseded_decision", "acceptance_rule", "placement_rule", "revision_rule",
    "determinate_rules_note", "query_correction", "bank_sha256"]

DETERMINATE_NOTE = (
    "Rules made determinate by the script (the bank does not fix them): (1) main-element queries are the placement "
    "sentence's subject with 'The/her' replaced by 'a/an', one query per noun joined by 'and', head noun only "
    "(an 'of ...' complement is dropped: 'The bowl of lemons' -> 'a bowl'; see query_correction) ('The two tables': "
    "query 'a table', two best distinct boxes); (2) V1 must also show the main elements to the detector, because "
    "the I2 placement sentence is built from their box; (3) for weather and light scenes the detector confirms the "
    "main elements and the description model the feature; (4) the description question is 'Does the image show ' + "
    "feature phrase of plan version 1 + '?'; (5) 'their box' for two or more elements is the smallest box enclosing "
    "each element's best box; (6) the prompt revision rule as stated in revision_rule; (7) the 20 tries are counted "
    "per file (V1 and I2 separately); (8) thresholds come from candidate 1 of V1 of the twelve main scenes; "
    "(9) web copies are JPEG at the model's own output size (never resized), quality 85 unless that exceeds "
    "400,000 bytes, then the highest quality below 85 that fits; (10) the no-text check is asked of every candidate "
    "and the revision sentence for it is fixed in revision_rule; (11) a reply with no image is not a candidate "
    "(retried, at most 6 calls); a refused seed is dropped and the call repeated without one (seed_note); "
    "(12) if the model returns a JPEG, the stored PNG is a lossless copy of its decoded pixels (stored_as); "
    "(13) 'rounded to two decimals' means the unrounded value rounded once, half-up. The first freeze of the "
    "Nano Banana Pro run rounded twice (areas to four decimals, then Python's round() of the median 0.155) and gave "
    "a scale cut of 0.15; on 27 October 2026 it was corrected to 0.16, the written rule applied to the unrounded "
    "median 0.15503 (thresholds.json, corrections). Every decision that uses the scale cut was re-judged in "
    "candidate order; decisions at 0.15 are kept in superseded_decision.")


def manifest_row(rec, scene, bank_sha, row_type, accepted_file="", web=None):
    ev = rec.get("evaluation") or {}
    det = rec.get("detector") or {}
    desc = rec.get("description") or {}
    fd = scene["feature_det"]
    usage = rec.get("usage") or {}
    return {
        "row_type": row_type, "scene": scene["scene"], "scene_title": scene["title"],
        "with_person": "yes" if scene["person"] else "no", "kind_of_feature": scene["kind"],
        "reserve_scene": "yes" if scene["reserve"] else "no", "file_kind": rec["file_kind"],
        "candidate": rec["candidate"], "prompt_revision": rec["prompt_revision"],
        "file": accepted_file or rec["file"], "web_file": web[0] if web else "", "web_jpeg_quality": web[1] if web else "",
        "web_bytes": web[2] if web else "",
        "accepted": "superseded (not a candidate for the current placement sentence)" if rec.get("superseded")
        else {True: "yes", False: "no"}.get(ev.get("accepted"), "not evaluated"),
        "failed_checks": "; ".join(ev.get("failed_checks", [])),
        "prompt": rec["prompt"], "placement_sentence": rec.get("placement_sentence", ""),
        "revision_sentence": rec.get("revision_sentence", ""), "plan_v1": scene["plan_v1"],
        "plan_v1_words": scene["plan_v1_words"], "plan_v2_words": scene["plan_v2_words"],
        "model_requested": rec.get("model_requested", ""), "model_reported": rec.get("model_reported", "") or "(not returned)",
        "settings": rec.get("settings", ""), "created_utc": rec.get("created_utc", ""), "seconds": rec.get("seconds", ""),
        "width": rec.get("width", ""), "height": rec.get("height", ""), "sha256": rec.get("sha256", ""),
        "seed_requested": rec.get("seed_requested", ""), "seed_used": rec.get("seed_used", ""),
        "seed_note": rec.get("seed_note", ""), "finish_reason": rec.get("finish_reason", ""),
        "mime_returned": rec.get("mime_returned", ""), "stored_as": rec.get("stored_as", ""),
        "image_input_tokens": usage.get("promptTokenCount", ""), "image_output_tokens": usage.get("candidatesTokenCount", ""),
        "image_thought_tokens": usage.get("thoughtsTokenCount", ""),
        "image_usage_json": json.dumps(usage, separators=(",", ":")),
        "image_usd_estimate": rec.get("usd_estimate", ""), "price_basis": rec.get("price_basis", ""),
        "detector": det.get("model", ""), "detector_queries": "; ".join(det.get("queries", [])),
        "detector_boxes_json": json.dumps(det.get("boxes", {}), separators=(",", ":")),
        "score_cut": ev.get("score_cut", ""), "scale_cut": ev.get("scale_cut", ""),
        "main_elements_json": json.dumps(ev.get("main_elements", []), separators=(",", ":")),
        "main_found": ev.get("main_found", ""), "main_box": json.dumps(ev.get("main_box")),
        "main_center_x": ev.get("main_center_x", ""), "main_area": ev.get("main_area", ""),
        "required_side": ev.get("required_side", ""), "side_ok": ev.get("side_ok", ""),
        "required_scale": ev.get("required_scale", ""), "scale_ok": ev.get("scale_ok", ""),
        "feature_detector_rule": f"{fd[0]}: {fd[1]}" if fd else "none (weather or light)",
        "feature_detector": ev.get("feature_detector", ""), "feature_detector_ok": ev.get("feature_detector_ok", ""),
        "description_model": desc.get("model", ""),
        "description_model_reported": (desc.get("feature") or {}).get("model_reported", ""),
        "description_settings": json.dumps(desc.get("settings", {})), "description_instruction": desc.get("instruction", ""),
        "feature_question": (desc.get("feature") or {}).get("question", ""),
        "feature_answer": (desc.get("feature") or {}).get("answer", ""),
        "feature_raw_replies": json.dumps((desc.get("feature") or {}).get("raw", [])),
        "text_question": (desc.get("text_free") or {}).get("question", ""),
        "text_answer": (desc.get("text_free") or {}).get("answer", ""), "text_free_ok": ev.get("text_free_ok", ""),
        **{f"plan_fit_{i}": next((a["answer"] for a in desc.get("plan_fit", []) if a["sentence_no"] == i), "not asked")
           for i in range(1, PLAN_FIT_SENTENCES + 1)},
        "plan_fit_ok": ev.get("plan_fit_ok", ""),
        "plan_fit_source": "; ".join(sorted({a.get("source", "") for a in desc.get("plan_fit", [])})),
        "rule_version": ev.get("rule_version", ""),
        "acceptance_rule": ACCEPTANCE_RULE, "placement_rule": PLACEMENT_RULE if rec["file_kind"] == "I2" else "",
        "record_note": "; ".join(x for x in (REPLACEMENT_NOTE.get(scene["scene"], ""),
                                             rec.get("superseded") or rec.get("record_note", "")) if x),
        "superseded_decision": "; ".join(
            f"{'accepted' if e.get('accepted') else 'rejected'} {e.get('failed_checks') or ''} at scale cut "
            f"{e.get('scale_cut')}{' (before the plan-fit amendment)' if not e.get('rule_version') else ''}".strip()
            for e in rec.get("evaluation_superseded", [])),
        "revision_rule": REVISION_RULE, "determinate_rules_note": DETERMINATE_NOTE,
        "query_correction": QUERY_CORRECTION, "bank_sha256": bank_sha}


def write_outputs(scenes, bank_sha):
    """Accepted files, web copies, manifest and contact sheet, all from the saved candidates."""
    recs = all_candidates()
    accepted = {}
    for r in recs:
        if (r.get("evaluation") or {}).get("accepted") and not r.get("superseded") and r["scene"] in b1_scenes():
            key = (r["scene"], r["file_kind"])
            if key not in accepted or r["candidate"] < accepted[key]["candidate"]:
                accepted[key] = r
    WEB.mkdir(exist_ok=True)
    rows = []
    for r in sorted(recs, key=lambda r: (r["scene"], r["file_kind"] != "V1", r["candidate"])):
        rows.append(manifest_row(r, scenes[r["scene"]], bank_sha,
                                 "candidate (scene replaced)" if r["scene"] in REPLACED_SCENES else "candidate"))
    sheet_rows = []
    order = b1_scenes()
    for code in order:
        if (code, "V1") not in accepted:
            continue
        entry = {"scene": code}
        for kind in ("V1", "I2"):
            r = accepted.get((code, kind))
            if not r:
                continue
            dst = OUT / f"{code}_{kind}.png"
            shutil.copyfile(CAND / Path(r["file"]).name, dst)
            q, size = web_copy(dst, WEB / f"{code}_{kind}.jpg")
            rows.append(manifest_row(r, scenes[code], bank_sha, "accepted", f"{code}_{kind}.png",
                                     (f"web/{code}_{kind}.jpg", q, size)))
            entry[kind] = r
        sheet_rows.append(entry)
    with open(MANIFEST, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=MANIFEST_FIELDS)
        w.writeheader()
        w.writerows(rows)
    if sheet_rows:
        contact_sheet(sheet_rows, scenes)
    log(f"outputs: {sum(1 for r in rows if r['row_type'] == 'accepted')} accepted files, {len(recs)} candidates")
    return accepted


# ------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outputs", action="store_true", help="rebuild outputs from saved candidates; no API calls")
    ap.add_argument("--only", default="", help="comma-separated scenes to search this run (default: all twelve); "
                    "the first batch and thresholds always cover all twelve")
    ap.add_argument("--no-reserves", action="store_true", help="never move a failed scene to its reserve; stop and report")
    ap.add_argument("--max-candidate", type=int, default=0, help="stop a file's search before this candidate "
                    "number is exceeded (0: no cap beyond the rescue rules)")
    ap.add_argument("--soft-cap", type=float, default=25.0, help="stop when this script's ledger spending would pass this")
    args = ap.parse_args()

    scenes, bank_sha = read_bank()
    read_generation_settings()  # stops if the bank's Set B model, realism line, closing, no-text question or seed rule differ
    for code, s in scenes.items():
        assert 27 <= s["plan_v1_words"] <= 36, (code, s["plan_v1_words"])
    CAND.mkdir(parents=True, exist_ok=True)
    if args.outputs:
        write_outputs(scenes, bank_sha)
        return

    write_rule(bank_sha)
    ledger = Ledger(SCRIPT, soft_cap_usd=args.soft_cap)
    log(f"ledgers: Set B ${ledger.total():.2f} + Set A ${other_ledger_total():.2f} (cap ${HARD_CAP_USD:.0f}); "
        f"this run so far ${ledger.script_total():.2f}; soft cap ${args.soft_cap:.2f}")
    detector = ac.Detector("cpu")
    ctx = {"scenes": scenes, "ledger": ledger, "detector": detector, "th": None, "max_candidate": args.max_candidate}

    # First batch: candidate 1 of V1 for the twelve main scenes, checked, before any acceptance decision.
    def first(code):
        sc = scenes[code]
        try:
            return code, make_candidate(ctx, sc, "V1", 1, build_prompt(sc), 0, None, None)
        except (BudgetStop, ApiFailure) as e:
            STOP.set()
            STOP_REASON.append(str(e))
            log(f"STOP: {e}")
            return code, None
    if (load_thresholds().get("values") or {}).get("scale_cut") is not None:
        ctx["th"] = load_thresholds()  # frozen: the first batch is not needed again
    else:
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            firsts = dict(pool.map(first, MAIN_SCENES))
        if STOP.is_set() or any(v is None for v in firsts.values()):
            log("first batch incomplete; stopping:", STOP_REASON)
            write_outputs(scenes, bank_sha)
            return
        ctx["th"] = freeze_thresholds(scenes, firsts)

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        run_list = [c for c in args.only.split(",") if c in scenes] if args.only else b1_scenes()
        results = list(pool.map(lambda c: run_scene(ctx, c), run_list))

    # Reserves for scenes that failed the checks (not for stops).
    used = set()
    for code, status, v1, i2 in list(results):
        if status == "failed" and args.no_reserves:
            log(f"{code} failed after its revision; reserve not used (--no-reserves): decision needed")
            continue
        if status == "failed" and not STOP.is_set():
            reserve = RESERVE_OF_KIND[scenes[code]["person"]]
            if reserve in used:
                log(f"{code} failed and its reserve {reserve} is already in use")
                continue
            used.add(reserve)
            log(f"{code} failed after its revision; replaced by reserve {reserve}")
            results.append(run_scene(ctx, reserve))

    if not STOP.is_set():
        complete_records(ctx)
    accepted = write_outputs(scenes, bank_sha)
    log("summary:")
    for code, status, v1, i2 in results:
        log(f"  {code}: {status}; V1 c{v1['candidate'] if v1 else '-'}; I2 c{i2['candidate'] if i2 else '-'}")
    if STOP_REASON:
        log("stop reasons:", STOP_REASON)
    log(f"ledgers: Set B ${ledger.total():.2f} + Set A ${other_ledger_total():.2f}; this run ${ledger.script_total():.2f}; "
        f"accepted files {len(accepted)}")


if __name__ == "__main__":
    main()
