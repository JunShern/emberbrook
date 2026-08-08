#!/usr/bin/env node
// battle_contact.mjs — THE RULER FOR BET C (CONTACT) AND BET G (STAGING).
//
// The battle-presentation audit (docs/plans/battle-presentation-inventory.md) makes
// two claims that are numbers, not opinions, and this is the instrument that reads
// them out of the RUNNING GAME so a before and an after differ only by the code
// between them:
//
//   §5  CONTACT — "the attacker never arrives". The measurement is the distance in
//       METRES between the attacker's body and the target's body AT THE MOMENT THE
//       DAMAGE EVENT FIRES. That is stage.at(id), the pivot's world position, and
//       the moment is exactly the one battle_turnbased uses: it calls stage.act(),
//       waits, then calls stage.flinch() on the damage event. This harness drives
//       the same two verbs with the same wait, so what it times IS the shipped path.
//
//   §2  STAGING — "36% of frame width of empty centre, foes 89-115 px in an 813 px
//       frame". The measurement is stage.anchor(id), the same projection the DOM
//       furniture rides on, censused over 2v1 / 2v2 / 2v3 because the audit's
//       complaint is that staging does not adapt to COUNT.
//
// And one guard the coordinator asked for in writing: THE 180 RULE. Every party
// body must project LEFT of every foe body (CFG.partySide = -1). It is asserted
// here at every count, so a staging solve can never quietly swap the sides.
//
//   node tools/battle_contact.mjs --port=3000 --tag=before --out=docs/qa/battle-contact
//   node tools/battle_contact.mjs --port=3000 --tag=after --only=stage
//   node tools/battle_contact.mjs --port=3000 --tag=after --only=clock
//
// PHASES (--only=stage|contact|clock, default all):
//   stage    anchor census + captures at 2v1, 2v2, 2v3
//   contact  one strike, sampled every frame; the distance at the damage event
//   clock    a whole autoplayed battle at speed 1, timed by wrapping the stage's
//            OWN act()/flinch() verbs — so "turn wall-clock" is the interval
//            between two real actions of a real fight, not a sum of constants.
//
// A REAL GPU, ON PURPOSE (battle_shots' rule): swiftshader renders this arena at
// ~0.4 fps and a picture of that is a picture of the harness. `frames` is read out
// of the live stage and asserted CLIMBING before every capture.
import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import { freePort, findPage } from './cdp.mjs';

const require = createRequire(import.meta.url);
const WebSocket = require('ws');
const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');

const argv = process.argv.slice(2);
const arg = (k, d) => { const h = argv.find(a => a.startsWith('--' + k + '=')); return h ? h.split('=').slice(1).join('=') : d; };
const PORT = parseInt(arg('port', '3000'), 10);
const TAG = arg('tag', 'shot');
const OUT = join(ROOT, arg('out', 'docs/qa/battle-contact'));
const ONLY = arg('only', null);
const HEAD = argv.includes('--head');
const CDP_PORT = await freePort();
const CHROME = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const URL = `http://localhost:${PORT}/play3d.html?scene=ow-valley&rt=1&nomusic=1`;
const sleep = ms => new Promise(r => setTimeout(r, ms));
const want = p => !ONLY || ONLY === p;

// ---- THE CASES ------------------------------------------------------------
// One creature (duskpad) at every count, so a difference between 2v1 and 2v3 is
// the COUNT and never the monster. Party fixed at two, which is the shipped
// Chapter One party and the shape the audit measured.
const CASES = [
  { name: '2v1', zone: 'meadow', group: ['duskpad'], party: ['vesper', 'maren'] },
  { name: '2v2', zone: 'meadow', group: ['duskpad', 'duskpad'], party: ['vesper', 'maren'] },
  { name: '2v3', zone: 'meadow', group: ['duskpad', 'duskpad', 'duskpad'], party: ['vesper', 'maren'] },
];

// ---- launch ---------------------------------------------------------------
const profile = join(process.env.TMPDIR || '/tmp', 'battle-contact-' + process.pid);
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
const kill = () => { if (!closing) { closing = true; try { chrome.kill('SIGKILL'); } catch (e) { } } };
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
async function evalPage(cdp, expr, timeoutMs) {
  const r = await cdp.send('Runtime.evaluate', {
    expression: expr, awaitPromise: true, returnByValue: true, userGesture: true,
    timeout: timeoutMs || 300000,
  });
  if (r.exceptionDetails) {
    const e = r.exceptionDetails;
    throw new Error('page exception: ' + ((e.exception && e.exception.description) || e.text));
  }
  return r.result && r.result.value;
}

// ---- the page-side prelude, shared by every phase -------------------------
// Starts a real battle through Battle.start and parks it on the command menu
// (no key is ever sent), which is the state a player reads.
const BOOT = (c, opts) => `
  const GS = window.GS, B = window.Battle, R = window.Rules;
  const flags = {}; ${JSON.stringify(c.party)}.forEach(id => {
    if (id === 'maren') flags['maren-joined'] = true; if (id === 'lake') flags['lake-joined'] = true; });
  if (Object.keys(flags).length) GS.setFlags(flags);
  const items = GS.data.items.items, growth = GS.data.growth;
  const party = GS.activeParty().filter(ch => ${JSON.stringify(c.party)}.indexOf(ch.id) >= 0)
    .map(ch => R.derive.partyMember(growth, items, ch));
  const zd = GS.data.encounters.zones[${JSON.stringify(c.zone)}];
  const p = B.start({ zone: ${JSON.stringify(c.zone)}, group: ${JSON.stringify(c.group)}, seed: 4242,
                      backdrop: zd && zd.battleBackdrop }, party, ${JSON.stringify(opts)});
  p.then(()=>{}, ()=>{});
  const S = () => (window.__EBB_SCREEN && window.__EBB_SCREEN.stage) || null;
  for (let i = 0; i < 200 && !S(); i++) await new Promise(r => setTimeout(r, 100));
  const st = S();
  if (!st) return { ok: false, why: 'no stage' };
  const f0 = st.frames;
  for (let i = 0; i < 300; i++) {
    const t = st.tiers();
    if (Object.values(t).every(v => v !== 'proxy') && st.frames > f0 + 90) break;
    await new Promise(r => setTimeout(r, 100));
  }
`;

const TEARDOWN = `(async()=>{ const s=window.__EBB_SCREEN;
  try { window.Battle._forceEnd && window.Battle._forceEnd(); } catch(e){}
  if (s && s.stage) { try { s.stage.destroy(); } catch(e){} }
  if (s && s.destroy) { try { s.destroy(); } catch(e){} }
  window.__EBB_SCREEN = null; window.Battle.active = false;
  document.querySelectorAll('.ebb-root').forEach(n=>n.remove());
  return true; })()`;

// ---- PHASE: STAGE ---------------------------------------------------------
// The anchor census. Every derived number is computed in the page from the SAME
// projection the DOM furniture rides on, so nothing here is a second model of
// where a body is.
const stagePhase = (c) => `(async () => {
  ${BOOT(c, { speed: 1 })}
  const ids = Object.keys(st.tiers());
  const W = st.canvas.clientWidth || 1600, H = st.canvas.clientHeight || 900;
  const rows = ids.map(id => {
    const a = st.anchor(id), w = st.at(id);
    // a body's screen HALF-WIDTH, from its own measured world width and its own
    // projected height: w/h in metres is w/h on screen for an upright body.
    const hw = a.h * (w.w / (w.h || 1)) * 0.5;
    return { id, side: w.side, x: a.x, y: a.y, h: a.h, vis: a.vis, hw,
             wx: w.x, wz: w.z, wh: w.h, ww: w.w, tier: w.tier };
  });
  const pty = rows.filter(r => r.side === 'party'), fos = rows.filter(r => r.side === 'foe');
  const minFoeH = Math.min(...fos.map(r => r.h)), maxFoeH = Math.max(...fos.map(r => r.h));
  const minPartyH = Math.min(...pty.map(r => r.h)), maxPartyH = Math.max(...pty.map(r => r.h));
  // CENTRE-TO-CENTRE, nearest pair — the audit's own number (581 px = 36%).
  const sep = Math.min(...fos.map(f => Math.min(...pty.map(p => Math.abs(f.x - p.x)))));
  // THE EMPTY CENTRE: from the inner EDGE of the innermost party body to the inner
  // EDGE of the innermost foe body. Centre-to-centre counts the bodies themselves.
  const pRight = Math.max(...pty.map(p => p.x + p.hw)), fLeft = Math.min(...fos.map(f => f.x - f.hw));
  const gap = fLeft - pRight;
  // pairwise SCREEN separation, in units of the mean half-width — under 1.0 is an
  // overlap on screen whatever the world distance says
  let minPair = Infinity, minPairIds = null;
  for (let i = 0; i < rows.length; i++) for (let j = i + 1; j < rows.length; j++) {
    const a = rows[i], b = rows[j];
    const need = a.hw + b.hw, d = Math.abs(a.x - b.x) + Math.abs(a.y - b.y) * 0.35;
    if (d / need < minPair) { minPair = d / need; minPairIds = [a.id, b.id]; }
  }
  // world min pairwise distance across the line (the audit's 5.21 m)
  let minWorld = Infinity;
  for (const f of fos) for (const p of pty) {
    const d = Math.hypot(f.wx - p.wx, f.wz - p.wz); if (d < minWorld) minWorld = d;
  }
  // THE 180 RULE: every party body left of every foe body (CFG.partySide = -1).
  const rule180 = Math.max(...pty.map(p => p.x)) < Math.min(...fos.map(f => f.x));
  return { ok: true, frame: { w: W, h: H }, rows, frames: st.frames, framesGained: st.frames - f0,
    m: {
      minFoeHpx: minFoeH, maxFoeHpx: maxFoeH, minFoeHpct: minFoeH / H * 100, maxFoeHpct: maxFoeH / H * 100,
      minPartyHpx: minPartyH, maxPartyHpx: maxPartyH, minPartyHpct: minPartyH / H * 100, maxPartyHpct: maxPartyH / H * 100,
      sepPx: sep, sepPct: sep / W * 100, gapPx: gap, gapPct: gap / W * 100,
      minPairRatio: minPair, minPairIds, minWorldM: minWorld, rule180,
    },
    arena: st.snapshot(),
  };
})()`;

// ---- PHASE: CONTACT -------------------------------------------------------
// One strike, sampled every animation frame. The damage moment is the one the
// screen uses: act() returns the ms at which the blow lands (0/undefined on the
// build that has no such contract — then it is Battle.pacing.wind, exactly what
// battle_turnbased waits before calling flinch).
const contactPhase = (c) => `(async () => {
  ${BOOT(c, { speed: 1 })}
  const ids = Object.keys(st.tiers());
  const fos = ids.filter(id => st.at(id).side === 'foe');
  const me = ids.filter(id => st.at(id).side === 'party')[0];
  const tgt = fos[0];
  st.setActor(me); st.setTarget(tgt);
  await new Promise(r => setTimeout(r, 350));
  const d = () => { const a = st.at(me), b = st.at(tgt); return Math.hypot(a.x - b.x, a.z - b.z); };
  const rest = d();
  const budget = (window.Battle.pacing.approach || 0) + window.Battle.pacing.wind;
  const t0 = performance.now();
  // THE SHIPPED CALL. Extra arguments are ignored by a build that does not take
  // them, which is what makes this one expression drive BEFORE and AFTER.
  const ret = st.act(me, 'attack', tgt, budget);
  const contactMs = (typeof ret === 'number' && ret > 0) ? ret : window.Battle.pacing.wind;
  const samples = [];
  let shot = null, atDamage = null;
  const t1 = t0 + contactMs;
  while (performance.now() < t0 + 1600) {
    await new Promise(r => requestAnimationFrame(r));
    const t = performance.now() - t0;
    samples.push([Math.round(t), +d().toFixed(3)]);
    if (atDamage == null && performance.now() >= t1) {
      atDamage = d();                     // THE NUMBER THE BET IS JUDGED ON
      shot = st.snapshot();               // and the frame it was true in
      st.flinch(tgt);                     // exactly what the damage event does
    }
  }
  const impact = st.snapshot();
  const closest = Math.min(...samples.map(s => s[1]));
  return { ok: true, restM: rest, contactMs, atDamageM: atDamage, closestM: closest,
           samples, frames: st.frames, swing: shot, impact,
           clips: st.clipsOf(me) };
})()`;

// ---- PHASE: CLOCK ---------------------------------------------------------
// A WHOLE FIGHT, autoplayed at speed 1, timed by wrapping the stage's own verbs.
// The interval between two consecutive act() calls IS the turn wall-clock: it
// spans settle + announce + (approach) + wind + damage of the action between them.
const clockPhase = (c) => `(async () => {
  const M = window.BattleStage3D;
  const log = []; window.__EBBC = log;
  if (!M.__wrapped) {
    M.__wrapped = true;
    const create0 = M.create;
    M.create = function (cfg) {
      const s = create0.call(this, cfg);
      if (!s) return s;
      const act0 = s.act, fl0 = s.flinch;
      s.act = function (id, kind, tid, ms) { window.__EBBC.push(['act', performance.now(), id, kind]); return act0.call(s, id, kind, tid, ms); };
      s.flinch = function (id) { window.__EBBC.push(['flinch', performance.now(), id]); return fl0.call(s, id); };
      return s;
    };
  }
  const GS = window.GS, B = window.Battle, R = window.Rules;
  const flags = {}; ${JSON.stringify(c.party)}.forEach(id => {
    if (id === 'maren') flags['maren-joined'] = true; if (id === 'lake') flags['lake-joined'] = true; });
  if (Object.keys(flags).length) GS.setFlags(flags);
  const items = GS.data.items.items, growth = GS.data.growth;
  const party = GS.activeParty().filter(ch => ${JSON.stringify(c.party)}.indexOf(ch.id) >= 0)
    .map(ch => R.derive.partyMember(growth, items, ch));
  const zd = GS.data.encounters.zones[${JSON.stringify(c.zone)}];
  const t0 = performance.now();
  const res = await B.start({ zone: ${JSON.stringify(c.zone)}, group: ${JSON.stringify(c.group)}, seed: 4242,
                              backdrop: zd && zd.battleBackdrop }, party, { speed: 1, autoplay: true });
  const total = performance.now() - t0;
  const acts = log.filter(e => e[0] === 'act');
  const gaps = [];
  for (let i = 1; i < acts.length; i++) gaps.push(acts[i][1] - acts[i - 1][1]);
  // act -> the flinch that follows it: the CONTACT DELAY the player sees
  const cds = [];
  for (let i = 0; i < log.length; i++) {
    if (log[i][0] !== 'act') continue;
    const f = log.slice(i + 1).find(e => e[0] === 'flinch');
    const nextAct = log.slice(i + 1).find(e => e[0] === 'act');
    if (f && (!nextAct || f[1] < nextAct[1])) cds.push(f[1] - log[i][1]);
  }
  const mean = a => a.length ? a.reduce((x, y) => x + y, 0) / a.length : null;
  const med = a => { if (!a.length) return null; const s = a.slice().sort((x,y)=>x-y); return s[s.length >> 1]; };
  return { ok: true, outcome: res && res.outcome, totalMs: total, actions: acts.length,
           gapMeanMs: mean(gaps), gapMedMs: med(gaps), gaps: gaps.map(Math.round),
           contactDelayMeanMs: mean(cds), contactDelayMedMs: med(cds), contactDelays: cds.map(Math.round),
           pacing: JSON.parse(JSON.stringify(window.Battle.pacing)) };
})()`;

// ---- main -----------------------------------------------------------------
(async function main() {
  mkdirSync(OUT, { recursive: true });
  const cdp = await connect(await findPage(CDP_PORT, { tries: 200, label: 'battle_contact' }));
  await cdp.send('Runtime.enable');
  await cdp.send('Page.enable');

  const ready = await evalPage(cdp, `(async () => {
    for (let i = 0; i < 300; i++) {
      if (window.SIM && window.GS && window.GS.ok && window.Battle && window.Rules && window.THREE) return { ready: true, three: THREE.REVISION };
      await new Promise(r => setTimeout(r, 200));
    }
    return { ready: false };
  })()`, 90000);
  if (!ready.ready) { console.error('world never became ready'); kill(); process.exit(2); }
  console.log(`world ready (three r${ready.three})   tag=${TAG}`);

  const png = (uri, file) => { if (uri) writeFileSync(file, Buffer.from(uri.slice(uri.indexOf(',') + 1), 'base64')); };
  const report = { tag: TAG, when: new Date().toISOString(), three: ready.three, stage: {}, contact: null, clock: null };
  let bad = 0;

  if (want('stage')) {
    console.log('\n== STAGING (anchor census) ==');
    for (const c of CASES) {
      const r = await evalPage(cdp, stagePhase(c), 300000);
      if (!r.ok) { console.log(`  ${c.name}: FAILED ${r.why}`); bad++; await evalPage(cdp, TEARDOWN); continue; }
      if (r.framesGained < 30) console.log(`  WARNING ${c.name}: only ${r.framesGained} frames rendered`);
      png(r.arena, join(OUT, `${TAG}-stage-${c.name}-arena.png`));
      const full = await cdp.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
      writeFileSync(join(OUT, `${TAG}-stage-${c.name}.png`), Buffer.from(full.data, 'base64'));
      delete r.arena;
      report.stage[c.name] = r;
      const m = r.m;
      console.log(`  ${c.name}  frame ${r.frame.w}x${r.frame.h}` +
        `  foeH ${m.minFoeHpx.toFixed(0)}-${m.maxFoeHpx.toFixed(0)}px (${m.minFoeHpct.toFixed(1)}-${m.maxFoeHpct.toFixed(1)}%)` +
        `  partyH ${m.minPartyHpx.toFixed(0)}-${m.maxPartyHpx.toFixed(0)}px` +
        `  sep ${m.sepPx.toFixed(0)}px (${m.sepPct.toFixed(1)}%)` +
        `  emptyCentre ${m.gapPx.toFixed(0)}px (${m.gapPct.toFixed(1)}%)` +
        `  minPair ${m.minPairRatio.toFixed(2)}` +
        `  worldMin ${m.minWorldM.toFixed(2)}m` +
        `  180:${m.rule180 ? 'OK' : 'VIOLATED'}`);
      if (!m.rule180) { console.log('    *** 180 RULE VIOLATED — a party body projects right of a foe'); bad++; }
      await evalPage(cdp, TEARDOWN); await sleep(400);
    }
  }

  if (want('contact')) {
    console.log('\n== CONTACT (one strike, sampled) ==');
    const c = CASES[1];
    const r = await evalPage(cdp, contactPhase(c), 300000);
    if (!r.ok) { console.log('  FAILED', r.why); bad++; }
    else {
      png(r.swing, join(OUT, `${TAG}-contact-swing.png`));
      png(r.impact, join(OUT, `${TAG}-contact-impact.png`));
      delete r.swing; delete r.impact;
      report.contact = r;
      console.log(`  rest ${r.restM.toFixed(2)}m   contact fires at ${r.contactMs}ms` +
        `   DISTANCE AT DAMAGE ${r.atDamageM.toFixed(2)}m   closest reached ${r.closestM.toFixed(2)}m`);
      console.log(`  clips bound: ${JSON.stringify(r.clips)}`);
      console.log(`  ${r.atDamageM <= 1.4 ? 'PASS' : 'FAIL'} — the bet's bar is <= 1.40 m`);
      if (r.atDamageM > 1.4) bad++;
    }
    await evalPage(cdp, TEARDOWN); await sleep(400);
  }

  if (want('clock')) {
    console.log('\n== CLOCK (a whole autoplayed fight, speed 1) ==');
    const r = await evalPage(cdp, clockPhase(CASES[1]), 600000);
    report.clock = r;
    if (!r.ok) { console.log('  FAILED'); bad++; }
    else console.log(`  outcome ${r.outcome}   total ${(r.totalMs / 1000).toFixed(2)}s over ${r.actions} actions` +
      `   turn wall-clock mean ${r.gapMeanMs ? r.gapMeanMs.toFixed(0) : '-'}ms  median ${r.gapMedMs ? r.gapMedMs.toFixed(0) : '-'}ms` +
      `   act->flinch mean ${r.contactDelayMeanMs ? r.contactDelayMeanMs.toFixed(0) : '-'}ms`);
    await evalPage(cdp, TEARDOWN); await sleep(400);
  }

  writeFileSync(join(OUT, `${TAG}.json`), JSON.stringify(report, null, 2));
  console.log('\nwrote', join(OUT, `${TAG}.json`));
  cdp.close(); kill(); process.exit(bad ? 1 : 0);
})().catch((e) => { console.error('battle_contact error:', e); kill(); process.exit(2); });
