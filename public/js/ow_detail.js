// ow_detail.js — THE OVERWORLD'S NEAR-FIELD GROUND: a blade carpet that follows the
// camera, and pixel-scale material on the terrain the carpet stands in.
//
// WHY IT IS RUNTIME AND NOT IN THE BUNDLE. Both halves are camera-relative. The refs
// (public/assets/refs/reimagine_ff9_overworld_{1,2,3}.jpg) carry blade geometry from the
// bottom of frame past the character; ours stopped a few metres in, so the meadow changed
// species mid-frame. Baking that density into ow-valley's GLB is not an option — the
// player walks the whole 280x200u region, so "dense wherever the player is" as static
// geometry is dense EVERYWHERE, which at the ~45/m2 this needs is millions of triangles in
// a 45 MB bundle. Placed against the live camera instead it costs no bytes at all, and the
// falloff can have the shape the refs have (thick at the near edge, thinning with depth)
// rather than the shape a static scatter can afford.
//
// WHAT IT IS NOT. It is CONTENT — geometry and materials. No fog, no AO, no bloom, no
// grading, no tone curve: those belong to the post-processing lane and nothing here may
// touch them (scope seam ratified 2026-08-04, docs/qa/ow-refs/LOOP.md).
//
// THE "DEAD NO-OP" THAT WASN'T (2026-08-04). The previous lane reported the ground detail
// material measured as a complete no-op and guessed at three.js's program cache. It is not:
// Material.customProgramCacheKey() returns onBeforeCompile.toString(), so assigning a new
// closure DOES change the key and DOES force a rebuild. Proved by patching diffuseColor to
// flat magenta through the same path — the terrain went magenta on the next frame, and the
// onBeforeCompile callback fired 3/3. The real defect was in the MEASUREMENT: mean
// |laplacian| over the frame cannot see a +/-17% multiply at 0.9-3.2 cycles/m, because at
// this camera those features are 10-30 px across and a 1 px laplacian is nearly blind to
// them. Pixel-diffing the two plates showed 15% of pixels moving by more than 2/255 — the
// shader was live the whole time and the instrument said nothing. Hence GRIT: the octave
// that matters is the one at ~0.1 m, and it is faded out by view depth so it never aliases
// into stipple at distance.
//
// COLLISION. Every mesh it adds is veg_-prefixed and is only ever scene.add()ed — never
// pushed into play3d's collide / walkRef / allMeshes, which are built once from the bundle.
// Both are needed: the name is what keeps it out if this is ever baked into a GLB. Verify
// in the ENGINE (tools/walk_engine_gate.mjs --scene ow-valley), never in the file.
//
// window.OWD — the instrument:
//   OWD.state()          counts, budget, last rebuild ms, current params
//   OWD.set({...})       any of the tunables below, then rebuilds
//   OWD.rebuild(force)   place the carpet at the player's current position
//   OWD.enable(false)    tear the carpet down and unpatch nothing (materials stay patched)
(function () {
  'use strict';

  // play3d.html is a classic script: its top-level const/let live in the shared global
  // lexical scope and are readable from here, but a missing one is a ReferenceError.
  var TH = function () { try { return THREE; } catch (e) { return window.THREE; } };
  var SCN = function () { try { return scene; } catch (e) { return null; } };
  var SKEY = function () {
    var s = null; try { s = SCENE; } catch (e) {}
    return s || new URLSearchParams(location.search).get('scene') || '';
  };

  var GROUP = 'veg_owd';
  var ON = true, MESH = null, IDX = null, SRC = null, LASTMS = 0, LASTAT = null, LASTT = 0;
  var PATCHED = {};

  // ---- tunables -----------------------------------------------------------------
  // dens0/r0/r1 are the ref SHAPE: full carpet under the character, thinning with depth,
  // zero past r1. Everything here is exposed on OWD.set() so the next lane can sweep it in
  // one Chrome launch instead of editing this file.
  var P = {
    dens0: 46,       // blades per m2 inside r0
    r0: 15,          // full density radius
    r1: 74,          // zero at this radius — set by the FRAME, not by taste: at boom 40 /
                     // pitch 0.61 the meadow still fills the top of the plate at 60 m, and
                     // a fade that ends inside the picture is a fade the player can SEE
                     // end, which is the whole deficit ("the blade layer visibly stops").
    tail: 1.30,      // falloff exponent; >1 keeps blades far out at low density
    budget: 220000,  // hard instance cap (x6 tris) — a safety valve, see rebuild()
    step: 9.0,       // rebuild once the player has moved this far
    minMs: 700,      // ...and never more often than this (see rebuild)
    // R6 (2026-08-04) HALVES THE BLADE. At 0.19-0.42 against a 1.45u character the
    // carpet measured knee-high and, at the meadow camera's 12 m boom, covered most of
    // the frame — the user's words were "enormous… green scribble". Ankle height on
    // this character is ~0.11-0.13, and that is what the refs' near grass reads as.
    hMin: 0.085, hMax: 0.235,
    hPow: 2.10,      // R6: heights are POWER-distributed, not uniform. A uniform draw
                     // between two numbers gives a crop, not a meadow — every blade
                     // lands in the same visual half of the range and the field has one
                     // silhouette height. >1 pushes the mass to the short end and leaves
                     // a thin tail of tall blades, which is what breaks the top edge up.
    wide: 0.030,     // blade half-width at the base (R6: 0.044 was chunky once the
                     // blades came down in height — the aspect ratio is what reads)
    grow: 0.45,      // extra height per r1 of distance — far blades read at fewer pixels
                     // (R6: 0.90 nearly doubled the tail and put the biggest cards where
                     // the frame is densest)
    slope: 0.62,     // reject triangles whose normal.y is below this (no grass on cliff)
    lift: 1.14,      // blade tint vs the ground it stands in, AFTER the texture mean is
                     // folded in (see texMean). >1 on purpose: the previous pass's carpet
                     // DARKENED the near field (gate L 0.457 -> 0.387 against REF1's 0.558).
                     // MEASURED, and it is a finding: raising this barely moves frame
                     // luminance (gate NEAR L50 0.375 / 0.380 / 0.385 at lift 1.40 / 1.70 /
                     // 2.00, postfx=off). The carpet darkens a frame by COVERAGE, not by
                     // albedo — chase that L back through density and exposure, not here.
                     // R6: 1.70 was compensating for the BACKFACE BUG below — half the
                     // carpet was rendering black, so the field was lifted to get its
                     // mean back. With the flip gone the same lift blows the near field
                     // out, so it comes down with it.
    jitV: 0.30,      // R6: per-instance VALUE jitter width (was a hardcoded 0.14, which
    jitH: 0.16,      // ...and HUE jitter width — green-vs-amber, which 0.14 of flat value
                     // could not give. A field of one hue is a texture; a field of many
                     // is vegetation. Both shrink with distance (see the jw comment).
    // ---- CLUMPING (R6) --------------------------------------------------------
    // The single biggest remaining "reads as noise rather than vegetation" term, and
    // the one that no per-blade jitter can supply: EVEN DENSITY IS THE TELL. A carpet
    // placed at a constant blades/m2 has no bare ground in it, so its top edge is a
    // continuous line across the frame and the eye reads one material, not plants.
    // Real turf is patches. Two octaves of world-space value noise multiply the local
    // density (and, more weakly, the height, because a thick tuft is also a tall one),
    // which costs one hash per triangle and no instances at all.
    clump: 0.95,     // 0 = the old even carpet; 1 = density swings 0..2x
    clumpM: 6.5,     // metres per clump cell — sized against a 1.45u character, so a
                     // patch is roughly four of her wide
    clumpH: 0.45,    // how much of the same field the blade HEIGHT follows
    grit: 0.42,      // ground material: amount of the pixel-scale octave
    gritFar: 30.0    // ...faded to nothing by this view depth, so it never stipples
  };

  // ---- the blade ------------------------------------------------------------------
  // Two quads tall with a lean and a baked base-to-tip value gradient. The gradient is
  // what stops a blade field reading as one flat colour no matter how many blades are in
  // it — the refs' grass has internal light variation inside a single clump.
  function bladeGeo() {
    var T = TH(), seg = 3, w = P.wide, h = 1.0, bend = 0.30;
    var Pp = [], N = [], U = [], C = [], I = [];
    for (var i = 0; i <= seg; i++) {
      var t = i / seg, tw = w * (1 - t * 0.85), y = h * t, z = bend * t * t;
      Pp.push(-tw, y, z, tw, y, z);
      // NORMALS POINT MOSTLY UP, not along the blade's own face. A blade card normal
      // (0,0.45,1) makes half the field face the low sun and half face away, and at
      // boom 40 — where a blade is 3-8 px — that per-blade contrast resolves as white
      // STIPPLE, not as grass (measured by eye on the first carpet: the meadow read as
      // frost). Shading them like the ground they stand in keeps the silhouette and
      // drops the noise; the value variation then comes from the baked tip gradient,
      // which is under our control, instead of from the light, which is not.
      // R6 MEASURED THE TILT AND IT WAS THE SPECKLE. 0.34 of lateral normal, against a
      // key at elevation 34 deg, swings a blade's own N.L from 0.24 to 0.81 depending on
      // which way it happens to be yawed — and yaw is uniform over 2*pi. That is a 3.4x
      // per-blade lighting range, i.e. exactly the stipple the comment above says it
      // exists to prevent, and it also put the AVERAGE blade at ~0.29 against the
      // ground's 0.56, which is why the carpet read as dark scribble over lit ground.
      // 0.14 keeps a trace of form (0.47..0.62) and lands the mean on the ground's own.
      N.push(0, 0.990, 0.14, 0, 0.990, 0.14);
      U.push(0, t, 1, t);
      var s = 0.72 + 0.36 * t;
      C.push(s, s, s, s, s, s);
    }
    for (var j = 0; j < seg; j++) { var a = j * 2; I.push(a, a + 1, a + 3, a, a + 3, a + 2); }
    var g = new T.BufferGeometry();
    g.setAttribute('position', new T.Float32BufferAttribute(Pp, 3));
    g.setAttribute('normal', new T.Float32BufferAttribute(N, 3));
    g.setAttribute('uv', new T.Float32BufferAttribute(U, 2));
    g.setAttribute('color', new T.Float32BufferAttribute(C, 3));
    g.setIndex(I);
    return g;
  }

  // ---- the source: the terrain's own GRASS primitive -------------------------------
  // Placing against the ground MESH rather than a height probe buys three things at once:
  // the exact surface y (no float above or sink below), the terrain's own COLOR_0 under
  // each blade (so the carpet is never a different green from the ground it stands in —
  // which is precisely the "changes species mid-frame" complaint), and the grass/dry/rock
  // slot choice for free, because the builder already split the terrain by slot and this
  // reads only the grass one.
  function source() {
    var sc = SCN(); if (!sc) return null;
    var hit = null;
    sc.traverse(function (m) {
      if (hit || !m.isMesh || !m.geometry) return;
      var n = m.name || '', mn = (m.material && m.material.name) || '';
      if (/^ground_valley_1$/.test(n) || mn === 'ow_f2_ter_grass') hit = m;
    });
    return hit;
  }

  // THE GROUND IS TEXTURE x COLOR_0, AND THE BLADES ONLY GET COLOR_0. Sampling the
  // terrain's vertex colour alone made the first carpet 1.5-2x brighter than the ground
  // it stood in, which at boom 40 is exactly the white frost the plate showed — the
  // terrain material is baseColorTexture * COLOR_0 (glTF can only multiply) and L3
  // deliberately pushed COLOR_0's grass to L 0.651 knowing a darker texture would come
  // back down over it. So measure the map's mean, in the shader's own colour space, and
  // fold it into the blade tint. Measured once per material; a texture that will not
  // draw (cross-origin, not yet decoded) leaves TEXMEAN null and the carpet falls back
  // to a flat factor rather than to a wrong one.
  var TEXMEAN = null;
  function texMean(mat) {
    if (TEXMEAN) return TEXMEAN;
    try {
      var img = mat && mat.map && mat.map.image;
      if (!img || !img.width) return null;
      var cv = document.createElement('canvas'); cv.width = cv.height = 24;
      var cxr = cv.getContext('2d', { willReadFrequently: true });
      cxr.drawImage(img, 0, 0, 24, 24);
      var d = cxr.getImageData(0, 0, 24, 24).data, s = [0, 0, 0];
      for (var i = 0; i < d.length; i += 4) { s[0] += d[i]; s[1] += d[i + 1]; s[2] += d[i + 2]; }
      var n = d.length / 4, out = [];
      for (var c = 0; c < 3; c++) {
        var u = s[c] / n / 255;
        out.push(u <= 0.04045 ? u / 12.92 : Math.pow((u + 0.055) / 1.055, 2.4)); // -> linear
      }
      TEXMEAN = out;
      return out;
    } catch (e) { return null; }
  }

  function index(mesh) {
    var g = mesh.geometry, pos = g.attributes.position, col = g.attributes.color;
    var ix = g.index; if (!ix) return null;
    mesh.updateWorldMatrix(true, false);
    var mw = mesh.matrixWorld.elements;
    var nv = pos.count, X = new Float32Array(nv), Y = new Float32Array(nv), Z = new Float32Array(nv);
    for (var v = 0; v < nv; v++) {
      var x = pos.getX(v), y = pos.getY(v), z = pos.getZ(v);
      X[v] = mw[0] * x + mw[4] * y + mw[8] * z + mw[12];
      Y[v] = mw[1] * x + mw[5] * y + mw[9] * z + mw[13];
      Z[v] = mw[2] * x + mw[6] * y + mw[10] * z + mw[14];
    }
    var nt = ix.count / 3, CELL = 8;
    var cells = new Map(), area = new Float32Array(nt), ny = new Float32Array(nt);
    for (var t = 0; t < nt; t++) {
      var a = ix.getX(t * 3), b = ix.getX(t * 3 + 1), c = ix.getX(t * 3 + 2);
      var ux = X[b] - X[a], uy = Y[b] - Y[a], uz = Z[b] - Z[a];
      var vx = X[c] - X[a], vy = Y[c] - Y[a], vz = Z[c] - Z[a];
      var cxn = uy * vz - uz * vy, cyn = uz * vx - ux * vz, czn = ux * vy - uy * vx;
      var len = Math.hypot(cxn, cyn, czn);
      area[t] = len * 0.5;
      ny[t] = len > 1e-9 ? Math.abs(cyn) / len : 0;
      var mx = (X[a] + X[b] + X[c]) / 3, mz = (Z[a] + Z[b] + Z[c]) / 3;
      var key = Math.floor(mx / CELL) + ',' + Math.floor(mz / CELL);
      var arr = cells.get(key); if (!arr) { arr = []; cells.set(key, arr); }
      arr.push(t);
    }
    return { X: X, Y: Y, Z: Z, ix: ix, col: col, nt: nt, CELL: CELL, cells: cells,
             area: area, ny: ny };
  }

  // WORLD-SPACE VALUE NOISE (R6), for the clump field. It is keyed on WORLD position,
  // not on the draw order, which is what makes a patch stay where it is across a
  // rebuild — a clump field derived from the per-call PRNG would reshuffle the meadow
  // every time the player walked 9 m, and a meadow that reshuffles is worse than a
  // meadow that is even.
  function vhash(a, b) {
    var s = (Math.imul(a | 0, 374761393) ^ Math.imul(b | 0, 668265263) ^ 0x9e3779b9) >>> 0;
    s = (s ^ (s >>> 13)) >>> 0; s = Math.imul(s, 1274126177) >>> 0;
    return ((s ^ (s >>> 16)) >>> 8) / 16777216;
  }
  function vnoise(x, z) {
    var xi = Math.floor(x), zi = Math.floor(z), xf = x - xi, zf = z - zi;
    var u = xf * xf * (3 - 2 * xf), v = zf * zf * (3 - 2 * zf);
    return (vhash(xi, zi) * (1 - u) + vhash(xi + 1, zi) * u) * (1 - v) +
           (vhash(xi, zi + 1) * (1 - u) + vhash(xi + 1, zi + 1) * u) * v;
  }
  function clumpAt(x, z) {
    var s = 1 / Math.max(0.5, P.clumpM);
    return vnoise(x * s, z * s) * 0.68 + vnoise(x * s * 2.7 + 11.3, z * s * 2.7 - 4.1) * 0.32;
  }

  // deterministic per-call PRNG: the same anchor always yields the same carpet, so a
  // plate is reproducible and a blade never twitches because the player turned round.
  function rngAt(x, z) {
    var s = (Math.imul(Math.round(x * 4) | 0, 374761393) ^
             Math.imul(Math.round(z * 4) | 0, 668265263) ^ 20260804) >>> 0;
    return function () { s = (Math.imul(s, 1664525) + 1013904223) >>> 0; return s / 4294967296; };
  }

  function clear() {
    var sc = SCN(); if (!sc) return;
    var g = sc.getObjectByName(GROUP);
    if (g) {
      g.traverse(function (n) {
        if (n.isMesh) { try { n.geometry.dispose(); n.material.dispose(); } catch (e) {} }
      });
      sc.remove(g);
    }
    MESH = null;
  }

  function rebuild(force) {
    var T = TH(), sc = SCN(), SIM = window.SIM;
    if (!ON || !T || !sc || !SIM || !SIM.pos) return null;
    if (softwareGL()) { clear(); return 0; }
    var p = SIM.pos();
    var now = (performance && performance.now) ? performance.now() : Date.now();
    if (!force) {
      if (LASTAT && Math.hypot(p.x - LASTAT.x, p.z - LASTAT.z) < P.step) return null;
      // A FLOOR ON HOW OFTEN THIS CAN COST 80 ms. Movement alone is not enough of a
      // guard: a harness that teleports (playthrough_test, transition_test, reach_probe)
      // clears the step test on every jump and would pay for a full rebuild each time.
      if (LASTT && now - LASTT < P.minMs) return null;
    }
    LASTT = now;
    if (!SRC || !sc.getObjectByName(SRC.name)) { SRC = source(); IDX = null; }
    if (!SRC) return null;
    if (!IDX) IDX = index(SRC);
    if (!IDX) return null;
    var t0 = (performance && performance.now) ? performance.now() : 0;

    var R = rngAt(p.x, p.z), cx = p.x, cz = p.z, r1 = P.r1, r0 = P.r0;
    // `budget` is a SAFETY VALVE, not a target. Cells are walked in x,z order, so a run
    // that actually hits the cap loses one whole side of the disc rather than thinning
    // evenly — visible as a straight edge in the carpet. At the shipped dens0/r1 the
    // worst frame measured is 177k against a 220k cap; if a future tune gets close,
    // lower dens0, do not raise the cap.
    var span = r1 - r0;
    var mats = [], cols = [], n = 0;
    var zone = SIM.zone ? SIM.zone : null;
    var m4 = new T.Matrix4(), q = new T.Quaternion(), up = new T.Vector3(0, 1, 0);
    var lean = new T.Quaternion(), axis = new T.Vector3();
    var vp = new T.Vector3(), vs = new T.Vector3();
    var c0 = IDX.CELL, i0 = Math.floor((cx - r1) / c0), i1 = Math.floor((cx + r1) / c0);
    var k0 = Math.floor((cz - r1) / c0), k1 = Math.floor((cz + r1) / c0);
    var COL = IDX.col, ix = IDX.ix, X = IDX.X, Y = IDX.Y, Z = IDX.Z;
    var TM = texMean(SRC.material) || [0.34, 0.34, 0.34];

    for (var ci = i0; ci <= i1 && n < P.budget; ci++) {
      for (var ck = k0; ck <= k1 && n < P.budget; ck++) {
        var list = IDX.cells.get(ci + ',' + ck);
        if (!list) continue;
        for (var li = 0; li < list.length && n < P.budget; li++) {
          var t = list[li];
          if (IDX.ny[t] < P.slope) continue;              // no grass growing out of cliff
          var a = ix.getX(t * 3), b = ix.getX(t * 3 + 1), c = ix.getX(t * 3 + 2);
          var mx = (X[a] + X[b] + X[c]) / 3, mz = (Z[a] + Z[b] + Z[c]) / 3;
          var d = Math.hypot(mx - cx, mz - cz);
          if (d > r1) continue;
          var fall = d <= r0 ? 1 : Math.pow(1 - (d - r0) / span, P.tail);
          // the clump field is sampled at the TRIANGLE, not per blade: a per-blade
          // sample thins a patch uniformly instead of moving its edge, which is the
          // even carpet again by another route.
          var cl = clumpAt(mx, mz);
          var want = IDX.area[t] * P.dens0 * fall * Math.max(0, 1 + P.clump * (2 * cl - 1));
          var k = Math.floor(want); if (R() < want - k) k++;
          for (var j = 0; j < k && n < P.budget; j++) {
            var u = R(), w = R();
            if (u + w > 1) { u = 1 - u; w = 1 - w; }
            var bx = X[a] + u * (X[b] - X[a]) + w * (X[c] - X[a]);
            var by = Y[a] + u * (Y[b] - Y[a]) + w * (Y[c] - Y[a]);
            var bz = Z[a] + u * (Z[b] - Z[a]) + w * (Z[c] - Z[a]);
            if (zone) { var zn = zone(bx, bz); if (zn === 'water') continue; }
            var dd = Math.hypot(bx - cx, bz - cz);
            // far blades get taller so they still subtend pixels; near blades stay ankle
            // height against the body. Without this the tail reads as bare ground with
            // dust on it, which is the same visible stop by another route.
            var h = (P.hMin + Math.pow(R(), P.hPow) * (P.hMax - P.hMin)) *
                    (1 + P.grow * (dd / r1)) *
                    (1 - P.clumpH * 0.5 + P.clumpH * cl);
            q.setFromAxisAngle(up, R() * Math.PI * 2);
            axis.set(Math.cos(R() * 6.283), 0, Math.sin(R() * 6.283));
            lean.setFromAxisAngle(axis, (R() - 0.5) * 0.55);
            q.multiply(lean);
            vp.set(bx, by - 0.015, bz);
            vs.set(0.8 + R() * 0.55, h, 0.8 + R() * 0.55);
            // flat floats, not 170k Matrix4 objects: the instanceMatrix wants exactly
            // this layout anyway, and the object form cost ~20 MB of transient garbage
            // on every rebuild for nothing.
            m4.compose(vp, q, vs);
            for (var e = 0; e < 16; e++) mats.push(m4.elements[e]);
            if (COL) {
              var cr = COL.getX(a) + u * (COL.getX(b) - COL.getX(a)) + w * (COL.getX(c) - COL.getX(a));
              var cg = COL.getY(a) + u * (COL.getY(b) - COL.getY(a)) + w * (COL.getY(c) - COL.getY(a));
              var cb = COL.getZ(a) + u * (COL.getZ(b) - COL.getZ(a)) + w * (COL.getZ(c) - COL.getZ(a));
              // per-blade tint jitter is deliberately SMALL and shrinks with distance:
              // near the body it is variety, far away it is the same stipple by another
              // name, because a 4 px blade is one sample of it.
              var dw = (1 - 0.7 * (dd / r1));
              var jw = P.jitV * dw;
              var jit = (1 - jw * 0.5) + R() * jw;
              // R6: the SECOND axis. Value jitter alone gives a field of one colour at
              // several brightnesses, which is still one colour; hue jitter rolls each
              // blade between a cooler green and the ground's own amber, which is what
              // the refs' grass does clump by clump. The two channels move OPPOSITE
              // ways so the blade's luminance is not disturbed by the hue draw.
              var hw = P.jitH * dw, hj = (R() - 0.5) * hw;
              cols.push(cr * TM[0] * P.lift * jit * (1 + hj),
                        cg * TM[1] * P.lift * jit * (1 - hj * 0.55),
                        cb * TM[2] * P.lift * jit * 0.98 * (1 - hj * 0.9));
            }
            n++;
          }
        }
      }
    }
    clear();
    if (!n) { LASTAT = { x: p.x, z: p.z }; return 0; }
    var mat = new T.MeshStandardMaterial({
      color: 0xffffff, roughness: 0.94, metalness: 0.0,
      vertexColors: true, side: T.DoubleSide
    });
    mat.name = 'veg_owd_blade';
    // ---- THE BACKFACE BUG (R6, 2026-08-04) -------------------------------------
    // HALF THE CARPET WAS RENDERING BLACK, and it is what the user saw as "hard black
    // alpha edges". There is no alpha in this material at all — the blade is solid
    // geometry — so the black was never a cutout. It is three.js's DOUBLE_SIDED normal
    // flip: `normal *= faceDirection` in normal_fragment_begin. bladeGeo() deliberately
    // points every normal UP (0, 0.94, 0.34 at the time; 0, 0.99, 0.14 now) so a blade
    // shades like the ground it stands in; on a back face that is negated — pointing at
    // roughly the dirt rather than the sky, i.e. at a direction which
    // receives neither the key nor the sky. Blade yaw is uniform over 2*pi, so ~half of
    // 177k instances were DOWN-facing, and the field read as green scribble over black.
    // Un-flipping the normal is the whole fix and costs two ALU ops: these normals are
    // authored, not derived, and there is no side of a blade that should be dark.
    // (The alternative — mirrored geometry at FrontSide — doubles the triangle count for
    // the same pixels.)
    //
    // AND IT MUST BE WRITTEN AS AN INCLUDE EDIT. The first version of this patch replaced
    // the chunk's own `float faceDirection = gl_FrontFacing ? 1.0 : - 1.0;` and MATCHED
    // NOTHING — three.js calls onBeforeCompile BEFORE resolveIncludes, so what the hook
    // is handed is the template with `#include <normal_fragment_begin>` still in it, not
    // the expanded chunk. The frames looked slightly better anyway (the height and jitter
    // changes landed in the same run) and the patch would have shipped as a no-op. Proved
    // by capturing sh.fragmentShader from inside the hook: 3942 chars, neither string
    // present. patchGround() below always replaced INCLUDES; this now does too.
    mat.onBeforeCompile = function (sh) {
      sh.fragmentShader = sh.fragmentShader.replace('#include <normal_fragment_begin>',
        '#include <normal_fragment_begin>\n' +
        '// owd: blade normals are authored (mostly +Y), never flipped by facing\n' +
        'normal = gl_FrontFacing ? normal : -normal;\nnonPerturbedNormal = normal;');
    };
    // No customProgramCacheKey override — Material's own default already returns
    // onBeforeCompile.toString(), which is unique to this closure, so there was nothing
    // to gain. (An earlier note here blamed a constant cache key for the black-frame bug
    // in play3d.html's owHearthOrb. THAT NOTE WAS WRONG and is corrected rather than
    // deleted: removing the override there did NOT fix the frame; the cause is elsewhere,
    // see the receipt in owHearthOrb. A wrong written interpretation is worse than none.)
    var im = new T.InstancedMesh(bladeGeo(), mat, n);
    im.instanceMatrix = new T.InstancedBufferAttribute(new Float32Array(mats), 16);
    if (cols.length === n * 3) {
      im.instanceColor = new T.InstancedBufferAttribute(new Float32Array(cols), 3);
      im.instanceColor.needsUpdate = true;
    }
    im.instanceMatrix.needsUpdate = true;
    im.frustumCulled = false;      // instanced bounds lie about a carpet this wide
    // R6: RECEIVE, DO NOT CAST. A carpet that ignores the shadow map is BRIGHTER than
    // the ground inside every tree shadow and darker than it outside — speckle in both
    // directions, and it undoes the terminator the lighting lane just bought. Receiving
    // costs one shadow-map lookup per fragment; casting would cost 174k instances in the
    // depth pass for shadows nothing can resolve at 3-8 px a blade.
    im.castShadow = false; im.receiveShadow = true;
    im.name = 'veg_owd_blades';    // veg_ => play3d's noStand test can never adopt it
    var g = new T.Group(); g.name = GROUP; g.add(im);
    sc.add(g);                     // scene ONLY: collide/walkRef/allMeshes are never touched
    MESH = im;
    LASTAT = { x: p.x, z: p.z };
    LASTMS = ((performance && performance.now) ? performance.now() : 0) - t0;
    return n;
  }

  // ---- pixel-scale ground material --------------------------------------------------
  // Three octaves of world-space value noise multiplied into diffuse. The finest is the
  // one that matters (gravel speckle in the worn dirt is most of what separates the refs'
  // path from ours) and it is also the one that aliases, so it is faded out by view depth.
  // Worn ground gets more of it than turf: the terrain builder already split those into
  // separate primitives, so "more grit on the dirt" is a per-material amount, not a mask.
  function patchGround() {
    var sc = SCN(); if (!sc) return 0;
    var AMT = { ow_f2_ter_grass: 0.62, ow_f2_ter_dry: 1.0, ow_f2_road: 1.15,
                ow_f2_dockpath: 1.0 };
    var n = 0;
    sc.traverse(function (m) {
      if (!m.isMesh || !m.material) return;
      var mn = m.material.name || '';
      if (!(mn in AMT) || PATCHED[m.material.uuid]) return;
      PATCHED[m.material.uuid] = true;
      var k = AMT[mn], mat = m.material;
      mat.onBeforeCompile = function (sh) {
        sh.uniforms.owdAmt = { value: P.grit * k };
        sh.uniforms.owdFar = { value: P.gritFar };
        sh.vertexShader = sh.vertexShader
          .replace('#include <common>', '#include <common>\nvarying vec3 vOWDW;\nvarying float vOWDD;')
          .replace('#include <begin_vertex>',
            '#include <begin_vertex>\nvOWDW = (modelMatrix * vec4(transformed,1.0)).xyz;\n' +
            'vOWDD = -(modelViewMatrix * vec4(transformed,1.0)).z;');
        sh.fragmentShader = sh.fragmentShader
          .replace('#include <common>', '#include <common>\n' +
            'varying vec3 vOWDW; varying float vOWDD;\n' +
            'uniform float owdAmt; uniform float owdFar;\n' +
            'float owdH(vec2 p){ return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453); }\n' +
            'float owdN(vec2 p){ vec2 i=floor(p),f=fract(p); f=f*f*(3.0-2.0*f);\n' +
            '  return mix(mix(owdH(i),owdH(i+vec2(1,0)),f.x),mix(owdH(i+vec2(0,1)),owdH(i+vec2(1,1)),f.x),f.y); }')
          .replace('#include <color_fragment>', '#include <color_fragment>\n' +
            '{ vec2 wp = vOWDW.xz;\n' +
            // ~1.4 m patches, ~0.35 m mottle, ~0.09 m grit. The grit is the one the eye
            // reads as material and the one that stipples at distance, so it alone is
            // faded out by depth.
            '  float grit = smoothstep(owdFar, owdFar*0.35, vOWDD);\n' +
            '  float v = owdN(wp*0.70)*0.42 + owdN(wp*2.90)*0.30 + owdN(wp*11.0)*0.28*grit;\n' +
            '  float amt = owdAmt * (0.55 + 0.45*grit);\n' +
            '  diffuseColor.rgb *= (1.0 - amt*0.5 + amt*v); }');
      };
      mat.needsUpdate = true; n++;
    });
    return n;
  }

  // ---- arming -----------------------------------------------------------------------
  // A SOFTWARE RASTERISER CANNOT AFFORD A CARPET, AND HALF THIS REPO'S GATES USE ONE.
  // tools/cdp.mjs:149 and transition_test.mjs:180 launch Chrome with
  // `--use-angle=swiftshader --disable-gpu`. The carpet is ~1.0 M triangles of alpha-free
  // but overdraw-heavy instancing; on the GPU path it costs nothing measurable, on
  // SwiftShader every one of those triangles is rasterised by the CPU. So the carpet is a
  // GPU feature: on a software context the module keeps the material patch (a few ALU ops
  // per fragment) and places no blades at all.
  // WHAT IS MEASURED AND WHAT IS NOT, stated plainly because the difference matters: the
  // DETECTION is measured — booted under the gates' own flags, OWD.state() comes back
  // {software:true, blades:0}. The saving is NOT isolated; this is a precaution taken
  // because the art is worthless in a SwiftShader frame anyway (nothing judges those
  // pixels) and a content change that makes the suite unrunnable gets reverted by
  // whoever is on call, rightly. Do not quote a speedup from this comment.
  var SOFT = null;
  function softwareGL() {
    if (SOFT !== null) return SOFT;
    SOFT = false;
    try {
      var ren = null; try { ren = R; } catch (e) {}
      var gl = ren && ren.getContext && ren.getContext();
      if (!gl) return SOFT;                       // undecided: retried on the next poll
      SOFT = null;
      var s = '';
      var dbg = gl.getExtension('WEBGL_debug_renderer_info');
      if (dbg) s += ' ' + (gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) || '');
      s += ' ' + (gl.getParameter(gl.RENDERER) || '') + ' ' + (gl.getParameter(gl.VENDOR) || '');
      SOFT = /swiftshader|softwar|llvmpipe|mesa offscreen/i.test(s);
      if (SOFT) console.warn('[owd] software WebGL (' + s.trim() + ') — blade carpet off');
    } catch (e) { SOFT = false; }
    return SOFT;
  }

  // `?owdetail=0` turns the whole module off — carpet AND material patch — so an A/B
  // capture never has to edit play3d.html to get a clean BEFORE. An art lane that has to
  // remove a script tag to photograph its own baseline will eventually photograph
  // somebody else's tree.
  function isOW() {
    try { if (new URLSearchParams(location.search).get('owdetail') === '0') return false; }
    catch (e) {}
    return /^ow-/.test(SKEY() || '');
  }

  var TICK = null, NPATCH = 0;
  function arm() {
    clear(); SRC = null; IDX = null; LASTAT = null; NPATCH = 0;
    if (TICK) { clearInterval(TICK); TICK = null; }
    if (!isOW()) return;
    // THE BUNDLE IS NOT LOADED YET. This module arms at DOMContentLoaded and on
    // 'eb-scene', and BOTH can land before ow-valley's 45 MB GLB has finished parsing —
    // at which point source() finds nothing and patchGround() patches nothing, silently
    // and forever. So arming only starts the poll; the poll is what does the work, and it
    // keeps retrying the material patch until the terrain actually exists. (A module that
    // decides at t=0 whether the world contains a thing is a module that ships off.)
    TICK = setInterval(function () {
      try {
        if (NPATCH < 2) NPATCH += patchGround();
        rebuild(false);
      } catch (e) {}
    }, 250);
  }

  window.OWD = {
    state: function () {
      return { on: ON, scene: SKEY(), software: softwareGL(), blades: MESH ? MESH.count : 0,
               ms: +LASTMS.toFixed(1), at: LASTAT, params: JSON.parse(JSON.stringify(P)),
               source: SRC ? SRC.name : null, tris: MESH ? MESH.count * 6 : 0 };
    },
    set: function (o) { for (var k in o) if (k in P) P[k] = o[k]; return rebuild(true); },
    rebuild: rebuild,
    enable: function (v) { ON = v !== false; if (!ON) clear(); else rebuild(true); return ON; }
  };

  if (typeof window !== 'undefined') {
    // self-arm at load AND on every in-place scene swap, which is the module contract
    // every module in this runtime keeps (see play3d.html's sgAnnounce comment).
    window.addEventListener('eb-scene', function () {
      try { arm(); } catch (e) { console.error('[owd] eb-scene', e); }
    });
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
      setTimeout(function () { try { arm(); } catch (e) { console.error('[owd] arm', e); } }, 0);
    } else {
      window.addEventListener('DOMContentLoaded', function () {
        try { arm(); } catch (e) { console.error('[owd] arm', e); }
      });
    }
  }
})();
