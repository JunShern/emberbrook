/* fall_probe.mjs — WHAT MOVED THE BODY 11.8 METRES DOWN?
 *
 *   node tools/playtest/fall_probe.mjs --port 3000 [--from x,y,z] [--to x,y,z]
 *                                      [--cam weave] [--secs 12] [--out <json>]
 *
 * THE QUESTION (FIXLOG rounds 24 and 25).  A playtest run stepped
 * `[70.41, 7.87, -25.48]` -> `[74.05, -3.90, -23.98]` in one action and sat there
 * seven steps.  `walkStep` provably refuses to walk off that lip under WALKLOCK and
 * jump is disabled in a routed town, so SOMETHING ELSE moved that body — round 25
 * listed `sgCorrect`, the marooned unstick and a cut spawn as unmeasured candidates
 * and refused to guess between them.
 *
 * WHY NOT ANOTHER FILL.  Rounds 24 and 25 both recorded that `_court_probe --comp`,
 * `reach_probe` and `--way` each answer a DIFFERENT question about this geometry and
 * all three were wrong here in different directions.  Round 24's closing order was
 * literal: until an instrument drives the body with the motor the harness itself
 * uses, a claim about this deck needs a run.  So this probe DRIVES REAL KEYS through
 * CDP — the same `Input.dispatchKeyEvent` path `adapter_emberbrook.mjs` holds keys
 * with — and samples the truth every animation frame:
 *
 *     t, P.x/P.y/P.z, the shot, SIM.cine().cuts, SIM.cine().corrections,
 *     SIM.busy(), and every `eb-scene` event with its edge id and spawn
 *
 * THE VERDICT COMES FROM THE COUNTERS, NOT FROM A THEORY.  On the frame P.y drops:
 *   corrections++    -> `sgCorrect` moved it (the camera safety net teleported)
 *   cuts++           -> an AUTHORED cut spawn did, and the trace names the edge
 *   neither, AIR     -> walkStep/gravity: a plain walk-off, and the world needs a rail
 *   neither, no AIR  -> the marooned unstick (it sets AIR=false and jumps to lastRoute)
 *
 * A NEGATIVE RESULT MUST PROVE IT COULD HAVE FOUND SOMETHING (cdp.mjs's own rule):
 * the run reports how far the body actually travelled and how many keys landed, so
 * "no fall" is distinguishable from "the keys never reached the page".
 */
import { freePort, findPage, killOrphans, sweepStaleProfiles, GAME_PAGE } from '../cdp.mjs';
import { spawn } from 'child_process';
import { writeFileSync, mkdirSync } from 'fs';
import { tmpdir } from 'os';
import { join, dirname } from 'path';
import WebSocket from 'ws';
import { mkArg } from '../argv.mjs';

const argv = process.argv.slice(2);
const { arg, checkArgs } = mkArg(argv, ['port', 'from', 'to', 'cam', 'scene', 'secs', 'out', 'keys', 'motor', 'box', 'step', 'spray', 'landing']);
checkArgs('fall_probe');

const PORT = parseInt(arg('port', '3000'), 10);
const SCENE = arg('scene', 'del-cine');
const CAM = arg('cam', 'weave');
const FROM = arg('from', '70.41,7.87,-25.48').split(',').map(Number);
const TO = arg('to', '81.69,14.04,-17.30').split(',').map(Number);
const SECS = parseFloat(arg('secs', '14'));
const LANDING = arg('landing', '74.05,-3.90,-23.98').split(',').map(Number);
const OUT = arg('out', 'docs/qa/playtest/round26/fall-probe.json');
mkdirSync(dirname(OUT), { recursive: true });

const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const PROFILE_PREFIX = 'fallprobe-';
sweepStaleProfiles(PROFILE_PREFIX);
const profile = join(tmpdir(), PROFILE_PREFIX + process.pid);
mkdirSync(profile, { recursive: true });
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
setTimeout(() => { console.error('SELF-EXPIRY at 300 s'); reap(); process.exit(2); }, 300000);

const wsUrl = await findPage(cdpPort, { tries: 240, label: 'fall_probe', match: /^about:blank/ });
const ws = new WebSocket(wsUrl, { perMessageDeflate: false, maxPayload: 64 * 1024 * 1024 });
await new Promise(r => ws.on('open', r));
let id = 0; const pend = new Map();
ws.on('message', m => { const o = JSON.parse(m); if (o.id && pend.has(o.id)) { pend.get(o.id)(o); pend.delete(o.id); } });
const send = (method, params = {}) => new Promise((res, rej) => {
  const i = ++id; pend.set(i, o => o.error ? rej(new Error(method + ': ' + o.error.message)) : res(o.result));
  ws.send(JSON.stringify({ id: i, method, params }));
});
const ev = async (e) => {
  const r = await send('Runtime.evaluate', { expression: e, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.text + ' ' +
    (r.exceptionDetails.exception && r.exceptionDetails.exception.description || ''));
  return r.result.value;
};
const sleep = ms => new Promise(r => setTimeout(r, ms));

await send('Runtime.enable'); await send('Page.enable');
const url = `http://localhost:${PORT}/play3d.html?nomusic=1&nofollow=1&scene=${SCENE}` +
            `&cam=${CAM}&sx=${FROM[0]}&sy=${FROM[1]}&sz=${FROM[2]}`;
await send('Page.navigate', { url });
console.log('  nav ' + url);

let ready = false;
for (let i = 0; i < 240; i++) {
  try {
    // READY MEANS THE SCENE IS BUILT, not that SIM exists. The first run of this
    // probe accepted `SIM.cine()` truthy, drove keys into a page whose walk network
    // was still loading, and reported "NO FALL" about a body sitting at [0,2,0].
    const ok = await ev(`(()=>{try{
      const c=SIM.cine(), g=SIM.gpu(), p=SIM.pos();
      return !!(c && c.shot && g.walk>0 && !SIM.busy() && Math.abs(p.x-${FROM[0]})<3);
    }catch(e){return false}})()`);
    if (ok) { ready = true; break; }
  } catch (e) { }
  await sleep(250);
}
if (!ready) { console.error('FAIL: the page never exposed SIM'); reap(); process.exit(3); }

// ---- the recorder, installed IN the page -----------------------------------
// rAF, so the sample rate is the physics rate. `eb-scene` is play3d's own module
// contract and carries the edge id and the spawn — the one place a transition
// announces itself without patching a module-scope function.
await ev(`(()=>{
  window.__fall = {t:[], ev:[], t0: performance.now()};
  const F = window.__fall;
  addEventListener('eb-scene', e => F.ev.push({at: performance.now()-F.t0, kind:'eb-scene', detail:e.detail}));
  F.raf = true;
  const tick = () => {
    if(!F.raf){ requestAnimationFrame(tick); return; }
    try{
      const p = SIM.pos(), c = SIM.cine();
      F.t.push([+(performance.now()-F.t0).toFixed(0), +p.x.toFixed(3), +p.y.toFixed(3), +p.z.toFixed(3),
                c && c.shot, c ? c.cuts : -1, c ? c.corrections : -1, SIM.busy()?1:0,
                c ? c.corrTicks : -1, (c && c.corrTarget) || null]);
    }catch(err){}
    requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
  return true;
})()`);

// ---- drive real keys toward the target -------------------------------------
// The heading is the one the playtest run's own goto used: from the weave stand to
// the LOCKHEAD LADDER HEAD, which is what sent it east off the deck's end.
const KEYMAP = {
  w: { code: 'KeyW', key: 'w', vk: 87 }, a: { code: 'KeyA', key: 'a', vk: 65 },
  s: { code: 'KeyS', key: 's', vk: 83 }, d: { code: 'KeyD', key: 'd', vk: 68 },
};
async function keyEvt(type, k) {
  const m = KEYMAP[k];
  return send('Input.dispatchKeyEvent', { type, code: m.code, key: m.key,
    windowsVirtualKeyCode: m.vk, nativeVirtualKeyCode: m.vk });
}
await sleep(1500);   // let the recorder gather enough samples to measure the tick rate
// SEED THE BODY WHERE THE RUN STOOD, EXPLICITLY.  The URL spawn goes through
// sgPlace, and sgPlace is one of the things under suspicion here: at this very xz it
// settles to y 2.04 when asked for 7.87.  Using it to place the body would be
// measuring the suspect with the suspect.  SIM.tp(x, z, y) sets P.y outright.
const SEEDY = FROM[1];
await ev(`SIM.tp(${FROM[0]},${FROM[2]},${SEEDY})`);
// AND THE SEAM LAYER MUST BE IDLE BEFORE THE DRIVE. `sgTick` — and therefore every
// cut and `sgCorrect` itself — returns immediately while `SGbusy`, and SGbusy only
// clears when the fade promise resolves, which needs rAF. On a machine with a bake on
// it the URL spawn's own correction can leave SGbusy set for the whole run: the first
// version of this probe drove 240 ticks with busy=1 throughout and therefore measured
// walkStep ALONE while believing it was measuring the seam layer.
await ev(`SIM.shot(${JSON.stringify(CAM)})`).catch(() => {});
let idle = false;
for (let i = 0; i < 160; i++) {
  if (!(await ev('SIM.busy()'))) { idle = true; break; }
  await sleep(250);
}
await ev(`SIM.tp(${FROM[0]},${FROM[2]},${SEEDY})`);
const before = await ev('JSON.stringify(SIM.pos())');
console.log('  seeded at ' + before + '  shot ' + await ev('SIM.cine().shot') +
            (idle ? '  (seam layer idle)' : '  !! SGbusy NEVER CLEARED — sgTick/sgCorrect are OFF, this run measures walkStep alone'));
if (!idle) { console.error('fall_probe: refusing to report a seam-layer verdict with SGbusy stuck'); }

// ---------------------------------------------------------------- THE DRIVE
// TWO MOTORS, and the tool says which one it used.
//
//   --motor keys   real `Input.dispatchKeyEvent`, physics on rAF. The honest one,
//                  and the one round 24 demanded — but rAF is the FIRST thing a
//                  loaded machine takes away: with a Cycles bake on this laptop the
//                  page ticked 143 frames in 60 s and the body walked 1.1 m. A probe
//                  that cannot move the body cannot see a fall.
//   --motor tick   SIM.keys()+SIM.tick(), which is phys() -> rayStep -> walkStep ->
//                  marooned() -> sgTick() -> sgCorrect() — THE SAME MOTOR, one tick
//                  per call, immune to the frame rate. Not the keyboard, and this
//                  file says so wherever it reports a result.
const MOTOR = arg('motor', 'tick');
const OCT = [['w'], ['w', 'd'], ['d'], ['s', 'd'], ['s'], ['s', 'a'], ['a'], ['w', 'a']];
const KEYOBJ = c => '{' + c.map(k => `${k}:1`).join(',') + '}';

async function holdKeys(combo, ms) {
  for (const k of combo) await keyEvt('keyDown', k);
  await sleep(ms);
  for (const k of combo) await keyEvt('keyUp', k);
  await sleep(60);
}
async function holdTicks(combo, n) {
  // THE rAF RECORDER IS SILENCED FOR THE DRIVE. Both recorders write one array, and
  // one stamps milliseconds while the other stamps a tick index — interleaved, the
  // trace reads as a 4-second gap that is really two clocks.
  return ev(`(()=>{const F=window.__fall; F.raf=false; SIM.keys(${KEYOBJ(combo)});
    for(let i=0;i<${n};i++){ const r=SIM.tick(1);
      const c=SIM.cine();
      F.t.push([F.t.length, +r.x.toFixed(3), +(r.AIR?r.airY:r.y).toFixed(3), +r.z.toFixed(3),
                c&&c.shot, c?c.cuts:-1, c?c.corrections:-1, SIM.busy()?1:0,
                c?c.corrTicks:-1, (c&&c.corrTarget)||null, r.AIR?1:0]); }
    SIM.keys(null); return SIM.pos();})()`);
}

let TRIAL = 320;
if (MOTOR === 'keys') {
  const fps = await ev(`(()=>{const F=window.__fall, n=F.t.length; return n>3 ?
    1000*(n-1)/Math.max(1,(F.t[n-1][0]-F.t[0][0])) : 60;})()`);
  TRIAL = Math.max(320, Math.round(1400 / Math.max(2, fps) * 8));
  console.log(`  motor=keys, page ticking at ${fps.toFixed(1)} fps -> trial window ${TRIAL} ms`);
} else {
  console.log('  motor=tick (SIM.keys + SIM.tick: phys/walkStep/marooned/sgTick/sgCorrect)');
  await ev('(()=>{window.__fall.t.length=0; return 1})()');
}

// One round of the adapter's own octant search, so the probe never has to know the
// page's yaw convention: whichever heading closes on the target is the one held.
let best = null;
for (const combo of OCT) {
  const p0 = await ev('SIM.pos()');
  if (MOTOR === 'keys') await holdKeys(combo, TRIAL); else await holdTicks(combo, 8);
  const p1 = await ev('SIM.pos()');
  const gain = Math.hypot(TO[0] - p0.x, TO[2] - p0.z) - Math.hypot(TO[0] - p1.x, TO[2] - p1.z);
  if (process.env.FALL_VERBOSE) console.log(`    ${combo.join('+')} gain ${gain.toFixed(3)}`);
  if (!best || gain > best.gain) best = { combo, gain };
  // SIM.tp's signature is (x, z, y) — NOT (x, y, z). Getting it wrong here would
  // silently re-seed every trial round at the wrong height.
  await ev(`SIM.tp(${FROM[0]},${FROM[2]},${SEEDY})`).catch(() => {});
}
console.log(`  heading ${best.combo.join('+')} (closes ${best.gain.toFixed(2)} m)`);
await ev('(()=>{window.__fall.t.length=0; window.__fall.ev.length=0; return 1})()');
await ev(`window.__fall.ev.push({at:0, kind:'HOLD', motor:'${MOTOR}', keys:${JSON.stringify(best.combo)}})`);
if (MOTOR === 'keys') await holdKeys(best.combo, SECS * 1000);
else await holdTicks(best.combo, Math.round(SECS * 60));

// A CORRECTION FIRED BY THE DRIVE LANDS AFTER THE DRIVE. transitionTo raises the
// veil, and `sgHandoff` — which is where sgPlace actually moves the body — runs only
// when the fade promise resolves. The tick motor cannot advance that; it is timers and
// rAF. So: after the keys are released, wait for the seam layer to go idle and record
// where the body ACTUALLY ended up. This is the frame the real run reported.
let settled = null;
{
  const p0 = await ev('JSON.stringify({p:SIM.pos(), c:SIM.cine().corrections, k:SIM.cine().cuts, s:SIM.cine().shot})');
  for (let i = 0; i < 160; i++) {
    if (!(await ev('SIM.busy()'))) break;
    await sleep(250);
  }
  const p1 = await ev('JSON.stringify({p:SIM.pos(), c:SIM.cine().corrections, k:SIM.cine().cuts, s:SIM.cine().shot, busy:SIM.busy()})');
  settled = { before: JSON.parse(p0), after: JSON.parse(p1) };
  const a = settled.before, b = settled.after;
  console.log('\n--- §1b where the pending transition put the body ---');
  console.log(`  at the end of the drive  [${a.p.x.toFixed(2)}, ${a.p.y.toFixed(2)}, ${a.p.z.toFixed(2)}]  shot=${a.s} cuts=${a.k} corr=${a.c}`);
  console.log(`  once the seam settled    [${b.p.x.toFixed(2)}, ${b.p.y.toFixed(2)}, ${b.p.z.toFixed(2)}]  shot=${b.s} cuts=${b.k} corr=${b.c} busy=${b.busy}`);
  const dy = b.p.y - a.p.y;
  if (Math.abs(dy) > 1.0)
    console.log(`  >> THE TRANSITION MOVED THE BODY ${dy.toFixed(2)} m VERTICALLY ` +
                `(${b.c > a.c ? 'a CORRECTION' : b.k > a.k ? 'an authored CUT' : 'neither counter moved'})`);
  else console.log('  >> the transition did not move the body vertically');
}

const rec = await ev('JSON.stringify({t: window.__fall.t, ev: window.__fall.ev})');
const F = JSON.parse(rec);
const T = F.t;
console.log(`  ${T.length} samples (${MOTOR}), ${F.ev.length} events`);

// ---- the verdict ------------------------------------------------------------
let drop = null;
for (let i = 1; i < T.length; i++) {
  const dy = T[i][2] - T[i - 1][2];
  if (dy < -1.5) { drop = i; break; }
}
const rows = [];
const fmt = r => `#${String(r[0]).padStart(6)}  [${r[1].toFixed(2)}, ${r[2].toFixed(2)}, ${r[3].toFixed(2)}]  ` +
  `shot=${String(r[4]).padEnd(10)} cuts=${r[5]} corr=${r[6]} busy=${r[7]} corrTicks=${String(r[8]).padStart(2)} AIR=${r[10]||0} corrTarget=${r[9] || '-'}`;
console.log('\n--- trajectory (first, every 30th, and the drop) ---');
for (let i = 0; i < T.length; i += 30) rows.push(fmt(T[i]));
console.log(rows.join('\n'));

let verdict;
if (drop == null) {
  const trav = Math.hypot(T[T.length - 1][1] - T[0][1], T[T.length - 1][3] - T[0][3]);
  verdict = `NO FALL in ${T.length} ticks. The body travelled ${trav.toFixed(2)} m in plan and ` +
            `ended at y ${T[T.length - 1][2].toFixed(2)} — so the keys DID reach the page.`;
} else {
  const a = T[drop - 1], b = T[drop];
  console.log('\n--- THE DROP ---');
  for (let i = Math.max(0, drop - 4); i <= Math.min(T.length - 1, drop + 3); i++) console.log('  ' + fmt(T[i]));
  const dCut = b[5] - a[5], dCorr = b[6] - a[6];
  const near = F.ev.filter(e => Math.abs(e.at - b[0]) < 900);
  const dPlan = Math.hypot(b[1] - a[1], b[3] - a[3]);
  if (dCorr > 0) verdict = `sgCorrect — THE CAMERA SAFETY NET MOVED THE BODY. corrections ` +
    `${a[6]}->${b[6]} on the drop frame; ${a[2].toFixed(2)} -> ${b[2].toFixed(2)} m ` +
    `(${(b[2]-a[2]).toFixed(2)} m) and ${dPlan.toFixed(2)} m in plan.`;
  else if (dCut > 0) verdict = 'AN AUTHORED CUT — cuts++ on the drop frame; the edge is in the events below.';
  else if (b[10]) verdict = 'walkStep/gravity — AIR is set on the drop frame: a plain walk-off, and the lip needs a rail.';
  else verdict = 'NEITHER a cut nor a correction and NOT airborne — the marooned unstick (it sets AIR=false and jumps to lastRoute).';
  console.log('\n  events within 900 ms of the drop:');
  for (const e of near) console.log('    ' + JSON.stringify(e));
}

// ---------------------------------------------------------------- §2 THE SETTLE
// sgCorrect does not choose a destination: its spawn IS the body's current position,
// and `sgPlace` then RE-SETTLES the height — `walkFloors(x, z)`, nearest to the y it
// was handed.  `walkGround`, which is what let the body stand there in the first
// place, probes (x, z) AND FOUR NEIGHBOURS at +/-0.18 m (the plank-crack tolerance).
// sgPlace has no such tolerance.  So a body standing legitimately on a plank crack is
// re-settled onto whatever the exact column holds — over these decks, the river.
//
// `SIM.tpY(x, z, ty)` IS sgPlace's settle, reachable from a test: same walkFloors,
// same nearest-to-ty pick.  This census walks the lip and prints where the two
// disagree.  A cell where the walker stands at ~7.9 and the settle returns -3.90 is a
// TRAPDOOR: any transition taken while standing on it drops the player 11.8 m.
// ---------------------------------------------------------------- §2 THE SPRAY
// ONE heading is not every heading (the adapter's own lesson, adapter_emberbrook
// finding: "Their own payload recorded `bursts: 1`. ONE HEADING IS NOT EVERY
// HEADING"). The run's goto pushed five headings per round and slid off three of
// them. So: from the stand, and from every metre of the lip, push all 16 world-space
// directions and report the LOWEST y the body reaches. `SIM.move(dx,dz,n)` is
// phys([dx,dz]) — walkStep in world space, no camera convention in the way.
const SPRAY_N = parseInt(arg('spray', '60'), 10);
const spray = await ev(`(()=>{
  const seeds = [];
  for (let x = 69.0; x <= 78.01; x += 1.0)
    for (let z = -27.0; z <= -22.99; z += 1.0) {
      const hi = SIM.tpY(x, z, 40).y;
      if (hi != null && hi > 4.0) seeds.push([+x.toFixed(2), +z.toFixed(2), +hi.toFixed(2)]);
    }
  const worst = [];
  for (const [sx, sz, sy] of seeds) {
    let lo = sy, at = null;
    for (let k = 0; k < 16; k++) {
      const a = k * Math.PI / 8, dx = Math.cos(a) * 0.075, dz = Math.sin(a) * 0.075;
      SIM.tp(sx, sz, sy);
      for (let i = 0; i < ${SPRAY_N}; i++) {
        const r = SIM.move(dx, dz, 1);
        const y = r.AIR ? r.y : r.y;
        if (y < lo) { lo = y; at = [+r.x.toFixed(2), +y.toFixed(2), +r.z.toFixed(2), k, i, !!r.AIR]; }
      }
    }
    if (lo < sy - 3.0) worst.push({ seed: [sx, sy, sz], lo: +lo.toFixed(2), at });
  }
  return { seeds: seeds.length, worst };
})()`);
console.log('\n--- §2 THE SPRAY: 16 headings x ' + SPRAY_N + ' steps from every seed on the lip ---');
console.log(`    ${spray.seeds} seeds on the weave/moorage lip (x 69..78, z -27..-23, any walk floor above y 4)`);
if (!spray.worst.length) {
  console.log(`  NO SEED FALLS MORE THAN 3 m. walkStep will not leave this tier in any direction.`);
} else {
  for (const w of spray.worst)
    console.log(`    from [${w.seed}] -> y ${w.lo}  at [${w.at && w.at.slice(0,3)}] heading ${w.at && w.at[3]} step ${w.at && w.at[4]} AIR=${w.at && w.at[5]}`);
  console.log(`  ${spray.worst.length} seed(s) from which the body can get more than 3 m below where it started.`);
}

// ---------------------------------------------------------------- §3 THE COLUMN
// What is actually in the column the run landed in? The floor SET, read out of the
// engine by sweeping sgPlace's own settle over every plausible target height. If
// -3.90 is not in this list, nothing that re-settles a height could have produced it.
const column = await ev(`(()=>{
  const seen = [], keep = SIM.pos();
  for (let ty = -12; ty <= 22.01; ty += 0.5) {
    const y = SIM.tpY(${LANDING[0]}, ${LANDING[2]}, ty).y;
    if (y != null && !seen.some(v => Math.abs(v - y) < 0.02)) seen.push(+y.toFixed(2));
  }
  SIM.tp(keep.x, keep.z, keep.y);
  return seen.sort((a,b)=>a-b);
})()`);
console.log(`\n--- §3 the walk floors in the landing column [${LANDING[0]}, ${LANDING[2]}] ---`);
console.log('  ' + (column.length ? column.join('  ') : '(none)'));
console.log(`  y ${LANDING[1]} is ${column.some(v => Math.abs(v - LANDING[1]) < 0.05) ? 'IN' : 'NOT IN'} the set.`);


// ---------------------------------------------------------------- §4 THE FALLBACK
// sgPlace, verbatim (play3d.html):
//     let ys = (walkRef.length ? walkFloors(p[0], p[2]) : []);
//     if (!ys.length) ys = floors(p[0], p[2]);
// So a spawn whose COLUMN carries no walk floor silently switches oracles: the settle
// stops asking the walk network and asks the COLLISION set, which over these decks
// contains the river. That is the one candidate the other three sections leave alive,
// and it is testable without a transition, because SIM.tpY carries the same fallback.
// Any column here that settles below y 2 while its neighbours are decks at ~7.9 is a
// place where taking a transition lands the player in the water.
const fb = await ev(`(()=>{
  const out = [], keep = SIM.pos();
  for (let x = 70; x <= 80.01; x += 0.4)
    for (let z = -28; z <= -22.01; z += 0.4) {
      const y = SIM.tpY(x, z, 7.87).y;
      if (y != null && y < 2.0) out.push([+x.toFixed(1), +z.toFixed(1), +y.toFixed(2)]);
    }
  SIM.tp(keep.x, keep.z, keep.y);
  return out;
})()`);
console.log('\n--- §4 columns where sgPlace settles below y 2 asking for 7.87 ---');
if (!fb.length) console.log('  NONE in x 70..80 / z -28..-22 at 0.4 m. The fallback does not bite on this tier.');
else { for (const r of fb.slice(0, 40)) console.log(`    [${r[0]}, ${r[1]}] -> y ${r[2]}`);
       console.log(`  ${fb.length} column(s).`); }

const CENSUS = { spray, column, fallback: fb };

console.log('\nVERDICT: ' + verdict);
writeFileSync(OUT, JSON.stringify({ url, motor: MOTOR, settled, census: CENSUS, from: FROM, to: TO, secs: SECS, seedY: SEEDY,
  heading: best.combo, verdict, drop, samples: T, events: F.ev }, null, 1));
console.log('wrote ' + OUT);
reap();
process.exit(0);
