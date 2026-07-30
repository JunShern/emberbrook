# The cinematic town — Dellhollow through fixed cameras (2026-07-30, night 2)

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
| The shot list | `public/townmap/dellhollow.cameras.json` | AUTHORED: 18 shots, what each frames and what each OWNS |
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
red-teamed and approved: **one bundle (`del-cine`), eighteen shots inside it.**

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

All 18 shots frame **100%** of their region's character-height samples. Character
height in a 768-line frame, near corner .. far corner:

| shot | standoff | char px | shot | standoff | char px |
|---|---|---|---|---|---|
| gate ★ | 29.9 m | 92..56 | crossing (transit) | 25.2 m | 90..74 |
| gate-stair (transit) | 15.2 m | 153..122 | weave | 30.4 m | 88..58 |
| shelf-west | 20.4 m | 172..69 | deep-stairs (transit) | 30.7 m | 78..60 |
| shelf-east | 15.8 m | 208..90 | boatyard (authored) | 24.3 m | 181..67 |
| loop-stairs (transit) | 20.3 m | 128..92 | waterfront | 22.8 m | 157..66 |
| quay-west | 29.5 m | 92..54 | fishdock | 26.6 m | 103..62 |
| quay-east | 16.0 m | 165..99 | cottage-steps (transit) | 24.9 m | 101..73 |
| lockhead | 19.1 m | 157..73 | lockfive | 26.8 m | 125..51 |
| cottage | 22.9 m | 111..75 | north-landing | 22.0 m | 162..62 |

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
**22 seams, 44 directed edges.** They are `auto` (fire on entry) and label-less
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
4. **Transit vignettes: five of eighteen** (`gate-stair`, `loop-stairs`, `crossing`,
   `deep-stairs`, `cottage-steps`). The map blessed transit parcels for `del-crossing`;
   four more is a bigger commitment to "the scene IS the walk" than the map anticipated.
5. **`townwalk` keeps the doors it no longer needs.** The scene graph now wires
   `del-cine`, so the real-time bundle has no edges at all — it walks as a pure geometry
   viewer. If you want prompts in the dev view too, the graph would need to emit both.
