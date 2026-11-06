"""Check whether each generated image contains what its prompt asked for.

Two independent image-reading models (OpenAI GPT-5.1 and Google Gemini 3.1 Pro)
answer the same fixed yes-or-no questions about every image: one question per
element the study needs, phrased so that "yes" is the wanted answer, plus two
questions about telltale errors (visible text or signatures; malformed hands,
faces, or objects). Writes adherence.csv in model_comparison_2026-10-15/.
"""

import base64
import csv
import io
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from PIL import Image

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "model_comparison_2026-10-15"

CHECKS = {
    "A1": ["Is a woman reading a letter at a table?", "Are a teapot and a cup on the table?",
           "Is part of the table bare, with nothing on it?", "Is a copper pot hanging on the wall?",
           "Is there a window on the right side of the image?"],
    "A2": ["Is an old fisherman mending a net?", "Are a wooden crate and a coil of rope beside him?",
           "Is there an empty stretch of dock on one side of him?", "Is a rowboat moored in the water?"],
    "A3": ["Are there exactly two children?", "Is a kite flying in the sky?", "Is a farmhouse visible in the distance?",
           "Are the children small and in the lower right part of the image?"],
    "A4": ["Is a young man playing the violin?", "Is there a music stand?", "Is there an empty wooden chair?",
           "Is there a mirror on the wall?", "Is there an oil lamp?"],
    "A5": ["Is a market vendor arranging oranges?", "Are there crates and a basket of lemons?",
           "Is a section of the counter bare and empty?", "Is an iron lantern hanging?", "Is there a striped awning?"],
    "A6": ["Is a rowboat pulled up on a riverbank?", "Are two oars visible?", "Is a stone bridge visible?",
           "Are there willow trees?"],
    "A7": ["Is there bread?", "Is there cheese?", "Is there a clay jug?", "Is there a knife?",
           "Is the table free of any objects other than bread, cheese, the jug, and the knife?",
           "Is the right half of the table bare?"],
    "A8": ["Is this a snowy village street?", "Is the street empty of people?", "Is there a hand cart?",
           "Is there a lamp post?", "Is a church steeple visible?"],
    "A9": ["Is there a wooden bench under a flowering tree?", "Is there a clay flowerpot near the bench?",
           "Is there an iron gate in a stone wall?", "Is there an empty path?"],
    "A10": ["Is there a lighthouse?", "Is there a red buoy?", "Is a ship visible on the horizon?",
            "Is there a small cottage at the foot of the lighthouse?", "Are waves breaking on rocks?"],
    "B1": ["Is a woman reading in an armchair by a window?", "Does the daylight come from the left side of the image?"],
    "B2": ["Is an older man repairing a bicycle in a garage?", "Is the man kneeling?",
           "Is there a single overhead light bulb?"],
    "B3": ["Is a young woman wearing a yellow raincoat?", "Is she holding a closed umbrella?",
           "Is this a narrow, wet side street?", "Is the scene free of recognizable landmarks or famous buildings?"],
    "B4": ["Is a chef plating a dish?", "Is the chef the only person visible?", "Is steam rising?"],
    "B5": ["Is a bowl of lemons on a marble counter?", "Is a lemon cut in half beside the bowl?",
           "Is the scene free of any knife?"],
    "B6": ["Is a red canoe on a sandy shore?", "Does the canoe point toward the water?", "Is the lake still?",
           "Is the sunlight low and golden?"],
    "B7": ["Is there an empty wooden chair?", "Does the chair stand against the left wall?",
           "Is there a window at the far end of the hallway?", "Are the walls pale yellow?"],
    "B8": ["Is this a city street at night after rain?", "Is a single parked car on the right?",
           "Is there a lit shop window?", "Are there streetlights?"],
}
TELLS = ["Is the image free of visible text, letters, signatures, or watermarks?",
         "Is the image free of malformed hands, faces, or bodies, impossible objects, or other visible errors?"]

INSTRUCTIONS = ("Look carefully at the image and answer each question with yes or no. "
                "Answer only with JSON of the form {\"answers\": [\"yes\", \"no\", ...], \"errors_noted\": \"...\"}, "
                "with one answer per question in order, and in errors_noted a short description of any visible "
                "errors (or an empty string).\n\nQuestions:\n")


def jpeg_b64(path):
    img = Image.open(path).convert("RGB")
    img.thumbnail((1024, 1024))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=90)
    return base64.b64encode(buf.getvalue()).decode()


def parse(text):
    m = re.search(r"\{.*\}", text, flags=re.S)
    d = json.loads(m.group(0))
    return [a.strip().lower().startswith("y") for a in d["answers"]], d.get("errors_noted", "")


def ask_openai(questions, b64):
    key = os.environ["OPENAI_API_KEY_AICOPYRIGHT"]
    prompt = INSTRUCTIONS + "\n".join(f"{i + 1}. {q}" for i, q in enumerate(questions))
    body = {"model": "gpt-5.1", "reasoning": {"effort": "low"},
            "input": [{"role": "user", "content": [{"type": "input_text", "text": prompt},
                                                   {"type": "input_image", "image_url": f"data:image/jpeg;base64,{b64}"}]}]}
    d = requests.post("https://api.openai.com/v1/responses", json=body,
                      headers={"Authorization": f"Bearer {key}"}, timeout=300).json()
    if "error" in d and d["error"]:
        raise RuntimeError(str(d["error"])[:300])
    text = "".join(c.get("text", "") for o in d["output"] if o.get("type") == "message" for c in o["content"])
    return parse(text)


def ask_gemini(questions, b64):
    key = os.environ["GEMINI_API_KEY_AICOPYRIGHT"]
    prompt = INSTRUCTIONS + "\n".join(f"{i + 1}. {q}" for i, q in enumerate(questions))
    body = {"contents": [{"parts": [{"text": prompt}, {"inlineData": {"mimeType": "image/jpeg", "data": b64}}]}],
            "generationConfig": {"responseMimeType": "application/json"}}
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-pro-preview:generateContent"
    d = requests.post(url, json=body, headers={"x-goog-api-key": key}, timeout=300).json()
    if "error" in d:
        raise RuntimeError(d["error"].get("message", "")[:300])
    return parse(d["candidates"][0]["content"]["parts"][0]["text"])


def run_one(row, checker):
    questions = CHECKS[row["scene"]] + TELLS
    b64 = jpeg_b64(BASE / "images" / row["file"])
    for attempt in range(3):
        try:
            answers, note = (ask_openai if checker == "gpt-5.1" else ask_gemini)(questions, b64)
            if len(answers) != len(questions):
                raise RuntimeError("wrong number of answers")
            n_el = len(CHECKS[row["scene"]])
            return {"file": row["file"], "model_short": row["model_short"], "set": row["set"], "scene": row["scene"],
                    "checker": checker, "elements_met": sum(answers[:n_el]), "elements_total": n_el,
                    "missing": "; ".join(q for q, a in zip(questions[:n_el], answers[:n_el]) if not a),
                    "no_text": int(answers[n_el]), "no_errors": int(answers[n_el + 1]), "errors_noted": note}
        except Exception as e:
            err = str(e)
            time.sleep(6 * (attempt + 1))
    return {"file": row["file"], "model_short": row["model_short"], "set": row["set"], "scene": row["scene"],
            "checker": checker, "elements_met": "", "elements_total": "", "missing": f"FAILED: {err}",
            "no_text": "", "no_errors": "", "errors_noted": ""}


def main():
    rows = [r for r in csv.DictReader(open(BASE / "manifest.csv", encoding="utf-8")) if r["status"] == "ok"]
    jobs = [(r, c) for r in rows for c in ("gpt-5.1", "gemini-3.1-pro")]
    out = []
    path = BASE / "adherence.csv"
    if path.exists():  # rerun only the checks that failed last time, keep the rest
        old = list(csv.DictReader(open(path, encoding="utf-8")))
        out = [r for r in old if not str(r["missing"]).startswith("FAILED")]
        done = {(r["file"], r["checker"]) for r in out}
        jobs = [(r, c) for r, c in jobs if (r["file"], c) not in done]
        print(f"{len(out)} earlier checks kept, {len(jobs)} to run")
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(run_one, r, c) for r, c in jobs]
        for f in as_completed(futures):
            out.append(f.result())
    out.sort(key=lambda r: (r["model_short"], r["file"], r["checker"]))
    with open(BASE / "adherence.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    failed = sum(str(r["missing"]).startswith("FAILED") for r in out)
    print(f"{len(out)} checks written, {failed} failed")


if __name__ == "__main__":
    main()
