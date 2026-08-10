# Scene red-team — dellhollow — run round10leaf

judge `gemini:gemini-3.6-flash` (pinned) · 7 plates · naive + checklist

## 1. Calibration

_not scored in this run_


## 2. Survivors by bucket

### known (9)

- [crossing/naive/occlusion/sev2] Harsh pitch-black shadows completely obscure the walkable surfaces and stairs beneath the roof structures.
- [crossing/naive/navigation/sev2] The broken wooden planks and chaotic structure make it hard to tell if this is a valid walkway or an impassable gap.
- [deep-stairs/naive/geometry/sev2] The green wooden plank pathway floats above the cliff slope without visible structural supports underneath.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 31.7,44.5,18.9,28
- [deep-stairs/naive/navigation/sev2] The primary wooden staircase leads into floating platforms and shadow, making the intended path up the cliff ambiguous.
- [deep-stairs/naive/navigation/sev2] High-contrast shadows obscure the stairwell and cliff recess, making it ambiguous whether this leads to a playable upper path or is blocked wall geometry.
- [deep-stairs/naive/occlusion/sev2] Deep harsh shadows completely hide the terrain and structures inside the central crevice, obscuring potential walkways and stairs.
- [lockfive/naive/immersion/sev2] The stair treads float in mid-air without stringers, side supports, or visible structural joinery underneath.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 64.3,94.4,20.1,30
- [lockfive/naive/geometry/sev2] The wooden step planks float individually in the air without side stringers or supporting beam structures.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 68.3,81.7,20.5,31.4
- [lockfive/naive/geometry/sev2] The wooden steps extend outward over the water without visible side stringers or vertical supports, appearing to float.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 67.6,95.3,21.2,32.6

### new (45)

- [gate/naive/immersion/sev1] The large background cliff wall has severe vertical texture stretching and flat lighting, breaking visual believability.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 14.7,151.7,-3.6,72.6
- [gate/naive/immersion/sev1] The lower tree foliage clips directly into the rock wall without a clear trunk or branch connection.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region -0.9,11,-0.4,4.3
- [gate/naive/geometry/sev1] The tree trunk clips directly into the vertical rock wall without roots or a proper terrain base.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region -1.1,3.2,-1,3.6
- [gate/naive/immersion/sev1] The background cavern wall features noticeably low-resolution, blurry texturing that breaks visual consistency with the foreground.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 14.7,145.1,-1.8,72.6
- [gate/naive/navigation/sev2] The visual path connecting the upper cliff walkway to the lower harbor docks is hidden behind dense buildings and fences, making vertical navigation between levels ambiguous.
- [gate/naive/geometry/sev1] The tree foliage clips directly into the vertical cliff rock face without visible structural trunk anchoring.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region -4.4,12.5,-6.1,4.4
- [gate/checklist/immersion/sev3] The world at the frame edges: WEAK — JUDGMENT: Distant canyon walls look flat with repetitive low-detail shading near the top left border. _(also on crossing, weave, deep-stairs)_
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 14.7,144.9,-1.8,72.6
- [cottage/naive/navigation/sev2] The overlapping and fragmented wooden ramps create a visually chaotic path structure where it is unclear which surfaces are walkable routes and which are collapsed background geometry.
- [cottage/naive/geometry/sev2] The orange mesh embedded in the cliff face contains open holes that expose backface-culled hollow interiors.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 88.2,103.7,-1.9,18.6
- [cottage/naive/immersion/sev1] Untextured primitive orange cones stick straight out of the cliff rock face without grounding or visual integration into the environment.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 82,87.1,13.1,19.7
- [cottage/naive/geometry/sev1] The metal ladder frame clips directly through the wooden walkway railing at its base without any connecting joint geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 80.5,85.6,16.9,23.5
- [cottage/naive/navigation/sev2] The collapsed and overlapping wooden ramp sections create visual clutter, making it unclear whether this is a walkable path or impassable debris.
- [cottage/naive/immersion/sev1] Smooth orange conical primitives protrude directly out of the rocky cliff face without context, breaking visual consistency.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 83.4,87.1,13.1,20.1
- [cottage/naive/immersion/sev1] A cluster of bright orange vehicle wreckage sits unnaturally clipped high up into the rock wall without clear structural support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 88.3,103.8,-1.8,18.6
- [cottage/naive/navigation/sev2] The broken and tilted wooden planks create an ambiguous path where it is unclear if the player can walk across or will fall through.
- [cottage/naive/geometry/sev1] The orange metallic debris mesh appears torn and clipped weirdly into the cliff face, making the geometry look incomplete.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 88.3,103.7,-1.9,18.6
- [cottage/checklist/occlusion/sev2] a door / entrance you can go through ("Enter Keepers' Cottage"): OCCLUDED — The lower front wall where an entrance would be located is hidden behind collapsed wooden beams and walkway platforms.
- [crossing/naive/geometry/sev2] Incomplete, untextured polygonal geometry clips through the wooden walkway floor at the bottom right corner.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,70,12.7,17.2
- [crossing/naive/occlusion/sev2] Harsh pitch-black shadows beneath the roofs and ramps completely obscure the ground level walkways, making navigable space unreadable.
- [crossing/naive/geometry/sev1] Broken wooden stairs and platform planks hover awkwardly without solid structural support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 71.1,83.3,20,38.7
- [crossing/naive/geometry/sev2] Raw, untextured low-poly geometry cuts into the scene along the bottom right edge.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,70,12.7,17.2
- [crossing/naive/navigation/sev1] Broken, overlapping wooden planks create ambiguous boundaries and make navigable paths difficult to distinguish.
- [crossing/naive/geometry/sev2] Untextured blue-grey geometric shapes clip awkwardly through the wooden platform structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,70.2,12.7,17.2
- [crossing/naive/occlusion/sev2] Deep pitch-black shadows under the gate structure obscure the floor and connection to the lower dock area.
- [weave/naive/navigation/sev2] Extreme visual clutter and heavy shadow overlapping make it very difficult to distinguish walkable paths from non-walkable roofs and structural supports.
- [weave/naive/immersion/sev1] A row of glass window frames sits directly on top of the open pier floor without supporting walls.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 58.8,76.8,21.5,31
- [weave/naive/geometry/sev1] An orange spiky sphere clips awkwardly into the rock wall above the upper path.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 82.9,134.7,-1.8,18.7
- [weave/naive/immersion/sev2] An orange textured sphere rests unnaturally against the cliff face without proper grounding or clear contextual integration.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 82.9,133.7,-2.4,18.2
- [weave/naive/navigation/sev2] The high density of overlapping wooden planks, roofs, and stilts lacks visual hierarchy, making it very difficult to identify walkable paths versus decorative structures.
- [weave/naive/navigation/sev2] The uniform dark-brown wood material and dense overlapping geometry make it extremely difficult to visually distinguish walkable paths from roofs and background supports.
- [deep-stairs/naive/occlusion/sev2] Extremely deep shadow across the central cliff completely obscures the geometry and path continuity.
- [deep-stairs/naive/geometry/sev2] The green-patterned ramp sections intersect unnaturally and float above the terrain without structural supports underneath.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 31.6,44.3,19,29.4
- [deep-stairs/naive/geometry/sev1] The long wooden support pole extends continuously downward and clips into the platform below without a clear base joint or frame connection.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 41.1,49.5,21.2,30
- [deep-stairs/naive/immersion/sev2] The long diagonal wooden staircase spans across the chasm with no visible supporting pillars or structural framing underneath.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 32.4,47.8,18,26.7
- [deep-stairs/naive/geometry/sev1] The flat blue water polygon abruptly clips into the rocky cliff face without any shoreline geometry or blending.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 36.6,44,23.4,29.8
- [deep-stairs/checklist/immersion/sev3] The water surface: FAILING — JUDGMENT: The water surface appears as a flat, untextured blue plane without transparency, specular highlights, or believable edge contact with the surrounding terrain.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 36.7,43.7,23.5,30.1
- [lockfive/naive/geometry/sev2] The water plane abruptly terminates at a straight line against a dark empty void, exposing the edge of the level.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 81.5,150.5,5.6,25.6
- [lockfive/checklist/navigation/sev3] Dam Crest Gate: ABSENT — The dam crest and its iron-banded gate lie beyond the top edge of the frame.
- [north-landing/naive/navigation/sev2] The dense cluster of overlapping wooden beams and ramps along the cliff makes it visually confusing to tell which paths are walkable.
- [north-landing/naive/navigation/sev1] The stepping stone path leads towards a dead end at the water wheel wall, making it ambiguous whether it is a intended route.
- [north-landing/naive/navigation/sev2] Dense overlapping wooden beams, platforms, and ladders obscure the main path, making it hard to see where the player can walk.
- [north-landing/naive/immersion/sev1] Conical green bushes protrude horizontally from the sheer rock wall without trunks or roots, appearing pasted onto the surface.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 94.3,111.3,18.2,28.2
- [north-landing/naive/navigation/sev2] The main walkway narrows into a dense cluster of wooden scaffolding and roofs, making it hard to see where the path continues or if it is walkable.
- [north-landing/naive/geometry/sev1] An un-rimmed square hole cut into the wooden floor lacks any hatch, border, or ladder geometry, looking like a missing floor section.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 82.3,89.4,36.8,44.5
- [north-landing/naive/immersion/sev1] Conical foliage models stick horizontally straight out of the sheer vertical rock wall, breaking believable terrain placement.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 95.3,102.2,19.2,23.9

### style-bar (0)



## 2b. Aim census — did the judge point at what it named?

0 of 5 [QUALITY] verdicts REFUTED: the judge's own box held under 2% of the subject the verdict names. 1 on-subject, 0 absence-claim (census abstains), 4 unmeasurable.

- `quality:frame-edge-world` — 0/4 refuted; box coverage n/a
- `quality:water-read` — 0/1 refuted; box coverage 57.1%


## 3. Budget

41 calls, 70934 prompt + 77698 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.