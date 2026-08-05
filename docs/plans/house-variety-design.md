# House variety & river flow — the topology, then the plan

**Status:** design note, written before any transform, per the coordinator's
instruction. Measurements are from `tools/blends/dellhollow-master.blend` at
commit `038b798` (post golden-rig, post green-mix).

The user's two notes from tonight's review:

1. *"A lot of the town buildings seem to be baked in green colour."* Houses should
   be a mix of colours — varied, alive, less bland.
2. *"It is a river."* The water must read as **flowing** in a still frame, not as
   a mirror-flat pond.

Both are palette/material questions, so both land here. This note answers the
first question the brief asks — *how does building colour actually work* — before
proposing anything, because the answer changes the plan substantially.

---

## Part 1 — How building colour actually works

### The kit template

Every district's structures are built from one material template
(`tools/kit_build.py` and the district `*_materials.py`
files). The shape is always the same:

```
ImageTexture(Diffuse) ──┐
ImageTexture(AO) ───────┴─ Mix(0.55) ─ Mix.00N(tint literal, fac) ─ … ─ Principled.Base Color
                                        ▲
Geometry.Normal.Z ─ ColorRamp ─┐        │  the up-facing × noise mask
NoiseTexture ─ ColorRamp.001 ──┴─ Math ─┘
```

So a material's colour is **not** a texture and **not** a vertex attribute — it is
**one or two literal RGB values sitting in `Mix` node inputs**, layered over a
greyscale photo texture. That is a very good thing for this pass: a palette
variant is a material copy with one socket changed, which is the cheapest
possible edit and trivially reviewable.

Two exceptions matter:

* **`lf_*` (the Lockfoot kit — 200 objects)** drives Base Color from a `Mix` whose
  **Factor is 1.0**, i.e. the image texture is fully overridden and the colour is
  the mesh's `Col` vertex attribute. This is the same survivability shape the
  foliage uses. Colour variants here mean recolouring `Col`, exactly as
  `tools/veg_greenmix.py` does.
* **`m_water`, `mat_flag_*`, window/glass materials** are bare flat Principled
  colours with no texture at all.

### The measured cause of "baked in green"

Two separate greens, and neither is the one you would guess.

**(a) Every roof in the town is green.** There are exactly two roof materials:

| material | mechanism | tint | objects |
|---|---|---|---|
| `mat_shingle_mossy` | tint literal `Mix.001.B` | `(0.125, 0.215, 0.08)` moss green | 17 |
| `lf_shingle` | vertex `Col` | mean `(0.155, 0.174, 0.090)` green-olive | 10 with real roof faces |

That is **27 of the town's roofs in one green**, including every building in the
shelf shop row, the gatehouse, the cookhouse, the chandlery, the netloft, the
boatwright's shed, all nine weave huts and the keeper's cottage. In a 3/4
top-down FF-grammar camera the roof is most of what you see of a building, so a
single roof colour reads as a single *town* colour. This is the finding.

**(b) A moss overlay is sprayed on nearly every material in town.** The literal
`(0.09, 0.16, 0.05)` appears in `Mix.001.B` or `Mix.002.B` of `mat_wallwood`,
`mat_wallwood_dark`, `mat_timber`, `mat_timber_dark`, `mat_lk_slate`,
`mat_paint_blue`, `mat_paint_red`, and **all ten** of the shelf and quay-market
paints. It is masked by up-facing normal × noise, so it greens every horizontal
surface in the town at once.

### What is NOT the cause — measured, so we do not "fix" it

The brief assumed the wall panels were uniform. **They are not.** Measured:

* **The nine weave huts** already carry five distinct wall colours in their
  `lf_deck` vertex `Col`: red `(0.64, 0.17, 0.10)`, olive `(0.31, 0.36, 0.17)`,
  orange `(0.72, 0.38, 0.10)`, cream `(0.90, 0.64, 0.31)`, blue
  `(0.25, 0.40, 0.49)` — and **no two adjacent huts along the row match already**.
  The hut row is the coordinator's named test case and it passes today.
* **The shelf shop row** already has five paints across seven buildings: inn
  green, item-shop teal, weapon-shop rust, armour-shop ochre, home_a green,
  home_b bone, home_c teal.

Repainting walls that already vary would be motion without progress, and would
spend the taste gate's credibility on the wrong axis. The two duplicated shelf
paints (green ×2, teal ×2) are worth resolving; the rest of the wall work is not.

---

## Part 2 — The plan for the houses

**Scope: roofs, plus two duplicate shelf paints. Nothing else.** Timber
structure, frames and the moss overlay stay exactly as they are — green and brown
remain the town's primary palette per the ruling.

### The roof set (four, from one)

`mat_shingle_mossy`'s tint literal becomes four materials. Moss stays; it becomes
one of four rather than the default.

| variant | tint (linear) | luminance |
|---|---|---|
| `mat_shingle_mossy` (unchanged) | `(0.125, 0.215, 0.080)` | 0.186 |
| `mat_shingle_cedar` | `(0.245, 0.145, 0.080)` | 0.162 |
| `mat_shingle_slate` | `(0.130, 0.145, 0.175)` | 0.144 |
| `mat_shingle_shake` | `(0.225, 0.200, 0.150)` | 0.202 |

Luminance is held inside ±23% of the moss original, on the same principle as the
green mix: the golden-hour key does the unifying, so only hue moves and no
composition needs re-checking. A dark slate roof reading darker than a bleached
shake roof is the point, not drift.

The `lf_shingle` kit roofs get the same four families, applied to `Col` by a
**fixed per-variant channel scale** computed against the kit's canonical mean
`(0.155, 0.174, 0.090)` — fixed, not per-object, so the transform is exactly
invertible and preserves each roof's own baked variation. Same discipline, same
revert story as `veg_greenmix.py`.

### Assignment: deterministic, with a neighbour constraint

`sha1(object name)`, never `random()`. Then a **neighbour-difference pass**: the
objects are walked in a stable name order and any roof whose colour matches an
already-assigned roof within 9 m in plan is bumped to its next-best choice. Nine
metres is roughly two building widths in this town, which is the distance at
which two roofs share a frame. The weave hut row and the shelf shop row are the
visible test cases and both are inside that radius.

### The two duplicate shelf paints

`shelf_home_a` green → **madder** `(0.46, 0.19, 0.17)`, `shelf_home_c` teal →
**slate blue** `(0.24, 0.30, 0.41)`, derived as `mat_shelf_paint_madder` and
`mat_shelf_paint_slate` from the existing template. That gives the shop row seven
distinct panel colours and completes the six-accent storybook palette the brief
asks for — rust, madder, ochre, bone/limewash, sage green, teal, slate blue — of
which the kit already contained five.

### Interiors

`shelf_item_shop`, `shelf_weapon_shop`, `shelf_armor_shop`, `shelf_inn` and
`qm_cookhouse` all have interior scenes (`tools/*_int_build.py`). **Neither
building I repaint has an interior scene** — `shelf_home_a` and `shelf_home_c` are
homes, not shops — so no exterior/interior door-and-trim divergence is created by
this pass. Noted, not chased, per the brief.

---

## Part 3 — The river

### What the water is today

`m_water` is a bare Principled: Base Color `(0.04, 0.105, 0.12)`, Roughness
`0.10`, nothing else. At roughness 0.1 that is very nearly a mirror, which is
exactly why it reads as a pond: a still frame of moving water is *defined* by
its broken reflection, and a mirror has none. Four objects wear it —
`water_pool-upstream` (z 3.4), `water_pool-mid` (z 0.0), `lf_lock_water`
(z −1.55), `water_pool-downstream` (z −4.0) — 8 to 16 vertices each.

The step down in surface height from upstream to downstream confirms the flow
axis: **the river runs +x**, the same direction through all four pools, so one
flow direction serves the whole town. (Verified against the pools' own extents,
not assumed; the script reads them from the blend.)

### The three deliverables

1. **Flow-stretched surface detail.** Noise sampled through a Mapping node scaled
   `(0.11, 1.0, 1.0)`, so features are ~9× longer along x than across it, driving
   a Bump. Anisotropy is what separates current from pond; it is the whole trick.
2. **Obstacle response.** An `Ambient Occlusion` node with a short distance is a
   *proximity to other geometry* probe: it returns 1.0 in open water and falls off
   against the weir, the lock walls, mooring piles, hulls and the slipway. Inverted
   and multiplied by a finer cross-flow noise, it drives both a whitening of the
   base colour and a roughness rise — foam where the water meets the town, with no
   hand-placed foam geometry and nothing to keep in sync when the town moves.
3. **Reflection breakup.** The bump above plus a roughness that rises with the
   flow noise. Vertical streaking of lantern and window reflections falls out of
   the anisotropy for free, because a long-along-x ripple tilts the surface
   across-x, which is the axis that smears a reflection vertically in these
   cameras.

The pool-turquoise base colour is **unchanged** — that was ruled earlier tonight
and goes to the user's taste board as its own knob.

### Mechanism, and why not a texture

The coordinator suggested a tiling normal/foam texture on glTF-survival grounds,
and the concern is exactly right: `cine_bake.py`'s GLB export takes **every
camera-visible mesh**, not just `walk_`, so the water surfaces really are in
`scene.glb` and really would arrive white if Base Color were linked to a
procedural tree.

I am using the repo's own established cure instead, because it is tested and adds
no binary assets: the **export proxy** from `tools/master_survivability.py`. The
render tree is nested in an outer `MixShader` at **factor 0.0** against a
`Principled` carrying the flat turquoise. Factor 0 renders branch A only, so
Cycles sees the full procedural water and Blender is unchanged, while the glTF
exporter finds a Principled and writes a real `baseColorFactor`. This is the same
mechanism that already carries `mat_darkfall` and the town's four flat pennants
through export, and it is verified the same way — `master_glb_albedo.py` reads the
GLB's own JSON.

The proxy's roughness is set to match the water's *character* rather than its peak
gloss, so the runtime reads a river rather than a plastic sheet.

An image texture would also work and is the right answer the day the water needs
to survive as *art* in the runtime rather than as collision. It is not the right
answer for a surface the runtime only ever uses as a depth-tested blocker under a
baked plate.

---

## Future — not this pass

**A live animated water layer composited over the baked plates.** The classic
FF7/8/9 trick: the pre-rendered background is a still, but the water inside it is
a small looping animated sprite layer drawn over the plate and depth-tested
against the same depth map the characters use. Dellhollow already has every piece
this needs — per-camera `bg.png` + `depth.png` from one Blender session, and a
runtime that composites characters into that depth. A water layer would be one
more RGBA strip per camera (a short loop of the water surface rendered alone,
alpha-masked to the water's screen area), drawn after the plate and before the
characters, at the water's own depth. It would cost one extra texture per river
camera and would make the river move in a game that is otherwise made of stills —
which is a large amount of life for a small amount of memory. Filed, not built.

**The moss overlay.** `(0.09, 0.16, 0.05)` in a dozen materials is the town's
second green and the reason even repainted walls trend green. Shifting it toward
a grey-green lichen in the *wall* materials only, leaving stone and roofs damp,
would desaturate the town-wide cast without touching the identity. It is a
cross-cutting change to a dozen materials and belongs in its own pass with its
own taste gate, not smuggled into this one.
