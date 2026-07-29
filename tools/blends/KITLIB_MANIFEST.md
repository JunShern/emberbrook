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
