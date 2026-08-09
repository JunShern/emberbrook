// ============================ THE MEASUREMENT LIBRARY ======================
// EXTRACTED SO TWO INSTRUMENTS CAN ASK THE SAME QUESTIONS OF TWO DIFFERENT
// FRAMES. tools/battle_place.mjs measures the `round` establishing plate with
// it; tools/battle_decide.mjs measures the `decide` command-step frame — the
// one the player actually dwells in — and a comparison between two sorts is
// only worth anything if the ruler is literally the same object. Moved
// verbatim from battle_place.mjs (2026-08-09, decide-census lane); nothing in
// it changed.
//
// ============================ THE MEASUREMENT LIBRARY ======================
// Installed once into the page, then called per site. Everything here reads
// either the FINAL DISPLAY FRAME (through the stage's own snapshot path) or the
// ENGINE (SIM.ground / a Raycaster against the drawn scene) — never a file and
// never an offscreen target.
export const LIB = `(() => {
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
