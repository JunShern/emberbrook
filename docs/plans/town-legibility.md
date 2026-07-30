# Dellhollow town legibility & route-channeling plan

**Update 2026-07-30 (later that morning): UNSTASHED — Step 0 assigned to the
legibility auditor agent. User expanded the mandate:** where the audit finds the
current 3D model is not amenable to the camera scenes we want, or pathways are too
confusing/cluttered, we are empowered to **re-architect parts of the town model**
— full ownership and creative freedom granted ("if there are tweaks that you need
to make to the town itself in order to achieve those goals, you should feel
empowered to do so"). Bucket 4 = model re-architecture, proposed by the auditor as
precise redlines, executed by the town custodian.

**Status: ACTIVE (was stashed)** — user-ratified direction (2026-07-30 morning), deliberately parked
while other work proceeds. Resurface as the next Dellhollow polish tranche.

## The feedback (user, morning after Night 2 playthrough)

Played the fully wired game end to end; happy overall, but in Dellhollow town:

1. **Navigation legibility is the main issue.** Camera angles are sensible, but it is
   hard to figure out where the character needs to walk. Walking flow feels janky.
   Every scene needs a clearly visible entry point and exit point that is
   **self-evident from how the scene looks**. Today that is not true of all scenes:
   transitions take the player by surprise, or the player can't find a transition
   where they expect one.
2. **Paths are janky and you can fall off them** into out-of-bounds areas below.
   This compounds the confusion — the player wants clearly defined routes.

## Diagnosis (agreed)

The overnight slope-slide bug (player slides off beside the gate stairs; camera
strands) was this same failure class — sgCorrect fixed the *consequence* (camera
stranding, 315 correction regions), not the *cause*: **the walkable floor is larger
than the intended route.** Town walk meshes were built for *coverage* (every platform
fully walkable, 367-box bit-identical gate), never for *channeling*.

The FF9 grammar we borrowed has a property we haven't replicated: the walkmesh IS the
route — you cannot fall off the path in Alexandria, and exits sit at screen edges in
the direction the path visibly flows. Night 2 delivered the camera half of that
grammar (del-cine) and skipped the floor half.

## Step 0 — diagnostic overlay + audit (do this first)

User's proposal, ratified. Almost entirely derivable from existing data:

- **Data:** add an authored `route` polyline per shot as a new field (refinement-first;
  fast-loop editable). Entry/exit points already exist as edge positions in
  `public/world/scenegraph.json`; shot cameras are numerically solved in
  `public/townmap/dellhollow.cameras.json` / `cine.json`, so route geometry can be
  projected pixel-exactly into each pre-rendered backdrop.
- **Runtime:** dev-mode toggle in `public/play3d.html` drawing entries (green), exits
  (orange), and the expected route polyline over the live scene. Off by default.
- **Audit:** screenshot all ~18 shots with the overlay on; grade each against
  *"would a player who has never seen this scene know where to walk?"* Deliver as a
  review-board page (like `docs/qa/review/`) so the user can see intent per shot.

## The three fix buckets (user-agreed, in impact order)

1. **Channeling at drop edges.** Every edge where the player can currently fall into
   out-of-bounds gets either a rail/parapet (visual + collision) or a walkmesh trim.
   Falling off should be *impossible*, not just recoverable-by-sgCorrect.
2. **Route affordance.** The intended path gets consistent ground language (boards /
   paving / lamps) that visually distinguishes "route" from "scenery floor" —
   especially where a transition point hides against busy geometry.
3. **Framing tweaks.** Shots whose exit is off-screen or ambiguous: exits should live
   at screen edges along the visible flow of the path.

## Constraints & taste decisions already settled

- **Walk-mesh gate collision:** bucket 1 is exactly the change the 367/367 zero-drift
  gate forbids. Plan: a deliberate, versioned **re-baseline** after the channeling
  pass lands; the gate then protects the new canonical floors.
- **Channeling extent:** channel hard at cliff/drop edges; keep interior plazas and
  courtyards generously walkable. No invisible walls — restriction comes from
  geography (rails, parapets, height), consistent with the overworld gating canon.
- sgCorrect stays as the safety net, but a healthy scene should almost never fire it —
  correction counts per shot are a useful post-fix metric (cine_test already tallies
  them separately).

## Suggested execution shape (when resurfaced)

1. Overlay + audit (Step 0) → review board page for user taste pass.
2. Per-shot fixes in bucket order; fast-loop iteration (route/rail data edits →
   rebake only affected backdrops via `tools/cine_bake.py --cams`).
3. Re-run `tools/cine_test.mjs` + `tools/slice_test.mjs`; watch correction counts drop.
4. Versioned walk-QA re-baseline once floors are final.
