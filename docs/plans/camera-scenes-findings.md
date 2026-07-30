# The cinematic town — Dellhollow through fixed cameras (2026-07-30, night 2)

**17 shots, 21 seams, 315/315 walk surfaces owned, 0 unreachable pockets.**

Dellhollow is now **played as a sequence of static pre-rendered shots**. You walk out
from the Valley Gate and the camera *cuts by itself* as you cross from one shot into
the next — a 350 ms fade, no prompt, no loading screen — which is the FF7/8/9 grammar
this project exists for. The real-time walkthrough is demoted to a developer view.

```
node tools/cine_solve.mjs           # solve framing   -> dellhollow.cameras.solved.json
node tools/scenegraph_derive.mjs    # emit cut edges  -> public/world/scenegraph.json
node tools/cine_test.mjs --plan     # 514+ assertions + the grand-tour plan
node tools/cine_map.mjs             # the region map  -> docs/qa/districts/cine_regions.svg
Blender -b tools/blends/dellhollow-master.blend -P tools/cine_bake.py -- --cams <ids>
/play.html                          # card: "DELLHOLLOW — the cinematic town"
```

## What was built

| Piece | File | Role |
|---|---|---|
| The shot list | `public/townmap/dellhollow.cameras.json` | AUTHORED: 17 shots, what each frames and what each OWNS |
| Shared brain | `tools/cine_regions.mjs` | ownership, framing solver, seam placement — one implementation, four consumers |
| Solver | `tools/cine_solve.mjs` | intent -> `dellhollow.cameras.solved.json` (the one numeric truth) |
| Bake | `tools/cine_bake.py` | one Blender session, N cameras: bg + depth per shot, ONE collision GLB |
| Cut edges | `tools/scenegraph_derive.mjs` (extended) | silent `kind:'cut'` edges where the walk network crosses a boundary |
| Runtime | `public/play3d.html` (additive) | cine mode, band triggers, camera gating, in-place cuts |
| Verifier | `tools/cine_test.mjs` | coverage, framing, chain, graph, hysteresis |
| Playthrough | `tools/cine_walk.js` + `public/world/cine_tour.json` | walks the whole town in a browser through real collision |
| Region map | `tools/cine_map.mjs` | plan + elevation, every walk surface coloured by its shot |

## The architecture, and the one deviation

The brief recommended **one depth-baked bundle per camera scene**. Deviation proposed,
red-teamed and approved: **one bundle (`del-cine`), all seventeen shots inside it.**

- A master-baked bundle carries the WHOLE town's collision (canon). At 48 MB, eighteen
  per-camera bundles would have committed **~860 MB of byte-identical GLB** for zero
  information.
- Worse, every camera cut would be a page load: re-parse 2108 primitives, rebuild the
  BVH. That is not a cut, it is a loading screen. The slice agent's `to === from`
  scene-internal handoff exists exactly for this and was already proven live.
- **The depth canon is untouched.** Each shot's `bg.png` and `depth.png` still come out
  of the same Cycles session, same transform, same camera, so the image and the
  occlusion still cannot disagree by construction. What changed is the directory
  layout and GLB sharing, not the bake.
- One Blender session bakes all eighteen instead of eighteen master loads.

Supervisor conditions, all honoured: (1) one source for camera numbers, asserted end to
end; (2) the depth quad is re-pointed in place, not rebuilt; (3) lazy art with
graph-adjacent prefetch; (4) cut hysteresis with a stated margin and an N-crossings
test.

### The chain (supervisor condition 1)

```
dellhollow.cameras.json     authored intent (yaw/pitch/fov/margin, or explicit pos/aim)
  -> cameras.solved.json    THE numeric truth: pos/aim/fov/clip, solved against geometry
     -> cine_bake.py        builds the BLENDER camera from it
        -> del-cine/cine.json   records what was baked (+ depth near/far)
           -> play3d.html    builds the THREE.PerspectiveCamera from the same numbers
```
`cine_solve.mjs --check` fails the build if link 1 drifts; `cine_test.mjs` asserts links
2–4 agree to 0.002u on every camera. **No camera number is typed twice in the project.**

## Coverage: the hard requirement, and how it is proven

Ownership is declared **by map record**, not by polygon: each shot owns a set of the
town map's landmarks and a set of its walk edges (optionally a *fraction* of an edge,
`from__to@0.45..1`, which is how a long boardwalk is split between two shots). Because
`townwalk`'s walk meshes are *named after the records that generated them*
(`walk_pad_<lm>`, `walk_lm_<lm>`, `walk_e_<a>__<b>_*`), every one of the town's **315
walk surfaces has exactly one owner by construction**, and the claim is checkable
rather than hopeful:

- 34 / 34 landmarks owned, 38 / 38 walk edges owned (edge splits tile [0,1] exactly).
- **315 / 315 walk meshes assigned, 0 orphans**, in BOTH bundles — and the cinematic
  bundle is asserted to carry the same walk network as the explore bundle, mesh for mesh.
- The xz region polygon per shot is *derived* from that ownership (hull of its walk
  meshes) and drawn in `docs/qa/districts/cine_regions.svg`.

Three map connections carry **no** walk ribbon — the cargo winch and the two
maintenance ladders — so no camera boundary is placed on them. Recorded in
`scenegraph.json.noRibbon` rather than silently dropped: if a ladder is ever made
climbable, its cut appears by itself.

## Framing: legibility is measured, not hoped

A shot is authored as **intent** (`yaw`, `pitch`, `fov`, `margin`) because a hand-typed
camera position cannot know whether the region it must cover fits in frame — the exact
mistake that buried the map's 13 draft cameras inside the cliffs. `cine_solve.mjs` fits
the standoff to the region's **character-height** samples and reports the character's
on-screen pixel height, so "can the player see themselves" is a number.

All 17 shots frame **100%** of their region's character-height samples. Character
height in a 768-line frame, near corner .. far corner:

| shot | standoff | char px | shot | standoff | char px |
|---|---|---|---|---|---|
| gate ★ | 29.9 m | 92..56 | weave | 30.4 m | 88..58 |
| shelf-west | 22.3 m | 136..63 | deep-stairs (transit) | 30.7 m | 78..60 |
| shelf-east | 15.8 m | 208..90 | boatyard (authored) | 24.3 m | 181..67 |
| loop-stairs (transit) | 20.3 m | 128..92 | waterfront | 25.0 m | 139..58 |
| quay-west | 29.5 m | 92..54 | fishdock | 26.6 m | 103..62 |
| quay-east | 18.0 m | 143..91 | cottage-steps (transit) | 24.9 m | 101..73 |
| lockhead | 19.1 m | 157..73 | lockfive | 26.8 m | 125..51 |
| cottage | 22.9 m | 111..75 | north-landing | 22.0 m | 162..62 |
| crossing (transit) | 25.2 m | 90..74 | | | |

`quay-east` carries a `minDist` floor of 18 m: the market's one stall pad *fits* from
10.8 m, and a camera 10.8 m from a market is standing inside it — and the quay-market
tier's stalls do not exist yet, so that frame has to hold geometry that was not there
when it was solved.

**The Boatyard reuses the accepted v10 hero camera verbatim** (explicit `pos`/`aim`);
the solver is forbidden from moving a frame a human accepted.

### Entrances and exits are framed, by construction

The brief's rule — *a player must never walk off-screen confused* — is enforced where
the standoff is chosen, not discovered afterwards by a test: **every arrival point that
lands in a shot is part of that shot's fit set** (every cut arrival, every shop door,
the town gate), at both foot and head height. `cine_test.mjs` then re-projects all of
them independently and asserts each is inside the frame.

## The cuts

A cut is **derived, never authored**: walk each map edge's ownership sequence (owner of
the `from` landmark, each t-segment, owner of the `to` landmark) and emit a reciprocal
pair wherever consecutive owners differ. "The camera changes at every region boundary"
is therefore a *theorem about the ownership table*, not a list somebody maintains.
**21 seams, 42 directed edges.** They are `auto` (fire on entry) and label-less
(**silent** — a camera change is not a choice; prompts stay for doors and portals).

**A cut triggers on a BAND, not a circle.** On the 11 m harbour deck a 1.7 m trigger
sphere is a thing you walk *around*, and a boundary you can side-step is a camera that
never changes. Each seam is an oriented rectangle whose half-width is **measured off
the walk surface** at derive time by stepping perpendicular until the ground runs out
(1.55 m to 9.25 m across the town). Extending `sgHit` to a second shape was the one
runtime change the slice agent predicted would be needed, in the one function it named.

**Camera gating is load-bearing.** A boundary and the boundary back are the *same
ground*, so an edge carries `camFrom` and exists only while that shot is up. Without it
the two halves of one seam fight over "nearest wins" forever. Doors and the gate portal
carry it too, so a shop's door is only offered in the shot that frames it — and coming
back out returns you to that same shot.

## Four findings worth keeping

**1. Backing off by ARC LENGTH is wrong on a switchback.** The first arrival derivation
moved `cutBackoff` = 2.4 m along the path from the seam. On the Valley Gate's S-bend
flight that is **0.73 m along the seam's own normal** — the arrival landed back inside
the band it had just come through, and a promptless auto edge that lands inside its own
reciprocal *strobes*. Cure: march along the path until the point is genuinely past the
band, measured on the crossing normal. And on a hairpin, where along-clearance is
geometrically unobtainable, **height is just as good a separator** — the band's own
`|dy|` gate (the thing that stops this town's tiers cross-triggering 5 m apart) does
the job. 4 of the 22 seams separate by height; 18 across the path; tightest clearance
over all 44 directed cuts is **0.54 m**.

**2. A seam belongs where the geometry can hold one.** Fixed offsets are not enough, so
the placer *slides* each seam along the window ownership allows and keeps the position
where both arrivals can be clear. This is what makes hairpin seams work at all.

**3. Two camera cuts inside half a metre — a design fault a metric caught.** The two
loop stairs off `shelf-homes` are 6.5 m and 8.3 m long on the ground while dropping
5 m. Given their own transit shot that owned the *flights but not their head*, both
endpoints of each flight belonged to other cameras, so each needed **two** seams inside
seven metres and the placer slid them to **0.4 m apart**. No FF field screen has ever
done that. Cure was ownership, not code: the transit shot owns the **junction**
(`shelf-homes`) as well as both flights, so each flight has exactly one seam, at its
foot, on flat ground. Two intermediate attempts (give each flight to the shot at its
foot; give both to `shelf-east`) each fixed the seams but pushed a neighbouring shot's
far-corner character below 50 px — the numbers chose the third.

**4. The accepted hero frame cuts its own near boardwalk.** `boatyard` is the v10 frame
a human approved, composed low along the slipway. A player arriving from the Waterfront
came in with their **feet below frame** (screen y −1.13, head fine at −0.74). The shot
does not move, so the *ownership* moved: `winch-foot__slipway` is split at 0.52 instead
of 0.30, putting the arrival 2 m further up the ways. Worth remembering as the general
shape — when a frame is fixed by taste, fit the region to the frame.

**5. "Does it FIT" and "can it SEE" are different questions, and only the second one
needs the town's 1900 objects.** The framing solver answers the first in milliseconds
and cannot answer the second at all — which is what buried the map's 13 draft cameras
in the cliffs. `tools/cine_visprobe.py` ray-casts the region's probe points in Blender
and sweeps yaw/pitch grids, so a buried shot is re-aimed in seconds instead of one
3½-minute Cycles frame at a time. It found **`gate-stair` at 4.2% visible** (the S-bend
flight is pinned between the rim and the Shelf, so a camera out over the gorge at street
height looks straight into the back of the inn), `shelf-west` at 37.5% and `waterfront`
at 36%. All three re-aimed to 88 / 94 / 80%. `shelf-west`'s swept best came back at
**yaw 140 — the map draft's own yaw**: the draft was right and my adjustment was wrong.

**The calibration that makes the number usable:** the human-**accepted** Boatyard v10
frame scores **~50%**, because probes sit on every walk mesh's corners and a scaffold
town occludes its own corners. So 50% is the bar, not 100%, and the shots between 52%
and 72% are left alone with their numbers reported rather than "fixed" toward a figure
that the accepted frame itself does not reach.

**6. A 1.4 m fence is transparent to a 1.7 m probe and opaque to a walking character.**
Head-height probing called the gate shot 77% visible while the runtime rendered the
character *fully hidden* at its own spawn. Probes and spawn-picking now test chest
height too, and require both.

### Two runtime occlusion bugs the browser found and no static test could

**A. The depth quad's projection was only synced inside `loop()`.** The quad converts
baked view-space depth to clip depth through the camera's `e10/e11/e14/e15`; with those
left at zero `gl_FragDepth` collapses to the near plane and **everything occludes
everything**. So every headless probe — which is where verification lives, and where
`requestAnimationFrame` is throttled to nothing — reported the character as hidden. It
read as "the character is behind the palisade" and it was really "loop() isn't running".
Measured: the gate shot went from **0/64** of its region visible to **56/64**. Cure:
`syncDepth()`, called from every render path. This is slice finding 7 one layer down —
not "screenshots are stale" but "the frame you rendered yourself is stale".

**B. The presence marker raycast the collidable set, not the depth-visible set.** Those
are deliberately different lists: `veg_`/`lm_`/`water_` meshes are kept *out* of
`collide` because foliage must never be a wall (geography-gating canon), but they are
render-visible and therefore in the baked depth map. Result: a rim tree's canopy
(`veg_gate_rimtreeE_2_2`) hid the character at the **Valley Gate — the town's own
arrival point, dead centre of frame — with no marker showing**, because the raycast
could not see the thing doing the hiding. Canon says a canopy hides the character and
never blocks them; that is only playable *if the marker knows*. Now verified: the
arrival is occluded by the canopy and the ring + diamond show, so the player is never
lost. **Flag for the gate-district owner:** that one rim tree stands over the arrival
point; pruning or nudging it would make the town's first frame read cleanly instead of
relying on the marker.

**7. A seam is a place, and places in a dense town are shared.** Two bugs, one cause,
both found by the *playthrough* and invisible to every static check:

*The rim-road mis-cut.* Walking the rim road from the Valley Gate to the cargo winch cut
to the stairwell shot. The seam at the head of the gate stair had measured its corridor
with a free perpendicular sweep over *any* walk surface, and the rim road runs alongside
— so the band came out 4 m wide and reached across a completely different path. First
cure: the corridor is this edge's OWN ribbon plus its two endpoint areas, so the sweep
stops when the ground under it belongs to somewhere else (4.00u → 1.90u there; the
harbour deck's genuinely wide frontiers stayed 4.35–5.75u). That was necessary and *not
sufficient*: at that junction the road passes 1.5 m across and only **1.1 m above** the
flight, so the two paths overlap in plan and no band there can avoid catching the road.
Second cure: a candidate seam is **rejected if any foreign walk surface lies inside its
band**, the placer slides until it is clean, and where a junction makes that impossible
it *narrows* the band. Width is the cheaper thing to give up — a narrow band only risks a
**missed** cut, which leaves you in the shot you were already in, while an overlapping
band guarantees a **wrong** one for everybody walking the neighbour.

*And the gate stair dissolved.* Requiring clean seams pushed the gate-stair seam to 0.5 m
from its sibling — the loop-stairs pathology exactly (finding 3): `valley-gate__inn` is a
7 m flight with **both** endpoints owned by other cameras, so it needs two seams inside
seven metres. It is now part of `shelf-west`: the flight comes down off the rim into the
top of the shop-street frame, one seam, and the arrival into the town's living street
reads in one shot. **The rule that emerged, twice: a short path whose two ends belong to
different cameras must be owned by one of THEM, or own a junction of its own.**

**Four seams still overlap a neighbour** and are shipped as named warnings: the harbour
deck (where four routes converge on one pad), the fish-dock boardwalk corner, and the
boatyard's shed cluster. See the refinement point below.

## THE DESIGNATED REFINEMENT POINT

**Camera cuts are edge-based; the four residual junction overlaps want a position-based
companion.** Today the shot changes only when you cross a seam, so at a junction where
routes converge a band can catch a player who is walking a *different* route, and
narrowing it trades that for the chance of missing a legitimate crossing. Both failure
modes have the same shape: the runtime knows *which seams exist* but not *which region it
is standing in*.

The cure is small and additive, and everything needed is already shipped: the ownership
regions and their derived hulls are in `cameras.solved.json`. Give the runtime a
`shotAt(x, y, z)` that resolves the owning shot from position, keep the cuts for the
*fade* (they are what makes a change feel authored rather than reactive), and use the
position resolution as a **correction** — if you are standing in a region the current
shot does not own and no cut is pending, cut. That makes every junction correct without
tuning a single band, and it removes the last place where a player can be somewhere the
frame does not show. It fits inside one function plus the data that already exists.

Two harness lessons, both already in the slice's list wearing new clothes: a
straight-line steerer between two points of one flight **cuts across the other seam of
the same flight**, and a waypoint-chaser that gets *teleported past its target* turns
round, walks back through the band and ping-pongs forever — a bug in the test that
looks exactly like a bug in the town. Both cured by driving the simulation along
**arc length**.

## Verification

`node tools/cine_test.mjs` — five independent groups, because each breaks alone:
**COVERAGE** (315/315 surfaces, 34/34 landmarks, 38/38 edges, both bundles agree),
**FRAMING** (18/18 shots at 100% in frame, legibility gate, plus an independent
re-projection of every region point), **CHAIN** (author = solved = baked = shipped
PNGs, per camera, to 0.002u; depth resolution, encoding, range and runtime clip
bracket), **GRAPH** (every shot reachable from the entry shot by cuts alone AND able to
get back — no one-way traps, no unreachable pockets; every seam and arrival on the walk
network; every arrival in frame; all six shop doors still wired, still prompting, still
returning to their own shot), **HYSTERESIS** (every arrival outside the band that sends
it back, and 5 round trips over every one of the 22 seams firing exactly 10 cuts through
a faithful model of the runtime's arm/disarm + teleport rules).

`tools/slice_walk.js`'s sibling `tools/cine_walk.js` walks
`public/world/cine_tour.json` — a 35-leg, 914-point route over the map's own walk
network that enters every shot — in a real browser through real collision, recording
every cut, and GL-reads the framebuffer to prove the character is still rasterised
after a depth-texture swap (screenshots of a background tab are stale; slice finding 7).

### Verification transcript — a real camera cut, in a real browser

`?scene=del-cine`, walked with `SIM` through the real collision and the real `sgTick`:

| Step | Result |
|---|---|
| load `del-cine` | shot **gate**, camera built from `cine.json` (pos `26.26,31.79,36.49` map = `26.26,36.49,-31.79` runtime), depth `20.98..58.25`, spawn on the walk network |
| edges out of the scene | 51, of which **2 are live** under `gate` — camera gating works |
| region visibility, measured through the SHIPPED depth map | **56 / 64** probe points visible (0/64 before the `syncDepth` fix) |
| walk east across the seam | at tick 12 the cut fires **by itself**; no banner shown |
| after the cut | shot **gate-stair**, depth range re-pointed **20.98..58.25 → 3.21..119.90**, character survives the depth test (**4734 px**), arrival on the walk network |
| walk back | tick 15, cut fires, shot **gate**, depth back to `20.98..58.25`, character **1269 px** |
| 4 crossings total | **exactly 4 cuts**, alternating, ending in the shot it started in — no oscillation |
| prompt during every cut | **never shown** — silent, as designed |
| interior regression (`del-inn-int`) | depth-map mode intact, spawns on its door pad, exit edge now carries `cam: shelf-west` |

The GL readback in two different shots after cuts is supervisor condition 2 discharged:
the depth-texture swap is the risk point, and a wrong near/far there makes the character
vanish exactly like the Boatyard phantom. It doesn't.

**One harness lesson worth keeping:** a cut is asynchronous — `transitionTo` fades to
black *first* and only then moves the player — so a synchronous walk loop runs to
completion having observed nothing while the teleport lands afterwards. That reads
exactly like "the cut never fired". Watch `SGbusy` (which flips synchronously) and wait
the transition out. And in a hidden tab Chrome throttles `setTimeout` hard, so the two
chained 350 ms fades can take tens of seconds: the harness sets `fadeMs` low for its own
run. Both are the slice's rAF lesson one layer down — *the frame you rendered yourself is
stale, and the timer you set may not have fired yet.*

## Open taste questions for the morning

1. **The two loosest shots.** `lockfive` (51 px) and `quay-west` (54 px) hold the most
   ground per frame. The far-corner figure is ~7% of frame height there — legible, but
   the smallest in the town. Splitting either costs a camera and a 3½-minute render;
   the numbers are in the table, the call is yours.
2. **`quay-east` is a close shot** (16 m, 165..99 px) because the market is small. It
   will read as a deliberate "stop and buy" framing or as a jarring push-in — worth a
   look once the market tier's stalls are actually built.
3. **`gate` was pulled off its draft yaw** (28° → 68°) purely for legibility: at 28° the
   rim road recedes along the view axis and the far figure fell to 47 px. The draft's
   note wanted "looking back upstream at the arch"; the shot now reads more broadside.
   Drama vs scale — the brief said scale, but this is the arrival shot.
4. **Transit vignettes: four of seventeen** (`loop-stairs`, `crossing`, `deep-stairs`,
   `cottage-steps`). The map blessed transit parcels for `del-crossing`; three more is a
   bigger commitment to "the scene IS the walk" than the map anticipated. A fifth
   (`gate-stair`) was built and then dissolved into `shelf-west` — see finding 7.
5. **A rim tree stands over the town's arrival point.** `veg_gate_rimtreeE_2_2`'s canopy
   covers the "Enter Dellhollow" spawn. The presence marker now correctly shows through
   it (that was bug B above), so it is playable — but the town's very first frame reading
   cleanly instead of relying on a marker is one pruned tree away. *Gate-district owner.*
6. **`townwalk` keeps the doors it no longer needs.** The scene graph now wires
   `del-cine`, so the real-time bundle has no edges at all — it walks as a pure geometry
   viewer. If you want prompts in the dev view too, the graph would need to emit both.
