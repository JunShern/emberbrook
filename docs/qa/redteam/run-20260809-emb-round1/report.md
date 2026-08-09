# Scene red-team — emberbrook — run 20260809-emb-round1

judge `gemini:gemini-3.6-flash` (pinned) · 11 plates · naive + checklist

## 1. Calibration

_not scored in this run_


## 2. Survivors by bucket

### known (27)

- [woodroad/naive/geometry/sev2] The circular platform's perimeter is constructed from harsh, blocky staircase steps that cut jaggedly into the smooth ground terrain.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 45.1,58,-34.3,-25.6
- [arch/naive/navigation/sev2] Harsh foliage shadows and low-contrast dark gray slabs obscure the edges and directions of the walkable path.
- [arch/checklist/navigation/sev3] the way out of this area on foot towards orchard: ABSENT — No exit path towards orchard is visible. _(also on orchard)_
- [arch/checklist/navigation/sev3] the way out of this area on foot towards therise: ABSENT — No path leading towards the rise leaves the frame.
- [orchard/naive/occlusion/sev2] Large foreground trees heavily obscure the bottom-right area, blocking the player's view of the ground and potential navigation paths.
- [orchard/naive/occlusion/sev2] Dense foreground foliage occludes a large portion of the play area and obscures ground-level details.
- [orchard/naive/occlusion/sev2] Dense foreground trees completely block the view of the ground and potential navigation paths on the right side.
- [therise/naive/navigation/sev2] Dense foreground foliage obscures the terrain and pathways, making it ambiguous where the player can walk.
- [therise/naive/occlusion/sev2] A dark tree in the immediate foreground heavily occludes the right side of the playable area.
- [therise/naive/occlusion/sev2] Dense foreground branches and leaves block view of the main pathways and ground layout.
- [therise/naive/occlusion/sev2] Dense foreground foliage completely blocks the view of central pathways and key space behind it.
- [therise/checklist/occlusion/sev2] Cider press barn: OCCLUDED — Hidden behind thick foreground tree foliage on the left.
- [square/naive/geometry/sev2] The terrain mesh at the bottom center breaks into blocky, jagged geometric steps and black voids.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 37.5,53.7,39,58.7
- [square/naive/occlusion/sev2] The large foreground roof and trees completely occlude the play space and paths in the lower right.
- [square/naive/occlusion/sev1] Dark tree canopies in the bottom left cover a large portion of the playable ground space.
- [square/checklist/navigation/sev3] the way out of this area on foot towards pondlane: ABSENT — Pond lane exit is not shown in this camera view.
- [pondlane/checklist/occlusion/sev2] Washline green: OCCLUDED — Hidden completely behind the dense tree canopy in the upper background.
- [pondlane/checklist/occlusion/sev2] Brook mouth: OCCLUDED — Obscured from view by thick vegetation.
- [pondlane/checklist/occlusion/sev2] Weir & sluice: OCCLUDED — Blocked from view by surrounding foliage.
- [pondlane/checklist/occlusion/sev2] the route between Pond jetty and Washline green: OCCLUDED — Covered by dense trees beyond the midground.
- [homerow/checklist/navigation/sev3] the route between Mara & Pip's cottage and Rowan's house: ABSENT — No distinct path ribbon exists between Mara & Pip's cottage and Rowan's house in this layout.
- [gateroad/naive/occlusion/sev2] Dense foreground trees and pitch-black shadows completely occlude the right side of the environment, making it impossible to see the space.
- [gateroad/naive/occlusion/sev2] Dense foreground foliage and heavy shadows completely block the view of the environment and any potential paths on the right half of the screen.
- [gateroad/naive/geometry/sev1] A dark grey block sitting in the field appears to be untextured or placeholder geometry.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 63,69.9,68.3,77.3
- [gateroad/naive/occlusion/sev2] Dense foreground tree trunks and dark foliage block the player's line of sight across half the screen.
- [gatefield/naive/geometry/sev2] The boundary of the central platform features jagged, blocky grid steps that contrast unnaturally with the organic environment.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 58,81.3,105.5,122.4
- [gatefield/checklist/occlusion/sev2] Downstream (vista beyond the Gate): OCCLUDED — Hidden entirely behind the closed wooden gate wall.

### new (67)

- [woodroad/naive/geometry/sev2] The perimeter of the circular paved area has jagged, stair-stepped grid geometry that does not blend cleanly with the surrounding terrain.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 44.5,59.1,-34.3,-21.9
- [woodroad/naive/immersion/sev1] The pedestal is flatly and brightly overexposed compared to the ambient lighting and nearby lamp post.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 53.7,58.3,-14.1,-5.6
- [woodroad/naive/geometry/sev2] The circular stone platform has jagged, stair-stepped rectangular edges that look like incomplete or broken mesh geometry.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 45,58.6,-34,-25.5
- [woodroad/checklist/navigation/sev3] a door / entrance you can go through ("Leave Emberbrook"): ABSENT — There is no door or designated 'Leave Emberbrook' entrance in this outdoor forest environment.
- [waystone/naive/navigation/sev2] The paved walkway ends abruptly in sharp floating edges, making it unclear whether the path continues or is blocked.
- [waystone/naive/geometry/sev1] The concrete walkway slab cuts off awkwardly near the monument, creating an unnatural seam and offset in the path geometry.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 53.8,59.5,-13.8,-4.7
- [arch/naive/navigation/sev2] The walkway consists of dark angular planes that merge visually into dark ground shadows, making walkable elevation changes and paths ambiguous.
- [arch/naive/geometry/sev1] The grey path slab clips sharply into the dirt terrain without any edge transition or border geometry.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 53.8,59.9,6.3,22.3
- [arch/naive/geometry/sev1] Small light-green spheres are uniformly scattered along the left path edge, appearing as stray or visually confusing asset clutter.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 41,50.7,12.5,21
- [arch/naive/navigation/sev2] The dark ground slabs cut into the terrain with low lighting contrast, making it difficult to discern navigable paths from non-traversable ground.
- [arch/naive/immersion/sev1] Small, identical green spheres are scattered along the left ground plane without clear contextual function or proper terrain blending.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 40.7,50.7,12,22
- [arch/checklist/navigation/sev2] the route between Village Arch and Orchard rows: VISIBLE-BUT-ILLEGIBLE — Path branch is dark and merges indistinctly with ground shadows.
- [arch/checklist/navigation/sev2] Inn: VISIBLE-BUT-ILLEGIBLE — Small cottage visible in background lacks identifying inn features. _(also on therise, square)_
- [arch/checklist/navigation/sev2] Item Shop: VISIBLE-BUT-ILLEGIBLE — Distant stalls are too small and dimly lit to identify as item shop. _(also on therise, square)_
- [arch/checklist/navigation/sev2] Festival dais: VISIBLE-BUT-ILLEGIBLE — Low wooden box structure lacks clear dais details.
- [orchard/naive/occlusion/sev2] The pitch-black shadow cast by the main building completely hides ground details and potential pathing in the middle of the yard.
- [orchard/naive/occlusion/sev2] Extreme shadow completely blacks out the area under the building roof, concealing pathways and entrances.
- [orchard/naive/navigation/sev2] Extreme darkness and low contrast make it difficult to distinguish walkable paths from non-navigable terrain.
- [orchard/checklist/navigation/sev3] Orchard rows: ABSENT — No orchard rows with apple trees, ladders, or baskets are present in this view.
- [orchard/checklist/navigation/sev2] Cider press barn: VISIBLE-BUT-ILLEGIBLE — The roof of the barn is visible, but its open side and interior are pitch black, making it impossible to identify cider presses, crates, or straw.
- [orchard/checklist/navigation/sev3] the route between Village Arch and Orchard rows: ABSENT — No path connecting the arch to orchard rows is present.
- [orchard/checklist/navigation/sev3] the route between Orchard rows and Cider press barn: ABSENT — No path between orchard rows and the cider press barn exists in this shot.
- [therise/naive/geometry/sev2] A flat path polygon clips unnaturally into the ground terrain with sharp unblended edges.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 55.2,61.7,14.3,21.7
- [therise/naive/geometry/sev2] Ground path polygons clip awkwardly through the terrain at sharp angles, leaving unblended seams.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 55.2,61.7,14.3,21.8
- [therise/naive/geometry/sev2] The dark path mesh slabs are visibly misaligned and clipping jaggedly above the terrain surface.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 55.3,61.7,14.4,21.4
- [therise/naive/geometry/sev1] A raw polygonal path mesh extends into the bottom-left screen edge without proper terrain blending or termination.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 48.9,56.1,12.8,17.8
- [therise/checklist/navigation/sev2] Poppy's bakery: VISIBLE-BUT-ILLEGIBLE — Reads as a standard small house rather than a bakery. _(also on square)_
- [therise/checklist/navigation/sev2] Lake's home (the keeper's cottage): VISIBLE-BUT-ILLEGIBLE — Reads as a generic cottage without specific keeper details.
- [therise/checklist/immersion/sev2] The sky: WEAK — JUDGMENT: Simple gradient visible in a narrow cutout lacks atmospheric detail. _(also on pondlane)_
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 62.4,85.1,64.7,77.1
- [square/naive/immersion/sev2] An extremely intense spot of light illuminates the central stone slab without any visible light source like a fire or lantern.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 59.3,68.6,39.2,50
- [square/naive/occlusion/sev2] A large roof in the immediate foreground blocks a significant portion of the view into the lower village area.
- [square/naive/immersion/sev2] The primary central light source is a raw white emissive cube without any fire, embers, or lamp fixture model.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 60.9,66.7,39.8,45.7
- [square/naive/occlusion/sev2] A massive roof structure in the bottom right foreground severely cuts off the player's view of the ground.
- [square/checklist/navigation/sev3] the route between Village Arch and Festival Square: ABSENT — Village arch and its connecting road are off-screen.
- [square/checklist/navigation/sev3] the route between Festival Square and Pond jetty: ABSENT — Pond jetty and its connecting road are outside this frame.
- [square/checklist/navigation/sev3] the route between Festival Square and Mara & Pip's cottage: ABSENT — Mara & Pip's cottage route is not visible in this shot.
- [square/checklist/navigation/sev3] the route between Brook footbridge and Festival Square: ABSENT — Brook footbridge path is not present in this frame.
- [pondlane/naive/geometry/sev2] A sharp, unnatural geometric black gap breaks the ground mesh in the middle of the path.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 76,87.6,45.2,52
- [pondlane/naive/geometry/sev2] A stray black spline/line segment floats unnaturally in mid-air without connecting properly to the surrounding posts.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 71.4,85.4,45.9,51.6
- [pondlane/naive/geometry/sev2] The wooden roof panels and small dark props on top feature floating geometry and clipping edges.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 69.4,82.1,38.2,48.5
- [pondlane/naive/geometry/sev2] A segment of the black overhead wire is broken and floats disconnected in mid-air between the poles.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 78.8,85.2,46.1,51
- [pondlane/checklist/navigation/sev2] The Pond: VISIBLE-BUT-ILLEGIBLE — The water appears as a dark murky strip without distinct pond features.
- [pondlane/checklist/navigation/sev2] Pond jetty: VISIBLE-BUT-ILLEGIBLE — Plank structure is dark and blends into surrounding foliage.
- [pondlane/checklist/occlusion/sev2] Pip's den: OCCLUDED — Hidden under the embankment beneath the bridge.
- [pondlane/checklist/immersion/sev2] The world at the frame edges: WEAK — JUDGMENT: Distant tree silhouettes terminate abruptly along the upper boundary.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 269.9,322.9,-35.8,214.3
- [pondlane/checklist/immersion/sev2] The water surface: WEAK — JUDGMENT: Flat dark surface showing minimal transparency, flow, or edge reflection.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 68.1,75.7,50.7,61.9
- [homerow/naive/geometry/sev2] A completely pitch-black rectangular block sits on the path, appearing as broken geometry or an unrendered shadow artifact.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 33.4,39.4,47,53.2
- [homerow/naive/geometry/sev2] A flat, untextured tan rectangular panel is attached to the timber structure without detail or material graphics.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 49.2,55.5,55.2,60.7
- [homerow/naive/geometry/sev2] A pitch-black rectangle sits flat on the stone pathway, resembling a missing texture or broken shadow decal.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 33.5,39.4,47,53
- [homerow/naive/geometry/sev2] A solid pitch-black rectangular block sits on the stone pathway, appearing as a missing texture or rendering artifact.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 33.4,39.4,47,53.2
- [homerow/naive/geometry/sev2] An untextured, plain tan geometric panel is attached to the upper building wall.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 49.1,55.2,55.1,60.7
- [homerow/checklist/navigation/sev3] Upper lane (closed): ABSENT — The upper lane extension closed by a festival cart is not visible in this frame.
- [homerow/checklist/navigation/sev3] Grandmother's bench: ABSENT — Grandmother's bench outside Lake's cottage is not present in this shot; only wooden crates are placed outside. _(also on gateroad)_
- [northlane/naive/navigation/sev2] The paved walkway abruptly terminates against the side of the house without a door or continuation.
- [northlane/naive/geometry/sev1] A rectangular hipped roof is placed directly over a cylindrical tower, causing the corners of the roof to awkwardly overhang open air.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 64.8,73.7,64,72.3
- [northlane/naive/geometry/sev1] Roof framing and timber beams extend out into open air without supporting walls underneath.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 52.1,59,60.5,70.9
- [northlane/checklist/navigation/sev3] Back lane (closed): ABSENT — No closed lane blocked by barrels is visible anywhere in the frame.
- [northlane/checklist/navigation/sev3] the route between Festival Square and Tithe barn: ABSENT — No walled north lane between the barn and square is present in this view.
- [gateroad/naive/navigation/sev2] The central clear pathway terminates directly into heavy darkness, obscuring where the player is supposed to walk next.
- [gateroad/naive/navigation/sev2] Extremely dark shadowing obscures ground details and makes it difficult to tell where navigable space ends and obstacles begin.
- [gateroad/naive/navigation/sev2] Extremely low lighting obscures terrain boundaries and path continuation, making navigation difficult.
- [gatefield/naive/geometry/sev2] The outer boundary of the dark circular pavement features raw, stair-stepped right-angled edges instead of a smooth or blended edge.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 64.2,80.9,108.9,130.4
- [gatefield/naive/geometry/sev1] The paved floor has sharp rectangular cutouts around the stone pillars that reveal bare dirt underneath.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 73.3,82.3,120,127.2
- [gatefield/naive/geometry/sev1] A sharp square cutout in the paved surface exposes grass and dirt directly in front of the bench structure.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 67.7,73.4,118.7,123.4
- [gatefield/naive/geometry/sev2] The perimeter of the dark pavement uses a harsh, blocky stepped mesh boundary that cuts unnaturally into the grass terrain.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 65.6,81,108.7,124.8
- [gatefield/naive/geometry/sev2] The pillars sit over unrefined rectangular cutouts in the patio flooring that expose raw ground gaps.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 73.5,82.3,120.1,127.1
- [gatefield/checklist/navigation/sev2] the route between Sigil Gate court and Whisperwood trailhead: VISIBLE-BUT-ILLEGIBLE — Merged completely into the general plaza stone floor.

### style-bar (0)



## 2b. Aim census — did the judge point at what it named?

2 of 6 [QUALITY] verdicts REFUTED: the judge's own box held under 2% of the subject the verdict names. 3 on-subject, 0 absence-claim (census abstains), 1 unmeasurable.

- `quality:sky` — 0/2 refuted; box coverage 32.7%, 49.5%
- `quality:water-read` — 2/3 refuted; box coverage 0.0%, 35.5%, 0.0%
- `quality:frame-edge-world` — 0/1 refuted; box coverage n/a


## 3. Budget

65 calls, 113765 prompt + 117613 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.