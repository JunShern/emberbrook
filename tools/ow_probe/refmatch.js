/* refmatch.js — overworld CONTENT treatment, measured against the real overworld refs.
 *
 * Injected into a live play3d.html by tools/ow_probe/ow_multi.mjs (--inject), after
 * tools/ow_probe/land.js, whose window.OWL supplies the zone raster and terrain probe.
 *
 * SCOPE (ratified 2026-08-04): this lane owns CONTENT — geometry and materials, what is
 * IN the scene. The post-processing lane owns everything after the scene renders: AO,
 * bloom, grading, DEPTH-BASED FOG, AA. Nothing here may build those. `s1` survives as a
 * MEASUREMENT ONLY (see its header) because its numbers are a finding the post lane needs.
 *
 * ALWAYS CAPTURE WITH `--extra postfx=off`. The composer is built for every RT scene, so
 * an unpinned before/after spans two lanes at once and cannot be attributed.
 *
 * WHAT THE REFS ESTABLISH, and what does NOT transfer.
 * public/assets/refs/reimagine_ff9_overworld_{1,2,3}.jpg are third-person overworld
 * gameplay at OUR shot type. Measured with imgstat.py on band crops (FAR/MID/NEAR = top/
 * middle/bottom third; under a downward camera the vertical axis IS a depth axis, so the
 * bands are comparable to theirs):
 *
 *   bmr_dark (blue minus red, dark quartile), FAR band minus NEAR band
 *     refs   REF1 +0.337   REF2 +0.164   REF3 +0.270      (far cool, near warm)
 *     ours   gate +0.009   meadow -0.057   gorge -0.079    (flat, and two run BACKWARDS)
 *
 * That gap is real. It is NOT ours to close, and a sweep proved fog cannot close it
 * anyway — see s1. Ours to close is the other half:
 *
 *   detail (mean |laplacian|), FAR -> MID -> NEAR
 *     REF3    12.9 -> 33.1 -> 34.7      (climbs into the near field)
 *     ours    21.1 -> 44.2 -> 33.8      (peaks mid, FALLS at the near field)
 *
 * In 3/3 of our frames near-field detail sits below mid-field. But BEWARE THIS METRIC:
 * mean |laplacian| cannot tell blades from vertex-colour mottling, and by it our near
 * field (33.8-43.0) already sits inside the refs' range (34.7-49.9). The eye disagrees
 * flatly — docs/qa/ow-refs is the photograph. What the refs have and we do not is
 * PIXEL-SCALE MATERIAL: gravel speckle in the worn dirt, individual blades with their own
 * silhouettes, grass fingering irregularly over the path edge. Ours is smooth vertex-
 * colour gradient with a few large flat star-shaped tufts. So detail is a tie-breaker
 * here, never the verdict.
 *
 * Nothing added here joins the walk set: instances are named veg_* and play3d.html:1282
 * keeps veg_ out of the walk geometry. Verified in the ENGINE, not the file.
 */
(() => {
  // INDIRECT eval `(0,eval)` is load-bearing: it always evaluates in GLOBAL scope, so it
  // sees play3d's top-level `const scene` (a classic script's lexical binding, NOT a
  // window property) and never this function's. A direct eval('scene') here resolves to
  // the `const scene` it is initialising and dies in the temporal dead zone (paid for).
  const _g = n => (0, eval)('typeof ' + n + ' !== "undefined" ? ' + n + ' : undefined');
  const THREE = window.THREE || _g('THREE');
  const scene = window.scene || _g('scene');
  if (!THREE || !scene) { console.warn('refmatch: no scene'); return; }

  const GROUP = 'veg_rm';
  const rng = s => () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296;
  const group = () => {
    let g = scene.getObjectByName(GROUP);
    if (!g) { g = new THREE.Group(); g.name = GROUP; scene.add(g); }
    return g;
  };

  /* ---- s1: FOG — MEASUREMENT ONLY, DO NOT SHIP FROM THIS LANE -------------------
   * Kept so the sweep is reproducible, because its result is a finding the post lane
   * needs. Shipped fog is Fog(0xd3e0e8, 34, 205). Sweep at the gorge/meadow FAR band,
   * postfx as-shipped, target = the day refs' FAR band (bmr_dark +0.19..+0.22,
   * S50 0.29..0.35):
   *
   *   cfg                       meadow bmr/S50      gorge bmr/S50
   *   base d3e0e8 34/205        -0.073 / 0.371      -0.092 / 0.305
   *   A    9ec4de 30/150        -0.031 / 0.289      -0.059 / 0.241
   *   B    8fb8d8 30/130        -0.017 / 0.256      -0.047 / 0.213
   *   C    9ec4de 40/190        -0.065 / 0.412      -0.091 / 0.328
   *   E    a8c8dc 44/210        -0.073 / 0.449      -0.097 / 0.342
   *
   * THE FINDING: fog cannot get there. The most aggressive setting (B) moves meadow
   * only +0.056 toward a target +0.26 away, and pays for it by dropping far-band
   * saturation to 0.256 — BELOW the refs' own floor of 0.286. It goes milky long before
   * it goes blue. The reason is structural: the refs' far band is a genuine distance
   * plane kilometres out; ours is ground and warm cliff at 60-120 m, and 60 m of air
   * cannot tint much before it just washes. Recommendation to the post lane: the cool
   * far field wants a DEPTH-GRADED HUE SHIFT (rotate toward blue while HOLDING
   * saturation), not a denser fog; and the shipped 34/205 is already near the best fog
   * alone can do, so leave it rather than trading saturation for an invisible hue gain.
   */
  const FOGSAVE = { v: null };
  function s1(o) {
    o = o || {};
    if (!scene.fog) return 'no fog';
    if (!FOGSAVE.v) FOGSAVE.v = { near: scene.fog.near, far: scene.fog.far, color: scene.fog.color.clone() };
    scene.fog.near = o.near != null ? o.near : 26;
    scene.fog.far = o.far != null ? o.far : 118;
    if (o.color != null) scene.fog.color.setHex(o.color).convertSRGBToLinear();
    return `fog ${scene.fog.near}..${scene.fog.far}`;
  }

  /* ---- bladeGeo: a FINE tapered blade ------------------------------------------
   * The shipped tufts are 6 single triangles ~0.25 m across lying near-flat, which at
   * boom 40 read as flat stars printed on the ground (docs/qa/ow-refs near-field crop,
   * left panel). The refs' blades are narrow, upright and numerous. Two quads tall with
   * a lean gives a silhouette that survives at ~10 px, which is what a 0.45 m blade
   * subtends at 35 m in this frame.
   */
  function bladeGeo(wIn) {
    // 0.030 m was sub-pixel at 35 m (~17.5 px/m) and aliased into stipple; 0.055 m with
    // dens 26 swung the other way and read as chunky spear leaves, not turf. The refs are
    // a CARPET: fine blades, high count. Width and count move together.
    const w = wIn != null ? wIn : 0.042, h = 1.0, bend = 0.28;
    const P = [], N = [], U = [], I = [];
    const seg = 3;
    // Baked vertical gradient: dark at the base, bright at the tip. The refs' grass has
    // internal light variation within a single clump — without it a blade field reads as
    // one flat colour no matter how many blades are in it.
    const C = [];
    for (let i = 0; i <= seg; i++) {
      const t = i / seg, tw = w * (1 - t * 0.85), y = h * t, z = bend * t * t;
      P.push(-tw, y, z, tw, y, z);
      N.push(0, 0.4, 1, 0, 0.4, 1);
      U.push(0, t, 1, t);
      const s = 0.45 + 0.55 * t;
      C.push(s, s, s, s, s, s);
    }
    for (let i = 0; i < seg; i++) {
      const a = i * 2;
      I.push(a, a + 1, a + 3, a, a + 3, a + 2);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(P, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(N, 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute(U, 2));
    g.setAttribute('color', new THREE.Float32BufferAttribute(C, 3));
    g.setIndex(I);
    return g;
  }

  /* ---- s4: NEAR-FIELD BLADES + PATH-EDGE ENCROACHMENT --------------------------
   * WHY NOT land.js's l2: l2 scatters by SEAM proximity (road verges and terrain-kind
   * edges). That is exactly why our detail peaks MID-frame — the seam crosses the middle
   * of the plate and the near field, which is open meadow, gets nothing. Density here is
   * driven by DISTANCE from the frame's near edge instead, which is the shape the refs
   * have. l2's `clumps` are additionally a regression at this camera (big faceted blobs
   * reading as debris; middle panel of the near-field crop) and are not used.
   *
   * Path edge: the road is the zone raster (Z_ROAD = 3), not a mesh. Blades are allowed
   * to spill INTO road cells with a probability that falls off over `spill` metres from
   * the boundary, which is what makes the ribbon's edge irregular instead of a decal.
   */
  function s4(o) {
    o = o || {};
    const OWL = window.OWL;
    if (!OWL) return 'no OWL';
    const Z = OWL.zones(), T = OWL.terrain();
    const cx = o.x != null ? o.x : SIM.pos().x, cz = o.z != null ? o.z : SIM.pos().z;
    const r0 = o.r0 != null ? o.r0 : 16;      // full density inside this radius
    const r1 = o.r1 != null ? o.r1 : 34;      // zero beyond this
    const dens = o.dens != null ? o.dens : 110; // blades per m2 at full density -- a carpet, not a scatter
    const spill = o.spill != null ? o.spill : 0.9;
    const R = rng(o.seed || 20260804);
    const step = 1 / Math.sqrt(dens);
    const rows = [];
    const M = new THREE.Matrix4(), q = new THREE.Quaternion(), up = new THREE.Vector3(0, 1, 0);
    const pos = new THREE.Vector3(), scl = new THREE.Vector3();
    for (let x = cx - r1; x <= cx + r1; x += step) {
      for (let z = cz - r1; z <= cz + r1; z += step) {
        const dx = x - cx, dz = z - cz, d = Math.hypot(dx, dz);
        if (d > r1) continue;
        // DETAIL FALLOFF: full near, thinning with distance. This is the ref shape.
        const fall = d <= r0 ? 1 : 1 - (d - r0) / (r1 - r0);
        if (R() > fall * fall) continue;
        const jx = x + (R() - 0.5) * step * 1.6, jz = z + (R() - 0.5) * step * 1.6;
        const t = T.at(jx, jz);
        if (!t || t.kind === 3) continue;         // no blades on rock
        const zone = Z.at(jx, jz);
        if (zone === 3) {
          // inside the road: allow a fringe that fades over `spill` m from the verge
          let near = false;
          for (let a = 0; a < 8 && !near; a++) {
            const th = a * Math.PI / 4;
            if (Z.at(jx + Math.cos(th) * spill, jz + Math.sin(th) * spill) !== 3) near = true;
          }
          if (!near || R() > 0.35) continue;
        }
        const y = t.y;
        if (!isFinite(y)) continue;
        const h = (0.15 + R() * 0.17) * (t.kind === 2 ? 0.7 : 1);   // shorter on dry ground
        q.setFromAxisAngle(up, R() * Math.PI * 2);
        const lean = new THREE.Quaternion().setFromAxisAngle(
          new THREE.Vector3(Math.cos(R() * 6.28), 0, Math.sin(R() * 6.28)), (R() - 0.5) * 0.5);
        q.multiply(lean);
        pos.set(jx, y - 0.02, jz);
        scl.set(0.8 + R() * 0.5, h, 0.8 + R() * 0.5);
        rows.push(new THREE.Matrix4().compose(pos, q, scl));
      }
    }
    if (!rows.length) return 'no blades';
    const geo = bladeGeo(o.w);
    // DO NOT clone the shipped ow_f2_matte here. It is authored with vertexColors:true
    // against the terrain's own COLOR_0, and a clone applied to blade geometry that has a
    // different colour attribute rendered the whole field near-black — the blades came out
    // as dead twigs (docs/qa/ow-refs, rejected-twigs). An explicit material with our own
    // baked tip gradient is both correct and controllable.
    const mat = new THREE.MeshStandardMaterial({
      color: o.color != null ? o.color : 0x7d9a44,
      roughness: 0.92, metalness: 0.0,
      vertexColors: true, side: THREE.DoubleSide,
    });
    mat.name = 'veg_rm_blade';
    const im = new THREE.InstancedMesh(geo, mat, rows.length);
    for (let i = 0; i < rows.length; i++) im.setMatrixAt(i, rows[i]);
    im.instanceMatrix.needsUpdate = true;
    im.frustumCulled = false;             // documented land.js trap: instanced bounds lie
    im.name = 'veg_rm_blades';            // veg_ => play3d.html:1282 keeps it out of the walk set
    im.castShadow = false; im.receiveShadow = false;
    group().add(im);
    return `blades ${rows.length}`;
  }

  /* ---- s5: PIXEL-SCALE GROUND MATERIAL -----------------------------------------
   * The refs' worn dirt carries gravel speckle and their grass carries blade-scale value
   * variation; ours is a smooth vertex-colour gradient, which is the loudest "untextured
   * blockout" tell in the plates. VERTEX COLOUR CANNOT FIX THIS: the terrain's vertices
   * are metres apart, so the finest thing it can represent is several metres across —
   * land.js's l3 already runs octaves down to a 1.9 m cell and the ground still reads
   * smooth. Pixel-scale detail has to come from the MATERIAL, so this is an
   * onBeforeCompile that multiplies world-space value noise into diffuse. It is a
   * material edit, not a post pass, and it adds no asset file.
   */
  const PATCHED = new Set();
  function s5(o) {
    o = o || {};
    const amt = o.amt != null ? o.amt : 0.34;
    const c1 = o.c1 != null ? o.c1 : 0.9;    // cycles/m -> ~1.1 m features, ~19 px at 35 m
    const c2 = o.c2 != null ? o.c2 : 3.2;    // cycles/m -> ~0.31 m grit, ~5 px at 35 m
    let n = 0;
    scene.traverse(m => {
      if (!m.isMesh || !m.material) return;
      if (!/^ground_valley_/.test(m.name || '')) return;
      const mat = m.material;
      if (PATCHED.has(mat.uuid)) return;
      PATCHED.add(mat.uuid);
      mat.onBeforeCompile = sh => {
        sh.uniforms.rmAmt = { value: amt };
        sh.uniforms.rmC1 = { value: c1 };
        sh.uniforms.rmC2 = { value: c2 };
        sh.vertexShader = sh.vertexShader
          .replace('#include <common>', '#include <common>\nvarying vec3 vRMW;')
          .replace('#include <begin_vertex>', '#include <begin_vertex>\nvRMW = (modelMatrix * vec4(transformed,1.0)).xyz;');
        sh.fragmentShader = sh.fragmentShader
          .replace('#include <common>', `#include <common>
varying vec3 vRMW; uniform float rmAmt; uniform float rmC1; uniform float rmC2;
float rmH(vec2 p){ return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453); }
float rmN(vec2 p){ vec2 i=floor(p),f=fract(p); f=f*f*(3.0-2.0*f);
  return mix(mix(rmH(i),rmH(i+vec2(1,0)),f.x),mix(rmH(i+vec2(0,1)),rmH(i+vec2(1,1)),f.x),f.y); }`)
          .replace('#include <color_fragment>', `#include <color_fragment>
{ float g = rmN(vRMW.xz*rmC1)*0.62 + rmN(vRMW.xz*rmC2)*0.38;
  diffuseColor.rgb *= (1.0 - rmAmt*0.5 + rmAmt*g); }`);
      };
      mat.needsUpdate = true; n++;
    });
    return `ground materials patched ${n}`;
  }

  function clear() {
    if (FOGSAVE.v && scene.fog) {
      scene.fog.near = FOGSAVE.v.near; scene.fog.far = FOGSAVE.v.far;
      scene.fog.color.copy(FOGSAVE.v.color);
    }
    const g = scene.getObjectByName(GROUP);
    if (g) { g.traverse(n => { if (n.isMesh) { n.geometry.dispose(); n.material.dispose(); } }); scene.remove(g); }
    if (window.OWL) window.OWL.clear();
    return 'cleared';
  }

  window.RM = { s1, s4, s5, clear };
  return 'RM ready';
})();
