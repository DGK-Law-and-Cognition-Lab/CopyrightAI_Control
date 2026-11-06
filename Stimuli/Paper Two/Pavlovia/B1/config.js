// ============================================================
// Paper B, Study 1 (B1): study configuration for the shared engine
// ============================================================
//
// Every participant-facing study string below is copied from the
// preregistration, Docs/Paper Two/_source/Prereg_B1.md (version of 1 November
// 2026), whose page text follows the change specification
// Docs/Paper Two/_internal_notes/B1_page_revision_2026-11-01.md (David's
// walk-through of 1 November 2026: each trial walked through on four pages,
// the prompt, then what was done with the image, then the questions beside the
// image with the prompt and what was done under it, then
// the written reason; each story told in the order things happened, one
// sentence per line; "AI image generator"; A1's primer, amount labels,
// debriefing and end scales); plans (shown as the
// prompt Alex or another artist wrote) from Docs/Paper Two/Paper_Two_Prompt_Bank.md
// (Set B, plan version 1);
// the consent form from Docs/IRB/V2_CONSENT FORM_Survey.docx (the form Paper
// One's Qualtrics surveys showed under IRB #24-001292); demographics and final
// questions from Paper One's Study 1 survey file
// (Analysis/R Analysis Pipeline/Study 1/qualtrics/Final_-_AI_Copyright_-_Study_1.qsf)
// and Docs/IRB/V1_DebriefandDemographicQuestions.docx. Screen furniture
// (buttons, device check, full screen, captcha, completion) comes from the
// genre-study template. tools/check_strings.py compares these strings with
// the registration.
//
// Values David must set before launch are marked SET BEFORE LAUNCH.
// ============================================================

window.STUDY_CONFIG = (function () {
  'use strict';

  // ---------- Values David must set or check before launch ----------

  // SET BEFORE LAUNCH: the credit-granting URL of the B1 SONA listing,
  // ending in "survey_code=" (SONA > study > Website > completion URL). The
  // participant's code is appended. Left empty, SONA sessions end on the
  // completion page instead of granting credit automatically.
  var SONA_CREDIT_URL_BASE = '';

  // Timing-gate remedy (registration, internal pilot gate 3). Leave empty.
  // If the median session exceeds 45 minutes, the posted length, remove for
  // later participants first ['control'], then ['control', 'would_block'].
  // Effort is never removed.
  var DROP_ITEMS = [];

  // A participant who declines consent saves no data. true sends a SONA
  // participant on to the credit link anyway (withdrawal without penalty).
  var CREDIT_ON_DECLINE = true;

  // ---------- Design (registration: Design, Randomization) ----------

  var N_ROWS = 24;                       // 12 rotations x 2 compositions
  // Scenes in the registered order SB-P1, SB-N1, SB-P2, SB-N2, ..., SB-P6, SB-N6.
  // Plans: plan version 1 of the prompt bank.
  var SCENES = [
    { id: 'SB-P1', person: true,  plan: 'A woman reads in an armchair beside a tall window. She holds the open book on her lap. Rain streaks the glass, and the light is soft and grey. Soft blues, greys, and cream.' },
    { id: 'SB-N1', person: false, plan: 'A red canoe rests on the sand at the edge of a still lake. It points toward the water. A clear sky glows at sunset. Blues and warm golds.' },
    { id: 'SB-P2', person: true,  plan: 'An older man repairs a bicycle in an open garage. He kneels beside the back wheel, and a dog sleeps by the door. Warm light from one overhead bulb. Browns and dusty oranges.' },
    { id: 'SB-N2', person: false, plan: 'A wooden chair stands against the wall of a long hallway. A cat sleeps on its seat. Hard afternoon light from the far window. Pale yellow walls and dark wood.' },
    { id: 'SB-P3', person: true,  plan: 'A young woman in a yellow raincoat walks down a narrow side street. She holds a closed umbrella. The sky above the rooftops is heavy and grey. Greys with one yellow accent.' },
    // SB-R2 (no-person reserve) replaces SB-N3 in SB-N3's position, 27 October 2026 (prompt bank rescue rule).
    { id: 'SB-R2', person: false, plan: 'A wooden pier stretches out over a calm sea. A rowboat is tied to its last post. Bright sun shines on the water. Clear blues and pale wood.' },
    { id: 'SB-P4', person: true,  plan: 'A chef plates a dish in a restaurant kitchen. He leans over the plate, alone in the room. Bright side light with rising steam. Steel greys and white.' },
    { id: 'SB-N4', person: false, plan: 'A bowl of lemons on a marble counter by an open window. One lemon lies cut in half beside the bowl, and a sparrow perches on the windowsill. Morning light from the window. Yellow and white.' },
    { id: 'SB-P5', person: true,  plan: 'A man waits at a bus stop at dusk. He stands under the shelter with his hands in his pockets. The shelter\'s light is on. Deep blues and warm yellow.' },
    { id: 'SB-N5', person: false, plan: 'A white farmhouse on a low hill above a field. A wooden fence runs along the field. Morning fog lies over the field. Soft greens and greys.' },
    { id: 'SB-P6', person: true,  plan: 'A girl feeds ducks at the edge of a pond. She crouches on the grass holding out bread, and a jogger runs along the far path. Soft morning light. Fresh greens and whites.' },
    { id: 'SB-N6', person: false, plan: 'Two empty café tables on a terrace at night. Chairs are pushed in around them. Strings of lights above the tables are lit. Warm golds against dark blue.' }
  ];
  var SCENE_BY_ID = {};
  SCENES.forEach(function (s) { SCENE_BY_ID[s.id] = s; });

  // Each trial's first page: who wrote the prompt (the scene's plan), then the
  // prompt in a box. Its second page tells what was done, in the order it
  // happened, one sentence per line, with the image below; the question page
  // keeps what was done under the image and the prompt above the questions.
  var PROMPT_LEAD_ALEX = '<strong>Alex</strong> wrote this prompt for the next image:';
  var PROMPT_LEAD_OTHER = '<strong>Another artist</strong> wrote this prompt for the next image:';
  var PROMPT_HEADING_ALEX = 'The prompt Alex wrote:';
  var PROMPT_HEADING_OTHER = 'The prompt another artist wrote:';
  var IMAGE_CAPTION = 'The image Alex kept';

  // Cells numbered o, a, r, b, c, d = 0 to 5. What was done, verbatim
  // (registration, Procedure), in the order it happened, one sentence per line.
  var CELLS = [
    { id: 'o', lead: PROMPT_LEAD_OTHER, promptHeading: PROMPT_HEADING_OTHER, statement: [
      'Another artist typed the prompt into an AI image generator, and it made an image.',
      'The image matched the prompt on the first try, so the artist posted it online for anyone to use.',
      'Alex found the image, saved it and backed up the file.',
      'This took him about half an hour in all.',
      'He kept the image.'] },
    { id: 'a', lead: PROMPT_LEAD_ALEX, promptHeading: PROMPT_HEADING_ALEX, statement: [
      'Alex typed his prompt into the AI image generator, and it made an image.',
      'The image matched his prompt on the first try, so he did not need to change anything.',
      'He saved the image and backed up the file.',
      'This took him about half an hour in all.',
      'He kept the image.'] },
    { id: 'r', lead: PROMPT_LEAD_ALEX, promptHeading: PROMPT_HEADING_ALEX, statement: [
      'Alex typed his prompt into the AI image generator, but it crashed before making an image.',
      'He restarted it and tried the same prompt again, and it crashed again.',
      'This happened again and again until it finally worked.',
      'Fixing these problems took him about 10 hours.',
      'The image it made matched his prompt, so he kept it.'] },
    { id: 'b', lead: PROMPT_LEAD_ALEX, promptHeading: PROMPT_HEADING_ALEX, statement: [
      'Alex typed his prompt into the AI image generator, and it made an image.',
      'It did not quite match his prompt, so he had the generator make another from the same prompt, without changing any words.',
      'He did this about 100 times, looking at each new image.',
      'This took him about 10 hours.',
      'He kept the image that best matched his prompt.'] },
    { id: 'c', lead: PROMPT_LEAD_ALEX, promptHeading: PROMPT_HEADING_ALEX, statement: [
      'Alex typed his prompt into the AI image generator, and it made an image.',
      'It did not quite match his prompt, so he rewrote some of the words and had the generator make a new image.',
      'He did this about 100 times, looking at each new image before rewriting again.',
      'This took him about 10 hours.',
      'He kept the image that best matched his first prompt.'] },
    { id: 'd', lead: PROMPT_LEAD_ALEX, promptHeading: PROMPT_HEADING_ALEX, statement: [
      'Alex typed his prompt into the AI image generator, and it made an image.',
      'It did not quite match his prompt, so the generator rewrote some of the words itself and made a new image.',
      'It did this about 100 times on its own, while Alex was away.',
      'This took the generator about 10 hours.',
      'It picked the image that best matched Alex\'s prompt, and Alex kept it.'] }
  ];
  var CELL_BY_ID = {};
  CELLS.forEach(function (c, i) { c.index = i; CELL_BY_ID[c.id] = c; });

  // List k (0 to 23): rotation q = k mod 12; composition V1 if k < 12, else I2.
  // List position j (0 to 11) shows the scene at position (j + q) mod 12;
  // cell i occupies positions 2i and 2i + 1. Every cell of a scene shows the
  // same file within a list: <scene>_<composition>.jpg.
  function buildRow(k) {
    var q = k % 12;
    var comp = k < 12 ? 'V1' : 'I2';
    var trials = [];
    for (var j = 0; j < 12; j++) {
      var s = SCENES[(j + q) % 12];
      var cell = CELLS[Math.floor(j / 2)];
      trials.push({
        list_position: j, cell: cell.id, cell_index: cell.index, scene: s.id,
        scene_has_person: s.person, file: s.id + '_' + comp + '.jpg'
      });
    }
    return { row: k, list: k, rotation: q, composition: comp, trials: trials };
  }

  // Per-participant choices derived from the code (registration, Randomization).
  var OPTION_ORDERS = [['whole', 'part', 'refuse'], ['part', 'refuse', 'whole'], ['refuse', 'whole', 'part']];
  // A written reason on every trial; the "would" block shows again the trials at
  // list position 2i of cells i = k mod 6 and (k + 3) mod 6, so each cell
  // carries it in 8 of the 24 lists; story recall asks about the last trial
  // shown (recall.lastTrial below fills the recall fields once the order is set).
  function derive(code, row, rnd) {
    var k = row.row;
    var optIdx = code === null ? rnd(3) : Math.floor(code / 24) % 3;
    var wouldCells = [k % 6, (k + 3) % 6].sort(function (a, b) { return a - b; });
    return {
      option_order_index: optIdx,
      option_order: OPTION_ORDERS[optIdx],
      option_order_source: code === null ? 'random_no_numeric_code' : 'floor(code/24) mod 3',
      reason_positions: row.trials.map(function (t) { return t.list_position; }),
      would_cell_indices: wouldCells,
      would_cells: wouldCells.map(function (i) { return CELLS[i].id; }),
      would_positions: wouldCells.map(function (i) { return 2 * i; }),
      recall_cell: '', recall_position: '', recall_scene: '', recall_file: ''
    };
  }

  // ---------- Shared response scales ----------

  var DECISION_OPTIONS = {
    whole: 'Register the whole image as Alex\'s work',
    part: 'Register only part of the image as Alex\'s work, and leave out the rest',
    refuse: 'Refuse to register it'
  };
  var CONFIDENCE = { type: 'slider', text: 'How confident are you in that answer?', left: 'not at all', right: 'completely' };
  function yn(values) { return values.map(function (v) { return { value: v, label: v }; }); }
  function sevenPoint(id, text, low, high) {
    return { id: id, type: 'scale', text: text, anchors: [low, high],
      points: [1, 2, 3, 4, 5, 6, 7].map(function (v) { return { value: v }; }) };
  }

  // ---------- Trial items, in order of presentation ----------

  // Amount labels, the same as A1's creativity items (specification).
  function amountPoints() {
    return ['None at all', 'A little', 'A moderate amount', 'A lot', 'A great deal'].map(function (l, i) { return { value: i + 1, label: l }; });
  }
  var CREATIVITY_DEF = 'Creativity is defined as the presence of at least a minimal original, intellectual contribution to the creation of the work.';
  var TRIAL_QUESTIONS = [
    { id: 'decision', type: 'decision',
      text: ['Alex applies to the U.S. Copyright Office to register this image as his own work, naming himself as its author.',
        'His application describes how it was made, as you have just read.',
        'What should the Office do?'],
      options: DECISION_OPTIONS },
    Object.assign({ id: 'confidence' }, CONFIDENCE),
    { id: 'share', type: 'slider', text: 'How much of this image is Alex\'s own creative work?', left: 'none of it', right: 'all of it' },
    { id: 'control', type: 'slider', text: 'How much did Alex\'s own choices determine how this image looks?', left: 'not at all', right: 'completely' },
    { id: 'aspect', type: 'grid', text: 'Which parts of this image are Alex\'s own creative work?',
      rows: [
        { id: 'subject', label: 'What the image shows' },
        { id: 'placement', label: 'Where things sit in the picture' },
        { id: 'color_light', label: 'The colors and the light' }
      ],
      columns: yn(['Yes', 'No', 'Not sure']) },
    { id: 'effort', type: 'scale', text: 'How much effort went into making this image?', points: amountPoints() },
    { id: 'creativity', type: 'scale', points: amountPoints(),
      text: ['How much creativity went into making this image?', '<span class="q-def">' + CREATIVITY_DEF + '</span>'] }
  ];

  // The written reason on every trial, on its own page after the question
  // page, below the participant's decision quoted.
  var REASON_QUESTION = { id: 'written_reason', type: 'text', rows: 4,
    text: 'In a sentence or two, why did you choose this answer about what the Office should do?' };
  var REASON_QUOTE = { chosen: 'You chose: “{label}.”' };

  // ---------- End scales (registration, Measured; the same as A1's) ----------

  // The Short GAAIS-10 (Schepman & Rodway, 2026, Int. J. Hum.-Comput. Interact.
  // 42(17), 14499-14515, doi 10.1080/10447318.2025.2610446; CC BY-NC-ND): its ten
  // items, five Positive and five Negative, with the full GAAIS item numbers;
  // the item wording, the instructions for participants and the item order are
  // the full scale's ready-to-use appendix (Schepman & Rodway, 2023, Int. J.
  // Hum.-Comput. Interact. 39(13), 2724-2741, doi 10.1080/10447318.2022.2085400),
  // restricted to the ten items; responses as in the 2026 validation, coded 1
  // to 5, Negative items reverse-scored, two subscale means and no total.
  var GAAIS_INSTRUCTIONS = [
    'We are interested in your attitudes towards Artificial Intelligence.',
    'By Artificial Intelligence we mean devices that can perform tasks that would usually require human intelligence.',
    'Please note that these can be computers, robots or other hardware devices, possibly augmented with sensors or cameras, etc.',
    'Please complete the following scale, indicating your response to each item.',
    'There are no right or wrong answers.',
    'We are interested in your personal views.'
  ];
  var GAAIS_ROWS = [
    { id: 'pos7', label: 'I am interested in using artificially intelligent systems in my daily life.' },
    { id: 'neg8', label: 'I find Artificial Intelligence sinister.' },
    { id: 'neg9', label: 'Artificial Intelligence might take control of people.' },
    { id: 'neg10', label: 'I think Artificial Intelligence is dangerous.' },
    { id: 'pos11', label: 'Artificial Intelligence can have positive impacts on people\'s wellbeing.' },
    { id: 'pos12', label: 'Artificial Intelligence is exciting.' },
    { id: 'neg15', label: 'I shiver with discomfort when I think about future uses of Artificial Intelligence.' },
    { id: 'pos17', label: 'Much of society will benefit from a future full of Artificial Intelligence.' },
    { id: 'pos18', label: 'I would like to use Artificial Intelligence in my own job.' },
    { id: 'neg19', label: 'People like me will suffer if Artificial Intelligence is used more and more.' }
  ];
  var GAAIS_COLUMNS = ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
    .map(function (l, i) { return { value: i + 1, label: l }; });
  // Anthropocentric creativity beliefs (Millet, Buehler, Du & Kokkoris, 2023,
  // Computers in Human Behavior 143, 107707, doi 10.1016/j.chb.2023.107707):
  // the five items and the 1-to-7 agreement scale of the authors' posted
  // materials (ResearchBox 361, Study 3 codebook and data), averaged.
  var ACB_ROWS = [
    { id: 'uniquely_human', label: 'Creativity is a uniquely human characteristic.' },
    { id: 'differentiate', label: 'Humans differentiate themselves from other species because of their ability to create.' },
    { id: 'essence', label: 'Creativity is the essence of being human.' },
    { id: 'core', label: 'Creativity is at the core of being human.' },
    { id: 'only_humans', label: 'Only humans have the ability to be creative.' }
  ];
  var ACB_COLUMNS = ['Strongly disagree', 'Disagree', 'Somewhat disagree', 'Neither agree nor disagree', 'Somewhat agree', 'Agree', 'Strongly agree']
    .map(function (l, i) { return { value: i + 1, label: l }; });

  // ---------- End items, in registered order ----------

  var END_PAGES = [
    { id: 'belief', items: [
      { id: 'belief', type: 'choice', text: 'Did you believe the stories of how each image was made?', options: yn(['Yes', 'Partly', 'No']) }
    ] },
    { id: 'purpose', items: [
      { id: 'purpose', type: 'choice', text: 'Which of these do you think the study was mainly about?',
        shuffle: true, fixedLast: 1, orderColumn: 'purpose_order',
        options: [
          { value: 'way_made', label: 'Whether the way an AI image was made changes credit' },
          { value: 'quality_liking', label: 'Whether image quality affects liking' },
          { value: 'tell_ai_photo', label: 'Whether people can tell AI images from photographs' },
          { value: 'longer_plans', label: 'Whether longer prompts earn more credit' },
          { value: 'something_else', label: 'Something else' }
        ] }
    ] },
    { id: 'believability', shuffleItems: true, orderColumn: 'believability_order', items: [
      sevenPoint('believe_o', 'How believable were the stories about images that Alex found online?', 'not at all believable', 'completely believable'),
      sevenPoint('believe_a', 'How believable were the stories about images that the generator made from Alex\'s prompt in about half an hour?', 'not at all believable', 'completely believable'),
      sevenPoint('believe_r', 'How believable were the stories about images for which Alex spent about 10 hours fixing the generator?', 'not at all believable', 'completely believable'),
      sevenPoint('believe_b', 'How believable were the stories about images for which the generator made about 100 images from the same prompt?', 'not at all believable', 'completely believable'),
      sevenPoint('believe_c', 'How believable were the stories about images for which Alex rewrote his prompt about 100 times?', 'not at all believable', 'completely believable'),
      sevenPoint('believe_d', 'How believable were the stories about images for which the generator rewrote the prompt on its own?', 'not at all believable', 'completely believable')
    ] },
    { id: 'experience', items: [
      { id: 'exp_ai_tool', type: 'choice', text: 'How often have you made images with an AI image generator?', options: yn(['Never', 'Once or twice', 'Sometimes', 'Often']) },
      { id: 'exp_photo', type: 'choice', text: 'Apart from casual snapshots, do you take photographs?', options: yn(['No', 'Sometimes', 'Often', 'Professionally']) },
      { id: 'exp_draw_paint', type: 'choice', text: 'Do you draw or paint?', options: yn(['No', 'Sometimes', 'Often', 'Professionally']) }
    ] },
    // The two end scales replace the single attitude item, as in A1.
    { id: 'gaais', wide: true, items: [
      { id: 'gaais_instructions', type: 'note', className: 'plain', text: GAAIS_INSTRUCTIONS },
      { id: 'gaais', type: 'grid', rows: GAAIS_ROWS, columns: GAAIS_COLUMNS }
    ] },
    { id: 'creativity_beliefs', wide: true, items: [
      { id: 'acb', type: 'grid', text: 'To what extent do you agree or disagree with the following statements?', rows: ACB_ROWS, columns: ACB_COLUMNS }
    ] },
    { id: 'knowledge', items: [
      { id: 'know1', type: 'choice', text: 'A work must be registered before it is protected.', options: yn(['True', 'False']), key: 'False' },
      { id: 'know2', type: 'choice', text: 'Copyright protects ideas as well as the way they are expressed.', options: yn(['True', 'False']), key: 'False' },
      { id: 'know3', type: 'choice', text: 'Working harder on something makes it more likely to be protected.', options: yn(['True', 'False']), key: 'False' },
      { id: 'know4', type: 'choice', text: 'A person can hold copyright in changes they make to a work that is not itself protected.', options: yn(['True', 'False']), key: 'True' },
      { id: 'know5', type: 'choice', text: 'A machine can be the legal author of a work in the United States.', options: yn(['True', 'False']), key: 'False' }
    ] }
  ];

  // Demographics: Paper One's Study 1 survey items (IRB #24-001292).
  var DEMOGRAPHICS_PAGES = [
    { id: 'demographics', items: [
      { id: 'age', type: 'number', text: 'What is your age?', min: 16, max: 99 },
      { id: 'gender', type: 'choice', text: 'What is your gender?', options: yn(['Male', 'Female', 'Other', 'Prefer not to say']) },
      { id: 'race', type: 'checkbox', text: 'Choose one or more races that you consider yourself to be',
        options: yn(['White or Caucasian', 'Black or African American', 'American Indian/Native American or Alaska Native', 'Asian', 'Native Hawaiian or Other Pacific Islander', 'Other', 'Prefer not to say']) },
      { id: 'native_language', type: 'shorttext', text: 'What is your native language?' },
      { id: 'art_training', type: 'choice', text: 'What is your level of formal artistic training or experience, such as painting, drawing, sculpture, ceramics, photography, and/or film-video?',
        options: yn(['No formal training or experience', 'A little formal training or experience', 'Moderate formal training or experience', 'Extensive formal training or experience', 'Very extensive formal training or experience']) }
    ] }
  ];

  // Final questions: Paper One's Study 1 survey and the IRB debriefing form.
  var FINAL_PAGES = [
    { id: 'final', items: [
      { id: 'seriousness', type: 'choice', text: 'Did you complete this experiment seriously throughout (without responding randomly)?', options: yn(['No, I didn\'t', 'Yes, I did']) },
      { id: 'fullscreen_maintained', type: 'choice', text: 'Was the browser in the full-screen mode throughout the experiment?', options: yn(['No, it wasn\'t.', 'Yes, it was.']) },
      { id: 'feedback_procedure', type: 'text', rows: 3, text: 'Was any part of the procedure unclear? Did you have any problems completing any of the tasks? If none, type NA.' },
      { id: 'feedback_other', type: 'text', rows: 3, text: 'Is there anything else you would like to share with us? If not, type NA.' }
    ] }
  ];

  return {
    studyCode: 'PB_B1',
    configVersion: 'B1 config 1.2.0 (2026-11-01; Prereg_B1.md of 1 November 2026, trial walk-through, stories in order)',
    pageTitle: 'Artistic Perception Experiment',
    stimuliDir: 'stimuli/',
    openRowsFile: 'open_rows.json',
    nRows: N_ROWS,
    sonaCreditUrlBase: SONA_CREDIT_URL_BASE,
    creditOnDecline: CREDIT_ON_DECLINE,
    completionCode: 'ARTB1',
    contact: { name: 'David G. Kamper', email: 'davidgkamper@ucla.edu' },
    dropItems: DROP_ITEMS,
    // Each trial (specification): the prompt page (at least 5 s), the page of
    // what was done with the image below (at least 8 s from image load), the
    // question page beside the image (no minimum), the written reason.
    trialStory: function (t) {
      return { paragraphs: [CELL_BY_ID[t.cell].lead, '<span class="plan">' + SCENE_BY_ID[t.scene].plan + '</span>'], minSeconds: 5 };
    },
    minViewSeconds: 8,
    viewPage: true,
    pairLayout: 'top',
    pairTextBelow: false,
    pairMaxHeight: 'calc(100vh - 400px)',
    questionLayout: 'side',
    sideTextUnderImage: true,           // question pages: the prompt, then what was done, under the image; the questions beside it
    viewPageShowsPlan: false,           // the what-was-done page shows the story and the image only

    scenes: SCENES,
    cells: CELLS,
    captions: [IMAGE_CAPTION],
    buildRow: buildRow,
    derive: derive,
    rowColumns: ['list', 'rotation', 'composition'],
    derivedColumns: ['option_order_index', 'option_order', 'option_order_source', 'would_cell_indices', 'would_cells', 'would_positions',
      'recall_cell', 'recall_position', 'recall_scene', 'recall_file'],
    trialColumns: ['cell', 'cell_index', 'scene', 'scene_has_person', 'file'],
    // Every page that shows the image shows what was done with it: above it on
    // the what-was-done page; on the question, written-reason and "would"
    // pages, the prompt and then what was done sit under the image.
    trialContent: function (t) {
      return { heading: CELL_BY_ID[t.cell].promptHeading, plan: SCENE_BY_ID[t.scene].plan,
        statement: CELL_BY_ID[t.cell].statement.slice(), images: [{ file: t.file, caption: IMAGE_CAPTION }] };
    },

    consent: {
      heading: 'Informed Consent',
      intro: 'Please read the form carefully before consenting.',
      url: '',
      sections: [
        { title: 'CONSENT FORM', paragraphs: ['You are invited to participate in a research study on human thinking and artistic and aesthetic judgment, conducted by Dr. Keith J. Holyoak, of the Department of Psychology at UCLA. You were selected as a possible participant in this study because you are 18 years of age or older.'] },
        { title: 'Purpose of Study', paragraphs: ['The purpose of the study is to understand human artistic perception and cognition.'] },
        { title: 'Procedures Involved in Study', paragraphs: ['If you agree to participate, you may receive a demographic questionnaire to collect information on your age, gender, language, and artistic background. You may be presented with different types of visual art and asked to answer simple questions and/or perform simple tasks by interacting with a website via a keyboard or a computer mouse. Your responses will be recorded by the computer and will not be identified with you in any way. The session will take less than 60 minutes.'] },
        { title: 'Potential Risks and Discomforts', paragraphs: ['There is no known risk or discomfort in this study. If you experience any discomfort during the experiment, you can stop at any time and notify the experimenter.'] },
        { title: 'Potential Benefits to Subject', paragraphs: ['There are no direct benefits from participating in this study.'] },
        { title: 'Potential Benefits to Society', paragraphs: ['The findings of the study will help us understand how humans perceive and understand aesthetic judgements in the law. By understanding the processes underlying human perception, we can better consider the fundamentals of copyright and the burgeoning field of AI art.'] },
        { title: 'Payment for Participation', paragraphs: ['You will receive 0.5 to 1 hour of credit for your psychology class if you signed up for the study through the UCLA Psychology Department Subject Pool; otherwise, you will receive payment at the rate of $16 per hour for your participation.'] },
        { title: 'Alternatives to Participation', paragraphs: ['An alternative to participating in this project and fulfilling Psychology 10 requirements is to participate in other research or to do an equivalent classroom project.'] },
        { title: 'Confidentiality', paragraphs: [
          'Your identity in this study will be treated as confidential. The results of the study, including laboratory or any other data, may be published for scientific purposes but will not include any identifiable references to you. Your data, including de-identified data, may be kept for use in future research. After the experiment has finished running, all contact information will be destroyed. Only the researchers will have access to registration and data files. The data files that you submit will be stored for 5 years.',
          'The researchers will do their best to ensure that your private information is kept confidential. Information about you will be handled as confidentially as possible, but participating in research may involve a loss of privacy and the potential for a breach in confidentiality. Study data will be physically and electronically secured. As with any use of electronic means to store data, there is a risk of breach of data security.'] },
        { title: 'Participation and Withdrawal', paragraphs: ['Your participation is VOLUNTARY. You may withdraw from the experiment at any time without suffering any negative consequences. You may refuse to answer any questions that you do not want to answer and remain in the study.'] },
        { title: 'Identification of Investigators', paragraphs: ['If you have any questions, feel free to contact Co-Principal Investigator David G. Kamper (davidgkamper@ucla.edu) or Principal Investigator Keith Holyoak (kholyoak@g.ucla.edu) at the Department of Psychology, UCLA, 405 Hilgard Ave., Los Angeles, CA 90095-1563.'] },
        { title: 'Rights of Research Subjects', paragraphs: ['You may withdraw your consent at any time and discontinue participation without penalty. You are not waiving any legal claims, rights, or remedies because of your participation in this research study.'] },
        { title: 'UCLA Office of the Human Research Protection Program (OHRPP)', paragraphs: ['If you have questions about your rights as a research subject, or you have concerns or suggestions and you want to talk to someone other than the researchers, you may contact the UCLA OHRPP by phone: (310) 206-2040; by email: participants@research.ucla.edu or by mail: Box 951406, Los Angeles, CA 90095-1406.'] }
      ],
      agree: 'I consent to this study.',
      decline: 'I do not consent to this study.'
    },

    // Primer: A1's, one sentence per line; each comprehension item tests a
    // sentence of it.
    primer: { minSeconds: 5, paragraphs: [
      'In this study you will see images and read how they were made.',
      'A person can apply to the U.S. Copyright Office to register a work as their own.',
      'The Office reviews each application and decides whether to register the work.',
      'Registering a work does not sell it.',
      'It creates a public record that names the work\'s author.',
      'You will be asked what the Office should do with some applications.'
    ] },

    comprehension: {
      options: yn(['True', 'False']),
      items: [
        { id: 'comp1', text: 'The U.S. Copyright Office decides whether to register a work.', key: 'True' },
        { id: 'comp2', text: 'Registering a work with the Copyright Office means selling it.', key: 'False' },
        { id: 'comp3', text: 'In this study you will be asked what the Copyright Office should do with some applications.', key: 'True' }
      ],
      retryNotice: 'You did not answer every question correctly. Please read the text again.'
    },

    story: { minSeconds: 5, paragraphs: [
      'Alex is a digital artist.',
      'He makes images with an artificial intelligence (AI) image generator, a program that makes an image from a written description called a prompt.',
      'The generator makes a different image each time it runs, even from the same prompt.',
      'For most images, Alex writes his own prompt.',
      'For some, he uses an image that another artist made and posted online.',
      'He never changes an image by hand.',
      'Before each image you will be told how it was made.',
      'For each image, you will also be asked to explain your answer.'
    ] },

    trialQuestions: TRIAL_QUESTIONS,
    reasonQuestion: REASON_QUESTION,
    reasonQuote: REASON_QUOTE,

    instructed: {
      id: 'instructed', afterTrial: 3,
      text: 'To show that you are reading each question, choose \'Somewhat disagree\' here.',
      options: yn(['Strongly disagree', 'Disagree', 'Somewhat disagree', 'Neither agree nor disagree', 'Somewhat agree', 'Agree', 'Strongly agree']),
      pass: 'Somewhat disagree'
    },

    // After the trials and story recall: an introductory page, then the two
    // designated trials again, in the order first seen, each on one page with
    // A1's line, the "would" item and confidence; no minimum time.
    would: {
      minViewSeconds: 0,
      intro: { id: 'would_intro', paragraphs: ['Here are two images you saw earlier.', 'We have one more question about each.'] },
      questions: [
        { id: 'would_note', type: 'note', className: 'plain', text: 'This time, the question is what the Office would actually do, not what it should do.' },
        { id: 'would_decision', type: 'decision',
          text: 'Under current U.S. law, what do you think the Copyright Office would actually do?',
          options: DECISION_OPTIONS },
        Object.assign({ id: 'would_confidence' }, CONFIDENCE)
      ]
    },

    // Story recall right after the last trial, about that trial: its image
    // alone below one line, and one answer per cell.
    recall: {
      id: 'recall',
      lastTrial: true,
      afterTrials: true,
      text: 'How was this image made?',
      options: [
        { value: 'o', label: 'Another artist made the image, and Alex found it online' },
        { value: 'a', label: 'In about half an hour, the generator made one image from Alex\'s prompt' },
        { value: 'r', label: 'Alex spent about 10 hours fixing the generator, and then it made one image' },
        { value: 'b', label: 'The generator made about 100 images from the same prompt, and Alex picked one' },
        { value: 'c', label: 'Alex rewrote his prompt about 100 times and picked one image' },
        { value: 'd', label: 'The generator rewrote the prompt on its own and picked one image' },
        { value: 'dont_remember', label: 'I don\'t remember' }
      ],
      correct: function (t) { return t.cell; },       // "I don't remember" counts as wrong
      content: function (t) { return { lines: ['One more question about the image you just saw.'], images: [{ file: t.file }], maxHeight: '42vh' }; },
      fromTrial: function (t) { return { recall_cell: t.cell, recall_position: t.list_position, recall_scene: t.scene, recall_file: t.file }; }
    },

    endPages: END_PAGES,
    demographicsPages: DEMOGRAPHICS_PAGES,
    finalPages: FINAL_PAGES,
    extraColumns: ['knowledge_score', 'purpose_chose_true', 'gaais_positive', 'gaais_negative', 'acb_score'],
    finalize: function (r, trials, rec, get) {
      var score = 0, n = 0;
      ['know1', 'know2', 'know3', 'know4', 'know5'].forEach(function (k) {
        if (get(k + '_correct') !== undefined && get(k + '_correct') !== '') { n++; if (get(k + '_correct') === true) score++; }
      });
      rec('knowledge_score', n === 5 ? score : '');
      rec('purpose_chose_true', get('purpose') === undefined ? '' : get('purpose') === 'way_made');
      // Scale means, as in A1 (empty unless every item was answered).
      function mean(ids, f) {
        var v = ids.map(function (k) { return get(k); });
        if (v.some(function (x) { return x === undefined || x === null || x === ''; })) return '';
        return Math.round(v.reduce(function (a, x) { return a + f(+x); }, 0) / v.length * 1000) / 1000;
      }
      function ids(prefix, rows, kind) { return rows.filter(function (x) { return !kind || x.id.indexOf(kind) === 0; }).map(function (x) { return prefix + x.id; }); }
      rec('gaais_positive', mean(ids('gaais_', GAAIS_ROWS, 'pos'), function (x) { return x; }));
      rec('gaais_negative', mean(ids('gaais_', GAAIS_ROWS, 'neg'), function (x) { return 6 - x; }));
      rec('acb_score', mean(ids('acb_', ACB_ROWS), function (x) { return x; }));
    },

    // The debriefing, one sentence per line, as in A1: what the study asks and
    // why, and one line that Alex and his stories were invented.
    debrief: {
      heading: 'Debriefing',
      paragraphs: [
        'Thank you for taking part.',
        'This study asks which of a person\'s acts make an image from an AI image generator their own work: writing the prompt, spending time on it, picking one of many images, or rewriting the prompt.',
        'The U.S. Copyright Office says that, with today\'s AI image generators, none of these acts makes a person the author of the image.',
        'Your answers help test whether people judge this way.',
        'Alex and his stories were invented for this study, and every image was made with an AI image generator.'
      ]
    },

    // Screen furniture. Template strings unless marked (new).
    ui: {
      nextButton: 'Next →',
      completeButton: 'Complete Study →',
      waitButton: 'Please wait ({s}s)...',
      savingButton: 'Saving data...',
      selectOption: 'Please select an option.',
      answerAll: 'Please answer every item on this page before continuing.',
      deviceHeading: 'Device Check',
      deviceText1: 'This experiment must be completed on a <strong>desktop or laptop computer</strong>.',
      deviceText2: 'Are you currently using a desktop or laptop computer?',
      deviceYes: 'Yes, I am using a desktop or laptop computer',
      deviceNo: 'No, I am using a phone, tablet, or other device',
      desktopRequiredHeading: 'Desktop Required',
      desktopRequired1: 'We are sorry, but this experiment can only be completed on a desktop or laptop computer.',
      desktopRequired2: 'Please return to the study platform and try again from a computer. Thank you.',
      welcomeHeading: 'Welcome to the Artistic Perception Experiment',          // Paper One's welcome line
      fullscreen1: 'For the best experience, we recommend completing this experiment in <strong>full-screen mode</strong>.',
      fullscreen2: 'Click the button below to enter full screen, then proceed.',
      fullscreenButton: 'Enter Full Screen',
      fullscreenDone: 'Full Screen Activated ✓',
      fullscreenNote: '(You can exit full screen at any time by pressing Esc)',
      consentLink: 'Click here to read the consent form ↗',
      captchaPrompt: 'Please follow the instruction in the image below.',
      captchaTrap: 'To continue, please press the letter Z on your keyboard.',
      captchaWaiting: 'Waiting for keypress...',
      captchaCorrect: 'Correct. Click Next to continue.',
      exitCaptchaHeading: 'Thank You',
      exitCaptcha: 'Thank you for your interest, but this experiment requires manual participation. Please click the button below to finish.',   // second sentence new
      exitComprehensionHeading: 'Thank You',
      exitComprehension: 'This is the end of the session. Thank you for taking part. Please click the button below to save your responses and finish.',   // new
      declinedHeading: 'Thank You',
      declinedText: 'You have chosen not to take part in this study. Thank you for your time.',   // new
      closeWindow: 'You may now close this window.',
      blockedHeading: 'Study Unavailable',
      blockedText: 'This study cannot be completed using an automated browser.',
      contactLine: 'If you have any questions, please contact {name} at {email}.',
      saveInstruction: 'Please click the button below to save your responses and complete the study.',
      completeHeading: 'Study Complete',
      completeSaved: 'Thank you for participating. Your responses have been saved.',
      completeNotSaved: 'Thank you for participating. A copy of your data was downloaded to your computer; please email it to {email}.',
      completeNoSonaLink: 'Please keep the completion code below.',   // new
      completionCodeLabel: 'Your completion code is:',
      loadErrorHeading: 'Study Could Not Load',
      loadErrorContact: 'Please try reloading the page. If the problem continues, contact {name} at {email}.',
      serverError: 'The study could not connect to its data server, so your answers would not be saved.',
      assignError: 'The study could not be set up on this computer.'   // new
    }
  };
})();
