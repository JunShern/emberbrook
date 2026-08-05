#!/usr/bin/env node
/* cam_sweep.mjs — SWEEP THE OVERWORLD BOOM AND MEASURE EVERY CANDIDATE.
 *
 *   node tools/ow_probe/cam_sweep.mjs --port 3000 --out <dir> [--grid "p,t,lift; ..."]
 *   node tools/ow_probe/cam_sweep.mjs --shots "0.535,0.225,0"   # photograph one rig
 *
 * ONE Chrome, five stations, every candidate measured at each of them through
 * tools/ow_probe/camfit.js.  A candidate is a triple (ORBIT.pitch, ORBIT.tilt,
 * ORBIT.panY); DISTANCE IS NEVER TOUCHED — boom 40 is a standing user ruling.
 *
 * THE STATIONS.  Derived from tools/valley_map.py's own resampled road, so they
 * survive a map edit the way tools/ow_probe/land_cams.json's do:
 *     world x = map x - 140,   world z = 100 - map y,   yaw = road tangent - pi
 * (verified against land_cams.json: station 12 -> (-57.43, 65.55), station 150 ->
 * (26.45, -22.61), both exact).  All five are photographed AT THE SHIPPED BOOM,
 * dist 40, which land_cams' gate/meadow entries are NOT — they sit at 16 and 12,
 * so three of the four historical landscape plates are not the player's camera and
 * a camera pass judged on them is judging a rig nobody plays.
 *
 * `wood` and `bend` are in the sweep because of a measurement land_cams already
 * carried and nothing ever acted on: at boom 40 the follow camera is INSIDE the
 * canopy for road stations ~78-172, most of the walked corridor.  A camera pass
 * that does not photograph those stations cannot see its own biggest prize.
 */
import { spawn } from 'child_process';
import { writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';
import { fileURLToPath } from 'url';
import { dirname as pdirname } from 'path';
import { mkArg } from '../argv.mjs';

const HERE = pdirname(fileURLToPath(import.meta.url));
const { arg } = mkArg(process.argv);
const PORT = arg('port', '3000');
const OUT = arg('out', '/tmp/camsweep');
const SHOTS = arg('shots', '');
const TAG = arg('tag', 'sw');

export const STATIONS = [
  { key: 'gate',  x: -57.43, z: 65.55,  yaw: -1.5426, note: 'station 12 — the Emberbrook gate portal' },
  { key: 'vista', x: -56.33, z: 47.95,  yaw: -1.8040, note: 'station 30 — open valley below the gate' },
  { key: 'wood',  x: -22.44, z: 8.41,   yaw: -2.1696, note: 'station 90 — mid-corridor, under the whisperwood' },
  { key: 'bend',  x: 1.11,   z: -8.35,  yaw: -2.3999, note: 'station 120 — mid-corridor, the bend' },
  { key: 'gorge', x: 26.45,  z: -22.61, yaw: -2.6882, note: 'station 150 — the gorge road, Dellhollow approach' },
];

// pitch x tilt.  0.61/0.22 is what ships.  The pitch axis stops at 0.46 because the
// 2026-08-04 sweep already measured 0.45 and below driving the boom into terrain —
// what it never sampled is the 0.61..0.46 band, which is where the horizon actually
// crosses the top edge of a 42 deg frame.
const PITCH = [0.61, 0.55, 0.49, 0.43, 0.37];
const TILT  = [0.04, 0.10, 0.16, 0.22];
function defaultGrid() {
  const g = [];
  for (const p of PITCH) for (const t of TILT) g.push([p, t, 0]);
  return g;
}
function parseGrid(s) {
  return s.split(';').map(x => x.trim()).filter(Boolean)
    .map(x => x.split(',').map(Number)).map(a => [a[0], a[1], a[2] || 0]);
}

const grid = arg('grid', '') ? parseGrid(arg('grid')) : (SHOTS ? parseGrid(SHOTS) : defaultGrid());
// `settle` is the ONLY thing giving the in-page async sweep time to finish; size it
// off the candidate count, and prove it by the row count coming back (a short settle
// reports `null`, loudly, rather than half a table).
const SETTLE = parseInt(arg('settle', String(6000 + grid.length * 2500)), 10);
mkdirSync(OUT, { recursive: true });

const tpl = (s) => `window.__tp(${s.x},${s.z}); var O=window.ORBIT; O.yaw=${s.yaw};`
  + ` O.dist=40; O.panX=0;O.panY=0;O.panZ=0; SIM.tick(2);`;

const spec = [];
if (SHOTS) {
  // PICTURE MODE: one plate per station per rig, no sweep.
  for (const [p, t, l] of grid) {
    const nm = `p${String(p).replace('.', '')}t${String(t).replace('.', '')}${l ? 'l' + l : ''}`;
    for (const s of STATIONS) {
      spec.push({
        out: join(OUT, `${TAG}-${nm}-${s.key}.png`),
        expr: `${tpl(s)} window.__report=null;`
          + ` OWFIT.at(${p},${t},${l}).then(function(r){window.__report=r;});`,
        settle: 4000, report: true,
      });
    }
  }
} else {
  // SWEEP MODE: one Chrome, one plate per station (the last candidate — thrown away),
  // and the whole grid measured inside the page so the terrain cache is paid once.
  for (const s of STATIONS) {
    const cands = JSON.stringify(grid);
    spec.push({
      out: join(OUT, `${TAG}-${s.key}-last.png`),
      expr: `${tpl(s)} window.__report=null; OWFIT.grid();`
        + ` OWFIT.sweep(${cands}).then(function(rs){`
        + `window.__report={station:${JSON.stringify(s.key)},rows:rs};});`,
      settle: SETTLE, report: true,
    });
  }
}
const specPath = join(OUT, `${TAG}-spec.json`);
writeFileSync(specPath, JSON.stringify(spec, null, 1));

const args = ['tools/ow_probe/ow_multi.mjs', '--spec', specPath, '--port', PORT,
  '--inject', 'tools/ow_probe/camfit.js'];
const child = spawn('node', args, { cwd: join(HERE, '..', '..'), stdio: ['ignore', 'pipe', 'inherit'] });
let buf = '';
child.stdout.on('data', d => { buf += d.toString(); process.stdout.write(d); });
child.on('exit', (code) => {
  const rows = [];
  for (const line of buf.split('\n')) {
    const i = line.indexOf('report=');
    if (i < 0) continue;
    let j;
    try { j = JSON.parse(line.slice(i + 7)); } catch (e) { continue; }
    if (j && j.rows) for (const r of j.rows) rows.push(Object.assign({ station: j.station }, r));
    else if (j) rows.push(j);
  }
  const jsonPath = join(OUT, `${TAG}-rows.json`);
  writeFileSync(jsonPath, JSON.stringify(rows, null, 1));
  console.log(`\nROWS ${rows.length} -> ${jsonPath}  (ow_multi exit ${code})`);
  process.exit(code);
});
