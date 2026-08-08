# Scene red-team — dellhollow — run 20260808-round6phase

judge `gemini:gemini-3.6-flash` (pinned) · 7 plates · naive + checklist

## 1. Calibration

_not scored in this run_


## 2. Survivors by bucket

### known (10)

- [shelf-east/checklist/navigation/sev3] the way out of this area on foot towards loop-stairs: ABSENT — The exit path toward loop-stairs is not visible in this frame.
- [waterfront/naive/immersion/sev2] A wooden step platform floats unsupported in mid-air above the water stream.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 37.5,43.8,22.4,28.7
- [waterfront/naive/geometry/sev2] A wooden plank platform floats unsupported in mid-air over the gap between the shore and lower deck.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 31.9,38.3,26.1,31.4
- [lockfive/naive/geometry/sev2] The wooden stair treads float suspended in mid-air without structural supports or stringers attached to the platform or ground.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 64.2,94.4,23.6,30
- [lockfive/naive/geometry/sev2] The wooden steps forming the staircase float in mid-air without supporting stringers or side frames.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 67.3,85,21.2,30.3
- [lockfive/naive/geometry/sev2] The wooden stair steps float in mid-air without any stringers, risers, or support beams beneath them.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 67.3,85,21.3,32.7
- [north-landing/naive/immersion/sev1] Rectangular stepping stones float on the water surface without visible depth or submerged base.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 86.8,95.2,33,42.3
- [north-landing/naive/immersion/sev1] A green wooden plank platform floats in the water without visible support pillars or attachment points.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 97.1,106.2,31.2,36.7
- [north-landing/naive/geometry/sev1] The stepping stones appear as thin flat tiles floating on the water surface with no underwater base or visible support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 86.8,95.4,33.1,42.3
- [north-landing/naive/immersion/sev1] A wooden plank platform floats freely on top of the water without any supports, tether, or connection to nearby structures.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 97.2,106.3,31.1,36.9

### new (39)

- [gate/naive/immersion/sev2] An untextured orange wedge of background geometry clips through the top-left sky backdrop.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 143.1,147.9,53.3,76.6
- [gate/checklist/immersion/sev3] The world at the frame edges: WEAK — WEAK — Distant cliff faces lack detail and fade abruptly into simple background haze. _(also on shelf-east, crossing, weave, lockfive)_
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 14.7,144.7,-1.8,72.6
- [shelf-east/naive/immersion/sev1] A gray rectangular pillar hangs in mid-air in the cavern background without connecting to any ceiling or structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region -89.3,42.1,9.5,69.5
- [shelf-east/naive/geometry/sev1] A white tarp sheet clips directly into the green tiled roof without any frame or supporting structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 30.7,50.3,-0.3,7.2
- [shelf-east/checklist/navigation/sev3] Weapon Shop: ABSENT — No shop weapons are visible in the scene.
- [shelf-east/checklist/navigation/sev3] Armor Shop: ABSENT — No shop armor is visible in the scene.
- [shelf-east/checklist/occlusion/sev2] a door / entrance you can go through ("Enter Weapon Shop"): OCCLUDED — The entrance is obscured by structural overhangs and deep shadow.
- [shelf-east/checklist/occlusion/sev2] a door / entrance you can go through ("Enter Armor Shop"): OCCLUDED — The doorway is blocked from view by rooflines and building angles.
- [shelf-east/checklist/navigation/sev2] Cookhouse: VISIBLE-BUT-ILLEGIBLE — The building is clear, but lacks features identifying it specifically as a cookhouse.
- [shelf-east/checklist/navigation/sev2] Inn: VISIBLE-BUT-ILLEGIBLE — Reads as a generic wooden structure without clear inn identifiers.
- [crossing/naive/geometry/sev2] A plain white untextured geometric plane clips through the wooden walkway visual geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.5,69.9,12.7,17.2
- [crossing/naive/navigation/sev1] Deep cast shadows heavily obscure the main cliffside path, making boundaries and hazards difficult to distinguish.
- [crossing/naive/geometry/sev2] A flat, untextured white shape cuts through the ground geometry at the edge of the scene.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.5,71.2,13.8,17.9
- [crossing/naive/navigation/sev2] The platform structure is broken apart with missing planks, leaving it ambiguous whether it is walkable or a hazard.
- [crossing/naive/geometry/sev1] An untextured white polygon slice clips sharply through the terrain at the bottom right edge of the frame.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.5,69.9,12.7,17.2
- [weave/naive/geometry/sev2] The cave entrance in the background mountain is a pitch-black, featureless void with no internal geometry or depth.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 87.8,132.9,-2.7,18
- [weave/naive/navigation/sev2] Overlapping roofs, walkways, and stilts blend together in shadow and visual clutter, making walkable paths ambiguous.
- [weave/naive/immersion/sev1] The wooden floor of the upper platform displays a pixelated, repetitive green noise texture overlay.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 47.2,61.7,6.7,21.2
- [weave/naive/navigation/sev2] Uniform wood texturing and dense overlapping structures make traversable walkways visually indistinct from non-traversable rooftops.
- [weave/naive/exit/sev2] The pitch-black cave aperture lacks floor definition or lighting cues, making it unclear if it is an accessible tunnel or simple geometry background.
- [weave/naive/navigation/sev2] The chaotic layering of overlapping stilts, walkways, and roofs with identical wood textures makes visual pathfinding extremely ambiguous.
- [weave/naive/geometry/sev2] A set of wooden steps clips directly onto the sloped roof paneling without any structural supports or framing.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 54.2,65,17.8,21.6
- [weave/naive/immersion/sev2] An unrendered dark void at the level boundary breaks world coherence.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 85.8,147.8,19,36.2
- [waterfront/naive/navigation/sev2] Multiple overlapping wooden ramps and steps create an ambiguous tangle where walkable routes are difficult to discern.
- [waterfront/naive/geometry/sev1] A wooden boat is embedded directly into the concrete dam wall on the right.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 17.9,25.6,30.6,38.3
- [waterfront/naive/geometry/sev2] The upper wooden staircase clips directly into the solid rock face with no structural integration.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 26.6,44.7,19,30
- [waterfront/naive/navigation/sev2] Multiple overlapping ramps, steps, and planks over the water create visual clutter, making walkable paths ambiguous.
- [waterfront/naive/navigation/sev2] Multiple overlapping staircases and wooden ramps make it difficult to determine which paths are walkable.
- [waterfront/naive/geometry/sev2] A wooden boat is embedded horizontally into the vertical wall of the background structure without support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 43.6,48.4,22.8,27.6
- [waterfront/checklist/navigation/sev3] Cargo Winch (foot): ABSENT — No cargo winch machine is visible on any of the quay decks or platforms.
- [lockfive/naive/navigation/sev2] Multiple overlapping wooden platforms, ramps, and fragmented docks make it difficult to distinguish walkable paths from background environment debris.
- [lockfive/naive/geometry/sev2] The hull of the middle rowboat clips directly into the adjacent wooden dock platform.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 71.8,82.9,31.5,40.6
- [lockfive/naive/navigation/sev2] The tangled overlap of broken platforms, posts, and low stairs creates high visual clutter, making walkable paths hard to distinguish from collision obstacles.
- [lockfive/naive/immersion/sev1] The water body cuts off sharply into a solid black void instead of fading or meeting a background horizon.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 85.5,147.3,26.5,53.1
- [lockfive/checklist/navigation/sev3] Dam Crest Gate: ABSENT — The iron-banded gate barring the dam-crest walk is not visible anywhere in this frame. _(also on north-landing)_
- [north-landing/naive/immersion/sev1] Stylized cone vegetation models stick horizontally straight out of the vertical rock face.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 96.6,107.7,18.2,26
- [north-landing/naive/immersion/sev1] A green wooden board floats unnaturally on top of the water without any supports or visible buoyancy physics.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 97.2,106.3,31.2,36.8
- [north-landing/naive/geometry/sev1] Conical green plant models jut out horizontally from the steep cliff face with no natural attachment or root geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 98.2,102.5,19.3,23.1
- [north-landing/naive/immersion/sev1] Stylized conical foliage assets clip directly into the vertical rock face without stems, soil, or natural attachments.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 96.7,111.6,18.3,27.5

### style-bar (0)



## 2b. Aim census — did the judge point at what it named?

0 of 5 [QUALITY] verdicts REFUTED: the judge's own box held under 2% of the subject the verdict names. 0 on-subject, 0 absence-claim (census abstains), 5 unmeasurable.

- `quality:frame-edge-world` — 0/5 refuted; box coverage n/a


## 3. Budget

42 calls, 72860 prompt + 84618 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.