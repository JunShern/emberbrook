# PAUSED LANES — how to resume each one (2026-08-02, ~21:30)

Five lanes were paused mid-flight when the account moved to a lower tier and the user
asked to **focus only on deployment**. Nothing here is abandoned; each entry is written so
a cold session can pick it up without re-deriving anything. Order is by how close to done.

**All committed work is pushed to `migration/3d-hybrid`.** Nothing below is lost — the
only uncommitted things in the tree are other lanes' in-flight plate bytes.

---

## 1. DEPLOY — the only lane still active. See `docs/DEPLOY.md`.
Not paused. Everything else waits behind it.

## 2. EMBERBROOK PLATE RE-BAKE — 3 of 7 plates done · commit `a23fd70`
**Done:** `square`, `orchard`, `pondlane` re-baked and committed with `cine.json`. The
square's staircase ledge is **gone** — 68% of that frame changed, and the orchard/square
contrast (0.09 vs 9.14 mean diff, same settings) proves it is real bounce light, not
denoiser noise.
**Remaining:** `arch`, `therise`, `gateroad`, `gatefield` — they bake straight off
`emberbrook-dressed.blend`, which is current and needs **no** rebuild. Grades are in DAYLOG.
**Unrun gates:** cine_test (to clear the baked-vs-solved red), routes_derive,
transition_test, walk_engine_gate. Green already: slice 848/0, seam 294/0, seam_walk 9/9.
**THE TRAP, paid for twice in this lane:** `arch` died silently — the log ended mid-run with
no `BG` line and no exit code, and a stale monitor flushed a *misleading* "BLENDER_EXIT" an
hour late. **Verify a bake by the ARTIFACT (mtime, byte size, its `cine.json` record), never
by the log or a notification.**
**Two decisions waiting on the user:** a bunting post moved ~0.9 m and now throws a hard
shadow stripe up a plaster wall; and `gatefield` is the only shot framing gate-court's
recovered floor, so it must not be skipped.

## 3. CHARACTER LIGHTING — cause 3 of 3 landed, unverified · commit `c0404c9`
**Done:** the AgX tone curve (see the commit message — it is the long one), gated behind
`?tone=off|aces|agx`. Also catches that the backdrop would have been tone-mapped *twice*.
**Remaining, and this is most of the job:** the per-town sun DIRECTION from each town's own
`defaults.lightRig.sun` in `<town>.cameras.json`; the ambient-vs-key fill ratio (0.95 white
ambient against a 1.3 key is ~42% flat fill — that is what reads as "unlit"); **Dellhollow
has no lightRig at all** and its key must be derived from its plates or its blend; and the
A/B across overworld and battle (only the two towns were checked).
**Reuse, do not re-derive:** the Blender-Z-up → three-Y-up conversion already exists in
`play3d.html` from the overworld lane. Instrument: `tools/light_shot.mjs` (new, committed).
Before/after frames: `docs/qa/charlight/`.

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
