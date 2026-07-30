# THE SEAM CANON

**What this is.** The rules a cinematic town's camera cuts must obey, each one written
because a player hit its violation in real play, and each one enforced by
`tools/seam_test.mjs` so it cannot rot. Dellhollow is the town that taught us these;
Emberbrook, and every town after it, inherits them for free.

**Status.** Ratified against live play on 2026-07-30. Dellhollow passes at 294
assertions with one annotated geometric exception (§5.1). Before the patch it failed
20.

---

## 0. Why coverage was never the problem

`cine_test.mjs` proves a strong thing: every walkable metre of the town belongs to
exactly one camera, every arrival is on screen, and the shot graph is connected. On
2026-07-30 it was **green, 666 assertions, zero failures**, and in the same hour a
player walking the town reported, unprompted:

> "quay-west, quay-east, and loop-stairs are too close and it's very confusing where
> the camera angle changes. When I'm descending the stairs, I keep accidentally
> triggering scene changes between the 3 unexpectedly and that's jarring."

> "Similar issue with the seams between the cottage and the weave. There are too many
> transitions as I'm walking on this one small bridge."

> "The boatyard shot is almost completely occluded by this one roof that is covering
> the path where my player is walking."

Coverage is a statement about the **ownership table**. What the player experiences is
the **sequence of camera changes produced by walking**, and nothing measured that.
Reconstructing the bridge walk headlessly found something worse than "too many
transitions": walking *westward* off the cottage, the camera changed **thirty times and
never stopped** — a hard strobe, in shipped data, that every existing test passed over.

So the canon's first principle is a method, not a rule:

> **Measure the walk, not the table.** Every invariant below is asserted against a
> headless replay of `play3d.html`'s own `sgTick()` + `sgCorrect()` — the band test,
> the arm/disarm rule, camera gating, and the 20-tick positional correction — walking
> the town's real routes at the runtime's real speed. A green gate is a claim about
> the runtime, not about a model of it.

---

## 1. NO-RETURN — every arrival lands clear of the band it just crossed

**Rule.** After a cut, the player must stand at least **0.5 m** (one stride) past the
band on the band's own normal, or be separated from it in height. `cutClearance` (1.6 m)
is the target the solver aims for; 0.5 m is the floor the gate refuses to cross.

**The failure that motivated it.** The deep-stairs↔waterfront arrival sat **+0.012 u**
past its own band on a switchback. One step forward re-entered the band and cut
straight back: a progression loop the user hit live. Raising `cutClearance` 1.0→1.6
(eabb63b) moved the *target*; it did not make the *result* checkable. Where the
geometry cannot satisfy the target the placer silently downgrades to an arc-length
back-off, and arc length is not clearance — 2.4 m along an S-bend is 0.7 m along the
seam normal.

**Enforcement.** `seam_test.mjs` measures `|along| − cutThickness` for every arrival of
every directed cut and asserts it, rather than trusting that the solver was satisfied.

---

## 2. ONE-CUT-PER-PASSAGE — the core rule

**Rule.** Walking one map edge end to end, in either direction, changes the camera **at
most once** and fires **zero** positional corrections.

A *passage* is one map edge — the smallest unit of travel the town's own topology
defines. The gate walks all of them, both ways, headlessly.

**Threshold pairs.** A shot that *is a place you enter and leave* — a bridge, a
tunnel, a flight of stairs with its own screen — legitimately costs two cuts. It gets
them only by declaring `"thresholdPair": true` on its camera record, and the allowance
is spent only when all three hold:

1. the passage has exactly two cuts,
2. the second leaves the same shot the first entered,
3. both cuts are on the edge being walked.

Without conditions 2 and 3 the allowance launders unrelated defects: walking the
quay's west arm out to the stair head fired the *deep stairs'* seam and fired straight
back, and "the deep stairs are a threshold pair" would have excused it.

**Corrections are never allowed on a normal route.** `sgCorrect()` exists for falls,
knockbacks and slides — for a player who never crossed a seam at all. If it fires while
somebody is *walking a road*, a seam is in the wrong place. It is also the mechanism
that turned the bridge into a strobe: walking west off the cottage, the correction
fired inside the ownership mismatch, which re-armed the seam, which cut the player back
east, which put them back in the mismatch.

**The failures that motivated it.** Both user reports above; the 30-cut bridge strobe;
the market flight, whose cut fired **3.7 m into a 10.9 m descent, 3.2 m above the deck,
and teleported the player 3.6 m down the stairs**; and the harbour deck, where walking
west across one open plaza fired `quay-west→quay-east→quay-west` in under a metre.

---

## 3. NO SLIVER SHOTS — a camera must own somewhere

**Rule.** Every camera owns at least **10 m of walkable route** and at least **one walk
mesh that lies inside no other shot's region**.

The test is deliberately in **route metres and exclusive floor**, not mesh count.

**The failure that motivated it.** `quay-east` ("The Market") owned two walk meshes and
**5.8 m of route**, and **both of its meshes sat inside the harbour deck's own pad** —
the map gives `quay-deck` extent 5.5 and `market-stalls` extent 3 with centres 5.7 m
apart, so the two shots were looking at *the same floor* with an invisible line drawn
across it. It solved at its `minDist` floor of 18 m against a natural fit of 10.8 m,
which is the solver saying "there is not enough here to be a shot". It produced a user
complaint within an hour of real play.

The counter-example proves the metric is the right one: **the Crossing owns three walk
meshes and 21.5 m of bridge that nothing else touches.** It is a real place, it keeps
its camera, and mesh count would have condemned it.

---

## 4. SEAMS SIT AT THRESHOLDS — and the placer must honour the author

**Rule.** A cut belongs at an articulation — a doorway, a landing, an abutment, the lip
where a plaza narrows to a plank — and never mid-span of an open walk.

**This is now largely structural rather than aspirational,** because the reason
Dellhollow's seams were *not* at thresholds turned out to be a bug, not a judgement:

> `cutGeometry()` builds a slide window around the authored seam position and scans it
> **end to end, keeping the first acceptable candidate**. For a `from`-endpoint the
> window starts at the authored offset, so `from` seams landed where the author asked.
> For a **`to`-endpoint** the window is `[t − slide, t]`, and for an **authored `@t`
> split** it is `[t − slide/4, t + slide/4]` — in both cases the scan *starts at the far
> end*. So every `to` seam and every authored split slid the full window by default.

That is why five of Dellhollow's cuts sat at exactly `t=0.500`: not because 0.500 was
right, but because it was as far from the landmark as ownership allowed. The player
felt it as a camera that changed halfway down a flight of stairs and as two cuts
mid-plank on a bridge whose ends were the obvious places to cut.

**The fix** (in `tools/cine_regions.mjs`, this pass): order the candidates by distance
from the authored position and take the **nearest** acceptable one. The window still
says how far a seam *may* slide to dodge a hairpin or a neighbour's path; it no longer
says sliding is free. Measured effect on Dellhollow, with no other change:

| seam | was | now | what moved |
|---|---|---|---|
| crossing↔cottage (bridge) | t 0.591, mid-plank | t 0.812, at the cottage abutment | +4.8 m |
| loop-stairs↔market flight | t 0.500, 3.2 m above the deck | t 0.633 | +2.3 m down |
| cottage-steps↔lockfive | t 0.500 | t 0.701 | +2.4 m |
| deep-stairs↔waterfront | t 0.637 | t 0.730 | +2.3 m |
| waterfront↔boatyard | t 0.385 | t 0.520 | +1.5 m |

The bridge strobe **disappears from this one change alone** (30 cuts + 31 corrections →
2 cuts, 0 corrections, both at abutments).

**Still a review line, not yet a number.** Band position versus local corridor width is
measurable and should become invariant 4b; tonight it is a checklist item:

- [ ] Does the seam sit where the walk **narrows** (stair landing, plaza lip, abutment)?
- [ ] Would a player describe the two sides as **different places**?
- [ ] Is the seam **off the pad** you stand on and **off the open floor** you cross?

---

## 5. NO PATH-OVERLAP — a seam band never sits on a route it does not separate

**Rule.** If a seam's band contains a walk mesh belonging to some other path, that is a
**failure**, not a warning. A player walking that other path gets cut for no reason.

**The failures that motivated it.** The original rim-road bug (a seam at the gate
stair's head caught walkers heading for the cargo winch). And then four warnings that
stood, printed on every solve, for a week — one of which the gate turned into a
reproduction on its first run:

> Walking `boatwright-shed__pitch-kettle` — two of the **boatyard's own** landmarks —
> the player was cut `boatyard→waterfront` and immediately back. The
> `winch-foot__slipway` band lay across the shed's own path.

A warning nobody owns is a defect nobody owns. In the gate it exits non-zero.

### 5.1 The one exemption, and the one annotated exception

**Exempt: co-located twins.** A foreign path that is split between the *same two shots*
within 1.5 m of this seam is not a wrong cut — two coincident bands separating the same
pair fire once, and the simulated walk is what proves it. Dellhollow's waterfront
boardwalk needs this: the map models it as two edges lying on top of each other
(`deep-stairs-foot__fish-dock` duplicates the middle of `fish-dock__winch-foot`), so
the fishdock↔waterfront frontier necessarily crosses both. The patch aligns the two
splits so the bands land 0.6 m apart and the walk fires once.

**Annotated exception: `winch-foot__slipway`.** This 11.1 m boardwalk admits **no**
clean seam, and the proof is arithmetic:

- hysteresis needs 2.7 m of clear path (`cutThickness` 1.1 + `cutClearance` 1.6) on
  both sides, leaving the usable arc window **[2.68 m, 8.43 m]**;
- `walk_pad_boatwright-shed` (x 23.37–25.97, 1.2 m above the boardwalk, inside
  `cutVTol`) blocks a band anywhere in the arc window **[2.68 m, 8.56 m]**.

The two windows have empty intersection. The patch takes the wrong-cut invariant as
primary — a wrong cut is worse than a thin arrival — places the seam at t=0.231, clear
of the shed pad, and accepts an arrival that falls back to arc-length back-off. The
simulated walk fires once in each direction with no oscillation. **The real fix is in
the map** (the boatwright shed's pad sits on the boardwalk); it is logged as a follow-up
and the gate reports it as a soft warning, not a pass.

---

## 6. Invariants absorbed from the existing suite

- **Every arrival on screen** — `cine_test.mjs` §B, unchanged.
- **Exits in frame** — `frameExits`, the solver default for new towns. Dellhollow opts
  out in its data while its backdrops are baked against the old frames; **that flag is
  out of scope here and is the user's own gate.**
- **Ownership-mismatch budget** — metres of floor walked under a camera that does not
  own it. This is not cosmetic: it is exactly where `sgCorrect()` fires, and it is what
  turned the bridge into a strobe.

  The budget is **derived, not chosen**: `cutOffset × (endpoint seams) × 1.45`. Every
  endpoint seam sits `cutOffset` out from its pad *on purpose*, so a town is mismatched
  by construction; the 1.45 is the allowance for seams the geometry forces to slide
  further. No single stretch may exceed **7 m** (a switchback's seam legitimately
  slides most of a leg to find clean ground).

---

## 7. Running the gate

```
node tools/seam_test.mjs                      # dellhollow, the shipped cameras
node tools/seam_test.mjs --town emberbrook    # any town with a <town>.cameras.json
node tools/seam_test.mjs --cameras townmap/proposal.cameras.json   # a PROPOSAL
node tools/seam_test.mjs --verbose            # every passage, not only failures
```

It reads the same `cine_regions.mjs` brain as the solver, the scene-graph generator and
`cine_test.mjs`, so it cannot drift from what ships. `--cameras` is the important one:
**a camera proposal is now testable before anything is written to `public/`**, which is
how this pass was designed without touching a shipped file.

**Verification order for a camera change:**

1. `node tools/seam_test.mjs --cameras <proposal>` — the seams
2. apply the change, `node tools/cine_solve.mjs` — the framing
3. `node tools/scenegraph_derive.mjs` — the runtime edges
4. `node tools/cine_test.mjs` — coverage, framing, chain, graph, hysteresis
5. `node tools/seam_test.mjs` — the seams again, against what shipped
6. re-bake only the cameras whose solved `pos`/`aim` moved

### Browser sessions: **`&nomusic=1`, always**

Any browser-driven verification — `tools/cine_walk.js`, a playtest tab, a screenshot
run — **must** append `&nomusic=1` to the `play3d.html` URL, or set
`window.__NOMUSIC = true` before sending input. Agent test sessions were audibly
playing music on the user's machine. This is a standing rule, not a courtesy: a headless
check has no business making noise in somebody's room.

---

## 8. For the next town

When Emberbrook gets cameras, the canon applies with no new authoring:

- Author ownership so that **each flight, bridge and plaza has exactly one owner**, and
  that owner also owns the **junction** it hangs off. (The loop stairs already taught
  this: a transit shot that owns a flight but not its head needs two seams inside seven
  metres.)
- Do not give a camera to a place that is **less than 10 m of route** or that shares
  its floor with a neighbour. If a shot wants to be tighter than its neighbour on the
  *same* floor, that is a zoom, not a cut.
- Declare `thresholdPair` on the bridges and the stairwells, and on nothing else.
- Run the gate **before** the bake, not after. Every defect in this document was
  cheaper to find in a simulated walk than in a 17-camera render.

---

## 9. Two traps that cost time on 2026-07-30

### 9.1 `yaw` is measured FROM THE AIM TO THE CAMERA. Both directions look plausible.

`cameras.json` states it: *"the direction FROM the aim point TO the camera in the map's
xy plane"*, i.e. `atan2(pos.y - aim.y, pos.x - aim.x)`. Computing it the other way round
(`aim - pos`) returns a number that is exactly **180 degrees off**, and because the
convention also has `90 = out over the river` and `270 = into the cliff face`, an
inverted reading reports a cliff-side camera as water-side and vice versa.

This happened: the Crossing's solved frame (`pos 67.916,10.857,18.133 ->
aim 79.867,22.807,9.147`) was read as "yaw ~45, sitting on the water side". By the file's
own convention it is **yaw 225, and the camera is cliff-side** -- `pos.y 10.86` against
`aim.y 22.81`, and smaller y IS the cliff. The composition complaint was real and
independent; the yaw diagnosis was not.

**Check it with the position, not the angle.** `pos.y < aim.y` means cliff-side, always,
in any town whose map runs y from cliff to water. One comparison, no trigonometry, no
convention to remember.

### 9.2 IN FRAME is not VISIBLE, and exit-seam framing cannot fix occlusion

`frameExits` guarantees a shot frames the seams it exits through. It says nothing about
whether anything is standing in front of them.

The town's arrival staircase measured **100% on-screen from both** the gate and the west
shelf, and **12.2% and 25.6% VISIBLE** (`tools/shot_probe.py`, against the shipped depth
plates). Flipping `frameExits` would have re-solved both shots, re-baked both plates, and
changed the number by nothing, because the stair was never off-frame -- it was behind the
rim lip, a surface at h 24-27 sitting 6-7 m in front of it.

### 9.3 THE DIAGNOSTIC STEP: measure WHY a thing is invisible before choosing the fix

Promoted to a named step because it is the one that would have saved the whole detour,
and because "invisible" has at least four causes with four different fixes:

| symptom | measured by | the fix |
|---|---|---|
| **off frame** — the point projects outside ndc | `cine_solve` in-frame fraction; `frameExits` | re-solve; the solver does it by construction |
| **occluded** — in frame, something in front | `tools/shot_probe.py` against the baked depth | move the camera, or cut the occluder back |
| **too small** — visible but unreadable | `charPx` in the solve report | shorter standoff, tighter margin, or split the region |
| **not there** — nothing was ever built | `tools/plate_flat.py`, or the plate itself | art, not cameras |

**There is a fifth symptom and it is not a cause of "invisible" at all: all four rows
above can pass and the player still reads the wrong way on. That one has its own
instrument and its own section — see §10.**

They are not distinguishable by looking at a screenshot and they are not distinguishable
by intuition. The gate staircase read as a framing problem to everyone who saw it,
including the plan to fix it by flipping `frameExits`; it was 100% in frame and 12%
visible, and the fix was **+2.4 m of camera height**. The Boatyard read the same way and
was also occlusion. Two reports, one misdiagnosis each, both caught by one probe.

**Run the probe first. It costs seconds against art that already exists; the wrong
diagnosis costs a bake.**

**Before proposing a re-aim for a visibility complaint, probe it.** `shot_probe.py`
answers "is it in frame" and "can it be seen" separately, in seconds, against art that
already exists. The fix that measurement produced was also far cheaper than the one
framing would have implied: the gate needed **+2.4 m of camera height** (pitch 22 -> 28)
and the west shelf **+1.2 m** (pitch 10 -> 13), each costing 0-2 px of character height,
because on many rays the sightline was missing the lip by as little as **4 cm**.

---

## 10. THE PERCEPTUAL GATE — the fifth cause of "invisible"

§9.3's table has four causes and four fixes. It is missing the one the user actually
reported, because the one the user reported leaves no geometric trace:

| symptom | measured by | the fix |
|---|---|---|
| **perceptually misleading** — in frame, unoccluded, big enough, and still read the wrong way on | `tools/nav_eval.mjs` | composition and route affordance: the art, not the camera |

**How it is measured.** A context-free vision model is shown ONE image — the shot's baked
plate with the character composited at an entry spawn — and nothing else: no map, no town
name, no route data, no memory of any other shot. It answers, in image coordinates, where
it would walk to continue onward. Those waypoints are unprojected through that shot's own
baked depth map, and the resulting world points are walked under **play3d.html's own
WALKLOCK stepping rules** against the **shipped** `scenegraph.json` seams. A trial passes
if the naive reading crosses an exit seam **onward** — to a shot other than the one it
arrived from. Shot score = pass rate over N readings. Run:

```
node tools/nav_eval.mjs --judge oracle-world      # ALWAYS FIRST: checks the walker
node tools/nav_eval.mjs                           # the town, N=5, one run = one folder
node tools/nav_eval.mjs --compare <runA> <runB>   # the eval-of-the-eval
```

and read the result in `docs/qa/naveval/viewer.html?run=<stamp>` — the input, the prompt
verbatim, the waypoints, the ground truth and the walk, on one page, each overlay
independently switchable. **The viewer is not a convenience. A perceptual metric nobody
can eyeball is a number nobody should trust.**

### 10.1 The calibration, reported as measured

Run against the tranche-2 plates (`9ed7591`, where the gate stair was measured at 12.2%
/ 25.6% visible and the crossing's handrails were rendering blockout slabs) and against
tonight's 16-camera surgery bake, same judge, same N:

| shot | tranche-2 | surgery bake | what changed tonight |
|---|---|---|---|
| **crossing** | **0.20** | **1.00** | real rails on all twelve blockout lines, deck, abutment portals |
| gate | 0.00 | 0.00 | pitch 22 -> 28 (+2.4 m of camera height) |
| shelf-west | 0.00 | 0.00 | pitch 10 -> 13 (+1.2 m) |
| town | 0.325 | 0.375 | |

Replicated at **N=10** on those three shots alone: crossing **2/10 -> 10/10**, gate
0/10 -> 0/10, shelf-west 0/10 -> 0/10.

**So the honest reading is: it discriminates, once, and not on the two shots we most
expected.** The crossing separation is large and replicates; it is not sampling noise.
The gate and the west shelf improved on the continuous sub-scores (gate progress
0.39 -> 0.67, waypoints-on-network 0.45 -> 0.66; shelf-west progress 0.34 -> 0.56) and
**did not cross the bar**, which is the finding: the +2.4 m and +1.2 m re-aims of §9.3
made the staircase VISIBLE and did not make the shot LEGIBLE. Those are two different
properties and this is the first instrument that can tell them apart.

Do not read the +0.05 town delta as "the surgery barely helped": twelve of the sixteen
shots had no legibility work done on them tonight, so twelve of the sixteen numbers are
a control group, and the control group did not move. That is what a working instrument
looks like.

### 10.2 The threshold, and why this number and not another

Measured, both bakes, N=5 and N=10: every shot scores **0.00, 0.20 or 1.00**. The
distribution is bimodal with a completely empty band between 0.20 and 1.00 — 32 shot
scores, none in it. So:

> **PERCEPTUAL GATE: a shot scores >= 0.6** — a majority of naive readings leave it
> onward.

0.6 is the midpoint of a **measured empty band**, not a taste call: anything in
(0.2, 1.0) classifies tonight's data identically, so the threshold cannot be tuned to
flatter a bake. Re-derive it if the band ever fills in.

**It is a SCORECARD, not yet a blocking gate.** Dellhollow scores **0.375**, and 10 of
16 shots fail. Wiring a red gate at 0.6 today would only mean turning it off. The
number goes in the bake report; the gate arms when the town clears it.

Two sub-signals are worth naming because they are distinct defects with distinct fixes:

- **reads backwards** — every reading crosses back the way it came (`wentBack` = N).
  Tonight: shelf-east, cottage, cottage-steps, lockfive, all 5/5. The shot's visible
  flow points at the door the player just came through.
- **off the network** — waypoints that unproject to no walkable ground at all
  (`onWalkFrac`). Tonight's floor is the gate at 0.51: half of what a first-time player
  reads as "the way on" is cliff, roof or river.
- **arrives invisible** — `composite.occludedFrac`, a byproduct of building the input
  image and the most surprising thing the tool found. Compositing the character means
  asking what the plate draws IN FRONT of her, and **four of sixteen arrivals are behind
  foreground geometry**: boatyard 1.00 (the plate is 25.71 m nearer than her feet at that
  pixel — she materialises as a ghost on the rim pillar), lockfive 1.00, cottage-steps
  0.999 (4.35 m), loop-stairs 1.00 (4.57 m); shelf-west 0.65, crossing 0.48, shelf-east
  0.45 partly. `cine_test` §B asserts every arrival is ON SCREEN and passes all sixteen.
  **This is §9.2 at the one moment it costs the most — the frame the player appears in.**

### 10.3 Standing rules

1. **Run `--judge oracle-world` before believing any number.** It replays the town's own
   ground-truth route straight into the walker and scores **0.875 (14/16)**. If it drops,
   the walker broke and every score in the run is meaningless.

   The two it misses are the walker's own steering limit and **were checked, not
   assumed**. At the **loop stairs**, the market flight's top tread covers the head of
   the quay flight, and `walkGround` keeps the HIGHEST surface in the step window exactly
   as `play3d.html` does — so the walker descends a legitimate but different flight from
   the one the oracle's route named. At **Lock Five**, the greedy fan cannot back up to
   find the way down off the moorage landing; a WALKLOCK flood fill from that arrival
   reaches **12 744 cells and the far end of the town**, so the player is emphatically
   not stuck and the town is not at fault. Both make the walker PESSIMISTIC on those two
   shots, in the opposite direction from rule 4.
2. **The judge model is pinned** (`gemini-3.6-flash`), never an alias. `gemini-flash-latest`
   would move under the metric and make two bakes incomparable.
3. **Never tune the metric to please the bake.** If a run does not separate, the run says
   so — as §10.1 does.
4. The walker ports WALKLOCK, the step tolerances, the seam bands and `sgCorrect`; it
   does NOT port prop body-box blocking (`boxSolid` needs the 52 MB collide bundle's
   triangles). That omission makes it OPTIMISTIC. Rule 1's steering limit makes it
   pessimistic in two named places. Neither error is silent: the oracle measures both,
   every run.
