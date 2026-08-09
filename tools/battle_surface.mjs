#!/usr/bin/env node
// battle_surface.mjs — CAN THE SEARCH AFFORD ONE-SURFACE DOMINANCE?
//
// THE STANDING BLOCKER. Across three independent sorts (round frame, round
// frame against the decide sort, decide frame) the axis that separates a good
// place to fight from a bad one is "how much of the frame does ONE SURFACE own"
// — surf.topSurface / surf.entropy, sep 0.844 / 0.949 / 0.937. It beat sun
// exposure (which shipped), sky presence, `view.back` (what the solver already
// optimises), and the tonal metric (which runs BACKWARDS as a placement
// metric). It did not ship because it had no affordable proxy: the ray-grid
// version measured 0.79 separation at 52 ms a candidate, against a staging
// ladder that evaluates up to 25 sites inside a ~42 ms solve.
//
// AND THE RAY GRID FAILED FOR A REASON THAT IS VISIBLE IN ITS OWN DATA:
// docs/qa/battle-placement/proxy-14x8.json reads meshTop >= 0.87 at every one
// of 62 sites and 1.00 at many, because the valley ground is ONE MESH. "One
// mesh owns the frame" is true everywhere; "one SURFACE owns the frame" is a
// statement about PIXELS. The winning axis was always a colour histogram.
//
// SO THE HYPOTHESIS THIS FILE TESTS FIRST: `TONE` in battle_world.js already
// renders the arena into a 320x180 offscreen target twice per candidate boom
// and differences them — the WITHOUT-CAST pass IS the background of that frame.
// At ladder time there is no cast at all, so the same measurement needs ONE
// render and no subtraction. If a small offscreen render plus a 6x6x6 histogram
// lands near the offline number, the metric costs a render and a histogram
// rather than a ray grid.
//
//   node tools/battle_surface.mjs --mode=probe  --port=3000     # proxy + cost
//   node tools/battle_surface.mjs --mode=stats                  # separation
//
// SAY WHICH SPACE THE BYTES ARE IN. r185 renders into a non-XR render target in
// the LINEAR working space whatever the texture declares, and OutputPass is not
// in that loop — the same trap TONE paid, which crushed a dark site and picked
// the wrong boom. Exactly one explicit sRGB encode is applied to the bytes read
// back here and nothing else converts anything. `--raw=1` measures the same
// frames WITHOUT that encode, so the cost of getting it wrong is a number in
// this run rather than a paragraph.
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
const MODE = arg('mode', 'probe');
const OUT = join(ROOT, arg('out', 'docs/qa/battle-surface'));
const HEAD = argv.includes('--head');
const TAG = arg('tag', '');
const RAW = arg('raw', '0') === '1';
const REPS = parseInt(arg('reps', '1'), 10);
const LIMIT = parseInt(arg('n', '999'), 10);

mkdirSync(OUT, { recursive: true });

// ---- the 62-site census, taken from the shipped board ---------------------
// Landing cells and the pinned yaw come out of the decide census that the
// current eye sorts were made on, so a proxy measured here is measured at the
// same places the verdicts describe.
function census() {
  const f = join(ROOT, 'docs/qa/battle-decide/census-sAfter.json');
  const d = JSON.parse(readFileSync(f, 'utf8'));
  return { yaw: d.meta.yaw,
           sites: d.rows.map(r => ({ id: r.id, px: r.at.x, pz: r.at.z, zone: r.zone,
                                     surf: r.surf, sil: r.sil, site: r.site })) };
}
function sorts() {
  const pile = s => (s || '').trim().split(/[\s—-]/)[0].toLowerCase();
  const out = {};
  for (const [k, f] of [['round', 'docs/qa/battle-placement/sort.json'],
                        ['decide', 'docs/qa/battle-decide/sort-decide.json'],
                        ['decide2', 'docs/qa/battle-decide/sort-decide-q.json']]) {
    const p = join(ROOT, f);
    if (!existsSync(p)) continue;
    const v = JSON.parse(readFileSync(p, 'utf8')).verdict;
    out[k] = Object.fromEntries(Object.entries(v).map(([id, s]) => [id, pile(s)]));
  }
  return out;
}

// ============================== THE PAGE DRIVER =============================
// One page, every site, the yaw pinned before every stage() call. solveArena's
// yaw ladder is relative to the live camera heading, so two runs of one cell
// are not comparable without the pin — six sites "differed" for exactly that
// reason before it went into the placement lane.
const probeDriver = (sites, yaw, opts) => `(async () => {
  const S = ${JSON.stringify(sites)};
  const YAW = ${yaw};
  const REPS = ${opts.reps};
  const RAW = ${opts.raw};
  const TH = window.THREE;
  const slots = BattleWorld.slotsFor([{id:'vesper'},{id:'maren'}], [{id:'m0'},{id:'m1'}]);

  // ---- SAY WHICH SPACE THE BYTES ARE IN, AND CONVERT ONCE -----------------
  // Identical to battle_world's own _srgbLUT: linear byte -> display byte.
  const SRGB = (function () {
    const t = new Uint8Array(256);
    for (let i = 0; i < 256; i++) {
      const c = i / 255;
      const v = c <= 0.0031308 ? c * 12.92 : 1.055 * Math.pow(c, 1 / 2.4) - 0.055;
      t[i] = Math.max(0, Math.min(255, Math.round(v * 255)));
    }
    return t;
  })();
  const ID = (function () { const t = new Uint8Array(256); for (let i = 0; i < 256; i++) t[i] = i; return t; })();

  // ---- the render targets, allocated ONCE per resolution ------------------
  // A target allocated per candidate would price the allocator, not the metric.
  const RTS = {};
  const BUF = {};
  function rtFor(rw, rh) {
    const k = rw + 'x' + rh;
    if (!RTS[k]) { RTS[k] = new TH.WebGLRenderTarget(rw, rh, { depthBuffer: true, stencilBuffer: false });
                   BUF[k] = new Uint8Array(rw * rh * 4); }
    return { rt: RTS[k], buf: BUF[k] };
  }
  // ---- ONE CANDIDATE'S BACKGROUND, AND WHAT ONE SURFACE OWNS OF IT --------
  // 6x6x6 colour cube, largest bin's share = topSurface; normalised entropy of
  // the same histogram = background VARIETY. Both are the offline library's own
  // arithmetic (tools/battle_place_lib.mjs W.surface) with the ONE difference
  // that there is no cast to hide: at ladder time nothing is staged yet.
  function shot(cam2, rw, rh, lut) {
    const { rt, buf } = rtFor(rw, rh);
    const prev = W_getRT();
    const t0 = performance.now();
    R.setRenderTarget(rt); R.render(scene, cam2);
    const t1 = performance.now();
    R.readRenderTargetPixels(rt, 0, 0, rw, rh, buf);
    const t2 = performance.now();
    R.setRenderTarget(prev);
    const H = new Float64Array(216);
    const n = rw * rh;
    for (let p = 0, i = 0; p < n; p++, i += 4) {
      const b = (Math.min(5, lut[buf[i]] * 6 / 256 | 0) * 36)
              + (Math.min(5, lut[buf[i + 1]] * 6 / 256 | 0) * 6)
              +  Math.min(5, lut[buf[i + 2]] * 6 / 256 | 0);
      H[b]++;
    }
    let top = 0, ent = 0, nz = 0, top2 = 0;
    for (let k = 0; k < 216; k++) {
      const h = H[k];
      if (h > top) { top2 = top; top = h; } else if (h > top2) top2 = h;
      if (h > 0) { const q = h / n; ent -= q * Math.log2(q); nz++; }
    }
    const t3 = performance.now();
    return { topSurface: +(top / n).toFixed(4), top2: +(top2 / n).toFixed(4),
             entropy: +ent.toFixed(3), bins: nz,
             ms: { render: +(t1 - t0).toFixed(2), read: +(t2 - t1).toFixed(2),
                   hist: +(t3 - t2).toFixed(2), all: +(t3 - t0).toFixed(2) },
             buf: null };
  }
  function W_getRT() { return R.getRenderTarget(); }

  // ---- A LARGEST-CONNECTED-REGION variant, priced beside the histogram ----
  // The histogram is blind to WHERE its bin is: a frame half sky and half grass
  // scores the same as a frame speckled with two colours. This labels 4-connected
  // components of the quantised image and returns the largest one's share.
  function region(cam2, rw, rh, lut) {
    const { rt, buf } = rtFor(rw, rh);
    const prev = R.getRenderTarget();
    const t0 = performance.now();
    R.setRenderTarget(rt); R.render(scene, cam2);
    R.readRenderTargetPixels(rt, 0, 0, rw, rh, buf);
    R.setRenderTarget(prev);
    const n = rw * rh;
    const q = new Uint8Array(n);
    for (let p = 0, i = 0; p < n; p++, i += 4) {
      q[p] = (Math.min(3, lut[buf[i]] * 4 / 256 | 0) * 16)
           + (Math.min(3, lut[buf[i + 1]] * 4 / 256 | 0) * 4)
           +  Math.min(3, lut[buf[i + 2]] * 4 / 256 | 0);
    }
    const lab = new Int32Array(n).fill(-1);
    const stack = new Int32Array(n);
    let best = 0, nComp = 0;
    for (let p = 0; p < n; p++) {
      if (lab[p] >= 0) continue;
      const c = q[p]; let sp = 0, cnt = 0;
      stack[sp++] = p; lab[p] = nComp;
      while (sp) {
        const cur = stack[--sp]; cnt++;
        const x = cur % rw, y = (cur / rw) | 0;
        if (x > 0 && lab[cur - 1] < 0 && q[cur - 1] === c) { lab[cur - 1] = nComp; stack[sp++] = cur - 1; }
        if (x < rw - 1 && lab[cur + 1] < 0 && q[cur + 1] === c) { lab[cur + 1] = nComp; stack[sp++] = cur + 1; }
        if (y > 0 && lab[cur - rw] < 0 && q[cur - rw] === c) { lab[cur - rw] = nComp; stack[sp++] = cur - rw; }
        if (y < rh - 1 && lab[cur + rw] < 0 && q[cur + rw] === c) { lab[cur + rw] = nComp; stack[sp++] = cur + rw; }
      }
      if (cnt > best) best = cnt;
      nComp++;
    }
    const t1 = performance.now();
    return { topRegion: +(best / n).toFixed(4), comps: nComp, ms: +(t1 - t0).toFixed(2) };
  }

  // ---- the pose a candidate would be scored from --------------------------
  // Same construction the ray-grid proxy used (battle_place.mjs proxyDriver), so
  // the two proxies are measured through the same lens at the same sites.
  function poseCam(st) {
    const b = st.plan.basis, P = st.at || { x: b.centre[0], y: b.centre[1], z: b.centre[2] };
    const pitch = (b.pitch == null ? BattleWorld.CFG.cam.pitch : b.pitch);
    const D = 9.0, FOV = BattleWorld.CAM.fov.rest;
    const eye = new TH.Vector3(P.x + Math.cos(b.yaw) * Math.cos(pitch) * D,
                               P.y + 1 + Math.sin(pitch) * D,
                               P.z + Math.sin(b.yaw) * Math.cos(pitch) * D);
    const c2 = new TH.PerspectiveCamera(FOV, cam.aspect, 0.1, 900);
    c2.position.copy(eye); c2.up.set(0, 1, 0); c2.lookAt(P.x, P.y + 1, P.z);
    c2.updateMatrixWorld(); c2.updateProjectionMatrix();
    return { c2: c2, P: P, pitch: pitch, yaw: b.yaw };
  }

  // ---- WHY A SMALL NATIVE RENDER IS NOT A SMALL PICTURE -------------------
  // The offline library reads the DISPLAY canvas through drawImage at 320x180,
  // which is a filtered 5x box reduction of a 1600x900 frame. A native 320x180
  // render POINT-SAMPLES the same scene: every twig gets its own bin and the
  // histogram scatters. This renders BIG and averages down, which is the same
  // reduction the ruler uses. The render is geometry-bound (0.43 ms at every
  // resolution measured) and the readback is a sync stall whose cost barely
  // tracks byte count, so the supersample is close to free.
  function shotSS(cam2, sw, sh, s, lut) {
    const rw = (sw / s) | 0, rh = (sh / s) | 0;
    const { rt, buf } = rtFor(sw, sh);
    const prev = R.getRenderTarget();
    const t0 = performance.now();
    R.setRenderTarget(rt); R.render(scene, cam2);
    R.readRenderTargetPixels(rt, 0, 0, sw, sh, buf);
    R.setRenderTarget(prev);
    const H = new Float64Array(216);
    const n = rw * rh;
    for (let y = 0; y < rh; y++) for (let x = 0; x < rw; x++) {
      let r = 0, g = 0, b = 0;
      for (let dy = 0; dy < s; dy++) for (let dx = 0; dx < s; dx++) {
        const i = (((y * s + dy) * sw) + (x * s + dx)) * 4;
        r += lut[buf[i]]; g += lut[buf[i + 1]]; b += lut[buf[i + 2]];
      }
      const k = s * s;
      r /= k; g /= k; b /= k;
      H[(Math.min(5, r * 6 / 256 | 0) * 36) + (Math.min(5, g * 6 / 256 | 0) * 6) + Math.min(5, b * 6 / 256 | 0)]++;
    }
    let top = 0, ent = 0, nz = 0;
    for (let k = 0; k < 216; k++) { const h = H[k]; if (h > top) top = h; if (h > 0) { const q = h / n; ent -= q * Math.log2(q); nz++; } }
    const t1 = performance.now();
    return { topSurface: +(top / n).toFixed(4), entropy: +ent.toFixed(3), bins: nz, ms: +(t1 - t0).toFixed(2) };
  }
  // ---- THE EXACT RULER, PRICED ------------------------------------------
  // The offline number comes off the DISPLAY canvas after RenderPass -> GTAO ->
  // bloom -> OutputPass. This drives the page's own renderFrame() at a candidate
  // pose and reads the canvas exactly as tools/battle_place_lib.mjs does, so the
  // upper bound on what any proxy can achieve is a number in this run.
  const c2d = document.createElement('canvas'); c2d.width = 320; c2d.height = 180;
  const g2d = c2d.getContext('2d', { willReadFrequently: true });
  function shotCanvas(pose) {
    const t0 = performance.now();
    const sv = { p: cam.position.clone(), q: cam.quaternion.clone(), fov: cam.fov,
                 near: cam.near, far: cam.far };
    cam.position.copy(pose.eye); cam.up.set(0, 1, 0); cam.lookAt(pose.look);
    cam.fov = pose.fov; cam.updateProjectionMatrix(); cam.updateMatrixWorld();
    try { window.renderFrame(); } catch (e) { }
    cam.position.copy(sv.p); cam.quaternion.copy(sv.q); cam.fov = sv.fov;
    cam.updateProjectionMatrix(); cam.updateMatrixWorld();
    const src = document.querySelector('canvas');
    g2d.drawImage(src, 0, 0, 320, 180);
    const d = g2d.getImageData(0, 0, 320, 180).data;
    const H = new Float64Array(216);
    const n = 320 * 180;
    for (let p = 0, i = 0; p < n; p++, i += 4) {
      H[(Math.min(5, d[i] * 6 / 256 | 0) * 36) + (Math.min(5, d[i + 1] * 6 / 256 | 0) * 6) + Math.min(5, d[i + 2] * 6 / 256 | 0)]++;
    }
    let top = 0, ent = 0, nz = 0;
    for (let k = 0; k < 216; k++) { const h = H[k]; if (h > top) top = h; if (h > 0) { const q = h / n; ent -= q * Math.log2(q); nz++; } }
    const t1 = performance.now();
    return { topSurface: +(top / n).toFixed(4), entropy: +ent.toFixed(3), bins: nz, ms: +(t1 - t0).toFixed(2) };
  }
  function poseOf(st, fov, D) {
    const b = st.plan.basis, P = st.at || { x: b.centre[0], y: b.centre[1], z: b.centre[2] };
    const pitch = (b.pitch == null ? BattleWorld.CFG.cam.pitch : b.pitch);
    const eye = new TH.Vector3(P.x + Math.cos(b.yaw) * Math.cos(pitch) * D,
                               P.y + 1 + Math.sin(pitch) * D,
                               P.z + Math.sin(b.yaw) * Math.cos(pitch) * D);
    const look = new TH.Vector3(P.x, P.y + 1, P.z);
    const c2 = new TH.PerspectiveCamera(fov, cam.aspect, 0.1, 900);
    c2.position.copy(eye); c2.up.set(0, 1, 0); c2.lookAt(look);
    c2.updateMatrixWorld(); c2.updateProjectionMatrix();
    return { c2: c2, eye: eye, look: look, fov: fov, P: P };
  }

  const RES = [[48, 27], [64, 36], [96, 54], [160, 90], [320, 180]];
  const out = [];
  // THE PLAYER'S OWN BODY IS NOT BACKGROUND. stageArena runs BEFORE the player
  // mesh is hidden for the fight, so a probe render taken at ladder time would
  // photograph the player standing in the middle of ring 0. A visibility flip,
  // never a teardown — the Ambient.hide lesson.
  for (const s of S) {
    const f = SIM.floors(s.px, s.pz);
    SIM.tp(s.px, s.pz, f.length ? f[0] : null); SIM.tick(3);
    window.ORBIT.yaw = YAW;
    const t0 = performance.now();
    const st = BattleWorld.stage(slots);
    const stageMs = performance.now() - t0;
    if (!st || !st.plan || !st.plan.ok) { out.push({ id: s.id, ok: false }); continue; }
    const pc = poseCam(st);
    const chWas = (typeof ch !== 'undefined' && ch) ? ch.visible : null;
    if (chWas !== null) ch.visible = false;
    const rows = {};
    try {
      for (const [rw, rh] of RES) {
        let last = null;
        const ms = [];
        for (let r = 0; r < REPS + 1; r++) {
          last = shot(pc.c2, rw, rh, RAW ? ID : SRGB);
          if (r > 0) ms.push(last.ms);
        }
        // the first pass is a warm-up (target upload, shader recompile on a new
        // viewport); the reported cost is the steady state
        const med = k => { const a = ms.map(m => m[k]).sort((x, y) => x - y); return a.length ? +a[(a.length / 2) | 0].toFixed(2) : null; };
        rows[rw + 'x' + rh] = { topSurface: last.topSurface, top2: last.top2,
                                entropy: last.entropy, bins: last.bins,
                                ms: { render: med('render'), read: med('read'), hist: med('hist'), all: med('all') } };
      }
      rows.region96 = region(pc.c2, 96, 54, RAW ? ID : SRGB);
      // the two poses under study: the ROUND establishing plate the first eye
      // sort was made on (fov 34 / 9 m) and the DECIDE command step the player
      // dwells in (fov 27 / 11 m), which the later two sorts were made on.
      const LUT = RAW ? ID : SRGB;
      const pRound = poseOf(st, BattleWorld.CAM.fov.rest, 9.0);
      const pDec = poseOf(st, 27, 11.03);
      for (const [k, pz, s] of [['ss2.round', pRound, 2], ['ss4.round', pRound, 4],
                                ['ss4.decide', pDec, 4]]) {
        shotSS(pz.c2, 1280, 720, s, LUT);                 // warm
        rows[k] = shotSS(pz.c2, 1280, 720, s, LUT);
      }
      rows['off.decide'] = shot(pDec.c2, 320, 180, LUT);
      shotCanvas(pRound);                                  // warm
      rows['cvs.round'] = shotCanvas(pRound);
      shotCanvas(pDec);
      rows['cvs.decide'] = shotCanvas(pDec);
    } finally {
      if (chWas !== null) ch.visible = chWas;
    }
    out.push({ id: s.id, ok: true, zone: s.zone,
               at: { x: +pc.P.x.toFixed(3), y: +pc.P.y.toFixed(3), z: +pc.P.z.toFixed(3) },
               R: st.R, stageMs: +stageMs.toFixed(1), res: rows });
  }
  return { rows: out, three: THREE.REVISION };
})()`;

// ---- MODE: nb — IS THERE A BETTER SITE TO PREFER? -------------------------
// THE QUESTION THAT DECIDES WHETHER A FIX IS WORTH BUILDING, and it is not
// "does the axis separate". The ladder's incumbent is its FIRST acceptance in
// ring order; a quality term can only help if the candidates it can already
// reach score better. This enumerates exactly the candidate set the shipped
// search collects (the first accepting ring plus PLACE.extraRings more), scores
// every one on the display-frame histogram, and reports the incumbent against
// the best. If the best is not better, the honest answer is to build nothing.
const nbDriver = (sites, yaw) => `(async () => {
  const S = ${JSON.stringify(sites)};
  const YAW = ${yaw};
  const TH = window.THREE;
  const slots = BattleWorld.slotsFor([{id:'vesper'},{id:'maren'}], [{id:'m0'},{id:'m1'}]);
  const RELOC = BattleWorld.RELOC, PLACE = BattleWorld.PLACE;
  const c2d = document.createElement('canvas'); c2d.width = 320; c2d.height = 180;
  const g2d = c2d.getContext('2d', { willReadFrequently: true });
  function histOfCanvas() {
    const src = document.querySelector('canvas');
    g2d.drawImage(src, 0, 0, 320, 180);
    const d = g2d.getImageData(0, 0, 320, 180).data;
    const H = new Float64Array(216); const n = 320 * 180;
    for (let p = 0, i = 0; p < n; p++, i += 4)
      H[(Math.min(5, d[i] * 6 / 256 | 0) * 36) + (Math.min(5, d[i+1] * 6 / 256 | 0) * 6) + Math.min(5, d[i+2] * 6 / 256 | 0)]++;
    let top = 0, ent = 0, nz = 0;
    for (let k = 0; k < 216; k++) { const h = H[k]; if (h > top) top = h; if (h > 0) { const q = h / n; ent -= q * Math.log2(q); nz++; } }
    return { topSurface: +(top / n).toFixed(4), entropy: +ent.toFixed(3), bins: nz };
  }
  function scorePose(plan, at, fov, D) {
    const b = plan.basis, P = at || { x: b.centre[0], y: b.centre[1], z: b.centre[2] };
    const pitch = (b.pitch == null ? BattleWorld.CFG.cam.pitch : b.pitch);
    const eye = new TH.Vector3(P.x + Math.cos(b.yaw) * Math.cos(pitch) * D,
                               P.y + 1 + Math.sin(pitch) * D,
                               P.z + Math.sin(b.yaw) * Math.cos(pitch) * D);
    const sv = { p: cam.position.clone(), q: cam.quaternion.clone(), fov: cam.fov };
    const t0 = performance.now();
    cam.position.copy(eye); cam.up.set(0,1,0); cam.lookAt(P.x, P.y + 1, P.z);
    cam.fov = fov; cam.updateProjectionMatrix(); cam.updateMatrixWorld();
    try { window.renderFrame(); } catch (e) {}
    cam.position.copy(sv.p); cam.quaternion.copy(sv.q); cam.fov = sv.fov;
    cam.updateProjectionMatrix(); cam.updateMatrixWorld();
    const h = histOfCanvas();
    h.ms = +(performance.now() - t0).toFixed(2);
    return h;
  }
  const out = [];
  for (const s of S) {
    const f0 = SIM.floors(s.px, s.pz);
    SIM.tp(s.px, s.pz, f0.length ? f0[0] : null); SIM.tick(3);
    window.ORBIT.yaw = YAW;
    const P0 = SIM.pos();
    const chWas = (typeof ch !== 'undefined' && ch) ? ch.visible : null;
    if (chWas !== null) ch.visible = false;
    const cands = [];
    let firstRing = -1;
    try {
      for (let ri = 0; ri < RELOC.rings.length; ri++) {
        if (firstRing >= 0 && ri > firstRing + PLACE.extraRings) break;
        const ring = RELOC.rings[ri];
        for (let a = 0; a < ring.n; a++) {
          const th = ring.ph + a * Math.PI * 2 / ring.n;
          let at = { x: P0.x, y: P0.y, z: P0.z };
          if (ring.R !== 0) {
            const x = P0.x + Math.cos(th) * ring.R, z = P0.z + Math.sin(th) * ring.R;
            const ff = (SIM.floors(x, z) || []).filter(v => isFinite(v));
            if (!ff.length) continue;
            let y = ff[0];
            for (const v of ff) if (Math.abs(v - P0.y) < Math.abs(y - P0.y)) y = v;
            if (Math.abs(y - P0.y) > RELOC.maxRise) continue;
            if (SIM.blocked(x, z, y)) continue;
            at = { x: x, y: y, z: z };
          }
          const viable = BattleWorld.screenYaws({ slots: slots, at: at });
          if (!viable.length) continue;
          const plan = BattleWorld.solveArena({ slots: slots, at: at, yaws: viable });
          if (!plan || !plan.ok) continue;
          if (firstRing < 0) firstRing = ri;
          const sc = scorePose(plan, at, BattleWorld.CAM.fov.rest, 9.0);
          cands.push({ R: ring.R, a: a, x: +at.x.toFixed(2), z: +at.z.toFixed(2),
                       lit: BattleWorld.sunLit(plan),
                       topSurface: sc.topSurface, entropy: sc.entropy, bins: sc.bins, ms: sc.ms });
        }
      }
    } finally { if (chWas !== null) ch.visible = chWas; }
    out.push({ id: s.id, zone: s.zone, n: cands.length, cands: cands });
  }
  return { rows: out };
})()`;

// ---- MODE: cost — WHAT DOES THE LADDER COST WITH AND WITHOUT ITS SHORT-CUTS
// The sun refusal's two short-circuits stop the candidate walk at 41 of 62
// cells, so a term that has to CHOOSE among candidates is inert wherever they
// fire. This prices the walk both ways at every census cell, with ORBIT.yaw
// pinned, so the design choice is made on a number.
const costDriver = (sites, yaw) => `(async () => {
  const S = ${JSON.stringify(sites)};
  const slots = BattleWorld.slotsFor([{id:'vesper'},{id:'maren'}], [{id:'m0'},{id:'m1'}]);
  const out = [];
  for (const s of S) {
    const f = SIM.floors(s.px, s.pz);
    SIM.tp(s.px, s.pz, f.length ? f[0] : null); SIM.tick(3);
    const row = { id: s.id };
    for (const fast of [true, false]) {
      BattleWorld.PLACE.fastPath = fast;
      window.ORBIT.yaw = ${yaw};
      const t0 = performance.now();
      const st = BattleWorld.stage(slots);
      row[fast ? 'fast' : 'full'] = { ms: +(performance.now() - t0).toFixed(1),
        choices: st && st.quality ? st.quality.choices : null,
        x: st && st.at ? +st.at.x.toFixed(3) : null, z: st && st.at ? +st.at.z.toFixed(3) : null };
    }
    BattleWorld.PLACE.fastPath = true;
    row.same = !!(row.fast.x !== null && row.full.x !== null &&
                  Math.abs(row.fast.x - row.full.x) < 1e-6 && Math.abs(row.fast.z - row.full.z) < 1e-6);
    out.push(row);
  }
  return { rows: out };
})()`;

// ---- MODE: ab — WHAT THE TERM MOVES, IN ONE BUILD -------------------------
// Both arms in ONE page with ORBIT.yaw pinned before every call, because
// solveArena's yaw ladder is relative to the live camera heading and two
// separate runs of one cell are not comparable.
const abDriver = (sites, yaw) => `(async () => {
  const S = ${JSON.stringify(sites)};
  const slots = BattleWorld.slotsFor([{id:'vesper'},{id:'maren'}], [{id:'m0'},{id:'m1'}]);
  const out = [];
  for (const s of S) {
    const f = SIM.floors(s.px, s.pz);
    SIM.tp(s.px, s.pz, f.length ? f[0] : null); SIM.tick(3);
    const row = { id: s.id, zone: s.zone };
    for (const on of [false, true]) {
      BattleWorld.PLACE.surf = on;
      window.ORBIT.yaw = ${yaw};
      const t0 = performance.now();
      const st = BattleWorld.stage(slots);
      row[on ? 'on' : 'off'] = st && st.at
        ? { x: +st.at.x.toFixed(3), z: +st.at.z.toFixed(3), R: st.R,
            ms: +(performance.now() - t0).toFixed(1),
            q: st.quality || null }
        : null;
    }
    BattleWorld.PLACE.surf = true;
    const A = row.off, B = row.on;
    row.same = !!(A && B && Math.abs(A.x - B.x) < 1e-6 && Math.abs(A.z - B.z) < 1e-6);
    out.push(row);
  }
  return { rows: out };
})()`;

// ============================== plumbing ====================================
const sleep = ms => new Promise(r => setTimeout(r, ms));
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
    expression: expr, awaitPromise: true, returnByValue: true, userGesture: true, timeout: ms || 600000 });
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
  return { already: false, on: !!(window.BattleWorld && window.BattleWorld.on) };
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

// ============================== stats =======================================
// AUC and a three-pile separation, the same shape battle_place_stats.py reports
// so a number from this file is comparable with the board's own.
function auc(pos, neg) {
  let n = 0, w = 0;
  for (const a of pos) for (const b of neg) { n++; w += a > b ? 1 : a === b ? 0.5 : 0; }
  return n ? w / n : null;
}
function sep(vals, piles) {
  // "sep" on the board = balanced separation of good vs bad by the best split,
  // reported as (2*balAcc - 1) style; recompute the board's own quantity:
  // AUC of good-vs-bad mapped to |2*auc-1| so direction does not matter.
  const g = piles.good, b = piles.bad;
  const A = auc(g.map(i => vals[i]), b.map(i => vals[i]));
  if (A == null) return null;
  return { auc: +A.toFixed(3), sep: +Math.abs(2 * A - 1).toFixed(3) };
}
function spearman(a, b) {
  const rank = arr => {
    const idx = arr.map((v, i) => [v, i]).sort((x, y) => x[0] - y[0]);
    const r = new Array(arr.length);
    for (let i = 0; i < idx.length;) {
      let j = i; while (j + 1 < idx.length && idx[j + 1][0] === idx[i][0]) j++;
      const m = (i + j) / 2 + 1;
      for (let k = i; k <= j; k++) r[idx[k][1]] = m;
      i = j + 1;
    }
    return r;
  };
  const ra = rank(a), rb = rank(b), n = a.length;
  const ma = ra.reduce((s, v) => s + v, 0) / n, mb = rb.reduce((s, v) => s + v, 0) / n;
  let sa = 0, sb = 0, sab = 0;
  for (let i = 0; i < n; i++) { const x = ra[i] - ma, y = rb[i] - mb; sa += x * x; sb += y * y; sab += x * y; }
  return +(sab / Math.sqrt(sa * sb)).toFixed(3);
}

function statsMode() {
  const file = join(OUT, 'probe' + (TAG ? '-' + TAG : '') + '.json');
  const d = JSON.parse(readFileSync(file, 'utf8'));
  const C = census(), SO = sorts();
  const bySite = Object.fromEntries(C.sites.map(s => [s.id, s]));
  const rows = d.rows.filter(r => r.ok);
  const report = { file: file, n: rows.length, axes: {}, cost: {}, agree: {} };
  const keys = Object.keys(rows[0].res);
  const series = {};
  for (const k of keys) {
    if (rows[0].res[k].topSurface != null) {
      series['proxy.' + k + '.topSurface'] = rows.map(r => r.res[k].topSurface);
      series['proxy.' + k + '.entropy'] = rows.map(r => r.res[k].entropy);
    }
    if (rows[0].res[k].topRegion != null) series['proxy.' + k + '.topRegion'] = rows.map(r => r.res[k].topRegion);
  }
  series['offline.decide.topSurface'] = rows.map(r => bySite[r.id].surf.topSurface);
  series['offline.decide.entropy'] = rows.map(r => bySite[r.id].surf.entropy);

  for (const [name, sortMap] of Object.entries(SO)) {
    const piles = { good: [], acceptable: [], bad: [] };
    rows.forEach((r, i) => { const p = sortMap[r.id]; if (piles[p]) piles[p].push(i); });
    if (!piles.good.length || !piles.bad.length) continue;
    report.axes[name] = {};
    for (const [k, v] of Object.entries(series)) {
      const s = sep(v, piles);
      const mean = ids => +(ids.reduce((a, i) => a + v[i], 0) / ids.length).toFixed(4);
      report.axes[name][k] = Object.assign(s || {}, { good: mean(piles.good), acc: mean(piles.acceptable), bad: mean(piles.bad) });
    }
    report.axes[name].__piles = { good: piles.good.length, acceptable: piles.acceptable.length, bad: piles.bad.length };
  }
  // rank agreement with the offline number the sorts were separated by
  for (const k of Object.keys(series)) {
    if (k.startsWith('offline')) continue;
    report.agree[k] = { vsOfflineTop: spearman(series[k], series['offline.decide.topSurface']),
                        vsOfflineEnt: spearman(series[k], series['offline.decide.entropy']) };
  }
  for (const k of keys) {
    const num = typeof rows[0].res[k].ms === 'number';
    const all = rows.map(r => (num ? r.res[k].ms : r.res[k].ms.all)).sort((a, b) => a - b);
    const q = p => all[Math.min(all.length - 1, Math.floor(all.length * p))];
    report.cost[k] = { p50: q(0.5), p95: q(0.95), max: all[all.length - 1] };
    if (!num) {
      report.cost[k].render = +(rows.reduce((a, r) => a + r.res[k].ms.render, 0) / rows.length).toFixed(2);
      report.cost[k].read = +(rows.reduce((a, r) => a + r.res[k].ms.read, 0) / rows.length).toFixed(2);
      report.cost[k].hist = +(rows.reduce((a, r) => a + r.res[k].ms.hist, 0) / rows.length).toFixed(2);
    }
  }
  report.stageMs = (() => { const a = rows.map(r => r.stageMs).sort((x, y) => x - y);
    return { p50: a[(a.length / 2) | 0], p95: a[Math.floor(a.length * 0.95)], max: a[a.length - 1] }; })();
  const o = join(OUT, 'stats' + (TAG ? '-' + TAG : '') + '.json');
  writeFileSync(o, JSON.stringify(report, null, 1));
  console.log(JSON.stringify(report, null, 1));
  console.log('\nWROTE ' + o);
}

// ============================== main ========================================
if (MODE === 'stats') { statsMode(); process.exit(0); }

const CDP_PORT = await freePort();
const CHROME = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const PROFILE_PREFIX = 'battle-surface-';
sweepStaleProfiles(PROFILE_PREFIX);
const profile = join(process.env.TMPDIR || '/tmp', PROFILE_PREFIX + process.pid);
const URL = `http://localhost:${PORT}/play3d.html?scene=ow-valley&rt=1&nomusic=1&arena=world`;
const chrome = spawn(CHROME, [
  `--remote-debugging-port=${CDP_PORT}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--disable-extensions',
  '--autoplay-policy=no-user-gesture-required',
  '--hide-scrollbars', '--force-device-scale-factor=1', '--window-size=1600,900',
  ...(HEAD ? [] : ['--headless=new']),
  URL,
], { stdio: 'ignore' });
let closing = false;
const kill = () => { if (closing) return; closing = true; try { chrome.kill('SIGKILL'); } catch (e) { } try { killOrphans(profile); } catch (e) { } };
process.on('exit', kill);
process.on('SIGINT', () => { kill(); process.exit(130); });

// A DESTROYED EXECUTION CONTEXT IS A STALE TARGET — the page navigates once
// after the first match, so the ws url is re-found rather than waited on.
async function findGame() {
  for (let i = 0; i < 120; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${CDP_PORT}/json/list`);
      const list = await r.json();
      const p = list.find(t => t.type === 'page' && /\/play3?d?\.html/.test(t.url || ''));
      if (p && p.webSocketDebuggerUrl) return p.webSocketDebuggerUrl;
    } catch (e) { }
    await sleep(500);
  }
  throw new Error('CDP never exposed the game page');
}

const wsUrl = await findGame();
let cdp = await connect(wsUrl);
await cdp.send('Runtime.enable');
const ready = await ev(cdp, READY);
if (!ready || !ready.ready) { console.error('page never became ready', ready); kill(); process.exit(1); }
console.log('ready', JSON.stringify(ready));
const inj = await ev(cdp, INJECT);
console.log('battle_world', JSON.stringify(inj));

const C = census();
const sites = C.sites.slice(0, LIMIT);
console.log(`${MODE}: ${sites.length} sites, yaw pinned ${C.yaw}, srgb=${RAW ? 'OFF (raw linear)' : 'on'}`);
const t0 = Date.now();
const driver = MODE === 'nb' ? nbDriver(sites, C.yaw)
              : MODE === 'cost' ? costDriver(sites, C.yaw)
              : MODE === 'ab' ? abDriver(sites, C.yaw)
              : probeDriver(sites, C.yaw, { reps: REPS, raw: RAW });
const res = await ev(cdp, driver, 900000);
const secs = Math.round((Date.now() - t0) / 1000);
const outFile = join(OUT, (MODE === 'nb' ? 'nb' : MODE === 'cost' ? 'cost' : MODE === 'ab' ? 'ab' : 'probe') + (TAG ? '-' + TAG : '') + '.json');
writeFileSync(outFile, JSON.stringify({ meta: { when: new Date().toISOString(), yaw: C.yaw, raw: RAW, reps: REPS, three: res.three, n: res.rows.length, secs }, rows: res.rows }, null, 1));
console.log(`WROTE ${outFile}  (${res.rows.filter(r => r.ok).length}/${res.rows.length} ok, ${secs}s)`);
cdp.close(); kill();
process.exit(0);
