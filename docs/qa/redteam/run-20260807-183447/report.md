# Scene red-team — dellhollow — run 20260807-183447

judge `gemini:gemini-3.6-flash` (pinned) · 1 plates · naive + checklist

## 1. Calibration

_not scored in this run_


## 2. Survivors by bucket

### known (0)


### new (6)

- [boatyard/naive/immersion/sev1] The lower right end of the bunting flag line hangs and terminates in mid-air without attaching to any pole or wall.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 18.1,27.4,18.2,32.9
- [boatyard/naive/immersion/sev1] Foliage assets are embedded directly into the flat rock face without visible stems, soil, or crevices.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 16.9,26.9,17.4,21.5
- [boatyard/checklist/navigation/sev3] Pitch kettle: ABSENT — No pitch kettle or curling tar smoke is visible in the scene.
- [boatyard/checklist/navigation/sev3] Lock Four (set dressing): ABSENT — No canal lock or lock gate structure is visible anywhere in the frame.
- [boatyard/checklist/navigation/sev3] the route between Cargo Winch (foot) and Slipway: ABSENT — No cargo winch is present in this view, so this route cannot be identified.
- [boatyard/checklist/navigation/sev3] the route between Boatwright's shed and Pitch kettle: ABSENT — Since the pitch kettle is absent, this route cannot be traced.

### style-bar (0)



## 3. Budget

6 calls, 9837 prompt + 15393 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.