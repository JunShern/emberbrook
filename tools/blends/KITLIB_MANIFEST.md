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

80. **`kitlib.blend` cannot ship through glTF, and that is by design — a district kit
    needs a SECOND material language.** Every kitlib material is object-space box
    projection plus a procedural noise/moss layer; the exporter carries neither, so an
    appended kit object arrives in a GLB as flat grey. A kit whose parts may reach the
    runtime speaks only in: vertex colour (`Col`, FLOAT_COLOR, CORNER) -> `COLOR_0`,
    Principled scalars, and image textures with REAL UVs. The one node tree allowed is
    `ImageTexture x VertexColor -> Base Color`, because the exporter writes
    `baseColorTexture * COLOR_0` and that is the same multiply.
81. **A multiply always darkens, so a textured material's vertex colours have to be
    pre-divided by that map's mean luminance.** `weathered_planks` means 0.269, so the
    deck colours carry a x1.64 gain; `old_stone_wall_02` (0.456) and
    `red_slate_roof_tiles_01` (0.512) need none. Without the gain every textured part
    comes back a value or two under the untextured parts beside it and the kit reads as
    two datasets — the same failure as manifest 53, one scale down.
82. **glTF renames the colour attribute and drops unused material slots.** `Col` comes
    back as `Color`, and a fixed global slot order (every object carrying all 8
    materials, so a face's material index is a kit-wide constant) does NOT survive: the
    exporter emits only the materials a mesh actually uses and re-indexes. Anything
    downstream that keys off a slot INDEX must key off the material NAME instead. The
    fixed order is still worth having in the .blend — it is what makes joining and
    splitting assemblies in the master free.
83. **Build a wheel from chord segments, not from a cylinder.** A shrouded waterwheel is
    two rings, N spokes and N buckets; modelling the rings as `create_cone` annuli forces
    a boolean to hollow them. Emitting each sector as an 8-vertex hex (inner/outer x
    two shroud planes) gives a faceted rim that reads as built timber, takes ~2 000 tris
    for a 4.4 m wheel, and lets the buckets be laid at a skew off the radius (which is
    what makes a breastshot wheel read as a breastshot wheel rather than a paddle wheel).
84. **A plank-laying helper must lay boards on a KNOWN side of its run.** `planks(a, b)`
    offsets by the run's left normal, so reversing the two endpoints mirrors the wall
    through its own line. Two assemblies were built inside-out before this was noticed
    (a gate leaf skinned on the wrong side of its heel post, a spill leaf buried in the
    dam). Cheapest fix is to keep the convention and reverse the ENDPOINTS; cheapest
    diagnosis is to print the resulting bbox against the intended one.
85. **A parapet and the thing standing in front of it will z-fight, and a mock-up hides
    it.** The spill bay's raised gate leaf and the crest parapet both wanted
    x1+0.02..x1+0.34. Break the parapet around the slot instead of moving the leaf — the
    gap is what a real dam has, and moving the leaf outboard puts it in the fall.
86. **Foam laid AT the waterline reads as paper.** Flat white slabs whose top face sits
    on the tail pool render as sheets of card floating in the water — the manifest-40
    failure from the other direction. The boil has to BREAK the surface: low wedges,
    tops barely proud, sloping away downstream, and the colour knocked off white
    (0.56 grey-green, not 0.73 white) so it can still be the brightest thing in the bay
    without being the brightest thing in the frame.
87. **A dam's drop is a CASTING decision, not a detail.** `dam-five` is specced at 1.8 m
    (pool-mid 0.2 -> pool-downstream -1.6) while the master reference painting shows
    three waterwheels roughly as tall as the dam face. A 4.4 m wheel on a 1.8 m head
    reads as a wheel standing in a puddle, and no amount of modelling fixes it. Check a
    hero prop's size against the map's own levels BEFORE building it, and if they
    disagree, surface it as a map question — the kit can ship three wheel sizes for the
    price of one function call, but the district cannot ship three dams.
88. **`Blender -b <file> -P <script>` is a genuinely safe read: instance, never edit.**
    The kit's six QA renders are made by copying each library object into a throwaway
    STAGE collection with `o.data = SRC.data` (linked duplicates: one mesh, many
    placements), lighting the stage and rendering. The library collections are
    `hide_render = True` for the duration. Nothing is saved, so the same blend can be
    re-shot from any camera without a snapshot copy — manifest 63 without the copy.
89. **A prep agent can do everything except the master.** Topology truth is readable from
    `tools/blends/districts/town_walk_reference.json` (367 walk/bar meshes with their
    world vertices) and blockout truth from `dellhollow-town.blend` opened read-only —
    between them you can write the whole no-go list, the whole `lm_` replacement table
    and the parcel extents without ever touching `dellhollow-master.blend`. The serial
    custody rule costs nothing but the build itself.

## Gate Approach findings (district #3, and the FIRST branch district — `tools/gate_*.py`)

The gate tier is the clifftop shelf where Dellhollow meets the outside world:
Porters' Yard (x~6), Gatehouse (x~11.3), Valley Gate (x~16.7, the town's only land
entrance) and the Cargo Winch head (x~27.3), all at z~24 with the gorge 24 m below.
It is also the first district built on a BRANCH COPY of the master
(`dellhollow-master-gate-branch.blend`) while another agent held the live master,
so half of what it cost is about the protocol rather than the art.

90. **A branch district cannot render-hide the master's ribbons.** Manifest 51's
    `hide_render = True` on decked-over `walk_*` meshes is an in-master move: a
    branch merges by DELETING the manifest's names and APPENDING the district
    collection, so a flag set on a master-owned object is simply not carried.
    Two consequences. The branch's paving has to sit visibly under the walk
    surface anyway (50 mm here) so the QA's down-ray still lands on canonical
    topology, and the review renders have to hide the ribbons AT RENDER TIME and
    never save (`gate_shots.py`) or every judgement is made on gray blockout
    tape. The merge custodian applies the render-hiding town-wide, after.
91. **A tier that already has buildings under it can only carry a PLATE.** East of
    x~18 the gate tier stands over the Inn and Item-Shop shells (z 19..23.55) and
    over the gate->inn stairs. A ground heightfield built the Waterfront way —
    terrace under every walk you meet (finding 38) — came to rest ON the shop road
    5 m below: 8 blocked down-ray samples, named exactly. What works is two
    regimes with an explicit boundary: WEST of it a solid rock promontory that
    plunges from the lip to below the river (there is nothing under it, and the
    town needed that mass anyway — everything on this tier was floating), EAST of
    it a flat 0.40 m plate at the tier's own level whose underside clears the
    roofs at 23.60 and whose plan footprint is DERIVED FROM THE WALK GRAPH: it may
    not exist over any walk within 2 m below it. Corbels under both lips make the
    plate read as carpentry instead of a floating slab.
92. **A walk BELOW the district is a disjunction, not a ceiling.** Ground may lie
    under it (terraced) or clear it by the full 2.0 m corridor — never inside the
    band between. `clamp_walks` treats every walk as a ceiling, which is right for
    a district with nothing beneath it and catastrophic for one built on top of
    the town. The test is three lines: `if lo < h < zt + CORRIDOR_H + d*0.6: h = lo`.
93. **A landmark's interaction PAD is where the player stands, not where the
    machine goes.** The Cargo Winch head was built on `walk_pad_winch-head` —
    32 blocked down-ray samples and 36 headroom samples, the largest single
    failure of the pass, and it was the most obvious placement in the district.
    Rebuilt as a derrick standing SOUTH of the pad, with the boom carried over the
    corridor at 3.4 m and the sheave block hung outside it. Every landmark has a
    2.6 x 2.6 m pad; read it before placing the landmark's own art.
94. **Read the neighbour's terminus off its geometry, never assume it.** The
    Waterfront's `cargo_winch_foot` already carries its hoist rope up to
    (28.70, 10.04, 25.03) — 24 m above the quay and inside the gate parcel. So the
    gate's rim had to be pulled back to y=9.95 there (or the rope would come out of
    the ground), and the new sheave is hung 0.42 m above the existing terminus so
    the two ropes meet without a vertex of accepted art being touched. Three lines
    of `max(P, key=z)` beat any amount of measuring off a screenshot.
95. **A flat Principled colour is not a dark surface, it is an untextured one.**
    v1 gave the ground, road and masonry flat colours at 0.09..0.13 albedo on the
    theory that the NUMBER is what manifest 53 is about. They rendered as pale
    cream next to the Boatyard's box-projected, AO-multiplied, moss-graded
    surfaces: the gap the eye reads is a DETAIL gap, not a value gap. The fix is
    two lines — copy `mat_rock`, re-tint its Base Color through a MULTIPLY mix —
    and it inherits the box projection, the AO multiply, the roughness map and,
    most usefully, the world-up moss layer, which grasses the flat tier and leaves
    the cliff faces bare for free.
96. **`mat_rock` is tuned for a 60 m cliff and has to be re-tiled for a road.**
    At the library's own Mapping scale (0.17) a carriageway reads as one enormous
    boulder and a gate pier as a cave wall. Ground 1.15, road 1.55, dressed
    masonry 1.90 — roughly one texture feature per metre, which is what "coursed
    rubble" looks like. (Manifest 8 from the other direction: the first pass
    tiles too FEW times as often as too many.)
97. **A joined multi-part mesh's bounding box is not its footprint** — finding 62
    used the other way round. Registering keep-outs from `world_bbox(gate_yard)`,
    one object holding a shed at x=7 and a cart at x=20, swallowed the whole
    district: clutter fell from 82 pieces to 12 and the planting to almost none.
    Keep-outs are declared EXPLICITLY, one rectangle per structure.
98. **A rail's beams need the same corridor test as its posts.** The mule lines'
    posts were filtered through `over_walk` and the rails between them were placed
    unconditionally: 14 samples of the Porters' Yard pad under solid timber, on
    both the down-ray and the headroom test. Anything that SPANS between two
    tested points has to be tested at its midpoint too.
99. **Bunting heights are absolute and its sag is per run.** One 1.55 m sag applied
    to runs of 4 m and 8 m put the long one's low point at z=25.3 over a road at
    24.06 — 1.2 m of headroom where the gate wants 2.0. And a pennant on the lens
    is finding 57 again: the run that ends nearest the hero camera is the one that
    ruins it.
100. **The sun runs DOWN the gorge, so the ARRIVAL side of everything is a shadow
    side.** `SUN_key`'s direction is (-0.86, -0.35, -0.38): the player walking in
    off the overworld looks straight into the shaded face of the arch, the toll
    house and the whole yard. Measured, the tier's west faces get 0.82 W/m2
    against 2.75 on its sunlit top. The answer is a faked up-gorge bounce CARD
    (no shadow, 34 m cutoff, solved to hold the shadow side at a fixed fraction of
    the top), not a second key — a key from up-gorge would kill the raking sun
    that is the only thing making a flat 30 m tier legible.
101. **Compare districts on the SHARED rig only.** Up-facing irradiance is
    2.75 W/m2 on the gate tier against 14.02 at the Boatyard reference point, and
    that ratio is not a lighting failure: the Boatyard number is dominated by its
    own eleven 680 W lantern practicals at 3-5 m. Measure the shared rig alone, or
    the practicals will talk you into over-lighting an open-air tier by 5x.
102. **A branch's QA has two regions and both have to be quoted.** The canonical
    gate (`master_walk_qa.py`, default region) must still read 367/367 zero-drift
    and 100% rays — that is what says the branch has not touched the town. The
    district's OWN region is where the honest number lives, and it has to be
    quoted against the SAME region on the base commit, or a pre-existing defect
    reads as the district's.

103. **The town's own backdrop slab is the gate tier's biggest problem, and it is
    not the sky.** Every `arrival` frame had a blown white field behind the gate.
    A ray-cast through it named `cliff_town` at 28 m: the town's backdrop is ONE
    170 x 6 x 46 m box at y -6..0 with a blockout material, and the gate road runs
    4..9 m in front of it, 24 m up, while `SUN_key` travels toward -y and hits it
    square on. Every other district looks at that box edge-on, from water level or
    in shadow. cliff_town is untouchable, so the fix is a VENEER inside the parcel:
    a 28 m x ~16 m rock face standing at y 0.1..0.9, textured with `mat_rock`,
    crest modulated (finding 7) and — the part that matters — held ABOVE
    cliff_town's own top edge at z=37.0 everywhere, or a band of the blockout slab
    shows over it and the whole exercise buys nothing. Pressed flat to 0.10 m
    behind every building so nothing already placed is disturbed. Autumn crowns
    seated ON the crest (findings 71/78) finish the skyline.
104. **Diagnose a blown field by RAY-CASTING it, not by reasoning about it.** Three
    rays through the suspect pixels took two minutes and overturned a confident
    diagnosis ("the world gradient near the sun") that would have shipped as an
    open question for the user instead of a fix. `sc.ray_cast` from the camera
    down a reconstructed pixel direction names the object and the distance.

## Gate Approach POLISH findings (v7 — the arrival frame, `tools/gate_*.py`)

The user's verdict on v6 was "a pretty good start" with three flags: the arrival
frame read as a murky corridor, the bunting read as saturated raw kit quads at
close range, and the planting crowded the near-field cameras. Everything below
came out of fixing those, and most of it is not about the gate.

105. **A hero frame with no subject is usually a frame with no VALUE STRUCTURE,
    and the fix is a surface, not a lamp.** The arrival frame's arch stood 4 m in
    front of 20 m of cliff wearing the *same* `mat_rock` at the *same* value, so
    it had no silhouette from any western camera. The instinct is to light the
    arch — but the bounce card that lifts the arch's shadow side lifts the wall
    behind it by the same fraction, which is exactly why v6's card stopped at 55%
    of the sunlit top and could not go further without just making a paler frame.
    Deriving the veneer as `mat_gate_cliff` (a third darker, cooled toward blue)
    separated figure from ground for two lines of node work, and *then* the card
    was affordable at 66%. Order matters: build the field, then light the figure.
106. **The near field is not a radius, it is the space between a lens and its
    subject.** Two cuts of a thinning rule failed before the third worked. Absolute
    radii around six eyes (2.7 m / 8.0 m) stripped the grass tufts along with the
    1.4 m autumn clumps — 180 tufts down to 38 — because at 5 m those are not the
    same problem. A pure distance/size ratio then deleted *every tree in the
    district*, because in a 30 m parcel a 4 m crown is always within nine of its
    own lengths of some camera. What separates an obstruction from scenery is
    where it stands **relative to the subject**: per camera, in frame, and nearer
    than ~85% of the camera-to-aim distance, and only then a size test. Clumps
    26 -> 15, everything else unchanged. (`gate_lib.near_field`.)
107. **Cull the masses, cap the ground cover.** The same rule must not treat a
    fern like a tree. Vegetation that lies on the floor never stands between a
    lens and its subject; it only ever needs a SIZE ceiling, or the tier goes
    bald in exactly the places the cameras point. `clone(..., cull=False)` for
    tufts/ferns/creepers, cull=True for crowns, clumps and clutter.
108. **A shot list is BUILD DATA.** Density and prop size are not properties of a
    zone, they are properties of a zone seen from somewhere — so the cameras moved
    from `gate_shots.py` into `gate_lib.py` and the build imports them. A camera
    edited in the shot script alone would silently invalidate the thinning that
    the frame was thinned for.
109. **A roof's course count comes off its DEPTH, not its height.** What the eye
    counts on a roof is the EXPOSURE — the strip of each course the one above
    leaves showing. Nine 0.42 m boards per pitch steps 0.30 m in per course, and
    `mat_shingle_mossy` then paints one bright green stripe per step: four of
    those crossing the top of the hero frame in one band is why v6 read as a
    lumber yard. Exposure ~0.12 m, courses broken across their length on a
    half-tile stagger, and it reads as tiles. Cost: boxes, which are free.
110. **The tallest thing in a gate has to be the gate.** The toll house ridge
    (28.80) and its chimney (29.39) matched the arch (29.21), so the district had
    no skyline — three roofs and an arch merged into one horizontal band. The arch
    got a proper gablet on posts and the lodge lost 0.72 m of ridge and 0.90 m of
    chimney. Deliberate subordination is a modelling decision, not a camera one.
111. **Read the landmark's PAD before placing the landmark — in X as well as Z.**
    Finding 93 caught this for the winch by measuring headroom; here nothing
    failed a gate at all. The Gatehouse simply stood at x=12.55 when
    `walk_pad_gatehouse` is centred at 11.33, and that 1.2 m put a 5.3 m lodge
    shoulder to shoulder with a 1.9 m gate pier in every western frame. Seating it
    on its own pad was both truer to the map and the single largest compositional
    improvement in the pass. (It then clipped the porters' shed by 0.23 m and the
    audit named the pair immediately — move the piece with no map position.)
112. **One lit window beats any number of lanterns.** The accepted Boatyard hero
    has exactly one and it is where the eye lands. The gate had none: an emissive
    pane in the toll hatch at strength 2.1-3.4 (not the 90 a lantern globe wants —
    at window scale AgX creams the hue out and it lands as a clipped white
    rectangle) gave the arrival frame the focal point it had been missing. And
    v6's two arch lanterns were on the piers' TOWN face, invisible from every
    frame an arriving player is ever in.
113. **Bunting is a DETAIL gap, not a colour gap — finding 94 one scale down.**
    `mat_flag_*` is one flat diffuse mixed with one flat translucent: fine at 20 m
    on a quay, a coloured rectangle at 4 m from the town's front-door camera. The
    fix is a weave (object-space noise x a broad sun-fade multiplying the tint),
    six materials instead of four so the variation is in VALUE not hue, and real
    cloth geometry — a stiff top edge, a taper to the point, a per-pennant curl
    signed by its phase so a run is not N copies of one shape.
114. **A veneer's extent is set by the shallowest ray that can see past it, and
    its FOOT matters as much as its crest.** Two separate leaks, both found by
    ray-casting pixels (finding 104) and neither guessable: a sightline through
    the gate opening crosses y=0.5 about 28 m downstream, so a veneer ending at
    the ground sheet's x=29.6 put the blown slab straight back in the one frame
    the exercise was for; and seating the foot 1.6 m under the *local* ground put
    it at z~22.4 east of the promontory, where the ground is a 0.40 m plate, so
    every ray under the gallery found `cliff_town` again. x to 31.6, floor at 19.0.
115. **An idempotent build must never be able to un-record its own deletions.**
    `gate_build.py` deletes every `gate_*` object and rebuilds, and it rewrote the
    deletions manifest from what it found — so the *second* run on its own saved
    output found nothing left to delete and published an EMPTY list. That file is
    the one thing the merge custodian obeys literally: the blockout shells would
    have survived the merge standing inside the built art. The manifest
    accumulates now (union by name), and the log prints "7 shells (0 removed this
    run)" so a no-op run says so out loud.

### HANDOVER -> the merge custodian (gate branch)

Rebuild the whole district from the base master with, in order:
```
Blender -b tools/blends/dellhollow-master-gate-branch.blend -P tools/gate_build.py -- save
Blender -b tools/blends/dellhollow-master-gate-branch.blend -P tools/gate_light.py -- save
```
`gate_build.py` is idempotent (it deletes every `gate_*` / `KEYG_*` object first)
but it must run BEFORE `gate_light.py`, because the light rig's lamps are `KEYG_*`
too and a rebuild would delete them.

Merge recipe:
1. delete the object names in `tools/blends/districts/gate_branch_deletions.json`
   (7 of them: all `lm_valley-gate_*`, `lm_gatehouse_*`, `lm_winch-head_*` — three
   of p-gate's four members; the fourth, porters-yard, has no `lm_` shell, only the
   canonical `walk_lm_porters-yard`, which is untouched).  The manifest accumulates
   and is never rewritten empty by a rebuild (finding 115);
2. append the `GATE_DISTRICT` collection (139 objects incl. 5 `KEYG_gate_*` spots,
   2 `KEYG_approach_*` cards and 9 lantern practicals).  Foliage carries the
   runtime's never-standable prefix: `veg_gate_*`, not `gate_*`;
3. remap duplicate materials by name — the district adds `mat_gate_road`,
   `mat_gate_turf`, `mat_gate_stone`, `mat_gate_sack`, `mat_gate_troughwater`,
   `mat_gate_cliff`, `mat_gate_window` and six `mat_gate_flag_*` cloths, and reuses
   everything else;
4. apply manifest-51 render-hiding to the gate tier's ~73 walk/bar ribbons
   (`gate_shots.py` lists the exact filter it uses for renders);
5. re-run both gates.

Review renders: `docs/qa/districts/gate_v1..v7_*.png`; v7 is the polish pass and
covers the three flagged frames (`arrival`, `gate`, `tollyard`).  Transcripts in
`docs/qa/districts/gate_qa.txt`.  Per the 2026-07-29 render norm the v7 set is
EEVEE and deliberately small — the value calls come from `gate_light.py`'s measured
irradiance, not from a frame (manifest 70), and QA cameras are scaffolding.

Two backdrop leaks remain and are NOT this parcel's to fix: `cliff_town` shows past
the east end of the gate's veneer at (56.8, 0.0, 29.2) and past its west end at
(-7.9, 0.0, 24.7).  Both are outside p-gate (x 1.5..31.8).  The SHELF tier owns the
first — veneer x 31.6 onward the same way (finding 103/114) and it closes.


---

## Locksfoot findings (in-master district #4 — `tools/locksfoot_*.py`)

The district that had to continue a rig which had been **truncated**, not finished:
the Waterfront's sky stops 4 m past its own east edge, and the whole gorge east of
x=66 was void.  It is also the first district whose hero prop only works because
the user changed the MAP (`dam-five` drop 1.8 -> 4.0, commit `e3f59a0`).

### Light

116. **A sky wash is a TILTED SHEET, so moving its centre in X does not slide it
     along itself — it lifts the whole plane.**  `SKY_wash` is 90 x 80 m at
     `rot_x = 7.125 deg`, which is `dz/dx = -0.125`.  Re-centring it from x=30 to
     x=51 to cover x -10..112 puts the sheet **2.6 m higher over the Boatyard**,
     and the finding-68 solve then asks for MORE power than the by-area rule
     (1249 W vs 1226 W) purely to undo the lift it just caused.  Any resize or
     extension has to keep the new centre ON the old plane:
     `z = 26 - 0.125 * (x - 30)`.  With that, the solve lands where it should —
     just under the by-area number (ratio 0.974).
117. **There is NO wattage that extends a truncated sky and leaves the
     neighbour's edge alone, and the solver will tell you so.**  Setting up the
     2x2 "hold the Boatyard AND hold the Waterfront's east end" returns
     `E_east = 0.0 W` **exactly**.  That is not a numerical failure, it is the
     answer: the accepted Waterfront was lit by a sky that stopped at x=70, so
     its east end is artificially dark and continuing the sky must brighten it.
     The decision is therefore *which* reference to hold, and the honest move is
     to hold the new district's own working level, then **measure and publish**
     the cost.  Measured, in Cycles, on accepted-content-only frames:
     Boatyard `continuity` **+0.04%**, Waterfront west **+0.21%**, Waterfront
     interior **+0.27%**, Waterfront **east lip +1.87%** — an order of magnitude
     under what the irradiance delta alone suggests, because the sky is only
     about a fifth of the light budget at deck level.  The one knob that
     actually moves that last number is where the extension STARTS: pushing the
     run's west edge from x=70 to x=76 took the east lip from +35% to +27% of its
     sky irradiance at no cost to Locksfoot, because the solve just redistributes.
118. **Measure a neighbour's luminance only on frames whose CONTENT is the
     neighbour.**  Two of the Waterfront's own nine cameras (`boardwalk`,
     `fishdock`) look EAST and have Locksfoot in the background, so they reported
     +9% and +24% when the district behind them was built — measuring the new
     art, not the disturbance to the old.  Swapping to west-looking Waterfront
     cameras cut the same numbers to +2.4% and +1.1%.  A continuity camera has to
     be chosen for what is IN it, not for which district owns it.
119. **A backup blend can only be rendered from the directory its relative
     texture paths were written for, and a missing-texture frame reads as a
     luminance regression.**  `master-pre-locksfoot.blend` uses
     `//../textures/...`; copied to a scratch dir (or read in place from
     `tools/blends/backups/`) that resolves to nothing, every material renders
     Blender's magenta, and the "before" measurement came back 0.2539 against an
     "after" of 0.2259 — an apparent **-11% regression that was entirely the
     measuring rig**.  Copy a backup to `tools/blends/` (the same depth) before
     rendering it, and *look at* a before-frame before believing a delta.
120. **A chain element standing beside a neighbouring chain's LAST aim point
     closes a TAPER; it is not spill.**  `chain_range` deliberately measures the
     interior because a chain's ends fall off "by design — there is no next
     lamp".  Once there IS a next lamp the end is no longer a taper, and the
     honest report is two separate numbers: spill measured where no chain is
     adjacent (0.0000 W/m2 into both accepted districts here) and seam closure
     quoted against the chain's own level (0.186 -> 0.272 vs a working level of
     0.316 — the taper is filled, not overshot).  Asserting on the seam as if it
     were spill fails a correct rig.

### Topology vs. what the map asks for

121. **Canonical topology can forbid the machinery the map promises, and the
     right answer is a different STATE, not a smaller model.**  `lock-five` wants
     two mitre gate pairs, but `walk_e_moorage__lock-five_l1` and
     `walk_e_lock-five__north-landing_l0` run at z~0 straight THROUGH both gate
     heads and `walk_pad_lock-five` takes 2.60 m of a 3.60 m chamber.  A closed
     3.74 m leaf anywhere in there cost **24 blocked samples**.  Locks recess
     their leaves into the wall when they are OPEN — and an open lock is also the
     correct state for a district whose story is a boat being brought through.
     Same class as finding 87: check the hero against the map's own numbers
     first, and let the STAGING absorb the conflict.
122. **A pool is a solid slab, and a lock chamber is cut off from its pool by its
     own gates.**  `walk_pad_lock-five` sits at z -0.08 under a `pool-mid`
     surface at +0.20, so its down-rays hit water — 7 samples in the baseline,
     22 more the moment the dam blockout that had been hiding them was removed.
     Notching the pool around the chamber and giving the chamber its own
     mid-cycle water is both the physical truth and worth **22 blocked samples**.
123. **A landmark that is a FILLED disc (manifest 35) reaches further than it
     looks.**  `walk_lm_moorage` is 8 m across and its inland lip is at y=23 —
     3 m inland of anything that reads as "the dock" — and it silently caught the
     tenant shack's drying stage and six props standing on it.
124. **A blockout that swallows its own landmark's standing pad is why the
     baseline had samples at all.**  `lm_tenant-shack_body` covered
     `walk_pad_tenant-shack` entirely (5 blocked).  The kit shack is 5.07 m and
     the pad is 2.60 m, so the building goes INLAND of its pad and opens onto it
     — which is also how a shack with a porch actually sits.

### Placement

125. **`over_walk` on a point misses a tall object.**  A 2.9 m winch, a 3.7 m gate
     leaf and a 4 m canopy only have to touch the corridor once; testing the base
     alone let a rim clump take 19 samples of the Lockhead walkway and a balance
     beam 11 of the boardwalk.  `clear_box(x, y, z0, z1, pad)` — step the whole
     height band — took the district from 64 self-inflicted blocked samples to 0.
     A sloped BEAM needs the same treatment along its section (a 0.40 m stringer
     probed on its centre line still reached over the moorage).
126. **The walk Corridor keeps props out of the WALKING lines but nothing keeps
     them out of EACH OTHER.**  A 7 m lock coping carrying a winch, a capstan,
     three bollards and loose cargo placed each of them independently and the
     audit found **50 interpenetrations**.  One shared occupancy list —
     `spot(x, y, r)`, reserve-or-refuse — took it to 0 with no other change.
     Every district that scatters props needs one; the Corridor is not it.
127. **Vegetation from boxes reads as boxes.**  Three `obox` shells and a trunk
     is what the first canopy pass shipped, and on a cliff face it read as a pile
     of green crates.  Tapered `cyl` drums at 9 segments cost the same and read as
     mass (finding 15).

### Working in someone else's file

128. **A helper that returns an EXISTING datablock untouched makes a build script
     non-idempotent for VALUES.**  `plain(name, rgb, ...)` returned early if the
     material already existed, so `mat_boil` was knocked down twice in the source
     and the master kept the first number both times.  Create-or-RE-TONE.
129. **A clean-up that matches a SUFFIX misses the datablock-name drift it is
     there to clean, and stacked practicals are invisible in a log.**  The
     lantern practicals are `lf_lantern_N_light`, cleared each run by
     `startswith("lf_") and endswith("_light")`.  But removing the object orphans
     its light data, so the next run's lamp is `lf_lantern_0_light.001` — which no
     longer ends with `_light`.  Eight rebuilds left **45 stacked 680 W point
     lamps where six belong**, and the build log said "6 lanterns" every single
     time.  It cost the accepted Waterfront's east lip **+9.4% instead of
     +1.9%**, and it was only ever going to be caught by COUNTING the objects in
     the saved file.  Every district pass should end with an inventory —
     `Counter(o.type for o in objects if name.startswith(prefix))` — checked
     against what the log claims it made.
130. **Scope a texture-path remap to the maps you actually appended.**  The kit's
     images are relative to `tools/blends/districts/` (manifest 63) and have to be
     re-pointed — but the first version looped over `bpy.data.images`, which is a
     loop over the WHOLE TOWN's textures.  Match on the three known basenames,
     and `user_remap` + remove the duplicate datablock the append just made, or
     the master collects `old_stone_wall_02_Diffuse.jpg.001 ... .0NN`, one per
     rebuild.  The same is true of light datablocks: removing the OBJECT orphans
     its data, so the next run's copy is `SKY_wash_lf_0.001` and the names drift
     out of the handover.
131. **Kit donors stand at the WORLD ORIGIN and `hide_render` does not stop a
     glTF export.**  `libraries.load` puts 19 finished assemblies at (0,0,0),
     which is inside the Boatyard.  Rename them (`KITSRC_*`) so the placed copies
     keep the clean names, and DELETE them once the last placement has copied
     from them.

### What the drop ruling bought

132. **A map edit is the cheapest fix for a scale problem, and it shows.**  The
     user's ruling (drop 1.8 -> 4.0, `pool-downstream` -1.6 -> -3.8) lets the
     kit's 4.4 m `lf_wheel_breast` hang with its axle at z -1.55, spanning
     z -3.81..+0.71 against a head of +0.20 and a tail of -3.80: the wheel takes
     water just under the crest and clears the bed.  The master-side cost is
     small and entirely mechanical — recut `water_pool-downstream`, stop the
     shared `riverbed` at the dam and give the tail its own deeper bed, and carry
     the bank down to the new level across the dam's own footprint — but it is
     not optional: at the old level the tail pool would have been **10 cm deep**
     over a bed whose top is at -3.90.

---

## HANDOVER -> the next district (from Locksfoot)

Rebuild the whole pass from `tools/blends/backups/master-pre-locksfoot.blend` with,
in order (the light rig must go first — `waterfront_light.py` deletes every
`KEY_gorge_*`, so re-running IT would remove the Locksfoot chains):
```
Blender -b tools/blends/dellhollow-master.blend -P tools/locksfoot_light.py -- save
Blender -b tools/blends/dellhollow-master.blend -P tools/locksfoot_build.py -- all save
```
`locksfoot_build.py` is idempotent (it clears every `lf_` mesh first) and takes a
phase list: `ground | deck | lock | dam | build | boats | dress | all`.

**What you inherit that is now DIFFERENT**
- `lf_ground` carries bank, 2.30 m strand and cliff from **x 66.1 to 112.1**,
  y 12.5..34.1, welded to `wf_ground` by re-using the Waterfront's own height
  function at the join and terraced under **every** walkway in the region —
  including the Weave's, the Lockhead's and the cottage spur's, none of which are
  Locksfoot's to build.  It carries two landforms: the Lockhead promontory and
  the Keepers' Spur buttress that puts rock under `walk_pad_keepers-cottage`.
- **The water east of the dam has moved** (map `e3f59a0`): `water_pool-downstream`
  is now -3.80, `riverbed` stops at x=87 and `lf_riverbed_tail` runs x 87..131 at
  -7.60.  `water_pool-mid` is **notched** around the lock chamber.
- The sky reaches the whole gorge: `SKY_wash` is untouched, and `SKY_wash_lf_0/1`
  (62 x 20 m each, 159.1 W / 124.3 W) cover world x 76..116 on its own plane.
  34 new `KEY_gorge_lf_*` spots in three chains — `lf_deck` (12, 24 deg, 914 W,
  level 0.60), `lf_cliff` (11, 24 deg, 359 W, 0.34), `lf_dam` (11, 24 deg,
  2269 W, 0.80).  **`lf_dam` is 24 deg, not 48**: it lights the dam's DOWNSTREAM
  face, so it stands downstream and fires back UP the gorge — along it, not
  across it — and at 48 deg the Waterfront sits inside the cone 52 m away.
- `FILL_bounce_lf_0..4` and `CLIFF_BOUNCE_lf_0..5`, half size / quarter power.
- 25 walk ribbons are decked and `hide_render = True`.

**Numbers, against the recorded P0 baseline**

| gate | baseline (P0) | now |
|---|---|---|
| `master_walk_qa.py` identity | 367/367 bit-identical | **367/367 bit-identical** |
| `master_walk_qa.py` (default region) | — | **1308/1308 = 100.00%, PASSED** |
| `--region 63,112,12,34` rays | 2253/2411 = **93.45%** (158 blocked) | **2379/2411 = 98.67%** (32 blocked) |
| ... blocked samples owned by this district | n/a | **0** |
| `geometry_audit --region 63,112,12,44` | 0 offenders, 3 strays | **0 offenders, 2 strays** |
| `geometry_audit --region 84,92,24,76` | 0 offenders, 0 strays | **0 offenders, 0 strays** |
| Cycles mean luminance, Boatyard `continuity` | 0.2237 | **0.2238 (+0.04%)** |
| ... Waterfront `stairmouth` / `winchfoot` | 0.2260 / 0.2408 | **0.2266 / 0.2413 (+0.27% / +0.21%)** |
| ... Waterfront east lip (the sky's real cost) | 0.2196 | **0.2237 (+1.87%)** |

All 32 remaining blocked samples are **pre-existing blockout owned by other
parcels**: `lm_weave-huts_1/2` (16), `lm_keepers-cottage_body` (8),
`e_lockhead__lock-five_rung00/30` (5), `e_weave-huts__fish-dock_rail/rung00` (3).
The two strays are `lm_keepers-cottage_roof` and `lm_weave-huts_1_roof` — blockout
roofs that overlap their own bodies, both pre-existing.  Locksfoot removed one of
the baseline's three (`lm_tenant-shack_roof`).

**Honest weaknesses handed on**
- **The Weave's bare ribbons dominate two of the eight camera angles.**
  `walk_e_weave-huts__moorage_l0/l1` and `walk_lm_drying-decks` are undecked
  white blockout hanging over the Moorage; the plan assigns the upper legs
  (z >= 4) to the Weave and this pass held that line.  They are the single
  biggest thing between Locksfoot and the Boatyard-v10 bar.
- Same for `walk_e_keepers-cottage__lock-five_l0/l1` above z 3.2 and
  `walk_pad_keepers-cottage` — `p-cottage`'s, and the kit's `lf_keeper_cottage`
  is still unused and waiting for that pass.  The rock is already under them.
- **`lf_crest_gate` costs 7 headroom samples (0.29%)** standing on
  `walk_pad_dam-crest-gate`.  That is the map's own intent (`state: "closed"`,
  "barring the crest walk") and it is 0 blocked samples, but it is a real
  obstruction and the next agent should not be surprised by it.
- The lock's coping still reads a value or two light against the black dam under
  the `lf_dam` chain's 2269 W, and the spill bays' kit nappe/lip is brighter than
  finding 86 would like even after `mat_boil` was knocked to 0.132.
- `p-lockhead` was left entirely untouched (jurisdiction unresolved) — but the
  ground and the cliff under it are built and terraced, so whoever takes it
  inherits a site, not a void.
- The **tar-dark story boat is NOT built** (ruled a shared library asset);
  `lf_barge_moorage` stands at the Moorage as a mooring placeholder so the berth
  and its framing are already correct when the real hull arrives.

Composition was judged from eleven cameras in `tools/locksfoot_shots.py`
(`lockbasin`, `damface`, `crestwalk`, `moorage`, `cottagespur`, `northlanding`,
`fromcrossing`, `fromriver`, `westseam`, plus `continuity` and `wfcontinuity`).
EEVEE versions v1..v6, Cycles beauty set `locksfoot_v6cyc_*`.

**Runtime canon adopted mid-pass:** commit `5e2d7fc` made `veg_` the NO-STAND
prefix (`play3d.html`: `water_` / `lm_` / `veg_`), because tree canopies were
climbable terrain.  Locksfoot's foliage is therefore `veg_lf_rimclump_*` and
`veg_lf_fern_*`, and `geometry_audit.VEG` now carries a bare `veg_`.  **The rest
of the town has not been migrated** — `wf_rimclump_*`, `wf_fern_*`,
`wf_creeper_*`, `wf_tuft_*`, `rimclump_*`, `creeper_*`, `farwallcrown_*` and the
gate branch's `gate_*` foliage are all still standable at runtime.  That is a
town-wide rename, not one district's, and it is the next cross-cutting job.

**Still outstanding (deliberately, and on the Waterfront's own precedent):** no
`del-lockfive` / `del-cottage` / `del-northlanding` / `del-lockhead` /
`del-crossing` depth bundles were baked.  There is no `del-waterfront` bundle
either — the exterior districts' occlusion bake has been a separate rollout, and
these five parcels are all still `draft: true` in the map.  The blend is ready for
it: the eleven `locksfoot_shots.py` cameras include the parcels' own framings, so
`tools/depth_bake.py` needs a camera per sceneKey and nothing else.

## Overworld ROUND 2 findings (styles E–H, `tools/overworld2_*.py`)

Round 1 (`6737da2`) put four art treatments on one shared miniature valley tile and
the user picked **D — textured naturalistic**.  Round 2 branches D four ways toward
realism under one hard constraint the user set: *the world map must cost far less
authoring time than a town.*  So round 2 does not re-author the world — it imports
round 1 (`overworld_lib.Field`, `overworld_build.build_base`, `overworld_build.dusk_rig`)
and spends everything on four different TERRAIN PIPELINES plus the shared tar boat.

  E  painted naturalism — albedo bake + dusk LIGHTING bake, terrain ships UNLIT
  F  PBR miniature      — NO bake; four tiled diffuse+normal+roughness slots
  G  relief map         — six altitude/slope bands + baked AO + detail normal on UV1
  H  lush canopy        — one plain albedo bake; the budget goes into alpha-MASK cards

133. **A guarded `main()` is what makes a second round cheap.**  `overworld_build.py`
     called `main()` at import, so nothing could reuse it.  Wrapping that one call in
     `if __name__ == "__main__":` (under `Blender -P`, `__name__` IS `"__main__"`, so
     round 1 still runs unchanged) let round 2 `import overworld_build` and inherit
     the field, the `Prop` accumulator, `build_base()` and — crucially — `dusk_rig()`.
     The dusk key is now literally the same function call in both rounds, which is the
     only way a cross-round comparison sheet means anything.

134. **A walk ribbon floating above the terrain SHADOWS the map it is about to
     sample.**  `walk_road` / `walk_village_green` / `walk_dockpath` sit 0.06–0.09u
     above the ground and take planar UVs into the same baked map.  Left visible during
     a lighting bake they cast a hard-edged shadow onto their own ground, and style E's
     road came out of the bake **pure black**.  The 1.45u scale capsules do the same and
     their shadow would have been baked into the world permanently.  `hide_render` on
     every overlay + every render-only reference before ANY bake, restore after.  This
     is not specific to E: it corrupts an AO bake just as badly.

135. **glTF `alphaMode: MASK` is no longer read from `Material.blend_method`.**  Since
     Blender 4.2 the exporter *sniffs the node tree* (`search_node_tree.detect_alpha_clip`)
     for `Alpha -> Math:GREATER_THAN(cutoff) -> BSDF.Alpha`, `Math:ROUND`, or
     `1 - (X < cutoff)`.  A material with `blend_method = 'CLIP'` and a bare
     image-alpha link exports as **BLEND** — order-dependent, sorts wrong through a
     canopy, and exactly not what a foliage card wants.  Insert the explicit
     GREATER_THAN node; `blend_method`/`alpha_threshold` are then only cosmetic.

136. **`for x in coll: x.select = (x is n)` silently does nothing.**  Iterating a bpy
     collection hands back a FRESH proxy each time, so `is` never matches the node you
     are holding and the bake target ends up deselected — Blender then reports
     *"No active and selected image texture node found"* and the bake writes an empty
     image while the script happily prints success.  Clear the flags in the loop, then
     set `n.select = True` on the object you already have.

137. **A background Blender cannot bake without `temp_override`.**  There is no window,
     so `bpy.context.scene` is not the scene you built, and `bpy.ops.object.bake.poll()`
     fails with *"context is incorrect"*.  The override has to name all four:
     `scene`, `view_layer`, `object`/`active_object`, and `selected_objects`.
     `select_set(..., view_layer=vl)` must be used too — the bare form targets the
     wrong layer.

138. **Per-facet triplanar UVs on a herringbone-triangulated terrain paint a diamond
     lattice.**  Round 1's terrain alternates its triangulation diagonal, so adjacent
     facets disagree about which axis is dominant and flip between the XY and the
     lateral projection.  On style F's first render the whole north rim wore a regular
     diamond grid.  Choose the projection axis from the ANALYTIC FIELD GRADIENT at the
     face centre (`np.gradient(F.H)`), not from the facet normal: neighbouring faces
     then agree and the lattice disappears completely.

139. **Tiled PBR is crisp everywhere and repeats visibly on any slope longer than ~8
     tiles.**  F at a 4.0u tile showed obvious repetition across a 40u rim; 6.2u plus
     the art-directed vertex-colour mottle makes it acceptable but never invisible.
     This is the permanent trade against a baked map: the bake is soft and unique, the
     tile is sharp and periodic.  There is no third option inside what glTF carries
     (no second UV blend, no procedural break-up, no detail-map multiply on baseColor).

140. **When the light is IN the map, ship the terrain UNLIT.**  E bakes albedo x dusk
     lighting into one image; feeding that to `baseColor` doubles up under the runtime's
     `AmbientLight(0.95) + DirectionalLight(1.3)` and the painted shadows go grey.
     Black `baseColorFactor` + the map on **Emission** exports as `emissiveTexture`
     with a black base — three.js then renders exactly what was baked, which is the
     pre-rendered-background contract applied to a 3D tile.  Cost: the terrain no
     longer responds to any dynamic light, ever.

141. **The shared river is narrower than the boat is long — carve, do not edit the
     field.**  At the village the valley profile gives a 2.53u half-width (≈5u of
     water) against a 4.6u hull, and the bank clears the waterline only 1.5u out.
     Widening `overworld_lib` would have invalidated style D as the reference row, so
     round 2 cuts a **mooring basin into each style's own terrain copy** —
     `pool_w()` is one anisotropic ellipse (longer along the river, dug harder into the
     village bank), `carve_pool()` only ever lowers vertices, and `pool_height()` is the
     same analytic function so the jetty root, the post feet and the dock path all agree
     with the mesh by construction.  ~30 lines, no hand placement.  The same guard has
     to be applied to G's micro-relief displacement or the basin gets a rippled floor.

142. **Tune terrain bands against the field's own percentiles, not by eye.**  G's first
     pass put snow on everything above alt 19 and turned the tile into a chalk model;
     the field's altitude p90 is 25.7 and p99 is 30.1, so `sstep(23.5, 29.5, alt)`
     lands the dusting on the top ~8% where it belongs.  Same for scree
     (`sstep(0.85, 1.45, slope)`, slope p90 = 1.71).  Two lines of numpy beats an
     afternoon of eyeballing renders.

143. **An alpha atlas must survive a JPEG-format export.**  `export_image_format="JPEG"`
     is what keeps F's 21 maps down to 12.7 MB, and the exporter is smart enough to
     leave images with used alpha as PNG — but that is worth ASSERTING, not assuming: a
     MASK material whose baseColor came out `image/jpeg` has no alpha left and every
     cutout silently becomes a solid card.  `overworld2_verify.py` now walks every
     `alphaMode: MASK` material back to its image's `mimeType`.

144. **Multiplying an alpha atlas by a class vertex colour makes black splats.**  glTF
     can only do `baseColorTexture * COLOR_0` and a multiply only darkens (round-1
     finding), so a green atlas times a green class colour is a very dark green.  Worse,
     the round-1 pre-divide gain reads the image's MEAN — and an alpha atlas is mostly
     transparent black, so the gain pins to its clamp and blows the foliage white.
     Compute the mean over `alpha > 0.5` pixels only, and for foliage just drop the
     vertex-colour multiply: the atlas already carries per-leaf variation.

145. **A card showing four thin blades reads as litter, not as grass.**  The first
     meadow pass drew 46 sparse blades per atlas cell and the chase camera saw
     scattered green flakes lying on the ground.  150 blades packed toward the cell
     centre, thicker at the base, at 0.56 x 0.66u per card, is the difference between
     "grass" and "debris".  Canopy cards need the opposite care: pitch them 38–72° from
     vertical and lean them OUTWARD (`yaw = a - pi/2`, not `a + pi/2` — the sign decides
     whether the canopy opens or collapses into the trunk), or the top-down chase camera
     sees them edge-on.

146. **The dusk key comes from the south, so a boat shot must look ALONG the river.**
     Both banks of an east–west river are lit from one side only; a camera across the
     channel puts the hull against a black north-facing cliff.  Sitting the camera in
     the water upstream of the bow, at `wl + 1.95`, gives the sheer line a lit valley
     behind it.  The moored boat also has to be on the camera's side of the jetty —
     with the deck between them the hero prop is a silhouette behind a fence.

147. **Two coplanar alpha-blended water sheets flash rectangles.**  The river strip and
     the new basin meet at the same z and EEVEE sorts them per fragment.  Offsetting the
     basin 0.02u down AND setting `show_transparent_back = False` makes the ordering
     deterministic.  Also set `scene.eevee.shadow_pool_size = 1024` (an INT, not the
     string an enum would want) — a 120 x 90u tile overflows the 512 default and drops
     shadows in patches.

148. **Build cost per tile is the axis the user is actually choosing on** (measured on
     an M1 Max, Cycles on Metal, `docs/qa/overworld/PERF2.md`, regenerated from
     `build_times.json` so the table can never drift from the run):

     | style | s/tile | draws | tris | GLB MB | tex MB | what recurs per new tile |
     |---|---|---|---|---|---|---|
     | E | 18.4 | 18 | 24 496 | 1.75 | 0.47 | 2 Cycles bakes (albedo + lighting) |
     | F |  0.8 | 30 | 24 052 | 14.33 | 12.71 | nothing — materials are shared |
     | G |  4.1 | 18 | 20 656 | 2.46 | 1.51 | 2 Cycles bakes (albedo + AO) |
     | H |  2.5 | 20 | 27 174 | 2.71 | 1.30 | 1 Cycles bake; atlases are one-off |

     F's 0.8s/tile is the cheapest authoring in the set and the most expensive DOWNLOAD
     by 5x; E and G buy their look with a bake that is paid again for every tile of a
     real world map.  H is the only one whose extra cost is a one-time asset (two
     procedural atlases) rather than a per-tile process.

149. **`veg_` has to be a SEPARATE MESH from the trunks.**  The runtime's new `veg_`
     rule (`5e2d7fc`) removes a mesh from `collide` entirely — no standing AND no
     blocking.  Round 1 baked trunks and canopies into one `trees` object, so naming it
     `veg_` would have made whole trees walk-through.  Round 2 splits every style into
     `tree_trunks` (solid) + `veg_canopy` (never standable), and H adds `veg_meadow`
     and `veg_hedge`.  All four variants verified: spawn scan lands on `walk_road` at
     runtime (4.00, 11.78, -7.87) with the terrain 0.21u beneath, in every style.

150. **`boat_tar` is a parametric clinker shell, not a modelled asset.**  Half-beam
     `sin(pi*s^0.78)^0.62` maxed against a transom stub gives a sharp stem and a flat
     stern from one expression; each strake is a quad ribbon whose outer edge bulges
     `+0.042u` at its lower seam and fairs to zero at its upper, which is what makes the
     lap shadows read.  Only the top three strakes get an inner skin (nothing else is
     ever visible over the floorboards).  4.6 x 1.62u — a workboat beside a 1.45u
     character, honest to the Boatyard's hero hull.  The rig is the ONE per-style
     variable: E furled sail, F mast + standing rigging, G bare with oars stowed,
     H canopy hoops + tarp.  Renamed once and the future shared-library asset drops in.

## Overworld ROUND 3 findings (style F2 — zones + terrain treatment + trees,
## `tools/overworld3_*.py`)

Round 2 (`18efaee`) put four naturalistic branches of style D on the shared valley
tile and the user picked **F — PBR miniature**, while naming two things they did
not want: *regular sharp triangles*, and *every tree shipped so far*.  Round 3 is F
plus a **terrain zone system**, plus fixes for those two.  It re-authors nothing:
`overworld_lib.Field`, `overworld_build.build_base`/`dusk_rig`, `overworld2_lib`'s
boat + dock + mooring basin and `overworld2_build.pbr_mat` are all imported.

151. **A zone grid is the cheapest thing in the build, and that is the argument for
     having one.**  96 x 72 cells of 1.25u over the whole tile derive in **0.01s**
     — 0.5% of a 2.1s tile — because every rule is already a field the blockout
     computed for its own reasons: slope and local relief percentiles give crag,
     the analytic river and the round-2 basin give water, the road polyline
     buffered to 1.9u gives road, and one coherent value-noise field gives forest.
     Encoded run-length per row the whole encounter geography is **5.3 kB**.  There
     was never a budget question here; the only real decisions are taxonomy.

152. **Store the grid in RUNTIME axes, not Blender's.**  Blender is +Y north, the
     runtime is +Z south (`runtime z = -blender y`).  A debug format that needs a
     mental axis flip is a debug format that gets misread, and `SIM.zone(x, z)` is
     what game code will actually call — so the json is in runtime axes and the
     BUILD does the flipping, once, where it can be tested.

153. **`types[]` IS the registry and cells hold INDICES, which is what makes the
     format extensible for free.**  Appending `"swamp"` upstream needs no schema
     change, no migration and not one line of runtime code — and shipping a
     parallel `colors[]` means the debug overlay does not need one either.  The
     price is that the array may never be REORDERED: an index is a permanent
     contract the moment a zones.json ships.  Documented in the file itself under
     `_doc`, because a format documented somewhere else is a format that drifts.

154. **Derive from landform, then let FICTION overrule it with a stamp layer.**  No
     slope threshold can express "the encounter table must not roll a wolf inside
     the village green".  A list of `{type, ellipse|polygon}` applied LAST, after
     the derivation, covers 534 of 6912 cells here and keeps the two settlements
     safe — and it is the same mechanism a quest will later use to make one
     clearing dangerous.

155. **ZONE DRIVES THE LOOK THROUGH ITS SMOOTHED WEIGHT FIELDS, NEVER THROUGH THE
     CELL INDEX.**  The first F2 pass forced terrain material slots off `zg.idx`
     and the road grew a blocky stair-stepped apron while the crag grew a square
     grass/rock seam: a 1.25u grid read DISCRETELY wears its cells in the art.  The
     box-filtered `crag_w` / `forest_w` fields carry the same information with a
     smooth contour.  Discrete grid for gameplay, continuous field for pixels.

156. **Three things together kill a "regular sharp triangles" read, and it takes
     all three.**  (1) the triangulation DIAGONAL hashed per quad, not alternated —
     round 1's herringbone `(i + j) % 2` is a perfectly regular chevron and any
     shading discontinuity at all makes the eye read the lattice instead of the
     land; (2) POLAR xy jitter (hashed angle x hashed radius) instead of two
     independent uniforms, which still leaves the grid legible along both axes;
     (3) crag quads fanned around a jittered CENTRE VERTEX.  A centre fan is
     crack-free by construction — the quad's own four boundary edges are untouched,
     so there is never a T-junction against a smooth neighbour — which makes it the
     cheapest possible way to be denser AND irregular exactly where it is wanted
     (23% of quads, +3200 tris).

157. **Sharpness is a ZONE PROPERTY, and the border blend is a THRESHOLD GAP.**
     Smooth-shaded everywhere; ridged-multifractal displacement scaled by
     `crag_w**1.35`; facets go flat only above weight 0.62 while the fan starts at
     0.45.  That 0.45–0.62 band IS the 1–2 cell blend the brief asked for: dense
     and displaced but still smooth, so meadow flows into rock instead of switching.
     Use a RIDGED fold (`1 - |2v-1|`, squared) not a plain fbm — fbm displacement
     makes lumps, and lumps are not crag.

158. **One material per FACE means every material boundary is a zigzag, so put the
     soft boundaries in COLOR_0 instead.**  Round 2's per-face argmax is why F's
     road wore a sawtooth: the chase camera looks straight down at the road apron,
     which is the one boundary that cannot afford to follow the triangulation.  F2
     drops the dirt SLOT from the terrain entirely and paints the apron as a
     per-vertex colour gradient (smooth by construction), hash-dithers the one
     remaining grass/rock seam so it reads as weathering rather than as a bug, and
     ships three fewer images for it.

159. **A walk ribbon floating 0.09u is pierced by its own hillside the moment the
     ground is touched.**  The ribbon is a LINEAR interpolation along the road
     polyline; the terrain is a BILINEAR interpolation of a nearest-index grade.
     They disagree by centimetres, and every terrain triangle that lands high shows
     as a sawtooth through the road.  Three fixes, all needed: notch the corridor
     0.16u (invisible, and a used road IS lower than its field), keep a FLAT_PATHS
     corridor list for ribbons with no analytic distance field of their own (the
     dock spur — which is why `build_dock` now runs BEFORE the terrain, purely to
     hand over its jetty root), and a lift-only `conform_ribbon()` safety net for
     the last few centimetres.  `overworld3_verify.py` gates it per ribbon;
     `walk_bridge` is excluded by name because its piers are cubes driven into the
     bank on purpose.

160. **`bmesh.ops.create_icosphere` INVALIDATES every existing BMVert proxy;
     BMFace proxies survive.**  So the `x in set(bm.faces)` idiom rounds 1 and 2
     use for CLASS TAGGING is safe (verified: cube, prism, ico, cube tags correctly
     — this is not a latent bug in shipped work), but the same idiom on VERTS says
     "new" about every vertex in the mesh.  A canopy sculpt built that way
     re-displaced all 400 earlier lobes relative to each new centre and the tile
     flew apart to 4000u.  `create_cube` does NOT invalidate, which is exactly why
     this hid: it reproduces only once an `ico()` is in the accumulation.  Count +
     `ensure_lookup_table()` + slice `bm.verts[n0:]` is exact.

161. **Per-tile build cost is measured in ONE-ELEMENT NUMPY CALLS.**  6.8s of the
     first 9.9s F2 build was `height()` invoked 8673 times on single-element arrays
     — once per crag centre vertex, once per overlay cell — each one re-running the
     analytic river distance over 601 points.  Batching them into one vectorised
     call each took the tile from 9.3s to 2.1s and changed nothing about the
     output.  Same for the per-loop UV and COLOR_0 writes: build a per-loop face
     index with `np.repeat(arange(nfaces), loop_totals)` once and `foreach_set` the
     whole array.

162. **Make the ground height ONE analytic function and every consumer agrees for
     free.**  `height() = F.sample + crag_disp + road_notch` is called by the
     terrain mesh, the tree feet, the shrub feet, the marker plinths, the ribbon
     conform and the QA overlay.  Six consumers, no hand placement, and nothing can
     drift — the round-2 pool-height lesson (finding 141) applied to relief.  The
     corollary: the guard list has to be module state, not a parameter, or one
     consumer will eventually be called without it.

163. **THE TREE VERDICT.  A canopy is MASS, and only geometry carries mass.**  Four
     constructions, side by side on one hillside, markers counting 1–4:
     (a) chunky sculpted mesh lobes + procedural albedo/normal — **the pick**: a
     solid silhouette at every distance, nothing to sort, and it is the only one
     that survives a steep aerial follow camera; (c) hybrid mesh core + card fringe
     on the lower outer band only — **second, and worth it** where a stand needs its
     edge broken; (d) recursive branch skeleton with clustered leaf lobes — the most
     characterful and the right answer for a hero/foreground tree, at ~2x the tris;
     (b) dense alpha-MASK card shells — **still the weakest even done properly**.
     32–43 cards over five shells stops reading as flakes and starts reading as a
     tree, which is a real improvement on round 2's six, but every card the camera
     looks DOWN on is seen flat, and this world is played through a high aerial
     cam.  (b) is therefore in the line-up and nowhere else on the tile.

164. **The two ways a foliage card fails are opposites, and the atlas has to dodge
     both.**  Round 2's cluster faded out toward the rim and read as litter
     (finding 145).  Packing the mass right out to the rim instead — `rand**0.34`
     over a near-cell-filling ellipse — reads as a hard-edged SHEET, which is worse
     under a steep camera.  What works: dense core (`rand**0.5`), a lobed rim, and
     ~16% of leaves thrown PAST the nominal radius so the silhouette is made of
     individual leaves rather than of the card's outline.

165. **A 162-vertex lobe cannot resolve a third harmonic.**  The first sculpt
     carried terms at 0.30 / 0.20 / 0.13; smooth shading over sub-facet deformation
     produced broad creased plates and the crowns read as cabbages.  Low-order
     terms only (0.31 / 0.17 / 0.06): the SILHOUETTE is what has to vary, and leaf
     detail is the normal map's job.

166. **Generate the "baked" maps in numpy.**  Canopy albedo + normal, bark albedo +
     normal and the leaf-mass alpha atlas are all procedural, tileable and written
     once to `tools/textures/overworld/veg3_*` — so F's near-zero per-tile cost
     survives having four times the vegetation, exactly like round 2's card atlases
     (finding 148).  A Cycles bake here would have been ~5s of every future tile
     forever, for maps that never change.

167. **The debug overlay has to clear the RIBBONS, not the ground.**  The runtime
     tint samples the LOWEST floor under each grid node (so a node landing on a
     trunk cannot spike a whole cell), which puts it BELOW a road that floats 0.09u
     over a corridor notched 0.16u down.  At 0.12u lift the road drew straight
     through the tint; 0.34u is the number.  7081 down-rays, one per node shared by
     the four cells around it, build the whole overlay in 62ms.

168. **F2's real cost is DOWNLOAD, not authoring.**  2.1s/tile against F's 0.8s,
     but 22.50 MB against 14.33 MB — tris double (crag fans + real trees) and
     texture goes 12.7 -> 17.0 MB.  The authoring number is what covers a world and
     it is still trivial; the download number is the one that will eventually need a
     decision, and the levers are known and unused: drop the roughness maps for
     flat factors (~-4 MB), halve the normal maps to 512 (~-5 MB).  Neither is an
     art change, so neither should be spent before the user has picked a look.

---

## Shelf tier findings (the west branch's SECOND district — `tools/shelf_*.py`)

The shop street one tier below the gate (`p-shelf-w` + `p-shelf-e`: inn, item,
weapon and armor shops, shelf-homes), built on the same branch blend under the
same additive-only protocol.  These nine were written into the Overworld ROUND 3
section with no heading of their own and read as overworld findings for it.

169. **A practicals check has to compare walking SURFACES, not hero points.**  The Shelf
     tier's first check put mid-street (35.0, 7.0) against the accepted Boatyard's hero aim
     point and reported 2.8x, then 1.9x after thinning.  Both numbers were mostly artefact:
     the mid-street probe sits 2.5 m from a hung lantern and the Boatyard's aim point 4.4 m
     from its nearest one, so the ratio was measuring LAMP PROXIMITY, not district exposure.
     Two point probes cannot be like-for-like across districts with different lamp spacings.
     The method that works is master_walk_qa.py's own sampling, run on both districts by one
     piece of code: a down-ray on a 0.75 m grid, accepted only where the first hit is a
     walk_/bar_ mesh, probed 0.60 m above the hit, up-facing, every lamp included, ~100
     probes a side.  Same rig, same code, same surface.  On that method the tier read 1.25x
     before thinning and 1.005x after — and the MEAN is what gates (district exposure) while
     the MAX is reported separately, because a street whose mean is right and whose peaks are
     double the reference's is blowing out material in pools.

170. **When the lamp's wattage is canon, DENSITY is the handle — and it is solvable.**  The
     680 W practical lights four districts and is not renegotiable inside one of them, so the
     Shelf tier solves spacing instead of choosing a count.  Shopfront lamps go first (a shop
     lights its own door is the one lantern a player can explain), then a strung lamp is hung
     only where no shopfront lamp is within LANT_MIN_SEP of that stretch.  Measured against
     the accepted Boatyard's surface: 4 strung = 1.25x, 3 strung (2.6 m) = 1.14x, 2 strung
     (3.0 m) = 1.005x.  3.0 m drops exactly the two redundant lamps — one 2.29 m from the item
     shop's bracket, one 1.67 m from home-b's — and keeps the two over genuinely unlit
     stretches.  On a 3 m street a strung lamp 1.7 m from a bracket lamp is not atmosphere,
     it is one pool of light paid for twice.  `bracket_at()` is shared by the solver and the
     builder so the lamps that were counted are the lamps that get built.

171. **A shingle course must be THICKER than the step it rises.**  Courses tile the roof's
     depth with generous plan overlap, which makes the roof look watertight from straight
     above and hides that consecutive boxes overlapped VERTICALLY by 0.002 m — 0.055 m of
     thickness against an 0.053 m rise.  The ±0.008 m jitter that keeps tiles from looking
     machined then opened real holes.  `thick = max(thick, rise + 0.032)`, in both the gable
     builder and the monopitch.  A roof that is only watertight from directly overhead is a
     venetian blind from everywhere else.

172. **Ask what the ray got in THROUGH, not what it hit.**  A flat black plane lay across the
     armor shop's roof.  Casting the pixel (finding 104) named the soffit board; three passes
     then chased the soffit — inset it, drop it, thicken it, make it a perimeter ring — and
     each one moved the sightline without closing it, the cast simply renaming whatever was
     next inside the building (then the wall's top plate).  Meanwhile a DOWN-RAY MAP over the
     footprint said the roof was solid shingle at every point above the board the whole time,
     which is the signature of a grazing sightline through an opening somewhere else.  The
     opening: `framed_wall` stops 0.20 m under the eave and the courses start at the eave, so
     above the wall plate every roof ended in an open triangle the full depth of the building.
     ALL SEVEN buildings had a hole into the roof void.  The soffit was never the bug — and a
     soffit is a ring under the eave overhang anyway, not a slab spanning the building with an
     open cavity over it.

173. **A camera 1.15 m above the ridgeline manufactures its own defect.**  The Shelf `shops`
     shot sat at z=24.00 over ridges capped at 22.85, 17.5 m of ground distance away: 6.5 deg
     of elevation, practically IN the roof plane, looking lengthwise into the overlaps between
     courses.  It rendered a sightline no player standing on a 19.00 m street can ever have.
     Worth keeping the frame long enough to find the gables it exposed, then worth moving:
     an elevated row shot wants ~18 deg.  A QA camera that generates its own artefacts costs
     more passes than it saves.

174. **A fix inside a bare `except: pass` can fail silently — and a silent fix for a silent
     failure is the worst kind.**  shelf_shots.py set `eevee.shadow_pool_size = '4096'` to stop
     EEVEE dropping shadows silently (finding 70).  In Blender 5.1 that property is an ENUM
     whose largest member is '1024', so the assignment raised, the except swallowed it, and the
     pool stayed at the '512' it started on — for every render of every pass that believed it
     was fixed.  Set to the real ceiling, PRINT what was actually got, and print the residual:
     this tier still overflows 1024, so its EEVEE frames prove subject-visible and nothing
     about value.  If a QA setting will not take, the script has to say so.

175. **Continuity needs an A/B CONTROL RENDER, not a stale baseline.**  Diffed against
     `boatyard_v10.png` as the shot list intended, the Shelf tier's continuity frame reads
     +7.77% mean luminance and +26% at p95 — which reads exactly like a district that has
     re-lit accepted art.  It has not: the same camera, engine and samples with
     SHELF_DISTRICT's 164 objects `hide_render`'d comes back at 58.266 vs 58.255, a drift of
     -0.02%, with 97.6% of pixels within 2 levels and 0.08% beyond 8.  The +7.77% accumulated
     in the BASELINE — the gate district, Locksfoot and the render-norm exposure change all
     landed after boatyard_v10.png was made.  A stale baseline hands every earlier pass's
     drift to whoever renders next.  Keep the point-probe spill assertions (they catch a rig
     re-valuing a surface) AND render the control (it catches everything else).

176. **An awning's height belongs to the STREET, not to its shop.**  master_walk_qa's headroom
     pass flagged shelf_awning_0 at 1.985 m, 15 mm under its 2.00 m bar, because the awning was
     measured 2.14 m above its own shop's threshold while the thing walking under it walks on
     the street — and this tier's walk ribbons climb up to 0.20 m across the parcels.
     `awning_lip()` samples the footprint against the walk graph and takes whichever is higher,
     what the shop wants or walk + 2.10 m.  A no-op where no ribbon is within 0.30 m, which is
     why the market stalls did not move.

177. **The glTF gate's boundary: district-owned materials HARD-FAIL, shared kit is inherited
     debt.**  shelf_gltf_verify.py re-imports the GLB into an empty blend and finds all 17
     mat_shelf_* materials surviving (textures, emissiveFactor, and live COLOR_0 on all five
     cloth objects at mean 0.196) — and five SHARED kit materials arriving white on this
     district's objects: mat_grass (47 slots), mat_fern (28), mat_leaf_creeper (22),
     mat_leaf_autumn (22), mat_rope (3).  Those are exactly the procedural foliage ramps and
     ropes whose cure MIGRATION.md queues as a master-wide pass; four accepted districts are
     built on them and re-authoring them from inside one district would fork the kit and change
     accepted art.  So the checker fails on what the district owns and REPORTS the rest by name
     and slot count.  Reading it either of the other two ways gives you a false green or 244
     failures nobody can act on.

---

## Weave findings (in-master district #5, the MID TIER — `tools/weave_*.py`)

The first district that is neither at water level nor on the rim: it hangs on the
cliff between z 6 and z 14, directly ABOVE the Waterfront's and Locksfoot's
boardwalks and directly BELOW the Quay.  Almost everything that cost a cycle
came from being in the MIDDLE of a stack rather than at the end of one.

### The runtime's material contract

178. **A procedural material is invisible to the exporter and perfectly visible
     in Blender, so a whole town can go white without one render looking wrong.**
     The user walked townwalk and found 516 primitives shipping as default
     white.  `mat_rock` / `mat_deck` and the entire pre-Locksfoot palette are
     object-space box projection plus noise, and glTF carries neither.  The
     authoring render is not evidence: the only test is to EXPORT and RE-IMPORT
     into an empty blend (`weave_gltf_verify.py`), which reports per group
     whether `COLOR_0` arrived and — the part that matters — whether it arrived
     FLAT WHITE, which is exactly what "the vertex colour was lost" looks like
     from outside.  This district speaks only the Locksfoot kit's language
     (findings 80-82), and every object it makes goes through one `finish()` call
     that gives it `Col` + `UVMap`; a build-time assert on all 140 objects is
     cheaper than a review pass afterwards.
179. **`finish()` has to run on the FINAL joined object, not on the parts.**
     `join_meshes` round-trips through bmesh via an intermediate mesh, and a
     colour layer is not guaranteed across that.  Painting after the join also
     means the tint table is keyed by MATERIAL NAME, which is what makes a nine-
     material assembly a single call.
180. **A material datablock is invisible in a render, so an append leak can run
     for 2000 datablocks before anyone notices.**  Finding 130 caught the IMAGE
     half of the kit-append leak; the MATERIAL half was never noticed because
     `use_fake_user` keeps an unused material from ever being purged.
     `kit_load()` asks for all eight `lf_*` materials once per call, so the
     master carried **2207 material datablocks, 2000 of them unused copies**, and
     the 19 kit-derived objects used **152 datablocks for what are 8 materials**.
     Collapsed by node signature: 2207 -> 63, and the .blend went 5.95 MB ->
     3.19 MB. The cost that mattered was not size — it was that the queued
     town-wide white-material fix would have had to edit 152 datablocks, and that
     a district reusing `lf_deck` BY NAME got the unused copy.

### Lighting from inside a stack

181. **A district built ON TOP of accepted art cannot have a DOWN-FACING bounce
     card, and shrinking is not the fix — DIRECTION is.**  Eight down-facing
     cards over the Weave put **23% of the Waterfront's own fill** back onto it;
     pulling the run east and shrinking to 1/3.2 size merely moved the problem to
     Locksfoot (**17%**).  Finding 69 (shrink, do not move) is about reach; this
     is about which way the lamp points.  The tier's frontages face the gorge, so
     the cards stand just gorge-ward of them and fire back at the cliff (-y,
     horizontal).  Any accepted deck further out in y then sits BEHIND the
     emitter, where the lamp's own cosine is negative: **0.000000 W/m2 into all
     three accepted districts, by construction rather than by tuning.**  It is
     also the physically honest card — what really bounces onto a stilt frontage
     at dusk is the lit water and the far wall, both of them out in +y.
182. **Practical spill in a stilt district has to be RAY-TRACED, because
     occlusion IS the design.**  Every earlier district is one deck under an open
     sky, where line-of-sight and reality agree.  Here 8-11 m of decking, joists,
     piles and hut walls lie on nearly every sight line between the Weave's
     lanterns and Locksfoot's.  Free-space, the drying-decks lantern reads **19%**
     of Locksfoot's moorage lamp; traced, `walk_lm_drying-decks` is squarely in
     the way and the answer is **0**.  District totals: 14.0% mean / 24.1% worst
     free-space, **0.58% / 3.51% traced**.  Finding 104 in another key: cast the
     ray, do not reason about it.
183. **A line-of-sight tracer needs a SKIN at both ends or it measures the lamp's
     own hood.**  Tracing a district's own lantern down to the point 2 m beneath
     it hit that lantern's shade, scored the denominator 0.0, and reported the
     Weave as adding **34 000 000 000%**.  Start and stop the ray 0.35 m inside
     each end.  A number that absurd is a free gift; the dangerous version of
     this bug returns 8% and gets believed.
184. **Measure a neighbour's practicals where its practicals actually light
     something** (finding 118, applied to lamps instead of cameras).  At
     Locksfoot's SKY-solve point the same rig reads **51%** — arithmetic about a
     spot its own lanterns barely reach (2.7 W/m2), not a statement about its
     art.  Under its own six lanterns the same rig reads **13%** free-space and
     **0.6%** traced.
185. **The tier was the darkest built surface in the gorge and no wattage was
     missing.**  Measured, it received 35% of the accepted deck working level —
     because `wf_cliff` and `lf_cliff` are aimed at the ROCK the Weave now stands
     in front of, so the district was lit from behind its own massing.  The fix
     is a chain aimed at the frontages, solved to supply only the SHORTFALL.
     Held deliberately at 78% rather than 100%: p-westweave's own stated intent
     is "tucked under the quay's shadow ... the town's poorer corner", and a tier
     lit to the boardwalk's level stops reading as under-the-quay at all.

### Building in the middle of a walk network

186. **`bar_*` railings are canonical topology and `master_walk_qa` casts a
     down-ray over every one of their top faces — but every district's Corridor
     is built from `walk_*` only.**  That is how a hut roof came to sit 0.40 m
     over a stair rail and the cottage clipped the Lockhead path's guard.  Rails
     need their own corridor, with a SHALLOWER band: the QA's ray starts 0.90 m
     above the surface, so only that 0.90 m has to be clear over a rail top, not
     the full 2.05 m walking corridor.
187. **A search that cannot fail is not a search.**  `site_hut` looked outward
     for a clear seat and, finding none, RETURNED THE FIRST CANDIDATE ANYWAY —
     the unmoved centre, i.e. precisely the blockout seat it existed to escape.
     It did that silently for three of nine houses and the tier came out WORSE
     than the blockout it replaced: **132 blocked samples against a baseline of
     93.**  A placer must widen, then shrink, then return None and say so.
188. **The landmark blockout owns most of a tier's blocked samples, because a
     blockout is placed AT the landmark coordinate and the landmark coordinate is
     the standing pad** (finding 93, quantified).  `lm_weave-north_1` (32),
     `lm_pilot-cluster_1` (16), `lm_weave-huts_1` (14) and their neighbours were
     **62 of the region's 93**.  Replacing a blockout is therefore usually a walk-
     QA IMPROVEMENT, and if it is not, the replacement is being placed the same
     careless way.
189. **A prop cannot stand on a walk ribbon, so a district whose decks ARE its
     walks needs APRONS.**  The Corridor test that keeps props out of walking
     lines rejects every prop standing on the district's own deck, because the
     deck is the walk.  The dye pots, the clutter, the fish racks and the whole
     North Landing dressing came out at **zero, and the log said "x0" four times
     in a row**.  The fix is the district's own planking OUTBOARD of the ribbon —
     a filled landmark disc is corridor all the way to its rim (manifest 35), and
     a working platform would really be bigger than its standing pad anyway.
190. **Decking may not be laid OVER a walk either.**  `below_walk` tolerates a
     plank 0.16 m under a walk because that is how decking meets its own ribbon;
     at the head of a flight the same +0.36 m generous offset overhangs the tread
     BELOW, and that tread's own down-ray then lands on the plank.  Anything
     walkable in the metre beneath a plank is someone else's surface.
191. **A pile is tested along its LENGTH.**  The weave-huts ribbons stand a metre
     over the drying decks and their piles came down inside that disc.  Finding
     113 for a vertical member rather than a tall one.
192. **A PLAN overlap with a neighbour's structure cannot be fixed by adjusting
     how deep the foundation goes.**  Making the undercroft land on Locksfoot's
     `lf_stage_shack` instead of passing through it only made the masonry WRAP it
     — one offender became two.  Neighbouring structures are declared as explicit
     keep-out rectangles (manifest 97) and the house slides along the contour.

### The user's steer, and what it cost

193. **"Houses on stilts" is what a district gets when the pads are the only
     thing it measures.**  Every `walk_pad_*` in this tier sits on the FLAT part
     of the terrain, 6-8 m above the rock; the rock reaches the pad's own height
     only 2-7 m INLAND (measured: the cliff falls ~2.5 m per metre of y between
     y=17 and y=19, then flattens to z~1.0 beyond y=21).  So a house AT its pad
     must float and a house 3-7 m inland sits on rock, with a gallery spanning
     the difference.  The first pass built at the pads and the user, walking it
     live, called it "houses floating in mid-air on forests of stilts".  Probe the
     TERRAIN before deciding what a district is standing on.
194. **The arrival level is the PAD level.**  Centring a house's two half-levels
     on its floor lifts the upper volume ~0.5 m, and under the Quay — which runs
     at z 14.24 over Westweave, leaving 4 m of headroom — that half metre was the
     whole difference between a house and no house.  The upper volume sits AT the
     pad and the second steps down from it.
195. **Under a tight ceiling, flatten the PITCH before giving up on the house.**
     Clamping only wall height skipped eight of nine houses; letting the roof rise
     shrink with the available headroom (and a house tucked under the Quay's own
     switchback stair) built all nine.  A lower house is a house.
196. **A relief valve that can run away will.**  The volume fitter marched a
     blocked volume's river edge back and its inland edge forward; unbounded, the
     inland branch walked whole houses **3.4 m river-ward off their rock seat** —
     the exact opposite of the steer it was serving.  Cap the direction that
     undoes your intent, and slide ALONG the contour instead.
197. **Palette by measurement, not by eye.**  Told the houses read "too dark and
     out of key", the useful move was not to guess brighter but to measure the
     accepted districts' own RENDERED frames: warm painted timber lands at sRGB
     #74481d..#be845b, and Locksfoot — lit by this tier's own rig — at #b17853.
     This tier receives 78% of that key, so its albedos have to sit ABOVE the
     kit's to land in the same family.  Reading the material datablocks instead
     is useless: a box-projected AO-multiplied material reports 0.5 grey at its
     Base Color input, which says nothing about what it renders as.
198. **A hero kit asset may not fit its site, and the honest resolution can be
     that a walkable platform IS the pad's decking.**  The kit cottage is
     7.5 x 8.4 m; p-cottage is 9 m wide with its standing pad in the middle, the
     Lockhead path descending across the west half ABOVE the cottage's own floor,
     and the basin steps leaving from the east.  A balcony is a walkable
     platform: it lands 85 mm under the walk top like every other deck in the
     district, the down-ray still hits canonical topology, and the player
     standing on `walk_pad_keepers-cottage` is standing where the map says supper
     is served.
199. **When constraints pull against each other, SCORE and search — and get the
     weights right.**  The cottage has three: corridor, parcel, and a buttress
     that rises to z 14.8 and buries a roof pushed inland.  Weighted equally the
     search bought a seat **21 samples out of parcel** to save a few buried-roof
     samples.  Burial is cheap (a cliff cottage cut into the rock is the look the
     map asks for); corridor and parcel are not.  Reweighted: **0 corridor, 0 out
     of parcel, 21 buried of 49.**
200. **Two more of the finding-117 family, both found by re-running the pass
     twice.**  (a) `hide_render` set by a PREVIOUS run of this pass made the
     second run deck nothing at all, while the clear-out had already removed the
     first run's planks — 62 invisible, undecked ribbons.  A flag a pass sets on
     objects it does not own is not evidence about someone else's district.
     (b) the fish-dock ladder was derived FROM the blockout it deletes, so the
     second run produced no ladder and said nothing.  **Run every district script
     twice before believing it.**
201. **A drying line whose panels are dropped on conflict hangs no panels.**  The
     Weave's entire identity is its laundry; every run crosses a deck somewhere,
     so drop-on-conflict emptied the district (0 panels from 17 runs) while the
     log happily reported the runs.  SIZE the panel to the headroom that exists
     — 56 panels on 8 runs — and only skip when there is genuinely under 0.28 m.

---

## West-branch MERGE findings (the first branch merge — `tools/master_west_merge.py`)

The GATE and SHELF tiers came home together: 17 blockout shells deleted, two
collections appended, 310 objects and 29 materials landed in the live master.
Almost everything that cost a cycle was about the SEAM between two files rather
than about either district's art — which is the whole point of the protocol, and
also where its remaining holes are.

202. **A deletion manifest's bboxes were recorded from live VERTICES, so a merge
     that verifies with `ob.bound_box` fails on the first rotated object.**  The
     manifests carry a vertex count and a world bbox per shell precisely so the
     custodian can prove it is deleting the object that was recorded and not a
     namesake.  Verifying with `matrix_world @ bound_box` reported
     `lm_gatehouse_roof` as 7.00 x 7.00 against a recorded 4.454 x 4.454 and
     stopped the merge dead: `bound_box` is only refreshed by a depsgraph
     evaluation, which never happens in a headless session (`boatyard_lib.
     world_bbox` exists for exactly this and says so in its docstring).  Verify
     with the same helper the recorder used, or the check is testing Blender's
     cache instead of the geometry.
203. **Reconcile appended IMAGES before appended MATERIALS, and identify an image
     by the FILE IT RESOLVES TO.**  The append produced 32 duplicate materials and
     44 duplicate images; collapsing materials first left three "divergent"
     (`mat_deck.001`, `mat_shingle_mossy.001/.002`) because a material's node
     signature names its image datablock, and `mat_deck` and `mat_deck.001` were
     still pointing at two different datablocks for one JPEG.  The datablocks
     differed only in how the path was SPELLED — the master holds a few textures
     absolute, the branch holds the same file as `//../textures/...` — and
     `bpy.path.abspath` expands `//` without collapsing `..`, so even the absolute
     forms compared unequal.  `os.path.realpath(bpy.path.abspath(...))`, images
     first, and all 76 duplicates collapse with 0 divergent.  Three false
     divergences is the good outcome; the bad one is remapping by name alone and
     never learning that two kits had drifted.
204. **`wm.append` parks an appended collection under an "Appended Data" wrapper.**
     Two of them, one per call, both linked at the scene root, each holding the
     real district collection as a child — so the outliner gains a level that no
     other district in the master has and every `scene.collection.children` walk
     sees the wrapper instead of `GATE_DISTRICT`.  Unwrap and remove them as part
     of the append step.  (`do_reuse_local_id=True` would also have avoided the
     duplicate datablocks entirely — deliberately not used, because then finding
     203's kit divergence would have been reused away silently instead of
     reported.)
205. **PROBE for outward references BEFORE appending, because the census can only
     tell you afterwards.**  Finding 180's leak is invisible in every render, and a
     count that comes out wrong still leaves you guessing which reference dragged
     what.  One read-only pass over the two collections — parent, modifier object,
     constraint target, animation data, per-object material and image use — said
     0 outward references, which is what made "+618 datablocks, 0 stray objects"
     a prediction rather than a discovery.
206. **Manifest-51 render-hiding must be scoped to the MAP's parcel bounds, not to
     the branch's own shot filters.**  A branch cannot set `hide_render` on the
     master's ribbons (finding 90), so its shot scripts hide them at render time
     with a deliberately loose box — `shelf_shots.py` uses x 0..60, y -2..20,
     z > 13, which is fine for a frame and catastrophic as a saved flag: it
     reaches into `p-quay-mkt`, whose tier is still unbuilt gray and whose ribbons
     are therefore its ONLY visible paths.  Hiding by parcel bounds
     (p-gate + p-shelf-w + p-shelf-e, 0.6 m pad) hid 118 and left the market's
     alone.  A render filter is scaffolding; a saved flag is topology dressing.
207. **A district built BEFORE a gate existed has never passed it, and the merge is
     where that comes due.**  The glTF-survival gate landed with the Weave, after
     the gate tier was built and reviewed, so there is no `gate_gltf_verify.py` and
     nobody had ever round-tripped `mat_gate_*`.  Six of them — the whole
     `mat_gate_flag_*` bunting set — arrive WHITE: `gate_build.cloth()` drives base
     colour through an object-space noise weave AND terminates in a
     Diffuse/Translucent MixShader with no Principled BSDF at all, so the exporter
     has nothing to read twice over.  The shelf tier had already diagnosed this in
     prose (its `vcol_mat` docstring names `gate_build.cloth()`) and solved it for
     its own cloth with COLOR_0 at mean 0.196 — but a lesson written next to the
     fixed district does not fix the broken one.  REPORTED, not fixed: the cure
     costs the pennants their translucency, which is an art call, and it belongs to
     the queued master-wide survivability pass.  The general rule: when a gate is
     ratified, the districts already on the shelf owe it a back-fill pass.
208. **A MERGE is where two branch districts' spill ADDS, and a point probe
     under-reports what a frame sees.**  Each pass measured its own light against
     the accepted Boatyard hero alone and passed: the gate asserted its approach
     cards at 0.8% of the yard's irradiance AT A POINT, and the shelf's control
     render came back -0.02% — measured on the branch, where the gate was already
     present and therefore already in the baseline.  Merged, the same camera moves
     **+1.94%**, and a five-config A/B in one session attributes it: +2.09% is new
     LIGHT, -0.16% is new geometry (mild occlusion), gate lamps +1.46%, shelf lamps
     +0.57%.  The gate's own assertion was not wrong, it was narrow — a shadowless
     733 W card with a 75 m cutoff reaches 24 m down the gorge, and the frame mean
     includes the cliff faces and water that face it better than the yard's aim
     point does.  Two candidate cures, both with a cost the gate pass documented:
     shadows on the cards (EEVEE's shadow pool already overflows, finding 174) or a
     ~30 m cutoff (the cutoff sphere cut a visible edge across the promontory at
     34 m).  A concurrent-branch protocol needs a spill budget that is measured
     ON THE FRAME and shared between the branches, not asserted per district.
209. **A LEVEL from the map is a WORLD z; a vertex coordinate is not.**
     `pool-downstream` read -2.80 in the master against the map's -3.80 because
     `locksfoot_build.py` wrote the world level straight into `v.co.z` on an object
     the town generator ships with its origin at z -1.8 and a 0.2 z SCALE — so the
     surface landed at `origin + 0.2 * level`.  The compounding half was the
     idempotence trick: "split the mesh on its OWN mid-plane so a re-run is safe"
     re-splits values that have already been moved, so each run walked the slab
     further until it reached a fixed point as a ZERO-THICKNESS sheet.  Everything
     else in the district was built for the true -3.80 (tail-race boils at -3.90,
     far-bank toe under -3.80, wheels axled at -1.55 to span to -3.805), so the
     whole tailwater assembly was a metre under water and no render said so.  The
     cure is to stop straddling two spaces: `boatyard_lib.reseat_slab` keeps the
     plan extent, drops the object onto an IDENTITY transform and writes world
     coordinates into the mesh — the form `water_pool-mid` already had.  Absolute
     target, one space, idempotent from any starting state including a broken one.
210. **Concurrent passes collide on finding numbers because each claims from the
     max it can see when it STARTS, and an ambiguous citation is worse than a
     duplicate heading.**  Five collisions had accumulated, not one: 79 (Waterfront
     / Locksfoot PREP), 121-131 (Gate POLISH / Overworld ROUND 2) and 139-162
     (Overworld ROUND 3 + Shelf / Weave) — 36 numbers used twice, and the Gate
     POLISH block sat physically BEFORE Locksfoot's 104-120 so the document did not
     even read in ascending order.  The damage was never the duplicate headings; it
     was that "finding 131" meant the deletions-manifest lesson to the gate and
     shelf agents and the alpha-atlas lesson to the overworld agents, so 36 numbers
     of citation had to be resolved by READING each one.  Renumbered by file order
     (see the ledger below).  Two mechanical notes for whoever does this next: the
     Shelf tier's nine findings had been appended into the Overworld ROUND 3 section
     with no heading of their own, which is half of why they read as overworld
     findings; and the Overworld ROUND 3 heading is WRAPPED across two `## ` lines,
     so a section tracker that resets on every `## ` silently skipped that entire
     block and the duplicate-check was the only thing that caught it.  Claim your
     range from the ledger, and write it back when you are done.

---

## MATERIAL-SURVIVABILITY findings (master-wide cure, 2026-07-30)

211. **The glTF exporter DOES traverse Mix Shaders, so a procedural material behind
     one needs a RELINK, not a rewrite — and the failure you can already see cannot
     tell you that.**  Every foliage material is `ColorRamp -> Principled.BaseColor`
     AND `ColorRamp -> Translucent.Color`, the two mixed by a Mix Shader that feeds
     the output.  Two hypotheses explain the white export equally well: (H1) the
     exporter finds the Principled through the mix but cannot evaluate a ColorRamp,
     or (H2) it never finds a Principled at all because the output is a Mix Shader.
     **Both predict exactly the observed result**, so the 760-slot measurement —
     however carefully taken — could not discriminate between them, and they demand
     opposite cures: H1 wants one link moved, H2 wants the Principled promoted to
     the output, which costs the foliage its translucent backlit component and
     would have failed the +-0.5% render gate on every frame with a leaf in it.
     One 40-object round trip settled it in a minute: relinking `mat_grass` alone
     brought COLOR_0 back at mean 0.129, std 0.055, gradient intact.  H1.  The
     general rule: when two mechanisms predict the same symptom, no amount of
     measuring the symptom chooses between them — build the smallest experiment
     whose OUTCOMES differ.
212. **A material with no Principled BSDF can be made to export without changing the
     render at all: nest its existing mix at Mix-Shader factor 0 against a proxy
     Principled.**  The ten bunting cloths and `mat_darkfall` terminate in
     `MixShader(Diffuse, Translucent|Glossy)`; a bare Diffuse BSDF is not a shader
     glTF export understands, which is why `mat_flag_red` arrives white even though
     its Diffuse colour is already the right colour sitting in the file.  The
     obvious cure is to promote a Principled to the output, and that is what the
     brief expected to cost the pennants their translucency (finding 207).  It does
     not have to: factor 0 on an outer mix renders branch A only, so EEVEE is
     untouched, while the exporter walks the tree (finding 211), finds the
     Principled and writes a real `baseColorFactor`.  The cost is different and
     worth naming honestly — **the colour now exists in two places and can drift in
     one of them** — so the proxy node is LABELLED as an export proxy in the tree,
     and the town's four flat flags read their colour out of their own Diffuse node
     at cure time rather than repeating it as a literal in the script.
213. **Bake EMIT of the albedo socket, not DIFFUSE/COLOR of the material.**  The
     canon says "bake the procedural albedo", and Cycles has a diffuse-colour pass
     that sounds exactly right.  It is wrong here: these trees mix Translucent and
     Transparent shaders into the surface, so a diffuse-colour pass folds the leaf
     CUTOUT and the translucency into the albedo it is supposed to be isolating —
     leaves come back darkened wherever the cutout is transparent, which is a
     shadow of the mask baked into the colour.  Temporarily rewiring the albedo
     socket alone into an Emission and baking EMIT at 1 sample is exact, needs
     neither UVs nor lighting, and is precisely what the VertexColor node has to
     reproduce.
214. **A district-scoped audit under-reports a SHARED material by construction, so
     the handed-down white list was a fraction of the real one.**  The list this
     pass inherited read `mat_grass` 47 slots, `mat_fern` 28, `mat_leaf_creeper` 22,
     `mat_leaf_autumn` 22, `mat_rope` 3 — accurate for the shelf tier's own objects
     and off by ~5x town-wide (241 / 147 / 96 / 167 / 48).  Worse, a district audit
     cannot see a material it does not use: the town-wide scan turned up
     `mat_leaf_autumn_far` (40 slots) and the FOUR `mat_flag_*` cloths on
     `bunting_0`/`bunting_1` that no list mentioned — the merge custodian had found
     the gate's six and there were ten.  When the cure is master-wide, re-scan
     master-wide; inherited lists are for orientation, not for scope.
215. **A static "will this export white?" scan OVER-reports, and the round trip is
     the only authority.**  A node-graph heuristic asking "is there a Principled
     with a non-white unlinked base colour?" flags every bare-Emission material —
     `mat_lantern_glass` (33 slots), `mat_embers`, `mat_gate_window`,
     `mat_lockhouse_glass` — because structurally they look exactly like the broken
     Diffuse-only cloths: no Principled, nothing for the exporter to read.  But
     glTF export DOES support an Emission node, and all 36 slots arrive correctly.
     The static scan said 802 slots across 27 materials; the round trip said 760
     across 23, and the 42-slot difference was entirely work that did not need
     doing.  Scan to find CANDIDATES, round-trip to decide.
216. **A bake is a measurement, so it also settles questions about whether the
     procedural detail was ever real.**  `mat_rope`'s albedo is a UV wave texture —
     and 47 of its 48 objects have no `UVMap` at all, so what Blender renders today
     is already a flat constant and the fibre banding the node graph promises exists
     on exactly one rope in the town.  This looked like it needed an art decision
     (bake the bands, or assign a flat brown?) and needed none: the EMIT bake
     captures whatever the chain actually evaluates to, degenerate UVs included, so
     the cure reproduces the CURRENT render either way, and the per-object `within`
     std in the pass report says which of the two it turned out to be.  Do not
     adjudicate what you can measure.
217. **Baking needs render-enabled objects, and `hide_render` is topology dressing
     (findings 51, 206).**  Cycles refuses to bake an object that is not enabled for
     rendering, and 5 of the 743 cured objects are render-hidden — alongside the 118
     walk/bar ribbons the west merge hid by parcel bounds, which one careless
     unhide-everything would have silently restored across the whole town and put
     collision ribbons back into every future frame.  Capture
     `hide_render`/`hide_viewport`/eye per object, clear them only for the bake set,
     restore all three afterwards and ASSERT the restore.  The same discipline
     applies to the render engine: the bake needs Cycles, the render norm is EEVEE,
     and this script saves the file.

---

## NUMBERING LEDGER — read this before you add a finding

### NEXT FREE FINDING NUMBER: **218**

Findings are numbered ONCE, in file order, and are never renumbered again except
to repair a collision.  A pass CLAIMS its range here before it writes, so a
concurrent pass cannot take the same numbers (finding 210).  Numbers 9 and 17 are
historical gaps and mean nothing.

Renumbering of 2026-07-30 (west-branch merge custodian) — old -> new, by section:

| section (in file order)          | old       | new       |
|----------------------------------|-----------|-----------|
| Probe .. Waterfront              | 1-79      | unchanged |
| Locksfoot PREP findings          | 79-88     | 80-89     |
| Gate Approach findings           | 89-103    | 90-104    |
| Gate Approach POLISH findings    | 121-131   | 105-115   |
| Locksfoot findings               | 104-120   | 116-132   |
| Overworld ROUND 2 findings       | 121-138   | 133-150   |
| Overworld ROUND 3 findings       | 139-156   | 151-168   |
| Shelf tier findings              | 157-165   | 169-177   |
| Weave findings                   | 139-162   | 178-201   |
| West-branch MERGE findings       | (new)     | 202-210   |
| Material-SURVIVABILITY findings  | (new)     | 211-217   |

Waterfront's 79 ("a district must register its assemblies with the audit") KEPT
79; Locksfoot PREP's 79 ("kitlib cannot ship through glTF") became 80.  144
cross-reference lines across 24 files were rewritten to match, each resolved
against the numbering ERA of the file that wrote it — the shelf and gate scripts
mean the Gate POLISH block by 121-131, the overworld scripts mean Overworld
ROUND 2, and only the weave scripts mean the Weave block.  The renumbering is
reproducible: `python3 tools/manifest_renumber.py` (dry run) prints every edit
with the headline of the finding it now points at.
