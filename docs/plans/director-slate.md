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

## Bet 3 — Vegetation's card-built asset family (OPEN — reversing my own deferral)
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

## Bet 6 — Legacy 2D runtime retirement (RUNNING — user-ordered 2026-08-05)
"This shouldn't still be around, please clean up any old content that is no longer
used in our latest game." Trap known and named: chapter1/2.js are the SCRIPT OF
RECORD for dialogue_style and exemplars.md — the gates' source of truth must move
or the files stay as data. Verify-then-delete, the three-way method.

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
