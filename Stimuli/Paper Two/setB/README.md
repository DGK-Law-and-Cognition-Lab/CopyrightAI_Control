# Set B images for Paper B Study 1 (B1)

**Status (27 October 2026): all 24 files are accepted** and installed in the B1 experiment. Under the prompt bank's rescue rule, the no-person reserve **SB-R2 (The pier) replaced SB-N3 (The night street)** and takes SB-N3's position in the scene order of every list; see "SB-N3 replaced by SB-R2" below. This folder holds the participant images of B1: for each of the twelve photographic scenes of Set B used in B1 (SB-P1 to SB-P6 with a person; SB-N1, SB-N2, SB-R2, SB-N4, SB-N5 and SB-N6 without), the first composition (V1) and the second composition (I2). Every file was made by script with Nano Banana Pro (`gemini-3-pro-image`) and the Set B realism line. Each was kept because it was the first candidate to pass the automatic checks; no person picked an image. The model, realism line, closing sentence, no-text question and seed rule are read from the prompt bank's "Generation settings" (`Docs/Paper Two/Paper_Two_Prompt_Bank.md`). The plans, feature phrases, placement sentences and reserve scenes are read from its "Set B" section.

An earlier set made with GPT Image 2.5 Flare was superseded on 27 October 2026, after David judged it obviously AI-made. It is kept in `../setB_superseded_flare_2026-10-27/`.

## What is here

| Path | What it is |
|---|---|
| `SB-P1_V1.png`, `SB-P1_I2.png`, ... | The accepted files, 1264 × 848 PNG, the model's own 3:2 size. The model returns JPEG; each PNG is a lossless copy of the decoded pixels. |
| `web/` | Copies for the experiment: JPEG at the same 1264 × 848 size (never resized), quality 85, 126 to 327 KB. These are installed in `../Pavlovia/B1/stimuli/`. |
| `superseded_SB-N3_replaced_by_SB-R2/` | Everything of SB-N3, kept and not used: its 85 candidates with their records (`candidates/`), its last accepted V1 (c23, PNG and JPEG) and that file's diagnostic rows, the I2 c22 accepted before the plan-fit amendment (`superseded_plan_fit_amendment/`), and the two SB-N3 copies removed from the Pavlovia stimuli folder. The manifest lists the 85 candidates as `candidate (scene replaced)`. |
| `superseded_at_scale_cut_0.15/` | Files accepted only under the superseded scale cut 0.15: SB-N4 I2 c13 (PNG and JPEG) and SB-P6 I2 c01, plus the diagnostic rows for SB-N4 I2 c13. Kept, not used. |
| `candidates/` | All candidates of the twelve scenes in use (155), accepted or rejected, numbered in the order made (`SB-P1_V1_c01.png`). Each has a JSON file with its prompt, seed, generation record, every check result and its decision. |
| `manifest.csv` | One row per candidate and one per accepted file. |
| `thresholds.json` | The threshold rule, written before any image of this run was made, and the two values, set from the first batch and frozen before any acceptance decision. |
| `contact_sheet_B1.png` | The 24 accepted images, V1 beside I2 for each scene, with the I2 placement sentence and the main-element box drawn in red. |
| `plan_match_check.csv` | The plan-sentence diagnostic (below). It does not decide acceptance. |
| `generation.log` | The console record of the run. |

The cost of every paid call is in `../api_cost_ledger.csv`, under the label `generate_setB_B1.py [gemini-3-pro-image]`.

## How a file is made

- **V1 prompt:** plan version 1, then the Set B realism line ("An unretouched documentary photograph taken with an ordinary digital camera in available light: true-to-life, slightly muted colors, fine sensor noise, natural imperfections and everyday clutter. Not cinematic, not HDR, no dramatic lighting, no glossy commercial look."), then "No text, watermark, or border."
- **I2 prompt:** plan version 1, then the scene's placement sentence, then the same two sentences. The placement sentence is built from the accepted V1:
  - the detector finds, in V1, the main elements that the sentence names;
  - if the centre of their box lies right of half the width, "right" becomes "left";
  - if the box covers less of the frame than the scale cut, "small, seen from farther away" becomes "large, seen from close by".

  So I2 asks for the other side of the frame and the other scale.
- **Settings:** aspect ratio 3:2, with no size requested, so the model returns its own 1264 × 848. Candidate n is requested with seed 1000 + n. The model accepted every seed.

## How a file is accepted

Two checks, in `../scripts/auto_checks.py`:

- **Object detector:** OWLv2 (`google/owlv2-base-patch16-ensemble`, revision `cfd3195ba4ea`), run locally on the CPU. It takes a short text query such as "a dog" and returns boxes, each with a score from 0 to 1.
- **Image-description model:** GPT-5.1 with reasoning off and temperature 0, asked one yes-or-no question per call. A reply must be exactly "yes" or "no", or it is asked again (at most three times) and then counts as not confirmed.

**Every file** must pass the no-text check: the description model answers yes to "Is the image free of any visible text, letters, numbers, signatures or watermarks?"

**Every file** must also pass the plan-fit check (amendment of 27 October 2026). The description model answers yes to 'Does this photograph fit the following description: "<sentence>"?' for each of plan version 1's first three sentences: subject, arrangement and light. The fourth sentence, colors, is excluded as too vague to judge and is recorded only by the plan-sentence diagnostic.

**V1** is accepted when all of these hold:

- The detector finds every main element: the elements the scene's placement sentence names, queried by their head noun ("a bowl", not "a bowl of lemons").
- The description model answers "yes" to "Does the image show " + the feature phrase of plan version 1 + "?"
- For animal and passer-by scenes, the detector also confirms the feature. The animal must be found (SB-P2 a dog, SB-N2 a cat, SB-N4 a sparrow). SB-P6 needs a jogger found apart from the girl. SB-P4 needs no person found apart from the chef.

Weather and lights (SB-P1, SB-P3, SB-N1, SB-N5, SB-P5, SB-N3, SB-N6) are not objects a detector can find. For those scenes the detector confirms the main elements and the description model confirms the feature.

**I2** passes the same checks. In addition, the detector's box around the main elements must sit on the side and at the scale its placement sentence names. Side: the box's centre is left of half the width for "left", or right of it for "right". Scale: the box's area is below the scale cut for "small", or at or above it for "large".

**Thresholds** (`thresholds.json`):

- *Score cut:* the midpoint between two numbers from the first batch. The first is the median best score of the main elements (0.503). The second is the highest best score given to five absent decoy animals (0.071). The cut is **0.29**.
- *Scale cut:* the median main-element box area in the first batch, over the 11 images whose main elements were all found, rounded once, half-up, to two decimals. The cut is **0.16** (the median is 0.15503, SB-P6's V1).

The first batch is candidate 1 of V1 for each of the twelve scenes.

The scale cut was first frozen at 0.15 by mistake; see "Scale-cut correction" below.

**Rescue rules:**

- After 20 failed candidates for one file, the prompt gets one added sentence, placed before the realism line. For a feature, main-element or placement failure it reads "The photograph clearly shows ...", naming the check that failed most often. For a text failure it reads "The photograph shows no visible text, letters, numbers, signatures or watermarks." That file then gets 20 more tries.
- A file that still fails replaces its scene with the reserve of the same kind (SB-R1 with a person, SB-R2 without).

Every rule's exact wording is in each manifest row (`acceptance_rule`, `placement_rule`, `revision_rule`, `determinate_rules_note`).

## Run record, 27 October 2026

- **Thresholds:** frozen at 22:32 UTC, three minutes after the rule was written and before any acceptance decision.
- **Accepted:** 24 files from 143 candidates. Rejections, where one candidate can fail several checks: text 80, placement 77, main elements 8, feature 2.
- **Prompt revision:** three files needed it before the correction (SB-P1 I2, SB-P5 I2, SB-N3 I2), and each passed after the revision, at candidates 26, 22 and 22. After the correction, SB-N4 I2 also needed it and passed at c21. No reserve scene was used.
- **Before the scale-cut correction:** 143 candidates and 24 accepted files. The correction added 9 candidates; see "Scale-cut correction".
- **Pauses:** the run was paused once and then continued by scene (`--only`), to keep spending in check while the Set A images were being made under the same cap. Pausing changes no rule; candidate numbers and seeds simply continue.
- **Failed calls:** two calls returned no image (finishReason OTHER) and were retried. They are not candidates, and they are in the ledger.
- **SB-N3 V1 (c16):** the detector's best "a parked car" box covers only part of the car (area 0.006, against about 0.05 for the whole car). Both values are below the scale cut, and the car is right of centre either way, so the I2 placement sentence (left, large) is the same as it would be with a box around the whole car.

## Scale-cut correction, 27 October 2026

**What went wrong.** The script rounded twice: each area to four decimals (SB-P6 V1, 0.15502906, became 0.155), then the median to two decimals with Python's `round()`. That returns 0.155 as 0.15, because 0.155 is stored in binary as slightly less than 0.155. The written rule (the median, rounded to two decimals) gives 0.16.

**What was changed.** The coordinator decided that the rule be applied as written. `thresholds.json` now holds:

- the scale cut 0.16;
- a dated correction entry (`corrections`) with the reason and the unrounded median;
- the old 0.15 under `superseded_values`.

The script now takes the unrounded median and rounds it once, half-up. The rule itself is unchanged.

**Re-judging.** Every decision that uses the scale cut was re-judged in candidate order at 0.16. The earlier decision is kept in each candidate's JSON and in the manifest column `superseded_decision`. Two decisions changed:

- **SB-P6:** V1 (area 0.155) now counts as small, so its I2 placement sentence became "The girl is on the left side of the frame, large, seen from close by." I2 c01, made under the old sentence, is superseded and is not a candidate for the new one. The new search began at c02 (seed 1002), and c02 passes (area 0.189, centre 0.30).
- **SB-N4 I2:** c13 (area 0.1563) now fails "large". The search continued from c14, and c14 to c20 all failed placement. Their areas were 0.06 to 0.13, and the highest of all 20 was 0.156: the model draws the bowl at about 6 to 16 percent of the frame even when asked for "large, seen from close by".
  - At first the search stopped at a cap of 20 candidates set by the coordinator.
  - The coordinator then lifted that cap for this file, so the bank's rescue rule applied as written. The prompt got its one recorded revision, "The photograph clearly shows the bowl of lemons on the right side of the frame, large, seen from close by."
  - The search continued at c21 (seed 1021), and c21 passed: area 0.170, centre 0.72, the sparrow found (score 0.78), feature yes, no text.

No other decision changes at 0.16.

**Cost.** The correction cost $1.29: 9 images, their checks, and the diagnostic for SB-P6 I2 and SB-N4 I2.

**Pavlovia.** After the scale-cut correction, `install_images.sh B1` installed all 24 then-accepted files. After the plan-faithfulness amendment, the five changed accepted files were copied in directly, because the script needs all 24. For a time SB-N3_I2.jpg there was the superseded c22, and `stimuli/PLACEHOLDER_IMAGES.txt` blocked deployment. After SB-R2 replaced SB-N3, `install_images.sh B1` installed all 24 accepted files and removed the marker. A local test-mode run (one V1 row, one I2 row) loaded all 24 with no image error.

## Plan-faithfulness amendment, 27 October 2026

**Why.** B1 tells participants that the image matches Alex's plan, and B2's matches/departs manipulation depends on that. The plan-sentence diagnostic showed content misses in five accepted files: SB-P2 V1, SB-P3 I2, SB-N3 V1, SB-N4 I2 and SB-N6 I2.

**The new condition.** Before any participant data, the coordinator added the plan-fit check above as an acceptance condition for every Set B file. It is recorded in `thresholds.json` under `amendments`; the thresholds themselves are unchanged.

**How it was applied:**

- Every new candidate is asked the three plan-fit questions.
- An earlier candidate is asked them only where they decide its fate, that is, where it passes every other check.
- For the 24 files accepted before the amendment, the answers already recorded by the plan-sentence diagnostic (same question, same image bytes) were reused.
- Candidate order still decides acceptance. Every file was re-judged in order, and a file that now fails continues at its next candidate.
- When a V1 is replaced, its I2 is searched again. Earlier I2 candidates made under a placement sentence that has since changed are superseded.
- The 20-try rule and the one recorded revision apply per file. The revision rule gained one case for the plan-fit check: the failing plan sentence, repeated unchanged.
- No scene is moved to a reserve without the orchestrator.

**Results:**

| File | Before | After | Note |
|---|---|---|---|
| SB-P2 V1 | c01 | c04 | Placement sentence unchanged, so SB-P2 I2 stays c02 |
| SB-P3 I2 | c05 | c08 | |
| SB-N3 V1 | c16 | c23 | After the recorded revision (text): "The photograph shows no visible text, letters, numbers, signatures or watermarks." |
| SB-N3 I2 | c22 | none yet | Its placement sentence changed (see below) |
| SB-N4 I2 | c21 | c32 | Under its existing revision |
| SB-N6 I2 | c02 | c14 | |

**SB-N3 I2.** The new V1 (c23: the car on the left, area 0.06) changes the placement sentence to "The parked car is on the right side of the frame, large, seen from close by." So c01 to c22 are superseded. Candidates c23 to c38 all failed, and the run stopped at the amendment's $8 budget. Most of them show a large car on the right, but they fail on three overlapping counts:

- **Placement (15 of 16).** In many, the detector's best "a parked car" box lands on a small car further down the street.
- **Text (15 of 16).** Shop signs.
- **Plan fit, sentence 2 (13 of 16).** "One car is parked at the curb." Other cars appear in the street.

**The rescue rule in full.** The combined cap was raised to $130, with $4 for this file. The rule then ran exactly as written:

- c39 to c42 completed the first 20 tries under the new sentence.
- The recorded revision followed. Placement and text were tied at 19, and placement comes first in the tie order, so the added sentence was "The photograph clearly shows the parked car on the right side of the frame, large, seen from close by."
- c43 to c62 followed under the revised prompt.

All 40 failed. In c23 to c42: text 19, placement 19, plan fit 14 (always sentence 2). In c43 to c62: text 20, placement 19, plan fit 13 (always sentence 2). No candidate failed on text alone.

Most candidates show one large parked car on the right, as asked. But each also shows text (shop signs, street signs or license plates), and many have other cars in the street. In many, the detector's best "a parked car" box is a small car further down the street.

As instructed, the detector box rule and the "one car" sentence were not changed, and the scene was not moved to SB-R2. Candidate numbers and seeds reached c62 (seed 1062).

**SB-P1 V1.** Its acceptance stands as decided, using the answer recorded when it was judged ("yes" to plan sentence 1). A later diagnostic re-run gave "no" on its sentence 1. GPT-5.1 at temperature 0 is not fully stable on borderline images; in this one the woman looks out of the window with the book open on her lap.

**Cost.** The amendment cost $11.21 in all: 52 images in the first pass and the diagnostic on 23 files ($7.71), then 24 more SB-N3 I2 images and their checks ($3.50).

## SB-N3 replaced by SB-R2, 27 October 2026

**Why.** SB-N3 I2 had no passing candidate after the bank's rescue rule ran in full under the placement sentence of SB-N3 V1 c23: 20 tries (c23 to c42), the recorded revision, then 20 more (c43 to c62). Every one of the 40 failed the no-text check; 38 also failed placement, and 27 failed plan sentence 2 ("One car is parked at the curb."). The bank's next step is the reserve of the same kind, so SB-R2 (no person) replaces SB-N3. It takes SB-N3's place in every list, between SB-P3 and SB-P4.

**SB-R2's files.** They were made under every current rule: the frozen thresholds (0.29 and 0.16), the no-text check, the plan-fit condition (sentences 1 to 3), the placement rule, and the 20 tries with one recorded revision (not needed).

| File | Accepted candidate | Checks |
|---|---|---|
| SB-R2 V1 | c01 (seed 1001), first try | Pier (score 0.46) and rowboat (0.71) found; main-element box area 0.515, centre 0.42; "Does the image show bright sun shining on the water?" yes; no text; plan sentences 1 to 3 yes |
| SB-R2 I2 | c11 (seed 1011) | Placement sentence "The pier and the rowboat are on the right side of the frame, small, seen from farther away."; box area 0.139 (below 0.16), centre 0.74; feature yes; no text; plan sentences 1 to 3 yes |

For I2, c01 to c10 failed placement: the pier and boat came out too large or not on the right. c10 also failed the feature question.

SB-R2 cost $1.76 (12 images and their checks). Its plan-sentence diagnostic is 4 of 4 "yes" for both files.

**Feature counts used in B1:**

| Kind of feature | Scenes | Count |
|---|---|---|
| Weather | SB-P1, SB-P3, SB-N1, SB-N5, SB-R2 | 5 (was 4) |
| Animal | SB-P2, SB-N2, SB-N4 | 3 |
| Light | SB-P5, SB-N6 | 2 (was 3) |
| Passer-by | SB-P4, SB-P6 | 2 |

Six scenes with a person and six without, as before. The bank allows a reserve in use to change one kind's count by one.

## Plan-sentence diagnostic

`../scripts/check_plan_match_B1.py` asks the description model, for every sentence of plan version 1 and each accepted file, whether the photograph fits the sentence. It records the answers in `plan_match_check.csv`, and it does not decide acceptance. `--files` re-checks only the named files.

After the amendment and the SB-R2 replacement, the diagnostic covers all 24 accepted files: 93 of 96 answers are "yes". SB-R2's two files were checked after the swap; the other files' answers are from the fresh run after the amendment. The 3 others:

- SB-N4 V1, sentence 4 (yellow and white), color only.
- SB-N4 I2 (c32), sentence 4 (yellow and white), color only.
- **SB-P1 V1, sentence 1** ("A woman reads in an armchair beside a tall window."). For acceptance, the earlier answer to the same question on the same image ("yes") was reused, as the amendment directs. The fresh run answered "no". So the description model is not fully stable at temperature 0 on a borderline image: in it the woman looks out of the window with the book open on her lap. The superseded Flare set had 5 of 96 not "yes".

## How to rerun

From a shell that has loaded `~/.zshrc` (so that `GEMINI_API_KEY_AICOPYRIGHT` and `OPENAI_API_KEY_AICOPYRIGHT` are set), with Python 3.12, torch 2.5.1, transformers 4.46.2, Pillow and requests:

```
cd "Stimuli/Paper Two/scripts"
python3 generate_setB_B1.py                     # make, check and accept; writes every output
python3 generate_setB_B1.py --only SB-N3,SB-P5  # search only these scenes (the first batch and thresholds still cover all twelve)
python3 generate_setB_B1.py --outputs           # rebuild accepted files, web copies, manifest and sheet from saved candidates (no API calls)
python3 check_plan_match_B1.py                  # plan-sentence diagnostic on the 24 accepted files
../Pavlovia/tools/install_images.sh B1          # copy web/ into the B1 experiment
```

The script stops if the bank's Set B model, realism line, closing sentence, no-text question or seed rule differ from its named constants.

A rerun reuses every saved candidate and its saved check results and never remakes them, so it continues where the last run stopped. The thresholds are never recomputed once frozen. To start from scratch, move `candidates/` and `thresholds.json` elsewhere first. The image model takes a seed, but the same seed and prompt are not guaranteed to give the same image on a later date.

Spending limits: before every call the script adds this ledger and the Set A ledger (`../api_cost_ledger_setA.csv`). It stops before any call that could take the two together past $100. It also stops before any call that could take this run's own spending past a soft cap, $25 by default (`--soft-cap`).

## Manifest columns

As in the superseded run, plus:

- `seed_requested`, `seed_used`, `seed_note`;
- `finish_reason`, `mime_returned`, `stored_as`;
- `image_thought_tokens`, `image_usage_json`;
- `text_free_ok`, the no-text acceptance check.

`text_question` and `text_answer` now hold the bank's no-text question and its answer.

Box coordinates are shares of the image's width and height, as [left, top, right, bottom].
