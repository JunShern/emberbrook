# RESUME — paused 2026-08-02 (usage-tier pause, all lanes stopped clean)

Everything below was IN FLIGHT when the user paused work. Nothing is half-written:
commit `44c4b2d` checkpointed every dirty file, remote verified, tree clean, no Blender
or generation processes alive. This file is the handover; delete or rewrite it when the
lanes are back and their work has landed.

Read CLAUDE.md first for doctrine. Read docs/qa/DAYLOG.md for what happened before this.

---

## Lane 1 — TRIGGERS / MARKERS / OLD GATE (agent stopped; work partly SHIPPED)

**Shipped and verified** (commits 3cae034, ad8d47e, plus play3d.html content that rode
into 77f751f/8b085e3 — verified byte-level, nothing lost):
- The step-away-and-return bug is FIXED. Root cause: `sgTick()`'s arrival-suppression
  latch gated the PROMPT, not just auto-fires, and `sgHandoff()` reset `armed=null` for
  every edge on every handoff — so any pad containing the player at bind time had its
  prompt swallowed until step-out/step-in. Prompts are now level-triggered; the latch is
  consulted by auto-fires only (seam-canon no-return still holds — probe: 60 ticks on an
  arrival pad, prompt up, zero fires).
- Markers now cover every transition class, not just doorways: `markersTick` no longer
  skips `e.auto`. Coverage measured — emb-cine 4/4 doors + 1/1 portal + 22/22 seams,
  del-cine 6/6 + 1/1 + 40/40, all 10 interiors, ow-valley 2/2.
- New instrument: `tools/trigger_probe.mjs` (browser mode + `--static` declared-vs-derived
  audit). Gauntlets green at pause: transition_test 168/0, dialogue_test 1210/0.

**NOT DONE — resume here.** The Emberbrook old gate has no marker because the transition
was never wired, and the coordinator ruled it should be:
1. Fix `tools/scenegraph_derive.mjs`: read `sealed` on map exits; pair portals to land
   exits BY NAME (portal declares its exit id) instead of first-in-list; replace the
   silent `continue` on `target:null` with a printed WARN naming the unpaired portal.
   (The current pairing CANNOT reach sigil-gate because valley-road-south is listed first
   — that is the latent trap.)
2. Wire `valley.region.json road.portals 'old-gate'` ↔ `emberbrook.map.json
   'sigil-gate-downstream'` (currently `target:null` on one side, `sealed:true` on the
   other). The seal is Ch1 story canon. Edge must be CONDITIONAL on the story flag that
   opens the sigil gate — check `public/js/chapter1.js`; if no clean flag exists, report
   what does and PROPOSE the minimal one, do not invent story. Sealed ⇒ sealed
   presentation and NO marker (a red arrow onto a sealed gate is a lie). Post-flag ⇒
   two-way edge + markers.
3. Same treatment for `forest-north` at forest-trailhead (declared, no edge).
4. Re-run the `--static` audit to zero unexplained rows; transition_test + dialogue_test
   green; pathspec commit; `git ls-remote` verify.

---

## Lane 2 — CUT-IN CAST ROLLOUT (agent stopped; Vesper SHIPPED, mains mid-flight)

**Shipped**: Vesper's full suite (commit 9a34a8e) — 10 user-picked poses live in game
(rest + happy/wry/worried/surprised/determined/sad/tender/thinking/annoyed), manifest
updated, dialogue_test green.

**Ratified but not built:**
- LAKE: **base candidate 3** is his ratified base, and his LOOK CHANGED to
  `public/assets/refs/lake.jpeg` (tousled brown hair, charcoal hooded cape over both
  shoulders with brass flame clasp, green X-laced vest). `tools/characters/lake.json` is
  already updated. Next: his 10×3 pose matrix by the Vesper recipe → picker page at
  `docs/qa/cutins/lake-poses/` → user picks. **Also owed (not started):** his
  bust.png / expr-*.png / sheet.png / 3D model re-anchor to the new identity. NOTE the
  physical tension: the old design deliberately swept the cape BACK so arms read in
  silhouette for the 3D model and sprite; the new ref drapes it front.
- MAREN: **base candidate 1** ratified, BUT the user flagged its matte as messy and the
  coordinator confirmed on the artifact: magenta fringing through flyaway hair strands
  and headband tails, worst above the crown. FIX BEFORE her matrix. Preferred order:
  (a) despill targeted at the partial-alpha hair RAMP band only (global despill on solid
  pixels was refuted earlier — see gen-cutin.py header), (b) widen bloom-cleanup radius
  after verifying her palette distance from magenta, (c) re-roll the base with a stronger
  drawn-outline/no-wisps edge instruction. Verify at 100% zoom composited over a NIGHT
  plate — magenta reads worst on dark.
- ROWAN: candidate B is his ratified new design; his new bust/bust-key art is committed
  in this checkpoint. His cut-in set (used-moods only — he is not a main) is not built.
- NPCs: not started. Order by dialogue frequency, single gated roll per mood.

**Pipeline state (all user-ratified, encoded in the tools):** pose-first prompt with the
animator-creativity bid; chained diversity (roll 2 sees roll 1, roll 3 sees both) with the
"uniquely different acting" clause; `calm` branch for rest plates; waist-up framing spec
worded positive-only (naming "bust" primed bust crops); base built by
`gen-cutin-base.mjs` at donor scale 0.52; matte cuts enclosed key islands to alpha 0 plus
a bloom-cleanup pass at radius 95 (verify per-character palette distance first).
**Tiered budget**: `cutins.spec.json` has `moodDefaults` (shared facial grammar — worry
brow RAISED not knitted, determined = level brows, tender = guard-drop event) and
`mainCharacters: [vesper, lake, maren]`. Mains inherit all defaults; everyone else
inherits only the moods their dialogue actually uses. Per-character overrides always win.

---

## Lane 3 — DELLHOLLOW EXITS (agent stopped; NOT started, only reading)

Two user rulings from live play (2026-08-02), neither implemented:
1. The overworld exit is confusingly placed — it must sit AT the main entrance gate where
   the player spawns. Check map history for why it sits where it does BEFORE moving it;
   honor seam-canon adjacency without spawn-overlap.
2. Shelf-west reshuffle: the stairs up to the gate are inaccessible — kill them as a gate
   route; the gate transition takes over Boatman's Rest's CURRENT door; Boatman's Rest's
   interior moves to the next building before the item shop. Flag dangling NPC/dialogue
   references. Assess (don't necessarily execute) the stairs MESH removal, including its
   re-bake bill.
Stamp both as dated USER REDLINE notes in `dellhollow.map.json` (map is authority), then
re-derive routes (`--check` CLEAN) + scenegraph; transition_test green; playable-first
(triggers/routes before mesh work). Coordinate with Lane 1 — it owns scenegraph_derive.

---

## Lane 4 — EMBERBROOK NIGHT LIGHTING (agent stopped; round essentially COMPLETE)

All 11 shots have modern plates on the rebuilt dressed blend. Final class table: lamped
shots 26.9–37.9 median luminance, both dressed lampless shots ~32.5. The floor pass lifted
the three dim shots (therise 19.3→27.2, arch 20.6→29.0, homerow 22.7→29.8). The realtime
townwalk re-export is in this checkpoint commit.

Rulings earned this round, all recorded in CLAUDE.md / the map / DAYLOG: the poolWarm
floor moved to 0.2593 backed by a three-lever refutation chain (moon-down rejected on
principle, lamp wattage refuted at +0.0000 across 2.94×, moon colour exhausted past its
authorised range); "adjusting an existing light has never moved this town, adding a new
source always has"; 1-wide serial bakes once a plate saturates the GPU; `emb_pixbox`'s
aspect bug fixed with a permanent `--selftest`.

**Two honest reds remain, both composition not light:**
- square `charPxFar` 37 px vs its 38 px floor — should retire naturally in the closeness
  round (NOT the same number as square's 37.9 median luminance, which is a PASS).
- gateroad — 21.9% visible, almost entirely tree canopy; PULLED from sign-off, on the
  camera/occluder ledger with pondlane's 40.6% soft flag. Its re-aim belongs to the
  closeness round.

**NOT DONE — the next phase.** User ruling (2026-08-02), stamped as a WORLD rule in both
towns' cameras.json `defaults._closeness_redline`: cameras are too high and far, characters
read as ants. Interior-shot closeness is the UPPER BOUND; ordinary town shots sit between
that and a far floor well above the old 38 px; deliberate establishing shots may go wider
but the player must stay easily visible. Sequence ordered: measure the interior charPx
bound → propose per-class bands and name which shots are establishing → re-SOLVE (not just
zoom: occlusion, spawn bands and seams all move) → cheap draft contact sheet at
1008×576/28spp with a character stand-in for scale → **user ratifies framing on drafts
before any full bakes** → bake. Dellhollow's re-solve joins the cliff lane's slate (task
#35); drone-y Dellhollow shots (the far-rim vista class especially) should be flagged as a
hit list first.

---

## Standing user rulings that outlive these lanes

- Cut-ins: everyone anchored LEFT (no party/NPC side split), 48 px in from the box edge,
  `CUTIN_MAX_PX` 364, `CUTIN_SINK` 0.20. Choice nodes name the chooser.
- The model picker is SESSION-scoped — a dev preview must never become the player body
  permanently (that was the finn-as-Vesper bug).
- Push regularly and VERIFY with `git ls-remote`; never trust a piped exit code, and never
  put a trailing `; echo EXIT=$?` after a command whose status matters.

---

## Session root moved (2026-08-02) — DONE, sandbox deleted

Sessions run from `/Users/junshernchan/projects/multiplayer-rpg`. The old `rpg-3d`
sandbox is GONE (deleted 2026-08-02, user-ruled), along with its Claude project
directory (~1.5 GB total). Before deletion, everything was audited file-by-file:

- Duplicates verified by hash and dropped (`Rogue_Hooded.glb` == the repo's `rogue.glb`,
  `vesper_sheet.png` == `characters3d/vesper.png`, three.js/GLTFLoader vendored in
  `public/lib/`, an older `genart.mjs`).
- RESCUED: the founding rendering-approach doc -> `docs/plans/target-system-origins.md`;
  the stray lamp classification -> `docs/qa/lampverdict.json`; the 25 orphaned transcript
  lines the mid-session copy missed -> `0e1c40c3-orphaned-tail-from-rpg3d.jsonl` in the
  Claude project dir.
- DELIBERATELY DESTROYED, user-ruled after the tradeoff was flagged: Vesper's original
  Tripo 3D delivery (zip + `base.obj` + 6 PBR textures + Mixamo FBX, ~130 MB), the
  prototype `dellhollow.blend`, and the original `dellhollow-slice` render bundle. The
  shipped GLBs (`vesper-v2.glb` etc.) are derivatives; **there is no longer a source mesh
  to re-rig or re-texture from.** If Vesper's model ever needs rebuilding, it starts from
  a fresh Tripo generation.
- Both memory sets were merged into the repo's project dir (21 files). The `rpg-3d` set
  had six design-canon memories no repo-rooted session had ever loaded.

The townwalk refresh cron is SESSION-ONLY and must be re-created in each new session:
`4-54/10 * * * *` -> `bash tools/townwalk_live_refresh.sh`, silent on success/skip,
report only on two consecutive failures (see /tmp/townwalk_refresh.log).
