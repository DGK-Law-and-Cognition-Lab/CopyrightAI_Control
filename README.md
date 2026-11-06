# CopyrightAI_Control: Paper B, Study 1 (B1)

Which of a person's acts make an image from an AI image generator their own work? Each participant reads about twelve images, each made from a prompt by an AI image generator, and is told how it came about: another artist made it, or Alex wrote one prompt, spent hours on routine work, picked one of about 100 images, revised his prompt about 100 times, or let the generator revise it on its own. The image is held fixed; only the story changes. Participants say what the U.S. Copyright Office should do with Alex's application and how much of the image is his own creative work.

The study runs on Pavlovia for the UCLA Psychology subject pool (SONA) in UCLA's Fall 2026
quarter, under IRB #24-001292. Its preregistration is in `Docs/Paper Two/_source/Prereg_B1.md`
(with a Word copy in `Docs/Paper Two/Preregistrations/`). Participant data are not here yet; they
are added after collection.

## What is here

| Folder | What it holds |
|---|---|
| `Docs/Paper Two/` | The preregistration, the prompt bank (every prompt, edit phrase and rule used to make the images), the change specification that records every screen text (`_internal_notes/`), and the script that makes the Word copy |
| `Docs/IRB/`, `Analysis/R Analysis Pipeline/Study 1/qualtrics/` | The IRB-approved consent and debriefing forms and Paper One's Study 1 survey file, which the page-text check compares the pages with |
| `Stimuli/Paper Two/Pavlovia/B1/` | The study's web pages as they run on Pavlovia: `index.html`, `config.js` (every text, item and list), the stimuli and the README that documents every data column |
| `Stimuli/Paper Two/Pavlovia/engine/` | The page code shared by the lab's Paper Two studies |
| `Stimuli/Paper Two/Pavlovia/tools/` | Checks: page text against the preregistration, automatic test sessions, the formula checks, session length, the daily list update |
| `Stimuli/Paper Two/setB/` | The image set: every accepted image, `manifest.csv` (every candidate with its instruction, model, settings, checks and SHA-256), `thresholds.json` and the earlier accepted sets |
| `Stimuli/Paper Two/scripts/` | The scripts that made and checked the images |
| `Analysis/Paper Two/Power/` | The sample-size simulation and its results |

Rejected candidate images are not in this repository (they are large); they are archived on
Zenodo, and the SHA-256 checksums in `manifest.csv` verify every file.

## How to run it from a fresh copy

Needs Python 3.10 or later, Node.js, Google Chrome, and for the simulation R 4.3 or later with
lme4 and lmerTest.

1. See the study as a participant would, with every answer filled in automatically:
   `cd "Stimuli/Paper Two/Pavlovia/B1" && python3 -m http.server 8000`, then open
   `http://localhost:8000/index.html?test=1&code=12345`. Leave out `test=1&code=12345` to
   answer yourself.
2. Check that every text on the pages matches the preregistration:
   `python3 "Stimuli/Paper Two/Pavlovia/tools/check_strings.py" --study B1`. It should end with "0 fail". About 46
   strings are listed as new: the page code's own buttons and messages, which come from the lab's
   page template in another project and so have no source here.
3. Run complete automatic sessions and check every formula and data column:
   `python3 "Stimuli/Paper Two/Pavlovia/tools/run_headless_tests.py" --study B1 --out sessions_B1`, then
   `python3 "Stimuli/Paper Two/Pavlovia/tools/test_formulas_B1.py" --csv-dir sessions_B1`.
4. Rerun the sample-size simulation: `Rscript "Analysis/Paper Two/Power/sim_B1.R"`
   (about 10 to 20 minutes on 11 cores; `--quick` for a short check).
5. Remake the images (needs an API key for the image model, in an environment variable; see
   the scripts' headers): the scripts in `Stimuli/Paper Two/scripts/`. Image models do not
   return the same image twice, so a rerun makes new candidates; `manifest.csv` records the
   ones used.

## Licence

Code (.R, .py, .js, .sh) under the MIT licence; everything else under CC BY 4.0. See `LICENSE`
and `LICENSE-CC-BY-4.0.md`.
