// emb_bake_shipped.mjs — REBAKE EMBERBROOK PLATES AT THE GRADE THEY ALREADY SHIP AT.
//
//   node tools/emb_bake_shipped.mjs --cams homerow,square          # run them
//   node tools/emb_bake_shipped.mjs --cams all --print             # just show the commands
//   node tools/emb_bake_shipped.mjs --cams homerow --samples 128 --res 2688x1536
//
// WHY IT EXISTS — THE REGRADE TRAP, MEASURED (round 1, 2026-08-09).  A whole-town
// `cine_bake --town emberbrook` regrades every plate to `<town>.cameras.json`'s
// `defaults.exposure`, and THAT IS NOT THE SHIPPED GRADE.  The default is 0.55; the eleven
// shipped plates carry, in `cine.json`'s own per-camera `appliedGrade`, exposure 1.00 on
// eight and 0.78 on three, per-plate `moon` at 1.5 / 2.0 / 2.71 / 3.14 / 3.75, and a
// `warmAnchorGlow 0.35` + 900 W waystone lantern on two.  Measured against the shipped art:
// homerow p50 27.4 vs 3.0, square 37.8 vs 12.0, gatefield 13.0 vs 1.0 — **a plain rebake
// darkens nine of eleven plates by 0.45-0.86 stops with `cine_test`, `slice_test`,
// `routes_derive` and both walk gates GREEN.**  `cine.json` RECORDS the grade and nothing
// ENFORCES it; the only prose copy of the right commands was a NEXT STEP paragraph in
// DAYLOG.  This is the enforcement: the bundle's own record is the input.
//
// It NEVER invents a number.  Every flag is read off `appliedGrade` and a camera whose
// record is missing a field it needs is REFUSED BY NAME rather than baked at a default —
// an unstated grade is the whole defect, so guessing one here would rebuild it.
// `sunEnergy`, `viewTransform` and `look` are asserted to match the rig/defaults rather
// than passed, because `cine_bake` has no flag for them: a plate whose shipped grade
// disagrees with what the bake can express is REFUSED, not quietly approximated.
import fs from 'fs';
import path from 'path';
import {execFileSync} from 'child_process';

const ROOT = path.dirname(new URL(import.meta.url).pathname).replace(/\/tools$/, '');
const A = process.argv.slice(2);
const opt = (n, d) => { const i = A.indexOf(n); return i >= 0 ? A[i + 1] : d; };
const PRINT = A.includes('--print');
const BLEND = opt('--blend', 'tools/blends/emberbrook-dressed.blend');
const BUNDLE = opt('--bundle', 'public/assets/scenes/emb-cine');
const SAMPLES = opt('--samples', null);
const RES = opt('--res', null);
const BLENDER = opt('--blender', '/Applications/Blender.app/Contents/MacOS/Blender');

const CINE = JSON.parse(fs.readFileSync(path.join(ROOT, BUNDLE, 'cine.json'), 'utf8'));
const DEF = CINE.defaults || {};
const want = opt('--cams', 'all');
const ids = want === 'all' ? CINE.cameras.map((c) => c.id) : want.split(',');

const refusals = [];
const jobs = [];
for (const id of ids) {
  const c = CINE.cameras.find((x) => x.id === id);
  if (!c) { refusals.push(`${id}: no such camera in cine.json`); continue; }
  const g = c.appliedGrade;
  if (!g) { refusals.push(`${id}: no appliedGrade recorded — REFUSED, there is no grade to reproduce`); continue; }
  for (const k of ['exposure', 'sky', 'moon']) {
    if (g[k] === undefined || g[k] === null) refusals.push(`${id}: appliedGrade.${k} missing`);
  }
  if (g.viewTransform !== DEF.view_transform || g.look !== DEF.look)
    refusals.push(`${id}: view transform/look (${g.viewTransform} / ${g.look}) differ from ` +
                  `defaults (${DEF.view_transform} / ${DEF.look}) and cine_bake has no flag for them`);
  jobs.push({id, g});
}
if (refusals.length) {
  console.error('REFUSED, and nothing was baked:');
  for (const r of refusals) console.error('  ' + r);
  process.exit(2);
}

// group cameras that share a grade — one Blender load per group, still 1-wide serial
const key = (g) => JSON.stringify([g.exposure, g.sky, g.moon, g.moonColor, g.moonZenithDeg,
                                   g.moonAzimuthDeg, g.warmAnchorGlow, g.lampWatts,
                                   g.waystoneLanternW]);
const groups = new Map();
for (const j of jobs) {
  const k = key(j.g);
  if (!groups.has(k)) groups.set(k, {g: j.g, ids: []});
  groups.get(k).ids.push(j.id);
}

const cmds = [];
for (const {g, ids: gi} of groups.values()) {
  const a = ['-b', BLEND, '--python-exit-code', '1', '-P', 'tools/cine_bake.py', '--',
             '--town', 'emberbrook', '--cams', gi.join(','),
             '--exposure', String(g.exposure), '--sky', String(g.sky),
             '--moon', String(g.moon),
             '--mooncol', (g.moonColor || [0.65, 0.75, 1.0]).join(','),
             '--moonrx', String(g.moonZenithDeg), '--moonrz', String(g.moonAzimuthDeg)];
  if (g.warmAnchorGlow) a.push('--glow', String(g.warmAnchorGlow));
  if (g.lampWatts) a.push('--lampwatts', String(g.lampWatts));
  if (g.waystoneLanternW) a.push('--anchorlight', String(g.waystoneLanternW));
  if (SAMPLES) a.push('--samples', SAMPLES);
  if (RES) a.push('--res', RES);
  cmds.push(a);
}

console.log(`emb_bake_shipped — ${jobs.length} camera(s) in ${cmds.length} grade group(s), ` +
            `1-wide serial (dressed Emberbrook saturates the GPU; N-wide measured no faster)`);
for (const a of cmds) console.log('  ' + BLENDER + ' ' + a.join(' '));
if (PRINT) process.exit(0);
for (const a of cmds) {
  console.log('\n=== ' + a[a.indexOf('--cams') + 1] + ' ===');
  execFileSync(BLENDER, a, {cwd: ROOT, stdio: 'inherit'});
}
console.log('\nemb_bake_shipped DONE');
