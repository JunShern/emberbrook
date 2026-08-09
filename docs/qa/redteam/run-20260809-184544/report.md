# Scene red-team — emberbrook — run 20260809-184544

judge `gemini:gemini-3.6-flash` (pinned) · 11 plates · naive + checklist

## 1. Calibration

_not scored in this run_


## 2. Survivors by bucket

### known (0)


### new (86)

- [woodroad/naive/geometry/sev2] The edge of the circular stone pad consists of coarse, stair-stepped blocky polygons that unnaturally cut into the surrounding ground terrain.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 44.6,59.2,-34.1,-21.9
- [woodroad/naive/geometry/sev2] The perimeter of the circular paved area features blocky, stair-stepped cutout geometry where it intersects with the ground terrain.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 44.2,59.2,-34.4,-21.7
- [woodroad/naive/geometry/sev2] The edges of the circular paved area display harsh, unblended stair-stepped geometry clipping awkwardly into the terrain.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 44.6,59.2,-34.4,-21.9
- [woodroad/naive/immersion/sev1] Intense warm illumination originates high up inside the tree canopy where no light fixture exists.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 53.8,64.3,-10.5,4.8
- [woodroad/checklist/navigation/sev3] a door / entrance you can go through ("Leave Emberbrook"): ABSENT — No door or entrance structure is present in this outdoor scene.
- [waystone/naive/geometry/sev2] The concrete path slabs intersect awkwardly with exposed black gaps and unaligned edges.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 54.9,59.3,-13.6,-9.2
- [waystone/naive/geometry/sev1] The path slab terminates in an awkward floating edge above the terrain rather than seating naturally into the ground.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 54.9,59.5,-13.6,-9.2
- [waystone/naive/geometry/sev1] The concrete path slab ends abruptly next to the pedestal, leaving an unaligned edge that floats slightly over the terrain.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 54.6,60.3,-13.6,-7
- [arch/naive/geometry/sev2] The flat gray pathway geometry clips directly into the uneven terrain mesh without edge detailing or depth transitions.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 47,66,5.2,23.2
- [arch/naive/immersion/sev1] The light source appears as a flat glowing white square attached directly to the wall without a lamp or fixture model.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 40,44.7,27.4,38.6
- [arch/naive/occlusion/sev2] Dense dark tree branches fill and obscure almost the entire right half of the frame, blocking visual sightlines into that portion of the area.
- [arch/naive/geometry/sev2] Flat grey geometry slabs cut sharply into the ground terrain without proper blending or structural edges.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 53.5,63.1,5.1,21.5
- [arch/naive/occlusion/sev2] Dense, dark foliage dominates the right side of the frame, obscuring sightlines and potential pathways.
- [arch/naive/navigation/sev2] Heavy shadows and uniform ground tone make it hard to tell where navigable paths lead compared to open terrain.
- [arch/naive/occlusion/sev2] Dense foreground tree branches completely block the view of the environment, walkways, and potential interactables on the right side of the scene.
- [arch/naive/navigation/sev2] The dark, angled pathway segments blend into tree shadows and terminate abruptly, leaving it ambiguous where the player is meant to walk.
- [arch/naive/geometry/sev1] The dark walkway ramp geometry clips flatly through the surrounding terrain with sharp, unintegrated edges.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 53.4,59.8,6.3,20.3
- [arch/checklist/navigation/sev3] the route between Village Arch and Orchard rows: ABSENT — No branching path toward orchard rows is visible.
- [arch/checklist/navigation/sev3] the way out of this area on foot towards orchard: ABSENT — No path exiting toward an orchard is present. _(also on orchard)_
- [orchard/naive/occlusion/sev2] Large foreground trees completely block the camera view of the ground plane and play area in the lower right corner.
- [orchard/naive/occlusion/sev2] Extremely dark pitch-black shadows completely obscure details on the ground next to and under the building roof.
- [orchard/naive/occlusion/sev2] The pitch-black shadow under the building overhang completely hides the ground, doorways, and any potential playable space beneath it.
- [orchard/naive/occlusion/sev2] The dense foliage heavily blocks the view of the ground and potential play space underneath.
- [orchard/naive/navigation/sev2] The extremely dark shadow completely hides ground details and potential obstacles, making pathfinding unclear.
- [orchard/checklist/navigation/sev3] Orchard rows: ABSENT — No orchard rows, apple trees, ladders, or baskets are present in this frame.
- [orchard/checklist/navigation/sev2] Cider press barn: VISIBLE-BUT-ILLEGIBLE — The barn structure is visible, but its interior and contents are completely obscured in deep shadow, rendering any cider press or crates illegible. _(also on therise)_
- [orchard/checklist/navigation/sev3] the route between Village Arch and Orchard rows: ABSENT — No path connecting a village arch to orchard rows exists in the frame.
- [orchard/checklist/navigation/sev3] the route between Orchard rows and Cider press barn: ABSENT — No path leading between orchard rows and the barn is present.
- [therise/naive/geometry/sev2] The dark path tiles clip directly through the terrain mesh with hard, raw geometric edges and visible alignment issues.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 62.1,69.4,21.2,26
- [therise/naive/geometry/sev2] The ground path plane clips unnaturally through the terrain with sharp exposed edges.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 55.3,61.6,14.3,21.2
- [therise/naive/geometry/sev1] A ground mesh strip terminates abruptly with sharp angled geometry cutting into the dirt.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 48.9,56.2,12.8,17.9
- [therise/naive/geometry/sev2] The ground plane exhibits sharp, unnatural polygonal cuts and misaligned mesh seams.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 55.1,61.6,14.2,21.9
- [therise/checklist/occlusion/sev2] Item Shop: OCCLUDED — The structure is blocked from view by surrounding trees and foreground roofs.
- [therise/checklist/navigation/sev2] The Heartlight: VISIBLE-BUT-ILLEGIBLE — The light pedestal is extremely distant and dark, rendering the flame illegible.
- [therise/checklist/immersion/sev2] The sky: WEAK — JUDGMENT: The visible patch of sky is a simple blue gradient with minimal atmospheric texture. _(also on pondlane)_
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 60,94.5,26.4,131.3
- [therise/checklist/immersion/sev2] The world at the frame edges: WEAK — JUDGMENT: Dense trees enclose most edges well, though ground shading near the bottom left feels somewhat flat. _(also on pondlane)_
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region -19.4,126.5,12.7,149.1
- [square/naive/occlusion/sev2] Dense foreground foliage completely blocks the view of the play area and potential pathways in the lower-left portion of the frame.
- [square/naive/occlusion/sev2] A large foreground roof structure heavily obscures the view of the space in the bottom-right corner.
- [square/naive/occlusion/sev2] Dense trees in the bottom-left foreground block visual access to the ground area beneath them.
- [square/naive/immersion/sev1] The central object is completely overexposed by intense bright lighting, blowing out all visual details.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 60.6,67.6,39.5,46.7
- [square/naive/occlusion/sev2] A massive foreground roof severely obstructs the view of the playable space and surrounding ground in the bottom-right corner.
- [square/checklist/navigation/sev3] the route between Village Arch and Festival Square: ABSENT — The village arch and its connecting route are outside this frame.
- [square/checklist/navigation/sev3] the route between Brook footbridge and Festival Square: ABSENT — The brook footbridge route is not visible in this frame.
- [pondlane/naive/occlusion/sev2] Extremely dense foliage fills the entire middle ground, completely obscuring paths, ground layout, and building entrances.
- [pondlane/naive/geometry/sev1] A segment of the black string hangs floating and disconnected from the central wooden pole.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 79.3,85.6,46.1,50.8
- [pondlane/naive/immersion/sev2] The scene terminates abruptly into a flat, empty grey void with bare tree models floating along the horizon line.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 67.7,108,53.1,77.9
- [pondlane/naive/geometry/sev1] A stray line segment floats in mid-air, disconnected from the surrounding support poles.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 79.3,85.1,46.2,50.8
- [pondlane/naive/occlusion/sev2] A massive tree canopy obscures the ground level and any paths beneath it from this camera angle.
- [pondlane/naive/geometry/sev2] A flat-shaded blue polygonal ribbon cuts through the ground, appearing as untextured placeholder geometry.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 67,76.4,50.3,62.1
- [pondlane/naive/immersion/sev2] The hanging wire snaps and disappears in mid-air rather than connecting continuously between the support posts.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 71.2,83,45.5,50.6
- [pondlane/naive/navigation/sev2] Dense foliage and deep shadows obscure the ground throughout the middle ground, making walkable paths ambiguous.
- [pondlane/checklist/navigation/sev2] The Pond: VISIBLE-BUT-ILLEGIBLE — Appears as a dark, flat green surface lacking clear aquatic characteristics.
- [pondlane/checklist/navigation/sev3] Pond jetty: ABSENT — No dock structure is visible along the water edge.
- [pondlane/checklist/navigation/sev3] Washline green: ABSENT — No open field area is present in this view.
- [pondlane/checklist/navigation/sev3] Brook mouth: ABSENT — The brook junction with the river is off-camera.
- [pondlane/checklist/navigation/sev3] Weir & sluice: ABSENT — No weir or sluice mechanism is visible.
- [pondlane/checklist/navigation/sev3] Finn's smokehouse: ABSENT — The fish smokehouse structure is not visible.
- [pondlane/checklist/navigation/sev3] Pip's den: ABSENT — Hidden under the bank line.
- [pondlane/checklist/navigation/sev3] the route between Pond jetty and Washline green: ABSENT — Route is obscured by dense tree foliage.
- [pondlane/checklist/immersion/sev2] The water surface: WEAK — JUDGMENT: Surface appears flat with minimal edge blending or transparency.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 70.3,76.7,52.4,62
- [homerow/naive/geometry/sev2] A massive wooden disk or log clips directly into the wall of the rightmost house.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 50.5,56.6,55.2,61.2
- [homerow/naive/immersion/sev2] A pitch-black rectangular box or unlit polygon geometry rests unnaturally on the stone pathway.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 33.4,39.4,47.2,53.1
- [homerow/naive/geometry/sev2] Flat brown placeholder blocks appear attached to the wall without texture or detailed geometry.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 49.2,55.5,55.2,60.7
- [homerow/naive/geometry/sev2] A pitch-black rectangular volume with missing lighting or missing texture sits directly on the stone walkway.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 44.1,50.1,56.7,61.9
- [homerow/naive/geometry/sev1] A large wooden wheel-like geometry clips into the wall and terrain on the right.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 44.1,51.2,43,53.5
- [homerow/checklist/occlusion/sev2] Brook spring: OCCLUDED — The brook spring is hidden inside the stone spring house structure at top left.
- [homerow/checklist/navigation/sev3] Upper lane (closed): ABSENT — The closed upper lane with festival cart is not present in this shot.
- [homerow/checklist/occlusion/sev2] the route between Mara & Pip's cottage and Rowan's house: OCCLUDED — The direct route is occluded where the building footprint overlaps the pathway location.
- [northlane/naive/immersion/sev1] Tree branches and leaves clip directly through the red roof tiles and upper wall structure.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 54.6,67.8,58.8,71.7
- [northlane/naive/geometry/sev2] Tree branches and foliage are clipping directly through the building wall and tiled roof.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 53.9,69.6,60.9,68.8
- [northlane/naive/immersion/sev1] The rectangular roof structure sits awkwardly atop the round stone tower, leaving its corners floating in mid-air beyond the circular walls.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 63.8,73.7,63.9,72.3
- [northlane/naive/geometry/sev1] A stark rectangular ground patch sits unblended on the grass with sharp geometric edges.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 68.7,78.4,73.6,81.1
- [northlane/checklist/navigation/sev3] Back lane (closed): ABSENT — No closed lane with stacked barrels is visible anywhere in this frame.
- [gateroad/naive/occlusion/sev2] Dense, dark foliage obscures a large portion of the frame, blocking the view of the environment and potential paths ahead.
- [gateroad/naive/navigation/sev2] Extreme shadows and overall underexposure make it difficult to clearly distinguish walkable ground from surrounding hazards or obstacles.
- [gateroad/naive/occlusion/sev2] Dense, heavily shadowed foliage obscures visually readable space across the entire right side of the frame.
- [gateroad/naive/navigation/sev2] Extremely low lighting and contrast blur the boundaries between the pathway and grassy areas, making path navigation ambiguous.
- [gateroad/naive/occlusion/sev2] Dense, dark foliage obscures the right half of the screen, blocking line-of-sight into the rest of the play space.
- [gateroad/naive/navigation/sev2] Deep shadows and indistinct terrain boundaries make it difficult to determine where walkable space ends and foliage begins.
- [gateroad/checklist/occlusion/sev2] Rowan's house: OCCLUDED — Hidden behind dense foliage on the right side.
- [gatefield/naive/geometry/sev2] The perimeter of the dark paved plaza features harsh, stair-stepped edges that do not blend smoothly into the surrounding terrain.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 64.1,81.1,108.8,130.4
- [gatefield/naive/geometry/sev2] Unblended rectangular holes are abruptly cut through the floor mesh around the bench and pillar bases, revealing underlying terrain.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 66.8,82.3,118.9,127.3
- [gatefield/naive/geometry/sev2] The outer border of the paved platform forms harsh, blocky stair-steps that intersect jaggedly with the underlying grass terrain.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 64.1,80.8,108.8,130.4
- [gatefield/naive/geometry/sev2] The edges of the paved patio have jagged, stair-stepped geometry that appears blocky and unfinished.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 64.1,81.1,108.8,130.4
- [gatefield/naive/geometry/sev2] The flooring cutout around the pillar bases exposes raw terrain in an unnatural rectangular gap.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 73.3,82.3,120,127.3
- [gatefield/checklist/navigation/sev3] Whisperwood trailhead: ABSENT — No stile or marked trailhead is visible along the perimeter.

### style-bar (0)



## 2b. Aim census — did the judge point at what it named?

3 of 9 [QUALITY] verdicts REFUTED: the judge's own box held under 2% of the subject the verdict names. 3 on-subject, 0 absence-claim (census abstains), 3 unmeasurable.

- `quality:sky` — 0/2 refuted; box coverage 74.0%, 37.0%
- `quality:frame-edge-world` — 0/3 refuted; box coverage n/a
- `quality:water-read` — 3/4 refuted; box coverage 0.0%, 35.0%, 0.0%, 0.0%


## 3. Budget

64 calls, 111893 prompt + 122148 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.