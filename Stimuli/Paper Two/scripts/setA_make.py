"""Make Set A candidates: one call to the image model per candidate, numbered in the order made.

Each candidate is saved in setA/candidates/ as <scene>_<kind>_c<NN>.png with a .json record beside
it (prompt or instruction, input file and its checksum, model, settings, time, tokens, cost). For an
edit the model's raw output is saved as <scene>_<kind>_c<NN>_raw.png; the checks (setA_judge.py)
later write the composited file and masks. Nothing here judges a candidate.
"""

import io
import json
import re
import time

from PIL import Image

import setA_common as C


def cand_stem(scene, kind, n):
    return f"{scene}_{kind}_c{n:02d}"


def existing_numbers(scene, kind):
    pat = re.compile(rf"^{re.escape(scene)}_{kind}_c(\d\d)\.json$")
    return sorted(int(m.group(1)) for p in C.CAND.glob(f"{scene}_{kind}_c*.json") if (m := pat.match(p.name)))


def record_path(scene, kind, n):
    return C.CAND / (cand_stem(scene, kind, n) + ".json")


def read_record(scene, kind, n):
    return json.loads(record_path(scene, kind, n).read_text(encoding="utf-8"))


def write_record(rec):
    record_path(rec["scene"], rec["kind"], rec["candidate"]).write_text(
        json.dumps(rec, indent=2, ensure_ascii=False), encoding="utf-8")


def _call_with_retries(fn, *args):
    """Up to three attempts for errors that are not the checks (network, server). BudgetStop passes through."""
    errors = []
    for attempt in range(3):
        try:
            return fn(*args), errors
        except C.BudgetStop:
            raise
        except Exception as e:  # noqa: BLE001
            errors.append(f"{C.now()} {str(e)[:300]}")
            time.sleep(10 * (attempt + 1))
    raise RuntimeError("Three failed requests: " + " | ".join(errors))


def make_source(scene, prompt, revision=0, note=""):
    C.CAND.mkdir(parents=True, exist_ok=True)
    n = (existing_numbers(scene["scene"], "source") or [0])[-1] + 1
    stem = cand_stem(scene["scene"], "source", n)
    t = time.time()
    (png, usage, usd), errors = _call_with_retries(C.generate_image, prompt, f"Set A source {stem}")
    img = Image.open(io.BytesIO(png))
    path = C.CAND / f"{stem}.png"
    path.write_bytes(png)
    rec = {"scene": scene["scene"], "kind": "source", "candidate": n, "revision": revision,
           "file": path.name, "prompt_or_instruction": prompt, "input_file": "", "input_sha256": "",
           "model": C.IMAGE_MODEL, "endpoint": "POST /v1/images/generations (JSON)",
           "settings": dict(C.IMAGE_SETTINGS, seed="none (model accepts no seed)"),
           "created_utc": C.now(), "seconds": round(time.time() - t, 1), "usage": usage,
           "estimated_usd": round(usd, 4), "width": img.width, "height": img.height,
           "sha256": C.sha256_file(path), "request_errors": errors, "note": note,
           "checks": None, "accepted": None}
    write_record(rec)
    return rec


def make_edit(scene, kind, input_path, instr, revision=0, note=""):
    C.CAND.mkdir(parents=True, exist_ok=True)
    n = (existing_numbers(scene["scene"], kind) or [0])[-1] + 1
    stem = cand_stem(scene["scene"], kind, n)
    src_bytes = input_path.read_bytes()
    t = time.time()
    (png, usage, usd), errors = _call_with_retries(C.edit_image, src_bytes, instr, f"Set A {kind} edit {stem}")
    img = Image.open(io.BytesIO(png))
    raw = C.CAND / f"{stem}_raw.png"
    raw.write_bytes(png)
    rec = {"scene": scene["scene"], "kind": kind, "candidate": n, "revision": revision,
           "file": f"{stem}.png", "raw_file": raw.name, "prompt_or_instruction": instr,
           "input_file": input_path.name, "input_sha256": C.sha256_file(input_path),
           "model": C.IMAGE_MODEL,
           "endpoint": "POST /v1/images/edits (multipart form; one input image in image[]; no mask)",
           "settings": dict(C.IMAGE_SETTINGS, seed="none (model accepts no seed)"),
           "created_utc": C.now(), "seconds": round(time.time() - t, 1), "usage": usage,
           "estimated_usd": round(usd, 4), "width": img.width, "height": img.height,
           "raw_sha256": C.sha256_file(raw), "request_errors": errors, "note": note,
           "checks": None, "accepted": None}
    write_record(rec)
    return rec
