# Director's slate — structural bets (opened 2026-08-05)

The user's mandate, given 2026-08-05 before a week away: **stop tweaking, start
rebuilding.** Models, geometry and new assets are pre-authorized. Playtest failures
are symptoms of area design (camera, layout, circulation), not bugs to hot-fix.
This file is the slate: each bet names the structural defect, the evidence that
treatment-level fixes plateaued, and the shape of the real fix. Bets run without
per-item approval; the user reviews results, not proposals.

## Bet 1 — The valley's houses are blockout boxes wearing paint (RUNNING → next)
**Evidence:** three blind critics independently: "one asset repeated at least six
times", "the whole village reads as one undifferentiated putty-coloured mass",
"houses hard-cropped". Fourteen rounds moved their *colours* (r13/r14 measured
roofs/walls into reference bands) and no critic moved them off last place.
`impression_house()` is a gabled box; the real towns' house-variety doctrine
(docs/plans/house-variety-design.md) never reached the overworld.
**The fix:** a real house prop family for ow-valley — 3-4 distinct silhouettes
(gable, L-plan, hip, lean-to additions), chimneys placed by the massing not glued
on, doorsteps/awnings/yards. Build in the valley builder's own vocabulary; the
r14 chimney lesson (three rounds of collar patches) says massing first.

## Bet 2 — Dellhollow's vertical circulation is hostile by design (OPEN)
**Evidence:** rounds 12–21: loop-stairs, deep stairs (switchback pivot), keepers'
steps (44°, unfixable in place, retired), the roofed-landing census (16/17), the
apron pit, the moorage ribbon/stair conflict ("the stair foot and that lane want
the same two metres of air"). Six separate lanes fixed six separate flights; the
*generator* and the town's circulation plan are the defect. A playtester — and a
player — should never need six repaired staircases to cross one town.
**The fix:** a circulation redesign pass on dellhollow.map.json: fewer, shallower,
wider flights; ramps where the vocabulary allows (a canal town has ramps); one
legible primary route from gate to waterline that the wayfinder and the eye agree
on. Then regenerate. This is a map-and-generator rebuild, not another patch.

## Bet 3 — Vegetation's card-built asset family (SHIPPED 2026-08-06, residuals named — gallery Round 22, LOOP.md F5)
**Shipped:** 261/361 near-field clumps converted to hull-interior + leaf-card shell
(the f4b recipe; veg_land_bushcards); road-edge naturalization (metre rag + edge
dropped to terrain + 571-tuft/119-card fringe straddling the seam — the coordinator's
scope upgrade); and the canopy-corridor residual EXECUTED as a road bend (trimming
measured inert to r=20; station-90 veg 43.8%→7.0% at the shipped rig). Blind judge:
after wins 4/5 matched pairs; our before-gorge was misgrouped INTO the reference set.
**Residuals (open, at LOOP.md F5 "Carried"):** close-range card read is still
"flat shards"; translucency term wired but invisible to a blind judge — measure on a
backlit frame before sweeping; aerial road still a constant-width ribbon (rag needs a
coarser octave); gorge pair confounded, re-judge alone.
**Evidence:** the blind gap question: "the references build vegetation from thin
translucent cards; ours are opaque volumes — you cannot light your way out of a
closed convex hull." I deferred the conversion when the clump UV fix closed most
of the *material* gap. The user's mandate reverses that judgment: the silhouette
and transmission gap is structural and stays until the assets change.
**The fix:** a proper card-built bush/shrub family (leaf-cluster cards on hull,
translucency term, wind later), replacing veg_land_clumps' volumes in the near
field. The f4 A/B prototype is the seed; the t1 crown pattern is the method.

## Bet 4 — Near-field silhouettes generally (RUNNING — silhouette round)
Subdivision + displacement on clumps/rocks; find what selects the crag teeth.
User's words: "we need to fix the underlying shapes, not just the lighting."

## Bet 5 — The camera/sky composition question (OPEN, user-opened long ago)
**Evidence:** the r14 sky census (ours ~2-5%, references 15-25%); "nothing visible
justifies that light"; the r3→r4 viewpoint regression the user caught by eye. The
user explicitly opened pitch/height/horizon ("very open to changes at that level")
and round 15 was killed by the loop pause before it could spend that permission.
**The fix:** a composed camera pass on the standing ow views — pitch down-tilt
reduction, real horizon in frame, judged against the references' composition by a
blind judge. Distance stays fixed (the one hard constraint).

## Bet 6 — Legacy 2D runtime retirement (BANKED 2026-08-05 — DAYLOG entry has the census)
"This shouldn't still be around, please clean up any old content that is no longer
used in our latest game." Trap known and named: chapter1/2.js are the SCRIPT OF
RECORD for dialogue_style and exemplars.md — the gates' source of truth must move
or the files stay as data. Verify-then-delete, the three-way method.
**BANKED:** deleted in three verified commits (~650 MB / ~900 files): the 2D runtime +
phone relay, the painted scene bundles (two ratified style anchors spared), the iso
prototype + 24 tools. chapter1/2.js survive as INERT script-of-record data (option (a));
the dialogue_style corpus proven byte-identical, all gates green.

## PHASE CHANGE 2026-08-06 ~01:10 (user, verbatim steers)
The overworld overhaul RESTS once the in-flight lanes land (F6 road/grass, sky round
2, Bet 11 motion, camera clamp). **New focus: DELLHOLLOW.** "A mix of heavy
playtesting, as well as heavy critiquing and fixing the visual artifacts and
geometrical artifacts of the town." Bet 2 is RATIFIED and sharpened by ruling:
**"there's nothing to gain by adding more complex, interesting stairs that just
confuse and frustrate our players"** — the gate->shelf descent (currently TWO
confusing ways down) collapses to ONE simple, wide, legible route; the same
simplicity bar applies to every flight and narrow pinch in the town. Geometry
updates PRE-AUTHORIZED ("be prepared to update the underlying 3D model").
THE FAST LOOP (user asked for it; it exists, declared here as the law of the
phase): map/generator edit -> town_blockout (seconds, deterministic) ->
walk_engine_gate + _court_probe + reach_probe (engine truth, no bake) +
three_shots on the realtime tier (visual truth, no bake) + llm_playtester legs ->
iterate. cine_solve + plate bakes run ONCE, at the end, on ratified geometry.
Baking mid-iteration and trusting stale plates is the named anti-pattern.

## Standing method for every bet
Blind judges on anonymized images; the picture is the verdict; wire-before-sweep;
receipts by playtest run where playability is the claim; delete superseded work.

---

# Phase 2 slate — the A+ pillars (opened 2026-08-05, user AFK week)

The user's framing: "The game is currently still a C-. What would it take to get
to an A+? What does a real 2026 AAA reimagining of a Final Fantasy-style JRPG
look like?" The answer, as five absences (not deficiencies — things the game does
not do at all), each cheaper than the art bets and each transformative:

## Bet 7 — THE CAST ACTS (character presence)
Stand-in bodies translate between points; AAA characters perform. Idle life
(breath, weight shift, look-at the person talking), talk gestures, facing
discipline in dialogue, party followers reacting. The retarget pipeline and
posture ladder exist; what is missing is the ACTING layer on top.

## Bet 8 — THE WORLD SOUNDS (audio beyond music)
Footsteps by surface, doors, dialogue blips, UI ticks, ambience beds (river,
wind, birds, tavern murmur, lock machinery), battle SFX. CC0 sourcing per the
repo's own precedent (Quaternius/KayKit), provenance recorded; synthesis where
sourcing fails. Music ducking under dialogue.

## Bet 9 — BEATS ARE STAGED (cinematic grammar)
Every ch1/ch2 beat gets deliberate camera work from the shipped primitives:
establishing/medium/close per beat phase, cut-ins on emotional lines, blocking
(who stands where, who turns). story.json already carries cams; most beats
simply never set them. FF grammar, data-driven, no new engine.

## Bet 10 — COMBAT PERFORMS (battle juice)
Attack lunges/tweens, hit flash + shake, damage number motion, turn camera
punch-ins, KO/victory beats. battle_stage3d owns presentation; rules untouched.

## Bet 11 — THE WORLD MOVES (ambient life)
Chimney smoke, fireflies at dusk, drifting leaves, birds off rooftops, NPC
idle wander within posts, river sparkle motion. Cheap particles + the existing
NPC post system; the hush/dusk systems already prove the vocabulary.

## Sequencing (machine-real: max 3-4 lanes, Blender-heavy never 2-wide)
Wave A (now): leg 9 end-card receipt (standing) · silhouette round (bet 4) ·
legacy cleanup (bet 6) · AUDIO (bet 8 — file-disjoint from everything).
Wave B (as A closes): houses (bet 1) · staging pass (bet 9) · combat juice (bet 10).
Wave C: circulation redesign (bet 2) · card vegetation (bet 3) · world life (11) ·
camera/sky (bet 5). End-to-end receipt re-run after every wave; the gallery and
FIXLOG stay current; blind judges verdict every art bet.

---

## STEER UPDATE 2026-08-05 13:10 (user, before AFK): "I'm most interested in seeing
## graphics upgrades! So let's focus on that but broadly."

Re-sequenced, graphics-first. Wave A: silhouettes (bet 4, restart — inherits the
killed lane's valley_land.py work) · end-card receipt (leg 9 restart — the standing
mandate) · then HOUSES (bet 1) as soon as the valley builder frees. Wave B: card
vegetation (bet 3) · camera/sky (bet 5) · world life (bet 11, the visual half:
smoke/fireflies/leaves/river motion). Wave C: staging (bet 9, camera work IS
graphics-adjacent) · Dellhollow circulation (bet 2, enables its vistas) · audio +
combat juice (bets 8/10) deferred behind all visual bets. Legacy cleanup (bet 6)
continues when a lane slot frees — it is hygiene, not graphics.

## BET 1: BANKED (2026-08-05 16:25). Two blind rounds moved the village from "reads
## as unfinished" to "good-enough — the correct outcome; architecture that isn't the
## subject shouldn't win", ranked above one reference. Residuals (open, small): the
## pad/ground decal read (bed plinths into terrain), flat soffits, tower proportion.
## Next graphics bet: BET 5 (camera/sky) — the largest frame-level lever left, user-
## opened, never spent.

## BET 5: BANKED (2026-08-05 17:50, gallery Round 21, board docs/qa/ow-camera/).
## The bet's premise was STALE — r14's "2-5% sky" predated ORBIT.tilt; measured now
## 18-32% and blind critics called the band a liability. Shipped pick: OWPITCH
## 0.61->0.66 (a942e49), body position and visible-ground-area constraint both held,
## blind-ranked above the shipped frame. The lane's first pick was REFUSED by a blind
## critic and it accepted — the protocol holding on its own work. RESIDUAL PROMOTED TO
## THE SLATE, a WORLD item not a camera one: at boom 40 the camera rides INSIDE the
## canopy for road stations ~78-172 (station 90: 65% veg, visible ground a 4 m radius)
## — where the road was put, no rig recovers it. Candidate fix: thin/limb the canopy
## over the walked corridor in valley_land, or bend the road out from under it (map-
## level). Surfaced-not-shipped option for the user: 0.70/0.16 puts the body near the
## references' frame-Y at the cost of the horizon band (plates r27-opt-*).
##
## LEG 12 (same window): PT-044/045/046 closed or split; wayhint now routes on the
## authored polylines. NEW GAME bar blocked on PT-049 (moorage one-way trap) +
## PT-050 (weave seam off-frame, seam-canon violation) — the unblock lane is RUNNING
## and carries the full receipt. BET 6 lane RUNNING in parallel (restarted after the
## session-limit kill).

## BET 12 — THE SKY IS A REAL SKY (2026-08-06, PROTOTYPE COMPLETE behind ?sky2=1;
## awaiting main's one-line default flip in play3d.html: `Q.get('sky2')==='1'` -> `!== '0'`).
## User: "the sky is also clearly just a boring gray MS Paint picture" (r27-refused-gate).
## Found first: at the shipped rig the frame top is 10 deg below horizontal — the gameplay
## frame can never see the horizon/dome/ring-crests; the visible sky band is one ring's
## mid-body, so the sky was painted INTO the ring bodies (3-row mist->ridge profile,
## azimuth-aware golden-hour palette, mist banks) with a real shader dome (sun on
## OWSUN_DIR, warm horizon, static cumulus — motion is Bet 11) for the vistas. Blind loop
## round 1 refused the first build (wallpaper/paleness) and its list became round 2, which
## WON EVERY MATCHED PAIR ("the difference between paper and atmosphere"); the sun-facing
## vista ranked 3rd behind only the two FFIX references, twice. Lighting neutrality proven
## (unchanged-ground |d| <= 0.8/255, L to 3 decimals). Gallery Round 23; LOOP.md BET 12.
## RESIDUALS: the shipped-rig band is ring 0's body only — the next sky lever is the
## CAMERA (a rig that shows the horizon shows the whole system); band-vs-terrain
## hour-agreement (warm ground / cool veil) is a grade item; sun-disc height vs horizon
## colour tracks the ratified key's el 34 — moving it is a user call, not a lane's.
##
## BET 12 ROUND 3 (2026-08-06, SHIPPED on the branch): the user's "giant blue dot" was
## the dome far-plane-clipped from high vantages (dome/rings follow XZ-only at y=0, far
## was 400) with scene.background pouring through the hole — proof: background red ->
## dot red; fix: _rtCam far 400->560 sized off a measured worst case; standing gate
## tools/ow_probe/sky_sweep.mjs 216/216 in-engine poses, worst margin 83.4 m. Rings
## de-papered structurally (7-level continuous body, boundary wobble, spur streaks,
## 2nd silhouette octave, +-7% radial wobble, sub-horizon cloud fade, dome-colour hem)
## on the SAME ratified palette anchors. Two fresh blind rounds: final build's three
## frames rank 3/4/5 of 8 behind only the two FFIX refs, all matched pairs won, no arc
## found. Ground neutrality 0.47-0.81/255 vs 0.45 floor; 120 fps; ?sky2=0 exact.
## OPEN RESIDUALS: (1) far rings still "paper terraces / knife edges" (judge, both
## rounds) — next levers: inter-ring haze veil, crest-edge vertex-alpha fade (both
## touch the ratified band, not spent inside the round cap); (2) THE CANVAS RENDERS AT
## CSS RESOLUTION (no setPixelRatio) — the user's "pixelated seam" is 2x2 device-pixel
## blocks on every contrasty silhouette on retina; a fix is 4x fragment cost vs the
## 60fps budget — COORDINATOR DECISION WANTED; (3) sky_sweep's `peak` station is
## standable-but-reachability-unproven (the walkStep flood-fill probe crashes the tab).

## BET 11 — THE WORLD MOVES, visual half (2026-08-06, PROTOTYPE COMPLETE; awaiting
## main's ONE-LINE include in play3d.html: `<script src="js/ambient.js"></script>`
## after js/hush.js — play3d itself is untouched, the Bet 12 cloud drift ships as a
## runtime patch on __owsky). Shipped in public/js/ambient.js, all default-on behind
## the include, ?ambient=0 kills: chimney smoke (derived from *_chim bundle meshes —
## 26 lit stacks in Emberbrook), river/pond glints (area-weighted per water mesh,
## view-depth faded), fireflies at the Emberwake dusk (walk-surface anchored, GO OUT
## UNDER THE HUSH — measured), near-field leaves/pollen in ow (lens-relative wrap
## box), and slow two-rate cloud advection on the Bet 12 dome. One wind
## (window.__wind) drives smoke, motes and clouds; all motion is vertex-shader off a
## clock, frame cost below measurement noise, battle pause + eb-scene teardown
## proven. Blind loop: both town pairs won ("exactly the kind of ambient life a
## night town needs"; fireflies "the most convincing ambient effect in the whole
## pack"); the smoke closeup REFUSED round 1 (cotton-ball chain, mouth gap) and the
## fix is what shipped. Gallery Round 24 (b11-*, motion contact sheets).
## REMAINING IN THE BET: birds off rooftops, NPC idle wander (unstarted); ow/del
## smoke blocked on their builders naming chimney meshes (*_chim) or emitting
## anchors; foliage wind is ow_detail's to take up via window.__wind. Audio = Bet 8.
