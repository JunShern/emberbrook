# Scene red-team — dellhollow — run round10uv

judge `gemini:gemini-3.6-flash` (pinned) · 2 plates · naive

## 1. Calibration

_not scored in this run_


## 2. Survivors by bucket

### known (1)

- [cottage/naive/geometry/sev2] The collapsed wooden ramp consists of floating, disjointed plank segments without proper physics or visual support underneath.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 86.6,96,16.5,24.3

### new (8)

- [cottage/naive/navigation/sev2] The main wooden walkway is fractured into jagged, disjointed planks, making it unclear whether it is a walkable path or an impassable hazard.
- [cottage/naive/immersion/sev2] A stylized green tree model floats in mid-air off the cliff face without any attachment or structural support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 91.7,95.4,15.5,18.9
- [cottage/naive/navigation/sev2] The wooden walkway is broken into steep, disjointed, overlapping planks, making it ambiguous whether it is navigable or blocked rubble.
- [cottage/naive/occlusion/sev2] Heavy cast shadows obscure the lower ground beneath the broken bridge, hiding whether the terrain underneath is walkable or an drop.
- [weave/naive/navigation/sev2] The dense visual overlap between wooden walkways and adjacent roofs made of identical materials makes distinguishing walkable paths from impassable roofs difficult.
- [weave/naive/navigation/sev2] Dense layering of sloped roofs and flat walkways makes it ambiguous which surfaces are walkable paths and which are inaccessible rooftops.
- [weave/naive/immersion/sev2] The elevated deck floor exhibits severe z-fighting and flickering texture patterns intersecting through the platform boards.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 49.8,61.9,9.6,21.5
- [weave/naive/navigation/sev2] The dense overlap of wooden platforms, roofs, and stilts using uniform textures makes it difficult to distinguish walkable paths from non-navigable roofs.

### style-bar (0)



## 3. Budget

8 calls, 12027 prompt + 12445 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.