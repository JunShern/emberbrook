# Scene red-team — dellhollow — run r12-before

judge `gemini:gemini-3.6-flash` (pinned) · 6 plates · naive

## 1. Calibration

_not scored in this run_


## 2. Survivors by bucket

### known (14)

- [cottage/naive/navigation/sev2] The chaotic overlap of broken ramps, sharp angled planks, and gaps makes it ambiguous where walkable paths end and fall hazards begin.
- [cottage/naive/geometry/sev2] Individual wooden planks on the broken ramp float in mid-air and clip through each other without visible fasteners or structural supports.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 86.6,95.6,17.7,24.3
- [cottage/naive/geometry/sev2] The collapsed wooden ramp consists of floating and clipping planks with disjointed angles, making it ambiguous whether it functions as a walkable path or debris.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 86.6,96,16.3,24.3
- [cottage/naive/geometry/sev2] The broken planks on the ramp clip awkwardly into support beams and float at irregular angles, making walkable surfaces ambiguous.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 84.3,92.5,16.3,22.2
- [crossing/naive/immersion/sev1] Broken wooden planks float in the air without visible support beams beneath them.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 73.9,80.6,12.7,18.5
- [crossing/naive/geometry/sev2] The wooden steps and platform contain floating, disconnected planks and disjointed support beams that lack proper structural anchoring.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 71,83.5,20.3,38
- [crossing/naive/geometry/sev1] The wooden planks on the lower walkway section feature disconnected and awkwardly clipping structural beams.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 71.2,85.2,21.6,37.9
- [crossing/naive/geometry/sev1] Broken wooden planks tilt and float disjointed without visible structural support underneath.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 71,87.3,21.6,38
- [crossing/naive/geometry/sev1] Wooden planks and stair segments overlap and float without clear structural joins or supports.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 70.7,93.3,11,17.8
- [waterfront/naive/geometry/sev2] A wooden plank platform floats in mid-air over the water gap without any visible supporting posts or framework.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 37.4,43.7,22.3,28.7
- [waterfront/naive/immersion/sev2] A wooden plank platform hovers in mid-air over the gap without any visible support posts or attachment.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 37.4,43.7,22.3,28.7
- [waterfront/naive/geometry/sev2] A wooden platform segment floats unnaturally in mid-air above the water without any visual support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 37.4,43.7,22.4,28.7
- [waterfront/naive/immersion/sev1] The upper staircase steps float independently without continuous stringers or clear underlying structural support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 24.7,44.7,18.2,30
- [north-landing/naive/immersion/sev1] The rectangular stepping stones float unsupported on top of the water without sub-surface geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 86.8,95.4,33,42.3

### new (117)

- [cottage/naive/navigation/sev2] The broken, layered wooden ramps visually collide and overlap, making it unclear which surfaces are walkable paths and which are dynamic debris or dead ends.
- [cottage/naive/occlusion/sev2] Deep, pitch-black shadows beneath the upper wooden shelter completely obscure whether there is an playable opening or wall inside.
- [cottage/naive/navigation/sev2] The fractured, overlapping green ramps and broken wooden planks make it difficult to distinguish traversable paths from non-interactive visual debris.
- [cottage/naive/geometry/sev2] The ladder structure floats diagonally without visible attachment points or physical anchors to the cliff or platform.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 78.2,85.9,15.3,23.4
- [cottage/naive/occlusion/sev1] Extremely dark shadows completely obscure the space and geometry underneath the bridge structure.
- [cottage/naive/navigation/sev2] Harsh cliff shadows completely black out the central wooden structure and walkways, making navigable paths impossible to discern.
- [cottage/naive/geometry/sev2] The long ladder structure clips directly into uneven rock faces without visible support mounts or logical grounding.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 79.3,85.8,15.4,23.5
- [cottage/naive/geometry/sev2] The metal ladder structure floats unanchored in mid-air along the cliff side without attachment brackets or base support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 76,92,16.7,22.4
- [cottage/naive/occlusion/sev2] Harsh, pitch-black shadows completely hide the structure's interior and any potential doorway or path continuing inward.
- [cottage/naive/navigation/sev2] The broken wooden ramp overlaps chaotically, making it ambiguous whether this is a walkable path or an impassable obstacle.
- [cottage/naive/geometry/sev2] The wooden ladder clips directly into the solid rock face near its base.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 80.4,85.4,16.7,23.4
- [cottage/naive/immersion/sev1] Multiple support beams and floor planks clip through each other without structural joins.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 83.7,91.8,16.3,23
- [cottage/naive/occlusion/sev2] Harsh cast shadows obscure the space beneath the roof, making it impossible to see if there is an open passage or entrance.
- [cottage/naive/immersion/sev1] The ladder lacks wall mounts and clips directly into the jagged rock face at its base.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 78.2,85.9,15.5,23.4
- [cottage/naive/navigation/sev2] The overlapping, broken wooden planks and scaffolding form a chaotic visual cluster that makes it hard to distinguish walkable paths from non-walkable debris.
- [cottage/naive/occlusion/sev2] Deep harsh shadows completely obscure the structure and ground beneath the upper bridge, hiding potential paths or openings.
- [cottage/naive/geometry/sev1] The long ladder clips directly through the platform edge without a cutout or mounting structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 78.2,85.7,14.9,23.4
- [cottage/naive/navigation/sev2] The central wooden ramp is fractured into overlapping, jagged planks, making it unclear whether this is a traversable path or impassable scenery.
- [cottage/naive/geometry/sev2] The long ladder connects directly into the solid underside of the wooden walkway without an opening or hatch for access.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 78.2,85.9,15.5,23.4
- [cottage/naive/occlusion/sev2] Deep harsh shadows obscuring the central area make it impossible to tell if the path continues into a cave, onto a lower platform, or terminates.
- [crossing/naive/geometry/sev2] An untextured grey polygon is clipping through the terrain in the bottom right corner.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,68.1,13.7,17.6
- [crossing/naive/occlusion/sev2] Extremely dark cast shadows obscure the walkable surface and path around the central structure.
- [crossing/naive/geometry/sev2] A sharp, flat grey polygon clips through the wooden ramp in the bottom right corner.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,69.7,12.7,17.2
- [crossing/naive/occlusion/sev2] Large foreground roof structures obscure the walkway below, making it hard to see the path underneath.
- [crossing/naive/occlusion/sev2] The large roof structure and dense cast shadows heavily obscure the wooden walkway beneath, making navigable paths hard to discern.
- [crossing/naive/geometry/sev2] A raw gray wedge of mesh clips into the camera view in the bottom right corner.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,69.8,12.7,17.2
- [crossing/naive/navigation/sev2] Heavy visual noise and deep shadows make it hard to tell walkable paths apart from roof geometry.
- [crossing/naive/occlusion/sev1] Harsh pitch-black shadows from the foreground roof obscure the floor space and potential paths beneath.
- [crossing/naive/navigation/sev2] Harsh pitch-black shadows and overlapping roofs obscure the path below, making player navigation difficult to discern.
- [crossing/naive/geometry/sev2] Untextured gray polygon faces are visible along the bottom-right corner of the viewport.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,69.8,12.7,17.2
- [crossing/naive/navigation/sev2] Harsh, pitch-black directional shadows obscure elevation changes and make it difficult to identify walkable paths.
- [crossing/naive/geometry/sev2] An untextured gray mesh wedge clips directly through the wooden walkway surface.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,70.2,12.7,17.2
- [crossing/naive/occlusion/sev2] The large roof and intense cast shadows completely block line of sight to the ground-level walkways beneath them.
- [crossing/naive/navigation/sev2] The fragmented, broken wooden walkways make it ambiguous whether the platform is navigable or a fall hazard.
- [crossing/naive/geometry/sev2] Grey untextured mesh geometry clips awkwardly through the ground plane at the bottom right corner.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,69.1,12.7,17.3
- [crossing/naive/immersion/sev1] The damaged wooden planks hover in mid-air over the water without underlying support beams.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 69.5,87.6,21.6,36.3
- [weave/naive/navigation/sev2] Walkable paths, roof slopes, and decorative scaffolding blend together into a uniform brown material, making walkable routes indistinguishable from impassable roofs.
- [weave/naive/geometry/sev2] The elevated wooden boardwalk clips directly through the green-shingled roof below without structural framing or cutouts.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 48.3,61.3,8.6,21.7
- [weave/naive/geometry/sev1] The orange rock formation clips abruptly into the grey cliff face without a natural transition or blending.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 82.9,132.1,-1.8,18.2
- [weave/naive/navigation/sev2] Uniform brown and olive texturing across roofs, walkways, and rock faces creates heavy visual noise, making playable paths and ramps difficult to distinguish.
- [weave/naive/immersion/sev2] The cliff geometry ends in a sharp, unrendered vertical boundary exposing the empty background void.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 102,147.8,13,32.5
- [weave/naive/navigation/sev2] Identical wood textures and dense overlapping structures make it difficult to distinguish playable walkways from inaccessible rooftops.
- [weave/naive/geometry/sev2] The terrain abruptly terminates into an empty black void at the edge of the screen, exposing the map boundary.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 86.1,147.4,18.2,34.3
- [weave/naive/occlusion/sev1] Overlapping ramps and stilt structures heavily shadow and obscure any potential ground-level pathways below.
- [weave/naive/navigation/sev2] Walkways, rooftops, and elevated platforms share identical textures and lighting, making walkable paths visually indistinguishable from non-navigable roofs.
- [weave/naive/geometry/sev1] Stilts supporting upper wooden platforms clip directly into lower foliage and ground terrain without clear structural joints or foundations.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 56.3,67.8,21.8,32.6
- [weave/naive/geometry/sev1] A wooden step structure clips directly through the green roof surface without support framing.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 55.8,64.6,17.5,21.6
- [weave/naive/immersion/sev1] The line holding the colorful flags terminates in mid-air on the right without attaching to a post or wall.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 43,52,16.7,26.9
- [weave/naive/navigation/sev2] Densely layered scaffolding, ramps, and roofs overlap with identical textures and shading, making the intended path hard to discern.
- [weave/naive/navigation/sev2] The dense stacking of identical wooden rooftops, platforms, and railings makes it difficult to visually separate walkable paths from background scenery.
- [weave/naive/geometry/sev2] The water plane and environment geometry end abruptly at the left edge of the screen, revealing the empty background void.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 103.9,147.8,19,32.8
- [weave/naive/immersion/sev2] The water plane terminates abruptly at a straight edge over the background void, revealing the edge of the map geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 86.1,147.4,18.2,34.3
- [weave/naive/navigation/sev2] Layered wooden walkways and rooftops overlap closely with uniform coloring and shadows, making walkable paths ambiguous to distinguish from non-walkable roofs.
- [weave/naive/navigation/sev2] Multiple layers of wooden walkways, stairs, and roofs share identical textures and lighting, making playable paths ambiguous.
- [weave/naive/navigation/sev1] The elevated track terminates directly against a solid cliff wall without an opening or visual transition.
- [weave/naive/immersion/sev2] The water and terrain abruptly terminate into empty dark space, exposing the edge of the game world.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 85.8,147.4,22.2,36.2
- [weave/naive/navigation/sev2] Uniform dark brown tones and overlapping roofs obscure navigable walkways from decorative rooftops, making paths difficult to discern.
- [weave/naive/navigation/sev2] Dense, monochromatic wooden structures make walkable paths visually merge with non-walkable roofs and railings, making navigation ambiguous.
- [weave/naive/geometry/sev1] The terrain geometry cuts off abruptly at the map edge, exposing the empty background void.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 94.5,106.5,-2.9,1.3
- [waterfront/naive/immersion/sev2] A small wooden platform floats in mid-air above the water gap without any visible supports or suspension.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 37.4,43.7,22.3,28.7
- [waterfront/naive/navigation/sev2] Multiple overlapping wooden staircases and ramps create visual clutter, making walkable pathways ambiguous.
- [waterfront/naive/geometry/sev2] The boat hull clips directly through the wooden support posts of the surrounding structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 17.9,26.4,30.7,38.3
- [waterfront/naive/navigation/sev2] The overlapping staircases, ramps, and wooden beams create visual clutter where walkable paths cannot be distinguished from decorative scaffolding.
- [waterfront/naive/immersion/sev2] A boat hull is suspended horizontally in mid-air next to the concrete structure without resting on water or physical supports.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 17.9,26.5,30.8,38.2
- [waterfront/naive/immersion/sev2] A wooden platform section floats mid-air without any supporting posts or connections underneath.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 37.4,43.7,22.3,28.7
- [waterfront/naive/navigation/sev2] The dense layer of overlapping ramps, stairs, clutter, and an overturned boat makes it ambiguous which path is walkable.
- [waterfront/naive/geometry/sev1] The wooden boat on the right clips awkwardly into the concrete wall and pier structure without resting on water or supports.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 17.9,25.6,30.6,38.3
- [waterfront/naive/navigation/sev2] The dense network of overlapping ramps, stairs, and scaffolding lacks clear visual cues, making it ambiguous which surfaces form a walkable path.
- [waterfront/naive/navigation/sev2] The overlapping staircases, ramps, and wooden beams create a visually confusing cluster where playable paths are ambiguous.
- [waterfront/naive/immersion/sev2] A wooden platform section floats detached over the water gap without visible structural support or connection.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 37.4,43.7,22.4,28.7
- [waterfront/naive/geometry/sev1] The boat is lodged awkwardly into the side of the concrete wall with clipping along its hull.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 17.9,25.6,30.7,38.3
- [waterfront/naive/navigation/sev2] Overlapping stairs, ramps, and planks create a visually chaotic path structure where valid walkable paths cannot be clearly distinguished.
- [waterfront/naive/geometry/sev2] A wooden platform section floats in mid-air across the gap with no visible structural supports or beams attached.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 37.3,43.7,22.3,28.7
- [waterfront/naive/navigation/sev2] The chaotic overlap of wooden walkways, stairs, and structural beams makes it ambiguous which surfaces are walkable paths.
- [waterfront/naive/navigation/sev2] Multiple overlapping staircases, ladders, and ramps crisscross densely without clear visual cues showing which surfaces are walkable paths versus background structure.
- [waterfront/naive/geometry/sev2] The wooden boat clips directly into the concrete wall and adjacent wooden scaffolding.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 17.9,25.6,30.7,38.3
- [waterfront/naive/geometry/sev2] A wooden platform section floats suspended over the water gap without support posts or beam connections underneath.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 37.3,43.7,22.3,28.7
- [waterfront/naive/geometry/sev2] The wooden boat rests precariously on thin scaffolding beams with no secure cradle or rigging, appearing to float or clip into the incline.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region -54.3,32.8,22.9,32.1
- [waterfront/naive/navigation/sev2] Multiple overlapping ramps, stairs, and planks create an ambiguous path where playable surfaces are hard to distinguish from background geometry.
- [waterfront/naive/immersion/sev2] A wooden boat is wedged sideways high above the water level on a wall without logical support or rigging.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 17.9,26.5,30.8,38.3
- [fishdock/naive/immersion/sev2] A wooden dock platform floats in mid-air directly above the small boat without any supports.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 44.7,52.4,26,34.5
- [fishdock/naive/geometry/sev2] The long diagonal wooden ladder clips directly through the platform railing.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 40.4,49.2,17.4,22.6
- [fishdock/naive/immersion/sev2] A wooden platform hovers in mid-air directly over a small boat without any supporting posts or stilts.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 44.5,52.4,26.1,35.7
- [fishdock/naive/geometry/sev1] A long diagonal wooden beam on the right side clips directly into the floorboards of the pier deck.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 40,47.3,19.7,30
- [fishdock/naive/immersion/sev2] A wooden platform section floats unsupported in mid-air directly above the rowboat with no legs or supports anchoring it.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 44,49.9,22.4,34.1
- [fishdock/naive/immersion/sev2] A wooden dock platform hovers unnaturally directly over a small rowboat without any visible support structures.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 44.6,52.4,26,35.6
- [fishdock/naive/immersion/sev2] A wooden platform floats directly in mid-air over a rowboat without any structural supports or attachments.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 44.7,52.3,26.1,34.5
- [fishdock/naive/geometry/sev2] A wooden platform appears to hover directly over and clip into a small boat without proper structural support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 44.7,52.3,26.1,34.5
- [fishdock/naive/immersion/sev1] The rope barrier connecting the posts in the water consists of rigid floating cylinder segments without proper rope sagging.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 42.7,56.7,27,40.1
- [fishdock/naive/geometry/sev1] A long diagonal wooden beam stretches across the right side without support joints or clear functional geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 40.1,47.4,17,30
- [fishdock/naive/immersion/sev2] A wooden dock section floats unsupported in mid-air directly above a rowboat without any pillars or connections to the water or surrounding structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 43.1,50.6,22.4,34.1
- [fishdock/naive/immersion/sev2] A wooden deck platform hovers above a small rowboat without any posts or structural connections linking it to the boat or water.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 44.7,52.4,26,34.5
- [fishdock/naive/geometry/sev1] An extremely long, thin beam stretches from the upper structure down to the pier railing without any supporting framework along its length.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 40,47.4,17.1,26.9
- [fishdock/naive/immersion/sev2] A heavy wooden platform is floating rigidly directly over a tiny rowboat without realistic buoyancy or support structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 44.7,52.4,26,34.5
- [north-landing/naive/immersion/sev1] Stylized conical plant assets protrude horizontally directly out of the vertical cliff face without stems or natural attachment points.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 96.7,111.6,17.7,27.5
- [north-landing/naive/geometry/sev1] The left side of the water wheel clips directly into the concrete dam structure without visible axle mountings or a housing cutout.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 85.8,93.6,31,36.3
- [north-landing/naive/navigation/sev2] The main elevated walkway narrows significantly and visually blends into dense background scaffolding, making the forward route hard to distinguish.
- [north-landing/naive/navigation/sev2] The stepping stones lead directly into a solid concrete wall with no ladder, ledge, or door to continue along.
- [north-landing/naive/immersion/sev1] Multiple stylized tree assets clip straight into the vertical rock face without trunks or bases.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region -27.9,102.4,19.2,82.9
- [north-landing/naive/navigation/sev2] The main path continues into a dense tangle of wooden beams and platforms, making it difficult to discern walkable routes from background clutter.
- [north-landing/naive/geometry/sev2] A large square opening cut into the wooden floor reveals unfinished internal geometry without railings, ladders, or clear visual purpose.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 105.3,110.8,24.1,30.3
- [north-landing/naive/navigation/sev2] The dense maze of wooden scaffolding and support beams against the cliff makes walkable paths and stairs difficult to distinguish from background structure.
- [north-landing/naive/immersion/sev1] Conical plant models are embedded sideways directly into the sheer vertical rock wall without visible stems, roots, or soil ledges.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 96.7,103.3,19.2,23.8
- [north-landing/naive/navigation/sev2] A square hole in the platform floor drops into dark structure underneath without a ladder or visual cue indicating if it is a path or a hazard.
- [north-landing/naive/immersion/sev1] Stylized conical plants stick horizontally out of the vertical cliff face without roots or soil, appearing like floating or misaligned geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 98.2,102.5,19.2,23
- [north-landing/naive/navigation/sev2] An unguarded square hole in the middle of the walkable wooden platform creates an ambiguous hazard without any railing or visible ladder.
- [north-landing/naive/navigation/sev2] The dense, overlapping wooden scaffolding visually blends together, making it hard to discern where the walkable path continues.
- [north-landing/naive/navigation/sev2] The dense overlap of wooden beams, stairs, and supports makes it visually ambiguous where playable paths continue.
- [north-landing/naive/immersion/sev1] Tree models stick directly horizontally out of the vertical rock face without roots or proper orientation.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 98.2,102.5,19.3,23
- [north-landing/naive/geometry/sev1] The cutout hole in the platform floor shows raw clipped geometry and incomplete framing underneath.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 105.3,110.9,24.1,30.3
- [north-landing/naive/geometry/sev1] The conical tree models stick horizontally out of the vertical cliff face without visible trunks or roots.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 101.9,107.8,19,24
- [north-landing/naive/navigation/sev2] Dense wooden structures along the cliff side obscure accessible paths, making it unclear which levels are playable.
- [north-landing/naive/geometry/sev1] The green cone-shaped vegetation models clip directly out of the rock face without roots or natural blending.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 94.4,111.3,18.2,28.1
- [north-landing/naive/navigation/sev2] The dense, overlapping wooden beams make it difficult to discern navigable paths from non-walkable background clutter.
- [north-landing/naive/navigation/sev2] The visual density of overlapping structural scaffolding makes it hard to distinguish walkable surfaces from non-walkable framing.
- [north-landing/naive/immersion/sev1] Cone-shaped vegetation models stick straight out horizontally from the steep rock face without roots or natural placement.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 97.3,101.8,20.2,23.8
- [north-landing/naive/geometry/sev1] An unbordered rectangular hole in the middle of the circular deck exposes raw structural pillars without a hatch or ladder.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 105.3,110.8,24.1,30.3

### style-bar (0)



## 3. Budget

66 calls, 101944 prompt + 108091 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.