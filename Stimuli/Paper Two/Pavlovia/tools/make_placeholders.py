#!/usr/bin/env python3
"""Write grey placeholder JPEGs for B1 (one per scene and composition).

Each placeholder shows its scene id, composition and file name, so a test run
shows at a glance which file a trial carries. They must be replaced by the
real files from Stimuli/Paper Two/setB/web/ (same names) before launch.

    python3 tools/make_placeholders.py            # writes B1/stimuli/*.jpg
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "B1" / "stimuli"
SCENES = ["SB-P1", "SB-N1", "SB-P2", "SB-N2", "SB-P3", "SB-R2",
          "SB-P4", "SB-N4", "SB-P5", "SB-N5", "SB-P6", "SB-N6"]
NAMES = {
    "SB-P1": "Reading by the window", "SB-P2": "The bicycle", "SB-P3": "The side street",
    "SB-P4": "The kitchen", "SB-P5": "The bus stop", "SB-P6": "The pond",
    "SB-N1": "The canoe", "SB-N2": "The hallway", "SB-R2": "The pier",
    "SB-N4": "The lemons", "SB-N5": "The farmhouse", "SB-N6": "The terrace",
}


def font(size):
    for f in ["/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial.ttf",
              "/System/Library/Fonts/Helvetica.ttc"]:
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            continue
    return ImageFont.load_default()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    real = [f for f in OUT.glob("SB-*.jpg")]
    if real and not (OUT / "PLACEHOLDER_IMAGES.txt").exists() and "--force" not in sys.argv:
        sys.exit(f"{OUT} already holds {len(real)} real images; not overwriting them (use --force).")
    for s in SCENES:
        for comp in ["V1", "I2"]:
            name = f"{s}_{comp}.jpg"
            im = Image.new("RGB", (1200, 800), (150, 150, 150) if comp == "V1" else (128, 128, 132))
            d = ImageDraw.Draw(im)
            d.rectangle([20, 20, 1179, 779], outline=(225, 225, 225), width=4)
            lines = [(s + "  " + comp, font(96)), (NAMES[s], font(54)), (name, font(44)),
                     ("PLACEHOLDER: replace with setB/web/" + name, font(30))]
            y = 190
            for text, f in lines:
                w = d.textlength(text, font=f)
                d.text(((1200 - w) / 2, y), text, fill=(245, 245, 245), font=f)
                y += f.size + 48
            im.save(OUT / name, "JPEG", quality=80)
            print("wrote", OUT / name)
    (OUT / "PLACEHOLDER_IMAGES.txt").write_text(
        "The JPEGs in this folder are grey placeholders made by tools/make_placeholders.py.\n"
        "Replace them with the files of the same names from Stimuli/Paper Two/setB/web/\n"
        "(tools/install_images.sh B1 does it and deletes this file). The deploy script\n"
        "refuses to push while this file exists.\n", encoding="utf-8")


if __name__ == "__main__":
    main()
