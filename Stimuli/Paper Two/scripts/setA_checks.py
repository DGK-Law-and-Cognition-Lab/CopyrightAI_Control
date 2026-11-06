"""The automatic checks for Set A: object detector, change mask, compositing, pixel identity.

- Object detector: OWLv2 (google/owlv2-base-patch16-ensemble, pinned to one revision, the same as the
  Set B checks), an open-vocabulary detector that takes a short text query ("a teapot") and returns
  boxes with a score from 0 to 1. Each query is scored on its own (the sigmoid of its logit), on the
  CPU, so the same image always gives the same numbers.
- Change mask: the per-pixel difference between two images is the Euclidean distance between their
  RGB values (0 to 441). Pixels whose difference exceeds the difference threshold are marked; the
  marks are cleaned by removing specks (8-connected groups of at most the speck size) and then
  filling holes (unmarked areas wholly enclosed by marks). The masked area is the share of the image
  inside the cleaned mask.
- Compositing: the cleaned mask is widened by the widening radius (every pixel within that distance
  of the mask, Euclidean), holes are filled again, and only the edited pixels inside the widened mask
  are pasted onto the input. Every pixel outside it is identical to the input.

All numbers come from setA/thresholds.json (setA_calibrate.py); nothing here chooses a number.
"""

import json

import numpy as np
import torch
from PIL import Image
from scipy import ndimage as ndi

import setA_common as C

DETECTOR_REPO = C.DETECTOR_MODEL
DETECTOR_REVISION = "cfd3195ba4ea9592eec887ded089f4c08eff231d"
RECORD_FLOOR = 0.05      # boxes scoring at least this are kept in the record (the best box is always kept)
NMS_IOU = 0.5            # two boxes for one query are the same object if their overlap (IoU) is at least this

# Objects that cannot appear in a scene plausible for 1900 to 1925 (prompt-bank rule 2). Their scores
# on the first source candidates are the detector's known-absent scores for setting the score cut.
ABSENT_QUERIES = ["a smartphone", "a laptop computer", "a television set", "a computer keyboard",
                  "a plastic water bottle", "a jet airplane", "a satellite dish", "a microwave oven"]


# ---------------------------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------------------------

class Detector:
    def __init__(self):
        from transformers import Owlv2ForObjectDetection, Owlv2Processor
        torch.set_grad_enabled(False)
        self.processor = Owlv2Processor.from_pretrained(DETECTOR_REPO, revision=DETECTOR_REVISION)
        self.model = Owlv2ForObjectDetection.from_pretrained(DETECTOR_REPO, revision=DETECTOR_REVISION).eval()
        self.name = f"{DETECTOR_REPO}@{DETECTOR_REVISION[:12]} (cpu)"

    def detect(self, image, queries):
        """{query: [{"score", "box": [x0, y0, x1, y1] in pixels}, ...]} best first."""
        img = image.convert("RGB")
        w, h = img.size
        side = max(w, h)                 # OWLv2 pads to a square (right and bottom) before resizing
        uniq = list(dict.fromkeys(queries))
        inputs = self.processor(text=[uniq], images=img, return_tensors="pt")
        out = self.model(**inputs)
        scores = torch.sigmoid(out.logits[0].float())          # [boxes, queries]
        cx, cy, bw, bh = out.pred_boxes[0].float().unbind(-1)
        x0 = ((cx - bw / 2) * side).clamp(0, w)
        y0 = ((cy - bh / 2) * side).clamp(0, h)
        x1 = ((cx + bw / 2) * side).clamp(0, w)
        y1 = ((cy + bh / 2) * side).clamp(0, h)
        # Boxes whose center lies in the padding (outside the image) are not in the image and are dropped.
        inside = ((cx * side) < w) & ((cy * side) < h) & (x1 > x0) & (y1 > y0)
        result = {}
        for qi, q in enumerate(uniq):
            s = scores[:, qi]
            boxes = []
            for i in torch.argsort(s, descending=True).tolist():
                if not inside[i]:
                    continue
                if boxes and s[i] < RECORD_FLOOR:
                    break
                boxes.append({"score": round(float(s[i]), 4),
                              "box": [round(float(v), 1) for v in (x0[i], y0[i], x1[i], y1[i])]})
            result[q] = boxes
        return result


def iou(a, b):
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def distinct(boxes, cut):
    """Boxes scoring at least cut, best first, dropping any that overlaps a better one (IoU >= NMS_IOU)."""
    kept = []
    for b in boxes:
        if b["score"] >= cut and all(iou(b["box"], k["box"]) < NMS_IOU for k in kept):
            kept.append(b)
    return kept


def center_inside(box, mask):
    x, y = int((box[0] + box[2]) / 2), int((box[1] + box[3]) / 2)
    y, x = min(max(y, 0), mask.shape[0] - 1), min(max(x, 0), mask.shape[1] - 1)
    return bool(mask[y, x])


# ---------------------------------------------------------------------------------------------
# Change mask and compositing
# ---------------------------------------------------------------------------------------------

def arr(img):
    return np.asarray(img.convert("RGB"), dtype=np.uint8)


def difference(a, b):
    """Per-pixel Euclidean RGB distance between two uint8 arrays."""
    return np.sqrt(((a.astype(np.float32) - b.astype(np.float32)) ** 2).sum(-1))


EIGHT = np.ones((3, 3), dtype=bool)


def remove_specks(marks, speck_px):
    lab, n = ndi.label(marks, structure=EIGHT)
    if n == 0:
        return marks
    sizes = np.bincount(lab.ravel())
    keep = sizes > speck_px
    keep[0] = False
    return keep[lab]


def change_mask(a, b, t):
    """Cleaned change mask between arrays a and b with the thresholds dict t."""
    marks = difference(a, b) > t["difference_threshold"]
    return ndi.binary_fill_holes(remove_specks(marks, t["speck_px"]))


def widen(mask, radius):
    if radius <= 0 or not mask.any():
        return mask.copy()
    dist = ndi.distance_transform_edt(~mask)
    return ndi.binary_fill_holes(dist <= radius)


def composite(edited, base, wide):
    out = base.copy()
    out[wide] = edited[wide]
    return out


def area_pct(mask):
    return round(100.0 * float(mask.mean()), 3)


def identical_outside(a, b, region):
    """True if a and b are identical at every pixel outside region; also returns the count that differ."""
    differ = np.any(a != b, axis=-1) & ~region
    return (not differ.any()), int(differ.sum())


def save_mask(mask, path):
    Image.fromarray((mask.astype(np.uint8) * 255), mode="L").save(path)


def load_mask(path):
    return np.asarray(Image.open(path).convert("L")) > 127


def load_thresholds():
    return json.loads(C.THRESHOLDS.read_text(encoding="utf-8"))
