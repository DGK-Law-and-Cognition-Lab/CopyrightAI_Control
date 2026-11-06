# Papers A and B: shared Pavlovia engine

`engine.js` and `style.css` run every Paper A and Paper B study (version 1.6.0, 1 November 2026; versions 1.1.0 to 1.6.0 added the options A1 and B1's revision of 1 November 2026 need, every one opt-in from `config.js`, so a study that sets none of them gets version 1.0's pages and data columns). A study folder (for example `../B1/` or `../A1/`) holds `index.html`, its own `config.js` (all study text, lists and formulas), copies of `engine.js`, `style.css` and `captcha.png` (made by `../tools/sync_engine.sh <study>`), `open_rows.json`, `stimuli/` and a deploy script. Plain JavaScript, no build step, no libraries.

Kept from the genre-study template (`DGK Lab - Scene A Faire Computational/Experiment/Study 1/`): Pavlovia session open and save through the REST API (`PAVLOVIA.init`, `PAVLOVIA.save`, unload beacon), local CSV download when not on Pavlovia, refusal to start on the live site without a Pavlovia session, desktop-only gate, full-screen button, hidden-instruction captcha trap (`captcha.png` says press Q; a hidden line says press Z), paste prevention, the page system with minimum-wait timers, SONA credit routing for numeric ids, demographics and final-question pages (now configured per study). Changed: the captcha comes after consent, and a failed captcha or two failed comprehension attempts are saved and sent to the credit link like a complete session; data are one row per trial.

## Session order

device check, welcome and full screen, consent, captcha, primer, comprehension (one retry, primer shown again; two failures end the session), story, trials in random order (instructed-response item after trial `instructed.afterTrial`; written reason on its own screen after each designated trial), "would" block, story recall, `endPages`, `demographicsPages`, `finalPages`, debriefing, save, credit link.

With `blocks` (A1), trials are in random order within each block, blocks in the configured order, and a block's `before` pages come before its first trial (A1: the follow-up section, then the rule and its recall items). With `viewPage` (A1), each trial is first shown without questions, with the minimum viewing time, then again with its questions. With `trialStory` (A1 since 1.4.0), each trial opens with a text page. With `preScreen` (A1 until 1.2.0, and again since 1.4.0), a screen showing one image alone comes before the trial's other screens.

## What `config.js` must define (`window.STUDY_CONFIG`)

| Key | Content |
| --- | --- |
| `studyCode`, `configVersion`, `pageTitle` | Data file prefix, version string, browser tab title. |
| `stimuliDir`, `openRowsFile`, `nRows` | Image folder, open-rows file, number of rows. |
| `sonaCreditUrlBase`, `creditOnDecline`, `completionCode`, `contact` | Credit link (code appended), whether a decliner is sent to it, code shown when there is no redirect, contact for the debriefing. |
| `dropItems` | Trial question ids to remove (timing-gate remedy); `'would_block'` removes the "would" block. |
| `minViewSeconds` | Minimum time an image is on screen before Next works (counted from image load). |
| `buildRow(k)` | Returns `{row, <rowColumns>..., trials: [{list_position, <trialColumns>...}]}` for row k. |
| `derive(code, row, rnd)` | Per-participant choices from the code (`code` is null for a non-numeric id; use `rnd(n)` then). Must return `option_order` (array of decision option keys), `reason_positions` (list positions with a written reason) and `recall_position`; any other keys listed in `derivedColumns` are recorded. |
| `rowColumns`, `derivedColumns`, `trialColumns` | Which fields of the row, of `derive()` and of each trial go into the data. |
| `trialContent(trial)` | `{heading, plan, statement, images: [{file, caption}]}`; two images give an image pair side by side. |
| `consent` | `heading`, `intro`, `sections: [{title, paragraphs}]`, `agree`, `decline`, optional `url` (a link shown above the choices). |
| `primer`, `story` | `{minSeconds, paragraphs}`. |
| `comprehension` | `{options, items: [{id, text, key}], retryNotice}`. |
| `trialQuestions` | Questions on each trial screen, in order (types below). |
| `reasonQuestion` | The written-reason item (`type: 'text'`). |
| `instructed` | `{id, afterTrial, text, options, pass}`. |
| `would` | `{minViewSeconds, questions}` (a `decision` question and a confidence slider). |
| `recall` | `{id, text, options, correct(trial)}`; shown on `derive().recall_position` without its statement. |
| `endPages`, `demographicsPages`, `finalPages` | Pages `{id, items, shuffleItems, orderColumn, heading, intro}`. |
| `extraColumns`, `finalize(r, trials, rec, get)` | Extra participant columns computed at the end (scores, flags). |
| `debrief` | `{heading, paragraphs}`. |
| `ui` | Every button, notice and screen-furniture string (see `../B1/config.js`). |

Optional keys (1.1.0; A1 uses them, B1 does not):

| Key | Content |
| --- | --- |
| `blocks` | `[{id, before: [pages]}]`. Each trial from `buildRow` carries `block`. A page in `before` is a text page `{id, minSeconds, paragraphs}` (time on screen saved as `<id>_page_ms`) or an item page `{id, items}`. |
| `preScreen` | `{minViewSeconds, content(trial)}`; `content` returns `{lines, images: [{file}]}`. Saves `pre_page_ms`, `pre_image_load_ms`, `pre_image_error`, `pre_min_view_ms`. |
| `trialQuestionsFor(trial, derived)` | The items of one trial's question screen, in order, all taken from `trialQuestions` (which still sets the data columns). Saves `trial_items`. |
| `afterTrialScreens` | `[{id, showIf(trial, derived), questions}]`: a screen of further items after a trial's question screen and before its written reason, on the trials `showIf` picks, with the same images and text. Saves the items like trial items, and `<id>_page_ms`. |
| `trialContent(t).lines` | Lines of text shown above the statement on every screen built from `trialContent` (A1: the reminder line). |
| `pairLayout`, `pairMaxHeight` | `'top'`: an image pair and its statement in a band across the top that stays in view while the questions scroll (`pairMaxHeight`, for example `'40vh'`, caps the image height). |
| `would.preScreen`, `would.preScreenMinViewSeconds` | Each "would" trial is preceded by its `preScreen`; saves `would_pre_page_ms`. A `followUp` on the "would" decision is saved like the trial's. |
| `recall.content(trial)` | What the story-recall screen shows (`{lines, images}`), instead of the trial's image and plan. |

Optional keys (1.2.0, A1's page revision of 1 November 2026; B1 uses none):

| Key | Content |
| --- | --- |
| Text as an array | A question's `text`, a `note`'s `text` and `trialContent(t).statement` may be an array of lines, each shown as its own paragraph (one sentence per line). The engine never splits sentences itself. Strings may hold simple inline HTML such as `<strong>`. |
| `trialContent(t).title`, `.vars` | `title`: a centered line above the image pair on every page built from `trialContent`. `vars`: values put into `{name}` placeholders of that trial's question text (A1: `{phrase}`, the added elements). |
| `pairTextBelow` | With `pairLayout 'top'`, the statement below the pair (title, pair, statement). |
| `viewPage` | Each trial is first shown without questions (page id `view_<n>`), with the minimum viewing time from image load; the question page (`trial_<n>`) then has no minimum. Saves `view_page_ms`, `question_page_ms` (in place of `trial_page_ms`); `image_load_ms`, `image_error`, `min_view_ms` and `trial_shown_at_ms` refer to the view page. |
| `note.className` | `'plain'` (normal text, for a definition) or `'boxed'` (a highlighted box, for a reminder). |
| `reasonQuote` | `{chosen, followUp}`, each with `{label}`: the participant's decision and, when answered, its follow-up, quoted above the written-reason box. Saves `<reason id>_quote`. |
| Revisit page in `blocks[].before` | `{id, revisit(trial, derived), questions, questionsFor(trial, derived)}`: the trials already shown that `revisit` picks, again in the order first seen, each on its own page with the trial's title, images and statement and its items. Answers go on that trial's row (columns from `questions`), with `<id>_order` and `<id>_page_ms`. |
| `pages` on a revisit spec (1.3.0) | `[{id, questions, questionsFor(trial, derived), quoteBefore}]`: several pages per picked trial, all shown before the next trial's. Each page saves `<page id>_page_ms`; the spec saves `<spec id>_order`. A page whose items are all dropped is skipped. |
| `quoteBefore` (1.3.0) | On such a page, the id of the item above which the trial's decision is quoted (`reasonQuote` gives the lines). Saves `<item id>_quote`. |
| `dropGroup` on an item (1.3.0) | An item whose `dropGroup` is listed in `dropItems` is removed, like an item listed by its id (A1: `would_block` removes the "would" line, item and confidence from the follow-up section). |
| `reasonQuestion`, `would` optional (1.3.0) | Without `reasonQuestion` there is no written-reason page inside a trial and no `has_reason` or in-trial reason columns; without `would` there is no "would" block and no `would_*` block columns (A1 asks both in its follow-up section). |
| `trialStory(t)` (1.4.0) | `{paragraphs, minSeconds}`: a text page before each trial (A1: how Alex made the first image). Saves `story_page_ms` on the trial's row. |
| `questionLayout: 'side'` (1.4.0) | On pages with questions and an image pair: the title and the pair, one image above the other, in a column that stays in view, sized so both images fit beside the Next row; the statement (in a light box) and the questions beside it. Below 900 pixels wide the column sits above the questions. Pages without questions keep `pairLayout`. |
| `wide` on an item page (1.4.0) | The page uses the wide layout (A1: the agreement grids of the two end scales). |
| One image in `pairLayout: 'top'` and `questionLayout: 'side'` (1.5.0) | B1's walk-through: the page of what was done with one large image, and the question page with the image in a column that stays in view. |
| `derived.would_positions` (1.5.0) | The trials the "would" block shows again; without it, the written-reason trials, as before. |
| `recall.lastTrial`, `recall.afterTrials`, `recall.fromTrial(t)`, `recall.content(t).maxHeight` (1.5.0) | Story recall about the last trial shown, right after it and before the "would" block; `fromTrial` gives the fields recorded once the order is drawn; `maxHeight` caps the image's height on the recall page. |
| `sideTextUnderImage`, `viewPageShowsPlan: false` (1.6.0) | B1's question pages: under the image, in the column that stays in view, the heading and plan (the prompt) and then the statement (what was done), with the questions alone beside them; the what-was-done page leaves the prompt out. |
| Two wordings of one item (1.7.0) | `trialQuestions` may hold two items with the same id (A1: "the second image" and, on no-change trials, "this image"); `trialQuestionsFor` picks one per trial; the id gets one set of data columns, from its first wording; the written-reason quote uses the trial's wording. |
| `would.intro` | `{id, paragraphs}`: a text page opening the "would" block; saves `<id>_page_ms`. |

## Question types

| `type` | Fields | Data |
| --- | --- | --- |
| `decision` | `text`, `options: {whole, part, refuse}` (labels), optional `followUp: {id, text, options, showIf}` shown and required only after the option `showIf` | key chosen, `_display_pos`, follow-up id |
| `choice` | `text`, `options: [{value, label}]`, optional `shuffle`, `fixedLast`, `orderColumn`, `key` (adds `_correct`) | value |
| `scale` | `text`, `points: [{value, label}]`, optional `anchors: [low, high]` (1-to-5 labeled, 1-to-7 anchored) | value |
| `slider` | `text`, `left`, `right`, optional `min`, `max` (default 0 to 100); no handle until clicked | integer |
| `grid` | `text`, `rows: [{id, label}]`, `columns: [{value, label}]` (Yes / No / Not sure, one row each) | `<id>_<row id>` |
| `text` | `text`, `rows`; pasting and dropping blocked and counted | text, `_chars`, `_paste_attempts` |
| `note` | `text` shown among the items (a shared stem); no answer | none |
| `shorttext`, `number`, `checkbox` | demographics | value (`;`-joined for checkboxes) |

Every answer is required. Trial items record `_rt_ms`, `_rt_last_ms` and `_n_changes`; other items record `_rt_ms`.

## Data

One CSV per session, one row per trial shown, participant columns repeated; one row when a session ends before the trials. The column order is fixed by `columns()` in `engine.js`, so every file of a study has the same header. The engine computes `excl_comprehension`, `excl_captcha`, `excl_instructed`, `excl_recall` and `excl_any_in_page`; the speed and earlier-participation exclusions need other sessions and are applied by `../tools/update_open_rows.py`.

## Test mode

`?test=1&code=12345` answers every page automatically (comprehension, instructed-response and recall correctly unless `test_fail` says otherwise), shrinks every minimum time to 20 ms, never follows a SONA redirect, and puts the CSV in `<pre id="csv-dump">` as well as downloading it. `test_fail=comp|comp1|captcha|instructed|recall|decline`; `auto=fill|off`; `row=K` forces a row. With `test=1` or an id beginning PILOT or TEST, `window.ENGINE_DEBUG` exposes the state for inspection.

## Tools (`../tools/`)

| Script | Use |
| --- | --- |
| `sync_engine.sh <study>` | Copy `engine.js`, `style.css`, `captcha.png` into a study folder. |
| `update_open_rows.py` | Daily: count analyzable participants per row from a Pavlovia export, apply the exclusions, rewrite `open_rows.json`, report the internal-pilot gates. Add a study to its `STUDIES` table. |
| `daily_update.sh <study>` | Clone the Pavlovia project, run the counter on `data/`, push only `open_rows.json`. |
| `install_images.sh <study>` | Copy a study's accepted images into its `stimuli/` (B1 from `setB/web/`, A1 from `setA/web/`), checking each copy. |
| `make_placeholders.py` | Grey placeholder images for B1. |
| `run_headless_tests.py` | Run many automatic sessions in headless Chrome and save their CSVs (`--study B1` or `--study A1`). |
| `test_formulas_B1.py`, `test_formulas_A1.py` | Recompute a study's lists and formulas from its registration and check saved sessions and documented columns. |
| `check_strings.py`, `dump_config.js` | Compare every participant-facing string with its source. |
| `session_length_B1.py`, `session_length_A1.py` | Session length by the design record's timing rule. |

## Not yet in the engine (needed by later studies)

Per-trial belief checks shown only on some cells (B3: use `trialQuestionsFor`); "would" trials on unseen scenes (B2, if its registration keeps them); B2's match and choice checks and per-executor end items. A1's blocks, rule paragraph and recall items, first-image screen, per-trial items and "would" follow-up are in 1.1.0; its two-page trials, titled pages, lines of text, quoted answer, revisit pages and introductory pages in 1.2.0; the follow-up section's several pages per revisited trial, quoted decision above a named item and drop groups in 1.3.0; the story page before each trial, the side layout of the question pages and wide item pages in 1.4.0.
