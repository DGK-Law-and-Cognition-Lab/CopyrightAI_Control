"""Write setA/thresholds.json: every rule first, then each number computed by its rule from the first
candidates. A number, once written, is never changed (the script refuses to overwrite it).

    python3 setA_calibrate.py rules      # writes the rules (before any acceptance decision)
    python3 setA_calibrate.py detector   # score cut, from candidate 1 of each main scene's source
    python3 setA_calibrate.py mask       # difference threshold, speck size and widening radius, from
                                         # candidate 1 of each main scene's small and medium additions
"""

import json
import math
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

import setA_common as C
import setA_checks as K

RULES = {
    "written_utc": None,
    "note": ("Rules written 27 October 2026 before any GPT Image 2 candidate was judged. Each number is "
             "computed by its rule from this model's first candidates and then frozen; none is relative to other "
             "candidates and none is changed after it is written."),
    "image_model": (f"{C.IMAGE_MODEL}, chosen by David G. Kamper on 27 October 2026 (prompt bank, 'The models'); "
                    "source prompt = the eight part sentences, the Set A realism line, and the closing sentence"),
    "history": ("A first run with GPT Image 2.5 Flare (../setA_superseded_flare_2026-10-27/) was stopped when David "
                "rejected that model. Its rules are kept here with three changes, all decided on 27 October 2026 "
                "before this run began: (1) the absolute bands (small 1 to 2, medium 8 to 12, large 25 to 35 "
                "percent) are replaced by within-scene ordering; (2) the element questions drop 'empty', 'bare', "
                "'open' and 'clear' where they describe the place before the edit; (3) every file must pass the "
                "no-text question. SA10's open-area question is used in the form amended in the first run."),
    "detector": {
        "model": f"{K.DETECTOR_REPO} at revision {K.DETECTOR_REVISION}, CPU, each query scored on its own "
                 "(sigmoid of its logit)",
        "score_cut_rule": (
            "Run the detector on candidate 1 of the source of each of the ten main scenes (SA01 to SA10) with two "
            "kinds of query. Present: the scene's rearrangement-object queries (19 in all; SA06 has one query, "
            "'an oar'). Absent: eight objects that cannot appear in a scene plausible for 1900 to 1925 "
            f"({'; '.join(K.ABSENT_QUERIES)}), the same eight for every scene (80 in all). Each query's score is "
            "its best box's score. Every observed score is a possible cut c; Youden's J(c) is the share of "
            "present scores at or above c minus the share of absent scores at or above c. c* is the smallest "
            "observed score with the largest J. The score cut is the midpoint between c* and the largest "
            "observed score below c*, rounded to three decimals. A detection counts when its score is at "
            "least the cut."),
        "distinct_boxes_rule": f"Two boxes for one query are the same object when their IoU is at least {K.NMS_IOU} "
                               "(fixed, not set from data).",
    },
    "change_mask": {
        "difference": "Per-pixel difference d: the Euclidean distance between the two images' RGB values "
                      "(0 to 441), with no smoothing.",
        "difference_threshold_rule": (
            "Over every pixel of candidate 1 of the small and of the medium addition of each of the ten main "
            "scenes (20 raw edits, each compared with the source it was made from), take the median m and the "
            "median absolute deviation MAD of d. The threshold is m + 3.5 x MAD / 0.6745, the value at which a "
            "pixel's modified z-score (Iglewicz and Hoaglin, 1993) passes 3.5, rounded to one decimal. A pixel "
            "is marked as changed when d is above the threshold."),
        "speck_rule": (
            "With that threshold, find every 8-connected group of marked pixels in the same 20 edits. The speck "
            "size is the 99.9th percentile of the groups' sizes in pixels, rounded up to a whole number. Every "
            "group of at most that many pixels is a speck and is removed; then every unmarked area wholly "
            "enclosed by marked pixels is filled. The result is the cleaned change mask."),
        "widening_rule": (
            "With the cleaned change masks of the same 20 edits, for each whole-pixel distance k = 1, 2, ... from "
            "the mask (Euclidean distance), take the median of d over the pixels whose distance lies in "
            "(k - 1, k], pooled over the 20 edits. The widening radius is the smallest k whose ring median is at "
            "most m, the median of d over all pixels (the level of the model's re-rendering of an unchanged "
            "pixel), so the edge of the pasted region falls where the edit differs from its input no more than "
            "a typical pixel does. If no k up to 64 qualifies, the radius is 64."),
        "widened_mask": "Every pixel within the widening radius of the cleaned mask (Euclidean distance), with "
                        "enclosed holes filled.",
        "compositing": "The accepted file takes the raw edit's pixels inside the widened mask and the input's "
                       "pixels everywhere else (input = the accepted source for small and medium; the accepted, "
                       "composited medium file for large).",
        "masked_area": "Share of the image (percent of 1536 x 1024 pixels) inside the cleaned change mask of the "
                       "composited file compared with the accepted source, computed with the same threshold and "
                       "cleaning. For the large file this includes the medium element.",
    },
    "acceptance": {
        "source": ("Detector: for each rearrangement-object query, at least one box scoring at least the cut "
                   "(SA06, whose two objects are both oars: at least two distinct 'an oar' boxes). Description "
                   "model: 'yes' to every object question, to the open-area question, and to the no-text "
                   f"question '{C.TEXT_QUESTION}'. The questions are in source_questions."),
        "source_questions": {k: [q for _, q in v["objects"]] + [v["open"]] for k, v in C.SOURCE_CHECKS.items()},
        "addition": ("Detector: for each element the file must show (small: the small element; medium: the "
                     "medium element; large: the medium element and the two further elements), a box for its "
                     "query scoring at least the cut whose center lies inside the region where the file was "
                     "composited from an edit (the widened mask; for large, the union of the medium's and the "
                     "large's widened masks). Description model: 'yes' to the element's question (element_questions: "
                     "'Does the image show ' + the bank phrase without 'empty', 'bare', 'open' and 'clear' where "
                     "they describe the place before the edit + '?') for each element, and 'yes' to the no-text "
                     f"question '{C.TEXT_QUESTION}'. Size, by within-scene ordering of the masked area (above): "
                     "small at least 0.1 percent of the image; medium at least 2 times the accepted small file's "
                     "masked area for the scene and at least 0.5 percent; large at least 2 times the accepted medium "
                     "file's masked area. Within a scene the small file is accepted before any medium candidate is "
                     "judged, and the medium before any large."),
        "element_questions": None,
        "description_model": (f"{C.VISION_MODEL}, reasoning effort none, temperature 0, at most 16 output tokens, one "
                              "question per call with the instruction 'Look at the image and answer the question "
                              "with exactly one word: yes or no.'; the reply must be exactly yes or no (case, "
                              "spaces and a final full stop ignored); other replies are asked again, three calls "
                              "at most, then recorded as invalid, which does not confirm."),
        "order": "Candidates are numbered in the order made, per scene and file; the first that passes every "
                 "check is accepted and no later candidate is judged.",
    },
    "rescue": {
        "count": "The 20 tries are counted per scene and per file (source, small, medium, large); only requests "
                 "that return an image count as tries.",
        "source_revision": ("After 20 failed source candidates, one revision: the bank's eight sentences, then the "
                            "sentence 'Make sure the image clearly shows ' + the items whose check failed in more "
                            "than half of the 20 tries (objects named by their detector query, the open area by "
                            "the scene's open-area phrase), joined with commas and 'and', + '.', then the closing "
                            "sentence. The candidate count restarts at the next number; 20 more tries."),
        "addition_revision": ("After 20 failed candidates of an addition, one revision: 'Add ' + phrase + ', clearly "
                              "visible. Change nothing else.' (for large, the phrase is the two further elements). "
                              "20 more tries."),
        "reserve": ("A scene with no passing candidate for any of its four files after the revision is replaced "
                    "by the reserve of its kind (SA-R1 for a scene with a person, SA-R2 without), which takes its "
                    "place in every A1 list; the reserve's four files are made by the same rules."),
    },
    "numbers": {},
}

OPEN_PHRASES = {  # used only by the source revision rule
    "SA01": "the far end of the table bare", "SA02": "an empty stretch of dock beside the man",
    "SA03": "a wide band of empty sky in the middle", "SA04": "the bare rug in front of the man",
    "SA05": "the right third of the counter bare and empty", "SA06": "an empty stretch of water",
    "SA07": "the right half of the table bare", "SA08": "the open right side of the street",
    "SA09": "the empty path", "SA10": "the open sea in the center",
    "SA-R1": "the left end of the table bare", "SA-R2": "the open field to the right",
}


def load():
    return json.loads(C.THRESHOLDS.read_text(encoding="utf-8")) if C.THRESHOLDS.exists() else None


def save(t):
    C.THRESHOLDS.write_text(json.dumps(t, indent=2, ensure_ascii=False), encoding="utf-8")


def set_number(t, key, value, basis):
    if key in t["numbers"]:
        sys.exit(f"{key} is already set to {t['numbers'][key]['value']}; numbers are never changed.")
    t["numbers"][key] = {"value": value, "computed_utc": C.now(), "basis": basis}


def element_questions():
    import re
    out = {}
    for sc in C.read_set_a().values():
        for e in [sc["small"], sc["medium"]] + sc["large_elements"]:
            out[e] = "Does the image show " + re.sub(r"\b(empty|bare|open|clear) ", "", e) + "?"
    return out


def cmd_rules():
    if C.THRESHOLDS.exists():
        sys.exit("thresholds.json exists; rules are written once.")
    C.OUT.mkdir(parents=True, exist_ok=True)
    t = json.loads(json.dumps(RULES))
    t["acceptance"]["element_questions"] = element_questions()
    t["written_utc"] = C.now()
    t["prompt_bank_sha256"] = C.bank_sha256()
    save(t)
    print("rules written", C.THRESHOLDS)


def cmd_detector():
    t = load()
    det = K.Detector()
    present, absent, rows = [], [], []
    for scene in C.MAIN_SCENES:
        img = C.load_rgb(C.CAND / f"{scene}_source_c01.png")
        qs = [q for q, _ in C.SOURCE_CHECKS[scene]["objects"]]
        res = det.detect(img, qs + K.ABSENT_QUERIES)
        for q in qs:
            present.append(res[q][0]["score"])
            rows.append((scene, "present", q, res[q][0]["score"]))
        for q in K.ABSENT_QUERIES:
            absent.append(res[q][0]["score"])
            rows.append((scene, "absent", q, res[q][0]["score"]))
    vals = sorted(set(present + absent))
    best, cstar = -2, None
    for c in vals:
        j = np.mean([p >= c for p in present]) - np.mean([a >= c for a in absent])
        if j > best + 1e-12:
            best, cstar = j, c
    below = [v for v in vals if v < cstar]
    cut = round((cstar + max(below)) / 2, 3) if below else round(cstar, 3)
    basis = {"present_scores": present, "absent_scores": absent, "youden_j": round(float(best), 4),
             "c_star": cstar, "largest_below_c_star": max(below) if below else None,
             "scores_by_query": [{"scene": s, "kind": k, "query": q, "best_score": v} for s, k, q, v in rows],
             "detector": det.name}
    set_number(t, "detector_score_cut", cut, basis)
    save(t)
    print(f"detector score cut {cut} (J = {best:.3f}; present min {min(present)}, absent max {max(absent)})")


def first_edit_pairs():
    pairs = []
    for scene in C.MAIN_SCENES:
        for kind in ("small", "medium"):
            rec = json.loads((C.CAND / f"{scene}_{kind}_c01.json").read_text(encoding="utf-8"))
            src = C.CAND / rec["input_file"]
            if not src.exists():
                src = C.OUT / rec["input_file"]
            pairs.append((scene, kind, src, C.CAND / rec["raw_file"]))
    return pairs


def cmd_mask():
    t = load()
    pairs = first_edit_pairs()
    ds = [K.difference(K.arr(C.load_rgb(s)), K.arr(C.load_rgb(e))) for _, _, s, e in pairs]
    pooled = np.concatenate([d.ravel() for d in ds])
    m = float(np.median(pooled))
    mad = float(np.median(np.abs(pooled - m)))
    thr = round(m + 3.5 * mad / 0.6745, 1)
    del pooled
    set_number(t, "difference_threshold", thr,
               {"pairs": [f"{s}_{k}_c01" for s, k, _, _ in pairs], "median_d": round(m, 4), "mad_d": round(mad, 4)})

    sizes = []
    for d in ds:
        lab, n = ndi.label(d > thr, structure=K.EIGHT)
        sizes.append(np.bincount(lab.ravel())[1:])
    sizes = np.concatenate(sizes)
    speck = int(math.ceil(np.percentile(sizes, 99.9)))
    set_number(t, "speck_px", speck, {"groups": int(sizes.size), "largest_group": int(sizes.max())})

    th = {"difference_threshold": thr, "speck_px": speck}
    ring_vals = {k: [] for k in range(1, 65)}
    for d in ds:
        marks = d > thr
        mask = ndi.binary_fill_holes(K.remove_specks(marks, speck))
        dist = ndi.distance_transform_edt(~mask)
        for k in range(1, 65):
            sel = (dist > k - 1) & (dist <= k)
            ring_vals[k].append(d[sel])
    radius, medians = 64, {}
    for k in range(1, 65):
        v = np.concatenate(ring_vals[k])
        medians[k] = round(float(np.median(v)), 3) if v.size else None
        if v.size and medians[k] <= m and radius == 64 and k < 64:
            radius = k
            break
    set_number(t, "widening_px", radius, {"ring_medians_by_distance": medians, "median_d_all_pixels": round(m, 4)})
    save(t)
    print(f"difference threshold {thr} (median {m:.2f}, MAD {mad:.2f}); speck size {speck} px "
          f"({sizes.size} groups); widening radius {radius} px")


def medium_mask_for(scene, sha):
    """The widened mask of the medium file a large candidate was made from (matched by checksum)."""
    for png in [C.OUT / f"{scene}_medium.png"] + sorted(C.CAND.glob(f"{scene}_medium_c[0-9][0-9].png")):
        if png.exists() and C.sha256_file(png) == sha:
            mask = png.with_name(png.stem + "_mask.png")
            return K.load_mask(mask), png.name
    raise FileNotFoundError(f"no medium file of {scene} with checksum {sha[:12]}")


def spill_of(rec, det, th):
    """Spill (percent) of one addition candidate, rebuilt from its raw edit and input with the frozen thresholds."""
    import setA_run as R
    t = {"difference_threshold": th["difference_threshold"]["value"], "speck_px": th["speck_px"]["value"]}
    cut, wpx = th["detector_score_cut"]["value"], th["widening_px"]["value"]
    sc = C.read_set_a()[rec["scene"]]
    src = C.CAND / rec["input_file"] if (C.CAND / rec["input_file"]).exists() else C.OUT / rec["input_file"]
    if not src.exists():
        src = R.SUPERSEDED_UC / rec["input_file"]
    inp = K.arr(C.load_rgb(src))
    raw = K.arr(C.load_rgb(C.CAND / rec["raw_file"]))
    wide = K.widen(K.change_mask(inp, raw, t), wpx)
    comp = K.composite(raw, inp, wide)
    region, medium_used = wide, None
    if rec["kind"] == "large":
        mm, medium_used = medium_mask_for(rec["scene"], rec["input_sha256"])
        region = wide | mm
    elements = C.added_elements(sc, rec["kind"])
    boxes, _ = det.detect(Image.fromarray(comp), [C.ELEMENT_QUERIES[e] for e in elements]), None
    spill, region_pct, used = R.spill_pct(inp, comp, t, boxes, elements, region, cut, wpx)
    return {"spill_pct": spill, "added_element_region_pct": region_pct, "input": src.name,
            "medium_mask_from": medium_used, "boxes_used": {e: len(v) for e, v in used.items()}}


def cmd_spill():
    t = load()
    if "--correct-first-inputs" in sys.argv and "spill_cut_pct" in t["numbers"]:
        old = t["numbers"].pop("spill_cut_pct")
        t.setdefault("corrections", []).append({
            "utc": C.now(), "number": "spill_cut_pct", "withdrawn_value": old["value"], "withdrawn_basis": old["basis"],
            "reason": ("The first computation (written " + old["computed_utc"] + ") took candidate c01 of every addition "
                       "file, including three made with a superseded phrase (SA04 medium c01, SA10 medium c01, SA-R1 "
                       "large c01), and measured them against the current phrase's elements, which those images do "
                       "not contain (SA-R1 large c01 scored 5.79 percent because the cupboard and rocking chair it was "
                       "measured against are not in it). Those candidates are marked excluded, not candidates of the "
                       "current file. The cut is recomputed from each file's first candidate under its current phrase "
                       "(SA04 medium c41, SA10 medium c81, SA-R1 large c41), before any acceptance decision used it.")})
        save(t)
    th = t["numbers"]
    det = K.Detector()
    vals = []
    for scene in C.MAIN_SCENES + ["SA-R1", "SA-R2"]:
        for kind in ("small", "medium", "large"):
            # The file's first candidate: the first one that is a candidate of the current file (candidates made
            # with a superseded phrase are marked excluded and are not candidates of the current file).
            recs = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(C.CAND.glob(f"{scene}_{kind}_c[0-9][0-9].json"))]
            recs = [r for r in recs if not r.get("excluded")]
            if not recs:
                continue
            rec = recs[0]
            r = spill_of(rec, det, th)
            vals.append(dict(r, file=rec["file"][:-4]))
            print(f"{rec['file'][:-4]} spill {r['spill_pct']}% (region {r['added_element_region_pct']}%, boxes {r['boxes_used']})", flush=True)
    x = np.array([v["spill_pct"] for v in vals])
    m = float(np.median(x)); mad = float(np.median(np.abs(x - m)))
    cut = math.ceil((m + 3.5 * mad / 0.6745) * 1000) / 1000
    set_number(t, "spill_cut_pct", cut, {"candidates": vals, "n": len(vals), "median": round(m, 4), "mad": round(mad, 4),
                                         "units": "percent of the image's 1536 x 1024 pixels"})
    save(t)
    print(f"spill cut {cut}% (median {m:.4f}, MAD {mad:.4f}, n {len(vals)})")


def cmd_known():
    """Spill of the two known cases, SA04 large c28 and SA-R1 large c42 (report only)."""
    t = load()
    det = K.Detector()
    for name in ("SA04_large_c28", "SA-R1_large_c42"):
        rec = json.loads((C.CAND / f"{name}.json").read_text(encoding="utf-8"))
        r = spill_of(rec, det, t["numbers"])
        cut = t["numbers"]["spill_cut_pct"]["value"]
        print(f"{name}: spill {r['spill_pct']}% vs cut {cut}% -> {'passes' if r['spill_pct'] <= cut else 'fails'}; {r}")


if __name__ == "__main__":
    {"rules": cmd_rules, "detector": cmd_detector, "mask": cmd_mask, "spill": cmd_spill,
     "known": cmd_known}[sys.argv[1]]()
