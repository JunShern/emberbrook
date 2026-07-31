# Scene red-team — dellhollow — run 20260731-dellhollow

judge `gemini:gemini-3.6-flash (replayed from run-20260731-calib3)` (pinned) · 12 plates · naive + checklist

## 1. Calibration

**On the user's own five complaints, the judge found 3 outright and 0 weakly (3/5), and raised 56 extra surviving findings.** (hand-adjudicated; the pre-registered keyword matcher scores 3/5 exact / 5/5 any-plate on the same run and over-credits.)

- **Canopy wall across the entrance** — HIT (adjudicated: gate plate, 3 of 3 independent looks, unprompted: 'the thick foliage completely blocks the view of the walkway edge, hiding where it is safe to walk versus where the drop-off begins'. Same object and same consequence the user named. The matcher agrees.)
    - naive: [gate] "The thick foliage completely blocks the view of the walkway edge, hiding where it is safe to walk versus where the drop-off begins." | [gate] "Dense foliage along the foreground edge obscures the path behind it, hiding ground boundaries and potential hazards." | [gate] "Dense foliage along the foreground edge blocks sight of the walkway surface and edge, making safe footing hard to determine."
    - checklist: miss
- **The gate stair is occluded / hard to navigate** — HIT (adjudicated: Found by the CHECKLIST mode on shelf-west, which owns the valley-gate__inn flight: 'ABSENT - Cliffside S-bend staircase is not shown', while the ray census puts that flight's midpoint on screen and unoccluded. This is the map-informed mode doing exactly the job it was added for, and the naive mode never mentions a stair on either gate plate. THE MATCHER CREDITED THIS ROW FOR THE WRONG FINDING (a deep-stairs complaint two plates away): its pre-registered key list has no synonym for 'not shown'. Left unfixed on purpose - editing the keys to catch a hit you have already seen is tuning the metric to please the bake.)
    - naive: [deep-stairs] "A bright plain untextured diagonal ramp clips into the wooden staircase, appearing as leftover blockout geometry." | [deep-stairs] "The staircase consists of fragmented, floating wooden platforms without clear supports or continuous paths, making it ambiguous where the player can walk."
    - checklist: miss
- **Stray / weird cliff geometry** — MISS (adjudicated: Every keyword match is a coincidence on the words 'cliff' and 'clip': a cloth banner mounted flat on the cliff face, plant stalks clipping into the cliff, a waterfall clipping through rock. Not one finding says the cliff geometry itself is stray, malformed or unfinished. The matcher scores this a hit; it is not one.)
    - naive: [gate] "The cloth banner is attached flat to the sheer cliff face without any visible hooks, ropes, or mounting frame." | [shelf-west] "Green plant stalks clip directly onto the sheer vertical cliff surface with no visible soil or structural support."
    - checklist: miss
- **Solid plank screens where a rope fence belongs** — MISS (adjudicated: The green plank screens are plainly in the quay-west plate - verified by cropping the plate at the region the user circled - and no mode mentioned them in three looks plus a fifteen-item checklist. The matcher's 'hits' are a floating white stick and an armour-shop door. A rail that reads as a rail is invisible to a critic who has not been told the designer wanted to see through it.)
    - naive: [weave] "A thin white stick or cylinder floats unattached in mid-air in front of the cliff wall." | [waterfront] "Wooden step platforms beneath the covered pavilion float in mid-air without attachment to supports or walls."
    - checklist: [shelf-east] "a door / entrance you can go through ("Enter Armor Shop"): VISIBLE-BUT-ILLEGIBLE — Dark wall recesses are visible, but specific doorways remain obscure."
- **Waterfront: confusing / incomplete geometry, walking on water** — HIT (adjudicated: waterfront plate, naive: 'the visual similarity between roofs, walkways and steps creates path ambiguity across the multiple vertical levels' and 'disjointed platform levels and cliffside stairs create an ambiguous navigation path with unclear playable boundaries'. That is the user's 'extremely confusing / incomplete geometry' in the judge's own words, on the exact plate, and it is corroborated on north-landing, fishdock, crossing, boatyard and lockfive. The walking-on-water half is not reproducible: no plate composites a character.)
    - naive: [crossing] "A flat green rectangular plank floats isolated in mid-air over the water without support." | [crossing] "A flat wooden board floats unsupported above the water surface with no pillars or connection to the surrounding dock structure." | [crossing] "A flat rectangular plank floats horizontally above the water without any visual support or attachment." | [boatyard] "Wooden beams in the framework float in mid-air without attaching to the cliff face or supporting structure." | [boatyard] "The top-left end of the bunting line floats in mid-air without being attached to any post or roof structure." | [boatyard] "The wooden roof planks float disconnected above the structure of the red hut." | [waterfront] "Two wooden step platforms underneath the open shelter float in mid-air without attached supports." | [waterfront] "The visual similarity between roofs, walkways, and steps creates path ambiguity across the multiple vertical levels." | [waterfront] "Wooden step platforms beneath the covered pavilion float in mid-air without attachment to supports or walls." | [waterfront] "Disjointed platform levels and cliffside stairs create an ambiguous navigation path with unclear playable boundaries." | [fishdock] "A wooden platform floats in mid-air directly above a small boat without any visible legs or structural support." | [fishdock] "A green wooden platform is floating unsupported in mid-air directly above a small boat." | [fishdock] "The horizontal wooden segments between the posts in the water are floating disconnected in mid-air." | [fishdock] "The rectangular green dock platform floats unnaturally directly above the small wooden boat." | [lockfive] "The wooden railing structure floats over the water with its left end hanging unattached in mid-air." | [lockfive] "The grey upper platform plane floats above the circular wooden deck and clips directly through the vertical support post." | [north-landing] "A flat green wooden plank floats on the water without any visible supports or connection to the nearby structures." | [north-landing] "Disjointed grey platform slabs float flat on the water surface without proper anchoring or water interaction." | [north-landing] "Dense and overlapping wooden beams along the cliff face obscure navigable paths and walkways, making it hard to see where to go." | [north-landing] "Plain grey geometric blocks sit disjointed on the water surface, appearing like unfinished geometry." | [north-landing] "A green rectangular board floats completely flat on top of the water without support or physical contact." | [north-landing] "The dense clutter of overlapping wooden beams, platforms, and stairways makes it visually ambiguous which paths are walkable." | [north-landing] "The open gap in the circular platform exposes chaotic wooden supports, making it unclear whether it is a drop hazard, a hole, or navigable terrain."
    - checklist: miss

## 2. Survivors by bucket

### known (25)

- [gate/naive/occlusion/sev2] The thick foliage completely blocks the view of the walkway edge, hiding where it is safe to walk versus where the drop-off begins.
- [gate/naive/occlusion/sev2] Dense foliage along the foreground edge obscures the path behind it, hiding ground boundaries and potential hazards.
- [gate/naive/occlusion/sev2] Dense foliage along the foreground edge blocks sight of the walkway surface and edge, making safe footing hard to determine.
- [shelf-east/checklist/navigation/sev3] the way out of this area on foot towards shelf-west: ABSENT — No path exiting off-screen to the west is visible due to rock walls and bamboo.
- [shelf-east/checklist/navigation/sev3] the way out of this area on foot towards loop-stairs: ABSENT — No continuous path leading out of the frame toward stairs is visible.
- [quay-west/checklist/navigation/sev3] the way out of this area on foot towards weave: ABSENT — There are no additional distinct paths exiting the frame beyond the identified routes.
- [crossing/naive/geometry/sev2] A flat green rectangular plank floats isolated in mid-air over the water without support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 99.8,108.6,30.2,37.8
- [crossing/naive/immersion/sev1] A flat wooden board floats unsupported above the water surface with no pillars or connection to the surrounding dock structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 101.7,108.7,30.9,37.9
- [crossing/naive/immersion/sev1] A flat rectangular plank floats horizontally above the water without any visual support or attachment.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 98.6,108.5,29.9,37.7
- [deep-stairs/naive/immersion/sev2] The individual wooden stair treads float in mid-air without structural supports connecting them to each other or the cliffside.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 26.2,36.9,17.4,21.5
- [deep-stairs/naive/geometry/sev2] A bright plain untextured diagonal ramp clips into the wooden staircase, appearing as leftover blockout geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 34.2,43.4,16.6,21.2
- [deep-stairs/naive/navigation/sev2] The staircase consists of fragmented, floating wooden platforms without clear supports or continuous paths, making it ambiguous where the player can walk.
- [deep-stairs/naive/geometry/sev2] The winding stair treads float in mid-air without structural support framing.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 35.4,44,16.9,27.6
- [boatyard/naive/immersion/sev2] The wooden roof planks float disconnected above the structure of the red hut.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 0.5,8.8,17.6,24.9
- [waterfront/naive/geometry/sev1] The wooden stair treads float unanchored along the cliff face without supporting stringers.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 29,40.5,18.5,23.5
- [waterfront/naive/immersion/sev2] Two wooden step platforms underneath the open shelter float in mid-air without attached supports.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 36.4,43.5,22.4,28.1
- [waterfront/naive/geometry/sev2] Wooden step platforms beneath the covered pavilion float in mid-air without attachment to supports or walls.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 36.5,43.4,22.4,28
- [lockfive/naive/geometry/sev2] The grey upper platform plane floats above the circular wooden deck and clips directly through the vertical support post.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 60.2,70.1,17.4,31.4
- [lockfive/checklist/navigation/sev3] Lock Five: ABSENT — No canal lock basin or lock gates exist in this open bay environment.
- [lockfive/checklist/navigation/sev3] the way out of this area on foot towards fishdock: ABSENT — No separate foot path leading towards a fishdock exits the edge of the frame.
- [lockfive/checklist/navigation/sev3] the way out of this area on foot towards cottage-steps: ABSENT — No foot path leading towards cottage-steps exits the frame.
- [lockfive/checklist/navigation/sev3] the way out of this area on foot towards north-landing: ABSENT — No foot path leading towards north-landing exits the frame.
- [north-landing/naive/immersion/sev2] A flat green wooden plank floats on the water without any visible supports or connection to the nearby structures.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 97.2,105.6,31.1,36.9
- [north-landing/naive/geometry/sev1] Disjointed grey platform slabs float flat on the water surface without proper anchoring or water interaction.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 86.8,95.2,32.9,42
- [north-landing/naive/immersion/sev1] A green rectangular board floats completely flat on top of the water without support or physical contact.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 97.3,105.6,31.1,37

### new (63)

- [gate/naive/immersion/sev1] The cloth banner is attached flat to the sheer cliff face without any visible hooks, ropes, or mounting frame.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 16.4,27.4,-1.1,2.1
- [gate/naive/navigation/sev2] The wooden structures and pathway on the lower left drop out of view into shadow and geometry clutter, making it ambiguous where the player can move downward.
- [gate/naive/navigation/sev2] The lower pathway beneath the cliff platform is heavily shadowed and obscured, making it unclear whether it is navigable space.
- [gate/naive/navigation/sev2] The path descending underneath the platform vanishes into heavy shadow, making it ambiguous whether it continues as a playable route.
- [shelf-west/naive/occlusion/sev2] Extremely dense dark shadows under the upper platform obscure the pathway and ground terrain completely, making spatial navigation unclear.
- [shelf-west/naive/geometry/sev2] Diagonal wooden support struts clip cleanly through the green tiled roof below.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 22.6,30.7,3.2,12.1
- [shelf-west/naive/geometry/sev1] Green plant stalks clip directly onto the sheer vertical cliff surface with no visible soil or structural support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 15.2,20,9.8,13.4
- [shelf-west/naive/occlusion/sev2] Deep pitch-black shadow obscures all details and potential paths underneath the upper platform.
- [shelf-west/naive/occlusion/sev2] Deep black shadow completely hides the space beneath the upper deck, making it impossible to see if there is a path or entrance.
- [shelf-west/naive/navigation/sev2] The floor drops abruptly into shadow without clear railing or edge definition, making walkable boundaries ambiguous.
- [shelf-west/checklist/navigation/sev2] Item Shop (chandlery skin): VISIBLE-BUT-ILLEGIBLE — Building lacks clear identifiers defining it as a chandlery or item shop.
- [shelf-west/checklist/navigation/sev3] Weapon Shop: ABSENT — Not visible anywhere in the frame. _(also on shelf-east)_
- [shelf-west/checklist/navigation/sev3] the route between Valley Gate and Inn: ABSENT — Cliffside S-bend staircase is not shown.
- [shelf-west/checklist/navigation/sev3] the route between Item Shop (chandlery skin) and Weapon Shop: ABSENT — Not present in the view.
- [shelf-west/checklist/occlusion/sev2] a door / entrance you can go through ("Enter The Boatmen's Rest"): OCCLUDED — Hidden behind the illuminated front stall counter.
- [shelf-west/checklist/navigation/sev3] a door / entrance you can go through ("Enter Item Shop"): ABSENT — No distinct entrance visible on the left building.
- [shelf-west/checklist/navigation/sev3] a door / entrance you can go through ("Enter Weapon Shop"): ABSENT — Not visible in frame.
- [shelf-west/checklist/navigation/sev2] the way out of this area on foot towards gate: VISIBLE-BUT-ILLEGIBLE — Extremely cropped ground segment at the left edge.
- [shelf-east/naive/immersion/sev2] Glowing orange shapes clip through the wooden crates and terrain without any visible fixtures or containers.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 41.4,53.1,2.1,13.4
- [shelf-east/checklist/navigation/sev2] Armor Shop: VISIBLE-BUT-ILLEGIBLE — The building structure is visible on the cliffside, but lacks distinct armor signs or displays.
- [shelf-east/checklist/navigation/sev2] a door / entrance you can go through ("Enter Armor Shop"): VISIBLE-BUT-ILLEGIBLE — Dark wall recesses are visible, but specific doorways remain obscure.
- [shelf-east/checklist/navigation/sev2] Cookhouse: VISIBLE-BUT-ILLEGIBLE — A wooden building is present, but lacks indicators like warm lit windows or tavern cues. _(also on deep-stairs)_
- [quay-west/naive/geometry/sev2] The white stairs in the lower right foreground appear to be untextured greybox geometry, clashing visually with the rest of the stylized assets.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 35,43.7,16.1,21.4
- [quay-west/naive/geometry/sev2] A pink rectangular strip floats isolated in mid-air in front of the middle building structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 43.6,51.6,9.1,19.9
- [quay-west/naive/immersion/sev1] Orange geometry fragments float unattached in mid-air beneath the central platform.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 41.2,46.1,16.6,20.3
- [quay-west/naive/geometry/sev2] A bright magenta rectangular polygon floats in mid-air, indicating missing texture or stray debug geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 43.7,50.2,8.6,19.6
- [quay-west/naive/immersion/sev2] The white staircase appears completely untextured, resembling grey-box placeholder geometry in an otherwise textured scene.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 29.3,39.1,14.1,20.3
- [quay-west/naive/geometry/sev2] A bright pink untextured strip floats in mid-air across the central walking area.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 43.6,51.6,9.4,19.9
- [quay-west/naive/geometry/sev2] The staircase structure consists of plain, untextured greybox geometry contrasting with the surrounding scene.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 34.9,43.8,16.2,21.2
- [quay-west/checklist/navigation/sev2] a door / entrance you can go through ("Enter Cookhouse"): VISIBLE-BUT-ILLEGIBLE — The entrance area is shrouded in deep shadows, making it difficult to clearly identify as an interactive doorway.
- [weave/naive/geometry/sev2] A thin white pole or untextured line floats horizontally in mid-air near the cliff face.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.3,75.9,-5.4,17.3
- [weave/naive/geometry/sev2] A thin white stick or cylinder floats unattached in mid-air in front of the cliff wall.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.3,76.3,-4.2,17
- [weave/checklist/navigation/sev3] the route between Weave huts and Fish dock: ABSENT — No rickety ladder leading from the right-side huts down to a fish dock can be seen in the frame.
- [deep-stairs/naive/geometry/sev2] The stark grey angled ramps look like untextured placeholder geometry clipping awkwardly through the wooden staircase structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 38.2,50.9,16.6,23.6
- [deep-stairs/naive/navigation/sev2] Harsh cast shadows obscure the pathways and doorways, making it unclear where the player can walk or ascend.
- [deep-stairs/naive/geometry/sev2] The smooth beige ramp sections above the stairs appear untextured and look like unfinished placeholder geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 34,43.4,16.7,21.2
- [deep-stairs/naive/immersion/sev2] The large wooden boat hull clips directly into the surrounding boardwalk and wooden buildings.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 25.5,33.9,18.9,31.9
- [boatyard/naive/immersion/sev2] The roof and floor surfaces are completely pitch black, appearing to lack materials or lighting.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 5.4,18,30.2,42.7
- [boatyard/naive/geometry/sev1] Wooden beams in the framework float in mid-air without attaching to the cliff face or supporting structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 12,19.7,18.4,33.6
- [boatyard/naive/geometry/sev2] The structure on the bottom right consists of untextured matte-black blockout geometry mixed with textured props.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 5.4,18.8,29.8,42.7
- [boatyard/naive/immersion/sev1] The top-left end of the bunting line floats in mid-air without being attached to any post or roof structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 18.1,23,18.5,24.2
- [boatyard/naive/geometry/sev2] A wooden support beam clips directly through the hull of the elevated boat.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 22.8,27,25,33.5
- [boatyard/checklist/navigation/sev3] Pitch kettle: ABSENT — There is no smoking pitch kettle or tar smoke near the water visible in the scene.
- [boatyard/checklist/navigation/sev3] Lock Four (set dressing): ABSENT — No canal lock gates or staircase-of-water lock structure is drawn in this frame.
- [boatyard/checklist/navigation/sev3] the route between Cargo Winch (foot) and Slipway: ABSENT — The cargo winch and its connecting route deck are not present in this shot.
- [boatyard/checklist/navigation/sev3] the route between Boatwright's shed and Pitch kettle: ABSENT — Because the pitch kettle is absent, the deck route leading to it does not exist.
- [waterfront/naive/immersion/sev2] The wooden boat rests horizontally high up against the vertical sluice wall with no visible cradles or supports.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 17.9,25.6,30.6,38.2
- [waterfront/naive/navigation/sev2] The visual similarity between roofs, walkways, and steps creates path ambiguity across the multiple vertical levels.
- [waterfront/naive/immersion/sev1] The wooden stair treads protrude directly from the cliff face without support beams or anchors.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 32,40.7,18.8,24.3
- [waterfront/naive/navigation/sev2] Disjointed platform levels and cliffside stairs create an ambiguous navigation path with unclear playable boundaries.
- [waterfront/naive/immersion/sev1] Individual wooden stair steps stick directly out of the cliff wall without visible structural supports.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 29.2,39.9,18.5,23.3
- [fishdock/naive/immersion/sev2] A wooden platform floats in mid-air directly above a small boat without any visible legs or structural support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 44.4,52.4,26,35.7
- [fishdock/naive/immersion/sev2] A green wooden platform is floating unsupported in mid-air directly above a small boat.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 44.7,52.4,26,34.5
- [fishdock/naive/immersion/sev2] The horizontal wooden segments between the posts in the water are floating disconnected in mid-air.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 43.8,52,31.3,39.2
- [fishdock/naive/geometry/sev2] The rectangular green dock platform floats unnaturally directly above the small wooden boat.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 44.7,52.4,26,34.5
- [lockfive/naive/geometry/sev2] The staircase leads directly into the solid underside of the wooden platform above, with no cutout or hatchway to allow passage.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 59.2,66.4,25,30.1
- [lockfive/naive/geometry/sev1] The wooden railing structure floats over the water with its left end hanging unattached in mid-air.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 67.5,74,29.8,37.5
- [lockfive/checklist/navigation/sev3] Dam Crest Gate: ABSENT — No iron-banded dam crest gate is present anywhere in the frame. _(also on north-landing)_
- [north-landing/naive/navigation/sev2] Dense and overlapping wooden beams along the cliff face obscure navigable paths and walkways, making it hard to see where to go.
- [north-landing/naive/geometry/sev1] Plain grey geometric blocks sit disjointed on the water surface, appearing like unfinished geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 86.8,95.2,32.9,42
- [north-landing/naive/navigation/sev2] The dense clutter of overlapping wooden beams, platforms, and stairways makes it visually ambiguous which paths are walkable.
- [north-landing/naive/navigation/sev2] The open gap in the circular platform exposes chaotic wooden supports, making it unclear whether it is a drop hazard, a hole, or navigable terrain.
- [north-landing/checklist/navigation/sev2] Weave huts: VISIBLE-BUT-ILLEGIBLE — The huts blend into the general stilt structure along the cliff face without distinct features like laundry lines readable.

### style-bar (0)



## 3. Budget

0 calls, 0 prompt + 0 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.