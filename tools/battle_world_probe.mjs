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
  let sawWorld = null, sawCanvases = null;
  for (let i = 0; i < 200; i++) {
    const s = window.__EBB_SCREEN && window.__EBB_SCREEN.stage;
    if (s) { sawWorld = !!s.world; sawCanvases = document.querySelectorAll('canvas').length; break; }
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
           bwCreated: window.BattleWorld ? window.BattleWorld.created : null,
           bwRefused: window.BattleWorld ? window.BattleWorld.refused : null,
           plan: window.__BW_LAST_PLAN ? { ok: window.__BW_LAST_PLAN.ok, failed: window.__BW_LAST_PLAN.failed } : null,
           base, after, residue, ebbRoots: roots,
           sceneEvents, uilock: !!(window.UILOCK && UILOCK.active()),
           battleActive: !!window.Battle.active };
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
    return { ok: true, visMin: BW.CFG.place.visMin, camOn: BW.CAM.on,
             pitches: BW.CAM.solve.pitches.slice() };
  })()`, 30000);
  console.log(`knobs: visMin=${knobs.visMin}  CAM.on=${knobs.camOn}  pitches=[${knobs.pitches}]`
            + `   [vis test = ${knobs.visMin > 0 ? 'NINE-SAMPLE (new)' : 'TWO SPINE RAYS (old)'};`
            + ` sweep = ${knobs.camOn ? (knobs.pitches.length > 1 ? 'yaw x pitch, best (new)' : 'yaw only, BEST (isolated)') : 'yaw only, first (old)'}]`);

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
    await ev(cdp, `SIM.tp(38.12, -26.88, SIM.floors(38.12,-26.88)[0]); SIM.tick(3); true`);
    const r = await ev(cdp, TEARDOWN, 300000);
    console.log(JSON.stringify(r, null, 2));
    writeFileSync(join(OUT, 'teardown.json'), JSON.stringify(r, null, 2));
    cdp.close(); kill(); process.exit(0);
  }

  console.error('unknown --mode=' + MODE);
  cdp.close(); kill(); process.exit(2);
})().catch((e) => { console.error('battle_world_probe error:', e); kill(); process.exit(2); });
