# Scene red-team — dellhollow — run 20260807-185607-calib

judge `gemini:gemini-3.6-flash` (pinned) · 12 plates · naive + checklist

## 1. Calibration

**On the user's own five complaints, the judge found 2/5 on the exact plate (5/5 on any plate holding the same object) and raised 54 other surviving findings.** (keyword matcher only, no hand adjudication)

- **Canopy wall across the entrance** — found (other plate)
    - naive: miss
    - checklist: [shelf-west] "the route between Valley Gate and Inn: OCCLUDED — Obscured by shadow and supporting timber beams beneath the main platform."
- **The gate stair is occluded / hard to navigate** — found (other plate)
    - naive: [deep-stairs] "The walkway dissolves into disjointed, floating wooden planks along the slope, obscuring whether this is a playable path or visual background geometry."
    - checklist: [shelf-west] "the route between Valley Gate and Inn: OCCLUDED — Obscured by shadow and supporting timber beams beneath the main platform."
- **Stray / weird cliff geometry** — FOUND
    - naive: [gate] "The background cliff face consists of flat, boxy geometric planes with visible harsh seams and unblended edges." | [gate] "The terrain mesh abruptly terminates at the top-left edge, exposing sky/void behind the cliff wall." | [crossing] "A large, untextured light grey wedge clips through the wooden ground structure in the bottom right corner." | [waterfront] "The small wooden boat frame clips directly into the grey stone wall."
    - checklist: [gate] "The world at the frame edges: WEAK — JUDGMENT: Backdrop wall geometry shows plain textures and flat cutoffs near upper edge."
- **Solid plank screens where a rope fence belongs** — found (other plate)
    - naive: [crossing] "An incomplete white geometric wedge clips into the lower right corner of the view." | [weave] "The cave interior is an unlit black void that hides whether it contains a playable tunnel or an impassable barrier."
    - checklist: miss
- **Waterfront: confusing / incomplete geometry, walking on water** — FOUND
    - naive: [crossing] "A wooden plank floats isolated in the water without any structural connection or supports to the dock." | [crossing] "A green panel floats unsupported on the surface of the water." | [crossing] "The wooden plank stairs and platform segments overlap and float disjointedly without proper support structure." | [boatyard] "Corrugated roof panels float disjointedly above the building structure without underlying framing or support." | [boatyard] "The interior floors and slabs of the lower-right building are flat untextured grey, resembling unfinished blockout geometry." | [waterfront] "The dense layer of overlapping ladders, steps, and scaffolding makes it very difficult to tell which surfaces are walkable paths versus decor." | [waterfront] "The visual tangle of overlapping stairs, ladders, and ramps makes it difficult to discern which paths are walkable vs decorative." | [waterfront] "The dense visual clutter of overlapping wooden planks, beams, and multiple staircases makes pathfinding ambiguous." | [waterfront] "A wooden platform segment floats in mid-air above the water without structural support connecting it to the path." | [fishdock] "A wooden deck segment floats unsupported directly above a small boat, clipping into it without physical structures anchoring it." | [fishdock] "A wooden platform floats in mid-air directly above a small boat without any supporting pillars or structures." | [fishdock] "A floating wooden dock platform clips directly through the hull of the small boat underneath it." | [lockfive] "A chaotic clutter of overlapping wooden frames, posts, and thin planks makes it ambiguous which surfaces are walkable paths versus non-interactive scenery." | [lockfive] "The narrow wooden stair frame floats in mid-air above the pier without proper structural support anchoring it below." | [lockfive] "Overlapping platforms, fences, and staircases blend visually into one another, making accessible walking routes ambiguous." | [lockfive] "A dense tangle of vertical posts, overlapping green platforms, and ladders obscures where player movement is allowed." | [north-landing] "Bright white, untextured rectangular blocks float on the water surface, appearing like unfinished placeholder assets." | [north-landing] "Dense overlapping wooden beams and stairs create heavy visual noise, making it difficult to distinguish walkable paths from decorative structures." | [north-landing] "A green-topped wooden plank path floats directly on the water surface without any support posts or visual connection to the structure." | [north-landing] "The dense overlap of wooden beams, stairs, and platforms along the cliff makes it hard to distinguish navigable paths from impassable scaffolding." | [north-landing] "Untextured bright white slabs sit flatly on the water surface without depth or immersion effects." | [north-landing] "Flat white rectangular shapes float on the water surface without lighting or visible support, resembling placeholder geometry." | [north-landing] "The dense clutter of wooden beams and platforms makes it hard to distinguish navigable walkways from decorative background structures."
    - checklist: [waterfront] "Cargo Winch (foot): ABSENT — No cargo winch machine is present in this scene."

## 2. Survivors by bucket

### known (16)

- [shelf-west/checklist/occlusion/sev2] the route between Valley Gate and Inn: OCCLUDED — Obscured by shadow and supporting timber beams beneath the main platform.
- [shelf-west/checklist/navigation/sev3] the way out of this area on foot towards shelf-east: ABSENT — No east shelf exit path is visible in this frame. _(also on shelf-east)_
- [shelf-east/checklist/navigation/sev3] the way out of this area on foot towards loop-stairs: ABSENT — No path extending out of frame toward loop-stairs is visible.
- [quay-west/checklist/navigation/sev3] the way out of this area on foot towards lockhead: ABSENT — No path leading out towards lockhead is visible in this frame.
- [quay-west/checklist/navigation/sev3] the way out of this area on foot towards weave: ABSENT — No path leading out towards weave is visible in this frame.
- [crossing/naive/immersion/sev1] A wooden plank floats isolated in the water without any structural connection or supports to the dock.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 99.9,106.9,30.7,37.7
- [crossing/naive/geometry/sev2] The wooden plank stairs and platform segments overlap and float disjointedly without proper support structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 69.5,87.5,24.5,36.4
- [deep-stairs/naive/immersion/sev2] The long wooden staircase descending across the cliff face lacks visible support beams or wall anchors, making it appear to float in mid-air.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 32.7,45.3,17.7,23
- [deep-stairs/naive/navigation/sev2] The walkway dissolves into disjointed, floating wooden planks along the slope, obscuring whether this is a playable path or visual background geometry.
- [deep-stairs/naive/geometry/sev2] The staircase steps descend across the cliff face without stringers or side supports, leaving the wooden treads floating in mid-air.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 32.7,47.8,17.6,30.5
- [deep-stairs/naive/immersion/sev2] The green plank walkway floats above the terrain without structural supports or anchor points beneath it.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 31.9,43.7,19.4,29.6
- [waterfront/naive/geometry/sev1] A wooden plank platform hovers in mid-air over the water gap without any visible support pillars or attachments.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 37.3,43.6,22.4,28.8
- [lockfive/naive/geometry/sev2] The narrow wooden stair frame floats in mid-air above the pier without proper structural support anchoring it below.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 66.6,77.7,27,31.9
- [north-landing/naive/immersion/sev2] A green-topped wooden plank path floats directly on the water surface without any support posts or visual connection to the structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 97.1,105.5,31,36.9
- [north-landing/naive/geometry/sev1] Untextured bright white slabs sit flatly on the water surface without depth or immersion effects.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 86.5,95.3,32.7,42
- [north-landing/checklist/occlusion/sev2] North Landing: OCCLUDED — North Landing is hidden behind the concrete lock walls and dam structures in the background.

### new (71)

- [gate/naive/geometry/sev2] The background cliff face consists of flat, boxy geometric planes with visible harsh seams and unblended edges.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 14.7,144.9,-2.1,72.6
- [gate/naive/geometry/sev1] The foreground cliff hill displays sharp, jagged, un-smoothed polygon edges along the slope.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region -2.2,10.2,-6.6,5.9
- [gate/naive/geometry/sev2] The terrain mesh abruptly terminates at the top-left edge, exposing sky/void behind the cliff wall.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 142.9,148.9,48.6,77.5
- [gate/naive/geometry/sev2] The background cliff wall ends in an exposed vertical edge and hard corner seam against the skybox void, revealing the raw boundary of the map geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 15,150.3,8.6,65.6
- [gate/naive/immersion/sev1] The tree trunk and foliage embed directly into the sheer rock wall without any visible ledge, soil, or root structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region -3.9,12.9,-6.1,4.4
- [gate/checklist/immersion/sev3] The world at the frame edges: WEAK — JUDGMENT: Backdrop wall geometry shows plain textures and flat cutoffs near upper edge. _(also on shelf-east, crossing, waterfront, north-landing)_
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 14.6,145,-2.6,72.6
- [shelf-west/naive/geometry/sev2] Wooden support beams under the upper platform stick out diagonally and terminate floating in mid-air without attaching to any wall or floor structure below.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 17.5,32.9,4.1,12.6
- [shelf-west/naive/geometry/sev2] Diagonal support struts clip straight through the roof tiles of the building below.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 19,33,4.3,12.6
- [shelf-west/naive/geometry/sev2] The angled wooden support joists under the platform jut out into open air without resting on or anchoring to any supporting structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 17.3,32.4,3.5,12.6
- [shelf-west/checklist/occlusion/sev2] the route between Item Shop (chandlery skin) and Weapon Shop: OCCLUDED — Hidden from view behind the main item shop structure.
- [shelf-west/checklist/navigation/sev2] a door / entrance you can go through ("Enter The Boatmen's Rest"): VISIBLE-BUT-ILLEGIBLE — Deeply shadowed, making it difficult to clearly distinguish as a doorway.
- [shelf-east/naive/geometry/sev1] The decorative banner string passes directly through the wooden eave of the roof.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 38.4,46.4,8.8,12.7
- [shelf-east/checklist/navigation/sev3] Weapon Shop: ABSENT — No shop weapons are visible in the scene.
- [shelf-east/checklist/navigation/sev3] Armor Shop: ABSENT — No shop armor is visible in the scene.
- [shelf-east/checklist/navigation/sev3] the route between Weapon Shop and Armor Shop: ABSENT — Specific shops are indistinguishable, making a route between them absent.
- [shelf-east/checklist/navigation/sev3] the route between Armor Shop and Shelf homes: ABSENT — The route cannot be designated without identifiable armor shop structures.
- [shelf-east/checklist/navigation/sev3] a door / entrance you can go through ("Enter Weapon Shop"): ABSENT — No weapon shop entrance is present.
- [shelf-east/checklist/navigation/sev3] a door / entrance you can go through ("Enter Armor Shop"): ABSENT — No armor shop entrance is present.
- [shelf-east/checklist/immersion/sev3] The water surface: FAILING — Water reads as a flat dark plane lacking reflections and depth. _(also on quay-west, deep-stairs)_
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region -13.9,47.5,12.3,78.6
- [quay-west/naive/geometry/sev2] A dark rectangular plane floats in mid-air across the central pathway with no supporting structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 40.2,52.1,7.9,19.8
- [quay-west/naive/navigation/sev2] The stairs drop off into pitch-black shadow without visual cues indicating if the descent is playable terrain or a deadly drop.
- [quay-west/naive/geometry/sev2] A dark rectangular plane floats in mid-air between platforms, appearing as stray geometry or an unanchored shadow box.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 40,52.5,7.7,20.3
- [quay-west/naive/geometry/sev2] Stray dark rectangular geometry floats horizontally above the dirt platform.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 40,52.5,7.7,17.2
- [quay-west/naive/navigation/sev2] Uniform ground textures and shadow contrast make elevation changes and walkable paths difficult to discern.
- [quay-west/naive/occlusion/sev1] A large foreground roof severely obscures the lower play space and potential paths beneath it.
- [crossing/naive/geometry/sev2] A large, untextured light grey wedge clips through the wooden ground structure in the bottom right corner.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.5,70,12.7,17.2
- [crossing/naive/immersion/sev1] Broken floor planks hover awkwardly without proper supporting beams connecting them to the platform frame.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 69.5,87.3,21.6,36.2
- [crossing/naive/geometry/sev2] An incomplete white geometric wedge clips into the lower right corner of the view.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 61.5,70,12.7,17.2
- [crossing/naive/immersion/sev1] A green panel floats unsupported on the surface of the water.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 99.9,106.9,30.7,37.7
- [weave/naive/navigation/sev2] The dense visual clutter of identical wooden platforms, stilts, and roofs makes walkable paths difficult to distinguish from background structures and roofs.
- [weave/naive/occlusion/sev1] The cave entrance is rendered as flat black geometry, masking depth and making it unclear whether it is an accessible tunnel or a visual backdrop.
- [weave/naive/navigation/sev2] Dense overlapping roofs, platforms, and stilts create severe visual noise that obscures which paths are walkable routes versus rooftops.
- [weave/naive/exit/sev2] The wooden stairs lead directly into a cliff wall beneath the upper building without a clear doorway, landing, or passable entry point.
- [weave/naive/occlusion/sev1] The cave interior is an unlit black void that hides whether it contains a playable tunnel or an impassable barrier.
- [weave/checklist/navigation/sev3] the route between Weave huts and Fish dock: ABSENT — No ladder connecting the weave huts down to the fish dock is visible in this frame.
- [deep-stairs/naive/geometry/sev1] The long diagonal staircase suspended mid-air lacks structural supports connecting it to the ground or cliff below.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 32.7,47.9,17.6,24.1
- [deep-stairs/checklist/navigation/sev2] Cookhouse: VISIBLE-BUT-ILLEGIBLE — While wooden buildings are visible along the upper level, none stand out visually as a cookhouse or tavern.
- [boatyard/naive/geometry/sev2] Corrugated roof panels float disjointedly above the building structure without underlying framing or support.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 0.5,9,17.7,25.2
- [boatyard/naive/geometry/sev2] The interior floors and slabs of the lower-right building are flat untextured grey, resembling unfinished blockout geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 8.2,17.7,29.8,41.9
- [boatyard/naive/geometry/sev2] A vertical wooden support beam clips straight through the hull of the large boat.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 22.6,27.2,24.7,33.9
- [boatyard/naive/geometry/sev1] A stray wooden plank clips flat through the surface of the circular platform.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 15.8,19.8,28.2,33.3
- [boatyard/checklist/navigation/sev3] Pitch kettle: ABSENT — No pitch kettle or curling tar smoke is visible anywhere near the water or boatyard.
- [boatyard/checklist/navigation/sev3] Lock Four overlook: ABSENT — No planked viewpoint structure positioned under lock gates with spray is present.
- [boatyard/checklist/navigation/sev3] the route between Boatwright's shed and Pitch kettle: ABSENT — The pitch kettle is absent, so this route cannot be identified.
- [boatyard/checklist/navigation/sev3] the route between Slipway and Lock Four overlook: ABSENT — The Lock Four overlook is absent, so this destination route does not exist.
- [waterfront/naive/navigation/sev2] The dense layer of overlapping ladders, steps, and scaffolding makes it very difficult to tell which surfaces are walkable paths versus decor.
- [waterfront/naive/immersion/sev2] A wooden plank platform hovers in mid-air without any supporting beams or pillars.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 37.3,43.7,22.3,28.7
- [waterfront/naive/geometry/sev2] A wooden boat is embedded sideways directly into the concrete wall structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 17.9,25.6,30.8,38.2
- [waterfront/naive/navigation/sev2] The visual tangle of overlapping stairs, ladders, and ramps makes it difficult to discern which paths are walkable vs decorative.
- [waterfront/naive/geometry/sev1] The small wooden boat frame clips directly into the grey stone wall.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 17.9,26.4,30.6,38.3
- [waterfront/naive/navigation/sev2] The dense visual clutter of overlapping wooden planks, beams, and multiple staircases makes pathfinding ambiguous.
- [waterfront/naive/geometry/sev2] A wooden platform segment floats in mid-air above the water without structural support connecting it to the path.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 37.4,43.7,22.3,28.7
- [waterfront/naive/occlusion/sev2] Tall vertical support poles cut through the center of the viewport, obscuring playable areas behind them.
- [waterfront/checklist/navigation/sev3] Cargo Winch (foot): ABSENT — No cargo winch machine is present in this scene.
- [fishdock/naive/immersion/sev2] A wooden deck segment floats unsupported directly above a small boat, clipping into it without physical structures anchoring it.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 44.7,52.4,25.9,34.5
- [fishdock/naive/immersion/sev2] A wooden platform floats in mid-air directly above a small boat without any supporting pillars or structures.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 44,50.6,22.4,34.1
- [fishdock/naive/geometry/sev2] A floating wooden dock platform clips directly through the hull of the small boat underneath it.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 44.4,52.4,26,35.7
- [fishdock/naive/geometry/sev1] The long diagonal wooden beam clips through the edge of the overhead building structure.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 40,47.4,16.8,26.9
- [lockfive/naive/navigation/sev2] A chaotic clutter of overlapping wooden frames, posts, and thin planks makes it ambiguous which surfaces are walkable paths versus non-interactive scenery.
- [lockfive/naive/immersion/sev1] A modern bright orange safety cone sits under the pier, breaking the rustic historical setting.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 59.1,68.5,19.8,28.8
- [lockfive/naive/immersion/sev2] The water surface terminates abruptly into a pitch-black void at the left edge, exposing an unrendered world boundary.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 85.8,147.2,27.4,52.8
- [lockfive/naive/navigation/sev2] Overlapping platforms, fences, and staircases blend visually into one another, making accessible walking routes ambiguous.
- [lockfive/naive/navigation/sev2] A dense tangle of vertical posts, overlapping green platforms, and ladders obscures where player movement is allowed.
- [lockfive/checklist/navigation/sev3] Dam Crest Gate: ABSENT — No iron-banded gate barring a dam-crest path is visible anywhere in this frame.
- [north-landing/naive/immersion/sev2] Bright white, untextured rectangular blocks float on the water surface, appearing like unfinished placeholder assets.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 86.7,95.3,32.9,42
- [north-landing/naive/navigation/sev2] Dense overlapping wooden beams and stairs create heavy visual noise, making it difficult to distinguish walkable paths from decorative structures.
- [north-landing/naive/geometry/sev1] A sharp square hole cut into the wooden floor planks around the crates lacks any edge framing or trim, looking like missing geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 103.7,110.9,24,28.8
- [north-landing/naive/navigation/sev2] The dense overlap of wooden beams, stairs, and platforms along the cliff makes it hard to distinguish navigable paths from impassable scaffolding.
- [north-landing/naive/immersion/sev2] Flat white rectangular shapes float on the water surface without lighting or visible support, resembling placeholder geometry.
      Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py -- --region 86.7,95.2,32.9,42
- [north-landing/naive/navigation/sev2] The dense clutter of wooden beams and platforms makes it hard to distinguish navigable walkways from decorative background structures.
- [north-landing/checklist/occlusion/sev2] the route between Lock Five and North Landing: OCCLUDED — The deck route leading to North Landing is occluded by the Lock Five structures.

### style-bar (0)



## 3. Budget

71 calls, 120815 prompt + 144257 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.