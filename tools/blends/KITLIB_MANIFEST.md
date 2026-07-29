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
