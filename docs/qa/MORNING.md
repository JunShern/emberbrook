# HANDOVER — 2026-08-08 06:45 (READ THIS SECTION FIRST; everything below is history)

An overnight window, ~17:00 → 06:45. Round 3 of the graphics loop CLOSED, the device-pixel-ratio
fix shipped, and the BATTLE PRESENTATION ARC opened and delivered its first wave. All work is
committed and pushed (branch `migration/3d-hybrid`).

## THE DEPLOY IS LIVE AND VERIFIED — and my diagnosis of it was WRONG, twice
Live: **build `2026-08-08T05:34:57Z`, static_verify 29/0 local AND against the URL**, with the
plate bytes compared on the wire (pondlane moved 957040 → 902084, so the ART shipped, not just
the stamp). Built from `d95f3e04`, so it carries EVERYTHING in this handover — dpr 2, the fields
and skies, and the whole battle wave. The only gameplay change after it is the RT-teardown leak
fix (`7545d2fd`), which a follow-up deploy is taking.
**WHAT I GOT WRONG, recorded because I put the wrong version in this file first:**
- I reported a "cold cache produced a 915 MB / 896-file tree" and inferred a build bug where
  `build-static.mjs`'s correctness depended on cache state. **BOTH FALSE.** `deploy-ghpages.sh`
  turns `dist` into its OWN throwaway git repo in place, so I was measuring `dist/.git`
  (503 files / 364 MB). Excluding it: 393 files / 545 MB — the normal shape. The build was never
  cold either (244 hit / 9 miss, the 9 being exactly the changed art). **The script's own
  pre-flight has the same trap** — it counts before its `rm -rf .git` and prints the inflated
  number on a rerun. MEASURE WHAT THE NUMBER INCLUDES BEFORE BUILDING A THEORY ON IT.
- What was actually true: the pushes kept dying. One died WITH ITS FOREGROUND TOOL CALL (a long
  push is bounded by the call, not the network — this belongs in the deploy tooling), and the
  link ran 70–143 KB/s with 21% retransmits, so a ~530 MB push takes 60–90 minutes. Also
  **`setsid` does not exist on macOS** and silently killed a launch; `(nohup … &)` is what works.
- The clean-worktree method was VINDICATED, not the villain: the file-list diff against a
  main-repo build differs by `js/battle_world.js` — another lane's uncommitted module, which a
  normal build would have published. Building from a worktree needs two things git does not
  carry: `node_modules` symlinked in, and `EB_BUILD_CACHE` pointed at the main repo's warm cache.

## WHAT SHIPPED (all verified, all pushed)
- **Both towns' water classes are closed.** Emberbrook went 0 CONVINCING / 6 FAILING → 0 FAILING.
  The cause was never lighting or shading: every water sheet was a 0.12 m-thick box floating
  0.17 m above its own bed, with a lit underside and a shadow cast on the bed it was meant to lie
  in. Seating them doubled the water's brightness with NO LIGHT TOUCHED. Dellhollow's deep-stairs
  "cyan plane" was its flat riverbed pinning the alpha ramp; its quay-west "deck sliver" was two
  market awnings, four of five of which had zero up-faces from a generator winding bug that
  Cycles' two-sided shading hid.
- **THE WEST WATERFRONT IS OPEN AGAIN.** It had regressed to a 92-cell one-way pit (reach_probe
  no-path both ways) because a searched stair landed on the corridor an earlier fix's planks were
  shaped to dodge. Fixed by giving the SEARCH the west-arm clearance oracle it never had; now one
  547-cell component, engine-receipted both ways. A builder was also found silently deleting the
  water-transparency bake — caught by A/B-ing a plate 25 m away that had lost its river.
- **dpr 2 (`?dpr=1` reverts).** The plates are authored at 2688x1536, EXACTLY twice the canvas —
  we were downsampling the art by half. Six hard-coded 1344x768 sites had to move together and
  five fail silently; measured cost is +9% on plate scenes, 60 fps holds everywhere.
- **BATTLE WAVE 1**: contact distance at the damage event 6.54 m → 1.32 m with turn wall-clock
  UNCHANGED, staging solved against the frame, the cast finally cheers/uses items/flees, weapons
  in hand, and `?arena=world` shipped INERT — fighting in the real valley is ONE context, ZERO
  new shaders and 31.8% FASTER than the diorama, but the painted plates are still more legible.

## WHAT NEEDS YOUR TASTE (nothing is blocked on it)
1. **Walk a battle.** `play3d.html` → fight. Then try `?arena=world` and tell me which world you
   want the game to fight in — that single answer orders the whole battle slate.
2. The battle slate's next bets are ranked and dispatchable in
   `docs/plans/battle-presentation-inventory.md`: a CAMERA LANGUAGE (gated on the backdrop
   question above), KO/victory as events (measured: nobody in the frame reacts to a kill), and
   monsters that look like one game (six creatures, four art styles).

## HONEST NOTES
- **A still frame cannot show a time freeze.** The harness lane reported "still no hit-stop" from
  a screenshot; the contact lane MEASURED hit-stop on a clock (90 ms, 150 on KO). The measurement
  stands and the screenshot claim is unsupported — do not file it as a defect without a clock.
- The audit's "four open post-battle tickets" were WRONG: one is verified fixed, three refuted.
  The world-arena risk argument was weaker than stated.
- `transition_test` is 162/6. Those six are NOT the battle (proven with the 3D stage never
  constructed) and NOT dpr — they are one resource leaked ONCE on a round trip through the
  real-time scene, in `play3d.html`. A lane is on it.
- Five worklist attributions were REFUTED by measurement before anything was built. That is the
  loop working, and it is why so little of tonight was spent on the thing each item named.

---

# HANDOVER — 2026-08-07 14:35 (history from here down)

The previous session ran ~44 h and closed cleanly. CURRENT STATE, all pushed (HEAD c4f05b6):

- **LIVE + VERIFIED 29/0**: https://junshern.github.io/emberbrook/ (build 2026-08-07T06:46)
  carries graphics rounds 1+2 and the pose-plate fix. Deploy lessons are IN THE TOOLS
  (deploy-ghpages.sh: pass the dir explicitly, script now queues the Pages build itself).
- **The calibrated judge**: tools/scene_redteam.mjs checklist mode carries [QUALITY]
  families (sky, frame-edge-world, water-read) validated at zero stage-2 refutals —
  built from the user's own five complaints (recall was 3/5 naive; the families cover
  the misses). Findings: docs/qa/redteam/run-20260806-1-findings.md (+ run-20260807-064138,
  the round-2 re-judge: FAILING -> WEAK, zero FAILING left on the seven plates).
- **Graphics rounds 1-2 BANKED** (boards: docs/qa/dellhollow-graphics/index.html):
  water-transparency regression found+restored, 5 legible shop doors, gorgewall
  de-quilt, pit lantern, ribbon paving. Blind after won every pair.

**THE NEXT WORK — round 3, measured and ready (dispatch as parallel lanes):**
1. EMBERBROOK WATER (the town-wide 0-CONVINCING/6-FAILING class): DIAGNOSIS DONE
   (DAYLOG 2026-08-07 09:45) — all four water_emb_* sheets have ZERO color layers;
   port Dellhollow's t2_water_shader depth-alpha recipe as an emb carrier, rebake the
   water-visible emb plates (HEAVY master, 1-wide serial).
2. deep-stairs water "flat untextured cyan plane" (a sheet the round-1 restore missed).
3. quay-west deck sliver (ribbon paving edge-on — round 2's noted residual).
4. Boil close-read, waterline foam/shore band, boatyard black slabs, railings/market
   stands, crushed-black street shadows (lighting class: ADD a source, per doctrine).
5. Town skies (emb WEAK x2, pondlane) — a dedicated round; baked into plates, not the ow dome.
Also standing: the moorage tread lane-waypoint (bake-lane residual, DAYLOG 20:20 entry),
PT-009 prompt overlap (play3d-owned), the DPR/retina trade (slate), far-rings east
vantage (LOOP.md BET 12 R4).

Method unchanged: RED-TEAM FIX LOOP (measure before build), blind verdicts, the fast
no-bake loop for geometry, bakes serial, commit --only + push + verify per batch.

---

# MORNING BRIEF — 2026-08-06

Written ~06:50 while the Dellhollow after-receipts run. Supersedes the 2026-08-02 brief
(in git history). Everything below is committed and pushed; HEAD lineage through `0d3b078`.

---

## 🏁 THE STANDING BAR IS MET — the game completes from scratch, by an LLM player

**`run-20260806-011853`: NEW GAME → the Chapter Two end card. All 28 beats on their own
triggers, no `Story.force`, 492 steps, $1.18.** The artifact lives at
`docs/qa/playtest/runs/run-20260806-011853/` (log + golden set). The chain that got there,
each wall measured before it was fixed: PT-049 (moorage switchback → STAIRS_V2 migration +
a new rail rule) → PT-050 (weave shot recomposed per seam canon) → PT-055 (the gate-court
flank as ONE line of map) → round 30 (the hold/arrive deadband, the door the bargeman ate,
the exit-walk false positive) → take 1 capped at 500 two beats short (walking, not stuck)
→ take 2 finished with 158 steps to spare. Mechanical spine: playthrough_test 86/0.

## 🎨 THE OVERWORLD SWEEP (your graphics steer, then your five complaints — all shipped)

- **Camera**: `OWPITCH/OWTILT 0.70/0.16` — the reference-matching composition (body at
  frame-Y 0.734, more ground, more visible area). Plus a **camera occlusion clamp**
  (your gorge complaint): the boom snaps in front of a blocking cliff and eases back out;
  receipt: 10/12 yaws clamp at the cliff-hugging station, zero at open ones. `?camclip=0`.
- **THE SKY IS REAL** (your "MS Paint" call): sun disk + glow on the true key direction,
  golden-hour hue ramp, fbm clouds, mist-seated ridges. Blind judge: the sun-facing vista
  ranked **behind only your two FFIX references**. Your giant blue dot = the camera's far
  plane clipping the sky dome (fixed with one measured number, far 400→560, plus a 216/216
  360-degree sweep gate). `?sky2=0` restores the old sky.
- **Vegetation**: 5,500-card bush family over dark hulls on all near-road clumps; blind
  after won 4/5 pairs. **The walked corridor is un-buried**: canopy trimming measured
  inert, so the road BENT — station-90 vegetation 43.8%→7.0%, visible ground 311→763 m².
- **The road**: was literally a causeway floating in its own trench (median 0.30 u, its
  own shadow beneath it) — now conformed (0.035 u), shadow-cast off, fringe on the lip,
  edge ragged + tufts straddling the seam per your "too distinct" note.
- **Grass pop while walking**: the scatter RNG was seeded from YOUR position — every few
  steps re-rolled the world. Now seeded from where the grass grows: 93% of instances
  survive movement; visible pop 0.71%→0.10% of pixels.
- **THE WORLD MOVES** (`public/js/ambient.js`): chimney smoke over the plates (depth-
  occluded), river glints, dusk fireflies that obey the hush, drifting leaves, cloud
  drift — one shared wind, 60 fps held, `?ambient=0`. Judge: fireflies "the most
  convincing ambient effect in the whole pack."
- Gallery rounds 21–24 + the sky/vegetation boards carry every verdict verbatim:
  `docs/qa/gauntlet/`, `docs/qa/ow-camera/`, `docs/qa/ow-refs/`.
- **Overworld now RESTS per your steer.** Residuals honestly named on the slate: bushes
  still read opaque at close range, aerial road width, DPR pixelation (needs a measured
  setPixelRatio trade), far-ring "paper terraces".

## 🏘 THE DELLHOLLOW PHASE (your 01:10 steer — opened and 7 iterations deep)

- **The inventory first**: `docs/plans/dellhollow-pain-inventory.md` — from all playtest
  history + 4 fresh legs + instrument sweeps. Headline numbers: **55% of walk cells sit in
  corridors under 1.25 m; town walk efficiency 52% (37% of steps are stalls, vs ZERO in
  Emberbrook); the engine is innocent** (walk_engine_gate green — it's the layout).
- **Bet 2, iterations 1–7** (board: `docs/qa/dellhollow-circulation/index.html`):
  1. **THE ONE DESCENT** — gate→shelf collapsed to a single straight 2.2 u flight (your
     named ask; the confusing second way down is gone).
  2. **THE QUAY INTERCHANGE** — the loop-landing fork deleted, market flight w2.0.
  3. **THE HEAD APRON** — a generator rule fixing a 0.6 m no-floor annulus; plaza↔pilot
     was unreachable BOTH ways and now walks both ways.
  4. Lock-five lane chop — dock→landing drives 4/4 both ways.
  5. **THE COTTAGE CROSSING** (P0) — the killer was the bridge's own rails across the
     ramp foot + a severed span; new generator rule: rails clip against the body window.
  6. **THE SEARCHED FOOT** — the pilot hairpin relocated by a 588-candidate search
     (authored candidates all measurably clipped something); pilot↔weave joins both ways.
  7. Gate toll-yard verdict + **deep-stairs DECIDED: simplify, not retire** (spec'd,
     execution next window).
- **In flight right now**: three after-receipt playtest legs on the new geometry.
- **Owed to a closing lane** (deliberately deferred per the fast-loop law): cine_solve +
  scenegraph + del-cine plate rebake ONCE on ratified geometry; t04 lip chop; shop-row
  widen-vs-demote call; deep-stairs execution; washing re-hang (pops lane debt).

## ⚠️ Honest notes

- del-cine's PLATES ARE STALE against the new geometry until the closing bake — expected,
  phase law, not a bug. transition_test carries 7 pre-existing del-* baseline fails
  (attributed thrice); slice_test carries 1 scenegraph-stale line (phase law).
- Two session-limit kills overnight (~03:25, reset 04:10): the Bet 2 lane's tree was HELD
  not reverted, and the restart inherited it at zero cost — that hold decision is the
  night's best process call. Monitors armed before a limit window don't survive it:
  re-arm waits on every resume (now standing practice).
- Gemini credits: topped up by you at ~00:50; overnight playtest spend ≈ $6.

## 💰 What's waiting on YOU (nothing blocks work; these are taste calls)

1. **Walk the overworld** — everything above in one walk: `play3d.html?scene=ow-valley&rt=1`.
2. **Walk Dellhollow's realtime tier** (`?scene=townwalk&rt=1`) — the new descent and
   quay/pilot circulation are live there; the CINEMATIC town still shows old plates until
   the closing bake (say the word and I run it — it is the one Blender-heavy step left).
3. The DPR/retina sharpness trade (4× fragment cost) — measured proposal on the slate.

---

## 07:25 ADDENDUM — the after-receipts are in, all three GREEN

The redesigned circulation, receipted by a player-shaped agent on the new bundle:
- gate → ch2.jam: **67 steps, 0 reports** (this leg killed a fresh run 120/120 on the
  old geometry).
- jam → ch2.maren through the pilot cluster: **completed** (killed 2/2 runs before);
  6 leads filed en route, instrument triage: 5 verified / 1 refuted — smaller pocket
  class, queued for the next iteration window, none route-blocking (the leg finished).
- dock → ch2.landing: **13 steps, 0 reports.**
Queue after triage: 69 verified / 8 unverified / 56 refuted. The closing bake stays
held for your call (walk the realtime tier first: ?scene=townwalk&rt=1).

## 10:55 ADDENDUM — window 3 complete; the closing bake is now the right next move

Iterations 8-10 landed (49260f0, e296cb2): moorage switchback 2/4→**11/11 both ways**,
deep stairs 3/10→**13/13 both ways** (both via candidate searches), the rail-guard
sampling defect killed at the generator (0.35 m grid → 0.10 m body lattice — posts had
stood inside flights with the guard green), shop row measured-and-cleared, five pockets
closed as stale-bundle artifacts. Every worklist item is done; all gates green.

THE FLAG THAT CHANGES THE PLAN: playtest filings now measure the OLD town — del-cine's
plates and bundle predate all ten iterations. The closing bake (cine_solve + scenegraph
+ plates + del-cine re-export) is blocking playtest correctness, not just visuals.
**Recommendation: I fire the closing bake lane at ~12:00 unless you say otherwise** —
that leaves you the morning to walk the realtime tier (?scene=townwalk&rt=1) first.
Residuals for after: west-waterfront knot (bank recut), stale walk rows (district
carries), reach_probe's lattice-vs-stair-foot instrument note.

## 20:20 ADDENDUM — the closing bake is DONE; Bet 2 is BANKED

The ~12:00 lane ran (an account-credits outage cost 15:00-19:40; nothing was lost —
the receipt and the LLM leg ran after restore). Commits 5e762f2 / 0c5f6d3 / 38ce143
+ records, all pushed. What it means for you:

- **The playtest-correctness flag is CLEARED**: del-cine's 15 plates and bundle are
  re-baked/re-exported from the ratified Bet 2 town. Filings measure the real town again.
- **All 7 stale walk-row carries taken** (the 2026-08-02 cookhouse doorstep edit finally
  landed: door arrival 18.7%/0% → 53.8%/100%, gullgirl's clearance red gone).
- **Gates**: slice 776/0 · findability 69/0 · walk_engine_gate GREEN · playthrough 85/1
  (the known stair-foot fill caveat; climb 21/21 in-engine) · transition 162/6 (one
  pinned post-battle allocation signature, play3d-domain, flagged to main) · cine/seam
  reds all one instrument family (a file walker cannot test a searched build; engine
  receipts recorded in DAYLOG).
- **The proof**: LLM leg run-20260806-184322 walked gate → waterline END TO END on the
  new plates, zero blockers en route — the descent that killed 2/2 runs before Bet 2.
  It stalled 9 m short of Maren on the WEST boardwalk arm: the switchback l2 tread's own
  box owns the lane at [73.4-73.8,-28.3] (the "same two metres of air" class at the new
  width). Lane-waypoint fix next window; the east approach and the beat trigger are fine.
- **Bet 2 → BANKED** on the slate, that one residual carried by name.

Worth your eyes when you have five minutes: the re-baked shelf-west / deep-stairs /
quay-west / weave plates (docs/qa/dellhollow-circulation/ closing section links the
before/afters), and the deploy is NOT yet refreshed with the new plates — that is the
next lane's first move if you want the live demo current.
