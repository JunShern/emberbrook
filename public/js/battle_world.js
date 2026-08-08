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
// solid and stays there); reduced-motion; a shot language (BET B). Formation
// constants are BORROWED from BattleStage3D.CFG.form on purpose, so a side-by-side
// differs by the WORLD and not by the blocking.
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
    place: { probeR: 0.42, maxDrop: 2.2, ring: [0, 0.5, -0.5, 1.0, -1.0, 1.6, -1.6] },
  };

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
  const _rc = { ray: null, v0: null, v1: null, set: null, stamp: 0 };
  const NOT_OCCLUDER = /^(__owsky|__owridge|__owveil|amb_|bw_)/;
  function occluders() {
    const TH = T();
    if (!TH) return null;
    let sc = null;
    try { sc = typeof scene !== 'undefined' ? scene : null; } catch (e) { return null; }
    if (!sc) return null;
    // rebuilt at most every 2 s: a battle is short and the region does not change
    if (_rc.set && (now() - _rc.stamp) < 2000) return _rc.set;
    const out = [];
    sc.traverse((o) => {
      if (!(o.isMesh || o.isInstancedMesh) || o.isSkinnedMesh) return;
      if (o.userData && (o.userData.isWalk || o.userData.isBattleWorld)) return;
      if (NOT_OCCLUDER.test(o.name || '')) return;
      let a = o;
      while (a) { if (a.userData && a.userData.isBattleWorld) return; a = a.parent; }
      if (o.visible) out.push(o);
    });
    _rc.set = out; _rc.stamp = now();
    return out;
  }
  function camPoseFor(P, yaw) {
    const p = CFG.cam.pitch, d = CFG.cam.dist;
    return { x: P.x + Math.cos(yaw) * Math.cos(p) * d,
             y: P.y + 1 + Math.sin(p) * d,
             z: P.z + Math.sin(yaw) * Math.cos(p) * d };
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
    const eye = camPoseFor(P, yaw);
    const vis = o.vis !== false;
    const out = { basis: { yaw, right: [rx, rz], fwd: [fx, fz], centre: [P.x, P.y, P.z], eye },
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
        // TWO RAYS, chest and head: a single chest ray calls a body standing
        // behind a low wall visible because the wall's top edge missed the ray.
        if (vis && (!seesPoint(eye, x, y + 0.9, z) || !seesPoint(eye, x, y + 1.5, z))) {
          lastWhy = 'occluded from the battle camera'; out.occluded++; continue;
        }
        done = { id: s.id, side: s.side, x: x, y: y + CFG.lift, z: z,
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
  function solveArena(o) {
    const base = (window.ORBIT && window.ORBIT.yaw) || 0;
    const cands = [0, 0.5, -0.5, 1.05, -1.05, 1.6, -1.6, 2.1, -2.1, Math.PI];
    let best = null;
    for (const d of cands) {
      const plan = solvePlacement(Object.assign({}, o, { yaw: base + d }));
      plan.yawDelta = +d.toFixed(3);
      if (plan.ok) return plan;
      if (!best || plan.placed.length > best.placed.length) best = plan;
    }
    return best;
  }

  // Slot geometry, borrowed from BattleStage3D.CFG.form so the two stages block
  // the same fight. `ax` is ACROSS the axis (negative = party side / screen left),
  // `az` is depth (positive = away from the camera).
  function slotsFor(party, foes) {
    const S3D = window.BattleStage3D;
    const f = (S3D && S3D.CFG && S3D.CFG.form) || {
      partyX: 3.2, partyDx: 1.05, partyZ: 0.35, partyDz: 2.0,
      foeX: 3.4, foeZ: -0.8, foeRank: 2.1, foeSpread: 3.2, foeJog: 0.78, foeChevron: 0.5 };
    const out = [];
    party.forEach((c, i) => {
      out.push({ id: c.id, side: 'party',
                 ax: -(f.partyX + i * f.partyDx),
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
      out.push({ id: c.id, side: 'foe', ax: ax, az: az });
    });
    return out;
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
    const plan = solveArena({ slots: slotsFor(party, foes) });

    // A FIGHT THAT CANNOT STAND DOES NOT STAND. If the real ground refuses even
    // one combatant the world arena RETURNS NULL, which battle_turnbased already
    // handles: it falls through to the DOM stage. (The right production answer is
    // to fall back to the diorama instead — one line, and it is called out in the
    // return; a spike that silently degrades to a worse look would hide exactly
    // the number §Q2 exists to measure.)
    if (!plan.ok && !cfg.forcePlace) {
      console.warn('[BattleWorld] placement refused', plan.failed);
      window.__BW_LAST_PLAN = plan;
      window.BattleWorld.refused++;
      return null;
    }
    window.__BW_LAST_PLAN = plan;

    const root = new TH.Group();
    root.name = 'bw_root';
    root.userData.isBattleWorld = true;              // never in collide/walkRef/allMeshes
    W.scene.add(root);

    // ---- the camera: ORBIT is the only thing we touch, and we own the copy ----
    const O = window.ORBIT;
    const camSaved = { yaw: O.yaw, pitch: O.pitch, dist: O.dist, tilt: O.tilt,
                       panX: O.panX, panY: O.panY, panZ: O.panZ };
    // THE TILT MUST GO TO ZERO, and finding that out was worth the spike on its
    // own. play3d aims the overworld boom UP by OWTILT (0.16 rad) about its own X
    // AFTER lookAt, deliberately, so the player sits high in frame and the ridges
    // are visible ("THE OVERWORLD BOOM"). Left alone during a battle it puts the
    // aim point at 0.5 + 0.5*tan(0.16)/tan(21deg) = 71% down the frame, i.e. the
    // whole fight in the bottom third, under the party status window. Measured
    // before the fix: the foes' feet projected at y 778 of 813.
    const camFrom = { pitch: O.pitch, dist: O.dist, tilt: O.tilt, yaw: O.yaw };
    const camTo = { pitch: CFG.cam.pitch, dist: CFG.cam.dist, tilt: 0,
                    yaw: (plan && plan.basis) ? plan.basis.yaw : O.yaw };
    // shortest arc, so a 180-degree arena flip does not swing the long way round
    camTo.yaw = camFrom.yaw + (((camTo.yaw - camFrom.yaw + Math.PI) % (2 * Math.PI) + 2 * Math.PI) % (2 * Math.PI) - Math.PI);
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
        if (c.dead) markDead(b, true);
      }).catch(() => { });
      if (c.dead) markDead(b, true);
    });

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
    const clock = new TH.Clock();
    let ticks = 0;
    function tick() {
      if (deadStage) return;
      raf = requestAnimationFrame(tick);
      const dt = Math.min(clock.getDelta(), 0.1);
      const t = (now() - camT0) / 1000;

      // the push-in, eased once, then held. Restored field-by-field on teardown.
      const u = clamp((now() - camT0) / CFG.cam.ms, 0, 1);
      const e = 1 - Math.pow(1 - u, 3);
      O.dist = lerp(camFrom.dist, camTo.dist, e);
      O.pitch = lerp(camFrom.pitch, camTo.pitch, e);
      O.tilt = lerp(camFrom.tilt, camTo.tilt, e);
      O.yaw = lerp(camFrom.yaw, camTo.yaw, e);
      // THE SHAKE rides the pan offsets, which are the camera's own aim point —
      // so a shake can never leave the camera somewhere ORBIT does not describe.
      O.panX = camSaved.panX; O.panY = camSaved.panY; O.panZ = camSaved.panZ;
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
      setTarget(id) { targetId = id && bodies[id] && !bodies[id].dead ? id : null; },
      setActor(id) { actorId = id && bodies[id] && !bodies[id].dead ? id : null; },
      act: act, flinch: flinch,
      ko(id) { const b = bodies[id]; if (b && !b.dead) markDead(b, false); },
      setDead(id, on) {
        const b = bodies[id]; if (!b) return;
        if (on && !b.dead) markDead(b, false); else if (!on && b.dead) revive(b);
      },
      cheer() { for (const id of order) { const b = bodies[id]; if (b.side === 'party' && !b.dead) oneShot(b, 'cheer'); } },
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
      // ---- TEARDOWN: TOTAL, AND EVERY LINE OF IT IS A RESTORE ---------------
      // The audit's constraint (§11.12) and the four post-battle queue tickets.
      // What this path CAN leak is not a context (it never made one) but WORLD
      // STATE — so the list is: our group out of the scene and disposed, mixers
      // stopped, timers cleared, rAF cancelled, the camera's ORBIT restored
      // field-by-field from the copy taken at create(), the player's body
      // visibility restored by identity. It touches no `at`, emits no 'eb-scene',
      // writes no save, and never calls SIM.tp().
      destroy() {
        if (deadStage) return;
        deadStage = true;
        if (raf) cancelAnimationFrame(raf);
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
    created: 0, refused: 0,
    CFG: CFG,
    solve(o) { return solveArena(o || { slots: slotsFor([{ id: 'a' }, { id: 'b' }], [{ id: 'm0' }, { id: 'm1' }]) }); },
    solveArena: solveArena,
    solveFixed: solvePlacement,
    slotsFor: slotsFor,
    worldReady: worldReady,
    _debug() {
      return { on: true, installed: api.installed, enabled: api.enabled,
               worldReady: worldReady(), live: !!api._live,
               three: T() ? T().REVISION : null,
               lastPlan: window.__BW_LAST_PLAN || null };
    },
  };
  window.BattleWorld = api;

  function patch(mod) {
    if (!mod || mod.__bwPatched) return mod;
    const orig = mod.create;
    mod.create = function (cfg) {
      if (!api.enabled) return orig.call(mod, cfg);
      let st = null;
      try { st = createWorldStage(cfg); }
      catch (e) { console.warn('[BattleWorld] world arena failed, falling back to the diorama', e); st = null; }
      if (st) return st;
      return orig.call(mod, cfg);
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
