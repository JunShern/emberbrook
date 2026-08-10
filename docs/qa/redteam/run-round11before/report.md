# Scene red-team — dellhollow — run round11before

judge `gemini:gemini-3.6-flash` (pinned) · 7 plates · naive

## 1. Calibration

_not scored in this run_


## 2. Survivors by bucket

### known (9)

- [quay-west/naive/navigation/sev2] The blocky stone staircase descends abruptly into a dark cliff gap without lighting or visual indicators showing if it connects to a path.
- [quay-west/naive/immersion/sev2] The blocky, grid-like steps clash abruptly with the detailed organic rock cliff texture around them.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 34.4,42,16.4,23
- [quay-west/naive/navigation/sev2] The oversized blocky steps blend directly into the cliff material with unclear step sizes, making it hard to read as a playable path.
- [cottage/naive/navigation/sev2] The main wooden ramp is heavily fractured into floating, misaligned planks, making it unclear if it represents a valid walkable route or impassable terrain.
- [cottage/naive/geometry/sev2] Planks along the collapsed section overlap and float in mid-air without structural supports or realistic debris geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 86.5,95.6,18,24.4
- [weave/naive/geometry/sev2] The brown blocky steps on the hillside look like unfinished placeholder terrain rather than stylized cliff rock or stairs.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 50,75.3,-4,16.8
- [deep-stairs/naive/geometry/sev2] The long wooden staircase spanning across the central gap lacks visible structural supports, appearing to float in mid-air.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 32.5,49.8,17.6,28.3
- [lockfive/naive/geometry/sev2] Wooden stair planks float in mid-air without structural supports underneath or connection to the cliff.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 67.6,85,20.7,30.4
- [lockfive/naive/geometry/sev2] The wooden stair treads float in mid-air without stringers or supporting framework underneath them.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 68,95.3,21.2,30.1

### new (34)

- [quay-west/naive/navigation/sev2] Walkable wooden walkways and building rooftops share near-identical green plank textures and flat geometry, making it ambiguous which surfaces are navigable paths versus off-limits roofs.
- [quay-west/naive/occlusion/sev2] Overlapping building levels, signboards, and posts obscure the main thoroughfare through the village, obscuring sightlines to potential exits.
- [quay-west/naive/geometry/sev2] A serrated wooden plank cuts horizontally across open space without visible structural support at either end.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 39.2,51.3,8.4,20.2
- [quay-west/naive/navigation/sev2] A dark gap drops off directly between upper and lower platforms, making it unclear whether it is a walkable path or a fatal drop.
- [quay-west/naive/occlusion/sev2] Pitch-black shadow conceals the ground level in the central pit, making it impossible to tell if it is a fall hazard or a walkable lower path.
- [quay-west/naive/geometry/sev1] The wooden stairs clip directly into the steep rock wall without supporting geometry or terrain blending.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 50.2,64.2,1.6,15.1
- [cottage/naive/immersion/sev1] The stylized conical tree is placed directly onto a smooth vertical rock face without roots or terrain support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 82,85.8,16.2,19.8
- [cottage/naive/navigation/sev2] The broken and overlapping wooden platforms create a chaotic path where it is unclear which surfaces are walkable versus non-walkable environment debris.
- [cottage/naive/geometry/sev1] The yellow cone-like object appears to float off the steep cliff face without a visible trunk or anchor point.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 91.7,95.4,15.5,18.9
- [cottage/naive/immersion/sev1] The long wooden ladder structure extends down the cliff face without proper structural anchoring or ground contact at its base.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 78.2,85.8,15.5,23.4
- [cottage/naive/geometry/sev2] The wooden planks along the collapsed ramp intersect and clip frantically into each other at erratic angles.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 78.6,95.8,14,24.3
- [cottage/naive/navigation/sev2] It is visually ambiguous whether the fractured, steep walkway is a valid platforming path or an impassable obstruction.
- [cottage/naive/immersion/sev1] The long metal/wooden ladder frame floats above the uneven rock wall without physical support brackets anchoring it.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 78.2,85.7,15.5,23.4
- [crossing/naive/geometry/sev2] Untextured low-poly grey polygon mesh pokes cleanly through the wooden floor surface.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,70,12.7,17.2
- [crossing/naive/geometry/sev2] Untextured, flat-shaded blue-grey polygons protrude into view at the bottom-right corner of the frame.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,70,12.7,17.2
- [crossing/naive/geometry/sev2] Untextured low-poly mesh clips through the wooden walkway surface in the bottom right foreground.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,70.1,12.7,17.2
- [weave/naive/navigation/sev2] Uniform brown coloring and dense visual clutter make walkable paths difficult to distinguish from roofs and background terrain.
- [weave/naive/navigation/sev2] Identical wooden textures and complex overlapping structures make walkable paths visually merge with rooftops, making navigation ambiguous.
- [weave/naive/navigation/sev2] Dense overlapping of multi-tiered platforms, roofs, and stilts makes it difficult to visually distinguish walkable paths from static scenery.
- [weave/naive/geometry/sev1] The orange rock formation appears clipped unnaturally onto the cliff background with disjointed shading.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 88.1,131.7,-1.7,18.2
- [deep-stairs/naive/geometry/sev1] The wooden plank walkway hovers above the ground without touching the terrain or having support posts underneath.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 31.7,43.8,19.3,29.9
- [deep-stairs/naive/immersion/sev1] An unnaturally long and thin wooden pole stretches unsupported across multiple vertical levels.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 42,49.5,19.8,30
- [deep-stairs/naive/immersion/sev1] An unrealistically long, thin wooden beam spans from the upper structure down to the lower platform without intermediate structural support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 42.1,49.5,19.8,30
- [lockfive/naive/geometry/sev1] The green fabric panels clip directly through the wooden decking and support beams below.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 59.9,84.3,17.6,28.5
- [lockfive/naive/geometry/sev2] The environment terminates abruptly into a solid black unrendered void beyond the pier.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 85.8,147.3,25.9,53.1
- [lockfive/naive/immersion/sev1] The cliff texture abruptly meets the flat water surface with a harsh straight line, revealing the flat backdrop polygon.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 85.5,147.8,24.7,53
- [north-landing/naive/geometry/sev1] Conical tree models protrude horizontally out of the vertical rock face without roots, soil, or natural trunk orientation.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 96.9,109.9,17.7,26.8
- [north-landing/naive/navigation/sev2] The sequence of stepping stones across the water leads directly into a flat retaining wall with no landing platform or exit.
- [north-landing/naive/navigation/sev2] Overlapping wooden staircases, platforms, and structural supports visually blend together, making traversable paths difficult to discern.
- [north-landing/naive/immersion/sev1] Multiple conical foliage models stick out horizontally from the vertical rock face without trunks or natural attachment.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 96.8,109.9,18.8,26.9
- [north-landing/naive/navigation/sev2] Scaffolding timber clutter intersects directly over the walkway ahead, making it unclear whether the path is navigable or blocked.
- [north-landing/naive/immersion/sev1] Stylized cone trees protrude horizontally directly out of the vertical cliff face without visible trunks or root support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 98.2,102.5,19.3,23
- [north-landing/naive/navigation/sev2] The central elevated pathway merges into a dense clutter of wooden supports and dark geometry, making it unclear if it continues as a playable path.
- [north-landing/naive/geometry/sev1] The square stepping stones sit flat on top of the water plane without depth, displacement, or underwater geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 86.8,95.4,33,42.4

### style-bar (0)



## 3. Budget

28 calls, 42368 prompt + 50086 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.