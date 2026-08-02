/* forest.js — OVERWORLD FOREST QUALITY: three candidate treatments for the
 * ow-valley treeline, injected into the LIVE runtime over CDP and photographed.
 *
 * NOTHING HERE SHIPS. Section A of the first probe was rejected ("not convinced
 * that 'adding more stuff' is more important than improving the quality of our
 * existing stuff — i.e. the forests"), so every candidate below spends the SAME
 * or FEWER triangles than what it replaces. Each prints its own triangle ledger.
 *
 * THE DIAGNOSIS THEY ARE ANSWERING (measured, see the gallery):
 *   * the stands (veg_canopy_*) are BUSH MASSES — a jittered-hex lattice of
 *     ellipsoid lobes welded into one skin, with NO TRUNK ANYWHERE in the code
 *     path (tools/valley_veg.py). A stand cannot have species because a stand is
 *     not made of trees.
 *   * the specimen field (veg_field) is one silhouette: plant_region only ever
 *     calls TREE_FN 'a' and 'c', both broadleaf ellipsoids on a 1.55 s trunk,
 *     varied by ONE number, s = uniform(0.86, 1.26).
 *   * per-crown mean luminance over the region's 500 crown lobes: mean 0.950,
 *     sd 0.0016. The whole canopy is one colour to within 0.2 %.
 *
 * THE THREE PAID-FOR TRAPS OF THIS LANE, INHERITED:
 *   * three r128 has no input colour management (play3d sets outputEncoding =
 *     sRGBEncoding), so a hex must be convertSRGBToLinear'd or it renders chalk.
 *     Values read back OUT of COLOR_0 are ALREADY linear — do not convert those.
 *   * SIM.tp(x,z) raycasts from the current P.y; ow_multi's __tp fixes it.
 *   * the vegetation meshes are UNINDEXED, so any component analysis must weld by
 *     position first or it returns one component per triangle.
 */
window.OWF = (function () {
  const R3 = THREE;
  let G = null;
  const HIDDEN = [];

  const C = (hex) => new R3.Color(hex).convertSRGBToLinear();
  function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0;
    let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

  function group() { if (!G) { G = new R3.Group(); G.name = '__owf'; scene.add(G); } return G; }
  function clear() {
    if (G) { G.traverse(o => { if (o.isMesh) { o.geometry && o.geometry.dispose();
        (Array.isArray(o.material) ? o.material : [o.material]).forEach(m => m && m.dispose()); } });
      scene.remove(G); G = null; }
    for (const [o, v] of HIDDEN) o.visible = v;
    HIDDEN.length = 0;
    for (const [g, saved] of COLSAVE) g.setAttribute('color', saved);
    COLSAVE.clear();
  }
  const COLSAVE = new Map();

  function find(name) { let hit = null; scene.traverse(o => { if (o.isMesh && o.name === name) hit = o; }); return hit; }
  function hide(name) { const o = find(name); if (o) { HIDDEN.push([o, o.visible]); o.visible = false; } return o; }
  const triCount = g => (g.index ? g.index.count : g.attributes.position.count) / 3;

  // ---- the shipped materials, reused ---------------------------------------
  // A flat untextured colour beside a mapped crag reads as pale plastic at any
  // hex (paid for in the first probe). Every candidate clones a SHIPPED material
  // so it keeps the map, and carries its colour on instanceColor instead.
  function shipped(name) { let hit = null; scene.traverse(o => { if (!o.isMesh) return;
    for (const m of (Array.isArray(o.material) ? o.material : [o.material]))
      if (m && m.name === name) hit = m; }); return hit; }
  function clonedFlat(name) {
    const src = shipped(name); if (!src) return null;
    const m = src.clone(); m.name = name + '__owf';
    m.vertexColors = false;        // our geometry carries no COLOR_0; instanceColor does the work
    return m;
  }
  // COLOR_0 as shipped, read off the bundle (LINEAR already — see the trap note).
  const CANOPY0 = new R3.Color(0.85, 1.00, 0.64);
  const BARK0 = new R3.Color(0.431, 0.334, 0.230);

  // ---- geometry helpers ----------------------------------------------------
  // No BufferGeometryUtils in play3d's bundle: merge by hand.
  function merge(parts) {
    let np = 0;
    parts.forEach(([g]) => { np += (g.index ? g.index.count : g.attributes.position.count); });
    const pos = new Float32Array(np * 3), nrm = new Float32Array(np * 3), uv = new Float32Array(np * 2);
    let o = 0; const v = new R3.Vector3(), n = new R3.Vector3(), nm = new R3.Matrix3();
    for (const [g, mat] of parts) {
      nm.getNormalMatrix(mat);
      const P = g.attributes.position, N = g.attributes.normal, U = g.attributes.uv, I = g.index;
      const cnt = I ? I.count : P.count;
      for (let k = 0; k < cnt; k++) {
        const i = I ? I.getX(k) : k;
        v.fromBufferAttribute(P, i).applyMatrix4(mat);
        n.fromBufferAttribute(N, i).applyMatrix3(nm).normalize();
        pos[o * 3] = v.x; pos[o * 3 + 1] = v.y; pos[o * 3 + 2] = v.z;
        nrm[o * 3] = n.x; nrm[o * 3 + 1] = n.y; nrm[o * 3 + 2] = n.z;
        if (U) { uv[o * 2] = U.getX(i); uv[o * 2 + 1] = U.getY(i); }
        o++;
      }
    }
    const g = new R3.BufferGeometry();
    g.setAttribute('position', new R3.Float32BufferAttribute(pos, 3));
    g.setAttribute('normal', new R3.Float32BufferAttribute(nrm, 3));
    g.setAttribute('uv', new R3.Float32BufferAttribute(uv, 2));
    return g;
  }
  const M4 = (x, y, z, sx, sy, sz, rx) => new R3.Matrix4()
    .compose(new R3.Vector3(x, y, z), new R3.Quaternion().setFromEuler(new R3.Euler(rx || 0, 0, 0)),
             new R3.Vector3(sx, sy, sz));

  // ---- the four forms, all normalised to height 1 at the origin ------------
  // Triangle counts are stated because the whole point of this lane is that
  // VARIETY IS NOT PAID FOR IN TRIANGLES.
  const FORM = {};
  function forms() {
    if (FORM.broadleaf) return FORM;
    const trunk = (h, rb, rt) => new R3.CylinderGeometry(rt, rb, h, 6, 1, true);   // 12 tris
    // BROADLEAF — what the region already has: an ellipsoid crown on a bare trunk.
    FORM.broadleaf = { geo: merge([
      [trunk(0.52, 0.045, 0.030), M4(0, 0.26, 0, 1, 1, 1)],
      [new R3.IcosahedronGeometry(0.30, 1), M4(0, 0.66, 0, 1.15, 0.92, 1.10)],     // 80
      [new R3.IcosahedronGeometry(0.19, 0), M4(0.14, 0.84, -0.06, 1, 0.85, 1)],    // 20
    ]), crown: true };
    // CONIFER — three narrowing skirts. A silhouette that shares NOTHING with the
    // broadleaf, and it is the CHEAPEST form here: 48 tris against 172.
    FORM.conifer = { geo: merge([
      [trunk(0.40, 0.036, 0.022), M4(0, 0.20, 0, 1, 1, 1)],
      [new R3.ConeGeometry(0.26, 0.40, 6, 1, true), M4(0, 0.42, 0, 1, 1, 1)],      // 6
      [new R3.ConeGeometry(0.20, 0.36, 6, 1, true), M4(0, 0.64, 0, 1, 1, 1)],
      [new R3.ConeGeometry(0.13, 0.30, 6, 1, true), M4(0, 0.85, 0, 1, 1, 1)],
    ]), crown: true };
    // SCRUB — a low wide crown with almost no trunk. The understory the wood has
    // no equivalent of; it also breaks the roof line from above.
    // subd 0 was 20 tris and rendered as a FLAT FACETED DISC from the follow
    // camera's 35 deg — an understory that reads as a leaf on the ground is worse
    // than no understory. subd 1 on the main lobe, 60 tris more per plant.
    FORM.scrub = { geo: merge([
      [trunk(0.16, 0.040, 0.032), M4(0, 0.08, 0, 1, 1, 1)],
      [new R3.IcosahedronGeometry(0.30, 1), M4(0, 0.34, 0, 1.30, 0.70, 1.22)],
      [new R3.IcosahedronGeometry(0.20, 0), M4(-0.18, 0.28, 0.12, 1.1, 0.66, 1.1)],
    ]), crown: true };
    // SNAG — a dead tree. Pure trunk and three broken limbs, 39 tris, no leaves:
    // the one form in the set whose whole job is to be a vertical against the sky.
    FORM.snag = { geo: merge([
      [trunk(0.86, 0.048, 0.018), M4(0, 0.43, 0, 1, 1, 1)],
      [trunk(0.30, 0.016, 0.008), M4(0.10, 0.62, 0.02, 1, 1, 1, 1.05)],
      [trunk(0.24, 0.014, 0.007), M4(-0.09, 0.74, -0.05, 1, 1, 1, -0.95)],
    ]), crown: false };
    // THE LEAF TEXTURE HAS TO REPEAT. IcosahedronGeometry's own UV wraps the whole
    // 1k canopy map once around a 2 m crown, so the first run came back as three
    // enormous smeared leaf strokes per tree — the same "one shape at the wrong
    // scale" failure the shipped forest has, just recreated. glTF samplers default
    // to REPEAT, so multiplying the UVs is all it takes.
    for (const k of Object.keys(FORM)) {
      const uv = FORM[k].geo.attributes.uv;
      for (let i = 0; i < uv.count; i++) uv.setXY(i, uv.getX(i) * 3.2, uv.getY(i) * 3.2);
      FORM[k].tris = triCount(FORM[k].geo);
    }
    return FORM;
  }

  // ---- placing a population -------------------------------------------------
  function plant(list, seed, palette, mix) {
    const F = forms(), r = rng(seed);
    const bins = {};
    for (const p of list) {
      let acc = 0, key = null; const t = r();
      for (const [k, w] of mix) { acc += w; if (t <= acc) { key = k; break; } }
      key = key || mix[mix.length - 1][0];
      (bins[key] = bins[key] || []).push(p);
    }
    let tris = 0;
    const dummy = new R3.Matrix4(), v = new R3.Vector3(), qq = new R3.Quaternion(), s = new R3.Vector3();
    for (const key of Object.keys(bins)) {
      const list2 = bins[key], f = F[key];
      const mat = clonedFlat(f.crown ? 'ow_f2_canopy' : 'ow_f2_bark');
      if (!mat) continue;
      const im = new R3.InstancedMesh(f.geo, mat, list2.length);
      im.castShadow = im.receiveShadow = true;
      const col = new R3.Color();
      list2.forEach((p, i) => {
        const h = p.h, w = p.w == null ? 1 : p.w;
        v.set(p.x, p.y, p.z);
        qq.setFromEuler(new R3.Euler(0, r() * 6.2832, (r() - 0.5) * 0.16));
        s.set(h * w, h, h * w);
        dummy.compose(v, qq, s);
        im.setMatrixAt(i, dummy);
        if (f.crown) {
          const t = palette(r);
          col.setRGB(CANOPY0.r * t[0], CANOPY0.g * t[1], CANOPY0.b * t[2]);
        } else col.setRGB(BARK0.r * (0.85 + r() * 0.4), BARK0.g * (0.85 + r() * 0.4), BARK0.b * (0.85 + r() * 0.4));
        im.setColorAt(i, col);
      });
      im.instanceMatrix.needsUpdate = true; if (im.instanceColor) im.instanceColor.needsUpdate = true;
      group().add(im);
      tris += f.tris * list2.length;
    }
    return tris;
  }

  // ---- reading the SHIPPED forest back out ---------------------------------
  // The stands' lobe sites and the field's tree feet are not in any file the
  // runtime can see, so both are recovered from the geometry itself.
  function footprint(name, cell) {
    // occupancy grid over a mesh's XZ shadow -> one site per occupied cell, at the
    // cell's own top. cell = valley_veg.LOBE_SP (3.8 m) reproduces the stand's own
    // lattice without needing the build to tell us where it was.
    const o = find(name); if (!o) return [];
    o.updateWorldMatrix(true, false);
    const P = o.geometry.attributes.position, v = new R3.Vector3(), g = new Map();
    for (let i = 0; i < P.count; i++) {
      v.fromBufferAttribute(P, i).applyMatrix4(o.matrixWorld);
      const k = Math.floor(v.x / cell) + '_' + Math.floor(v.z / cell);
      let c = g.get(k);
      if (!c) { c = { x: 0, z: 0, n: 0, top: -1e9, bot: 1e9 }; g.set(k, c); }
      c.x += v.x; c.z += v.z; c.n++;
      if (v.y > c.top) c.top = v.y; if (v.y < c.bot) c.bot = v.y;
    }
    return [...g.values()].filter(c => c.n >= 6)
      .map(c => ({ x: c.x / c.n, z: c.z / c.n, y: c.bot, top: c.top, h: c.top - c.bot }));
  }
  function feet(name) {
    // tree feet from tree_field_trunks: weld by position, union-find, take the
    // lowest vertex of each 2D cluster. 1.6 m link radius — the tightest planting
    // spacing in STAND_CFG is 3.05 m, so no two trees can merge.
    const o = find(name); if (!o) return [];
    o.updateWorldMatrix(true, false);
    const P = o.geometry.attributes.position, v = new R3.Vector3(), pts = [];
    for (let i = 0; i < P.count; i++) { v.fromBufferAttribute(P, i).applyMatrix4(o.matrixWorld); pts.push([v.x, v.y, v.z]); }
    const CELL = 1.6, grid = new Map();
    pts.forEach((p, i) => { const k = Math.floor(p[0] / CELL) + '_' + Math.floor(p[2] / CELL);
      let a = grid.get(k); if (!a) { a = []; grid.set(k, a); } a.push(i); });
    const par = new Int32Array(pts.length); for (let i = 0; i < pts.length; i++) par[i] = i;
    const fnd = a => { while (par[a] !== a) { par[a] = par[par[a]]; a = par[a]; } return a; };
    const uni = (a, b) => { a = fnd(a); b = fnd(b); if (a !== b) par[a] = b; };
    for (const [k, a] of grid) { const [cx, cz] = k.split('_').map(Number);
      for (let dx = -1; dx <= 1; dx++) for (let dz = -1; dz <= 1; dz++) {
        const b = grid.get((cx + dx) + '_' + (cz + dz)); if (!b) continue;
        for (const i of a) for (const j of b)
          if ((pts[i][0] - pts[j][0]) ** 2 + (pts[i][2] - pts[j][2]) ** 2 < CELL * CELL) uni(i, j); } }
    const cl = new Map();
    pts.forEach((p, i) => { const r = fnd(i); let c = cl.get(r);
      if (!c) { c = { x: 0, z: 0, n: 0, bot: 1e9 }; cl.set(r, c); }
      c.x += p[0]; c.z += p[2]; c.n++; if (p[1] < c.bot) c.bot = p[1]; });
    return [...cl.values()].filter(c => c.n >= 12).map(c => ({ x: c.x / c.n, z: c.z / c.n, y: c.bot }));
  }

  // ---- palettes -------------------------------------------------------------
  // The towns' ratified look is golden-hour variant C, greens going into autumn
  // (docs/plans/pops-of-color.md). The corridor should sit BESIDE that, not fight
  // it: these are multipliers on the shipped canopy COLOR_0, never replacements.
  // FIRST PASS WAS TOO TIMID AND IT MEASURED AS NOTHING. Multipliers in 0.8-1.2
  // over a mid-grey COLOR_0 under a dominant albedo map moved 0.8 % of pixels — a
  // change nobody could see. Proved the machinery was fine by forcing COLOR_0 to
  // pure red on every veg mesh: 16.8 % of pixels moved and the stand went crimson.
  // So the lesson is about AMPLITUDE, not plumbing: on a mapped surface a tone
  // draw has to be a real hue rotation or it is invisible.
  const P_FLAT = () => [1, 1, 1];
  // The LUMINANCE spread (j) matters more than the hue draw: light and dark
  // crowns are what let the eye cut a mass into individual trees. 0.62-1.30 is a
  // full stop either side.
  const P_AUTUMN = (r) => {
    const t = r(), j = 0.62 + r() * 0.68;
    if (t < 0.44) return [0.62 * j, 0.86 * j, 0.66 * j];   // deep cool green
    if (t < 0.74) return [1.30 * j, 1.00 * j, 0.44 * j];   // warm olive
    if (t < 0.90) return [1.58 * j, 0.80 * j, 0.28 * j];   // rust
    return [1.08 * j, 1.18 * j, 0.98 * j];                 // pale, wind-turned
  };

  // ===========================================================================
  // F1 — TONE AND CROWN VARIANCE. NO NEW GEOMETRY AT ALL.
  // ===========================================================================
  // The cheapest possible answer, and the one that tests whether "one silhouette"
  // is really "one COLOUR". Every crown keeps its shape, its position and its
  // triangle; only COLOR_0 moves, per crown, on a 3.8 m noise cell (a crown is
  // 2.6 m across, so the cell is the crown). Triangle delta: exactly ZERO.
  function f1() {
    const cell = 3.4, r = rng(4711);
    const hash = new Map();
    const draw = (k) => { let c = hash.get(k); if (!c) { c = P_AUTUMN(r); hash.set(k, c); } return c; };
    let touched = 0;
    for (const nm of ['veg_field', 'veg_canopy_whisperwood', 'veg_canopy_farwall-crown',
                      'veg_canopy_pocket-grove', 'veg_field_cards', 'veg_canopy_whisperwood_cards',
                      'veg_canopy_farwall-crown_cards', 'veg_canopy_pocket-grove_cards']) {
      const o = find(nm); if (!o) continue;
      const g = o.geometry, P = g.attributes.position, A = g.attributes.color;
      if (!A) continue;
      if (!COLSAVE.has(g)) COLSAVE.set(g, A.clone());
      o.updateWorldMatrix(true, false);
      const v = new R3.Vector3(), out = A.array.slice();
      const n = A.itemSize;
      // veg_field_cards' COLOR_0 is a NORMALIZED Uint16 vec4; the others are plain
      // float vec3. Clamping to 1 without the scale writes 1/65535 and the mesh
      // goes black — a silent, mesh-specific failure.
      const FULL = A.normalized ? (A.array.BYTES_PER_ELEMENT === 2 ? 65535 : 255) : 1;
      for (let i = 0; i < P.count; i++) {
        v.fromBufferAttribute(P, i).applyMatrix4(o.matrixWorld);
        const t = draw(Math.floor(v.x / cell) + '_' + Math.floor(v.z / cell));
        for (let k = 0; k < 3; k++) out[i * n + k] = Math.min(FULL, A.array[i * n + k] * t[k]);
      }
      g.setAttribute('color', new R3.BufferAttribute(out, n, A.normalized));
      touched++;
    }
    return `F1 tone variance — ${touched} meshes recoloured per 3.4 m crown cell, +0 tris`;
  }

  // ===========================================================================
  // F2 — SPECIES MIX AT THE SAME BUDGET.
  // ===========================================================================
  // Both populations are rebuilt in place: the stands' bush lattice becomes one
  // TREE per lobe site, and the specimen field becomes a mixed stand on its own
  // feet. Nothing moves; the SHAPES change and so does the per-tree colour.
  function f2() {
    let drop = 0, add = 0, n = 0;
    const mix = [['conifer', 0.34], ['broadleaf', 0.34], ['scrub', 0.20], ['snag', 0.12]];
    for (const st of ['whisperwood', 'farwall-crown', 'pocket-grove']) {
      const core = find('veg_canopy_' + st), cards = find('veg_canopy_' + st + '_cards');
      if (!core) continue;
      const sites = footprint('veg_canopy_' + st, 3.8);
      drop += triCount(core.geometry) + (cards ? triCount(cards.geometry) : 0);
      hide('veg_canopy_' + st); if (cards) hide('veg_canopy_' + st + '_cards');
      // CROWN WIDTH IS CAPPED AGAINST THE LATTICE. First run drew w up to 1.45 on
      // h up to 6 m, i.e. crowns 4.2 m across on a 3.8 m lattice: every tree
      // overlapped its neighbour and the stand rendered as a solid dark wall —
      // the hedge again, in a different material. 0.85-1.15 on 3.0-5.4 m gives
      // 2.2-3.2 m crowns: a closed canopy that still has holes in it.
      const r = rng(1201);
      add += plant(sites.map(s => ({ x: s.x, y: s.y, z: s.z,
        h: Math.max(2.4, Math.min(5.4, s.h * (1.10 + r() * 0.95))), w: 0.85 + r() * 0.30 })),
        900 + st.length, P_AUTUMN, mix);
      n += sites.length;
    }
    const fl = feet('tree_field_trunks');
    if (fl.length) {
      drop += triCount(find('veg_field').geometry) + triCount(find('tree_field_trunks').geometry)
            + (find('veg_field_cards') ? triCount(find('veg_field_cards').geometry) : 0);
      hide('veg_field'); hide('tree_field_trunks'); hide('veg_field_cards');
      const r = rng(77);
      add += plant(fl.map(p => ({ x: p.x, y: p.y, z: p.z, h: 2.6 + r() * 3.0, w: 0.80 + r() * 0.35 })),
                   1313, P_AUTUMN, mix);
      n += fl.length;
    }
    return `F2 species mix — ${n} trees (conifer/broadleaf/scrub/snag), ${add} tris in, ${drop} out, net ${add - drop}`;
  }

  // ===========================================================================
  // F3 — LAYERED FOREST. ONE SPECIES, THREE STOREYS.
  // ===========================================================================
  // The other hypothesis: the wood is flat because it has no VERTICAL RANGE and
  // no holes, not because it has one species. Same broadleaf everywhere, but a
  // few emergents stand well clear of the roof, the main canopy varies 2x rather
  // than 1.4x, an understory fills the floor, and 18 % of the sites are dropped
  // outright so the wood has gaps you can see trunks and sky through.
  function f3() {
    let drop = 0, add = 0, n = 0, cut = 0;
    const LAY = [['broadleaf', 0.14, 6.4, 2.4, 0.62],    // emergents: tall and narrow
                 ['broadleaf', 0.56, 3.4, 2.2, 0.98],    // main canopy
                 ['scrub',     0.30, 1.9, 1.0, 1.20]];   // understory
    const place = (sites, seed) => {
      const r = rng(seed), out = { broadleaf: [], scrub: [] };
      for (const s of sites) {
        // 18 % was too many: at the Emberbrook gate the two stands came back as
        // five scattered bushes and the seam read EMPTIER than the hedge did,
        // which is the one outcome this lane is not allowed to produce.
        if (r() < 0.08) { cut++; continue; }             // the gaps ARE the candidate
        let t = r(), acc = 0, pick = LAY[1];
        for (const L of LAY) { acc += L[1]; if (t <= acc) { pick = L; break; } }
        out[pick[0]].push({ x: s.x, y: s.y, z: s.z, h: pick[2] + (r() - 0.5) * pick[3], w: pick[4] * (0.85 + r() * 0.3) });
      }
      let t2 = 0;
      for (const k of Object.keys(out)) if (out[k].length)
        t2 += plant(out[k], seed + k.length, P_FLAT, [[k, 1]]);
      n += out.broadleaf.length + out.scrub.length;
      return t2;
    };
    for (const st of ['whisperwood', 'farwall-crown', 'pocket-grove']) {
      const core = find('veg_canopy_' + st), cards = find('veg_canopy_' + st + '_cards');
      if (!core) continue;
      const sites = footprint('veg_canopy_' + st, 3.8);
      drop += triCount(core.geometry) + (cards ? triCount(cards.geometry) : 0);
      hide('veg_canopy_' + st); if (cards) hide('veg_canopy_' + st + '_cards');
      add += place(sites, 500 + st.length);
    }
    const fl = feet('tree_field_trunks');
    if (fl.length) {
      drop += triCount(find('veg_field').geometry) + triCount(find('tree_field_trunks').geometry)
            + (find('veg_field_cards') ? triCount(find('veg_field_cards').geometry) : 0);
      hide('veg_field'); hide('tree_field_trunks'); hide('veg_field_cards');
      add += place(fl, 631);
    }
    return `F3 layered — ${n} trees in 3 storeys, ${cut} sites cut for gaps, ${add} tris in, ${drop} out, net ${add - drop}`;
  }

  function census() {
    const out = {};
    for (const nm of ['veg_field', 'tree_field_trunks', 'veg_field_cards',
                      'veg_canopy_whisperwood', 'veg_canopy_whisperwood_cards',
                      'veg_canopy_farwall-crown', 'veg_canopy_farwall-crown_cards',
                      'veg_canopy_pocket-grove', 'veg_canopy_pocket-grove_cards']) {
      const o = find(nm); if (o) out[nm] = triCount(o.geometry);
    }
    out._formTris = Object.fromEntries(Object.entries(forms()).map(([k, v]) => [k, v.tris]));
    return out;
  }
  return { clear, f1, f2, f3, census, forms, footprint, feet };
})();
