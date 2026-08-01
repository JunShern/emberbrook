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
- Canon rulings log + nightly state: **docs/qa/DAYLOG.md** (append handover-quality
  notes there after major phases; agent transcripts expire).

## The townmap system (the authoring layer for every town — start here for town work)
- public/townmap/viewer.html?town=<name> — 3D/plan/elevation viewer of a town's map:
  landmarks, path edges, districts, **parcels (each derives a scene contract + sceneKey)**,
  draft camera frustums, live validation. Serve repo /public on a local port.
- public/townmap/<town>.map.json — the landmarks-first town layout: THE design authority
  a town model is built from (Dellhollow was built this way). Emberbrook's carries
  dated REDLINE notes from the user — honor them.
- <town>.cameras.json (authoring; grade in defaults.exposure) → tools/cine_solve.mjs →
  .cameras.solved.json → tools/scenegraph_derive.mjs → scenegraph.json →
  tools/cine_bake.py (Blender headless, ALWAYS `-b --python-exit-code 1`; bake ray-cast
  is the ONLY visibility oracle). PLATE BAKES RUN FULLY PARALLEL (user standing order
  2026-08-01): one Blender process per camera, wall-clock = slowest frame, never
  sequential; still rebake ONLY frustum-affected cameras on incremental changes.
  MEMORY CAP (2026-08-01, the laptop drowned in swap at 6 bakes + a Metal render):
  max 3 concurrent heavy Blender jobs town-wide across ALL lanes; check
  `sysctl vm.swapusage` before spawning — if swap used > 75%, run 2. Parallel
  within the budget, queued beyond it. Lanes coordinate via main. routes: <town>.routes.json (tools/routes_derive;
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
  dialogue, route_overlay, music. Each self-arms at load AND re-arms on 'eb-scene'.
- Game data (public/game/): monsters, items, encounters, growth, shops, music.json
  (map rules first-match-wins), npcs.json, dialogue.json.

## Test gauntlet (run what your change touches; all green before ship)
- node tools/slice_test.mjs · cine_test.mjs · seam_test.mjs · seam_walk.mjs ·
  economy_test.mjs · battle_sim / encounter_sim · transition_test.mjs --port=<port>
  (real Chrome; needs a server on the port serving /public)
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
  hits with a body.
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
1b. tools/gen-cutin.py — mats busts into cut-in portraits (alpha cutout, chest-up) +
    public/assets/characters/cutins.json, the manifest dialogue.js picks cut-in vs
    framed-thumbnail from; QA docs/qa/cutins/index.html
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

## Working rules (hard-won)
- Git: stage-and-commit one breath WITH pathspec on the commit; never `git add -A`
  (shared index across agents). PUSH REGULARLY (user standing order 2026-08-01): the
  coordinator pushes migration/3d-hybrid to origin after each substantive batch —
  not necessarily every commit, never less than once per work session. VERIFY the
  push with `git ls-remote --heads origin <branch>` — never trust a piped exit code
  (the 2026-08-01 3.3GB first push died on GitHub's ~2GB pack limit while reporting
  success through `| tail`; big pushes go in fast-forward chunks).
- Blender: always `-b --python-exit-code 1`. Builders deterministic — gate is a
  SHA-256 CONTENT digest (world verts to 1e-5 + materials + lights + camera), NOT
  byte-compare (.blend serializes memory addresses; see tools/embint_verify.py).
  Disk: clean temp renders/profiles every run.
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
