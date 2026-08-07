# Scene red-team — dellhollow — run 20260807-round3

judge `gemini:gemini-3.6-flash` (pinned) · 2 plates · checklist

## 1. Calibration

_not scored in this run_


## 2. Survivors by bucket

### known (0)


### new (2)

- [quay-west/checklist/immersion/sev3] The water surface: FAILING — There is no water surface rendered anywhere around or beneath the quay deck, leaving only dry earth and rock beneath the structures. _(also on deep-stairs)_
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 40.5,66,8.5,21.9
- [deep-stairs/checklist/navigation/sev2] Cookhouse: VISIBLE-BUT-ILLEGIBLE — While wooden buildings are visible along the upper cliff, none read clearly as a cookhouse or tavern hub without distinct features or glowing windows.

### style-bar (0)



## 3. Budget

4 calls, 7472 prompt + 11227 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.