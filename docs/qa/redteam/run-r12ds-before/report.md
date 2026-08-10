# Scene red-team — dellhollow — run r12ds-before

judge `gemini:gemini-3.6-flash` (pinned) · 1 plates · naive

## 1. Calibration

_not scored in this run_


## 2. Survivors by bucket

### known (11)

- [deep-stairs/naive/geometry/sev2] The long wooden staircase spans a large open gap with no supporting beams or columns underneath.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 32.3,49.1,17.6,29.2
- [deep-stairs/naive/immersion/sev2] The long wooden staircase spans across a deep gap with no visible supporting posts or beams underneath.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 32.3,49.7,17.6,28.6
- [deep-stairs/naive/occlusion/sev2] Pitch-black cast shadows completely obscure the cliff wall and middle landing, hiding terrain details and potential paths.
- [deep-stairs/naive/navigation/sev2] Dark shadows inside the cliff doorway obscure whether the walkway continues inside or terminates.
- [deep-stairs/naive/navigation/sev2] Deep, harsh cast shadows obscure the cliff face and staircase landings, making it ambiguous whether the area is walkable or where the path leads.
- [deep-stairs/naive/geometry/sev2] The long diagonal staircase span lacks adequate vertical support structures underneath, making it appear to float over the terrain.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 32.3,47.9,18,27.4
- [deep-stairs/naive/immersion/sev2] The wooden plank ramp floats above the sloped rock surface without any visible pillars or supports holding it up.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 32,43.1,18,28.8
- [deep-stairs/naive/navigation/sev2] A harsh directional shadow cuts straight across the wooden staircase, obscuring step geometry and making it difficult to discern if the path is walkable.
- [deep-stairs/naive/navigation/sev2] The main staircase transitions into visually cluttered, floating ramp segments where the continuation of the path is ambiguous.
- [deep-stairs/naive/navigation/sev2] Harsh cast shadows obscure where the long outdoor staircase connects to the upper platform, making it difficult to discern if the path is walkable.
- [deep-stairs/naive/occlusion/sev2] Pitch-black shadow completely hides the spatial layout and potential doorways or paths inside the central cliffside structure.

### new (19)

- [deep-stairs/naive/occlusion/sev2] Harsh, deep shadows completely obscure the path and doorway beneath the upper structure, hiding potential pathways.
- [deep-stairs/naive/geometry/sev2] The wooden plank walkway clips directly into the rocky slope at sharp angles without supporting posts or groundwork.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 31.7,44.2,18.9,30
- [deep-stairs/naive/occlusion/sev2] A heavy shadow cuts across the central cliff section, rendering pathways and geometry in complete darkness.
- [deep-stairs/naive/navigation/sev2] Multiple overlapping wooden staircases and ramps crisscross at steep, ambiguous angles, making it difficult to discern readable walking paths.
- [deep-stairs/naive/occlusion/sev2] A very harsh black shadow obscures the central cliff face and structural elements, making terrain and navigation paths hidden.
- [deep-stairs/naive/geometry/sev2] The long central wooden staircase spans across open space without visible structural support beams or posts beneath it.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 32.4,48.6,16.3,30
- [deep-stairs/naive/navigation/sev2] The illuminated passageway at the top of the stairs terminates into dense shadow, making it ambiguous whether it is an accessible route.
- [deep-stairs/naive/geometry/sev1] Multiple wooden walkway ramps clip directly into each other without supporting joints or clean alignments.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 31.6,44.2,18.9,29.8
- [deep-stairs/naive/immersion/sev1] A single wooden pole extends seamlessly across multiple vertical tiers down to the pier without realistic structural framing or joints.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 43,52.2,17.7,30
- [deep-stairs/naive/occlusion/sev2] Extremely pitch-black shadows obscure the upper cliff area, making it impossible to see if the structure continues or if there is a walkable path.
- [deep-stairs/naive/navigation/sev2] Multiple overlapping staircases and ramps blend together into the shadowed cliff, creating visual confusion about where the player can walk.
- [deep-stairs/naive/occlusion/sev2] Pitch-black shadow covers the central upper staircase and passageway, hiding path boundaries and making navigation ambiguous.
- [deep-stairs/naive/navigation/sev2] Multiple overlapping staircases, ramps, and platforms tangle together, making it difficult to discern walkable pathways from visual background detail.
- [deep-stairs/naive/geometry/sev1] Thin vertical wooden posts clip directly into the rough cliff rock face without visible mounts or ground anchoring.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 27.3,31.5,17.2,23.6
- [deep-stairs/naive/occlusion/sev2] Extreme shadow darkness under the upper cliff overhang hides structural depth and potential pathways or exits.
- [deep-stairs/naive/geometry/sev1] The long angled wooden beam extends down from the upper structure and clips directly into the lower platform deck.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 42.1,49.5,19.8,30
- [deep-stairs/naive/occlusion/sev2] Extremely deep cast shadows hide the geometry inside the cliff cavity, making it impossible to read depth or discern walkable paths.
- [deep-stairs/naive/geometry/sev1] An unrealistically long, thin diagonal wooden post stretches continuously between the upper deck and lower dock without structural logic.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 42.1,49.5,20,30
- [deep-stairs/naive/geometry/sev1] The long angled wooden beam clips directly into the boardwalk floor without a visible mounting joint or anchor.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 42.8,52.2,17.7,28.2

### style-bar (0)



## 3. Budget

11 calls, 17229 prompt + 18845 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.