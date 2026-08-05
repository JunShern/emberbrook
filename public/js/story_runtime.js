// story_runtime.js — window.Story: THE CHAPTER DIRECTOR.
//
// WHAT THIS IS FOR. Until 2026-08-02 the chapters lived only in the legacy 2-D
// engine (join-legacy.html): `public/js/chapter1.js` and `chapter2.js` are loaded
// by that page and by nothing else, so the game the player actually plays —
// play3d.html, the pre-rendered towns — had no chapter, no cutscene, no objective,
// no end card and no durable story flag. The elements were all built; the bridge
// was not. This module is the bridge, and `public/game/story.json` is the script it
// reads. See docs/plans/end-to-end-wiring.md (the audit) and
// docs/plans/ch1-staging-audit.md (the beat-to-scene staging authority).
//
// IT INVENTS NOTHING IT COULD REUSE. That is the design, not modesty:
//   prose        -> Dialogue.play() on nodes injected from story.json. One box,
//                   one typing rule, one bust/cut-in chain, one UILOCK contract.
//   conditions   -> Dialogue.check() verbatim. There is exactly ONE condition
//                   language in this project and dialogue.json already speaks it.
//   effects      -> GS.setFlags / GS.addItem / GS.addGold. A beat NEVER writes a
//                   flag by hand, so the save, the join sync and every listening
//                   panel agree by construction.
//   camera       -> SIM.shot(id), which is the shipped cut, not a second one.
//   the freeze   -> UILOCK, the engine's own modal-input contract.
//   scene moves  -> NONE. A beat never teleports the player across a scene: the
//                   corridor between the towns is WALKED. (chapter2.js:261 fakes it
//                   with a fade and a coordinate; that is the anti-pattern this
//                   whole layer exists to retire.)
//
// A CHAPTER IS A SET OF FLAGS PLUS A SET OF BEATS, NEVER A MODE. There is no
// setChapter(), no Chapter2.begin(), no resetFlags(). `GS.state.at.chapter` is a
// LABEL for the save screen and the music; it never changes how input or the world
// works. That is what makes Ch1 -> corridor -> Ch2 one continuous game instead of
// three games in a trench coat.
//
// SELF-ARMING, like every other module (play3d.html's 'eb-scene' contract): it
// arms at load AND re-arms on every scene swap, and it no-ops safely if
// game/story.json is absent.
(function () {
  'use strict';

  var URL_DATA = 'game/story.json';
  var DATA = null, LOADING = null, FAILED = false;
  var busy = false;                 // a beat is running
  var ticks = 0;
  var objective = null;             // the current objective string (null = hidden)
  var lastScene = null, lastShot = null;
  var log = [];                     // {id, at} — what fired this session, for the harness

  var HAS_DOM = typeof document !== 'undefined' && !!document.createElement;
  // ?nostory=1 (or window.__NOSTORY) — the escape hatch, and it exists for the same
  // reason ?nomusic=1 and ?walklock=0 do: a harness that is measuring something ELSE
  // must be able to get a story-free world without anybody switching the story off
  // by default. It is NEVER the default and no shipped gate sets it: a gauntlet that
  // passes because the story was disabled is worth nothing.
  var OFF = (function () {
    try { if (window.__NOSTORY) return true;
      return new URLSearchParams(location.search).get('nostory') === '1'; } catch (e) { return false; }
  })();

  function G() { return window.GS && window.GS.state ? window.GS : null; }
  function flags() { var g = G(); return g ? g.state.flags : null; }
  function ledger() { var g = G(); if (!g) return null;
    if (!g.state.beats) g.state.beats = {}; return g.state.beats; }
  function check(c) {
    if (c === undefined || c === null) return true;
    if (window.Dialogue && window.Dialogue.check) { try { return !!Dialogue.check(c); } catch (e) { return false; } }
    return false;                   // fail closed: no evaluator, no beat
  }
  function scene() { return window.SIM && SIM.scene ? SIM.scene() : null; }
  function shot() { var c = window.SIM && SIM.cine ? SIM.cine() : null; return c ? c.shot : null; }

  // ------------------------------------------------------------------- data --
  function load() {
    if (DATA) return Promise.resolve(DATA);
    if (FAILED) return Promise.resolve(null);
    if (LOADING) return LOADING;
    if (typeof fetch !== 'function') { FAILED = true; return Promise.resolve(null); }
    LOADING = fetch(URL_DATA).then(function (r) { return r.ok ? r.json() : null; })
      .catch(function () { return null; })
      .then(function (j) {
        LOADING = null;
        if (!j) { FAILED = true; console.log('[Story] no ' + URL_DATA + ' — the story layer is idle'); return null; }
        DATA = j;
        // the prose goes to the ONE dialogue window (see Dialogue.inject)
        if (window.Dialogue && window.Dialogue.inject)
          Dialogue.inject({ nodes: j.nodes || {}, speakers: j.speakers || {} });
        return j;
      });
    return LOADING;
  }

  // -------------------------------------------------------------------- HUD --
  // DOM overlays in the style of play3d's own sgPrompt and exit markers: a
  // pre-rendered scene carries fixed light, so the UI layer carries the legibility.
  var box = null;
  function host() { return (HAS_DOM && document.getElementById('s')) || (HAS_DOM && document.body) || null; }
  function style() {
    if (!HAS_DOM || document.getElementById('story-css')) return;
    var s = document.createElement('style'); s.id = 'story-css';
    s.textContent = [
      '#story-obj{position:absolute;left:50%;top:3.5%;transform:translateX(-50%);z-index:3;',
      ' color:#e7ddd0;font:13px monospace;background:#000b;border:1px solid #3a2c20;border-radius:8px;',
      ' padding:6px 13px;text-shadow:0 1px 2px #000;pointer-events:none;white-space:nowrap;',
      ' opacity:0;transition:opacity 200ms linear;max-width:88%;overflow:hidden;text-overflow:ellipsis}',
      '#story-obj b{color:#e9a24b}',
      '#story-banner{position:absolute;inset:0;z-index:6;display:flex;flex-direction:column;',
      ' align-items:center;justify-content:center;pointer-events:none;opacity:0;',
      ' transition:opacity 420ms linear;text-align:center;text-shadow:0 2px 10px #000}',
      '#story-banner .t{color:#f2e2c8;font:600 clamp(20px,3.4vw,44px)/1.2 Georgia,serif;letter-spacing:.06em}',
      '#story-banner .s{color:#c9b393;font:italic clamp(12px,1.5vw,19px)/1.6 Georgia,serif;margin-top:.5em}',
      '#story-card{position:fixed;inset:0;z-index:8;background:#000;display:flex;flex-direction:column;',
      ' align-items:center;justify-content:center;opacity:0;transition:opacity 700ms linear;gap:1.1em;padding:6vh 8vw}',
      '#story-card .t{color:#f2e2c8;font:600 clamp(22px,3.6vw,46px)/1.2 Georgia,serif;letter-spacing:.06em}',
      '#story-card p{color:#bda98a;font:italic clamp(13px,1.6vw,20px)/1.7 Georgia,serif;margin:0;max-width:44ch;text-align:center}',
      '#story-card .k{color:#7c6a52;font:11px monospace;margin-top:1.6em}',
      '#story-toast{position:absolute;left:50%;bottom:16%;transform:translateX(-50%);z-index:5;',
      ' font:13px monospace;background:#000c;border:1px solid #3a2c20;border-radius:8px;padding:7px 15px;',
      ' pointer-events:none;opacity:0;transition:opacity 220ms linear;white-space:nowrap}',
    ].join('');
    document.head.appendChild(s);
  }
  function el(id, cls) {
    if (!HAS_DOM) return null;
    var e = document.getElementById(id);
    if (!e) { e = document.createElement('div'); e.id = id; if (cls) e.className = cls;
      var h = host(); if (!h) return null; h.appendChild(e); }
    return e;
  }
  /* AN OBJECTIVE THAT NAMES A JOB ALREADY DONE IS WORSE THAN ONE THAT NAMES NOTHING
   * (playtest round 15). Chapter One's "See to them" is four anchors in ONE scene, so
   * the wayfinder has nothing to draw — routeTo() only ever answers with an EXIT — and
   * the sentence IS the route. But a beat fires once and cannot know what the other
   * three beats have done since, so a static string kept sending the player back to
   * Poppy after Poppy: measured at 20+ steps of a 200-step budget in run-20260805-015721.
   *
   *   {!flag: text}   emit `text` only while `flag` is falsy.
   *
   * The RAW string is what is stored, so every re-render re-reads the flags — which is
   * what makes one string serve all five beats and update itself as they tick off. It
   * expands BEFORE the <> strip, and the syntax itself carries no <> , so an author
   * cannot smuggle markup through the template. No flags, no evaluator, or a malformed
   * template: the segment is DROPPED, never printed raw. */
  function expandObjective(s) {
    return String(s).replace(/\{!([A-Za-z0-9_.\-]+):([^{}]*)\}/g, function (_, f, txt) {
      var F = flags(); if (!F) return '';
      return F[f] ? '' : txt;
    }).replace(/\s{2,}/g, ' ').replace(/[\s,;:—-]+$/, '').trim();
  }
  function setObjective(txt) {
    if (txt !== undefined) objective = txt || null;
    style(); var e = el('story-obj'); if (!e) return objective;
    if (!objective) { e.style.opacity = '0'; return null; }
    e.innerHTML = '<b>&#9670;</b> ' + expandObjective(objective).replace(/[<>]/g, '');
    e.style.opacity = '1';
    return objective;
  }
  function banner(b) {
    style(); var e = el('story-banner'); if (!e) return Promise.resolve();
    e.innerHTML = '<div class="t"></div><div class="s"></div>';
    e.children[0].textContent = b.title || '';
    e.children[1].textContent = b.sub || '';
    e.style.opacity = '1';
    var ms = (b.ms == null ? 3200 : b.ms);
    return wait(ms / 1000).then(function () { e.style.opacity = '0'; return wait(0.45); });
  }
  function toast(t) {
    style(); var e = el('story-toast'); if (!e) return Promise.resolve();
    e.textContent = t.text || '';
    e.style.color = t.color || '#e7ddd0';
    e.style.opacity = '1';
    return wait(t.ms == null ? 2.6 : t.ms / 1000).then(function () { e.style.opacity = '0'; });
  }
  // THE END CARD. It is DISMISSIBLE AND IT ALSO TIMES OUT, both, because the one
  // thing a chapter ending must never be is a screen the player cannot leave.
  function endCard(c) {
    style(); var e = el('story-card'); if (!e) return Promise.resolve();
    var html = '<div class="t"></div>';
    (c.lines || []).forEach(function () { html += '<p></p>'; });
    html += '<div class="k">press any key</div>';
    e.innerHTML = html;
    e.children[0].textContent = c.title || '';
    (c.lines || []).forEach(function (t, i) { e.children[i + 1].textContent = t; });
    e.style.display = 'flex';
    return wait(0.05).then(function () {
      e.style.opacity = '1';
      return new Promise(function (res) {
        var done = false, t0 = Date.now();
        function go() { if (done) return; done = true;
          if (HAS_DOM) window.removeEventListener('keydown', onKey, true);
          e.style.opacity = '0';
          setTimeout(function () { e.style.display = 'none'; res(); }, 750); }
        function onKey() { if (Date.now() - t0 < 1200) return; go(); }   // no accidental skip
        if (HAS_DOM) window.addEventListener('keydown', onKey, true);
        setTimeout(go, c.ms == null ? 16000 : c.ms);                     // and it leaves by itself
      });
    });
  }
  function wait(sec) {
    // setTimeout, NOT rAF: rAF is throttled to nothing in a background tab, and
    // every headless verification this project has lives in one (play3d.html's
    // own note at sgOpen). A beat that never advances there is a beat no test
    // can drive.
    return new Promise(function (r) { setTimeout(r, Math.max(0, (sec || 0) * 1000)); });
  }

  // ------------------------------------------------------------------ steps --
  function doStep(s) {
    if (!s || typeof s !== 'object') return Promise.resolve();
    // -- prose ---------------------------------------------------------------
    if (s.dialogue) {
      if (!(window.Dialogue && Dialogue.play)) return Promise.resolve();
      return Promise.resolve(Dialogue.play(s.dialogue)).then(function (r) {
        if (r === null) console.warn('[Story] dialogue node "' + s.dialogue + '" did not play');
      });
    }
    // -- world state (ALWAYS through GS) -------------------------------------
    if (s.setFlags) { if (G()) GS.setFlags(s.setFlags); }
    if (s.incFlags && G()) { var f = flags(), m = {};
      for (var k in s.incFlags) m[k] = (f[k] || 0) + s.incFlags[k];
      GS.setFlags(m); }
    if (s.giveItem && G() && GS.ok) GS.addItem(s.giveItem, s.qty || 1);
    if (s.gold && G() && GS.ok) GS.addGold(s.gold);
    if (s.chapter && G()) { GS.setAt({ chapter: s.chapter }); }
    // -- presentation --------------------------------------------------------
    if (s.objective !== undefined) setObjective(s.objective);
    if (s.shot && window.SIM && SIM.shot) return Promise.resolve(SIM.shot(s.shot));
    // -- WHOSE BODY IS THE PLAYER --------------------------------------------
    // {pov:{as:'lake', scene:'emb-lake-int', spawn:[x,y,z], yaw, cam}}. The ONLY
    // route to SIM.pov, and it is a CHANGE OF PROTAGONIST, not the teleport step
    // the schema forbids. The distinction is `as`: a pov step must name a new body,
    // so it can never be a shortcut for travel with the same character (asserted in
    // tools/story_test.mjs §7). Chapter One's Lake act is the only caller: Vesper's
    // half ends in the square, the cut hands the player to Lake in his grandmother's
    // cottage — where he has been all evening, nobody has been moved — and every
    // metre from that cottage to the pond lane is walked by the player.
    if (s.pov) {
      if (!(window.SIM && SIM.pov)) { console.warn('[Story] pov step but no SIM.pov'); return Promise.resolve(); }
      return Promise.resolve(SIM.pov(s.pov)).then(function (r) {
        if (r && r.error) console.warn('[Story] pov failed: ' + r.error);
        return r;
      });
    }
    if (s.banner) return banner(s.banner);
    if (s.toast) return toast(s.toast);
    if (s.endCard) return endCard(s.endCard);
    if (s.wait) return wait(s.wait);
    if (s.save) { if (G() && GS.autosave) GS.autosave(); }
    return Promise.resolve();
  }

  function runBeat(b) {
    busy = true;
    // The world holds its breath for the whole beat: UILOCK is play3d's own modal
    // contract — phys() freezes, held keys are zeroed, sgTick cannot fire a door
    // and markersTick hides every arrow. The dialogue window layers its own panel
    // lock on top and captures its own keys, exactly as an NPC conversation does.
    if (window.UILOCK) UILOCK.lock('story');
    var steps = (b['do'] || []).slice(), i = 0;
    function next() {
      if (i >= steps.length) return Promise.resolve();
      var s = steps[i++];
      return Promise.resolve(doStep(s)).then(next, function (err) {
        console.error('[Story] beat "' + b.id + '" step failed', err); return next();
      });
    }
    return next().then(function () {
      // THE LEDGER IS WRITTEN AT THE END, not the start: a beat interrupted by a
      // reload should play again rather than be silently lost. It goes in the SAVE
      // (GS.state.beats), so a `once` beat cannot replay across a session either.
      var L = ledger();
      if (b.once !== false && L) { L[b.id] = 1; }
      log.push({ id: b.id, scene: scene(), t: Date.now() });
      if (window.UILOCK) UILOCK.unlock('story');
      busy = false;
      if (G() && GS.autosave) { recordAt(); GS.autosave(); }
      return b.id;
    }, function (err) {
      console.error('[Story] beat "' + b.id + '" failed', err);
      if (window.UILOCK) UILOCK.unlock('story');
      busy = false;
      return null;
    });
  }

  // ------------------------------------------------------------ eligibility --
  function eligible(b) {
    if (!b || !b.id) return false;
    var L = ledger();
    if (b.once !== false && L && L[b.id]) return false;
    if (b.scene && b.scene !== scene()) return false;
    if (b.cam && b.cam !== shot()) return false;
    if (b.when && !check(b.when)) return false;
    if (b.at) {
      if (!(window.SIM && SIM.pos)) return false;
      var p = SIM.pos(), r = b.r == null ? 3.0 : b.r;
      var dy = Math.abs(p.y - b.at[1]);
      if (dy > (b.vTol == null ? 3 : b.vTol)) return false;
      if (Math.hypot(p.x - b.at[0], p.z - b.at[2]) > r) return false;
    }
    return true;
  }

  /* ================= THE WAY TO THE OBJECTIVE (playtest round 11) =============
   *
   * WHY THIS IS HERE AND NOT IN THE MARKER LAYER. The objective banner says WHERE
   * ("Midnight, at Lock Five — the head-gate winches"). Nothing on screen said
   * WHICH WAY, and Dellhollow is fifteen shots joined by forty-two anonymous cut
   * bands. THREE independent playtest runs failed at the same spot, and every
   * filing was reach-REFUTED on tools/reach_probe.mjs — the walk network is clean
   * twice over. The defect was legibility, and the banner is this module's, so the
   * direction is this module's too.
   *
   * MEASURED, before anything was written (tools/playtest/wayfind_probe.mjs, the
   * three failing runs' own positions and shots, 2026-08-04):
   *
   *   station        markers drawn   identical red cuts   the ONE toward Lock Five
   *   cottage door         4                3             cottage>cottage-steps
   *   lockhead             2                2             lockhead>quay-west
   *   quay deck            6                5             quay-west>weave
   *   loop-stairs          3                3             loop-stairs>quay-west
   *   valley gate          3                2             the gate stair
   *
   * At the quay deck the right triangle and a WRONG one draw 9 px apart in x. And
   * SIM.pick at each marker's own drawn pixel lands on SCENERY — cliff_town_back,
   * shelf_home_a_5, an awning, a rail — for 9 of the 21 shown markers, because
   * markersTick lifts the arrow 2.1 m + 30 px (measured here at 86-164 px, 0.12 to
   * 0.23 of frame height, in EVERY shot, not only steep ones). The lift is
   * deliberate FF7 grammar and is left alone; what was missing is a NAME.
   *
   * WHAT IT DOES. Finds the beat the chapter is waiting on, BFS's the shipped
   * scenegraph from the shot the player is standing in to the shot that beat names,
   * and puts the objective's own amber diamond and the DESTINATION's own name under
   * the ONE marker that starts that route.
   *
   * THREE RULES IT KEEPS:
   *  1. IT DECORATES, IT NEVER DRAWS. The label is appended INSIDE markersTick's own
   *     marker div, found by `data-edge`. So it inherits every gate that layer
   *     already applies — sealed, denied, camFrom, frustum, UILOCK — and it is
   *     structurally incapable of naming a way the game is not offering.
   *  2. IT NAMES THE DESTINATION, NOT THE HOP. At the quay deck the next hop is
   *     `weave`; the label still reads "Lock Five", because that is what the banner
   *     says and matching them is the entire point.
   *  3. ONE MARKER, EVER. "A town of named doorways is noise" (markersTick's own
   *     ruling, kept): every other triangle stays bare, which is what makes this one
   *     mean something.
   *
   * ?nohint=1 disables it. Story.wayhint() is the instrument.
   */
  var HINT_OFF = (function () {
    try { return new URLSearchParams(location.search).get('nohint') === '1'; }
    catch (e) { return false; }
  })();
  var hintEdge = null, hintTicks = 0, lastHint = null, lastObjDrawn = null;

  // play3d.html is a classic script: CINE and SG are top-level `let`s, so they live
  // in the shared global LEXICAL scope and are readable bare — but NOT as window.SG
  // (window.cam being undefined is how the probe first read "this edge has no
  // position"). Guarded, because a missing binding must disable the hint, never throw.
  function SGraph() { try { return SG; } catch (e) { return null; } }
  function CineDef() { try { return CINE; } catch (e) { return null; } }

  // THE BEAT THE CHAPTER IS WAITING ON: eligible on its CONDITIONS but not yet on
  // its place. Deliberately not eligible() — that one answers "may this fire HERE",
  // and the whole question is where "here" ought to be.
  function pendingBeat() {
    if (!DATA) return null;
    var L = ledger(), bs = DATA.beats || [];
    for (var i = 0; i < bs.length; i++) {
      var b = bs[i];
      if (!b || !b.id) continue;
      if (b.once !== false && L && L[b.id]) continue;
      if (b.when && !check(b.when)) continue;
      if (!b.scene && !b.cam) continue;          // nothing to point at
      return b;
    }
    return null;
  }

  function nodeKey(s, c) { return s + '|' + (c || '*'); }
  // A conditional edge is evaluated with the game's own condition language, the same
  // way sgLive does it, so a sealed gate is never routed through. FAILS CLOSED.
  function edgeLive(e) {
    var w = e.when || (e.requires ? { flag: e.requires } : null);
    return w ? check(w) : true;
  }

  /* THE ROUTE. Nodes are (scene, shot) pairs, so one search answers both "which
   * triangle in this town" and "which door out of it" — the corridor between the
   * towns is the same graph. An edge with no camFrom leaves from ANY shot (that is
   * what an interior's single-shot door is), and one whose destination shot is
   * unknown lands on the scene's wildcard node. Optimistic on the wildcard, which is
   * right for a HINT: the cost of a hop too many is a longer walk, the cost of
   * refusing is the silence we are fixing.
   *
   * IT COSTS METRES, NOT HOPS (2026-08-05). This was a hop-count BFS, and hops are
   * not metres. Standing on the Lockhead — directly above Lock Five — BOTH routes to
   * `lockfive` are exactly three hops:
   *     lockhead > cottage > cottage-steps > lockfive   21.9 m
   *     lockhead > quay-west > weave      > lockfive   45.9 m
   * BFS returned whichever it dequeued first, which was the second, so the ONE
   * labelled arrow pointed the player away down the length of the town — and the
   * playtest agent walked it, twice, into the pilot-cluster stalls. A tie in hops is
   * not a tie on the ground. Cost is the distance the body actually covers: from
   * where the player IS to the first seam, then seam to seam, using each edge's own
   * `spawn` (where the player lands) when it has one. A hop into ANOTHER scene has
   * no comparable coordinates, so it pays a flat XSCENE and the walk restarts from
   * that edge's spawn — an honest "a scene away", never a number pretending to be
   * measured. Dijkstra over 42 edges at 6 Hz is free. */
  var XSCENE = 40;      // nominal metres for a hop the coordinates cannot span
  var NOPOS = 12;       // nominal metres for a seam that carries no position
  function seamPos(e) { return (e && (e.spawn || e.at)) || null; }
  function gap(a, b) {
    if (!a || !b || a.length < 3 || b.length < 3) return NOPOS;
    var dx = a[0] - b[0], dy = a[1] - b[1], dz = a[2] - b[2];
    var d = Math.sqrt(dx * dx + dy * dy + dz * dz);
    return isFinite(d) ? d : NOPOS;
  }
  function routeTo(destScene, destCam) {
    var G = SGraph(); if (!G || !G.edges) return null;
    var here = scene(); if (!here) return null;
    var start = nodeKey(here, shot());
    var byFrom = {};
    for (var i = 0; i < G.edges.length; i++) {
      var e = G.edges[i]; if (!e.from || !e.to) continue;
      (byFrom[e.from] = byFrom[e.from] || []).push(e);
    }
    var goal = function (s, c) {
      return s === destScene && (!destCam || c === destCam || c === '*');
    };
    if (goal(here, shot())) return { hops: 0, edge: null };
    var p = window.SIM && SIM.pos ? SIM.pos() : null;
    var at0 = (p && isFinite(p.x)) ? [p.x, p.y, p.z] : null;
    // best[node] = cheapest cost seen; open = frontier, scanned linearly (tiny graph)
    var best = {}, open = [{ k: start, at: at0, cost: 0, hops: 0, first: null }];
    best[start] = 0;
    var found = null;
    while (open.length) {
      var bi = 0;
      for (var m = 1; m < open.length; m++) if (open[m].cost < open[bi].cost) bi = m;
      var cur = open.splice(bi, 1)[0];
      if (found && cur.cost >= found.cost) break;      // nothing cheaper can remain
      if (best[cur.k] < cur.cost) continue;
      var parts = cur.k.split('|'), sc = parts[0], cm = parts[1];
      var outs = byFrom[sc] || [];
      for (var j = 0; j < outs.length; j++) {
        var ed = outs[j];
        if (ed.camFrom && cm !== '*' && ed.camFrom !== cm) continue;
        if (!edgeLive(ed)) continue;
        var cross = ed.to !== sc;
        var step = cross ? XSCENE : gap(cur.at, ed.at || ed.spawn);
        var cost = cur.cost + step;
        var nc = (ed.cam && ed.cam.key) || null, nk = nodeKey(ed.to, nc);
        var first = cur.first || ed, hops = cur.hops + 1;
        if (goal(ed.to, nc || '*')) {
          if (!found || cost < found.cost) found = { hops: hops, edge: first, cost: cost };
          continue;                                    // keep looking for a shorter one
        }
        if (best[nk] !== undefined && best[nk] <= cost) continue;
        best[nk] = cost;
        open.push({ k: nk, at: seamPos(ed), cost: cost, hops: hops, first: first });
      }
    }
    return found ? { hops: found.hops, edge: found.edge } : null;
  }

  /* THE SHOT A BEAT WITHOUT A `cam` IS ACTUALLY ASKING FOR (2026-08-05, round 15's
   * deferred fix). A beat may name a place with `at` and no `cam` — all four of Chapter
   * One's `ch1.see.*` do — and `routeTo(scene, null)` then has a `goal` whose camera
   * clause is vacuously true, so it collapses to "are we in this scene". The player IS,
   * so the route is zero hops, the edge is null, and NO LABEL IS EVER DRAWN for the one
   * objective in the chapter that sends the player to four places 40-90 m apart across
   * four camera bands. Not a wrong arrow — no arrow.
   *
   * The bands are already in the scenegraph and this is `findability_test.ownerShot()`
   * written out: whichever shot's box contains the beat's own `at`, last match wins,
   * the same rule play3d's band test uses. It FAILS CLOSED — no `at`, no graph, no
   * owning band, and the caller gets null and today's behaviour back. */
  function beatCam(b) {
    if (!b) return null;
    if (b.cam) return b.cam;
    var at = b.at; if (!at || at.length < 3) return null;
    var G = SGraph(); if (!G || !G.nodes) return null;
    var n = G.nodes[b.scene || scene()]; if (!n || !n.shots) return null;
    var hit = null;
    for (var i = 0; i < n.shots.length; i++) {
      var s = n.shots[i], bx = s.boxes || [];
      for (var j = 0; j < bx.length; j++) {
        var q = bx[j];
        if (q[0] <= at[0] && at[0] <= q[2] && q[1] <= at[2] && at[2] <= q[3]) hit = s.id;
      }
    }
    return hit;
  }

  // The destination's own authored name: a shot's `name` out of the bundle's
  // cine.json ("Lock Five"), or the scene node's label out of the scenegraph
  // ("Dellhollow"). Never a string invented here. `cam` is passed in because it may
  // have been DERIVED from the beat's `at` (see beatCam) rather than authored.
  function destName(b, cam) {
    var C = CineDef(), G = SGraph();
    var c = cam === undefined ? b.cam : cam;
    if (c && b.scene === scene() && C && C.byId && C.byId[c] && C.byId[c].name)
      return C.byId[c].name;
    if (b.scene && G && G.nodes && G.nodes[b.scene] && G.nodes[b.scene].label)
      return G.nodes[b.scene].label;
    return null;
  }

  function clearHint() {
    if (!HAS_DOM) { hintEdge = null; return; }
    undimRivals();
    if (!hintEdge) { hintEdge = null; return; }
    var m = document.querySelector('#exit-markers > div[data-edge="' + cssEsc(hintEdge) + '"]');
    if (m) {
      var t = m.querySelector('.story-way'); if (t) t.remove();
      m.style.zIndex = '';
      if (m.firstChild && m.firstChild.style) m.firstChild.style.scale = '';
      unclampLift(m);
    }
    hintEdge = null;
  }

  /* THE ARROW ON THE CLIFF (round 19) — the routed marker was drawn 97 px above the
   * ground it names, and that is far enough to be a different place.
   *
   * MEASURED, `wayfind_probe --from ch2.jam --liftcap 16,20,24,28,32,35,50,70,90`
   * (docs/qa/playtest/wayfind-r19, -r19b), 24 shown markers over seven Dellhollow
   * stations. For each one: SIM.pick at the arrow's OWN drawn pixel, and the distance
   * from what it hit to the seam's own `at`.
   *
   *   lift            uncapped   20 px   35 px   50 px   90 px
   *   within 3 m         5/24    19/24   17/24   15/24    7/24
   *
   * `quay-west>lockhead` — the arrow Chapter Two's `ch2.jam` is reached by — was the
   * worst of them: **31.4 m off**, landing on `cliff_town_back` 70 m behind the town,
   * because 2.1 m of world lift on a 14 m seam is 97 px of screen and the deck it names
   * is only a few px deep in that shot. `run-20260805-044813`'s agent wrote *"ground
   * marked as not walkable"* and *"cannot figure out how to reach the marker"* FIVE
   * times. Round 10 made the EXECUTOR immune (a click on an arrow resolves to the edge's
   * own `at`); nothing makes the reader immune. Same family as round 5's off-screen
   * label and round 18's rival arrow: THE ARROW IS IN THE RIGHT PLACE IN THE WORLD AND
   * THE WRONG PLACE ON THE SCREEN.
   *
   * 20 px is both the global optimum and the ONLY band that fixes that arrow (24 px and
   * up put it back on the cliff — its ground is a 4 px-deep sliver). With markersTick's
   * 16 px glyph the tip then lands ~4 px above the seam: still the FF7 "floats over the
   * spot and points down at it" grammar, just honest about which spot.
   *
   * IT DECORATES, IT NEVER DRAWS (this module's rule 1, kept). `markersTick` rewrites
   * `transform` and `display` on the marker div every frame and nothing else, so this
   * writes the CSS `translate` property on the div's CHILDREN — a different property on
   * different nodes, exactly as `dimRivals` already writes `scale` on the triangle. The
   * offset is measured off the triangle's OWN bounding rect (the artifact, not a re-derived
   * intent) with our previous nudge subtracted, and only rewritten when it moves more
   * than 6 px, which is wider than markersTick's own +-5 px bob — so the arrow keeps
   * bobbing and this never thrashes at 6 Hz.
   *
   * THE GENERAL FIX BELONGS IN `markersTick` and is prepared for the coordinator in
   * FIXLOG round 19: this clamps the ONE routed marker, that would clamp all 24. If it
   * lands, this goes to zero by construction (dy is a max against 0) and can be deleted. */
  var LIFT_CAP = 20;
  function unclampLift(m) {
    if (!m || !m.dataset) return;
    for (var i = 0; i < m.children.length; i++)
      if (m.children[i].style) m.children[i].style.translate = '';
    delete m.dataset.wayDy;
  }
  function clampLift(m, edge) {
    if (!m || !edge || !edge.at || typeof THREE === 'undefined') return;
    var C = null; try { C = cam; } catch (e) {}
    var H = window.innerHeight || 0;
    if (!C || !H) return;
    if (m.style.display === 'none') return;     // a hidden marker's rect is all zeroes
    var tri = m.firstChild; if (!tri || !tri.getBoundingClientRect) return;
    var v = new THREE.Vector3(edge.at[0], edge.at[1], edge.at[2]).project(C);
    if (v.z > 1) return;                       // seam behind the camera: no honest y
    var seamY = (-v.y * 0.5 + 0.5) * H;
    var prev = parseFloat(m.dataset.wayDy || '0') || 0;
    var top = tri.getBoundingClientRect().top - prev;
    var dy = Math.max(0, (seamY - top) - LIFT_CAP);
    if (Math.abs(dy - prev) <= 6) return;      // inside the bob: leave it alone
    m.dataset.wayDy = String(dy.toFixed(1));
    var s = dy ? '0 ' + dy.toFixed(1) + 'px' : '';
    for (var i = 0; i < m.children.length; i++)
      if (m.children[i].style) m.children[i].style.translate = s;
  }

  /* THE RIVAL ARROW — why the routed marker is not enough on its own (2026-08-05).
   *
   * `markersTick` draws ONE red triangle per live seam in the shot, and a camera-boundary
   * cut is UNLABELLED by construction (play3d labels portals only; a town of named
   * doorways is noise). So a shot with two seams shows two identical anonymous arrows,
   * and the hint dresses exactly one of them.
   *
   * MEASURED, `run-20260805-040031`: at `therise` the player stood on the north road
   * with the beat arrow captioned "The Waystone" drawn DOWN-screen (that camera looks
   * back south over the square) and the bare `therise>square` arrow drawn UP-screen at
   * ny 0.32. The agent aimed at ny 0.34 on 22 of its last 40 steps, crossed back into
   * `square`, correctly aimed north again, and re-crossed — 46 seam crossings between
   * two spawn points 5 m apart, `ch1.see.mochi` never firing in 147 steps. Its own words
   * at step 122: "a red marker pointing at a spot in the midground and another red marker
   * for 'The Waystone' lower down" — and it took the midground one. THE LABEL LOST TO
   * SCREEN POSITION, because both arrows claimed the same thing with the same glyph.
   *
   * So while a beat hint is live the OTHER markers are demoted: still drawn (a player
   * may always choose to leave), plainly secondary. Opacity and scale only — play3d
   * pools these nodes and rewrites `transform` and `display` per frame and nothing else,
   * which is the same contract the `scale = 1.3` above already relies on. Every node
   * touched is remembered so the demotion is exactly reversible; a marker that dies out
   * of the pool takes its inline style with it. */
  var dimmed = [];
  function dimRivals(keepId) {
    if (!HAS_DOM) return;
    undimRivals();
    var all = document.querySelectorAll('#exit-markers > div[data-edge]');
    for (var i = 0; i < all.length; i++) {
      var m = all[i];
      if (m.dataset.edge === keepId) continue;
      if (m.style.display === 'none') continue;         // not in this shot: nothing to demote
      m.style.opacity = '0.34';
      if (m.firstChild && m.firstChild.style) m.firstChild.style.scale = '0.78';
      dimmed.push(m);
    }
  }
  function undimRivals() {
    for (var i = 0; i < dimmed.length; i++) {
      var m = dimmed[i];
      m.style.opacity = '';
      if (m.firstChild && m.firstChild.style) m.firstChild.style.scale = '';
    }
    dimmed.length = 0;
  }
  // The edge ids carry '>', '@', ':' and '.' — all meaningful inside an attribute
  // selector. CSS.escape is the browser's own answer; the fallback is for a headless
  // context that lacks it.
  function cssEsc(s) {
    if (typeof CSS !== 'undefined' && CSS.escape) return CSS.escape(s);
    return String(s).replace(/["\\]/g, '\\$&');
  }

  function hintTick() {
    if (HINT_OFF || !DATA || OFF || !HAS_DOM) return;
    if (++hintTicks % 10) return;                 // ~6 Hz; a label is not frame-critical
    // a templated objective is re-read here, not on a timer of its own: the frame a
    // `seen.` flag flips, the name it guarded has to leave the banner. Re-render ONLY
    // when the expansion actually changed — innerHTML at 6 Hz is a repaint per tick.
    if (objective && objective.indexOf('{!') >= 0) {
      var xo = expandObjective(objective);
      if (xo !== lastObjDrawn) { lastObjDrawn = xo; setObjective(); }
    }
    var b = pendingBeat();
    var bc = beatCam(b);
    var r = b ? routeTo(b.scene || scene(), bc) : null;
    var want = (r && r.edge) ? r.edge.id : null;
    var name = b ? destName(b, bc) : null;
    if (!want || !name) { clearHint(); lastHint = null; return; }
    if (want !== hintEdge) clearHint();
    var m = document.querySelector('#exit-markers > div[data-edge="' + cssEsc(want) + '"]');
    if (!m) { hintEdge = null; lastHint = null; return; }   // not drawn: say nothing
    hintEdge = want;
    dimRivals(want);                                        // see dimRivals: the rival arrow
    var t = m.querySelector('.story-way');
    if (!t) {
      t = document.createElement('div'); t.className = 'story-way';
      /* THE OBJECTIVE BANNER, IN MINIATURE — same pill, same border, same amber
       * diamond. A player should read the label and the banner as ONE thing without
       * being told they are, and the pill is what makes it legible over a plate: the
       * first cut was a bare glow-shadowed caption and it sat on a dark cliff face.
       *
       * IT IS THIS SIZE FOR A REASON. That first cut shipped at 11 px, the portal
       * label's size, and the receipt run walked straight past it: at step 2 of
       * run-20260804-204212 the label was on screen, bottom-left, correct — and the
       * agent's own stated goal was still "climb the stairs UP to the head-gate
       * winches", after which it spent five legs stuck on the platform above. This
       * game is played on a TV (memory: controller-agnostic, everything renders on
       * the TV), where 11 px is not a label, it is a texture. */
      t.style.cssText = 'margin-top:4px;font:700 13px/1.2 ui-monospace,Menlo,monospace;' +
        'letter-spacing:.02em;color:#e7ddd0;white-space:nowrap;' +
        'background:#000c;border:1px solid #3a2c20;border-radius:7px;padding:3px 9px;' +
        'text-shadow:0 1px 2px #000';
      m.appendChild(t);
      m.style.zIndex = '1';                       // over its neighbours when they crowd
      // and the arrow itself a size up, so the one that matters reads at a glance
      if (m.firstChild && m.firstChild.style) m.firstChild.style.scale = '1.3';
    }
    // Compared on a data-attribute, NOT on innerHTML: the browser re-serialises what
    // it parsed, so an innerHTML round-trip can never be relied on to equal what was
    // written, and this would repaint at 6 Hz forever.
    if (t.dataset.dest !== name) {
      t.dataset.dest = name;
      t.innerHTML = '<b style="color:#e9a24b">\u25C6</b> ' + String(name).replace(/[<>]/g, '');
    }
    /* AND IT IS CLAMPED INTO THE FRAME (2026-08-05). The pill is centred on an arrow
     * markersTick puts wherever the seam projects, and a seam near the edge of a shot
     * put the label half outside it: run-20260805-003146 step 3 drew "Lock Five" at
     * x 38 px of 1400, its diamond and its left half off the picture entirely, and the
     * agent took the bare triangle on the other side of the frame instead. A LABEL
     * HALF OFF THE FRAME IS NOT A LABEL. Only the caption slides \u2014 the arrow keeps
     * pointing at the seam, because the arrow is the claim and the pill is the caption.
     * Measured against the untranslated box so the nudge cannot accumulate. */
    var prev = parseFloat(t.dataset.dx || '0') || 0;
    var box = t.getBoundingClientRect();
    if (box.width) {
      var W = window.innerWidth || (document.documentElement || {}).clientWidth || 0;
      var pad = 8, dx = 0, L = box.left - prev, R = box.right - prev;
      if (L < pad) dx = pad - L;
      else if (W && R > W - pad) dx = (W - pad) - R;
      if (Math.abs(dx - prev) > 0.5) {
        t.dataset.dx = String(dx);
        t.style.transform = dx ? 'translateX(' + dx.toFixed(1) + 'px)' : '';
      }
    }
    clampLift(m, r.edge);       // see clampLift: the arrow was drawn 97 px off its ground
    lastHint = { beat: b.id, edge: want, dest: name, hops: r.hops };
  }

  function tick() {
    hintTick();                 // BEFORE the modal guards: a marker is not a modal
    if (busy || !DATA || OFF) return;
    // A beat must never open on top of another modal — the shop, the pause menu,
    // the dialogue window or a transition all hold UILOCK, and all four of them
    // own the screen while they do.
    if (window.UILOCK && UILOCK.active()) return;
    // NOR INSIDE A TRANSITION. UILOCK is not enough: transitionTo() raises the veil
    // and sets SGbusy BEFORE sgSwap takes UILOCK('transition'), so there is a
    // fade-length window — 350 ms, ~20 physics ticks — in which the scene is on its
    // way out and nothing holds the modal lock. A beat opening there would play
    // over a scene the player is leaving, and would still hold UILOCK when the new
    // one arrives. (Plan §6: "a beat never runs while SGbusy or UILOCK.active()".)
    if (window.SIM && SIM.busy && SIM.busy()) return;
    if (++ticks % 6) return;                   // beats are not frame-critical
    /* THE SHOT IS HALF OF `at`, AND IT MOVES WITHOUT A SCENE CHANGE. A cinematic
     * town cuts between shots as the player walks, and until this ran, `at.cam`
     * held whichever shot the scene happened to arrive on — measured as `gate`
     * while the body stood in `lockhead`. IN MEMORY ONLY, deliberately: a manual
     * SAVE serialises GS.state and now writes the shot the player is actually
     * looking at, while a shot cut adds no localStorage write of its own. The
     * autosave on the next scene change or beat carries it to disk. */
    if (lastShot !== shot()) { lastShot = shot(); recordAt(); }
    var bs = DATA.beats || [];
    for (var i = 0; i < bs.length; i++) if (eligible(bs[i])) { runBeat(bs[i]); return; }
  }

  // ------------------------------------------------------------ where we are --
  // `at` is written on every scene change and after every beat, and it is the ONLY
  // resume authority (docs/plans/end-to-end-wiring.md §5). Everything it needs is
  // already exposed by play3d: SIM.scene(), SIM.cine().shot, SIM.pos(), ORBIT.yaw.
  /* HAS THE SCENE ACTUALLY ARRIVED?
   *
   * `arm()` runs the moment this module loads, which on a cold boot is BEFORE
   * play3d has read sx/sy/sz off the URL and placed the body, and before a
   * cinematic scene has chosen its shot. Measured 2026-08-04 in `del-cine`, booted
   * at the ch2.jam checkpoint with the beat ledger non-empty:
   *
   *   t=0s     body [0,2,0]         shot null      at.pos [0,2,0]  cam null
   *   t=3s     body [78.93,...]     shot lockhead  at.pos [0,2,0]  cam null
   *   t=20s    body [78.93,...]     shot lockhead  at.pos [0,2,0]  cam null
   *   after one 'eb-scene'          shot lockhead  at.pos [78.93,...] cam lockhead
   *
   * `at` IS THE RESUME AUTHORITY, and the autosave was committing [0,2,0] to disk
   * on the first frame of every load. Nothing corrected it until the next scene
   * change or beat — so a player who loaded a save, walked around one scene and
   * closed the tab came back somewhere else, AND a save that was correct on disk
   * was overwritten with the placeholder by the act of loading it.
   *
   * The test is the scene's own: a pre-rendered scene that has not chosen a shot
   * has not arrived. A real-time scene has no cine(), so it is judged on position
   * alone, which is exactly the behaviour it had before. Recording nothing leaves
   * the previous `at` standing, which is the right answer — the old one is at worst
   * stale, and the placeholder is wrong. */
  function arrived() {
    try {
      if (!window.SIM || !SIM.pos) return false;
      var p = SIM.pos(); if (!p || !isFinite(p.x)) return false;
      var c = SIM.cine ? SIM.cine() : null;
      if (c && !c.shot) return false;
      return true;
    } catch (e) { return false; }
  }

  function recordAt() {
    var g = G(); if (!g || !g.setAt) return null;
    if (!arrived()) return null;
    var p = window.SIM && SIM.pos ? SIM.pos() : null;
    return GS.setAt({
      scene: scene(), cam: shot(),
      pos: p ? [+p.x.toFixed(3), +p.y.toFixed(3), +p.z.toFixed(3)] : null,
      yaw: window.ORBIT ? +Number(window.ORBIT.yaw).toFixed(4) : null,
    });
  }

  // -------------------------------------------------------------- self-arming --
  function arm(detail) {
    return load().then(function (d) {
      if (!d) return null;
      var sc = scene();
      if (sc !== lastScene) { lastScene = sc; }
      // The objective survives a door: it is a property of the chapter, not the room.
      if (objective) setObjective(objective);
      recordAt();
      /* AND AGAIN ONCE THE SCENE HAS ARRIVED. recordAt() refuses to write a
       * placeholder (see arrived()), so on a cold boot the call above does nothing
       * — and nothing else would write `at` until the next scene change. This poll
       * is the missing edge: it fires ONCE, as soon as the body is placed and the
       * shot is chosen, and gives up after ~15 s rather than spinning forever.
       * Idempotent by construction: each arm() owns its own timer and the first
       * successful record clears it. */
      (function pollArrival(n) {
        if (arrived()) {
          if (recordAt() && G() && GS.autosave) { var L2 = ledger(); if (L2 && Object.keys(L2).length) GS.autosave(); }
          return;
        }
        if (n > 60) return;
        setTimeout(function () { pollArrival(n + 1); }, 250);
      })(0);
      // AUTOSAVE ON EVERY 'eb-scene', BUT ONLY ONCE THERE IS A PLAYTHROUGH TO LOSE.
      // play3d.html's own module contract says a door does NO save and NO load —
      // "GS is page state and persists untouched across a door" — and
      // tools/transition_test.mjs booby-traps GS.save to prove it, because the old
      // full-reload path re-created GS from localStorage at every doorway and a run
      // with no save silently reset. That contract is about a SCENE JUMP, which is
      // what a developer walking the scene cards is doing. The moment a story beat
      // has actually happened, the session stops being a scene jump and becomes a
      // game, and losing the walk into Dellhollow because the tab was closed is the
      // worse failure. `beats` is empty for the whole of a dev session and non-empty
      // for the whole of a playthrough, so it is the honest switch.
      if (G() && GS.autosave) { var L = ledger(); if (L && Object.keys(L).length) GS.autosave(); }
      return sc;
    });
  }

  window.Story = {
    tick: tick,
    ready: null,
    reload: function () { DATA = null; FAILED = false; return load(); },
    objective: function (t) { return t === undefined ? objective : setObjective(t); },
    // TEST/DEBUG surface — enough for a headless assert without reading the DOM.
    debug: function () {
      var L = ledger() || {};
      return { loaded: !!DATA, busy: busy, objective: objective,
               scene: scene(), shot: shot(),
               beats: DATA ? (DATA.beats || []).length : 0,
               done: Object.keys(L), fired: log.map(function (r) { return r.id; }),
               at: G() ? GS.state.at : null,
               eligible: DATA ? (DATA.beats || []).filter(eligible).map(function (b) { return b.id; }) : [] };
    },
    // TEST-ONLY: run a beat by id regardless of its trigger, so a gauntlet can
    // drive the chapter without walking every metre of two towns. It still runs
    // the REAL steps through the REAL modules.
    force: function (id) {
      if (!DATA) return Promise.resolve(null);
      var b = (DATA.beats || []).find(function (x) { return x.id === id; });
      if (!b) return Promise.resolve({ error: 'no beat ' + id });
      return runBeat(b);
    },
    recordAt: recordAt,
    /* THE WAYFINDING INSTRUMENT. What the hint currently says, plus the two answers
     * it is derived from, so a harness can assert "the way to the objective is
     * named" without reading a pixel — and so a null can be told apart from a lie:
     * `beat` null means the chapter is waiting on nothing here, `edge` null with a
     * beat means no route (or you have arrived), and `shown` false means the route
     * exists but its marker is not on screen from this spot. */
    wayhint: function () {
      var b = pendingBeat();
      var bc = beatCam(b);
      var r = b ? routeTo(b.scene || scene(), bc) : null;
      var e = r && r.edge ? r.edge.id : null;
      var m = (e && HAS_DOM) ? document.querySelector('#exit-markers > div[data-edge="' + cssEsc(e) + '"]') : null;
      return {
        off: HINT_OFF, scene: scene(), shot: shot(),
        beat: b ? b.id : null, wantScene: b ? (b.scene || null) : null,
        // wantCam is what the ROUTE used: the beat's own, or the band that owns its `at`.
        wantCam: bc || null, camAuthored: b ? (b.cam || null) : null,
        edge: e, hops: r ? r.hops : null, dest: b ? destName(b, bc) : null,
        shown: !!(m && m.style.display !== 'none'),
        labelled: !!(m && m.querySelector('.story-way')),
        drawn: hintEdge, last: lastHint,
      };
    },
  };

  if (typeof window !== 'undefined' && window.addEventListener)
    window.addEventListener('eb-scene', function (ev) {
      try { arm(ev && ev.detail); } catch (e) { console.error('[Story] eb-scene', e); }
    });

  // load-time arming, after GS so the flag store and the beat ledger exist
  Story.ready = (window.GS && window.GS.ready && window.GS.ready.then)
    ? window.GS.ready.then(function () { return arm(null); })
    : load();
})();
