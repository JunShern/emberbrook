/* camfit.js — WHAT DOES THE OVERWORLD CAMERA ACTUALLY SEE.  Injected into the live
 * ow-valley render over CDP (tools/ow_probe/ow_multi.mjs --inject), never shipped.
 *
 *   OWFIT.grid()            build/refresh the terrain height cache around the player
 *   OWFIT.measure(opts)     -> the numbers for the CURRENT window.ORBIT
 *
 * WHY IT EXISTS.  Bet 5 is a camera composition pass under ONE hard user constraint —
 * "so long as the user continues to have a wide field of view of the space around
 * them" — and a constraint you cannot measure is a constraint you will violate by
 * eye.  Three numbers, three different instruments, on purpose:
 *
 *  1. THE FRAME CENSUS is PIXELS.  Every mesh is repainted a flat identifying colour
 *     (MeshBasicMaterial, toneMapped:false) and the framebuffer is counted, so
 *     sky / ridge / ground / water / canopy / building are read off the picture the
 *     player gets rather than off a scene-graph guess.  Alpha-cut foliage keeps its
 *     alphaTest through a one-line map_fragment swap: paint a leaf card as an opaque
 *     quad and you re-run the R7 g-buffer bug inside your own instrument.
 *     THE PROBE RENDERS WITH toneMapping OFF AND outputColorSpace = NoColorSpace and
 *     puts both back.  Say which space the bytes are in (CLAUDE.md): a magenta that
 *     goes through the tone curve comes back with a green channel and counts as
 *     nothing, which is the exact bug SIM.paint's own comment records.
 *
 *  2. THE HORIZON is ANALYTIC.  The follow camera is a 42 deg vertical fov, so the
 *     horizon sits at ndcY = tan(down-angle)/tan(21 deg) — off the top of the frame
 *     for any down-angle >= 21 deg, at any aim.  Reported as a signed number, not a
 *     boolean, because "1.3 degrees short" and "12 degrees short" are different
 *     problems and a boolean calls them both false.
 *
 *  3. GROUND COVERAGE is GEOMETRY.  36 bearings from the PLAYER, marched outward in
 *     2 m steps: a sample counts when it is inside the frustum AND the terrain does
 *     not stand between it and the camera.  coverR[b] is the CONTIGUOUS radius from
 *     the player, so a strip of ground visible past a ridge does not get credited as
 *     "the player can see the space around them".  Heights come from the engine's own
 *     floors() (collide list, up-facing hits only — vegetation is not collision here,
 *     which is what keeps a canopy out of the terrain profile), cached on a 4 m grid
 *     per station because it is the same terrain for every candidate at that station.
 *
 * The census and the coverage measure DIFFERENT things and both are needed: canopy
 * that swallows the frame shows up as veg% climbing while coverR collapses, and a
 * camera that has simply been aimed at the sky shows up as sky% climbing while coverR
 * collapses.  One number cannot tell those apart.
 */
window.OWFIT = (function () {
  const T = THREE;
  const DEG = Math.PI / 180;

  // ---- class map: every mesh name in ow-valley falls in exactly one bucket -----
  const CLASSES = [
    ['sky',    /^__owsky$/,                                  0xff0000],
    ['ridge',  /^__owridge/,                                 0x00ff00],
    ['ground', /^(ground_valley|walk_|edge_skirt)/,          0x0000ff],
    ['water',  /^water_/,                                    0xffff00],
    ['veg',    /^(veg_|tree_field_trunks)/,                  0xff00ff],
    ['build',  /^(emberbrook_|dellhollow_|oldgate_|props_|boat_|portal_)/, 0x00ffff],
  ];
  const OTHER = 0x808080;                       // character, contact shadow, tripo nodes
  function classOf(name) {
    for (const c of CLASSES) if (c[1].test(name || '')) return c;
    return null;
  }

  // ---- 1. THE FRAME CENSUS ----------------------------------------------------
  const _cache = new WeakMap();
  function probeMat(orig, hex) {
    const key = hex + '|' + (orig.map ? orig.map.uuid : '-') + '|' + (orig.alphaTest || 0);
    let byMat = _cache.get(orig);
    if (!byMat) { byMat = {}; _cache.set(orig, byMat); }
    if (byMat[key]) return byMat[key];
    const m = new T.MeshBasicMaterial({
      color: hex, toneMapped: false, fog: false,
      side: orig.side, depthTest: orig.depthTest, depthWrite: true,
      transparent: false, opacity: 1,
    });
    if (orig.map && orig.alphaTest > 0) {
      m.map = orig.map; m.alphaTest = orig.alphaTest;
      // KEEP THE CUT, DROP THE COLOUR.  map_fragment normally multiplies diffuseColor
      // by the texel; we want only its alpha so alphatest_fragment still discards the
      // gaps in a leaf card while the rgb stays the flat identifying colour.
      m.onBeforeCompile = (sh) => {
        sh.fragmentShader = sh.fragmentShader.replace(
          '#include <map_fragment>', 'diffuseColor.a *= texture2D( map, vMapUv ).a;');
      };
      m.customProgramCacheKey = () => 'owfit-alphaonly';
    }
    byMat[key] = m;
    return m;
  }

  function census() {
    const saved = [];
    scene.traverse((o) => {
      if (!(o.isMesh || o.isInstancedMesh) || !o.visible) return;
      const c = classOf(o.name);
      saved.push([o, o.material]);
      o.material = probeMat(o.material, c ? c[2] : OTHER);
    });
    const tm = R.toneMapping, cs = R.outputColorSpace;
    const gl = R.getContext();
    const w = gl.drawingBufferWidth, h = gl.drawingBufferHeight;
    const px = new Uint8Array(w * h * 4);
    try {
      // LinearSRGB, not NoColorSpace: the working space IS linear-sRGB, so this is the
      // no-op output and the bytes come back as the hex that was authored.  r185 THROWS
      // on NoColorSpace as an OUTPUT space ("cannot read fromXYZ") — and the first
      // version of this probe threw INSIDE the render with no finally, which left the
      // renderer in that state and made every later frame on the page fail the same way.
      // A probe that can poison the thing it measures must restore in a finally.
      R.toneMapping = T.NoToneMapping; R.outputColorSpace = T.LinearSRGBColorSpace;
      R.render(scene, cam);
      gl.readPixels(0, 0, w, h, gl.RGBA, gl.UNSIGNED_BYTE, px);
    } finally {
      R.toneMapping = tm; R.outputColorSpace = cs;
      for (const [o, m] of saved) o.material = m;
    }

    const out = { _w: w, _h: h, _px: w * h };
    for (const c of CLASSES) out[c[0]] = 0;
    out.other = 0; out.clear = 0;
    for (let i = 0; i < w * h; i++) {
      const r = px[i * 4] > 128, g = px[i * 4 + 1] > 128, b = px[i * 4 + 2] > 128;
      const lo = px[i * 4] < 40 && px[i * 4 + 1] < 40 && px[i * 4 + 2] < 40;
      if (lo) { out.clear++; continue; }
      const k = (r ? 4 : 0) | (g ? 2 : 0) | (b ? 1 : 0);
      if (k === 4) out.sky++;
      else if (k === 2) out.ridge++;
      else if (k === 1) out.ground++;
      else if (k === 6) out.water++;
      else if (k === 5) out.veg++;
      else if (k === 3) out.build++;
      else out.other++;
    }
    const n = w * h, pc = (v) => +(100 * v / n).toFixed(2);
    return {
      skyPct: pc(out.sky), ridgePct: pc(out.ridge), groundPct: pc(out.ground),
      waterPct: pc(out.water), vegPct: pc(out.veg), buildPct: pc(out.build),
      otherPct: pc(out.other), clearPct: pc(out.clear),
      // "air at distance" — what the references get their cool and their depth from
      airPct: +(pc(out.sky) + pc(out.ridge)).toFixed(2),
      res: [w, h],
    };
  }

  // ---- 2. THE HORIZON ---------------------------------------------------------
  function horizon() {
    const f = new T.Vector3(0, 0, -1).applyQuaternion(cam.quaternion).normalize();
    const down = Math.asin(-f.y);                       // camera axis below horizontal
    const half = (cam.fov / 2) * DEG;
    const ndcY = Math.tan(down) / Math.tan(half);       // horizon's ndc y at frame centre
    return {
      downDeg: +(down / DEG).toFixed(2),
      horizonNdcY: +ndcY.toFixed(3),
      // fraction of frame HEIGHT that sits above the horizon line (0 = no horizon)
      aboveHorizonPct: +(100 * Math.max(0, Math.min(1, (1 - ndcY) / 2))).toFixed(2),
      // how many degrees the horizon is above the top edge (negative = in frame)
      horizonMissDeg: +((down - half) / DEG).toFixed(2),
      topEdgeDeg: +((down - half) / DEG).toFixed(2),
      botEdgeDeg: +((down + half) / DEG).toFixed(2),
    };
  }

  // ---- 3. GROUND COVERAGE -----------------------------------------------------
  // 4 m lattice of terrain tops, rebuilt when the player moves.  floors() is a real
  // raycast against the collide list; 86x86 of them is ~1 s and it is the same terrain
  // for every candidate at a station, so it is paid once.
  const GSTEP = 4, GHALF = 172;
  let G = null;
  function gridBuild() {
    const p = SIM.pos(), n = Math.round((2 * GHALF) / GSTEP) + 1;
    const h = new Float32Array(n * n);
    const x0 = p.x - GHALF, z0 = p.z - GHALF;
    for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) {
      const fs = SIM.floors(x0 + i * GSTEP, z0 + j * GSTEP);
      h[j * n + i] = (fs && fs.length) ? Math.max.apply(null, fs) : NaN;
    }
    G = { x0, z0, n, h, at: [p.x, p.z] };
    return { cells: n * n, origin: [+x0.toFixed(1), +z0.toFixed(1)], step: GSTEP };
  }
  function gridOk() {
    const p = SIM.pos();
    return G && Math.abs(G.at[0] - p.x) < 0.5 && Math.abs(G.at[1] - p.z) < 0.5;
  }
  function hAt(x, z) {                                   // bilinear, NaN outside/holes
    if (!G) return NaN;
    const fx = (x - G.x0) / GSTEP, fz = (z - G.z0) / GSTEP;
    const i = Math.floor(fx), j = Math.floor(fz);
    if (i < 0 || j < 0 || i >= G.n - 1 || j >= G.n - 1) return NaN;
    const tx = fx - i, tz = fz - j;
    const a = G.h[j * G.n + i], b = G.h[j * G.n + i + 1];
    const c = G.h[(j + 1) * G.n + i], d = G.h[(j + 1) * G.n + i + 1];
    if (!(a === a) || !(b === b) || !(c === c) || !(d === d)) return NaN;
    return (a * (1 - tx) + b * tx) * (1 - tz) + (c * (1 - tx) + d * tx) * tz;
  }

  const _v = new T.Vector3();
  function inFrame(x, y, z) {
    _v.set(x, y, z).project(cam);
    return Math.abs(_v.x) <= 1 && Math.abs(_v.y) <= 1 && _v.z > -1 && _v.z < 1;
  }
  // terrain line of sight, sampled on the cached profile.  CLEAR is the tolerance a
  // 4 m lattice earns: a bilinear sample of a ridge crest under-reads the crest.
  const LOS_STEP = 3, CLEAR = 0.6;
  function visible(x, y, z) {
    const c = cam.position, dx = x - c.x, dy = y - c.y, dz = z - c.z;
    const L = Math.hypot(dx, dy, dz), n = Math.max(2, Math.round(L / LOS_STEP));
    for (let k = 1; k < n; k++) {
      const t = k / n, sx = c.x + dx * t, sy = c.y + dy * t, sz = c.z + dz * t;
      const g = hAt(sx, sz);
      if (g === g && g > sy + CLEAR) return false;
    }
    return true;
  }

  const NB = 36, RSTEP = 2, RMAX = 160;
  function coverage() {
    if (!gridOk()) gridBuild();
    const p = SIM.pos();
    const cover = new Array(NB).fill(0);
    for (let b = 0; b < NB; b++) {
      const th = (b / NB) * 2 * Math.PI, cs = Math.cos(th), sn = Math.sin(th);
      for (let r = RSTEP; r <= RMAX; r += RSTEP) {
        const x = p.x + cs * r, z = p.z + sn * r, y = hAt(x, z);
        if (!(y === y)) break;
        if (!inFrame(x, y + 0.15, z) || !visible(x, y + 0.15, z)) break;
        cover[b] = r;
      }
    }
    // the camera's own bearing, so "behind" and "ahead" are named not guessed
    const fwd = new T.Vector3(0, 0, -1).applyQuaternion(cam.quaternion);
    const camBear = Math.atan2(fwd.z, fwd.x);
    const bi = (a) => ((Math.round((a / (2 * Math.PI)) * NB) % NB) + NB) % NB;
    const sorted = cover.slice().sort((a, b) => a - b);
    const area = cover.reduce((s, r) => s + 0.5 * r * r * (2 * Math.PI / NB), 0);
    return {
      coverMin: sorted[0], coverP25: sorted[Math.floor(NB * 0.25)],
      coverMed: sorted[Math.floor(NB * 0.5)], coverMax: sorted[NB - 1],
      coverMean: +(cover.reduce((a, b) => a + b, 0) / NB).toFixed(1),
      // m2 of terrain that is BOTH in frame and unoccluded, contiguous from the player
      areaM2: Math.round(area),
      ahead: cover[bi(camBear)],
      behind: cover[bi(camBear + Math.PI)],
      left: cover[bi(camBear + Math.PI / 2)], right: cover[bi(camBear - Math.PI / 2)],
      _cover: cover,
    };
  }

  // ---- where the player sits in the frame -------------------------------------
  // The composition constraint the geometry note in play3d.html states as a formula
  // (0.5 + 0.5*tan(tilt)/tan(21 deg)) — MEASURED instead, because ORBIT.panY moves
  // the body down the frame without touching the camera axis and the formula has no
  // term for it.  0 = top of frame, 1 = bottom.
  function player() {
    const p = SIM.pos();
    const feet = _v.set(p.x, p.y + 0.05, p.z).project(cam).clone();
    const head = _v.set(p.x, p.y + 1.5, p.z).project(cam).clone();
    return {
      playerFrameY: +((1 - feet.y) / 2).toFixed(3),
      playerHeadY: +((1 - head.y) / 2).toFixed(3),
      playerPx: +(((head.y - feet.y) / 2) * (R.getContext().drawingBufferHeight)).toFixed(0),
      playerInFrame: Math.abs(feet.x) <= 1 && Math.abs(feet.y) <= 1 && Math.abs(head.y) <= 1,
    };
  }

  // ---- the whole card ---------------------------------------------------------
  function measure(opt) {
    opt = opt || {};
    const O = window.ORBIT, p = SIM.pos();
    const t0 = performance.now();
    const cv = coverage(), hz = horizon(), pl = player();
    const cs = opt.census === false ? null : census();
    if (!opt.cover) delete cv._cover;
    return Object.assign({
      pos: [+p.x.toFixed(2), +p.z.toFixed(2)],
      pitch: +O.pitch.toFixed(3), tilt: +(O.tilt || 0).toFixed(3),
      dist: O.dist, panY: +(O.panY || 0).toFixed(2),
      camY: +cam.position.y.toFixed(2),
      // null, never a number, when the boom hangs over a hole in the profile — a
      // "51 m of clearance" that is really `NaN || 0` is the exact shape of a gate
      // that cannot fail.
      camAboveGround: (function () { const g = hAt(cam.position.x, cam.position.z);
        return (g === g) ? +(cam.position.y - g).toFixed(2) : null; })(),
      camAbovePlayer: +(cam.position.y - p.y).toFixed(2),
      ms: Math.round(performance.now() - t0),
    }, hz, pl, cv, cs || {});
  }

  // THE CAMERA IS PLACED IN frame(), NOT IN SIM.tick().  play3d's boom lives in the
  // rAF frame callback, so setting ORBIT and calling SIM.tick() measures the PREVIOUS
  // camera — an instrument that reports the frame before the change is worse than none.
  // Every candidate therefore waits two real animation frames before it is measured,
  // which makes the sweep asynchronous; ow_multi's `settle` is what gives it time.
  const raf = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  async function at(pitch, tilt, panY, opt) {
    const O = window.ORBIT;
    O.pitch = pitch; O.tilt = tilt; O.panX = 0; O.panY = panY || 0; O.panZ = 0;
    await raf();
    return measure(opt);
  }
  async function sweep(cands, opt) {
    if (!gridOk()) gridBuild();
    const out = [];
    for (const c of cands) out.push(await at(c[0], c[1], c[2], opt));
    return out;
  }

  return { measure, at, sweep, census, horizon, coverage, player, grid: gridBuild, classOf, CLASSES };
})();
