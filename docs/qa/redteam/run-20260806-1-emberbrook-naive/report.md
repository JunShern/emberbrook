# Scene red-team — emberbrook — run 20260806-1-emberbrook-naive

judge `gemini:gemini-3.6-flash` (pinned) · 11 plates · naive

## 1. Calibration

_not scored in this run_


## 2. Survivors by bucket

### known (31)

- [woodroad/naive/geometry/sev2] The perimeter of the circular stone pad has blocky, stair-stepped edges that clip awkwardly into the surrounding terrain.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 43.9,59.4,-34.3,-21.8
- [woodroad/naive/geometry/sev2] The perimeter of the circular paved area consists of jagged, stair-stepped blocky steps that look like unrefined grid geometry. _(also on gatefield)_
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 44,59.3,-34.5,-21.6
- [waystone/naive/occlusion/sev1] Dense, pitch-black foliage obscures the right portion of the frame, hiding the path's continuation and surrounding terrain.
- [waystone/naive/immersion/sev1] The underside of the tree canopy above is brightly illuminated despite the light fixture having an opaque top cover.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 52.3,60,-9.2,-1.5
- [waystone/naive/geometry/sev1] The stone path slabs end abruptly with exposed, floating edges that do not connect cleanly with the surrounding ground terrain.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 53.8,60.4,-13.8,-4.2
- [waystone/naive/navigation/sev2] Dense foliage and shadow completely block the view of the environment, making it ambiguous whether the path continues or ends.
- [arch/naive/geometry/sev2] The path geometry clips flat and unnaturally into the ground plane with sharp, unintegrated edges.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 52.3,74.2,0.8,64.4
- [orchard/naive/occlusion/sev2] The pitch-black shadow cast by the roof completely obscures the building's base, entrances, and ground details underneath.
- [orchard/naive/geometry/sev2] A bright green untextured object clips strangely into the terrain and foliage.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 47.4,56.1,25.5,34.8
- [orchard/naive/occlusion/sev2] An extremely dark roof shadow completely obscures the ground and terrain details, making it impossible to see objects or paths in that area.
- [orchard/naive/occlusion/sev2] Dense foreground foliage blocks a large portion of the right side of the screen, obscuring the surrounding space and potential navigation routes.
- [therise/naive/occlusion/sev2] A dense foreground bush occupies a major section of the camera frame, blocking sightlines to the surrounding town layout.
- [therise/naive/navigation/sev2] Deep shadows and dense foliage obscure the walkable terrain, making it ambiguous which way the player is intended to progress.
- [therise/naive/occlusion/sev2] Extremely dense and dark foliage dominates the left side of the frame, severely obscuring paths and environment layout.
- [therise/naive/geometry/sev2] The pathway mesh clips awkwardly through the terrain, leaving floating edges and untextured vertical gaps.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 55.3,61.7,14.3,21.3
- [therise/naive/occlusion/sev1] A large foreground bush severely blocks the player's view of the ground and playable path directly behind it.
- [square/naive/geometry/sev2] Several rectangular holes are cut into the ground plane mesh near the well, showing black untextured gaps.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 54.7,60.2,42.3,48.7
- [square/naive/immersion/sev2] A bright, untextured white block sits inside the central pit, appearing as a placeholder light object rather than a finished asset.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 60.7,66.8,39.7,45.7
- [pondlane/naive/geometry/sev2] Untextured green blockout slabs on the path appear to be unfinished developer placeholder geometry.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 71,80.8,53.9,64.7
- [pondlane/naive/geometry/sev2] The cyan rectangular steps look like untextured placeholder geometry that does not blend into the terrain.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 70.6,81.1,52.9,64.8
- [pondlane/naive/navigation/sev2] Dense trees and dark foliage obscure the middle ground, leaving no clear visible path or direction for movement.
- [pondlane/naive/geometry/sev2] The blocky steps on the lower left appear to be untextured greybox geometry.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 70.6,81.1,52.9,64.8
- [pondlane/naive/occlusion/sev2] The dense central foliage hides the ground and paths underneath, making it unclear where the player can walk.
- [homerow/naive/geometry/sev2] A large untextured, flat box structure is attached to the upper side of the building.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 49.1,55.5,55.2,60.7
- [homerow/naive/immersion/sev1] A plain brown rectangular face on the upper wall appears untextured, resembling placeholder geometry.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 49.2,55.2,55.1,60.7
- [northlane/naive/immersion/sev1] A flat orange plane on the upper building structure looks untextured compared to the rest of the scene.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 50,59.3,55.7,64.2
- [gateroad/naive/occlusion/sev2] Dense foreground trees and foliage completely obscure the right side of the view, blocking visibility of the surrounding terrain and potential hazards.
- [gateroad/naive/occlusion/sev2] Dense dark foliage and pitch-black shadows obscure the right half of the viewport, blocking line of sight and hiding potential paths.
- [gateroad/naive/immersion/sev2] The lighter ground patch has abrupt edges with no texture blending or ambient shading, appearing like a flat cutout over the grass.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 62.7,80.1,80.9,102.4
- [gateroad/naive/geometry/sev1] The grey rectangular block lacks grounding shadows and proper contact ambient occlusion with the dark grass beneath it.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 62.9,69.5,68.3,76.6
- [gateroad/naive/occlusion/sev2] Extremely dense foreground foliage and deep shadows completely block visibility of the environment and any potential paths on the right side of the screen.

### new (33)

- [woodroad/naive/geometry/sev1] The straight path plane clips directly into the terrain with razor-sharp, unblended edges.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 49.8,60.2,-25.4,-2.7
- [woodroad/naive/geometry/sev2] The perimeter of the circular paved area has unnatural, pixelated stair-step edges where it intersects the grass.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 44.1,59.3,-34.3,-21.2
- [waystone/naive/immersion/sev2] The pedestal is brightly lit in cool white light from an opposing angle, inconsistent with the warm orange light emitted by the adjacent lamp post.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 53.2,58.3,-14.2,-7.4
- [waystone/naive/navigation/sev2] The path vanishes into complete darkness beneath the tree canopy, making it unclear if the way forward is walkable.
- [arch/naive/geometry/sev2] A dark flat geometric plane clips cleanly into the terrain path, creating an unnatural jagged tear in the ground geometry.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 53.4,62.4,6.8,21.3
- [arch/naive/geometry/sev2] Dark geometric path polygons clip abruptly into the ground terrain with sharp edges and no blending.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 46.6,66,5.2,22.5
- [orchard/naive/occlusion/sev1] Dense foreground trees obstruct the view of the terrain and potential navigation paths on the right side of the screen.
- [orchard/naive/occlusion/sev2] Pitch-black shadow completely obscures the ground and structure below the roof, concealing paths and potential obstacles.
- [orchard/naive/immersion/sev1] The active light source casts a sharp, dark shadow outward without illuminating its immediate surroundings.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 36.1,44.4,18.1,26
- [orchard/naive/immersion/sev1] The small bushes are placed in an unnaturally rigid circular arc across the clearing, breaking environmental believability.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 27.3,48.3,11.7,27.2
- [therise/naive/geometry/sev2] The paved path geometry features sharp, unblended polygonal edges clipping abruptly into the surrounding terrain mesh.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 55.3,61.6,14.3,21.3
- [therise/naive/geometry/sev2] The ground path mesh segments are disjointed and misaligned, creating visible seams and clipping edges on the terrain.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 55.3,61.7,14.5,21.5
- [square/naive/geometry/sev2] Black square holes and grid-shaped missing patches are visible in the ground terrain mesh.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 54.7,68.1,42.2,57.5
- [square/naive/geometry/sev2] The ground terrain mesh terminates in a jagged, blocky stepped edge with missing geometry exposing black void underneath.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 64.7,74.4,53.3,59.5
- [square/naive/occlusion/sev2] A massive foreground roof severely occludes the ground and play area in the lower right section of the screen.
- [pondlane/naive/geometry/sev1] The wooden roof panels on the market stalls visibly clip through one another at harsh angles.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 69.3,82.2,38.2,48.5
- [pondlane/naive/immersion/sev2] Tree trunks in the background cut off abruptly against the sky without foliage tops or proper bases.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 113,116,76.9,79.9
- [homerow/naive/immersion/sev2] A hard-edged, perfectly square black shadow box appears unexpectedly on the walkway path.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 33.4,39.4,47,53.2
- [homerow/naive/geometry/sev2] A massive wooden wheel structure clips unnaturally into the building's stone wall.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 50.3,56.7,55.1,61.2
- [homerow/naive/immersion/sev2] A pitch-black rectangular plane sits flat on the walkway, appearing as a broken shadow artifact.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 33.4,39.4,47,53.2
- [homerow/naive/geometry/sev2] An elevated section of the building overhangs and floats in mid-air without structural support underneath.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 42.2,50.9,57.5,65.5
- [homerow/naive/geometry/sev1] A wooden beam clips straight through the paved walkway surface.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 45.2,50.8,52.5,57
- [homerow/naive/geometry/sev2] A pitch-black rectangular block artifact is embedded on the path, suggesting missing lighting or broken shadow geometry.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 33.4,39.4,47,53.2
- [homerow/naive/geometry/sev2] The massive wooden wheel clips directly into the ground terrain without visible support or housing.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 50.3,56.7,55.1,61.2
- [northlane/naive/immersion/sev1] Modern street lamp posts conflict visually with the rustic, medieval cottage setting.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 64.4,70.3,69.5,74
- [northlane/naive/geometry/sev1] The chimney clips directly through the roof tiles without flashing or structural framing.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 61.8,68.4,64.6,69.1
- [northlane/naive/geometry/sev1] The square roof section clips directly into the main building wall without a proper architectural transition.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 64.7,73.7,64,72.3
- [northlane/naive/geometry/sev1] The paved ground section cuts sharply into the surrounding terrain with a harsh, unblended rectangular edge.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 60.1,67.7,53.8,62.2
- [gateroad/naive/navigation/sev2] The cleared path curves directly into deep darkness beneath the trees, making it ambiguous whether the way forward continues or ends.
- [gateroad/naive/navigation/sev2] Severe underexposure and heavy shadows make it difficult to distinguish readable pathways from impassable ground terrain.
- [gatefield/naive/geometry/sev2] The edge of the paved courtyard floor forms a jagged, blocky step pattern rather than a clean border or natural blending into the terrain.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 65.6,81.1,108.8,124.8
- [gatefield/naive/geometry/sev2] A square cutout in the paved floor exposes lower ground around the wooden structure, creating raw floating floor edges.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 66.4,73.8,118.6,125.7
- [gatefield/naive/geometry/sev2] The edge of the paved courtyard mesh has rough, jagged stair-step cuts where it meets the grass terrain.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 64.2,81.2,108.7,122.8

### style-bar (0)



## 3. Budget

44 calls, 66216 prompt + 70694 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.