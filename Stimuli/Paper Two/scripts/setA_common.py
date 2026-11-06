"""Shared pieces for the Set A images of Paper A (scenes SA01 to SA10, reserves SA-R1 and SA-R2).

- Reads every Set A prompt part and edit phrase from Docs/Paper Two/Paper_Two_Prompt_Bank.md,
  so the prompts sent are the bank's text exactly.
- Holds the fixed check questions and detector queries (written before any candidate was judged).
- Logs every paid API call to api_cost_ledger_setA.csv and refuses any call that could push the
  combined spending of both Paper Two ledgers past the hard limit.
- Sends the three kinds of OpenAI request: image generation, instruction edit, and one fixed
  yes-or-no question per call to the image-description model (GPT-5.1, reasoning off,
  temperature 0, the same model and settings as the Set B checks in auto_checks.py).

The API key is read from the environment variable OPENAI_API_KEY_AICOPYRIGHT and is never printed
or written anywhere.
"""

import base64
import csv
import fcntl
import hashlib
import io
import json
import os
import re
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from PIL import Image

HERE = Path(__file__).resolve().parent
STIM = HERE.parent                                   # Stimuli/Paper Two
PROJECT = HERE.parents[2]
BANK = PROJECT / "Docs" / "Paper Two" / "Paper_Two_Prompt_Bank.md"
OUT = STIM / "setA"
CAND = OUT / "candidates"
WEB = OUT / "web"
SHEETS = OUT / "contact_sheets"
LEDGER = STIM / "api_cost_ledger_setA.csv"
OTHER_LEDGER = STIM / "api_cost_ledger.csv"          # Paper B Study 1 images (other script)
THRESHOLDS = OUT / "thresholds.json"
MANIFEST = OUT / "manifest.csv"

IMAGE_MODEL = "gpt-image-2-2026-04-21"   # David's choice for Set A, 27 Oct 2026 (bank, "The models")
IMAGE_SETTINGS = {"size": "1536x1024", "quality": "high", "n": 1}
VISION_MODEL = "gpt-5.1-2025-11-13"
DETECTOR_MODEL = "google/owlv2-base-patch16-ensemble"
W, H = 1536, 1024

SOURCE_SUFFIX = "No text, lettering, signature, watermark, or frame."
# Acceptance condition for every file (bank, "How each prompt is sent", 27 October 2026).
TEXT_QUESTION = "Is the image free of any visible text, letters, numbers, signatures or watermarks?"


def realism_line():
    """The Set A realism line, read from the bank's "How each prompt is sent"."""
    text = BANK.read_text(encoding="utf-8")
    m = re.search(r"the Set A realism line, \"(.+?)\", then", text)
    if not m:
        raise ValueError("Set A realism line not found in the prompt bank")
    return m.group(1)
PARTS = ["Subject", "Composition", "Colors", "Lighting", "Style", "Mood", "Viewpoint", "Background"]
MAIN_SCENES = [f"SA{i:02d}" for i in range(1, 11)]
RESERVES = {"person": "SA-R1", "no person": "SA-R2"}
BANDS = {"small": (1.0, 2.0), "medium": (8.0, 12.0), "large": (25.0, 35.0)}   # superseded 27 Oct 2026
# Size rule since the amendment of 27 October 2026 (thresholds.json, amendments): within-scene ordering.
SMALL_MIN_PCT = 0.1          # small: masked area at least 0.1 percent of the image
MEDIUM_MIN_PCT = 0.5         # medium: at least 0.5 percent and at least RATIO x the accepted small's area
RATIO = 2.0                  # large: at least RATIO x the accepted medium's area
MAX_TRIES = 20

# Budget. HARD_LIMIT is David's stop across all Paper Two image work this quarter (both ledgers).
# SOFT_LIMIT is the target for this script's own ledger; the pipeline pauses there.
HARD_LIMIT = 175.00  # raised by David: 50 to 100 and 130 on 27 October, 160 on 28 October, 175 on 29 October 2026
SOFT_LIMIT = 113.00  # 113 on 29 Oct 2026 (combined cap $175 binds); Set A's own pause point (this ledger, all runs): 30, 60, 70, then 100 on 28 Oct 2026 so
                     # that David's combined HARD_LIMIT is the binding stop.
# Most a single call can cost, reserved before the call is sent (the actual cost is logged after).
RESERVE = {"generate": 0.40, "edit": 0.50, "vision": 0.02}
# Token prices in USD per token. Images: OpenAI pricing page, read 27 October 2026, the same for GPT Image 2
# and GPT Image 2.5: text input $5/M, image input $8/M, image output $30/M.
# Confirmed on OpenAI's pricing page the same day. Description model gpt-5.1: $1.25/M input,
# $10/M output (no cached-input discount assumed).
PRICE = {"img_text_in": 5e-6, "img_image_in": 8e-6, "img_out": 30e-6,
         "vis_in": 1.25e-6, "vis_out": 10e-6}
FALLBACK_COST = {"generate": 0.21, "edit": 0.21, "vision": 0.01}  # used only if usage is missing


# ---------------------------------------------------------------------------------------------
# The prompt bank
# ---------------------------------------------------------------------------------------------

def bank_sha256():
    return hashlib.sha256(BANK.read_bytes()).hexdigest()


def read_set_a():
    """Return {scene: {...}} for SA01 to SA10 and the two reserves, straight from the bank."""
    text = BANK.read_text(encoding="utf-8")
    set_a = text.split("## Set A:", 1)[1].split("## Set B:", 1)[0]
    scenes = {}
    realism = realism_line()
    for block in re.split(r"\n### ", set_a)[1:]:
        head = block.split("\n", 1)[0]
        m = re.match(r"(SA\d\d|SA-R\d)\. (.+?) \((.+?)\)", head)
        if not m:
            continue
        code, title, kind = m.groups()
        rows = dict(re.findall(r"^\| ([^|]+?) \| (.+?) \|$", block, flags=re.M))
        parts = [rows[p] for p in PARTS]
        large = rows["Large, added to the medium file"]
        large_elements = large.split(", and ")
        if len(large_elements) != 2:
            raise ValueError(f"{code}: cannot split the large phrase into two elements: {large}")
        scenes[code] = {
            "scene": code, "title": title,
            "person": not kind.startswith("no person"),
            "parts": parts,
            "prompt": " ".join(parts) + " " + realism + " " + SOURCE_SUFFIX,
            "small": rows["Small"], "medium": rows["Medium"], "large": large,
            "large_elements": large_elements,
            "rearrangement": rows["Rearrangement"],
        }
    expected = MAIN_SCENES + ["SA-R1", "SA-R2"]
    if sorted(scenes) != sorted(expected):
        raise ValueError(f"Expected scenes {expected}, found {sorted(scenes)}")
    return scenes


def instruction(scene, amount):
    """The bank's edit frames: "Add " + phrase + ". Change nothing else." """
    phrase = scene["large"] if amount == "large" else scene[amount]
    return "Add " + phrase + ". Change nothing else."


# ---------------------------------------------------------------------------------------------
# Fixed checks (written 27 October 2026, before any candidate was judged)
# ---------------------------------------------------------------------------------------------
# Source: the two objects the rearrangement moves (detector query + question each) and the open
# area where the additions go (question only). SA03's rearrangement moves the children and the
# kite; SA06's moves the two oars, so its detector query is "an oar" and its question asks for two.

SOURCE_CHECKS = {
    "SA01": {"objects": [("a teapot", "Is there a teapot on the table?"),
                         ("a cup", "Is there a cup on the table?")],
             "open": "Is the far end of the table bare, with nothing on it?"},
    "SA02": {"objects": [("a wooden crate", "Is there a wooden crate on the dock?"),
                         ("a coil of rope", "Is there a coil of rope on the dock?")],
             "open": "Is there an empty stretch of dock beside the man, with nothing on it?"},
    "SA03": {"objects": [("a child", "Are there two children?"),
                         ("a kite", "Is there a kite flying in the sky?")],
             "open": "Is there a wide band of empty sky in the middle of the image?"},
    "SA04": {"objects": [("a music stand", "Is there a music stand?"),
                         ("a wooden chair", "Is there an empty wooden chair?")],
             "open": "Is the rug in front of the man bare, with nothing on it?"},
    "SA05": {"objects": [("a crate", "Are there crates at one end of the counter?"),
                         ("a basket of lemons", "Is there a basket of lemons?")],
             "open": "Is one end of the counter bare and empty?"},
    "SA06": {"objects": [("an oar", "Are there two oars resting across the boat's seats?")],
             "open": "Is there an empty stretch of water, with no boats or birds on it?"},
    "SA07": {"objects": [("a clay jug", "Is there a clay jug on the table?"),
                         ("a loaf of bread", "Is there bread on the table?")],
             "open": "Is the right half of the table bare wood, with nothing on it?"},
    "SA08": {"objects": [("a hand cart", "Is there a hand cart?"),
                         ("a lamp post", "Is there a lamp post?")],
             "open": "Is the right side of the street open, with nothing standing in it?"},
    "SA09": {"objects": [("a wooden bench", "Is there a wooden bench?"),
                         ("a flowerpot", "Is there a clay flowerpot beside the bench?")],
             "open": "Is the path empty?"},
    "SA10": {"objects": [("a red buoy", "Is there a red buoy in the water?"),
                         ("a ship", "Is there a small ship on the horizon?")],
             "open": "Is there an open stretch of sea in the center of the image?"},  # amended 27 Oct 2026, see thresholds.json
    "SA-R1": {"objects": [("scissors", "Is there a pair of scissors on the table?"),
                          ("a spool of thread", "Is there a spool of thread on the table?")],
              "open": "Is the left end of the table bare, with nothing on it?"},
    "SA-R2": {"objects": [("a hay wagon", "Is there a hay wagon?"),
                          ("a ladder", "Is there a wooden ladder?")],
              "open": "Is the field to the right of the barn open, with nothing in it?"},
}

# Detector query for each added element (the element without its place). The description-model
# question for an added element is always "Does the image show " + the bank's phrase + "?".
ELEMENT_QUERIES = {
    "a spoon beside the cup": "a spoon",
    "a vase of daisies on the bare end of the table": "a vase of daisies",
    "a loaf of bread on a board": "a loaf of bread",
    "a cat asleep on a stool": "a cat",
    "a gull standing on the wooden crate": "a gull",
    "a dog lying on the empty dock to the man's right": "a dog",
    "a stack of barrels": "a barrel",
    "a lantern on a post": "a lantern",
    "a bird flying in the open sky": "a bird",
    "a dog running beside the two children": "a dog",
    "a picnic blanket with a basket": "a picnic blanket",
    "a second kite": "a kite",
    "a sheet of music on the floor": "a sheet of paper",
    "a dog asleep on the rug in front of the man": "a dog",
    "a side table with a vase": "a side table",
    "a candlestick": "a candlestick",
    "a single lemon on the ground": "a lemon",
    "a basket of eggs on the empty end of the counter": "a basket of eggs",
    "buckets of flowers": "a bucket of flowers",
    "a customer with a shopping bag": "a person carrying a bag",
    "a duck on the empty stretch of water": "a duck",
    "a heron standing in the shallow water": "a heron",
    "a second boat": "a boat",
    "a stand of reeds": "reeds",
    "a single walnut": "a walnut",
    "a pear on the bare right side of the table": "a pear",
    "a bowl of grapes": "a bowl of grapes",
    "a bird on a rooftop": "a bird",
    "a horse-drawn sled on the open right side of the street": "a horse-drawn sled",
    "a snowman": "a snowman",
    "a row of lanterns along the houses": "a lantern",
    "a butterfly over the path": "a butterfly",
    "a watering can on the path": "a watering can",
    "a wheelbarrow": "a wheelbarrow",
    "a birdbath": "a birdbath",
    "a single gull": "a gull",
    "a small sailboat in the open sea": "a sailboat",
    "a rowboat": "a rowboat",
    "a flare in the sky": "a flare",
    # Phrase amendments of 28 October 2026 (bank, "Phrase amendments"); the earlier phrases are kept above.
    "a large dog asleep on the rug in front of the man": "a dog",
    "a sailboat in the open sea": "a sailboat",
    "a large sailing ship in the open sea": "a sailing ship",      # second SA10 amendment, 28 Oct 2026
    "a tall wooden cupboard against the back wall": "a cupboard",
    "a rocking chair beside the table": "a rocking chair",
    "a teacup on a saucer beside the scissors": "a teacup",
    "a basket of folded cloth on the bare left end of the table": "a basket of folded cloth",
    "a dress form beside the table": "a dress form",
    "a cat asleep on the floor": "a cat",
    "a milk churn beside the hay wagon": "a milk churn",
    "a haystack on the open right side of the field": "a haystack",
    "a grazing horse": "a horse",
    "a stone water trough": "a water trough",
    # SA04 large amendment of 29 October 2026 (bank, "Phrase amendments")
    "a side table with a vase in the far right corner": "a side table",
    "a candlestick on the mantelpiece": "a candlestick",
    "a side table with a vase in the right foreground": "a side table",
    "a candlestick on the side table": "a candlestick",
}


def added_elements(scene, amount):
    """Elements a file must show. The large file shows the medium element and the two further ones."""
    if amount == "small":
        return [scene["small"]]
    if amount == "medium":
        return [scene["medium"]]
    return [scene["medium"]] + scene["large_elements"]


def element_question(phrase):
    """The fixed question for an added element: the amended list frozen in thresholds.json (27 October 2026),
    which drops 'empty', 'bare', 'open' and 'clear' where they describe the place before the edit."""
    t = json.loads(THRESHOLDS.read_text(encoding="utf-8"))
    if phrase in ((t.get("acceptance") or {}).get("element_questions") or {}):
        return t["acceptance"]["element_questions"][phrase]
    for a in t.get("amendments", []):        # questions added by a dated amendment
        if phrase in (a.get("questions") or {}):
            return a["questions"][phrase]
    raise RuntimeError("The amended element questions are missing from thresholds.json")


# ---------------------------------------------------------------------------------------------
# Ledger and budget guard
# ---------------------------------------------------------------------------------------------

LEDGER_FIELDS = ["utc_time", "model", "purpose", "tokens_or_images", "estimated_usd", "running_total_usd"]
_lock = threading.Lock()
_reserved = 0.0


class BudgetStop(RuntimeError):
    pass


def _num(x):
    try:
        return float(str(x).replace("$", "").strip())
    except ValueError:
        return None


def ledger_total(path):
    """Total spent in a ledger: the larger of the summed cost column and the last running total."""
    if not path.exists():
        return 0.0
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        return 0.0
    cols = list(rows[0].keys())
    cost_cols = [c for c in cols if c and ("usd" in c.lower() or "cost" in c.lower()) and "running" not in c.lower()]
    run_cols = [c for c in cols if c and "running" in c.lower()]
    summed = sum(v for r in rows for v in [_num(r.get(cost_cols[0], ""))] if v is not None) if cost_cols else 0.0
    running = 0.0
    if run_cols:
        vals = [_num(r.get(run_cols[0], "")) for r in rows]
        vals = [v for v in vals if v is not None]
        running = max(vals) if vals else 0.0
    return max(summed, running)


def budget_state():
    mine, other = ledger_total(LEDGER), ledger_total(OTHER_LEDGER)
    return {"mine": round(mine, 4), "other": round(other, 4), "combined": round(mine + other, 4)}


def reserve(kind, soft_limit=SOFT_LIMIT):
    """Reserve the most this call can cost; raise BudgetStop if it could pass a limit."""
    global _reserved
    need = RESERVE[kind]
    with _lock:
        s = budget_state()
        if s["combined"] + _reserved + need > HARD_LIMIT:
            raise BudgetStop(f"Hard stop: combined spending {s['combined']:.2f} + in flight {_reserved:.2f} "
                             f"+ next call {need:.2f} would pass ${HARD_LIMIT:.2f}")
        if s["mine"] + _reserved + need > soft_limit:
            raise BudgetStop(f"Soft stop: Set A spending {s['mine']:.2f} + in flight {_reserved:.2f} "
                             f"+ next call {need:.2f} would pass ${soft_limit:.2f}")
        _reserved += need
    return need


def release_and_log(need, model, purpose, tokens_or_images, usd):
    """Log one call (after it returns, even if it failed after being billed) and free its reservation."""
    global _reserved
    with _lock:
        _reserved -= need
        new = not LEDGER.exists()
        with open(LEDGER, "a", newline="", encoding="utf-8") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX)
            total = ledger_total(LEDGER) + usd
            w = csv.DictWriter(fh, fieldnames=LEDGER_FIELDS)
            if new:
                w.writeheader()
            w.writerow({"utc_time": now(), "model": model, "purpose": purpose,
                        "tokens_or_images": tokens_or_images, "estimated_usd": f"{usd:.4f}",
                        "running_total_usd": f"{total:.4f}"})
            fcntl.flock(fh, fcntl.LOCK_UN)


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------------------------------------
# OpenAI requests
# ---------------------------------------------------------------------------------------------

def _key():
    return os.environ["OPENAI_API_KEY_AICOPYRIGHT"]


def _image_cost(usage, kind):
    if not usage:
        return FALLBACK_COST[kind], "usage missing; fallback estimate"
    det = usage.get("input_tokens_details") or {}
    text_in = det.get("text_tokens", usage.get("input_tokens", 0) if kind == "generate" else 0)
    img_in = det.get("image_tokens", 0)
    out = usage.get("output_tokens", 0)
    usd = text_in * PRICE["img_text_in"] + img_in * PRICE["img_image_in"] + out * PRICE["img_out"]
    return usd, f"text_in={text_in}; image_in={img_in}; image_out={out}"


def _post_image(kind, purpose, send):
    """Send one image request with the budget guard; return (png bytes, usage dict, usd)."""
    need = reserve(kind)
    usd, tokens, d = 0.0, "no response", None
    try:
        r = send()
        try:
            d = r.json()
        except ValueError:
            d = {"error": {"message": f"HTTP {r.status_code}, body not JSON"}}
        if "error" in d and d["error"]:
            tokens = "error: no image billed"
            raise RuntimeError(str(d["error"].get("message", d["error"]))[:400])
        usd, tokens = _image_cost(d.get("usage"), kind)
        return base64.b64decode(d["data"][0]["b64_json"]), d.get("usage") or {}, usd
    finally:
        release_and_log(need, IMAGE_MODEL, purpose, tokens, usd)


def generate_image(prompt, purpose):
    body = {"model": IMAGE_MODEL, "prompt": prompt, **IMAGE_SETTINGS}
    return _post_image("generate", purpose, lambda: requests.post(
        "https://api.openai.com/v1/images/generations", json=body,
        headers={"Authorization": f"Bearer {_key()}"}, timeout=600))


def edit_image(png_bytes, prompt, purpose):
    """Instruction edit: POST /v1/images/edits, multipart form, one input image in image[], no mask."""
    data = {"model": IMAGE_MODEL, "prompt": prompt, "size": IMAGE_SETTINGS["size"],
            "quality": IMAGE_SETTINGS["quality"], "n": str(IMAGE_SETTINGS["n"])}
    files = [("image[]", ("input.png", png_bytes, "image/png"))]
    return _post_image("edit", purpose, lambda: requests.post(
        "https://api.openai.com/v1/images/edits", data=data, files=files,
        headers={"Authorization": f"Bearer {_key()}"}, timeout=600))


VISION_INSTRUCTION = "Look at the image and answer the question with exactly one word: yes or no."
VISION_SETTINGS = {"reasoning": {"effort": "none"}, "temperature": 0, "max_output_tokens": 16}


def ask_yes_no(img, question, purpose):
    """One fixed yes-or-no question to the description model (GPT-5.1, reasoning off, temperature 0).

    The reply must be exactly yes or no (case, spaces and a final full stop ignored). Any other reply
    is asked again, at most three calls in all, and is then recorded as "invalid" (not confirmed).
    Returns {"question", "answer", "raw", "model_reported", "calls"}.
    """
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    body = {"model": VISION_MODEL, **VISION_SETTINGS,
            "input": [{"role": "user", "content": [
                {"type": "input_text", "text": f"{VISION_INSTRUCTION}\n\nQuestion: {question}"},
                {"type": "input_image", "image_url": f"data:image/png;base64,{b64}", "detail": "high"}]}]}
    raws, reported, calls = [], "", 0
    for attempt in range(3):
        need = reserve("vision")
        usd, tokens = 0.0, "no reply"
        calls += 1
        try:
            d = requests.post("https://api.openai.com/v1/responses", json=body,
                              headers={"Authorization": f"Bearer {_key()}"}, timeout=180).json()
            if d.get("error"):
                tokens = "API error; not billed"
                raws.append(f"<error: {str(d['error'].get('message', d['error']))[:200]}>")
                if "temperature" in str(d["error"]).lower() or "model" in str(d["error"].get("param", "")):
                    raise RuntimeError(f"description model call rejected: {d['error']}")
                time.sleep(4 * (attempt + 1))
                continue
            u = d.get("usage") or {}
            reported = d.get("model", VISION_MODEL)
            usd = u.get("input_tokens", 0) * PRICE["vis_in"] + u.get("output_tokens", 0) * PRICE["vis_out"]
            tokens = f"in={u.get('input_tokens', 0)}; out={u.get('output_tokens', 0)}"
            text = "".join(c.get("text", "") for o in d.get("output", []) if o.get("type") == "message"
                           for c in o.get("content", []))
            raws.append(text)
            t = text.strip().lower().rstrip(".").strip()
            if t in ("yes", "no"):
                return {"question": question, "answer": t, "raw": raws, "model_reported": reported, "calls": calls}
        except requests.RequestException as e:
            usd, tokens = RESERVE["vision"], f"no reply ({type(e).__name__}); charged the reserve"
            raws.append(f"<no reply: {type(e).__name__}>")
            time.sleep(4 * (attempt + 1))
        finally:
            release_and_log(need, VISION_MODEL, purpose, tokens, usd)
    return {"question": question, "answer": "invalid", "raw": raws, "model_reported": reported, "calls": calls}


# "Unchanged elsewhere" check (amendment of 28 October 2026): the input and the composited file are shown
# together, labelled first and second, with one fixed question.
PAIR_INSTRUCTION = "Look at the two images and answer the question with exactly one word: yes or no."


def unchanged_question(scene, kind):
    """'Apart from <the added element or elements, named as in the instruction>, is everything that was in the
    first image still in the same place and unchanged in the second image?' For large: the medium element and
    the two further elements."""
    named = scene[kind] if kind != "large" else scene["medium"] + ", " + scene["large"]
    return (f"Apart from {named}, is everything that was in the first image still in the same place and "
            f"unchanged in the second image?")


def ask_yes_no_pair(first, second, question, purpose):
    """One yes-or-no question about two images in one request (GPT-5.1, reasoning off, temperature 0)."""
    def b64(img):
        buf = io.BytesIO()
        img.convert("RGB").save(buf, "PNG")
        return base64.b64encode(buf.getvalue()).decode()
    body = {"model": VISION_MODEL, **VISION_SETTINGS,
            "input": [{"role": "user", "content": [
                {"type": "input_text", "text": "First image:"},
                {"type": "input_image", "image_url": f"data:image/png;base64,{b64(first)}", "detail": "high"},
                {"type": "input_text", "text": "Second image:"},
                {"type": "input_image", "image_url": f"data:image/png;base64,{b64(second)}", "detail": "high"},
                {"type": "input_text", "text": f"{PAIR_INSTRUCTION}\n\nQuestion: {question}"}]}]}
    raws, reported, calls = [], "", 0
    for attempt in range(3):
        need = reserve("vision")
        usd, tokens = 0.0, "no reply"
        calls += 1
        try:
            d = requests.post("https://api.openai.com/v1/responses", json=body,
                              headers={"Authorization": f"Bearer {_key()}"}, timeout=180).json()
            if d.get("error"):
                tokens = "API error; not billed"
                raws.append(f"<error: {str(d['error'].get('message', d['error']))[:200]}>")
                if "temperature" in str(d["error"]).lower() or "model" in str(d["error"].get("param", "")):
                    raise RuntimeError(f"description model call rejected: {d['error']}")
                time.sleep(4 * (attempt + 1))
                continue
            u = d.get("usage") or {}
            reported = d.get("model", VISION_MODEL)
            usd = u.get("input_tokens", 0) * PRICE["vis_in"] + u.get("output_tokens", 0) * PRICE["vis_out"]
            tokens = f"in={u.get('input_tokens', 0)}; out={u.get('output_tokens', 0)}"
            text = "".join(c.get("text", "") for o in d.get("output", []) if o.get("type") == "message"
                           for c in o.get("content", []))
            raws.append(text)
            t = text.strip().lower().rstrip(".").strip()
            if t in ("yes", "no"):
                return {"question": question, "answer": t, "raw": raws, "model_reported": reported, "calls": calls,
                        "images": "first = the edit's input, second = the composited file"}
        except requests.RequestException as e:
            usd, tokens = RESERVE["vision"], f"no reply ({type(e).__name__}); charged the reserve"
            raws.append(f"<no reply: {type(e).__name__}>")
            time.sleep(4 * (attempt + 1))
        finally:
            release_and_log(need, VISION_MODEL, purpose, tokens, usd)
    return {"question": question, "answer": "invalid", "raw": raws, "model_reported": reported, "calls": calls,
            "images": "first = the edit's input, second = the composited file"}


# ---------------------------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------------------------

def load_rgb(path):
    return Image.open(path).convert("RGB")


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_png(img, path):
    img.save(path, "PNG")
    return path
