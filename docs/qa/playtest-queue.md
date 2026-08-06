# Emberbrook — LLM playtest queue

Generated 2026-08-06T06:14:21.257Z by `tools/playtest_triage.mjs`. Source of truth: `docs/qa/playtest/queue.json`.

**An UNVERIFIED complaint is a lead, never a ticket.** Filed by an LLM playing the game through
screenshots and real key events; measured by instruments before anybody builds. REFUTED entries are
as informative as VERIFIED ones — the agent sees one still frame with no parallax, so it is biased
toward "I cannot find it", and that false-positive rate is this tool's calibration.

| status | sev | id | title | measured by |
|---|---|---|---|---|
| VERIFIED | P0 | PT-20260803-014 | Attempted to navigate towards the village, but the game is unresponsive and visually broken. | same as PT-20260803-013 |
| VERIFIED | P0 | PT-20260803-018 | Unable to move character on this map view after trying multiple coordinates across the screen, so I must give up. | same as PT-20260803-016 |
| REFUTED against the game · VERIFIED against the harness | P0 | PT-20260805-036 | Character stuck on terrain geometry on middle platform | tools/_court_probe.mjs --way/--at + tools/playtest/seen_probe.mjs + tools/playtest/wayfind_probe.mjs |
| VERIFIED | P0 | PT-20260805-048 | Cannot enter Keepers' Cottage despite standing on the waypoint marker | tools/reach_probe.mjs (in the running page) |
| VERIFIED | P0 | PT-20260806-003 | Stuck on plank bridge geometry trying to reach Lock Five exit | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P0 | PT-20260806-027 | Cannot transition through Lock Five exit | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P0 | PT-20260806-031 | Scene transition 'Lock Five' does not trigger when reached | tools/reach_probe.mjs + SIM.move (in the running page) |
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
| VERIFIED | P1 | PT-20260805-001 | Character stuck on wooden platform, unable to move left or right | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260805-004 | Character stuck on Lock Five central deck geometry | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260805-005 | Cannot interact with head-gate winches to progress objective | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260805-011 | Cannot interact with Mara at the Heartlight | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260805-012 | Character gets stuck trying to navigate around the Heartlight well | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260805-013 | The player can leave the chapter on its first frame, and the objective follows them out | llm_playtester spine detector (public/game/story.json vs the running scene) |
| VERIFIED | P1 | PT-20260805-019 | Cannot figure out how to reach 'The Lockhead' marker from the upper balcony | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260805-020 | Quest NPC Dellhollow gives generic dialogue instead of advancing quest | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260805-022 | Character gets stuck on stairs trying to reach Lock Five transition | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260805-023 | Navigation fails when trying to move around the lower dock area | tools/reach_probe.mjs (in the running page) |
| VERIFIED | P1 | PT-20260805-024 | Player gets stuck under circular deck, unable to navigate to girl on lock apron | tools/reach_probe.mjs (in the running page) |
| VERIFIED | P1 | PT-20260805-025 | Character stuck in geometry under circular platform | tools/reach_probe.mjs (in the running page) |
| VERIFIED | P1 | PT-20260805-027 | Cannot move character towards Dellhollow in the cookhouse | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260805-028 | Character stuck in geometry near cookhouse table | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260805-029 | Player gets stuck trying to walk down stairs to Lock Five | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260805-030 | Walk blocked: the body closed 0 m of an intended 4.34 m, twice at the same place | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260805-031 | Walk blocked: the body closed 0 m of an intended 3.41 m, twice at the same place | tools/reach_probe.mjs + SIM.move (in the running page) |
| REFUTED against the game · VERIFIED against the harness | P1 | PT-20260805-035 | Character stuck on middle cliffside path | tools/_court_probe.mjs --way/--at + tools/playtest/seen_probe.mjs + tools/playtest/wayfind_probe.mjs |
| REFUTED (round 24, recorded here in round 25) | P1 | PT-20260805-037 | Character gets stuck navigating down stairs towards Lock Five | tools/playtest/wayfind_probe.mjs --from=ch2.supper --target=cottage (docs/qa/playtest/wayfind-r24) |
| REFUTED as filed (round 24, recorded here in round 25) | P1 | PT-20260805-038 | Character stuck on walkway near lantern, cannot reach Keepers' Cottage | tools/_court_probe.mjs --comp/--grid + tools/reach_probe.mjs |
| VERIFIED | P1 | PT-20260805-043 | Player falls through upper deck walkway collision geometry | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260806-007 | Taking 'The Lockhead' exit loops back to start position | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260806-008 | Stuck in screen transition loop following Lockhead objective path | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260806-009 | Quest router loops infinitely between screen transitions | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260806-010 | Infinite screen transition loop following Lockhead objective marker | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260806-013 | The player can leave the chapter on its first frame, and the objective follows them out | llm_playtester spine detector (public/game/story.json vs the running scene) |
| VERIFIED | P1 | PT-20260806-015 | Cannot enter Keepers' Cottage; transition marker not working | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260806-016 | Cannot reach Keepers' Cottage transition point | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260806-017 | Cannot enter Keepers' Cottage, character gets stuck on walkway | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260806-018 | Pathfinding stuck trying to reach The Lockhead marker | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260806-019 | Stuck on upper walkway, cannot reach 'The Lockhead' marker below | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260806-020 | Player stuck on porch/roof above 'The Lockhead' marker, cannot path down | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260806-021 | Unable to pathfind to 'The Lockhead' entrance from upper porch | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260806-022 | Pathfinding stuck on upper deck railing when targeting marker below | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260806-023 | Pathfinding fails when trying to reach a marker directly below the player | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260806-024 | Pathfinding to The Lockhead is blocked from the upper deck | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260806-025 | Pathfinding fails to reach 'The Lockhead' marker from the upper roof/path | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260806-028 | Cannot interact with 'Lock Five' exit marker from the walkway directly above it | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260806-032 | Lock Five area transition fails to trigger when standing on marker | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260806-033 | Character stuck on roof above Lock Five marker | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260806-034 | Character gets stuck on walkway above 'Lock Five' transition marker | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260806-037 | Character stuck on upper platform, cannot navigate to Lock Five waypoint | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260806-039 | Walk blocked: the body closed 0 m of an intended 6.43 m, twice at the same place | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260806-040 | Character stuck on elevated walkway, unable to pathfind to Lock Five exit | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260806-041 | Character stuck on elevated walkway pathfinding to Lock Five | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260806-042 | Pathfinding to Lock Five exit marker is stuck | tools/reach_probe.mjs + SIM.move (in the running page) |
| UNVERIFIED | P0 | PT-20260803-006 | End the test session as the game is stuck on a black screen and cannot continue. | tools/reach_probe.mjs (needs a target) |
| UNVERIFIED | P1 | PT-20260803-001 | Walk blocked: the body closed 0 m of an intended 35.57 m, twice at the same place | tools/reach_probe.mjs (NOT RUN) |
| UNVERIFIED | P1 | PT-20260803-003 | Character stuck on terrain geometry | tools/reach_probe.mjs (needs a target) |
| UNVERIFIED | P1 | PT-20260803-004 | Character stuck on terrain near rock formation | tools/reach_probe.mjs (needs a target) |
| UNVERIFIED | P1 | PT-20260803-005 | Screen remains black after leaving Emberbrook | — |
| UNVERIFIED | P1 | PT-20260804-005 | Cannot navigate to character with orange marker on right platform | tools/reach_probe.mjs (FAILED) |
| UNVERIFIED | P1 | PT-20260804-010 | I spent 12 turns inside del-inn-int and nothing in the room answered me | — |
| UNVERIFIED | P1 | PT-20260805-039 | Stuck on lower dock, cannot climb stairs to Keepers' Cottage | tools/reach_probe.mjs (NOT RUN) |
| REFUTED | P0 | PT-20260803-019 | Battle softlocks after defeating the enemy | the run's own run.jsonl (percept.battle + truth.locked, step by step) |
| REFUTED | P0 | PT-20260804-011 | Cannot walk up the path to the head-gate winches | tools/reach_probe.mjs (in the running page) |
| REFUTED | P0 | PT-20260805-014 | Cannot interact with the NPC at 'The Lockhead' marker | tools/reach_probe.mjs + SIM.move (in the running page) |
| REFUTED | P0 | PT-20260805-021 | Cannot interact with 'The Lockhead' NPC to advance objective | tools/reach_probe.mjs + SIM.move (in the running page) |
| REFUTED | P0 | PT-20260805-061 | Cannot trigger 'The Lockhead' area transition marker | tools/reach_probe.mjs + SIM.move (in the running page) |
| REFUTED | P0 | PT-20260806-012 | Character stuck on ledge, unable to move to follow objective | tools/reach_probe.mjs + SIM.move (in the running page) |
| REFUTED | P0 | PT-20260806-035 | Standing on 'Lock Five' transition marker does not trigger area change | tools/reach_probe.mjs + SIM.move (in the running page) |
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
| REFUTED | P1 | PT-20260804-012 | Cannot walk up the path to the head-gate winches at Lock Five | tools/reach_probe.mjs (in the running page) |
| REFUTED | P1 | PT-20260804-013 | Cannot reach red quest markers for head-gate winches | tools/reach_probe.mjs (in the running page) |
| REFUTED | P1 | PT-20260804-014 | Character stuck in collision on Lock Five upper platform | tools/reach_probe.mjs (in the running page) |
| REFUTED | P1 | PT-20260804-015 | Duplicate word 'the' in cook interaction prompt | tools/reach_probe.mjs (in the running page) |
| REFUTED | P1 | PT-20260805-002 | Character stuck on narrow wooden plank bridge | tools/reach_probe.mjs (in the running page) |
| REFUTED | P1 | PT-20260805-003 | Character stuck in place on central wooden platform | tools/reach_probe.mjs (in the running page) |
| REFUTED | P1 | PT-20260805-006 | Cannot walk to the head-gate winches at Lock Five | tools/reach_probe.mjs + SIM.move (in the running page) |
| REFUTED | P1 | PT-20260805-007 | Cannot interact with the two figures on the path | tools/reach_probe.mjs + SIM.move (in the running page) |
| REFUTED | P1 | PT-20260805-008 | Cannot interact with Poppy at her stall | tools/reach_probe.mjs + SIM.move (in the running page) |
| REFUTED | P1 | PT-20260805-009 | Overlapping interaction prompts for 'Leave Item Shop' and 'Talk to shopkeeper' | tools/reach_probe.mjs + SIM.move (in the running page) |
| REFUTED | P1 | PT-20260805-010 | Old Gate exit loops back to Village Square | tools/reach_probe.mjs + SIM.move (in the running page) |
| REFUTED | P1 | PT-20260805-015 | Reached the red objective marker at The Lockhead but nothing happens | tools/reach_probe.mjs + SIM.move (in the running page) |
| REFUTED | P1 | PT-20260805-017 | Transition trigger for 'Shelf street' blocks access to 'The Lockhead' objective | tools/reach_probe.mjs + SIM.move (in the running page) |
| REFUTED | P1 | PT-20260805-018 | Cannot walk to 'The Lockhead' NPC, ground marked as not walkable | tools/reach_probe.mjs + SIM.move (in the running page) |
| REFUTED | P1 | PT-20260805-026 | Character stuck behind wooden pillars under circular deck | tools/reach_probe.mjs + SIM.move (in the running page) |
| REFUTED against the game · VERIFIED against the harness | P1 | PT-20260805-032 | Player gets stuck on geometry at far right of upper wooden platform | tools/_court_probe.mjs --way/--at + tools/playtest/seen_probe.mjs + tools/playtest/wayfind_probe.mjs |
| REFUTED against the game · VERIFIED against the harness | P1 | PT-20260805-033 | Stuck in geometry at far right platform | tools/_court_probe.mjs --way/--at + tools/playtest/seen_probe.mjs + tools/playtest/wayfind_probe.mjs |
| REFUTED against the game · VERIFIED against the harness | P1 | PT-20260805-034 | Character stuck on central wooden platform unable to move | tools/_court_probe.mjs --way/--at + tools/playtest/seen_probe.mjs + tools/playtest/wayfind_probe.mjs |
| THE HOLE IS VERIFIED · THE MECHANISM IS STILL UNNAMED · ONE SUSPECT REFUTED | P1 | PT-20260805-040 | Walk blocked: the body closed 0 m of an intended 11.33 m, twice at the same place | tools/_court_probe.mjs --at/--way + tools/scenegraph_derive.mjs + docs/qa/playtest/runs/run-20260805-121612/run.jsonl |
| THE HOLE IS VERIFIED · THE MECHANISM IS STILL UNNAMED · ONE SUSPECT REFUTED | P1 | PT-20260805-041 | Character stuck on bottom right dock geometry | tools/_court_probe.mjs --at/--way + tools/scenegraph_derive.mjs + docs/qa/playtest/runs/run-20260805-121612/run.jsonl |
| VERIFIED | P1 | PT-20260805-053 | Walk blocked: the body closed 0 m of an intended 10.13 m, twice at the same place | tools/reach_probe.mjs (in the running page) |
| REFUTED | P1 | PT-20260805-042 | Keepers' Cottage exit teleports player back to lower dock loop | tools/reach_probe.mjs + SIM.move (in the running page) |
| PARTIAL | P1 | PT-20260805-044 | Clicking upper level objective marker causes character to walk underneath it | tools/playtest/wayfind_probe.mjs + tools/_court_probe.mjs --way |
| FIXED | P1 | PT-20260805-045 | Stuck on plank bridge due to missing walkable ground navmesh | tools/playtest/wayfind_probe.mjs + tools/_court_probe.mjs --way/--grid |
| FIXED | P1 | PT-20260805-046 | Cannot navigate to Lock Five exit from broken bridge | tools/playtest/wayfind_probe.mjs + tools/_court_probe.mjs --way/--grid |
| VERIFIED | P1 | PT-20260805-054 | Walk blocked: the body closed 0 m of an intended 8.45 m, twice at the same place | tools/reach_probe.mjs (in the running page) |
| REFUTED | P1 | PT-20260805-047 | NPC blocking narrow bridge path | tools/reach_probe.mjs + SIM.move (in the running page) |
| FIXED | P1 | PT-20260805-049 | Moorage deck at [76.15,1.32,-27.11] is a one-way pocket: the body can only leave eastward | tools/_court_probe.mjs --way (SIM.move, the drive, 400 ticks per leg) |
| FIXED | P1 | PT-20260805-050 | weave shot: the routed Lock Five arrow sits at the frame edge on wv_piles, and every click on it fails | tools/playtest/wayfind_probe.mjs --from ch2.winches --stations weave |
| REFUTED | P1 | PT-20260805-051 | Stuck on plank bridge, cannot move up or down | tools/reach_probe.mjs + SIM.move (in the running page) |
| REFUTED | P1 | PT-20260805-052 | Character stuck behind wooden pillars under curved platform | tools/reach_probe.mjs + SIM.move (in the running page) |
| FIXED | P1 | PT-20260805-055 | The player can leave the chapter on its first frame, and the objective follows them out | tools/_court_probe.mjs --way (SIM.move in the running game) + tools/routes_derive.mjs --check + tools/playthrough_test.mjs |
| FIXED | P1 | PT-20260805-057 | The player can leave the chapter on its first frame, and the objective follows them out | the recorded run itself (run-20260805-194359 percepts) replayed through the amended detector |
| VERIFIED | P1 | PT-20260806-002 | Character stuck on wooden plank bridge geometry at Lock Five | tools/reach_probe.mjs + SIM.move (in the running page) |
| VERIFIED | P1 | PT-20260806-004 | The player can leave the chapter on its first frame, and the objective follows them out | llm_playtester spine detector (public/game/story.json vs the running scene) |
| REFUTED | P1 | PT-20260805-058 | Exit trigger to The Emberbrook Valley does not activate when standing on marker | tools/reach_probe.mjs + SIM.move (in the running page) |
| REFUTED | P1 | PT-20260805-059 | Overlapping interaction prompts for 'Leave' and 'Talk' use the same key | tools/reach_probe.mjs + SIM.move (in the running page) |
| REFUTED | P1 | PT-20260805-060 | Scene transition for 'The Lockhead' is not triggering | tools/reach_probe.mjs + SIM.move (in the running page) |
| REFUTED | P1 | PT-20260805-062 | Cannot trigger 'The Lockhead' transition marker | tools/reach_probe.mjs + SIM.move (in the running page) |
| REFUTED | P1 | PT-20260805-063 | Multiple actions bound to the same key [E] prevent leaving the room | tools/reach_probe.mjs + SIM.move (in the running page) |
| FIXED | P1 | PT-20260805-064 | Interact button prioritizes bargeman dialogue over exiting room | tools/_court_probe.mjs --comp/--who + adapter drive (real keys + E) in del-inn-int, both ways |
| REFUTED against the game · VERIFIED against the harness | P1 | PT-20260805-065 | Infinite screen transition loop following 'The Lockhead' marker | run traces (runs 194359/211913/215044) + adapter drive reproduction + follow-the-arrow scripted bot |
| REFUTED against the game · VERIFIED against the harness | P1 | PT-20260805-066 | Wrong transition prompt appears at 'The Lockhead' marker | same as PT-20260805-065 |
| REFUTED | P1 | PT-20260805-067 | Stuck on stairs trying to reach 'The Lockhead' exit marker | tools/reach_probe.mjs + SIM.move (in the running page) |
| REFUTED | P1 | PT-20260806-001 | Cannot navigate up the stairs to reach the girl for the objective | tools/reach_probe.mjs + SIM.move (in the running page) |
| REFUTED | P1 | PT-20260806-005 | Cannot walk across the long wooden bridge | tools/reach_probe.mjs + SIM.move (in the running page) |
| REFUTED | P1 | PT-20260806-006 | Wooden bridge navmesh is missing or unwalkable | tools/reach_probe.mjs + SIM.move (in the running page) |
| REFUTED | P1 | PT-20260806-011 | Cannot walk across the wooden bridge; 'not ground' error | tools/reach_probe.mjs + SIM.move (in the running page) |
| REFUTED | P1 | PT-20260806-014 | Cannot walk left across the wooden bridge | tools/reach_probe.mjs + SIM.move (in the running page) |
| REFUTED | P1 | PT-20260806-026 | Lock Five zone transition trigger not activating | tools/reach_probe.mjs + SIM.move (in the running page) |
| REFUTED | P1 | PT-20260806-029 | Exit label 'Lock Five' jumps to player's location | tools/reach_probe.mjs + SIM.move (in the running page) |
| REFUTED | P1 | PT-20260806-030 | Cannot pathfind to Lock Five transition from upper walkway | tools/reach_probe.mjs + SIM.move (in the running page) |
| REFUTED | P1 | PT-20260806-036 | Pathfinding fails when trying to reach the Lock Five exit | tools/reach_probe.mjs + SIM.move (in the running page) |
| REFUTED | P1 | PT-20260806-038 | Cannot pathfind down to Lock Five exit marker from upper platform | tools/reach_probe.mjs + SIM.move (in the running page) |
| REFUTED | P2 | PT-20260804-009 | Cannot interact with NPCs inside The Boatmen's Rest | tools/reach_probe.mjs (in the running page) |
| REFUTED | P2 | PT-20260805-016 | Area transition trigger blocks path to objective building | tools/reach_probe.mjs + SIM.move (in the running page) |
| REFUTED | P2 | PT-20260805-056 | Overlapping interaction prompts near shop exit | tools/reach_probe.mjs + SIM.move (in the running page) |

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

### PT-20260805-036 — Character stuck on terrain geometry on middle platform

- **status** REFUTED against the game · VERIFIED against the harness (tools/_court_probe.mjs --way/--at + tools/playtest/seen_probe.mjs + tools/playtest/wayfind_probe.mjs)
- **severity** P0 · **kind** blocker · **found by** stuck-interview
- **I was doing** I was trying to move in any direction (left towards the stairs, right towards the walkway, or down) to get off this middle platform and head towards Lock Five.
- **I expected** I expected my character to walk along the path in the direction I clicked.
- **What happened** My character is completely stuck in place and won't move no matter where I click. I seem to be caught on some invisible geometry.

```
STRAIGHT-LINE DRIVE TO THE CLICKED POINT: stalls (this triage run).
BUT THE WORLD IS OPEN. _court_probe --way from the same cell [58.11,14.24,-12.8] toward the
route the game routes through (east, the quay-west>weave cut) walks 3/3 legs BOTH ways, ending
[61.99,14.07,-14.39] / [58.63,14.39,-12.98], stalled: no. --at: ground clear east and south;
only ls_rail west, a fence doing its job. The claim under test was 'trapped, cannot move in any
direction', and that is FALSE.
WHY THE STRAIGHT DRIVE STALLS: every point the agent clicked was WEST (x 33-53) or on the tier
5 m above (y 19.07). SIM.move is not a pathfinder, and reach_probe's own answer says so --
'reachable via 3 in-scene edges', i.e. by taking a cut, not by pushing through the fence.
THE DEFECT IS THE AIM, AND ITS CAUSE IS MEASURED: seen_probe puts the body at charNdc
[-0.623,0.238] = screen [241,274] of 1280x720 with 353/428 pixels through the plate, while the
ticket says 'far right of the platform'; wayfind_probe --from=ch2.maren (the run's own state)
shows the routed 'Lock Five' arrow at nx 0.076, lift 22 px, its click landing on
walk_e_quay-deck__pilot-cluster_landing. The agent aimed nx 0.30-0.86 on 29 consecutive steps.
Fixed in the percept (690c1d4): percept.you + percept.markers. FIXLOG round 23.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-036` (captured at fca1c303)

### PT-20260805-048 — Cannot enter Keepers' Cottage despite standing on the waypoint marker

- **status** VERIFIED (tools/reach_probe.mjs (in the running page))
- **severity** P0 · **kind** blocker · **found by** stuck-interview
- **I was doing** I was trying to enter the Keepers' Cottage to continue the supper quest.
- **I expected** I expected to transition into the cottage or trigger a cutscene/dialogue when standing on or interacting with the marker.
- **What happened** I am standing right on the marker and clicking it or trying to walk past it does nothing. I am stuck outside.

```
where I stood -> where I pointed: UNREACHABLE — [75.88,1.32,-26.85] -> [67.95,6.91,-29.5]: 4165 cells filled from the start, 48 from the target, and they never meet. Nearest standable cell to the target is 1.9 m away (at 66.8,1.64,-28, 5.27 m off in height); the two regions come within 0.4 m of each other between [61.2,1.2,-28.8] and [61.6,6.91,-28.8] — a 5.71 m step.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-048` (captured at 99d3dacd)

### PT-20260806-003 — Stuck on plank bridge geometry trying to reach Lock Five exit

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P0 · **kind** blocker · **found by** stuck-interview
- **I was doing** I was trying to walk down the broken plank bridge to reach the 'Lock Five' exit arrow at the bottom.
- **I expected** My character should walk down the planks and trigger the area transition.
- **What happened** My character is stuck on the slanted planks and won't move any further down towards the exit arrow, no matter where I click.

```
where I stood -> where I pointed: reachable (1.3 m apart, 1 cells filled on foot)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [90.22,8.68,-21.69] and stopped 1.29 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-003` (captured at c210feeb)

### PT-20260806-027 — Cannot transition through Lock Five exit

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P0 · **kind** blocker · **found by** stuck-interview
- **I was doing** I'm trying to leave the area by clicking on the 'Lock Five' exit marker.
- **I expected** I expected the game to load the next area or transition me to Lock Five.
- **What happened** My character walks right up to the marker, but nothing happens. I'm just stuck standing there.

```
where I stood -> where I pointed: reachable (12.5 m apart, 1200 cells filled, via 2 in-scene edges)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [61.71,11.6,-17.66] and stopped 10.95 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-027` (captured at d9b5ff70)

### PT-20260806-031 — Scene transition 'Lock Five' does not trigger when reached

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P0 · **kind** blocker · **found by** stuck-interview
- **I was doing** I was trying to take the 'Lock Five' scene transition to continue my objective.
- **I expected** When I reached the coordinates for the 'Lock Five' transition, I expected the scene to change.
- **What happened** I walked right up to the 'Lock Five' marker, but nothing happened. I'm stuck on this screen.

```
where I stood -> where I pointed: reachable (15.4 m apart, 1887 cells filled on foot)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [61.74,11.6,-19.49] and stopped 14.2 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-031` (captured at d9b5ff70)

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

### PT-20260805-001 — Character stuck on wooden platform, unable to move left or right

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I was trying to walk left towards the head-gate winches, and when that failed, I tried to backtrack to the right.
- **I expected** I expected my character to walk along the wooden paths to the clicked locations.
- **What happened** My character is stuck in place on the platform near the red plank and won't move anywhere.

```
where I stood -> where I pointed: reachable (23.1 m apart, 1565 cells filled, via 2 in-scene edges)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [58.11,14.24,-12.16] and stopped 22.96 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-001` (captured at 9896586b)

### PT-20260805-004 — Character stuck on Lock Five central deck geometry

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** blocker · **found by** agent
- **I was doing** Trying to walk across the walkway towards the head-gate winches.
- **I expected** The character should walk towards clicked ground on the path.
- **What happened** The character is completely stuck and cannot move in any direction (0 meters closed on every movement attempt).

```
where I stood -> where I pointed: reachable (8.5 m apart, 627 cells filled, via 2 in-scene edges)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [57.74,15.3,-11.45] and stopped 8.52 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-004` (captured at 37ce4161)

### PT-20260805-005 — Cannot interact with head-gate winches to progress objective

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I walked right up to the head-gate winches on the left platform, where the red marker is, and pressed the interact button.
- **I expected** I expected my character to use the winches and for the objective to update or a cutscene to play.
- **What happened** Nothing happened at all. I'm just standing next to the winches and the objective hasn't changed.

```
where I stood -> where I pointed: reachable (1.4 m apart, 40 cells filled, via 1 in-scene edge)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [57.74,15.3,-11.25] and stopped 1.39 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-005` (captured at 37ce4161)

### PT-20260805-011 — Cannot interact with Mara at the Heartlight

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I was trying to talk to Mara at the Heartlight to complete that part of the objective.
- **I expected** I expected a conversation to start when I interacted with her.
- **What happened** I clicked to interact but nothing happened, and the objective hasn't updated.

```
where I stood -> where I pointed: reachable (11.0 m apart, 1553 cells filled on foot)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [55.18,1.36,-45.83] and stopped 10.65 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-011` (captured at 475f6161)

### PT-20260805-012 — Character gets stuck trying to navigate around the Heartlight well

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I was trying to walk around the central well to reach Mara and talk to her.
- **I expected** My character should have walked around the well to get to Mara.
- **What happened** My character got stuck near the wooden platform and wouldn't pathfind around the well, no matter where I clicked.

```
where I stood -> where I pointed: reachable (9.5 m apart, 1605 cells filled on foot)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [55.17,1.36,-45.81] and stopped 9.51 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-012` (captured at 475f6161)

### PT-20260805-013 — The player can leave the chapter on its first frame, and the objective follows them out

- **status** VERIFIED (llm_playtester spine detector (public/game/story.json vs the running scene))
- **severity** P1 · **kind** bug · **found by** spine-detector
- **I was doing** I read the opening narration by pressing the action button, then used the only prompt on screen.
- **I expected** To carry on with the objective the game was showing me.
- **What happened** I ended up somewhere with no way to advance the story, and the objective on screen ("Step through the Old Gate") still refers to where I was. Nothing here can continue the chapter.

```
The body was in "emb-cine" for three consecutive steps while none of the next un-fired beats in story.json lives there. Beats fired at the time: ch1.open, ch1.waystone, ch1.reveal, ch1.rowan, ch1.lake.handoff, ch1.lake.wake, ch1.lake.hearth, ch1.lake.lamp, ch1.meet, ch1.lamps, ch1.hush, ch1.see.mara, ch1.see.poppy, ch1.see.finn, ch1.see.mochi, ch1.pact, ch1.sigils, ch1.sendoff. This is a mechanical fact about the game, not a model opinion — there is nothing left to measure. What to DO about it is a design decision.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-013` (captured at b8b6f12a)

### PT-20260805-019 — Cannot figure out how to reach 'The Lockhead' marker from the upper balcony

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** confusion · **found by** stuck-interview
- **I was doing** Trying to walk to the objective marker labeled 'The Lockhead'.
- **I expected** To be able to walk down to the marker or find a clear path to it.
- **What happened** I'm stuck on the upper balcony of the building. Clicking near the marker or on the stairs below doesn't work; my character either doesn't move or the game says I can't walk there. I can't see a way to get down to where the objective is pointing.

```
where I stood -> where I pointed: reachable (3.1 m apart, 42 cells filled, via 1 in-scene edge)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [53.76,18.43,-9.87] and stopped 3.09 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-019` (captured at b8b6f12a)

### PT-20260805-020 — Quest NPC Dellhollow gives generic dialogue instead of advancing quest

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I was trying to talk to Dellhollow to find out about the lockhead, since they have a quest marker over their head.
- **I expected** I expected Dellhollow to tell me about the lockhead or for the quest to update after speaking to them.
- **What happened** Dellhollow just repeats generic dialogue like 'Pot's on...' and the quest doesn't progress.

```
where I stood -> where I pointed: reachable (3.3 m apart, 50 cells filled on foot)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [0.11,-0.06,-1.97] and stopped 3.31 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-020` (captured at b8b6f12a)

### PT-20260805-022 — Character gets stuck on stairs trying to reach Lock Five transition

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I was trying to walk down the stairs towards the 'Lock Five' marker to reach the lock apron.
- **I expected** I expected my character to walk down the stairs and trigger the area transition.
- **What happened** My character gets stuck on the stairs and cannot move far enough down to reach the transition marker.

```
where I stood -> where I pointed: reachable (1.3 m apart, 4129 cells filled, via 5 in-scene edges)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [39.43,14.07,-18.51] and stopped 1.27 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-022` (captured at 44e93c6b)

### PT-20260805-023 — Navigation fails when trying to move around the lower dock area

- **status** VERIFIED (tools/reach_probe.mjs (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I was trying to walk to the girl and the red markers on the lower dock area under the circular deck.
- **I expected** My character should walk to the spots I click on, as they look like open, accessible areas.
- **What happened** My character gets stuck and won't move to the locations I click, preventing me from reaching the objective.

```
where I stood -> where I pointed: UNREACHABLE — [72.07,1.25,-29.19] -> [68.11,6.91,-29.5]: 1467 cells filled from the start, 48 from the target, and they never meet. Nearest standable cell to the target is 1.9 m away (at 68,1.79,-27.6, 5.12 m off in height); the two regions come within 0.4 m of each other between [61.2,1.2,-28.8] and [61.6,6.91,-28.8] — a 5.71 m step.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-023` (captured at 44e93c6b)

### PT-20260805-024 — Player gets stuck under circular deck, unable to navigate to girl on lock apron

- **status** VERIFIED (tools/reach_probe.mjs (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** Trying to walk to the girl on the dock/lock apron.
- **I expected** To walk around the pillars and reach the girl.
- **What happened** I keep getting stuck under the circular deck and my character won't move past the pillars to get to her.

```
where I stood -> where I pointed: UNREACHABLE — [70.76,1.25,-28.01] -> [65.48,6.91,-29.5]: 1467 cells filled from the start, 47 from the target, and they never meet. Nearest standable cell to the target is 1.1 m away (at 65.6,1.48,-28.4, 5.43 m off in height); the two regions come within 0.4 m of each other between [61.2,1.2,-28.8] and [61.6,6.91,-28.8] — a 5.71 m step.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-024` (captured at 44e93c6b)

### PT-20260805-025 — Character stuck in geometry under circular platform

- **status** VERIFIED (tools/reach_probe.mjs (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I ended up underneath the large circular wooden platform and was trying to navigate back out through the support pillars to reach the objective.
- **I expected** I expected to be able to walk between the pillars to get back to the main path or dock area.
- **What happened** My character is completely stuck in the geometry between the wooden support pillars under the deck. I cannot move in any direction to escape.

```
where I stood -> where I pointed: UNREACHABLE — [70.76,1.25,-28.01] -> [66.43,6.91,-29.5]: 1467 cells filled from the start, 48 from the target, and they never meet. Nearest standable cell to the target is 1.4 m away (at 65.6,1.48,-28.4, 5.43 m off in height); the two regions come within 0.4 m of each other between [61.2,1.2,-28.8] and [61.6,6.91,-28.8] — a 5.71 m step.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-025` (captured at 44e93c6b)

### PT-20260805-027 — Cannot move character towards Dellhollow in the cookhouse

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I'm trying to walk over to Dellhollow on the right side of the room because he has a marker over his head.
- **I expected** My character should walk across the room to where I'm clicking.
- **What happened** My character is stuck standing near the cook and won't move towards Dellhollow at all.

```
where I stood -> where I pointed: reachable (2.7 m apart, 33 cells filled on foot)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [0.19,0,-1.97] and stopped 2.7 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-027` (captured at 22002c13)

### PT-20260805-028 — Character stuck in geometry near cookhouse table

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** blocker · **found by** agent
- **I was doing** Trying to navigate across the cookhouse floor towards Dellhollow.
- **I expected** Character should pathfind or move around the furniture.
- **What happened** 5 consecutive goto actions failed to move the character at all (0 m closed).

```
where I stood -> where I pointed: reachable (3.7 m apart, 95 cells filled on foot)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [0.07,0,-1.95] and stopped 3.67 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-028` (captured at 22002c13)

### PT-20260805-029 — Player gets stuck trying to walk down stairs to Lock Five

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I was trying to walk down the wooden stairs/ramps to reach the 'Lock Five' marker at the bottom of the screen.
- **I expected** My character should walk down the stairs towards the marker.
- **What happened** My character seems to get stuck on the geometry of the stairs and won't path downwards, even though I'm clicking below them.

```
where I stood -> where I pointed: reachable (3.3 m apart, 3 cells filled on foot)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [39.48,5.98,-20.87] and stopped 3.26 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-029` (captured at 22002c13)

### PT-20260805-030 — Walk blocked: the body closed 0 m of an intended 4.34 m, twice at the same place

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** blocker · **found by** walk-executor
- **I was doing** I tried to walk to a point on screen at [0.47, 0.65]; my goal was "Follow the green mossy platforms down to reach Lock Five.".
- **I expected** To walk about 4.34 m and arrive there.
- **What happened** The character moved 0 m and stopped 4.34 m short — twice in this run. All five headings were pushed (5 bursts at ~159 ms each) and none of them moved the body, so this is the world refusing rather than the harness running out of time. Something is in the way, or that ground is not connected to where I was standing.

```
where I stood -> where I pointed: reachable (4.3 m apart, 61 cells filled on foot)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [39.62,5.94,-20.81] and stopped 4.34 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-030` (captured at 22002c13)

### PT-20260805-031 — Walk blocked: the body closed 0 m of an intended 3.41 m, twice at the same place

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** blocker · **found by** walk-executor
- **I was doing** I tried to walk to a point on screen at [0.55, 0.58]; my goal was "Descend the stairs by walking right to the stair landing and then down to Lock Five.".
- **I expected** To walk about 3.41 m and arrive there.
- **What happened** The character moved 0 m and stopped 3.41 m short — twice in this run. All five headings were pushed (5 bursts at ~161 ms each) and none of them moved the body, so this is the world refusing rather than the harness running out of time. Something is in the way, or that ground is not connected to where I was standing.

```
where I stood -> where I pointed: reachable (3.4 m apart, 3 cells filled on foot)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [39.62,5.94,-20.81] and stopped 3.41 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-031` (captured at 22002c13)

### PT-20260805-035 — Character stuck on middle cliffside path

- **status** REFUTED against the game · VERIFIED against the harness (tools/_court_probe.mjs --way/--at + tools/playtest/seen_probe.mjs + tools/playtest/wayfind_probe.mjs)
- **severity** P1 · **kind** blocker · **found by** agent
- **I was doing** Trying to walk along or down from the middle platform near x=0.43, y=0.42
- **I expected** Character should navigate around obstacles to reach the destination
- **What happened** Character is completely stuck in place and cannot move in any direction despite multiple movement attempts

```
STRAIGHT-LINE DRIVE TO THE CLICKED POINT: stalls (this triage run).
BUT THE WORLD IS OPEN. _court_probe --way from the same cell [58.11,14.24,-12.8] toward the
route the game routes through (east, the quay-west>weave cut) walks 3/3 legs BOTH ways, ending
[61.99,14.07,-14.39] / [58.63,14.39,-12.98], stalled: no. --at: ground clear east and south;
only ls_rail west, a fence doing its job. The claim under test was 'trapped, cannot move in any
direction', and that is FALSE.
WHY THE STRAIGHT DRIVE STALLS: every point the agent clicked was WEST (x 33-53) or on the tier
5 m above (y 19.07). SIM.move is not a pathfinder, and reach_probe's own answer says so --
'reachable via 3 in-scene edges', i.e. by taking a cut, not by pushing through the fence.
THE DEFECT IS THE AIM, AND ITS CAUSE IS MEASURED: seen_probe puts the body at charNdc
[-0.623,0.238] = screen [241,274] of 1280x720 with 353/428 pixels through the plate, while the
ticket says 'far right of the platform'; wayfind_probe --from=ch2.maren (the run's own state)
shows the routed 'Lock Five' arrow at nx 0.076, lift 22 px, its click landing on
walk_e_quay-deck__pilot-cluster_landing. The agent aimed nx 0.30-0.86 on 29 consecutive steps.
Fixed in the percept (690c1d4): percept.you + percept.markers. FIXLOG round 23.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-035` (captured at fca1c303)

### PT-20260805-037 — Character gets stuck navigating down stairs towards Lock Five

- **status** REFUTED (round 24, recorded here in round 25) (tools/playtest/wayfind_probe.mjs --from=ch2.supper --target=cottage (docs/qa/playtest/wayfind-r24))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I was trying to walk down the stairs from the upper walkway to the lower bridge to head left towards Lock Five.
- **I expected** My character should walk down the stairs and continue left along the lower bridge towards the objective.
- **What happened** My character reaches the stairs but then stops and cannot seem to navigate down them or across the lower bridge, leaving me stuck on the upper level.

```
At the honest seed, the routed hint at this stand is SHOWN, LABELLED, dest "Keepers' Cottage",
lift 22.6 px, and its first hop is identical to the metre-shortest. No station printed
SHIPPED HINT DISAGREES. Not a routing defect. FIXLOG round 24.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-037` (captured at 690c1d4e)

### PT-20260805-038 — Character stuck on walkway near lantern, cannot reach Keepers' Cottage

- **status** REFUTED as filed (round 24, recorded here in round 25) (tools/_court_probe.mjs --comp/--grid + tools/reach_probe.mjs)
- **severity** P1 · **kind** blocker · **found by** stuck-interview
- **I was doing** I was trying to walk left along the wooden dock towards the red arrow for the Keepers' Cottage.
- **I expected** My character should walk along the path to the entrance.
- **What happened** My character seems to be stuck on something invisible near the lantern and won't move left towards the objective, no matter where I click on the walkway.

```
--comp at the filed cell [61.85,1.25,-25.06] returns SEED UNSTANDABLE: under WALKLOCK there is
no walk network under the cell the agent filed from. --grid walk:true shows why — the fish
dock's east side at that z is a 0.4 m curtain of VISIBLE floor carrying no walk network, while
the real exit lane is two metres SOUTH at z -27.0..-27.4, where the network runs continuously
from x 58 to x 70. reach_probe maren -> cottage door is ok=true. The ticket named a tier; the
cause was a lane. FIXLOG round 24.
THE LAUNDRY, SEPARATELY: t2c_W9_laundry_planking_5 leaves 1.28 m over walk against BODY_H 1.30
and severs the crossing one tier up. Recorded in gate_cloth_headroom.py's UNFIXED register and
deliberately NOT fixed — it owes a re-bake and the story steps over it (weave>crossing is a cut
whose spawn lands 9.3 m east).
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-038` (captured at 690c1d4e)

### PT-20260805-043 — Player falls through upper deck walkway collision geometry

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** agent
- **I was doing** Walking along the elevated walkway towards the Keepers' Cottage transition
- **I expected** To walk along the upper deck to reach the Keepers' Cottage entrance at [0.558, 0.272]
- **What happened** Stepping onto the upper walkway near [0.55, 0.33] repeatedly causes the character to fall through the floor back to the lower level at [0.375, 0.565] or [0.48, 0.64]

```
where I stood -> where I pointed: reachable (12.6 m apart, 559 cells filled on foot)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [77.06,1.07,-26.08] and stopped 2.23 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-043` (captured at 8ce6d0a3)

### PT-20260806-007 — Taking 'The Lockhead' exit loops back to start position

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** agent
- **I was doing** Walking to 'The Lockhead' exit arrow at [0.083, 0.442] as directed by the quest route.
- **I expected** To transition smoothly into the Lockhead area.
- **What happened** Every time I take the exit, I end up stuck on a bridge in the next scene with no valid path forward, which then bounces me back to this exact spot in Lock Five.

```
where I stood -> where I pointed: reachable (24.9 m apart, 1690 cells filled, via 2 in-scene edges)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [58.16,14.24,-12.16] and stopped 23.68 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-007` (captured at f21557cc)

### PT-20260806-008 — Stuck in screen transition loop following Lockhead objective path

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** blocker · **found by** agent
- **I was doing** Trying to navigate to 'The Lockhead' by taking the indicated exit at [0.083, 0.436].
- **I expected** To transition to the Lockhead area or be able to walk up the stairs on the adjacent screen to progress.
- **What happened** Taking 'The Lockhead' exit transitions to the next screen, but movement up the stairs on that screen is blocked by invisible geometry, resulting in an endless loop back and forth between the two screens.

```
where I stood -> where I pointed: reachable (26.4 m apart, 1689 cells filled, via 3 in-scene edges)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [58.15,14.24,-12.39] and stopped 25.3 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-008` (captured at f21557cc)

### PT-20260806-009 — Quest router loops infinitely between screen transitions

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** agent
- **I was doing** Following the routed exit 'The Lockhead' at [0.083, 0.426]
- **I expected** The waypoint path leads forward to the Lockhead
- **What happened** Taking 'The Lockhead' exit transitions to the right side of Lock Five, where the route directs right back into this screen, creating an endless loop.

```
where I stood -> where I pointed: reachable (26.5 m apart, 1689 cells filled, via 3 in-scene edges)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [58.15,14.24,-12.4] and stopped 25.37 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-009` (captured at f21557cc)

### PT-20260806-010 — Infinite screen transition loop following Lockhead objective marker

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** agent
- **I was doing** Walking to the routed exit marker 'The Lockhead' at [0.083, 0.434].
- **I expected** To reach the Lockhead area above Lock Five as instructed by the objective.
- **What happened** Taking the left exit transitions to the adjacent screen on the right, and taking the exit there transitions back here, creating an endless loop back and forth between screens.

```
where I stood -> where I pointed: reachable (4.4 m apart, 110 cells filled, via 1 in-scene edge)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [58.11,14.24,-12.18] and stopped 4.11 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-010` (captured at f21557cc)

### PT-20260806-013 — The player can leave the chapter on its first frame, and the objective follows them out

- **status** VERIFIED (llm_playtester spine detector (public/game/story.json vs the running scene))
- **severity** P1 · **kind** bug · **found by** spine-detector
- **I was doing** I read the opening narration by pressing the action button, then used the only prompt on screen.
- **I expected** To carry on with the objective the game was showing me.
- **What happened** I ended up somewhere with no way to advance the story, and the objective on screen ("Through the Dellhollow gate — find whoever runs the locks") still refers to where I was. Nothing here can continue the chapter.

```
The body was in "ow-valley" for three consecutive steps while none of the next un-fired beats in story.json lives there. Beats fired at the time: ch1.open, ch1.waystone, ch1.reveal, ch1.rowan, ch1.lake.handoff, ch1.lake.wake, ch1.lake.hearth, ch1.lake.lamp, ch1.meet, ch1.lamps, ch1.hush, ch1.see.mara, ch1.see.poppy, ch1.see.finn, ch1.see.mochi, ch1.pact, ch1.sigils, ch1.sendoff, ch1.done, ch2.road. This is a mechanical fact about the game, not a model opinion — there is nothing left to measure. What to DO about it is a design decision.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-013` (captured at ae3dfb12)

### PT-20260806-015 — Cannot enter Keepers' Cottage; transition marker not working

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I was trying to enter the Keepers' Cottage by walking to the red exit arrow marker.
- **I expected** I expected to transition into the cottage to continue my objective.
- **What happened** I walked to the marker multiple times, but nothing happened and I am stuck outside on the walkway.

```
where I stood -> where I pointed: reachable (1.8 m apart, 17 cells filled on foot)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [74.41,4.52,-25.81] and stopped 0.78 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-015` (captured at ae3dfb12)

### PT-20260806-016 — Cannot reach Keepers' Cottage transition point

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** Trying to enter the Keepers' Cottage by clicking on the transition arrow.
- **I expected** My character to walk to the arrow and enter the cottage.
- **What happened** My character gets stuck and cannot reach the transition point, even though I'm clicking right on it.

```
where I stood -> where I pointed: reachable (2.1 m apart, 19 cells filled on foot)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [74.25,4.14,-25.75] and stopped 0.83 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-016` (captured at ae3dfb12)

### PT-20260806-017 — Cannot enter Keepers' Cottage, character gets stuck on walkway

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** blocker · **found by** stuck-interview
- **I was doing** I was trying to enter the Keepers' Cottage by clicking on the red transition arrow.
- **I expected** My character should walk up to the door and transition into the cottage.
- **What happened** My character just stands on the walkway below the arrow and won't move to the transition point, so I can't go inside.

```
where I stood -> where I pointed: reachable (1.1 m apart, 1 cells filled on foot)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [74.78,4.52,-26.03] and stopped 0.91 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-017` (captured at ae3dfb12)

### PT-20260806-018 — Pathfinding stuck trying to reach The Lockhead marker

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** blocker · **found by** agent
- **I was doing** Trying to walk to 'The Lockhead' marker at [0.489, 0.582] as directed by the objective.
- **I expected** My character should pathfind down to the target marker.
- **What happened** My character gets stuck against terrain geometry at [0.495, 0.455] and makes no progress towards the destination.

```
where I stood -> where I pointed: reachable (4.8 m apart, 224 cells filled on foot)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [17.79,24.07,-5.95] and stopped 4.69 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-018` (captured at dfe35338)

### PT-20260806-019 — Stuck on upper walkway, cannot reach 'The Lockhead' marker below

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** blocker · **found by** stuck-interview
- **I was doing** Trying to reach the objective marker 'The Lockhead' which is on the dirt path below my current position.
- **I expected** My character should find a path down from the wooden platform to the marker.
- **What happened** I am stuck on the wooden platform. Clicking the marker or trying to click around to find a way down doesn't work; my character won't move off the platform.

```
where I stood -> where I pointed: reachable (4.8 m apart, 224 cells filled on foot)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [17.79,24.07,-5.95] and stopped 4.69 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-019` (captured at dfe35338)

### PT-20260806-020 — Player stuck on porch/roof above 'The Lockhead' marker, cannot path down

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** Trying to reach 'The Lockhead' way-out marker from the porch above it.
- **I expected** The character to walk down from the porch to the marker.
- **What happened** The character is stuck on the porch and the goto command fails to find a path to the marker below.

```
where I stood -> where I pointed: reachable (12.4 m apart, 329 cells filled, via 2 in-scene edges)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [20.93,24.07,-7.13] and stopped 7.85 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-020` (captured at dfe35338)

### PT-20260806-021 — Unable to pathfind to 'The Lockhead' entrance from upper porch

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** agent
- **I was doing** Attempting to walk to 'The Lockhead' marker at [0.489, 0.579] using both direct goto and manual waypoints
- **I expected** The character should be able to walk down off the porch to the target marker
- **What happened** Direct pathfinding fails to move the character down, and manual waypoints get stuck trying to approach the entrance marker.

```
where I stood -> where I pointed: reachable (13.4 m apart, 380 cells filled, via 2 in-scene edges)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [20.93,24.07,-7.28] and stopped 10.96 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-021` (captured at dfe35338)

### PT-20260806-022 — Pathfinding stuck on upper deck railing when targeting marker below

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** agent
- **I was doing** Directly targeting 'The Lockhead' way-out marker at [0.489, 0.577] as directed
- **I expected** Character should auto-path down the left walkway stairs to reach the marker below
- **What happened** Character walks into the upper balcony railing and stops after moving 0.02m

```
where I stood -> where I pointed: reachable (4.7 m apart, 241 cells filled on foot)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [17.79,24.07,-6.17] and stopped 4.67 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-022` (captured at dfe35338)

### PT-20260806-023 — Pathfinding fails when trying to reach a marker directly below the player

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I'm trying to click on 'The Lockhead' marker to go there.
- **I expected** My character should find a path down from the upper deck to the marker.
- **What happened** My character just stands there on the upper deck and doesn't move towards the marker below.

```
where I stood -> where I pointed: reachable (4.7 m apart, 241 cells filled on foot)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [17.78,24.07,-6.23] and stopped 4.66 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-023` (captured at dfe35338)

### PT-20260806-024 — Pathfinding to The Lockhead is blocked from the upper deck

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** agent
- **I was doing** Attempting to navigate to 'The Lockhead' way-out marker at [0.489, 0.572] using direct goto and stair waypoints
- **I expected** The character should be able to walk down to the Lockhead entrance.
- **What happened** Direct navigation attempts fail with zero progress, and waypoint paths down the stairs get stuck near [0.49, 0.58].

```
where I stood -> where I pointed: reachable (15.4 m apart, 329 cells filled, via 2 in-scene edges)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [20.93,24.07,-7.12] and stopped 7.85 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-024` (captured at dfe35338)

### PT-20260806-025 — Pathfinding fails to reach 'The Lockhead' marker from the upper roof/path

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** Clicking exactly on 'The Lockhead' marker to auto-walk there.
- **I expected** My character should find a path down to the lower level and reach the marker.
- **What happened** My character gets stuck on the upper level above the marker and barely moves.

```
where I stood -> where I pointed: reachable (4.8 m apart, 164 cells filled on foot)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [17.79,24.07,-5.95] and stopped 4.69 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-025` (captured at dfe35338)

### PT-20260806-028 — Cannot interact with 'Lock Five' exit marker from the walkway directly above it

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** Trying to take the 'Lock Five' exit by clicking on the red marker.
- **I expected** My character to automatically navigate down to the correct level and trigger the transition.
- **What happened** My character just shuffles around on the upper wooden walkway directly above the marker. Clicking the marker doesn't route me down to it, and I'm stuck on this upper level.

```
where I stood -> where I pointed: reachable (15.3 m apart, 1888 cells filled on foot)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [61.58,11.6,-19.67] and stopped 13.9 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-028` (captured at d9b5ff70)

### PT-20260806-032 — Lock Five area transition fails to trigger when standing on marker

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** agent
- **I was doing** Walking directly onto the Lock Five transition marker at [0.514, 0.461] as routed by the objective guide.
- **I expected** Stepping onto the transition marker should trigger an area transition down to Lock Five / lock apron.
- **What happened** The character reaches the marker at [0.514, 0.461] repeatedly ('reached'), but no screen transition or interaction occurs.

```
where I stood -> where I pointed: reachable (11.5 m apart, 1101 cells filled, via 2 in-scene edges)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [61.74,11.6,-17.66] and stopped 9.87 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-032` (captured at 8ba970bc)

### PT-20260806-033 — Character stuck on roof above Lock Five marker

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** trying to reach the Lock Five transition marker to continue the objective
- **I expected** to walk along the wooden walkway to the marker and transition to the next area
- **What happened** my character is stuck standing on the slanted roof of the building right above the marker and cannot path down to it

```
where I stood -> where I pointed: reachable (11.4 m apart, 1127 cells filled, via 2 in-scene edges)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [61.78,11.6,-17.65] and stopped 9.81 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-033` (captured at 8ba970bc)

### PT-20260806-034 — Character gets stuck on walkway above 'Lock Five' transition marker

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I was trying to click the 'Lock Five' marker to move to the next area.
- **I expected** My character should walk to the marker and trigger the transition to the next screen.
- **What happened** My character walks to the wooden walkway directly above the marker and stops. The transition doesn't trigger, and I'm stuck on the upper level.

```
where I stood -> where I pointed: reachable (11.4 m apart, 1127 cells filled, via 2 in-scene edges)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [61.77,11.6,-17.65] and stopped 9.79 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-034` (captured at 8ba970bc)

### PT-20260806-037 — Character stuck on upper platform, cannot navigate to Lock Five waypoint

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I was trying to click on the 'Lock Five' waypoint to go down to the lock apron as instructed by the objective.
- **I expected** My character should have found a path down the stairs or walkways to reach the waypoint.
- **What happened** My character seems stuck on the roof or upper platform and won't move towards the waypoint when I click it.

```
where I stood -> where I pointed: reachable (14.5 m apart, 1887 cells filled, via 1 in-scene edge)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [61.74,11.6,-19.48] and stopped 14.21 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-037` (captured at 5c53dd3f)

### PT-20260806-039 — Walk blocked: the body closed 0 m of an intended 6.43 m, twice at the same place

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** blocker · **found by** walk-executor
- **I was doing** I tried to walk to a point on screen at [0.12, 0.52]; my goal was "Navigate to Lock Five at [0.12, 0.522] to reach the lock apron.".
- **I expected** To walk about 6.43 m and arrive there.
- **What happened** The character moved 0 m and stopped 6.43 m short — twice in this run. All five headings were pushed (5 bursts at ~162 ms each) and none of them moved the body, so this is the world refusing rather than the harness running out of time. Something is in the way, or that ground is not connected to where I was standing.

```
where I stood -> where I pointed: reachable (6.4 m apart, 612 cells filled on foot)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [53.08,14.83,-12.81] and stopped 6.43 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-039` (captured at 5c53dd3f)

### PT-20260806-040 — Character stuck on elevated walkway, unable to pathfind to Lock Five exit

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I was trying to walk to the Lock Five exit by clicking on the red arrow marker.
- **I expected** I expected my character to automatically navigate down the walkways and stairs to reach the exit.
- **What happened** My character barely moved and seems stuck on the current platform, unable to find a path to the destination despite repeated clicks.

```
where I stood -> where I pointed: reachable (11.2 m apart, 1168 cells filled, via 2 in-scene edges)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [61.77,11.6,-17.66] and stopped 10.83 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-040` (captured at 5c53dd3f)

### PT-20260806-041 — Character stuck on elevated walkway pathfinding to Lock Five

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** blocker · **found by** agent
- **I was doing** Attempting to walk to the Lock Five exit arrow at [0.205, 0.585].
- **I expected** The character should pathfind along the wooden walkways down towards Lock Five.
- **What happened** The character makes virtually no progress (stuck at [0.525, 0.42]) across repeated movement commands.

```
where I stood -> where I pointed: reachable (11.2 m apart, 1168 cells filled, via 2 in-scene edges)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [61.77,11.6,-17.66] and stopped 10.83 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-041` (captured at 5c53dd3f)

### PT-20260806-042 — Pathfinding to Lock Five exit marker is stuck

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** blocker · **found by** agent
- **I was doing** Attempting to navigate to the Lock Five exit marker at [0.205, 0.576].
- **I expected** The character should walk along the wooden walkways down towards Lock Five.
- **What happened** The character remains stuck at [0.505, 0.43] across multiple movement attempts.

```
where I stood -> where I pointed: reachable (14.5 m apart, 1887 cells filled, via 1 in-scene edge)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [61.78,11.6,-18.8] and stopped 14.45 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-042` (captured at 5c53dd3f)

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

### PT-20260804-010 — I spent 12 turns inside del-inn-int and nothing in the room answered me

- **status** UNVERIFIED (nothing measured yet)
- **severity** P1 · **kind** bug · **found by** empty-room-detector
- **I was doing** I went through a door the game offered me and tried to talk to everyone and everything inside.
- **I expected** Somebody to talk to, something to buy, or something to do — a room the game lets me into should hold something.
- **What happened** 12 turns in this room and not one dialogue box, shop or menu opened. The only figures in here are the party I walked in with.

```
no instrument in this repo answers this claim — it is about taste, audio, or a comparison the agent could not have made. A human judges this one, or it is dropped.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260804-010` (captured at 9534b95d)

### PT-20260805-039 — Stuck on lower dock, cannot climb stairs to Keepers' Cottage

- **status** UNVERIFIED (tools/reach_probe.mjs (NOT RUN))
- **severity** P1 · **kind** blocker · **found by** stuck-interview
- **I was doing** trying to climb the wooden stairs to get up to the Keepers' Cottage for my objective
- **I expected** my character to walk up the stairs to the circular platform above
- **What happened** my character just shuffles around on the lower dock and won't actually go up the stairs, so I can't reach the objective marker

```
the reachability probe needs a running server: re-run this with --port=3000.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-039` (captured at e9bf1ba7)

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

### PT-20260804-011 — Cannot walk up the path to the head-gate winches

- **status** REFUTED (tools/reach_probe.mjs (in the running page))
- **severity** P0 · **kind** blocker · **found by** stuck-interview
- **I was doing** I was trying to walk up the dirt path towards the buildings and the NPC to reach the head-gate winches for my objective.
- **I expected** I expected to be able to walk up the path and reach the area under the canopy or the doorway.
- **What happened** I keep getting blocked by invisible walls. The game tells me the area right in front of me is 'not ground you can walk to', so I can't get to the winches.

```
where I stood -> where I pointed: reachable (0.4 m apart, 1 cells filled on foot)
  The ground IS connected, so the walk was not blocked by the world. The likely causes are the executor giving up (a narrow gap, a step it could not take at its 150 ms burst) or a body-box snag that the cell fill does not model — confirm with tools/walk_bodygate.mjs.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260804-011` (captured at 9534b95d)

### PT-20260805-014 — Cannot interact with the NPC at 'The Lockhead' marker

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P0 · **kind** blocker · **found by** stuck-interview
- **I was doing** I'm trying to talk to the person standing under the red 'The Lockhead' marker to complete my objective.
- **I expected** I expected an interaction prompt to appear, or for pressing the interact button to start a conversation with the NPC.
- **What happened** Nothing happens when I press interact. I've tried moving around to find the right spot, but I can't seem to trigger any dialogue or progress the objective.

```
where I stood -> where I pointed: reachable (1.0 m apart, 1 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [19.02,24.07,-5.17], 0.6 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-014` (captured at b8b6f12a)

### PT-20260805-021 — Cannot interact with 'The Lockhead' NPC to advance objective

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P0 · **kind** blocker · **found by** stuck-interview
- **I was doing** I walked up to the NPC marked 'The Lockhead' to talk to them and complete my current objective.
- **I expected** I expected an interaction prompt to appear, or for a conversation to start when I got close or clicked on the NPC.
- **What happened** Nothing happens. I can't interact with the NPC, and when I try to move closer into the structure they are standing in, the game tells me it's not walkable ground. I'm stuck and can't progress the quest.

```
where I stood -> where I pointed: reachable (0.8 m apart, 1 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [17.47,24.07,-5.16], 0.57 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-021` (captured at 44e93c6b)

### PT-20260805-061 — Cannot trigger 'The Lockhead' area transition marker

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P0 · **kind** bug · **found by** stuck-interview
- **I was doing** Trying to walk into 'The Lockhead' way-out marker to proceed to the next area.
- **I expected** To transition to the new area or initiate a conversation.
- **What happened** I walk into the marker and stand there, but nothing happens. Interacting also does nothing.

```
where I stood -> where I pointed: reachable (0.9 m apart, 1 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [33.33,19.07,-7.63], 0.58 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-061` (captured at a7be573f)

### PT-20260806-012 — Character stuck on ledge, unable to move to follow objective

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P0 · **kind** blocker · **found by** stuck-interview
- **I was doing** I was trying to follow the valley road down to Dellhollow as instructed by the objective.
- **I expected** I expected to be able to walk down the path or find a way off the ledge.
- **What happened** My character seems to be stuck on this dark stone ledge. No matter which direction I try to click to move, it tells me it's not ground I can walk to, and I can't progress.

```
where I stood -> where I pointed: reachable (0.6 m apart, 1 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [-48.32,26.37,23.32], 0.57 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-012` (captured at ae3dfb12)

### PT-20260806-035 — Standing on 'Lock Five' transition marker does not trigger area change

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P0 · **kind** blocker · **found by** stuck-interview
- **I was doing** I was trying to leave the area by walking onto the 'Lock Five' exit marker.
- **I expected** I expected the game to transition me to the next area when I reached the marker.
- **What happened** I am standing right on top of the red arrow for 'Lock Five' but nothing is happening. I can't progress.

```
where I stood -> where I pointed: reachable (0.3 m apart, 1 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [60.6,11.33,-19.51], 0.32 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-035` (captured at 8ba970bc)

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

### PT-20260804-012 — Cannot walk up the path to the head-gate winches at Lock Five

- **status** REFUTED (tools/reach_probe.mjs (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I was trying to walk up the dirt path towards the cottage and the wooden structure (the head-gate winches) to reach my objective.
- **I expected** I expected my character to walk up the path to the area with the winches.
- **What happened** The game wouldn't let me click to walk on most of the path leading up there, acting like it wasn't valid ground, so I couldn't reach my objective.

```
where I stood -> where I pointed: reachable (1.0 m apart, 1 cells filled on foot)
  The ground IS connected, so the walk was not blocked by the world. The likely causes are the executor giving up (a narrow gap, a step it could not take at its 150 ms burst) or a body-box snag that the cell fill does not model — confirm with tools/walk_bodygate.mjs.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260804-012` (captured at 9534b95d)

### PT-20260804-013 — Cannot reach red quest markers for head-gate winches

- **status** REFUTED (tools/reach_probe.mjs (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I was trying to walk to the red quest markers on the dirt bank to interact with the head-gate winches.
- **I expected** I expected to be able to walk up to the markers and interact with the winches to progress the objective.
- **What happened** The game wouldn't let me walk to the markers, saying it's 'not ground you can walk to', leaving me stuck on the wooden platform.

```
where I stood -> where I pointed: reachable (4.8 m apart, 150 cells filled, via 2 in-scene edges)
  The ground IS connected, so the walk was not blocked by the world. The likely causes are the executor giving up (a narrow gap, a step it could not take at its 150 ms burst) or a body-box snag that the cell fill does not model — confirm with tools/walk_bodygate.mjs.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260804-013` (captured at dfa47db3)

### PT-20260804-014 — Character stuck in collision on Lock Five upper platform

- **status** REFUTED (tools/reach_probe.mjs (in the running page))
- **severity** P1 · **kind** blocker · **found by** agent
- **I was doing** Trying to move away from the upper right ledge back down the path
- **I expected** Character should walk smoothly back along the wooden platform
- **What happened** Character is wedged in geometry at [0.88, 0.22] and cannot move in any direction (0m traveled over 3 attempts)

```
where I stood -> where I pointed: reachable (23.7 m apart, 1557 cells filled, via 3 in-scene edges)
  The ground IS connected, so the walk was not blocked by the world. The likely causes are the executor giving up (a narrow gap, a step it could not take at its 150 ms burst) or a body-box snag that the cell fill does not model — confirm with tools/walk_bodygate.mjs.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260804-014` (captured at c5224ee0)

### PT-20260804-015 — Duplicate word 'the' in cook interaction prompt

- **status** REFUTED (tools/reach_probe.mjs (in the running page))
- **severity** P1 · **kind** bug · **found by** agent
- **I was doing** Standing near the cook inside the cookhouse
- **I expected** The prompt banner should read 'Talk to the cook? [E]'.
- **What happened** The prompt banner displays 'Talk to the the cook? [E]' with 'the' repeated.

```
where I stood -> where I pointed: reachable (4.6 m apart, 39 cells filled on foot)
  The ground IS connected, so the walk was not blocked by the world. The likely causes are the executor giving up (a narrow gap, a step it could not take at its 150 ms burst) or a body-box snag that the cell fill does not model — confirm with tools/walk_bodygate.mjs.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260804-015` (captured at 06fc4924)

### PT-20260805-002 — Character stuck on narrow wooden plank bridge

- **status** REFUTED (tools/reach_probe.mjs (in the running page))
- **severity** P1 · **kind** bug · **found by** agent
- **I was doing** Trying to walk to the left towards the head-gate winches or back to the right platform.
- **I expected** The character should move along the walkway or step off the plank.
- **What happened** The character is stuck on the plank at (0.43, 0.42) and all movement attempts fail to close any distance.

```
where I stood -> where I pointed: reachable (24.1 m apart, 1649 cells filled, via 3 in-scene edges)
  The ground IS connected, so the walk was not blocked by the world. The likely causes are the executor giving up (a narrow gap, a step it could not take at its 150 ms burst) or a body-box snag that the cell fill does not model — confirm with tools/walk_bodygate.mjs.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-002` (captured at 9896586b)

### PT-20260805-003 — Character stuck in place on central wooden platform

- **status** REFUTED (tools/reach_probe.mjs (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** Trying to walk towards the objective markers or back down the path.
- **I expected** My character should move to where I click.
- **What happened** My character is completely stuck in place and won't move no matter where I click on the platform.

```
where I stood -> where I pointed: reachable (8.1 m apart, 386 cells filled, via 2 in-scene edges)
  The ground IS connected, so the walk was not blocked by the world. The likely causes are the executor giving up (a narrow gap, a step it could not take at its 150 ms burst) or a body-box snag that the cell fill does not model — confirm with tools/walk_bodygate.mjs.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-003` (captured at 37ce4161)

### PT-20260805-006 — Cannot walk to the head-gate winches at Lock Five

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I was trying to walk to the winches under the shelter to complete my objective.
- **I expected** I expected to be able to walk up to the winches and interact with them.
- **What happened** I keep getting told the area around the winches is not ground I can walk to, so I can't reach the objective.

```
where I stood -> where I pointed: reachable (0.3 m apart, 1 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [20.5,24.07,-6.49], 0.29 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-006` (captured at edde27bc)

### PT-20260805-007 — Cannot interact with the two figures on the path

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I walked up to the two people standing on the path of footprints and tried to talk to them.
- **I expected** I expected to be able to interact with them to progress the objective.
- **What happened** I pressed the interact button multiple times while standing right next to them, but nothing happened.

```
where I stood -> where I pointed: reachable (0.6 m apart, 1 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [36.22,0.46,-17.58], 0.56 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-007` (captured at 08dd3d04)

### PT-20260805-008 — Cannot interact with Poppy at her stall

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** blocker · **found by** stuck-interview
- **I was doing** I'm trying to talk to Poppy at her stall to progress the objective.
- **I expected** When I stand next to the figures under the red marker and press interact, a conversation should start.
- **What happened** I'm standing right at the red marker next to the figures, but pressing interact does absolutely nothing. I've tried moving around and pressing it from different angles, but I'm stuck.

```
where I stood -> where I pointed: reachable (2.0 m apart, 18 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [45.6,0.46,-20.53], 0.54 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-008` (captured at 08dd3d04)

### PT-20260805-009 — Overlapping interaction prompts for 'Leave Item Shop' and 'Talk to shopkeeper'

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I was trying to leave the item shop after talking to the shopkeeper.
- **I expected** I expected to be able to press E to leave the shop.
- **What happened** The 'Leave Item Shop? [E]' prompt is overlapping with the 'Talk to the shopkeeper? [E]' prompt. Because they both use the same key, pressing E just makes me talk to the shopkeeper again instead of leaving.

```
where I stood -> where I pointed: reachable (1.5 m apart, 1 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [4.79,0,-5.55], 0.54 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-009` (captured at 08dd3d04)

### PT-20260805-010 — Old Gate exit loops back to Village Square

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** blocker · **found by** agent
- **I was doing** Walking north towards The Old Gate to leave the village per the objective.
- **I expected** Walking north through The Old Gate should transition to the world map or area outside the village.
- **What happened** Crossing the northern exit zone at The Old Gate repeatedly transitions back to the Village Square, creating an infinite scene loop.

```
where I stood -> where I pointed: reachable (2.8 m apart, 39 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [58.88,0.26,-14.73], 0.6 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-010` (captured at 764c561f)

### PT-20260805-015 — Reached the red objective marker at The Lockhead but nothing happens

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** blocker · **found by** stuck-interview
- **I was doing** I was trying to find the lockhead by walking to the red marker under the roof of The Lockhead building.
- **I expected** I expected to find a person to talk to, get an interaction prompt, or have the objective update when I reached the marker.
- **What happened** I walked right up to the area under the red marker, but there's no one to interact with, no prompt appears, and the objective hasn't changed. I'm just stuck here.

```
where I stood -> where I pointed: reachable (0.3 m apart, 1 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [20.83,24.07,-6.26], 0.34 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-015` (captured at b8b6f12a)

### PT-20260805-017 — Transition trigger for 'Shelf street' blocks access to 'The Lockhead' objective

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I was trying to walk over to the NPC under 'The Lockhead' marker to complete my objective.
- **I expected** I expected to be able to walk onto the porch/deck area and talk to the NPC.
- **What happened** The trigger zone for 'Down to the Shelf street? [E]' seems to cover the whole path. I keep hitting it and can't seem to walk past it to get to the building where the objective is.

```
where I stood -> where I pointed: reachable (0.4 m apart, 1 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [20.74,24.07,-5.89], 0.39 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-017` (captured at b8b6f12a)

### PT-20260805-018 — Cannot walk to 'The Lockhead' NPC, ground marked as not walkable

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** Trying to walk up to the NPC under the red 'The Lockhead' marker to progress the objective.
- **I expected** My character should walk up to the NPC so I can interact with them.
- **What happened** I can't get close to the NPC. The game keeps saying the ground around them isn't walkable, and I just end up stuck near the 'Down to the Shelf street' transition trigger.

```
where I stood -> where I pointed: reachable (0.3 m apart, 1 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [20.71,24.07,-6.03], 0.27 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-018` (captured at b8b6f12a)

### PT-20260805-026 — Character stuck behind wooden pillars under circular deck

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I was trying to walk over to the girl on the dock to talk to her.
- **I expected** I expected my character to walk around the wooden supports and reach the girl.
- **What happened** My character got stuck behind the vertical support pillars under the large circular deck and couldn't move past them to get to the dock.

```
where I stood -> where I pointed: reachable (4.5 m apart, 35 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [74.58,1.25,-29.23], 0.53 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-026` (captured at 44e93c6b)

### PT-20260805-032 — Player gets stuck on geometry at far right of upper wooden platform

- **status** REFUTED against the game · VERIFIED against the harness (tools/_court_probe.mjs --way/--at + tools/playtest/seen_probe.mjs + tools/playtest/wayfind_probe.mjs)
- **severity** P1 · **kind** blocker · **found by** stuck-interview
- **I was doing** I walked to the far right end of the upper wooden walkway and then tried to turn around and walk back left.
- **I expected** I should be able to walk back along the path I came from.
- **What happened** I got stuck on the environment and couldn't move left or anywhere else.

```
STRAIGHT-LINE DRIVE TO THE CLICKED POINT: stalls (this triage run).
BUT THE WORLD IS OPEN. _court_probe --way from the same cell [58.11,14.24,-12.8] toward the
route the game routes through (east, the quay-west>weave cut) walks 3/3 legs BOTH ways, ending
[61.99,14.07,-14.39] / [58.63,14.39,-12.98], stalled: no. --at: ground clear east and south;
only ls_rail west, a fence doing its job. The claim under test was 'trapped, cannot move in any
direction', and that is FALSE.
WHY THE STRAIGHT DRIVE STALLS: every point the agent clicked was WEST (x 33-53) or on the tier
5 m above (y 19.07). SIM.move is not a pathfinder, and reach_probe's own answer says so --
'reachable via 3 in-scene edges', i.e. by taking a cut, not by pushing through the fence.
THE DEFECT IS THE AIM, AND ITS CAUSE IS MEASURED: seen_probe puts the body at charNdc
[-0.623,0.238] = screen [241,274] of 1280x720 with 353/428 pixels through the plate, while the
ticket says 'far right of the platform'; wayfind_probe --from=ch2.maren (the run's own state)
shows the routed 'Lock Five' arrow at nx 0.076, lift 22 px, its click landing on
walk_e_quay-deck__pilot-cluster_landing. The agent aimed nx 0.30-0.86 on 29 consecutive steps.
Fixed in the percept (690c1d4): percept.you + percept.markers. FIXLOG round 23.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-032` (captured at fca1c303)

### PT-20260805-033 — Stuck in geometry at far right platform

- **status** REFUTED against the game · VERIFIED against the harness (tools/_court_probe.mjs --way/--at + tools/playtest/seen_probe.mjs + tools/playtest/wayfind_probe.mjs)
- **severity** P1 · **kind** blocker · **found by** agent
- **I was doing** Trying to walk back left towards the lower lock apron
- **I expected** Character should be able to navigate back along the upper walkway
- **What happened** Character is trapped in geometry at the far right and pathfinding fails to move in any direction

```
STRAIGHT-LINE DRIVE TO THE CLICKED POINT: stalls (this triage run).
BUT THE WORLD IS OPEN. _court_probe --way from the same cell [58.11,14.24,-12.8] toward the
route the game routes through (east, the quay-west>weave cut) walks 3/3 legs BOTH ways, ending
[61.99,14.07,-14.39] / [58.63,14.39,-12.98], stalled: no. --at: ground clear east and south;
only ls_rail west, a fence doing its job. The claim under test was 'trapped, cannot move in any
direction', and that is FALSE.
WHY THE STRAIGHT DRIVE STALLS: every point the agent clicked was WEST (x 33-53) or on the tier
5 m above (y 19.07). SIM.move is not a pathfinder, and reach_probe's own answer says so --
'reachable via 3 in-scene edges', i.e. by taking a cut, not by pushing through the fence.
THE DEFECT IS THE AIM, AND ITS CAUSE IS MEASURED: seen_probe puts the body at charNdc
[-0.623,0.238] = screen [241,274] of 1280x720 with 353/428 pixels through the plate, while the
ticket says 'far right of the platform'; wayfind_probe --from=ch2.maren (the run's own state)
shows the routed 'Lock Five' arrow at nx 0.076, lift 22 px, its click landing on
walk_e_quay-deck__pilot-cluster_landing. The agent aimed nx 0.30-0.86 on 29 consecutive steps.
Fixed in the percept (690c1d4): percept.you + percept.markers. FIXLOG round 23.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-033` (captured at fca1c303)

### PT-20260805-034 — Character stuck on central wooden platform unable to move

- **status** REFUTED against the game · VERIFIED against the harness (tools/_court_probe.mjs --way/--at + tools/playtest/seen_probe.mjs + tools/playtest/wayfind_probe.mjs)
- **severity** P1 · **kind** blocker · **found by** agent
- **I was doing** Attempting to walk left towards the stairs to reach Lock Five
- **I expected** Vesper should move along the walkway towards the targeted ground coordinates
- **What happened** Vesper remains fixed at x=0.43, y=0.42 regardless of target coordinates, failing to navigate in any direction.

```
STRAIGHT-LINE DRIVE TO THE CLICKED POINT: stalls (this triage run).
BUT THE WORLD IS OPEN. _court_probe --way from the same cell [58.11,14.24,-12.8] toward the
route the game routes through (east, the quay-west>weave cut) walks 3/3 legs BOTH ways, ending
[61.99,14.07,-14.39] / [58.63,14.39,-12.98], stalled: no. --at: ground clear east and south;
only ls_rail west, a fence doing its job. The claim under test was 'trapped, cannot move in any
direction', and that is FALSE.
WHY THE STRAIGHT DRIVE STALLS: every point the agent clicked was WEST (x 33-53) or on the tier
5 m above (y 19.07). SIM.move is not a pathfinder, and reach_probe's own answer says so --
'reachable via 3 in-scene edges', i.e. by taking a cut, not by pushing through the fence.
THE DEFECT IS THE AIM, AND ITS CAUSE IS MEASURED: seen_probe puts the body at charNdc
[-0.623,0.238] = screen [241,274] of 1280x720 with 353/428 pixels through the plate, while the
ticket says 'far right of the platform'; wayfind_probe --from=ch2.maren (the run's own state)
shows the routed 'Lock Five' arrow at nx 0.076, lift 22 px, its click landing on
walk_e_quay-deck__pilot-cluster_landing. The agent aimed nx 0.30-0.86 on 29 consecutive steps.
Fixed in the percept (690c1d4): percept.you + percept.markers. FIXLOG round 23.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-034` (captured at fca1c303)

### PT-20260805-040 — Walk blocked: the body closed 0 m of an intended 11.33 m, twice at the same place

- **status** THE HOLE IS VERIFIED · THE MECHANISM IS STILL UNNAMED · ONE SUSPECT REFUTED (tools/_court_probe.mjs --at/--way + tools/scenegraph_derive.mjs + docs/qa/playtest/runs/run-20260805-121612/run.jsonl)
- **severity** P1 · **kind** blocker · **found by** walk-executor
- **I was doing** I tried to walk to a point on screen at [0.58, 0.75]; my goal was "Walk up the walkway and stairs towards Keepers' Cottage at [0.558, 0.264]".
- **I expected** To walk about 11.33 m and arrive there.
- **What happened** The character moved 0 m and stopped 11.33 m short — twice in this run. All five headings were pushed (5 bursts at ~157 ms each) and none of them moved the body, so this is the world refusing rather than the harness running out of time. Something is in the way, or that ground is not connected to where I was standing.

```
THE HOLE IS REAL. --at along z -24.0: the weave deck's last floor is x 73.2 at y 7.90, x 73.6
is cx_rail at 7.53, and from x 74.0 east there is NO floor at all above the river plane at
y -3.90. The run went [70.41,7.87,-25.48] (step 25) -> [74.05,-3.90,-23.98] (step 26) and sat
there for seven steps.

A SUSPECT WAS RAISED AND REFUTED IN THE SAME PASS, WHICH IS WHY IT IS WRITTEN DOWN. The
scenegraph's lockfive>weave arrival spawn is [72.452,7.75,-24.338] — 1.64 m in plan from the
landing — and _court_probe --at reports EVERY floor there (7.90/7.87/7.81) blocked by cx_rail,
with nothing below until -3.90. That looked like the answer. IT IS NOT: --way tp'd to that
exact spawn walks 2/2 legs to [70.71,7.87,-25.03] and 2/2 back, no stall, either direction.
LESSON, and it is the same shape as round 24's: --at's second column answers 'what intersects
a body box raised at this floor', NOT 'can a body stand here' — the settle picks a workable
floor and the drive proves it. Do not read a blocker name as a verdict.
scenegraph_derive emits NO warning for that arrival, and its ARRIVAL vs CAMERA-CUT BANDS table
passes it.

STILL UNNAMED: what moved the body 11.8 m down. walkStep provably refuses to walk off that lip
under WALKLOCK and jump is disabled in a routed town. Remaining candidates, none measured:
sgCorrect, the marooned unstick, or a cut spawn taken mid-fall. Naming it needs an instrumented
page that logs P.y per tick across the transition, not another fill.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-040` (captured at e9bf1ba7)

### PT-20260805-041 — Character stuck on bottom right dock geometry

- **status** THE HOLE IS VERIFIED · THE MECHANISM IS STILL UNNAMED · ONE SUSPECT REFUTED (tools/_court_probe.mjs --at/--way + tools/scenegraph_derive.mjs + docs/qa/playtest/runs/run-20260805-121612/run.jsonl)
- **severity** P1 · **kind** blocker · **found by** agent
- **I was doing** Trying to walk towards Keepers' Cottage from the lower dock area at [0.605, 0.945]
- **I expected** Character should walk along the navmesh towards the destination
- **What happened** Every goto action results in 0m closed over four consecutive turns; character appears completely stuck.

```
THE HOLE IS REAL. --at along z -24.0: the weave deck's last floor is x 73.2 at y 7.90, x 73.6
is cx_rail at 7.53, and from x 74.0 east there is NO floor at all above the river plane at
y -3.90. The run went [70.41,7.87,-25.48] (step 25) -> [74.05,-3.90,-23.98] (step 26) and sat
there for seven steps.

A SUSPECT WAS RAISED AND REFUTED IN THE SAME PASS, WHICH IS WHY IT IS WRITTEN DOWN. The
scenegraph's lockfive>weave arrival spawn is [72.452,7.75,-24.338] — 1.64 m in plan from the
landing — and _court_probe --at reports EVERY floor there (7.90/7.87/7.81) blocked by cx_rail,
with nothing below until -3.90. That looked like the answer. IT IS NOT: --way tp'd to that
exact spawn walks 2/2 legs to [70.71,7.87,-25.03] and 2/2 back, no stall, either direction.
LESSON, and it is the same shape as round 24's: --at's second column answers 'what intersects
a body box raised at this floor', NOT 'can a body stand here' — the settle picks a workable
floor and the drive proves it. Do not read a blocker name as a verdict.
scenegraph_derive emits NO warning for that arrival, and its ARRIVAL vs CAMERA-CUT BANDS table
passes it.

STILL UNNAMED: what moved the body 11.8 m down. walkStep provably refuses to walk off that lip
under WALKLOCK and jump is disabled in a routed town. Remaining candidates, none measured:
sgCorrect, the marooned unstick, or a cut spawn taken mid-fall. Naming it needs an instrumented
page that logs P.y per tick across the transition, not another fill.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-041` (captured at e9bf1ba7)

### PT-20260805-053 — Walk blocked: the body closed 0 m of an intended 10.13 m, twice at the same place

- **status** VERIFIED (tools/reach_probe.mjs (in the running page))
- **severity** P1 · **kind** blocker · **found by** walk-executor
- **I was doing** I tried to walk to a point on screen at [0.51, 0.33]; my goal was "Walk up the elevated walkway towards the top-right exit marker at [0.573, 0.243]".
- **I expected** To walk about 10.13 m and arrive there.
- **What happened** The character moved 0 m and stopped 10.13 m short — twice in this run. All five headings were pushed (5 bursts at ~157 ms each) and none of them moved the body, so this is the world refusing rather than the harness running out of time. Something is in the way, or that ground is not connected to where I was standing.

```
where I stood -> where I pointed: UNREACHABLE — [74.66,2,-27.47] -> [83.98,7.38,-23.49]: 1 cells filled from the start, 1 from the target, and they never meet. Nearest standable cell to the target is 10.1 m away (at 74.8,1.12,-27.6, 6.26 m off in height); the two regions come within 10.03 m of each other between [74.8,1.12,-27.6] and [84,7.38,-23.6] — a 6.26 m step.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-053` (captured at a2461edd)

### PT-20260805-042 — Keepers' Cottage exit teleports player back to lower dock loop

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** agent
- **I was doing** Walking into the Keepers' Cottage transition marker at [0.55, 0.32]
- **I expected** To transition inside the Keepers' Cottage to progress the objective
- **What happened** The scene reloads and respawns my character at the bottom dock at [0.375, 0.565] in a loop.

```
where I stood -> where I pointed: reachable (4.7 m apart, 65 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [90.53,-0.15,-27.71], 0.59 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-042` (captured at 8ce6d0a3)

### PT-20260805-044 — Clicking upper level objective marker causes character to walk underneath it

- **status** PARTIAL (tools/playtest/wayfind_probe.mjs + tools/_court_probe.mjs --way)
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I was trying to go up to the Keepers' Cottage by clicking the objective marker and the stairs.
- **I expected** I expected my character to automatically pathfind up the stairs to reach the upper level, or for clicking the stairs to let me walk up them.
- **What happened** My character just walked underneath the upper platform on the lower dock. When I tried clicking the stairs manually, it either didn't move me much or said it wasn't ground.

```
round 28: root named and fixed in public/js/story_runtime.js (wayAim reads <town>.routes.json and aims the routed arrow at the furthest route vertex the body can reach in a straight line, gated by an in-page march of SIM.walkFloors+SIM.blocked under walkGround's own step window). Measured with tools/playtest/wayfind_probe.mjs (real Chrome, the shipped projection), frames pinned in docs/qa/playtest/wayfind-r28-*, and the aim driven with tools/_court_probe.mjs --way. THE ARROW IS FIXED: it moved from [713,291] (5.0 m overhead, picking the laundry decks) to [608,~466], aim [75.00,1.93,-27.70] on the switchbacks lower flight, SIM.pick returning wv_planking. THE REMAINING HALF IS A WORLD DEFECT, split out as PT-20260805-047: the stand [76.15,1.32,-27.11] is a one-way pocket — SIM.move drives out of it EAST only (0.00 m south, 0.11 m west, 0.22 m north, 0.30 m north-west) while every reverse drive walks back into it.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-044` (captured at 0d6c0c0f)

### PT-20260805-045 — Stuck on plank bridge due to missing walkable ground navmesh

- **status** FIXED (tools/playtest/wayfind_probe.mjs + tools/_court_probe.mjs --way/--grid)
- **severity** P1 · **kind** bug · **found by** agent
- **I was doing** Trying to walk along the plank bridge to satisfy the objective
- **I expected** The player character should be able to walk along the wooden plank bridge surface
- **What happened** Multiple movement attempts in all directions on the bridge failed with 'is not ground you can walk to', leaving me stuck

```
round 28: root named and fixed in public/js/story_runtime.js (wayAim reads <town>.routes.json and aims the routed arrow at the furthest route vertex the body can reach in a straight line, gated by an in-page march of SIM.walkFloors+SIM.blocked under walkGround's own step window). Measured with tools/playtest/wayfind_probe.mjs (real Chrome, the shipped projection), frames pinned in docs/qa/playtest/wayfind-r28-*, and the aim driven with tools/_court_probe.mjs --way. Cottage: the arrow moved from [568,686] (the seam, across a 1.5 m hole 2.6 m down) to [405,~627], aim [91.27,7.75,-22.13]; SIM.pick at its own pixel returns walk_e_lockhead__keepers-cottage_l16 (the spur the body is on); _court_probe --way drives that chord clean in BOTH directions from the cottage door. Past the junction the aim withdraws by itself and the arrow is round 19s plain lift clamp on the bridge.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-045` (captured at 0d6c0c0f)

### PT-20260805-046 — Cannot navigate to Lock Five exit from broken bridge

- **status** FIXED (tools/playtest/wayfind_probe.mjs + tools/_court_probe.mjs --way/--grid)
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** Trying to walk down the broken plank bridge to reach the 'Lock Five' exit arrow at the bottom of the screen.
- **I expected** My character should walk down the structure and reach the exit.
- **What happened** I seem to be stuck on the broken bridge pieces. Clicking near the exit arrow doesn't move my character there, and I can't find a path down.

```
round 28: root named and fixed in public/js/story_runtime.js (wayAim reads <town>.routes.json and aims the routed arrow at the furthest route vertex the body can reach in a straight line, gated by an in-page march of SIM.walkFloors+SIM.blocked under walkGround's own step window). Measured with tools/playtest/wayfind_probe.mjs (real Chrome, the shipped projection), frames pinned in docs/qa/playtest/wayfind-r28-*, and the aim driven with tools/_court_probe.mjs --way. Cottage: the arrow moved from [568,686] (the seam, across a 1.5 m hole 2.6 m down) to [405,~627], aim [91.27,7.75,-22.13]; SIM.pick at its own pixel returns walk_e_lockhead__keepers-cottage_l16 (the spur the body is on); _court_probe --way drives that chord clean in BOTH directions from the cottage door. Past the junction the aim withdraws by itself and the arrow is round 19s plain lift clamp on the bridge.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-046` (captured at 0d6c0c0f)

### PT-20260805-054 — Walk blocked: the body closed 0 m of an intended 8.45 m, twice at the same place

- **status** VERIFIED (tools/reach_probe.mjs (in the running page))
- **severity** P1 · **kind** blocker · **found by** walk-executor
- **I was doing** I tried to walk to a point on screen at [0.54, 0.64]; my goal was "Walk along the curved platform to the right toward the exit arrow at [0.654, 0.736].".
- **I expected** To walk about 8.45 m and arrive there.
- **What happened** The character moved 0 m and stopped 8.45 m short — twice in this run. All five headings were pushed (5 bursts at ~158 ms each) and none of them moved the body, so this is the world refusing rather than the harness running out of time. Something is in the way, or that ground is not connected to where I was standing.

```
where I stood -> where I pointed: UNREACHABLE — [74.66,2,-27.47] -> [66.46,6.91,-29.5]: 1 cells filled from the start, 48 from the target, and they never meet. Nearest standable cell to the target is 8.6 m away (at 74.8,1.12,-27.6, 5.79 m off in height); the two regions come within 6.12 m of each other between [74.8,1.12,-27.6] and [68.8,6.91,-28.8] — a 5.79 m step.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-054` (captured at a2461edd)

### PT-20260805-047 — NPC blocking narrow bridge path

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** blocker · **found by** stuck-interview
- **I was doing** Trying to walk down the plank bridge towards the Lock Five objective.
- **I expected** To be able to walk down the bridge.
- **What happened** Another character is standing in the middle of the narrow bridge, blocking my path, and I can't get around them.

```
where I stood -> where I pointed: reachable (1.1 m apart, 1 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [91.15,8.5,-21.14], 0.55 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-047` (captured at f10d3ca3)

### PT-20260805-049 — Moorage deck at [76.15,1.32,-27.11] is a one-way pocket: the body can only leave eastward

- **status** FIXED (tools/_court_probe.mjs --way (SIM.move, the drive, 400 ticks per leg))
- **severity** P1 · **kind** bug · **found by** lane
- **I was doing** Walking from the moorage toward the switchback up to the weave tier, following the routed Keepers Cottage arrow.
- **I expected** A body standing on the moorage deck can walk to the foot of the stair one metre south.
- **What happened** The leg closed 0.06 m of 2.4 m. Split out of PT-20260805-044, whose HUD half (an arrow drawn 5 m above the tier) is fixed in round 28 — this is the world half and no arrow can cure it.

```
From [76.15,1.32,-27.11] on the moorage deck the body drives EAST to [76.74,1.32,-27.15] cleanly and stalls in every other heading: south to [76.15,1.32,-28.2] travels 0.00 m, west to [75.2,1.3,-27.0] 0.11 m, north to [76.15,1.32,-26.2] 0.22 m, north-west to [74.6,1.25,-26.75] 0.30 m. The REVERSE drives all walk back INTO it. The columns around it carry walk_e_weave-huts__moorage_l2_t03/t04 treads at 1.19-1.32 — the deck height itself — so a body standing at 1.32 is wedged against the flights own treads. | FIXED round 29 (a2461ed): the south wall was cx_rail at z 2.12 -- RAIL_H over the OLD 1.70 foot, never re-derived when 8752b87 lowered the floor; and behind it the un-migrated switchback itself (l1 over l2 in the body window, both hairpins). STAIRS_V2 += weave-huts__moorage with weave/locksfoot/cx re-run in the same window; town_blockout grew lay_stair_rails (a rail may not stand in a body window of its own edge). _court_probe --way: DOWN 12/12 legs clean, UP threads; run-20260805-163944 walked moorage->weave->crossing->cottage and fired ch2.supper.
```
- **repro** none

### PT-20260805-050 — weave shot: the routed Lock Five arrow sits at the frame edge on wv_piles, and every click on it fails

- **status** FIXED (tools/playtest/wayfind_probe.mjs --from ch2.winches --stations weave)
- **severity** P1 · **kind** bug · **found by** lane
- **I was doing** Crossing into the weave shot and walking at the one labelled Lock Five arrow.
- **I expected** The arrow marks ground the player can walk to, inside the frame.
- **What happened** Five separate steps (7, 9, 19, 21, 23) drove at nx 0.10-0.11 and each returned "is not ground you can walk to"; the agent bounced weave<->crossing for eighteen steps. Round 5 fixed the LABEL being half off frame and round 19 the arrow being lifted onto scenery; this is the seam itself projecting to the margin, which neither covers.

```
In shot weave standing at [72.4,7.87,-23.56] the routed weave>lockfive arrow draws at [128,468] of 1280x720 — nx 0.100, the frames LEFT MARGIN — and SIM.pick at its own drawn pixel returns wv_piles, a stilt. The seam itself projects to [139,488]; the aim correctly does NOT engage, because from the weave tier the straight line to the seam IS ground. Frame: docs/qa/playtest/wayfind-r28-weave/weave arrival.jpg. | FIXED round 29 (565ba15): weave yaw 118 -> 142 (seam nx 0.104 -> 0.203, ground/chest/head occluder rays clear, charPxFar 54 >= 50 floor, region 81.3% vs 90.6%), one plate baked. run-20260805-170550 took the weave>lockfive cut AT STEP 9 and the Chapter Two END CARD was drawn and perceived at step 12.
```
- **repro** none

### PT-20260805-051 — Stuck on plank bridge, cannot move up or down

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** blocker · **found by** stuck-interview
- **I was doing** Trying to walk along the plank bridge, either up towards the top right or down following the routing arrow to Lock Five.
- **I expected** To be able to walk up or down the bridge to continue exploring or follow the objective.
- **What happened** I keep getting told the areas I click are not ground I can walk to, leaving me stuck in place on the ramp.

```
where I stood -> where I pointed: reachable (1.2 m apart, 1 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [89.12,10.3,-19.06], 0.57 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-051` (captured at a03eb7b2)

### PT-20260805-052 — Character stuck behind wooden pillars under curved platform

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** Trying to walk along the lower walkway towards the exit markers.
- **I expected** I expected to be able to walk along the path to the next area.
- **What happened** My character got stuck behind the vertical wooden pillars supporting the platform above and I can't move in any direction.

```
where I stood -> where I pointed: reachable (2.4 m apart, 27 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [74.91,1.25,-30.11], 0.59 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-052` (captured at a2461edd)

### PT-20260805-055 — The player can leave the chapter on its first frame, and the objective follows them out

- **status** FIXED (tools/_court_probe.mjs --way (SIM.move in the running game) + tools/routes_derive.mjs --check + tools/playthrough_test.mjs)
- **severity** P1 · **kind** bug · **found by** spine-detector
- **I was doing** I read the opening narration by pressing the action button, then used the only prompt on screen.
- **I expected** To carry on with the objective the game was showing me.
- **What happened** I ended up somewhere with no way to advance the story, and the objective on screen ("Step through the Old Gate") still refers to where I was. Nothing here can continue the chapter.

```
Fixed as filed, in the map: gate-court->sigil-gate carried no waypoints, so the routed polyline ran the holed centre line and wayAim failed closed over the channel head. The edge now carries the measured west-flank waypoints ([74.6,122.5],[74.6,125.0],[76.5,127.3] map coords, verbatim from the 4/4 drive in run-20260805-182057). routes_derive --check clean. Engine drive along the NEW routed polyline: 4/4 legs BOTH ways (forward terminus [77.99,2.66,-128.44], 1.56 m from the portal, inside its r 2.2). playthrough_test 86/0, findability 69/0, story gate green. The channel-head hole itself is untouched on purpose: THE FLANK IS THE DESIGN, and the fix class is one line of map plus one re-derive, exactly the doctrine's shape.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-055` (captured at 7e63a317)

### PT-20260805-057 — The player can leave the chapter on its first frame, and the objective follows them out

- **status** FIXED (the recorded run itself (run-20260805-194359 percepts) replayed through the amended detector)
- **severity** P1 · **kind** bug · **found by** spine-detector
- **I was doing** I read the opening narration by pressing the action button, then used the only prompt on screen.
- **I expected** To carry on with the objective the game was showing me.
- **What happened** I ended up somewhere with no way to advance the story, and the objective on screen ("Step through the Old Gate") still refers to where I was. Nothing here can continue the chapter.

```
Detector false positive by design, fixed in the harness (episode.mjs): the walk from the sigil court to the Old Gate takes more than three steps and the next un-fired beat (ch1.done) lives in ow-valley, so any correctly guided exit walk tripped the 3-step window — the SAME run fired ch1.done and crossed the corridor right after this filing. The filing sentence "nothing here can continue the chapter" is false whenever the routed wayhint arrow is drawn, so a step with a live routed marker no longer counts toward off-spine. Replayed over the recorded run: all 15 post-sendoff emb-cine steps carried the routed marker; the amended detector files nothing. An unguided exit (hint broken, edge sealed, marker off-screen 3 straight steps) still files exactly as before. percept_test 704/704.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-057` (captured at a7be573f)

### PT-20260806-002 — Character stuck on wooden plank bridge geometry at Lock Five

- **status** VERIFIED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** blocker · **found by** agent
- **I was doing** Attempting to walk down the plank bridge walkway to the Lock Five scene transition at [0.255, 0.889].
- **I expected** The character should walk down the bridge towards the exit arrow.
- **What happened** The character remains stuck at [0.365, 0.77] across multiple movement attempts, closing 0 meters.

```
where I stood -> where I pointed: reachable (1.3 m apart, 1 cells filled on foot)
  BUT THE DRIVE STALLS. SIM.move from the same start reached [90.22,8.68,-21.69] and stopped 1.29 m short, gaining nothing for 41 ticks. The lattice bridges what the stride and the body box cannot: this is a body trap, not an executor giving up. Name the mesh with tools/_court_probe.mjs --at / --way.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-002` (captured at c210feeb)

### PT-20260806-004 — The player can leave the chapter on its first frame, and the objective follows them out

- **status** VERIFIED (llm_playtester spine detector (public/game/story.json vs the running scene))
- **severity** P1 · **kind** bug · **found by** spine-detector
- **I was doing** I read the opening narration by pressing the action button, then used the only prompt on screen.
- **I expected** To carry on with the objective the game was showing me.
- **What happened** I ended up somewhere with no way to advance the story, and the objective on screen ("Through the Dellhollow gate — find whoever runs the locks") still refers to where I was. Nothing here can continue the chapter.

```
The body was in "ow-valley" for three consecutive steps while none of the next un-fired beats in story.json lives there. Beats fired at the time: ch1.open, ch1.waystone, ch1.reveal, ch1.rowan, ch1.lake.handoff, ch1.lake.wake, ch1.lake.hearth, ch1.lake.lamp, ch1.meet, ch1.lamps, ch1.hush, ch1.see.mara, ch1.see.poppy, ch1.see.finn, ch1.see.mochi, ch1.pact, ch1.sigils, ch1.sendoff, ch1.done, ch2.road. This is a mechanical fact about the game, not a model opinion — there is nothing left to measure. What to DO about it is a design decision.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-004` (captured at f21557cc)

### PT-20260805-058 — Exit trigger to The Emberbrook Valley does not activate when standing on marker

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** agent
- **I was doing** Trying to step through the Old Gate into The Emberbrook Valley by walking on and around the red marker [0.665, 0.191].
- **I expected** Walking onto or interacting near the exit marker should trigger a map transition to the next area.
- **What happened** My character is standing directly at the marker location [0.635, 0.15] and walking/interacting repeatedly does nothing.

```
where I stood -> where I pointed: reachable (1.1 m apart, 1 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [75.97,2.66,-127.17], 0.55 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-058` (captured at a7be573f)

### PT-20260805-059 — Overlapping interaction prompts for 'Leave' and 'Talk' use the same key

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** Trying to leave The Boatmen's Rest.
- **I expected** Pressing the interact button would let me leave the building.
- **What happened** The prompt to leave and the prompt to talk to the bargeman are both on screen and use the same key [E]. Pressing it keeps triggering the conversation instead of letting me leave.

```
where I stood -> where I pointed: reachable (1.2 m apart, 1 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [-2.58,0,-1.83], 0.53 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-059` (captured at a7be573f)

### PT-20260805-060 — Scene transition for 'The Lockhead' is not triggering

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I was trying to leave the area by walking onto the scene exit marker labelled 'The Lockhead'.
- **I expected** I expected to transition to the next scene or area.
- **What happened** I just stand on the marker and nothing happens, I can't leave the area.

```
where I stood -> where I pointed: reachable (1.0 m apart, 1 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [32.01,19.07,-8.02], 0.6 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-060` (captured at a7be573f)

### PT-20260805-062 — Cannot trigger 'The Lockhead' transition marker

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** blocker · **found by** stuck-interview
- **I was doing** I'm trying to follow the objective marker to 'The Lockhead' by walking onto the red arrow at the edge of the walkway.
- **I expected** Walking onto or past the red arrow should trigger a transition to the next screen or area.
- **What happened** I walked all over the marker and past it, but nothing happens. I'm stuck on this screen.

```
where I stood -> where I pointed: reachable (1.1 m apart, 1 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [33.38,19.07,-7.61], 0.53 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-062` (captured at a7be573f)

### PT-20260805-063 — Multiple actions bound to the same key [E] prevent leaving the room

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I was trying to leave The Boatmen's Rest by pressing the interact button [E].
- **I expected** I expected to exit the tavern and go back to Dellhollow.
- **What happened** Instead of leaving, pressing [E] kept triggering the dialogue with the bargeman because both the 'Leave' and 'Talk' prompts are active at the same time and use the same key.

```
where I stood -> where I pointed: reachable (1.7 m apart, 3 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [-2.9,-0.06,-1.79], 0.57 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-063` (captured at a7be573f)

### PT-20260805-064 — Interact button prioritizes bargeman dialogue over exiting room

- **status** FIXED (tools/_court_probe.mjs --comp/--who + adapter drive (real keys + E) in del-inn-int, both ways)
- **severity** P1 · **kind** bug · **found by** agent
- **I was doing** Pressing interact while standing at the Dellhollow exit point to leave the building.
- **I expected** Pressing interact should execute the primary/exit prompt 'Leave The Boatmen's Rest?'.
- **What happened** Pressing interact triggers dialogue with the nearby bargeman ('Still third...') every time instead of exiting.

```
The door was never region-unreachable: the exit pad [-3.4,0.04,-2.72] r 1.8 sits in the room's main walk component (377-cell fill contains it) and a real-key drive reaches 0.46 m from it. The reach probe's unreachable target [-3.61,0,0.81] is a 23-cell dead POCKET between the hearth and the settle (sealed at both mouths by hearth_dress_5/the fire-iron stand at [-3.62,z-0.78] and the settle's body shadow — _court_probe --who) that no body can enter; a click-target trap only. The player-facing defect was the KEY: ui_kit dispatches global keys in the CAPTURE phase and npc.js's chain consumed E whenever any villager was within 1.9 m, so play3d's bubble-phase door keydown never saw it — and the bargeman's reach covers the whole door pad. npc.js now yields E to a nearer live scene edge. Drive-verified: at [-3.6,-1.39] (the filing's own spot, door 1.35 m < bargeman 1.80 m) E exits to del-cine [23.94,19.07,-5.54]; at [-2.2,-1.5] (bargeman 0.45 m) E still talks. The double prompt banner remains the known PT-009/056 cosmetic.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-064` (captured at a7be573f)

### PT-20260805-065 — Infinite screen transition loop following 'The Lockhead' marker

- **status** REFUTED against the game · VERIFIED against the harness (run traces (runs 194359/211913/215044) + adapter drive reproduction + follow-the-arrow scripted bot)
- **severity** P1 · **kind** bug · **found by** agent
- **I was doing** Walking left toward 'The Lockhead' marker at [0.25, 0.62].
- **I expected** To reach the Lockhead location or continue along the path above Lock Five.
- **What happened** Walking to the marker at [0.25, 0.62] triggers a scene transition back to the previous village screen, which in turn immediately routes back to this screen.

```
There is no transition loop in the game: the shelf-west<->shelf-east cuts are the authored route to the Lockhead and a scripted bot that clicks the routed arrow crosses them once each and reaches the ch2.jam trigger. The loop was the EXECUTOR: (1) the hold/arrive deadband made every leg at the arrow a zero-metre "arrived" (fixed b957de5), (2) a flat ARRIVE_M floored clicks under 1.2 m so inching east never moved (fixed 3b5d7ce), (3) the agent aimed at midpoints between itself and the arrow, which under the toward-camera shelf-east shot resolve backwards or onto awnings (percept line now instructs aiming AT the arrow, e71b8e2). LLM receipt of the fixed executor is BLOCKED: Gemini prepaid credits depleted mid-round (429 RESOURCE_EXHAUSTED).
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-065` (captured at 71082c27)

### PT-20260805-066 — Wrong transition prompt appears at 'The Lockhead' marker

- **status** REFUTED against the game · VERIFIED against the harness (same as PT-20260805-065)
- **severity** P1 · **kind** blocker · **found by** stuck-interview
- **I was doing** I was trying to enter 'The Lockhead' to find the person who runs the locks.
- **I expected** I expected to see a prompt to enter The Lockhead or talk to someone when standing on the red marker.
- **What happened** The prompt says 'Down to the Shelf street? [E]' instead, and I can't seem to trigger the correct transition to progress the objective.

```
"Down to the Shelf street?" is the gate-stair passage prompt, correct where it stands; the agent was at the gate because its own midpoint-goto had carried it up there (same loop as PT-065). The routed arrow the objective needs was drawn and labelled on every one of those frames. Same harness class and same fixes as PT-065.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-066` (captured at 71082c27)

### PT-20260805-067 — Stuck on stairs trying to reach 'The Lockhead' exit marker

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** trying to walk down the stairs to trigger 'The Lockhead' exit.
- **I expected** I expected my character to walk all the way down the stairs and transition to the next area.
- **What happened** My character gets stuck on the stairs and stops moving before reaching the exit marker, preventing me from leaving the area.

```
where I stood -> where I pointed: reachable (0.9 m apart, 1 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [54.15,16.34,-11.25], 0.56 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-067` (captured at c210feeb)

### PT-20260806-001 — Cannot navigate up the stairs to reach the girl for the objective

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I was trying to walk up the wooden stairs to reach the girl standing there, to complete the 'Down to the lock apron' objective.
- **I expected** My character should walk up the stairs so I can interact with the girl.
- **What happened** My character gets stuck at the bottom of the stairs and cannot navigate up to her.

```
where I stood -> where I pointed: reachable (0.8 m apart, 143 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [73.21,1.25,-28.23], 0.54 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-001` (captured at c210feeb)

### PT-20260806-005 — Cannot walk across the long wooden bridge

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I was trying to walk left across the long wooden bridge with the boxes on it to continue towards my objective.
- **I expected** My character would walk across the bridge.
- **What happened** The game repeatedly told me the bridge is 'not ground you can walk to' and I couldn't cross it.

```
where I stood -> where I pointed: reachable (0.7 m apart, 1 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [64.66,14.07,-14.37], 0.59 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-005` (captured at f21557cc)

### PT-20260806-006 — Wooden bridge navmesh is missing or unwalkable

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** agent
- **I was doing** Trying to walk left across the wooden bridge towards Lock Five.
- **I expected** The character should be able to walk onto and across the wooden bridge deck.
- **What happened** All points on the bridge deck return 'not ground you can walk to', leaving the path forward blocked.

```
where I stood -> where I pointed: reachable (0.7 m apart, 1 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [64.66,14.07,-14.37], 0.59 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-006` (captured at f21557cc)

### PT-20260806-011 — Cannot walk across the wooden bridge; 'not ground' error

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** blocker · **found by** stuck-interview
- **I was doing** I was trying to walk across the wooden bridge to the left.
- **I expected** I expected to be able to walk along the bridge deck.
- **What happened** The game keeps telling me the bridge is 'not ground you can walk to', so I am stuck and cannot cross it.

```
where I stood -> where I pointed: reachable (2.8 m apart, 23 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [66.79,14.07,-14.69], 0.58 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-011` (captured at f21557cc)

### PT-20260806-014 — Cannot walk left across the wooden bridge

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I was trying to walk left across the long wooden bridge to find the lockhead.
- **I expected** I expected to be able to walk along the bridge deck since it looks like a clear path.
- **What happened** The game keeps telling me the bridge is 'not ground you can walk to' and I can't move left at all.

```
where I stood -> where I pointed: reachable (1.5 m apart, 2 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [66.6,14.07,-14.6], 0.57 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-014` (captured at ae3dfb12)

### PT-20260806-026 — Lock Five zone transition trigger not activating

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** agent
- **I was doing** Walking directly onto the routed Lock Five transition marker at [0.514, 0.464].
- **I expected** The area should transition to Lock Five / lock apron when stepping on the red transition arrow.
- **What happened** The character reaches [0.53, 0.455] right on the marker, but no zone transition occurs.

```
where I stood -> where I pointed: reachable (1.7 m apart, 3 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [61.2,11.6,-19.01], 0.56 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-026` (captured at d9b5ff70)

### PT-20260806-029 — Exit label 'Lock Five' jumps to player's location

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** Trying to follow the objective to Lock Five.
- **I expected** The exit label to stay in its correct location so I can navigate to it.
- **What happened** The red arrow and 'Lock Five' label keep glitching and jumping from the actual exit down below to right next to my character. Clicking it when it's next to me doesn't trigger the transition.

```
where I stood -> where I pointed: reachable (1.5 m apart, 1 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [61.25,11.6,-19.06], 0.55 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-029` (captured at d9b5ff70)

### PT-20260806-030 — Cannot pathfind to Lock Five transition from upper walkway

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** Trying to click the Lock Five transition arrow to leave the area.
- **I expected** The character should walk down the walkways to the transition and leave the scene.
- **What happened** The character barely moves and pathfinding fails, leaving me stuck on the upper walkway.

```
where I stood -> where I pointed: reachable (1.1 m apart, 1 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [61.35,11.6,-19.19], 0.53 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-030` (captured at d9b5ff70)

### PT-20260806-036 — Pathfinding fails when trying to reach the Lock Five exit

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I was trying to follow the objective marker to the 'Lock Five' exit.
- **I expected** My character should automatically walk to the exit and transition to the next area.
- **What happened** My character gets stuck and stops moving shortly after I click the exit. Also, the exit marker seems to jump between two different locations on the screen.

```
where I stood -> where I pointed: reachable (0.9 m apart, 1 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [60.36,11.6,-19.34], 0.58 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-036` (captured at 8ba970bc)

### PT-20260806-038 — Cannot pathfind down to Lock Five exit marker from upper platform

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P1 · **kind** bug · **found by** stuck-interview
- **I was doing** I'm clicking on the 'Lock Five' exit marker to leave the area.
- **I expected** My character should find a path down to the marker and exit.
- **What happened** My character just stands on the wooden platform above the marker and won't walk down to it.

```
where I stood -> where I pointed: reachable (0.5 m apart, 1 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [57.22,14.24,-17.1], 0.47 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260806-038` (captured at 5c53dd3f)

### PT-20260804-009 — Cannot interact with NPCs inside The Boatmen's Rest

- **status** REFUTED (tools/reach_probe.mjs (in the running page))
- **severity** P2 · **kind** confusion · **found by** stuck-interview
- **I was doing** I walked up to the two characters standing in the middle of the room and tried to talk to them.
- **I expected** I expected a conversation to start, or at least a prompt to appear so I could interact with them.
- **What happened** Nothing happened when I pressed the interact button. There is no prompt and they don't respond at all.

```
where I stood -> where I pointed: reachable (1.1 m apart, 1 cells filled on foot)
  The ground IS connected, so the walk was not blocked by the world. The likely causes are the executor giving up (a narrow gap, a step it could not take at its 150 ms burst) or a body-box snag that the cell fill does not model — confirm with tools/walk_bodygate.mjs.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260804-009` (captured at 9534b95d)

### PT-20260805-016 — Area transition trigger blocks path to objective building

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P2 · **kind** bug · **found by** stuck-interview
- **I was doing** I was trying to walk into The Lockhead building to reach the red objective marker.
- **I expected** I expected to be able to walk up to the building and find the person I'm looking for.
- **What happened** The trigger to leave the area ('Down to the Shelf street?') is placed right in the path to the building. I keep hitting it and getting the prompt instead of being able to easily walk past it to the objective.

```
where I stood -> where I pointed: reachable (0.4 m apart, 1 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [20.74,24.07,-5.89], 0.39 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-016` (captured at b8b6f12a)

### PT-20260805-056 — Overlapping interaction prompts near shop exit

- **status** REFUTED (tools/reach_probe.mjs + SIM.move (in the running page))
- **severity** P2 · **kind** bug · **found by** stuck-interview
- **I was doing** Walking to the door to leave the item shop.
- **I expected** A clean 'Leave Item Shop? [E]' prompt.
- **What happened** The 'Leave Item Shop' prompt is overlapping with the 'Talk to shopkeeper' prompt, making it look like 'Ta Leave Item Shop? [E] [E]'.

```
where I stood -> where I pointed: reachable (1.4 m apart, 1 cells filled on foot)
  The ground is connected AND SIM.move drives it (ended [5.22,0.03,-5.19], 0.57 m from the target). So the world did not block the walk — the likely cause is the executor giving up at its 150 ms burst, or the way being unreadable rather than unwalkable.
```
- **repro** `node tools/llm_playtester.mjs --port=3000 --repro=PT-20260805-056` (captured at a7be573f)
