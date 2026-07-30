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
