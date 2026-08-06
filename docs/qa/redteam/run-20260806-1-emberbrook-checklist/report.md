# Scene red-team — emberbrook — run 20260806-1-emberbrook-checklist

judge `gemini:gemini-3.6-flash` (pinned) · 11 plates · checklist

## 1. Calibration

_not scored in this run_


## 2. Survivors by bucket

### known (4)

- [arch/checklist/navigation/sev3] the way out of this area on foot towards orchard: ABSENT — No path leading off towards the orchard out of the frame edge is shown in this shot. _(also on orchard)_
- [pondlane/checklist/navigation/sev3] the way out of this area on foot towards square: ABSENT — The egress path from the pond area toward the square is not in view in this camera angle.
- [homerow/checklist/navigation/sev3] the route between Mara & Pip's cottage and Rowan's house: ABSENT — No paved path connects Mara & Pip's cottage to Rowan's house directly.
- [gatefield/checklist/occlusion/sev2] Downstream (vista beyond the Gate): OCCLUDED — The vista beyond the gate is completely hidden behind the closed stone wall.

### new (29)

- [woodroad/checklist/navigation/sev3] a door / entrance you can go through ("Leave Emberbrook"): ABSENT — No door or gateway visual exists in this outdoor forest scene.
- [orchard/checklist/navigation/sev3] Orchard rows: ABSENT — No apple orchard rows, ladders, or baskets are present in this view.
- [orchard/checklist/navigation/sev2] Cider press barn: VISIBLE-BUT-ILLEGIBLE — The structure's roof is visible, but the area underneath is pitch black in shadow, hiding any press, apple crates, or straw needed to identify it as a cider press barn.
- [orchard/checklist/navigation/sev3] the route between Village Arch and Orchard rows: ABSENT — The path connecting the Village Arch to the orchard rows is not in frame.
- [orchard/checklist/navigation/sev3] the route between Orchard rows and Cider press barn: ABSENT — No path connecting orchard rows to the cider press barn is present.
- [therise/checklist/navigation/sev2] Inn: VISIBLE-BUT-ILLEGIBLE — A building is visible in the background behind the square, but lacks identifying signage or features distinguishing it as an inn.
- [therise/checklist/navigation/sev2] Poppy's bakery: VISIBLE-BUT-ILLEGIBLE — A stone cottage stands near the square, but lacks visible bakery features or signs to identify it as Poppy's bakery.
- [square/checklist/navigation/sev3] the route between Village Arch and Festival Square: ABSENT — Village Arch area is off-screen.
- [square/checklist/navigation/sev3] the route between Festival Square and Pond jetty: ABSENT — Pond jetty route is off-screen.
- [square/checklist/navigation/sev3] the route between Festival Square and Mara & Pip's cottage: ABSENT — Cottage route is not visible in frame.
- [square/checklist/navigation/sev3] the route between Festival Square and Tithe barn: ABSENT — Tithe barn road is off-screen.
- [square/checklist/navigation/sev3] the route between Brook footbridge and Festival Square: ABSENT — Footbridge route is outside visible frame.
- [square/checklist/occlusion/sev2] a door / entrance you can go through ("Enter The Ember Hearth"): OCCLUDED — Door is hidden behind lower building structures and angle of view.
- [pondlane/checklist/navigation/sev3] The Pond: ABSENT — No body of water or pond is visible in this frame.
- [pondlane/checklist/navigation/sev3] Pond jetty: ABSENT — No jetty or fishing dock is present in this frame.
- [pondlane/checklist/navigation/sev3] Washline green: ABSENT — No washline green or drying field is visible in this frame.
- [pondlane/checklist/navigation/sev3] Brook footbridge: ABSENT — No brook or footbridge is present in this frame.
- [pondlane/checklist/navigation/sev3] Brook mouth: ABSENT — The brook mouth is not visible in this shot.
- [pondlane/checklist/navigation/sev3] Weir & sluice: ABSENT — No weir or sluice mechanism is visible in this frame.
- [pondlane/checklist/navigation/sev3] Finn's smokehouse: ABSENT — Finn's smokehouse is not present in this shot.
- [pondlane/checklist/navigation/sev3] Pip's den: ABSENT — Pip's den is not visible in this frame.
- [pondlane/checklist/navigation/sev3] the route between Festival Square and Pond jetty: ABSENT — The route to the pond jetty is not visible in this shot.
- [pondlane/checklist/navigation/sev3] the route between Pond jetty and Brook footbridge: ABSENT — The path between the jetty and brook footbridge is not in this frame.
- [pondlane/checklist/navigation/sev3] the route between Pond jetty and Washline green: ABSENT — The path to Washline green is not present in this frame.
- [homerow/checklist/navigation/sev3] Brook spring: ABSENT — No water spring is visible anywhere in this frame.
- [homerow/checklist/navigation/sev3] Upper lane (closed): ABSENT — No closed upper lane or festival cart is present in this view.
- [homerow/checklist/navigation/sev3] Spring house: ABSENT — There is no stone spring house in the scene.
- [homerow/checklist/navigation/sev3] Grandmother's bench: ABSENT — No second bench outside Lake's home is visible.
- [homerow/checklist/navigation/sev3] the route between Rowan's house and Hilltop bench: ABSENT — There is no established path leading between Rowan's house and the bench.

### style-bar (0)



## 3. Budget

20 calls, 41568 prompt + 45998 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.