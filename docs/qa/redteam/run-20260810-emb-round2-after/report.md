# Scene red-team — emberbrook — run 20260810-emb-round2-after

judge `gemini:gemini-3.6-flash` (pinned) · 11 plates · naive + checklist

## 1. Calibration

_not scored in this run_


## 2. Survivors by bucket

### known (0)


### new (87)

- [woodroad/naive/geometry/sev2] The path geometry has sharp, unblended polygonal edges that visibly cut into and float above the ground texture.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 50.3,57.9,-26.2,-20.6
- [woodroad/naive/geometry/sev1] The pathway ribbon mesh has sharp, unblended polygonal edges that clip abruptly into the terrain surface.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 50.3,58.6,-27.3,-20.9
- [woodroad/naive/geometry/sev2] The circular paved area features raw low-poly edges intersecting the surrounding ground without blending.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 43.9,58.7,-34.2,-21.6
- [woodroad/checklist/navigation/sev3] a door / entrance you can go through ("Leave Emberbrook"): ABSENT — There are no doors, gates, or enterable structures visible in this forest environment.
- [waystone/naive/geometry/sev2] The path terrain mesh features sharp, unstitched geometric seams and step gaps near the light pole.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 54.2,60,-13.7,-5.4
- [waystone/naive/geometry/sev2] A sharp geometric seam and mesh misalignment splits the path terrain near the monument.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 54.5,60,-13.5,-5.6
- [waystone/naive/geometry/sev2] The path mesh has sharp, unnatural step-like seams and gaps next to the stone monument.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 54.2,60,-14.2,-6.7
- [waystone/checklist/navigation/sev3] the way out of this area on foot towards arch: ABSENT — The path fades into tree shadows before reaching the frame edge on the arch side.
- [arch/naive/geometry/sev2] Jagged, intersecting terrain polygons create unnatural sharp gaps and clipping artifacts along the walkway.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 53.8,59.9,6.3,22
- [arch/naive/geometry/sev2] Unstitched terrain mesh produces unnatural sharp triangular black shadow cuts across the pathway.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 53.6,62.3,6.6,21.8
- [arch/naive/geometry/sev2] The paved path mesh clips jaggedly into the terrain, creating broken edges and sharp geometric cuts along the ground.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 53.5,59.9,6.3,22.4
- [arch/naive/immersion/sev1] Small green spherical assets are scattered unnaturally across the lawn, clipping into the ground like misplaced placeholder geometry.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 41,50.1,11.7,21.9
- [arch/checklist/occlusion/sev2] the way out of this area on foot towards waystone: OCCLUDED — The distant road exiting towards the waystone is hidden behind the background buildings and trees.
- [arch/checklist/navigation/sev2] Item Shop: VISIBLE-BUT-ILLEGIBLE — Small illuminated stalls in the background are too distant and dark to read specifically as a general item store.
- [orchard/naive/occlusion/sev2] Heavy foreground foliage covers a large portion of the frame, completely blocking vision of the ground and potential paths on the right.
- [orchard/naive/immersion/sev2] The illuminated ground area cuts off with an unnaturally sharp, straight geometric edge rather than a smooth light falloff.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 36.8,49.3,22.7,33.3
- [orchard/naive/occlusion/sev2] Dense foreground tree branches cover a large fraction of the playable ground area, obscuring movement and sightlines.
- [orchard/naive/immersion/sev1] The light cast by the post lamp forms a harsh, perfectly straight diagonal shadow boundary on the terrain.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 25.1,42,14.2,26.2
- [orchard/naive/occlusion/sev2] Dense foreground trees obscure a large portion of the lower-right play area and screen space.
- [orchard/naive/immersion/sev2] The light pool cast on the ground has sharp, straight geometric edges that create an unnatural polygonal boundary.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 36.7,49.5,21,33.3
- [orchard/checklist/navigation/sev3] Orchard rows: ABSENT — No apple orchard rows, ladders, or apple baskets are present in this frame.
- [orchard/checklist/navigation/sev3] the route between Village Arch and Orchard rows: ABSENT — Neither the village arch nor the orchard rows are visible in this view.
- [orchard/checklist/navigation/sev3] the route between Orchard rows and Cider press barn: ABSENT — No path leading from an orchard to the barn is present.
- [orchard/checklist/navigation/sev3] the way out of this area on foot towards arch: ABSENT — There is no defined egress path leading out of the frame towards a village arch.
- [therise/naive/geometry/sev2] Sharp polygonal mesh slabs cut harshly into the terrain without edge blending, creating unnatural ground geometry.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 55,61.8,14.3,24.2
- [therise/naive/geometry/sev2] A flat grey polygon plane clips horizontally across the ground texture.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 47.8,56.2,12.8,19.7
- [therise/naive/geometry/sev2] Dark grey floor geometry slabs stick up awkwardly out of the terrain at disjointed angles with unblended, sharp edges.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 55.1,61.6,14.4,21.7
- [therise/naive/geometry/sev2] Abrupt, raw polygon edges of dark floor geometry clip unnaturally into the ground surface without terrain blending.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 48.7,56.1,12.8,18
- [therise/naive/geometry/sev2] Sharp, unblended stone slab polygons protrude awkwardly from the terrain mesh with harsh vertical edges.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 55.3,61.6,14.4,21.3
- [therise/checklist/navigation/sev2] Cider press barn: VISIBLE-BUT-ILLEGIBLE — Structure is heavily obscured by foliage and shadows.
- [therise/checklist/occlusion/sev2] Village bell: OCCLUDED — Blocked from view by surrounding tree foliage and props.
- [therise/checklist/navigation/sev2] The Heartlight: VISIBLE-BUT-ILLEGIBLE — Small light source blends into background wooden props.
- [therise/checklist/immersion/sev2] The sky: WEAK — Visible sky strip is relatively flat with minimal gradient. _(also on pondlane)_
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 62,93.7,27.6,131.3
- [square/naive/geometry/sev2] A roof structure rests directly on the terrain without supporting walls or visible foundation.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 30.4,46.9,24.4,40.9
- [square/naive/occlusion/sev2] The massive foreground roof blocks line of sight to the ground area and pathing along the lower-right side of the plaza.
- [square/naive/occlusion/sev2] A large building roof in the immediate foreground blocks visibility of the ground area along the bottom-right edge of the screen.
- [square/naive/navigation/sev1] The gaps between outer houses blend into dark, dense trees, making it difficult to distinguish accessible paths from impassable map boundaries.
- [square/checklist/navigation/sev2] poppy-stall: VISIBLE-BUT-ILLEGIBLE — Blends in with nearby market stalls and wooden props.
- [square/checklist/navigation/sev3] the route between Village Arch and Festival Square: ABSENT — Village arch and its connecting route are not visible in this view.
- [square/checklist/navigation/sev3] the route between Festival Square and Tithe barn: ABSENT — Tithe barn road is not captured in this frame.
- [square/checklist/occlusion/sev2] a door / entrance you can go through ("Enter Item Shop"): OCCLUDED — Hidden from view by the building's exterior wall angle.
- [square/checklist/navigation/sev3] the way out of this area on foot towards northlane: ABSENT — Northlane exit path is not visible in this scene orientation.
- [pondlane/naive/geometry/sev2] The terrain mesh contains missing polygons and sharp triangular holes that expose black void underneath.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 73.6,86.8,35.7,55
- [pondlane/naive/geometry/sev2] The flat green water plane clips bluntly through the ground terrain without shore geometry or blending.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 70.6,77.8,50.3,62.3
- [pondlane/naive/navigation/sev2] Dense overlapping foliage, unclear elevation drops, and visual clutter obscure walkable paths and destination routes.
- [pondlane/naive/geometry/sev2] There are open gaps and tearing in the ground terrain mesh, revealing black void underneath.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 71.9,84.9,46,51.8
- [pondlane/naive/geometry/sev2] Mesh tearing in the terrain geometry creates visible black holes in the floor.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 72.2,79.5,38,42.5
- [pondlane/naive/immersion/sev1] The window appears as a flat, untextured white emissive rectangle without frame or depth detail.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 86.2,89.4,37.5,41.6
- [pondlane/naive/navigation/sev2] Large, dense foliage completely obscures ground paths and walkable areas, making spatial navigation ambiguous.
- [pondlane/naive/geometry/sev2] There is a sharp black triangular hole in the ground terrain mesh where polygon edges fail to meet.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 71.3,85.1,46,51.8
- [pondlane/naive/geometry/sev2] Multiple black triangular tears and missing polygons are visible in the ground mesh near the right edge.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 70.3,79.6,37.9,43.8
- [pondlane/naive/immersion/sev2] The overhead banner string breaks into disconnected floating segments rather than forming a continuous line.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 71.2,82.1,45.5,50.6
- [pondlane/checklist/navigation/sev3] Pond jetty: ABSENT — No dock or jetty structure extending into the water is visible.
- [pondlane/checklist/navigation/sev3] Brook mouth: ABSENT — The point where the brook joins the main river is not visible.
- [pondlane/checklist/navigation/sev3] Weir & sluice: ABSENT — No weir mechanism or sluice gate can be seen.
- [pondlane/checklist/navigation/sev3] Finn's smokehouse: ABSENT — No small smokehouse structure is present near the shore.
- [pondlane/checklist/occlusion/sev2] Pip's den: OCCLUDED — Hidden beneath foliage and the steep bank near the footbridge.
- [pondlane/checklist/immersion/sev2] The world at the frame edges: WEAK — WEAK: Background trees end abruptly against the sky, creating stark borders.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 67.9,88.5,39.4,58.1
- [pondlane/checklist/immersion/sev2] The water surface: WEAK — WEAK: Reads as a flat green fill with sharp, unblended contact along the shore.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 70.6,77.7,50.3,62.2
- [homerow/naive/occlusion/sev2] The large pine tree in the foreground heavily occludes the path and building in the lower-left area, obscuring player vision.
- [homerow/naive/geometry/sev2] The elevated box structure juts out from the roof on thin, floating beams with unsupported vertical posts.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 40.7,50.7,57.6,71
- [homerow/naive/geometry/sev2] A massive wooden cylinder/disc is clipped directly into the stone foundation wall and terrain.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 50.5,56.6,55.3,61.2
- [homerow/naive/occlusion/sev2] The large evergreen tree in the foreground completely blocks the view of the house and walkway on the lower-left, hiding potential gameplay space.
- [homerow/naive/immersion/sev1] An overexposed or untextured white mesh sits in the vegetation behind the upper house, standing out unnaturally from the lighting.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 37.8,45.9,56,70.1
- [homerow/checklist/navigation/sev2] Brook spring: VISIBLE-BUT-ILLEGIBLE — A tiny glistening patch of water is visible in deep shadow behind the cottage, but it is too small and dark to clearly read as a spring.
- [homerow/checklist/navigation/sev3] Upper lane (closed): ABSENT — No closed lane or festival cart is visible past Lake's home.
- [homerow/checklist/navigation/sev3] Spring house: ABSENT — No stone hut structure over the spring is present in this frame.
- [northlane/naive/occlusion/sev2] Dense tree canopy heavily covers the left side of the building and ground path, obscuring ground layout and visual clarity.
- [northlane/naive/exit/sev2] The steep overhead camera angle and roof overhang completely hide all entrances and doors, making it unclear how to access the structure.
- [northlane/naive/occlusion/sev2] Dense foliage completely blocks sight of the ground and paths surrounding the house, hiding player movement and potential hazards.
- [northlane/naive/geometry/sev1] A rectangular hip roof sits awkwardly on top of a round tower wall base, causing mismatched geometry overhangs.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 64.7,73.7,64,72.3
- [northlane/naive/occlusion/sev2] Dense tree foliage completely covers the ground and building perimeter on the left and top, hiding potential paths and entrances from view.
- [northlane/checklist/navigation/sev3] Back lane (closed): ABSENT — No closed lane with stacked barrels exists in this frame.
- [northlane/checklist/navigation/sev3] the route between Festival Square and Tithe barn: ABSENT — No north lane bordered by walls is visible anywhere in this shot.
- [gateroad/naive/occlusion/sev2] Extremely dark foliage and heavy shadows obscure the right half of the frame, hiding any ground features or potential paths.
- [gateroad/naive/navigation/sev2] Deep darkness in the foreground obscures the path boundaries, making it difficult to discern walkable terrain.
- [gateroad/naive/occlusion/sev2] Extreme darkness and dense tree foliage completely obscure the right side of the frame, hiding terrain and potential paths.
- [gateroad/naive/geometry/sev1] The cleared dirt area has a sharp, unnaturally hard edge with the surrounding grass texture without proper blending.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 62.5,80.2,80.2,102.5
- [gateroad/naive/occlusion/sev2] Extremely dense and pitch-black foliage obscures over half the frame, hiding layout and potential pathways.
- [gateroad/naive/navigation/sev2] Deep shadows across the foreground obscure where the walkable path leads.
- [gatefield/naive/geometry/sev2] The paved floor mesh around the stone structure has square cutouts revealing empty black space beneath the terrain.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 73.1,82,119.9,128.3
- [gatefield/naive/navigation/sev2] Deep shadow and severe underexposure conceal the terrain and boundaries, making navigation difficult across the left half of the scene.
- [gatefield/naive/geometry/sev2] The terrain ground mesh cuts off abruptly around the stone pillars and platform, leaving empty black voids underneath.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 73.2,82,119.9,126.6
- [gatefield/naive/navigation/sev2] Extremely dark shadows obscure the environment and path, making navigable terrain nearly impossible to distinguish from obstacles.
- [gatefield/naive/geometry/sev2] The paved ground mesh cuts off abruptly next to the pillar base, leaving a hole into empty space underneath.
      Blender -b tools/blends/emberbrook-master.blend -P tools/geometry_audit.py -- --region 77.8,82.3,120.7,126.5
- [gatefield/naive/navigation/sev2] The dense foliage and trees are heavily underexposed in shadow, obscuring terrain bounds and path edges.
- [gatefield/checklist/occlusion/sev2] Downstream (vista beyond the Gate): OCCLUDED — Blocked from view by the closed wooden gate doors and wall.

### style-bar (0)



## 2b. Aim census — did the judge point at what it named?

2 of 9 [QUALITY] verdicts REFUTED: the judge's own box held under 2% of the subject the verdict names. 3 on-subject, 0 absence-claim (census abstains), 4 unmeasurable.

- `quality:sky` — 0/2 refuted; box coverage 83.3%, 48.8%
- `quality:frame-edge-world` — 0/4 refuted; box coverage n/a
- `quality:water-read` — 2/3 refuted; box coverage 0.0%, 31.6%, 0.0%


## 3. Budget

66 calls, 114748 prompt + 117580 reply tokens, 0 errors.

## 4. Limits

`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool reads pixels only; the loop-stairs class of defect is invisible to it by construction. See index.html §5 for where each of those defects IS caught.