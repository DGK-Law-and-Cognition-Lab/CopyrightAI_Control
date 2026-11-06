"""Score every image with three open AI-image detectors, and test the detectors first.

Each detector is a small image classifier from Hugging Face that outputs the
probability an image was AI-generated. The real paintings and photographs in
references/ have a known answer (not AI), so they show whether each detector
can tell real from generated at all. Writes detector_scores.csv (one row per
image per detector) in model_comparison_2026-10-15/.
"""

import csv
from pathlib import Path

import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "model_comparison_2026-10-15"
DETECTORS = {
    "haywoodsloan": "haywoodsloan/ai-image-detector-deploy",
    "ateeqq": "Ateeqq/ai-vs-human-image-detector",
    "organika": "Organika/sdxl-detector",
}
AI_WORDS = ("artificial", "fake", "ai", "generated", "sdxl", "synthetic")


def ai_label_ids(config):
    ids = [i for i, name in config.id2label.items()
           if any(w == name.lower() or name.lower().startswith(w) or w in name.lower().split("_") for w in AI_WORDS)]
    if not ids:
        raise RuntimeError(f"Cannot tell which label means AI: {config.id2label}")
    return ids


def images():
    refs = list(csv.DictReader(open(BASE / "references" / "refs.csv", encoding="utf-8")))
    for r in refs:
        yield BASE / "references" / r["file"], r["kind"], "", ""
    for r in csv.DictReader(open(BASE / "manifest.csv", encoding="utf-8")):
        if r["status"] == "ok":
            yield BASE / "images" / r["file"], "ai_" + ("painting" if r["set"] == "A" else "photo"), r["model_short"], r["scene"]


def main():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    items = list(images())
    rows = []
    for short, repo in DETECTORS.items():
        proc = AutoImageProcessor.from_pretrained(repo)
        model = AutoModelForImageClassification.from_pretrained(repo).to(device).eval()
        ai_ids = ai_label_ids(model.config)
        print(short, model.config.id2label, "-> AI labels", [model.config.id2label[i] for i in ai_ids], flush=True)
        for path, kind, gen_model, scene in items:
            img = Image.open(path).convert("RGB")
            with torch.no_grad():
                logits = model(**proc(images=img, return_tensors="pt").to(device)).logits
            p = torch.softmax(logits.float().cpu(), dim=-1)[0]
            rows.append({"detector": short, "file": path.name, "kind": kind, "model_short": gen_model,
                         "scene": scene, "p_ai": round(float(sum(p[i] for i in ai_ids)), 4)})
    with open(BASE / "detector_scores.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} scores written")


if __name__ == "__main__":
    main()
