#!/usr/bin/env node
// battle_camera.mjs — THE INSTRUMENT FOR THE SHOT LANGUAGE (BET B, world arena).
//
//   node tools/battle_camera.mjs --port=3000 --mode=sides       # stage.sides() partitions, both arenas
//   node tools/battle_camera.mjs --port=3000 --mode=shots       # the contact sheet, both arenas
//   node tools/battle_camera.mjs --port=3000 --mode=legibility  # the numbers, 4 sites, cam off vs on
//   node tools/battle_camera.mjs --port=3000 --mode=moves       # the KO push and the victory move
//   node tools/battle_camera.mjs --port=3000 --mode=assert      # the 180-degree rule, every shot
//   node tools/battle_camera.mjs --port=3000 --mode=fps         # the frame budget, after
//   node tools/battle_camera.mjs --port=3000 --mode=regress     # flag OFF = today's game
//
// WHY IT MEASURES LEGIBILITY THE WAY IT DOES. The BET A spike's honest verdict
// was that the world wins on picture and LOSES on legibility — "two clean
// silhouettes on a low-contrast painted field is a composition; the valley is
// rock, foliage, houses and cast shadows". That is an assertion about PIXELS, so
// it is measured in pixels, and the extraction is a subtraction rather than a
// guess: render the frame with a body, render it without, and the difference IS
// that body's silhouette — shadow, rim light, alpha and all. Render it again
// with the cast's depth test off and the difference is the silhouette it WOULD
// have had unoccluded, so occlusion is one division and never an opinion.
//
// Everything is read out of the running game through the stage's own `qa`
// accessors. Chrome goes through tools/cdp.mjs and is reaped by --user-data-dir
// prefix; this tool never pattern-kills Chrome by name.
import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync } from 'node:fs';
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
const MODE = arg('mode', 'shots');
const OUT = join(ROOT, arg('out', 'docs/qa/battle-camera'));
const HEAD = argv.includes('--head');
const CDP_PORT = await freePort();
const CHROME = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const sleep = ms => new Promise(r => setTimeout(r, ms));

const PROFILE_PREFIX = 'battle-camera-';
sweepStaleProfiles(PROFILE_PREFIX);
const profile = join(process.env.TMPDIR || '/tmp', PROFILE_PREFIX + process.pid);

const flag = MODE === 'regress' ? '' : '&arena=world';
const URL = `http://localhost:${PORT}/play3d.html?scene=ow-valley&rt=1&nomusic=1${flag}`;

const chrome = spawn(CHROME, [
  `--remote-debugging-port=${CDP_PORT}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--disable-extensions',
  '--autoplay-policy=no-user-gesture-required',
  '--hide-scrollbars', '--force-device-scale-factor=1',
  ...(MODE === 'fps' ? ['--disable-gpu-vsync', '--disable-frame-rate-limit'] : []),
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
    const ws = new WebSocket(url, { perMessageDeflate: false, maxPayload: 512 * 1024 * 1024 });
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
const png = (name, uri) => { if (uri) writeFileSync(join(OUT, name), Buffer.from(uri.slice(uri.indexOf(',') + 1), 'base64')); };

// SAY WHICH PATH ANSWERED, AND PROVE IT PARTITIONS. A side map that silently
// came from an id pattern is the defect this convention exists to make visible,
// so every run prints the path — and asserts the map covers every body on the
// stage exactly once, with no id on both sides and none missing.
function sideReport(tag, r) {
  const ids = Object.keys(r.tiers || {});
  const sides = r.sides || {};
  const party = ids.filter(i => sides[i] === 'party'), foes = ids.filter(i => sides[i] === 'foe');
  const missing = ids.filter(i => sides[i] !== 'party' && sides[i] !== 'foe');
  const overlap = party.filter(i => foes.indexOf(i) >= 0);
  const extra = Object.keys(sides).filter(i => ids.indexOf(i) < 0);
  const ok = !missing.length && !overlap.length && !extra.length && ids.length > 0;
  console.log(`  sides[${tag}] via ${r.sidesVia || 'stage.sides()'} · party=[${party}] foes=[${foes}]`
            + ` · partition ${ok ? 'OK' : 'BROKEN'}`
            + (ok ? '' : ` missing=[${missing}] overlap=[${overlap}] extra=[${extra}]`));
  if (!ok) throw new Error('side map does not partition the body set: ' + JSON.stringify({ ids, sides }));
  return { party, foes, via: r.sidesVia || 'stage.sides()' };
}

const READY = `(async () => {
  for (let i = 0; i < 400; i++) {
    if (window.SIM && window.GS && window.GS.ok && window.Battle && window.Rules && window.THREE
        && window.ORBIT && window.SIM.pos && SIM.floors(SIM.pos().x, SIM.pos().z).length) {
      return { ready: true, three: THREE.REVISION, scene: SIM.bounds().scene,
               bw: window.BattleWorld ? { on: window.BattleWorld.on, installed: window.BattleWorld.installed } : null,
               fov: (typeof cam !== 'undefined' && cam) ? cam.fov : null };
    }
    await new Promise(r => setTimeout(r, 200));
  }
  return { ready: false };
})()`;

// ---------------------------------------------------------------------------
// THE SHARED PRELUDE, injected once: start a battle at a spot, wait for models.
// ---------------------------------------------------------------------------
const PRELUDE = `
window.__BC = window.__BC || {};
window.__BC.startAt = async function (x, z, group, opts) {
  opts = opts || {};
  const GS = window.GS, B = window.Battle, RU = window.Rules;
  GS.setFlags({ 'maren-joined': true });
  const f = SIM.floors(x, z);
  SIM.tp(x, z, f.length ? f[0] : null);
  SIM.tick(3);
  if (window.BattleWorld && !Object.isFrozen(window.BattleWorld)) {
    window.BattleWorld.CAM.on = opts.cam !== false;
    window.BattleWorld.enabled = opts.world !== false;   // false => the DIORAMA answers
  }
  const items = GS.data.items.items, growth = GS.data.growth;
  const party = GS.activeParty().filter(c => ['vesper','maren'].indexOf(c.id) >= 0)
                 .map(c => RU.derive.partyMember(growth, items, c));
  const zone = SIM.zone() || 'meadow';
  const zd = GS.data.encounters.zones[zone] || GS.data.encounters.zones.meadow;
  const p = B.start({ zone: zone, group: group, seed: 4242, backdrop: zd && zd.battleBackdrop },
                    party, { speed: opts.speed == null ? 1 : opts.speed });
  p.then(()=>{},()=>{});
  const S = () => (window.__EBB_SCREEN && window.__EBB_SCREEN.stage) || null;
  for (let i = 0; i < 250 && !S(); i++) await new Promise(r => setTimeout(r, 100));
  const st = S();
  if (!st) return { ok: false, why: 'no stage', plan: window.__BW_LAST_PLAN || null };
  const f0 = st.frames;
  for (let i = 0; i < 260; i++) {
    if (Object.values(st.tiers()).every(v => v !== 'proxy') && st.frames > f0 + 100) break;
    await new Promise(r => setTimeout(r, 100));
  }
  await new Promise(r => setTimeout(r, opts.settle == null ? 1500 : opts.settle));
  // AN ID IS NOT A SIDE. BOTH arenas now carry sides() — the per-body value
  // newBody() was constructed with (battle_world.js :1427, battle_stage3d.js
  // :3259) — so this asks the stage and REPORTS WHICH PATH ANSWERED. The id
  // pattern is a labelled last resort: /^m/ matches **maren**, and even
  // /^m\\d+$/ is a guess about battle_rules' private id scheme that was safe
  // in the diorama column only by accident of build order.
  let sidesVia = 'stage.sides()';
  let sides = st.sides ? st.sides() : null;
  if (!sides) {
    sidesVia = 'stage.at().side';
    sides = Object.keys(st.tiers()).reduce((o, k) => { const a = st.at && st.at(k); if (a && a.side) o[k] = a.side; return o; }, {});
    if (!Object.keys(sides).length) {
      sidesVia = 'id-pattern-fallback';
      sides = Object.keys(st.tiers()).reduce((o, k) => (o[k] = /^m\\d+$/.test(k) ? 'foe' : 'party', o), {});
    }
  }
  return { ok: true, zone: zone, world: !!st.world, tiers: st.tiers(), sides: sides, sidesVia: sidesVia,
           cam: st.cam ? st.cam() : null, plan: st.plan || null };
};
window.__BC.end = async function () {
  const s = window.__EBB_SCREEN;
  if (s && s.stage) { try { s.stage.destroy(); } catch (e) {} }
  if (s && s.destroy) { try { s.destroy(); } catch (e) {} }
  window.__EBB_SCREEN = null; window.Battle.active = false;
  document.querySelectorAll('.ebb-root').forEach(n => n.remove());
  try { window.UILOCK && UILOCK.unlock('battle'); } catch (e) {}
  await new Promise(r => setTimeout(r, 400));
  return true;
};
window.__BC.stage = () => (window.__EBB_SCREEN && window.__EBB_SCREEN.stage) || null;
window.__BC.shot = () => window.__BC.stage().snapshot();

// ============================ THE LEGIBILITY METER =========================
// A silhouette is a SUBTRACTION, not a heuristic: frame-with-body minus
// frame-without-body. Everything else follows from that one mask.
window.__BC.legibility = function () {
  const st = window.__BC.stage(); if (!st || !st.qa) return null;
  const cv = st.canvas, W = cv.width, H = cv.height;
  const c2 = window.__BC._c2 || (window.__BC._c2 = document.createElement('canvas'));
  c2.width = W; c2.height = H;
  const g = c2.getContext('2d', { willReadFrequently: true });
  const grab = (x, y, w, h) => { g.drawImage(cv, 0, 0); return g.getImageData(x, y, w, h); };
  const L = (d, i) => 0.2126 * d[i] + 0.7152 * d[i + 1] + 0.0722 * d[i + 2];
  const ids = st.qa.ids();
  const boxes = {};
  for (const id of ids) boxes[id] = st.qa.box(id);
  // the region each body could occupy, in device pixels, with a margin for the ring
  const dpr = W / cv.getBoundingClientRect().width;
  const regionOf = (id) => {
    const b = boxes[id]; if (!b) return null;
    const M = 26;
    const x0 = Math.max(0, Math.floor((b.x0 - M) * dpr)), y0 = Math.max(0, Math.floor((b.y0 - M) * dpr));
    const x1 = Math.min(W, Math.ceil((b.x1 + M) * dpr)), y1 = Math.min(H, Math.ceil((b.y1 + M) * dpr));
    if (x1 <= x0 + 2 || y1 <= y0 + 2) return null;
    return { x: x0, y: y0, w: x1 - x0, h: y1 - y0 };
  };
  // ---- pass 1: the world with no cast in it (the background every body sits on)
  st.qa.showAll(false); st.draw();
  const bgFull = grab(0, 0, W, H);
  const bgOf = (r) => {
    const out = new Uint8ClampedArray(r.w * r.h * 4);
    for (let y = 0; y < r.h; y++) {
      const src = ((y + r.y) * W + r.x) * 4;
      out.set(bgFull.data.subarray(src, src + r.w * 4), y * r.w * 4);
    }
    return out;
  };
  const maskOf = (id, r) => {
    st.qa.show(id, true); st.draw();
    const im = grab(r.x, r.y, r.w, r.h).data;
    st.qa.show(id, false);
    const bg = bgOf(r);
    const m = new Uint8Array(r.w * r.h);
    let n = 0;
    for (let i = 0, p = 0; p < m.length; p++, i += 4) {
      const d = Math.max(Math.abs(im[i] - bg[i]), Math.abs(im[i + 1] - bg[i + 1]), Math.abs(im[i + 2] - bg[i + 2]));
      if (d > 12) { m[p] = 1; n++; }
    }
    return { m, n, im, bg };
  };
  const out = [];
  for (const id of ids) {
    const r = regionOf(id); if (!r) continue;
    const A = maskOf(id, r);
    if (!A.n) { out.push({ id: id, side: boxes[id].side, silPx: 0, why: 'no silhouette' }); continue; }
    // ---- the mask's own bbox, its edge band, and the background ring ---------
    let x0 = 1e9, y0 = 1e9, x1 = -1, y1 = -1;
    for (let p = 0; p < A.m.length; p++) if (A.m[p]) {
      const px = p % r.w, py = (p / r.w) | 0;
      if (px < x0) x0 = px; if (px > x1) x1 = px;
      if (py < y0) y0 = py; if (py > y1) y1 = py;
    }
    // dilate by K to get the ring OUTSIDE the body, and erode to get the edge band INSIDE it
    const K = 4, RING = 10;
    const dil = new Uint8Array(A.m.length), ero = new Uint8Array(A.m.length);
    const at = (x, y) => (x < 0 || y < 0 || x >= r.w || y >= r.h) ? 0 : A.m[y * r.w + x];
    for (let y = 0; y < r.h; y++) for (let x = 0; x < r.w; x++) {
      const p = y * r.w + x;
      let any = 0, all = 1;
      for (let dy = -K; dy <= K && (!any || all); dy++) for (let dx = -K; dx <= K; dx++) {
        const v = at(x + dx, y + dy);
        if (v) any = 1; else all = 0;
      }
      dil[p] = any; ero[p] = all;
    }
    let sumB = 0, nB = 0, sumBg = 0, sumEdge = 0, nEdge = 0, sumRing = 0, nRing = 0, sumRing2 = 0;
    const eRGB = [0, 0, 0], rRGB = [0, 0, 0];
    for (let p = 0, i = 0; p < A.m.length; p++, i += 4) {
      const lb = L(A.im, i), lg = L(A.bg, i);
      if (A.m[p]) {
        sumB += lb; sumBg += lg; nB++;
        if (!ero[p]) { sumEdge += lb; nEdge++; eRGB[0] += A.im[i]; eRGB[1] += A.im[i + 1]; eRGB[2] += A.im[i + 2]; }
      }
      else if (dil[p]) {
        // the ring is read off the BACKGROUND frame, so a body's own rim light
        // never inflates the contrast it is being scored against
        const px = p % r.w, py = (p / r.w) | 0;
        let near = 0;
        for (let dy = -RING; dy <= RING && !near; dy += 2) for (let dx = -RING; dx <= RING; dx += 2) if (at(px + dx, py + dy)) { near = 1; break; }
        if (near) { sumRing += lg; sumRing2 += lg * lg; nRing++; rRGB[0] += A.bg[i]; rRGB[1] += A.bg[i + 1]; rRGB[2] += A.bg[i + 2]; }
      }
    }
    // ---- pass 2: the same body with depth testing off = its FREE silhouette --
    st.qa.xray(true);
    const B2 = maskOf(id, r);
    st.qa.xray(false);
    // OCCLUSION IS AN INTERSECTION, NOT A RATIO OF AREAS. Both masks carry a
    // halo the body did not draw — GTAO darkens the ground around a body that
    // writes depth, bloom bleeds outward from a bright one — and the two passes
    // do not carry the SAME halo, which is how a fully visible Maren measured
    // "-136% occluded". Asking how much of the FREE silhouette survived in the
    // real frame is immune to both.
    let inter = 0;
    for (let p = 0; p < A.m.length; p++) if (A.m[p] && B2.m[p]) inter++;
    const mB = nB ? sumB / nB : 0, mBgUnder = nB ? sumBg / nB : 0;
    const mEdge = nEdge ? sumEdge / nEdge : mB;
    const mRing = nRing ? sumRing / nRing : 0;
    const vRing = nRing ? Math.max(0, sumRing2 / nRing - mRing * mRing) : 0;
    // AND THE EDGE CONTRAST IS RGB DISTANCE, NOT LUMINANCE. This repo has paid
    // for the luminance-only version once already (cutin_edge's halo term: a rim
    // of the wrong HUE at the right brightness was invisible to it on 79 of 112
    // shipped plates). A teal eel on tan rock is 6 units apart in luminance and
    // 39 apart in RGB, and it reads.
    const dr = nEdge && nRing ? eRGB[0] / nEdge - rRGB[0] / nRing : 0;
    const dg = nEdge && nRing ? eRGB[1] / nEdge - rRGB[1] / nRing : 0;
    const db = nEdge && nRing ? eRGB[2] / nEdge - rRGB[2] / nRing : 0;
    out.push({
      id: id, side: boxes[id].side, tier: boxes[id].tier,
      silPx: A.n, freePx: B2.n, interPx: inter,
      occl: B2.n ? +(1 - inter / B2.n).toFixed(4) : null,
      edgeRGB: +Math.sqrt((dr * dr + dg * dg + db * db) / 3).toFixed(2),
      hPx: +((y1 - y0 + 1) / dpr).toFixed(1),
      hPct: +(((y1 - y0 + 1) / H) * 100).toFixed(2),
      // SILHOUETTE CONTRAST: how far the body's own edge band sits from the
      // background immediately around it. This is the number the spike's verdict
      // is about — a body that reads has a big one.
      edge: +Math.abs(mEdge - mRing).toFixed(2),
      // and the same thing measured over the WHOLE body against exactly what it
      // covers, which is blind to a busy background but immune to mask slop
      dL: +Math.abs(mB - mBgUnder).toFixed(2),
      // HOW BUSY THE BACKGROUND IS. A high-contrast body on a noisy field still
      // does not read; this is the noise.
      clutter: +Math.sqrt(vRing).toFixed(2),
      ringN: nRing, bodyL: +mB.toFixed(1), ringL: +mRing.toFixed(1),
    });
  }
  st.qa.showAll(true); st.draw();
  return { bodies: out, canvas: [W, H], cam: st.cam ? st.cam() : null };
};
true;
`;

// ---------------------------------------------------------------------------
const SITES = [
  { name: 'meadow', at: [38.12, -26.88], group: ['duskpad', 'duskpad'] },
  { name: 'forest', at: [15.6, -16.9], group: ['bramble-shade', 'duskpad'] },
  { name: 'water', at: [-45.8, 26.7], group: ['weir-eel', 'brook-sprite'] },
  { name: 'crag', at: [65.6, -40.6], group: ['scree-shell', 'duskpad'] },
];

(async function main() {
  mkdirSync(OUT, { recursive: true });
  const cdp = await connect(await findPage(CDP_PORT, { tries: 250, label: 'battle_camera' }));
  await cdp.send('Runtime.enable');
  await cdp.send('Page.enable');
  const consoleErrs = [];
  cdp.send('Log.enable').catch(() => { });
  const ready = await ev(cdp, READY, 120000);
  if (!ready.ready) { console.error('world never became ready'); kill(); process.exit(2); }
  console.log(`world ready  three r${ready.three}  scene=${ready.scene}  bw=${JSON.stringify(ready.bw)}  fov=${ready.fov}`);
  await ev(cdp, PRELUDE, 60000);

  // ------------------------------------------------------------------ shots
  // THE CONTACT SHEET. THREE COLUMNS, ONE BUILD, THE SAME BEATS, DRIVEN BY THE
  // STAGE'S OWN VERBS — never by the shot solver, so what is photographed is the
  // game rather than the instrument:
  //   dio = the shipped diorama (BattleWorld.enabled = false)
  //   off = the world arena on the spike's single solved pose (CAM.on = false)
  //   on  = the world arena with the shot language
  // ------------------------------------------------------------------ sides
  // THE ACCESSOR'S OWN RECEIPT, in BOTH arenas. `stage.sides()` is the value
  // newBody() was constructed with; the claim it has to support is that it
  // PARTITIONS the stage's roster — every body on exactly one side, none
  // missing, none invented. The build orders differ between the two stages
  // (the diorama stages foes first, battle_world the party first), which is
  // exactly what made the old id-pattern fallback safe by accident in one
  // column and wrong in the other, so both are printed with their orders.
  if (MODE === 'sides') {
    const S = SITES.find(s => s.name === arg('site', 'meadow')) || SITES[0];
    const out = { site: S.name, group: S.group, arenas: {} };
    let bad = 0;
    for (const [tag, opt] of [['diorama', 'false, world:false'], ['world', 'true, world:true']]) {
      const [c1, c2] = opt.split(', ');
      const r = await ev(cdp, `window.__BC.startAt(${S.at[0]}, ${S.at[1]}, ${JSON.stringify(S.group)}, {cam:${c1}, ${c2}})`, 300000);
      if (!r.ok) { console.log(tag, 'FAILED', r.why); out.arenas[tag] = { ok: false, why: r.why }; bad++; continue; }
      const ids = Object.keys(r.tiers);
      console.log(`${tag}: build order ${JSON.stringify(ids)}`);
      let res = null;
      try { res = sideReport(tag, r); } catch (e) { console.error('  ' + e.message); bad++; }
      if (res) {
        // the id pattern, computed alongside, so the divergence is on the record
        const pat = ids.filter(i => /^m\d+$/.test(i));
        const same = pat.length === res.foes.length && pat.every(i => res.foes.indexOf(i) >= 0);
        console.log(`  /^m\\d+$/ would have said foes=[${pat}] — ${same ? 'same answer here' : 'DIFFERENT'}`);
        out.arenas[tag] = { ok: true, order: ids, via: res.via, party: res.party, foes: res.foes,
                            idPatternFoes: pat, idPatternAgrees: same };
      }
      await ev(cdp, `window.__BC.end()`, 60000);
    }
    console.log('\n' + JSON.stringify(out, null, 2));
    writeFileSync(join(OUT, 'sides.json'), JSON.stringify(out, null, 2));
    cdp.close(); kill(); process.exit(bad ? 3 : 0);
  }

  if (MODE === 'shots') {
    const site = arg('site', 'meadow');
    const S = SITES.find(s => s.name === site) || SITES[0];
    const meta = { site: S.name, at: S.at, group: S.group, fovBefore: ready.fov, runs: {} };
    const COLS = [['dio', 'false, world:false'], ['off', 'false, world:true'], ['on', 'true, world:true']];
    for (const [tag, opt] of COLS) {
      const [c1, c2] = opt.split(', ');
      const r = await ev(cdp, `window.__BC.startAt(${S.at[0]}, ${S.at[1]}, ${JSON.stringify(S.group)}, {cam:${c1}, ${c2}})`, 300000);
      if (!r.ok) { console.log(tag, 'FAILED', r.why); meta.runs[tag] = r; continue; }
      const { foes, party } = sideReport(`${S.name}/${tag}`, r);
      // ONE CONTINUOUS BEAT SEQUENCE, photographed on the way past. Timings are
      // the shipped pacing's own (announce 300 / approach 260 / wind 300 /
      // damage 640 / ko 820 / winHold 900 / winCheer 620).
      const seq = await ev(cdp, `(async () => {
        const st = window.__BC.stage();
        const W = ms => new Promise(r => setTimeout(r, ms));
        const shots = {}, cams = {};
        const grab = (k) => { shots[k] = st.snapshot(); cams[k] = st.cam ? st.cam() : null; };
        grab('opening');
        st.setActor('${party[0]}'); st.setTarget('${foes[0]}');
        await W(900); grab('decide');
        st.act('${party[0]}', 'attack', '${foes[0]}', 560);
        await W(430); grab('strike');
        st.flinch('${foes[0]}');
        await W(130); grab('impact');
        await W(900);
        if (st.ko) st.ko('${foes[0]}'); else st.setDead('${foes[0]}', true);
        await W(1000); grab('ko');
        await W(1100); grab('koSettled');
        st.cheer();
        await W(820); grab('victory');
        return { shots, cams, world: !!st.world };
      })()`, 180000);
      for (const [k, uri] of Object.entries(seq.shots)) png(`shot-${tag}-${k}.png`, uri);
      const table = tag === 'on' || tag === 'off'
        ? await ev(cdp, `window.__BC.stage().shotTable ? window.__BC.stage().shotTable() : null`) : null;
      meta.runs[tag] = { start: r, world: seq.world, cams: seq.cams, table };
      console.log(`  ${tag}: world=${seq.world} shots=${Object.keys(seq.shots).length}`);
      await ev(cdp, `window.__BC.end()`, 60000);
      meta.runs[tag].fovAfterTeardown = await ev(cdp, `(typeof cam!=='undefined'&&cam)?cam.fov:null`);
    }
    writeFileSync(join(OUT, 'shots.json'), JSON.stringify(meta, null, 2));
    console.log('fov after teardown:', JSON.stringify(Object.entries(meta.runs).map(([k, v]) => [k, v.fovAfterTeardown])));
    cdp.close(); kill(); process.exit(0);
  }

  // ------------------------------------------------------------- legibility
  if (MODE === 'legibility') {
    const out = { sites: {}, when: new Date().toISOString() };
    for (const S of SITES) {
      out.sites[S.name] = {};
      for (const on of [false, true]) {
        const tag = on ? 'on' : 'off';
        process.stdout.write(`  ${S.name} cam=${tag} ... `);
        let r;
        try { r = await ev(cdp, `window.__BC.startAt(${S.at[0]}, ${S.at[1]}, ${JSON.stringify(S.group)}, {cam:${on}})`, 300000); }
        catch (e) { console.log('EXCEPTION', e.message); out.sites[S.name][tag] = { ok: false, why: e.message }; continue; }
        if (!r.ok) { console.log('refused:', r.why); out.sites[S.name][tag] = r; await ev(cdp, `window.__BC.end()`, 60000); continue; }
        const m = await ev(cdp, `(async () => {
          const st = window.__BC.stage();
          st.shotTo('round', {});
          await new Promise(r => setTimeout(r, 1500));
          const lg = window.__BC.legibility();
          return { lg: lg, shot: st.snapshot() };
        })()`, 180000);
        png(`leg-${S.name}-${tag}.png`, m.shot);
        const b = m.lg.bodies;
        const foes = b.filter(x => x.side === 'foe');
        const mean = (a, k) => a.length ? +(a.reduce((s, v) => s + (v[k] || 0), 0) / a.length).toFixed(2) : null;
        const summ = {
          edgeAll: mean(b, 'edgeRGB'), edgeFoe: mean(foes, 'edgeRGB'),
          edgeLumAll: mean(b, 'edge'),
          occlAll: mean(b, 'occl'), occlMax: b.length ? +Math.max(...b.map(x => x.occl || 0)).toFixed(3) : null,
          foeHPctMin: foes.length ? +Math.min(...foes.map(x => x.hPct)).toFixed(2) : null,
          foeHPctMean: mean(foes, 'hPct'),
          clutter: mean(b, 'clutter'),
          pose: m.lg.cam && m.lg.cam.pose, base: m.lg.cam && m.lg.cam.base,
          view: m.lg.cam && m.lg.cam.view, axis: m.lg.cam && m.lg.cam.axis,
        };
        out.sites[S.name][tag] = { ok: true, zone: r.zone, bodies: b, summary: summ, plan: r.plan && { yawDelta: r.plan.yawDelta, relief: r.plan.relief } };
        console.log(`edge=${summ.edgeAll} foeH=${summ.foeHPctMean}% occl=${summ.occlAll} clutter=${summ.clutter}`);
        await ev(cdp, `window.__BC.end()`, 60000);
      }
    }
    writeFileSync(join(OUT, 'legibility.json'), JSON.stringify(out, null, 2));
    // the roll-up, printed so a run is readable without opening the file
    console.log('\nsite      | edge off->on | foe h% off->on | occl off->on | clutter off->on');
    for (const [n, v] of Object.entries(out.sites)) {
      const a = v.off && v.off.summary, c = v.on && v.on.summary;
      if (!a || !c) { console.log(`${n.padEnd(9)} | INCOMPLETE`); continue; }
      console.log(`${n.padEnd(9)} | ${String(a.edgeAll).padStart(5)} -> ${String(c.edgeAll).padStart(5)} | ${String(a.foeHPctMean).padStart(5)} -> ${String(c.foeHPctMean).padStart(5)} | ${String(a.occlAll).padStart(5)} -> ${String(c.occlAll).padStart(5)} | ${String(a.clutter).padStart(5)} -> ${String(c.clutter).padStart(5)}`);
    }
    cdp.close(); kill(); process.exit(0);
  }

  // ------------------------------------------------------------------ moves
  if (MODE === 'moves') {
    const S = SITES.find(s => s.name === (arg('site', 'meadow'))) || SITES[0];
    const meta = { site: S.name, ko: {}, victory: {} };
    for (const on of [false, true]) {
      const tag = on ? 'on' : 'off';
      const r = await ev(cdp, `window.__BC.startAt(${S.at[0]}, ${S.at[1]}, ${JSON.stringify(S.group)}, {cam:${on}})`, 300000);
      if (!r.ok) { meta.ko[tag] = { ok: false, why: r.why }; continue; }
      const { foes, party } = sideReport(`${S.name}/ko-${tag}`, r);
      // THE KO PUSH — sampled on the same clock the beat runs on
      const ko = await ev(cdp, `(async () => {
        const st = window.__BC.stage();
        st.setActor('${party[0]}'); st.setTarget('${foes[0]}');
        const samples = [], shots = {};
        const t0 = performance.now();
        st.ko('${foes[0]}');
        const marks = [80, 340, 700, 1000, 1500, 2100, 2800];
        let mi = 0;
        while (mi < marks.length) {
          await new Promise(r => setTimeout(r, 40));
          const t = performance.now() - t0;
          const c = st.cam();
          samples.push({ t: +t.toFixed(0), dist: c.pose ? c.pose.dist : null, fov: c.pose ? c.pose.fov : null, kind: c.kind });
          if (t >= marks[mi]) { shots['t' + marks[mi]] = st.snapshot(); mi++; }
        }
        return { samples, shots, cam: st.cam() };
      })()`, 180000);
      for (const [k, uri] of Object.entries(ko.shots || {})) png(`ko-${tag}-${k}.jpg`.replace('.jpg', '.png'), uri);
      delete ko.shots;
      const ds = ko.samples.map(s => s.dist).filter(v => v != null);
      ko.travel = ds.length ? +(Math.max(...ds) - Math.min(...ds)).toFixed(3) : null;
      meta.ko[tag] = ko;
      console.log(`  ko cam=${tag}: boom travel ${ko.travel} m over the hold`);
      // THE VICTORY MOVE
      const vic = await ev(cdp, `(async () => {
        const st = window.__BC.stage();
        const samples = [], shots = {};
        const t0 = performance.now();
        st.cheer();
        const marks = [60, 400, 800, 1200, 1600];
        let mi = 0;
        while (mi < marks.length) {
          await new Promise(r => setTimeout(r, 40));
          const t = performance.now() - t0;
          const c = st.cam();
          samples.push({ t: +t.toFixed(0), dist: c.pose ? c.pose.dist : null, yaw: c.pose ? c.pose.yaw : null, kind: c.kind });
          if (t >= marks[mi]) { shots['t' + marks[mi]] = st.snapshot(); mi++; }
        }
        return { samples, shots, cam: st.cam() };
      })()`, 180000);
      for (const [k, uri] of Object.entries(vic.shots || {})) png(`vic-${tag}-${k}.png`, uri);
      delete vic.shots;
      const ys = vic.samples.map(s => s.yaw).filter(v => v != null);
      const vd = vic.samples.map(s => s.dist).filter(v => v != null);
      vic.yawSwing = ys.length ? +(Math.max(...ys) - Math.min(...ys)).toFixed(3) : null;
      vic.travel = vd.length ? +(Math.max(...vd) - Math.min(...vd)).toFixed(3) : null;
      meta.victory[tag] = vic;
      console.log(`  victory cam=${tag}: yaw swing ${vic.yawSwing} rad, boom travel ${vic.travel} m`);
      await ev(cdp, `window.__BC.end()`, 60000);
    }
    writeFileSync(join(OUT, 'moves.json'), JSON.stringify(meta, null, 2));
    cdp.close(); kill(); process.exit(0);
  }

  // ----------------------------------------------------------------- assert
  // THE 180-DEGREE RULE, ON EVERY SHOT IN THE TABLE, AT EVERY SITE, AT EVERY
  // ENCOUNTER SHAPE THE STAGING SOLVE SUPPORTS. A rule that is only checked on
  // the shot you photographed is not a rule.
  if (MODE === 'assert') {
    const shapes = [['duskpad'], ['duskpad', 'duskpad'], ['duskpad', 'reed-nibbler', 'scree-shell']];
    const out = { rows: [], fail: 0, checked: 0 };
    for (const S of SITES) {
      for (const g of shapes) {
        const r = await ev(cdp, `window.__BC.startAt(${S.at[0]}, ${S.at[1]}, ${JSON.stringify(g)}, {cam:true})`, 300000);
        if (!r.ok) { out.rows.push({ site: S.name, n: g.length, ok: false, why: r.why }); continue; }
        const t = await ev(cdp, `(() => {
          const st = window.__BC.stage();
          const ids = st.qa.ids(), sides = st.sides();
          const party = ids.filter(i => sides[i] === 'party'), foes = ids.filter(i => sides[i] === 'foe');
          const rows = [];
          // every (actor, target) pairing the fight can produce, not just one
          for (const a of ids) for (const tg of ids) {
            if (sides[a] === sides[tg]) continue;
            st.setActor(a); st.setTarget(tg);
            for (const row of st.shotTable({ decide: { actor: a, target: tg }, strike: { actor: a, target: tg },
                                             impact: { actor: a, target: tg }, ko: { victim: tg } })) {
              rows.push({ actor: a, target: tg, kind: row.kind, ok: row.axis.ok, order: row.axis.order,
                          side: row.axis.side, gap: row.axis.gap, refused: row.refused, softened: row.softened });
            }
          }
          return { rows, cam: st.cam() };
        })()`, 180000);
        for (const row of t.rows) {
          out.checked++;
          if (!row.ok) out.fail++;
          out.rows.push(Object.assign({ site: S.name, n: g.length }, row));
        }
        console.log(`  ${S.name} ${g.length}v2: ${t.rows.length} shots, ${t.rows.filter(x => !x.ok).length} axis violations, ${t.rows.filter(x => x.refused).length} refused`);
        await ev(cdp, `window.__BC.end()`, 60000);
      }
    }
    out.softened = out.rows.filter(r => r.softened != null && r.softened < 1).length;
    out.refused = out.rows.filter(r => r.refused).length;
    writeFileSync(join(OUT, 'assert.json'), JSON.stringify(out, null, 2));
    console.log(`\n180-RULE: ${out.checked} shots solved, ${out.fail} violations, ${out.softened} softened, ${out.refused} refused`);
    cdp.close(); kill(); process.exit(out.fail ? 1 : 0);
  }

  // -------------------------------------------------------------------- fps
  if (MODE === 'fps') {
    const S = SITES[0];
    const out = {};
    for (const on of [false, true]) {
      const tag = on ? 'camOn' : 'camOff';
      const r = await ev(cdp, `window.__BC.startAt(${S.at[0]}, ${S.at[1]}, ${JSON.stringify(S.group)}, {cam:${on}})`, 300000);
      if (!r.ok) { out[tag] = { ok: false, why: r.why }; continue; }
      out[tag] = await ev(cdp, `(async () => {
        const st = window.__BC.stage();
        // measure WHILE the camera is working, not while it is parked
        st.shotTo('strike', {});
        let n = 0, stop = false; const t0 = performance.now();
        const tick = () => { n++; if (!stop) requestAnimationFrame(tick); };
        requestAnimationFrame(tick);
        await new Promise(r => setTimeout(r, 4000));
        stop = true;
        const dt = (performance.now() - t0) / 1000;
        return { ok: true, fps: +(n / dt).toFixed(1), dt: +dt.toFixed(2),
                 canvases: document.querySelectorAll('canvas').length,
                 calls: R.info.render.calls, tris: R.info.render.triangles,
                 moves: st.cam().moves, refusals: st.cam().refusals };
      })()`, 180000);
      console.log(`  ${tag}: ${out[tag].fps} fps`);
      await ev(cdp, `window.__BC.end()`, 60000);
    }
    // and the field with no battle, for the same reason the spike measured it
    out.fieldIdle = await ev(cdp, `(async () => {
      let n = 0, stop = false; const t0 = performance.now();
      const tick = () => { n++; if (!stop) requestAnimationFrame(tick); };
      requestAnimationFrame(tick);
      await new Promise(r => setTimeout(r, 4000)); stop = true;
      return { fps: +(n / ((performance.now() - t0) / 1000)).toFixed(1) };
    })()`, 60000);
    console.log('  fieldIdle:', out.fieldIdle.fps);
    writeFileSync(join(OUT, 'fps.json'), JSON.stringify(out, null, 2));
    cdp.close(); kill(); process.exit(0);
  }

  // ---------------------------------------------------------------- regress
  // FLAG OFF MUST BE TODAY'S GAME. The page is opened with no ?arena=world, so
  // battle_world.js is the frozen inert object it ships as; the battle must come
  // up on the DIORAMA with two canvases and the field's own fov untouched.
  if (MODE === 'regress') {
    const bw = await ev(cdp, `JSON.parse(JSON.stringify(window.BattleWorld))`);
    const before = await ev(cdp, `({ fov: cam.fov, orbit: Object.assign({}, window.ORBIT), pos: SIM.pos(),
                                     canvases: document.querySelectorAll('canvas').length })`);
    const r = await ev(cdp, `(async () => {
      const GS = window.GS, RU = window.Rules;
      GS.setFlags({ 'maren-joined': true });
      const items = GS.data.items.items, growth = GS.data.growth;
      const party = GS.activeParty().filter(c => ['vesper','maren'].indexOf(c.id) >= 0)
                     .map(c => RU.derive.partyMember(growth, items, c));
      const zone = SIM.zone() || 'meadow';
      const zd = GS.data.encounters.zones[zone] || GS.data.encounters.zones.meadow;
      const p = window.Battle.start({ zone, group: ['duskpad','duskpad'], seed: 4242, backdrop: zd && zd.battleBackdrop },
                                    party, { speed: 1 });
      p.then(()=>{},()=>{});
      const S = () => (window.__EBB_SCREEN && window.__EBB_SCREEN.stage) || null;
      for (let i = 0; i < 250 && !S(); i++) await new Promise(r => setTimeout(r, 100));
      const st = S(); if (!st) return { ok: false, why: 'no stage' };
      await new Promise(r => setTimeout(r, 2500));
      const out = { ok: true, world: !!st.world, hasCam: typeof st.cam === 'function',
                    canvases: document.querySelectorAll('canvas').length,
                    fov: cam.fov, orbit: Object.assign({}, window.ORBIT),
                    bodies: Object.keys(st.tiers()).length,
                    patched: !!(window.BattleStage3D && window.BattleStage3D.__bwPatched),
                    shot: st.snapshot ? st.snapshot() : null };
      try { st.destroy(); } catch (e) {}
      try { window.__EBB_SCREEN && window.__EBB_SCREEN.destroy(); } catch (e) {}
      document.querySelectorAll('.ebb-root').forEach(n => n.remove());
      window.__EBB_SCREEN = null; window.Battle.active = false;
      try { window.UILOCK && UILOCK.unlock('battle'); } catch (e) {}
      await new Promise(r => setTimeout(r, 500));
      out.after = { fov: cam.fov, orbit: Object.assign({}, window.ORBIT), pos: SIM.pos(),
                    canvases: document.querySelectorAll('canvas').length };
      return out;
    })()`, 300000);
    png('regress-diorama.png', r.shot); delete r.shot;
    const out = { battleWorld: bw, before, battle: r };
    console.log(JSON.stringify(out, null, 2));
    writeFileSync(join(OUT, 'regress.json'), JSON.stringify(out, null, 2));
    cdp.close(); kill(); process.exit(0);
  }

  console.error('unknown --mode=' + MODE);
  cdp.close(); kill(); process.exit(2);
})().catch((e) => { console.error('battle_camera error:', e); kill(); process.exit(2); });
