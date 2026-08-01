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
import fs from 'fs';
import path from 'path';
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

// ------------------------------------------------------- report
console.log('\n' + '-'.repeat(64));
console.log(`${pass} passed, ${fail} failed, ${warn} warnings`);
if (warn) { console.log('\nwarnings (not failures):'); warns.forEach(w => console.log('  · ' + w)); }
if (fail) { console.log('\nFAILURES:'); fails.forEach(f => console.log('  · ' + f)); process.exit(1); }
console.log('green — every speaker has a face and every person has a body.');
