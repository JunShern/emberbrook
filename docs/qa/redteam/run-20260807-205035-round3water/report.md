# Scene red-team — emberbrook — run 20260807-205035-round3water

judge `gemini:gemini-3.6-flash` (pinned) · 11 plates · checklist · blockout mode

## 1. Calibration

_not scored in this run_


## 2. Survivors by bucket

### known (6)

- [arch/checklist/navigation/sev3] the way out of this area on foot towards orchard: ABSENT — No path exiting towards an orchard is visible leading off-camera. _(also on orchard)_
- [arch/checklist/navigation/sev3] the way out of this area on foot towards therise: ABSENT — No path exiting towards the rise is visible leading off-camera.
- [square/checklist/navigation/sev3] the way out of this area on foot towards homerow: ABSENT — Exit path towards homerow is not visible.
- [homerow/checklist/occlusion/sev2] Brook spring: OCCLUDED — The spring source is occluded by the spring house structure and dense surrounding foliage.
- [homerow/checklist/navigation/sev3] the route between Mara & Pip's cottage and Rowan's house: ABSENT — No dedicated direct path connects Mara & Pip's cottage to Rowan's house across the lawn.
- [gatefield/checklist/occlusion/sev2] Downstream (vista beyond the Gate): OCCLUDED — Hidden completely behind the solid masonry wall and door of the gate.

### new (22)

- [woodroad/checklist/navigation/sev3] a door / entrance you can go through ("Leave Emberbrook"): ABSENT — No doorway or physical entrance portal exists in this outdoor forest scene.
- [orchard/checklist/navigation/sev3] Orchard rows: ABSENT — No orchard rows, apple trees, ladders, or baskets are present in the frame.
- [orchard/checklist/navigation/sev2] Cider press barn: VISIBLE-BUT-ILLEGIBLE — The shelter structure is visible, but deep pitch-black shadows beneath the roof completely hide its interior and any cider press equipment or crates.
- [orchard/checklist/navigation/sev3] the route between Village Arch and Orchard rows: ABSENT — No path connecting a village arch to orchard rows is visible in this shot.
- [orchard/checklist/navigation/sev3] the route between Orchard rows and Cider press barn: ABSENT — No path leading from orchard rows to the cider press barn is present.
- [square/checklist/navigation/sev2] Village bell: VISIBLE-BUT-ILLEGIBLE — Small post structure obscured by shadows and surrounding timber props.
- [square/checklist/navigation/sev3] the route between Festival Square and Pond jetty: ABSENT — Pond jetty and its road are not present in this shot.
- [square/checklist/navigation/sev3] the route between Festival Square and Tithe barn: ABSENT — Road towards the tithe barn lies outside the camera view.
- [square/checklist/navigation/sev3] the route between Brook footbridge and Festival Square: ABSENT — Brook footbridge path is not visible in this frame.
- [square/checklist/navigation/sev2] a door / entrance you can go through ("Enter Item Shop"): VISIBLE-BUT-ILLEGIBLE — Recessed entrance area dark and indistinct from distance.
- [square/checklist/immersion/sev2] The world at the frame edges: WEAK — Dense foliage borders most edges well, though upper corners dissolve abruptly into blackness. _(also on pondlane)_
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 28.2,98.6,0.4,67.9
- [pondlane/checklist/navigation/sev2] The Pond: VISIBLE-BUT-ILLEGIBLE — The dark surface merges into surrounding ground without clear water shading or defined banks.
- [pondlane/checklist/navigation/sev3] Washline green: ABSENT — No distinct field or open green area is visible in frame.
- [pondlane/checklist/navigation/sev3] Brook mouth: ABSENT — The brook outlet into the river is not in view.
- [pondlane/checklist/navigation/sev3] Weir & sluice: ABSENT — The weir structure and sluice assembly are not present.
- [pondlane/checklist/navigation/sev3] Finn's smokehouse: ABSENT — No dedicated smokehouse structure or fish drying racks can be seen.
- [pondlane/checklist/navigation/sev3] Pip's den: ABSENT — The hidden den under the bank is not visible.
- [pondlane/checklist/navigation/sev3] the route between Pond jetty and Washline green: ABSENT — Path leading towards the north shore is not visible.
- [homerow/checklist/navigation/sev3] Grandmother's bench: ABSENT — No bench is present outside the keeper's cottage.
- [homerow/checklist/navigation/sev3] the route between Rowan's house and Hilltop bench: ABSENT — No path connects Rowan's house directly down to the hilltop bench.
- [northlane/checklist/navigation/sev3] Back lane (closed): ABSENT — No closed lane with stacked barrels is visible in this frame.
- [northlane/checklist/navigation/sev3] the route between Festival Square and Tithe barn: ABSENT — No walled north lane connecting to Festival Square appears in this view.

### style-bar (2)

- [therise/checklist/immersion/sev2] The sky: WEAK — Gradient appears slightly flat and lacks atmospheric depth or cloud structure. _(also on pondlane)_
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 63.7,93.8,128.3,131.3
- [square/checklist/immersion/sev2] The water surface: ABSENT — No water body appears within the camera view. _(also on pondlane)_


## 3. Budget

21 calls, 48358 prompt + 52183 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.