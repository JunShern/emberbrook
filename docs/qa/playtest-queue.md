# Emberbrook — LLM playtest queue

Generated 2026-08-03T01:35:48.610Z by `tools/playtest_triage.mjs`. Source of truth: `docs/qa/playtest/queue.json`.

**An UNVERIFIED complaint is a lead, never a ticket.** Filed by an LLM playing the game through
screenshots and real key events; measured by instruments before anybody builds. REFUTED entries are
as informative as VERIFIED ones — the agent sees one still frame with no parallax, so it is biased
toward "I cannot find it", and that false-positive rate is this tool's calibration.

| status | sev | id | title | measured by |
|---|---|---|---|---|
| VERIFIED | P1 | PT-20260803-002 | The player can leave the chapter on its first frame, and the objective follows them out | llm_playtester spine detector (public/game/story.json vs the running scene) |
| UNVERIFIED | P1 | PT-20260803-001 | Walk blocked: the body closed 0 m of an intended 35.57 m, twice at the same place | tools/reach_probe.mjs (NOT RUN) |
| UNVERIFIED | P1 | PT-20260803-003 | Character stuck on terrain geometry | tools/reach_probe.mjs (needs a target) |
| UNVERIFIED | P1 | PT-20260803-004 | Character stuck on terrain near rock formation | tools/reach_probe.mjs (needs a target) |

## Detail

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
