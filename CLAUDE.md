# Emberbrook — context index for Claude sessions

Two-player couch co-op JRPG in the FFIX pre-rendered-background style. This file is the
map of where truth lives. **Read the entries relevant to your task BEFORE designing or
building — sessions lose conversational context at compaction; the repo does not.**
Keep this file current: when you add a system, add its pointer here (one line, same
commit). Sessions may be rooted at ../rpg-3d (a legacy sandbox, NOT a git repo) — all
git runs here, on branch `migration/3d-hybrid`.

## Story & world canon (read before ANY town/character/dialogue design)
- **STORY.md** — the story bible: ten-chapter arc, flame/Heartlight metaphysics, full
  cast, reveal schedule, writers' rules (lore budget: ONE deep fictional system). Not
  final — expect revisions — but town/character design must accommodate it.
- public/js/chapter1.js — Chapter One "Emberwake", SHIPPED content; Emberbrook town
  must stage it. chapter2.js = Dellhollow, chapter3.js = Lanternstead.
- docs/chapter2-script.md — Lanternstead full script. VOICES.md — dialogue voice per
  character.
- **docs/exemplars.md** — the RATIFIED style set: 42 shipped Ch1–Ch2 lines that already
  obey VOICES.md, ~5 per main voice, each with one line on why. Read it before writing
  any dialogue; paste PART 2 as the few-shot block for any generated dialogue (match by
  example, never by describing the style in the abstract). Every quote in it is verbatim
  from the script — change a line there and you owe the same change in the chapter.
  Ch3 is deliberately absent: it is not the house style (user ruling 2026-08-02).
- **docs/plans/end-to-end-wiring.md** — the AUDIT of what stands between three
  scripted chapters and one continuous playthrough (2026-08-02). Headline: the chapters
  live in the LEGACY 2D runtime (join-legacy.html); play3d.html has no chapter runner,
  no story flag, no end card. Carries the save-state schema, the chapter-handoff
  contract, the story-flag proposal (`story.ch1.gate-open`), and the measured
  empty-Emberbrook finding. Read before any wiring work.
- **docs/qa/MORNING.md** — the 2026-08-02 overnight brief: what shipped, the seven
  decisions waiting on the user, the honest reds, and the night's measurement lessons.
  Read this before RESUME.md, which it supersedes.
- **docs/qa/TOMORROW.md** — the 2026-08-03 plan: five tranches, the art calls the user
  DELEGATED to me (Old Gate structure, the bunting post, forest-vs-the-FFIX-refs), what is
  settled and must not be re-asked, and the standing risks. Read it before picking up work.
- **docs/qa/RESUME-LANES.md** — 2026-08-02 ~21:30: the FIVE lanes paused when the account
  moved to a lower tier and work narrowed to deployment. One entry each: what landed, what
  remains, the traps already paid for, and the decisions waiting on the user. Read it before
  restarting any of them.
- **docs/qa/RESUME.md** — WORK PAUSED 2026-08-02: what every lane was mid-way
  through and how to pick it up. Read it before restarting any lane.
- Canon rulings log + nightly state: **docs/qa/DAYLOG.md** (append handover-quality
  notes there after major phases; agent transcripts expire).

## The townmap system (the authoring layer for every town — start here for town work)
- public/townmap/viewer.html?town=<name> — 3D/plan/elevation viewer of a town's map:
  landmarks, path edges, districts, **parcels (each derives a scene contract + sceneKey)**,
  draft camera frustums, live validation. Serve repo /public on a local port.
- public/townmap/<town>.map.json — the landmarks-first town layout: THE design authority
  a town model is built from (Dellhollow was built this way). Emberbrook's carries
  dated REDLINE notes from the user — honor them.
- **A CARRIER, never a rebuild, for a district already dressed:** tools/gate_rimchop.py (the
  rim) and tools/gate_roadchop.py (the ENTRY ROAD — rim + GX0 + SPINE, rebuilding
  gate_ground/gate_road/gate_parapet only) carry a one-list edit in tools/gate_lib.py onto
  the live master. gate_build.py MUST NOT be run against it (36 objects vs the master's 147).
  Each prints its own faithfulness gate; roadchop's `repro` mode proves the copy bit-exact
  BEFORE it builds. tools/walk_rederive.py `--drop` takes a deleted map entity's walk records
  out (an orphaned walk record goes on paving the town).
- <town>.cameras.json (authoring; grade in defaults.exposure) → tools/cine_solve.mjs →
  .cameras.solved.json → tools/scenegraph_derive.mjs → scenegraph.json →
  tools/cine_bake.py (Blender headless, ALWAYS `-b --python-exit-code 1`; bake ray-cast
  is the ONLY visibility oracle). PLATE BAKES RUN FULLY PARALLEL (user standing order
  2026-08-01): one Blender process per camera, wall-clock = slowest frame, never
  sequential; still rebake ONLY frustum-affected cameras on incremental changes.
  MEMORY CAP (2026-08-01, the laptop drowned in swap at 6 bakes + a Metal render):
  max 3 concurrent heavy Blender jobs town-wide across ALL lanes; check
  `sysctl vm.swapusage` before spawning — if swap used > 75%, run 2. Parallel
  within the budget, queued beyond it. Lanes coordinate via main.
  PARALLELISM CONDITION (2026-08-01, measured): the parallel order holds only while
  one plate fits comfortably (gray master ~1.6GB — parallel pays). Once a single
  plate saturates the GPU (dressed Emberbrook: 9.8GB, 27M tris via Metal on unified
  memory), go 1-wide serial: pondlane baked at both widths — 2-wide 411 s/plate vs
  1-wide 403 s/plate, ZERO throughput gain, plus 3/7 crashes at 2-wide. The tell is
  that exact test: if N-wide doesn't beat 1-wide on seconds-per-plate, it's
  contention — serialize. routes: <town>.routes.json (tools/routes_derive;
  `--check` must be CLEAN — nav-eval composites from routes, stale routes = wrong scores).

## Canon documents (each is a constitution earned from Dellhollow scars)
- docs/plans/seam-canon.md — scene-transition law: no-return arrivals, one-cut-per-
  passage, exits-in-frame, invisible-arrival diagnostic, perceptual gate.
- docs/plans/town-legibility.md — why cameras exist; player-readable paths.
- docs/plans/combat-ecosystem.md — battle architecture + Rulings log.
- docs/plans/battle-core-design.md, house-variety-design.md, water-transparency.md,
  cliff-completion.md, pops-of-color.md (AS BUILT sections) — the look pillars
  (golden-hour variant C, greens into autumn, varied houses, transparent flowing water).

## Runtime (public/play3d.html — COORDINATOR-OWNED, agents message main for edits)
- Scene system: pre-rendered bg.png + depth.png per camera, exact-pixel depth occlusion;
  WALKLOCK (walk network is law in /^(del-|townwalk)/ scenes); GHOST v2 stencil;
  UILOCK modal contract; in-place scene swaps via transitionTo() + 'eb-scene'
  CustomEvent module contract (see sgAnnounce comment; ?reload=1 = fallback).
- Modules (public/js/): game_state (GS), battle_rules (pure kernel — untouchable),
  battle_turnbased + battle_stage3d, encounters, ui_kit (FF-blue), shop, menu, npc,
  dialogue, **story_runtime**, followers, hush, route_overlay, music. Each self-arms at
  load AND re-arms on 'eb-scene'.
- **public/js/followers.js — THE PARTY WALKS BEHIND YOU, IN TOWNS** (2026-08-03, user
  playthrough item). A BREADCRUMB TRAIL, never a pathfinder: the leader's positions are
  sampled on the physics tick and each follower is drawn a fixed ARC LENGTH back along that
  polyline, so every place a follower stands is a place walkStep() already allowed — it
  cannot get stuck, cannot need a nav query, cannot disagree with WALKLOCK. If you find
  yourself wanting a path solver you have left the design. Towns only (WALKLOCK's own
  /^(del-|emb-|townwalk)/ — the overworld is excluded by the user's ruling). Nothing it
  builds enters collide/walkRef/allMeshes, which is what makes "a follower can never block
  the player" true by construction. Roster = GS.activeParty() minus the player's body
  (vesper/lake/maren ONLY); THE LEADER MUST HIMSELF BE ACTIVE, which is what keeps Ch1's
  Lake POV solo without naming a scene. Mochi is a cat, not a party member: `story.ch1.pact`,
  and the posted cats stand down via the new **Npc.hide(id,on)** (page-level intent, honoured
  by every later spawn). `?nofollow=1` disables. QA docs/qa/followers/index.html.
- **public/js/hush.js — THE HUSH: Emberbrook loses its heart** (2026-08-03). Flag-driven off
  `story.ch1.hush`, /^emb-/ only. The user chose "TAKE THE LIGHT" over a grayscale wash and
  the reason is canon — Emberbrook IS the Heartlight town. The town is a PRE-RENDERED PLATE,
  so no runtime light can put its baked lamps out: the frame is graded ON THE WEBGL CANVAS,
  and that placement IS the effect — a cut-in is a DOM <img> dialogue.js paints OVER that
  canvas, so THE PORTRAITS STAY WARM while the town goes blue and flat. Move the grade to a
  parent element and the effect breaks silently (Hush.debug().cutinsWarm asserts it). The
  same decision drives the shipped charLight() rig through `window.__hush` + **SIM.relight()**.
  The brightness cut is PLATE-ADAPTIVE off window.__charlight.plate.p70 (measured: gatefield
  at 0.115 vs the square's 0.21 — a flat cut made the Old Gate a dark frame, not a hush).
  `?hush=1|0` forces it. Capture with tools/hush_shot.mjs; QA docs/qa/hush/index.html.
- **public/game/lightrigs.json — THE PER-TOWN SUN, as runtime data** (2026-08-02). Tier 2 of
  charLight()'s rig lookup: a town whose `<town>.cameras.json` carries no `defaults.lightRig`
  (Dellhollow) gets its key direction/colour/energy from here. IT SHIPPED UNTRACKED ONCE —
  the code that fetches it was committed, the file was not, so every clone and every `dist`
  silently fell back to the page-default sun with only a console warning. A runtime data file
  that is not in git is a bug that only reproduces off the author's machine.
- Game data (public/game/): monsters, items, encounters, growth, shops, music.json
  (map rules first-match-wins), npcs.json, dialogue.json, **story.json**.
- **THE STORY LAYER (2026-08-02 — read docs/plans/end-to-end-wiring.md first).**
  window.Story reads public/game/story.json and drives the SHIPPED primitives: prose
  through Dialogue.play() on nodes it injects (Dialogue.inject — merge, never replace;
  dialogue.json wins a collision), conditions through Dialogue.check() verbatim,
  effects through GS.setFlags/addItem/addGold, cameras through SIM.shot(), the freeze
  through UILOCK. It rides phys() between sgTick and Encounters: a beat LOSES to a
  transition and WINS over an ambush. **A CHAPTER IS A SET OF FLAGS PLUS A SET OF
  BEATS, NEVER A MODE** — `at.chapter` is a label for the save screen and the music,
  never a switch, and NO BEAT MAY TELEPORT the player across a scene (the corridor
  between the towns is walked). Chapters 1-2 only; Ch2's end card is terminal.
- **Conditional edges.** An edge carrying `when` (or the `requires` shorthand) is
  evaluated by sgLive() with Dialogue.check on EVERY PHYSICS TICK — not at bind time,
  because the frame a story flag flips the edge AND its marker must appear with
  nothing reloaded. It FAILS CLOSED. scenegraph_derive emits a `sealed` exit that
  declares `sealedUntil` as exactly such a pair (no `sealedUntil` = still no edge).
  The Old Gate is the first: `story.ch1.gate-open`.
- **The save is v2** (`emberbrook-save`; the v1 key is read once and migrated). It
  carries `at` {chapter, scene, cam, pos, yaw} — THE resume authority — plus `beats`
  (the once:true ledger) and `meta`. GS.load() MIGRATES and never refuses a save it
  can parse; the old "reject any v!==1" silently erased playthroughs. GS.syncJoins()
  honours growth.json's `joinFlag` (lake-joined, maren-joined). Autosave fires on
  'eb-scene' ONLY once `beats` is non-empty — a dev scene-jump must not write a save,
  which is play3d's own module contract and what transition_test booby-traps.

## Shipping it (the live demo is a standing deliverable, refreshed every work window)
- **docs/DEPLOY.md** — tools/build-static.mjs (inclusion-not-exclusion; its own glTF-magic,
  scene-geometry and reference-integrity gates) → tools/deploy-ghpages.sh → LIVE at
  https://junshern.github.io/emberbrook/ . `--compress` is the deploy flag set.
- **The build has an ENCODE CACHE, on by default** (`.build-cache/`, gitignored):
  sha256(source) + sha256(EVERY parameter that changes the bytes — the encoder source
  itself, `--plate-max`, the Pillow/gltf-transform versions). Warm rebuild is SECONDS
  instead of 28 minutes, which is the point: a 28-minute deploy is a deploy you skip and
  the site drifts behind the branch. `--no-cache` bypasses; a bad entry is DEMOTED TO A
  MISS, never a build failure; depth.png is deliberately uncached because its encode
  carries the byte-exact round-trip proof. A cache keyed on the source alone would serve
  stale art the first time a quality setting moved — invisibly.
- **node tools/static_verify.mjs** drives a built tree off `python3 -m http.server`;
  **`--url https://…` drives THE DEPLOY**. Only the live run can see a file that
  committed code fetches and git does not carry (the lightrigs.json class).

## Test gauntlet (run what your change touches; all green before ship)
- node tools/slice_test.mjs · cine_test.mjs · seam_test.mjs · seam_walk.mjs ·
  economy_test.mjs · battle_sim / encounter_sim · transition_test.mjs --port=<port>
  (real Chrome; needs a server on the port serving /public)
- **tools/cdp.mjs — the shared Chrome/CDP plumbing for EVERY browser tool** (transition_test,
  playthrough_test, trigger_probe, arena_playtest, ow_shot). Never hardcode a CDP port or
  match a page by literal URL again: `freePort()` (OS-assigned — two tools both shipped 9351
  and the collision reported "chrome never exposed a page", a lie about the world caused by a
  neighbour), `GAME_PAGE` (matches BOTH /play.html and /play3d.html — server.js serves both),
  `findPage()` (a failure that DUMPS every CDP target it saw and separates "CDP unreachable"
  from "matcher wrong"), `killOrphans()`, `chromeArgs()`. The rule it encodes: AN INSTRUMENT
  THAT FINDS NOTHING MUST PROVE IT COULD HAVE FOUND SOMETHING.
- **A BROWSER TOOL THAT DOES NOT REAP ITS CHROME POISONS EVERY OTHER LANE** (2026-08-03,
  measured). `tools/mood_shots.mjs` shipped without going through cdp.mjs's cleanup and left
  SIX orphaned Chrome instances (`--user-data-dir=/tmp/moodshots-*`, all `ppid 1`) alive after
  its own lane had finished. They held **7.6 GB of swap**: the machine sat at 17.7/18.4 GB
  swap used with 675 MB free and ZERO Blender running, and every browser gate on it was slow
  and flaky for half an hour. Reaping them returned swap to 10.1 GB and free to 8.3 GB — so
  "the lanes are straining the machine" was FALSE; one leaked tool was.
  Tell an orphan from a live gate with
  `ps -Ao pid,ppid,etime,command | grep 'MacOS/Google Chrome '`: root Chrome with **ppid 1**
  is an orphan, one with a live parent pid is somebody's running gate and MUST NOT be killed.
  **NEVER pattern-kill Chrome by name — 25 of the processes on this machine are the USER'S OWN
  browser.** Match on the tool's own `--user-data-dir` prefix and prove the parent is gone
  (`pgrep -if <toolname>` empty) first. Any new browser tool goes through cdp.mjs, which
  already has `killOrphans()` and `sweepStaleProfiles()`.
- node tools/dialogue_style.mjs — THE STYLE GATE (no browser, no network): every spoken,
  `system` and `narrate` box in chapter1.js + chapter2.js + dialogue.json against
  VOICES.md's OWN numbers — two sentences a box, 25/30-word ceilings, one capped word,
  banned register, reading grade, exclamation density — reported BY SCENE and BY
  CHARACTER so a writer can act on it. Chapter3 is OUT of scope and does not gate
  (`--scope=all` measures it for information only). `--selftest` proves the sentence
  counter on hand-checked cases FIRST: '…' and '—' are not enders, abbreviations don't
  split, and a ≤2-word segment with no copula is a noise, not a sentence. Judgment calls
  (aphorism budget, aim band, internal ration) are WARNINGS on purpose — a heuristic that
  fails a build is a heuristic that gets written around.
- node tools/story_test.mjs — THE STORY GATE (no browser, no network): every beat's
  scene is a scenegraph node and every named cam a baked shot in that bundle's
  cine.json; every line resolves to a node and a speaker; no story node id shadows a
  dialogue.json one; THE FLAG LEDGER — a flag READ with no writer is a FAILURE (it
  caught the Old Gate's `ch1.gateOpen`, which nothing in the shipped game ever set), a
  flag WRITTEN with no reader is a WARNING (the next orphan joinFlag); the three
  §6 contract flags each written by exactly ONE beat; no beat moves the player.
- node tools/playthrough_test.mjs --port=3000 — §W REACHABILITY (default ON, `--no-walk`
  to skip, 16.7 s = 2.2% of the run): flood-fills between consecutive SAME-SCENE beat
  anchors INSIDE the page via tools/reach_probe.mjs — SIM.walkFloors/ground/blocked/edges,
  the engine's own rays and the player's own body box, never the file. It audits the
  TELEPORTS the story spine is built on: the harness drives SIM.tp() to each anchor, so
  without §W "the beat fires" never implied "a player could get there". It takes in-scene
  cut/passage edges deliberately — Dellhollow's levels are joined by 42 self-edges and a
  walk-only fill calls the gate arrival and the log-jam unreachable when they are 0.4 m
  apart in plan and 10 m in height. A clean run is 69/1 until ch2.road's anchor is fixed.
- node tools/playthrough_test.mjs --port=3000 — THE END-TO-END RECEIPT (real Chrome):
  cleared localStorage → NEW GAME → every Ch1 beat firing on ITS OWN trigger (it never
  calls Story.force) → the sealed gate edge absent before the flag and live after →
  the handoff TAKEN as an edge into ow-valley → Ch2 → maren in activeParty() → a cold
  reload built from `at` alone landing in the same scene, shot and place. Every other
  gate in this repo was green on 2026-08-02 while the game had no chapter in it; a
  suite of green unit gates cannot tell you the thing is not a game. This one walks it.
- **node tools/findability_test.mjs — THE FINDABILITY GATE** (no browser, no network,
  0.4 s): for every villager, the shot whose BAND owns their post, their own body box
  projected into that camera, and depth.png asked whether those pixels survive the plate —
  plus every story beat's trigger ground. FAIL for anyone the story names, WARN for an
  ambient villager. It exists because Poppy was 100% behind her own stall canopy with every
  gate green, and the user could not complete Chapter One's first objective: A TEST THAT
  TELEPORTS TO A COORDINATE AND CALLS `Npc.talk()` BY ID DOES NOT PROVE A HUMAN CAN FIND THE
  PERSON STANDING THERE. Her record even read "Verified on the walk network, not by eye" —
  that sentence WAS the defect. QA docs/qa/findability/index.html.
- node tools/dialogue_test.mjs — THE CAST GATE (no browser, no network): every speaker
  has a bust §2, resolves to a cut-in or a thumbnail with the alpha MEASURED IN THE PNG
  §2b, and the PARTY has a face on every beat the player speaks — choice lists
  included, since a choice is the one line the player authors §2c. Also bodies, posts
  and arrival clearance.
- tools/cine_sweep.mjs — WHICH ANGLE SHOULD THIS SHOT BE AT. Calls the shipped solver with
  yaw/pitch overridden and ray-casts the result against the walk bundle's own triangles
  (BVH, no Blender, ~3 s for 468 angles x 7 shots), so "does the region fit" and "can the
  camera see it" are one answer. `--fov/--margin/--maxdist/--cameras` sweep the knobs and
  proposed shot lists. A SCREEN, not a verdict: the bundle is the blockout, and the bake's
  ray-cast against the dressed master is still the only visibility oracle.
- tools/nav_eval.mjs — perceptual navigability (judge PINNED gemini-3.6-flash; noise
  ±0.20/shot at N=5 → N=10 for per-shot claims). Viewer: docs/qa/naveval/viewer.html
- tools/plate_flat.py — background-leak audit.
- tools/walk_bodygate.mjs — body-box step gate: can a character actually get from one
  walk sample to the next? Reproduces play3d's walkStep() at its own 0.075 m stride
  (ray gates see headroom, not bodies). A calibrated SCREEN, not a verdict — confirm
  hits with a body. It reads THE FILE — pair it with walk_engine_gate.
- **node tools/walk_engine_gate.mjs --scene <bundle> --port 3000 — THE FILE-VS-ENGINE
  GATE (real Chrome).** Censuses standable cells TWICE on one lattice: triangles out of
  the shipped GLB, and SIM.walkFloors() inside the running game. Red on any cell that is
  floor in the file and not floor for the player, and on SIM.bvh().fail > 0. Every other
  walk instrument here (walk_bodygate, glb_read, cine_solve, routes_derive) reads the
  file, which is why 209.6 m2 of Emberbrook and 54.3 m2 of Dellhollow could be
  non-collidable for weeks with every gate green: A WALK-NETWORK GATE THAT NEVER ASKS
  THE ENGINE IS MEASURING THE ARTIST'S INTENT, NOT THE PLAYER'S WORLD. `--reduced` is
  the no-browser mechanism proof (three-mesh-bvh permutes geometry.index.array in place
  while GLTFLoader shares one index attribute between primitives).
- tools/scene_redteam.mjs — LLM scene critique (naive + map-informed checklist modes,
  adversarial verify; judge PINNED, shares GEMINI_API_KEY). Calibrated 4/5 hand / 2/5
  matcher on the user's own annotated complaints (sweep 2; was 3/5 — the gate rows moved
  because 96114cc recomposed the shot, not because the judge changed). Stage 2 filters weak
  criticism, NOT confabulation — triage survivors by eye, and MEASURE before building.
  `--replay a,b` (newest first) merges runs into ONE report and every plate records which
  run judged it; `--plates` pins the bake and stale shots self-mark against-superseded-bake.
  CURRENT: docs/qa/redteam/run-20260731-dellhollow2/index.html — all 16 Dellhollow plates
  (:3000/docs/). Emberbrook is UNSWEPT: its blockout frames die to the dressing pass.
- RED-TEAM FIX LOOP (user-ratified workflow, run on their ask): judge finds a flaw →
  MEASURE the claim on an instrument (geometry_audit --region / ray census — never
  build from an unverified perception; see the pink-plank confabulation) → builder
  fixes → re-bake → re-judge; stop after K consecutive clean rounds, pin findings to
  bake stamps (plates going stale mid-loop is a measured failure mode). At 3/5 recall
  a clean round means "the visible part is clean," not done — it is not the review gate.

## Character factory (pipeline order; docs in each tool's header)
1. tools/gen-character.mjs (busts/expressions; config tools/characters/<name>.json)
1b. tools/gen-cutin-art.mjs — draws each portrait FOR the matte: chest-up on a flat
    magenta key, identity anchored on bust.png, expression sets from
    tools/characters/cutins.spec.json (the cast's emotional coverage; `rest` is a
    CHARACTERFUL at-rest face per VOICES.md, never deadpan). Studio plates are
    gitignored; the matte is what ships.
1c. tools/gen-cutin.py — mats that art into cut-in portraits (chroma key; the old
    bust-salvage path stays as the fallback) + public/assets/characters/cutins.json,
    the manifest dialogue.js picks cut-in vs framed-thumbnail from. ROLLOUT IS GATED
    AND ATOMIC PER CHARACTER on tools/cutin_edge.py (edge_noise/halo/ramp/speckle/
    pinhole) plus a NO-REGRESSION floor: a set that would lose a scripted or
    already-shipped mood is refused and the character keeps today's art.
    QA docs/qa/cutins/index.html — every plate over a baked plate, read ACROSS a row
    for identity drift. Baseline before the pass: 19/62 plates passed the gate.
    **`cutin_edge` STILL HAS NO CHROMA TERM — the hole is OPEN** (2026-08-03). Its `halo`
    is a LUMINANCE difference, so a rim of the wrong HUE at the right brightness is
    invisible to it: a bright chartreuse outline sat on **79 of 112 SHIPPED plates**, every
    one gate-green, until someone LOOKED. Cause was in the despill, which estimated key
    share by summing the R and B deltas against the local opaque reference — so a
    legitimately brighter edge pixel read as magenta residue and the subtraction drove R
    and B under G. Fixed by solving the mixture on the key's own chroma axis,
    `(R+B)/2 - G`: 79/112 → 20/119, magenta residue unchanged or lower everywhere.
    THE GATE ITSELF WAS NOT FIXED. Until it grows a chroma term, a green/cyan/magenta
    fringe can ship gate-green again — A GATE THAT MEASURES BRIGHTNESS CANNOT SEE COLOUR.
    **RE-ROLL `rest` FIRST, NEVER LAST**: `rest` is the identity reference the mood plates
    are drawn from, so re-rolling it after them orphans the set against a superseded
    reference (sorrel's striped apron went plain white, her peel wood → terracotta). The
    chain IS the identity.
    **THE TWO RUNTIMES DRAW DIFFERENT ART**: 2D (chapter1/2) uses `expr-*.png` busts, 3D
    uses `cutin-*.png`. 15 scripted moods exist in one and not the other — LATENT, not
    live, because they sit only in story.json. Lake's 2D busts were still the RETIRED
    design (black hair, green vest, cape) against a ratified brown-haired, red-vested
    bust.png, so his neutral line showed one man and every emotional line another.
2. tools/gen-turnaround.mjs — A-pose 4-view sets (style anchor = user's Vesper A-pose;
   hands empty; capes swept back)
3. Tripo (user via web, or tools/gen3d.mjs API) → GLB
4. Intake gate: joint×IBM≈I probe; repair via tools/vesper_fix_glb.py if broken
   (Vesper's export was broken; later deliveries were clean)
5. tools/vesper_retarget.py — per-clip donors (Quaternius UAL idle/walk CC0 +
   KayKit jump), solved arm/leg offsets, per-clip arm targets; read its docstring
6. tools/vesper_verify.py gates (arms ≤15° off vertical, elbow 10–40°, hand-coat
   clearance) → MODELS registry (play3d) / npcs.json bodies
- Gen-art rules: no third-party IP names in prompts; full-scene style refs OK,
  character crops may trip filters; flat even light for mesh inputs.

## Music
- public/js/music.js + public/game/music.json; tracks public/assets/music/*.mp3
  (original, Lyria via GEMINI_API_KEY); loop points via tools/music_loops.mjs.
  Agents: NEVER audible in browser tests — ?nomusic=1 (exception: transition_test,
  which mutes at source).

## Scope rulings (user decisions that bound the work)
- **SINGLE-PLAYER FOR THE PROTOTYPE** (user ruling 2026-08-02, verbatim: "Let's leave the
  two-player version of the game as an upgrade for later, and in the prototype we can keep
  things as single-player"). The 3D runtime is single-body and STAYS so. Chapter One's climax
  (two keepers on twin sigil plates) and Chapter Two's (a six-hand winch) are staged as
  single-player + companion so nothing soft-locks. DO NOT re-open this as an open question —
  it was carried on a status list as "undecided" for hours after it had been decided, which is
  its own small lesson: a ruling that is not written down is a ruling that gets re-asked.
- **LAKE IS A PARTY MEMBER**, not a narrative-only companion (settled 2026-08-02: the user
  refers to "Lake as a party member", and growth.json already carries his record with
  `joinFlag: lake-joined` and stats). His `joinFlag` stays.
- **DELETE SUPERSEDED WORK, DO NOT ARCHIVE IT** (user ruling 2026-08-02, emphatic, given
  twice). They asked for a repo cleanup in the morning and repeated it in the evening:
  "I emphatically disagree with this, we should be deleting stuff - that's exactly what I
  asked for this morning when I said to clean up the repo". THIS OVERRIDES the
  agent-authored policy in public/game/scenes.js ("Deprecate by MOVING a group down, never
  by deleting; bundles stay on disk and in git") — that line was never a user decision and
  must not be quoted back at them as though it were. It also overrides the reflex, twice
  displayed by me, of answering a delete request with "deleting gains nothing because the
  blobs stay in history": TRUE ABOUT SIZE, IRRELEVANT TO THE ASK. A tree full of superseded
  bundles costs comprehension, misleads measurement (the 3.2 GB "deployable" figure was
  mostly dead scenes) and invites work against dead art.
  WHAT STANDS: the three-way verification METHOD (referenced by no file, named in no doc,
  inert by its own header) is still how a deletion is made safe. Verify, then delete —
  do not verify, then find a reason to keep.
- The goal is A PLAYABLE PROTOTYPE, not a polished product (user steer 2026-08-02) — prefer
  the 80/20 that gets the thing playable over the round that gets it perfect.

## Working rules (hard-won)
- Git: stage-and-commit one breath WITH pathspec on the commit; never `git add -A`
  (shared index across agents). PUSH REGULARLY (user standing order 2026-08-01): the
  coordinator pushes migration/3d-hybrid to origin after each substantive batch —
  not necessarily every commit, never less than once per work session. VERIFY the
  push with `git ls-remote --heads origin <branch>` — never trust a piped exit code
  (the 2026-08-01 3.3GB first push died on GitHub's ~2GB pack limit while reporting
  success through `| tail`; big pushes go in fast-forward chunks). SAME CLASS
  (2026-08-01): `<cmd>; echo EXIT=$?` makes the shell's status the echo's — a failed
  Blender rebuild reported "exit 0" to the harness all session. No trailing echo
  after commands whose status matters; the last command IS the status. The proof of
  any build is the ARTIFACT (mtime, digest, SAVED line), never the report.
- Blender: always `-b --python-exit-code 1`. Builders deterministic — gate is a
  SHA-256 CONTENT digest (world verts to 1e-5 + materials + lights + camera), NOT
  byte-compare (.blend serializes memory addresses; see tools/embint_verify.py).
  Disk: clean temp renders/profiles every run. A bake that SIGABRTs deterministically
  at render start on ONE camera while others pass is the Metal kernel cache corrupting
  (.ips names ccl::MetalKernelPipeline::compile / free_tiny_botch): quarantine
  /var/folders/*/C/org.blenderfoundation.blender and rebake — no free-RAM gate cures it.
- Browser verify: foreground tab for rAF/screenshots (osascript Chrome activate);
  hidden-tab canvas screenshots go stale — trust SIM readPixels probes.
- emb-townwalk ships the DRESSED realtime tier (emberbrook-realtime.blend): any lane
  that rebuilds the MASTER owes a dressing re-run (emb_dress --tier realtime --out)
  in the same window, and anyone who rebuilds the REALTIME blend must re-run
  emb_decimate --save (the decimation is baked into the blend, deliberately — an
  export-time-only decimation would be silently undone by the cron's next tick).
- Blender datablock rule (three paid instances: save_render, im.scale, decimate):
  EDITING A DATABLOCK IS NOT EDITING THE ARTIFACT — any consumer that re-reads from
  disk needs the edit written out and the datablock repointed; the only proof is
  measuring the artifact, never the log.
- **A BACKTICK INSIDE A CSS COMMENT ENDS THE TEMPLATE LITERAL** (2026-08-02, hit
  INDEPENDENTLY by two lanes within one hour: ui_kit.js:122 and battle_turnbased.js:207).
  Every UI module keeps its stylesheet in ``const CSS = ` … ` ``; writing a quoted word
  like `` `sm` `` in a comment inside it TERMINATES the string, and the file becomes a
  SyntaxError. HEAD parsed, the working tree did not — it crashed economy_test and
  encounter_sim outright. The nastier half: a module that fails to parse still LOOKS
  present, and since every module self-arms at load AND on 'eb-scene', a parse error is
  invisible until an in-place scene swap silently leaves the module absent.
  transition_test's console gate is what catches it. Use plain quotes in CSS comments.
- **AND A BACKTICK INSIDE A DOUBLE-QUOTED `git commit -m` RUNS AS A COMMAND** (2026-08-03,
  paid immediately after writing the bullet above). Committing a message that quoted a word
  in backticks made zsh execute it: the shell printed `command not found`, the word was
  substituted OUT of the message, and THE COMMIT STILL SUCCEEDED AND PUSHED — a silent
  edit to the permanent record, with a nonzero-looking error that belonged to a
  subshell rather than to git. Same root as the CSS-comment trap: a backtick is live
  inside double quotes wherever it appears. **Use single quotes for commit messages, or
  a heredoc.** Do not amend a pushed shared branch to fix cosmetic damage — rewriting
  history other lanes have fetched costs more than the missing word.
- **A TEST THAT CANNOT BOOT IS NOT A TEST THAT FAILED.** transition_test exits 13 at
  `== BOOT` while any lane (or the townwalk refresh cron) is mid-write on
  public/assets/scenes/townwalk/scene.glb (~51 MB) — the boot gate waits on that asset.
  Re-run once the export settles; do not read it as a regression, and do not "fix" code
  against it.
- **`git commit -m … -- <pathspec>` COMMITS THE WORKING TREE AND IGNORES THE INDEX**
  (2026-08-03, paid for across three lanes). A lane staged ONE hunk with `git apply --cached`,
  then committed with a pathspec — the pathspec form re-reads those paths from the WORKING
  TREE, so it published 309 insertions of two other lanes' in-progress edits. The repair then
  diffed against the base it started from rather than current HEAD and reverted a third lane's
  committed beats out of HEAD. Nothing was lost (restored byte-identical, sha-verified) but
  ORIGIN WAS BRIEFLY RED and two lanes had 20 minutes of work committed under another's name.
  With a dirty shared tree: stage precisely, then `git commit` with NO pathspec, or
  `git commit --only <paths>`. And repair against CURRENT HEAD, never against your own base.
- Agent lanes: written handovers (transcripts expire); DAYLOG notes per phase;
  coordinator owns play3d.html, the town maps, and this file.
- Documentation bar (user ruling): notes carry AUTHORITY — a written interpretation
  short-circuits future investigation (the loop-stairs "walker pessimism" note hid a
  real defect for a day). Record measurements WITH their instruments; an
  interpretation may be recorded only alongside the instrument that proved it. High
  bar for inclusion; condense over accumulate.

## World-building doctrine (earned in Dellhollow + the Emberbrook founding; details in DAYLOG)
- Footprints live IN THE MAP; the blockout derives floors AND doorsteps from it.
  A conflict fix is a landmark move or a lane waypoint — one line of map, one
  command to re-derive. Never re-cut floors in a district builder.
- A free-standing solid is SEARCHED, never authored (ring/clearance search against
  the walk network + camera probe sets). Measure the fallback in the same pass.
- Audit geometry WHERE IT LANDS, not where it was. A standable surface is not a
  buildable volume. A bound loose enough to refuse everything is a veto, not a test.
- "In frame" ≠ "visible" ≠ "unobstructed ray": probe occluders (incl. the
  camera-inside-tree-crown case) before re-aiming; move the occluder, not the aim.
  Bake ray-cast is the ONLY visibility oracle. For dusk grades, measure GROUND
  luminance on the region probes — the floor is what has to be read.
- Night grades (Emberbrook, measured HISTORY not law — DAYLOG 2026-08-01 night lane):
  adjusting an existing light has never moved this town; adding a new source always
  has (sky ladder, lamp wattage twice, moon colour: inert or exhausted; the moon's and
  the waystone lantern's ADDITION are what made frames read). Solve a class recipe on
  the class's MEDIAN member; a plate under the 25-median floor gets its OWN two-rung
  moon slope (probe rungs at 1008x576/28spp, anchor on the shipped plate's measured
  median) — slopes ran 4.8-10.1 L/W across one town, so never borrow another shot's.
- Road ribbons stop at their own map edge's end; an edge carrying a camera boundary
  must keep walkable identity; prop-class pads size to the prop; the walk pad IS
  the doorstep.
- Interiors: separate blends via tools/embint_lib.py (arbitrary-plan walls — the
  box was in the code, not the art direction) + embint_verify.py gate; bake via
  tools/depth_bake.py (cine_solve is town-only). Ceilings stay when the camera is
  inside the room; every ray must terminate on real geometry; test the body as a
  BOX, probe floors with a 25 mm cross (plank shadow-gaps are not holes). Each
  bundle ships doors.json (which wall the door is in — the one fact derive can't check).
- Nav-eval noise is ±0.20/shot at N=5: per-shot claims need N=10; judge stays pinned.
