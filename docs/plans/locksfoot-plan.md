# Locksfoot — district build plan

**Status: PREP COMPLETE, BUILD NOT STARTED.** Written by the prep agent, which never had
master custody. Everything here is desk work done against
`public/townmap/dellhollow.map.json`, `tools/blends/dellhollow-town.blend` (the topology
reference, read-only), `MIGRATION.md` and `tools/blends/KITLIB_MANIFEST.md`.
`tools/blends/dellhollow-master.blend` was **never opened**.

The build products that go with this plan:

| Artifact | What it is |
|---|---|
| `tools/blends/districts/locksfoot-kit.blend` | 25 reusable assemblies, glTF-safe materials. **Never move this file** (manifest 63 — its texture paths are relative to `tools/blends/districts/`). |
| `tools/locksfoot_kit.py` | Rebuilds the kit from scratch: `Blender -b --factory-startup -P tools/locksfoot_kit.py` |
| `tools/locksfoot_kit_render.py` | Six taste-check renders: `Blender -b tools/blends/districts/locksfoot-kit.blend -P tools/locksfoot_kit_render.py` |
| `docs/qa/districts/locksfoot_kit_*.png` | lock, wheels, dam, crest, cottage, clutter |

---

## 1. Scope

Locksfoot is the district `z = 1.0` in the map, but the *build* region is the whole
downstream end of the gorge — everything east of where the Waterfront's ground stops.

> Waterfront handover, verbatim: *"`wf_ground` carries the bank and the cliff from
> x=40.1 to x=66.0 … **East of x=66 there is still void** — that is yours."*

**Region: x 63 → 112, y 12 → 34 (town side), plus the dam which spans the full widened
river to y ≈ 76.** Vertical range z −4.6 (river bed) → +15 (Lockhead deck / cottage roof).

Parcels inside it (all `draft: true`, all `projection: persp` — projection canon):

| Parcel | sceneKey | bounds min → max | Members | Camera intent |
|---|---|---|---|---|
| `p-lockfive` | `del-lockfive` | 65.4, 21.5, −1.5 → 91.5, 34.5, 5.5 | moorage, tenant-shack, lock-five, dam-crest-gate | yaw 157, pitch 14, vh 13 — low in the gorge looking downstream: the black dam + wheels, the moored boat, cottage lantern above |
| `p-cottage` | `del-cottage` | 88.1, 17.5, 6.3 → 97.1, 26.5, 11.3 | keepers-cottage | yaw 76, pitch 18, vh 10 — intimate from over the basin; balcony over the drop |
| `p-northlanding` | `del-northlanding` | 101.2, 22.5, −2.5 → 110.2, 31.5, 2.5 | north-landing | yaw −30, pitch 18, vh 11 — the goodbye shot, town stacked behind |
| `p-lockhead` | `del-lockhead` | 76.2, 11.5, 12.5 → 85.2, 20.5, 17.5 | lockhead | yaw 60, pitch 26, vh 11 — Odessa's post; the lock machinery readable far below |

`p-crossing` (the transit vignette, x 71.5–92.5 at z 5.5–11.5) flies **over** this region.
Its postcard is the plank bridge `walk_e_weave-huts__keepers-cottage_*`; the thing the
camera looks *down* at is Locksfoot's basin. Build the basin so it reads from above.

`p-weave` (x 54.6–76.0) overlaps at the west end. **Do not build the Weave.** Stop at the
walkways; the stilt clusters standing on nothing above `wf_ground` are the Weave's job
(same ruling the Waterfront made about them).

### Landmark inventory (map coordinates)

| id | class / kind | pos (x, y, z) | notes from the map |
|---|---|---|---|
| `tenant-shack` | structure / building | 69.91, 26, 2.0 | resident `tenant` |
| `moorage` | area / dock, extent 4 | 76.09, 27, 1.0 | **the tar-dark boat waits here** |
| `lock-five` | structure / lock | 86.91, 28, 0.0 | the basin + gates; namesake centrepiece; boat gained here |
| `dam-crest-gate` | portal / gate, **state closed** | 87, 30, 0.9 | iron-banded gate barring the crest walk to the far shore; far-side stairs "not kept" |
| `north-landing` | area / dock, extent 3 | 105.65, 27, −1.0 | last pier before the gorge narrows; the night boat slips out from here |
| `keepers-cottage` | structure / building, **enterable** → `del-cottage-int` | 92.61, 22, 7.83 | "the house over the locks"; **balcony platform river-side**, its lantern-lit underside is what Locksfoot sees from below |
| `lockhead` | prop / post | 80.73, 16, 14.0 | Odessa's post (Quay district, but it overlooks this basin — its cliff face is Locksfoot's backdrop) |

River spec that governs the dam (`river.dams[1]`):

```
dam-five   x = 87   drop = 1.8   waterwheels = 3
  "black stone dam per ref 6b: three waterwheels on its face,
   crest walkway with cargo, thundering spill gates"
  crossing: planned, state "closed" — model the crest + closed gate, no detail beyond
pools: pool-mid  x 14..87  level  0.2      (headwater)
       pool-downstream x 87..130 level -1.6 (tailwater)
river: centerY 50, width 48, near bank y≈26, far bank y≈74, far wall y≈84
```

Style block (unchanged, and the palette this district must hold):
*weathered PAINTED timber — oxblood red, moss green, faded blue — over brown scaffold
structure; **black stone for the dam**; teal-green water; autumn oranges on the rim trees.*
Motifs: bunting across the gorge, moored flat barges with pumpkins/crates, waterwheels on
the dam faces, **ordinary warm hanging lanterns** (world canon: Heartlights do **not**
exist in Dellhollow), rope and cargo clutter on every deck, autumn trees on both rims.

Master reference: `public/assets/refs/dellhollow-master-6b.png` — the shot the dam has to
reproduce. Aesthetic bar: `docs/qa/districts/boatyard_v10.png` + `waterfront_v7_*.png`.

---

## 2. THE NO-GO SET — `walk_` / `bar_` meshes in the region

Canonical topology. **Never move, edit, delete, parent, scale or re-mesh these.** The only
legal change is `hide_render = True` where real decking covers a ribbon (manifest 51 —
`hide_viewport` is destructive: the glTF exporter drops the object and the runtime loses
its collision). `master_walk_qa.py` compares them bit-for-bit against
`tools/blends/dellhollow-town.blend`.

**112 meshes have at least one vertex at x ≥ 63.** Cached vertex data:
`tools/blends/districts/town_walk_reference.json`.

Locksfoot's own — deck these, light these, build ground under these:

```
walk_lm_moorage                    x 72.1..80.1   the moorage pad (a FILLED disc: manifest 35)
walk_lm_north-landing              x102.7..108.7  the last pier
walk_pad_tenant-shack              x 68.6..71.2
walk_pad_lock-five                 x 85.6..88.2
walk_pad_dam-crest-gate            x 85.7..88.3   the crest landing at the closed gate
walk_pad_keepers-cottage           x 91.3..93.9
walk_e_moorage__tenant-shack_l0    x 69.8..75.3
walk_e_moorage__lock-five_l0/l1    x 77.0..86.1   waterline boardwalk curving to the gates
walk_e_lock-five__north-landing_l0/l1  x 87.8..105.7  descending past the gates
walk_e_keepers-cottage__lock-five_l0..l3_t00..t06 (21) + _landing, _landing.001, _landing.002
                                   x 87.3..95.5   the switchback from the porch to the basin
bar_e_keepers-cottage__lock-five_l0..l3_railA/B  (8)
```

Borrowed / shared — they cross the region but belong to neighbours. Do not re-deck what
another district owns; the rule is *whoever owns the parcel decks it*:

```
walk_lm_fish-dock, walk_e_tenant-shack__fish-dock_l0/l1   (Waterfront — already decked)
walk_lm_drying-decks, walk_pad_weave-huts,
walk_e_pilot-cluster__weave-huts_l0..l2,
walk_e_weave-huts__drying-decks_l0/l1                     (the Weave)
walk_e_weave-huts__moorage_l0..l3_t* (18) + 3 landings,
bar_e_weave-huts__moorage_l0..l2_railA/B (6)              switchback DOWN into Locksfoot —
                                                          Locksfoot decks the lower legs
                                                          (z < 4), the Weave the upper
walk_e_weave-huts__keepers-cottage_l0..l2 + 6 rails       THE PLANK BRIDGE (p-crossing)
walk_e_market-stalls__lockhead_l0..l2, walk_pad_lockhead  (the Quay)
walk_e_lockhead__keepers-cottage_l0..l18                  the cliff spur to the cottage —
                                                          Locksfoot's, from x≈86 east
```

Ladders exist as topology in the map but as `e_*_rung*` PATHS meshes in the blockout
(not `walk_`): `e_lockhead__lock-five_rung00..27` (Odessa's maintenance ladder down the
cliff, x 80.4–87.2) and `e_weave-huts__fish-dock_rung00..10`. Those **are** blockout-owned
and may be replaced with real ironwork — but check the master before assuming, and
re-run the walk QA either way.

---

## 3. Blockout `lm_` / `dam_` shells to replace

All confirmed present in `dellhollow-town.blend`; the master's copies may have moved
(`master_river_widen.py` re-spanned the dam-five blockout across the widened river — the
numbers below are the *reference* file's, i.e. pre-widening, and the master's dam is wider).

| Object | Extent (reference blend) | Replace with |
|---|---|---|
| `lm_lock-five_wallS` | x 83.4–90.4, y 24.6–26.2, z 0–2.4 | real chamber wall: coped masonry, ladder recesses, mooring rings |
| `lm_lock-five_wallN` | x 83.4–90.4, y 29.8–31.4, z 0–2.4 | ditto |
| `lm_lock-five_gateA` | x 83.4–84.1, y 26.1–29.9, z 0–2 | `lf_gate_leaf` ×2 mitred (upper head) |
| `lm_lock-five_gateB` | x 89.8–90.5, y 26.1–29.9, z 0–2 | `lf_gate_leaf` ×2 mitred (lower head) |
| `lm_dam-crest-gate_postL/postR/lintel` | x 85.5–88.5, y 29.7–30.3, z 0.9–4.05 | `lf_crest_gate` (leaf closed, chain + padlock, "not kept" board) |
| `lm_tenant-shack_body` | x 67.8–72.0, y 24.2–27.8, z 2.0–5.2 | `lf_tenant_shack` (4.6 × 3.9 footprint incl. porch — the shell is bigger than the kit prop; extend with a lean-to store or a drying stage) |
| `lm_tenant-shack_roof` | x 67.7–72.1, z 5.15–6.55 | ↑ |
| `lm_keepers-cottage_body` | x 90.5–94.7, y 20.2–23.8, z 7.83–11.03 | `lf_keeper_cottage` (6.4 × 5.0 body; the shell is 4.2 × 3.6 — the cottage is **bigger** than its blockout, so check the plank bridge and the switchback clearances before committing) |
| `lm_keepers-cottage_roof` | x 90.4–94.8, z 10.98–12.38 | ↑ |
| `dam_dam-five_wall` | x 85.5–88.5, y 25–43 (master: y 25–75), z −3.1–0.8 | run of `lf_crest_bay` + `lf_spill_bay` |
| `dam_dam-five_crest` | x 85.9–88.1, z 0.8–1.1 | carried by the bays |
| `dam_dam-five_foam` | x 88.4–90.8, z −1.75–−1.25 | the bays' own nappe / lip / boil |
| `dam_dam-five_wheel0/1/2` | x 88.7–89.5, 4.4 dia, y 30 / 34 / 38 (master: redistributed across the full 48 m span) | `lf_wheel_breast` ×3 + `lf_wheel_bearing` ×6 |

`lm_lockhead` (x 80.3–81.1, z 14–15) belongs to `p-lockhead`; leave it unless you take
that parcel too. `lm_weave-huts_0/1/2` + roofs (x 67.3–75.3, z 7.8–11.9) are the **Weave's**.

**`lm_*` placeholders are non-solid at runtime** (commit 7134cc2), so removing one does not
change collision — but it does change what a down-ray hits, so re-run the walk QA.

---

## 4. The machinery the map promises

### Lock Five (x 83.4–90.5, y 24.6–31.4)
A 7 m × 5.2 m chamber with a head of 1.8 m — small, which is the honest reading of the
map: pool-mid 0.2, pool-downstream −1.6. Build it as a working lock, not as scenery:

* two **mitre** gate pairs (`lf_gate_leaf`), heel posts on the chamber walls, leaves
  closing **upstream** with the balance beams swinging out over the coping. The kit leaf is
  3.20 m wide × 3.60 m tall; a 5.2 m chamber wants two leaves of ≈ 2.75 m at a 20° mitre —
  **rebuild the leaf at `gate_leaf(name, W=2.75, H=2.60)` rather than scaling the object**
  (scale ≠ 1 breaks the kit's texel-density contract).
* `lf_gate_winch` on the coping at each head, one per side (four total). Ratchet + pawl
  face the water so the crew silhouettes against it.
* `lf_sluice_paddle` set into the chamber wall at each head — the paddles that fill/empty.
* `lf_capstan` + `lf_bollard` + `lf_mooring_post` on the coping for warping the barge in.
* Odessa's maintenance ladder (`e_lockhead__lock-five_rung*`) lands here; give it a proper
  iron stringer and a cage where it passes the coping.

### Dam Five (x 85.5–88.5, spanning y 25 → 75 in the master)
The hero. Ref 6b: **black stone**, three waterwheels on the downstream face, a crest
walkway carrying cargo and bunting, thundering spill gates, and the crest doubling as a
closed bridge to the far shore.

Build it as a **run of repeats** (manifest 61: extend detailed art by duplicating its own
components, never by re-modelling them):

```
crest bay (pier unit)   lf_crest_bay   3.90 m pitch, 3.50 m thick, battered downstream face
spill bay (gate window) lf_spill_bay   same 3.90 m pitch; raised leaf, nappe, lip foam, boil
```

Alternate pier / bay / pier / bay across the span. On the *piers*, hang
`lf_wheel_breast` (4.4 m dia) in `lf_wheel_bearing` pillow blocks. Three wheels over a
48 m span is ref 6b's spacing (the blockout already redistributed them that way). The
crest walk is `walk_pad_dam-crest-gate` at z 0.9 — the kit's crest deck sits at z +0.12
above the bay origin, so place the bays with origin z = 0.78.

**Water rule, inherited and re-proved:** the white belongs at the lip and in the boil. A
full-height sheet of `mat_whitewater` across the weir is what made Boatyard v3 read as
concrete panels (Lock Four rebuilt it as dark banded timber + a thin fall). `lf_spill_bay`
already encodes that: a dark glassy nappe leaving the sill, a foam line where it tips, and
four low wedges that break the tail waterline rather than lying on it.

### Dam crest gate (x 87, y 30, z 0.9 — `state: "closed"`)
`lf_crest_gate`: two black-stone jamb piers, a banded timber leaf, chain and padlock, and
the weathered board that says the far-side stairs are not kept. **No detail beyond the
gate** — the far shore is a future district hook and the map says so explicitly.

### Moorage + North Landing
`moorage` (x 72.1–80.1) holds **the tar-dark boat** — the boat gained at Lock Five, which
per OVERWORLD canon becomes drivable river traversal after the chapter's departure finale.
`lf_barge` is the flat cargo hull for the *other* boats (pumpkins and crates in the calm
pool — the map's motif). The tar-dark boat itself is a **story prop**: build it distinct,
darker, and readable at `p-northlanding`'s goodbye framing.

Manifest 77 applies to every hull: float with the FLOOR above the water plane or the pool
renders inside it, and loft a solid U-section — one sheet of stations reads as a sliver.

---

## 5. Palette + materials spec

The district's own objects use the **Boatyard/Waterfront material set already in the
master** (`mat_deck`, `mat_timber`, `mat_timber_dark`, `mat_rock`, `mat_wet`, `mat_iron`,
`mat_rope`, `mat_paint_red`, `mat_paint_blue`, `mat_wallwood`, `mat_wallwood_dark`,
`mat_shingle_mossy`, `mat_lantern_glass`, `mat_grass`, `mat_fern`, `mat_vine`,
`mat_leaf_creeper`, `mat_freshwood`). Fetch them with `boatyard_lib.M(name)` and add only
what the dam needs:

| New material | Base | Why |
|---|---|---|
| `mat_stone_black` | very dark, low-chroma, rough 0.86 | THE dam. It has to out-dark everything. Lock Four's `MAT_STONE` is the reference value — match it, do not invent a second black. |
| `mat_stone_black_cap` | one step up in value | coursing, cap, parapet — a single flat black mass has no form |
| `mat_nappe` | dark teal, rough 0.10 | the glassy sheet leaving a sill |
| `mat_boil` | near-white but **desaturated and knocked down** | manifest 40/41: measure the ROI before deciding a fall "reads weak" |

Values (linear, the kit's own palette — carry these into the master's materials so the two
datasets are one town):

```
oxblood   6d2a20    painted timber (the reference shed red)
mossgreen 45543a    painted timber
fadeblue  37505c    painted timber
timber    5c4630    brown scaffold structure
timberdk  3d2e20    framing, doors, gate leaves
deck      6f5a3d    planking
stoneblk  24211f    THE DAM        stoneblk2 302c28  its coursing/cap
stonegrey 4c463d    ordinary masonry (plinths, abutments)
iron      241f1c    irondk 171412   rust 44291a
fall      16292c    foam 8e9a94     water 1b4344 (teal-green pool)
shingle   4e5638    mosswood 3f4a33  glass ffc27a (lantern)
```

**Everything within half a metre of a practical gets a sooted / darkened variant**
(manifest 42) or the masonry out-values the flame it contains.

### Lighting — you inherit a rig, extend it, do not replace it

From the Waterfront handover:

* 21 `KEY_gorge_*` spots on `KEY_slip`'s own direction and standoff, in three chains
  (`wf_deck` 8, `wf_cliff` 6, `dam` 7), each carrying a `level` (0.34 cliff / 0.60 deck /
  0.80 dam). **Add to the chains; do not add a new rig.**
* Chains that fire ALONG the gorge are narrow-and-many (≤ 26° cone, `spot_blend = 1.0`);
  the dam chain, which fires ACROSS it, keeps 48°. (Manifest 65/66.)
* Match the **mean**, not the peak, of the accepted district (manifest 67).
* **`SKY_wash` is 90 × 80 at 804 W and covers world x −10 … 70. Locksfoot builds
  x 66 … 112, so you MUST extend it — and SOLVE the wattage against a reference point
  rather than scaling by area (manifest 68), or you will lift the accepted Boatyard.**
* Bounce cards: half size, quarter power, half standoff (manifest 69).
* Give EEVEE its shadow budget back (`use_custom_distance` + `cutoff_distance`,
  `use_shadow = False` on fake bounce cards) — **but make every value judgement in
  Cycles** (manifest 70). The kit renders are EEVEE because they are a 4-lamp stage; the
  master is not.

---

## 6. Ground — the district's first pass

East of x = 66 there is no ground at all. Build it exactly the way the Waterfront did
(`waterfront_build.py` §1), because that is what made its walkways read as *built*:

1. A base height function + noise, **noise applied BEFORE the walk clamp** (manifest 39 —
   afterwards it lifts the ground back through the deck it was just clamped under).
2. Clamp to `min(base, walk_top − 0.42 + d·1.15)` over the distance `d` to the nearest walk
   face (manifest 38/55) so the terrain terraces itself around every path.
3. The walk surface at a point is the **HIGHEST** walk face there, not each face's own z
   (manifest 36) — `walk_pad_dam-crest-gate` sits over `walk_pad_lock-five`, and the
   moorage switchback's ribbon ends are buried the same way.
4. A **2.3 m flat strand** at the foot of the cliff (manifest 72) or nothing will stand:
   with a slope test in the placer the Waterfront landed 0 of 130 clutter attempts before
   it had one, 65 after.
5. Carry the ground **up to the Keepers' Spur** (z 7.83) — the cottage, its balcony braces
   and the switchback all need something to stand on, and the spur is inside your region.
   Register the new mesh in `geometry_audit.GROUND` (`lf_ground`).

Seam: meet `wf_ground` at x = 66.0 by re-using its own height function at the join
(manifest 55 — carry the ground under the neighbour, do not decorate the join).

---

## 7. Build order + QA gates

Every pass: rolling backup to `tools/blends/backups/` (gitignored) **first**, then the pass,
then both gates. Never let a pass end red.

```
master_walk_qa.py   Blender -b tools/blends/dellhollow-master.blend -P tools/master_walk_qa.py \
                       -- --region 63,112,12,34
geometry_audit.py   Blender -b tools/blends/dellhollow-master.blend -P tools/geometry_audit.py \
                       -- --region 63,112,12,44        # town side
                    ... and a second run  --region 84,92,24,76   # the dam across the river
```

| Pass | Work | Gate |
|---|---|---|
| **P0 baseline** | Touch nothing. Run both gates and **write the numbers down**. The Waterfront's region baseline was 1907/1966 (97.00%) with 59 known blockout blockers; Locksfoot's number is unknown and you must own the delta, not the absolute. | both gates, recorded |
| **P1 ground** | `lf_ground` x 66→112 + the Keepers' Spur; strand at the cliff foot; seam to `wf_ground` at x = 66. Extend `SKY_wash` east (solve the wattage). | walk QA ≥ baseline; audit: `lf_ground` in `GROUND` |
| **P2 light** | Add `KEY_gorge_lf_*` chain elements to the existing chains (levels 0.34/0.60/0.80); half-size bounce cards; verify the accepted Boatyard's mean luminance in **Cycles** hasn't moved (the Waterfront held 0.326 vs 0.340 through a whole rig change — that is the number that says "one town"). | Cycles luminance check on the `continuity` camera |
| **P3 decking** | Plank every Locksfoot walk ribbon; joists + piles; guards laid where `bar_*` are, placed **by search** not by taste (`over_walk()`, manifest 76); treads INSET −0.045, flat decking +0.50 (manifest 74); one stringer per flight, both ends walked in (manifest 74). `hide_render = True` on the ribbons you cover — **never `hide_viewport`**. | walk QA: 0 new blocked, 0 new headroom |
| **P4 Lock Five** | Chamber walls, mitre gate pairs, winches, sluices, capstan, coping clutter. Delete `lm_lock-five_*`. | both gates |
| **P5 Dam Five** | Crest bays + spill bays across the widened span, three wheels + bearings, crest gate. Delete `dam_dam-five_*` and `lm_dam-crest-gate_*`. Re-check the far-bank toe: manifest 60 (moving a waterline leaves a hole, and the toe's LIP must be cut to the LOCAL pool level — there are two pools either side of this dam). | both gates + the dam-region audit |
| **P6 buildings** | Keepers' Cottage + balcony (+ the under-balcony lantern — it is what Locksfoot sees from below and the map calls it out), tenant's shack, moorage staging. Delete `lm_keepers-cottage_*`, `lm_tenant-shack_*`. **Check the cottage against the plank bridge and the switchback: the kit shell is bigger than the blockout it replaces.** | both gates; cottage footprint vs `walk_pad_keepers-cottage` |
| **P7 water & boats** | The tar-dark boat at the moorage, cargo barges in the calm pool above the dam, North Landing pier + the night-departure staging. Hulls float floor-above-water (manifest 77). | audit: hulls in `SAME_ASSEMBLY` |
| **P8 dressing** | Bunting across the gorge, ordinary lanterns (never Heartlights), rope/cleats/cargo on every deck, autumn rim planting re-seated **on the crest function** (manifest 71 — do not translate `farwallcrown_*`, re-seat them). Compose for the ROUND, not for one camera (manifest 57/62). | audit: `lf_` veg prefixes in `VEG` |
| **P9 close-out** | Register every `lf_*` assembly pair in `geometry_audit.SAME_ASSEMBLY` (manifest 78 — the Waterfront went 16 offenders → 0 with unchanged geometry). Re-export `townwalk`. Re-bake the affected bundles with `tools/depth_bake.py` (occlusion canon: `del-lockfive`, `del-cottage`, `del-northlanding`, `del-lockhead`, and `del-crossing`, whose vignette looks straight down at this basin). Shot script + QA renders + `python3 tools/make_qa_index.py`. | both gates green; district gate = Boatyard v10 aesthetics + geometry coherence |

**District gate (user, 2026-07-29):** aesthetics bar = Boatyard v10, **plus** geometry
coherence — no interpenetrating major objects, no unsupported/orphaned strays, and the
walkable path must READ visually in frame.

Camera set for the QA renders (mirror `tools/waterfront_shots.py`): `lockbasin`,
`damface`, `crestwalk`, `moorage`, `cottagebalcony`, `northlanding`, `fromcrossing`
(down from the plank bridge), and **`continuity`** — reproduce the Waterfront's
`continuity` camera unchanged so the two districts can be compared frame to frame.

---

## 8. What is in `locksfoot-kit.blend`

25 objects, 19 190 tris, object scale 1.0 everywhere, character reference = 1.70 u.

| Collection | Objects |
|---|---|
| `LF_LOCK` | `lf_gate_leaf` (3.20 × 3.60 mitre leaf: planked skin, ledgers, iron bands, strap hinges, top walkway + rail, balance beam), `lf_gate_leaf_low` (2.60 × 2.40), `lf_gate_winch` (A-frame, 14-tooth gear, pinion, crank, rack, pawl), `lf_capstan` (staved drum, two bars shipped, rope turn), `lf_sluice_paddle` (slotted frame, screw stem, hand wheel) |
| `LF_WHEELS` | `lf_wheel_breast` (4.4 m dia, 24 buckets + sole boards, 12 spokes/side, shrouds + iron tyre), `lf_wheel_breast_wide` (5.2 m, 28 buckets), `lf_wheel_undershot` (3.0 m, 16 flat paddles), `lf_wheel_bearing` (stone corbel + pillow block + gudgeon) |
| `LF_DAM` | `lf_crest_bay` (3.90 m pier unit: battered mass, string courses, cap, parapet, timber crest walk), `lf_spill_bay` (same pitch, gate window, raised leaf on chains + guides, nappe/lip/boil), `lf_crest_gate` (closed, chained, "not kept" board) |
| `LF_BUILD` | `lf_keeper_cottage` (6.4 × 5.0 painted green, shingle gable, stone chimney, **cantilevered balcony with supper table, a rail, a post lantern and an under-balcony lantern**, door lantern, bench), `lf_tenant_shack` (oxblood, corrugated mono-pitch, stove pipe, porch, drying net) |
| `LF_PROPS` | `lf_lantern_post`, `lf_bollard`, `lf_cleat`, `lf_mooring_post`, `lf_barrel`, `lf_crate`, `lf_cargo_stack` (crates + barrel + pumpkin load + tarp), `lf_rope_coil`, `lf_bunting_swag` (9 m catenary, 15 pennants), `lf_barge` (7.6 m flat cargo hull, solid, floor above the waterline) |
| `LF_REF` | `REF_human_1p7` |

### How to bring them into the master

```python
import bpy
KIT = "/Users/junshernchan/projects/multiplayer-rpg/tools/blends/districts/locksfoot-kit.blend"
names = ["lf_gate_leaf", "lf_wheel_breast", ...]
with bpy.data.libraries.load(KIT, link=False) as (src, dst):
    dst.objects   = list(names)      # manifest 31: pass a COPY, load() rewrites it in place
    dst.materials = [m for m in src.materials if m.startswith("lf")]   # manifest 3
```

`bpy.ops.wm.append` fails headless (manifest 4). After appending, read `matrix_basis` and
compute bounds from `data.vertices` — `matrix_world` and `bound_box` are depsgraph-
evaluated and lie in a headless build (manifest 32).

### Materials — the deliberate difference from `kitlib.blend`

`kitlib.blend`'s materials are object-space box projection + a procedural noise moss layer.
That is beautiful in Cycles and **exports as flat grey**. The Locksfoot kit speaks only in
things glTF carries:

* vertex colour (`Col`, FLOAT_COLOR, CORNER) → `COLOR_0`
* three materials add an image texture with **real box-projected UVs**; the exporter writes
  `baseColorTexture * COLOR_0`, which is the same multiply the viewport shows
* nothing else: no noise, no box projection, no Musgrave

Textures used, referenced relative (`//../../textures/`): `weathered_planks_Diffuse.jpg`
(deck), `old_stone_wall_02_Diffuse.jpg` (stone), `red_slate_roof_tiles_01_Diffuse.jpg`
(shingle). A multiply always darkens, so each textured material's vertex colours are
pre-divided by that map's mean luminance (gain ×1.64 / ×1.00 / ×1.00 — printed at build).

**Verified by round trip:** 25/25 objects export and re-import with UVs, vertex colours and
textures intact (3.73 MB GLB). Two things change on the way back and the custodian should
expect them — see manifest findings 79–81.

---

## 9. Open questions for the user

1. **A 1.8 m drop cannot carry ref 6b's wheels.** The map gives dam-five `drop: 1.8`
   (pool-mid 0.2 → pool-downstream −1.6), but the reference painting shows three
   waterwheels that are roughly as tall as the dam face, with long white falls. A 4.4 m
   wheel against a 1.8 m head reads as a wheel standing in a puddle. Three options:
   (a) **deepen the drop** to ~4.0 m in `dellhollow.map.json` (a map edit — needs the
   validator and a walk-graph re-check, because `walk_e_lock-five__north-landing_*`
   descends through it); (b) keep 1.8 m and use `lf_wheel_undershot` (3.0 m dia) so the
   proportion is honest — a smaller, busier dam; (c) keep 1.8 m and cheat the *apparent*
   height by standing the wheels in a recessed tail race cut below the pool. The kit ships
   all three sizes so the decision is cheap either way. **This is the one thing that should
   be settled before P5.**
2. **Is `p-lockhead` Locksfoot's or the Quay's?** `lockhead` is `district: quay` and
   `lm_lockhead` sits at z 14, but the parcel's whole subject is *this* basin seen from
   above, and the maintenance ladder down the cliff is shared. Cheapest answer: Locksfoot
   builds the cliff face and the ladder; the Quay builds Odessa's post.
3. **Keepers' Cottage footprint.** The kit shell is 6.4 × 5.0 m; the blockout it replaces
   is 4.2 × 3.6 m. The bigger house is what the balcony and the supper scene want, and
   `del-cottage-int` is already built at interior scale — but it has to be checked against
   `walk_pad_keepers-cottage` and the plank bridge landing before it goes in. Shrink or
   move the pad? (A pad move is a map edit and a topology delta, like the rail trim.)
4. **Bunting across the gorge.** The style block calls for it and the gorge is now 48 m
   wide. A 48 m swag needs an anchor on the far wall, which is otherwise pure backdrop.
   Anchor it to the dam's own crest posts instead (3.9 m spans), or accept far-wall masts?
5. **The tar-dark boat.** Story-critical (it becomes drivable overworld traversal). Should
   it be modelled in the district, or does it belong in a shared prop library because the
   overworld will need it too?

---

## 10. First three things the Locksfoot custodian should do

1. **Take the backup and the baseline.** `cp dellhollow-master.blend backups/master-pre-locksfoot.blend`,
   then run both gates over `--region 63,112,12,34` and record the exact numbers. Every
   later claim ("0 new blocked samples") is measured against that line, and every defect
   already there is provably not yours.
2. **Look at the six kit renders** (`docs/qa/districts/locksfoot_kit_*.png`) next to
   `boatyard_v10.png`, and settle open question 1 (the dam drop) with the user before
   modelling any of the dam. Everything else in the plan is independent of that answer.
3. **Build the ground first** (P1) — including extending `SKY_wash` east of x = 70 with a
   *solved* wattage. Nothing else in this district can be judged until there is a bank
   under it and a key on it; the Waterfront's whole first day went that way and it was
   right.
