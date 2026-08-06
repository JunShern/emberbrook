# Scene red-team — dellhollow — run 20260806-1-dellhollow-checklist

judge `gemini:gemini-3.6-flash` (pinned) · 15 plates · checklist

## 1. Calibration

_not scored in this run_


## 2. Survivors by bucket

### known (4)

- [shelf-west/checklist/occlusion/sev2] the route between Valley Gate and Inn: OCCLUDED — The stair flight descending from the upper area is hidden behind the upper platform deck and support beams.
- [shelf-west/checklist/navigation/sev3] the way out of this area on foot towards shelf-east: ABSENT — No path leading off-frame towards shelf-east is present in this view.
- [loop-stairs/checklist/navigation/sev3] the way out of this area on foot towards shelf-east: ABSENT — No path continuing off-screen to the east along the upper shelf is visible in the scene.
- [lockfive/checklist/navigation/sev3] the way out of this area on foot towards north-landing: ABSENT — No third foot path exit is present in this view.

### new (18)

- [shelf-west/checklist/navigation/sev3] the route between Item Shop (chandlery skin) and Weapon Shop: ABSENT — The road section leading to the Weapon Shop is not visible because the Weapon Shop is not in this shot.
- [shelf-west/checklist/occlusion/sev2] a door / entrance you can go through ("Enter The Boatmen's Rest"): OCCLUDED — The door to enter the Inn is obscured in shadow beneath the lower overhang.
- [shelf-west/checklist/occlusion/sev2] a door / entrance you can go through ("Enter Item Shop"): OCCLUDED — The entrance door to the Item Shop is hidden behind its counter facade and side walls.
- [shelf-east/checklist/navigation/sev3] Weapon Shop: ABSENT — No shop weapons are visible in the scene.
- [shelf-east/checklist/navigation/sev3] Armor Shop: ABSENT — No armor pieces are visible on display.
- [shelf-east/checklist/navigation/sev2] a door / entrance you can go through ("Enter Weapon Shop"): VISIBLE-BUT-ILLEGIBLE — Darkened wall opening lacks clear door framing or interactive cues.
- [shelf-east/checklist/occlusion/sev2] a door / entrance you can go through ("Enter Armor Shop"): OCCLUDED — Hidden behind elevated wooden structures and roofs.
- [shelf-east/checklist/navigation/sev2] Inn: VISIBLE-BUT-ILLEGIBLE — Reads as a generic wooden structure without identifying inn features.
- [quay-west/checklist/navigation/sev2] a door / entrance you can go through ("Enter Cookhouse"): VISIBLE-BUT-ILLEGIBLE — The recessed doorway under the cookhouse eaves is too dark and merges into the surrounding shadowed wood.
- [cottage/checklist/occlusion/sev2] a door / entrance you can go through ("Enter Keepers' Cottage"): OCCLUDED — The entrance to the cottage is hidden behind the wooden scaffolding and collapsed walkway timbers.
- [boatyard/checklist/navigation/sev3] Pitch kettle: ABSENT — No pitch kettle or curling tar smoke is present in the scene.
- [boatyard/checklist/navigation/sev3] Lock Four (set dressing): ABSENT — No upstream water lock gates or Lock Four set dressing are visible in the scene.
- [boatyard/checklist/navigation/sev3] the route between Cargo Winch (foot) and Slipway: ABSENT — The cargo winch and its connecting deck route are not present in this view.
- [boatyard/checklist/navigation/sev3] the route between Boatwright's shed and Pitch kettle: ABSENT — The route cannot exist because the pitch kettle is absent.
- [waterfront/checklist/navigation/sev3] Cargo Winch (foot): ABSENT — Cargo Winch (foot) is not visible in this scene.
- [waterfront/checklist/navigation/sev3] the route between Cargo Winch (foot) and Slipway: ABSENT — The route connected to the Cargo Winch is not present as the cargo winch is absent.
- [waterfront/checklist/navigation/sev3] the route between Fish dock and Cargo Winch (foot): ABSENT — The route between Fish dock and Cargo Winch is absent.
- [lockfive/checklist/navigation/sev3] Dam Crest Gate: ABSENT — No iron-banded gate barring a dam crest path is visible in this frame.

### style-bar (0)



## 3. Budget

23 calls, 44452 prompt + 56517 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.