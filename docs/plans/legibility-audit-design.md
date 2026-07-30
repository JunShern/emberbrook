# Legibility audit — design note (Step 0 of the town-legibility plan)

Author: legibility auditor · 2026-07-30 · reviewed-by-file by the coordinator.
Scope: make the *intended* route through every Dellhollow shot into DATA, draw it
over the live game, then grade all 17 shots against the user's question:

> "Would a player who has never seen this scene know, from the image alone, where
> the entries and exits are and what route to take?"

Deliverables: this note → `public/townmap/dellhollow.routes.json` →
`public/js/route_overlay.js` → the 17-shot audit → `docs/qa/review/legibility-audit.html`.

---

## 1. Position: route data is DERIVED, not drawn by hand

The plan said "add an authored `route` polyline per shot". After reading the data I
am pushing back on the *authored* half, and I want the coordinator to rule on it:

**Dellhollow already states its intended routes, in two places, and neither is the
walkmesh.**

1. `townmap/dellhollow.map.json` — 38 walk edges of typed classes
   (`road`/`deck`/`path`/`stairs`/`bridge`/`ladder`), each with waypoints. This IS the
   designed network; the 315 walk meshes were *generated from it* (`walk_e_<from>__<to>_*`)
   and are wider than it by construction. The plan's own diagnosis — "the walkable
   floor is larger than the intended route" — is exactly the statement that *the map
   edge is the route and the walk mesh is the coverage*.
2. `townmap/dellhollow.cameras.json` — every shot `owns` a set of those edges, with
   fractional ranges (`edge@0.45..1`) where a flight or boardwalk is split between two
   shots. So "which route belongs to this shot" is already a fact in the camera file.

Therefore: **route polylines are generated from map-edge ownership**, by
`tools/routes_derive.mjs`, reusing `tools/cine_regions.mjs` (`loadCine`, `edgePoint`,
`edgeT`, `project`, `shotRegions`) so there is no second implementation of ownership
or projection. Entry/exit points come from `public/world/scenegraph.json` — seam bands,
door circles and the portal, already generated and already numerically exact.

Consequences that make this the right call:

* **Zero drift.** A camera re-aim, an ownership re-split, a new waypoint or a new door
  re-derives correct routes. A hand-authored polyline silently rots — the exact disease
  this codebase keeps curing (image-vs-geometry, cameras.json→solved→cine.json).
* **Generalises for free** (the user's repeatable-yet-generalisable directive):
  Emberbrook and every future town ship the same two files, so they get route data
  with one command and no authoring pass.
* **It is still authorable.** Every generated field can be overridden per shot in an
  `overrides` block inside the routes file, which the generator preserves. Where the
  derived line is wrong — a route through a plaza that should hug the stalls, a spur
  that is not a real destination — I hand-fix *that* line and the rest stays derived.
  Refinement-first, as the plan asked, but with a floor of correctness under it.

`--check` mode (`node tools/routes_derive.mjs --check`) re-derives and diffs, so a stale
routes file fails like `cine_solve --check` and `scenegraph_derive --check` do.

## 2. Route-data schema (`public/townmap/<town>.routes.json`)

Design rules: **runtime coordinates only** (`[x, y-up, z]`, +x east +z south — the same
frame as scenegraph `at`/`spawn`, so a reader never converts); **keyed by shot id** with
`"*"` meaning "the whole scene, no shots" (that is how a real-time scene like `townwalk`
or a future Emberbrook gets routes with the identical schema and the identical overlay);
**every point carries its provenance** so a finding can be traced back to the map record
that caused it.

```jsonc
{
  "version": 1, "town": "dellhollow", "generated": "<iso>",
  "generator": "tools/routes_derive.mjs",
  "appliesTo": ["del-cine", "townwalk"],      // scene keys this file describes
  "coords": "runtime [x, y(up), z]",
  "defaults": { "lift": 0.18, "ribbonWidth": 0.55, "beaconH": 2.1,
                "entryColor": "2fff6a", "exitColor": "ff9a2e", "routeColor": "ffe08a" },
  "shots": {
    "<shotId|*>": {
      "name": "The Valley Gate",
      "intent": "<the shot's own prose from cameras.json — what it is FOR>",
      "entries": [{
        "id": "portal:dellhollow-valley-gate",     // stable id
        "kind": "portal" | "door" | "seam" | "spawn",
        "at":  [x, y, z],                          // where the player STANDS on arrival
        "via": "<scenegraph edge id>",             // the edge that produced it
        "from": "ow-valley" | "<shotId>",          // where the player came from
        "seam": { "n": [nx, nz], "t": 1.1, "w": 2.25 } | null,
        "screen": { "ndc": [sx, sy], "px": [x, y], "onScreen": true, "charPx": 63 }
      }],
      "exits": [{ /* same fields, plus: */
        "to": "shelf-west" | "ow-valley",
        "toKind": "shot" | "scene",
        "prompt": "E" | null,                      // null = silent auto cut
        "aim": [ax, az]                            // unit xz: the way the path LEAVES
      }],
      "routes": [{
        "id": "gate:valley-gate__inn",
        "role": "spine" | "spur" | "vignette",     // spine = the through-route
        "class": "road" | "deck" | "path" | "stairs" | "bridge",
        "from": "entry:<id>" | "node:<landmark>",  // endpoints, symbolic
        "to":   "exit:<id>"   | "node:<landmark>",
        "points": [[x, y, z], ...],                // dense enough to follow the ground
        "length": 27.4,
        "source": "map edge valley-gate__inn@0..1"
      }],
      "measure": { /* the objective half of the rubric — see §4 */ }
    }
  },
  "overrides": { "<shotId>": { /* hand edits the generator must preserve */ } }
}
```

Why these fields and not others:

* `entries`/`exits` are **separate lists even though a seam is both** (a seam is an exit
  of one shot and an entry of its neighbour). The player question is asked per shot, so
  the data has to answer it per shot.
* `aim` on an exit is the seam normal (or the door approach direction). It is what makes
  "exits should sit at screen edges *along the visible flow of the path*" checkable: the
  arrow the overlay draws is data, not decoration.
* `role` distinguishes the through-route from spurs. Four Dellhollow shots
  (`crossing`, `deep-stairs`, `cottage-steps`, plus `quay-east` in effect) own no
  landmarks at all — they are transit vignettes whose only job is "walk on"; grading
  them against "find the shop" would be wrong, so the rubric reads `role`.
* No colours or pixel sizes per point: presentation lives in `defaults`, so retuning the
  overlay is one edit.

## 3. Overlay (`public/js/route_overlay.js`)

Contract from the stub: `R` toggles; entries GREEN, exits ORANGE, route polylines just
above ground; silent no-op with no data; never touches game state.

* **Key `R`.** Checked against `play3d.html`: taken are `w/a/s/d`, arrows, space, `g`
  (debug), `2` (blank art), `[`/`]` (char height), `m` (menu), `z` (zones), `e`
  (scenegraph default interact key). `r` is free. `Shift+R` cycles
  *current shot → all shots → off* — seeing the neighbour shots' routes is how you tell
  "exit off-screen" from "exit into a shot that does not exist yet".
* **Lazy.** Nothing is fetched, built or added to the scene until `R` is first pressed.
  Cost when off is one keydown listener.
* **Resolution of the data file, generalised:** `?routes=<url>` override, else the town
  parsed out of `SG.nodes[SCENE].origin` (`townmap/<town>.map.json` — every node states
  its own provenance), else `townmap/<SCENE>.routes.json`. Then shot =
  `window.__cine.cam` if present, else `"*"`. So del-cine, townwalk and any future town
  all work with no code change.
* **Drawn as world-space three.js objects in `scene`**, exactly like the zones overlay
  (`buildZoneOverlay` is the precedent: added straight to `scene`, never pushed into
  `collide`/`walkRef`/`allMeshes`, so it can never become floor, wall or occluder). This
  is also why it renders correctly under the fixed cine cameras — there is nothing
  camera-specific about it.
* **Depth-honest.** Materials are `depthTest:true`, so the baked depth map hides a
  marker that the *backdrop* hides. That is the point: an entry the player cannot see is
  an entry the overlay must not show either. `depthWrite:false` + a `lift` of 0.18 above
  the ground keeps the ribbon off the floor without z-fighting (the zone overlay needed
  0.34 to clear the ribbons; 0.18 is enough here because routes are drawn *on* them).
* **Form, chosen for the audit's question:** routes are a **ribbon** (0.55 u triangle
  strip, warm) with a brighter centre line, not a 1-px `THREE.Line` — a hairline cannot
  answer "does this read as a route". The ribbon is deliberately a preview of bucket-2
  ground language. Entries/exits are a ground ring + a translucent beacon column
  (2.1 u = character height, so the marker doubles as a legibility ruler) + an arrow
  along `aim` for exits. Labels are three.js `Sprite`s with canvas textures, not DOM,
  so they survive `gl.readPixels` and canvas captures (DOM labels would vanish from
  exactly the ground-truth probe this project relies on).
* **`window.ROUTES` probe API** (the audit's instrument, and reusable by any future
  agent): `toggle/mode/data/shot`, and
  `ROUTES.probe()` → per entry/exit/route-sample **visibility measured by GL readback**:
  paint a marker magenta with the depth test ON, render, `readPixels` a window at its
  projected position, count pixels. Zero surviving pixels at an on-screen point means the
  backdrop's own baked depth hides it. This is the same instrument as `SIM.paint()`,
  generalised from the character to the route, and it is why "entry invisible" is a
  measurement in this audit and not an opinion.
  `ROUTES.dropEdges()` → for samples along the route, probe `SIM.floors` at ±1.2 u
  perpendicular; a sample with no floor within a step-down and a >2.5 u fall below is a
  **fall-off risk with exact coordinates**, which is precisely the bucket-1 redline the
  town custodian needs.

## 4. Audit method

Per shot, in one CDP session against `http://localhost:8899/play3d.html?scene=del-cine`:

1. `SIM.shot(<id>)` to take the shot (no walking — framing review, as the harness
   intends), then `ROUTES.toggle(1)`.
2. **Pace every multi-step operation across separate CDP calls** and `await` the fade —
   NIGHTLOG 09:15: a synchronous block starves the event loop and fade timers never run,
   which reads as "the cut never fired". Walks are paced; shot jumps are awaited.
3. **Verify the frame with `readPixels` before trusting any capture** — NIGHTLOG /
   slice finding 7: a hidden tab's canvas compositing is stale, so a screenshot can show
   the previous shot. `ROUTES.probe()` returns the shot id it measured *and* a non-zero
   pixel count, so every captured image is paired with proof of what was on the GPU.
4. Capture the canvas to `docs/qa/review/shots/<id>.png` (overlay on) — plus a clean
   plate for comparison where a verdict depends on the art alone.
5. Walk the spine with the SIM harness where the geometry is in question, to confirm the
   route is walkable and to catch fall-off.

**Grading rubric.** Measured signals first, then the human question. A shot is graded on
its *primary* route (`role:"spine"`); vignettes are graded on "walk on" only.

| signal | pass |
| --- | --- |
| `entry-visible` | every entry on-screen, unoccluded by baked depth, figure ≥50 px |
| `exit-visible` | every exit on-screen and unoccluded |
| `exit-flow` | exit sits in the outer 35% of frame **or** a visible route runs to it |
| `route-visible` | ≥85% of spine samples on-screen and unoccluded, no hidden gap >3 u |
| `route-distinct` | each exit is reached by exactly one visible route (no ambiguity) |
| `no-fall-off` | zero unrailed >2.5 u drops within 1.2 u of the spine |

* **GREEN** — all six pass, and the image alone answers the user's question.
* **AMBER** — one signal fails, or the answer needs a second look, but the primary route
  and its main exit are still discoverable.
* **RED** — the primary route or the main exit is **not** discoverable from the image, or
  a fall-off is likely while walking the spine.

**Defect vocabulary** (one or more per AMBER/RED, using the user's words):
`entry-invisible` · `exit-ambiguous` · `exit-offscreen` · `route-reads-as-scenery` ·
`clutter` · `fall-off-risk` · `camera-fights-route`.

**Fix buckets** (from the ratified plan; 4 added by this morning's expanded mandate):
1. channeling at drop edges (rail/parapet/walkmesh trim)
2. route affordance ground language (boards/paving/lamps)
3. framing tweak (exit to a screen edge along the flow)
4. **model re-architecture** — the shot's geometry resists the camera grammar, or the
   paths are too confusing/cluttered to fix with 1–3. Proposed here as precise redlines
   (exact coords/params) in coordinator-owned files; executed by the town custodian.

## 5. Ownership and constraints

* **Mine:** `public/townmap/dellhollow.routes.json`, `public/js/route_overlay.js`,
  this note, `docs/qa/review/legibility-audit.html` (+ its images),
  `tools/routes_derive.mjs`.
* **One deviation to flag:** the brief allowed "a small `tools/routes_check.mjs`
  validator". I am shipping `tools/routes_derive.mjs` instead — one file that both
  generates and (with `--check`) validates, because per §1 the data is derived and a
  checker without a generator would be a second truth. Say the word and I will rename it.
* **Not touched:** `public/play3d.html`, `public/townmap/dellhollow.cameras.json`,
  `public/world/*`, any map file, any `.blend`. All findings against those land as
  redlines in the review page and my final report.
* **Gates:** `node tools/cine_test.mjs` (667/0) and `node tools/slice_test.mjs` (532/0)
  green before the final commit. Nothing in this tranche touches walk geometry, so the
  367-box zero-drift gate is unaffected — bucket 1 is the pass that will need the
  deliberate re-baseline the plan already reserved.
