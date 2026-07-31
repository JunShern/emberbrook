# Scene red-team — dellhollow — run 20260731-dellhollow2

judge `gemini:gemini-3.6-flash (replayed from run-20260731-dh2-fresh + run-20260731-dellhollow)` (pinned) · 16 plates · naive + checklist

## 0. Which plates were judged this round

| plate | critique | replies from | bake judged against | survivors |
|---|---|---|---|---|
| gate | **FRESH** | run-20260731-dh2-fresh | 2026-07-31T17:30:28Z | 16 |
| shelf-west | **REPLAYED** | run-20260731-dellhollow | 2026-07-31T14:25:13Z — AGAINST-SUPERSEDED-BAKE (shipped is now 2026-07-31T17:04:24Z) | 13 |
| shelf-east | **REPLAYED** | run-20260731-dellhollow | 2026-07-31T02:32:12Z — AGAINST-SUPERSEDED-BAKE (shipped is now 2026-07-31T17:30:28Z) | 6 |
| loop-stairs | **FRESH** | run-20260731-dh2-fresh | 2026-07-31T13:24:41Z | 9 |
| quay-west | **REPLAYED** | run-20260731-dellhollow | 2026-07-31T13:24:41Z | 9 |
| lockhead | **FRESH** | run-20260731-dh2-fresh | 2026-07-30T21:31:37Z | 6 |
| cottage | **FRESH** | run-20260731-dh2-fresh | 2026-07-30T21:31:37Z | 11 |
| crossing | **REPLAYED** | run-20260731-dellhollow | 2026-07-30T23:01:04Z | 3 |
| weave | **REPLAYED** | run-20260731-dellhollow | 2026-07-30T21:31:37Z | 3 |
| deep-stairs | **REPLAYED** | run-20260731-dellhollow | 2026-07-30T21:31:37Z | 8 |
| boatyard | **REPLAYED** | run-20260731-dellhollow | 2026-07-30T23:01:04Z | 10 |
| waterfront | **REPLAYED** | run-20260731-dellhollow | 2026-07-30T21:31:37Z | 8 |
| fishdock | **REPLAYED** | run-20260731-dellhollow | 2026-07-30T21:31:37Z | 4 |
| cottage-steps | **FRESH** | run-20260731-dh2-fresh | 2026-07-30T23:01:04Z | 9 |
| lockfive | **REPLAYED** | run-20260731-dellhollow | 2026-07-30T23:01:04Z | 8 |
| north-landing | **REPLAYED** | run-20260731-dellhollow | 2026-07-30T21:31:37Z | 8 |

## 1. Calibration

**On the user's own five complaints, the judge found 3 outright and 1 weakly (4/5), and raised 100 extra surviving findings.** (hand-adjudicated; the pre-registered keyword matcher scores 2/5 exact / 4/5 any-plate on the same run and over-credits.)

- **Canopy wall across the entrance** — WEAK (adjudicated: The user's complaint was 'the only way IN is behind foliage'. On the OLD gate plate the naive mode said so outright in 3 of 3 looks and the matcher agreed; on the NEW vista framing not one look mentions canopy, foliage or the entrance being hidden, and the matcher now scores MISS. What the judge does say is the CONSEQUENCE without the CAUSE: the checklist mode returns ABSENT for Valley Gate, the toll gatehouse, the Porters' Yard, all three roads off the gate, the way out towards shelf-west and the 'Leave Dellhollow' portal — seven items — and the ray census independently puts every one of them ON SCREEN AND OCCLUDED, behind something 3.25 to 8.46 m nearer, at charPx 25-29. So the entrance is still not findable and an instrument seconds it; the judge simply no longer names foliage as the reason. WEAK, not HIT: the finding is about legibility of the entrance, which is the complaint, but the object the user circled is not what the judge described. 96114cc already recorded this cost in its own commit message (portal arrival 32.1% -> 0.0% chest, 18 of 18 rays blocked by veg_gate_rimclump_26), so the cause is on record even though this run did not re-derive it.)
    - naive: miss
    - checklist: miss
- **The gate stair is occluded / hard to navigate** — HIT (adjudicated: Unchanged from the previous read and carried on the SAME replies: found by the CHECKLIST mode on shelf-west, which owns the valley-gate__inn flight — 'ABSENT - Cliffside S-bend staircase is not shown' — while the ray census puts that flight's midpoint on screen and unoccluded. CAVEAT, AND IT MATTERS: shelf-west was re-baked at 2026-07-31T17:04:24Z and these replies are about the 14:25:13Z bake, so the row is marked against-superseded-bake in section 4. The gate stair itself was rebuilt one commit earlier (gs_rail) and 96114cc measured gate-visible 32.9% -> 37.8%; this verdict therefore describes a plate that has since been worked on and needs re-judging before anyone acts on it. The matcher still credits this row for the wrong finding (a deep-stairs complaint two plates away) because its key list has no synonym for 'not shown'; left unfixed on purpose.)
    - naive: [deep-stairs] "A bright plain untextured diagonal ramp clips into the wooden staircase, appearing as leftover blockout geometry." | [deep-stairs] "The staircase consists of fragmented, floating wooden platforms without clear supports or continuous paths, making it ambiguous where the player can walk."
    - checklist: miss
- **Stray / weird cliff geometry** — HIT (adjudicated: REVERSED from the previous read, and the reason is the new plate rather than a new opinion. Last round every keyword match was a coincidence on the words 'cliff' and 'clip' and nothing said the cliff geometry itself was malformed — so it was scored a miss against the stated test 'does any finding say the cliff geometry itself is stray, malformed or unfinished'. On the vista framing three of three looks say exactly that, in three phrasings: 'the cliff geometry ends abruptly on the left edge with a flat vertical seam exposing empty space', 'abruptly cuts off into an unrendered black void edge on the left side of the screen', 'constructed from identical duplicated mesh blocks with noticeably repeating vertical groove patterns'. Confirmed by eye on the plate. Not the same piece of geometry the user circled — that one is out of frame now — but the same complaint, and it passes the test as it was written. THE JUDGE'S DIAGNOSIS IS STILL WRONG AND IT WAS MEASURED, see the extras note.)
    - naive: [gate] "The cliff geometry ends abruptly on the left edge with a flat vertical seam exposing empty space." | [gate] "The cliff geometry abruptly cuts off into an unrendered black void edge on the left side of the screen." | [gate] "The cliff geometry ends abruptly at a sharp vertical seam against a dark unrendered void beside the sky." | [shelf-west] "Green plant stalks clip directly onto the sheer vertical cliff surface with no visible soil or structural support."
    - checklist: miss
- **Solid plank screens where a rope fence belongs** — MISS (adjudicated: Unchanged and carried on the same replies; quay-west has not been re-baked since (bake 2026-07-31T13:24:41Z, still shipped). The green plank screens are plainly in the quay-west plate and no mode mentioned them in three looks plus a fifteen-item checklist. The matcher's 'hits' are a floating white stick and an armour-shop door. A rail that reads as a rail is invisible to a critic who has not been told the designer wanted to see through it.)
    - naive: [weave] "A thin white stick or cylinder floats unattached in mid-air in front of the cliff wall." | [waterfront] "Wooden step platforms beneath the covered pavilion float in mid-air without attachment to supports or walls."
    - checklist: [shelf-east] "a door / entrance you can go through ("Enter Armor Shop"): VISIBLE-BUT-ILLEGIBLE — Dark wall recesses are visible, but specific doorways remain obscure."
- **Waterfront: confusing / incomplete geometry, walking on water** — HIT (adjudicated: Unchanged and carried on the same replies; waterfront has not been re-baked (bake 2026-07-30T21:31:37Z). naive, on the exact plate: 'the visual similarity between roofs, walkways and steps creates path ambiguity across the multiple vertical levels' and 'disjointed platform levels and cliffside stairs create an ambiguous navigation path with unclear playable boundaries', corroborated on north-landing, fishdock, crossing, boatyard and lockfive. The walking-on-water half is still not reproducible: no plate composites a character.)
    - naive: [crossing] "A flat green rectangular plank floats isolated in mid-air over the water without support." | [crossing] "A flat wooden board floats unsupported above the water surface with no pillars or connection to the surrounding dock structure." | [crossing] "A flat rectangular plank floats horizontally above the water without any visual support or attachment." | [boatyard] "Wooden beams in the framework float in mid-air without attaching to the cliff face or supporting structure." | [boatyard] "The top-left end of the bunting line floats in mid-air without being attached to any post or roof structure." | [boatyard] "The wooden roof planks float disconnected above the structure of the red hut." | [waterfront] "Two wooden step platforms underneath the open shelter float in mid-air without attached supports." | [waterfront] "The visual similarity between roofs, walkways, and steps creates path ambiguity across the multiple vertical levels." | [waterfront] "Wooden step platforms beneath the covered pavilion float in mid-air without attachment to supports or walls." | [waterfront] "Disjointed platform levels and cliffside stairs create an ambiguous navigation path with unclear playable boundaries." | [fishdock] "A wooden platform floats in mid-air directly above a small boat without any visible legs or structural support." | [fishdock] "A green wooden platform is floating unsupported in mid-air directly above a small boat." | [fishdock] "The horizontal wooden segments between the posts in the water are floating disconnected in mid-air." | [fishdock] "The rectangular green dock platform floats unnaturally directly above the small wooden boat." | [lockfive] "The wooden railing structure floats over the water with its left end hanging unattached in mid-air." | [lockfive] "The grey upper platform plane floats above the circular wooden deck and clips directly through the vertical support post." | [north-landing] "A flat green wooden plank floats on the water without any visible supports or connection to the nearby structures." | [north-landing] "Disjointed grey platform slabs float flat on the water surface without proper anchoring or water interaction." | [north-landing] "Dense and overlapping wooden beams along the cliff face obscure navigable paths and walkways, making it hard to see where to go." | [north-landing] "Plain grey geometric blocks sit disjointed on the water surface, appearing like unfinished geometry." | [north-landing] "A green rectangular board floats completely flat on top of the water without support or physical contact." | [north-landing] "The dense clutter of overlapping wooden beams, platforms, and stairways makes it visually ambiguous which paths are walkable." | [north-landing] "The open gap in the circular platform exposes chaotic wooden supports, making it unclear whether it is a drop hazard, a hole, or navigable terrain."
    - checklist: miss

## 2. Survivors by bucket

### known (28)

- [gate/checklist/navigation/sev3] the way out of this area on foot towards shelf-west: ABSENT — No path leading off-screen to shelf-west can be identified. _(also on shelf-west)_
- [gate/checklist/navigation/sev3] a door / entrance you can go through ("Leave Dellhollow"): ABSENT — No exit door or transition entrance marked for leaving the area is present.
- [shelf-east/checklist/navigation/sev3] the way out of this area on foot towards shelf-west: ABSENT — No path exiting off-screen to the west is visible due to rock walls and bamboo.
- [shelf-east/checklist/navigation/sev3] the way out of this area on foot towards loop-stairs: ABSENT — No continuous path leading out of the frame toward stairs is visible. _(also on loop-stairs)_
- [loop-stairs/naive/immersion/sev1] Wooden planks and poles near the top right cliff edge appear to float unsupported in mid-air.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 43.6,52.2,-1.4,13.7
- [loop-stairs/naive/navigation/sev2] Disjointed floating wooden blocks act as steps along the wall, making it unclear if they are navigable platforms or decorative debris.
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
- [cottage-steps/naive/immersion/sev2] A sequence of square stepping blocks floats completely unsupported in mid-air near the ladder base.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 80.8,88.1,24.2,29.2
- [cottage-steps/naive/immersion/sev2] A series of wooden step blocks float in mid-air near the ladder without structural framing or supports beneath them.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 81,88.4,24.1,29.2
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

### new (103)

- [gate/naive/geometry/sev2] The cliff geometry ends abruptly on the left edge with a flat vertical seam exposing empty space.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 88.2,144.1,8,27.5
- [gate/naive/immersion/sev1] The background rock face has noticeably repetitive modular column ridges that break the visual immersion of a natural environment.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 53.3,98.9,-1.8,21
- [gate/naive/navigation/sev2] Dense, uniform wooden beams and overlapping stairs blend together into the cliff shadow, making navigable paths difficult to discern.
- [gate/naive/immersion/sev2] The cliff geometry abruptly cuts off into an unrendered black void edge on the left side of the screen.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 48.3,130.8,-6.1,1.6
- [gate/naive/immersion/sev1] The cliff face is constructed from identical duplicated mesh blocks with noticeably repeating vertical groove patterns.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 58.9,142.7,-3.4,19.8
- [gate/naive/immersion/sev2] The cliff geometry ends abruptly at a sharp vertical seam against a dark unrendered void beside the sky.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 87.8,143.9,8.2,27.7
- [gate/naive/immersion/sev1] The cliff wall uses visibly repeating tiled geometry blocks, creating noticeable grid patterns.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 49.5,98.9,-1.8,21
- [gate/naive/navigation/sev2] Dense visual clutter of overlapping wooden stilts, stairs, and roofs makes it difficult to discern walkable paths from scenery.
- [gate/checklist/navigation/sev3] Valley Gate: ABSENT — No town gate with arch or palisade is visible anywhere in this scene.
- [gate/checklist/navigation/sev3] Gatehouse (toll): ABSENT — There is no recognisable toll gatehouse building in view.
- [gate/checklist/navigation/sev3] Porters' Yard: ABSENT — No yard with pack mules or portage crews is visible in the frame.
- [gate/checklist/navigation/sev3] the route between Valley Gate and Gatehouse (toll): ABSENT — The road connecting Valley Gate and Gatehouse is not present because neither structure is shown.
- [gate/checklist/navigation/sev3] the route between Valley Gate and Cargo Winch (head): ABSENT — The road leading from the gate to the winch head is not shown in this camera frame.
- [gate/checklist/navigation/sev3] the route between Valley Gate and Porters' Yard: ABSENT — The road to the porters' yard is absent along with the gate and yard.
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
- [shelf-east/naive/immersion/sev2] Glowing orange shapes clip through the wooden crates and terrain without any visible fixtures or containers.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 41.4,53.1,2.1,13.4
- [shelf-east/checklist/navigation/sev2] Armor Shop: VISIBLE-BUT-ILLEGIBLE — The building structure is visible on the cliffside, but lacks distinct armor signs or displays.
- [shelf-east/checklist/navigation/sev2] a door / entrance you can go through ("Enter Armor Shop"): VISIBLE-BUT-ILLEGIBLE — Dark wall recesses are visible, but specific doorways remain obscure.
- [shelf-east/checklist/navigation/sev2] Cookhouse: VISIBLE-BUT-ILLEGIBLE — A wooden building is present, but lacks indicators like warm lit windows or tavern cues. _(also on deep-stairs)_
- [loop-stairs/naive/geometry/sev2] An untextured flat white block cuts through the terrain, looking like unfinished prototype geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 57.8,64.2,10.8,18.4
- [loop-stairs/naive/immersion/sev1] Severe vertical texture stretching is visible along the rock wall face.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 59.4,74.4,-5.3,9.8
- [loop-stairs/naive/geometry/sev2] The texture on the left cliff wall is severely stretched vertically, creating a smeared visual artifact.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 56.1,79.6,-5.6,17.3
- [loop-stairs/naive/geometry/sev2] A flat, untextured white rectangular plane cuts through the ground without matching the surrounding environment.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 57.8,66.1,10.8,18.4
- [loop-stairs/naive/navigation/sev2] The center wooden structure consists of fragmented pillars and platforms with no clear walkable path or steps.
- [loop-stairs/naive/geometry/sev2] A flat, untextured greybox mesh strip is left exposed across the lower-left portion of the scene.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 57.9,81,-2.2,18.3
- [loop-stairs/naive/immersion/sev2] Severe vertical texture stretching distorts the cliff face, breaking visual consistency.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 59.4,74.6,-5.3,9.8
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
- [lockhead/naive/navigation/sev2] Large crates are placed directly along the narrow wooden walkway path, making it unclear whether this is a walkable route or an impassable barrier.
- [lockhead/naive/geometry/sev1] A ladder structure under the wooden walkway hangs in mid-air without connecting to any lower surface.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 79.4,83.7,15,19.1
- [lockhead/naive/geometry/sev1] Vertical wooden support posts terminate in mid-air without reaching the cliff wall below.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 71.2,75.9,13.6,17.9
- [lockhead/naive/geometry/sev1] Severe vertical UV texture stretching is visible across the steep rock wall.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 62.2,85.4,-3.7,15.5
- [lockhead/naive/immersion/sev1] The vertical cliff wall exhibits severe vertical texture stretching and harsh texture seam alignment.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 62,85.4,-3.7,15.7
- [lockhead/naive/navigation/sev2] A continuous line of repetitive crates completely clutters the narrow bridge deck, making it ambiguous whether this is a walkable path or an impassable obstacle.
- [cottage/naive/geometry/sev2] A pure black hole in the cliff wall appears to be a gap in the world mesh, lacking interior geometry or proper lighting.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 97.6,108,13.7,22.3
- [cottage/naive/immersion/sev1] Extreme vertical texture stretching on the upper cliff face creates obvious projection artifacts.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 88.4,111.9,-2.8,15.9
- [cottage/naive/navigation/sev2] The messy pile of collapsed wooden planks overlaps ambiguously, making it hard to tell if this is a traversable path or an impassable obstruction.
- [cottage/naive/geometry/sev2] A pure black cutout hole in the cliff face lacks lighting and texturing, appearing as missing geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 98.2,108,12.2,22.1
- [cottage/naive/geometry/sev1] The texture on the upper rock face is heavily stretched vertically relative to the rest of the terrain.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 88,108.7,-1.9,15.9
- [cottage/naive/navigation/sev2] The tangled pile of broken planks makes it ambiguous whether this section is a walkable incline or broken terrain.
- [cottage/naive/immersion/sev2] The ladder terminates directly into the railing of the lower walkway without an opening or proper landing platform.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 78.5,85.9,14.9,24.8
- [cottage/naive/geometry/sev2] The hole in the cliff face is completely pitch black with no depth or internal details, reading like missing geometry or broken lighting.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 98.3,108,12.2,22
- [cottage/naive/geometry/sev2] The shattered wooden platform segments clip chaotically into support beams and each other, making the visual structure hard to read.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 84.9,94.5,16,23.7
- [cottage/naive/navigation/sev2] The long ladder leads up directly into the underside of a platform overhang without a clear top landing or opening.
- [cottage/checklist/navigation/sev3] a door / entrance you can go through ("Enter Keepers' Cottage"): ABSENT — No door or doorway into the Keepers' Cottage is visible from this viewing angle.
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
- [cottage-steps/naive/immersion/sev1] Green conical bush models float in mid-air next to the rock face without visible attachment or support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 94.6,99,21.2,25.1
- [cottage-steps/naive/immersion/sev1] Yellowish rounded rock props hover freely in front of the cliff wall.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 93.5,98.5,19.3,23.3
- [cottage-steps/naive/immersion/sev1] A green tree model floats in mid-air off the cliff edge.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 93,97.4,17.3,22
- [cottage-steps/naive/navigation/sev2] Dense visual clutter from overlapping wooden beams, ladders, and supports makes it difficult to read walkable paths versus non-walkable structure.
- [cottage-steps/naive/immersion/sev1] The green plant shapes hover in mid-air off the cliff face without any visible support or root attachment to the rock.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 94.6,99,21.2,25.1
- [cottage-steps/naive/immersion/sev1] Stylized plant geometry floats against the vertical cliff wall without any visible soil or ledge support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 94.6,99,21.2,25.1
- [cottage-steps/naive/immersion/sev1] A green tree object hangs levitating off the vertical rock face without roots or a ground platform.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 92.9,97.4,17.3,22
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