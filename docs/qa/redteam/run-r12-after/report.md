# Scene red-team — dellhollow — run r12-after

judge `gemini:gemini-3.6-flash` (pinned) · 6 plates · naive

## 1. Calibration

_not scored in this run_


## 2. Survivors by bucket

### known (15)

- [cottage/naive/geometry/sev2] Multiple wooden planks float without visible structural support or clip unnaturally through the underlying frame.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 86.7,95.6,15.9,25
- [cottage/naive/navigation/sev2] The wooden ramp breaks into fragmented, floating planks, making it ambiguous whether it is an active walkway or collapsed impassable scenery.
- [crossing/naive/geometry/sev1] Several broken wooden planks on the lower platform float in mid-air without structural supports.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 70.4,87.3,21.6,35.8
- [crossing/naive/occlusion/sev2] Extremely dark cast shadows obscure the wooden staircases and cliffside paths, making navigation and terrain readability difficult.
- [waterfront/naive/immersion/sev2] A wooden platform slab floats detached in mid-air above the water without any supports underneath or connection to the surrounding terrain.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 37.4,43.7,22.3,28.7
- [waterfront/naive/geometry/sev2] A wooden plank platform floats in mid-air near the cliff edge without any visible physical supports.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 37.3,43.7,22.3,28.7
- [waterfront/naive/geometry/sev2] A wooden plank step floats unsupported in mid-air above the water.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 37.4,43.7,22.3,28.7
- [waterfront/naive/geometry/sev2] A wooden platform section floats unattached in mid-air above the water channel.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 37.4,43.7,22.4,28.7
- [waterfront/naive/geometry/sev2] A wooden plank segment floats completely unsupported in mid-air over the stream.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 37.4,43.7,22.3,28.7
- [waterfront/naive/immersion/sev2] A wooden step platform floats in mid-air over the water channel without any visible attachment or support structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 37.4,43.7,22.4,28.7
- [north-landing/naive/geometry/sev1] The concrete blocks float unnaturally on the water surface near the ledge without visible supports or immersion into the water depth.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 86.9,95.2,33,42.3
- [north-landing/naive/immersion/sev2] The rectangular stepping stones float unnaturally on top of the water surface without visible depth, reflections, or support structures.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 86.9,95.8,33,42.3
- [north-landing/naive/immersion/sev1] The rectangular stone blocks appear to float loosely on the surface of the water without bases or water interaction.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 86.9,95.2,33,42.3
- [north-landing/naive/immersion/sev1] The white rectangular blocks in the water appear untextured and float on the water surface without realistic displacement or alignment.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 95.3,109.5,28.8,34.1
- [north-landing/naive/geometry/sev2] The stepping stones in the water appear as untextured greybox rectangular blocks floating without proper water blending or detail.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 86.9,95.3,33,42.4

### new (106)

- [cottage/naive/immersion/sev2] A row of uniform orange cubes floats in mid-air without visible support or logical connection to the environment.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 84.4,88.9,12.3,18.6
- [cottage/naive/navigation/sev2] The main walkway breaks down into a cluttered pile of fragmented planks, making it visually ambiguous whether the path continues or is blocked.
- [cottage/naive/navigation/sev2] The chaotic, overlapping, and fractured plank structure makes it unclear which parts form a walkable path versus impassable debris.
- [cottage/naive/immersion/sev1] The bright orange cube objects look like untextured placeholder blocks floating precariously along a thin beam.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 88.5,95.8,15.8,20.4
- [cottage/naive/geometry/sev2] The broken wooden planks clip through each other chaotically, making it unclear whether the path is walkable geometry or broken debris.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 87,96.2,13.5,20.7
- [cottage/naive/immersion/sev1] The orange hanging boxes resemble untextured placeholder primitives strung on an invisible line, breaking visual consistency.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 88.4,96,16,21.4
- [cottage/naive/occlusion/sev2] Extremely high-contrast dark shadows obscure the structure underneath, hiding pathways and terrain depth.
- [cottage/naive/immersion/sev2] A row of orange cube blocks floats unnaturally in mid-air near the building.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 88.3,95.8,15.8,21.1
- [cottage/naive/navigation/sev2] The jumble of broken, overlapping planks makes it ambiguous whether this area is playable terrain or a dead-end hazard.
- [cottage/naive/geometry/sev1] The ladder extends along the cliff face without clear structural anchoring at its top.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 78.3,85.9,15.3,23.4
- [cottage/naive/navigation/sev2] The collapsed wooden ramp is severely fractured into steep, disjointed planks, making it ambiguous whether it is a walkable route or non-traversable environmental destruction.
- [cottage/naive/navigation/sev2] The top of the long ladder ends near the upper platform without a clear landing edge or dismount area, making its usability as a climbable route unclear.
- [cottage/naive/geometry/sev1] A sequence of orange blocks floats in mid-air across the gap without visible support geometry underneath.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 88.8,95.8,15.8,20.5
- [cottage/naive/immersion/sev2] A row of orange square blocks floats in mid-air near the roof without any support structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 88.5,95.8,15.8,20.4
- [cottage/naive/navigation/sev2] The chaotic overlap of shattered ramp planks and underlying support beams makes it difficult to discern walkable pathways from visual background debris.
- [cottage/naive/immersion/sev1] The long wooden ladder appears to hover along the cliff face without clear structural anchoring or attachment points.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 78.2,85.7,15.4,23.4
- [cottage/naive/navigation/sev2] The collapsed wooden bridge breaks into a chaotic slope of jagged planks, making it visually unclear if it can be traversed.
- [cottage/naive/immersion/sev1] A series of orange square objects float in mid-air across the gap without visible cables or supports.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 88.4,96,16,21.4
- [cottage/naive/geometry/sev1] The long wooden ladder floats alongside the cliff wall without visual anchors or support structures.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 78.2,85.9,15.5,23.4
- [cottage/naive/occlusion/sev2] Heavy shadows and overlapping architecture completely obscure the area behind the lower hut, hiding potential pathways or doorways.
- [cottage/naive/immersion/sev2] A row of orange blocks is floating horizontally in mid-air without any visible rope, wire, or attachment.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 88.9,95.8,15.9,20.5
- [cottage/naive/navigation/sev2] The collapsed section of the wooden bridge is a chaotic heap of intersecting, misaligned planks, making it unclear if it is walkable or impassable.
- [cottage/naive/navigation/sev2] The ladder leads straight under the overhang of the upper platform without a clear hatch or landing area.
- [cottage/naive/navigation/sev2] The chaotic arrangement of fragmented planks and collapsed ramp geometry makes it very difficult to distinguish walkable paths from impassable debris.
- [cottage/naive/occlusion/sev2] Deep cast shadows combined with the overlapping ramp geometry completely obscure the entry point and interior structure of the building.
- [crossing/naive/geometry/sev2] An untextured grey geometric mesh clips through the wooden walkway in the bottom right corner.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,69.7,12.7,17.2
- [crossing/naive/geometry/sev2] Raw, untextured gray geometry clips through the terrain at the bottom right edge of the frame.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.6,69.7,12.7,17.2
- [crossing/naive/geometry/sev2] Incomplete or grey placeholder geometry cuts into the foreground terrain in the bottom right corner.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,69.7,12.7,17.3
- [crossing/naive/geometry/sev1] The white canopy roof in the upper right is a paper-thin flat plane without structural thickness or support beams.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 79.7,95.6,11.5,18.3
- [crossing/naive/geometry/sev2] Unrendered raw polygonal mesh with missing textures is visible at the terrain boundary.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,68.3,13.4,17.3
- [crossing/naive/occlusion/sev2] Extremely harsh, pitch-black shadows completely hide the terrain and structures underneath the roofs, obscuring potential pathways.
- [crossing/naive/geometry/sev2] An untextured gray polygonal wedge cuts through the bottom-right foreground path.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,69.7,12.7,17.2
- [crossing/naive/navigation/sev2] Pitch-black cast shadows completely obscure structural details and walkways, making it difficult to discern walkable paths from drops.
- [crossing/naive/geometry/sev2] An untextured grey polygon cuts directly through the ground terrain in the bottom right corner.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,69.1,12.7,17.3
- [weave/naive/navigation/sev2] The dense layering of rooftops, bridges, and stilts creates visual clutter that makes walkable pathways hard to distinguish from background environment.
- [weave/naive/geometry/sev1] Sharp, needle-like rock geometry along the cliff edge sticks out awkwardly without organic terrain blending.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 90.4,150.3,-1.8,19.4
- [weave/naive/navigation/sev2] The high density of overlapping wooden roofs, stilts, and walkways with identical materials makes it difficult to distinguish playable paths from non-navigable roofs.
- [weave/naive/geometry/sev1] The top edge of the rock wall features sharp, unnatural polygon spikes jutting into empty space.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 143.5,149.6,5.8,16.2
- [weave/naive/navigation/sev2] Dense overlapping of wooden walkways, roofs, and support stilts using uniform textures creates extreme visual clutter, making walkable paths difficult to discern.
- [weave/naive/occlusion/sev2] Upper platforms and roofs cast heavy shadows over lower pathways, obscuring ground-level routes and drop-offs.
- [weave/naive/geometry/sev1] Sharp, needle-like geometry spikes protrude unnaturally along the top of the cliff ridge.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 91.4,149.7,-1.8,19.4
- [weave/naive/immersion/sev1] The colorful banner panels hang rigidly under the wooden beam without visible rope, rings, or fabric physics.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 43.1,62.6,16.8,26.6
- [weave/naive/navigation/sev2] The visual overlap of stilts, roofs, and walkways without distinct lighting or color contrast makes navigable routes and floor levels ambiguous.
- [weave/naive/immersion/sev1] The hanging lantern floats beneath the roof edge without any string, rope, or chain connecting it to the structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 49.9,54.6,17.7,23.1
- [weave/naive/immersion/sev1] The rectangular colored flag banners float edge-to-edge beneath the wooden railing without any visible rope or fasteners.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 49.2,63.1,17.7,21.6
- [weave/naive/occlusion/sev2] Harsh cast shadows completely obscure the structural connections and ground level beneath the elevated bridge.
- [weave/naive/geometry/sev1] The water and terrain geometry clip off abruptly into a dark background void on the far left edge.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 89.6,148.2,11.5,32.2
- [weave/naive/navigation/sev2] The dense, overlapping arrangement of wooden stilts, roofs, and platforms creates heavy visual noise, making it ambiguous which pathways are walkable.
- [weave/naive/occlusion/sev2] Deep cast shadows under the elevated walkways completely obscure ground-level paths and terrain features.
- [weave/naive/navigation/sev2] Dense overlapping wooden structures and harsh shadows make it difficult to distinguish walkable paths from non-traversable roofs.
- [weave/naive/immersion/sev2] The water body cuts off abruptly into a pitch-black void at the left edge of the map.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 98.9,147.8,19,34.3
- [weave/naive/geometry/sev1] The background on the left ends abruptly into a flat, dark void without atmospheric blending or sky detail.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 80.6,150.1,-5,30.3
- [waterfront/naive/navigation/sev2] Multiple overlapping wooden staircases and support beams create a confusing cluster, making it hard to discern navigable paths from decorative geometry.
- [waterfront/naive/immersion/sev2] A large wooden boat hovers in mid-air against the concrete structure without visible ropes, scaffolding, or water supporting it.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 17.9,25.6,30.7,38.3
- [waterfront/naive/immersion/sev2] A wooden platform segment hovers in mid-air above the water without any supporting pillars or connections.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 37.4,43.7,22.3,28.7
- [waterfront/naive/immersion/sev2] The large wooden deck extends far out over the cliff edge without visible support beams or pillars underneath.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 38,50.7,19,27.9
- [waterfront/naive/navigation/sev2] Overlapping wooden staircases, ramps, and platforms create a visually cluttered path structure where it is difficult to distinguish walkable surfaces from obstacles.
- [waterfront/naive/immersion/sev1] The large wooden deck extends out over empty space without structural supports underneath its outer corner.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 38,50.7,19,28
- [waterfront/naive/geometry/sev2] A wooden platform segment floats isolated in mid-air over the water without any structural supports.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 37.4,43.8,22.4,28.7
- [waterfront/naive/navigation/sev2] The dense, crisscrossing wooden staircases and platforms lack clear visual cues, making navigable paths hard to distinguish.
- [waterfront/naive/geometry/sev1] The wooden boat clips directly into the concrete structure and adjacent wall without natural placement or support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 17.9,25.6,30.7,38.3
- [waterfront/naive/navigation/sev2] Overlapping layers of stairs, scaffolding, and angled planks make it difficult to determine which surfaces are walkable paths versus non-interactive scenery.
- [waterfront/naive/navigation/sev2] Dense, overlapping wooden stairs and scaffolding clutter the center of the scene, making walkable paths ambiguous.
- [waterfront/naive/geometry/sev1] The wooden platform clips directly through the rocky cliffside without transition geometry or structural supports.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 38,50.4,18.9,27.9
- [waterfront/naive/navigation/sev2] The dense crisscrossing of stairs, planks, and scaffolding creates visual noise that conceals navigable paths.
- [waterfront/naive/immersion/sev1] The wooden boat on the right clips directly into the stone wall without proper support or floating physics.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 17.9,26,30.5,38.3
- [waterfront/naive/navigation/sev2] Overlapping staircases, planks, and railings crisscross without clear visual hierarchy, making walkable paths visually ambiguous.
- [waterfront/naive/immersion/sev1] A wooden boat is unnaturally resting tilted sideways against the concrete wall and pier without realistic support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 17.9,26,30.5,38.3
- [waterfront/naive/navigation/sev2] Overlapping stairs, ladders, and scaffolding beams create visual clutter where walkable paths are difficult to distinguish from structural scenery.
- [waterfront/naive/geometry/sev2] A boat hull is partially embedded into the side of the concrete dam wall and surrounding scaffolding.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 17.9,25.6,30.6,38.3
- [waterfront/naive/navigation/sev2] The dense layer of overlapping wooden beams and stairs creates visual clutter that makes walkable pathways hard to identify.
- [fishdock/naive/geometry/sev2] Bright orange untextured placeholder cubes are left sitting on the dock platform.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 56.2,63.8,30.9,36.6
- [fishdock/naive/geometry/sev2] The wooden platform clips directly through the hull of the rowboat underneath it.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 44.7,52.3,26.1,34.4
- [fishdock/naive/immersion/sev2] A wooden platform section clips straight through a small boat without any realistic support structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 43.1,49.9,22.4,34.1
- [fishdock/naive/geometry/sev1] An extremely thin, long diagonal wooden plank spans from the upper roof directly down to the pier railing with no support or thickness.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 46.3,61.4,32.7,42.9
- [fishdock/naive/immersion/sev2] The rectangular wooden dock segment hovers unsupported directly above the small rowboat.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 44.8,52.3,26.1,34.4
- [fishdock/naive/geometry/sev1] An unnaturally long, thin wooden beam stretches to the upper building without structural supports.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 40.1,47.4,17,30
- [fishdock/naive/immersion/sev2] Bright orange untextured greybox prototype cubes are left sitting on the dock surface.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 56,63.8,30.1,36.6
- [fishdock/naive/geometry/sev2] A wooden platform intersects and floats awkwardly directly inside and above a small boat.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 44.5,52.3,26.1,35.7
- [fishdock/naive/immersion/sev2] A wooden platform floats over a small boat in the water without any supporting posts or dock structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 44.8,52.4,26,34.4
- [fishdock/naive/geometry/sev1] An unnaturally long single timber beam spans diagonally across the height of the cliff with no structural support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 40.3,47.4,17.6,30
- [fishdock/naive/immersion/sev2] A green platform floats unnaturally directly on top of a small boat without clear structural support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 44.8,52.6,26,34.5
- [fishdock/naive/navigation/sev2] The main boardwalk terminates abruptly against the rock wall with no visible exit or continuation.
- [fishdock/naive/navigation/sev2] The main wooden walkway leads off to the right edge but terminates abruptly at the rock wall with no clear path forward.
- [fishdock/naive/immersion/sev1] Featureless bright orange cubes sit on the dock platform, looking like untextured developer placeholder assets.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 55.3,64.4,30,36
- [fishdock/naive/immersion/sev2] A wooden platform floats directly above and clips into a rowboat without any support structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 44.5,52.4,26,35.7
- [fishdock/naive/geometry/sev2] The green wooden platform floats in mid-air directly above the small boat without visible supporting posts or structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 44.7,52.4,26,34.5
- [north-landing/naive/navigation/sev2] The dense clutter of overlapping wooden beams and platforms makes it ambiguous which levels are walkable paths and which are non-interactive scenery.
- [north-landing/naive/geometry/sev2] The water plane ends abruptly at a sharp horizontal seam without any waterfall effect or edge geometry, making the water look like a floating mesh.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 90.6,105,27.7,43.8
- [north-landing/naive/navigation/sev2] A large square hole in the floor of the main platform lacks railings or clear visual signaling, creating an unexpected hazard that blends into the floor shadows.
- [north-landing/naive/immersion/sev2] Ground grass material texture is mapped directly onto the elevated wooden bridge walkway, appearing like a texture projection error.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 85.9,99.3,24,30.5
- [north-landing/naive/geometry/sev2] The hole in the wooden floor lacks finished edge framing or interior geometry, exposing raw open cuts.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 105.3,110.8,24.2,30.3
- [north-landing/naive/navigation/sev1] Densely packed vertical wooden scaffolding and overlapping walkways create visual clutter with unclear path continuity.
- [north-landing/naive/navigation/sev2] The elevated walkway leads directly into a dense cluster of wooden scaffolding and stilts, making it ambiguous whether the path continues or is blocked.
- [north-landing/naive/geometry/sev1] The rectangular floor opening lacks edging or structural framing, cutting cleanly into the plank texture like unfinished geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 105.4,110.8,24,30.3
- [north-landing/naive/immersion/sev1] The rectangular stepping stones sit completely flat on top of the water surface without displacement, immersion depth, or contact shading.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 86.8,95.4,33,42.3
- [north-landing/naive/navigation/sev2] The elevated green path leads directly into a dense mesh of wooden scaffolding where walkable routes are visually indistinguishable from non-walkable support beams.
- [north-landing/naive/navigation/sev1] The series of stepping stones in the water leads toward the dam wall without reaching any clear platform, ladder, or walkable shore.
- [north-landing/naive/navigation/sev2] The dense cluster of wooden scaffolding along the cliff is visually cluttered and ambiguous, making it difficult to discern walkable pathways from background geometry.
- [north-landing/naive/navigation/sev2] The dense cluster of overlapping wooden beams and platforms makes the playable path through the scaffolding visually ambiguous.
- [north-landing/naive/navigation/sev2] The dense cluster of wooden beams, ladders, and platforms along the cliff face creates high visual noise, making navigable paths difficult to distinguish from background structures.
- [north-landing/naive/geometry/sev1] The rectangular cutout in the floor deck lacks a frame, lip, or trim, appearing as a raw geometry slice into the platform texture.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 105.3,110.8,24.2,30.3
- [north-landing/naive/navigation/sev2] Dense, overlapping timber beams create extreme visual clutter, making it difficult to discern walkable pathways from non-traversable structure.
- [north-landing/naive/navigation/sev2] The dense, overlapping timber beams make path readability difficult, obscuring which platforms are walkable routes.
- [north-landing/naive/navigation/sev2] The stepping stones lead directly toward a flat wall with no clear ledge, door, or continuing path.
- [north-landing/naive/geometry/sev1] The un-railed hole cut into the wooden floor reveals floating internal support geometry without a ladder or clear gameplay function.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 105.2,110.9,23.7,30.3

### style-bar (0)



## 3. Budget

66 calls, 101871 prompt + 109780 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.