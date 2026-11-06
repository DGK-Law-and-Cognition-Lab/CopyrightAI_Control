# B1 page revision, 1 November 2026

David walked through B1 on Pavlovia on 1 November 2026, after A1's revision, and asked for the same changes: a walk-through of each image, one sentence per line, a clearer story, "prompt" rather than "plan", A1's primer, amount labels, a written reason on every image, an easier story recall, and A1's debriefing and end scales. This file fixes every change and every new participant-facing string. It is the source for the registration edits (Prereg_B1.md), the design record entry 12.29 and the page code (Pavlovia/B1/config.js, engine 1.5.0). Strings in quotation marks are verbatim; `**...**` marks bold.

His decisions (AskUserQuestion, 1 November 2026): in cell r, Alex spends the 10 hours fixing a generator that keeps crashing ("Fixing the generator"); the aspect question is reworded, not dropped; story recall asks about the image just seen; all six believability items stay. And, in his words: "Walk through: show the prompt, new page, show what was done, and then new page ask questions with what was done. We need more story with each sentence as a new paragraph. Input the two new scales as well."

Unchanged: the scenes, plans, images, lists, rotations, compositions, cells and their order, option orders, the measures and their order on the question page, the comprehension items, captcha, device check, instructed-response item (after the third trial), purpose probe, believability items (reworded only), knowledge quiz, demographics and final questions; every confirmatory test, model, bound, criterion, sample size and simulation file. No simulation is rerun.

## 1. Primer

A1's, one sentence per line: "In this study you will see images and read how they were made." / "A person can apply to the U.S. Copyright Office to register a work as their own." / "The Office reviews each application and decides whether to register the work." / "Registering a work does not sell it." / "It creates a public record that names the work's author." / "You will be asked what the Office should do with some applications."

## 2. Story

"Alex is a digital artist." / "He makes images with an artificial intelligence (AI) image generator, a program that makes an image from a written description called a prompt." / "The generator makes a different image each time it runs, even from the same prompt." / "For most images, Alex writes his own prompt." / "For some, he uses an image that another artist made and posted online." / "He never changes an image by hand." / "Before each image you will be told how it was made." / "For each image, you will also be asked to explain your answer."

The third line answers "why is the tool generating versions?": an AI image generator gives a different image each run, so running one prompt many times and keeping the best is common.

## 3. Each trial: four pages

1. Prompt page, at least 5 seconds: "**Alex** wrote this prompt for the next image:" (cells a to d) or "**Another artist** wrote this prompt for the next image:" (cell o), then the scene's plan in a box. Participants see the plan as the prompt; in cell c it is his first prompt, which he then rewrites.
2. What was done, at least 8 seconds from image load: the cell's story, one sentence per line, then the image below it, large, labeled "The image Alex kept".
3. Question page, no minimum: the image in a column that stays in view; what was done in a light box and the questions beside it.
4. Written reason, laid out the same way.

What was done, verbatim, one sentence per line (word counts o 55, a 51, r 53, b 49, c 53, d 53; contrasts differ by at most five words):

- o: "Another artist typed the prompt into an AI image generator." / "The generator made one image from it, and the artist posted the image online." / "Alex found the image online." / "He spent about half an hour on it, most of it saving and backing up the file." / "The image matches the prompt, and Alex kept it."
- a: "Alex typed his prompt into the AI image generator." / "The generator needed some setting up before it would run." / "He spent about half an hour on it, most of it on this setup." / "Then the generator made one image from his prompt." / "The image matches his prompt, and he kept it."
- r: "Alex typed his prompt into the AI image generator." / "The generator kept crashing, and he had to restart it again and again." / "He spent about 10 hours on it, most of it fixing these problems." / "Then the generator made one image from his prompt." / "The image matches his prompt, and he kept it."
- b: "Alex typed his prompt into the AI image generator." / "He had the generator make about 100 images from that same prompt, without changing it." / "He spent about 10 hours on it, making the images and looking through each of them." / "He kept the image that best matched his prompt."
- c: "Alex typed his prompt into the AI image generator." / "He then rewrote his prompt about 100 times, and the generator made a new image after each change." / "He spent about 10 hours on it, rewriting the prompt and looking at each new image." / "He kept the image that best matched his first prompt."
- d: "Alex typed his prompt into the AI image generator." / "The generator then rewrote the prompt on its own about 100 times, making a new image after each change." / "This took the generator about 10 hours, while Alex was away." / "The generator picked the image that best matched Alex's prompt, and Alex kept it."

Each story now says what the hours were spent on. Cell r's 10 hours are work on making this image that involves no choice about how it looks; cell a's half hour goes to setting the generator up, so r minus a still isolates time.

## 4. Question page

- Decision, three lines: "Alex applies to the U.S. Copyright Office to register this image as his own work, naming himself as its author." / "His application describes how it was made, as you have just read." / "What should the Office do?" (options unchanged).
- Confidence, share, control unchanged.
- Aspect items, reworded: "Which parts of this image are Alex's own creative work?" rows "What the image shows", "Where things sit in the picture", "The colors and the light" (Yes / No / Not sure). Data names unchanged (aspect_subject, aspect_placement, aspect_color_light).
- Effort: "How much effort went into making this image?" 1 None at all, 2 A little, 3 A moderate amount, 4 A lot, 5 A great deal.
- Creativity: "How much creativity went into making this image?" with Paper One's definition below the question; the same labels.

## 5. Written reason, every trial

Its own page after the question page: "You chose: “{decision label}.”" in a box, then "In a sentence or two, why did you choose this answer about what the Office should do?" Free text, required, pasting disabled.

## 6. Story recall, right after the last trial

"One more question about the image you just saw." above the last trial's image (no prompt, no story), then "How was this image made?": "Another artist made the image, and Alex found it online" / "In about half an hour, the generator made one image from Alex's prompt" / "Alex spent about 10 hours fixing the generator, and then it made one image" / "The generator made about 100 images from the same prompt, and Alex picked one" / "Alex rewrote his prompt about 100 times and picked one image" / "The generator rewrote the prompt on its own and picked one image" / "I don't remember". Correct is the trial's cell.

## 7. "Would" block

After story recall. Intro page: "Here are two images you saw earlier." / "We have one more question about each." Then the trials at list position 2i of cells i = k mod 6 and (k + 3) mod 6 (the old written-reason trials), each on one page with what was done, the line "This time, the question is what the Office would actually do, not what it should do.", "Under current U.S. law, what do you think the Copyright Office would actually do?" and confidence.

## 8. End items

Belief: "Did you believe the stories of how each image was made?" Purpose probe: "Whether longer plans earn more credit" becomes "Whether longer prompts earn more credit". Believability: "How believable were the stories about images that Alex found online?"; "... that the generator made from Alex's prompt in about half an hour?"; "... for which Alex spent about 10 hours fixing the generator?"; "... for which the generator made about 100 images from the same prompt?"; "... for which Alex rewrote his prompt about 100 times?"; "... for which the generator rewrote the prompt on its own?" Experience: "How often have you made images with an AI image generator?" The attitude item is replaced by A1's two scales (Short GAAIS-10; anthropocentric creativity beliefs), on wide pages, before the knowledge quiz.

## 9. Debriefing

"Thank you for taking part." / "This study asks which of a person's acts make an image from an AI image generator their own work: writing the prompt, spending time on it, picking one of many images, or rewriting the prompt." / "The U.S. Copyright Office says that, with today's AI image generators, none of these acts makes a person the author of the image." / "Your answers help test whether people judge this way." / "Alex and his stories were invented for this study, and every image was made with an AI image generator." Then the contact line. LAW_AS_OF and ALLEN_STATUS leave B1's config.

## 10. Length

About 39 minutes (37.9 to 39.3; twelve trials 26.2, recall and the "would" block 1.1, fixed parts 11.3), posted as 45. The timing gate is a median of at most 45 minutes; its remedy is unchanged (control, then the "would" block).

## 11. Data columns

New: per trial `story_page_ms`, `view_page_ms`, `question_page_ms`, `written_reason_quote`; derived `would_cell_indices`, `would_cells`, `would_positions` (the old `reason_*` derived columns go; `has_reason` is true on every row); `would_intro_page_ms`; the scale items and `gaais_positive`, `gaais_negative`, `acb_score`. Removed: `plan_heading`, `trial_page_ms`, `reason_cell_indices`, `reason_cells`, `attitude`. Recall columns now describe the last trial shown.

## 12. Second pass: stories told in order; the prompt on the question page (1 November 2026)

David asked that each story follow the order of events ("he rewrote his prompt 100 times" after or before he saw the first image?) and that the question page keep the prompt, with the prompt and what was done both under the image ("the prompt should also go under the image"). The stories of section 3 are replaced by these (word counts o 58, a 53, r 57, b 62, c 66, d 68; contrasts still differ by at most five words):

- o: "Another artist typed the prompt into an AI image generator, and it made an image." / "The image matched the prompt on the first try, so the artist posted it online for anyone to use." / "Alex found the image, saved it and backed up the file." / "This took him about half an hour in all." / "He kept the image."
- a: "Alex typed his prompt into the AI image generator, and it made an image." / "The image matched his prompt on the first try, so he did not need to change anything." / "He saved the image and backed up the file." / "This took him about half an hour in all." / "He kept the image."
- r: "Alex typed his prompt into the AI image generator, but it crashed before making an image." / "He restarted it and tried the same prompt again, and it crashed again." / "This happened again and again until it finally worked." / "Fixing these problems took him about 10 hours." / "The image it made matched his prompt, so he kept it."
- b: "Alex typed his prompt into the AI image generator, and it made an image." / "It did not quite match his prompt, so he had the generator make another from the same prompt, without changing any words." / "He did this about 100 times, looking at each new image." / "This took him about 10 hours." / "He kept the image that best matched his prompt."
- c: "Alex typed his prompt into the AI image generator, and it made an image." / "It did not quite match his prompt, so he rewrote some of the words and had the generator make a new image." / "He did this about 100 times, looking at each new image before rewriting again." / "This took him about 10 hours." / "He kept the image that best matched his first prompt."
- d: "Alex typed his prompt into the AI image generator, and it made an image." / "It did not quite match his prompt, so the generator rewrote some of the words itself and made a new image." / "It did this about 100 times on its own, while Alex was away." / "This took the generator about 10 hours." / "It picked the image that best matched Alex's prompt, and Alex kept it."

Why: the order of events is what the Office's reasoning turns on. Rewriting after each image is the iterative prompting it calls "re-rolling" (report, p. 20); rerunning one prompt and choosing is selection of a single output (p. 21); a generator that rewrites its own prompt is the automation case (pp. 19, 21). Every story ends with an image that matches the prompt, so the outcome is the same and only the acts differ. In cell r the hours now go to a generator that crashes before it makes anything, so no choice about the image is possible. In cell o the artist posts the image "for anyone to use," so that a lower share there cannot come from reading Alex's use as theft (the found image is another's AI output; permission is not the question).

Question page (engine 1.6.0, `sideTextUnderImage`): the image, then the prompt under "The prompt Alex wrote:" or "The prompt another artist wrote:", then what was done, all in the column that stays in view; the questions alone beside it. The column is sized to the window (checked at 1440 by 900, 1280 by 800 and 1280 by 720; on the smallest, the last line of the longest story scrolls inside the column). The what-was-done page shows the story and the image only (`viewPageShowsPlan: false`). Written-reason and "would" pages use the question page's layout. Length about 39 minutes (38.3 to 39.8). B1 config 1.2.0.

The registration question needs nothing more: the primer states what registration is, and telling participants how the Office decides would turn the study into a test of following the rule, which is what B1 must not do (Design, safeguard 5).
