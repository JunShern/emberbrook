#!/usr/bin/env node
'use strict';
/* ============================================================
   build-story.mjs — extract all dialogue from chapter1.js,
   chapter2.js (Dellhollow) and chapter3.js (the Lanternstead)
   into public/assets/story-manifest.json for the story
   explorer (public/story.html).

   Re-runnable: extraction is anchored to enclosing function
   names and line content prefixes, never to line numbers, so it
   survives concurrent edits to the chapters (e.g. playEnding).

   Run:  node tools/build-story.mjs
   ============================================================ */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const MAIN = path.join(ROOT, 'public/js/main.js');
const OUT = path.join(ROOT, 'public/assets/story-manifest.json');

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
  void close;
}

const unesc = (v) => v.replace(/\\(.)/g, '$1');
const STR = /'((?:\\.|[^'\\])*)'/;          // single-quoted literal (files use typographic ’ inside)
const ANYSTR = /'((?:\\.|[^'\\])*)'|`((?:\\.|[^`\\])*)`/;  // single-quoted or template literal

/* an expression that is either 'literal' or `cond ? 'a' : 'b'` → variants list */
function condLabels(cond) {
  const c = cond.trim();
  if (/isVesper|role\s*===\s*'vesper'/.test(c)) return ['as Vesper', 'as Lake'];
  if (/hushDone/.test(c)) return ['after the Hush', 'before the Hush'];
  if (/alive|'festival'/.test(c)) return ['before the Hush', 'after the Hush'];
  if (/state\s*===\s*'lantern'/.test(c)) return ['after the great-lantern is lit', 'while it is dark'];
  if (/lockSeen/.test(c)) return ['after the Tenant is understood', 'at first sight'];
  if (/boatDown/.test(c)) return ['after the boat is lowered', 'while it hangs shrouded'];
  if (/supperDone/.test(c)) return ['after the supper', 'before the supper'];
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

function sliceMethods(source) {             // 2-space-indented methods of the chapter object literal
  const re = /^ {2}(?:async )?([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*\{/gm;
  const marks = [];
  let m;
  while ((m = re.exec(source))) marks.push({ name: m[1], at: m.index });
  const out = {};
  for (let i = 0; i < marks.length; i++)
    out[marks[i].name] = source.slice(marks[i].at, i + 1 < marks.length ? marks[i + 1].at : source.length);
  return out;
}

/* split extracted cutscene lines into two runs at a content anchor */
function splitAt(lines, prefix, label) {
  const i = lines.findIndex(l => l[1] && l[1].startsWith(prefix));
  if (i === -1) { warn(`${label}: split anchor not found: "${prefix}"`); return [lines, []]; }
  return [lines.slice(0, i), lines.slice(i)];
}

/* ---------------- per-chapter extractor ---------------- */

function makeExtractor(file) {
  const label = path.basename(file);
  const src = fs.readFileSync(path.join(ROOT, file), 'utf8');
  const FN = sliceMethods(src);

  function fnSlice(name) {
    if (!FN[name]) warn(`function ${name}() not found in ${label}`);
    return FN[name] || '';
  }

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
    if (!lines.length) warn(`${label} cutscene ${fnName}: no dialogue extracted`);
    return lines;
  }

  /* all D([...]) / D(cond ? [...] : [...]) blocks in talkTo, in source order */
  function extractTalkBlocks() {
    const s = fnSlice('talkTo');
    const blocks = [];
    const re = /(?<![\w.])D\(/g;
    let m;
    while ((m = re.exec(s))) {
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
    }
    return blocks;
  }
  const TALK = extractTalkBlocks();
  const talkUsed = new Set();

  function talkBlock(prefix, context) {
    const idx = TALK.findIndex(b => b.lines[0] && b.lines[0][1].startsWith(prefix));
    if (idx === -1) {
      warn(`${label} talkTo block not found: "${prefix}"`);
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
      warn(`${label} Dialog.start in ${fnName} not found: "${prefix}"`);
      return { context, lines: [['system', `(missing — no Dialog.start starting “${prefix}…”)`]] };
    }
    return { context, lines: found };
  }

  /* interact() flavor, chapter-1 style: each `t.kind === 'x'` branch with its own
     Dialog.start (incl. ternary variants) */
  function extractInteract(kind, context) {
    const s = fnSlice('interact');
    const at = s.indexOf(`t.kind === '${kind}'`);
    if (at === -1) {
      warn(`${label} interact kind not found: ${kind}`);
      return { context, lines: [['system', `(missing — interact '${kind}')`]] };
    }
    const nextKind = s.indexOf('t.kind ===', at + 10);
    const region = s.slice(at, nextKind === -1 ? s.length : nextKind);
    const saved = FN.interactRegion; FN.interactRegion = region;
    const blocks = extractDialogStarts('interactRegion');
    if (saved === undefined) delete FN.interactRegion; else FN.interactRegion = saved;
    if (!blocks.length) {
      warn(`${label} interact '${kind}': no dialogue found`);
      return { context, lines: [['system', `(missing — interact '${kind}')`]] };
    }
    return { context, lines: blocks.flat() };
  }

  /* interact() flavor, chapter-2 style: branches route through the local
     `sys(text)` helper — extract each sys('…') / sys(cond ? '…' : '…') call */
  function extractInteractSys(kind, context) {
    const s = fnSlice('interact');
    const at = s.indexOf(`t.kind === '${kind}'`);
    if (at === -1) {
      warn(`${label} interact kind not found: ${kind}`);
      return { context, lines: [['system', `(missing — interact '${kind}')`]] };
    }
    const nextKind = s.indexOf('t.kind ===', at + 10);
    const region = s.slice(at, nextKind === -1 ? s.length : nextKind);
    const lines = [];
    const re = /(?<![\w.$])sys\(/g;
    let m;
    while ((m = re.exec(region))) {
      const open = m.index + m[0].length - 1;
      const end = matchBracket(region, open);
      if (end === -1) continue;
      const variants = parseExpr(region.slice(open + 1, end));
      if (variants) for (const v of variants)
        lines.push(v.label ? ['system', v.value, v.label] : ['system', v.value]);
      re.lastIndex = end;
    }
    if (!lines.length) {
      warn(`${label} interact '${kind}': no sys() dialogue found`);
      return { context, lines: [['system', `(missing — interact '${kind}')`]] };
    }
    return { context, lines };
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
    if (!lines.length) warn(`${label}: no deniedLine entries found`);
    return lines;
  }

  /* a plain string literal anywhere in a slice, matched by prefix; template
     literals are matched too, with ${…} interpolations elided */
  function findString(fnName, prefix) {
    const s = fnSlice(fnName);
    const re = new RegExp(ANYSTR.source, 'g');
    let m;
    while ((m = re.exec(s))) {
      const v = unesc(m[1] !== undefined ? m[1] : m[2]).replace(/\$\{[^}]*\}/g, '…');
      if (v.startsWith(prefix)) return v;
    }
    warn(`${label}: string not found in ${fnName}(): "${prefix}"`);
    return `(missing — “${prefix}…”)`;
  }

  return { label, FN, fnSlice, extractCutscene, TALK, talkUsed, talkBlock,
    dialogStartBlock, extractInteract, extractInteractSys, extractDeniedExits, findString };
}

const ex1 = makeExtractor('public/js/chapter1.js');
const ex2 = makeExtractor('public/js/chapter2.js');
const ex3 = makeExtractor('public/js/chapter3.js');

/* end-card text from the END_CARDS table in main.js — one entry per chapter */
function extractEndCard(idx) {
  const at = mainSrc.indexOf('const END_CARDS = [');
  if (at === -1) { warn('END_CARDS table not found in main.js'); return []; }
  const open = mainSrc.indexOf('[', at);
  const body = mainSrc.slice(open + 1, matchBracket(mainSrc, open));
  const entry = topLevelItems(body, '{')[idx];
  if (!entry) { warn(`END_CARDS: no entry ${idx}`); return []; }
  const lines = [];
  const grab = (key) => {
    const m = entry.match(new RegExp(key + ':\\s*' + STR.source));
    return m ? unesc(m[1]) : null;
  };
  const title = grab('title'), tag = grab('tag'), next = grab('next');
  if (title) lines.push(['system', title]);
  if (tag) lines.push(['system', tag]);
  const lb = entry.indexOf('lines:');
  if (lb !== -1) {
    const lo = entry.indexOf('[', lb);
    const larr = entry.slice(lo + 1, matchBracket(entry, lo));
    const re = new RegExp(STR.source, 'g');
    let lm;
    while ((lm = re.exec(larr))) lines.push(['system', unesc(lm[1])]);
  }
  lines.push(['system', '— to be continued —']);
  if (next) lines.push(['system', next]);
  if (lines.length < 3) warn(`END_CARDS entry ${idx}: too little text extracted`);
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
      [{ context: 'cutscene — Vesper’s arrival (playVesperIntro)', lines: ex1.extractCutscene('playVesperIntro') }]),

    B('The waystone & Mochi', 'entrance',
      'The waystone from drawing forty-one is real, and a cat decides something about Vesper.',
      [
        { context: 'cutscene — at the village entrance (playWaystone)', lines: ex1.extractCutscene('playWaystone') },
        ex1.extractInteract('waystone', 'looking at the waystone (flavor, by role)'),
      ]),

    B('The square — Emberwake festival', 'square',
      'Vesper meets the villagers on festival night and learns what the Kindling Hour is.',
      [
        ex1.talkBlock('A new face!', 'talking to Poppy as Vesper, pre-Hush (the telling explained)'),
        ex1.talkBlock('Pip, love, stop orbiting', 'talking to Mara & Pip as Vesper, pre-Hush'),
        ex1.talkBlock('A guest! Welcome', 'talking to Rowan as Vesper before greeting two villagers'),
        ex1.talkBlock('Now then. A guest', 'talking to Rowan as Vesper, pre-Hush (leads into Vesper’s outro)'),
        ex1.talkBlock('Mrrp.', 'talking to Mochi, pre-Hush'),
        ex1.extractInteract('notice', 'the notice board (flavor, before/after the Hush)'),
        ex1.extractInteract('heartlight', 'the Heartlight (flavor, before/after the Hush)'),
      ]),

    B('Interlude — the third honeybun', 'square',
      'Vesper waits for the lamps; the story turns to the other side of the village.',
      [{ context: 'cutscene — Vesper’s outro / Lake’s title card (playVesperOutro)', lines: ex1.extractCutscene('playVesperOutro') }]),

    B('Lake — the cottage', 'interior',
      'The last lamplighter takes down his grandmother’s flame, a year after she set it down.',
      [
        { context: 'cutscene — Lake’s introduction (playLakeIntro)', lines: ex1.extractCutscene('playLakeIntro') },
        ex1.extractInteract('hearth', 'the hearth (flavor)'),
      ]),

    B('The rounds', 'lane',
      'Three dark lamps before the Kindling Hour — and the pond has started acting strangely.',
      [
        ex1.dialogStartBlock('lightLamp', '(One.', 'lighting the first lamp'),
        ex1.dialogStartBlock('lightLamp', '(Two.', 'lighting the second lamp'),
        ex1.dialogStartBlock('lightLamp', '(Three.', 'lighting the last lamp — the ring closed'),
        ex1.talkBlock('Festival’s up in the square.', 'talking to Finn in the lane, pre-Hush (Vesper/Lake variants)'),
        ex1.talkBlock('There he is!', 'talking to Poppy as Lake, pre-Hush'),
        ex1.talkBlock('Lake! The Kindling Hour', 'talking to Rowan as Lake, pre-Hush'),
        ex1.talkBlock('He’s been up since dawn', 'talking to Mara & Pip as Lake, pre-Hush'),
        ex1.talkBlock('(Mochi is escorting', 'talking to Mochi, pre-Hush'),
        { context: 'blocked ways (denied-exit lines, shown when a road can’t be taken)',
          lines: ex1.extractDeniedExits() },
      ]),

    B('The meet', 'square',
      'The mapmaker finds the lamplighter — just as the Kindling Hour is called.',
      [{ context: 'cutscene — Vesper meets Lake (playMeet)', lines: ex1.extractCutscene('playMeet') }]),

    B('The Kindling Hour & the Hush', 'square',
      'The village brings its year to the flame — and between two heartbeats, the light leaves.',
      [{ context: 'cutscene — the festival and the catastrophe (playKindlingHour)', lines: ex1.extractCutscene('playKindlingHour') }]),

    B('Aftermath — seeing to the village', 'square',
      'Two strangers give the villagers their names back, borrowed, one by one.',
      [
        ex1.talkBlock('See to them first.', 'talking to Rowan before seeing to everyone, post-Hush'),
        ex1.talkBlock('…Why am I holding bread? Whose stall is this? Whose HANDS', 'seeing to Poppy, post-Hush'),
        ex1.talkBlock('Honeybuns. Poppy. Thumb.', 'talking to Poppy again, post-Hush (repeat)'),
        ex1.talkBlock('My name… I can say the word', 'seeing to Finn, post-Hush'),
        ex1.talkBlock('Finn. Still short.', 'talking to Finn again, post-Hush (repeat)'),
        ex1.talkBlock('Tell her. TELL her!', 'seeing to Mara & Pip, post-Hush'),
        ex1.talkBlock('I’m teaching her me again.', 'talking to Mara & Pip again, post-Hush (repeat)'),
        ex1.talkBlock('The cat. The cat is FINE?!', 'seeing to Mochi, post-Hush'),
        ex1.talkBlock('Mrrrrp.', 'talking to Mochi again, post-Hush (repeat)'),
      ]),

    B('The pact', 'square',
      'Rowan reads the fading ledger, names the Kindling, and binds two keepers to one flame.',
      [
        ex1.dialogStartBlock('playPact', 'Both of you.', 'Rowan, if only one keeper comes to him'),
        { context: 'cutscene — the pact by the Heartlight (playPact)', lines: ex1.extractCutscene('playPact') },
        ex1.talkBlock('Twin sigils, before the Gate. Two keepers', 'talking to Rowan after the pact (repeat)'),
      ]),

    B('The gate & the sigils', 'gate',
      'Two keepers stand the twin sigils together, and the Old Gate opens.',
      [{ context: 'objective & prompt text at the Old Gate', lines: [
        ['system', ex1.findString('objective', 'Stand on the twin sigils')],
        ['system', ex1.findString('promptFor', 'Stand on the sigil')],
        ['system', ex1.findString('objective', 'Step through the Old Gate')],
      ] }]),

    B('The ending — beyond the gate', 'gate',
      'The road beyond runs grey with moths, and the first lamp of the long road waits.',
      [{ context: 'cutscene — the road beyond the gate (playEnding)', lines: ex1.extractCutscene('playEnding') }]),

    B('End card', 'gate',
      'End of Chapter One.',
      [{ context: 'the end card (END_CARDS, main.js)', lines: extractEndCard(0) }]),
  ],
};

/* ---- Chapter Two — Dellhollow ---- */

const chapterTwo = {
  title: 'Chapter Two — Dellhollow',
  sub: 'a river-gorge lock-town, a nesting tenant, and the first boat',
  beats: [
    B('The descent', 'descent',
      'The road steps off the edge of the world — cut switchbacks, and the other thing.',
      [{ context: 'cutscene — the chapter open (playDescent)', lines: ex2.extractCutscene('playDescent') }]),

    B('The valley from above', 'vista',
      'The gorge in one breath: river, five locks, a painted town down both walls — a whole country not on the sheet.',
      [{ context: 'cutscene — the valley pan, spliced inside the open (playValley)', lines: ex2.extractCutscene('playValley') }]),

    B('The chart halt — map-is-wrong', 'descent',
      'The one impossible thing that finally offends Vesper is bad surveying.',
      [
        { context: 'cutscene — the chart halt (playChart)', lines: ex2.extractCutscene('playChart') },
        ex2.extractInteractSys('bracket', 'the empty lamp bracket (flavor)'),
        ex2.extractInteractSys('charthalt', 'the corrected sheet, after the beat (flavor)'),
        { context: 'objectives on the descent', lines: [
          ['system', ex2.findString('objective', 'Down the switchbacks')],
          ['system', ex2.findString('objective', 'Down — Dellhollow is not on the map')],
        ] },
      ]),

    B('The Stranger across the ravine', 'descent',
      'A figure on the far rim road bows — low, at something carried — and Mochi makes a sound he has never made.',
      [{ context: 'cutscene — the ravine (playRavine)', lines: ex2.extractCutscene('playRavine') }]),

    B('The vista', 'descent',
      'The second look, from the parapet: the town stops being geography and starts being NOISE.',
      [
        { context: 'cutscene — the rim vista (playVista)', lines: ex2.extractCutscene('playVista') },
        ex2.extractInteractSys('parapet', 'the vista parapet (flavor)'),
        { context: 'blocked ways (denied-exit lines, descent & Dellhollow)',
          lines: ex2.extractDeniedExits() },
      ]),

    B('Arrival — the stair-street', 'stairs',
      'Tar, bread, wet rope, roasting chestnuts — and nobody stares. The town happens to them from every side at once.',
      [
        { context: 'cutscene — arrival (playArrival)', lines: ex2.extractCutscene('playArrival') },
        ex2.talkBlock('Mind the drip-line, loves', 'talking to Sorrel at the bread-window, first time'),
        ex2.talkBlock('Half-loaf’s still a penny.', 'talking to Sorrel again (repeat)'),
        ex2.talkBlock('Four hundred years of stairs', 'talking to Old Creel on his step, first time'),
        ex2.talkBlock('Mind your feet going down.', 'talking to Old Creel again (repeat)'),
        ex2.talkBlock('That one’s Bailiff', 'talking to Nib, the gull officer, first time'),
        ex2.talkBlock('Soup! SOUP!', 'talking to Nib again (repeat)'),
        ex2.extractInteractSys('cistern', 'the public cistern (flavor)'),
        ex2.extractInteractSys('laundry', 'the laundry lines (flavor)'),
        ex2.extractInteractSys('gullrail', 'the gull rail (flavor)'),
        ex2.extractInteractSys('hoist', 'the barrel-hoist (flavor)'),
        ex2.extractInteractSys('cottagedoor', 'the keepers’ door (flavor, before/after supper)'),
      ]),

    B('The quay', 'dellhollow',
      'Down the stairs to the water: the quay reads the strangers before the harbormistress does.',
      [
        ex2.talkBlock('Don’t buy anything', 'talking to Captain Hobb, first time (nineteen days of pumpkins)'),
        ex2.talkBlock('You want north, I hear.', 'talking to Hobb again (repeat)'),
        ex2.talkBlock('Watchman. Night shift.', 'talking to Watchman Pell, first time (the pale-blue light)'),
        ex2.talkBlock('Sleep’s for the day shift.', 'talking to Pell again (repeat)'),
        ex2.talkBlock('(Mochi is sitting at the eel-stall', 'talking to Mochi in town'),
        ex2.extractInteractSys('queue', 'the rafted queue (flavor)'),
        ex2.extractInteractSys('barge', 'the pumpkin barge (flavor)'),
        ex2.extractInteractSys('eelstall', 'the eel-stall (flavor)'),
        ex2.extractInteractSys('notice', 'the notice board (flavor)'),
        ex2.extractInteractSys('wheels', 'the waterwheels (flavor)'),
        ex2.extractInteractSys('lamppole', 'Pell’s lamp-pole (flavor)'),
        ex2.extractInteractSys('ropebridge', 'the west rope bridge, retired to dressing (flavor)'),
        { context: 'objectives on the quay', lines: [
          ['system', ex2.findString('objective', 'Dellhollow — meet the quay')],
          ['system', ex2.findString('objective', 'The lockhead — ask the harbormistress')],
        ] },
      ]),

    B('The jam — Odessa’s ruling', 'dellhollow',
      'The river is the road, and the road is shut: the Tenant lies on the only water out of the gorge, and the town is polite to its river.',
      [
        ex2.talkBlock('Walk the quay before you spend my time', 'talking to Odessa before hearing the quay out'),
        { context: 'cutscene — the ruling at the lockhead (playJam)', lines: ex2.extractCutscene('playJam') },
        ex2.talkBlock('My ruling stands as posted. And the deep stairs', 'talking to Odessa afterwards (repeat)'),
      ]),

    B('Maren, entering wet', 'dellhollow',
      'The harbormistress’s daughter is fished out of Lock Five for the tenth time, and the tally beam says the why out loud.',
      [
        { context: 'cutscene — mother and daughter at the beam (playMarenWet)', lines: ex2.extractCutscene('playMarenWet') },
        ex2.talkBlock('Deep stairs, then.', 'talking to Maren at the stairhead'),
        ex2.extractInteractSys('tallybeam', 'the tally beam (flavor)'),
        { context: 'objective after the beam', lines: [
          ['system', ex2.findString('objective', 'Down to Lock Five')],
        ] },
      ]),

    B('Lock Five — the Tenant', 'lockfive',
      'A cathedral that works for a living, the oldest thing in the river — and a plan that needs water, a boat, and a pilot.',
      [
        { context: 'cutscene — the deep chamber (playLockFive)', lines: ex2.extractCutscene('playLockFive') },
        ex2.talkBlock('The flume goes DOWN.', 'talking to Maren after the plan is made'),
        ex2.extractInteractSys('pool', 'the flooded chamber (flavor)'),
        ex2.extractInteractSys('grate', 'the sluice-gallery grate (flavor, before/after)'),
        ex2.extractInteractSys('flume', 'the flume mouth (flavor)'),
        ex2.extractInteractSys('winch', 'the twin winches (flavor)'),
        ex2.extractInteractSys('boatlook', 'the hung boat (flavor, before/after)'),
        { context: 'objective below', lines: [
          ['system', ex2.findString('objective', 'Evening — back up to the quay')],
        ] },
      ]),

    B('Supper at the keepers’ cottage', 'cottage',
      'Odessa hosts by serving; Maren talks too much; one locked drawer sits in the middle of the table, politely orbited — and night falls with the step joke.',
      [
        { context: 'glue — the supper call at dusk (playSupperCall)', lines: ex2.extractCutscene('playSupperCall') },
        ex2.talkBlock('Door’s open. Lintel’s low', 'talking to Maren in the cottage, pre-supper'),
        ex2.talkBlock('Sit or stir, guest.', 'talking to Odessa in the cottage, pre-supper'),
        ex2.extractInteractSys('tallies', 'the height-tally doorframe (flavor)'),
        ex2.extractInteractSys('coatpeg', 'the father’s oilskin coat (flavor)'),
        ex2.extractInteractSys('drawer', 'the locked chart drawer (flavor)'),
        ex2.extractInteractSys('toolwall', 'the eel-spears and winch-parts (flavor)'),
        ex2.extractInteractSys('tableseats', 'the table and the three seats (flavor)'),
        ex2.extractInteractSys('hearthpot', 'the hearth — also the supper trigger (flavor)'),
        { context: 'cutscene — the supper, and nightfall (playSupper2)', lines: ex2.extractCutscene('playSupper2') },
        { context: 'objective at dusk', lines: [
          ['system', ex2.findString('objective', 'Supper at the keepers’ cottage')],
        ] },
      ]),

    B('Night on the quay — the dock', 'dellhollow',
      'The chapter’s quiet center: lantern-strings over the water, a honeybun changing hands, and Vesper’s whole biography, filed.',
      [
        { context: 'cutscene — the dock at night (playDockNight)', lines: ex2.extractCutscene('playDockNight') },
        ex2.talkBlock('Night shift. The proper one.', 'talking to Pell at night'),
        ex2.talkBlock('(Captain Hobb has turned in.', 'looking for Hobb at night'),
        ex2.talkBlock('(low) Stairs. Quietly.', 'talking to Maren after the dock scene'),
        ex2.talkBlock('Mrrp.', 'talking to Mochi elsewhere'),
        ex2.extractInteractSys('dockedge', 'the dock-edge bench (flavor, after)'),
        { context: 'objectives at night', lines: [
          ['system', ex2.findString('objective', 'Night on the quay')],
          ['system', ex2.findString('objective', 'Meet Maren at the deep stairs')],
        ] },
      ]),

    B('The twin winches', 'lockfive',
      'The boat comes down out of the dark; the left winch takes two; the widow-winch takes six hands — and the sixth pair arrives unhurried.',
      [{ context: 'cutscene — the winches, and Odessa’s station (playWinches)', lines: ex2.extractCutscene('playWinches') }]),

    B('The flume run', 'lockfive',
      'The held-breath glide past the watching eye, and then a mile of roaring black with Maren calling the timings.',
      [{ context: 'cutscene — the run (playFlumeRun)', lines: ex2.extractCutscene('playFlumeRun') }]),

    B('The landing — Maren joins', 'landing',
      'Dawn at the tailwater: the bag, the boat, and a dead pilot’s wrong chart set in the right hands.',
      [{ context: 'cutscene — the landing (playLanding)', lines: ex2.extractCutscene('playLanding') }]),

    B('End card', 'landing',
      'End of Chapter Two.',
      [{ context: 'the end card (END_CARDS, main.js)', lines: extractEndCard(1) }]),
  ],
};

/* ---- Chapter Three — the Lanternstead ---- */

const swarmLines = ex3.extractCutscene('playSwarm');
const [swarmA, swarmB] = splitAt(swarmLines, 'Don’t put it out — OUTSHINE it!', 'chapter3.js playSwarm');

const chapterThree = {
  title: 'Chapter Three — The Lanternstead',
  sub: 'a waystation, a friar, and the first light of the necklace',
  beats: [
    B('Cold open — the grey road', 'road',
      'Off the river at an old stone landing, onto the Order road north — grey, mossed, and measured in lamps.',
      [{ context: 'cutscene — the cold open (playRoadOpen)', lines: ex3.extractCutscene('playRoadOpen') }]),

    B('The dead lamps', 'road',
      'Lake lights three dead road-lamps and learns the road was measured in light, not miles.',
      [
        ex3.dialogStartBlock('lightLamp', '(One.', 'lighting the first road-lamp'),
        ex3.dialogStartBlock('lightLamp', '(Two.', 'lighting the second road-lamp — the mile-lamp'),
        ex3.dialogStartBlock('lightLamp', '(Three.', 'lighting the third road-lamp — the street’s taken'),
        ex3.extractInteractSys('waymarkA', 'the first waymarker (flavor, by role)'),
        ex3.extractInteractSys('waymarkB', 'the leaning waymarker (flavor)'),
        ex3.extractInteractSys('darkstretch', 'the dark stretch between lamps (flavor)'),
        ex3.talkBlock('Mrrp.', 'talking to Mochi on the road'),
        { context: 'blocked ways (denied-exit lines, road & Lanternstead)',
          lines: ex3.extractDeniedExits() },
        { context: 'objectives on the road', lines: [
          ['system', ex3.findString('objective', 'The grey road — light the road-lamps')],
          ['system', ex3.findString('objective', 'Make the Lanternstead by dusk')],
          ['system', ex3.findString('objective', 'The Lanternstead — someone is singing')],
        ] },
      ]),

    B('The Stranger on the road', 'road',
      'A pale-blue lantern, full to the glass — and a bow to the lighter, not to the men.',
      [{ context: 'cutscene — the Stranger glimpse (playStranger)', lines: ex3.extractCutscene('playStranger') }]),

    B('Arrival — Friar Tally', 'lanternstead',
      'The waystation is kept, impossibly: the Order’s last friar has the whole liturgy and never had a guest.',
      [
        { context: 'cutscene — dusk at the Lanternstead (playArrival)', lines: ex3.extractCutscene('playArrival') },
        ex3.talkBlock('Ask me anything!', 'talking to Tally, first time (the necklace explained)'),
        ex3.talkBlock('Friars keep; lighters walk.', 'talking to Tally again (the fourteenth keeper)'),
        ex3.talkBlock('Eat! Doctrine can wait an hour.', 'talking to Tally after that (repeat, on loop)'),
        ex3.talkBlock('(Mochi has inspected', 'talking to Mochi at the Lanternstead'),
        ex3.extractInteractSys('washing', 'the washing line (flavor)'),
        ex3.extractInteractSys('flags', 'the prayer flags (flavor)'),
        ex3.extractInteractSys('veg', 'the vegetable patch (flavor)'),
      ]),

    B('The well', 'lanternstead',
      'The well was cut by the Order — which is to say, the crank takes two.',
      [
        ex3.dialogStartBlock('playWell', 'The crank takes two, friend', 'Tally, if only one keeper is at the well'),
        { context: 'cutscene — drawing water together (playWell)', lines: ex3.extractCutscene('playWell') },
        ex3.extractInteractSys('well', 'the well afterwards (flavor)'),
        { context: 'objective at the well', lines: [
          ['system', ex3.findString('objective', 'Help Tally draw water')],
        ] },
      ]),

    B('Supper', 'lanternstead-int',
      'The rite pays off at the table: four places laid every night, and at last the arithmetic comes out.',
      [
        { context: 'cutscene — supper at the round table (playSupper)', lines: ex3.extractCutscene('playSupper') },
        ex3.extractInteractSys('books', 'the round room — the rite-books (flavor)'),
        ex3.extractInteractSys('hearth2', 'the round room — the hearth and the empty bracket (flavor)'),
        ex3.extractInteractSys('bed', 'the round room — the walkers’ bed (flavor)'),
        { context: 'objective at dusk', lines: [
          ['system', ex3.findString('objective', 'Supper at the Lanternstead')],
        ] },
      ]),

    B('Night — the swarm', 'lanternstead',
      'Rule one, learned the hard way: after dark on the dead road, the lighter is the only lit thing in the world.',
      [
        { context: 'cutscene — the moth swarm (playSwarm, first half)', lines: swarmA },
        { context: 'objectives at nightfall', lines: [
          ['system', ex3.findString('objective', 'Moths! — the great-lantern')],
        ] },
      ]),

    B('The great-lantern', 'lanternstead',
      'Three hundred years of polish take the flame at last — the necklace gets its first light.',
      [
        { context: 'cutscene — wick and winch, together (playSwarm, second half)', lines: swarmB },
        ex3.extractInteractSys('greatlantern', 'the great-lantern (flavor, dark / lit)'),
      ]),

    B('Morning — the letter', 'lanternstead',
      'Twenty-Two brings the first letter on the route since Tally’s teacher died — and every line of it is true.',
      [
        { context: 'cutscene — the grey post-crow and Rowan’s letter (playLetter)', lines: ex3.extractCutscene('playLetter') },
        { context: 'objective in the morning', lines: [
          ['system', ex3.findString('objective', 'Morning — see what the crow brought')],
        ] },
      ]),

    B('The wall-map — Tally joins', 'lanternstead-int',
      'The circuit, the count, and a request practiced twice: the keeping goes with the walkers.',
      [
        ex3.talkBlock('Before you walk', 'talking to Tally before the wall-map (he sends you to the round room)'),
        ex3.extractInteractSys('wallmap', 'the wall-map before the letter (flavor)'),
        { context: 'cutscene — the wall-map and the road to Harrowdel (playWallMap)', lines: ex3.extractCutscene('playWallMap') },
        { context: 'objective in the round room', lines: [
          ['system', ex3.findString('objective', 'The round room — ask Tally')],
        ] },
      ]),

    B('End card', 'lanternstead',
      'End of Chapter Three.',
      [{ context: 'the end card (END_CARDS, main.js)', lines: extractEndCard(2) }]),
  ],
};

/* unplaced talkTo blocks (new dialogue since the scaffold was written) get surfaced, not dropped */
function appendUnplaced(ex, chapter) {
  const unplaced = ex.TALK.map((b, i) => ({ b, i })).filter(x => !ex.talkUsed.has(x.i));
  if (!unplaced.length) return;
  warn(`${ex.label}: ${unplaced.length} talkTo block(s) not referenced by the scaffold — appended as an extra beat`);
  chapter.beats.push(B('Unplaced dialogue (new since scaffold)', '—',
    'talkTo blocks found in the source but not yet placed in a beat — re-check the scaffold.',
    unplaced.map(x => ({ context: `talkTo block #${x.i}` + (x.b.variant ? ` — ${x.b.variant}` : ''), lines: x.b.lines }))));
}
appendUnplaced(ex1, chapterOne);
appendUnplaced(ex2, chapterTwo);
appendUnplaced(ex3, chapterThree);

/* planned chapters — one beat each, one-liners from STORY.md §5 */
const planned = {
  title: 'Chapters 4–10 (planned)',
  sub: 'the arc of the Long Rekindling — no dialogue written yet',
  beats: [
    B('Ch. 4 — Harrowdel', 'a living valley',
      'One of the last living valleys, its elderly keeper failing; the Warden recalls Harrowdel before the party’s eyes — first face-to-face, first bow. Sable the heretic moth-catcher joins in cold fury; Marrow the ferryman — payment only in memories — is met en route, feels one for the first time in years, and poles after them: “You’ve paid me before. Long ago.”', []),
    B('Ch. 5 — Ashfield', 'the ghost town',
      'Intact, grey, silent — found off Maren’s father’s wrong chart. The double reveal: this happened before, and this is Emberbrook’s future if they fail. Vesper’s birthplace; her parents’ fog explained and exonerated in the same stroke; Lake finally says grandmother’s sayings as teaching, not grief.', []),
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

const chapters = [chapterOne, chapterTwo, chapterThree, planned];
let nBlocks = 0, nLines = 0;
for (const ch of chapters) for (const bt of ch.beats) {
  nBlocks += bt.blocks.length;
  for (const bl of bt.blocks) nLines += bl.lines.length;
}

const nSubs = bible.sections.reduce((a, s) => a + s.subs.length, 0);

const manifest = {
  generated: new Date().toISOString(),
  source: 'public/js/chapter1.js + chapter2.js + chapter3.js (+ END_CARDS in main.js, arc from STORY.md §5, bible from STORY.md)',
  stats: { blocks: nBlocks, lines: nLines,
    talkToBlocksFound: ex1.TALK.length + ex2.TALK.length + ex3.TALK.length,
    bibleSections: bible.sections.length, bibleSubs: nSubs, warnings },
  bible,
  chapters,
};

fs.writeFileSync(OUT, JSON.stringify(manifest, null, 1));
console.log(`story-manifest.json written — ${chapters.length} chapters, ` +
  `${chapterOne.beats.length} Ch.1 / ${chapterTwo.beats.length} Ch.2 / ${chapterThree.beats.length} Ch.3 beats, ` +
  `${nBlocks} blocks, ${nLines} lines, ` +
  `bible ${bible.sections.length} sections / ${nSubs} subs` +
  (warnings.length ? `, ${warnings.length} warning(s)` : ', no warnings'));
