#!/usr/bin/env node
// battle_place.mjs — IS THIS A GOOD PLACE TO FIGHT?
//
// THE QUESTION NOBODY HAD ASKED. `stageArena` stages 100% of sampled ow-valley
// cells and the camera language owns size, occlusion and (2026-08-09) tonal
// separation — but the staging search only ever asked "can bodies stand here"
// and "can the camera see them". It never asked whether the PLACE is any good.
// Measured examples that motivated this file: crag stages on a bare rock dome
// that fills 70% of frame; meadow stages into a building's shadow; forest
// stages the party INSIDE a hedge bank at the hedge's own value. All legal.
//
//   node tools/battle_place.mjs --mode=capture --port=3000 --n=80
//   node tools/battle_place.mjs --mode=sheets                    # contact sheets
//   node tools/battle_place.mjs --mode=board                     # the QA page
//
// THE METHOD IS DELIBERATELY IN THIS ORDER, and the order is the whole point:
// CAPTURE a large sample -> SORT IT BY EYE into good/acceptable/bad from the
// contact sheets alone -> ONLY THEN ask which recorded axis separates the piles.
// A metric invented before the sort is taste with a number on it. The sorting
// verdicts live in docs/qa/battle-placement/sort.json and are hand-written.
//
// EVERY PICTURE IS THE PLAYER'S OWN PIPELINE. A site is captured by starting a
// REAL battle at it (Battle.start -> the shipped BattleWorld stage, the shipped
// camera language, the shipped tone chooser) and calling the stage's own
// `snapshot()`, which renders through play3d's renderFrame (RenderPass -> GTAO
// -> bloom -> OutputPass). So the bytes read back are DISPLAY-SPACE and no
// explicit encode is applied or needed anywhere below — the trap the separation
// lane paid (r185 renders a non-XR target in the LINEAR working space and
// OutputPass is not in that loop) does not exist on this path, because this
// path never reads an offscreen target.
//
// Chrome goes through tools/cdp.mjs and is reaped by --user-data-dir prefix.
import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync, readFileSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import { freePort, killOrphans, sweepStaleProfiles } from './cdp.mjs';

const require = createRequire(import.meta.url);
const WebSocket = require('ws');
const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');

const argv = process.argv.slice(2);
const arg = (k, d) => { const h = argv.find(a => a.startsWith('--' + k + '=')); return h ? h.split('=').slice(1).join('=') : d; };
const PORT = parseInt(arg('port', '3000'), 10);
const MODE = arg('mode', 'capture');
const N = parseInt(arg('n', '80'), 10);
const OUT = join(ROOT, arg('out', 'docs/qa/battle-placement'));
const SHOTS = join(OUT, arg('shots', 'sites'));
const HEAD = argv.includes('--head');
const START = parseInt(arg('start', '0'), 10);
const SPREAD = parseFloat(arg('spread', '7'));   // metres between accepted sites
const TAG = arg('tag', '');
const ROT0 = parseInt(arg('rot', '0'), 10);   // shift the landing-bearing ladder (second-pass sampling)                      // suffix on the output json/dir

mkdirSync(OUT, { recursive: true });
mkdirSync(SHOTS, { recursive: true });

const CDP_PORT = await freePort();
const CHROME = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const sleep = ms => new Promise(r => setTimeout(r, ms));

const PROFILE_PREFIX = 'battle-place-';
sweepStaleProfiles(PROFILE_PREFIX);
const profile = join(process.env.TMPDIR || '/tmp', PROFILE_PREFIX + process.pid);

const URL = `http://localhost:${PORT}/play3d.html?scene=ow-valley&rt=1&nomusic=1&arena=world`;
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
      return { ready: true, three: THREE.REVISION, scene: SIM.bounds().scene, pos: SIM.pos() };
    }
    await new Promise(r => setTimeout(r, 200));
  }
  return { ready: false };
})()`;

// ============================ THE MEASUREMENT LIBRARY ======================
// Installed once into the page, then called per site. Everything here reads
// either the FINAL DISPLAY FRAME (through the stage's own snapshot path) or the
// ENGINE (SIM.ground / a Raycaster against the drawn scene) — never a file and
// never an offscreen target.
const LIB = `(() => {
  const W = {};
  window.__PLACE = W;
  const TH = window.THREE;

  // ---- the two frames -----------------------------------------------------
  // A 2D canvas of the WebGL canvas at probe resolution. The WebGL canvas is
  // already display-space (OutputPass ran), so drawImage is a resize and
  // nothing else. Rows run TOP-DOWN here, both frames the same way, which is
  // the only thing the difference cares about.
  const RW = 320, RH = 180;
  const c2 = document.createElement('canvas'); c2.width = RW; c2.height = RH;
  const g2 = c2.getContext('2d', { willReadFrequently: true });
  function grab() {
    const src = document.querySelector('canvas');
    g2.drawImage(src, 0, 0, RW, RH);
    return g2.getImageData(0, 0, RW, RH).data;
  }
  // hide/show every node the world arena added, so the SAME renderFrame can be
  // asked for the frame WITHOUT the cast. The mask is then the real silhouette,
  // shadows/bloom and all, rather than a guess from a projected box.
  function bwRoots() {
    const out = [];
    scene.traverse(o => {
      if (o.userData && o.userData.isBattleWorld) {
        let p = o.parent, own = true;
        while (p) { if (p.userData && p.userData.isBattleWorld) { own = false; break; } p = p.parent; }
        if (own) out.push(o);
      }
    });
    return out;
  }
  W.frames = function () {
    const st = window.__EBB_SCREEN && window.__EBB_SCREEN.stage;
    const roots = bwRoots();
    st.snapshot();                          // one render, cast in
    const full = grab();
    const were = roots.map(r => r.visible);
    roots.forEach(r => { r.visible = false; });
    st.snapshot();                          // one render, cast out
    const bg = grab();
    roots.forEach((r, i) => { r.visible = were[i]; });
    st.snapshot();                          // put the picture back
    return { full: full, bg: bg, rw: RW, rh: RH };
  };

  const lum = (r, g, b) => 0.2126 * r + 0.7152 * g + 0.0722 * b;

  // ---- the cast mask, and what the silhouette reads against ---------------
  W.silhouette = function (F) {
    const { full, bg, rw, rh } = F;
    const m = new Uint8Array(rw * rh);
    let n = 0;
    for (let i = 0, p = 0; p < rw * rh; p++, i += 4) {
      const d = Math.max(Math.abs(full[i] - bg[i]), Math.abs(full[i + 1] - bg[i + 1]), Math.abs(full[i + 2] - bg[i + 2]));
      if (d > 12) { m[p] = 1; n++; }
    }
    if (n < 20) return { ok: false, why: 'no silhouette', castPx: n };
    const at = (x, y) => (x < 0 || y < 0 || x >= rw || y >= rh) ? 0 : m[y * rw + x];
    const K = 1, RING = 5;
    const eRGB = [0, 0, 0], rRGB = [0, 0, 0];
    let nE = 0, nR = 0, sL = 0, sL2 = 0, castL = 0, nC = 0;
    // per-column contrast, so the WORST part of the cast is visible as a number
    const colD = [];
    for (let y = 0; y < rh; y++) for (let x = 0; x < rw; x++) {
      const p = y * rw + x, i = p * 4;
      if (m[p]) {
        castL += lum(full[i], full[i + 1], full[i + 2]); nC++;
        let edge = 0;
        for (let dy = -K; dy <= K && !edge; dy++) for (let dx = -K; dx <= K; dx++) if (!at(x + dx, y + dy)) { edge = 1; break; }
        if (edge) { eRGB[0] += full[i]; eRGB[1] += full[i + 1]; eRGB[2] += full[i + 2]; nE++; }
      } else {
        let near = 0;
        for (let dy = -RING; dy <= RING && !near; dy++) for (let dx = -RING; dx <= RING; dx++) if (at(x + dx, y + dy)) { near = 1; break; }
        if (near) {
          rRGB[0] += bg[i]; rRGB[1] += bg[i + 1]; rRGB[2] += bg[i + 2]; nR++;
          const L = lum(bg[i], bg[i + 1], bg[i + 2]);
          sL += L; sL2 += L * L;
        }
      }
    }
    if (!nE || !nR) return { ok: false, why: 'no edge or no ring', castPx: n };
    const dr = eRGB[0] / nE - rRGB[0] / nR, dg = eRGB[1] / nE - rRGB[1] / nR, db = eRGB[2] / nE - rRGB[2] / nR;
    const mL = sL / nR;
    // THE WORST BODY, approximated by the worst COLUMN BAND of the mask: split
    // the mask's x-extent into 6 bands and score each the same way. A mean-only
    // number buys a good average and one invisible body (scoreView's lesson).
    let x0 = rw, x1 = 0;
    for (let y = 0; y < rh; y++) for (let x = 0; x < rw; x++) if (m[y * rw + x]) { if (x < x0) x0 = x; if (x > x1) x1 = x; }
    const B = 6, bw = Math.max(1, (x1 - x0 + 1) / B);
    for (let b = 0; b < B; b++) {
      const bx0 = Math.floor(x0 + b * bw), bx1 = Math.floor(x0 + (b + 1) * bw);
      const e = [0, 0, 0], r = [0, 0, 0]; let ne = 0, nr = 0;
      for (let y = 0; y < rh; y++) for (let x = bx0; x < bx1; x++) {
        const p = y * rw + x, i = p * 4;
        if (m[p]) {
          let edge = 0;
          for (let dy = -K; dy <= K && !edge; dy++) for (let dx = -K; dx <= K; dx++) if (!at(x + dx, y + dy)) { edge = 1; break; }
          if (edge) { e[0] += full[i]; e[1] += full[i + 1]; e[2] += full[i + 2]; ne++; }
        } else {
          let near = 0;
          for (let dy = -RING; dy <= RING && !near; dy++) for (let dx = -RING; dx <= RING; dx++) if (at(x + dx, y + dy)) { near = 1; break; }
          if (near) { r[0] += bg[i]; r[1] += bg[i + 1]; r[2] += bg[i + 2]; nr++; }
        }
      }
      if (ne > 8 && nr > 8) {
        const a = e[0] / ne - r[0] / nr, b2 = e[1] / ne - r[1] / nr, c = e[2] / ne - r[2] / nr;
        colD.push(+Math.sqrt((a * a + b2 * b2 + c * c) / 3).toFixed(2));
      }
    }
    return { ok: true, castPx: n, castFrac: +(n / (rw * rh)).toFixed(4),
             edgeRGB: +Math.sqrt((dr * dr + dg * dg + db * db) / 3).toFixed(2),
             bandMin: colD.length ? Math.min.apply(null, colD) : null,
             bands: colD,
             clutter: +Math.sqrt(Math.max(0, sL2 / nR - mL * mL)).toFixed(2),
             ringL: +mL.toFixed(1),
             castL: nC ? +(castL / nC).toFixed(1) : null,
             mask: m };
  };

  // ---- what the FRAME is made of ------------------------------------------
  // "How much of frame does ONE surface own" — asked of the background frame
  // (the cast removed, so a big body cannot answer its own question). Colours
  // are quantised to a 6x6x6 cube; the biggest bin's share is the answer, and
  // the histogram's normalised entropy is background VARIETY.
  W.surface = function (F, mask) {
    const { bg, rw, rh } = F;
    const H = new Float64Array(216);
    let tot = 0;
    const Hb = new Float64Array(216); let totB = 0;   // behind the cast only
    const RING = 10;
    const at = (x, y) => (!mask || x < 0 || y < 0 || x >= rw || y >= rh) ? 0 : mask[y * rw + x];
    for (let y = 0; y < rh; y++) for (let x = 0; x < rw; x++) {
      const i = (y * rw + x) * 4;
      const b = (Math.min(5, bg[i] * 6 / 256 | 0) * 36) + (Math.min(5, bg[i + 1] * 6 / 256 | 0) * 6) + Math.min(5, bg[i + 2] * 6 / 256 | 0);
      H[b]++; tot++;
      if (mask) {
        let near = 0;
        for (let dy = -RING; dy <= RING && !near; dy += 2) for (let dx = -RING; dx <= RING; dx += 2) if (at(x + dx, y + dy)) { near = 1; break; }
        if (near && !at(x, y)) { Hb[b]++; totB++; }
      }
    }
    const stat = (h, t) => {
      if (!t) return { top: null, ent: null };
      let top = 0, ent = 0, nz = 0;
      for (let i = 0; i < h.length; i++) { if (h[i] > top) top = h[i]; if (h[i] > 0) { const p = h[i] / t; ent -= p * Math.log2(p); nz++; } }
      return { top: +(top / t).toFixed(4), ent: +ent.toFixed(3), bins: nz };
    };
    const a = stat(H, tot), b = stat(Hb, totB);
    return { topSurface: a.top, entropy: a.ent, bins: a.bins,
             backTopSurface: b.top, backEntropy: b.ent, backBins: b.bins };
  };

  // ---- what the camera is actually looking at ------------------------------
  // A ray grid through the live camera against the DRAWN scene minus the sky
  // dome, the haze veils, the ambient particles, the walk meshes and our own
  // bodies. A MISS is therefore sky. InstancedMesh ground scatter is excluded
  // wholesale: it is ground detail the player walks through, it is not a
  // surface behind anybody, and it is where all the raycast seconds live
  // (docs/qa/battle-world/raycost.json).
  const NOTOCC = /^(__owsky|__owveil|amb_|bw_)/;
  let _set = null, _stamp = 0;
  function occl() {
    if (_set && performance.now() - _stamp < 3000) return _set;
    const out = [];
    scene.traverse(o => {
      if (!(o.isMesh || o.isInstancedMesh) || o.isSkinnedMesh) return;
      if (o.isInstancedMesh) return;
      if (o.userData && (o.userData.isWalk || o.userData.isBattleWorld)) return;
      if (NOTOCC.test(o.name || '')) return;
      let a = o; while (a) { if (a.userData && a.userData.isBattleWorld) return; a = a.parent; }
      if (!o.visible) return;
      out.push(o);
    });
    _set = out; _stamp = performance.now();
    return out;
  }
  W.rays = function (GX, GY) {
    const rc = new TH.Raycaster();
    const set = occl();
    const c = cam;
    const d = [], sky = [];
    let nSky = 0, n = 0;
    const v = new TH.Vector2();
    for (let gy = 0; gy < GY; gy++) for (let gx = 0; gx < GX; gx++) {
      v.set((gx + 0.5) / GX * 2 - 1, 1 - (gy + 0.5) / GY * 2);
      rc.setFromCamera(v, c);
      rc.far = 900;
      const h = rc.intersectObjects(set, true);
      n++;
      if (!h.length) { nSky++; sky.push(1); d.push(null); }
      else { sky.push(0); d.push(+h[0].distance.toFixed(2)); }
    }
    const hits = d.filter(v2 => v2 != null).sort((a, b) => a - b);
    const q = (p) => hits.length ? hits[Math.min(hits.length - 1, Math.floor(hits.length * p))] : null;
    // DEPTH LAYERING: how many distinct distance bands the frame contains, in
    // octaves. A frame whose every ray lands between 6 and 9 m is a wall.
    const oct = {};
    for (const v2 of hits) oct[Math.round(Math.log2(Math.max(1, v2)) * 2)] = 1;
    // HORIZON: is there sky in the frame AND is its lower boundary inside it.
    let horizonRow = null;
    for (let gy = 0; gy < GY && horizonRow == null; gy++) {
      let s = 0; for (let gx = 0; gx < GX; gx++) s += sky[gy * GX + gx];
      if (s / GX < 0.5) horizonRow = gy;
    }
    return { skyFrac: +(nSky / n).toFixed(3),
             dNear: q(0.05), dMed: q(0.5), dFar: q(0.95),
             dSpanOct: hits.length ? +(Math.log2(Math.max(1, q(0.95)) / Math.max(1, q(0.05)))).toFixed(2) : null,
             layers: Object.keys(oct).length,
             horizonRow: horizonRow == null ? null : +(horizonRow / GY).toFixed(3),
             grid: [GX, GY] };
  };

  // ---- the ground the formation stands on ---------------------------------
  // SIM.ground on a lattice over the arena footprint, plane-fit. SLOPE is the
  // fitted plane's tilt; ROUGHNESS is the RMS residual off it, which is the
  // thing "a bare rock dome" and "a stair" have and a meadow does not.
  W.ground = function (A0, half, step) {
    const xs = [], zs = [], ys = [];
    let miss = 0, n = 0;
    for (let dx = -half; dx <= half + 1e-6; dx += step) for (let dz = -half; dz <= half + 1e-6; dz += step) {
      n++;
      const g = SIM.ground(A0.x + dx, A0.z + dz, A0.y);
      if (g == null) { miss++; continue; }
      xs.push(dx); zs.push(dz); ys.push(g);
    }
    const m = ys.length;
    if (m < 6) return { ok: false, miss: miss, n: n };
    let sx = 0, sz = 0, sy = 0;
    for (let i = 0; i < m; i++) { sx += xs[i]; sz += zs[i]; sy += ys[i]; }
    const mx = sx / m, mz = sz / m, my = sy / m;
    let sxx = 0, szz = 0, sxz = 0, sxy = 0, szy = 0;
    for (let i = 0; i < m; i++) {
      const a = xs[i] - mx, b = zs[i] - mz, c = ys[i] - my;
      sxx += a * a; szz += b * b; sxz += a * b; sxy += a * c; szy += b * c;
    }
    const det = sxx * szz - sxz * sxz;
    let A = 0, B = 0;
    if (Math.abs(det) > 1e-9) { A = (sxy * szz - szy * sxz) / det; B = (szy * sxx - sxy * sxz) / det; }
    let r2 = 0, mn = 1e9, mx2 = -1e9;
    for (let i = 0; i < m; i++) {
      const p = my + A * (xs[i] - mx) + B * (zs[i] - mz);
      const e = ys[i] - p; r2 += e * e;
      if (ys[i] < mn) mn = ys[i]; if (ys[i] > mx2) mx2 = ys[i];
    }
    return { ok: true, n: n, miss: miss,
             slopeDeg: +(Math.atan(Math.hypot(A, B)) * 180 / Math.PI).toFixed(2),
             rough: +Math.sqrt(r2 / m).toFixed(3),
             span: +(mx2 - mn).toFixed(3) };
  };

  // ---- is the cast in shadow --------------------------------------------
  // Two independent readings, because one alone is ambiguous. (a) the SUN RAY:
  // from each placed body's chest toward the key light, against the same set —
  // a hit means that body is shadowed by geometry. (b) the PIXELS: the mean
  // luminance of the ring band the silhouette is read against, versus the
  // frame's own median. A body in a building's shadow reads low on both.
  W.sun = function (plan) {
    let dir = null;
    try {
      scene.traverse(o => { if (!dir && o.isDirectionalLight && o.intensity > 0.05) {
        const p = new TH.Vector3().setFromMatrixPosition(o.matrixWorld);
        const t = o.target ? new TH.Vector3().setFromMatrixPosition(o.target.matrixWorld) : new TH.Vector3();
        dir = p.sub(t).normalize();
      } });
    } catch (e) { }
    if (!dir) return { ok: false, why: 'no directional light' };
    const rc = new TH.Raycaster();
    const set = occl();
    let shaded = 0, n = 0;
    for (const r of (plan && plan.placed) || []) {
      n++;
      rc.set(new TH.Vector3(r.x, r.y + (r.h || 1.6) * 0.6, r.z), dir.clone());
      rc.far = 120;
      if (rc.intersectObjects(set, true).length) shaded++;
    }
    return { ok: true, n: n, shaded: shaded, shadedFrac: n ? +(shaded / n).toFixed(2) : null,
             dir: [+dir.x.toFixed(3), +dir.y.toFixed(3), +dir.z.toFixed(3)] };
  };
  W.frameL = function (F) {
    const { bg, rw, rh } = F;
    const a = [];
    for (let p = 0; p < rw * rh; p += 3) { const i = p * 4; a.push(lum(bg[i], bg[i + 1], bg[i + 2])); }
    a.sort((x, y) => x - y);
    const q = p => a[Math.min(a.length - 1, Math.floor(a.length * p))];
    return { L05: +q(0.05).toFixed(1), L50: +q(0.5).toFixed(1), L95: +q(0.95).toFixed(1) };
  };
  return true;
})()`;

// ---- MODE: proxy — CAN THE SEARCH AFFORD THE AXIS THAT WON? ---------------
// The by-eye sort is separated best by "how much of the frame does ONE SURFACE
// own" (surf.topSurface, AUC 0.922) — but that number comes from a 320x180
// RENDER, and the staging ladder evaluates up to 25 candidate sites before it
// accepts one. Rendering each is not affordable. So this mode asks whether a
// RAY GRID answers the same question: fire a coarse grid through the candidate
// pose and count what share of it lands on a single MESH. It is measured
// against the same 62 sites and the same hand sort, so the proxy is validated
// before anything is built on it — and its cost is billed in the same run.
const proxyDriver = (sites, gx, gy) => `(async () => {
  const S = ${JSON.stringify(sites)};
  const GX = ${gx}, GY = ${gy};
  const TH = window.THREE;
  const NOTOCC = /^(__owsky|__owveil|amb_|bw_)/;
  const set = [];
  scene.traverse(o => {
    if (!(o.isMesh || o.isInstancedMesh) || o.isSkinnedMesh) return;
    if (o.isInstancedMesh) return;
    if (o.userData && (o.userData.isWalk || o.userData.isBattleWorld)) return;
    if (NOTOCC.test(o.name || '')) return;
    if (!o.visible) return;
    set.push(o);
  });
  const slots = BattleWorld.slotsFor([{id:'vesper'},{id:'maren'}], [{id:'m0'},{id:'m1'}]);
  const out = [];
  let sun = null;
  scene.traverse(o => { if (!sun && o.isDirectionalLight && o.intensity > 0.05) {
    const p = new TH.Vector3().setFromMatrixPosition(o.matrixWorld);
    const t = o.target ? new TH.Vector3().setFromMatrixPosition(o.target.matrixWorld) : new TH.Vector3();
    sun = p.sub(t).normalize();
  } });
  for (const s of S) {
    const f = SIM.floors(s.px, s.pz);
    SIM.tp(s.px, s.pz, f.length ? f[0] : null); SIM.tick(3);
    const t0 = performance.now();
    const st = BattleWorld.stage(slots);
    const stageMs = performance.now() - t0;
    if (!st || !st.plan || !st.plan.ok) { out.push({ id: s.id, ok: false }); continue; }
    const b = st.plan.basis, P = st.at || { x: b.centre[0], y: b.centre[1], z: b.centre[2] };
    const pitch = (b.pitch == null ? BattleWorld.CFG.cam.pitch : b.pitch);
    const D = 9.0, FOV = BattleWorld.CAM.fov.rest;
    const eye = new TH.Vector3(P.x + Math.cos(b.yaw) * Math.cos(pitch) * D,
                               P.y + 1 + Math.sin(pitch) * D,
                               P.z + Math.sin(b.yaw) * Math.cos(pitch) * D);
    const c2 = new TH.PerspectiveCamera(FOV, cam.aspect, 0.1, 900);
    c2.position.copy(eye); c2.up.set(0,1,0); c2.lookAt(P.x, P.y + 1, P.z);
    c2.updateMatrixWorld(); c2.updateProjectionMatrix();
    const t1 = performance.now();
    const rc = new TH.Raycaster(); const v = new TH.Vector2();
    const hitN = {}; let nh = 0, nsky = 0;
    for (let gy2 = 0; gy2 < GY; gy2++) for (let gx2 = 0; gx2 < GX; gx2++) {
      v.set((gx2 + 0.5) / GX * 2 - 1, 1 - (gy2 + 0.5) / GY * 2);
      rc.setFromCamera(v, c2); rc.far = 900;
      const h = rc.intersectObjects(set, true);
      if (!h.length) { nsky++; continue; }
      let o = h[0].object; while (o.parent && o.parent !== scene && !(o.userData && o.userData.owGroup)) o = o.parent;
      const k = o.uuid; hitN[k] = (hitN[k] || 0) + 1; nh++;
    }
    const gridMs = performance.now() - t1;
    let top = 0; for (const k in hitN) if (hitN[k] > top) top = hitN[k];
    const N = GX * GY;
    // sun exposure of the placed slots, four rays, the cheapest term measured
    const t2 = performance.now();
    let shaded = 0;
    if (sun) for (const r of st.plan.placed) {
      rc.set(new TH.Vector3(r.x, r.y + (r.h || 1.6) * 0.6, r.z), sun.clone()); rc.far = 120;
      if (rc.intersectObjects(set, true).length) shaded++;
    }
    const sunMs = performance.now() - t2;
    out.push({ id: s.id, ok: true, meshTop: +(top / N).toFixed(4), meshN: Object.keys(hitN).length,
               skyFrac: +(nsky / N).toFixed(3),
               shadedFrac: st.plan.placed.length ? +(shaded / st.plan.placed.length).toFixed(3) : null,
               stageMs: +stageMs.toFixed(1), gridMs: +gridMs.toFixed(1), sunMs: +sunMs.toFixed(2),
               R: st.R, occl: set.length,
               // the CHOSEN SITE, so a run can prove a search optimisation did
               // not change any answer (the short-circuit proof)
               at: { x: +P.x.toFixed(3), y: +P.y.toFixed(3), z: +P.z.toFixed(3) },
               quality: st.quality || null });
  }
  return out;
})()`;

// ---- MODE: equiv — THE SHORT-CIRCUIT PROOF -------------------------------
// PLACE.fastPath stops the candidate walk early in two cases that are argued to
// be answer-preserving. An argument is not a receipt. This drives both arms at
// every sampled cell IN ONE PAGE, with ORBIT.yaw PINNED before each call —
// solveArena's yaw ladder is relative to the live camera heading, so two
// separate runs of the same cell are not comparable and six cells appeared to
// "differ" for exactly that reason before the pin.
const equivDriver = (sites, yaw) => `(async () => {
  const S = ${JSON.stringify(sites)};
  const slots = BattleWorld.slotsFor([{id:'vesper'},{id:'maren'}], [{id:'m0'},{id:'m1'}]);
  const out = [];
  for (const s of S) {
    const f = SIM.floors(s.px, s.pz);
    SIM.tp(s.px, s.pz, f.length ? f[0] : null); SIM.tick(3);
    const arms = {};
    for (const fast of [true, false]) {
      BattleWorld.PLACE.fastPath = fast;
      window.ORBIT.yaw = ${yaw};
      const t0 = performance.now();
      const st = BattleWorld.stage(slots);
      const ms = performance.now() - t0;
      arms[fast ? 'fast' : 'full'] = st && st.at
        ? { x: +st.at.x.toFixed(3), z: +st.at.z.toFixed(3), R: st.R, ms: +ms.toFixed(1),
            lit: st.quality ? st.quality.lit : null, moved: st.quality ? st.quality.moved : null,
            choices: st.quality ? st.quality.choices : null }
        : null;
    }
    BattleWorld.PLACE.fastPath = true;
    const A = arms.fast, B = arms.full;
    out.push({ id: s.id, same: !!(A && B && Math.abs(A.x - B.x) < 1e-6 && Math.abs(A.z - B.z) < 1e-6),
               fast: A, full: B });
  }
  return out;
})()`;

// ---- MODE: neighbours — IS THERE A BETTER SITE TO PREFER? -----------------
// THE QUESTION THAT DECIDES WHETHER A FIX IS WORTH BUILDING, and it is not
// "does the axis separate" (it does). The shipped ladder takes the FIRST
// ring/bearing the solver accepts, and ring 0 — where the player stands —
// accepts most of the time, so the search never sees a second candidate. A
// quality term can only ever help if the sites it could have reached are
// actually better. This mode enumerates ring 0 + the 5 m and 8 m rings at every
// sampled cell, keeps every candidate the SHIPPED solver accepts, scores each
// on sun exposure, and reports the incumbent against the best. If the best is
// not better, the honest answer is to build nothing.
const nbDriver = (sites, rings) => `(async () => {
  const S = ${JSON.stringify(sites)};
  const RINGS = ${JSON.stringify(rings)};
  const TH = window.THREE;
  const NOTOCC = /^(__owsky|__owveil|amb_|bw_)/;
  const set = [];
  scene.traverse(o => {
    if (!(o.isMesh || o.isInstancedMesh) || o.isSkinnedMesh) return;
    if (o.isInstancedMesh) return;
    if (o.userData && (o.userData.isWalk || o.userData.isBattleWorld)) return;
    if (NOTOCC.test(o.name || '')) return;
    if (!o.visible) return;
    set.push(o);
  });
  let sun = null;
  scene.traverse(o => { if (!sun && o.isDirectionalLight && o.intensity > 0.05) {
    const p = new TH.Vector3().setFromMatrixPosition(o.matrixWorld);
    const t = o.target ? new TH.Vector3().setFromMatrixPosition(o.target.matrixWorld) : new TH.Vector3();
    sun = p.sub(t).normalize();
  } });
  const rc = new TH.Raycaster();
  const lit = (x, y, z) => { rc.set(new TH.Vector3(x, y, z), sun.clone()); rc.far = 120;
                             return rc.intersectObjects(set, true).length ? 0 : 1; };
  const slots = BattleWorld.slotsFor([{id:'vesper'},{id:'maren'}], [{id:'m0'},{id:'m1'}]);
  const out = [];
  for (const s of S) {
    const f0 = SIM.floors(s.px, s.pz);
    SIM.tp(s.px, s.pz, f0.length ? f0[0] : null); SIM.tick(3);
    const P0 = SIM.pos();
    const cands = [];
    for (const R of RINGS) {
      const n = R === 0 ? 1 : 8;
      for (let a = 0; a < n; a++) {
        const th = a * Math.PI * 2 / n;
        const x = R === 0 ? P0.x : P0.x + Math.cos(th) * R;
        const z = R === 0 ? P0.z : P0.z + Math.sin(th) * R;
        let at = { x: P0.x, y: P0.y, z: P0.z };
        if (R !== 0) {
          const ff = (SIM.floors(x, z) || []).filter(v => isFinite(v));
          if (!ff.length) continue;
          let y = ff[0];
          for (const v of ff) if (Math.abs(v - P0.y) < Math.abs(y - P0.y)) y = v;
          if (Math.abs(y - P0.y) > 4.0) continue;
          if (SIM.blocked(x, z, y)) continue;
          at = { x: x, y: y, z: z };
        }
        const t0 = performance.now();
        const viable = BattleWorld.screenYaws({ slots: slots, at: at });
        if (!viable.length) continue;
        const plan = BattleWorld.solveArena({ slots: slots, at: at, yaws: viable });
        const solveMs = performance.now() - t0;
        if (!plan || !plan.ok) continue;
        const t1 = performance.now();
        let l = 0;
        for (const r of plan.placed) l += lit(r.x, r.y + (r.h || 1.6) * 0.6, r.z);
        const bodyMs = performance.now() - t1;
        const t2 = performance.now();
        const cLit = lit(at.x, at.y + 1.0, at.z);
        const centreMs = performance.now() - t2;
        cands.push({ R: R, a: a, lit: +(l / plan.placed.length).toFixed(3), cLit: cLit,
                     solveMs: +solveMs.toFixed(1), bodyMs: +bodyMs.toFixed(2), centreMs: +centreMs.toFixed(2),
                     x: +at.x.toFixed(2), z: +at.z.toFixed(2) });
      }
    }
    out.push({ id: s.id, n: cands.length, cands: cands });
  }
  return out;
})()`;

// ---- ONE SITE: land, fight, photograph, measure, tear down ----------------
const siteDriver = (pt, seen, opts) => `(async () => {
  const P = ${JSON.stringify(pt)};
  const SEEN = ${JSON.stringify(seen)};
  const ROT = ${opts.rot | 0};
  const FIGHT = ['meadow','forest','crag','water'];
  const GS = window.GS, B = window.Battle, RU = window.Rules;
  GS.setFlags({ 'maren-joined': true });
  // WALK THE ROAD CELL INTO A CELL A FIGHT CAN FIRE IN — placeDriver's own
  // ladder, to the line, so the sample is the same population the staging rate
  // was measured over.
  // ONE CHANGE, AND IT IS A SAMPLING FIX RATHER THAN A DIFFERENT POPULATION:
  // placeDriver always walks bearing 0 first, so 400 road cells collapse onto a
  // few dozen landing cells and a spatial-spread filter throws most of the
  // sample away (measured: 400 road cells -> 26 sites at 7 m spread). The
  // bearing ladder is ROTATED by the sample index, so the same cells are asked
  // in a different order and the walk lands over the whole encounter band
  // beside the road instead of one side of it. Every landing is still a real
  // standable cell in a real fight zone within 11 m of a road cell.
  let landed = null;
  for (const r of [5, 8, 11]) {
    for (let ai = 0; ai < 8; ai++) {
      const a = (ai + ROT) % 8;
      const th = a * Math.PI / 4;
      const x = P[0] + Math.cos(th) * r, z = P[1] + Math.sin(th) * r;
      const zn = SIM.zone(x, z);
      if (!zn || FIGHT.indexOf(zn) < 0) continue;
      const f = SIM.floors(x, z);
      if (!f.length) continue;
      SIM.tp(x, z, f[0]); SIM.tick(3);
      const p0 = SIM.pos();
      if (!isFinite(p0.y) || Math.abs(p0.y - f[0]) > 3) continue;
      landed = { x: p0.x, y: p0.y, z: p0.z, zone: SIM.zone(p0.x, p0.z) };
      break;
    }
    if (landed) break;
  }
  if (!landed) return { skip: 'no standable encounter cell within 11 m' };
  for (const s of SEEN) if (Math.hypot(s[0]-landed.x, s[1]-landed.z) < ${SPREAD}) return { skip: 'within ${SPREAD} m of an accepted site' };

  // THE SUBJECT IS HELD CONSTANT ACROSS SITES ON PURPOSE. Same party, same two
  // foes, same seed: the only thing that differs between two pictures in this
  // sample is the PLACE, which is the whole variable under study.
  const items = GS.data.items.items, growth = GS.data.growth;
  const party = GS.activeParty().filter(c => ['vesper','maren'].indexOf(c.id) >= 0)
                 .map(c => RU.derive.partyMember(growth, items, c));
  const zd = GS.data.encounters.zones[landed.zone] || GS.data.encounters.zones.meadow;
  const t0 = performance.now();
  const pr = B.start({ zone: landed.zone, group: ['duskpad','reed-nibbler'], seed: 4242,
                       backdrop: zd && zd.battleBackdrop }, party, { speed: 1 });
  pr.then(()=>{}, ()=>{});
  const S = () => (window.__EBB_SCREEN && window.__EBB_SCREEN.stage) || null;
  for (let i = 0; i < 300 && !S(); i++) await new Promise(r => setTimeout(r, 100));
  const st = S();
  if (!st) return { skip: 'no stage', at: landed };
  if (!st.world) return { skip: 'not the world stage', at: landed };
  const f0 = st.frames;
  for (let i = 0; i < 300; i++) {
    const t = st.tiers();
    if (Object.values(t).every(v => v !== 'proxy') && st.frames > f0 + 90) break;
    await new Promise(r => setTimeout(r, 100));
  }
  // let the tone chooser fire and its 700 ms correction land
  for (let i = 0; i < 160; i++) { const tn = st.tone(); if (tn && (tn.ok || tn.why && !/waiting/.test(tn.why))) break; await new Promise(r => setTimeout(r, 100)); }
  await new Promise(r => setTimeout(r, 1100));
  const solveMs = performance.now() - t0;

  // THE FRAME THIS STUDY JUDGES IS THE ESTABLISHING SHOT, AND IT HAS TO BE ASKED
  // FOR. By the time the cast has arrived, battle_turnbased has already handed
  // the turn to the player, so the camera sits on 'decide' — fov 27, show 'actor'
  // — and BOTH FOES ARE OFF FRAME (measured: anchors vis:false for m0/m1 on
  // every pilot site). A place is judged against the whole fight, so the shot
  // table's own 'round' (show all, fov 34) is driven explicitly through the
  // stage's QA verb and given its move time. The 'decide' frame is kept too,
  // unmeasured, because it is the frame the player dwells on longest.
  // (Plain quotes: a backtick in a comment INSIDE a template literal ends the
  // literal — CLAUDE.md's own trap, paid again here at first run.)
  st.shotTo('round', { ms: 520 });
  await new Promise(r => setTimeout(r, 900));
  const shot = st.snapshot();
  const F = window.__PLACE.frames();
  const sil = window.__PLACE.silhouette(F);
  const surf = window.__PLACE.surface(F, sil.ok ? sil.mask : null);
  if (sil.ok) delete sil.mask;
  const rays = window.__PLACE.rays(28, 16);
  const site = st.site || {};
  const A0 = site.at || landed;
  const grd = window.__PLACE.ground(A0, 5, 1.25);
  const sun = window.__PLACE.sun(st.plan);
  const fl = window.__PLACE.frameL(F);
  const camr = st.cam ? st.cam() : null;
  const anchors = {};
  for (const id of Object.keys(st.tiers())) { const a = st.anchor(id); if (a) anchors[id] = { x:+a.x.toFixed(0), y:+a.y.toFixed(0), h:+a.h.toFixed(0), vis:a.vis }; }
  const tone = st.tone ? st.tone() : null;
  const plan = st.plan || {};
  let foe = null; const sides = st.sides ? st.sides() : {};
  for (const id of Object.keys(sides)) if (sides[id] === 'foe') { foe = id; break; }
  st.setActor('vesper'); if (foe) st.setTarget(foe);
  await new Promise(r => setTimeout(r, 800));
  const shotDecide = st.snapshot();
  const out = { at: landed, site: site, zone: landed.zone,
    relief: plan.relief, yawDelta: plan.yawDelta,
    view: plan.view || null,
    pitch: camr && camr.base ? camr.base.pitch : null,
    fov: camr && camr.pose ? camr.pose.fov : null,
    camDist: camr && camr.pose ? camr.pose.dist : null,
    tone: tone ? { ok: tone.ok, chose: tone.chose, was: tone.was, moved: tone.moved,
                   winScore: tone.winScore, incScore: tone.incScore } : null,
    sil: sil, surf: surf, rays: rays, ground: grd, sun: sun, frameL: fl,
    anchors: anchors, tiers: st.tiers(), stageMs: +solveMs.toFixed(0) };

  // teardown (the battle_world_probe recipe)
  try { st.destroy(); } catch (e) {}
  const sc = window.__EBB_SCREEN;
  if (sc && sc.destroy) { try { sc.destroy(); } catch (e) {} }
  window.__EBB_SCREEN = null; window.Battle.active = false;
  document.querySelectorAll('.ebb-root').forEach(n => n.remove());
  try { window.UILOCK && UILOCK.unlock('battle'); } catch (e) {}
  return { ok: true, row: out, shot: shot, shotDecide: shotDecide };
})()`;

(async () => {
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
  const inj = await ev(cdp, INJECT, 60000);
  console.log('battle_world: ' + JSON.stringify(inj));
  await ev(cdp, LIB, 30000);

  if (MODE === 'equiv') {
    const src = JSON.parse(readFileSync(join(OUT, 'sites.json'), 'utf8')).rows
      .concat(existsSync(join(OUT, 'sites-b.json')) ? JSON.parse(readFileSync(join(OUT, 'sites-b.json'), 'utf8')).rows : []);
    const sites = src.map(r => ({ id: r.id, px: r.at.x, pz: r.at.z }));
    const res = [];
    for (let i = 0; i < sites.length; i += 6) {
      res.push(...await ev(cdp, equivDriver(sites.slice(i, i + 6), 0), 300000));
      process.stdout.write('  ' + res.length + '/' + sites.length + '\r');
    }
    const bad = res.filter(r => !r.same);
    const f2 = join(OUT, 'equiv.json');
    const fm = res.map(r => r.fast && r.fast.ms).filter(v => v != null).sort((a, b) => a - b);
    const fl = res.map(r => r.full && r.full.ms).filter(v => v != null).sort((a, b) => a - b);
    const q = (a, p) => a[Math.min(a.length - 1, Math.floor(a.length * p))];
    const sum = { n: res.length, agree: res.length - bad.length, differ: bad.length,
                  fast_ms: { p50: q(fm, 0.5), p90: q(fm, 0.9), max: fm[fm.length - 1] },
                  full_ms: { p50: q(fl, 0.5), p90: q(fl, 0.9), max: fl[fl.length - 1] } };
    writeFileSync(f2, JSON.stringify({ summary: sum, rows: res }, null, 2));
    console.log('\n' + JSON.stringify(sum, null, 2));
    if (bad.length) console.log('DIFFER: ' + JSON.stringify(bad, null, 2));
    console.log('wrote ' + f2);
    cdp.close(); kill(); process.exit(bad.length ? 1 : 0);
  }

  if (MODE === 'neighbours') {
    const src = JSON.parse(readFileSync(join(OUT, 'sites.json'), 'utf8')).rows
      .concat(existsSync(join(OUT, 'sites-b.json')) ? JSON.parse(readFileSync(join(OUT, 'sites-b.json'), 'utf8')).rows : []);
    const sites = src.map(r => ({ id: r.id, px: r.at.x, pz: r.at.z }));
    const rings = arg('rings', '0,5,8').split(',').map(Number);
    const res = [];
    for (let i = 0; i < sites.length; i += 4) {
      res.push(...await ev(cdp, nbDriver(sites.slice(i, i + 4), rings), 300000));
      process.stdout.write('  ' + res.length + '/' + sites.length + '\r');
    }
    const f2 = join(OUT, 'neighbours.json');
    writeFileSync(f2, JSON.stringify({ rings, rows: res }, null, 2));
    console.log('\nwrote ' + f2);
    cdp.close(); kill(); process.exit(0);
  }

  if (MODE === 'proxy') {
    const src = JSON.parse(readFileSync(join(OUT, 'sites.json'), 'utf8')).rows
      .concat(existsSync(join(OUT, 'sites-b.json')) ? JSON.parse(readFileSync(join(OUT, 'sites-b.json'), 'utf8')).rows : []);
    const sites = src.map(r => ({ id: r.id, px: r.at.x, pz: r.at.z }));
    const GX = parseInt(arg('gx', '8'), 10), GY = parseInt(arg('gy', '5'), 10);
    const res = [];
    for (let i = 0; i < sites.length; i += 8) {
      res.push(...await ev(cdp, proxyDriver(sites.slice(i, i + 8), GX, GY), 300000));
      process.stdout.write('  ' + res.length + '/' + sites.length + '\r');
    }
    const f2 = join(OUT, 'proxy-' + GX + 'x' + GY + '.json');
    writeFileSync(f2, JSON.stringify({ grid: [GX, GY], rows: res }, null, 2));
    console.log('\nwrote ' + f2);
    cdp.close(); kill(); process.exit(0);
  }

  const all = JSON.parse(readFileSync(join(ROOT, 'tools/_bw_roadpts.json'), 'utf8'));
  const rows = [];
  const seen = [];
  // A SECOND PASS OVER THE SAME ROAD CELLS, SEEDED WITH THE FIRST PASS'S SITES.
  // The 400 road cells are exhausted in one pass (60 sites at 5 m spread), so a
  // larger sample comes from asking the SAME cells for a DIFFERENT bearing —
  // `--rot` shifts the ladder, `--seedfrom` carries the accepted sites forward
  // so the spread filter still guarantees no two sites in the pooled sample are
  // within 5 m of each other.
  const SEEDF = arg('seedfrom', null);
  let idBase = 0;
  if (SEEDF) {
    const prev = JSON.parse(readFileSync(join(ROOT, SEEDF), 'utf8'));
    for (const r of prev.rows) seen.push([r.at.x, r.at.z]);
    idBase = prev.rows.length;
    console.log('seeded with ' + prev.rows.length + ' sites from ' + SEEDF);
  }
  let idx = START;
  const t0 = Date.now();
  while (rows.length < N && idx < all.length) {
    const pt = all[idx++];
    let r;
    try { r = await ev(cdp, siteDriver(pt, seen, { rot: idx * 3 + ROT0 }), 300000); }
    catch (e) { console.log(`  [${idx}] EXCEPTION ${e.message}`); continue; }
    if (!r || r.skip) { continue; }
    const id = 's' + String(idBase + rows.length).padStart(3, '0');
    if (r.shot) writeFileSync(join(SHOTS, id + '.png'), Buffer.from(r.shot.slice(r.shot.indexOf(',') + 1), 'base64'));
    if (r.shotDecide) writeFileSync(join(SHOTS, id + '-decide.png'), Buffer.from(r.shotDecide.slice(r.shotDecide.indexOf(',') + 1), 'base64'));
    r.row.id = id; r.row.from = pt;
    rows.push(r.row);
    seen.push([r.row.at.x, r.row.at.z]);
    const el = (Date.now() - t0) / 1000;
    console.log(`  ${id} ${r.row.zone.padEnd(7)} R=${String(r.row.site.R).padStart(2)}m  edgeRGB=${r.row.sil.edgeRGB}  top=${r.row.surf.topSurface}  sky=${r.row.rays.skyFrac}  ${el.toFixed(0)}s`);
    await sleep(350);
  }
  const outf = join(OUT, 'sites' + (TAG ? '-' + TAG : '') + '.json');
  writeFileSync(outf, JSON.stringify({ meta: { n: rows.length, scanned: idx - START, spread: SPREAD,
      group: ['duskpad', 'reed-nibbler'], party: ['vesper', 'maren'], three: ready.three,
      when: new Date().toISOString(), secs: +((Date.now() - t0) / 1000).toFixed(0) }, rows }, null, 2));
  console.log(`\nwrote ${rows.length} sites -> ${outf}`);
  console.log(`shots -> ${SHOTS}`);
  cdp.close(); kill(); process.exit(0);
})().catch(e => { console.error('battle_place error:', e); kill(); process.exit(2); });
