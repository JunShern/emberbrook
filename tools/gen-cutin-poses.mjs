#!/usr/bin/env node
// gen-cutin-poses.mjs — CHAINED POSE-DIVERSITY MATRIX: three pose candidates per
// expression, for the user to pick from.
//
//   node tools/gen-cutin-poses.mjs vesper            # 3 rolls x every expression + rest
//   node tools/gen-cutin-poses.mjs vesper --mood sad,wry
//   node tools/gen-cutin-poses.mjs vesper --page     # rebuild the picker page only
//
// THE METHOD IS THE USER'S OWN (2026-08-01, suite v2 review): per expression, roll
// pose 1 from the base plate; roll 2 attaches roll 1 as an extra reference with the
// instruction "same character, same expression, DIFFERENT pose — a different
// silhouette from the pose shown in the reference"; roll 3 attaches both. The pose
// prompt itself is pose-first, not hands-first — see promptFor in gen-cutin-art.mjs.
// USER OVERRIDE, same day: no gate ceremony on these rolls — generate, matte for
// transparency, and put them on a page to look at. Nothing here touches the shipped
// set; picks feed the real gated rollout afterwards.
//
// Rolls land in public/assets/characters/<id>/studio/poses/ (gitignored, like all
// studio plates); mattes + page land in docs/qa/cutins/<id>-poses/.
import fs from 'fs';
import path from 'path';
import { execFileSync } from 'child_process';
import { genart, PRICE } from './genart.mjs';
import { promptFor, DEFAULT_FRAMING, DEFAULT_KEY, loadSpec, hintFor } from './gen-cutin-art.mjs';

const root = path.join(import.meta.dirname, '..');
const CHARS = path.join(root, 'public/assets/characters');

const argv = process.argv.slice(2);
const id = argv.find(a => !a.startsWith('--'));
const pageOnly = argv.includes('--page');
const mi = argv.indexOf('--mood');
if (!id) { console.error('usage: gen-cutin-poses.mjs <character> [--mood a,b] [--page]'); process.exit(1); }

const spec = loadSpec();
const ent = spec[id];
if (!ent) { console.error(`no spec entry for "${id}"`); process.exit(1); }
const hint = hintFor(id, ent);
const framing = ent.framing || DEFAULT_FRAMING;
const rest = path.join(CHARS, id, 'studio', 'rest.png');
if (!fs.existsSync(rest)) { console.error(`no base plate: ${rest}`); process.exit(1); }

const posesDir = path.join(CHARS, id, 'studio', 'poses');
const qaDir = path.join(root, 'docs/qa/cutins', id + '-poses');
const ROLLS = 3;
// rest included: the user asked for the full 9-expression matrix, rest too.
const MOODS = ['rest', ...Object.keys(ent.moods || {})];
const picked = mi >= 0 ? new Set(argv[mi + 1].split(',').map(s => s.trim())) : null;
const moods = MOODS.filter(m => !picked || picked.has(m));

async function chain(mood) {
  const expression = mood === 'rest' ? ent.rest : ent.moods[mood];
  const prior = [];
  let calls = 0;
  for (let n = 1; n <= ROLLS; n++) {
    const out = path.join(posesDir, `${mood}-${n}.png`);
    if (fs.existsSync(out)) { prior.push(out); console.log(`  have ${mood}-${n}`); continue; }
    const prompt = promptFor({
      hint, key: DEFAULT_KEY, expression, framing, extra: ent.extra || null,
      gesture: ent.gesture || null, first: false, chain: prior.length,
    });
    const r = await genart({ out, refs: [rest, ...prior], prompt });
    if (!r.ok) { console.log(`  FAIL ${mood}-${n}  ${r.error.slice(0, 120)}`); break; }
    calls++;
    console.log(`  ok   ${mood}-${n}  ${Math.round(r.bytes / 1024)} KB`);
    prior.push(out);
  }
  return calls;
}

function mattes() {
  // One python pass mats every pose plate to an RGBA cutout via gen-cutin.py's own
  // key path (make_cutin, key=True). No gates — a plate whose matte fails is copied
  // through raw so the user still sees the pose.
  execFileSync('python3', ['-c', `
import importlib.util, os, shutil, sys
root, cid, src_dir, out_dir = sys.argv[1:5]
spec = importlib.util.spec_from_file_location('gen_cutin', os.path.join(root, 'tools/gen-cutin.py'))
gc = importlib.util.module_from_spec(spec); spec.loader.exec_module(gc)
os.makedirs(out_dir, exist_ok=True)
for n in sorted(os.listdir(src_dir)):
    if not n.endswith('.png'):
        continue
    dst = os.path.join(out_dir, n)
    if os.path.exists(dst):
        continue
    cut, diag = gc.make_cutin(os.path.join(src_dir, n), dst, cid, key=True)
    if cut is None:
        shutil.copyfile(os.path.join(src_dir, n), dst)
        print('  raw   %s  (matte: %s)' % (n, diag.get('error')))
    else:
        print('  matte %s  %dx%d' % (n, cut.width, cut.height))
`, root, id, posesDir, qaDir], { stdio: 'inherit' });
}

function page() {
  // SIZING IS THE GAME'S OWN (user asked to see it, 2026-08-01): dialogue.js's
  // placeCutin gives EVERY plate the same on-screen HEIGHT and lets width follow
  // the pose (silhouette crops mean a folded-arm pose is wider, never taller),
  // with the art's bottom sunk CUTIN_SINK (55%) behind the dialogue box so no
  // bottom edge is ever visible. The picker reproduces exactly that: uniform
  // figure height, bottom-anchored, sunk behind a faux box strip — width-fitting
  // the cell was how the page lied about scale before.
  const rows = MOODS.map(mood => {
    const cards = [];
    for (let n = 1; n <= ROLLS; n++) {
      const f = `${mood}-${n}.png`;
      if (!fs.existsSync(path.join(qaDir, f))) continue;
      cards.push(`<div class=c><div class=stage><img src="${f}" loading=lazy><div class=box>${id} — “…”</div></div><div class=m>pose ${n}${
        n > 1 ? ` <span class=k>· chained on ${n === 2 ? 'pose 1' : 'poses 1+2'}</span>` : ''}</div></div>`);
    }
    return `<h2>${mood}</h2><div class=g>${cards.join('') || '<p class=k>no rolls yet</p>'}</div>`;
  });
  const html = `<meta charset=utf-8><title>${id} — pose candidates</title>
<style>body{background:#1a1620;color:#e7ddd0;font:14px system-ui;margin:20px}
h1{font-size:20px}h2{font-size:16px;margin:26px 0 8px;text-transform:capitalize;border-top:1px solid #3a3145;padding-top:14px}
p{color:#a89179;max-width:70em}
.g{display:grid;grid-template-columns:repeat(3,minmax(240px,360px));gap:14px}
.c{border-radius:10px;overflow:hidden;border:1px solid #3a3145;background:#141019}
/* the stage mimics placeCutin: uniform portrait HEIGHT (320px here = the game's
   ~560px at picker scale), width free, bottom sunk 55% behind the box strip */
.stage{position:relative;height:380px;background:conic-gradient(#2a2433 90deg,#221c2b 90deg 180deg,#2a2433 180deg 270deg,#221c2b 270deg) 0 0/28px 28px;overflow:hidden}
.stage img{position:absolute;left:50%;transform:translateX(-50%);bottom:${Math.round(66 - 0.55 * 66) - 66}px;height:320px;width:auto;z-index:0}
.box{position:absolute;left:6px;right:6px;bottom:6px;height:66px;z-index:1;border-radius:8px;
background:linear-gradient(#2c3a6e,#1a2140);border:2px solid #8ea3d8;box-shadow:inset 0 0 12px #0008;
color:#dfe6ff;font-size:12px;padding:8px 10px}
.m{padding:6px 10px;background:#141019}.k{color:#7a6a8a}</style>
<h1>${id} — pose candidates (pick one per expression)</h1>
<p>Pose-first prompt (silhouette before hands, staged like an animator's key frame) with the user's
chained-diversity method: pose 1 rolls from the base plate; pose 2 sees pose 1 as a reference and is
asked for a DIFFERENT silhouette; pose 3 sees both. SIZING IS THE GAME'S: every portrait renders at
the same height (width follows the pose), bottom sunk 55% behind the dialogue box exactly as
dialogue.js places it — so what you compare here is what the game will show.</p>
${rows.join('\n')}\n`;
  fs.mkdirSync(qaDir, { recursive: true });
  fs.writeFileSync(path.join(qaDir, 'index.html'), html);
  console.log('picker page: docs/qa/cutins/' + id + '-poses/index.html');
}

if (!pageOnly) {
  fs.mkdirSync(posesDir, { recursive: true });
  fs.mkdirSync(qaDir, { recursive: true });
  console.log(`${moods.length} expressions x ${ROLLS} chained rolls · ~$${(moods.length * ROLLS * PRICE).toFixed(2)} max`);
  // Chains are sequential inside an expression (roll 2 needs roll 1) but the nine
  // expressions are independent — four run at a time.
  let spent = 0, i = 0;
  async function worker() {
    for (;;) {
      const m = moods[i++];
      if (!m) return;
      console.log(`\n${m}:`);
      spent += await chain(m);
    }
  }
  await Promise.all(Array.from({ length: Math.min(4, moods.length) }, worker));
  console.log(`\n${spent} generation calls · ~$${(spent * PRICE).toFixed(2)}`);
  mattes();
}
page();
