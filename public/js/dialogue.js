// dialogue.js — window.Dialogue: the game's talking window.
// WORLD-POPULATION agent owned. Additive and self-contained: it no-ops silently
// on a page with no EBUI, before its data lands, and in a scene with nobody to
// talk to. Nothing here knows a character, a line, a district or a coordinate —
// every word the player reads comes out of public/game/dialogue.json.
//
// WHY THIS FILE EXISTS
//   npc.js puts people in the town; this puts their voices on screen. They are
//   split because they fail differently: a missing pose plate should still let a
//   conversation happen, and a missing dialogue node should still leave a person
//   standing in the market. Either half is useful without the other.
//
// THE LOOK IS NOT NEW. The user ruled the BLUE SYSTEM-VOICE window language for
// everything, so this file draws NO chrome of its own: the frame, the bevel, the
// grain, the title bar, the cursor glyph, the row and the portrait plate are all
// ui_kit's primitives (.eb-win / .eb-wtitle / .eb-wbody / .eb-cur / .eb-port),
// and the only CSS below is GEOMETRY — where the window sits, how big the bust
// is, how the choices stack. A re-tint of ui_kit re-tints the conversation.
//
// FOUR DEPARTURES FROM THE SHOP/MENU PANEL SHAPE, each deliberate:
//   1. BOTTOM, NOT CENTRE. A dialogue box is furniture at the foot of the frame
//      (FF's whole grammar); the pause menu is a screen you go to. Same panel,
//      `align-items:flex-end`.
//   2. NO SCRIM. The menu veils the world because you have left it; a
//      conversation happens IN the world and must not grey it out. The veil
//      element survives (it is what carries the panel and the fade) with its
//      wash and blur removed.
//   3. THE PORTRAIT IS A CUT-IN, NOT A THUMBNAIL. The user ruled the modern
//      cut-in grammar on 2026-08-01: the character is an alpha cutout that
//      RISES OUT OF THE BOX — chest-up, no frame, no background, standing over
//      the scene with its lower body hidden behind the dialogue window. See
//      THE CUT-IN below for the geometry and the fallback. Expressions are per
//      LINE, not per character: cutin-<mood>.png / expr-<mood>.png, falling
//      back to the neutral plate the moment a mood has no art.
//   4. TYPEWRITER ON A TIMER, NOT rAF. rAF is throttled to nothing in a
//      background tab and every headless verification this project has lives
//      there. setInterval means a test can open a conversation, wait, and read
//      the finished line — the same reason shop.js keepalives its tick.
//
// THE CUT-IN (the 2026-08-01 ruling, "the character art is actually rising out
// of the box"). Three facts hold it together:
//
//   IT LIVES BEHIND THE WINDOW, NOT BESIDE IT. The art is absolutely positioned
//   in the panel at z-index 0, under .ebui-body/.ebui-foot's z-index 1, and its
//   bottom is SUNK halfway into the box. So the character is occluded by the
//   window rather than clipped by a rectangle: there is no hard bottom edge on
//   screen at all, the crop's own bottom never has to be right, and the ruling's
//   "never covering the text column" holds structurally instead of by arithmetic.
//
//   IT IS A PERSISTENT ELEMENT, NOT PART OF render()'s HTML. render() rewrites
//   the body every typewriter tick (16 ms); a CSS entrance animation inside that
//   markup would restart sixty times a second and never play. The <img> is
//   created once per conversation and only its src changes, which is also what
//   makes the slide-and-fade on SPEAKER CHANGE mean something.
//
//   THE FALLBACK IS THE OLD THUMBNAIL, chosen from a MANIFEST rather than a
//   probe. assets/characters/cutins.json (written by tools/gen-cutin.py) says
//   which ids have cut-in art, so the window knows which shape it is drawing
//   BEFORE the first paint — a probe would show a framed thumbnail for a beat
//   and then jump layout. No manifest, no entry, or a 404 on the art: the
//   speaker keeps the framed .eb-port bust and the conversation is unharmed.
//   dialogue_test asserts every speaker lands in one of those two states.
//
// UILOCK: EBUI.panel({name:'dialogue'}) takes the named engine lock, so phys()
// freezes, held keys are zeroed and the scene-graph/debug keys stand down for
// exactly as long as the window is up. That is the established modal contract
// and this file adds nothing to it.
//
// window.Dialogue
//   Dialogue.load()               -> Promise<data|null>   (cached; safe to call often)
//   Dialogue.play(nodeId, opt)    -> Promise<{ended,node}>  opens the window
//   Dialogue.speaker(id)          -> {name,color,portrait} from the data's own table
//   Dialogue.isOpen / .close()
//   Dialogue.check(cond)          -> the condition evaluator, over GS.state.flags
//   Dialogue.debug()              -> live state for a headless assert
(function () {
  'use strict';

  var DATA_URL = 'game/dialogue.json';
  var CUTIN_URL = 'characters/cutins.json';   // under assetBase, not the game data
  var TICK_MS = 16;              // typewriter clock (timer, not rAF — see header)
  var DEF_CPS = 46;              // characters per second, overridable in the data
  var CUTIN_MAX_PX = 560;        // ~3x the old 190px thumbnail; see placeCutin()
  var CUTIN_VH = 0.45;           // ...VISIBLE portrait never exceeds this much viewport
  var CUTIN_STAGE = 0.62;        // ...nor this much of the game frame
  var CUTIN_WIDE = 0.60;         // ...nor this much of the window's width
  var CUTIN_SINK = 0.55;         // share of the box the art's bottom sinks behind
  // THE PARTY, and why the runtime needs to know. The user ruled (2026-08-01) that
  // the player characters get a cut-in on every beat the PLAYER speaks — including
  // the choice list, which is the player talking and used to sit under whichever
  // NPC happened to have spoken last — and that the two sides of a conversation are
  // anchored opposite each other, NPC left and party right, so an exchange reads as
  // two people facing one another. Data first, this list second: dialogue.json's
  // `defaults.players` wins, and these two are the fallback for a data file that
  // predates the ruling.
  var PLAYERS = ['vesper', 'lake'];

  var U = function () { return window.EBUI || null; };
  var HAS_DOM = typeof document !== 'undefined' && !!document.createElement;

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
        if (!j) { FAILED = true; console.log('[Dialogue] no ' + DATA_URL + ' — dialogue disabled'); return null; }
        DATA = j;
        loadCutins();
        return j;
      });
    return LOADING;
  }
  // WHICH SPEAKERS HAVE CUT-IN ART. A tiny map, fetched once, never blocking:
  // until it lands (or if it never does) every speaker draws the old framed
  // thumbnail, which is exactly the migration behaviour the ruling asked for.
  var CUT = null;
  function loadCutins() {
    if (CUT || typeof fetch !== 'function') return;
    CUT = {};                                     // claim it: one fetch per session
    fetch(base() + CUTIN_URL).then(function (r) { return r.ok ? r.json() : null; })
      .catch(function () { return null; })
      .then(function (j) { if (j) CUT = j; });
  }

  function nodes() { return (DATA && DATA.nodes) || {}; }
  function node(id) { return nodes()[id] || null; }
  function defaults() { return (DATA && DATA.defaults) || {}; }

  // The speaker table lives in the DATA, not here: play3d.html does not load
  // assets.js, so the nameplate colours that chapter1/2/3 use have to travel
  // with the lines. `portrait:false` is the nameplate-only contract the scripts
  // specify for the sprite-first extras (Hobb, Pell, Sorrel, Creel, Nib) —
  // those speakers render with a name and no bust, deliberately.
  function speaker(id) {
    var t = (DATA && DATA.speakers) || {};
    var s = t[id] || null;
    return {
      id: id,
      name: (s && s.name) || (id ? String(id).charAt(0).toUpperCase() + String(id).slice(1) : ''),
      color: (s && s.color) || 'var(--eb-amber)',
      // portrait id defaults to the speaker id; `false`/null means nameplate-only
      portrait: s && s.portrait !== undefined ? s.portrait : id,
    };
  }

  // ---------------------------------------------------- conditions/effects ----
  // Everything a condition can ask about is GS state, so a quest tomorrow needs
  // no new vocabulary here: gate a node on a flag it sets itself.
  function flags() {
    try { if (window.GS && window.GS.state && window.GS.state.flags) return window.GS.state.flags; } catch (e) { }
    return null;
  }
  function flagVal(k) { var f = flags(); return f ? f[k] : undefined; }

  function check(c) {
    if (c === undefined || c === null) return true;
    if (typeof c === 'string') return !!flagVal(c);          // shorthand: "flag name"
    if (Array.isArray(c)) return c.every(check);             // shorthand: all of
    if (c.all) { if (!c.all.every(check)) return false; }
    if (c.any) { if (!c.any.some(check)) return false; }
    if (c.not !== undefined) { if (check(c.not)) return false; }
    if (c.flag !== undefined) { if (!flagVal(c.flag)) return false; }
    if (c.notFlag !== undefined) { if (flagVal(c.notFlag)) return false; }
    if (c.flagIs) { for (var k in c.flagIs) if (flagVal(k) !== c.flagIs[k]) return false; }
    if (c.flagAtLeast) { for (var k2 in c.flagAtLeast) if (!((flagVal(k2) || 0) >= c.flagAtLeast[k2])) return false; }
    if (c.hasItem !== undefined) {
      try { if (!(window.GS && window.GS.ok && window.GS.count(c.hasItem) > 0)) return false; }
      catch (e) { return false; }
    }
    if (c.goldAtLeast !== undefined) {
      try { if (!(window.GS && window.GS.ok && window.GS.state.gold >= c.goldAtLeast)) return false; }
      catch (e) { return false; }
    }
    return true;
  }

  // Effects are applied through GS so a save records them and every panel
  // listening on GS 'change' repaints. `shop` is deferred to the window's close
  // (see run()): a shop opened over an open dialogue would be two modals deep
  // for no reason, and "greet, THEN trade" is the whole point of the handoff.
  var pendingShop = null;
  function effects(e) {
    if (!e) return;
    var changed = false;
    try {
      var f = flags();
      if (f && e.setFlags) { for (var k in e.setFlags) { f[k] = e.setFlags[k]; changed = true; } }
      if (f && e.incFlags) { for (var k2 in e.incFlags) { f[k2] = (f[k2] || 0) + e.incFlags[k2]; changed = true; } }
      if (e.giveItem && window.GS && window.GS.ok) { window.GS.addItem(e.giveItem, e.giveQty || 1); changed = true; }
      if (e.gold && window.GS && window.GS.ok) { window.GS.addGold(e.gold); changed = true; }
      if (changed && window.GS && window.GS.emit) window.GS.emit('change', window.GS.state);
    } catch (err) { console.error('[Dialogue] effects', err); }
    if (e.shop) pendingShop = e.shop;
  }

  // ------------------------------------------------------------ geometry ----
  // GEOMETRY ONLY. Every colour, bevel, grain and font in the window comes from
  // ui_kit's custom properties; if a value below is a colour it is a var().
  var CSS = [
    /* the window sits on the floor of the frame, and the world stays visible
       through it — a conversation is not a place you go. */
    '.ebui-veil.dlg{background:none;backdrop-filter:none;-webkit-backdrop-filter:none;',
    '  align-items:flex-end;justify-content:center;padding:0 0 3.4vh}',
    /* position:relative so the cut-in has this panel — not the veil — as its
       containing block; overflow stays visible so the art can stand above it. */
    '.ebui-veil.dlg .ebui-panel.float{width:min(940px,90vw);max-height:none;gap:0;position:relative}',
    '.ebui-veil.dlg .ebui-head{display:none}',
    '.ebui-veil.dlg .ebui-foot{margin-top:7px;align-self:center;padding:5px 14px}',
    /* THE CUT-IN. z-index 0 puts it UNDER .ebui-body (z-index 1), which is the
       whole trick: the window occludes the character's lower body, so the art
       reads as standing behind the box rather than pasted next to it. The two
       drop-shadows are what lift an alpha cutout off a busy pre-rendered plate —
       a tight one for contact, a wide soft one for separation. Size and offsets
       are set from JS (placeCutin) because they are measured off the live box. */
    '.dlg-cutin{position:absolute;z-index:0;pointer-events:none;width:auto;',
    '  image-rendering:auto;transform-origin:50% 100%;',
    '  filter:drop-shadow(0 2px 5px #000000a6) drop-shadow(0 8px 26px #0006)}',
    '.dlg-cutin.in{animation:dlg-rise 260ms cubic-bezier(.2,.86,.3,1) both}',
    '@keyframes dlg-rise{from{opacity:0;transform:translateY(18px) scale(.99)}',
    '  to{opacity:1;transform:none}}',
    /* The flip has to be baked into its OWN keyframes rather than layered on the
       element: `transform` is one property, so a scaleX(-1) written to the style
       would be overwritten by the entrance animation's own transform for 260 ms
       and the portrait would visibly un-mirror as it rose. Off by default —
       see cutinFlip() for why mirroring these plates is opt-in. */
    '.dlg-cutin.flip{transform:scaleX(-1)}',
    '.dlg-cutin.flip.in{animation:dlg-rise-flip 260ms cubic-bezier(.2,.86,.3,1) both}',
    '@keyframes dlg-rise-flip{from{opacity:0;transform:scaleX(-1) translateY(18px) scale(.99)}',
    '  to{opacity:1;transform:scaleX(-1)}}',
    '@media (prefers-reduced-motion:reduce){.dlg-cutin.in,.dlg-cutin.flip.in{animation:none}}',
    /* FALLBACK ROW — the pre-cut-in shape, still the layout for any speaker with
       no cut-in art: bust + box on one baseline, the plate hanging above the
       window's top edge. With a cut-in the row has no bust in it at all and the
       text gets the whole box, because the portrait is behind it. */
    '.dlg-wrap{display:flex;align-items:flex-end;gap:12px}',
    '.dlg-bust{flex:0 0 auto;margin-bottom:-6px;background-size:cover;background-position:50% 12%}',
    '.dlg-col{flex:1 1 auto;min-width:0}',
    /* the nameplate carries the SPEAKER'S canon colour (assets.js's palette,
       travelling in the data), lifted so a muted one — Odessa's slate, Creel's
       olive — still reads white-hot on the head bar's near-black. Brightening
       at paint time rather than storing lightened hex keeps one source of truth
       for a character's colour. */
    '.dlg-name{filter:brightness(1.5) saturate(1.15)}',
    '.dlg-text{min-height:5.1em;font:15.5px/1.62 var(--eb-face);color:var(--eb-ink);',
    '  text-shadow:0 1px 2px #0009;white-space:pre-wrap}',
    /* the character being typed is invisible rather than absent: the box never
       reflows mid-line, so a long line does not jump the choices around. */
    '.dlg-text i{font-style:normal;opacity:0}',
    '.dlg-more{position:absolute;right:11px;bottom:6px;color:var(--eb-amber);font-size:12px;',
    '  animation:dlg-blink 1s steps(2,jump-none) infinite}',
    '.dlg-choices{margin-top:8px;padding-top:7px;border-top:1px solid var(--eb-rule)}',
    '.dlg-choices .ebui-row{font:14.5px/1.5 var(--eb-face)}',
    '@keyframes dlg-blink{0%,100%{opacity:.25}50%{opacity:1}}',
    '@media (prefers-reduced-motion:reduce){.dlg-more{animation:none;opacity:1}}',
  ].join('\n');
  var styled = false;
  function style() {
    if (styled || !HAS_DOM || !U()) return;
    styled = true;
    U().style();                                  // ui_kit's sheet first — we only add geometry
    var s = document.createElement('style');
    s.id = 'ebdlg-style'; s.textContent = CSS;
    document.head.appendChild(s);
  }

  // Expression plates are optional by design: a character gets `expr-warm.png`
  // the day somebody draws it, and until then the line simply wears the neutral
  // bust. Probed once per url and cached, so a missing mood costs one 404 for
  // the whole session and never blocks a line.
  var bustOk = Object.create(null);
  function probe(url) {
    if (bustOk[url] !== undefined) return bustOk[url];
    bustOk[url] = new Promise(function (res) {
      if (typeof Image !== 'function') return res(false);
      var im = new Image();
      // DECODE, not just load. These plates are 1024px 2 MB PNGs; `onload` fires
      // when the bytes are in, and the browser then decodes on the next paint —
      // which is a visible beat of EMPTY PORTRAIT FRAME at the top of every
      // conversation. Resolving on decode() means the bust appears with the
      // first line instead of a moment after it. Falls back to onload where
      // decode() is unavailable.
      im.onload = function () {
        if (im.decode) im.decode().then(function () { res(true); }, function () { res(true); });
        else res(true);
      };
      im.onerror = function () { res(false); };
      im.src = url;
    });
    return bustOk[url];
  }
  function base() { return (U() && U().assetBase) || 'assets/'; }
  function bustUrl(pid, expr) {
    var d = base() + 'characters/' + pid + '/';
    return expr ? d + 'expr-' + expr + '.png' : d + 'bust.png';
  }
  // The manifest answers both questions at once: is there a cut-in for this
  // speaker, and was this MOOD matted too. An unlisted mood falls to the neutral
  // cut-in rather than to the thumbnail — changing the portrait's whole shape
  // mid-conversation because one line asked for a face nobody drew would be a
  // worse fallback than simply not changing the face.
  function cutin(pid, expr) {
    var e = CUT && CUT[pid];
    if (!e) return null;
    var d = base() + 'characters/' + pid + '/';
    if (expr && e.expr && e.expr.indexOf(expr) >= 0) return d + 'cutin-' + expr + '.png';
    return d + 'cutin.png';
  }
  function cutinAspect(pid) {
    var e = CUT && CUT[pid];
    return (e && e.w && e.h) ? e.w / e.h : 0.9;
  }
  // MIRRORED PLACEMENT IS THE CONVENTION; MIRRORING THE ART IS NOT, and the
  // difference is deliberate. Putting the party on the opposite side of the frame
  // is free and it is what makes an exchange read as two people. Flipping the
  // PIXELS to make them face inward is not free: these portraits are near-frontal,
  // so the gain is small, and their asymmetries are canon — Lake's brass flame pin
  // sits at his throat, Vesper's map-satchel strap crosses one shoulder, Odessa's
  // whistle hangs on one cord — and a mirrored plate quietly moves them. So the
  // flip is per-character, off unless the manifest says otherwise, and turning it
  // on for a face is a decision someone made after looking at that face.
  function cutinFlip(pid) {
    var e = CUT && CUT[pid];
    return !!(e && e.flip);
  }
  function players() {
    var d = defaults();
    return (d && Array.isArray(d.players) && d.players.length) ? d.players : PLAYERS;
  }
  function isPlayer(pid) { return players().indexOf(pid) >= 0; }

  // ------------------------------------------------------------- the run ----
  // One conversation at a time. `S` is the whole of it: a queue of resolved
  // lines, a cursor, the typewriter's reveal count, and the choice state.
  var S = null;

  function esc(s) { return U() ? U().esc(s) : String(s); }

  // Flatten a node into concrete lines, dropping any whose condition fails.
  // Done UP FRONT so a flag set by line 2's effect cannot retroactively change
  // whether line 1 was shown — the conversation the player is reading is fixed
  // the moment it starts.
  function linesOf(n) {
    var out = [], src = n.lines || (n.text ? [n.text] : []);
    for (var i = 0; i < src.length; i++) {
      var l = src[i];
      if (typeof l === 'string') l = { text: l };
      if (!check(l.if)) continue;
      out.push({
        text: String(l.text === undefined ? '' : l.text),
        speaker: l.speaker || n.speaker || null,
        name: l.name || (l.speaker ? null : n.name) || null,
        expr: l.expr || n.expr || null,
        effects: l.effects || null,
      });
    }
    return out;
  }

  // Follow a node's `if`/`else` until a node whose guard passes (or nothing).
  // Bounded, so a data file that points a node's else at itself reports rather
  // than hanging the page.
  function resolve(id) {
    var seen = {}, cur = id;
    while (cur) {
      if (seen[cur]) { console.warn('[Dialogue] node loop at "' + cur + '"'); return null; }
      seen[cur] = 1;
      var n = node(cur);
      if (!n) { console.warn('[Dialogue] unknown node "' + cur + '"'); return null; }
      if (check(n.if)) return { id: cur, node: n };
      cur = n['else'] || null;
    }
    return null;
  }

  function enter(id) {
    var r = resolve(id);
    if (!r) return false;
    S.nodeId = r.id; S.node = r.node;
    S.lines = linesOf(r.node);
    S.li = -1; S.choice = 0; S.mode = 'line';
    S.visited.push(r.id);
    if (S.visited.length > 64) { console.warn('[Dialogue] node chain too long; stopping'); return false; }
    return nextLine();
  }

  function nextLine() {
    S.li++;
    if (S.li < S.lines.length) {
      var l = S.lines[S.li];
      effects(l.effects);
      S.shown = 0; S.mode = 'line';
      S.full = l.text.length;
      loadBust(l);
      render();
      return true;
    }
    // lines exhausted: the node's own effects fire once, then choices or `next`
    effects(S.node.effects);
    var ch = (S.node.choices || []).filter(function (c) { return check(c.if); });
    if (ch.length) {
      S.mode = 'choice'; S.avail = ch; S.choice = 0;
      loadChooser(S.node);                           // the choice list is the player talking
      render(); return true;
    }
    if (S.node.next) return enter(S.node.next);
    return false;                                    // end of conversation
  }

  // Resolve the plate for a line and repaint when it lands. Never blocks the
  // line: the text types immediately and the bust swaps in a frame later.
  // WHO IS TALKING DURING A CHOICE. The list of choices is the player's own line —
  // it is the one beat of a conversation the player authors — and before the ruling
  // it wore whichever NPC had spoken last, which reads as the NPC asking themselves
  // the question. The chooser is the node's `chooser` if the script names one, and
  // otherwise the first of the party: Vesper is the protagonist and the default
  // voice of a choice. Falls back silently to leaving the portrait alone if the
  // chooser has no art, because a missing plate must never eat a choice list.
  function chooserId(n) {
    return (n && n.chooser) || players()[0] || null;
  }
  function loadChooser(n) {
    var id = chooserId(n);
    if (!id) return;
    var sp = speaker(id);
    var pid = sp && sp.portrait;
    if (!pid) return;
    S.pid = pid;
    S.side = 'right';
    S.cutin = cutin(pid, (n && n.chooserExpr) || null);
    S.bust = bustUrl(pid, null);
  }

  function loadBust(l) {
    var sp = speaker(l.speaker);
    var pid = sp.portrait;
    if (!pid) { S.bust = null; S.cutin = null; S.pid = null; return; }
    S.pid = pid;
    // `players` names SPEAKERS, and a speaker's portrait id is usually but not
    // always the same string (del.deckhand -> villager-man). Both are checked so a
    // party member who is ever given a distinct portrait id still lands on the
    // right, and so an ARCHETYPE portrait can never drag an NPC over there by
    // sharing a name with one.
    S.side = (isPlayer(l.speaker) || isPlayer(pid)) ? 'right' : 'left';
    S.cutin = cutin(pid, l.expr);
    var neutral = bustUrl(pid, null);
    // The NEUTRAL plate goes up immediately and unconditionally — a portrait
    // frame is never empty while a mood is being fetched, and a mood that has
    // no art (most of them, today) simply never arrives and the neutral stands.
    S.bust = neutral;
    if (!l.expr || S.cutin) return;               // the cut-in owns the mood if it exists
    var want = bustUrl(pid, l.expr);
    Promise.resolve(probe(want)).then(function (ok) {
      if (!S || S.lines[S.li] !== l) return;         // the line moved on
      if (ok) { S.bust = want; render(); }
    });
  }

  // ------------------------------------------------------------- cut-in ----
  // Where the art stands, measured off the live window rather than guessed.
  // getBoundingClientRect is a synchronous layout read and render() runs on a
  // 16 ms tick, so it is gated on a GEOMETRY KEY: the box only changes shape when
  // the mode changes, when a choice list appears, or when the frame is resized.
  function geoKey() {
    return (S.mode || '') + '/' + (S.avail ? S.avail.length : 0) + '/' +
      (S.side || '') + '/' + (S.pid || '') + '/' +
      (S.panel && S.panel.frame ? S.panel.frame.clientWidth + 'x' + S.panel.frame.clientHeight : '');
  }

  function placeCutin(force) {
    var el = S && S.cutinEl;
    if (!el || !S.cutin) return;
    var k = geoKey();
    if (!force && k === S.geo) return;
    S.geo = k;
    var fr = S.panel.frame, box = fr.querySelector('.eb-win');
    if (!box) return;
    var fb = fr.getBoundingClientRect(), bb = box.getBoundingClientRect();
    if (!bb.height) return;

    // The bottom sinks INTO the box: no bottom edge is ever on screen, so the
    // character emerges from the window instead of resting on it.
    var sink = Math.min(Math.round(bb.height * CUTIN_SINK), bb.height - 6);

    // HEIGHT: the ruling's ~2.5-3x the old 190px thumbnail, then three caps.
    // THE VIEWPORT CAP IS ON THE VISIBLE PORTRAIT, not on the element — `sink`
    // of this art is behind the window and was never on screen to be capped, and
    // measuring the element instead quietly shrank every portrait by the box's
    // half-height. The stage cap is separate and not redundant: play3d's frame is
    // a 16:9 letterbox inside the page, so 45vh can be taller than the whole
    // game. The WIDTH cap has to be generous or it silently punishes a pose: the
    // crops are cut to the silhouette, so Maren's folded arms make hers 1.58 wide
    // where the cast's norm is ~1.0, and at 44% she rendered 262 px tall against
    // Rowan's 426 — the same ruling producing two different portraits because one
    // character crossed her arms. At 60% she lands at 369 and the cap is back to
    // being what it is for: stopping a portrait from becoming a wall.
    var stageH = (S.panel.el && S.panel.el.clientHeight) || 0;
    var viewH = (typeof window !== 'undefined' && window.innerHeight) || stageH || 720;
    var h = Math.min(CUTIN_MAX_PX, viewH * CUTIN_VH + sink);
    if (stageH > 0) h = Math.min(h, stageH * CUTIN_STAGE);
    var wide = fb.width * CUTIN_WIDE, asp = cutinAspect(S.pid);
    if (asp * h > wide) h = wide / asp;
    h = Math.max(90, Math.round(h));
    el.style.height = h + 'px';
    // WHICH SIDE. The NPC keeps the left edge of the box, the party takes the right,
    // and each is anchored to its OWN edge rather than to a computed x — so a wide
    // portrait and a narrow one both sit flush against the frame they belong to
    // instead of drifting toward the middle by however much the crop happened to
    // measure. Both properties are always written: an element that kept a stale
    // `left` while gaining a `right` would be stretched between the two.
    if (S.side === 'right') {
      el.style.left = 'auto';
      el.style.right = Math.round(fb.right - bb.right + 14) + 'px';
    } else {
      el.style.right = 'auto';
      el.style.left = Math.round(bb.left - fb.left + 14) + 'px';
    }
    el.style.bottom = Math.round(fb.bottom - bb.top - sink) + 'px';
  }

  // Push S.cutin into the persistent element. Re-arms the entrance animation on
  // a SPEAKER CHANGE only (src change), never on a typewriter tick.
  function syncCutin() {
    var el = S && S.cutinEl;
    if (!el) return;
    if (!S.cutin) { el.style.display = 'none'; S.cutinSrc = null; return; }
    el.style.display = '';
    el.classList.toggle('flip', cutinFlip(S.pid));
    if (S.cutinSrc !== S.cutin) {
      S.cutinSrc = S.cutin;
      el.classList.remove('in');
      el.style.visibility = 'hidden';       // no half-drawn art under the rise
      el.src = S.cutin;
      var arm = function () {
        if (!S || S.cutinSrc !== S.cutin) return;
        el.style.visibility = '';
        void el.offsetWidth;                // restart the keyframes
        el.classList.add('in');
        placeCutin(true);
      };
      if (el.complete && el.naturalWidth) arm(); else el.onload = arm;
    }
    placeCutin(false);
  }

  // --------------------------------------------------------------- paint ----
  function render() {
    if (!S || !S.panel) return;
    var E = U();
    var l = S.lines[S.li] || S.lines[S.lines.length - 1] || { text: '', speaker: null };
    var sp = speaker(l.speaker);
    var nm = l.name || sp.name;

    // reveal: raw slice, THEN escape — escaping first would type "&amp;" one
    // character at a time. The unrevealed tail is emitted invisible so the box
    // never reflows mid-line.
    var shown = S.mode === 'choice' ? l.text.length : Math.min(S.shown | 0, l.text.length);
    var body = esc(l.text.slice(0, shown));
    if (shown < l.text.length) body += '<i>' + esc(l.text.slice(shown)) + '</i>';

    var done = shown >= l.text.length;
    var more = (S.mode === 'line' && done) ? '<span class="dlg-more">&#9660;</span>' : '';

    var choices = '';
    if (S.mode === 'choice') {
      choices = '<div class="dlg-choices">' + S.avail.map(function (c, i) {
        return E.row('<span class="k">' + esc(c.text) + '</span>', { cur: i === S.choice });
      }).join('') + '</div>';
    }

    // the window primitive's own markup — .eb-win / .eb-wtitle / .eb-wbody —
    // hand-built only so the nameplate can carry the speaker's canon colour.
    var box =
      '<div class="eb-win" style="position:relative">' +
      (nm ? '<span class="eb-wtitle dlg-name" style="color:' + sp.color + '">' + esc(nm) + '</span>' : '') +
      '<div class="eb-wbody"><div class="dlg-text">' + body + '</div>' + choices + '</div>' +
      more + '</div>';

    // The framed thumbnail is the FALLBACK SHAPE and is emitted only when this
    // speaker has no cut-in: with one, the portrait is a sibling of the body
    // standing behind it, and the row must not also reserve a column for a plate.
    var bust = '';
    if (S.bust && !S.cutin) {
      var px = (defaults().bustPx || 190);
      bust = '<div class="eb-port big dlg-bust" style="width:' + px + 'px;height:' + px +
        'px;background-image:url(&quot;' + S.bust + '&quot;)"></div>';
    }
    // The fallback row obeys the same convention: a party thumbnail sits on the
    // right of the box, an NPC's on the left. Otherwise a speaker who has a cut-in
    // and one who does not would swap sides mid-conversation.
    var mine = S.side === 'right';

    var foot = S.mode === 'choice'
      ? '<b>&uarr;&darr;</b> choose &middot; <b>E/Enter</b> select'
      : (done ? '<b>E/Enter</b> continue' : '<b>E/Enter</b> skip');

    S.panel.set({
      html: '<div class="dlg-wrap">' + (mine ? '' : bust) +
        '<div class="dlg-col">' + box + '</div>' + (mine ? bust : '') + '</div>',
      foot: foot,
    });
    syncCutin();                                   // after the box exists to measure
  }

  // --------------------------------------------------------------- input ----
  function onKey(a) {
    if (!S) return;
    if (S.mode === 'choice') {
      if (a === 'up') { S.choice = U().cursor(S.avail.length, S.choice - 1); return render(); }
      if (a === 'down') { S.choice = U().cursor(S.avail.length, S.choice + 1); return render(); }
      if (a === 'confirm') {
        var c = S.avail[S.choice];
        if (!c) return;
        effects(c.effects);
        if (c.to) { if (!enter(c.to)) finish(); return; }
        return finish();
      }
      return;                                        // cancel does not skip a choice
    }
    // line mode: the FIRST press completes the typewriter, the second advances.
    // Skippable is a promise to the player; skipping straight past a line they
    // never saw is not.
    if (a === 'confirm' || a === 'cancel') {
      var l = S.lines[S.li];
      if (l && S.shown < l.text.length) { S.shown = l.text.length; return render(); }
      if (!nextLine()) finish();
    }
  }

  function finish() {
    if (!S) return;
    var p = S.panel;
    S.ending = true;
    if (p) p.close();                                 // onClose does the teardown
  }

  function teardown() {
    var s = S; S = null;
    if (s && s.timer) clearInterval(s.timer);
    var shop = pendingShop; pendingShop = null;
    if (s && s.resolve) s.resolve({ ended: true, node: s.nodeId, visited: s.visited });
    // the shop opens AFTER the greeting window is gone: one modal at a time, and
    // the keeper says hello before the counter does.
    if (shop && window.Shop && window.Shop.openShop) {
      setTimeout(function () { try { window.Shop.openShop(shop); } catch (e) { console.error('[Dialogue] shop handoff', e); } }, 40);
    }
  }

  // --------------------------------------------------------------- public ----
  function play(nodeId, opt) {
    opt = opt || {};
    if (!HAS_DOM || !U() || !U().HAS_DOM) return Promise.resolve(null);
    if (S) return Promise.resolve(null);                          // already talking
    return load().then(function (d) {
      if (!d) return null;
      if (S) return null;
      if (!resolve(nodeId)) return null;
      style();
      var done;
      var p = new Promise(function (res) { done = res; });
      S = { nodeId: null, node: null, lines: [], li: -1, shown: 0, mode: 'line',
            bust: null, cutin: null, cutinSrc: null, cutinEl: null, pid: null, side: 'left', geo: null,
            choice: 0, avail: [], visited: [], resolve: done, panel: null,
            cps: opt.cps || defaults().cps || DEF_CPS };
      // layout 'float' so the frame steps back and what floats over the world is
      // the window itself; the veil is re-classed to sit it on the floor of the
      // frame with no wash (see the CSS block).
      S.panel = U().panel({ name: 'dialogue', layout: 'float', onKey: onKey, onClose: teardown });
      if (!S.panel) { S = null; return null; }
      S.panel.el.classList.add('dlg');
      // THE WINDOW SITS ON THE FLOOR OF THE GAME FRAME, NOT THE BROWSER'S.
      // ui_kit's veil is position:fixed, which is right for the pause menu and
      // the shop because those are CENTRED — a taller browser window just moves
      // them a little. A dialogue box is bottom-anchored, and play3d's stage
      // (#s) is a 16:9 letterbox inside the page: fixed positioning dropped the
      // window into the black bar UNDER the game. Re-homing it to `absolute`
      // inside the stage puts it back on the frame's own floor, which is where
      // FF's box lives. Falls back to fixed on a page with no stage element.
      var host = S.panel.el.parentNode;
      if (host && host !== document.body && host.clientHeight > 0) {
        S.panel.el.style.position = 'absolute';
      }
      // The cut-in's one element, created before the first render so the first
      // line already has its portrait. onerror is the last fallback in the
      // chain: a manifest that outran the art on disk drops this speaker back to
      // the framed thumbnail instead of leaving a hole where a face should be.
      var art = document.createElement('img');
      art.className = 'dlg-cutin';
      art.alt = '';
      art.setAttribute('aria-hidden', 'true');
      art.onerror = function () {
        console.warn('[Dialogue] no cut-in art at ' + art.getAttribute('src') + ' — falling back to the bust');
        if (!S) return;
        if (CUT && S.pid) delete CUT[S.pid];
        S.cutin = null; S.cutinSrc = null;
        render();
      };
      S.cutinEl = art;
      S.panel.frame.appendChild(art);
      if (!enter(nodeId)) { finish(); return p; }
      var last = Date.now();
      S.timer = setInterval(function () {
        if (!S) return;
        // dt is UNCLAMPED on purpose. Chrome throttles a background tab's timers
        // to ~1 Hz, and every headless verification this project has lives in a
        // background tab; a clamp would make a two-second line take eight
        // seconds THERE and nowhere else, which is exactly the kind of bug that
        // only ever appears in the test. Elapsed time is the truth: a line the
        // player has been looking at for ten seconds is a finished line.
        var now = Date.now(), dt = (now - last) / 1000; last = now;
        if (S.mode !== 'line') return;
        var l = S.lines[S.li]; if (!l) return;
        if (S.shown >= l.text.length) return;
        S.shown = Math.min(l.text.length, S.shown + S.cps * dt);
        render();
      }, TICK_MS);
      return p;
    });
  }

  window.Dialogue = {
    load: load, play: play,
    node: node, speaker: speaker, check: check,
    close: function () { if (S) finish(); return true; },
    get isOpen() { return !!S; },
    get data() { return DATA; },
    // TEST/DEBUG surface — enough for a headless assert without reading the DOM
    debug: function () {
      return {
        open: !!S, node: S && S.nodeId, line: S ? S.li : null,
        of: S ? S.lines.length : null, mode: S && S.mode,
        text: S && S.lines[S.li] ? S.lines[S.li].text : null,
        shown: S ? Math.floor(S.shown) : null,
        typed: !!(S && S.lines[S.li] && S.shown >= S.lines[S.li].text.length),
        speaker: S && S.lines[S.li] ? S.lines[S.li].speaker : null,
        bust: S && S.bust, cutin: S && S.cutin,
        // WHICH PORTRAIT SHAPE IS ON SCREEN — the fact dialogue_test's cut-in
        // gate and any headless pass need, without reading the DOM.
        portrait: S ? (S.cutin ? 'cutin' : (S.bust ? 'thumbnail' : 'none')) : null,
        side: S ? S.side : null,
        players: players(),
        cutins: CUT ? Object.keys(CUT).length : 0,
        choices: S && S.mode === 'choice' ? S.avail.map(function (c) { return c.text; }) : null,
        choice: S && S.choice, locked: !!(U() && U().locked),
        nodes: DATA ? Object.keys(nodes()).length : 0,
      };
    },
    // TEST-ONLY: drive the window without a keyboard (rAF/keys are unavailable
    // in a headless pass, and this is the same idea as SIM.move/SIM.tick).
    key: function (a) { onKey(a); return this.debug(); },
    finishLine: function () { if (S && S.lines[S.li]) { S.shown = S.lines[S.li].text.length; render(); } return this.debug(); },
  };

  // INSURANCE, NOT A FEATURE. play3d's 'eb-scene' says a door just swapped the
  // world underneath us. This window should be structurally incapable of being up
  // when that happens — a panel holds UILOCK, phys() returns early under it, so
  // sgTick never arms an edge and transitionTo() is never reached. But the cost of
  // being wrong is the worst kind: a conversation with somebody who is no longer in
  // the scene, over a lock nothing will ever release, and the player cannot move.
  // So: close cleanly through the normal path (finish() -> panel.close() -> onClose
  // -> teardown), which releases the lock and resolves the caller's promise the way
  // an ordinary goodbye does. pendingShop is dropped first — a greeting that was
  // about to open a counter must not open the previous scene's counter in this one.
  // A no-op on every swap where the window was already closed, which is all of them.
  //
  // Guarded on addEventListener and not merely on `window`: the headless suites boot
  // these modules with globalThis AS window, and that object only grows a DOM when a
  // test asks for one — assuming otherwise takes a whole suite down at load.
  // A finished line stops calling render(), so nothing would re-measure the box
  // if the frame changed size while the player was reading. One listener, no-op
  // whenever the window is closed or the speaker has no cut-in.
  if (typeof window !== 'undefined' && window.addEventListener) {
    window.addEventListener('resize', function () { if (S) placeCutin(true); });
  }

  if (typeof window !== 'undefined' && window.addEventListener) {
    window.addEventListener('eb-scene', function () {
      try {
        if (!S) return;
        console.warn('[Dialogue] a scene swap fired with a window open — closing it');
        pendingShop = null;
        finish();
      } catch (e) { console.error('[Dialogue] eb-scene', e); }
    });
  }

  // Warm the data as soon as the store is up, so the first "Talk to Odessa"
  // opens instantly instead of on a fetch. Harmless without GS.
  if (window.GS && window.GS.ready && window.GS.ready.then) window.GS.ready.then(function () { load(); });
  else if (HAS_DOM) setTimeout(load, 0);
})();
