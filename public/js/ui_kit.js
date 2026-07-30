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
  // Injected once. Kept in one template so the palette is a single edit.
  const CSS = `
.ebui-veil{position:fixed;inset:0;z-index:20;background:#08060420;
  backdrop-filter:blur(1.5px);-webkit-backdrop-filter:blur(1.5px);
  display:flex;align-items:center;justify-content:center;
  opacity:0;transition:opacity 120ms linear;pointer-events:none}
.ebui-veil.on{opacity:1}
.ebui-panel{min-width:min(620px,86vw);max-width:min(900px,92vw);max-height:86vh;
  display:flex;flex-direction:column;overflow:hidden;
  background:#12100dfa;color:#e7ddd0;border:1px solid #3a2c20;border-radius:10px;
  box-shadow:0 10px 40px #000a;
  font:14px/1.45 system-ui,-apple-system,Segoe UI,sans-serif;
  text-shadow:0 1px 2px #0008}
.ebui-head{display:flex;align-items:baseline;gap:12px;padding:10px 14px;
  border-bottom:1px solid #3a2c20;background:#1a150fcc}
.ebui-title{font-weight:600;letter-spacing:.02em}
.ebui-sub{color:#a99a86;font-size:12px}
.ebui-gold{margin-left:auto;font-family:ui-monospace,Menlo,monospace;color:#e9a24b}
.ebui-body{padding:10px 14px;overflow:auto}
.ebui-foot{padding:7px 14px;border-top:1px solid #3a2c20;background:#1a150fcc;
  color:#a99a86;font-size:12px;font-family:ui-monospace,Menlo,monospace}
.ebui-tabs{display:flex;gap:6px;padding:8px 14px 0}
.ebui-tab{padding:3px 12px;border:1px solid #3a2c20;border-radius:6px;
  color:#a99a86;background:#0000;font-size:13px}
.ebui-tab.on{color:#12100d;background:#e9a24b;border-color:#e9a24b;font-weight:600}
.ebui-row{display:flex;gap:10px;align-items:baseline;padding:3px 8px;
  border-radius:5px;border:1px solid transparent}
.ebui-row.cur{background:#e9a24b1f;border-color:#e9a24b66}
.ebui-row.dim{color:#6f6558}
.ebui-row .k{flex:1 1 auto;min-width:0;overflow:hidden;text-overflow:ellipsis;
  white-space:nowrap}
.ebui-row .n{font-family:ui-monospace,Menlo,monospace;text-align:right;
  flex:0 0 auto;font-variant-numeric:tabular-nums}
.ebui-cur{color:#e9a24b;flex:0 0 1em}
.ebui-note{margin-top:8px;padding-top:8px;border-top:1px dashed #3a2c2088;
  color:#c9bcab;font-size:13px;min-height:2.6em}
.ebui-msg{color:#e9a24b;font-family:ui-monospace,Menlo,monospace;font-size:12px}
.ebui-msg.bad{color:#e07a5f}
.ebui-cols{display:grid;gap:14px}
.ebui-card{border:1px solid #3a2c2099;border-radius:8px;padding:8px 10px;
  background:#0000000f}
.ebui-stat{display:flex;gap:8px;font-family:ui-monospace,Menlo,monospace;
  font-size:12.5px}
.ebui-stat .l{color:#a99a86;flex:0 0 3.2em}
.ebui-bar{height:6px;border-radius:3px;background:#3a2c20;overflow:hidden;
  margin:3px 0 5px}
.ebui-bar>i{display:block;height:100%;background:#e9a24b}
.ebui-up{color:#8fbf6a}.ebui-dn{color:#e07a5f}
.ebui-shake{animation:ebui-sh 180ms linear}
@keyframes ebui-sh{0%,100%{transform:translateX(0)}25%{transform:translateX(-4px)}
  75%{transform:translateX(4px)}}
.ebui-banner{position:absolute;left:50%;bottom:8%;transform:translateX(-50%);
  z-index:3;color:#e7ddd0;font:14px monospace;background:#000b;
  border:1px solid #3a2c20;border-radius:8px;padding:7px 14px;
  text-shadow:0 1px 2px #000;pointer-events:none;white-space:nowrap;
  opacity:0;transition:opacity 120ms linear}`;
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
    const frame = document.createElement('div'); frame.className = 'ebui-panel';
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
      .replace('{key}', '<b style="color:#e9a24b">' + k + '</b>');
    b.style.opacity = '1';
  }

  // ---- small helpers the panels share -------------------------------------
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  // a cursor over a list: wrapping, page-window aware, index-safe on shrink
  function cursor(n, i) { n = Math.max(0, n | 0); if (!n) return 0; i = i | 0; return ((i % n) + n) % n; }
  function row(cells, opt) {
    opt = opt || {};
    const cls = 'ebui-row' + (opt.cur ? ' cur' : '') + (opt.dim ? ' dim' : '');
    const c = '<span class="ebui-cur">' + (opt.cur ? '▸' : '') + '</span>';
    return '<div class="' + cls + '">' + c + cells + '</div>';
  }
  function bar(frac) {
    const p = Math.max(0, Math.min(1, frac || 0)) * 100;
    return '<div class="ebui-bar"><i style="width:' + p.toFixed(1) + '%"></i></div>';
  }
  function delta(n) {
    if (!n) return '';
    return ' <span class="ebui-' + (n > 0 ? 'up' : 'dn') + '">' + (n > 0 ? '+' : '') + n + '</span>';
  }

  window.EBUI = {
    HAS_DOM, KEYMAP, act, sgDef, panel, prompt, style,
    esc, row, bar, delta, cursor,
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
