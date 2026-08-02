#!/usr/bin/env node
// dialogue_style.mjs — THE STYLE GATE. No browser, no deps, no network.
//
//   node tools/dialogue_style.mjs            (exit 0 = green, 1 = a failure)
//   node tools/dialogue_style.mjs -v         every box, not just the bad ones
//   node tools/dialogue_style.mjs --selftest prove the sentence counter first
//   node tools/dialogue_style.mjs --scope=all  include chapter3.js (NOT gated)
//   node tools/dialogue_style.mjs --json     machine-readable dump
//
// WHY THIS FILE EXISTS. docs/VOICES.md is an excellent style guide that nothing
// checked. The user's complaint, 2026-08-02: "a script I can read happily and just
// engage with at the story level, without having to keep repeating myself about
// simple style guides." A guide nobody measures is a guide the long tail escapes:
// the measured baseline that day was 735 spoken boxes with a healthy median (13
// words) and a rotten tail — 236 boxes (32%) at three or more sentences against
// §3's "maximum two sentences per box", 29 boxes over the 25-word ceiling.
//
// So VOICES.md gets an INSTRUMENT. Every number below is quoted from the document;
// this file invents no taste of its own.
//
// SCOPE. chapter1.js, chapter2.js and ALL of public/game/dialogue.json — the Ch1+Ch2
// town content. chapter3.js is OUT (user ruling 2026-08-02: they are not happy with
// it and it must not define the house style); --scope=all measures it for information
// and never gates on it.
//
// THE CHANNELS (VOICES.md §5) — a box is judged as exactly one of:
//   spoken   a character talking, internal `(…)` lines included (§6 is the same shape)
//   system   present-tense stage direction / examine text
//   narrate  past-tense cinematic card
//
// FAIL CLASS — objective, and every threshold is VOICES.md's own number:
//   F1  sentences per box > 2                      §3 "Maximum two sentences per box"
//   F2  words > 25 spoken / > 30 system+narrate    §3 "hard ceiling ~25" / "ceiling ~30"
//   F3  more than one CAPS emphasis in a box       §8 "maximum one capped word per line"
//   F4  banned register token (whom, 'tis, …)      §4, minus the licensed registers
//   F5  inverted syntax ("never have I seen")      §4, minus the licensed registers
//   F6  Flesch-Kincaid grade > 10 on a box of      §4 "a 14-year-old should never have
//       12+ words                                       to read a line twice"
//   F7  three or more exclamation marks in a box   §4 "no exclamation-point padding"
//
// WARN CLASS — judgment calls. Reported, never gated: a heuristic that fails a build
// is a heuristic that gets written around.
//   W1  spoken box outside the 8–18 word aim band  §3
//   W2  scene exclamation density over 30%         §4
//   W3  more than 3 internal `(…)` boxes per character per scene   §6 "Ration: about three"
//   W4  more than one aphorism candidate in one scene              §2 "Budget: ONE per scene"
//   W5  an aphorism candidate from an unlicensed voice             §2 "Licensed sources only"
//       (candidate = a spoken box that addresses nobody, names nobody, counts nothing
//        and touches nothing physical — mechanically detected, hence a warning)
//   W6  a 5+ syllable word outside the lore lexicon — a hint, never a verdict  §4
//
// COUNTING SENTENCES — the part that has to be right, because the first naive count
// over-reported and would have sent a writer chasing ghosts. The rules, each with a
// hand-checked case in --selftest:
//   · '…' and '—' are NOT terminators. They are §3's cheap-and-good voice tools.
//   · a '.' inside an abbreviation (Mr., St., e.g.) or a decimal does not split.
//   · a terminator only splits when what follows opens a new box-worth of text:
//     end-of-string, or whitespace then a capital / quote / digit / dash / ellipsis.
//     `“…forever,” she said.` stays one sentence.
//   · a segment of two words or fewer with no copula or auxiliary is an INTERJECTION,
//     not a sentence: "Soup!", "Ha!", "…Ma.", "Noted." VOICES' own §9 quiz answers
//     and Nib's entry depend on this — "Soup! SOUP! …He knows his name. He just
//     doesn't respect it." is a two-sentence box with two noises in front of it.
// Everything else counts. A verbless clipped fragment of three words or more ("Two
// roads north.") IS a sentence here: it carries an idea, and §3 rations ideas.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const argv = process.argv.slice(2);
const has = (f) => argv.includes(f);
const VERBOSE = has('-v') || has('--verbose');
const SELFTEST = has('--selftest');
const JSONOUT = has('--json');
const SCOPE = (argv.find(a => a.startsWith('--scope=')) || '--scope=gate').slice(8);

/* ================= VOICES.md's numbers ================= */

const LIMIT = {
  sentences: 2,               // §3
  wordsSpoken: 25,            // §3 hard ceiling
  wordsCard: 30,              // §3 narration ceiling — system boxes share it (§5: essays banned)
  aimLo: 8, aimHi: 18,        // §3 aim band
  capsRuns: 1,                // §8
  bangs: 3,                   // §4 — three in one box is padding
  fkGrade: 10,                // §4 reading level
  fkMinWords: 12,             // below this, FK is noise
  syllHard: 5,                // a five-syllable word is a word a 14-year-old rereads
  internalPerScene: 3,        // §6 ration
  bangDensity: 0.30,          // §4, per scene
};

// §4: "no 'whom,' no ''tis,' no inverted syntax — except inside Tally's and Rowan's
// licensed registers". Tally is exempt outright (§2: over-styling IS his character);
// Rowan's tradition register is rationed, so his hits report as warnings, not failures.
const REGISTER_EXEMPT = new Set(['tally']);
const REGISTER_RATIONED = new Set(['rowan']);

const BANNED = [
  /\bwhom\b/i, /\b'tis\b/i, /\b'twas\b/i, /\bthou\b/i, /\bthee\b/i, /\bthy\b/i,
  /\bthine\b/i, /\bshalt\b/i, /\bnay\b/i, /\balas\b/i, /\bhenceforth\b/i,
  /\bwhilst\b/i, /\bamongst\b/i, /\bbetwixt\b/i, /\bperchance\b/i, /\bverily\b/i,
  /\bforsooth\b/i, /\bmayhap\b/i, /\bhereto(?:fore)?\b/i, /\bwherein\b/i,
  /\bthereupon\b/i, /\bnotwithstanding\b/i,
];
const INVERTED = [
  /\b(never|rarely|seldom|little|scarcely|hardly|no sooner|not only|nor)\s+(have|has|had|did|do|does|was|were|is|are|will|would|could|can|shall|should|may|might)\b\s+\w/i,
  /\bsuch\s+\w+\s+(was|were|is|are)\b/i,
];

// §7's lore lexicon plus the cast and the places: long words the rewrite must NOT
// strip, and proper nouns a syllable counter would otherwise punish.
const LEXICON = new Set(`
heartlight kindling emberwake emberbrook dellhollow lanternstead whisperwood harrowdel
ashfield flamebearer waykeeper lamplighter lamplighters vesper lake maren odessa rowan
poppy mochi mara pip finn tally hobb pell sorrel creel nib marrow sable renn biscuit
grandmother honeybun honeybuns harbormistress guildmother waystone waystation
lantern lanterns lantern-strings tailwater sluice gallery clinker gunwale
professional professionally professionalism cartography theodolite conviction
lamplight remember remembered remembering somebody everybody anybody everything
anything everyone somewhere everywhere apparently immediately especially exactly
absolutely reliably genuinely
`.trim().split(/\s+/));

/* ================= tiny source scanner (shared shape with build-story.mjs) ================= */

function skipString(s, i) {
  const q = s[i];
  for (let k = i + 1; k < s.length; k++) {
    if (s[k] === '\\') { k++; continue; }
    if (s[k] === q) return k;
  }
  return s.length;
}
function matchBracket(s, i) {
  let depth = 0;
  for (let k = i; k < s.length; k++) {
    const c = s[k];
    if (c === "'" || c === '"' || c === '`') { k = skipString(s, k); continue; }
    if (c === '/' && s[k + 1] === '/') { const n = s.indexOf('\n', k); if (n === -1) return -1; k = n; continue; }
    if (c === '/' && s[k + 1] === '*') { const n = s.indexOf('*/', k); if (n === -1) return -1; k = n + 1; continue; }
    if (c === '(' || c === '[' || c === '{') depth++;
    else if (c === ')' || c === ']' || c === '}') { depth--; if (depth === 0) return k; }
  }
  return -1;
}
function topLevelSplit(s) {
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
const unesc = (v) => v.replace(/\\(.)/g, '$1');
const STR = /'((?:\\.|[^'\\])*)'/;

/* an expression that is 'literal' or `cond ? 'a' : 'b'` → the string values it can take */
function exprStrings(expr) {
  const e = expr.trim().replace(/,\s*$/, '');
  let m = e.match(new RegExp('^' + STR.source + '$'));
  if (m) return [unesc(m[1])];
  m = e.match(new RegExp('^(?:.*?)\\?\\s*' + STR.source + '\\s*:\\s*' + STR.source + '\\s*$', 's'));
  if (m) return [unesc(m[1]), unesc(m[2])];
  return null;
}

/* ================= the box harvest ================= */

const DLG = JSON.parse(fs.readFileSync(path.join(ROOT, 'public/game/dialogue.json'), 'utf8'));
const SPEAKERS = new Set([...Object.keys(DLG.speakers || {}), 'tally', 'twentytwo', 'stranger', 'warden']);

const boxes = [];   // { src, scene, line, who, mood, channel, text }

function channelOf(who) {
  if (who === 'narrate') return 'narrate';
  if (who === 'system') return 'system';
  return 'spoken';
}

/* map a character offset to the enclosing 2-space-indented method name */
function fnIndex(src) {
  const re = /^ {2}(?:async )?([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*\{/gm;
  const marks = [];
  let m;
  while ((m = re.exec(src))) marks.push({ name: m[1], at: m.index });
  return (at) => {
    let name = '(top level)';
    for (const k of marks) { if (k.at <= at) name = k.name; else break; }
    return name;
  };
}

function harvestChapter(rel) {
  const src = fs.readFileSync(path.join(ROOT, rel), 'utf8');
  const label = path.basename(rel);
  const whereFn = fnIndex(src);
  const lineAt = (i) => src.slice(0, i).split('\n').length;
  const push = (at, whoRaw, text) => {
    const [who, mood] = String(whoRaw).split(':');
    if (!text || !text.trim()) return;
    // `['vesper', 'lake']` in activeRoles() is a role list, not a line: a two-string
    // array whose second element is itself a speaker id is never dialogue.
    if (SPEAKERS.has(text.trim().toLowerCase())) return;
    boxes.push({ src: label, scene: whereFn(at), line: lineAt(at),
      who, mood: mood || null, channel: channelOf(who), text });
  };

  // 1. every ['who', 'text'] pair — covers { say: … }, D([…]), deniedLine, after, patter
  for (let k = 0; k < src.length; k++) {
    const c = src[k];
    if (c === "'" || c === '"' || c === '`') { k = skipString(src, k); continue; }
    if (c === '/' && src[k + 1] === '/') { const n = src.indexOf('\n', k); if (n === -1) break; k = n; continue; }
    if (c === '/' && src[k + 1] === '*') { const n = src.indexOf('*/', k); if (n === -1) break; k = n + 1; continue; }
    if (c !== '[') continue;
    const end = matchBracket(src, k);
    if (end === -1 || end - k > 4000) continue;
    const parts = topLevelSplit(src.slice(k + 1, end));
    if (parts.length !== 2) continue;
    const whos = exprStrings(parts[0]);
    if (!whos || !whos.every(w => SPEAKERS.has(String(w).split(':')[0]))) continue;
    const texts = exprStrings(parts[1]);
    if (!texts) continue;
    const n = Math.max(whos.length, texts.length);
    for (let i = 0; i < n; i++)
      push(k, whos[Math.min(i, whos.length - 1)], texts[Math.min(i, texts.length - 1)]);
  }

  // 2. { who: …, text: … } — Dialog.start objects
  {
    const re = /\{\s*who\s*:/g;
    let m;
    while ((m = re.exec(src))) {
      const end = matchBracket(src, m.index);
      if (end === -1) continue;
      const parts = topLevelSplit(src.slice(m.index + 1, end));
      const whoPart = parts.find(p => /^who\s*:/.test(p));
      const textPart = parts.find(p => /^text\s*:/.test(p));
      if (!whoPart || !textPart) continue;
      const whos = exprStrings(whoPart.replace(/^who\s*:/, ''));
      const texts = exprStrings(textPart.replace(/^text\s*:/, ''));
      if (!whos || !texts) continue;
      const n = Math.max(whos.length, texts.length);
      for (let i = 0; i < n; i++)
        push(m.index, whos[Math.min(i, whos.length - 1)], texts[Math.min(i, texts.length - 1)]);
    }
  }

  // 3. narrate: '…' cards, sys('…') stage boxes, flavor: '…' examine text
  for (const [re, who, cut] of [
    [/\bnarrate\s*:/g, 'narrate', (s2, i) => s2.slice(i)],
    [/\bflavor\s*:/g, 'system', (s2, i) => s2.slice(i)],
  ]) {
    let m;
    while ((m = re.exec(src))) {
      const rest = cut(src, m.index + m[0].length);
      const sm = rest.match(STR);
      if (sm && rest.indexOf(sm[0]) < 8) push(m.index, who, unesc(sm[1]));
    }
  }
  {
    const re = /(?<![\w.$])sys\(/g;
    let m;
    while ((m = re.exec(src))) {
      const open = m.index + m[0].length - 1;
      const end = matchBracket(src, open);
      if (end === -1) continue;
      const vals = exprStrings(src.slice(open + 1, end));
      if (vals) for (const v of vals) push(m.index, 'system', v);
      re.lastIndex = end;
    }
  }
}

// dialogue.json and game/story.json hold the same shape of node and the same kind of
// line, and since 2026-08-02 story.json holds the CUTSCENE prose of both chapters —
// the boxes a player reads most. Measuring one and not the other would let the whole
// of Chapters One and Two drift out of VOICES.md through the file that ships them.
// Same harvester, one `src` label apart, so a failure names the file it is in.
function harvestNodeFile(DATA, src) {
  const chooser = (DATA.defaults && DATA.defaults.players && DATA.defaults.players[0]) || 'vesper';
  for (const [nodeId, node] of Object.entries(DATA.nodes || {})) {
    for (const l of node.lines || []) {
      const who = (typeof l === 'object' ? l.speaker : null) || node.speaker;
      const text = typeof l === 'object' ? l.text : l;
      if (!text || !who) continue;
      boxes.push({ src, scene: nodeId, line: 0, who,
        mood: (typeof l === 'object' ? l.expr : null) || node.expr || null,
        channel: channelOf(who), text });
    }
    // a choice is the one line of a conversation the player authors (dialogue_test §2c)
    for (const c of node.choices || [])
      if (c && c.text) boxes.push({ src, scene: nodeId, line: 0,
        who: node.chooser || chooser, mood: null, channel: 'spoken', text: c.text, isChoice: true });
  }
}

/* ================= the measurements ================= */

// the apostrophe class matters: the scripts are typeset with ’, and a straight-quote
// -only pattern silently classified "It’s bookkeeping." as a noise instead of a clause.
const COPULA = /\b(is|are|was|were|am|be|been|being|do|does|did|has|have|had|can|could|will|would|shall|should|may|might|must|ain)\b|['’](s|re|m|ve|ll|d)\b/i;
const ABBREV = /(^|[\s(“"'])(mr|mrs|ms|dr|st|ch|vs|etc|no|fig|approx|e\.g|i\.e|jr|sr)\.$/i;

/** split a box into sentence segments — see the header for every rule. */
function sentences(text) {
  const t = String(text);
  const segs = [];
  let start = 0;
  for (let i = 0; i < t.length; i++) {
    const c = t[i];
    if (c !== '.' && c !== '!' && c !== '?') continue;
    // ellipsis, in either spelling, is hesitation and not an ending
    if (c === '.' && (t[i + 1] === '.' || t[i - 1] === '.' || t[i - 1] === '…')) continue;
    if (t[i + 1] === '…') continue;
    // a decimal point
    if (c === '.' && /\d/.test(t[i - 1] || '') && /\d/.test(t[i + 1] || '')) continue;
    // an abbreviation
    if (c === '.' && ABBREV.test(t.slice(Math.max(0, i - 10), i + 1))) continue;
    // swallow a run of terminators and any closing quote/bracket
    let j = i;
    while (j + 1 < t.length && '.!?'.includes(t[j + 1])) j++;
    while (j + 1 < t.length && '”"’\')]'.includes(t[j + 1])) j++;
    const after = t.slice(j + 1);
    // it only ends a sentence if a new one can start
    if (after.length && !/^\s/.test(after)) { i = j; continue; }
    const nxt = after.replace(/^\s+/, '');
    if (nxt.length && !/^[A-Z“"'(\d—…]/.test(nxt)) { i = j; continue; }
    segs.push(t.slice(start, j + 1));
    start = j + 1;
    i = j;
  }
  if (start < t.length && t.slice(start).trim()) segs.push(t.slice(start));
  return segs.length ? segs : [t];
}

const stripTag = (text) => {
  // a leading stage tag — (quiet), (low), (loud whisper, to Lake) — is direction, not words
  const m = String(text).match(/^\s*\(([^()]{1,40})\)\s*(?=\S)/);
  return m ? String(text).slice(m[0].length) : String(text);
};
const wordsOf = (text) => stripTag(text)
  .replace(/[—–]/g, ' ')
  .split(/\s+/)
  .map(w => w.replace(/^[^\w'’]+|[^\w'’]+$/g, ''))
  .filter(Boolean);

/** an interjection: two words or fewer, carrying no copula or auxiliary.
    Measured trap: an earlier version also treated any word ending in -s/-ed/-ing as a
    verb, which made "Yes?", "Names!" and "HONEYBUNS." count as whole sentences and
    over-reported three scenes. Plural nouns are not verbs; the copula list is. */
const isInterjection = (seg) => wordsOf(seg).length <= 2 && !COPULA.test(seg);
const sentenceCount = (text) => {
  const segs = sentences(text).filter(s => s.trim());
  const real = segs.filter(s => !isInterjection(s));
  return Math.max(real.length, segs.length ? (real.length ? real.length : 1) : 1);
};

function syllables(word) {
  const w = word.toLowerCase().replace(/[^a-z]/g, '');
  if (!w) return 0;
  if (LEXICON.has(w)) return 1;
  let s = (w.replace(/e\b/, '').match(/[aeiouy]+/g) || []).length;
  if (/[^aeiou]le\b/.test(w)) s++;
  return Math.max(1, s);
}
function fkGrade(text) {
  const w = wordsOf(text);
  if (!w.length) return 0;
  const s = Math.max(1, sentenceCount(text));
  const syl = w.reduce((a, x) => a + syllables(x), 0);
  return 0.39 * (w.length / s) + 11.8 * (syl / w.length) - 15.59;
}
/** runs of consecutive ALL-CAPS words count as ONE emphasis (§8: one punch per line) */
function capsRuns(text) {
  const toks = stripTag(text).split(/[\s—–]+/);
  let runs = 0, inRun = false;
  for (const raw of toks) {
    const t = raw.replace(/^[^\w]+|[^\w]+$/g, '');
    const capped = t.length >= 2 && /^[A-Z][A-Z'’-]*$/.test(t) && /[A-Z]{2}/.test(t);
    if (capped && !inRun) { runs++; inRun = true; }
    else if (!capped) inRun = false;
  }
  return runs;
}

const isInternal = (text) => /^\s*\(.*\)\s*$/s.test(String(text));
// A SENTENTIOUS box (§2's "aphorism": a line built to be quoted) is detected purely
// mechanically — nobody addressed, nobody named, nothing counted, nothing physical.
// A line that mentions a rope or a penny or a person is doing work; a line that
// mentions none of them is a line about Meaning, and §2 rations those to one a scene.
const CONCRETE = /\b(\d+|lamp|lamps|bread|loaf|loaves|bun|buns|rope|boat|boats|river|water|road|door|doors|stair|stairs|gate|gates|fire|flame|cat|chart|map|maps|stew|coat|bag|penny|pennies|eel|eels|gull|gulls|lock|locks|winch|wick|wicks|oil|hill|well|fence|stone|beam|tally|tallies|hook|kettle|ledger|thumb|stick|bowl|pot|chain|chains|boot|boots|hand|hands|step|steps|night|nights|morning|winter|spring|dusk|rain|wind|weather|bell|window|table|chair|hearth|notebook|pen|ink|lane|pond|square|street|dock|quay|gorge|cliff|bunting|ribbon|oven|ovens|tray|tar|pitch|flood|barge|pumpkin|pumpkins|ladder|basin|drawer|key|keyhole|sheet|page|book|books|letter|crow|moth|moths|bread-window|cistern|laundry|net|nets|fish|smoke|stall|kitchen|house|village|town)\b/i;
const PERSONAL = /\b(i|me|my|mine|you|your|yours|we|us|our|ours|he|him|his|she|her|hers|they|them|their|theirs)\b/i;
const PROPER = (text) => /(?:[a-z,;:—]\s+|["“(])([A-Z][a-z]{2,})/.test(stripTag(text))
  || wordsOf(text).some(w => LEXICON.has(w.toLowerCase().replace(/[^a-z]/g, '')));
const sententious = (b) => b.channel === 'spoken' && !b.isChoice && !isInternal(b.text)
  && wordsOf(b.text).length >= 6 && !/\?/.test(b.text)
  && !PERSONAL.test(b.text) && !CONCRETE.test(b.text) && !PROPER(b.text);
// §2's licensed sources. Lake only when the line is flagged as his grandmother's.
const APHORISM_OK = new Set(['rowan', 'odessa', 'tally', 'creel']);
const licensedAphorism = (b) => APHORISM_OK.has(b.who)
  || (b.who === 'lake' && /grandmother|used to say|her rule/i.test(b.text));

/* ================= run ================= */

if (SELFTEST) {
  // hand-checked cases. VOICES.md's own lines, and the shapes that broke the naive count.
  const CASES = [
    ['Wash. Basin’s by the door.', 1],                                     // "Wash." is an interjection
    ['It’s not sad. It’s bookkeeping.', 2],
    ['Half a loaf’s a penny. The cat’s credit is good.', 2],
    ['Soup! SOUP! …He knows his name. He just doesn’t respect it.', 2],     // two noises, two sentences
    ['Noted. Filed under: things I refuse to call impossible twice in one week.', 1],
    ['That is LAW on Emberwake, ask anyone.', 1],
    ['The books say — oh, oh no, the books SAY this—', 1],                  // em-dash is not an ending
    ['(…Wait.)', 1],
    ['(Two. “Light them like you mean it,” she said, “or they gutter by midnight.”)', 1],
    ['…Ten. The point stands!', 1],                                        // "…Ten." is a count, not a clause
    ['Two roads north. The high one’s broken. So it’s the river or nothing.', 3],
    ['I’ve been down it ten times. Ma says nine. Ma is wrong, for once, and I’m counting.', 3],
    ['Mind the drip-line, loves — wash overhead, bread underhand.', 1],
    ['Da pulled it out — well, GRAND-da — one of them—', 1],
    ['Are you a REAL mapmaker? Have you been EVERYWHERE?', 2],
    ['Renn says you can SEE the memories go in. I’m staying awake to check.', 2],
    ['She died a year ago tonight. I do the rounds anyway. It’s the only part of her I get to keep doing.', 3],
    ['Sit or stir, guest. Standing in the middle of a kitchen is for weathervanes.', 2],
    ['Three lamps before dark. Pond lane first — that’s the order. It matters.', 2],
    ['Yes? The first one. Lake. The cats don’t talk, to my knowledge.', 2],
    ['HONEYBUNS. Say more words. Both of you.', 2],
    ['He’ll fall asleep mid-sentence and deny it mid-fall.', 1],
    ['Mr. Creel is on the stair.', 1],
    ['It cost 3.5 pennies.', 1],
    ['“The river is right,” she said, and went back to the winch.', 1],
    ['Mrrp.', 1],
    ['Hhhhhhhh.', 1],
  ];
  let bad = 0;
  console.log('\nsentence counter — hand-checked cases');
  for (const [text, want] of CASES) {
    const got = sentenceCount(text);
    const ok = got === want;
    if (!ok) bad++;
    console.log(`  ${ok ? 'ok  ' : 'FAIL'} ${String(got).padStart(2)} (want ${want})  ${text.slice(0, 78)}`);
  }
  // the caps counter, which has its own trap: a capped PHRASE is one punch
  const CAPS = [['FULL GATE! She’s running!', 1], ['That is LAW on Emberwake', 1],
    ['LAW, and it is LAW twice', 2], ['I ate two.', 0], ['A REAL mapmaker who has been EVERYWHERE', 2]];
  console.log('\ncaps-emphasis counter');
  for (const [text, want] of CAPS) {
    const got = capsRuns(text);
    const ok = got === want;
    if (!ok) bad++;
    console.log(`  ${ok ? 'ok  ' : 'FAIL'} ${got} (want ${want})  ${text.slice(0, 60)}`);
  }
  console.log(bad ? `\n${bad} counter case(s) FAILED\n` : '\nall counter cases green\n');
  process.exitCode = bad ? 1 : 0;
}

if (!SELFTEST) {

const CHAPTERS = SCOPE === 'all'
  ? ['public/js/chapter1.js', 'public/js/chapter2.js', 'public/js/chapter3.js']
  : ['public/js/chapter1.js', 'public/js/chapter2.js'];
for (const f of CHAPTERS) harvestChapter(f);
harvestNodeFile(DLG, 'dialogue.json');
// game/story.json is optional: a tree without the story layer still gates cleanly.
try {
  const SP = path.join(ROOT, 'public/game/story.json');
  if (fs.existsSync(SP)) harvestNodeFile(JSON.parse(fs.readFileSync(SP, 'utf8')), 'story.json');
} catch (e) { console.log('  (story.json unreadable — not measured: ' + e.message + ')'); }

const fails = [], warns = [];
const add = (list, box, code, msg) => list.push({ ...box, code, msg });

for (const b of boxes) {
  const text = b.text;
  const w = wordsOf(text);
  const n = w.length;
  const s = sentenceCount(text);
  const card = b.channel !== 'spoken';
  const cap = card ? LIMIT.wordsCard : LIMIT.wordsSpoken;
  b.words = n; b.sents = s;

  if (s > LIMIT.sentences) add(fails, b, 'F1', `${s} sentences (max ${LIMIT.sentences})`);
  if (n > cap) add(fails, b, 'F2', `${n} words (ceiling ${cap})`);

  const cr = capsRuns(text);
  if (cr > LIMIT.capsRuns) add(fails, b, 'F3', `${cr} capped emphases (max ${LIMIT.capsRuns})`);

  const exempt = REGISTER_EXEMPT.has(b.who);
  const rationed = REGISTER_RATIONED.has(b.who);
  for (const re of BANNED) {
    const m = text.match(re);
    if (!m) continue;
    if (exempt) break;
    add(rationed ? warns : fails, b, 'F4', `banned register "${m[0]}" (§4)`);
    break;
  }
  for (const re of INVERTED) {
    const m = text.match(re);
    if (!m) continue;
    if (exempt) break;
    add(rationed ? warns : fails, b, 'F5', `inverted syntax "${m[0].trim()}" (§4)`);
    break;
  }

  if (n >= LIMIT.fkMinWords) {
    const g = fkGrade(text);
    if (g > LIMIT.fkGrade) add(fails, b, 'F6', `reading grade ${g.toFixed(1)} (max ${LIMIT.fkGrade})`);
  }
  // a long word is a HINT, not a verdict: "apologizing" and "extraordinary" are five
  // syllables and no obstacle at all, so this reports and never gates.
  for (const part of w.flatMap(x => x.split(/[-–]/))) {
    const bare = part.toLowerCase().replace(/[^a-z]/g, '').replace(/s$/, '');
    if (syllables(part) >= LIMIT.syllHard && !LEXICON.has(bare) && !LEXICON.has(bare + 's'))
      { add(warns, b, 'W6', `"${part}" is a ${syllables(part)}-syllable word`); break; }
  }

  const bangs = (text.match(/!/g) || []).length;
  if (bangs >= LIMIT.bangs) add(fails, b, 'F7', `${bangs} exclamation marks`);

  if (b.channel === 'spoken' && (n < LIMIT.aimLo || n > LIMIT.aimHi))
    add(warns, b, 'W1', `${n} words (aim ${LIMIT.aimLo}–${LIMIT.aimHi})`);
  if (sententious(b) && !licensedAphorism(b))
    add(warns, b, 'W5', 'aphorism from an unlicensed voice (§2)');
}

/* per-scene checks */
const byScene = {};
for (const b of boxes) (byScene[`${b.src} · ${b.scene}`] ||= []).push(b);
for (const [scene, list] of Object.entries(byScene)) {
  const spoken = list.filter(b => b.channel === 'spoken');
  const banged = spoken.filter(b => /!/.test(b.text));
  if (spoken.length >= 8 && banged.length / spoken.length > LIMIT.bangDensity)
    warns.push({ src: list[0].src, scene: list[0].scene, line: 0, who: '—', code: 'W2',
      text: `${banged.length}/${spoken.length} spoken boxes carry an exclamation`,
      msg: `exclamation density ${(banged.length / spoken.length * 100).toFixed(0)}% (max ${LIMIT.bangDensity * 100}%)` });
  const aph = spoken.filter(sententious);
  if (aph.length > 1)
    warns.push({ src: list[0].src, scene: list[0].scene, line: aph[1].line, who: '—', code: 'W4',
      text: aph.map(x => `${x.who}: ${x.text}`).join('  ·  ').slice(0, 200),
      msg: `${aph.length} aphorism candidates in one scene (budget 1, §2)` });
  const internal = {};
  for (const b of spoken) if (isInternal(b.text)) internal[b.who] = (internal[b.who] || 0) + 1;
  for (const [who, k] of Object.entries(internal))
    if (k > LIMIT.internalPerScene)
      warns.push({ src: list[0].src, scene: list[0].scene, line: 0, who, code: 'W3',
        text: `${k} internal (…) boxes in this scene`, msg: `internal ration ${k} (about ${LIMIT.internalPerScene}, §6)` });
  void scene;
}

/* ================= report ================= */

if (JSONOUT) {
  console.log(JSON.stringify({ boxes: boxes.length, fails, warns }, null, 1));
  process.exitCode = fails.length ? 1 : 0;
}
if (!JSONOUT) {

const chan = (c) => boxes.filter(b => b.channel === c).length;
const spokenBoxes = boxes.filter(b => b.channel === 'spoken');
const median = (xs) => { const a = xs.slice().sort((x, y) => x - y); return a.length ? a[a.length >> 1] : 0; };

console.log('\nEMBERBROOK — dialogue style gate     docs/VOICES.md §2 §3 §4 §5 §6 §8');
console.log(`scope: ${CHAPTERS.map(f => path.basename(f)).join(' · ')} · public/game/dialogue.json · public/game/story.json`
  + (SCOPE === 'all' ? '   (chapter3 measured for information; it does not gate)' : ''));
console.log(`boxes: ${boxes.length}  (${chan('spoken')} spoken · ${chan('system')} system · ${chan('narrate')} narrate)`);
console.log(`spoken median: ${median(spokenBoxes.map(b => b.words))} words · ${median(spokenBoxes.map(b => b.sents))} sentences`
  + `   3+ sentences: ${spokenBoxes.filter(b => b.sents > 2).length}`
  + `   over 25 words: ${spokenBoxes.filter(b => b.words > 25).length}`);

const groupBy = (list, key) => list.reduce((a, x) => { (a[key(x)] ||= []).push(x); return a; }, {});

// per-source budget: a writer's-eye view of how much text each file is actually spending
console.log('\n  source            boxes   words   med   3+sent  >ceiling');
for (const [src, list] of Object.entries(groupBy(boxes, b => b.src))) {
  const words = list.reduce((a, b) => a + b.words, 0);
  const over = list.filter(b => b.words > (b.channel === 'spoken' ? LIMIT.wordsSpoken : LIMIT.wordsCard)).length;
  console.log(`  ${src.padEnd(16)} ${String(list.length).padStart(6)} ${String(words).padStart(7)} `
    + `${String(median(list.map(b => b.words))).padStart(5)} ${String(list.filter(b => b.sents > 2).length).padStart(7)} ${String(over).padStart(9)}`);
}
const show = (list, title, cap) => {
  if (!list.length) { console.log(`\n${title}: none`); return; }
  console.log(`\n${title} — ${list.length}`);
  console.log('\n  BY SCENE');
  const byS = groupBy(list, x => `${x.src} · ${x.scene}`);
  for (const k of Object.keys(byS).sort((a, b) => byS[b].length - byS[a].length)) {
    console.log(`    ${k}  (${byS[k].length})`);
    const rows = VERBOSE ? byS[k] : byS[k].slice(0, cap);
    for (const r of rows)
      console.log(`      ${String(r.line || '').padStart(4)}  ${r.code} ${(r.who + '').padEnd(9)} ${r.msg}`
        + `\n            “${String(r.text).replace(/\s+/g, ' ').slice(0, 96)}”`);
    if (!VERBOSE && byS[k].length > cap) console.log(`      … ${byS[k].length - cap} more`);
  }
  console.log('\n  BY CHARACTER');
  const byC = groupBy(list, x => x.who);
  for (const k of Object.keys(byC).sort((a, b) => byC[b].length - byC[a].length))
    console.log(`    ${k.padEnd(12)} ${String(byC[k].length).padStart(4)}   `
      + Object.entries(groupBy(byC[k], x => x.code)).map(([c, v]) => `${c}:${v.length}`).sort().join(' '));
  console.log('\n  BY RULE');
  const byR = groupBy(list, x => x.code);
  for (const k of Object.keys(byR).sort())
    console.log(`    ${k}  ${String(byR[k].length).padStart(4)}  ${byR[k][0].msg.replace(/^[^ ]+ /, '').slice(0, 60)}`);
};

show(fails, 'FAILURES', 6);
show(warns, 'WARNINGS (reported, not gated)', 3);

console.log(`\n${fails.length ? '✗ FAIL' : '✓ PASS'}  ${fails.length} failure(s), ${warns.length} warning(s), ${boxes.length} boxes measured\n`);
process.exitCode = fails.length ? 1 : 0;

}

}
