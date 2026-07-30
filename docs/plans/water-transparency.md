# Water transparency — feasibility, shader design, and the bathymetry work list

**Status:** design note, tranche-2 direction C. Written read-only against
`tools/blends/dellhollow-master.blend` while the 17-camera bake held the GPU.
No master edits, no renders.

The user's note: *"the land terrain disappears as soon as it hits the water…
in reality you can see the terrain extend below the surface and slowly fade out
as the water gets deeper."*

---

## Method

Two read-only probes:

* **Bathymetry** (`tally.py`, water stage) — a 0.75 m grid over each water
  sheet's footprint, with a **down-ray stack** at every sample: cast straight
  down, record every hit in order, identify the water surface, then the first
  non-water hit *below* it. 13,000 samples over four sheets. Yields, per sample:
  is there water here, is there a bed under it, and how deep.
* **Shoreline visibility** (`t2_shore.py`) — every wet cell with a dry
  4-neighbour, projected into all 17 cameras and occlusion-ray-cast, so the work
  list is scoped by metres of shoreline each camera can *actually see*.

---

## Finding 1 — the bed exists almost everywhere. It is a flat slab.

**Does terrain exist below the waterline? Yes — 94-98% of it.**

| sheet | surface z | wet samples | no bed under them | bed object |
|---|---|---|---|---|
| `water_pool-upstream` | +3.60 | 2,671 | 168 (6%) | `riverbed` (87%) |
| `water_pool-mid` | +0.20 | 6,165 | 313 (5%) | `riverbed` (85%) |
| `water_pool-downstream` | -3.80 | 3,633 | 78 (2%) | `lf_riverbed_tail` (94%) |
| `lf_lock_water` | -1.40 | 36 | 11 (31%) | `lf_lock_floor` |

So "the terrain stops at the waterline" is **not** what is happening. The bed is
there. The problem is its shape:

```
riverbed          8 vertices ·  6 polygons · z -4.20 .. -3.90 · x -70..87, y 18..78
lf_riverbed_tail  8 vertices ·  6 polygons · z -7.60 .. -7.30 · x  87..131, y 18..78
```

Two flat slabs. Depth histograms, in 0.5 m bins:

* `water_pool-mid` — **4,999 of 6,165 samples land in the single 4.0-4.5 m bin.**
  Median depth 4.10 m.
* `water_pool-downstream` — **3,356 of 3,633 in the 3.5 m bin.** Median 3.50 m.
* `water_pool-upstream` — median **7.50 m** (its surface sits 3.6 m above the
  same `riverbed` slab the mid pool uses).

And the shoreline profile is a step, not a ramp:

| sheet | 0.75 m from land | 1.50 m | 2.25 m | 3.00 m | 3.75 m |
|---|---|---|---|---|---|
| upstream, mean depth | 0.21 m | **7.25 m** | 7.29 | 7.42 | 7.50 |
| mid, mean depth | 1.82 m | **3.57 m** | 3.69 | 3.60 | 3.66 |
| downstream, mean depth | 3.25 m | 3.23 m | 3.45 | 3.51 | 3.50 |

**The upstream pool goes from ankle-deep to seven and a half metres in one
0.75 m step.** The downstream pool is already 3.25 m deep in the *first* cell.

### What this means for the shader

**A depth-based transparency shader, on its own, would produce almost no visible
change.** There is no shallow zone to see through. Beer-Lambert absorption tuned
so that 3-4 m reaches the ruled turquoise would render the mid pool at a uniform
"3-4 m" everywhere, the downstream pool likewise, and the upstream pool
completely opaque — with the same hard edge the user is complaining about, now
achieved by physics instead of by an opaque material.

**The bathymetry is the deliverable. The shader is the cheap part.** That
inverts the brief's implied ordering and is the single most important sentence
in this document.

---

## Finding 2 — half the "shoreline" is not a shoreline at all

The water sheets are **axis-aligned boxes**: 8 or 16 vertices, 0.4 m thick, with
rectangular footprints. Classifying every waterline cell by what its dry
neighbour actually is:

| sheet | real bank (land above water) | quad edge floating over open bed / void |
|---|---|---|
| `water_pool-upstream` | 44 cells | **161 cells — 79%** |
| `water_pool-mid` | 250 cells | **189 cells — 43%** |
| `water_pool-downstream` | 91 cells | **162 cells — 64%** |

Between **43% and 79% of each pool's perimeter is the rectangle's own straight
edge**, ending in mid-air over the bed rather than meeting land. In
`variety_waterfront.png` that is the dead-straight diagonal where the turquoise
stops — it is not a bank, it is the corner of a box. Making that edge
*transparent* would make it worse, not better: you would see a straight-line
fade hanging over the riverbed.

Where the water *does* meet land, the bank is usually a wall: on
`water_pool-mid`, **46% of waterline cells rise more than 1 m within one 0.75 m
step and 23% rise more than 3 m** (quay walls, piles, the seam bank). On
`water_pool-upstream` the figure is 0% — every one of its 43 bank cells sits at
exactly +0.36 m, i.e. the flat lip of `yard_ground`.

---

## Finding 3 — which shoreline the cameras can actually see

| camera | shoreline in frame | of which a wall | gentle bank (worth shelving) |
|---|---|---|---|
| lockfive | 35.5 m | 8.0 m | **27.5 m** |
| north-landing | 34.0 m | 33.0 m | 1.0 m |
| fishdock | 25.5 m | 22.0 m | 3.5 m |
| cottage-steps | 17.5 m | 11.0 m | 6.5 m |
| boatyard | 15.5 m | 0.0 m | **15.5 m** |
| deep-stairs | 5.5 m | 3.5 m | 2.0 m |
| waterfront | 3.0 m | 3.0 m | 0.0 m |

Water screen-share for reference: fishdock 30.2%, waterfront 20.5%,
north-landing 15.7%, lockfive 8.0%, cottage-steps 4.3%, boatyard 2.5%.

The reading: **waterfront and fishdock are dominated by water but see almost no
natural bank** — their water meets quay walls, the dam and the barge. Their
"hard cutoff" is mostly Finding 2 (the floating quad edge), not Finding 1.
**lockfive and boatyard are where a real shelf will read**, and cottage-steps
third. That is 49 m of gentle bank across three cameras — a small, precise job.

---

## The shader design

### Cycles side (for the bake)

`m_water` today, post the river-flow pass, is already the right shape and must
stay that way (finding 221):

```
foam_mix (Mix Shader)
 ├─ water_lobe  Principled  BaseColor (0.04,0.105,0.12) FLAT  rough 0.09  IOR 1.33  Alpha 1.0
 └─ foam_lobe   Principled  BaseColor (0.55,0.60,0.62)  FLAT  rough 0.62  IOR 1.33  Alpha 1.0
        driven by  AO-proximity x flow-noise foam mask
```

Neither Base Color is linked. **That must not change** — it is the only reason
`m_water` exports a real `baseColorFactor` today, and finding 221 records two
measured failures from breaking it.

**Rejected: Volume Absorption.** Physically the right answer and it would give
Beer-Lambert depth falloff for free — but only if the water mesh is a closed
prism whose bottom face follows the bed. Today it is a 0.4 m slab, so the volume
path length is a constant 0.4 m everywhere. Remodelling all four sheets into
bed-following prisms plus enabling volume bounces would multiply the beauty
render cost (currently ~3.5 min/frame at 128 samples) on the six water cameras.
Filed as the "someday, correctly" option; not this pass.

**Rejected: Transmission = 1.0 + IOR 1.33.** True refraction, no volume needed —
but it adds transmission bounces on 20-30% of the pixels of three frames, and
refraction through a flat 0.4 m slab bends the bed in a way that reads as glass,
not river. Also the water would stop receiving the foam lobe's roughness story
coherently.

**Chosen: baked depth -> alpha, with a flat-lobe Principled.** A build-time
script raycasts down from each water-surface vertex to the bed and writes the
result into a `Col` colour attribute on the water meshes:

```
Col.rgb = (1,1,1)                  ← WHITE, the neutral element (finding 218)
Col.a   = ramp(depth) : 0.00 m → 0.06     nearly clear at the waterline
                        0.60 m → 0.30
                        1.50 m → 0.62
                        3.00 m → 0.88
                        ≥4.00 m → 0.97     the ruled turquoise, effectively solid
```

In the material, one new `Color Attribute` node feeds a `ColorRamp` (for
authoring control) into **`water_lobe.Alpha` and `foam_lobe.Alpha`**. Base Color
on both lobes stays flat and unlinked. Cycles alpha-blends the water over the
bed with no refraction, no volume, and no extra bounce budget — the cost is a
handful of extra transparent bounces (`transparent_max_bounces` is already 8),
which on a stylised backdrop is close to free.

The absorption *colour* comes for free from the existing turquoise: partial
alpha over a tan bed reads as the bed desaturating toward `#38</>5B61` as depth
rises, which is exactly "fading toward the ruled turquoise" without touching the
ruled turquoise itself. (The ruled turquoise, for reference: linear
`(0.04, 0.105, 0.12)`, sRGB `#385B61`.)

`m_water` is already `blend_method = HASHED` / `surface_render_method =
DITHERED`; for a smooth shoreline fade this must become **`BLENDED`**. Note that
`master_survivability`'s EEVEE luminance gate renders in EEVEE, where this
property is load-bearing — expect the gate to move on the water cameras and
budget for it (see gates below).

**The depth pass is unaffected**, and this is worth stating because it is the
obvious thing to worry about. `cine_bake.py` renders depth under a
`view_layer.material_override` that replaces *every* material with one Emission
shader. The water stays opaque for depth, so `depth.png` continues to record the
water **surface**, and character occlusion at the waterline is unchanged. The
only consequence: a character standing on the bed *under* transparent water
would be occluded by the surface even though you can see through it. Dellhollow
has no wading, so this is a note, not a bug.

### Runtime side (townwalk / del-cine GLB)

Per finding 221, the render tree may not gain a linked Base Color and the export
proxy will not rescue a Principled-bearing tree. This design does not need
either:

* **Base colour** — `water_lobe`'s flat `(0.04, 0.105, 0.12)` is untouched, so
  the exporter keeps writing the same `baseColorFactor` it writes today. Verified
  green by `master_glb_albedo.py` two commits ago; it should read identically
  after this pass.
* **Alpha mode** — set `surface_render_method = 'BLENDED'` and the exporter
  writes `alphaMode: "BLEND"`.
* **Alpha value — two tiers.**

  **Tier 1, the guaranteed floor.** A **fixed** `baseColorFactor[3]` — set
  `water_lobe.Alpha` default to **0.72** and accept a uniformly translucent
  river at runtime. Zero risk, zero new mechanism, and still strictly better
  than today's opaque sheet. This is what the brief proposes and it is the
  fallback.

  **Tier 2, worth one experiment.** glTF multiplies `baseColorFactor` by
  `COLOR_0` **including the alpha channel**, and Blender's exporter emits
  `COLOR_0` from a colour attribute the material reads. Since this design
  already bakes `Col` with `rgb = white` and `a = depth alpha`, the runtime
  would get `alpha = 1.0 x COLOR_0.a` — **the same depth fade as the bake, for
  free, with no linked Base Color anywhere.** RGB is unaffected because white is
  the neutral element.

  This is the finding-211 relink shape applied to the alpha channel instead of
  the colour channel, and it is exactly the kind of thing that either works
  cleanly or fails silently. **Measure it, do not assume it**: export, parse the
  GLB chunk table with `master_glb_albedo.py`, confirm a 4-component `COLOR_0`
  with a non-trivial alpha range, and confirm three.js is built with
  `vertexColors` on the water material. If any link in that chain is missing,
  ship Tier 1 and move on. Do not spend a second attempt on it.

---

## The bed-geometry work list

The rule: **a shelf is only worth building where a camera can see a gentle bank.**
49 m of shoreline qualify, in three places.

| # | region | world extent | serves | current bed | build |
|---|---|---|---|---|---|
| **B1** | boatyard slipway bank, upstream pool south edge | x 0..27, y 29..32 | boatyard (15.5 m, 100% gentle), waterfront | `riverbed` slab at -3.9, i.e. **7.5 m** under a +3.6 surface | sloping shelf from the waterline down to -1.0 over 4 m, then a talus run to meet the slab; ~140 quads |
| **B2** | Lock Five / drying-deck bank, mid pool east edge | x 60..84, y 26..31 | **lockfive (27.5 m gentle)**, crossing, cottage-steps | slab at -3.9 under a +0.2 surface (4.1 m) | shelf to -0.8 over the first 3 m, -2.0 by 5 m; ~230 quads |
| **B3** | cottage-steps / north-landing bank, downstream pool | x 95..112, y 26..34 | cottage-steps (6.5 m gentle), north-landing | `lf_riverbed_tail` at -7.3 under a -3.8 surface (3.5 m) | shelf to -4.4 over 3 m; ~110 quads |

Around **480 quads / ~540 vertices.** The shelf should be a *shore-parallel
strip* welded to the existing bank mesh at the waterline and to the slab at its
outer edge, wearing the same `mat_rock` the bank already uses so the material
transition is invisible.

**And the fix that is not geometry:** the water sheets' rectangular footprints.
Where a quad edge floats over the bed inside a camera frustum, either extend the
sheet under the bank (cheapest — the water is 0.4 m thick and hidden inside the
terrain) or cut the footprint to follow the bank. Priority is
`water_pool-mid`'s south edge at y = 26, which stops 2 m short of `wf_ground`
(y ≤ 24.1) directly in the waterfront and fishdock frames. `water_pool-mid`
already has 16 verts / 12 polys, so it is a two-box mesh and extending one box's
y-extent is a one-line edit.

---

## Execution plan

**Scope and effort**

| phase | work | effort | independent commit |
|---|---|---|---|
| **W1** | extend the three water sheets so no quad edge floats inside a frustum | 1 h | yes |
| **W2** | build shelves B1, B2, B3 (~540 verts) | 3-4 h | yes |
| **W3** | `tools/water_depth_bake.py` — raycast down from each water vertex, write `Col` (rgb white / a = depth ramp). Idempotent, run-twice-verified, invertible | 2 h | yes |
| **W4** | wire `Color Attribute -> ColorRamp -> both lobes' Alpha`; set `surface_render_method = 'BLENDED'`; keep both Base Colors flat | 1 h | yes |
| **W5** | export experiment: does `COLOR_0.a` survive? Timeboxed to one attempt; fall back to fixed alpha 0.72 | 1 h | fold into W4 |

**~8-9 h.**

A note on W3's resolution: the water sheets have 8-16 vertices, so a per-vertex
depth attribute has nowhere to live. **W3 must subdivide the water surfaces
first** — roughly 1.5 m spacing over the wet footprint, ~2,000 verts across all
four sheets. That subdivision is also what lets the surface follow a shelf's
shape rather than cutting a straight line across it, so it does double duty. It
is included in the W3 estimate.

**Risk**

* **Medium on W4, and it is a gate risk.** `master_survivability`'s EEVEE
  luminance gate has a +/-0.5% band. Turning the water blended will move
  waterfront, fishdock and north-landing by well over that — legitimately. The
  gate must be re-baselined for those three cameras rather than "fixed", and per
  finding 220 **any failing render gate is repeated twice and localised with an
  ablation before it is believed** (a parallel bake alone can fake -0.5%).
* **Low-medium on W2.** The shelves sit under water and are never walked, but
  B2's strip runs beside the Lock Five walk corridor. `walk QA` must be
  bit-identical; if it is not, the shelf is poking through the deck.
* **Low on W1/W3.** Mesh extension and an attribute bake, both scripted and
  invertible.
* **The one that will bite.** `water_pool-upstream` is **7.5 m deep** over the
  same slab the 4.1 m mid pool uses. A ramp tuned on the mid pool renders the
  upstream pool fully opaque and the B1 shelf invisible. **Either the ramp must
  be per-sheet, or B1's shelf must reach out far enough to matter at 7.5 m.**
  Recommend per-sheet ramp maxima driven by each sheet's own median depth, which
  the bake script already measures.

**Gates needed**

1. `walk QA` bit-identical.
2. `tools/master_glb_survival.py` — 0 white primitives.
3. `tools/master_glb_albedo.py` — `m_water` still reports `(0.04, 0.105, 0.12)`.
   If it reports absent-factor instead, the flat-lobe rule was broken; revert W4.
4. GLB chunk inspection — `alphaMode == "BLEND"` on the water material, and (if
   Tier 2) a 4-component `COLOR_0` whose alpha spans the ramp.
5. **Depth-map gate**, specific to this pass: bake `waterfront` and `fishdock`
   and diff `depth.png` against the current plates. It **must be unchanged** —
   the material override makes this true by construction, and a change means the
   override is not covering the water and character occlusion is about to break.
6. EEVEE luminance: re-baselined on the three water cameras, unchanged
   elsewhere, per finding 220's repeat-and-ablate rule.
7. Taste gate: **waterfront** (the frame the user was looking at) and
   **lockfive** (the frame with the most gentle bank in view).

**Re-bake**

Cameras where `m_water` is on screen at all: **boatyard (2.5%), waterfront
(20.5%), fishdock (30.2%), cottage-steps (4.3%), lockfive (8.0%),
north-landing (15.7%), deep-stairs (0.6%)** — plus **weave and crossing**, whose
frames include the B2 shelf region even though they show little water.

**Nine of seventeen.** Combined with `cliff-completion.md`'s fifteen, the union
is sixteen — so if these two tranches land together, **bake all 17 once** rather
than twice.

**Ordering.** W1 and W2 (geometry) must land before W3 and W4 (shader). Baking
a depth attribute against the current flat slab would encode the very step
function this pass exists to remove, and the ramp would then be tuned to hide it.
