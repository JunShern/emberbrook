// ui_kit.js — window.EBUI: the shared keyboard-UI kit for the game's overlays
// (shop.js, menu.js today; a battle menu tomorrow). ECONOMY-agent owned.
//
// WHY THIS FILE EXISTS: shop and menu are two keyboard-driven panels that must
// look identical, key identically, and pause the overworld identically. Written
// twice they drift. Everything visual or input-related that they share lives
// here and nowhere else; the modules themselves contain only their own content.
//
// THREE THINGS IT PROVIDES
//   1. PALETTE + PANEL — one injected stylesheet and one panel factory, matching
//      play3d's own HUD/prompt idiom (warm off-white on near-black, #3a2c20
//      borders, #e9a24b accent). Panel chrome is system-ui; every number is
//      monospace so columns of prices and stats line up.
//   2. THE INPUT LOCK — "pause the overworld", via the engine's own contract:
//        - window.UILOCK.lock(name) / .unlock(name) (play3d, coordinator-owned).
//          While ANY lock is held, phys() freezes, held keys are zeroed, and the
//          scene-graph E handler and the debug keys (g 2 [ ] m z) ignore input.
//          THAT is what pauses the world — a stated contract, not a trick.
//        - a CAPTURE-phase keydown listener on window is still ours, but now only
//          to drive our own cursor and to preventDefault browser keys (space
//          scroll, tab focus). It also stops propagation so no other page
//          listener double-handles a panel keystroke.
//        - FALLBACK for a page with no UILOCK (older bundle, isolated test):
//          SIM.keys({}) zeroing, which is what pausing looked like before the
//          contract existed. Never needed when UILOCK is present.
//   3. PROMPT BANNERS — sgPrompt's recipe, reused so a module's E-prompt is
//      indistinguishable from a door's. Format/key/vTol come from the scene
//      graph's own defaults via SIM.graph(), never from constants here.
//
// KEYBOARD-ONLY BY CONTRACT. No mouse handler anywhere in this file: this is a
// couch co-op game and both seats are keyboards. Arrows AND WASD both drive the
// cursor so either seat can work a menu.
//
// Loads DOM-free: nothing here touches `document` at load time, so Node tests
// (tools/economy_test.mjs) can import the modules that depend on it.
(function () {
  'use strict';
  const HAS_DOM = typeof document !== 'undefined' && !!document.createElement;

  // ---- key normalisation ---------------------------------------------------
  // One table, so every panel in the game answers to the same keys. Both
  // arrow-cluster and WASD map to the same logical actions (couch seating).
  const KEYMAP = {
    arrowup: 'up', w: 'up', arrowdown: 'down', s: 'down',
    arrowleft: 'left', a: 'left', arrowright: 'right', d: 'right',
    enter: 'confirm', e: 'confirm', ' ': 'confirm',
    escape: 'cancel', q: 'cancel', backspace: 'cancel',
    tab: 'next', pageup: 'pageup', pagedown: 'pagedown',
  };
  const REPEATABLE = { up: 1, down: 1, left: 1, right: 1, pageup: 1, pagedown: 1 };
  function act(ev) { return KEYMAP[String(ev.key).toLowerCase()] || null; }

  // ---- style ---------------------------------------------------------------
  // Injected once. THE WHOLE GAME'S UI PALETTE AND WINDOW GRAMMAR LIVE HERE, as
  // CSS custom properties on :root plus one window primitive (.eb-win), so shop,
  // pause menu and battle screen all inherit the same material and a re-tint is
  // a single edit.
  //
  // DESIGN LANGUAGE — "FF window grammar, CLASSIC FF BLUE" (v2, user-ratified):
  //   FF6/FF7's signature is that EVERYTHING is a bordered window: a deep
  //   navy-to-blue VERTICAL GRADIENT fill, a crisp 2-tone SILVER bevel (bright
  //   top-left / steel bottom-right), gently rounded corners, consistent inner
  //   padding, WHITE text, and a cursor that points at the live row.
  //   v1 tried the same grammar in Emberbrook's lantern materials (timber and
  //   brass); the user rejected it as plain and too yellow. The grammar and the
  //   architecture survive untouched — only these custom properties changed.
  //   THE AMBER SURVIVES ONLY AS HIGHLIGHT: the cursor glyph, the selected row,
  //   window titles, gold and HP numerals. Nothing structural is warm any more.
  //   The bevel is drawn with two inset box-shadows rather than a border image,
  //   so it costs nothing and scales with the radius.
  //
  //   TRANSLUCENCY IS LOAD-BEARING, not decoration: the pause menu and the shop
  //   are OVERLAYS over the paused world (see .ebui-veil), so the window fill is
  //   ~90% opaque and the scene reads faintly through it, FF7-style.
  const CSS = `
:root{
  /* ink — white/silver on blue */
  --eb-ink:#f3f5ff; --eb-ink-dim:#c2caee; --eb-ink-faint:#8e97c6;
  /* the surviving accent: highlight only */
  --eb-amber:#f0b45c; --eb-amber-hi:#ffdca6; --eb-amber-dim:#b1803a;
  /* THE WINDOW: deep navy at the top falling to royal blue at the foot */
  --eb-win:linear-gradient(180deg,#0e1038db 0%,#191a63e0 54%,#2a2b8cdb 100%);
  --eb-win-head:linear-gradient(180deg,#0a0b2ae8 0%,#15165ae8 100%);
  --eb-win-solid:linear-gradient(180deg,#0e1038 0%,#2a2b8c 100%);
  /* SILVER bevel, 2-tone + the hairline that seats a window on the backdrop */
  --eb-bevel-lt:#eef1ff; --eb-bevel-dk:#7b84c0; --eb-edge:#04051a;
  --eb-rule:#4a53a8;
  /* the inner surfaces (cards, chips, sub-panels) derive from the same blue, so
     nothing anywhere hand-mixes a colour and the next re-tint is still one edit */
  --eb-inset-lt:#ffffff3d; --eb-inset-dk:#00021e8c;
  --eb-card:linear-gradient(180deg,#ffffff14 0%,#00042426 100%);
  --eb-card-cur:linear-gradient(180deg,#ffffff26 0%,#0b0e5433 100%);
  --eb-chip:linear-gradient(180deg,#2a2c86 0%,#141560 100%);
  /* semantics */
  --eb-good:#8fdc8a; --eb-bad:#ff8f7a;
  --eb-hp:linear-gradient(180deg,#ffdca6 0%,#f0b45c 55%,#bd8330 100%);
  --eb-hp-low:linear-gradient(180deg,#ffb4a0 0%,#e8624a 55%,#a83426 100%);
  --eb-xp:linear-gradient(180deg,#eef4ff 0%,#a8c6f2 55%,#6b8ed4 100%);
  --eb-track:#05061f;
  /* type */
  --eb-face:system-ui,-apple-system,"Segoe UI",sans-serif;
  --eb-mono:ui-monospace,Menlo,Consolas,monospace;
  /* a faint tooth, so the blue is not a flat CSS gradient */
  --eb-grain:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='140' height='140'><filter id='g'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/></filter><rect width='140' height='140' filter='url(%23g)'/></svg>");
}

/* ===== THE WINDOW PRIMITIVE ==============================================
   Every panel in the game is one of these. Bevel = two inset shadows; the
   inner ring darkens the fill just inside the silver so the border reads as
   a raised frame rather than a stroke. */
.eb-win{position:relative;border-radius:8px;border:1px solid var(--eb-edge);
  background:var(--eb-win);color:var(--eb-ink);
  box-shadow:inset 2px 2px 0 0 var(--eb-bevel-lt),
             inset -2px -2px 0 0 var(--eb-bevel-dk),
             inset 0 0 0 3px #00021e3d,
             0 10px 30px #000a;}
.eb-win::before{content:'';position:absolute;inset:3px;border-radius:5px;
  pointer-events:none;background-image:var(--eb-grain);background-size:140px 140px;
  opacity:.045;mix-blend-mode:overlay}
.eb-win>*{position:relative;z-index:1}
.eb-win.flat{box-shadow:inset 2px 2px 0 0 var(--eb-bevel-lt),
             inset -2px -2px 0 0 var(--eb-bevel-dk),inset 0 0 0 3px #00021e3d}
.eb-wtitle{display:block;padding:6px 12px 5px;font:600 12px/1.2 var(--eb-face);
  letter-spacing:.13em;text-transform:uppercase;color:var(--eb-amber);
  background:var(--eb-win-head);border-bottom:1px solid var(--eb-rule);
  border-radius:6px 6px 0 0;text-shadow:0 1px 2px #000}
.eb-wbody{padding:9px 12px}

/* ===== THE CURSOR ========================================================
   FF's pointing glyph, drawn in CSS (no font dependency): a shafted arrow in
   flame amber that bobs one pixel toward the row it is pointing at. The bob is
   decoration and dies under prefers-reduced-motion; the glyph itself never
   does, because WHICH ROW IS SELECTED is information. */
.eb-cur{flex:0 0 1.05em;display:inline-block;width:1.05em;height:1em;
  vertical-align:-.12em}
.eb-cur.on{background:linear-gradient(160deg,var(--eb-amber-hi),var(--eb-amber) 55%,var(--eb-amber-dim));
  clip-path:polygon(0 30%,45% 30%,45% 8%,100% 50%,45% 92%,45% 70%,0 70%);
  filter:drop-shadow(0 1px 1px #000a);animation:eb-bob 900ms steps(2,jump-none) infinite}
@keyframes eb-bob{0%,100%{transform:translateX(0)}50%{transform:translateX(2px)}}

/* ===== GAUGES ============================================================ */
.eb-gauge{display:flex;align-items:center;gap:7px;font-family:var(--eb-mono);
  font-size:11.5px;font-variant-numeric:tabular-nums}
.eb-gauge .lb{flex:0 0 auto;color:var(--eb-ink-faint);letter-spacing:.1em;
  font-size:10px;font-weight:600}
.eb-gauge .tk{flex:1 1 auto;min-width:24px;height:8px;border-radius:4px;
  background:var(--eb-track);overflow:hidden;
  box-shadow:inset 0 1px 2px #000c,0 1px 0 var(--eb-inset-lt)}
.eb-gauge .tk>i{display:block;height:100%;background:var(--eb-hp);
  border-radius:4px;transition:width 220ms linear}
.eb-gauge.low .tk>i{background:var(--eb-hp-low)}
.eb-gauge.xp .tk>i{background:var(--eb-xp)}
.eb-gauge .nm{flex:0 0 auto;color:var(--eb-ink);font-size:11.5px}
.eb-gauge .nm b{color:var(--eb-amber-hi);font-weight:600}
.eb-none{color:var(--eb-ink-faint)}

/* ===== PORTRAITS =========================================================
   The busts are 512x512 colour-pencil plates on warm paper. Small sizes crop
   to the face; the large menu bust shows the whole plate in a brass frame. */
.eb-port{flex:0 0 auto;border-radius:6px;border:1px solid var(--eb-edge);
  background-color:#0b0d33;background-repeat:no-repeat;
  background-size:190%;background-position:50% 14%;
  box-shadow:inset 1px 1px 0 var(--eb-bevel-lt),inset -1px -1px 0 var(--eb-bevel-dk),
             0 2px 6px #0008}
.eb-port.big{background-size:104%;background-position:50% 22%;border-radius:8px;
  box-shadow:inset 2px 2px 0 var(--eb-bevel-lt),inset -2px -2px 0 var(--eb-bevel-dk),
             0 10px 26px #000b}
.eb-port.miss{background-image:linear-gradient(160deg,#252a72,#0d0f3a)}

/* ===== LEGACY EBUI SURFACES, RESTYLED IN THE NEW GRAMMAR ================= */
/* THE SCRIM. A pause menu is an OVERLAY: the engine keeps rendering the frozen
   world under UILOCK, and you are meant to see where you are while you read it.
   So this is a ~30% wash, not a curtain — enough to sit the windows off the
   scene and take the glare out of a bright render, never enough to hide it.
   The 2px blur is a depth cue, not a darkener; it is what lets a dark navy
   window read against a dark town render without dropping the scrim lower. */
.ebui-veil{position:fixed;inset:0;z-index:20;background:#060a1c4f;
  backdrop-filter:blur(2px) saturate(.92);-webkit-backdrop-filter:blur(2px) saturate(.92);
  display:flex;align-items:center;justify-content:center;
  opacity:0;transition:opacity 140ms linear;pointer-events:none}
.ebui-veil.on{opacity:1}
.ebui-panel{min-width:min(660px,88vw);max-width:min(920px,93vw);max-height:88vh;
  display:flex;flex-direction:column;overflow:hidden;
  color:var(--eb-ink);border-radius:9px;border:1px solid var(--eb-edge);
  background:var(--eb-win);
  box-shadow:inset 2px 2px 0 0 var(--eb-bevel-lt),
             inset -2px -2px 0 0 var(--eb-bevel-dk),
             inset 0 0 0 3px #00021e3d,0 14px 44px #000c;
  font:14px/1.5 var(--eb-face);text-shadow:0 1px 2px #0009}
.ebui-panel::before{content:'';position:absolute;inset:3px;border-radius:6px;
  pointer-events:none;background-image:var(--eb-grain);background-size:140px 140px;
  opacity:.055;mix-blend-mode:overlay}
.ebui-head{position:relative;z-index:1;display:flex;align-items:baseline;gap:12px;
  padding:9px 15px;border-bottom:1px solid var(--eb-rule);background:var(--eb-win-head);
  border-radius:7px 7px 0 0}
.ebui-title{font-weight:600;letter-spacing:.12em;text-transform:uppercase;
  font-size:13px;color:var(--eb-amber)}
.ebui-sub{color:var(--eb-ink-dim);font-size:12px;letter-spacing:.02em}
.ebui-gold{margin-left:auto;font-family:var(--eb-mono);color:var(--eb-amber-hi);
  font-variant-numeric:tabular-nums}
.ebui-body{position:relative;z-index:1;padding:11px 15px;overflow:auto}
.ebui-foot{position:relative;z-index:1;padding:7px 15px;border-top:1px solid var(--eb-rule);
  background:var(--eb-win-head);color:var(--eb-ink-faint);font-size:11.5px;
  font-family:var(--eb-mono);border-radius:0 0 7px 7px}
.ebui-foot b{color:var(--eb-ink-dim);font-weight:600}

/* ===== THE FLOATING LAYOUTS ==============================================
   THE MENU AND THE SHOP ARE OVERLAYS. The engine already renders the frozen
   world under UILOCK; these two layouts make the panel honour that, by having
   the outer frame step back to NOTHING so what floats over the scene is a set
   of separate windows with the scene showing in the gaps — FF9's pause screen,
   not a dialog box. Head and foot become free-standing windows of their own.
     full  — the pause menu's screen-wide grid (nav / plate / help / gold)
     float — a content-sized cluster (the shop)
   BOTH ARE HEIGHT:AUTO. A fixed 660px box would letterbox its own content and
   paint blue over scene nobody asked it to cover; sized to content, the windows
   only ever occupy what they need and the town is visible around them. */
.ebui-panel.full,.ebui-panel.float{max-width:none;min-width:0;height:auto;
  background:none;border:none;box-shadow:none;gap:9px;overflow:visible}
.ebui-panel.full::before,.ebui-panel.float::before{display:none}
.ebui-panel.full{width:min(1140px,92vw);max-height:94vh}
.ebui-panel.float{width:min(800px,92vw);max-height:92vh}
.ebui-panel.full .ebui-head,.ebui-panel.full .ebui-foot,
.ebui-panel.float .ebui-head,.ebui-panel.float .ebui-foot{
  border:1px solid var(--eb-edge);border-radius:8px;background:var(--eb-win-head);
  box-shadow:inset 2px 2px 0 0 var(--eb-bevel-lt),inset -2px -2px 0 0 var(--eb-bevel-dk),
             inset 0 0 0 3px #00021e3d,0 10px 30px #000a}
.ebui-panel.full .ebui-body,.ebui-panel.float .ebui-body{
  padding:0;flex:0 1 auto;min-height:0;overflow:visible;background:none}

.ebui-tabs{display:flex;gap:7px;padding:0 0 9px}
.ebui-tab{padding:3px 15px;border-radius:5px;color:var(--eb-ink-dim);
  background:var(--eb-chip);font-size:12px;letter-spacing:.1em;
  font-weight:600;text-transform:uppercase;border:1px solid var(--eb-edge);
  box-shadow:inset 1px 1px 0 var(--eb-bevel-lt),inset -1px -1px 0 var(--eb-bevel-dk)}
.ebui-tab.on{color:#241704;background:linear-gradient(180deg,var(--eb-amber-hi),var(--eb-amber) 60%,var(--eb-amber-dim));
  text-shadow:none;box-shadow:inset 1px 1px 0 #fff0d4,inset -1px -1px 0 #7a5418}
.ebui-row{display:flex;gap:9px;align-items:baseline;padding:3px 8px;
  border-radius:5px;border:1px solid transparent}
.ebui-row.cur{background:linear-gradient(90deg,#f0b45c3d,#f0b45c14 70%,#f0b45c00);
  border-color:#f0b45c5c;box-shadow:inset 0 0 0 1px #ffdca626}
.ebui-row.cur .k{color:var(--eb-amber-hi)}
.ebui-row.dim{color:var(--eb-ink-faint)}
.ebui-row .k{flex:1 1 auto;min-width:0;overflow:hidden;text-overflow:ellipsis;
  white-space:nowrap}
.ebui-row .n{font-family:var(--eb-mono);text-align:right;
  flex:0 0 auto;font-variant-numeric:tabular-nums}
.ebui-cur{color:var(--eb-amber);flex:0 0 1em}
.ebui-note{margin-top:9px;padding-top:8px;border-top:1px solid var(--eb-rule);
  color:var(--eb-ink-dim);font-size:13px;min-height:2.6em}
.ebui-msg{color:var(--eb-amber);font-family:var(--eb-mono);font-size:12px}
.ebui-msg.bad{color:var(--eb-bad)}
.ebui-cols{display:grid;gap:14px}
.ebui-card{border-radius:7px;padding:9px 11px;background:var(--eb-card);
  box-shadow:inset 1px 1px 0 var(--eb-inset-lt),inset -1px -1px 0 var(--eb-inset-dk)}
.ebui-stat{display:flex;gap:8px;font-family:var(--eb-mono);font-size:12.5px}
.ebui-stat .l{color:var(--eb-ink-faint);flex:0 0 3.2em;letter-spacing:.08em}
.ebui-bar{height:8px;border-radius:4px;background:var(--eb-track);overflow:hidden;
  margin:3px 0 6px;box-shadow:inset 0 1px 2px #000c,0 1px 0 var(--eb-inset-lt)}
.ebui-bar>i{display:block;height:100%;background:var(--eb-hp);border-radius:4px}
.ebui-up{color:var(--eb-good)}.ebui-dn{color:var(--eb-bad)}
.ebui-shake{animation:ebui-sh 180ms linear}
@keyframes ebui-sh{0%,100%{transform:translateX(0)}25%{transform:translateX(-4px)}
  75%{transform:translateX(4px)}}
.ebui-banner{position:absolute;left:50%;bottom:8%;transform:translateX(-50%);
  z-index:3;color:var(--eb-ink);font:14px var(--eb-mono);
  background:var(--eb-win);border:1px solid var(--eb-edge);border-radius:8px;
  box-shadow:inset 1px 1px 0 var(--eb-bevel-lt),inset -1px -1px 0 var(--eb-bevel-dk),
             0 6px 18px #000a;
  padding:7px 14px;text-shadow:0 1px 2px #000;pointer-events:none;white-space:nowrap;
  opacity:0;transition:opacity 120ms linear}

/* Decoration stops; information never does. */
@media (prefers-reduced-motion:reduce){
  .eb-cur.on{animation:none}
  .ebui-shake{animation:none}
}`;
  let styled = false;
  function style() {
    if (styled || !HAS_DOM) return;
    styled = true;
    const s = document.createElement('style'); s.id = 'ebui-style';
    s.textContent = CSS; document.head.appendChild(s);
  }

  // ---- scene-graph defaults ------------------------------------------------
  // The prompt key, format and vertical tolerance are the SCENE GRAPH'S, read
  // live from SIM.graph().defaults — so a module's prompt cannot drift from a
  // door's, and changing the graph's promptFmt changes ours too.
  function sgDefaults() {
    try { const g = window.SIM && window.SIM.graph && window.SIM.graph(); if (g && g.defaults) return g.defaults; }
    catch (e) { /* SIM may not be up yet */ }
    return {};
  }
  const SGFALLBACK = { key: 'e', promptFmt: '{label}? [{key}]', vTol: 2, doorRadius: 1.8 };
  function sgDef(k) { const d = sgDefaults(); return d[k] !== undefined ? d[k] : SGFALLBACK[k]; }

  // ---- the input lock ------------------------------------------------------
  const stack = [];             // open panels; only the top one gets keys
  const globals = {};           // key -> handler, live ONLY when no panel is open
  let wired = false;

  // UILOCK is the engine-side half of the pause contract. Locks are NAMED, so
  // two panels (a shop and a battle screen) cannot unlock each other.
  function lock(name, on) {
    const L = window.UILOCK;
    if (L && L.lock) { try { on ? L.lock(name) : L.unlock(name); } catch (e) { } return; }
    // no contract on this page: fall back to zeroing the key map
    try { if (window.SIM && window.SIM.keys) window.SIM.keys({}); } catch (e) { }
  }
  function locked() {
    try { if (window.UILOCK && window.UILOCK.active()) return true; } catch (e) { }
    return stack.length > 0;
  }

  function onKeyDown(ev) {
    if (stack.length) {
      // Ours to handle: stop other page listeners double-handling, and kill the
      // browser defaults (space scrolls, tab moves focus). The WORLD is already
      // frozen by UILOCK — this is not what pauses it.
      ev.stopImmediatePropagation(); ev.preventDefault();
      const a = act(ev);
      if (!a) return;
      if (ev.repeat && !REPEATABLE[a]) return;
      const top = stack[stack.length - 1];
      try { top.onKey(a, ev); } catch (e) { console.error('[EBUI] key handler', e); }
      return;
    }
    if (locked()) return;         // somebody else's modal (e.g. a battle) owns input
    const g = globals[String(ev.key).toLowerCase()];
    if (!g || ev.repeat) return;
    let consumed = false;
    try { consumed = g(ev) !== false; } catch (e) { console.error('[EBUI] global key', e); }
    if (consumed) { ev.stopImmediatePropagation(); ev.preventDefault(); }
  }
  function swallow(ev) { if (stack.length) { ev.stopImmediatePropagation(); ev.preventDefault(); } }

  function wire() {
    if (wired || !HAS_DOM) return; wired = true;
    // CAPTURE phase on window: runs before play3d's bubble-phase listeners.
    window.addEventListener('keydown', onKeyDown, true);
    window.addEventListener('keypress', swallow, true);
    // keyup is deliberately NOT swallowed: it only ever CLEARS a key in play3d's
    // map, which is exactly what we want a panel to allow through.
  }

  // ---- panel ---------------------------------------------------------------
  // A panel is: a veil, a frame with head/body/foot, an onKey handler, and a
  // render function the owner calls whenever its state changes. The panel never
  // holds game state — it re-derives everything from GS on each render, and
  // subscribes to GS 'change' so an external mutation repaints it.
  function panel(spec) {
    style(); wire();
    if (!HAS_DOM) return null;
    const lockName = spec.name || 'ebui';
    const host = document.getElementById('s') || document.body;
    const veil = document.createElement('div'); veil.className = 'ebui-veil';
    const frame = document.createElement('div');
    // 'dialog' (default) = one centred opaque window. The two FF9 shapes both
    // step the outer frame back so the head, the foot and the body's own
    // windows float SEPARATELY over the paused scene:
    //   'full'  screen-wide grid (the pause menu)
    //   'float' content-sized cluster (the shop)
    const LAYOUTS = { full: ' full', float: ' float' };
    frame.className = 'ebui-panel' + (LAYOUTS[spec.layout] || '');
    frame.innerHTML = '<div class="ebui-head"><span class="ebui-title"></span>' +
      '<span class="ebui-sub"></span><span class="ebui-gold"></span></div>' +
      '<div class="ebui-body"></div><div class="ebui-foot"></div>';
    veil.appendChild(frame); host.appendChild(veil);
    const q = c => frame.querySelector('.ebui-' + c);

    const P = {
      el: veil, frame, body: q('body'),
      onKey: spec.onKey || function () { },
      set(o) {
        if (o.title !== undefined) q('title').textContent = o.title;
        if (o.sub !== undefined) q('sub').textContent = o.sub;
        if (o.gold !== undefined) q('gold').textContent = o.gold === null ? '' : o.gold + ' g';
        if (o.foot !== undefined) q('foot').innerHTML = o.foot;
        if (o.html !== undefined) P.body.innerHTML = o.html;
      },
      shake() { frame.classList.remove('ebui-shake'); void frame.offsetWidth; frame.classList.add('ebui-shake'); },
      close() {
        const i = stack.indexOf(P); if (i < 0) return false;
        stack.splice(i, 1);
        if (P._unsub) { P._unsub(); P._unsub = null; }
        veil.classList.remove('on');
        setTimeout(() => { if (veil.parentNode) veil.parentNode.removeChild(veil); }, 160);
        lock(lockName, false);
        if (spec.onClose) try { spec.onClose(); } catch (e) { console.error('[EBUI] onClose', e); }
        return true;
      },
    };
    stack.push(P); lock(lockName, true);
    // GS repaint subscription: one per panel, dropped on close.
    if (spec.render && window.GS && window.GS.on) {
      let live = true;
      const cb = () => { if (live && stack.indexOf(P) >= 0) spec.render(); };
      window.GS.on('change', cb);
      P._unsub = () => { live = false; };   // GS.on has no off(); the flag is the unsubscribe
    }
    setTimeout(() => veil.classList.add('on'), 8);   // setTimeout not rAF: rAF is throttled in background tabs
    return P;
  }

  // ---- prompt banner -------------------------------------------------------
  // sgPrompt's recipe VERBATIM — same host element (#s), same position
  // (left:50%, bottom:8%), same 14px monospace, same #000b / #3a2c20 / #e7ddd0,
  // same #e9a24b key, same 120ms opacity fade, same promptFmt from the graph's
  // own defaults. A counter prompt must be indistinguishable from a door prompt.
  // One banner per owner id; hidden by passing a falsy label. Never shown while
  // a modal is up (UILOCK held or a panel open) — no floating "Talk to the
  // chandler" over an open shop.
  const banners = {};
  function prompt(id, label, key) {
    if (!HAS_DOM) return;
    style();
    if (label && locked()) label = null;
    let b = banners[id];
    if (!b) {
      const host = document.getElementById('s') || document.body;
      b = banners[id] = document.createElement('div');
      b.className = 'ebui-banner'; b.id = 'ebui-p-' + id;
      host.appendChild(b);
    }
    if (!label) { b.style.opacity = '0'; return; }
    const k = String(key || sgDef('key')).toUpperCase();
    b.innerHTML = String(sgDef('promptFmt'))
      .replace('{label}', label)
      .replace('{key}', '<b style="color:var(--eb-amber)">' + k + '</b>');
    b.style.opacity = '1';
  }

  // ---- small helpers the panels share -------------------------------------
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  // a cursor over a list: wrapping, page-window aware, index-safe on shrink
  function cursor(n, i) { n = Math.max(0, n | 0); if (!n) return 0; i = i | 0; return ((i % n) + n) % n; }
  // THE CURSOR GLYPH. One definition for every list in the game — the FF
  // pointing arrow, CSS-drawn so no font has to ship it. `on` false still emits
  // the box, so rows do not jump horizontally as the cursor moves.
  function cur(on) { return '<span class="eb-cur' + (on ? ' on' : '') + '"></span>'; }
  function row(cells, opt) {
    opt = opt || {};
    const cls = 'ebui-row' + (opt.cur ? ' cur' : '') + (opt.dim ? ' dim' : '');
    return '<div class="' + cls + '">' + cur(opt.cur) + cells + '</div>';
  }
  function bar(frac) {
    const p = Math.max(0, Math.min(1, frac || 0)) * 100;
    return '<div class="ebui-bar"><i style="width:' + p.toFixed(1) + '%"></i></div>';
  }
  function delta(n) {
    if (!n) return '';
    return ' <span class="ebui-' + (n > 0 ? 'up' : 'dn') + '">' + (n > 0 ? '+' : '') + n + '</span>';
  }

  // ---- the window primitive, as HTML --------------------------------------
  // One factory so nothing in the game hand-rolls a border again. `title` gives
  // the window a head bar (FF's titled window); omit it for a plain frame.
  function win(inner, opt) {
    opt = opt || {};
    const cls = 'eb-win' + (opt.flat ? ' flat' : '') + (opt.cls ? ' ' + opt.cls : '');
    const st = opt.style ? ' style="' + opt.style + '"' : '';
    return '<div class="' + cls + '"' + st + '>' +
      (opt.title ? '<span class="eb-wtitle">' + esc(opt.title) + '</span>' : '') +
      (opt.raw ? inner : '<div class="eb-wbody"' +
        (opt.bodyStyle ? ' style="' + opt.bodyStyle + '"' : '') + '>' + inner + '</div>') +
      '</div>';
  }

  // ---- a labelled gauge ----------------------------------------------------
  // HP/XP/MP all read the same way: LABEL [======----] 34/34. `value===null`
  // renders the reserved-column dash (MP today, magic later) rather than a bar,
  // so a column can exist before the system behind it does.
  function gauge(label, value, max, opt) {
    opt = opt || {};
    if (value === null || value === undefined) {
      return '<div class="eb-gauge"><span class="lb">' + esc(label) + '</span>' +
        '<span class="tk" style="opacity:.35"></span><span class="nm eb-none">—</span></div>';
    }
    const f = max > 0 ? Math.max(0, Math.min(1, value / max)) : 0;
    const kind = (opt.kind === 'xp' ? ' xp' : '') + (opt.kind !== 'xp' && f <= 0.3 ? ' low' : '');
    return '<div class="eb-gauge' + kind + '"><span class="lb">' + esc(label) + '</span>' +
      '<span class="tk"><i style="width:' + (f * 100).toFixed(1) + '%"></i></span>' +
      '<span class="nm"><b>' + value + '</b>/' + max + '</span></div>';
  }

  // ---- character busts -----------------------------------------------------
  // ONE convention: assets/characters/<id>/bust.png. assetBase is mutable so a
  // mock harness (tools/ui_mock.html) can point at the same files from another
  // directory without any module knowing where it is being rendered.
  let assetBase = 'assets/';
  function bustUrl(id) { return assetBase + 'characters/' + String(id) + '/bust.png'; }
  // px = box size; big = show the whole plate rather than crop to the face.
  function portrait(id, px, opt) {
    opt = opt || {};
    const w = opt.w || px, h = opt.h || px;
    return '<div class="eb-port' + (opt.big ? ' big' : '') + (opt.cls ? ' ' + opt.cls : '') +
      '" style="width:' + w + 'px;height:' + h + 'px;background-image:url(&quot;' +
      bustUrl(id) + '&quot;)' + (opt.style ? ';' + opt.style : '') + '"></div>';
  }

  // ---- FIELD SPRITES: the chroma key ---------------------------------------
  // A character's battle sprite is their full-body pose plate, which the art
  // pipeline (tools/gen-character.mjs) delivers ON FLAT CHROMA MAGENTA — the
  // same background its 4x4 sheet stage uses, because that is what the image
  // model reliably paints. gen-character has NO keying stage, so the alpha is
  // cut HERE, at load, on a canvas.
  //
  // WHY AT LOAD AND NOT IN A BUILD STEP: the convention has to hold for art
  // that has not been drawn yet. A build step means every new character needs
  // someone to remember to run it; keying at load means dropping
  // assets/characters/<id>/pose.png into the repo is the whole job and the
  // character walks onto the battlefield with no code and no command. The cost
  // is one canvas pass per character per session, cached below.
  //
  // THE KEY ITSELF, three passes:
  //   1. MAGENTA-NESS  m = min(r,b) - g. Magenta is red AND blue over green, so
  //      this is high (~130) on the background and <=20 on essentially every
  //      pixel of the art — a 100-wide gap, hence a soft edge between 45 and 95
  //      rather than a hard cut, which is what keeps the outline from crawling.
  //   2. DESPILL       kept pixels that still lean magenta get their red and
  //      blue pulled back toward green in proportion to how far they leaned.
  //      This is the fringe: without it the sprite wears a pink halo.
  //   3. ONE ISLAND    these plates carry a stray smudge in a corner (a
  //      generator artifact — the top-left of both shipped poses has one). Only
  //      the largest connected run of opaque pixels survives, so the smudge
  //      goes without anybody hand-tuning a crop box per character.
  // Then the result is cropped to its own opaque bounds, which is what puts the
  // sprite's FEET on the bottom edge — the caller can seat it on a ground line
  // by simply bottom-aligning the element.
  const POSE_NAMES = ['pose.png', 'pose-front.png'];
  const KEY_LO = 45, KEY_HI = 95, KEY_SPILL = 0.85;

  function keepLargestIsland(keep, w, h) {
    const n = w * h, lab = new Int32Array(n).fill(-1), st = new Int32Array(n);
    let best = -1, bestN = 0, id = 0;
    for (let s = 0; s < n; s++) {
      if (!keep[s] || lab[s] >= 0) continue;
      let count = 0, top = 0;
      st[top++] = s; lab[s] = id;
      while (top) {
        const q = st[--top]; count++;
        const x = q % w, y = (q / w) | 0;
        if (x > 0 && keep[q - 1] && lab[q - 1] < 0) { lab[q - 1] = id; st[top++] = q - 1; }
        if (x < w - 1 && keep[q + 1] && lab[q + 1] < 0) { lab[q + 1] = id; st[top++] = q + 1; }
        if (y > 0 && keep[q - w] && lab[q - w] < 0) { lab[q - w] = id; st[top++] = q - w; }
        if (y < h - 1 && keep[q + w] && lab[q + w] < 0) { lab[q + w] = id; st[top++] = q + w; }
      }
      if (count > bestN) { bestN = count; best = id; }
      id++;
    }
    if (best < 0) return;
    for (let q = 0; q < n; q++) if (keep[q] && lab[q] !== best) keep[q] = 0;
  }

  // img -> a canvas holding the keyed, despilled, cropped sprite (or null if the
  // canvas is unreadable, e.g. cross-origin art on some other host).
  function chromaKey(img) {
    const w = img.naturalWidth || img.width, h = img.naturalHeight || img.height;
    if (!w || !h) return null;
    const src = document.createElement('canvas');
    src.width = w; src.height = h;
    const cx = src.getContext('2d', { willReadFrequently: true });
    if (!cx) return null;
    cx.drawImage(img, 0, 0);
    let d;
    try { d = cx.getImageData(0, 0, w, h); } catch (e) { return null; }   // tainted
    const p = d.data, keep = new Uint8Array(w * h);
    for (let i = 0, q = 0; q < keep.length; i += 4, q++) {
      const r = p[i], g = p[i + 1], b = p[i + 2];
      const m = (r < b ? r : b) - g;
      let a = 255;
      if (m >= KEY_HI) a = 0;
      else if (m > KEY_LO) a = ((KEY_HI - m) / (KEY_HI - KEY_LO) * 255) | 0;
      if (a && m > 0) {
        const k = (m < KEY_HI ? m : KEY_HI) / KEY_HI * KEY_SPILL;
        p[i] = r - (r - g) * k; p[i + 2] = b - (b - g) * k;
      }
      p[i + 3] = a;
      keep[q] = a > 8 ? 1 : 0;
    }
    keepLargestIsland(keep, w, h);
    let x0 = w, y0 = h, x1 = -1, y1 = -1;
    for (let q = 0; q < keep.length; q++) {
      if (!keep[q]) { p[q * 4 + 3] = 0; continue; }
      const x = q % w, y = (q / w) | 0;
      if (x < x0) x0 = x; if (x > x1) x1 = x;
      if (y < y0) y0 = y; if (y > y1) y1 = y;
    }
    cx.putImageData(d, 0, 0);
    if (x1 < x0 || y1 < y0) return null;
    const out = document.createElement('canvas');
    out.width = x1 - x0 + 1; out.height = y1 - y0 + 1;
    out.getContext('2d').drawImage(src, x0, y0, out.width, out.height, 0, 0, out.width, out.height);
    return out;
  }

  // poseSprite(id) -> Promise<canvas|null>. Resolves the FIRST pose plate that
  // loads, so a character with no field art resolves null and the caller simply
  // does not put them on the field. Cached per id: the key is idempotent and a
  // battle screen is rebuilt every encounter.
  const poseCache = Object.create(null);
  function poseUrls(id) {
    return POSE_NAMES.map(n => assetBase + 'characters/' + String(id) + '/' + n);
  }
  function poseSprite(id) {
    if (!HAS_DOM) return Promise.resolve(null);
    const k = String(id);
    if (poseCache[k]) return poseCache[k];
    const urls = poseUrls(k);
    return (poseCache[k] = new Promise((resolve) => {
      let i = 0;
      const next = () => {
        if (i >= urls.length || typeof Image !== 'function') return resolve(null);
        const im = new Image();
        im.onload = () => { let c = null; try { c = chromaKey(im); } catch (e) { c = null; } resolve(c); };
        im.onerror = () => { i++; next(); };
        im.src = urls[i];
      };
      next();
    }));
  }

  window.EBUI = {
    HAS_DOM, KEYMAP, act, sgDef, panel, prompt, style,
    esc, row, bar, delta, cursor,
    // the window grammar (see the CSS block): every panel in the game builds
    // from these four and nothing hand-rolls a border.
    win, gauge, cur, portrait, bustUrl,
    // field sprites: the chroma key and its convention
    poseSprite, poseUrls, chromaKey,
    get assetBase() { return assetBase; },
    set assetBase(v) { assetBase = String(v == null ? '' : v); },
    get depth() { return stack.length; },
    get open() { return stack.length > 0; },
    // "is ANY modal up" — our panels plus anyone else holding the engine lock
    // (a battle screen). Prompt suppression and open-triggers both use this.
    get locked() { return locked(); },
    // module open-triggers (E at a counter, Esc for the menu). Suppressed while
    // ANY modal is up, so a panel's own cancel key always wins and a battle
    // screen can never be interrupted by a shop prompt.
    onGlobalKey(key, fn) { globals[String(key).toLowerCase()] = fn; wire(); },
    // TEST/DEBUG surface
    debug() { return { depth: stack.length, locked: locked(), globals: Object.keys(globals), dom: HAS_DOM, styled }; },
  };
})();
