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

## Gate Approach findings (district #3, and the FIRST branch district — `tools/gate_*.py`)

The gate tier is the clifftop shelf where Dellhollow meets the outside world:
Porters' Yard (x~6), Gatehouse (x~11.3), Valley Gate (x~16.7, the town's only land
entrance) and the Cargo Winch head (x~27.3), all at z~24 with the gorge 24 m below.
It is also the first district built on a BRANCH COPY of the master
(`dellhollow-master-gate-branch.blend`) while another agent held the live master,
so half of what it cost is about the protocol rather than the art.

89. **A branch district cannot render-hide the master's ribbons.** Manifest 51's
    `hide_render = True` on decked-over `walk_*` meshes is an in-master move: a
    branch merges by DELETING the manifest's names and APPENDING the district
    collection, so a flag set on a master-owned object is simply not carried.
    Two consequences. The branch's paving has to sit visibly under the walk
    surface anyway (50 mm here) so the QA's down-ray still lands on canonical
    topology, and the review renders have to hide the ribbons AT RENDER TIME and
    never save (`gate_shots.py`) or every judgement is made on gray blockout
    tape. The merge custodian applies the render-hiding town-wide, after.
90. **A tier that already has buildings under it can only carry a PLATE.** East of
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
91. **A walk BELOW the district is a disjunction, not a ceiling.** Ground may lie
    under it (terraced) or clear it by the full 2.0 m corridor — never inside the
    band between. `clamp_walks` treats every walk as a ceiling, which is right for
    a district with nothing beneath it and catastrophic for one built on top of
    the town. The test is three lines: `if lo < h < zt + CORRIDOR_H + d*0.6: h = lo`.
92. **A landmark's interaction PAD is where the player stands, not where the
    machine goes.** The Cargo Winch head was built on `walk_pad_winch-head` —
    32 blocked down-ray samples and 36 headroom samples, the largest single
    failure of the pass, and it was the most obvious placement in the district.
    Rebuilt as a derrick standing SOUTH of the pad, with the boom carried over the
    corridor at 3.4 m and the sheave block hung outside it. Every landmark has a
    2.6 x 2.6 m pad; read it before placing the landmark's own art.
93. **Read the neighbour's terminus off its geometry, never assume it.** The
    Waterfront's `cargo_winch_foot` already carries its hoist rope up to
    (28.70, 10.04, 25.03) — 24 m above the quay and inside the gate parcel. So the
    gate's rim had to be pulled back to y=9.95 there (or the rope would come out of
    the ground), and the new sheave is hung 0.42 m above the existing terminus so
    the two ropes meet without a vertex of accepted art being touched. Three lines
    of `max(P, key=z)` beat any amount of measuring off a screenshot.
94. **A flat Principled colour is not a dark surface, it is an untextured one.**
    v1 gave the ground, road and masonry flat colours at 0.09..0.13 albedo on the
    theory that the NUMBER is what manifest 53 is about. They rendered as pale
    cream next to the Boatyard's box-projected, AO-multiplied, moss-graded
    surfaces: the gap the eye reads is a DETAIL gap, not a value gap. The fix is
    two lines — copy `mat_rock`, re-tint its Base Color through a MULTIPLY mix —
    and it inherits the box projection, the AO multiply, the roughness map and,
    most usefully, the world-up moss layer, which grasses the flat tier and leaves
    the cliff faces bare for free.
95. **`mat_rock` is tuned for a 60 m cliff and has to be re-tiled for a road.**
    At the library's own Mapping scale (0.17) a carriageway reads as one enormous
    boulder and a gate pier as a cave wall. Ground 1.15, road 1.55, dressed
    masonry 1.90 — roughly one texture feature per metre, which is what "coursed
    rubble" looks like. (Manifest 8 from the other direction: the first pass
    tiles too FEW times as often as too many.)
96. **A joined multi-part mesh's bounding box is not its footprint** — finding 62
    used the other way round. Registering keep-outs from `world_bbox(gate_yard)`,
    one object holding a shed at x=7 and a cart at x=20, swallowed the whole
    district: clutter fell from 82 pieces to 12 and the planting to almost none.
    Keep-outs are declared EXPLICITLY, one rectangle per structure.
97. **A rail's beams need the same corridor test as its posts.** The mule lines'
    posts were filtered through `over_walk` and the rails between them were placed
    unconditionally: 14 samples of the Porters' Yard pad under solid timber, on
    both the down-ray and the headroom test. Anything that SPANS between two
    tested points has to be tested at its midpoint too.
98. **Bunting heights are absolute and its sag is per run.** One 1.55 m sag applied
    to runs of 4 m and 8 m put the long one's low point at z=25.3 over a road at
    24.06 — 1.2 m of headroom where the gate wants 2.0. And a pennant on the lens
    is finding 57 again: the run that ends nearest the hero camera is the one that
    ruins it.
99. **The sun runs DOWN the gorge, so the ARRIVAL side of everything is a shadow
    side.** `SUN_key`'s direction is (-0.86, -0.35, -0.38): the player walking in
    off the overworld looks straight into the shaded face of the arch, the toll
    house and the whole yard. Measured, the tier's west faces get 0.82 W/m2
    against 2.75 on its sunlit top. The answer is a faked up-gorge bounce CARD
    (no shadow, 34 m cutoff, solved to hold the shadow side at a fixed fraction of
    the top), not a second key — a key from up-gorge would kill the raking sun
    that is the only thing making a flat 30 m tier legible.
100. **Compare districts on the SHARED rig only.** Up-facing irradiance is
    2.75 W/m2 on the gate tier against 14.02 at the Boatyard reference point, and
    that ratio is not a lighting failure: the Boatyard number is dominated by its
    own eleven 680 W lantern practicals at 3-5 m. Measure the shared rig alone, or
    the practicals will talk you into over-lighting an open-air tier by 5x.
101. **A branch's QA has two regions and both have to be quoted.** The canonical
    gate (`master_walk_qa.py`, default region) must still read 367/367 zero-drift
    and 100% rays — that is what says the branch has not touched the town. The
    district's OWN region is where the honest number lives, and it has to be
    quoted against the SAME region on the base commit, or a pre-existing defect
    reads as the district's.

102. **The town's own backdrop slab is the gate tier's biggest problem, and it is
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
103. **Diagnose a blown field by RAY-CASTING it, not by reasoning about it.** Three
    rays through the suspect pixels took two minutes and overturned a confident
    diagnosis ("the world gradient near the sun") that would have shipped as an
    open question for the user instead of a fix. `sc.ray_cast` from the camera
    down a reconstructed pixel direction names the object and the distance.

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
1. delete the 7 object names in `tools/blends/districts/gate_branch_deletions.json`
   (all `lm_valley-gate_*`, `lm_gatehouse_*`, `lm_winch-head_*` — three of p-gate's
   four members; the fourth, porters-yard, has no `lm_` shell, only the canonical
   `walk_lm_porters-yard`, which is untouched);
2. append the `GATE_DISTRICT` collection (155 objects incl. 5 `KEYG_gate_*` spots,
   2 `KEYG_approach_*` cards and 6 lantern practicals);
3. remap duplicate materials by name — the district adds `mat_gate_road`,
   `mat_gate_turf`, `mat_gate_stone`, `mat_gate_sack`, `mat_gate_troughwater`
   and reuses everything else;
4. apply manifest-51 render-hiding to the gate tier's ~40 walk/bar ribbons
   (`gate_shots.py` lists the exact filter it uses for renders);
5. re-run both gates.

Review renders: `docs/qa/districts/gate_v1..v6_*.png` (EEVEE per version, v6 the
final set), gate transcripts in `docs/qa/districts/gate_qa.txt`.  Cycles fell back
to CPU in `-b` on this machine, so v6 `arrival/gate/throughgate/tollyard/winch`
are Cycles 64/24 and the four wide shots are EEVEE — the value calls in the build
were made from the Cycles frames and from `gate_light.py`'s measured irradiance,
not from EEVEE (manifest 70).

---

## Locksfoot findings (in-master district #4 — `tools/locksfoot_*.py`)

The district that had to continue a rig which had been **truncated**, not finished:
the Waterfront's sky stops 4 m past its own east edge, and the whole gorge east of
x=66 was void.  It is also the first district whose hero prop only works because
the user changed the MAP (`dam-five` drop 1.8 -> 4.0, commit `e3f59a0`).

### Light

104. **A sky wash is a TILTED SHEET, so moving its centre in X does not slide it
     along itself — it lifts the whole plane.**  `SKY_wash` is 90 x 80 m at
     `rot_x = 7.125 deg`, which is `dz/dx = -0.125`.  Re-centring it from x=30 to
     x=51 to cover x -10..112 puts the sheet **2.6 m higher over the Boatyard**,
     and the finding-68 solve then asks for MORE power than the by-area rule
     (1249 W vs 1226 W) purely to undo the lift it just caused.  Any resize or
     extension has to keep the new centre ON the old plane:
     `z = 26 - 0.125 * (x - 30)`.  With that, the solve lands where it should —
     just under the by-area number (ratio 0.974).
105. **There is NO wattage that extends a truncated sky and leaves the
     neighbour's edge alone, and the solver will tell you so.**  Setting up the
     2x2 "hold the Boatyard AND hold the Waterfront's east end" returns
     `E_east = 0.0 W` **exactly**.  That is not a numerical failure, it is the
     answer: the accepted Waterfront was lit by a sky that stopped at x=70, so
     its east end is artificially dark and continuing the sky must brighten it.
     The decision is therefore *which* reference to hold, and the honest move is
     to hold the new district's own working level, then **measure and publish**
     the cost.  Measured, in Cycles, on accepted-content-only frames:
     Boatyard `continuity` **+1.16%**, Waterfront west **+1.08%**, Waterfront
     interior **+2.39%**, Waterfront **east lip +9.43%**.  The one knob that
     actually moves that last number is where the extension STARTS: pushing the
     run's west edge from x=70 to x=76 took the east lip from +35% to +27% of its
     sky irradiance at no cost to Locksfoot, because the solve just redistributes.
106. **Measure a neighbour's luminance only on frames whose CONTENT is the
     neighbour.**  Two of the Waterfront's own nine cameras (`boardwalk`,
     `fishdock`) look EAST and have Locksfoot in the background, so they reported
     +9% and +24% when the district behind them was built — measuring the new
     art, not the disturbance to the old.  Swapping to west-looking Waterfront
     cameras cut the same numbers to +2.4% and +1.1%.  A continuity camera has to
     be chosen for what is IN it, not for which district owns it.
107. **A backup blend can only be rendered from the directory its relative
     texture paths were written for, and a missing-texture frame reads as a
     luminance regression.**  `master-pre-locksfoot.blend` uses
     `//../textures/...`; copied to a scratch dir (or read in place from
     `tools/blends/backups/`) that resolves to nothing, every material renders
     Blender's magenta, and the "before" measurement came back 0.2539 against an
     "after" of 0.2259 — an apparent **-11% regression that was entirely the
     measuring rig**.  Copy a backup to `tools/blends/` (the same depth) before
     rendering it, and *look at* a before-frame before believing a delta.
108. **A chain element standing beside a neighbouring chain's LAST aim point
     closes a TAPER; it is not spill.**  `chain_range` deliberately measures the
     interior because a chain's ends fall off "by design — there is no next
     lamp".  Once there IS a next lamp the end is no longer a taper, and the
     honest report is two separate numbers: spill measured where no chain is
     adjacent (0.0000 W/m2 into both accepted districts here) and seam closure
     quoted against the chain's own level (0.186 -> 0.272 vs a working level of
     0.316 — the taper is filled, not overshot).  Asserting on the seam as if it
     were spill fails a correct rig.

### Topology vs. what the map asks for

109. **Canonical topology can forbid the machinery the map promises, and the
     right answer is a different STATE, not a smaller model.**  `lock-five` wants
     two mitre gate pairs, but `walk_e_moorage__lock-five_l1` and
     `walk_e_lock-five__north-landing_l0` run at z~0 straight THROUGH both gate
     heads and `walk_pad_lock-five` takes 2.60 m of a 3.60 m chamber.  A closed
     3.74 m leaf anywhere in there cost **24 blocked samples**.  Locks recess
     their leaves into the wall when they are OPEN — and an open lock is also the
     correct state for a district whose story is a boat being brought through.
     Same class as finding 86: check the hero against the map's own numbers
     first, and let the STAGING absorb the conflict.
110. **A pool is a solid slab, and a lock chamber is cut off from its pool by its
     own gates.**  `walk_pad_lock-five` sits at z -0.08 under a `pool-mid`
     surface at +0.20, so its down-rays hit water — 7 samples in the baseline,
     22 more the moment the dam blockout that had been hiding them was removed.
     Notching the pool around the chamber and giving the chamber its own
     mid-cycle water is both the physical truth and worth **22 blocked samples**.
111. **A landmark that is a FILLED disc (manifest 35) reaches further than it
     looks.**  `walk_lm_moorage` is 8 m across and its inland lip is at y=23 —
     3 m inland of anything that reads as "the dock" — and it silently caught the
     tenant shack's drying stage and six props standing on it.
112. **A blockout that swallows its own landmark's standing pad is why the
     baseline had samples at all.**  `lm_tenant-shack_body` covered
     `walk_pad_tenant-shack` entirely (5 blocked).  The kit shack is 5.07 m and
     the pad is 2.60 m, so the building goes INLAND of its pad and opens onto it
     — which is also how a shack with a porch actually sits.

### Placement

113. **`over_walk` on a point misses a tall object.**  A 2.9 m winch, a 3.7 m gate
     leaf and a 4 m canopy only have to touch the corridor once; testing the base
     alone let a rim clump take 19 samples of the Lockhead walkway and a balance
     beam 11 of the boardwalk.  `clear_box(x, y, z0, z1, pad)` — step the whole
     height band — took the district from 64 self-inflicted blocked samples to 0.
     A sloped BEAM needs the same treatment along its section (a 0.40 m stringer
     probed on its centre line still reached over the moorage).
114. **The walk Corridor keeps props out of the WALKING lines but nothing keeps
     them out of EACH OTHER.**  A 7 m lock coping carrying a winch, a capstan,
     three bollards and loose cargo placed each of them independently and the
     audit found **50 interpenetrations**.  One shared occupancy list —
     `spot(x, y, r)`, reserve-or-refuse — took it to 0 with no other change.
     Every district that scatters props needs one; the Corridor is not it.
115. **Vegetation from boxes reads as boxes.**  Three `obox` shells and a trunk
     is what the first canopy pass shipped, and on a cliff face it read as a pile
     of green crates.  Tapered `cyl` drums at 9 segments cost the same and read as
     mass (finding 15).

### Working in someone else's file

116. **A helper that returns an EXISTING datablock untouched makes a build script
     non-idempotent for VALUES.**  `plain(name, rgb, ...)` returned early if the
     material already existed, so `mat_boil` was knocked down twice in the source
     and the master kept the first number both times.  Create-or-RE-TONE.
117. **Scope a texture-path remap to the maps you actually appended.**  The kit's
     images are relative to `tools/blends/districts/` (manifest 63) and have to be
     re-pointed — but the first version looped over `bpy.data.images`, which is a
     loop over the WHOLE TOWN's textures.  Match on the three known basenames,
     and `user_remap` + remove the duplicate datablock the append just made, or
     the master collects `old_stone_wall_02_Diffuse.jpg.001 ... .0NN`, one per
     rebuild.  The same is true of light datablocks: removing the OBJECT orphans
     its data, so the next run's copy is `SKY_wash_lf_0.001` and the names drift
     out of the handover.
118. **Kit donors stand at the WORLD ORIGIN and `hide_render` does not stop a
     glTF export.**  `libraries.load` puts 19 finished assemblies at (0,0,0),
     which is inside the Boatyard.  Rename them (`KITSRC_*`) so the placed copies
     keep the clean names, and DELETE them once the last placement has copied
     from them.

### What the drop ruling bought

119. **A map edit is the cheapest fix for a scale problem, and it shows.**  The
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
| Cycles mean luminance, Boatyard `continuity` | 0.2237 | **0.2263 (+1.16%)** |

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
  finding 85 would like even after `mat_boil` was knocked to 0.132.
- `p-lockhead` was left entirely untouched (jurisdiction unresolved) — but the
  ground and the cliff under it are built and terraced, so whoever takes it
  inherits a site, not a void.
- The **tar-dark story boat is NOT built** (ruled a shared library asset);
  `lf_barge_moorage` stands at the Moorage as a mooring placeholder so the berth
  and its framing are already correct when the real hull arrives.

Composition was judged from eleven cameras in `tools/locksfoot_shots.py`
(`lockbasin`, `damface`, `crestwalk`, `moorage`, `cottagespur`, `northlanding`,
`fromcrossing`, `fromriver`, `westseam`, plus `continuity` and `wfcontinuity`).
EEVEE versions v1..v5, Cycles beauty set `locksfoot_v5cyc_*`.

**Still outstanding (deliberately, and on the Waterfront's own precedent):** no
`del-lockfive` / `del-cottage` / `del-northlanding` / `del-lockhead` /
`del-crossing` depth bundles were baked.  There is no `del-waterfront` bundle
either — the exterior districts' occlusion bake has been a separate rollout, and
these five parcels are all still `draft: true` in the map.  The blend is ready for
it: the eleven `locksfoot_shots.py` cameras include the parcels' own framings, so
`tools/depth_bake.py` needs a camera per sceneKey and nothing else.
