// dialogue_test.mjs — THE CAST GATE. No browser, no deps, no network.
//
//   node tools/dialogue_test.mjs          (exit 0 = green, 1 = a failure)
//   node tools/dialogue_test.mjs -v       (list every assertion)
//
// WHY THIS FILE EXISTS. The user played on 2026-08-01 and ruled two things about
// the people of the towns: every one of them wears a 3D body, and "every time you
// speak to somebody, they should have an appropriate character bust". Both are
// DATA facts — a line of public/game/npcs.json, a line of dialogue.json — and both
// fail SILENTLY at runtime. dialogue.js is written to keep talking when the art is
// missing (`portrait:false` means nameplate-only, and that is a real contract for
// the narrator channel), so a villager who lost his bust in an edit does not throw,
// does not warn, and does not look broken until somebody walks up to him in a
// build. npc.js is the same: a body.src that 404s pushes the id onto `missing`,
// logs one line, and leaves a blob shadow standing in the street.
//
// So the ruling gets an INSTRUMENT rather than a note. A speaker with no bust on
// disk is a FAILING BUILD here, not a blank frame in front of the player.
//
// WHAT IT ASSERTS
//   1. INTEGRITY   every node's `speaker` (node-level and per-line) is in the
//                  speakers table; every npcs.json `dialogue` id resolves to a
//                  node; every node's `next`/`else`/choice `to` resolves.
//   2. BUSTS       every speaker resolves to a portrait id and that id has a real
//                  public/assets/characters/<id>/bust.png. EXACTLY ONE id may opt
//                  out — `system`, the narrator channel, which is a typographic
//                  mark and not a person. Any other `portrait:false` is a failure,
//                  and so is a portrait id pointing at art nobody drew.
//   2b. CUT-INS   the 2026-08-01 follow-on ruling: the portrait is an alpha cutout
//                  rising out of the box, with the framed thumbnail as the
//                  migration fallback. So the gate is EVERY SPEAKER RESOLVES TO
//                  CUT-IN OR THUMBNAIL, NEVER BLANK — and a cut-in that exists is
//                  a real one, MEASURED IN THE PNG rather than trusted from the
//                  manifest that made it: 8-bit RGBA, at least 600 px tall, and an
//                  alpha channel that is actually doing work (a matte that keyed
//                  nothing comes back fully opaque and looks fine in a file
//                  listing). The manifest is checked AGAINST the files in both
//                  directions, because it is what dialogue.js decides from: an
//                  entry with no art is a 404 in the player's face, and art with no
//                  entry is money spent on something the runtime will never show.
//   2c. PLAYER BEATS  the 2026-08-01 amendment: the party (dialogue.json's
//                  `defaults.players`, Vesper and Lake) must have a face on every
//                  beat THE PLAYER speaks, and a choice list is such a beat — it is
//                  the one line of a conversation the player authors. Before the
//                  ruling it wore whichever NPC had spoken last, which reads as the
//                  NPC asking themselves the question. So: every node that offers
//                  choices resolves its CHOOSER (node `chooser`, else players[0]) to
//                  real art, every player-spoken line resolves to real art, and each
//                  member of the party has a cut-in rather than only a thumbnail —
//                  they are the most-seen faces in the game. All three are FAILURES,
//                  the same class as a bustless NPC, and they are here rather than
//                  folded into §2 because §2 walks the SPEAKERS TABLE and a chooser
//                  is never in it: nothing marks that node as having a voice.
//   3. EXPRESSIONS every `expr` a line asks for exists as expr-<mood>.png. This one
//                  is a WARNING, not a failure, and deliberately: dialogue.js falls
//                  back to the neutral bust by design so a mood can be written
//                  before it is drawn (its own header says so). The warning exists
//                  to make the fallback VISIBLE instead of invisible.
//   4. BODIES      every npcs.json record's body.src exists on disk, and every
//                  record is body.type 'model' — with one allow-list, THE CATS.
//                  There is no quadruped GLB; a biped scaled to 0.30 charH is a
//                  tiny person, not a cat. The allow-list is two ids long and any
//                  THIRD billboard is a regression against the ruling.
//   5. POSTS       ids unique, positions present and numeric, a scene named,
//                  facing in range, and no two people standing within 0.9 m of
//                  each other in the same scene (a post nobody can tell from
//                  another post is not a post).
//   6. ARRIVALS    NOBODY STANDS WHERE THE PLAYER MATERIALISES. Every arrival in
//                  public/world/scenegraph.json carries a `spawn` — doors, seams
//                  AND camera cuts — and a villager posted on one is a body the
//                  player appears inside. Measured MINUS the wander radius,
//                  because clearance has to survive the errand and not just the
//                  post. This is npcs.json's `_posts` note as an instrument, and
//                  it is here because the mistake is attractive rather than
//                  careless: three of the five villagers added on 2026-08-01 were
//                  authored 0.09 / 0.39 / 0.43 m from a spawn, every one of them
//                  for a GOOD reason — a cut point and a doorstep are the legible,
//                  well-composed places a person belongs, which is exactly why the
//                  camera layer already claimed them.
import fs from 'fs';
import path from 'path';
import zlib from 'zlib';
import { fileURLToPath } from 'url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const PUB = path.join(ROOT, 'public');
const VERBOSE = process.argv.includes('-v');

// The one speaker allowed to have no face, and the reason, in the file that
// enforces it. `system` is the narrator: dialogue.json gives it the name "✦".
const NAMEPLATE_ONLY = new Set(['system']);
// The one body allowed to stay a plate, and the reason. See §4 above.
const BILLBOARD_OK = new Set(['mochi', 'mochi-emb']);

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
const exists = p => fs.existsSync(path.join(PUB, p));

const D = JSON.parse(fs.readFileSync(path.join(PUB, 'game/dialogue.json'), 'utf8'));
const N = JSON.parse(fs.readFileSync(path.join(PUB, 'game/npcs.json'), 'utf8'));
const speakers = D.speakers || {};
const nodes = D.nodes || {};
const people = N.npcs || [];

// dialogue.js's own resolution rule, reproduced exactly (dialogue.js speaker()):
// an ABSENT portrait defaults to the speaker id; `false`/null is nameplate-only.
const portraitOf = (id) => {
  const s = speakers[id];
  return s && s.portrait !== undefined ? s.portrait : id;
};
const bustPath = (pid) => 'assets/characters/' + pid + '/bust.png';
const cutinPath = (pid, mood) =>
  'assets/characters/' + pid + '/cutin' + (mood ? '-' + mood : '') + '.png';

// ---- the PNG instrument -----------------------------------------------------
// MEASURE THE ARTIFACT, NOT THE LOG. gen-cutin.py records what it thinks it made;
// this reads what is on disk. No dependency: a PNG's IHDR is at a fixed offset,
// and zlib is in node, so unfiltering the scanlines to reach the alpha channel is
// forty lines. Returns null for anything that is not the 8-bit non-interlaced
// RGBA the matter writes, which is itself the failure the caller reports.
function pngAlpha(abs) {
  const buf = fs.readFileSync(abs);
  if (buf.length < 33 || buf.readUInt32BE(0) !== 0x89504e47) return null;
  const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20);
  const depth = buf[24], color = buf[25], interlace = buf[28];
  const out = { w, h, depth, color, interlace, clear: 0, opaque: 0 };
  if (depth !== 8 || color !== 6 || interlace !== 0) return out;   // no alpha to read

  const idat = [];
  for (let p = 8; p + 8 <= buf.length;) {
    const len = buf.readUInt32BE(p), tag = buf.toString('latin1', p + 4, p + 8);
    if (tag === 'IDAT') idat.push(buf.subarray(p + 8, p + 8 + len));
    if (tag === 'IEND') break;
    p += 12 + len;
  }
  const raw = zlib.inflateSync(Buffer.concat(idat));
  const bpp = 4, stride = w * bpp;
  let prev = Buffer.alloc(stride), cur = Buffer.alloc(stride), off = 0;
  for (let y = 0; y < h; y++) {
    const f = raw[off++];
    raw.copy(cur, 0, off, off + stride); off += stride;
    for (let i = 0; i < stride; i++) {
      const a = i >= bpp ? cur[i - bpp] : 0, b = prev[i], c = i >= bpp ? prev[i - bpp] : 0;
      let v = cur[i];
      if (f === 1) v += a;
      else if (f === 2) v += b;
      else if (f === 3) v += (a + b) >> 1;
      else if (f === 4) {                                   // Paeth
        const pp = a + b - c, pa = Math.abs(pp - a), pb = Math.abs(pp - b), pc = Math.abs(pp - c);
        v += (pa <= pb && pa <= pc) ? a : (pb <= pc ? b : c);
      }
      cur[i] = v & 255;
    }
    for (let x = 3; x < stride; x += bpp) {
      if (cur[x] < 8) out.clear++; else if (cur[x] > 247) out.opaque++;
    }
    const t = prev; prev = cur; cur = t;
  }
  const n = w * h;
  out.clearF = out.clear / n;
  out.opaqueF = out.opaque / n;
  return out;
}

// A cut-in that keyed nothing is fully opaque; one that ate the character is
// fully clear. Both look like a valid PNG and neither looks like a portrait.
const MIN_CUTIN_H = 600, MIN_CLEAR = 0.06, MIN_OPAQUE = 0.12;
function checkCutin(rel, label) {
  const abs = path.join(PUB, rel);
  if (!ok(fs.existsSync(abs), `${label} art is on disk`, 'missing public/' + rel)) return;
  const m = pngAlpha(abs);
  if (!ok(m && m.depth === 8 && m.color === 6 && m.interlace === 0,
          `${label} is 8-bit RGBA with an alpha channel`,
          m ? `depth ${m.depth}, colour type ${m.color}, interlace ${m.interlace}` : 'unreadable PNG'))
    return;
  ok(m.h >= MIN_CUTIN_H, `${label} is at least ${MIN_CUTIN_H}px tall`, m.w + 'x' + m.h);
  ok(m.clearF >= MIN_CLEAR && m.opaqueF >= MIN_OPAQUE,
     `${label} alpha is a real cutout`,
     `${(m.clearF * 100).toFixed(1)}% clear / ${(m.opaqueF * 100).toFixed(1)}% opaque ` +
     `(need >=${MIN_CLEAR * 100}% / >=${MIN_OPAQUE * 100}%)`);
  return m;
}

// ------------------------------------------------------- 1. integrity
section('1. every speaker and every jump resolves');
const used = new Set();
for (const [nid, n] of Object.entries(nodes)) {
  if (n.speaker) used.add(n.speaker);
  const src = n.lines || (n.text ? [n.text] : []);
  for (const l of src) if (l && typeof l === 'object' && l.speaker) used.add(l.speaker);
  for (const key of ['next', 'else']) {
    if (n[key]) ok(!!nodes[n[key]], `node "${nid}".${key} -> "${n[key]}" exists`);
  }
  for (const c of n.choices || []) {
    if (c.to) ok(!!nodes[c.to], `node "${nid}" choice "${c.text}" -> "${c.to}" exists`);
  }
  // A node with neither lines, choices nor next is a dead end the player walks
  // into and out of with nothing shown.
  ok((src.length || (n.choices || []).length || n.next || n['else']),
     `node "${nid}" says or does something`);
}
for (const s of used) ok(!!speakers[s], `speaker "${s}" is in the speakers table`);
for (const s of Object.keys(speakers)) {
  note(used.has(s), `speaker "${s}" is used by at least one node`);
}
for (const p of people) {
  if (p.dialogue) ok(!!nodes[p.dialogue], `npc "${p.id}" dialogue "${p.dialogue}" exists`);
}

/* THE PROMPT IS A SENTENCE, AND NOBODY HAD EVER READ IT (PT-20260804-015).
 * `promptLabel` is a template and `name` is a string, and the two are only ever seen
 * joined — on the interaction banner, in the player's face. del.cook carried
 * "Talk to the {name}" over the name "the cook" and shipped **"Talk to the the cook?"**
 * with every gate green, because no gate had ever EXPANDED the template. Expand it and
 * read the result: a doubled article, a doubled space, or an empty slot is a defect a
 * player sees on the first press of E. */
section('1b. every interaction prompt reads as a sentence');
const DEFPROMPT = (N.defaults && N.defaults.promptLabel) || 'Talk to {name}';
for (const p of people) {
  if (!p.name) continue;
  const label = String(p.promptLabel || DEFPROMPT).replace(/\{name\}/g, p.name);
  ok(!/\b(the|a|an|to|of)\s+\1\b/i.test(label), `npc "${p.id}" prompt has no doubled word`, label);
  ok(!/\s{2}|\{|\}/.test(label), `npc "${p.id}" prompt has no stray spacing or slot`, label);
}

// ------------------------------------------------------- 2. THE BUST GATE
section('2. every speaker has a bust (the 2026-08-01 ruling)');
for (const [id, s] of Object.entries(speakers)) {
  const pid = portraitOf(id);
  if (!pid) {
    ok(NAMEPLATE_ONLY.has(id),
       `speaker "${id}" (${s.name}) has a bust`,
       'portrait is false and "' + id + '" is not the narrator channel — give it a bust ' +
       '(tools/gen-character.mjs <id> --only key,bust) or map it to an archetype');
    continue;
  }
  ok(exists(bustPath(pid)),
     `speaker "${id}" (${s.name}) -> ${pid}/bust.png`,
     'missing public/' + bustPath(pid));
}
// And the reverse direction: an npc who talks must reach a speaker with a face.
for (const p of people) {
  const n = p.dialogue && nodes[p.dialogue];
  if (!n) continue;
  const first = n.speaker || ((n.lines || []).find(l => l && l.speaker) || {}).speaker;
  if (!first) continue;
  const pid = portraitOf(first);
  ok(!!pid || NAMEPLATE_ONLY.has(first), `npc "${p.id}" opens on a speaker with a face`,
     'speaker "' + first + '" is nameplate-only');
}

// ------------------------------------------------- 2b. THE CUT-IN GATE
section('2b. every speaker resolves to a cut-in or a thumbnail (the cut-in ruling)');
const MANIFEST = 'assets/characters/cutins.json';
let CUT = {};
if (!fs.existsSync(path.join(PUB, MANIFEST))) {
  // Not a failure: no manifest is the pre-migration state, and dialogue.js is
  // written to draw the old framed thumbnail for everybody in exactly that case.
  note(false, `public/${MANIFEST} is absent — every speaker falls back to the thumbnail`);
} else {
  CUT = JSON.parse(fs.readFileSync(path.join(PUB, MANIFEST), 'utf8'));
  ok(Object.keys(CUT).length > 0, `${MANIFEST} lists cut-ins (${Object.keys(CUT).length})`);
  for (const [pid, e] of Object.entries(CUT)) {
    const m = checkCutin(cutinPath(pid), `cut-in "${pid}"`);
    // dialogue.js sizes the element from w/h BEFORE the image loads, so a wrong
    // aspect here is a portrait that jumps size on its own first paint.
    if (m && e.w && e.h) {
      ok(m.w === e.w && m.h === e.h, `cut-in "${pid}" manifest size matches the file`,
         `manifest ${e.w}x${e.h}, file ${m.w}x${m.h}`);
    }
    for (const mood of e.expr || []) checkCutin(cutinPath(pid, mood), `cut-in "${pid}" mood "${mood}"`);
  }
  // The other direction: art the runtime will never reach, because dialogue.js
  // asks the manifest and not the disk.
  const CHDIR = path.join(PUB, 'assets/characters');
  for (const d of fs.readdirSync(CHDIR)) {
    if (!fs.existsSync(path.join(CHDIR, d, 'cutin.png'))) continue;
    note(!!CUT[d], `cut-in art for "${d}" is listed in the manifest`);
  }
}
// THE RULING ITSELF. Two states are allowed and a third is not.
for (const [id, s] of Object.entries(speakers)) {
  const pid = portraitOf(id);
  if (!pid) continue;                                   // §2 already ruled on these
  const shape = CUT[pid] ? 'cut-in' : (exists(bustPath(pid)) ? 'thumbnail' : null);
  ok(!!shape, `speaker "${id}" (${s.name}) draws something — ${shape || 'NOTHING'}`,
     `portrait "${pid}" has neither a manifest cut-in nor a bust.png`);
}

// -------------------------------------------- 2c. THE PLAYER-BEAT GATE
section('2c. the player has a face on every beat the player speaks');
const PLAYERS = (D.defaults && Array.isArray(D.defaults.players) && D.defaults.players.length)
  ? D.defaults.players : ['vesper', 'lake'];
// dialogue.js's own rule, reproduced: art exists if the manifest lists a cut-in or
// a bust.png is on disk. Anything else draws nothing.
const drawsSomething = (pid) => !!pid && (!!CUT[pid] || exists(bustPath(pid)));

ok(PLAYERS.length > 0, 'the data names a party (defaults.players)');
for (const id of PLAYERS) {
  ok(!!speakers[id], `party member "${id}" is in the speakers table`);
  const pid = portraitOf(id);
  ok(drawsSomething(pid), `party member "${id}" draws something`,
     `portrait "${pid}" has neither a manifest cut-in nor a bust.png`);
  // Stronger than the cast bar, and deliberately: these two are on screen more
  // than anyone, and the thumbnail is the MIGRATION fallback, not a destination.
  ok(!!CUT[pid], `party member "${id}" has cut-in art, not just a thumbnail`,
     'only a framed bust — run tools/gen-cutin-art.mjs ' + pid + ' then tools/gen-cutin.py ' + pid);
}
// Every choice list is a player beat. The chooser is never named in the speakers
// table, so nothing else in this file would ever look at it.
let choiceNodes = 0;
for (const [nid, n] of Object.entries(nodes)) {
  const ch = (n.choices || []);
  if (!ch.length) continue;
  choiceNodes++;
  const chooser = n.chooser || PLAYERS[0];
  ok(!!speakers[chooser], `node "${nid}" chooser "${chooser}" is a known speaker`);
  const pid = portraitOf(chooser);
  ok(drawsSomething(pid), `node "${nid}" choice list has a portrait (${chooser})`,
     `chooser "${chooser}" -> portrait "${pid}" draws NOTHING`);
  if (n.chooserExpr) {
    note(!!(CUT[pid] && (CUT[pid].expr || []).includes(n.chooserExpr)),
         `node "${nid}" chooserExpr "${n.chooserExpr}" has cut-in art for ${pid}`);
  }
}
ok(choiceNodes > 0, `the script has choice lists to measure (${choiceNodes})`);
// And the other direction: a line SPOKEN by a party member must draw too.
for (const [nid, n] of Object.entries(nodes)) {
  for (const l of n.lines || []) {
    const sp = (l && typeof l === 'object' && l.speaker) || n.speaker;
    if (!PLAYERS.includes(sp)) continue;
    ok(drawsSomething(portraitOf(sp)), `node "${nid}" player line (${sp}) draws something`);
    break;                                   // one assertion per node is enough
  }
}

// ------------------------------------------------------- 3. expressions
section('3. expression plates a line asks for (warn: dialogue.js falls back)');
for (const [nid, n] of Object.entries(nodes)) {
  const src = n.lines || [];
  for (const l of src) {
    const e = (l && typeof l === 'object' && l.expr) || n.expr;
    if (!e) continue;
    const sp = (l && typeof l === 'object' && l.speaker) || n.speaker;
    const pid = portraitOf(sp);
    if (!pid) continue;
    note(exists('assets/characters/' + pid + '/expr-' + e + '.png'),
         `node "${nid}" expr "${e}" for ${pid}`);
  }
}

// ------------------------------------------------------- 4. THE BODY GATE
section('4. every person is a body (the same ruling, other half)');
for (const p of people) {
  const b = p.body || {};
  ok(!!b.src, `npc "${p.id}" has a body.src`);
  if (b.src) ok(exists(b.src), `npc "${p.id}" body ${b.src} is on disk`);
  if (b.plate) ok(exists(b.plate), `npc "${p.id}" body.plate ${b.plate} is on disk`);
  if (b.type !== 'model') {
    ok(BILLBOARD_OK.has(p.id), `npc "${p.id}" is a 3D model`,
       'billboard body — the ruling allows only ' + [...BILLBOARD_OK].join(', ') +
       ' (no quadruped GLB exists)');
  }
}

// ------------------------------------------------------- 5. posts
section('5. the posts themselves');
const seen = new Set();
for (const p of people) {
  ok(!seen.has(p.id), `npc id "${p.id}" is unique`); seen.add(p.id);
  ok(!!p.scene, `npc "${p.id}" names a scene`);
  const q = p.position;
  ok(Array.isArray(q) && q.length === 3 && q.every(v => typeof v === 'number' && isFinite(v)),
     `npc "${p.id}" has a numeric [x,y,z] position`);
  if (p.facing !== undefined) {
    ok(typeof p.facing === 'number' && p.facing >= 0 && p.facing < 360,
       `npc "${p.id}" facing ${p.facing} is a yaw in [0,360)`);
  }
}
// Two people closer than this in the same scene are one silhouette from any
// camera that is not standing between them.
const MIN_GAP = 0.9;
const scenesOf = (p) => (Array.isArray(p.scene) ? p.scene : [p.scene]);
for (let i = 0; i < people.length; i++) {
  for (let j = i + 1; j < people.length; j++) {
    const a = people[i], b = people[j];
    if (!scenesOf(a).some(s => scenesOf(b).includes(s))) continue;
    const d = Math.hypot(a.position[0] - b.position[0],
                         a.position[1] - b.position[1],
                         a.position[2] - b.position[2]);
    ok(d >= MIN_GAP, `"${a.id}" and "${b.id}" stand ${MIN_GAP} m apart`, d.toFixed(2) + ' m');
  }
}

// ------------------------------------------------------- 6. THE ARRIVAL GATE
section('6. nobody stands where the player materialises');
const SGPATH = path.join(PUB, 'world/scenegraph.json');
if (!fs.existsSync(SGPATH)) {
  note(false, 'public/world/scenegraph.json is absent — arrival clearance UNCHECKED');
} else {
  // Every object anywhere in the graph that carries both a `spawn` point and the
  // scene it lands in. Collected structurally rather than from a known shape:
  // doors, seams and cuts are all different node kinds and all of them spawn.
  // TWO KINDS OF CLAIMED GROUND, and the second was learned the hard way an hour
  // after the first: moving the deckhand off a cut spawn put him 0.32 m INSIDE the
  // chandlery's door trigger, which is the same mistake one layer over. A `spawn`
  // is where the player APPEARS; an `at`+`r` is a trigger circle the player stands
  // in to take the door. A villager may not own either.
  const spawns = [], triggers = [];
  (function collect(o) {
    if (Array.isArray(o)) return o.forEach(collect);
    if (!o || typeof o !== 'object') return;
    if (Array.isArray(o.spawn) && o.spawn.length === 3 && typeof o.to === 'string')
      spawns.push({ id: o.id || '(unnamed)', to: o.to, at: o.spawn });
    if (Array.isArray(o.at) && o.at.length === 3 && typeof o.to === 'string' && typeof o.r === 'number')
      triggers.push({ id: o.id || '(unnamed)', from: o.from, at: o.at, r: o.r });
    for (const k in o) collect(o[k]);
  })(JSON.parse(fs.readFileSync(SGPATH, 'utf8')));
  ok(spawns.length > 0, `scenegraph offers arrival spawns to measure against (${spawns.length})`);
  ok(triggers.length > 0, `scenegraph offers door/seam triggers to measure against (${triggers.length})`);
  // 1.0 m: a body is ~0.5 m wide and the player is another ~0.5 m. Below this
  // they are interpenetrating on arrival, which is what this gate exists to stop.
  const MIN_ARRIVAL = 1.0;
  for (const p of people) {
    const scn = Array.isArray(p.scene) ? p.scene : [p.scene];
    const wander = p.idleBehavior === 'wander'
      ? ((p.wander && p.wander.radius) || (N.defaults && N.defaults.wanderRadius) || 1.6) : 0;
    let worst = null;
    for (const s of spawns) {
      if (!scn.includes(s.to)) continue;
      const d = Math.hypot(p.position[0] - s.at[0], p.position[1] - s.at[1],
                           p.position[2] - s.at[2]) - wander;
      if (!worst || d < worst.d) worst = { d, id: s.id };
    }
    if (worst) {
      ok(worst.d >= MIN_ARRIVAL,
         `npc "${p.id}" is clear of every arrival in its scenes`,
         `${worst.d.toFixed(2)} m from "${worst.id}"` + (wander ? ` (wander ${wander} subtracted)` : ''));
    }
    // Outside the circle, not merely near it: a villager inside a door's trigger is
    // standing in the doorway, and his talk prompt argues with the door's.
    let tight = null;
    for (const t of triggers) {
      if (t.from && !scn.includes(t.from)) continue;
      const d = Math.hypot(p.position[0] - t.at[0], p.position[1] - t.at[1],
                           p.position[2] - t.at[2]) - t.r - wander;
      if (!tight || d < tight.d) tight = { d, id: t.id, r: t.r };
    }
    if (tight) {
      ok(tight.d >= 0,
         `npc "${p.id}" stands outside every door trigger`,
         `${tight.d.toFixed(2)} m outside "${tight.id}" (r ${tight.r}` +
         (wander ? `, wander ${wander}` : '') + ')');
    }
  }
}

// ------------------------------------------------------- report
console.log('\n' + '-'.repeat(64));
console.log(`${pass} passed, ${fail} failed, ${warn} warnings`);
if (warn) { console.log('\nwarnings (not failures):'); warns.forEach(w => console.log('  · ' + w)); }
if (fail) { console.log('\nFAILURES:'); fails.forEach(f => console.log('  · ' + f)); process.exit(1); }
console.log('green — every speaker has a face and every person has a body.');
