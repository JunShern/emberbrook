// battle_world.js — BET 3 / BET A SPIKE: "FIGHT WHERE YOU STAND".
//
// STATUS: SPIKE, BEHIND A FLAG. Nothing in this file runs unless the page was
// opened with `?arena=world` (or `window.Battle.arena === 'world'` was set before
// a battle starts). With the flag off the module returns at line one of its IIFE
// having defined exactly one inert read-only object (window.BattleWorld) and
// having patched, wrapped, listened to or allocated NOTHING. That is the whole
// default-path regression argument and it is checkable in one expression:
// `BattleWorld.on === false && BattleWorld.installed === false`.
//
// ============================ WHAT IT PROVES ================================
// docs/plans/battle-presentation-inventory.md §10 BET A. Today a battle builds a
// SECOND WebGL context containing a procedural dish, a curved band carrying one
// of four 1344x768 Gemini plates keyed to the ZONE TYPE, a mist ribbon, 157
// scatter cones and a five-light hand rig with `scene.environment = null` and
// `NoToneMapping` — while 100% of encounters fire in `ow-valley`, which the page
// is ALREADY rendering with a solved key, a PMREM environment ("THE FILL IS THE
// SKY") and RenderPass -> GTAO -> bloom -> Output.
//
// ==================== AND IT NEVER FALLS BACK TO THE DIORAMA ================
// USER RULING 2026-08-08: "if we go with the world setup then we shouldn't be
// maintaining the diorama. Rather if we need a fallback, we should just fallback
// to the 'nearest feasible' place." A refusal therefore RELOCATES WITHIN THE
// WORLD — see stageArena and the measured ring/bearing ladder above it — and the
// line that used to call the diorama's own create() is gone. The DOM stage
// remains only as the crash guard on a thrown exception. `?arena=world` is still
// OPT-IN and battle_stage3d.js is still what a default page draws.
//
// This module stages the same fight in that live scene instead. It adds nothing
// to `collide`, `walkRef` or `allMeshes` (the followers.js rule — a combatant can
// never block the player, by construction), it creates NO renderer, NO camera and
// NO post chain, and it draws through `renderFrame()` — the page's one render, so
// a QA photograph is of the pipeline the player sees.
//
// ============================ HOW IT ATTACHES ===============================
// `battle_turnbased.js` calls `window.BattleStage3D.create(cfg)` and treats the
// return as an opaque 10-verb object (anchor / setActor / setTarget / act /
// flinch / setDead / cheer / destroy / tiers / frames + the cfg.onFrame
// callback). So the world arena is a DROP-IN for that return value: with the flag
// on we wrap `BattleStage3D.create` and answer with our own object. battle_stage3d
// is untouched; battle_turnbased is untouched; one flag selects the whole look.
//
// battle_stage3d.js is LAZILY INJECTED by battle_turnbased during the entry fade,
// so `window.BattleStage3D` does not exist at load. We install an accessor on
// window that patches the module the instant it is assigned, then hands the real
// object on. (Read-only pages, and any page where the module is already present,
// are handled by the direct branch.)
//
// ============================ WHAT IT DOES NOT DO ===========================
// A spike, not a product. Deliberately absent, and each one is future work rather
// than an oversight: the hit package beyond flash + shake + a ground ring; the
// pose-plate / pixel-sprite billboard tiers (a body that has no GLB gets the proxy
// solid and stays there); reduced-motion. Formation constants are BORROWED from
// BattleStage3D.CFG.form on purpose, so a side-by-side differs by the WORLD and
// not by the blocking.
//
// ==================== WAVE 3: THE SHOT LANGUAGE (BET B) =====================
// BET B is GATED ON THE DIORAMA and FREE HERE, and that asymmetry is the whole
// reason it was built in this file. assets/battle/MANIFEST.md states that the
// four backdrop plates were generated from a prompt carrying the arena camera's
// exact height, tilt and fov, and that "if the arena camera moves, this
// paragraph moves with it and the plates are re-shot". IN THE WORLD ARENA THERE
// IS NO BACKDROP, SO THE CAMERA IS FREE. Nothing below touches the diorama's
// camera, invalidates a plate, or changes what the flag-off game does.
// See CAM, solveShot, solveShotSafe (the 180-degree refusal) and the rig in
// tick(). Board: docs/qa/battle-camera/index.html. `?bcam=0` turns it off and
// leaves the spike's single solved pose, which is what the board's A/B is.
//
// ============================ THE CAMERA ====================================
// It does not touch `cam`. The overworld camera is recomputed from `window.ORBIT`
// + the player's position on EVERY frame of play3d's loop() — assigning to the
// camera would be overwritten 16 ms later. ORBIT is the world camera's own
// authoring surface (yaw / pitch / dist / panX,Y,Z), so the battle drives THAT and
// restores it field-by-field on teardown. This is also why the spike cannot leak a
// camera: there is no camera state of its own to leak, and play3d's own occlusion
// clamp (CAMCLIP) keeps running, which is the thing PT-20260803-025 was about.
(function () {
  'use strict';

  const HAS_DOM = typeof document !== 'undefined' && !!document.createElement;
  // THE FLAG, read once. `?arena=world` turns the spike on for the page.
  const Q = HAS_DOM && typeof location !== 'undefined'
    ? new URLSearchParams(location.search || '') : null;
  const FLAG = !!(Q && Q.get('arena') === 'world');
  // `?bcam=0` turns the shot language off and leaves the spike's single solved
  // pose. It exists so the before/after board is ONE BUILD with one switch —
  // the same discipline the KO lane's `--noreact` A/B used.
  const BCAM_OFF = !!(Q && Q.get('bcam') === '0');
  // `?btone=0` turns the tonal boom chooser off and leaves the geometric one.
  const BTONE_OFF = !!(Q && Q.get('btone') === '0');
  // `?bplace=0` turns the placement-quality term off and leaves the ladder's
  // own first-acceptance rule. One build, one flag — the same A/B discipline
  // `?bcam=0` and `?btone=0` were built with.
  const BPLACE_OFF = !!(Q && Q.get('bplace') === '0');

  if (!HAS_DOM) return;                       // node (battle_sim / encounter_sim): nothing at all
  if (!FLAG) {
    // THE DEFAULT PATH. One frozen object, no patch, no listener, no allocation.
    window.BattleWorld = Object.freeze({ version: 1, on: false, installed: false,
      why: 'flag off — open with ?arena=world' });
    return;
  }

  const T = () => (typeof window !== 'undefined' ? window.THREE : null);
  const now = () => (typeof performance !== 'undefined' ? performance.now() : Date.now());
  const clamp = (v, a, b) => (v < a ? a : v > b ? b : v);
  const lerp = (a, b, u) => a + (b - a) * u;

  // ---- THE WORLD HANDLES ---------------------------------------------------
  // play3d.html is ONE classic <script>, so its top-level `const scene`,
  // `const R` and `let cam` are GLOBAL LEXICAL bindings: they are not properties
  // of window, but any later classic script sees them by unqualified name. That
  // is the whole reason this spike needs no hook in a coordinator-owned file —
  // see the DAYLOG note. `typeof` guards keep a page without them silent.
  const W = {
    get scene() { try { return typeof scene !== 'undefined' ? scene : null; } catch (e) { return null; } },
    get cam() { try { return typeof cam !== 'undefined' ? cam : null; } catch (e) { return null; } },
    get R() { try { return typeof R !== 'undefined' ? R : null; } catch (e) { return null; } },
    get ch() { try { return typeof ch !== 'undefined' ? ch : null; } catch (e) { return null; } },
    get render() { return typeof window.renderFrame === 'function' ? window.renderFrame : null; },
  };
  function worldReady() {
    return !!(W.scene && W.cam && W.R && window.SIM && window.ORBIT);
  }

  // ---- TUNABLES ------------------------------------------------------------
  // Only the numbers this spike had to invent live here. Everything about the
  // FORMATION is read from BattleStage3D.CFG.form at create() time.
  const CFG = {
    // The overworld boom is 40 m at fov 42; the diorama frames at 11.6 m / fov 34.
    // Same subject height needs dist = 11.6 * tan(17deg) / tan(21deg) = 9.24 m, so
    // the battle pushes the boom in to roughly the diorama's read. Swept by eye
    // against the audit captures — see docs/qa/battle-world/index.html.
    cam: { dist: 9.6, pitch: 0.27, ms: 900 },
    // The formation is scaled DOWN from the diorama's, because the diorama's dish
    // is 20 m across and flat and the real valley road is not: the smaller the
    // footprint, the more of the distribution in §Q2 can stage a fight at all.
    scale: 0.72,
    lift: 0.0,               // metres above the sampled floor a body stands
    fx: { flashMs: 150, flash: 0.62, shakeMs: 260, shake: 0.10, shakeKo: 0.19,
          lungeM: 1.35, lungeMs: 620, flinchM: 0.42, flinchMs: 330, ringMs: 430 },
    // A body that cannot find real ground within this many metres of the sampled
    // column is REFUSED its slot and the solver tries the next candidate.
    place: { probeR: 0.42, maxDrop: 2.2, ring: [0, 0.5, -0.5, 1.0, -1.0, 1.6, -1.6],
             // the fraction of a body's own box that must have a clear line to
             // the battle camera before its slot is accepted (see visFrac)
             visMin: 0.67 },
  };

  // ======================= THE SHOT LANGUAGE (wave 3) ========================
  // BET B, built HERE and nowhere else. The diorama's camera is pinned to four
  // painted plates by `assets/battle/MANIFEST.md` ("if the arena camera moves,
  // this paragraph moves with it and the plates are re-shot"). In the world
  // arena there is no backdrop, so the camera is free — which is why a camera
  // language costs nothing here and a re-bake there.
  //
  // A SHOT IS DERIVED, NEVER TYPED. Every pose below is solved from the bodies
  // it has to show: their real positions, their own measured heights and their
  // own measured widths (the same discipline the contact fix used for the strike
  // station). What the table carries is INTENT — who is in frame, how much of
  // the frame they fill, how high the boom rides, how long the lens is, and how
  // long the move takes. Not one metre value in it is a camera position.
  //
  // AND IT NEVER CUTS. §11.11 of the inventory leaves "may the battle cut?" open
  // for the coordinator, so every transition here is a MOVE with an ease. `cut`
  // exists as a per-shot policy and every shipped value is `false`; flipping one
  // is a one-word change once the ruling lands.
  const CAM = {
    on: true,                 // ?bcam=0, or BattleWorld.CAM.on = false at runtime
    // THE LENS. play3d's own overworld camera is 42 deg vertical and this is the
    // only place in the battle that ever moves it (restored on teardown). A
    // longer lens is a legibility instrument, not a zoom: at a fixed framing it
    // pushes the eye back, which compresses the background and drops its spatial
    // frequency — the thing that makes a body read against rock and foliage.
    fov: { rest: 34, tight: 27, min: 24, max: 46 },
    dist: { min: 4.6, max: 24 },
    pitch: { min: 0.075, max: 0.52 },
    // A CAMERA THAT IS ALIVE. The audit measured the diorama's drift at a 103 s
    // period — a cycle no player ever sees a whole one of. This is 5.4 s.
    drift: { amp: 0.055, ms: 5400 },
    // THE BASE POSE IS SOLVED AGAINST THE TERRAIN, not chosen. See scoreView().
    solve: {
      // THE BAND IS NOT SYMMETRIC ABOUT THE SPIKE'S 0.27 ON PURPOSE. Dropping the
      // boom is what buys a background instead of a floor — but below ~0.15 the
      // NEAR ground rises into the frame and eats the fight, which is a measured
      // loss (crag: the low boom put both foes behind the crest of their own
      // slope and half the frame under a bank).
      pitches: [0.16, 0.22, 0.28, 0.34],
      // KEEP THE FIRST PLACEABLE YAW — how many placeable yaws go on to the
      // ranking, and it is ONE. Rank the PITCH axis; never re-pick the yaw. This
      // is where "the player's own current heading is ALWAYS tried first, so
      // where the world is open the camera does not swing" actually lives.
      // MEASURED, docs/qa/battle-world/factorial.json, 160 road cells per arm:
      // at 4 the camera swung off the player's heading on 89.3% of staged cells
      // against the spike's 49.0%, and BOUGHT NOTHING — a ranking scores
      // `okPlans` and every member of `okPlans` is already `ok`, so it cannot
      // make a cell fail (arms 5-6: best-of reproduced its yaw-only partner's
      // staging rate per zone, symmetric difference 0 cells). At 1 the staging
      // rate is unchanged — 103/160, THE SAME 103 CELLS, symmetric difference 0
      // — and yawTurned falls to 49.5%, the spike's own 49.0% to within half a
      // point. IN CELLS IT IS ALREADY BETTER THAN THE SPIKE: 52 staged cells keep
      // the player's heading here against the spike's 51, because the extra
      // pitches give that heading more chances to place than 0.27 alone did. The
      // rate reads 0.5 higher only because the pitch axis also staged 3 cells the
      // spike could not, and all three of those need a turn.
      // Set it back to 4 to reproduce the shipped arm.
      yawKeep: 1,
      backCap: 30,            // metres of clear depth behind a body that counts as "sky"
      wBack: 3.0, wBoom: 1.4, wPitch: 0.0,
    },
    // ---- THE TABLE ----------------------------------------------------------
    // show   : which bodies the shot is contractually about
    // fillH/V: the fraction of the frame the subject group spans, per axis
    // dPitch : boom elevation RELATIVE to the solved base (a strike rides low)
    // yawOff : radians around the arena, SIGNED BY HANDEDNESS and hard-refused
    //          if it would cross the axis (see axisOk)
    // lead   : push the subject off centre, in fractions of the half-frame
    // ms/ease: the move, never a cut
    shots: {
      round:   { show: 'all',    fillH: 0.86, fillV: 0.74, dPitch: 0.00, fov: 'rest',  yawOff: 0.00, lead: 0.00, ms: 900, ease: 'out',  cut: false },
      // `show:'actor'` resolves to the deciding body AND its current target when
      // the player has one — a "medium on the character deciding" that loses the
      // thing they are aiming at is not a shot, it is a bug with a lens on it.
      decide:  { show: 'actor',  fillH: 0.58, fillV: 0.50, dPitch: -0.02, fov: 'tight', yawOff: 0.30, lead: 0.12, ms: 620, ease: 'io',  cut: false },
      strike:  { show: 'pair',   fillH: 0.66, fillV: 0.58, dPitch: -0.07, fov: 'rest',  yawOff: 0.22, lead: 0.00, ms: 380, ease: 'io',  cut: false },
      impact:  { show: 'pair',   fillH: 0.78, fillV: 0.68, dPitch: -0.07, fov: 'rest',  yawOff: 0.22, lead: 0.00, ms: 170, ease: 'out', cut: false },
      // MEASURED AND LOOSENED: at 0.40/0.46 the push ended on a 5.4 m boom and
      // the fallen body filled the frame edge to edge — a close-up with no
      // ground, no ring and nobody else in it. A KO is a beat in a fight, not a
      // portrait; it keeps its neighbours.
      ko:      { show: 'victim', fillH: 0.30, fillV: 0.36, dPitch: 0.03, fov: 'tight', yawOff: 0.16, lead: 0.14, ms: 420, ease: 'out', cut: false,
                 // THE SLOW PUSH the KO lane wanted and refused: it runs across
                 // CFG.ko.holdMs — the beat where the body is already lying there
                 // — so the move is the thing that makes the hold legible rather
                 // than a pause. Ends before the dissolve begins.
                 push: { k: 0.86, ms: 1180, ease: 'lin' } },
      victory: { show: 'party',  fillH: 0.62, fillV: 0.66, dPitch: -0.05, fov: 'tight', yawOff: 0.95, lead: 0.00, ms: 780, ease: 'io',  cut: false,
                 // AND THE MOVE ONTO THE PARTY. yawOff swings the boom around to
                 // three-quarter FRONT of the party — it stops well short of the
                 // axis, so the shot the tally lands on is still on the same side
                 // of the line as every other shot in the fight.
                 push: { k: 0.88, ms: 900, ease: 'lin' } },
    },
  };

  // ============ WHAT WAS TRIED FIRST, MEASURED, AND DELETED ==================
  // AERIAL RE-ANCHOR (2026-08-09): play3d already ships an aerial-perspective
  // pass whose ramp R11 deliberately anchors on the PLAYER (`dRef` = lens-to-
  // character, `dNear` a 10 m offset past her). A battle is a different subject —
  // a fight up to 13 m wide that may have relocated 13 m from the player — so the
  // ramp was re-anchored onto the arena every frame, derived from the farthest
  // combatant's own distance from the lens, with the cast exempt BY ARITHMETIC
  // (t = 0 at every body) rather than by a `material.fog` list. Two uniform
  // writes, no shader, restored on teardown.
  // IT MEASURED ESSENTIALLY NULL AND IS GONE (docs/qa/battle-separation/sep-ab.json
  // and sep-sweep.json, four sites plus a strength ladder): edgeRGB 21.14->21.41,
  // 12.38->12.19, 13.36->12.12, 21.81->20.25 — two up, two down — against a
  // clutter fall of 2-13%. At scale 6 and 3 (a far harder ramp than the overworld's
  // 20) water read 13.59 -> 13.03 -> 12.66 and crag 21.34 -> 20.38 -> 20.23: the
  // contrast never moved.
  // THE REASON IS STRUCTURAL AND IT IS WORTH MORE THAN THE FEATURE: at three of the
  // four sites the background a body actually fails against is TWO TO FOUR METRES
  // BEHIND IT — a cliff face at water and crag, near grass at meadow — and no
  // distance-keyed cue can separate a body from something it is nearly touching.
  // Aerial perspective is a cue for the far band; the legibility problem is in the
  // near one. Do not re-open this without first measuring how far the offending
  // background actually is.

  const TONE = {
    on: true,                 // ?btone=0
    res: [320, 180],          // the probe target; the ranking is a mean, not a detail
    wClutter: 0.35,           // how much a busy background discounts a contrasty one
    // A REFUSAL, NOT A PREFERENCE: the probe may only overrule the geometric
    // solver when it beats the INCUMBENT rung's score by this fraction.
    // AND THE FIRST NUMBER WAS BACKWARDS, WHICH IS WHY IT IS WRITTEN DOWN. At
    // 0.35 the margin was inert everywhere it was supposed to help — forest
    // (0.74 -> 3.52, 4.7x) and crag (5.35 -> 9.36, 1.75x) clear any plausible bar
    // — and it bit ONLY at water, the one site where the axis is worth a factor
    // of 3.4, whose winner runs about 1.38x. Measured across four runs the water
    // decision fired three times and REFUSED once, which is a coin flip on the
    // whole result. A gate that only ever blocks the case it exists to pass is
    // not a gate. 0.15 keeps the shape (a decisive override, never a preference)
    // at a bar the evidence actually sits above.
    margin: 0.15,
    waitMs: 12000,            // give up waiting for models and keep the solver's pitch
  };

  function toneOn() { return !!(TONE.on && !BTONE_OFF); }

  // ============================ THE SOLVER ==================================
  // WHERE THE FIGHT STANDS. Given the player's position and a candidate camera
  // yaw, lay the diorama's own formation into world space with the party on
  // screen-LEFT and the foes on screen-RIGHT (CFG.partySide is the only place
  // handedness is written down in this game and it stays true here), then ask the
  // REAL WORLD three questions per slot:
  //
  //   1. IS THERE A FLOOR — SIM.ground within a step of the player's own, else the
  //      column census (SIM.floors) picked nearest the player's height, because on
  //      a valley wall the TOP surface is a cliff thirty metres up;
  //   2. DOES A BODY FIT — SIM.blocked, which returns the blocking MESH'S NAME;
  //   3. CAN THE CAMERA SEE IT — a ray from the BATTLE camera's pose (not the
  //      current one: we are about to move it) to the slot's chest, against
  //      `collide`. "In frame" is not "visible" and this repo has paid for the
  //      difference more than once. Without this the party can stage a perfectly
  //      legal fight behind a shack — measured, docs/qa/battle-world.
  //
  // A slot that fails walks the ring offsets in CFG.place.ring before it is called
  // impossible. Returns {ok, placed[], failed[], basis, occluded}
  // WHAT CAN HIDE A BODY IS NOT WHAT CAN BLOCK ONE. `collide` is deliberately
  // missing the ow region's foliage (it is `noStand`, so a player may walk through
  // a bush) — and a set that cannot see a bush reports a party standing INSIDE one
  // as perfectly visible. Measured: at the forest sample the whole party vanished
  // into the hedge bank with `occluded: 0`. So the visibility set is built from the
  // DRAWN scene instead, minus the things that are not occluders by construction:
  // walk meshes, the sky dome / ridge rings / haze veils (they are always behind
  // everything), the ambient particle systems, and our own bodies.
  // ---- AND GROUND SCATTER IS NOT AN OCCLUDER, WHICH IS WHERE THE SECONDS WERE -
  // MEASURED (docs/qa/battle-world/raycost.json, ow-valley, the shipped bundle):
  // one visibility ray against this set cost 11,696 us, and 11,629 us of it —
  // **99.4%** — was SIX InstancedMeshes of ground scatter: veg_owd_short (60,590
  // instances), _med (56,126), _seed (16,017), _weed, _flower, _sedge. 137,356
  // instances between them. Every other object in the valley — the two 27k-tri
  // terrain sheets, the whole town, the tree canopies, the hedge banks — costs
  // 4.2 us EACH, because play3d gives every ordinary mesh a three-mesh-bvh tree
  // and an accelerated raycast. An InstancedMesh gets neither: three's raycast
  // loops the instance list, so cost tracks INSTANCE COUNT and the tree with
  // 37,280 triangles is three thousand times cheaper than the grass with six.
  //
  // THE RULE IS DERIVED, NOT A NAME LIST: an instanced piece shorter than
  // SCATTER_H is ground detail. The player WALKS THROUGH it (play3d marks veg_
  // `noStand`, so it is not in `collide` either), and a knee-high tuft between
  // the boom and a body's ankle sample is a FALSE refusal — precisely the kind
  // the relocation ruling exists to stop paying for. The hedge bank that made
  // this set come from the drawn scene in the first place is NOT affected: it is
  // `veg_field` and `veg_canopy_whisperwood*`, ordinary meshes, still in.
  // Cost after the rule: 66 us/ray, one solvePlacement 278 ms -> 1.5 ms.
  const SCATTER_H = 1.5;
  const _scatH = typeof WeakMap === 'function' ? new WeakMap() : null;
  function pieceHeight(o) {
    if (_scatH && _scatH.has(o)) return _scatH.get(o);
    let h = Infinity;
    try {
      const g = o.geometry;
      if (g) {
        if (!g.boundingBox) g.computeBoundingBox();
        h = g.boundingBox.max.y - g.boundingBox.min.y;
        // the tallest instance decides, sampled — a scatter with one 4 m outlier
        // is not ground detail
        const im = o.instanceMatrix && o.instanceMatrix.array;
        if (im) {
          let s = 0;
          const n = o.count || (im.length / 16), step = Math.max(1, Math.floor(n / 64));
          for (let i = 0; i < n; i += step) {
            const b = i * 16;
            const sy = Math.sqrt(im[b + 4] * im[b + 4] + im[b + 5] * im[b + 5] + im[b + 6] * im[b + 6]);
            if (sy > s) s = sy;
          }
          h *= (s || 1);
        }
        h *= Math.abs(o.scale ? o.scale.y : 1);
      }
    } catch (e) { h = Infinity; }
    if (_scatH) _scatH.set(o, h);
    return h;
  }
  const _rc = { ray: null, v0: null, v1: null, set: null, stamp: 0, dropped: [] };
  const NOT_OCCLUDER = /^(__owsky|__owridge|__owveil|amb_|bw_)/;
  function occluders() {
    const TH = T();
    if (!TH) return null;
    let sc = null;
    try { sc = typeof scene !== 'undefined' ? scene : null; } catch (e) { return null; }
    if (!sc) return null;
    // rebuilt at most every 2 s: a battle is short and the region does not change
    if (_rc.set && (now() - _rc.stamp) < 2000) return _rc.set;
    const out = [], dropped = [];
    sc.traverse((o) => {
      if (!(o.isMesh || o.isInstancedMesh) || o.isSkinnedMesh) return;
      if (o.userData && (o.userData.isWalk || o.userData.isBattleWorld)) return;
      if (NOT_OCCLUDER.test(o.name || '')) return;
      let a = o;
      while (a) { if (a.userData && a.userData.isBattleWorld) return; a = a.parent; }
      if (!o.visible) return;
      if (o.isInstancedMesh && pieceHeight(o) < SCATTER_H) {
        dropped.push({ name: o.name || '(anon)', n: o.count, h: +pieceHeight(o).toFixed(2) });
        return;
      }
      out.push(o);
    });
    _rc.set = out; _rc.stamp = now(); _rc.dropped = dropped;
    return out;
  }
  function camPoseFor(P, yaw, pitch, dist) {
    const p = pitch == null ? CFG.cam.pitch : pitch, d = dist == null ? CFG.cam.dist : dist;
    return { x: P.x + Math.cos(yaw) * Math.cos(p) * d,
             y: P.y + 1 + Math.sin(p) * d,
             z: P.z + Math.sin(yaw) * Math.cos(p) * d };
  }
  // HOW FAR THE WORLD IS BEHIND A BODY — the whole legibility argument in one
  // ray. The spike's honest verdict was that the world loses on legibility
  // ("two clean silhouettes on a low-contrast painted field is a composition;
  // the valley is rock, foliage, houses and cast shadows"). What actually makes
  // a silhouette read is DEPTH BEHIND IT: a body with a cliff 1 m behind it is
  // camouflage, the same body with thirty metres of air behind it is a
  // silhouette. So the base pose is not chosen — it is searched, and this is
  // the thing it is searched on. Returns metres, capped.
  // TWO RAYS ARE NOT A SILHOUETTE — the spike's own named defect, and the thing
  // that let a party stand half behind a stilt with `occluded: 0`. This samples
  // the body's own BOX: three heights by three lateral offsets, using the
  // camera's own screen-right so the samples straddle the silhouette rather than
  // the world axes. Returns the fraction of the body that has a clear line.
  // MEASURED CONSEQUENCE: it is what demotes the crag's low boom, where the foes
  // sat behind the crest of the near slope and both centre rays cleared it.
  function visFrac(eye, x, y, z, h, w, yaw) {
    const rx = Math.sin(yaw), rz = -Math.cos(yaw);
    const hw = Math.max(0.12, (w || 0.7) * 0.42);
    let ok = 0, n = 0;
    for (const fy of [0.28, 0.62, 0.92]) {
      for (const fx of [-1, 0, 1]) {
        n++;
        if (seesPoint(eye, x + rx * hw * fx, y + h * fy, z + rz * hw * fx)) ok++;
      }
    }
    return n ? ok / n : 1;
  }
  function backDepth(eye, x, y, z) {
    const set = occluders();
    const TH = T();
    const cap = CAM.solve.backCap;
    if (!set || !set.length || !TH) return cap;
    if (!_rc.ray) { _rc.ray = new TH.Raycaster(); _rc.v0 = new TH.Vector3(); _rc.v1 = new TH.Vector3(); }
    _rc.v0.set(eye.x, eye.y, eye.z);
    _rc.v1.set(x - eye.x, y - eye.y, z - eye.z);
    const d0 = _rc.v1.length();
    if (d0 <= 0.01) return cap;
    _rc.ray.set(_rc.v0, _rc.v1.normalize());
    _rc.ray.far = d0 + cap;
    const hits = _rc.ray.intersectObjects(set, true);
    for (const h of hits) { if (h.distance > d0 + 0.35) return Math.min(cap, h.distance - d0); }
    return cap;
  }
  function seesPoint(eye, x, y, z) {
    const set = occluders();
    const TH = T();
    if (!set || !set.length || !TH) return true;
    if (!_rc.ray) { _rc.ray = new TH.Raycaster(); _rc.v0 = new TH.Vector3(); _rc.v1 = new TH.Vector3(); }
    _rc.v0.set(eye.x, eye.y, eye.z);
    _rc.v1.set(x - eye.x, y - eye.y, z - eye.z);
    const far = _rc.v1.length() - 0.35;      // stop short of the body itself
    if (far <= 0) return true;
    _rc.ray.set(_rc.v0, _rc.v1.normalize());
    _rc.ray.far = far;
    const hits = _rc.ray.intersectObjects(set, true);
    return hits.length === 0;
  }

  function solvePlacement(o) {
    const S = window.SIM;
    const P = o.at || S.pos();
    const yaw = o.yaw != null ? o.yaw : ((window.ORBIT && window.ORBIT.yaw) || 0);
    // play3d's own basis (see its pan handler): screen-right on the ground is
    // (sin yaw, -cos yaw); the direction INTO the screen is (-cos yaw, -sin yaw).
    const rx = Math.sin(yaw), rz = -Math.cos(yaw);
    const fx = -Math.cos(yaw), fz = -Math.sin(yaw);
    const k = o.scale == null ? CFG.scale : o.scale;
    const pitch = o.pitch == null ? CFG.cam.pitch : o.pitch;
    const eye = camPoseFor(P, yaw, pitch);
    const vis = o.vis !== false;
    const out = { basis: { yaw, pitch, right: [rx, rz], fwd: [fx, fz], centre: [P.x, P.y, P.z], eye },
                  placed: [], failed: [], occluded: 0 };

    for (const s of o.slots) {
      // s = {id, side, ax (across, party negative), az (depth, + = away)}
      let done = null, tries = 0, lastWhy = 'no floor';
      for (const jitter of CFG.place.ring) {
        tries++;
        const ax = s.ax * k, az = (s.az + jitter) * k;
        const x = P.x + rx * ax + fx * az;
        const z = P.z + rz * ax + fz * az;
        let y = S.ground(x, z, P.y);
        if (y == null) {
          const f = S.floors(x, z) || [];
          if (f.length) {
            let best = f[0];
            for (const v of f) if (Math.abs(v - P.y) < Math.abs(best - P.y)) best = v;
            if (Math.abs(best - P.y) <= CFG.place.maxDrop) y = best;
          }
        }
        if (y == null || Math.abs(y - P.y) > CFG.place.maxDrop) { lastWhy = 'no floor within ' + CFG.place.maxDrop + ' m'; continue; }
        const b = S.blocked(x, z, y);
        if (b) { lastWhy = 'blocked by ' + b; continue; }
        // NINE SAMPLES ACROSS THE BODY'S OWN BOX, not two rays down its spine.
        // A slot is refused when less than `visMin` of the body has a line to
        // the battle camera — the spike passed a body that was half behind a
        // stilt because its chest and head rays both cleared the post.
        // CHEAP FIRST, HONEST SECOND. The two spine rays reject most bad slots
        // for two raycasts; only a slot that survives them pays for the nine-
        // sample body test. Same verdict, a fraction of the cost — which matters
        // because the sweep is now yaw x pitch rather than yaw alone.
        if (vis) {
          if (!seesPoint(eye, x, y + 0.9, z) || !seesPoint(eye, x, y + 1.5, z)) {
            lastWhy = 'occluded from the battle camera'; out.occluded++; continue;
          }
          const vf = visFrac(eye, x, y, z, s.h || 1.7, s.w || 0.7, yaw);
          if (vf < CFG.place.visMin) { lastWhy = 'only ' + Math.round(vf * 100) + '% of the body is visible from the battle camera'; out.occluded++; continue; }
        }
        done = { id: s.id, side: s.side, h: s.h || 1.7, w: s.w || 0.8, x: x, y: y + CFG.lift, z: z,
                 yaw: Math.atan2(-rx * Math.sign(s.ax || 1), -rz * Math.sign(s.ax || 1)),
                 slot: [ax, az], drop: +(y - P.y).toFixed(3), tries: tries };
        break;
      }
      if (done) out.placed.push(done);
      else out.failed.push({ id: s.id, side: s.side, slot: [s.ax * k, s.az * k], why: lastWhy });
    }
    out.ok = out.failed.length === 0;
    const ys = out.placed.map(r => r.y);
    out.relief = ys.length ? +(Math.max.apply(null, ys) - Math.min.apply(null, ys)).toFixed(3) : null;
    return out;
  }

  // THE ARENA TURNS TO FACE A CLEAR VIEW. The fight is centred on the player, so
  // the only free variable is which way round the axis runs — and that is also the
  // camera's yaw, which the battle is going to drive anyway. Sweeping it is a
  // handful of raycasts and it converts most of the "there was a shack in the way"
  // failures into a fight the player can see. The player's own current heading is
  // ALWAYS tried first, so where the world is open the camera does not swing.
  // THE PITCH IS SOLVED TOO, AND ON THE SAME EVIDENCE. Given a placeable yaw,
  // score each candidate boom elevation by (a) how much clear depth sits behind
  // each body from that eye — the silhouette argument above — and (b) whether
  // the world intervenes between the eye and the arena, because play3d's CAMCLIP
  // would then haul the boom in and throw the framing away. A low boom is not
  // preferred on taste: it wins when the terrain lets it, and loses where a bank
  // behind the fight means the only clear background is the ground.
  function scoreView(plan, pitch) {
    const P = { x: plan.basis.centre[0], y: plan.basis.centre[1], z: plan.basis.centre[2] };
    const eye = camPoseFor(P, plan.basis.yaw, pitch);
    let back = 0, seen = 0, n = 0, backMin = 1e9;
    for (const r of plan.placed) {
      n++;
      const cy = r.y + (r.h || 1.5) * 0.6;
      seen += visFrac(eye, r.x, r.y, r.z, r.h || 1.7, r.w || 0.8, plan.basis.yaw);
      const bd = backDepth(eye, r.x, cy, r.z) / CAM.solve.backCap;
      back += bd;
      if (bd < backMin) backMin = bd;
    }
    if (!n) return { score: -1, back: 0, seen: 0, boom: false };
    // THE WORST-PLACED BODY IS THE ONE THAT FAILS TO READ, so the depth term is
    // half the mean and half the minimum — the same lesson BET G's staging solve
    // learned when pricing foe silhouette (score the mean first, the minimum
    // second; pricing only the mean buys a good average and one invisible body).
    const backScore = 0.5 * (back / n) + 0.5 * backMin;
    // the boom's own line, so the shot the solver picked is the shot CAMCLIP lets it keep
    const boomClear = seesPoint(eye, P.x, P.y + 1, P.z);
    const S = CAM.solve;
    // VISIBILITY DOMINATES. A background thirty metres deep is worth nothing if
    // the body in front of it is behind a crest: the weights are a ranking, and
    // this one is not close (measured — the crag's low boom scored best on
    // back-depth alone and hid both foes behind the near slope).
    const score = (seen / n) * 6
      + S.wBack * backScore
      + S.wBoom * (boomClear ? 1 : 0)
      - S.wPitch * (pitch / 0.31);
    return { score: +score.toFixed(4), back: +(back / n * CAM.solve.backCap).toFixed(2),
             seen: +(seen / n).toFixed(3), of: n, boom: boomClear, pitch: +pitch.toFixed(3) };
  }
  // THE ARENA TURNS **AND THE BOOM RISES** TO FIND A CLEAR VIEW. The spike swept
  // yaw at one fixed elevation and took the first yaw that placed. With the
  // camera free there is a second axis for nothing: a slot that no yaw can see
  // at 0.27 rad is often in plain sight from 0.34, because the thing in the way
  // is a crest rather than a wall.
  // THE TWO AXES ARE NOT SELECTED THE SAME WAY, AND THAT ASYMMETRY IS THE POINT.
  // The YAW is still the spike's rule — the FIRST that places, the player's own
  // heading first of all (CAM.solve.yawKeep = 1, and the receipt is written
  // there). Only the PITCH is ranked, by scoreView: nine-sample body visibility
  // with clear background depth as the tie-break. Ranking yaw as well was
  // measured and reverted — it cost 39.8 points of "the camera did not swing"
  // and bought zero staging sites, because scoring plans that are all already
  // `ok` cannot change which cells stage.
  // THE YAW LADDER, in one place, because two things now walk it: solveArena
  // itself and the geometry screen that decides which of its rungs solveArena is
  // even allowed to pay for (see screenYaws).
  const YAWS = [0, 0.5, -0.5, 1.05, -1.05, 1.6, -1.6, 2.1, -2.1, Math.PI];
  function solveArena(o) {
    const base = (window.ORBIT && window.ORBIT.yaw) || 0;
    // `o.yaws` restricts the sweep to a subset of YAWS **IN YAWS' OWN ORDER**.
    // That ordering is the whole correctness argument for the cheap screen: the
    // subset is a superset of the yaws that can place with vis:true, so the
    // FIRST member of the subset that places is the first member of the full
    // list that places, and the plan returned is the same object it would have
    // been. (See screenYaws for why the superset relation holds.)
    const cands = o.yaws ? YAWS.filter(d => o.yaws.indexOf(d) >= 0) : YAWS;
    const pitches = camOn() ? CAM.solve.pitches : [CFG.cam.pitch];
    let best = null;
    const okPlans = [];
    for (const d of cands) {
      for (const pit of pitches) {
        const plan = solvePlacement(Object.assign({}, o, { yaw: base + d, pitch: pit }));
        plan.yawDelta = +d.toFixed(3);
        if (plan.ok) {
          okPlans.push(plan);
          // WITHOUT THE CAMERA LANGUAGE THIS IS THE SPIKE'S OWN BEHAVIOUR, to
          // the line: the first yaw that places, at the one fixed pitch. The A/B
          // on this page is one build, one flag.
          if (!camOn()) return plan;
          break;                       // this yaw is solved; stop sampling pitch
        }
        if (!best || plan.placed.length > best.placed.length) best = plan;
      }
      // AND AT yawKeep = 1 THIS IS THE SPIKE'S YAW RULE WITH THE CAMERA ON: the
      // first yaw that places is the only one that reaches the ranking below, so
      // the ranking can only move the boom. A larger yawKeep re-opens best-of.
      if (okPlans.length >= CAM.solve.yawKeep) break;
    }
    if (!okPlans.length) return best;
    let win = null;
    for (const plan of okPlans) {
      for (const p of CAM.solve.pitches) {
        const s = scoreView(plan, p);
        if (!win || s.score > win.s.score) win = { plan: plan, s: s };
      }
    }
    win.plan.basis.pitch = win.s.pitch;
    win.plan.view = win.s;
    return win.plan;
  }
  function camOn() {
    return !!(CAM.on && !BCAM_OFF);
  }

  // ==================== THE RELOCATION LADDER (the ruling) ====================
  // "THE BATTLE FIGHTS IN THE REAL WORLD, AND THERE IS NO DIORAMA FALLBACK"
  // (user ruling 2026-08-08). A refusal RELOCATES WITHIN THE WORLD; it does not
  // switch arenas. The ladder below is the one tools/battle_world_probe.mjs
  // `--relocate` measured over 160 ow-valley road cells:
  //
  //   ring 0 (where the player stands) -> 5 m -> 8 m -> 11 m -> 13 m,
  //   EIGHT BEARINGS A RING, first ring/bearing the solver accepts wins.
  //
  // MEASURED: 5 m -> 89.4% of cells, 8 m -> 98.8%, 13 m -> 100%, and 15 / 20 /
  // 30 / 40 / 60 / 100 m are all flat at 100% — everything past 13 m is dead
  // weight, which is why the ladder stops there. ZERO residual class. Every
  // accepted site was re-confirmed through this same solveArena, 160/160 planOk.
  // Relocation distance p50 5.0 m, p90 8.0, max 13.0 — one sideways step, which
  // is what makes the opening camera move sufficient and a fade/cut/travel beat
  // unjustified.
  //
  // THE BINDING VARIABLE IS BEARING, NOT DISTANCE: 41 of the 57 cells the old
  // search refused stage at the SAME 5 m radius on a different compass bearing.
  // A search that walks one direction out and asks the solver once was measuring
  // its own first guess, not the world.
  //
  // THE ARENA MOVES, THE PLAYER DOES NOT. The player's own body is hidden for
  // the fight and drawn as a combatant in the formation (see chSaved), so
  // centring the arena on a neighbouring cell puts the party THERE and leaves
  // nothing behind — the same picture a teleport would give, with the teardown
  // obligation discharged by construction: this path never calls SIM.tp(), so
  // "the player is returned exactly where they stood" cannot fail. The camera
  // reaches the new centre through ORBIT's pan, which play3d applies relative to
  // the player's live position every frame.
  const RELOC = {
    // {R metres, ph phase in radians, n bearings}. The 13 m ring is offset half a
    // step so its bearings decorrelate from the rings below it — the probe's own
    // rule, kept so the shipped ladder IS the measured one.
    rings: [{ R: 0, ph: 0, n: 1 }, { R: 5, ph: 0, n: 8 }, { R: 8, ph: 0, n: 8 },
            { R: 11, ph: 0, n: 8 }, { R: 13, ph: Math.PI / 8, n: 8 }],
    // How far the arena's floor may sit above or below the player's own. The
    // ladder is a sideways step, not a climb: without this a 13 m ring can find
    // standable ground on a valley shelf ten metres up and stage the fight on a
    // ledge the player is looking up at.
    maxRise: 4.0,
  };
  // A CANDIDATE CENTRE, asked of the ENGINE. Column census first (on a valley
  // wall the top surface is a cliff thirty metres up, so `floors` is a list and
  // the nearest rung to the player is the one they could be standing on), then
  // the body test SIM.blocked — which is also the thing that returns the
  // blocking mesh's name when a bearing is refused.
  function centreAt(x, z, P0) {
    const S = window.SIM;
    const f = (S.floors(x, z) || []).filter(v => isFinite(v));
    if (!f.length) return null;
    let y = f[0];
    for (const v of f) if (Math.abs(v - P0.y) < Math.abs(y - P0.y)) y = v;
    if (Math.abs(y - P0.y) > RELOC.maxRise) return null;
    if (S.blocked(x, z, y)) return null;
    return { x: x, y: y, z: z };
  }
  // THE CHEAP SCREEN, AND WHY IT CANNOT CHANGE A VERDICT. `vis:false` is a
  // STRICT RELAXATION of `vis:true` — solvePlacement's visibility branch can
  // only ever REJECT a slot the geometry already accepted — so a yaw that cannot
  // lay the formation down geometrically cannot place with the camera test on
  // either, at ANY pitch (with vis off, pitch is not read at all: it feeds only
  // `eye`, and `eye` is only used inside the visibility branch). So the yaws this
  // returns are a SUPERSET of the yaws solveArena could have accepted, and
  // restricting the sweep to them leaves the returned plan identical.
  // IT IS THE WHOLE PERFORMANCE ARGUMENT: a refused candidate costs ten
  // raycast-free placements instead of ten yaws x four pitches of nine-sample
  // body visibility. The probe verified the equivalence empirically as well
  // (`--verify`, 10 candidates, 0 disagreements against the real solveArena).
  function screenYaws(o) {
    const base = (window.ORBIT && window.ORBIT.yaw) || 0;
    const out = [];
    for (const d of YAWS) {
      const p = solvePlacement(Object.assign({}, o, { yaw: base + d, vis: false }));
      if (p.ok) out.push(d);
    }
    return out;
  }
  // ============ IS THIS A GOOD PLACE TO FIGHT (wave 5, 2026-08-09) ===========
  // Everything above this point asks only whether bodies can STAND somewhere and
  // whether the camera can SEE them. Both are satisfied almost everywhere — and
  // the places the ladder then picks are bad: it staged on a bare rock dome, in
  // a building's shadow, inside a hedge bank, ON A ROOF, and once with the lens
  // inside a leaf. All legal. NOBODY HAD EVER MEASURED THE DIFFERENCE.
  //
  // THE DEFINITION IS DERIVED FROM A SORT, NOT FROM TASTE. 62 sites — the whole
  // ow-valley encounter band at 5 m spacing — were staged as REAL battles,
  // photographed through the player's own pipeline, and sorted by eye into
  // good/acceptable/bad BEFORE any number was read (docs/qa/battle-placement/
  // sort.json). Only then was every recorded axis asked how well it separates
  // the piles. What won, and what did not, is in that board; the short version:
  //
  //   * SUN EXPOSURE of the placed bodies separates good from bad at AUC 0.902
  //     / balanced accuracy 0.917 — good sites average 39% of the cast in
  //     shadow, bad sites 86% — and it costs FOUR RAYS.
  //   * "how much of the frame ONE surface owns" is marginally the best axis of
  //     all (AUC 0.922) but needs a RENDER; its ray-grid proxy is much weaker
  //     (0.79) and costs 52 ms a candidate, so it is measured on the board and
  //     NOT shipped in the search.
  //   * THE AXIS THE SOLVER ALREADY OPTIMISES BARELY SEPARATES: `view.back`
  //     (clear depth behind a body) reads AUC 0.733, and `view.seen` 0.657
  //     because it is ~0.99 everywhere by construction.
  //   * SKY / HORIZON PRESENCE IS NOT THE AXIS (AUC 0.68, and 0.556 for where
  //     the horizon sits) — almost no frame in this valley contains sky.
  //   * RELOCATION DISTANCE PREDICTS NOTHING (AUC 0.450). Where the ladder puts
  //     the fight relative to the player has no bearing on whether it reads.
  //   * AND THE SHIPPED TONAL METRIC RUNS BACKWARDS ACROSS SITES: silhouette
  //     edgeRGB ranks the three piles at 0.291 concordance — good sites average
  //     8.9 against bad sites' 17.3, because a lit body against near-black is
  //     enormous RGB contrast and is exactly the pile a human calls bad. TONE is
  //     not wrong at its own job (choosing a boom AT one site) but it is not a
  //     placement metric and must never be used as one.
  //
  // SO THE TERM IS SUN EXPOSURE, AND IT IS A REFUSAL RATHER THAN A PREFERENCE —
  // the same shape TONE's margin has, for the same reason. The ladder's "the
  // fight stays where you are" property is worth keeping; a challenger has to
  // move at least HALF THE CAST out of shadow (sunMargin 0.5) before it takes
  // the site. Measured over the 62 cells that bar fires on 23 and leaves 38
  // alone, and it touches only 2 of the 9 sites already sorted good.
  const PLACE = {
    on: true,                 // ?bplace=0
    sunMargin: 0.5,           // a challenger must light this much more of the cast
    // How many rings past the FIRST ACCEPTING ONE the search keeps collecting.
    // The ladder normally returns on its first acceptance, and ring 0 accepts at
    // most cells, so without this there is no second candidate to prefer and the
    // term is inert by construction. At 1 the choice set measured 9.4 candidates
    // (p50 10, max 17).
    extraRings: 1,
    // A BUDGET, NOT A HOPE. Collecting stops when the solve has already spent
    // this long, so the worst case is bounded by the same clock the staging
    // budget is stated in (p50 16 ms / max 407 ms before this change).
    budgetMs: 260,
    sunRay: 120,              // metres of shadow-caster to look through
    // THE TWO SHORT-CIRCUITS BELOW ARE AN OPTIMISATION, NOT A RULE, so they get
    // a switch: `PLACE.fastPath = false` evaluates every candidate and must
    // return the identical site. tools/battle_place.mjs --mode=equiv drives both
    // arms in ONE page with ORBIT.yaw pinned (the yaw ladder is relative to the
    // live camera heading, so two separate runs are not comparable — six sites
    // "differed" that way before the pin went in, and none of them was the
    // optimisation).
    fastPath: true,
  };
  function placeOn() { return !!(PLACE.on && !BPLACE_OFF); }
  // THE KEY LIGHT, out of the live scene rather than a constant: play3d solves
  // the town/overworld sun per rig and "THE FILL IS THE SKY" replaced the flat
  // hemisphere, so the one directional light left IS the sun. Cached beside the
  // occluder set and invalidated with it.
  let _sunDir = null, _sunStamp = 0;
  function sunDir() {
    const TH = T();
    if (!TH) return null;
    if (_sunDir && (now() - _sunStamp) < 2000) return _sunDir;
    let sc = null;
    try { sc = typeof scene !== 'undefined' ? scene : null; } catch (e) { return null; }
    if (!sc) return null;
    let d = null, bestI = 0;
    sc.traverse((o) => {
      if (!o.isDirectionalLight || !(o.intensity > bestI)) return;
      const p = new TH.Vector3().setFromMatrixPosition(o.matrixWorld);
      const t = o.target ? new TH.Vector3().setFromMatrixPosition(o.target.matrixWorld) : new TH.Vector3();
      const v = p.sub(t);
      if (v.lengthSq() < 1e-6) return;
      d = v.normalize(); bestI = o.intensity;
    });
    _sunDir = d; _sunStamp = now();
    return d;
  }
  // WHAT FRACTION OF THE CAST STANDS IN THE LIGHT. One ray per placed body from
  // its own chest toward the key light, against the SAME occluder set the
  // visibility test uses — so "in shadow" here means "geometry this search can
  // see is between this body and the sun", never a guess from a shadow map.
  function sunLit(plan) {
    const dir = sunDir(), TH = T(), set = occluders();
    if (!dir || !TH || !set || !set.length || !plan || !plan.placed.length) return null;
    if (!_rc.ray) { _rc.ray = new TH.Raycaster(); _rc.v0 = new TH.Vector3(); _rc.v1 = new TH.Vector3(); }
    let lit = 0;
    for (const r of plan.placed) {
      _rc.v0.set(r.x, r.y + (r.h || 1.6) * 0.6, r.z);
      _rc.ray.set(_rc.v0, dir);
      _rc.ray.far = PLACE.sunRay;
      if (!_rc.ray.intersectObjects(set, true).length) lit++;
    }
    return lit / plan.placed.length;
  }

  // WHERE THIS FIGHT STANDS. Walks the ladder and returns a site, or null — and
  // null here means the world refused every bearing on every ring, which the
  // sweep has never once seen. Callers treat null as a crash guard, not as a
  // fallback.
  // IT NO LONGER RETURNS ON THE FIRST ACCEPTANCE (see PLACE above): it finishes
  // the ring that first accepted, walks `extraRings` more, and prefers a
  // materially sunnier site among them. THE INCUMBENT IS STILL THE FIRST
  // ACCEPTANCE IN LADDER ORDER, so with `?bplace=0` — or with no sun in the
  // scene, or no challenger clearing the margin — the answer is byte-for-byte
  // what the ladder returned before, including its `cands/screened/solved`
  // counters up to that point.
  function stageArena(slots) {
    const S = window.SIM;
    const p = S.pos();
    const P0 = { x: p.x, y: p.y, z: p.z };
    const t0 = now();
    let cands = 0, screened = 0, solved = 0, best = null;
    const whys = [];
    const accepted = [];
    let firstRingIdx = -1, stop = false;
    for (let ri = 0; ri < RELOC.rings.length && !stop; ri++) {
      const ring = RELOC.rings[ri];
      if (firstRingIdx >= 0 && ri > firstRingIdx + PLACE.extraRings) break;
      if (accepted.length && now() - t0 > PLACE.budgetMs) break;
      for (let a = 0; a < ring.n && !stop; a++) {
        const th = ring.ph + a * Math.PI * 2 / ring.n;
        const at = ring.R === 0 ? P0
          : centreAt(P0.x + Math.cos(th) * ring.R, P0.z + Math.sin(th) * ring.R, P0);
        if (!at) continue;
        cands++;
        const viable = screenYaws({ slots: slots, at: at });
        if (!viable.length) { screened++; continue; }
        solved++;
        const plan = solveArena({ slots: slots, at: at, yaws: viable });
        if (plan && plan.ok) {
          const site = { plan: plan, at: at, R: ring.R,
                         bearing: +(th % (Math.PI * 2)).toFixed(3),
                         d: +Math.hypot(at.x - P0.x, at.z - P0.z).toFixed(2),
                         dy: +(at.y - P0.y).toFixed(2),
                         cands: cands, screened: screened, solved: solved,
                         ms: Math.round(now() - t0) };
          // THE OLD RETURN, kept exactly, behind the flag.
          if (!placeOn()) return site;
          if (firstRingIdx < 0) firstRingIdx = ri;
          site.lit = sunLit(plan);
          accepted.push(site);
          if (site.lit == null) return site;      // no sun in this scene: nothing to rank on
          // TWO SHORT-CIRCUITS, AND BOTH ARE PROVABLY THE SAME ANSWER — the
          // reason for writing them down is that the naive version cost 159 ms
          // of solve at p50 and these give most of it back for nothing.
          // (1) `lit` is a fraction, so it cannot exceed 1: if the INCUMBENT is
          //     already within `sunMargin` of fully lit, no candidate can clear
          //     the bar and the rest of the search cannot change the result.
          //     Measured: fires on 22 of the 62 sampled cells.
          // (2) Candidates are generated in (ring, bearing) order and the
          //     tie-break is sunniest -> nearest -> earliest bearing, so the
          //     FIRST candidate that is fully lit AND clears the margin is
          //     exactly the one the ranking below would choose. 19 of 62.
          if (PLACE.fastPath && accepted[0].lit + PLACE.sunMargin > 1 + 1e-9) { stop = true; continue; }
          if (PLACE.fastPath && site !== accepted[0] && site.lit >= 1 - 1e-9 &&
              site.lit >= accepted[0].lit + PLACE.sunMargin) { stop = true; continue; }
          if (accepted.length > 1 && now() - t0 > PLACE.budgetMs) { stop = true; }
          continue;
        }
        if (plan) {
          // kept ONLY for cfg.forcePlace, the QA lever that stages a fight the
          // world refused so a picture of the refusal can be taken
          if (!best || plan.placed.length > best.placed.length) { best = plan; best.__at = at; }
          for (const f of plan.failed) if (whys.length < 8) whys.push(f.why);
        }
      }
    }
    if (accepted.length) {
      // THE INCUMBENT IS THE LADDER'S OWN ANSWER — first acceptance, in ladder
      // order — and it is never assumed to be the worst (TONE's own lesson).
      const inc = accepted[0];
      let win = inc;
      for (const c of accepted) {
        if (c.lit < inc.lit + PLACE.sunMargin) continue;
        // among challengers that clear the bar: sunniest, then NEAREST, then the
        // ladder's own bearing order. Deterministic, and it keeps the ruling's
        // "one sideways step" shape rather than wandering for a marginal gain.
        if (win === inc || c.lit > win.lit + 1e-9 ||
            (Math.abs(c.lit - win.lit) < 1e-9 && c.R < win.R)) win = c;
      }
      win.quality = { on: true, axis: 'sunLit', margin: PLACE.sunMargin,
                      incLit: +inc.lit.toFixed(3), lit: +win.lit.toFixed(3),
                      moved: win !== inc, choices: accepted.length,
                      incR: inc.R, litOf: accepted.map(c => +c.lit.toFixed(2)) };
      win.cands = cands; win.screened = screened; win.solved = solved;
      win.ms = Math.round(now() - t0);
      return win;
    }
    return { plan: null, bestPlan: best, at: best ? best.__at : null, R: null,
             cands: cands, screened: screened, solved: solved, whys: whys,
             ms: Math.round(now() - t0) };
  }

  // Slot geometry, borrowed from BattleStage3D.CFG.form so the two stages block
  // the same fight. `ax` is ACROSS the axis (negative = party side / screen left),
  // `az` is depth (positive = away from the camera).
  function slotsFor(party, foes) {
    const S3D = window.BattleStage3D;
    const f = (S3D && S3D.CFG && S3D.CFG.form) || {
      partyX: 3.2, partyDx: 1.05, partyZ: 0.35, partyDz: 2.0,
      foeX: 3.4, foeZ: -0.8, foeRank: 2.1, foeSpread: 3.2, foeJog: 0.78, foeChevron: 0.5 };
    // HANDEDNESS IS WRITTEN DOWN IN EXACTLY ONE PLACE, and it is not here:
    // BattleStage3D.CFG.partySide. -1 = the party is on screen LEFT. Every shot
    // in the camera language and the 180-degree assertion that guards them read
    // the same sign out of the same field, so flipping it flips the whole game.
    const PS = partySide();
    const out = [];
    party.forEach((c, i) => {
      out.push({ id: c.id, side: 'party', h: 1.7, w: 0.75,
                 ax: PS * (f.partyX + i * f.partyDx),
                 az: f.partyZ + (i - (party.length - 1) / 2) * f.partyDz });
    });
    const n = foes.length;
    foes.forEach((c, i) => {
      let ax, az;
      if (n === 1) { ax = f.foeX; az = f.foeZ; }
      else if (n <= 3) {
        const sp = f.foeSpread * 0.62;
        az = f.foeZ + (i - (n - 1) / 2) * sp;
        ax = f.foeX + Math.abs(i - (n - 1) / 2) * f.foeChevron;
      } else {
        const front = Math.ceil(n / 2), back = n - front;
        const sp = f.foeSpread * 0.55;
        if (i < front) { ax = f.foeX; az = f.foeZ + (i - (front - 1) / 2) * sp; }
        else { const j = i - front; ax = f.foeX + f.foeRank; az = f.foeZ + (j - (back - 1) / 2) * sp - f.foeJog; }
      }
      // the creature's OWN height out of the MON registry, so the visibility
      // samples straddle the body that is actually going to stand there
      const md = ((window.BattleStage3D && window.BattleStage3D.MON) || {})[c.ref] || {};
      const h = md.h || 1.3;
      out.push({ id: c.id, side: 'foe', h: h, w: h * 1.15, ax: -PS * ax, az: az });
    });
    return out;
  }
  function partySide() {
    const S3D = window.BattleStage3D;
    const v = (S3D && S3D.CFG && S3D.CFG.partySide);
    return (v == null ? -1 : v) < 0 ? -1 : 1;
  }

  // ============================ CAST ========================================
  const CLIP = {
    idle: ['Idle', 'Unarmed_Idle', '2H_Melee_Idle', 'Idle_A'],
    attack: ['1H_Melee_Attack_Slice_Diagonal', '1H_Melee_Attack_Chop', 'Attack', 'Melee_Attack',
             'Unarmed_Melee_Attack_Punch_A', 'Attack_A', 'Bite_Front', 'Attack_Bite'],
    hit: ['Hit_A', 'Hit', 'Hit_B', 'HitRecieve', 'Take_Damage'],
    die: ['Death_A', 'Death', 'Die', 'Death_B'],
    item: ['Use_Item', 'PickUp', 'Interact'],
    cheer: ['Cheer', 'Victory'],
  };
  const RE = { idle: /idle/i, attack: /attack|bite|slash|swipe/i, hit: /hit|damage|flinch/i,
               die: /death|die/i, item: /item|pick|interact/i, cheer: /cheer|victory|win/i };
  function pickClip(clips, kind) {
    if (!clips || !clips.length) return null;
    for (const want of CLIP[kind] || []) { const h = clips.find(c => c.name === want); if (h) return h; }
    return (RE[kind] && clips.find(c => RE[kind].test(c.name))) || null;
  }

  const bufCache = Object.create(null);
  function loadGlb(url) {
    if (!url) return Promise.resolve(null);
    const TH = T();
    if (!TH || !TH.GLTFLoader) return Promise.resolve(null);
    if (!bufCache[url]) {
      bufCache[url] = fetch(url).then(r => (r.ok ? r.arrayBuffer() : null)).catch(() => null);
    }
    return bufCache[url].then(buf => {
      if (!buf) return null;
      return new Promise((res) => {
        try { new TH.GLTFLoader().parse(buf.slice(0), '', res, () => res(null)); }
        catch (e) { res(null); }
      });
    }).catch(() => null);
  }
  function firstGlb(urls) {
    const list = (Array.isArray(urls) ? urls : [urls]).filter(Boolean);
    if (!list.length) return Promise.resolve(null);
    return loadGlb(list[0]).then(g => g || (list.length > 1 ? firstGlb(list.slice(1)) : null));
  }

  // ============================ THE STAGE ===================================
  function createWorldStage(cfg) {
    const TH = T();
    if (!TH || !worldReady()) return null;
    const S = window.SIM;
    const S3D = window.BattleStage3D;
    const MON = (S3D && S3D.MON) || {};
    const art = (S3D && S3D.art) || { models: {}, base: 'assets/', modelDir: 'monsters/3d/' };

    const party = (cfg.party || []), foes = (cfg.foes || []);
    // A REFUSAL RELOCATES; IT DOES NOT SWITCH ARENAS (user ruling 2026-08-08).
    // stageArena walks the measured ring/bearing ladder and hands back the site
    // it staged on. Returning null here is NOT a fallback to the diorama any
    // more — it is the crash guard, reached only if the world refused all 25
    // sites, which the 160-cell sweep never saw once.
    const site = stageArena(slotsFor(party, foes));
    const plan = site.plan || (cfg.forcePlace ? site.bestPlan : null);
    if (!plan) {
      console.warn('[BattleWorld] every ring and bearing refused', site);
      window.__BW_LAST_SITE = site;
      window.BattleWorld.refused++;
      return null;
    }
    window.__BW_LAST_PLAN = plan;
    window.__BW_LAST_SITE = site;
    if (site.R) window.BattleWorld.relocated++;

    const root = new TH.Group();
    root.name = 'bw_root';
    root.userData.isBattleWorld = true;              // never in collide/walkRef/allMeshes
    W.scene.add(root);

    // ---- the camera: ORBIT is the only thing we touch, and we own the copy ----
    const O = window.ORBIT;
    const camSaved = { yaw: O.yaw, pitch: O.pitch, dist: O.dist, tilt: O.tilt,
                       panX: O.panX, panY: O.panY, panZ: O.panZ,
                       fov: W.cam ? W.cam.fov : null };
    // THE TILT MUST GO TO ZERO, and finding that out was worth the spike on its
    // own. play3d aims the overworld boom UP by OWTILT (0.16 rad) about its own X
    // AFTER lookAt, deliberately, so the player sits high in frame and the ridges
    // are visible ("THE OVERWORLD BOOM"). Left alone during a battle it puts the
    // aim point at 0.5 + 0.5*tan(0.16)/tan(21deg) = 71% down the frame, i.e. the
    // whole fight in the bottom third, under the party status window. Measured
    // before the fix: the foes' feet projected at y 778 of 813. Every pose the
    // shot solver emits therefore carries tilt 0, and teardown restores 0.16.
    const P0 = (function () { const p = S.pos(); return { x: p.x, y: p.y, z: p.z }; })();
    // TWO ANCHORS, AND CONFUSING THEM IS THE ONE WAY RELOCATION BREAKS.
    // P0 = where the PLAYER'S BODY is. It is the origin ORBIT's pan is measured
    //      from (play3d recomputes `target = P + pan` every frame), so every
    //      world aim -> pan conversion has to go through it and it must never be
    //      the arena's centre.
    // A0 = where the FIGHT is — the site the ladder staged on, which is P0 only
    //      when the ladder accepted ring 0. Everything about the arena's own
    //      geometry (which side of the axis a body stands on, the 180-degree
    //      reference eye, the degenerate aim) is measured from here.
    const A0 = { x: plan.basis.centre[0], y: plan.basis.centre[1], z: plan.basis.centre[2] };
    const baseYaw = (plan && plan.basis) ? plan.basis.yaw : O.yaw;
    // NOT A CONST ANY MORE: the tonal probe re-picks the boom once the cast has
    // arrived, and every shot in the table is solved RELATIVE to this number.
    let basePitch = (plan && plan.basis && plan.basis.pitch != null) ? plan.basis.pitch : CFG.cam.pitch;

    // ======================= THE SHOT SOLVER ================================
    // Every pose is derived from the bodies the shot must show. Nothing here is
    // a camera position; the table upstairs carries intent and this turns it
    // into (aim, yaw, pitch, dist, fov) against the real cast.
    const camB = { boom: {}, fwd: {}, right: {}, up: {} };
    function camBasis(yaw, pitch, out) {
      const cy = Math.cos(yaw), sy = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch);
      out.boom.x = cy * cp; out.boom.y = sp; out.boom.z = sy * cp;      // aim -> eye
      out.fwd.x = -out.boom.x; out.fwd.y = -out.boom.y; out.fwd.z = -out.boom.z;
      out.right.x = sy; out.right.y = 0; out.right.z = -cy;             // play3d's own pan basis
      out.up.x = -cy * sp; out.up.y = cp; out.up.z = -sy * sp;          // right x fwd
      return out;
    }
    const dot3 = (a, x, y, z) => a.x * x + a.y * y + a.z * z;
    // WHICH SIDE OF THE FRAME A BODY LANDS ON, exactly — the perspective divide
    // included, because an ordering taken on a flat dot product is wrong the
    // moment two bodies are at different depths.
    function screenX(pose, x, y, z) {
      camBasis(pose.yaw, pose.pitch, camB);
      const ex = pose.ax + camB.boom.x * pose.dist,
            ey = pose.ay + camB.boom.y * pose.dist,
            ez = pose.az + camB.boom.z * pose.dist;
      const vx = x - ex, vy = y - ey, vz = z - ez;
      const w = dot3(camB.fwd, vx, vy, vz);
      if (w <= 0.05) return dot3(camB.right, vx, vy, vz) > 0 ? 9 : -9;   // behind the lens
      const tanV = Math.tan(pose.fov * Math.PI / 360);
      const tanH = tanV * (W.cam ? W.cam.aspect : 16 / 9);
      return dot3(camB.right, vx, vy, vz) / (w * tanH);
    }
    // THE 180-DEGREE RULE, AS A REFUSAL. Two independent tests, because they
    // fail differently: (1) the EYE must stay on the side of the party->foe axis
    // it started on — cross the line and the whole fight mirrors; (2) every
    // party body must still project outboard of every foe body, which is the
    // thing the player actually experiences. `partySide()` is the only place the
    // handedness is written and both tests read it.
    let axisRef = 0;                  // the side of the axis the fight was solved from
    // THE RIG's own state, declared before anything that writes it.
    const RIG = { cur: null, from: null, to: null, t0: 0, ms: 1, ease: 'out',
                  kind: null, next: null, refusals: 0, lastRefusal: null,
                  log: [], moves: 0 };
    function sides() {
      const p = [], f = [];
      for (const id of order) {
        const b = bodies[id];
        if (!b || b.root.visible === false) continue;
        (b.side === 'foe' ? f : p).push(b);
      }
      return { p, f };
    }
    function axisSign(eyeX, eyeZ) {
      const s = sides();
      if (!s.p.length || !s.f.length) return 0;
      let px = 0, pz = 0, fx = 0, fz = 0;
      for (const b of s.p) { px += b.home.x; pz += b.home.z; }
      for (const b of s.f) { fx += b.home.x; fz += b.home.z; }
      px /= s.p.length; pz /= s.p.length; fx /= s.f.length; fz /= s.f.length;
      const ax = fx - px, az = fz - pz, bx = eyeX - px, bz = eyeZ - pz;
      const cr = ax * bz - az * bx;
      return cr > 0 ? 1 : cr < 0 ? -1 : 0;
    }
    function axisCheck(pose) {
      camBasis(pose.yaw, pose.pitch, camB);
      const ex = pose.ax + camB.boom.x * pose.dist, ez = pose.az + camB.boom.z * pose.dist;
      const sgn = axisSign(ex, ez);
      const s = sides();
      let pMax = -Infinity, pMin = Infinity, fMax = -Infinity, fMin = Infinity;
      for (const b of s.p) { const x = screenX(pose, b.root.position.x, b.root.position.y + b.h * 0.5, b.root.position.z); if (x > pMax) pMax = x; if (x < pMin) pMin = x; }
      for (const b of s.f) { const x = screenX(pose, b.root.position.x, b.root.position.y + b.h * 0.5, b.root.position.z); if (x > fMax) fMax = x; if (x < fMin) fMin = x; }
      const PS = partySide();
      // one side empty (a KO'd line, the victory shot) = nothing to cross
      const both = s.p.length > 0 && s.f.length > 0;
      const order2 = !both || (PS < 0 ? pMax < fMin : pMin > fMax);
      const gap = !both ? null : +(PS < 0 ? fMin - pMax : pMin - fMax).toFixed(4);
      const sideOk = !both || axisRef === 0 || sgn === axisRef;
      return { ok: !!(order2 && sideOk), order: !!order2, side: sideOk, gap: gap,
               sgn: sgn, ref: axisRef, party: both ? [+pMin.toFixed(3), +pMax.toFixed(3)] : null,
               foe: both ? [+fMin.toFixed(3), +fMax.toFixed(3)] : null };
    }

    function subjectsFor(kind, o) {
      o = o || {};
      const live = order.map(id => bodies[id]).filter(b => b && b.root.visible !== false);
      const sh = CAM.shots[kind] || CAM.shots.round;
      const pick = (ids) => ids.map(id => bodies[id]).filter(b => b && b.root.visible !== false);
      if (sh.show === 'actor') {
        const l = pick([o.actor || actorId].concat(o.target || targetId ? [o.target || targetId] : []));
        return l.length ? l : live;
      }
      if (sh.show === 'pair') {
        const l = pick([o.actor || actorId, o.target || targetId].filter(Boolean));
        return l.length ? l : live;
      }
      if (sh.show === 'victim') { const l = pick([o.victim].filter(Boolean)); return l.length ? l : live; }
      if (sh.show === 'party') { const l = live.filter(b => b.side !== 'foe' && !b.dead); return l.length ? l : live; }
      return live;
    }
    // The side of the arena a body stands on, in the arena's own basis: -1 is the
    // party's side when partySide is -1. Derived, never assumed from the id.
    function sideSign(b) {
      const rx = Math.sin(baseYaw), rz = -Math.cos(baseYaw);
      const d = (b.home.x - A0.x) * rx + (b.home.z - A0.z) * rz;
      return d < 0 ? -1 : 1;
    }
    function solveShot(kind, o) {
      o = o || {};
      const sh = CAM.shots[kind] || CAM.shots.round;
      const subj = subjectsFor(kind, o);
      const fov = clamp(typeof sh.fov === 'number' ? sh.fov : (CAM.fov[sh.fov] || CAM.fov.rest),
                        CAM.fov.min, CAM.fov.max);
      const pitch = clamp(basePitch + (sh.dPitch || 0) + (o._dp || 0), CAM.pitch.min, CAM.pitch.max);
      // WHICH WAY THE BOOM SWINGS is derived from who the shot is about: toward
      // the end of the axis the subject FACES, so a shot on a body shows its
      // front. A pair takes the attacker's sign. Capped well short of the axis.
      let s = 0;
      if (sh.show === 'actor' || sh.show === 'pair') { const a = bodies[o.actor || actorId]; if (a) s = sideSign(a); }
      else if (sh.show === 'victim') { const v = bodies[o.victim]; if (v) s = sideSign(v); }
      else if (sh.show === 'party') s = partySide();
      const yawOff = clamp((sh.yawOff || 0) * s, -1.05, 1.05);
      const pose = { kind: kind, ax: 0, ay: 0, az: 0, yaw: baseYaw + yawOff, pitch: pitch,
                     dist: CFG.cam.dist, fov: fov, tilt: 0 };
      // WHERE A BODY WILL BE WHEN THE SHOT IS ON SCREEN, not where it is when the
      // shot is asked for. The strike shot is requested the instant act() starts,
      // with the attacker still at home five metres away — framing the pair from
      // there produced a wide shot of a gap she was about to close, and by the
      // time she arrived the frame was two seconds stale. `o.pos` carries the
      // strike station act() has already derived from both bodies' own widths.
      const posOf = (b) => (o.pos && o.pos[b.id]) || b.root.position;
      const subjP = subj.map(b => ({ b: b, p: posOf(b) }));
      // AIM: the subject group's own centre of mass at chest height.
      let n = 0;
      for (const s2 of subjP) { pose.ax += s2.p.x; pose.ay += s2.p.y + s2.b.h * 0.52; pose.az += s2.p.z; n++; }
      if (!n) { pose.ax = A0.x; pose.ay = A0.y + 1; pose.az = A0.z; n = 1; }
      pose.ax /= n; pose.ay /= n; pose.az /= n;
      // DISTANCE: solved so every one of the subject's own extremes — feet, head,
      // and its own measured half-width either side — lands inside the fill band.
      // Two passes, because `lead` moves the aim and the aim moves the fit.
      const fit = () => {
        camBasis(pose.yaw, pose.pitch, camB);
        const tanV = Math.tan(pose.fov * Math.PI / 360);
        const tanH = tanV * (W.cam ? W.cam.aspect : 16 / 9);
        let d = CAM.dist.min;
        for (const s2 of subjP) {
          const b = s2.b, hw = b.w / 2;
          for (const sx of [-1, 1]) for (const sy of [0, 1]) {
            const px = s2.p.x + camB.right.x * hw * sx,
                  py = s2.p.y + (sy ? b.h * 1.08 : -0.05),
                  pz = s2.p.z + camB.right.z * hw * sx;
            const vx = px - pose.ax, vy = py - pose.ay, vz = pz - pose.az;
            const u = dot3(camB.right, vx, vy, vz), v = dot3(camB.up, vx, vy, vz), w = dot3(camB.fwd, vx, vy, vz);
            const dh = Math.abs(u) / (Math.max(0.05, sh.fillH) * tanH) - w;
            const dv = Math.abs(v) / (Math.max(0.05, sh.fillV) * tanV) - w;
            if (dh > d) d = dh;
            if (dv > d) d = dv;
          }
        }
        pose.dist = clamp(d, CAM.dist.min, CAM.dist.max);
        return tanH;
      };
      const tanH = fit();
      if (sh.lead) {
        // LOOKING ROOM, on the side the subject is facing away from. `lead` is a
        // fraction of the half-frame; the sign comes from which side of the
        // arena the subject stands on, never from the table.
        camBasis(pose.yaw, pose.pitch, camB);
        const k = (s || 1) * sh.lead * pose.dist * tanH;
        pose.ax -= camB.right.x * k; pose.az -= camB.right.z * k;
        fit();
      }
      pose._subj = subjP;
      return pose;
    }
    // CAN THE SHOT SEE ITS OWN SUBJECT — nine samples per body, from this pose's
    // own eye. `boomClear` only ever asked about the line to the aim point; the
    // strike shot rides low and the thing that eats it is knee-high foliage in
    // front of the attacker, which a single boom ray flies straight over.
    function subjVis(pose) {
      camBasis(pose.yaw, pose.pitch, camB);
      const eye = { x: pose.ax + camB.boom.x * pose.dist, y: pose.ay + camB.boom.y * pose.dist,
                    z: pose.az + camB.boom.z * pose.dist };
      let worst = 1;
      for (const s2 of (pose._subj || [])) {
        const v = visFrac(eye, s2.p.x, s2.p.y, s2.p.z, s2.b.h, s2.b.w, pose.yaw);
        if (v < worst) worst = v;
      }
      return worst;
    }
    // THE HARD REFUSAL. A shot that would cross the axis is not softened and not
    // shipped: the swing is halved, then dropped, and if the geometry still
    // crosses (two bodies interleaved on the line) the camera KEEPS THE POSE IT
    // HAS. A camera language that can mirror the fight is worse than one angle.
    // AND THE BOOM MUST HAVE A LINE. play3d's CAMCLIP hauls the boom in when the
    // world intervenes (it is the fix PT-20260803-025 is about, and it keeps
    // running through a battle by design) — so a shot solved into a bank does
    // not get refused, it gets silently re-framed at 3 m by somebody else's
    // easing. Lifting the boom is the cheaper answer than losing the shot.
    function boomClear(pose) {
      camBasis(pose.yaw, pose.pitch, camB);
      return seesPoint({ x: pose.ax + camB.boom.x * pose.dist,
                         y: pose.ay + camB.boom.y * pose.dist,
                         z: pose.az + camB.boom.z * pose.dist }, pose.ax, pose.ay, pose.az);
    }
    function solveShotSafe(kind, o) {
      const sh = CAM.shots[kind] || CAM.shots.round;
      const saveOff = sh.yawOff;
      let fallback = null, lastChk = null;
      for (const k of [1, 0.5, 0]) {
        for (const dp of [0, 0.09, 0.19]) {
          sh.yawOff = saveOff * k;
          const pose = solveShot(kind, Object.assign({}, o, { _dp: dp }));
          const chk = axisCheck(pose);
          sh.yawOff = saveOff;
          lastChk = chk;
          if (!chk.ok) break;                      // a bigger pitch cannot fix handedness
          pose.axis = chk; pose.softened = k; pose.lifted = dp;
          pose.vis = +subjVis(pose).toFixed(3);
          if (boomClear(pose) && pose.vis >= CFG.place.visMin) return pose;
          if (!fallback || pose.vis > fallback.vis) fallback = pose;
        }
      }
      if (fallback) return fallback;
      RIG.refusals++; RIG.lastRefusal = { kind: kind, chk: lastChk };
      return null;
    }

    // ======================= THE RIG (moves, never cuts) ====================
    const EASE = {
      lin: u => u,
      out: u => 1 - Math.pow(1 - u, 3),
      io: u => (u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2),
    };
    function shortArc(from, to) {
      return from + (((to - from + Math.PI) % (2 * Math.PI) + 2 * Math.PI) % (2 * Math.PI) - Math.PI);
    }
    function poseNow() {
      const p = { kind: RIG.kind, ax: P0.x + O.panX, ay: P0.y + 1 + O.panY, az: P0.z + O.panZ,
                  yaw: O.yaw, pitch: O.pitch, dist: O.dist, fov: W.cam ? W.cam.fov : 42, tilt: O.tilt };
      return p;
    }
    function goTo(pose, ms, ease, why) {
      if (!pose) return false;
      RIG.from = RIG.cur ? Object.assign({}, RIG.cur) : poseNow();
      RIG.to = Object.assign({}, pose);
      RIG.to.yaw = shortArc(RIG.from.yaw, RIG.to.yaw);
      RIG.t0 = now(); RIG.ms = Math.max(1, ms || 600); RIG.ease = ease || 'io';
      RIG.kind = pose.kind || RIG.kind;
      RIG.moves++;
      RIG.log.push({ t: +(now() - camT0).toFixed(0), kind: RIG.kind, why: why || null,
                     dist: +pose.dist.toFixed(2), fov: +pose.fov.toFixed(1),
                     pitch: +pose.pitch.toFixed(3), yaw: +pose.yaw.toFixed(3) });
      if (RIG.log.length > 200) RIG.log.shift();
      return true;
    }
    // THE ONE ENTRY POINT the stage's verbs call. A shot that the 180-degree
    // check refuses leaves the camera where it is and is counted.
    function shot(kind, o) {
      if (!camOn()) return false;
      const sh = CAM.shots[kind]; if (!sh) return false;
      const pose = solveShotSafe(kind, o);
      if (!pose) return false;
      RIG.next = null;
      const ok = goTo(pose, (o && o.ms) || sh.ms, sh.cut ? 'lin' : sh.ease, (o && o.why) || kind);
      if (ok && sh.push && !(o && o.nopush)) {
        // the queued second leg: a slow dolly that starts when the move lands
        const p2 = Object.assign({}, pose);
        p2.dist = clamp(pose.dist * sh.push.k, CAM.dist.min, CAM.dist.max);
        RIG.next = { pose: p2, ms: sh.push.ms, ease: sh.push.ease, why: kind + '-push' };
      }
      return ok;
    }
    const camT0 = now();
    // The player's own body is a combatant now (or would be a duplicate standing
    // in the middle of her own battle), so it is hidden and restored by identity.
    const chSaved = W.ch ? W.ch.visible : null;
    if (W.ch) W.ch.visible = false;

    // ---- bodies --------------------------------------------------------------
    const bodies = Object.create(null);
    const order = [];
    const mixers = [];
    const owned = { geo: [], mat: [], tex: [] };
    let deadStage = false, raf = 0;
    let actorId = null, targetId = null;
    const tweens = [];

    function ownDispose(objRoot) {
      objRoot.traverse((o) => {
        if (o.geometry) owned.geo.push(o.geometry);
        const ms = o.material ? (Array.isArray(o.material) ? o.material : [o.material]) : [];
        for (const m of ms) {
          owned.mat.push(m);
          for (const k of ['map', 'emissiveMap', 'alphaMap', 'normalMap', 'roughnessMap', 'metalnessMap']) {
            if (m[k]) owned.tex.push(m[k]);
          }
        }
      });
    }

    function newBody(rec) {
      const g = new TH.Group();
      g.position.set(rec.x, rec.y, rec.z);
      g.rotation.y = rec.yaw;
      const bob = new TH.Group();
      g.add(bob);
      root.add(g);
      const b = { id: rec.id, side: rec.side, root: g, bob: bob, obj: null, home: g.position.clone(),
                  tier: 'none', dead: false, h: 1.7, w: 0.7, mixer: null, actions: null, flash: 0,
                  holdUntil: 0, alpha: 1 };   // the killer's hold, and the alpha this stage set
      bodies[rec.id] = b; order.push(rec.id);
      return b;
    }

    function setVisual(b, obj, targetH, opt) {
      opt = opt || {};
      if (b.obj) { b.bob.remove(b.obj); }
      const box = new TH.Box3().setFromObject(obj);
      const h = Math.max(0.05, box.max.y - box.min.y);
      if (!opt.noScale) { const s = targetH / h; obj.scale.setScalar(s); }
      obj.position.y -= box.min.y * (opt.noScale ? 1 : targetH / h);
      obj.traverse((o) => {
        if (o.isMesh) {
          o.castShadow = true; o.receiveShadow = true;
          o.frustumCulled = false;                    // skinned bounds go stale mid-clip
        }
      });
      ownDispose(obj);
      b.bob.add(obj);
      b.obj = obj; b.tier = opt.tier || 'model'; b.h = targetH;
      // THE BODY'S OWN WIDTH, out of the Box3 the loader measured, scaled the way
      // the body was. act()'s strike station is derived from it — a duskpad is
      // 2.07 m across and a party rig 0.73, and a constant stand-off cannot know that.
      const k = opt.noScale ? 1 : targetH / h;
      b.w = Math.max(0.25, Math.max(box.max.x - box.min.x, box.max.z - box.min.z) * k);
    }

    // The proxy solid, borrowed in spirit from battle_stage3d's: a spike does not
    // need six creature shapes, it needs a body-sized volume that is honestly a
    // placeholder and casts a real shadow into the real GTAO.
    function proxy(colour, tall) {
      const g = new TH.Group();
      const m = new TH.MeshStandardMaterial({ color: colour, roughness: 0.78, metalness: 0.0 });
      const add = (geo, x, y, z) => { const me = new TH.Mesh(geo, m); me.position.set(x, y, z); g.add(me); };
      if (tall) {
        add(new TH.CylinderGeometry(0.2, 0.26, 0.62, 8), 0, 1.03, 0);
        add(new TH.SphereGeometry(0.19, 10, 8), 0, 1.47, 0);
        for (const s of [-1, 1]) {
          add(new TH.CylinderGeometry(0.075, 0.075, 0.5, 6), s * 0.26, 1.06, 0);
          add(new TH.CylinderGeometry(0.09, 0.08, 0.72, 6), s * 0.11, 0.36, 0);
        }
      } else {
        add(new TH.SphereGeometry(0.5, 12, 9), 0, 0.44, 0);
        add(new TH.SphereGeometry(0.2, 8, 6), 0.3, 0.62, 0.16);
        add(new TH.SphereGeometry(0.2, 8, 6), 0.3, 0.62, -0.16);
      }
      return g;
    }

    function rigUp(b, gltf) {
      const clips = gltf.animations || [];
      if (!clips.length) return;
      const mixer = new TH.AnimationMixer(b.obj);
      mixers.push(mixer); b.mixer = mixer; b.actions = {};
      for (const kind of Object.keys(CLIP)) {
        const c = pickClip(clips, kind);
        if (!c) continue;
        const a = mixer.clipAction(c);
        if (kind !== 'idle') { a.setLoop(TH.LoopOnce, 1); a.clampWhenFinished = kind === 'die'; }
        b.actions[kind] = a;
      }
      if (b.actions.idle) { b.actions.idle.play(); b.actions.idle.time = Math.random() * 2; }
    }
    function oneShot(b, kind, hold) {
      if (!b.actions || !b.actions[kind]) return false;
      const a = b.actions[kind], idle = b.actions.idle;
      a.reset(); a.setEffectiveWeight(1); a.fadeIn(0.08).play();
      const dur = a.getClip().duration;
      if (idle && !hold) {
        idle.fadeOut(0.08);
        clearTimeout(b._backT);
        b._backT = setTimeout(() => {
          if (deadStage || b.dead) return;
          a.fadeOut(0.2); idle.reset().fadeIn(0.2).play();
        }, Math.max(140, dur * 1000 - 200));
      } else if (hold && idle) idle.fadeOut(0.15);
      return true;
    }

    // ---- build the cast ------------------------------------------------------
    const byId = Object.create(null);
    for (const r of plan.placed) byId[r.id] = r;
    party.forEach((c) => {
      const rec = byId[c.id]; if (!rec) return;
      const b = newBody(rec);
      setVisual(b, proxy(0x6f8a63, true), 1.7, { tier: 'proxy' });
      const urls = (art.models && art.models[c.ref || c.id]) || null;
      firstGlb(urls).then((g) => {
        if (deadStage || !g || b.tier !== 'proxy') return;
        setVisual(b, g.scene, 1.7, { tier: 'model' });
        rigUp(b, g);
        reframeOpening();
        if (c.dead) markDead(b, true);
      }).catch(() => { });
      if (c.dead) markDead(b, true);
    });
    foes.forEach((c) => {
      const rec = byId[c.id]; if (!rec) return;
      const b = newBody(rec);
      const md = MON[c.ref] || MON.default || { h: 1.3 };
      setVisual(b, proxy(0x8d8064, false), md.h, { tier: 'proxy' });
      const url = art.base + art.modelDir + String(c.ref) + '.glb';
      loadGlb(url).then((g) => {
        if (deadStage || !g || b.tier !== 'proxy') return;
        if (md.yaw) g.scene.rotation.y += md.yaw;
        setVisual(b, g.scene, md.h, { tier: 'model' });
        rigUp(b, g);
        reframeOpening();
        if (c.dead) markDead(b, true);
      }).catch(() => { });
      if (c.dead) markDead(b, true);
    });

    // ---- THE OPENING SHOT ----------------------------------------------------
    // Solved now, because the bodies exist now. `axisRef` is the side of the
    // party->foe axis this fight was staged from, and every later shot is
    // refused if it would put the eye on the other one.
    (function openingShot() {
      camBasis(baseYaw, basePitch, camB);
      axisRef = axisSign(A0.x + camB.boom.x * CFG.cam.dist, A0.z + camB.boom.z * CFG.cam.dist);
      if (!camOn()) {
        // THE SPIKE'S OWN POSE, to the number: one boom, one pitch, tilt to zero,
        // the pan left where the player had it, eased over CFG.cam.ms. This is
        // what `?bcam=0` gets and it is what the before column measures.
        // A0, NOT P0: the spike wrote P0 here because the arena WAS the player's
        // own cell and the two were the same point. With the ladder they are not,
        // and aiming the ?bcam=0 arm at the player would frame the place the
        // fight ISN'T. The pan offset the player had is preserved either way.
        goTo({ kind: 'fixed', ax: A0.x + camSaved.panX, ay: A0.y + 1 + camSaved.panY,
               az: A0.z + camSaved.panZ, yaw: baseYaw, pitch: CFG.cam.pitch,
               dist: CFG.cam.dist, fov: camSaved.fov == null ? 42 : camSaved.fov, tilt: 0 },
              CFG.cam.ms, 'out', 'entry(fixed)');
        return;
      }
      shot('round', { ms: CFG.cam.ms, why: 'entry' });
    })();
    // A MODEL ARRIVING CHANGES THE SUBJECT'S OWN MEASUREMENTS — the proxy is
    // 0.52 m across and a duskpad is 2.07 — so the opening frame is re-solved
    // when the real cast lands, and ONLY while nothing else has asked for a shot.
    let acted = false;
    function reframeOpening() {
      if (deadStage || acted || !camOn() || RIG.kind !== 'round') return;
      shot('round', { ms: 420, why: 'reframe(models)' });
    }
    // ALWAYS SETTLE BACK TO REST. The rule set BET B names: never cross the axis,
    // at most one move per beat, and always return to the shot the whole fight is
    // readable from. A later shot request cancels a pending return, so a fast
    // exchange never fights itself.
    let restT = 0;
    function restLater(ms) {
      clearTimeout(restT);
      restT = setTimeout(() => { if (!deadStage) shot('round', { why: 'settle' }); }, ms);
    }
    function shotB(kind, o) {          // every verb goes through here
      clearTimeout(restT);
      return shot(kind, o);
    }

    // ---- markers: two rings on the REAL ground -------------------------------
    function ringMesh(colour) {
      const geo = new TH.RingGeometry(0.42, 0.62, 28);
      geo.rotateX(-Math.PI / 2);
      const mat = new TH.MeshBasicMaterial({ color: colour, transparent: true, opacity: 0.6,
                                             depthWrite: false, side: TH.DoubleSide });
      const m = new TH.Mesh(geo, mat);
      m.visible = false; m.renderOrder = 3;
      owned.geo.push(geo); owned.mat.push(mat);
      root.add(m);
      return m;
    }
    const targetRing = ringMesh(0xf0b45c), actorRing = ringMesh(0xffe6c0);
    function placeRing(ring, id, s) {
      const b = id && bodies[id];
      if (!b || b.dead) { ring.visible = false; return; }
      ring.visible = true;
      ring.position.set(b.root.position.x, b.root.position.y + 0.03, b.root.position.z);
      ring.scale.setScalar(s);
    }

    // ---- fx ------------------------------------------------------------------
    let shakeAmp = 0, shakeT0 = 0, shakeDur = 1;
    function shake(a, ms) { shakeAmp = a; shakeT0 = now(); shakeDur = ms || CFG.fx.shakeMs; }
    function tween(ms, fn, end) { tweens.push({ t0: now(), ms: ms, fn: fn, end: end }); }
    function runTweens() {
      for (let i = tweens.length - 1; i >= 0; i--) {
        const t = tweens[i], u = clamp((now() - t.t0) / t.ms, 0, 1);
        try { t.fn(u); } catch (e) { }
        if (u >= 1) { tweens.splice(i, 1); if (t.end) { try { t.end(); } catch (e) { } } }
      }
    }
    function flashOn(b) {
      if (!b.obj) return;
      const hit = [];
      b.obj.traverse((o) => { if (o.isMesh && o.material && 'emissive' in o.material) {
        hit.push([o.material, o.material.emissive.clone(), o.material.emissiveIntensity]); } });
      for (const [m] of hit) { m.emissive.setRGB(1, 0.92, 0.8); m.emissiveIntensity = CFG.fx.flash; }
      setTimeout(() => {
        for (const [m, c, i] of hit) { m.emissive.copy(c); m.emissiveIntensity = i; }
      }, CFG.fx.flashMs);
    }
    function shockRing(b) {
      const geo = new TH.RingGeometry(0.2, 0.3, 24); geo.rotateX(-Math.PI / 2);
      const mat = new TH.MeshBasicMaterial({ color: 0xfff4dd, transparent: true, opacity: 0.85,
                                             depthWrite: false, side: TH.DoubleSide });
      const m = new TH.Mesh(geo, mat);
      m.position.set(b.root.position.x, b.root.position.y + 0.05, b.root.position.z);
      root.add(m);
      tween(CFG.fx.ringMs, (u) => { m.scale.setScalar(1 + u * 5); mat.opacity = 0.85 * (1 - u); },
            () => { root.remove(m); geo.dispose(); mat.dispose(); });
    }

    // ===== THE KO IS A BEAT HERE TOO, AND THE SINK WAS WORSE HERE ==============
    // The diorama's 0.55 m sink put a body under a procedural dish. THIS stage
    // stands its bodies on real terrain solved out of SIM.ground, so the same
    // line drove a corpse 0.55 m THROUGH SOLID ROCK, in frame, on a ledge. The
    // rest height is now the real floor under wherever the body landed — asked of
    // the scene, never assumed to be a plane. Phases and numbers are read from
    // BattleStage3D.CFG.ko so the two stages stage the same death; this one has no
    // particle system, so its dissolve is the fade plus the ring it already had.
    function koCfg() {
      const S3D = window.BattleStage3D;
      return (S3D && S3D.CFG && S3D.CFG.ko) || { knockM: 0.62, knockMs: 300, fallMs: 520,
        holdMs: 760, dissolveMs: 620, partyAlpha: 0.22, attackerHold: 380,
        react: { ms: 640, delay: 130, stagger: 110, lean: 0.26, leanIn: 0.22,
                 look: 0.55, allyK: 0.5 } };
    }
    function setAlpha(b, a) {
      b.alpha = a;                    // what the STAGE set — see at()
      b.root.traverse((o) => {
        if (o.isMesh && o.material) { o.material.transparent = true; o.material.opacity = a; }
      });
    }
    function markDead(b, instant) {
      if (b.dead) return;
      b.dead = true;
      b.bob.rotation.set(0, 0, 0);
      const K = koCfg();
      clearTimeout(b._backT);                 // a pending return-to-idle must not raise the dead
      oneShot(b, 'die', true);
      if (instant) { b.root.visible = false; return; }
      // (0) THE CAMERA GOES TO THE BODY, AND THEN IT PUSHES IN. The KO lane
      // wanted exactly this and refused it in the diorama, where the plate is
      // pinned to one pose: a slow dolly across CFG.ko.holdMs, so the 760 ms the
      // corpse lies there is a move rather than a pause. It ends before the
      // dissolve; the return to rest is scheduled past both.
      shotB('ko', { victim: b.id });
      restLater(K.holdMs + K.dissolveMs + 320);
      // (1) THE BLOW LANDS. battle_turnbased sets dead BEFORE it calls flinch and
      // flinch returns early on a dead body, so without this the killing blow is
      // the one blow with no feedback — the same defect measured in the diorama.
      flashOn(b); shockRing(b); shake(CFG.fx.shakeKo, 420);
      // (2) THE STAGGER, away from whoever struck it — and THE KILLER HOLDS
      const src = (actorId && bodies[actorId] && bodies[actorId] !== b) ? bodies[actorId] : null;
      if (src && !src.dead) src.holdUntil = now() + K.attackerHold;
      let kx = 1, kz = 0;
      if (src) {
        const dx = b.home.x - src.home.x, dz = b.home.z - src.home.z;
        const L = Math.hypot(dx, dz) || 1; kx = dx / L; kz = dz / L;
      }
      reactToKO(b);
      const x1 = b.home.x + kx * K.knockM, z1 = b.home.z + kz * K.knockM;
      // (3) THE FALL, ONTO THE REAL GROUND. A column with no floor under it keeps
      // the body's own height rather than guessing — a refusal, not a drop.
      let restY = b.home.y;
      try { const g = window.SIM && window.SIM.ground(x1, z1, b.home.y);
            if (g != null && Math.abs(g - b.home.y) < 2.2) restY = g; } catch (e) { }
      const y0 = b.root.position.y, fall = K.knockMs + K.fallMs;
      tween(fall, (u) => {
        const kp = 1 - Math.pow(1 - clamp(u * (fall / K.knockMs), 0, 1), 3);
        b.root.position.x = b.home.x + kx * K.knockM * kp;
        b.root.position.z = b.home.z + kz * K.knockM * kp;
        b.root.position.y = lerp(y0, restY, u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2)
                          + Math.sin(kp * Math.PI) * 0.09;
      }, () => {
        b.root.position.set(x1, restY, z1);
        if (b.side !== 'foe') { setAlpha(b, K.partyAlpha); return; }
        // (4) IT LIES THERE — the beat that did not exist — and (5) then it goes
        tween(K.holdMs, () => { }, () => {
          if (deadStage || !b.dead) return;
          tween(K.dissolveMs, (u) => { if (b.dead) setAlpha(b, 1 - u); },
                () => { if (b.dead) b.root.visible = false; });
        });
      });
    }
    // ===== THE OTHERS REACT ===================================================
    // Same rule as the diorama's (battle_stage3d reactToKO): the killer's beat is
    // the hold at its strike station, everybody else turns to look with a recoil
    // under it, and the turn goes on `bob` because root.rotation.y is the facing
    // every lunge here is derived from. No clip is added — there is none to source.
    const _qA = new TH.Quaternion(), _qB = new TH.Quaternion();
    const _UP = new TH.Vector3(0, 1, 0), _LN = new TH.Vector3(1, 0, 0);
    function reactToKO(victim) {
      const K = koCfg().react;
      let i = 0, j = 0;
      for (const id of order) {
        const o = bodies[id];
        if (!o || o === victim || o.dead || o.id === actorId) continue;
        const ally = o.side === victim.side;    // recoil on its own side, lean in on the other
        reactBeat(o, victim, ally ? -K.lean : (K.leanIn || K.lean * 0.85),
                  ally ? K.look : K.look * K.allyK,
                  K.delay + (ally ? (i++) * K.stagger : 90 + (j++) * K.stagger), K.ms);
      }
    }
    function reactBeat(b, at, lean, look, delay, ms) {
      const dx = at.home.x - b.home.x, dz = at.home.z - b.home.z;
      let dy = Math.atan2(dx, dz) - b.root.rotation.y;
      while (dy > Math.PI) dy -= 2 * Math.PI;
      while (dy < -Math.PI) dy += 2 * Math.PI;
      const yaw = clamp(dy, -1.2, 1.2) * look;
      tween(Math.max(1, delay), () => { }, () => {
        if (deadStage || b.dead) return;
        tween(ms, (u) => {
          const s = u < 0.18 ? 1 - Math.pow(1 - u / 0.18, 3)
                  : u < 0.55 ? 1 : 1 - (u - 0.55) / 0.45;
          _qA.setFromAxisAngle(_UP, yaw * s);
          _qB.setFromAxisAngle(_LN, lean * s);      // SIGNED: away = recoil, toward = watch
          b.bob.quaternion.copy(_qA).multiply(_qB);
        }, () => { b.bob.rotation.set(0, 0, 0); });
      });
    }
    function revive(b) {
      if (!b.dead) return;
      b.dead = false; b.root.visible = true; b.root.position.copy(b.home);
      b.bob.rotation.set(0, 0, 0);          // a KO reaction must not outlive the body's death
      b.root.traverse((o) => { if (o.isMesh && o.material) o.material.opacity = 1; });
      if (b.actions && b.actions.idle) b.actions.idle.reset().fadeIn(0.2).play();
    }

    // THE SEAM MOVED UNDER THIS SPIKE, ON PURPOSE (battle wave 1, 088c8703):
    // `stage.act(id, kind, targetId, contactMs) -> ms the blow lands`, and
    // battle_turnbased waits for THAT return rather than a fixed 300 ms wind. A
    // stage that answers nothing keeps the whole budget, so the spike was already
    // compatible — but BET C's arithmetic is world-space arithmetic and reads
    // BETTER here than in the diorama, because the gap is whatever the terrain
    // made it rather than a constant 5.21 m. So it is implemented, not borrowed.
    function act(id, kind, tid, contactMs) {
      const b = bodies[id]; if (!b || b.dead) return 0;
      const budget = (typeof contactMs === 'number' && contactMs > 0) ? contactMs : CFG.fx.lungeMs;
      if (kind === 'flee') return 0;
      if (kind === 'item') { oneShot(b, 'item'); return budget; }
      // who is being hit: the caller's name, else the player's cursor, else the
      // nearest living enemy — a body must always have something to walk at
      const named = (tid != null && bodies[tid] && !bodies[tid].dead && bodies[tid].side !== b.side)
        ? bodies[tid] : null;
      const cur = targetId && bodies[targetId] && bodies[targetId].side !== b.side ? bodies[targetId] : null;
      let tgt = named || cur;
      if (!tgt) {
        for (const oid of order) {
          const o = bodies[oid];
          if (o.side !== b.side && !o.dead) { tgt = o; break; }
        }
      }
      let nx = 0, nz = 0, travel = CFG.fx.lungeM;
      if (tgt && tgt !== b) {
        nx = tgt.root.position.x - b.home.x; nz = tgt.root.position.z - b.home.z;
        const L = Math.hypot(nx, nz) || 1; nx /= L; nz /= L;
        // THE STRIKE STATION comes from the two BODIES, not from a constant: stop
        // half of each body's own measured width apart, plus a hand's reach.
        travel = Math.max(0, L - ((b.w + tgt.w) / 2 * 1.05 + 0.22));
      }
      // THE STRIKE SHOT — low three-quarter, framed on the two bodies that are
      // about to touch, and it lands while the attacker is still walking in.
      acted = true;
      const station = {};
      station[id] = { x: b.home.x + nx * travel, y: b.home.y, z: b.home.z + nz * travel };
      shotB('strike', { actor: id, target: tgt && tgt !== b ? tgt.id : null, pos: station,
                        ms: Math.min(420, Math.max(200, budget * 0.7)) });
      oneShot(b, 'attack');
      const total = budget + 320;
      const arriveU = clamp((budget * 0.62) / total, 0.05, 0.95);
      // THE PLANT CAN BE HELD, exactly as in the diorama: if this blow kills, the
      // killer stands over the body it felled instead of walking home while it
      // falls. The tween runs `attackerHold` longer so it cannot end mid-hold.
      const K = koCfg();
      b.holdUntil = 0;
      const t0 = now(), dur = total + K.attackerHold;
      tween(dur, (u) => {
        const uu = clamp(u * dur / total, 0, 1), el = now() - t0;
        let p;
        if (uu < arriveU) p = 1 - Math.pow(1 - uu / arriveU, 3);
        else {
          const holdEnd = Math.max(budget, b.holdUntil ? b.holdUntil - t0 : 0);
          p = el <= holdEnd ? 1 : 1 - clamp((el - holdEnd) / 320, 0, 1);
        }
        b.root.position.x = b.home.x + nx * travel * p;
        b.root.position.z = b.home.z + nz * travel * p;
      }, () => { b.root.position.copy(b.home); b.holdUntil = 0; });
      return budget;
    }
    function flinch(id) {
      const b = bodies[id]; if (!b || b.dead) return;
      // THE IMPACT — the same angle, pushed in. A cut here would be a different
      // design and §11.11 has not been ruled on; a push is not a cut.
      shotB('impact', { actor: actorId, target: id });
      restLater(940);                      // pacing.damage + settle: back to rest
      oneShot(b, 'hit');
      flashOn(b); shockRing(b); shake(CFG.fx.shake);
      const ax = b.home.x - (bodies[actorId] ? bodies[actorId].home.x : b.home.x);
      const az = b.home.z - (bodies[actorId] ? bodies[actorId].home.z : b.home.z);
      const L = Math.hypot(ax, az) || 1;
      tween(CFG.fx.flinchMs, (u) => {
        const e = Math.sin(u * Math.PI);
        b.root.position.x = b.home.x + (ax / L) * CFG.fx.flinchM * e;
        b.root.position.z = b.home.z + (az / L) * CFG.fx.flinchM * e;
      }, () => { if (!b.dead) b.root.position.copy(b.home); });
    }

    // ---- anchors -------------------------------------------------------------
    const _v = new TH.Vector3();
    function anchor(id) {
      const b = bodies[id];
      if (!b || !W.cam) return null;
      const cv = W.R.domElement, rect = cv.getBoundingClientRect();
      const wpx = rect.width, hpx = rect.height;
      _v.set(b.root.position.x, b.root.position.y, b.root.position.z).project(W.cam);
      const fx = (_v.x * 0.5 + 0.5) * wpx + rect.left;
      const fy = (-_v.y * 0.5 + 0.5) * hpx + rect.top;
      _v.set(b.root.position.x, b.root.position.y + b.h, b.root.position.z).project(W.cam);
      const ty = (-_v.y * 0.5 + 0.5) * hpx + rect.top;
      const h = Math.max(8, fy - ty);
      const vis = !b.dead && b.root.visible && _v.z < 1 &&
                  fx > -200 && fx < wpx + 200 && fy > -200 && fy < hpx + 400;
      return { x: fx, y: fy, h: h, vis: vis };
    }

    // ---- the tick ------------------------------------------------------------
    // This module has NO renderer and NO render call of its own: play3d's loop()
    // is already drawing every frame under the modal panel (its own phys() comment
    // says so). All this does is advance mixers/tweens, drive ORBIT, and hand
    // battle_turnbased the projection callback it needs.
    // ================= THE BOOM, CHOSEN ON TONE (wave 4) =====================
    // The meter's own subtraction, run inside the game at 320x180. See TONE.
    let toneLive = { ok: false, why: 'waiting for the cast' }, toneDone = false;
    // ---- SAY WHICH SPACE THE BYTES ARE IN, AND CONVERT ONCE ------------------
    // r185 renders into a non-XR render target in the LINEAR working space
    // whatever the texture declares, and this probe reads that target directly —
    // so its bytes are LINEAR and the page's own OutputPass, which is what the
    // player and the meter see, is not in the loop. Differencing linear bytes
    // measures a dark site through a crushed transfer: MEASURED, and it is why
    // the first build of this probe picked the WRONG boom at the forest (edgeRGB
    // 12.88 -> 11.11 where the truth table's best rung was a third one).
    // This is the one conversion the r185 rules ASK for — the pass that would
    // have done it is absent, so exactly one explicit encode is applied here and
    // nothing else in this file converts anything. It is NOT the double
    // `convertSRGBToLinear` the notes warn about; that is a conversion applied on
    // top of the renderer's own, and the renderer performed none.
    // TONE MAPPING IS NOT APPLIED and that is the probe's stated approximation:
    // it moves highlights, it is monotone, and this is a RANKING.
    const _srgbLUT = (function () {
      const t = new Uint8Array(256);
      for (let i = 0; i < 256; i++) {
        const c = i / 255;
        const v = c <= 0.0031308 ? c * 12.92 : 1.055 * Math.pow(c, 1 / 2.4) - 0.055;
        t[i] = Math.max(0, Math.min(255, Math.round(v * 255)));
      }
      return t;
    })();
    function castReady() {
      for (const id of order) if (bodies[id] && bodies[id].tier === 'proxy') return false;
      return order.length > 0;
    }
    // ONE BODY'S NUMBERS OUT OF TWO BUFFERS. `full` is the frame with the cast in
    // it, `bg` the same frame without — so `mask` IS the silhouette, shadow and
    // alpha and all, rather than a guess at where the body is. Buffer rows run
    // BOTTOM-UP out of readRenderTargetPixels and the projection is done straight
    // into that space, which is why there is no flip anywhere below: a flip that
    // exists in one place and not the other is the classic way this measurement
    // comes back plausible and wrong.
    function toneBody(b, cam2, full, bg, rw, rh) {
      const bx = new TH.Box3().setFromObject(b.root);
      let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
      for (let i = 0; i < 8; i++) {
        _v.set(i & 1 ? bx.max.x : bx.min.x, i & 2 ? bx.max.y : bx.min.y, i & 4 ? bx.max.z : bx.min.z).project(cam2);
        const px = (_v.x * 0.5 + 0.5) * rw, py = (_v.y * 0.5 + 0.5) * rh;
        if (px < x0) x0 = px; if (px > x1) x1 = px;
        if (py < y0) y0 = py; if (py > y1) y1 = py;
      }
      const M = 6;
      const ax0 = Math.max(0, Math.floor(x0 - M)), ay0 = Math.max(0, Math.floor(y0 - M));
      const ax1 = Math.min(rw, Math.ceil(x1 + M)), ay1 = Math.min(rh, Math.ceil(y1 + M));
      const w = ax1 - ax0, h = ay1 - ay0;
      if (w < 4 || h < 4) return null;
      const m = new Uint8Array(w * h);
      const S = _srgbLUT;                    // linear byte -> display byte, once
      let n = 0;
      for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
        const i = ((y + ay0) * rw + (x + ax0)) * 4;
        const d = Math.max(Math.abs(S[full[i]] - S[bg[i]]), Math.abs(S[full[i + 1]] - S[bg[i + 1]]), Math.abs(S[full[i + 2]] - S[bg[i + 2]]));
        if (d > 12) { m[y * w + x] = 1; n++; }
      }
      if (n < 12) return null;
      const at = (x, y) => (x < 0 || y < 0 || x >= w || y >= h) ? 0 : m[y * w + x];
      const eRGB = [0, 0, 0], rRGB = [0, 0, 0];
      let nE = 0, nR = 0, sL = 0, sL2 = 0;
      const K = 1, RING = 4;                 // one twenty-fifth of the meter's pixels
      for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
        const p = y * w + x, i = ((y + ay0) * rw + (x + ax0)) * 4;
        if (m[p]) {
          // the EDGE BAND: a body pixel with a background pixel within K. That
          // band is what an eye reads a silhouette by and what the shipped meter
          // scores, so it is what is scored here.
          let edge = 0;
          for (let dy = -K; dy <= K && !edge; dy++) for (let dx = -K; dx <= K; dx++) if (!at(x + dx, y + dy)) { edge = 1; break; }
          if (edge) { eRGB[0] += S[full[i]]; eRGB[1] += S[full[i + 1]]; eRGB[2] += S[full[i + 2]]; nE++; }
        } else {
          let near = 0;
          for (let dy = -RING; dy <= RING && !near; dy++) for (let dx = -RING; dx <= RING; dx++) if (at(x + dx, y + dy)) { near = 1; break; }
          if (near) {
            // read off the BACKGROUND buffer, so a body's own bloom or contact
            // shadow never inflates the contrast it is being scored against
            rRGB[0] += S[bg[i]]; rRGB[1] += S[bg[i + 1]]; rRGB[2] += S[bg[i + 2]]; nR++;
            const L = 0.2126 * S[bg[i]] + 0.7152 * S[bg[i + 1]] + 0.0722 * S[bg[i + 2]];
            sL += L; sL2 += L * L;
          }
        }
      }
      if (!nE || !nR) return null;
      const dr = eRGB[0] / nE - rRGB[0] / nR, dg = eRGB[1] / nE - rRGB[1] / nR, db = eRGB[2] / nE - rRGB[2] / nR;
      const mL = sL / nR;
      return { edgeRGB: Math.sqrt((dr * dr + dg * dg + db * db) / 3),
               clutter: Math.sqrt(Math.max(0, sL2 / nR - mL * mL)), px: n };
    }
    function toneProbe() {
      const t0 = now();
      const pitches = (camOn() && CAM.solve.pitches && CAM.solve.pitches.length) ? CAM.solve.pitches : [basePitch];
      if (pitches.length < 2) return { ok: false, why: 'one candidate boom' };
      const rw = TONE.res[0], rh = TONE.res[1];
      const rt = new TH.WebGLRenderTarget(rw, rh, { depthBuffer: true, stencilBuffer: false });
      const cam2 = new TH.PerspectiveCamera(CAM.fov.rest, W.cam.aspect, W.cam.near, W.cam.far);
      const full = new Uint8Array(rw * rh * 4), bg = new Uint8Array(rw * rh * 4);
      const prevRT = W.R.getRenderTarget();
      // THE MARKERS ARE NOT THE CAST. Both rings are ground decals under a body's
      // feet; counted as silhouette they would flatter every candidate equally
      // and add noise to none of them usefully, so they sit out both passes.
      const ringsWere = [targetRing.visible, actorRing.visible];
      targetRing.visible = actorRing.visible = false;
      const savedPitch = basePitch;
      const rows = [];
      try {
        for (const p of pitches) {
          basePitch = p;                            // solveShot reads it
          let pose = null;
          try { pose = solveShot('round', {}); } catch (e) { continue; }
          camBasis(pose.yaw, pose.pitch, camB);
          cam2.fov = pose.fov; cam2.aspect = W.cam.aspect;
          cam2.position.set(pose.ax + camB.boom.x * pose.dist,
                            pose.ay + camB.boom.y * pose.dist,
                            pose.az + camB.boom.z * pose.dist);
          cam2.up.set(0, 1, 0);
          cam2.lookAt(pose.ax, pose.ay, pose.az);
          cam2.updateProjectionMatrix(); cam2.updateMatrixWorld();
          root.visible = false;
          W.R.setRenderTarget(rt); W.R.render(W.scene, cam2);
          W.R.readRenderTargetPixels(rt, 0, 0, rw, rh, bg);
          root.visible = true;
          W.R.setRenderTarget(rt); W.R.render(W.scene, cam2);
          W.R.readRenderTargetPixels(rt, 0, 0, rw, rh, full);
          const per = [];
          for (const id of order) {
            const b = bodies[id];
            if (!b || b.dead || b.root.visible === false) continue;
            const r = toneBody(b, cam2, full, bg, rw, rh);
            if (r) per.push({ id: id, side: b.side, edgeRGB: +r.edgeRGB.toFixed(2), clutter: +r.clutter.toFixed(2) });
          }
          if (!per.length) continue;
          const mean = per.reduce((s, r) => s + r.edgeRGB, 0) / per.length;
          const min = Math.min(...per.map(r => r.edgeRGB));
          const clut = per.reduce((s, r) => s + r.clutter, 0) / per.length;
          // HALF THE MEAN AND HALF THE MINIMUM. Pricing only the mean buys a good
          // average and one invisible body — scoreView's own comment, and the
          // measurement behind it: at crag one party body reads 2.7 against a
          // four-body mean of 21.4.
          rows.push({ pitch: p, score: +(0.5 * mean + 0.5 * min - TONE.wClutter * clut).toFixed(3),
                      mean: +mean.toFixed(2), min: +min.toFixed(2), clutter: +clut.toFixed(2), bodies: per });
        }
      } finally {
        basePitch = savedPitch;
        root.visible = true;
        targetRing.visible = ringsWere[0]; actorRing.visible = ringsWere[1];
        W.R.setRenderTarget(prevRT);
        rt.dispose();
      }
      if (!rows.length) return { ok: false, why: 'no candidate produced a silhouette' };
      let win = rows[0];
      for (const r of rows) if (r.score > win.score) win = r;
      // THE INCUMBENT IS THE RUNG THE GEOMETRIC SOLVER ALREADY CHOSE, scored on
      // the same evidence as its challengers — never assumed to be the worst.
      let inc = null;
      for (const r of rows) if (Math.abs(r.pitch - savedPitch) < 1e-6) inc = r;
      const decisive = !inc || win.score > inc.score + Math.abs(inc.score) * TONE.margin;
      const chose = decisive ? win.pitch : savedPitch;
      return { ok: true, chose: chose, best: win.pitch, was: savedPitch,
               moved: chose !== savedPitch, decisive: decisive,
               incScore: inc ? inc.score : null, winScore: win.score, margin: TONE.margin,
               rows: rows, ms: +(now() - t0).toFixed(1), res: [rw, rh] };
    }
    // ONE SHOT AT IT, and the frame it happens on is the frame the cast finishes
    // arriving. The opening `round` move is still easing then (900 ms), so
    // re-issuing it lands as ONE continuous move rather than a correction — which
    // is also why this must not be deferred to a later beat.
    function toneMaybe() {
      if (toneDone || !toneOn()) return;
      const waited = now() - camT0;
      if (!castReady() && waited < TONE.waitMs) return;
      toneDone = true;
      if (!castReady()) { toneLive = { ok: false, why: 'cast never left proxy in ' + TONE.waitMs + ' ms' }; return; }
      try { toneLive = toneProbe(); } catch (e) { toneLive = { ok: false, why: 'threw: ' + e.message }; return; }
      // AND IT ONLY EVER LANDS ON THE OPENING. If the models were slow enough
      // that a turn has already started, the fight owns the camera and a boom
      // correction would read as a mistake being fixed in front of the player —
      // so the probe's answer is RECORDED and not applied. That is what lets
      // `waitMs` be generous without buying a camera swing mid-swing.
      if (toneLive.ok && toneLive.moved && RIG.kind === 'round') {
        basePitch = toneLive.chose;
        shotB('round', { ms: 700, why: 'tone' });
      } else if (toneLive.ok && toneLive.moved) {
        toneLive.applied = false; toneLive.why = 'a beat already owns the camera (' + RIG.kind + ')';
      }
    }

    const clock = new TH.Clock();
    let ticks = 0;
    function tick() {
      if (deadStage) return;
      raf = requestAnimationFrame(tick);
      const dt = Math.min(clock.getDelta(), 0.1);
      const t = (now() - camT0) / 1000;

      // ---- THE CAMERA, one move at a time -----------------------------------
      // The rig eases from pose to pose; a queued second leg (the KO's slow push,
      // the victory dolly) starts the frame the first one lands. ORBIT is the
      // only surface written, exactly as the spike established, so teardown is
      // still a six-number copy-back.
      if (RIG.to) {
        const u = clamp((now() - RIG.t0) / RIG.ms, 0, 1);
        const e = (EASE[RIG.ease] || EASE.io)(u);
        const A = RIG.from, B = RIG.to;
        const cur = RIG.cur || (RIG.cur = {});
        cur.kind = B.kind; cur.fov = lerp(A.fov, B.fov, e);
        cur.ax = lerp(A.ax, B.ax, e); cur.ay = lerp(A.ay, B.ay, e); cur.az = lerp(A.az, B.az, e);
        cur.yaw = lerp(A.yaw, B.yaw, e); cur.pitch = lerp(A.pitch, B.pitch, e);
        cur.dist = lerp(A.dist, B.dist, e); cur.tilt = lerp(A.tilt == null ? camSaved.tilt : A.tilt, B.tilt || 0, e);
        if (u >= 1 && RIG.next) {
          const nx = RIG.next; RIG.next = null;
          goTo(nx.pose, nx.ms, nx.ease, nx.why);
        }
      }
      const C = RIG.cur;
      if (C) {
        O.yaw = C.yaw; O.pitch = C.pitch; O.dist = C.dist; O.tilt = C.tilt;
        // A CAMERA THAT IS ALIVE — 5.4 s, not the diorama's 103 s cycle that no
        // player ever sees a whole one of. Amplitude is centimetres on the aim.
        const D = CAM.drift, ph = (now() - camT0) / D.ms * Math.PI * 2;
        const dx = camOn() ? Math.sin(ph) * D.amp : 0;
        const dy = camOn() ? Math.sin(ph * 0.61 + 1.3) * D.amp * 0.55 : 0;
        const dz = camOn() ? Math.cos(ph * 0.83 + 0.4) * D.amp : 0;
        O.panX = C.ax - P0.x + dx; O.panY = C.ay - P0.y - 1 + dy; O.panZ = C.az - P0.z + dz;
        // THE LENS. play3d never touches fov after construction, so this is the
        // one write and teardown restores the number it found.
        if (W.cam && Math.abs(W.cam.fov - C.fov) > 0.005) { W.cam.fov = C.fov; W.cam.updateProjectionMatrix(); }
      }
      // THE SHAKE rides the pan offsets, which are the camera's own aim point —
      // so a shake can never leave the camera somewhere ORBIT does not describe.
      if (shakeAmp > 0) {
        const su = clamp((now() - shakeT0) / shakeDur, 0, 1);
        if (su >= 1) shakeAmp = 0;
        else {
          const a = shakeAmp * (1 - su) * (1 - su), ph = (now() - shakeT0) / 1000;
          O.panX += Math.sin(ph * 61) * a;
          O.panY += Math.sin(ph * 47 + 1.1) * a * 0.85;
          O.panZ += Math.sin(ph * 53 + 2.3) * a * 0.5;
        }
      }

      toneMaybe();
      runTweens();
      for (const m of mixers) m.update(dt);
      placeRing(targetRing, targetId, 1.0 + Math.sin(t * 4.2) * 0.06);
      placeRing(actorRing, actorId, 0.9);
      ticks++;
      if (cfg.onFrame) { try { cfg.onFrame(stage); } catch (e) { } }
    }
    raf = requestAnimationFrame(tick);

    const stage = {
      world: true,
      canvas: W.R.domElement, scene: W.scene, camera: W.cam, renderer: W.R,
      // THE HONEST FRAME COUNT is the world renderer's own, not this module's rAF:
      // the picture on screen is drawn by play3d's loop, so that is the counter a
      // harness must assert is climbing.
      get frames() { return W.R.info.render.frame; },
      get ticks() { return ticks; },
      plan: plan,
      // WHERE THIS FIGHT STAGED, and how far from the player it moved to do it —
      // the receipt the relocation ruling is checkable against, off the live
      // stage. `player` is the body's own position at create(): this path never
      // moves it, and teardown asserts it is still there.
      site: { R: site.R, d: site.d == null ? 0 : site.d, dy: site.dy == null ? 0 : site.dy,
              bearing: site.bearing == null ? null : site.bearing,
              at: { x: +A0.x.toFixed(3), y: +A0.y.toFixed(3), z: +A0.z.toFixed(3) },
              player: { x: +P0.x.toFixed(3), y: +P0.y.toFixed(3), z: +P0.z.toFixed(3) },
              cands: site.cands, screened: site.screened, solved: site.solved, ms: site.ms,
              // WHY THIS SITE AND NOT THE ONE THE LADDER WOULD HAVE TAKEN —
              // null when the quality term is off or had no second candidate.
              quality: site.quality || null },
      anchor: anchor,
      tierOf(id) { return bodies[id] ? bodies[id].tier : null; },
      tiers() { const o = {}; for (const id of order) o[id] = bodies[id].tier; return o; },
      // WHICH SIDE A BODY IS ON, because a harness must never infer it from the id.
      // `/^m/` — the filter tools/battle_shots.mjs uses to find the foes — matches
      // **maren**, so the audit's own impact captures had Vesper attacking her own
      // party member. An id is not a side.
      sides() { const o = {}; for (const id of order) o[id] = bodies[id].side; return o; },
      // WHERE A BODY ACTUALLY IS, in world metres — the diorama's own QA accessor
      // (battle_stage3d :3061), implemented here so ONE instrument can measure both
      // arenas. `floorY` is the REAL ground under the body (SIM.ground), which is
      // the whole point in this stage: a KO that sinks 0.55 m in the diorama sinks
      // 0.55 m through solid rock here. QA path only — it allocates.
      at(id) {
        const b = bodies[id]; if (!b) return null;
        // THE ALPHA THIS STAGE SET, not a survey of the model's own materials: a
        // sourced GLB can ship a legitimately transparent mesh at opacity 0 (an
        // eye decal, a cut-out), and taking the minimum over the tree reported a
        // fully solid body as ALREADY GONE at 1 ms. A stage reports what it did.
        const alpha = b.root.visible === false ? 0 : (b.alpha == null ? 1 : b.alpha);
        let fy = null;
        try { fy = window.SIM ? window.SIM.ground(b.root.position.x, b.root.position.z, b.home.y) : null; } catch (e) { }
        return { x: b.root.position.x, y: b.root.position.y, z: b.root.position.z,
                 h: b.h, w: b.w, side: b.side, dead: b.dead, tier: b.tier,
                 alpha: +alpha.toFixed(3), floorY: fy == null ? null : +fy.toFixed(3),
                 bob: { x: +b.bob.rotation.x.toFixed(4), y: +b.bob.rotation.y.toFixed(4),
                        z: +b.bob.rotation.z.toFixed(4) } };
      },
      clipsOf(id) { const b = bodies[id]; return b && b.actions ? Object.keys(b.actions) : []; },
      // THE CURSOR MOVES, THE FRAME FOLLOWS. Re-solving `decide` when the player
      // picks a different foe is what keeps the thing being aimed at in shot —
      // `show:'actor'` resolves to the deciding body AND its target.
      setTarget(id) {
        const was = targetId;
        targetId = id && bodies[id] && !bodies[id].dead ? id : null;
        if (targetId && targetId !== was && actorId && RIG.kind === 'decide') shotB('decide', { ms: 380 });
      },
      // WHOSE TURN IT IS, as a shot. setActor(null) deliberately does NOT return
      // to rest: battle_turnbased clears the actor at settle() and announces the
      // action 300 ms later, so a return here would be a move the player sees
      // undone. The beat that follows owns the camera; restLater owns the rest.
      setActor(id) {
        const was = actorId;
        actorId = id && bodies[id] && !bodies[id].dead ? id : null;
        if (actorId && actorId !== was) shotB('decide', {});
      },
      act: act, flinch: flinch,
      ko(id) { const b = bodies[id]; if (b && !b.dead) markDead(b, false); },
      setDead(id, on) {
        const b = bodies[id]; if (!b) return;
        if (on && !b.dead) markDead(b, false); else if (!on && b.dead) revive(b);
      },
      // THE VICTORY MOVE — the second thing the KO lane wanted and could not
      // have. The boom swings round to three-quarter FRONT of the party (it
      // stops 54 deg short of the axis, so the shot the tally lands on is on the
      // same side of the line as every other shot in the fight) and dollies in
      // while they cheer. battle_turnbased gives it winHold + winCheer = 1520 ms
      // before the box arrives.
      cheer() {
        shotB('victory', {});
        for (const id of order) { const b = bodies[id]; if (b.side === 'party' && !b.dead) oneShot(b, 'cheer'); }
      },
      // ONE synchronous render through the PAGE's renderFrame(), so a QA photograph
      // is of the player's pipeline (GTAO + bloom + OutputPass), never a second one.
      // No preserveDrawingBuffer is needed: toDataURL in the same task as the draw
      // still sees the buffer — which is one shipping cost the diorama carries and
      // this path does not.
      snapshot() {
        try { if (W.render) W.render(); return W.R.domElement.toDataURL('image/png'); }
        catch (e) { return null; }
      },
      fx: { shake: shake, flash: (id) => bodies[id] && flashOn(bodies[id]),
            ring: (id) => bodies[id] && shockRing(bodies[id]) },
      // ---- THE CAMERA, AS QA SURFACE ---------------------------------------
      // Everything an instrument needs to assert the shot language without
      // knowing anything about how it is implemented.
      cam() {
        const c = RIG.cur;
        return { on: camOn(), kind: RIG.kind, actor: actorId, target: targetId,
                 moves: RIG.moves, refusals: RIG.refusals,
                 lastRefusal: RIG.lastRefusal, base: { yaw: +baseYaw.toFixed(4), pitch: +basePitch.toFixed(4) },
                 view: plan.view || null, axisRef: axisRef,
                 pose: c ? { ax: +c.ax.toFixed(3), ay: +c.ay.toFixed(3), az: +c.az.toFixed(3),
                             yaw: +c.yaw.toFixed(4), pitch: +c.pitch.toFixed(4),
                             dist: +c.dist.toFixed(3), fov: +c.fov.toFixed(2) } : null,
                 axis: c ? axisCheck(c) : null,
                 orbit: { yaw: +O.yaw.toFixed(4), pitch: +O.pitch.toFixed(4), dist: +O.dist.toFixed(3),
                          tilt: +O.tilt.toFixed(4), panX: +O.panX.toFixed(3), panY: +O.panY.toFixed(3), panZ: +O.panZ.toFixed(3) },
                 fov: W.cam ? +W.cam.fov.toFixed(2) : null, log: RIG.log.slice(-24) };
      },
      // SOLVE EVERY SHOT IN THE TABLE against the cast as it stands and report
      // the 180-degree check for each — the automated assertion BET B asks for.
      shotTable(o) {
        o = o || {};
        const out = [];
        for (const kind of Object.keys(CAM.shots)) {
          const opt = Object.assign({ actor: actorId || order[0], target: null, victim: null }, o[kind] || {});
          if (!opt.target) { for (const id of order) if (bodies[id].side === 'foe' && !bodies[id].dead) { opt.target = id; break; } }
          if (!opt.victim) opt.victim = opt.target;
          const raw = solveShot(kind, opt);
          const chk = axisCheck(raw);
          const safe = solveShotSafe(kind, opt);
          out.push({ kind: kind, show: CAM.shots[kind].show, cut: !!CAM.shots[kind].cut,
                     dist: +raw.dist.toFixed(2), fov: +raw.fov.toFixed(1),
                     pitch: +raw.pitch.toFixed(3), yawOff: +(raw.yaw - baseYaw).toFixed(3),
                     axis: chk, refused: !safe, softened: safe ? safe.softened : null });
        }
        return out;
      },
      // drive one shot by name (the contact sheet), and the 'why' goes in the log
      shotTo(kind, o) { return shotB(kind, Object.assign({ why: 'qa' }, o || {})); },
      // ---- pixels: what an instrument needs to MEASURE legibility -----------
      // Toggling a body's visibility and re-rendering is how a silhouette is
      // extracted honestly (the frame with the body minus the frame without it).
      // `xray` drops depth testing on the cast, so the SAME diff yields the
      // silhouette the body WOULD have had unoccluded — occlusion is then one
      // subtraction rather than an assertion.
      qa: {
        ids() { return order.slice(); },
        show(id, on) { const b = bodies[id]; if (b) b.root.visible = !!on; },
        showAll(on) { for (const id of order) if (!bodies[id].dead) bodies[id].root.visible = !!on; },
        // DEPTH WRITE GOES WITH DEPTH TEST. Leaving depthWrite on while depthTest
        // is off scribbles the body's depth over the terrain's, and GTAO reads
        // that buffer — so the "free" silhouette came back with a different AO
        // ring around it and the occlusion figure went NEGATIVE. Both flags are
        // saved per material and restored, never assumed to have been true.
        xray(on) {
          for (const id of order) {
            const b = bodies[id]; if (!b || !b.obj) continue;
            b.obj.traverse((o2) => {
              if (!o2.isMesh || !o2.material) return;
              const ms = Array.isArray(o2.material) ? o2.material : [o2.material];
              for (const m of ms) {
                if (on) {
                  if (!m.__bcSave) m.__bcSave = { t: m.depthTest, w: m.depthWrite, o: o2.renderOrder };
                  m.depthTest = false; m.depthWrite = false;
                } else if (m.__bcSave) {
                  m.depthTest = m.__bcSave.t; m.depthWrite = m.__bcSave.w; m.__bcSave = null;
                }
                m.needsUpdate = true;
              }
              o2.renderOrder = on ? 999 : 0;
            });
          }
        },
        // the body's own world box, projected — the region a mask lives in
        box(id) {
          const b = bodies[id]; if (!b || !W.cam) return null;
          const cv = W.R.domElement, rect = cv.getBoundingClientRect();
          const bx = new TH.Box3().setFromObject(b.root);
          let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
          for (let i = 0; i < 8; i++) {
            _v.set(i & 1 ? bx.max.x : bx.min.x, i & 2 ? bx.max.y : bx.min.y, i & 4 ? bx.max.z : bx.min.z).project(W.cam);
            const px = (_v.x * 0.5 + 0.5) * rect.width, py = (-_v.y * 0.5 + 0.5) * rect.height;
            if (px < x0) x0 = px; if (px > x1) x1 = px;
            if (py < y0) y0 = py; if (py > y1) y1 = py;
          }
          return { x0: x0, y0: y0, x1: x1, y1: y1, w: rect.width, h: rect.height,
                   side: b.side, dead: b.dead, tier: b.tier };
        },
      },
      // WHAT THE TONAL BOOM CHOOSER DID — every candidate's score, the rung it
      // took, the rung the geometric solver had picked, and how long it cost.
      // A run where it never fired says WHY rather than reporting nothing.
      tone() { return Object.assign({ on: toneOn(), done: toneDone, basePitch: +basePitch.toFixed(4) }, toneLive || {}); },
      draw() { if (W.render) W.render(); return W.R.info.render.frame; },
      // ---- TEARDOWN: TOTAL, AND EVERY LINE OF IT IS A RESTORE ---------------
      // The audit's constraint (§11.12) and the four post-battle queue tickets.
      // What this path CAN leak is not a context (it never made one) but WORLD
      // STATE — so the list is: our group out of the scene and disposed, mixers
      // stopped, timers cleared, rAF cancelled, the camera's ORBIT restored
      // field-by-field from the copy taken at create(), the player's body
      // visibility restored by identity. It touches no `at`, emits no 'eb-scene',
      // writes no save, and never calls SIM.tp().
      // THAT LAST CLAUSE IS NOW LOAD-BEARING. Relocation moves the ARENA, not the
      // player, so "the player is returned exactly where they stood, whatever
      // distance the fight relocated" is true by construction rather than by a
      // restore that could be forgotten: there is no player-position write on
      // this path to undo. Do not "improve" relocation by teleporting the body.
      destroy() {
        if (deadStage) return;
        deadStage = true;
        if (raf) cancelAnimationFrame(raf);
        clearTimeout(restT);
        tweens.length = 0;
        for (const id of order) { try { clearTimeout(bodies[id]._backT); } catch (e) { } }
        for (const m of mixers) { try { m.stopAllAction(); m.uncacheRoot(m.getRoot()); } catch (e) { } }
        mixers.length = 0;
        if (root.parent) root.parent.remove(root);
        for (const g of owned.geo) { try { g.dispose(); } catch (e) { } }
        for (const m of owned.mat) { try { m.dispose(); } catch (e) { } }
        for (const t of owned.tex) { try { t.dispose(); } catch (e) { } }
        owned.geo.length = owned.mat.length = owned.tex.length = 0;
        // the camera, restored to the numbers it had before the battle
        O.yaw = camSaved.yaw; O.pitch = camSaved.pitch; O.dist = camSaved.dist;
        O.tilt = camSaved.tilt;
        O.panX = camSaved.panX; O.panY = camSaved.panY; O.panZ = camSaved.panZ;
        // AND THE LENS. The shot language is the only thing in this game that
        // ever writes cam.fov after construction; a battle that left a 27 deg
        // lens on the overworld would be a silent, permanent regression that no
        // ORBIT receipt could see.
        if (W.cam && camSaved.fov != null && W.cam.fov !== camSaved.fov) {
          W.cam.fov = camSaved.fov; W.cam.updateProjectionMatrix();
        }
        if (W.ch && chSaved !== null) W.ch.visible = chSaved;
        if (window.BattleStage3D && window.BattleStage3D._live === stage) {
          window.BattleStage3D._live = null;
        }
        if (window.BattleWorld) window.BattleWorld._live = null;
      },
    };
    if (window.BattleStage3D) window.BattleStage3D._live = stage;
    window.BattleWorld._live = stage;
    // A LEDGER, so a teardown receipt can say WHICH stage it tore down. A battle
    // that fell back to the diorama and tore that down cleanly proves nothing
    // about this path, and the fallback is silent by design.
    window.BattleWorld.created++;
    return stage;
  }

  // ============================ INSTALL =====================================
  // Wrap BattleStage3D.create. battle_stage3d.js is injected LAZILY during the
  // battle's entry fade, so the module may not exist yet: an accessor on window
  // catches the assignment, patches, and hands the real object on. Setting the
  // property is idempotent and the original create() is kept, so a page can flip
  // back at runtime (BattleWorld.enabled = false) and get the diorama.
  const api = {
    version: 1, on: true, installed: false, enabled: true, _live: null,
    created: 0, refused: 0, relocated: 0, crashed: 0,
    CFG: CFG,
    // THE LADDER, live — an instrument can shorten it or widen a ring without a
    // code change, the same way --vismin / --bcam / --pitches work.
    RELOC: RELOC,
    // THE SHOT TABLE, live. `BattleWorld.CAM.on = false` is the A/B switch the
    // board is built from — one build, one flag, everything else identical.
    CAM: CAM,
    camOn() { return camOn(); },
    // THE TONAL BOOM CHOOSER, live. `BattleWorld.TONE.on = false` is the A/B the
    // separation board is built from — one build, one flag, everything else
    // identical — and `tone()` is the live stage's own receipt for it.
    TONE: TONE,
    toneOn() { return toneOn(); },
    // THE PLACEMENT-QUALITY TERM, live. `BattleWorld.PLACE.on = false` is the
    // A/B the placement board is built from; `sunLit` is callable so an
    // instrument can score a plan the search did not choose.
    PLACE: PLACE,
    placeOn() { return placeOn(); },
    sunLit: sunLit,
    sunDir: sunDir,
    tone() { return api._live && api._live.tone ? api._live.tone() : { on: toneOn(), ok: false, why: 'no battle' }; },
    solve(o) { return solveArena(o || { slots: slotsFor([{ id: 'a' }, { id: 'b' }], [{ id: 'm0' }, { id: 'm1' }]) }); },
    solveArena: solveArena,
    solveFixed: solvePlacement,
    // THE SHIPPED STAGING PATH, callable. createWorldStage calls exactly this, so
    // an instrument that times `stage()` is timing what a battle pays, and one
    // that reads its `.R` is reading how far the fight really moved.
    stage(slots) {
      return stageArena(slots || slotsFor([{ id: 'a' }, { id: 'b' }], [{ id: 'm0' }, { id: 'm1' }]));
    },
    screenYaws: screenYaws,
    slotsFor: slotsFor,
    worldReady: worldReady,
    _debug() {
      return { on: true, installed: api.installed, enabled: api.enabled,
               worldReady: worldReady(), live: !!api._live,
               three: T() ? T().REVISION : null,
               created: api.created, refused: api.refused,
               relocated: api.relocated, crashed: api.crashed,
               rings: RELOC.rings.map(r => r.R),
               occluders: (occluders() || []).length,
               scatterDropped: _rc.dropped.slice(),
               lastPlan: window.__BW_LAST_PLAN || null,
               lastSite: window.__BW_LAST_SITE || null };
    },
  };
  window.BattleWorld = api;

  function patch(mod) {
    if (!mod || mod.__bwPatched) return mod;
    const orig = mod.create;
    // THERE IS NO DIORAMA FALLBACK ON THIS PATH (user ruling 2026-08-08). The
    // world arena used to answer a refusal by calling `orig` — the diorama — and
    // that line is deleted. A refusal now relocates inside createWorldStage (see
    // stageArena), and if even that fails we return NULL, which battle_turnbased
    // resolves to its DOM stage: the coarsest tier, a crash guard, and NOT a
    // second arena to maintain. `BattleWorld.enabled = false` still hands the
    // whole page back to the diorama in one assignment — that is the A/B switch
    // the boards are built from and it is deliberately not a fallback.
    mod.create = function (cfg) {
      if (!api.enabled) return orig.call(mod, cfg);
      try { return createWorldStage(cfg); }
      catch (e) {
        console.warn('[BattleWorld] world arena threw — DOM stage (crash guard)', e);
        api.crashed++;
        return null;
      }
    };
    mod.__bwPatched = true;
    api.installed = true;
    return mod;
  }

  if (window.BattleStage3D) patch(window.BattleStage3D);
  else {
    let held = undefined;
    try {
      Object.defineProperty(window, 'BattleStage3D', {
        configurable: true,
        get() { return held; },
        set(v) { held = v; try { patch(v); } catch (e) { } },
      });
    } catch (e) { console.warn('[BattleWorld] could not install the accessor', e); }
  }
})();
