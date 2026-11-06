"""Contact sheets for the first look: one sheet per set, one row per scene.

Reads first_look_2026-10-14/manifest.csv and writes contact_sheet_set_A.jpg and
contact_sheet_set_B.jpg next to it. Columns are the candidates for each model
found in the manifest.
"""

import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "first_look_2026-10-14"
THUMB_W, THUMB_H = 480, 320
LABEL_W, PAD = 230, 8


def font(size):
    for name in ("/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def main():
    rows = [r for r in csv.DictReader(open(OUT / "manifest.csv", encoding="utf-8")) if r["status"] == "ok"]
    columns = sorted({(r["model_requested"], int(r["candidate"])) for r in rows})
    big, small = font(22), font(17)
    for set_name in ("A", "B"):
        set_rows = [r for r in rows if r["set"] == set_name]
        scenes = sorted({(int(r["scene"][1:]), r["scene"], r["title"]) for r in set_rows})
        width = LABEL_W + len(columns) * (THUMB_W + PAD) + PAD
        height = 50 + len(scenes) * (THUMB_H + PAD) + PAD
        sheet = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(sheet)
        for j, (model, cand) in enumerate(columns):
            x = LABEL_W + PAD + j * (THUMB_W + PAD)
            draw.text((x, 15), f"{model}  candidate {cand}", fill="black", font=small)
        for i, (_, scene, title) in enumerate(scenes):
            y = 50 + i * (THUMB_H + PAD)
            draw.text((PAD, y + 10), scene, fill="black", font=big)
            draw.text((PAD, y + 42), title, fill="black", font=small)
            for j, (model, cand) in enumerate(columns):
                match = [r for r in set_rows if r["scene"] == scene and r["model_requested"] == model
                         and int(r["candidate"]) == cand]
                x = LABEL_W + PAD + j * (THUMB_W + PAD)
                if not match:
                    draw.rectangle([x, y, x + THUMB_W, y + THUMB_H], outline="gray")
                    draw.text((x + 10, y + 10), "missing", fill="gray", font=small)
                    continue
                img = Image.open(OUT / "images" / match[0]["file"]).convert("RGB")
                img.thumbnail((THUMB_W, THUMB_H))
                sheet.paste(img, (x + (THUMB_W - img.width) // 2, y + (THUMB_H - img.height) // 2))
        path = OUT / f"contact_sheet_set_{set_name}.jpg"
        sheet.save(path, quality=88)
        print(path)


if __name__ == "__main__":
    main()
