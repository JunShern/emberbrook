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
    if (T.sRGBEncoding !== undefined) tex.encoding = T.sRGBEncoding;
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
    root.rotation.y = (rec.facing || 0) * Math.PI / 180;   // authored in degrees; a
                                                          // billboard cancels it, a
                                                          // future GLB will not
    var bob = new T.Group(); root.add(bob);
    GROUP.add(root);

    var P = {
      id: rec.id, name: rec.name || rec.id, rec: rec,
      root: root, bob: bob, mesh: null, shadow: null,
      home: root.position.clone(), y: root.position.y,
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
  // without any other line of this file changing.
  function loadModel(P, body, ep) {
    var T = TH();
    return new Promise(function (res) {
      var L = null;
      try { L = new T.GLTFLoader(); } catch (e) { }
      if (!L) { missing.push(P.id); return res(P); }
      L.load(body.src, function (g) {
        if (ep !== EPOCH) { disposeTree(g.scene); return res(P); }  // arrived for a scene we left
        var o = g.scene;
        var box = new T.Box3().setFromObject(o), sz = new T.Vector3(); box.getSize(sz);
        var targetH = CHARH() * (P.rec.height || 1);
        if (sz.y > 0.001) { var k = targetH / sz.y; o.scale.multiplyScalar(k); o.position.y -= box.min.y * k; sz.multiplyScalar(k); }
        P.bob.add(o); P.mesh = o; P.model = true; P.h = targetH; P.w = Math.max(sz.x, sz.z) || targetH * 0.5;
        P.art = true;
        var sw = Math.max(0.5, Math.min(2.2, P.w * 1.4));
        P.shadow.scale.set(sw, sw * 0.62, 1);
        res(P);
      }, null, function () { missing.push(P.id); res(P); });
    });
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
      if (!RM) {
        var amp = P.idle === 'lean' ? 0.018 : 0.028;
        P.bob.position.y = Math.sin(now * 1.55 + P.bobPhase) * amp;
      }
      if (P.idle === 'wander') wander(P, dt);
    }
  }

  // A SMALL WALK ON THE WALK NETWORK. The candidate step must land on a walk
  // floor within STEP_TOL of the current height and must not be blocked — the
  // same two questions play3d's phys() asks under WALKLOCK, asked through SIM so
  // this file owns no collision logic. A rejected step ends the errand rather
  // than sliding along a wall: villagers pace, they do not pathfind.
  function wander(P, dt) {
    var S = SIM(); if (!S) return;
    if (P.wait > 0) { P.wait -= dt; return; }
    if (!P.tgt) {
      var a = Math.random() * Math.PI * 2, r = P.wr * (0.35 + Math.random() * 0.65);
      P.tgt = { x: P.home.x + Math.cos(a) * r, z: P.home.z + Math.sin(a) * r };
      return;
    }
    var vx = P.tgt.x - P.root.position.x, vz = P.tgt.z - P.root.position.z;
    var d = Math.hypot(vx, vz);
    if (d < 0.12) { P.tgt = null; P.wait = 1.5 + Math.random() * 4; return; }
    var step = Math.min(d, P.wspd * dt);
    var nx = P.root.position.x + vx / d * step, nz = P.root.position.z + vz / d * step;
    var ny = groundAt(nx, nz, P.root.position.y);
    var offNet = ny === null || Math.abs(ny - P.root.position.y) > STEP_TOL;
    var wall = false;
    try { wall = !!S.blocked(nx, nz, P.root.position.y); } catch (e) { }
    if (offNet || wall) { P.tgt = null; P.wait = 2 + Math.random() * 3; return; }
    P.root.position.set(nx, ny, nz);
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
  function disposeTree(root) {
    if (!root || !root.traverse) return;
    var tex = new Set();
    root.traverse(function (o) {
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
  function dropScene() {
    EPOCH++;                                   // strand every continuation in flight
    if (GROUP) {
      var sc = SCN(); if (sc) { try { sc.remove(GROUP); } catch (e) { } }
      disposeTree(GROUP);
      GROUP = null;
    }
    if (shadowTex) { try { shadowTex.dispose(); } catch (e) { } shadowTex = null; }
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
                 h: +P.h.toFixed(2), art: P.art, idle: P.idle, dialogue: P.dialogue, shop: P.rec.shop || null };
      });
    },
    near: function () { var n = nearest(); return n ? { id: n.p.id, name: n.p.name, d: +n.d.toFixed(2) } : null; },
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
