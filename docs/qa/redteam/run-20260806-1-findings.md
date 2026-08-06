# Scene red-team 20260806-1 — flat findings list

First geometry/visual-quality sweep of the CURRENT world: 15 del-cine plates (baked 2026-08-06, commits 0c5f6d3/38ce143, HEAD da69f9a) and 11 dressed emb-cine plates (baked 2026-08-02, first sweep on current bytes).

Judge gemini-3.6-flash (pinned), temp 0.4, naive N=3 looks/plate. Emberbrook judged in ART mode (`--no-blockout`): the emb-cine plates are the dressed bake, so the blockout style bar no longer applies.
Naive pass ran first and unseeded (no checklist, no docs); checklist pass second, as shipped.
Full reports: `run-20260806-1-dellhollow/index.html`, `run-20260806-1-emberbrook/index.html`. Per-pass untouched records: `run-20260806-1-<town>-{naive,checklist}/`.

Confidence: naive findings carry `support` = how many of the N=3 independent looks raised it; checklist findings are single-look verdicts and carry the stage-2 channel that upheld them (ray-census = the plate's own depth agrees; adversarial-judge = a second sceptic call). The judge emits no numeric confidence; these are the only confidence signals the tool records.

## dellhollow — 100 surviving findings (25 refuted at stage 2)

### severity 3 (17)

- **boatyard** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: occluded
  > Pitch kettle: ABSENT — No pitch kettle or curling tar smoke is present in the scene.
- **boatyard** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: occluded
  > Lock Four (set dressing): ABSENT — No upstream water lock gates or Lock Four set dressing are visible in the scene.
- **boatyard** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: occluded
  > the route between Cargo Winch (foot) and Slipway: ABSENT — The cargo winch and its connecting deck route are not present in this view.
- **boatyard** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > the route between Boatwright's shed and Pitch kettle: ABSENT — The route cannot exist because the pitch kettle is absent.
- **lockfive** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: occluded
  > Dam Crest Gate: ABSENT — No iron-banded gate barring a dam crest path is visible in this frame.
- **lockfive** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > the way out of this area on foot towards north-landing: ABSENT — No third foot path exit is present in this view.
- **loop-stairs** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: occluded
  > the way out of this area on foot towards shelf-east: ABSENT — No path continuing off-screen to the east along the upper shelf is visible in the scene.
- **north-landing** · naive · geometry · sev 3 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > An untextured flat orange rectangle holding primitive grey blocks floats in mid-air without supports or material, appearing as unfinished placeholder geometry.
- **shelf-east** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > Weapon Shop: ABSENT — No shop weapons are visible in the scene.
- **shelf-east** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > Armor Shop: ABSENT — No armor pieces are visible on display.
- **shelf-west** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > the route between Item Shop (chandlery skin) and Weapon Shop: ABSENT — The road section leading to the Weapon Shop is not visible because the Weapon Shop is not in this shot.
- **shelf-west** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > the way out of this area on foot towards shelf-east: ABSENT — No path leading off-frame towards shelf-east is present in this view.
- **waterfront** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > Cargo Winch (foot): ABSENT — Cargo Winch (foot) is not visible in this scene.
- **waterfront** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: occluded
  > the route between Cargo Winch (foot) and Slipway: ABSENT — The route connected to the Cargo Winch is not present as the cargo winch is absent.
- **waterfront** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > the route between Fish dock and Cargo Winch (foot): ABSENT — The route between Fish dock and Cargo Winch is absent.
- **waterfront** · naive · geometry · sev 3 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The cliff surface is a single-sided paper-thin polygon sheet with no backface or volumetric geometry beneath it.
- **waterfront** · naive · geometry · sev 3 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The cliff surface ends abruptly as a paper-thin single-sided mesh, exposing a hollow gap underneath.

### severity 2 (64)

- **boatyard** · naive · immersion · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The large horizontal surfaces on the foreground structure appear as completely untextured, pitch-black voids.
- **boatyard** · naive · immersion · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Large sections of the building's lower structure are rendered as flat pitch-black blocks lacking textures and lighting, breaking visual consistency.
- **boatyard** · naive · immersion · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The line of colorful flags terminates floating in mid-air on the right side without any support or attachment point.
- **boatyard** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The lower portion of the building consists of completely flat, unshaded black geometry that lacks lighting and texture detail.
- **cottage** · checklist · occlusion · sev 2 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > a door / entrance you can go through ("Enter Keepers' Cottage"): OCCLUDED — The entrance to the cottage is hidden behind the wooden scaffolding and collapsed walkway timbers.
- **cottage** · naive · occlusion · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > An extremely dark shadow completely hides the terrain and potential pathways in the upper cave area.
- **cottage** · naive · navigation · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The broken, cluttered planks on the bridge make it ambiguous whether this is a traversable path or an impassable hazard.
- **cottage** · naive · occlusion · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Extremely pitch-black shadow completely obscures the structure and potential path behind the cliff face.
- **cottage** · naive · navigation · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The central elevated ramp is heavily broken into fragmented planks, creating ambiguity as to whether it is a walkable path or impassable obstacle.
- **cottage** · naive · immersion · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A row of small orange boxes floats in mid-air across the gap without any visible ropes, platforms, or supports.
- **cottage** · naive · occlusion · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Harsh, pitch-black cast shadows completely obscure the terrain and background structures, making the spatial layout unreadable.
- **cottage** · naive · navigation · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The central elevated ramp is heavily collapsed and fragmented, leaving it ambiguous whether it serves as a playable path or a dead-end hazard.
- **crossing** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A plain, untextured light-grey blockout polygon covers the lower right corner of the frame.
- **crossing** · naive · occlusion · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Pitch-black shadow completely obscures the left half of the environment, making depth and layout impossible to read.
- **crossing** · naive · occlusion · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Pitch-black shadows completely cover the upper left wall and canyon, obscuring the scale and depth of the space.
- **crossing** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A flat turquoise rectangular plane floats in mid-air under the platform structure.
- **crossing** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > An untextured light-grey block clips into the foreground right in front of the camera.
- **crossing** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > An untextured grey and white block clips into the foreground view, appearing as unfinished or placeholder geometry.
- **crossing** · naive · immersion · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A flat grey rectangular plane floats in mid-air without any supporting structure.
- **crossing** · naive · navigation · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A continuous line of stacked blocks completely obstructs the narrow sloped path, leaving it ambiguous whether it is an accessible route or a barrier.
- **deep-stairs** · naive · geometry · sev 2 · confidence: 2/3 looks; upheld by adversarial-judge:naive
  > The wooden stair treads float in mid-air without visible structural supports, posts, or stringers underneath.
- **deep-stairs** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Individual stair treads hover in mid-air along the cliffside without visible stringers or structural support underneath.
- **fishdock** · naive · navigation · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Extremely dark pitch-black shadows obscure the ground and stilt structure, making it impossible to read vertical depth or determine if there are walkable paths below.
- **fishdock** · naive · navigation · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Multiple overlapping wooden staircases and broken platforms visually clutter the cliff face, making walkable routes ambiguous.
- **lockfive** · naive · navigation · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Extremely dark lighting leaves the left half of the environment completely unlit, obscuring navigable space and terrain context.
- **lockfive** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The wooden stairs and support beams clip directly into adjacent platform edges and structures, creating disjointed geometry.
- **lockfive** · naive · navigation · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Dense, visually cluttered wooden beams and overlapping platforms make navigable paths hard to distinguish from background structure.
- **lockfive** · naive · immersion · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Extremely dark shadow on the left completely hides geometry and creates an unnatural pitch-black void.
- **lockfive** · naive · navigation · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Overlapping, densely cluttered wooden platforms and posts obscure which paths are walkable or visual obstacles.
- **lockfive** · naive · occlusion · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Extreme darkness on the left side conceals spatial boundaries and depth, making the environment hard to parse.
- **lockhead** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > An untextured white strip clips through the walkway near the upper stairs.
- **lockhead** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Untextured white placeholder geometry is exposed underneath the lower wooden staircase.
- **lockhead** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A bright white rectangular beam or plane floats in mid-air without attached support.
- **loop-stairs** · naive · immersion · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A flat, untextured white mesh plane sits on the ground, appearing like an incomplete placeholder asset.
- **loop-stairs** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A flat, untextured white block lies on the ground, appearing to be leftover placeholder geometry.
- **north-landing** · naive · immersion · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A flat brown panel floats unsupported in mid-air with blocks sitting on it.
- **north-landing** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A completely flat, unshaded brown plane with loose gray blocks floats in mid-air without structural support.
- **north-landing** · naive · navigation · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The narrow elevated walkway disappears into a dense cluster of wooden beams, making the route forward ambiguous.
- **north-landing** · naive · navigation · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The main wooden walkway leads directly into a dense mesh of structural beams, making it ambiguous where the player can actually walk forward.
- **quay-west** · checklist · navigation · sev 2 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > a door / entrance you can go through ("Enter Cookhouse"): VISIBLE-BUT-ILLEGIBLE — The recessed doorway under the cookhouse eaves is too dark and merges into the surrounding shadowed wood.
- **quay-west** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Thin grey rectangular planes hover mid-air without attachment or structural support.
- **quay-west** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Thin white rectangular meshes are floating mid-air without attachment to any surrounding structures.
- **quay-west** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Two thin horizontal white planes are floating in mid-air with no structural support or attachment to surrounding objects.
- **shelf-east** · checklist · navigation · sev 2 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > a door / entrance you can go through ("Enter Weapon Shop"): VISIBLE-BUT-ILLEGIBLE — Darkened wall opening lacks clear door framing or interactive cues.
- **shelf-east** · checklist · occlusion · sev 2 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > a door / entrance you can go through ("Enter Armor Shop"): OCCLUDED — Hidden behind elevated wooden structures and roofs.
- **shelf-east** · checklist · navigation · sev 2 · confidence: upheld by adversarial-judge:checklist; ray census: occluded
  > Inn: VISIBLE-BUT-ILLEGIBLE — Reads as a generic wooden structure without identifying inn features.
- **shelf-west** · checklist · occlusion · sev 2 · confidence: upheld by ray-census; ray census: occluded
  > the route between Valley Gate and Inn: OCCLUDED — The stair flight descending from the upper area is hidden behind the upper platform deck and support beams.
- **shelf-west** · checklist · occlusion · sev 2 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > a door / entrance you can go through ("Enter The Boatmen's Rest"): OCCLUDED — The door to enter the Inn is obscured in shadow beneath the lower overhang.
- **shelf-west** · checklist · occlusion · sev 2 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > a door / entrance you can go through ("Enter Item Shop"): OCCLUDED — The entrance door to the Item Shop is hidden behind its counter facade and side walls.
- **shelf-west** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The pulley cable extends down and penetrates directly into the stone ground without any anchor or spool structure.
- **shelf-west** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The diagonal wooden support beams project out into mid-air beneath the upper platform without resting on any lower wall or rock face.
- **shelf-west** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The diagonal wooden support beams end floating in mid-air over the open chasm rather than resting against a wall or pillar.
- **shelf-west** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The wooden support beams under the upper deck extend outward and terminate floating in mid-air without connecting to any wall or support structure.
- **waterfront** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A wooden platform step floats in mid-air with no physical supports connecting it to the surrounding cliff or stairs.
- **waterfront** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The rock face model on the right is a single-sided paper-thin surface, leaving open space visible underneath its edges.
- **waterfront** · naive · navigation · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A dense tangle of overlapping wooden ramps, stairs, and debris obscures which surfaces are actually walkable.
- **waterfront** · naive · immersion · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A wooden step platform floats in mid-air without any supporting beams or posts underneath.
- **waterfront** · naive · navigation · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Tightly packed overlapping wooden beams, platforms, and stairs create visual clutter that makes it difficult to parse navigable paths.
- **waterfront** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A wooden platform step floats unsupported in mid-air without connection to the adjacent stairs or cliff face.
- **waterfront** · naive · navigation · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Extremely cluttered and overlapping wooden staircases, planks, and debris make walkable pathways visually ambiguous.
- **weave** · naive · navigation · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Dense layering of identically textured wooden roofs and scaffolding makes walkable paths very difficult to distinguish from non-walkable roofs.
- **weave** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The cliff backdrop terminates abruptly into an untextured dark purple void along the screen edge.
- **weave** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A featureless dark purple void borders the cliffside, creating an unrendered backdrop that breaks visual consistency and spatial depth.
- **weave** · naive · navigation · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Slanted house roofs and flat wooden walkways share nearly identical textures, shapes, and lighting, making navigable paths hard to distinguish from non-walkable scenery.

### severity 1 (19)

- **boatyard** · naive · geometry · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The roof planks on the top-right hut overlap and float in a disjointed stack.
- **boatyard** · naive · geometry · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A stray polygon strip clips awkwardly through the center of the circular wooden floor platform.
- **boatyard** · naive · geometry · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The wooden framework in the background consists of loose beams floating and clipping without supporting joints.
- **boatyard** · naive · geometry · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The wooden planks forming the roof overlap at erratic angles with severe clipping and unsupported floating edges.
- **cottage** · naive · geometry · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The stylized tree models clip directly into the steep rock face without a natural base or root connection.
- **fishdock** · naive · geometry · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A thin diagonal beam spans from the top right building to the lower railing without visible structural connections or anchors at its ends.
- **fishdock** · naive · immersion · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A wooden boat is perched high above dry ground on support pillars without any water or clear mechanism for launching.
- **lockfive** · naive · immersion · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The green fabric sheets along the upper railing are completely flat, rigid geometry that clip through the wooden framework.
- **lockfive** · naive · geometry · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The staircase steps appear to float without visible support structures underneath.
- **lockhead** · naive · geometry · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A bright white untextured plank floats in mid-air beneath the wooden stairs.
- **lockhead** · naive · geometry · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A cardboard box clips directly through the sloped wooden roof tiles.
- **loop-stairs** · naive · geometry · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > An untextured bright white plane sits flat on the terrain, appearing as unfinished blockout geometry.
- **loop-stairs** · naive · geometry · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The black wire near the foreground ground ends abruptly in mid-air without attaching to any anchor point.
- **north-landing** · naive · geometry · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A flat green rectangular mesh is laying loosely on the ground without thickness or blending.
- **north-landing** · naive · immersion · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A flat green rectangular texture strip is pasted onto the ground terrain without any blending or depth.
- **shelf-west** · naive · immersion · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The long diagonal cable clips straight into the ground surface without any pulley base, anchor, or spool visual.
- **weave** · naive · geometry · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A flat white rectangular plane sits on the terrain near the walkway like placeholder or missing geometry.
- **weave** · naive · geometry · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The left cliffside terminates abruptly into a flat, dark untextured void wall.
- **weave** · naive · immersion · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Wooden crates are stacked at an unnaturally steep angle directly on a sloped roof without sliding or having visible support.

### refuted at stage 2 (25) — not findings; kept for audit

- **boatyard** · naive · immersion · sev 1 · 1/3 looks · REFUTED by adversarial-judge:naive: The left end of the flag line is explicitly anchored to a vertical wooden post on the roof below.
  > The decorative flag line floats in mid-air on its left end without attaching to any wall, post, or roof.
- **deep-stairs** · naive · occlusion · sev 2 · 1/3 looks · REFUTED by adversarial-judge:naive: The dark shadow in the cliff recess is a normal result of high-contrast directional sunlight rather than a scene defect.
  > Extremely dark shadows obscure the cliff face and geometry, making it impossible to tell if there is walkable space or a fatal drop.
- **deep-stairs** · naive · occlusion · sev 2 · 1/3 looks · REFUTED by adversarial-judge:naive: Deep cast shadows behind the central building are an intentional lighting choice for sunny exterior environments and do not impede primary navigation.
  > Pitch-black cast shadow obscures the path continuity and terrain geometry behind the central building, making navigation unreadable.
- **deep-stairs** · naive · occlusion · sev 2 · 1/3 looks · REFUTED by adversarial-judge:naive: The dark shadow in the upper center is standard directional cast lighting on background cliff geometry rather than a layout flaw.
  > Deep cast shadows obscure the cliff face and structures behind the staircase, hiding potential pathways and layout.
- **fishdock** · naive · navigation · sev 2 · 1/3 looks · REFUTED by adversarial-judge:naive: The walkway extending off the right edge of the frame is standard camera framing for level pathways continuing off-screen.
  > The primary wooden walkway leads off to the right edge and abruptly terminates without a clear way forward or visible destination.
- **fishdock** · naive · occlusion · sev 2 · 1/3 looks · REFUTED by adversarial-judge:naive: The shaded central area beneath the upper platforms remains clearly visible, showing foliage, props, lanterns, and background rock geometry.
  > Deep, harsh shadows under the central platforms render the geometry and potential paths completely unreadable.
- **fishdock** · naive · immersion · sev 2 · 1/3 looks · REFUTED by adversarial-judge:naive: The green wooden platform is supported from below by dark wooden stilt legs.
  > The green wooden platform hovers in mid-air without any supporting stilts, beams, or ropes attaching it to the surrounding structures.
- **fishdock** · naive · immersion · sev 2 · 1/3 looks · REFUTED by adversarial-judge:naive: The banners are mounted onto overhead wooden beams and connecting cross-bars.
  > The rectangular colored banners float freely in mid-air without any connecting ropes, poles, or wires.
- **gate** · naive · immersion · sev 1 · 1/3 looks · REFUTED by adversarial-judge:naive: The lower right foliage cluster rests directly on and intersects the sloping rock face rather than floating in mid-air.
  > A cluster of leaves is floating in mid-air near the cliff face without any supporting trunk or attachment.
- **gate** · naive · occlusion · sev 1 · 1/3 looks · REFUTED by adversarial-judge:naive: Foreground terrain partially occluding background areas is a standard result of 3D perspective and composition, not a design defect.
  > The large rock wall in the immediate foreground blocks the view of the lower dock area and pathways below.
- **gate** · naive · immersion · sev 1 · 1/3 looks · REFUTED by adversarial-judge:naive: The string supporting the banners connects directly to the wooden post structure on the left side of the path.
  > The green banner hangs from a string that terminates in mid-air without connecting to a support on the left.
- **loop-stairs** · naive · navigation · sev 2 · 1/3 looks · REFUTED by adversarial-judge:naive: The stepped wooden planks and stone risers clearly form a readable, continuous staircase path leading directly to the upper structure.
  > The steps feature disjointed, floating planks and steep vertical drops, making it visually unclear if this is a usable staircase or impassable terrain.
- **north-landing** · naive · immersion · sev 1 · 1/3 looks · REFUTED by adversarial-judge:naive: Simplified conical foliage protruding directly from rock walls is a standard convention for this stylized art style.
  > Stylized tree tops are attached directly to the vertical cliff wall without any trunks or soil.
- **quay-west** · naive · navigation · sev 2 · 1/3 looks · REFUTED by adversarial-judge:naive: The green tiled rooftops, wooden plank walkways, and dirt ground terrain use distinct textures and structural cues that keep traversable paths clearly distinguishable.
  > Walkways, rooftops, and ground terrain share identical textures and blocky geometry, making it ambiguous which surfaces are traversable.
- **shelf-east** · naive · geometry · sev 1 · 1/3 looks · REFUTED by adversarial-judge:naive: The lantern bracket is mounted to the wooden roof beam structure rather than floating or clipping unsupported through shingles.
  > A black lantern fixture clips directly into the roof shingles without proper structural mounting or support.
- **shelf-east** · naive · occlusion · sev 2 · 1/3 looks · REFUTED by adversarial-judge:naive: Ground textures, pebbles, and path contours remain clearly visible inside the shadow, so terrain detail and navigation are not obscured.
  > Extremely dense pitch-black shadow across the central village path hides terrain detail and makes navigation hard to parse.
- **shelf-east** · naive · geometry · sev 1 · 1/3 looks · REFUTED by adversarial-judge:naive: Simplified geometric mesh intersections without trim or flashing are normal for this stylized art direction and do not affect player experience.
  > The stone chimney intersects directly through the roof shingles without any base trim, flashing, or structural join.
- **shelf-east** · naive · navigation · sev 2 · 1/3 looks · REFUTED by adversarial-judge:naive: The upper right background clearly displays shadowed rock faces and canyon walls framing the map rather than an unrendered black void.
  > The area beyond the upper path merges into a solid black void, making it impossible to tell if the space continues or ends.
- **shelf-west** · naive · occlusion · sev 2 · 1/3 looks · REFUTED by adversarial-judge:naive: The space beneath the walkway is sufficiently illuminated to clearly discern the floor, barrels, and surrounding structures.
  > Pitch-black shadows beneath the overhang conceal ground geometry, making it impossible to see if the area below is walkable.
- **shelf-west** · naive · navigation · sev 2 · 1/3 looks · REFUTED by adversarial-judge:naive: Sunlight and indirect lighting clearly show the building roofs and walkways beneath the upper structure rather than obscuring depth.
  > Deep shadows underneath the structure obscure spatial depth and make it unclear whether the ground below is walkable space or a pit fall.
- **shelf-west** · naive · occlusion · sev 2 · 1/3 looks · REFUTED by adversarial-judge:naive: The covered area under the platform is well-lit enough that props and walkable surfaces are clearly recognizable.
  > Heavy pitch-black shadowing under the wooden platform obscures the floor and pathway, making it unclear whether the area is walkable.
- **waterfront** · naive · geometry · sev 2 · 1/3 looks · REFUTED by adversarial-judge:naive: The large brown building on the left is embedded directly into the cliff wall behind it rather than hovering in mid-air.
  > The large brown structure on the left hovers mid-air over the cliff edge without visible foundations or support beams.
- **weave** · naive · immersion · sev 1 · 1/3 looks · REFUTED by adversarial-judge:naive: The lanterns have thin black cords connecting them to the wooden beams overhead.
  > Lanterns float beneath roof structures without visible cords, hooks, or mounting hardware.
- **weave** · naive · navigation · sev 2 · 1/3 looks · REFUTED by adversarial-judge:naive: A solid dark cave mouth is standard visual shorthand in stylised environments for an entrance or background cave portal.
  > The cavern opening is pitch black with no depth or bounced light, making it ambiguous whether it is an accessible path.
- **weave** · naive · navigation · sev 2 · 1/3 looks · REFUTED by adversarial-judge:naive: The stairs lead directly up to the platform and structure in the upper right corner.
  > The wooden stairs going up the right cliffside end abruptly against a sheer rock face with no visible landing or continuation.

## emberbrook — 97 surviving findings (18 refuted at stage 2)

### severity 3 (28)

- **arch** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: occluded _(also on orchard)_
  > the way out of this area on foot towards orchard: ABSENT — No path leading off towards the orchard out of the frame edge is shown in this shot.
- **homerow** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > Brook spring: ABSENT — No water spring is visible anywhere in this frame.
- **homerow** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: occluded
  > Upper lane (closed): ABSENT — No closed upper lane or festival cart is present in this view.
- **homerow** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: occluded
  > Spring house: ABSENT — There is no stone spring house in the scene.
- **homerow** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > Grandmother's bench: ABSENT — No second bench outside Lake's home is visible.
- **homerow** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: occluded
  > the route between Mara & Pip's cottage and Rowan's house: ABSENT — No paved path connects Mara & Pip's cottage to Rowan's house directly.
- **homerow** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > the route between Rowan's house and Hilltop bench: ABSENT — There is no established path leading between Rowan's house and the bench.
- **orchard** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > Orchard rows: ABSENT — No apple orchard rows, ladders, or baskets are present in this view.
- **orchard** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: occluded
  > the route between Village Arch and Orchard rows: ABSENT — The path connecting the Village Arch to the orchard rows is not in frame.
- **orchard** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: occluded
  > the route between Orchard rows and Cider press barn: ABSENT — No path connecting orchard rows to the cider press barn is present.
- **pondlane** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > The Pond: ABSENT — No body of water or pond is visible in this frame.
- **pondlane** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > Pond jetty: ABSENT — No jetty or fishing dock is present in this frame.
- **pondlane** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > Washline green: ABSENT — No washline green or drying field is visible in this frame.
- **pondlane** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > Brook footbridge: ABSENT — No brook or footbridge is present in this frame.
- **pondlane** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: occluded
  > Brook mouth: ABSENT — The brook mouth is not visible in this shot.
- **pondlane** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > Weir & sluice: ABSENT — No weir or sluice mechanism is visible in this frame.
- **pondlane** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > Finn's smokehouse: ABSENT — Finn's smokehouse is not present in this shot.
- **pondlane** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > Pip's den: ABSENT — Pip's den is not visible in this frame.
- **pondlane** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > the route between Festival Square and Pond jetty: ABSENT — The route to the pond jetty is not visible in this shot.
- **pondlane** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: occluded
  > the route between Pond jetty and Brook footbridge: ABSENT — The path between the jetty and brook footbridge is not in this frame.
- **pondlane** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > the route between Pond jetty and Washline green: ABSENT — The path to Washline green is not present in this frame.
- **pondlane** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > the way out of this area on foot towards square: ABSENT — The egress path from the pond area toward the square is not in view in this camera angle.
- **square** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: occluded
  > the route between Village Arch and Festival Square: ABSENT — Village Arch area is off-screen.
- **square** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > the route between Festival Square and Pond jetty: ABSENT — Pond jetty route is off-screen.
- **square** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > the route between Festival Square and Mara & Pip's cottage: ABSENT — Cottage route is not visible in frame.
- **square** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > the route between Festival Square and Tithe barn: ABSENT — Tithe barn road is off-screen.
- **square** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > the route between Brook footbridge and Festival Square: ABSENT — Footbridge route is outside visible frame.
- **woodroad** · checklist · navigation · sev 3 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > a door / entrance you can go through ("Leave Emberbrook"): ABSENT — No door or gateway visual exists in this outdoor forest scene.

### severity 2 (52)

- **arch** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The path geometry clips flat and unnaturally into the ground plane with sharp, unintegrated edges.
- **arch** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A dark flat geometric plane clips cleanly into the terrain path, creating an unnatural jagged tear in the ground geometry.
- **arch** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Dark geometric path polygons clip abruptly into the ground terrain with sharp edges and no blending.
- **gatefield** · checklist · occlusion · sev 2 · confidence: upheld by adversarial-judge:checklist; ray census: off-frame
  > Downstream (vista beyond the Gate): OCCLUDED — The vista beyond the gate is completely hidden behind the closed stone wall.
- **gatefield** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The edge of the paved courtyard floor forms a jagged, blocky step pattern rather than a clean border or natural blending into the terrain.
- **gatefield** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A square cutout in the paved floor exposes lower ground around the wooden structure, creating raw floating floor edges.
- **gatefield** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The edge of the paved courtyard mesh has rough, jagged stair-step cuts where it meets the grass terrain.
- **gateroad** · naive · occlusion · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Dense foreground trees and foliage completely obscure the right side of the view, blocking visibility of the surrounding terrain and potential hazards.
- **gateroad** · naive · navigation · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The cleared path curves directly into deep darkness beneath the trees, making it ambiguous whether the way forward continues or ends.
- **gateroad** · naive · occlusion · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Dense dark foliage and pitch-black shadows obscure the right half of the viewport, blocking line of sight and hiding potential paths.
- **gateroad** · naive · immersion · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The lighter ground patch has abrupt edges with no texture blending or ambient shading, appearing like a flat cutout over the grass.
- **gateroad** · naive · occlusion · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Extremely dense foreground foliage and deep shadows completely block visibility of the environment and any potential paths on the right side of the screen.
- **gateroad** · naive · navigation · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Severe underexposure and heavy shadows make it difficult to distinguish readable pathways from impassable ground terrain.
- **homerow** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A large untextured, flat box structure is attached to the upper side of the building.
- **homerow** · naive · immersion · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A hard-edged, perfectly square black shadow box appears unexpectedly on the walkway path.
- **homerow** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A massive wooden wheel structure clips unnaturally into the building's stone wall.
- **homerow** · naive · immersion · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A pitch-black rectangular plane sits flat on the walkway, appearing as a broken shadow artifact.
- **homerow** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > An elevated section of the building overhangs and floats in mid-air without structural support underneath.
- **homerow** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A pitch-black rectangular block artifact is embedded on the path, suggesting missing lighting or broken shadow geometry.
- **homerow** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The massive wooden wheel clips directly into the ground terrain without visible support or housing.
- **orchard** · checklist · navigation · sev 2 · confidence: upheld by adversarial-judge:checklist; ray census: occluded
  > Cider press barn: VISIBLE-BUT-ILLEGIBLE — The structure's roof is visible, but the area underneath is pitch black in shadow, hiding any press, apple crates, or straw needed to identify it as a cider press barn.
- **orchard** · naive · occlusion · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The pitch-black shadow cast by the roof completely obscures the building's base, entrances, and ground details underneath.
- **orchard** · naive · occlusion · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Pitch-black shadow completely obscures the ground and structure below the roof, concealing paths and potential obstacles.
- **orchard** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A bright green untextured object clips strangely into the terrain and foliage.
- **orchard** · naive · occlusion · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > An extremely dark roof shadow completely obscures the ground and terrain details, making it impossible to see objects or paths in that area.
- **orchard** · naive · occlusion · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Dense foreground foliage blocks a large portion of the right side of the screen, obscuring the surrounding space and potential navigation routes.
- **pondlane** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Untextured green blockout slabs on the path appear to be unfinished developer placeholder geometry.
- **pondlane** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The cyan rectangular steps look like untextured placeholder geometry that does not blend into the terrain.
- **pondlane** · naive · navigation · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Dense trees and dark foliage obscure the middle ground, leaving no clear visible path or direction for movement.
- **pondlane** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The blocky steps on the lower left appear to be untextured greybox geometry.
- **pondlane** · naive · immersion · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Tree trunks in the background cut off abruptly against the sky without foliage tops or proper bases.
- **pondlane** · naive · occlusion · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The dense central foliage hides the ground and paths underneath, making it unclear where the player can walk.
- **square** · checklist · occlusion · sev 2 · confidence: upheld by adversarial-judge:checklist; ray census: clear
  > a door / entrance you can go through ("Enter The Ember Hearth"): OCCLUDED — Door is hidden behind lower building structures and angle of view.
- **square** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Black square holes and grid-shaped missing patches are visible in the ground terrain mesh.
- **square** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The ground terrain mesh terminates in a jagged, blocky stepped edge with missing geometry exposing black void underneath.
- **square** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Several rectangular holes are cut into the ground plane mesh near the well, showing black untextured gaps.
- **square** · naive · occlusion · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A massive foreground roof severely occludes the ground and play area in the lower right section of the screen.
- **square** · naive · immersion · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A bright, untextured white block sits inside the central pit, appearing as a placeholder light object rather than a finished asset.
- **therise** · checklist · navigation · sev 2 · confidence: upheld by adversarial-judge:checklist; ray census: occluded
  > Inn: VISIBLE-BUT-ILLEGIBLE — A building is visible in the background behind the square, but lacks identifying signage or features distinguishing it as an inn.
- **therise** · checklist · navigation · sev 2 · confidence: upheld by adversarial-judge:checklist; ray census: occluded
  > Poppy's bakery: VISIBLE-BUT-ILLEGIBLE — A stone cottage stands near the square, but lacks visible bakery features or signs to identify it as Poppy's bakery.
- **therise** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The paved path geometry features sharp, unblended polygonal edges clipping abruptly into the surrounding terrain mesh.
- **therise** · naive · occlusion · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A dense foreground bush occupies a major section of the camera frame, blocking sightlines to the surrounding town layout.
- **therise** · naive · navigation · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Deep shadows and dense foliage obscure the walkable terrain, making it ambiguous which way the player is intended to progress.
- **therise** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The ground path mesh segments are disjointed and misaligned, creating visible seams and clipping edges on the terrain.
- **therise** · naive · occlusion · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Extremely dense and dark foliage dominates the left side of the frame, severely obscuring paths and environment layout.
- **therise** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The pathway mesh clips awkwardly through the terrain, leaving floating edges and untextured vertical gaps.
- **waystone** · naive · immersion · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The pedestal is brightly lit in cool white light from an opposing angle, inconsistent with the warm orange light emitted by the adjacent lamp post.
- **waystone** · naive · navigation · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The path vanishes into complete darkness beneath the tree canopy, making it unclear if the way forward is walkable.
- **waystone** · naive · navigation · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Dense foliage and shadow completely block the view of the environment, making it ambiguous whether the path continues or ends.
- **woodroad** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The perimeter of the circular stone pad has blocky, stair-stepped edges that clip awkwardly into the surrounding terrain.
- **woodroad** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive _(also on gatefield)_
  > The perimeter of the circular paved area consists of jagged, stair-stepped blocky steps that look like unrefined grid geometry.
- **woodroad** · naive · geometry · sev 2 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The perimeter of the circular paved area has unnatural, pixelated stair-step edges where it intersects the grass.

### severity 1 (17)

- **gateroad** · naive · geometry · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The grey rectangular block lacks grounding shadows and proper contact ambient occlusion with the dark grass beneath it.
- **homerow** · naive · geometry · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A wooden beam clips straight through the paved walkway surface.
- **homerow** · naive · immersion · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A plain brown rectangular face on the upper wall appears untextured, resembling placeholder geometry.
- **northlane** · naive · immersion · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Modern street lamp posts conflict visually with the rustic, medieval cottage setting.
- **northlane** · naive · geometry · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The chimney clips directly through the roof tiles without flashing or structural framing.
- **northlane** · naive · geometry · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The square roof section clips directly into the main building wall without a proper architectural transition.
- **northlane** · naive · immersion · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A flat orange plane on the upper building structure looks untextured compared to the rest of the scene.
- **northlane** · naive · geometry · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The paved ground section cuts sharply into the surrounding terrain with a harsh, unblended rectangular edge.
- **orchard** · naive · occlusion · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Dense foreground trees obstruct the view of the terrain and potential navigation paths on the right side of the screen.
- **orchard** · naive · immersion · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The active light source casts a sharp, dark shadow outward without illuminating its immediate surroundings.
- **orchard** · naive · immersion · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The small bushes are placed in an unnaturally rigid circular arc across the clearing, breaking environmental believability.
- **pondlane** · naive · geometry · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The wooden roof panels on the market stalls visibly clip through one another at harsh angles.
- **therise** · naive · occlusion · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > A large foreground bush severely blocks the player's view of the ground and playable path directly behind it.
- **waystone** · naive · occlusion · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > Dense, pitch-black foliage obscures the right portion of the frame, hiding the path's continuation and surrounding terrain.
- **waystone** · naive · immersion · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The underside of the tree canopy above is brightly illuminated despite the light fixture having an opaque top cover.
- **waystone** · naive · geometry · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The stone path slabs end abruptly with exposed, floating edges that do not connect cleanly with the surrounding ground terrain.
- **woodroad** · naive · geometry · sev 1 · confidence: 1/3 looks; upheld by adversarial-judge:naive
  > The straight path plane clips directly into the terrain with razor-sharp, unblended edges.

### refuted at stage 2 (18) — not findings; kept for audit

- **arch** · checklist · navigation · sev 2 · single look · REFUTED by adversarial-judge:checklist: The complaint is based on the building lacking a sign or label identifying it as an inn, which is explicitly disallowed under the rules.
  > Inn: VISIBLE-BUT-ILLEGIBLE — A small stone cottage with a chimney is visible, but lacks any sign or feature identifying it specifically as the inn.
- **arch** · naive · navigation · sev 2 · 1/3 looks · REFUTED by adversarial-judge:naive: The tree shadows are semi-transparent dappled light, leaving ground textures and paths clearly visible underneath.
  > Pitch-black tree shadows obscure the terrain surface, making walkable routes indistinguishable.
- **arch** · naive · occlusion · sev 2 · 2/3 looks · REFUTED by adversarial-judge:naive: Foreground foliage framing the right side of the camera view is a standard artistic choice that does not constitute a gameplay defect.
  > Extremely dense and dark tree foliage obscures most of the space and potential paths on the right side of the screen.
- **gatefield** · naive · exit · sev 2 · 1/3 looks · REFUTED by adversarial-judge:naive: The wooden door and archway frame at the top center remain clearly recognizable as an entrance despite the dark lighting.
  > The doorway is submerged in deep shadow, making it difficult to identify as a usable portal or exit.
- **gatefield** · naive · immersion · sev 1 · 1/3 looks · REFUTED by adversarial-judge:naive: The wooden structure is placed inside a recessed dirt cutout rather than sitting flatly on top of the paved floor.
  > The wooden structures sit flatly on the ground without proper footings or ground blending.
- **gatefield** · naive · exit · sev 2 · 1/3 looks · REFUTED by adversarial-judge:naive: The doorway is easily distinguishable by its frame and wooden paneling, so the lighting shadow does not obscure its function.
  > The doorway in the back wall is completely obscured in shadow, making it difficult to recognize as a path forward.
- **gatefield** · naive · exit · sev 2 · 1/3 looks · REFUTED by adversarial-judge:naive: The door outline and wood grain texture are still visible and clearly identifiable as a doorway.
  > The doorway set into the rear brick wall is deeply shadowed, making it difficult to read as a usable entrance or exit.
- **homerow** · naive · occlusion · sev 2 · 1/3 looks · REFUTED by adversarial-judge:naive: Foreground foliage is a standard framing element in isometric environment art and does not constitute a defect.
  > The dense evergreen tree severely obstructs the view of the building entrance, path, and surrounding walkable space.
- **northlane** · naive · occlusion · sev 2 · 1/3 looks · REFUTED by adversarial-judge:naive: The tree foliage around the house is standard environmental scenery and does not impede gameplay or obscure essential navigation.
  > Thick dark foliage obscures the ground and left side of the house, hiding potential paths and entrances.
- **northlane** · naive · occlusion · sev 2 · 1/3 looks · REFUTED by adversarial-judge:naive: Tree canopies surrounding structures are normal environment art details rather than game-breaking occlusion issues.
  > Dense foliage completely covers the area around the house, concealing paths and potential doors from view.
- **northlane** · naive · navigation · sev 1 · 1/3 looks · REFUTED by adversarial-judge:naive: The stone pathway on the right remains clearly visible as it curves across the grass toward the edge of the frame.
  > The stone pathway cuts across the grass and disappears into dark foliage without a clear continuation.
- **northlane** · naive · occlusion · sev 2 · 1/3 looks · REFUTED by adversarial-judge:naive: Dense foliage behind the building serves as standard background dressing and does not obstruct player movement.
  > Heavy tree foliage completely blocks view of the space behind the central building, hiding potential walkways and wall boundaries.
- **northlane** · naive · navigation · sev 2 · 1/3 looks · REFUTED by adversarial-judge:naive: Terrain and path details remain easily readable despite the ambient shadows on the right side.
  > Extremely dark ambient shadows obscure the terrain and path boundaries, making it hard to see where walkable ground continues.
- **square** · checklist · navigation · sev 2 · single look · REFUTED by adversarial-judge:checklist: The building is plainly visible, and objecting to its lack of trade signage is a complaint about missing signs rather than art readability.
  > Item Shop: VISIBLE-BUT-ILLEGIBLE — Building located near the square, but lacks distinct trade signage.
- **square** · checklist · navigation · sev 2 · single look · REFUTED by adversarial-judge:checklist: The cottage is clearly visible, and complaining about a lack of inn indicators is a complaint about missing signage or labels.
  > Inn: VISIBLE-BUT-ILLEGIBLE — Small cottage visible in background without clear inn indicators.
- **square** · checklist · navigation · sev 2 · single look · REFUTED by adversarial-judge:checklist: The building is fully legible as a cottage, and expecting specific bakery signifiers on a standard house is a complaint about missing labels.
  > Poppy's bakery: VISIBLE-BUT-ILLEGIBLE — Orange-roofed cottage on plaza edge, indistinguishable from ordinary houses.
- **waystone** · checklist · navigation · sev 3 · single look · REFUTED by adversarial-judge:checklist: The paved path remains clearly visible and continues all the way to the bottom edge of the frame.
  > the way out of this area on foot towards arch: ABSENT — The road fades into darkness before reaching the edge of the frame, so an exit toward the arch is not shown.
- **woodroad** · naive · navigation · sev 2 · 1/3 looks · REFUTED by adversarial-judge:naive: The dense, dark pine trees clearly function as a standard impassable forest boundary wall rather than a confusing navigation path.
  > Pitch-black foliage completely obscures the right side of the scene, making it impossible to determine if it is a playable path or an impassable boundary.

