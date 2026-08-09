# Scene red-team — dellhollow — run round8awning

judge `gemini:gemini-3.6-flash` (pinned) · 7 plates · naive + checklist

## 1. Calibration

_not scored in this run_


## 2. Survivors by bucket

### known (17)

- [loop-stairs/naive/occlusion/sev2] Extremely dark shadow under the stairs and building completely obscures ground visibility and potential paths behind the structure.
- [loop-stairs/naive/geometry/sev1] The wooden stair treads float loosely on top of rectangular dirt columns without proper structural joints.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 52.3,62.3,1.9,12.5
- [loop-stairs/naive/geometry/sev1] The wooden stair planks float slightly above and clip unnaturally into the tops of the supporting dirt blocks.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 52.3,62.2,1.9,12.5
- [quay-west/naive/geometry/sev1] The staircase structure consists of blocky voxel-like geometry that contrasts unnaturally with the detailed rock wall behind it.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 34.1,42,16.2,23
- [quay-west/naive/geometry/sev1] The stepped path cut into the right cliff face consists of harsh voxel-like block shapes that clash with the surrounding terrain.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 34.1,42,16,23
- [quay-west/checklist/navigation/sev3] the way out of this area on foot towards lockhead: ABSENT — No exit path towards lockhead is visible leading off-screen in this view.
- [quay-west/checklist/navigation/sev3] the way out of this area on foot towards weave: ABSENT — No exit path towards weave is visible leading off-screen in this view.
- [quay-west/checklist/navigation/sev3] the way out of this area on foot towards loop-stairs: ABSENT — No exit path towards loop-stairs is visible leading off-screen in this view.
- [lockhead/naive/geometry/sev2] A stray thin white polygon floats in mid-air near the staircase.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 52.9,64.2,7.8,16.9
- [crossing/naive/immersion/sev1] A flat wooden plank floats in isolation on the water with no supports or buoyancy physics.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 100.2,107.6,30.6,37.9
- [crossing/naive/immersion/sev1] A wooden plank floats on the water without any supporting structure or visible attachment.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 100,107.6,30.5,37.8
- [crossing/naive/geometry/sev1] The damaged wooden pier features floating, disconnected planks lacking supporting posts underneath.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 69.7,87.5,21,37.6
- [crossing/naive/immersion/sev2] A wooden platform floats unsupported over the water surface.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 99.9,107.5,30.5,37.9
- [crossing/naive/geometry/sev2] Disconnected wooden planks create messy, floating, and clipping geometry in the lower walkway.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 69.4,87.5,20.8,36.4
- [deep-stairs/naive/geometry/sev2] The wooden stair treads float individually in mid-air without any supporting stringers, risers, or structural beams.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 32.9,44.7,17.6,23
- [deep-stairs/naive/geometry/sev2] The wooden stair steps float individually in mid-air without stringers, side rails, or structural supports underneath.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 32.7,43,15.2,22.2
- [deep-stairs/naive/geometry/sev2] The wooden step planks span across the gap without stringers or structural supports underneath, appearing to float mid-air.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 33.1,49.7,16.7,22.2

### new (29)

- [gate/naive/geometry/sev2] An orange void/skybox leak is visible where the cliff mesh terminates abruptly at the top-left edge.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 144.5,148.6,69,77.2
- [gate/naive/geometry/sev1] An untextured orange polygon leaks through the top-left edge of the mountain mesh.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 143.9,148.8,62.1,76.5
- [gate/naive/geometry/sev2] The terrain mesh terminates prematurely in the top-left corner, exposing the skybox background past the map boundary.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 143.6,148.5,63.3,78.2
- [gate/checklist/immersion/sev3] The world at the frame edges: WEAK — JUDGMENT: Distant background fog and canyon walls appear somewhat flat, though cliff geometry frames the shot reasonably well. _(also on crossing, weave)_
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 14.7,152.1,-2.7,72.6
- [loop-stairs/naive/immersion/sev1] Blocky, pixelated square shadow glitches appear on the terrain surface near the bottom right.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 46.6,55.8,8.3,14.6
- [loop-stairs/naive/geometry/sev1] The green roof tiles are constructed from disjointed rectangular blocks leaving noticeable empty gaps between individual shingles.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 46.1,57.3,-0.8,15.3
- [loop-stairs/checklist/occlusion/sev2] the way out of this area on foot towards shelf-east: OCCLUDED — Hidden behind the shelf house structure and stacked crates blocking the upper east exit.
- [quay-west/naive/navigation/sev2] The overlapping decks, roofs, and bridges share identical textures and lighting, making it difficult to discern walkable pathways from roofs or environmental hazards.
- [quay-west/naive/navigation/sev2] A pitch-black pit opens up between the wooden platforms with no lighting or depth cues, making it ambiguous whether it is navigable space or a fatal fall.
- [quay-west/naive/navigation/sev2] Walkable paths, rooftops, and edge drops share identical texturing and dark shadows, making it difficult to discern navigable routes from hazards.
- [quay-west/naive/geometry/sev1] The large sloped wooden roof cantilevers over the deep chasm without visible supporting posts or beams beneath its edge.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 40.4,52.2,16,26.4
- [lockhead/naive/navigation/sev2] A light post is placed directly in the center of the narrow elevated walkway, blocking player movement.
- [lockhead/naive/immersion/sev1] A conical green tree model clips directly through the lower wooden support structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 77.9,81.6,14.9,18.4
- [crossing/naive/geometry/sev2] A bright white untextured mesh protrudes into the bottom right corner of the screen.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,70.1,12.7,17.2
- [crossing/naive/occlusion/sev2] Pitch-black cast shadows completely blind the player to details and geometry along the central walkway and roof.
- [crossing/naive/geometry/sev2] An untextured white low-poly mesh protrudes sharply out of the environment geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,70,12.7,17.2
- [crossing/naive/geometry/sev1] A blocky container clips directly through the sloped roof structure beneath it.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 67.7,74.5,16.9,21.9
- [crossing/checklist/navigation/sev3] the route between Weave huts and Keepers' Cottage: ABSENT — No high plank bridge spanning across the basin is present in this view.
- [weave/naive/navigation/sev2] The dense layering of walkways, roofs, and stilts with identical wood materials makes it hard to distinguish navigable routes from background scenery.
- [weave/naive/occlusion/sev2] The interior of the cave mouth is pure unlit black, creating a jarring void that completely hides any depth or path information.
- [weave/naive/navigation/sev2] Walkable platforms, stairs, and roof structures use identical wood textures and shading, making playable pathways visually ambiguous.
- [weave/naive/geometry/sev2] The cave entrance is a flat black silhouette cutout that lacks internal geometry or natural rock depth.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 79.9,133.2,-2.6,19.1
- [weave/naive/geometry/sev2] The body of water cuts off abruptly against a dark void at the left edge of the map without any surrounding terrain or border geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 85.8,147.5,19.1,34.5
- [weave/naive/navigation/sev2] The cave entrance in the upper cliff face is solid black without lighting or interior geometry, making it unclear whether it is a usable route or non-playable space.
- [weave/checklist/navigation/sev2] the route between Weave huts and Fish dock: VISIBLE-BUT-ILLEGIBLE — The ladder blends into the dense surrounding forest of wooden stilt posts and crossbeams, making it hard to distinguish as a ladder.
- [deep-stairs/naive/geometry/sev1] Wooden beams and boat-like structures clip improperly into each other and into the ground terrain.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 26.2,34.7,24.6,31.4
- [deep-stairs/naive/geometry/sev1] The angled plank ramp hovers above the terrain without vertical stilts or physical anchor points.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 31.4,43.1,17.9,29.8
- [deep-stairs/checklist/navigation/sev2] Cookhouse: VISIBLE-BUT-ILLEGIBLE — The building lacks glowing windows, smoke, or culinary props that would distinguish it as a cookhouse.
- [deep-stairs/checklist/immersion/sev3] The water surface: FAILING — The water appears as a flat, opaque blue polygon cutting sharply into the rock mesh without transparency, reflections, or foam contact.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 36.8,44.6,23.7,29.9

### style-bar (0)



## 2b. Aim census — did the judge point at what it named?

0 of 5 [QUALITY] verdicts REFUTED: the judge's own box held under 2% of the subject the verdict names. 2 on-subject, 0 absence-claim (census abstains), 3 unmeasurable.

- `quality:frame-edge-world` — 0/3 refuted; box coverage n/a
- `quality:water-read` — 0/2 refuted; box coverage 51.7%, 54.5%


## 3. Budget

40 calls, 66036 prompt + 75672 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.