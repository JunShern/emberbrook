# Scene red-team — dellhollow — run round11after

judge `gemini:gemini-3.6-flash` (pinned) · 7 plates · naive

## 1. Calibration

_not scored in this run_


## 2. Survivors by bucket

### known (8)

- [quay-west/naive/geometry/sev2] The cliffside stairs consist of harsh blocky cubes protruding from the smooth rockface, looking like placeholder geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 33.6,42,16.2,23
- [quay-west/naive/navigation/sev2] The steps descend into complete darkness, leaving it unclear if it is a playable path or a fall hazard.
- [quay-west/naive/geometry/sev2] The staircase cut into the cliff consists of plain, blocky geometry that looks unfinished compared to the surrounding wooden architecture.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 33.6,42.5,14.8,23
- [deep-stairs/naive/occlusion/sev2] Harsh, pitch-black shadows obscure the central cliff recess, making it impossible to discern path continuity or background geometry.
- [deep-stairs/naive/occlusion/sev2] Extremely pitch-black shadows obscure the cliff face and path landings, making vertical depth and potential routes invisible.
- [lockfive/naive/geometry/sev2] The wooden steps float unsupported along their left edge without any stringer or structural framework holding them.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 65.1,93.7,19,29.6
- [lockfive/naive/geometry/sev2] The wooden stair treads lack structural support stringers or posts underneath, appearing to float in mid-air.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 66.6,85.3,21.3,32.5
- [lockfive/naive/geometry/sev2] The steps on the central wooden staircase lack clear stringers or continuous structural supports, causing them to float in mid-air.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 66.6,85.3,21.3,32.5

### new (36)

- [quay-west/naive/navigation/sev2] Two large wooden signboards are placed flat across the walkway deck, awkwardly blocking path progression.
- [quay-west/naive/immersion/sev2] The large wooden roof structure extends out into open air above a canyon without visible supporting walls or posts beneath it.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 40.4,52.2,15.7,26.3
- [quay-west/naive/navigation/sev2] The wooden staircase leads directly into a solid cliff face without a platform or continuation path.
- [quay-west/naive/geometry/sev1] The green wooden panel clips directly into the floor structure without visible supports or mounts.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 39.4,45.9,13.9,21.5
- [quay-west/naive/navigation/sev2] Walkable platform walkways and structural roofs visually blend into each other, making navigable paths hard to distinguish from background roofs.
- [cottage/naive/occlusion/sev2] Extremely pitch-black lighting conceals the structure beneath the roof, hiding whether there is a doorway, passageway, or obstacle.
- [cottage/naive/navigation/sev2] The broken wooden walkway collapses into a messy pile of planks, leaving it ambiguous whether the slope is walkable terrain or decorative blocking debris.
- [cottage/naive/immersion/sev1] The long ladder hovers parallel to the rock face without visible mounting brackets or structural supports attaching it to the wall.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 78.2,85.9,15.5,23.3
- [cottage/naive/navigation/sev2] Multiple broken wooden platforms overlap at chaotic angles, making it difficult to discern playable pathways from decorative wreckage.
- [cottage/naive/occlusion/sev2] Heavy pitch-black shadows beneath the upper wooden structure completely hide the terrain and obscure potential paths.
- [cottage/naive/immersion/sev1] The white ladder/rail structure floats parallel to the cliff face without visible mounting supports or ground contact at the base.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 76,92.3,16.7,22.5
- [cottage/naive/navigation/sev2] The chaotic clutter of broken planks and overlapping angles makes it ambiguous whether this structure is a walkable path or impassable debris.
- [cottage/naive/immersion/sev2] The long ladder structure floats freely parallel to the rock wall without clear anchors or support posts.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 76,92,16.7,22.4
- [cottage/naive/geometry/sev1] The green stylised bush and lamp model clip directly into the sheer cliff surface.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 82.8,88.6,12.2,17.7
- [crossing/naive/geometry/sev2] A sharp, untextured geometric polygon clips through the ground terrain in the bottom-right corner.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,69.1,12.7,17.4
- [crossing/naive/geometry/sev2] A flat grey polygon clips awkwardly through the wooden floor surface.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,70,12.7,17.3
- [crossing/naive/navigation/sev2] Multiple parallel ramps and wooden elevated structures overlap closely, making it unclear which paths are accessible.
- [crossing/naive/geometry/sev2] An untextured grey triangular polygon clips visually into the wooden path surface.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,70.1,12.7,17.2
- [crossing/naive/navigation/sev1] Tilted and broken wooden walkway sections create ambiguous paths over the water.
- [weave/naive/geometry/sev2] The water body and scene geometry abruptly terminate into an unmodeled void along the left frame boundary.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 89,147.6,18.1,34.2
- [weave/naive/navigation/sev2] The dense layering of identical dark wood stilts, walkways, and roofs creates heavy visual monotony, making walkable paths indistinguishable from roofs and structural supports.
- [weave/naive/geometry/sev1] The vertical posts and railings of the upper platform clip directly into the sloped roof surface below without any structural anchors or physical support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 47.4,54,12.1,19.8
- [weave/naive/immersion/sev1] A flat, untextured green rectangular block stands on the bridge without support or details, standing out against the surrounding environment.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 60.9,81.5,-2.9,18.5
- [weave/naive/navigation/sev2] Multiple overlapping wooden ramps and elevated walkways lack clear visual depth and distinct connections, making path progression confusing to parse.
- [weave/naive/geometry/sev1] The upper stone stairs lead directly into the solid side wall of the top-right structure without a landing or doorway.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 50.4,69.3,-3.7,15
- [deep-stairs/naive/occlusion/sev2] Extreme cast shadow completely obscures the depth and geometry in the central cliff gap, hiding potential paths.
- [deep-stairs/naive/geometry/sev1] The green wooden walkway sections clip straight into the rocky terrain at unnatural angles without supporting posts or flush joints.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 31.9,44.2,18.8,29.5
- [deep-stairs/naive/geometry/sev1] The long diagonal wooden beam clips straight through the lower walkway deck without any structural socket or connection.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 27.1,47.9,17.3,29.5
- [deep-stairs/naive/geometry/sev1] The segmented wooden walkway floats above the ground without any vertical support posts anchoring it to the terrain.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 26.5,36.1,17.9,31
- [deep-stairs/naive/geometry/sev2] The green-surfaced wooden walkway segments float unsupported over the rocky slope without legs or anchors.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 31.7,43.7,19.4,29.8
- [north-landing/naive/geometry/sev1] Multiple conical tree models protrude horizontally directly out of the steep rock face without trunks or root anchorage, breaking believable placement.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 96.6,111.5,17.7,27.5
- [north-landing/naive/navigation/sev2] An open square gap in the wooden floor lacks railings or visual cues, creating an ambiguous hazards/navigation path.
- [north-landing/naive/geometry/sev2] The large gray dam and waterwheel housing appear as untextured greybox geometry, looking visually incomplete relative to the rest of the scene.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 66.1,92,27.6,52.4
- [north-landing/naive/immersion/sev1] Stylized cone-shaped objects are clipped perpendicularly into the sheer cliff face without logical attachment or roots.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 96.6,111.5,18.1,27.5
- [north-landing/naive/navigation/sev2] A sudden rectangular opening in the circular platform lacks railings or visual markers, making it ambiguous whether it is an intentional path down or a hazard.
- [north-landing/naive/immersion/sev1] Cone-shaped vegetation models are stuck horizontally into the steep cliff face, breaking immersion.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 95.7,111.2,17.6,27.7

### style-bar (0)



## 3. Budget

28 calls, 42321 prompt + 46640 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.