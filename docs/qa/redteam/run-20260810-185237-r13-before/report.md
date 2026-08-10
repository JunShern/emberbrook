# Scene red-team — dellhollow — run 20260810-185237-r13-before

judge `gemini:gemini-3.6-flash` (pinned) · 6 plates · naive

## 1. Calibration

_not scored in this run_


## 2. Survivors by bucket

### known (18)

- [gate/naive/immersion/sev2] The lower foliage cluster floats in mid-air in front of the cliff face without any trunk or structural attachment to the rock.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region -1,11,-0.5,4.3
- [lockhead/naive/geometry/sev1] A thin rod or line segment floats horizontally in mid-air near the upper staircase.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 53.1,65.3,8.4,17
- [lockhead/naive/geometry/sev2] A stray line or beam floats horizontally in mid-air near the stairs without support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 53,65.4,8.2,17
- [lockhead/naive/geometry/sev1] A thin blue spline or wire floats in mid-air near the upper staircase without proper anchor points.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 53.1,65.3,8.4,17
- [lockhead/naive/geometry/sev1] A thin grey rod floats horizontally in mid-air alongside the staircase without any structural support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 53.1,60.5,8.4,12.5
- [lockhead/naive/geometry/sev2] A thin wooden beam or stick floats horizontally near the upper staircase without visible support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 53.1,65.3,7.9,17.3
- [crossing/naive/geometry/sev2] The wooden platform contains disconnected, floating, and misaligned planks.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 71.1,87.3,21.6,37.6
- [crossing/naive/geometry/sev1] Disconnected and floating wooden planks on the lower pier section look like unfinished geometry rather than a readable path.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 69.7,87.6,20.9,38.6
- [crossing/naive/geometry/sev1] Wooden planks on the dilapidated pier float above their support beams without visible attachment points.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 71.3,85.1,20.3,38
- [crossing/naive/navigation/sev2] Disconnected and overlapping wooden plank structures create ambiguous paths, making it unclear which parts are walkable terrain versus decorative obstacles.
- [deep-stairs/naive/occlusion/sev2] Harsh pitch-black cast shadows obscure the stairs and rock face, making path continuity and spatial depth unreadable.
- [deep-stairs/naive/navigation/sev2] The wooden staircase blends heavily into the rock face behind it and cuts through harsh shadow borders, making pathing ambiguous.
- [deep-stairs/naive/geometry/sev2] The long diagonal flight of stairs spans a wide gap without any structural support posts or beams underneath.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 32.4,48.2,17.8,28.5
- [deep-stairs/naive/navigation/sev2] Harsh pitch-black shadows across the central cliff structure obscure stair depth and path connectivity, making it difficult to discern where to walk.
- [deep-stairs/naive/geometry/sev2] The long wooden staircase spanning across the open gap lacks any supporting posts or framing beneath it, floating unsupported in mid-air.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 32.4,50.9,16.5,26.9
- [deep-stairs/naive/geometry/sev2] The long diagonal wooden staircase floats across the open gap without visible structural supports or pillars attached to the ground.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 32.4,50.1,16.3,26.9
- [deep-stairs/naive/navigation/sev2] Pitch-black pitch shadows completely obscure the cliffside path and stairs, making it unclear where the route continues.
- [deep-stairs/naive/occlusion/sev2] Deep, harsh shadows obscure the terrain and structure depth, making it hard to discern whether walkable paths exist behind the main staircase.

### new (92)

- [gate/naive/geometry/sev1] The stylized tree canopy and branches clip directly into the flat vertical rock face.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region -0.8,12.8,-6.7,4.3
- [gate/naive/immersion/sev1] The distant background wall uses a stretched, flat texture map that visually breaks depth compared to the foreground 3D rock wall.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 14.7,152.1,-2.7,72.6
- [gate/naive/immersion/sev2] The trees protrude directly out of the sheer vertical rock face without roots, soil, or a supporting ledge.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region -4.4,14.3,-6.1,4.2
- [gate/naive/geometry/sev2] The terrain transitions into harsh, low-polygon blocky geometry with stretched textures along the lower right edge.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region -2.3,10.9,-6.5,6.6
- [gate/naive/immersion/sev1] The background cliff wall appears as a flat, unshaded surface where the water abruptly ends without proper shoreline geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 14.7,151.7,-3.6,72.6
- [gate/naive/geometry/sev1] The foreground terrain at the bottom right displays blocky, unrefined polygon edges and stretched textures.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region -2.6,7.9,-7.2,6
- [gate/naive/immersion/sev1] The large background cliff wall consists of flat vertical planes with low-resolution, stretched textures.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 14.2,150.3,8.5,66.1
- [gate/naive/immersion/sev1] The lower cluster of orange and green foliage floats in mid-air on the right side of the path without any visible trunk or branch connecting it to the cliff wall.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region -0.9,11,-0.4,4.3
- [gate/naive/geometry/sev1] The low-poly rock geometry in the foreground terminates in raw polygonal edges and unblended seams.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region -2.5,8.7,-7.2,5.8
- [lockhead/naive/immersion/sev1] Plain brown placeholder cubes rest awkwardly on the sloped rooftop without proper alignment or securing structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 65.3,72.4,15,20.9
- [lockhead/naive/immersion/sev2] Untextured prototype geometry (cubes and orange spheres) sits on top of the roof, appearing as unfinished developer assets.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 58.4,65.3,13.9,20.5
- [lockhead/naive/immersion/sev2] Plain, untextured blockout boxes sit on the roof surface without proper materials or details.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 65.3,72.4,14.8,20.9
- [lockhead/naive/navigation/sev2] The central bridge walkway is heavily blocked by crates and blocks, making it unclear if the path is walkable.
- [lockhead/naive/geometry/sev2] Unfinished grey box blockout models and orange placeholder spheres clip into the roof.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 58.4,65.1,13.9,20.3
- [lockhead/naive/immersion/sev1] Plain grey cubes resting on the sloped roof appear to be placeholder blockout objects.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 65.3,72.4,14.9,20.9
- [lockhead/naive/geometry/sev1] A thin blue line clips horizontally through the wooden staircase structure without anchor points.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 53,60.4,8.4,12.5
- [lockhead/naive/immersion/sev2] Untextured brown blockout cubes sit on the roof, breaking visual immersion in an otherwise textured scene.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 65.3,72.5,14.9,20.9
- [lockhead/naive/immersion/sev1] The bright orange and green crates along the bridge appear as untextured primitive blockout shapes.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 65.4,79,11.3,19.1
- [lockhead/naive/geometry/sev2] Untextured white placeholder geometry is left exposed beneath the wooden walkway.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 79.1,83.6,13.9,18.5
- [lockhead/naive/immersion/sev2] Bright featureless orange blocks sit atop the crates along the bridge, resembling untextured placeholder geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 65.5,77.2,12.4,19.1
- [lockhead/naive/immersion/sev2] Simple untextured box primitives sit on the roof, looking like unfinished placeholder greybox geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 67.2,72.4,16.6,21
- [lockhead/naive/immersion/sev2] Untextured orange and green blockout primitives sit on the bridge structure, looking like unfinished placeholder art.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 65.4,79.2,11.3,19.1
- [lockhead/naive/immersion/sev2] Featureless brown prototype boxes sit on the sloped roof tiles, breaking visual consistency with the rest of the environment.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 65.1,72.6,14.3,20.9
- [lockhead/naive/navigation/sev2] A sequence of crates is placed directly across the walkway, visually blocking the player's primary path.
- [lockhead/naive/immersion/sev1] Untextured box geometry rests unnaturally at sharp angles on a sloped roof without logical support or ties.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 65.3,72.6,14.3,20.9
- [lockhead/naive/immersion/sev2] Blocky, prototype-like colored boxes are perched unnaturally along the narrow bridge railing without proper support or functional context.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 65.5,78.9,11.4,19.1
- [cottage/naive/geometry/sev2] The broken wooden planks clip awkwardly into support beams and hover unnaturally.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 86.5,95.6,17.7,24.4
- [cottage/naive/navigation/sev2] It is unclear whether this steep, damaged ramp is a navigable path or non-interactive environment debris.
- [cottage/naive/navigation/sev2] The severely broken and fragmented wooden bridge makes it ambiguous whether the path is navigable or impassable debris.
- [cottage/naive/navigation/sev2] The broken wooden ramp is composed of heavily disjointed and clipping planks, making it ambiguous whether it functions as a walkable path or impassable debris.
- [cottage/naive/geometry/sev1] The ladder lacks attachment hardware and clips directly into the surrounding timber and cliff geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 79.3,85.9,15.5,23.5
- [cottage/naive/geometry/sev1] The rock mesh displays unnaturally sharp, repetitive sawtooth polygon spikes that break the organic cliff face.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 91.9,112.3,-1.8,22.4
- [cottage/naive/navigation/sev2] The wooden walkway collapses into several jagged, overlapping layers, making it visually unclear which surface is walkable and where the path leads.
- [cottage/naive/navigation/sev2] The chaotic, overlapping wooden planks of the broken ramp make it ambiguous where walkable terrain ends and impassable debris begins.
- [cottage/naive/navigation/sev2] The broken wooden walkway consists of disjointed, overlapping planks that make it hard to tell if this is a passable ramp or an impassable structure.
- [cottage/naive/immersion/sev2] A line of identical orange cubes sits unnaturally along a narrow wooden beam without visible support or context, appearing like untextured placeholder blocks.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 88.3,95.8,16,21.4
- [cottage/naive/navigation/sev2] The fragmented wooden ramp and underlying roof structures overlap with identical textures, making it ambiguous which surfaces are walkable paths.
- [crossing/naive/geometry/sev2] An untextured triangular polygon mesh clips into view at the bottom-right edge of the screen.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,69.7,12.7,17.2
- [crossing/naive/geometry/sev1] Broken wooden floorboards on the lower platform extend horizontally into open space without visible structural support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 70.7,78.5,23.6,29.1
- [crossing/naive/geometry/sev2] An unfinished grey triangular mesh clips through the wooden walkway terrain at the bottom right corner.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,69.7,12.7,17.2
- [crossing/naive/navigation/sev2] Heavy shadows combined with dense structural layering make it visually difficult to discern navigable paths from background scenery.
- [crossing/naive/geometry/sev2] Untextured graybox geometry protrudes through the terrain and walkway edge.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,70.1,12.7,17.2
- [crossing/naive/geometry/sev2] Untextured grey low-poly geometry cuts awkwardly into the wooden walkway path at the bottom right edge.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,69.1,12.7,17.8
- [crossing/naive/navigation/sev2] Harsh shadows and overlapping wooden decks obscure whether there is continuous walkable ground or a fatal drop into water.
- [crossing/naive/geometry/sev2] Unfinished gray polygonal geometry is exposed along the bottom right edge of the terrain mesh.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,69.7,12.7,17.2
- [crossing/naive/occlusion/sev2] Extremely dark, pitch-black shadows obscure the central walkway and structures, hiding elevation changes and potential paths.
- [crossing/naive/geometry/sev1] An untextured or incomplete polygon mesh protrudes out of the ground at the bottom-right corner of the screen.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,69.1,12.7,17.3
- [crossing/naive/immersion/sev1] Broken wooden floorboards float in mid-air without structural support or connection to the walkway framing.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 70.6,82,22.6,29.2
- [crossing/naive/geometry/sev2] A sharp, flat blue-grey polygon clips directly through the wooden walkway surface.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,69.7,12.7,17.2
- [crossing/naive/geometry/sev2] An untextured grey polygon clips into the ground terrain near the bottom right corner.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,69,12.7,17.4
- [crossing/naive/geometry/sev1] The broken wooden platform contains planks suspended in mid-air without structural support beneath them.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 69.5,87.3,21.6,36.6
- [crossing/naive/geometry/sev2] An untextured blue-grey geometric wedge clips through the terrain at the bottom-right edge of the screen.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,69.7,12.7,17.2
- [crossing/naive/immersion/sev1] A glowing lantern floats directly over the wooden pier structure without any base or support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 70,78.6,22.1,28.2
- [crossing/naive/immersion/sev1] The white canopy roof is a paper-thin single polygon plane without visible depth or structural framing.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 79.7,95.6,11.5,18.3
- [deep-stairs/naive/navigation/sev2] The green-patterned wooden planks crisscross at conflicting angles without readable elevation steps or connections, making the path unclear.
- [deep-stairs/naive/geometry/sev1] The long wooden support beam passes straight through the lower bridge deck without any socket or join geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 42.6,52.2,17.7,28.5
- [deep-stairs/naive/occlusion/sev2] An extremely dark cast shadow completely hides the cliffside geometry and any potential pathways or entrances behind it.
- [deep-stairs/naive/navigation/sev2] The main staircase breaks down into disjointed green planks resting unevenly on the rock slope, making the continuing path ambiguous.
- [deep-stairs/naive/immersion/sev1] The colored banners appear as stiff flat rectangles clipping directly into wooden beams without any visible ropes or attachment points.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 43.1,56,16.7,30.5
- [deep-stairs/naive/occlusion/sev2] Extremely high-contrast, jet-black shadows completely hide walkways and geometry along the central wall, obscuring navigation options.
- [deep-stairs/naive/occlusion/sev2] Pitch-black cast shadows completely obscure the cliffside path and visual depth, making it unclear where the player can walk.
- [deep-stairs/naive/immersion/sev1] The vertical support beam on the left clips directly through the platform floor without proper joints or visual anchors.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 43,52.2,17.7,30
- [deep-stairs/naive/immersion/sev1] The hanging banners appear as rigid, thick rectangular solids rather than cloth draped over the line.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 41.1,56.2,16.8,30.5
- [deep-stairs/naive/occlusion/sev2] Harsh, pitch-black cast shadows obscure the terrain and structure geometry, masking navigable paths and depth.
- [deep-stairs/naive/geometry/sev2] The wooden ramp segments float in mid-air above the ground terrain without posts or scaffolding anchoring them.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 31.7,44.4,18.9,29.9
- [deep-stairs/naive/navigation/sev2] Deep pitch-black shadows completely hide the cliff face and path connections, making vertical navigation routes unclear.
- [deep-stairs/naive/geometry/sev1] The green-patterned walkway segments appear paper-thin and float without visible structural depth or clear supports beneath them.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 31.8,44.2,18.9,25
- [deep-stairs/naive/immersion/sev1] The extremely long, thin wooden beam spans almost the entire height of the structure with no intermediate supports or realistic joints.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 41.2,49.5,21.2,30
- [deep-stairs/naive/geometry/sev2] The wooden stair steps lack supporting stringers or beams beneath them, appearing to hover unattached in mid-air.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 32.3,47.9,17.9,29.5
- [deep-stairs/naive/occlusion/sev2] Extremely dark shadows mask the interior path and cliffside geometry, making spatial layout and walkable routes unreadable.
- [deep-stairs/naive/navigation/sev2] Multiple overlapping staircases and platforms span across the chasm with low lighting contrast, creating ambiguity in where the player can walk.
- [deep-stairs/naive/geometry/sev1] The long wooden staircase spans across open space without visible structural support beams or posts.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 32.4,48,17.8,28.4
- [deep-stairs/naive/navigation/sev2] The staircase path visually merges with the dark background shadow, making the landing points and navigation route ambiguous.
- [deep-stairs/naive/immersion/sev2] The long elevated wooden staircase lacks supporting structural posts or brackets anchoring it to the cliff face or ground.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 32.4,48,17.9,29.4
- [deep-stairs/naive/geometry/sev1] The large angled wooden trough structure visually clips into adjacent scaffolding beams and floor planks.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 26.8,33.4,21.2,31.9
- [fishdock/naive/geometry/sev2] A rectangular floating dock structure is clipping directly through the small rowboat below it.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 44.5,52.4,26,35.7
- [fishdock/naive/immersion/sev2] An extremely long, unsupported diagonal timber beam spans down to the lower level without any visible fasteners or logical structural purpose.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 40.1,47.4,16.6,30
- [fishdock/naive/geometry/sev2] The wooden platform floats in mid-air over a small boat, disconnected from the main dock with no visible pilings or supports.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 44.8,52.6,26,34.5
- [fishdock/naive/immersion/sev2] Untextured bright orange primitive cubes sit on the dock deck, looking like forgotten developer placeholders.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 56.2,64.8,30.8,35.8
- [fishdock/naive/immersion/sev2] A wooden platform hovers rigidly inside and above a small boat without visible physical supports or ropes.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 44.7,52.4,26.1,34.5
- [fishdock/naive/geometry/sev1] An unnaturally long, thin diagonal wooden plank extends from the upper structure down to the railing without intermediate support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 40.1,47.4,17,30
- [fishdock/naive/immersion/sev2] A wooden platform floats awkwardly over a small boat in the water without visible physics or structural attachment.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 44.7,52.4,26,34.6
- [fishdock/naive/geometry/sev1] An extremely long, thin wooden plank stretches unsupported from the top right cliff down to the lower walkway.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 40.1,47.5,16.9,27
- [fishdock/naive/immersion/sev1] The rope barrier in the water consists of rigid floating cylinder segments that do not sag like natural ropes.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 42.7,56.6,27.2,40.1
- [fishdock/naive/immersion/sev2] Several bright orange blocks appear to be untextured placeholder cubes left on the pier.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 56.1,63.8,30.9,36.6
- [fishdock/naive/immersion/sev2] A green wooden platform floats unsupported in the air directly above the small rowboat.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 44.7,52.3,26.1,34.4
- [fishdock/naive/geometry/sev1] The long diagonal pole passes straight through structural roofs and railings without visible connections or cutouts.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 40,47.3,16.5,30
- [fishdock/naive/immersion/sev2] A green-tinted wooden platform floats directly above a small rowboat without any supporting posts or dock structure attaching it to the main pier.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 44.7,52.4,26,34.6
- [fishdock/naive/immersion/sev2] A wooden platform hovers in mid-air above the small boat without any pillars or structural support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 44.8,52.4,26,34.4
- [fishdock/naive/immersion/sev2] Bright orange placeholder cubes appear on the dock surface without textures.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 56,64.8,31.5,35.9
- [fishdock/naive/navigation/sev2] An extremely long, thin plank spans steeply up to the upper building, leaving it ambiguous if it is a playable path or structural beam.
- [fishdock/naive/geometry/sev2] The wooden dock platform clips directly through the rowboat hull beneath it.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 44.6,52.4,26,35.6

### style-bar (0)



## 3. Budget

66 calls, 101633 prompt + 105903 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.