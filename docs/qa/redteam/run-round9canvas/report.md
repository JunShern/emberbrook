# Scene red-team — dellhollow — run round9canvas

judge `gemini:gemini-3.6-flash` (pinned) · 7 plates · naive + checklist

## 1. Calibration

_not scored in this run_


## 2. Survivors by bucket

### known (8)

- [loop-stairs/naive/occlusion/sev2] Harsh diagonal shadow obscures the depth and individual treads of the staircase, making it hard to tell if it is a continuous, walkable path.
- [loop-stairs/naive/navigation/sev2] The stairs lead up to a narrow platform completely blocked by crates and sacks, leaving no clear path forward or exit.
- [loop-stairs/checklist/navigation/sev3] the way out of this area on foot towards shelf-east: ABSENT — No path continues out of frame on foot towards the eastern side of the shelf.
- [quay-west/naive/geometry/sev1] The staircase carved into the cliff face consists of stark blocky voxel cubes that clash with the organic texture of the surrounding cliff rock.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 33.2,43.1,11.2,23
- [lockhead/naive/geometry/sev2] A stray thin beam or cylinder is floating horizontally in mid-air across the steps.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 53.1,64.2,7.8,16.9
- [lockhead/naive/geometry/sev2] A stray thin piece of mesh geometry floats in mid-air next to the upper staircase.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 53,60.1,7.8,12.5
- [deep-stairs/naive/geometry/sev2] The wooden walkway planks float above the terrain without visible support posts or structural beams underneath.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 31.6,45.2,18.9,29.8
- [deep-stairs/naive/occlusion/sev2] Pitch-black cast shadow completely obscures the passage and stairwell cut into the cliff face.

### new (34)

- [gate/naive/geometry/sev2] The slope geometry at the bottom right has harsh, blocky facets and stretched UV maps that break the environment's visual flow.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region -2.2,10.1,-6.5,5.7
- [gate/naive/immersion/sev1] The tree trunk emerges directly out of solid vertical rock face without roots or a soil pocket.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region -1.4,8.6,-1.4,3.9
- [gate/naive/immersion/sev1] The vertical banners on the cliff wall float directly against the rock face without any visible mounting rods or hooks.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 8.7,25.8,-1.4,4.2
- [gate/naive/geometry/sev2] A stray untextured orange polygon clips into the sky area at the top-left edge of the screen.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 143.1,148.8,53.7,77.6
- [gate/naive/immersion/sev1] The trees protrude directly out of vertical shear rock face without visible roots, soil, or anchored trunks.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region -4.5,14.4,-6.1,4.3
- [gate/checklist/immersion/sev3] The world at the frame edges: WEAK — JUDGMENT: The far canyon background displays low-detail texturing and flat lighting that visually degrades near the top frame edge. _(also on weave)_
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 14.7,152.1,-2.7,72.6
- [loop-stairs/naive/navigation/sev2] The top of the stairs leads into a cramped ledge cluttered with boxes and barrels, making the continuation of the route unclear.
- [loop-stairs/naive/geometry/sev1] The wooden roof clips directly into the rock cliff wall without any connecting geometry or trim.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 49.9,57.3,-1.4,14.8
- [loop-stairs/naive/immersion/sev2] The hanging line with flags terminates mid-air on the right without being attached to any wall or post.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 45.7,50.1,8.3,11.6
- [loop-stairs/naive/navigation/sev2] The staircase leads up to an ambiguous, cramped ledge beside the building with no clearly readable doorway or entrance.
- [loop-stairs/naive/immersion/sev1] The decorated banner line clips directly into the ground terrain surface.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 54.6,60.6,11,15.9
- [quay-west/naive/navigation/sev2] Green tiled surfaces are used identically for both pitched rooftops and flat walkways, making it difficult to visually distinguish traversable ground from non-walkable roofs.
- [quay-west/naive/geometry/sev1] The rock staircase consists of raw, perfectly cubical steps that clash visually with the surrounding natural terrain geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 33.4,41.9,16.9,23
- [quay-west/naive/immersion/sev2] Unnatural orange geometry and pitch-black void holes beneath the central platforms reveal untextured or clipped interior mesh spaces.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 37.8,44.3,14.8,24.4
- [quay-west/naive/navigation/sev2] The distinction between walkable wooden platforms and inaccessible roofs is ambiguous due to identical green plank textures and visual noise.
- [quay-west/naive/geometry/sev1] The wooden steps clip directly into the organic rock wall without logical structural supports or terrain blending.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 52.9,64.1,1.8,12.5
- [quay-west/naive/navigation/sev2] Overlapping wooden walkways and rooftops share identical textures and green tile patterns, making it ambiguous which surfaces are walkable paths and which are decorative roofs.
- [quay-west/naive/occlusion/sev2] Two large blank wooden signboards sit directly along the main platform, blocking the player's view of the path and space behind them.
- [lockhead/naive/geometry/sev2] A thin stray mesh polygon extends horizontally into open air from the stairs structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 52.9,60.1,7.8,12.5
- [crossing/naive/geometry/sev2] Incomplete low-poly grey mesh geometry clips through the wooden walkway surface.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,70.1,12.7,17.2
- [crossing/naive/geometry/sev2] A bright untextured polygon wedge clips through the wooden walkway surface.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,70.1,12.7,17.2
- [weave/naive/navigation/sev2] The dark tunnel opening lacks lighting or edge contrast, making it visually ambiguous whether it is an accessible route or background detail.
- [weave/naive/navigation/sev2] Overlapping wooden boardwalks, roofs, and stilts share identical color and texture, making walkable paths difficult to distinguish from static structures.
- [weave/naive/immersion/sev2] The water and cliffs cut off abruptly at the left frame edge, revealing an unrendered void beyond the environment.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 88.3,106.5,-2.4,1.3
- [weave/naive/navigation/sev2] The dense layering of stilted wooden platforms and rooftops sharing identical textures makes it difficult to distinguish walkable paths from non-walkable roofs.
- [weave/naive/occlusion/sev1] The cave entrance in the cliff face is rendered as a pitch-black shape, obscuring whether it is an accessible tunnel or solid rock.
- [weave/naive/navigation/sev2] Walkable wooden platforms visually merge with adjacent roof planes and walkways due to uniform textures and lighting, making navigation pathways ambiguous.
- [weave/naive/exit/sev2] The dark cave opening is rendered as a flat black void without depth cues, making it ambiguous whether it is an accessible tunnel or non-interactive geometry.
- [weave/checklist/occlusion/sev2] the route between Weave huts and Fish dock: OCCLUDED — Hidden behind the dense stilt piles and lower deck supports beneath the huts.
- [deep-stairs/naive/occlusion/sev2] Extremely harsh cast shadows completely obscure the pathing and structure inside the cliff wall crevice, making depth and layout unreadable.
- [deep-stairs/naive/navigation/sev2] Extremely dark cast shadows obscure the cliff recess and path landings, making it unclear where the route continues.
- [deep-stairs/naive/geometry/sev2] The main wooden staircase spans across open air without any support posts or structural frame anchoring it underneath.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 32.3,47.4,17.9,30.5
- [deep-stairs/naive/immersion/sev1] The small hanging lantern inside the dark cliff niche floats without visible cords or mountings attaching it to the rock.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 38.1,43.2,11.2,19.8
- [deep-stairs/checklist/immersion/sev3] The water surface: FAILING — JUDGMENT: The water reads as a flat, opaque teal fill polygon with no transparency, wave texture, or believable contact shading along the rocks.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 36.7,43.4,23.6,30.1

### style-bar (0)



## 2b. Aim census — did the judge point at what it named?

0 of 3 [QUALITY] verdicts REFUTED: the judge's own box held under 2% of the subject the verdict names. 1 on-subject, 0 absence-claim (census abstains), 2 unmeasurable.

- `quality:frame-edge-world` — 0/2 refuted; box coverage n/a
- `quality:water-read` — 0/1 refuted; box coverage 57.5%


## 3. Budget

39 calls, 64326 prompt + 70858 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.