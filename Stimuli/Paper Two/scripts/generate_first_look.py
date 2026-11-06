"""First look at the Paper Two prompt bank on two image models.

Reads every prompt from the 14 October prompt bank,
Docs/Paper Two/Background/Superseded 2026-10-14/Paper_Two_Prompt_Bank_2026-10-14.md, sends each to
Google's Nano Banana 2.1 and OpenAI's GPT Image 2.5 (Sunburst), and saves the
images with one manifest row per image. API keys are read from the environment
variables GEMINI_API_KEY_AICOPYRIGHT and OPENAI_API_KEY_AICOPYRIGHT.

Run from a shell that has loaded ~/.zshrc. Name the models to run (none means both),
optionally a subset of scenes and an output subfolder:
    python3 generate_first_look.py gptimage
    python3 generate_first_look.py nanobanana --out=round2
    python3 generate_first_look.py gptimage --scenes=A4,A5,A6,A7,B3 --out=round2
"""

import base64
import csv
import hashlib
import io
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import requests
from PIL import Image

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
BANK = PROJECT / "Docs" / "Paper Two" / "Background" / "Superseded 2026-10-14" / "Paper_Two_Prompt_Bank_2026-10-14.md"
OUT = HERE.parent / "first_look_2026-10-14"
IMG_DIR = OUT / "images"
for _arg in sys.argv[1:]:
    if _arg.startswith("--out="):
        OUT = OUT / _arg.split("=", 1)[1]
        IMG_DIR = OUT / "images"

CANDIDATES = 2
SEEDS = [1001, 1002]
SET_A_SUFFIX = "No text, lettering, signature, watermark, or frame."
SET_B_SUFFIX = "Color photograph, natural light balance, sharp focus. No text, watermark, or border."

GEMINI_MODEL = "gemini-nano-banana-2.1"
OPENAI_MODEL = "gpt-image-2.5-sunburst-2026-09-08"
PARTS = ["Subject", "Composition", "Colors", "Lighting", "Style", "Mood", "Viewpoint", "Background"]


def read_prompts():
    text = BANK.read_text(encoding="utf-8")
    scenes = []
    for block in re.split(r"\n### ", text)[1:]:
        head = block.split("\n", 1)[0]
        m = re.match(r"(A\d+)\. (.+?) \(", head)
        if m:
            rows = dict(re.findall(r"^\| (\w+) \| (.+?) \|$", block, flags=re.M))
            parts = [rows[p] for p in PARTS]
            scenes.append({"set": "A", "scene": m.group(1), "title": m.group(2),
                           "prompt": " ".join(parts) + " " + SET_A_SUFFIX})
            continue
        m = re.match(r"(B\d+)\. (.+?) \(", head)
        if m:
            plan = re.search(r"- \*\*Plan:\*\* (.+)", block).group(1).strip()
            scenes.append({"set": "B", "scene": m.group(1), "title": m.group(2),
                           "prompt": plan + " " + SET_B_SUFFIX})
    if len(scenes) != 18:
        sys.exit(f"Expected 18 scenes in the prompt bank, found {len(scenes)}")
    return scenes


def call_gemini(prompt, seed):
    key = os.environ["GEMINI_API_KEY_AICOPYRIGHT"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["IMAGE"],
                                 "imageConfig": {"aspectRatio": "3:2"},
                                 "seed": seed}}
    r = requests.post(url, json=body, headers={"x-goog-api-key": key}, timeout=300)
    d = r.json()
    if "error" in d:
        raise RuntimeError(d["error"].get("message", str(d["error"]))[:300])
    for part in d["candidates"][0]["content"]["parts"]:
        if "inlineData" in part:
            return base64.b64decode(part["inlineData"]["data"]), d.get("modelVersion", GEMINI_MODEL), "3:2", f"seed {seed}"
    raise RuntimeError("No image in response")


def call_openai(prompt, seed):
    key = os.environ["OPENAI_API_KEY_AICOPYRIGHT"]
    body = {"model": OPENAI_MODEL, "prompt": prompt, "size": "1536x1024", "quality": "high", "n": 1}
    r = requests.post("https://api.openai.com/v1/images/generations", json=body,
                      headers={"Authorization": f"Bearer {key}"}, timeout=300)
    d = r.json()
    if "error" in d:
        raise RuntimeError(str(d["error"].get("message", d["error"]))[:300])
    return base64.b64decode(d["data"][0]["b64_json"]), OPENAI_MODEL, "1536x1024", "quality high; no seed parameter"


def run_one(job):
    scene, model, cand = job["scene"], job["model"], job["candidate"]
    seed = SEEDS[cand - 1]
    fn = f"{scene['scene']}_{model}_c{cand}.png"
    row = {"file": fn, "set": scene["set"], "scene": scene["scene"], "title": scene["title"],
           "model_requested": GEMINI_MODEL if model == "nanobanana" else OPENAI_MODEL,
           "candidate": cand, "prompt": scene["prompt"],
           "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    for attempt in range(3):
        try:
            data, version, size, settings = (call_gemini if model == "nanobanana" else call_openai)(scene["prompt"], seed)
            img = Image.open(io.BytesIO(data))
            (IMG_DIR / fn).write_bytes(data)
            row.update(status="ok", error="", model_reported=version, size=size, settings=settings,
                       width=img.width, height=img.height, sha256=hashlib.sha256(data).hexdigest())
            return row
        except Exception as e:  # recorded in the manifest, retried twice
            err = str(e)
            time.sleep(5 * (attempt + 1))
    row.update(status="failed", error=err, model_reported="", size="", settings="", width="", height="", sha256="")
    return row


def main():
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    scenes = read_prompts()
    models = [a for a in sys.argv[1:] if a in ("nanobanana", "gptimage")] or ["nanobanana", "gptimage"]
    wanted = [a.split("=", 1)[1].split(",") for a in sys.argv[1:] if a.startswith("--scenes=")]
    if wanted:
        scenes = [s for s in scenes if s["scene"] in wanted[0]]
    jobs = [{"scene": s, "model": m, "candidate": c}
            for s in scenes for m in models for c in range(1, CANDIDATES + 1)]
    rows = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(run_one, j) for j in jobs]
        for f in as_completed(futures):
            row = f.result()
            rows.append(row)
            print(f"{row['status']:7s} {row['file']} {row['error'][:120]}", flush=True)
    rows.sort(key=lambda r: (r["set"], int(r["scene"][1:]), r["model_requested"], r["candidate"]))
    fields = ["file", "set", "scene", "title", "model_requested", "model_reported", "candidate",
              "size", "settings", "width", "height", "sha256", "created_utc", "status", "error", "prompt"]
    path = OUT / "manifest.csv"
    new = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        if new:
            w.writeheader()
        w.writerows(rows)
    ok = sum(r["status"] == "ok" for r in rows)
    print(f"Done: {ok} of {len(rows)} images saved to {IMG_DIR}")


if __name__ == "__main__":
    main()
