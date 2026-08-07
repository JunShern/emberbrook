# Scene red-team — dellhollow — run 20260807-064138

judge `gemini:gemini-3.6-flash` (pinned) · 7 plates · checklist

## 1. Calibration

_not scored in this run_


## 2. Survivors by bucket

### known (3)

- [quay-west/checklist/navigation/sev3] the way out of this area on foot towards lockhead: ABSENT — The path toward lockhead is not visible in this frame.
- [quay-west/checklist/navigation/sev3] the way out of this area on foot towards weave: ABSENT — The path toward weave is not visible in this frame.
- [lockfive/checklist/navigation/sev3] the way out of this area on foot towards north-landing: ABSENT — No foot path leading out of the frame towards north-landing exists in this shot.

### new (4)

- [gate/checklist/navigation/sev2] Inn: VISIBLE-BUT-ILLEGIBLE — Distant dockside buildings are visible but lack identifying features.
- [gate/checklist/immersion/sev3] The world at the frame edges: WEAK — JUDGMENT: Distant cliff wall ends abruptly against a flat gray sky plane. _(also on crossing)_
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 15.1,150.1,8.9,57.7
- [gate/checklist/immersion/sev3] The water surface: WEAK — JUDGMENT: Basic turquoise surface shader with simple contact edges at docks. _(also on quay-west)_
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region -0.3,150.1,-1.9,14.2
- [lockfive/checklist/navigation/sev3] Dam Crest Gate: ABSENT — No iron-banded dam crest gate is visible anywhere in this frame.

### style-bar (0)



## 3. Budget

11 calls, 23698 prompt + 33583 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.