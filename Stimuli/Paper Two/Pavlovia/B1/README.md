# Paper B, Study 1 (B1): Pavlovia experiment

Plain-JavaScript Pavlovia experiment for B1 ("Prompting, the work after the prompt, and lay authorship"), built on the shared engine in `../engine/` (version 1.6.0). No build step and no libraries. Every participant-facing study string comes from the preregistration, `Docs/Paper Two/_source/Prereg_B1.md` (version of 1 November 2026), whose page text follows the change specification `Docs/Paper Two/_internal_notes/B1_page_revision_2026-11-01.md` (David's walk-through of 1 November 2026); the plans, shown to participants as the prompt Alex or another artist wrote, come from `Docs/Paper Two/Paper_Two_Prompt_Bank.md` (Set B, plan version 1).

## Before launch

1. **Images.** `stimuli/` must hold the 24 files of `Stimuli/Paper Two/setB/web/` (`SB-P1_V1.jpg`, `SB-P1_I2.jpg`, and so on; 1264 × 848 JPEG, Nano Banana Pro's own 3:2 size, 126 to 327 KB each). The Nano Banana Pro set was installed on 27 October 2026 with `../tools/install_images.sh B1`, replacing the superseded GPT Image 2.5 Flare set. After the scale-cut correction the same day, SB-P6_I2.jpg and SB-N4_I2.jpg were replaced and all 24 were reinstalled. After the plan-faithfulness amendment, five files were replaced. Then, because SB-N3 I2 failed the prompt bank's full rescue rule, the no-person reserve **SB-R2 (The pier) replaced SB-N3** in SB-N3's position in the scene order. `config.js` holds SB-R2's plan version 1, verbatim from the bank, and the files are `SB-R2_V1.jpg` and `SB-R2_I2.jpg`. The scene lists in `../tools/install_images.sh`, `../tools/test_formulas_B1.py` and `../tools/make_placeholders.py` were changed the same way; no check was changed. On 27 October 2026 `../tools/install_images.sh B1` installed all 24 accepted files, byte-identical to `setB/web/`, and removed the placeholder marker. The two SB-N3 files that remained in `stimuli/` were moved, not deleted, to `setB/superseded_SB-N3_replaced_by_SB-R2/removed_from_pavlovia_stimuli/`. After the swap:

- `../tools/check_strings.py`: 264 pass, 0 fail.
- `../tools/run_headless_tests.py`: 40 of 40 scenarios produced output, with no image error in 444 trial rows.
- `../tools/test_formulas_B1.py`: all checks passed.
- Local test-mode sessions on a V1 row and an I2 row loaded all 24 files with no image error. If any Set B file is ever remade, run that script again. If the folder ever has to be rebuilt before the images exist, `../tools/make_placeholders.py` writes grey placeholders with the scene and file name on each, plus a marker file `stimuli/PLACEHOLDER_IMAGES.txt`; placeholders must be replaced by the `setB/web/` files, and the deploy script refuses to push while the marker exists.
2. **SONA credit link.** In `config.js`, set `SONA_CREDIT_URL_BASE` to the B1 listing's credit-granting URL, ending in `survey_code=`. While it is empty, a SONA participant ends on the completion page (code `ARTB1`) and is not credited automatically.
3. **Pavlovia project.** Create a new project on Pavlovia for B1. Then, from this folder, run `./deploy_to_pavlovia.sh`. It asks for the project path (`owner/name`), clones `https://gitlab.pavlovia.org/<owner>/<name>.git`, checks that the clone points there, copies the page files, shows what changes, and pushes only after you type the project's name. It never pushes `config.json` (Pavlovia serves its own) and never touches `data/`. It saves the path in `.pavlovia_project` (local only) for the daily script. On the dashboard, set the project to RUNNING, covered by the UCLA license, with results saved as CSV.
4. **Pilot run on Pavlovia.** `https://run.pavlovia.org/<owner>/<name>/index.html?participant=PILOT_DK1` (no SONA, no credit; flagged `is_test`). A file `data/PB_B1_PILOT_DK1_SESSION_<date>.csv` should appear in the repository. An automatic run: `...index.html?test=1&code=12345`.
5. **SONA study URL.** `https://run.pavlovia.org/<owner>/<name>/index.html?participant=%SURVEY_CODE%`. SONA fills in each participant's numeric survey code; a numeric id is treated as a SONA session, so the credit link is used at the end. Never add `row`, `code` or `test` to the SONA link.
6. **Earlier participants.** Put the SONA codes of everyone who took part in Paper One, a Paper A or Paper B study, or Prompt Position in `../tools/prior_codes.txt` (one per line, or comma separated). The daily script excludes them. The SONA prescreen restrictions remain the main safeguard.

## Daily during data collection

`../tools/daily_update.sh B1` clones the project, runs `../tools/update_open_rows.py` on its `data/` folder, rewrites `open_rows.json` so that rows with 4 analyzable participants close (target 96), and pushes only `open_rows.json` after you type the project's name. It prints counts only (per row, per exclusion, recruited against the cap of 119) and, once 40 participants are analyzable, the three internal-pilot gates (belief at least 70 percent "Yes" or "Partly"; recall at least 80 percent correct; median session at most 30 minutes). If the cap is reached or every row is full, it says to close the SONA listing. After the end date, run `python3 ../tools/update_open_rows.py --study B1 --data <data folder> --target 3` so rows below the fallback of 3 per row (72 in all) stay open, until the last day of UCLA's Winter 2027 quarter at the latest.

If the timing gate fails, set `DROP_ITEMS` in `config.js` to `['control']`, then to `['control', 'would_block']` if needed, and redeploy. Effort is never removed.

## Files

| File | Purpose |
| --- | --- |
| `index.html` | Page shell. Loads `config.js`, then `engine.js`. |
| `config.js` | Everything specific to B1: strings, scenes, cells, the list rule, the per-participant formulas, item lists, debriefing, values to set before launch. |
| `engine.js`, `style.css`, `captcha.png` | Copies of `../engine/` (run `../tools/sync_engine.sh B1` after changing the engine; the deploy script checks they match). |
| `open_rows.json` | The open rows, rewritten daily by `../tools/update_open_rows.py`. Starts with all 24 rows open. |
| `stimuli/` | 24 images, `<scene>_<V1 or I2>.jpg`, copied from `Stimuli/Paper Two/setB/web/`. |
| `deploy_to_pavlovia.sh` | Pushes this folder to the B1 Pavlovia project only. Not itself uploaded. |

## Session

Device check, full screen, consent (the IRB-approved survey consent form, `Docs/IRB/V2_CONSENT FORM_Survey.docx`, the text Paper One's Qualtrics surveys showed; "I consent to this study." or "I do not consent to this study."), captcha trap (the image says press Q; a hidden line says press Z; Z ends the session), primer, three true-or-false comprehension items (one retry after the primer is shown again; a second failure ends the session), the story, twelve trials in random order with the instructed-response item after the third, story recall (about the last trial, right after it), the "would" block, belief, purpose probe, six believability items, experience, the Short GAAIS-10, the anthropocentric creativity beliefs, the copyright quiz, demographics (Paper One's Study 1 items), final questions (Paper One's Study 1 survey and the IRB debriefing form), debriefing, save, SONA credit link. The session takes about 39 minutes and is posted as 45. The primer, story, each trial's pages, registration decision and debriefing show one sentence per line.

Each trial has four pages, nothing else:

1. **Prompt page** (at least 5 seconds; `trialStory`): "**Alex** wrote this prompt for the next image:" or, in cell o, "**Another artist** wrote this prompt for the next image:", then the scene's plan in a box.
2. **What was done** (Next disabled for 8 seconds after the image loads; `viewPage`, `viewPageShowsPlan: false`): the cell's story, in the order it happened, one sentence per line, and below it the image, large, labeled "The image Alex kept".
3. **Question page** (no minimum time; `questionLayout: 'side'`, `sideTextUnderImage`): the image, then the prompt under "The prompt Alex wrote:" or "The prompt another artist wrote:", then what was done, all in a column that stays in view (sized to the window; on very short screens it scrolls inside); beside it the questions, in registered order: registration decision (three lines; options in the participant's order), confidence, authorship share, control (sliders with no handle until clicked), the three aspect rows ("Which parts of this image are Alex's own creative work?" Yes / No / Not sure), effort and creativity (1 to 5, None at all to A great deal; creativity with Paper One's definition below its question).
4. **Written reason**, laid out the same way: the decision quoted ("You chose: “....”") and the reason box; pasting and dropping text are blocked and attempts counted.

Every answer is required. Story recall shows the last trial's image alone below "One more question about the image you just saw." and asks "How was this image made?" with one answer per cell and "I don't remember". The "would" block opens with an introductory page, then shows the two designated trials again in the order first seen, each on one page with the line "This time, the question is what the Office would actually do, not what it should do.", the "would" item and confidence.

Every session that ends early after consent (comprehension failed twice, captcha trap) is saved and sent to the SONA credit link, like a complete session. A participant who declines consent saves nothing; with `CREDIT_ON_DECLINE = true` a SONA participant is still sent to the credit link. A phone or tablet user who says so on the device check is stopped before consent (the template's rule).

## How the registered formulas are implemented

All in `config.js`; `../tools/test_formulas_B1.py` recomputes them independently.

| Registered rule | Implementation |
| --- | --- |
| Row from the SONA code modulo the number of open rows, open rows taken in order of k | `engine.js` `assignRow()`: reads `open_rows.json`, sorts and de-duplicates the listed rows, takes `open[code % n_open]`. If the file cannot be read, every row counts as open (`open_rows_source = fallback_all`); if it lists none, all 24 are used and the daily script tells you to close the listing. A non-numeric id (pilots) gets a random open row. `?row=K` forces row K (testing). |
| List k: rotation q = k mod 12; V1 if k < 12, else I2 | `buildRow(k)`. |
| Position j shows the scene at (j + q) mod 12 of SB-P1, SB-N1, SB-P2, SB-N2, SB-P3, SB-R2, SB-P4, SB-N4, SB-P5, SB-N5, SB-P6, SB-N6 (SB-R2, the no-person reserve, in SB-N3's position since 27 October 2026); cell i (o, a, r, b, c, d) at positions 2i and 2i + 1; one file per scene and composition | `buildRow(k)`; file `<scene>_<composition>.jpg`. |
| Option order: floor(code / 24) mod 3 = 0, 1, 2 gives whole, part, refuse; part, refuse, whole; refuse, whole, part | `derive()`; the same order on the "would" item. Random when the code is not numeric (recorded in `option_order_source`). |
| Written reason on every trial; "would" block on the trials at position 2i for i = k mod 6 and (k + 3) mod 6 | `derive()` gives `reason_positions` (all twelve) and `would_positions`; the engine shows the "would" block on `would_positions`. |
| Story recall about the last trial shown, right after it | `recall.lastTrial` and `recall.afterTrials`: the engine sets `recall_position`, `recall_cell`, `recall_scene` and `recall_file` once the order is drawn; the recall screen shows that trial's image alone. "I don't remember" is wrong. |
| Trial order randomized in the page | Fisher-Yates shuffle of the 12 list positions; `trial_order` records it. |
| Instructed-response item after the third trial | After the third trial's four pages. Only "Somewhat disagree" passes. |
| "Would" block: an introductory page, then the two designated trials again, each with what was done, the line, the "would" item with the same option order, then confidence | Shown in the order the two trials were first seen; no minimum viewing time. |
| Purpose probe: first four options random, "Something else" last; six believability items in random order | Randomized in the page; `purpose_order` and `believability_order` record them. |
| Exclusions computed in the page | `excl_comprehension`, `excl_captcha`, `excl_instructed`, `excl_recall`, `excl_any_in_page`. The two that need other sessions (less than one third of the median completion time; earlier participation) are applied by `../tools/update_open_rows.py`. |

## URL parameters

| Parameter | Effect |
| --- | --- |
| `participant`, `survey_code`, `id` | Participant id (SONA sends `participant=%SURVEY_CODE%`). An id beginning PILOT or TEST is flagged `is_test`. |
| `code` | The numeric code used by the formulas, if different from the id (testing). With `test=1` and no id, the id becomes `TEST_<code>`. |
| `platform` | `sona` or anything else; if absent, a numeric id means SONA. |
| `row` | Forces row 0 to 23 (testing only). |
| `test=1` | Test mode: every page is answered automatically, minimum times shrink to 20 ms, and a whole session runs in under a second. Data are flagged `is_test` and `test_mode`; a SONA redirect is never followed; the CSV is placed in the page (`<pre id="csv-dump">`) and downloaded locally. |
| `test_fail` | With `test=1`: `comp` (fail both comprehension attempts), `comp1` (fail the first only), `captcha`, `instructed`, `recall`, `decline`. |
| `auto` | With `test=1`: `fill` answers each page but leaves Next to you; `off` does nothing. |
| `auto_delay` | With `test=1`: ms between pages (default 5). |
| `__pilotToken` | Added by Pavlovia when piloting. |

## Local test

```
cd "Stimuli/Paper Two/Pavlovia/B1"
python3 -m http.server 8000
```

Open `http://localhost:8000/index.html?test=1&code=12345` (automatic) or `http://localhost:8000/index.html?participant=PILOT_X&code=12345` (by hand). Local runs never contact Pavlovia; the CSV downloads instead.

Checks, from `Stimuli/Paper Two/Pavlovia/`:

```
python3 tools/run_headless_tests.py --study B1 --out /tmp/b1_runs   # 40 automatic sessions in headless Chrome
python3 tools/test_formulas_B1.py --csv-dir /tmp/b1_runs            # lists, formulas, saved data, columns
python3 tools/check_strings.py --study B1                           # every string against its source
python3 tools/session_length_B1.py                                  # timing rule of design record 1.13
```

## Data columns

One CSV per session, `data/PB_B1_<id>_SESSION_<date>.csv`, with one row per trial (12 rows), in the order the trials were shown. Participant-level columns repeat on every row. A session that ended before the trials (comprehension failed twice, captcha) has one row with the trial columns empty. Times are milliseconds. `_rt_ms` is the time from the screen appearing to the first answer to that item; `_rt_last_ms` to the last change; `_n_changes` counts changes. Lists inside a cell are separated by `;`.

### Session and assignment

| Column | Meaning |
| --- | --- |
| `study_code` | `PB_B1`. |
| `engine_version` | Engine version string. |
| `config_version` | B1 configuration version string. |
| `participant_id` | SONA survey code (or PILOT/TEST id). |
| `code` | Numeric code used by the formulas (empty if the id is not numeric). |
| `is_test` | true for test mode or a PILOT/TEST id; dropped before analysis. |
| `test_mode` | true when `test=1`. |
| `test_fail` | Failure injected in test mode, if any. |
| `platform` | `sona`, `test`, or other. |
| `platform_source` | How the platform was decided (`numeric_id`, `url`, `test_mode`, `none`). |
| `pavlovia_session` | `open` (saved to Pavlovia), `local`, or `failed`. |
| `session_complete` | true only when the debriefing was reached. |
| `exit_reason` | `complete`, `comprehension_failed` or `captcha_failed`. |
| `start_time` | ISO time the page loaded. |
| `end_time` | ISO time of the end (or early exit). |
| `total_duration_ms` | Page load to end. Used for the one-third-of-the-median exclusion. |
| `row` | Row k (0 to 23); in B1 a row is a list. |
| `list` | List k (same as `row`). |
| `rotation` | k mod 12. |
| `composition` | V1 (k < 12) or I2. |
| `n_rows` | 24. |
| `dropped_items` | Items removed by the timing-gate remedy (`control`, `would_block`), if any. |
| `open_rows` | The open rows read from `open_rows.json`, in order of k. |
| `n_open_rows` | Number of open rows. |
| `open_rows_index` | code mod n_open_rows (empty for a forced or random row). |
| `open_rows_source` | `file` or `fallback_all` (file unreadable); `_none_open_used_all` appended if the file listed no row. |
| `open_rows_updated` | The `updated` stamp of `open_rows.json`. |
| `assignment_source` | `code_mod_open_rows`, `url_row` or `random_no_numeric_code`. |
| `option_order_index` | floor(code / 24) mod 3. |
| `option_order` | Registration options in display order (`whole`, `part`, `refuse`). |
| `option_order_source` | `floor(code/24) mod 3` or `random_no_numeric_code`. |
| `would_cell_indices` | i = k mod 6 and (k + 3) mod 6, ascending. |
| `would_cells` | The two cells shown again in the "would" block. |
| `would_positions` | Their list positions (2i). |
| `recall_cell` | The cell of the last trial shown (the story-recall trial). |
| `recall_position` | Its list position. |
| `recall_scene` | Scene of the recall trial. |
| `recall_file` | File of the recall trial. |
| `trial_order` | List positions in the order shown. |
| `n_trials` | 12. |

### Trial (one row per trial)

| Column | Meaning |
| --- | --- |
| `trial_position` | 1 to 12, order of presentation. |
| `list_position` | 0 to 11, position j in the list. |
| `cell` | o, a, r, b, c or d. |
| `cell_index` | 0 to 5. |
| `scene` | SB-P1 ... SB-N6, with SB-R2 in place of SB-N3. |
| `scene_has_person` | true for SB-P scenes. |
| `file` | Image file shown. |
| `story_page_ms` | Time on the trial's prompt page (at least 5 s). |
| `trial_shown_at_ms` | Time since page load when the trial's what-was-done page appeared. |
| `view_page_ms` | Time on the what-was-done page. |
| `image_load_ms` | Time until the image had loaded (the 8-second minimum starts then). |
| `image_error` | true if the image failed to load. |
| `min_view_ms` | 8000. |
| `question_page_ms` | Time on the question page (no minimum). |
| `decision` | Registration decision: `whole`, `part` or `refuse`. |
| `decision_rt_ms` | Time to first answer. |
| `decision_rt_last_ms` | Time to last change. |
| `decision_n_changes` | Number of changes. |
| `decision_display_pos` | Screen position (1 to 3) of the chosen option. |
| `confidence` | 0 to 100. |
| `confidence_rt_ms` | Time to first answer. |
| `confidence_rt_last_ms` | Time to last change. |
| `confidence_n_changes` | Number of value changes (dragging counts each step). |
| `share` | Authorship share, 0 to 100 (primary outcome). |
| `share_rt_ms` | Time to first answer. |
| `share_rt_last_ms` | Time to last change. |
| `share_n_changes` | Number of value changes. |
| `control` | 0 to 100 (empty if dropped). |
| `control_rt_ms` | Time to first answer. |
| `control_rt_last_ms` | Time to last change. |
| `control_n_changes` | Number of value changes. |
| `aspect_placement` | "Where things sit in the picture": Yes, No or Not sure. |
| `aspect_placement_rt_ms` | Time to first answer. |
| `aspect_placement_rt_last_ms` | Time to last change. |
| `aspect_placement_n_changes` | Number of changes. |
| `aspect_color_light` | "The colors and the light". |
| `aspect_color_light_rt_ms` | Time to first answer. |
| `aspect_color_light_rt_last_ms` | Time to last change. |
| `aspect_color_light_n_changes` | Number of changes. |
| `aspect_subject` | "What the image shows". |
| `aspect_subject_rt_ms` | Time to first answer. |
| `aspect_subject_rt_last_ms` | Time to last change. |
| `aspect_subject_n_changes` | Number of changes. |
| `effort` | 1 (None at all) to 5 (A great deal). |
| `effort_rt_ms` | Time to first answer. |
| `effort_rt_last_ms` | Time to last change. |
| `effort_n_changes` | Number of changes. |
| `creativity` | 1 (None at all) to 5 (A great deal). |
| `creativity_rt_ms` | Time to first answer. |
| `creativity_rt_last_ms` | Time to last change. |
| `creativity_n_changes` | Number of changes. |
| `has_reason` | true on every trial. |
| `written_reason` | The text. |
| `written_reason_rt_ms` | Time to the first keystroke. |
| `written_reason_chars` | Length of the text. |
| `written_reason_paste_attempts` | Blocked paste attempts. |
| `written_reason_page_ms` | Time on the written-reason screen. |
| `written_reason_quote` | The decision quoted above the box ("You chose: “....”"), tags removed. |
| `would_shown` | true if the trial was shown again in the "would" block. |
| `would_order` | 1 or 2. |
| `would_page_ms` | Time on that screen. |
| `would_decision` | "Would" item: `whole`, `part` or `refuse`. |
| `would_decision_rt_ms` | Time to first answer. |
| `would_decision_display_pos` | Screen position of the chosen option. |
| `would_confidence` | 0 to 100. |
| `would_confidence_rt_ms` | Time to first answer. |
| `is_recall_trial` | true on the trial asked about in story recall. |

### Participant measures

| Column | Meaning |
| --- | --- |
| `device_type` | desktop or mobile (user agent). |
| `device_self_report` | 1 = desktop or laptop. |
| `user_agent` | Browser user agent. |
| `screen_width` | Screen width in pixels. |
| `screen_height` | Screen height in pixels. |
| `fullscreen_entered` | yes if the full-screen button was used. |
| `atlas_detected` | true if an automated browser was detected (session blocked). |
| `consent` | agreed. |
| `consent_time` | ISO time of consent. |
| `captcha_response` | q or z. |
| `captcha_pass` | true for q. |
| `captcha_rt_ms` | Time to the key press. |
| `comp1_attempt1` | Comprehension item 1, first attempt (True or False). |
| `comp1_attempt1_rt_ms` | Time to first answer. |
| `comp1_attempt1_correct` | Matches the key. |
| `comp2_attempt1` | Item 2, first attempt. |
| `comp2_attempt1_rt_ms` | Time to first answer. |
| `comp2_attempt1_correct` | Matches the key. |
| `comp3_attempt1` | Item 3, first attempt. |
| `comp3_attempt1_rt_ms` | Time to first answer. |
| `comp3_attempt1_correct` | Matches the key. |
| `comp_attempt1_pass` | All three correct on the first attempt. |
| `comp1_attempt2` | Item 1, retry (empty if not needed). |
| `comp1_attempt2_rt_ms` | Time to first answer. |
| `comp1_attempt2_correct` | Matches the key. |
| `comp2_attempt2` | Item 2, retry. |
| `comp2_attempt2_rt_ms` | Time to first answer. |
| `comp2_attempt2_correct` | Matches the key. |
| `comp3_attempt2` | Item 3, retry. |
| `comp3_attempt2_rt_ms` | Time to first answer. |
| `comp3_attempt2_correct` | Matches the key. |
| `comp_attempt2_pass` | All three correct on the retry. |
| `comp_failed_twice` | true if both attempts failed (session ended). |
| `instructed` | Answer to the instructed-response item. |
| `instructed_rt_ms` | Time to first answer. |
| `instructed_pass` | true only for "Somewhat disagree". |
| `instructed_after_trial` | 3. |
| `would_block_shown` | false if the block was dropped. |
| `would_intro_page_ms` | Time on the "would" block's introductory page (empty if the block was dropped). |
| `recall` | Story recall answer: o, a, r, b, c, d or dont_remember. |
| `recall_rt_ms` | Time to first answer. |
| `recall_correct_answer` | The designated trial's cell. |
| `recall_correct` | true if the answer matches it. |
| `belief` | Yes, Partly or No. |
| `belief_rt_ms` | Time to first answer. |
| `purpose_order` | Purpose-probe options in display order. |
| `purpose` | way_made (the true purpose), quality_liking, tell_ai_photo, longer_plans or something_else. |
| `purpose_rt_ms` | Time to first answer. |
| `believability_order` | Believability items in display order. |
| `believe_o` | Found online, 1 to 7. |
| `believe_o_rt_ms` | Time to first answer. |
| `believe_a` | One prompt, 1 to 7. |
| `believe_a_rt_ms` | Time to first answer. |
| `believe_r` | 10 hours of routine work, 1 to 7. |
| `believe_r_rt_ms` | Time to first answer. |
| `believe_b` | Regenerated about 100 times, 1 to 7. |
| `believe_b_rt_ms` | Time to first answer. |
| `believe_c` | Revised the prompt about 100 times, 1 to 7. |
| `believe_c_rt_ms` | Time to first answer. |
| `believe_d` | Tool revised on its own, 1 to 7. |
| `believe_d_rt_ms` | Time to first answer. |
| `exp_ai_tool` | Never, Once or twice, Sometimes, Often. |
| `exp_ai_tool_rt_ms` | Time to first answer. |
| `exp_photo` | No, Sometimes, Often, Professionally. |
| `exp_photo_rt_ms` | Time to first answer. |
| `exp_draw_paint` | No, Sometimes, Often, Professionally. |
| `exp_draw_paint_rt_ms` | Time to first answer. |
| `gaais_pos7` | Short GAAIS-10 item 7 of the full GAAIS (Positive: interested in using AI systems in daily life), 1 Strongly disagree to 5 Strongly agree, as answered. |
| `gaais_pos7_rt_ms` | Time to first answer. |
| `gaais_neg8` | Short GAAIS-10 item 8 of the full GAAIS (Negative: AI is sinister), 1 Strongly disagree to 5 Strongly agree, as answered. |
| `gaais_neg8_rt_ms` | Time to first answer. |
| `gaais_neg9` | Short GAAIS-10 item 9 of the full GAAIS (Negative: AI might take control of people), 1 Strongly disagree to 5 Strongly agree, as answered. |
| `gaais_neg9_rt_ms` | Time to first answer. |
| `gaais_neg10` | Short GAAIS-10 item 10 of the full GAAIS (Negative: AI is dangerous), 1 Strongly disagree to 5 Strongly agree, as answered. |
| `gaais_neg10_rt_ms` | Time to first answer. |
| `gaais_pos11` | Short GAAIS-10 item 11 of the full GAAIS (Positive: positive impacts on wellbeing), 1 Strongly disagree to 5 Strongly agree, as answered. |
| `gaais_pos11_rt_ms` | Time to first answer. |
| `gaais_pos12` | Short GAAIS-10 item 12 of the full GAAIS (Positive: AI is exciting), 1 Strongly disagree to 5 Strongly agree, as answered. |
| `gaais_pos12_rt_ms` | Time to first answer. |
| `gaais_neg15` | Short GAAIS-10 item 15 of the full GAAIS (Negative: shiver with discomfort about future uses), 1 Strongly disagree to 5 Strongly agree, as answered. |
| `gaais_neg15_rt_ms` | Time to first answer. |
| `gaais_pos17` | Short GAAIS-10 item 17 of the full GAAIS (Positive: society will benefit), 1 Strongly disagree to 5 Strongly agree, as answered. |
| `gaais_pos17_rt_ms` | Time to first answer. |
| `gaais_pos18` | Short GAAIS-10 item 18 of the full GAAIS (Positive: would like to use AI in own job), 1 Strongly disagree to 5 Strongly agree, as answered. |
| `gaais_pos18_rt_ms` | Time to first answer. |
| `gaais_neg19` | Short GAAIS-10 item 19 of the full GAAIS (Negative: people like me will suffer), 1 Strongly disagree to 5 Strongly agree, as answered. |
| `gaais_neg19_rt_ms` | Time to first answer. |
| `acb_uniquely_human` | Anthropocentric creativity beliefs, "Creativity is a uniquely human characteristic.", 1 Strongly disagree to 7 Strongly agree. |
| `acb_uniquely_human_rt_ms` | Time to first answer. |
| `acb_differentiate` | Anthropocentric creativity beliefs, "Humans differentiate themselves from other species because of their ability to create.", 1 Strongly disagree to 7 Strongly agree. |
| `acb_differentiate_rt_ms` | Time to first answer. |
| `acb_essence` | Anthropocentric creativity beliefs, "Creativity is the essence of being human.", 1 Strongly disagree to 7 Strongly agree. |
| `acb_essence_rt_ms` | Time to first answer. |
| `acb_core` | Anthropocentric creativity beliefs, "Creativity is at the core of being human.", 1 Strongly disagree to 7 Strongly agree. |
| `acb_core_rt_ms` | Time to first answer. |
| `acb_only_humans` | Anthropocentric creativity beliefs, "Only humans have the ability to be creative.", 1 Strongly disagree to 7 Strongly agree. |
| `acb_only_humans_rt_ms` | Time to first answer. |
| `know1` | "A work must be registered before it is protected." (key False). |
| `know1_rt_ms` | Time to first answer. |
| `know1_correct` | Matches the key. |
| `know2` | Ideas as well as expression (key False). |
| `know2_rt_ms` | Time to first answer. |
| `know2_correct` | Matches the key. |
| `know3` | Working harder (key False). |
| `know3_rt_ms` | Time to first answer. |
| `know3_correct` | Matches the key. |
| `know4` | Changes to an unprotected work (key True). |
| `know4_rt_ms` | Time to first answer. |
| `know4_correct` | Matches the key. |
| `know5` | A machine as legal author (key False). |
| `know5_rt_ms` | Time to first answer. |
| `know5_correct` | Matches the key. |
| `age` | Years. |
| `age_rt_ms` | Time to first keystroke. |
| `gender` | Male, Female, Other, Prefer not to say. |
| `gender_rt_ms` | Time to first answer. |
| `race` | Selected options, `;`-separated. |
| `race_rt_ms` | Time to first answer. |
| `native_language` | Free text. |
| `native_language_rt_ms` | Time to first keystroke. |
| `art_training` | Paper One's five levels of formal artistic training. |
| `art_training_rt_ms` | Time to first answer. |
| `seriousness` | "No, I didn't" or "Yes, I did". |
| `seriousness_rt_ms` | Time to first answer. |
| `fullscreen_maintained` | "No, it wasn't." or "Yes, it was.". |
| `fullscreen_maintained_rt_ms` | Time to first answer. |
| `feedback_procedure` | Free text (or NA). |
| `feedback_procedure_rt_ms` | Time to first keystroke. |
| `feedback_procedure_chars` | Length. |
| `feedback_procedure_paste_attempts` | Blocked paste attempts. |
| `feedback_other` | Free text (or NA). |
| `feedback_other_rt_ms` | Time to first keystroke. |
| `feedback_other_chars` | Length. |
| `feedback_other_paste_attempts` | Blocked paste attempts. |
| `knowledge_score` | Number of the five quiz items answered correctly. |
| `purpose_chose_true` | true if the true purpose was chosen (for the robustness rerun). |
| `gaais_positive` | Mean of the five Positive Short GAAIS-10 items (1 to 5); empty unless all were answered. |
| `gaais_negative` | Mean of the five Negative items reverse-scored (6 minus the answer), so that higher means more forgiving of AI's drawbacks, as the scale's authors score it. |
| `acb_score` | Mean of the five anthropocentric creativity belief items (1 to 7). |
| `excl_comprehension` | Failed the comprehension items twice. |
| `excl_captcha` | Failed the captcha trap. |
| `excl_instructed` | Failed the instructed-response item. |
| `excl_recall` | Wrong story recall ("I don't remember" counts as wrong). |
| `excl_any_in_page` | Any of the four above. Not included: the speed and earlier-participation rules, applied by `../tools/update_open_rows.py`. |
| `page_timestamps` | JSON list of `{p, id, t}`: page index, page id, ms since load. |
| `n_pages` | Pages built for the session. |
