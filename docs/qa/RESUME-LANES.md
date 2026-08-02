# PAUSED LANES — how to resume each one (2026-08-02, ~21:30)

Five lanes were paused mid-flight when the account moved to a lower tier and the user
asked to **focus only on deployment**. Nothing here is abandoned; each entry is written so
a cold session can pick it up without re-deriving anything. Order is by how close to done.

**All committed work is pushed to `migration/3d-hybrid`.** Nothing below is lost — the
only uncommitted things in the tree are other lanes' in-flight plate bytes.

---

## 1. DEPLOY — the only lane still active. See `docs/DEPLOY.md`.
Not paused. Everything else waits behind it.

## 2. EMBERBROOK PLATE RE-BAKE — **DONE, 7 of 7** · commits `a23fd70`, `3c948a5`, `c330ddb`
All seven plates re-baked off `emberbrook-dressed.blend`. `arch` and `therise` turned out to
be already on disk (proved by artifact + grade + pixels, not by log); `gateroad` and
`gatefield` baked here. `gatefield` shows gate-court's recovered floor — the bare tan earth
scar in the court paving is now a small planted pocket. `gateroad` is visually unchanged
(0.06% of pixels) and did not need its 725 s.
**Gates:** cine_test 479/1 (the one red is the PRE-EXISTING `square` charPxFar 37-vs-38,
provably not plate-related) · routes_derive clean · slice 848/0 · seam 294/0 · seam_walk
10/10 · transition_test 168/0 · walk_engine_gate GREEN. Baked-vs-solved red CLEARED.
**Traps paid for, all three in DAYLOG 2026-08-03:** a Metal kernel-cache SIGABRT that the
harness reported as exit 0 (quarantine the cache; read the .ips); a coordinator "it's dead"
report against a bake that was ten minutes into its beauty pass (absence of an artifact is
evidence only once the process is gone); and a `pgrep -f` matcher that matched a
neighbour's waiter shell and invented a 25-minute blocker.
**STILL WAITING ON THE USER:** the bunting post that now throws a hard shadow bar up a
plaster wall — frame at `docs/qa/emberbrook/redress/bunting-post-shadow.png`.

## 3. CHARACTER LIGHTING — DONE and verified · commits `c0404c9`, `755e6f1`, `236bf72`
All three causes landed: the AgX tone curve, the per-town sun from each town's own
`defaults.lightRig`, and fill:key down from ~1.3:1 white to **0.34** warm-sky/cool-ground.
Full record in DAYLOG 2026-08-02 (night). Frames: `docs/qa/charlight/v2/`.
**The defect this lane actually found:** `c0404c9`'s message under-claimed. The code for
all three causes was already in its 313 lines of `play3d.html`; what was missing was
`public/game/lightrigs.json` — the second tier of charLight's rig lookup — left **untracked
on disk**, so every clone and every `dist` silently put Dellhollow back on the page-default
sun. Committed as `755e6f1`. A message that under-claims costs as much as one that over-claims.
**Dellhollow's key** (no `lightRig` in its cameras.json): `SUN_key` 12.0 W, rot 53.285/0/112.38,
colour 1.0/0.79/0.56, elev 36.7° — derived from the blend read headless AND from
`tools/look_golden.py`, which set exactly that rig in code. A third instrument confirms it:
projected into `del-cine weave`'s own camera the key lands screen UP-LEFT, and the plate's
free-standing deck posts are lit on their screen-LEFT faces.
**One tone curve does not serve three renderers, and the shipped code already handled it:**
AgX in baked-plate towns, `NoToneMapping` in `ow-*` (`play3d.html:1010`), and the battle arena
untouched because `battle_stage3d.js:602` builds its own renderer. All three verified, not read.
**Left for the user, a taste call not a measurement:** the character is now dimmer, and on
the darkest Emberbrook night plates the FACE loses some legibility. Correct direction for the
complaint; the readability floor is a design decision. `?charlight=0` restores the old rig.

## 4. DELLHOLLOW CARRYOVERS — 2 of 3 done · commits `6ca774f`, `c2eb8f0`
**Done:** the cookhouse doorstep moved from the building's south side to its north front
(27/27 body rays clear, was 0/27); and the gate-stair blocker turned out **not** to be the
bunting at all but **a 7.61 m flagpole driven through the stair** — my handed-down diagnosis
was wrong twice and the lane's own measurement found it.
**Remaining:** `del.gullgirl`'s clearance broke as a knock-on of the doorstep move —
`dialogue_test` is **1398/2**, both reds hers. The lane's last words before it died: the
arrival needs the full 4.0 m radius+wander which the deck cannot give, **but the doorstep
move freed her original south-side post, so putting her back there is the fix**. Start there.
**Also owed:** the cookhouse's door LEAF is still on the SOUTH face (joined into
`qm_cookhouse`, no separate mesh) — the prompt is now right and the art is not. Recorded in
the map as `_owed_bake_2026-08-02` with the window re-spacing it needs.

## 5. COMBAT CLIPS — done and committed · commit `5a4e165`
All six rigs carry `Attack`/`Hit_A`/`Death_A` (Quaternius UAL, CC0 1.0, licences recorded).
Gates green: 6/6 vesper_verify, battle_sim, encounter_sim, ARENA PLAYTEST GREEN.
**Owed:** `transition_test` was mid-gauntlet (17 ok, 0 real failures) and **the live clip
binding is not proven** — arena_playtest ran under such contention that bodies rendered at
`proxy` tier, so the clips are confirmed in the GLB but never seen playing in a battle.
`scratchpad/clipprobe.js` + `arena_playtest --eval=` closes it.
**Known defect, evidence attached:** two-panel open coats break under `Death_A` (f32–f48, a
flat hard-edged slab). Lake and Finn both; Maren, Mara, Pip clean — so it is the GARMENT
CLASS, not the rig or the clip. Fix is a skin reweight upstream, next character slate.
**Taste call parked for the user:** the attack donor is a *sword* lunge on empty-handed
characters. One-word swap (`attack=Punch_Cross`) if the mime bothers them.
**Scoping note for next time (user correction):** all six rigs got clips, but only Vesper,
Lake and Maren are playable — scope to what the player sees, not to what is uniform.

## 6. SCENE DELETION — DONE · 7 commits ending `3c197eb`
533 files, 64+ dirs, ~637 MB out of the working tree; `public/assets/scenes/` 60 → 35.
**Its most valuable act was refusing part of its brief:** 17 of the 30 "orphans" I named
are LIVE ART — the 2D runtime's backgrounds for Chapters 1–3, absent from `scenes.js` only
because that file is the 3D registry. Deleting them would have blanked the only playable
chapters. Nothing further owed.

---

## HOW TO RESUME
1. **Poke the agent in the sidebar first if it is still listed** — that revives the original
   with its context. Relaunching instead creates a TWIN, and two twins collided tonight
   (one left an orphaned bake script racing the original's own output).
2. If it cannot be poked, relaunch from the entry above — each one is written to be a
   sufficient brief on its own.
3. Re-create the 20-minute status cron if the session restarted (`lane-status` skill).
