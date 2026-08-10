# Scene red-team — dellhollow — run round10before

judge `gemini:gemini-3.6-flash` (pinned) · 2 plates · naive

## 1. Calibration

_not scored in this run_


## 2. Survivors by bucket

### known (0)


### new (16)

- [cottage/naive/occlusion/sev2] A pitch-black shadow completely obscures the cliff face and structures underneath, concealing geometry and potential paths.
- [cottage/naive/navigation/sev2] The middle section of the wooden walkway collapses into fragmented, overlapping planks, making it visually ambiguous whether the route is walkable or impassable visual noise.
- [cottage/naive/geometry/sev2] The ladder extends upwards and clips directly into the solid underside of the wooden bridge deck with no opening for a player to climb through.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 79,84,15.2,19.3
- [cottage/naive/navigation/sev2] The chaotic overlap of broken wooden planks makes it ambiguous whether this is a walkable slope or impassable visual debris.
- [cottage/naive/occlusion/sev2] An extremely dark pitch-black shadow completely obscures the cliff geometry and hut structure, hiding potential pathways.
- [cottage/naive/immersion/sev1] A conical tree model sticks directly out of a steep vertical rock wall without visible support or roots.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 91.7,95.5,15.5,18.9
- [cottage/naive/occlusion/sev2] A harsh, completely black shadow conceals the terrain and building geometry beneath the upper cliff, making depth and pathing unreadable.
- [cottage/naive/immersion/sev1] The stylized tree or cone prop is attached horizontally to a vertical cliff face without any supporting ledge or surface.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 91.7,95.5,15.5,18.9
- [cottage/naive/geometry/sev1] Wooden planks and support beams intersect and clip haphazardly into each other without structural joins.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 83.6,92.2,14.4,21.2
- [weave/naive/navigation/sev2] The dense layering of wooden platforms, roofs, and stilts without clear visual distinction makes it difficult to discern walkable paths from roofs.
- [weave/naive/immersion/sev2] The cave entrance is a flat pitch-black polygon without ambient lighting or geometry falloff, breaking environment realism.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 82.9,133.7,-2.4,18.2
- [weave/naive/geometry/sev1] Wooden fence posts and support beams clip directly through the sloped roof surfaces below.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 47.2,61.8,7,21.7
- [weave/naive/navigation/sev2] Uniform brown wood materials across roofs, walkways, railings, and support pillars create high visual noise, making walkable paths visually indistinguishable from roofs.
- [weave/naive/navigation/sev1] Multiple overlapping stairs, ramps, and roof edges share identical colors and silhouettes, making the climbing route up the cliff face visually confusing.
- [weave/naive/navigation/sev2] Multiple overlapping layers of dark wooden boardwalks, roofs, and stilts blend together, making it difficult to distinguish walkable paths from non-traversable architecture.
- [weave/naive/exit/sev2] The cave entrance is a completely flat, pitch-black void without depth or lighting falloff, making it ambiguous whether it is an accessible tunnel or background art.

### style-bar (0)



## 3. Budget

8 calls, 12216 prompt + 13861 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.