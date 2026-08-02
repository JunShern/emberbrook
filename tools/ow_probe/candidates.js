/* candidates.js — OVERWORLD ART PROBE: runtime candidate treatments.
 *
 * NOTHING HERE SHIPS. Every candidate is injected into the LIVE ow-valley render
 * over CDP and photographed; the shipped bundle is never touched. The runtime is
 * the right instrument for this and Blender is not: ow-valley renders in real
 * time under play3d's own sun/ambient rig (the rig 69eadd3 just fixed), so a
 * Blender still would be a picture of a different lighting model.
 *
 * Adoption cost per candidate is stated on the gallery page; these are PREVIEWS
 * of a direction, at production density, not the production assets.
 */
window.OWC = (function () {
  const R3 = THREE;
  let G = null;

  // COLOUR: three r128 has NO input colour management, and play3d sets
  // R.outputEncoding = sRGBEncoding (play3d.html:100). A hex handed straight to
  // MeshStandardMaterial is therefore treated as LINEAR and gamma-encoded on the
  // way out — measured: every candidate in the first smoke run rendered chalk
  // white. GLTF materials come through GLTFLoader, which converts; injected ones
  // must convert themselves.
  const C = (hex) => new R3.Color(hex).convertSRGBToLinear();

  // deterministic RNG — a candidate must be re-photographable
  function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0;
    let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

  function group() {
    if (!G) { G = new R3.Group(); G.name = '__owc'; scene.add(G); }
    return G;
  }
  function clear() {
    if (!G) return;
    G.traverse(o => { if (o.isMesh) { o.geometry && o.geometry.dispose();
      (Array.isArray(o.material) ? o.material : [o.material]).forEach(m => m && m.dispose()); } });
    scene.remove(G); G = null;
    // restore anything a candidate mutated in place
    for (const [mat, saved] of MUT) Object.assign(mat, saved);
    MUT.clear();
  }
  // material mutations get an undo ledger — a candidate that cannot be taken back
  // is a commit, and this lane does not commit to the bundle
  const MUT = new Map();
  function mutate(mat, props) {
    if (!MUT.has(mat)) {
      const saved = {};
      for (const k of Object.keys(props)) saved[k] = mat[k];
      saved.color = mat.color && mat.color.clone();
      MUT.set(mat, saved);
    }
    Object.assign(mat, props); mat.needsUpdate = true;
  }
  function findMat(name) {
    let hit = null;
    scene.traverse(m => { if (!m.isMesh) return;
      for (const mm of (Array.isArray(m.material) ? m.material : [m.material]))
        if (mm && mm.name === name) hit = mm; });
    return hit;
  }

  // ---- ground sampling -------------------------------------------------------
  // SIM.floors is the collision BVH's own answer, so a scattered prop stands on
  // the surface the PLAYER stands on, not on the artist's idea of it.
  function groundY(x, z) { const f = SIM.floors(x, z); return (f && f.length) ? Math.max.apply(null, f) : null; }

  // Points near the walked road. Rejects the ribbon itself (props in the road are
  // a walk-network bug, not dressing) and rejects water.
  function corridor(n, minOff, maxOff, seed, zoneOk) {
    const road = window.__ROAD, r = rng(seed), out = [];
    let guard = 0;
    while (out.length < n && guard++ < n * 40) {
      const p = road[(r() * road.length) | 0];
      const a = r() * Math.PI * 2, d = minOff + r() * (maxOff - minOff);
      const x = p[0] + Math.cos(a) * d, z = p[1] + Math.sin(a) * d;
      const zn = SIM.zone(x, z);
      if (zn === 'road' || zn === 'water' || zn == null) continue;
      if (zoneOk && !zoneOk(zn)) continue;
      const y = groundY(x, z); if (y == null) continue;
      out.push([x, y, z, r]);
    }
    return out;
  }

  // ROAD HEADING — MEASURED TWO WAYS, AND THE RAY WALK LOST.
  // window.__ROAD is the zone grid's road cells in RLE SCAN order, so
  // road[i-1]->road[i] means "the next cell EAST", not "the next cell along the
  // road": the first rut pass believed it and laid a ladder of rungs across the
  // carriageway. The fix attempt — walk rays out from the cell and keep the
  // direction with the longest road run — was WORSE, and measurably so. Against a
  // PCA of the same 9 m neighbourhood at four corridor points the ray walk
  // returned 140/100/0/150 deg where PCA returned -29/-47/-26/-26, and the
  // corridor's own end-to-end bearing is -45. The road is only ~4 m wide, so a
  // 7.8 m ray leaves it in EVERY direction and the score is noise (6-8 of 12).
  // PCA over the neighbouring cells is the instrument that answers the question.
  function roadDir(p) {
    const R = window.__ROAD, near = [];
    // WINDOW RADIUS MUST BEAT THE ROAD WIDTH. At 9 m a 5 m-wide ribbon fills nearly
    // half the window across and only 9 m along, and PCA's major axis flips to ACROSS
    // the carriageway — which is exactly how the ruts came back crosswise at the town
    // gate even after the anisotropy gate was tightened. 18 m gives the along-road
    // extent a 3.6:1 head start over the width.
    for (const q of R) if (Math.abs(q[0] - p[0]) < 18 && Math.abs(q[1] - p[1]) < 18 &&
      Math.hypot(q[0] - p[0], q[1] - p[1]) < 18) near.push(q);
    if (near.length < 6) return null;
    let mx = 0, mz = 0;
    for (const q of near) { mx += q[0]; mz += q[1]; }
    mx /= near.length; mz /= near.length;
    let sxx = 0, sxz = 0, szz = 0;
    for (const q of near) { const a = q[0] - mx, b = q[1] - mz; sxx += a * a; sxz += a * b; szz += b * b; }
    const th = 0.5 * Math.atan2(2 * sxz, sxx - szz);
    // anisotropy: a junction blob is round and its major axis is meaningless
    const tr = sxx + szz, det = sxx * szz - sxz * sxz;
    const disc = Math.sqrt(Math.max(0, tr * tr / 4 - det));
    const l1 = tr / 2 + disc, l2 = tr / 2 - disc;
    let cx = Math.cos(th), cz = Math.sin(th);
    // VERIFY THE AXIS AGAINST THE GRID, AND FLIP IT IF THE GRID DISAGREES.
    // PCA was wrong at the town gate through three rounds of tuning (window radius,
    // anisotropy floor) and each round LOOKED like it might be the rotation instead —
    // the two failures are indistinguishable in a screenshot. So stop guessing which
    // one is broken and ask the road: step 3.5 m along the candidate axis and 3.5 m
    // across it, and keep whichever direction is still road on both sides. This is
    // self-checking, so a future map edit cannot silently reintroduce the ladder.
    const on = (ax, az) => (SIM.zone(p[0] + ax * 3.5, p[1] + az * 3.5) === 'road') &&
                           (SIM.zone(p[0] - ax * 3.5, p[1] - az * 3.5) === 'road');
    const along = on(cx, cz), across = on(-cz, cx);
    if (!along && across) { const t = cx; cx = -cz; cz = t; }
    else if (!along && !across) return null;
    return { a: Math.atan2(cz, cx), cx, cz, aniso: l2 > 1e-6 ? l1 / l2 : 999 };
  }

  // ---- geometry vocabulary ---------------------------------------------------
  function tuftGeo() {   // three crossed blades, tapered — reads as a clump, 6 tris
    const pos = [], g = new R3.BufferGeometry();
    for (let i = 0; i < 3; i++) {
      const a = i * Math.PI / 3, cx = Math.cos(a), cz = Math.sin(a), w = 0.045;
      pos.push(-cz * w, 0, cx * w, cz * w, 0, -cx * w, cx * 0.10, 1, cz * 0.10);
      pos.push(cz * w, 0, -cx * w, -cz * w, 0, cx * w, cx * 0.10, 1, cz * 0.10);
    }
    g.setAttribute('position', new R3.Float32BufferAttribute(pos, 3));
    g.computeVertexNormals(); return g;
  }
  function blobGeo(detail, jitter, seed) {
    const g = new R3.IcosahedronGeometry(1, detail), p = g.attributes.position, r = rng(seed);
    for (let i = 0; i < p.count; i++) {
      const s = 1 + (r() - 0.5) * jitter;
      p.setXYZ(i, p.getX(i) * s, p.getY(i) * s * 0.8, p.getZ(i) * s);
    }
    g.computeVertexNormals(); return g;
  }
  function crossGeo(w, h) {   // 2-quad billboard cross — flowers
    const g = new R3.BufferGeometry(), pos = [];
    for (const rot of [0, Math.PI / 2]) {
      const c = Math.cos(rot), s = Math.sin(rot);
      const P = (x, y, z) => pos.push(x * c - z * s, y, x * s + z * c);
      P(-w, 0, 0); P(w, 0, 0); P(w, h, 0); P(-w, 0, 0); P(w, h, 0); P(-w, h, 0);
    }
    g.setAttribute('position', new R3.Float32BufferAttribute(pos, 3));
    g.computeVertexNormals(); return g;
  }

  // one InstancedMesh per colour — instanceColor support varies by three build,
  // and a candidate that silently renders grey is a lie about the direction
  function instances(geo, colour, rough, list, place, borrow) {
    if (!list.length) return null;
    let mat;
    if (borrow) {
      // BORROW THE SHIPPED MATERIAL. A flat untextured colour beside a mapped crag
      // reads as pale plastic however far the hex is taken down (three rounds of
      // measured-by-eye darkening did not fix it). Cloning ow_f2_ter_rock gives the
      // candidate the same texture, the same recipe and — the point for adoption —
      // no new material at all. The borrowed material wants both a uv and a colour
      // attribute; IcosahedronGeometry ships uv, so only colour has to be added.
      const src = findMat(borrow);
      if (src) {
        mat = src.clone(); mat.side = R3.DoubleSide; mat.flatShading = true;
        if (colour) mat.color.copy(C(colour));
        if (mat.vertexColors && !geo.attributes.color) {
          const n = geo.attributes.position.count, a = new Float32Array(n * 3).fill(1);
          geo.setAttribute('color', new R3.BufferAttribute(a, 3));
        }
      }
    }
    if (!mat) mat = new R3.MeshStandardMaterial({ color: C(colour), roughness: rough == null ? 0.95 : rough,
      metalness: 0, side: R3.DoubleSide, flatShading: true });
    const im = new R3.InstancedMesh(geo, mat, list.length);
    const m = new R3.Matrix4(), q = new R3.Quaternion(), e = new R3.Euler(),
          v = new R3.Vector3(), s = new R3.Vector3();
    list.forEach((p, i) => { place(p, v, e, s); q.setFromEuler(e); m.compose(v, q, s); im.setMatrixAt(i, m); });
    im.instanceMatrix.needsUpdate = true;
    im.castShadow = true; im.receiveShadow = true;
    group().add(im); return im;
  }

  // ===========================================================================
  // A — GROUND / WAYSIDE
  // ===========================================================================

  // A1 MEADOW SCATTER: the corridor is a living meadow. Detail comes from PLANTS.
  function a1() {
    const tg = tuftGeo(), bg = blobGeo(1, 0.55, 7), fg = crossGeo(0.055, 0.16);
    const greens = ['#5d7a34', '#6f8c3c', '#4c6a2c', '#7d9a47'];
    greens.forEach((c, k) => {
      const pts = corridor(1400, 1.4, 15, 101 + k, z => z === 'meadow' || z === 'forest');
      instances(tg, c, 1.0, pts, (p, v, e, s) => { const r = p[3];
        v.set(p[0], p[1] - 0.03, p[2]); e.set(0, r() * 6.28, 0);
        const h = 0.16 + r() * 0.22; s.set(0.5 + r() * 0.4, h, 0.5 + r() * 0.4); });
    });
    ['#3f5a26', '#4d6b30'].forEach((c, k) => {
      const pts = corridor(210, 2.4, 17, 211 + k, z => z === 'meadow');
      instances(bg, c, 1.0, pts, (p, v, e, s) => { const r = p[3];
        const sc = 0.22 + r() * 0.42; v.set(p[0], p[1] + sc * 0.32, p[2]);
        e.set(0, r() * 6.28, 0); s.set(sc, sc * (0.7 + r() * 0.4), sc); });
    });
    // pops of colour — the ratified pillar; 3% of the scatter, warm against green
    // pale lilac was in the first pass and read as SCRAPS OF PAPER at 12 m — a
    // billboard cross only says 'flower' while it is small and warm.
    ['#d8b84e', '#c9743f', '#b8536a'].forEach((c, k) => {
      const pts = corridor(190, 1.6, 12, 331 + k, z => z === 'meadow');
      instances(fg, c, 0.85, pts, (p, v, e, s) => { const r = p[3];
        v.set(p[0], p[1], p[2]); e.set(0, r() * 6.28, 0); const h = 0.55 + r() * 0.5; s.set(h, h, h); });
    });
    return 'A1 meadow scatter';
  }

  // A2 TRODDEN WAY: the ground stays bare; the ROAD becomes a made thing.
  // Detail comes from HUMAN USE. Cheapest direction, fewest new assets.
  function a2() {
    const road = window.__ROAD, r = rng(55);
    // verge stones: step out from a road cell until the zone stops being road
    const verge = [];
    for (let i = 0; i < road.length; i += 2) {
      const p = road[i];
      for (const dir of [0, 1]) {
        const a = r() * Math.PI * 2;
        let hit = null;
        for (let d = 1.2; d < 7; d += 0.35) {
          const x = p[0] + Math.cos(a) * d, z = p[1] + Math.sin(a) * d;
          if (SIM.zone(x, z) !== 'road') { hit = [x, z]; break; }
        }
        if (!hit) continue;
        const y = groundY(hit[0], hit[1]); if (y == null) continue;
        if (r() < 0.45) verge.push([hit[0], y, hit[1], r]);
      }
    }
    const sg = blobGeo(0, 0.5, 9);
    instances(sg, '#6d5940', 0.95, verge, (p, v, e, s) => { const rr = p[3];
      const sc = 0.09 + rr() * 0.17; v.set(p[0], p[1] + sc * 0.3, p[2]);
      e.set(rr() * 0.6, rr() * 6.28, rr() * 0.6); s.set(sc * 1.4, sc, sc * 1.2); });
    // ruts: two darker strips just proud of the ribbon, following the centreline
    // RUTS: CUT FROM THIS CANDIDATE, AFTER FOUR MEASURED ROUNDS.
    // The idea was two cart ruts following the road. Getting them to follow it cost:
    //   1. scan-order finite differences  -> every rut due east (a ladder of rungs)
    //   2. longest-road-run ray walk      -> 140/100/0/150 deg where PCA said
    //                                        -29/-47/-26/-26 and the corridor's own
    //                                        bearing is -45. The road is ~4 m wide,
    //                                        so a 7.8 m ray leaves it in EVERY
    //                                        direction; the score was noise.
    //   3. PCA over 9 m, then 18 m, with an anisotropy floor -> right in the middle
    //                                        of the corridor, still crosswise at the
    //                                        town gate and on the shelf.
    //   4. PCA verified against the zone grid and flipped when it disagreed ->
    //                                        better near the body, still wrong in
    //                                        the foreground.
    // A RUT IS A CLAIM ABOUT DIRECTION, and four instruments could not make the claim
    // reliably from a 1.25 m zone raster. In production a rut is not geometry anyway:
    // it is a vertex-colour darkening of the road mesh, authored where the road
    // POLYLINE lives (tools/valley_map.py), which knows its own heading exactly and
    // needs none of this. Cut here so the plate carries no bug the eye must forgive.

    // waymarker posts every ~24 m, with a lit lamp head — the corridor gains a rhythm
    const postG = new R3.CylinderGeometry(0.09, 0.11, 1, 6), headG = new R3.BoxGeometry(1, 1, 1);
    const posts = [], heads = [];
    for (let i = 6; i < road.length; i += 40) {
      const p = road[i]; const a = r() * 6.28;
      for (let d = 2.2; d < 8; d += 0.4) {
        const x = p[0] + Math.cos(a) * d, z = p[1] + Math.sin(a) * d;
        if (SIM.zone(x, z) !== 'road' && SIM.zone(x, z) != null) {
          const y = groundY(x, z);
          if (y != null) { posts.push([x, y, z, r]); heads.push([x, y, z, r]); }
          break;
        }
      }
    }
    instances(postG, '#54402c', 0.98, posts, (p, v, e, s) => {
      v.set(p[0], p[1] + 0.95, p[2]); e.set(0, 0, 0); s.set(1, 1.9, 1); });
    const hm = new R3.MeshStandardMaterial({ color: C('#ffc98a'), emissive: C('#ffb85c'),
      emissiveIntensity: 1.7, roughness: 0.5 });
    const him = new R3.InstancedMesh(headG, hm, heads.length);
    const m4 = new R3.Matrix4();
    heads.forEach((p, i) => { m4.makeTranslation(p[0], p[1] + 2.05, p[2]);
      m4.scale(new R3.Vector3(0.2, 0.27, 0.2)); him.setMatrixAt(i, m4); });
    him.instanceMatrix.needsUpdate = true; group().add(him);
    // a wayside cairn at the corridor's midpoint — one landmark you can name
    const mid = road[(road.length * 0.5) | 0], cy = groundY(mid[0], mid[1] + 4);
    if (cy != null) {
      const cm = new R3.MeshStandardMaterial({ color: C('#6b6053'), roughness: 0.95, flatShading: true });
      for (let k = 0; k < 6; k++) {
        const s = 0.42 - k * 0.055, st = new R3.Mesh(blobGeo(0, 0.4, 300 + k), cm);
        st.position.set(mid[0] + (r() - 0.5) * 0.12, cy + 0.16 + k * 0.24, mid[1] + 4 + (r() - 0.5) * 0.12);
        st.scale.set(s, s * 0.55, s * 0.85); st.rotation.y = r() * 6.28;
        st.castShadow = st.receiveShadow = true; group().add(st);
      }
    }
    return 'A2 trodden way';
  }

  // A3 ROCK & SCREE: the corridor is a GORGE and the ground should say so.
  // Detail comes from GEOLOGY, and the hard grass/rock zone edge gets a talus apron.
  function a3() {
    // boulders: grass cells that are within 6 m of a crag cell — the wall foot
    const near = [], r = rng(77), road = window.__ROAD;
    let guard = 0;
    while (near.length < 260 && guard++ < 20000) {
      const p = road[(r() * road.length) | 0];
      const a = r() * 6.28, d = 3 + r() * 20;
      const x = p[0] + Math.cos(a) * d, z = p[1] + Math.sin(a) * d;
      const zn = SIM.zone(x, z); if (zn === 'road' || zn === 'water' || zn == null) continue;
      let byCrag = zn === 'crag';
      if (!byCrag) for (let k = 0; k < 8 && !byCrag; k++) {
        const t = k / 8 * 6.28;
        if (SIM.zone(x + Math.cos(t) * 5, z + Math.sin(t) * 5) === 'crag') byCrag = true;
      }
      if (!byCrag && r() > 0.22) continue;
      const y = groundY(x, z); if (y == null) continue;
      near.push([x, y, z, r]);
    }
    // VALUE, not hue, was what broke the first pass: mid-grey rock at roughness 1
    // under this key light reads chalk white beside a textured crag. Two stops down.
    // TINT MULTIPLIES the borrowed texture: mid-brown tints came out chocolate.
    // Keep the tints near white and let ow_f2_ter_rock's own map carry the hue.
    ['#f0e6d6', '#fffaf0', '#dfd2c0'].forEach((c, k) => {
      const sub = near.filter((_, i) => i % 3 === k);
      instances(blobGeo(0, 0.62, 400 + k), c, 0.98, sub, (p, v, e, s) => { const rr = p[3];
        const sc = 0.24 + rr() * rr() * 1.35;
        v.set(p[0], p[1] + sc * 0.28, p[2]);
        e.set((rr() - 0.5) * 0.5, rr() * 6.28, (rr() - 0.5) * 0.5);
        s.set(sc * 1.25, sc * 0.8, sc); }, 'ow_f2_ter_rock');
    });
    // scree: a dense fan of flat chips, tight to the wall — kills the paint-line edge
    const chips = [];
    guard = 0;
    while (chips.length < 1400 && guard++ < 60000) {
      const p = road[(r() * road.length) | 0];
      const a = r() * 6.28, d = 4 + r() * 22;
      const x = p[0] + Math.cos(a) * d, z = p[1] + Math.sin(a) * d;
      const zn = SIM.zone(x, z); if (zn === 'road' || zn === 'water' || zn == null) continue;
      let byCrag = false;
      for (let k = 0; k < 6 && !byCrag; k++) { const t = k / 6 * 6.28;
        if (SIM.zone(x + Math.cos(t) * 4, z + Math.sin(t) * 4) === 'crag') byCrag = true; }
      if (!byCrag) continue;
      const y = groundY(x, z); if (y == null) continue;
      chips.push([x, y, z, r]);
    }
    ['#f6ece0', '#e2d5c4'].forEach((c, k) => {
      instances(blobGeo(0, 0.7, 500 + k), c, 1.0, chips.filter((_, i) => i % 2 === k),
        (p, v, e, s) => { const rr = p[3]; const sc = 0.08 + rr() * 0.2;
          v.set(p[0], p[1] + sc * 0.2, p[2]); e.set((rr() - 0.5) * 0.7, rr() * 6.28, (rr() - 0.5) * 0.7);
          s.set(sc * 1.25, sc * 0.55, sc * 1.05); }, 'ow_f2_ter_rock');
    });
    // half-buried shelves breaking the grass, so the meadow reads as thin soil on rock
    const slabs = corridor(70, 3, 20, 611, () => true).filter(q => {
      for (let k = 0; k < 8; k++) { const t = k / 8 * 6.28;
        if (SIM.zone(q[0] + Math.cos(t) * 6, q[2] + Math.sin(t) * 6) === 'crag') return true; }
      return false; });
    instances(blobGeo(0, 0.3, 700), '#ece1d0', 1.0, slabs, (p, v, e, s) => { const rr = p[3];
      const w = 0.8 + rr() * 1.9; v.set(p[0], p[1] - 0.14, p[2]);
      e.set((rr() - 0.5) * 0.22, rr() * 6.28, (rr() - 0.5) * 0.22);
      s.set(w, 0.2 + rr() * 0.26, w * (0.5 + rr() * 0.6)); }, 'ow_f2_ter_rock');
    return 'A3 rock and scree';
  }

  // ===========================================================================
  // B — WATER   (one material, ow_f2_water; every option is a recipe, not geometry)
  // ===========================================================================
  function b1() {   // GLASS RIVER — real transparency, the bed reads through the shallows
    const m = findMat('ow_f2_water'); if (!m) return 'no water material';
    mutate(m, { transparent: true, opacity: 0.62, roughness: 0.06, metalness: 0.0,
      envMapIntensity: 1.0, depthWrite: false });
    m.color.copy(C('#bfe6ee'));
    return 'B1 glass river';
  }
  function b2() {   // SKY MIRROR — opaque, near-specular, takes the sky and the warm walls
    const m = findMat('ow_f2_water'); if (!m) return 'no water material';
    mutate(m, { transparent: false, opacity: 1, roughness: 0.02, metalness: 0.55,
      envMapIntensity: 1.4, depthWrite: true });
    m.color.copy(C('#8fb9c9'));
    return 'B2 sky mirror';
  }
  function b3() {   // WATERLINE — the edge is what is missing, not the colour
    // TWO IDEAS MEASURED AWAY BEFORE THIS ONE, both recorded because each was
    // killed by a number rather than by taste:
    //   (1) grade by DEPTH (surface y minus bed): SIM.floors answers with WALK
    //       floors and the riverbed is not collidable, so 4467 of 4548 vertices
    //       measured zero depth and the river came out one flat cyan.
    //   (2) grade by DISTANCE TO SHORE: the shore is real (695 welded boundary
    //       vertices) but water_river is 336 triangles over ~180 m — the triangles
    //       are wider than the river, so no interior vertex is far enough from a
    //       bank for any ramp to develop. Tightening the ramp to 3.5 m changed
    //       nothing visible. PER-VERTEX COLOUR CANNOT WORK ON THIS MESH.
    // What the mesh CAN carry is geometry on its boundary. Those same boundary
    // edges are the waterline; a pale strip laid along them gives the river an
    // edge, which is the thing a flat blue plate most conspicuously lacks.
    const m = findMat('ow_f2_water'); if (!m) return 'no water material';
    const pos = [], nrm = [];
    let edges = 0;
    scene.traverse(o => {
      if (!o.isMesh) return;
      const mats = Array.isArray(o.material) ? o.material : [o.material];
      if (!mats.includes(m)) return;
      const g = o.geometry, p = g.attributes.position;
      const idx = g.index, nTri = (idx ? idx.count : p.count) / 3;
      const weld = new Map(), wid = new Int32Array(p.count), wpos = [];
      for (let i = 0; i < p.count; i++) {
        const k = Math.round(p.getX(i) * 100) + '_' + Math.round(p.getY(i) * 100) + '_' + Math.round(p.getZ(i) * 100);
        if (!weld.has(k)) { weld.set(k, weld.size); wpos.push([p.getX(i), p.getY(i), p.getZ(i)]); }
        wid[i] = weld.get(k);
      }
      const key = (a, b) => a < b ? a + ':' + b : b + ':' + a;
      const use = new Map(), third = new Map();
      for (let t = 0; t < nTri; t++) {
        const i0 = idx ? idx.getX(t * 3) : t * 3, i1 = idx ? idx.getX(t * 3 + 1) : t * 3 + 1,
              i2 = idx ? idx.getX(t * 3 + 2) : t * 3 + 2;
        const w = [wid[i0], wid[i1], wid[i2]];
        for (let e = 0; e < 3; e++) {
          const k = key(w[e], w[(e + 1) % 3]);
          use.set(k, (use.get(k) || 0) + 1);
          third.set(k, w[(e + 2) % 3]);   // the opposite corner tells us which way is INWARD
        }
      }
      const v = new R3.Vector3(), W = 1.1;
      for (const [k, n] of use) {
        if (n !== 1) continue;
        const [ia, ib] = k.split(':').map(Number), ic = third.get(k);
        const A = wpos[ia], B = wpos[ib], Cc = wpos[ic];
        const mx = (A[0] + B[0]) / 2, mz = (A[2] + B[2]) / 2;
        let ix = Cc[0] - mx, iz = Cc[2] - mz;
        const L = Math.hypot(ix, iz) || 1; ix /= L; iz /= L;
        const seg = Math.hypot(B[0] - A[0], B[2] - A[2]);
        if (seg < 0.05) continue;
        const A2 = [A[0] + ix * W, A[1], A[2] + iz * W], B2 = [B[0] + ix * W, B[1], B[2] + iz * W];
        for (const q of [A, B, B2, A, B2, A2]) {
          v.set(q[0], q[1] + 0.06, q[2]); o.localToWorld(v);
          pos.push(v.x, v.y, v.z); nrm.push(0, 1, 0);
        }
        edges++;
      }
    });
    if (edges) {
      const g = new R3.BufferGeometry();
      g.setAttribute('position', new R3.Float32BufferAttribute(pos, 3));
      g.setAttribute('normal', new R3.Float32BufferAttribute(nrm, 3));
      const mat = new R3.MeshStandardMaterial({ color: C('#dcecf0'), roughness: 0.6, metalness: 0,
        transparent: true, opacity: 0.62, side: R3.DoubleSide, depthWrite: false });
      const mesh = new R3.Mesh(g, mat); mesh.renderOrder = 3; group().add(mesh);
    }
    mutate(m, { transparent: true, opacity: 0.9, roughness: 0.1, metalness: 0.0 });
    m.color.copy(C('#7fc0d2'));
    return 'B3 waterline  (' + edges + ' shore edges)';
  }

  return { clear, a1, a2, a3, b1, b2, b3, group, corridor, groundY,
    stats() { let t = 0, o = 0; if (G) G.traverse(m => { if (!m.isMesh) return; o++;
      const g = m.geometry, n = (g.index ? g.index.count : g.attributes.position.count) / 3;
      t += n * (m.isInstancedMesh ? m.count : 1); });
      return { objects: o, tris: Math.round(t) }; } };
})();
