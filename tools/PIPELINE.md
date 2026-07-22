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

### 2 · Walkability derivation (flood edit of the chosen scene)
**MAGENTA is the flood key for all new scenes (2026-07-21).** Green is legacy:
greens exist in the art (moss, hull paint, water), so its threshold had to be
strict and the bake compensated with a blanket dilate — the source of most
boundary slop. Magenta appears nowhere in the paintings, so the threshold can
be loose and the mask can trust the flood's own boundary. The baker
auto-detects the key per maskraw (whichever color hits more cells wins), so
legacy green scenes rebake bit-identically with zero config.
**Gate B (programmatic):** flood coverage 15–60% (interiors and gorge scenes
run lean); every exit mouth flooded; one connected component holds ≥90% of
flood area. Fail → retry ×2 with feedback; persistent fail → authored
corridor **segments** for the failing regions (the model reliably
under-floods roads — authored connectors are the accepted recipe, not a hack).
**Walkability-first alternative for NEW scenes:** `tools/walkfirst.mjs`
inverts the order — author the walkable layout map first, then have the model
paint the scene to match it (verdict 2026-07-21: adopt; deriving masks from
finished paintings remains the path for existing art).

### 3 · Mask bake (`tools/bakemask.py`, the production baker; `bake-core.js`
is its in-browser mirror and MUST stay behaviorally identical — reviewed live
via `workflow.html`, which shows every stage plus the params/slop box)
threshold (key auto-detected: magenta-loose or green-strict) → close (v2 r=2,
v1 r=3) → heal blocked specks (<8 cells) → **bay-filling** (close blocked
r=4: seals trap pockets < ~32px; real roads are wider and survive) →
authored corridor union → v1 only: dilate walkable 1 → despeck → v2 only:
**edge-snap** (expansion-only: boundary cells scan ≤3 cells outward and fill
up to a strong drawn edge — sobel ≥ p85 — recovering plank strips the loose
threshold missed; it can never disconnect anything) → authored blockedRects →
**clearance carve**: every gameplay POI must reach the plaza center through
cells with ≥20px of room (aligned with navGate's standard); failures get a
wide corridor carved.
**Corridor SEGMENTS replace rects (2026-07-21).** `bake.json` `segments`
(`{pts: [[x,y],…], w, label}`) stamp a polyline of width `w` — they follow
the painted stairs/gangways at any angle instead of smashing axis-aligned
boxes over them. Legacy `corridors` rects still work and still ship in old
scenes; new scenes author segments only.
**v2 has NO blanket dilate.** The dilate existed to open v1's pinch points;
under the loose magenta threshold it only smeared the mask over railings and
water. Pinches are now fixed where they are: a wider segment, or the carve.
**SLOP METRIC** (printed by `bakemask.py`, shown in `workflow.html`'s params
box): % of ALL grid cells that are walkable AND sit on a strong image edge
(per-cell mean sobel ≥ p85). It is grid-normalized on purpose — dividing by
walkable count instead would reward sloppy masks that cover big flat surfaces
(water, lock walls). A bake should never raise it against the shipped mask;
the scaffold-town rebake dropped it 6.1→4.6 (dellhollow), 7.5→5.4 (stairs),
4.2→3.7 (cottage).
**No walk-behind (decided 2026-07-19):** objects block WHOLESALE. Walk-behind
required splitting "tall part" from "base", and the flood can't express that
boundary reliably (e.g. the emberstone's ground platform read as
walkable-behind). Simple and predictable beats surprising-but-fragile; NPCs
that live behind counters (poppy) get a larger interaction radius instead.
**Gate C (navigation, `window.navGate(pois)` in the running game):** BFS with
clearance on the live mask between every pair of gameplay positions (NPC
approach spots, lamp bases, interaction marks, exit mouths), then the real
movement code drives each route waypoint-to-waypoint. Required: 0 failures,
0 orbit-assist warnings. Failure kinds tell you what to fix:
- `DISCONNECT` → add the point to the bake's POI carve list, rebake
- `PINCH` (with pinch location) → widen there: a wider segment `w` (v2), or a corridor rect / bigger dilation (legacy v1)
- `STALL` / orbit warnings → movement-code issue, not the mask
- `POI_TIGHT` → the standing spot itself needs clearance; move it or carve

### 4 · Props
Walk-behind occlusion is retired (see stage 3). If a scene ever needs a prop
the backdrop doesn't contain, add it as a keyed cutout drawn in the painter's
y-sort (`cutouts` in the scene def) — but never regenerate a prop that's
already painted into the backdrop: it can only double against its twin.
(The self-cutout machinery — cropping the backdrop through a baked alpha —
still exists in field.js/`cutSrc` if walk-behind ever returns.)

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
