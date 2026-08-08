# Scene red-team — dellhollow — run 20260808-round7water

judge `gemini:gemini-3.6-flash` (pinned) · 5 plates · naive + checklist

## 1. Calibration

_not scored in this run_


## 2. Survivors by bucket

### known (6)

- [weave/checklist/navigation/sev3] the way out of this area on foot towards lockfive: ABSENT — No visible path towards lockfive extends continuously out of frame in this direction.
- [lockfive/naive/geometry/sev2] The wooden stair steps lack visible stringers or support structures underneath, making them appear to float mid-air above the lower dock.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 66.5,85,21.2,30.5
- [lockfive/naive/geometry/sev2] The wooden flight of stairs floats in mid-air without visible structural supports anchoring it to the ground or upper deck.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 66.1,94.9,21.2,30.1
- [lockfive/naive/navigation/sev2] Overlapping broken boardwalks and floating staircases obscure where the player can actually walk or traverse.
- [north-landing/naive/immersion/sev2] A green planked platform segment floats flat on the water surface without any visible supports or dock attachments.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 97.2,105.6,31.1,36.9
- [north-landing/naive/geometry/sev1] The stepping stones appear to float flat on the water surface without underwater foundations or proper visual anchoring.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 86.9,95.3,33.1,42.5

### new (29)

- [gate/naive/geometry/sev1] An orange triangle of skybox/missing geometry clips through the fog wall at the top-left corner.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 143.5,148.7,60.2,76.6
- [gate/naive/geometry/sev1] The cliff terrain geometry on the bottom right cuts off with sharp, unpolished blocky faces.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region -2.8,4.9,-6.5,4.8
- [gate/naive/geometry/sev1] A stray orange polygon/geometry artifact is visible at the very top-left edge of the scene.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 143.3,148.2,59.2,76.6
- [gate/naive/geometry/sev1] The huge background cliff face on the left has flat, severely stretched textures that make it look unrendered or unfinished.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 14.7,151.7,-3.6,72.6
- [gate/checklist/immersion/sev3] The world at the frame edges: WEAK — JUDGMENT: Upper cliff geometry transitions into flat, muted shading near top edge. _(also on crossing, weave, lockfive, north-landing)_
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 14.4,145.5,-2.6,72.6
- [gate/checklist/immersion/sev2] The water surface: WEAK — JUDGMENT: Water exhibits good color, but shoreline contact transitions appear stiff. _(also on weave)_
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 4.7,125.7,12.1,72.6
- [crossing/naive/geometry/sev2] A bright white, untextured polygon is visible along the bottom right edge.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.5,70,12.7,17.2
- [crossing/naive/geometry/sev2] The lower wooden walkways and stairs clip through each other with disjointed and missing support posts.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 69.4,87.5,20.8,36.4
- [crossing/naive/geometry/sev2] An untextured bright white geometry plane cuts into the bottom right corner of the view.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.5,69.9,12.7,17.2
- [crossing/naive/geometry/sev2] A flat white untextured plane is visible through the terrain at the bottom right edge, revealing missing geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.5,70,12.7,17.2
- [crossing/naive/navigation/sev2] The overlapping, broken wooden ramps and walkways create high visual noise, making it ambiguous which paths are walkable.
- [crossing/checklist/navigation/sev3] the route between Weave huts and Keepers' Cottage: ABSENT — The high plank bridge spanning the basin is not present in this camera view.
- [weave/naive/navigation/sev2] The cave opening is a solid pitch-black void with no lighting or visible interior, making it ambiguous whether it is an accessible path or decorative scenery.
- [weave/naive/navigation/sev2] High structural density and uniform wood materials cause walkable paths, railings, and rooftops to visually merge, making navigable routes difficult to distinguish from drops or hazards.
- [weave/naive/immersion/sev1] The water body cuts off sharply at the edge of the world geometry, revealing void space underneath.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 85.8,147.4,18.2,34.5
- [weave/naive/immersion/sev2] The water plane cuts off abruptly at the map boundary, exposing the void outside the level geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 105.6,147.8,19.9,31.4
- [weave/naive/geometry/sev1] The cave opening is a flat black cutout with no visible interior geometry or depth.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 82.9,133.7,-2.4,18.2
- [weave/naive/navigation/sev2] Overlapping wooden roofs, ramps, and platforms share identical textures and tones, making it difficult to distinguish walkable paths from non-navigable roofs.
- [weave/naive/immersion/sev2] The body of water terminates abruptly in mid-air at the level boundary, exposing empty void space.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 107.2,147.4,20.9,31.2
- [weave/naive/navigation/sev2] Uniform wood textures and dense layering cause walkable bridges, decorative scaffolding, and pitched roofs to blend together, making navigable routes ambiguous.
- [weave/naive/occlusion/sev1] The cave interior is a flat pitch-black silhouette, completely masking any visual depth or geometry inside.
- [lockfive/naive/immersion/sev2] The wooden guardrail segment floats unsupported over the water without posts anchoring it beneath.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 67.3,73,28.9,36.7
- [lockfive/naive/navigation/sev2] Multiple overlapping steps and disjointed wooden platforms create an ambiguous, confusing visual path for player movement.
- [lockfive/naive/geometry/sev1] The rock wall background abruptly ends at a flat dark horizontal seam against the water plane.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 105.4,147.2,25.8,53
- [lockfive/checklist/navigation/sev3] Dam Crest Gate: ABSENT — The iron-banded dam crest gate is not visible anywhere in this frame.
- [north-landing/naive/immersion/sev2] A detached green walkway panel floats flat in the water without support pillars or connection to nearby structures.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 92.1,100.1,33.9,43.4
- [north-landing/naive/immersion/sev1] Conical foliage models stick out horizontally from the smooth cliff wall without roots or stems.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 17.9,102.4,19.3,65
- [north-landing/naive/immersion/sev1] Conical green foliage assets are embedded directly into the vertical cliff face at unnatural angles without trunks, stems, or roots.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 96.6,109.9,18.1,27
- [north-landing/naive/navigation/sev2] The open hole in the platform floor suggests a path down, but lacks stairs, a ladder, or a visual prompt indicating how it can be used.

### style-bar (0)



## 2b. Aim census — did the judge point at what it named?

0 of 7 [QUALITY] verdicts REFUTED: the judge's own box held under 2% of the subject the verdict names. 2 on-subject, 0 absence-claim (census abstains), 5 unmeasurable.

- `quality:frame-edge-world` — 0/5 refuted; box coverage n/a
- `quality:water-read` — 0/2 refuted; box coverage 40.5%, 28.2%


## 3. Budget

30 calls, 53472 prompt + 55785 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.