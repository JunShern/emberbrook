/* land.js — OVERWORLD LANDSCAPE QUALITY: three candidate treatments aimed at the
 * WHOLE LANDSCAPE, injected into the LIVE ow-valley runtime over CDP.
 *
 * NOTHING HERE SHIPS. It is a probe; the bundle, the map files and play3d.html
 * are not modified by anything in this file.
 *
 * WHY THIS LANE EXISTS AT ALL. Three forest candidates (F1/F2/F3) were rejected:
 *   "go back to the FFIX reimagined reference images ... those images should give
 *    you a sense of the level of polish that we need to aspire to."
 * The references contain NO FOREST. So the target is not a tree-species problem.
 * It is whole-landscape: light, air, ground detail, and blended transitions.
 *
 * THE MEASUREMENT THAT SET THESE THREE (tools/ow_probe/imgstat.py, crops that
 * exclude every HUD pixel; L = Rec.709 luma of the sRGB frame):
 *
 *      frame                L05    L50    L95   Lrange  b-r(dark) b-r(lit)  detail
 *      REF1 Dali day       0.298  0.541  0.799  0.501    +0.090   -0.040    48.1
 *      REF3 windmill day   0.270  0.477  0.696  0.425    +0.033   +0.110    29.7
 *      REF2 Treno NIGHT    0.093  0.245  0.423  0.330    +0.234   +0.151    45.9
 *      ours gate           0.097  0.366  0.539  0.442    -0.098   -0.366    33.9
 *      ours shelf b12      0.085  0.199  0.399  0.314    -0.072   -0.248    23.0
 *      ours shelf b40      0.096  0.227  0.398  0.302    -0.064   -0.257    14.6
 *      ours Dellhollow     0.093  0.222  0.473  0.380    -0.055   -0.264    17.5
 *
 *   1. THREE OF OUR FOUR DAYLIGHT CAMERAS ARE DARKER THAN THE REFERENCE'S NIGHT
 *      PLATE (L50 0.199/0.227/0.222 vs Treno's 0.245), and NOTHING in any of our
 *      frames is brighter than 0.54 where the references put 5 % of the frame
 *      above 0.70. There is no highlight in the corridor at all.
 *   2. b-r IS NEGATIVE IN BOTH THE DARK AND THE LIGHT QUARTILE of every frame:
 *      nothing in the corridor is cool. Ref 1's shadows are +0.090 — actually
 *      blue. A shadow that is only "the same colour, darker" is a multiply layer,
 *      and that is the 2003 tell the light lane was chasing.
 *   3. PIXEL-SCALE DETAIL IS A THIRD OF THE REFERENCE'S in the gorge (14.6 vs
 *      29.7-48.1 mean |laplacian| x1000). That is the "painted plane" complaint
 *      as a number.
 *
 * AND THE ALBEDO SAYS THE SAME THING (COLOR_0 means read out of the live bundle):
 *      ground_valley_1  grass   L 0.383   rgb 0.356 0.403 0.260   (G-R = +0.047)
 *      ground_valley_3  rock    L 0.502   rgb 0.519 0.505 0.420
 *   THE GRASS IS DARKER THAN THE ROCK. The largest bright surface in the corridor
 *   is a brown cliff; in every reference the largest bright surface is lit ground.
 *
 * INHERITED TRAPS, ALL PAID FOR BY EARLIER LANES:
 *   * three r128 has NO input colour management and play3d sets outputEncoding =
 *     sRGBEncoding: a hex handed to a material must be convertSRGBToLinear'd or it
 *     renders chalk. Values read back OUT of COLOR_0 are ALREADY linear.
 *   * SIM.tp(x,z) raycasts from the CURRENT P.y — ow_multi's __tp fixes it.
 *   * r128 does not count toneMapping among the reasons to rebuild a program, so
 *     changing R.toneMapping without material.needsUpdate changes nothing.
 *   * the vegetation and terrain meshes are UNINDEXED.
 *   * NO INSTRUMENT CAN DERIVE A ROAD HEADING from the RLE-ordered zone raster
 *     (four tried). Nothing here needs one: the road is used as a MASK, never as
 *     a direction.
 */
window.OWL = (function () {
  const R3 = THREE;
  let G = null;
  const HIDDEN = [];
  const COLSAVE = new Map();
  let LSAVE = null, FSAVE = null, RSAVE = null;
  const ADDED = [];

  const C = (hex) => new R3.Color(hex).convertSRGBToLinear();
  function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0;
    let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  // deterministic value noise on a lattice — no random() anywhere in a builder
  function h2(x, y, s) { let n = Math.sin(x * 127.1 + y * 311.7 + s * 74.7) * 43758.5453; return n - Math.floor(n); }
  function vnoise(x, y, cell, s) {
    const fx = x / cell, fy = y / cell, ix = Math.floor(fx), iy = Math.floor(fy);
    const tx = fx - ix, ty = fy - iy, sx = tx * tx * (3 - 2 * tx), sy = ty * ty * (3 - 2 * ty);
    const a = h2(ix, iy, s), b = h2(ix + 1, iy, s), c = h2(ix, iy + 1, s), d = h2(ix + 1, iy + 1, s);
    return (a * (1 - sx) + b * sx) * (1 - sy) + (c * (1 - sx) + d * sx) * sy;
  }

  function find(name) { let hit = null; scene.traverse(o => { if (o.isMesh && o.name === name) hit = o; }); return hit; }
  function group() { if (!G) { G = new R3.Group(); G.name = '__owl'; scene.add(G); } return G; }
  const triCount = g => (g.index ? g.index.count : g.attributes.position.count) / 3;

  // ---- the shipped materials, reused -----------------------------------------
  // A flat untextured colour beside a mapped crag reads as pale plastic at ANY
  // hex (paid for in the first probe). Clone a SHIPPED material so the map comes
  // with it; carry the candidate's colour on instanceColor.
  function shipped(name) { let hit = null; scene.traverse(o => { if (!o.isMesh) return;
    for (const m of (Array.isArray(o.material) ? o.material : [o.material]))
      if (m && m.name === name) hit = m; }); return hit; }
  function clonedFlat(name) { const s = shipped(name); if (!s) return null;
    const m = s.clone(); m.name = name + '__owl'; m.vertexColors = true; return m; }

  // ===========================================================================
  // THE ZONE RASTER  (a MASK, never a direction)
  // ===========================================================================
  let ZG = null;
  function zones() {
    if (ZG) return ZG;
    const x = new XMLHttpRequest();                 // sync on purpose: the CDP
    x.open('GET', 'assets/scenes/ow-valley/zones.json', false);  // inject is one
    x.send(null);                                   // synchronous evaluate
    const j = JSON.parse(x.responseText);
    const g = new Uint8Array(j.cols * j.rows);
    for (let r = 0; r < j.rows; r++) {
      const row = j.rows_rle[r]; let c = 0;
      for (let k = 0; k < row.length; k += 2) { const t = row[k], n = row[k + 1];
        for (let i = 0; i < n; i++) g[r * j.cols + c++] = t; }
    }
    ZG = { cell: j.cell, ox: j.origin[0], oz: j.origin[1], cols: j.cols, rows: j.rows,
           types: j.types, g,
           at(x, z) { const c = Math.floor((x - this.ox) / this.cell), r = Math.floor((z - this.oz) / this.cell);
             if (c < 0 || r < 0 || c >= this.cols || r >= this.rows) return -1;
             return this.g[r * this.cols + c]; } };
    return ZG;
  }
  const Z_MEADOW = 0, Z_FOREST = 1, Z_CRAG = 2, Z_ROAD = 3, Z_WATER = 4;

  // ===========================================================================
  // THE TERRAIN SAMPLER — a 2D triangle hash over the three ground batches.
  // ===========================================================================
  // Built rather than raycast because the terrain is a HEIGHTFIELD: one y per xz.
  // It answers TWO questions in one lookup, and the second is the one the
  // reference frames are about: what is the SURFACE at this point (grass / dry /
  // rock), so a "transition" can be found without any zone at all. The hard
  // grass->sand cut at the Emberbrook gate is a MESH boundary, not a zone
  // boundary — the zone raster calls both sides `meadow` and cannot see it.
  const GROUND = [['ground_valley_1', 1], ['ground_valley_2', 2], ['ground_valley_3', 3]];
  let TS = null;
  function terrain() {
    if (TS) return TS;
    const CELL = 4.0;
    let minx = 1e9, minz = 1e9, maxx = -1e9, maxz = -1e9;
    const tris = [];   // [ax,ay,az,bx,by,bz,cx,cy,cz, kind]
    for (const [nm, kind] of GROUND) {
      const o = find(nm); if (!o) continue;
      o.updateMatrixWorld(true);
      const g = o.geometry, P = g.attributes.position, I = g.index;
      const n = I ? I.count : P.count, v = new R3.Vector3(), M = o.matrixWorld;
      for (let k = 0; k < n; k += 3) {
        const t = [];
        for (let j = 0; j < 3; j++) { const i = I ? I.getX(k + j) : k + j;
          v.fromBufferAttribute(P, i).applyMatrix4(M); t.push(v.x, v.y, v.z);
          if (v.x < minx) minx = v.x; if (v.x > maxx) maxx = v.x;
          if (v.z < minz) minz = v.z; if (v.z > maxz) maxz = v.z; }
        t.push(kind); tris.push(t);
      }
    }
    const cols = Math.ceil((maxx - minx) / CELL) + 1, rows = Math.ceil((maxz - minz) / CELL) + 1;
    const bins = new Array(cols * rows); for (let i = 0; i < bins.length; i++) bins[i] = null;
    for (let i = 0; i < tris.length; i++) {
      const t = tris[i];
      const c0 = Math.floor((Math.min(t[0], t[3], t[6]) - minx) / CELL), c1 = Math.floor((Math.max(t[0], t[3], t[6]) - minx) / CELL);
      const r0 = Math.floor((Math.min(t[2], t[5], t[8]) - minz) / CELL), r1 = Math.floor((Math.max(t[2], t[5], t[8]) - minz) / CELL);
      for (let r = r0; r <= r1; r++) for (let c = c0; c <= c1; c++) {
        const k = r * cols + c; if (k < 0 || k >= bins.length) continue;
        (bins[k] || (bins[k] = [])).push(i);
      }
    }
    TS = { tris, bins, cols, rows, minx, minz, CELL,
      // highest surface under (x,z); returns {y, kind} or null
      at(x, z) {
        const c = Math.floor((x - this.minx) / this.CELL), r = Math.floor((z - this.minz) / this.CELL);
        if (c < 0 || r < 0 || c >= this.cols || r >= this.rows) return null;
        const b = this.bins[r * this.cols + c]; if (!b) return null;
        let best = null;
        for (const i of b) {
          const t = this.tris[i];
          const ax = t[0], az = t[2], bx = t[3], bz = t[5], cx = t[6], cz = t[8];
          const d = (bz - cz) * (ax - cx) + (cx - bx) * (az - cz);
          if (Math.abs(d) < 1e-9) continue;
          const l1 = ((bz - cz) * (x - cx) + (cx - bx) * (z - cz)) / d;
          const l2 = ((cz - az) * (x - cx) + (ax - cx) * (z - cz)) / d;
          const l3 = 1 - l1 - l2;
          if (l1 < -1e-4 || l2 < -1e-4 || l3 < -1e-4) continue;
          const y = l1 * t[1] + l2 * t[4] + l3 * t[7];
          if (!best || y > best.y) best = { y, kind: t[9] };
        }
        return best;
      } };
    return TS;
  }

  // ===========================================================================
  // GEOMETRY HELPERS  (no BufferGeometryUtils in play3d's bundle)
  // ===========================================================================
  function merge(parts) {
    let np = 0; parts.forEach(([g]) => { np += (g.index ? g.index.count : g.attributes.position.count); });
    const pos = new Float32Array(np * 3), nrm = new Float32Array(np * 3), uv = new Float32Array(np * 2);
    let o = 0; const v = new R3.Vector3(), n = new R3.Vector3(), nm = new R3.Matrix3();
    for (const [g, mat] of parts) {
      nm.getNormalMatrix(mat);
      const P = g.attributes.position, N = g.attributes.normal, U = g.attributes.uv, I = g.index;
      const cnt = I ? I.count : P.count;
      for (let k = 0; k < cnt; k++) { const i = I ? I.getX(k) : k;
        v.fromBufferAttribute(P, i).applyMatrix4(mat);
        n.fromBufferAttribute(N, i).applyMatrix3(nm).normalize();
        pos[o * 3] = v.x; pos[o * 3 + 1] = v.y; pos[o * 3 + 2] = v.z;
        nrm[o * 3] = n.x; nrm[o * 3 + 1] = n.y; nrm[o * 3 + 2] = n.z;
        if (U) { uv[o * 2] = U.getX(i); uv[o * 2 + 1] = U.getY(i); }
        o++; }
    }
    const g = new R3.BufferGeometry();
    g.setAttribute('position', new R3.Float32BufferAttribute(pos, 3));
    g.setAttribute('normal', new R3.Float32BufferAttribute(nrm, 3));
    g.setAttribute('uv', new R3.Float32BufferAttribute(uv, 2));
    return g;
  }

  // ---- THE TUFT.  Six blades, ONE TRIANGLE EACH. --------------------------
  // A blade is a triangle whose apex leans: base 0.10 wide at y=0, tip at y=1
  // offset by (lean). Six of them fanned = 6 triangles, which is an eighth of
  // what one lobed bush costs. THE POINT OF A TUFT IS ITS SILHOUETTE, and a
  // silhouette is the cheapest thing in a renderer.
  function tuftGeo(nb, seed) {
    const r = rng(seed), pos = [], nrm = [], uv = [];
    for (let i = 0; i < nb; i++) {
      const a = (i / nb) * Math.PI * 2 + r() * 0.9;
      const w = 0.055 + r() * 0.035, h = 0.62 + r() * 0.55, lean = 0.20 + r() * 0.34;
      const ca = Math.cos(a), sa = Math.sin(a);
      const bx = ca * 0.055, bz = sa * 0.055;
      const A = [bx - sa * w, 0, bz + ca * w], B = [bx + sa * w, 0, bz - ca * w],
            T = [bx + ca * lean, h, bz + sa * lean];
      pos.push(A[0], A[1], A[2], B[0], B[1], B[2], T[0], T[1], T[2]);
      for (let k = 0; k < 3; k++) nrm.push(-sa, 0.55, ca);
      // UVs sample a SMALL PATCH in the middle of the borrowed atlas, never 0..1.
      // The forest lane paid for the same thing on a crown: an icosahedron's own
      // UVs wrap a 1k canopy map ONCE around the whole form and it renders as
      // three enormous smeared strokes.
      uv.push(0.42, 0.42, 0.50, 0.42, 0.46, 0.50);
    }
    return unitGeo(pos, nrm, uv);
  }
  // Every injected form carries an all-ones COLOR_0. r128's color_fragment only
  // applies vColor when USE_COLOR is defined, and USE_COLOR comes from
  // material.vertexColors — so an InstancedMesh's instanceColor is SILENTLY
  // DROPPED by a material with vertexColors:false, and a geometry with no color
  // attribute under vertexColors:true reads the attribute as zero and renders
  // black. One all-ones attribute plus vertexColors:true is the only combination
  // that is right.
  function unitGeo(pos, nrm, uv) {
    const g = new R3.BufferGeometry();
    g.setAttribute('position', new R3.Float32BufferAttribute(pos, 3));
    g.setAttribute('normal', new R3.Float32BufferAttribute(nrm, 3));
    g.setAttribute('uv', new R3.Float32BufferAttribute(uv, 2));
    const n = pos.length / 3, col = new Float32Array(n * 3); col.fill(1);
    g.setAttribute('color', new R3.Float32BufferAttribute(col, 3));
    return g;
  }
  // ---- THE CLUMP.  A squashed low icosahedron: a bush at a rock's foot. ----
  function clumpGeo() { const src = new R3.IcosahedronGeometry(0.5, 0); const p = src.attributes.position;
    for (let i = 0; i < p.count; i++) { p.setY(i, p.getY(i) * 0.62 + 0.5); }
    src.computeVertexNormals();
    const P = src.attributes.position, N = src.attributes.normal, I = src.index;
    const pos = [], nrm = [], uv = []; const cnt = I ? I.count : P.count;
    for (let k = 0; k < cnt; k++) { const i = I ? I.getX(k) : k;
      pos.push(P.getX(i), P.getY(i), P.getZ(i)); nrm.push(N.getX(i), N.getY(i), N.getZ(i));
      uv.push(0.42 + (k % 3) * 0.03, 0.44 + ((k / 3 | 0) % 3) * 0.03); }
    src.dispose(); return unitGeo(pos, nrm, uv); }
  // ---- THE FLOWER.  Two triangles, in CLUMPS never scattered.
  function flowerGeo() { const s = 0.5, h = 1.0;
    return unitGeo(
      [-s, h - 0.35, 0, s, h - 0.35, 0, 0, h, 0, 0, h - 0.35, -s, 0, h - 0.35, s, 0, h, 0],
      [0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0],
      [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]); }

  function instance(geo, mat, rows, name) {
    const m = new R3.InstancedMesh(geo, mat, rows.length);
    m.name = name;
    // THE TRAP THIS LANE PAID FOR, AND IT COST THE FIRST TWO ROUNDS.
    // r128 frustum-culls an InstancedMesh against geometry.boundingSphere
    // transformed by the OBJECT's matrixWorld — the per-instance matrices are not
    // in it. A scatter batch whose base form is a 0.15 m tuft at the origin is
    // therefore culled from every camera that cannot see world (0,0,0), and 28,347
    // tufts rendered as EXACTLY NOTHING while every count in the report was right.
    // A report that says "28,347 placed" and a frame that shows none is a culling
    // bug, never a placement bug: check visibility before you touch the density.
    m.frustumCulled = false;
    const q = new R3.Quaternion(), e = new R3.Euler(), s = new R3.Vector3(), p = new R3.Vector3(), M = new R3.Matrix4();
    for (let i = 0; i < rows.length; i++) {
      const R_ = rows[i];
      e.set(R_.tilt || 0, R_.yaw || 0, 0); q.setFromEuler(e);
      p.set(R_.x, R_.y, R_.z); s.set(R_.w, R_.h, R_.w);
      m.setMatrixAt(i, M.compose(p, q, s));
      m.setColorAt(i, R_.c);
    }
    m.instanceMatrix.needsUpdate = true; if (m.instanceColor) m.instanceColor.needsUpdate = true;
    m.castShadow = true; m.receiveShadow = true;
    group().add(m);
    return triCount(geo) * rows.length;
  }

  // ===========================================================================
  function clear() {
    if (G) { G.traverse(o => { if (o.isMesh) { o.geometry && o.geometry.dispose();
        (Array.isArray(o.material) ? o.material : [o.material]).forEach(m => m && m.dispose()); } });
      scene.remove(G); G = null; }
    for (const o of ADDED) scene.remove(o); ADDED.length = 0;
    for (const [o, v] of HIDDEN) o.visible = v; HIDDEN.length = 0;
    for (const [g, saved] of COLSAVE) { g.setAttribute('color', saved); }
    COLSAVE.clear();
    if (LSAVE) {
      AMBIENT.intensity = LSAVE.a; AMBIENT.color.copy(LSAVE.ac);
      dl.intensity = LSAVE.d; dl.color.copy(LSAVE.dc);
      if (LSAVE.hemi) { LSAVE.hemi.intensity = LSAVE.hi; LSAVE.hemi.color.copy(LSAVE.hc); LSAVE.hemi.groundColor.copy(LSAVE.hg); }
      LSAVE = null;
    }
    if (FSAVE !== null) { if (FSAVE === 0) scene.fog = null;
      else { scene.fog.near = FSAVE.n; scene.fog.far = FSAVE.f; scene.fog.color.copy(FSAVE.c); } FSAVE = null; }
    if (RSAVE) { R.toneMappingExposure = RSAVE.e; RSAVE = null; }
    return 'cleared';
  }

  function owHemi() {   // the scene-scoped RTLIGHT: the one the ow rig actually drives
    let best = null; scene.traverse(o => { if (o.isHemisphereLight && o.intensity > 0.01) best = o; });
    return best;
  }
  function saveLights() {
    if (LSAVE) return; const h = owHemi();
    LSAVE = { a: AMBIENT.intensity, ac: AMBIENT.color.clone(), d: dl.intensity, dc: dl.color.clone(),
              hemi: h, hi: h ? h.intensity : 0, hc: h ? h.color.clone() : null, hg: h ? h.groundColor.clone() : null };
  }
  function saveFog() { if (FSAVE !== null) return;
    FSAVE = scene.fog ? { n: scene.fog.near, f: scene.fog.far, c: scene.fog.color.clone() } : 0; }
  function saveCol(g) { if (!COLSAVE.has(g)) COLSAVE.set(g, g.getAttribute('color')); }

  // ===========================================================================
  // L1 — THE HOUR.  Light, air and the shadow side.  ZERO TRIANGLES.
  // ===========================================================================
  // The reference's signature is not an asset. It is that a SHADOWED surface is
  // still bright and is a DIFFERENT HUE from a lit one. Ref 1's dark quartile
  // measures b-r = +0.090 — its shadows are blue. Ours are -0.06 to -0.10:
  // brown, only darker. And our corridor spends most of its length inside the
  // gorge wall's own cast shadow, lit by 0.32 ambient + 0.55 hemi against a
  // 2.60 key.
  //
  // WHAT THIS DOES *NOT* DO, and why. It does not add a filmic tone curve. That
  // was already tried and LOOKED AT (docs/qa/charlight/tone-ow-{off,aces,agx}.png)
  // and the finding stands: at exposure 1.0 AgX and ACES take the meadow to khaki
  // and the river to grey-teal, because this palette is direct albedo under a key
  // solved in linear. The fault in these frames is not the curve. It is the FILL.
  //
  // The fill is raised on the HEMISPHERE, not on the ambient, on purpose: a
  // hemisphere is directional (sky above, ground below) so it keeps the top/bottom
  // gradient that gives a solid its form, while flat ambient is exactly the 1.70-
  // of-omnidirectional-fill mistake the light lane already paid for and named.
  function l1(o) {
    o = o || {};
    saveLights(); saveFog(); if (!RSAVE) RSAVE = { e: R.toneMappingExposure };
    const h = owHemi();
    // KEY: unchanged in colour and angle. The golden hour is ratified; this lane
    // does not get to re-decide it.
    dl.intensity = o.key != null ? o.key : 2.60;
    // FILL: same total order of magnitude, moved onto the hemisphere and made
    // properly blue, so a shadowed face reads as SKY-LIT rather than as dim sun.
    AMBIENT.color.setRGB(0.30, 0.42, 0.72); AMBIENT.intensity = o.amb != null ? o.amb : 0.34;
    if (h) { h.color.setRGB(0.50, 0.68, 1.00); h.groundColor.setRGB(0.52, 0.42, 0.30);
             h.intensity = o.hemi != null ? o.hemi : 1.25; }
    // BOUNCE: one dim, cool, shadowless light from roughly opposite the key at a
    // low elevation. This is the second thing every reference frame has and we do
    // not: a shadowed vertical face that is not flat. It casts nothing, so it
    // costs a shader loop and no shadow pass.
    const b = new R3.DirectionalLight(0x000000, 0);
    b.color.setRGB(0.44, 0.60, 0.92); b.intensity = o.bounce != null ? o.bounce : 0.85;
    b.position.set(0.62, 0.34, 0.71); b.name = '__owl_bounce';
    scene.add(b); ADDED.push(b);
    // AIR: the fog ships at near 150 / far 340 and the whole walked corridor is
    // 172 m long, so IT NEVER RUNS. Measured on the four cameras: not one fogged
    // pixel. Ref 3 is carried almost entirely by aerial perspective.
    if (scene.fog) { scene.fog.near = o.fogN != null ? o.fogN : 34;
                     scene.fog.far = o.fogF != null ? o.fogF : 205;
                     scene.fog.color.copy(C(o.fogC || 0xd3e0e8)); }
    R.toneMappingExposure = o.exp != null ? o.exp : 1.0;
    return `L1 the hour — key ${dl.intensity}, amb ${AMBIENT.intensity}, hemi ${h ? h.intensity : 'n/a'}, ` +
           `bounce ${b.intensity}, fog ${scene.fog ? scene.fog.near + '/' + scene.fog.far : 'none'}, +0 triangles`;
  }

  // ===========================================================================
  // L2 — THE GROUND IS GEOMETRY.  Detail placed ONLY where it makes an edge.
  // ===========================================================================
  // The reference's grass reads as grass because BLADES BREAK THE SILHOUETTE:
  // against sky at a ridge, against rock at a cliff foot, against the worn earth
  // at a path edge. It is not a carpet — a carpet is what the first probe's A1
  // was, and "adding more stuff" was refused.
  //
  // So the placement rule IS the candidate: a tuft is emitted only where the
  // ground CHANGES — road edge, grass/sand seam, grass/rock seam — with density
  // falling off over ~2.4 m. That answers three complaints with one pass:
  // the ground has no scale cue, the transitions are hard vector cuts, and the
  // vegetation is not clustered at multiple scales.
  function l2(o) {
    o = o || {};
    const Z = zones(), T = terrain();
    const STEP = o.step || 1.0;       // COARSE lattice: where is there an edge?
    const DENS = o.dens != null ? o.dens : 9;   // tufts per m2 AT a seam
    const BAND = o.band || 2.6;       // how far from an edge a tuft may stand
    const r = rng(4711);
    const tufts = [], clumps = [], flowers = [];
    // The corridor the player actually walks, plus a margin. Sampling the whole
    // 280x200 tile would spend the entire budget on ground no camera ever sees —
    // which is the shipped bundle's own mistake (38,740 tris of tree field, ZERO
    // within 15 m of the road at all seven sampled points).
    const X0 = o.x0 != null ? o.x0 : -75, X1 = o.x1 != null ? o.x1 : 60;
    const Z0 = o.z0 != null ? o.z0 : -50, Z1 = o.z1 != null ? o.z1 : 85;
    const PAL = [C(0x8fa845), C(0x7d9a3e), C(0xa8b757), C(0x6b8438), C(0xbcae5c)];
    const PALDRY = [C(0xb2a86a), C(0xa39a5e), C(0xc4b878)];
    const FLOW = [C(0xf2ead6), C(0xe8c85a), C(0xd98fae), C(0xf2ead6), C(0xc9d8ee)];
    let edgeSites = 0;
    for (let x = X0; x <= X1; x += STEP) for (let z = Z0; z <= Z1; z += STEP) {
      const jx = x + (r() - 0.5) * STEP * 1.5, jz = z + (r() - 0.5) * STEP * 1.5;
      const here = T.at(jx, jz); if (!here) continue;
      const zt = Z.at(jx, jz);
      if (zt === Z_WATER) continue;
      // ---- is this an EDGE?  probe the surface kind and the zone on a ring ----
      let diff = 0, near = 0, rockNear = 0, roadNear = 0;
      for (let k = 0; k < 8; k++) {
        const a = k * Math.PI / 4;
        for (const d of [BAND * 0.45, BAND]) {
          const px = jx + Math.cos(a) * d, pz = jz + Math.sin(a) * d;
          const s = T.at(px, pz); if (!s) continue;
          near++;
          if (s.kind !== here.kind) { diff++; if (s.kind === 3) rockNear++; }
          if (Z.at(px, pz) === Z_ROAD && zt !== Z_ROAD) roadNear++;
        }
      }
      if (!near) continue;
      const edge = diff / near, road = roadNear / near;
      // WEIGHT IS A SEAM WEIGHT AND NOTHING ELSE. This is the whole candidate:
      // grass geometry stands where the ground CHANGES and nowhere else. A
      // uniform meadow scatter is the carpet that was already refused, and a
      // carpet is also the one thing that costs real triangles.
      let wgt = Math.max(edge * 1.9, road * 2.1);
      // the road ribbon itself stays bare — a path with grass ON it is a path
      // nobody uses, and the walk network is law
      if (zt === Z_ROAD) wgt *= 0.12;
      // ONE ration away from the seams, and only along the walked verge, so the
      // ground the player is actually looking at is not bald between edges.
      if (road > 0.02 || edge > 0.02) wgt = Math.max(wgt, 0.16);
      wgt = Math.min(1, wgt);
      if (wgt < 0.02) continue;
      edgeSites++;
      const dry = here.kind === 2, rock = here.kind === 3;
      const pal = dry ? PALDRY : PAL;
      // ---- SCALE ONE: the blades. n per m2 scaled by the seam weight --------
      // SCALE IS AGAINST THE BODY, NOT AGAINST TASTE. Vesper is 1.45 u. The first
      // round put tufts 0.4-1.0 u tall and the shelf grew a hedge of black agave;
      // the reference's grass is ankle-to-shin on its character, so 0.10-0.34.
      const n = Math.round(wgt * DENS * STEP * STEP * (0.55 + r() * 0.9));
      for (let k = 0; k < n; k++) {
        const px = jx + (r() - 0.5) * STEP * 1.4, pz = jz + (r() - 0.5) * STEP * 1.4;
        const s = T.at(px, pz); if (!s) continue;
        if (Z.at(px, pz) === Z_WATER) continue;
        // SLOPE GATE. Without it the tufts climb the gorge WALL — the seam test
        // fires hardest exactly where grass meets vertical rock, and 60 m of
        // cliff sprouted grass growing straight out of it.
        const sa = T.at(px + 0.7, pz), sb = T.at(px - 0.7, pz),
              sc = T.at(px, pz + 0.7), sd = T.at(px, pz - 0.7);
        if (!sa || !sb || !sc || !sd) continue;
        const grad = Math.hypot(sa.y - sb.y, sc.y - sd.y) / 1.4;
        if (grad > (o.maxSlope != null ? o.maxSlope : 0.85)) continue;
        const c = pal[(r() * pal.length) | 0].clone();
        c.multiplyScalar(0.78 + r() * 0.52);           // a real value spread per tuft
        const hh = (s.kind === 3 ? 0.13 : s.kind === 2 ? 0.15 : 0.24) * (0.62 + r() * 0.90);
        tufts.push({ x: px, y: s.y - 0.02, z: pz, w: 0.34 + r() * 0.30, h: hh, yaw: r() * 6.28,
                     tilt: (r() - 0.5) * 0.26, c });
      }
      // ---- SCALE TWO: a shrub clump where grass meets ROCK -------------------
      // THE COLOUR MULTIPLIER IS AGAINST THE MAP'S OWN MEAN, NOT AGAINST 1.0.
      // ow_valley_bushcore ships COLOR_0 at L 0.311; instance-colouring it at
      // 0.5-0.8 produced faceted BLACK BOULDERS at every rock foot. x2.4 puts a
      // clump back in the band the shipped bush masses occupy.
      if (rockNear > 3 && r() < 0.24) {
        const cc = PAL[(r() * PAL.length) | 0].clone().multiplyScalar(1.9 + r() * 0.9);
        clumps.push({ x: jx + (r() - 0.5) * 0.9, y: here.y - 0.10, z: jz + (r() - 0.5) * 0.9,
                      w: 0.75 + r() * 1.05, h: 0.45 + r() * 0.75, yaw: r() * 6.28, tilt: 0, c: cc });
      }
    }
    // ---- SCALE THREE: FLOWERS IN CLUMPS, never scattered -------------------
    // The reference's flower pops are always 5-12 heads in a patch a metre or two
    // across. An even scatter at the same count reads as noise; that difference
    // is the whole trick, and it costs nothing to obey.
    const NCL = o.flowerClumps != null ? o.flowerClumps : 900;
    let placed = 0;
    for (let i = 0; i < NCL; i++) {
      const cx = X0 + r() * (X1 - X0), cz = Z0 + r() * (Z1 - Z0);
      if (Z.at(cx, cz) !== Z_MEADOW) continue;
      const s = T.at(cx, cz); if (!s || s.kind !== 1) continue;
      // a clump the player never walks past is a triangle spent on nobody: only
      // within sight of the road, which is the census lesson of the first probe
      let seen = false;
      for (let k = 0; k < 10 && !seen; k++) { const a = k * 0.628;
        for (const d of [6, 12, 18]) if (Z.at(cx + Math.cos(a) * d, cz + Math.sin(a) * d) === Z_ROAD) { seen = true; break; } }
      if (!seen) continue;
      placed++;
      const col = FLOW[(r() * FLOW.length) | 0];
      const n = 6 + ((r() * 9) | 0), rad = 0.55 + r() * 1.35;
      for (let k = 0; k < n; k++) {
        const a = r() * 6.28, d = Math.sqrt(r()) * rad;
        const px = cx + Math.cos(a) * d, pz = cz + Math.sin(a) * d;
        const p = T.at(px, pz); if (!p) continue;
        flowers.push({ x: px, y: p.y, z: pz, w: 0.055 + r() * 0.045, h: 0.13 + r() * 0.10,
                       yaw: r() * 6.28, tilt: (r() - 0.5) * 0.3, c: col });
      }
    }
    // ow_f2_matte is the one shipped material with NO map (verified in the live
    // bundle), so the tuft's colour is entirely the instance's. The "flat colour
    // beside a mapped crag reads as pale plastic" finding is about metre-scale
    // SOLIDS; a 0.25 m blade has no room for a texture to read in.
    const mT = clonedFlat('ow_f2_matte') || clonedFlat('ow_f2_canopy');
    const mC = clonedFlat('ow_valley_bushcore') || mT;
    const mF = clonedFlat('ow_f2_matte') || mT;
    if (mT) { mT.side = R3.DoubleSide; mT.roughness = 0.95; }
    if (mF) { mF.side = R3.DoubleSide; mF.roughness = 0.80; }
    let tris = 0;
    tris += instance(tuftGeo(6, 91), mT, tufts, '__owl_tufts');
    if (clumps.length) tris += instance(clumpGeo(), mC, clumps, '__owl_clumps');
    if (flowers.length) tris += instance(flowerGeo(), mF, flowers, '__owl_flowers');
    return `L2 ground-is-geometry — ${tufts.length} tufts (6 tris each) at ${edgeSites} seam cells + ` +
           `${clumps.length} clumps + ${flowers.length} flowers in ${placed} clumps, ` +
           `${tris} triangles in, 0 out`;
  }

  // ===========================================================================
  // L3 — THE SURFACE.  Zero triangles: COLOR_0 only.
  // ===========================================================================
  // Taken literally, "improve the quality of our existing stuff" means: the
  // terrain we already have is the wrong colour and has no variation. Three
  // measured faults, three edits, no geometry:
  //
  //   (a) THE GRASS IS DARKER THAN THE ROCK (L 0.383 vs 0.502) and barely green
  //       (G-R = +0.047). In every reference the biggest bright area is lit
  //       ground and the rock is the mid value. Lift and green the grass.
  //   (b) THE ROCK IS WARM-NEUTRAL, so the frame has no cool anywhere and the
  //       whole picture sits in one 30-degree hue bin (44-56 % of coloured
  //       pixels, against the references' 32-43 %). Cool it, and give it
  //       BEDDING: a banding in world y, which is what "strata" is.
  //   (c) EVERY TRANSITION IS A CUT. The seam between grass and sand at the
  //       Emberbrook gate is a mesh boundary; a vertex near it is dragged toward
  //       the other surface's tone with a NOISY threshold, so the line becomes
  //       ragged instead of vector. The honest limit is stated in the gallery:
  //       the terrain lattice is 1.6 m, so this buys a 1.6-3.2 m ragged seam and
  //       NOT a true blend — the textures still change abruptly underneath.
  function l3(o) {
    o = o || {};
    const T = terrain();
    const stats = {};
    for (const [nm, kind] of GROUND) {
      const mesh = find(nm); if (!mesh) continue;
      mesh.updateMatrixWorld(true);
      const g = mesh.geometry, P = g.attributes.position, A = g.attributes.color;
      if (!A) continue;
      saveCol(g);
      const out = new Float32Array(A.count * (A.itemSize >= 3 ? 3 : 3));
      const v = new R3.Vector3(), M = mesh.matrixWorld;
      const c = new R3.Color();
      let l0 = 0, l1v = 0;
      for (let i = 0; i < A.count; i++) {
        v.fromBufferAttribute(P, i).applyMatrix4(M);
        c.setRGB(A.getX(i), A.getY(i), A.getZ(i));       // ALREADY LINEAR
        l0 += 0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b;
        const nBig = vnoise(v.x, v.z, 15.0, 3.1), nMid = vnoise(v.x, v.z, 4.6, 8.7),
              nFine = vnoise(v.x, v.z, 1.9, 21.3);
        const n = nBig * 0.52 + nMid * 0.33 + nFine * 0.15;   // 0..1
        // SATURATING CONTROL. A null result on a recolour has to be separated
        // from a broken recolour by an amplitude that CANNOT be missed — the
        // forest lane paid for this lesson (a 0.8-1.2 tone draw moved 0.8 % of
        // pixels and read as "the code does not work").
        if (o.control) { const CC = [null, [1, 0, 0], [0, 1, 0], [0, 0, 1]][kind];
          out[i * 3] = CC[0]; out[i * 3 + 1] = CC[1]; out[i * 3 + 2] = CC[2];
          l1v += 0.2126 * CC[0] + 0.7152 * CC[1] + 0.0722 * CC[2]; continue; }
        if (kind === 1) {          // ---- GRASS -------------------------------
          c.setRGB(c.r * (0.86 + n * 0.30), c.g * (1.14 + n * 0.40), c.b * (0.70 + n * 0.34));
          c.multiplyScalar((o.grassGain != null ? o.grassGain : 1.34) * (0.80 + n * 0.46));
        } else if (kind === 2) {   // ---- DRY / SAND --------------------------
          c.setRGB(c.r * (1.02 + n * 0.24), c.g * (1.00 + n * 0.26), c.b * (0.88 + n * 0.34));
          c.multiplyScalar((o.dryGain != null ? o.dryGain : 1.16) * (0.86 + n * 0.32));
        } else {                   // ---- ROCK --------------------------------
          // strata: a band in world y, plus a slow tonal drift so no two faces
          // of the same wall are the same value.
          // AMPLITUDE, AGAIN. The first pass multiplied b by 1.10 and the cliff
          // did not move: the BROWN IS IN THE MAP, and COLOR_0 multiplies it, so
          // a 10 % blue push against a map whose blue channel is already the
          // smallest is nothing. It takes r x0.66 / b x1.62 for the gorge wall to
          // stop being the warmest surface in the frame.
          const bed = 0.5 + 0.5 * Math.sin(v.y * 1.55 + vnoise(v.x, v.z, 22.0, 5.5) * 4.2);
          const band = 0.72 + bed * 0.52;
          const k = o.rockCool != null ? o.rockCool : 1.0;
          c.setRGB(c.r * (1 - 0.34 * k + n * 0.14), c.g * (1 - 0.10 * k + n * 0.14),
                   c.b * (1 + 0.62 * k + n * 0.20));
          c.multiplyScalar((o.rockGain != null ? o.rockGain : 1.16) * band * (0.86 + n * 0.30));
        }
        // ---- (c) THE RAGGED SEAM -------------------------------------------
        if (o.seam !== false) {
          let other = 0, tot = 0;
          for (let k = 0; k < 6; k++) { const a = k * Math.PI / 3;
            const s = T.at(v.x + Math.cos(a) * 2.1, v.z + Math.sin(a) * 2.1);
            if (!s) continue; tot++; if (s.kind !== kind) other++; }
          if (tot && other) {
            const wr = other / tot;
            // noisy threshold: without it the blend is a smooth ramp, which is
            // just a softer vector edge. Reference seams are RAGGED.
            const t = Math.max(0, Math.min(1, wr * 1.5 - 0.25 + (nFine - 0.5) * 0.85));
            const dark = 0.72 + nMid * 0.30;
            c.multiplyScalar(1 - t * 0.30 * dark);
          }
        }
        l1v += 0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b;
        out[i * 3] = c.r; out[i * 3 + 1] = c.g; out[i * 3 + 2] = c.b;
      }
      g.setAttribute('color', new R3.Float32BufferAttribute(out, 3));
      stats[nm] = { n: A.count, L0: +(l0 / A.count).toFixed(3), L1: +(l1v / A.count).toFixed(3) };
    }
    return 'L3 surface — COLOR_0 only, +0 triangles — ' +
      Object.entries(stats).map(([k, v]) => `${k} L ${v.L0}->${v.L1} (${v.n} verts)`).join(' · ');
  }

  function all(o) { const a = l1(o), b = l3(o), c = l2(o); return [a, b, c].join(' | '); }

  return { clear, l1, l2, l3, all, zones, terrain, find, triCount };
})();
