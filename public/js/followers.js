// followers.js — window.Followers: the party walks behind you, IN TOWNS.
//
// THE COMPLAINT THIS ANSWERS (user, playthrough feedback 2026-08-03): party
// members and the cat do not follow the player. Lake joins at ch1.meet, Maren at
// ch2.landing, Mochi hires himself at ch1.pact — and every one of them then stood
// exactly where the script left them while the player walked the town alone.
//
// IT IS A BREADCRUMB TRAIL AND IT IS NOT A PATHFINDER. The leader's own recent
// positions are recorded on the physics tick; a follower is drawn at the point a
// fixed ARC LENGTH back along that polyline. That single choice is the whole
// design, and the reason it was chosen over anything cleverer:
//
//   * THE LEADER'S PATH IS WALKABLE BY DEFINITION. play3d's walkStep() already
//     refused every step that left the walk network, so every crumb is a place a
//     body was legally standing. A follower therefore cannot get stuck, cannot
//     need a nav-mesh query, cannot disagree with WALKLOCK, and cannot be asked
//     to solve a problem the walker already solved.
//   * IT HAS NO OPINION ABOUT COLLISION, so it cannot have a wrong one.
//   * ITS FAILURE MODE IS COSMETIC. The worst a bug here can do is put a
//     companion in the wrong place; it can never move, block or trap the player.
//
// If a future session finds itself wanting a path solver, a steering behaviour or
// an avoidance rule, it has left the design — go back to the trail.
//
// FOUR RULES, the npc.js rules restated because they are the ones that keep a
// decorative body from becoming a gameplay bug:
//  1. NEVER a floor, a wall or an occluder. Everything built here goes into ONE
//     THREE.Group and is never pushed into collide / walkRef / allMeshes. That is
//     what makes "followers must not block the player or each other" true by
//     construction rather than by tuning: play3d's blocked() tests `collide` and
//     nothing else, so a body that is not in it can never be in the way. A
//     follower that could push the player off a ledge would be worse than no
//     follower at all, and this is the line that makes it impossible.
//  2. NEVER touches game state. It READS GS.activeParty() and the flag ledger; it
//     writes nothing, and it decides nothing about who is in the party.
//  3. DEPTH-HONEST, STENCIL-CLEAN. Default materials, default render order: the
//     bundle's own baked depth map hides a companion behind a house exactly as it
//     hides a villager. Nothing here writes stencil — the player's GHOST pass owns
//     ref 1 alone (play3d.html), and a follower that stamped would punch holes in
//     the player's see-through-occluders twin.
//  4. RE-ARMS ON 'eb-scene'. Every module in this runtime self-arms at load AND on
//     the in-place scene swap; without that half, the followers would be built
//     into a Group that sceneDispose() does not empty and would silently be absent
//     from every scene after the first door. The teardown is total (geometry,
//     material, texture, skeleton boneTexture, mixer) because transition_test
//     counts exactly those.
//
// TOWNS ONLY — the user's ruling, verbatim: followers trail the leader IN TOWNS,
// NOT IN THE OVERWORLD. The scene test is the same regex WALKLOCK uses
// (/^(del-|emb-|townwalk)/), so "a scene where the walk network is law" and "a
// scene where the party walks behind you" are one predicate. ow-* is excluded and
// the corridor between the towns stays a solo walk, which is what the script has
// the party doing there anyway.
//
// WHO FOLLOWS.
//   * THE PARTY, from GS.activeParty(), minus whoever the player is wearing.
//     ONLY vesper / lake / maren are playable and only they have entries in
//     BODIES: a previous lane applied party logic to Finn and Mara — villagers —
//     and the user corrected it. A member with no BODIES entry is skipped, loudly
//     once, rather than guessed at.
//   * THE LEADER MUST HIM/HERSELF BE AN ACTIVE PARTY MEMBER, and that one line is
//     what keeps Chapter One's Lake POV solo. During ch1.lake.* the player wears
//     Lake, `lake-joined` is not set yet (ch1.meet sets it), so Lake is not in the
//     active party — the roster comes back empty and Vesper does not follow him
//     around his own cottage at four in the morning. It falls out of the data
//     instead of being a special case about a scene name.
//   * MOCHI IS NOT A PARTY MEMBER. He is a cat. He carries no growth.json record
//     and no joinFlag; he follows from `story.ch1.pact` — the beat that fires the
//     "Mochi joined the party" toast — and he wears the same plate npcs.json gives
//     him, keyed through the same EBUI.chromaKey the villagers use.
//     WHILE THE FOLLOWER CAT IS ALIVE, THE POSTED CATS ARE HIDDEN (Npc.hide):
//     'mochi-emb' at the Emberbrook waystone and 'mochi' at the Dellhollow eel
//     stall are the SAME CAT, and a cat at your heel while a second one sits at
//     the stall is a duplicate the player will read as a bug. The hail nodes stay
//     in the data; they are simply not reachable once he is yours.
//
// THE ONE THING A BREADCRUMB TRAIL NEEDS THAT IS NOT OBVIOUS: A TELEPORT IS NOT A
// WALK. SIM.tp(), an arrival spawn and a scene swap all move the leader metres in
// one tick, and replaying that as a path drags the followers through whatever is
// between the two points. Any sample further than SNAP metres from the last one
// RESETS the trail and re-seeds it BEHIND the player's own heading, so a companion
// arrives standing behind you instead of sprinting across the town to catch up.
//
// window.Followers
//   Followers.tick()     sample the leader (called from play3d's phys hook, so it
//                        runs under SIM.tick(n) in a background tab where rAF is dead)
//   Followers.list()     who is following, where they are, which clip — headless-readable
//   Followers.debug()    the whole live state
//   Followers.ready()    a promise for "the bodies have landed"
(function () {
  'use strict';

  // ---- knobs ---------------------------------------------------------------
  var LAG = [1.75, 2.90, 3.85];   // arc-length metres behind the leader, per slot
  var CRUMB = 0.14;               // metres between recorded crumbs
  var TRAIL = 9.0;                // metres of history kept (> max LAG + slack)
  var SNAP = 2.2;                 // a jump this big is a teleport, not a step
  var MOVE_EPS = 0.02;            // below this a follower is standing still
  var MAX_SPD = 9.0;              // m/s ceiling while catching up after a snap
  var NPC_WALK_UPS = 0.46;        // npc.js's measured Walk_Loop ground speed at 1.0
  var TICK_MS = 250;              // keepalive; rAF is throttled to nothing in a background tab

  // WHO CAN FOLLOW. Party ids -> body. Vesper is here because the player is not
  // always wearing her (the Lake POV), and when she is, she is filtered out as the
  // leader. Heights are multiples of charH, the same convention npcs.json uses.
  var BODIES = {
    vesper: { src: 'assets/characters/vesper/vesper-v2.glb', h: 1.00 },
    lake:   { src: 'assets/characters/lake/lake-v1.glb',     h: 1.10 },
    maren:  { src: 'assets/characters/maren/maren-v1.glb',   h: 1.05 },
  };
  // The MODELS key play3d hands the player -> the party id it means.
  var BODY_ID = { 'vesper-v2': 'vesper', 'vesper-test': 'vesper', 'lake': 'lake', 'maren': 'maren' };
  // The cat. `flag` is his joining, `hides` are the posted records he replaces.
  var CAT = {
    id: 'mochi', name: 'Mochi', plate: 'assets/characters/mochi/pose-front.png',
    h: 0.30, flag: 'story.ch1.pact', hides: ['mochi', 'mochi-emb'],
  };

  // play3d.html is a classic script: its top-level let/const live in the shared
  // global lexical scope and are readable from here — but a missing one is a
  // ReferenceError, so every read is guarded (npc.js / route_overlay precedent).
  var TH = function () { try { return THREE; } catch (e) { return window.THREE; } };
  var SCN = function () { try { return scene; } catch (e) { return null; } };
  var CHARH = function () { try { return MODEL_H; } catch (e) { return 1.45; } };
  var SIM = function () { return window.SIM || null; };
  var U = function () { return window.EBUI || null; };
  var HAS_DOM = typeof document !== 'undefined' && !!document.createElement;

  function skey() {
    var S = SIM(); if (S && S.scene) { try { return S.scene() || ''; } catch (e) { } }
    var s = null; try { s = SCENE; } catch (e) { }
    try { return s || new URLSearchParams(location.search).get('scene') || ''; } catch (e) { return s || ''; }
  }
  // TOWNS ONLY. Same predicate as WALKLOCK (play3d.html sceneParams): the scenes
  // where the walk network is law are the scenes where the party walks behind you.
  function inTown(k) { return /^(del-|emb-|townwalk)/.test(String(k || '')); }
  function flagOn(name) {
    var g = window.GS;
    try { return !!(g && g.state && g.state.flags && g.state.flags[name]); } catch (e) { return false; }
  }
  var OFF = (function () {
    try { if (window.__NOFOLLOW) return true;
      return new URLSearchParams(location.search).get('nofollow') === '1'; } catch (e) { return false; }
  })();

  // ---- state ---------------------------------------------------------------
  var GROUP = null;               // the one group; never in collide/walkRef/allMeshes
  var FOLK = [];                  // built followers for THIS scene
  var crumbs = [];                // [{x,y,z,s}] newest LAST; s = cumulative arc length
  var head = null;                // last sampled leader position
  var sceneKey = null, built = false, driving = false, hidden = [];
  // A RE-SEED IS A TELEPORT, AND A TELEPORT MUST NOT BE JOGGED TO. Without this the
  // speed cap in frame() applies to the catch-up as well, so after SIM.tp() (a
  // harness, an in-scene arrival spawn, play3d's marooned unstick) the party is
  // seen sprinting across the town for as long as the distance takes — measured
  // 2026-08-03 at 30 m and still closing. Consumed by the next frame().
  var SNAPQ = false;
  var settleP = null, settleGo = null, inflight = 0, warned = {};
  var EPOCH = 0;                  // strand every continuation a scene swap outran

  function buildStart() { inflight++; if (!settleP) settleP = new Promise(function (r) { settleGo = r; }); }
  function buildEnd() { if (--inflight <= 0) { inflight = 0; var g = settleGo; settleP = null; settleGo = null; if (g) g(true); } }
  function ready() { return settleP || Promise.resolve(true); }

  // ---- the roster ----------------------------------------------------------
  // READ-ONLY over GS. The party's composition is decided by story flags and
  // GS.syncJoins(); this file only asks who is active and who the player is.
  function leaderId() {
    var S = SIM();
    var b = null; try { b = S && S.body ? S.body() : null; } catch (e) { }
    return BODY_ID[b] || 'vesper';
  }
  function roster() {
    if (OFF) return [];
    var g = window.GS, out = [];
    var lead = leaderId();
    var party = [];
    try { party = (g && g.activeParty) ? g.activeParty() : []; } catch (e) { party = []; }
    var isLead = false;
    for (var i = 0; i < party.length; i++) if (party[i].id === lead) isLead = true;
    // The leader must be IN the active party — see the header: this is what keeps
    // the Lake POV solo without naming a scene.
    if (isLead) {
      for (var j = 0; j < party.length; j++) {
        var id = party[j].id;
        if (id === lead) continue;
        if (!BODIES[id]) {
          if (!warned[id]) { warned[id] = 1; console.warn('[Followers] no body for party member "' + id + '" — not following'); }
          continue;
        }
        out.push({ id: id, name: party[j].name || id, kind: 'model',
                   src: BODIES[id].src, h: BODIES[id].h });
      }
    }
    // The cat is not a party member and does not ride isLead: he follows whoever
    // is carrying the Spark, and he hired himself to the party, not to Vesper.
    if (flagOn(CAT.flag))
      out.push({ id: CAT.id, name: CAT.name, kind: 'plate', src: CAT.plate, h: CAT.h, cat: true });
    return out;
  }

  // ---- art -----------------------------------------------------------------
  // The blob shadow and the chroma key are npc.js's, called the same way for the
  // same reason: a companion's shadow and a villager's are the same shadow.
  var shadowTex = null;
  function blobShadow() {
    if (shadowTex) return shadowTex;
    var c = document.createElement('canvas'); c.width = c.height = 128;
    var g = c.getContext('2d');
    var rg = g.createRadialGradient(64, 64, 0, 64, 64, 64);
    rg.addColorStop(0, 'rgba(0,0,0,0.62)'); rg.addColorStop(0.45, 'rgba(0,0,0,0.36)');
    rg.addColorStop(0.78, 'rgba(0,0,0,0.10)'); rg.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = rg; g.fillRect(0, 0, 128, 128);
    shadowTex = new (TH().CanvasTexture)(c);
    return shadowTex;
  }
  var plateCache = Object.create(null);
  function plate(src) {
    if (plateCache[src]) return plateCache[src];
    return (plateCache[src] = new Promise(function (res) {
      if (typeof Image !== 'function' || !U() || !U().chromaKey) return res(null);
      var im = new Image();
      im.onload = function () { var c = null; try { c = U().chromaKey(im); } catch (e) { c = null; } res(c); };
      im.onerror = function () { console.warn('[Followers] missing plate ' + src); res(null); };
      im.src = src;
    }));
  }

  function makeRoot(rec) {
    var T = TH();
    var F = { id: rec.id, name: rec.name, cat: !!rec.cat, kind: rec.kind, h: CHARH() * rec.h,
              lag: 0, root: new T.Group(), mesh: null, mixer: null, aIdle: null, aWalk: null,
              clip: null, moving: false, yaw: 0, spd: 0, art: false };
    var sh = new T.Mesh(new T.PlaneGeometry(1, 1),
      new T.MeshBasicMaterial({ map: blobShadow(), transparent: true, depthWrite: false, opacity: 0.9 }));
    sh.rotation.x = -Math.PI / 2; sh.position.y = 0.02; F.shadow = sh; F.root.add(sh);
    var sw = Math.max(0.45, F.h * 0.62);
    sh.scale.set(sw, sw * 0.62, 1);
    GROUP.add(F.root);
    return F;
  }

  function loadModel(F, rec, ep) {
    var T = TH();
    return new Promise(function (res) {
      var L = null; try { L = new T.GLTFLoader(); } catch (e) { }
      if (!L) return res(F);
      L.load(rec.src, function (g) {
        if (ep !== EPOCH) { disposeTree(g.scene); return res(F); }
        var o = g.scene;
        var box = new T.Box3().setFromObject(o), sz = new T.Vector3(); box.getSize(sz);
        if (sz.y > 0.001) { var k = F.h / sz.y; o.scale.multiplyScalar(k); o.position.y -= box.min.y * k; sz.multiplyScalar(k); }
        o.traverse(function (c) {
          if (!c.isMesh) return;
          // A skinned bounding box is the BIND pose's box; an animated arm that
          // leaves it makes three.js cull a companion walking right beside you.
          c.frustumCulled = false; c.castShadow = false; c.receiveShadow = false;
        });
        F.root.add(o); F.mesh = o; F.art = true;
        var sw = Math.max(0.45, Math.max(sz.x, sz.z) * 1.4);
        F.shadow.scale.set(sw, sw * 0.62, 1);
        buildMixer(F, g.animations || []);
        res(F);
      }, null, function () { console.warn('[Followers] missing body ' + rec.src); res(F); });
    });
  }

  function loadPlate(F, rec, ep) {
    var T = TH();
    return plate(rec.src).then(function (canvas) {
      if (ep !== EPOCH || !canvas) return F;
      var tex = new T.CanvasTexture(canvas);
      if (T.sRGBEncoding !== undefined) tex.encoding = T.sRGBEncoding;
      tex.minFilter = T.LinearFilter; tex.generateMipmaps = false; tex.needsUpdate = true;
      var pw = F.h * (canvas.width / canvas.height);
      var geo = new T.PlaneGeometry(pw, F.h); geo.translate(0, F.h / 2, 0);
      var m = new T.Mesh(geo, new T.MeshBasicMaterial({ map: tex, transparent: true,
        alphaTest: 0.28, side: T.DoubleSide }));
      F.root.add(m); F.mesh = m; F.art = true; F.plate = true;
      F.shadow.scale.set(pw * 1.1, pw * 0.7, 1);
      return F;
    });
  }

  // Clip cadence: the same measured ratio npc.js uses (Walk_Loop covers 0.46 u/s
  // on a 1.45-unit body), driven off the follower's OWN speed, which is the
  // leader's speed one lag behind. Clamped, so a snap cannot make a blur.
  function buildMixer(F, clips) {
    var T = TH();
    if (!clips.length || !T.AnimationMixer) return;
    var pick = function (re) { for (var i = 0; i < clips.length; i++) if (re.test(clips[i].name)) return clips[i]; return null; };
    var ci = pick(/^Idle$/i) || pick(/idle/i) || clips[0];
    var cw = pick(/^Walking_A$/i) || pick(/walk/i) || pick(/run/i);
    F.mixer = new T.AnimationMixer(F.mesh);
    F.aIdle = ci ? F.mixer.clipAction(ci) : null;
    F.aWalk = cw ? F.mixer.clipAction(cw) : null;
    if (F.aIdle) { F.aIdle.play(); F.clip = 'idle'; }
  }
  function setClip(F, want) {
    if (!F.mixer || F.clip === want) return;
    var next = want === 'walk' ? F.aWalk : F.aIdle, prev = want === 'walk' ? F.aIdle : F.aWalk;
    if (!next) return;
    if (prev) prev.fadeOut(0.2);
    next.reset().fadeIn(0.2).play();
    F.clip = want;
  }

  // ---- the trail -----------------------------------------------------------
  function push(p) {
    var last = crumbs.length ? crumbs[crumbs.length - 1] : null;
    var s = last ? last.s + Math.hypot(p.x - last.x, p.z - last.z) : 0;
    crumbs.push({ x: p.x, y: p.y, z: p.z, s: s });
    var cut = s - TRAIL;
    while (crumbs.length > 2 && crumbs[0].s < cut) crumbs.shift();
  }
  // A follower is drawn at arc length `d` back from the newest crumb. Linear along
  // the polyline: the leader walked every one of these segments, so any point on
  // one is somewhere a body legally stood.
  function at(d) {
    if (!crumbs.length) return null;
    var end = crumbs[crumbs.length - 1], want = end.s - d;
    if (want <= crumbs[0].s) { var a = crumbs[0]; return { x: a.x, y: a.y, z: a.z, tail: true }; }
    for (var i = crumbs.length - 1; i > 0; i--) {
      var b = crumbs[i], a2 = crumbs[i - 1];
      if (want >= a2.s && want <= b.s) {
        var span = b.s - a2.s, t = span > 1e-6 ? (want - a2.s) / span : 0;
        return { x: a2.x + (b.x - a2.x) * t, y: a2.y + (b.y - a2.y) * t,
                 z: a2.z + (b.z - a2.z) * t, tail: false };
      }
    }
    var e = crumbs[0]; return { x: e.x, y: e.y, z: e.z, tail: true };
  }
  // HUDDLE AT THE DOOR. On an arrival there IS no trail — the leader has walked
  // nowhere in this scene yet — so every lag resolves to the same tail crumb and
  // three bodies stack on one point, which reads as one body with a rendering bug.
  // MEASURED, 2026-08-03: through emb-cine -> emb-item-int all three landed at
  // (5.75, 0, -6.08) exactly. A follower whose lag runs off the end of the trail
  // therefore takes a small fixed offset ACROSS it instead: the party bunches at
  // the doorway and strings back out the moment you walk. Cosmetic by
  // construction — nothing this file makes is in `collide` (rule 1).
  function trailDir() {
    if (crumbs.length >= 2) {
      var a = crumbs[0], b = crumbs[crumbs.length - 1];
      var dx = b.x - a.x, dz = b.z - a.z, m = Math.hypot(dx, dz);
      if (m > 0.05) return { x: dx / m, z: dz / m };
    }
    var yaw = 0; try { yaw = ch.rotation.y; } catch (e) { yaw = 0; }
    return { x: Math.sin(yaw), z: Math.cos(yaw) };
  }
  function spot(F, i) {
    var t = at(F.lag);
    if (!t || !t.tail) return t;
    var d = trailDir(), span = crumbs.length ? crumbs[crumbs.length - 1].s - crumbs[0].s : 0;
    var back = Math.min(0.7, Math.max(0, F.lag - span));
    var side = (i % 2 ? -1 : 1) * 0.42 * (Math.floor(i / 2) + 1);
    return { x: t.x - d.x * back - d.z * side, y: t.y, z: t.z - d.z * back + d.x * side, tail: true };
  }

  // SEED THE TRAIL BEHIND THE PLAYER'S HEADING, so an arrival (or a teleport)
  // puts the party at your back rather than starting them all inside you and
  // letting them unwind. `ch.rotation.y` is play3d's own facing and its
  // convention is atan2(dx, dz), so forward is (sin y, cos y).
  function seed(p) {
    crumbs = [];
    var yaw = 0; try { yaw = ch.rotation.y; } catch (e) { yaw = 0; }
    var fx = Math.sin(yaw), fz = Math.cos(yaw);
    var S = SIM(), n = Math.ceil((LAG[LAG.length - 1] + 1.2) / CRUMB);
    var pts = [];
    for (var i = n; i >= 1; i--) {
      var x = p.x - fx * (i * CRUMB), z = p.z - fz * (i * CRUMB), y = p.y;
      if (S && S.walkFloors) {
        var ys = null; try { ys = S.walkFloors(x, z); } catch (e) { }
        if (ys && ys.length) {
          var best = ys[0];
          for (var k = 1; k < ys.length; k++) if (Math.abs(ys[k] - p.y) < Math.abs(best - p.y)) best = ys[k];
          if (Math.abs(best - p.y) < 1.2) y = best; else { pts = []; continue; }
        } else { pts = []; continue; }   // off the network: drop everything further back
      }
      pts.push({ x: x, y: y, z: z });
    }
    for (var j = 0; j < pts.length; j++) push(pts[j]);
    push(p);
    head = { x: p.x, y: p.y, z: p.z };
    SNAPQ = true;
  }

  // Sample the leader. Rides play3d's PHYSICS tick (not rAF) so it advances under
  // SIM.tick(n) in a background tab, which is where headless verification lives.
  function tick() {
    if (!built) return null;
    var S = SIM(); if (!S) return null;
    var p = null; try { p = S.pos(); } catch (e) { }
    if (!p || !isFinite(p.x)) return null;
    if (!head || !crumbs.length) { seed(p); return crumbs.length; }
    var d = Math.hypot(p.x - head.x, p.z - head.z), dy = Math.abs(p.y - head.y);
    if (d > SNAP || dy > SNAP) { seed(p); return crumbs.length; }   // a teleport is not a walk
    if (d >= CRUMB) { push(p); head = { x: p.x, y: p.y, z: p.z }; }
    return crumbs.length;
  }

  // ---- the frame -----------------------------------------------------------
  var lastT = 0;
  function frame() {
    if (!FOLK.length) return;
    var now = Date.now() / 1000;
    var dt = lastT ? Math.min(0.1, now - lastT) : 0.016;
    lastT = now;
    var S = SIM(), lead = null;
    try { lead = S && S.pos ? S.pos() : null; } catch (e) { }
    for (var i = 0; i < FOLK.length; i++) {
      var F = FOLK[i];
      var t = spot(F, i);
      if (t) {
        var px = F.root.position.x, pz = F.root.position.z;
        var dx = t.x - px, dz = t.z - pz, dist = Math.hypot(dx, dz);
        // Move toward the trail point at a speed ceiling. Without the cap a snap
        // teleports the body; with it, a companion who fell behind jogs back on
        // the leader's OWN path and never leaves it.
        var step = SNAPQ ? dist : Math.min(dist, MAX_SPD * dt);
        if (dist > 1e-6) { F.root.position.x = px + dx / dist * step; F.root.position.z = pz + dz / dist * step; }
        F.root.position.y = SNAPQ ? t.y : F.root.position.y + (t.y - F.root.position.y) * Math.min(1, dt * 8);
        // A SNAP IS NOT A STRIDE. Without this line the frame that covers 30 m of
        // teleport reports a 30 m step, which reads as "moving" and plays one frame
        // of Walking_A at the clamp — a body that materialises mid-stride.
        F.spd = (SNAPQ || dt <= 0) ? 0 : step / dt;
        F.moving = !SNAPQ && step > MOVE_EPS;
        if (F.moving && dist > 1e-6) F.yaw = Math.atan2(dx, dz);
        else if (lead) {
          // Standing still, a companion turns to the person they are following.
          var ly = Math.atan2(lead.x - F.root.position.x, lead.z - F.root.position.z);
          var dpp = Math.atan2(Math.sin(ly - F.yaw), Math.cos(ly - F.yaw));
          F.yaw += dpp * Math.min(1, dt * 2.2);
        }
      }
      if (SNAPQ) F.root.rotation.y = F.yaw;    // arrive facing, do not swivel into place
      else {
        var dp = Math.atan2(Math.sin(F.yaw - F.root.rotation.y), Math.cos(F.yaw - F.root.rotation.y));
        F.root.rotation.y += dp * Math.min(1, dt * 9);
      }
      // A plate is yaw-billboarded to the camera and stays STANDING (a full lookAt
      // lies it down as the camera pitches) — the cat's whole body is one quad.
      if (F.plate && F.mesh) {
        var c = null; try { c = cam; } catch (e) { c = null; }
        if (c) F.mesh.rotation.y = Math.atan2(c.position.x - F.root.position.x,
                                              c.position.z - F.root.position.z) - F.root.rotation.y;
      }
      if (F.mixer) {
        setClip(F, F.moving ? 'walk' : 'idle');
        if (F.aWalk) F.aWalk.timeScale = Math.max(0.5, Math.min(3.2,
          F.spd / (NPC_WALK_UPS * ((F.h || CHARH()) / 1.45))));
        F.mixer.update(dt);
      }
    }
    SNAPQ = false;                   // one frame's worth: the teleport is spent
  }

  // ---- build / teardown ----------------------------------------------------
  function build() {
    var T = TH(), sc = SCN();
    if (!T || !sc) return Promise.resolve([]);
    sceneKey = skey();
    var town = inTown(sceneKey);
    var recs = town ? roster() : [];
    // Unconditional, and BEFORE the early returns: the posted cat must come back
    // the moment the following cat is not here, in whatever scene that is.
    syncDoubles(recs.some(function (r) { return r.cat; }));
    if (!town) return Promise.resolve([]);                 // towns only — the user's ruling
    if (!recs.length) return Promise.resolve([]);
    var ep = ++EPOCH;
    GROUP = new T.Group(); GROUP.name = 'followers'; sc.add(GROUP);
    // NOT pushed into collide / walkRef / allMeshes. See rule 1.
    var p = null; try { p = SIM() && SIM().pos(); } catch (e) { }
    if (p) seed(p);
    var jobs = recs.map(function (rec, i) {
      var F = makeRoot(rec);
      F.lag = LAG[Math.min(i, LAG.length - 1)] + (i >= LAG.length ? (i - LAG.length + 1) * 0.9 : 0);
      var t = spot(F, i) || p;
      if (t) F.root.position.set(t.x, t.y, t.z);
      FOLK.push(F);
      return rec.kind === 'plate' ? loadPlate(F, rec, ep) : loadModel(F, rec, ep);
    });
    return Promise.all(jobs).then(function () {
      if (ep !== EPOCH) return [];
      built = true;
      return FOLK;
    });
  }

  // The posted cat and the following cat are one animal — see the header. Npc.hide
  // is a PAGE-level intent, not scene state: it is honoured by every later spawn,
  // so it survives the doorway without either module having to win a race with the
  // other's 'eb-scene' handler.
  function syncDoubles(on) {
    if (!window.Npc || !window.Npc.hide) return;
    hidden = [];
    for (var i = 0; i < CAT.hides.length; i++) {
      try { window.Npc.hide(CAT.hides[i], !!on); } catch (e) { }
      if (on) hidden.push(CAT.hides[i]);
    }
  }

  // npc.js's disposal contract, verbatim in intent: three.js only decrements its
  // counters when it is TOLD. A rigged body hides one more texture than a plate —
  // the Skeleton's boneTexture, reachable from neither geometry nor material.
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

  function dropScene() {
    EPOCH++;
    for (var i = 0; i < FOLK.length; i++) {
      var F = FOLK[i];
      if (!F.mixer) continue;
      try { F.mixer.stopAllAction(); } catch (e) { }
      try { if (F.mesh) F.mixer.uncacheRoot(F.mesh); } catch (e) { }
      F.mixer = null; F.aIdle = null; F.aWalk = null;
    }
    if (GROUP) {
      var sc = SCN(); if (sc) { try { sc.remove(GROUP); } catch (e) { } }
      disposeTree(GROUP); GROUP = null;
    }
    if (shadowTex) { try { shadowTex.dispose(); } catch (e) { } shadowTex = null; }
    // `hidden` is NOT cleared here: build() re-decides it from the roster on the
    // way back up, and clearing it in the teardown would flash the posted cat back
    // into the frame for the length of a GLB load.
    FOLK = []; crumbs = []; head = null; built = false; sceneKey = null;
  }

  function drive() {
    if (driving || !HAS_DOM) return;
    driving = true;
    var raf = function () { frame(); requestAnimationFrame(raf); };
    requestAnimationFrame(raf);
    setInterval(function () { frame(); }, TICK_MS);   // rAF is dead in a background tab
  }

  function arm() {
    buildStart();
    var done = function () { buildEnd(); }, p = null;
    try { p = build().then(function (l) { if (l.length) drive(); return l; }); }
    catch (e) { console.error('[Followers]', e); }
    Promise.resolve(p).then(done, function (e) { console.error('[Followers]', e); done(); });
  }

  // THE PARTY CHANGES MID-SCENE. Lake joins at ch1.meet and Mochi at ch1.pact —
  // both inside emb-cine, with no door between the beat and the moment a companion
  // should be at your heel. Rebuilding on GS's own change event is what makes the
  // roster live rather than per-doorway; it is cheap because it no-ops unless the
  // roster's ids actually differ.
  function rosterKey() { return roster().map(function (r) { return r.id; }).join(','); }
  var lastKey = '';
  function resync() {
    if (!inTown(skey())) return;
    var k = rosterKey();
    if (k === lastKey) return;
    lastKey = k;
    try { dropScene(); } catch (e) { console.error('[Followers] resync teardown', e); }
    arm();
  }

  if (typeof window !== 'undefined' && window.addEventListener) {
    window.addEventListener('eb-scene', function () {
      try { dropScene(); } catch (e) { console.error('[Followers] eb-scene teardown', e); }
      lastKey = rosterKey();
      try { arm(); } catch (e) { console.error('[Followers] eb-scene', e); }
    });
  }

  window.Followers = {
    tick: tick, ready: ready, frame: frame,
    list: function () {
      return FOLK.map(function (F) {
        return { id: F.id, at: F.root.position.toArray().map(function (v) { return +v.toFixed(2); }),
                 lag: F.lag, art: F.art, body: F.plate ? 'billboard' : (F.art ? 'model' : 'none'),
                 clip: F.clip || null, moving: !!F.moving, spd: +(F.spd || 0).toFixed(2),
                 yaw: Math.round(((F.root.rotation.y * 180 / Math.PI) % 360 + 360) % 360) };
      });
    },
    debug: function () {
      return { scene: sceneKey, town: inTown(skey()), built: built, count: FOLK.length,
               leader: leaderId(), roster: rosterKey(), crumbs: crumbs.length,
               span: crumbs.length ? +(crumbs[crumbs.length - 1].s - crumbs[0].s).toFixed(2) : 0,
               hiddenNpcs: hidden.slice(), inGroup: GROUP ? GROUP.children.length : 0,
               mixers: FOLK.filter(function (F) { return !!F.mixer; }).length, epoch: EPOCH, off: OFF };
    },
  };

  if (window.GS && window.GS.ready && window.GS.ready.then)
    window.GS.ready.then(function () { lastKey = rosterKey(); arm(); });
  else if (HAS_DOM) setTimeout(function () { lastKey = rosterKey(); arm(); }, 0);
  // The party is data: a flag written by a beat has to reach the world without a
  // door. GS emits 'change' on every setFlags, so this is the same signal the
  // menu and the save screen already listen to.
  try { if (window.GS && window.GS.on) window.GS.on('change', function () { try { resync(); } catch (e) { } }); } catch (e) { }
})();
