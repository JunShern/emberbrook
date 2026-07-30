# p-lockhead — measured prep, and why the quay-market custodian did NOT build it

Written 2026-07-30 by the quay-market custodian, which was assigned p-lockhead as
a secondary parcel ("if your window allows... keep it modest").  The window
allowed the measurement but not the design call the measurement turned up.
Everything under **Measured** was read out of `tools/blends/dellhollow-master.blend`
at that commit; it is the part that would be expensive to reproduce.

## The finding: p-lockhead is not gray, it is one shell in a pad

The parcel is `x 76.2..85.2, y 11.5..20.5, z 12.5..17.5`, one member (`lockhead`),
Odessa the harbormistress.  Map intent: *"The overlook: harbormistress's post at
the deck's end, long approach walk, the whole lock machinery readable below."*

**Locksfoot already built most of it.**  Reaching into this parcel already:

```
lf_ladder_iron    x 80.39..86.45  y 15.84..26.61  z  1.88..14.13   584 v
lf_planking       x 68.23..98.27  y 16.46..29.68  z -0.95..12.17  1046 v
lf_piles          x 68.67..97.44  y 16.93..30.64  z -8.00..11.92   714 v
lf_joists         x 68.57..97.35  y 16.79..29.68  z -1.06..12.04   480 v
lf_pile_bracing   x 68.76..97.35  y 16.99..30.54  z -4.18..11.16  1952 v
lf_ground         x 66.10..112.10 y 12.50..34.10  z -7.60..18.93  6380 v
e_lockhead__lock-five_rung00..18  the map's own ladder, z 14.13 down to 5.94
```

So the camera note's "maintenance ladder plunging" and "Lock Five and the dam
small and thunderous far below" are already there and already good.  The ONLY
blockout left in the parcel is:

```
lm_lockhead       x 80.33..81.13  y 15.60..16.40  z 14.00..15.00    8 v   m_gray
```

— a 0.80 m gray box, and it stands **dead centre of `walk_pad_lockhead`**
(79.43..82.03 / 14.70..17.30), straddling `walk_e_lockhead__keepers-cottage_l0`
(80.46..81.29 / 15.23..16.86) and sitting on top of the ladder head at rung00
(80.38..81.08 / 15.85..16.15, z 14.07).  It is the same finding-93 error as
`lm_notice-board` and the three `lm_deep-stairs-head_` shells, which this
custody deleted and rebuilt off their pads.

## Measured: why it could not simply be moved off its pad

Every direction out of that pad is taken.

| direction | what is there | verdict |
|---|---|---|
| west  `x 76..79.4` | `walk_e_market-stalls__lockhead_l2` (75.15..80.90 / 14.02..16.78, z 14.07) | the approach walk; blocked |
| east  `x 82..85` | `walk_e_lockhead__keepers-cottage_l1..l5` descending 13.96 -> 11.92 | the route to the cottage; blocked |
| north `y 17.3..20` | the ladder and its rungs, then `lf_planking` 12 m below | the plunge; nothing to stand on |
| south `y 12.5..14.0` | `lf_ground` **rises to z 15.54 at (80, 13)** | free of walks, but 1.5 m ABOVE the pad |

The south strip is the only free ground, and it is the reason this is a design
call and not a build.  A post sited there stands **1.50 m above the deck it
serves**, looking down on it — which is a genuinely better reading of "the
overlook" than a box on the deck ever was, and it is what the parcel camera
(yaw 60, pitch 26, viewHeight 11, *"from high over the basin"*) is composed for.
But a raised post that a player can see and never reach is the
floating-building defect wearing a hat, and closing that needs one of:

1. **a map edge** — `walk_e_lockhead__lockhead-post` or a threshold pad on the
   bank, i.e. an edit to `public/townmap/dellhollow.map.json` and a regenerated
   walk graph.  That is the topology owner's call, not a district custodian's
   (architecture canon 2026-07-29: the map is the source of truth for topology
   and district art may never add walkables).
2. **or a post that is explicitly NOT enterable** — a signal mast, a bell on a
   frame, a chart board and a lamp, all on the bank behind the pad, with Odessa's
   actual station being the deck itself.  This needs no map change at all and it
   is the modest option: `lm_lockhead` is then replaced by dressing rather than by
   a building, which is honest about what a 0.8 m shell was ever standing for.

Option 2 is what this custodian would do with another hour, and it is the
recommendation.  What stopped it tonight was not the hour: it is that deleting
`lm_lockhead` and putting a mast where it stood is a taste call about whether
Odessa has a hut at all, and the map says `class: structure` for her post
(`lockhead`, `mapVisible: true`) while offering no interior scene key — so the
question "is this a building or a station?" is genuinely open and belongs to the
user or the topology owner.

## If you take it, here is the rest of the measurement

* The pad's surface is **z 13.92..14.04**; `lf_ground` under it is **13.35 at
  (80, 16)** and **12.75 at (84, 16)**, so the pad is bedded within 0.7 m — a
  paving lap, not a deck.  South of y = 14 the ground rises through 15.54 at
  (80, 13); north of y = 17.5 it falls to 3.34 at (80, 19).
* `veg_lf_rimclump_4/34` sit at x 84.9..89.3 / y 14.6..20.2, z 7.2..9.6 — below
  and east, so they are backdrop, not keep-out.
* Nothing in this parcel is render-visible blockout except `lm_lockhead` itself:
  `walk_e_lockhead__keepers-cottage_l6..l13` and `walk_e_weave-huts__*` are
  already `hide_render`, and `walk_pad_lockhead`,
  `walk_e_market-stalls__lockhead_l1/l2` and `..._l0..l5` are NOT — they fall
  outside p-quay-mkt's bounds, so this custody's render-hide pass (by map parcel
  bounds) correctly left them alone.  **Whoever builds p-lockhead owes those
  ribbons the same treatment**, and it is 10 lines: see section 0b of
  `tools/qm_build.py`.
* Materials: `mat_qm_*` (19 of them, all glTF-proven) are in the master and are
  the right family — this parcel is the market's own east end and shares its
  timber, stone and paint.  `derive()` returns an existing material by name, so
  reusing them costs nothing and adds no datablocks.
* Gates to quote: `master_walk_qa.py --region 74,90,10,22` and
  `geometry_audit.py --region 74,90,10,22`.  Baseline for the region was not taken
  by this custody — take it BEFORE touching anything (this custody's own baselines
  are in its final report and in `docs/qa/NIGHTLOG.md`).

## The remaining-gray statement, corrected

Dellhollow's gray inventory after the quay-market pass is **not** "p-lockhead and
p-crossing".  It is:

* **`lm_lockhead`** — one 8-vertex box in a pad, in a parcel whose art is
  otherwise finished by Locksfoot (above).
* **`p-crossing`** — a transit parcel with no landmarks by design (blessed
  2026-07-29): the plank-bridge postcard.  Its span is `bar_e_weave-huts__
  keepers-cottage_railA0..B2` + `walk_e_weave-huts__keepers-cottage_l0..l2`, all
  already render-hidden, and the Weave built the huts at both ends.

Every other `lm_` shell in the town is gone.
