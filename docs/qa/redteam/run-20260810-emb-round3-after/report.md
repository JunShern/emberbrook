# Scene red-team — emberbrook — run 20260810-emb-round3-after

judge `gemini:gemini-3.6-flash` (pinned) · 11 plates · naive + checklist

## 1. Calibration

_not scored in this run_


## 2. Survivors by bucket

### known (0)


### new (80)

- [woodroad/naive/geometry/sev2] The path surface is a flat ribbon with harsh, sharp polygonal edges that clip unnaturally through the terrain.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 50.5,59.1,-25.2,-10.1
- [woodroad/naive/navigation/sev2] The dark circular zone lacks surface details or reflections, making it ambiguous whether it is a pit, a body of water, or navigable ground.
- [woodroad/naive/geometry/sev1] Low-polygon triangulation seams and jagged facet lines are clearly visible where the path connects to the circle.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 50.3,58.6,-27.3,-21.4
- [woodroad/naive/geometry/sev1] The path surface is a flat mesh strip with sharp, hard-edged polygon boundaries cutting through the ground terrain without blending.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 50.3,58.9,-25.6,-9.8
- [woodroad/naive/immersion/sev1] The rocks outlining the circular perimeter appear repetitively placed and float slightly or clip unnaturally into the ground surface.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 43.6,59.8,-35,-20.7
- [woodroad/naive/geometry/sev1] The dirt path and circular pad have sharp, unblended polygonal edges where they intersect the grass terrain.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 43.9,58.9,-34.2,-21.3
- [woodroad/checklist/navigation/sev3] the way out of this area on foot towards waystone: ABSENT — There is no path extending past the waystone out of the frame.
- [woodroad/checklist/navigation/sev3] a door / entrance you can go through ("Leave Emberbrook"): ABSENT — No door or entrance is present in this frame.
- [woodroad/checklist/immersion/sev3] The world at the frame edges: FAILING — The terrain extending toward the top and left edges becomes an featureless flat plane with shadow projections rather than fully modeled world geometry. _(also on square, pondlane)_
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 31.6,56.8,-19.4,4.5
- [waystone/naive/geometry/sev1] A sharp, unnaturally straight polygonal seam cuts through the ground texture along the path edge.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 54,60,-13.8,-5.5
- [waystone/naive/geometry/sev1] The path geometry intersects the surrounding terrain in a hard, unblended straight line edge.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 50.2,59.2,-21.6,-14.4
- [waystone/naive/geometry/sev1] The path polygon has sharp, unblended straight edges that cut directly through the terrain geometry without transition.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 47.6,61,-21.6,-4.8
- [waystone/naive/navigation/sev1] The stone monument completely occupies the narrow path, making it ambiguous whether the player can walk past it.
- [waystone/checklist/occlusion/sev2] the way out of this area on foot towards arch: OCCLUDED — The exit path towards the arch is occluded by low-hanging tree branches and deep shadows.
- [arch/naive/geometry/sev2] The terrain mesh along the path has sharp, unnatural polygonal seams and geometry slicing into the walkway surface.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 53.4,62.5,4.8,24.1
- [arch/naive/geometry/sev2] Sharp polygonal black cuts and misaligned mesh edges create broken shadow and ground geometry.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 52.4,60.7,5.5,23.4
- [arch/naive/geometry/sev2] The path mesh features broken, jagged terrain polygons intersecting awkwardly and leaving sharp gaps across the walkway.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 52.1,61,1.8,23.4
- [arch/checklist/navigation/sev2] the route between Village Arch and Orchard rows: VISIBLE-BUT-ILLEGIBLE — It merges into the surrounding terrain without reading as a distinct branching path towards orchard rows.
- [arch/checklist/navigation/sev3] the way out of this area on foot towards orchard: ABSENT — There is no path exiting the frame toward an orchard. _(also on orchard)_
- [arch/checklist/navigation/sev3] the way out of this area on foot towards therise: ABSENT — No exit path heading toward the rise is visible in this shot.
- [arch/checklist/navigation/sev2] Item Shop: VISIBLE-BUT-ILLEGIBLE — It appears as a plain residential house with a lit window rather than a general store.
- [arch/checklist/navigation/sev2] Festival dais: VISIBLE-BUT-ILLEGIBLE — The distant lit structures in the square are too small and indistinct to be clearly identified as a festival dais.
- [orchard/naive/immersion/sev2] The light patch on the ground terminates in a sharp, straight polygon edge, creating an unnatural visual boundary for the lamp's illumination.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 36.7,49.5,21,33.3
- [orchard/naive/immersion/sev1] The illuminated area on the ground creates an unnatural, sharp polygonal edge of light and shadow.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 36.7,49.5,21,33.1
- [orchard/naive/immersion/sev2] The light and shadow cast on the ground form unnaturally sharp geometric polygon edges.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 36.7,49.8,21.2,33.3
- [orchard/checklist/navigation/sev3] Orchard rows: ABSENT — No rows of fruit trees, ladders, or harvest baskets are present in this scene.
- [orchard/checklist/navigation/sev3] the route between Village Arch and Orchard rows: ABSENT — No arch or connecting path to orchard rows exists in the frame.
- [orchard/checklist/navigation/sev3] the route between Orchard rows and Cider press barn: ABSENT — There is no path connecting orchard rows to the cider press barn.
- [therise/naive/geometry/sev2] Disjointed grey polygon slabs clip into the dirt terrain with harsh, unblended edges.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 55.3,61.6,14.3,21.4
- [therise/naive/geometry/sev2] A flat grey mesh plane clips unnaturally into the sloped ground terrain.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 48.6,56.1,12.8,18.4
- [therise/naive/geometry/sev2] Sharp, unblended polygon edges of the ground panels stick out unnaturally above the terrain texture.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 55.1,61.6,14.4,21.7
- [therise/naive/geometry/sev1] A jagged, unblended polygon mesh corner clips visibly across the bottom-left corner of the view.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 48.8,56.1,12.8,17.8
- [therise/naive/geometry/sev2] Dark flat polygon slabs clip awkwardly through the ground plane, creating sharp artificial edges.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 55.3,61.6,14.3,21.4
- [therise/checklist/occlusion/sev2] Cider press barn: OCCLUDED — Hidden behind thick foreground foliage on the left.
- [therise/checklist/occlusion/sev2] The Heartlight: OCCLUDED — Obscured behind plaza wooden structures and foliage.
- [therise/checklist/immersion/sev2] The sky: WEAK — WEAK — Small patch of sky lacks rich atmospheric gradients.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 57,60,61.3,64.3
- [square/naive/occlusion/sev2] The large roof in the foreground completely blocks the view of the ground and play area behind it.
- [square/naive/occlusion/sev2] Dense tree foliage in the foreground obscures a large section of the ground and potential pathways.
- [square/naive/occlusion/sev2] A massive foreground roof severely blocks the player's view of the ground and potential paths in the bottom-right area.
- [square/naive/occlusion/sev1] Dense foreground trees block vision along the bottom-left edge of the scene.
- [square/naive/occlusion/sev2] A large roof in the immediate bottom-right foreground heavily blocks the view of the playable area and pathing below.
- [square/naive/occlusion/sev1] Dense foreground foliage obstructs the ground level and left side of the path.
- [square/checklist/navigation/sev2] a door / entrance you can go through ("Enter Item Shop"): VISIBLE-BUT-ILLEGIBLE — Entrance is heavily shadowed and hard to distinguish.
- [square/checklist/navigation/sev2] a door / entrance you can go through ("Enter The Ember Hearth"): VISIBLE-BUT-ILLEGIBLE — Doorway area blends into ambient wall shadows.
- [square/checklist/navigation/sev2] a door / entrance you can go through ("Enter Poppy's bakery"): VISIBLE-BUT-ILLEGIBLE — Door structure hidden under dark roof overhang.
- [square/checklist/immersion/sev2] The water surface: ABSENT — No water bodies or surfaces appear in this shot. _(also on pondlane)_
- [pondlane/naive/geometry/sev2] The terrain mesh contains severe geometric tears and black gaps revealing missing polygons beneath the ground surface.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 69.6,92.2,39.8,51.9
- [pondlane/naive/geometry/sev2] The green water channel cuts directly through the ground terrain with raw, unmodeled mesh edges and no riverbank geometry.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 86.4,144.5,34.8,46.1
- [pondlane/naive/immersion/sev1] The wooden canopy panels clip heavily into one another without visible support posts under the roof sections.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 70.3,82.2,39.1,47.8
- [pondlane/naive/geometry/sev2] There are visible black triangular holes and missing polygons torn throughout the ground mesh.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 72,87.7,35.4,52.2
- [pondlane/naive/geometry/sev1] The flat water plane cuts sharply through the terrain mesh with unblended geometry edges.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 70.6,78.8,50.3,62.5
- [pondlane/naive/geometry/sev3] The ground mesh has severe visible polygon tears and black holes revealing empty void beneath the walkable area.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 72,87.7,35.4,54.7
- [pondlane/naive/geometry/sev2] The water body is a flat, untextured green plane that harsh-clips into the surrounding terrain without proper shores.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 69.3,76.4,49.5,62.3
- [pondlane/naive/immersion/sev2] The wooden roof and awning planks float, clip awkwardly, and lack logical structural supports.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 69.5,82.6,37.9,48.5
- [pondlane/checklist/occlusion/sev2] Brook mouth: OCCLUDED — Hidden behind dense trees and bushes along the watercourse.
- [pondlane/checklist/navigation/sev3] Weir & sluice: ABSENT — Not visible within the current camera frame.
- [pondlane/checklist/navigation/sev2] Finn's smokehouse: VISIBLE-BUT-ILLEGIBLE — Blends into the surrounding structures without clear identifying smokehouse traits.
- [pondlane/checklist/occlusion/sev2] Pip's den: OCCLUDED — Concealed beneath the embankment structure and out of view.
- [homerow/naive/occlusion/sev2] The large pine tree in the foreground severely blocks the view of the building, path, and surrounding space in the bottom-left corner.
- [homerow/naive/geometry/sev2] The oversized wooden wheel clips directly into the stone wall and terrain without any visible axle or mechanical support.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 50.5,56.6,55.2,61.2
- [homerow/naive/occlusion/sev2] The large foreground pine tree heavily obscures the path and corner building, preventing clear visibility for navigation.
- [homerow/naive/immersion/sev1] The modern minimalist square post light visual style clashes with the rustic medieval environment.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 43.6,48.5,46.5,57.7
- [homerow/naive/geometry/sev1] The large wooden disc is clipped directly into the ground without visible axle mountings or functional support.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 50.6,56.7,55.1,61.2
- [homerow/naive/occlusion/sev2] A dense foreground tree obscures a significant portion of the lower-left playable space and building.
- [homerow/naive/immersion/sev1] A massive sliced tree trunk stands upright against the house wall without visible support, clipping into the ground.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 50.5,56.7,55.2,61.2
- [homerow/checklist/navigation/sev3] Upper lane (closed): ABSENT — No upper lane closed by a festival cart is visible in this frame.
- [northlane/naive/immersion/sev2] Modern square post lights appear incongruous in an ancient medieval village setting, breaking thematic immersion.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 64.4,70.3,69.6,73.9
- [northlane/naive/geometry/sev1] A sharp, unblended grey rectangular polygon sits flat on the grass without edge transitions or proper ground integration.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 68.8,78.4,73.6,81
- [northlane/naive/geometry/sev2] An untextured flat rectangular slab sits unnaturally in the grass without proper blending or surface detail.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 69.6,76.2,72.7,86
- [northlane/checklist/navigation/sev3] Back lane (closed): ABSENT — No back lane blocked by stacked barrels is visible anywhere in this frame.
- [northlane/checklist/navigation/sev3] the route between Festival Square and Tithe barn: ABSENT — The walled north lane route is not present in this frame.
- [gateroad/naive/navigation/sev2] Pitch-black lighting across the dense trees obscures pathways and terrain contours, making spatial navigation difficult.
- [gateroad/naive/geometry/sev1] The transition between the dirt ground texture and the surrounding grass features an unnaturally sharp geometric boundary.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 44.2,67.7,-53.8,94.9
- [gateroad/naive/occlusion/sev2] Dense, dark foliage and foreground tree trunks obscure more than half the screen, hiding the layout of the space.
- [gateroad/naive/navigation/sev2] The open path terminates abruptly in deep shadow without clear visual indicators of where the player can continue walking.
- [gateroad/naive/occlusion/sev2] Extremely dark shadows and dense tree canopy hide the right side of the space, making it impossible to tell if terrain or paths continue behind them.
- [gateroad/naive/immersion/sev1] The flat dirt patch meets the surrounding grass with a sharp, unblended edge that looks unintegrated with the rest of the terrain.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 62.5,80.2,80.7,102.3
- [gatefield/naive/navigation/sev2] The extreme darkness and dense foliage obscure terrain boundaries, making it hard to discern where walkable paths end.
- [gatefield/naive/exit/sev2] The wooden door sits on a high wall ledge without clear stairs or a walkway leading up to it, making its status as an exit ambiguous.
- [gatefield/checklist/navigation/sev3] the route between Sigil Gate court and Whisperwood trailhead: ABSENT — No distinct path markings link the court center to the stile prop.

### style-bar (0)



## 2b. Aim census — did the judge point at what it named?

2 of 8 [QUALITY] verdicts REFUTED: the judge's own box held under 2% of the subject the verdict names. 2 on-subject, 0 absence-claim (census abstains), 4 unmeasurable.

- `quality:frame-edge-world` — 0/3 refuted; box coverage n/a
- `quality:sky` — 1/2 refuted; box coverage 50.5%, 1.0%
- `quality:water-read` — 1/3 refuted; box coverage 2.7%, 0.0%


## 3. Budget

65 calls, 113346 prompt + 122762 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.