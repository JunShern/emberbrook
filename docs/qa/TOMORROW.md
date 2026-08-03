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
- **Forest** — all three candidates (F1/F2/F3) REJECTED. The bar is the FFIX reimagined refs
  in `public/assets/refs/reimagine_ff9*.jpg`. A new lane is running against them. The reframe:
  the refs contain NO forest, so this is not a tree-species problem — it is whole-landscape
  integration (ground geometry, blended transitions, multi-scale clustered planting, light).

## TRANCHES

**T1 — Land, integrate, redeploy.** Six lanes are running. The interesting part is the merge:
three of them write `story.json` (Lake adding beats, expressions adding mood tags, ch2.road
changing one coordinate). Then a full gate sweep, then a build with everything. The live site
is `https://junshern.github.io/emberbrook/` and is behind HEAD.

**T2 — Followers + the hush.** Both were HELD because they need `play3d.html`, which the Lake
lane owns for the body swap. Unblock them the moment Lake lands.
  - Followers: party members and Mochi trail the leader IN TOWNS, not the overworld. The cheap
    correct shape is a BREADCRUMB TRAIL — followers replay the leader's recent positions
    rather than pathfinding. No navigation code, cannot get stuck.
  - Hush: user approved *"take the light"* over grayscale. Emberbrook IS the Heartlight town;
    kill the warm sources and leave cold ambient, so the town goes blue and flat while the
    CUT-INS STAY WARM AND COLOURED — the people become the only warmth in frame. Tonight's
    AgX tone-curve work is the machinery.

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
