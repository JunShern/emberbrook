# Scene red-team — emberbrook — run 20260807-190224

judge `gemini:gemini-3.6-flash` (pinned) · 2 plates · checklist · blockout mode

## 1. Calibration

_not scored in this run_


## 2. Survivors by bucket

### known (8)

- [pondlane/checklist/occlusion/sev2] The Pond: OCCLUDED — The main body of the pond is completely hidden behind the dense central tree canopy and foliage.
- [pondlane/checklist/occlusion/sev2] Washline green: OCCLUDED — Hidden from view behind the thick central cluster of trees.
- [pondlane/checklist/occlusion/sev2] Brook footbridge: OCCLUDED — Hidden behind the dense midground bushes along the brook's course.
- [pondlane/checklist/occlusion/sev2] Brook mouth: OCCLUDED — Hidden behind the low foliage and terrain in the midground background.
- [pondlane/checklist/occlusion/sev2] Weir & sluice: OCCLUDED — Obscured by the dense shrubbery in the middle distance.
- [pondlane/checklist/occlusion/sev2] Pip's den: OCCLUDED — Hidden beneath the bank foliage near the brook edge.
- [pondlane/checklist/occlusion/sev2] the route between Pond jetty and Brook footbridge: OCCLUDED — The pathway along the brook is blocked from sight by the dense middle ground bushes.
- [pondlane/checklist/occlusion/sev2] the route between Pond jetty and Washline green: OCCLUDED — Hidden behind the central cluster of trees and shrubs.

### new (3)

- [pondlane/checklist/immersion/sev2] The world at the frame edges: WEAK — JUDGMENT: The background tree line thins out abruptly into the bare sky gradient at the top left edge.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 84.4,192.4,63.4,153.1
- [northlane/checklist/navigation/sev3] Back lane (closed): ABSENT — No closed lane with stacked barrels is visible anywhere in this frame.
- [northlane/checklist/navigation/sev3] the route between Festival Square and Tithe barn: ABSENT — No north lane between walls is visible in this frame.

### style-bar (2)

- [pondlane/checklist/immersion/sev2] The sky: WEAK — JUDGMENT: The sky is a flat, featureless blue gradient lacking cloud forms or realistic atmospheric haze.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 67.7,85.3,53,67
- [pondlane/checklist/immersion/sev3] The water surface: FAILING — JUDGMENT: The water surface reads as a solid, flat black plane with no transparency, flow, or believable reflections.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 71.2,96.1,40.5,54.5


## 3. Budget

4 calls, 8969 prompt + 13289 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.