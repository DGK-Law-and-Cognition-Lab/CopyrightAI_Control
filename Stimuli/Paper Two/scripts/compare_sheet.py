"""Side-by-side sheets comparing Nano Banana 2.1 and GPT Image 2.5, one row per scene.

Uses round 2 (first_look_2026-10-14/round2) for Nano Banana on every scene and for
GPT Image on the scenes whose prompts were revised; GPT Image images for the other
scenes come from round 1. Writes compare_set_A.jpg and compare_set_B.jpg in round2.
"""

import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROUND1 = HERE.parent / "first_look_2026-10-14"
ROUND2 = ROUND1 / "round2"
THUMB_W, THUMB_H = 420, 280
LABEL_W, PAD = 230, 8
NANO, GPT = "gemini-nano-banana-2.1", "gpt-image-2.5-sunburst-2026-09-08"
COLUMNS = [(NANO, 1), (NANO, 2), (GPT, 1), (GPT, 2)]


def font(size):
    for name in ("/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def load(folder):
    path = folder / "manifest.csv"
    rows = [r for r in csv.DictReader(open(path, encoding="utf-8")) if r["status"] == "ok"]
    for r in rows:
        r["path"] = folder / "images" / r["file"]
    return rows


def main():
    r1, r2 = load(ROUND1), load(ROUND2)
    revised = {r["scene"] for r in r2 if r["model_requested"] == GPT}
    rows = r2 + [r for r in r1 if r["model_requested"] == GPT and r["scene"] not in revised]
    big, small = font(22), font(17)
    for set_name in ("A", "B"):
        set_rows = [r for r in rows if r["set"] == set_name]
        scenes = sorted({(int(r["scene"][1:]), r["scene"], r["title"]) for r in set_rows})
        width = LABEL_W + len(COLUMNS) * (THUMB_W + PAD) + PAD
        height = 50 + len(scenes) * (THUMB_H + PAD) + PAD
        sheet = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(sheet)
        for j, (model, cand) in enumerate(COLUMNS):
            name = "Nano Banana 2.1" if model == NANO else "GPT Image 2.5"
            draw.text((LABEL_W + PAD + j * (THUMB_W + PAD), 15), f"{name}, candidate {cand}", fill="black", font=small)
        for i, (_, scene, title) in enumerate(scenes):
            y = 50 + i * (THUMB_H + PAD)
            draw.text((PAD, y + 10), scene, fill="black", font=big)
            draw.text((PAD, y + 42), title, fill="black", font=small)
            if scene in revised:
                draw.text((PAD, y + 66), "(revised prompt)", fill="gray", font=small)
            for j, (model, cand) in enumerate(COLUMNS):
                x = LABEL_W + PAD + j * (THUMB_W + PAD)
                match = [r for r in set_rows if r["scene"] == scene and r["model_requested"] == model
                         and int(r["candidate"]) == cand]
                if not match:
                    draw.rectangle([x, y, x + THUMB_W, y + THUMB_H], outline="gray")
                    draw.text((x + 10, y + 10), "missing", fill="gray", font=small)
                    continue
                img = Image.open(match[0]["path"]).convert("RGB")
                img.thumbnail((THUMB_W, THUMB_H))
                sheet.paste(img, (x + (THUMB_W - img.width) // 2, y + (THUMB_H - img.height) // 2))
        out = ROUND2 / f"compare_set_{set_name}.jpg"
        sheet.save(out, quality=88)
        print(out)


if __name__ == "__main__":
    main()
