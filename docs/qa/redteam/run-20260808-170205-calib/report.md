# Scene red-team — dellhollow — run 20260808-170205-calib

judge `gemini:gemini-3.6-flash` (pinned) · 12 plates · naive + checklist

## 1. Calibration

**On the user's own five complaints, the judge found 2/5 on the exact plate (5/5 on any plate holding the same object) and raised 61 other surviving findings.** (keyword matcher only, no hand adjudication)

- **Canopy wall across the entrance** — found (other plate)
    - naive: miss
    - checklist: [shelf-west] "the route between Valley Gate and Inn: ABSENT — The specified straight stair flight path is not visible in this view."
- **The gate stair is occluded / hard to navigate** — found (other plate)
    - naive: [deep-stairs] "Harsh, pitch-black cast shadows completely obscure the cliff stairs and pathway, hiding where the player can walk." | [deep-stairs] "Deep shadow completely hides the path ahead, making it ambiguous whether the staircase leads to a usable upper level or a dead end."
    - checklist: [shelf-west] "the route between Valley Gate and Inn: ABSENT — The specified straight stair flight path is not visible in this view."
- **Stray / weird cliff geometry** — FOUND
    - naive: [gate] "The tree trunk cuts straight into the cliff face with an unblended, sharp intersection and no visible root system." | [gate] "The trees on the right wall clip directly out of the vertical rock face without realistic trunks or visible roots." | [gate] "Sharp, unrefined low-polygon cliff geometry with severely stretched textures protrudes prominently into the foreground." | [crossing] "An untextured white geometric plane is visible cutting into the terrain at the bottom-right corner." | [waterfront] "Multiple overlapping wooden ladders, staircases, and ramps intersect and blend into the rocky background, making it ambiguous which paths are walkable."
    - checklist: [gate] "The world at the frame edges: WEAK — Dense cloud layer cuts off somewhat abruptly against cliff geometry."
- **Solid plank screens where a rope fence belongs** — found (other plate)
    - naive: [crossing] "An untextured solid white triangle of geometry protrudes into the bottom right corner of the screen." | [waterfront] "The wooden boat structure clips heavily through the solid grey wall on the right."
    - checklist: [crossing] "the route between Weave huts and Keepers' Cottage: ABSENT — No high sagging plank bridge spanning over the basin is present in this view."
- **Waterfront: confusing / incomplete geometry, walking on water** — FOUND
    - naive: [crossing] "A wooden plank floats disconnectedly on the water surface without buoyant interaction or support." | [crossing] "Walkway planks and stair structures are disconnected and float without clear structural support." | [crossing] "A flat wooden platform floats independently on the water surface without visible supports or buoyant structure." | [boatyard] "The wooden roof slats on the upper-right structure are unattached and floating above the frame without visible fasteners or beam support." | [boatyard] "The large boat rests at a steep angle floating/clipping into the surrounding roofing and shore structure without adequate visible physical support." | [waterfront] "The dense, overlapping wooden stairs and scaffolding lack clear visual contrast or path signposting, making the walkable route highly ambiguous." | [waterfront] "A wooden plank platform floats in mid-air across the water channel without any visible attachment or support." | [waterfront] "A wooden plank platform floats completely unsupported in mid-air over the narrow water gap." | [waterfront] "A wooden platform segment floats in mid-air without any supports connecting it to the surrounding terrain or structures." | [fishdock] "The green wooden dock structure appears to float mid-air directly above the small boat without any vertical posts or supports." | [fishdock] "A wooden platform floats in mid-air directly over a small wooden boat without any supporting posts or connections." | [fishdock] "A wooden platform appears to float unsupported in mid-air directly above and inside a small boat." | [lockfive] "The wooden stair treads float individually without stringers or side beams supporting them from the dock or cliff face." | [lockfive] "Multiple broken, overlapping boardwalk layers and disjointed platforms make the playable path through the lower docks confusing and ambiguous." | [lockfive] "The dock walkway disintegrates into tilted, submerged planks, making it ambiguous whether this is a valid walking path or impassable terrain." | [north-landing] "A green wooden plank floats on the water without any visible framing, posts, or connection to the nearby dock." | [north-landing] "The rectangular stepping stones float visually on top of the water surface without visible bases or underwater geometry." | [north-landing] "An open square hole in the wooden deck lacks railing or clear path indicators, creating ambiguous navigation and a fall hazard." | [north-landing] "A wooden plank platform floats flat on the water surface without any visible support posts or flotation structures." | [north-landing] "An open square cutout in the wooden platform lacks railings or a visible ladder, making it unclear if it is an intended entry point or a floor hazard." | [north-landing] "The path of stepping stones in the water abruptly ends near the dam wall, leaving the intended route forward ambiguous."
    - checklist: [waterfront] "Cargo Winch (foot): ABSENT — The cargo winch machine is not present anywhere on the lower quays or decks in this frame."

## 2. Survivors by bucket

### known (23)

- [shelf-west/checklist/navigation/sev3] the route between Valley Gate and Inn: ABSENT — The specified straight stair flight path is not visible in this view.
- [shelf-west/checklist/navigation/sev3] the way out of this area on foot towards gate: ABSENT — The egress route toward the gate does not extend out of frame here.
- [shelf-west/checklist/navigation/sev3] the way out of this area on foot towards shelf-east: ABSENT — No path exiting toward shelf-east appears in this frame.
- [quay-west/naive/navigation/sev2] The blocky stone staircase descends into absolute darkness and an ambiguous crevasse, making it unclear if it is a playable path or a dead end.
- [quay-west/checklist/navigation/sev3] the way out of this area on foot towards lockhead: ABSENT — There is no identifiable path or exit leading towards lockhead visible in this frame.
- [quay-west/checklist/navigation/sev3] the way out of this area on foot towards weave: ABSENT — There is no identifiable path or exit leading towards weave visible in this frame.
- [crossing/naive/immersion/sev1] A wooden plank floats disconnectedly on the water surface without buoyant interaction or support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 99.9,106.8,30.7,37.6
- [crossing/naive/geometry/sev1] Walkway planks and stair structures are disconnected and float without clear structural support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 69.3,87.3,20.9,38.8
- [crossing/checklist/navigation/sev3] Dam Crest Gate: VISIBLE-BUT-ILLEGIBLE — The gate structure on the high dam walk is obscured in deep shadow under its roof frame. _(also on lockfive, north-landing)_
- [deep-stairs/naive/occlusion/sev2] Harsh, pitch-black cast shadows completely obscure the cliff stairs and pathway, hiding where the player can walk.
- [deep-stairs/naive/geometry/sev1] The long descending wooden staircase lacks supporting beams underneath, appearing to float unsupported over the drop.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 33.1,47.8,17.9,23
- [deep-stairs/naive/geometry/sev1] The wooden walkway planks clip awkwardly into the rocky terrain and float above the ground level without proper support posts.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 31.7,44.6,18.8,29.9
- [deep-stairs/naive/immersion/sev2] The staircase steps float in mid-air without structural support columns connecting them to the ground or wall.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 32.7,49.1,17.6,29.2
- [deep-stairs/naive/navigation/sev2] Deep shadow completely hides the path ahead, making it ambiguous whether the staircase leads to a usable upper level or a dead end.
- [waterfront/naive/geometry/sev2] A wooden plank platform floats in mid-air across the water channel without any visible attachment or support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 37.1,43.7,22.1,28.7
- [waterfront/naive/geometry/sev2] A wooden plank platform floats completely unsupported in mid-air over the narrow water gap.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 37.3,43.7,22.3,28.8
- [lockfive/naive/geometry/sev2] The wooden stair steps float individually in mid-air without visible stringers or support posts beneath them.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 67.3,85,21.2,30.3
- [lockfive/naive/geometry/sev2] The wooden stair treads float individually without stringers or side beams supporting them from the dock or cliff face.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 66.5,85,21.2,32.6
- [lockfive/naive/geometry/sev2] The wooden stair treads leading upward lack support stringers on their outer edge, making them appear floating.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 64.2,91.2,23.6,30
- [lockfive/checklist/navigation/sev3] the way out of this area on foot towards north-landing: ABSENT — The path to the north-landing beyond the lock is not visible in this frame.
- [north-landing/naive/immersion/sev1] A green wooden plank floats on the water without any visible framing, posts, or connection to the nearby dock.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 97.2,106.3,31.2,36.9
- [north-landing/naive/geometry/sev1] The rectangular stepping stones float visually on top of the water surface without visible bases or underwater geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 86.9,95.2,33.1,42.3
- [north-landing/naive/immersion/sev1] A wooden plank platform floats flat on the water surface without any visible support posts or flotation structures.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 97.2,105.6,31.1,36.9

### new (72)

- [gate/naive/immersion/sev1] The vertical banners hanging on the cliff wall are embedded directly into the rock face without visible mounting poles, ropes, or anchors.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 8.6,25.6,-1.4,4.2
- [gate/naive/geometry/sev1] The tree trunk cuts straight into the cliff face with an unblended, sharp intersection and no visible root system.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region -1.1,2.9,-0.7,3.6
- [gate/naive/geometry/sev1] The trees on the right wall clip directly out of the vertical rock face without realistic trunks or visible roots.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region -0.7,13.7,-6.7,4.4
- [gate/naive/geometry/sev1] Sharp, unrefined low-polygon cliff geometry with severely stretched textures protrudes prominently into the foreground.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region -2.4,9.9,-6.5,6
- [gate/checklist/immersion/sev3] The world at the frame edges: WEAK — Dense cloud layer cuts off somewhat abruptly against cliff geometry. _(also on shelf-east, weave, waterfront, north-landing)_
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 14.7,145.3,-1.8,72.6
- [shelf-west/naive/geometry/sev2] The angled structural support beams under the upper platform terminate floating in mid-air without touching any lower wall or support frame.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 17.3,26.3,-0.5,11.6
- [shelf-west/naive/geometry/sev2] The diagonal cable/rope intersects and clips straight through the edge of the wooden walkway floor.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 30.7,38.1,3.8,12
- [shelf-west/naive/immersion/sev2] The diagonal wooden support beams beneath the upper platform terminate in mid-air without connecting to any wall or support below.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 17.3,32.2,4.4,12.4
- [shelf-west/naive/geometry/sev2] The diagonal support beams under the upper deck clip directly through the tiled roof of the house below.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 19.9,32.6,3.4,12.6
- [shelf-west/naive/geometry/sev1] The diagonal wooden support beams end in mid-air without connecting to the cliff face or any underlying structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 17.3,26.3,-0.6,12
- [shelf-west/checklist/occlusion/sev2] the route between Item Shop (chandlery skin) and Weapon Shop: OCCLUDED — The rear serpentine path is hidden behind shop buildings and upper decking.
- [shelf-east/naive/geometry/sev2] Untextured greybox pillars stand in the background, appearing as incomplete developer geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region -89.4,25.8,16.9,77.3
- [shelf-east/naive/immersion/sev1] The lantern light fixture protrudes directly from the roof tile without any mounting bracket or beam support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 46.5,53.6,3.3,8.6
- [shelf-east/naive/geometry/sev1] The roof of the upper-left building clips directly into the rock wall without any structural transition or framing.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 19.1,36.5,-0.7,5
- [shelf-east/naive/immersion/sev1] Untextured greybox pillars stand visible in the background ravine, breaking visual consistency.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region -89.4,42.1,9.5,77
- [shelf-east/naive/geometry/sev1] The stone chimney rests directly on top of the wooden roof shingles without proper joining or intersecting geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 47.6,52,1.4,5.6
- [shelf-east/checklist/navigation/sev3] Weapon Shop: ABSENT — No weapon props are visible anywhere in the scene.
- [shelf-east/checklist/navigation/sev3] Armor Shop: ABSENT — No armor props are displayed on or inside the structures.
- [shelf-east/checklist/navigation/sev2] a door / entrance you can go through ("Enter Weapon Shop"): VISIBLE-BUT-ILLEGIBLE — Shaded wall cavity lacks clear door framing or interactive detail.
- [shelf-east/checklist/navigation/sev2] a door / entrance you can go through ("Enter Armor Shop"): VISIBLE-BUT-ILLEGIBLE — Recessed shadow area does not clearly define an entrance way.
- [shelf-east/checklist/navigation/sev2] Cookhouse: VISIBLE-BUT-ILLEGIBLE — Appears as a standard wooden house without identifying cookhouse traits. _(also on deep-stairs)_
- [shelf-east/checklist/navigation/sev2] Inn: VISIBLE-BUT-ILLEGIBLE — Reads as a generic residence rather than a distinct inn.
- [quay-west/naive/geometry/sev2] A solid black unlit/untextured block intersects the central path, appearing as floating broken geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 40.8,52.7,7.8,17.2
- [quay-west/naive/geometry/sev2] A dark flat geometry plane is floating horizontally in mid-air between the buildings.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 40.1,52.5,7.7,20.2
- [quay-west/naive/navigation/sev2] The visual hierarchy lacks clear contrast, leading lines, or signage to differentiate walkable paths from background architecture.
- [quay-west/naive/geometry/sev2] A dark, untextured rectangular geometric artifact floats horizontally across the central pathway.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 40.6,52.7,7.9,17.3
- [quay-west/naive/navigation/sev2] Harsh directional shadows and monochrome textures make it difficult to distinguish walkable ledges from steep drops.
- [crossing/naive/geometry/sev2] Untextured greybox geometry is visible protruding at the bottom-right edge of the screen.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.5,69.9,12.7,17.2
- [crossing/naive/navigation/sev2] Harsh, pitch-black cast shadows completely obscure the walkway surface, hiding path boundaries and potential drops.
- [crossing/naive/geometry/sev1] An untextured solid white triangle of geometry protrudes into the bottom right corner of the screen.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.5,70.1,12.7,17.2
- [crossing/naive/immersion/sev1] A flat wooden platform floats independently on the water surface without visible supports or buoyant structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 100.2,106.8,30.8,37.6
- [crossing/naive/geometry/sev2] An untextured white geometric plane is visible cutting into the terrain at the bottom-right corner.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.5,70,12.7,17.2
- [crossing/naive/immersion/sev2] A flat roof canopy floats in mid-air above the path without visible structural supports.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 79.7,94.7,11.8,18.3
- [crossing/naive/immersion/sev1] A green board sits completely flat on top of the water surface with no visible support or depth.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 100.2,106.9,30.8,37.6
- [crossing/checklist/navigation/sev3] the route between Weave huts and Keepers' Cottage: ABSENT — No high sagging plank bridge spanning over the basin is present in this view.
- [weave/naive/navigation/sev2] The cave interior is pure black with no depth or light falloff, making it ambiguous whether it is a playable path.
- [weave/naive/navigation/sev2] Uniform brown coloration and dense layering of rooftops, ramps, and walkways make navigable paths visually indistinguishable from non-walkable roofs.
- [weave/naive/navigation/sev2] The pitch-black void inside the cliff opening gives no visual cues to indicate if it is a playable path or simple background geometry.
- [weave/naive/immersion/sev1] The upper wooden walkway platform clips directly into roof tiles without clear load-bearing support structures.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 47.2,61.8,7,21.7
- [deep-stairs/naive/occlusion/sev2] Extreme dark shadows obscure the interior space and passageway, making it impossible to gauge depth or see walkable paths.
- [deep-stairs/naive/geometry/sev1] The wooden plank walkway hovers above the rocky terrain without underlying support beams.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 31.7,44.6,18.8,29.9
- [deep-stairs/naive/geometry/sev2] The wooden stair treads hover over the ravine with no supporting structure or anchors connecting them to the terrain below.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 33.1,40.6,18.5,27.5
- [deep-stairs/checklist/immersion/sev2] The water surface: WEAK — The water reads as a flat, opaque teal plane that lacks surface movement, reflections, and soft shoreline blending where it meets the ground.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 36.8,44.6,23.7,29.9
- [boatyard/naive/geometry/sev1] The wooden roof slats on the upper-right structure are unattached and floating above the frame without visible fasteners or beam support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 0.5,8.7,17.6,25.2
- [boatyard/naive/geometry/sev2] Loose wooden roof planks hover in mid-air above the red building without structural attachments.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 0.9,9,17.6,24.8
- [boatyard/naive/immersion/sev2] The large boat rests at a steep angle floating/clipping into the surrounding roofing and shore structure without adequate visible physical support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 22.5,34.9,24.7,30.7
- [boatyard/checklist/navigation/sev3] Pitch kettle: ABSENT — There is no pitch kettle or curling tar smoke visible anywhere in the scene.
- [boatyard/checklist/navigation/sev3] Lock Four (set dressing): ABSENT — No upstream water lock structure is visible in this frame.
- [boatyard/checklist/navigation/sev3] the route between Boatwright's shed and Pitch kettle: ABSENT — Because the pitch kettle is absent, there is no route connecting to it.
- [waterfront/naive/navigation/sev2] The dense, overlapping wooden stairs and scaffolding lack clear visual contrast or path signposting, making the walkable route highly ambiguous.
- [waterfront/naive/immersion/sev2] A wooden boat hull is unnaturally clipped into the concrete wall structure at a steep angle.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 17.9,26,30.4,38.2
- [waterfront/naive/geometry/sev2] The wooden boat structure clips heavily through the solid grey wall on the right.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 17.9,25.6,30.6,38.3
- [waterfront/naive/navigation/sev2] Overlapping wooden ramps, stairs, and structural beams create visual clutter that makes walkable paths completely ambiguous.
- [waterfront/naive/immersion/sev2] The upper section of the wooden staircase terminates directly into the overhanging cliff face without clearance to walk.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 24.8,44.7,18.5,30
- [waterfront/naive/immersion/sev2] A wooden platform segment floats in mid-air without any supports connecting it to the surrounding terrain or structures.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 37.4,43.7,22.3,28.7
- [waterfront/naive/navigation/sev2] Multiple overlapping wooden ladders, staircases, and ramps intersect and blend into the rocky background, making it ambiguous which paths are walkable.
- [waterfront/naive/geometry/sev2] A wooden boat appears awkwardly suspended and clipping into the vertical concrete wall structure above the water.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 17.9,25.6,30.7,38.2
- [waterfront/checklist/navigation/sev3] Cargo Winch (foot): ABSENT — The cargo winch machine is not present anywhere on the lower quays or decks in this frame.
- [fishdock/naive/immersion/sev2] The green wooden dock structure appears to float mid-air directly above the small boat without any vertical posts or supports.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 44.7,52.3,26,34.4
- [fishdock/naive/immersion/sev2] A wooden platform floats in mid-air directly over a small wooden boat without any supporting posts or connections.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 44.7,52.4,26,34.5
- [fishdock/naive/immersion/sev2] A wooden platform appears to float unsupported in mid-air directly above and inside a small boat.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 44.7,52.4,26,34.4
- [fishdock/naive/geometry/sev1] An extremely long, thin wooden beam stretches diagonally down from the top right roof structure down to the lower dock without clear joints or support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 40,47.4,16.5,30
- [lockfive/naive/immersion/sev1] The body of water ends abruptly in a flat black void without cliff base geometry or horizon blending.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 85.5,147.3,26.5,53.1
- [lockfive/naive/navigation/sev2] Multiple broken, overlapping boardwalk layers and disjointed platforms make the playable path through the lower docks confusing and ambiguous.
- [lockfive/naive/immersion/sev2] The massive cliff face on the left uses a flat, stretched noise texture that terminates abruptly into a black void at the waterline.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 72.6,153,-0.8,50.8
- [lockfive/naive/navigation/sev2] The dock walkway disintegrates into tilted, submerged planks, making it ambiguous whether this is a valid walking path or impassable terrain.
- [north-landing/naive/immersion/sev1] Cone-shaped foliage objects stick out horizontally from the vertical cliff face without trunks or roots.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 98.2,102.6,19.3,23
- [north-landing/naive/geometry/sev2] The cliff mesh terminates abruptly, revealing the empty black void outside the map bounds.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 100.2,106.4,16.6,21.1
- [north-landing/naive/navigation/sev2] An open square hole in the wooden deck lacks railing or clear path indicators, creating ambiguous navigation and a fall hazard.
- [north-landing/naive/geometry/sev1] Stylized conical plant meshes stick horizontally out of the vertical rock wall at unnatural angles, looking like improperly aligned assets.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 96.6,107.7,18.2,26
- [north-landing/naive/navigation/sev2] An open square cutout in the wooden platform lacks railings or a visible ladder, making it unclear if it is an intended entry point or a floor hazard.
- [north-landing/naive/navigation/sev1] The path of stepping stones in the water abruptly ends near the dam wall, leaving the intended route forward ambiguous.

### style-bar (0)



## 2b. Aim census — did the judge point at what it named?

0 of 6 [QUALITY] verdicts REFUTED: the judge's own box held under 2% of the subject the verdict names. 1 on-subject, 0 absence-claim (census abstains), 5 unmeasurable.

- `quality:frame-edge-world` — 0/5 refuted; box coverage n/a
- `quality:water-read` — 0/1 refuted; box coverage 54.5%


## 3. Budget

71 calls, 122082 prompt + 141784 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.