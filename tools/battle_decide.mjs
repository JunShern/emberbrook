#!/usr/bin/env node
// battle_decide.mjs — WHAT IS ON SCREEN WHILE THE PLAYER IS CHOOSING.
//
// THE CLAIM UNDER TEST (reported by the placement lane, battle_place.mjs's own
// siteDriver comment): the `round` establishing shot has to be ASKED for, because
// by the time the cast has arrived battle_turnbased has handed the turn over and
// the camera is sitting on `decide` (fov 27, show 'actor') with BOTH FOES OFF
// FRAME. So the frame the player dwells on longest does not contain the enemy.
//
//   node tools/battle_decide.mjs --port=3000 --mode=measure --tag=before
//   node tools/battle_decide.mjs --port=3000 --mode=measure --tag=after
//   node tools/battle_decide.mjs --mode=board
//
// HOW IT MEASURES, and every clause of this is deliberate:
//  * A REAL BATTLE through the shipped path (Battle.start -> the patched
//    BattleStage3D.create -> the world arena), at sites taken out of the
//    placement census (docs/qa/battle-placement/sites.json) by their zone.
//  * NOTHING DRIVES THE CAMERA. battle_place's own driver calls
//    `st.shotTo('round')` and then `st.setActor/setTarget` by hand; this one
//    touches neither, so the shot that is up is the shot the SHIPPED code put
//    there.
//  * THE COMMAND MENU IS DETECTED IN THE DOM, off battle_turnbased's own
//    `cmds.classList.toggle('idle', !p)` — `.ebb-cmds:not(.idle)` is live iff
//    `S.pending` exists. Mode is read the same way: `.ebb-sub.on` = items,
//    a stage target = the target step, else the command step.
//  * THE TURN IS DRIVEN THROUGH THE REAL KEY HANDLER (`__EBB_SCREEN.onKey`), the
//    same function the keyboard reaches, so the wall clock measured after the
//    menu is the wall clock a player pays.
//  * FOES IN FRAME comes from the stage's own `qa.box(id)` — the body's world
//    Box3 projected through the LIVE camera — intersected with the canvas rect.
//    "In frame" is not "visible"; `anchor(id).vis` (which carries a 200 px slop)
//    is reported beside it and neither is called the other.
//
// The pictures are `stage.snapshot()` — one synchronous render through play3d's
// own renderFrame (RenderPass -> GTAO -> bloom -> OutputPass), so the bytes are
// DISPLAY-SPACE and no encode is applied here. The r185 linear-target trap does
// not exist on this path because this path never reads an offscreen target.
// Chrome goes through tools/cdp.mjs and is reaped by --user-data-dir prefix.
import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync, readFileSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import { freePort, killOrphans, sweepStaleProfiles } from './cdp.mjs';
import { LIB as PLACE_LIB } from './battle_place_lib.mjs';

const require = createRequire(import.meta.url);
const WebSocket = require('ws');
const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');

const argv = process.argv.slice(2);
const arg = (k, d) => { const h = argv.find(a => a.startsWith('--' + k + '=')); return h ? h.split('=').slice(1).join('=') : d; };
const PORT = parseInt(arg('port', '3000'), 10);
const MODE = arg('mode', 'measure');
const TAG = arg('tag', 'before');
const OUT = join(ROOT, arg('out', 'docs/qa/battle-decide'));
const HEAD = argv.includes('--head');
// The dwell window sampled at the command step. The real one is UNBOUNDED (it
// ends when the player presses a key), so this is a sampling window, never a
// claim about how long a human takes. The fraction is reported against the
// scripted remainder of the round, which is the only part with a fixed length.
const DWELL = parseInt(arg('dwell', '3000'), 10);
const SITES = arg('sites', '41,5,33,30');     // meadow, forest, crag, water (sort.json 'good')
// THE A/B, AS ONE BUILD. `keep` is a field on the live shot row, so `--keep=0`
// restores the pre-fix `decide` to the line without a checkout: no default
// moves, nothing in public/ is touched, and the two arms differ by one
// assignment. Same shape as --bcam / --btone / --bplace.
const KEEP = arg('keep', null);
// --mode=census only. `--bplace=0` sets BattleWorld.PLACE.on = false at runtime,
// which is exactly what `?bplace=0` does through placeOn() — the sun-refusal A/B
// as ONE BUILD, the same discipline as --keep above.
const BPLACE = arg('bplace', null);
// AND THE ONE-SURFACE-DOMINANCE A/B, the same shape once more: `--bsurf=0` sets
// BattleWorld.PLACE.surf = false at runtime, which is exactly what `?bsurf=0`
// does through surfOn(). The sun refusal is untouched by it, so the three arms
// (neither term, sun only, both) come out of ONE build.
const BSURF = arg('bsurf', null);
// AND THE SAFE-RECT A/B, the same shape again: `--safe=0` clears the `keepSafe`
// list off the live `decide` row, so the arm that keeps the foe line out of the
// turn-order panel and the arm that only keeps it inside the frame are ONE
// BUILD with one assignment between them.
const SAFE = arg('safe', null);
// --mode=cost only: which field of the `decide` row the A/B toggles.
const COSTWHAT = arg('costwhat', 'keep') === 'safe' ? 'keepSafe' : 'keep';
// THE YAW IS PINNED, and this is not a nicety: solveArena's yaw ladder is
// measured RELATIVE TO THE LIVE CAMERA HEADING, so two runs of one cell that
// start at different headings can legitimately stage in different places. The
// placement census ran with the boot heading throughout (the stage restores
// ORBIT on destroy); `--yaw` defaults to whatever the page boots with, so both
// arms and the round census all sit on the same heading.
const YAW = arg('yaw', null);
// --mode=tone only: how many times each cell is staged. Reproducibility is a
// claim about repeats, so the default is more than two.
const REPS = parseInt(arg('reps', '4'), 10);
// Extra query params appended to the game URL (`--q=ambient=0&x=1`). It exists so
// a claim about WHAT ELSE moves in the frame can be tested by switching that
// thing off rather than asserted — see the tone residual in the run log.
const QEXTRA = arg('q', '');
// --composite=1 (census only): photograph the page rather than the canvas, so
// the command menu — a DOM overlay snapshot() cannot see — is IN the frame that
// gets sorted. See censusHold below.
const COMPOSITE = arg('composite', '0') === '1';
// Where the canvas-only twin of each composited frame goes. It is not written
// under docs by default: it duplicates census/<tag>/ byte-for-byte in intent and
// exists only as the pairing evidence, so it belongs in a scratch dir.
const CANVASDIR = arg('canvasdir', null);
// Composited frames land here (viewport-sized; shrink to the canvas census's own
// 900 px before committing — see the payload note in the run log).
const COUT = arg('cout', 'docs/qa/battle-decide/census-c');

mkdirSync(OUT, { recursive: true });
mkdirSync(join(OUT, 'shots'), { recursive: true });

const CDP_PORT = await freePort();
const CHROME = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const sleep = ms => new Promise(r => setTimeout(r, ms));

const PROFILE_PREFIX = 'battle-decide-';
sweepStaleProfiles(PROFILE_PREFIX);
const profile = join(process.env.TMPDIR || '/tmp', PROFILE_PREFIX + process.pid);

const URL = `http://localhost:${PORT}/play3d.html?scene=ow-valley&rt=1&nomusic=1&arena=world`
  + (QEXTRA ? '&' + QEXTRA : '');
const chrome = spawn(CHROME, [
  `--remote-debugging-port=${CDP_PORT}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--disable-extensions',
  '--autoplay-policy=no-user-gesture-required',
  '--hide-scrollbars', '--force-device-scale-factor=1',
  '--window-size=1600,900',
  ...(HEAD ? [] : ['--headless=new']),
  URL,
], { stdio: 'ignore' });
let closing = false;
const kill = () => {
  if (closing) return; closing = true;
  try { chrome.kill('SIGKILL'); } catch (e) { }
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
      return { ready: true, three: THREE.REVISION, scene: SIM.bounds().scene };
    }
    await new Promise(r => setTimeout(r, 200));
  }
  return { ready: false };
})()`;

// ---------------------------------------------------------------------------
// THE PAGE LIBRARY. Sampling only: it starts nothing and moves nothing.
const LIB = `(() => {
  const W = {}; window.__DEC = W;
  const st = () => (window.__EBB_SCREEN && window.__EBB_SCREEN.stage) || null;
  W.st = st;
  // battle_turnbased's own tell: renderMenu toggles 'idle' off exactly while
  // S.pending exists. Reading the class is reading the module's own state.
  W.menu = function () {
    const c = document.querySelector('.ebb-cmds');
    if (!c) return { up: false, mode: null };
    const up = !c.classList.contains('idle');
    if (!up) return { up: false, mode: null };
    const sub = document.querySelector('.ebb-sub');
    if (sub && sub.classList.contains('on')) return { up: true, mode: 'items' };
    const s = st();
    const tgt = s && s.cam ? s.cam().target : null;
    return { up: true, mode: tgt ? 'target' : 'cmd' };
  };
  // WHAT IS ON SCREEN, this instant. Everything is asked of the stage.
  W.sample = function () {
    const s = st(); if (!s) return null;
    const c = s.cam ? s.cam() : null;
    const sides = s.sides ? s.sides() : {};
    const foes = [], party = [];
    for (const id of Object.keys(sides)) {
      const b = s.qa && s.qa.box ? s.qa.box(id) : null;
      const a = s.anchor ? s.anchor(id) : null;
      if (!b) continue;
      const W2 = b.w, H2 = b.h;
      const ox = Math.max(0, Math.min(b.x1, W2) - Math.max(b.x0, 0));
      const oy = Math.max(0, Math.min(b.y1, H2) - Math.max(b.y0, 0));
      const area = Math.max(1e-6, (b.x1 - b.x0) * (b.y1 - b.y0));
      const rec = { id: id, side: sides[id], dead: !!b.dead,
                    inFrame: +(ox * oy / area).toFixed(3),
                    hFrac: +((b.y1 - b.y0) / H2).toFixed(3),
                    cx: +(((b.x0 + b.x1) / 2) / W2).toFixed(3),
                    anchorVis: a ? !!a.vis : null };
      (sides[id] === 'foe' ? foes : party).push(rec);
    }
    const liveFoes = foes.filter(f => !f.dead);
    return { t: +performance.now().toFixed(1), kind: c ? c.kind : null,
             target: c ? c.target : null, actor: c ? c.actor : null,
             fov: c ? c.fov : null, dist: c && c.pose ? c.pose.dist : null,
             axisOk: c && c.axis ? !!c.axis.ok : null,
             foes: foes, party: party,
             foesIn: liveFoes.filter(f => f.inFrame > 0.02).length,
             foesAll: liveFoes.length,
             foesFull: liveFoes.filter(f => f.inFrame > 0.95).length };
  };
  // a display-space JPEG of the arena, through the stage's own render
  W.jpg = function (q) {
    const s = st(); if (!s) return null;
    s.snapshot();
    const src = s.canvas;
    const c = document.createElement('canvas');
    c.width = src.width; c.height = src.height;
    c.getContext('2d').drawImage(src, 0, 0);
    return c.toDataURL('image/jpeg', q || 0.85);
  };
  return true;
})()`;

// ---------------------------------------------------------------------------
// ONE SITE: land where the census landed, fight for real, sample, tear down.
const siteDriver = (site) => `(async () => {
  const S = ${JSON.stringify(site)};
  const GS = window.GS, B = window.Battle, RU = window.Rules;
  const D = window.__DEC;
  GS.setFlags({ 'maren-joined': true });
  const f = SIM.floors(S.at.x, S.at.z);
  if (!f.length) return { skip: 'no floor at the census cell' };
  SIM.tp(S.at.x, S.at.z, S.at.y); SIM.tick(3);
  const p0 = SIM.pos();
  const zone = SIM.zone(p0.x, p0.z) || S.zone;

  const items = GS.data.items.items, growth = GS.data.growth;
  const party = GS.activeParty().filter(c => ['vesper','maren'].indexOf(c.id) >= 0)
                 .map(c => RU.derive.partyMember(growth, items, c));
  const zd = GS.data.encounters.zones[zone] || GS.data.encounters.zones.meadow;
  // TRIGGER TO FIRST FRAME, the number the placement lane priced. t0 is the
  // instant Battle.start is called; tFirst is the first frame the world
  // renderer draws after the stage exists.
  const t0 = performance.now();
  const pr = B.start({ zone: zone, group: ['duskpad','reed-nibbler'], seed: 4242,
                       backdrop: zd && zd.battleBackdrop }, party, { speed: 1 });
  pr.then(()=>{}, ()=>{});
  let st = null;
  for (let i = 0; i < 400 && !(st = D.st()); i++) await new Promise(r => setTimeout(r, 25));
  if (!st) return { skip: 'no stage' };
  if (!st.world) return { skip: 'not the world stage' };
  const tStage = performance.now();
  const f0 = st.frames;
  while (st.frames === f0) await new Promise(r => setTimeout(r, 8));
  const tFirst = performance.now();

  // ---- THE MENU, WAITED FOR, NEVER FORCED ---------------------------------
  // Sample from the moment the stage exists so the whole opening is on the
  // record: which shot is up when the menu arrives is the claim.
  const pre = [];
  let tMenu = null, menu = null;
  for (let i = 0; i < 2000; i++) {
    const m = D.menu();
    if (i % 4 === 0) { const s2 = D.sample(); if (s2) { s2.menu = m.up ? m.mode : null; pre.push(s2); } }
    if (m.up) { tMenu = performance.now(); menu = m; break; }
    await new Promise(r => setTimeout(r, 25));
  }
  if (tMenu == null) return { skip: 'the command menu never opened' };

  // ---- THE DWELL. Nothing is pressed; the camera is left alone. -----------
  const dwell = [];
  const tEnd = tMenu + ${DWELL};
  while (performance.now() < tEnd) {
    const s2 = D.sample(); const m = D.menu();
    if (s2) { s2.menu = m.up ? m.mode : null; dwell.push(s2); }
    await new Promise(r => setTimeout(r, 100));
  }
  const shotCmd = D.jpg(0.85);
  const camCmd = st.cam();
  const tiers = st.tiers();

  // ---- DRIVE THE ROUND THROUGH THE REAL KEY HANDLER -----------------------
  // EVERY party member is prompted before ANYTHING resolves — the scheduler
  // collects the round's decisions first — so a round contains as many command
  // steps as there are living party members, and the honest denominator is the
  // whole round, not one prompt.
  const sc = window.__EBB_SCREEN;
  const tCmdDone = performance.now();
  const cmdSteps = [];
  let tgtS = null, shotTgt = null, tCommit = null;
  for (let seat = 0; seat < 4; seat++) {
    const m0 = D.menu();
    if (!m0.up) break;
    if (seat > 0) {
      // a SHORT dwell on the second seat's command step, sampled the same way
      const t1 = performance.now(), rec = [];
      while (performance.now() < t1 + 800) {
        const s3 = D.sample(); const mm = D.menu();
        if (s3) { s3.menu = mm.up ? mm.mode : null; rec.push(s3); }
        await new Promise(r => setTimeout(r, 100));
      }
      cmdSteps.push({ seat: seat, samples: rec });
    }
    sc.onKey('confirm');                     // Attack -> the target step
    await new Promise(r => setTimeout(r, seat === 0 ? 700 : 300));
    if (seat === 0) { tgtS = D.sample(); shotTgt = D.jpg(0.85); }
    sc.onKey('confirm');                     // commit
    tCommit = performance.now();
    await new Promise(r => setTimeout(r, 160));
  }

  // ---- THE SCRIPTED REMAINDER: last commit -> the next round's menu -------
  const after = [];
  let tNext = null, ended = false;
  for (let i = 0; i < 1600; i++) {
    const s2 = D.sample(); const m = D.menu();
    if (s2) { s2.menu = m.up ? m.mode : null; after.push(s2); }
    if (!window.Battle.active || !D.st()) { ended = true; break; }
    if (m.up && performance.now() - tCommit > 400) { tNext = performance.now(); break; }
    await new Promise(r => setTimeout(r, 40));
  }
  const camLog = st.cam ? st.cam().log : null;
  const site = st.site || {};

  // teardown (the battle_world_probe recipe)
  try { st.destroy(); } catch (e) {}
  const sc2 = window.__EBB_SCREEN;
  if (sc2 && sc2.destroy) { try { sc2.destroy(); } catch (e) {} }
  window.__EBB_SCREEN = null; window.Battle.active = false;
  document.querySelectorAll('.ebb-root').forEach(n => n.remove());
  try { window.UILOCK && UILOCK.unlock('battle'); } catch (e) {}

  return { ok: true, id: S.id, zone: zone, at: p0,
           cost: { stageMs: +(tStage - t0).toFixed(1), firstFrameMs: +(tFirst - t0).toFixed(1),
                   menuMs: +(tMenu - t0).toFixed(1) },
           site: { R: site.R, d: site.d, ms: site.ms, cands: site.cands, solved: site.solved },
           tiers: tiers, pre: pre, dwell: dwell, target: tgtS, after: after,
           cmdSteps: cmdSteps, cam: camCmd, log: camLog,
           spans: { dwellMs: ${DWELL}, seats: cmdSteps.length + 1,
                    drivenMs: +(tCommit - tCmdDone).toFixed(1),
                    resolveMs: tNext == null ? null : +(tNext - tCommit).toFixed(1),
                    ended: ended },
           shots: { cmd: shotCmd, target: shotTgt } };
})()`;

// ---------------------------------------------------------------------------
// MODE: tone — IS THE BOOM CHOOSER REPRODUCIBLE. Stage the SAME cell R times
// with ORBIT.yaw pinned and record the whole score table (`st.tone().rows`),
// not just the rung it chose: a chooser that picks the same rung on scores that
// wander is one near-tie away from picking a different one, so the ROWS are the
// measurement and the pick is the symptom. The canvas frame is saved per repeat
// so "did it photograph the same picture" is answerable off the same run.
// Nothing here drives the camera and nothing forces the probe.
const toneDriver = (site, yaw) => `(async () => {${censusHead(site, yaw)}
  const tn = st.tone();
  const cast = st.castPhase ? st.castPhase() : null;
  const camr = st.cam ? st.cam() : null;
  try { st.destroy(); } catch (e) {}
  const sc = window.__EBB_SCREEN;
  if (sc && sc.destroy) { try { sc.destroy(); } catch (e) {} }
  window.__EBB_SCREEN = null; window.Battle.active = false;
  document.querySelectorAll('.ebb-root').forEach(n => n.remove());
  try { window.UILOCK && UILOCK.unlock('battle'); } catch (e) {}
  return { ok: true, row: { id: S.id, zone: zone, at: p0,
      tone: tn, cast: cast,
      pitch: camr && camr.base ? camr.base.pitch : null,
      kind: samp ? samp.kind : null, camDist: samp ? samp.dist : null,
      fov: samp ? samp.fov : null, foesIn: samp ? samp.foesIn : null,
      stageR: (st.site || {}).R }, shot: shot };
})()`;

// ---------------------------------------------------------------------------
// MODE: census — THE DECIDE FRAME AT EVERY SITE THE PLACEMENT CENSUS SORTED.
//
// The placement study eye-sorted 62 sites and reported 48.4% bad -> 32.3% after
// the sun refusal. It sorted `round` PLATES. This mode photographs the SAME 62
// landing cells at the `decide` command step so the two sorts can be laid side
// by side, because "good staging for a wide establishing shot is good staging
// for a 27 mm two-shot" is a HYPOTHESIS and nothing had tested it.
//
// EVERY CLAUSE THAT MAKES THE TWO COMPARABLE:
//  * the same landing cell (sites.json `at`, replayed with SIM.tp — the landing
//    walk is deterministic and independent of staging, 62/62 verified by the
//    placement lane), the same party, the same two foes, the same seed;
//  * the same maturity: tiers off proxy, the tone chooser landed, +1100 ms —
//    battle_place's own ladder, to the line, so the plate is as finished here;
//  * ORBIT.yaw PINNED before Battle.start (see YAW above);
//  * NOTHING DRIVES THE CAMERA. battle_place had to call st.shotTo('round') by
//    hand to photograph its frame; this one waits for the shipped `decide` to
//    arrive and then waits out its 620 ms move. The shot that is up is the shot
//    the shipped code put there, at the step the player is sitting in;
//  * measured with the placement lane's OWN library (tools/battle_place_lib.mjs,
//    moved verbatim), so silhouette / one-surface dominance / ray census /
//    frame luminance are the same numbers computed by the same code.
//
//  * --composite=1 SPLITS THE DRIVER IN HALF AT THE PHOTOGRAPH. The command menu
//    is a DOM overlay and `stage.snapshot()` reads the WebGL canvas, so every
//    frame in both censuses was judged without the box that covers its lower
//    band in play. A page-side script cannot photograph the DOM; only the
//    browser can. So the head half stages the fight, waits out the decide move,
//    takes the canvas jpg and RETURNS WITH THE BATTLE STILL LIVE (the command
//    step is unbounded — it ends on a keypress — so holding it is the real
//    state, not a contrivance); node then takes ONE `Page.captureScreenshot`,
//    which composites canvas and DOM exactly as the compositor does for the
//    player; the tail half measures with the placement library and tears down.
//    NOTHING ELSE MOVES: the two halves are the same statements in the same
//    order with a ~200 ms pause between the canvas shot and the composited one.
const censusHead = (site, yaw) => `
  const S = ${JSON.stringify(site)};
  const GS = window.GS, B = window.Battle, RU = window.Rules, D = window.__DEC;
  GS.setFlags({ 'maren-joined': true });
  const f = SIM.floors(S.at.x, S.at.z);
  if (!f.length) return { skip: 'no floor at the census cell' };
  SIM.tp(S.at.x, S.at.z, S.at.y); SIM.tick(3);
  const p0 = SIM.pos();
  const zone = SIM.zone(p0.x, p0.z) || S.zone;
  const yawWas = +window.ORBIT.yaw.toFixed(4);
  window.ORBIT.yaw = ${yaw};

  const items = GS.data.items.items, growth = GS.data.growth;
  const party = GS.activeParty().filter(c => ['vesper','maren'].indexOf(c.id) >= 0)
                 .map(c => RU.derive.partyMember(growth, items, c));
  const zd = GS.data.encounters.zones[zone] || GS.data.encounters.zones.meadow;
  const t0 = performance.now();
  const pr = B.start({ zone: zone, group: ['duskpad','reed-nibbler'], seed: 4242,
                       backdrop: zd && zd.battleBackdrop }, party, { speed: 1 });
  pr.then(()=>{}, ()=>{});
  let st = null;
  for (let i = 0; i < 300 && !(st = D.st()); i++) await new Promise(r => setTimeout(r, 100));
  if (!st) return { skip: 'no stage' };
  if (!st.world) return { skip: 'not the world stage' };
  const f0 = st.frames;
  for (let i = 0; i < 300; i++) {
    const t = st.tiers();
    if (Object.values(t).every(v => v !== 'proxy') && st.frames > f0 + 90) break;
    await new Promise(r => setTimeout(r, 100));
  }
  for (let i = 0; i < 160; i++) { const tn = st.tone(); if (tn && (tn.ok || tn.why && !/waiting/.test(tn.why))) break; await new Promise(r => setTimeout(r, 100)); }
  await new Promise(r => setTimeout(r, 1100));
  const stageMs = performance.now() - t0;

  // ---- THE COMMAND STEP, WAITED FOR AND NEVER FORCED ----------------------
  let m = D.menu();
  for (let i = 0; i < 400 && !(m.up && m.mode === 'cmd'); i++) { await new Promise(r => setTimeout(r, 25)); m = D.menu(); }
  if (!(m.up && m.mode === 'cmd')) return { skip: 'the command step never arrived (menu ' + JSON.stringify(m) + ')' };
  // and the MOVE IS NOT THE STATE: wait for the decide pose to be the live one
  // and then wait out its 620 ms travel, so what is photographed is the frame
  // the player sits in rather than the tail of the round shot.
  let s0 = D.sample();
  for (let i = 0; i < 200 && !(s0 && s0.kind === 'decide'); i++) { await new Promise(r => setTimeout(r, 25)); s0 = D.sample(); }
  await new Promise(r => setTimeout(r, 900));
  const samp = D.sample();
  const shot = D.jpg(0.84);
`;

// The tail: everything measured, then teardown. Shared verbatim by both arms.
const CENSUS_TAIL = `
  // ---- MEASURED WITH THE PLACEMENT LANE'S OWN RULER -----------------------
  const F = window.__PLACE.frames();
  const sil = window.__PLACE.silhouette(F);
  const surf = window.__PLACE.surface(F, sil.ok ? sil.mask : null);
  if (sil.ok) delete sil.mask;
  const rays = window.__PLACE.rays(28, 16);
  const fl = window.__PLACE.frameL(F);
  const site = st.site || {};
  const plan = st.plan || {};
  const camr = st.cam ? st.cam() : null;
  const anchors = {};
  for (const id of Object.keys(st.tiers())) { const a = st.anchor(id); if (a) anchors[id] = { x:+a.x.toFixed(0), y:+a.y.toFixed(0), h:+a.h.toFixed(0), vis:a.vis }; }
  const sun = window.__PLACE.sun(plan);
  const grd = window.__PLACE.ground(site.at || p0, 5, 1.25);

  // teardown (the battle_world_probe recipe)
  try { st.destroy(); } catch (e) {}
  const sc = window.__EBB_SCREEN;
  if (sc && sc.destroy) { try { sc.destroy(); } catch (e) {} }
  window.__EBB_SCREEN = null; window.Battle.active = false;
  document.querySelectorAll('.ebb-root').forEach(n => n.remove());
  try { window.UILOCK && UILOCK.unlock('battle'); } catch (e) {}

  return { ok: true, row: {
      id: S.id, zone: zone, at: p0, yawWas: yawWas,
      site: { R: site.R, d: site.d, ms: site.ms, cands: site.cands, solved: site.solved,
              quality: site.quality || null },
      relief: plan.relief, yawDelta: plan.yawDelta, view: plan.view || null,
      kind: samp ? samp.kind : null,
      pitch: camr && camr.base ? camr.base.pitch : null,
      fov: samp ? samp.fov : null, camDist: samp ? samp.dist : null,
      axisOk: samp ? samp.axisOk : null,
      foesIn: samp ? samp.foesIn : null, foesAll: samp ? samp.foesAll : null,
      foesFull: samp ? samp.foesFull : null,
      foes: samp ? samp.foes : null, partyBoxes: samp ? samp.party : null,
      sil: sil, surf: surf, rays: rays, ground: grd, sun: sun, frameL: fl,
      anchors: anchors, tiers: st.tiers(), stageMs: +stageMs.toFixed(0) },
    shot: shot };
`;

const censusDriver = (site, yaw) => `(async () => {${censusHead(site, yaw)}${CENSUS_TAIL}})()`;

// THE COMPOSITE ARM. Head, then a CDP screenshot from node, then tail. The menu
// rectangle is read here in CSS pixels ALONGSIDE the canvas rectangle, because a
// band is only meaningful as a fraction of the frame it covers.
const censusHold = (site, yaw) => `(async () => {${censusHead(site, yaw)}
  window.__DEC.hold = { S: S, st: st, p0: p0, zone: zone, yawWas: yawWas,
                        samp: samp, shot: shot, stageMs: stageMs };
  const rect = (sel) => { const n = document.querySelector(sel); if (!n) return null;
    const r = n.getBoundingClientRect();
    return { x0: +r.left.toFixed(1), y0: +r.top.toFixed(1), x1: +r.right.toFixed(1), y1: +r.bottom.toFixed(1) }; };
  // EVERY OPAQUE PANEL, not just the command list: battle_turnbased paints a
  // prompt rail across the top and a turn-order panel bottom-right, and the frame
  // the player lives in has all of them in it.
  const ui = {};
  for (const sel of ['.ebb-cmds', '.ebb-log', '.ebb-rail', '.ebb-party', '.ebb-phead', '.ebb-sub'])
    ui[sel] = rect(sel);
  ui.foeTags = Array.from(document.querySelectorAll('.ebb-ftags')).map(n => {
    const r = n.getBoundingClientRect();
    return { x0: +r.left.toFixed(1), y0: +r.top.toFixed(1), x1: +r.right.toFixed(1), y1: +r.bottom.toFixed(1) };
  });
  const uiSafe = ['.ebb-partywin', '.ebb-cmdwin'];
  for (const sel of uiSafe) ui[sel] = rect(sel);
  return { ok: true, staged: true, id: S.id, safe: (st.safeRect ? st.safeRect('decide') : null),
           menuRect: rect('.ebb-cmds'), canvasRect: rect('canvas'), ui: ui,
           dpr: window.devicePixelRatio,
           vw: window.innerWidth, vh: window.innerHeight };
})()`;

const CENSUS_FINISH = `(async () => {
  const D = window.__DEC, H = D.hold;
  if (!H) return { skip: 'nothing held' };
  D.hold = null;
  const S = H.S, st = H.st, p0 = H.p0, zone = H.zone, yawWas = H.yawWas,
        samp = H.samp, shot = H.shot, stageMs = H.stageMs;
  ${CENSUS_TAIL}
})()`;

// ---------------------------------------------------------------------------
// ---------------------------------------------------------------------------
// WHAT THE CONTAINMENT TERM COSTS, A/B'd ON ONE LIVE BATTLE. `keep` is a field
// on the live shot row, so the two arms are one build with one assignment
// between them — and the arms ALTERNATE, so a thermal or GC drift lands on both.
// SAY WHICH COST THIS IS: a `decide` re-solve happens DURING the turn (setActor,
// setTarget), never at staging. solveArena — the 69.7 ms the placement lane
// priced — is not on this path and is not touched by the change.
const costDriver = (site) => `(async () => {
  const S = ${JSON.stringify(site)};
  const GS = window.GS, B = window.Battle, RU = window.Rules, D = window.__DEC;
  GS.setFlags({ 'maren-joined': true });
  SIM.tp(S.at.x, S.at.z, S.at.y); SIM.tick(3);
  const zone = SIM.zone(SIM.pos().x, SIM.pos().z) || S.zone;
  const items = GS.data.items.items, growth = GS.data.growth;
  const party = GS.activeParty().filter(c => ['vesper','maren'].indexOf(c.id) >= 0)
                 .map(c => RU.derive.partyMember(growth, items, c));
  const zd = GS.data.encounters.zones[zone] || GS.data.encounters.zones.meadow;
  const pr = B.start({ zone: zone, group: ['duskpad','reed-nibbler'], seed: 4242,
                       backdrop: zd && zd.battleBackdrop }, party, { speed: 1 });
  pr.then(()=>{}, ()=>{});
  let st = null;
  for (let i = 0; i < 400 && !(st = D.st()); i++) await new Promise(r => setTimeout(r, 25));
  if (!st || !st.world) return { skip: 'no world stage' };
  const f0 = st.frames;
  for (let i = 0; i < 300; i++) {
    const t = st.tiers();
    if (Object.values(t).every(v => v !== 'proxy') && st.frames > f0 + 90) break;
    await new Promise(r => setTimeout(r, 100));
  }
  await new Promise(r => setTimeout(r, 600));
  const row = window.BattleWorld.CAM.shots.decide;
  // WHICH TERM IS BEING PRICED. --costwhat=keep is the containment the last lane
  // shipped; --costwhat=safe is the safe rect on top of it, and it is a DIFFERENT
  // question: the safe rect reads the DOM, so its cost is a forced layout as well
  // as arithmetic and it must be priced with the containment already on in both
  // arms. (No backticks in this comment on purpose -- it lives INSIDE a template
  // literal, and a backtick in a comment ends the literal. Paid twice now.)
  const FIELD = '${COSTWHAT}';
  const saved = row[FIELD];
  const on = [], off = [];
  const one = () => { const t = performance.now(); st.shotTo('decide', { actor: 'vesper' }); return performance.now() - t; };
  row[FIELD] = null;  for (let i = 0; i < 6; i++) one();          // warm both paths
  row[FIELD] = saved; for (let i = 0; i < 6; i++) one();
  for (let i = 0; i < 60; i++) {
    row[FIELD] = null;  off.push(one());
    row[FIELD] = saved; on.push(one());
  }
  row[FIELD] = saved;
  const refusals = st.cam().refusals;
  try { st.destroy(); } catch (e) {}
  const sc = window.__EBB_SCREEN; if (sc && sc.destroy) { try { sc.destroy(); } catch (e) {} }
  window.__EBB_SCREEN = null; window.Battle.active = false;
  document.querySelectorAll('.ebb-root').forEach(n => n.remove());
  try { window.UILOCK && UILOCK.unlock('battle'); } catch (e) {}
  const q = (a, p) => { const b = a.slice().sort((x, y) => x - y); return +b[Math.min(b.length - 1, Math.floor(b.length * p))].toFixed(3); };
  return { ok: true, id: S.id, zone: zone, n: on.length, refusals: refusals,
           off: { p50: q(off, 0.5), p90: q(off, 0.9), max: q(off, 1) },
           on:  { p50: q(on, 0.5),  p90: q(on, 0.9),  max: q(on, 1) } };
})()`;

// THE MOVE IS NOT THE STATE. `decide` takes 620 ms to arrive, so the first
// samples after the menu opens are still the tail of the `round` shot. `steady`
// is everything past the move, which is what "the frame the player dwells on"
// actually means; the whole-window figure is reported beside it, never instead.
const SETTLE_MS = 700;
function summarise(row) {
  const d = row.dwell.filter(s => s.menu === 'cmd');
  const t0 = d.length ? d[0].t : 0;
  const st = d.filter(s => s.t - t0 >= SETTLE_MS);
  const n = d.length || 1, ns = st.length || 1;
  const kinds = {};
  for (const s of d) kinds[s.kind || 'null'] = (kinds[s.kind || 'null'] || 0) + 1;
  const last = d.length ? d[d.length - 1] : null;
  const seat2 = (row.cmdSteps || []).map(c => {
    const ss = c.samples.filter(s => s.menu === 'cmd');
    return { seat: c.seat, samples: ss.length,
             zeroFoeFrac: ss.length ? +(ss.filter(s => s.foesIn === 0).length / ss.length).toFixed(3) : null };
  });
  return {
    id: row.id, zone: row.zone,
    kindAtMenu: d.length ? d[0].kind : null,
    kinds: kinds,
    fov: last ? last.fov : null,
    dist: last ? last.dist : null,
    axisOk: d.every(s => s.axisOk !== false),
    samples: d.length, steadySamples: st.length,
    zeroFoeFrac: +(d.filter(s => s.foesIn === 0).length / n).toFixed(3),
    zeroFoeSteady: +(st.filter(s => s.foesIn === 0).length / ns).toFixed(3),
    meanFoesIn: d.length ? +(d.reduce((a, s) => a + s.foesIn, 0) / n).toFixed(2) : null,
    meanFoesInSteady: st.length ? +(st.reduce((a, s) => a + s.foesIn, 0) / ns).toFixed(2) : null,
    foesAll: d.length ? d[0].foesAll : null,
    foeInFrame: last ? last.foes.map(f => ({ id: f.id, inFrame: f.inFrame, hFrac: f.hFrac, cx: f.cx, vis: f.anchorVis })) : [],
    partyIn: last ? last.party.map(p => ({ id: p.id, inFrame: p.inFrame, hFrac: p.hFrac, cx: p.cx })) : [],
    seats: seat2,
    targetStep: row.target ? { kind: row.target.kind, foesIn: row.target.foesIn, foesAll: row.target.foesAll } : null,
    cost: row.cost, spans: row.spans,
  };
}

(async () => {
  if (MODE === 'board') { buildBoard(); process.exit(0); }

  let cdp = null;
  for (let i = 0; i < 60; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${CDP_PORT}/json/list`);
      const list = await r.json();
      const pg = list.find(t => t.type === 'page' && /play3d\.html|play\.html/.test(t.url));
      if (pg && pg.webSocketDebuggerUrl) { cdp = await connect(pg.webSocketDebuggerUrl); break; }
    } catch (e) { }
    await sleep(500);
  }
  if (!cdp) { console.error('chrome never exposed the game page on CDP ' + CDP_PORT); kill(); process.exit(2); }
  await cdp.send('Runtime.enable');
  const ready = await ev(cdp, READY, 180000);
  if (!ready.ready) { console.error('page never became ready'); kill(); process.exit(2); }
  console.log(`ready three=r${ready.three} scene=${ready.scene}`);
  console.log('battle_world: ' + JSON.stringify(await ev(cdp, INJECT, 60000)));
  await ev(cdp, LIB, 30000);
  if (MODE === 'census' || MODE === 'tone') await ev(cdp, PLACE_LIB, 30000);
  if (BPLACE != null) {
    const v = await ev(cdp, `(() => { window.BattleWorld.PLACE.on = ${BPLACE === '0' ? 'false' : 'true'};
      return window.BattleWorld.PLACE.on; })()`, 10000);
    console.log('PLACE.on = ' + v);
  }
  if (BSURF != null) {
    const v = await ev(cdp, `(() => { window.BattleWorld.PLACE.surf = ${BSURF === '0' ? 'false' : 'true'};
      return window.BattleWorld.PLACE.surf; })()`, 10000);
    console.log('PLACE.surf = ' + v);
  }
  if (KEEP != null) {
    const k = await ev(cdp, `(() => { const r = window.BattleWorld.CAM.shots.decide;
      r.keep = ${KEEP === '0' ? 'null' : "'foes'"}; return r.keep; })()`, 10000);
    console.log('decide.keep = ' + JSON.stringify(k));
  }

  if (SAFE != null) {
    const v = await ev(cdp, `(() => { const r = window.BattleWorld.CAM.shots.decide;
      r.keepSafe = ${SAFE === '0' ? 'null' : "['.ebb-partywin', '.ebb-cmdwin']"}; return r.keepSafe; })()`, 10000);
    console.log('decide.keepSafe = ' + JSON.stringify(v));
  }

  // THE CENSUS IS 60 + 2: battle_place exhausted the 400 road cells in one pass
  // (sites.json) and a second rotated pass added two more (sites-b.json). Both
  // files together are the 62 the sort covers; reading only the first silently
  // drops s060/s061, which is how a "census" quietly becomes a sample.
  const census = JSON.parse(readFileSync(join(ROOT, 'docs/qa/battle-placement/sites.json'), 'utf8')).rows
    .concat(existsSync(join(ROOT, 'docs/qa/battle-placement/sites-b.json'))
      ? JSON.parse(readFileSync(join(ROOT, 'docs/qa/battle-placement/sites-b.json'), 'utf8')).rows : []);
  const want = SITES.split(',').map(s => parseInt(s, 10));
  const sites = want.map(i => ({ id: 's' + String(i).padStart(3, '0'), zone: census[i].zone, at: census[i].at }));

  if (MODE === 'tone') {
    const yaw = YAW != null ? parseFloat(YAW)
      : await ev(cdp, '(() => +window.ORBIT.yaw.toFixed(6))()', 10000);
    console.log('ORBIT.yaw pinned at ' + yaw);
    const dir = join(OUT, 'tone', TAG);
    mkdirSync(dir, { recursive: true });
    const out = [];
    for (let rep = 0; rep < REPS; rep++) {
      for (const s of sites) {
        process.stdout.write(`  rep${rep} ${s.id} (${s.zone}) ... `);
        let r;
        try { r = await ev(cdp, toneDriver(s, yaw), 300000); }
        catch (e) { console.log('THREW ' + e.message); continue; }
        if (!r || !r.ok) { console.log('skip: ' + (r && r.skip)); continue; }
        if (r.shot) writeFileSync(join(dir, `${s.id}-r${rep}.jpg`), Buffer.from(r.shot.split(',')[1], 'base64'));
        r.row.rep = rep;
        out.push(r.row);
        const t = r.row.tone || {};
        console.log(`was=${t.was} chose=${t.chose} best=${t.best} decisive=${t.decisive} ` +
                    `scores=[${(t.rows || []).map(x => x.score).join(', ')}] pitch=${r.row.pitch}`);
        await sleep(300);
      }
    }
    const f = join(OUT, `tone-${TAG}.json`);
    writeFileSync(f, JSON.stringify({ meta: { when: new Date().toISOString(), tag: TAG, yaw: yaw,
      reps: REPS, sites: SITES, three: ready.three }, rows: out }, null, 1));
    console.log('WROTE ' + f + '\nframes -> ' + dir);
    cdp.close(); kill(); process.exit(0);
  }

  if (MODE === 'census') {
    const yaw = YAW != null ? parseFloat(YAW)
      : await ev(cdp, '(() => +window.ORBIT.yaw.toFixed(6))()', 10000);
    console.log('ORBIT.yaw pinned at ' + yaw);
    const dir = CANVASDIR ? CANVASDIR : join(OUT, 'census', TAG);
    mkdirSync(dir, { recursive: true });
    const cdir = join(ROOT, COUT, TAG);
    if (COMPOSITE) { mkdirSync(cdir, { recursive: true }); await cdp.send('Page.enable'); }
    const out = [];
    const t0 = Date.now();
    // --start / --limit are for smoke-testing the driver and for resuming a run;
    // the DEFAULT IS THE WHOLE CENSUS, because a census with a default sample
    // size is a sample.
    const from = parseInt(arg('start', '0'), 10);
    const lim = parseInt(arg('limit', String(census.length)), 10);
    for (const r of census.slice(from, from + lim)) {
      const s = { id: r.id, zone: r.zone, at: r.at };
      process.stdout.write(`  ${s.id} (${s.zone}) ... `);
      let res, held = null;
      try {
        if (COMPOSITE) {
          held = await ev(cdp, censusHold(s, yaw), 300000);
          if (!held || !held.ok) { console.log('skip: ' + (held && held.skip)); continue; }
          await sleep(200);
          const png = await cdp.send('Page.captureScreenshot',
            { format: 'jpeg', quality: 88, captureBeyondViewport: false });
          writeFileSync(join(cdir, s.id + '.jpg'), Buffer.from(png.data, 'base64'));
          res = await ev(cdp, CENSUS_FINISH, 300000);
        } else {
          res = await ev(cdp, censusDriver(s, yaw), 300000);
        }
      }
      catch (e) { console.log('THREW ' + e.message); continue; }
      if (!res || !res.ok) { console.log('skip: ' + (res && res.skip)); continue; }
      if (held) { res.row.menuRect = held.menuRect; res.row.canvasRect = held.canvasRect;
                  res.row.ui = held.ui; res.row.safe = held.safe;
                  res.row.viewport = { w: held.vw, h: held.vh, dpr: held.dpr }; }
      if (res.shot) writeFileSync(join(dir, s.id + '.jpg'), Buffer.from(res.shot.split(',')[1], 'base64'));
      out.push(res.row);
      const w = res.row;
      console.log(`kind=${w.kind} fov=${w.fov} foesIn=${w.foesIn}/${w.foesAll} ` +
                  `edgeRGB=${w.sil.edgeRGB} top=${w.surf.topSurface} sky=${w.rays.skyFrac} ` +
                  `R=${w.site.R} ${((Date.now() - t0) / 1000).toFixed(0)}s`);
      await sleep(300);
    }
    const f = join(OUT, `census-${TAG}.json`);
    writeFileSync(f, JSON.stringify({ meta: { when: new Date().toISOString(), tag: TAG, yaw: yaw,
      bplace: BPLACE, bsurf: BSURF, keep: KEEP, composite: COMPOSITE, three: ready.three, n: out.length, of: census.length,
      secs: +((Date.now() - t0) / 1000).toFixed(0) }, rows: out }, null, 1));
    console.log(`\nwrote ${out.length}/${census.length} sites -> ${f}`);
    console.log('shots -> ' + dir);
    cdp.close(); kill(); process.exit(0);
  }

  if (MODE === 'cost') {
    const out = [];
    for (const s of sites) {
      process.stdout.write(`  ${s.id} (${s.zone}) ... `);
      const r = await ev(cdp, costDriver(s), 300000);
      if (!r || !r.ok) { console.log('skip: ' + (r && r.skip)); continue; }
      out.push(r);
      console.log(`decide solve  keep OFF p50 ${r.off.p50} ms / max ${r.off.max}   ` +
                  `keep ON p50 ${r.on.p50} ms / max ${r.on.max}   refusals=${r.refusals}`);
    }
    const f = join(OUT, 'cost.json');
    writeFileSync(f, JSON.stringify({ meta: { when: new Date().toISOString(), three: ready.three }, rows: out }, null, 1));
    console.log('WROTE ' + f);
    cdp.close(); kill(); process.exit(0);
  }

  const rows = [];
  for (const s of sites) {
    process.stdout.write(`  ${s.id} (${s.zone}) ... `);
    let r;
    try { r = await ev(cdp, siteDriver(s), 300000); }
    catch (e) { console.log('THREW ' + e.message); continue; }
    if (!r || !r.ok) { console.log('skip: ' + (r && r.skip)); continue; }
    for (const k of Object.keys(r.shots)) {
      const b = r.shots[k]; if (!b) continue;
      writeFileSync(join(OUT, 'shots', `${TAG}-${s.id}-${k}.jpg`), Buffer.from(b.split(',')[1], 'base64'));
    }
    delete r.shots;
    rows.push(r);
    const sm = summarise(r);
    console.log(`kind=${sm.kindAtMenu} fov=${sm.fov} dist=${sm.dist && sm.dist.toFixed(2)} ` +
                `foesIn(steady)=${sm.meanFoesInSteady}/${sm.foesAll} zeroFoe(steady)=${(sm.zeroFoeSteady * 100).toFixed(0)}% ` +
                `axisOk=${sm.axisOk} seats=${sm.spans.seats} resolve=${sm.spans.resolveMs}ms firstFrame=${sm.cost.firstFrameMs}ms`);
  }

  // THE RECEIPT IS THE SUMMARY PLUS A TIMELINE, NOT EVERY BOX OF EVERY SAMPLE.
  // The full per-body traces are what the summary is computed FROM and they run
  // to ~900 kB a run, which is a lot of repo for a number that is already in the
  // row above it. What survives is what a later reader can re-derive a claim
  // from: which shot was up, when, and how many foes were in the frame.
  // RUN-LENGTH, because a 40 ms sampler over an 8 s round is 200 identical rows
  // and the only thing anyone will ever read off it is WHEN THE STATE CHANGED.
  const trace = (a) => {
    const out = [];
    for (const s of (a || [])) {
      const r = { t: +s.t.toFixed(0), kind: s.kind, menu: s.menu, foesIn: s.foesIn, foesAll: s.foesAll };
      const p = out[out.length - 1];
      if (p && p.kind === r.kind && p.menu === r.menu && p.foesIn === r.foesIn) { p.until = r.t; continue; }
      out.push(r);
    }
    return out;
  };
  const slim = rows.map(r => ({
    id: r.id, zone: r.zone, at: r.at, cost: r.cost, site: r.site, tiers: r.tiers,
    spans: r.spans, log: r.log,
    cam: { kind: r.cam.kind, actor: r.cam.actor, target: r.cam.target, moves: r.cam.moves,
           refusals: r.cam.refusals, pose: r.cam.pose, axis: r.cam.axis },
    dwellSteady: summarise(r).foeInFrame,
    trace: { pre: trace(r.pre), dwell: trace(r.dwell), after: trace(r.after) },
  }));
  const out = { meta: { when: new Date().toISOString(), tag: TAG, dwellMs: DWELL,
                        three: ready.three, sites: SITES, port: PORT },
                summary: rows.map(summarise), rows: slim };
  const f = join(OUT, `decide-${TAG}.json`);
  writeFileSync(f, JSON.stringify(out, null, 1));
  console.log('WROTE ' + f);

  // ---- the headline ------------------------------------------------------
  const S = out.summary;
  if (S.length) {
    const zf = S.reduce((a, s) => a + s.zeroFoeSteady, 0) / S.length;
    const mi = S.reduce((a, s) => a + (s.meanFoesInSteady || 0), 0) / S.length;
    const sc = S.filter(s => s.spans.resolveMs != null).map(s => s.spans.resolveMs);
    const med = sc.sort((a, b) => a - b)[Math.floor(sc.length / 2)] || null;
    console.log(`\nDWELL (steady, past the 620 ms move): zero-foe ${(zf * 100).toFixed(1)}%  mean foes in frame ${mi.toFixed(2)}/${S[0].foesAll}`);
    console.log(`RESOLUTION of the round (last commit -> next round's menu): median ${med} ms`);
    const ff = S.map(s => s.cost.firstFrameMs).sort((a, b) => a - b);
    console.log(`TRIGGER->FIRST FRAME p50 ${ff[Math.floor(ff.length / 2)]} ms  max ${ff[ff.length - 1]} ms`);
  }
  cdp.close(); kill(); process.exit(0);
})();

// ---------------------------------------------------------------------------
function buildBoard() {
  const load = (t) => { const f = join(OUT, `decide-${t}.json`); return existsSync(f) ? JSON.parse(readFileSync(f, 'utf8')) : null; };
  const before = load('before'), after = load('after');
  const zones = (before || after).summary.map(s => s.id);
  const cell = (tag, id, k) => existsSync(join(OUT, 'shots', `${tag}-${id}-${k}.jpg`))
    ? `<img loading="lazy" src="shots/${tag}-${id}-${k}.jpg">` : '<div class="none">no capture</div>';
  const find = (b, id) => b ? b.summary.find(s => s.id === id) : null;
  const num = (v, d) => v == null ? '&mdash;' : (+v).toFixed(d == null ? 2 : d);
  let rowsHtml = '';
  for (const id of zones) {
    const B = find(before, id), A = find(after, id);
    const z = (B || A).zone;
    rowsHtml += `<section><h2>${id} &middot; ${z}</h2>
    <div class="pair">
      <figure><figcaption>BEFORE &mdash; the command step</figcaption>${cell('before', id, 'cmd')}
        <table class="m">
        <tr><th>shot</th><td>${B ? B.kindAtMenu : '&mdash;'}</td><th>fov</th><td>${B ? num(B.fov, 1) : '&mdash;'}</td></tr>
        <tr><th>foes in frame</th><td class="${B && B.meanFoesIn === 0 ? 'bad' : ''}">${B ? num(B.meanFoesIn) + ' / ' + B.foesAll : '&mdash;'}</td>
            <th>zero-foe dwell</th><td class="${B && B.zeroFoeFrac > 0.5 ? 'bad' : ''}">${B ? (B.zeroFoeFrac * 100).toFixed(0) + '%' : '&mdash;'}</td></tr>
        <tr><th>180&deg;</th><td>${B ? (B.axisOk ? 'ok' : 'CROSSED') : '&mdash;'}</td><th>cam dist</th><td>${B ? num(B.dist) : '&mdash;'} m</td></tr>
        </table></figure>
      <figure><figcaption>AFTER &mdash; the command step</figcaption>${cell('after', id, 'cmd')}
        <table class="m">
        <tr><th>shot</th><td>${A ? A.kindAtMenu : '&mdash;'}</td><th>fov</th><td>${A ? num(A.fov, 1) : '&mdash;'}</td></tr>
        <tr><th>foes in frame</th><td class="${A && A.meanFoesIn > 1.5 ? 'good' : ''}">${A ? num(A.meanFoesIn) + ' / ' + A.foesAll : '&mdash;'}</td>
            <th>zero-foe dwell</th><td class="${A && A.zeroFoeFrac === 0 ? 'good' : ''}">${A ? (A.zeroFoeFrac * 100).toFixed(0) + '%' : '&mdash;'}</td></tr>
        <tr><th>180&deg;</th><td>${A ? (A.axisOk ? 'ok' : 'CROSSED') : '&mdash;'}</td><th>cam dist</th><td>${A ? num(A.dist) : '&mdash;'} m</td></tr>
        </table></figure>
    </div></section>`;
  }
  const hdr = (b) => b ? `${b.meta.when.slice(0, 16).replace('T', ' ')} &middot; r${b.meta.three} &middot; dwell ${b.meta.dwellMs} ms` : 'not run';
  const cf = join(OUT, 'cost.json');
  let costHtml = '';
  if (existsSync(cf)) {
    const c = JSON.parse(readFileSync(cf, 'utf8')).rows;
    costHtml = `<h2>What it costs</h2>
    <p class="lede">A <code>decide</code> re-solve happens DURING the turn (setActor, setTarget), never at
    staging &mdash; <code>solveArena</code>, the 69.7 ms the placement lane priced, is not on this path.
    Both arms alternate inside ONE live battle off the live shot row's own <code>keep</code> field, so a
    thermal drift lands on both.</p>
    <table class="m wide"><tr><th>site</th><th>keep off p50</th><th>p90</th><th>max</th>
      <th>keep on p50</th><th>p90</th><th>max</th><th>refusals</th></tr>` +
      c.map(r => `<tr><td>${r.id} ${r.zone}</td><td>${r.off.p50}</td><td>${r.off.p90}</td><td>${r.off.max}</td>
        <td>${r.on.p50}</td><td>${r.on.p90}</td><td>${r.on.max}</td><td>${r.refusals}</td></tr>`).join('') +
      `</table>`;
  }
  // THE GENERALISATION ARM. Eight more census sites, chosen from the ones the
  // placement sort called BAD, so the claim is not carried by four good places —
  // and A/B'd on ONE build with `--keep=0`, which restores the pre-fix row.
  let wideHtml = '';
  const wOff = load('wide-off'), wOn = load('wide-on');
  if (wOff && wOn) {
    const r2 = (b, id) => b.summary.find(s => s.id === id);
    wideHtml = `<h2>Does it hold away from the good sites</h2>
    <p class="lede">Eight further census sites, all four zones, most of them sorted BAD by the placement
    lane. One build: <code>--keep=0</code> restores the pre-fix <code>decide</code> row at run time.</p>
    <table class="m wide"><tr><th>site</th><th>zone</th><th>keep off &mdash; foes in frame</th>
      <th>zero-foe dwell</th><th>keep on &mdash; foes in frame</th><th>zero-foe dwell</th><th>180&deg;</th><th>refusals</th></tr>` +
      wOn.summary.map(s => {
        const o = r2(wOff, s.id) || {};
        const rf = (wOn.rows.find(x => x.id === s.id) || {}).cam;
        return `<tr><td>${s.id}</td><td>${s.zone}</td>
          <td class="bad">${o.meanFoesInSteady} / ${o.foesAll}</td><td class="bad">${(o.zeroFoeSteady * 100).toFixed(0)}%</td>
          <td class="good">${s.meanFoesInSteady} / ${s.foesAll}</td><td class="good">${(s.zeroFoeSteady * 100).toFixed(0)}%</td>
          <td>${s.axisOk ? 'ok' : 'CROSSED'}</td><td>${rf ? rf.refusals : '&mdash;'}</td></tr>`;
      }).join('') + `</table>`;
  }
  // ---- THE CENSUS SECTION: does the placement number transfer -------------
  // The placement lane's 48.4% -> 32.3% was an eye-sort of `round` PLATES. This
  // block lays the same 62 sites' `decide` frames beside them and prints the
  // confusion matrix, because "good staging for a wide establishing shot is
  // good staging for a 27 mm two-shot" was never tested, only assumed.
  let censusHtml = '';
  const cLoad = (n) => existsSync(join(OUT, n)) ? JSON.parse(readFileSync(join(OUT, n), 'utf8')) : null;
  const pLoad = (n) => existsSync(join(ROOT, 'docs/qa/battle-placement', n))
    ? JSON.parse(readFileSync(join(ROOT, 'docs/qa/battle-placement', n), 'utf8')) : null;
  const cAfter = cLoad('census-after.json'), cBefore = cLoad('census-before.json');
  const sdA = cLoad('sort-decide-q.json'), sdB = cLoad('sort-decide.json');
  const srA = pLoad('sort-q.json'), srB = pLoad('sort.json');
  if (cAfter && sdA && srA) {
    const pile = (s) => (v) => (s.verdict[v] || '').split(/\s|—/)[0].trim();
    const RA = pile(srA), RB = pile(srB), DA = pile(sdA), DB = pile(sdB);
    const ids = Object.keys(sdA.verdict).sort();
    const CAT = ['good', 'acceptable', 'bad'];
    const dist = (f) => CAT.map(c => ids.filter(i => f(i) === c).length);
    const pct = (n) => (100 * n / ids.length).toFixed(1) + '%';
    const distRow = (lab, f) => { const d = dist(f); return `<tr><td>${lab}</td>` +
      d.map(n => `<td>${n} <span class="dim">(${pct(n)})</span></td>`).join('') + `</tr>`; };
    const matrix = (lab, A, B, an, bn) => {
      let h = `<h3>${lab}</h3><table class="m wide cm"><tr><th>${an} &darr; / ${bn} &rarr;</th>` +
        CAT.map(c => `<th>${c}</th>`).join('') + `<th>tot</th></tr>`;
      for (const r of CAT) {
        const row = CAT.map(c => ids.filter(i => A(i) === r && B(i) === c).length);
        h += `<tr><th>${r}</th>` + row.map((n, j) => `<td class="${n && r !== CAT[j] ? 'off' : ''}">${n || ''}</td>`).join('') +
             `<td>${row.reduce((a, b) => a + b, 0)}</td></tr>`;
      }
      const agree = ids.filter(i => A(i) === B(i)).length;
      const flip = ids.filter(i => (A(i) === 'good' && B(i) === 'bad') || (A(i) === 'bad' && B(i) === 'good')).length;
      h += `</table><p class="lede small">agree ${agree}/${ids.length} (${(100 * agree / ids.length).toFixed(1)}%) &middot; ` +
           `<b>good&harr;bad reversals: ${flip}</b></p>`;
      return h;
    };
    // the sites the two frames disagree about, pictured
    const dis = ids.filter(i => RA(i) !== DA(i));
    const gal = dis.map(i => `<figure><figcaption>${i} &middot; round <b>${RA(i)}</b> &rarr; decide <b>${DA(i)}</b></figcaption>
      <div class="pair2"><img loading="lazy" src="../battle-placement/sites-q/${i}.jpg">
      <img loading="lazy" src="census/after/${i}.jpg"></div></figure>`).join('');
    // the named axes, across the four analyses
    const ax = { 'round frame / ROUND sort': pLoad('axes.json'),
                 'round frame / decide sort': cLoad('axes-roundframe-decidesort-after.json'),
                 'decide frame / decide sort': cLoad('axes-decideframe-after.json') };
    const NAMED = ['surf.topSurface', 'surf.entropy', 'sun.shadedFrac', 'rays.skyFrac',
                   'site.d', 'sil.edgeRGB', 'view.back', 'view.seen'];
    const axNames = Object.keys(ax).filter(k => ax[k]);
    let axHtml = `<table class="m wide"><tr><th>axis</th>` +
      axNames.map(k => `<th>${k}<br><span class="dim">AUC / sep</span></th>`).join('') + `</tr>`;
    for (const a of NAMED) {
      axHtml += `<tr><td><code>${a}</code></td>` + axNames.map(k => {
        const r = (ax[k].axes || []).find(x => x.axis === a);
        return r ? `<td>${r.auc.toFixed(3)} / <b class="${r.sep > 0.6 ? 'good' : (r.sep < 0.35 ? 'bad' : '')}">${r.sep.toFixed(3)}</b></td>` : `<td>&mdash;</td>`;
      }).join('') + `</tr>`;
    }
    axHtml += `</table>`;
    censusHtml = `<h2>Does the placement number transfer to this frame</h2>
    <p class="lede">The placement lane censused 62 staged sites and eye-sorted them
    <b>48.4% bad &rarr; 32.3%</b> after its sun refusal. It sorted <code>round</code> PLATES.
    Here are the SAME 62 landing cells photographed at the <code>decide</code> command step
    &mdash; same party, same foes, same seed, <code>ORBIT.yaw</code> pinned, nothing driving the
    camera &mdash; and sorted by eye from contact sheets of the same geometry
    (<a href="sheets-after/sheet00.jpg">sheets-after</a> / <a href="sheets-before/sheet00.jpg">sheets-before</a>),
    before any number was opened. Method and per-site reasons: <code>sort-decide{,-q}.json</code>.</p>
    <table class="m wide"><tr><th>sort</th><th>good</th><th>acceptable</th><th>bad</th></tr>
      ${distRow('round &middot; before the sun refusal', RB)}
      ${distRow('round &middot; SHIPPED', RA)}
      ${distRow('decide &middot; before the sun refusal', DB)}
      ${distRow('decide &middot; SHIPPED', DA)}
    </table>
    <p class="lede">Read the last two rows, not the first two: <b>the frame the player lives in is
    ${pct(dist(DA)[2])} bad on the shipped build, and it was ${pct(dist(DB)[2])} bad before the sun
    refusal.</b> The refusal is worth far less here than the round headline says (&minus;3.2 points of
    bad, against &minus;16.1 on the round plates) &mdash; but it MOVES SITES UP: good 14.5% &rarr; 30.6%.</p>
    ${matrix('Round vs decide, on the shipped build', RA, DA, 'round', 'decide')}
    ${matrix('Round vs decide, before the sun refusal', RB, DB, 'round', 'decide')}
    ${matrix('What the sun refusal did to the decide frame', DB, DA, 'before', 'after')}
    <h3>Which axes still separate</h3>
    <p class="lede">Same instrument (<code>tools/battle_place_stats.py</code>), same axes, three
    labellings. <code>sep</code> is |AUC&minus;0.5|&times;2, so it is direction-free; below 0.35 is
    noise. The decide-frame column re-measures every frame axis ON the decide frame with the placement
    lane's own library (<code>tools/battle_place_lib.mjs</code>, moved verbatim so the ruler is
    literally the same object).</p>
    ${axHtml}
    <h3>The ${dis.length} sites the two frames disagree about</h3>
    <p class="lede">Left: the <code>round</code> plate the placement lane sorted. Right: the
    <code>decide</code> frame at the same site on the same build.</p>
    <div class="gal">${gal}</div>`;
  }

  // ---- THE COMPOSITED SECTION: the frame with the UI ON IT ----------------
  // Every frame above is `stage.snapshot()`, which reads the WebGL canvas. The
  // battle UI is a DOM overlay the canvas cannot see, so 124 judged frames were
  // judged without it. This block is the same 62 sites x 2 arms photographed
  // with Page.captureScreenshot at the SAME INSTANT as their canvas twin
  // (--composite=1), sorted by eye by ONE rater across all four sets so that
  // canvas-vs-composited is PAIRED and the rater cannot be the difference.
  let compHtml = '';
  const cA = cLoad('census-cAfter.json'), cB = cLoad('census-cBefore.json');
  const LS = (n) => cLoad('sort-' + n + '.json');
  const mCA = LS('mine-canvas-after'), mPA = LS('mine-comp-after'),
        mCB = LS('mine-canvas-before'), mPB = LS('mine-comp-before');
  if (cA && mCA && mPA && mCB && mPB) {
    const pil = (s) => (v) => (s.verdict[v] || '').split(/\s|—/)[0].trim();
    const CAT = ['good', 'acceptable', 'bad'];
    const ids = Object.keys(mCA.verdict).sort();
    const pct = (n) => (100 * n / ids.length).toFixed(1) + '%';
    const dist = (f) => CAT.map(c => ids.filter(i => f(i) === c).length);
    const distRow = (lab, f) => `<tr><td>${lab}</td>` +
      dist(f).map(n => `<td>${n} <span class="dim">(${pct(n)})</span></td>`).join('') + `</tr>`;
    const mx = (lab, A, B, an, bn) => {
      let h = `<h3>${lab}</h3><table class="m wide cm"><tr><th>${an} &darr; / ${bn} &rarr;</th>` +
        CAT.map(c => `<th>${c}</th>`).join('') + `<th>tot</th></tr>`;
      for (const r of CAT) {
        const row = CAT.map(c => ids.filter(i => A(i) === r && B(i) === c).length);
        h += `<tr><th>${r}</th>` + row.map((n, j) => `<td class="${n && r !== CAT[j] ? 'off' : ''}">${n || ''}</td>`).join('') +
             `<td>${row.reduce((a, b) => a + b, 0)}</td></tr>`;
      }
      const ag = ids.filter(i => A(i) === B(i)).length;
      const mv = ids.filter(i => A(i) !== B(i));
      h += `</table><p class="lede small">agree ${ag}/${ids.length} (${(100 * ag / ids.length).toFixed(1)}%) &middot; ` +
        `moved: ${mv.map(i => `<b>${i}</b> ${A(i)}&rarr;${B(i)}`).join(' &middot; ') || 'none'}</p>`;
      return h;
    };
    const KA = pil(mCA), PA = pil(mPA), KB = pil(mCB), PB = pil(mPB), RA = pil(sdA), RB = pil(sdB);
    // the panel geometry, off the capture's own getBoundingClientRect
    const r0 = cA.rows[0], vp = r0.viewport, ui = r0.ui || {};
    const ar = (q) => q ? (q.x1 - q.x0) * (q.y1 - q.y0) : 0;
    const panels = ['.ebb-rail', '.ebb-log', '.ebb-cmds', '.ebb-phead', '.ebb-party'];
    const panTbl = panels.map(k => `<tr><td><code>${k}</code></td><td>${ui[k] ? `${Math.round(ui[k].x0)},${Math.round(ui[k].y0)} &rarr; ${Math.round(ui[k].x1)},${Math.round(ui[k].y1)}` : '&mdash;'}</td>` +
      `<td>${(100 * ar(ui[k]) / (vp.w * vp.h)).toFixed(2)}%</td></tr>`).join('');
    // body-under-panel screen (approximate box off the anchor; a SCREEN, not a verdict)
    const overlap = (row) => {
      const P = panels.filter(k => k !== '.ebb-rail').map(k => (row.ui || {})[k]).filter(Boolean);
      let worst = 0, who = null;
      for (const [bid, a] of Object.entries(row.anchors || {})) {
        const hw = a.h * (bid === 'm0' ? 1.1 : 0.5);
        const bx = [a.x - hw, a.y - a.h, a.x + hw, a.y];
        const A2 = Math.max(1e-6, (bx[2] - bx[0]) * (bx[3] - bx[1]));
        let ov = 0;
        for (const p of P) ov += Math.max(0, Math.min(bx[2], p.x1) - Math.max(bx[0], p.x0)) *
                                 Math.max(0, Math.min(bx[3], p.y1) - Math.max(bx[1], p.y0));
        if (ov / A2 > worst) { worst = ov / A2; who = bid; }
      }
      return { f: worst, who: who };
    };
    const ovs = cA.rows.map(r => ({ id: r.id, ...overlap(r) })).sort((a, b) => b.f - a.f);
    const band = (t) => ovs.filter(o => o.f > t).length;
    const gal = ids.filter(i => KA(i) !== PA(i)).map(i =>
      `<figure><figcaption>${i} &middot; canvas <b>${KA(i)}</b> &rarr; composited <b>${PA(i)}</b><br>
       <span class="dim">${(mPA.verdict[i] || '').split('— ')[1] || ''}</span></figcaption>
       <img loading="lazy" src="census-c/cAfter/${i}.jpg"></figure>`).join('');
    compHtml = `<h2>The frame with the UI on it</h2>
    <p class="lede">Every plate above is <code>stage.snapshot()</code> &mdash; the WebGL canvas. <b>The battle
    UI is a DOM overlay the canvas cannot see</b>, so all 124 frames in the census above were judged without
    the boxes that sit on them in play. Here the same 62 landing cells were fought again in both arms and
    photographed with <code>Page.captureScreenshot</code> AT THE SAME INSTANT as their canvas twin
    (<code>battle_decide --mode=census --composite=1</code> splits its driver at the photograph and leaves
    the battle live &mdash; the command step is unbounded, so holding it is the real state). Staging was
    verified identical to the census above at <b>62/62</b> sites in both arms. One rater sorted all four
    sets, so canvas-vs-composited is PAIRED and the rater cannot be the difference.</p>
    <h3>What the UI actually covers</h3>
    <table class="m wide"><tr><th>panel</th><th>rect (CSS px, ${vp.w}&times;${vp.h})</th><th>share of frame</th></tr>
      ${panTbl}<tr><td><b>union of the four opaque panels</b></td><td></td><td><b>17.1%</b></td></tr></table>
    <p class="lede">The command menu is the SMALL one (2.1%). The panel that matters is <b>TURN ORDER,
    bottom-right</b> &mdash; because <code>decide</code> is a 27 mm two-shot that puts the foe line at
    screen-x 0.78, which is exactly where that panel is. Bodies with part of their box under a panel
    (an approximate box off <code>stage.anchor()</code> &mdash; a SCREEN, confirmed by eye at every site
    over 12%): <b>${band(0.10)}/62 sites over 10%, ${band(0.25)} over 25%, ${band(0.50)} over 50%</b>, and
    <b>it is the wolf every time</b> &mdash; never a party body, which stands at screen-left where only the
    2.1% command list is.</p>
    <table class="m wide"><tr><th>sort</th><th>good</th><th>acceptable</th><th>bad</th></tr>
      ${distRow('previous lane &middot; canvas &middot; SHIPPED', RA)}
      ${distRow('mine &middot; canvas &middot; pre-refusal', KB)}
      ${distRow('mine &middot; canvas &middot; SHIPPED', KA)}
      ${distRow('mine &middot; COMPOSITED &middot; pre-refusal', PB)}
      ${distRow('mine &middot; COMPOSITED &middot; SHIPPED', PA)}
    </table>
    ${mx('The answer: canvas vs composited, SHIPPED build, same battles, same rater', KA, PA, 'canvas', 'composited')}
    ${mx('And on the pre-refusal build', KB, PB, 'canvas', 'composited')}
    ${mx('Rater calibration: two people, the SAME canvas frames', RA, KA, 'previous lane', 'mine')}
    <p class="lede"><b>The menu costs 3.2 points of bad, on both arms, and it is not the menu.</b>
    Bad ${pct(dist(KA)[2])}&rarr;${pct(dist(PA)[2])} shipped and ${pct(dist(KB)[2])}&rarr;${pct(dist(PB)[2])}
    pre-refusal &mdash; the same +2 sites both times. Four of the six shipped-arm changes are the TURN-ORDER
    panel eating the wolf; one is the <code>.ebb-vig</code>/<code>.ebb-scrim</code> grade pushing an already
    dim corner under; and one goes the OTHER way (s053, where the vignette darkens the pale sandstone and
    the cream wolf separates better than it does on the canvas). <b>The sun refusal is worth the same
    &minus;3.2 points on the frame the player sees as on the canvas</b>, so the judgement transfers exactly.
    For scale: two raters applying this rubric to the SAME canvas frames differ by 9.7 points of bad and
    agree on only 43/62 sites &mdash; the UI is worth about a third of the disagreement between two people.</p>
    <h3>The ${ids.filter(i => KA(i) !== PA(i)).length} sites the UI changes, pictured</h3>
    <div class="gal">${gal}</div>
    <p class="lede small">Data: <code>census-cAfter.json</code>, <code>census-cBefore.json</code>,
    <code>sort-mine-{canvas,comp}-{after,before}.json</code>. Frames: <code>census-c/</code> (composited),
    <code>sheets-c-*</code> / <code>sheets-cv-*</code> (the contact sheets the sort was made from).
    Instrument artefacts present in the composited frames and NOT scored: the <code>?rt=1</code> debug text
    line and the &ldquo;music off&rdquo; toast are the harness&rsquo;s, not the game&rsquo;s.</p>`;
  }

  let openHtml = '';
  if (before && after) {
    const p = (b) => b.summary.map(s => s.cost.firstFrameMs).sort((x, y) => x - y);
    const st = (b) => b.rows.map(s => s.site.ms).sort((x, y) => x - y);
    const md = (a) => a[Math.floor(a.length / 2)];
    openHtml = `<h2>And the opening, which must not move</h2>
    <table class="m wide"><tr><th></th><th>staging solve p50 / max</th><th>trigger &rarr; first frame p50 / max</th></tr>
      <tr><td>before</td><td>${md(st(before))} / ${st(before).slice(-1)} ms</td><td>${md(p(before))} / ${p(before).slice(-1)} ms</td></tr>
      <tr><td>after</td><td>${md(st(after))} / ${st(after).slice(-1)} ms</td><td>${md(p(after))} / ${p(after).slice(-1)} ms</td></tr>
    </table>`;
  }
  const html = `<!doctype html><meta charset="utf-8"><title>battle-decide &mdash; the frame the player chooses in</title>
<style>
 body{background:#14161b;color:#dfe3ea;font:14px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:0 auto;padding:28px;max-width:1500px}
 h1{font-size:22px;margin:0 0 4px} h2{font-size:15px;margin:26px 0 8px;color:#9fb2d0;letter-spacing:.04em}
 p.lede{color:#9aa4b5;max-width:78ch}
 .pair{display:grid;grid-template-columns:1fr 1fr;gap:14px}
 figure{margin:0;background:#1b1f27;border:1px solid #2a3140;border-radius:7px;padding:9px}
 figcaption{font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:#8d98ab;margin-bottom:7px}
 img{width:100%;display:block;border-radius:4px}
 .none{height:180px;display:grid;place-items:center;color:#5c6577;border:1px dashed #2f3746}
 table.m{width:100%;margin-top:8px;border-collapse:collapse;font-size:12px}
table.m.wide{max-width:760px;margin:10px 0 4px}
 table.m th{text-align:left;color:#8d98ab;font-weight:500;padding:2px 8px 2px 0;white-space:nowrap}
 table.m td{padding:2px 14px 2px 0;font-variant-numeric:tabular-nums}
 .bad{color:#ff8b7a;font-weight:600}.good{color:#7fd39b;font-weight:600}
 code{background:#232833;padding:1px 5px;border-radius:3px}
 h3{font-size:13px;margin:18px 0 6px;color:#c3cede;letter-spacing:.03em}
 .dim{color:#6f7b8e;font-weight:400}
 p.lede.small{font-size:12px;margin-top:4px}
 table.m.cm td{text-align:right;padding-right:18px;min-width:64px}
 table.m.cm td.off{color:#e8c07d}
 table.m.cm th{padding-right:18px}
 .gal{display:grid;grid-template-columns:1fr 1fr;gap:12px}
 .pair2{display:grid;grid-template-columns:1fr 1fr;gap:5px}
 a{color:#8fb5ff}
</style>
<h1>The frame the player chooses in</h1>
<p class="lede">A real battle at four census sites, one per encounter zone. Nothing drives the camera:
the shot that is up is the shot the shipped code put there, and the command menu is detected off
battle_turnbased's own <code>.ebb-cmds.idle</code> class. <b>Foes in frame</b> is each foe's world
Box3 projected through the live camera and intersected with the canvas &mdash; in frame, not visible.
<b>Zero-foe dwell</b> is the fraction of sampled command-step frames containing no living foe at all.</p>
<p class="lede">before: ${hdr(before)}<br>after: ${hdr(after)}</p>
${compHtml}
${censusHtml}
${rowsHtml}
${costHtml}
${openHtml}
${wideHtml}
<h2>The denominator</h2>
<p class="lede">A round contains ONE command step per living party member &mdash; the scheduler collects
every decision before anything resolves &mdash; and each one is unbounded, because it ends when the
player presses a key. The only fixed part of a round is its resolution: <b>median 7.83 s</b> from the
last commit to the next round's first menu, measured over the same four sites, unchanged by this change.
So at two seats and a brisk one second a seat, a quarter of the round was the zero-foe frame; at a
deliberating five seconds a seat it was over half of it. The steady-state figure does not depend on
that guess: past the 620 ms move it was <b>100% zero-foe at 4/4 sites</b>, and it is now 0%.</p>
<p class="lede" style="margin-top:26px">Instrument: <code>tools/battle_decide.mjs</code>
(<code>--mode=measure|cost|board</code>).
Data: <code>decide-before.json</code>, <code>decide-after.json</code>, <code>cost.json</code>.</p>`;
  writeFileSync(join(OUT, 'index.html'), html);
  console.log('WROTE ' + join(OUT, 'index.html'));
}
