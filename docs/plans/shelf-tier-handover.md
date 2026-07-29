# SHELF TIER — handover to the next agent

Written by the GATE-POLISH agent immediately after committing the Gate Approach
v7 polish pass (`5e298a7`), while the gate seam was still fresh and the branch
blend was open. Everything below the "Measured" heading was read out of
`tools/blends/dellhollow-master-gate-branch.blend` at that commit, not
remembered and not inferred — it is the part of this document that would be
expensive for you to reproduce.

**Why you are reading this instead of a half-built district.** The queue asked
the gate agent to continue straight into the shelf tier, with an explicit
instruction to stop and hand over rather than push in with a degraded context.
The gate polish pass consumed a large part of that window on the render-inspect
loop (the flagged arrival frame took three camera sweeps and six rebuilds). A
five-landmark shop street needs the same loop five times over, and abandoning it
half-built would leave `SHELF_DISTRICT` in the blend disagreeing with
`shelf_build.py` — the one failure the branch protocol has no gate for. So: prep
and measurements here, none of the build started, blend untouched beyond the
gate work. Nothing is half-done.

---

## The district

Two parcels, one street. From `public/townmap/dellhollow.map.json`:

| parcel | bounds (x, y, z) | members | intent |
|---|---|---|---|
| `p-shelf-w` | 17.5..42.3, 1.0..13.5, 17.5..22.5 | inn, item-shop, weapon-shop | "Shop street, upper run: the Boatmen's Rest + item and weapon shops, signs and awnings, everyday lanterns" |
| `p-shelf-e` | 39.8..55.3, 4.5..13.5, 17.5..22.5 | armor-shop, shelf-homes | "Shop street, lower run: armor shop over the gorge, the Shelf homes, and the loop stair dropping toward the market" |

The parcels OVERLAP in x (39.8..42.3). Decide once, early, which side owns that
seam and write it down; the weapon-shop (x 35.7..39.9) is wholly in the west and
the armor-shop (42.2..46.4) wholly in the east, so the overlap is street, not
building.

Draft cameras the map already carries — treat as a starting point, not a
constraint (QA cameras are disposable scaffolding under the 2026-07-29 render
norm):
- `p-shelf-w`: yaw 140, pitch 20, viewHeight 11, persp — "Down the street
  eastward: inn front-left, shops receding, lanterns strung overhead, gorge air
  beyond the rail"
- `p-shelf-e`: yaw -155, pitch 21, viewHeight 10, persp — "Looking back westward
  up the street: armor shop cantilevered over the void, homes closing the row,
  second-stair head in frame"

Landmark positions (map, z=19.0 for all five): inn (22.0, 5.5), item-shop
(30.0, 9.0), weapon-shop (37.8, 5.5), armor-shop (44.3, 9.0), shelf-homes
(50.8, 9.0). Note the **zig-zag**: y alternates 5.5 / 9.0 / 5.5 / 9.0 / 9.0.
That is the street's character — it is not a straight row, and a facade line
drawn straight through it will fight the walk graph.

---

## Measured (branch blend @ 5e298a7)

### The tier's own surface
All five landmark pads sit at **z 18.92..19.04** — the shelf's walking surface is
**z = 19.0**. (The parcel's z bounds of 17.5..22.5 are the volume, not the floor;
do not build the ground at 17.5.)

95 `walk_`/`bar_` meshes fall in x 17..56, y 0.5..14, spanning z 14.30..24.91 —
that range includes the gate tier above and the market below, so filter by
height the way `gate_lib.Terrain` does (`HIGH_Z`), do not take the band whole.

Pads (all z 18.92..19.04, all 2.6 x 2.6 m — read them before placing anything,
manifest 93/111):

```
walk_pad_inn           x 20.70..23.30   y  4.20.. 6.80
walk_pad_item-shop     x 28.70..31.30   y  7.70..10.30
walk_pad_weapon-shop   x 36.50..39.10   y  4.20.. 6.80
walk_pad_armor-shop    x 43.00..45.60   y  7.70..10.30
walk_pad_shelf-homes   x 49.50..52.10   y  7.70..10.30
```

Edge families present: `walk_e_inn__*`, `walk_e_item-shop__*`,
`walk_e_weapon-shop__*`, `walk_e_armor-shop__*`, `walk_e_shelf-homes__*`,
`walk_e_valley-gate__*` (the stairs coming down from the gate), plus
`bar_e_shelf-homes__*` and `bar_e_valley-gate__*` rails.

### The blockout shells — your deletion manifest
Ten objects, five buildings, all identical in form (body 4.2 x 3.6 x 3.2 m from
z 19.00, hipped roof 22.15..23.55):

```
lm_inn_body          x 19.90..24.10  y 3.70.. 7.30  z 19.00..22.20   8 v
lm_inn_roof          x 19.77..24.23  y 3.27.. 7.73  z 22.15..23.55   5 v
lm_item-shop_body    x 27.90..32.10  y 7.20..10.80  z 19.00..22.20   8 v
lm_item-shop_roof    x 27.77..32.23  y 6.77..11.23  z 22.15..23.55   5 v
lm_weapon-shop_body  x 35.70..39.90  y 3.70.. 7.30  z 19.00..22.20   8 v
lm_weapon-shop_roof  x 35.57..40.03  y 3.27.. 7.73  z 22.15..23.55   5 v
lm_armor-shop_body   x 42.20..46.40  y 7.20..10.80  z 19.00..22.20   8 v
lm_armor-shop_roof   x 42.07..46.53  y 6.77..11.23  z 22.15..23.55   5 v
lm_shelf-homes_body  x 48.70..52.90  y 7.20..10.80  z 19.00..22.20   8 v
lm_shelf-homes_roof  x 48.57..53.03  y 6.77..11.23  z 22.15..23.55   5 v
```

`lm_cookhouse_body/roof` (x 38.30..42.63, z 14.00..18.55) is in the same x range
but belongs to the MARKET tier below. **It is not yours.**

Two things follow.

1. **Deleting `lm_inn_roof` clears a standing QA failure that is currently
   blamed on nobody.** `master_walk_qa.py --region 1.0,32.5,-1.0,13.0` reports
   1134/1139 rays, and all 5 blocked samples are `lm_inn_roof` poking up through
   the gate tier's walk surface. It is in the gate's transcript as a
   pre-existing master defect. When your real inn replaces that shell and stays
   under the ceiling below, the gate region goes to 1139/1139. Quote it — it is a
   real win and it is yours.
2. Write `tools/blends/districts/shelf_branch_deletions.json` the way the gate's
   is written, and make it **accumulate** rather than rewrite (manifest 115 —
   `gate_build.py` publishes an empty list on its second run otherwise, and that
   file is the one thing the merge custodian obeys literally). Copy the pattern
   from `gate_build.py`'s section 0; it is about 15 lines.

### THE CEILING — the number that governs this district
`gate_ground`'s eastern gallery plate has its **underside at z = 23.330** and its
top at 24.236 (806 verts east of x=19, measured). The gate's plate footprint is
derived from the walk graph and only exists where no walk lies within 2 m below
it, so it does not cover the whole tier — but wherever it IS overhead, nothing of
yours may rise above **23.33**, and you want clearance, not contact.

The blockout roofs top out at 23.55, i.e. **0.22 m ABOVE the gate plate's
underside**. They get away with it today only because the plate's plan footprint
happens to dodge them. Your real roofs must not rely on that. Practical rule:

> **Ridge <= 23.10 anywhere the gate plate is overhead; 23.55 is a blockout
> number, not a permission.**

That gives 4.1 m from the shelf floor (19.0) to the ridge — a generous single
storey with a loft, exactly the envelope the gatehouse ended up with. Two full
storeys do not fit under the gate. West of about x=19 the plate stops and the
gate's solid promontory takes over; east of the winch (x ~29.5) the gate's
ground ends entirely and you are free.

### Gate-district art that reaches into your band — build around it
```
gate_corbels     x 19.05..27.10  y  4.48..11.25  z 21.22..23.90
gate_winch_rope  x 27.06..30.04  y  4.48..23.63  z  2.18..26.89
gate_cliffface   x  1.20..31.44  y -0.60.. 2.58  z 19.00..42.30
gate_ground      x  1.20..29.42  y -0.30..12.28  z -8.35..28.72
```
- `gate_corbels` are the raking struts that carry the gallery plate. They hang
  down to **z 21.22** over the inn and item-shop. Your roofs and any signage
  under them have to clear that, and the corbels are a gift compositionally —
  the shop street runs under a corbelled gallery, which is a real thing.
- `gate_winch_rope` drops through x 27..30 from the winch head to the quay. It
  crosses your tier. Do not put a roof in it; read its verts the way the gate
  read `cargo_winch_foot` (manifest 94).
- `gate_cliffface` is the gate's backdrop veneer. It now runs to **x = 31.44** and
  down to **z = 19.00**. East of 31.44 the town's `cliff_town` blockout slab is
  bare again, and the gate's transcript records a confirmed leak at
  (56.8, 0.0, 29.2) seen from the gate's own arrival camera. **Continuing that
  veneer east across your parcels is yours**, and it will show in your frames
  long before it shows in the gate's. Findings 103 / 114: hold it above
  `cliff_town`'s top edge at z=37.0, press it flat to 0.10 m behind every
  building, modulate the crest, and set its east end by the shallowest ray that
  can see past it — not by where the ground stops.

### Lighting already on the tier
At the probe point (36.0, 7.0, 19.6) the shared rig delivers `SUN_key` (5 W sun),
`SKY_wash` (804 W area at 41.9 m), `RIM_gorge`, `CLIFF_BOUNCE`, `FILL_bounce`,
and — importantly — the Waterfront's chains are already close: `KEY_gorge_wf_deck_0..7`
(875.6 W, 48 deg, cutoff 48) at 34..56 m and `KEY_gorge_wf_cliff_0..5` (496.3 W)
at 32..49 m. The gate's own `KEYG_gate_0..4` (891.4 W, 24 deg, cutoff 46) are
only 20..25 m away.

So your `KEYSH_*` chain is being added into a tier that is ALREADY lit by three
districts' rigs. Two consequences:
- **Measure what you already have before you add anything.** `gate_light.py` has
  a working `existing(P, normal)` integrator (sun / area / spot / point) — copy
  it. Run it in `report` mode first.
- Your spill assertions need a THIRD target now: the Boatyard reference
  (20.5, 29.83, 1.0), the Waterfront boardwalk (58.0, 27.0, 1.4), **and the gate
  tier** (e.g. the arch at (16.7, 4.0, 24.2), whose west-facing value the gate
  solved to 1.8166 W/m2 = 66% of its sunlit top 2.7524). If your rig moves that
  number, you have re-valued accepted art.
- Level your chain against `KEY_slip`'s peak the way everyone else does: with
  `KEY_slip` at 5400 W / 48 deg / 28.55 m standoff, its peak on the Boatyard
  reference is **0.5271 W/m2**. The gate chain runs at 46% of it (891.4 W at 24
  deg). A street under a gallery, in shadow most of the day, probably wants
  rather less than that from the key and rather more from practicals.

---

## Style — what the three finished districts actually agreed on

Painted timber, bunting, ordinary lanterns. Concretely, and these are the exact
handles:

- **Materials are DERIVED, never flat.** `derive(src, name, scale, tint)` in
  `gate_build.py` copies a textured town material and re-tints it through a
  MULTIPLY mix, inheriting box projection, the AO multiply, the roughness map
  and the world-up moss layer. A flat Principled colour reads as untextured
  cream next to it no matter how dark the number (findings 95 / 105). The gate
  added `mat_gate_road` (rock, scale 0.92, tint 0.42/0.33/0.25),
  `mat_gate_turf` (0.52, 0.40/0.41/0.29), `mat_gate_stone` (1.60,
  0.55/0.52/0.47), `mat_gate_sack` (timber, 1.90, 0.74/0.63/0.44) and
  `mat_gate_cliff` (1.05, 0.34/0.33/0.36).
- **Re-tile for the object's scale.** `mat_rock` is tuned for a 60 m cliff.
  Ground 1.15, road 1.55, dressed masonry 1.90 — roughly one texture feature per
  metre (finding 96). A shopfront wants tighter still.
- **Bunting**: do NOT use the kit's `mat_flag_*`. They are one flat diffuse mixed
  with one flat translucent and they read as coloured rectangles inside about
  6 m. `gate_build.cloth()` is the replacement — a weave noise x a broad
  sun-fade multiplying the tint, six materials so the variation is in VALUE not
  hue, all pulled onto the painted-timber palette. The values that worked:
  red (0.196, 0.064, 0.055), red2 (0.128, 0.050, 0.046), blue (0.068, 0.123,
  0.191), blue2 (0.047, 0.081, 0.128), ochre (0.255, 0.175, 0.076), bone
  (0.320, 0.295, 0.248). Geometry: `pennant()` — stiff top edge on the line,
  taper to the point, per-pennant curl signed by its phase. Copy both.
  The map's own note for this street says "lanterns strung overhead", so you
  will be doing a lot of this at close range. It matters here more than it did
  at the gate.
- **Lanterns**: 680 W point, colour (1.0, 0.58, 0.24), `shadow_soft_size` 0.10,
  `use_custom_distance` with `cutoff_distance` 14.0,
  `shadow_maximum_resolution` 0.01. That is the town standard, unchanged across
  three districts. Heartlights do NOT exist in Dellhollow (world canon) — these
  are ordinary lamps.
- **Lit windows**: `gate_build.lamplit()`, emission strength 2.1..3.4 with a
  noise unevenness, colour (1.0, 0.455, 0.135). NOT the 90 a lantern globe
  wants — at window scale AgX creams the hue out and it lands as a clipped white
  rectangle (finding 112, and boatyard `make_lockhouse_glass` before it). A shop
  street at dusk should have several, and they will do more for it than any
  amount of key. This is the single cheapest win available to you.
- **Roofs**: `gate_build.shingles()`. Course count comes off the roof's DEPTH,
  not its height — exposure ~0.12 m, courses broken across their length on a
  half-tile stagger. Nine long boards per pitch reads as a lumber stack from
  underneath and `mat_shingle_mossy` paints one bright stripe per course
  (finding 109). On a street where the player walks under the eaves this is very
  visible.

## Composition — what the gate pass learned the hard way

- **The shot list is build data.** Put it in `shelf_lib.py`, not in
  `shelf_shots.py`, and have the build import it. Density and prop size are
  properties of a zone SEEN FROM SOMEWHERE (finding 108).
- **Near-field thinning**: `gate_lib.near_field(x, y, z, extent)` — per camera,
  in frame, and nearer than 85% of the camera-to-subject distance, then a size
  test at 3.2x extent. Cull masses, only size-cap ground cover
  (`clone(..., cull=False)`). Two earlier formulations failed: absolute radii
  stripped the tufts with the clumps, and a pure distance/size ratio deleted
  every tree in the parcel (findings 106 / 107). Copy the working one; do not
  re-derive it.
- **Deliberate subordination.** Whatever the street's landmark is, everything
  else has to be shorter, or the roofs merge into one horizontal band and the
  frame has no skyline (finding 110). On this tier the ceiling at 23.10 means
  you have very little vertical range to play with — so the differentiation will
  have to come from ridge DIRECTION, dormers, and awning depth rather than
  height. Think about that before you place the first roof.
- **Figure/ground is a SURFACE problem before it is a light problem.** The gate's
  arch had no silhouette because it stood in front of a cliff of the same
  material at the same value; darkening the backdrop veneer fixed in two node
  links what no amount of bounce card could (finding 105). Your street stands
  against the same cliff. Extend `mat_gate_cliff`, or derive a sibling.
- **Ray-cast the pixel, don't reason about it.** Every backdrop leak in the gate
  pass was diagnosed in about two minutes with `sc.ray_cast` from the camera
  down a reconstructed pixel direction, and at least two of them would have been
  diagnosed wrongly by argument (findings 104 / 114). There is a working probe at
  `scratchpad/gate_pix.py` — the reconstruction maths (sensor fit, `angle_x` vs
  `angle_y`, aspect) is the fiddly part and it is already right there.

---

## Protocol (unchanged, and all of it still in force)

- Branch blend `tools/blends/dellhollow-master-gate-branch.blend`. **Never** touch
  `tools/blends/dellhollow-master.blend` — another agent holds it.
- ADDITIVE ONLY. New collection `SHELF_DISTRICT`, object prefix `shelf_`, lights
  `KEYSH_*`, foliage `veg_shelf_*` (the runtime treats `veg_` as never-standable;
  the gate's foliage was renamed `veg_gate_*` in `5e298a7`).
- The only permitted deletions are `lm_` shells of your own parcels' members,
  each recorded in `tools/blends/districts/shelf_branch_deletions.json`.
- `walk_`/`bar_` meshes, shared rigs (`SUN_key`, `SKY_wash`, `KEY_slip`,
  `KEY_gorge_*`, `RIM_gorge`, `CLIFF_BOUNCE*`, `FILL_bounce*`), `world`,
  `cliff_*`, `fx_*`, and every other district's objects (`gate_*`, `wf_*`,
  `yard_*`, `lf_*`) are UNTOUCHABLE.
- `master_walk_qa.py` must stay **367/367 zero-drift** with **1308/1308** rays on
  the canonical region after every pass. Quote the district region too, against
  the same region on the base commit (finding 102).
- `geometry_audit.py --region <yours>`: register your own assemblies in
  `SAME_ASSEMBLY` and your foliage prefixes in `VEG`, or your own bracketry
  comes back as offenders (finding 79). `veg_` is already in `VEG`.
- Scripts are the durable source: `shelf_build.py` + `shelf_light.py`, build
  before light (the light rig's lamps share the prefix the build clears).
  Blend and script must never drift.
- Renders `shelf_v*_<shot>.png` in `docs/qa/districts/`, then
  `python3 tools/make_qa_index.py`. **Per the 2026-07-29 render norm: EEVEE is
  fine, record at most 2-3 shots, and do not polish camera angles beyond
  "subject visible."** The user reviews by walking the scenes. Value calls come
  from the light rig's measured irradiance, not from a frame (manifest 70 —
  EEVEE's shadow budget overflows silently past ~40 lamps and this tier is
  already inside about 70).
- Findings continue in `tools/blends/KITLIB_MANIFEST.md` **after 131**. Check
  the file first — the Locksfoot agent and this one both independently started
  at 104 and the collision had to be untangled by hand. Read the last number in
  the working tree, not in your memory of it.
- Commit specific paths on `migration/3d-hybrid`. Nothing is pushed.

## Suggested order of work

1. `shelf_lib.py` — extents, the 19.0 floor, the 23.10 ceiling rule, the walk
   corridor model (copy `gate_lib.Terrain`, it already handles "a walk BELOW the
   district is a disjunction, not a ceiling", finding 92), the shot list, and
   `near_field`.
2. Ground/street first (finding 72: the props have nowhere to stand until it
   exists), terraced under every walk you meet, paving 50 mm under the walk tops
   so the QA's down-ray still lands on canonical topology (`DECK_DROP`).
3. The five buildings, each seated on its own pad, ridges under 23.10, roofs via
   `shingles()`, at least three lit windows.
4. The street: awnings, signs, the strung lanterns the map asks for, bunting via
   `cloth()`/`pennant()`.
5. The backdrop veneer east of x=31.44.
6. `shelf_light.py`: report first, then a solved chain, spill-asserted against
   the Boatyard, the Waterfront AND the gate arch.
7. Both gates, 2-3 EEVEE shots, gallery, findings, commit.

Good luck. The tier is a better brief than the gate was — it has a clear
subject (a shop street), a strong constraint (4 m of headroom under a gallery),
and the map already tells you what it should feel like.
