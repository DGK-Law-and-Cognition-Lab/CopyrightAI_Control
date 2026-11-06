"""Finish Set A: verify pixel identity, write the manifest, the web copies and the contact sheets.

    python3 setA_finalize.py

- Pixel identity, checked on the saved PNGs: each accepted small and medium file is identical to the
  accepted source at every pixel outside its mask; the large file is identical to the accepted medium
  file outside its own mask, and to the source outside the union of the medium's and its own masks.
- manifest.csv: one row per candidate and one per accepted file (scene, file, prompt or instruction,
  model and version, settings, time, every check question and answer, detector boxes and scores,
  masked area, thresholds, accepted or not). Lists and dicts are JSON inside their cells.
- web/: JPEG copies of the accepted files, 1536 x 1024, optimized and progressive, at quality 85 when all
  four of a scene's files are then at most 400 KB; otherwise at the highest quality in steps of 5 at which
  all four are, the same quality for every file of the scene (a source and its additions are shown side
  by side, so they are compressed alike). The quality used is in accepted_summary.json.
- contact_sheets/: one sheet per scene, source, small, medium and large side by side.
Makes no API call.
"""

import csv
import json

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import setA_common as C
import setA_checks as K

KINDS = ["source", "small", "medium", "large"]
FIELDS = ["row_type", "scene", "kind", "file", "candidate", "revision", "accepted", "excluded",
          "prompt_or_instruction", "input_file", "input_sha256", "sha256", "raw_file", "model", "endpoint",
          "settings", "created_utc", "seconds", "usage", "estimated_usd",
          "detector", "detector_score_cut", "detector_pass", "detections",
          "description_model", "description_settings", "description_pass", "questions_and_answers",
          "difference_threshold", "speck_px", "widening_px", "change_area_vs_input_pct", "masked_area_pct",
          "widened_area_pct", "size_rule", "size_min_pct", "size_pass", "object_position_pass", "object_position",
          "spill_pct_superseded", "spill_cut_pct_superseded", "spill_pass_superseded",
          "unchanged_question_superseded", "unchanged_answer_superseded",
          "previous_judgments", "identical_to_input_outside_mask",
          "identical_to_source_outside_edit_region", "mask_file", "pixel_identity_verified",
          "band_pct_under_bands", "band_pass_under_bands", "description_pass_under_bands",
          "questions_and_answers_under_bands", "accepted_under_bands", "excluded_under_bands",
          "superseded_checks", "request_errors", "note"]


def j(x):
    return json.dumps(x, ensure_ascii=False) if x not in (None, "") else ""


def row_from_record(rec, row_type, file_name=None, mask_file="", verified=""):
    c = rec.get("checks") or {}
    old = rec.get("judgment_under_bands") or {}
    ob = old.get("checks") or {}
    stem = rec["file"][:-4]
    if row_type == "candidate" and rec["kind"] != "source" and (C.CAND / f"{stem}_mask.png").exists():
        mask_file = f"candidates/{stem}_mask.png"
    return {
        "row_type": row_type, "scene": rec["scene"], "kind": rec["kind"],
        "file": file_name or f"candidates/{rec['file']}", "candidate": rec["candidate"],
        "revision": rec["revision"], "accepted": rec.get("accepted"), "excluded": rec.get("excluded", ""),
        "prompt_or_instruction": rec["prompt_or_instruction"], "input_file": rec.get("input_file", ""),
        "input_sha256": rec.get("input_sha256", ""), "sha256": rec.get("sha256", ""),
        "raw_file": f"candidates/{rec['raw_file']}" if rec.get("raw_file") else "",
        "model": rec["model"], "endpoint": rec.get("endpoint", ""), "settings": j(rec.get("settings")),
        "created_utc": rec["created_utc"], "seconds": rec.get("seconds", ""), "usage": j(rec.get("usage")),
        "estimated_usd": rec.get("estimated_usd", ""),
        "detector": c.get("detector", ""), "detector_score_cut": c.get("detector_score_cut", ""),
        "detector_pass": c.get("detector_pass", ""), "detections": j(c.get("detections")),
        "description_model": c.get("description_model", ""),
        "description_settings": j(C.VISION_SETTINGS) if c else "",
        "description_pass": c.get("description_pass", ""),
        "questions_and_answers": j([{"question": q["question"], "answer": q["answer"]} for q in c.get("questions", [])]),
        "difference_threshold": c.get("difference_threshold", ""), "speck_px": c.get("speck_px", ""),
        "widening_px": c.get("widening_px", ""), "change_area_vs_input_pct": c.get("change_area_vs_input_pct", ""),
        "masked_area_pct": c.get("masked_area_pct", ""), "widened_area_pct": c.get("widened_area_pct", ""),
        "size_rule": c.get("size_rule", ""), "size_min_pct": c.get("size_min_pct", ""),
        "size_pass": c.get("size_pass", ""),
        "object_position_pass": c.get("object_position_pass", ""),
        "object_position": j([{k: o.get(k) for k in ("object", "in_input", "iou", "pass")}
                              for o in (c.get("object_position") or {}).get("objects", [])]) if c.get("object_position") else "",
        "spill_pct_superseded": next(((pj.get("checks") or {}).get("spill", {}).get("spill_pct", "")
                                      for pj in reversed(rec.get("previous_judgments", []))
                                      if (pj.get("checks") or {}).get("spill")), ""),
        "spill_cut_pct_superseded": next(((pj.get("checks") or {}).get("spill", {}).get("cut_pct", "")
                                          for pj in reversed(rec.get("previous_judgments", []))
                                          if (pj.get("checks") or {}).get("spill")), ""),
        "spill_pass_superseded": next(((pj.get("checks") or {}).get("spill_pass", "")
                                       for pj in reversed(rec.get("previous_judgments", []))
                                       if (pj.get("checks") or {}).get("spill")), ""),
        "unchanged_question_superseded": next(((pj.get("checks") or {}).get("unchanged", {}).get("question", "")
                                               for pj in reversed(rec.get("previous_judgments", []))
                                               if (pj.get("checks") or {}).get("unchanged")), ""),
        "unchanged_answer_superseded": next(((pj.get("checks") or {}).get("unchanged", {}).get("answer", "")
                                             for pj in reversed(rec.get("previous_judgments", []))
                                             if (pj.get("checks") or {}).get("unchanged")), ""),
        "previous_judgments": j([{"why": pj.get("why"), "accepted": pj.get("accepted"),
                                  "masked_area_pct": (pj.get("checks") or {}).get("masked_area_pct"),
                                  "size_pass": (pj.get("checks") or {}).get("size_pass"),
                                  "detector_pass": (pj.get("checks") or {}).get("detector_pass"),
                                  "description_pass": (pj.get("checks") or {}).get("description_pass"),
                                  "unchanged_answer": ((pj.get("checks") or {}).get("unchanged") or {}).get("answer"),
                                  "spill_pct": ((pj.get("checks") or {}).get("spill") or {}).get("spill_pct")}
                                 for pj in rec.get("previous_judgments", [])]) if rec.get("previous_judgments") else "",
        "band_pct_under_bands": j(ob.get("band_pct")), "band_pass_under_bands": ob.get("band_pass", ""),
        "description_pass_under_bands": ob.get("description_pass", ""),
        "questions_and_answers_under_bands": j([{"question": q["question"], "answer": q["answer"]}
                                                for q in ob.get("questions", [])]) if ob else "",
        "accepted_under_bands": old.get("accepted", "") if old else "",
        "excluded_under_bands": old.get("excluded") or "" if old else "",
        "identical_to_input_outside_mask": c.get("identical_to_input_outside_mask", ""),
        "identical_to_source_outside_edit_region": c.get("identical_to_source_outside_edit_region", ""),
        "mask_file": mask_file, "pixel_identity_verified": verified,
        "superseded_checks": j(rec.get("superseded_checks")), "request_errors": j(rec.get("request_errors")),
        "note": rec.get("note", ""),
    }


def verify(scene):
    """Pixel identity of the accepted files of one scene, from the saved PNGs."""
    out = {}
    p = {k: C.OUT / f"{scene}_{k}.png" for k in KINDS}
    if not p["source"].exists():
        return out
    src = K.arr(C.load_rgb(p["source"]))
    for k in ("small", "medium"):
        if p[k].exists():
            f = K.arr(C.load_rgb(p[k]))
            m = K.load_mask(C.OUT / f"{scene}_{k}_mask.png")
            ok, n = K.identical_outside(f, src, m)
            out[k] = {"identical_to_source_outside_mask": ok, "pixels_differing": n}
    if p["large"].exists():
        f = K.arr(C.load_rgb(p["large"]))
        med = K.arr(C.load_rgb(p["medium"]))
        ml = K.load_mask(C.OUT / f"{scene}_large_mask.png")
        mm = K.load_mask(C.OUT / f"{scene}_medium_mask.png")
        ok1, n1 = K.identical_outside(f, med, ml)
        ok2, n2 = K.identical_outside(f, src, ml | mm)
        out["large"] = {"identical_to_medium_outside_large_mask": ok1, "pixels_differing_from_medium": n1,
                        "identical_to_source_outside_both_masks": ok2, "pixels_differing_from_source": n2}
    return out


def font(size):
    for name in ("/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def contact_sheet(scene, info):
    tw, th, pad, top = 768, 512, 12, 70
    sheet = Image.new("RGB", (4 * tw + 5 * pad, th + top + pad), "white")
    d = ImageDraw.Draw(sheet)
    d.text((pad, 8), f"{scene}  {C.read_set_a()[scene]['title']}", fill="black", font=font(26))
    for i, k in enumerate(KINDS):
        x = pad + i * (tw + pad)
        path = C.OUT / f"{scene}_{k}.png"
        label = k
        if k in info:
            label += f"  (c{info[k]['candidate']:02d}" + (f", {info[k]['area']}%" if k != "source" else "") + ")"
        d.text((x, 42), label, fill="black", font=font(20))
        if path.exists():
            sheet.paste(C.load_rgb(path).resize((tw, th)), (x, top))
        else:
            d.rectangle([x, top, x + tw, top + th], outline="gray")
            d.text((x + 20, top + 20), "no accepted file", fill="gray", font=font(20))
    C.SHEETS.mkdir(exist_ok=True)
    sheet.save(C.SHEETS / f"{scene}_contact_sheet.jpg", quality=85)


WEB_LIMIT_KB = 400


def web_quality(scene):
    """Highest JPEG quality (85, 80, ...) at which every accepted file of the scene is at most 400 KB."""
    import io
    imgs = [C.load_rgb(C.OUT / f"{scene}_{k}.png") for k in KINDS if (C.OUT / f"{scene}_{k}.png").exists()]
    for q in range(85, 39, -5):
        sizes = []
        for img in imgs:
            buf = io.BytesIO()
            img.save(buf, "JPEG", quality=q, optimize=True, progressive=True)
            sizes.append(buf.tell() / 1024)
        if max(sizes) <= WEB_LIMIT_KB:
            return q
    return 40


def rule_rows():
    """The rules, as applied, recorded in the manifest: one row per rule in thresholds.json (with the frozen
    number where the rule sets one), each amendment, and the web-copy rule."""
    t = K.load_thresholds()
    out = []

    def add(name, text):
        r = {f: "" for f in FIELDS}
        r.update(row_type="rule", file=name, note=text)
        out.append(r)
    for section in ("detector", "change_mask", "acceptance", "rescue"):
        for key, text in t[section].items():
            add(f"{section}.{key}", text)
    for key, v in t["numbers"].items():
        add(f"number.{key}", f"{v['value']} (computed {v['computed_utc']} by its rule)")
    for a in t.get("amendments", []):
        parts = [a.get("utc", "")]
        if "old" in a:
            parts.append(f"old: {json.dumps(a['old'], ensure_ascii=False)}; new: {json.dumps(a['new'], ensure_ascii=False)}")
        for key in ("rule", "reason", "consequences"):
            if a.get(key):
                parts.append(f"{key}: {a[key]}")
        if a.get("questions"):
            parts.append("questions: " + json.dumps(a["questions"], ensure_ascii=False))
        add(f"amendment: {a['what']}", " | ".join(parts))
    status = json.loads((C.OUT / "status.json").read_text(encoding="utf-8")) if (C.OUT / "status.json").exists() else {}
    for scene, v in status.items():
        if isinstance(v, dict) and isinstance(v.get("reserve"), dict):
            r = v["reserve"]
            add(f"reserve: {scene} replaced by {r['replaced_by']}",
                f"{r.get('utc', '')}: {scene} failed at its {r.get('failed_file')} file; {r['replaced_by']} takes its "
                f"place in every A1 list. Decided by: {r.get('decided_by', 'the rescue rule')}. Evidence: "
                f"{r.get('evidence', '')} {r.get('note', '')}".strip())
    add("web_copies", "JPEG 1536 x 1024, optimized, progressive, quality 85 when all of a scene's accepted files are "
        "then at most 400 KB; otherwise the highest quality in steps of 5 at which all are, the same for every "
        "file of the scene. The two targets given (quality 85; under about 400 KB) cannot both hold for six of "
        "the ten scenes.")
    return out


def main():
    scenes = list(C.read_set_a())
    rows, summary = [], []
    for scene in scenes:
        for kind in KINDS:
            for f in sorted(C.CAND.glob(f"{scene}_{kind}_c*.json")):
                rows.append(row_from_record(json.loads(f.read_text(encoding="utf-8")), "candidate"))
    C.WEB.mkdir(exist_ok=True)
    status_all = json.loads((C.OUT / "status.json").read_text(encoding="utf-8")) if (C.OUT / "status.json").exists() else {}
    for scene in scenes:
        ver = verify(scene)
        info = {}
        quality = web_quality(scene) if (C.OUT / f"{scene}_source.png").exists() else None
        for kind in KINDS:
            jp = C.OUT / f"{scene}_{kind}.json"
            if not jp.exists():
                continue
            rec = json.loads(jp.read_text(encoding="utf-8"))
            mask = f"{scene}_{kind}_mask.png" if kind != "source" else ""
            v = ver.get(kind, {})
            verified = all(val for key, val in v.items() if key.startswith("identical")) if v else ("n/a" if kind == "source" else "")
            row = row_from_record(rec, "accepted", f"{scene}_{kind}.png", mask, verified)
            rep = (status_all.get(scene, {}).get("reserve") or {}).get("replaced_by")
            if rep:
                row["note"] = (row["note"] + " " if row["note"] else "") + f"Not used in A1: {scene} is replaced by {rep}."
            rows.append(row)
            img = C.load_rgb(C.OUT / f"{scene}_{kind}.png")
            web = C.WEB / f"{scene}_{kind}.jpg"
            img.save(web, "JPEG", quality=quality, optimize=True, progressive=True)
            info[kind] = {"candidate": rec["candidate"], "area": (rec.get("checks") or {}).get("masked_area_pct")}
            summary.append({"scene": scene, "kind": kind, "candidate": rec["candidate"], "revision": rec["revision"],
                            "masked_area_pct": info[kind]["area"], "pixel_identity": v,
                            "web_quality": quality, "web_kb": round(web.stat().st_size / 1024, 1)})
        if info:
            contact_sheet(scene, info)
    rows = rule_rows() + rows
    with open(C.MANIFEST, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    areas = {(x["scene"], x["kind"]): x["masked_area_pct"] for x in summary}
    status = json.loads((C.OUT / "status.json").read_text(encoding="utf-8")) if (C.OUT / "status.json").exists() else {}
    ratios = []
    for scene in scenes:
        sm, md, lg = (areas.get((scene, k)) for k in ("small", "medium", "large"))
        if sm is None and md is None and lg is None:
            continue
        ratios.append({"scene": scene, "small_pct": sm, "medium_pct": md, "large_pct": lg,
                       "medium_to_small": round(md / sm, 2) if sm and md else None,
                       "large_to_medium": round(lg / md, 2) if md and lg else None,
                       "replaced_by_reserve": (status.get(scene, {}).get("reserve") or {}).get("replaced_by")})
    a1 = []
    for scene in C.MAIN_SCENES:
        src = (status.get(scene, {}).get("reserve") or {}).get("replaced_by") or scene
        for kind in KINDS:
            hit = [x for x in summary if x["scene"] == src and x["kind"] == kind]
            a1.append({"a1_scene": scene, "files_from": src, "kind": kind,
                       "file": f"{src}_{kind}.png" if hit else None,
                       "candidate": hit[0]["candidate"] if hit else None,
                       "masked_area_pct": hit[0]["masked_area_pct"] if hit else None})
    out = {"a1_places": a1, "accepted_files": summary, "ratios_by_scene": ratios,
           "reserves_used": {s: v["reserve"] for s, v in status.items()
                             if isinstance(v, dict) and "reserve" in v}}
    (C.OUT / "accepted_summary.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    bad = [s for s in summary if s["pixel_identity"] and not all(v for k, v in s["pixel_identity"].items()
                                                                  if k.startswith("identical"))]
    print(f"{len(rows)} manifest rows; {len(summary)} accepted files; identity failures: {bad or 'none'}")
    big = [s for s in summary if s["web_kb"] > WEB_LIMIT_KB]
    print("web copies over 400 KB:", [(s['scene'], s['kind'], s['web_kb']) for s in big] or "none")


if __name__ == "__main__":
    main()
