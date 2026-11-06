"""Summarize the model comparison: detector validity, AI-likeness, prompt accuracy.

Reads detector_scores.csv, adherence.csv and manifest.csv in
model_comparison_2026-10-15/, writes summary.md there, and builds one contact
sheet per image set with the first candidate from every model side by side.
"""

import csv
import statistics as st
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from sklearn.metrics import roc_auc_score

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "model_comparison_2026-10-15"
NAMES = {"nb21": "Nano Banana 2.1", "nbpro": "Nano Banana Pro", "nb2": "Nano Banana 2",
         "gpt25s": "GPT Image 2.5 Sunburst", "gpt25f": "GPT Image 2.5 Flare", "gpt2": "GPT Image 2"}
PRICE = {"nb21": 33.6, "nbpro": 134.0, "nb2": 67.0, "gpt25s": 210.7, "gpt25f": 210.7, "gpt2": 211.0}  # $ per 1,000, Artificial Analysis, Oct 14 2026
ORDER = list(NAMES)


def pct(x):
    return f"{100 * x:.0f}%"


def main():
    det = list(csv.DictReader(open(BASE / "detector_scores.csv", encoding="utf-8")))
    adh = [r for r in csv.DictReader(open(BASE / "adherence.csv", encoding="utf-8")) if r["elements_total"]]
    man = [r for r in csv.DictReader(open(BASE / "manifest.csv", encoding="utf-8")) if r["status"] == "ok"]
    lines = ["# Model comparison, October 15, 2026", ""]

    lines += ["## 1. Can the detectors tell real images from AI images at all?", "",
              "AUC is the chance that a randomly chosen AI image gets a higher AI score than a randomly chosen real "
              "image of the same kind: 0.5 is guessing, 1.0 is perfect. False alarms are real images scored above 0.5.", "",
              "| Detector | Paintings: AUC | Paintings: false alarms | Photographs: AUC | Photographs: false alarms |",
              "|---|---|---|---|---|"]
    valid = {}
    for d in sorted({r["detector"] for r in det}):
        rows = [r for r in det if r["detector"] == d]
        cells = []
        for real, ai in (("real_painting", "ai_painting"), ("real_photo", "ai_photo")):
            y = [0] * sum(r["kind"] == real for r in rows) + [1] * sum(r["kind"] == ai for r in rows)
            s = [float(r["p_ai"]) for r in rows if r["kind"] == real] + [float(r["p_ai"]) for r in rows if r["kind"] == ai]
            auc = roc_auc_score(y, s)
            fa = st.mean(float(r["p_ai"]) > 0.5 for r in rows if r["kind"] == real)
            valid[(d, ai)] = auc
            cells += [f"{auc:.2f}", pct(fa)]
        lines.append(f"| {d} | " + " | ".join(cells) + " |")

    lines += ["", "## 2. How AI-like does each model's output look to the detectors?", "",
              "Mean AI score (0 to 1; lower means less detectably AI). Only detectors with AUC of at least 0.70 for "
              "that kind of image are averaged; the others cannot tell real from AI and are shown in brackets.", "",
              "| Model | Paintings (Set A) | Photographs (Set B) |", "|---|---|---|"]
    for m in ORDER:
        cells = []
        for ai in ("ai_painting", "ai_photo"):
            good = [float(r["p_ai"]) for r in det if r["model_short"] == m and r["kind"] == ai and valid[(r["detector"], ai)] >= 0.70]
            allv = [float(r["p_ai"]) for r in det if r["model_short"] == m and r["kind"] == ai]
            cells.append(f"{st.mean(good):.2f}" if good else f"[{st.mean(allv):.2f}]" if allv else "")
        lines.append(f"| {NAMES[m]} | " + " | ".join(cells) + " |")

    lines += ["", "## 3. Does each model draw what the prompt asked for?", "",
              "Share of required elements present, as judged by each checker; images with every element present "
              "according to both checkers; images free of visible text; images free of visible errors (both checkers).", "",
              "| Model | Elements present (GPT-5.1) | Elements present (Gemini 3.1 Pro) | All elements, both agree | No text | No visible errors | Seconds per image | Cost per 1,000 |",
              "|---|---|---|---|---|---|---|---|"]
    by_file = defaultdict(dict)
    for r in adh:
        by_file[r["file"]][r["checker"]] = r
    for m in ORDER:
        rs = [r for r in adh if r["model_short"] == m]
        if not rs:
            continue
        share = {c: st.mean(int(r["elements_met"]) / int(r["elements_total"]) for r in rs if r["checker"] == c)
                 for c in ("gpt-5.1", "gemini-3.1-pro")}
        files = [f for f, v in by_file.items() if len(v) == 2 and next(iter(v.values()))["model_short"] == m]
        allok = st.mean(all(v[c]["elements_met"] == v[c]["elements_total"] for c in v) for v in (by_file[f] for f in files))
        notext = st.mean(all(v[c]["no_text"] == "1" for c in v) for v in (by_file[f] for f in files))
        noerr = st.mean(all(v[c]["no_errors"] == "1" for c in v) for v in (by_file[f] for f in files))
        secs = [float(r["seconds"]) for r in man if r["model_short"] == m and r["seconds"]]
        lines.append(f"| {NAMES[m]} | {pct(share['gpt-5.1'])} | {pct(share['gemini-3.1-pro'])} | {pct(allok)} | "
                     f"{pct(notext)} | {pct(noerr)} | {st.mean(secs):.0f} | ${PRICE[m]:.0f} |" if secs else "")

    lines += ["", "## 4. Elements most often missing, by model", ""]
    for m in ORDER:
        miss = defaultdict(int)
        for r in adh:
            if r["model_short"] == m and r["missing"] and not r["missing"].startswith("FAILED"):
                for q in r["missing"].split("; "):
                    miss[f"{r['scene']}: {q}"] += 1
        top = sorted(miss.items(), key=lambda kv: -kv[1])[:6]
        lines.append(f"- **{NAMES[m]}:** " + ("; ".join(f"{k} ({v})" for k, v in top) if top else "none"))
    (BASE / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    sheets(man)


def font(size):
    for name in ("/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def sheets(man):
    tw, th, lw, pad = 330, 220, 150, 6
    big, small = font(20), font(15)
    for set_name in ("A", "B"):
        scenes = sorted({(int(r["scene"][1:]), r["scene"], r["title"]) for r in man if r["set"] == set_name})
        sheet = Image.new("RGB", (lw + len(ORDER) * (tw + pad) + pad, 40 + len(scenes) * (th + pad) + pad), "white")
        draw = ImageDraw.Draw(sheet)
        for j, m in enumerate(ORDER):
            draw.text((lw + pad + j * (tw + pad), 12), NAMES[m], fill="black", font=small)
        for i, (_, scene, title) in enumerate(scenes):
            y = 40 + i * (th + pad)
            draw.text((pad, y + 8), scene, fill="black", font=big)
            draw.text((pad, y + 36), title, fill="black", font=small)
            for j, m in enumerate(ORDER):
                hit = [r for r in man if r["scene"] == scene and r["model_short"] == m and r["candidate"] == "1"]
                if hit:
                    img = Image.open(BASE / "images" / hit[0]["file"]).convert("RGB")
                    img.thumbnail((tw, th))
                    sheet.paste(img, (lw + pad + j * (tw + pad) + (tw - img.width) // 2, y + (th - img.height) // 2))
        sheet.save(BASE / f"six_models_set_{set_name}.jpg", quality=88)


if __name__ == "__main__":
    main()
