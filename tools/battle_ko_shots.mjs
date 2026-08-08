#!/usr/bin/env node
// battle_ko_shots.mjs — MEASURE AND PHOTOGRAPH THE KO AND THE VICTORY.
//
// The eye gate and the ruler for slate BET I (KO AND VICTORY AS EVENTS). It
// answers four questions that battle_shots.mjs cannot, because battle_shots
// photographs three fixed offsets and this has to watch a whole beat:
//
//   1. WHERE DOES THE BODY END UP — `stage.at(id).y` sampled every ~40 ms from
//      before the blow to two and a half seconds after it, against the y the same
//      body had while it was alive. A NEGATIVE number is the body going THROUGH
//      the floor (the shipped 0.55 m sink), and in ?arena=world that floor is real
//      terrain.
//   2. IS ANYTHING STILL THERE — `at(id).alpha`, so "the corpse evaporated" is a
//      number and not an impression.
//   3. DOES ANYBODY ELSE MOVE — every OTHER body's `anchor(id)` sampled on the same
//      tick, reported as peak |dx| / |dh| in SCREEN PIXELS against its own pre-blow
//      baseline. Pixels, because the claim is "nobody in the frame reacts to the
//      kill" and the frame is what the player has.
//   4. DOES THE KILLING BLOW FLASH AT ALL — the shipped screen calls
//      syncHp() (-> stage.setDead) BEFORE hitShake() (-> stage.flinch), and
//      flinch() returns early on a dead body. So the loudest blow in the fight got
//      no flash, no sparks and no shock ring. Measured here as the MEAN LUMINANCE
//      of the victim's own screen box 60 ms after the blow, once for a survivable
//      hit and once for a killing one, in the same battle.
//
// The KO scenario drives the stage EXACTLY the way battle_turnbased does
// (`setDead(id,true)` then `flinch(id)`), never `ko()` on its own, because the
// order of those two calls IS the defect in (4).
//
// The victory scenario runs a REAL autoplay battle to its end (no stage verbs at
// all) and photographs the last foe going down, the held moment, the cheer and the
// tally, so "the tally box covers the party it celebrates" is a picture.
//
//   node tools/battle_ko_shots.mjs --port=3000 --tag=before --out=docs/qa/battle-ko
//   node tools/battle_ko_shots.mjs --port=3000 --tag=before-world --arena=world
//
// A REAL GPU (no --use-angle), frames asserted climbing before every capture, and
// Chrome launched + reaped through its own --user-data-dir prefix via cdp.mjs.
import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync, rmSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import { freePort, findPage, sweepStaleProfiles } from './cdp.mjs';

const require = createRequire(import.meta.url);
const WebSocket = require('ws');
const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');

const argv = process.argv.slice(2);
const arg = (k, d) => { const h = argv.find(a => a.startsWith('--' + k + '=')); return h ? h.split('=').slice(1).join('=') : d; };
const PORT = parseInt(arg('port', '3000'), 10);
const TAG = arg('tag', 'ko');
const OUT = join(ROOT, arg('out', 'docs/qa/battle-ko'));
const ARENA = arg('arena', null);
const ONLY = arg('only', null);              // 'ko' | 'victory'
const HEAD = argv.includes('--head');
// THE A/B FOR THE REACTION, on ONE build. Sets CFG.ko.react amplitudes to zero
// before the blow, so the same instrument measures the same frame with the only
// difference being whether the survivors react. Cleaner than photographing two
// checkouts, because the KO staging underneath is held constant.
const NOREACT = argv.includes('--noreact');
const CDP_PORT = await freePort();
const CHROME = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const URL = `http://localhost:${PORT}/play3d.html?scene=ow-valley&rt=1&nomusic=1`
          + (ARENA ? `&arena=${encodeURIComponent(ARENA)}` : '');
const sleep = ms => new Promise(r => setTimeout(r, ms));

// EVERY PROFILE THIS TOOL HAS EVER LEFT BEHIND, before it makes another one. A
// run of this tool costs ~100 MB of Chrome profile and twelve of them had already
// accumulated; the repo's rule about a browser tool reaping after itself is about
// swap, but the disk half is free to honour. Only this tool's own prefix is
// touched, and only entries older than the default age.
sweepStaleProfiles('battle-ko-shots-');
const profile = join(process.env.TMPDIR || '/tmp', 'battle-ko-shots-' + process.pid);
const chrome = spawn(CHROME, [
  `--remote-debugging-port=${CDP_PORT}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--disable-extensions',
  '--autoplay-policy=no-user-gesture-required',
  '--hide-scrollbars', '--force-device-scale-factor=1', '--window-size=1600,900',
  ...(HEAD ? [] : ['--headless=new']),
  URL,
], { stdio: 'ignore' });
let closing = false;
const kill = () => {
  if (closing) return;
  closing = true;
  try { chrome.kill('SIGKILL'); } catch (e) { }
  try { rmSync(profile, { recursive: true, force: true }); } catch (e) { }
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

// AN ID IS NOT A SIDE (battle_shots.mjs, d865ee80). Ask the stage — BOTH arenas
// carry sides() now (battle_world.js :1427, battle_stage3d.js :3259), the value
// newBody() was constructed with. The path that answered is REPORTED, never
// assumed, and the id pattern is a labelled last resort.
const SIDE_JS = `
  let SIDE_VIA = 'id-pattern-fallback';
  const sideOf = (id) => {
    if (typeof st.sides === 'function') { const s = st.sides(); if (s && s[id]) { SIDE_VIA = 'stage.sides()'; return s[id]; } }
    if (typeof st.at === 'function') { const a = st.at(id); if (a && a.side) { SIDE_VIA = 'stage.at().side'; return a.side; } }
    return /^m\\d+$/.test(id) ? 'foe' : 'party';
  };
  const roster = Object.keys(st.tiers()).map(id => ({ id, side: sideOf(id) }));
  const FOES = roster.filter(r => r.side === 'foe').map(r => r.id);
  const ALLIES = roster.filter(r => r.side !== 'foe').map(r => r.id);
  const SIDE_RES = { via: SIDE_VIA, party: ALLIES, foes: FOES };
  if (FOES.length < 2) throw new Error('need two foes: ' + JSON.stringify(roster));
  if (ALLIES.indexOf(FOES[0]) >= 0) throw new Error('an id is not a side');
`;

// MEAN LUMINANCE OF A BODY'S OWN SCREEN BOX, out of a synchronous stage render.
// The flash is a 150 ms event; a screenshot cannot be trusted to catch it, so the
// pixels come from stage.snapshot() (renderFrame + toDataURL) decoded in-page.
const LUM_JS = `
  const lumBox = async (uri, a) => {
    if (!uri || !a) return null;
    const img = new Image();
    await new Promise((ok, no) => { img.onload = ok; img.onerror = no; img.src = uri; });
    const cv = document.createElement('canvas'); cv.width = img.width; cv.height = img.height;
    const cx = cv.getContext('2d'); cx.drawImage(img, 0, 0);
    // the stage canvas may be a different pixel size from the CSS box the anchor
    // is quoted in: anchors come back in CSS px of the canvas rect
    const rect = st.canvas.getBoundingClientRect();
    const sx = img.width / Math.max(1, rect.width), sy = img.height / Math.max(1, rect.height);
    const w = Math.max(8, a.h * 0.6), x0 = Math.round((a.x - w / 2 - rect.left) * sx);
    const y0 = Math.round((a.y - a.h - rect.top) * sy), h = Math.round(a.h * sy);
    const X = Math.max(0, Math.min(img.width - 2, x0)), Y = Math.max(0, Math.min(img.height - 2, y0));
    const W = Math.max(2, Math.min(img.width - X, Math.round(w * sx))), H = Math.max(2, Math.min(img.height - Y, h));
    const d = cx.getImageData(X, Y, W, H).data;
    let s = 0; for (let i = 0; i < d.length; i += 4) s += 0.299 * d[i] + 0.587 * d[i + 1] + 0.114 * d[i + 2];
    return +(s / (d.length / 4)).toFixed(2);
  };
  // THE PIXELS OF A BODY'S OWN BOX, so two frames can be differenced. anchor()
  // projects the PIVOT and a CONSTANT height, so it is blind to every procedural
  // layer in battle_stage3d by construction — the swing, the recoil, the flee turn
  // and the KO reaction all live on the 'bob' node, which anchor never reads. Measuring
  // "did anybody else move" off anchor therefore reports 3-5 px of noise whether
  // the reaction fired or not. It has to be pixels.
  const grabBox = async (uri, a) => {
    if (!uri || !a) return null;
    const img = new Image();
    await new Promise((ok, no) => { img.onload = ok; img.onerror = no; img.src = uri; });
    const cv = document.createElement('canvas'); cv.width = img.width; cv.height = img.height;
    const cx = cv.getContext('2d'); cx.drawImage(img, 0, 0);
    const rect = st.canvas.getBoundingClientRect();
    const sx = img.width / Math.max(1, rect.width), sy = img.height / Math.max(1, rect.height);
    // GENEROUS: a body that turns or leans sweeps OUTSIDE its own standing box
    const w = Math.max(24, a.h * 1.6), hh = Math.max(24, a.h * 1.5);
    const X = Math.max(0, Math.min(img.width - 4, Math.round((a.x - w / 2 - rect.left) * sx)));
    const Y = Math.max(0, Math.min(img.height - 4, Math.round((a.y - a.h * 1.15 - rect.top) * sy)));
    const W = Math.max(4, Math.min(img.width - X, Math.round(w * sx)));
    const H = Math.max(4, Math.min(img.height - Y, Math.round(hh * sy)));
    return { d: cx.getImageData(X, Y, W, H).data, W: W, H: H };
  };
  const boxDiff = (a, b) => {
    if (!a || !b || a.W !== b.W || a.H !== b.H) return null;
    let s = 0, n = 0;
    for (let i = 0; i < a.d.length; i += 4) {
      const la = 0.299 * a.d[i] + 0.587 * a.d[i + 1] + 0.114 * a.d[i + 2];
      const lb = 0.299 * b.d[i] + 0.587 * b.d[i + 1] + 0.114 * b.d[i + 2];
      s += Math.abs(la - lb); n++;
    }
    return +(s / Math.max(1, n)).toFixed(2);
  };
`;

// ---- boot a battle and park it (no key is ever sent) ----------------------
const BOOT = (party, zone, group) => `
  const GS = window.GS, B = window.Battle, R = window.Rules;
  const flags = {}; ${JSON.stringify(party)}.forEach(id => { if (id === 'maren') flags['maren-joined'] = true; if (id === 'lake') flags['lake-joined'] = true; });
  if (Object.keys(flags).length) GS.setFlags(flags);
  const items = GS.data.items.items, growth = GS.data.growth;
  const members = GS.activeParty().filter(ch => ${JSON.stringify(party)}.indexOf(ch.id) >= 0)
    .map(ch => R.derive.partyMember(growth, items, ch));
  const zd = GS.data.encounters.zones[${JSON.stringify(zone)}];
`;
const WAIT_STAGE = `
  const SR = () => (window.__EBB_SCREEN && window.__EBB_SCREEN.stage) || null;
  for (let i = 0; i < 250 && !SR(); i++) await new Promise(r => setTimeout(r, 100));
  const st = SR();
  if (!st) return { ok: false, why: 'no stage' };
  const f0 = st.frames;
  for (let i = 0; i < 300; i++) {
    const settled = Object.values(st.tiers()).every(v => v !== 'proxy');
    if (settled && st.frames > f0 + 90) break;
    await new Promise(r => setTimeout(r, 100));
  }
`;

// ============================ SCENARIO 1: THE KO ============================
const koDrive = `(async () => {
  ${BOOT(['vesper', 'maren'], 'meadow', ['duskpad', 'duskpad'])}
  const p = B.start({ zone: 'meadow', group: ['duskpad','duskpad'], seed: 4242, backdrop: zd && zd.battleBackdrop },
                    members, { speed: 1 });
  p.then(()=>{},()=>{});
  ${WAIT_STAGE}
  ${SIDE_JS}
  ${LUM_JS}
  const VICTIM = FOES[0], OTHER = FOES[1], ACTOR = 'vesper';
  const KCFG = window.BattleStage3D && window.BattleStage3D.CFG && window.BattleStage3D.CFG.ko;
  if (${NOREACT ? 'true' : 'false'} && KCFG) { KCFG.react.lean = 0; KCFG.react.look = 0; }
  const ids = Object.keys(st.tiers());
  const snap = (id) => { const a = st.anchor(id) || {}; const w = (st.at && st.at(id)) || {};
    return { ax: a.x, ay: a.y, ah: a.h, vis: a.vis, y: w.y, x: w.x, z: w.z, alpha: w.alpha, dead: w.dead,
             bob: w.bob ? Math.max(Math.abs(w.bob.x), Math.abs(w.bob.y), Math.abs(w.bob.z)) : null }; };
  const sampleAll = () => { const o = {}; for (const id of ids) o[id] = snap(id); return o; };

  // --- (4) A SURVIVABLE HIT FIRST, in the same battle and on the same body type.
  st.setTarget(OTHER); st.setActor(ACTOR);
  st.flinch(OTHER);
  await new Promise(r => setTimeout(r, 60));
  const hitShot = st.snapshot();
  const hitLum = await lumBox(hitShot, st.anchor(OTHER));
  await new Promise(r => setTimeout(r, 700));
  const baseShot = st.snapshot();
  const baseLum = await lumBox(baseShot, st.anchor(OTHER));

  // --- the KO, driven the way the screen drives it -------------------------
  st.setTarget(VICTIM); st.setActor(ACTOR);
  const before = sampleAll();
  st.act(ACTOR, 'attack', VICTIM, 560);            // the real approach, so the killer is AT the body
  await new Promise(r => setTimeout(r, 560));
  const shots = {}, series = [];
  // THE BASELINE FRAME every other body's pixels are differenced against, taken
  // one frame before the blow lands.
  const baseShotK = st.snapshot();
  const baseBox = {};
  for (const id of ids) baseBox[id] = await grabBox(baseShotK, st.anchor(id));
  const pxDiff = {};
  const t0 = performance.now();
  // battle_turnbased: syncHp() -> setDead, THEN hitShake() -> flinch. That order.
  st.setDead(VICTIM, true);
  st.flinch(VICTIM);
  const marks = [80, 200, 340, 620, 1000, 1500, 2100, 2800];
  let mi = 0;
  let killLum = null;
  while (performance.now() - t0 < 3000) {
    const t = performance.now() - t0;
    series.push(Object.assign({ t: Math.round(t) }, { b: sampleAll() }));
    if (mi < marks.length && t >= marks[mi]) {
      shots['t' + marks[mi]] = st.snapshot();
      if (marks[mi] === 80) killLum = await lumBox(shots.t80, st.anchor(VICTIM) || before[VICTIM] && { x: before[VICTIM].ax, y: before[VICTIM].ay, h: before[VICTIM].ah });
      // DID ANYBODY ELSE MOVE, in the only currency that counts
      for (const id of ids) {
        if (id === VICTIM) continue;
        const g = await grabBox(shots['t' + marks[mi]], st.anchor(id));
        const d = boxDiff(baseBox[id], g);
        if (d != null) pxDiff[id] = Math.max(pxDiff[id] || 0, d);
      }
      mi++;
    }
    await new Promise(r => setTimeout(r, 34));
  }
  return { ok: true, kind: 'ko', victim: VICTIM, other: OTHER, actor: ACTOR, foes: FOES, allies: ALLIES, sideResolution: SIDE_RES,
           noreact: ${NOREACT ? 'true' : 'false'},
           before, series, shots, pxDiff, lum: { base: baseLum, hit: hitLum, kill: killLum },
           frames: st.frames, framesGained: st.frames - f0 };
})()`;

// ========================= SCENARIO 2: THE VICTORY ==========================
// A real autoplay battle, run to its end. No stage verb is called: everything is
// battle_turnbased driving its own screen, which is the only way the victory
// SEQUENCE (last foe down -> hold -> cheer -> tally) can be photographed honestly.
const victoryStart = `(async () => {
  ${BOOT(['vesper', 'maren'], 'meadow', ['reed-nibbler'])}
  window.__KO_DONE = null;
  const p = B.start({ zone: 'meadow', group: ['reed-nibbler'], seed: 7, backdrop: zd && zd.battleBackdrop },
                    members, { speed: 1, autoplay: true });
  window.__KO_BATTLE = p; p.then(r => { window.__KO_DONE = r; }, e => { window.__KO_DONE = { error: String(e) }; });
  ${WAIT_STAGE}
  window.__KO_STAGE = st;
  return { ok: true, ids: Object.keys(st.tiers()), framesGained: st.frames - f0 };
})()`;

const victoryPoll = `(() => {
  const st = window.__KO_STAGE;
  const out = { outro: !!document.querySelector('.ebb-outro'), done: !!window.__KO_DONE };
  if (!st) return out;
  try {
    const sides = typeof st.sides === 'function' ? st.sides() : null;
    const ids = Object.keys(st.tiers());
    out.foesAlive = ids.filter(id => {
      const side = sides ? sides[id] : ((st.at && st.at(id) || {}).side);
      if (side !== 'foe') return false;
      const a = st.at ? st.at(id) : null;
      return a && !a.dead;
    }).length;
    out.frames = st.frames;
  } catch (e) { out.err = String(e); }
  return out;
})()`;

// Tear a battle down between scenarios. Same shape battle_shots.mjs uses.
const TEARDOWN = `(async () => {
  const s = window.__EBB_SCREEN;
  if (window.Battle) { try { window.Battle._forceEnd && window.Battle._forceEnd(); } catch (e) { } }
  if (s && s.stage) { try { s.stage.destroy(); } catch (e) { } }
  if (s && s.destroy) { try { s.destroy(); } catch (e) { } }
  window.__EBB_SCREEN = null; window.__KO_STAGE = null;
  if (window.Battle) window.Battle.active = false;
  document.querySelectorAll('.ebb-root').forEach(n => n.remove());
  return true;
})()`;

(async function main() {
  mkdirSync(OUT, { recursive: true });
  const cdp = await connect(await findPage(CDP_PORT, { tries: 200, label: 'battle_ko_shots' }));
  await cdp.send('Runtime.enable');
  await cdp.send('Page.enable');
  const ready = await evalPage(cdp, `(async () => {
    for (let i = 0; i < 300; i++) {
      if (window.SIM && window.GS && window.GS.ok && window.Battle && window.Rules && window.THREE) return { ready: true, three: THREE.REVISION };
      await new Promise(r => setTimeout(r, 200));
    }
    return { ready: false };
  })()`, 120000);
  if (!ready.ready) { console.error('world never became ready'); kill(); process.exit(2); }
  console.log(`world ready (three r${ready.three})  arena=${ARENA || 'diorama'}`);

  const png = (uri, file) => { if (uri) writeFileSync(file, Buffer.from(uri.slice(uri.indexOf(',') + 1), 'base64')); };
  const report = { tag: TAG, arena: ARENA || 'diorama', when: new Date().toISOString() };

  // ---------- KO ----------
  if (!ONLY || ONLY === 'ko') {
    process.stdout.write('  ko ... ');
    const r = await evalPage(cdp, koDrive, 300000);
    if (!r.ok) { console.log('FAILED:', r.why); }
    else {
      if (r.sideResolution) {
        const sr = r.sideResolution;
        const cover = sr.party.concat(sr.foes);
        const ok = cover.length === new Set(cover).size;
        console.log(`\n    sides via ${sr.via} · party=[${sr.party}] foes=[${sr.foes}] · partition ${ok ? 'OK' : 'BROKEN'}`);
      }
      if (r.framesGained < 30) console.log(`\n    WARNING: only ${r.framesGained} frames — canvas may be stalled`);
      for (const [k, uri] of Object.entries(r.shots)) png(uri, join(OUT, `${TAG}-ko-${k}.png`));
      const V = r.victim, base = r.before;
      const aliveY = base[V].y, aliveAlpha = base[V].alpha;
      let minY = Infinity, endY = null, endAlpha = null, gone = null, lastAlpha = null;
      for (const s of r.series) {
        const b = s.b[V];
        if (b.y != null) { minY = Math.min(minY, b.y); endY = b.y; }
        // ALPHA ONLY. anchor().vis in battle_world is `!b.dead && ...`, so a body
        // that has just been marked dead reads invisible on the very next tick and
        // "gone at 1 ms" was the instrument describing a flag, not a picture.
        if (b.alpha != null) { endAlpha = b.alpha; if (gone === null && b.alpha <= 0.02) gone = s.t; lastAlpha = b.alpha; }
      }
      // did anybody ELSE move, in screen pixels
      const react = {};
      for (const id of Object.keys(base)) {
        if (id === V) continue;
        let dx = 0, dh = 0, dy = 0, bob = 0;
        for (const s of r.series) {
          const b = s.b[id]; if (!b || b.ax == null) continue;
          dx = Math.max(dx, Math.abs(b.ax - base[id].ax));
          dy = Math.max(dy, Math.abs(b.ay - base[id].ay));
          dh = Math.max(dh, Math.abs(b.ah - base[id].ah));
          if (b.bob != null) bob = Math.max(bob, b.bob);
        }
        // anchor() PROJECTS THE PIVOT and a constant height, so it is blind to every
        // procedural layer in this file by construction — including this one. The
        // rotation is read directly, and the pixels are the verdict.
        react[id] = { dxPx: +dx.toFixed(1), dyPx: +dy.toFixed(1), dhPx: +dh.toFixed(1),
                      bobRad: +bob.toFixed(3), pxDiff: (r.pxDiff || {})[id] ?? null };
      }
      report.ko = {
        victim: V, actor: r.actor, foes: r.foes, allies: r.allies,
        aliveY: +aliveY.toFixed(3), minY: +minY.toFixed(3), endY: +endY.toFixed(3),
        sinkBelowAliveM: +(aliveY - minY).toFixed(3),
        alphaAlive: aliveAlpha, alphaEnd: endAlpha, goneAtMs: gone,
        react, lum: r.lum, frames: r.frames,
      };
      console.log('ok');
      console.log('    victim ' + V + '  alive y ' + report.ko.aliveY + ' -> min ' + report.ko.minY +
                  '  (sink below its own floor: ' + report.ko.sinkBelowAliveM + ' m)');
      console.log('    alpha ' + report.ko.alphaAlive + ' -> ' + report.ko.alphaEnd +
                  '   gone at ' + (gone == null ? 'never (still on screen at 3.0 s)' : gone + ' ms'));
      console.log('    OTHERS REACT (peak px vs their own pre-blow anchor): ' + JSON.stringify(react));
      console.log('    body luminance 60 ms after the blow — idle ' + r.lum.base +
                  ' | survivable hit ' + r.lum.hit + ' | KILLING blow ' + r.lum.kill);
    }
    await evalPage(cdp, TEARDOWN);
    await sleep(500);
  }

  // ---------- VICTORY ----------
  if (!ONLY || ONLY === 'victory') {
    process.stdout.write('  victory ... ');
    const s0 = await evalPage(cdp, victoryStart, 300000);
    if (!s0.ok) console.log('FAILED:', s0.why);
    else {
      const grab = async (name) => {
        const full = await cdp.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
        writeFileSync(join(OUT, `${TAG}-win-${name}.png`), Buffer.from(full.data, 'base64'));
      };
      // THE GEOMETRY IS READ WHILE THE BOX IS ON SCREEN, not afterwards: with
      // autoplay the outro auto-confirms and the whole screen is destroyed inside
      // a second, so a measurement taken after the loop measures nothing.
      const GEOM = `(() => {
        const box = document.querySelector('.ebb-obox'); const st = window.__KO_STAGE;
        const out = { vw: innerWidth, vh: innerHeight };
        if (box) { const r = box.getBoundingClientRect(); out.box = { x0: Math.round(r.left), y0: Math.round(r.top), x1: Math.round(r.right), y1: Math.round(r.bottom) }; }
        const sc = document.querySelector('.ebb-outro');
        if (sc) { const cs = getComputedStyle(sc); out.scrim = { bg: cs.backgroundColor, filter: cs.backdropFilter || cs.webkitBackdropFilter }; }
        if (st) { out.anchors = {}; for (const id of Object.keys(st.tiers())) { try { out.anchors[id] = st.anchor(id); } catch (e) { } } }
        if (out.box && out.anchors) {
          out.covered = Object.keys(out.anchors).filter((id) => { const a = out.anchors[id];
            return a && a.x >= out.box.x0 && a.x <= out.box.x1 && a.y >= out.box.y0 - a.h && a.y <= out.box.y1; });
        }
        return out;
      })()`;
      let lastDown = null, sawOutro = 0, shot = {}, geom = null;
      const t0 = Date.now();
      while (Date.now() - t0 < 90000) {
        const p = await evalPage(cdp, victoryPoll);
        if (lastDown === null && p.foesAlive === 0) { lastDown = Date.now(); await grab('0-down'); }
        if (lastDown && !shot.h700 && Date.now() - lastDown > 700) { shot.h700 = 1; await grab('1-hold700'); }
        if (lastDown && !shot.h1400 && Date.now() - lastDown > 1400) { shot.h1400 = 1; await grab('2-hold1400'); }
        if (p.outro && !sawOutro) { sawOutro = Date.now(); geom = await evalPage(cdp, GEOM); await grab('3-tally'); }
        if (sawOutro && !shot.late && Date.now() - sawOutro > 1200) { shot.late = 1; await grab('4-tally-late'); break; }
        await sleep(100);
      }
      geom = geom || {};
      report.victory = { sawOutro: !!sawOutro, holdMs: (sawOutro && lastDown) ? sawOutro - lastDown : null, geom };
      console.log('ok');
      console.log('    last foe down -> tally box on screen: ' +
                  (report.victory.holdMs == null ? 'n/a' : report.victory.holdMs + ' ms'));
      console.log('    outro box ' + JSON.stringify(geom.box) + '  in a ' + geom.vw + 'x' + geom.vh + ' frame');
      console.log('    scrim ' + JSON.stringify(geom.scrim));
      console.log('    BODIES UNDER THE BOX: ' + JSON.stringify(geom.covered || []));
    }
    await evalPage(cdp, TEARDOWN);
  }

  writeFileSync(join(OUT, `${TAG}-report.json`), JSON.stringify(report, null, 2));
  console.log('\nwrote to ' + OUT);
  cdp.close(); kill(); process.exit(0);
})().catch((e) => { console.error('battle_ko_shots error:', e); kill(); process.exit(2); });
