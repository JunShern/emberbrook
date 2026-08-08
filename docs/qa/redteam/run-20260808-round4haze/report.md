# Scene red-team — dellhollow — run 20260808-round4haze

judge `gemini:gemini-3.6-flash` (pinned) · 4 plates · naive + checklist

## 1. Calibration

_not scored in this run_


## 2. Survivors by bucket

### known (4)

- [crossing/naive/immersion/sev2] A flat board floats unsupported in mid-air above the water surface near the pier.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 99.9,107.7,30.6,37.6
- [lockfive/naive/geometry/sev2] The wooden stair steps float in mid-air without structural supports or pillars holding them up.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 65.8,94.7,21.3,32.6
- [lockfive/naive/geometry/sev2] The wooden staircase steps float independently in mid-air without any stringers or support beams holding them.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 66.1,85,21.2,30.4
- [lockfive/naive/geometry/sev2] The stair treads float in mid-air without structural side stringers or supports connecting them.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 64.5,93.2,20.1,30

### new (17)

- [gate/naive/geometry/sev2] The cliff geometry cuts off abruptly in a straight vertical line, exposing the background void.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 27.1,152.1,-4.2,8
- [gate/naive/immersion/sev1] The foliage cluster floats in mid-air off the cliff side without a visible trunk or connection to the rock.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region -0.8,11,-0.3,4.4
- [gate/naive/geometry/sev2] The cliff geometry abruptly terminates in a sharp vertical edge against the background mountain.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 52.3,122.2,-2.9,5.1
- [gate/checklist/navigation/sev2] Inn: VISIBLE-BUT-ILLEGIBLE — Blends in with surrounding wooden structures without defining signage.
- [gate/checklist/immersion/sev3] The world at the frame edges: WEAK — Vertical seam where cliff geometry ends abruptly against background fog. _(also on crossing, weave)_
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 24.6,152.1,-2.7,8.2
- [gate/checklist/immersion/sev2] The water surface: WEAK — Lacks convincing depth transparency and soft foam at shore contact.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 7.8,125.6,12.2,72.6
- [crossing/naive/geometry/sev2] An untextured white polygon clips into the bottom right corner of the scene.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,70,12.7,17.2
- [crossing/naive/geometry/sev2] An untextured bright grey plane cuts abruptly through the terrain geometry along the bottom right edge.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.5,70,12.7,17.2
- [crossing/naive/geometry/sev2] An untextured white wedge cuts into the scene along the bottom-right frame edge.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.5,70,12.7,17.2
- [crossing/naive/immersion/sev1] A wooden board floats static in mid-air right above the water surface without support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 100.2,107,30.8,37.6
- [crossing/checklist/navigation/sev3] the route between Weave huts and Keepers' Cottage: ABSENT — No high plank bridge spanning across the water basin is present in this view.
- [weave/naive/navigation/sev2] The dense layering of roofs, railings, and elevated platforms makes it difficult to discern walkable pathways from non-traversable architecture.
- [lockfive/naive/navigation/sev2] Multiple overlapping tiers of docks and ramps create a confusing tangle where walkable paths cannot be clearly distinguished.
- [lockfive/naive/geometry/sev1] The wooden railing segment in the foreground ends abruptly with unattached beams floating in space.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.4,72.9,29,37
- [lockfive/naive/immersion/sev1] The wooden railing section near the bottom floats above the water without vertical posts anchoring it to the pier structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 67.4,72.8,29.1,36.5
- [lockfive/naive/navigation/sev2] Multiple overlapping platforms, posts, and stairs meet at chaotic angles, making the readable path up from the docks ambiguous.
- [lockfive/checklist/navigation/sev3] Dam Crest Gate: ABSENT — The iron-banded gate barring the dam crest walk is not visible in this frame.

### style-bar (0)



## 2b. Aim census — did the judge point at what it named?

0 of 4 [QUALITY] verdicts REFUTED: the judge's own box held under 2% of the subject the verdict names. 1 on-subject, 0 absence-claim (census abstains), 3 unmeasurable.

- `quality:frame-edge-world` — 0/3 refuted; box coverage n/a
- `quality:water-read` — 0/1 refuted; box coverage 44.3%


## 3. Budget

24 calls, 41614 prompt + 47438 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.