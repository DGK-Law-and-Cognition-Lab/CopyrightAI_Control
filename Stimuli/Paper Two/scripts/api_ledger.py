"""Append-only cost ledger for every paid API call made for Paper Two's images.

Every call is checked against the ledger before it is sent and written to it
after it returns. The ledger file is Stimuli/Paper Two/api_cost_ledger.csv,
one row per call: UTC time, script, model, purpose, scene, file, input and
output tokens, image count, estimated cost in US dollars, the price used, the
running total, and the call's status. Rows are only ever appended.

Spending limits
- HARD_CAP_USD (100 dollars, raised from 50 by David on 27 October 2026)
  covers all Paper Two image work this quarter: this ledger plus the Set A
  ledger (api_cost_ledger_setA.csv, written by the setA_ scripts in its own
  format). Before each call the ledger adds both ledgers' totals, the cost of
  calls still in flight, and the most the next call could cost; if that sum
  passes the cap, the call is not sent and BudgetStop is raised.
- A script may also set a lower soft cap on its own spending (the sum of the
  ledger rows it wrote under its script name, over all of its runs).

Prices
- Image model calls: the price of GPT Image 2.5 Flare per high-quality
  1536 x 1024 image is not published in a form this script can read. Artificial
  Analysis listed it at $210.70 per 1,000 images on 14 October 2026 (see
  summarize_comparison.py), probably at a smaller size. Each image is
  therefore charged the larger of a conservative $0.30 and its returned token
  usage priced at GPT Image 1's published rates ($5 per million text input
  tokens, $10 per million image input tokens, $40 per million image output
  tokens).
- Nano Banana Pro (gemini-3-pro-image) images: the larger of $0.134 per image
  (the rate used in the 15 October comparison) and the returned usage priced
  at Google's published Gemini 3 Pro Image rates ($2 per million input
  tokens, $12 per million text and thinking output tokens, $120 per million
  image output tokens).
- Image-reading (description) model calls: the returned token usage priced at
  OpenAI's published GPT-5.1 rates ($1.25 per million input tokens, $10 per
  million output tokens), with no discount for cached input.
- A call that ends without any reply (a timeout or broken connection) may
  still have been billed, so it is charged the most that call could cost. A
  call that returns an API error is charged nothing, since errors are not
  billed.
"""

import csv
import fcntl
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

LEDGER = Path(__file__).resolve().parent.parent / "api_cost_ledger.csv"
FIELDS = ["utc_time", "script", "model", "purpose", "scene", "file", "input_tokens", "output_tokens",
          "image_count", "usd_estimate", "price_basis", "running_total_usd", "status"]
HARD_CAP_USD = 175.0  # raised by David: 50 to 100 and 130 on 27 October, 160 on 28 October, 175 on 29 October 2026
SETA_LEDGER = LEDGER.parent / "api_cost_ledger_setA.csv"  # counted toward the same cap

GEMINI_IMAGE_USD = 0.134  # per image, the 15 October comparison's rate
GEMINI_RATES = {"in": 2.0, "text_out": 12.0, "image_out": 120.0}  # $ per million tokens (Gemini 3 Pro Image)
GEMINI_IMAGE_MAX_USD = 0.30  # the most one Nano Banana Pro image call is assumed able to cost

IMAGE_FLOOR_USD = 0.30
IMAGE_RATES = {"text_in": 5.0, "image_in": 10.0, "out": 40.0}  # $ per million tokens (GPT Image 1)
IMAGE_MAX_USD = 0.60  # the most one high-quality 1536 x 1024 image call is assumed able to cost
TEXT_RATES = {"gpt-5.1": {"in": 1.25, "out": 10.0}}  # $ per million tokens
TEXT_MAX_USD = 0.02  # the most one yes-or-no image question is assumed able to cost


class BudgetStop(Exception):
    """Raised when the next call could push spending past a cap."""


def image_cost(usage):
    """Estimated dollars for one image call, from the usage the API returned."""
    usage = usage or {}
    details = usage.get("input_tokens_details") or {}
    text_in = details.get("text_tokens", usage.get("input_tokens", 0) or 0) or 0
    image_in = details.get("image_tokens", 0) or 0
    out = usage.get("output_tokens", 0) or 0
    by_tokens = (text_in * IMAGE_RATES["text_in"] + image_in * IMAGE_RATES["image_in"]
                 + out * IMAGE_RATES["out"]) / 1e6
    if by_tokens > IMAGE_FLOOR_USD:
        return by_tokens, "returned tokens at GPT Image 1 published rates (above the $0.30 floor)"
    return IMAGE_FLOOR_USD, "conservative $0.30 per high-quality 1536x1024 image (model price unpublished)"


def gemini_image_cost(usage):
    """Estimated dollars for one Nano Banana Pro call, from its usageMetadata."""
    usage = usage or {}
    prompt = usage.get("promptTokenCount", 0) or 0
    thoughts = usage.get("thoughtsTokenCount", 0) or 0
    details = usage.get("candidatesTokensDetails") or []
    if details:
        image_out = sum(d.get("tokenCount", 0) for d in details if d.get("modality") == "IMAGE")
        # output tokens not broken down by modality are counted as text
        text_out = max(0, (usage.get("candidatesTokenCount", 0) or 0) - image_out)
    else:  # no breakdown: count every output token at the image rate (the higher one)
        image_out, text_out = usage.get("candidatesTokenCount", 0) or 0, 0
    by_tokens = (prompt * GEMINI_RATES["in"] + (text_out + thoughts) * GEMINI_RATES["text_out"]
                 + image_out * GEMINI_RATES["image_out"]) / 1e6
    if by_tokens > GEMINI_IMAGE_USD:
        return by_tokens, "returned usage at Gemini 3 Pro Image published rates (above $0.134)"
    return GEMINI_IMAGE_USD, "$0.134 per image (15 October comparison rate; returned usage priced lower)"


def other_ledger_total():
    """Total of the Set A ledger, which has its own columns (estimated_usd)."""
    if not SETA_LEDGER.exists():
        return 0.0
    with open(SETA_LEDGER, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    col = "estimated_usd" if rows and "estimated_usd" in rows[0] else "usd_estimate"
    total = 0.0
    for r in rows:
        try:
            total += float(r.get(col) or 0)
        except ValueError:
            pass
    return total


def text_cost(model, usage):
    """Estimated dollars for one image-reading call, from the usage the API returned."""
    rates = TEXT_RATES.get(model.split("-20")[0], TEXT_RATES["gpt-5.1"])
    usage = usage or {}
    cost = ((usage.get("input_tokens", 0) or 0) * rates["in"] + (usage.get("output_tokens", 0) or 0) * rates["out"]) / 1e6
    return cost, f"returned tokens at ${rates['in']}/M input, ${rates['out']}/M output (OpenAI published)"


class Ledger:
    def __init__(self, script, soft_cap_usd=None):
        self.script = script
        self.soft_cap = soft_cap_usd
        self.reserved = 0.0
        self.lock = threading.Lock()
        self.stopped = False
        if not LEDGER.exists():
            with open(LEDGER, "w", newline="", encoding="utf-8") as fh:
                csv.DictWriter(fh, fieldnames=FIELDS).writeheader()

    def _rows(self):
        with open(LEDGER, newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))

    def total(self):
        return sum(float(r["usd_estimate"] or 0) for r in self._rows())

    def script_total(self):
        return sum(float(r["usd_estimate"] or 0) for r in self._rows() if r["script"] == self.script)

    def authorize(self, max_usd):
        """Reserve max_usd for the next call, or raise BudgetStop if it could pass a cap."""
        with self.lock:
            if self.stopped:
                raise BudgetStop("spending stop already reached in this run")
            total = self.total() + other_ledger_total()
            if total + self.reserved + max_usd > HARD_CAP_USD:
                self.stopped = True
                raise BudgetStop(f"hard cap: both ledgers ${total:.2f} + in flight ${self.reserved:.2f} "
                                 f"+ next call up to ${max_usd:.2f} would pass ${HARD_CAP_USD:.2f}")
            if self.soft_cap is not None:
                own = self.script_total()
                if own + self.reserved + max_usd > self.soft_cap:
                    self.stopped = True
                    raise BudgetStop(f"soft cap: {self.script} spent ${own:.2f} + in flight ${self.reserved:.2f} "
                                     f"+ next call up to ${max_usd:.2f} would pass ${self.soft_cap:.2f}")
            self.reserved += max_usd
            return max_usd

    def record(self, reservation, model, purpose, scene, file, usd, price_basis, status,
               input_tokens="", output_tokens="", image_count=""):
        """Release the reservation and append one row for the call."""
        with self.lock:
            self.reserved = max(0.0, self.reserved - reservation)
            with open(LEDGER, "a+", newline="", encoding="utf-8") as fh:
                try:
                    fcntl.flock(fh, fcntl.LOCK_EX)
                except OSError:
                    pass
                fh.seek(0)
                running = sum(float(r["usd_estimate"] or 0) for r in csv.DictReader(fh)) + usd
                fh.seek(0, os.SEEK_END)
                csv.DictWriter(fh, fieldnames=FIELDS).writerow({
                    "utc_time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "script": self.script, "model": model, "purpose": purpose, "scene": scene, "file": file,
                    "input_tokens": input_tokens, "output_tokens": output_tokens, "image_count": image_count,
                    "usd_estimate": f"{usd:.5f}", "price_basis": price_basis,
                    "running_total_usd": f"{running:.5f}", "status": status})
                try:
                    fcntl.flock(fh, fcntl.LOCK_UN)
                except OSError:
                    pass
            return running
