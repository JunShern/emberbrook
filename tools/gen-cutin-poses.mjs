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
    // rest rolls CALM (user, pose-matrix review: the rest row came back
    // over-acting): no theatrical push, no pose mandate, no gesture line —
    // chained variety still applies, but between quiet at-ease poses.
    const prompt = promptFor({
      hint, key: DEFAULT_KEY, expression, framing, extra: ent.extra || null,
      gesture: mood === 'rest' ? null : ent.gesture || null,
      first: false, chain: prior.length, calm: mood === 'rest',
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
# tools/ ON THE PATH FIRST. gen-cutin.py imports cutin_edge as a sibling module, and
# "python3 -c" seeds sys.path with the CWD, not with the script's directory — so this
# whole step died with ModuleNotFoundError unless the caller happened to have
# PYTHONPATH set. It reached main only because Vesper's matrix was matted from a
# shell that did.
sys.path.insert(0, os.path.join(root, 'tools'))
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

// USER PICKS, PER CHARACTER (2026-08-01): locked rows get a highlight on the picker
// so the user can see at a glance what is already decided. Re-rolled rows have no
// entry; a character absent here gets a fresh page with nothing pre-picked.
const ALL_PICKS = {
  vesper: { rest: 1, happy: 3, wry: 2, worried: 2, surprised: 3, determined: 1, sad: 1, tender: 2, thinking: 3, annoyed: 3 }, // COMPLETE 2026-08-01 — SHIPPED as vesper's suite
  // AGENT PICKS, 2026-08-02, made under the user's explicit delegation ("you pick,
  // ship them") while they were away, against the taste Vesper's own picks set:
  // a distinct silhouette per emotion, hands serving the pose rather than
  // performing, a composed rest, and the emotion aimed at the off-frame partner.
  // SHIPPED, and every one of them is a single number away from being overruled —
  // change it here, re-run `--page`, and re-ship with
  // `gen-cutin.py <id> --picks ...`. The picker pages stay live for exactly that.
  lake: { rest: 1, happy: 3, wry: 3, worried: 3, surprised: 3, determined: 3, sad: 3, tender: 1, thinking: 2, annoyed: 3, hollow: 3, weary: 3 },
  maren: { rest: 1, happy: 3, awed: 3, determined: 3, indignant: 2, crushed: 2, surprised: 3, wry: 1, worried: 3, sad: 3, tender: 1, thinking: 3, annoyed: 2 },
};
const PICKS = ALL_PICKS[id] || {};
// BASE PICKS (user, 2026-08-02): the ratified base candidate per character —
// studio/rest.png is a copy of studio/rest-cand<N>.png, and the picker page shows
// the pick at the top so every pose row is read against the base it rolled from.
const BASE_PICKS = { lake: 3, maren: 1 };

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
      const picked = PICKS[mood] === n;
      cards.push(`<div class="c${picked ? ' picked' : ''}"><div class=stage><img src="${f}" loading=lazy><div class=box>${id} — “…”</div></div><div class=m>${
        picked ? '★ PICKED — ' : ''}pose ${n}${
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
/* art bottom = box top (72px up) minus the 20% sink (13px) = 59px — INSIDE the
   opaque box, never below it; mirrors dialogue.js CUTIN_SINK=0.20 exactly. */
.stage img{position:absolute;left:50%;transform:translateX(-50%);bottom:59px;height:160px;width:auto;z-index:0} /* halved with CUTIN_MAX_PX 2026-08-01 */
.box{position:absolute;left:6px;right:6px;bottom:6px;height:66px;z-index:1;border-radius:8px;
background:linear-gradient(#2c3a6e,#1a2140);border:2px solid #8ea3d8;box-shadow:inset 0 0 12px #0008;
color:#dfe6ff;font-size:12px;padding:8px 10px}
.m{padding:6px 10px;background:#141019}.k{color:#7a6a8a}
.c.picked{border:3px solid #ffb52e;box-shadow:0 0 14px #ffb52e66}
.c.picked .m{background:#2a1f0a;color:#ffd98a;font-weight:600}</style>
<h1>${id} — pose candidates (pick one per expression)</h1>
${fs.existsSync(path.join(qaDir, `base-cand${BASE_PICKS[id] || 0}.png`)) ? `
<h2>THE RATIFIED BASE — every roll below starts from this pick</h2>
<div class=g>
${fs.existsSync(path.join(qaDir, 'ratified-ref.jpeg')) ? `<div class=c><div class=stage><img src="ratified-ref.jpeg" style="height:100%;bottom:0"></div><div class=m>the user-ratified look (reference)</div></div>` : ''}
<div class="c picked"><div class=stage><img src="base-cand${BASE_PICKS[id]}.png"><div class=box>${id} — “…”</div></div><div class=m>★ PICKED — base candidate ${BASE_PICKS[id]}</div></div>
</div>` : ''}
${fs.existsSync(path.join(qaDir, 'reference-new.png')) ? `
<h2>BASE CANDIDATES — pick one (characterful rest is back, waist-up framing kept)</h2>
<p>User ruling: the neutralized base watered her personality out of every pose roll. These three
restore the wry sizing-up rest on the deep waist-up composite. The pick becomes the reference
every future roll starts from; the matrix rerolls from it.</p>
<div class=g>
<div class=c><div class=stage><img src="reference-cand1.png" loading=lazy></div><div class=m>base candidate 1</div></div>
<div class=c><div class=stage><img src="reference-cand2.png" loading=lazy></div><div class=m>base candidate 2</div></div>
<div class=c><div class=stage><img src="reference-cand3.png" loading=lazy></div><div class=m>base candidate 3</div></div>
</div>
<div class=g style="margin-top:10px">
<div class=c><div class=stage><img src="reference-new.png" loading=lazy></div><div class=m>(for comparison) the neutralized base being replaced</div></div>
</div>` : ''}
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
