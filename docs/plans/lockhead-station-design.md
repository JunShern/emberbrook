# p-lockhead — Odessa's station and the bank sweep (design note)

Written 2026-07-30 14:40 by the town custodian (day shift), before implementation, per
the coordinator's design-first rule.  Measurements are mine, taken in the live master
this morning; they extend `docs/plans/lockhead-prep.md` (which is trusted and correct)
with the one thing it did not measure: **what is underneath the walk ribbons.**

## The finding that shapes the whole build

`lockhead-prep.md` established the parcel is one 0.8 m gray box in a pad, and that the
south bank is the only free ground.  Hiding the parcel's ribbons (item 5 of the brief)
turned out to be more than a 10-line debt, because with `walk_*`/`bar_*`/`lm_*` masked
the first surface under the route is:

| where | walk top | first surface below | gap |
|---|---|---|---|
| approach, south half (x 75.5..80.9, y ~14.4) | 14.07 | `lf_ground` 13.6..13.95 | 0.1..0.4 m — **bedded** |
| approach, north half (x 75.5..80.9, y ~16.5) | 14.07 | `lf_ground` 10.4..12.2 | **1.9..3.7 m — void** |
| pad, north half (y 16.3..17.3) | 13.92..14.04 | `lf_ground` 10.6..13.2 | **0.8..3.4 m — void** |
| the cottage route `..._l0..l5` (x 80.9..86) | 14.07 -> 11.92 | `lf_ground` 13.0 -> 9.5 | **1..2.5 m — void** |
| `..._l6..l13` (already hidden) | 11.44 -> 7.77 | `lf_planking` 11.75 -> | dressed by the Weave |

So the route through this parcel is a LEDGE for its south half and a **cantilever over
the drop** for its north half, and the descending route to the Keepers' Cottage is an
undressed flight hanging 1..2.5 m over the bank until it lands on the Weave's planking
at x ~ 86.  Render-hiding the ribbons without laying art under them would replace a gray
ribbon with *invisible floor over a 12 m drop* — the exact defect the legibility program
is about.  The ribbon debt is therefore paid **with structure**, not with a flag.

This is also the honest reading of the parcel camera's own note ("Odessa's post on its
jetty of deck"): the lockhead IS a timber jetty pinned to a cut bank.

## Layout, in words and coordinates

Everything below is NEW `lk_*` geometry.  No `walk_*`/`bar_*` mesh is touched (item 5
sets `hide_render` only).  Nothing is enterable; no map topology changes.

```
                     N  (the plunge: lf_ground 8..12, then Locksfoot 12 m down)
   y 17.9  ......... lk_rail (posts 1.05 m, top rail, midrail, kickboard) .........
   y 17.3  --- lk_planking apron edge ---                     ladder-head gap
   y 16.3  ~~~ lk_planking on lk_joists on lk_bearers (raked, founded by ray-cast)
   y 14.7  === walk_pad_lockhead (hidden) under lk_paving  ===   \ lk_boardwalk
   y 14.0  === walk_e_market-stalls__lockhead_l2 (hidden) under lk_paving  \ (l0..l5)
   y 13.6  ### lk_bankface: the cut bank's revetment + kerb, 1.0..2.4 m of it
   y 12.6  ### lk_shelf: the bank crest, z 15.4..16.9 — the mast stands here
                     S  (lf_ground ends at y 12.50: void beyond, nothing may sit there)
```

* **Odessa's working corner — on the pad, at its south-east elbow** where the player
  arrives and leaves: free ground at `x 82.1..84.0, y 13.7..15.4`, `lf_ground`
  13.9..15.6, i.e. pad level.  It carries `lk_station`: a chart board on a raked stand
  facing the pad, a plank desk with the lock ledger, a stool, a shelf of gauge glasses,
  an oilskin on a hook post, and `lk_brazier` (small, embers, warm).  This is the "place
  a real person works all day" — reachable-looking, standing on the same floor the
  player stands on, and outside every walk polygon.
* **Signal mast — on the bank shelf behind, `(81.55, 13.25)`, foot z 15.5, 5.6 m tall**,
  with a yard, two day-mark boards (lock open / lock shut), a halyard and a cleat on the
  revetment below.  It is DELIBERATELY 1.5 m above the deck and behind a revetment face:
  the parcel camera (yaw 60, pitch 26, "from high over the basin") gets the vertical it
  is composed for, and the player can never mistake it for somewhere to stand, which is
  option 2 of `lockhead-prep.md` and needs no map edge.
* **Bell frame — `(81.3, 14.35)`, at the pad's south lip**, a bell in an A-frame with a
  lanyard falling to hand height.  Odessa's actual instrument: it is how the lockhead
  talks to Lock Five 12 m below.
* **The rim (item 4).** `lk_rail`, VISUAL ONLY, along the deck's whole north lip from
  `x 75.2` to `x 82.4` and returning down the pad's east side, with a **gap at the
  ladder head** (`x 80.35..81.15`) and a grab frame either side of it — the ladder is the
  one legitimate way over the edge and the rail must say so.  Posts stand on `lk_planking`
  and are carried by `lk_bearers`, so nothing floats.
* **Route affordance (item 3).** `lk_paving` (mat_qm_paving setts) over the bedded half,
  `lk_planking` (mat_qm_deck boards) over the cantilevered half, both laid **30 mm under
  the walk top** so the master's down-ray still lands on canonical topology (finding 90);
  a continuous kerb (`lk_bankface`) on the south side and the rail on the north.  Result:
  the walkable route is the only thing that reads as floor, edge to edge, from the market
  arch to the cottage steps — boards where it flies, setts where it is cut into rock.
* **Occupancy (item 3).** `lk_clut`: crates, a barrel, rope coils, a spare lock paddle and
  a bundle of iron bar (lock-machinery spares) along the bank foot, a chain coil at the
  ladder head, a bucket.  `veg_lk_*`: tufts and ferns in the joints and along the kerb,
  same crossed-quad language and `mat_fern`/`mat_grass` as the `veg_lf_*` family, and
  never in a walk polygon.
* **Light.** Two ordinary warm practicals, `lk_lantern_0/1` (`KEYL_*`, 680 W, 14 m cutoff
  — the town standard, unchanged for six districts), one on the mast's foot cleat post at
  the station corner, one at the ladder head.  No Heartlights (world canon: they are rare
  and magical; a working post has lanterns).  Spill measured and recorded.

## Materials

`mat_qm_*` family by `derive()`-by-name (returns the existing datablock, adds nothing):
`mat_qm_paving` (setts), `mat_qm_deck` (boards), `mat_qm_stone`/`mat_qm_stone_dark`
(revetment face and its shaded backs), `mat_qm_sack`, `mat_qm_paint_red/ochre/bone`
(the day-marks and the chart board frame), plus `mat_iron`, `mat_rope`, `mat_timber_dark`,
`mat_canvas`, `mat_fern`, `mat_grass`, `mat_lantern_glass` from the town set.  Two new
derived surfaces only where the family has no answer: `mat_lk_slate` (the chart board's
face, derived from `mat_rock`) and `mat_lk_ember` (a flat emissive Principled).
**No procedural node tree reaches export** — every material is either an existing
glTF-proven town material, an image texture times a constant, or a flat Principled.

## What this serves in the legibility program

* Bucket 1 (channeling at drop edges): the entire north lip of this parcel gets a rail,
  and the ladder head becomes the one legible way down instead of one of many ways off.
* Bucket 2 (route affordance): boards/setts/kerb make the intended path the only floor-
  reading surface in the frame; the descending flight to the cottage becomes visible
  treads instead of a hidden ribbon.
* Bucket 3 (framing): the mast gives the parcel camera a vertical at the exit end, and
  the chart board + brazier mark the elbow where the route turns from the market approach
  to the cottage descent — the transition the player currently cannot find.

## Constraints held

* No `walk_*`/`bar_*` geometry edited; `hide_render` only, on
  `walk_pad_lockhead`, `walk_e_market-stalls__lockhead_l1/l2`,
  `walk_e_lockhead__keepers-cottage_l0..l5` (the prep doc's list).
* Nothing solid stands **on** a walk polygon or within 2.0 m above one (finding 93 and
  the master's headroom check): every prop is placed through a corridor guard, and the
  substructure lives BELOW the walk plane where the down-ray cannot see it.
* Nothing is placed south of `y = 12.60`: `lf_ground` ends at 12.50 and beyond it is void.
* `lm_lockhead` is the only deletion, recorded in
  `tools/blends/districts/lockhead_deletions.json` (accumulating, per finding 115).
* Build is one idempotent script, `tools/lk_build.py`, which opens the live master; it
  clears every `lk_*`/`veg_lk_*`/`KEYL_*` object and orphan light datablock first, so a
  re-run is a rebuild and lamp names never drift.

## Requests for the coordinator (topology owner)

1. **No map change is needed for this build** — the station is deliberately not enterable.
   If the user later wants Odessa reachable at her post, the map edge
   `walk_e_lockhead__lockhead-post` from `lockhead-prep.md` option 1 is the way, and it is
   the coordinator's call, not mine.
2. **Pre-existing region gate failure, not mine:** `e_lockhead__lock-five_rung00` (the
   map ladder's top rung, `z 14.07..14.13`) stands 30..90 mm ABOVE `walk_pad_lockhead`
   inside the pad, and the region walk QA counts it as 3 non-walk first hits and 3
   headroom samples.  It is the map ladder generator's output, not district art, so I am
   not touching it.  Fix is a generator change (top rung flush with, or below, the pad
   plane) and it belongs to whoever owns the ladder builder.
