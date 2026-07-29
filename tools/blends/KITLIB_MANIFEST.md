# Dellhollow Kit Library — `kitlib.blend`

Shared asset library for the pre-rendered background pipeline.
**Object names are the contract** — other agents APPEND/LINK by name.

Scale contract: character = **1.7u**. Doors 2.1u, railings 1.0u, stair rise 0.22u,
wall panels 3x3u. Everything is modelled at final world scale (no object scaling),
because materials use **object-space box projection** — scaling an object would
change its texel density.

Rebuild from scratch with:
```
exec(open("tools/kit_materials.py").read())   # then make_all()
exec(open("tools/kit_build.py").read())       # then build_all()
```

## Collections

### KIT_WALLS
| Object | Size | Notes |
|---|---|---|
| `kit_wall_plain` | 3.0 x 3.0 | Timber-framed panel: sill, head, corner posts, mid rail, diagonal brace. Vertical cladding boards with per-board random rotation. |
| `kit_wall_window` | 3.0 x 3.0 | 4-pane window (1.1 x 1.2) at z=1.55, casing + mullions + protruding sill + dark glass. |
| `kit_wall_door` | 3.0 x 3.0 | Planked door leaf 1.0 x 2.1 with cross-battens and diagonal brace, jambs, lintel, iron handle. Leaf hung slightly off-square. |

### KIT_STRUCT
| Object | Size | Notes |
|---|---|---|
| `kit_stilt_trestle` | 1.5 x 1.5 x 4.2 | Battered legs, 2 rings of horizontals, X-bracing on all 4 faces at 3 levels. |
| `kit_stair_flight` | 2.4 run x 1.76 rise | 8 treads, rise 0.22 / run 0.30, stringers both sides. |
| `kit_roof_panel` | 3.0 x 2.2 | 9 overlapping shingle courses + sheathing + rafter tails. Heaviest moss setting. |
| `kit_plank_deck_2x2` | 2 x 2 | Top surface at z=0, 3 joists below. Planks jittered. |
| `kit_railing_1m` | 1.0 span x 1.0 tall | Origin at left post, runs +X. Top + mid rail. |
| `kit_railing_post` | 1.04 tall | Single post with cap. |
| `kit_beam` | 3.0 x 0.22 x 0.22 | Centred at origin, runs X. |

### KIT_PROPS
| Object | Notes |
|---|---|
| `kit_barrel` | 0.9 tall, bellied staves + 3 iron bands. |
| `kit_crate` | 0.75 cube, slatted sides + corner battens. |
| `kit_lantern_hanging` | Iron cage + **emissive glass** + child `kit_lantern_light` (POINT, 55W, warm 1.0/0.60/0.28). Appending the lantern brings the light with it. |
| `kit_rope_coil` | 5 stacked coils, procedural twisted-fibre material. |
| `kit_bucket` | Tapered staves, iron band, swing handle. |
| `REF_human_1p7` | **1.70u scale reference.** Keep one in frame while composing. |

### LIGHT_SUNSET
| Object | Notes |
|---|---|
| `SUN_key` | SUN, 4.2W, colour 1.0/0.68/0.40, angle 2.5deg, elevation ~11deg — long raking shadows. |
| `FILL_bounce` | AREA 9x9, 90W, cool teal — fakes bounce off the river so shadows aren't black. |
| `RIM_gorge` | AREA 6x6, 130W, warm — separates silhouettes from the misty background. |
| `FOG_BOX` | 160 x 160 x 60 box with `mat_fog` (Volume Scatter, density 0.004). Provides aerial perspective. |

Full recipe is stored in the text datablock **`LIGHTING_NOTES`** inside the blend.

> **Do not put volume scatter on the World.** A world volume is infinite in
> extent, so sun and sky light — which arrive from infinite distance — are fully
> extinguished: the sky renders black and the sun stops lighting the scene.
> Use the bounded `FOG_BOX` instead. (Cost us a debugging cycle; measured scene
> mean brightness 0.0009 with world volume vs 0.48 without.)

## Materials

All textured materials are Diffuse(xAO) -> Base Color, Rough -> Roughness,
nor_gl -> Normal Map, with **object-space BOX projection** (no UV unwrapping
needed) and a procedural **moss/grime layer** driven by world-up normal x noise,
so moss accumulates on upward faces the way it does in the reference art.

| Material | PolyHaven asset (1k) | Moss | Notes |
|---|---|---|---|
| `mat_deck` | `weathered_planks` | 0.55 | Decking, darkened 0.62 |
| `mat_timber` | `raw_plank_wall` | 0.42 | Framing; darkened 0.42 + brown tint |
| `mat_wallwood` | `green_rough_planks` | 0.35 | Peeling green paint — the reference shed colour |
| `mat_wallwood_dark` | `dark_wooden_planks` | 0.28 | Red-tinted; doors, barrels, crates |
| `mat_plaster` | `clay_plaster` | 0.30 | |
| `mat_rock` | `rock_face_03` | 0.45 | Cliff walls |
| `mat_shingle` | `red_slate_roof_tiles_01` | 0.75 | Asset is itself tagged "moss / mosscovered" |
| `mat_mosswood` | `moss_wood` | 0.25 | Waterline / wet timber |
| `mat_metal` | `worn_corrugated_iron` | 0.20 | Accent roofing |
| `mat_ground` | `forest_ground_04` | 0.30 | Terrain |

Procedural (no textures — these correctly show as "no image" in `verify()`):
`mat_rope` (twisted-fibre wave + bump), `mat_water` (deep teal, layered noise
normals), `mat_tar` (pitch kettle), `mat_lantern_glass` (emission 28),
`mat_iron`, `mat_glass_dark`, `mat_fog`.

Textures live in `tools/textures/` with `_manifest.json` recording asset id and
map paths. Re-download with `tools/`-local script logic in `kit_materials.py`.

---

## Probe findings (lessons the next scene should inherit)

Built `tools/blends/probe.blend` (Boatyard slipway) from this kit over 9
iterations. Things that cost a cycle and are worth not rediscovering:

1. **Volume scatter on the World kills everything.** Infinite extent extinguishes
   sun and sky. Use the bounded `FOG_BOX`. (mean 0.0009 -> 0.48)
2. **The fog box must actually CONTAIN the far geometry.** Distant ridges sitting
   outside the box rendered crisp and bright and read as cardboard cutouts.
   Scale `FOG_BOX` to enclose the furthest thing in frame.
3. **Zero-user datablocks are dropped on save.** Materials no kit object uses
   (`mat_water`, `mat_rock`, `mat_tar`...) vanished from kitlib until they were
   given `use_fake_user`. Appenders must also pull `dst.materials` explicitly.
4. **`bpy.ops.wm.append` needs UI context** and fails headless. Use
   `bpy.data.libraries.load`.
5. **Back-lighting flattens the frame.** Keying from up-gorge put every
   camera-facing plane in shadow. A 3/4 key from over the camera's left shoulder
   at ~21 deg elevation is what models the forms and gives raking shadows.
6. **Physically-correct water reads muddy brown.** A low camera sees water at
   grazing angles where Fresnel makes it a mirror of the warm sky. Mix a fixed
   teal diffuse body under the gloss instead of letting Fresnel win.
7. **Displacing a cliff only in/out leaves a dead-straight skyline.** Modulate
   the crest height along the wall (`ragged=`) or it reads as wallpaper.
8. **Watch texture tiling on large surfaces.** `mat_rock` at scale 0.35 tiled ~30x
   across a 60u cliff. Distant rock gets its own `mat_rock_far` at scale 0.05.
9. Empty water/deck expanses read as dead space -- pilings and working clutter
   are cheap and do a lot.

---

## Dusk pass findings (probe v10/v11, `tools/probe_dusk.py`)

The v9 probe was critiqued as "bright afternoon, zero vegetation, brown
monopoly". Fixing that cost these, which are cheaper to read than to rediscover:

10. **A world colour ramp's first stop paints the ENTIRE lower hemisphere.**
    `Generated` Z for a world runs -1..1 but ColorRamp clamps Fac at 0, so a
    stop at position 0 is every downward direction. v9/v10a had a bright ember
    there: a vast warm ambient dome that no amount of lowering the sun could
    make read as evening. Put the ember in a thin band at the elevation the
    camera actually sees (here Z ~ 0.05-0.15), keep everything below it dark,
    and let a deep blue zenith be the ambient -- that is what cools shadows.
11. **A key that travels along the view axis hides its own shadows.** Lowering
    the sun to 10 deg gave 17-26u shadows that all fell behind their casters.
    Long raking shadows in the FOREGROUND come from casters standing behind and
    to the side of the camera, outside the frame entirely.
12. **Ray-map the frame before trusting any volume.** The pitch kettle's smoke
    box (3 x 3 x 4.8) was harmless off-frame at v9 and covered six of ten frame
    rows once the kettle moved into shot, quietly hazing the whole centre. Cast
    a grid of `scene.ray_cast` rays through the camera frame and print what each
    cell hits; it finds this in seconds.
13. **Shingle courses need sheathing in the SAME material.** Courses laid at
    0.62 of their step leave gaps that show the board underneath, and course
    EDGES are vertical so they carry no moss -- every "mossy" roof read as pale
    louvres. Overlap the courses and sheathe in the shingle material.
14. **A light inside enclosed geometry lights nothing.** The kettle fire sat in
    a near-solid ring of hearth stones capped by the pot; it illuminated the
    underside of its own kettle. Put practicals at the mouth/gap, not the
    physical source point.
15. **Distant vegetation must be mass.** A trunk with sparse leaf cards reads as
    a DEAD tree at 100u. Far rims get canopy clumps only; trunks start to be
    worth modelling around 40u.
16. **Place by projection, not by eyeball.** `bpy_extras.object_utils.
    world_to_camera_view` for screen-space bounds plus a `ray_cast` occlusion
    test (`probe_dusk.report()`) answers "is it in frame and can I see it" for
    free. Every placement in the dusk pass was set that way; the render was only
    ever used to judge whether it looked good, never where things landed.
17. Leaf cards need real **UVs**. Object/Generated coords cannot give per-card
    local space inside one mesh, and the foliage shader cuts the rectangle to a
    leafy blob with a radial mask measured from the card centre.

---

## Interior pass findings (cottage-int v10/v11, `tools/cottage_build.py`)

The v9 cottage interior was critiqued as "two black bars across the frame,
murk in the upper half, an empty stage in the middle, papery plaster". Fixing
that cost these:

18. **Decide beam placement by projection, not by taste.** A tie beam spans the
    full width, so the only question is which screen ROWS it lands on.
    `world_to_camera_view` on eight bbox corners gives that in one pass: the
    v9 ties landed on rows 196-306 and 129-206 while the dresser occupied
    165-303, i.e. both crossed the hero of the back wall. Sweeping candidate
    (height, section) pairs through the same projection showed that no tie
    forward of the back wall clears the dresser at ANY height -- so the camera
    keeps one. Ten seconds of arithmetic replaced several render cycles.
19. **`ray_cast` occlusion QA must skip the cutaway.** `visible_camera=False`
    only hides an object from camera rays; `scene.ray_cast` still hits it. Set
    `hide_viewport` on every camera-invisible mesh **and on the fog box** first,
    or the answer is always "blocked by shadow_nearwall" / "blocked by
    FOG_BOX_INT" and tells you nothing.
20. **A hearth fire has to sit FORWARD in the firebox.** A camera looking into
    a wall opening from a 3/4 angle sees past the near cheek only for a narrow
    band of depth. The v9/v10 fire bed sat at x~0.15 in a 0.62-deep box and
    `hearth_pier0_01` ate the ember bed and the roots of every flame outright:
    all that reached the lens was mid-flame, so the fire read as floating paper
    triangles with no glowing base. Moving it to x~0.35 fixed it. (Same family
    as finding 14: model the fire where it can be SEEN, not where it would be.)
21. **Stacked emissive cones add.** Stylised flames are ~25 Transparent+Emission
    cones two ranks deep, so 3-5 of them lie along any one view ray and their
    emission sums. Any per-flame strength above ~1 blows the stack to white
    through AgX and the fire renders as flat paper. Tune the strength for the
    MASS (landed at 0.8), not for one cone.
22. **A pale scatter colour desaturates everything behind it.** `mat_fog` with
    Color (1.0, 0.86, 0.70) at the v9 light levels was invisible; at v10 levels
    it laid a milky veil over the whole hearth end and crushed the contrast
    there. Volume scatter colour has to be tuned WITH the lighting, and wants
    to be saturated in the direction of the light it is scattering
    (1.0, 0.62, 0.34 here) rather than near-white. Density 0.0075 -> 0.0030.
23. **Move soot gradients when you move the timbers.** `mat_int_beam`'s world-Z
    soot ramp started at z=2.0; raising the ties to 2.82 and the joists to 3.46
    pushed them deep into it and they came back black no matter how much
    uplight they got.
24. **Traffic wear belongs in the material, keyed on world position; replaced
    boards belong in the geometry.** A per-object wear flag makes the lane
    switch on and off at every plank joint. An ellipse-set mask on
    `Geometry->Position` (see `int_mat(lane=)`) runs the lane continuously
    across the whole floor. Conversely a *replaced* board is genuinely one
    object, so that one is a material swap at build time.
25. **A small prop must be HORIZONTAL to read in a side-lit room.** A toy boat's
    sail -- a flat upright plane -- rendered as a white stick when it went
    edge-on and as a small dark rectangle when it did not. A rag doll lying on
    her back reads instantly: the firelight rakes across her, and
    head-body-limbs is unmistakable at 25px. Same for the sleeping cat.
26. **`lath_mix > 0.25` turns a plaster wall into corduroy.** Faking laths
    under limewash with a banded Wave texture works, but the wave has to stay a
    small minority of the bump height (0.17 @ scale 33) or the panel reads as
    ribbed cardboard.

---

## Cookhouse pass findings (cookhouse-int v1-v8, `tools/cookhouse_int_build.py`)

The cookhouse is the first room in the set with WORKING volumes in it (steam
over the pots) and two fire apertures at different heights. What that cost:

27. **A steam/smoke volume's density is a TEXTURE, not a number.** A flat
    density high enough to see is high enough to print the box's own faces as
    a hard-edged milky rectangle across the frame (finding 12, again). Low
    enough to hide the faces is low enough that there is no steam. There is no
    good flat value. Drive Density from a radial falloff on **`Generated`**
    coordinates -- which map any box to 0..1 whatever its size -- so the
    volume reaches zero before it reaches a face, then multiply by a noise
    ramp to break the ellipsoid into a ragged plume. The box may then be
    generous; the falloff decides where the steam ends.
28. **Two masonry masses meeting in one corner merge into one lump** unless
    they differ in BOTH colour and course size. The cookhouse hearth is big
    grey river rubble and the range beside it is small red brick, and even
    then the brick had to come down two stops: shipped at `darken=1.00` it
    read salmon pink and was BRIGHTER than the fire it contains, so the value
    leader was the masonry rather than the flame.
29. **Anything you put between the camera and a fire will be found by the
    ray-cast probe, including the props that belong there.** A spit is
    correctly in front of a cooking fire, and at a plausible z=0.46 it sat
    exactly on the sightline into the firebox: the probe hit roasting meat
    instead of the ember bed from all three angles. Raised to 0.68 the
    sightline passes under it and the meat silhouettes against the flames,
    which is the better picture anyway. Extend the finding-20 probe to a
    small GRID of points across the bed, not one centre point -- the near
    end, the middle and the far end fail independently.
30. **Interaction pads must be excluded from the ray map as well as the
    beauty render.** `hide_render=True` does nothing to `scene.ray_cast`, so
    `walk_pad_counter` reported as the thing the camera sees over an eighth
    of the frame. Same family as finding 19.

---

## District pass findings (del-boatyard, `tools/boatyard_*.py`)

First fully-detailed exterior built AROUND a verified walk graph, at true town
coordinates. Things that cost a cycle:

31. **`bpy.data.libraries.load` rewrites the list you hand it, in place.**
    `dst.objects = names` turns `names` into a list of Objects once the `with`
    block exits, so any later `zip(names, dst.objects)` silently keys a dict by
    Object. Pass `list(names)`.
32. **`ob.matrix_world` and `ob.bound_box` are depsgraph-evaluated.** In a
    headless build there is no evaluation, so freshly appended or freshly moved
    objects report identity matrices and stale bounds. Every placement helper
    must read `matrix_basis` and compute bounds from `data.vertices`.
33. **Bake donor transforms by copying the object, not by making a new one.**
    `bpy.data.objects.new(name, mesh)` drops the BEVEL modifier every probe
    asset relies on, and probe hulls carry an 11 deg X rotation (they sit on a
    slip) that is lost if you transform only the mesh.
34. **The town cliff makes a screen-left key impossible.** Mapping the probe
    rig through the probe->town rotation puts the sun over the camera's left
    shoulder, which at the boatyard is a 28 u wall 6 u away: clearing it needs
    77 deg of elevation. Mirror the key to the river side and replace the light
    the cliff would really bounce with a warm area light — the frame keeps the
    same 3/4 modelling and the same 22 deg raking shadows.
35. **A walk landmark pad is a filled disc, not a ring.** `walk_lm_slipway` is
    a 32-gon 8 u across, so its whole interior is corridor. Anything that wants
    to straddle a landmark (hull frames over `drydock-frames`) has to go up on
    stocks above walk_top + 2 and let the player pass underneath.
36. **Walk meshes overlap at different heights.** `walk_pad_pitch-kettle` sits
    0.6 u UNDER `walk_lm_slipway`; ribbon ends are buried the same way. The
    surface the player stands on is the HIGHEST walk face at that point, so
    both the deck generator and the ray-cast QA must be written against that
    effective top, not against each face's own z.
37. **Test long deck strips along their whole length.** Planks and joists are
    metres long; a centroid-only burial test kept strips whose far end lay over
    a lower walkway, which is exactly the "first hit is not a walk mesh" failure
    the QA is looking for. Probe the centroid, every corner and every midpoint.
38. **Build the terrain FROM the walk graph.** Ribbons floating over a void read
    as scaffolding; a hard whose height is `min(base, walk_top - 0.42 + d*1.15)`
    over the distance `d` to each walk face terraces itself around every path
    and kills nearly all the exposed piles.
39. **Add the terrain noise before the walk clamp, not after.** Noise applied
    afterwards lifts the ground back through the deck it was just clamped under.
40. **`mat_spray` is a VOLUME.** A thin box of it is invisible, so a weir's
    falling water disappears. White water needs a surface shader; and a
    full-height sheet of it over the whole crest erases the black stone the
    river spec asks for — spill only through the gate bays.

---

## Polish-pass findings (inn v12, weapon v4, armor v4, cookhouse v9)

Four ACCEPTED-WITH-NOTES rooms taken through a small-diff polish pass. Notes
of the form "X reads weak" cost the most, because the obvious response to them
is wrong nearly every time:

41. **"The glow reads weak" usually means its SURROUND is clipped, not that
    the source is dim.** The weapon shop's forge was noted as having a weak
    ember glow. Measuring the strip of coal bed the camera can actually see
    (it clears the counter's back edge by a few centimetres) returned 93%
    of it pinned at white: there was no weak glow, there was a hole. Adding
    light made it worse twice before the measurement was taken. Crop the ROI,
    print `frac > 0.95` and the mean RGB, and only then decide whether the
    note means "more" or "less".
42. **A fire's masonry has to be dark enough for the fire to out-value it**
    (finding 28, generalised past brick). A mid-grey albedo half a metre from
    a practical has nowhere to go but the AgX shoulder. Give every surface
    that touches a fire its own sooted variant, and drop the wattage with the
    albedo — the forge went 430 W on hearth stone to 170 W on firebrick, and
    only then did the coals become the brightest thing in their own bowl.
43. **Where a practical sits matters more than how hard it is driven.** A
    POINT at 0.17 m delivers ~1200 W/m²; the same lamp at 0.6 m delivers 90.
    Both forge lamps were inside the fire they were supposed to light the room
    with. Move the lamp to the mouth and it lights the room instead of the fuel
    (this is finding 14 stated as a budget rather than as a rule).
44. **An AREA lamp features nothing.** Asked to give the armour shop's hero
    harness a spotlight moment, a 110 W area over it lifted the entire
    front-left bay 2.3× — shields, peg rail and barrel came up with the
    harness, so the harness ended up no more featured than before, only
    brighter. A SPOT falls off inside the bay, which is the entire point of a
    featured prop. Note the scale change: a 52° cone concentrates ~20× versus
    a POINT, so a two-figure wattage replaces a three-figure one.
45. **Polished steel has no highlight of its own.** It is a mirror; it can only
    show you a light that is already in the room. Rim separation on armour
    comes from putting a small hot source high and BEHIND the piece, opposite
    the camera — not from raising the key.
46. **Adding to a scene built off one shared RNG stream: draw from a PRIVATE
    `random.Random`.** Every one of these rooms consumes a single `R` in build
    order, so inserting three flames into the hearth silently re-deals every
    prop built after it and the "nothing else changed" check fails everywhere
    at once. Appending with a private stream (and never reordering existing
    draws — changing a *threshold* is safe, changing the number of `.random()`
    calls is not) keeps the frame diff at denoiser noise outside the ROI.
47. **Grow a fire's mass at the ENDS of its opening, not in the middle.**
    Finding 21 says stacked emissive cones add; more cones in the centre only
    deepens the stack on the view rays that were already clipping. Spending
    the extra mass beyond the old spread widens the silhouette for free.
48. **Uplight aimed straight up misses the face the camera sees.** A room-wide
    `BEAM_up` under the ceiling reaches the beams' soffits but arrives nearly
    parallel to their camera-facing cheeks — which is why the inn's front
    stubs were still black bars after it was installed. Put a small lamp
    FORWARD of the beam and tilt its normal back toward the wall so the light
    rakes the cheek as well as the soffit.
49. **Check a wall fixture's screen ROW before modelling it.** The cookhouse's
    crock shelf at its natural height projected to row 281 — the exact row the
    front beam lands on across that whole side of the frame. `ray_cast` from
    the camera reported "blocked by beams" in a second; z = 2.05 clears it.
    (Finding 18, applied to props rather than to the beams themselves.)

---

## In-master district findings (Boatyard seam weld, `tools/master_weld.py`)

The first pass that edited `tools/blends/dellhollow-master.blend` IN PLACE, welding
the composited Boatyard into the town.  What it cost, for the agent that details
the Waterfront next:

50. **A composite loses collection-level visibility flags.** `boatyard.blend` parks
    its harvested probe donors in a `PROBE_SRC` collection with
    `hide_render`/`hide_viewport` set **on the collection**; the composite re-linked
    every object into one flat `DIST_boatyard`, so 54 donors — a second copy of the
    shed, the hulls, the kit prototypes, both fog boxes and a duplicate of every rig
    light — came back VISIBLE, most of them standing at probe coordinates in the
    middle of the town.  Hidden state that matters must live on the OBJECT.
51. **Inside a detailed district, walk_/bar_ meshes must be `hide_render=True` and
    `hide_viewport=False`.** The blockout ribbons are the town's visible paths
    everywhere else, but under district decking they show through as gray slabs.
    Render-hiding is not an edit (QA still proves the vertices are bit-identical);
    `hide_viewport` IS destructive, because the glTF exporter drops those objects
    and the runtime loses its collision.
52. **Every non-diegetic object is `fx_*`.** Fog boxes, haze slabs, hazed backdrop
    ridges, silhouettes, smoke/spray volumes: the runtime exporter strips
    `^(fx_|FOG|.*haze|ridge_upstream|far_town|v10_)` — anything that misses the net
    ships as a giant opaque box through the middle of the player's river.
53. **A district's key light re-values the whole town.** Swapping the blockout's flat
    3.2 W sun for the district's 5 W sunset key put every 0.5-albedo placeholder
    surface on the AgX shoulder: the gray town rendered pale salmon next to a
    district whose textures are darkened 0.42..0.62 with moss over them.  The value
    gap, not the geometry, is what reads as "two datasets".  The blockout palette
    (`m_wood`, `m_stair`, `m_gray`, `m_port`, `m_rock`) was multiplied 0.40..0.52.
54. **Blockout context slabs lie over district walkways.** `water_pool-upstream` ran
    to y=26 and floated on top of the lock-four paths — the district had quietly
    re-cut its own water to y=30.35 and that fix did not survive the composite.
    Down-ray QA finds this instantly; eyeballing does not.
55. **Weld a border by carrying the GROUND under the neighbour, not by decorating
    the join.** East of the Boatyard the blockout is ribbons and stairs floating over
    void.  Re-using the district's own `gh_base` height function with the toe
    walking north and the shoreline walking south (`seam_h` in `master_weld.py`),
    clamped to `walk_top - 0.42 + d*1.15`, produces a bank the blockout stairs land
    on — that single mesh does more for the seam than every prop on it.
56. **Two gates, both cheap, run them every pass:**
    `tools/master_walk_qa.py` (topology bit-identical vs `dellhollow-town.blend`,
    100% down-ray coverage, GLB-safety) and `tools/geometry_audit.py --region ...`
    (interpenetration + strays, exits non-zero).  The audit's inside-fraction test
    is what separates a beam resting ON a deck from a beam driven THROUGH it;
    vegetation and fire are exempt because interpenetration is how they are drawn.
57. **Foreground framing props do not survive a walkable town.** The Boatyard's
    `foreground_timber` spars were composed for one hero camera; from the other
    seven directions the player can stand in they read as beams stabbing through the
    yard.  Compose set dressing for the round, not for the shot.

## River-widening findings (3x gorge in the master, `tools/master_river_widen.py`)

The map's river spec went 16 -> 48 wide with the NEAR bank pinned; every built
thing in the town sits on that bank, so the whole change lands on the far side.
What that cost:

58. **A "3x wider river" is a 3x wider *scene*, and the light rig does not know
    it.** `SKY_wash` was a 46 x 34 area lamp centred on the old river; two thirds
    of the widened Lock Four dam fell outside it and rendered as a black mass
    that looked like a modelling failure. Widen the fill WITH the gorge and scale
    its wattage by the same factor so the accepted district keeps its irradiance
    (finding 53 again, from the other direction). The remaining shortfall is
    real: `KEY_slip` still only reaches y~42, so the dam north of that has no key.
59. **`mat_rock_far` is tuned for 130 m, not 58 m.** Dropping the far wall to the
    ridge material put it at the same value as the black-stone dam in front of it
    and erased the dam's silhouette; leaving it on the blockout `m_rock` put it at
    the same value as the sunlit water and erased the bank. A widened gorge needs
    its own mid-distance rock (`mat_rock_farwall`: crush 0.30, haze 0.60).
60. **Moving the waterline leaves a hole, not a bank.** Stretching the pool planes
    to the new far edge left 10 m between water and cliff face that rendered as
    world background from any camera looking down the gorge. The fix is a toe mesh
    whose LIP IS CUT TO THE LOCAL POOL LEVEL — one shoreline height per pool —
    otherwise the upstream pool floats 3.4 m over its own shore.
61. **Extend detailed art by DUPLICATING its own components, never by re-modelling
    them.** `lock_four_dam` is one joined mesh, but `join_meshes` leaves every
    original box as a separate connected component, so the dam decomposes back
    into its parts by flood-fill. Classify the components by their (x0,x1,z0,z1)
    signature — that separates the repeating units (piers 1.55, gallery piers 1.42,
    gallery posts 0.72, crest posts 2.90) from the bay art, and the bay is then
    exactly the 17 components inside one gate window. Spanning elements stretch,
    repeats carry on at their own pitch, bays clone. The join is invisible because
    nothing was re-derived.
62. **Foreground framing props, again (finding 57).** The two `foreground_timber`
    spars were not merely unsupported: their HEADS WERE INSIDE the boatwright shed
    (they stood on the yard and drove through its east wall), and the geometry
    audit missed them because they are 16 verts of a 120-vert joined mesh, well
    under the 0.08 inside-fraction. A per-component test against the neighbour's
    bounds catches what a per-object test cannot.
63. **Interior blends reference textures by RELATIVE path** (`//../../textures/
    brown_planks_*.jpg` → `tools/textures/`). Copying a .blend anywhere else
    silently breaks every image texture and Cycles renders the material's
    missing-texture MAGENTA — the whole room turns bubblegum pink. Snapshot
    copies must either live in the same directory, run `bpy.ops.file.
    make_paths_absolute()` before use, or (best) just open the original with
    `-b` and never save: `blender -b file.blend -P script.py` is read-only
    unless the script calls save, so bake/render scripts need no copy at all.
64. **Cycles shader-space "camera" transform has +Z pointing INTO the scene** —
    opposite of Blender's object-space camera convention (camera looks down
    its local -Z). A Vector Transform (World→Camera) followed by multiply -1
    yields negative emission strengths that clamp to zero: the whole depth
    pass renders black. Use Math ABSOLUTE on the Z component instead; correct
    in both conventions. (Found building tools/depth_bake.py, which bakes
    background + per-pixel depth map + collision GLB from one session so the
    runtime's exact-pixel occlusion cannot disagree with the backdrop image.)
## Waterfront findings (in-master district #2, `tools/waterfront_*.py`)

The Waterfront is the first district built on a stretch that had NO GROUND AT
ALL — east of the Boatyard's seam the town is walk ribbons over void — and the
first to have to re-light a gorge three times wider than the rig that lit it.
What that cost, for the agent that details Locksfoot next:

65. **A key aimed DOWN the valley keeps opening, so cone width is what keeps a
    chain out of its neighbour.** Replicating `KEY_slip` (48 deg, 28.6 m
    standoff) along the boardwalk put **20% of KEY_slip's own key back onto the
    accepted Boatyard** — the yard lies further along the same beam, where the
    cone is 20 m across. At <= 26 deg the yard falls outside the cone entirely
    and the spill is 0.000 W/m2. Chains that fire ALONG the gorge are
    narrow-and-many; the dam chain, which fires ACROSS it, keeps 48 deg.
66. **A chain element is not a solo key.** `KEY_slip`'s 0.62 blend is a
    flat-topped cone; eight of them end to end scallop by 0.6 stop (33% ripple).
    `spot_blend = 1.0` cross-fades into the neighbours for 22% ripple at the
    same cutoff angle — so the same zero spill, without the pooling.
67. **Match a chain to the accepted district's MEAN, not to its peak.**
    `KEY_slip`'s peak lands on one spot in the yard; holding that peak the whole
    length of a 28 m boardwalk renders the new district PALER than the accepted
    one (everything sits higher on the AgX shoulder and the values flatten).
    Each chain carries a `level` (0.34 cliff / 0.60 deck / 0.80 dam here).
68. **Scaling an area lamp's power by its AREA preserves radiance, not
    irradiance.** The enlarged source also subtends more solid angle: widening
    `SKY_wash` 34 -> 80 m across the gorge on the by-area rule measured **+43%**
    on the accepted yard. Solve the wattage instead — integrate the emitter
    against a reference point and match the irradiance it used to deliver
    (804 W, not 1151 W). Finding 58 got away with it only because it widened the
    lamp END-ON to the yard, where the added area subtends almost nothing.
69. **Shrink a bounce card rather than move it.** Half the size and a quarter of
    the power is the SAME radiance with a quarter of the reach, and a half-size
    card at half the standoff delivers the same bounce to the thing in front of
    it. That is what lets a Waterfront bounce card exist 20 m from the Boatyard.
70. **EEVEE's shadow budget (2048 tilemaps) overflows silently at ~40 lamps and
    the frame stops being repeatable.** The same file measured 0.364 and 0.405
    mean luminance on consecutive runs, and turning lights OFF made it BRIGHTER
    — dropped shadows, not more light. **Every value judgement in this town has
    to be made in Cycles.** Give the budget back with per-lamp
    `use_custom_distance` + `cutoff_distance`, a coarser
    `shadow_maximum_resolution`, and `use_shadow = False` on faked bounce cards.
71. **Vegetation that sits on a wall must follow the wall's CREST FUNCTION, not
    a translation.** The river pass moved `farwallcrown_*` 26 m in Y only, so
    they ended up hanging at z~15 at the FOOT of a 58 m wall. It also left
    `cliff_far` an 8-vertex slab with a dead-straight z=58 skyline (finding 7).
    Both are rebuilt in `waterfront_light.py`: a modulated crest + a mid shelf,
    with the crowns re-seated ON the crest in groves.
72. **Ground first, and give the waterfront a STRAND.** A cliff that starts at
    the waterline leaves every prop standing on a 40-degree bank: with a slope
    test in the placer, **0 of 130 clutter attempts landed**. A 2.3 m flat rock
    shelf between the water and the foot of the cliff took it to 65, and it is
    what the barrels, nets and crates of a working waterfront actually sit on.
73. **A rail on a flight is a SLOPED box, so its lowest vertices are the four at
    one end.** "The two most distant low verts" therefore measures its SECTION
    (0.06 m), not its run, and every rail-following routine silently no-ops.
    Take the most distant pair in XY over ALL vertices, then split the vertices
    into two end groups by their parameter along that axis.
74. **A tread plank must never overhang.** The tread below is only 0.38 m down,
    so 60 mm of overhang both blocks its down-ray and eats its 2 m headroom.
    Stairs are INSET (-0.045); flat decking is generous (+0.50). Stringers are
    one per FLIGHT, laid outboard, with BOTH ends walked in until every sample
    along the run is clear — clearing only the ends leaves the middle over the
    flight below.
75. **A zigzag staircase cannot carry a straight cover.** A timber throat or a
    roof built on one flight's tread line stands squarely over the flight above:
    the deep stairs' mouth cost seven blocked samples before the cover was
    replaced by a hood at the pad plus a boarded screen, both of which are
    filtered through the Corridor before they are placed.
76. **Place a guard by SEARCH, not by taste.** Scan outward from the walk's own
    lip until the Corridor lets go, then stand the post there. The first pass
    offset the rail 0.36 m the WRONG WAY and stood every post in the walking
    line; the down-ray QA named the exact sample coordinates, which is a faster
    diagnosis than any render. Generalised into `over_walk(x, y, z, pad)` —
    every part this district puts near the stairs is filtered through it.
77. **A moored boat must float with its FLOOR above the water plane**, or the
    pool renders inside the hull. And a boat is a SOLID, not a surface: one
    lofted sheet of stations reads from every camera as a curved sliver of
    plank. Loft the U-section, fold the sheer inboard for a gunwale, floor it,
    and stand a stem and a transom.
78. **Ground a silhouette PER BLOCK, not per object.**
    `fx_far_town_silhouette` is 36 separate boxes cut off at their own heights
    and hanging in the sky; the user could see one broad block over two narrow
    ones from the town and read it, correctly, as a giant table and chairs on
    the ridge. "Every vertex below the OBJECT's minimum + 0.35" grounds only the
    lowest row and leaves every higher block still floating — flood-fill the
    components (finding 61's trick, used the other way round) and drop each
    component's own lower half. Same family as findings 71 and 69: a distant
    mass has to be attached to something at ITS OWN height.
79. **A district must register its assemblies with the audit.** Its own decking,
    bracing, brackets and vegetation come back as interpenetration offenders
    until the `wf_*` pairs are in `geometry_audit.SAME_ASSEMBLY` and the `wf_`
    vegetation prefixes are in `VEG` (16 offenders -> 0, unchanged geometry).

### Rail trim (`tools/master_rail_trim.py`) — a DELIBERATE topology delta
The map generator emits one `bar_*_rail*` per stair LEG, including the flat
approach leg a flight starts from. Under volume collision that railing is a real
fence standing on open decking: on the quay it closed the market -> quay
crossing. The rule (now also in the generator) is that **a rail only earns its
length where it is guarding something** — the walk surface under it is sloped,
or the ground within 1.6 m to either side steps down >= 0.30 m or is missing.
Contiguous non-guarding runs at the head or tail are trimmed; a 0.60 m newel
stub always remains; middles are never carved.

Note the trap: the town's decks are big flat pads (`walk_lm_quay-deck` is
11 x 11 m) and the flights that leave them lie ON them, so "is the ground below
the rail lower than the ground beside it" answers 0 for a rail standing beside
its own treads. The question that separates a guard from a fence is whether the
surface is at DIFFERENT HEIGHTS ACROSS the rail.

Four rails trimmed, identically in `dellhollow-master.blend` AND in the topology
reference `dellhollow-town.blend` (the trim is deterministic from the same
input), so `master_walk_qa.py` still reports **367/367 bit-identical**:
`bar_e_quay-deck__pilot-cluster_l0_railA/B` (4.24 -> 0.60 m, the whole run was
flat quay deck) and `bar_e_shelf-homes__quay-deck_l2_railA/B` (4.02 -> 3.18 m,
the overshoot past the last tread onto the deck).

---

## HANDOVER -> the Locksfoot agent

**State of the master after this pass** (`tools/blends/backups/master-pre-waterfront.blend`
is the roll-back point; `backups/town-pre-railtrim.blend` for the reference blend).

Rebuild the whole pass from the backup with, in order:
```
Blender -b tools/blends/dellhollow-master.blend -P tools/run_rail_trim.py
Blender -b tools/blends/dellhollow-master.blend -P tools/run_wf_light.py
Blender -b tools/blends/dellhollow-master.blend -P tools/run_wf_build.py
```
(`waterfront_build.py` is idempotent — it deletes every `wf_*` object first.)

What you inherit that is now DIFFERENT:
- **The gorge has a key everywhere.** 21 `KEY_gorge_*` spots on KEY_slip's own
  direction and standoff: `wf_deck` (8), `wf_cliff` (6), `dam` (7). Add to the
  chains rather than adding a new rig — the `level`/cone/standoff discipline in
  `waterfront_light.py` is what keeps districts at the same value.
- `SKY_wash` is 90 x 80 at 804 W and covers world x -10..70. If you build east of
  x=70 you must extend it the same way (SOLVE the wattage, finding 68).
- `FILL_bounce_wf_0..5` and `CLIFF_BOUNCE_wf_0..3` are half-size, quarter-power
  copies. Same trick works for Lock Five.
- `cliff_far` is a 654-vertex wall with a real crest; `farwallcrown_*` and
  `farcrown_*` sit on crests now. Don't translate them again — re-seat.
- `wf_ground` carries the bank and the cliff from x=40.1 to x=66.0, y 12.5..31.0,
  terraced under every walkway, with a 2.3 m strand at the cliff foot. It is in
  `geometry_audit.GROUND`. **East of x=66 there is still void** — that is yours.
- All 7 Waterfront walk ribbons + the deep stairs' lower flights are decked and
  `hide_render = True` (47 walk meshes render-hidden town-wide now).

Known defects you will see in your region, all PRE-EXISTING and none mine
(verified against the backup with the same tools):
- `master_walk_qa.py --region 33,66,17,33` reports **1907/1966 (97.00%)**, the
  exact baseline. The 59 blocked samples are all Weave blockout standing on its
  own walkways: `lm_weave-north_1` (32), `lm_pilot-cluster_1` (16),
  `e_weave-huts__fish-dock_rail` (8), `lm_weave-north_2` (1), two ladder rungs.
  The Waterfront contributes **0** blocked samples and **0** headroom samples.
- `geometry_audit.py --region 33,67,16,38`: **0 intersection offenders**, 2
  strays — `lm_pilot-cluster_1_roof` and `lm_weave-north_1_roof`, blockout roofs
  that overlap their own bodies so the support ray starts inside them. The
  baseline had 3; this pass removed one (`lm_deep-stairs-foot_lintel`).
- The stilt clusters (`lm_pilot-cluster_*`, `lm_weave-north_*`) and the elevated
  weave walkways at z~9 still stand on nothing above `wf_ground`. Carrying the
  ground up to them is the Weave's job, not the Waterfront's.

Composition notes: the district was judged from nine cameras in
`tools/waterfront_shots.py` (`boardwalk`, `stairmouth`, `fishdock`, `winchfoot`,
`fromriver`, `fromquay`, `continuity`, `damnorth`, `farrim`). `continuity`
reproduces the Boatyard v10 hero exactly — keep using it: this pass held the
accepted yard at **0.326 vs 0.340** mean luminance in Cycles across the whole
light-rig change, which is the number that says "one town, not two datasets".

---

## Locksfoot PREP findings (`tools/locksfoot_kit.py`, `tools/blends/districts/locksfoot-kit.blend`)

The first kit built to survive a glTF round trip rather than to render in Cycles, and the
first district prepped by an agent that never held master custody. Full plan:
`docs/plans/locksfoot-plan.md`.

79. **`kitlib.blend` cannot ship through glTF, and that is by design — a district kit
    needs a SECOND material language.** Every kitlib material is object-space box
    projection plus a procedural noise/moss layer; the exporter carries neither, so an
    appended kit object arrives in a GLB as flat grey. A kit whose parts may reach the
    runtime speaks only in: vertex colour (`Col`, FLOAT_COLOR, CORNER) -> `COLOR_0`,
    Principled scalars, and image textures with REAL UVs. The one node tree allowed is
    `ImageTexture x VertexColor -> Base Color`, because the exporter writes
    `baseColorTexture * COLOR_0` and that is the same multiply.
80. **A multiply always darkens, so a textured material's vertex colours have to be
    pre-divided by that map's mean luminance.** `weathered_planks` means 0.269, so the
    deck colours carry a x1.64 gain; `old_stone_wall_02` (0.456) and
    `red_slate_roof_tiles_01` (0.512) need none. Without the gain every textured part
    comes back a value or two under the untextured parts beside it and the kit reads as
    two datasets — the same failure as manifest 53, one scale down.
81. **glTF renames the colour attribute and drops unused material slots.** `Col` comes
    back as `Color`, and a fixed global slot order (every object carrying all 8
    materials, so a face's material index is a kit-wide constant) does NOT survive: the
    exporter emits only the materials a mesh actually uses and re-indexes. Anything
    downstream that keys off a slot INDEX must key off the material NAME instead. The
    fixed order is still worth having in the .blend — it is what makes joining and
    splitting assemblies in the master free.
82. **Build a wheel from chord segments, not from a cylinder.** A shrouded waterwheel is
    two rings, N spokes and N buckets; modelling the rings as `create_cone` annuli forces
    a boolean to hollow them. Emitting each sector as an 8-vertex hex (inner/outer x
    two shroud planes) gives a faceted rim that reads as built timber, takes ~2 000 tris
    for a 4.4 m wheel, and lets the buckets be laid at a skew off the radius (which is
    what makes a breastshot wheel read as a breastshot wheel rather than a paddle wheel).
83. **A plank-laying helper must lay boards on a KNOWN side of its run.** `planks(a, b)`
    offsets by the run's left normal, so reversing the two endpoints mirrors the wall
    through its own line. Two assemblies were built inside-out before this was noticed
    (a gate leaf skinned on the wrong side of its heel post, a spill leaf buried in the
    dam). Cheapest fix is to keep the convention and reverse the ENDPOINTS; cheapest
    diagnosis is to print the resulting bbox against the intended one.
84. **A parapet and the thing standing in front of it will z-fight, and a mock-up hides
    it.** The spill bay's raised gate leaf and the crest parapet both wanted
    x1+0.02..x1+0.34. Break the parapet around the slot instead of moving the leaf — the
    gap is what a real dam has, and moving the leaf outboard puts it in the fall.
85. **Foam laid AT the waterline reads as paper.** Flat white slabs whose top face sits
    on the tail pool render as sheets of card floating in the water — the manifest-40
    failure from the other direction. The boil has to BREAK the surface: low wedges,
    tops barely proud, sloping away downstream, and the colour knocked off white
    (0.56 grey-green, not 0.73 white) so it can still be the brightest thing in the bay
    without being the brightest thing in the frame.
86. **A dam's drop is a CASTING decision, not a detail.** `dam-five` is specced at 1.8 m
    (pool-mid 0.2 -> pool-downstream -1.6) while the master reference painting shows
    three waterwheels roughly as tall as the dam face. A 4.4 m wheel on a 1.8 m head
    reads as a wheel standing in a puddle, and no amount of modelling fixes it. Check a
    hero prop's size against the map's own levels BEFORE building it, and if they
    disagree, surface it as a map question — the kit can ship three wheel sizes for the
    price of one function call, but the district cannot ship three dams.
87. **`Blender -b <file> -P <script>` is a genuinely safe read: instance, never edit.**
    The kit's six QA renders are made by copying each library object into a throwaway
    STAGE collection with `o.data = SRC.data` (linked duplicates: one mesh, many
    placements), lighting the stage and rendering. The library collections are
    `hide_render = True` for the duration. Nothing is saved, so the same blend can be
    re-shot from any camera without a snapshot copy — manifest 63 without the copy.
88. **A prep agent can do everything except the master.** Topology truth is readable from
    `tools/blends/districts/town_walk_reference.json` (367 walk/bar meshes with their
    world vertices) and blockout truth from `dellhollow-town.blend` opened read-only —
    between them you can write the whole no-go list, the whole `lm_` replacement table
    and the parcel extents without ever touching `dellhollow-master.blend`. The serial
    custody rule costs nothing but the build itself.
