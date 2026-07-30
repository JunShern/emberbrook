# Cliff completeness and resolution — the audit, and what is actually wrong

**Status:** design note, tranche-2 direction B. Written read-only against
`tools/blends/dellhollow-master.blend` while the 17-camera bake held the GPU.
No master edits, no renders.

The user's two observations from the probe review:

1. *"At least one ENTIRE cliff wall missing — flat gray background showing
   through"* (visible above the weave rim in `variety_weave.png`, and elsewhere).
2. *"Built-out cliff faces at inconsistent resolution/detail."*

Both are real. **Neither is what it looks like**, and the difference matters
because the obvious fix — "find the hole, fill it" — would have addressed 0% of
observation 1 on eight of the ten affected cameras.

---

## Method

Three read-only ray passes over all 17 solved cameras, at 224x128 = 28,672 rays
per frame, using the same camera construction as `cine_bake.py::build_cam` so
the grid and the shipped plate agree:

* **`tally.py`** — first hit per pixel: object, material, distance.
* **`tally2.py`** — *first opaque hit*: FX cards whose material is volume-only
  (`mat_haze_*`, `mat_spray`, `mat_smoke`) are skipped, so a pixel that really
  shows the world background counts as a leak. This distinction is the whole
  audit; without it every number below is wrong.
* **resolution proxy** — for each visible mesh, `px_per_edge = mean_edge_m x
  (H/2) / (d_mean x tan(fov/2))` at the shipped 2688x1536: **how many delivered
  pixels a single mesh edge spans.** Under ~80 px an edge reads as curvature;
  over ~150 px you are looking at a flat facet.

---

## Finding 1 — the "missing wall" is not missing. It is an eight-vertex grey box.

True background leak, measured with FX cards skipped:

| camera | sky-leak % | verdict |
|---|---|---|
| **lockfive** | **19.96%** | real void — 54% of leak rays point *downward* |
| **cottage-steps** | **16.26%** | real void — 73% of leak rays point *downward* |
| boatyard | 0.36% | legitimate sky above the rim, 100% upward |
| shelf-east | 0.08% | 22 px hairline at the far frame edge |
| the other 13 | **0.00%** | no leak at all |

So on **gate, quay-west, weave, loop-stairs, quay-east, lockhead, cottage,
crossing and deep-stairs — every camera the user was looking at — not one pixel
shows the world background.** Every ray hits geometry.

What the grey is: **`cliff_town`.**

```
cliff_town      8 vertices · 6 polygons · 18,232 m² of surface
                bbox (-35, -6, -9) .. (135, 0, 37)     the town's whole south wall
                material  m_rock  —  a bare Principled, NO texture, NO bump,
                                     base colour #716D6A, roughness 0.9
```

It is a 170 x 46 m cube standing in for the valley's south side, wearing a flat
neutral warm grey. At 30-70 m under the golden key it renders as exactly what
the user described: flat grey background. It is not a hole in the wall — **it is
the wall, built as a placeholder and never replaced.**

| camera | cliff_town screen-% | d_mean | px per mesh edge | visible world patch (on the y=0 face) |
|---|---|---|---|---|
| **lockhead** | **22.64%** | 32.8 m | 5,495 | x 61.0 .. 82.3, z 9.9 .. 19.9 |
| **loop-stairs** | **20.05%** | 36.3 m | 4,963 | x 64.3 .. 78.5, z 7.8 .. 24.6 |
| **quay-east** | **19.96%** | 41.1 m | 4,382 | x 64.5 .. 98.6, z 9.3 .. 20.6 |
| **cottage** | **16.92%** | 42.8 m | 4,212 | x 64.0 .. 105.3, z 9.1 .. 18.9 |
| **gate** | **11.84%** | 50.0 m | 3,603 | x -21.0 .. 17.8, z -1.9 .. 33.3 |
| **weave** | **9.98%** | 59.3 m | 3,041 | x 64.4 .. 114.5, z 10.2 .. 19.3 |
| **crossing** | **8.86%** | 50.2 m | 3,591 | x 64.0 .. 109.2, z 13.9 .. 20.0 |
| **quay-west** | **8.41%** | 54.1 m | 3,332 | x 41.3 .. 80.2, z -4.2 .. 23.5 |
| **deep-stairs** | **3.45%** | 67.7 m | 2,664 | x 45.5 .. 82.0, z 7.9 .. 23.5 |
| **cottage-steps** | **3.04%** | 66.9 m | 2,694 | x 115.5 .. 135.0, z 1.9 .. 16.2 |
| lockfive | 0.04% | 78.2 m | — | x 112.7 .. 128.4 |

**One tenth to nearly one quarter of ten frames is a single untextured quad.**
`px_per_edge` of 3,000-5,500 means one mesh edge spans two to three and a half
*entire frame heights*. There is no other surface in Dellhollow within two
orders of magnitude of that.

### The part that is genuinely surprising

`cliff_far` — the *properly built* far wall, **654 vertices, textured with
`mat_rock_farwall`**, 210 m long, standing at y 80-99 — is visible in **zero of
the seventeen cameras. 0.0% in every single frame.**

The town's whole vista budget went into the wall that nobody looks at. Every
solved camera stands on the north side of the valley and looks south; the only
wall in any frame is the placeholder. The same is true of the rest of the vista
kit — `cliff_far_toe` (0.1% on two cameras), `fx_ridge_upstream`,
`fx_far_town_silhouette`, `fx_far_town_base` — all of which serve the *west*
(upstream) view and appear only in boatyard, waterfront and north-landing.

So Dellhollow has a fully dressed west vista, a fully dressed but invisible
north wall, a **placeholder south wall that fills a fifth of most frames**, and
no east wall at all.

---

## Finding 2 — the two genuine voids are both the missing east (downstream) closure

`cottage-steps` (16.26%) and `lockfive` (19.96%) are the only real leaks, and
they are the same hole seen from two angles.

| camera | leak | leak rays | screen region | azimuth | elevation |
|---|---|---|---|---|---|
| cottage-steps | 16.26% | 4,662 | left 27% of frame, top 67% | 323-338 deg | -17.2 .. +1 deg |
| lockfive | 19.96% | 5,722 | left half, top 48% | same fan | -10.7 .. +2 deg |

73% and 54% of those rays point *downward* — a downward ray that hits nothing in
a valley town is unambiguously a hole, not sky.

**Where the world ends:** `lf_ground` stops at x = 112.1, `lf_riverbed_tail` at
x = 131.0, `cliff_town` at x = 135.0, `cliff_far` at x = 150.0. East of that
there is nothing at all. The leak rays fly out over the downstream gorge and
never come back.

**The fix, specified exactly.** I traced all 10,384 leak rays against candidate
closure planes:

| plane | rays caught | required extent |
|---|---|---|
| x = 140 | **10,384 / 10,384 (100%)** | y -4 .. 50, z -12 .. 19 |
| x = 150 | 100% | y -11 .. 52, z -16 .. 20 |
| x = 165 | 100% | y -23 .. 54, z -21 .. 22 |

**A single wall at x = 140 spanning y -8..54 and z -14..22 closes both leaks
completely.** 62 x 36 m. That is the entire geometric requirement for the void
problem — one panel.

`shelf-east`'s 22-pixel hairline (0.08%, azimuth 181-182 deg, landing at
x -30..-53, y 12-14) is a separate, trivial gap: the ray passes *under*
`fx_ridge_upstream`, whose bbox bottoms out at z = -9 while the ray is at z ≈ -24
by then. Extending that ridge's toe down 15 m closes it. Not worth its own pass;
fold it into the vista commit.

---

## Finding 3 — the resolution gradient, quantified

The town's *own* terrain is fine. The gradient is a cliff between two
populations, not a continuum:

| surface | verts | polys | edge m | typical px/edge | verdict |
|---|---|---|---|---|---|
| `yard_ground` | 4,176 | 4,042 | 0.42 | 32 | excellent |
| `lf_ground` | 6,380 | 6,210 | 0.54 | 41-63 | excellent |
| `wf_ground` | 3,102 | 2,990 | 0.58 | 43-71 | good |
| `gate_cliffface` | 4,526 | 4,524 | 0.60 | 43 | good |
| `shelf_cliffface` | 3,968 | 3,966 | 0.68 | 45-76 | good |
| `lk_bankface` | 1,136 | 852 | 0.55 | 69 | good |
| `shelf_ground` | 7,906 | 7,902 | 0.61 | 76 | good |
| `seam_bank` | 560 | 507 | 0.88 | 91 | acceptable |
| `gate_ground` | 4,774 | 4,766 | 0.88 | 70-156 | **marginal at shelf-west (156)** |
| `qm_stair_underworks` | 192 | 144 | 1.63 | **189-204** | **visibly faceted** |
| `wv_hut_*` (weave huts) | 152-248 | 106-178 | 1.30-1.76 | **118-233** | **visibly faceted at close range** |
| **`cliff_town`** | **8** | **6** | **74.00** | **2,664-5,495** | **placeholder** |

Ranked by visual cost (screen-% x coarseness), the offenders in order are:

1. **`cliff_town`** on ten cameras — 3-23% of frame at 2,664-5,495 px/edge. Nothing
   else is close.
2. **`gate_ground`** at shelf-west — 13.5% of frame at 156 px/edge, seen from 13 m.
   This is the one *town* surface that is genuinely under-resolved at its
   closest camera; every other ground mesh holds up.
3. **`qm_stair_underworks`** — 5.0% at quay-east (204 px/edge, 19 m) and 3.8% at
   loop-stairs (189 px/edge, 21 m). 192 verts holding a 20 m stair soffit.
4. **The weave huts' walls** — 2.5-7.0% per frame at 118-233 px/edge across
   cottage, lockhead, crossing, lockfive, quay-west. These are the `lf_*` kit's
   kitbash boxes and they read as boxes wherever a camera stands inside 25 m.

Everything else in the town measures under 100 px/edge and needs nothing.

---

## The build plan

### Region 1 — replace `cliff_town` (the whole point of this pass)

Not "extend" — **replace**. Delete the 8-vertex box, build a real south wall on
the same footprint with the same silhouette, using **`mat_rock_farwall`** (the
textured far-wall material already in the file, currently used by `cliff_far`
and `cliff_far_toe`, and already glTF-clean).

Target detail: **60-80 px/edge**, matching `gate_cliffface`'s 43 and
`shelf_cliffface`'s 45-76 so that no camera can tell where the built cliff stops
and the vista starts. At the measured viewing distances that means edge lengths
of 0.9-1.6 m, tiered by how close a camera gets:

| tier | world extent | seen by | d_mean | edge m | quads | verts |
|---|---|---|---|---|---|---|
| **A** | x 60..116, z 6..26 | lockhead, loop-stairs, quay-east, cottage, weave, crossing | 33-59 m | 1.1 | ~930 | ~1,000 |
| **B** | x -25..20, z -5..35 | gate | 39-69 m | 1.4 | ~930 | ~1,000 |
| **C** | x 38..62, z -5..25 | quay-west, deep-stairs | 47-74 m | 1.5 | ~330 | ~370 |
| **D** | x 110..137, z 0..20 | cottage-steps, lockfive | 59-78 m | 1.6 | ~210 | ~240 |

**Total ~2,400 quads / ~2,600 vertices** — smaller than `shelf_ground` alone.
This is a cheap fix for the single largest visual defect in the town.

Shape brief: it must not be a plane. The tier-A patch is the backdrop for six
cameras, so it needs the same language as the built faces — stepped ledges,
a talus toe around z 6-9, two or three vertical fissures to break the 56 m run,
and the moss overlay (`(0.09,0.16,0.05)` in `Mix.003.B`, already in
`mat_rock_farwall`) doing its up-facing work. Tier B is the gate's backdrop and
carries the most vertical range (40 m); give it one strong diagonal strata line.
Tiers C and D are pure silhouette at 47-78 m and want profile, not detail.

Optional and cheap: add a **fourth haze card** on the south side, mirroring
`fx_haze_mid`, at y ≈ 8-12 spanning the tier-A/B run. The west vista's read
comes as much from its three haze layers as from its ridges, and the south wall
currently has none — which is a second reason it reads flat.

### Region 2 — the east closure

One wall at **x = 140, y -8..54, z -14..22**, `mat_rock_farwall`, edge ~2.0 m
(it is 60-100 m from both cameras and is pure silhouette): **~560 quads**. Add
a haze card in front of it at x ≈ 128 to give the downstream gorge depth, and
extend `fx_ridge_upstream`'s toe from z -9 down to z -25 to close shelf-east's
22-pixel hairline.

### Region 3 — targeted resolution repair

Only three, and only where a camera is close enough to care:

| target | current | action | scope |
|---|---|---|---|
| `qm_stair_underworks` | 192 v, 204 px/edge at 19 m | subdivide + displace the soffit to ~0.6 m edges | ~700 verts |
| `gate_ground` (west lobe only, x 1-15) | 0.88 m edges, 156 px/edge at 13 m from shelf-west | local subdivide to ~0.45 m | ~2,000 verts |
| `wv_hut_*` walls (9 huts) | 1.3-1.76 m edges | one bevel/loop-cut pass on wall panels only; do **not** touch roofs — they carry the four new shingle variants and their `Col` | ~1,800 verts total |

Everything else stays. Subdividing surfaces already under 100 px/edge buys
nothing and costs bake time.

---

## Execution plan

**Scope and effort**

| phase | work | verts added | effort | independent commit |
|---|---|---|---|---|
| C1 | build the south wall (tiers A-D), swap `m_rock` -> `mat_rock_farwall`, delete `cliff_town` | ~2,600 | 5-7 h | yes |
| C2 | east closure wall + south haze card + upstream toe extension | ~600 | 1-2 h | yes |
| C3 | three targeted resolution repairs | ~4,500 | 2-3 h | yes |

**~9-12 h, ~7,700 vertices** on a town that already carries ~1.75M across 1,753
meshes. Render-cost impact is negligible; the visual impact is the largest
available in this tranche.

**Risk**

* **Medium-high on C1, and it is a composition risk, not a technical one.**
  Replacing 3-23% of ten frames changes ten compositions at once. Mitigation:
  build tier A first, bake **lockhead** alone (the 22.64% worst case), and put
  that single frame through a taste gate before building B/C/D. Do not build all
  four tiers before seeing one.
* **Silhouette regression.** `cliff_town`'s top edge is currently a dead-straight
  horizon at z = 37 in several frames. A modelled rim will cut a different
  skyline and may crowd the frame tops of lockhead / quay-east / cottage, whose
  cliff_town patches reach z 19-25. Gate: assert the new wall's silhouette stays
  below each camera's current cliff_town upper screen bound + 5%.
* **Low on C2.** The east wall is invisible to 15 of 17 cameras and pure
  background in the other two.
* **Low on C3.** Local subdivision of existing meshes; walk QA covers it.
* **Collision / walk.** None of this geometry is walkable and none of it is
  inside a walk corridor. `walk QA` must come back bit-identical; if it does not,
  the new wall is intersecting a walk surface and the tier bounds are wrong.

**Gates needed**

1. `walk QA` bit-identical (all three phases).
2. `tools/master_glb_survival.py` — 0 white primitives. `mat_rock_farwall` is
   textured with an absent `baseColorFactor`, which is *healthy* per finding
   219; do not "cure" it.
3. `tools/master_glb_albedo.py` on `mat_rock_farwall` before and after.
4. `tools/look_golden.py` — the blend must still agree with the solved file's
   exposure. This pass touches no light, so it must not move.
5. **Sky-leak re-probe**: re-run `tally2.py` and assert leak < 0.5% on every
   camera (currently 19.96% and 16.26%).
6. **Resolution re-probe**: re-run the px/edge audit and assert no visible
   surface over 250 px/edge above 1% screen area.
7. Taste gate on **lockhead** after tier A; full taste gate on
   **lockhead, gate, cottage-steps, quay-west** after C1+C2.

**Re-bake**

* **C1 forces a re-bake of 10 cameras**: gate, loop-stairs, quay-west,
  quay-east, lockhead, cottage, crossing, weave, deep-stairs, cottage-steps.
  (lockfive sees cliff_town at 0.04% — below the noise floor — but is already in
  the C2 set.)
* **C2 forces cottage-steps, lockfive** (and shelf-east, for 22 pixels — batch
  it rather than reason about it).
* **C3 forces shelf-west, quay-east, loop-stairs, cottage, lockhead, crossing,
  lockfive, quay-west**.

Union: **15 of 17.** Only `boatyard` and `fishdock` are untouched by any phase.
**Bake all 17.** Two frames is 7 minutes of GPU; a partially re-baked shot list
where two plates were rendered against a different south wall is a continuity bug
that will not be found until someone walks the town.

**Ordering.** C1+C2 before `pops-of-color.md`. That document's budget is
measured against frames in which up to 22.6% of the pixels are about to change.

---

## AS BUILT — 2026-07-30, tranche-2 custodian

This document was written read-only. Everything above held under measurement, but
**four things could only be learned by rendering**, and three of them change the
text rather than the numbers. The build is `tools/t2_cliff_south.py` (C1),
`tools/t2_cliff_east.py` (C2) and `tools/t2_cliff_res.py` (C3); the ratified
deviations are recorded here so the plan stays the truth.

### 1. `mat_rock_farwall` is not a rock material — do not use it at 33 m

Tier A was built in it exactly as specified above and probe-rendered at lockhead.
It came back a **cold blue-grey slab** standing ten metres from warm-tan
`lf_ground`. Reading the tree afterwards says why:

| material | the tint it applies | authored for |
|---|---|---|
| `mat_rock_farwall` | Mix.001 @ 0.60 -> (0.33, 0.35, 0.45), then Mix.002 @ 1.0 -> (0.30, 0.295, 0.30) | `cliff_far` at y 80-99 m |
| `mat_rock` | Mix.001 @ 1.0 -> (0.72, 0.72, 0.72) neutral | the town's terrain |
| `mat_gate_cliff` / `mat_shelf_cliff` | as `mat_rock`, plus a 0.85 distance tint | the built faces at 13-20 m |

It is an **atmospheric-perspective** material, not a rock material. Baking
recession into the albedo of a wall thirty metres from the camera is the opposite
of this document's own stated goal. **The south wall is built in
`mat_rock_townwall` — a copy of `mat_shelf_cliff` — and the recession comes from
the C2 south haze card**, which section "Region 2" already proposed as optional.
It is not optional; it is now the only source of depth on that wall.

`mat_rock_farwall` *is* still correct for the **east closure** at 60-100 m, and
that is what it wears.

### 2. NOTHING in Dellhollow's rock kit is UV-mapped, and that is the town's look

Every rock material runs `Texture Coordinate.Object -> Mapping -> Image Texture`,
and **a 2D image texture fed a 3D vector uses only its X and Y**. On a wall
standing in the x-z plane that means **the rock pattern does not vary with
height** — the texture's second axis is the wall's own *depth*. Every cliff face
in town is therefore a set of vertical streaks, and that is where the house look
came from: by accident, then kept.

At `mat_gate_cliff`'s Mapping scale of 1.05 the streak period is ~0.95 m and it
reads as striation. At `mat_rock`'s 0.17 it is 5.9 m, and crossed with the new
wall's relief it rendered **a grid of six-metre rectangular blocks**. Fixed by
rotating the derived material's Mapping 90 degrees about X so the rock maps to
x-z, at the built faces' own scale.

**Filed for a future town-wide decision (NOT done here):** `gate_cliffface`,
`shelf_cliffface`, `cliff_far`, and every `lf_`/`wf_`/`yard_` rock surface are
all mapped this way. Re-mapping them is a taste decision for the user, in the
same bucket as the moss-overlay literal `(0.09, 0.16, 0.05)` that
`house-variety-design.md` also deferred.

### 3. No periodic ledges — a regular vertical period reads as machining

The shape brief's "stepped ledges", built literally as a sawtooth in z, rendered
as **a stacked quarry**: a regular vertical period under the ratified 53-degree
raking key cuts hard-edged terraces, and terraces read as machined. Replaced with
**seven incommensurate plane-wave octaves plus two horizontal strata biases**,
keeping the talus toe at z 5-10 and the six vertical fissures. The strata biases
do double duty: they are also the crosscut that stops the vertical texture
streaks smearing at the nearest band.

### 4. `from_pydata()` leaves every polygon flat

A 1 m quad at 35 m is a 68-pixel facet with one constant normal, and the frame
came back as a grid of hard-edged rectangles for that reason alone. The new wall
is smooth-shaded.

This also **reframes finding 3 above**, and the reframing is worth keeping:
**every mesh in Dellhollow is flat-shaded** — `gate_cliffface` 0/4,524 smooth
polygons, `lf_ground` 0/6,210, `shelf_ground` 0/7,902, `yard_ground` 0/4,042, all
nine weave huts 0/N. The town buys its smoothness with *tessellation*. So
`px_per_edge` is not a proxy for facet size, **it is facet size** — and
subdividing a surface that is already planar buys nothing at all. Each C3 repair
therefore pairs refinement with the thing that makes refinement visible
(displacement on the two terrain surfaces, a 6 cm chamfer on the hut walls).

### What actually landed

| object | verts | polys | extent | material |
|---|---|---|---|---|
| `cliff_town_a` | 2,255 | 2,160 | x 58..112 | `mat_rock_townwall` |
| `cliff_town_b` | 1,558 | 1,480 | x -25..20 | " |
| `cliff_town_c` | 615 | 560 | x 38..58 | " |
| `cliff_town_d` | 696 | 639 | x 112..135 | " |
| `cliff_town_west` | 286 | 239 | x -35..-25 | " |
| `cliff_town_mid` | 410 | 360 | x 20..38 | " |
| `cliff_east_closure` | 640 | 589 | x 140, y -8..54, z -14..22 | `mat_rock_farwall` |
| `fx_haze_south` | 8 | 6 | y -2.4..0.3 over the whole run | `mat_haze_south` |
| `fx_haze_east` | 8 | 6 | x 124..130 | `mat_haze_east` |
| `fx_ridge_upstream_skirt` | 8 | 6 | under the ridge, to z -25 | `mat_rock_far` |

**C1 is 5,820 verts / 5,438 polys**, not the ~2,600 estimated above: the estimate
counted only the tier rectangles inside the visible z band, but the placeholder
is *deleted*, so the wall has to close its whole footprint or every uncovered
metre becomes a new sky leak. The two extra "filler" bands (`west`, `mid`) are
that closure. **C3 is +13,193 verts.**

Two structural choices worth keeping:

* **One shared z-row list across all six patches**, so adjacent patches place
  bit-identical vertices on their shared column. Per-tier rows would have made
  T-junctions, and a T-junction on this wall is a pinhole to the world
  background — the exact defect being repaired.
* **Clearance is ray-cast, not assumed.** Every vertex is measured against the
  town before it is placed, because `gate_cliffface` already reaches y = -0.6,
  i.e. *inside* the placeholder's own volume; a naive sheet at y = -0.35 would
  have poked through the gate's own cliff.

The silhouette gate is vacuous by construction: the top row stays at z = 37.0,
the placeholder's own horizon, with a cap strip running back from it, and no
solved camera stands above z = 36.5.
