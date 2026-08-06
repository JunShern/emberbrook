# Dellhollow pain inventory — the defect map the circulation redesign builds against

2026-08-06, playtest-harvest lane. Sources: queue.json (81 Dellhollow entries, all triaged),
FIXLOG rounds 11–31, the stall census over every run of 2026-08-05/06 (36 runs, incl. the
full NEW GAME run run-20260806-001811, 500 steps, 26/28 beats), and a fresh instrument sweep
on the shipped del-cine bundle (walk_engine_gate, walk_bodygate, _court_probe --comp/--way/
--who, a corridor-width census, a stair-edge census). Every number below names its
instrument. DO NOT build from a row marked LEAD — measure first.

Player cost = steps demonstrably burned in recorded runs (the stall census clusters, 2 m
grid). **Aggregate: 906 of 2,419 Dellhollow steps across all runs were stall steps (37%);
Emberbrook over the same runs: 0 of ~1,700.** Walk efficiency (metres closed / metres
intended, all goto legs, all 08-05/06 runs): **town-wide 52%** — a Dellhollow player loses
half of every intended metre. Per shot: quay-west 30%, lockfive 40%, weave 37%,
loop-stairs 46%, fishdock 47%, cottage 52%, gate 56%, shelf-west 61%, deep-stairs 9%
(31 legs); clean by comparison: lockhead 82%, shelf-east 85%, north-landing 84%.

## §1 The systemic findings (these are what the redesign should treat, not the single rows)

1. **The town is built of ribbons one body wide.** Corridor-width census (walk triangles
   rasterized at 0.25 m; width = 2× clearance to the nearest floorless cell in the same
   tier): **7,938 of 14,555 floor cells (55%) sit in corridors narrower than 1.25 m** —
   under two body widths (body diameter 0.6 m). The standard `walk_e_*` lane is 1.6 m
   wide; every stair flight is 1.4 m; landings 2.0 m. There is no district whose main
   route is generously walkable — the "a lot of narrow spaces" complaint is the network's
   own default lane width. 406 clusters ≥6 cells; worst concentrations are the moorage
   switchback, shelf-homes__market-stalls, quay-deck__pilot-cluster, the shop row, and
   the whole lockhead__keepers-cottage plank run (§3.3).
2. **Five of seven stair flights are still v1 (un-split switchback pivots).** STAIRS_V2
   migration ledger (tools/town_blockout.py:271): migrated = deep-stairs (r21),
   weave-huts__moorage (r29); retired = keepers-cottage__lock-five (r22). **Still v1:
   valley-gate__inn, shelf-homes__market-stalls, loop-landing__quay-deck,
   quay-deck__pilot-cluster** — and this lane MEASURED two of them failing both ways
   (§3.4, §3.5). Round 14's census ("16 of 17 landings roofed by their own flight,
   30–52%") was never retracted for the v1 set. Migration requires carrying the district
   art (gs_build, ls_build, qm_build) in the same window.
3. **Stair art blocks its own stair.** walk_bodygate (0.075 m stride, 12.60% of all legal
   steps blocked town-wide): top blockers are cx_rail 18,968, qm_stair_underworks 12,870,
   ls_treads 8,109, ls_rail 6,990, ls_frame 6,608, wf_stair_treads 7,371 — stair
   furniture, all of it. r29's generator rule ("a rail may not stand in a body window of
   its own edge") exists but only the migrated flights have been rebuilt under it.
4. **The engine is NOT the problem.** walk_engine_gate del-cine: file 3,934 cells =
   engine 3,934 cells, 0 lost, BVH FAIL 0 — GREEN. Every defect below is in the
   geometry/records themselves or in guidance, not in walkStep.

## §2 Top defects by player cost

| # | place (scene del-cine) | class | cost (measured) | status |
|---|---|---|---|---|
| 1 | **quay-west wedge pocket + "Lockhead exit loop"** [58.1, 14.24, −12.2] | geometry AND guidance | 137 stall steps / 8 runs (census); ~150 steps r30; 29 steps r23; NEW GAME run: 37+13+8 steps + 5 filings (PT-20260806-007..010 VERIFIED) | GEOMETRY FIXED 2026-08-06 (Bet 2 it.2, d9b5ff7): fork+branch deleted, market flight v2 w2.0 — pocket->plaza reached, `--comp` one component. Guidance half (spawn placement) still open. |
| 2 | **lockfive apron / moorage complex** [70–80, 1–5, −29..−26] | geometry (residue) + guidance | 112 steps / 8 runs + 43 steps (supper) + 46/120 steps (west store, since FIXED r20) + pocket (FIXED r29) | partly fixed; residue §3.2 |
| 3 | **cottage plank ramp to Lock Five** [89.5–91.8, 8–10, −19..−21.5] | geometry (sub-body width) | 42 steps / 7 runs + NEW GAME run's last 4 steps churning; PT-20260806-002 (P1) / -003 (P0) VERIFIED by SIM.move stall | FIXED 2026-08-06 (Bet 2 it.5): the "taper" was the weave bridge's rails + parapet across the ramp foot (`--who` railA2 35 cells + cx_rail 8), not the ribbon — bridge rails now post-pass-clipped against other ways' floors, junction-inset; ramp drives 4/4 BOTH ways. SAME iteration found and fixed the bridge itself SEVERED mid-span (t2c washing in the 1.1 m rail slot; span widened 1.3→1.8, crossing_lane_chop): `--pairs` weave<->cottage reached BOTH ways, was no-path. Residual: greedy NE doorstep line wedges at [90.36,7.76,−22.18] (ramp chaikin bend self-roof, 13 cells) — fair line drives clean. |
| 4 | **shelf shop row pinches** [32–36.5, 19, −8.5..−6] | geometry (narrow pinch) | 34 steps / 5 runs + 17 steps; drive W→E stalls at [34.64, 19.07, −8.31] | OPEN |
| 5 | **valley-gate__inn hairpin (gate→shelf descent)** [22.5, 19.8–21.6, −4] | geometry (v1 stair) | 58 steps / 7 runs at [23.5, 20.1, −6.4] + 57 steps / 6 runs on the gate tier above it | FIXED 2026-08-06 (Bet 2 it.1, 0abf9e8): THE ONE DESCENT — `--way` 7/7 both ways, one component 331 cells |
| 6 | **quay promenade wall at the loop-stairs foot** [53.8–55.6, 14.24, −13.4..−11.5] | geometry | part of #1's basin; both drives stall at [54.6, 14.2, −13.3], dist 1.65/4.99 | FIXED 2026-08-06 (Bet 2 it.2, d9b5ff7): the wall WAS the deleted branch's foot treads+rails; promenade drives clean |
| 7 | **quay-deck__pilot-cluster flight** [58–60.6, 9.8–13.9, −20.8..−17.3] | geometry (v1 stair) | 21 steps / 4 runs (weave cluster); down stalls [58.61, 13.67, −17.66], up stalls [59.34, 9.04, −20.83] | FIXED 2026-08-06 (Bet 2 it.6): THE SEARCHED FOOT — 588-candidate ring search (generator-exact geometry, 75k-tri art BVH) rejected the whole road band and won the SOUTH ring, wp2 [60.0,25.8,10.2]; pivot separation now scales with width (the w2.0 stack l1_t06-over-l2_t01 was the v1 disease back at a new width); lg_wv_rail chopped off the head (tools/pilot_head_chop.py). RECEIPTS: pilot<->weave reached BOTH ways + road drive 3/3 both ways (was no-path); flight 8/8 both ways; §9.4's y-11.6 killer pocket geometry REPLACED (no walk floors at 11.6 there). Also closes §9.5 item 1 and PT-20260806-027/028/031/032/034's geometry half. |
| 8 | **deep stairs ascent** [38.3, 2.3, −25.1] up | geometry (one-way, known) | 28 steps / 2 runs; eff 9% in shot; r21 left uphill 6/40 deliberately (descent-only + cut) | OPEN by design — redesign should decide |
| 9 | **lock-five↔north-landing lane blocked by retired stair art** [88–93, −0.2..1, −28..−26] | geometry (orphaned art) | 27 steps / 4 runs at [87.1, 0.0, −26.9]; westbound drive stalls [90.38, −0.14, −27.57] | FIXED 2026-08-06 (Bet 2 it.4, tools/lockfive_lane_chop.py): 57 loose parts of lg_ks_* out of the lane corridor, snapshots LKC_SRC_*, digest-asserted — `--way` 4/4 legs BOTH ways, no stalls |
| 10 | **lockhead "wooden bridge" percepts** [64.4, 14.1, −13.8] | guidance/percept only | 27 steps / 5 runs unprojection; PT-20260806-005/006/011 all REFUTED — SIM.move walks it clean | OPEN (harness/percept, not world) |

Below the fold: interiors (cookhouse-int 20 steps at [0.2, 0, −2.0] — table pocket, PT-20260805-027/028 VERIFIED; inn-int 15 steps — hearth pocket measured r30, deferred), fishdock's east 0.4 m visible-not-walk curtain (r24, REFUTED as defect but still eats 17 steps/2 runs of aiming), boatyard/slipway west waterfront (off-spine; its fill is a separate 584-cell component and both my drives stalled crossing the seam-gate area [36.6, 2.2, −25.0] and [26.1, 2.6, −25.0] — LEAD, waypoints not yet proven fair).

## §3 Hot spots in detail

### 3.1 The quay-west basin (defect #1 + #6) — the single most expensive place in the town
The lockhead-return spawn [59.19, 14.0, −13.03] (scenegraph edge
`…market-stalls__lockhead:0.126:lockhead>quay-west`) sits one metre from a **sub-metre
wedge pocket at [58.1, 14.24, −12.2]**: `--who` over x 56.5–60.5, z −13.8..−11 names
**ls_rail (40 cells)** west and **walk_e_shelf-homes__market-stalls l2_t01/landing001
treads (19 cells)** north/east. Triage SIM.move from the run's own positions
[58.16, 14.24, −12.16] and [58.15, 14.24, −12.39] **gains nothing for 41 ticks** — yet my
drive from [58.15, 14.24, −12.3], 30 cm away, walks 3/3 legs clean to the seam and back.
The pocket is smaller than a body stride. The loop mechanic: spawn → wander 1 m → wedge →
the wayfinder still points at the cut → re-take exit → repeat (PT-20260806-007..010, all
VERIFIED). Two metres west, the **loop-landing__quay-deck stair foot lies across the quay
promenade**: `--who` at [53–55.6, 14.24, −13.1..−11.5] names the stair's own tread meshes
`walk_e_loop-landing__quay-deck_l0_t05/t06` + ls_frame; drives from BOTH sides stall at
[54.6, 14.2, −13.3]. PT-20260805-004 (landing lip, 0.63 m headroom under l1_t04, refuted-
fix twice) is this same complex one tread up and is still OPEN. **Redesign note: this is
one basin, not four tickets — the loop-stairs/market-stalls interchange plus the spawn
placement. Both flights involved are un-migrated v1.**

### 3.2 The moorage / lockfive apron (defect #2) — mostly paid, residue is real
FIXED and receipted: west store one-way pit (r20 moorage_westlink, `--comp` 10→643),
cx_rail pocket + switchback migration (r29, down 12/12 first ever). Residue this lane
measured: (a) **the ascent is a one-thread needle** — r29's own receipt says UP passes
"with one west-line thread past t04's lip"; my hairpin drive stalled up at
[73.06, 3.37, −27.34]; fresh PT-20260806-001 (player unable to get up to Maren) was
REFUTED by the probe (the thread exists, 143 cells) — so it is now a **findability/width
problem, not connectivity**: a first-time player cannot find a 0.9 m thread. (b) the
narrowness census puts the whole switchback in the worst band (l2 corridor 0.25 m min).
(c) **moorage__tenant-shack headroom** under the flight (1.05 m vs BODY_H 1.30 over open
water, x 72.2–74.7) is a standing build item (r12/r20, OPEN).

### 3.3 The cottage plank ramp (defect #3) — the plank tapers below the body
`lockhead__keepers-cottage` ships as 19 micro-legs (stair census, del-cine GLB): widths
shrink monotonically **1.26 m (l3) → 0.61 (l12) → 0.41 (l15) → 0.16 (l18)** while the
run stays 1.6 m — the last third of the ramp is narrower than the 0.6 m body. Triage
receipt: SIM.move from [90.22, 8.68, −21.69] toward [91.43, 8.27, −21.24] **stalls 1.29 m
short, 41 ticks no gain** (PT-20260806-002/003 VERIFIED; the P0). walk_bodygate names
lf_joists ([90.3, 7.81, −21.6], 46 steps) and lf_planking ([89.9, 10.01, −19.0], 26). The
NEW GAME run's final stretch (steps 497–500) is THIS: goto legs closing 2.2–2.6 m of
2.9–4.0 m intended with noGain=true, body oscillating [90.2, 9.3, −20.4]↔[92.5, 7.9,
−21.5] — each leg closes the wide top of the ramp and loses the narrow bottom.
**Characterization for the coordinator: terrain, not deadband, not aim** — r30's deadband
fixes are in (median close 0.79 across the run), and the body reaches r28's aim-hold point
[91.27, 7.87, −22.13] (step 493) before churning. Also here: the **cottage pit** x 88.6,
z −20.0..−21.5 (no walk floor, a metre with no collide floor — r28, routed around, never
filled) and PT-20260805-045/046's history.

### 3.4 The gate→shelf descent (defect #5) — the user's named target, now measured
`--way` down [15, 24, −5] → [30, 19, −8] via the valley-gate__inn switchback **stalls at
[22.51, 21.61, −3.92]** (l1/l2 hairpin); up stalls at [22.53, 19.77, −4.09], 1.02 m short
of the pivot. Both directions, v1 pivot-stack signature (r21's class). The flight is also
the steepest thing in town: l2 gradient **0.85** (rise 1.19 / run 1.40), l1 0.66. The
town-wide `--comp` fill (12 seeds) leaves the gate tier a **546-cell component that never
joins the 2,275-cell shelf/quay component**. Runs corroborate: 58 stall steps at
[23.5, 20.1, −6.4] + 57 on the gate tier, and gate-tier unprojection (32 legs) says the
players also cannot AIM down it. Ruling context: "the gate->shelf descent (currently TWO
confusing ways down) collapses to ONE simple, wide, legible route."

### 3.5 quay-deck__pilot-cluster (defect #7) — v1, failing both ways, plus a 0.92 m stub
Down stalls at [58.61, 13.67, −17.66] (2.16 m short of the l1 flight); up stalls at
[59.34, 9.04, −20.83]. qm_stair_underworks is bodygate's #2 blocker town-wide (12,870
steps). The flight carries a 0.92 m-wide leg (l3, grad 0.53) — under the 1.4 m standard.
This is the shops→weave/moorage connector, i.e. the shop-visiting player's route down.

### 3.6 lock-five↔north-landing lane (defect #9) — the retired stair's body remains
r22 retired keepers-cottage__lock-five's WALK RECORDS; its art did not leave: `--who` over
x 88–93, z −28.5..−26 names **lg_ks_treads (33) / lg_ks_rail (18) / lg_ks_frame (4)** in
the lane band; westbound drive lock-five ← north-landing stalls at [90.38, −0.14, −27.57].
This is the ch2.dock→landing walk. Candidate one-commit fix for THIS lane's exception
rule, but it is art deletion in a dressed district — flagging to the redesign lane instead.

## §4 Stair-edge census (shipped del-cine GLB; 169 edge groups, full table via the script)
Flights with any leg over gradient 0.5 — all five need a redesign position:
valley-gate__inn (0.44/0.66/**0.85**, v1) · deep-stairs (0.64–0.76 ×4, v2, descent-only) ·
loop-landing__quay-deck l0 (0.69, v1) · quay-deck__pilot-cluster (0.46–0.66 + 0.92 m-wide
stub, v1) · weave-huts__moorage (0.53–0.63, v2) · shelf-homes__market-stalls (0.35–0.56,
v1). lockhead__keepers-cottage is 19 legs of gradient 0.11–0.39 whose widths taper to
0.16 m (§3.3). Landings are uniformly 2.0 m pads; every flight is 1.4 m wide.
Script: scratchpad stair_census.mjs (PCA width on each edge's own verts; short curved
legs' widths are approximate — confirm with `--who` before citing a single number).

## §5 Component census (`_court_probe --comp`, 12 seeds, box 0..109 × −34..−1, 0.4 m)
gate tier **546** · shelf/quay/market/lockhead/cottage-stair **2,275** · moorage/lockfive/
north-landing **1,893** · fishdock **1,446** · boatyard **584** — five worlds. Tier
components joined only by the stairs above, so every stair defect is a component split.
(Caveat carried from r24: the fill's membership is not symmetric on tiered decks; the
drives and named blockers above are the evidence, the fill is the map of where to look.)

## §6 Guidance-only items (no geometry change needed)
- **lockhead "bridge unwalkable" percepts** (PT-20260806-005/006/011, REFUTED): the walk
  is clean; the agent/percept cannot see ground on the bridge pixels. Harness/percept lane.
- **PT-20260805-067 / PT-20260806-001** (REFUTED): drives succeed; the failure is finding
  the way (the moorage up-thread, the loop-stairs exit line). Wayhint/legibility.
- Odessa re-talk gives no state cue (r23, OPEN, content lane).
- The quay-west spawn placement (§3.1) is HALF guidance: moving the lockhead-return spawn
  out of the wedge basin is a scenegraph edit, no geometry.
- Standing FIXLOG lessons the redesign inherits: name the first hop's landmark, never
  compass words (r14/16/18); the arrow is a promise about the ground (r28).

## §7 Do not re-file (measured and refuted)
fishdock east curtain is 2 m off the real lane (r24) · weave-tier "unfenced 12 m hole"
(r25 vs r26) · r26's trapdoor coordinates (r27: 0.14 m past the deck edge) · festival-dais
class in Emberbrook (r18). The three-instruments-three-answers rule stands: **only keys
are the oracle; the fill locates, the drive convicts, `--who` names.**

## §8 Instruments run + outputs (all on the shipped bundle @ ae3dfb1, port 3111)
walk_engine_gate GREEN (0 lost of 3,934) · walk_bodygate 12.60% blocked, census by object ·
_court_probe --comp/--way/--who transcripts, corridor-width + stair censuses: scratchpad of
this session (`comp_town.txt`, `way_*.txt`, `who_*.txt`, `narrow_census.mjs`,
`stair_census.mjs`) — re-runnable in minutes; the numbers above are self-contained.
Queue: 46 verified · 8 unverified · 48 refuted after this lane's triage of
PT-20260805-067 + PT-20260806-001..011 (docs/qa/playtest-queue.md).

## §9 Addendum — 2026-08-06 post-reset (fresh receipts; every run pinned to bundle del-cine c47bd403 / townwalk 50a72165, the SAME bytes §1–§8 measured. Bet 2's iteration-1 commit 0abf9e8 had NOT re-exported the shipped bundle when these ran.)

### 9.1 dock→lockfive/landing drag, characterized (closes the coordinator's ask)
Two runs, same stretch, same bundle:
- run-20260806-001811 (died at cap): steps 497–500 oscillate [90.2,9.3,−20.4]↔[92.5,7.9,−21.5]
  on the cottage plank ramp, closing 2.2–2.6 m of 2.9–4.0 m intended, noGain — churn at the
  ramp's sub-body taper (§3.3).
- run-20260806-011853 (the 28/28 GREEN run): paid **8 steps of the same oscillation**
  (476–483, incl. noGain at 479/481), then ESCAPED — not down the ramp bottom but via
  [91.21,8.3,−21.61] onto the **crossing lane at y7.5** (weave-huts__keepers-cottage), down
  the migrated moorage switchback in one step (487→488, y7.87→1.25), landing at 492.
**Verdict: terrain, not deadband, not aim** (median close healthy, r28 aim-hold reached in
both runs). The ramp's last third (width 0.41→0.16 m, §3.3) is not a route; the crossing
lane is the only real one. The redesign either widens the ramp bottom or makes the crossing
THE route and stops routing/marking the ramp bottom as an exit.
Even the green run concentrates its Dellhollow cost in the four basins: of its 296 del-cine
steps — lockhead 79, quay-west 57, lockfive 56, loop-stairs 33 (65%).

### 9.2 The moorage ascent is no longer "findability" — the t04 lip is VERIFIED three ways
PT-20260806-015/016/017 (triaged this window): SIM.move from [73.4–75.0, 4.1–4.5, −26.3..−26.6]
toward the l0/l1 hairpin [74.78, 6.27, −25.12] stalls 0.78–0.91 m short, 41 ticks no gain,
three distinct starts. §3.2(a) upgrades from "one-thread findability" to: **the ascent's
mid-flight is a drivable defect** — the cottage-transition marker above it draws players
into it (three filings in one successful run). Geometry, with a guidance rider (the marker
aims across the lip).

### 9.3 Fresh targeted leg 1 — the gate tier eats an entire run (the Bet 2 "before" receipt)
run-20260806-032313 (--from=ch2.arrive --stop-beat=ch2.jam, 120 steps, $0.51): the body
spent ALL 120 steps in the gate shot, pinned at **[17.8, 24.07, −5.5]** from step ~10 —
46 arrived walk legs of 157, dozens of "closed 0 m of ~4.7 m" toward the routed Lockhead
marker, ch2.jam never fired. Consistent with §3.4's both-ways hairpin stall, the 546-cell
gate component, and bodygate's gate_barrier (444 blocked steps at [15.4, 24.07, −3.8]) +
shelf_stair_underworks (137 at [20.0, 22.9, −4.1]). **A cold ch2.arrive on this bundle
cannot reach the town in 120 steps.** This is the measured "before" for Bet 2's ONE
DESCENT; re-run the same leg on the re-exported bundle for the after. 8 leads filed
(PT-20260806-018..025), triage pending this window.

### 9.4 Fresh legs 2–4 (all on bundle del-cine c47bd403; Bet 2 iterations incl. fe5b051
"THE COTTAGE CROSSING" landed in source AFTER these ran and had not re-exported the bundle —
re-attribute nothing here to the new geometry until the after-runs)
- **Leg 2, run-20260806-034459** (--from=ch2.jam → ch2.maren, 120 steps, $0.38): ch2.maren
  NEVER fired. 116/120 steps pinned on the pilot-cluster mid-tier at [60.4–61.8, 11.6,
  −18..−19.7] — the quay-deck__pilot-cluster landing.001 pocket. Median closed/leg 0.25.
- **Leg 4, run-20260806-040032** (same start, WANDER/shops brief, 120 steps, $0.40): never
  reached a shop — **fell into the SAME pocket within 12 steps** and spent 116/120 there,
  median closed 0.16. Two goals, one trap: everything leaving the lockhead south-west lands
  on the y11.6 deck and cannot leave it (triaged VERIFIED: PT-20260806-027/028/031/032/034;
  short-hop claims refuted). With §3.5's both-ways flight stalls this makes
  **quay-deck__pilot-cluster the single most reliably fatal element in the town**: 2/2
  fresh runs, 100% of steps after entry.
- **Leg 3, run-20260806-035832** (--from=ch2.dock → ch2.landing, 11 steps, $0.01, ZERO
  reports): CLEAN — router took the crossing lane at y7.5, moorage switchback DOWN in one
  step, landing fired. Sharpens §9.1: dock→landing has a working route; the drag in full
  runs is the Lock Five exit arrow luring players down the ramp taper instead of it.
- Gate addendum from leg 1's triage (PT-20260806-018..025, ALL VERIFIED): the pocket is on
  the FLAT toll yard — --who names **t2c_G3_awning_tollyard_2 + gate_arch001 +
  gate_parapet_1** walling [13–18, 24, −7..−4], and the routed Lockhead marker projects
  WEST at [13.12, 24, −6.35] (into the walled yard) while the descent is EAST at x 19–23.
  Geometry (dressing across the yard) AND guidance (marker pulls the wrong way).

### 9.5 Final cost ranking (fresh legs folded in) — what the redesign should spend on
1. quay-deck__pilot-cluster flight + landing pocket (§3.5, §9.4) — 232/240 fresh-leg steps
2. the gate toll yard + gate→shelf descent (§3.4, §9.3/9.4) — 120/120 fresh-leg steps
   (Bet 2 iteration 1 targets the descent; the TOLL-YARD POCKET is a separate item)
3. quay-west basin: wedge pocket + loop-stairs foot + spawn placement (§3.1)
4. cottage plank ramp taper + Lock Five arrow at its foot (§3.3, §9.1) — Bet 2 iteration 5
5. moorage ascent t04 lip (§9.2)
6. lock-five↔north-landing lg_ks art (§3.6)
7. shelf shop row pinches (§2#4)
8. deep-stairs ascent policy (§2#8)
9. lockhead bridge percept (harness lane, §6)
10. interiors' furniture pockets (cookhouse/inn)
Runs this window: run-20260806-032313 ($0.51) · -034459 ($0.38) · -035832 ($0.01) ·
-040032 ($0.40) — total ~$1.30 of the ~$2-3 authorized; the fifth/sixth runs are best
spent as AFTER-receipts on the re-exported Bet 2 bundle, same legs, digests pinned.
