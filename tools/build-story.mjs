#!/usr/bin/env node
'use strict';
/* ============================================================
   build-story.mjs — extract all dialogue from chapter1.js into
   public/assets/story-manifest.json for the story explorer
   (public/story.html).

   Re-runnable: extraction is anchored to enclosing function
   names and line content prefixes, never to line numbers, so it
   survives concurrent edits to the chapter (e.g. playEnding).

   Run:  node tools/build-story.mjs
   ============================================================ */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const CH1 = path.join(ROOT, 'public/js/chapter1.js');
const MAIN = path.join(ROOT, 'public/js/main.js');
const OUT = path.join(ROOT, 'public/assets/story-manifest.json');

const src = fs.readFileSync(CH1, 'utf8');
const mainSrc = fs.readFileSync(MAIN, 'utf8');

const warnings = [];
const warn = (msg) => { warnings.push(msg); console.warn('  ⚠ ' + msg); };

/* ---------------- tiny source scanner ---------------- */

function skipString(s, i) {                 // s[i] is a quote; returns index of the closing quote
  const q = s[i];
  for (let k = i + 1; k < s.length; k++) {
    if (s[k] === '\\') { k++; continue; }
    if (s[k] === q) return k;
  }
  return s.length;
}

function matchBracket(s, i) {               // s[i] is ( [ or { ; returns index of the matching closer
  let depth = 0;
  for (let k = i; k < s.length; k++) {
    const c = s[k];
    if (c === "'" || c === '"' || c === '`') { k = skipString(s, k); continue; }
    if (c === '/' && s[k + 1] === '/') { k = s.indexOf('\n', k); if (k === -1) return -1; continue; }
    if (c === '/' && s[k + 1] === '*') { k = s.indexOf('*/', k) + 1; if (k === 0) return -1; continue; }
    if (c === '(' || c === '[' || c === '{') depth++;
    else if (c === ')' || c === ']' || c === '}') { depth--; if (depth === 0) return k; }
  }
  return -1;
}

function topLevelSplit(s) {                 // split on top-level commas, respecting strings/brackets
  const out = [];
  let start = 0, depth = 0;
  for (let k = 0; k < s.length; k++) {
    const c = s[k];
    if (c === "'" || c === '"' || c === '`') { k = skipString(s, k); continue; }
    if (c === '(' || c === '[' || c === '{') depth++;
    else if (c === ')' || c === ']' || c === '}') depth--;
    else if (c === ',' && depth === 0) { out.push(s.slice(start, k)); start = k + 1; }
  }
  out.push(s.slice(start));
  return out.map(x => x.trim()).filter(Boolean);
}

function topLevelItems(s, open) {           // find top-level [..] or {..} spans inside s
  const close = open === '[' ? ']' : '}';
  const items = [];
  let depth = 0;
  for (let k = 0; k < s.length; k++) {
    const c = s[k];
    if (c === "'" || c === '"' || c === '`') { k = skipString(s, k); continue; }
    if (c === open && depth === 0) {
      const end = matchBracket(s, k);
      if (end === -1) break;
      items.push(s.slice(k + 1, end));
      k = end;
      continue;
    }
    if (c === '(' || c === '[' || c === '{') depth++;
    else if (c === ')' || c === ']' || c === '}') depth--;
  }
  return items;
}

const unesc = (v) => v.replace(/\\(.)/g, '$1');
const STR = /'((?:\\.|[^'\\])*)'/;          // single-quoted literal (file uses typographic ’ inside)

/* an expression that is either 'literal' or `cond ? 'a' : 'b'` → variants list */
function condLabels(cond) {
  const c = cond.trim();
  if (/isVesper|role\s*===\s*'vesper'/.test(c)) return ['as Vesper', 'as Lake'];
  if (/hushDone/.test(c)) return ['after the Hush', 'before the Hush'];
  if (/alive|'festival'/.test(c)) return ['before the Hush', 'after the Hush'];
  return ['if ' + c, 'otherwise'];
}

function parseExpr(expr) {                  // → [{ value, label|null }] (1 or 2 variants) | null
  const e = expr.trim().replace(/,\s*$/, '');
  let m = e.match(new RegExp('^' + STR.source + '$'));
  if (m) return [{ value: unesc(m[1]), label: null }];
  m = e.match(new RegExp('^(.*?)\\?\\s*' + STR.source + '\\s*:\\s*' + STR.source + '\\s*$', 's'));
  if (m) {
    const [a, b] = condLabels(m[1]);
    return [{ value: unesc(m[2]), label: a }, { value: unesc(m[3]), label: b }];
  }
  return null;
}

/* a ['who', 'text'] pair (either side may be a ternary) → lines [[who, text, variant?]] */
function parsePair(pairSrc) {
  const parts = topLevelSplit(pairSrc);
  if (parts.length < 2) return [];
  const whos = parseExpr(parts[0]);
  const texts = parseExpr(parts.slice(1).join(','));
  if (!whos || !texts) return [];
  const n = Math.max(whos.length, texts.length);
  const lines = [];
  for (let i = 0; i < n; i++) {
    const w = whos[Math.min(i, whos.length - 1)];
    const t = texts[Math.min(i, texts.length - 1)];
    const variant = t.label || w.label;
    lines.push(variant ? [w.value, t.value, variant] : [w.value, t.value]);
  }
  return lines;
}

/* ---------------- function slicing ---------------- */

function sliceMethods(source) {             // 2-space-indented methods of the Chapter1 object literal
  const re = /^ {2}(?:async )?([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*\{/gm;
  const marks = [];
  let m;
  while ((m = re.exec(source))) marks.push({ name: m[1], at: m.index });
  const out = {};
  for (let i = 0; i < marks.length; i++)
    out[marks[i].name] = source.slice(marks[i].at, i + 1 < marks.length ? marks[i + 1].at : source.length);
  return out;
}
const FN = sliceMethods(src);

function fnSlice(name) {
  if (!FN[name]) warn(`function ${name}() not found in chapter1.js`);
  return FN[name] || '';
}

/* ---------------- extractors ---------------- */

/* cutscene steps (say / narrate / banner / toast / dialog / bothHold), in source order */
function extractCutscene(fnName) {
  const s = fnSlice(fnName);
  const lines = [];
  const stepRe = /\{\s*(say|narrate|banner|toast|dialog|bothHold)\s*:/g;
  let m;
  while ((m = stepRe.exec(s))) {
    const kind = m[1];
    const at = m.index + m[0].length;
    const rest = s.slice(at);
    if (kind === 'say' || kind === 'dialog') {
      const br = rest.indexOf('[');
      if (br === -1) continue;
      const end = matchBracket(rest, br);
      const body = rest.slice(br + 1, end);
      if (kind === 'say') lines.push(...parsePair(body));
      else for (const pair of topLevelItems(body, '[')) lines.push(...parsePair(pair));
      stepRe.lastIndex = at + end;
    } else if (kind === 'narrate') {
      const sm = rest.match(STR);
      if (sm) lines.push(['narrate', unesc(sm[1])]);
    } else if (kind === 'banner') {
      const br = rest.indexOf('{');
      if (br === -1) continue;
      const body = rest.slice(br + 1, matchBracket(rest, br));
      const t = body.match(new RegExp("title:\\s*" + STR.source));
      const sub = body.match(new RegExp("sub:\\s*" + STR.source));
      if (t) lines.push(['banner', unesc(t[1]) + (sub ? ' — ' + unesc(sub[1]) : '')]);
    } else if (kind === 'toast') {
      const t = rest.match(new RegExp("text:\\s*" + STR.source));
      if (t) lines.push(['toast', unesc(t[1])]);
    } else if (kind === 'bothHold') {
      const t = rest.match(new RegExp("prompt:\\s*" + STR.source));
      if (t) lines.push(['system', '[' + unesc(t[1]) + ']']);
    }
  }
  if (!lines.length) warn(`cutscene ${fnName}: no dialogue extracted`);
  return lines;
}

/* all D([...]) / D(cond ? [...] : [...]) blocks in talkTo, in source order */
function extractTalkBlocks() {
  const s = fnSlice('talkTo');
  const blocks = [];
  const re = /(?<![\w.])D\(/g;
  let m;
  while ((m = re.exec(s))) {
    const par = m.index + 1 + m[0].length - 2;     // index of '('
    const open = m.index + m[0].length - 1;
    const end = matchBracket(s, open);
    if (end === -1) continue;
    const inner = s.slice(open + 1, end);
    const arrays = topLevelItems(inner, '[');
    const trimmed = inner.trim();
    if (trimmed.startsWith('[')) {
      // plain D([pairs...], onFinish?) — first top-level array is the lines
      const body = arrays[0] || '';
      const lines = [];
      for (const pair of topLevelItems(body, '[')) lines.push(...parsePair(pair));
      if (lines.length) blocks.push({ lines, variant: null });
    } else {
      // D(cond ? [A] : [B])
      const cond = trimmed.slice(0, trimmed.indexOf('?'));
      const [la, lb] = condLabels(cond);
      arrays.slice(0, 2).forEach((body, i) => {
        const lines = [];
        for (const pair of topLevelItems(body, '[')) lines.push(...parsePair(pair));
        if (lines.length) blocks.push({ lines, variant: i === 0 ? la : lb });
      });
    }
    re.lastIndex = end;
    void par;
  }
  return blocks;
}
const TALK = extractTalkBlocks();
const talkUsed = new Set();

function talkBlock(prefix, context) {
  const idx = TALK.findIndex(b => b.lines[0] && b.lines[0][1].startsWith(prefix));
  if (idx === -1) {
    warn(`talkTo block not found: "${prefix}"`);
    return { context, lines: [['system', `(missing — no talkTo block starting “${prefix}…”)`]] };
  }
  talkUsed.add(idx);
  const b = TALK[idx];
  return { context: context + (b.variant ? ` — ${b.variant}` : ''), lines: b.lines };
}

/* Dialog.start([...]) blocks inside a given function slice, in source order */
function extractDialogStarts(fnName) {
  const s = fnSlice(fnName);
  const blocks = [];
  const re = /Dialog\.start\(\s*\[/g;
  let m;
  while ((m = re.exec(s))) {
    const br = s.indexOf('[', m.index);
    const end = matchBracket(s, br);
    if (end === -1) continue;
    const body = s.slice(br + 1, end);
    const lines = [];
    for (const obj of topLevelItems(body, '{')) {
      const om = obj.match(/who\s*:\s*((?:\\.|[^,])+?),\s*text\s*:\s*([\s\S]+)$/);
      if (!om) continue;
      const whos = parseExpr(om[1]);
      const texts = parseExpr(om[2].trim().replace(/\}?\s*$/, ''));
      if (!whos || !texts) continue;
      const n = Math.max(whos.length, texts.length);
      for (let i = 0; i < n; i++) {
        const w = whos[Math.min(i, whos.length - 1)];
        const t = texts[Math.min(i, texts.length - 1)];
        const variant = t.label || w.label;
        lines.push(variant ? [w.value, t.value, variant] : [w.value, t.value]);
      }
    }
    if (lines.length) blocks.push(lines);
    re.lastIndex = end;
  }
  return blocks;
}

function dialogStartBlock(fnName, prefix, context) {
  const all = extractDialogStarts(fnName);
  const found = all.find(lines => lines[0] && lines[0][1].startsWith(prefix));
  if (!found) {
    warn(`Dialog.start in ${fnName} not found: "${prefix}"`);
    return { context, lines: [['system', `(missing — no Dialog.start starting “${prefix}…”)`]] };
  }
  return { context, lines: found };
}

/* interact() flavor: each `t.kind === 'x'` branch with its Dialog.start (incl. ternary variants) */
function extractInteract(kind, context) {
  const s = fnSlice('interact');
  const at = s.indexOf(`t.kind === '${kind}'`);
  if (at === -1) {
    warn(`interact kind not found: ${kind}`);
    return { context, lines: [['system', `(missing — interact '${kind}')`]] };
  }
  const nextKind = s.indexOf('t.kind ===', at + 10);
  const region = s.slice(at, nextKind === -1 ? s.length : nextKind);
  const tmp = { interactRegion: region };
  const saved = FN.interactRegion; FN.interactRegion = region;
  const blocks = extractDialogStarts('interactRegion');
  if (saved === undefined) delete FN.interactRegion; else FN.interactRegion = saved;
  void tmp;
  if (!blocks.length) {
    warn(`interact '${kind}': no dialogue found`);
    return { context, lines: [['system', `(missing — interact '${kind}')`]] };
  }
  return { context, lines: blocks.flat() };
}

/* deniedLine entries in buildScenes, with their destination */
function extractDeniedExits() {
  const s = fnSlice('buildScenes');
  const lines = [];
  const re = new RegExp("deniedLine:\\s*\\[\\s*" + STR.source + "\\s*,\\s*" + STR.source + "\\s*\\]", 'g');
  let m;
  while ((m = re.exec(s))) {
    const back = s.slice(Math.max(0, m.index - 400), m.index);
    const to = [...back.matchAll(/to:\s*'(\w+)'/g)].pop();
    lines.push([unesc(m[1]), unesc(m[2]), to ? `way to the ${to[1]} blocked` : 'blocked way']);
  }
  if (!lines.length) warn('no deniedLine entries found');
  return lines;
}

/* a plain string literal anywhere in a slice, matched by prefix */
function findString(fnName, prefix) {
  const s = fnSlice(fnName);
  const re = new RegExp(STR.source, 'g');
  let m;
  while ((m = re.exec(s))) if (unesc(m[1]).startsWith(prefix)) return unesc(m[1]);
  warn(`string not found in ${fnName}(): "${prefix}"`);
  return `(missing — “${prefix}…”)`;
}

/* end-card text from drawEnd() in main.js */
function extractEndCard() {
  const at = mainSrc.indexOf('function drawEnd');
  if (at === -1) { warn('drawEnd not found in main.js'); return []; }
  const next = mainSrc.indexOf('\nfunction ', at + 10);
  const s = mainSrc.slice(at, next === -1 ? mainSrc.length : next);
  const lines = [];
  const re = new RegExp("fillText\\(\\s*" + STR.source, 'g');
  let m;
  while ((m = re.exec(s))) {
    const v = unesc(m[1]);
    if (/^\W?🕯/u.test(v)) continue;
    lines.push(['system', v]);
  }
  if (!lines.length) warn('drawEnd: no text extracted');
  return lines;
}

/* ---------------- story bible (STORY.md) ---------------- */
/* Parsed at build time into { sections: [{ id, title, body, subs: [{title, body}] }] }.
   STORY.md stays the single source of truth; the explorer renders from the manifest.
   Split on ## headings; the premise text before the first ## is its own entry;
   §5 subs split on '- **Ch. N' list items; §6 subs on bolded character names;
   other sections sub-split on ### headings; the trailing '### Canon quick-reference'
   is peeled out of §7 into its own top-level section. */

function parseBible() {
  const raw = fs.readFileSync(path.join(ROOT, 'STORY.md'), 'utf8');
  const slug = (t) => t.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
  const sections = [];

  const body = raw.replace(/^# .*\r?\n/, '');            // drop the document title line
  const chunks = body.split(/\r?\n(?=## )/);

  // premise: everything before the first "## " (minus the trailing rule)
  const premise = chunks.shift().replace(/\r?\n---\s*$/, '').trim();
  if (premise) sections.push({ id: 'premise', title: 'Premise', body: premise, subs: [] });
  else warn('bible: no premise text found before the first ## heading');

  let canon = null;
  for (const chunk of chunks) {
    const nl = chunk.indexOf('\n');
    const title = chunk.slice(3, nl === -1 ? undefined : nl).trim();
    let secBody = nl === -1 ? '' : chunk.slice(nl + 1).trim();
    const subs = [];

    // peel the canon quick-reference off the end of the last section
    const ci = secBody.search(/^### Canon quick-reference/m);
    if (ci !== -1) {
      const cChunk = secBody.slice(ci);
      secBody = secBody.slice(0, ci).replace(/\r?\n---\s*$/, '').trim();
      const cn = cChunk.indexOf('\n');
      canon = { id: 'canon-quick-reference', title: cChunk.slice(4, cn === -1 ? undefined : cn).trim(),
        body: cn === -1 ? '' : cChunk.slice(cn + 1).trim(), subs: [] };
    }

    if (/^5\./.test(title)) {
      // arc chapters: one sub per '- **Ch. N — Title.**' list item
      const parts = secBody.split(/\r?\n(?=- \*\*Ch\. )/);
      secBody = parts.shift().trim();
      for (const p of parts) {
        const m = p.match(/^- \*\*(Ch\.\s*\d+\s*—\s*[^*]+?)\.?\*\*\s*([\s\S]*)$/);
        if (!m) { warn('bible §5: unparsed chapter list item'); continue; }
        subs.push({ title: m[1].trim(), body: m[2].replace(/\r?\n\s*/g, ' ').trim() });
      }
      if (subs.length !== 9) warn(`bible §5: expected 9 chapter subs, found ${subs.length}`);
    } else if (/^6\./.test(title)) {
      // characters: one sub per bolded '**Name** — ' at line start
      const parts = secBody.split(/\r?\n(?=\*\*[^*\n]+\*\* — )/);
      secBody = /^\*\*[^*\n]+\*\* — /.test(parts[0]) ? '' : parts.shift().trim();
      for (const p of parts) {
        const m = p.match(/^\*\*([^*\n]+)\*\*/);
        if (!m) { warn('bible §6: unparsed character entry'); continue; }
        subs.push({ title: m[1].trim(), body: p.trim() });
      }
      if (subs.length < 8) warn(`bible §6: only ${subs.length} character subs found`);
    } else {
      // generic: sub-split on ### headings, if any
      const parts = secBody.split(/\r?\n(?=### )/);
      if (parts.length > 1 || /^### /.test(parts[0])) {
        secBody = /^### /.test(parts[0]) ? '' : parts.shift().trim();
        for (const p of parts) {
          const pn = p.indexOf('\n');
          subs.push({ title: p.slice(4, pn === -1 ? undefined : pn).trim(),
            body: pn === -1 ? '' : p.slice(pn + 1).trim() });
        }
      }
    }

    sections.push({ id: slug(title), title, body: secBody, subs });
  }
  if (canon) sections.push(canon);
  else warn('bible: Canon quick-reference section not found');
  return { source: 'STORY.md', sections };
}

const bible = parseBible();

/* ================= THE SCAFFOLD ================= */
/* Hand-authored story structure; every block resolves against the live source. */

const B = (title, scene, summary, blocks) => ({ title, scene, summary, blocks });

const chapterOne = {
  title: 'Chapter One — Emberwake',
  sub: 'a mapmaker, a lamplighter, and the night the village forgot itself',
  beats: [
    B('Opening — Vesper', 'forest',
      'On the last night of autumn, a mapmaker follows a road she has only ever dreamed.',
      [{ context: 'cutscene — Vesper’s arrival (playVesperIntro)', lines: extractCutscene('playVesperIntro') }]),

    B('The waystone & Mochi', 'entrance',
      'The waystone from drawing forty-one is real, and a cat decides something about Vesper.',
      [
        { context: 'cutscene — at the village entrance (playWaystone)', lines: extractCutscene('playWaystone') },
        extractInteract('waystone', 'looking at the waystone (flavor, by role)'),
      ]),

    B('The square — Emberwake festival', 'square',
      'Vesper meets the villagers on festival night and learns what the Kindling Hour is.',
      [
        talkBlock('A new face!', 'talking to Poppy as Vesper, pre-Hush (the telling explained)'),
        talkBlock('Pip, love, stop orbiting', 'talking to Mara & Pip as Vesper, pre-Hush'),
        talkBlock('A guest! Welcome', 'talking to Rowan as Vesper before greeting two villagers'),
        talkBlock('Now then. A guest', 'talking to Rowan as Vesper, pre-Hush (leads into Vesper’s outro)'),
        talkBlock('Mrrp.', 'talking to Mochi, pre-Hush'),
        extractInteract('notice', 'the notice board (flavor, before/after the Hush)'),
        extractInteract('heartlight', 'the Heartlight (flavor, before/after the Hush)'),
      ]),

    B('Interlude — the third honeybun', 'square',
      'Vesper waits for the lamps; the story turns to the other side of the village.',
      [{ context: 'cutscene — Vesper’s outro / Lake’s title card (playVesperOutro)', lines: extractCutscene('playVesperOutro') }]),

    B('Lake — the cottage', 'interior',
      'The last lamplighter takes down his grandmother’s flame, a year after she set it down.',
      [
        { context: 'cutscene — Lake’s introduction (playLakeIntro)', lines: extractCutscene('playLakeIntro') },
        extractInteract('hearth', 'the hearth (flavor)'),
      ]),

    B('The rounds', 'lane',
      'Three dark lamps before the Kindling Hour — and the pond has started acting strangely.',
      [
        dialogStartBlock('lightLamp', '(One.', 'lighting the first lamp'),
        dialogStartBlock('lightLamp', '(Two.', 'lighting the second lamp'),
        talkBlock('Festival’s up in the square.', 'talking to Finn in the lane, pre-Hush (Vesper/Lake variants)'),
        talkBlock('There he is!', 'talking to Poppy as Lake, pre-Hush'),
        talkBlock('Lake! The Kindling Hour', 'talking to Rowan as Lake, pre-Hush'),
        talkBlock('He’s been up since dawn', 'talking to Mara & Pip as Lake, pre-Hush'),
        talkBlock('(Mochi is escorting', 'talking to Mochi, pre-Hush'),
        { context: 'blocked ways (denied-exit lines, shown when a road can’t be taken)',
          lines: extractDeniedExits() },
      ]),

    B('The meet', 'square',
      'The mapmaker finds the lamplighter — just as the Kindling Hour is called.',
      [{ context: 'cutscene — Vesper meets Lake (playMeet)', lines: extractCutscene('playMeet') }]),

    B('The Kindling Hour & the Hush', 'square',
      'The village brings its year to the flame — and between two heartbeats, the light leaves.',
      [{ context: 'cutscene — the festival and the catastrophe (playKindlingHour)', lines: extractCutscene('playKindlingHour') }]),

    B('Aftermath — seeing to the village', 'square',
      'Two strangers give the villagers their names back, borrowed, one by one.',
      [
        talkBlock('See to them first.', 'talking to Rowan before seeing to everyone, post-Hush'),
        talkBlock('…Why am I holding bread? Whose stall is this? Whose HANDS', 'seeing to Poppy, post-Hush'),
        talkBlock('Honeybuns. Poppy. Thumb.', 'talking to Poppy again, post-Hush (repeat)'),
        talkBlock('Can’t recall my own name', 'seeing to Finn, post-Hush'),
        talkBlock('Finn. Still short.', 'talking to Finn again, post-Hush (repeat)'),
        talkBlock('Tell her. TELL her!', 'seeing to Mara & Pip, post-Hush'),
        talkBlock('I’m teaching her me again.', 'talking to Mara & Pip again, post-Hush (repeat)'),
        talkBlock('The cat. The cat is FINE?!', 'seeing to Mochi, post-Hush'),
        talkBlock('Mrrrrp.', 'talking to Mochi again, post-Hush (repeat)'),
      ]),

    B('The pact', 'square',
      'Rowan reads the fading ledger, names the Kindling, and binds two keepers to one flame.',
      [
        dialogStartBlock('playPact', 'Both of you.', 'Rowan, if only one keeper comes to him'),
        { context: 'cutscene — the pact by the Heartlight (playPact)', lines: extractCutscene('playPact') },
        talkBlock('Twin sigils, before the Gate. Two keepers', 'talking to Rowan after the pact (repeat)'),
      ]),

    B('The gate & the sigils', 'gate',
      'Two keepers stand the twin sigils together, and the Old Gate opens.',
      [{ context: 'objective & prompt text at the Old Gate', lines: [
        ['system', findString('objective', 'Stand on the twin sigils')],
        ['system', findString('promptFor', 'Stand on the sigil')],
        ['system', findString('objective', 'Step through the Old Gate')],
      ] }]),

    B('The ending — beyond the gate', 'gate',
      'The road beyond runs grey with moths, and the first lamp of the long road waits.',
      [{ context: 'cutscene — the road beyond the gate (playEnding)', lines: extractCutscene('playEnding') }]),

    B('End card', 'gate',
      'End of Chapter One.',
      [{ context: 'the end card (drawEnd, main.js)', lines: extractEndCard() }]),
  ],
};

/* unplaced talkTo blocks (new dialogue since the scaffold was written) get surfaced, not dropped */
const unplaced = TALK.map((b, i) => ({ b, i })).filter(x => !talkUsed.has(x.i));
if (unplaced.length) {
  warn(`${unplaced.length} talkTo block(s) not referenced by the scaffold — appended as an extra beat`);
  chapterOne.beats.push(B('Unplaced dialogue (new since scaffold)', '—',
    'talkTo blocks found in the source but not yet placed in a beat — re-check the scaffold.',
    unplaced.map(x => ({ context: `talkTo block #${x.i}` + (x.b.variant ? ` — ${x.b.variant}` : ''), lines: x.b.lines }))));
}

/* planned chapters — one beat each, one-liners from STORY.md §5 */
const planned = {
  title: 'Chapters 2–10 (planned)',
  sub: 'the arc of the Long Rekindling — no dialogue written yet',
  beats: [
    B('Ch. 2 — The Lanternstead', 'the Whisperwood road',
      'First road chapter: Tally, the Order’s cheerfully unqualified last friar, joins; the rules of the road are learned; Rowan’s first letter arrives with three blanks.', []),
    B('Ch. 3 — Harrowdel', 'a living valley',
      'The Warden recalls Harrowdel before the party’s eyes — first face-to-face, first bow; Sable the heretic moth-catcher joins in cold fury.', []),
    B('Ch. 4 — The Ferry', 'the river crossing',
      'Marrow the ferryman takes payment only in memories, feels one for the first time in years, and poles after them: “You’ve paid me before. Long ago.”', []),
    B('Ch. 5 — Ashfield', 'a grey valley',
      'Vesper’s birthplace. Midpoint reveal: her dreams are her own name calling from the mother-fire; Lake finally says grandmother’s sayings as teaching, not grief.', []),
    B('Ch. 6 — The Parley', 'the road',
      'The Warden speaks: the Kindling is dying; he offers Lake the succession and asks for the lighter. Lake learns of the unclaimed year and takes the knife of it.', []),
    B('Ch. 7 — The Mothway', 'a storm of moths',
      'The migration reveals moths as stray moments; a meant fire calls them home; Lake finally understands “mean it” and stops improvising.', []),
    B('Ch. 8 — The Gatehouse', 'the Warden’s home',
      'The archive of poured valleys. The mechanism of restoration is confirmed — Vesper’s notebook and Rowan’s ledger become the endgame keys; Marrow repays his debt.', []),
    B('Ch. 9 — The Pouring', 'the clearing of drawing forty-one',
      'The Kindling is nearly ash; the pour begins; stopping it saves Emberbrook and starves the mother-fire. Nobody is wrong. Cliffhanger on the choice.', []),
    B('Ch. 10 — The Long Rekindling', 'the Kindling',
      'The lighter goes home to the stone bowl; Emberbrook is called back name by name, Pip first; the Warden is kept by the flame he served; the circuit is walked again.', []),
  ],
};

/* ================= write ================= */

const chapters = [chapterOne, planned];
let nBlocks = 0, nLines = 0;
for (const ch of chapters) for (const bt of ch.beats) {
  nBlocks += bt.blocks.length;
  for (const bl of bt.blocks) nLines += bl.lines.length;
}

const nSubs = bible.sections.reduce((a, s) => a + s.subs.length, 0);

const manifest = {
  generated: new Date().toISOString(),
  source: 'public/js/chapter1.js (+ drawEnd in main.js, arc from STORY.md §5, bible from STORY.md)',
  stats: { blocks: nBlocks, lines: nLines, talkToBlocksFound: TALK.length,
    bibleSections: bible.sections.length, bibleSubs: nSubs, warnings },
  bible,
  chapters,
};

fs.writeFileSync(OUT, JSON.stringify(manifest, null, 1));
console.log(`story-manifest.json written — ${chapters.length} chapters, ` +
  `${chapterOne.beats.length} Ch.1 beats, ${nBlocks} blocks, ${nLines} lines, ` +
  `bible ${bible.sections.length} sections / ${nSubs} subs` +
  (warnings.length ? `, ${warnings.length} warning(s)` : ', no warnings'));
