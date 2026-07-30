# CAMERA SURGERY — the quay junction, the bridge, the boatyard, and the water

Measured design + the exact `dellhollow.cameras.json` patch. Read
`docs/plans/seam-canon.md` first: this is the canon's first application, and every
change below exists to make the town pass `tools/seam_test.mjs`.

**Everything here was measured against a proposal file off to the side**
(`--cameras <path>`), so no shipped artifact was touched to design it. The bake was
running when this work started; nothing in `public/assets/scenes/del-cine/` was read
or written.

| | shipped | proposed |
|---|---|---|
| `seam_test.mjs` | **20 failures** | **PASS**, 294 ok, 0 failed, 2 annotated warnings |
| cameras | 17 | **16** |
| water in frame, mean | 10.1 % | **21.8 %** |
| shots with zero water | 11 | 8 |

---

## 1. THE DESCENT — what the player was actually hitting

Reconstructed from the walk graph and replayed headlessly.

### The seam inventory of the descent (shipped)

The loop stairs' yard (`shelf-homes`, h 19) drops 5 m to the quay on two flights. Every
band the descent crosses or grazes:

| # | seam | at (runtime) | height above deck | where it sits |
|---|---|---|---|---|
| 1 | shelf-east↔loop-stairs | `[47.55, 19.07, −8.20]` | +5.1 m | on the shelf street, fine |
| 2 | loop-stairs↔**quay-west** on `shelf-homes__quay-deck` @t 0.500 | `[54.27, 15.14, −9.81]` | **+1.1 m** | on the flight's lower landing, **4.3 m before the deck** |
| 3 | loop-stairs↔**quay-east** on `shelf-homes__market-stalls` @t 0.500 | `[56.21, 17.24, −9.17]` | **+3.2 m** | on the flight's **upper** landing, **5.5 m and 3.2 m of drop before the deck** |
| 4 | **quay-west↔quay-east** on `quay-deck__market-stalls` @t 0.485 | `[56.16, 14.00, −13.51]` | 0 | **in the middle of the open plaza**, 2.8 m from its centre |
| 5 | quay-east↔lockhead | `[61.79, 14.00, −13.73]` | 0 | at the plaza's east lip, fine |

**Seams 2 and 3 are 2.04 m apart in plan** and 2.1 m apart in height — two camera
boundaries inside a 2 m square, kept apart only by the 1.6 m height gate. Seam 4 sits
on open floor with three ribbons radiating through it.

### What the simulated walk produced

- `quay-deck__market-stalls`, walked **west**: `quay-west→quay-east→quay-west` — **two
  cuts 4 cm apart.** This is the user's "triggering scene changes between the 3
  unexpectedly", exactly.
- `shelf-homes__market-stalls`, walked **up**: one positional **correction**
  (`quay-west→loop-stairs`) with no seam crossed at all.
- `market-stalls__lockhead`: one positional correction.
- Descending the market flight: the cut fires **3.7 m into a 10.9 m flight**, and
  because a cut **teleports the player to its arrival point**, it lands them
  `[58.2, 15.93, −10.22]` — **3.6 m further down and 1.9 m lower**, behind 700 ms of
  fade, mid-stride on a staircase.
- And after that teleport the player stands on `loop-stairs`-owned treads with
  `quay-east`'s camera up. They are off their own ground for **0.49 m of the 1.5 m
  correction grace**. Keep walking and nothing happens; **pause for a third of a second
  — which is what a confused player does — and the camera changes again.** That is the
  "unexpected" in the report: the second change is timing-dependent, not
  position-dependent.

### The root causes (two, both structural)

**(a) `quay-east` is a second camera on somebody else's floor.** The map gives
`quay-deck` extent 5.5 and `market-stalls` extent 3, centres 5.7 m apart, so
`walk_lm_quay-deck` (x 47.9–58.9) and `walk_lm_market-stalls` (x 56.09–62.09)
**physically overlap at identical height**. `quay-east` owns 2 walk meshes and 5.8 m of
route, **both meshes inside quay-west's region**, and solves at its `minDist` floor of
18 m against a natural fit of 10.8 m. There is no threshold between the harbour deck
and the market because they are one deck. → **canon §3.**

**(b) The seam placer was sliding every `to`-endpoint seam the full width of its
window.** See canon §4. This is why both flight cuts sat at exactly `t=0.500` — as far
from the landing as ownership allowed.

---

## 2. THE BRIDGE — junction #2

`weave-huts__keepers-cottage` is a **21.5 m** span. The Crossing owned all of it; the
two cuts sat at t 0.188 (4.1 m along) and t 0.591 (12.7 m along) — **both mid-plank**,
leaving 12.9 m of bridge walked under a camera that did not own it.

**Walked westward, from the cottage, the shipped data strobes forever:**

```
s= 4.43  CORRECTION cottage -> crossing     (inside the 8.8 m mismatch)
s= 7.73  cut        crossing -> cottage     (teleported back east)
s= 7.60  CORRECTION cottage -> crossing
s= 7.75  cut        crossing -> cottage
 ... 30 cuts + 31 corrections, never terminating
```

The correction fires inside the ownership mismatch, which re-arms the seam, which cuts
the player backwards into the mismatch. It is a hard softlock of the camera layer, and
it is in shipped data.

**Design chosen: (b) — the Crossing keeps exactly the bridge, both seams at the
abutments.** The span is 21.5 m; at that length stepping on and stepping off genuinely
read as entering and leaving a place, which is the condition the coordinator set for
preferring (b) over retiring the camera.

**And it needs no ownership change at all.** The placer fix alone moves the cottage-side
seam from t 0.591 to **t 0.812** — `[88.58, 7.55, −22.39]`, 1.5 m off the cottage
abutment — while the weave-side seam stays at t 0.188, 2.8 m off the weave-huts pad.
Result: **2 cuts, 0 corrections, no oscillation, in both directions.** The crossing
declares `thresholdPair: true` to spend its second cut legitimately.

> **FOR THE CROSSING CUSTODIAN: the camera is NOT retired.** Its record-shot vantage
> does change if the water-facing re-aim in §5 is taken (yaw 96→225, pitch 10→28), which
> is a **user taste call**, flagged as such. The seam positions move regardless, so the
> abutments — where the player now steps into and out of the shot — are at
> `[75.19, 7.77, −22.64]` (weave end) and `[88.58, 7.55, −22.39]` (cottage end). Those
> are the two metres of plank that want to *look* like thresholds.

---

## 3. JUNCTION #3 — the waterfront boardwalk (found by the gate, not by a report)

The map models the boardwalk as two edges lying on top of each other:
`deep-stairs-foot__fish-dock` (x 43→59) duplicates the middle of
`fish-dock__winch-foot` (x 59→30). Both carried a fishdock↔waterfront seam, 3.6 m apart,
so walking the boardwalk fired one seam and then bounced between the two:

```
fish-dock__winch-foot:  1 cut + 2 CORRECTIONS  (waterfront->fishdock->waterfront)
```

**Fix:** align the two splits so the bands land 0.6 m apart and read as one seam
(canon §5.1, co-located twins). Measured result: **1 cut, 0 corrections.**

The gate also found, with no user report:

- **`boatwright-shed__pitch-kettle`** — walking between two of the *boatyard's own*
  landmarks fired `boatyard→waterfront` and straight back. The `winch-foot__slipway`
  band lay across the shed's own path.
- **`quay-deck__deep-stairs-head`** — walking the quay's west arm out to the stair head
  fired `quay-west→deep-stairs` and back. The deep-stairs seam sat at `dy = 1.60` from
  the deck arm against a `cutVTol` of 1.6 — on the tolerance boundary exactly.

---

## 4. THE OPTIONS, WITH NUMBERS

For the quay junction the brief asked for three options measured before choosing.

| | (a) retire quay-east | (b) re-split ownership only | (c) band/hysteresis tuning only |
|---|---|---|---|
| cameras | 17 → **16** | 17 | 17 |
| descent cuts per passage | **1** | 1 | 1–2 |
| the plaza ping-pong (`quay-west↔quay-east` 4 cm apart) | **gone** — no seam exists | remains: the seam must still cross open floor | remains |
| the standing path-overlap warning | **gone** | unfixable: any seam on the plaza sits on the pilot-cluster ribbon | unfixable |
| `quay-west` charPx | **93..54 → 88..52** (gate 50) | 93..54 | 93..54 |
| canon §3 (no sliver) | **passes** | still fails (5.8 m of route, 0 exclusive meshes) | still fails |
| what is lost | the market close shot (charPx 143..91, 85 % visible spawns) | — | — |

**(c) is measurably the weakest and is recommended against.** Widening the bands makes
the plaza seam catch *more* of the pilot-cluster ribbon; narrowing them below the 1.4 m
floor is not authorable; and neither touches the two structural causes. Raising
`cutClearance` further — the one knob that helped last night — makes the boatyard seam
strictly worse (§5.1 of the canon: its clean window and its hysteresis window already
have empty intersection at 1.6).

**(b) is necessary but not sufficient**, and it is *in* the chosen design — the placer
fix is exactly "re-split so the descent belongs to loop-stairs until the bottom". It
moves the market-flight cut from t 0.500 to t 0.633 and the deck-flight cut from
t 0.500 to t 0.558. But with `quay-east` alive the plaza still has an invisible line
across it that fires twice in 4 cm.

**Chosen: (a) + (b).** Retire `quay-east`; let the corrected placer put the flight cuts
where the author asked.

**What is lost, honestly.** `quay-east` was the market close shot — 143..91 charPx
against quay-west's 88..52, and 85 % visible spawns. The market is now read at
~52–60 charPx from the harbour shot. That is the price of the plaza being one place.
The mitigation, if the user misses it, is a *zoom* on the same camera, not a second
camera on the same floor.

**What it costs quay-west:** the region grows from 25.0 m to 28.2 m of span; standoff
29.34 → 29.24 m (it also gained the deep-stairs head landing, which pulled the aim);
charPx **93..54 → 88..52**, still clear of the 50 px legibility gate. The merge is
almost free because the market pad only extends the deck 3.2 m east.

---

## 5. THE BOATYARD — pin lifted

The user's ruling supersedes the v10 acceptance. The bake log agrees: boatyard's
spawn-visibility probes were **48.4 %**, the worst in town, and its own route probes
read `visiblePct 0` on two of five routes.

**The occluder.** The accepted frame stands at `[37.6, 25.4, 8.5]` and looks *along the
slipway* to `[14.4, 30.4, 3.4]`. The boatwright shed sits at x 24.67 — **on that axis,
halfway along it.** Any shot composed along the yard has the shed in the middle of it.

**A literal cliff-side camera is impossible here, and here is the arithmetic.** The
gorge's near wall falls ~24 m over ~28 m of horizontal (≈40°). A camera at standoff `D`
and pitch `p` sits `D·cos p` landward and `D·sin p` up, so clearing the wall needs
`tan p > tan 40°`, i.e. **p > 40°** — a bird's-eye shot, not "looking out towards the
water". A pure yaw-270 boatyard camera at D=27, p=20 lands at map `(19, 1.1, 11.8)`
where the wall is at h≈23: **buried in rock.**

**What is possible, and what is proposed:** put the camera **upstream** on the cliff
side and look **downstream and outward**. That is cliff-side in the along-gorge sense,
it is in open air, and the river fills the frame behind the yard.

```
boatyard   yaw 205   pitch 28   margin 0.07     (pin removed, pos/aim removed)
  solved   pos [-1.04, 17.26, 15.55]  aim [18.99, 26.59, 3.80]  dist 25.02
  charPx   135..59        in-frame 1.000        wall clearance 4.2 m
  water    0 % -> 60.8 %
```

The shed is now the **farthest** object in the frame rather than the middle one, and
the whole boardwalk approach runs across the frame instead of down its axis.

The pin also resolves the old off-frame exit: `winch-foot__slipway` no longer needs the
0.52 ownership split that was authored *around* the hero frame, so the split moves to
**0.20** — which is what clears the shed pad and kills the
`boatwright-shed__pitch-kettle` double cut.

> **Not verified by ray-cast.** No blend access during design; occlusion is the bake's
> `visibleFrac` job. The geometric case is above; **confirm at bake and re-aim if the
> probe disagrees.**

---

## 6. WATER-FACING SURVEY

**Method.** Analytic ray tally: 960 rays per frame against the town's 2.5-D silhouette
— the river surface from `map.river` (pool level by x, y ∈ [26, 74]), an empirical near-
wall profile `h(y)` fitted from the walk network's own lowest surface per y-bin, and the
far wall. Town props are not modelled, so the number is an **upper bound on water
pixels**; it is used for **ranking and for before/after comparison of a re-aim**, which
is what the survey needs. Every candidate re-aim is re-solved and rejected unless it
keeps `inFrame = 1.000`, `charPxFar ≥ 55`, is not `maxDist`-capped, and leaves the
camera ≥ 2 m clear of the near wall.

**The finding: eleven of seventeen shots have zero water in frame.** The whole upper
town — quay, shelf street, lockhead, cottage, crossing, loop stairs, gate — stands out
over the gorge and looks *into* the wall, which is the town's own documented default
("most shots stand out over the gorge (yaw near 90) and look back into the wall").
Mean water in frame: **10.1 %**.

### Proposed (in this patch)

| shot | yaw/pitch | water % | charPx | why it is safe |
|---|---|---|---|---|
| **boatyard** | 348/12 → **205/28** | 0 → **60.8** | 135..59 | pin lifted by user ruling; §5 |
| **cottage-steps** | 128/13 → **330/23** | 7.8 → **66.8** | 101..73 → **193..93** | transit vignette, **no landmarks** — lowest art risk in town, largest gain. Camera downstream at `[104.25, 18.21, 11.16]`, looking back up the flight with Lock Five's pool below. |
| **crossing** | 96/10 → **225/28** | 0 → **60.7** | 93..76 → **154..75** | the bridge art is being rebuilt right now, so the re-aim is free — but see the caveat |

> **CROSSING IS A USER TASTE CALL.** The blessed description is "side-on to the span,
> the plank bridge sagging across frame". yaw 225 changes it to *along* the span, from
> the weave end, looking down-river — the bridge leads the eye out over the water
> instead of crossing the frame. That is arguably a better postcard and it is exactly
> what "look out towards the water" asks for, but it is not the shot that was blessed.
> **Keeping yaw 96/pitch 10 costs the patch nothing** — the seam fixes in §2 are
> independent of the framing. Rule either way.

### Measured, not proposed (tier 2 — recommend after the user sees the first three)

| shot | best feasible | water % | charPx | note |
|---|---|---|---|---|
| lockhead | 325/23 | 0 → 46.3 | 157..67 | camera up the wall at y 4.9; profile is x-independent there, wants a real check |
| fishdock | 335/23 | 40.3 → 61.8 | 136..58 | already water-heavy; +21.5 |
| waterfront | 340/23 | 40.1 → 55.6 | 159..76 | already water-heavy; +15.5 |
| north-landing | 336/26 | 44 → 57.1 | 113..55 | already the goodbye shot; +13 |
| weave / deep-stairs / cottage | 315/23, 335/23, 210/23 | +40 to +57 | — | large gains but they reverse three *blessed* compositions at once |

**Structurally inward-facing, stay as they are:** `shelf-west`, `shelf-east`,
`loop-stairs`, `gate`, `quay-west`. Their regions are pinned against the wall at h 14–24;
every water-positive aim for them puts the camera **behind the cliff rim** looking down,
which is a wholesale restyle of the town and would show building backs and un-modelled
tableland. The sweep's global optimum wanted exactly that (yaw ~300, pitch 30, +27 to
+48 % water each) and it is rejected on those grounds, with the numbers recorded here so
the choice can be revisited deliberately.

**Result of what is proposed: mean water in frame 10.1 % → 21.8 %.**

---

## 7. THE PATCH

Two tool changes are **already applied** (they change no shipped artifact until the
generators are re-run); the `cameras.json` change is a proposal for the coordinator.

### 7.1 Applied: `tools/cine_regions.mjs` — the placer scan order

In `cutGeometry()`, the slide-window candidates are now ordered by distance from the
authored position and the **nearest** acceptable one wins, instead of the first one
found scanning the window end to end. ~15 lines, commented in place. This is the root
cause of canon §4 and it is what fixes the bridge.

### 7.2 Applied: `tools/seam_test.mjs` — the gate

New. Invariants 1/2/3/5/6 as hard assertions, town-agnostic, `--cameras` to test a
proposal before writing anything.

### 7.3 Proposed: `public/townmap/dellhollow.cameras.json`

**a. DELETE the whole `quay-east` camera record.**

**b. `quay-west`** — absorbs the market and the deep-stairs head landing:

```jsonc
"name": "The Harbour Deck",           // was "The Harbour Deck"; consider "…& Market"
"owns": {
  "landmarks": ["cookhouse", "notice-board", "quay-deck", "deep-stairs-head",
                "market-stalls"],                                   // + market-stalls
  "edges": ["quay-deck__cookhouse", "quay-deck__notice-board",
            "quay-deck__deep-stairs-head",
            "quay-deck__market-stalls",                             // + from quay-east
            "deep-stairs-head__deep-stairs-foot@0..0.22"]           // + the stair head
}
```

`deep-stairs-head__deep-stairs-foot@0..0.22` pushes the deep-stairs seam from t 0.146
(h 12.33, `dy` 1.60 from the deck arm — on the tolerance boundary) to t 0.220
(h 11.13, `dy` 2.98). Kills the `quay-deck__deep-stairs-head` double cut.

**c. `deep-stairs`** — the other side of that split, and it declares its pair:

```jsonc
"owns": { "landmarks": [], "edges": ["deep-stairs-head__deep-stairs-foot@0.22..1"] },
"thresholdPair": true
```

Bonus, measured: deep-stairs' own framing improves from **78..60 to 94..70 charPx**
(standoff 30.67 → 25.46) because it no longer has to frame the stair head's landing.

**d. `crossing`** — declares its pair; framing change is the §6 taste call:

```jsonc
"thresholdPair": true,
"framing": { "yaw": 225, "pitch": 28, "margin": 0.13 }   // OPTIONAL — user ruling
```

**e. `cottage-steps`** — declares its pair, and the water re-aim:

```jsonc
"thresholdPair": true,
"framing": { "yaw": 330, "pitch": 23, "margin": 0.09 }
```

**f. `waterfront`** and **`fishdock`** — co-locate the boardwalk seams, and hand the
boatyard approach over:

```jsonc
// waterfront
"edges": ["winch-foot__slipway@0..0.20",          // was @0..0.52
          "fish-dock__winch-foot@0.45..1",
          "deep-stairs-foot__fish-dock@0..0.174"] // was @0..0.4
// fishdock
"edges": ["fish-dock__winch-foot@0..0.45",
          "deep-stairs-foot__fish-dock@0.174..1", // was @0.4..1
          "tenant-shack__fish-dock@0.35..1"]
```

**g. `boatyard`** — pin lifted:

```jsonc
// REMOVE: "pin": true, "_pin_why": …, "pos": […], "aim": […]
"framing": { "yaw": 205, "pitch": 28, "margin": 0.07 },
"owns": { …, "edges": ["winch-foot__slipway@0.20..1", …] }   // was @0.52..1
```

Every `_framing_note` / `_owns_note` on a changed record should be rewritten to say what
this document says; the existing notes on `quay-east` and `boatyard`'s pin become false
the moment the patch lands.

---

## 8. PREDICTED RESULT

**Canonical descent (shelf street → shelf-homes → either flight → the quay): exactly
one cut per passage.**

```
armor-shop__shelf-homes      shelf-east > loop-stairs      1 cut
shelf-homes__quay-deck       loop-stairs > quay-west       1 cut   (t 0.500 -> 0.558)
shelf-homes__market-stalls   loop-stairs > quay-west       1 cut   (t 0.500 -> 0.633)
quay-deck__market-stalls     (no cut — one plaza, one shot)
market-stalls__lockhead      quay-west > lockhead          1 cut
```

and, for the bridge:

```
weave-huts__keepers-cottage  weave > crossing > cottage    2 cuts, both at abutments
                             (declared thresholdPair; was 30 cuts + 31 corrections west-bound)
```

Town-wide, `node tools/seam_test.mjs`: **294 assertions ok, 0 failed**, 2 annotated
warnings (the `winch-foot__slipway` geometric exception, canon §5.1).

## 9. RE-BAKE LIST

The tranche-2 bake (9ed7591) made all 17 plates current. Against that state:

**Every remaining camera moves, so the batch is all of them — a full 16-camera bake.**
Reasons, so this is a fact and not a shrug:

- the coordinator's `cutClearance` 1.0→1.6 re-solve already left **14** cameras drifted;
- the placer fix moves **11 of 20 seams**, and every moved seam changes the arrival and
  exit points the solver frames, so a shot two hops from a change still re-solves;
- `quay-east` is deleted (−1 plate, and its art can be dropped);
- `quay-west`, `deep-stairs`, `boatyard`, `cottage-steps` and (if ruled) `crossing`
  change region or framing outright.

**16 cameras, one batch, overnight.** Delete `public/assets/scenes/del-cine/cameras/quay-east/`
when it lands.

## 10. FOLLOW-UPS (not tonight)

1. **`winch-foot__slipway` wants a map fix**, not a camera fix: `walk_pad_boatwright-shed`
   sits on the boardwalk, and while it does, no seam on that edge can satisfy both
   canon §1 and §5. Moving the shed pad ~2 m north opens a clean window.
2. **`deep-stairs-foot__fish-dock` duplicates `fish-dock__winch-foot`** in the map. The
   co-located-twin exemption is a workaround for a redundant edge.
3. **Invariant 4b** — band position versus local corridor width, as a number.
4. **`frameExits`** — deliberately untouched; the user's own gate.
