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
  var lastScene = null;
  var log = [];                     // {id, at} — what fired this session, for the harness

  var HAS_DOM = typeof document !== 'undefined' && !!document.createElement;

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
  function setObjective(txt) {
    objective = txt || null;
    style(); var e = el('story-obj'); if (!e) return objective;
    if (!objective) { e.style.opacity = '0'; return null; }
    e.innerHTML = '<b>&#9670;</b> ' + String(objective).replace(/[<>]/g, '');
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

  function tick() {
    if (busy || !DATA) return;
    // A beat must never open on top of another modal — the shop, the pause menu,
    // the dialogue window or a transition all hold UILOCK, and all four of them
    // own the screen while they do.
    if (window.UILOCK && UILOCK.active()) return;
    if (++ticks % 6) return;                   // beats are not frame-critical
    var bs = DATA.beats || [];
    for (var i = 0; i < bs.length; i++) if (eligible(bs[i])) { runBeat(bs[i]); return; }
  }

  // ------------------------------------------------------------ where we are --
  // `at` is written on every scene change and after every beat, and it is the ONLY
  // resume authority (docs/plans/end-to-end-wiring.md §5). Everything it needs is
  // already exposed by play3d: SIM.scene(), SIM.cine().shot, SIM.pos(), ORBIT.yaw.
  function recordAt() {
    var g = G(); if (!g || !g.setAt) return null;
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
      if (G() && GS.autosave) GS.autosave();     // autosave on every 'eb-scene'
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
