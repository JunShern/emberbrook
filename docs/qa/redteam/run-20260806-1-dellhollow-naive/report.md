# Scene red-team — dellhollow — run 20260806-1-dellhollow-naive

judge `gemini:gemini-3.6-flash` (pinned) · 15 plates · naive

## 1. Calibration

_not scored in this run_


## 2. Survivors by bucket

### known (12)

- [lockhead/naive/geometry/sev2] A bright white rectangular beam or plane floats in mid-air without attached support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 53,61.1,8.4,13.4
- [lockhead/naive/geometry/sev1] A bright white untextured plank floats in mid-air beneath the wooden stairs.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 53.1,64.3,8.4,17.2
- [deep-stairs/naive/geometry/sev2] The wooden stair treads float in mid-air without visible structural supports, posts, or stringers underneath.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 32.9,47.2,18,30.3
- [boatyard/naive/geometry/sev1] The roof planks on the top-right hut overlap and float in a disjointed stack.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 0.6,8.5,17.6,25.2
- [boatyard/naive/geometry/sev1] The wooden planks forming the roof overlap at erratic angles with severe clipping and unsupported floating edges.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 0.5,8.9,17.6,24.8
- [waterfront/naive/geometry/sev2] A wooden platform step floats in mid-air with no physical supports connecting it to the surrounding cliff or stairs.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 37.1,43.7,22.1,28.7
- [waterfront/naive/navigation/sev2] A dense tangle of overlapping wooden ramps, stairs, and debris obscures which surfaces are actually walkable.
- [waterfront/naive/immersion/sev2] A wooden step platform floats in mid-air without any supporting beams or posts underneath.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 37.1,43.7,22.1,28.7
- [waterfront/naive/geometry/sev2] A wooden platform step floats unsupported in mid-air without connection to the adjacent stairs or cliff face.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 37.4,43.7,22.4,28.7
- [lockfive/naive/navigation/sev2] Extremely dark lighting leaves the left half of the environment completely unlit, obscuring navigable space and terrain context.
- [lockfive/naive/geometry/sev1] The staircase steps appear to float without visible support structures underneath.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 64.7,80.2,20.9,31.2
- [lockfive/naive/navigation/sev2] Overlapping, densely cluttered wooden platforms and posts obscure which paths are walkable or visual obstacles.

### new (66)

- [shelf-west/naive/geometry/sev2] The pulley cable extends down and penetrates directly into the stone ground without any anchor or spool structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 22.9,39.9,7.7,19.9
- [shelf-west/naive/geometry/sev2] The diagonal wooden support beams project out into mid-air beneath the upper platform without resting on any lower wall or rock face.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 17.3,32.9,3.5,11.4
- [shelf-west/naive/geometry/sev2] The diagonal wooden support beams end floating in mid-air over the open chasm rather than resting against a wall or pillar.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 17.3,30.7,2.1,11.9
- [shelf-west/naive/geometry/sev2] The wooden support beams under the upper deck extend outward and terminate floating in mid-air without connecting to any wall or support structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 17.4,24.6,2.2,12
- [shelf-west/naive/immersion/sev1] The long diagonal cable clips straight into the ground surface without any pulley base, anchor, or spool visual.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 22.9,38.4,8.6,20
- [loop-stairs/naive/immersion/sev2] A flat, untextured white mesh plane sits on the ground, appearing like an incomplete placeholder asset.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 55.6,66.9,12.1,19.4
- [loop-stairs/naive/geometry/sev2] A flat, untextured white block lies on the ground, appearing to be leftover placeholder geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 55.6,66.9,12.1,19.3
- [loop-stairs/naive/geometry/sev1] An untextured bright white plane sits flat on the terrain, appearing as unfinished blockout geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 55.7,66.9,12.1,19.5
- [loop-stairs/naive/geometry/sev1] The black wire near the foreground ground ends abruptly in mid-air without attaching to any anchor point.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 53,60.5,11,20.3
- [quay-west/naive/geometry/sev2] Thin grey rectangular planes hover mid-air without attachment or structural support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 39.6,51.7,9,17.5
- [quay-west/naive/geometry/sev2] Thin white rectangular meshes are floating mid-air without attachment to any surrounding structures.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 39.6,51.7,8.5,17.4
- [quay-west/naive/geometry/sev2] Two thin horizontal white planes are floating in mid-air with no structural support or attachment to surrounding objects.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 39.6,51.6,8.8,17.5
- [lockhead/naive/geometry/sev2] An untextured white strip clips through the walkway near the upper stairs.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 52.9,61.2,8.4,13.2
- [lockhead/naive/geometry/sev2] Untextured white placeholder geometry is exposed underneath the lower wooden staircase.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 79.3,83.5,15,19.3
- [lockhead/naive/geometry/sev1] A cardboard box clips directly through the sloped wooden roof tiles.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 72.5,76.9,16.3,21
- [cottage/naive/occlusion/sev2] An extremely dark shadow completely hides the terrain and potential pathways in the upper cave area.
- [cottage/naive/navigation/sev2] The broken, cluttered planks on the bridge make it ambiguous whether this is a traversable path or an impassable hazard.
- [cottage/naive/geometry/sev1] The stylized tree models clip directly into the steep rock face without a natural base or root connection.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 78.3,83.1,15.9,19.7
- [cottage/naive/occlusion/sev2] Extremely pitch-black shadow completely obscures the structure and potential path behind the cliff face.
- [cottage/naive/navigation/sev2] The central elevated ramp is heavily broken into fragmented planks, creating ambiguity as to whether it is a walkable path or impassable obstacle.
- [cottage/naive/immersion/sev2] A row of small orange boxes floats in mid-air across the gap without any visible ropes, platforms, or supports.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 88.9,95.8,15.8,20.5
- [cottage/naive/occlusion/sev2] Harsh, pitch-black cast shadows completely obscure the terrain and background structures, making the spatial layout unreadable.
- [cottage/naive/navigation/sev2] The central elevated ramp is heavily collapsed and fragmented, leaving it ambiguous whether it serves as a playable path or a dead-end hazard.
- [crossing/naive/geometry/sev2] A plain, untextured light-grey blockout polygon covers the lower right corner of the frame.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.7,71,12.7,18
- [crossing/naive/occlusion/sev2] Pitch-black shadow completely obscures the left half of the environment, making depth and layout impossible to read.
- [crossing/naive/occlusion/sev2] Pitch-black shadows completely cover the upper left wall and canyon, obscuring the scale and depth of the space.
- [crossing/naive/geometry/sev2] A flat turquoise rectangular plane floats in mid-air under the platform structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 100.2,109.1,30.6,38.4
- [crossing/naive/geometry/sev2] An untextured light-grey block clips into the foreground right in front of the camera.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.7,69.1,12.7,17.8
- [crossing/naive/geometry/sev2] An untextured grey and white block clips into the foreground view, appearing as unfinished or placeholder geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.7,71.2,12.7,17.9
- [crossing/naive/immersion/sev2] A flat grey rectangular plane floats in mid-air without any supporting structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 99.9,108.3,30.4,37.9
- [crossing/naive/navigation/sev2] A continuous line of stacked blocks completely obstructs the narrow sloped path, leaving it ambiguous whether it is an accessible route or a barrier.
- [weave/naive/navigation/sev2] Dense layering of identically textured wooden roofs and scaffolding makes walkable paths very difficult to distinguish from non-walkable roofs.
- [weave/naive/geometry/sev2] The cliff backdrop terminates abruptly into an untextured dark purple void along the screen edge.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 84.2,149.5,-6,26.7
- [weave/naive/geometry/sev2] A featureless dark purple void borders the cliffside, creating an unrendered backdrop that breaks visual consistency and spatial depth.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 79,149.4,-6.6,30.3
- [weave/naive/geometry/sev1] A flat white rectangular plane sits on the terrain near the walkway like placeholder or missing geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 57.8,65.2,9.7,18.9
- [weave/naive/navigation/sev2] Slanted house roofs and flat wooden walkways share nearly identical textures, shapes, and lighting, making navigable paths hard to distinguish from non-walkable scenery.
- [weave/naive/geometry/sev1] The left cliffside terminates abruptly into a flat, dark untextured void wall.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 80.9,149.3,-9.7,29.6
- [weave/naive/immersion/sev1] Wooden crates are stacked at an unnaturally steep angle directly on a sloped roof without sliding or having visible support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 57.5,68.9,14,20.9
- [deep-stairs/naive/geometry/sev2] Individual stair treads hover in mid-air along the cliffside without visible stringers or structural support underneath.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 32.6,47.4,17.9,30.5
- [boatyard/naive/immersion/sev2] The large horizontal surfaces on the foreground structure appear as completely untextured, pitch-black voids.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 7.8,18,29.9,42.1
- [boatyard/naive/geometry/sev1] A stray polygon strip clips awkwardly through the center of the circular wooden floor platform.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 16,19.8,28.4,33.4
- [boatyard/naive/geometry/sev1] The wooden framework in the background consists of loose beams floating and clipping without supporting joints.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 12.1,19.7,18.4,33.2
- [boatyard/naive/immersion/sev2] Large sections of the building's lower structure are rendered as flat pitch-black blocks lacking textures and lighting, breaking visual consistency.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 5.3,18.7,29,42.7
- [boatyard/naive/immersion/sev2] The line of colorful flags terminates floating in mid-air on the right side without any support or attachment point.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 18.1,23.1,18.5,24.2
- [boatyard/naive/geometry/sev2] The lower portion of the building consists of completely flat, unshaded black geometry that lacks lighting and texture detail.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 5.3,18.8,29.6,42.7
- [waterfront/naive/geometry/sev2] The rock face model on the right is a single-sided paper-thin surface, leaving open space visible underneath its edges.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 24.9,44.3,28,35.4
- [waterfront/naive/geometry/sev3] The cliff surface is a single-sided paper-thin polygon sheet with no backface or volumetric geometry beneath it.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 24.9,44.5,28.1,35.4
- [waterfront/naive/navigation/sev2] Tightly packed overlapping wooden beams, platforms, and stairs create visual clutter that makes it difficult to parse navigable paths.
- [waterfront/naive/geometry/sev3] The cliff surface ends abruptly as a paper-thin single-sided mesh, exposing a hollow gap underneath.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 25.6,44.5,27.9,35.4
- [waterfront/naive/navigation/sev2] Extremely cluttered and overlapping wooden staircases, planks, and debris make walkable pathways visually ambiguous.
- [fishdock/naive/navigation/sev2] Extremely dark pitch-black shadows obscure the ground and stilt structure, making it impossible to read vertical depth or determine if there are walkable paths below.
- [fishdock/naive/geometry/sev1] A thin diagonal beam spans from the top right building to the lower railing without visible structural connections or anchors at its ends.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 40.1,47.3,17.1,30
- [fishdock/naive/immersion/sev1] A wooden boat is perched high above dry ground on support pillars without any water or clear mechanism for launching.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 55.6,64,34.7,40.6
- [fishdock/naive/navigation/sev2] Multiple overlapping wooden staircases and broken platforms visually clutter the cliff face, making walkable routes ambiguous.
- [lockfive/naive/geometry/sev2] The wooden stairs and support beams clip directly into adjacent platform edges and structures, creating disjointed geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 65.8,97.8,21.1,32.4
- [lockfive/naive/immersion/sev1] The green fabric sheets along the upper railing are completely flat, rigid geometry that clip through the wooden framework.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 60.3,85.4,17.6,28.5
- [lockfive/naive/navigation/sev2] Dense, visually cluttered wooden beams and overlapping platforms make navigable paths hard to distinguish from background structure.
- [lockfive/naive/immersion/sev2] Extremely dark shadow on the left completely hides geometry and creates an unnatural pitch-black void.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 81.9,152,1.1,50.5
- [lockfive/naive/occlusion/sev2] Extreme darkness on the left side conceals spatial boundaries and depth, making the environment hard to parse.
- [north-landing/naive/immersion/sev2] A flat brown panel floats unsupported in mid-air with blocks sitting on it.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 88,98.4,31.6,44.9
- [north-landing/naive/geometry/sev1] A flat green rectangular mesh is laying loosely on the ground without thickness or blending.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 97.2,105.6,31.2,36.9
- [north-landing/naive/geometry/sev2] A completely flat, unshaded brown plane with loose gray blocks floats in mid-air without structural support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 87.9,98.2,31.6,44.9
- [north-landing/naive/immersion/sev1] A flat green rectangular texture strip is pasted onto the ground terrain without any blending or depth.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 97.1,105.6,31.2,36.9
- [north-landing/naive/navigation/sev2] The narrow elevated walkway disappears into a dense cluster of wooden beams, making the route forward ambiguous.
- [north-landing/naive/geometry/sev3] An untextured flat orange rectangle holding primitive grey blocks floats in mid-air without supports or material, appearing as unfinished placeholder geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 93.3,108.5,29.2,36
- [north-landing/naive/navigation/sev2] The main wooden walkway leads directly into a dense mesh of structural beams, making it ambiguous where the player can actually walk forward.

### style-bar (0)



## 3. Budget

60 calls, 90131 prompt + 97202 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.