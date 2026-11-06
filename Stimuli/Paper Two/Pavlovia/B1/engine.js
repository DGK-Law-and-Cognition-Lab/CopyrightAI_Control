// ============================================================
// Papers A and B: shared Pavlovia engine (plain JavaScript, no build step)
// ============================================================
//
// One engine, one configuration file per study. The study's config.js sets
// window.STUDY_CONFIG before this file loads; this file never holds study text.
//
// Flow (every study):
//   device check > welcome and full screen > consent > captcha trap >
//   primer > comprehension items (one retry; two failures end the session) >
//   story > trials in random order (instructed-response item after trial N,
//   written reason after designated trials) > "would" block > story recall >
//   end items > demographics > final questions > debriefing >
//   save data > SONA credit redirect (or completion page)
//
// Optional configuration added in 1.1.0 for A1 (each is unused by B1, whose
// pages and data columns are unchanged):
//   blocks           trials ordered at random within each block, with pages
//                    (text and items) shown before a block;
//   preScreen        a screen showing one image alone, with lines of text and
//                    a minimum viewing time, before each trial's question screen;
//   trialQuestionsFor(trial, derived)  the questions of one trial, in order;
//   afterTrialScreens  screens of further items shown after a trial's
//                    question screen (and before its written reason) on the
//                    trials they name, with the same images and text;
//   trialContent(t).lines  lines of text shown above the trial's statement;
//   pairLayout 'top' two images side by side across the top of the screen,
//                    kept in view while the questions scroll beneath them;
//   'note' items     text shown among the questions, with no answer;
//   would.preScreen, and a follow-up on the "would" item;
//   recall.content(trial)  what the story-recall screen shows.
//
// Optional configuration added in 1.2.0 for A1's page revision of
// 1 November 2026 (again each unused by B1, whose pages and data columns are
// unchanged):
//   text given as an array of lines (question text, notes, statements), each
//   shown as its own line; the engine never splits sentences itself;
//   trialContent(t).title  a centered title above the image pair (may hold
//                    <strong>); trialContent(t).vars  values put into {name}
//                    placeholders of that trial's question text;
//   pairTextBelow    the statement shown below the image pair, not above it;
//   viewPage         each trial is first shown without questions, with the
//                    minimum viewing time, then again with its questions and
//                    no minimum (view_page_ms, question_page_ms);
//   note.className   a style for a 'note' item ('plain', 'boxed');
//   reasonQuote      the participant's decision (and follow-up) quoted above
//                    the written-reason box (saved as <reason id>_quote);
//   revisit pages    in a block's 'before' list, earlier trials shown again,
//                    in the order first seen, with further items saved on
//                    each trial's own row;
//   would.intro      a text page before the "would" block.
//
// Optional configuration added in 1.3.0 for A1's follow-up section of
// 1 November 2026 (again each unused by B1, whose pages and data columns are
// unchanged):
//   revisit pages    a revisit spec may list several pages (spec.pages), all
//                    shown for one trial before the next trial's, each with
//                    its own items and time on screen (<page id>_page_ms);
//   quoteBefore      on such a page, the participant's decision on that trial
//                    (reasonQuote) quoted above the named item, saved as
//                    <item id>_quote;
//   dropGroup        an item whose dropGroup is listed in dropItems is
//                    removed like an item listed by its own id;
//   reasonQuestion and would  optional: without them there is no written
//                    reason inside a trial and no "would" block (A1 asks both
//                    in its follow-up section).
//
// Optional configuration added in 1.4.0 for A1's walk-through of each trial
// (1 November 2026; again each unused by B1, whose pages and data columns are
// unchanged):
//   trialStory(t)    a text page before each trial, {paragraphs, minSeconds}
//                    (A1: how Alex made the first image), saved as
//                    story_page_ms; with preScreen it is followed by the first
//                    image alone, and with viewPage by the change page;
//   questionLayout 'side'  on pages with questions, the image pair stacked in
//                    a column that stays in view, the title above it, and the
//                    statement and questions in a column beside it (stacked on
//                    narrow windows);
//   wide on an item page  the page uses the wide layout (A1: the agreement
//                    grids of the end scales).
//
// Optional configuration added in 1.5.0 for B1's walk-through of each trial
// (1 November 2026; each unused by A1, whose pages and data are unchanged):
//   pairLayout 'top' and questionLayout 'side' with one image (B1) as well as
//                    a pair (A1);
//   derived.would_positions  the trials the "would" block shows again (default
//                    the written-reason trials, as before);
//   recall.lastTrial  story recall asks about the last trial shown, whatever it
//                    is (recall.fromTrial(t) gives the fields to record);
//   recall.afterTrials  story recall comes right after the last trial, before
//                    the "would" block; recall.content(t).maxHeight caps the
//                    height of its image.
//
// Optional configuration added in 1.6.0 for B1 (1 November 2026; unused by A1):
//   sideTextUnderImage  on pages with questions in the side layout, the
//                    heading and plan (B1: the prompt) and then the statement
//                    (B1: what was done) sit under the image in the column
//                    that stays in view, and the questions alone beside it;
//   viewPageShowsPlan: false  the viewPage (B1: what was done, with the image)
//                    leaves out the heading and plan.
//
// Changed in 1.7.0 (2 November 2026, for A1's no-change trials; B1 unchanged):
//   trialQuestions may hold two wordings of one item under the same id (A1:
//                    "the second image" and, on no-change trials, "this
//                    image"); trialQuestionsFor picks one per trial, and the
//                    id gets one set of data columns, from its first wording;
//   reasonQuote quotes the decision as the trial worded it.
//
// Every session that ends early after consent (two comprehension failures,
// the captcha trap) goes through the same save and the same credit link.
//
// Kept from the genre-study template (Scene A Faire Computational, Study 1):
// Pavlovia init and save through the REST API, local CSV download fallback,
// desktop-only gate, full-screen button, hidden-instruction captcha trap,
// paste prevention, page system with minimum-wait timers, SONA credit routing.
//
// URL parameters: see the README of each study folder.
// ============================================================

var ENGINE_VERSION = 'pb-engine 1.7.0 (2026-11-02)';

(function () {
'use strict';

var C = window.STUDY_CONFIG;
if (!C) { document.body.innerHTML = '<p>Missing study configuration (config.js).</p>'; return; }
var UI = C.ui;

var UP = new URLSearchParams(window.location.search);
var TEST = UP.get('test') === '1';
var AUTO = TEST ? (UP.get('auto') || 'run') : 'off';     // run | fill | off
var TEST_FAIL = TEST ? (UP.get('test_fail') || '').toLowerCase() : '';
var AUTO_DELAY = TEST ? (parseInt(UP.get('auto_delay'), 10) || 5) : 0;
var TEST_MIN_MS = 20;                                      // minimum times shrink to this in test mode

// ============================================================
// PAVLOVIA INTEGRATION (from the template; multi-row CSV)
// ============================================================

function isLocalHost() {
  if (window.location.protocol === 'file:') return true;
  return /^(localhost|127\.0\.0\.1|\[::1\])$/.test(window.location.hostname);
}

var PAVLOVIA = {
  isActive: false,
  experimentId: null,
  projectId: null,
  sessionToken: null,
  apiBase: 'https://pavlovia.org/api/v2',
  _lastCSV: null,
  _lastKey: null,

  init: async function () {
    try {
      if (isLocalHost()) throw new Error('Local run: Pavlovia is not contacted');
      var pilotToken = UP.get('__pilotToken');
      var resp = await fetch('./config.json');
      if (!resp.ok) throw new Error('No config.json (status ' + resp.status + ')');
      var config = await resp.json();
      this.experimentId = config.experiment.fullpath || config.experiment.name;
      this.projectId = (config.gitlab && config.gitlab.projectId);
      if (!this.projectId) throw new Error('No gitlab.projectId in config.json');
      var formData = new FormData();
      if (pilotToken) formData.append('pilotToken', pilotToken);
      var sessionResp = await fetch(this.apiBase + '/experiments/' + this.projectId + '/sessions', {
        method: 'POST', mode: 'cors', cache: 'no-cache', credentials: 'same-origin',
        redirect: 'follow', referrerPolicy: 'no-referrer', body: formData
      });
      if (!sessionResp.ok) {
        var errBody = await sessionResp.text().catch(function () { return ''; });
        throw new Error('Session open failed (' + sessionResp.status + '): ' + errBody);
      }
      var sessionData = await sessionResp.json();
      this.sessionToken = sessionData.token;
      if (!this.sessionToken) throw new Error('No token in response: ' + JSON.stringify(sessionData));
      this.isActive = true;
      var self = this;
      window.addEventListener('unload', function () {
        if (self.isActive && self._lastCSV) {
          var fd = new FormData();
          fd.append('key', self._lastKey);
          fd.append('value', self._lastCSV);
          navigator.sendBeacon(self.apiBase + '/experiments/' + self.projectId + '/sessions/' + self.sessionToken + '/results', fd);
          var cfd = new FormData();
          cfd.append('isCompleted', 'false');
          navigator.sendBeacon(self.apiBase + '/experiments/' + self.projectId + '/sessions/' + self.sessionToken + '/delete', cfd);
        }
      });
    } catch (e) {
      console.warn('[Pavlovia] Init failed:', e.message);
      this.isActive = false;
    }
  },

  csvKey: function () {
    var d = new Date();
    var ds = d.getFullYear() + '-' + ('0' + (1 + d.getMonth())).slice(-2) + '-' + ('0' + d.getDate()).slice(-2) + '_';
    ds += ('0' + d.getHours()).slice(-2) + 'h' + ('0' + d.getMinutes()).slice(-2) + '.' + ('0' + d.getSeconds()).slice(-2) + '.' + d.getMilliseconds();
    return 'data/' + C.studyCode + '_' + safeId(ST.pid || 'anon') + '_SESSION_' + ds + '.csv';
  },

  save: async function (csv) {
    var csvKey = this.csvKey();
    if (this.isActive) {
      try {
        this._lastCSV = csv;
        this._lastKey = csvKey;
        var uploadUrl = this.apiBase + '/experiments/' + this.projectId + '/sessions/' + this.sessionToken + '/results';
        var fd = new FormData();
        fd.append('key', csvKey);
        fd.append('value', csv);
        var uploadResp = await fetch(uploadUrl, {
          method: 'POST', mode: 'cors', cache: 'no-cache', credentials: 'same-origin',
          redirect: 'follow', referrerPolicy: 'no-referrer', body: fd
        });
        var uploadJson = await uploadResp.json().catch(function () { return { status: uploadResp.status }; });
        if (uploadResp.status !== 200) throw new Error('Upload HTTP ' + uploadResp.status + ': ' + JSON.stringify(uploadJson));
        var closeUrl = this.apiBase + '/experiments/' + this.projectId + '/sessions/' + this.sessionToken;
        var closeFd = new FormData();
        closeFd.append('isCompleted', 'true');
        await fetch(closeUrl, {
          method: 'DELETE', mode: 'cors', cache: 'no-cache', credentials: 'same-origin',
          redirect: 'follow', referrerPolicy: 'no-referrer', body: closeFd
        });
        this._lastCSV = null;
        this.isActive = false;
        return true;
      } catch (e) {
        console.error('[Pavlovia] Fetch failed:', e.message, '. Using sendBeacon...');
        var bfd = new FormData();
        bfd.append('key', csvKey);
        bfd.append('value', csv);
        var sent = navigator.sendBeacon(this.apiBase + '/experiments/' + this.projectId + '/sessions/' + this.sessionToken + '/results', bfd);
        var cfd = new FormData();
        cfd.append('isCompleted', 'true');
        navigator.sendBeacon(this.apiBase + '/experiments/' + this.projectId + '/sessions/' + this.sessionToken + '/delete', cfd);
        this._lastCSV = null;
        this.isActive = false;
        if (sent) return true;
        this.downloadCSV(csv);
        return false;
      }
    } else {
      this.downloadCSV(csv);
      return true;
    }
  },

  downloadCSV: function (csv) {
    try {
      var blob = new Blob([csv], { type: 'text/csv' });
      var url = URL.createObjectURL(blob);
      var a = document.createElement('a');
      a.href = url;
      a.download = C.studyCode + '_' + safeId(ST.pid || 'test') + '_' + Date.now() + '.csv';
      a.style.display = 'none';
      document.body.appendChild(a);
      a.click();
      setTimeout(function () { URL.revokeObjectURL(url); a.remove(); }, 1000);
    } catch (e) { console.warn('[Local] CSV download failed', e); }
  }
};

// ============================================================
// STATE AND HELPERS
// ============================================================

var ST = {
  pid: '', code: null, platform: 'other',
  cp: 0, r: {}, t0: Date.now(), pts: [], lastRenderAt: 0,
  row: null, derived: null, trials: [], trialByPos: {}, order: [],
  resp: {},            // responses on the current page: id -> {value, rt_ms, rt_last_ms, n_changes}
  exitReason: null, finished: false, csv: null
};

function rec(k, v) { ST.r[k] = v; }
function get(k) { return ST.r[k]; }
function safeId(s) { return String(s).replace(/[^A-Za-z0-9_.-]/g, '_').slice(0, 64); }
function esc(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
function rnd(n) { return Math.floor(Math.random() * n); }
function shuffle(arr) {
  var a = arr.slice();
  for (var i = a.length - 1; i > 0; i--) { var j = rnd(i + 1); var t = a[i]; a[i] = a[j]; a[j] = t; }
  return a;
}
function now() { return Date.now(); }
function sinceStart() { return now() - ST.t0; }
function fill(tpl, vars) { return String(tpl).replace(/\{(\w+)\}/g, function (m, k) { return vars[k] !== undefined ? vars[k] : m; }); }
function secsFor(s) { return TEST ? 0 : (s || 0); }
// Text given as one string or as an array of lines (1.2.0).
function linesOf(x) { return (x === undefined || x === null || x === '') ? [] : (Array.isArray(x) ? x : [x]); }
function plain(s) { return String(s).replace(/<[^>]+>/g, ''); }

// Automated-browser detection (template)
(function () {
  var u = navigator.userAgent.toLowerCase();
  if (u.indexOf('atlas') >= 0 || u.indexOf('chatgpt') >= 0 || u.indexOf('oai-searchbot') >= 0) ST.r.atlas_detected = true;
})();

// Paste and drop prevention (template, plus drop)
document.addEventListener('paste', function (e) {
  if (e.target && e.target.dataset && e.target.dataset.allowPaste === 'true') return;
  e.preventDefault();
  var q = e.target && e.target.dataset && e.target.dataset.qid;
  if (q && ST.resp[q]) ST.resp[q].paste_attempts = (ST.resp[q].paste_attempts || 0) + 1;
});
document.addEventListener('drop', function (e) {
  if (e.target && e.target.tagName === 'TEXTAREA') e.preventDefault();
});

// ============================================================
// PAGE SYSTEM (template pattern: html / onShow / val / timer / cond / fin)
// ============================================================

var P = [];
function gR(n) { var e = document.querySelector('input[name="' + n + '"]:checked'); return e ? e.value : null; }
function sE(id) { var e = document.getElementById(id); if (e) e.style.display = 'block'; }
function hE() { document.querySelectorAll('.error-msg').forEach(function (e) { e.style.display = 'none'; }); }

function render(idx) {
  ST.cp = idx;
  var pg = P[idx];
  if (!pg) return;
  if (pg.cond && !pg.cond()) { if (idx < P.length - 1) render(idx + 1); return; }
  ST.lastRenderAt = now();
  ST.pts.push({ p: idx, id: pg.id || '', t: ST.lastRenderAt - ST.t0 });
  ST.resp = {};
  var c = document.getElementById('pageContainer');
  var cont = document.getElementById('experimentContainer');
  if (cont) cont.classList.toggle('wide', !!pg.wide);
  var bt = pg.fin ? UI.completeButton : UI.nextButton;
  var html = typeof pg.html === 'function' ? pg.html() : pg.html;
  c.innerHTML = '<div class="page active">' + html + '<div class="btn-row"><button class="btn" id="nextBtn" type="button">' + bt + '</button></div></div>';
  document.getElementById('nextBtn').addEventListener('click', nxt);
  document.getElementById('progressFill').style.width = Math.round(idx / Math.max(1, P.length - 1) * 100) + '%';
  wireWidgets(c);

  var nb = document.getElementById('nextBtn');
  var secs = secsFor(pg.timer || 0);
  if (pg.waitImages) {
    startImageTimer(pg, nb);
  } else if (pg.timer && (secs > 0 || TEST)) {
    countdown(nb, TEST ? TEST_MIN_MS / 1000 : secs, pg.fin);
  }
  if (pg.onShow) pg.onShow();
  window.scrollTo(0, 0);
  if (TEST && AUTO !== 'off') autopilot(pg);
}

function countdown(nb, secs, fin) {
  if (!nb) return;
  nb.disabled = true;
  var endAt = now() + secs * 1000;
  var label = function () {
    var left = Math.max(0, Math.ceil((endAt - now()) / 1000));
    nb.textContent = fill(UI.waitButton, { s: left });
  };
  label();
  var t = setInterval(function () {
    if (now() >= endAt) {
      clearInterval(t);
      nb.disabled = false;
      nb.textContent = fin ? UI.completeButton : UI.nextButton;
    } else label();
  }, TEST ? 5 : 250);
}

// The minimum viewing time starts when every image on the page has loaded.
function startImageTimer(pg, nb) {
  var imgs = Array.prototype.slice.call(document.querySelectorAll('#pageContainer img.stim'));
  var shownAt = ST.lastRenderAt;
  var started = false;
  var minSecs = TEST ? TEST_MIN_MS / 1000 : (pg.minView || 0);
  nb.disabled = true;
  nb.textContent = fill(UI.waitButton, { s: Math.ceil(minSecs) });
  function go(err) {
    if (started) return;
    started = true;
    pg._imageLoadMs = now() - shownAt;
    pg._imageError = !!err;
    countdown(nb, minSecs, pg.fin);
  }
  var pending = imgs.length, anyErr = false;
  if (!pending) { go(false); return; }
  imgs.forEach(function (im) {
    var done = function (isErr) { if (isErr) anyErr = true; pending--; if (pending <= 0) go(anyErr); };
    if (im.complete && im.naturalWidth > 0) done(false);
    else { im.addEventListener('load', function () { done(false); }); im.addEventListener('error', function () { done(true); }); }
  });
}

function nxt() {
  hE();
  var pg = P[ST.cp];
  var nb = document.getElementById('nextBtn');
  if (nb && nb.disabled) return;
  if (pg.val && !pg.val()) return;
  if (ST.exitReason) return;            // the page started an early exit
  if (pg.fin) {
    if (nb) { nb.disabled = true; nb.textContent = UI.savingButton; }
    finishStudy();
    return;
  }
  if (ST.cp < P.length - 1) render(ST.cp + 1);
}

// ============================================================
// QUESTION WIDGETS
// Each question renders inside <div class="q" data-qid="...">. Answers go to
// ST.resp[id] = {value, rt_ms, rt_last_ms, n_changes}; times are ms from the
// moment the page was shown.
// ============================================================

function touch(id, value) {
  var r = ST.resp[id] || (ST.resp[id] = { value: null, rt_ms: null, rt_last_ms: null, n_changes: 0 });
  var t = now() - ST.lastRenderAt;
  if (r.rt_ms === null) r.rt_ms = t;
  r.rt_last_ms = t;
  r.n_changes += 1;
  r.value = value;
  var box = document.querySelector('.q[data-qid="' + cssEsc(id) + '"]');
  if (box) box.classList.remove('unanswered');
}
function cssEsc(s) { return String(s).replace(/"/g, '\\"'); }

// Question text: one string (one paragraph, as in B1) or an array of lines,
// each its own paragraph (A1, 1.2.0).
function qHead(q) {
  if (Array.isArray(q.text)) return '<div class="question-text">' + q.text.map(function (l) { return '<p>' + l + '</p>'; }).join('') + '</div>';
  return q.text ? '<p class="question-text">' + q.text + '</p>' : '';
}

// A question with {name} placeholders in its text filled from a trial's
// trialContent(t).vars (A1: the added elements). Without vars, the question itself.
function withVars(q, vars) {
  if (!vars || !q.text) return q;
  var c = {};
  Object.keys(q).forEach(function (k) { c[k] = q[k]; });
  c.text = Array.isArray(q.text) ? q.text.map(function (l) { return fill(l, vars); }) : fill(q.text, vars);
  return c;
}

function choiceHTML(q, opts) {
  var h = '<div class="q q-choice" data-qid="' + q.id + '">' + qHead(q) + '<div class="radio-group">';
  opts.forEach(function (o, i) {
    h += '<label class="radio-option"><input type="radio" name="' + q.id + '" value="' + esc(o.value) + '" data-qid="' + q.id + '" data-pos="' + (i + 1) + '"> ' + o.label + '</label>';
  });
  h += '</div>';
  if (q.followUp) {
    var f = q.followUp;
    h += '<div class="followup" id="fu_' + q.id + '" data-show-if="' + esc(f.showIf) + '" style="display:none">' + choiceHTML({ id: f.id, text: f.text }, f.options) + '</div>';
  }
  h += '</div>';
  return h;
}

function scaleHTML(q) {
  // Horizontal 1-to-k scale. Each point shows its number and, if given, its label.
  var h = '<div class="q q-scale" data-qid="' + q.id + '">' + qHead(q) + '<div class="scale-group' + (q.points.length > 5 ? ' scale7' : '') + '">';
  q.points.forEach(function (p) {
    h += '<label class="scale-option"><input type="radio" name="' + q.id + '" value="' + esc(p.value) + '" data-qid="' + q.id + '">'
      + '<span class="scale-num">' + p.value + '</span>' + (p.label ? '<span class="scale-lab">' + p.label + '</span>' : '') + '</label>';
  });
  h += '</div>';
  if (q.anchors) h += '<div class="scale-anchors"><span>' + q.anchors[0] + '</span><span>' + q.anchors[1] + '</span></div>';
  h += '</div>';
  return h;
}

function sliderHTML(q) {
  return '<div class="q q-slider" data-qid="' + q.id + '">' + qHead(q)
    + '<div class="slider" data-qid="' + q.id + '" data-min="' + (q.min || 0) + '" data-max="' + (q.max === undefined ? 100 : q.max) + '" tabindex="0" role="slider" aria-valuemin="' + (q.min || 0) + '" aria-valuemax="' + (q.max === undefined ? 100 : q.max) + '">'
    + '<div class="slider-track"></div><div class="slider-thumb" style="display:none"><span class="slider-val"></span></div></div>'
    + '<div class="slider-anchors"><span><b>' + (q.min || 0) + '</b><br>' + q.left + '</span><span><b>' + (q.max === undefined ? 100 : q.max) + '</b><br>' + q.right + '</span></div>'
    + '</div>';
}

function gridHTML(q) {
  var h = '<div class="q q-grid" data-qid="' + q.id + '">' + qHead(q) + '<table class="grid"><thead><tr><th></th>';
  q.columns.forEach(function (c) { h += '<th>' + c.label + '</th>'; });
  h += '</tr></thead><tbody>';
  q.rows.forEach(function (r) {
    var rid = q.id + '_' + r.id;
    h += '<tr class="q grid-row" data-qid="' + rid + '"><td class="grid-label">' + r.label + '</td>';
    q.columns.forEach(function (c) {
      h += '<td class="grid-cell"><label><input type="radio" name="' + rid + '" value="' + esc(c.value) + '" data-qid="' + rid + '"></label></td>';
    });
    h += '</tr>';
  });
  h += '</tbody></table></div>';
  return h;
}

function textHTML(q) {
  return '<div class="q q-text" data-qid="' + q.id + '">' + qHead(q)
    + '<textarea rows="' + (q.rows || 4) + '" data-qid="' + q.id + '" autocomplete="off" spellcheck="true"></textarea></div>';
}
function shortTextHTML(q) {
  return '<div class="q q-short" data-qid="' + q.id + '">' + qHead(q)
    + '<input type="text" data-qid="' + q.id + '" autocomplete="off"' + (q.placeholder ? ' placeholder="' + esc(q.placeholder) + '"' : '') + '></div>';
}
function numberHTML(q) {
  return '<div class="q q-number" data-qid="' + q.id + '">' + qHead(q)
    + '<input type="number" data-qid="' + q.id + '" min="' + (q.min || 0) + '" max="' + (q.max || 120) + '" style="max-width:200px"' + (q.placeholder ? ' placeholder="' + esc(q.placeholder) + '"' : '') + '></div>';
}
function checkboxHTML(q) {
  var h = '<div class="q q-check" data-qid="' + q.id + '">' + qHead(q) + '<div>';
  q.options.forEach(function (o) {
    h += '<label class="radio-option"><input type="checkbox" name="' + q.id + '" value="' + esc(o.value) + '" data-qid="' + q.id + '"> ' + o.label + '</label>';
  });
  return h + '</div></div>';
}

// Ordered options of a question (decision options follow the participant's
// option order; options marked shuffle are randomized once per participant).
function optionsOf(q) {
  if (q.type === 'decision') {
    return ST.derived.option_order.map(function (key) { return { value: key, label: q.options[key] }; });
  }
  if (q._order) return q._order;
  if (q.shuffle) {
    var nFixed = q.fixedLast || 0;
    var head = q.options.slice(0, q.options.length - nFixed), tail = q.options.slice(q.options.length - nFixed);
    q._order = shuffle(head).concat(tail);
    if (q.orderColumn) rec(q.orderColumn, q._order.map(function (o) { return o.value; }).join(';'));
    return q._order;
  }
  return q.options;
}

function questionHTML(q) {
  switch (q.type) {
    case 'note': return '<div class="q-note' + (q.className ? ' ' + q.className : '') + '">'
      + (Array.isArray(q.text) ? q.text.map(function (l) { return '<p>' + l + '</p>'; }).join('') : q.text) + '</div>';
    case 'choice': return choiceHTML(q, optionsOf(q));
    case 'decision': return choiceHTML(q, optionsOf(q));
    case 'scale': return scaleHTML(q);
    case 'slider': return sliderHTML(q);
    case 'grid': return gridHTML(q);
    case 'text': return textHTML(q);
    case 'shorttext': return shortTextHTML(q);
    case 'number': return numberHTML(q);
    case 'checkbox': return checkboxHTML(q);
  }
  throw new Error('Unknown question type ' + q.type);
}

function wireWidgets(root) {
  // Radio buttons: selection styling and answer capture
  root.querySelectorAll('input[type="radio"]').forEach(function (inp) {
    inp.addEventListener('change', function () {
      var lab = inp.closest('label');
      var group = inp.closest('.radio-group, .scale-group, tr');
      if (group) group.querySelectorAll('label').forEach(function (l) { l.classList.remove('selected'); });
      if (lab) lab.classList.add('selected');
      touch(inp.dataset.qid, inp.value);
      if (ST.resp[inp.dataset.qid]) ST.resp[inp.dataset.qid].pos = inp.dataset.pos ? parseInt(inp.dataset.pos, 10) : null;
      var fu = document.getElementById('fu_' + inp.dataset.qid);
      if (fu) {
        var show = fu.dataset.showIf ? fu.dataset.showIf === inp.value : false;
        fu.style.display = show ? 'block' : 'none';
        if (!show) {     // a hidden follow-up keeps no answer
          fu.querySelectorAll('input').forEach(function (x) { x.checked = false; });
          fu.querySelectorAll('label').forEach(function (l) { l.classList.remove('selected'); });
          var fq = fu.querySelector('.q');
          if (fq) delete ST.resp[fq.dataset.qid];
        }
      }
    });
  });
  root.querySelectorAll('input[type="checkbox"]').forEach(function (inp) {
    inp.addEventListener('change', function () {
      var lab = inp.closest('label');
      if (lab) lab.classList.toggle('selected', inp.checked);
      var vals = Array.prototype.slice.call(root.querySelectorAll('input[type="checkbox"][data-qid="' + inp.dataset.qid + '"]:checked')).map(function (x) { return x.value; });
      touch(inp.dataset.qid, vals.join(';'));
    });
  });
  root.querySelectorAll('textarea[data-qid], input[type="text"][data-qid], input[type="number"][data-qid]').forEach(function (el) {
    var id = el.dataset.qid;
    ST.resp[id] = ST.resp[id] || { value: null, rt_ms: null, rt_last_ms: null, n_changes: 0, paste_attempts: 0 };
    el.addEventListener('input', function () { touch(id, el.value); });
  });
  root.querySelectorAll('.slider').forEach(wireSlider);
}

// 0-to-100 slider with no handle until the participant clicks on it, so there
// is no starting value to anchor on. Click or drag sets the value; after the
// first click the arrow keys move it by 1.
function wireSlider(sl) {
  var id = sl.dataset.qid, min = +sl.dataset.min, max = +sl.dataset.max;
  var thumb = sl.querySelector('.slider-thumb'), lab = sl.querySelector('.slider-val');
  var dragging = false, touched = false;
  function set(v) {
    v = Math.max(min, Math.min(max, Math.round(v)));
    touched = true;
    thumb.style.display = 'block';
    thumb.style.left = ((v - min) / (max - min) * 100) + '%';
    lab.textContent = v;
    sl.setAttribute('aria-valuenow', v);
    sl.classList.add('touched');
    var r = ST.resp[id];
    if (!r || r.value !== v) touch(id, v);
  }
  function fromEvent(e) {
    var rect = sl.getBoundingClientRect();
    return min + (e.clientX - rect.left) / rect.width * (max - min);
  }
  sl._set = set;
  sl.addEventListener('pointerdown', function (e) {
    dragging = true;
    try { sl.setPointerCapture(e.pointerId); } catch (err) {}
    set(fromEvent(e));
    e.preventDefault();
  });
  sl.addEventListener('pointermove', function (e) { if (dragging) set(fromEvent(e)); });
  sl.addEventListener('pointerup', function () { dragging = false; });
  sl.addEventListener('pointercancel', function () { dragging = false; });
  sl.addEventListener('keydown', function (e) {
    if (!touched) return;
    var v = ST.resp[id] ? ST.resp[id].value : null;
    if (v === null) return;
    if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') { set(v - 1); e.preventDefault(); }
    if (e.key === 'ArrowRight' || e.key === 'ArrowUp') { set(v + 1); e.preventDefault(); }
  });
}

// Check that every listed question has an answer; mark the missing ones.
function requireAll(qs, errId) {
  var missing = null;
  qs.forEach(function (q) {
    ids(q).forEach(function (id) {
      var r = ST.resp[id];
      var ok = r && r.value !== null && r.value !== undefined && String(r.value).trim() !== '';
      if (ok && q.type === 'number') {
        var n = Number(r.value);
        ok = isFinite(n) && n >= (q.min || 0) && n <= (q.max || 120);
      }
      if (!ok) {
        var box = document.querySelector('.q[data-qid="' + cssEsc(id) + '"]');
        if (box) { box.classList.add('unanswered'); if (!missing) missing = box; }
        else if (!missing) missing = true;
      }
    });
  });
  if (missing) {
    sE(errId);
    if (missing !== true) try {
      var band = document.querySelector('#pageContainer .trial-band');
      if (band) {
        // pairLayout 'top': put the unanswered item just below the pinned image band, not under it.
        var top = window.scrollY + missing.getBoundingClientRect().top - band.getBoundingClientRect().height - 16;
        window.scrollTo({ top: Math.max(0, top), behavior: 'smooth' });
      } else {
        missing.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    } catch (e) {}
    return false;
  }
  return true;
}

// Answer ids that a question produces (grids give one per row; a follow-up
// adds its own id when it is shown).
function ids(q) {
  if (q.type === 'note') return [];          // text only, no answer
  if (q.type === 'grid') return q.rows.map(function (r) { return q.id + '_' + r.id; });
  var out = [q.id];
  if (q.followUp && ST.resp[q.id] && ST.resp[q.id].value === q.followUp.showIf) out.push(q.followUp.id);
  return out;
}
function allIds(q) {
  if (q.type === 'note') return [];
  if (q.type === 'grid') return q.rows.map(function (r) { return q.id + '_' + r.id; });
  return q.followUp ? [q.id, q.followUp.id] : [q.id];
}

// Copy the page's answers into a target object (a trial record or the
// participant record). Trial items keep rt_last_ms and n_changes as well.
function store(qs, target, full) {
  qs.forEach(function (q) {
    allIds(q).forEach(function (id) {
      var r = ST.resp[id];
      target[id] = r ? r.value : '';
      target[id + '_rt_ms'] = r ? r.rt_ms : '';
      if (full) {
        target[id + '_rt_last_ms'] = r ? r.rt_last_ms : '';
        target[id + '_n_changes'] = r ? r.n_changes : '';
      }
      if (q.type === 'decision' && id === q.id) target[id + '_display_pos'] = r ? r.pos : '';
      if (q.type === 'text') {
        target[id + '_chars'] = r && r.value ? String(r.value).length : 0;
        target[id + '_paste_attempts'] = r ? (r.paste_attempts || 0) : 0;
      }
      if (q.key !== undefined && id === q.id) target[id + '_correct'] = r ? (String(r.value) === String(q.key)) : '';
    });
  });
}

// ============================================================
// IDENTITY, PLATFORM AND ASSIGNMENT
// ============================================================

function parseIdentity() {
  var codeParam = UP.get('code');
  var pid = UP.get('participant') || UP.get('survey_code') || UP.get('id') || '';
  if (!pid && codeParam) pid = (TEST ? 'TEST_' : '') + codeParam;
  ST.pid = pid;
  var codeStr = (codeParam !== null && codeParam !== '') ? codeParam : pid;
  ST.code = /^[0-9]+$/.test(String(codeStr).trim()) ? parseInt(codeStr, 10) : null;

  var plat = (UP.get('platform') || '').toLowerCase().trim();
  var platSource;
  if (TEST) { ST.platform = 'test'; platSource = 'test_mode'; }
  else if (plat) { ST.platform = plat; platSource = 'url'; }
  else if (/^[1-9][0-9]*$/.test(ST.pid)) { ST.platform = 'sona'; platSource = 'numeric_id'; }
  else { ST.platform = 'other'; platSource = 'none'; }

  rec('study_code', C.studyCode);
  rec('engine_version', ENGINE_VERSION);
  rec('config_version', C.configVersion);
  rec('participant_id', ST.pid);
  rec('code', ST.code === null ? '' : ST.code);
  rec('is_test', TEST || /^(pilot|test)/i.test(ST.pid));
  rec('test_mode', TEST);
  rec('test_fail', TEST_FAIL);
  rec('platform', ST.platform);
  rec('platform_source', platSource);
  rec('start_time', new Date().toISOString());
}

async function loadOpenRows() {
  try {
    var resp = await fetch(C.openRowsFile || 'open_rows.json', { cache: 'no-store' });
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    var j = await resp.json();
    var rows = (j.open_rows || []).map(Number).filter(function (k) { return Number.isInteger(k) && k >= 0 && k < C.nRows; });
    rows = rows.filter(function (k, i) { return rows.indexOf(k) === i; }).sort(function (a, b) { return a - b; });
    rec('open_rows_source', 'file');
    rec('open_rows_updated', j.updated || '');
    return rows;
  } catch (e) {
    console.warn('[Assignment] open_rows.json could not be read (' + e.message + '); every row is treated as open.');
    rec('open_rows_source', 'fallback_all');
    rec('open_rows_updated', '');
    var all = []; for (var k = 0; k < C.nRows; k++) all.push(k);
    return all;
  }
}

// Row: the SONA code modulo the number of open rows picks one of the open
// rows, taken in order of k. ?row=K forces row K (testing only).
async function assignRow() {
  var forced = UP.get('row');
  var k, source, open = await loadOpenRows(), idx = '';
  if (open.length === 0) {
    rec('open_rows_source', get('open_rows_source') + '_none_open_used_all');
    for (var j = 0; j < C.nRows; j++) open.push(j);
  }
  if (forced !== null && /^[0-9]+$/.test(forced) && +forced < C.nRows) {
    k = +forced; source = 'url_row';
  } else if (ST.code !== null) {
    idx = ST.code % open.length; k = open[idx]; source = 'code_mod_open_rows';
  } else {
    idx = rnd(open.length); k = open[idx]; source = 'random_no_numeric_code';
  }
  rec('open_rows', open.join(';'));
  rec('n_open_rows', open.length);
  rec('open_rows_index', idx);
  rec('assignment_source', source);
  rec('n_rows', C.nRows);
  rec('dropped_items', (C.dropItems || []).join(';'));

  ST.row = C.buildRow(k);
  rec('row', ST.row.row);
  (C.rowColumns || []).forEach(function (col) { rec(col, ST.row[col]); });

  ST.derived = C.derive(ST.code, ST.row, rnd);
  (C.derivedColumns || []).forEach(function (col) {
    var v = ST.derived[col];
    rec(col, Array.isArray(v) ? v.join(';') : v);
  });

  // Trials: one record per trial of the row, presented in random order.
  ST.trials = ST.row.trials.map(function (t) {
    var tr = {};
    Object.keys(t).forEach(function (key) { tr[key] = t[key]; });
    tr.has_reason = (ST.derived.reason_positions || []).indexOf(t.list_position) >= 0;
    tr.is_recall_trial = t.list_position === ST.derived.recall_position;
    tr.has_would = (ST.derived.would_positions || ST.derived.reason_positions || []).indexOf(t.list_position) >= 0;
    tr.would_shown = false;
    return tr;
  });
  ST.trials.forEach(function (t) { ST.trialByPos[t.list_position] = t; });
  if (C.blocks) {
    // Blocks in the configured order; trial order random within each block.
    ST.order = [];
    C.blocks.forEach(function (b) {
      var inBlock = ST.trials.filter(function (t) { return t.block === b.id; }).map(function (t) { return t.list_position; });
      ST.order = ST.order.concat(shuffle(inBlock));
    });
    if (ST.order.length !== ST.trials.length) throw new Error('Every trial must belong to one of the configured blocks');
  } else {
    ST.order = shuffle(ST.trials.map(function (t) { return t.list_position; }));
  }
  ST.order.forEach(function (pos, i) { ST.trialByPos[pos].trial_position = i + 1; });
  rec('trial_order', ST.order.join(';'));
  if (C.recall && C.recall.lastTrial) {
    // 1.5.0 (B1): story recall asks about the last trial shown.
    var lastT = ST.trialByPos[ST.order[ST.order.length - 1]];
    ST.derived.recall_position = lastT.list_position;
    var fields = C.recall.fromTrial ? C.recall.fromTrial(lastT) : { recall_position: lastT.list_position };
    Object.keys(fields).forEach(function (k) { ST.derived[k] = fields[k]; rec(k, fields[k]); });
    ST.trials.forEach(function (t) { t.is_recall_trial = t === lastT; });
  }
  rec('n_trials', ST.order.length);
}

// ============================================================
// SHARED SCREENS (template): device check, welcome, consent, captcha
// ============================================================

function buildGate() {
  var isMobile = /Mobi|Android|iPhone|iPad|iPod|webOS|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
  rec('device_type', isMobile ? 'mobile' : 'desktop');
  rec('fullscreen_entered', 'no');

  P.push({
    id: 'device_check',
    html: '<div class="center-text pad40"><h1 class="plain">' + UI.deviceHeading + '</h1><p class="big">' + UI.deviceText1 + '</p><p class="big">' + UI.deviceText2 + '</p>'
      + '<div class="radio-group"><label class="radio-option"><input type="radio" name="devicecheck" value="1" data-qid="devicecheck"> ' + UI.deviceYes + '</label>'
      + '<label class="radio-option"><input type="radio" name="devicecheck" value="2" data-qid="devicecheck"> ' + UI.deviceNo + '</label></div>'
      + '<p class="error-msg" id="err-dev">' + UI.selectOption + '</p></div>',
    questions: [{ id: 'devicecheck', type: 'choice', options: [{ value: '1' }, { value: '2' }], _auto: '1' }],
    val: function () {
      var v = gR('devicecheck');
      if (!v) { sE('err-dev'); return false; }
      rec('device_self_report', v);
      if (v === '2') {
        document.getElementById('pageContainer').innerHTML = '<div class="page active center-text pad60"><h1 class="plain">' + UI.desktopRequiredHeading + '</h1><p class="big">' + UI.desktopRequired1 + '</p><p>' + UI.desktopRequired2 + '</p></div>';
        return false;
      }
      return true;
    }
  });

  P.push({
    id: 'welcome',
    html: '<div class="center-text pad40"><h1 class="plain">' + UI.welcomeHeading + '</h1><p class="big">' + UI.fullscreen1 + '</p><p class="big">' + UI.fullscreen2 + '</p>'
      + '<button id="fsBtn" class="fs-btn" type="button">' + UI.fullscreenButton + '</button><p class="muted small">' + UI.fullscreenNote + '</p></div>',
    onShow: function () {
      var b = document.getElementById('fsBtn');
      if (b) b.onclick = function () {
        var d = document.documentElement;
        try {
          if (d.requestFullscreen) d.requestFullscreen();
          else if (d.webkitRequestFullscreen) d.webkitRequestFullscreen();
        } catch (e) {}
        b.textContent = UI.fullscreenDone;
        b.classList.add('done');
        b.disabled = true;
        rec('fullscreen_entered', 'yes');
      };
    },
    val: function () { return true; }
  });

  // Consent: the IRB-approved text in config, with the template's page structure.
  P.push({
    id: 'consent',
    html: function () {
      var h = '<h1>' + C.consent.heading + '</h1>';
      if (C.consent.intro) h += '<p class="muted">' + C.consent.intro + '</p>';
      h += '<div class="consent-text">';
      C.consent.sections.forEach(function (s) {
        if (s.title) h += '<p class="consent-title">' + s.title + '</p>';
        s.paragraphs.forEach(function (p) { h += '<p>' + p + '</p>'; });
      });
      h += '</div>';
      if (C.consent.url) h += '<p><a href="' + esc(C.consent.url) + '" target="_blank" rel="noopener">' + UI.consentLink + '</a></p>';
      h += '<div class="radio-group"><label class="radio-option"><input type="radio" name="consent" value="agreed" data-qid="consent"> ' + C.consent.agree + '</label>'
        + '<label class="radio-option"><input type="radio" name="consent" value="declined" data-qid="consent"> ' + C.consent.decline + '</label></div>'
        + '<p class="error-msg" id="err-consent">' + UI.selectOption + '</p>';
      return h;
    },
    questions: [{ id: 'consent', type: 'choice', options: [{ value: 'agreed' }, { value: 'declined' }], _auto: TEST_FAIL === 'decline' ? 'declined' : 'agreed' }],
    val: function () {
      var v = gR('consent');
      if (!v) { sE('err-consent'); return false; }
      if (v === 'declined') { declined(); return false; }
      rec('consent', 'agreed');
      rec('consent_time', new Date().toISOString());
      return true;
    }
  });

  // Captcha trap (template): the image says press Q; a hidden line says press Z.
  // Placed after consent, so a failed trap is saved and credited like any
  // other early exit.
  P.push({
    id: 'captcha',
    html: '<div class="center-text pad40"><p class="big">' + UI.captchaPrompt + '</p><div class="captcha-box"><img src="captcha.png" alt=""></div>'
      + '<p class="trap" aria-hidden="true">' + UI.captchaTrap + '</p><p id="captcha-status" class="muted">' + UI.captchaWaiting + '</p></div>',
    onShow: function () {
      var nb = document.getElementById('nextBtn');
      if (nb) nb.style.display = 'none';
      var shown = now();
      var handler = function (e) {
        var k = (e.key || '').toLowerCase();
        if (k === 'q') {
          rec('captcha_response', 'q'); rec('captcha_pass', true); rec('captcha_rt_ms', now() - shown);
          var s = document.getElementById('captcha-status');
          s.textContent = UI.captchaCorrect; s.classList.add('ok');
          if (nb) nb.style.display = 'inline-block';
          document.removeEventListener('keydown', handler);
        } else if (k === 'z') {
          rec('captcha_response', 'z'); rec('captcha_pass', false); rec('captcha_rt_ms', now() - shown);
          document.removeEventListener('keydown', handler);
          earlyExit('captcha_failed', UI.exitCaptchaHeading, UI.exitCaptcha);
        }
      };
      document.addEventListener('keydown', handler);
      ST._captchaHandler = handler;
    },
    val: function () { return get('captcha_pass') === true; }
  });
}

// ============================================================
// PRIMER AND COMPREHENSION (one retry; two failures end the session)
// ============================================================

function buildComprehension() {
  var cc = C.comprehension;
  function primerPage(attempt) {
    return {
      id: 'primer_' + attempt, timer: C.primer.minSeconds,
      cond: attempt === 2 ? function () { return get('comp_attempt1_pass') === false; } : null,
      html: '<div class="text-page">' + C.primer.paragraphs.map(function (p) { return '<p class="lead">' + p + '</p>'; }).join('') + '</div>',
      val: function () { return true; }
    };
  }
  function compPage(attempt) {
    var qs = cc.items.map(function (it) {
      return { id: it.id + '_attempt' + attempt, type: 'choice', text: it.text, options: cc.options, key: it.key, _comp: true };
    });
    return {
      id: 'comprehension_' + attempt,
      cond: attempt === 2 ? function () { return get('comp_attempt1_pass') === false; } : null,
      questions: qs,
      html: function () { return qs.map(questionHTML).join('') + '<p class="error-msg" id="err-comp' + attempt + '">' + UI.answerAll + '</p>'; },
      val: function () {
        if (!requireAll(qs, 'err-comp' + attempt)) return false;
        store(qs, ST.r, false);
        var pass = qs.every(function (q) { return String(ST.resp[q.id].value) === String(q.key); });
        rec('comp_attempt' + attempt + '_pass', pass);
        if (attempt === 2 && !pass) {
          rec('comp_failed_twice', true);
          earlyExit('comprehension_failed', UI.exitComprehensionHeading, UI.exitComprehension);
          return false;
        }
        if (pass) rec('comp_failed_twice', false);
        return true;
      }
    };
  }
  P.push(primerPage(1));
  P.push(compPage(1));
  P.push({
    id: 'comprehension_retry_notice',
    cond: function () { return get('comp_attempt1_pass') === false; },
    html: '<div class="center-text pad40"><p class="big">' + cc.retryNotice + '</p></div>',
    val: function () { return true; }
  });
  P.push(primerPage(2));
  P.push(compPage(2));
}

// ============================================================
// TRIALS
// ============================================================

function figHTML(im) {
  return '<figure class="stim-fig">' + (im.caption ? '<figcaption>' + im.caption + '</figcaption>' : '') + '<img class="stim" src="' + esc(C.stimuliDir + im.file) + '" alt=""></figure>';
}

function stimHTML(t, opts) {
  opts = opts || {};
  var c = C.trialContent(t);
  var lines = '', plan = '', stmt = '';
  (c.lines || []).forEach(function (l) { lines += '<p class="reminder">' + l + '</p>'; });   // lines above the statement
  if (c.heading && !opts.noPlan) plan += '<p class="plan-heading">' + c.heading + '</p>';
  if (c.plan && !opts.noPlan) plan += '<p class="plan">' + c.plan + '</p>';
  // The statement: one string (B1 until 1 November 2026) or one line per sentence.
  if (c.statement && !opts.noStatement) linesOf(c.statement).forEach(function (l) { stmt += '<p class="statement">' + l + '</p>'; });
  var h = '<div class="trial-text' + (C.pairTextBelow ? ' below' : '') + '">' + lines + plan + stmt + '</div>';
  var imgs = c.images.map(figHTML).join('');
  return { title: c.title ? '<p class="trial-title">' + c.title + '</p>' : '', text: h, n: c.images.length,
    lines: lines, plan: plan, statement: stmt,                                   // the parts, for the 1.6.0 side layout
    images: '<div class="trial-image' + (c.images.length > 1 ? ' pair' : '') + '">' + imgs + '</div>' };
}

// Trial screen. Default: text on top, image beside the questions (B1).
// With pairLayout 'top', an image pair and its text sit in a band across the
// top that stays in view while the questions scroll beneath it (A1); a title,
// if any, heads the band, and with pairTextBelow the statement follows the
// pair. With no questions (a viewPage), the band does not stay in view.
function trialLayout(t, questionsHTML, opts) {
  var s = stimHTML(t, opts);
  if (C.questionLayout === 'side' && questionsHTML && s.n >= 1 && C.sideTextUnderImage) {
    // 1.6.0 (B1): the image, then the heading and plan (the prompt), then the
    // statement (what was done), in the column that stays in view; the
    // questions alone beside it.
    return '<div class="trial trial-side text-under' + (s.n === 1 ? ' one-image' : '') + '"><div class="side-media">' + s.title + s.images
      + (s.plan ? '<div class="side-prompt">' + s.plan + '</div>' : '')
      + (s.statement ? '<div class="trial-text side-statement">' + s.lines + s.statement + '</div>' : '') + '</div>'
      + '<div class="trial-questions">' + questionsHTML + '</div></div>';
  }
  if (C.questionLayout === 'side' && questionsHTML && s.n >= 1) {
    // 1.4.0 (A1): title and the pair stacked in a column that stays in view;
    // statement and questions beside it. 1.5.0 (B1): one image the same way.
    return '<div class="trial trial-side' + (s.n === 1 ? ' one-image' : '') + '"><div class="side-media">' + s.title + s.images + '</div>'
      + '<div class="trial-questions">' + s.text + questionsHTML + '</div></div>';
  }
  if (C.pairLayout === 'top' && s.n >= 1) {
    var view = !questionsHTML;
    return '<div class="trial trial-top' + (view ? ' view-only' : '') + (s.n === 1 ? ' one-image' : '') + '"><div class="trial-band"' + (C.pairMaxHeight ? ' style="--pair-max-h:' + esc(C.pairMaxHeight) + '"' : '') + '>'
      + s.title + (C.pairTextBelow ? s.images + s.text : s.text + s.images) + '</div>'
      + (view ? '' : '<div class="trial-questions">' + questionsHTML + '</div>') + '</div>';
  }
  return '<div class="trial">' + s.title + (opts && opts.textBelow ? '' : s.text) + '<div class="trial-body">' + s.images
    + '<div class="trial-questions">' + (opts && opts.textBelow ? s.text : '') + questionsHTML + '</div></div></div>';
}

// One image alone, centered, with lines of text above it and, optionally,
// questions below it (preScreen pages; the A1 story-recall screen).
function singleLayout(c, questionsHTML) {
  var h = '<div class="single">';
  (c.lines || []).forEach(function (l) { h += '<p class="reminder">' + l + '</p>'; });
  h += '<div class="single-image"' + (c.maxHeight ? ' style="--single-max-h:' + esc(c.maxHeight) + '"' : '') + '>' + c.images.map(figHTML).join('') + '</div>';   // maxHeight: 1.5.0 (B1 recall)
  if (questionsHTML) h += '<div class="single-questions">' + questionsHTML + '</div>';
  return h + '</div>';
}

function activeTrialQuestions() {
  return C.trialQuestions.filter(function (q) { return !(C.dropItems || []).some(function (d) { return d === q.id; }); });
}

// The questions of one trial, in order. Without trialQuestionsFor, every
// trial asks every trial question (B1).
function trialQuestionsOf(t) {
  if (!C.trialQuestionsFor) return activeTrialQuestions();
  var qs = C.trialQuestionsFor(t, ST.derived);
  qs.forEach(function (q) {
    if (C.trialQuestions.indexOf(q) < 0) throw new Error('trialQuestionsFor returned an item that is not in trialQuestions: ' + q.id);
  });
  return qs.filter(function (q) { return !(C.dropItems || []).some(function (d) { return d === q.id; }); });
}

function notDropped(q) { return !(C.dropItems || []).some(function (d) { return d === q.id || (q.dropGroup && d === q.dropGroup); }); }

// A trial's questions as shown: {name} placeholders in their text filled from
// trialContent(t).vars (A1: the added elements). Without vars (B1), the items themselves.
function shownQuestions(t, qs) {
  var vars = C.trialContent(t).vars;
  return qs.map(function (q) { return withVars(q, vars); });
}

// The participant's answer to the trial's registration decision, quoted above
// the written-reason box (reasonQuote, A1): the chosen option's label and,
// when a follow-up was answered, the follow-up's label.
function reasonQuoteLines(t) {
  var rq = C.reasonQuote;
  var isDecision = function (q) { return q.type === 'decision'; };
  var dq = trialQuestionsOf(t).filter(isDecision)[0] || C.trialQuestions.filter(isDecision)[0];   // as this trial worded it (1.7.0)
  if (!rq || !dq || !t[dq.id]) return [];
  var out = [fill(rq.chosen, { label: dq.options[t[dq.id]] })];
  var f = dq.followUp;
  if (f && rq.followUp && t[f.id] !== undefined && t[f.id] !== '') {
    var o = f.options.filter(function (x) { return String(x.value) === String(t[f.id]); })[0];
    if (o) out.push(fill(rq.followUp, { label: o.label }));
  }
  return out;
}
function quoteHTML(t) {
  var quote = reasonQuoteLines(t);
  return quote.length ? '<div class="reason-quote">' + quote.map(function (l) { return '<p>' + l + '</p>'; }).join('') + '</div>' : '';
}

// A preScreen page: the trial's first image alone with its lines of text.
// prefix names the data fields (pre_page_ms, ...; would_pre_page_ms).
function preScreenPage(t, id, minSecs, prefix, recordImage) {
  var pg = {
    id: id, wide: true, trial: t, waitImages: minSecs > 0, minView: minSecs,
    html: function () { return singleLayout(C.preScreen.content(t)); },
    onShow: function () { t['_' + prefix + 'ShownAt'] = now(); },
    val: function () {
      t[prefix + '_page_ms'] = now() - t['_' + prefix + 'ShownAt'];
      if (recordImage) {
        t[prefix + '_image_load_ms'] = pg._imageLoadMs;
        t[prefix + '_image_error'] = pg._imageError;
        t[prefix + '_min_view_ms'] = minSecs * 1000;
      }
      return true;
    }
  };
  return pg;
}

function blockSpec(id) { return (C.blocks || []).filter(function (b) { return b.id === id; })[0]; }

function buildTrials() {
  var prevBlock = null;
  ST.order.forEach(function (pos, i) {
    var t = ST.trialByPos[pos];
    if (C.blocks && t.block !== prevBlock) {        // pages shown before a block (A1: follow-up section, rule, recall items)
      var b = blockSpec(t.block);
      if (b && b.before) buildPages(b.before, ST.order.slice(0, i));
      prevBlock = t.block;
    }
    var qs = trialQuestionsOf(t);
    if (C.trialQuestionsFor) t.trial_items = qs.filter(function (q) { return q.type !== 'note'; }).map(function (q) { return q.id; }).join(';');
    qs = shownQuestions(t, qs);
    if (C.trialStory) {
      // 1.4.0 (A1): how the first image was made, on its own page before the image.
      var st = C.trialStory(t);
      P.push({
        id: 'story_' + (i + 1), timer: st.minSeconds || 0, trial: t,
        html: '<div class="text-page trial-story">' + st.paragraphs.map(function (p) { return '<p class="lead">' + p + '</p>'; }).join('') + '</div>',
        onShow: function () { t._storyShownAt = now(); },
        val: function () { t.story_page_ms = now() - t._storyShownAt; return true; }
      });
    }
    if (C.preScreen) P.push(preScreenPage(t, 'pre_' + (i + 1), C.preScreen.minViewSeconds || 0, 'pre', true));
    if (C.viewPage) {
      // The trial without its questions, for at least minViewSeconds from
      // image load (A1); the question page that follows has no minimum.
      var view = {
        id: 'view_' + (i + 1), wide: true, waitImages: true, minView: C.minViewSeconds, trial: t,
        html: function () { return trialLayout(t, '', { noPlan: C.viewPageShowsPlan === false }); },
        onShow: function () { t._viewShownAt = now(); t.trial_shown_at_ms = sinceStart(); },
        val: function () {
          t.view_page_ms = now() - t._viewShownAt;
          t.image_load_ms = view._imageLoadMs;
          t.image_error = view._imageError;
          t.min_view_ms = C.minViewSeconds * 1000;
          return true;
        }
      };
      P.push(view);
    }
    var page = {
      id: 'trial_' + (i + 1), wide: true, waitImages: !C.viewPage, minView: C.minViewSeconds,
      questions: qs, trial: t,
      html: function () {
        return trialLayout(t, qs.map(questionHTML).join('') + '<p class="error-msg" id="err-trial' + i + '">' + UI.answerAll + '</p>');
      },
      onShow: function () { t._shownAt = now(); if (!C.viewPage) t.trial_shown_at_ms = sinceStart(); },
      val: function () {
        if (!requireAll(qs, 'err-trial' + i)) return false;
        store(qs, t, true);
        if (C.viewPage) {
          t.question_page_ms = now() - t._shownAt;
        } else {
          t.trial_page_ms = now() - t._shownAt;
          t.image_load_ms = page._imageLoadMs;
          t.image_error = page._imageError;
          t.min_view_ms = C.minViewSeconds * 1000;
        }
        t._answered = true;
        return true;
      }
    };
    P.push(page);

    // Further item screens on designated trials (A1: stop-others items 1 to 3),
    // after the trial's other items and before its written reason.
    (C.afterTrialScreens || []).forEach(function (sc) {
      if (!sc.showIf(t, ST.derived)) return;
      var sq = sc.questions.filter(function (q) { return !(C.dropItems || []).some(function (d) { return d === q.id; }); });
      if (!sq.some(function (q) { return q.type !== 'note'; })) return;
      P.push({
        id: sc.id + '_' + (i + 1), wide: true, questions: sq, trial: t,
        html: function () { return trialLayout(t, sq.map(questionHTML).join('') + '<p class="error-msg" id="err-' + sc.id + i + '">' + UI.answerAll + '</p>'); },
        onShow: function () { t['_' + sc.id + 'ShownAt'] = now(); },
        val: function () {
          if (!requireAll(sq, 'err-' + sc.id + i)) return false;
          store(sq, t, true);
          t[sc.id + '_page_ms'] = now() - t['_' + sc.id + 'ShownAt'];
          return true;
        }
      });
    });

    if (t.has_reason) {
      var rq = [C.reasonQuestion];
      P.push({
        id: 'reason_' + (i + 1), wide: true, questions: rq, trial: t,
        html: function () {
          // With reasonQuote, the answer being explained is quoted above the box.
          return trialLayout(t, quoteHTML(t) + rq.map(questionHTML).join('') + '<p class="error-msg" id="err-reason' + i + '">' + UI.answerAll + '</p>');
        },
        onShow: function () {
          t._reasonShownAt = now();
          if (C.reasonQuote) t[C.reasonQuestion.id + '_quote'] = reasonQuoteLines(t).map(plain).join(' ');
        },
        val: function () {
          if (!requireAll(rq, 'err-reason' + i)) return false;
          store(rq, t, false);
          t[C.reasonQuestion.id + '_page_ms'] = now() - t._reasonShownAt;
          return true;
        }
      });
    }

    if (C.instructed && i + 1 === C.instructed.afterTrial) {
      var iq = [{ id: C.instructed.id, type: 'choice', text: C.instructed.text, options: C.instructed.options, _instructed: true }];
      P.push({
        id: 'instructed', questions: iq,
        html: function () { return iq.map(questionHTML).join('') + '<p class="error-msg" id="err-instr">' + UI.answerAll + '</p>'; },
        val: function () {
          if (!requireAll(iq, 'err-instr')) return false;
          store(iq, ST.r, false);
          rec(C.instructed.id + '_pass', String(ST.resp[C.instructed.id].value) === String(C.instructed.pass));
          rec(C.instructed.id + '_after_trial', C.instructed.afterTrial);
          return true;
        }
      });
    }
  });
}

// "Would" block: the written-reason trials shown again, in the order they
// were first shown, each with the "would" item, its follow-up if it has one,
// and the confidence item. With would.preScreen, each is preceded by its
// first image alone, as in the trial; with would.intro, the block opens with
// that text page (A1 since 1.2.0, saved as <intro id>_page_ms).
function buildWould() {
  if (!C.would) return;                                      // A1 asks "would" in its follow-up section
  if ((C.dropItems || []).indexOf('would_block') >= 0) { rec('would_block_shown', false); return; }
  rec('would_block_shown', true);
  if (C.would.intro) buildPages([C.would.intro]);
  var shownTrials = ST.order.map(function (p) { return ST.trialByPos[p]; }).filter(function (t) { return t.has_would; });
  shownTrials.forEach(function (t, wi) {
    var qs = shownQuestions(t, C.would.questions);
    if (C.would.preScreen && C.preScreen) P.push(preScreenPage(t, 'would_pre_' + (wi + 1), C.would.preScreenMinViewSeconds || 0, 'would_pre', false));
    P.push({
      id: 'would_' + (wi + 1), wide: true, questions: qs, trial: t,
      waitImages: C.would.minViewSeconds > 0, minView: C.would.minViewSeconds,
      html: function () { return trialLayout(t, qs.map(questionHTML).join('') + '<p class="error-msg" id="err-would' + wi + '">' + UI.answerAll + '</p>'); },
      onShow: function () { t._wouldShownAt = now(); },
      val: function () {
        if (!requireAll(qs, 'err-would' + wi)) return false;
        store(qs, t, false);
        t.would_shown = true;
        t.would_order = wi + 1;
        t.would_page_ms = now() - t._wouldShownAt;
        return true;
      }
    });
  });
}

// Story recall on the designated trial: by default its image and plan shown
// again without its statement; recall.content(trial) can set what is shown
// instead (A1: the first image alone, without its reminder line).
function buildRecall() {
  if (!C.recall) return;
  var t = ST.trialByPos[ST.derived.recall_position];
  var q = { id: C.recall.id, type: 'choice', text: C.recall.text, options: C.recall.options, _recall: true };
  var correct = C.recall.correct(t);
  rec(C.recall.id + '_correct_answer', correct);
  P.push({
    id: 'recall', wide: true, questions: [q], trial: t,
    html: function () {
      var qh = questionHTML(q) + '<p class="error-msg" id="err-recall">' + UI.answerAll + '</p>';
      if (C.recall.content) return singleLayout(C.recall.content(t), qh);
      return trialLayout(t, qh, { noStatement: true });
    },
    val: function () {
      if (!requireAll([q], 'err-recall')) return false;
      store([q], ST.r, false);
      rec(C.recall.id + '_correct', String(ST.resp[q.id].value) === String(correct));
      return true;
    }
  });
}

// Pages placed by the configuration before a block: a text page (spec with
// paragraphs; its time on screen is saved as <id>_page_ms), revisit pages
// (spec with revisit; shown lists the trials already placed) or an item page.
function buildPages(specs, shown) {
  (specs || []).forEach(function (spec) {
    if (spec.paragraphs) {
      P.push({
        id: spec.id, timer: spec.minSeconds || 0,
        html: '<div class="text-page">' + spec.paragraphs.map(function (p) { return '<p class="lead">' + p + '</p>'; }).join('') + '</div>',
        onShow: function () { spec._shownAt = now(); },
        val: function () { rec(spec.id + '_page_ms', now() - spec._shownAt); return true; }
      });
    } else if (spec.revisit) {
      buildRevisit(spec, shown || []);
    } else {
      buildItemPages([spec]);
    }
  });
}

// Earlier trials shown again (1.2.0; A1 since 1.3.0: the follow-up section
// after block 1): every trial already shown that spec.revisit(trial, derived)
// picks, in the order first seen, with the trial's title, images and
// statement. Each trial gets one page, or (1.3.0) the pages of spec.pages,
// all shown before the next trial's; a page asks the items of
// questionsFor(trial, derived) (default its questions, which also set the
// data columns), less dropped items, and with quoteBefore shows the trial's
// quoted decision above that item. Answers are saved on the trial's row, with
// <spec id>_order and <page id>_page_ms.
function buildRevisit(spec, shown) {
  var picked = shown.map(function (p) { return ST.trialByPos[p]; }).filter(function (t) { return spec.revisit(t, ST.derived); });
  var pages = spec.pages || [spec];
  picked.forEach(function (t, k) {
    pages.forEach(function (pg) {
      var qs = pg.questionsFor ? pg.questionsFor(t, ST.derived) : pg.questions;
      qs.forEach(function (q) {
        if (pg.questions.indexOf(q) < 0) throw new Error('questionsFor of ' + pg.id + ' returned an item that is not in its questions: ' + q.id);
      });
      qs = shownQuestions(t, qs.filter(notDropped));
      if (!qs.some(function (q) { return q.type !== 'note'; })) return;      // every item of the page dropped
      P.push({
        id: pg.id + '_' + (k + 1), wide: true, questions: qs, trial: t,
        html: function () {
          return trialLayout(t, qs.map(function (q) { return (pg.quoteBefore === q.id ? quoteHTML(t) : '') + questionHTML(q); }).join('')
            + '<p class="error-msg" id="err-' + pg.id + k + '">' + UI.answerAll + '</p>');
        },
        onShow: function () {
          t['_' + pg.id + 'ShownAt'] = now();
          if (pg.quoteBefore) t[pg.quoteBefore + '_quote'] = reasonQuoteLines(t).map(plain).join(' ');
        },
        val: function () {
          if (!requireAll(qs, 'err-' + pg.id + k)) return false;
          store(qs, t, true);
          t[spec.id + '_order'] = k + 1;
          t[pg.id + '_page_ms'] = now() - t['_' + pg.id + 'ShownAt'];
          return true;
        }
      });
    });
  });
}

// Revisit specs of every block, for the data columns.
function revisitSpecs() {
  var out = [];
  (C.blocks || []).forEach(function (b) { (b.before || []).forEach(function (pg) { if (pg.revisit) out.push(pg); }); });
  return out;
}

// Generic item pages (end items, demographics, final questions)
function buildItemPages(pages) {
  (pages || []).forEach(function (pgSpec) {
    var qs = pgSpec.items;
    var page = {
      id: pgSpec.id, timer: pgSpec.minSeconds || 0, questions: qs, wide: !!pgSpec.wide,
      html: function () {
        var list = pgSpec.shuffleItems ? (page._order || (page._order = shuffle(qs))) : qs;
        if (pgSpec.shuffleItems && pgSpec.orderColumn) rec(pgSpec.orderColumn, list.map(function (q) { return q.id; }).join(';'));
        return (pgSpec.heading ? '<h1>' + pgSpec.heading + '</h1>' : '') + (pgSpec.intro ? '<p>' + pgSpec.intro + '</p>' : '')
          + list.map(questionHTML).join('') + '<p class="error-msg" id="err-' + pgSpec.id + '">' + UI.answerAll + '</p>';
      },
      val: function () {
        var req = qs.filter(function (q) { return q.required !== false; });
        if (!requireAll(req, 'err-' + pgSpec.id)) return false;
        store(qs, ST.r, false);
        return true;
      }
    };
    P.push(page);
  });
}

function buildDebrief() {
  P.push({
    id: 'debriefing', fin: true,
    html: '<h1>' + C.debrief.heading + '</h1><div class="debrief-text">' + C.debrief.paragraphs.map(function (p) { return '<p>' + p + '</p>'; }).join('')
      + '<p>' + fill(UI.contactLine, { name: esc(C.contact.name), email: '<a href="mailto:' + esc(C.contact.email) + '">' + esc(C.contact.email) + '</a>' }) + '</p></div>'
      + '<p>' + UI.saveInstruction + '</p>',
    val: function () { finalizeRecord('complete'); return true; }
  });
}

function buildAll() {
  if (ST.r.atlas_detected) {
    P.push({ id: 'blocked', html: '<h1>' + UI.blockedHeading + '</h1><p>' + UI.blockedText + '</p>', val: function () { return false; } });
    return;
  }
  buildGate();
  buildComprehension();
  P.push({
    id: 'story', timer: C.story.minSeconds,
    html: '<div class="text-page">' + C.story.paragraphs.map(function (p) { return '<p class="lead">' + p + '</p>'; }).join('') + '</div>',
    val: function () { return true; }
  });
  buildTrials();
  var recallFirst = C.recall && C.recall.afterTrials;          // 1.5.0 (B1): recall right after the last trial
  if (recallFirst) buildRecall();
  buildWould();
  if (!recallFirst) buildRecall();
  buildItemPages(C.endPages);
  buildItemPages(C.demographicsPages);
  buildItemPages(C.finalPages);
  buildDebrief();
}

// ============================================================
// EARLY EXITS, DECLINE, SAVE AND COMPLETION
// ============================================================

function earlyExit(reason, heading, text) {
  ST.exitReason = reason;
  finalizeRecord(reason);
  ST.pts.push({ p: -1, id: 'exit_' + reason, t: sinceStart() });
  var c = document.getElementById('pageContainer');
  document.getElementById('experimentContainer').classList.remove('wide');
  c.innerHTML = '<div class="page active center-text pad60"><h1 class="plain">' + heading + '</h1><p class="big">' + text + '</p>'
    + '<div class="btn-row center"><button class="btn" id="exitBtn" type="button">' + UI.completeButton + '</button></div></div>';
  document.getElementById('exitBtn').addEventListener('click', function () {
    this.disabled = true; this.textContent = UI.savingButton;
    finishStudy();
  });
  if (TEST && AUTO === 'run') setTimeout(function () { document.getElementById('exitBtn').click(); }, AUTO_DELAY);
}

// Declining consent: nothing is saved. With creditOnDecline, a SONA
// participant is still sent to the credit link (withdrawal without penalty).
function declined() {
  ST.exitReason = 'declined';
  var c = document.getElementById('pageContainer');
  c.innerHTML = '<div class="page active center-text pad60"><h1 class="plain">' + UI.declinedHeading + '</h1><p class="big">' + UI.declinedText + '</p>'
    + '<div class="btn-row center"><button class="btn" id="declineBtn" type="button">' + UI.completeButton + '</button></div></div>';
  document.getElementById('declineBtn').addEventListener('click', function () {
    exitFullscreen();
    if (!TEST && C.creditOnDecline && ST.platform === 'sona' && C.sonaCreditUrlBase) {
      window.location.href = C.sonaCreditUrlBase + encodeURIComponent(ST.pid || 'UNKNOWN');
      return;
    }
    c.innerHTML = '<div class="page active center-text pad60"><p class="big">' + UI.closeWindow + '</p>'
      + (TEST ? '<p class="muted">TEST MODE: declined; nothing saved.</p><pre id="csv-dump" style="display:none">DECLINED</pre>' : '') + '</div>';
  });
  if (TEST && AUTO === 'run') setTimeout(function () { document.getElementById('declineBtn').click(); }, AUTO_DELAY);
}

function finalizeRecord(exitReason) {
  rec('exit_reason', exitReason);
  rec('session_complete', exitReason === 'complete');
  rec('end_time', new Date().toISOString());
  rec('total_duration_ms', sinceStart());
  // Exclusion flags that the page can compute (the registration's rules).
  var f = {
    excl_comprehension: get('comp_failed_twice') === true,
    excl_captcha: get('captcha_pass') === false,
    excl_instructed: C.instructed ? get(C.instructed.id + '_pass') === false : false,
    excl_recall: C.recall ? get(C.recall.id + '_correct') === false : false
  };
  Object.keys(f).forEach(function (k) { rec(k, f[k]); });
  rec('excl_any_in_page', f.excl_comprehension || f.excl_captcha || f.excl_instructed || f.excl_recall);
  if (C.finalize) C.finalize(ST.r, ST.trials, rec, get);
}

// Columns, in a fixed order, so every session's file has the same header.
function columns() {
  var pre = ['study_code', 'engine_version', 'config_version', 'participant_id', 'code', 'is_test', 'test_mode', 'test_fail',
    'platform', 'platform_source', 'pavlovia_session', 'session_complete', 'exit_reason', 'start_time', 'end_time', 'total_duration_ms',
    'row'].concat(C.rowColumns || []).concat(['n_rows', 'dropped_items', 'open_rows', 'n_open_rows', 'open_rows_index', 'open_rows_source', 'open_rows_updated', 'assignment_source'])
    .concat(C.derivedColumns || []).concat(['trial_order', 'n_trials']);
  var trialCols = ['trial_position', 'list_position'].concat(C.trialColumns || []);
  if (C.trialStory) trialCols.push('story_page_ms');
  if (C.preScreen) trialCols.push('pre_page_ms', 'pre_image_load_ms', 'pre_image_error', 'pre_min_view_ms');
  if (C.viewPage) trialCols = trialCols.concat(['trial_shown_at_ms', 'view_page_ms', 'image_load_ms', 'image_error', 'min_view_ms', 'question_page_ms']);
  else trialCols = trialCols.concat(['trial_shown_at_ms', 'trial_page_ms', 'image_load_ms', 'image_error', 'min_view_ms']);
  if (C.trialQuestionsFor) trialCols.push('trial_items');
  var trialIdSeen = {};                                    // 1.7.0: an id with two wordings gets one set of columns
  activeTrialQuestionsAll().forEach(function (q) {
    allIds(q).forEach(function (id) {
      if (trialIdSeen[id]) return;
      trialIdSeen[id] = true;
      trialCols.push(id, id + '_rt_ms', id + '_rt_last_ms', id + '_n_changes');
      if (q.type === 'decision' && id === q.id) trialCols.push(id + '_display_pos');
    });
  });
  (C.afterTrialScreens || []).forEach(function (sc) {      // further item screens after a trial (unused since A1 1.2.0)
    sc.questions.forEach(function (q) {
      allIds(q).forEach(function (id) { trialCols.push(id, id + '_rt_ms', id + '_rt_last_ms', id + '_n_changes'); });
    });
    trialCols.push(sc.id + '_page_ms');
  });
  revisitSpecs().forEach(function (sp) {                    // A1: the follow-up section, on the rows of slots 6 and 7
    (sp.pages || [sp]).forEach(function (pg) {
      pg.questions.forEach(function (q) {
        if (pg.quoteBefore === q.id) trialCols.push(q.id + '_quote');
        allIds(q).forEach(function (id) {
          trialCols.push(id, id + '_rt_ms', id + '_rt_last_ms', id + '_n_changes');
          if (q.type === 'decision' && id === q.id) trialCols.push(id + '_display_pos');
          if (q.type === 'text') trialCols.push(id + '_chars', id + '_paste_attempts');
        });
      });
      if (sp.pages) trialCols.push(pg.id + '_page_ms');
    });
    trialCols.push(sp.id + '_order');
    if (!sp.pages) trialCols.push(sp.id + '_page_ms');
  });
  var rq = C.reasonQuestion;
  if (rq) {                                                // a written reason inside designated trials (B1)
    trialCols.push('has_reason');
    trialCols.push(rq.id, rq.id + '_rt_ms', rq.id + '_chars', rq.id + '_paste_attempts', rq.id + '_page_ms');
    if (C.reasonQuote) trialCols.push(rq.id + '_quote');
  }
  if (C.would) {                                           // the "would" block (B1)
    trialCols.push('would_shown', 'would_order');
    if (C.would.preScreen && C.preScreen) trialCols.push('would_pre_page_ms');
    trialCols.push('would_page_ms');
    C.would.questions.forEach(function (q) {
      allIds(q).forEach(function (id) {            // with no follow-up: the item's id only (B1)
        trialCols.push(id, id + '_rt_ms');
        if (q.type === 'decision' && id === q.id) trialCols.push(id + '_display_pos');
      });
    });
  }
  trialCols.push('is_recall_trial');

  var post = ['device_type', 'device_self_report', 'user_agent', 'screen_width', 'screen_height', 'fullscreen_entered', 'atlas_detected',
    'consent', 'consent_time', 'captcha_response', 'captcha_pass', 'captcha_rt_ms'];
  [1, 2].forEach(function (a) {
    C.comprehension.items.forEach(function (it) {
      var id = it.id + '_attempt' + a;
      post.push(id, id + '_rt_ms', id + '_correct');
    });
    post.push('comp_attempt' + a + '_pass');
  });
  post.push('comp_failed_twice');
  if (C.instructed) { var ii = C.instructed.id; post.push(ii, ii + '_rt_ms', ii + '_pass', ii + '_after_trial'); }
  (C.blocks || []).forEach(function (b) {          // pages before a block (A1: follow-up intro, rule paragraph, rule recall)
    (b.before || []).forEach(function (pg) {
      if (pg.revisit) return;                     // trial columns, above
      if (pg.paragraphs) { post.push(pg.id + '_page_ms'); return; }
      itemColumns(pg, post);
    });
  });
  if (C.would) post.push('would_block_shown');
  if (C.would && C.would.intro) post.push(C.would.intro.id + '_page_ms');
  if (C.recall) { var ri = C.recall.id; post.push(ri, ri + '_rt_ms', ri + '_correct_answer', ri + '_correct'); }
  [C.endPages, C.demographicsPages, C.finalPages].forEach(function (pages) {
    (pages || []).forEach(function (pg) { itemColumns(pg, post); });
  });
  post = post.concat(C.extraColumns || []);
  post.push('excl_comprehension', 'excl_captcha', 'excl_instructed', 'excl_recall', 'excl_any_in_page', 'page_timestamps', 'n_pages');
  return { participant: pre.concat(post), pre: pre, trial: trialCols, post: post };
}
function activeTrialQuestionsAll() { return C.trialQuestions; }
// Columns of one item page, in the order its answers are stored.
function itemColumns(pg, post) {
  if (pg.shuffleItems && pg.orderColumn) post.push(pg.orderColumn);
  pg.items.forEach(function (q) {
    if (q.shuffle && q.orderColumn) post.push(q.orderColumn);
    allIds(q).forEach(function (id) {
      post.push(id, id + '_rt_ms');
      if (q.key !== undefined && id === q.id) post.push(id + '_correct');
      if (q.type === 'text') post.push(id + '_chars', id + '_paste_attempts');
    });
  });
}

function csvCell(v) {
  if (v === null || v === undefined) v = '';
  if (Array.isArray(v)) v = v.join(';');
  if (typeof v === 'object') v = JSON.stringify(v);
  return '"' + String(v).replace(/"/g, '""') + '"';
}

function buildCSV() {
  rec('page_timestamps', JSON.stringify(ST.pts));
  rec('n_pages', P.length);
  rec('user_agent', navigator.userAgent);
  rec('screen_width', screen.width);
  rec('screen_height', screen.height);
  var cols = columns();
  var header = cols.pre.concat(cols.trial).concat(cols.post);
  var lines = [header.map(csvCell).join(',')];
  var trials = ST.order.map(function (p) { return ST.trialByPos[p]; });
  var shown = trials.filter(function (t) { return t._answered; });      // trials whose question page was completed
  var rows = shown.length ? shown : [null];
  rows.forEach(function (t) {
    var vals = cols.pre.map(function (k) { return ST.r[k]; })
      .concat(cols.trial.map(function (k) { return t ? t[k] : ''; }))
      .concat(cols.post.map(function (k) { return ST.r[k]; }));
    lines.push(vals.map(csvCell).join(','));
  });
  return lines.join('\n') + '\n';
}

function exitFullscreen() {
  try {
    if (document.fullscreenElement && document.exitFullscreen) document.exitFullscreen();
    else if (document.webkitFullscreenElement && document.webkitExitFullscreen) document.webkitExitFullscreen();
  } catch (e) {}
}

// Save first, then redirect to the SONA credit link (or show the completion page).
async function finishStudy() {
  if (ST.finished) return;
  ST.finished = true;
  var saved = false;
  var csv = buildCSV();
  ST.csv = csv;
  window.__ENGINE_CSV = csv;
  try { saved = await PAVLOVIA.save(csv); }
  catch (e) { console.error('[Study] Data save failed:', e); }
  exitFullscreen();
  if (!TEST && ST.platform === 'sona' && C.sonaCreditUrlBase) {
    window.location.href = C.sonaCreditUrlBase + encodeURIComponent(ST.pid || 'UNKNOWN');
    return;
  }
  showCompletionPage(saved);
}

function showCompletionPage(saved) {
  var c = document.getElementById('pageContainer');
  document.getElementById('experimentContainer').classList.remove('wide');
  var h = '<div class="page active center-text pad50"><h1 class="plain">' + UI.completeHeading + '</h1>';
  h += '<p class="big">' + (saved === false ? fill(UI.completeNotSaved, { email: esc(C.contact.email) }) : UI.completeSaved) + '</p>';
  if (ST.platform === 'sona' && !C.sonaCreditUrlBase) h += '<p>' + UI.completeNoSonaLink + '</p>';
  h += '<p>' + UI.completionCodeLabel + '</p><div class="completion-code">' + esc(C.completionCode) + '</div>';
  h += '<p class="muted">' + UI.closeWindow + '</p>';
  if (TEST) {
    var would = ST.platform === 'sona' && C.sonaCreditUrlBase ? C.sonaCreditUrlBase + encodeURIComponent(ST.pid) : '(no redirect)';
    h += '<p class="muted small">TEST MODE: exit_reason=' + esc(get('exit_reason')) + '; row=' + esc(get('row')) + '; a SONA session would go to ' + esc(would) + '</p>';
    h += '<pre id="csv-dump" style="display:none">' + esc(ST.csv) + '</pre>';
  }
  h += '</div>';
  c.innerHTML = h;
  document.getElementById('progressFill').style.width = '100%';
  window.scrollTo(0, 0);
}

function showFatalError(msg) {
  document.getElementById('loading-screen').style.display = 'none';
  document.getElementById('experimentContainer').style.display = 'block';
  document.getElementById('pageContainer').innerHTML = '<div class="page active center-text pad60"><h1 class="plain">' + UI.loadErrorHeading + '</h1><p class="big">' + esc(msg) + '</p><p>'
    + fill(UI.loadErrorContact, { name: esc(C.contact.name), email: '<a href="mailto:' + esc(C.contact.email) + '">' + esc(C.contact.email) + '</a>' }) + '</p></div>';
}

function preloadImages() {
  var files = {};
  ST.trials.forEach(function (t) { C.trialContent(t).images.forEach(function (im) { files[im.file] = true; }); });
  Object.keys(files).forEach(function (f) { var im = new Image(); im.src = C.stimuliDir + f; });
}

// ============================================================
// TEST MODE AUTOPILOT (?test=1). Fills every page and advances.
// ?test_fail=comp | comp1 | captcha | instructed | recall | decline
// ?auto=fill fills answers without clicking Next; ?auto=off does nothing.
// ============================================================

function pickAnswer(q) {
  if (q._auto !== undefined) return q._auto;
  if (q._comp) {
    var wrongFirst = TEST_FAIL === 'comp' || (TEST_FAIL === 'comp1' && /_attempt1$/.test(q.id));
    if (!wrongFirst) return q.key;
    return q.options.filter(function (o) { return String(o.value) !== String(q.key); })[0].value;
  }
  if (q._instructed) {
    if (TEST_FAIL === 'instructed') return C.instructed.options[0].value;
    return C.instructed.pass;
  }
  if (q._recall) {
    var correct = get(C.recall.id + '_correct_answer');
    if (TEST_FAIL === 'recall') return C.recall.options[C.recall.options.length - 1].value;
    return correct;
  }
  var opts = q.type === 'decision' ? optionsOf(q) : (q.options || q.points);
  return opts[rnd(opts.length)].value;
}

function setAnswer(q) {
  if (q.type === 'note') return;
  var root = document.getElementById('pageContainer');
  if (q.type === 'grid') {
    q.rows.forEach(function (r) {
      var rid = q.id + '_' + r.id;
      var c = q.columns[rnd(q.columns.length)].value;
      clickRadio(root, rid, c);
    });
    return;
  }
  if (q.type === 'slider') {
    var sl = root.querySelector('.slider[data-qid="' + q.id + '"]');
    if (sl && sl._set) sl._set(rnd(101));
    return;
  }
  if (q.type === 'text' || q.type === 'shorttext' || q.type === 'number') {
    var el = root.querySelector('[data-qid="' + q.id + '"]:not(.q)');
    if (el) {
      el.value = q.type === 'number' ? '20' : (q.type === 'text' ? 'Test answer written by the autopilot.' : 'Test');
      el.dispatchEvent(new Event('input', { bubbles: true }));
    }
    return;
  }
  if (q.type === 'checkbox') {
    var cb = root.querySelector('input[type="checkbox"][data-qid="' + q.id + '"]');
    if (cb) { cb.checked = true; cb.dispatchEvent(new Event('change', { bubbles: true })); }
    return;
  }
  var v = pickAnswer(q);
  clickRadio(root, q.id, v);
  if (q.followUp && String(v) === String(q.followUp.showIf)) {
    var fo = q.followUp.options;
    clickRadio(root, q.followUp.id, fo[rnd(fo.length)].value);
  }
}
function clickRadio(root, name, value) {
  var inp = root.querySelector('input[type="radio"][name="' + name + '"][value="' + String(value).replace(/"/g, '\\"') + '"]');
  if (inp) { inp.checked = true; inp.dispatchEvent(new Event('change', { bubbles: true })); }
  else console.warn('[Autopilot] no option', name, value);
}

function fillPage(pg) {
  if (pg.id === 'captcha') {
    var key = TEST_FAIL === 'captcha' ? 'z' : 'q';
    document.dispatchEvent(new KeyboardEvent('keydown', { key: key }));
    return;
  }
  (pg.questions || []).forEach(setAnswer);
}

function autopilot(pg) {
  var idx = ST.cp;
  setTimeout(function () {
    if (ST.cp !== idx || ST.exitReason) return;
    fillPage(pg);
    if (AUTO !== 'run') return;
    var tries = 0;
    var t = setInterval(function () {
      tries++;
      if (ST.cp !== idx || ST.exitReason || ST.finished) { clearInterval(t); return; }
      var nb = document.getElementById('nextBtn');
      if (nb && !nb.disabled && nb.style.display !== 'none') { clearInterval(t); nxt(); }
      if (tries > 2000) { clearInterval(t); console.error('[Autopilot] stuck on page', pg.id); }
    }, 5);
  }, AUTO_DELAY);
}

if (TEST || /^(pilot|test)/i.test(UP.get('participant') || UP.get('id') || '')) {
  window.ENGINE_DEBUG = { ST: ST, P: P, fillPage: function () { fillPage(P[ST.cp]); }, next: nxt, columns: columns, buildCSV: buildCSV };
}

// ============================================================
// INITIALIZE
// ============================================================

(async function () {
  document.title = C.pageTitle;
  parseIdentity();
  try { await assignRow(); }
  catch (e) { console.error(e); showFatalError(UI.assignError); return; }
  await PAVLOVIA.init();
  rec('pavlovia_session', PAVLOVIA.isActive ? 'open' : (isLocalHost() ? 'local' : 'failed'));
  if (!PAVLOVIA.isActive && !isLocalHost()) {
    showFatalError(UI.serverError);
    return;
  }
  buildAll();
  preloadImages();
  document.getElementById('loading-screen').style.display = 'none';
  document.getElementById('experimentContainer').style.display = 'block';
  render(0);
})();

})();
