# Pops of colour — a measured placement plan for all 17 cine cameras

**Status:** design note, tranche-2 direction A. Written read-only against
`tools/blends/dellhollow-master.blend` while the 17-camera bake held the GPU.
No master edits, no renders. Method and vocabulary inherit from
`docs/plans/house-variety-design.md`.

The user's note: cliff dominance is fine and expected, but *"well placed
pops… even 5-10% of the overall pixels can change a lot of the visual
identity."*

Everything below is measured, not estimated. Three read-only Blender passes
were run: a **224x128 per-pixel ray tally** of all 17 solved cameras recording
the hit object (`tally.py`), the same tally recording the hit **material**
(`tally3.py`), and a **placement probe** that projects a proposed rectangle into
every camera and ray-casts its 25 sample points for occlusion (`t2_place.py`).
So every screen-% in this document is a number the town produced, not one I
chose.

---

## Part 1 — Where the colour actually is today

### The measurement

"Chromatic pop" is defined narrowly and on purpose: **pixels whose hit material
is a painted panel, cloth, awning, flag or produce**. Timber, roofs, rock and
deck planking are excluded even where they are technically saturated, because a
warm brown plank is the thing we are trying to break up, not an instance of
breaking it up. (A looser filter that counts any saturated material returns
12-53% per frame and is useless — it just re-measures the timber.)

| camera | chroma % | top contributors |
|---|---|---|
| shelf-east | **12.65%** | madder 3.70, bone 3.42, ochre 1.32, teal 1.16, shelf_cloth 1.14 |
| quay-west | **9.01%** | ochre 1.86, madder 1.24, rust 1.21, qm red 1.05, teal 0.84 |
| loop-stairs | **8.82%** | madder 4.22, ochre 1.65, qm_cloth 0.60, qm blue 0.45 |
| shelf-west | **5.71%** | rust 2.71, teal 1.26, green 0.67, qm red 0.56 |
| quay-east | **5.44%** | madder 3.39, qm ochre 0.88, qm_cloth 0.63 |
| deep-stairs | 2.84% | qm red 0.55, qm bone 0.41, qm ochre 0.33 |
| weave | 2.32% | madder 1.27, qm ochre 0.35 |
| boatyard | 2.27% | paint_blue 0.80, paint_red 0.65, flags 0.54 |
| lockhead | 1.40% | qm ochre 0.63, qm red 0.51 |
| gate | **0.61%** | teal 0.27, green 0.14, awning 0.06 |
| waterfront | **0.59%** | paint_red 0.31, paint_blue 0.17 |
| cottage | **0.17%** | qm ochre 0.11 |
| fishdock | **0.16%** | paint_blue 0.10, paint_red 0.06 |
| crossing | **0.11%** | qm red 0.06 |
| north-landing | **0.03%** | paint_red 0.02 |
| cottage-steps | **0.00%** | — |
| lockfive | **0.00%** | — |

Town mean: **3.07%**.

### The finding that changes the brief

The brief named **gate and quay-west** as the two flagged brown shots.

* **gate is right** — 0.61%, one of the three brownest frames in town.
* **quay-west is wrong** — at **9.01%** it is the *second most colourful frame
  in Dellhollow*, behind only shelf-east. It reads brown for a different
  reason: 45.4% of its pixels are rock and 8.4% is the flat grey vista slab
  (see `cliff-completion.md`). Adding paint to quay-west would be spending the
  taste gate's credit on a frame that already passes this test.

The actual brown belt is **the eastern half of the town** — the six Lockfoot
and downstream cameras: **cottage-steps 0.00%, lockfive 0.00%, north-landing
0.03%, crossing 0.11%, fishdock 0.16%, cottage 0.17%.** Six of seventeen shots
have *essentially no chromatic pixel at all*. Every painted thing in Dellhollow
lives west of x≈65: the shelf shop row, the quay market, the boatyard. The
Lockfoot district was built with the `lf_*` kit and got timber, stone and
shingle and nothing else.

That is the plan's centre of gravity, and it is not where the brief pointed.

### Two free wins found in the census

1. **The awnings are grey.** `qm_awning_2.001` is 100% neutral `(0.60,0.57,0.54)`
   by loop count; `qm_awning_0/1/3/4` and `shelf_awning_1/3` are 12 grey loops
   to 9 coloured ones. Nine awning objects already exist, already sit in frame,
   and are **more than half unpainted**. Recolouring their `Col` is a vertex-colour
   edit with zero new geometry (the `lf_matte`/awning materials drive Base Color
   from `Col`, the finding-211 shape).
2. **The Lockfoot bunting is 89% rope.** `lf_bunting_0..3` are 810 loops each, of
   which **720 are the brown line colour `(0.42,0.35,0.25)`** and only 90 carry
   flag colour. They are also 0.08 m wide, hung at z 0.16-1.64 — down at the
   waterline where nothing sees them (measured contribution: 0.045% at lockfive,
   0.017% at north-landing). They should be re-strung at deck height and
   re-coloured, not duplicated.

---

## Part 2 — Calibration: what one dressing element is worth

Measured from objects already in the file, so the estimates below are anchored,
not modelled:

| element | measured screen-% | conditions |
|---|---|---|
| bunting run + rope line, 23 m | **1.20%** (0.60 cloth + 0.60 line) | loop-stairs / quay-east, 20-30 m |
| bunting run, 25 m | **1.38%** | shelf-east, 12-25 m |
| same run seen from 48 m | **0.12%** | weave |
| one awning, 2.5 x 1.0 m | **0.06-0.25%** | 16-30 m |
| laundry line, 33 m of cloth | **0.10-0.37%** | fishdock/weave, 30-45 m |
| one painted building panel | **1.2-4.2%** | shelf paints at 14-30 m |
| painted boat hull | **1.06%** | `barge_mid_pool` at boatyard |

**The rule of thumb this produces:** screen-% of a face-on panel is simply
`area_m2 / (2 d tan(fov/2))^2 / aspect`. At Dellhollow's 35 deg vertical FOV the
frame is `20.8 x 36.4 m` at 33 m and `12.6 x 22.1 m` at 20 m — so **one square
metre of face-on colour is worth 0.13% of frame at 33 m and 0.36% at 20 m.**
To move a frame by 5 points you need roughly **38 m² of colour at 33 m, or 14 m²
at 20 m.** That is why awnings and hulls beat bunting: bunting is 60% air.

---

## Part 3 — The placement table

Every row below was projected into all 17 cameras and occlusion-tested with 25
rays. `screen-%` is *after* occlusion. `scale` is the recommended size relative
to the probed rectangle (some probes overshot and are trimmed).

Palette column uses the six-accent storybook set completed by the house-variety
pass, plus the market and pennant colours already in the file:

| name | material | sRGB | H/S/V |
|---|---|---|---|
| rust | `mat_shelf_paint_rust` | `#BE8B78` | 13 / 0.64 / 0.52 |
| madder | `mat_shelf_paint_madder` | `#B47872` | 4 / 0.63 / 0.46 |
| ochre | `mat_shelf_paint_ochre` | `#CEB688` | 36 / 0.60 / 0.62 |
| bone | `mat_shelf_paint_bone` | `#D9D4C5` | 43 / 0.20 / 0.70 |
| teal | `mat_shelf_paint_teal` | `#88A7B0` | 196 / 0.43 / 0.44 |
| slate | `mat_shelf_paint_slate` | `#8694AB` | 219 / 0.41 / 0.41 |
| sage | `mat_shelf_paint_green` | `#94A994` | 120 / 0.25 / 0.40 |
| market red | `mat_qm_paint_red` | `#C88675` | 9 / 0.69 / 0.58 |
| market blue | `mat_qm_paint_blue` | `#86A3B4` | 204 / 0.48 / 0.46 |
| pennant red / blue / ochre / green | `mat_flag_*` | `#853130` `#3B5F7F` `#97773D` `#426646` | high-chroma, low-value |
| pumpkin | `mat_pumpkin` | `#B46626` | 16 / 0.96 / 0.46 |

### 3a. Gate district — target +7.1 (0.61% -> 7.7%)

| id | what | world (x, y, z) | size m | cameras (screen-%) | palette |
|---|---|---|---|---|---|
| G7 | second bunting run, winch -> gatehouse | (15.0, 6.5, 26.6), 18 m span | 18 x 0.4 | gate **1.11** | pennant set, 4 colours |
| GB3 | guild banner on cliff face, east | (20.5, 2.3, 29.0) | 1.6 x 4.4 | gate **1.09**, shelf-west 0.11 | madder |
| GB4 | big tarpaulin over porters' yard | (10.0, 7.0, 25.2) | 4.8 x 4.0 | gate **0.74** | ochre |
| GB2 | guild banner on cliff face, centre | (13.0, 2.3, 29.5) | 1.6 x 4.4 | gate **0.69** | slate |
| GB1 | guild banner on cliff face, west | (6.5, 2.3, 29.0) | 1.6 x 4.4 | gate **0.56** | teal |
| GB5 | toll-road awning row | (22.0, 7.5, 25.0) | 4.4 x 3.2 | gate **0.49** | rust |
| G6 | tarpaulin over cargo stack | (6.5, 10.5, 24.9) | 2.6 x 2.6 | gate **0.44** | bone |
| G2 | awning, porters' yard north | (8.0, 9.0, 25.9) | 3.0 x 2.2 | gate **0.38** | market red |
| G3 | awning, toll table | (19.5, 5.5, 25.7) | 2.8 x 2.0 | gate **0.36** | teal |
| G4 | banner under the gate arch | (16.8, 4.2, 26.6) | 2.5 x 3.2 | gate **0.35** | pennant blue |
| G5 | painted gatehouse door | (11.5, 4.7, 25.5) | 1.2 x 2.2 | gate **0.30** | madder |
| G8 | flower baskets along gate cliff | (14.0, 2.2, 26.5), 14 m | 14 x 0.6 | gate **0.29** | pumpkin + sage |
| G1 | awning, porters' yard west | (4.5, 6.5, 25.9) | 3.0 x 2.2 | gate **0.27** | ochre |

The three cliff banners are the interesting move: `gate_cliffface` is **30% of
the gate frame** and is the largest single surface in that shot. Hanging cloth
*on* it is the only way to put colour into the part of the frame that is
actually brown. This is a real FF9 gesture, not a workaround.

### 3b. Lockfoot / weave district — serves the six brown eastern cameras

| id | what | world (x, y, z) | size m | cameras (screen-%) | palette |
|---|---|---|---|---|---|
| W1 | laundry line over drying decks (A) | (65.2, 26.0, 8.0) | 6.8 x 1.1 | lockfive **2.42**, fishdock 0.90, weave 0.82, crossing 0.52 | bone / teal / madder |
| W2 | laundry line over drying decks (B) | (65.2, 28.4, 8.0) | 6.8 x 1.1 | lockfive **2.12**, fishdock 1.00, weave 0.88 | ochre / slate |
| WV2 | awning on the drying decks | (65.0, 26.5, 7.9) | 5.2 x 4.0 | weave **1.89**, lockfive 1.81 | rust |
| W9 | laundry over the weave planking | (80.0, 23.0, 9.4) | 12 x 1.2, at 0.5 scale | crossing **1.64**, cottage-steps 1.53, cottage 1.44, lockfive 0.47 | mixed |
| W8 | painted gable, tenant shack | (69.9, 24.9, 3.6) | 4.4 x 3.0, at 0.6 | crossing **1.51**, fishdock 0.49, lockfive 0.41 | market blue |
| W5 | flower boxes on the weave-deck rail | (86.0, 23.5, 8.1), 10 m | 10 x 0.6, at 0.6 | cottage-steps **1.06**, cottage 1.05, crossing 0.77 | pumpkin + sage |
| LH6 | painted gables, weave huts (upper) | (74.6, 20.2, 11.3) | 4.4 x 1.8, at 0.7 | crossing **1.13**, lockfive 0.64, cottage 0.64 | madder / ochre |
| LH5 | shutters at hut roofline | (73.5, 19.8, 11.0), 10 m band | 10 x 0.9, at 0.7 | crossing **0.96**, lockhead 0.97, lockfive 0.61 | teal / rust |
| W7 | keeper's-cottage flower boxes | (91.7, 19.7, 10.5) | 4.0 x 0.6 | cottage **0.67**, crossing 0.39, cottage-steps 0.40 | pumpkin |
| W4 | painted shutters, weave hut row | (71.5, 19.7, 7.6), 10 m band | 10 x 0.9 | crossing 0.41, lockfive 0.41, fishdock 0.27 | slate / madder |
| W6 | keeper's-cottage painted door | (91.5, 19.6, 9.0) | 1.1 x 2.2 | cottage 0.40, crossing 0.20 | rust |
| W3 | painted doors, weave hut row | (71.5, 19.7, 4.4) | 10 x 2.2 band | crossing 0.32, lockfive 0.13 | six-accent, one per hut |

### 3c. Lock head — target +7.6 (1.40% -> 9.0%)

| id | what | world (x, y, z) | size m | cameras (screen-%) | palette |
|---|---|---|---|---|---|
| LH1 | awning over the lockhead station | (82.0, 15.6, 16.1) | 3.4 x 2.2 | lockhead **2.04**, cottage 0.15 | ochre |
| LH3 | flower boxes along the lockhead rail | (73.5, 17.4, 15.4), 17 m, at 0.5 | 17 x 0.6 | lockhead **1.85**, crossing 0.87, cottage 0.52, quay-east 0.14 | pumpkin + sage |
| LH2 | bunting along the lockhead rail | (73.5, 17.0, 16.0), 17 m, at 0.5 | 17 x 0.4 | lockhead **1.45**, crossing 0.67, cottage 0.39 | pennant set |
| LH4 | painted cargo on the lock deck | (70.0, 16.2, 15.9) | 3.6 x 1.6, at 0.6 | lockhead **0.89**, crossing 0.61, quay-east 0.23 | market red / blue |

### 3d. North landing / downstream — target +7.9 (0.03% -> 7.9%)

| id | what | world (x, y, z) | size m | cameras (screen-%) | palette |
|---|---|---|---|---|---|
| N1 | awning cluster on the pier | (105.5, 27.0, 1.4) | 7.2 x 4.4, at 0.5 | north-landing **2.78**, cottage-steps 0.64 | rust / ochre / teal |
| N5 | cargo cloth on the moored barge deck | (103.0, 33.6, -3.0) | 9 x 2.6, at 0.5 | north-landing **2.09**, cottage-steps 0.49 | bone + market red |
| N2 | bunting across the landing | (105.5, 27.0, 2.4), 11 m, at 0.7 | 11 x 0.44 | north-landing **1.03**, cottage-steps 0.45 | pennant set |
| N4 | painted barge hull strake | (103.0, 32.4, -3.3) | 9 x 1.7 | cottage-steps **0.79**, north-landing 0.46 | madder |
| N3 | painted cargo stack | (104.5, 25.5, -0.1) | 3.0 x 1.7 | north-landing **0.66**, cottage-steps 0.37 | market blue |
| N6 | drying nets on frames | (99.5, 24.2, 0.7) | 4.4 x 2.4, at 0.7 | cottage-steps **0.71**, north-landing 0.59 | ochre |
| L1 | banners on the Lock Five crest gate | (86.9, 30.4, 3.2) | 2.8 x 2.6, at 0.7 | cottage-steps **1.08** | pennant blue + red |
| L2 | painted panel, keeper's station | (91.8, 27.6, 3.0) | 5.2 x 4.0, at 0.5 | cottage-steps **1.42**, crossing 0.41 | slate |

### 3e. Waterfront / fish dock / boatyard

| id | what | world (x, y, z) | size m | cameras (screen-%) | palette |
|---|---|---|---|---|---|
| F1 | awnings over the fish-dock clutter | (46.0, 23.7, 2.7) | 5.2 x 2.2 | waterfront **3.19**, fishdock 0.51 | market red / ochre |
| F4 | laundry over the waterfront stair | (44.5, 21.0, 5.2) | 5.2 x 1.2 | waterfront **2.32**, fishdock 1.32, deep-stairs 0.69 | bone / teal |
| DS2 | painted strake on the hero hull | (27.9, 28.3, 4.6) | 7.2 x 2.4, at 0.55 | boatyard **3.56**, deep-stairs 1.64 | madder |
| B1 | canvas over the hero hull | (27.5, 29.4, 6.5) | 6 x 2, at 0.7 | boatyard **2.16**, deep-stairs 0.90 | bone |
| WV3 | painted panel, weave-north hut 2 | (50.9, 19.6, 8.5) | 5.2 x 2.8, at 0.7 | fishdock **1.64**, deep-stairs 0.82 | teal |
| DS1 | tarps over the boatyard stock | (28.0, 24.0, 3.2) | 4 x 3.6 | boatyard **1.42** | ochre |
| DS4 | laundry over the yard | (31.5, 22.0, 6.5) | 5.2 x 1.2 | deep-stairs **1.09**, waterfront 0.42 | rust / bone |
| F5 | painted net floats on the fish stage | (59.0, 34.0, 1.6) | 6 x 3, at 0.6 | fishdock **0.91** | market red + pumpkin |
| F2/F3 | two painted skiffs in the mid pool | (48.0, 32.0, 0.5), (56.0, 35.5, 0.5) | 5 x 1.6 each, at 0.7 | fishdock **0.77 + 0.60** | slate, rust |
| DS3 | painted boatwright shed doors | (25.5, 27.0, 3.4) | 3.2 x 3.0 | deep-stairs 0.69, boatyard 0.46 | market blue |
| WV1 | laundry over the quay deck | (53.0, 18.5, 15.6) | 9 x 1.2, at **0.33** | quay-east **3.63**, weave 0.67, quay-west 0.56, loop-stairs 0.23 | mixed |

WV1 is the one row that must be built at the stated scale: probed full size it
adds **10.99%** to quay-east alone, because it sits 11 m from that camera.

---

## Part 4 — The resulting budget

| camera | now | added | after | |
|---|---|---|---|---|
| gate | 0.61% | +7.06 | **7.67%** | on target |
| shelf-west | 5.71% | +0.11 | **5.82%** | already fine, left alone |
| shelf-east | 12.65% | 0 | **12.65%** | already over, left alone |
| loop-stairs | 8.82% | +0.23 | **9.05%** | on target |
| quay-west | 9.01% | +0.72 | **9.73%** | on target |
| quay-east | 5.44% | +4.11 | **9.55%** | on target |
| lockhead | 1.40% | +7.62 | **9.02%** | on target |
| cottage | 0.17% | +5.62 | **5.79%** | on target |
| crossing | 0.11% | +10.48 | **10.59%** | at ceiling |
| weave | 2.32% | +7.06 | **9.38%** | on target |
| deep-stairs | 2.84% | +6.22 | **9.06%** | on target |
| boatyard | 2.27% | +7.60 | **9.87%** | on target |
| waterfront | 0.59% | +6.70 | **7.29%** | on target |
| fishdock | 0.16% | +9.23 | **9.39%** | on target |
| cottage-steps | 0.00% | +9.15 | **9.15%** | on target |
| lockfive | 0.00% | +9.61 | **9.61%** | on target |
| north-landing | 0.03% | +7.88 | **7.91%** | on target |

Every frame lands in **5.8-12.7%**, and every number is the sum of
occlusion-tested projections rather than a wish. Ceiling rule for execution:
**11%** — if a frame exceeds it after the build, halve the largest single
contributor rather than deleting rows, because coverage across many small
objects is what makes it read as a lived-in town instead of a paint splash.

---

## Part 5 — Craft rules

1. **No new colours.** The palette table above is closed. Twelve hues already
   exist in the file and the six-accent set was completed two commits ago; a
   thirteenth would be a taste decision this pass has no mandate for.
2. **Value discipline, as in the roof pass.** Keep every added element's
   luminance inside the band the golden key already unifies. The pennant
   materials sit at V 0.14-0.31 and the paints at V 0.40-0.71; use the *paints*
   for anything larger than 2 m² and the pennants only for cloth strips, or
   large low-value banners will read as holes.
3. **Neighbour separation, as in the roof pass.** Where a row of like objects
   gets painted (the weave hut doors, the shelf-style shutters), reuse the
   `sha1(name)` + 9 m neighbour-difference assignment from
   `house-variety-design.md`. Do not call `random()`.
4. **Recolour before you model.** The nine grey awnings and the four brown
   Lockfoot buntings are vertex-colour edits with zero geometry cost and should
   land first, so the modelled rows are measured against an already-improved
   baseline.
5. **glTF survivability.** All the paints, cloths and flags in the palette
   already ship correctly (`mat_flag_*` via export proxy, the tint kit via
   texture x absent-factor). Any NEW material must follow the same shapes and
   must not introduce a Principled-bearing Mix tree with a linked Base Color —
   finding 221. Re-colouring `Col` on `lf_matte`/awning objects is the
   finding-211 relink shape and is already proven here.
6. **Interiors.** `shelf_item_shop`, `shelf_weapon_shop`, `shelf_armor_shop`,
   `shelf_inn` and `qm_cookhouse` have interior scenes. **None of the buildings
   in the table above is one of them** — the Lockfoot huts, tenant shack,
   keeper's cottage and boatwright's shed have no interior scene — so this pass
   creates no exterior/interior divergence. Verified against `tools/*_int_build.py`.

---

## Execution plan

**Scope.** Four scripted phases, each its own commit and each independently
revertible:

| phase | work | new objects | effort |
|---|---|---|---|
| P1 recolour | repaint the 9 grey awnings + 4 Lockfoot buntings via `Col` | 0 | ~1 h |
| P2 flat dressing | all doors / shutters / gables / hull strakes / painted panels — these are **material-slot and `Col` edits on existing meshes**, not new geometry | 0-4 | ~3 h |
| P3 cloth | laundry lines, bunting runs, awnings, tarps, banners, cargo cloth | ~34 | ~4 h |
| P4 props | flower boxes, net floats, crates, two skiffs, barge cargo | ~18 | ~3 h |

Roughly **56 new objects, ~11 h**, all built by a parameterised script in the
established `tools/*_build.py` idiom (a table of rows -> meshes), so the table in
Part 3 *is* the source file.

**Risk.** Low-medium.
* *Occlusion drift* — the probe used 25 sample points per rectangle; a real
  awning with posts will occlude slightly more. Expect measured results 5-15%
  below the table. Mitigation: re-run `t2_place.py` against the built geometry
  before the bake and confirm each frame is >= 5%.
* *Silhouette clutter* — 56 objects in a town of 1753 is a 3% object-count rise
  and no meaningful render-time change, but cloth over walk surfaces can shadow
  the walkable deck. Gate: `walk QA` bit-identical (this pass adds no collision).
* *Value inversion* — the pennant materials are dark. Named in rule 2.

**Gates needed.**
1. `tools/master_glb_survival.py` — 0 white primitives (any new material).
2. `tools/master_glb_albedo.py` — every new material reports a real
   `factor x mean COLOR_0`, per finding 219 (do not read re-imported materials).
3. `walk QA` bit-identical — no new collision, no walk-surface change.
4. Re-run the placement probe post-build; assert every camera in [5%, 11%].
5. Taste gate on 4 probe renders: **gate, cottage-steps, lockhead, north-landing**
   — the three biggest movers plus the one the user named.

**Re-bake.** **All 17 cameras.** Sixteen of seventeen frames change by more than
0.1% of pixels; only shelf-east is untouched, and re-baking 16 vs 17 saves 3.5
minutes and risks a plate/depth mismatch. Bake the set.

**Ordering.** This pass should land **after** `cliff-completion.md`, not before.
Ten frames currently spend 3-23% of their pixels on a featureless grey slab; a
colour budget measured against that baseline would be measured against a frame
that is about to change. Cliff first, then re-run this document's probe, then
build.
