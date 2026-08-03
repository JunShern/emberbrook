/* edge_probe — WHERE DOES THE WORLD LEAK, AND CAN THE PLAYER GET BACK?  (playtest round 6)
 *
 * Round 5's closing run walked past the Dellhollow gate (y 12.65), down the riverbed,
 * and spent 56 steps at y -2 .. -4.6 with no barrier and no way back. `walk_engine_gate`
 * cannot see this class: it asks whether a cell is STANDABLE, never whether a standable
 * cell is supposed to be REACHABLE, nor whether a descent is REVERSIBLE.
 *
 * The mechanism, from play3d.html's own walkStep, is an ASYMMETRY and not a hole:
 * stepping DOWN, the body box is floored at `max(g+STEP_UP, P.y+.02)` — the slope you
 * are leaving cannot obstruct you. Stepping UP, the box sits at `g+STEP_UP` on the new,
 * higher ground and the hillside above it is solid. So a slope steep enough to refuse a
 * climb still accepts a descent. Terrain that runs continuously downhill is therefore a
 * ONE-WAY VALVE by construction, and needs no hole to swallow a player.
 *
 *   §0 WATER      the water planes' own world boxes — "below the water plane" as a number
 *   §1 CENSUS     top standable surface + zone at every cell of the region tile
 *                 (SIM.floors / SIM.zone), so the leak can be drawn as a contour
 *   §2 DESCENT    from N seeds on the road and around the gate, a greedy downhill walk
 *                 driven by the ENGINE (SIM.tp + SIM.move at play3d's own 0.075 stride).
 *                 How many seeds end below water tells you gap-vs-flank.
 *   §3 RETURN     from each descent's resting place, 24 headings x M steps: the best
 *                 height regained. This is the number that makes it a soft-lock.
 *
 *   node tools/playtest/edge_probe.mjs [--port 3000] [--scene ow-valley] [--cell 4]
 *      [--seeds '[[x,z],...]'] [--descent 400] [--return 400] [--out <json>]
 *
 * Runs ONE Chrome, self-expires at 900 s, reaps on every exit path.
 */
import { freePort, findPage, killOrphans } from '../cdp.mjs';
import { spawn } from 'child_process';
import { mkdtempSync, writeFileSync, mkdirSync } from 'fs';
import { tmpdir } from 'os';
import { join, dirname } from 'path';
import WebSocket from 'ws';

const argv = process.argv.slice(2);
const arg = (k, d) => { const i = argv.indexOf('--' + k); return i >= 0 ? argv[i + 1] : d; };
const PORT = parseInt(arg('port', '3000'), 10);
const SC = arg('scene', 'ow-valley');
const CELL = parseFloat(arg('cell', '4'));
const NDESC = parseInt(arg('descent', '400'), 10);
const NRET = parseInt(arg('return', '400'), 10);
const OUT = arg('out', 'docs/qa/playtest/edge/edge-' + SC + '.json');
mkdirSync(dirname(OUT), { recursive: true });
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

const profile = mkdtempSync(join(tmpdir(), 'edgeprobe-'));
const cdpPort = await freePort();
const child = spawn(CHROME, [
  `--remote-debugging-port=${cdpPort}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--disable-extensions',
  '--disable-background-timer-throttling', '--disable-renderer-backgrounding',
  '--autoplay-policy=no-user-gesture-required',
  '--window-size=1280,800', '--headless=new', 'about:blank',
], { stdio: 'ignore' });
let done = false;
const reap = () => { if (done) return; done = true; try { child.kill('SIGKILL'); } catch (e) {} killOrphans(profile); };
process.on('exit', reap);
for (const s of ['SIGINT', 'SIGTERM']) process.on(s, () => { reap(); process.exit(1); });
setTimeout(() => { console.error('SELF-EXPIRY at 900 s'); reap(); process.exit(2); }, 900000);

const wsUrl = await findPage(cdpPort, { tries: 240, label: 'edge_probe', match: /^about:blank/ });
const ws = new WebSocket(wsUrl, { perMessageDeflate: false, maxPayload: 256 * 1024 * 1024 });
await new Promise(r => ws.on('open', r));
let id = 0; const pend = new Map();
ws.on('message', m => { const o = JSON.parse(m); if (o.id && pend.has(o.id)) { pend.get(o.id)(o); pend.delete(o.id); } });
const send = (method, params = {}) => new Promise((res, rej) => {
  const i = ++id; pend.set(i, o => o.error ? rej(new Error(method + ': ' + o.error.message)) : res(o.result));
  ws.send(JSON.stringify({ id: i, method, params }));
});
const ev = async (e) => {
  const r = await send('Runtime.evaluate', { expression: e, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.text + ' ' + (r.exceptionDetails.exception && r.exceptionDetails.exception.description || ''));
  return r.result.value;
};
await send('Runtime.enable'); await send('Page.enable');
await send('Page.navigate', { url: `http://localhost:${PORT}/play3d.html?nomusic=1&scene=${SC}` });

for (let i = 0; i < 240; i++) {
  if (await ev(`(()=>{try{return !!(window.SIM&&SIM.gpu&&SIM.gpu().meshes>0&&SIM.pos)}catch(e){return false}})()`)) break;
  await new Promise(r => setTimeout(r, 1000));
}
await ev(`(()=>{const f={};for(const k of ["story.ch1.started","story.ch1.done","story.ch1.gate-open","story.ch1.sendoff","lake-joined"])f[k]=true;GS.setFlags(f);return 1})()`);
await new Promise(r => setTimeout(r, 1200));

// FREEZE THE SCENE GRAPH. sgTick runs on the physics tick, so a probe walk that
// crosses a portal TRANSITIONS — and then reports the NEXT scene's coordinates as
// though the body had walked there. Measured: a 52.5 u walk from [138,-90] "arrived"
// at [60.5,-50.2], 87 u away, because it had actually re-entered ow-valley at its own
// bundle spawn. Terrain is what this instrument measures; doors are marker_probe's job.
const froze = await ev(`(()=>{try{ if(typeof SGE!=='undefined'){const n=SGE.length; SGE.length=0; return 'SGE cleared ('+n+' edges)'; } return 'SGE not reachable'; }catch(e){ return 'SGE error: '+e.message }})()`);

// AN INSTRUMENT THAT FINDS NOTHING MUST PROVE IT COULD HAVE FOUND SOMETHING:
// --nobound disarms the world bound in the live page so §4 can be run against the
// world as it was, and the same seeds shown leaking.
if (argv.includes('--nobound')) console.log('  --nobound: ' + await ev(`(()=>{try{FLOORY=null;return 'world bound disarmed';}catch(e){return 'could not disarm: '+e.message}})()`));
const bounds = JSON.parse(await ev(`JSON.stringify(SIM.bounds?SIM.bounds():{floorY:null,loaded:false})`));
const report = { scene: SC, cell: CELL, froze, bounds };
console.log(`edge_probe — ${SC}   [${froze}]  world bound: ${bounds.floorY === null ? 'NONE' : 'y >= ' + bounds.floorY} (worldbounds.json ${bounds.loaded ? 'loaded' : 'MISSING'})`);

// ------------------------------------------------------------------ §0 WATER
// No scene root is exported; climb to it from the camera play3d itself publishes.
const water = JSON.parse(await ev(`(()=>{
  let r=window._rtCam||window.__sgCam; if(!r) return '[]';
  while(r.parent) r=r.parent;
  const out=[]; const B=new THREE.Box3(); const seen=[];
  r.traverse(o=>{ if(o.isMesh && /^(water_|.*water.*)/i.test(o.name)) seen.push(o); });
  for(const o of seen){ B.setFromObject(o); out.push([o.name, +B.min.y.toFixed(2), +B.max.y.toFixed(2),
    [+B.min.x.toFixed(1),+B.max.x.toFixed(1)], [+B.min.z.toFixed(1),+B.max.z.toFixed(1)]]); }
  return JSON.stringify(out);
})()`).catch(() => '[]') || '[]');
report.water = water;
if (water.length) {
  console.log(`  §0 water planes (${water.length}):`);
  for (const w of water.slice(0, 8)) console.log(`       ${w[0]}  y ${w[1]}..${w[2]}  x ${w[3].join('..')}  z ${w[4].join('..')}`);
} else console.log('  §0 water: none found (SIM.root unavailable — see §1 contour instead)');

// ------------------------------------------------------------------ §1 CENSUS
const ZI = JSON.parse(await ev(`JSON.stringify(SIM.zoneInfo())`));
const X0 = ZI.origin[0], Z0 = ZI.origin[1];
const NX = Math.floor(ZI.cols * ZI.cell / CELL), NZ = Math.floor(ZI.rows * ZI.cell / CELL);
console.log(`  §1 tile x ${X0}..${X0 + ZI.cols * ZI.cell}  z ${Z0}..${Z0 + ZI.rows * ZI.cell}   lattice ${NX}x${NZ} @${CELL}u`);
const CENSUS_JS = `(function(x0,z,n,d){const out=[];for(let i=0;i<n;i++){const x=x0+i*d;
  const ys=SIM.floors(x,z); out.push([ys.length?+ys[0].toFixed(2):null, ys.length, SIM.zone(x,z)||'']);}
  return out;})`;
const census = [];
for (let j = 0; j < NZ; j++) {
  const z = Z0 + (j + 0.5) * CELL;
  census.push(JSON.parse(await ev(`JSON.stringify(${CENSUS_JS}(${X0 + 0.5 * CELL},${z},${NX},${CELL}))`)));
  if (j % 10 === 0) process.stdout.write(`\r     census row ${j}/${NZ}   `);
}
process.stdout.write('\r                              \r');
let nF = 0, minY = 1e9, maxY = -1e9; const zc = {};
for (const row of census) for (const c of row) { if (c[0] === null) continue; nF++; minY = Math.min(minY, c[0]); maxY = Math.max(maxY, c[0]); zc[c[2] || '-'] = (zc[c[2] || '-'] || 0) + 1; }
console.log(`     standable-top ${nF}/${NX * NZ} cells   y ${minY.toFixed(2)} .. ${maxY.toFixed(2)}`);
console.log(`     zones: ${Object.entries(zc).sort((a, b) => b[1] - a[1]).map(([k, v]) => `${k} ${v}`).join(' · ')}`);
report.census = { x0: X0, z0: Z0, nx: NX, nz: NZ, cell: CELL, grid: census };

// ------------------------------------------------------------------ §2 DESCENT
// The engine's own walk, greedy downhill. This is what "aim down into the hollow" is.
// A modal panel freezes phys() outright (UILOCK), so a story beat firing under a
// probe silently turns every later walk into zero motion — measured: one descent ran
// 50 legs, every seed after it reported '1 leg'. Clear the lock before every probe.
const SETTLE = `function unlock(){ try{ for(const k in UILOCK._h) UILOCK.unlock(k); }catch(e){} }
  function settle(x,z,ty){ unlock(); const ys=SIM.floors(x,z); if(!ys.length) return false;
    let b=ys[0]; if(ty!=null){ for(const y of ys) if(Math.abs(y-ty)<Math.abs(b-ty)) b=y; }
    SIM.tp(x,z,b); return true; }`;
const DESC_JS = `(function(sx,sz,n){ ${SETTLE}
  if(!settle(sx,sz,null)) return {path:[],end:[sx,null,sz],zone:'',nofloor:true};
  let p=SIM.pos(); const path=[[+p.x.toFixed(2),+p.y.toFixed(2),+p.z.toFixed(2)]];
  const D=[]; for(let k=0;k<16;k++){const a=k*Math.PI/8; D.push([Math.cos(a),Math.sin(a)]);}
  let stuck=0;
  for(let s=0;s<n;s++){
    unlock();
    const cur=SIM.pos(); let best=null;
    for(const [dx,dz] of D){
      SIM.tp(cur.x,cur.z,cur.y); unlock();
      for(let k=0;k<8;k++) SIM.move(dx*0.075,dz*0.075,1);       // 0.6 u probe
      const q=SIM.pos();
      const drop=cur.y-q.y, moved=Math.hypot(q.x-cur.x,q.z-cur.z);
      if(moved<0.05) continue;
      const score=drop;
      if(!best||score>best.score) best={score,dx,dz,q:{x:q.x,y:q.y,z:q.z}};
    }
    if(!best||best.score<=0.002){ stuck++; if(stuck>3) { SIM.tp(cur.x,cur.z,cur.y); break; } }
    else stuck=0;
    if(!best){ break; }
    SIM.tp(cur.x,cur.z,cur.y);
    for(let k=0;k<8;k++) SIM.move(best.dx*0.075,best.dz*0.075,1);
    const q=SIM.pos(); path.push([+q.x.toFixed(2),+q.y.toFixed(2),+q.z.toFixed(2)]);
    if(path.length>2000) break;
  }
  const e=SIM.pos();
  return {path, end:[+e.x.toFixed(2),+e.y.toFixed(2),+e.z.toFixed(2)], zone:SIM.zone(e.x,e.z)||''};
})`;

// --points 'name,x,z;name,x,z' skips the greedy descent entirely and runs §3 from
// exactly those places — the mode that answers "can a player who is ALREADY down
// there get out", which is the soft-lock question. The greedy walker is a screen for
// finding descents; a named pit is the thing you actually argue about.
const PTS = (arg('points', '') || '').split(';').filter(Boolean).map(t => {
  const p = t.split(','); return [p[0], parseFloat(p[1]), parseFloat(p[2])];
});
// Seeds: the ch1.done arrival, the road, the gate court, and the banks either side.
const SEEDS = JSON.parse(arg('seeds', JSON.stringify([
  ['ch1 arrival', -36.2, 17.2],
  ['road mid', 0.0, -4.0],
  ['road lower', 21.5, -17.7],
  ['gate approach', 36.0, -30.0],
  ['gate court', 44.9, -36.2],
  ['gate N flank', 44.9, -46.0],
  ['gate S flank', 44.9, -26.0],
  ['east bank', 60.0, -44.0],
  ['emberbrook gate', -57.8, 60.6],
  ['upvalley N', -20.0, -40.0],
  ['upvalley S', -20.0, 40.0],
  ['far east', 90.0, -60.0],
])));
const descents = [];
if (PTS.length) {
  console.log(`  §2 SKIPPED — --points given: ${PTS.length} named places`);
  for (const [name, sx, sz] of PTS) {
    const q = JSON.parse(await ev(`(()=>{const ys=SIM.floors(${sx},${sz}); if(!ys.length) return 'null';
      return JSON.stringify([${sx}, +ys[0].toFixed(2), ${sz}, SIM.zone(${sx},${sz})||'', ys.length]);})()`));
    if (!q) { console.log(`     ${name.padEnd(16)} NO FLOOR`); descents.push({ name, nofloor: true }); continue; }
    console.log(`     ${name.padEnd(16)} floor y ${q[1]}  zone ${q[3]}  (${q[4]} surfaces in the column)`);
    descents.push({ name, seed: [sx, sz], y0: q[1], end: [q[0], q[1], q[2]], zone: q[3], legs: 0, path: [] });
  }
} else {
console.log(`  §2 descent from ${SEEDS.length} seeds (greedy downhill, engine walk, <=${NDESC} legs)`);
for (const [name, sx, sz] of SEEDS) {
  const r = JSON.parse(await ev(`JSON.stringify(${DESC_JS}(${sx},${sz},${NDESC}))`));
  if (!r.path.length) { console.log(`     ${name.padEnd(16)} NO FLOOR at seed`); descents.push({ name, seed: [sx, sz], nofloor: true, end: r.end, path: [] }); continue; }
  const y0 = r.path[0][1], y1 = r.end[1];
  descents.push({ name, seed: [sx, sz], y0, end: r.end, zone: r.zone, legs: r.path.length, path: r.path });
  console.log(`     ${name.padEnd(16)} y ${String(y0).padStart(7)} -> ${String(y1).padStart(7)}  at [${r.end[0]}, ${r.end[2]}]  zone ${r.zone || '-'}  (${r.path.length} legs)`);
}
}
report.descents = descents;

// ------------------------------------------------------------------ §3 RETURN
const RET_JS = `(function(sx,sy,sz,n){ ${SETTLE}
  const D=[]; for(let k=0;k<24;k++){const a=k*Math.PI/12; D.push([Math.cos(a),Math.sin(a)]);}
  let best={gain:-1e9,y:sy,x:sx,z:sz,head:null};
  for(const [dx,dz] of D){
    settle(sx,sz,sy); let top=sy, tp=null, stallBy='', stallAt=null, trail=[];
    for(let k=0;k<n;k++){ if(k%50===0) unlock(); const q=SIM.move(dx*0.075,dz*0.075,1);
      if(k%50===0) trail.push([+q.x.toFixed(1),+q.y.toFixed(2),+q.z.toFixed(1),q.AIR?1:0]);
      if(q.y>top){top=q.y; tp={x:q.x,y:q.y,z:q.z};} }
    { const e=SIM.pos(); stallBy=SIM.blocked(e.x,e.z,e.y)||''; stallAt=[+e.x.toFixed(1),+e.y.toFixed(2),+e.z.toFixed(1)]; }
    if(top-sy>best.gain) best={gain:+(top-sy).toFixed(2), y:+top.toFixed(2),
      x:tp?+tp.x.toFixed(1):sx, z:tp?+tp.z.toFixed(1):sz, head:+Math.atan2(dz,dx).toFixed(3),
      // SELF-CHECK: a body walking n strides of SPD can be at most n*SPD from where it
      // started. Anything further means the tick did something other than walk — a void
      // respawn, a transition, a settle that never happened. Report it, never hide it.
      dist:+Math.hypot((tp?tp.x:sx)-sx,(tp?tp.z:sz)-sz).toFixed(1), budget:+(n*0.075).toFixed(1),
      stallBy, stallAt, trail};
  }
  return best;
})`;
console.log(`  §3 return: 24 headings x ${NRET} strides (${(NRET * 0.075).toFixed(1)} u each) from every descent's resting place`);
const returns = [];
for (const d of descents) {
  if (d.nofloor) continue;
  const b = JSON.parse(await ev(`JSON.stringify(${RET_JS}(${d.end[0]},${d.end[1]},${d.end[2]},${NRET}))`));
  returns.push({ name: d.name, from: d.end, ...b });
  const impossible = b.dist > b.budget + 1;
  console.log(`     ${d.name.padEnd(16)} best climb ${String(b.gain).padStart(6)} u  -> y ${String(b.y).padStart(6)} at [${b.x}, ${b.z}]  ${b.dist}u of ${b.budget}u walked${impossible ? '  <-- IMPOSSIBLE: not a walk' : ''}`);
  if (impossible || arg('trace', null) === d.name) console.log(`        trail ${JSON.stringify(b.trail)}`);
}
report.returns = returns;

// ------------------------------------------------------------------ §4 ESCAPE
// The other half of the same question, and the one that says whether the fence is
// doing anything: standing INSIDE, how far out can the body get? 24 headings from
// each seed, tracking the DEEPEST ground reached. With a bound armed this must never
// go below it; with no bound it is the leak, restated as a number.
const ESC_JS = `(function(sx,sz,n){ ${SETTLE}
  if(!settle(sx,sz,null)) return null;
  const s0=SIM.pos(); const D=[]; for(let k=0;k<24;k++){const a=k*Math.PI/12; D.push([Math.cos(a),Math.sin(a)]);}
  let worst={low:s0.y,x:s0.x,z:s0.z};
  for(const [dx,dz] of D){
    settle(sx,sz,null);
    for(let k=0;k<n;k++){ if(k%50===0) unlock(); const q=SIM.move(dx,dz,1);
      if(!q.AIR && q.y<worst.low) worst={low:+q.y.toFixed(2),x:+q.x.toFixed(1),z:+q.z.toFixed(1)}; }
  }
  return {start:+s0.y.toFixed(2), low:+worst.low.toFixed(2), at:[worst.x,worst.z]};
})`;
const ESC = JSON.parse(arg('escape', JSON.stringify([
  ['gate court', 44.9, -36.2], ['moorage bank', 61, -50], ['gorge road', 54, -46],
  ['east plateau', 90, -34], ['road lower', 21.5, -17.7],
])));
console.log(`  §4 escape: from ${ESC.length} IN-BOUNDS seeds, the deepest ground 24 headings x ${NRET} strides can reach`);
const escapes = [];
let leaked = 0;
for (const [name, sx, sz] of ESC) {
  const e = JSON.parse(await ev(`JSON.stringify(${ESC_JS}(${sx},${sz},${NRET}))`) || 'null');
  if (!e) { console.log(`     ${name.padEnd(16)} NO FLOOR`); continue; }
  const bad = bounds.floorY !== null && e.low < bounds.floorY - 0.01;
  if (bad) leaked++;
  escapes.push({ name, ...e, leaked: bad });
  console.log(`     ${name.padEnd(16)} from y ${String(e.start).padStart(6)} down to y ${String(e.low).padStart(6)} at [${e.at[0]}, ${e.at[1]}]${bad ? '   <-- LEAKED past the bound' : ''}`);
}
report.escapes = escapes;
if (bounds.floorY !== null) console.log(`     ${leaked ? 'FAIL' : 'ok'} — ${leaked}/${escapes.length} seeds reached ground below the bound (y ${bounds.floorY})`);

writeFileSync(OUT, JSON.stringify(report));
console.log(`  wrote ${OUT}`);
reap();
process.exit(0);
