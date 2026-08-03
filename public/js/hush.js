// hush.js — window.Hush: the moment Emberbrook loses its heart.
//
// THE BEAT. `ch1.hush` (public/game/story.json) is the chapter's hinge: the lamps
// are lit, the Kindling Hour comes, and the flame goes out of the town. It shipped
// as prose and a banner over a frame that looked exactly like the frame before it.
// This is the picture the words were promising.
//
// THE USER CHOSE "TAKE THE LIGHT" OVER A GRAYSCALE WASH, and the reason is canon,
// not taste: EMBERBROOK **IS** THE HEARTLIGHT TOWN (memory: world-canon-lights —
// Heartlights are rare globally and this is the one place that has them). Draining
// the colour out of the frame says "something is wrong with your television". Taking
// the warm sources out and leaving cold ambient says "the fire is gone", which is
// the thing that actually happened. So the town goes blue and flat, and:
//
//   THE CUT-INS STAY WARM AND FULLY COLOURED. That is the whole effect, and it is
//   the one line here that must never be "optimised". The people become the only
//   warmth left in the frame. A hush that also drains the portraits has said
//   "everything is cold" instead of "everything except them".
//
// It is free to keep that promise, because of where the grade is applied: the world
// is a WebGL canvas and a cut-in is a DOM <img> in dialogue.js's panel, painted by
// the browser OVER that canvas. Filtering the canvas element cannot reach it. If a
// later change ever moves the grade to a parent element, or into a post pass that
// composites the UI, this effect breaks and nothing will fail — so it is asserted
// instead: Hush.debug().cutinsWarm reports which element carries the filter.
//
// WHY A CANVAS GRADE AND NOT A SECOND LIGHT RIG. Because the town is a PRE-RENDERED
// PLATE. Emberbrook's lamps, its windows and its golden hour are pixels baked by
// tools/cine_bake.py; no runtime light can turn them off. The only two honest ways
// to take the light out of a plate are to re-bake it (a full Blender pass over
// every Emberbrook camera — hours, and a second art set to keep in sync forever) or
// to grade the frame. This grades the frame, and it drives the SHIPPED character
// rig (play3d.html charLight, via window.__hush) in the same breath so the bodies
// standing in the graded plate are lit by the same decision instead of being warm
// stickers under a blue filter. One decision, two consumers — see SIM.relight().
//
// WHAT IT CANNOT DO, stated plainly because a later session will notice it: a
// filter desaturates a baked lamp pool, it does not extinguish it. The bright warm
// pools under Emberbrook's lanterns survive as pale cold pools. Whether that reads
// as "the light has no warmth left in it" or as "the grade is broken" is a
// judgement for eyes, and the pair under docs/qa/hush/ is where those eyes go.
//
// SCOPE. Emberbrook only (/^emb-/) and only from the flag `story.ch1.hush`, which
// is set by exactly one beat. Dellhollow is not hushed; the overworld is not
// hushed. `?hush=1` and `?hush=0` force it either way for capture and for QA, and
// the URL always wins over the flag.
//
// window.Hush
//   Hush.set(on[, ms])   raise or drop the hush (ms = the fade, default 2200)
//   Hush.on() / .off()
//   Hush.active()        is it up right now
//   Hush.debug()         the live state, the grade string, and which element wears it
(function () {
  'use strict';

  var FLAG = 'story.ch1.hush';
  var TOWN = /^emb-/;               // Emberbrook is the Heartlight town; nowhere else
  var FADE = 2200;                  // ms — a held breath, not a cut

  // THE GRADE, and every number in it was picked by looking (docs/qa/hush/).
  // Read left to right, which is the order the browser applies it:
  //   saturate(0.34)   take the town's own colour down to a residue — not to zero:
  //                    zero is the grayscale wash the user turned down.
  //   brightness(0.80) the warm sources were most of the light, so the frame loses
  //                    some. It also pulls the baked lamp pools down hardest, which
  //                    is the closest a grade gets to putting a lamp out.
  //   contrast(0.90)   FLAT. The fire is what made the picture have highlights.
  //   sepia/hue-rotate/saturate  a cold cast, at partial strength: sepia lays a
  //                    monochrome tone over the residue, hue-rotate swings it to
  //                    blue and the trailing saturate decides how far the cast goes.
  var G = { sat: 0.34, bri: 0.80, con: 0.90, sep: 0.42, hue: 196, sat2: 1.55 };

  // THE BRIGHTNESS CUT IS PLATE-ADAPTIVE, and this is a measured fix rather than a
  // flourish. `brightness(0.80)` is right where there is light to take: Festival
  // Square and Home Row are full of lamp pools and losing a fifth of them is what
  // sells the hush. `gatefield` is not — the Old Gate plate is outside the village
  // with no lamp in frame, and charLight measured its 70th-percentile plate
  // luminance at 0.115 against the square's 0.21 (window.__charlight.plate.p70, the
  // number the character rig already uses to set its own level). Taking a further
  // fifth off THAT plate did not read as a hush; it read as a dark frame, and this
  // repo has the rule for it already: visible is not readable. So the cut scales
  // with what the plate actually has, floored, and a dark plate keeps its floor.
  var P70_REF = 0.21;               // the square's measured level = the full cut
  function plateP70() {
    try { var c = window.__charlight; return (c && c.plate && c.plate.p70) || null; } catch (e) { return null; }
  }
  function grade(g) {
    g = g || G;
    var p = plateP70();
    var k = p == null ? 1 : Math.max(0.35, Math.min(1, p / P70_REF));
    var bri = 1 - (1 - g.bri) * k;
    return 'saturate(' + g.sat + ') brightness(' + bri.toFixed(3) + ') contrast(' + g.con + ') ' +
           'sepia(' + g.sep + ') hue-rotate(' + g.hue + 'deg) saturate(' + g.sat2 + ')';
  }

  // THE CHARACTER RIG under the hush, read by play3d.html's charLight(). These are
  // MULTIPLIERS on whatever the plate-derived gain decided, not replacements for it:
  // a hushed Vesper must still sit at the right exposure for her plate, and only
  // lose the warmth. The key colour is the moon's, because on a hushed night the
  // moon is what is left.
  var RIG = { key: [0.55, 0.65, 0.88], sky: [0.44, 0.55, 0.82], grd: [0.20, 0.24, 0.34],
              keyMul: 0.55, fillMul: 0.85, ambMul: 1.10 };

  var HAS_DOM = typeof document !== 'undefined' && !!document.createElement;
  var state = false, faded = null;

  function q(k) { try { return new URLSearchParams(location.search).get(k); } catch (e) { return null; } }
  var FORCE = (function () { var v = q('hush'); return v === '1' ? true : (v === '0' ? false : null); })();
  function scene() {
    try { if (window.SIM && SIM.scene) return SIM.scene() || ''; } catch (e) { }
    return q('scene') || '';
  }
  function flagOn() {
    try { return !!(window.GS && GS.state && GS.state.flags && GS.state.flags[FLAG]); } catch (e) { return false; }
  }
  // The renderer's own canvas and nothing above it — see the header. #s is the
  // world host; the dialogue window and its cut-ins are siblings/children painted
  // over it, and they must not be inside whatever wears this filter.
  function canvas() {
    if (!HAS_DOM) return null;
    var host = document.getElementById('s');
    return (host && host.querySelector('canvas')) || document.querySelector('#s canvas') || null;
  }

  function apply(on, ms) {
    var c = canvas();
    if (c) {
      // ms === 0 MUST CLEAR THE TRANSITION, not merely decline to set one. A
      // previous call leaves `transition: filter 2200ms` on the element, so an
      // "instant" apply after it is still a 2.2 s fade — and CSS interpolates the
      // whole filter list, so a frame captured part-way through carries a
      // PARTIAL hue-rotate. MEASURED 2026-08-03: a QA plate taken 700 ms after
      // Hush.on(0) came out olive-green (hue-rotate at ~60deg of its 196), which
      // looked exactly like a wrong grade and was a wrong clock.
      c.style.transition = ms === 0 ? 'none' : 'filter ' + (ms == null ? FADE : ms) + 'ms ease-in-out';
      c.style.filter = on ? grade() : 'none';
    }
    window.__hush = on ? { on: true, key: RIG.key, sky: RIG.sky, grd: RIG.grd,
                           keyMul: RIG.keyMul, fillMul: RIG.fillMul, ambMul: RIG.ambMul }
                       : { on: false };
    // The rig is re-solved for the shot that is up; play3d owns CINECAM, we do not.
    try { if (window.SIM && SIM.relight) SIM.relight(); } catch (e) { }
    faded = c;
    return !!c;
  }

  function set(on, ms) {
    on = !!on;
    if (on === state && faded === canvas()) return state;
    state = on;
    apply(on, ms);
    return state;
  }

  // WHAT THE WORLD SAYS IT SHOULD BE. The URL wins (capture and QA), then the flag,
  // and the scene gates both: walking out of Emberbrook lifts the hush from the
  // frame without touching the flag, because Dellhollow is not the town that lost
  // its heart.
  function want() {
    if (!TOWN.test(scene())) return false;
    if (FORCE !== null) return FORCE;
    return flagOn();
  }
  function sync(ms) { return set(want(), ms); }

  if (typeof window !== 'undefined' && window.addEventListener) {
    // A scene swap rebuilds the canvas' contents but not the element; re-applying is
    // cheap and it is what makes an arrival in a hushed town arrive hushed, with no
    // fade — you did not just watch the light go out, it was already out.
    window.addEventListener('eb-scene', function () { try { sync(0); } catch (e) { } });
  }

  window.Hush = {
    set: set, on: function (ms) { return set(true, ms); }, off: function (ms) { return set(false, ms); },
    active: function () { return state; }, sync: sync,
    grade: grade,
    debug: function () {
      var c = canvas();
      return { on: state, want: want(), scene: scene(), flag: flagOn(), force: FORCE,
               grade: c ? c.style.filter : null,
               // The promise, asserted: the filter is on the WebGL canvas, so the
               // DOM cut-ins above it are untouched and stay fully coloured.
               cutinsWarm: !!c && c.tagName === 'CANVAS',
               rig: window.__hush || null };
    },
  };

  // Self-arming and flag-driven, like every other module here. GS emits 'change' on
  // every setFlags, which is how the beat that sets the flag reaches the frame with
  // nothing reloaded — the hush has to fall while the player is standing there.
  // A CAMERA CUT CHANGES THE PLATE, AND THE GRADE IS A FUNCTION OF THE PLATE. There
  // is no per-cut event to listen to (cineApply is play3d-internal), and hanging a
  // callback off charLight would recurse — charLight is what apply() calls. Polling
  // the shot id is the cheap, non-recursive answer: one string compare every 400 ms,
  // and it only touches the canvas' filter (no relight — charLight has already run
  // for the new cut and window.__hush has not changed).
  var lastShot = null;
  function regrade() {
    var s = null; try { s = (window.SIM && SIM.cine && (SIM.cine() || {}).shot) || null; } catch (e) { }
    if (s === lastShot) return;
    lastShot = s;
    if (!state) return;
    var c = canvas(); if (!c) return;
    c.style.transition = 'none'; c.style.filter = grade();
  }
  if (HAS_DOM) setInterval(function () { try { regrade(); } catch (e) { } }, 400);

  function arm() { try { sync(FORCE !== null ? 0 : undefined); } catch (e) { } }
  if (window.GS && window.GS.ready && window.GS.ready.then) window.GS.ready.then(arm);
  else if (HAS_DOM) setTimeout(arm, 0);
  try { if (window.GS && window.GS.on) window.GS.on('change', function () { try { sync(); } catch (e) { } }); } catch (e) { }
  if (HAS_DOM) setTimeout(arm, 1200);      // the canvas may land after we do
})();
