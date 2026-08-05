// npc.js — window.Npc: the people of the town.
// WORLD-POPULATION agent owned. Additive and self-contained: it no-ops silently
// on a page with no THREE, in a scene nobody lives in, and before its data file
// lands. There is NOT ONE character, coordinate, line or district in this file —
// adding a villager is an edit to public/game/npcs.json and nothing else.
//
// FOUR RULES IT KEEPS (the route_overlay discipline, restated for bodies):
//  1. NEVER a floor, a wall or an occluder. Everything it builds goes into ONE
//     THREE.Group added to `scene` and is never pushed into collide / walkRef /
//     allMeshes. A person you can walk through is a smaller bug than a person
//     who becomes a step, an invisible wall, or a thing the presence-marker
//     thinks is hiding you — and the walk network is law in the routed town.
//  2. NEVER touches game state except through GS (which only dialogue.js does).
//     This file reads SIM and paints; it does not decide anything.
//  3. DEPTH-HONEST. Plates are depthTest:true with the default render order, so
//     in a cinematic shot the bundle's OWN baked depth map hides whatever the
//     backdrop hides. A villager standing behind a house is behind the house.
//  4. STENCIL-CLEAN. Nothing here writes stencil. The player's ghost pass owns
//     stencil ref 1 (play3d.html: her visible pixels stamp it, the ghost draws
//     only where it is unstamped); an NPC that stamped would punch holes in the
//     player's own see-through-occluders twin, and one that read it would ghost
//     itself. Default stencilWrite:false does exactly the right thing — this
//     comment exists so nobody "improves" it later.
//
// THE FIGURE IS THE BATTLE ARENA'S FIGURE. Same technique, deliberately:
// ui_kit's chroma key (magenta-ness -> despill -> largest island -> crop to
// opaque bounds, which is what puts the FEET on the bottom edge) feeding a
// bottom-anchored plane that is YAW-ONLY billboarded — it turns to face the
// camera and stays STANDING, because a full billboard lies down as the camera
// pitches. Blob shadow underneath from the same procedural canvas recipe. The
// one thing added here is `tint`, which is the chapter-2 expansion script's own
// instruction for sprite-first extras ("reuse the poppy sheet, tint #d9b08a"):
// borrowed art, worn as somebody else's coat.
//
// AND SINCE 2026-07-31, WHERE A BODY EXISTS, IT IS A BODY. Four of the town's
// people wear a rigged GLB instead of a plate (body.type 'model'), retargeted by
// tools/vesper_retarget.py onto the same skeleton the player uses, with a mixer
// each playing Idle — and Walking_A for exactly as long as a wander errand is
// moving. The plate path is not deprecated and not going anywhere: it is what
// every villager without a model still wears, and the two live side by side in
// the same Group, the same teardown and the same frame().
//
// WHICH WAY IS A PERSON POINTING — `facing`, THE POST YAW. A record's `facing`
// is DEGREES of yaw about +Y, applied to the figure's root, and it is the same
// convention play3d turns the player with (`ch.rotation.y = atan2(dx, dz)`):
//
//     facing 0    looks down runtime +Z      90 -> +X, 180 -> -Z, 270 -> -X
//
// and runtime +Z is map -Y (a town map authors [x, across-gorge, height]; a
// runtime position is [x, height, -y]), so 0 is "toward the front of the room /
// the near side of the gorge" — the side the fixed cameras and the doors are on.
// A BILLBOARD IGNORES IT: a plate is yaw-billboarded to the camera every frame,
// which cancels root yaw by construction (frame(), below). A MODEL OBEYS IT, and
// obeys it as a POST rather than a one-time pose: `facing` is where the person
// stands when nobody is making them stand anywhere else, so a wander errand turns
// the body with its travel (a body walks the way it is pointed) and the moment the
// errand ends the yaw EASES BACK to the post — slower than the travel turn,
// because settling back to your work is not a pivot.
//
// MEASURED, 2026-07-31, and the reason this comment exists: all three Dellhollow
// shopkeepers were authored `facing: 180`, which under the convention above is
// backs-to-the-counter, greeting the shelves. It cost nothing while they were
// plates (a billboard cancels it) and became visible the day they got bodies. A
// yaw sweep at the item-shop counter (0/90/180/270, screenshots) is what fixed
// the zero direction here rather than in someone's head.
//
// HOW TALL — `body.h`, `height`, and `defaults.adultHeight`. Heights are
// MULTIPLES of the engine's charH (MODEL_H, the [ / ] dial), so re-tuning the
// player re-tunes the town. A model takes body.h if it has one, else the record's
// `height`, else `defaults.adultHeight` — which exists because the stand-in
// multiple of 1.0 made every rigged villager exactly the player's height, and the
// player is a slight nineteen-year-old. The interiors are built around the kit's
// REF_human_1p7, and against a 1.05 m counter (tools/shop_props.py CTR_H) a 1.45
// keeper shows nothing but a head. 1.10 x 1.45 = 1.60 reads as an adult at that
// counter. A CHILD CARRIES HIS OWN NUMBER and is untouched by the default: Nib is
// body.h 0.72 because he is eight.
//
// WHY NOT ui_kit's poseSprite(): that helper resolves a fixed name list
// (pose.png, pose-front.png) from a character id, which is right for a battle
// where the combatant IS the character. Here the BODY is a data field —
// `body.src` — so a villager can wear a borrowed plate, a side-on pose, or
// (tomorrow) a GLB, without ui_kit learning about villagers. The keying itself
// is EBUI.chromaKey, called directly. One implementation, two callers.
//
// A DOOR IS NOW A SCENE SWAP, NOT A PAGE LOAD. play3d's transitionTo() rebuilds
// the world in place and announces it with ONE window CustomEvent, 'eb-scene'
// (contract at sgAnnounce() in play3d.html): fired after the new bundle is
// playable, before the veil drops, never on a fresh page load. A handler means
// "do again what you did at load time, for THIS scene" — and for this module the
// load-time job has a second half nobody else's has: the town's ten figures are
// GPU objects parented to a `scene` that sceneDispose() does NOT empty of them.
//
// WITHOUT THE HANDLER, MEASURED ON THE PRE-FIX FILE: all ten of Dellhollow's
// plates were still in the world inside every one of the six interiors, worth a
// permanent one-time step over every later per-(scene, shot) GPU baseline
// (tools/transition_test.mjs reported 7 FAILs of that one signature). They did not
// project into any interior's frame in the sweep, and they never could become
// floors or walls — rule 1 keeps them out of collide/walkRef — so the leak was
// real and the apparition was luck. The half a player COULD see was the opposite
// one: sceneKey was read once at build and `built` never cleared, so the chandler,
// the weaponsmith and the armorer — villagers whose scene IS a shop interior —
// were never built at all. Three shopkeepers were missing from the game.
//
// So the handler is teardown THEN rebuild, and the teardown is total: every
// geometry, every material, every texture including the chroma-keyed
// CanvasTextures and the shared blob shadow.
//
// window.Npc
//   Npc.tick()              one frame of the prompt state machine (public and
//                           idempotent, exactly like Shop.tick — a test drives
//                           it by hand because rAF is dead in a background tab)
//   Npc.list() / .near()    who is here, who is in reach
//   Npc.talk(id)            open a conversation without walking there
//   Npc.ready()             a promise for "the figures have finished landing" —
//                           the settle signal a leak test needs (see below)
//   Npc.debug()             the whole live state, for a headless assert
(function () {
  'use strict';

  var DATA_URL = 'game/npcs.json';
  var TICK_MS = 250;              // keepalive; rAF is throttled to nothing in a background tab
  var STEP_TOL = 0.5;             // how far a wander step may change height and still be "the walk network"
  var DEF_RADIUS = 1.9;           // talk reach when the data does not say

  // play3d.html is a classic script: its top-level let/const live in the shared
  // global lexical scope and are readable from here — but a missing one is a
  // ReferenceError, so every read is guarded (route_overlay.js precedent). A
  // binding that is gone disables the module; it never throws into the page.
  var TH = function () { try { return THREE; } catch (e) { return window.THREE; } };
  var SCN = function () { try { return scene; } catch (e) { return null; } };
  var CAM = function () { try { return cam; } catch (e) { return null; } };
  var CHARH = function () { try { return MODEL_H; } catch (e) { return 1.45; } };
  var SKEY = function () {
    var s = null; try { s = SCENE; } catch (e) { }
    try { return s || new URLSearchParams(location.search).get('scene') || ''; } catch (e) { return s || ''; }
  };
  var SIM = function () { return window.SIM || null; };
  var U = function () { return window.EBUI || null; };
  var HAS_DOM = typeof document !== 'undefined' && !!document.createElement;
  var RM = HAS_DOM && window.matchMedia && window.matchMedia('(prefers-reduced-motion:reduce)').matches;

  // ---------------------------------------------------------------- data ----
  var DATA = null, LOADING = null, FAILED = false;
  function load() {
    if (DATA) return Promise.resolve(DATA);
    if (FAILED) return Promise.resolve(null);
    if (LOADING) return LOADING;
    if (typeof fetch !== 'function') { FAILED = true; return Promise.resolve(null); }
    LOADING = fetch(DATA_URL).then(function (r) { return r.ok ? r.json() : null; })
      .catch(function () { return null; })
      .then(function (j) {
        LOADING = null;
        if (!j) { FAILED = true; console.log('[Npc] no ' + DATA_URL + ' — town unpopulated'); return null; }
        DATA = j; return j;
      });
    return LOADING;
  }
  function defaults() { return (DATA && DATA.defaults) || {}; }
  // `scene` accepts a key or a list of keys, so one villager can stand in both
  // the real-time explore bundle and the cinematic one (del-cine ships the whole
  // town's collision, so a world coordinate is the same place in both).
  function inScene(rec, key) {
    var s = rec.scene;
    if (s == null) return false;
    if (Array.isArray(s)) return s.indexOf(key) >= 0;
    return String(s) === key;
  }

  // -------------------------------------------------------------- texture ----
  // The blob shadow: one 128px radial-gradient canvas, generated once and shared
  // by every figure. No files, no fetches, no failure mode. (battle_stage3d's
  // recipe, stop-by-stop — a villager's shadow and a combatant's are the same
  // shadow because they are lit by the same sun.)
  var shadowTex = null;
  function blobShadow() {
    if (shadowTex) return shadowTex;
    var c = document.createElement('canvas'); c.width = c.height = 128;
    var g = c.getContext('2d');
    var rg = g.createRadialGradient(64, 64, 0, 64, 64, 64);
    rg.addColorStop(0, 'rgba(0,0,0,0.62)');
    rg.addColorStop(0.45, 'rgba(0,0,0,0.36)');
    rg.addColorStop(0.78, 'rgba(0,0,0,0.10)');
    rg.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = rg; g.fillRect(0, 0, 128, 128);
    shadowTex = new (TH().CanvasTexture)(c);
    return shadowTex;
  }

  // One keyed canvas per source plate, shared by every figure that wears it —
  // the key is idempotent and two villagers in borrowed coats should not pay for
  // it twice. Resolves null if the art is missing, and a figure with no art is
  // simply not built (their prompt and their dialogue still work: a person you
  // can talk to and cannot see is a smaller failure than a crash).
  var plateCache = Object.create(null);
  function plate(src) {
    if (plateCache[src]) return plateCache[src];
    return (plateCache[src] = new Promise(function (res) {
      if (typeof Image !== 'function' || !U() || !U().chromaKey) return res(null);
      var im = new Image();
      im.onload = function () {
        var c = null;
        try { c = U().chromaKey(im); } catch (e) { c = null; }
        if (!c) console.warn('[Npc] chroma key produced nothing for ' + src);
        res(c);
      };
      im.onerror = function () { console.warn('[Npc] missing body plate ' + src); res(null); };
      im.src = src;
    }));
  }

  // ------------------------------------------------------------- geometry ----
  // Where does a person's foot go? The walk network, if there is one — the same
  // surface the player is allowed to stand on under WALKLOCK — choosing the
  // floor NEAREST the authored height so a villager on a quay does not snap to
  // the deck three storeys above them. Falls back to any floor, then to the
  // authored value, so a bundle that has not loaded yet still places them
  // roughly right and the re-snap below fixes it when the GLB lands.
  function groundAt(x, z, wantY) {
    var S = SIM(); if (!S) return wantY;
    var ys = [];
    try { ys = S.walkFloors(x, z) || []; } catch (e) { }
    if (!ys.length) { try { ys = S.floors(x, z) || []; } catch (e) { } }
    if (!ys.length) return null;
    var best = ys[0];
    for (var i = 1; i < ys.length; i++) if (Math.abs(ys[i] - wantY) < Math.abs(best - wantY)) best = ys[i];
    return best;
  }

  // The plate, as a standing figure. Bottom-anchored (geo.translate(0,h/2,0))
  // so the crop's bottom edge — which the key put at the character's feet — sits
  // on y=0 of the root, and the root sits on the floor.
  function billboardFrom(canvas, targetH, tint) {
    var T = TH();
    var w = canvas.width, h = canvas.height;
    var tex = new T.CanvasTexture(canvas);
    tex.colorSpace = T.SRGBColorSpace;
    tex.minFilter = T.LinearFilter; tex.generateMipmaps = false; tex.needsUpdate = true;
    var pw = targetH * (w / h);
    var geo = new T.PlaneGeometry(pw, targetH);
    geo.translate(0, targetH / 2, 0);
    var mat = new T.MeshBasicMaterial({
      map: tex, transparent: true, alphaTest: 0.28, side: T.DoubleSide,
      // `tint` multiplies the plate — the expansion script's own device for
      // dressing a reused villager sheet as somebody else. White = untouched.
      color: tint ? new T.Color(tint) : 0xffffff,
    });
    var m = new T.Mesh(geo, mat);
    m.userData.npcPlate = true;
    return { mesh: m, w: pw, h: targetH };
  }

  // ----------------------------------------------------------------- state ----
  var GROUP = null;               // the one group; never in collide/walkRef/allMeshes
  var PEOPLE = [];                // built figures for THIS scene
  var built = false, building = false, driving = false;
  var armed = null, nearId = null;   // prompt state machine (Shop.tick's shape)
  var sceneKey = null, missing = [];

  // EPOCH — play3d's own device, for the same reason play3d needs it. A figure is
  // built across two async hops (fetch the data, load-and-key the plate) and a
  // door can land in the middle of both. Every continuation therefore carries the
  // epoch it started in and does nothing if the world has moved on: the plate that
  // resolves for a town we already left must not build a mesh, because that mesh
  // would be parented to a disposed Group where nothing can ever find it again —
  // invisible to the eye and visible only to renderer.info, which is the exact
  // shape of the leak this file is here to stop making.
  var EPOCH = 0;

  // HIDDEN — "this posted villager is somewhere else right now", as PAGE state.
  // Its one caller today is followers.js: once Mochi is at the player's heel, the
  // posted cats ('mochi' at the Dellhollow eel stall, 'mochi-emb' at the Emberbrook
  // waystone) are the SAME ANIMAL, and a cat following you while a second one sits
  // at the stall reads as a bug. It is page state and not scene state deliberately:
  // spawn() honours it, so the intent survives a doorway without either module
  // having to win a race with the other's 'eb-scene' handler. A hidden figure is
  // also out of nearest(), so their prompt and their hail node are unreachable
  // rather than invisible-but-talkable.
  var HIDDEN = Object.create(null);

  // THE SETTLE SIGNAL. "the 'eb-scene' handler returned" is NOT "the villagers are
  // standing there": the art arrives over an <img> load and a chroma key, several
  // hops later. Anything MEASURING this page needs that difference — a per-(scene,
  // shot) renderer.info baseline captured between the two is a baseline with ten
  // people missing from it, and every later visit then reads as a leak. So the
  // module publishes the state instead of leaving callers to guess with a sleep:
  // Npc.ready() is a promise that resolves when nothing is in flight, and
  // Npc.debug().building is the same fact for a synchronous assert.
  var inflight = 0, settleP = null, settleGo = null;
  function buildStart() {
    inflight++;
    if (!settleP) settleP = new Promise(function (r) { settleGo = r; });
  }
  function buildEnd() {
    if (inflight > 0) inflight--;
    if (!inflight && settleGo) { var go = settleGo; settleGo = null; settleP = null; go(true); }
  }
  function ready() { return settleP || Promise.resolve(true); }

  function build() {
    if (built || building) return Promise.resolve(PEOPLE);
    var T = TH(), sc = SCN();
    if (!T || !sc || !HAS_DOM) return Promise.resolve([]);
    building = true;
    sceneKey = SKEY();
    var ep = EPOCH;
    return load().then(function (d) {
      if (ep !== EPOCH) return [];              // another door landed while we fetched
      if (!d) { building = false; return []; }
      var recs = (d.npcs || []).filter(function (r) { return inScene(r, sceneKey); });
      if (!recs.length) { built = true; building = false; return []; }
      GROUP = new T.Group(); GROUP.name = 'npcs'; GROUP.frustumCulled = false;
      sc.add(GROUP);
      var jobs = recs.map(function (r) { return spawn(r, ep); });
      return Promise.all(jobs).then(function () {
        if (ep !== EPOCH) return [];
        built = true; building = false;
        console.log('[Npc] ' + PEOPLE.length + ' in ' + sceneKey +
          (missing.length ? ' (' + missing.length + ' without art: ' + missing.join(', ') + ')' : ''));
        return PEOPLE;
      });
    });
  }

  function spawn(rec, ep) {
    var T = TH();
    var D = defaults();
    var pos = rec.position || [0, 0, 0];
    var y = groundAt(pos[0], pos[2], pos[1]);
    var root = new T.Group();
    root.position.set(pos[0], y === null ? pos[1] : y, pos[2]);
    // THE POST YAW (see the header): degrees about +Y, 0 down runtime +Z, the
    // same convention as the player's own turn. A billboard cancels it every
    // frame; a model wears it, walks away from it on an errand, and eases back.
    var post = (rec.facing || 0) * Math.PI / 180;
    root.rotation.y = post;
    var bob = new T.Group(); root.add(bob);
    GROUP.add(root);

    var P = {
      id: rec.id, name: rec.name || rec.id, rec: rec,
      root: root, bob: bob, mesh: null, shadow: null,
      home: root.position.clone(), y: root.position.y, post: post,
      h: 0, w: 0.6,
      idle: rec.idleBehavior || 'stand',
      radius: rec.radius || D.radius || DEF_RADIUS,
      dialogue: rec.dialogue || null,
      bobPhase: Math.random() * 6.283,
      // wander
      wr: (rec.wander && rec.wander.radius) || D.wanderRadius || 1.6,
      wspd: (rec.wander && rec.wander.speed) || D.wanderSpeed || 0.55,
      wait: 1 + Math.random() * 3, tgt: null,
      art: false,
    };
    PEOPLE.push(P);
    if (HIDDEN[P.id]) { root.visible = false; P.hidden = true; }   // see Npc.hide

    // the shadow exists whether or not the art does — it is the figure's
    // contact with the ground, and it is also how a missing plate is visible in
    // a screenshot instead of silently absent.
    var sh = new T.Mesh(new T.PlaneGeometry(1, 1), new T.MeshBasicMaterial({
      map: blobShadow(), transparent: true, depthWrite: false, opacity: 0.8,
      color: 0x000000, fog: false,
    }));
    sh.rotation.x = -Math.PI / 2; sh.position.y = 0.04; sh.renderOrder = 2;
    root.add(sh); P.shadow = sh;
    sh.scale.set(0.7, 0.7 * 0.62, 1);

    var body = rec.body || {};
    if (body.type === 'model' && body.src) return loadModel(P, body, ep);
    if (!body.src) { missing.push(P.id); return Promise.resolve(P); }

    var targetH = CHARH() * (rec.height || 1);
    return plate(body.src).then(function (canvas) {
      if (ep !== EPOCH) return P;                // we are not in that scene any more
      if (!canvas) { missing.push(P.id); return P; }
      var b = billboardFrom(canvas, targetH, body.tint);
      P.mesh = b.mesh; P.h = b.h; P.w = b.w; P.art = true;
      bob.add(b.mesh);
      var sw = Math.max(0.5, Math.min(2.2, b.w * (body.shadow || D.shadow || 1.15)));
      sh.scale.set(sw, sw * 0.62, 1);
      // 'lean' is a pose, not an animation: a few degrees of roll into whatever
      // the villager is leaning on, and a slower breath. Cheap, and it stops a
      // street of standing figures reading as a shop-window display.
      if (P.idle === 'lean') { b.mesh.rotation.z = (body.leanDeg === undefined ? 5 : body.leanDeg) * Math.PI / 180; }
      return P;
    });
  }

  // Swap-ready by design: the schema says body:{type:'model',src:'…glb'} and this
  // is what honours it, so a villager becomes a rigged body the day one exists
  // without any other line of this file changing. That day is 2026-07-31: the four
  // Tripo deliveries (finn/mara/maren/pip) went through tools/vesper_retarget.py's
  // NPC recipe — same rig as the player, clips Idle / Walking_A / Jump_Full_Short,
  // Walking_A from the UAL Walk_Loop because villagers wander instead of running.
  //
  // THE FOUR RULES STILL HOLD, and a GLB is where they are easiest to break:
  //  1. it goes into P.bob and nowhere else — never collide / walkRef / allMeshes.
  //     A villager you can walk through, again, on purpose.
  //  4. nothing here sets stencilWrite. GLTF materials default to false, which is
  //     already right (see the header); the player's ghost pass owns ref 1 alone.
  // frustumCulled is turned OFF on the skinned meshes: a skinned bounding box is
  // the BIND pose's box, and an animated arm that leaves it makes three.js cull a
  // villager who is standing right in front of you.
  //
  // TINT, for a borrowed body: the plate path multiplies its texture by body.tint,
  // and this does exactly the same thing to the model's base colour, for the same
  // reason (the expansion script's "reuse the sheet, tint it" device). A tinted
  // figure gets CLONED materials (see cloneBody) so this never reaches through to
  // another villager wearing the same file.
  //
  // ============================================================================
  // ONE GLB PER FILE, NOT ONE PER PERSON.  (2026-08-03 — the renderer-collapse fix)
  //
  // This function used to mint `new T.GLTFLoader()` and call `.load(body.src)` for
  // EVERY figure. npcs.json posts 29 villagers across FOUR distinct bodies, and
  // each of those bodies is a 12 MB GLB carrying THREE 4096x4096 maps — 257 MB of
  // decoded texture per instance. GLTFLoader shares nothing across calls, so a
  // town paid that 257 MB once per PERSON.
  //
  // MEASURED, not reasoned (tools/npc_mem_gate.mjs, real GPU, macOS physical
  // footprint via vmmap — `ps rss` overcounts shared IOSurface pages and is not
  // the instrument): emb-cine booted at renderer 2867 MB + gpu-process 3379 MB =
  // 6.2 GB, and blocking js/npc.js over CDP dropped the renderer to 302 MB. Eight
  // figures x 257 MB is the 2 GB. On the author's M1 Max that is 6 GB of unified
  // memory and the machine merely swaps; on a weaker machine it is the hang the
  // playtest harness photographed as a 103-second scene transition.
  //
  // THE CACHE IS SCENE-SCOPED ON PURPOSE. Page-scoped would be a bigger win and
  // would break the disposal contract this module is built on: transition_test
  // requires renderer.info to return to baseline across every door, and a master
  // held past dropScene() is exactly the leak that gate exists to catch.
  var modelCache = Object.create(null);       // src -> Promise<gltf>, THIS scene's
  function modelMaster(src) {
    if (modelCache[src]) return modelCache[src];
    return (modelCache[src] = new Promise(function (res) {
      var T = TH(), L = null;
      try { L = new T.GLTFLoader(); } catch (e) { }
      if (!L) return res(null);
      L.load(src, function (g) { res(g); }, null, function () { res(null); });
    }));
  }
  // Object3D.clone() shares geometry and material by reference — which is the whole
  // point — but it leaves every SkinnedMesh bound to the SOURCE's bones, so N clones
  // animate as one. This is three.js's own SkeletonUtils.clone recipe, inlined
  // because this repo ships three.min.js + GLTFLoader and nothing else.
  function parallelTraverse(a, b, cb) {
    cb(a, b);
    for (var i = 0; i < a.children.length && i < b.children.length; i++)
      parallelTraverse(a.children[i], b.children[i], cb);
  }
  function cloneBody(source) {
    var srcOf = new Map(), cloneOf = new Map();
    var out = source.clone(true);
    parallelTraverse(source, out, function (s, c) { srcOf.set(c, s); cloneOf.set(s, c); });
    out.traverse(function (node) {
      if (!node.isSkinnedMesh) return;
      var sm = srcOf.get(node); if (!sm || !sm.skeleton) return;
      var bones = sm.skeleton.bones;
      node.skeleton = sm.skeleton.clone();
      node.bindMatrix.copy(sm.bindMatrix);
      node.skeleton.bones = bones.map(function (b) { return cloneOf.get(b) || b; });
      node.bind(node.skeleton, node.bindMatrix);
    });
    return out;
  }
  function loadModel(P, body, ep) {
    var T = TH();
    return modelMaster(body.src).then(function (master) {
      if (!master || !master.scene) { missing.push(P.id); return P; }
      if (ep !== EPOCH) return P;                 // arrived for a scene we left; the
                                                 // CACHE owns the master, not us
      return new Promise(function (res) {
        var g = { scene: cloneBody(master.scene), animations: master.animations };
        var o = g.scene;
        var box = new T.Box3().setFromObject(o), sz = new T.Vector3(); box.getSize(sz);
        // body.h wins over the record's height so a shared record can carry a
        // billboard height and a model height that are not the same number, and
        // BOTH win over defaults.adultHeight — which is the town's grown-ups, not
        // a floor under everybody: a record that states a height states it because
        // that person is not a standard adult (see the header; Nib is eight).
        var hMul = (body.h != null ? body.h
                    : (P.rec.height != null ? P.rec.height
                       : (defaults().adultHeight || 1)));
        var targetH = CHARH() * hMul;
        if (sz.y > 0.001) { var k = targetH / sz.y; o.scale.multiplyScalar(k); o.position.y -= box.min.y * k; sz.multiplyScalar(k); }
        var tint = body.tint ? new T.Color(body.tint) : null;
        o.traverse(function (c) {
          if (!c.isMesh) return;
          c.frustumCulled = false;
          c.castShadow = false; c.receiveShadow = false;
          if (!tint) return;
          // THE ONE THING THE CLONE MAY NOT SHARE. Materials come across by
          // reference, so multiplying in place would tint every OTHER villager
          // wearing this file — and compound once per wearer. Material.clone()
          // copies the map references, so the tinted figure still costs no
          // second texture upload; the clone is inside GROUP and dies with it.
          var ms = Array.isArray(c.material) ? c.material : [c.material];
          var out = [];
          for (var i = 0; i < ms.length; i++) {
            var m = ms[i] ? ms[i].clone() : ms[i];
            if (m && m.color) m.color.multiply(tint);
            out.push(m);
          }
          c.material = Array.isArray(c.material) ? out : out[0];
        });
        P.bob.add(o); P.mesh = o; P.model = true; P.h = targetH; P.w = Math.max(sz.x, sz.z) || targetH * 0.5;
        P.art = true;
        var sw = Math.max(0.5, Math.min(2.2, P.w * 1.4));
        P.shadow.scale.set(sw, sw * 0.62, 1);
        buildMixer(P, g.animations || []);
        res(P);
      });
    });
  }

  // ONE MIXER PER VILLAGER, driven from the same frame() the billboards ride, so a
  // background tab (where rAF is dead and TICK_MS is the only heartbeat) still
  // advances them — the same reason the yaw billboard is driven there.
  //
  // Two clips, because that is what a villager needs: Idle, and Walking_A while a
  // wander errand is actually moving. Clip names are matched loosely, exactly the
  // way play3d picks the player's, so a future body with different spelling still
  // finds them; a file with only one clip simply never walks.
  //
  // WALK CADENCE. The NPC recipe's Walk_Loop covers a measured 0.46 u/s on a
  // 1.45-unit body (tools/vesper_retarget.py's note, stride.py); a villager's
  // wander speed is data (0.55 default). Scaling the clip by the ratio is what
  // stops the small skate that a fixed 1x leaves, and it is per-person because the
  // speed is per-person. Clamped, so a silly datum cannot make a blur.
  var NPC_WALK_UPS = 0.46;
  function buildMixer(P, clips) {
    var T = TH();
    if (!clips.length || !T.AnimationMixer) return;
    var pick = function (re) {
      for (var i = 0; i < clips.length; i++) if (re.test(clips[i].name)) return clips[i];
      return null;
    };
    var ci = pick(/^Idle$/i) || pick(/idle/i) || clips[0];
    var cw = pick(/^Walking_A$/i) || pick(/walk/i) || pick(/run/i);
    P.mixer = new T.AnimationMixer(P.mesh);
    P.aIdle = ci ? P.mixer.clipAction(ci) : null;
    P.aWalk = cw ? P.mixer.clipAction(cw) : null;
    if (P.aWalk) {
      var h = P.h || CHARH();
      P.aWalk.timeScale = Math.max(0.5, Math.min(2.5, P.wspd / (NPC_WALK_UPS * (h / 1.45))));
    }
    if (P.aIdle) { P.aIdle.play(); P.clip = 'idle'; }
    // A street of figures all breathing on frame 0 together is a chorus line; the
    // same phase that offsets the billboards' bob offsets the cycle here.
    if (P.aIdle) P.aIdle.time = (P.bobPhase / 6.283) * (P.aIdle.getClip().duration || 0);
  }

  function setClip(P, want) {
    if (!P.mixer || P.clip === want) return;
    var next = want === 'walk' ? P.aWalk : P.aIdle;
    var prev = want === 'walk' ? P.aIdle : P.aWalk;
    if (!next) return;                       // nothing to switch to: stay as we are
    if (prev) prev.fadeOut(0.25);
    next.reset().fadeIn(0.25).play();
    P.clip = want;
  }

  // ------------------------------------------------------------ animation ----
  var lastT = 0;
  function frame() {
    var now = Date.now() / 1000;
    var dt = lastT ? Math.min(0.1, now - lastT) : 0.016;
    lastT = now;
    var c = CAM();
    for (var i = 0; i < PEOPLE.length; i++) {
      var P = PEOPLE[i];
      if (!P.mesh) continue;
      // yaw-only billboard: the plate turns to face the camera and STAYS
      // STANDING. A full lookAt lies the figure down as the camera pitches.
      if (!P.model && c) {
        var dx = c.position.x - P.root.position.x, dz = c.position.z - P.root.position.z;
        P.mesh.rotation.y = Math.atan2(dx, dz) - P.root.rotation.y;
      }
      // A PLATE BOBS, A BODY BREATHES. The sine on `bob` is the billboard's whole
      // sign of life; on a model the Idle clip already breathes, and adding the
      // sine on top gives a villager two heartbeats at different rates.
      if (!RM && !P.model) {
        var amp = P.idle === 'lean' ? 0.018 : 0.028;
        P.bob.position.y = Math.sin(now * 1.55 + P.bobPhase) * amp;
      }
      if (P.idle === 'wander') wander(P, dt); else P.moving = false;
      // BACK TO THE POST. wander() turns a body with its travel; when the errand
      // ends, the authored facing is where the person belongs again — so the yaw
      // eases home at half the travel turn's rate, which reads as settling rather
      // than as a turret snapping back. Model-only (a plate's root yaw is
      // cancelled by the billboard above) and free for a figure that never left
      // its post: standing villagers are already AT `post`, so the delta is zero
      // and this costs one subtraction a frame.
      if (P.model && !P.moving) {
        var dp = P.post - P.root.rotation.y;
        dp = Math.atan2(Math.sin(dp), Math.cos(dp));
        if (Math.abs(dp) > 1e-3) P.root.rotation.y += dp * Math.min(1, dt * 3);
      }
      if (P.mixer) { setClip(P, P.moving ? 'walk' : 'idle'); P.mixer.update(dt); }
    }
  }

  // A SMALL WALK ON THE WALK NETWORK. The candidate step must land on a walk
  // floor within STEP_TOL of the current height and must not be blocked — the
  // same two questions play3d's phys() asks under WALKLOCK, asked through SIM so
  // this file owns no collision logic. A rejected step ends the errand rather
  // than sliding along a wall: villagers pace, they do not pathfind.
  // P.moving is the errand's own state, published for the animation: a plate does
  // not care, a model plays Walking_A exactly while this is true.
  function wander(P, dt) {
    var S = SIM(); if (!S) { P.moving = false; return; }
    if (P.wait > 0) { P.wait -= dt; P.moving = false; return; }
    if (!P.tgt) {
      var a = Math.random() * Math.PI * 2, r = P.wr * (0.35 + Math.random() * 0.65);
      P.tgt = { x: P.home.x + Math.cos(a) * r, z: P.home.z + Math.sin(a) * r };
      P.moving = false;
      return;
    }
    var vx = P.tgt.x - P.root.position.x, vz = P.tgt.z - P.root.position.z;
    var d = Math.hypot(vx, vz);
    if (d < 0.12) { P.tgt = null; P.wait = 1.5 + Math.random() * 4; P.moving = false; return; }
    var step = Math.min(d, P.wspd * dt);
    var nx = P.root.position.x + vx / d * step, nz = P.root.position.z + vz / d * step;
    var ny = groundAt(nx, nz, P.root.position.y);
    var offNet = ny === null || Math.abs(ny - P.root.position.y) > STEP_TOL;
    var wall = false;
    try { wall = !!S.blocked(nx, nz, P.root.position.y); } catch (e) { }
    if (offNet || wall) { P.tgt = null; P.wait = 2 + Math.random() * 3; P.moving = false; return; }
    P.root.position.set(nx, ny, nz);
    P.moving = true;
    // A BODY WALKS THE WAY IT IS POINTED. play3d turns the player with
    // atan2(dx,dz) and this is the same convention on the same rig; eased rather
    // than snapped, because a villager who pivots in one frame reads as a turret.
    // (A billboard cancels root yaw every frame, so this is model-only by nature.)
    if (P.model) {
      var want = Math.atan2(vx, vz), cur = P.root.rotation.y;
      var dy = Math.atan2(Math.sin(want - cur), Math.cos(want - cur));
      P.root.rotation.y = cur + dy * Math.min(1, dt * 6);
    }
  }

  // ---------------------------------------------------------- the prompt ----
  // Arming mirrors play3d's sgTick and shop.js exactly: a region that already
  // contains you when you arrive starts DISARMED and arms when you step out, so
  // spawning on top of a villager does not flash a prompt you did not walk to.
  function reach(P, pos) {
    var vt = U() ? U().sgDef('vTol') : 2;
    var d = Math.hypot(pos.x - P.root.position.x, pos.z - P.root.position.z);
    var dy = Math.abs(pos.y - P.root.position.y);
    return { d: d, dy: dy, 'in': d <= P.radius && dy <= vt };
  }

  function nearest() {
    var S = SIM(); if (!S || !PEOPLE.length) return null;
    var pos = null;
    try { pos = S.pos && S.pos(); } catch (e) { }
    if (!pos) return null;
    var best = null;
    for (var i = 0; i < PEOPLE.length; i++) {
      if (PEOPLE[i].hidden) continue;                 // Npc.hide: not here right now
      var h = reach(PEOPLE[i], pos);
      if (!h['in']) continue;
      if (!best || h.d < best.d) best = { p: PEOPLE[i], d: h.d };
    }
    return best;
  }

  function label(P) {
    var fmt = P.rec.promptLabel || (defaults().promptLabel || 'Talk to {name}');
    return fmt.replace('{name}', P.name);
  }

  function tick() {
    if (!built || !PEOPLE.length) return null;
    var E = U(); if (!E) return null;
    var n = nearest();
    // ARRIVAL SUPPRESSION (sgTick's rule)
    if (armed === null) { armed = !n; nearId = null; E.prompt('npc', null); return n; }
    if (!n) { armed = true; if (nearId) { nearId = null; E.prompt('npc', null); } return null; }
    if (!armed || E.locked) { if (nearId) { nearId = null; E.prompt('npc', null); } return n; }
    if (nearId !== n.p.id) {
      nearId = n.p.id;
      E.prompt('npc', label(n.p), E.sgDef('key'));
    }
    // A SHOPKEEPER OWNS HIS OWN COUNTER. shop.js arms an identical banner off the
    // same pad; this hook runs AFTER Shop.tick in the physics tick (that is the
    // whole reason the coordinator's hook line sits below Shop's), so standing
    // the shop banner down here is the last word in the frame. One prompt, one
    // person — and the keeper says hello before the counter opens, because the
    // greeting node's effect is what opens the shop.
    if (n.p.rec.shop) { try { E.prompt('shop', null); } catch (e) { } }
    return n;
  }

  function talk(id) {
    var P = null;
    for (var i = 0; i < PEOPLE.length; i++) if (PEOPLE[i].id === id) P = PEOPLE[i];
    if (!P || !P.dialogue) return false;
    if (!window.Dialogue || !window.Dialogue.play) return false;
    if (window.Dialogue.isOpen) return false;
    var was = nearId;
    nearId = null; if (U()) U().prompt('npc', null);   // the banner steps aside
    window.Dialogue.play(P.dialogue).then(function (r) {
      if (!r) { nearId = was; }                        // nothing opened: let the prompt come back
    });
    return true;
  }

  // ---------------------------------------------------------------- keys ----
  // ONE HANDLER PER KEY is EBUI's contract (globals[key] = fn), so the last
  // module to register a key REPLACES the one before it — shop.js and this file
  // both want E. Rather than depend on script order, the registry is wrapped
  // ONCE into a chain: handlers are offered the key in turn and a `false` return
  // (EBUI's own "not mine" convention) falls through to the next. Ours is asked
  // first, because a person at arm's reach is more specific than a counter you
  // are also standing at. Idempotent, and invisible to every other module.
  function chainKeys() {
    var E = U(); if (!E || E.__npcChain) return;
    var orig = E.onGlobalKey.bind(E);
    var chain = Object.create(null);
    E.__npcChain = chain;
    E.onGlobalKey = function (key, fn, first) {
      var k = String(key).toLowerCase();
      var list = chain[k] = chain[k] || [];
      // RE-REGISTERING REPLACES YOURSELF. EBUI's contract was one handler per key —
      // globals[k] = fn — so a module calling onGlobalKey twice cost nothing. The
      // chain broke that for free, and a door now makes EVERY module re-arm: shop.js
      // re-registers its counter key on every 'eb-scene' and so do we, so an
      // append-only list grows one entry per doorway for the life of the page.
      // Identity is the handler's own source text, which is stable per registration
      // SITE and different between modules; every one of these closures reads
      // module-level state, so the newest copy and the one it replaces behave
      // identically and swapping in place keeps the priority order intact.
      var src = String(fn);
      for (var i = 0; i < list.length; i++) if (String(list[i]) === src) { list[i] = fn; return; }
      if (first) list.unshift(fn); else list.push(fn);
      orig(k, function (ev) {
        var l = chain[k];
        for (var i = 0; i < l.length; i++) { if (l[i](ev) !== false) return true; }
        return false;                       // nobody took it: play3d gets the keystroke
      });
    };
  }

  function registerPrompts() {
    var E = U(); if (!E || !E.HAS_DOM) return false;
    chainKeys();
    return build().then(function (list) {
      if (!list.length) return false;
      armed = null; nearId = null;
      E.onGlobalKey(E.sgDef('key'), function () {
        if (!nearId || !armed) return false;           // not ours: fall through the chain
        var n = nearest();
        if (!n || !n.p.dialogue) return false;
        // THE DOOR THE BARGEMAN ATE (PT-20260805-064, measured in del-inn-int).
        // EBUI dispatches global keys in the CAPTURE phase and a consumed key is
        // stopImmediatePropagation'd, so while ANY villager is in talk reach this
        // handler starves play3d's bubble-phase door keydown — the whole door pad
        // of the Boatmen's Rest sits inside the bargeman's 1.9 m, and "E exits"
        // was unreachable no matter where the body stood. "A person at arm's
        // reach is more specific than a counter" (the chain's founding comment)
        // stays true — but only while the person is the NEARER claim. When a live,
        // in-range scene edge (a door, never an auto cut) is closer than the
        // villager, yield the key: returning false leaves the event unconsumed
        // and play3d's own handler takes the door — or speaks its denial, which
        // is also that handler's job, so a denied-but-nearer door yields too.
        try {
          var S = SIM();
          if (S && S.edges) {
            var es = S.edges(), d = null;
            for (var i = 0; i < es.length; i++) {
              var e = es[i];
              if (e.auto || !e.inRange) continue;
              if (!e.live && !e.denied) continue;
              if (d === null || e.dist < d) d = e.dist;
            }
            if (d !== null && d < n.d) return false;   // the door is the nearer claim
          }
        } catch (err) { }
        return talk(n.p.id);
      }, true);
      drive();
      return true;
    });
  }

  function drive() {
    if (driving || !HAS_DOM) return;
    driving = true;
    var raf = function () { frame(); requestAnimationFrame(raf); };
    requestAnimationFrame(raf);
    // keepalive: rAF stops in a background tab, which is where headless
    // verification lives — and a billboard that stops turning between SIM.tick()
    // renders would photograph edge-on.
    setInterval(function () { frame(); tick(); }, TICK_MS);
  }

  // Re-seat everyone on the floor once the bundle's geometry is actually in.
  // The first placement can run before the GLB lands (walkFloors returns
  // nothing), and a villager 30 cm into the deck reads as a bug in the art.
  function resettle() {
    var moved = 0;
    for (var i = 0; i < PEOPLE.length; i++) {
      var P = PEOPLE[i];
      var y = groundAt(P.root.position.x, P.root.position.z, P.rec.position[1]);
      if (y === null) continue;
      if (Math.abs(y - P.root.position.y) > 0.02) { P.root.position.y = y; P.home.y = y; moved++; }
    }
    return moved;
  }

  // ------------------------------------------------------------- teardown ----
  // THE DISPOSAL CONTRACT, in the words play3d's own sceneDispose() uses: three.js
  // only decrements its counters when it is TOLD, so anything dropped without
  // dispose() stays uploaded and is invisible to everything except renderer.info.
  // Removing the Group from the scene is the half you can see; this is the half
  // you can only measure.
  //
  // A material's textures are not reachable from material.dispose(), so they are
  // walked by hand — and they are SHARED (every figure's shadow is the one blob
  // canvas, two villagers in the same borrowed coat wear the same plate), so a
  // Set makes each one exactly one dispose call instead of one per wearer.
  // A RIGGED BODY HIDES ONE MORE TEXTURE THAN A PLATE DOES, and it is reachable
  // from neither the geometry nor the material: three.js gives every Skeleton a
  // boneTexture (the bone matrices, uploaded as a DataTexture) the first time it
  // is DRAWN, and hangs it off SkinnedMesh.skeleton. MEASURED, not guessed — the
  // town with four bodies in it reports skinned 4 / boneTexture 4 / material
  // textures 19, and before this line tools/transition_test.mjs failed 16 GPU
  // assertions whose whole delta was {tex:+4} per town visit and {tex:+1} per
  // interior: exactly one per rigged villager, every time, for the life of the
  // page. skeleton.dispose() is what three.js documents; the boneTexture fallback
  // covers a build old enough not to have it.
  function disposeTree(root) {
    if (!root || !root.traverse) return;
    var tex = new Set();
    root.traverse(function (o) {
      if (o.isSkinnedMesh && o.skeleton) {
        if (o.skeleton.dispose) { try { o.skeleton.dispose(); } catch (e) { } }
        else if (o.skeleton.boneTexture) tex.add(o.skeleton.boneTexture);
      }
      if (o.geometry && o.geometry.dispose) o.geometry.dispose();
      if (!o.material) return;
      var ms = Array.isArray(o.material) ? o.material : [o.material];
      for (var i = 0; i < ms.length; i++) {
        var m = ms[i]; if (!m) continue;
        for (var k in m) { var v = m[k]; if (v && v.isTexture && v.dispose) tex.add(v); }
        if (m.dispose) m.dispose();
      }
    });
    tex.forEach(function (t) { try { t.dispose(); } catch (e) { } });
  }

  // Everything this module put in the world, gone — and every piece of per-scene
  // bookkeeping back to its page-load value, so the rebuild that follows takes
  // exactly the path a fresh page takes. Idempotent (a second call finds nothing)
  // and it never throws: play3d's contract is that a handler must not.
  //
  // WHAT SURVIVES, deliberately: `plateCache`, the keyed canvases. Those are CPU
  // pixels, not GPU objects — they cost renderer.info nothing, the key is
  // expensive and deterministic, and re-running it on every doorway would put a
  // fetch-and-key back into the swap the swap exists to make instant. Same
  // reasoning that keeps music.js's AudioContext alive across a door: page state
  // stays, scene state goes. `shadowTex` is NOT page state by that test — it IS a
  // GPU object — so it goes, and blobShadow() mints it again for the next town.
  // A MIXER IS NOT A GPU OBJECT, AND IS EXACTLY WHY IT GETS FORGOTTEN. It holds
  // the AnimationActions, the interpolant caches and a reference to the root it
  // drives, so a mixer left behind keeps a torn-down villager's whole skeleton
  // alive on the JS heap where renderer.info cannot see it — the same class of
  // leak as an undisposed texture, one layer up. stopAllAction() then
  // uncacheRoot() is the pair three.js documents; both are wrapped, because the
  // eb-scene contract is that a handler never throws.
  function stopMixers() {
    for (var i = 0; i < PEOPLE.length; i++) {
      var P = PEOPLE[i];
      if (!P.mixer) continue;
      try { P.mixer.stopAllAction(); } catch (e) { }
      try { if (P.mesh) P.mixer.uncacheRoot(P.mesh); } catch (e) { }
      P.mixer = null; P.aIdle = null; P.aWalk = null; P.clip = null;
    }
  }

  function dropScene() {
    EPOCH++;                                   // strand every continuation in flight
    stopMixers();                              // before the tree goes: it needs P.mesh
    if (GROUP) {
      var sc = SCN(); if (sc) { try { sc.remove(GROUP); } catch (e) { } }
      disposeTree(GROUP);
      GROUP = null;
    }
    if (shadowTex) { try { shadowTex.dispose(); } catch (e) { } shadowTex = null; }
    // THE MASTER BODIES. Each is a GLB the figures above were CLONED from, and it
    // is not in GROUP, so nothing above has disposed it — a cache that outlives
    // the scene is the leak transition_test counts, and it would be a 257 MB one.
    // A master still in flight is disposed WHEN IT LANDS: the figure continuation
    // sees ep !== EPOCH and returns without touching it, precisely so the cache
    // stays the only owner.
    var stale = modelCache; modelCache = Object.create(null);
    for (var k in stale) {
      try {
        Promise.resolve(stale[k]).then(function (g) {
          if (g && g.scene) { try { disposeTree(g.scene); } catch (e) { } }
        }, function () { });
      } catch (e) { }
    }
    PEOPLE = [];
    built = false; building = false;
    // the banner is per-scene too: walking out of the town with "Talk to Odessa"
    // still lit is the leaked state the full page load made impossible (shop.js
    // resets its own for the same reason, and says so).
    armed = null; nearId = null; missing = [];
    try { if (U()) U().prompt('npc', null); } catch (e) { }
    sceneKey = null;
  }

  // play3d's ONE transition event. Teardown, then the SAME arming path a fresh
  // page takes — build() re-reads SKEY(), which play3d has already made truthful
  // with history.replaceState before dispatching. drive() self-guards, so the
  // rAF/interval pair is started once for the page and never stacked; the key
  // registration de-duplicates itself in the chain (see chainKeys), so twenty
  // doors leave twenty times nothing behind.
  function rescene() {
    buildStart();                              // synchronous: an observer that reads
                                               // Npc.ready() any time after the event
                                               // gets a promise for the NEW figures
    try { dropScene(); } catch (e) { console.error('[Npc] eb-scene teardown', e); }
    var done = function () { buildEnd(); };
    var p = null;
    try { p = registerPrompts(); } catch (e) { console.error('[Npc] eb-scene', e); }
    Promise.resolve(p).then(done, function (e) { console.error('[Npc] eb-scene', e); done(); });
  }
  // `window.addEventListener` and not just `window`: the headless suites boot these
  // modules under vm.runInThisContext with globalThis AS window, and that window has
  // an addEventListener only when the fake DOM is switched on. A module that assumes
  // otherwise takes the whole suite down at import time — which is a live bug in this
  // tree today (tools/economy_test.mjs, js/shop.js:470) and not one to reproduce.
  if (typeof window !== 'undefined' && window.addEventListener) {
    window.addEventListener('eb-scene', function () {
      try { rescene(); } catch (e) { console.error('[Npc] eb-scene', e); }
    });
  }

  window.Npc = {
    // integration surface
    registerPrompts: registerPrompts, tick: tick, talk: talk, load: load,
    resettle: resettle, ready: ready,
    list: function () {
      return PEOPLE.map(function (P) {
        return { id: P.id, name: P.name, at: P.root.position.toArray().map(function (v) { return +v.toFixed(2); }),
                 h: +P.h.toFixed(2), art: P.art, idle: P.idle, dialogue: P.dialogue, shop: P.rec.shop || null,
                 // the post yaw as authored and the yaw the body is actually
                 // wearing (degrees) — a facing claim is checkable without a
                 // screenshot, and after an errand the two converge
                 face: Math.round(P.post * 180 / Math.PI),
                 yaw: Math.round(((P.root.rotation.y * 180 / Math.PI) % 360 + 360) % 360),
                 // a body, and which clip it is playing — the same fact CHAR3D
                 // publishes for the player, so a headless assert can read it
                 body: P.model ? 'model' : (P.art ? 'billboard' : 'none'), clip: P.clip || null };
      });
    },
    near: function () { var n = nearest(); return n ? { id: n.p.id, name: n.p.name, d: +n.d.toFixed(2) } : null; },
    // Npc.hide(id, on) — take a posted villager out of the world without editing
    // npcs.json (see HIDDEN above). Returns true if the id is one this town knows
    // about right now; the intent is recorded either way, for the next spawn.
    hide: function (id, on) {
      if (on === undefined) on = true;
      if (on) HIDDEN[id] = true; else delete HIDDEN[id];
      var found = false;
      for (var i = 0; i < PEOPLE.length; i++) {
        if (PEOPLE[i].id !== id) continue;
        found = true;
        PEOPLE[i].hidden = !!on;
        PEOPLE[i].root.visible = !on;
        if (on && nearId === id) { nearId = null; try { if (U()) U().prompt('npc', null); } catch (e) { } }
      }
      return found;
    },
    hidden: function () { return Object.keys(HIDDEN); },
    get group() { return GROUP; },
    debug: function () {
      return { scene: sceneKey, built: built, count: PEOPLE.length, missingArt: missing.slice(),
               // `built` says a build FINISHED; `building` says one is in flight
               // right now. Between the 'eb-scene' teardown and the last plate
               // landing, built is false and building is true — and that window is
               // exactly where a GPU baseline must not be read. Npc.ready() is the
               // same fact as something to await.
               building: inflight > 0, epoch: EPOCH,
               armed: armed, near: nearId, chained: !!(U() && U().__npcChain),
               // how many are rigged bodies, and how many mixers are live — the
               // second number must be zero after a teardown, and it is the one
               // a leak test can read without a heap snapshot
               models: PEOPLE.filter(function (P) { return P.model; }).length,
               mixers: PEOPLE.filter(function (P) { return !!P.mixer; }).length,
               // the discipline, asserted rather than promised
               inGroup: GROUP ? GROUP.children.length : 0,
               talking: !!(window.Dialogue && window.Dialogue.isOpen) };
    },
  };

  // Self-arming, like every other module here: additive, idempotent, and it
  // works with no coordinator hook at all (the hook only buys the deterministic
  // ordering against Shop's prompt). Waits for GS so dialogue's flag conditions
  // have somewhere to read from.
  // Bracketed by the settle signal exactly like the swap's rebuild is, so a
  // harness that waits on Npc.ready() gets the same guarantee on a fresh page load
  // as it gets across a door — the ?reload=1 fallback and every deep link run
  // through here and nowhere else.
  function arm() {
    buildStart();
    var done = function () { buildEnd(); }, p = null;
    try { p = registerPrompts(); } catch (e) { console.error('[Npc]', e); }
    Promise.resolve(p).then(done, function (e) { console.error('[Npc]', e); done(); });
  }
  if (window.GS && window.GS.ready && window.GS.ready.then) window.GS.ready.then(arm);
  else if (HAS_DOM) setTimeout(arm, 0);
  // the bundle lands after we do; re-seat once it has
  if (HAS_DOM) { setTimeout(resettle, 1500); setTimeout(resettle, 4000); }
})();
