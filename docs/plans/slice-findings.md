# The vertical slice — scene graph + transitions (2026-07-30, night 2)

Emberbrook's scenes are now ONE CONTINUOUS GAME: the valley road runs into
Dellhollow's Valley Gate, the town's doors open into the six interiors, and every
one of them comes back out. This is the wiring layer only — no story, no state, no
party; walk up to a door and a prompt offers it to you.

```
node tools/scenegraph_derive.mjs        # public/world/scenegraph.json (NEVER hand-edited)
node tools/slice_test.mjs               # 154 assertions: graph + geometry + routes
tools/slice_walk.js                     # browser payload: walk it with real collision
/play.html                              # top card: "PLAY — the connected slice"
```

## What was built

| Piece | File | Role |
|---|---|---|
| Generator | `tools/scenegraph_derive.mjs` | projects the map files into a scene graph |
| Graph | `public/world/scenegraph.json` | 8 nodes, 14 edges, `_doc` + `defaults` + provenance |
| GLB reader | `tools/glb_read.mjs` | node world matrices, AABBs, down-ray over `walk_` tris, from Node |
| Runtime | `public/play3d.html` (additive block) | edge test, prompt, `transitionTo`, arrival spawn |
| Verifier | `tools/slice_test.mjs` | asserts graph, geometry and map-network routes |
| Walk harness | `tools/slice_walk.js` | drives the real walker through a scene via `SIM` |

## Coordinate frames — measured, not assumed

Both were verified against the shipped bundles before a single edge was written.

- **Town map** `pos [x, y, h] -> runtime (x, h, -y)`. Confirmed by comparing all 25
  `walk_pad_<id>` mesh centres in `townwalk/scene.glb` against the map: identical to
  **0.02u** (the pad's 0.12u ribbon top vs. the map's height). The map is the single
  source; the bundle is only ever asked "is the pad where you said?".
- **Region/world** `pos [x, y, h] -> runtime (x-140, h, 100-y)` (`valley_map.w2r`,
  origin at the massif tile's centre). Confirmed against `ow-valley/meta.json`'s own
  spawn: `w2r(98,127) == [-41.6, ., -26.7]`.

## The 14 edges

| From | To | Trigger (runtime) | r | Arrival | Prompt |
|---|---|---|---|---|---|
| ow-valley | townwalk | 70, 12.4, 50 | 3.2 | 13.58, 24.07, -5.16 | Enter Dellhollow |
| townwalk | ow-valley | 16.67, 24.04, -4 | 2.2 | 65.78, 12.65, 49.16 | Leave Dellhollow |
| townwalk | del-inn-int | 22, 19.04, -5.5 | 1.8 | -3.4, 0.04, -2.72 | Enter The Boatmen's Rest |
| townwalk | del-item-int | 30, 19.04, -9 | 1.8 | -2.5, 0.04, -2.28 | Enter Item Shop |
| townwalk | del-weapon-int | 37.8, 19.04, -5.5 | 1.8 | -2.5, 0.04, -2.28 | Enter Weapon Shop |
| townwalk | del-armor-int | 44.3, 19.04, -9 | 1.8 | -2.5, 0.04, -2.28 | Enter Armor Shop |
| townwalk | del-cookhouse-int | 40.4, 14.04, -11 | 1.8 | 3, 0.04, -2.58 | Enter Cookhouse |
| townwalk | del-cottage-int | 92.61, 7.87, -22 | 1.8 | 1.9, 0.03, -6.38 | Enter Keepers' Cottage |
| *(each interior)* | townwalk | its own `walk_pad_door` | 1.8 | the street outside its door | Leave *name* |

Emberbrook contributes nothing yet — correctly: it has a map but no walkable
bundle, and the generator says so in a warning instead of inventing an edge.

## UX decisions taken

1. **Non-modal HUD banner**, bottom-centre of the stage, `label? [E]` with the key
   in the hub's warm accent, 120ms opacity fade. Styled from the existing HUD's
   palette (`#e7ddd0` on `#000b`, `#3a2c20` border, monospace) so it reads as part
   of the same game. `pointer-events:none` — it is a label, never a button.
2. **Nearest in-range edge wins**, so two doors close together never fight, and a
   **vertical gate** (`|dy| <= vTol`, default 2.0) stops a quay door triggering
   through the shelf street 5u above it.
3. **Arrival suppression (arm/disarm).** An edge whose radius already contains you
   when you arrive starts *disarmed* and arms the moment you step out of it. This
   is load-bearing, not polish: interiors spawn ON their door pad, which IS the exit
   trigger, so without it every room would open with "Leave the Inn?" in your face.
   It also makes portal ping-pong impossible on the frame a transition lands.
4. **Arrivals are pushed clear** of the trigger that sends you back (radius +
   `spawnBackoff`), along the flattest street leaving that landmark. Leaving the inn
   puts you 2.9u down the shelf street, facing the town, with no prompt showing.
5. **Fade both ways** (350ms, `defaults.fadeMs`), and the target page opens black
   and fades in when its scene is ready, so a load is a fade, not a flash.
6. **Prompts work in fixed-camera interiors** — it is HUD, independent of camera
   mode. Verified in `del-inn-int`, which is a depth-map fixed-camera room.

## Architecture: what is data and what is code

- **Nothing about Dellhollow is in the runtime.** No scene key, landmark id, radius,
  label or timing. Adding a door, a portal, an interior or a whole town is a map
  edit plus `node tools/scenegraph_derive.mjs`.
- **Every tunable is in `defaults`** inside the generated file: fade time, prompt
  format, the three radii, the vertical tolerance, the arrival back-off. Retuning
  the feel of every transition in the game is one data edit.
- **Provenance is shipped**: each edge carries `of` (the map record) and `source`
  (the derivation in words), so any row traces back to the map line that made it.
- **Two map fields were requested and granted** rather than assumed (the rule of the
  night — if the choice is "assume a convention" or "ask for a data field", ask):
  `world.json regions[].sceneKey`, and `dellhollow.map.json walkSceneKey`. The
  second one matters more than it looks: district bundles carry the WHOLE town's
  collision, so `del-boatyard/scene.glb` contains all 25 `walk_pad_<id>` meshes and
  the first generator run resolved Dellhollow's walk scene to **the Boatyard**.
- **Arrival direction is order-independent**: among the walk edges touching a
  landmark, flat types first, then the flattest first sub-segment, then lexicographic
  — never "the first edge in the file", which would let a reordered map silently
  move every arrival point in the game.

## THE DESIGNATED REFINEMENT POINT

`transitionTo(edge)` is the only place a scene change happens. Tonight it is a
**state-free full page load** — robust, nothing leaks, correct by construction, and
it costs a bundle reload. The replacement (preload + in-place bundle swap, persistent
party state, no reload) fits **inside that one function**: edge selection, arming,
the prompt and the fade never need to know. Two known-untested edges around it:

- **Browser back/forward.** Each transition is a real navigation, so Back returns to
  the previous scene at its *old* spawn params. Untested, and it will change meaning
  entirely when the swap goes in-place (`history.pushState` would then be a choice,
  not a side effect).
- **A stalled load** leaves the veil up; there is an 8s safety that fades in anyway.

## For the camera-scene navigation agent — READ THIS

Your camera cuts are the same mechanism, already implemented and already proven.

- **An edge with `to === from` is a scene-internal handoff.** No page load, no
  reload of townwalk's 2108-primitive bundle: `transitionTo` fades, moves the player
  to `spawn`, calls `applyCam(edge.cam)`, fades in. Verified live tonight with a
  synthetic edge: the player moved gate pad -> shelf street inside one document, the
  follow-camera yaw took the edge's `spawnYaw`, and `applyCam` received the payload.
- **`cam` is a reserved slot** the runtime hands to `applyCam()` untouched. I did not
  invent its shape — that is yours (a named camera from the map's camera hints, or an
  explicit `{pos,target,fov}`). `applyCam` is currently a documented no-op that
  records to `window.__sgCam`; teaching the game camera cuts is that function plus
  data. Nothing in the runtime switches on `kind`, so add whatever kinds you need.
- **`spawnYaw` (radians) already works** for real-time follow cameras and is read
  from `?yaw=` on cross-scene loads too.
- **Add your edges in the generator**, not by hand — `scenegraph.json` is a build
  artifact and `slice_test.mjs --check` fails the build if it drifts from the maps.
  Camera edges will want a trigger volume more expressive than a circle eventually
  (a doorway line, a corridor band); `r` + `vTol` is what exists today and extending
  the *shape* is a runtime change in one function (`sgHit`).
- **`SIM.addEdge({...})`** injects an edge into a running scene. Prototype a camera
  cut live before you commit it to the pipeline.
- **Test in the physics tick, not the frame.** `sgTick()` hangs off `phys()`, so
  `SIM.move`/`SIM.tick` exercise the real prompt logic; rAF is throttled to nothing
  in a background tab, which is where headless verification lives.

## Verification transcript (real browser, real collision)

`node tools/slice_test.mjs` — **154/154 assertions**: graph freshness, bundles,
reciprocity, reachability from `ow-valley`, every trigger reachable and every arrival
standing on its scene's `walk_` surfaces, and a Dijkstra route through the town's own
walk network for each leg. Then the loop, walked in Chrome with `SIM`:

| Step | Result |
|---|---|
| spawn `ow-valley` | -41.62, 25.94, -26.70 (Emberbrook gate), on walk network |
| road, 14 legs to the Valley Gate | walkable, 161ms sim, 3 detours (see finding 1) |
| gate trigger | dist 1.34, dy 0.02 -> **"Enter Dellhollow? [E]"** visible |
| press E | fade to black, navigate with `sx/sy/sz/yaw/fade` |
| arrive `townwalk` | 13.58, 24.07, -5.16 — exactly the graph's arrival, on network, yaw 0.358, fade in |
| S-bend flight down to the shelf street | 19/19 legs, 0 detours, lands on the inn pad at h19.04 |
| inn door | dist 0.41 -> **"Enter The Boatmen's Rest? [E]"** |
| press E | arrive `del-inn-int` at -3.40, 0.04, -2.72 = its `walk_pad_door`, on network |
| exit edge on arrival | inRange **but disarmed**, no prompt (suppression works) |
| step into the room | edge arms at 2.78u |
| return to the door | **"Leave The Boatmen's Rest? [E]"** (banner rect 274x32 at bottom-centre) |
| press E | arrive `townwalk` at 24.84, 19.07, -6.07 — 2.9u clear of the door, no prompt |
| walk the shelf street east | prompts raise and clear in turn at the **Item Shop** (28.5,-8), **Weapon Shop** (36.3,-6.4), **Armor Shop** (42.9,-7.9) |
| descend to the quay | market-stalls flight 30/30 legs, lands h14.39 on network |
| quay deck -> deep-stairs head | 49/49 legs |
| deep stairs | 43/63 legs, then **blocked** (finding 2) |
| deep-stairs foot -> the Moorage | walked from the foot: 34/34 to the fish dock, on to **74.24, 1.25, -26.77 — 1.86u from the Moorage** |
| return: Valley Gate trigger | **"Leave Dellhollow? [E]"** |
| press E | arrive `ow-valley` at 65.78, 12.65, 49.16 on the road ridge, yaw -2.9442 facing the gate, 4.3u clear of the return trigger |
| scene-internal handoff (synthetic edge) | player moved inside one document, `spawnYaw` applied, `applyCam` got the payload, veil faded back |
| legacy scene (`square3d`) | 0 edges, no banner, no veil, walks as before, no console errors |

## Findings for other owners

1. **`emberbrook_5` (an Emberbrook impression house) blocks the region road** ~3u
   north-east of the ow-valley spawn: the straight road line is obstructed and the
   walker needs 3 detours to pass. A player will walk around it, but the road
   corridor should be clear of the town impression. *Valley pipeline owner.*
2. **The Deep Stairs' l2 hairpin is impassable**: following the map's own polyline
   (`deep-stairs-head -> deep-stairs-foot`, waypoint 3 -> 4) the walker is stopped at
   39.0, 4.78, -23.9 by `bar_e_deep-stairs-head__deep-stairs-foot_l2_railB` — the
   flight's own outer railing across the turn. Reproducible with detours disabled, so
   it is the geometry, not a harness artifact. Everything below the hairpin walks
   fine. *Dellhollow geometry owner.*
3. **Two flights leave `shelf-homes` and one blocks the other.** Walking the map
   polyline of `shelf-homes -> quay-deck` (stairs) is stopped at 54.17, 18.43, -9.87
   by `bar_e_shelf-homes__market-stalls_l0_railB` — the *sibling* flight's railing
   crossing it. `shelf-homes -> market-stalls` walks perfectly (30/30), so the shelf
   tier still has a descent, but these are the **only two** shelf->quay links in the
   map and one of them is fouled by the other. Note `market-stalls` belongs to the
   quay-market tier under construction, so its rail may move anyway.
   *Quay-market custodian / geometry owner.*
4. **The ow-valley `walk_road` ribbon ends 0.11u short of its own
   `dellhollow-valley-gate` portal point** (road max x = 209.89 vs. the portal's
   210). Harmless — the gate radius is 3.2 — and deliberately not "fixed" by nudging
   the portal: the map is truth and the ribbon is the derived thing. The generator
   takes the trigger's height from a walk surface 1.6u away and warns. *Valley owner.*
5. **A town's walk scene is not identifiable from its bundle** (fixed by
   `walkSceneKey`, above) — worth remembering as a pattern: district bundles carrying
   the whole town's collision makes several kinds of "which bundle is this?" question
   unanswerable from geometry.
6. **Harness lesson, for anyone writing walk tests**: steer along a DENSE polyline
   (0.4-0.8u). Coarse waypoints let a straight-line steerer cut the corner into the
   `bar_` railings of the town's flights — the first S-bend "failure" tonight was the
   test, not the game. A tight follower with detours *disabled* is the diagnostic
   tool: when it stops, `SIM.blocked()` names the mesh.
7. **Hidden-tab screenshots are stale** (as warned) — the first interior screenshot
   showed a frozen frame and no banner while the DOM said opacity 1 at (716,782).
   `getBoundingClientRect` + `SIM` probes are the ground truth for HUD work.
