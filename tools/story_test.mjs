// story_test.mjs — THE SCRIPT GATE. No browser, no deps, no network.
//
//   node tools/story_test.mjs           (exit 0 = green, 1 = a failure)
//   node tools/story_test.mjs -v        (list every assertion)
//
// WHY THIS FILE EXISTS. public/game/story.json is the chapter script AS DATA:
// its own `_schema` says story_runtime.js "owns no line, no flag name, no
// coordinate and no camera id of its own — adding a beat is an edit HERE, never
// a code change." That is the right shape, and it moves every way a chapter can
// break out of the code and into a JSON file where nothing type-checks it. A
// beat that names a camera nobody baked does not throw: the trigger simply never
// matches and the cutscene never plays. A beat gated on a flag that no other
// beat writes is a chapter that can never start. Neither shows up as an error —
// both show up as a player standing in an empty square wondering what to do.
//
// So the script gets an INSTRUMENT rather than a review. Every fact a beat
// asserts about the world — the scene exists, the shot exists, the line has a
// voice, the flag has a writer — is checked against the file that owns that
// fact, off disk, in under a second.
//
// WHAT IT ASSERTS
//   1. SCHEMA      ids unique, every beat has a `do[]`, `chapter` is 1 or 2, and
//                  `once` is a boolean when stated. Chapter Three is OUT OF
//                  SCOPE by user ruling (docs/plans/end-to-end-wiring.md §3.9,
//                  "for stubbing — do not build"), so a chapter-3 beat is a
//                  FAILURE here rather than a warning: the terminal end card is
//                  a design decision and this is the thing that keeps it true.
//   2. LANDING     every beat's `scene` is a node in world/scenegraph.json and
//                  every `cam` is a shot id in that bundle's cine.json. This is
//                  the check written against the SILENT trigger: `scene` and
//                  `cam` are trigger CONDITIONS, so a typo does not error, it
//                  just makes the beat unreachable forever. A beat naming a cam
//                  in a bundle that ships no cine.json fails for the same
//                  reason — an un-baked bundle has no shot to be up.
//   3. VOICES      every {dialogue:id} step resolves — in story.json's own
//                  `nodes` or in dialogue.json's — and every line of every story
//                  node has a `speaker` in one of the two speaker tables. Plus
//                  the collision rule: story nodes are INJECTED into dialogue.js
//                  at load (`Dialogue.inject`, per story.json's `_schema`), and
//                  the shipped table is what a live conversation is holding, so
//                  a duplicated id means the node this file checked is not the
//                  node the player hears. Any collision is a failure.
//                  BUSTS AND CUT-INS ARE DELIBERATELY NOT CHECKED HERE:
//                  tools/dialogue_test.mjs §2/§2b/§2c already walks the SPEAKERS
//                  TABLE with a PNG instrument, and every speaker story.json
//                  uses is in that table, so the art coverage of the story layer
//                  is already gated there. Two gates measuring the same PNG with
//                  two thresholds is how the thresholds drift apart.
//   4. FLAG LEDGER every flag READ has a writer (FAILURE — that is an
//                  unreachable beat, a sealed exit that never opens, or a party
//                  member who never joins), and every flag WRITTEN has a reader
//                  (WARNING — dead ledger entries are how the orphan `joinFlag`
//                  happened). Readers are collected across all four files that
//                  hold conditions: story `when`, dialogue `if`, the townmaps'
//                  `sealedUntil`, and growth.json's `joinFlag`. That breadth is
//                  the whole point — a flag name is a contract BETWEEN files and
//                  no single file can see both ends of it.
//                  `npc.met.*` is exempt from the write-without-read warning:
//                  those are ambient bookkeeping written by first-meeting nodes
//                  and legitimately read by nobody.
//   5. REACHABILITY  the beats walked in file order against a growing set of
//                  flags that COULD be true. A beat whose `when` cannot be
//                  satisfied by anything written earlier is one the player can
//                  never trigger. Deliberately optimistic — `notFlag` is always
//                  satisfiable (flags start false), `hasItem`/`goldAtLeast` are
//                  not flag-gated, and anything dialogue.json can write is
//                  available from the start because an NPC can be talked to at
//                  any time. It reports ordering mistakes, not orderings it
//                  merely dislikes.
//   6. CHAPTER SPINE  the three handoff flags of end-to-end-wiring.md §6 exist
//                  and are each written EXACTLY ONCE by a beat. Once, not
//                  at-least-once: two writers means two beats each believe they
//                  end the chapter, and whichever fires second replays an end
//                  card the save already recorded. Plus growth.json's declared
//                  `maren-joined` is written by a chapter-2 beat, and the last
//                  end card is terminal.
//   7. NO TELEPORTS  the §6 invariant, as an assertion: "a beat never teleports
//                  across a scene. Movement between towns is always an edge the
//                  player takes." story.json's `_schema` says THERE IS NO
//                  TELEPORT STEP on purpose. A checker is how it stays true
//                  after the twentieth beat, when fading to a coordinate is
//                  once again the shortest way to fix a staging problem.
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const PUB = path.join(ROOT, 'public');
const VERBOSE = process.argv.includes('-v');

// The chapters this script is allowed to contain. See §1 above.
const CHAPTERS = new Set([1, 2]);
// Written-and-never-read is a warning; these are exempt from even that. See §4.
const LEDGER_EXEMPT = /^npc\.met\./;
// The §6 contract flags, verbatim from docs/plans/end-to-end-wiring.md §6.
const SPINE = ['story.ch1.gate-open', 'story.ch1.done', 'story.ch2.done'];
// Keys that would move the player between scenes from inside a `do` step. See §7.
const TELEPORT_KEYS = new Set(['teleport', 'scene', 'warp', 'goto']);

let pass = 0, fail = 0, warn = 0;
const fails = [], warns = [];
function ok(cond, what, extra) {
  if (cond) { pass++; if (VERBOSE) console.log('  ok   ' + what); return true; }
  fail++; const m = what + (extra ? '  [' + extra + ']' : '');
  fails.push(m); console.log('  FAIL ' + m); return false;
}
function note(cond, what) {
  if (cond) { pass++; if (VERBOSE) console.log('  ok   ' + what); return true; }
  warn++; warns.push(what); console.log('  warn ' + what); return false;
}
const section = t => console.log('\n' + t);
const readJSON = (rel) => JSON.parse(fs.readFileSync(path.join(PUB, rel), 'utf8'));
const has = (rel) => fs.existsSync(path.join(PUB, rel));

const S = readJSON('game/story.json');
const D = readJSON('game/dialogue.json');
const SG = readJSON('world/scenegraph.json');
const G = readJSON('game/growth.json');

const beats = Array.isArray(S.beats) ? S.beats : [];
const storyNodes = S.nodes || {};
const dlgNodes = D.nodes || {};
const speakers = Object.assign({}, D.speakers || {}, S.speakers || {});
// scenegraph.json's `nodes` is an object keyed by sceneKey; take the keys only,
// so this reads the same whichever way a future derive emits the container.
const sgNodes = new Set(Array.isArray(SG.nodes)
  ? SG.nodes.map(n => n && (n.id || n.key || n.scene)).filter(Boolean)
  : Object.keys(SG.nodes || {}));

// ---- the condition language -------------------------------------------------
// ONE language, story.json `_schema`: flag/notFlag/flagIs/flagAtLeast/hasItem/
// goldAtLeast/all/any/not. Both walkers below live here so the reader and the
// satisfiability check can never disagree about what a condition means.
// flagIs/flagAtLeast are accepted in both shapes ({name: value} and [name,
// value]) because the schema names them without pinning one.
function flagOperand(v) {
  if (Array.isArray(v)) return typeof v[0] === 'string' ? [[v[0], v[1]]] : [];
  if (v && typeof v === 'object') return Object.entries(v);
  return [];
}
function condFlags(c, out) {                       // every flag a condition READS
  if (!c || typeof c !== 'object') return out;
  if (Array.isArray(c)) { c.forEach(x => condFlags(x, out)); return out; }
  for (const [k, v] of Object.entries(c)) {
    if (k === 'flag' || k === 'notFlag') { if (typeof v === 'string') out.add(v); }
    else if (k === 'flagIs' || k === 'flagAtLeast') flagOperand(v).forEach(([f]) => out.add(f));
    else if (k === 'all' || k === 'any' || k === 'not') condFlags(v, out);
  }
  return out;
}

// ------------------------------------------------------- 1. schema
section('1. the beats are well-formed (and Chapter Three is out of scope)');
ok(beats.length > 0, `story.json ships beats to check (${beats.length})`);
const seenIds = new Set();
for (const b of beats) {
  const id = b && b.id;
  ok(typeof id === 'string' && id.length > 0, `every beat has an id`, JSON.stringify(b).slice(0, 80));
  if (typeof id !== 'string') continue;
  ok(!seenIds.has(id), `beat id "${id}" is unique`); seenIds.add(id);
  ok(Array.isArray(b.do) && b.do.length > 0, `beat "${id}" has a do[] that does something`);
  ok(CHAPTERS.has(b.chapter), `beat "${id}" is in chapter 1 or 2`,
     `chapter ${JSON.stringify(b.chapter)} — Chapter Three is out of scope ` +
     '(docs/plans/end-to-end-wiring.md §3.9)');
  if (b.once !== undefined) {
    ok(typeof b.once === 'boolean', `beat "${id}" once is a boolean`, JSON.stringify(b.once));
  }
}

// ------------------------------------------------------- 2. every beat lands somewhere real
section('2. every beat lands in a real scene, on a real shot');
const cineCache = new Map();
function shotsOf(scene) {
  if (cineCache.has(scene)) return cineCache.get(scene);
  const rel = `assets/scenes/${scene}/cine.json`;
  let v = null;                                    // null = the bundle ships no cine.json
  if (has(rel)) {
    const c = readJSON(rel);
    const cams = Array.isArray(c.cameras) ? c.cameras : Object.values(c.cameras || {});
    v = new Set(cams.map(x => (typeof x === 'string' ? x : x && x.id)).filter(Boolean));
  }
  cineCache.set(scene, v);
  return v;
}
for (const b of beats) {
  if (!b || typeof b.id !== 'string') continue;
  ok(typeof b.scene === 'string' && sgNodes.has(b.scene),
     `beat "${b.id}" scene "${b.scene}" is a scenegraph node`,
     'not in public/world/scenegraph.json nodes');
  if (!b.cam) continue;
  const shots = shotsOf(b.scene);
  if (!ok(shots !== null, `beat "${b.id}" names cam "${b.cam}" in a baked bundle`,
          `public/assets/scenes/${b.scene}/cine.json does not exist — nothing can be the shot that is up`))
    continue;
  ok(shots.has(b.cam), `beat "${b.id}" cam "${b.cam}" is a shot of ${b.scene}`,
     `cine.json shots: ${[...shots].join(', ')}`);
}

// ------------------------------------------------------- 3. every line has a voice
section('3. every line resolves to a node and a speaker');
// The collision rule first: dialogue.js holds ONE table, so a duplicate id means
// one of the two definitions is unreachable — and the unreachable one is the one
// this file just checked.
for (const nid of Object.keys(storyNodes)) {
  ok(!dlgNodes[nid], `story node "${nid}" does not collide with a dialogue.json node`,
     'dialogue.json wins at runtime, so the story version would never play');
}
const allNodes = Object.assign({}, dlgNodes, storyNodes);
for (const b of beats) {
  if (!b || !Array.isArray(b.do)) continue;
  for (const step of b.do) {
    if (!step || typeof step !== 'object' || typeof step.dialogue !== 'string') continue;
    ok(!!allNodes[step.dialogue], `beat "${b.id}" plays node "${step.dialogue}"`,
       'no such node in story.json nodes or dialogue.json nodes');
  }
}
for (const [nid, n] of Object.entries(storyNodes)) {
  const lines = n.lines || (n.text ? [n.text] : []);
  ok(lines.length > 0 || n.choices || n.next,
     `story node "${nid}" says or does something`);
  for (const l of lines) {
    const sp = (l && typeof l === 'object' && l.speaker) || n.speaker;
    if (!ok(!!sp, `story node "${nid}" line has a speaker`,
            JSON.stringify(l).slice(0, 60))) continue;
    ok(!!speakers[sp], `story node "${nid}" speaker "${sp}" is in a speakers table`,
       'not in dialogue.json speakers nor story.json speakers');
  }
}

// ------------------------------------------------------- 4. the flag ledger
section('4. the flag ledger — every read has a writer, every write has a reader');
const writers = new Map();                         // flag -> [where it is written]
const readers = new Map();                         // flag -> [where it is read]
const incTotal = new Map();                        // flag -> sum of increments (for §5)
const addTo = (m, f, where) => { if (!m.has(f)) m.set(f, []); m.get(f).push(where); };

function writesOf(o, where) {
  for (const key of ['setFlags', 'incFlags']) {
    const t = o && o[key];
    if (!t || typeof t !== 'object') continue;
    for (const [f, v] of Object.entries(t)) {
      addTo(writers, f, where);
      if (key === 'incFlags' && typeof v === 'number') {
        incTotal.set(f, (incTotal.get(f) || 0) + v);
      }
    }
  }
}
// story.json: writes live in `do` steps, reads in `when`.
for (const b of beats) {
  for (const step of b.do || []) if (step && typeof step === 'object') writesOf(step, `beat ${b.id}`);
  for (const f of condFlags(b.when, new Set())) addTo(readers, f, `beat ${b.id} when`);
}
// dialogue.json: `effects` anywhere (node level, choice level), `if` anywhere.
// Walked per node so a report names the node the author has to open.
for (const [nid, n] of Object.entries(dlgNodes)) {
  (function walk(o) {
    if (Array.isArray(o)) return o.forEach(walk);
    if (!o || typeof o !== 'object') return;
    if (o.effects) writesOf(o.effects, `dialogue node ${nid}`);
    if (o.if) for (const f of condFlags(o.if, new Set())) addTo(readers, f, `dialogue node ${nid}`);
    for (const [k, v] of Object.entries(o)) { if (k !== 'effects' && k !== 'if') walk(v); }
  })(n);
}
// the townmaps: a `sealedUntil` on an exit is a READ — the exit stays sealed
// until something writes that flag, and nothing ever will if the name is wrong.
const MAPDIR = path.join(PUB, 'townmap');
let sealedSeen = 0;
if (fs.existsSync(MAPDIR)) {
  for (const f of fs.readdirSync(MAPDIR).filter(x => x.endsWith('.map.json'))) {
    (function walk(o) {
      if (Array.isArray(o)) return o.forEach(walk);
      if (!o || typeof o !== 'object') return;
      if (typeof o.sealedUntil === 'string') {
        sealedSeen++;
        addTo(readers, o.sealedUntil, `${f} exit "${o.id || '(unnamed)'}" sealedUntil`);
      }
      for (const k in o) walk(o[k]);
    })(JSON.parse(fs.readFileSync(path.join(MAPDIR, f), 'utf8')));
  }
}
note(sealedSeen > 0, `the townmaps declare sealed exits to check (${sealedSeen})`);
// growth.json: a `joinFlag` is a READ — the party member joins when it is set.
for (const [cid, c] of Object.entries(G.characters || {})) {
  if (typeof c.joinFlag === 'string') addTo(readers, c.joinFlag, `growth.json ${cid}.joinFlag`);
}

for (const [f, where] of [...readers].sort()) {
  ok(writers.has(f), `flag "${f}" has a writer`,
     `read by ${where.join(', ')} — nothing sets it, so that gate never opens`);
}
for (const [f, where] of [...writers].sort()) {
  if (LEDGER_EXEMPT.test(f)) continue;             // ambient bookkeeping; see §4
  note(readers.has(f), `flag "${f}" is read by something (written by ${where.join(', ')})`);
}

// ------------------------------------------------------- 5. reachability
section('5. every beat can become eligible');
// Flags an NPC conversation can set are available from the start: nothing orders
// the player's walk through a town. Everything else has to be written by a beat
// EARLIER in the list than the beat that reads it.
const avail = new Set();
const availInc = new Map();
for (const [f, where] of writers) {
  if (where.some(w => w.startsWith('dialogue node'))) { avail.add(f); availInc.set(f, Infinity); }
}
function satisfiable(c, unmet) {
  if (!c || typeof c !== 'object') return true;
  if (Array.isArray(c)) return c.every(x => satisfiable(x, unmet));
  let out = true;
  for (const [k, v] of Object.entries(c)) {
    if (k === 'flag') {
      // npc.met.* is satisfiable by definition: the player can always go and
      // meet somebody. Anything else needs a writer that has already run.
      if (!(LEDGER_EXEMPT.test(v) || avail.has(v))) { unmet.push(v); out = false; }
    } else if (k === 'notFlag') {                  // flags start false
    } else if (k === 'flagIs') {
      for (const [f] of flagOperand(v)) if (!avail.has(f)) { unmet.push(f); out = false; }
    } else if (k === 'flagAtLeast') {
      for (const [f, n] of flagOperand(v)) {
        const got = availInc.has(f) ? availInc.get(f) : (avail.has(f) ? Infinity : 0);
        if (!(got >= (typeof n === 'number' ? n : 1))) {
          unmet.push(`${f} >= ${n} (earlier beats can reach ${got === Infinity ? 'any' : got})`);
          out = false;
        }
      }
    } else if (k === 'all') { if (!satisfiable(v, unmet)) out = false; }
    else if (k === 'any') {
      const sub = [];
      const list = Array.isArray(v) ? v : [v];
      if (!list.some(x => satisfiable(x, sub))) { unmet.push(...sub); out = false; }
    } else if (k === 'not') {                      // a negation of a false flag: satisfiable
    }
    // hasItem / goldAtLeast are not flag-gated and are always reachable.
  }
  return out;
}
for (const b of beats) {
  const unmet = [];
  ok(satisfiable(b.when, unmet), `beat "${b.id}" can become eligible`,
     unmet.length ? 'never satisfiable: ' + [...new Set(unmet)].join(', ') : '');
  for (const step of b.do || []) {
    if (!step || typeof step !== 'object') continue;
    for (const f of Object.keys(step.setFlags || {})) { avail.add(f); availInc.set(f, Infinity); }
    for (const [f, v] of Object.entries(step.incFlags || {})) {
      avail.add(f);
      availInc.set(f, (availInc.get(f) || 0) + (typeof v === 'number' ? v : 1));
    }
  }
}

// ------------------------------------------------------- 6. the chapter spine
section('6. the chapter spine (end-to-end-wiring.md §6)');
const beatWriters = (f) => (writers.get(f) || []).filter(w => w.startsWith('beat '));
for (const f of SPINE) {
  const w = beatWriters(f);
  ok(w.length === 1, `contract flag "${f}" is written by exactly one beat`,
     w.length ? w.join(', ') : 'no beat writes it — the handoff never happens');
}
const beatById = new Map(beats.map(b => [b.id, b]));
for (const [cid, c] of Object.entries(G.characters || {})) {
  if (typeof c.joinFlag !== 'string') continue;
  const w = beatWriters(c.joinFlag).map(s => s.slice(5));
  if (c.joinFlag === 'maren-joined') {
    ok(w.some(id => (beatById.get(id) || {}).chapter === 2),
       `growth.json ${cid}.joinFlag "${c.joinFlag}" is written by a chapter-2 beat`,
       w.length ? 'written by ' + w.join(', ') : 'no beat writes it');
  } else {
    note(w.length > 0, `growth.json ${cid}.joinFlag "${c.joinFlag}" is written by a beat`);
  }
}
// The last end card is terminal. Two halves: nothing anywhere reaches for
// Chapter Three, and nothing runs after the final card that would raise the
// chapter. Only STRUCTURAL fields are scanned (flag names, dialogue ids, the
// chapter step) — prose is allowed to mention whatever the writer likes.
const CH3 = /(^|\.)ch(apter)?3(\.|$)/i;
let lastCard = -1;
beats.forEach((b, i) => { if ((b.do || []).some(s => s && s.endCard !== undefined)) lastCard = i; });
ok(lastCard >= 0, 'the script ends on an end card');
beats.forEach((b, i) => {
  for (const step of b.do || []) {
    if (!step || typeof step !== 'object') continue;
    if (typeof step.chapter === 'number') {
      ok(step.chapter <= 2, `beat "${b.id}" does not label a chapter past two`, `chapter ${step.chapter}`);
      ok(i <= lastCard, `beat "${b.id}" does not raise the chapter after the final end card`);
    }
    const names = [
      ...Object.keys(step.setFlags || {}), ...Object.keys(step.incFlags || {}),
      typeof step.dialogue === 'string' ? step.dialogue : null,
    ].filter(Boolean);
    for (const n of names) {
      ok(!CH3.test(n), `beat "${b.id}" does not reference chapter three ("${n}")`,
         'Chapter Three is out of scope — the Ch2 end card is terminal');
    }
  }
});

// ------------------------------------------------------- 7. no teleports
section('7. no beat moves the player across a scene');
for (const b of beats) {
  for (const step of b.do || []) {
    if (!step || typeof step !== 'object') continue;
    for (const k of Object.keys(step)) {
      ok(!TELEPORT_KEYS.has(k), `beat "${b.id}" step has no "${k}"`,
         'the corridor between towns is WALKED (end-to-end-wiring.md §6 invariant; ' +
         'story.json _schema: "THERE IS NO TELEPORT STEP, on purpose")');
    }
  }
}

// ------------------------------------------------------- report
console.log('\n' + '-'.repeat(64));
console.log(`${pass} passed, ${fail} failed, ${warn} warnings`);
if (warn) { console.log('\nwarnings (not failures):'); warns.forEach(w => console.log('  · ' + w)); }
if (fail) { console.log('\nFAILURES:'); fails.forEach(f => console.log('  · ' + f)); process.exit(1); }
console.log('green — every beat lands, every line has a voice, every flag has both ends.');
