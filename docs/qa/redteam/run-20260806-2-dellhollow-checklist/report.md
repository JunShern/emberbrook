# Scene red-team — dellhollow — run 20260806-2-dellhollow-checklist

judge `gemini:gemini-3.6-flash (replayed from run-tmp-qv-del + run-tmp-qr-del)` (pinned) · 15 plates · checklist

## 0. Which plates were judged this round

| plate | critique | replies from | bake judged against | survivors |
|---|---|---|---|---|
| gate | **REPLAYED** | run-tmp-qv-del | 2026-08-06T22:07:32Z | 2 |
| shelf-west | **FRESH** | run-tmp-qr-del | 2026-08-06T22:15:20Z | 5 |
| shelf-east | **FRESH** | run-tmp-qr-del | 2026-08-06T22:15:20Z | 4 |
| loop-stairs | **FRESH** | run-tmp-qr-del | 2026-08-06T11:26:59Z | 0 |
| quay-west | **FRESH** | run-tmp-qr-del | 2026-08-06T22:07:32Z | 0 |
| lockhead | **FRESH** | run-tmp-qr-del | 2026-08-06T11:26:59Z | 0 |
| cottage | **FRESH** | run-tmp-qr-del | 2026-08-06T11:26:59Z | 1 |
| crossing | **REPLAYED** | run-tmp-qv-del | 2026-08-06T22:07:32Z | 0 |
| weave | **FRESH** | run-tmp-qr-del | 2026-08-06T22:07:32Z | 0 |
| deep-stairs | **FRESH** | run-tmp-qr-del | 2026-08-06T22:07:32Z | 1 |
| boatyard | **FRESH** | run-tmp-qr-del | 2026-08-06T22:07:32Z | 6 |
| waterfront | **REPLAYED** | run-tmp-qv-del | 2026-08-06T21:37:17Z | 1 |
| fishdock | **FRESH** | run-tmp-qr-del | 2026-08-06T22:07:32Z | 0 |
| lockfive | **REPLAYED** | run-tmp-qv-del | 2026-08-06T22:07:32Z | 2 |
| north-landing | **FRESH** | run-tmp-qr-del | 2026-08-06T21:40:37Z | 1 |

## 1. Calibration

_not scored in this run_


## 2. Survivors by bucket

### known (4)

- [shelf-west/checklist/navigation/sev3] the route between Valley Gate and Inn: ABSENT — The specified stair descent is not visible in frame.
- [shelf-west/checklist/navigation/sev3] the way out of this area on foot towards gate: ABSENT — No gate path exits the frame from this angle.
- [lockfive/checklist/navigation/sev3] Lock Five: ABSENT — The lock basin and lock gates are not present in this camera view.
- [north-landing/checklist/navigation/sev3] the way out of this area on foot towards lockfive: ABSENT — No pedestrian exit path leading out of the frame toward Lock Five is visible in this view.

### new (19)

- [gate/checklist/navigation/sev2] Inn: VISIBLE-BUT-ILLEGIBLE — The buildings at the harbor level are too small, shadowed, and distant to uniquely identify which structure is the Boatmen's Rest inn.
- [gate/checklist/immersion/sev3] The world at the frame edges: WEAK — The top-left background fades into a flat, empty dark void with starkly cut mountain silhouettes rather than a fully rendered sky and horizon. _(also on shelf-east, loop-stairs, weave, lockfive)_
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 14.4,145.5,-2.7,72.6
- [shelf-west/checklist/navigation/sev2] the route between Item Shop (chandlery skin) and Weapon Shop: VISIBLE-BUT-ILLEGIBLE — Path section behind platform supports is obscured by darkness.
- [shelf-west/checklist/occlusion/sev2] a door / entrance you can go through ("Enter The Boatmen's Rest"): OCCLUDED — Entrance is obscured by roof overhang and deep shadow.
- [shelf-west/checklist/navigation/sev3] Weapon Shop: VISIBLE-BUT-ILLEGIBLE — Building lacks distinctive weapon visual cues in this view. _(also on shelf-east)_
- [shelf-east/checklist/navigation/sev3] Armor Shop: ABSENT — No shop armor items are visible.
- [shelf-east/checklist/navigation/sev2] a door / entrance you can go through ("Enter Weapon Shop"): VISIBLE-BUT-ILLEGIBLE — Dark opening heavily obscured by roof shadow.
- [shelf-east/checklist/navigation/sev2] a door / entrance you can go through ("Enter Armor Shop"): VISIBLE-BUT-ILLEGIBLE — Recessed dark doorway hidden under deep overhangs.
- [shelf-east/checklist/immersion/sev3] The water surface: WEAK — Water reads as a plain dark plane with minimal shore integration or specular reflections. _(also on quay-west, deep-stairs)_
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region -11.5,50.2,10.2,78.6
- [cottage/checklist/occlusion/sev2] a door / entrance you can go through ("Enter Keepers' Cottage"): OCCLUDED — The cottage doorway is hidden behind the pile of collapsed wooden beams and bridge debris.
- [deep-stairs/checklist/navigation/sev2] Cookhouse: VISIBLE-BUT-ILLEGIBLE — Wooden buildings are visible on the upper stilt platforms, but without distinct features, signage, or glowing interior light, none can be identified as a cookhouse.
- [boatyard/checklist/navigation/sev3] Pitch kettle: ABSENT — No pitch kettle or curling tar smoke is present in the scene.
- [boatyard/checklist/navigation/sev3] Lock Four overlook: ABSENT — No lock overlook post or spray-covered viewpoint under lock gates exists here.
- [boatyard/checklist/navigation/sev3] Lock Four (set dressing): ABSENT — No lock structure or lock gates are visible anywhere in this frame.
- [boatyard/checklist/navigation/sev3] the route between Cargo Winch (foot) and Slipway: ABSENT — No cargo winch exists in this shot to form a route with.
- [boatyard/checklist/navigation/sev3] the route between Boatwright's shed and Pitch kettle: ABSENT — Pitch kettle is absent from the scene.
- [boatyard/checklist/navigation/sev3] the route between Slipway and Lock Four overlook: ABSENT — Lock Four overlook is absent from the scene.
- [waterfront/checklist/navigation/sev3] Cargo Winch (foot): ABSENT — No winch mechanism or machine with a drum or crank is present at the quay level.
- [lockfive/checklist/navigation/sev3] Dam Crest Gate: ABSENT — The iron-banded gate barring the dam-crest walkway is not visible in this frame. _(also on north-landing)_

### style-bar (0)



## 3. Budget

0 calls, 0 prompt + 0 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.