#!/usr/bin/env node
/* sky_sweep.mjs — THE DOME-CLIP GATE: can any standing vantage see past the sky?
 *
 *   node tools/ow_probe/sky_sweep.mjs --port 8931 [--out /tmp/skysweep] [--frames 0]
 *
 * WHY THIS EXISTS (2026-08-06, the user's "giant blue dot"). The overworld sky
 * dome (r=360) and ridge rings (r<=345) are pinned at y=0 and follow the player
 * in XZ only, so their far side sits at radius + the eye's offset from the dome
 * centre in view depth. With cam.far=400 a high vantage far-plane-CLIPPED a cap
 * out of the dome, and flat scene.background poured through the hole as an
 * enormous pale-blue disc. Every gate was green: nothing ever measured the sky's
 * own geometry against the frustum. This does, exhaustively.
 *
 * WHAT IT MEASURES. In the RUNNING game (real ORBIT solve, real cam — so a
 * future boom/clamp lane is measured too, not the formula in this file): for a
 * grid of stations x rigs x 24 yaws, after the frame loop settles each pose,
 *   domeMax = fwd . (domeCentre - cam.position) + 360   (rings: + 370 — the outermost ring at its +7% radial wobble)
 * and FAILS on any pose with domeMax/ringMax >= cam.far (margin printed). The
 * rigs deliberately include the WORST reachable one: max zoom (dist 70), max
 * pitch (1.35) — the input clamps in play3d's own orbit handler — and the
 * stations include the highest walkable cell (SIM.floors census, y 51.06).
 * A screen, then your eye: --frames N also photographs N yaws at the worst rig
 * so a human can look at what the numbers claim.
 */
import { spawn } from 'child_process';
import { writeFileSync, mkdirSync, readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { mkArg } from '../argv.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const { arg } = mkArg(process.argv);
const PORT = arg('port', '3000');
const OUT = arg('out', '/tmp/skysweep');
const FRAMES = parseInt(arg('frames', '8'), 10);

// Stations: low valley floor, the gate spawn shelf, the highest walkable cell.
const STATIONS = [
  { key: 'gorge', x: 22.81, z: -21.66 },   // low — cam_sweep station 150
  { key: 'gate',  x: -57.43, z: 65.55 },   // the Emberbrook gate shelf (y ~27)
  { key: 'peak',  x: -84,    z: -100 },    // highest walkable cell (y 51.06)
];
// Rigs: shipped, raised, and the orbit handler's own clamp corner (worst case).
const RIGS = [
  { key: 'ship', pitch: 0.70, tilt: 0.16, dist: 40 },
  { key: 'high', pitch: 1.05, tilt: 0.16, dist: 70 },
  { key: 'max',  pitch: 1.35, tilt: 0.16, dist: 70 },
];
const NYAW = 24;

// One async in-page pass: every pose, two rAFs to let frame() re-solve the cam,
// then the analytic depth of the dome/ring far side against cam.far.
const SWEEP = `(async function(){
  const raf=()=>new Promise(r=>requestAnimationFrame(r));
  const rows=[];
  for(const st of ${JSON.stringify(STATIONS)}){
    window.__tp(st.x,st.z);
    for(const rig of ${JSON.stringify(RIGS)}){
      for(let i=0;i<${NYAW};i++){
        const O=window.ORBIT;
        O.yaw=i*Math.PI*2/${NYAW}; O.pitch=rig.pitch; O.tilt=rig.tilt; O.dist=rig.dist;
        O.panX=0;O.panY=0;O.panZ=0;
        await raf(); await raf();
        const p=SIM.pos();
        const C=new THREE.Vector3(p.x,0,p.z);
        const fwd=new THREE.Vector3(0,0,-1).applyQuaternion(cam.quaternion);
        const dc=fwd.dot(C.clone().sub(cam.position));
        rows.push({st:st.key,rig:rig.key,yaw:+O.yaw.toFixed(2),py:+p.y.toFixed(1),
                   far:cam.far,domeMax:+(dc+360).toFixed(1),ringMax:+(dc+370).toFixed(1)});
      }
    }
  }
  window.__report=rows; return rows.length;
})()`;

mkdirSync(OUT, { recursive: true });
const spec = [{ out: join(OUT, 'sweep-last.png'),
  expr: `window.__report=null; ${SWEEP};`,
  settle: STATIONS.length * RIGS.length * NYAW * 60 + 6000, report: true }];
// frames for the eye: worst rig at the two high stations, FRAMES yaws
for (let i = 0; i < FRAMES; i++) {
  const yaw = +(i * Math.PI * 2 / FRAMES).toFixed(3);
  for (const st of [STATIONS[1], STATIONS[2]]) {
    spec.push({ out: join(OUT, `eye-${st.key}-y${i}.png`),
      expr: `window.__tp(${st.x},${st.z}); var O=window.ORBIT; O.yaw=${yaw};`
        + ` O.pitch=1.05; O.tilt=0.16; O.dist=70; O.panX=0;O.panY=0;O.panZ=0;`,
      settle: 1200 });
  }
}
const specPath = join(OUT, 'spec.json');
writeFileSync(specPath, JSON.stringify(spec, null, 1));

const child = spawn('node', ['tools/ow_probe/ow_multi.mjs', '--spec', specPath, '--port', PORT],
  { cwd: join(HERE, '..', '..'), stdio: ['ignore', 'pipe', 'inherit'] });
let buf = '';
child.stdout.on('data', d => { buf += d.toString(); process.stdout.write(d); });
child.on('exit', (code) => {
  let rows = null;
  for (const line of buf.split('\n')) {
    const i = line.indexOf('report=');
    if (i < 0) continue;
    try { const j = JSON.parse(line.slice(i + 7)); if (Array.isArray(j)) rows = j; } catch (e) {}
  }
  if (!rows) { console.error('SKY SWEEP: no report rows — the sweep never ran'); process.exit(2); }
  writeFileSync(join(OUT, 'rows.json'), JSON.stringify(rows, null, 1));
  const bad = rows.filter(r => r.domeMax >= r.far || r.ringMax >= r.far);
  let worst = rows[0];
  for (const r of rows) if (r.domeMax - r.far > worst.domeMax - worst.far) worst = r;
  console.log(`\nSKY SWEEP: ${rows.length} poses, worst dome margin ` +
    `${(worst.far - worst.domeMax).toFixed(1)} m (st=${worst.st} rig=${worst.rig} yaw=${worst.yaw})`);
  if (bad.length) {
    console.log(`FAIL — ${bad.length} poses clip the sky:`);
    for (const r of bad.slice(0, 10)) console.log('  ', JSON.stringify(r));
    process.exit(1);
  }
  console.log('PASS — no standing vantage can see past the dome or the rings.');
  process.exit(code || 0);
});
