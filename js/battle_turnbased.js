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
// UI IDIOM: ui_kit's window grammar — the classic FF blue window, silver bevel,
// white text, amber only as highlight — and its key map, so battle keys are the
// same keys as every other panel in the game. EBUI's pure helpers are reused when
// present; its panel() factory is not (a centred 620-900px dialog is the wrong
// shape for a full-bleed battle screen, and innerHTML-swapping bodies cannot host
// in-flight animations).
//
// THE BATTLE IS A STAGE. Monsters stand on the LEFT of a painted plate, the
// active party stands facing them on the RIGHT, both bottom-aligned to ONE
// ground line, each casting a shadow onto it. The party's sprites are their
// full-body pose plates, chroma-keyed at load by ui_kit (EBUI.poseSprite). A
// character with no pose art simply is not on the field — they still hold their
// row in the status window, and they walk on by themselves the day their plate
// lands in assets/characters/<id>/. No list of party sprites exists anywhere.
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
  // LAYOUT (FF7/FF9): full-bleed painted backdrop; a small HUD window in the top
  // corner; a STAGE of monsters (left) facing the party's sprites (right) on one
  // ground line; a slim log strip; and a bottom band of TWO windows — the command
  // list pinned left, the compact party status table pinned right, with the plate
  // showing through the gap between them. The field is the star: every number in
  // the bottom band is sized to be read at a glance and no larger.
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
  background:radial-gradient(122% 90% at 50% 42%,#0000 40%,#02030fa8 100%)}
/* The windows have to read over whatever art lands in assets/battle/, but the
   plates are the point now: the scrim is a foot-of-frame wash under the bottom
   band only, cool-tinted so it sits with the blue windows instead of muddying
   the ground the sprites are standing on. */
.ebb-scrim{position:absolute;left:0;right:0;bottom:0;height:42%;z-index:1;pointer-events:none;
  background:linear-gradient(180deg,#0000 0%,#03051540 52%,#03051599 100%)}

/* ONE MARGIN, USED BY BOTH ENDS. The top rail, the message line and the bottom
   band all inset by --ebb-gut, so nothing floats and nothing is flush on one
   side and adrift on the other. */
.ebb-root{--ebb-gut:clamp(16px,3.2vw,40px)}
.ebb-top{position:relative;z-index:3;display:flex;flex-direction:column;gap:7px;
  padding:clamp(12px,2.2vh,20px) var(--ebb-gut) 0}
.ebb-rail{display:flex;gap:9px;align-items:flex-start}
.ebb-hud{padding:7px 15px;display:flex;gap:15px;align-items:baseline;
  font-family:var(--eb-mono);font-size:var(--eb-fs-xs);letter-spacing:.1em}
.ebb-hud .zone{color:var(--eb-amber-hi);font-weight:700;letter-spacing:.22em}
.ebb-hud .rnd{color:var(--eb-ink-faint)}
.ebb-seatwin{margin-left:auto;padding:7px 15px;font-family:var(--eb-mono);
  font-size:var(--eb-fs-xs);
  color:var(--eb-ink-dim);letter-spacing:.1em;max-width:40vw;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap}
.ebb-seatwin:empty{display:none}

/* ---- THE STAGE ------------------------------------------------------------
   EVERYONE STANDS ON ONE GROUND LINE. The stage is a single bottom-aligned flex
   row, so a 190px monster and a 240px hero share a floor no matter what art
   resolves for either; the empty space is all ABOVE them, where the plate reads
   as sky and canopy. Foes left, party right, facing each other across a gap the
   plate shows through. */
.ebb-field{position:relative;z-index:3;flex:1 1 auto;min-height:0;display:flex;
  align-items:flex-end;justify-content:center;
  padding:min(2vh,18px) min(4vw,48px) min(7vh,58px)}
.ebb-stage{display:flex;align-items:flex-end;justify-content:center;
  gap:min(9vw,110px);max-width:100%}
.ebb-foes{display:flex;align-items:flex-end;justify-content:flex-end;
  gap:min(3.5vw,40px);flex-wrap:wrap}
.ebb-heroes{display:flex;align-items:flex-end;justify-content:flex-start;
  gap:min(2vw,22px)}
.ebb-heroes:empty{display:none}
/* a hero seat whose plate has not resolved (or never will) takes no space */
.ebb-hero.pending{display:none}
.ebb-foe,.ebb-hero{position:relative;display:flex;flex-direction:column;align-items:center;
  gap:6px;transition:opacity 300ms linear,transform 300ms ease-in}
.ebb-foe.dead{opacity:0;transform:translateY(14px) scale(.9)}
/* KO'd party members stay on the field as a grey ghost. The fade is INFORMATION
   ("she is down"), so it survives reduced motion; only the movement dies. */
.ebb-hero.down{opacity:.17;filter:grayscale(1) brightness(.6)}
/* the target caret: ui_kit's cursor glyph, turned to point down at the foe */
.ebb-mark{width:19px;height:15px;opacity:0;
  background:linear-gradient(180deg,var(--eb-amber-hi),var(--eb-amber) 55%,var(--eb-amber-dim));
  clip-path:polygon(28% 0,72% 0,72% 40%,100% 40%,50% 100%,0 40%,28% 40%);
  filter:drop-shadow(0 2px 3px #000b);animation:ebb-caret 820ms steps(2,jump-none) infinite}
.ebb-foe.cur .ebb-mark{opacity:1}

/* THE STAND is the seat on the ground: it holds the cast shadow and it is what
   STEPS FORWARD when its owner acts. The shadow must not bob with the sprite —
   a shadow that floats is worse than no shadow — so the bob lives one level in,
   on .ebb-sil, and the ellipse stays pinned to the floor. */
.ebb-stand{position:relative;display:flex;align-items:flex-end;justify-content:center;
  transition:transform 200ms ease-out}
.ebb-stand::after{content:'';position:absolute;left:50%;bottom:-9px;z-index:-1;
  transform:translateX(-50%);width:88%;min-width:56px;height:26px;pointer-events:none;
  background:radial-gradient(50% 50% at 50% 50%,#000000cc 0%,#00000073 46%,#0000 72%)}
/* the step-forward is TOWARD THE ENEMY, and the enemy is now on the right */
.ebb-hero.act .ebb-stand{transform:translateX(30px)}
.ebb-foe.act .ebb-stand{transform:translateX(-30px)}

.ebb-sil{display:flex;align-items:flex-end;justify-content:center;
  filter:drop-shadow(0 9px 10px #0009);animation:ebb-bob 2.8s ease-in-out infinite}
.ebb-sil img,.ebb-sil canvas{display:block;max-width:none}
.ebb-foe.cur .ebb-sil{filter:drop-shadow(0 9px 10px #0009) drop-shadow(0 0 7px #f0b45c99)}
.ebb-hero.cur .ebb-sil{filter:drop-shadow(0 9px 10px #0009) drop-shadow(0 0 8px #ffdca6a6)}
.ebb-sil.hit{animation:ebb-hit 200ms linear}
/* FF9 proportions: the party reads a little taller than the beasts it faces,
   and both are big enough that the 30px busts in the status band are clearly a
   different register of image. */
.ebb-hero .ebb-sil canvas{height:clamp(176px,34vh,300px);width:auto}
/* THE TAGS HANG BELOW THE GROUND LINE, out of flow. In flow they were part of
   the foe's height, and since the stage bottom-aligns everything, a tagged
   monster stood ~40px HIGHER than an untagged hero — the whole point of the
   shared ground line, lost to a label. */
.ebb-ftags{position:absolute;top:calc(100% + 8px);left:50%;transform:translateX(-50%);
  display:flex;flex-direction:column;align-items:center;gap:4px;pointer-events:none}
/* A NAME TAG IS READ ACROSS A ROOM OR IT IS DECORATION. These float over a lit
   arena whose ground is bright warm sand, so they carry the window's own dark
   fill and the ramp's small step rather than 12px of dim ink. The HP pip under
   them wears the SAME three bands as every other gauge in the game — a monster
   about to die must look like a party member about to die. */
.ebb-ftag{padding:3px 13px;border-radius:6px;font-size:var(--eb-fs-sm);
  font-weight:600;letter-spacing:.06em;
  color:var(--eb-ink);white-space:nowrap;border:1px solid var(--eb-edge);
  background:var(--eb-win);text-shadow:0 1px 3px #000;
  box-shadow:inset 1px 1px 0 var(--eb-bevel-lt),inset -1px -1px 0 var(--eb-bevel-dk),
             0 3px 10px #0009}
.ebb-foe.cur .ebb-ftag{color:var(--eb-amber-hi);
  box-shadow:inset 1px 1px 0 var(--eb-bevel-lt),inset -1px -1px 0 var(--eb-bevel-dk),
             0 0 0 2px #f0b45cad,0 3px 12px #000a}
.ebb-fbar{position:relative;width:92px;height:7px;border-radius:4px;background:var(--eb-track);
  overflow:hidden;box-shadow:inset 0 1px 2px #000c,0 0 0 1px #ffffff33}
.ebb-fbar>i{position:absolute;left:0;top:0;display:block;height:100%;background:var(--eb-hp);
  transition:width var(--eb-t-med) var(--eb-ease-soft)}
.ebb-fbar>i.gh{background:var(--eb-hp-ghost);
  transition:width var(--eb-t-ghost) var(--eb-ease-soft) var(--eb-t-ghost-wait)}
.ebb-fbar.warn>i:not(.gh){background:var(--eb-hp-warn)}
.ebb-fbar.low>i:not(.gh){background:var(--eb-hp-low)}

/* ---- the damage pop: FF-sized, hard outline, one beat of overshoot -------- */
/* SIZE CARRIES THE STORY. Every hit used to pop at the same 42px, so a scratch
   and a near-lethal blow read identically and the only way to know which you
   had just taken was to go and read the gauge. The number is now sized by what
   FRACTION of the target's own maximum it took off — 'tap' under an eighth,
   'big' over a third — which is the cheapest possible way for the screen to
   tell you how bad that was, and it is legible from the sofa either way. */
.ebb-num{position:absolute;left:50%;top:12%;transform:translateX(-50%);pointer-events:none;
  z-index:7;font:800 clamp(34px,2.6vw,64px)/1 var(--eb-mono);letter-spacing:-.02em;color:#fff6e6;
  text-shadow:2px 0 0 #180d05,-2px 0 0 #180d05,0 2px 0 #180d05,0 -2px 0 #180d05,
              2px 2px 0 #180d05,-2px 2px 0 #180d05,2px -2px 0 #180d05,-2px -2px 0 #180d05,
              0 6px 10px #000a;
  animation:ebb-pop 950ms cubic-bezier(.18,.85,.3,1) forwards}
.ebb-num.heal{color:#c8f2a1}
.ebb-num.tap{font-size:clamp(26px,1.9vw,46px);color:#e8e4d6}
.ebb-num.big{font-size:clamp(44px,3.5vw,84px);color:#ffe7bd}
.ebb-num.crit{color:#ffcf88;font-size:clamp(50px,3.9vw,94px)}
.ebb-num.miss{color:#d5d9ee;font-size:clamp(22px,1.5vw,34px);font-weight:700}
/* THE HURT FLASH. A party member taking damage lights the edges of the frame
   red for a fifth of a second — the one tell that works when the player is
   looking at the monster they aimed at rather than at their own gauge. It is a
   DOM layer over the arena, never a change to the arena's own render. */
.ebb-hurt{position:absolute;inset:0;z-index:5;pointer-events:none;opacity:0;
  background:radial-gradient(118% 88% at 50% 50%,#0000 46%,#c0261488 100%)}
.ebb-hurt.on{animation:ebb-hurt 420ms var(--eb-ease-out)}
@keyframes ebb-hurt{0%{opacity:0}18%{opacity:1}100%{opacity:0}}
/* a hero's number pops clear of the head — a full-body sprite has a face worth
   not covering, which a 90px monster silhouette does not */
.ebb-hero .ebb-num{top:-14px}
/* FALLBACK ONLY — a party member with no pose art has no body on the field, so
   their number goes over their portrait in the status row instead of nowhere. */
.ebb-prow .ebb-num{left:56px;top:-34px;font-size:28px}
.ebb-prow .ebb-num.crit{font-size:34px}

/* ---- bottom furniture -----------------------------------------------------
   The band is PINNED TO THE EDGES, not stretched: the command window hugs the
   left, the status window hugs the right, and the plate shows through between
   them. Every measure here was pulled in from v1 — the field is the star and
   the furniture is meant to be read, not admired. */
/* NOT max-width + auto margins: that centres the band and leaves the command
   window floating in from the left edge on a wide screen while the party window
   floats in from the right. Full width, one gutter each side, flush to both. */
.ebb-bottom{position:relative;z-index:3;flex:0 0 auto;display:flex;flex-direction:column;
  gap:7px;width:100%;padding:0 var(--ebb-gut) clamp(14px,2.6vh,26px)}
/* the message line: full width of the frame, and tall enough for two lines so a
   long message does not reflow the rail under it */
/* ---- THE MESSAGE BAND -----------------------------------------------------
   THIS IS THE LINE THE PLAYER READS EVERY BEAT, and at TV distance it was mush:
   14.5px on a 1920 canvas, marooned at the far left of a 1900px window with the
   key hints marooned at the far right and nothing in between (measured,
   docs/qa/ui/before/battle-cmd.tv.png). Three changes, in order of importance:

   1. IT IS TYPED TO BE READ FROM A SOFA (--eb-fs-lg, ~22px at 1080p).
   2. THE DEAD AIR IS NOW THE TURN TELEGRAPH. Whoever is up — hero or monster —
      gets their face and name at the head of the bar, so "who is about to move"
      and "what just happened" are one glance in one place, instead of a chip in
      the opposite corner of the screen.
   3. THE LINE ANIMATES IN. A new message slides up a few pixels rather than
      being swapped under the eye, so the player can see that something NEW was
      said even when two consecutive lines look alike.
   And the whole window HIDES when there is nothing to say ('.mute'): an empty
   1900px blue slab across the top of a lit arena is not chrome, it is damage. */
.ebb-log{padding:9px 16px;min-height:2.6em;display:flex;align-items:center;gap:14px;
  font-size:var(--eb-fs-lg);line-height:1.3;
  transition:opacity var(--eb-t-med) var(--eb-ease-out),
             transform var(--eb-t-med) var(--eb-ease-out)}
.ebb-log.mute{opacity:0;transform:translateY(-6px);pointer-events:none}
.ebb-actor{flex:0 0 auto;display:none;align-items:center;gap:9px;padding-right:14px;
  border-right:1px solid var(--eb-rule)}
.ebb-actor.on{display:flex}
.ebb-actor .eb-port{width:2.05em;height:2.05em;border-radius:5px}
.ebb-actor .ebb-qic{width:2.05em;height:2.05em;border-radius:5px}
.ebb-actor b{font:700 var(--eb-fs-md)/1.1 var(--eb-face);letter-spacing:.06em;
  text-transform:uppercase;color:var(--eb-amber-hi);white-space:nowrap}
.ebb-actor.foe b{color:#ffb9a0}
.ebb-logtxt{flex:1 1 auto;min-width:0}
.ebb-logtxt em{color:var(--eb-amber-hi);font-style:normal;font-weight:700}
.ebb-logtxt.beat{animation:ebb-line 260ms var(--eb-ease-out)}
@keyframes ebb-line{from{opacity:0;transform:translateY(7px)}to{opacity:1;transform:none}}
.ebb-hint{flex:0 0 auto;font-family:var(--eb-mono);font-size:var(--eb-fs-2xs);
  color:var(--eb-ink-faint);letter-spacing:.04em;opacity:.72}
.ebb-hint b{color:var(--eb-amber-dim);font-weight:700}
/* FF convention, followed after the mirror: the command window sits on the
   PARTY's side (now bottom-LEFT, under the party it belongs to) and the status
   window takes the opposite corner. Both flush to their gutter, the plate
   showing through between them. */
.ebb-band{display:flex;gap:9px;align-items:stretch;justify-content:space-between;
  align-items:flex-end}
/* ---- THE COMMAND WINDOW ---------------------------------------------------
   IT NOW SAYS WHOSE TURN IT IS. Its title bar carries the deciding character's
   bust and name (FF9's own idiom) instead of the word "Command", so the answer
   to "who am I choosing for" is where the choosing happens — it used to live in
   a chip in the opposite corner of a 1920px screen.

   AND IT ARRIVES. '.live' is added the moment a decision opens: the window
   slides in from its own gutter and lights its frame, so the handoff from one
   actor to the next is an event you can see out of the corner of your eye
   rather than a silent re-render of three words. */
.ebb-cmdwin{position:relative;flex:0 0 min(248px,28vw);display:flex;flex-direction:column;
  transform:translateX(-14px);opacity:.55;
  transition:transform var(--eb-t-slow) var(--eb-ease-out),
             opacity var(--eb-t-med) var(--eb-ease-out),
             box-shadow var(--eb-t-med) linear}
.ebb-cmdwin.live{transform:none;opacity:1;
  box-shadow:inset 2px 2px 0 0 var(--eb-bevel-lt),inset -2px -2px 0 0 var(--eb-bevel-dk),
             inset 0 0 0 3px #00021e3d,0 10px 30px #000a,0 0 0 1px #f0b45c66}
.ebb-cmdwin .eb-wtitle{gap:9px;padding:5px 12px}
.ebb-cmdwin .eb-wtitle .eb-port,.ebb-cmdwin .eb-wtitle .ebb-qic{
  width:1.85em;height:1.85em;border-radius:4px;flex:0 0 auto}
.ebb-cmdwin .eb-wtitle span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ebb-cmds{padding:7px 8px 8px;display:flex;flex-direction:column;gap:2px;flex:1 1 auto}
.ebb-cmd{display:flex;align-items:center;gap:6px;padding:6px 9px;border-radius:6px;
  font:700 var(--eb-fs-md)/1.15 var(--eb-face);letter-spacing:.1em;color:var(--eb-ink-dim);
  border:1px solid transparent;
  transition:transform var(--eb-t-fast) var(--eb-ease-out),color var(--eb-t-fast) linear}
.ebb-cmd.cur{color:var(--eb-amber-hi);border-color:#f0b45c7a;transform:translateX(4px);
  background:linear-gradient(90deg,#f0b45c5c,#f0b45c1f 72%,#f0b45c00);
  box-shadow:inset 3px 0 0 var(--eb-amber)}
.ebb-cmds.idle .ebb-cmd{opacity:.38}
.ebb-cmds.idle .ebb-cmd.cur{opacity:.55}

/* SIZED TO ITS CONTENT, not to the screen. Every column is a fixed measure and
   the name sits hard against the HP block, FF9's compact status window — a
   1fr name column on a 1600px screen turns the row into a runway of dead air. */
.ebb-partywin{flex:0 1 auto;min-width:0;display:flex;flex-direction:column}
.ebb-phead,.ebb-prow{display:grid;align-items:center;gap:9px;
  grid-template-columns:1em 38px minmax(6.5em,10em) 15em 3em}
.ebb-phead{padding:5px 13px 4px;border-bottom:1px solid var(--eb-rule);
  font:700 var(--eb-fs-2xs)/1 var(--eb-face);letter-spacing:.2em;color:var(--eb-ink-faint)}
.ebb-phead .r{text-align:right}
/* "TURN ORDER" is wider than its column and was wrapping to two lines; it is a
   label, not data, so it may overflow into the gap beside it rather than grow
   the column and push every row's measures around. */
.ebb-phead span:nth-child(3){white-space:nowrap;letter-spacing:.14em;overflow:visible}
.ebb-party{padding:5px 13px 7px;display:flex;flex-direction:column;gap:3px;flex:1 1 auto}
.ebb-prow{position:relative;padding:4px 0;border-radius:6px;
  transition:transform var(--eb-t-fast) var(--eb-ease-out)}
.ebb-prow.cur{background:linear-gradient(90deg,#f0b45c47,#f0b45c14 70%,#f0b45c00);
  box-shadow:inset 3px 0 0 var(--eb-amber),inset 0 0 0 1px #f0b45c5c}
.ebb-prow.down{opacity:.48}
.ebb-prow.hit{animation:ebb-hit 200ms linear}
.ebb-pname{min-width:0}
.ebb-pname b{display:block;font:700 var(--eb-fs-md)/1.15 var(--eb-face);letter-spacing:.01em;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ebb-pname small{font:var(--eb-fs-2xs)/1.35 var(--eb-mono);color:var(--eb-ink-faint);
  letter-spacing:.12em}
.ebb-php{display:flex;align-items:center;gap:9px;min-width:0}
.ebb-php .tk{position:relative;flex:1 1 auto;min-width:26px;height:11px;border-radius:6px;
  background:var(--eb-track);
  overflow:hidden;box-shadow:inset 0 1px 3px #000d,0 1px 0 var(--eb-inset-lt)}
.ebb-php .tk>i{position:absolute;left:0;top:0;display:block;height:100%;border-radius:6px;
  background:var(--eb-hp);transition:width var(--eb-t-med) var(--eb-ease-soft)}
.ebb-php .tk>i.gh{background:var(--eb-hp-ghost);
  transition:width var(--eb-t-ghost) var(--eb-ease-soft) var(--eb-t-ghost-wait)}
.ebb-php.warn .tk>i:not(.gh){background:var(--eb-hp-warn)}
.ebb-php.low .tk>i:not(.gh){background:var(--eb-hp-low)}
.ebb-php.low .tk{animation:eb-danger 1.15s ease-in-out infinite}
.ebb-php .nm{flex:0 0 auto;font-family:var(--eb-mono);font-size:var(--eb-fs-sm);
  font-variant-numeric:tabular-nums;color:var(--eb-ink-faint)}
.ebb-php .nm b{color:var(--eb-amber-hi);font-weight:700;font-size:var(--eb-fs-md)}
.ebb-php.low .nm b{color:#ffb0a0}
/* ---- FOE ROWS IN THE TURN QUEUE -------------------------------------------
   Same grid as a party row so every column lines up, but deliberately SLIMMER:
   the party rows stay visually primary because they carry the vital gauges, and
   a foe only needs to answer "who is it, when do they go, how hurt are they". */
.ebb-qrow{display:grid;align-items:center;gap:9px;position:relative;padding:3px 0;
  grid-template-columns:1em 38px minmax(6.5em,10em) 15em 3em;border-radius:6px;
  transition:opacity 180ms linear}
/* THE FOE THUMBNAIL. It used to be image-rendering:pixelated, because the art
   behind it was a 16 px hand-drawn sprite. It is now a 256 px render OF THE MODEL
   THE ARENA STAGES (tools/monster_icons.mjs), so nearest-neighbour down to 28 px
   would throw away eight pixels in nine and alias what it kept. Smooth is the
   correct filter for the art that is actually there. */
.ebb-qic{width:28px;height:28px;justify-self:center;border-radius:5px;
  background:#0c0e2acc center/contain no-repeat;
  box-shadow:inset 0 0 0 1px var(--eb-rule)}
.ebb-qname{font:600 var(--eb-fs-sm)/1.15 var(--eb-face);color:var(--eb-ink-dim);letter-spacing:.02em;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ebb-qhp .tk{position:relative;display:block;height:7px;border-radius:4px;background:var(--eb-track);
  overflow:hidden;box-shadow:inset 0 1px 2px #000c}
.ebb-qhp .tk>i{position:absolute;left:0;top:0;display:block;height:100%;width:100%;border-radius:4px;
  background:var(--eb-hp);transition:width var(--eb-t-med) var(--eb-ease-soft)}
.ebb-qhp .tk>i.gh{background:var(--eb-hp-ghost);
  transition:width var(--eb-t-ghost) var(--eb-ease-soft) var(--eb-t-ghost-wait)}
.ebb-qhp.warn .tk>i:not(.gh){background:var(--eb-hp-warn)}
.ebb-qhp.low .tk>i:not(.gh){background:var(--eb-hp-low)}
.ebb-qrow.dead,.ebb-qrow.gone,.ebb-prow.gone{display:none}

/* QUEUE STATE, shared by both row kinds. "now" is whoever is up — the arrow plus
   a lit rail down the left edge. "done" is whoever has already gone this round;
   they sink to the tail and grey out rather than vanish, so the player can still
   read the shape of the round. */
.ebb-prow.now,.ebb-qrow.now{background:linear-gradient(90deg,#f0b45c33,#f0b45c0f 70%,#f0b45c00);
  box-shadow:inset 2px 0 0 var(--eb-amber),inset 0 0 0 1px #f0b45c47}
.ebb-prow.now .ebb-pname b,.ebb-qrow.now .ebb-qname{color:var(--eb-amber-hi)}
.ebb-prow.done,.ebb-qrow.done{opacity:.42}
.ebb-prow.done .ebb-pname b,.ebb-qrow.done .ebb-qname{color:var(--eb-ink-faint)}

/* MP is a RESERVED COLUMN — a dash until magic exists, so nothing shifts later */
.ebb-pmp{text-align:right;font-family:var(--eb-mono);font-size:12px;
  color:var(--eb-ink-faint);font-variant-numeric:tabular-nums}

/* The item list opens INTO THE GAP beside the command window — the dead space
   between the two bottom windows, which is exactly where FF7 puts it. Above the
   command window (where it used to open) it covered the log strip, i.e. the line
   that says "Use what?" — the sub-menu was hiding its own prompt. */
.ebb-sub{position:absolute;left:calc(100% + 9px);bottom:0;min-width:min(340px,34vw);
  max-height:min(44vh,300px);overflow:auto;display:none;z-index:6;padding:7px}
.ebb-sub.on{display:block;animation:ebb-subin 220ms var(--eb-ease-out)}
@keyframes ebb-subin{from{opacity:0;transform:translateX(-10px)}to{opacity:1;transform:none}}
.ebb-item{display:flex;gap:9px;align-items:center;padding:5px 9px;border-radius:6px;
  border:1px solid transparent;font-size:var(--eb-fs-md);
  transition:transform var(--eb-t-fast) var(--eb-ease-out)}
.ebb-item.cur{background:linear-gradient(90deg,#f0b45c5c,#f0b45c1f 72%,#f0b45c00);
  border-color:#f0b45c7a;transform:translateX(4px);box-shadow:inset 3px 0 0 var(--eb-amber)}
.ebb-item.cur .k{color:var(--eb-amber-hi);font-weight:600}
.ebb-item.dim{color:var(--eb-ink-faint)}
.ebb-item .k{flex:1 1 auto;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ebb-item .n{flex:0 0 auto;font-family:var(--eb-mono);font-size:var(--eb-fs-sm);color:var(--eb-ink-dim)}

/* ---- THE VICTORY SCREEN ---------------------------------------------------
   THE PAYOFF WAS TYPED LIKE A RECEIPT. A 440px box of 13.5px rows announcing
   the thing the last minute of play was FOR. It is now sized and typed for the
   moment: a wider box that rises into place, a headline set at the top of the
   ramp, and the two numbers that matter — experience and gold — promoted out of
   the row list into their own pair of big amber readouts. */
/* WHERE THE BOX SITS IS A MEASURED FIX (2026-08-08, BET I). The tally used to be
   dead centre over a full-bleed dim + blur, and tools/battle_ko_shots.mjs put a
   number on the obvious: in a 1600x813 frame the box occupied x 520-1080 and
   Vesper's own projected anchor was INSIDE it, with Maren behind the blur. The
   screen celebrated the party by hiding it. So the box now stands on the side of
   the frame the party is NOT on — measured from the stage's own anchors at outro
   time, never assumed from CFG.partySide, because the world arena solves its own
   camera yaw — and the scrim is masked so it fades out over the party's half.
   No class = centred and fully dimmed, which is the DOM stage's own case. */
.ebb-outro{position:absolute;inset:0;z-index:8;display:flex;align-items:center;
  justify-content:center;animation:eb-fade 200ms var(--eb-ease-out)}
.ebb-oscrim{position:absolute;inset:0;background:#0305158c;
  backdrop-filter:blur(3px);-webkit-backdrop-filter:blur(3px)}
.ebb-outro.pleft{justify-content:flex-end;padding-right:clamp(16px,4.5vw,80px)}
.ebb-outro.pright{justify-content:flex-start;padding-left:clamp(16px,4.5vw,80px)}
.ebb-outro.pleft .ebb-oscrim{
  -webkit-mask-image:linear-gradient(90deg,transparent 0,transparent 20%,#000 46%,#000 100%);
  mask-image:linear-gradient(90deg,transparent 0,transparent 20%,#000 46%,#000 100%)}
.ebb-outro.pright .ebb-oscrim{
  -webkit-mask-image:linear-gradient(270deg,transparent 0,transparent 20%,#000 46%,#000 100%);
  mask-image:linear-gradient(270deg,transparent 0,transparent 20%,#000 46%,#000 100%)}
/* POSITIONED, and that is load-bearing rather than cosmetic: the scrim beside it
   is position:absolute, and a STATIC flex item paints BELOW a positioned sibling
   in the same stacking context — so without this the dim + blur landed ON TOP of
   the panel and the backdrop plate showed straight through the VICTORY box.
   Photographed once (docs/qa/battle-ko/, first after-run) before it was found. */
.ebb-obox{position:relative;z-index:1;min-width:min(560px,86vw);overflow:hidden;
  animation:ebb-orise 420ms var(--eb-ease-out) both}
@keyframes ebb-orise{from{opacity:0;transform:translateY(22px) scale(.97)}to{opacity:1;transform:none}}
.ebb-ohead{display:block;padding:11px 20px;font:800 var(--eb-fs-xl)/1.2 var(--eb-face);
  letter-spacing:.24em;
  text-transform:uppercase;color:var(--eb-amber-hi);background:var(--eb-win-head);
  border-bottom:1px solid var(--eb-rule);border-radius:6px 6px 0 0;
  text-shadow:0 0 22px #f0b45c66,0 2px 3px #000}
.ebb-obody{padding:13px 20px}
/* the two headline spoils, side by side and unmissable */
.ebb-ospoils{display:flex;gap:10px;margin:0 0 10px}
.ebb-ospoil{flex:1 1 0;padding:8px 13px;border-radius:7px;background:var(--eb-card);
  box-shadow:inset 1px 1px 0 var(--eb-inset-lt),inset -1px -1px 0 var(--eb-inset-dk)}
.ebb-ospoil .l{display:block;font:700 var(--eb-fs-2xs)/1 var(--eb-face);letter-spacing:.2em;
  color:var(--eb-ink-faint);margin-bottom:5px}
.ebb-ospoil .v{font:800 var(--eb-fs-2xl)/1.05 var(--eb-mono);color:var(--eb-amber-hi);
  font-variant-numeric:tabular-nums}
.ebb-ospoil .v small{font-size:var(--eb-fs-md);color:var(--eb-amber-dim);margin-left:4px}
.ebb-orow{display:flex;gap:10px;padding:4px 0;font-size:var(--eb-fs-md)}
.ebb-orow .n{margin-left:auto;font-family:var(--eb-mono);color:var(--eb-amber-hi);
  font-weight:700;font-variant-numeric:tabular-nums}
/* ---- THE VICTORY TALLY ----------------------------------------------------
   One row per active party member: name, level, the xp bar, and the LEVEL UP!
   stamp that only exists while the bar is wrapping. The bar animates by width
   with a transition, so the fill is smooth between the 20 ms steps the script
   writes — and the transition is killed for exactly one frame when a bar resets
   to empty after a level, or the reset would animate backwards across the row. */
.ebb-tally{display:flex;flex-direction:column;gap:8px;padding:2px 0 11px;
  margin-bottom:9px;border-bottom:1px solid var(--eb-rule)}
.ebb-trow{display:grid;grid-template-columns:minmax(5em,8em) 5em 1fr;gap:11px;
  align-items:center;position:relative}
.ebb-trow .nm{font:700 var(--eb-fs-md)/1.2 var(--eb-face);overflow:hidden;text-overflow:ellipsis;
  white-space:nowrap}
.ebb-trow .lv{font-family:var(--eb-mono);font-size:var(--eb-fs-2xs);color:var(--eb-ink-faint);
  letter-spacing:.1em}
.ebb-trow .lv b{color:var(--eb-ink);font-weight:700;font-size:var(--eb-fs-md)}
.ebb-trow.levelled .lv b{color:var(--eb-amber-hi)}
.ebb-trow .xb{height:12px;border-radius:6px;background:var(--eb-track);overflow:hidden;
  box-shadow:inset 0 1px 3px #000d,0 1px 0 var(--eb-inset-lt)}
.ebb-trow .xb > i{display:block;height:100%;width:0;border-radius:6px;
  background:linear-gradient(180deg,#bfe0ff,#4d7fd0);transition:width 90ms linear}
.ebb-trow .up{position:absolute;right:0;top:-17px;opacity:0;pointer-events:none;
  font:800 var(--eb-fs-sm)/1 var(--eb-face);letter-spacing:.16em;color:var(--eb-amber-hi);
  text-shadow:0 0 12px #f0b45ccc,0 1px 2px #000}
.ebb-trow.flash .up{animation:ebb-levelup 620ms ease-out}
.ebb-trow.flash .xb > i{background:linear-gradient(180deg,#fff3d6,#f0b45c)}
.ebb-trow.flash .xb{box-shadow:inset 0 1px 2px #000c,0 0 0 1px #f0b45c,0 0 14px #f0b45c80}
@keyframes ebb-levelup{
  0%{opacity:0;transform:translateY(6px) scale(.9)}
  25%{opacity:1;transform:translateY(-2px) scale(1.08)}
  70%{opacity:1;transform:translateY(-3px) scale(1)}
  100%{opacity:0;transform:translateY(-10px) scale(1)}}
@media (prefers-reduced-motion:reduce){
  /* the VALUES still animate — they are the information — but the pop does not */
  .ebb-trow.flash .up{animation:none;opacity:1}}
.ebb-ofoot{padding:9px 20px;border-top:1px solid var(--eb-rule);background:var(--eb-win-head);
  font-family:var(--eb-mono);font-size:var(--eb-fs-sm);color:var(--eb-ink-dim);letter-spacing:.14em;
  border-radius:0 0 6px 6px;animation:ebb-breathe 2.2s ease-in-out infinite}
@keyframes ebb-breathe{0%,100%{opacity:.55}50%{opacity:1}}
.ebb-toast{position:fixed;left:50%;top:12%;transform:translateX(-50%);z-index:27;
  padding:9px 20px;color:var(--eb-ink);font:var(--eb-fs-md) var(--eb-face);text-shadow:0 1px 2px #000;
  opacity:0;transition:opacity 180ms linear;pointer-events:none}
.ebb-toast.on{opacity:1}

/* ---- 3D ARENA MODE (battle_stage3d.js) ------------------------------------
   ONE set of markup, two stages. When the 3D arena is live the root wears
   .ebb-3d and every rule below re-homes the SAME elements: the bodies move into
   the WebGL scene, and what stays in the DOM is each combatant's FURNITURE —
   name tag, HP pip, target caret, damage number — parked over their 3D body by
   projection each frame. Nothing here is a second implementation of anything;
   strip the class (or the file) and the DOM stage renders exactly as before. */
.ebb-gl{position:absolute;inset:0;z-index:0;display:block;width:100%;height:100%}
.ebb-3d .ebb-bg,.ebb-3d .ebb-sil,.ebb-3d .ebb-stand{display:none}
/* The field stops being a flex ROW and becomes a full-bleed projection LAYER —
   which takes it out of the root's column flow, so the bottom band has to be
   pushed back down by hand or it floats up under the HUD. */
.ebb-3d .ebb-field{position:absolute;inset:0;padding:0;pointer-events:none;z-index:3}
.ebb-3d .ebb-bottom{margin-top:auto}
.ebb-3d .ebb-stage{position:absolute;inset:0;display:block;gap:0;max-width:100%}
.ebb-3d .ebb-foes,.ebb-3d .ebb-heroes{display:block;gap:0}
.ebb-3d .ebb-heroes:empty{display:block}
/* A ZERO-WIDTH ANCHOR whose height is the body's PROJECTED PIXEL HEIGHT. That is
   what lets every measure in the sheet above keep working untouched: .ebb-ftags
   still hangs at 100%+8px (= just under the feet) and .ebb-num still pops at 12%
   (= up by the head), because the box really is the body's screen rectangle. */
.ebb-3d .ebb-foe,.ebb-3d .ebb-hero{position:absolute;left:0;top:0;width:0;
  transform:translateX(-50%);flex-direction:column;align-items:center;justify-content:flex-start}
.ebb-3d .ebb-hero.pending{display:flex}
.ebb-3d .ebb-hero .ebb-num{top:8%}
/* the caret rides above the head; the ring at the feet is the 3D half of the mark */
.ebb-3d .ebb-mark{margin-top:-21px}
/* a KO'd party member is dimmed in the SCENE — the tag stays legible */
.ebb-3d .ebb-hero.down{opacity:.6;filter:none}
/* WHOSE TURN IT IS. The tell has to work on a monster as well as on a hero —
   the complaint was not being able to see an enemy action coming — so it lives on
   the shared body/anchor element and not on the party table alone. */
.ebb-foe.acting .ebb-ftag,.ebb-prow.acting .ebb-pname b{color:var(--eb-amber-hi)}
.ebb-foe.acting .ebb-sil,.ebb-hero.acting .ebb-sil{
  filter:drop-shadow(0 9px 10px #0009) drop-shadow(0 0 10px #ffdca6b0)}
.ebb-prow.acting{background:linear-gradient(90deg,#f0b45c2e,#f0b45c0d 70%,#f0b45c00)}
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
/* Reduced motion kills the idle bob, the caret bob, the hit shake and the
   step-forward — all decoration. It NEVER kills the damage number (it carries
   the outcome of the turn) nor the KO fade (it says who is down), so those two
   still play. */
@media (prefers-reduced-motion:reduce){
  .ebb-sil,.ebb-sil.hit,.ebb-prow.hit,.ebb-mark{animation:none}
  .ebb-stand,.ebb-hero.act .ebb-stand,.ebb-foe.act .ebb-stand{transition:none;transform:none}
  /* the new furniture. The gauge BANDS, the damage number's SIZE and the hurt
     flash's COLOUR are all information and stay; only the idling and the
     sliding stop. */
  .ebb-php.low .tk{animation:none;box-shadow:inset 0 1px 3px #000d,0 0 0 2px #ff5a4b4d}
  .ebb-cmd,.ebb-item,.ebb-prow{transition:none}
  .ebb-cmd.cur,.ebb-item.cur{transform:none}
  .ebb-cmdwin{transition:opacity var(--eb-t-fast) linear;transform:none}
  .ebb-logtxt.beat,.ebb-sub.on,.ebb-obox,.ebb-ofoot{animation:none}
  .ebb-obox{opacity:1;transform:none}}`;
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
      f.textContent = ':root{--eb-ink:#f3f5ff;--eb-ink-dim:#c2caee;--eb-ink-faint:#8e97c6;' +
        '--eb-amber:#f0b45c;--eb-amber-hi:#ffdca6;--eb-amber-dim:#b1803a;' +
        '--eb-win:linear-gradient(180deg,#0e1038e6,#2a2b8ce8);' +
        '--eb-win-head:linear-gradient(180deg,#0a0b2af0,#15165af0);' +
        '--eb-bevel-lt:#eef1ff;--eb-bevel-dk:#7b84c0;--eb-edge:#04051a;--eb-rule:#4a53a8;' +
        '--eb-inset-lt:#ffffff3d;--eb-inset-dk:#00021e8c;' +
        '--eb-track:#05061f;--eb-hp:linear-gradient(180deg,#ffdca6,#bd8330);' +
        '--eb-hp-warn:linear-gradient(180deg,#ffc48a,#b4551c);' +
        '--eb-hp-low:linear-gradient(180deg,#ffb4a0,#a83426);--eb-hp-ghost:#ff5a4bb0;' +
        // the ramp and the motion tokens, so a kit-less page is still a TV UI
        '--eb-fs-2xs:clamp(10px,.60vw,15px);--eb-fs-xs:clamp(11px,.70vw,17px);' +
        '--eb-fs-sm:clamp(12.5px,.82vw,20px);--eb-fs-md:clamp(14px,.95vw,23px);' +
        '--eb-fs-lg:clamp(16px,1.15vw,28px);--eb-fs-xl:clamp(19px,1.45vw,35px);' +
        '--eb-fs-2xl:clamp(24px,2.0vw,48px);' +
        '--eb-ease-out:cubic-bezier(.16,1,.3,1);--eb-ease-in:cubic-bezier(.55,0,1,.45);' +
        '--eb-ease-soft:cubic-bezier(.33,1,.68,1);' +
        '--eb-t-fast:120ms;--eb-t-med:220ms;--eb-t-slow:380ms;' +
        '--eb-t-ghost:560ms;--eb-t-ghost-wait:220ms;' +
        '--eb-card:linear-gradient(180deg,#ffffff14 0%,#00042426 100%);' +
        '--eb-face:system-ui,sans-serif;--eb-mono:ui-monospace,Menlo,monospace}' +
        '@keyframes eb-danger{0%,100%{box-shadow:inset 0 1px 3px #000d}' +
        '50%{box-shadow:inset 0 1px 3px #000d,0 0 0 2px #ff5a4b4d}}' +
        '@keyframes eb-fade{from{opacity:0}to{opacity:1}}' +
        '.eb-win{border-radius:8px;border:1px solid var(--eb-edge);background:var(--eb-win);' +
        'box-shadow:inset 2px 2px 0 var(--eb-bevel-lt),inset -2px -2px 0 var(--eb-bevel-dk),' +
        'inset 0 0 0 3px #00021e3d,0 10px 30px #000a}' +
        '.eb-cur{flex:0 0 1.05em;display:inline-block;width:1.05em;height:1em}' +
        '.eb-cur.on{background:var(--eb-amber);' +
        'clip-path:polygon(0 30%,45% 30%,45% 8%,100% 50%,45% 92%,45% 70%,0 70%)}' +
        // the command window's title bar now carries a bust and a name, so a
        // kit-less page needs enough of .eb-wtitle/.eb-port for it to have a shape
        '.eb-wtitle{display:flex;align-items:center;gap:8px;padding:5px 12px;' +
        'font:700 var(--eb-fs-xs)/1.25 var(--eb-face);letter-spacing:.13em;' +
        'text-transform:uppercase;color:var(--eb-amber);background:var(--eb-win-head);' +
        'border-bottom:1px solid var(--eb-rule);border-radius:6px 6px 0 0}' +
        '.eb-port{flex:0 0 auto;border-radius:5px;background-color:#0b0d33;' +
        'background-repeat:no-repeat;background-size:190%;background-position:50% 14%}';
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

  // ===== THE 3D ARENA, LAZILY ===============================================
  // battle_stage3d.js is NOT in play3d.html's script list — that file is
  // coordinator custody and read-only to this agent — so this module fetches its
  // own sibling the first time a battle starts on a page that has THREE. A page
  // without THREE (or without WebGL) never issues the request and never leaves
  // the DOM stage. The URL is derived from THIS script's own src, so it follows
  // the page wherever it is mounted (play3d, ui_mock's <base>, a harness).
  const SELF_URL = (function () {
    try {
      const s = document.currentScript && document.currentScript.src;
      if (s) return s.replace(/[^/]*$/, 'battle_stage3d.js');
    } catch (e) { }
    return 'js/battle_stage3d.js';
  })();
  let stagePromise = null;
  function loadStage3d() {
    if (stagePromise) return stagePromise;
    if (!HAS_DOM || !window.THREE || !window.THREE.GLTFLoader || Battle.stage3d === false) {
      return (stagePromise = Promise.resolve(null));
    }
    if (window.BattleStage3D) return (stagePromise = Promise.resolve(window.BattleStage3D));
    return (stagePromise = new Promise((resolve) => {
      const s = document.createElement('script');
      s.src = SELF_URL;
      s.async = true;
      s.onload = () => resolve(window.BattleStage3D || null);
      s.onerror = () => { console.warn('[Battle] no 3D stage at', SELF_URL, '— DOM stage'); resolve(null); };
      document.head.appendChild(s);
      // never let a hung request hold up a battle: the DOM stage is right there
      setTimeout(() => resolve(window.BattleStage3D || null), 2500);
    }));
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
      // STAGE BODIES, keyed the same way. A foe's stage body IS its nodes entry;
      // a party member's nodes entry is their STATUS ROW, so their body on the
      // field lives here — and is absent for anyone with no pose art, which is
      // what makes "no sprite" a silent, total non-event everywhere below.
      bodies: {},                // combatantId -> {el, sil, stand}
      qnodes: {},                // combatantId -> its TURN QUEUE row
      acted: Object.create(null),// who has already acted this round
      actor: null,               // who is resolving (or being decided for) right now
      pending: null,             // the live decision request
      state: cfg.state,
      round: 0,
      cmds: ['Attack', 'Item', 'Flee'],
    };

    const root = document.createElement('div');
    root.className = 'ebb-root';
    root.innerHTML =
      '<div class="ebb-bg"></div><div class="ebb-vig"></div><div class="ebb-scrim"></div>' +
      '<div class="ebb-hurt"></div>' +
      // THE MESSAGE LINE LIVES AT THE TOP (user ruling 2026-07-31), full width
      // inside the frame margin, with the zone/round chip and the seat chip on a
      // rail above it. It is the thing the player reads every beat, so it gets
      // the top of the screen and the whole of it.
      '<div class="ebb-top">' +
        '<div class="ebb-rail">' +
          '<div class="eb-win ebb-hud"><span class="zone"></span><span class="rnd"></span></div>' +
          '<div class="eb-win ebb-seatwin seat"></div>' +
        '</div>' +
        // the actor chip lives at the HEAD of the message line: who is up, then
        // what they are doing, in one band, in reading order
        '<div class="eb-win ebb-log"><span class="ebb-actor"></span>' +
          '<span class="ebb-logtxt"></span>' +
          '<span class="ebb-hint"></span></div>' +
      '</div>' +
      // PARTY LEFT, FOES RIGHT (user ruling 2026-07-31) — the DOM stage mirrors
      // with the arena, so the two never disagree about which side you are on.
      '<div class="ebb-field"><div class="ebb-stage">' +
        '<div class="ebb-heroes"></div><div class="ebb-foes"></div></div></div>' +
      '<div class="ebb-bottom">' +
        '<div class="ebb-band">' +
          '<div class="eb-win ebb-cmdwin"><span class="eb-wtitle"><span>Command</span></span>' +
            '<div class="ebb-cmds idle"></div><div class="eb-win ebb-sub"></div></div>' +
          '<div class="eb-win ebb-partywin">' +
            '<div class="ebb-phead"><span></span><span></span><span>TURN ORDER</span>' +
              '<span>HP</span><span class="r">MP</span></div>' +
            '<div class="ebb-party"></div>' +
          '</div>' +
        '</div>' +
      '</div>';
    host.appendChild(root);
    const q = (c) => root.querySelector('.ebb-' + c);
    const qq = (c) => root.querySelector('.' + c);

    // ---- THE 3D ARENA -------------------------------------------------------
    // Built FIRST, because whether it exists changes how the combatant furniture
    // below is built. It is built at all only if battle_stage3d.js loaded (it is
    // fetched during the entry fade) AND a WebGL context is really obtainable —
    // a probe, not a user-agent guess. If create() returns null for any reason we
    // fall through to the DOM stage with nothing half-built behind us, which is
    // exactly why it is constructed before a single body element exists.
    let stage = null;
    const S3D = (!cfg.noStage3d && window.BattleStage3D && Battle.stage3d !== false &&
                 window.BattleStage3D.available()) ? window.BattleStage3D : null;
    if (S3D) {
      try {
        stage = S3D.create({
          mount: root, zone: cfg.zone, backdrop: cfg.backdrop || cfg.zone,
          familyOf: cfg.familyOf,
          // WHAT THE PARTY IS HOLDING. The stage owns pixels and geometry and never
          // reads GS — that seam is the reason this is a callback and not a lookup
          // inside the arena. The screen already knows the world; the arena only
          // needs an item id per character.
          weaponOf: cfg.weaponOf || null,
          party: (cfg.state.party || []).map(c => ({ id: c.id, ref: c.ref || c.id, dead: !!c.dead })),
          foes: (cfg.state.foes || []).map(c => ({ id: c.id, ref: c.ref, dead: !!c.dead })),
          onFrame: syncAnchors,
        });
      } catch (e) { console.warn('[Battle] 3D arena failed, falling back to the DOM stage', e); stage = null; }
    }
    S.stage = stage;
    if (stage) root.classList.add('ebb-3d');

    // The plate is the 3D backdrop's texture in arena mode; painting it into the
    // DOM as well would decode 2.5 MB twice for a layer that is display:none.
    if (!stage) paintBackdrop(q('bg'), cfg.backdrop, cfg);
    qq('zone').textContent = (cfg.zone || 'battle').toUpperCase();
    q('hint').innerHTML = '<b>WASD/&larr;&uarr;&darr;&rarr;</b> move &middot; ' +
      '<b>E/Enter</b> confirm &middot; <b>Esc/Q</b> back';
    // and it starts MUTED: nothing has been said yet, and an empty full-width
    // window across the top of the arena during the entry fade is the same
    // dead slab the outro used to leave there. The first message brings it in.
    q('log').classList.add('mute');

    // --- build combatant nodes ---
    // The shape is built FIRST and is what shows if no sprite resolves; the
    // sprite quietly takes its place once it decodes. Missing art degrades to
    // the old look rather than to a hole.
    function silEl(family, monsterId, i) {
      const d = sprites[family] || sprites.default;
      const wrap = document.createElement('div');
      wrap.className = 'ebb-sil';
      wrap.style.animationDelay = (i * 0.37).toFixed(2) + 's';
      // in arena mode the body is a mesh in the scene: the CSS silhouette and its
      // sprite probe are dead weight (and a second 404 per monster), so skip them
      if (stage) return wrap;
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
    // THE STAND: the seat on the ground. Everything that stands on the field is
    // wrapped in one, so the cast shadow and the step-forward are written once
    // and a hero and a monster are the same kind of object to the stage.
    function stand(sil) {
      const st = document.createElement('div');
      st.className = 'ebb-stand';
      st.appendChild(sil);
      return st;
    }
    const foesBox = q('foes'), heroBox = q('heroes'), partyBox = q('party');
    (cfg.state.foes || []).forEach((c, i) => {
      const el = document.createElement('div');
      el.className = 'ebb-foe';
      const mark = document.createElement('div'); mark.className = 'ebb-mark';
      const sil = silEl(cfg.familyOf ? cfg.familyOf(c.ref) : 'default', c.ref, i);
      const st = stand(sil);
      const tags = document.createElement('div'); tags.className = 'ebb-ftags';
      const name = document.createElement('div'); name.className = 'ebb-ftag'; name.textContent = c.name;
      const bar = document.createElement('div'); bar.className = 'ebb-fbar';
      // the chase bar goes in FIRST (it sits behind the fill and lags it)
      const ghost = document.createElement('i'); ghost.className = 'gh';
      ghost.style.width = '100%'; bar.appendChild(ghost);
      const fill = document.createElement('i'); fill.style.width = '100%'; bar.appendChild(fill);
      tags.appendChild(name);
      if (Battle.showFoeHp) tags.appendChild(bar);
      el.appendChild(mark); el.appendChild(st); el.appendChild(tags);
      foesBox.appendChild(el);
      S.nodes[c.id] = { el: el, sil: sil, fill: fill, ghost: ghost, bar: bar, txt: null, name: name };
      S.bodies[c.id] = { el: el, sil: sil, stand: st, anchored: !!stage };
    });
    // THE PARTY ON THE FIELD. Their sprite is their pose plate, chroma-keyed by
    // ui_kit; the request is fired now and MOUNTS WHEN IT RESOLVES, so a battle
    // never waits on a 1.4 MB PNG and a character with no plate (or a page with
    // no ui_kit at all) is simply not on the field. Order matches the status
    // table, and the box is bottom-aligned, so a short and a tall hero share the
    // ground line whatever their plates measure.
    //
    // IN ARENA MODE this is inverted: every party member has a body in the scene
    // (model, or the ruled billboard, or a proxy solid), so the anchor exists up
    // front and unconditionally, and the pose plate is the STAGE's business — it
    // is fetched there, through the same EBUI.poseSprite cache, only if no model
    // resolves. A hero is never missing from an arena.
    (cfg.state.party || []).forEach((c, i) => {
      const k = EB();
      if (!stage && (!k || !k.poseSprite)) return;
      const el = document.createElement('div');
      // seated in PARTY ORDER right now and revealed when (if) its plate lands —
      // appending on resolve would leave the party standing in whatever order
      // four PNGs happened to decode in.
      el.className = 'ebb-hero' + (stage ? '' : ' pending');
      const sil = document.createElement('div');
      sil.className = 'ebb-sil';
      sil.style.animationDelay = (i * 0.53).toFixed(2) + 's';
      const st = stand(sil);
      el.appendChild(st);
      heroBox.appendChild(el);
      if (stage) {
        S.bodies[c.id] = { el: el, sil: sil, stand: st, anchored: true };
        if (c.dead) el.classList.add('down');
        return;
      }
      Promise.resolve(k.poseSprite(c.ref || c.id)).then((canvas) => {
        if (!canvas || !el.parentNode) return;
        canvas.setAttribute('aria-hidden', 'true');
        sil.appendChild(canvas);
        el.classList.remove('pending');
        S.bodies[c.id] = { el: el, sil: sil, stand: st };
        if (c.dead) el.classList.add('down');
      }).catch(() => { /* no field art for this character — the table still has them */ });
    });
    // THE PROJECTION PASS. Called by the stage after every rendered frame: it
    // parks each combatant's DOM furniture over their 3D body and sizes the box
    // to the body's screen rectangle. This is the whole of the 2D/3D join — six
    // style writes per combatant per frame, and no layout in between.
    function syncAnchors() {
      if (!stage) return;
      for (const id in S.bodies) {
        const b = S.bodies[id];
        if (!b.anchored) continue;
        const a = stage.anchor(id);
        if (!a) continue;
        const el = b.el, s = el.style;
        s.left = a.x.toFixed(1) + 'px';
        s.top = (a.y - a.h).toFixed(1) + 'px';
        s.height = a.h.toFixed(1) + 'px';
        if (el._vis !== a.vis) { el._vis = a.vis; s.visibility = a.vis ? '' : 'hidden'; }
      }
    }
    // ===== THE TURN QUEUE =====================================================
    // User ruling 2026-07-31: the party panel becomes an EVER-UPDATING QUEUE of
    // whose turn comes next, MONSTERS INCLUDED — "this is the panel that lets the
    // player plan", which is the entire reason enemies are in it.
    //
    // ITS ORDER IS NEVER COMPUTED HERE. It comes from Battle.queueFeed, whose
    // default asks the kernel's rules.order(state) — the SAME function the
    // commit-then-resolve scheduler ranks collected actions by. Displayed order
    // is therefore resolution order by construction, not by agreement, and it
    // cannot drift.
    //
    // ROWS ARE BUILT ONCE AND REORDERED, never re-rendered: appendChild MOVES a
    // node, so the HP gauges keep their transitions and the busts never flicker.
    //
    // THE PARTY STATUS TABLE: one row per member — bust, name/level, HP gauge
    // with numerals, and the reserved MP column.
    (cfg.state.party || []).forEach((c) => {
      const el = document.createElement('div');
      el.className = 'ebb-prow';
      const bust = cfg.bustFor ? cfg.bustFor(c.ref || c.id) : null;
      el.innerHTML = '<span class="eb-cur"></span>' +
        '<div class="eb-port ebb-pport" style="width:30px;height:30px' +
          (bust ? ';background-image:url(&quot;' + bust + '&quot;)' : '') + '"></div>' +
        '<div class="ebb-pname"><b></b><small></small></div>' +
        '<div class="ebb-php"><span class="tk"><i class="gh"></i><i></i></span>' +
          '<span class="nm"><b class="hp"></b>/<span class="mx"></span></span></div>' +
        '<div class="ebb-pmp">—</div>';
      el.querySelector('.ebb-pname b').textContent = c.name;
      el.querySelector('.ebb-pname small').textContent = 'LV ' + (c.level || 1);
      if (!bust) el.querySelector('.ebb-pport').classList.add('miss');
      partyBox.appendChild(el);
      S.nodes[c.id] = { el: el, sil: el, fill: el.querySelector('.ebb-php .tk>i:not(.gh)'),
                        ghost: el.querySelector('.ebb-php .tk>i.gh'),
                        txt: el.querySelector('.ebb-php .nm'), bar: el.querySelector('.ebb-php'),
                        cursor: el.querySelector('.eb-cur') };
      S.qnodes[c.id] = { el: el, cursor: el.querySelector('.eb-cur') };
    });
    // FOE ROWS: slimmer on purpose — the party rows stay visually primary because
    // they carry the vital gauges. A foe gets its sprite thumbnail, the SAME name
    // the field tag shows (Duskpad A / B, so the queue and the field agree about
    // who is who), and a small HP bar. Same grid as the party row, so every column
    // lines up down the panel.
    (cfg.state.foes || []).forEach((c) => {
      const el = document.createElement('div');
      el.className = 'ebb-qrow';
      const icon = cfg.foeIcon ? cfg.foeIcon(c.ref) : null;
      el.innerHTML = '<span class="eb-cur"></span>' +
        '<div class="ebb-qic"' + (icon ? ' style="background-image:url(&quot;' + icon + '&quot;)"' : '') + '></div>' +
        '<div class="ebb-qname"></div>' +
        '<div class="ebb-qhp"><span class="tk"><i class="gh"></i><i></i></span></div>' +
        '<div class="ebb-pmp">—</div>';
      el.querySelector('.ebb-qname').textContent = c.name;
      partyBox.appendChild(el);
      S.qnodes[c.id] = { el: el, cursor: el.querySelector('.eb-cur'),
                         fill: el.querySelector('.ebb-qhp .tk>i:not(.gh)'),
                         ghost: el.querySelector('.ebb-qhp .tk>i.gh'),
                         bar: el.querySelector('.ebb-qhp') };
    });
    // Order it ONCE at construction, or the panel shows the order the rows were
    // BUILT in (party then foes) for the whole entry fade — which is the one
    // moment the player is looking straight at it, deciding what to do first.
    renderQueue();

    // --- rendering ---
    function nameOf(id) {
      const c = window.Rules.findById(S.state, id);
      return c ? c.name : id;
    }
    // THE THREE-BAND VOCABULARY, borrowed from the kit so a monster's pip, a
    // hero's gauge and the pause menu all mean the same thing by the same
    // colour. The fallback matches EBUI.band exactly — a page without ui_kit
    // must not have a different idea of "nearly dead".
    function band(f) {
      const k = EB();
      if (k && k.band) { try { return k.band(f); } catch (e) { } }
      return f <= 0.25 ? ' low' : f <= 0.5 ? ' warn' : '';
    }
    function setBand(el, f) {
      if (!el) return;
      const b = band(f);
      el.classList.toggle('warn', b === ' warn');
      el.classList.toggle('low', b === ' low');
    }
    // A NUMBER THAT MOVES WITH ITS BAR. speed:0 (every suite, every automated
    // caller) snaps, because a tween there is a delay nobody watches.
    function setNum(el, v) {
      const k = EB();
      if (S.speed && k && k.tweenNum) { try { return k.tweenNum(el, v, 300); } catch (e) { } }
      el.textContent = String(v);
    }
    function syncHp(state) {
      S.state = state || S.state;
      for (const c of S.state.party.concat(S.state.foes)) {
        const n = S.nodes[c.id]; if (!n) continue;
        const f = clamp01(c.maxHp ? c.hp / c.maxHp : 0);
        const w = (f * 100).toFixed(1) + '%';
        n.fill.style.width = w;
        // the chase bar is written to the SAME width; its own delay and easing
        // are what leave a red sliver showing what the last blow cost
        if (n.ghost) n.ghost.style.width = w;
        if (n.txt) {
          // the numerals are two elements (current bright, max dim), so this
          // writes the parts rather than the whole string
          const cur = n.txt.querySelector('.hp'), mx = n.txt.querySelector('.mx');
          if (cur && mx) { setNum(cur, c.hp); mx.textContent = c.maxHp; }
          else n.txt.textContent = c.hp + '/' + c.maxHp;
        }
        setBand(n.bar, f);
        if (c.side === 'foe') n.el.classList.toggle('dead', !!c.dead);
        else {
          n.el.classList.toggle('down', !!c.dead);
          const b = S.bodies[c.id];              // and the body on the field, if she has one
          if (b) b.el.classList.toggle('down', !!c.dead);
        }
        // and the body in the arena: setDead is idempotent, so calling it on
        // every sync is how "who is down" stays true without a second bookkeeper
        if (stage) stage.setDead(c.id, !!c.dead);
        // ...and the foe's row in the turn queue, which has its own small bar
        const qn = S.qnodes[c.id];
        if (qn && qn.fill && qn !== n) {
          qn.fill.style.width = w;
          if (qn.ghost) qn.ghost.style.width = w;
          setBand(qn.bar, f);
          qn.el.classList.toggle('dead', !!c.dead);
        }
      }
      qq('rnd').textContent = 'ROUND ' + S.round;
    }
    // THE QUEUE, REDRAWN. Pending combatants first in resolution order, then the
    // ones who have already gone, greyed at the round's tail. Rows are MOVED by
    // appendChild rather than rebuilt, so gauges keep animating across the
    // reorder and nothing flickers.
    function renderQueue() {
      const feed = Battle.queueFeed;
      let list = [];
      try { list = feed.upcoming(S.state, { acted: S.acted, actor: S.actor }) || []; }
      catch (e) { return; }
      const box = q('party');
      const seen = Object.create(null);
      for (const row of list) {
        const n = S.qnodes[row.id];
        if (!n) continue;
        seen[row.id] = 1;
        n.el.classList.toggle('done', !!row.acted);
        n.el.classList.toggle('now', row.id === S.actor && !row.acted);
        if (n.cursor) n.cursor.classList.toggle('on', row.id === S.actor);
        box.appendChild(n.el);                       // MOVES the existing node
      }
      // anyone the feed dropped (KO'd — order() returns the living only) leaves
      // the queue immediately, which is the ruling's "on KO the row exits"
      for (const id in S.qnodes) {
        if (!seen[id]) S.qnodes[id].el.classList.add('gone');
        else S.qnodes[id].el.classList.remove('gone');
      }
    }
    // THE MESSAGE LINE. Three jobs beyond writing text: it re-triggers its own
    // entrance so a NEW line is visibly new (two consecutive "takes 6 damage"
    // lines used to be indistinguishable from a frozen screen); it HIDES the
    // whole window when there is nothing to say, rather than leaving an empty
    // blue slab across the top of the arena; and it never fights the actor chip
    // beside it for the mute decision.
    function logLine(html) {
      const t = q('logtxt');
      t.innerHTML = html == null ? '' : html;
      q('log').classList.toggle('mute', !html && !S.chip);
      if (!html) return;
      t.classList.remove('beat'); void t.offsetWidth; t.classList.add('beat');
    }
    // WHOSE TURN IT IS, at the head of the message line and in the command
    // window's own title bar. Hero or monster: the complaint the ruling of
    // 2026-07-31 came from was not being able to see an enemy action coming, and
    // a chip that only ever showed party members would answer half of it.
    function actorArt(c) {
      if (!c) return null;
      if (c.side === 'foe') return cfg.foeIcon ? cfg.foeIcon(c.ref) : null;
      return cfg.bustFor ? cfg.bustFor(c.ref || c.id) : null;
    }
    function faceHtml(c) {
      const url = actorArt(c);
      if (!url) return '';
      return '<div class="' + (c.side === 'foe' ? 'ebb-qic' : 'eb-port') +
        '" style="background-image:url(&quot;' + url + '&quot;)"></div>';
    }
    function setActorChip(id) {
      const el = q('actor'); if (!el) return;
      const c = id == null ? null : window.Rules.findById(S.state, id);
      S.chip = c ? String(id) : null;
      if (!c) { el.className = 'ebb-actor'; el.innerHTML = ''; return; }
      el.className = 'ebb-actor on' + (c.side === 'foe' ? ' foe' : '');
      el.innerHTML = faceHtml(c) + '<b>' + esc(c.name) + '</b>';
      q('log').classList.remove('mute');
    }
    // The command window titles itself with the character it is deciding for
    // (FF9's idiom) and lights up while it is live, so the handoff between
    // actors is something you SEE at the bottom-left instead of inferring from
    // a chip in the opposite corner.
    function setCmdTitle(id) {
      const win = q('cmdwin'); if (!win) return;
      const title = win.querySelector('.eb-wtitle');
      const c = id == null ? null : window.Rules.findById(S.state, id);
      win.classList.toggle('live', !!c);
      if (!title) return;
      title.innerHTML = c ? faceHtml(c) + '<span>' + esc(c.name) + '</span>'
                          : '<span>Command</span>';
    }
    // THE HURT FLASH — the party took a hit. It reads when the player is looking
    // at the monster they aimed at rather than at their own gauge, which is
    // exactly when a bar sliding by four pixels does not.
    function hurtFlash() {
      const h = q('hurt'); if (!h) return;
      h.classList.remove('on'); void h.offsetWidth; h.classList.add('on');
    }
    // A number pops over the BODY that took the hit — that is where the eye
    // already is. Only a party member with no field sprite falls back to their
    // status row, which is the one place they exist on screen.
    function floatNum(id, text, kind) {
      const host = (S.bodies[id] || S.nodes[id] || {}).el;
      if (!host) return;
      const e = document.createElement('div');
      e.className = 'ebb-num' + (kind ? ' ' + kind : '');
      e.textContent = text;
      host.style.position = 'relative';
      host.appendChild(e);
      setTimeout(() => { if (e.parentNode) e.parentNode.removeChild(e); }, 1000);
    }
    // The flinch runs on BOTH surfaces: the body on the field and the status row,
    // so a hit reads whichever one you happened to be looking at.
    function hitShake(id) {
      if (stage) stage.flinch(id);                        // the arena knocks the body back
      const a = S.nodes[id] && S.nodes[id].sil, b = S.bodies[id] && S.bodies[id].sil;
      for (const t of (a === b ? [a] : [a, b])) {          // a foe's row IS its body
        if (!t) continue;
        // a projected anchor is positioned by transform every frame — a CSS
        // shake on it would be overwritten; in the arena the body does the work
        if (stage && t.classList.contains('ebb-sil')) continue;
        t.classList.remove('hit'); void t.offsetWidth; t.classList.add('hit');
      }
    }
    // The step forward — and, in the arena, THE APPROACH. It returns the number of
    // milliseconds until the blow lands, and the caller waits exactly that before
    // firing the damage event. It used to wait a constant (pacing.wind) while the
    // body travelled a fixed 1.35 m of a 5.21 m gap, so the flash and the number
    // landed on a body four metres from the swing. The stage derives the travel
    // from the target's own body and times the swing to the clip's own contact
    // frame, so only the stage can say when — see battle_stage3d act().
    function stepIn(id, kind, target) {
      if (stage) return stage.act(id, kind, target, beat('approach') + beat('wind'));
      const b = S.bodies[id]; if (!b) return null;
      b.el.classList.add('act');
      setTimeout(() => b.el.classList.remove('act'), 360 * (S.speed || 1));
      return null;                                        // the DOM stage keeps the old beat
    }

    // --- the event feed (this is what makes `emit` awaited in the kernel) -----
    // THE BEATS ARE THE POINT NOW. User ruling 2026-07-31: enemy actions resolved
    // "too fast to read". A turn is no longer one 170 ms blur — it is ANNOUNCED
    // (message + a ring under the actor, so you know who is about to move), then
    // a beat, then the body moves, then the damage lands and is read, then a
    // settle before the next actor. Every wait is `Battle.pacing.<beat> * speed`,
    // so speed:0 is still instant and every suite and automated caller is
    // untouched, while a human gets a cadence they can follow.
    //
    // `say()` is the other half: it writes the message AND owns the beat, so a
    // message cannot be evicted by the next event before it has been on screen
    // for its own duration. Before, the log was overwritten on the next line of
    // code and the wait was a separate number that could be shorter.
    const beat = k => (Battle.pacing[k] || 0) * S.speed;
    const say = async (html, k) => { logLine(html); await wait(beat(k)); };
    let acted = false;                       // has anyone moved yet this battle?
    async function play(events, state) {
      for (const ev of events) {
        S.state = state || S.state;
        switch (ev.t) {
          case 'round':
            // a new round: everyone is pending again, and the queue reprojects
            S.round = ev.n; S.acted = Object.create(null); S.actor = null;
            syncHp(state); renderQueue(); break;
          case 'action': {
            // a settle between actors, so two turns never run together
            if (acted) { markActing(null); await wait(beat('settle')); }
            acted = true;
            const who = '<em>' + esc(nameOf(ev.by)) + '</em>';
            markActing(ev.by);               // THE TELL: a ring under whoever is up
            if (ev.kind === 'attack') await say(who + ' attacks!', 'announce');
            else if (ev.kind === 'item') await say(who + ' uses ' + esc(cfg.itemName(ev.item)) + '.', 'announce');
            else if (ev.kind === 'flee') await say(who + ' tries to flee…', 'announce');
            else await say(who + ' ' + esc(ev.kind) + 's.', 'announce');
            // THE DAMAGE EVENT WAITS FOR THE BLOW, not for a constant. A stage
            // that answers with a number owns the beat; anything else (the DOM
            // stage, a stage that refuses the action) keeps the whole
            // approach+wind budget, so the turn's wall clock is the same either way.
            // FLEE IS A BEAT NOW (2026-08-08). It used to be the one action that
            // moved no body at all — the stage's flee verb was `return` — so
            // "tries to flee…" was a line of text over four people standing still.
            // It gets the same call every other action gets; what it does NOT get is
            // the wind wait, because the beat it is waiting for is the kernel's
            // answer, which arrives on the very next event.
            {
              const c = stepIn(ev.by, ev.kind, ev.target);
              if (ev.kind !== 'flee') {
                await wait(typeof c === 'number' && c > 0 ? c : beat('approach') + beat('wind'));
              }
            }
            break;
          }
          case 'damage': {
            syncHp(state); hitShake(ev.target);
            // SIZE BY WHAT IT COST THE TARGET, not by a constant: a third of
            // someone's health looks like a third of someone's health. Amber for
            // a crit if the kernel ever emits one.
            const t = window.Rules.findById(S.state, ev.target);
            const frac = (t && t.maxHp) ? ev.amount / t.maxHp : 0;
            floatNum(ev.target, String(ev.amount),
              ev.crit ? 'crit' : frac >= 0.34 ? 'big' : frac <= 0.12 ? 'tap' : '');
            if (t && t.side !== 'foe') hurtFlash();
            await say('<em>' + esc(nameOf(ev.target)) + '</em> takes ' + ev.amount + ' damage.', 'damage');
            break;
          }
          case 'heal':
            syncHp(state); floatNum(ev.target, '+' + ev.amount, 'heal');
            await say('<em>' + esc(nameOf(ev.target)) + '</em> recovers ' + ev.amount + ' HP.', 'heal');
            break;
          case 'ko':
            syncHp(state); renderQueue();          // order() drops the dead: the row exits
            if (String(ev.id) === S.actor) { S.actor = null; }
            await say('<em>' + esc(nameOf(ev.id)) + '</em> ' +
                      (ev.side === 'foe' ? 'is defeated!' : 'falls!'), 'ko');
            break;
          case 'flee':
            // the picture and the line land together: away into the haze, or back
            // to the slot facing the enemy again
            if (stage) { try { stage.flee(ev.by, ev.ok); } catch (e) { } }
            await say(ev.ok ? 'Got away safely!' : 'Cornered — no escape!', 'flee');
            break;
          case 'noop':
            if (ev.why === 'round-cap') await say('The fight breaks off.', 'ko');
            break;
          case 'end':
            markActing(null); syncHp(state); break;
        }
      }
      syncHp(state);
    }
    // WHO IS ACTING, shown on the field. The same ring the decision cursor uses,
    // because "this one is up" means the same thing whether a player or the AI is
    // deciding — and an enemy about to swing is exactly what the player said they
    // could not see coming.
    function markActing(id) {
      // whoever was up has now gone: they sink to the tail of this round's queue
      if (id == null && S.actor != null) S.acted[S.actor] = 1;
      S.actor = id == null ? null : String(id);
      setActorChip(id);                 // the face at the head of the message line
      for (const k in S.nodes) {
        const n = S.nodes[k];
        if (n && n.el) n.el.classList.toggle('acting', k === String(id));
      }
      for (const k in S.bodies) {
        const b2 = S.bodies[k];
        if (b2 && b2.el) b2.el.classList.toggle('acting', k === String(id));
      }
      if (stage) stage.setActor(id == null ? null : id);
      renderQueue();
    }

    // --- the decision cursor -------------------------------------------------
    // One request at a time per screen; a second seat would get its own cursor
    // object (the scheduler already collects seats concurrently).
    function promptAction(actorId, state, api) {
      S.state = state;
      return new Promise((resolve) => {
        S.pending = { actorId, api, resolve, mode: 'cmd', ci: 0, ti: 0, ii: 0, items: [] };
        // DECISION PHASE: the queue shows the round's PROJECTED resolution order,
        // which is the whole point of the panel — you choose knowing who moves
        // before you do. The character being decided for carries the cursor.
        S.actor = String(actorId);
        renderQueue();
        for (const c of state.party) markActor(c.id, c.id === actorId);
        qq('seat').textContent = (api && api.seatName ? api.seatName.toUpperCase() + ' · ' : '') +
          nameOf(actorId);
        // WHOSE TURN, said twice on purpose: at the head of the message line
        // (where the eye already is) and on the command window that is about to
        // take the keystroke (where the hands already are).
        setActorChip(actorId);
        setCmdTitle(actorId);
        renderMenu();
      });
    }
    function livingFoes() { return S.state.foes.filter(c => !c.dead); }
    // the status row that is deciding gets the cursor glyph, exactly like a
    // menu row — one cursor grammar across the whole game
    function markActor(id, on) {
      const b = S.bodies[id];                 // the body on the field gets a rim light
      if (b) b.el.classList.toggle('cur', !!on);
      // ...and a pale ring at her feet in the arena. Only the TRUE case writes:
      // markActor is called in a loop over the party, so clearing on the false
      // case would erase the ring the same tick it was drawn. settle() clears.
      if (stage && on) stage.setActor(id);
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
        // the actor chip beside this line already names them in amber caps, and
        // the command window's title says it a third time — one is enough here
        logLine('What will you do?');
      }
    }
    // THE TARGET MARK. In the DOM stage it is the caret glyph over the foe; in
    // the arena it is that caret PLUS an amber ring pulsing at the target's feet
    // and its name tag lit — the "ring or arrow at the target's feet + name tag"
    // the ruling asks for. The keyboard flow above is untouched by either.
    function markFoe(id) {
      for (const c of S.state.foes) {
        const n = S.nodes[c.id]; if (n) n.el.classList.toggle('cur', c.id === id);
      }
      if (stage) stage.setTarget(id === -1 ? null : id);
    }
    function settle(action) {
      const p = S.pending; if (!p) return;
      S.pending = null;
      for (const c of S.state.party) markActor(c.id, false);
      if (stage) stage.setActor(null);
      markFoe(-1);
      setCmdTitle(null);          // the window dims and steps back until it is asked again
      renderMenu();
      p.resolve(action);
    }
    // returns true if the key was consumed
    function onKey(a) {
      const p = S.pending;
      if (S.outro) {
        if (a === 'confirm' || a === 'cancel') {
          // FIRST press skips the tally to its final values, SECOND leaves. A
          // player who wants the numbers now gets them now, and one who mashes
          // Enter never blows past the screen without seeing the totals.
          if (S.tallySkip && !S.tallyDone) { S.tallyDone = true; S.tallySkip(); return true; }
          const f = S.outro; S.outro = null; f();
        }
        return true;
      }
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
    // THE TALLY IS THE REWARD. User ruling 2026-07-31: animate the spoils —
    // classic FF. Gold counts up, each party member's XP bar FILLS, and when a
    // bar wraps it flashes and says LEVEL UP. The curve retune (k 25->10) means
    // that moment lands often, so it is worth making it feel like something.
    //
    // THE AWKWARD BIT, AND WHY IT IS DONE THIS WAY: at outro time the xp has NOT
    // been applied. Battle REPORTS xp/gold and `GS.applyBattleResult` applies
    // them afterwards — that separation is the contract that stops a battle
    // module owning the economy, and it is not being broken for an animation. So
    // the tally simulates the same curve GS will walk (cfg.xpToNext, handed in by
    // the caller) and animates from the party's real pre-battle values to where
    // GS is about to put them. If the two ever disagreed the bar would be lying,
    // which is why they read the SAME function rather than two copies of k.
    // WHICH HALF OF THE FRAME THE PARTY IS IN, ASKED RATHER THAN ASSUMED. The
    // diorama writes its handedness down once (BattleStage3D.CFG.partySide) but the
    // world arena SOLVES its camera yaw against the terrain, so the only honest
    // answer is where the bodies actually project this frame. null = no stage (the
    // DOM stage), and the box stays centred exactly as it was.
    function partySideOnScreen() {
      if (!stage || !stage.anchor || !S.state) return null;
      let sum = 0, n = 0;
      for (const c of S.state.party) {
        let a = null; try { a = stage.anchor(c.id); } catch (e) { }
        if (!a || a.vis === false) continue;
        sum += a.x; n++;
      }
      if (!n) return null;
      const w = root.getBoundingClientRect().width || window.innerWidth || 1;
      return (sum / n) < w / 2 ? 'pleft' : 'pright';
    }
    async function outro(result) {
      const titles = { victory: 'Victory', defeat: 'Defeated', fled: 'Escaped' };
      const box = document.createElement('div');
      const win = result.outcome === 'victory';
      box.className = 'ebb-outro' + (win ? (' ' + (partySideOnScreen() || '')) : '').trimEnd();
      const drops = (result.drops || []).map(id => cfg.itemName(id));
      const xpEach = win ? cfg.xpShare(result.xp) : 0;

      // one plan per member: the frames its bar will walk through
      const plan = (win && cfg.xpToNext) ? (cfg.tallyParty() || []).map((c) => {
        let lv = c.level, xp = c.xp, left = xpEach, ups = 0;
        const legs = [];
        // each leg is "fill from xp to `to` at this level"; a leg that reaches
        // the top is a level-up and the next leg starts empty one level higher
        let guard = 40;
        while (guard-- > 0) {
          const need = cfg.xpToNext(lv);
          if (xp + left < need) { legs.push({ lv, from: xp, to: xp + left, need, up: false }); break; }
          legs.push({ lv, from: xp, to: need, need, up: true });
          left -= (need - xp); xp = 0; lv++; ups++;
        }
        return { id: c.id, name: c.name, level: c.level, newLevel: lv, ups, legs };
      }) : [];

      // THE TWO NUMBERS THE FIGHT WAS FOR come out of the row list and become a
      // pair of big amber readouts at the top of the box. They used to be the
      // first two of four identical 13.5px rows, which is how you type a
      // receipt, not how you announce a reward.
      const rows = [];
      if (win && drops.length) rows.push(['Found', drops.join(', ')]);
      rows.push(['Rounds', result.turns]);
      const spoils = win
        ? '<div class="ebb-ospoils">' +
            '<div class="ebb-ospoil"><span class="l">EXPERIENCE</span>' +
              '<span class="v"><b class="oxp">0</b></span></div>' +
            '<div class="ebb-ospoil"><span class="l">GOLD</span>' +
              '<span class="v"><b class="ogold">0</b><small>g</small></span></div>' +
          '</div>'
        : '';

      box.innerHTML = '<div class="ebb-oscrim"></div>' +
        '<div class="eb-win ebb-obox"><span class="ebb-ohead">' +
        esc(titles[result.outcome] || result.outcome) + '</span><div class="ebb-obody">' +
        spoils +
        (plan.length ? '<div class="ebb-tally">' + plan.map((p, i) =>
          '<div class="ebb-trow" data-i="' + i + '">' +
            '<span class="nm">' + esc(p.name) + '</span>' +
            '<span class="lv">LV <b>' + p.level + '</b></span>' +
            '<span class="xb"><i style="width:' +
              (100 * p.legs[0].from / Math.max(1, p.legs[0].need)).toFixed(1) + '%"></i></span>' +
            '<span class="up">LEVEL UP!</span>' +
          '</div>').join('') + '</div>' : '') +
        rows.map(r => '<div class="ebb-orow"><span>' + esc(r[0]) + '</span><span class="n">' +
          esc(r[1]) + '</span></div>').join('') +
        '</div><div class="ebb-ofoot">ENTER TO CONTINUE</div></div>';
      // the message band has nothing left to say and no one left to point at, so
      // it steps off the top of the arena rather than sitting there empty
      setActorChip(null); setCmdTitle(null); logLine('');
      qq('seat').textContent = '';      // and the seat chip, or it hangs in the corner alone
      // ===== THE VICTORY IS A BEAT, NOT A STATE CHANGE (2026-08-08, BET I) =====
      // MEASURED before this: 1812 ms after the last foe went down the tally box
      // was on screen — and in between, nothing happened. The cheer fired on the
      // SAME line that appended the box, so the one victory pose this cast has was
      // played behind a dimmed, blurred panel that covered the party (Vesper's own
      // anchor was inside the box; see docs/qa/battle-ko/before-win-3-tally.png).
      // The order is now: THE FIELD ALONE while the last body settles and the
      // survivors' reactions play out, THEN the cheer, THEN — once it has been on
      // screen long enough to be a picture — the tally.
      // speed 0 (every suite, every automated caller) still gets all of it at once.
      if (win && stage) {
        await wait(beat('winHold'));
        try { stage.cheer(); } catch (e) { }
        await wait(beat('winCheer'));
      }
      root.appendChild(box);

      // --- the animation ---------------------------------------------------
      const goldRow = box.querySelector('.ogold'), xpRow = box.querySelector('.oxp');
      const trows = [...box.querySelectorAll('.ebb-trow')];
      let skipped = false;
      const finish = () => {                       // ENTER SKIPS TO FINAL VALUES
        skipped = true; S.tallyDone = true;
        if (goldRow) goldRow.textContent = String(result.gold);
        if (xpRow) xpRow.textContent = String(result.xp);
        trows.forEach((el, i) => {
          const p = plan[i]; if (!p) return;
          const last = p.legs[p.legs.length - 1];
          el.querySelector('.xb > i').style.width = (100 * last.to / Math.max(1, last.need)).toFixed(1) + '%';
          el.querySelector('.lv b').textContent = String(p.newLevel);
          el.classList.toggle('levelled', p.ups > 0);
        });
      };
      S.tallySkip = finish;

      const run = (async () => {
        if (!win || S.speed === 0) { finish(); return; }
        const T = Battle.tally;
        // the two spoils count up together — the quick beat that starts the
        // tally moving, before the per-character bars take over
        if (goldRow || xpRow) {
          const g0 = performance.now(), dur = T.goldMs * S.speed;
          while (!skipped) {
            const u = clamp01((performance.now() - g0) / dur);
            const e = 1 - Math.pow(1 - u, 3);      // the kit's decelerating tail
            if (goldRow) goldRow.textContent = String(Math.round(result.gold * e));
            if (xpRow) xpRow.textContent = String(Math.round(result.xp * e));
            if (u >= 1) break;
            await wait(30);
          }
        }
        // then each member's bar, in party order
        for (let i = 0; i < trows.length && !skipped; i++) {
          const el = trows[i], p = plan[i];
          const fill = el.querySelector('.xb > i'), lvb = el.querySelector('.lv b');
          for (const leg of p.legs) {
            if (skipped) break;
            const span = leg.to - leg.from;
            const dur = Math.max(T.legMinMs, T.perXpMs * span) * S.speed;
            const t0 = performance.now();
            while (!skipped) {
              const u = clamp01((performance.now() - t0) / dur);
              const v = leg.from + span * u;
              fill.style.width = (100 * v / Math.max(1, leg.need)).toFixed(1) + '%';
              if (u >= 1) break;
              await wait(20);
            }
            if (leg.up && !skipped) {
              // THE MOMENT: the bar tops out, flashes, resets to empty, the level
              // number ticks over. This is what the curve retune bought.
              el.classList.add('flash');
              await wait(T.upFlashMs * S.speed);
              el.classList.remove('flash');
              lvb.textContent = String(leg.lv + 1);
              el.classList.add('levelled');
              fill.style.transition = 'none';
              fill.style.width = '0%';
              await wait(40);
              fill.style.transition = '';
            }
          }
        }
        if (!skipped) finish();
      })();

      if (cfg.autoConfirm) return run.then(() => wait(700 * S.speed));
      return new Promise((resolve) => {
        S.outro = resolve;
        // never strand a player on a summary screen if a key event is eaten
        setTimeout(() => { if (S.outro === resolve) { S.outro = null; resolve(); } }, 60000);
      });
    }

    return {
      el: root, play, promptAction, onKey, outro, syncHp,
      stage: stage,
      show() { root.classList.add('on'); },
      // The arena's renderer, its rAF, its geometry and its textures all die
      // here. A battle must not be able to leave a WebGL context behind in the
      // overworld — that is the price of owning a renderer and it is paid here.
      destroy() {
        if (stage) { try { stage.destroy(); } catch (e) { console.warn('[Battle] stage teardown', e); } stage = null; }
        if (root.parentNode) root.parentNode.removeChild(root);
      },
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
    // THE STAGE SWITCH. null/true = use the 3D arena when this page can; false =
    // force the DOM stage. It is the coarsest tier of the fallback chain and the
    // one a QA pass kills first (Battle.stage3d = false; Battle.demo('forest')).
    stage3d: true,
    // ---- PACING (milliseconds, multiplied by opts.speed) --------------------
    // The cadence a HUMAN reads a turn at. User ruling 2026-07-31: the old debug
    // numbers made enemy actions "too fast to understand what's happening". These
    // are tuned by feel against real fights, and they are live-editable from the
    // console (Battle.pacing.announce = 700) so the next tuning pass costs a
    // reload rather than an edit. speed:0 zeroes all of them, so every automated
    // caller and every suite keeps the instant path it had.
    pacing: {
      // THE APPROACH IS PAID FOR OUT OF THE ANNOUNCE, and that is deliberate
      // (2026-08-08, the contact pass). The attacker now WALKS to its target
      // instead of leaning 1.35 m toward it, and travelling five metres takes
      // time the turn did not have. announce 560 -> 300 and a new approach beat
      // of 260 leaves announce + approach + wind at 860 ms, exactly what
      // announce + wind was, so the turn's wall clock does not move — measured
      // at 1965 ms/turn before and after by tools/battle_contact.mjs --only=clock.
      // The message is still on screen for the whole approach; what shrank is the
      // dead beat between reading it and anything happening.
      announce: 300,   // "Duskpad A attacks!" — read BEFORE anything moves
      approach: 260,   // the attacker crosses the ground to its target
      wind: 300,       // the body steps in and the clip starts
      damage: 640,     // the number lands and is read
      heal: 620,
      ko: 820,         // a death gets its own moment
      flee: 850,
      settle: 320,     // the gap between one actor finishing and the next starting
      // ---- THE VICTORY BEAT (2026-08-08, BET I) ----
      // winHold covers the last KO's own staging: the blow, the stagger, the fall,
      // the hold and the dissolve run 2.2 s from contact and `ko` above has
      // already spent 820 ms of it, so the field is empty of the fight by the time
      // the party cheers. winCheer is how long the cheer is the ONLY thing on
      // screen before the tally arrives — the hop is 900 ms, so this shows its
      // first two thirds and the box lands while the party is still up.
      winHold: 900,
      winCheer: 620,
    },
    // ---- the victory tally (also * speed; speed:0 snaps to final values) ----
    tally: { goldMs: 700, perXpMs: 26, legMinMs: 420, upFlashMs: 620 },

    // ---- THE TURN QUEUE'S FEED (the swap seam) -----------------------------
    // The queue widget asks THIS for "who acts next", and knows nothing else. The
    // default answers from the kernel's rules.order(state) — the same function
    // commit-then-resolve ranks its collected actions by, so what the panel shows
    // IS what will happen, by construction rather than by two things agreeing.
    //
    // SWAPPING THE SCHEDULER SWAPS THIS, NOT THE WIDGET. An ATB policy would set
    // Battle.queueFeed to one that predicts from gauge fill instead of spd order;
    // it must return the same shape and the panel needs no edit. That is the whole
    // reason the queue takes its data through one narrow accessor.
    //   upcoming(state, ctx) -> [{ id, acted }]  in resolution order
    queueFeed: {
      name: 'spd-order',
      upcoming(state, ctx) {
        const R = window.Rules;
        if (!R || !R.order || !state) return [];
        const acted = (ctx && ctx.acted) || Object.create(null);
        const ids = R.order(state);                 // LIVING ONLY, resolution order
        const pending = [], done = [];
        for (const id of ids) (acted[id] ? done : pending).push({ id, acted: !!acted[id] });
        return pending.concat(done);                // gone-already sink to the tail
      },
    },
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
          // THE ARENA IS FETCHED DURING THE FADE. Both awaits are started
          // together so the 350 ms veil pays for the script; if it is slow or
          // missing, loadStage3d resolves null and the DOM stage takes the
          // screen. A headless run never reaches this line at all.
          await Promise.all([fade(1), loadStage3d()]);
          screen = makeScreen({
            state: state0, zone: spec.zone, backdrop: spec.backdrop || spec.zone,
            speed: speed, autoConfirm: !!opts.autoplay || speed === 0,
            familyOf: (mid) => (monstersMap[mid] && monstersMap[mid].family) || 'default',
            itemName: (id) => (itemsMap[id] && itemsMap[id].name) || id,
            // THE EQUIPPED WEAPON, BY CHARACTER (2026-08-08). The kernel's
            // partyMember() deliberately drops `equip` — it derives stats from it and
            // then has no further use for it — and the kernel is untouchable, so the
            // visual reads the slot from the SAME source the stats came from: GS's
            // own party records, with an explicitly-passed member's `equip` honoured
            // first so a harness can stage a weapon without a save.
            weaponOf: (charRef) => {
              try {
                const m = (members || []).find(x => x && (x.id === charRef || x.ref === charRef));
                if (m && m.equip && m.equip.weapon) return m.equip.weapon;
                if (!gs || !gs.ok) return null;
                const ch = gs.activeParty().find(x => x && x.id === charRef);
                return (ch && ch.equip && ch.equip.weapon) || null;
              } catch (e) { return null; }
            },
            // THE TALLY READS THE SAME CURVE GS IS ABOUT TO WALK. Not a copy of
            // k, not a re-derivation — the same function, so a bar that fills to
            // the top is a level GS will actually grant. And the same share
            // arithmetic grantXp uses, or the bar would animate a number the
            // player never receives.
            xpToNext: (lv) => (gs && gs.xpToNext ? gs.xpToNext(lv) : null),
            xpShare: (total) => {
              const n = Math.max(1, (gs && gs.ok ? gs.activeParty().length : 1));
              return Math.max(1, Math.floor(total / n));
            },
            // pre-battle levels and xp: GS has not been touched yet, because
            // applyBattleResult runs only after start()'s promise settles
            tallyParty: () => {
              if (!gs || !gs.ok) return [];
              try {
                return gs.activeParty().map(c => ({
                  id: c.id, name: (growth && growth.characters && growth.characters[c.id] &&
                                   growth.characters[c.id].name) || c.id,
                  level: c.level, xp: c.xp,
                }));
              } catch (e) { return []; }
            },
            // the party's own bust art, through ui_kit's one convention — the
            // status table shows the same faces the dialogue boxes do
            // THE FOE'S QUEUE THUMBNAIL, and it is the same art the DOM stage uses.
            // The lookup never changed and never needs to: convention, not a list.
            // WHAT CHANGED IS WHAT IS AT THE END OF IT (2026-08-08). These were 16 px
            // hand-drawn sprites whose colours contradicted the bodies — duskpad's
            // was salmon-pink over a grey wolf, scree shell's green over a red crab,
            // 105 degrees of mean-hue disagreement — so the panel that exists for the
            // player to PLAN with showed creatures in colours they do not have. They
            // are now rendered FROM the arena's own GLBs by tools/monster_icons.mjs,
            // which makes agreement structural instead of remembered. Measured with
            // tools/monster_regrade.py --icons: worst hue error 164 degrees -> 24.5.
            foeIcon: (mid) => monsterUrl(mid),
            bustFor: (charId) => {
              const k = EB();
              if (k && k.bustUrl) { try { return k.bustUrl(charId); } catch (e) { } }
              return 'assets/characters/' + String(charId) + '/bust.webp';
            },
          });
          screenRef = screen;
          // QA HANDLE: the live screen (and through it stage.snapshot()) while a
          // battle is up, so a harness can photograph the arena off the real page
          // instead of screenshotting a headless tab's stale canvas. Cleared with
          // screenRef on teardown; nothing in the game reads it.
          window.__EBB_SCREEN = screen;
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
        screenRef = null; window.__EBB_SCREEN = null;
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
        stage3d: {
          wanted: Battle.stage3d, module: !!window.BattleStage3D,
          available: !!(window.BattleStage3D && window.BattleStage3D.available()),
          live: !!(screenRef && screenRef.stage),
          tiers: screenRef && screenRef.stage ? screenRef.stage.tiers() : null,
          // RENDERED-FRAME COUNT. The one honest "is the arena actually running"
          // reading, and the only way a headless harness can tell a live intro
          // sweep from a stage that mounted and then stalled. A screenshot cannot
          // answer it: a background tab's canvas is stale.
          frames: screenRef && screenRef.stage ? screenRef.stage.frames : null,
          url: SELF_URL,
        },
        backdrops: Object.keys(backdrops), sprites: Object.keys(sprites),
        art: { base: art.base, enabled: art.enabled,
               backdropSample: backdropUrl('meadow'), monsterSample: monsterUrl('reed-nibbler') },
      };
    },
  };
  wire();
})();
