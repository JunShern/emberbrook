# Scene red-team — emberbrook — run 20260808-005259-round3fieldsky

judge `gemini:gemini-3.6-flash` (pinned) · 11 plates · checklist · blockout mode

## 1. Calibration

_not scored in this run_


## 2. Survivors by bucket

### known (14)

- [arch/checklist/navigation/sev3] the way out of this area on foot towards orchard: ABSENT — No path exiting toward an orchard is present in this frame. _(also on orchard)_
- [therise/checklist/occlusion/sev2] Cider press barn: OCCLUDED — Hidden behind dense trees and foliage in the midground.
- [therise/checklist/navigation/sev2] The Heartlight: VISIBLE-BUT-ILLEGIBLE — Pedestal area is too small and shadowed to identify the flame mesh clearly.
- [therise/checklist/immersion/sev2] The sky: WEAK — JUDGMENT: Sky appears as a plain blue gradient lacking cloud detail.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 90.8,93.8,128.3,131.3
- [square/checklist/navigation/sev3] the way out of this area on foot towards therise: ABSENT — Exit path toward rise not visible.
- [square/checklist/navigation/sev3] the way out of this area on foot towards pondlane: ABSENT — Pondlane exit not in frame.
- [square/checklist/navigation/sev3] the way out of this area on foot towards homerow: ABSENT — Homerow exit not in frame.
- [square/checklist/navigation/sev3] the way out of this area on foot towards northlane: ABSENT — Northlane exit not in frame.
- [pondlane/checklist/occlusion/sev2] Washline green: OCCLUDED — Hidden entirely behind the dense tree canopy in the midground.
- [pondlane/checklist/occlusion/sev2] the route between Pond jetty and Washline green: OCCLUDED — Blocked from view by the thick forest canopy in the upper middle ground.
- [homerow/checklist/occlusion/sev2] Brook spring: OCCLUDED — Hidden behind the dense tree canopy in the upper left section.
- [homerow/checklist/navigation/sev2] the route between Mara & Pip's cottage and Rowan's house: VISIBLE-BUT-ILLEGIBLE — The path between the two cottages is heavily shadowed and obscured by ground clutter and foliage.
- [homerow/checklist/immersion/sev3] The water surface: FAILING — No water surface material or geometry is rendered in the stream bed, leaving only flat dark ground.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 47.7,55.3,54,60.3
- [gatefield/checklist/occlusion/sev2] Downstream (vista beyond the Gate): OCCLUDED — Hidden behind the solid masonry wall of the Old Gate.

### new (24)

- [woodroad/checklist/navigation/sev3] a door / entrance you can go through ("Leave Emberbrook"): ABSENT — No door or entrance structure is present anywhere in this outdoor woodland scene.
- [arch/checklist/navigation/sev3] the route between Village Arch and Orchard rows: ABSENT — No distinct branch or path leading toward an orchard is visible near the arch.
- [arch/checklist/navigation/sev2] Item Shop: VISIBLE-BUT-ILLEGIBLE — Partially cropped at the top left edge without clear storefront identifiers.
- [orchard/checklist/navigation/sev3] Orchard rows: ABSENT — No orchard rows, apple trees, ladders, or baskets are visible anywhere in this frame.
- [orchard/checklist/navigation/sev2] Cider press barn: VISIBLE-BUT-ILLEGIBLE — The gabled roof barn structure is visible, but deep shadow renders its interior completely pitch black, obscuring any cider press, crates, or straw.
- [orchard/checklist/navigation/sev3] the route between Village Arch and Orchard rows: ABSENT — No path connecting a village arch to orchard rows is present.
- [orchard/checklist/navigation/sev3] the route between Orchard rows and Cider press barn: ABSENT — No path leading from orchard rows to the cider press barn is visible.
- [square/checklist/navigation/sev3] the route between Village Arch and Festival Square: ABSENT — Village arch and route not present in scene.
- [square/checklist/navigation/sev3] the route between Festival Square and Pond jetty: ABSENT — Pond jetty route is not visible in frame.
- [square/checklist/navigation/sev3] the route between Festival Square and Mara & Pip's cottage: ABSENT — Cottage route not identifiable in shot.
- [square/checklist/navigation/sev3] the route between Festival Square and Tithe barn: ABSENT — Tithe barn route not present in scene.
- [square/checklist/navigation/sev3] the route between Brook footbridge and Festival Square: ABSENT — Footbridge path not visible in frame.
- [square/checklist/navigation/sev2] a door / entrance you can go through ("Enter Item Shop"): VISIBLE-BUT-ILLEGIBLE — Doorway area obscured by heavy shadow.
- [square/checklist/navigation/sev2] a door / entrance you can go through ("Enter The Ember Hearth"): VISIBLE-BUT-ILLEGIBLE — Entrance door is dark and lacks definition.
- [square/checklist/navigation/sev2] a door / entrance you can go through ("Enter Poppy's bakery"): VISIBLE-BUT-ILLEGIBLE — Doorway blends into shadowed building surface.
- [square/checklist/immersion/sev2] The world at the frame edges: WEAK — JUDGMENT: Heavy darkness masks outer boundaries, leaving perimeter depth unconvincing. _(also on pondlane)_
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 25.9,98.6,0.4,30.8
- [pondlane/checklist/navigation/sev2] Pond jetty: VISIBLE-BUT-ILLEGIBLE — A small wooden structure is visible, but dark lighting makes it hard to distinguish as a jetty.
- [pondlane/checklist/navigation/sev3] Brook mouth: ABSENT — The brook mouth where it meets the river is not present in this shot.
- [pondlane/checklist/navigation/sev3] Weir & sluice: ABSENT — The weir and hand-winched sluice structure is not in view.
- [pondlane/checklist/navigation/sev3] Finn's smokehouse: ABSENT — The smokehouse structure cannot be seen in this frame.
- [pondlane/checklist/navigation/sev3] Pip's den: ABSENT — Pip's den hideout is not visible anywhere in this frame.
- [homerow/checklist/navigation/sev3] Upper lane (closed): ABSENT — The upper lane continuation and closure cart are not present in the scene.
- [homerow/checklist/navigation/sev3] Grandmother's bench: ABSENT — No bench is present outside Lake's cottage door, only wooden crates.
- [northlane/checklist/navigation/sev3] Back lane (closed): ABSENT — No back lane blocked with Emberwake barrels is visible in this frame.

### style-bar (0)



## 2b. Aim census — did the judge point at what it named?

4 of 10 [QUALITY] verdicts REFUTED: the judge's own box held under 2% of the subject the verdict names. 1 on-subject, 1 absence-claim (census abstains), 4 unmeasurable.

- `quality:sky` — 1/2 refuted; box coverage 75.0%, 1.0%
- `quality:frame-edge-world` — 0/4 refuted; box coverage n/a
- `quality:water-read` — 3/4 refuted; box coverage 0.0%, 0.0%, 0.0%, 0.0%


## 3. Budget

20 calls, 47190 prompt + 50448 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.