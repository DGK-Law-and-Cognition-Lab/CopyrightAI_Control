"""Generate every prompt-bank scene on six image models for the model comparison.

Models: three from Google (Nano Banana 2.1, Nano Banana Pro, Nano Banana 2) and
three from OpenAI (GPT Image 2.5 Sunburst, GPT Image 2.5 Flare, GPT Image 2).
Two candidates per scene per model, all from the current prompt bank, saved to
model_comparison_2026-10-15/images with one manifest row per image.

Run from a shell that has loaded ~/.zshrc:
    python3 generate_model_comparison.py
"""

import base64
import csv
import hashlib
import io
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import requests
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_first_look import read_prompts  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "model_comparison_2026-10-15"
IMG_DIR = OUT / "images"
SEEDS = [1001, 1002]

MODELS = {
    "nb21": ("google", "gemini-nano-banana-2.1"),
    "nbpro": ("google", "gemini-3-pro-image"),
    "nb2": ("google", "gemini-3.1-flash-image"),
    "gpt25s": ("openai", "gpt-image-2.5-sunburst-2026-09-08"),
    "gpt25f": ("openai", "gpt-image-2.5-flare-2026-09-08"),
    "gpt2": ("openai", "gpt-image-2-2026-04-21"),
}


def call_google(model, prompt, seed):
    key = os.environ["GEMINI_API_KEY_AICOPYRIGHT"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    config = {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "3:2"}, "seed": seed}
    for attempt_config, note in ((config, f"seed {seed}"),
                                 ({k: v for k, v in config.items() if k != "seed"}, "seed not accepted")):
        body = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": attempt_config}
        d = requests.post(url, json=body, headers={"x-goog-api-key": key}, timeout=300).json()
        if "error" in d:
            if "seed" in d["error"].get("message", "").lower() and attempt_config is config:
                continue
            raise RuntimeError(d["error"].get("message", str(d["error"]))[:300])
        for part in d["candidates"][0]["content"]["parts"]:
            if "inlineData" in part:
                return base64.b64decode(part["inlineData"]["data"]), d.get("modelVersion", model), note
        raise RuntimeError("No image in response")
    raise RuntimeError("Request failed with and without seed")


def call_openai(model, prompt, seed):
    key = os.environ["OPENAI_API_KEY_AICOPYRIGHT"]
    body = {"model": model, "prompt": prompt, "size": "1536x1024", "quality": "high", "n": 1}
    d = requests.post("https://api.openai.com/v1/images/generations", json=body,
                      headers={"Authorization": f"Bearer {key}"}, timeout=400).json()
    if "error" in d:
        raise RuntimeError(str(d["error"].get("message", d["error"]))[:300])
    return base64.b64decode(d["data"][0]["b64_json"]), model, "quality high; no seed parameter"


def run_one(job):
    scene, short, cand = job
    provider, model = MODELS[short]
    fn = f"{scene['scene']}_{short}_c{cand}.png"
    row = {"file": fn, "set": scene["set"], "scene": scene["scene"], "title": scene["title"],
           "model_short": short, "model": model, "candidate": cand, "prompt": scene["prompt"],
           "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    if (IMG_DIR / fn).exists():
        data = (IMG_DIR / fn).read_bytes()
        img = Image.open(io.BytesIO(data))
        row.update(status="ok", error="", model_reported="(existing file)", settings="", width=img.width,
                   height=img.height, sha256=hashlib.sha256(data).hexdigest(), seconds="")
        return row
    err = ""
    for attempt in range(3):
        try:
            t = time.time()
            fn_call = call_google if provider == "google" else call_openai
            data, version, settings = fn_call(model, scene["prompt"], SEEDS[cand - 1])
            img = Image.open(io.BytesIO(data))
            (IMG_DIR / fn).write_bytes(data)
            row.update(status="ok", error="", model_reported=version, settings=settings, width=img.width,
                       height=img.height, sha256=hashlib.sha256(data).hexdigest(),
                       seconds=round(time.time() - t, 1))
            return row
        except Exception as e:
            err = str(e)
            time.sleep(8 * (attempt + 1))
    row.update(status="failed", error=err, model_reported="", settings="", width="", height="", sha256="", seconds="")
    return row


def main():
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    scenes = read_prompts()
    shorts = [a for a in sys.argv[1:] if a in MODELS] or list(MODELS)
    jobs = [(s, m, c) for m in shorts for s in scenes for c in (1, 2)]
    rows = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        for f in as_completed([pool.submit(run_one, j) for j in jobs]):
            r = f.result()
            rows.append(r)
            print(f"{r['status']:7s} {r['file']} {r['error'][:100]}", flush=True)
    rows.sort(key=lambda r: (r["model_short"], r["set"], int(r["scene"][1:]), r["candidate"]))
    fields = ["file", "set", "scene", "title", "model_short", "model", "model_reported", "candidate", "settings",
              "width", "height", "seconds", "sha256", "created_utc", "status", "error", "prompt"]
    with open(OUT / "manifest.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"Done: {sum(r['status'] == 'ok' for r in rows)} of {len(rows)} images")


if __name__ == "__main__":
    main()
