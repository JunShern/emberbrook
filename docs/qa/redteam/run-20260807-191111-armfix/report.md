# Scene red-team — emberbrook — run 20260807-191111-armfix

judge `gemini:gemini-3.6-flash` (pinned) · 2 plates · checklist · blockout mode

## 1. Calibration

_not scored in this run_


## 2. Survivors by bucket

### known (6)

- [pondlane/checklist/occlusion/sev2] Pond jetty: OCCLUDED — Hidden behind the dense trees and wooden market structures in the foreground.
- [pondlane/checklist/occlusion/sev2] Brook mouth: OCCLUDED — Obscured by thick foliage in the middle ground.
- [pondlane/checklist/occlusion/sev2] Weir & sluice: OCCLUDED — Blocked from view by central tree branches and terrain.
- [pondlane/checklist/occlusion/sev2] Finn's smokehouse: OCCLUDED — Hidden behind foreground trees near the shore.
- [pondlane/checklist/occlusion/sev2] the route between Pond jetty and Washline green: OCCLUDED — Blocked by tree trunks along the northern shore.
- [pondlane/checklist/immersion/sev2] The sky: WEAK — JUDGMENT: Lacks atmospheric depth and cloud detail, appearing as a plain gradient fill.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 67.7,85.4,52.8,66.8

### new (5)

- [pondlane/checklist/navigation/sev3] Washline green: ABSENT — Not present anywhere within the visible bounds of this frame.
- [pondlane/checklist/occlusion/sev2] Pip's den: OCCLUDED — Hidden beneath the embankment near the bridge.
- [pondlane/checklist/immersion/sev2] The world at the frame edges: WEAK — JUDGMENT: Tree canopy meets the sky with abrupt cut-offs, exposing thin backdrop density.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 67.7,86,51.1,65.3
- [northlane/checklist/navigation/sev3] Back lane (closed): ABSENT — No closed lane with stacked barrels is visible anywhere in this shot.
- [northlane/checklist/navigation/sev3] the route between Festival Square and Tithe barn: ABSENT — No walled lane leading towards a festival square is present in this view.

### style-bar (1)

- [pondlane/checklist/immersion/sev2] The water surface: WEAK — JUDGMENT: Simple dark reflection plane without proper shallow transparency or contact blending.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 67.1,90.6,35.4,47.6


## 3. Budget

4 calls, 9071 prompt + 8194 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.