"""Make and judge the Set A files for Paper A Study 1, by rule only.

    python3 setA_run.py sources [SCENE ...]        # judge/make sources until one passes per scene
    python3 setA_run.py first-edits [SCENE ...]    # candidate 1 of small and medium per scene (for the
                                                   # mask thresholds; judged later like any candidate)
    python3 setA_run.py additions [SCENE ...]      # judge/make small and medium, then large
    python3 setA_run.py status

Candidates are judged in the order made; the first that passes is accepted and copied to
setA/<scene>_<kind>.png (and <scene>_<kind>_mask.png for an addition). Each candidate's check
results are written into its .json record in setA/candidates/. A file with 20 failed tries gets the
one revision in thresholds.json; a scene that still fails is marked for its reserve. At most three
requests are in flight; every call passes the budget guard in setA_common first.
"""

import json
import shutil
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from PIL import Image

import setA_common as C
import setA_checks as K
import setA_make as M
import setA_objects as O

SCENES = C.read_set_a()
_det, _det_lock = None, threading.Lock()
STATUS = C.OUT / "status.json"
_status_lock = threading.Lock()


def detect(img, queries):
    global _det
    with _det_lock:
        if _det is None:
            _det = K.Detector()
        return _det.detect(img, queries), _det.name


def thresholds():
    t = K.load_thresholds()
    n = t["numbers"]
    return {"cut": n["detector_score_cut"]["value"],
            "difference_threshold": n.get("difference_threshold", {}).get("value"),
            "speck_px": n.get("speck_px", {}).get("value"),
            "widening_px": n.get("widening_px", {}).get("value"), "raw": t}


def load_status():
    return json.loads(STATUS.read_text(encoding="utf-8")) if STATUS.exists() else {}


def set_status(scene, kind, value):
    with _status_lock:
        s = load_status()
        s.setdefault(scene, {})[kind] = value
        STATUS.write_text(json.dumps(s, indent=2), encoding="utf-8")


def accepted_path(scene, kind):
    return C.OUT / f"{scene}_{kind}.png"


# ---------------------------------------------------------------------------------------------
# Judging
# ---------------------------------------------------------------------------------------------

def judge_source(rec):
    th = thresholds()
    scene = rec["scene"]
    img = C.load_rgb(C.CAND / rec["file"])
    spec = C.SOURCE_CHECKS[scene]
    queries = [q for q, _ in spec["objects"]]
    boxes, det_name = detect(img, queries)
    det = []
    for q in queries:
        need = 2 if scene == "SA06" else 1
        kept = K.distinct(boxes[q], th["cut"])
        det.append({"query": q, "boxes_at_or_above_cut": len(kept), "needed": need,
                    "best_score": boxes[q][0]["score"] if boxes[q] else None,
                    "boxes": boxes[q][:5], "pass": len(kept) >= need})
    questions = [qq for _, qq in spec["objects"]] + [spec["open"], C.TEXT_QUESTION]
    answers = [C.ask_yes_no(img, q, f"Set A check {rec['file']}") for q in questions]
    checks = {"detector": det_name, "detector_score_cut": th["cut"], "detections": det,
              "description_model": C.VISION_MODEL, "questions": answers,
              "detector_pass": all(d["pass"] for d in det),
              "description_pass": all(a["answer"] == "yes" for a in answers),
              "judged_utc": C.now()}
    checks["pass"] = checks["detector_pass"] and checks["description_pass"]
    rec["checks"], rec["accepted"] = checks, checks["pass"]
    M.write_record(rec)
    return rec


def size_minimum(scene, kind):
    """The amended size rule (27 October 2026): within-scene ordering against the accepted files."""
    if kind == "small":
        return C.SMALL_MIN_PCT, "small: masked area at least 0.1 percent"
    prev = "small" if kind == "medium" else "medium"
    prev_area = json.loads((C.OUT / f"{scene}_{prev}.json").read_text(encoding="utf-8"))["checks"]["masked_area_pct"]
    if kind == "medium":
        return (round(max(C.RATIO * prev_area, C.MEDIUM_MIN_PCT), 3),
                f"medium: at least 2 x the accepted small's {prev_area} percent and at least 0.5 percent")
    return round(C.RATIO * prev_area, 3), f"large: at least 2 x the accepted medium's {prev_area} percent"


def added_element_region(boxes, elements, region, cut, widen_px, shape):
    """Spill check (amendment of 28 October 2026): the union of the detector's accepted boxes for the file's added
    elements (every box for the element's query scoring at least the cut whose center lies inside the composited
    region), each box's rectangle grown by widen_px pixels on every side and clipped to the image."""
    h, w = shape
    m = np.zeros(shape, dtype=bool)
    used = {}
    for e in elements:
        q = C.ELEMENT_QUERIES[e]
        sel = [b for b in boxes[q] if b["score"] >= cut and K.center_inside(b["box"], region)]
        used[e] = sel
        for b in sel:
            x0, y0, x1, y1 = b["box"]
            m[max(0, int(np.floor(y0 - widen_px))):min(h, int(np.ceil(y1 + widen_px))),
              max(0, int(np.floor(x0 - widen_px))):min(w, int(np.ceil(x1 + widen_px)))] = True
    return m, used


def spill_pct(inp, comp, t, boxes, elements, region, cut, widen_px):
    """Percent of the image inside the cleaned change mask (input against composited file, before widening) but
    outside the added-element region."""
    change_in = K.change_mask(inp, comp, t)
    area, used = added_element_region(boxes, elements, region, cut, widen_px, change_in.shape)
    return round(100.0 * float((change_in & ~area).mean()), 4), K.area_pct(area), used


def judge_addition(rec):
    th = thresholds()
    t = {"difference_threshold": th["difference_threshold"], "speck_px": th["speck_px"]}
    scene, kind = rec["scene"], rec["kind"]
    sc = SCENES[scene]
    stem = rec["file"][:-4]
    src = K.arr(C.load_rgb(accepted_path(scene, "source")))
    inp = K.arr(C.load_rgb(C.CAND / rec["input_file"] if (C.CAND / rec["input_file"]).exists()
                           else C.OUT / rec["input_file"]))
    raw = K.arr(C.load_rgb(C.CAND / rec["raw_file"]))
    change = K.change_mask(inp, raw, t)
    wide = K.widen(change, th["widening_px"])
    comp = K.composite(raw, inp, wide)
    if kind == "large":
        region = wide | K.load_mask(C.OUT / f"{scene}_medium_mask.png")
    else:
        region = wide
    vs_source = K.change_mask(src, comp, t)
    area = K.area_pct(vs_source)
    min_pct, size_rule = size_minimum(scene, kind)
    same_in, n_in = K.identical_outside(comp, inp, wide)
    same_src, n_src = K.identical_outside(comp, src, region)
    Image.fromarray(comp).save(C.CAND / f"{stem}.png")
    K.save_mask(wide, C.CAND / f"{stem}_mask.png")
    K.save_mask(change, C.CAND / f"{stem}_change.png")
    K.save_mask(vs_source, C.CAND / f"{stem}_change_vs_source.png")
    img = Image.fromarray(comp)
    elements = C.added_elements(sc, kind)
    queries = [C.ELEMENT_QUERIES[e] for e in elements]
    boxes, det_name = detect(img, queries)
    det = []
    for e, q in zip(elements, queries):
        inside = [b for b in boxes[q] if K.center_inside(b["box"], region)]
        best = inside[0]["score"] if inside else None
        det.append({"element": e, "query": q, "best_score_inside_region": best,
                    "best_score_anywhere": boxes[q][0]["score"] if boxes[q] else None,
                    "boxes": boxes[q][:5], "pass": best is not None and best >= th["cut"]})
    # An answer recorded earlier for the same question about the same composited file is reused (the file is
    # rebuilt identically from the same masks); a new or amended question is asked.
    prior = {}
    earlier = [((rec.get("judgment_under_bands") or {}).get("checks") or {})] + \
        [(j.get("checks") or {}) for j in rec.get("previous_judgments", [])]
    for e in earlier:
        if e.get("masked_area_pct") == area and e.get("input_sha256", rec["input_sha256"]) == rec["input_sha256"]:
            prior.update({a["question"]: a for a in e.get("questions", []) if a["answer"] in ("yes", "no")})
    answers = []
    for q in [C.element_question(e) for e in elements] + [C.TEXT_QUESTION]:
        if q in prior:
            answers.append(dict(prior[q], reused_from="judgment_under_bands"))
        else:
            answers.append(C.ask_yes_no(img, q, f"Set A check {rec['file']}"))
    checks = {"detector": det_name, "detector_score_cut": th["cut"],
              "difference_threshold": th["difference_threshold"], "speck_px": th["speck_px"],
              "widening_px": th["widening_px"],
              "change_area_vs_input_pct": K.area_pct(change), "widened_area_pct": K.area_pct(wide),
              "masked_area_pct": area, "size_rule": size_rule, "size_min_pct": min_pct,
              "size_pass": area >= min_pct,
              "identical_to_input_outside_mask": same_in, "pixels_differing_outside_mask": n_in,
              "identical_to_source_outside_edit_region": same_src, "pixels_differing_from_source_outside": n_src,
              "detections": det, "description_model": C.VISION_MODEL, "questions": answers,
              "detector_pass": all(d["pass"] for d in det),
              "description_pass": all(a["answer"] == "yes" for a in answers),
              "judged_utc": C.now()}
    if kind == "large":
        med = K.load_mask(C.OUT / f"{scene}_medium_mask.png")
        checks["medium_mask_pixels_inside_large_mask"] = int((med & wide).sum())
    earlier_pass = (checks["size_pass"] and checks["detector_pass"] and checks["description_pass"]
                    and same_in and same_src)
    checks["input_sha256"] = rec["input_sha256"]
    # Object-position check (amendment of 29 October 2026; replaces the spill check, whose values stay in
    # previous_judgments): every trackable object found in the input must be found in the composited file by a box
    # with IoU at least 0.5 against its input box.
    trk = th["raw"]["tracked_objects"][scene]["trackable"]
    det_in, _ = detect(Image.fromarray(inp), trk)
    det_out, _ = detect(img, trk)
    pos_ok, pos_rows = O.position_check(det_in, det_out, trk, th["cut"])
    checks["object_position"] = {"trackable": trk, "iou_min": O.IOU_MIN, "objects": pos_rows}
    checks["object_position_pass"] = pos_ok
    checks["pass"] = earlier_pass and checks["object_position_pass"]
    rec["checks"], rec["accepted"] = checks, checks["pass"]
    rec["sha256"] = C.sha256_file(C.CAND / rec["file"])
    M.write_record(rec)
    return rec


# ---------------------------------------------------------------------------------------------
# Search: the first candidate that passes, 20 tries, one revision, then the reserve
# ---------------------------------------------------------------------------------------------

def failure_counts(recs):
    counts = {"size": 0, "detector": 0, "description": 0}
    for r in recs:
        c = r["checks"]
        if "size_pass" in c and not c["size_pass"]:
            counts["size"] += 1
        if not c["detector_pass"]:
            counts["detector"] += 1
        if not c["description_pass"]:
            counts["description"] += 1
    return counts


def source_revision(scene, recs):
    sc = SCENES[scene]
    spec = C.SOURCE_CHECKS[scene]
    from setA_calibrate import OPEN_PHRASES
    items = []
    n = len(recs)
    for i, (q, _) in enumerate(spec["objects"]):
        fails = sum(1 for r in recs if not r["checks"]["detections"][i]["pass"]
                    or r["checks"]["questions"][i]["answer"] != "yes")
        if fails > n / 2:
            items.append(q)
    open_i = len(spec["objects"])          # questions: objects, then the open area, then no text
    if sum(1 for r in recs if r["checks"]["questions"][open_i]["answer"] != "yes") > n / 2:
        items.append(OPEN_PHRASES[scene])
    if not items:
        items = [q for q, _ in spec["objects"]] + [OPEN_PHRASES[scene]]
    joined = items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]
    return " ".join(sc["parts"]) + f" Make sure the image clearly shows {joined}. " + C.SOURCE_SUFFIX


def addition_revision(scene, kind, recs):
    """Amended 27 October 2026: with no target percentage, the one revision is always 'clearly visible'."""
    sc = SCENES[scene]
    phrase = sc["large"] if kind == "large" else sc[kind]
    return f"Add {phrase}, clearly visible. Change nothing else.", failure_counts(recs), "fixed wording"


def accept(rec):
    scene, kind = rec["scene"], rec["kind"]
    shutil.copyfile(C.CAND / rec["file"], accepted_path(scene, kind))
    if kind != "source":
        shutil.copyfile(C.CAND / (rec["file"][:-4] + "_mask.png"), C.OUT / f"{scene}_{kind}_mask.png")
    (C.OUT / f"{scene}_{kind}.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False), encoding="utf-8")
    set_status(scene, kind, {"state": "accepted", "candidate": rec["candidate"], "revision": rec["revision"]})
    print(f"ACCEPTED {scene} {kind} candidate {rec['candidate']}"
          + (f" area {rec['checks'].get('masked_area_pct')}%" if kind != "source" else ""), flush=True)


def search(scene, kind):
    """Judge existing candidates in order; make new ones until one passes or the rescue rule ends."""
    if accepted_path(scene, kind).exists():
        return True
    sc = SCENES[scene]
    judge = judge_source if kind == "source" else judge_addition
    if kind == "source":
        base_prompt, input_path = sc["prompt"], None
    else:
        input_path = accepted_path(scene, "medium" if kind == "large" else "source")
        if not input_path.exists():
            return False
        base_prompt = C.instruction(sc, kind)
    revised, revision_note = None, None
    st = load_status().get(scene, {}).get(kind, {})
    if st.get("revised_prompt"):
        revised = st["revised_prompt"]
    expected_input = C.sha256_file(input_path) if input_path else None
    while True:
        nums = M.existing_numbers(scene, kind)
        recs = [M.read_record(scene, kind, n) for n in nums]
        for r in recs:
            if expected_input and r["input_sha256"] != expected_input and not r.get("excluded"):
                r["excluded"] = (f"made from {r['input_file']}, which is not the accepted input "
                                 f"{input_path.name}; not a candidate and not counted as a try")
                r["accepted"] = False
                M.write_record(r)
            if (r["kind"] != "source" and r["revision"] == 1 and "enough to fill about" in r["prompt_or_instruction"]
                    and not r.get("excluded")):
                r["excluded"] = ("made with the superseded size revision ('... enough to fill about P percent of "
                                 "the picture'), which the amended rules of 27 October 2026 do not have; not a "
                                 "candidate under the amended rules and not counted as a try")
                r["accepted"] = False
                M.write_record(r)
            if (r["kind"] != "source" and not r.get("excluded")
                    and r["prompt_or_instruction"] not in (base_prompt, addition_revision(scene, kind, [])[0])):
                r["excluded"] = ("made with an earlier phrase (before the phrase amendment of 28 October 2026); kept "
                                 "in the manifest, not a try under the current phrase")
                r["accepted"] = False
                M.write_record(r)
        recs = [r for r in recs if not r.get("excluded")]
        for r in recs:
            if r["accepted"] is None:
                r = judge(r)
                tag = (f"area {r['checks']['masked_area_pct']}% (min {r['checks']['size_min_pct']}), "
                       if kind != "source" else "")
                print(f"  {r['file']}: {tag}detector {r['checks']['detector_pass']}, "
                      f"description {r['checks']['description_pass']} -> {'PASS' if r['accepted'] else 'fail'}",
                      flush=True)
            if r["accepted"]:
                accept(r)
                return True
        rev0 = [r for r in recs if r["revision"] == 0]
        rev1 = [r for r in recs if r["revision"] == 1]
        if len(rev1) >= C.MAX_TRIES:
            set_status(scene, kind, {"state": "failed after revision", "revised_prompt": revised,
                                     "tries": len(recs)})
            print(f"FAILED {scene} {kind}: 20 tries and 20 revised tries; the scene goes to its reserve", flush=True)
            return False
        if len(rev0) >= C.MAX_TRIES and revised is None:
            if kind == "source":
                revised, counts, top = source_revision(scene, rev0), None, None
            else:
                revised, counts, top = addition_revision(scene, kind, rev0)
            set_status(scene, kind, {"state": "revised", "revised_prompt": revised, "failure_counts": counts,
                                     "most_frequent_failure": top, "revised_utc": C.now()})
            print(f"REVISION {scene} {kind}: {revised}", flush=True)
        prompt = revised if len(rev0) >= C.MAX_TRIES else base_prompt
        revision = 1 if len(rev0) >= C.MAX_TRIES else 0
        if kind == "source":
            M.make_source(sc, prompt, revision=revision)
        else:
            M.make_edit(sc, kind, input_path, prompt, revision=revision)


def run_parallel(jobs, workers=3):
    results = {}
    with ThreadPoolExecutor(workers) as ex:
        futs = {ex.submit(search, s, k): (s, k) for s, k in jobs}
        for f, key in futs.items():
            try:
                results[key] = f.result()
            except C.BudgetStop as e:
                print(f"BUDGET STOP during {key}: {e}", flush=True)
                results[key] = None
    return results


def cmd_sources(scenes):
    run_parallel([(s, "source") for s in scenes])


def cmd_first_edits(scenes):
    jobs = []
    for s in scenes:
        if not accepted_path(s, "source").exists():
            print(f"{s}: no accepted source yet")
            continue
        for kind in ("small", "medium"):
            if not M.existing_numbers(s, kind):
                jobs.append((s, kind))

    def one(job):
        s, kind = job
        r = M.make_edit(SCENES[s], kind, accepted_path(s, "source"), C.instruction(SCENES[s], kind))
        return f"{r['raw_file']} ${r['estimated_usd']}"
    with ThreadPoolExecutor(3) as ex:
        for line in ex.map(one, jobs):
            print(line, flush=True)


def cmd_additions(scenes):
    # small and medium for every scene (three files searched at once), then large where medium passed
    run_parallel([(s, k) for s in scenes for k in ("small", "medium")])
    run_parallel([(s, "large") for s in scenes if accepted_path(s, "medium").exists()])


A1_ORDER = ["SA01", "SA06", "SA02", "SA07", "SA03", "SA08", "SA04", "SA09", "SA05", "SA10"]


def cmd_search(scenes):
    """Scene by scene in A1's list order: small and medium searched together, then large once the medium
    is accepted; three workers, earlier scenes first. Stops every worker at the first budget stop."""
    import heapq
    rank = {s: i for i, s in enumerate(A1_ORDER)}
    kind_rank = {"small": 0, "medium": 1, "large": 2}
    heap = [(rank[s], kind_rank[k], s, k) for s in scenes for k in ("small", "medium")]
    for s in scenes:
        if accepted_path(s, "medium").exists():
            heap.append((rank[s], 2, s, "large"))
    heapq.heapify(heap)
    cond = threading.Condition()
    state = {"running": 0, "stop": None, "failed": set()}

    def worker():
        while True:
            with cond:
                while not heap and state["running"] and not state["stop"]:
                    cond.wait()
                if state["stop"] or not heap:
                    cond.notify_all()
                    return
                _, _, s, k = heapq.heappop(heap)
                if s in state["failed"]:
                    continue
                state["running"] += 1
            try:
                ok = search(s, k)
            except C.BudgetStop as e:
                ok = None
                with cond:
                    state["stop"] = str(e)
                print(f"BUDGET STOP during {s} {k}: {e}", flush=True)
            except Exception as e:  # noqa: BLE001 - stop rather than switch anything
                ok = None
                with cond:
                    state["stop"] = f"{s} {k}: {e}"
                print(f"STOPPED on error during {s} {k}: {e}", flush=True)
            with cond:
                state["running"] -= 1
                if ok and k == "medium":
                    heapq.heappush(heap, (rank[s], 2, s, "large"))
                if ok is False:
                    state["failed"].add(s)
                cond.notify_all()

    threads = [threading.Thread(target=worker) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    if state["stop"]:
        print("STOPPED:", state["stop"])
    if state["failed"]:
        print("Scenes failed after revision (reserve needed):", sorted(state["failed"]))


SUPERSEDED = C.OUT / "superseded_2026-10-27_bands"


def cmd_migrate(_):
    """Amendment of 27 October 2026: keep every judgment made under the absolute bands, then clear the addition
    judgments so that every candidate is re-judged in candidate order under the amended rules."""
    n = 0
    for f in sorted(C.CAND.glob("SA*_*_c[0-9][0-9].json")):
        r = json.loads(f.read_text(encoding="utf-8"))
        if r["kind"] == "source" or "judgment_under_bands" in r:
            continue
        r["judgment_under_bands"] = {"checks": r["checks"], "accepted": r["accepted"],
                                     "excluded": r.get("excluded"), "moved_utc": C.now()}
        if not r.get("excluded"):
            r["checks"], r["accepted"] = None, None
        f.write_text(json.dumps(r, indent=2, ensure_ascii=False), encoding="utf-8")
        n += 1
    SUPERSEDED.mkdir(exist_ok=True)
    moved = []
    for kind in ("small", "medium", "large"):
        for p in list(C.OUT.glob(f"SA*_{kind}.png")) + list(C.OUT.glob(f"SA*_{kind}.json")) + \
                list(C.OUT.glob(f"SA*_{kind}_mask.png")):
            shutil.move(str(p), SUPERSEDED / p.name)
            moved.append(p.name)
    st = load_status()
    old = {s: {k: v for k, v in d.items() if k != "source"} for s, d in st.items() if s != "superseded_under_bands"}
    new = {s: {k: v for k, v in d.items() if k == "source"} for s, d in st.items() if s != "superseded_under_bands"}
    new["superseded_under_bands"] = old
    STATUS.write_text(json.dumps(new, indent=2), encoding="utf-8")
    print(f"{n} addition records moved to judgment_under_bands; files moved to {SUPERSEDED.name}: {moved}")


def cmd_finish(scenes):
    """Per scene, in A1's list order, three scenes at a time: small, then medium (judged against the accepted
    small), then large (made from and judged against the accepted medium). A scene whose file fails after the
    revision is replaced by the reserve of its kind, whose source and three additions are made by the same rules."""
    order = list(scenes) if len(sys.argv) > 2 else [s for s in A1_ORDER if s in scenes]   # given order if named
    lock = threading.Lock()
    status = load_status()
    replaced = {s: v["reserve"]["replaced_by"] for s, v in status.items()
                if isinstance(v, dict) and isinstance(v.get("reserve"), dict)}
    used = {r: s for s, r in replaced.items()}
    stop = {"why": None}

    def chain(scene, with_source=False):
        for kind in (["source"] if with_source else []) + ["small", "medium", "large"]:
            if stop["why"]:
                return None
            if not search(scene, kind):
                return kind
        return "done"

    def run_scene(scene):
        try:
            if scene in replaced:                # a recorded replacement: make the reserve's four files
                print(f"{scene} is replaced by {replaced[scene]}; making the reserve's files", flush=True)
                res = chain(replaced[scene], with_source=True)
                if res not in ("done", None):
                    print(f"RESERVE {replaced[scene]} FAILED at {res}; no reserve of its kind is left", flush=True)
                return
            res = chain(scene)
            if res in ("done", None):
                return
            kind = "person" if SCENES[scene]["person"] else "no person"
            reserve = C.RESERVES[kind]
            with lock:
                if reserve in used:
                    print(f"{scene} failed at {res}; its reserve {reserve} is already used for {used[reserve]}",
                          flush=True)
                    return
                used[reserve] = scene
            set_status(scene, "reserve", {"replaced_by": reserve, "failed_file": res, "utc": C.now()})
            print(f"RESERVE {reserve} replaces {scene} (failed at {res})", flush=True)
            chain(reserve, with_source=True)
        except C.BudgetStop as e:
            stop["why"] = str(e)
            print(f"BUDGET STOP during {scene}: {e}", flush=True)
        except Exception as e:  # noqa: BLE001 - stop and report rather than switch anything
            stop["why"] = f"{scene}: {e}"
            print(f"STOPPED on error during {scene}: {e}", flush=True)

    with ThreadPoolExecutor(3) as ex:
        list(ex.map(run_scene, order))
    if stop["why"]:
        print("STOPPED:", stop["why"])


SUPERSEDED_UC = C.OUT / "superseded_2026-10-28_before_unchanged_check"
REJUDGE = {"migrate-unchanged": (SUPERSEDED_UC, "re-judged with the unchanged-elsewhere check"),
           "migrate-spill": (C.OUT / "superseded_2026-10-28_before_spill_check",
                             "re-judged with the spill check in place of the unchanged-elsewhere question"),
           "migrate-objects": (C.OUT / "superseded_2026-10-29_before_object_check",
                               "re-judged with the object-position check in place of the spill check")}


def cmd_migrate_unchanged(_, which="migrate-unchanged"):
    """Amendment of 28 October 2026 (unchanged-elsewhere check): keep every current judgment of the additions of the
    scenes in use, clear it so that every candidate is re-judged in order, and move the accepted additions aside."""
    status = load_status()
    replaced = {s for s, v in status.items() if isinstance(v, dict) and isinstance(v.get("reserve"), dict)}
    n = 0
    for f in sorted(C.CAND.glob("*_c[0-9][0-9].json")):
        r = json.loads(f.read_text(encoding="utf-8"))
        if r["kind"] == "source" or r["scene"] in replaced or r.get("excluded") or r["checks"] is None:
            continue
        r.setdefault("previous_judgments", []).append({"checks": r["checks"], "accepted": r["accepted"],
                                                        "moved_utc": C.now(), "why": REJUDGE[which][1]})
        r["checks"], r["accepted"] = None, None
        f.write_text(json.dumps(r, indent=2, ensure_ascii=False), encoding="utf-8")
        n += 1
    folder = REJUDGE[which][0]
    folder.mkdir(exist_ok=True)
    moved = []
    for scene in [s for s in SCENES if s not in replaced]:
        for kind in ("small", "medium", "large"):
            for suffix in (".png", ".json", "_mask.png"):
                q = C.OUT / f"{scene}_{kind}{suffix}"
                if q.exists():
                    shutil.move(str(q), folder / q.name)
                    moved.append(q.name)
    sup = status.setdefault("superseded_" + which.split("-", 1)[1], {})
    for scene in [s for s in SCENES if s not in replaced]:
        for kind in ("small", "medium", "large"):
            if kind in status.get(scene, {}):
                sup.setdefault(scene, {})[kind] = status[scene].pop(kind)
    STATUS.write_text(json.dumps(status, indent=2), encoding="utf-8")
    print(f"{n} judgments kept under previous_judgments; {len(moved)} files moved to {folder.name}")


def cmd_status(_):
    print(json.dumps(load_status(), indent=1))
    print(C.budget_state())


if __name__ == "__main__":
    cmd = sys.argv[1]
    scenes = sys.argv[2:] or C.MAIN_SCENES
    {"sources": cmd_sources, "first-edits": cmd_first_edits, "additions": cmd_additions,
     "search": cmd_search, "migrate": cmd_migrate, "migrate-unchanged": cmd_migrate_unchanged,
     "migrate-spill": lambda sc: cmd_migrate_unchanged(sc, "migrate-spill"),
     "migrate-objects": lambda sc: cmd_migrate_unchanged(sc, "migrate-objects"),
     "finish": cmd_finish, "status": cmd_status}[cmd](scenes)
    print(C.budget_state())
