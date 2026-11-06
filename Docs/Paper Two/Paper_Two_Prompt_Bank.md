# Papers A and B: the prompt bank

26 October 2026. This file fixes every prompt, edit instruction and scene phrase used to make the images for Papers A and B, and the lists that assign the scenes to conditions. Every image is new and is made by script with one AI image model, the sketches by a script that traces the outlines of its images. None of the images of Paper One (Kamper, Lin and Holyoak, submitted, *Beyond the Original Sin: How People Judge a Person's Contribution to Artworks Built on Artificial Intelligence*) is reused. There are two sets of scenes.

- **Set A**, ten painterly scenes (SA01 to SA10) and two reserves, serves Paper A. One image per scene, chosen by rule, is the source (the first image) that both Paper A studies show. Every second version is made by editing that source.
- **Set B**, twelve photographic scenes (SB-P1 to SB-P6 with a person, SB-N1 to SB-N6 without) and two reserves, serves Paper B. Each scene's plan is also the text participants read as Alex's plan.

Alex is the fictional artist in every study's story. Paper A Study 1 (A1) asks whether people divide an image into Alex's addition and the rest. Paper A Study 2 (A2) asks along which line they divide, and whether a source made by AI lowers Alex's credit more than an old painting does. Paper B Study 1 (B1) compares prompting with finding the same image, and tests work done after the prompt. Paper B Study 2 (B2) asks whether credit depends on who carried out Alex's plan, on the plan coming true, or on his choice to keep the image. Paper B Study 3 (B3) asks whether Alex's own sketch or photograph keeps its credit through a machine step.

In every study each participant sees each scene in one cell only (a cell is one combination of the conditions the study varies) and meets every cell on a different scene. A list is one fixed assignment of scenes to cells, and each participant gets one; the lists rotate which scene carries which cell, so that across lists every scene appears in every cell equally often. Each study's preregistration holds its design and analysis; this file holds the materials and the lists.

The 14 October bank is kept unchanged at `Docs/Paper Two/Background/Superseded 2026-10-14/Paper_Two_Prompt_Bank_2026-10-14.md`. The first-look images (trial generations from its prompts, made on 14 October to see how each scene renders) and the model comparison of 15 and 16 October were made from it, and the scripts that made them read it there. Its scene codes (A1 to A10, B1 to B8) name those image files only.

## Rules for every prompt

1. **No names.** No artist's name, no "in the style of," no brand, no real person, and no recognizable place or artwork.
2. **Plausible as a hundred-year-old painting (Set A only).** Each Set A scene is written to be believable under three stories: a digital painting Alex made without using any AI, an image made by writing prompts for an AI image generator, and a painting made about a hundred years ago. So every object in a Set A scene could have existed around 1900 to 1925, and every style is a painterly style that existed then.
3. **Room for every edit (Set A only).** Each scene contains two movable objects (for the rearrangement) and an empty area where something can be added.
4. **One feature that chance can change, and no placement (Set B only).** Each plan contains one feature that could differ from the plan by chance under any way of making the image: the weather, a light on or off, an animal present or absent, or a passer-by present or absent. No plan says where things sit in the frame, so two different compositions of a scene both match its plan.
5. **Parts are separate sentences.** Each part of a prompt is its own sentence, and the full prompt is the sentences in the order listed. In Set B, the two versions of a plan differ only in the feature sentence and, where the feature changes the light, in the color sentence, so each version describes its own image fully.
6. **Settings are recorded.** Every file has a row in the manifest, the record described under "The manifest" below.

## Generation settings

### The models

Each set has one model, chosen by David on 27 October 2026 by eye from a side-by-side comparison of six models, each with the bank's earlier style line and with a realism style line, on five scenes (`Stimuli/Paper Two/style_comparison_2026-10-27/`). He judged the earlier choice, GPT Image 2.5 Flare, obviously AI-made in the photographs.

- **Set B (photographs, Paper B):** Nano Banana Pro (`gemini-3-pro-image`), for every Set B file made by a model, including the instruction edits.
- **Set A (paintings, Paper A):** GPT Image 2 (`gpt-image-2-2026-04-21`), for every Set A source and every instruction edit.

Choosing the model and the style line was David's judgment. Every individual file is still accepted or rejected by the automatic checks alone.

### How each prompt is sent

- **Set A source:** the eight part sentences in the order listed (subject, composition, colors, lighting, style, mood, viewpoint, background), then the Set A realism line, "Painterly and hand-made in feel: uneven brush marks, varied paint thickness, small imperfections and a muted, slightly faded palette. Not glossy, not airbrushed, not photorealistic, no digital sheen.", then "No text, lettering, signature, watermark, or frame."
- **Set B, first composition (V1):** plan version 1, then the Set B realism line, "An unretouched documentary photograph taken with an ordinary digital camera in available light: true-to-life, slightly muted colors, fine sensor noise, natural imperfections and everyday clutter. Not cinematic, not HDR, no dramatic lighting, no glossy commercial look.", then "No text, watermark, or border."
- **Set B, second composition (I2):** plan version 1, then the scene's placement sentence, then the same realism line and closing sentence.

Participants never see the realism lines, the closing sentences or the placement sentence. In Set B they see only the plan. Because the Google model adds stray text more often than the OpenAI models did, every file must also pass a no-text check: the description model answers yes to "Is the image free of any visible text, letters, numbers, signatures or watermarks?"

### Settings

- Set A (GPT Image 2): 3:2 landscape, 1536 × 1024 pixels, at "high" quality. The model accepts no seed (a number that fixes a model's random starting point, so that the same seed and prompt give the same image), so its candidates are repeated calls with the same prompt, numbered in the order made.
- Set B (Nano Banana Pro): 3:2 landscape at the model's own output size, recorded in the manifest. Candidate n is requested with seed 1000 + n; if the model does not accept a seed, the call is repeated without one and the manifest says so. Candidates are numbered in the order made.

## Edit instructions

Every edit is made with the model's instruction editor, its mode that changes an existing image to follow a written instruction. No edit is made by hand. Each instruction is one of the fixed frames below with the scene's phrase put in, so the phrase in each scene's table is the only part that varies. The examples are scene SA01 and scene SB-P1.

| Edit | Applied to | Instruction |
|---|---|---|
| Small or medium addition (Set A) | The source | "Add " + the phrase + ". Change nothing else." For example: "Add a vase of daisies on the bare end of the table. Change nothing else." |
| Large addition (Set A) | The medium file | "Add " + the two further elements + ". Change nothing else." For example: "Add a loaf of bread on a board, and a cat asleep on a stool. Change nothing else." |
| Restyle (Set A) | The source | "Repaint the whole image in these colors and this way of painting: " + the phrase + ". Keep every object, outline and position. Change nothing else." |
| Rearrangement (Set A) | The source | "Move " + the phrase + ". Change nothing else." For example: "Move the teapot and the cup to the woman's left. Change nothing else." No crop is made, because a crop changes every pixel. |
| Departing version (V2, Set B) | V1 | "Change only this: " + the sentences that change in plan version 2 + " Keep everything else exactly the same." For example: "Change only this: Sunlight streams through the glass onto her lap. Warm creams and golds with soft blue. Keep everything else exactly the same." |
| Addition (Set B) | V1 | "Add " + the phrase + ". Change nothing else." For example: "Add a potted plant on the windowsill. Change nothing else." |
| Restyle (Set B) | V1 | "Repaint the whole photograph " + the phrase + ", keeping every object, outline and position. Change nothing else." For example: "Repaint the whole photograph as a watercolor painting in soft blues, keeping every object, outline and position. Change nothing else." |

The same phrases go into the participant statements, so an image and its statement name the same thing. A1's statement for SA01 at the medium amount reads "He added a vase of daisies on the bare end of the table. He changed nothing else." Where a statement joins, shortens or rewords a phrase, the section on each set below shows how.

## How a file is accepted

No one paints, draws or picks an image. David runs every generation script, candidates are numbered in the order made, and the first that passes the automatic checks is used.

### The automatic checks

- An **object detector** is a model that finds and outlines named objects in an image. An **image-description model** is a model that describes an image; here it is asked a fixed yes-or-no question about each element a file must show. Where both are named, both must confirm.
- A **change mask** is the set of pixels an edit changed, found by comparing the edited image with the image it was made from. Its **masked area** is the share of the image inside it. Before an addition is accepted, its mask is widened by a fixed number of pixels on every side. Only the edited pixels inside the widened mask are then pasted onto the original (the file is **composited** through its mask), so every pixel outside it is identical to the original.
- **DreamSim** is a model that scores how different two images look to people. **Masked DreamSim** is that score computed only outside a named region, so it measures change everywhere except where the edit was meant to act.
- An **edge map** is the set of outlines in an image, found by **edge detection**, a standard filter that marks sharp changes in brightness. Two edge maps **overlap** to the extent their outline pixels coincide. **Mean color distance** is the average difference in color between matching pixels of two images.

Every threshold is an absolute number, set from the first batch of candidates before any participant data exist and written into the manifest and the preregistrations. None is relative to the other candidates.

| File | Accepted when |
|---|---|
| Set A source | The detector and the description model confirm the two objects the rearrangement moves, and the description model confirms the open area where the additions go |
| Set A addition (small, medium, large) | The detector and the description model confirm each added element; the description model confirms the file is free of visible text; the masked area, measured against the source, keeps the within-scene order (small at least 0.1 percent of the image; medium at least twice the scene's accepted small and at least 0.5 percent; large at least twice the accepted medium), which replaced the original bands of 1 to 2, 8 to 12 and 25 to 35 percent on 27 October 2026 because the elements are smaller than the bands at natural size; every object named in the scene's Composition and Background sentences that the detector finds in the input is found in the edited file with intersection over union of at least 0.5 (29 October 2026); the file is composited through its widened mask |
| Set A restyle | Edge-map overlap with the source is above a fixed threshold, and mean color distance from the source is above a fixed threshold |
| Set A rearrangement | The detector confirms both objects in their new positions, and masked DreamSim from the source, outside the regions where the two objects were and now are, is below a fixed threshold |
| Set B V1 | The detector and the description model confirm the feature as plan version 1 states it |
| Set B I2 | The detector confirms the new placement: the main elements on the side and at the scale the placement sentence names. As for V1, the detector and the description model also confirm the feature as plan version 1 states it, because B1 and B3 present I2 as matching that plan |
| Set B V2 | By kind of feature. Animal or passer-by: the detector confirms the change, and masked DreamSim from V1 outside the changed region is below a fixed threshold. Weather or a light, which change the light across the whole frame: the description model confirms the feature as plan version 2 states it, and the edge maps and detected object positions of V1 and V2 agree above fixed thresholds |
| Set B sketches (S1, S2) | Outline overlap with its own image is above a fixed threshold, and with the scene's other composition below it |
| Set B addition | The detector and the description model confirm the object; the masked area is 4 to 10 percent; the file is composited through its widened mask |
| Set B restyle | Edge-map overlap with V1 is above a fixed threshold, and mean color distance from V1 is above a fixed threshold |

### What the studies check

Every file is accepted on the automatic checks alone. How people read the files and the statements built from this file's phrases is measured inside each study, on its own participants.

- **Equal wording by construction.** Wording that must not differ across conditions uses one sentence frame and differs in length by at most four words, checked by the manifest script (below).
- **Believability by condition.** Each study except A1 ends with believability items (A1 dropped them on 1 November 2026, design record 12.25), one per kind of description (1 to 7, "How believable were the descriptions of images that ...?"), reported by condition. They never exclude anyone or change any material.
- **Internal pilot.** The first 40 analyzable participants of each study (those left after its registered exclusions) form an internal pilot, checked by script against fixed gates (pass rules) before recruitment continues. Every study has a gate on its story belief item, the end item asking whether the participant believed the study's account of how the images were made (at least 70 percent answer "Yes" or "Partly"), and one on session length. The gates that test this file's materials are:
  - A2: levels 2 to 4 say that Alex added an element by hand, that an AI tool added it where he said, or that an AI tool chose it from his goal. On the first trial of each of these levels, two checks follow: "Who decided what to add and where to put it?" and "Who painted the vase of daisies into the image?" (SA01; every other scene names its own element). At least 80 percent of the answers must match the statement.
  - B2: on the match check ("How closely does this image match Alex's plan?" 0 to 100), the mean rating on trials whose image matches the plan is at least 20 points above the mean on trials whose image departs from it.
  - B3, sketches: in cell g (an image beside its own sketch), at least 60 percent of answers to "How much of Alex's sketch can you see in the image?" (0 to 100) are 50 or more, and in cell f (an image beside the other composition's sketch) at least 60 percent are below 50. At least 70 percent answer "Yes" or "Partly" to "Did you believe that Alex drew the sketches by hand before the images were made?"
  - B3, photographs: at least 70 percent of the belief checks on cells h and j (the addition and the restyle Alex made by hand) are "Yes" or "Not sure."

If one of these gates fails, the materials it tests are changed before recruitment continues. A changed file passes the automatic checks like any other, and every change is recorded in the manifest. The pilot participants are then dropped from the sample and barred from taking part again, and the change is reported as a deviation from the preregistration. If a B3 sketch gate fails, the sketches are remade by the sketch rescue rule below.

### Rescue rules

- A scene with no candidate that passes the automatic checks within 20 tries gets one prompt revision, recorded in the manifest, and the search starts again. A scene that still fails is replaced by a reserve scene.
- Each set has two reserve scenes, one with a person and one without, written to the same rules as its main scenes and listed at the end of each set below (SA-R1 and SA-R2; SB-R1 and SB-R2), so that no replacement is written after a failure is seen. A reserve takes the failed scene's place in every list and replaces only a scene of its own kind, with a person or without.
- **Sketch rescue rule.** Line simplification is the fixed rule that removes short or redundant line segments from an edge map. If a B3 sketch gate fails in the internal pilot, the line-simplification settings are changed step by step along a preset grid recorded in the manifest, fewer interior lines first, and for each scene the next setting whose sketches pass the automatic checks is used. A scene with no passing setting is replaced by its reserve scene.

### The manifest

Every file has one row recording the model, its version, the prompt or instruction, the settings, the mask file, the result of every check, and the time it was made. The manifest also holds every participant-facing statement with its word count, computed by script, and two checks on those counts. First, wording that must not differ across conditions differs in length by at most four words. This covers a scene's A2 statements at levels 2, 3 and 4, and its B3 statements for one change made by hand and by an AI tool (the addition in cells h and i, the repainting in cells j and k). It also covers a scene's B2 sentences saying that the image matched or departed from the plan, which are the same under every executor (the AI tool, camera or hired photographer that carried out Alex's plan). Second, any other two statements that a confirmatory contrast (a planned difference between cells that tests a hypothesis) compares differ in length by at most five words. The one exception is B2's chose and unseen sentences (Alex looked at the image and chose to send it to the client; it went to the client automatically, before he looked), which differ by seven or eight words, because only the chose sentence says what Alex did.

---

## Set A: ten painterly scenes (Paper A)

Scenes SA01 to SA05 include a person; SA06 to SA10 do not. The two reserve scenes, SA-R1 (with a person) and SA-R2 (without), follow SA10. Each scene lists its eight prompt parts in the order they are sent, then its edit phrases.

### Edits and where they are used

| Edit | Target share of the image changed | Used in |
|---|---|---|
| Small addition | One element; at least 0.1 percent of the image | A1 |
| Medium addition | One element; at least twice the scene's small and at least 0.5 percent | A1; A2 levels 2, 3 and 4 (one file, three statements) |
| Large addition | The medium element plus two more, added to the medium file; at least twice the scene's medium | A1, both blocks |
| Restyle | Colors and rendering changed across the whole image; nothing added or removed | A2 level 5 |
| Rearrangement | The two listed objects moved; nothing added, removed or recolored; no crop | A2 level 6 |

A1 shows each source after a short story page saying either that Alex made it with an AI image generator, by writing prompts (the AI source), or that he painted it himself with digital painting tools, without using any AI (the hand-made source), and first shows the source alone. Beside it A1 then shows one of its additions, saying that Alex made the addition himself with his digital painting tools, or the unchanged source, saying that he kept the image as it was. Its first block of eight trials comes before a paragraph stating the U.S. Copyright Office's rule for works built on material that is not the applicant's to claim; its second block of two trials, both at the large addition, comes after it.

A2 shows each source with a reminder line saying either that another person made it with an AI image tool (AI-found) or that it is a painting made about a hundred years ago. A2 has five levels, numbered 2 to 6 to match the edits; levels 2, 3 and 4 show the same file, and each level appears once with each source.

- Level 2: Alex added the medium element by hand.
- Level 3: an AI tool added it where he told it to.
- Level 4: an AI tool chose and added it after he gave it the scene's goal.
- Level 5: Alex restyled the whole image by hand.
- Level 6: he moved the two listed objects by hand.

How the phrases are used:

- A1's statement names the scene's phrase for the amount shown and is the same under both kinds of source. At the large amount it names the medium element and then the two further elements (SA01: "He added a vase of daisies on the bare end of the table, a loaf of bread on a board, and a cat asleep on a stool. He changed nothing else.").
- A2's level 4 statement names the goal and then the scene's level 4 element, listed in its table. That element is the medium element with words dropped where needed, so that the scene's level 2, 3 and 4 statements differ in length by at most four words (SA01: "He told the tool to make the table look more cheerful; the tool chose to add a vase of daisies on the bare end.").
- A2's level 5 statement gives the restyle's colors after "in" and its paint after "with" (SA01: "in cool blues and violets with smooth, flat paint"), and its level 6 statement uses the rearrangement phrase as written (SA01: "He moved the teapot and the cup to the woman's left").
- A2's aspect items (questions answered Yes, No or Not sure on whether one named part of the second image is Alex's own creative work) name the medium element and the two moved objects without their places (SA01: "How the vase of daisies looks: its shape, colors and brushwork"; "Where the teapot and the cup are placed in the frame"). The check "Who painted the vase of daisies into the image?" names the element the same way.
- Each goal is written so that the scene's medium element plausibly answers it.

### SA01. The letter (person)

| Part | Text |
|---|---|
| Subject | A woman reading a letter at a kitchen table. |
| Composition | She sits in the left third of the frame, a teapot and a cup stand near her right hand, and the far end of the table is bare. |
| Colors | Muted ochres and soft sage greens. |
| Lighting | Morning light falls from a window on the right. |
| Style | Oil painting with loose, visible brushwork. |
| Mood | Quiet and absorbed. |
| Viewpoint | Eye level, three-quarter view. |
| Background | A plain plaster wall with a copper pot hanging from a hook. |

**Edits**

| Edit | Phrase |
|---|---|
| Small | a spoon beside the cup |
| Medium | a vase of daisies on the bare end of the table |
| Large, added to the medium file | a loaf of bread on a board, and a cat asleep on a stool |
| Restyle | cool blues and violets, smooth flat paint |
| Rearrangement | the teapot and the cup to the woman's left |
| Goal (A2, level 4) | make the table look more cheerful |
| Level 4 element (A2) | a vase of daisies on the bare end |

### SA02. The net mender (person)

| Part | Text |
|---|---|
| Subject | An old fisherman mending a net on a wooden dock. |
| Composition | He sits low in the center, a wooden crate and a coil of rope lie to his left, and the dock stretches empty to his right. |
| Colors | Slate blues and rust browns. |
| Lighting | Flat, overcast light. |
| Style | Thick oil paint with heavy impasto. |
| Mood | Weathered and patient. |
| Viewpoint | Seen from slightly above. |
| Background | A gray harbor with a single moored rowboat. |

**Edits**

| Edit | Phrase |
|---|---|
| Small | a gull standing on the wooden crate |
| Medium | a dog lying on the empty dock to the man's right |
| Large, added to the medium file | a stack of barrels, and a lantern on a post |
| Restyle | sunset oranges and pinks, smooth glazed paint |
| Rearrangement | the wooden crate and the coil of rope to the man's right |
| Goal (A2, level 4) | make the dock feel less lonely |
| Level 4 element (A2) | a dog lying to the man's right |

### SA03. The kite (people)

| Part | Text |
|---|---|
| Subject | Two children flying a kite on a grassy hill. |
| Composition | The children stand small in the lower right, the kite flies high in the upper left, and a wide band of empty sky fills the middle. |
| Colors | Bright cerulean, grass green, and white. |
| Lighting | Bright afternoon sun from the left. |
| Style | Impressionist painting with short, dabbed strokes. |
| Mood | Breezy and joyful. |
| Viewpoint | Low angle, looking up the slope. |
| Background | Scattered clouds and a small farmhouse on a distant ridge. |

**Edits**

| Edit | Phrase |
|---|---|
| Small | a bird flying in the open sky |
| Medium | a dog running beside the two children |
| Large, added to the medium file | a picnic blanket with a basket, and a second kite |
| Restyle | autumn ochres and reds, smooth tonal paint |
| Rearrangement | the children to the lower left and the kite to the upper right |
| Goal (A2, level 4) | make the hillside feel livelier |
| Level 4 element (A2) | a dog running beside the two children |

### SA04. The violinist (person)

| Part | Text |
|---|---|
| Subject | A young man practicing the violin in a dim parlor. |
| Composition | He stands right of center, a music stand and an empty wooden chair are at the left, and the rug in front of him is bare. |
| Colors | Deep reds and browns with touches of gold. |
| Lighting | A single oil lamp on the left casts strong shadows. |
| Style | Tonal oil painting with soft edges. |
| Mood | Intimate and melancholy. |
| Viewpoint | Eye level, seen from the side. |
| Background | Heavy curtains and a tall gilt-framed mirror on the wall that reflects the lamp's glow. |

**Edits**

| Edit | Phrase |
|---|---|
| Small | a sheet of music on the floor |
| Medium | a large dog asleep on the rug in front of the man |
| Large, added to the medium file | a side table with a vase in the right foreground, and a candlestick on the side table |
| Restyle | cool daylight blues and whites, crisp linear rendering |
| Rearrangement | the music stand and the empty chair to the right side of the room |
| Goal (A2, level 4) | make the parlor feel cozier |
| Level 4 element (A2) | a dog asleep on the rug in front of the man |

### SA05. The fruit stall (person)

| Part | Text |
|---|---|
| Subject | A market vendor arranging oranges at an outdoor stall. |
| Composition | She stands at the center behind a long wooden counter, with crates and a basket of lemons at the left end, oranges piled only in front of her, and the right third of the counter bare and empty. |
| Colors | Oranges and lemon yellows against shaded blues. |
| Lighting | Midday sun, with a striped awning casting shade. |
| Style | Oil painting in a post-impressionist manner, with bold outlines and thick, visible brushwork. |
| Mood | Busy and warm. |
| Viewpoint | Eye level, facing the stall. |
| Background | A stone arcade with a hanging iron lantern. |

**Edits**

| Edit | Phrase |
|---|---|
| Small | a single lemon on the ground |
| Medium | a basket of eggs on the empty end of the counter |
| Large, added to the medium file | buckets of flowers, and a customer with a shopping bag |
| Restyle | evening violets and greens, soft blended paint |
| Rearrangement | the crates and the basket of lemons to the right end of the counter |
| Goal (A2, level 4) | make the stall look better stocked |
| Level 4 element (A2) | a basket of eggs on the empty end |

### SA06. The rowboat (no person)

| Part | Text |
|---|---|
| Subject | A rowboat pulled up on a riverbank. |
| Composition | The boat lies diagonally across the foreground with two long wooden oars resting across its seats in plain view, and the river curves away to the right past an empty stretch of water. |
| Colors | Soft greens, pale blue, and ochre. |
| Lighting | Early evening, with the low sun behind the trees. |
| Style | Outdoor oil sketch with broken color. |
| Mood | Calm and still. |
| Viewpoint | Standing height, looking slightly down. |
| Background | Willow trees and, in the middle distance, a small arched stone bridge clearly visible across the river. |

**Edits**

| Edit | Phrase |
|---|---|
| Small | a duck on the empty stretch of water |
| Medium | a heron standing in the shallow water |
| Large, added to the medium file | a second boat, and a stand of reeds |
| Restyle | cold whites and grays, smooth paint |
| Rearrangement | the two oars from the boat's seats to the bank beside the boat |
| Goal (A2, level 4) | bring some wildlife into the scene |
| Level 4 element (A2) | a heron in the shallow water |

### SA07. The table (no person)

| Part | Text |
|---|---|
| Subject | A still life of bread, cheese, and a clay wine jug on a wooden table. |
| Composition | The bread, cheese, and jug cluster in the left half with a knife laid diagonally in front of them, nothing else is on the table, and the whole right half of the table is bare wood. |
| Colors | Warm browns, cream, and deep red. |
| Lighting | Raking light from the left. |
| Style | Realist oil painting with smooth blending. |
| Mood | Rustic and generous. |
| Viewpoint | Slightly above, close up. |
| Background | A dark, nearly black wall. |

**Edits**

| Edit | Phrase |
|---|---|
| Small | a single walnut |
| Medium | a pear on the bare right side of the table |
| Large, added to the medium file | a bowl of grapes, and a candlestick |
| Restyle | cool greens and blues, loose sketchy paint |
| Rearrangement | the jug and the bread into each other's places |
| Goal (A2, level 4) | make the table look more plentiful |
| Level 4 element (A2) | a pear on the bare right side |

### SA08. The snowy street (no person)

| Part | Text |
|---|---|
| Subject | A snowy village street at dusk, with no one in sight. |
| Composition | The street recedes to the center between rows of houses, a hand cart and a lamp post stand on the left, and the right side of the street is open. |
| Colors | Blue-violet snow and warm yellow windows. |
| Lighting | Dusk, with lamplight glowing in the windows. |
| Style | Tonal oil painting with soft edges. |
| Mood | Hushed and cold. |
| Viewpoint | Eye level, from the middle of the street. |
| Background | A church steeple against a fading sky. |

**Edits**

| Edit | Phrase |
|---|---|
| Small | a bird on a rooftop |
| Medium | a horse-drawn sled on the open right side of the street |
| Large, added to the medium file | a snowman, and a row of lanterns along the houses |
| Restyle | sunset pinks and oranges, crisp outlined rendering |
| Rearrangement | the hand cart and the lamp post to the right side of the street |
| Goal (A2, level 4) | make the street look less empty |
| Level 4 element (A2) | a horse-drawn sled on the open right side |

### SA09. The garden bench (no person)

| Part | Text |
|---|---|
| Subject | A wooden bench under a flowering cherry tree in a garden. |
| Composition | The bench sits in the lower left with a clay flowerpot beside it, the tree arches across the top, and the path to the right is empty. |
| Colors | Pinks, whites, and fresh greens. |
| Lighting | Dappled spring sunlight. |
| Style | Impressionist painting with short brushstrokes. |
| Mood | Gentle and airy. |
| Viewpoint | Eye level. |
| Background | A low stone wall with an iron gate. |

**Edits**

| Edit | Phrase |
|---|---|
| Small | a butterfly over the path |
| Medium | a watering can on the path |
| Large, added to the medium file | a wheelbarrow, and a birdbath |
| Restyle | moonlit blues, smooth dark paint |
| Rearrangement | the bench and the flowerpot to the right side of the garden |
| Goal (A2, level 4) | make the garden look tended |
| Level 4 element (A2) | a watering can on the path |

### SA10. The lighthouse (no person)

| Part | Text |
|---|---|
| Subject | A lighthouse on a rocky coast during a storm. |
| Composition | The lighthouse stands in the right third, waves break over rocks on the left where a red buoy bobs, and the sea in the center is open. |
| Colors | Dark slate, white foam, and the yellow beam of the lamp. |
| Lighting | Storm light under heavy clouds, with the lamp lit. |
| Style | Expressive oil painting with heavy, sweeping strokes. |
| Mood | Dramatic and turbulent. |
| Viewpoint | Low, from the shore. |
| Background | Dark clouds, a small ship on the horizon, and a keeper's cottage at the foot of the lighthouse. |

**Edits**

| Edit | Phrase |
|---|---|
| Small | a single gull |
| Medium | a large sailing ship in the open sea |
| Large, added to the medium file | a rowboat, and a flare in the sky |
| Restyle | pastel blues and pinks, smooth flat paint |
| Rearrangement | the red buoy and the small ship to the middle of the open sea |
| Goal (A2, level 4) | make the open sea feel less empty |
| Level 4 element (A2) | a small sailboat |

### SA-R1. The seamstress (person, reserve)

| Part | Text |
|---|---|
| Subject | A young woman sewing a dress at a wooden worktable. |
| Composition | She sits in the right third of the frame, a pair of scissors and a spool of thread lie beside her on the table, and the left end of the table is bare. |
| Colors | Soft rose, cream, and warm gray. |
| Lighting | Afternoon light falls from a window on the left. |
| Style | Oil painting with soft, broken brushwork. |
| Mood | Patient and focused. |
| Viewpoint | Eye level, seen from the front. |
| Background | A papered wall with a small framed picture. |

**Edits**

| Edit | Phrase |
|---|---|
| Small | a teacup on a saucer beside the scissors |
| Medium | a basket of folded cloth on the bare left end of the table |
| Large, added to the medium file | a tall wooden cupboard against the back wall, and a rocking chair beside the table |
| Restyle | deep greens and golds, smooth glazed paint |
| Rearrangement | the scissors and the spool of thread to the left end of the table |
| Goal (A2, level 4) | make the worktable look busier |
| Level 4 element (A2) | a basket of folded cloth on the bare left end of the table |

### SA-R2. The hay barn (no person, reserve)

| Part | Text |
|---|---|
| Subject | An old wooden barn beside a hayfield in late summer. |
| Composition | The barn stands in the left third, a hay wagon and a wooden ladder stand in front of it, and the field to the right is open. |
| Colors | Golden yellows, faded reds, and pale blue. |
| Lighting | Warm late-afternoon sun from the right. |
| Style | Impressionist painting with thick, broken strokes. |
| Mood | Warm and unhurried. |
| Viewpoint | Eye level, from the edge of the field. |
| Background | Rolling hills and a line of poplar trees. |

**Edits**

| Edit | Phrase |
|---|---|
| Small | a milk churn beside the hay wagon |
| Medium | a haystack on the open right side of the field |
| Large, added to the medium file | a grazing horse, and a stone water trough |
| Restyle | silvery grays and blues, smooth tonal paint |
| Rearrangement | the hay wagon and the ladder to the right side of the field |
| Goal (A2, level 4) | make the field look harvested |
| Level 4 element (A2) | a haystack on the open right side of the field |

**Phrase amendments (28 October 2026, decided by David before any participant data).** Three A1 phrases could not meet the within-scene size rule or the content checks under the rescue rule, with both reserves already in use, so they were reworded and only the files that depend on them are made again under the same rules: SA04 medium "a dog asleep on the rug in front of the man" became "a large dog asleep on the rug in front of the man" (its accepted small, a sheet of music, came out at 1.1 percent, and no dog reached twice that); SA10 medium "a small sailboat in the open sea" became "a sailboat in the open sea" (the word "small" worked against a medium addition, which never reached twice the gull); SA-R1 large "a dress form beside the table, and a cat asleep on the floor" became "a tall wooden cupboard against the back wall, and a rocking chair beside the table" (the model rarely drew a dress form or a sleeping cat that the checks confirmed, and the pair rarely reached twice the medium). Later on 28 October, SA10 medium was reworded again, from "a sailboat in the open sea" to "a large sailing ship in the open sea": in 40 tries under the first rewording the sailboat changed 0.67 to 0.98 percent of the image, never twice the gull's 0.82 percent. On 29 October 2026 David also gave SA04's large addition a place: "a side table with a vase, and a candlestick" became "a side table with a vase in the far right corner, and a candlestick on the mantelpiece", because with no place given the model put the table where the empty chair stood and moved the chair. The same day the place was changed to the right foreground ("a side table with a vase in the right foreground, and a candlestick on the side table"), because in the far corner the table was drawn too small to reach twice the medium addition in 17 tries. Every earlier candidate and phrase is kept in the manifest.

### Which files each study uses

| Study | Scenes | Files per scene |
|---|---|---|
| A1 | All ten, one per trial: eight in block 1, one per combination of source and amount, and two in block 2, the large addition under each source | Source; small, medium and large additions |
| A2 | All ten, one per trial, one per combination of source and level | Source; medium addition; restyle; rearrangement |

Set A makes 60 participant files: 10 sources, 30 additions, 10 restyles and 10 rearrangements.

### Lists

Both studies order the ten scenes SA01, SA06, SA02, SA07, SA03, SA-R2, SA04, SA09, SA-R1, SA10 (positions 0 to 9; the reserves SA-R2 and SA-R1 hold the places of SA08 and SA05, which they replaced on 28 October 2026), so even positions hold scenes with a person. A slot is one of a list's places for a trial. In rotation k (0 to 9), slot j (0 to 9) shows the scene at position (j + k) modulo 10, the remainder after dividing j + k by 10.

- **A1** has ten lists, one per rotation. Slots 0 to 7 form block 1: slots 0 and 1 carry no change, 2 and 3 the small addition, 4 and 5 the medium and 6 and 7 the large; the AI source takes slots 0, 2, 5 and 7, and the hand-made source slots 1, 3, 4 and 6. Slots 8 and 9 form block 2: slot 8 carries the large addition under the AI source, and slot 9 under the hand-made source. Each source in block 1 falls on two scenes with a person and two without, each amount on one scene of each kind, and across the ten lists every scene appears in every slot once.
- **A2** has twenty lists, the ten rotations crossed with two source maps: list n (0 to 19) uses rotation n modulo 10, with map 0 if n is below 10 and map 1 otherwise. Slot pairs (0, 1), (2, 3), (4, 5), (6, 7) and (8, 9) carry levels 2 to 6. In map 0 the first slot of a pair is AI-found for levels 2, 4 and 6 and the second slot for levels 3 and 5; map 1 reverses this. Each level falls once on a scene with a person and once on one without, and across the twenty lists every scene appears in every combination of source and level twice.

A1 randomizes trial order within each block and A2 across its ten trials; the order is recorded.

---

## Set B: twelve photographic scenes (Paper B)

Scenes SB-P1 to SB-P6 include a person; SB-N1 to SB-N6 do not. Each plan has four sentences (subject, arrangement, light, colors), and participants read it as "Alex's plan" (in B1's cell where Alex found the image, as "The plan another artist wrote"). Each scene has one feature that chance could change under any way of making the image. Its two plan versions differ only in that feature and, where the feature changes the light, in the colors. Plans run 27 to 36 words, counted by script.

| Kind of feature | With a person | Without a person |
|---|---|---|
| Weather | SB-P1, SB-P3 | SB-N1, SB-N5 |
| An animal present or absent | SB-P2 | SB-N2, SB-N4 |
| A light on or off | SB-P5 | SB-N3, SB-N6 |
| A passer-by present or absent | SB-P4, SB-P6 | none |

The two reserve scenes follow SB-N6: SB-R1, with a person and an animal, and SB-R2, without a person and with weather. A reserve in use can change the count of a kind of feature by one; the counts used are reported.

**Reserve in use (27 October 2026).** SB-N3 failed under the rescue rule (in all 40 tries of its second composition the model added shop signs or other text, and usually more than one car where the plan has one), so SB-R2 takes SB-N3's place in every Paper B list. The counts in use are weather 5 (SB-P1, SB-P3, SB-N1, SB-N5, SB-R2), animal 3, light 2 (SB-P5, SB-N6) and passer-by 2.

### Files per scene

| File | What it is and how it is made | Used in |
|---|---|---|
| V1 | The first composition, generated from plan version 1 | B1, B2, B3 |
| V2 | V1 with only the feature changed to plan version 2, by instruction edit | B2 |
| I2 | The second composition, generated from plan version 1 with the scene's placement sentence, which participants never see | B1, B3 |
| S1, S2 | Sketches of V1 and of I2, made by edge detection and line simplification: the outlines of figures and main objects and a few interior placement lines (where a face's features sit, where an arm bends), with no shading or texture, rendered as black lines in a hand-drawn style on white | B3 |
| Addition | V1 with one object added by instruction edit, composited so that every pixel outside the object's widened mask is identical to V1 | B3 |
| Restyle | V1 repainted whole in the listed style by instruction edit, keeping every object and position | B3 |

Set B makes 84 files, seven per scene. Because both compositions match the written plan, which names no placement, B1 and B3 show plans in version 1 only.

### How the scene phrases are used

- **The plan (B1, B3).** B1 and B3 show plan version 1. B1's six statements name no scene phrase; the four that describe work after the prompt (routine hours, choosing among about 100 versions from one prompt, revising the prompt about 100 times, and the tool revising its own prompt) each state about 10 hours.
- **The two plan versions (B2).** Under plan version 1, V1 matches the plan and V2 departs from it; under version 2, the reverse. Each B2 list shows one version of every plan. A trial whose image matches the plan shows the file that the shown version describes, and a trial whose image departs shows the other file.
- **The feature phrases (B2).** The sentence that follows the one saying who or what made the image (an AI tool, Alex's camera on a timer, or a photographer he hired) names the shown image's feature in the words of the plan version that describes it. For SB-P1 under version 1, the matching sentence is "The image came out as planned, with rain streaking the glass." The departing sentence is "The image came out with sunlight streaming through the glass, not as planned." These sentences are the same under every executor, and within a scene they differ in length by at most four words.
- **The feature item (B2)** is one of B2's two aspect items. It asks whether the feature, as it appears in the shown image, is Alex's own creative work; the other asks the same of "How things are arranged in the frame."
- **The placement sentence (I2)** is written in one form: the main elements on the right side of the frame, small, seen from farther away. Before I2 is generated, the object detector finds those elements in V1. If the center of their box lies in the right half of V1, "right" becomes "left." If their box covers less of the frame than a fixed scale cut, "small, seen from farther away" becomes "large, seen from close by." The scale cut is an absolute number set from the first batch, like every threshold. The prompt thus asks for the main elements on the other side of the frame from V1 and at the other scale, the I2 check confirms it, and the two sketches overlap little. If V1 is ever remade after its I2 exists, the new V1 must also pass the same detector check against I2, with its main elements on the other side of the frame from I2's and at the other scale.
- **The addition and restyle (B3)** go unchanged into the instruction frames above and into the statements for B3's four photograph cells, in which Alex added the object himself (cell h) or had an AI tool add it (cell i), or repainted the photograph himself (cell j) or had an AI tool repaint it (cell k). For SB-P1, cell h reads "He added a potted plant on the windowsill, cut from another photograph he took himself, and changed nothing else." Cell k reads "He told it to repaint the whole photograph as a watercolor painting in soft blues." Within a scene, the h and i statements differ in length by one word, as do the j and k statements.
- **The addition aspect item (B3)** names the added object without its place.

### SB-P1. Reading by the window (person)

| Part | Text |
|---|---|
| Plan, version 1 | A woman reads in an armchair beside a tall window. She holds the open book on her lap. Rain streaks the glass, and the light is soft and grey. Soft blues, greys, and cream. |
| Plan, version 2 | A woman reads in an armchair beside a tall window. She holds the open book on her lap. Sunlight streams through the glass onto her lap. Warm creams and golds with soft blue. |
| Kind of feature | Weather |
| Feature item (B2) | The weather outside the window |
| Feature phrase, version 1 | rain streaking the glass |
| Feature phrase, version 2 | sunlight streaming through the glass |
| Placement sentence (I2) | The woman and her armchair are on the right side of the frame, small, seen from farther away. |
| Addition (B3) | a potted plant on the windowsill |
| Addition aspect item (B3) | The added potted plant |
| Restyle (B3) | as a watercolor painting in soft blues |

### SB-P2. The bicycle (person)

| Part | Text |
|---|---|
| Plan, version 1 | An older man repairs a bicycle in an open garage. He kneels beside the back wheel, and a dog sleeps by the door. Warm light from one overhead bulb. Browns and dusty oranges. |
| Plan, version 2 | An older man repairs a bicycle in an open garage. He kneels beside the back wheel, and the doorway is empty. Warm light from one overhead bulb. Browns and dusty oranges. |
| Kind of feature | Animal |
| Feature item (B2) | Whether a dog is in the picture |
| Feature phrase, version 1 | a dog sleeping by the door |
| Feature phrase, version 2 | the doorway empty |
| Placement sentence (I2) | The man and the bicycle are on the right side of the frame, small, seen from farther away. |
| Addition (B3) | a red toolbox on the floor by the wheel |
| Addition aspect item (B3) | The added red toolbox |
| Restyle (B3) | as an oil painting with thick brushwork in warm oranges |

### SB-P3. The side street (person)

| Part | Text |
|---|---|
| Plan, version 1 | A young woman in a yellow raincoat walks down a narrow side street. She holds a closed umbrella. The sky above the rooftops is heavy and grey. Greys with one yellow accent. |
| Plan, version 2 | A young woman in a yellow raincoat walks down a narrow side street. She holds a closed umbrella. The sky above the rooftops is clear and blue. Blues and greys with one yellow accent. |
| Kind of feature | Weather |
| Feature item (B2) | The sky |
| Feature phrase, version 1 | a heavy grey sky above the rooftops |
| Feature phrase, version 2 | a clear blue sky above the rooftops |
| Placement sentence (I2) | The young woman is on the right side of the frame, small, seen from farther away. |
| Addition (B3) | a bicycle leaning against the wall |
| Addition aspect item (B3) | The added bicycle |
| Restyle (B3) | as an ink drawing with grey washes |

### SB-P4. The kitchen (person)

| Part | Text |
|---|---|
| Plan, version 1 | A chef plates a dish in a restaurant kitchen. He leans over the plate, alone in the room. Bright side light with rising steam. Steel greys and white. |
| Plan, version 2 | A chef plates a dish in a restaurant kitchen. He leans over the plate while a second cook passes behind him. Bright side light with rising steam. Steel greys and white. |
| Kind of feature | Passer-by |
| Feature item (B2) | Whether anyone else is in the picture |
| Feature phrase, version 1 | the chef alone in the room |
| Feature phrase, version 2 | a second cook passing behind the chef |
| Placement sentence (I2) | The chef is on the right side of the frame, small, seen from farther away. |
| Addition (B3) | a bowl of lemons on the counter |
| Addition aspect item (B3) | The added bowl of lemons |
| Restyle (B3) | as a flat poster in bold colors |

### SB-P5. The bus stop (person)

| Part | Text |
|---|---|
| Plan, version 1 | A man waits at a bus stop at dusk. He stands under the shelter with his hands in his pockets. The shelter's light is on. Deep blues and warm yellow. |
| Plan, version 2 | A man waits at a bus stop at dusk. He stands under the shelter with his hands in his pockets. The shelter's light is off. Deep blues and dark greys. |
| Kind of feature | Light |
| Feature item (B2) | The shelter's light |
| Feature phrase, version 1 | the shelter's light on |
| Feature phrase, version 2 | the shelter's light off |
| Placement sentence (I2) | The man and the bus shelter are on the right side of the frame, small, seen from farther away. |
| Addition (B3) | a folded newspaper on the bench |
| Addition aspect item (B3) | The added folded newspaper |
| Restyle (B3) | as a watercolor painting in evening blues |

### SB-P6. The pond (person)

| Part | Text |
|---|---|
| Plan, version 1 | A girl feeds ducks at the edge of a pond. She crouches on the grass holding out bread, and a jogger runs along the far path. Soft morning light. Fresh greens and whites. |
| Plan, version 2 | A girl feeds ducks at the edge of a pond. She crouches on the grass holding out bread, and the far path is empty. Soft morning light. Fresh greens and whites. |
| Kind of feature | Passer-by |
| Feature item (B2) | Whether anyone is on the far path |
| Feature phrase, version 1 | a jogger running along the far path |
| Feature phrase, version 2 | the far path empty |
| Placement sentence (I2) | The girl is on the right side of the frame, small, seen from farther away. |
| Addition (B3) | a red ball on the grass |
| Addition aspect item (B3) | The added red ball |
| Restyle (B3) | as an oil painting with thick brushwork in fresh greens |

### SB-N1. The canoe (no person)

| Part | Text |
|---|---|
| Plan, version 1 | A red canoe rests on the sand at the edge of a still lake. It points toward the water. A clear sky glows at sunset. Blues and warm golds. |
| Plan, version 2 | A red canoe rests on the sand at the edge of a still lake. It points toward the water. Low clouds cover the sky at sunset. Greys with dim gold. |
| Kind of feature | Weather |
| Feature item (B2) | The sky |
| Feature phrase, version 1 | a clear sky glowing at sunset |
| Feature phrase, version 2 | low clouds covering the sky at sunset |
| Placement sentence (I2) | The canoe is on the right side of the frame, small, seen from farther away. |
| Addition (B3) | a paddle lying on the sand |
| Addition aspect item (B3) | The added paddle |
| Restyle (B3) | as an ink drawing with blue washes |

### SB-N2. The hallway (no person)

| Part | Text |
|---|---|
| Plan, version 1 | A wooden chair stands against the wall of a long hallway. A cat sleeps on its seat. Hard afternoon light from the far window. Pale yellow walls and dark wood. |
| Plan, version 2 | A wooden chair stands against the wall of a long hallway. Its seat is bare. Hard afternoon light from the far window. Pale yellow walls and dark wood. |
| Kind of feature | Animal |
| Feature item (B2) | Whether a cat is in the picture |
| Feature phrase, version 1 | a cat sleeping on the chair's seat |
| Feature phrase, version 2 | the chair's seat bare |
| Placement sentence (I2) | The chair is on the right side of the frame, small, seen from farther away. |
| Addition (B3) | a framed picture on the wall |
| Addition aspect item (B3) | The added framed picture |
| Restyle (B3) | as a flat poster in bold colors |

### SB-N3. The night street (no person; replaced by SB-R2 on 27 October 2026, see above)

| Part | Text |
|---|---|
| Plan, version 1 | A city street at night after rain. One car is parked at the curb. The streetlights are on, and the corner shop window is lit. Deep blues with orange highlights. |
| Plan, version 2 | A city street at night after rain. One car is parked at the curb. The streetlights are on, and the corner shop window is dark. Deep blues with orange highlights. |
| Kind of feature | Light |
| Feature item (B2) | The shop window |
| Feature phrase, version 1 | the corner shop window lit |
| Feature phrase, version 2 | the corner shop window dark |
| Placement sentence (I2) | The parked car is on the right side of the frame, small, seen from farther away. |
| Addition (B3) | a bicycle locked to a lamppost |
| Addition aspect item (B3) | The added bicycle |
| Restyle (B3) | as a watercolor painting in deep blues and oranges |

The streetlights stay on in both versions, so "orange highlights" fits both.

### SB-N4. The lemons (no person)

| Part | Text |
|---|---|
| Plan, version 1 | A bowl of lemons on a marble counter by an open window. One lemon lies cut in half beside the bowl, and a sparrow perches on the windowsill. Morning light from the window. Yellow and white. |
| Plan, version 2 | A bowl of lemons on a marble counter by an open window. One lemon lies cut in half beside the bowl, and the windowsill is empty. Morning light from the window. Yellow and white. |
| Kind of feature | Animal |
| Feature item (B2) | Whether a bird is in the picture |
| Feature phrase, version 1 | a sparrow perched on the windowsill |
| Feature phrase, version 2 | the windowsill empty |
| Placement sentence (I2) | The bowl of lemons is on the right side of the frame, small, seen from farther away. |
| Addition (B3) | a glass of water beside the bowl |
| Addition aspect item (B3) | The added glass of water |
| Restyle (B3) | as an oil painting with thick brushwork in yellows |

### SB-N5. The farmhouse (no person)

| Part | Text |
|---|---|
| Plan, version 1 | A white farmhouse on a low hill above a field. A wooden fence runs along the field. Morning fog lies over the field. Soft greens and greys. |
| Plan, version 2 | A white farmhouse on a low hill above a field. A wooden fence runs along the field. The morning air over the field is clear. Fresh greens under a pale blue sky. |
| Kind of feature | Weather |
| Feature item (B2) | The fog |
| Feature phrase, version 1 | morning fog lying over the field |
| Feature phrase, version 2 | clear morning air over the field |
| Placement sentence (I2) | The farmhouse is on the right side of the frame, small, seen from farther away. |
| Addition (B3) | a red mailbox by the fence |
| Addition aspect item (B3) | The added red mailbox |
| Restyle (B3) | as an ink drawing with grey washes |

### SB-N6. The terrace (no person)

| Part | Text |
|---|---|
| Plan, version 1 | Two empty café tables on a terrace at night. Chairs are pushed in around them. Strings of lights above the tables are lit. Warm golds against dark blue. |
| Plan, version 2 | Two empty café tables on a terrace at night. Chairs are pushed in around them. Strings of lights above the tables are unlit. Dark blues and greys. |
| Kind of feature | Light |
| Feature item (B2) | The lights above the tables |
| Feature phrase, version 1 | the strings of lights above the tables lit |
| Feature phrase, version 2 | the strings of lights above the tables unlit |
| Placement sentence (I2) | The two tables are on the right side of the frame, small, seen from farther away. |
| Addition (B3) | a potted palm beside the tables |
| Addition aspect item (B3) | The added potted palm |
| Restyle (B3) | as a flat poster in warm golds and blues |

### SB-R1. The vegetable garden (person, reserve)

| Part | Text |
|---|---|
| Plan, version 1 | An old woman weeds a vegetable bed in her garden. She kneels on a folded mat, and a hen pecks at the path beside her. Soft afternoon light. Greens and earthy browns. |
| Plan, version 2 | An old woman weeds a vegetable bed in her garden. She kneels on a folded mat, and the path beside her is empty. Soft afternoon light. Greens and earthy browns. |
| Kind of feature | Animal |
| Feature item (B2) | Whether a hen is in the picture |
| Feature phrase, version 1 | a hen pecking at the path beside the woman |
| Feature phrase, version 2 | the path beside the woman empty |
| Placement sentence (I2) | The woman and the vegetable bed are on the right side of the frame, small, seen from farther away. |
| Addition (B3) | a watering can beside the vegetable bed |
| Addition aspect item (B3) | The added watering can |
| Restyle (B3) | as a watercolor painting in soft greens |

### SB-R2. The pier (no person, reserve)

| Part | Text |
|---|---|
| Plan, version 1 | A wooden pier stretches out over a calm sea. A rowboat is tied to its last post. Bright sun shines on the water. Clear blues and pale wood. |
| Plan, version 2 | A wooden pier stretches out over a calm sea. A rowboat is tied to its last post. Dark storm clouds gather over the water. Slate greys and pale wood. |
| Kind of feature | Weather |
| Feature item (B2) | The weather over the water |
| Feature phrase, version 1 | bright sun shining on the water |
| Feature phrase, version 2 | dark storm clouds gathering over the water |
| Placement sentence (I2) | The pier and the rowboat are on the right side of the frame, small, seen from farther away. |
| Addition (B3) | a stack of crates on the pier |
| Addition aspect item (B3) | The added stack of crates |
| Restyle (B3) | as an oil painting with thick brushwork in blues |

### Which files each study uses

| Study | Scenes | Files per scene |
|---|---|---|
| B1 | All twelve, one per trial | V1 or I2 by list, shown alone, with plan version 1 |
| B2 | All twelve, one per trial | V1 or V2, with plan version 1 or 2 by list |
| B3 | All twelve, one per trial | Sketch cells: V1 or I2 by list, beside its own sketch or beside the other composition's sketch. Photograph cells: V1, then the addition or the restyle |

### Lists

All three studies order the twelve scenes SB-P1, SB-N1, SB-P2, SB-N2, and so on to SB-N6 (positions 0 to 11). In rotation k (0 to 11), slot j (0 to 11) shows the scene at position (j + k) modulo 12, so slots alternate between scenes with and without a person. Each study has 24 lists, numbered 0 to 23: list L uses rotation L modulo 12, and lists 0 to 11 differ from lists 12 to 23 as follows.

- **B1.** Lists 0 to 11 show V1 and lists 12 to 23 show I2. Its six cells are o (another artist prompted the image and Alex found it), a (prompt only), r (routine hours), b (choosing among versions from one prompt), c (revising the prompt) and d (the tool revising its own prompt); with these numbered 0 to 5 in that order, cell number n takes slots 2n and 2n + 1. Each cell falls once on a scene with a person and once on one without, and every scene appears in every cell four times across the 24 lists.
- **B2.** Lists 0 to 11 use plan version 1 and lists 12 to 23 plan version 2. Each slot carries one cell: an executor with matches or departs (the image matches the plan or departs from it) and chose or unseen. Slots 0 to 11 carry, in order: AI tool matches-chose, AI tool matches-unseen, camera matches-unseen, camera matches-chose, hired photographer matches-chose, hired photographer matches-unseen, AI tool departs-unseen, AI tool departs-chose, camera departs-chose, camera departs-unseen, hired photographer departs-unseen, hired photographer departs-chose. Each executor falls on two scenes with a person and two without, and within each executor, matches, departs, chose and unseen each fall once on each kind of scene. Across the 24 lists every scene appears in every cell twice, once under each plan version.
- **B3.** Lists 0 to 11 show V1 in the sketch cells and lists 12 to 23 show I2. With cells f, g, h, i, j and k numbered 0 to 5 in that order, cell number n takes slots 2n and 2n + 1. Each cell falls once on a scene with a person and once on one without, and every scene appears in every cell four times across the 24 lists.

Trial order is randomized, and the order is recorded.
