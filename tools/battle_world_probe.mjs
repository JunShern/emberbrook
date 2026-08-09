#!/usr/bin/env node
// battle_world_probe.mjs — THE INSTRUMENT FOR THE BET-3 SPIKE (?arena=world).
//
// docs/plans/battle-presentation-inventory.md §10 BET A asks five questions and
// this tool answers four of them with numbers; the fifth (what does it LOOK like)
// it answers with pictures, in the same run, off the same page.
//
//   node tools/battle_world_probe.mjs --mode=place  --port=3000 --n=120
//   node tools/battle_world_probe.mjs --mode=battle --port=3000 --out=docs/qa/battle-world
//   node tools/battle_world_probe.mjs --mode=fps    --port=3000
//   node tools/battle_world_probe.mjs --mode=teardown --port=3000
//   node tools/battle_world_probe.mjs --mode=regress --port=3000    # flag OFF proof
//
// EVERYTHING IT REPORTS IS READ OUT OF THE RUNNING GAME. Placement is asked of
// SIM.ground / SIM.floors / SIM.blocked — the ENGINE's own answers, not the file's
// (the walk_engine_gate lesson). Frames are `renderer.info.render.frame`, the
// world renderer's own counter, because the picture is drawn by play3d's loop.
// Chrome goes through tools/cdp.mjs and is reaped by --user-data-dir prefix.
import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import { freePort, findPage, killOrphans, sweepStaleProfiles } from './cdp.mjs';
import { censusExpr, verdict as rayVerdict } from './ray_budget.mjs';

const require = createRequire(import.meta.url);
const WebSocket = require('ws');
const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');

const argv = process.argv.slice(2);
const arg = (k, d) => { const h = argv.find(a => a.startsWith('--' + k + '=')); return h ? h.split('=').slice(1).join('=') : d; };
const PORT = parseInt(arg('port', '3000'), 10);
const MODE = arg('mode', 'place');
const N = parseInt(arg('n', '120'), 10);
const OUT = join(ROOT, arg('out', 'docs/qa/battle-world'));
const HEAD = argv.includes('--head');
const WORLD = arg('arena', 'world');
// ---- THE TWO KNOBS THAT SEPARATE THE CONFOUNDED STAGING-RATE CHANGE --------
// The rate moved 68.8% -> 64.4% over the same 160 road cells while TWO things
// changed at once, and DAYLOG named them as confounded:
//   (a) the visibility test got stricter — two spine rays became two spine rays
//       PLUS nine samples across the body's own box, refused below 67% visible.
//       `--vismin=0` restores the old verdict exactly: the nine-sample refusal
//       is `vf < CFG.place.visMin`, so at 0 it can never fire and the two spine
//       rays are the whole test, which is byte-for-byte the spike's own gate.
//   (b) the sweep became yaw x pitch and takes the BEST rather than the first.
//       `--bcam=0` sets BattleWorld.CAM.on = false, which solveArena already
//       treats as "the spike's own behaviour, to the line": one fixed pitch,
//       return the first yaw that places, no scoreView ranking.
// Neither knob is a code change and neither moves a default — both are read at
// solve time out of the module's own config.
//   (c) AND --bcam ITSELF BUNDLES TWO THINGS: the pitch AXIS and best-of-rather-
//       than-first. `--pitches=0.27` overwrites CAM.solve.pitches with the ONE
//       elevation the spike used (= CFG.cam.pitch), so `--bcam=1 --pitches=0.27`
//       is the new sweep machinery — yawKeep collection plus the scoreView
//       ranking — with the extra pitch samples taken away. That is the fifth arm
//       of the factorial and the only one that can attribute the yawTurned
//       erosion (52.7 -> 91.9%) to best-of versus the pitch axis. Same shape as
//       the two above: a list read at solve time, no default moved, nothing in
//       public/ touched.
const VISMIN = arg('vismin', null);      // null = leave CFG.place.visMin alone
const BCAM = arg('bcam', null);          // '0' = yaw-only sweep (spike behaviour)
const PITCHES = arg('pitches', null);    // e.g. '0.27' — CAM.solve.pitches, comma-separated
// ---- (d) THE PLACEMENT-QUALITY TERM (2026-08-09) --------------------------
// `--bplace=0` sets BattleWorld.PLACE.on = false, which restores the ladder's
// own first-acceptance rule to the line. It is the A/B this instrument needs to
// price the term: the extra candidates it evaluates are the whole cost, and the
// only honest way to state that cost is the same cells through both arms.
const BPLACE = arg('bplace', null);
// ---- THE RELOCATION SWEEP (--relocate) ------------------------------------
// THE RULING THIS MEASURES (CLAUDE.md, 2026-08-08): when placement refuses a
// spot the game RELOCATES WITHIN THE WORLD to the nearest feasible staging
// site and never falls back to the diorama, so DISTANCE IS NOT A CONSTRAINT —
// the search radius is whatever gives full coverage. `--mode=place` already
// walks each road cell into the nearest standable ENCOUNTER cell within 11 m
// and then asks the solver ONCE; that is not the ruling's mechanism, it is the
// zone model. `--relocate=<maxR>` keeps walking outward, ring by ring, until
// the shipped solver ACCEPTS, and records the ring it accepted at — so ONE run
// yields the whole radius-to-coverage curve (coverage(R) = cells whose first
// accepting ring is <= R), the relocation-distance distribution, and the
// residual set. Nothing in public/ is touched and no default moves: the solver
// called is the shipped `BattleWorld.solveArena` at the shipped config.
//
// THE SOUND CHEAP SCREEN. A candidate that no yaw can lay the formation onto
// GEOMETRICALLY (floor + SIM.blocked, `vis:false`) can never pass with the
// visibility test ON — vis:false is a strict relaxation of the same test — so
// it is refused for ten cheap solvePlacement calls instead of the 40 ray-heavy
// ones a full solveArena costs. No false negatives by construction; the screen
// can only skip work the shipped solver was going to refuse anyway.
const RELOC = arg('relocate', null);     // metres, e.g. '100' — enables the sweep
const RINGS = arg('rings', '5,8,11,13,15,17,20,24,27,30,35,40,48,60,72,85,100');
const SOLVECAP = parseInt(arg('solvecap', '80'), 10);  // full solves per cell, then the cell is capped
const VERIFY = argv.includes('--verify');  // run the REAL solveArena on every candidate and compare
const CDP_PORT = await freePort();
const CHROME = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const sleep = ms => new Promise(r => setTimeout(r, ms));

const PROFILE_PREFIX = 'battle-world-probe-';
sweepStaleProfiles(PROFILE_PREFIX);
const profile = join(process.env.TMPDIR || '/tmp', PROFILE_PREFIX + process.pid);

const flag = MODE === 'regress' ? '' : `&arena=${WORLD}`;
const URL = `http://localhost:${PORT}/play3d.html?scene=ow-valley&rt=1&nomusic=1${flag}`;

const chrome = spawn(CHROME, [
  `--remote-debugging-port=${CDP_PORT}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--disable-extensions',
  '--autoplay-policy=no-user-gesture-required',
  '--hide-scrollbars', '--force-device-scale-factor=1',
  // VSYNC OFF FOR THE FRAME-BUDGET MODE ONLY. With it on, both paths return
  // exactly 120.0 fps because the compositor caps them, which measures the
  // display and not the renderer.
  ...(MODE === 'fps' ? ['--disable-gpu-vsync', '--disable-frame-rate-limit'] : []),
  '--window-size=1600,900',
  ...(HEAD ? [] : ['--headless=new']),
  URL,
], { stdio: 'ignore' });
let closing = false;
const kill = () => {
  if (closing) return; closing = true;
  try { chrome.kill('SIGKILL'); } catch (e) { }
  // reap by OUR profile prefix only — never by process name
  try { killOrphans(profile); } catch (e) { }
};
process.on('exit', kill);
process.on('SIGINT', () => { kill(); process.exit(130); });

function connect(url) {
  return new Promise((res, rej) => {
    const ws = new WebSocket(url, { perMessageDeflate: false, maxPayload: 256 * 1024 * 1024 });
    const pend = new Map(); let id = 0;
    ws.on('open', () => res({
      send(method, params) {
        return new Promise((ok, no) => { const mid = ++id; pend.set(mid, { ok, no }); ws.send(JSON.stringify({ id: mid, method, params: params || {} })); });
      },
      close() { try { ws.close(); } catch (e) { } },
    }));
    ws.on('error', rej);
    ws.on('message', (raw) => {
      let m; try { m = JSON.parse(raw); } catch (e) { return; }
      if (m.id && pend.has(m.id)) { const { ok, no } = pend.get(m.id); pend.delete(m.id); m.error ? no(new Error(m.error.message)) : ok(m.result); }
    });
  });
}
async function ev(cdp, expr, ms) {
  const r = await cdp.send('Runtime.evaluate', {
    expression: expr, awaitPromise: true, returnByValue: true, userGesture: true, timeout: ms || 300000 });
  if (r.exceptionDetails) {
    const e = r.exceptionDetails;
    throw new Error('page exception: ' + ((e.exception && e.exception.description) || e.text));
  }
  return r.result && r.result.value;
}

// THE SPIKE MODULE IS NOT IN play3d.html's SCRIPT LIST (coordinator custody), so
// the probe injects it the way the page's own modules arrive: a classic <script>
// with a src, appended to the document. Nothing about the module changes — it is
// the same file, in the same global scope, reading the same ?arena= flag.
const INJECT = `(async () => {
  if (window.BattleWorld) return { already: true, on: window.BattleWorld.on };
  await new Promise((res, rej) => {
    const s = document.createElement('script');
    s.src = 'js/battle_world.js?v=' + Date.now();
    s.onload = res; s.onerror = () => rej(new Error('battle_world.js failed to load'));
    document.head.appendChild(s);
  });
  return { already: false, on: !!(window.BattleWorld && window.BattleWorld.on),
           installed: !!(window.BattleWorld && window.BattleWorld.installed) };
})()`;

const READY = `(async () => {
  for (let i = 0; i < 400; i++) {
    if (window.SIM && window.GS && window.GS.ok && window.Battle && window.Rules && window.THREE
        && window.ORBIT && window.SIM.pos && SIM.floors(SIM.pos().x, SIM.pos().z).length) {
      return { ready: true, three: THREE.REVISION, scene: SIM.bounds().scene,
               pos: SIM.pos(), postfx: window.__postfx || null,
               env: !!(typeof scene !== 'undefined' && scene.environment),
               tone: (typeof R !== 'undefined') ? R.toneMapping : null };
    }
    await new Promise(r => setTimeout(r, 200));
  }
  return { ready: false };
})()`;

// ---- MODE: place ----------------------------------------------------------
// The distribution, not the best case. For each sample point: teleport, settle,
// then ask the solver. Records why each failure failed and how far each body had
// to drop, plus the slope across the whole footprint.
const placeDriver = (pts) => `(async () => {
  const PTS = ${JSON.stringify(pts)};
  const out = [];
  const slots = BattleWorld.slotsFor([{id:'vesper'},{id:'maren'}], [{id:'m0'},{id:'m1'}]);
  const FIGHT = ['meadow','forest','crag','water'];   // encounters.js: roads rate 0
  for (const p of PTS) {
    // WHERE A FIGHT ACTUALLY FIRES. The road itself never spawns one, so each road
    // cell is walked PERPENDICULAR into the first neighbouring encounter zone the
    // player could really be standing in. A sample the player cannot occupy is
    // reported as such rather than counted as a placement failure.
    let landed = null;
    for (const r of [5, 8, 11]) {
      for (const a of [0, 1, 2, 3, 4, 5, 6, 7]) {
        const th = a * Math.PI / 4;
        const x = p[0] + Math.cos(th) * r, z = p[1] + Math.sin(th) * r;
        const zn = SIM.zone(x, z);
        if (!zn || FIGHT.indexOf(zn) < 0) continue;
        const f = SIM.floors(x, z);
        if (!f.length) continue;
        SIM.tp(x, z, f[0]);
        SIM.tick(3);
        const P = SIM.pos();
        // the player must really be there: tp settles, and a settle that fell
        // through the world (below the region's bound) is not a sample
        if (!isFinite(P.y) || Math.abs(P.y - f[0]) > 3) continue;
        landed = { P, zone: SIM.zone(P.x, P.z), off: r };
        break;
      }
      if (landed) break;
    }
    if (!landed) { out.push({ from: p, ok: null, why: 'no standable encounter cell within 11 m of this road cell' }); continue; }
    const P = landed.P;
    // TWO NUMBERS, because they are two different claims: what a naive "stage it
    // where the camera already points" gives, and what the shipped solver (which
    // sweeps the arena's yaw for a clear view) gives at the same spot.
    const fixed = BattleWorld.solveFixed({ slots });
    const plan = BattleWorld.solveArena({ slots });
    // the footprint measured RAW as well as solved: the ideal (un-jittered) slot
    // positions, so a pass rate can be read against the terrain that produced it
    const raw = [];
    for (const s of slots) {
      const b = plan.basis;
      const ax = s.ax * BattleWorld.CFG.scale, az = s.az * BattleWorld.CFG.scale;
      const x = P.x + b.right[0]*ax + b.fwd[0]*az, z = P.z + b.right[1]*ax + b.fwd[1]*az;
      const g = SIM.ground(x, z, P.y);
      const bl = g == null ? null : SIM.blocked(x, z, g);
      raw.push({ id: s.id, g: g == null ? null : +(g - P.y).toFixed(2), blocked: bl });
    }
    const ys = plan.placed.map(r => r.y);
    const relief = ys.length ? Math.max(...ys) - Math.min(...ys) : null;
    out.push({ x:+P.x.toFixed(2), y:+P.y.toFixed(2), z:+P.z.toFixed(2), zone: landed.zone, off: landed.off,
               ok: plan.ok, placed: plan.placed.length, failed: plan.failed.length,
               fixedOk: fixed.ok, fixedPlaced: fixed.placed.length, fixedOccluded: fixed.occluded,
               yawDelta: plan.yawDelta,
               relief: relief == null ? null : +relief.toFixed(2),
               drops: plan.placed.map(r => r.drop),
               tries: plan.placed.map(r => r.tries),
               raw: raw,
               rawNoFloor: raw.filter(r => r.g == null).length,
               rawBlocked: raw.filter(r => r.blocked).length,
               rawBlockers: raw.filter(r => r.blocked).map(r => r.blocked),
               why: plan.failed.length ? plan.failed[0].why : null });
  }
  return out;
})()`;

// ---- MODE: place --relocate=<maxR> ----------------------------------------
// Same 160 road cells, same solver, same knobs — but the walk does not stop at
// the first standable encounter cell. Rings out to maxR, 8 bearings a ring (odd
// rings past 11 m offset half a step so bearings decorrelate), FIRST ring whose
// candidate the shipped solver accepts wins. The first three rings are 5/8/11 m
// at bearing 0, which is `placeDriver`'s own ladder to the line, so `first` is
// exactly the cell the control staged on and `zone0` is the control's zone label.
const relocDriver = (pts, rings, cap) => `(async () => {
  const PTS = ${JSON.stringify(pts)};
  const RINGS = ${JSON.stringify(rings)};
  const CAP = ${cap};
  const YAWS = [0, 0.5, -0.5, 1.05, -1.05, 1.6, -1.6, 2.1, -2.1, Math.PI];  // solveArena's own list
  const out = [];
  const slots = BattleWorld.slotsFor([{id:'vesper'},{id:'maren'}], [{id:'m0'},{id:'m1'}]);
  const FIGHT = ['meadow','forest','crag','water'];
  const base = (window.ORBIT && window.ORBIT.yaw) || 0;
  const PIT = (BattleWorld.CAM && BattleWorld.CAM.on) ? BattleWorld.CAM.solve.pitches.slice()
                                                      : [BattleWorld.CFG.cam.pitch];
  const VERIFY = ${VERIFY ? 'true' : 'false'};
  let mismatch = 0, verified = 0;
  const bucket = (w) => !w ? 'null'
      : (/^blocked by /.test(w) ? w
      : (/^only \\d+% of the body/.test(w) ? 'nine-sample body visibility < visMin'
      : w));
  // THE SOUND CHEAP SCREEN. vis:false is a strict relaxation of vis:true, so a
  // yaw that cannot lay the formation down geometrically cannot place with the
  // camera test on either. Returns the yaws that survive — solveArena's verdict
  // depends on NO OTHER yaw, so evaluating only these gives the same ok/not-ok
  // for a fraction of the raycasts. ('--verify' proves it against the real
  // solveArena on every candidate — plain quotes: a backtick in a comment
  // inside a template literal ends the literal, CLAUDE.md's own trap.)
  const geom = (P) => {
    const whys = []; const viable = [];
    for (const d of YAWS) {
      const p = BattleWorld.solveFixed({ slots: slots, at: P, yaw: base + d, pitch: 0.27, vis: false });
      if (p.ok) viable.push(d);
      else for (const f of p.failed) whys.push(bucket(f.why));
    }
    return { ok: viable.length > 0, viable: viable, whys: whys };
  };
  // the shipped test, restricted to the surviving yaws
  const feasible = (P, viable, sink) => {
    for (const d of viable) {
      for (const pit of PIT) {
        const p = BattleWorld.solveFixed({ slots: slots, at: P, yaw: base + d, pitch: pit, vis: true });
        if (p.ok) return true;
        if (sink) for (const f of p.failed) sink(bucket(f.why));
      }
    }
    return false;
  };
  for (const p of PTS) {
    const t0 = performance.now();
    let first = null, staged = null, cands = 0, screened = 0, solved = 0, capped = false, yawsViable = 0;
    const whyCount = {};
    const bump = (s) => { whyCount[s] = (whyCount[s] || 0) + 1; };
    for (let ri = 0; ri < RINGS.length && !staged && !capped; ri++) {
      const R = RINGS[ri];
      const ph = (ri % 2 && R > 11) ? Math.PI / 8 : 0;
      for (let a = 0; a < 8; a++) {
        const th = ph + a * Math.PI / 4;
        const x = p[0] + Math.cos(th) * R, z = p[1] + Math.sin(th) * R;
        const zn = SIM.zone(x, z);
        if (!zn || FIGHT.indexOf(zn) < 0) continue;
        const f = SIM.floors(x, z);
        if (!f.length) continue;
        SIM.tp(x, z, f[0]);
        SIM.tick(3);
        const P = SIM.pos();
        if (!isFinite(P.y) || Math.abs(P.y - f[0]) > 3) continue;
        cands++;
        if (!first) first = { x:+P.x.toFixed(2), y:+P.y.toFixed(2), z:+P.z.toFixed(2),
                              R: R, zone: SIM.zone(P.x, P.z) };
        const g = geom(P);
        if (VERIFY) {
          const truth = BattleWorld.solveArena({ slots: slots });
          const mine = g.ok && feasible(P, g.viable, null);
          verified++;
          if (!!(truth && truth.ok) !== !!mine) mismatch++;
        }
        if (!g.ok) { screened++; for (const w of g.whys) bump(w); continue; }
        solved++;
        yawsViable += g.viable.length;
        if (feasible(P, g.viable, bump)) {
          const plan = BattleWorld.solveArena({ slots: slots });   // the shipped plan, for its yaw/relief
          staged = { x:+P.x.toFixed(2), y:+P.y.toFixed(2), z:+P.z.toFixed(2), R: R,
                     zone: SIM.zone(P.x, P.z), yawDelta: plan ? plan.yawDelta : null,
                     planOk: !!(plan && plan.ok),
                     d: +Math.hypot(P.x - p[0], P.z - p[1]).toFixed(2),
                     relief: plan ? plan.relief : null };
          break;
        }
        if (solved >= CAP) { capped = true; break; }
      }
    }
    const whys = Object.entries(whyCount).sort((a,b) => b[1]-a[1]).slice(0, 6);
    out.push({ from: p, zone0: first ? first.zone : null, first: first,
               ok: !!staged, staged: staged, capped: capped,
               cands: cands, screened: screened, solved: solved, yawsViable: yawsViable,
               ms: Math.round(performance.now() - t0), whys: whys });
  }
  return { rows: out, verified: verified, mismatch: mismatch };
})()`;

// ---- MODE: battle ---------------------------------------------------------
// The five beats the audit photographed, off the real page, at a real spot.
const battleDriver = (spot, opts) => `(async () => {
  const GS = window.GS, B = window.Battle, RU = window.Rules;
  GS.setFlags({ 'maren-joined': true });
  const f = SIM.floors(${spot[0]}, ${spot[1]});
  SIM.tp(${spot[0]}, ${spot[1]}, f.length ? f[0] : null);
  SIM.tick(3);
  ${opts && opts.yaw != null ? `window.ORBIT.yaw = ${opts.yaw};` : ''}
  const pos0 = SIM.pos(), orbit0 = Object.assign({}, window.ORBIT);
  const info0 = { geo: R.info.memory.geometries, tex: R.info.memory.textures,
                  calls: R.info.render.calls, tris: R.info.render.triangles };
  const items = GS.data.items.items, growth = GS.data.growth;
  const party = GS.activeParty().filter(c => ['vesper','maren'].indexOf(c.id) >= 0)
                 .map(c => RU.derive.partyMember(growth, items, c));
  const zone = SIM.zone(pos0.x, pos0.z) || 'meadow';
  const zd = GS.data.encounters.zones[zone] || GS.data.encounters.zones.meadow;
  const p = B.start({ zone: zone, group: ${JSON.stringify(opts.group)}, seed: 4242,
                      backdrop: zd && zd.battleBackdrop }, party, { speed: 1 });
  p.then(()=>{}, ()=>{});
  const S = () => (window.__EBB_SCREEN && window.__EBB_SCREEN.stage) || null;
  for (let i = 0; i < 250 && !S(); i++) await new Promise(r => setTimeout(r, 100));
  const st = S();
  if (!st) return { ok:false, why:'no stage', plan: window.__BW_LAST_PLAN || null };
  const f0 = st.frames;
  for (let i = 0; i < 260; i++) {
    const t = st.tiers();
    if (Object.values(t).every(v => v !== 'proxy') && st.frames > f0 + 100) break;
    await new Promise(r => setTimeout(r, 100));
  }
  const shots = {};
  const grab = () => st.snapshot();
  await new Promise(r => setTimeout(r, 700));
  shots.opening = grab();
  // AN ID IS NOT A SIDE — /^m/ MATCHES 'maren'. BOTH arenas carry sides() now
  // (battle_world.js :1427, battle_stage3d.js :3259), the per-body value
  // newBody() was constructed with. Ask the stage, say which path answered, and
  // keep the kernel's id scheme only as a labelled last resort.
  let sidesVia = 'stage.sides()';
  let sides = st.sides ? st.sides() : null;
  if (!sides && st.at) { sidesVia = 'stage.at().side'; sides = {}; for (const k of Object.keys(st.tiers())) { const a = st.at(k); if (a && a.side) sides[k] = a.side; } }
  if (!sides || !Object.keys(sides).length) { sidesVia = 'id-pattern-fallback'; sides = {}; for (const k of Object.keys(st.tiers())) sides[k] = /^m\d+$/.test(k) ? 'foe' : 'party'; }
  const foes = Object.keys(st.tiers()).filter(k => sides[k] === 'foe');
  const allies = Object.keys(st.tiers()).filter(k => sides[k] === 'party');
  if (!foes.length) throw new Error('no foe-side body on the stage: ' + JSON.stringify(sides));
  if (allies.indexOf(foes[0]) >= 0) throw new Error('side resolution returned a party member');
  const sideResolution = { via: sidesVia, party: allies, foes: foes };
  st.setActor('vesper'); st.setTarget(foes[0]);
  st.act('vesper', 'attack');
  await new Promise(r => setTimeout(r, 210));
  shots.swing = grab();
  await new Promise(r => setTimeout(r, 60));
  st.flinch(foes[0]);
  await new Promise(r => setTimeout(r, 70));
  shots.impact = grab();
  await new Promise(r => setTimeout(r, 500));
  st.ko(foes[0]);
  await new Promise(r => setTimeout(r, 340));
  shots.ko = grab();
  await new Promise(r => setTimeout(r, 900));
  shots.koSettled = grab();
  st.cheer();
  await new Promise(r => setTimeout(r, 500));
  shots.cheer = grab();
  // FPS, in PRESENTED FRAMES (rAF), over 3 s while the fight is up
  let nf = 0, stopf = false; const t0 = performance.now();
  const tk = () => { nf++; if (!stopf) requestAnimationFrame(tk); };
  requestAnimationFrame(tk);
  await new Promise(r => setTimeout(r, 3000));
  stopf = true;
  const fps = nf / ((performance.now() - t0) / 1000);
  const info1 = { geo: R.info.memory.geometries, tex: R.info.memory.textures,
                  calls: R.info.render.calls, tris: R.info.render.triangles };
  // anchors, for the framing census the audit ran on the diorama
  const rect = R.domElement.getBoundingClientRect();
  const anchors = {};
  for (const id of Object.keys(st.tiers())) { const a = st.anchor(id); if (a) anchors[id] = { x:+a.x.toFixed(0), y:+a.y.toFixed(0), h:+a.h.toFixed(0), vis:a.vis }; }
  return { ok:true, zone, pos0, orbit0, plan: st.plan || null, tiers: st.tiers(),
           clips: Object.keys(st.tiers()).reduce((o,k)=>(o[k]=st.clipsOf(k),o),{}),
           frames: st.frames, framesGained: st.frames - f0, fps:+fps.toFixed(1),
           info0, info1, anchors, canvas:[rect.width, rect.height],
           world: !!st.world, sideResolution, shots };
})()`;

// ---- MODE: fps / teardown -------------------------------------------------
const TEARDOWN = `(async () => {
  const base = { geo: R.info.memory.geometries, tex: R.info.memory.textures,
                 progs: R.info.programs ? R.info.programs.length : null,
                 sceneKids: scene.children.length,
                 collide: (typeof collide !== 'undefined') ? collide.length : null,
                 allMeshes: (typeof allMeshes !== 'undefined') ? allMeshes.length : null,
                 canvases: document.querySelectorAll('canvas').length,
                 orbit: Object.assign({}, window.ORBIT), pos: SIM.pos(),
                 chVisible: (typeof ch !== 'undefined') ? ch.visible : null,
                 at: (window.GS && GS.state && GS.state.at) ? Object.assign({}, GS.state.at) : null,
                 save: localStorage.getItem('emberbrook-save') };
  let sceneEvents = 0;
  const onScene = () => { sceneEvents++; };
  window.addEventListener('eb-scene', onScene);
  const GS2 = window.GS, RU = window.Rules;
  GS2.setFlags({ 'maren-joined': true });
  const items = GS2.data.items.items, growth = GS2.data.growth;
  const party = GS2.activeParty().filter(c => ['vesper','maren'].indexOf(c.id) >= 0)
                 .map(c => RU.derive.partyMember(growth, items, c));
  const zone = SIM.zone() || 'meadow';
  const zd = GS2.data.encounters.zones[zone] || GS2.data.encounters.zones.meadow;
  // a REAL battle, played to the end by the autopilot at speed 0 (the harness canon).
  // WHICH PATH RAN IS SAMPLED WHILE IT IS UP: a teardown receipt that cannot say
  // which stage it tore down proves nothing (the world path returns null when the
  // ground refuses, and the diorama answers instead).
  const pr = window.Battle.start({ zone: zone, group: ['reed-nibbler'], seed: 99,
      backdrop: zd && zd.battleBackdrop }, party, { speed: 0, autoplay: true, fade: () => Promise.resolve() });
  let sawWorld = null, sawCanvases = null, sawSite = null;
  for (let i = 0; i < 200; i++) {
    const s = window.__EBB_SCREEN && window.__EBB_SCREEN.stage;
    if (s) { sawWorld = !!s.world; sawCanvases = document.querySelectorAll('canvas').length;
             sawSite = s.site || null; break; }
    await new Promise(r => setTimeout(r, 50));
  }
  const res = await pr;
  await new Promise(r => setTimeout(r, 600));
  window.removeEventListener('eb-scene', onScene);
  const after = { geo: R.info.memory.geometries, tex: R.info.memory.textures,
                  progs: R.info.programs ? R.info.programs.length : null,
                  sceneKids: scene.children.length,
                  collide: (typeof collide !== 'undefined') ? collide.length : null,
                  allMeshes: (typeof allMeshes !== 'undefined') ? allMeshes.length : null,
                  canvases: document.querySelectorAll('canvas').length,
                  orbit: Object.assign({}, window.ORBIT), pos: SIM.pos(),
                  chVisible: (typeof ch !== 'undefined') ? ch.visible : null,
                  at: (window.GS && GS.state && GS.state.at) ? Object.assign({}, GS.state.at) : null,
                  save: localStorage.getItem('emberbrook-save') };
  // does a lone bw_ node survive anywhere in the graph?
  let residue = [];
  scene.traverse(o => { if (o.userData && o.userData.isBattleWorld) residue.push(o.name || '(anon)'); });
  const roots = document.querySelectorAll('.ebb-root').length;
  return { outcome: res && res.outcome, sawWorldStage: sawWorld, canvasesDuringBattle: sawCanvases,
           sawSite: sawSite,
           bwCreated: window.BattleWorld ? window.BattleWorld.created : null,
           bwRefused: window.BattleWorld ? window.BattleWorld.refused : null,
           plan: window.__BW_LAST_PLAN ? { ok: window.__BW_LAST_PLAN.ok, failed: window.__BW_LAST_PLAN.failed } : null,
           base, after, residue, ebbRoots: roots,
           sceneEvents, uilock: !!(window.UILOCK && UILOCK.active()),
           battleActive: !!window.Battle.active };
})()`;

// ---- MODE: stageperf ------------------------------------------------------
// A BATTLE MUST NOT TAKE SECONDS TO START, so the ladder is timed on the path a
// battle actually walks: BattleWorld.stage(), the same call createWorldStage
// makes, at real cells the player can stand on. Cells come from placement.json,
// which labels each one with the OLD single-solve verdict — so the sample can be
// split into the fast path (cells that stage where the player stands) and the
// SLOW PATH (cells the old search refused, which are now the ones that walk the
// rings). Reports both, because a p95 taken only over cells that never relocate
// is not a measurement of relocation.
const stageDriver = (pts) => `(async () => {
  const PTS = ${JSON.stringify(pts)};
  const out = [];
  const slots = BattleWorld.slotsFor([{id:'vesper'},{id:'maren'}], [{id:'m0'},{id:'m1'}]);
  for (const p of PTS) {
    const f = SIM.floors(p.x, p.z) || [];
    let y = f.length ? f[0] : p.y;
    for (const v of f) if (Math.abs(v - p.y) < Math.abs(y - p.y)) y = v;
    SIM.tp(p.x, p.z, y);
    SIM.tick(3);
    const P = SIM.pos();
    if (!isFinite(P.y) || Math.abs(P.y - p.y) > 3) { out.push({ from: [p.x, p.z], was: p.ok, skipped: true }); continue; }
    // THE MEASUREMENT. One call, cold — the occluder set is rebuilt at most every
    // 2 s inside the module, which is the same cache a real battle gets.
    const t0 = performance.now();
    const s = BattleWorld.stage(slots);
    const ms = performance.now() - t0;
    out.push({ from: [p.x, p.z], was: p.ok, ok: !!s.plan, R: s.R,
               d: s.d == null ? 0 : s.d, dy: s.dy == null ? 0 : s.dy,
               bearing: s.bearing == null ? null : s.bearing,
               cands: s.cands, screened: s.screened, solved: s.solved,
               yawDelta: s.plan ? s.plan.yawDelta : null,
               ms: +ms.toFixed(1) });
  }
  return out;
})()`;

// ---- MODE: raycost --------------------------------------------------------
// WHERE THE SECONDS GO. The staging solve is raycasts and nothing else, so this
// splits the bill: the geometry half (ground / blocked, vis:false) against the
// visibility half (vis:true), then times the module's OWN occluder set one mesh
// at a time so the worst offenders can be named rather than guessed at.
const rayDriver = `(async () => {
  const TH = window.THREE;
  const P = SIM.pos();
  const slots = BattleWorld.slotsFor([{id:'vesper'},{id:'maren'}], [{id:'m0'},{id:'m1'}]);
  const base = (window.ORBIT && window.ORBIT.yaw) || 0;
  const t = (f, n) => { const t0 = performance.now(); for (let i = 0; i < n; i++) f(i); return (performance.now() - t0) / n; };
  const msGeom = t(i => BattleWorld.solveFixed({ slots: slots, at: P, yaw: base + i * 0.31, vis: false }), 10);
  const msVis  = t(i => BattleWorld.solveFixed({ slots: slots, at: P, yaw: base + i * 0.31, vis: true  }), 10);
  // the occluder set, as the module builds it
  const set = [];
  scene.traverse(o => {
    if (!(o.isMesh || o.isInstancedMesh) || o.isSkinnedMesh) return;
    if (o.userData && (o.userData.isWalk || o.userData.isBattleWorld)) return;
    if (/^(__owsky|__owridge|__owveil|amb_|bw_)/.test(o.name || '')) return;
    if (o.visible) set.push(o);
  });
  const rc = new TH.Raycaster();
  const dirs = [];
  for (let i = 0; i < 24; i++) dirs.push(new TH.Vector3(Math.cos(i), 0.35, Math.sin(i)).normalize());
  const eye = new TH.Vector3(P.x, P.y + 3.5, P.z);
  const per = [];
  for (const o of set) {
    const t0 = performance.now();
    for (const d of dirs) { rc.set(eye, d); rc.far = 40; rc.intersectObject(o, true); }
    per.push({ name: o.name || '(anon)', us: +((performance.now() - t0) / dirs.length * 1000).toFixed(1),
               tris: o.geometry && o.geometry.index ? o.geometry.index.count / 3
                     : (o.geometry && o.geometry.attributes.position ? o.geometry.attributes.position.count / 3 : null),
               bvh: !!(o.geometry && o.geometry.boundsTree),
               inst: !!o.isInstancedMesh, accel: o.raycast === (window.MeshBVHLib && MeshBVHLib.acceleratedRaycast) });
  }
  per.sort((a, b) => b.us - a.us);
  // WHAT THE EXPENSIVE ONES ACTUALLY ARE. An InstancedMesh raycast loops every
  // instance, so cost tracks instance COUNT and not triangle count — and whether
  // the thing is tall enough to hide a body is the only question that decides
  // whether it belongs in an occluder set at all.
  for (const p of per.slice(0, 15)) {
    const o = set.find(m => (m.name || '(anon)') === p.name);
    if (!o) continue;
    p.count = o.isInstancedMesh ? o.count : 1;
    const bb = new TH.Box3().setFromObject(o);
    p.height = +(bb.max.y - bb.min.y).toFixed(2);
    if (o.isInstancedMesh && o.geometry) {
      o.geometry.computeBoundingBox();
      const g = o.geometry.boundingBox;
      p.pieceH = +((g.max.y - g.min.y) * (o.scale ? o.scale.y : 1)).toFixed(2);
    }
  }
  const t0 = performance.now();
  for (const d of dirs) { rc.set(eye, d); rc.far = 40; rc.intersectObjects(set, true); }
  const usWholeSet = (performance.now() - t0) / dirs.length * 1000;
  // 'set' above is the RAW drawn set — every visible mesh, the rule as it stood
  // before ground scatter was measured out of it. What the module actually uses
  // is its own, so report both: the difference IS the fix. (Plain quotes: a
  // backtick in a comment inside a template literal ends the literal — CLAUDE.md
  // names this trap and it cost this lane one silently stale artifact.)
  const dbg = BattleWorld._debug();
  return { rawDrawnSet: set.length, moduleOccluders: dbg.occluders,
           moduleDropped: dbg.scatterDropped,
           occluders: set.length, withBVH: per.filter(p => p.bvh).length,
           accelerated: per.filter(p => p.accel).length,
           instanced: per.filter(p => p.inst).length,
           bvhStats: SIM.bvh ? SIM.bvh() : null,
           usPerRayWholeSet: +usWholeSet.toFixed(1),
           msSolveGeomOnly: +msGeom.toFixed(1), msSolveWithVis: +msVis.toFixed(1),
           worst: per.slice(0, 15) };
})()`;

// TRIGGER TO FIRST BATTLE FRAME, end to end: the clock starts on Battle.start —
// the call an encounter makes — and stops on the first frame the world stage has
// ticked. Nothing is mocked and the entry fade is included, because the player's
// wait includes it.
const e2eDriver = (spot) => `(async () => {
  const GS2 = window.GS, RU = window.Rules;
  GS2.setFlags({ 'maren-joined': true });
  const f = SIM.floors(${spot[0]}, ${spot[1]}) || [];
  SIM.tp(${spot[0]}, ${spot[1]}, f.length ? f[0] : null);
  SIM.tick(3);
  const pos0 = SIM.pos();
  const items = GS2.data.items.items, growth = GS2.data.growth;
  const party = GS2.activeParty().filter(c => ['vesper','maren'].indexOf(c.id) >= 0)
                 .map(c => RU.derive.partyMember(growth, items, c));
  const zone = SIM.zone(pos0.x, pos0.z) || 'meadow';
  const zd = GS2.data.encounters.zones[zone] || GS2.data.encounters.zones.meadow;
  const t0 = performance.now();
  const pr = window.Battle.start({ zone: zone, group: ['reed-nibbler','reed-nibbler'], seed: 7,
      backdrop: zd && zd.battleBackdrop }, party, { speed: 1 });
  pr.then(()=>{}, ()=>{});
  let tStage = null, tFrame = null, st = null;
  for (let i = 0; i < 1200; i++) {
    const s = window.__EBB_SCREEN && window.__EBB_SCREEN.stage;
    if (s) { st = s; tStage = performance.now() - t0; break; }
    await new Promise(r => requestAnimationFrame(r));
  }
  if (st) for (let i = 0; i < 600; i++) {
    if (st.ticks >= 1) { tFrame = performance.now() - t0; break; }
    await new Promise(r => requestAnimationFrame(r));
  }
  const site = st && st.site ? st.site : null;
  const world = st ? !!st.world : null;
  // tear the fight down again so the next spot starts clean
  try { if (st) st.destroy(); } catch (e) { }
  const s2 = window.__EBB_SCREEN;
  try { if (s2 && s2.destroy) s2.destroy(); } catch (e) { }
  window.__EBB_SCREEN = null; window.Battle.active = false;
  document.querySelectorAll('.ebb-root').forEach(n => n.remove());
  try { window.UILOCK && UILOCK.unlock('battle'); } catch (e) { }
  return { at: [${spot[0]}, ${spot[1]}], world: world, site: site,
           msToStage: tStage == null ? null : +tStage.toFixed(0),
           msToFirstFrame: tFrame == null ? null : +tFrame.toFixed(0) };
})()`;

// FPS IS COUNTED IN rAF CALLBACKS, NOT IN renderer.info.render.frame. The world's
// post chain calls renderer.render() once per PASS (RenderPass + GTAO + grade +
// bloom + Output + AA = 6), so info.render.frame runs at ~6x the frame rate and
// the first version of this probe reported 2653 "fps". A frame is a presented
// frame; only rAF knows how many there were.
const RAFPS = (ms) => `(async () => {
  let n = 0; let stop = false;
  const t0 = performance.now();
  const tick = () => { n++; if (!stop) requestAnimationFrame(tick); };
  requestAnimationFrame(tick);
  await new Promise(r => setTimeout(r, ${ms}));
  stop = true;
  return { fps: +(n / ((performance.now() - t0) / 1000)).toFixed(1), frames: n };
})()`;

const FPSDRIVE = (worldMode) => `(async () => {
  const GS = window.GS, RU = window.Rules;
  GS.setFlags({ 'maren-joined': true });
  if (window.BattleWorld && !Object.isFrozen(window.BattleWorld)) window.BattleWorld.enabled = ${worldMode ? 'true' : 'false'};
  const items = GS.data.items.items, growth = GS.data.growth;
  const party = GS.activeParty().filter(c => ['vesper','maren'].indexOf(c.id) >= 0)
                 .map(c => RU.derive.partyMember(growth, items, c));
  const zone = SIM.zone() || 'meadow';
  const zd = GS.data.encounters.zones[zone] || GS.data.encounters.zones.meadow;
  const p = window.Battle.start({ zone: zone, group: ['duskpad','duskpad'], seed: 4242,
      backdrop: zd && zd.battleBackdrop }, party, { speed: 1 });
  p.then(()=>{},()=>{});
  const S = () => (window.__EBB_SCREEN && window.__EBB_SCREEN.stage) || null;
  for (let i = 0; i < 250 && !S(); i++) await new Promise(r => setTimeout(r, 100));
  const st = S(); if (!st) return { ok:false, why:'no stage' };
  for (let i = 0; i < 200; i++) { if (Object.values(st.tiers()).every(v=>v!=='proxy')) break; await new Promise(r=>setTimeout(r,100)); }
  await new Promise(r => setTimeout(r, 1200));
  let n = 0, stop = false;
  const t0 = performance.now();
  const tick = () => { n++; if (!stop) requestAnimationFrame(tick); };
  requestAnimationFrame(tick);
  const f0 = st.frames;
  await new Promise(r => setTimeout(r, 4000));
  stop = true;
  const dt = (performance.now() - t0) / 1000;
  const fps = n / dt;
  const r = { ok:true, world: !!st.world, fps:+fps.toFixed(1), dt:+dt.toFixed(2),
              plan: window.__BW_LAST_PLAN ? { ok: window.__BW_LAST_PLAN.ok, failed: window.__BW_LAST_PLAN.failed } : null,
              bw: (window.BattleWorld && window.BattleWorld._debug) ? window.BattleWorld._debug()
                  : (window.BattleWorld ? Object.assign({}, window.BattleWorld) : null),
              rendersPerFrame: +((st.frames - f0) / n).toFixed(2),
              calls: R.info.render.calls, tris: R.info.render.triangles,
              geo: R.info.memory.geometries, tex: R.info.memory.textures,
              canvases: document.querySelectorAll('canvas').length,
              dpr: st.renderer ? st.renderer.getPixelRatio() : null,
              bodies: Object.keys(st.tiers()).length };
  try { window.__EBB_SCREEN && window.__EBB_SCREEN.stage && window.__EBB_SCREEN.stage.destroy(); } catch(e){}
  try { window.__EBB_SCREEN && window.__EBB_SCREEN.destroy(); } catch(e){}
  document.querySelectorAll('.ebb-root').forEach(n=>n.remove());
  window.__EBB_SCREEN = null; window.Battle.active = false;
  try { window.UILOCK && UILOCK.unlock('battle'); } catch(e){}
  await new Promise(r => setTimeout(r, 500));
  return r;
})()`;

(async function main() {
  mkdirSync(OUT, { recursive: true });
  const cdp = await connect(await findPage(CDP_PORT, { tries: 250, label: 'battle_world_probe' }));
  await cdp.send('Runtime.enable');
  await cdp.send('Page.enable');
  const errs = [];
  cdp.send('Log.enable').catch(() => { });
  const ready = await ev(cdp, READY, 120000);
  if (!ready.ready) { console.error('world never became ready'); kill(); process.exit(2); }
  console.log(`world ready  three r${ready.three}  scene=${ready.scene}  env=${ready.env}  tone=${ready.tone}`);
  console.log('postfx:', JSON.stringify(ready.postfx));

  // ---- RAY-BUDGET PREFLIGHT (tools/ray_budget.mjs) -------------------------
  // EVERY MODE, before any of them measures anything. This probe runs on a REAL
  // GPU (no swiftshader flags above, unlike every other headless gate here), which
  // makes it the one instrument in the repo that can see ow_detail's runtime
  // scatter — and the scatter is where the 32-second staging solve came from.
  // `--mode=raycost` already bills a ray per mesh; what was missing was anyone
  // ASSERTING on the bill. `--no-raybudget` skips it. A red preflight aborts:
  // every number this probe would print next is a measurement of a defect, and
  // publishing those as if they described the shipped game is how a stale artifact
  // becomes a canon note.
  if (!argv.includes('--no-raybudget')) {
    const rb = await ev(cdp, censusExpr({ timing: true }), 300000);
    const rv = rayVerdict(rb);
    console.log(`ray budget: ${rv.state}  ${rv.why}` +
                (rb && rb.usPerRay != null ? `   [${rb.usPerRay} us/ray measured on this machine]` : ''));
    if (!rv.ok) {
      console.error('ray-budget preflight FAILED — refusing to measure a defective world. ' +
                    'Run `node tools/ray_budget.mjs --port=' + PORT + '` for the full census, ' +
                    'or pass --no-raybudget to measure anyway.');
      cdp.close(); kill(); process.exit(3);
    }
  }

  if (MODE === 'regress') {
    // THE DEFAULT-PATH PROOF. No flag in the URL; inject the module anyway (this
    // is the worst case for the patch play3d would carry — the file present on
    // every page) and assert it did nothing at all, then fight a real battle and
    // assert the DIORAMA answered.
    const inj = await ev(cdp, INJECT, 60000);
    const bw = await ev(cdp, `JSON.parse(JSON.stringify(window.BattleWorld))`);
    const r = await ev(cdp, FPSDRIVE(false), 300000);
    const patched = await ev(cdp, `!!(window.BattleStage3D && window.BattleStage3D.__bwPatched)`);
    const out = { inject: inj, battleWorld: bw, patchedStage3d: patched, battle: r };
    console.log(JSON.stringify(out, null, 2));
    writeFileSync(join(OUT, 'regress.json'), JSON.stringify(out, null, 2));
    cdp.close(); kill(); process.exit(0);
  }

  const inj = await ev(cdp, INJECT, 60000);
  console.log('inject:', JSON.stringify(inj));

  // THE KNOBS, APPLIED AND READ BACK OUT OF THE MODULE. A run that says which
  // arm of the factorial it is cannot be mistaken for another arm's numbers.
  const knobs = await ev(cdp, `(() => {
    const BW = window.BattleWorld;
    if (!BW) return { ok: false };
    ${VISMIN == null ? '' : `BW.CFG.place.visMin = ${parseFloat(VISMIN)};`}
    ${BCAM == null ? '' : `BW.CAM.on = ${BCAM === '0' || BCAM === 'false' ? 'false' : 'true'};`}
    ${PITCHES == null ? '' : `BW.CAM.solve.pitches = ${JSON.stringify(PITCHES.split(',').map(parseFloat))};`}
    ${BPLACE == null ? '' : `if (BW.PLACE) BW.PLACE.on = ${BPLACE === '0' || BPLACE === 'false' ? 'false' : 'true'};`}
    return { ok: true, visMin: BW.CFG.place.visMin, camOn: BW.CAM.on,
             pitches: BW.CAM.solve.pitches.slice(),
             placeOn: BW.PLACE ? BW.PLACE.on : null,
             sunMargin: BW.PLACE ? BW.PLACE.sunMargin : null };
  })()`, 30000);
  console.log(`knobs: visMin=${knobs.visMin}  CAM.on=${knobs.camOn}  pitches=[${knobs.pitches}]`
            + `   [vis test = ${knobs.visMin > 0 ? 'NINE-SAMPLE (new)' : 'TWO SPINE RAYS (old)'};`
            + ` sweep = ${knobs.camOn ? (knobs.pitches.length > 1 ? 'yaw x pitch, best (new)' : 'yaw only, BEST (isolated)') : 'yaw only, first (old)'};`
            + ` placement quality = ${knobs.placeOn === null ? 'absent' : (knobs.placeOn ? 'ON, sunMargin ' + knobs.sunMargin : 'OFF (first acceptance)')}]`);

  if (MODE === 'raycost') {
    await ev(cdp, `SIM.tp(-66.88, 45.62, (SIM.floors(-66.88,45.62)||[0])[0]); SIM.tick(3); true`);
    const r = await ev(cdp, rayDriver, 600000);
    console.log(JSON.stringify(r, null, 2));
    writeFileSync(join(OUT, 'raycost.json'), JSON.stringify(r, null, 2));
    cdp.close(); kill(); process.exit(0);
  }

  if (MODE === 'stageperf') {
    const src = JSON.parse(readFileSync(join(OUT, 'placement.json'), 'utf8')).rows
      .filter(r => r.ok !== null && isFinite(r.x));
    // BOTH PATHS, INTERLEAVED, so a drifting machine cannot be mistaken for a
    // difference between them: every other cell is one the old search refused.
    const good = src.filter(r => r.ok), bad = src.filter(r => !r.ok);
    const half = Math.max(1, Math.floor(N / 2));
    const pick = [];
    for (let i = 0; i < half; i++) {
      if (bad[i]) pick.push(bad[i]);
      if (good[i]) pick.push(good[i]);
    }
    console.log(`stageperf: ${pick.length} cells (${pick.filter(r => !r.ok).length} the old search REFUSED), rings [${'0,5,8,11,13'}]`);
    const rows = [];
    const CH = 3;
    const t0 = Date.now();
    for (let i = 0; i < pick.length; i += CH) {
      const r = await ev(cdp, stageDriver(pick.slice(i, i + CH)), 900000);
      rows.push(...r);
      const el = (Date.now() - t0) / 1000;
      process.stdout.write(`  ${rows.length}/${pick.length}  ${el.toFixed(0)}s   \r`);
    }
    const live = rows.filter(r => !r.skipped);
    const srt = a => a.slice().sort((x, y) => x - y);
    const pct = (a, p) => (a.length ? a[Math.min(a.length - 1, Math.floor(a.length * p))] : null);
    const band = (rs) => {
      const ms = srt(rs.map(r => r.ms));
      return { n: rs.length, ok: rs.filter(r => r.ok).length,
               p50: pct(ms, 0.5), p95: pct(ms, 0.95), max: ms[ms.length - 1] };
    };
    // END TO END, WORST-CASE-WEIGHTED: the five slowest cells this sample found,
    // five spread evenly through the rest, and a control that stages where the
    // player stands. A p95 taken over easy cells is not a worst case.
    const bySlow = live.slice().sort((a, b) => b.ms - a.ms);
    const worst = bySlow.slice(0, 5).map(r => r.from);
    const rest = bySlow.slice(5);
    const spread = [];
    for (let i = 0; i < 5 && rest.length; i++) spread.push(rest[Math.floor(i * rest.length / 5)].from);
    const control = (live.find(r => r.was && r.R === 0) || live[0]).from;
    const e2e = [];
    for (const sp of [control].concat(worst, spread)) {
      process.stdout.write(`\n  e2e ${sp} ... `);
      try { const r = await ev(cdp, e2eDriver(sp), 300000); e2e.push(r); console.log(`${r.msToFirstFrame} ms  world=${r.world}  moved=${r.site ? r.site.d : '?'} m`); }
      catch (err) { console.log('EXCEPTION ' + err.message); e2e.push({ at: sp, error: err.message }); }
      await sleep(800);
    }
    const e2ems = srt(e2e.filter(r => r.msToFirstFrame != null).map(r => r.msToFirstFrame));
    const summary = {
      arm: { visMin: knobs.visMin, camOn: knobs.camOn, pitches: knobs.pitches,
             placeOn: knobs.placeOn, sunMargin: knobs.sunMargin },
      sampled: live.length, skipped: rows.length - live.length,
      ok: live.filter(r => r.ok).length,
      rate: +(live.filter(r => r.ok).length / Math.max(1, live.length) * 100).toFixed(1),
      solve_ms_all: band(live),
      solve_ms_oldRefused: band(live.filter(r => !r.was)),
      solve_ms_oldStaged: band(live.filter(r => r.was)),
      ringHistogram: [0, 5, 8, 11, 13].map(R => [R, live.filter(r => r.ok && r.R === R).length]),
      dist: { p50: pct(srt(live.filter(r => r.ok).map(r => r.d)), 0.5),
              p90: pct(srt(live.filter(r => r.ok).map(r => r.d)), 0.9),
              max: srt(live.filter(r => r.ok).map(r => r.d)).slice(-1)[0] },
      e2e_ms_toFirstFrame: { n: e2ems.length, p50: pct(e2ems, 0.5), p95: pct(e2ems, 0.95), max: e2ems[e2ems.length - 1] },
      e2e: e2e,
      residual: live.filter(r => !r.ok).map(r => r.from),
    };
    console.log('\n' + JSON.stringify(summary, null, 2));
    writeFileSync(join(OUT, 'stageperf.json'), JSON.stringify({ summary, rows }, null, 2));
    cdp.close(); kill(); process.exit(0);
  }

  if (MODE === 'place' && RELOC != null) {
    const maxR = parseFloat(RELOC);
    const rings = RINGS.split(',').map(parseFloat).filter(r => r <= maxR + 1e-6);
    const all = JSON.parse(readFileSync(arg('pts', join(ROOT, 'tools/_bw_roadpts.json')), 'utf8'));
    const pts = all.slice(0, N);
    console.log(`relocate: rings [${rings}] m x 8 bearings, solve cap ${SOLVECAP}/cell, ${pts.length} road cells`);
    const rows = [];
    let vTot = 0, vMis = 0;
    const CH = 4;
    const t0 = Date.now();
    for (let i = 0; i < pts.length; i += CH) {
      const r = await ev(cdp, relocDriver(pts.slice(i, i + CH), rings, SOLVECAP), 1800000);
      rows.push(...r.rows); vTot += r.verified; vMis += r.mismatch;
      const el = (Date.now() - t0) / 1000;
      process.stdout.write(`  ${rows.length}/${pts.length}  ${el.toFixed(0)}s  eta ${(el / rows.length * (pts.length - rows.length)).toFixed(0)}s   \r`);
    }
    const ZONES = ['meadow', 'forest', 'crag', 'water'];
    const zoneOf = r => r.zone0 || 'null';
    const nZone = {}; for (const r of rows) nZone[zoneOf(r)] = (nZone[zoneOf(r)] || 0) + 1;
    // coverage(R) = cells whose FIRST ACCEPTING RING is <= R. One run, whole curve.
    const curve = rings.map(R => {
      const inR = rows.filter(r => r.ok && r.staged.R <= R);
      const byZone = {};
      for (const z of Object.keys(nZone)) {
        byZone[z] = { n: nZone[z], ok: inR.filter(r => zoneOf(r) === z).length };
      }
      return { R, ok: inR.length, of: rows.length,
               rate: +(inR.length / Math.max(1, rows.length) * 100).toFixed(1), byZone };
    });
    const moved = rows.filter(r => r.ok).map(r => r.staged.d).sort((a, b) => a - b);
    const movedBeyond = rows.filter(r => r.ok && r.staged.R > 11).map(r => r.staged.d).sort((a, b) => a - b);
    const pct = (a, p) => (a.length ? a[Math.min(a.length - 1, Math.floor(a.length * p))] : null);
    const residual = rows.filter(r => !r.ok);
    const resWhy = {};
    for (const r of residual) for (const [w, c] of r.whys) resWhy[w] = (resWhy[w] || 0) + c;
    const summary = {
      arm: { visMin: knobs.visMin, camOn: knobs.camOn, pitches: knobs.pitches,
             visTest: knobs.visMin > 0 ? 'nine-sample' : 'two-spine-rays',
             sweep: knobs.camOn ? (knobs.pitches.length > 1 ? 'yaw x pitch (best)' : 'yaw only (best)') : 'yaw only (first)',
             relocate: maxR, rings, solveCap: SOLVECAP },
      verify: VERIFY ? { candidates: vTot, mismatchVsSolveArena: vMis } : null,
      sampled: rows.length, ok: rows.filter(r => r.ok).length, fail: residual.length,
      rate: +(rows.filter(r => r.ok).length / Math.max(1, rows.length) * 100).toFixed(1),
      capped: rows.filter(r => r.capped).length,
      curve,
      dist_all: { p50: pct(moved, 0.5), p90: pct(moved, 0.9), max: moved[moved.length - 1] },
      dist_relocated: { n: movedBeyond.length, p50: pct(movedBeyond, 0.5), p90: pct(movedBeyond, 0.9),
                        max: movedBeyond[movedBeyond.length - 1] },
      ringHistogram: rings.map(R => [R, rows.filter(r => r.ok && r.staged.R === R).length]),
      residual: residual.map(r => ({ from: r.from, zone0: r.zone0, cands: r.cands,
                                     screened: r.screened, solved: r.solved, capped: r.capped,
                                     whys: r.whys })),
      residualWhy: Object.entries(resWhy).sort((a, b) => b[1] - a[1]).slice(0, 12),
      cost: { candTotal: rows.reduce((s, r) => s + r.cands, 0),
              screenedTotal: rows.reduce((s, r) => s + r.screened, 0),
              solvedTotal: rows.reduce((s, r) => s + r.solved, 0),
              msTotal: rows.reduce((s, r) => s + r.ms, 0) },
    };
    console.log('\n' + JSON.stringify(summary, null, 2));
    writeFileSync(join(OUT, 'relocate.json'), JSON.stringify({ summary, rows }, null, 2));
    cdp.close(); kill(); process.exit(0);
  }

  if (MODE === 'place') {
    const all = JSON.parse(readFileSync(arg('pts', join(ROOT, 'tools/_bw_roadpts.json')), 'utf8'));
    const pts = all.slice(0, N);
    const rows = [];
    const CH = 20;
    for (let i = 0; i < pts.length; i += CH) {
      const r = await ev(cdp, placeDriver(pts.slice(i, i + CH)), 300000);
      rows.push(...r);
      process.stdout.write(`  ${rows.length}/${pts.length}\r`);
    }
    const usable = rows.filter(r => r.ok !== null);
    const skipped = rows.filter(r => r.ok === null);
    const ok = usable.filter(r => r.ok);
    const bad = usable.filter(r => !r.ok);
    const byZone = {};
    for (const r of usable) { const z = r.zone || 'null'; byZone[z] = byZone[z] || { n: 0, ok: 0 }; byZone[z].n++; if (r.ok) byZone[z].ok++; }
    const sortN = a => a.filter(v => v != null).sort((x, y) => x - y);
    const pct = (a, p) => (a.length ? a[Math.min(a.length - 1, Math.floor(a.length * p))] : null);
    const rel = sortN(ok.map(r => r.relief));
    const relAll = sortN(usable.map(r => r.relief));
    const jit = ok.flatMap(r => r.tries || []);
    const rawNo = usable.reduce((s, r) => s + (r.rawNoFloor || 0), 0);
    const rawBl = usable.reduce((s, r) => s + (r.rawBlocked || 0), 0);
    const blockers = {};
    for (const r of usable) for (const b of (r.rawBlockers || [])) blockers[b] = (blockers[b] || 0) + 1;
    const summary = {
      arm: { visMin: knobs.visMin, camOn: knobs.camOn, pitches: knobs.pitches,
             visTest: knobs.visMin > 0 ? 'nine-sample' : 'two-spine-rays',
             sweep: knobs.camOn
               ? (knobs.pitches.length > 1 ? 'yaw x pitch (best)' : 'yaw only (best)')
               : 'yaw only (first)' },
      sampled: rows.length, skipped: skipped.length, usable: usable.length,
      ok: ok.length, fail: bad.length,
      rate: +(ok.length / Math.max(1, usable.length) * 100).toFixed(1),
      rateFixedYaw: +(usable.filter(r => r.fixedOk).length / Math.max(1, usable.length) * 100).toFixed(1),
      yawTurned: +(ok.filter(r => Math.abs(r.yawDelta || 0) > 0.001).length / Math.max(1, ok.length) * 100).toFixed(1),
      occludedSlotsFixedYaw: usable.reduce((s, r) => s + (r.fixedOccluded || 0), 0),
      byZone,
      relief_ok: { p50: pct(rel, 0.5), p90: pct(rel, 0.9), max: rel[rel.length - 1] },
      relief_all: { p50: pct(relAll, 0.5), p90: pct(relAll, 0.9), max: relAll[relAll.length - 1] },
      // the RAW footprint, before the ring search rescues anything: this is the
      // honest picture of the terrain a fixed formation would land on
      rawSlots: usable.length * 4,
      rawNoFloor: rawNo, rawBlocked: rawBl,
      rawCleanPct: +((usable.length * 4 - rawNo - rawBl) / Math.max(1, usable.length * 4) * 100).toFixed(1),
      blockers: Object.entries(blockers).sort((a, b) => b[1] - a[1]).slice(0, 10),
      firstTryFraction: +(jit.filter(v => v === 1).length / Math.max(1, jit.length) * 100).toFixed(1),
      failWhy: bad.slice(0, 6).map(r => r.why),
    };
    console.log('\n' + JSON.stringify(summary, null, 2));
    writeFileSync(join(OUT, 'placement.json'), JSON.stringify({ summary, rows }, null, 2));
    cdp.close(); kill(); process.exit(0);
  }

  if (MODE === 'battle') {
    // THREE DIFFERENT PLACES, which is the audit's own stated proof for BET A.
    const SPOTS = JSON.parse(arg('spots', JSON.stringify([
      { name: 'road-north', at: [-49.4, 23.1], group: ['reed-nibbler', 'reed-nibbler'] },
      { name: 'gorge', at: [56.9, -41.9], group: ['duskpad', 'bramble-shade'] },
      { name: 'meadow-open', at: [10.6, -16.9], group: ['scree-shell', 'duskpad'] },
    ])));
    const meta = {};
    for (const s of SPOTS) {
      process.stdout.write(`  ${s.name} ... `);
      let r;
      try { r = await ev(cdp, battleDriver(s.at, { group: s.group }), 300000); }
      catch (e) { console.log('EXCEPTION', e.message); meta[s.name] = { ok: false, why: e.message }; continue; }
      if (!r.ok) { console.log('FAILED', r.why, JSON.stringify(r.plan && r.plan.failed)); meta[s.name] = r; continue; }
      for (const [k, uri] of Object.entries(r.shots || {})) {
        if (!uri) continue;
        writeFileSync(join(OUT, `world-${s.name}-${k}.png`), Buffer.from(uri.slice(uri.indexOf(',') + 1), 'base64'));
      }
      const full = await cdp.send('Page.captureScreenshot', { format: 'png' });
      writeFileSync(join(OUT, `world-${s.name}-full.png`), Buffer.from(full.data, 'base64'));
      delete r.shots;
      meta[s.name] = r;
      console.log(`ok  fps=${r.fps}  frames+${r.framesGained}  tiers=${JSON.stringify(r.tiers)}`);
      // SAY WHICH PATH RESOLVED THE SIDES, and prove the map partitions the roster.
      if (r.sideResolution) {
        const sr = r.sideResolution, ids = Object.keys(r.tiers || {});
        const cover = sr.party.concat(sr.foes);
        const ok = ids.length && cover.length === ids.length && ids.every(i => cover.indexOf(i) >= 0)
                   && !sr.party.some(i => sr.foes.indexOf(i) >= 0);
        console.log(`    sides via ${sr.via} · party=[${sr.party}] foes=[${sr.foes}] · partition ${ok ? 'OK' : 'BROKEN'}`);
        if (!ok) { console.error('side map does not partition the body set'); process.exitCode = 3; }
      }
      await ev(cdp, `(async()=>{ const s=window.__EBB_SCREEN;
        if (s && s.stage) { try { s.stage.destroy(); } catch(e){} }
        if (s && s.destroy) { try { s.destroy(); } catch(e){} }
        window.__EBB_SCREEN=null; window.Battle.active=false;
        document.querySelectorAll('.ebb-root').forEach(n=>n.remove());
        try { window.UILOCK && UILOCK.unlock('battle'); } catch(e){}
        return true; })()`);
      await sleep(600);
    }
    writeFileSync(join(OUT, 'battle.json'), JSON.stringify(meta, null, 2));
    console.log(JSON.stringify(meta, null, 2));
    cdp.close(); kill(); process.exit(0);
  }

  if (MODE === 'fps') {
    // a spot the solver accepts, so the two paths are compared at the same place
    await ev(cdp, `SIM.tp(38.12, -26.88, SIM.floors(38.12,-26.88)[0]); SIM.tick(3); true`);
    const idle0 = await ev(cdp, RAFPS(4000), 60000);
    const world = await ev(cdp, FPSDRIVE(true), 300000);
    const dio = await ev(cdp, FPSDRIVE(false), 300000);
    const out = { fieldIdle: idle0, world, diorama: dio };
    console.log(JSON.stringify(out, null, 2));
    writeFileSync(join(OUT, 'fps.json'), JSON.stringify(out, null, 2));
    cdp.close(); kill(); process.exit(0);
  }

  if (MODE === 'teardown') {
    // `--at=x,z` picks the cell. The default stages where the player stands; a
    // cell the ladder RELOCATES from is the one that proves the ruling's own
    // obligation ("the player is returned exactly where they stood, whatever
    // distance the fight relocated"), so the receipt must be taken at both.
    const AT = arg('at', '38.12,-26.88').split(',').map(parseFloat);
    console.log(`teardown at ${AT}`);
    await ev(cdp, `SIM.tp(${AT[0]}, ${AT[1]}, SIM.floors(${AT[0]},${AT[1]})[0]); SIM.tick(3); true`);
    const r = await ev(cdp, TEARDOWN, 300000);
    console.log(JSON.stringify(r, null, 2));
    writeFileSync(join(OUT, arg('outfile', 'teardown.json')), JSON.stringify(r, null, 2));
    cdp.close(); kill(); process.exit(0);
  }

  console.error('unknown --mode=' + MODE);
  cdp.close(); kill(); process.exit(2);
})().catch((e) => { console.error('battle_world_probe error:', e); kill(); process.exit(2); });
