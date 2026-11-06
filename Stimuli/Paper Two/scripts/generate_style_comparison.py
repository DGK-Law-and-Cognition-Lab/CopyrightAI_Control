"""Side-by-side comparison of image models and style lines, for David to judge by eye.

Five scenes from the current prompt bank (three Set B photographs, two Set A paintings), each
made once by six models with two style lines: the bank's current one and a realism line written
to avoid the polished, cinematic look. Writes style_comparison_2026-10-27/ with every image, a
manifest, and one contact sheet per scene (rows: models; columns: current, realism).

Run from a shell that has loaded ~/.zshrc:
    python3 generate_style_comparison.py
"""

import csv
import io
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from api_ledger import Ledger  # noqa: E402
from generate_model_comparison import MODELS, call_google, call_openai  # noqa: E402
from generate_setB_B1 import read_bank as read_set_b  # noqa: E402
from setA_common import read_set_a, ledger_total  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "style_comparison_2026-10-27"
IMG = OUT / "images"
LEDGER_A = HERE.parent / "api_cost_ledger_setA.csv"
HARD_CAP = 100.0  # David's cap on all Paper Two image work this quarter (both ledgers), 27 October 2026

SCENES_B = ["SB-P1", "SB-P4", "SB-N2"]
SCENES_A = ["SA01", "SA06"]

# Price per image from the 15 October comparison (cost per 1,000 images divided by 1,000).
PRICE = {"nb21": 0.034, "nbpro": 0.134, "nb2": 0.067, "gpt25s": 0.211, "gpt25f": 0.211, "gpt2": 0.211}

B_CURRENT = "Color photograph, natural light balance, sharp focus."
B_REALISM = ("An unretouched documentary photograph taken with an ordinary digital camera in available light: "
             "true-to-life, slightly muted colors, fine sensor noise, natural imperfections and everyday clutter. "
             "Not cinematic, not HDR, no dramatic lighting, no glossy commercial look.")
B_CLOSING = "No text, watermark, or border."
A_REALISM = ("Painterly and hand-made in feel: uneven brush marks, varied paint thickness, small imperfections "
             "and a muted, slightly faded palette. Not glossy, not airbrushed, not photorealistic, no digital sheen.")
A_CLOSING = "No text, lettering, signature, watermark, or frame."

lock = threading.Lock()


def prompts():
    jobs = []
    set_b, _ = read_set_b()
    for code in SCENES_B:
        plan = set_b[code]["plan_v1"]
        jobs.append((code, "current", f"{plan} {B_CURRENT} {B_CLOSING}"))
        jobs.append((code, "realism", f"{plan} {B_REALISM} {B_CLOSING}"))
    set_a = read_set_a()
    for code in SCENES_A:
        parts = set_a[code]["parts"]
        jobs.append((code, "current", " ".join(parts) + " " + A_CLOSING))
        jobs.append((code, "realism", " ".join(parts) + " " + A_REALISM + " " + A_CLOSING))
    return jobs


def combined_total(ledger):
    return ledger.total() + ledger_total(LEDGER_A)


def run_model(short, jobs, ledger, rows):
    provider, model = MODELS[short]
    for code, style, prompt in jobs:
        fn = f"{code}_{short}_{style}.png"
        path = IMG / fn
        if path.exists():
            continue
        price = PRICE[short]
        with lock:
            if combined_total(ledger) + ledger.reserved + price > HARD_CAP:
                print(f"STOP: next call would pass ${HARD_CAP:.0f}", flush=True)
                return
            res = ledger.authorize(price)
        status, note = "ok", ""
        try:
            png, version, note = (call_google if provider == "google" else call_openai)(model, prompt, 1001)
            img = Image.open(io.BytesIO(png)).convert("RGB")
            img.save(path)
        except Exception as e:  # noqa: BLE001
            status, version, note = "error", model, str(e)[:200]
        ledger.record(res, model, f"style comparison {style}", code, fn, price if status == "ok" else 0.0,
                      "15 October comparison price per image", status, image_count=1)
        with lock:
            rows.append({"file": fn, "scene": code, "model_short": short, "model": version, "style": style,
                         "prompt": prompt, "status": status, "note": note,
                         "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")})
        print(short, code, style, status, note[:80], flush=True)


def sheets(jobs):
    font = ImageFont.load_default()
    scenes = list(dict.fromkeys(code for code, _, _ in jobs))
    w, h, pad, label = 600, 400, 8, 150
    for code in scenes:
        sheet = Image.new("RGB", (label + 2 * (w + pad), 30 + len(MODELS) * (h + pad)), "white")
        d = ImageDraw.Draw(sheet)
        d.text((label, 8), "current style line", fill="black", font=font)
        d.text((label + w + pad, 8), "realism style line", fill="black", font=font)
        for i, short in enumerate(MODELS):
            y = 30 + i * (h + pad)
            d.text((6, y + h // 2), MODELS[short][1][:22], fill="black", font=font)
            for j, style in enumerate(("current", "realism")):
                p = IMG / f"{code}_{short}_{style}.png"
                if p.exists():
                    im = Image.open(p).convert("RGB")
                    im.thumbnail((w, h))
                    sheet.paste(im, (label + j * (w + pad), y))
        sheet.save(OUT / f"sheet_{code}.jpg", quality=88)


def main():
    IMG.mkdir(parents=True, exist_ok=True)
    jobs = prompts()
    ledger = Ledger("generate_style_comparison", soft_cap_usd=15.0)
    rows = []
    with ThreadPoolExecutor(max_workers=len(MODELS)) as ex:
        for short in MODELS:
            ex.submit(run_model, short, jobs, ledger, rows)
    with open(OUT / "manifest.csv", "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["file", "scene", "model_short", "model", "style", "prompt", "status",
                                           "note", "created_utc"])
        if fh.tell() == 0:
            w.writeheader()
        w.writerows(rows)
    sheets(jobs)
    print(f"Done. Combined spend now ${combined_total(ledger):.2f}")


if __name__ == "__main__":
    main()
