# Scene art pipeline — quality-gated workflow

Principle: **never hand-tune low-level details into passing**. Each stage has an
automated gate; a stage that fails its gate gets retried (with the violated
constraint fed back into the prompt) or regenerated. Human review happens only
on candidates that already passed their gates, via a localhost gallery page.

Second principle: **collision is simpler and smaller than the art**. Interior
obstacles become axis-aligned footprint rectangles; concave bays get sealed.
Pixel-faithful collision reads as jank, not fidelity.

## Stages and gates

### 1 · Scene generation (`tools/genart.mjs`, style ref `jrpg-3.png`)
Generate 2–3 candidates per scene with composition constraints (exit mouths,
required landmarks, no text/watermarks) enumerated in the prompt.
**Gate A (art-director check, by Claude viewing the gallery page):** style
matches anchor, all exits declared in the scene graph are visibly open, no
text/signature artifacts, landmark props present. Fail → re-roll with the
violated constraint quoted verbatim in the prompt. Only passers go to the user.

### 2 · Walkability derivation (green-flood edit of the chosen scene)
**Gate B (programmatic):** green coverage 25–60%; every exit mouth green;
one connected component holds ≥90% of green area. Fail → retry ×2 with
feedback; persistent fail → authored corridor rects for the failing regions
(the model reliably under-floods roads — corridors are the accepted recipe,
not a hack).

### 3 · Mask bake (`bake-square.html` recipe — copy per scene)
threshold → close(3) → island healing (interior blobs = props: heal, then
re-block as inset bottom-band **rectangles**, emit auto-anchors) → border
shave (dilate walkable 1) → **bay-filling** (close blocked r=4: seals trap
pockets < ~32px; real roads are wider and survive) → authored corridor union
→ dilate walkable 1 → speck removal (<8 cells) → connectivity carve to POIs.
**Gate C (navigation, `window.navGate(pois)` in the running game):** BFS with
clearance on the live mask between every pair of gameplay positions (NPC
approach spots, lamp bases, interaction marks, exit mouths), then the real
movement code drives each route waypoint-to-waypoint. Required: 0 failures,
0 orbit-assist warnings. Failure kinds tell you what to fix:
- `DISCONNECT` → add the point to the bake's POI carve list, rebake
- `PINCH` (with pinch location) → widen there: corridor rect or bigger dilation
- `STALL` / orbit warnings → movement-code issue, not the mask
- `POI_TIGHT` → the standing spot itself needs clearance; move it or carve

### 4 · Prop isolation (magenta-key crops for walk-behind occluders)
Prompt: "isolate ONLY the X exactly as it appears … on flat magenta".
**Gate D:** keyed alpha coverage 5–70% of the crop, anchor sits inside a
baked footprint. Fail → re-roll that prop.

### 5 · Integration
Scene def gets: states, maskSrc, cutouts at auto-anchor positions, lamps,
exits matching the corridor mouths. Then Gate C runs again in-game (that is
the acceptance run) and a screenshot set goes on the gallery page.

## Hard-won rules
- **Dev server serves everything no-store.** A stale cached mask PNG once ate
  three full bake-test cycles: every "fix" was tested against the old file.
- Removal edits fail (the model keeps objects); additive dressing works.
- Whole-scene generation with constraints beats compositing props onto stages.
- The acceptance test must model a *player* (pathfind, then drive), not a
  greedy walker — greedy-walker failures conflate driver limits with mask
  defects and send you tuning the wrong layer.
