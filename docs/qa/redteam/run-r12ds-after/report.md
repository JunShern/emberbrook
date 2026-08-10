# Scene red-team — dellhollow — run r12ds-after

judge `gemini:gemini-3.6-flash` (pinned) · 1 plates · naive

## 1. Calibration

_not scored in this run_


## 2. Survivors by bucket

### known (7)

- [deep-stairs/naive/occlusion/sev2] Harsh, pitch-black cast shadows completely obscure the cliff interior and terrain depth behind the staircase, hiding potential pathways.
- [deep-stairs/naive/geometry/sev2] The zigzagging wooden boardwalk ramps float over the ground and clip into one another without visible support pillars underneath.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 31.7,44.9,18.9,29.5
- [deep-stairs/naive/immersion/sev1] The plank walkway geometry hovers above the terrain surface with visible gaps underneath.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 31.5,44.8,18.8,29.9
- [deep-stairs/naive/occlusion/sev2] Deep cast shadow completely obscures the upper cliff pathway and stairwell, making it difficult to read where the path leads.
- [deep-stairs/naive/immersion/sev1] The long wooden staircase hangs over a wide gap with no visible supports or beams underneath.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 32.5,50,16.3,27.2
- [deep-stairs/naive/occlusion/sev2] A heavy cast shadow completely obscures the upper stair landings and rock wall, making path continuity impossible to see.
- [deep-stairs/naive/geometry/sev2] The long diagonal wooden staircase lacks support pillars or structural anchoring, appearing to float unsupported over the drop.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 32.3,49.7,16.4,27.4

### new (13)

- [deep-stairs/naive/occlusion/sev2] Heavy pitch-black shadows obscure the vertical depth and terrain below the walkways, making it impossible to see if falling off is fatal.
- [deep-stairs/naive/immersion/sev1] The long wooden staircase spans across the open chasm without vertical support posts or beams anchoring its midsection.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 32.3,47.8,17.5,30.5
- [deep-stairs/naive/geometry/sev2] The multi-tiered plank walkway hovers above the uneven cliffside terrain without legs or structural ground contacts.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 26.3,36.1,17.9,31
- [deep-stairs/naive/geometry/sev1] The large wooden hull clips directly into the surrounding timber platform without visible joinery or structural supports.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 26.9,33.6,18.7,31.8
- [deep-stairs/naive/occlusion/sev2] Deep pitch-black shadow completely obscures the vertical terrain and any potential doorways or path extensions behind the structures.
- [deep-stairs/naive/geometry/sev1] The wooden plank walkways overlap and intersect at unnatural angles without clear supporting posts or structural joins.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 32,43.1,17.9,29.8
- [deep-stairs/naive/geometry/sev1] The thin support beam clips directly through the platform floor without proper structural framing or joints.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 42.1,49.7,19.8,30
- [deep-stairs/naive/geometry/sev2] A long diagonal wooden support pole clips directly through the edge of the lower roof platform without any joint or structural connection.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 43,52.2,17.7,30
- [deep-stairs/naive/geometry/sev2] The long wooden support pole clips straight through the lower platform's railing and deck planks.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 42,49.6,19.8,30
- [deep-stairs/naive/occlusion/sev2] Deep, high-contrast shadows completely black out the cliff crevice, obscuring whether there is a passable ledge, doorway, or obstacle inside.
- [deep-stairs/naive/immersion/sev1] The wooden walkway ramps float over the sloped terrain without supporting posts or anchoring geometry beneath them.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 31.6,43.3,18.3,29.6
- [deep-stairs/naive/geometry/sev1] The large dark wooden hull clips directly into the adjacent scaffolding and floor planks.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 26.7,33.6,18.7,31.9
- [deep-stairs/naive/occlusion/sev2] Extremely harsh cast shadows completely obscure the cliffside structures and terrain, hiding potential paths and geometry.

### style-bar (0)



## 3. Budget

11 calls, 17150 prompt + 18706 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.