// battle_turnbased.js — window.Battle: BATTLE V1 (battle-core agent).
//
// THE ONLY THING THE REST OF THE GAME KNOWS:
//   Battle.start(spec, party, opts) -> Promise<result>
//   spec   {zone, group:[monsterId], seed, backdrop}
//   result {outcome:'victory'|'defeat'|'fled', xp, gold, drops:[itemId], turns,
//           partyHp:{charId:hp}, log:[events]}
//   Battle.active — true from the first frame of the entry fade to the last frame
//                   of the exit fade (the overworld freezes itself via UILOCK).
// Nothing else. No state leaks out, xp/gold/drops are REPORTED and never applied
// (GS.applyBattleResult is the world's job), so a real-time battle module can
// replace this file wholesale and the overworld cannot tell.
//
// WHAT LIVES HERE vs IN THE KERNEL: this file is PRESENTATION AND SEATS. Every
// number, the turn order, the damage roll, the scheduler and the AI live in
// battle_rules.js, which runs in node — so tools/battle_sim.mjs balance-tests the
// engine that ships rather than a copy of it. This file adds: the screen, the
// human decision menus, the fade, and the GS plumbing for the Item command.
//
// UI IDIOM: play3d's own HUD/prompt palette (warm off-white #e7ddd0 on near-black,
// #3a2c20 borders, #e9a24b accent, 8px radii, text-shadow 0 1px 2px #000) and the
// economy agent's EBUI key map, so battle keys are the same keys as every other
// panel in the game. EBUI's pure helpers are reused when present; its panel()
// factory is not (a centred 620-900px dialog is the wrong shape for a full-bleed
// battle screen, and innerHTML-swapping bodies cannot host in-flight animations).
(function () {
  'use strict';

  const HAS_DOM = typeof document !== 'undefined' && !!document.createElement;
  const EB = () => (typeof window !== 'undefined' ? window.EBUI : null);

  // ---- shared-kit helpers, with fallbacks so this module never hard-depends --
  const KEYMAP = {
    arrowup: 'up', w: 'up', arrowdown: 'down', s: 'down',
    arrowleft: 'left', a: 'left', arrowright: 'right', d: 'right',
    enter: 'confirm', e: 'confirm', ' ': 'confirm',
    escape: 'cancel', q: 'cancel', backspace: 'cancel',
  };
  function act(ev) {
    const k = EB();
    if (k && k.act) { try { return k.act(ev); } catch (e) { /* fall through */ } }
    return KEYMAP[String(ev.key).toLowerCase()] || null;
  }
  function esc(s) {
    const k = EB();
    if (k && k.esc) { try { return k.esc(s); } catch (e) { /* fall through */ } }
    return String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  }
  const wrapIdx = (n, i) => (n <= 0 ? 0 : ((i % n) + n) % n);
  const clamp01 = v => v < 0 ? 0 : v > 1 ? 1 : v;
  const wait = (ms) => ms > 0 ? new Promise(r => setTimeout(r, ms))     // setTimeout, not rAF:
                              : Promise.resolve();                      // rAF is throttled in background tabs

  // ---- UILOCK (coordinator-owned modal-input contract) ----------------------
  function lockWorld(on) {
    try {
      const L = window.UILOCK;
      if (L) { on ? L.lock('battle') : L.unlock('battle'); }
    } catch (e) { /* no contract on this page */ }
    try { if (window.SIM && window.SIM.keys) window.SIM.keys({}); } catch (e) { }
  }

  // ===== STYLE ==============================================================
  // One injected sheet, and it inherits: every colour, bevel and gauge comes
  // from ui_kit's :root custom properties and its .eb-win / .eb-cur / .eb-port
  // primitives. What lives here is BATTLE GEOMETRY only — the field, the two
  // bottom windows, the damage pop.
  //
  // LAYOUT (FF7/FF9): full-bleed backdrop; a small HUD window in the top corner;
  // monsters standing in the field with name tags; a slim log strip; and a
  // bottom band of TWO windows — the command list on the left, the party status
  // table on the right.
  const CSS = `
/* Scoped border-box: the bottom band is width:100% PLUS horizontal padding, and
   under content-box that overflows the root (which clips). Everything measured
   in this sheet is a border box. */
.ebb-root,.ebb-root *,.ebb-toast,.ebb-toast *{box-sizing:border-box}
.ebb-veil{position:fixed;inset:0;background:#000;z-index:26;pointer-events:none;opacity:0}
.ebb-root{position:fixed;inset:0;z-index:24;display:flex;flex-direction:column;
  overflow:hidden;color:var(--eb-ink);text-shadow:0 1px 2px #0009;
  font:14px/1.45 var(--eb-face);opacity:0;transition:opacity 160ms linear}
.ebb-root.on{opacity:1}
.ebb-bg{position:absolute;inset:0;z-index:0;background-size:cover;
  background-position:center bottom;background-repeat:no-repeat}
.ebb-vig{position:absolute;inset:0;z-index:1;pointer-events:none;
  background:radial-gradient(118% 86% at 50% 40%,#0000 34%,#000000b3 100%)}
/* the windows have to read over whatever art lands in assets/battle/ */
.ebb-scrim{position:absolute;left:0;right:0;bottom:0;height:52%;z-index:1;pointer-events:none;
  background:linear-gradient(180deg,#0000 0%,#0b070459 48%,#0b0704bf 100%)}

.ebb-top{position:relative;z-index:3;display:flex;gap:9px;align-items:flex-start;
  padding:12px min(4vw,44px) 0}
.ebb-hud{padding:6px 14px;display:flex;gap:15px;align-items:baseline;
  font-family:var(--eb-mono);font-size:11.5px;letter-spacing:.1em}
.ebb-hud .zone{color:var(--eb-amber-hi);font-weight:600;letter-spacing:.22em}
.ebb-hud .rnd{color:var(--eb-ink-faint)}
.ebb-seatwin{margin-left:auto;padding:6px 14px;font-family:var(--eb-mono);font-size:11.5px;
  color:var(--eb-ink-dim);letter-spacing:.1em;max-width:40vw;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap}
.ebb-seatwin:empty{display:none}

/* Foes STAND ON THE GROUND LINE, not in the middle of the void: aligning them
   to the bottom of the field leaves the empty space above them, where it reads
   as sky, and puts them just over the log strip the way FF does. */
.ebb-field{position:relative;z-index:3;flex:1 1 auto;min-height:0;display:flex;
  align-items:flex-end;justify-content:center;
  padding:min(2vh,20px) min(5vw,60px) min(6vh,54px)}
.ebb-foes{display:flex;align-items:flex-end;justify-content:center;
  gap:min(5vw,56px);flex-wrap:wrap}
.ebb-foe{position:relative;display:flex;flex-direction:column;align-items:center;gap:6px;
  transition:opacity 300ms linear,transform 300ms ease-in}
.ebb-foe.dead{opacity:0;transform:translateY(14px) scale(.9)}
/* the target caret: ui_kit's cursor glyph, turned to point down at the foe */
.ebb-mark{width:19px;height:15px;opacity:0;
  background:linear-gradient(180deg,var(--eb-amber-hi),var(--eb-amber) 55%,var(--eb-amber-dim));
  clip-path:polygon(28% 0,72% 0,72% 40%,100% 40%,50% 100%,0 40%,28% 40%);
  filter:drop-shadow(0 2px 3px #000b);animation:ebb-caret 820ms steps(2,jump-none) infinite}
.ebb-foe.cur .ebb-mark{opacity:1}
.ebb-sil{display:flex;align-items:flex-end;justify-content:center;
  filter:drop-shadow(0 10px 12px #000a);animation:ebb-bob 2.8s ease-in-out infinite}
.ebb-sil img{display:block;max-width:none}
.ebb-foe.cur .ebb-sil{filter:drop-shadow(0 10px 12px #000a) drop-shadow(0 0 7px #e9a24b99)}
.ebb-sil.hit{animation:ebb-hit 200ms linear}
.ebb-ftag{padding:2px 11px;border-radius:5px;font-size:12px;letter-spacing:.07em;
  color:var(--eb-ink-dim);white-space:nowrap;border:1px solid var(--eb-edge);
  background:linear-gradient(180deg,#2b2117e6,#191309f2);
  box-shadow:inset 1px 1px 0 #7d5f3966,inset -1px -1px 0 #0d080599}
.ebb-foe.cur .ebb-ftag{color:var(--eb-amber-hi);
  box-shadow:inset 1px 1px 0 #c08f4f99,inset -1px -1px 0 #0d0805,0 0 0 1px #e9a24b4d}
.ebb-fbar{width:76px;height:5px;border-radius:3px;background:#0f0b07cc;overflow:hidden;
  box-shadow:inset 0 1px 2px #000c,0 0 0 1px #7d5f3959}
.ebb-fbar>i{display:block;height:100%;background:var(--eb-hp);opacity:.82;
  transition:width 220ms linear}

/* ---- the damage pop: FF-sized, hard outline, one beat of overshoot -------- */
.ebb-num{position:absolute;left:50%;top:12%;transform:translateX(-50%);pointer-events:none;
  z-index:7;font:800 42px/1 var(--eb-mono);letter-spacing:-.02em;color:#fff6e6;
  text-shadow:2px 0 0 #180d05,-2px 0 0 #180d05,0 2px 0 #180d05,0 -2px 0 #180d05,
              2px 2px 0 #180d05,-2px 2px 0 #180d05,2px -2px 0 #180d05,-2px -2px 0 #180d05,
              0 6px 10px #000a;
  animation:ebb-pop 950ms cubic-bezier(.18,.85,.3,1) forwards}
.ebb-num.heal{color:#c8f2a1}
.ebb-num.crit{color:#ffcf88;font-size:54px}
.ebb-num.miss{color:#cdbfa9;font-size:26px;font-weight:700}
/* on a status ROW the number belongs over the portrait, not over the gauge */
.ebb-prow .ebb-num{left:62px;top:-38px;font-size:30px}
.ebb-prow .ebb-num.crit{font-size:36px}

/* ---- bottom furniture ---------------------------------------------------- */
.ebb-bottom{position:relative;z-index:3;flex:0 0 auto;display:flex;flex-direction:column;
  gap:8px;width:100%;max-width:1260px;margin:0 auto;
  padding:0 min(4vw,44px) max(18px,min(3.5vh,30px))}
.ebb-log{padding:8px 15px;min-height:2.6em;display:flex;align-items:center;gap:14px;
  font-size:14px}
.ebb-logtxt{flex:1 1 auto;min-width:0}
.ebb-logtxt em{color:var(--eb-amber-hi);font-style:normal;font-weight:600}
.ebb-hint{flex:0 0 auto;font-family:var(--eb-mono);font-size:11px;color:var(--eb-ink-faint);
  letter-spacing:.04em}
.ebb-hint b{color:var(--eb-ink-dim);font-weight:600}
.ebb-band{display:flex;gap:9px;align-items:stretch}
.ebb-cmdwin{position:relative;flex:0 0 min(216px,27vw);display:flex;flex-direction:column}
.ebb-cmds{padding:7px 8px 8px;display:flex;flex-direction:column;gap:2px;flex:1 1 auto}
.ebb-cmd{display:flex;align-items:center;gap:5px;padding:6px 8px;border-radius:5px;
  font:600 14px/1.1 var(--eb-face);letter-spacing:.11em;color:var(--eb-ink-dim);
  border:1px solid transparent}
.ebb-cmd.cur{color:var(--eb-amber-hi);border-color:#e9a24b4d;
  background:linear-gradient(90deg,#e9a24b33,#e9a24b12 72%,#e9a24b00)}
.ebb-cmds.idle .ebb-cmd{opacity:.38}
.ebb-cmds.idle .ebb-cmd.cur{opacity:.55}

.ebb-partywin{flex:1 1 auto;min-width:0;display:flex;flex-direction:column}
/* Name takes the slack; HP and MP are FIXED blocks pinned to the right, so the
   gauge never stretches into a runway on a wide screen (FF7's status window). */
.ebb-phead,.ebb-prow{display:grid;align-items:center;gap:12px;
  grid-template-columns:1.05em 40px minmax(0,1fr) 20em 4.4em}
.ebb-phead{padding:6px 14px 5px;border-bottom:1px solid var(--eb-rule);
  font:600 9.5px/1 var(--eb-face);letter-spacing:.22em;color:var(--eb-ink-faint)}
.ebb-phead .r{text-align:right}
.ebb-party{padding:5px 14px 8px;display:flex;flex-direction:column;gap:3px;flex:1 1 auto}
.ebb-prow{position:relative;padding:5px 0;border-radius:5px}
.ebb-prow.cur{background:linear-gradient(90deg,#e9a24b26,#e9a24b0a 70%,#e9a24b00);
  box-shadow:inset 0 0 0 1px #e9a24b3d}
.ebb-prow.down{opacity:.48}
.ebb-prow.hit{animation:ebb-hit 200ms linear}
.ebb-pname{min-width:0}
.ebb-pname b{display:block;font:600 14px/1.15 var(--eb-face);letter-spacing:.02em;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ebb-pname small{font:10px/1.45 var(--eb-mono);color:var(--eb-ink-faint);letter-spacing:.14em}
.ebb-php{display:flex;align-items:center;gap:10px;min-width:0}
.ebb-php .tk{flex:1 1 auto;min-width:28px;height:9px;border-radius:4px;background:var(--eb-track);
  overflow:hidden;box-shadow:inset 0 1px 2px #000c,0 1px 0 #6b512f55}
.ebb-php .tk>i{display:block;height:100%;border-radius:4px;background:var(--eb-hp);
  transition:width 220ms linear}
.ebb-php.low .tk>i{background:var(--eb-hp-low)}
.ebb-php .nm{flex:0 0 auto;font-family:var(--eb-mono);font-size:12.5px;
  font-variant-numeric:tabular-nums;color:var(--eb-ink-dim)}
.ebb-php .nm b{color:var(--eb-ink);font-weight:600}
/* MP is a RESERVED COLUMN — a dash until magic exists, so nothing shifts later */
.ebb-pmp{text-align:right;font-family:var(--eb-mono);font-size:12.5px;
  color:var(--eb-ink-faint);font-variant-numeric:tabular-nums}

.ebb-sub{position:absolute;left:0;bottom:calc(100% + 8px);min-width:min(260px,60vw);
  max-height:44vh;overflow:auto;display:none;z-index:6;padding:6px}
.ebb-sub.on{display:block}
.ebb-item{display:flex;gap:8px;align-items:center;padding:4px 8px;border-radius:5px;
  border:1px solid transparent;font-size:13.5px}
.ebb-item.cur{background:linear-gradient(90deg,#e9a24b2e,#e9a24b12 72%,#e9a24b00);
  border-color:#e9a24b4d}
.ebb-item.cur .k{color:var(--eb-amber-hi)}
.ebb-item.dim{color:var(--eb-ink-faint)}
.ebb-item .k{flex:1 1 auto;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ebb-item .n{flex:0 0 auto;font-family:var(--eb-mono);font-size:12.5px;color:var(--eb-ink-dim)}

.ebb-outro{position:absolute;inset:0;z-index:8;display:flex;align-items:center;
  justify-content:center;background:#00000073;
  backdrop-filter:blur(2px);-webkit-backdrop-filter:blur(2px)}
.ebb-obox{min-width:min(440px,82vw);overflow:hidden}
.ebb-ohead{display:block;padding:9px 17px;font:600 15px/1.2 var(--eb-face);letter-spacing:.22em;
  text-transform:uppercase;color:var(--eb-amber-hi);background:var(--eb-win-head);
  border-bottom:1px solid var(--eb-rule);border-radius:6px 6px 0 0}
.ebb-obody{padding:11px 17px}
.ebb-orow{display:flex;gap:10px;padding:3px 0;font-size:13.5px}
.ebb-orow .n{margin-left:auto;font-family:var(--eb-mono);color:var(--eb-amber-hi);
  font-variant-numeric:tabular-nums}
.ebb-ofoot{padding:7px 17px;border-top:1px solid var(--eb-rule);background:var(--eb-win-head);
  font-family:var(--eb-mono);font-size:11px;color:var(--eb-ink-faint);letter-spacing:.1em;
  border-radius:0 0 6px 6px}
.ebb-toast{position:fixed;left:50%;top:12%;transform:translateX(-50%);z-index:27;
  padding:7px 17px;color:var(--eb-ink);font:13.5px var(--eb-face);text-shadow:0 1px 2px #000;
  opacity:0;transition:opacity 180ms linear;pointer-events:none}
.ebb-toast.on{opacity:1}

@keyframes ebb-bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-5px)}}
@keyframes ebb-caret{0%,100%{transform:translateY(0)}50%{transform:translateY(3px)}}
@keyframes ebb-hit{0%,100%{transform:translateX(0)}25%{transform:translateX(-7px)}
  75%{transform:translateX(7px)}}
@keyframes ebb-pop{
  0%{opacity:0;transform:translate(-50%,10px) scale(.55)}
  14%{opacity:1;transform:translate(-50%,-9px) scale(1.3)}
  28%{transform:translate(-50%,-13px) scale(1)}
  70%{opacity:1}
  100%{opacity:0;transform:translate(-50%,-60px) scale(.98)}}
/* reduced motion kills the idle bob, the caret bob and the hit shake, but NEVER
   the damage number: it carries information, so it still rises and fades. */
@media (prefers-reduced-motion:reduce){
  .ebb-sil,.ebb-sil.hit,.ebb-prow.hit,.ebb-mark{animation:none}}`;
  let styled = false;
  function style() {
    if (styled || !HAS_DOM) return;
    styled = true;
    // the shared kit first, so :root's custom properties exist before this sheet
    // reads them. On a page with no ui_kit (isolated harness) we plant the few
    // properties this sheet actually needs, so the battle never renders unstyled.
    let kit = false;
    try { if (EB() && EB().style) { EB().style(); kit = true; } } catch (e) { }
    if (!kit) {
      const f = document.createElement('style');
      f.id = 'ebb-fallback-vars';
      f.textContent = ':root{--eb-ink:#ece0d0;--eb-ink-dim:#b6a68f;--eb-ink-faint:#82735f;' +
        '--eb-amber:#e9a24b;--eb-amber-hi:#ffd39a;--eb-amber-dim:#a8763a;' +
        '--eb-win:linear-gradient(180deg,#2b2117f2,#191309fa);' +
        '--eb-win-head:linear-gradient(180deg,#3d2e1ff2,#2c2115f7);' +
        '--eb-bevel-lt:#7d5f39;--eb-bevel-dk:#0d0805;--eb-edge:#090603;--eb-rule:#4a3823;' +
        '--eb-track:#0f0b07;--eb-hp:linear-gradient(180deg,#f3c079,#b96f24);' +
        '--eb-hp-low:linear-gradient(180deg,#f0a48d,#a94328);' +
        '--eb-face:system-ui,sans-serif;--eb-mono:ui-monospace,Menlo,monospace}' +
        '.eb-win{border-radius:8px;border:1px solid var(--eb-edge);background:var(--eb-win);' +
        'box-shadow:inset 2px 2px 0 var(--eb-bevel-lt),inset -2px -2px 0 var(--eb-bevel-dk),' +
        'inset 0 0 0 3px #0000002e,0 10px 30px #000a}' +
        '.eb-cur{flex:0 0 1.05em;display:inline-block;width:1.05em;height:1em}' +
        '.eb-cur.on{background:var(--eb-amber);' +
        'clip-path:polygon(0 30%,45% 30%,45% 8%,100% 50%,45% 92%,45% 70%,0 70%)}';
      document.head.appendChild(f);
    }
    const s = document.createElement('style');
    s.id = 'ebb-style'; s.textContent = CSS;
    document.head.appendChild(s);
  }

  // ===== SWAPPABLE ART LOOKUPS ==============================================
  // BACKDROPS: keyed by encounters.json `battleBackdrop`. A value is either a CSS
  // background string or a function(ctx) returning one (or an element to mount) —
  // so replacing a placeholder gradient with a pre-rendered PNG, or with a canvas
  // that animates, is ONE TABLE ENTRY and touches nothing else in this file.
  const backdrops = {
    meadow: 'radial-gradient(60% 40% at 50% 26%,#ffe6b83d 0%,#0000 70%),' +
            'linear-gradient(180deg,#a9c3d4 0%,#d9cfae 33%,#cbbf95 46%,#6f8046 47%,#55643a 70%,#2b3220 100%)',
    forest: 'radial-gradient(45% 32% at 62% 16%,#ffe6b833 0%,#0000 70%),' +
            'linear-gradient(180deg,#22301f 0%,#3c4b33 24%,#2f3a27 47%,#28331f 48%,#131b0e 100%)',
    crag:   'radial-gradient(60% 40% at 42% 22%,#ffd9a83a 0%,#0000 70%),' +
            'linear-gradient(180deg,#c9c0a8 0%,#b39a72 30%,#8d6f4d 46%,#6a4f37 47%,#3b2a1d 100%)',
    water:  'radial-gradient(60% 40% at 50% 24%,#cfe8f03a 0%,#0000 70%),' +
            'linear-gradient(180deg,#9fc0cf 0%,#cfd9cf 30%,#4d8496 47%,#2f6072 48%,#173540 100%)',
    default:'linear-gradient(180deg,#3b3630 0%,#2a2620 48%,#171410 100%)',
  };
  // SILHOUETTES: keyed by monsters.json `family`, so a new monster of a known
  // family needs no code. These are now the FALLBACK — the shape a creature
  // wears until (or unless) a sprite file resolves for it. `artH` is the height
  // the sprite is drawn at: FF9 proportions, i.e. every monster reads bigger
  // than the 40px busts in the status window.
  const sprites = {
    nibbler: { w: 92, h: 68, artH: 160, lit: '#c8b877', dark: '#6c5f34', radius: '52% 52% 46% 46%' },
    sprite:  { w: 56, h: 76, artH: 148, lit: '#bfe9f2', dark: '#3f8ea6', clip: 'polygon(50% 0,100% 46%,50% 100%,0 46%)' },
    duskpad: { w: 104, h: 72, artH: 190, lit: '#8b7f92', dark: '#413a4c',
               clip: 'polygon(4% 100%,9% 44%,24% 26%,46% 22%,70% 30%,88% 24%,96% 42%,98% 100%,78% 100%,74% 70%,28% 70%,24% 100%)' },
    shade:   { w: 88, h: 84, artH: 194, lit: '#6a5a78', dark: '#2c2436',
               clip: 'polygon(50% 0,62% 20%,84% 12%,76% 36%,100% 50%,78% 62%,88% 88%,58% 78%,50% 100%,40% 78%,14% 90%,22% 62%,0 50%,24% 36%,16% 12%,38% 20%)' },
    shell:   { w: 112, h: 62, artH: 180, lit: '#c3a173', dark: '#6b4f31', radius: '54% 54% 14% 14%' },
    eel:     { w: 118, h: 52, artH: 180, lit: '#79c9ae', dark: '#2f6a58',
               clip: 'polygon(0 44%,28% 16%,62% 30%,100% 4%,88% 52%,100% 96%,58% 72%,26% 88%)' },
    default: { w: 84, h: 70, artH: 172, lit: '#a2957f', dark: '#4b4237', radius: '48%' },
  };

  // ---- ART PATHS: convention, not a list -----------------------------------
  // Both lookups are "id -> path" with a base + extension convention and an
  // explicit override map for the exceptions. Nothing here enumerates zones or
  // monsters, so a new zone or a new monster needs no code — drop the file in
  // and it is picked up; leave it out and the gradient/shape fallback holds.
  //   backdrop  spec.backdrop (encounters.json battleBackdrop) -> assets/battle/<key>.png
  //   monster   monsters.json id                 -> assets/monsters/placeholder/<id>.png
  // Both are probed with an Image() and applied only ON LOAD, so a missing file
  // is silent and costs one 404 — never a broken image box, never a blank screen.
  const art = {
    base: 'assets/',                 // mutable, so a mock harness can re-root it
    backdropDir: 'battle/',
    monsterDir: 'monsters/placeholder/',
    ext: '.png',
    backdrop: {},                    // key -> explicit path (overrides the convention)
    monster: {},                     // monsterId -> explicit path
    enabled: true,                   // set false to force the gradient/shape look
  };
  const cleanId = s => String(s == null ? '' : s).replace(/[^a-z0-9_-]/gi, '');
  function backdropUrl(key) {
    if (!art.enabled || !key) return null;
    if (art.backdrop[key]) return art.backdrop[key];
    const k = cleanId(key); return k ? art.base + art.backdropDir + k + art.ext : null;
  }
  function monsterUrl(id) {
    if (!art.enabled || !id) return null;
    if (art.monster[id]) return art.monster[id];
    const k = cleanId(id); return k ? art.base + art.monsterDir + k + art.ext : null;
  }

  function bgFor(key, ctx) {
    let v = backdrops[key];
    if (v === undefined) v = backdrops.default;
    if (typeof v === 'function') { try { v = v(ctx); } catch (e) { v = backdrops.default; } }
    return v;
  }
  // The gradient goes on FIRST and unconditionally — it is the floor, and it is
  // what every zone looks like until its plate is baked. The image replaces the
  // gradient's layer only once it has actually decoded.
  function paintBackdrop(el, key, ctx) {
    el.style.background = bgFor(key, ctx);
    const url = backdropUrl(key);
    if (!url || typeof Image !== 'function') return;
    const im = new Image();
    im.onload = () => {
      if (!el.parentNode) return;
      el.style.backgroundImage = 'url("' + url + '")';
      el.classList.add('img');
    };
    im.onerror = () => { /* no plate for this zone yet — the gradient stands */ };
    im.src = url;
  }
  // Pixel art (a small source) is snapped to an INTEGER scale and rendered
  // nearest-neighbour; anything bigger is treated as painted art and scaled
  // freely. One rule, so replacing the 16px placeholders with real plates needs
  // no code change.
  function fitSprite(img, targetH) {
    const nh = img.naturalHeight || targetH, nw = img.naturalWidth || targetH;
    let k = targetH / nh;
    if (nh <= 64) { k = Math.max(1, Math.round(k)); img.style.imageRendering = 'pixelated'; }
    img.style.width = Math.round(nw * k) + 'px';
    img.style.height = Math.round(nh * k) + 'px';
  }

  // ===== THE SCREEN =========================================================
  // Owns DOM and nothing else: it renders events, runs the cursor, and resolves
  // one action per request. It never computes a number and never reads GS
  // directly (the bag adapter does that), so a different screen is a drop-in.
  function makeScreen(cfg) {
    style();
    const host = document.body;
    const S = {
      speed: cfg.speed == null ? 1 : cfg.speed,
      nodes: {},                 // combatantId -> {el, sil, fill, txt}
      pending: null,             // the live decision request
      state: cfg.state,
      round: 0,
      cmds: ['Attack', 'Item', 'Flee'],
    };

    const root = document.createElement('div');
    root.className = 'ebb-root';
    root.innerHTML =
      '<div class="ebb-bg"></div><div class="ebb-vig"></div><div class="ebb-scrim"></div>' +
      '<div class="ebb-top">' +
        '<div class="eb-win ebb-hud"><span class="zone"></span><span class="rnd"></span></div>' +
        '<div class="eb-win ebb-seatwin seat"></div>' +
      '</div>' +
      '<div class="ebb-field"><div class="ebb-foes"></div></div>' +
      '<div class="ebb-bottom">' +
        '<div class="eb-win ebb-log"><span class="ebb-logtxt"></span>' +
          '<span class="ebb-hint"></span></div>' +
        '<div class="ebb-band">' +
          '<div class="eb-win ebb-cmdwin"><span class="eb-wtitle">Command</span>' +
            '<div class="ebb-cmds idle"></div><div class="eb-win ebb-sub"></div></div>' +
          '<div class="eb-win ebb-partywin">' +
            '<div class="ebb-phead"><span></span><span></span><span>PARTY</span>' +
              '<span>HP</span><span class="r">MP</span></div>' +
            '<div class="ebb-party"></div>' +
          '</div>' +
        '</div>' +
      '</div>';
    host.appendChild(root);
    const q = (c) => root.querySelector('.ebb-' + c);
    const qq = (c) => root.querySelector('.' + c);

    paintBackdrop(q('bg'), cfg.backdrop, cfg);
    qq('zone').textContent = (cfg.zone || 'battle').toUpperCase();
    q('hint').innerHTML = '<b>WASD/&larr;&uarr;&darr;&rarr;</b> move &middot; ' +
      '<b>E/Enter</b> confirm &middot; <b>Esc/Q</b> back';

    // --- build combatant nodes ---
    // The shape is built FIRST and is what shows if no sprite resolves; the
    // sprite quietly takes its place once it decodes. Missing art degrades to
    // the old look rather than to a hole.
    function silEl(family, monsterId, i) {
      const d = sprites[family] || sprites.default;
      const wrap = document.createElement('div');
      wrap.className = 'ebb-sil';
      wrap.style.animationDelay = (i * 0.37).toFixed(2) + 's';
      const shape = document.createElement('div');
      shape.style.width = d.w + 'px'; shape.style.height = d.h + 'px';
      shape.style.background = 'linear-gradient(165deg,' + d.lit + ' 0%,' + d.dark + ' 78%)';
      if (d.clip) shape.style.clipPath = d.clip;
      if (d.radius) shape.style.borderRadius = d.radius;
      wrap.appendChild(shape);
      const url = monsterUrl(monsterId);
      if (url && typeof Image === 'function') {
        const img = new Image();
        img.alt = '';
        img.onload = () => {
          if (!wrap.parentNode) return;
          fitSprite(img, d.artH || sprites.default.artH);
          wrap.replaceChild(img, shape);
        };
        img.onerror = () => { /* no plate for this monster — the shape stands */ };
        img.src = url;
      }
      return wrap;
    }
    const foesBox = q('foes'), partyBox = q('party');
    (cfg.state.foes || []).forEach((c, i) => {
      const el = document.createElement('div');
      el.className = 'ebb-foe';
      const mark = document.createElement('div'); mark.className = 'ebb-mark';
      const sil = silEl(cfg.familyOf ? cfg.familyOf(c.ref) : 'default', c.ref, i);
      const name = document.createElement('div'); name.className = 'ebb-ftag'; name.textContent = c.name;
      const bar = document.createElement('div'); bar.className = 'ebb-fbar';
      const fill = document.createElement('i'); fill.style.width = '100%'; bar.appendChild(fill);
      el.appendChild(mark); el.appendChild(sil); el.appendChild(name);
      if (Battle.showFoeHp) el.appendChild(bar);
      foesBox.appendChild(el);
      S.nodes[c.id] = { el: el, sil: sil, fill: fill, txt: null, name: name };
    });
    // THE PARTY STATUS TABLE: one row per member — bust, name/level, HP gauge
    // with numerals, and the reserved MP column.
    (cfg.state.party || []).forEach((c) => {
      const el = document.createElement('div');
      el.className = 'ebb-prow';
      const bust = cfg.bustFor ? cfg.bustFor(c.ref || c.id) : null;
      el.innerHTML = '<span class="eb-cur"></span>' +
        '<div class="eb-port ebb-pport" style="width:40px;height:40px' +
          (bust ? ';background-image:url(&quot;' + bust + '&quot;)' : '') + '"></div>' +
        '<div class="ebb-pname"><b></b><small></small></div>' +
        '<div class="ebb-php"><span class="tk"><i></i></span>' +
          '<span class="nm"><b class="hp"></b>/<span class="mx"></span></span></div>' +
        '<div class="ebb-pmp">—</div>';
      el.querySelector('.ebb-pname b').textContent = c.name;
      el.querySelector('.ebb-pname small').textContent = 'LV ' + (c.level || 1);
      if (!bust) el.querySelector('.ebb-pport').classList.add('miss');
      partyBox.appendChild(el);
      S.nodes[c.id] = { el: el, sil: el, fill: el.querySelector('.ebb-php .tk>i'),
                        txt: el.querySelector('.ebb-php .nm'), bar: el.querySelector('.ebb-php'),
                        cursor: el.querySelector('.eb-cur') };
    });

    // --- rendering ---
    function nameOf(id) {
      const c = window.Rules.findById(S.state, id);
      return c ? c.name : id;
    }
    function syncHp(state) {
      S.state = state || S.state;
      for (const c of S.state.party.concat(S.state.foes)) {
        const n = S.nodes[c.id]; if (!n) continue;
        const f = clamp01(c.maxHp ? c.hp / c.maxHp : 0);
        n.fill.style.width = (f * 100).toFixed(1) + '%';
        if (n.txt) {
          // the numerals are two elements (current bright, max dim), so this
          // writes the parts rather than the whole string
          const cur = n.txt.querySelector('.hp'), mx = n.txt.querySelector('.mx');
          if (cur && mx) { cur.textContent = c.hp; mx.textContent = c.maxHp; }
          else n.txt.textContent = c.hp + '/' + c.maxHp;
        }
        if (n.bar) n.bar.classList.toggle('low', f <= 0.3);
        if (c.side === 'foe') n.el.classList.toggle('dead', !!c.dead);
        else n.el.classList.toggle('down', !!c.dead);
      }
      qq('rnd').textContent = 'ROUND ' + S.round;
    }
    function logLine(html) { q('logtxt').innerHTML = html; }
    function floatNum(id, text, kind) {
      const n = S.nodes[id]; if (!n) return;
      const e = document.createElement('div');
      e.className = 'ebb-num' + (kind ? ' ' + kind : '');
      e.textContent = text;
      n.el.style.position = 'relative';
      n.el.appendChild(e);
      setTimeout(() => { if (e.parentNode) e.parentNode.removeChild(e); }, 1000);
    }
    function hitShake(id) {
      const n = S.nodes[id]; if (!n) return;
      n.sil.classList.remove('hit'); void n.sil.offsetWidth; n.sil.classList.add('hit');
    }

    // --- the event feed (this is what makes `emit` awaited in the kernel) -----
    async function play(events, state) {
      for (const ev of events) {
        S.state = state || S.state;
        switch (ev.t) {
          case 'round':
            S.round = ev.n; syncHp(state); break;
          case 'action':
            if (ev.kind === 'attack') logLine('<em>' + esc(nameOf(ev.by)) + '</em> attacks.');
            else if (ev.kind === 'item') logLine('<em>' + esc(nameOf(ev.by)) + '</em> uses ' + esc(cfg.itemName(ev.item)) + '.');
            else if (ev.kind === 'flee') logLine('<em>' + esc(nameOf(ev.by)) + '</em> tries to flee…');
            else logLine('<em>' + esc(nameOf(ev.by)) + '</em> ' + esc(ev.kind) + 's.');
            await wait(170 * S.speed);
            break;
          case 'damage':
            syncHp(state); hitShake(ev.target);
            // amber for a crit if the kernel ever emits one; plain white otherwise
            floatNum(ev.target, String(ev.amount), ev.crit ? 'crit' : '');
            logLine('<em>' + esc(nameOf(ev.target)) + '</em> takes ' + ev.amount + ' damage.');
            await wait(400 * S.speed);
            break;
          case 'heal':
            syncHp(state); floatNum(ev.target, '+' + ev.amount, 'heal');
            logLine('<em>' + esc(nameOf(ev.target)) + '</em> recovers ' + ev.amount + ' HP.');
            await wait(380 * S.speed);
            break;
          case 'ko':
            syncHp(state);
            logLine('<em>' + esc(nameOf(ev.id)) + '</em> ' + (ev.side === 'foe' ? 'is defeated.' : 'falls.'));
            await wait(300 * S.speed);
            break;
          case 'flee':
            logLine(ev.ok ? 'Got away safely!' : 'Cornered — no escape!');
            await wait(400 * S.speed);
            break;
          case 'noop':
            if (ev.why === 'round-cap') logLine('The fight breaks off.');
            break;
          case 'end':
            syncHp(state); break;
        }
      }
      syncHp(state);
    }

    // --- the decision cursor -------------------------------------------------
    // One request at a time per screen; a second seat would get its own cursor
    // object (the scheduler already collects seats concurrently).
    function promptAction(actorId, state, api) {
      S.state = state;
      return new Promise((resolve) => {
        S.pending = { actorId, api, resolve, mode: 'cmd', ci: 0, ti: 0, ii: 0, items: [] };
        for (const c of state.party) markActor(c.id, c.id === actorId);
        qq('seat').textContent = (api && api.seatName ? api.seatName.toUpperCase() + ' · ' : '') +
          nameOf(actorId);
        renderMenu();
      });
    }
    function livingFoes() { return S.state.foes.filter(c => !c.dead); }
    // the status row that is deciding gets the cursor glyph, exactly like a
    // menu row — one cursor grammar across the whole game
    function markActor(id, on) {
      const n = S.nodes[id]; if (!n) return;
      n.el.classList.toggle('cur', !!on);
      if (n.cursor) n.cursor.classList.toggle('on', !!on);
    }
    function renderMenu() {
      const p = S.pending;
      const cmds = q('cmds'), sub = q('sub');
      cmds.classList.toggle('idle', !p);
      // vertical command list with the pointing cursor, FF-style
      cmds.innerHTML = S.cmds.map((c, i) => {
        const on = !!(p && p.ci === i);
        return '<div class="ebb-cmd' + (on ? ' cur' : '') + '">' +
          '<span class="eb-cur' + (on ? ' on' : '') + '"></span>' + esc(c) + '</div>';
      }).join('');
      if (!p) { sub.classList.remove('on'); markFoe(-1); return; }
      if (p.mode === 'target') {
        sub.classList.remove('on');
        const fs = livingFoes();
        markFoe(fs.length ? fs[wrapIdx(fs.length, p.ti)].id : -1);
        logLine('Attack which?');
      } else if (p.mode === 'items') {
        markFoe(-1);
        sub.classList.add('on');
        sub.innerHTML = p.items.length
          ? p.items.map((it, i) => '<div class="ebb-item' + (p.ii === i ? ' cur' : '') +
              (it.count > 0 ? '' : ' dim') + '"><span class="eb-cur' + (p.ii === i ? ' on' : '') +
              '"></span><span class="k">' + esc(it.name) + '</span><span class="n">&times;' +
              it.count + '</span></div>').join('')
          : '<div class="ebb-item dim"><span class="eb-cur"></span>' +
            '<span class="k">no usable items</span></div>';
        logLine('Use what?');
      } else {
        sub.classList.remove('on'); markFoe(-1);
        logLine('<em>' + esc(nameOf(p.actorId)) + '</em> — what will you do?');
      }
    }
    function markFoe(id) {
      for (const c of S.state.foes) {
        const n = S.nodes[c.id]; if (n) n.el.classList.toggle('cur', c.id === id);
      }
    }
    function settle(action) {
      const p = S.pending; if (!p) return;
      S.pending = null;
      for (const c of S.state.party) markActor(c.id, false);
      markFoe(-1);
      renderMenu();
      p.resolve(action);
    }
    // returns true if the key was consumed
    function onKey(a) {
      const p = S.pending;
      if (S.outro) { if (a === 'confirm' || a === 'cancel') { const f = S.outro; S.outro = null; f(); } return true; }
      if (!p) return true;                       // battle is resolving: swallow, never leak to the world
      const step = (a === 'down' || a === 'right') ? 1 : (a === 'up' || a === 'left') ? -1 : 0;
      if (p.mode === 'cmd') {
        if (step) { p.ci = wrapIdx(S.cmds.length, p.ci + step); renderMenu(); return true; }
        if (a === 'confirm') {
          if (p.ci === 0) { p.mode = 'target'; p.ti = 0; }
          else if (p.ci === 1) { p.items = p.api.bag.list(); p.mode = 'items'; p.ii = 0; }
          else { settle({ type: 'flee', by: p.actorId }); return true; }
          renderMenu(); return true;
        }
        return true;
      }
      if (p.mode === 'target') {
        const fs = livingFoes();
        if (step) { p.ti = wrapIdx(fs.length, p.ti + step); renderMenu(); return true; }
        if (a === 'cancel') { p.mode = 'cmd'; renderMenu(); return true; }
        if (a === 'confirm') {
          if (!fs.length) { p.mode = 'cmd'; renderMenu(); return true; }
          settle({ type: 'attack', by: p.actorId, target: fs[wrapIdx(fs.length, p.ti)].id });
          return true;
        }
        return true;
      }
      if (p.mode === 'items') {
        if (step) { p.ii = wrapIdx(p.items.length, p.ii + step); renderMenu(); return true; }
        if (a === 'cancel') { p.mode = 'cmd'; renderMenu(); return true; }
        if (a === 'confirm') {
          const it = p.items[p.ii];
          if (!it || it.count <= 0) return true;
          // party-of-N: a second living member opens a target step. v1 has one.
          const targets = S.state.party.filter(c => !c.dead);
          const tgt = targets.length === 1 ? targets[0].id : (targets[0] && targets[0].id);
          if (!p.api.bag.use(it.id)) { logLine('None left.'); return true; }
          settle({ type: 'item', by: p.actorId, target: tgt, item: it.id, effect: it.effect });
          return true;
        }
        return true;
      }
      return true;
    }

    // --- outro ---------------------------------------------------------------
    function outro(result) {
      const titles = { victory: 'Victory', defeat: 'Defeated', fled: 'Escaped' };
      const box = document.createElement('div');
      box.className = 'ebb-outro';
      const drops = (result.drops || []).map(id => cfg.itemName(id));
      const rows = [];
      if (result.outcome === 'victory') {
        rows.push(['Experience', result.xp]);
        rows.push(['Gold', result.gold]);
        if (drops.length) rows.push(['Found', drops.join(', ')]);
      }
      rows.push(['Rounds', result.turns]);
      box.innerHTML = '<div class="eb-win ebb-obox"><span class="ebb-ohead">' +
        esc(titles[result.outcome] || result.outcome) + '</span><div class="ebb-obody">' +
        rows.map(r => '<div class="ebb-orow"><span>' + esc(r[0]) + '</span><span class="n">' +
          esc(r[1]) + '</span></div>').join('') +
        '</div><div class="ebb-ofoot">ENTER TO CONTINUE</div></div>';
      root.appendChild(box);
      logLine('');
      if (cfg.autoConfirm) return wait(700 * S.speed);
      return new Promise((resolve) => {
        S.outro = resolve;
        // never strand a player on a summary screen if a key event is eaten
        setTimeout(() => { if (S.outro === resolve) { S.outro = null; resolve(); } }, 30000);
      });
    }

    return {
      el: root, play, promptAction, onKey, outro, syncHp,
      show() { root.classList.add('on'); },
      destroy() { if (root.parentNode) root.parentNode.removeChild(root); },
      _state() { return S; },
    };
  }

  // ===== INPUT ==============================================================
  // ONE capture-phase listener for the page lifetime, gated on Battle.active.
  // Capture on window runs before play3d's bubble-phase handlers, so while a
  // battle is up the world cannot see a keystroke — belt and braces with UILOCK,
  // and it wins the registration race against any other capture listener as long
  // as this file loads first.
  let wired = false, screenRef = null;
  function wire() {
    if (wired || !HAS_DOM) return; wired = true;
    const swallow = (ev) => {
      if (!Battle.active) return;
      ev.stopImmediatePropagation();
      ev.preventDefault();
    };
    window.addEventListener('keydown', (ev) => {
      if (!Battle.active) return;
      ev.stopImmediatePropagation();
      ev.preventDefault();
      if (!screenRef) return;
      const a = act(ev);
      if (a) { try { screenRef.onKey(a); } catch (e) { console.error('[Battle] key', e); } }
    }, true);
    window.addEventListener('keyup', swallow, true);
    window.addEventListener('keypress', swallow, true);
  }

  // ===== FADE ===============================================================
  // Battle owns its veil: play3d's sgFade is module-internal. Same duration and
  // easing as the scene-graph transition so a cut to battle feels like a cut to a
  // shot. opts.fade lets a caller (or a future in-place transition layer) supply
  // its own.
  const FADE_MS = 350;
  let veil = null;
  function veilEl() {
    if (veil) return veil;
    style();
    veil = document.createElement('div');
    veil.className = 'ebb-veil';
    document.body.appendChild(veil);
    return veil;
  }
  function fadeTo(to, ms) {
    if (!HAS_DOM) return Promise.resolve();
    ms = ms == null ? FADE_MS : ms;
    const v = veilEl();
    v.style.transition = 'opacity ' + ms + 'ms linear';
    v.style.opacity = String(to);
    return wait(ms + 20);
  }

  // ===== BAG ADAPTER ========================================================
  // The one place a battle touches the inventory. Items are consumed through GS
  // immediately (a fled or lost battle must still have spent its tonics) but the
  // HEAL is applied inside the battle state, never through GS.useItem — in-battle
  // HP is battle state and is written back once, via result.partyHp.
  function makeBag(gs, itemsMap, override) {
    if (override) return override;
    return {
      list() {
        const out = [];
        if (!gs || !gs.state) return out;
        for (const id in gs.state.inventory) {
          const d = itemsMap[id];
          if (!d || d.type !== 'consumable' || !d.effect) continue;
          out.push({ id, name: d.name || id, count: gs.state.inventory[id], effect: Object.assign({}, d.effect) });
        }
        out.sort((a, b) => (a.name < b.name ? -1 : a.name > b.name ? 1 : 0));
        return out;
      },
      use(id) { return gs && gs.removeItem ? gs.removeItem(id) : true; },
      count(id) { return gs && gs.count ? gs.count(id) : 0; },
    };
  }

  // ===== TOAST (level-up pings etc; used by encounters.js) ==================
  let toastEl = null, toastT = 0;
  function toast(text, ms) {
    if (!HAS_DOM) return;
    style();
    if (!toastEl) { toastEl = document.createElement('div'); toastEl.className = 'ebb-toast'; document.body.appendChild(toastEl); }
    toastEl.textContent = text;
    toastEl.classList.add('on');
    clearTimeout(toastT);
    toastT = setTimeout(() => { if (toastEl) toastEl.classList.remove('on'); }, ms || 2600);
  }

  // ===== THE CONTRACT =======================================================
  const Battle = window.Battle = {
    version: 1,
    active: false,
    showFoeHp: true,      // classic FF hides it; on by default while art is placeholder
    backdrops, sprites,   // swappable lookups, mutable by anyone
    art,                  // path convention for backdrop plates + monster sprites
    router: null,         // the LIVE router of the running battle (remap mid-battle)
    scheduler: null,      // the policy object in use
    last: null,           // last result (debug)
    toast,

    // ---- Battle.start(spec, party, opts) -> Promise<result> ----------------
    async start(spec, party, opts) {
      opts = opts || {};
      const RU = window.Rules;
      if (!RU) { console.warn('[Battle] battle_rules.js not loaded — battle skipped'); return null; }
      if (Battle.active) { console.warn('[Battle] already running'); return null; }
      spec = spec || {};

      const gs = opts.gs !== undefined ? opts.gs : (typeof window !== 'undefined' ? window.GS : null);
      const data = (gs && gs.data) || {};
      const monstersMap = opts.monsters || (data.monsters && data.monsters.monsters) || {};
      const itemsMap = opts.items || (data.items && data.items.items) || {};
      const growth = opts.growth || data.growth;

      // party: given, else derived from GS (so a console one-liner works)
      let members = party;
      if (!members && gs && gs.ok && growth) {
        members = gs.activeParty().map(ch => RU.derive.partyMember(growth, itemsMap, ch));
      }
      members = (members || []).filter(m => m && m.hp > 0);
      if (!members.length) { console.warn('[Battle] no living party — battle skipped'); return null; }

      const group = (spec.group || []).filter(id => monstersMap[id]);
      if (!group.length) { console.warn('[Battle] empty monster group — battle skipped'); return null; }

      const seed = (spec.seed != null ? spec.seed : RU.hashSeed(spec.zone || '', group.join(','))) >>> 0;
      const rng = RU.mulberry32(seed);
      const state0 = RU.makeState({ party: members, foes: RU.derive.foesFromGroup(monstersMap, group) });

      Battle.active = true;              // set BEFORE the first await: the phys() freeze is immediate
      lockWorld(true);
      wire();

      const log = [];
      const speed = opts.speed == null ? 1 : opts.speed;
      const headless = !HAS_DOM || opts.headless === true;
      let screen = null, result = null;
      const fade = opts.fade || fadeTo;

      try {
        if (!headless) {
          await fade(1);
          screen = makeScreen({
            state: state0, zone: spec.zone, backdrop: spec.backdrop || spec.zone,
            speed: speed, autoConfirm: !!opts.autoplay || speed === 0,
            familyOf: (mid) => (monstersMap[mid] && monstersMap[mid].family) || 'default',
            itemName: (id) => (itemsMap[id] && itemsMap[id].name) || id,
            // the party's own bust art, through ui_kit's one convention — the
            // status table shows the same faces the dialogue boxes do
            bustFor: (charId) => {
              const k = EB();
              if (k && k.bustUrl) { try { return k.bustUrl(charId); } catch (e) { } }
              return 'assets/characters/' + String(charId) + '/bust.png';
            },
          });
          screenRef = screen;
          screen.show(); screen.syncHp(state0);
          await fade(0);
        }

        // ---- seats -----------------------------------------------------------
        const bag = makeBag(gs, itemsMap, opts.bag);
        const human = screen ? {
          name: 'menu',
          decide: (actorId, state, api) => screen.promptAction(actorId, state,
            Object.assign({ seatName: Battle.router && Battle.router.seatFor(actorId) }, api)),
        } : null;
        // The party autopilot doubles as the drop-out seat. It keeps its own
        // inventory tally, so the real bag is spent by this wrapper.
        const invSnapshot = {};
        for (const it of bag.list()) invSnapshot[it.id] = it.count;
        const partyAi = RU.policies.partyAi({ items: itemsMap, inventory: invSnapshot });
        const autopilot = {
          name: 'party-ai',
          async decide(actorId, state, api) {
            const a = await partyAi.decide(actorId, state, api);
            if (a && a.type === 'item' && a.item && !bag.use(a.item)) return { type: 'attack', by: actorId };
            return a;
          },
        };
        // THE 'ai' SEAT IS SIDE-AWARE, and that is not a detail: it is what makes
        // "player 2 drops out -> router.set(charId,'ai')" work mid-battle. Monsters
        // get the monster policy, a party member routed to 'ai' gets the autopilot.
        const foeAi = RU.policies.monsterAi();
        const aiSeat = {
          name: 'ai',
          decide(actorId, state, api) {
            const c = RU.findById(state, actorId);
            return (c && c.side === 'foe' ? foeAi : autopilot).decide(actorId, state, api);
          },
        };
        const seats = Object.assign({
          p1: human || autopilot,       // no screen (headless) -> the autopilot plays
          p2: human || autopilot,       // unbound until a second seat exists
          ai: aiSeat,
        }, opts.seats);
        // v1 routes every party member to p1; the table is REAL and remappable
        // mid-battle (Battle.router.set('vesper','p2')) — that is the co-op seam.
        const router = opts.router || RU.makeRouter({
          seats: seats,
          defaults: { party: opts.autoplay ? 'ai' : 'p1', foe: 'ai' },
        });
        Battle.router = router;
        const scheduler = opts.scheduler || RU.schedulers.commitThenResolve;
        Battle.scheduler = scheduler;

        const emit = async (events, state) => {
          for (const ev of events) log.push(ev);
          if (screen) await screen.play(events, state);
        };

        const final = await RU.engine.run({
          state: state0, rng, router, seats, scheduler, emit,
          api: { bag, items: itemsMap, seatName: null },
          maxRounds: opts.maxRounds,
        });

        result = RU.engine.result(final, { monsters: monstersMap, rng, log });
        Battle.last = result;
        if (screen) await screen.outro(result);
      } catch (e) {
        console.error('[Battle] failed', e);
        // A crashed battle must never eat the party or freeze the world.
        result = { outcome: 'fled', xp: 0, gold: 0, drops: [], turns: 0,
                   partyHp: members.reduce((o, m) => (o[m.id] = m.hp, o), {}), log: log, error: String(e) };
      } finally {
        if (screen) { await fade(1); screen.destroy(); }
        screenRef = null;
        Battle.active = false;
        lockWorld(false);
        if (screen) await fade(0);
      }
      return result;
    },

    // ---- conveniences (console + coordinator playtest) ---------------------
    // Battle.demo('meadow') — build a spec from encounters.json and fight it.
    demo(zone, opts) {
      const gs = window.GS;
      if (!gs || !gs.ok) { console.warn('[Battle] GS not ready'); return null; }
      const RU = window.Rules;
      const zd = gs.data.encounters.zones[zone || 'meadow'];
      if (!zd) { console.warn('[Battle] no such zone', zone); return null; }
      const seed = (opts && opts.seed != null) ? opts.seed : RU.hashSeed('demo', zone, gs.state.party[0].xp);
      const group = RU.derive.pickGroup(zd, RU.mulberry32(seed)) || [];
      return Battle.start({ zone: zone, group: group, seed: seed, backdrop: zd.battleBackdrop }, null, opts);
    },
    _debug() {
      return {
        active: Battle.active, scheduler: Battle.scheduler && Battle.scheduler.name,
        router: Battle.router && Battle.router.table(),
        rules: !!window.Rules, dom: HAS_DOM, last: Battle.last,
        ebui: !!(EB() && EB().act), showFoeHp: Battle.showFoeHp,
        backdrops: Object.keys(backdrops), sprites: Object.keys(sprites),
        art: { base: art.base, enabled: art.enabled,
               backdropSample: backdropUrl('meadow'), monsterSample: monsterUrl('reed-nibbler') },
      };
    },
  };
  wire();
})();
