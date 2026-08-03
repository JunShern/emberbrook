# TOMORROW — the plan, and the decisions I have been delegated (2026-08-03, ~01:45)

The user is asleep and at work tomorrow, less available. They asked for sizeable tranches to
keep things spinning. **They have delegated the art calls below to me** — do not park work
waiting for them.

## THE ONE THING THAT MATTERS MOST

Tonight the user played the deployed game and found **six real defects in one sitting**, and
**five green gate suites had caught none of them**. Every gate we owned tested MACHINERY.
None tested being a player. Two gates built tonight moved toward perception —
`findability_test` and §W reachability — and **both found real bugs within minutes of
existing**. That is the pattern worth continuing, and it is why the LLM playtester is the
highest-value lane on the board.

## STANDING DECISIONS (user delegated these to me; do not re-ask)

- **Old Gate structure candidates** — user: *"whenever those land, I want you to go ahead and
  make the call yourself. No need to wait on me."* Judge them against the FFIX refs and the
  quality-over-volume principle, pick one, ship it, and show them the result afterwards.
- **The bunting post shadow** (Festival Square, a hard dark bar up pale plaster) — user:
  *"You decide."* **DECISION: FIX IT.** It sits on one of the brightest surfaces in the town's
  main square and reads as a defect rather than as any object's shadow. Nudge the one post,
  re-bake `square` only. QUEUED, not urgent — fold it into whichever lane next touches
  Emberbrook plates rather than opening a lane for it.
- **Character lighting / face legibility on dark plates** — SETTLED. User: *"this current
  lighting is good."* No further work. Do not revisit.
- **Forest / overworld landscape — DECIDED 2026-08-03 ~02:30: TAKE ALL THREE (L1+L2+L3).**
  The lane's own columns show they are ORTHOGONAL — each barely moves the others' metric —
  so this is not a pick-one. Combined, the sunlit gate meadow goes L p50 0.364 -> 0.511,
  level with ref 3's 0.469. **I looked at the frames before deciding** (`LA-gate.jpg` vs
  `L0-gate.jpg`): the before is a murky olive with no light in it; the after reads as a
  sunlit meadow, and L2's tufts do the real work of defining the road/grass and grass/sand
  seams. Gallery `docs/qa/ow-land/index.html`.
    * **L1 the hour** (+0 tris) — blue fill on the HEMISPHERE not the ambient, one cool
      bounce, fog 150 m -> 34 m. Key untouched (the user ratified the key).
    * **L2 ground-is-geometry** (+113,924 tris) — 6-tri tufts ONLY where the ground changes,
      flowers in patches of 6-14, never scattered. The placement rule IS the candidate.
    * **L3 the surface** (`COLOR_0` only) — the bundle's own vertex colours had grass at
      L 0.383 and rock at L 0.502, i.e. **the grass was darker than the rock**.
  **THE FINDING THAT REFRAMES IT:** three of our four daylight cameras were darker than the
  reference's NIGHT plate (ours L50 0.204 vs REF2-night 0.245), and `b-r` was negative in
  both quartiles of every frame — nothing in the corridor was cool. The refs are pictures of
  LIGHT, not of ground detail. That is the transferable property, and it is why "add more
  stuff" candidates kept missing.
  **LANDED 2026-08-03** in `4b7d259` (L1 -> play3d's ow rig) and `f94545d` (L2+L3 ->
  `tools/valley_land.py`, run from `valley_build.py`, baked into `ow-valley/scene.glb`).
  The shipped build reproduces the probe to **±0.002 on every imgstat column of all four
  cameras**, and the GLB's own COLOR_0 lands the probe's L3 numbers to ±0.001 on identical
  vertex counts. Shipped frames + the port-check table: `docs/qa/ow-land/index.html` §LANDED.
  The four cameras are now WRITTEN DOWN (`tools/ow_probe/land_cams.json`, pinned to road
  stations) — they never were, and the landing lane had to re-derive them.
  Cost paid: `scene.glb` 31.7 -> 45.5 MB (12.9 MB of it tufts; glTF cannot instance what
  the probe drew as one InstancedMesh). Not collision — 1,800 tuft vertices through
  `SIM.blocked()` in the running game, 62 blocked and NOT ONE by a `veg_land_*` mesh.
  **Left standing, deliberately:** the 273 clumps ship faceted (they are stand-ins and read
  as green gems at boom 12 — a modelling pass, not a knob); §4 the road shadow was already
  fixed by another lane before this one started.
  **Also proven and out of reach for now:** all four ow cameras contain ZERO sky pixels, so
  the sky dome, ridge rings and horizon fog built 2026-08-02 are invisible in play. Raising
  the pitch is a GAMEPLAY call, so it goes to the user, not to me. **NEW, same class
  (measured 2026-08-03):** at boom 40 the shipped follow camera is INSIDE the canopy for
  road stations ~78-172 — six of nine sampled stations photograph nothing but leaves, i.e.
  most of the walked corridor. Camera/collision question, not an art one.

## TRANCHES

**T1 — Land, integrate, redeploy.** Six lanes are running. The interesting part is the merge:
three of them write `story.json` (Lake adding beats, expressions adding mood tags, ch2.road
changing one coordinate). Then a full gate sweep, then a build with everything. The live site
is `https://junshern.github.io/emberbrook/` and is behind HEAD.

**T2 — Followers + the hush. ~~HELD~~ LANDED 2026-08-03** (`public/js/followers.js`,
`public/js/hush.js`; pointers in CLAUDE.md, findings in DAYLOG, QA at
`docs/qa/followers/index.html` and `docs/qa/hush/index.html`).
  - Followers: shipped as the BREADCRUMB TRAIL described below. Towns only, cannot block the
    player (never in `collide`), survives the scene swap. New `Npc.hide(id,on)` stands the
    posted cats down while Mochi follows.
  - Hush: shipped as "take the light" — the WebGL canvas is graded and the DOM cut-ins are
    not, which is what keeps the portraits warm. Brightness cut is plate-adaptive.
  - **STILL OPEN, and it needs a human's eye, not another lane's:** the grade desaturates a
    baked lamp pool but cannot extinguish it. Read `docs/qa/hush/index.html`; if the pale
    cold pools read as broken rather than as lightless, the only fix is a second Blender bake
    of every Emberbrook camera and that is a decision, not a task.

**T3 — Make redeploys cheap.** The build is ~28 min and re-encodes 219 unchanged plates every
run. A content-hash cache makes it seconds. Without it I will redeploy less often than I
should, which is the real cost. Do this BEFORE the next big art round.

**T4 — The LLM playtester** (running). The constraint that decides its worth: it must only do
what a human can do — real keyboard events, screenshots and on-screen text only, NO `SIM.tp`,
NO `Npc.talk()` by id. Reports go through triage; an unverified complaint is a lead, never a
ticket.

**T5 — The measured backlog.** All diagnosed, none needing a decision: `del.deckhand` 0%
visible from `shelf-east` (needs a 4.5 m move); `emb.miller` visible but standing in ground
luminance 0.004, i.e. pitch dark (visible ≠ readable); `del.gullgirl` clearance, `dialogue_test`
1398/2, pre-existing; the live clip binding never proven from the mixer (`scratchpad/clipprobe.js`
+ `arena_playtest --eval=`); Lake's and Finn's coats breaking under `Death_A` f32–f48 (a garment
class defect — two-panel open coats — fix is a skin reweight upstream).

## NEW BACKLOG ITEM (2026-08-03 ~02:10) — THE EXPRESSION CEILING IS ART, NOT WRITING

The expression pass raised `story.json` mood coverage 30% -> **90%** (Vesper 31 -> **91%**)
with **portrait tags only — no dialogue rewritten**, verified mechanically. But it hit a hard
ceiling it cannot pass:

  * **Five speakers have ZERO expression plates** — hobb (23 lines), sorrel (14), creel (17),
    the weaponsmith and the armorer. **44+ lines physically cannot emote**, whatever is written.
  * **The 2D and 3D runtimes draw DIFFERENT art**: 2D uses `expr-*.png` busts, 3D uses
    `cutin-*.png`, and the bust set is smaller. `vesper:wry`, `vesper:annoyed` and `lake:wry`
    are LIVE in 3D and REFUSED in 2D for want of art.

Both want a `tools/gen-cutin-art.mjs` pass. QUEUED — dispatch when a lane frees. Cheap
(image generation, no GPU) and it unlocks writing work already done.

**The find worth remembering from that lane:** `dialogue.js` has shipped a `chooserExpr` hook
since the chooser ruling and **nothing had ever set it**, so the protagonist sat on her neutral
plate for EVERY choice in the game. 0/17 -> 14/17. A shipped hook that nothing calls is
invisible to every gate.

## RISKS

- **Session limits killed lanes twice tonight.** Mitigation: every lane is now briefed to
  COMMIT EARLY with an honest "this part is unproven" message. Keep `RESUME-LANES.md` current.
- **The 20-minute status cron is session-only** and dies with the session. Re-create it.
- **Three lanes contending on `story.json`.** Each is committing tight and pushing immediately.

## MY OWN RECURRING FAILURE, recorded so the next session does not repeat it

Three times tonight I wrote a PROCESS CHECK THAT FAILED OPEN rather than loudly:
`pgrep -f blender` (the binary is capital-B, so it silently returned 0 mid-render and I told a
lane to re-spawn a live bake); `pgrep -ic` (invalid on macOS, printed a usage error I nearly
read as zero); and a "control test" for the deploy blocker that changed TWO variables at once
(server AND machine load) and led me to blame compression for a load-dependent timeout.
**The rule: an instrument that finds nothing must prove it could have found something — and
one that finds something must prove it found the right thing.**
