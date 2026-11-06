#!/usr/bin/env node
// Print every participant-facing string of a study's config.js as JSON lines
// {path, kind, text}, for tools/check_strings.py.  Usage: node tools/dump_config.js B1/config.js
// Parts a study does not have are skipped (B1: plans and cells; A1: added
// elements, statements built from them, titles, image labels, the pages
// before block 2, text items, introductory pages and lines, the quoted-answer
// lines of the written-reason box; since 1.3.0 the pages of the follow-up
// section, and no in-trial written reason or "would" block). Text given as an
// array of lines (A1 since 1 November 2026) gives one string per line, path
// ending in [i].
'use strict';
const fs = require('fs');
const vm = require('vm');
const file = process.argv[2];
const ctx = { window: {} };
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(file, 'utf8'), ctx);
const C = ctx.window.STUDY_CONFIG;
const out = [];
function add(path, kind, text, extra) { out.push(Object.assign({ path, kind, text: String(text) }, extra || {})); }

function lines(x) { return Array.isArray(x) ? x : [x]; }
function addText(path, kind, text, extra) {
  if (Array.isArray(text)) text.forEach((l, i) => add(path + '[' + i + ']', kind, l, extra));
  else add(path, kind, text, extra);
}

function question(q, path) {
  if (q.type === 'note') { addText(path + '.text', 'note', q.text); return; }
  if (q.text) addText(path + '.text', 'item', q.text, { qtype: q.type });
  if (q.type === 'decision') Object.keys(q.options).forEach(k => add(path + '.options.' + k, 'option', q.options[k]));
  else if (q.options) q.options.forEach((o, i) => add(path + '.options[' + i + ']', 'option', o.label, { value: o.value }));
  if (q.options && q.type !== 'decision') add(path + '.option_list', 'option_list', q.options.map(o => o.label).join(' / '), { labels: q.options.map(o => o.label) });
  if (q.points) q.points.forEach((p, i) => { if (p.label) add(path + '.points[' + i + ']', 'scale_label', p.label, { value: p.value }); });
  if (q.anchors) q.anchors.forEach((a, i) => add(path + '.anchors[' + i + ']', 'anchor', a, { end: i ? 'high' : 'low', points: q.points.length }));
  if (q.type === 'slider') { add(path + '.left', 'slider_anchor', q.left, { end: 'low' }); add(path + '.right', 'slider_anchor', q.right, { end: 'high' }); }
  if (Array.isArray(q.rows)) q.rows.forEach((r, i) => add(path + '.rows[' + i + ']', 'grid_row', r.label));
  if (q.columns) q.columns.forEach((c, i) => add(path + '.columns[' + i + ']', 'grid_column', c.label));
  if (q.followUp) question(q.followUp, path + '.followUp');
}

C.scenes.forEach(s => { if (s.plan !== undefined) add('scenes.' + s.id + '.plan', 'plan', s.plan, { scene: s.id }); });
// B1: each cell's plan heading (before 1 November 2026) or prompt-page lead, and its statement (one string; since
// 1 November 2026 its lines joined by a space, the lines kept in "lines")
(C.cells || []).forEach(c => {
  if (c.heading !== undefined) add('cells.' + c.id + '.heading', 'plan_heading', c.heading);
  if (c.lead !== undefined) add('cells.' + c.id + '.lead', 'plan_heading', c.lead);
  if (c.promptHeading !== undefined) add('cells.' + c.id + '.promptHeading', 'plan_heading', c.promptHeading);
  const st = lines(c.statement);
  add('cells.' + c.id + '.statement', 'statement', st.join(' '), { cell: c.id, lines: st });
});
// A1: each scene's added elements, and the statement shown for each amount
C.scenes.forEach(s => ['small', 'medium', 'large'].forEach(a => { if (s[a] !== undefined) add('scenes.' + s.id + '.' + a, 'phrase', s[a], { scene: s.id, amount: a }); }));
// A statement is one string (its lines joined by a space) with its lines kept in "lines".
if (C.statementFor) C.scenes.forEach(s => ['none', 'small', 'medium', 'large'].forEach(a => {
  const st = lines(C.statementFor(s.id, a));
  add('statement.' + s.id + '.' + a, 'a1_statement', st.join(' '), { scene: s.id, amount: a, lines: st });
}));
if (C.reminders) Object.keys(C.reminders).forEach(k => add('reminders.' + k, 'reminder', C.reminders[k]));
if (C.titles) Object.keys(C.titles).forEach(k => add('titles.' + k, 'title', C.titles[k]));
if (C.titlesOneImage) Object.keys(C.titlesOneImage).forEach(k => add('titlesOneImage.' + k, 'title', C.titlesOneImage[k]));   // A1 no-change trials (2 November 2026)
(C.captions || []).forEach((c, i) => add('captions[' + i + ']', 'caption', c));
(C.blocks || []).forEach(b => (b.before || []).forEach(pg => {
  if (pg.paragraphs) pg.paragraphs.forEach((p, i) => add('blocks.' + b.id + '.' + pg.id + '[' + i + ']', 'block_text', p));
  else if (pg.revisit) (pg.pages || [pg]).forEach(sp => sp.questions.forEach((q, i) => question(q, 'blocks.' + b.id + '.' + sp.id + '[' + i + ']:' + q.id)));
  else pg.items.forEach((q, i) => question(q, 'blocks.' + b.id + '.' + pg.id + '[' + i + ']:' + q.id));
}));
C.primer.paragraphs.forEach((p, i) => add('primer[' + i + ']', 'primer', p));
C.comprehension.items.forEach((it, i) => add('comprehension.items[' + i + ']', 'comprehension', it.text, { key: it.key }));
C.comprehension.options.forEach((o, i) => add('comprehension.options[' + i + ']', 'tf_option', o.label));
add('comprehension.retryNotice', 'ui_new', C.comprehension.retryNotice);
C.story.paragraphs.forEach((p, i) => add('story[' + i + ']', 'story', p));
// Each trial's story page (A1 since 1.4.0, by story; B1 since 1 November 2026, by cell), once per distinct
// line; a line holding the scene's plan (B1's prompt) is checked as a plan above, not here.
if (C.trialStory) {
  const seenStory = new Set();
  C.buildRow(0).trials.forEach(t => {
    const key = t.story || t.cell;
    const plan = (C.scenes.find(s => s.id === t.scene) || {}).plan;
    (C.trialStory(t).paragraphs || []).forEach((p, i) => {
      if (plan && p.indexOf(plan) >= 0) return;
      const tag = key + '|' + i + '|' + p;
      if (seenStory.has(tag)) return;
      seenStory.add(tag);
      add('trialStory.' + key + '[' + i + ']', 'story', p);
    });
  });
}
C.trialQuestions.forEach((q, i) => question(q, 'trialQuestions[' + i + ']:' + q.id));
(C.afterTrialScreens || []).forEach(sc => sc.questions.forEach((q, i) => question(q, 'afterTrialScreens.' + sc.id + '[' + i + ']:' + q.id)));
if (C.reasonQuestion) question(C.reasonQuestion, 'reasonQuestion');
if (C.reasonQuote) Object.keys(C.reasonQuote).forEach(k => add('reasonQuote.' + k, 'reason_quote', C.reasonQuote[k]));
add('instructed.text', 'instructed', C.instructed.text);
C.instructed.options.forEach((o, i) => add('instructed.options[' + i + ']', 'instructed_option', o.label));
if (C.would && C.would.intro) C.would.intro.paragraphs.forEach((p, i) => add('would.intro[' + i + ']', 'intro', p));
if (C.would) C.would.questions.forEach((q, i) => question(q, 'would.questions[' + i + ']:' + q.id));
if (C.recall.content) ((C.recall.content(C.buildRow(0).trials[0]) || {}).lines || []).forEach((l, i) => add('recall.lines[' + i + ']', 'intro', l));
question({ text: C.recall.text, options: C.recall.options, type: 'choice' }, 'recall');
C.endPages.forEach(pg => { if (pg.intro) add('endPages.' + pg.id + '.intro', 'intro', pg.intro); pg.items.forEach((q, i) => question(q, 'endPages.' + pg.id + '[' + i + ']:' + q.id)); });
C.demographicsPages.forEach(pg => pg.items.forEach((q, i) => question(q, 'demographics.' + pg.id + '[' + i + ']:' + q.id)));
C.finalPages.forEach(pg => pg.items.forEach((q, i) => question(q, 'final.' + pg.id + '[' + i + ']:' + q.id)));
add('consent.heading', 'ui', C.consent.heading);
add('consent.intro', 'consent_intro', C.consent.intro);
C.consent.sections.forEach((s, i) => { add('consent.sections[' + i + '].title', 'consent', s.title); s.paragraphs.forEach((p, j) => add('consent.sections[' + i + '].p[' + j + ']', 'consent', p)); });
add('consent.agree', 'consent', C.consent.agree);
add('consent.decline', 'consent', C.consent.decline);
add('debrief.heading', 'ui', C.debrief.heading);
C.debrief.paragraphs.forEach((p, i) => add('debrief[' + i + ']', 'debrief', p));
Object.keys(C.ui).forEach(k => add('ui.' + k, 'ui', C.ui[k]));
add('pageTitle', 'ui', C.pageTitle);
process.stdout.write(JSON.stringify({ studyCode: C.studyCode, strings: out }, null, 1) + '\n');
