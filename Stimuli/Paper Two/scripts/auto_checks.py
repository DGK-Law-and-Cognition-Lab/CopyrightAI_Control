"""The automatic checks shared by Paper Two's image scripts.

Two checks, as the prompt bank names them (Docs/Paper Two/Paper_Two_Prompt_Bank.md,
"How a file is accepted"):

- An object detector, a model that finds and outlines named objects in an
  image. This is OWLv2 (google/owlv2-base-patch16-ensemble, pinned to one
  revision), an open-vocabulary detector: it takes any short text query, such
  as "a dog", and returns boxes with a score from 0 to 1 for how well each box
  matches the query. It runs locally on the CPU, so it costs nothing and gives
  the same numbers on every run. Each query is scored on its own (the sigmoid
  of the model's logit for that query), so queries never compete for a box.
- An image-description model, a model that describes an image, asked one fixed
  yes-or-no question per call. This is OpenAI's GPT-5.1 with reasoning off and
  temperature 0. Its reply must be exactly "yes" or "no" (case, spaces and a
  final full stop ignored); any other reply is asked again, at most three times
  in all, and is then recorded as "invalid", which counts as not confirmed.
  Every call is checked against and written to the cost ledger (api_ledger.py).

Box coordinates are shares of the image's width and height (0 to 1), as
[left, top, right, bottom].
"""

import base64
import io
import os
import time

import requests
import torch
from PIL import Image

from api_ledger import TEXT_MAX_USD, BudgetStop, text_cost

DETECTOR_REPO = "google/owlv2-base-patch16-ensemble"
DETECTOR_REVISION = "cfd3195ba4ea9592eec887ded089f4c08eff231d"
RECORD_FLOOR = 0.05  # boxes scoring at least this are kept in the record; acceptance uses the frozen score cut

DESCRIBER_MODEL = "gpt-5.1"
DESCRIBER_SETTINGS = {"reasoning": {"effort": "none"}, "temperature": 0, "max_output_tokens": 16}
DESCRIBER_INSTRUCTION = "Look at the image and answer the question with exactly one word: yes or no."
DESCRIBER_ATTEMPTS = 3


# ---------------------------------------------------------------- detector

class Detector:
    def __init__(self, device="cpu"):
        from transformers import Owlv2ForObjectDetection, Owlv2Processor
        torch.set_grad_enabled(False)
        self.device = device
        self.processor = Owlv2Processor.from_pretrained(DETECTOR_REPO, revision=DETECTOR_REVISION)
        self.model = Owlv2ForObjectDetection.from_pretrained(DETECTOR_REPO, revision=DETECTOR_REVISION)
        self.model = self.model.to(device).eval()
        self.name = f"{DETECTOR_REPO}@{DETECTOR_REVISION[:12]} ({device})"

    def detect(self, image, queries):
        """Return {query: [{"score": s, "box": [x0, y0, x1, y1]}, ...]} best first.

        Every query's best box is kept whatever its score; other boxes are kept
        when they score at least RECORD_FLOOR.
        """
        img = image.convert("RGB")
        w, h = img.size
        side = max(w, h)  # OWLv2 pads the image to a square (right and bottom) before resizing
        uniq = list(dict.fromkeys(queries))
        inputs = self.processor(text=[uniq], images=img, return_tensors="pt").to(self.device)
        out = self.model(**inputs)
        scores = torch.sigmoid(out.logits[0].float().cpu())  # [boxes, queries]
        cx, cy, bw, bh = out.pred_boxes[0].float().cpu().unbind(-1)
        x0 = ((cx - bw / 2) * side / w).clamp(0, 1)
        y0 = ((cy - bh / 2) * side / h).clamp(0, 1)
        x1 = ((cx + bw / 2) * side / w).clamp(0, 1)
        y1 = ((cy + bh / 2) * side / h).clamp(0, 1)
        result = {}
        for qi, q in enumerate(uniq):
            s = scores[:, qi]
            order = torch.argsort(s, descending=True)
            boxes = []
            for rank, i in enumerate(order.tolist()):
                if rank > 0 and s[i] < RECORD_FLOOR:
                    break
                if x1[i] <= x0[i] or y1[i] <= y0[i]:
                    continue
                boxes.append({"score": round(float(s[i]), 4),
                              "box": [round(float(v), 4) for v in (x0[i], y0[i], x1[i], y1[i])]})
            result[q] = boxes
        return result


def area(b):
    return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])


def intersection(a, b):
    return area([max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])])


def iou(a, b):
    i = intersection(a, b)
    u = area(a) + area(b) - i
    return i / u if u > 0 else 0.0


def inside_share(a, b):
    """Share of the smaller box that lies inside the larger one."""
    small = min(area(a), area(b))
    return intersection(a, b) / small if small > 0 else 0.0


def same_object(a, b, iou_cut, inside_cut):
    return iou(a, b) >= iou_cut or inside_share(a, b) >= inside_cut


def distinct_boxes(boxes, score_cut, iou_cut, inside_cut):
    """Boxes scoring at least score_cut, best first, dropping any box that is the
    same object as a better one (greedy non-maximum suppression)."""
    kept = []
    for b in boxes:
        if b["score"] < score_cut:
            continue
        if any(same_object(b["box"], k["box"], iou_cut, inside_cut) for k in kept):
            continue
        kept.append(b)
    return kept


def union_box(boxes):
    return [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]


def center_x(b):
    return (b[0] + b[2]) / 2


# ---------------------------------------------------------- description model

def image_b64_jpeg(path):
    img = Image.open(path).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=95)
    return base64.b64encode(buf.getvalue()).decode()


def _parse(text):
    t = text.strip().lower().rstrip(".").strip()
    return t if t in ("yes", "no") else None


def ask_yes_no(ledger, image_path, question, scene="", file="", purpose="description check", b64=None):
    """Ask one fixed yes-or-no question about one image. Returns a dict with the
    question, the parsed answer ("yes", "no" or "invalid"), the raw replies, the
    model version the API reported and the number of calls made."""
    key = os.environ["OPENAI_API_KEY_AICOPYRIGHT"]
    b64 = b64 or image_b64_jpeg(image_path)
    body = {"model": DESCRIBER_MODEL, **DESCRIBER_SETTINGS,
            "input": [{"role": "user", "content": [
                {"type": "input_text", "text": f"{DESCRIBER_INSTRUCTION}\n\nQuestion: {question}"},
                {"type": "input_image", "image_url": f"data:image/jpeg;base64,{b64}", "detail": "high"}]}]}
    raws, reported, calls = [], "", 0
    for attempt in range(DESCRIBER_ATTEMPTS):
        res = ledger.authorize(TEXT_MAX_USD)
        calls += 1
        try:
            r = requests.post("https://api.openai.com/v1/responses", json=body,
                              headers={"Authorization": f"Bearer {key}"}, timeout=120)
            d = r.json()
        except Exception as e:  # no reply: charge the most the call could cost
            ledger.record(res, DESCRIBER_MODEL, purpose, scene, file, TEXT_MAX_USD,
                          "no reply; charged the assumed maximum", f"no reply: {type(e).__name__}")
            raws.append(f"<no reply: {type(e).__name__}>")
            time.sleep(5 * (attempt + 1))
            continue
        if d.get("error"):
            ledger.record(res, DESCRIBER_MODEL, purpose, scene, file, 0.0, "API error; not billed",
                          f"error: {str(d['error'].get('message', d['error']))[:120]}")
            raws.append(f"<error: {str(d['error'].get('message', d['error']))[:200]}>")
            if "temperature" in str(d["error"]).lower() or "model" in str(d["error"].get("param", "")):
                raise RuntimeError(f"description model call rejected: {d['error']}")
            time.sleep(5 * (attempt + 1))
            continue
        usage = d.get("usage") or {}
        reported = d.get("model", DESCRIBER_MODEL)
        usd, basis = text_cost(reported, usage)
        text = "".join(c.get("text", "") for o in d.get("output", []) if o.get("type") == "message"
                       for c in o.get("content", []))
        raws.append(text)
        ledger.record(res, reported, purpose, scene, file, usd, basis, "ok",
                      usage.get("input_tokens", ""), usage.get("output_tokens", ""))
        ans = _parse(text)
        if ans:
            return {"question": question, "answer": ans, "raw": raws, "model_reported": reported, "calls": calls}
    return {"question": question, "answer": "invalid", "raw": raws, "model_reported": reported, "calls": calls}


__all__ = ["Detector", "ask_yes_no", "distinct_boxes", "union_box", "center_x", "area", "iou", "inside_share",
           "same_object", "BudgetStop", "DESCRIBER_MODEL", "DESCRIBER_SETTINGS", "DESCRIBER_INSTRUCTION",
           "DETECTOR_REPO", "DETECTOR_REVISION", "RECORD_FLOOR", "image_b64_jpeg"]
