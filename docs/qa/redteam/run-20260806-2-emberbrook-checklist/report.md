# Scene red-team — emberbrook — run 20260806-2-emberbrook-checklist

judge `gemini:gemini-3.6-flash (replayed from run-tmp-qv-emb + run-tmp-qr-emb)` (pinned) · 11 plates · checklist

## 0. Which plates were judged this round

| plate | critique | replies from | bake judged against | survivors |
|---|---|---|---|---|
| woodroad | **FRESH** | run-tmp-qr-emb | 2026-08-02T11:41:56Z | 1 |
| waystone | **FRESH** | run-tmp-qr-emb | 2026-08-02T12:15:59Z | 0 |
| arch | **FRESH** | run-tmp-qr-emb | 2026-08-02T20:20:29Z | 5 |
| orchard | **FRESH** | run-tmp-qr-emb | 2026-08-02T19:48:21Z | 5 |
| therise | **REPLAYED** | run-tmp-qv-emb | 2026-08-02T20:38:44Z | 4 |
| square | **REPLAYED** | run-tmp-qv-emb | 2026-08-02T19:48:21Z | 7 |
| pondlane | **REPLAYED** | run-tmp-qv-emb | 2026-08-02T19:48:21Z | 9 |
| homerow | **REPLAYED** | run-tmp-qv-emb | 2026-08-02T12:46:58Z | 3 |
| northlane | **FRESH** | run-tmp-qr-emb | 2026-08-02T13:00:24Z | 2 |
| gateroad | **FRESH** | run-tmp-qr-emb | 2026-08-02T22:42:37Z | 1 |
| gatefield | **FRESH** | run-tmp-qr-emb | 2026-08-02T22:57:09Z | 2 |

## 1. Calibration

_not scored in this run_


## 2. Survivors by bucket

### known (17)

- [arch/checklist/navigation/sev3] the way out of this area on foot towards waystone: ABSENT — No third distinct path leading out of the frame edge is visible in this shot.
- [arch/checklist/navigation/sev2] Item Shop: VISIBLE-BUT-ILLEGIBLE — The general store is obscured among the small distant background structures and foliage. _(also on square)_
- [orchard/checklist/navigation/sev3] the way out of this area on foot towards arch: ABSENT — No distinct path leading off-screen towards an arch is visible.
- [therise/checklist/occlusion/sev2] Cider press barn: OCCLUDED — Structure behind tree branches and dense leaves on the left.
- [square/checklist/navigation/sev3] the way out of this area on foot towards therise: ABSENT — Path toward the rise is not visible.
- [square/checklist/navigation/sev3] the way out of this area on foot towards pondlane: ABSENT — Pond lane exit is outside frame boundaries.
- [pondlane/checklist/occlusion/sev2] Washline green: OCCLUDED — The field is hidden behind the dense central trees and foliage.
- [pondlane/checklist/occlusion/sev2] Brook footbridge: OCCLUDED — The brook footbridge is occluded by the thick midground trees.
- [pondlane/checklist/occlusion/sev2] Brook mouth: OCCLUDED — The brook mouth is hidden behind the dense central vegetation.
- [pondlane/checklist/occlusion/sev2] Weir & sluice: OCCLUDED — The weir and sluice structure is hidden behind the heavy midground foliage.
- [pondlane/checklist/occlusion/sev2] Finn's smokehouse: OCCLUDED — The smokehouse is occluded by the dense trees near the center of the frame.
- [pondlane/checklist/occlusion/sev2] Pip's den: OCCLUDED — Pip's den is hidden under the bank behind the midground trees.
- [pondlane/checklist/occlusion/sev2] the route between Pond jetty and Brook footbridge: OCCLUDED — This section of path is hidden behind the midground tree growth.
- [pondlane/checklist/occlusion/sev2] the route between Pond jetty and Washline green: OCCLUDED — The path around the north shore is occluded by the tree canopy.
- [homerow/checklist/navigation/sev3] Brook spring: ABSENT — The spring source is completely hidden in the dark tree shadows with no visible water.
- [gateroad/checklist/occlusion/sev2] Rowan's house: OCCLUDED — Rowan's house is hidden behind the Tithe barn and surrounding foliage.
- [gatefield/checklist/occlusion/sev2] Downstream (vista beyond the Gate): OCCLUDED — Hidden from view behind the closed wooden gate and solid masonry wall.

### new (22)

- [woodroad/checklist/navigation/sev3] a door / entrance you can go through ("Leave Emberbrook"): ABSENT — There is no doorway or gateway structure in this open woodland clearing.
- [arch/checklist/navigation/sev2] Inn: VISIBLE-BUT-ILLEGIBLE — It appears as a generic distant village building without distinguishing inn features or legible detail. _(also on square)_
- [arch/checklist/navigation/sev2] Festival dais: VISIBLE-BUT-ILLEGIBLE — Too small and distant in the background lighting to clearly read as a festival dais.
- [arch/checklist/immersion/sev3] The water surface: FAILING — JUDGMENT: The water surface underneath the footbridge is rendered as an untextured, flat black void lacking transparency, water flow, or reflections. _(also on therise, square, pondlane, homerow, gateroad)_
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 56.1,61.7,5.3,12.5
- [orchard/checklist/navigation/sev3] Orchard rows: ABSENT — No apple trees in rows, ladders, or apple baskets are visible in this scene.
- [orchard/checklist/navigation/sev2] Cider press barn: VISIBLE-BUT-ILLEGIBLE — A roof structure is visible, but the area underneath is pitch black, making it impossible to see any cider press, crates, or straw to identify it as a cider press barn.
- [orchard/checklist/navigation/sev3] the route between Village Arch and Orchard rows: ABSENT — Neither the Village Arch nor the orchard rows are present in this frame.
- [orchard/checklist/navigation/sev3] the route between Orchard rows and Cider press barn: ABSENT — There is no orchard row present to form a path connecting to the barn.
- [therise/checklist/navigation/sev2] Poppy's bakery: VISIBLE-BUT-ILLEGIBLE — Stone structure lacks distinct visual features identifying it as a bakery. _(also on square)_
- [therise/checklist/immersion/sev2] The sky: WEAK — Visible sky area is a flat gradient with minimal atmospheric volume. _(also on pondlane)_
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 65.1,91.1,64.5,130.3
- [therise/checklist/immersion/sev2] The world at the frame edges: WEAK — Deep shadows near lower boundaries merge ground elements into dark shapes. _(also on square, pondlane)_
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region -19.4,126.5,12.7,149.1
- [square/checklist/navigation/sev3] the route between Village Arch and Festival Square: ABSENT — No arch or corresponding road section in this frame.
- [square/checklist/navigation/sev3] the route between Festival Square and Pond jetty: ABSENT — Pond jetty lane is not visible in shot.
- [square/checklist/navigation/sev3] the route between Festival Square and Tithe barn: ABSENT — Tithe barn road is not present in frame.
- [square/checklist/navigation/sev3] the route between Brook footbridge and Festival Square: ABSENT — Brook footbridge route is outside visible frame.
- [square/checklist/navigation/sev2] a door / entrance you can go through ("Enter Item Shop"): VISIBLE-BUT-ILLEGIBLE — Door opening is obscured in deep shadow.
- [pondlane/checklist/navigation/sev2] The Pond: VISIBLE-BUT-ILLEGIBLE — The body of water is rendered so dark and unreflective that it is indistinguishable from dark ground or heavy shadow under the trees.
- [homerow/checklist/navigation/sev3] Upper lane (closed): ABSENT — No cart or closed upper lane boundary is visible in this frame.
- [homerow/checklist/navigation/sev3] Grandmother's bench: ABSENT — Only wooden crates and barrels sit outside Lake's home; no bench is present there.
- [northlane/checklist/navigation/sev3] Back lane (closed): ABSENT — No closed lane with stacked barrels is visible in this frame.
- [northlane/checklist/navigation/sev3] the route between Festival Square and Tithe barn: ABSENT — There is no north lane enclosed by stone walls depicted in this view.
- [gatefield/checklist/navigation/sev3] the route between Sigil Gate court and Whisperwood trailhead: ABSENT — No separate path is drawn as the trailhead sits directly on the court rim.

### style-bar (0)



## 3. Budget

0 calls, 0 prompt + 0 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.