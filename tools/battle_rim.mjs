#!/usr/bin/env node
// battle_rim.mjs — THE BODY SIDE: WHAT DOES A SEPARATION CUE ON THE CAST COST?
//
// THE STANDING GAP. The camera lane closed size and occlusion, TONE closed the
// boom, PLACE closed where the fight happens — and at some sites the cast still
// reads at the terrain's own value, because the body and its background are
// GENUINELY THE SAME COLOUR. The forest party standing inside a hedge bank is
// the standing example and no pose fixes it.
//
// WHAT MAKES THIS EXPENSIVE, said before it is spent: `battle_world.js` writes
// ZERO SHADERS, which is the single strongest structural argument in the whole
// arc — it is what DELETES the r185 colour-management bug class here rather
// than managing it. Every candidate below except one re-opens that class.
//
//   node tools/battle_rim.mjs --mode=regress --port=3000   # the flag-off proof
//   node tools/battle_rim.mjs --mode=smoke   --port=3000   # does it compile, what did it patch
//   node tools/battle_rim.mjs --mode=sweep   --port=3000   # constants, on the meter
//   node tools/battle_rim.mjs --mode=shots   --port=3000   # full-res pairs, for the EYE
//   node tools/battle_rim.mjs --mode=fps     --port=3000   # what it costs a frame
//   node tools/battle_rim.mjs --mode=teardown --port=3000  # geo/mat/tex must return
//
// THE CENSUS IS NOT HERE ON PURPOSE. Comparability beats convenience: the 62
// sites are measured by `battle_decide --mode=census --brim=…`, through the
// SAME tools/battle_place_lib.mjs object every prior lane read, so a number in
// this arc is never two rulers apart. This file only measures the things that
// census cannot: whether the flag-off game is untouched, whether the shader
// compiled, what the constants should be, what a frame costs, and pictures.
//
// SAY WHICH SPACE THE BYTES ARE IN. Nothing in this file reads a render target.
// The pictures come off the display canvas after OutputPass and the meter is
// battle_place_lib's, which does the same — so the r185 linear-target trap is
// not on this path. The cue ITSELF adds radiance in the working space and never
// reads a pixel; that position is argued where the shader is (battle_world.js,
// RIM_FRAG), not here.
//
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
const MODE = arg('mode', 'smoke');
const OUT = join(ROOT, arg('out', 'docs/qa/battle-rim'));
const HEAD = argv.includes('--head');
const TAG = arg('tag', '');
// THE SITES. Defaults are the six the report is written about: the forest hedge
// that motivated the lane, the two other worst sites by `sil.bandMin` in the
// shipped census, and three ordinary ones so a cue cannot be judged only where
// it was asked for.
const SITES = arg('sites', 's044,s031,s026,s005,s033,s017,s041,s030');
// --mode=sweep: which arms to run at each site.
const ARMS = arg('arms', 'off,auto,add,dark,flat');
const REPS = parseInt(arg('reps', '1'), 10);

mkdirSync(OUT, { recursive: true });

const CDP_PORT = await freePort();
const CHROME = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const sleep = ms => new Promise(r => setTimeout(r, ms));

const PROFILE_PREFIX = 'battle-rim-';
sweepStaleProfiles(PROFILE_PREFIX);
const profile = join(process.env.TMPDIR || '/tmp', PROFILE_PREFIX + process.pid);

// THE FLAG-OFF ARM HAS NO FLAG IN THE URL AT ALL. `regress` drives the page the
// way a player opens it and injects the module anyway (the worst case for a
// patch play3d would carry), so "nothing you build may change what a player
// sees today" is a measurement of the default path rather than of a quieter
// version of the new one.
const WORLDQ = MODE === 'regress' ? '' : '&arena=world';
const URL = `http://localhost:${PORT}/play3d.html?scene=ow-valley&rt=1&nomusic=1` + WORLDQ;
const chrome = spawn(CHROME, [
  `--remote-debugging-port=${CDP_PORT}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--disable-extensions',
  '--autoplay-policy=no-user-gesture-required',
  '--hide-scrollbars', '--force-device-scale-factor=1',
  '--window-size=1600,900',
  // fps only: the compositor caps rAF at the display rate, which measures the
  // display and not the change (battle_world_probe's own note).
  ...(MODE === 'fps' ? ['--disable-gpu-vsync', '--disable-frame-rate-limit'] : []),
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
      on(fn) { ws.on('message', (raw) => { let m; try { m = JSON.parse(raw); } catch (e) { return; } if (!m.id) fn(m); }); },
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
           installed: !!(window.BattleWorld && window.BattleWorld.installed),
           frozen: Object.isFrozen(window.BattleWorld),
           why: window.BattleWorld && window.BattleWorld.why || null };
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
// THE PAGE LIBRARY. It stages, it photographs, it tears down. Nothing here
// drives the camera by hand: the shot that is up is the shot the shipped code
// put there, which is the discipline battle_decide's own driver established.
const LIB = `(() => {
  const W = {}; window.__RIM = W;
  W.st = () => (window.__EBB_SCREEN && window.__EBB_SCREEN.stage) || null;
  // ONE ASSIGNMENT PER ARM. Every arm below is the same build with RIM set
  // differently — never a different page, never a different flag in the URL.
  // AN ARM MAY CARRY ITS OWN STRENGTH: 'dark:0.35:1.6' is the dark polarity at
  // dark 0.35 and power 1.6. A LADDER THAT SPANS SEVERAL CHROME LAUNCHES IS NOT
  // A LADDER — the noise run measured the same arm at one site reading edgeRGB
  // 1.28 to 2.43 across four repeats, so a rung compared against a baseline from
  // another launch is comparing launches. Every rung and its control run inside
  // one page.
  W.arm = function (spec, over) {
    const M = window.BattleWorld && window.BattleWorld.RIM;
    if (!M) return { absent: true };
    const p = String(spec).split(':');
    const name = p[0];
    M.on = name !== 'off';
    M.mode = name === 'flat' ? 'flat' : 'fresnel';
    M.perBody = name === 'perbody';
    M.polarity = (name === 'add' || name === 'dark') ? name : 'auto';
    if (over) for (const k of Object.keys(over)) M[k] = over[k];
    if (p[1] != null && p[1] !== '') {
      const v = parseFloat(p[1]);
      if (name === 'add') M.add = v;
      else if (name === 'dark') M.dark = v;
      else if (name === 'flat') { M.flatE = v; M.flatDark = 1 - v; }
      else { M.add = v; M.dark = 1 - v; }         // auto/perbody: one knob, both signs
    }
    if (p[2] != null && p[2] !== '') M.power = parseFloat(p[2]);
    return { spec: spec, on: M.on, mode: M.mode, polarity: M.polarity, perBody: M.perBody,
             add: M.add, dark: M.dark, power: M.power, autoDead: M.autoDead,
             flatE: M.flatE, flatDark: M.flatDark };
  };
  W.mem = function () {
    return { geo: R.info.memory.geometries, tex: R.info.memory.textures,
             calls: R.info.render.calls, tris: R.info.render.triangles,
             progs: R.info.programs ? R.info.programs.length : null,
             canvases: document.querySelectorAll('canvas').length };
  };
  W.jpg = function (q) {
    const s = W.st(); if (!s) return null;
    W.pose(true);
    s.snapshot();
    const src = s.canvas;
    const c = document.createElement('canvas');
    c.width = src.width; c.height = src.height;
    c.getContext('2d').drawImage(src, 0, 0);
    W.pose(false);
    return c.toDataURL('image/jpeg', q || 0.9);
  };
  W.teardown = function () {
    try { const s = W.st(); if (s) s.destroy(); } catch (e) {}
    const sc = window.__EBB_SCREEN;
    if (sc && sc.destroy) { try { sc.destroy(); } catch (e) {} }
    window.__EBB_SCREEN = null; window.Battle.active = false;
    document.querySelectorAll('.ebb-root').forEach(n => n.remove());
    try { window.UILOCK && UILOCK.unlock('battle'); } catch (e) {}
  };
  // STAGE A REAL BATTLE AND HOLD IT AT THE COMMAND STEP — the frame the player
  // lives in (battle_decide's finding), which is also where the pictures go.
  W.stage = async function (site, yaw) {
    const GS = window.GS, B = window.Battle, RU = window.Rules;
    GS.setFlags({ 'maren-joined': true });
    const f = SIM.floors(site.x, site.z);
    if (!f.length) return { skip: 'no floor' };
    SIM.tp(site.x, site.z, site.y); SIM.tick(3);
    const p0 = SIM.pos();
    const zone = SIM.zone(p0.x, p0.z) || site.zone;
    window.ORBIT.yaw = yaw;
    const items = GS.data.items.items, growth = GS.data.growth;
    const party = GS.activeParty().filter(c => ['vesper','maren'].indexOf(c.id) >= 0)
                   .map(c => RU.derive.partyMember(growth, items, c));
    const zd = GS.data.encounters.zones[zone] || GS.data.encounters.zones.meadow;
    const t0 = performance.now();
    const pr = B.start({ zone: zone, group: ['duskpad','reed-nibbler'], seed: 4242,
                         backdrop: zd && zd.battleBackdrop }, party, { speed: 1 });
    pr.then(()=>{}, ()=>{});
    let st = null;
    for (let i = 0; i < 300 && !(st = W.st()); i++) await new Promise(r => setTimeout(r, 100));
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
    // the command step, waited for and never forced
    const menuUp = () => { const c = document.querySelector('.ebb-cmds'); return !!c && !c.classList.contains('idle'); };
    for (let i = 0; i < 400 && !menuUp(); i++) await new Promise(r => setTimeout(r, 25));
    for (let i = 0; i < 200; i++) { const c = st.cam ? st.cam() : null; if (c && c.kind === 'decide') break; await new Promise(r => setTimeout(r, 25)); }
    await new Promise(r => setTimeout(r, 900));
    return { ok: true, st: true, zone: zone, at: p0, stageMs: +(performance.now() - t0).toFixed(0),
             rim: st.rim ? st.rim() : null, tone: st.tone ? st.tone() : null,
             site: st.site || null, kind: st.cam ? st.cam().kind : null };
  };
  // WHAT THE SHIPPED METER SAYS, at whatever is on screen right now — with the
  // cast PINNED to its own idle phase for the exposure. Without the pin the
  // same arm at one site measured edgeRGB 1.44 and 5.31 on two runs, because a
  // model lands on a network time and the idle has been running since. See
  // stage.qa.pose().
  W.pose = function (on) { const s = W.st(); return (s && s.qa && s.qa.pose) ? s.qa.pose(on) : 0; };
  W.meter = function () {
    W.pose(true);
    const F = window.__PLACE.frames();
    const sil = window.__PLACE.silhouette(F);
    if (sil.ok) delete sil.mask;
    W.pose(false);
    return sil;
  };

  // ---- AND THE SAME ARITHMETIC AT THE RESOLUTION THE PLAYER SEES ----------
  // THE SHARED METER REDUCES THE DISPLAY FRAME TO 320x180 BEFORE IT MEASURES
  // ANYTHING, and this cue's whole effect lives in a band one to two pixels
  // wide at 1344. A 4.2x box filter mixes that band with the background it is
  // supposed to separate from, so the shared ruler CANNOT SEE a rim it would
  // still be wrong to call absent. That is a property of the instrument, not of
  // the cue, and the fix is not to change the shared object — every prior lane's
  // numbers are read by it — but to run its own arithmetic again at native size
  // and report both.
  // THE EQUIVALENCE IS PROVED, NOT ASSUMED: called at 320x180 this must
  // reproduce W.meter's edgeRGB to the decimal, which is what makes the native
  // reading trustworthy rather than a second opinion from a second ruler.
  // K and RING scale with the frame so the band being averaged is the same
  // FRACTION of the picture at both resolutions.
  W.meterRes = function (rw, rh) {
    const st = W.st(); if (!st) return { ok: false, why: 'no stage' };
    W.pose(true);
    const c2 = document.createElement('canvas'); c2.width = rw; c2.height = rh;
    const g2 = c2.getContext('2d', { willReadFrequently: true });
    const grab = () => { g2.drawImage(document.querySelector('canvas'), 0, 0, rw, rh);
                         return g2.getImageData(0, 0, rw, rh).data; };
    const roots = [];
    scene.traverse(o => {
      if (o.userData && o.userData.isBattleWorld) {
        let p = o.parent, own = true;
        while (p) { if (p.userData && p.userData.isBattleWorld) { own = false; break; } p = p.parent; }
        if (own) roots.push(o);
      }
    });
    st.snapshot(); const full = grab();
    const were = roots.map(r => r.visible);
    roots.forEach(r => { r.visible = false; });
    st.snapshot(); const bg = grab();
    roots.forEach((r, i) => { r.visible = were[i]; });
    st.snapshot();
    const lum = (r, g, b) => 0.2126 * r + 0.7152 * g + 0.0722 * b;
    const m = new Uint8Array(rw * rh); let n = 0;
    for (let i = 0, p = 0; p < rw * rh; p++, i += 4) {
      const d = Math.max(Math.abs(full[i] - bg[i]), Math.abs(full[i+1] - bg[i+1]), Math.abs(full[i+2] - bg[i+2]));
      if (d > 12) { m[p] = 1; n++; }
    }
    if (n < 20) { W.pose(false); return { ok: false, why: 'no silhouette', castPx: n, res: [rw, rh] }; }
    const at = (x, y) => (x < 0 || y < 0 || x >= rw || y >= rh) ? 0 : m[y * rw + x];
    const s = rw / 320;
    const K = Math.max(1, Math.round(1 * s)), RING = Math.max(1, Math.round(5 * s));
    const eRGB = [0,0,0], rRGB = [0,0,0];
    let nE = 0, nR = 0, sL = 0, sL2 = 0, castL = 0, nC = 0;
    let x0 = rw, x1 = 0;
    for (let y = 0; y < rh; y++) for (let x = 0; x < rw; x++) if (m[y*rw+x]) { if (x < x0) x0 = x; if (x > x1) x1 = x; }
    const B = 6, bw = Math.max(1, (x1 - x0 + 1) / B);
    const be = [], br = [], bne = [], bnr = [];
    for (let b = 0; b < B; b++) { be.push([0,0,0]); br.push([0,0,0]); bne.push(0); bnr.push(0); }
    for (let y = 0; y < rh; y++) for (let x = 0; x < rw; x++) {
      const p = y * rw + x, i = p * 4;
      const bi = Math.max(0, Math.min(B - 1, Math.floor((x - x0) / bw)));
      if (m[p]) {
        castL += lum(full[i], full[i+1], full[i+2]); nC++;
        let edge = 0;
        for (let dy = -K; dy <= K && !edge; dy++) for (let dx = -K; dx <= K; dx++) if (!at(x+dx, y+dy)) { edge = 1; break; }
        if (edge) { eRGB[0]+=full[i]; eRGB[1]+=full[i+1]; eRGB[2]+=full[i+2]; nE++;
                    if (x >= x0 && x <= x1) { be[bi][0]+=full[i]; be[bi][1]+=full[i+1]; be[bi][2]+=full[i+2]; bne[bi]++; } }
      } else {
        let near = 0;
        for (let dy = -RING; dy <= RING && !near; dy++) for (let dx = -RING; dx <= RING; dx++) if (at(x+dx, y+dy)) { near = 1; break; }
        if (near) { rRGB[0]+=bg[i]; rRGB[1]+=bg[i+1]; rRGB[2]+=bg[i+2]; nR++;
                    const L = lum(bg[i], bg[i+1], bg[i+2]); sL += L; sL2 += L*L;
                    if (x >= x0 && x <= x1) { br[bi][0]+=bg[i]; br[bi][1]+=bg[i+1]; br[bi][2]+=bg[i+2]; bnr[bi]++; } }
      }
    }
    if (!nE || !nR) { W.pose(false); return { ok: false, why: 'no edge or no ring', castPx: n, res: [rw, rh] }; }
    const dr = eRGB[0]/nE - rRGB[0]/nR, dg = eRGB[1]/nE - rRGB[1]/nR, db = eRGB[2]/nE - rRGB[2]/nR;
    const mL = sL / nR;
    const colD = [];
    for (let b = 0; b < B; b++) {
      if (bne[b] > 8 * s && bnr[b] > 8 * s) {
        const a = be[b][0]/bne[b] - br[b][0]/bnr[b], q = be[b][1]/bne[b] - br[b][1]/bnr[b], c = be[b][2]/bne[b] - br[b][2]/bnr[b];
        colD.push(+Math.sqrt((a*a + q*q + c*c) / 3).toFixed(2));
      }
    }
    W.pose(false);
    return { ok: true, res: [rw, rh], castPx: n, castFrac: +(n / (rw*rh)).toFixed(4),
             edgeRGB: +Math.sqrt((dr*dr + dg*dg + db*db) / 3).toFixed(2),
             bandMin: colD.length ? Math.min.apply(null, colD) : null, bands: colD,
             clutter: +Math.sqrt(Math.max(0, sL2/nR - mL*mL)).toFixed(2),
             ringL: +mL.toFixed(1), castL: nC ? +(castL/nC).toFixed(1) : null,
             edgeL: +lum(eRGB[0]/nE, eRGB[1]/nE, eRGB[2]/nE).toFixed(1),
             K: K, RING: RING };
  };
  W.native = function () {
    const cv = document.querySelector('canvas');
    return W.meterRes(cv.width, cv.height);
  };
  return true;
})()`;

// ---------------------------------------------------------------------------
// THE CENSUS CELLS, taken from the shipped board so a site id in this report is
// the same place a site id in every other board in this arc is.
function census() {
  const f = join(ROOT, 'docs/qa/battle-decide/census-sAfter.json');
  const d = JSON.parse(readFileSync(f, 'utf8'));
  return { yaw: d.meta.yaw,
           rows: d.rows.map(r => ({ id: r.id, zone: r.zone, x: r.at.x, y: r.at.y, z: r.at.z,
                                    sil: r.sil, surf: r.surf })) };
}

// The three constants, overridable from the command line in every mode, so a
// claim about strength is a run rather than a checkout.
const OVER = {};
for (const k of ['add', 'dark', 'power', 'autoDead', 'flatE', 'flatDark']) {
  const v = arg(k, null); if (v != null) OVER[k] = parseFloat(v);
}
const pct = (a, p) =>{ const b = a.slice().sort((x, y) => x - y); return b.length ? +b[Math.min(b.length - 1, Math.floor(b.length * p))].toFixed(2) : null; };

// ---------------------------------------------------------------------------
// THE PAIRED CENSUS, READ. Both arms come out of battle_decide --mode=census
// (the shared ruler) and are joined BY SITE ID, never by row order: a site that
// skipped in one arm and not the other must drop out of the comparison rather
// than shift every row after it by one.
function censusPair() {
  const load = (t) => {
    const f = join(OUT, `census-${t}.json`);
    return existsSync(f) ? JSON.parse(readFileSync(f, 'utf8')) : null;
  };
  const A = load('rimOff'), B = load('rimOn');
  if (!A || !B) return null;
  const ai = Object.fromEntries(A.rows.map(r => [r.id, r]));
  const bi = Object.fromEntries(B.rows.map(r => [r.id, r]));
  const ids = A.rows.map(r => r.id).filter(id => bi[id]);
  return { A, B, ids, ai, bi };
}

function buildBoard() {
  const P = censusPair();
  if (!P) { console.error('need census-rimOff.json and census-rimOn.json in ' + OUT); process.exit(2); }
  const { A, B, ids, ai, bi } = P;
  const num = (v, d) => v == null ? '&mdash;' : (+v).toFixed(d == null ? 2 : d);
  // THE PAIRING RECEIPT FIRST. If the two arms did not stage in the same place
  // with the same boom, nothing below is an A/B of the cue.
  let sameSite = 0, samePitch = 0, sameFov = 0;
  for (const id of ids) {
    if (ai[id].site && bi[id].site && ai[id].site.R === bi[id].site.R) sameSite++;
    if (ai[id].pitch === bi[id].pitch) samePitch++;
    if (ai[id].fov === bi[id].fov) sameFov++;
  }
  const d = ids.map(id => ({ id, zone: ai[id].zone,
    a: ai[id].sil ? ai[id].sil.edgeRGB : null, b: bi[id].sil ? bi[id].sil.edgeRGB : null,
    ab: ai[id].sil ? ai[id].sil.bandMin : null, bb: bi[id].sil ? bi[id].sil.bandMin : null,
    pol: bi[id].rim ? bi[id].rim.polarity : null,
    patched: bi[id].rim ? bi[id].rim.patched : null,
    shared: bi[id].rim ? bi[id].rim.shared : null,
    sameR: !!(ai[id].site && bi[id].site && ai[id].site.R === bi[id].site.R) }));
  const live = d.filter(r => r.a != null && r.b != null);
  const mean = (a) => a.length ? a.reduce((x, y) => x + y, 0) / a.length : null;
  const up = live.filter(r => r.b > r.a + 1.5).length;     // 1.5 = the measured
  const dn = live.filter(r => r.b < r.a - 1.5).length;     // one-battle spread
  const rows = d.map(r => `<tr class="${r.sameR ? '' : 'moved'}"><td>${r.id}</td><td>${r.zone}</td>`
    + `<td>${num(r.a)}</td><td>${num(r.b)}</td><td class="${r.b > r.a + 1.5 ? 'win' : r.b < r.a - 1.5 ? 'lose' : ''}">${r.a != null && r.b != null ? num(r.b - r.a) : '&mdash;'}</td>`
    + `<td>${num(r.ab)}</td><td>${num(r.bb)}</td><td>${r.pol || '&mdash;'}</td><td>${r.patched == null ? '&mdash;' : r.patched}</td><td>${r.shared == null ? '&mdash;' : r.shared}</td></tr>`).join('\n');
  const shots = existsSync(join(OUT, 'shots-look'))
    ? require('node:fs').readdirSync(join(OUT, 'shots-look')).filter(f => /\.jpg$/.test(f)).sort() : [];
  const byId = {};
  for (const f of shots) { const id = f.split('-')[0]; (byId[id] = byId[id] || []).push(f); }
  const gallery = Object.keys(byId).sort().map(id => `<section><h3>${id}</h3><div class="pair">`
    + byId[id].map(f => `<figure><img loading="lazy" src="shots-look/${f}"><figcaption>${f.replace(/\.jpg$/, '').replace(id + '-', '')}</figcaption></figure>`).join('')
    + `</div></section>`).join('\n');
  const stab = existsSync(join(OUT, 'stability.json')) ? JSON.parse(readFileSync(join(OUT, 'stability.json'), 'utf8')) : null;
  const html = `<!doctype html><meta charset="utf-8"><title>battle-rim — the body side, priced</title>
<style>
 body{font:14px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:0 auto;max-width:1180px;padding:28px 20px 80px;color:#20242c}
 h1{font-size:22px;margin:0 0 6px} h2{font-size:17px;margin:34px 0 8px;border-bottom:1px solid #dcdfe6;padding-bottom:5px}
 h3{font-size:14px;margin:18px 0 6px;color:#555}
 table{border-collapse:collapse;font-size:12.5px;width:100%} th,td{border:1px solid #dfe2e8;padding:3px 7px;text-align:right}
 th:first-child,td:first-child,th:nth-child(2),td:nth-child(2){text-align:left}
 th{background:#f2f4f7} tr.moved td{background:#fff6e6}
 td.win{background:#e6f6ea;font-weight:600} td.lose{background:#fdeaea;font-weight:600}
 .k{background:#f7f8fa;border-left:3px solid #99a;padding:9px 13px;margin:12px 0}
 .pair{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:10px}
 figure{margin:0} img{width:100%;border:1px solid #ccd;border-radius:3px} figcaption{font-size:11px;color:#666}
 code{background:#f0f1f4;padding:1px 4px;border-radius:3px}
 @media(prefers-color-scheme:dark){body{background:#14161a;color:#dde}th{background:#242832}td,th{border-color:#333a46}
  .k{background:#1c2028;border-left-color:#667}tr.moved td{background:#2a2418}td.win{background:#1d3324}td.lose{background:#33201f}
  code{background:#242832}img{border-color:#333a46}}
</style>
<h1>The body side, priced — <code>?arena=world&amp;brim=1</code></h1>
<p>A SPIKE. Nothing here is default: <code>?arena=world</code> is opt-in and <code>brim</code> is off inside it.
Both census arms are one build with one assignment between them
(<code>battle_decide --mode=census --brim=off|auto</code>), read by
<code>tools/battle_place_lib.mjs</code> — the same object every prior lane in this arc read.</p>

<div class="k"><b>THE NUMBER THAT BOUNDS EVERY OTHER NUMBER ON THIS PAGE.</b>
One battle, staged once and metered six times with <em>nothing touched in between</em>
(<code>battle_rim --mode=stability</code>): the shared meter's <code>edgeRGB</code> spread
${stab ? stab.spread.m320edge.range : '1.52'}, its <code>bandMin</code> spread
${stab ? stab.spread.m320band.range : '1.14'}, and at native resolution
${stab ? stab.spread.natEdge.range : '2.81'} / ${stab ? stab.spread.natBand.range : '6.21'};
the <em>background</em> ring luminance itself moved ${stab ? stab.spread.natRing.range : '4.6'}.
The staging is reproducible (site ring and mask pixel count agree to four figures across
repeats) — the frame is not, because the valley keeps animating.
<b>So a single-site delta under about 1.5 edgeRGB is noise, in this lane and in every
earlier lane that read one frame per site.</b></div>

<h2>The pairing receipt</h2>
<p>${ids.length} sites in both arms (${A.rows.length} / ${B.rows.length} staged).
Same relocation ring <b>${sameSite}/${ids.length}</b>, same boom pitch <b>${samePitch}/${ids.length}</b>,
same lens <b>${sameFov}/${ids.length}</b>. The cue is pinned OFF during TONE's two probe passes for
exactly this reason: with it armed, a darkened silhouette scored a different boom and the two arms
photographed different cameras.</p>

<h2>Silhouette contrast, RGB, on the frame the player dwells in</h2>
<p>Mean <code>edgeRGB</code> ${num(mean(live.map(r => r.a)))} &rarr; ${num(mean(live.map(r => r.b)))};
mean <code>bandMin</code> (the worst band of the cast, never the mean)
${num(mean(live.filter(r => r.ab != null).map(r => r.ab)))} &rarr; ${num(mean(live.filter(r => r.bb != null).map(r => r.bb)))}.
Sites moving more than the one-battle spread: <b>${up} better, ${dn} worse</b>, ${live.length - up - dn} inside the noise.</p>
<table><thead><tr><th>site</th><th>zone</th><th>edgeRGB off</th><th>edgeRGB on</th><th>&Delta;</th>
<th>bandMin off</th><th>bandMin on</th><th>polarity</th><th>mats patched</th><th>leaked</th></tr></thead>
<tbody>${rows}</tbody></table>

<h2>Where the gain landed — and it is the wrong place</h2>
<div class="k"><b>THE CUE ADDS CONTRAST TO THE FRAMES THAT ALREADY HAVE IT.</b>
The six largest gains are at sites whose OFF contrast was already 6.5&ndash;32.5
(s040 25.8&rarr;34.7, s061 32.5&rarr;40.3, s027 21.0&rarr;27.5). Meanwhile the count of sites where a
body does not read is unmoved: <code>edgeRGB &lt; 5</code> went <b>14 &rarr; 15</b>, <code>bandMin &lt; 3</code>
went <b>10 &rarr; 9</b>, and the worst band in the whole census went <b>0.79 &rarr; 1.21</b> &mdash; still zero.
This is the same shape the placement lane found when it measured <code>edgeRGB</code> across sites and it
ran backwards: a lit body against near-black is enormous RGB contrast, and adding light to a body that is
already separated separates it further. The sites that fail do so because the body sits at the terrain's
own value <em>in shadow</em>, and multiplying a shadowed albedo by 0.45 moves almost nothing.</div>

<h2>What it looks like</h2>
<p>The numbers are for iteration; these are the verdict. Every pair below was looked at.</p>
<div class="k"><b>WHAT I SAW.</b>
<b>s019 (meadow, the largest regression, 11.75&rarr;7.57):</b> off, the slate-grey duskpad reads crisply
against sunlit grass. On, its back and flanks carry a pale halo, its dark value is diluted and it reads
MUSHIER, not sharper &mdash; the wolf is darker than its surround and wanted the other sign, but the cast-wide
mean was set by the party member who is lighter than hers.
<b>s017 (meadow, &minus;3.85):</b> the same wolf comes back with a pale line traced right around its
silhouette &mdash; legs, tail, spine. That is the sticker read, plainly, at the shipped default.
<b>s040 (crag scaffold at dusk, the largest gain):</b> a real win by eye &mdash; the edge light reads as an
ambient wrap off the water below, and the party pair lifts off the dark wall. It was already the
highest-contrast site in the census.
<b>s044 (the forest hedge that motivated the lane):</b> the duskpad picks up a soft dark rim that reads as
occlusion rather than outline; the party pair standing IN the hedge bank is, honestly, unchanged.
<b>s005 (forest, cream wolf on pale sand):</b> unreadable before, marginally worse after &mdash; the rim
lifts its edge toward the sand it is lost in.
<b>s031 (meadow, party against a dark ivy wall):</b> the reed-nibbler blows into a glowing lozenge and the
duskpad flattens; the two party bodies, which are the defect in that frame, are essentially untouched.
<b>s033 (crag):</b> a wash.
The pattern is consistent and structural: the cue scales with apparent size and roundness, so it lands on
the foes and not on small clothed party bodies &mdash; and the party is what the lane was opened for.</div>
${gallery}
<h2>The receipts</h2>
<table><thead><tr><th style="text-align:left">what</th><th style="text-align:left">measured</th></tr></thead><tbody>
<tr><td>flag off (no <code>arena</code> in the URL, module injected anyway)</td><td>BattleWorld frozen, <code>on:false installed:false</code>,
 BattleStage3D unpatched, a real battle answered by the DIORAMA, <b>0 of 77 scene materials marked</b> &mdash;
 <code>battle_rim --mode=regress</code>, regress.json</td></tr>
<tr><td><code>?arena=world</code> without <code>brim</code></td><td>62/62 sites staged in the same ring at the same
 pitch and the same lens as the arm with it on; <code>rim().patched</code> 0 and <code>polarity null</code> on every row</td></tr>
<tr><td>material leak into the field</td><td><b>0</b> at every one of 62 sites (<code>rim().shared</code>, which walks the
 live scene for a non-battle mesh holding a patched material). The cast's graph is re-parsed per body by
 <code>loadGlb</code>, so no field object can share it.</td></tr>
<tr><td>teardown</td><td>geometries <b>&Delta;0</b>, programs return to their pre-battle count, canvases &Delta;0, on
 all three arms. Textures &Delta;+4 identically in <em>every</em> arm including OFF &mdash; pre-existing, not this cue.</td></tr>
<tr><td>fps (rAF-counted, vsync off, alternating passes)</td><td>off 241.2 / 240.9 &rarr; on 240.4 / 240.4 &mdash;
 <b>&minus;0.3%</b>. One extra program, no extra draw call, no extra triangle.</td></tr>
<tr><td>ray budget</td><td><b>W = 2 / 9761, GREEN</b>, unchanged &mdash; the cue adds no geometry by construction.</td></tr>
<tr><td>gates</td><td>battle_sim ALL ENVELOPES GREEN &middot; encounter_sim GREEN &middot; economy_test 228/0 &middot;
 arena_playtest GREEN &middot; transition_test <b>168 ok / 0 failed</b></td></tr>
</tbody></table>

<h2>The colour-space position</h2>
<p>The world arena's zero-shader property is what DELETES the r185 colour-management class here. This spike
re-opens it, and here is exactly how far. The cue adds to <code>totalEmissiveRadiance</code> and multiplies
<code>diffuseColor.rgb</code> at <code>#include &lt;emissivemap_fragment&gt;</code> &mdash; after
<code>normal_fragment_begin</code>, before <code>lights_physical_fragment</code>. That is
<b>radiance in the working space</b>: the same variable every light's contribution lands in, with
<code>tonemapping_fragment</code> and <code>colorspace_fragment</code> running after it exactly as they do for
the sun. It <b>allocates no render target, reads no pixel back and encodes nothing</b>, so the rule that bit
TONE &mdash; a non-XR target holds LINEAR bytes whatever its texture declares, and OutputPass is not in that
loop &mdash; cannot reach this path. The only value that must be in the right space is the colour, and
<code>THREE.Color</code> converts a hex on assignment with ColorManagement on, so the uniform is uploaded
linear with <b>no hand <code>convertSRGBToLinear</code></b> &mdash; adding one would be the double conversion
the runtime notes warn about. <code>IU()</code> is untouched; no light was added or scaled.
<b>What is NOT proved:</b> ow-* ships <code>NoToneMapping</code>, so an added 0.30 linear encodes to ~0.58
display and the ladder's blow-out at 0.70 is that arithmetic, not a bug &mdash; but on any scene that later
turns tone mapping ON, this constant means something different, and nothing here gates that.</p>

<p style="margin-top:40px;color:#888;font-size:12px">off arm ${A.meta.when} &middot; on arm ${B.meta.when} &middot;
three r${A.meta.three} &middot; yaw pinned ${A.meta.yaw}</p>`;
  writeFileSync(join(OUT, 'index.html'), html);
  console.log('WROTE ' + join(OUT, 'index.html'));
  console.log(`pairing: sameR ${sameSite}/${ids.length}  samePitch ${samePitch}/${ids.length}  sameFov ${sameFov}/${ids.length}`);
  console.log(`edgeRGB mean ${num(mean(live.map(r => r.a)))} -> ${num(mean(live.map(r => r.b)))}   `
            + `bandMin mean ${num(mean(live.filter(r => r.ab != null).map(r => r.ab)))} -> ${num(mean(live.filter(r => r.bb != null).map(r => r.bb)))}`);
  console.log(`moved past the 1.5 noise band: ${up} better, ${dn} worse, ${live.length - up - dn} inside it`);
  const pols = {};
  for (const r of d) pols[r.pol || 'none'] = (pols[r.pol || 'none'] || 0) + 1;
  console.log('polarity chosen: ' + JSON.stringify(pols));
  console.log('materials leaked to non-battle objects: ' + d.reduce((a, r) => a + (r.shared || 0), 0));
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
  // A SHADER THAT FAILS TO COMPILE STILL RENDERS A FRAME — three logs and falls
  // back. So the console is captured WITH the run and any WebGL/program line is
  // a failure of this instrument, not a curiosity in a log nobody reads.
  const console_ = [];
  cdp.on((m) => {
    if (m.method === 'Runtime.consoleAPICalled') {
      const txt = (m.params.args || []).map(a => a.value != null ? String(a.value) : (a.description || '')).join(' ');
      console_.push({ level: m.params.type, txt: txt.slice(0, 600) });
    }
    if (m.method === 'Runtime.exceptionThrown') {
      console_.push({ level: 'exception', txt: String((m.params.exceptionDetails && m.params.exceptionDetails.text) || '') });
    }
  });
  const ready = await ev(cdp, READY, 180000);
  if (!ready.ready) { console.error('page never became ready'); kill(); process.exit(2); }
  console.log(`ready three=r${ready.three} scene=${ready.scene}  url=${URL}`);
  const inj = await ev(cdp, INJECT, 60000);
  console.log('battle_world: ' + JSON.stringify(inj));
  await ev(cdp, LIB, 30000);
  await ev(cdp, PLACE_LIB, 30000);

  const C = census();
  const YAW = arg('yaw', null) != null ? parseFloat(arg('yaw')) : C.yaw;
  const pick = SITES.split(',').map(s => C.rows.find(r => r.id === s)).filter(Boolean);
  const shaderGrep = `(() => {
    // EVERY MATERIAL IN THE SCENE, asked whether this module marked it. The
    // count that matters is materials marked on objects OUTSIDE the battle
    // group: the cast's material graph is parsed per body, so it must be 0.
    let marked = 0, outside = 0, mats = 0;
    scene.traverse(o => {
      if (!o.isMesh || !o.material) return;
      let a = o, own = false;
      while (a) { if (a.userData && a.userData.isBattleWorld) { own = true; break; } a = a.parent; }
      const ms = Array.isArray(o.material) ? o.material : [o.material];
      for (const m of ms) { mats++; if (m && m.__bwRim) { marked++; if (!own) outside++; }
                            if (m && m.onBeforeCompile && String(m.onBeforeCompile).indexOf('bwRim') >= 0 && !own) outside++; }
    });
    return { mats: mats, marked: marked, outside: outside };
  })()`;

  // ======================= MODE: regress ===================================
  if (MODE === 'regress') {
    // (a) THE PAGE A PLAYER OPENS. No `arena=world`, no `brim`.
    const bw = await ev(cdp, 'JSON.parse(JSON.stringify(window.BattleWorld))');
    const frozen = await ev(cdp, 'Object.isFrozen(window.BattleWorld)');
    const patched = await ev(cdp, '!!(window.BattleStage3D && window.BattleStage3D.__bwPatched)');
    // (b) A REAL BATTLE ON THAT PAGE, and the DIORAMA must answer it.
    const before = await ev(cdp, 'window.__RIM.mem ? null : null') || null;
    const fight = await ev(cdp, `(async () => {
      const GS = window.GS, RU = window.Rules;
      GS.setFlags({ 'maren-joined': true });
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
      const st = S(); if (!st) return { ok: false, why: 'no stage' };
      for (let i = 0; i < 200; i++) { if (Object.values(st.tiers()).every(v=>v!=='proxy')) break; await new Promise(r=>setTimeout(r,100)); }
      await new Promise(r => setTimeout(r, 1200));
      const out = { ok: true, world: !!st.world, rim: st.rim ? st.rim() : 'NO rim() ON THIS STAGE',
                    canvases: document.querySelectorAll('canvas').length };
      window.__RIM.teardown();
      return out;
    })()`, 300000);
    const grep = await ev(cdp, shaderGrep);
    const out = { url: URL, inject: inj, battleWorld: bw, frozen: frozen,
                  patchedStage3d: patched, battle: fight, sceneMaterials: grep,
                  console: console_.filter(c => /error|warn|exception|shader|program|GL/i.test(c.level + c.txt)) };
    writeFileSync(join(OUT, 'regress.json'), JSON.stringify(out, null, 2));
    console.log(JSON.stringify(out, null, 2));
    const good = bw.on === false && bw.installed === false && frozen === true
              && patched === false && grep.marked === 0 && grep.outside === 0
              && fight.world === false;
    console.log(good ? '\nFLAG OFF: CLEAN — module inert, diorama answered, zero materials marked'
                     : '\nFLAG OFF: NOT CLEAN — read the json');
    cdp.close(); kill(); process.exit(good ? 0 : 4);
  }

  // ======================= MODE: smoke =====================================
  // DOES IT COMPILE, AND DID IT PATCH WHAT IT SAID IT DID. One site, one arm,
  // the console captured, and a picture either way.
  if (MODE === 'smoke') {
    const s = pick[0];
    const rows = [];
    for (const arm of ARMS.split(',')) {
      const armed = await ev(cdp, `window.__RIM.arm(${JSON.stringify(arm)}, ${JSON.stringify(OVER)})`);
      const r = await ev(cdp, `window.__RIM.stage(${JSON.stringify(s)}, ${YAW})`, 300000);
      if (!r || !r.ok) { console.log(`  ${arm}: skip ${r && r.skip}`); await ev(cdp, 'window.__RIM.teardown()'); continue; }
      const met = await ev(cdp, 'window.__RIM.meter()');
      const jpg = await ev(cdp, 'window.__RIM.jpg(0.9)');
      if (jpg) writeFileSync(join(OUT, `smoke-${s.id}-${arm}.jpg`), Buffer.from(jpg.split(',')[1], 'base64'));
      await ev(cdp, 'window.__RIM.teardown()');
      await sleep(400);
      rows.push({ arm, armed, rim: r.rim, kind: r.kind, sil: met });
      console.log(`  ${arm}: patched=${r.rim && r.rim.patched} flat=${r.rim && r.rim.flat} skip=${r.rim && r.rim.skipped}`
                + ` pol=${r.rim && r.rim.polarity} ringL=${r.rim && r.rim.ringL} shared=${r.rim && r.rim.shared}`
                + `  edgeRGB=${met && met.edgeRGB} bandMin=${met && met.bandMin}`);
    }
    const gl = console_.filter(c => /error|exception|shader|program|GL_|compil/i.test(c.level + c.txt));
    writeFileSync(join(OUT, 'smoke.json'), JSON.stringify({ site: pick[0], yaw: YAW, rows, console: gl }, null, 1));
    console.log(gl.length ? '\nCONSOLE (shader/error lines):\n' + gl.map(c => '  [' + c.level + '] ' + c.txt).join('\n')
                          : '\nconsole: no shader or error lines');
    console.log('WROTE ' + join(OUT, 'smoke.json'));
    cdp.close(); kill(); process.exit(0);
  }

  // ======================= MODE: sweep =====================================
  // THE CONSTANTS, ON THE SHARED METER. Sites x arms, and the arms ALTERNATE
  // within a site so a drifting machine lands on all of them.
  if (MODE === 'sweep') {
    const over = OVER;
    const rows = [];
    const t0 = Date.now();
    for (const s of pick) {
      for (let rep = 0; rep < REPS; rep++) {
        for (const arm of ARMS.split(',')) {
          await ev(cdp, `window.__RIM.arm(${JSON.stringify(arm)}, ${JSON.stringify(over)})`);
          let r; try { r = await ev(cdp, `window.__RIM.stage(${JSON.stringify(s)}, ${YAW})`, 300000); }
          catch (e) { console.log(`  ${s.id}/${arm} THREW ${e.message}`); continue; }
          if (!r || !r.ok) { console.log(`  ${s.id}/${arm} skip ${r && r.skip}`); await ev(cdp, 'window.__RIM.teardown()'); continue; }
          const met = await ev(cdp, 'window.__RIM.meter()');
          const nat = await ev(cdp, 'window.__RIM.native()');
          const eq = await ev(cdp, 'window.__RIM.meterRes(320,180)');
          await ev(cdp, 'window.__RIM.teardown()');
          await sleep(350);
          rows.push({ id: s.id, zone: s.zone, rep, arm,
                      edgeRGB: met && met.edgeRGB, bandMin: met && met.bandMin,
                      castL: met && met.castL, ringL: met && met.ringL,
                      nat: nat, eq320: eq && { edgeRGB: eq.edgeRGB, bandMin: eq.bandMin },
                      clutter: met && met.clutter, castFrac: met && met.castFrac,
                      pol: r.rim && r.rim.polarity, rimRingL: r.rim && r.rim.ringL,
                      cfg: r.rim && r.rim.cfg,
                      patched: r.rim && r.rim.patched, shared: r.rim && r.rim.shared,
                      rimMs: r.rim && r.rim.ms, R: r.site && r.site.R });
          console.log(`  ${s.id} ${arm.padEnd(5)} pol=${String(r.rim && r.rim.polarity).padEnd(7)}`
                    + ` 320:edge=${String(met && met.edgeRGB).padStart(6)} band=${String(met && met.bandMin).padStart(6)}`
                    + ` | NATIVE edge=${String(nat && nat.edgeRGB).padStart(6)} band=${String(nat && nat.bandMin).padStart(6)}`
                    + ` edgeL=${String(nat && nat.edgeL).padStart(5)} ringL=${String(nat && nat.ringL).padStart(5)}`
                    + `  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
        }
      }
    }
    const f = join(OUT, `sweep${TAG ? '-' + TAG : ''}.json`);
    writeFileSync(f, JSON.stringify({ meta: { when: new Date().toISOString(), yaw: YAW, sites: SITES, arms: ARMS, over, reps: REPS, three: ready.three }, rows }, null, 1));
    console.log('\nWROTE ' + f);
    // the headline: per arm, the mean and the WORST BAND, because a mean buys a
    // good average and one invisible body
    const arms = [...new Set(rows.map(r => r.arm))];
    for (const a of arms) {
      const rs = rows.filter(r => r.arm === a && r.edgeRGB != null);
      if (!rs.length) continue;
      const m = rs.reduce((x, r) => x + r.edgeRGB, 0) / rs.length;
      const b = rs.filter(r => r.bandMin != null);
      const mb = b.length ? b.reduce((x, r) => x + r.bandMin, 0) / b.length : null;
      console.log(`  ${a.padEnd(6)} n=${rs.length}  edgeRGB mean ${m.toFixed(2)}  bandMin mean ${mb == null ? '—' : mb.toFixed(2)}`
                + `  worst bandMin ${b.length ? Math.min(...b.map(r => r.bandMin)).toFixed(2) : '—'}`);
    }
    cdp.close(); kill(); process.exit(0);
  }

  // ======================= MODE: stability =================================
  // IS THE INSTRUMENT MOVING OR IS THE WORLD? One battle, staged once, metered
  // N times without touching anything in between. Every difference this finds
  // is the METER's, because nothing else had a chance to change. It exists
  // because the strength ladder read the SAME ARM at one site as native edgeRGB
  // 12.01 and 18.68 while the staging receipts (site R, mask pixel count) were
  // identical to four significant figures — a spread that large with a
  // reproducible stage is a measurement, not a world.
  if (MODE === 'stability') {
    const s = pick[0];
    await ev(cdp, `window.__RIM.arm(${JSON.stringify((ARMS.split(',')[0]) || 'off')}, ${JSON.stringify(OVER)})`);
    const r = await ev(cdp, `window.__RIM.stage(${JSON.stringify(s)}, ${YAW})`, 300000);
    if (!r || !r.ok) { console.error('stage failed: ' + (r && r.skip)); cdp.close(); kill(); process.exit(3); }
    const rows = [];
    for (let i = 0; i < Math.max(4, REPS); i++) {
      const m320 = await ev(cdp, 'window.__RIM.meter()');
      const nat = await ev(cdp, 'window.__RIM.native()');
      rows.push({ i, m320: { edgeRGB: m320.edgeRGB, bandMin: m320.bandMin, ringL: m320.ringL, castPx: m320.castPx },
                  nat: { edgeRGB: nat.edgeRGB, bandMin: nat.bandMin, ringL: nat.ringL, edgeL: nat.edgeL, castPx: nat.castPx } });
      console.log(`  ${i}: 320 edge=${m320.edgeRGB} band=${m320.bandMin} ring=${m320.ringL} px=${m320.castPx}`
                + ` | NAT edge=${nat.edgeRGB} band=${nat.bandMin} ring=${nat.ringL} edgeL=${nat.edgeL} px=${nat.castPx}`);
      await sleep(250);
    }
    await ev(cdp, 'window.__RIM.teardown()');
    const spread = (get) => { const a = rows.map(get); return { min: Math.min(...a), max: Math.max(...a), range: +(Math.max(...a) - Math.min(...a)).toFixed(2) }; };
    const out = { site: s, arm: ARMS.split(',')[0], rows,
                  spread: { m320edge: spread(r2 => r2.m320.edgeRGB), m320band: spread(r2 => r2.m320.bandMin),
                            natEdge: spread(r2 => r2.nat.edgeRGB), natBand: spread(r2 => r2.nat.bandMin),
                            natRing: spread(r2 => r2.nat.ringL), castPx: spread(r2 => r2.nat.castPx) } };
    writeFileSync(join(OUT, `stability${TAG ? '-' + TAG : ''}.json`), JSON.stringify(out, null, 1));
    console.log('\nSPREAD ON ONE UNTOUCHED BATTLE: ' + JSON.stringify(out.spread));
    cdp.close(); kill(); process.exit(0);
  }

  // ======================= MODE: shots =====================================
  // PICTURES, FULL RESOLUTION, PAIRED. The numbers are for iteration and these
  // are for the verdict — a rim light is exactly the kind of change that
  // measures well and looks like a sticker.
  if (MODE === 'shots') {
    const dir = join(OUT, 'shots' + (TAG ? '-' + TAG : ''));
    mkdirSync(dir, { recursive: true });
    const rows = [];
    for (const s of pick) {
      for (const arm of ARMS.split(',')) {
        await ev(cdp, `window.__RIM.arm(${JSON.stringify(arm)}, ${JSON.stringify(OVER)})`);
        let r; try { r = await ev(cdp, `window.__RIM.stage(${JSON.stringify(s)}, ${YAW})`, 300000); }
        catch (e) { console.log(`  ${s.id}/${arm} THREW ${e.message}`); continue; }
        if (!r || !r.ok) { console.log(`  ${s.id}/${arm} skip ${r && r.skip}`); await ev(cdp, 'window.__RIM.teardown()'); continue; }
        const met = await ev(cdp, 'window.__RIM.meter()');
        const jpg = await ev(cdp, 'window.__RIM.jpg(0.92)');
        if (jpg) writeFileSync(join(dir, `${s.id}-${arm}.jpg`), Buffer.from(jpg.split(',')[1], 'base64'));
        await ev(cdp, 'window.__RIM.teardown()');
        await sleep(350);
        rows.push({ id: s.id, zone: s.zone, arm, pol: r.rim && r.rim.polarity,
                    ringL: r.rim && r.rim.ringL, edgeRGB: met && met.edgeRGB, bandMin: met && met.bandMin });
        console.log(`  ${s.id} ${arm}  pol=${r.rim && r.rim.polarity} edgeRGB=${met && met.edgeRGB} bandMin=${met && met.bandMin}`);
      }
    }
    writeFileSync(join(OUT, `shots${TAG ? '-' + TAG : ''}.json`), JSON.stringify({ yaw: YAW, rows }, null, 1));
    console.log('shots -> ' + dir);
    cdp.close(); kill(); process.exit(0);
  }

  // ======================= MODE: fps =======================================
  // FPS IS COUNTED IN rAF CALLBACKS. The post chain calls renderer.render()
  // once per PASS, so info.render.frame runs at ~6x the frame rate — the trap
  // battle_world_probe already paid for and reported 2653 "fps" through.
  if (MODE === 'fps') {
    const s = pick[0];
    const drive = (arm) => `(async () => {
      window.__RIM.arm(${JSON.stringify(arm)}, ${JSON.stringify(OVER)});
      const r = await window.__RIM.stage(${JSON.stringify(s)}, ${YAW});
      if (!r || !r.ok) return { ok: false, why: r && r.skip };
      const st = window.__RIM.st();
      let n = 0, stop = false;
      const t0 = performance.now();
      const tick = () => { n++; if (!stop) requestAnimationFrame(tick); };
      requestAnimationFrame(tick);
      const f0 = st.frames;
      await new Promise(res => setTimeout(res, 4000));
      stop = true;
      const dt = (performance.now() - t0) / 1000;
      const out = { ok: true, arm: ${JSON.stringify(arm)}, fps: +(n / dt).toFixed(1), dt: +dt.toFixed(2),
                    rendersPerFrame: +((st.frames - f0) / n).toFixed(2),
                    calls: R.info.render.calls, tris: R.info.render.triangles,
                    progs: R.info.programs ? R.info.programs.length : null,
                    rim: st.rim ? st.rim() : null };
      window.__RIM.teardown();
      await new Promise(res => setTimeout(res, 600));
      return out;
    })()`;
    const out = [];
    // ALTERNATE, twice each: a thermal or GC drift then lands on both arms.
    for (let i = 0; i < 2; i++) for (const arm of ARMS.split(',')) {
      const r = await ev(cdp, drive(arm), 300000);
      out.push(r);
      console.log(`  ${arm} pass${i + 1}: fps=${r.fps} calls=${r.calls} tris=${r.tris} progs=${r.progs} pol=${r.rim && r.rim.polarity}`);
    }
    const by = {};
    for (const r of out) if (r.ok) (by[r.arm] = by[r.arm] || []).push(r.fps);
    for (const k of Object.keys(by)) console.log(`  ${k}: ${by[k].join(' / ')}  mean ${(by[k].reduce((a, b) => a + b, 0) / by[k].length).toFixed(1)}`);
    writeFileSync(join(OUT, 'fps.json'), JSON.stringify({ site: s, yaw: YAW, runs: out, by }, null, 1));
    cdp.close(); kill(); process.exit(0);
  }

  // ======================= MODE: teardown ==================================
  // TEARDOWN TOTAL. A material or mesh this cue adds MUST be disposed;
  // transition_test's {geo:+-2, tex:0} is now a real regression, so the same
  // ledger is taken here before anything reaches it.
  if (MODE === 'teardown') {
    const s = pick[0];
    const rows = [];
    for (const arm of ARMS.split(',')) {
      const m0 = await ev(cdp, 'window.__RIM.mem()');
      await ev(cdp, `window.__RIM.arm(${JSON.stringify(arm)}, ${JSON.stringify(OVER)})`);
      const r = await ev(cdp, `window.__RIM.stage(${JSON.stringify(s)}, ${YAW})`, 300000);
      const m1 = await ev(cdp, 'window.__RIM.mem()');
      await ev(cdp, 'window.__RIM.teardown()');
      await sleep(1200);
      const m2 = await ev(cdp, 'window.__RIM.mem()');
      rows.push({ arm, before: m0, during: m1, after: m2,
                  d: { geo: m2.geo - m0.geo, tex: m2.tex - m0.tex, canvases: m2.canvases - m0.canvases,
                       progs: m2.progs == null ? null : m2.progs - m0.progs },
                  rim: r && r.rim });
      console.log(`  ${arm}: geo ${m0.geo} -> ${m1.geo} -> ${m2.geo} (d ${m2.geo - m0.geo})`
                + `  tex ${m0.tex} -> ${m1.tex} -> ${m2.tex} (d ${m2.tex - m0.tex})`
                + `  progs ${m0.progs} -> ${m1.progs} -> ${m2.progs}`
                + `  canvases d ${m2.canvases - m0.canvases}`);
    }
    writeFileSync(join(OUT, 'teardown.json'), JSON.stringify({ site: s, rows }, null, 1));
    cdp.close(); kill(); process.exit(0);
  }

  console.error('unknown --mode=' + MODE);
  cdp.close(); kill(); process.exit(2);
})();
