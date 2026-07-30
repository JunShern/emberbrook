# Battle backdrop plates

Four plates, one per encounter zone, resolved by convention in the battle screen:
`assets/battle/<zoneKey>.png` (key = `encounters.json → battleBackdrop`), gradient
fallback when absent. Generated with `tools/genart.mjs` (Gemini
`gemini-2.5-flash-image`, the repo's own art pipeline — same as the character
busts), 1344x768 (16:9), style-referenced to our own renders.

## v2 — 2026-07-30, "painted for the arena" (battle-arena v3)

The v1 plates were full pre-rendered *scenes*: a low horizon and a fully painted
foreground running to the bottom edge. That is the right picture for a flat DOM
battle screen and the **wrong** one behind a 3D arena, where the painted
foreground has to stand up as a vertical wall of grass behind a real floor. Per
the user ruling ("a mix of a very simple 3D model overlaid on an arena
background — generated backdrop images made WITH AWARENESS of the 3D arena model
they sit behind"), all four were re-shot to a spec derived from the actual arena
camera.

**The spec, stated to the generator in metres and degrees:**

> The virtual camera is 3.9 metres above the ground, tilted 14 degrees downward,
> with a 34-degree vertical field of view. PLACE THE HORIZON LINE AT 42 PERCENT
> DOWN FROM THE TOP OF THE FRAME. The BOTTOM 30 PERCENT OF THE FRAME MUST BE
> COMPLETELY EMPTY: warm low ground haze over indistinct, out-of-focus ground,
> no objects, no props, no rocks, no plants, no detail, no foreground elements at
> all, nothing crossing the bottom edge — a 3D arena floor is composited over
> that band and its far edge must dissolve into the haze. Late-afternoon
> golden-hour light raking from the upper left; warm amber key light, cool
> violet-grey shadows, soft aerial perspective. Painterly pre-rendered CGI
> matching the reference render. No characters, no creatures, no people, no
> text, no watermark, no user interface.

Those numbers ARE `BattleStage3D.CFG.cam` (`{fov:34, dist:11.6, pitch:13}` puts
the eye 3.9 m up). **If the arena camera moves, this paragraph moves with it and
the plates are re-shot** — that is the whole contract between the two.

Per-zone subject lines, prepended to the spec above:

| plate | style ref | subject |
|---|---|---|
| `meadow.png` | `docs/qa/overworld/valley_record_midvalley.png` | "An open river-valley MEADOW seen across a wide green clearing. Above the horizon: warm evening sky and distant rolling golden hills. Just below the horizon: a band of green far meadow with wildflowers, a bright stream bending away to the right, and full green oaks and hedgerows standing at the left and right edges of frame only." |
| `forest.png` | `docs/qa/overworld/foliage_stand.png` | "An autumn WOODLAND clearing. Above the horizon: a high canopy of amber and gold leaves with shafts of low sun breaking through. Just below the horizon: a middle band of receding tree trunks and deep forest shadow at the left and right edges of frame, opening into an empty clearing at centre." |
| `crag.png` | `docs/qa/districts/golden_gate.png` | "A high stony CRAG bowl in the hills. Above the horizon: pale hazy sky and distant sunlit peaks. Just below the horizon: a middle band of broken cliff walls, ledges and scree slopes closing in at the left and right edges of frame, opening onto an empty gravel floor at centre." |
| `water.png` | `docs/qa/districts/golden_waterfront.png` | "The gravel SHORE of a wide slow river. Above the horizon: soft evening sky with warm light on the water. Just below the horizon: a middle band of glittering river surface and a far bank of reeds and willows, with low wet rocks at the left and right edges of frame only." |

`meadow.png` took a second pass: the first came back fogged edge to edge, so its
prompt calls the horizon at 34 % and adds "KEEP THE UPPER TWO THIRDS CRISP AND
SATURATED — clear air, readable green grass and green foliage, strong colour; the
haze belongs ONLY to the bottom band."

## THE SEAM — where a plate meets the 3D ground

`battle_stage3d.js` maps the whole plate onto a curved band standing 34 m from
the camera and pins ONE painted row of it to the world height where the arena
ground's far silhouette projects. Which row is `ZONES[zone].horizon` in that
file — **a fraction measured down from the top of the plate**:

| zone | `horizon` | what is being pinned to the 3D ground's far edge |
|---|---|---|
| meadow | 0.60 | just under the far meadow band, above the haze |
| forest | 0.63 | where the trunk bases dissolve into haze |
| crag | 0.56 | the base of the cliff walls |
| water | 0.60 | the near edge of the water, above the gravel |

Everything painted BELOW that row is hidden by the real floor; everything above
is the vista. That is why the bottom-30 %-empty rule in the prompt matters: it
is the band the 3D ground eats. A soft mist ribbon is drawn on the plate side of
the join, and scene fog dissolves the ground's far edge into the same haze
colour, so the two grounds meet in mist rather than on a line.

**Re-shooting a plate is therefore two steps:** generate it with the spec above,
then re-measure `horizon` for that zone — shoot
`tools/ui_mock.html?view=battle&zone=<zone>` and nudge the number until the
painted ground and the real ground line up. Nothing else changes.

The band is mapped at the plate's own aspect and only its central ~95 % is ever
in frame, so a 16:9 plate is upscaled about 1.3x where it shows. Going wider
than 16:9 buys resolution in the visible band if a future pass wants it.

## v1 — 2026-07-30 (superseded; in git history)

FF9-style pre-rendered battle backgrounds with an empty foreground clearing for
combatants, same four style references, same golden-hour direction. Recoverable
from history: they remain the right art for the **DOM fallback stage**, which
paints the plate flat behind CSS sprites and has no seam to honour. If that
stage is ever judged to look worse on the v2 plates, the fix is a second
directory keyed the same way, not a change here.
