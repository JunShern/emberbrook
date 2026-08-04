# Emberbrook — LLM playtest queue

Generated 2026-08-04T11:34:23.345Z by `tools/playtest_triage.mjs`. Source of truth: `docs/qa/playtest/queue.json`.

**An UNVERIFIED complaint is a lead, never a ticket.** Filed by an LLM playing the game through
screenshots and real key events; measured by instruments before anybody builds. REFUTED entries are
as informative as VERIFIED ones — the agent sees one still frame with no parallax, so it is biased
toward "I cannot find it", and that false-positive rate is this tool's calibration.

| status | sev | id | title | measured by |
|---|---|---|---|---|
| VERIFIED | P0 | PT-20260803-014 | Attempted to navigate towards the village, but the game is unresponsive and visually broken. | same as PT-20260803-013 |
| VERIFIED | P0 | PT-20260803-018 | Unable to move character on this map view after trying multiple coordinates across the screen, so I must give up. | same as PT-20260803-016 |
| VERIFIED | P1 | PT-20260803-002 | The player can leave the chapter on its first frame, and the objective follows them out | llm_playtester spine detector (public/game/story.json vs the running scene) |
| VERIFIED | P1 | PT-20260803-007 | The player can leave the chapter on its first frame, and the objective follows them out | llm_playtester spine detector (public/game/story.json vs the running scene) |
| VERIFIED | P1 | PT-20260803-008 | The player can leave the chapter on its first frame, and the objective follows them out | llm_playtester spine detector (public/game/story.json vs the running scene) |
| VERIFIED | P1 | PT-20260803-009 | Camera detached or character missing after battle | tools/llm_playtester.mjs run-20260803-195450 (rule 3 close-out) |
| VERIFIED | P1 | PT-20260803-013 | Game screen rendered as a tiny thumbnail in top-left corner | PIL luminance of the written frames + a 21-probe CDP experiment |
| VERIFIED | P1 | PT-20260803-015 | The player can leave the chapter on its first frame, and the objective follows them out | ow-valley meta.json spawn vs scenegraph edge pad + tools/playtest/spawn_gate.mjs |
| VERIFIED | P1 | PT-20260803-016 | Cannot move or interact with the valley map screen | the playtester picker (INSTALL_MOTOR) on a 5x5 screen grid, real Chrome |
| VERIFIED | P1 | PT-20260803-017 | Valley map ground is non-walkable | same as PT-20260803-016 |
| VERIFIED | P1 | PT-20260803-021 | The player can leave the chapter on its first frame, and the objective follows them out | llm_playtester spine detector (public/game/story.json vs the running scene) |
| VERIFIED | P1 | PT-20260803-023 | The player can leave the chapter on its first frame, and the objective follows them out | llm_playtester spine detector (public/game/story.json vs the running scene) |
| VERIFIED | P1 | PT-20260803-024 | The player can leave the chapter on its first frame, and the objective follows them out | llm_playtester spine detector (public/game/story.json vs the running scene) |
| VERIFIED | P1 | PT-20260803-027 | The player can leave the chapter on its first frame, and the objective follows them out | llm_playtester spine detector (public/game/story.json vs the running scene) |
| VERIFIED | P1 | PT-20260803-029 | The player can leave the chapter on its first frame, and the objective follows them out | llm_playtester spine detector (public/game/story.json vs the running scene) |
| VERIFIED | P1 | PT-20260804-001 | The player can leave the chapter on its first frame, and the objective follows them out | llm_playtester spine detector (public/game/story.json vs the running scene) |
| VERIFIED | P1 | PT-20260804-002 | The player can leave the chapter on its first frame, and the objective follows them out | llm_playtester spine detector (public/game/story.json vs the running scene) |
| VERIFIED | P1 | PT-20260804-004 | Character stuck on wooden platform, cannot reach objective markers | tools/reach_probe.mjs (in the running page) |
| UNVERIFIED | P0 | PT-20260803-006 | End the test session as the game is stuck on a black screen and cannot continue. | tools/reach_probe.mjs (needs a target) |
| UNVERIFIED | P1 | PT-20260803-001 | Walk blocked: the body closed 0 m of an intended 35.57 m, twice at the same place | tools/reach_probe.mjs (NOT RUN) |
| UNVERIFIED | P1 | PT-20260803-003 | Character stuck on terrain geometry | tools/reach_probe.mjs (needs a target) |
| UNVERIFIED | P1 | PT-20260803-004 | Character stuck on terrain near rock formation | tools/reach_probe.mjs (needs a target) |
| UNVERIFIED | P1 | PT-20260803-005 | Screen remains black after leaving Emberbrook | — |
| UNVERIFIED | P1 | PT-20260804-005 | Cannot navigate to character with orange marker on right platform | tools/reach_probe.mjs (FAILED) |
| REFUTED | P0 | PT-20260803-019 | Battle softlocks after defeating the enemy | the run's own run.jsonl (percept.battle + truth.locked, step by step) |
| REFUTED | P1 | PT-20260803-010 | Walk blocked: the body closed 0 m of an intended 5.7 m, twice at the same place | tools/reach_probe.mjs (in the running page) |
| REFUTED | P1 | PT-20260803-011 | Walk blocked: the body closed 0 m of an intended 8.74 m, twice at the same place | tools/reach_probe.mjs (in the running page) |
| REFUTED | P1 | PT-20260803-012 | Character stuck on terrain in sandy clearing | tools/reach_probe.mjs (in the running page) |
| DUPLICATE | P1 | PT-20260803-020 | The player can leave the chapter on its first frame, and the objective follows them out | the spine detector, same as PT-20260803-002 / -008 |
| REFUTED | P1 | PT-20260803-022 | Camera clipped inside foliage obscuring entire screen | tools/reach_probe.mjs (in the running page) |
| REFUTED | P1 | PT-20260803-025 | Camera clipped under map geometry after battle | tools/reach_probe.mjs (in the running page) |
| REFUTED | P1 | PT-20260803-026 | Camera clipped through map geometry | tools/reach_probe.mjs (in the running page) |
| REFUTED | P1 | PT-20260803-028 | Glitched view and out-of-bounds geometry after battle | tools/reach_probe.mjs (in the running page) |
| REFUTED | P1 | PT-20260804-003 | Character cannot navigate up the stairs from the middle walkway | tools/reach_probe.mjs (in the running page) |
| REFUTED | P1 | PT-20260804-006 | Walk blocked: the body closed 0 m of an intended 3.14 m, twice at the same place | tools/reach_probe.mjs (in the running page) |
| REFUTED | P1 | PT-20260804-007 | Character stuck on upper wooden platform at Lock Five | tools/reach_probe.mjs (in the running page) |
| REFUTED | P1 | PT-20260804-008 | Character stuck on wooden platform near cat at Lock Five | tools/reach_probe.mjs (in the running page) |

## Detail

### PT-20260803-014 — Attempted to navigate towards the village, but the game is unresponsive and visually broken.

- **status** VERIFIED (same as PT-20260803-013)
- **severity** P0 · **kind** confusion · **found by** agent

```
same frame one step later; same status
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260803-014` (captured at 42ccd33e)

### PT-20260803-018 — Unable to move character on this map view after trying multiple coordinates across the screen, so I must give up.

- **status** VERIFIED (same as PT-20260803-016)
- **severity** P0 · **kind** confusion · **found by** agent

```
duplicate of -016, same root cause, same fix 10ea7a4
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260803-018` (captured at 5c15518b)

### PT-20260803-002 — The player can leave the chapter on its first frame, and the objective follows them out

- **status** VERIFIED (llm_playtester spine detector (public/game/story.json vs the running scene))
- **severity** P1 · **kind** bug · **found by** spine-detector
- **I was doing** I read the opening narration by pressing the action button, then used the only prompt on screen.
- **I expected** To carry on with the objective the game was showing me.
- **What happened** I ended up somewhere with no way to advance the story, and the objective on screen ("Follow the road north") still refers to where I was. Nothing here can continue the chapter.

```
The body was in "ow-valley" for three consecutive steps while none of the next un-fired beats in story.json lives there. Beats fired at the time: ch1.open. This is a mechanical fact about the game, not a model opinion — there is nothing left to measure. What to DO about it is a design decision.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260803-002` (captured at 0ac851e9)

### PT-20260803-007 — The player can leave the chapter on its first frame, and the objective follows them out

- **status** VERIFIED (llm_playtester spine detector (public/game/story.json vs the running scene))
- **severity** P1 · **kind** bug · **found by** spine-detector
- **I was doing** I read the opening narration by pressing the action button, then used the only prompt on screen.
- **I expected** To carry on with the objective the game was showing me.
- **What happened** I ended up somewhere with no way to advance the story, and the objective on screen ("Follow the road north") still refers to where I was. Nothing here can continue the chapter.

```
The body was in "ow-valley" for three consecutive steps while none of the next un-fired beats in story.json lives there. Beats fired at the time: ch1.open. This is a mechanical fact about the game, not a model opinion — there is nothing left to measure. What to DO about it is a design decision.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260803-007` (captured at 19dcc158)

### PT-20260803-008 — The player can leave the chapter on its first frame, and the objective follows them out

- **status** VERIFIED (llm_playtester spine detector (public/game/story.json vs the running scene))
- **severity** P1 · **kind** bug · **found by** spine-detector
- **I was doing** I read the opening narration by pressing the action button, then used the only prompt on screen.
- **I expected** To carry on with the objective the game was showing me.
- **What happened** I ended up somewhere with no way to advance the story, and the objective on screen ("Follow the road north") still refers to where I was. Nothing here can continue the chapter.

```
The body was in "ow-valley" for three consecutive steps while none of the next un-fired beats in story.json lives there. Beats fired at the time: ch1.open. This is a mechanical fact about the game, not a model opinion — there is nothing left to measure. What to DO about it is a design decision.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260803-008` (captured at 82dfdc13)

### PT-20260803-009 — Camera detached or character missing after battle

- **status** VERIFIED (tools/llm_playtester.mjs run-20260803-195450 (rule 3 close-out))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** Dismissing the victory screen to return to the map.
- **I expected** To see my character on the map where the battle started.
- **What happened** The camera is looking at a cliff and some trees, and my character is nowhere to be seen. There's just floating text saying 'Vesper reached level 2'.

```
Fix ffe507d verified on SIM.occ in round 2. Round 3 closed the circuit: the agent fought a full ow-valley encounter (Reed Nibblers, MEADOW, 2 rounds, Vesper + Lake), won it, dismissed the victory screen, and step 18 is post-battle ow-valley at meanL 110.23, ready and shown to the model, with ZERO reports filed.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260803-009` (captured at 82dfdc13)

### PT-20260803-013 — Game screen rendered as a tiny thumbnail in top-left corner

- **status** VERIFIED (PIL luminance of the written frames + a 21-probe CDP experiment)
- **severity** P1 · **kind** bug · **found by** agent
- **I was doing** Advancing past the dialogue to continue down the road.
- **I expected** The full game scene should be rendered across the screen.
- **What happened** The screen went black and the game view shrunk to a tiny rectangle in the top-left corner, making navigation impossible.

```
step-003/004/008.jpg are 1280x720 at meanL 0.08 with 0.2 pct above black, the game live in a 64x40 corner, while the run log recorded meanL 32.8 ready:true. Harness half fixed at 8b76529 (verdict now taken on the full-size frame). CAUSE OF THE THUMBNAIL STILL UNKNOWN: the clip.scale probe-poisoning hypothesis is REFUTED (21 probes, full capture unchanged at meanL 68.22, bbox 1280x720).
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260803-013` (captured at 42ccd33e)

### PT-20260803-015 — The player can leave the chapter on its first frame, and the objective follows them out

- **status** VERIFIED (ow-valley meta.json spawn vs scenegraph edge pad + tools/playtest/spawn_gate.mjs)
- **severity** P1 · **kind** bug · **found by** spine-detector
- **I was doing** I read the opening narration by pressing the action button, then used the only prompt on screen.
- **I expected** To carry on with the objective the game was showing me.
- **What happened** I ended up somewhere with no way to advance the story, and the objective on screen ("Follow the valley road down to Dellhollow") still refers to where I was. Nothing here can continue the chapter.

```
bundle spawn was 0.072 m from the centre of ow-valley>emb-cine@emberbrook-gate (r 3.2); 2 runs of 2 took the portal home on step 2. Fixed 5c15518: 5.054 m, spawn_gate PASS. Control at the old spawn also found 6/24 headings blocked by emberbrook_5.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260803-015` (captured at b3bf841a)

### PT-20260803-016 — Cannot move or interact with the valley map screen

- **status** VERIFIED (the playtester picker (INSTALL_MOTOR) on a 5x5 screen grid, real Chrome)
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I'm trying to click on the road and the red markers to follow the valley road to Dellhollow.
- **I expected** I expected my character to move along the path or for a level to load.
- **What happened** Nothing happens when I click anywhere on the map. I seem to be stuck on this overview screen.

```
ow-valley kept the region GLB overview camera at [-4,236,212]: 0/25 screen points hit any surface. play3d line 30 RT regex lacked ow- while line 48 OWCAM had it; the follow camera only exists inside if(RT). Fixed 10ea7a4: 25/25 hit, 5/25 on the walk network.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260803-016` (captured at 5c15518b)

### PT-20260803-017 — Valley map ground is non-walkable

- **status** VERIFIED (same as PT-20260803-016)
- **severity** P1 · **kind** bug · **found by** agent
- **I was doing** Trying to click on visible ground and dirt paths to walk down to Dellhollow.
- **I expected** Clicking on the dirt paths or clearings near the red objective markers should move the character.
- **What happened** All movement coordinates across multiple attempts return 'not ground you can walk to'.

```
duplicate of -016, same root cause, same fix 10ea7a4
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260803-017` (captured at 5c15518b)

### PT-20260803-021 — The player can leave the chapter on its first frame, and the objective follows them out

- **status** VERIFIED (llm_playtester spine detector (public/game/story.json vs the running scene))
- **severity** P1 · **kind** bug · **found by** spine-detector
- **I was doing** I read the opening narration by pressing the action button, then used the only prompt on screen.
- **I expected** To carry on with the objective the game was showing me.
- **What happened** I ended up somewhere with no way to advance the story, and the objective on screen ("Follow the valley road down to Dellhollow") still refers to where I was. Nothing here can continue the chapter.

```
The body was in "emb-cine" for three consecutive steps while none of the next un-fired beats in story.json lives there. Beats fired at the time: ch1.open, ch1.waystone, ch1.reveal, ch1.rowan, ch1.lake.handoff, ch1.lake.wake, ch1.lake.hearth, ch1.lake.lamp, ch1.meet, ch1.lamps, ch1.hush, ch1.see.poppy, ch1.see.mara, ch1.see.finn, ch1.see.mochi, ch1.pact, ch1.sigils, ch1.sendoff, ch1.done. This is a mechanical fact about the game, not a model opinion — there is nothing left to measure. What to DO about it is a design decision.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260803-021` (captured at 81e4a624)

### PT-20260803-023 — The player can leave the chapter on its first frame, and the objective follows them out

- **status** VERIFIED (llm_playtester spine detector (public/game/story.json vs the running scene))
- **severity** P1 · **kind** bug · **found by** spine-detector
- **I was doing** I read the opening narration by pressing the action button, then used the only prompt on screen.
- **I expected** To carry on with the objective the game was showing me.
- **What happened** I ended up somewhere with no way to advance the story, and the objective on screen ("Follow the valley road down to Dellhollow") still refers to where I was. Nothing here can continue the chapter.

```
The body was in "emb-cine" for three consecutive steps while none of the next un-fired beats in story.json lives there. Beats fired at the time: ch1.open, ch1.waystone, ch1.reveal, ch1.rowan, ch1.lake.handoff, ch1.lake.wake, ch1.lake.hearth, ch1.lake.lamp, ch1.meet, ch1.lamps, ch1.hush, ch1.see.poppy, ch1.see.mara, ch1.see.finn, ch1.see.mochi, ch1.pact, ch1.sigils, ch1.sendoff, ch1.done. This is a mechanical fact about the game, not a model opinion — there is nothing left to measure. What to DO about it is a design decision.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260803-023` (captured at e35a6573)

### PT-20260803-024 — The player can leave the chapter on its first frame, and the objective follows them out

- **status** VERIFIED (llm_playtester spine detector (public/game/story.json vs the running scene))
- **severity** P1 · **kind** bug · **found by** spine-detector
- **I was doing** I read the opening narration by pressing the action button, then used the only prompt on screen.
- **I expected** To carry on with the objective the game was showing me.
- **What happened** I ended up somewhere with no way to advance the story, and the objective on screen ("Down into the hollow — find whoever runs the locks") still refers to where I was. Nothing here can continue the chapter.

```
The body was in "ow-valley" for three consecutive steps while none of the next un-fired beats in story.json lives there. Beats fired at the time: ch1.open, ch1.waystone, ch1.reveal, ch1.rowan, ch1.lake.handoff, ch1.lake.wake, ch1.lake.hearth, ch1.lake.lamp, ch1.meet, ch1.lamps, ch1.hush, ch1.see.poppy, ch1.see.mara, ch1.see.finn, ch1.see.mochi, ch1.pact, ch1.sigils, ch1.sendoff, ch1.done, ch2.road. This is a mechanical fact about the game, not a model opinion — there is nothing left to measure. What to DO about it is a design decision.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260803-024` (captured at cb203c19)

### PT-20260803-027 — The player can leave the chapter on its first frame, and the objective follows them out

- **status** VERIFIED (llm_playtester spine detector (public/game/story.json vs the running scene))
- **severity** P1 · **kind** bug · **found by** spine-detector
- **I was doing** I read the opening narration by pressing the action button, then used the only prompt on screen.
- **I expected** To carry on with the objective the game was showing me.
- **What happened** I ended up somewhere with no way to advance the story, and the objective on screen ("Through the Dellhollow gate — find whoever runs the locks") still refers to where I was. Nothing here can continue the chapter.

```
The body was in "ow-valley" for three consecutive steps while none of the next un-fired beats in story.json lives there. Beats fired at the time: ch1.open, ch1.waystone, ch1.reveal, ch1.rowan, ch1.lake.handoff, ch1.lake.wake, ch1.lake.hearth, ch1.lake.lamp, ch1.meet, ch1.lamps, ch1.hush, ch1.see.poppy, ch1.see.mara, ch1.see.finn, ch1.see.mochi, ch1.pact, ch1.sigils, ch1.sendoff, ch1.done, ch2.road. This is a mechanical fact about the game, not a model opinion — there is nothing left to measure. What to DO about it is a design decision.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260803-027` (captured at 2b068735)

### PT-20260803-029 — The player can leave the chapter on its first frame, and the objective follows them out

- **status** VERIFIED (llm_playtester spine detector (public/game/story.json vs the running scene))
- **severity** P1 · **kind** bug · **found by** spine-detector
- **I was doing** I read the opening narration by pressing the action button, then used the only prompt on screen.
- **I expected** To carry on with the objective the game was showing me.
- **What happened** I ended up somewhere with no way to advance the story, and the objective on screen ("Find whoever runs the locks — the lockhead, above Lock Five") still refers to where I was. Nothing here can continue the chapter.

```
The body was in "del-inn-int" for three consecutive steps while none of the next un-fired beats in story.json lives there. Beats fired at the time: ch1.open, ch1.waystone, ch1.reveal, ch1.rowan, ch1.lake.handoff, ch1.lake.wake, ch1.lake.hearth, ch1.lake.lamp, ch1.meet, ch1.lamps, ch1.hush, ch1.see.poppy, ch1.see.mara, ch1.see.finn, ch1.see.mochi, ch1.pact, ch1.sigils, ch1.sendoff, ch1.done, ch2.road, ch2.arrive. This is a mechanical fact about the game, not a model opinion — there is nothing left to measure. What to DO about it is a design decision.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260803-029` (captured at 80eedbd7)

### PT-20260804-001 — The player can leave the chapter on its first frame, and the objective follows them out

- **status** VERIFIED (llm_playtester spine detector (public/game/story.json vs the running scene))
- **severity** P1 · **kind** bug · **found by** spine-detector
- **I was doing** I read the opening narration by pressing the action button, then used the only prompt on screen.
- **I expected** To carry on with the objective the game was showing me.
- **What happened** I ended up somewhere with no way to advance the story, and the objective on screen ("Down to the lock apron — the girl who was in the water") still refers to where I was. Nothing here can continue the chapter.

```
The body was in "del-cookhouse-int" for three consecutive steps while none of the next un-fired beats in story.json lives there. Beats fired at the time: ch1.open, ch1.waystone, ch1.reveal, ch1.rowan, ch1.lake.handoff, ch1.lake.wake, ch1.lake.hearth, ch1.lake.lamp, ch1.meet, ch1.lamps, ch1.hush, ch1.see.poppy, ch1.see.mara, ch1.see.finn, ch1.see.mochi, ch1.pact, ch1.sigils, ch1.sendoff, ch1.done, ch2.road, ch2.arrive, ch2.jam. This is a mechanical fact about the game, not a model opinion — there is nothing left to measure. What to DO about it is a design decision.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260804-001` (captured at 03af0da5)

### PT-20260804-002 — The player can leave the chapter on its first frame, and the objective follows them out

- **status** VERIFIED (llm_playtester spine detector (public/game/story.json vs the running scene))
- **severity** P1 · **kind** bug · **found by** spine-detector
- **I was doing** I read the opening narration by pressing the action button, then used the only prompt on screen.
- **I expected** To carry on with the objective the game was showing me.
- **What happened** I ended up somewhere with no way to advance the story, and the objective on screen ("Down to the lock apron — the girl who was in the water") still refers to where I was. Nothing here can continue the chapter.

```
The body was in "del-cookhouse-int" for three consecutive steps while none of the next un-fired beats in story.json lives there. Beats fired at the time: ch1.open, ch1.waystone, ch1.reveal, ch1.rowan, ch1.lake.handoff, ch1.lake.wake, ch1.lake.hearth, ch1.lake.lamp, ch1.meet, ch1.lamps, ch1.hush, ch1.see.poppy, ch1.see.mara, ch1.see.finn, ch1.see.mochi, ch1.pact, ch1.sigils, ch1.sendoff, ch1.done, ch2.road, ch2.arrive, ch2.jam. This is a mechanical fact about the game, not a model opinion — there is nothing left to measure. What to DO about it is a design decision.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260804-002` (captured at 743c2956)

### PT-20260804-004 — Character stuck on wooden platform, cannot reach objective markers

- **status** VERIFIED (tools/reach_probe.mjs (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I was trying to walk to the red objective markers to interact with the head-gate winches.
- **I expected** My character should walk to the red markers when I click on them.
- **What happened** My character seems stuck on the small wooden platform and won't move to either of the red markers on the left or right.

```
where I stood -> where I pointed: UNREACHABLE — the TARGET anchor [60.47,16.58,-3.53] is not standable in the running game, and the nearest ground the player can reach from [56.47,17.4,-7.84] is 6.0 m away (3411 cells filled). No walk can ever trigger this beat.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260804-004` (captured at 23336cbf)

### PT-20260803-006 — End the test session as the game is stuck on a black screen and cannot continue.

- **status** UNVERIFIED (tools/reach_probe.mjs (needs a target))
- **severity** P0 · **kind** confusion · **found by** agent

```
a blocked-path claim with no recorded destination. Re-run it with --repro so the walk executor records the from/to pair, then triage again.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260803-006` (captured at 5bc18c8b)

### PT-20260803-001 — Walk blocked: the body closed 0 m of an intended 35.57 m, twice at the same place

- **status** UNVERIFIED (tools/reach_probe.mjs (NOT RUN))
- **severity** P1 · **kind** blocker · **found by** walk-executor
- **I was doing** I tried to walk to a point on screen at [0.50, 0.40]; my goal was "Follow the road north by walking along the stone path past the monument.".
- **I expected** To walk about 35.57 m and arrive there.
- **What happened** The character moved 0 m and stopped 35.57 m short — twice in this run. Something is in the way, or that ground is not connected to where I was standing.

```
the reachability probe needs a running server: re-run this with --port=3000.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260803-001` (captured at 7dc81dad)

### PT-20260803-003 — Character stuck on terrain geometry

- **status** UNVERIFIED (tools/reach_probe.mjs (needs a target))
- **severity** P1 · **kind** bug · **found by** agent
- **I was doing** Trying to walk away from the brown rock face on the grassy hill
- **I expected** Character should navigate around collision or walk downhill when ground is clicked
- **What happened** Character is completely immobile and closed 0 meters across three movement attempts

```
a blocked-path claim with no recorded destination. Re-run it with --repro so the walk executor records the from/to pair, then triage again.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260803-003` (captured at 0ac851e9)

### PT-20260803-004 — Character stuck on terrain near rock formation

- **status** UNVERIFIED (tools/reach_probe.mjs (needs a target))
- **severity** P1 · **kind** blocker · **found by** stuck-interview
- **I was doing** I was trying to walk around the rock formation to find the road north.
- **I expected** I expected my character to walk down the grassy slope when I clicked.
- **What happened** My character is completely stuck in place and won't move in any direction, no matter where I click.

```
a blocked-path claim with no recorded destination. Re-run it with --repro so the walk executor records the from/to pair, then triage again.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260803-004` (captured at 0ac851e9)

### PT-20260803-005 — Screen remains black after leaving Emberbrook

- **status** UNVERIFIED (nothing measured yet)
- **severity** P1 · **kind** blocker · **found by** agent
- **I was doing** Leaving Emberbrook to follow the road north
- **I expected** The new area to load and be displayed on screen
- **What happened** The screen turned completely black and did not load the new area after multiple waits

```
no instrument in this repo answers this claim — it is about taste, audio, or a comparison the agent could not have made. A human judges this one, or it is dropped.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260803-005` (captured at 5bc18c8b)

### PT-20260804-005 — Cannot navigate to character with orange marker on right platform

- **status** UNVERIFIED (tools/reach_probe.mjs (FAILED))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** Trying to walk across the wooden walkway to the character with the orange marker on the right.
- **I expected** My character would walk over to them.
- **What happened** My character gets stuck and stops moving before reaching the platform, even though the path looks clear.

```
the probe itself failed: Execution context was destroyed.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260804-005` (captured at fc47150f)

### PT-20260803-019 — Battle softlocks after defeating the enemy

- **status** REFUTED (the run's own run.jsonl (percept.battle + truth.locked, step by step))
- **severity** P0 · **kind** blocker · **found by** stuck-interview
- **I was doing** I was waiting for the battle to end after Lake's attack defeated the only enemy, Duskpad.
- **I expected** The battle should end and return me to the map or show a victory screen.
- **What happened** The message says 'Duskpad is defeated!' and the enemy model is gone, but the battle doesn't end. The command menu is greyed out and I can't do anything else.

```
The battle ENDED, four steps before this report was written. Straight out of run-20260803-203813/run.jsonl: step 12 percept.battle.log is 'Duskpad is defeated!' with foes []; steps 13-15 are the Victory card (meanL 36.7, UILOCK held); step 16 has no battle, UILOCK released, and the agent walks on for another 29 steps. Nothing softlocked. THIS WAS THE HARNESS: the stuck detector measures metres over a six-step window, and a battle is exactly a window in which zero metres is correct play. It fired at step 12 because the body had not moved since step 7 — the battle's first step — and the interview it paid for produced this P0 against a fight that had already been won. Fixed in episode.mjs: a step where UILOCK is held or a battle/dialogue/card is on screen is dropped from the window rather than counted. A real modal freeze is still caught by the frame gate's separate `frozen` check.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260803-019` (captured at 22db4473)

### PT-20260803-010 — Walk blocked: the body closed 0 m of an intended 5.7 m, twice at the same place

- **status** REFUTED (tools/reach_probe.mjs (in the running page))
- **severity** P1 · **kind** blocker · **found by** walk-executor
- **I was doing** I tried to walk to a point on screen at [0.45, 0.60]; my goal was "Follow the road north into the village.".
- **I expected** To walk about 5.7 m and arrive there.
- **What happened** The character moved 0 m and stopped 5.7 m short — twice in this run. Something is in the way, or that ground is not connected to where I was standing.

```
where I stood -> where I pointed: reachable (5.7 m apart, 339 cells filled on foot)
  The ground IS connected, so the walk was not blocked by the world. The likely causes are the executor giving up (a narrow gap, a step it could not take at its 150 ms burst) or a body-box snag that the cell fill does not model — confirm with tools/walk_bodygate.mjs.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260803-010` (captured at 82dfdc13)

### PT-20260803-011 — Walk blocked: the body closed 0 m of an intended 8.74 m, twice at the same place

- **status** REFUTED (tools/reach_probe.mjs (in the running page))
- **severity** P1 · **kind** blocker · **found by** walk-executor
- **I was doing** I tried to walk to a point on screen at [0.50, 0.70]; my goal was "Walk down to the open ground connecting to the village dirt road, then follow it north.".
- **I expected** To walk about 8.74 m and arrive there.
- **What happened** The character moved 0 m and stopped 8.74 m short — twice in this run. Something is in the way, or that ground is not connected to where I was standing.

```
where I stood -> where I pointed: reachable (8.7 m apart, 1367 cells filled on foot)
  The ground IS connected, so the walk was not blocked by the world. The likely causes are the executor giving up (a narrow gap, a step it could not take at its 150 ms burst) or a body-box snag that the cell fill does not model — confirm with tools/walk_bodygate.mjs.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260803-011` (captured at 82dfdc13)

### PT-20260803-012 — Character stuck on terrain in sandy clearing

- **status** REFUTED (tools/reach_probe.mjs (in the running page))
- **severity** P1 · **kind** blocker · **found by** agent
- **I was doing** Trying to navigate towards the road leading north into the village.
- **I expected** Vesper should move across the terrain towards the clicked location.
- **What happened** Four consecutive movement attempts in different directions (south, west, southwest) all failed to move Vesper at all (0m closed).

```
where I stood -> where I pointed: reachable (8.7 m apart, 1367 cells filled on foot)
  The ground IS connected, so the walk was not blocked by the world. The likely causes are the executor giving up (a narrow gap, a step it could not take at its 150 ms burst) or a body-box snag that the cell fill does not model — confirm with tools/walk_bodygate.mjs.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260803-012` (captured at 82dfdc13)

### PT-20260803-020 — The player can leave the chapter on its first frame, and the objective follows them out

- **status** DUPLICATE (the spine detector, same as PT-20260803-002 / -008)
- **severity** P1 · **kind** bug · **found by** spine-detector
- **I was doing** I read the opening narration by pressing the action button, then used the only prompt on screen.
- **I expected** To carry on with the objective the game was showing me.
- **What happened** I ended up somewhere with no way to advance the story, and the objective on screen ("Follow the valley road down to Dellhollow") still refers to where I was. Nothing here can continue the chapter.

```
The third filing of the SAME design question already logged as PT-20260803-002 (round 0) and -008 (round 1): the player can leave the chapter and the objective follows them out. The remedy is a user design call, and a separate lane is implementing their ruling. Carried, not re-triaged.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260803-020` (captured at 22db4473)

### PT-20260803-022 — Camera clipped inside foliage obscuring entire screen

- **status** REFUTED (tools/reach_probe.mjs (in the running page))
- **severity** P1 · **kind** bug · **found by** agent
- **I was doing** Following the path down the valley
- **I expected** A clear view of the character and the path ahead
- **What happened** The camera is stuck inside foreground leaf geometry, completely hiding the player character and surroundings

```
where I stood -> where I pointed: reachable (16.2 m apart, 1661 cells filled on foot)
  The ground IS connected, so the walk was not blocked by the world. The likely causes are the executor giving up (a narrow gap, a step it could not take at its 150 ms burst) or a body-box snag that the cell fill does not model — confirm with tools/walk_bodygate.mjs.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260803-022` (captured at e35a6573)

### PT-20260803-025 — Camera clipped under map geometry after battle

- **status** REFUTED (tools/reach_probe.mjs (in the running page))
- **severity** P1 · **kind** bug · **found by** agent
- **I was doing** Dismissing the victory screen to return to the level
- **I expected** To return to the walkable level path where the character was before combat
- **What happened** The player and camera ended up underneath the level geometry, looking up at the underside of rock models and floating collision boxes.

```
where I stood -> where I pointed: reachable (16.0 m apart, 3363 cells filled on foot)
  The ground IS connected, so the walk was not blocked by the world. The likely causes are the executor giving up (a narrow gap, a step it could not take at its 150 ms burst) or a body-box snag that the cell fill does not model — confirm with tools/walk_bodygate.mjs.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260803-025` (captured at cb203c19)

### PT-20260803-026 — Camera clipped through map geometry

- **status** REFUTED (tools/reach_probe.mjs (in the running page))
- **severity** P1 · **kind** bug · **found by** agent
- **I was doing** Walking down the wooden walkway in the canyon hollow.
- **I expected** To follow the pathway smoothly with the camera remaining focused on the character and environment.
- **What happened** The view clipped under the terrain geometry, showing an out-of-bounds sky void and dark cliff meshes.

```
where I stood -> where I pointed: reachable (10.6 m apart, 1138 cells filled on foot)
  The ground IS connected, so the walk was not blocked by the world. The likely causes are the executor giving up (a narrow gap, a step it could not take at its 150 ms burst) or a body-box snag that the cell fill does not model — confirm with tools/walk_bodygate.mjs.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260803-026` (captured at cb203c19)

### PT-20260803-028 — Glitched view and out-of-bounds geometry after battle

- **status** REFUTED (tools/reach_probe.mjs (in the running page))
- **severity** P1 · **kind** bug · **found by** agent
- **I was doing** Returning to exploration after winning a battle
- **I expected** I expected to return to the game world path normally
- **What happened** The camera or character ended up under/outside the environment geometry, showing floating collision blocks and open void

```
where I stood -> where I pointed: reachable (10.9 m apart, 1471 cells filled on foot)
  The ground IS connected, so the walk was not blocked by the world. The likely causes are the executor giving up (a narrow gap, a step it could not take at its 150 ms burst) or a body-box snag that the cell fill does not model — confirm with tools/walk_bodygate.mjs.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260803-028` (captured at 2b068735)

### PT-20260804-003 — Character cannot navigate up the stairs from the middle walkway

- **status** REFUTED (tools/reach_probe.mjs (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I was trying to climb the stairs from the middle platform to get to the upper levels for the objective.
- **I expected** I expected my character to walk up the stairs when I clicked on them or the path above.
- **What happened** My character just stood there and wouldn't go up the stairs, no matter where I clicked around them. I seem to be stuck on this level.

```
where I stood -> where I pointed: reachable (4.7 m apart, 325 cells filled, via 2 in-scene edges)
  The ground IS connected, so the walk was not blocked by the world. The likely causes are the executor giving up (a narrow gap, a step it could not take at its 150 ms burst) or a body-box snag that the cell fill does not model — confirm with tools/walk_bodygate.mjs.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260804-003` (captured at 23336cbf)

### PT-20260804-006 — Walk blocked: the body closed 0 m of an intended 3.14 m, twice at the same place

- **status** REFUTED (tools/reach_probe.mjs (in the running page))
- **severity** P1 · **kind** blocker · **found by** walk-executor
- **I was doing** I tried to walk to a point on screen at [0.61, 0.72]; my goal was "Walk down the stairs and around through the lower path to reach the head-gate winches.".
- **I expected** To walk about 3.14 m and arrive there.
- **What happened** The character moved 0 m and stopped 3.14 m short — twice in this run. All five headings were pushed (5 bursts at ~158 ms each) and none of them moved the body, so this is the world refusing rather than the harness running out of time. Something is in the way, or that ground is not connected to where I was standing.

```
where I stood -> where I pointed: reachable (3.1 m apart, 86 cells filled, via 1 in-scene edge)
  The ground IS connected, so the walk was not blocked by the world. The likely causes are the executor giving up (a narrow gap, a step it could not take at its 150 ms burst) or a body-box snag that the cell fill does not model — confirm with tools/walk_bodygate.mjs.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260804-006` (captured at fc47150f)

### PT-20260804-007 — Character stuck on upper wooden platform at Lock Five

- **status** REFUTED (tools/reach_probe.mjs (in the running page))
- **severity** P1 · **kind** bug · **found by** agent
- **I was doing** Trying to move toward the head-gate winches or down the stairs from the upper wooden platform
- **I expected** Vesper should be able to walk across the platform, interact with the winch, or walk back down the stairs
- **What happened** Vesper is completely stuck on the platform next to the cat; four consecutive goto commands in different directions closed 0m.

```
where I stood -> where I pointed: reachable (1.6 m apart, 15 cells filled on foot)
  The ground IS connected, so the walk was not blocked by the world. The likely causes are the executor giving up (a narrow gap, a step it could not take at its 150 ms burst) or a body-box snag that the cell fill does not model — confirm with tools/walk_bodygate.mjs.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260804-007` (captured at fc47150f)

### PT-20260804-008 — Character stuck on wooden platform near cat at Lock Five

- **status** REFUTED (tools/reach_probe.mjs (in the running page))
- **severity** P1 · **kind** blocker · **found by** stuck-interview
- **I was doing** I was trying to walk down the stairs or across the platform to reach the head-gate winches.
- **I expected** I expected my character to move down the stairs or across the platform when I clicked.
- **What happened** My character is completely stuck on the platform next to the cat and won't move anywhere.

```
where I stood -> where I pointed: reachable (1.6 m apart, 15 cells filled on foot)
  The ground IS connected, so the walk was not blocked by the world. The likely causes are the executor giving up (a narrow gap, a step it could not take at its 150 ms burst) or a body-box snag that the cell fill does not model — confirm with tools/walk_bodygate.mjs.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260804-008` (captured at fc47150f)
