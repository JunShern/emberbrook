# Playtest fix log — bugs the LLM playtester found, and what we did about them

**User instruction, 2026-08-03:** *"run the playtester, fix all verified bugs / issues, run
playtester again, fix, and just keep doing that in a loop. Keep a log of the bugs that were
fixed in this manner for me to review later."*

This file IS that log. It is for the user to review, so it is written for a reader who was not
here: what the agent experienced, what the instrument said, what changed, and how we know.

## The rules this loop runs under

1. **An UNVERIFIED complaint is a LEAD, never a ticket.** The agent plays through screenshots
   and real key events; it sees one still frame with no parallax, so it is biased toward "I
   cannot find it." Every claim is MEASURED on an instrument before anybody builds. This is
   the red-team fix loop the user ratified, applied to the playtester.
2. **REFUTED entries stay in the log.** A false positive is calibration data, not noise —
   the false-positive rate is how we learn what this tool is worth.
3. **A fix is not done until the playtester stops reporting it.** The loop closes the circuit:
   the same instrument that found it has to stop finding it.
4. **Fixes get their own commit** with the PT id in the message, so this log and git agree.

## Ledger

| round | id | sev | title | verdict | fix | commit |
|---|---|---|---|---|---|---|
| 1 | PT-20260803-005 | P1 | Screen remains black after leaving Emberbrook | **REFUTED against the game · VERIFIED against the harness** | the playtester's readiness gate + an honest capture | `19dcc15` |
| 1 | PT-20260803-006 | P0 | End the test session, the game is stuck on a black screen | **REFUTED against the game · VERIFIED against the harness** | same | `19dcc15` |
| 1 | (not filed) | — | the agent was blind in combat and the gate called a battle "nothing" | **HARNESS DEFECT, found while fixing the above** | the battle is now in the percept | `82dfdc1` |
| 2 | PT-20260803-009 | P1 | Camera detached or character missing after battle | **VERIFIED — but nothing to do with the battle** | the overworld gets the presence marker, and the occlusion ray can see foliage | `ffe507d` |
| 2 | PT-20260803-010 | P1 | Walk blocked: closed 0 m of an intended 5.7 m | **REFUTED against the game · VERIFIED against the harness** | a leg may only cry "blocked" once every heading was tried | `7fde690` |
| 2 | PT-20260803-011 | P1 | Walk blocked: closed 0 m of an intended 8.74 m | **REFUTED against the game · VERIFIED against the harness** | same | `7fde690` |
| 2 | PT-20260803-012 | P1 | Character stuck on terrain in sandy clearing | **REFUTED** — 24/24 headings open, character visible at 218 px | same | `7fde690` |
| 2 | PT-20260803-001 | P1 | Walk blocked: closed 0 m of an intended 35.57 m | **REFUTED** — reachable, 1296 cells, via 2 in-scene edges | (carried from round 0; no code change needed) | — |
| 2 | PT-20260803-003 | P1 | Character stuck on terrain geometry | **REFUTED** — 24/24 headings open at that spot, character visible at 219 px | (carried from round 0) | — |
| 2 | PT-20260803-004 | P1 | Character stuck on terrain near rock formation | **REFUTED** — same position as -003, same measurement | (carried from round 0) | — |
| 2 | PT-20260803-002 / -008 | P1 | The player can leave the chapter on its first frame, and the objective follows them out | **VERIFIED — the spawn WAS the exit pad** | spawn moved 7.0 m up the road; a new `denied` edge state answers in Vesper's voice | `615fa16` |
| 3 | PT-20260803-015 | P1 | I ended up somewhere with no way to advance the story | **VERIFIED — the overworld arrival was the door back to Emberbrook** | `ow-valley`'s bundle spawn backed 4.3u down-road, off the return pad; new `spawn_gate` instrument | `5c15518` |
| 3 | PT-20260803-013 | P1 | Game screen rendered as a tiny thumbnail in top-left corner | **VERIFIED as a picture — CAUSE STILL UNKNOWN** | the gate already refuses to vouch for it (`8b76529`); the probe-poisoning hypothesis is refuted below | — |
| 3 | PT-20260803-014 | P0 | The game is unresponsive and visually broken | **VERIFIED — same frame as -013**, one step later | same | — |
| 3 | PT-20260803-016 / -017 / -018 | P0 | Cannot move on the valley map screen · valley map ground is non-walkable · I must give up | **VERIFIED — the overworld booted as a diorama, with no follow camera at all** | `ow-` added to play3d's `RT` test, where `OWCAM`'s regex already had it | `10ea7a4` |
| 3 | (not filed) | — | yesterday's percept cursor fix shipped inert: `\s` in a template literal | **HARNESS DEFECT, found by re-reading `percept_test`'s own output** | call the percept's own `cur()` helper; the stale KNOWN-defect allowance retired | `b3bf841` |
| 4 | (round 3's blocker) | — | The page goes silent after an `ow-valley` battle | **REFUTED against the game · VERIFIED against the harness** — the harness was drowning the page in its own keys | Chrome boots at `about:blank` and the game arrives by `Page.navigate`; a new INPUT SENTINEL | `22db447` |
| 4 | PT-20260803-019 | P0 | Battle softlocks after defeating the enemy | **REFUTED** — the battle had already ended four steps earlier | the stuck detector no longer counts steps in which the body is not allowed to move | `22db447`+ |
| 4 | PT-20260803-020 | P1 | The player can leave the chapter on its first frame | **DUPLICATE** of PT-002 / -008 — a design call already with the user | (carried) | — |
| 5 | (round 4's finding) | — | The agent spent 26 steps failing to reach Dellhollow and never complained | **VERIFIED — every marker on that road said Emberbrook, and the one naming Dellhollow was drawn off the top of the screen** | portal markers carry the edge's own label; the marker clamps into the frame | `81e4a62` |
| 5 | (not filed) | — | the drop-in this whole loop runs from was at the wrong end of the valley | **HARNESS DEFECT, found while fixing the above** | a checkpoint arrives by the edge the player would have taken — position AND yaw | `e35a657`+`0f1e0c5` |
| 5 | PT-20260803-025 / -026 | P1 | The player and camera ended up underneath the level geometry | **VERIFIED — the ground runs continuously off the end of the play area, down the gorge, under the water plane** | not fixed: a world-building call, round 6's headline | — |
| 5 | PT-20260803-022 | P1 | Camera clipped inside foliage obscuring entire screen | **UNVERIFIED** — filed on the first frame of the corrected Old Gate arrival | — | — |
| 5 | PT-20260803-021 / -023 / -024 | P1 | The player can leave the chapter on its first frame | **DUPLICATE** of PT-002 / -008 / -020 | (carried) | — |
| 6 | PT-20260803-025 / -026 | P1 | The player and camera ended up underneath the level geometry | **VERIFIED — 126 of 3500 cells stand below y 0, in two components, out to y −6.07; the region's builder suppresses its own rims within 22 u of the river on purpose** | the world gets a bottom as map data (`worldbounds.json`), one-way so it can never strand anyone | `f1f5243` |
| 6 | (not filed — read off round 5's own frame) | — | The objective banner named a DIRECTION where it meant a PLACE, and the agent obeyed it | **VERIFIED — `ch2.road` fires AT the gate and said "Down into the hollow"** | "Through the Dellhollow gate — find whoever runs the locks", which is what the exit marker reads | `f1f5243` |
| 6 | PT-20260803-028 | P1 | Glitched view and out-of-bounds geometry after battle | **VERIFIED AS A PICTURE, REFUTED AS A PLACE** — filed from `[69.0, 0.00, −55.0]`, in bounds, on real ground; the Moorage reads as submerged decks and bare gorge wall | not fixed — round 7's headline | — |
| 6 | PT-20260803-027 | P1 | The player can leave the chapter on its first frame | **DUPLICATE** of PT-002 / -008 / -020 / -021 / -023 / -024 | (carried) | — |
| 7 | (round 6's handover) | — | The gorge encounter rate eats the run | **REFUTED as a game defect** — 3 battles in 175.5 u against an analytic 4.48; the corridor ON ITS ROAD is 28.6 u, 77% road, expected **0.28** battles. The cost is a battle costing 10.7 HARNESS steps against ~1 for a 15 u walk leg | measurement + recommendation only; `encounters.json` untouched by instruction | — |
| 7 | PT-20260803-028 | P1 | Glitched view and out-of-bounds geometry | **VERIFIED AS AN ART DEFECT, reproduced on tonight's rebuilt bundle** — the same river surface measures **222.3 L at one camera yaw and 83.4 L at another**, and at 222 it is BRIGHTER than the sky (189) while the gorge around it is 55–70 | not fixed by this lane — `GLASS_ROUGH 0.06` is a dated user art pick and the lighting lane owns the surface; handed over with the numbers | — |
| 7 | (not filed — found by the same probe) | P1 | The camera boom sits inside the new grass and 88.2% of the frame is grass cards | **VERIFIED on the current build** — same position, yaw 0.4 | routed to the overworld-content lane; same class as `PT-20260803-022` | — |
| 7 | (found by playing) | P1 | The Boatmen's Rest is a door onto an empty room — the agent spent 18 of 70 steps trying to talk to its own party | **VERIFIED on `npcs.json` + `shops.json`** — 0 NPC records for `del-inn-int` against 1 each for the three shop interiors, no shop with that `sceneKey`, and 1 dialogue box in the whole run | not fixed — content, reported | — |
| 7 | PT-20260803-029 | P1 | The player can leave the chapter on its first frame | **REFUTED — the spine detector fired because the player walked into a pub** and left again six steps later; 8th of this class | kept as calibration, per rule 2 | — |
| 7 | (not filed — read off this run's own log) | — | Three legs blamed a slow machine at 160 ms/burst for a walk that had tried every heading | **HARNESS DEFECT** — `sinceGain >= 8` was falling into the starvation branch | `walkLeg` returns `noGain`; `episode.mjs` prints its own sentence for it | `03af0da` |
| 8 | (not filed — found by building the probe the tool asked for) | **P0** | **The act of loading a save destroys it: the autosave writes `at.pos [0,2,0]` on the first frame of every boot** | **VERIFIED — `story_runtime.arm()` runs before play3d has placed the body, and nothing corrected it for the 20 s measured** (body `[78.93,14.07,-15.6]`, `at.pos [0,2,0]`, `cam null`, through to the next scene change) | `recordAt()` refuses to write a scene that has not arrived; `arm()` polls for arrival; `at.cam` now follows the shot in memory | this commit |
| 8 | PT-20260804-002 | P1 | The player can leave the chapter on its first frame | **REFUTED — the ninth of this class, filed from `del-cookhouse-int`** six steps before the agent walked back out of the door | the spine detector now asks scenegraph.json whether it is standing in an `interior` | this commit |
| 8 | (found by playing) | P1 | The Cookhouse is the SECOND door onto an empty room | **VERIFIED on `npcs.json`** — 0 records for `del-cookhouse-int`, `del-inn-int`, `del-boatyard`; 1 each for the three shop interiors | not fixed — content; the new empty-room detector will now name the room instead of mis-filing the spine | this commit |
| 8 | (found by playing) | P1 | 34 of 45 steps inside one shot of Dellhollow, walking well and getting nowhere | **VERIFIED as LEGIBILITY, REFUTED as connectivity** — `reach_probe` in the running page: the lock apron IS reachable from the deck (39.7 m, 2469 cells, 2 in-scene edges). `del-cine` ships **40 label-less `cut` edges against 9 labelled ones**, and `quay-west` has **6 exits of which 5 are silent** — the only labelled thing in the shot is the door into the empty Cookhouse | not fixed — the look decision carried since round 5, now with a price | — |
| 8 | (not filed) | — | The playtest agent cannot read the pause menu | **HARNESS DEFECT** — `menu.js` renders `.mn-navrow`, the percept queried `.ebui-row`; measured live: menu open, six commands in the DOM, **zero rows in the percept** | `.mn-navrow` in the percept's union, a fifth `percept_test` fixture, and menu.js added to the selector census | this commit |
| 8 | (the run itself) | **BLOCKER** | The LLM playtest died at step 46 of 120 | **`HTTP 429 — "Your prepayment credits are depleted"` (Gemini/AI Studio).** Not a game or harness fault; the loop cannot run further without credit | reported to the user; the round finished on the no-model instruments | — |
| 10 | PT-20260804-004 | P1 | Character stuck on wooden platform, cannot reach objective markers | **REFUTED against the game · VERIFIED against the harness** — the world is open (`SIM.move` crosses to the seam in 46 ticks; the agent itself was two levels down one step later), but every failed leg aimed at a **cliff face 7 m past the deck**, because an exit marker is drawn 2.1 m above the ground it names and the executor ray-marched the arrow's pixel | a pixel on an exit arrow resolves to that edge's own `at`; and in a walk-network scene a ray that never crosses the network is refused instead of walked at — re-run `run-20260804-112506`: off-network legs **14 → 0**, median leg closed **0.11 → 0.63**, zero verified blockers | this commit |
| 10 | PT-20260804-003 | P1 | Character cannot navigate up the stairs from the middle walkway | **REFUTED** (triage, round 10) — reachable, 4.7 m, 325 cells, via 2 in-scene edges; the agent climbed those stairs later in the same run | same root cause as -004 | — |
| 14 | PT-20260805-006 | P1 | Cannot walk to the head-gate winches at Lock Five | **VERIFIED — and filed from 70 m away.** The objective named `the head-gate winches`; Dellhollow's head gate is the VALLEY GATE at the dam (`winch-head`/`winch-foot`, x≈20), Lock Five is x≈87. The agent spawned 2 hops / 7.2 m from the goal and spent 45 of 60 steps at the wrong landmark, with the correct amber `Lock Five` caption drawn on screen the whole time | the objective carries a bearing instead of a decoy noun; re-run fired **`ch2.winches` at step 5** and the Ch2 card at step 8 | `459f861` |
| 14 | PT-20260805-004 | P1 | One-way lip at `[57.74, 15.30, −11.24]` (carried, round 13) | **VERIFIED, and round 13's "one map line" REFUTED by arithmetic.** New `_court_probe --stand` census: **16 of 17 stairs landings in `del-cine` are roofed by their own flight, 30–52% of each**; clearing the body band needs `step ≤ 0.29`, which needs a leg descending under 0.87 m — no waypoint in the map can make one | **NOT FIXED — filed as the build lane it is** (tread-top convention + `walk_rederive`×6 + `ls_build` + `cine_solve` + plates) | `f3f3f39` (instrument) |

## Rounds

### Round 0 — 2026-08-03 01:18 & 01:32 (the overnight lane, killed by a session limit)

Two runs before the account limit killed it. Filed 4 × P1: one VERIFIED, three UNVERIFIED.

- **PT-20260803-002 · VERIFIED · P1** — *the player can leave the chapter on its first frame,
  and the objective follows them out.* The agent read the opening narration, took the only
  prompt on screen, and landed in `ow-valley` with no way to advance, while the objective
  still read "Follow the road north." Proven mechanically by the spine detector: the body was
  in `ow-valley` for three consecutive steps while none of the next unfired beats in
  `story.json` lives there. **What to do about it is a DESIGN decision, not a bug fix.**
- **PT-20260803-001 / -003 / -004 · UNVERIFIED · P1** — three reports of the same experience:
  *"completely immobile"*, *"closed 0 m across three movement attempts"*, *"won't move no
  matter where I click"*, all in the overworld, all trying to get north. Never verified:
  `reach_probe` needs a running server and the lane did not pass one, and two of the three
  recorded no destination so they cannot be replayed as filed.

**The standing hypothesis going into round 1** (mine, and it is a hypothesis, not a finding):
those three are the OLD GATE QUARTER TURN, found by a player hours before we diagnosed it as
builders. The prop's local frame was 90° out, so the gate was four detached piers and a
0.42 m plank, and the overworld's walk network was THREE disjoint components. The agent was
trying to walk north through it. Fixed at `28a5f9d` (12:02), merging 3 components into 1 of
712 cells. **If PT-001/003/004 vanish in round 1, that is the case for this tool**: it
described a rotation bug the way a player would — *"I'm stuck and I can't get north."*
If they survive, we have a blocker nobody has found by hand. Both outcomes are worth the run.

### Round 1 — 2026-08-03 11:39 · the run that died at step 6, and why it was our fault

**What the agent experienced.** It read the opening narration, took the only prompt on screen
("Leave Emberbrook? [E]"), and then saw a **completely black screen for four steps in a row**.
It filed PT-20260803-005 (*"The screen turned completely black and did not load the new area
after multiple waits"*) and then PT-20260803-006, giving up: *"End the test session as the game
is stuck on a black screen and cannot continue."* Both P1/P0 blockers. Both entirely reasonable
conclusions from what it was shown. `frames/step-003.jpg` through `step-005.jpg` are genuinely
black — only the music chip renders.

**What the instrument said.** The game was rendering the whole time. Driving the same path over
CDP — same `--headless=new`, same real GPU, same key events through the same transition — and
measuring the luminance of the captured frames:

| stage | scene | mean luminance | pixels above black |
|---|---|---|---|
| boot | `emb-cine` | 33.6 | 87% |
| immediately after the transition | `ow-valley` | 15.1 | 81% |
| +2 s, and stable to +20 s | `ow-valley` | **121.5** | **100%** |

`ow-valley` renders correctly and stays rendered. Independently: `docs/qa/oldgate/ship-final-*.png`
and `docs/qa/ow-land/plates/SL1-*.jpg` are real-time `ow-valley` frames photographed headless by
`tools/_gate_shots.mjs`, so the scene has been photographing fine all along.

**So what was black?** play3d's own fade veil, over a scene load. The harness's `settle()` waited
a flat 10 s for the transition to finish, timed out — and `observe()` **captured anyway** and
handed the frame to the model labelled as what the player sees. The run log even printed the
timeout three times, and the frame went out regardless. Re-measured under the fix, that
transition takes **~103 seconds** cold in this harness (45 + 45 + 13 s of waiting before a frame
appeared), so 10 s was never going to be enough.

**None of the readiness predicate's conjuncts was the culprit**, which is worth writing down
because it was the obvious suspect. `SIM.gpu().meshes` is renderer bookkeeping (47 in
`ow-valley`, so > 0 is true); `SIM.cam` is a function and always truthy; `SIM.cine()` is null in
a real-time scene so the shot clause passes; `SGbusy` goes false the moment the swap lands.
**Not one of them is a statement about pixels.** The gate was asking the wrong question, and its
answer had nothing to do with whether anything was on screen.

**What changed (`19dcc15`).**

- Readiness is now a question whose true answer implies a **painted frame**: no transition in
  flight, meshes loaded, a pre-rendered scene has chosen its shot, no opaque full-screen black
  veil, and — the backstop that would have caught this on its own — **the measured mean
  luminance of the captured frame**.
- `observe()` **waits** (45 s budget, enough for a cold 45 MB bundle) and reports whether it got
  a frame. An unready frame is written as `step-NNN-UNREADY.jpg`, kept through the retention
  sweep as evidence, and **never sent to a model**.
- Six unready steps in a row stops the run with *"THE HARNESS COULD NOT SEE — INSTRUMENT FAULT"*.
  It cannot file a bug against the game for its own blindness any more.
- Boot is held to the same bar: "the page became playable" now also means something is drawn.

**The lesson, in one line:** *an instrument that cannot see must say so rather than emit a black
frame.* The harness knew its own precondition had failed and published the picture anyway; the
agent believed it, because that picture was its only sense.

### Round 1, second finding — the playtester was blind in combat (`82dfdc1`)

Not filed as a PT report, because the harness could not see well enough to file one. The first
run under the new gate got past step 6, and then stalled for four and a half minutes on steps
8–13 insisting *"the game holds a modal lock with nothing drawn on it"* over a frame measuring
**117 luminance**. Opening `step-008-UNREADY.jpg` settled it instantly: it was **a turn-based
battle**, fully drawn and fully playable — a Scree Shell in CRAG, ROUND 1, "What will you do?",
Attack / Item / Flee.

The percept read `#story-obj`, `#story-card`, `#sgp` and `.ebui-veil`. A battle is none of those.
So the agent's entire perception during combat was *"OBJECTIVE ON SCREEN: Follow the road north"*,
and the readiness gate — asked whether anything was drawn — correctly answered *no* about the only
four things it knew how to look at. **This was true before the black-screen fix as well**: the old
`settle()` would have spun on the same battle and shipped the screenshot anyway, with no text.

Fixed: the battle is now in the percept (zone and round, the actor line, the command list with the
cursor marked, an open sub-menu, the foes by name, party HP, and whether it is your turn), the
doorway banner still sitting in the DOM underneath a full-screen battle is suppressed because a
player cannot see it, and `adapter.choose(n)` measures where the cursor is and moves relative to
it instead of assuming it starts at the top. Verified against a live battle: it reads the menu,
opens Item, sees "Tonic×2", spends it, and reads back "Vesper takes 10 damage" with party HP at
24/34. A "frozen" game (a modal lock with genuinely nothing drawn) is now reported separately
from a black frame and **files a blocker against the game**, because those are two different
sentences about two different things.

### Round 1 — the receipt: the loop turns

`node tools/llm_playtester.mjs --port=3000` (run `run-20260803-122026`), against the same build
that produced the black-screen reports. What the same path looks like now, straight out of
`run.jsonl`:

| step | scene | frame ready? | mean luminance | what it was |
|---|---|---|---|---|
| 1–2 | `emb-cine` | yes, in 31–42 ms | 32.4 | the opening narration, read and answered |
| 3–4 | `ow-valley` | **no** — held back, 45 s each | 0.38 | the transition veil. **Not shown to the agent.** |
| 5 | `ow-valley` | yes, after 13 s | 121.8 | the overworld, exactly as the CDP probe measured it |
| 6–22 | `ow-valley` | yes | 116–182 | walking the valley |
| 23–24 | `ow-valley` | yes | 37 | **a battle**, read and fought through the menus |
| 25–33+ | `ow-valley` | yes | 103–116 | back on the map, still playing |

Round 1 died at step 6. This run passed 30 and kept going. The two black frames that killed the
previous run are still black — the transition really does take about 100 seconds cold here — but
they are now labelled `step-003-UNREADY.jpg` / `step-004-UNREADY.jpg`, no model was paid to look
at them, and no blocker was filed against the game for the harness's own wait.

**New leads the now-seeing agent filed** (UNVERIFIED — they are leads, not tickets, and triage is
the next round's work):

- **PT-20260803-009 · P1** — *"Camera detached or character missing after battle."* After a
  victory the overworld camera is looking at a cliff face and Vesper is nowhere on screen, with
  "Vesper reached level 2" floating over it. This is a report the instrument **could not have
  written yesterday**, because yesterday it could not see that a battle had happened.
- **PT-20260803-010 / -011 · P1** — walk blocked in `ow-valley`: 0 m closed of an intended 5.7 m,
  and 0 m of an intended 8.74 m, each twice at the same place. Measured by the executor, not
  claimed by the model.
- **PT-20260803-012 · P1** — *"Character stuck on terrain in sandy clearing."*
- **PT-20260803-008** — the spine detector firing again on the same design question already
  logged as PT-002 in round 0: the player can leave the chapter on its first frame. Duplicate,
  not new information.


### Round 2 — 2026-08-03 · the now-seeing agent's first six reports, triaged

Round 1 gave the playtester its eyes back. This is the first round where what it filed could
be taken at face value — so the first thing worth saying is that **five of its six reports
were wrong about the game, and the sixth was right about something it could not name.**
That is not a complaint about the tool. Two of those five are wrong in a way that turned out
to be *the harness's own fault*, and the one that was right found a defect no gate in this
repo covers.

#### PT-20260803-009 · VERIFIED · P1 — and the battle was innocent

**What the agent experienced.** After winning a random encounter in `ow-valley` it dismissed
the victory screen and reported: *"The camera is looking at a cliff and some trees, and my
character is nowhere to be seen. There's just floating text saying 'Vesper reached level 2'."*
`frames/step-025.jpg` is exactly that — a cliff face, tree canopy, the level-up line floating
in the middle of the screen, and no Vesper anywhere in the frame.

**What the instruments said.** First, the battle is not the culprit. Driving a real encounter
to victory over CDP and reading `SIM.cam()` either side of it, the camera is **bit-identical
before, during and after** — position and forward vector unchanged — and the body never moves:
`model:true, visible:true, inScene:true`, same coordinates throughout. Nothing detaches.

What is actually true at that spot is worse, and permanent. Using `SIM.paint()`, play3d's own
GL readback (it paints the character magenta and counts the pixels), at the exact position the
report was filed from — `[-34.78, 29.64, 79.42]`, `ow-valley` under `rt=1`:

| question | instrument | answer |
|---|---|---|
| is the character drawn at all? | `SIM.paint({tested:false})` | **219 px** — yes |
| do any of those pixels survive the depth test? | `SIM.paint({tested:true})` | **0 px** — wholly hidden |
| does the engine's own ray see an occluder? | `SIM.occ()` | **`nHits: 0`** — it sees nothing |
| is the presence marker up? | `SIM.occCheck()` | **DOWN** |

The character is drawn, is completely behind a cliff-side tree canopy, and **the game does not
know it**. Two stacked defects:

1. `occCheck()` opened with `if(RT||!cam) return`. Every `ow-*` scene is `RT`, so the whole
   overworld skipped the presence check outright. The ring-at-the-feet and diamond-overhead
   that exist precisely so a hidden character can still be found have never run there.
2. Even when asked, the ray searched `collide`. Foliage and terrain dressing are deliberately
   **not** collidable — canon is that a canopy hides you and never blocks you — so the ray
   could not see the thing doing the hiding. The comment sitting directly above `occCheck`
   already tells this exact story about a rim tree over the Valley Gate. The scar was written
   down, and the fix was applied to the one mode where the check was switched off.

**What changed (`ffe507d`).** The occluder set is now the render-visible geometry whenever
`DEPTH || RT`, and `SIM.occ()` uses the same set so the harness and the game agree about what
hides you. Re-measured on the same four spots:

| spot | before | after |
|---|---|---|
| PT-009's position | `nHits:0`, marker DOWN | **`nHits:8`, first `veg_canopy_whisperwood_cards` @ 35.1 m, marker UP** |
| "sandy clearing" | marker DOWN | `nHits:0`, 218 px visible, marker DOWN |
| "brown rock face" | marker DOWN | `nHits:0`, 219 px visible, marker DOWN |
| the spine spot | marker DOWN | `nHits:0`, 220 px visible, marker DOWN |

It fires where the character is hidden and **nowhere else** — the three control spots stay
clean, which is the part that makes it a fix rather than a new source of noise.

**Worth keeping:** the agent said *"camera detached or character missing"*, and both halves
were wrong. The camera was fine and the character was present. What it could actually observe
— *"my character is nowhere to be seen"* — was true, precisely true, and pointed at a real
defect. **A playtester's diagnosis is a lead; its description of what it saw is the evidence.**

#### PT-20260803-010 / -011 / -012 · REFUTED against the game · VERIFIED against the harness

**What the agent experienced.** Stuck in a sandy clearing in `ow-valley` at
`[-53.64, 26.75, 75.47]`, filing three P1 blockers from that one spot: *"The character moved
0 m and stopped 5.7 m short — twice in this run. Something is in the way, or that ground is not
connected to where I was standing"*, and then *"Four consecutive movement attempts in different
directions (south, west, southwest) all failed to move Vesper at all (0 m closed)."* The run
ended with the body at that identical coordinate for its last eight steps.

**What the instruments said.** Three of them, independently, that nothing is in the way:

| instrument | result |
|---|---|
| `tools/reach_probe.mjs`, in the running page | reachable, 5.7 m, **289 cells**, on foot |
| the same, for the second target | reachable, 8.7 m, **1270 cells**, on foot |
| `SIM.ground` / `SIM.blocked`, 24-heading census at r=0.8 m | **24/24 headings have floor, 0/24 body-blocked** |
| real CDP key events — the executor's own `hold()` | one 150 ms burst moves **0.90 m** |
| driving from that point for ~3 minutes | the body walked **~21 m** clean out of the clearing |

The ground is open in every direction and the body crosses it at nearly a metre per burst.

**So why did the executor measure 0 m?** The leg budget is 9 s of *wall clock*, but almost none
of a leg is spent walking — it is spent on CDP round-trips. On a loaded machine one burst plus
its two position reads measured **7 to 66 seconds** (the filed legs record `ms` of 14810 to
132928); on an idle one the same iteration takes ~500 ms. So the inner `if (elapsed > budget)
break` fired **after the first heading**, the five-heading slide never ran, and `moved < 0.10`
was then read as *"every heading refused: blocked"*.

Every one of those three reports carries **`bursts: 1`** in its own payload. One heading is not
every heading. The report contained its own refutation and nobody had read it.

**What changed (`7fde690`).** A round of headings is no longer cut short by the ordinary budget
— only by a hard ceiling at 6×. The leg now returns `exhausted` (all five pushed, nothing moved:
*the world refused*, and this is worth filing) separately from `starved` (the ceiling stopped
it: what the world would have done is **unknown**). `episode.mjs` may only file a blocker on
`exhausted`; a starved leg is logged with its measured ms/burst and files nothing. The surviving
blocker text now states its own evidence — how many bursts, at what cost — so the next reader
does not have to go find it.

This is round 1's lesson relocated from the eye to the motor loop: **an instrument that could
not look must say so rather than report what it did not see.**

#### PT-20260803-001 / -003 / -004 · REFUTED — the round-0 carry-over, finally measured

These three were filed before the Old Gate quarter-turn fix (`28a5f9d`) and never verified,
because `reach_probe` needs a running server and that lane did not pass one. Measured now:

- **PT-001** (*"closed 0 m of an intended 35.57 m"*, in `emb-cine`) — `reach_probe`:
  **reachable, 35.6 m apart, 1296 cells filled, via 2 in-scene edges.**
- **PT-003 / PT-004** (*"completely immobile"*, *"won't move no matter where I click"*, both at
  `[-95.18, 30.37, 90.67]`) — the destination was never recorded, so the claim cannot be
  replayed as filed. But the 24-heading census at that exact position answers the claim
  directly: **24/24 headings have floor, 0/24 are body-blocked**, and `SIM.paint` puts the
  character on screen at **219 px**. A body with open floor in every direction is not immobile.

**The standing hypothesis from round 1 was that these three were the Old Gate rotation bug and
are now dead. That is not what the measurement says.** They are the same harness defect as
PT-010/011/012 — the walk executor calling its own timeout a wall — which is why the class kept
reappearing *after* the gate was fixed. The gate fix was real; it was never what these reports
were about. Both the original hypothesis and the evidence offered against it were wrong, and
the instrument settled it.

#### PT-20260803-008 — not triaged here, by instruction

The spine detector re-finding round 0's PT-002: the player can leave Chapter One on its first
frame and the objective follows them out. Verified and mechanical, but the remedy is a design
call the user is deciding (seal the road vs. let the chapter follow), and a separate lane is
mid-flight implementing their ruling — *"spawn the character inside Emberbrook to begin with,
and don't let them exit from the whisperwood side until after Ch1 ... just use a denial
prompt"*. Left alone deliberately.

#### A blocker for the next round, found by accident and not fixed here

A `newgame` run now dies at step 2 with
`FATAL: FIREWALL: the agent prompt contains privileged state it must never see:
["waystone (soft, in harness-authored text)"]`. The cause is in
`assertNoPrivileged`: the soft-token check does `harnessText == null ? prompt : harnessText`,
so when a plan carries **no brief** — which `newgame` does not — the "harness-authored text"
falls back to *the entire prompt*, and any camera name the game legitimately drew on screen
trips it. It only started firing now because the in-flight spawn change moves a new game into
the `waystone` shot. It belongs to that lane, so it is reported rather than patched; round 2's
closing run used `--from=ch1.open`, which carries a brief and starts in `woodroad`, to get
around it.


#### Round 2 — the receipt: the loop turns

`node tools/llm_playtester.mjs --port=3000 --from=ch1.open --steps=26`, run
`run-20260803-135651`, on a machine that happened to be as loaded as the one that produced
the false blockers (swap 3.7 GB of 5.1 GB used). That load is not a nuisance here, it is the
test: it is the exact condition the defect needed.

```
  4 goto  goal="Follow the paved road further into the forest towa"  [0.52,0.42] only closed 16.86 m of 25.77 m
leg not conclusive: gave up after 6 burst(s) at ~42127 ms/burst — no blocker filed (the headings were never all tried)
  5 goto  goal="Follow the path towards the red indicator near the"   [0.53,0.42] only closed 0 m of 18.97 m
```

**A leg closed 0 m of an intended 18.97 m — the exact shape of PT-010/011/012 — and no
blocker was filed.** The executor said what it actually knew instead: it gave up after six
bursts, the headings were never all tried, and the reason is printed as a number —
**~42 seconds per burst**. That single figure is the whole diagnosis, measured in the wild
rather than argued: forty-two seconds to hold a key for 150 ms and read a position twice.

**Reports filed by the closing run: 0.** The queue is unchanged at 12 entries. The same
instrument that filed six P1s against this ground now walks the same ground under the same
load and files nothing, while still reporting honestly that it is not closing the distance.

What this round did NOT prove: PT-009's fix has not yet been seen by the playtester, because
this run never reached a battle in `ow-valley` within its step budget. The marker is verified
on the instrument (`SIM.occ` naming `veg_canopy_whisperwood_cards`, the marker up at the
reported spot and down at three controls) but not yet by the tool that filed it. **That is
an open item for round 3, by rule 3 of this log** — a fix is not done until the playtester
stops reporting it, and this one has not had the chance to.

### Round 2, the last piece — the spawn was the door out (`615fa16`)

**What the agent experienced,** twice, in two different runs a day apart: it read the opening
narration, took the only prompt on screen, and was in `ow-valley` — outside the chapter, with the
objective still reading "Follow the road north," and nothing out there able to advance anything.

**What the instrument said.** The cause was not the prompt and not the story wiring. Shot
`woodroad`'s baked fallback spawn **is the map exit's own pad** (`walk_pad_arrival-clearing`,
r 2.2). **A new game began standing on the door out.** The first thing a player could do was
leave, because it was the only thing in reach.

**What changed.**

  * **The spawn is now a story fact.** `story.json` gained `start` (scene, cam, pos), and
    `index.html`, `playthrough_test` and `llm_playtester` all read it instead of each carrying
    its own URL. The position moved **7.0 m up the Whisperwood road** to `[53.7,-0.385,21.2]`.
    `checkpointsFromStory` is seeded from the same fact, so a `--from=ch1.open` drop-in no longer
    reproduces the bug it starts after.
  * **A new edge state: `denied`, between open and sealed.** A sealed edge shows no prompt at
    all, which suits a gate you cannot see through and NOT a road you just walked in on. A denied
    edge keeps the prompt and drops the transition. It writes no flag and moves nobody, so it is
    not a beat, and `SIM.door`/`SIM.go`/markers all honour it.
  * **The line**, per the user's ruling that this should be a refusal in her own voice rather
    than a wall:

    > **"(South is eleven days of road I've surveyed. The lights north aren't on any map I carry.)"**

    Fact first, filed as paperwork. The refusal is a survey record; the noticing is a gap in her
    own maps, which is *why* she goes north. It branches into Lake's voice during his playable act.

**The circuit closed.** A real `newgame` run: 10 steps, all in `emb-cine`, shots running
`woodroad -> waystone -> arch` (northward, which is the point), `ch1.open` and `ch1.waystone`
fired, **the spine detector never fired, zero reports**.

**A red that was not real, and the lesson in it.** That lane's own `playthrough_test` came back
**54 passed / 16 failed**, cascading from `ch1.pact` "never fired" — while the flag dump printed by
that very failure read `story.ch1.pact: true`. It ran at load 19-22 against another lane's Chrome
swarm and took 28 minutes instead of 12. Re-run by the coordinator on a QUIET machine, the same
tree is **86 passed / 0 failed**. Second time in one day a browser-gate red dissolved when the
machine was idle. **ON THIS BOX A BROWSER GATE'S RESULT IS ONLY MEANINGFUL WHEN NOTHING ELSE IS
RUNNING** — treat a red from a loaded machine as unproven, not as a finding.

### Open going into round 3

  * **PT-009's fix is verified on the instrument but the playtester has not re-seen it.** Rule 3
    says a fix is not done until the playtester stops reporting it, and no run has yet reached an
    `ow-valley` battle since. First job of round 3.
  * **The closing runs starve.** One printed `STARVED after 1 burst(s) at ~210402 ms/burst` while
    the agent closed 0 m of 20.87 m on ground measured open in all 24 directions. The
    exhausted/starved split held and it filed nothing, which is the round-2 fix working — but a
    loop whose closing condition cannot walk cannot close. Being fixed now.

### Round 3 — 2026-08-03 · the first round where the harness was not the thing in the way

Rounds 1 and 2 spent themselves on the instrument: it could not see, then it could not walk.
Round 3 opened with a seeing, walking, self-checking harness — and the first thing that
harness did was hand back **a real defect on the one seam the whole game depends on**, in
2 runs out of 2, on the agent's first action.

#### Before anything else: yesterday's percept fix had never actually run (`b3bf841`)

The round-2 close-out said menus should work better now. They did not. `b4ae9d7` fixed the
ui_kit cursor blindness by inlining a regex into `PERCEPT_JS`:

```js
selected: /(^|\s)cur(\s|$)|sel|active|cursor/.test(r.className||'')
```

`PERCEPT_JS` is a **template literal**. `\s` inside one collapses to a literal `s` before the
page ever sees the regex, so what actually ran was `/(^|s)cur(s|$)|sel|active|cursor/`, which
does not match `class="ebui-row cur"`. Proven in node rather than argued — the collapsed
source tests `false` on the real class string and the double-escaped one tests `true`. The
helper twenty lines above (`cur()`) had doubled its backslashes and was right all along; the
fix now calls it.

**The part worth keeping is not the escape.** `percept_test` was *already printing this as a
failure* — as a `KNOWN` defect, with a note written before the fix, under a green `PASS` line.
The allowance outlived the bug it described, so a red assertion sat in plain sight for a day
and nobody read it. The note is gone; it is an ordinary assertion now. **A known-defect
allowance that is not retired with its fix converts a passing gate into a lie.**

That is the same trap family as the backtick in a CSS comment and the backtick in `git -m`,
now on its fourth syntax in two days — and it was hit by the person who wrote the CLAUDE.md
entry about it, in the commit that fixed the previous instance.

#### PT-20260803-015 · VERIFIED · P1 — the overworld arrival was the door back to Emberbrook

**What the agent experienced.** Dropped in at `ch1.done` — the Chapter One → Chapter Two
handoff, standing in the valley with the town behind it — it took one action and was back
inside Emberbrook, with a Chapter Two objective ("Follow the valley road down to Dellhollow")
floating over a Chapter One street. It filed: *"I ended up somewhere with no way to advance
the story. Nothing here can continue the chapter."*

**What the instruments said.** Not a diagnosis from the model — a coordinate from the run log,
in two independent runs:

| run | step 1 | step 2 |
|---|---|---|
| `run-20260803-191540` | `ow-valley` `[-57.43, 27.20, 65.55]` | **`emb-cine` `woodroad`** |
| `run-20260803-191750` | `ow-valley` `[-57.43, 27.20, 65.55]` | **`emb-cine` `woodroad`** |

That spawn is `public/assets/scenes/ow-valley/meta.json`'s own — what `play3d` uses whenever
nothing else supplies a position. Against `public/world/scenegraph.json`:

| | |
|---|---|
| bundle spawn | `[-57.434, 27.230, 65.547]` |
| the edge `ow-valley>emb-cine@emberbrook-gate` | `at [-57.4, 27.207, 65.61]`, **`r 3.2`** |
| distance between them | **0.072 m** |

**The arrival was 7.2 cm from the centre of the portal that sends you back.** `meta.json`'s
own `spawn_note` said so in plain words — *"emberbrook-gate portal"* — because it was placed
there deliberately; nobody checked that the portal it was pinned to was the one pointing home.

This is **PT-20260803-002 on the other side of the same seam.** Round 2 found a new game
spawning on its exit pad and moved it 7 m up the road. The return trip had the identical
defect and was never looked at. It also breaks the law in `docs/plans/seam-canon.md`:
an arrival may not be a return.

Who actually hits it: the checkpoint drop-ins (all of the overworld ones — the tool this
whole loop is being run with), a resume whose save carries no position, and any
`?scene=ow-valley` jump. A player walking out of Emberbrook takes the *edge*, which bakes its
own arrival 4.3 m clear, which is why `playthrough_test` is 86/0 over this seam and never saw it.

**What changed (`5c15518`).** The back-off is not a new number. `world/regions/valley.region.json`
already carries the house rule for portal arrivals — `gateRadius 3.2 + spawnBackoff 1.1 = 4.3u`
of road arc — and it had simply never been applied to the region's own spawn, twenty lines away.
Applied down-road, so the gate ends up behind the player and Dellhollow ahead:

```
spawn  [-57.434, 27.230, 65.547] -> [-57.848, 26.755, 60.576]
camYaw -1.5426 -> -1.4869
distance to the return pad   0.072 m -> 5.054 m   (1.85 m outside r 3.2)
```

The rule now lives **once**, in `valley_map.region_spawn()`; `valley_export.py` calls it instead
of carrying its own copy. Before touching it, the unmodified rule was made to reproduce the
shipped spawn to all seventeen digits, so the only delta in `meta.json` is the back-off — the
faithfulness gate this repo asks of every carrier.

**A new instrument, and a second defect it found by itself.** `tools/playtest/spawn_gate.mjs`
boots the real page with **no position in the URL** — exactly what a drop-in does — and asks the
*engine*, not the file, where the body landed: floor census, body-box census reported **by
blocking mesh name**, and the distance to every edge pad in the scene. Run against the old
spawn as a control it fails twice, and the second failure is something no report mentioned:

| | floor | body-blocked | distance to return pad |
|---|---|---|---|
| old spawn (control) | 24/24 | **6/24, by `emberbrook_5`** | 0.07 m — inside `r 3.2` |
| new spawn | 20/24 | **0/24** | 5.05 m |

The old spawn was pressed against the gate structure *as well as* standing on its own exit,
with a quarter of its headings walled off. That is very likely why those two runs also logged
`closed 0 m` legs from their first step.

20/24 is the road verge, not a ledge: a ~4 m ribbon censused 0.8 m out in 24 directions loses
the headings over each edge, and the control scores the same in kind. The gate's threshold is
18, with the control written down beside it — a bound loose enough to refuse everything is a
veto, not a test.

#### PT-20260803-013 / -014 · VERIFIED as a picture · CAUSE STILL UNKNOWN

Filed at 17:34 by a run nobody had triaged: *"the game view shrunk to a tiny rectangle in the
top-left corner"*, then, four steps later, *"the game is unresponsive and visually broken."*

**The agent was exactly right, and it is worth being blunt about that.** `frames/step-004.jpg`
is 1280x720, mean luminance **0.08**, with **0.2%** of its pixels above black — the entire game
drawn into a **64x40** rectangle in the top-left corner. Measured on the written files:

| frame | size | meanL | above black | what the run log recorded |
|---|---|---|---|---|
| `step-002.jpg` | 1280x720 | 32.25 | 84.7% | `meanL 32.21, ready:true` |
| `step-003.jpg` | 1280x720 | **0.09** | **0.2%** | `meanL 33.56, ready:true` |
| `step-004.jpg` | 1280x720 | **0.08** | **0.2%** | `meanL 32.80, ready:true` |
| `step-008.jpg` | 1280x720 | **0.08** | **0.2%** | `meanL 32.83, ready:true` |

The gate vouched for a painted frame five times over a picture that was 99.8% black, because
the cheap 64-px poll probe and the JPEG the agent is handed **were not the same picture** — and
the probe is exactly the size of the surviving thumbnail, so it kept reading a healthy scene
nobody was looking at. That half was already fixed before this round began (`8b76529`: the
verdict is now taken on a full-size capture of the frame that gets handed over), with the
thumbnail itself explicitly parked as belonging to whoever owns `play3d`.

**The obvious suspect is refuted.** The coincidence of `64` is loud enough that it had to be
destroyed rather than assumed: `Page.captureScreenshot` with `clip.scale` can resize a page's
surface, so the harness's own probe was the leading hypothesis for the harness's own broken
frame. Driven directly over CDP with the playtester's exact Chrome flags, real GPU, same
viewport:

| stage | full capture | content bounding box | `innerWidth` / canvas |
|---|---|---|---|
| before any probe | meanL 68.22, 92.4% non-black | `[0,0]..[1279,719]` = **1280x720** | 1280x720 / attr 1344x768 |
| after 1 clipped probe | 68.22, 92.4% | **1280x720** | unchanged |
| 1.5 s later | 68.22, 92.4% | **1280x720** | unchanged |
| after 20 more probes | 68.22, 92.4% | **1280x720** | unchanged |

**Twenty-one probes move nothing.** The probe is not the cause, and that is a false lead
retired rather than a fix shipped against a guess.

**What is still open.** The 64x36 surface was *live* — `step-003` and `step-008` differ in
their thumbnail, so the game was rendering into it, not frozen. The strongest remaining
hypothesis, and it is labelled as a hypothesis because nothing has measured it: that run
predates the NPC model cache (`c3a35cb`, which took `emb-cine` boot from 6246 MB to 3277 MB),
and a compositor surface collapsing under memory pressure fits both the timing and the shape.
**It has not been reproduced since.** It is a lead for round 4, and the honest status is that
the harness will no longer show such a frame to a model or file a bug from it, while the thing
that made the frame is still unidentified.

One incidental measurement from the same probe, not a defect and not chased: `play3d` sizes its
renderer once, from the constants `W=1344, H=768`, with no `resize` handler anywhere in the
page. The canvas backing store is 1344x768 while CSS stretches it to whatever the window is
(1280x720 here) — a ~1.6% aspect stretch, and a window resize is not followed at all.
Reported, not fixed: it is a design call about what the game should do when the window changes.

#### PT-20260803-016 / -017 / -018 · VERIFIED · P0 — the overworld booted as a diorama

This one only became findable *because* the spawn was fixed. With the arrival no longer a
return, the agent stayed in `ow-valley` — and immediately could not play it.

**What the agent experienced.** Fourteen consecutive aim attempts, spread deliberately across
the whole frame — `[0.32,0.60]`, `[0.65,0.55]`, `[0.25,0.76]`, `[0.52,0.40]` — every one of
them answered *"is not ground you can walk to."* It filed three reports in one run and then
gave up: *"Cannot move or interact with the valley map screen"*, *"Valley map ground is
non-walkable"*, *"Unable to move character on this map view after trying multiple coordinates
across the screen, so I must give up."*

**Note the words it chose: "map screen", "map view".** Open `run-20260803-192758/frames/step-010.jpg`
and that is precisely what it is — **a tabletop diorama of the entire valley**, the terrain tile
floating on a brown backdrop seen from far above, three red portal markers on it, the Chapter
Two objective across the top, and **no character anywhere**. The agent was not confused. It was
describing the screen accurately, and the diagnosis in its own words was better than any of our
gates managed.

**What the instruments said.** The camera was at `[-4.00, 236.00, 212.00]` — 200 m above a body
standing at `[-57.85, 26.72, 60.58]`. That is the region GLB's own baked overview camera, and
the follow camera did not exist. `play3d.html` says the same thing about the same scene in two
regexes eighteen lines apart, and only one of them knew about the overworld:

```js
line 30   RT    = q.get('rt') || /(^|-)townwalk$/.test(SCENE)     // no ow-
line 48   OWCAM = /^ow-/.test(SCENE)                              // ow-
```

The follow camera is built and assigned **entirely inside `if(RT)`** in `frame()`. With `RT`
false there is no follow camera at all, so `cam` stays whatever the bundle baked. `ow-*` scenes
were getting overworld *lighting* and overworld *sky* and no overworld *camera*.

Measured with the playtester's own picker — lifted out of the adapter source rather than
copied, so the probe cannot drift from the thing being tested — on a 5x5 grid of screen points
at the `ow-valley` bundle spawn:

| | camera | pixels that hit a surface | on the walk network |
|---|---|---|---|
| as shipped | `[-4.00, 236.00, 212.00]` | **0/25** | 0/25 |
| with `&rt=1` | `[-55.10, 50.64, 27.91]` | **25/25** | 5/25 |
| after the fix, no `rt` in the URL | `[-55.10, 50.64, 27.91]` | **25/25** | 5/25 |

**It is not a regression from the spawn fix.** The control at the *old* spawn gives the
identical overview camera and the identical 0/25 — the diorama was there all along.

**Why no gate had caught it.** It hit every entry into the overworld *except one*: the in-place
swap from a page that booted somewhere else. That is the single path `playthrough_test`,
`transition_test` and `seam_test` all take. Checkpoint drop-ins, dev jumps and QA links — every
way a human or a tool visits the overworld directly — got the diorama. **A suite that only ever
enters a scene by the front door cannot tell you the side door opens onto nothing.**

**What changed (`10ea7a4`).** `ow-` added to the `RT` test. Gates re-run on a quiet machine,
both exactly at baseline: `playthrough_test` **86 passed / 0 failed**, `transition_test`
**168 ok / 0 failed**.

`public/play3d.html` is coordinator-owned; this is a one-line, one-regex change to it, recorded
here and in the commit so the owner sees it.

#### PT-20260803-009 · CLOSED by rule 3 — the playtester finally re-saw it, and said nothing

This was round 3's first job and the one open item from round 2: the fix for *"camera detached
or character missing after battle"* was verified on `SIM.occ` but **no run had reached an
`ow-valley` battle since**, so by rule 3 it was not done.

Run `run-20260803-195450` reached one. Straight out of the log:

| step | scene | battle | meanL | what happened |
|---|---|---|---|---|
| 4–7 | `ow-valley` | MEADOW, ROUND 1 | — | a random encounter: Reed Nibblers, fought through the menus |
| 8–14 | `ow-valley` | MEADOW, ROUND 2 | 96 | Vesper *and* Lake both given Attack and a target |
| 15–17 | `ow-valley` | MEADOW | 45 | victory, and the Victory screen dismissed |
| **18** | **`ow-valley`** | **none** | **110.23** | **back on the map, frame ready, shown to the model** |

**Zero reports.** The agent entered an overworld battle, won it, came out the other side onto
the exact class of frame that produced PT-009 in round 2, and did not file anything. The
circuit is closed and the entry can come off the open list.

The honest qualification, because this log is worth more if it states its own limits: that is
**one** post-battle frame, at a different spot in the valley from the one PT-009 was filed at,
so it is evidence the defect is not ubiquitous rather than proof it is gone everywhere. The
instrument evidence from round 2 remains the stronger half — the marker fires where the
character is hidden and at none of the three controls.

**A second thing this run settles, quietly.** Every menu step reads `chose 0 (cursor was on 0)`.
The agent could see where the cursor was, measure it, and act relative to it — through a
two-character battle with target sub-menus. That is the percept fix from the top of this round
actually working, as opposed to yesterday's, which shipped and did nothing.

#### Round 3 — the receipt: the loop turns, and how far the agent got

`node tools/llm_playtester.mjs --port=3000 --from=ch1.done --steps=45 --stop-beat=ch2.arrive`,
run `run-20260803-195450`, quiet machine, one run only — which is itself a lesson from earlier
in this round.

```
  steps        24
  beats fired  all 19 of Chapter One, through ch1.done
  reports      0
  walk legs    2
  finished     harness-blind
```

**Reports filed: 0.** Against the same build and the same ground that produced five P0/P1
blockers three runs earlier.

**How far it got, which is the number that says whether this loop is worth continuing.** Round 1
died at step 6 on a black screen. Round 2's closing run walked but never reached a battle. Round
3 dropped into the Chapter One → Chapter Two handoff, stayed in the overworld instead of falling
back through the door, crossed the valley, **fought and won a random encounter through the
menus with a two-character party**, dismissed the victory, and returned to the map still
playing. That whole sequence was unreachable this morning — twice over, once because the arrival
was an exit and once because the overworld had no camera.

**What is still not right, stated plainly.** The run ended `harness-blind`: from step 19 the
page stopped answering, six unready steps in a row, and the harness stopped itself with
*"THIS IS AN INSTRUMENT FAULT. No bug was filed against the game, on purpose."* That is the
round-1 rule working exactly as designed — it refused to invent a bug out of its own blindness —
but a loop whose closing run goes blind at step 19 is still a loop that cannot run long. The
page going silent after a battle in `ow-valley` is the top lead for round 4, and it is genuinely
unknown at this point whether it is the game or the harness.

### Open going into round 4

  * **The page goes silent after an `ow-valley` battle** (run `run-20260803-195450`, steps 19–24;
    also seen in the two killed runs earlier in this round as repeated
    `did not answer in 12000 ms (captureScreenshot)`). Game or harness is undetermined. Highest
    value next measurement, because it is what caps run length.
  * **PT-20260803-013/014's 64x36 thumbnail has no cause.** The probe-poisoning hypothesis is
    refuted and the memory-pressure one is unmeasured. Not reproduced since. The harness will no
    longer show such a frame to a model.
  * **Two concurrent playtester runs is too many on this box** for a scene as heavy as
    `ow-valley`. Both starved into `captureScreenshot` timeouts and had to be killed; the single
    quiet run that replaced them is the one that got a battle. Round 3's own contribution to the
    house rule: **one run at a time in the overworld.**
  * **Reported, not fixed — a design call for the user.** `play3d` sizes its renderer once from
    the constants `W=1344, H=768` and has no `resize` handler at all. The canvas backing store
    is 1344x768 stretched by CSS to whatever the window is, so the picture is ~1.6% off-aspect
    at 1280x720 and a window resize is not followed. Harmless today, a real annoyance on a TV.

### Round 4 — 2026-08-03 · the page was never dead. We were standing on its air hose.

Round 3 ended with the honest admission that nobody knew whether the post-battle silence was
the game or the harness. It was the harness, and the mechanism turned out to be the harness's
own keyboard.

#### The symptom, and why it was worth being careful about

Run `run-20260803-195450` fought a real random encounter in `ow-valley` (Reed Nibblers,
MEADOW, two rounds), won it, dismissed the victory card, and produced a good frame at step 18.
Steps 19–24 then came back blind, six in a row, each waiting ~50 seconds and reporting *both*
"the page's main thread did not answer the readiness gate in 6000 ms" *and* "the page never
returned a screenshot". The run stopped itself.

If that had been the game it would have been the worst bug in the repo: **win a random
encounter in the overworld, then be unable to continue** — and no gate we own would have seen
it, because `playthrough_test` never fights, `transition_test` does not battle and
`battle_sim` has no page.

#### What the instruments said, in the order they said it

**`percept_test`: PASS, 159/160, in 1.1 seconds.** So the adapter could still see a battle, a
dialogue, a veil and the overworld. Not the eye this time.

**The renderer was healthy the whole time.** Driving a real `ow-valley` encounter to victory
over CDP with the playtester's own Chrome flags (real GPU, `--headless=new`) and watching the
process rather than the page:

| | |
|---|---|
| renderer process | **alive throughout** — no `Inspector.targetCrashed`, no `executionContextsCleared` |
| renderer physical footprint (`vmmap`, not `ps rss`) | **~900 MB, flat** across the battle and after it |
| JS heap (`Performance.getMetrics`) | **12 MB** |
| `UILOCK` after the victory | **not held** |
| `Battle.active` after the victory | **false** |
| `Encounters._debug()` | **live** |

So the memory-pressure hypothesis carried over from round 3 is **refuted for this symptom**.
Nothing collapsed and nothing crashed.

**And yet `Runtime.evaluate` went silent for eight seconds while `Page.captureScreenshot`
answered normally.** That is a strange pair, and it is the pair that cracked it: a dead main
thread cannot do either. So the question stopped being "is the page alive" and became "what
is the main thread doing instead of answering us".

**Asked from inside the page.** A recorder that stamps every `requestAnimationFrame` and every
50 ms `setTimeout` and keeps the worst gap in each window, drained once per walk leg:

| | worst rAF gap | worst `setTimeout(…,50)` gap |
|---|---|---|
| a healthy leg | 10 ms | 53 ms |
| a leg where `Runtime.evaluate` timed out | 33–50 ms | **41151 ms** |

**The frame loop never stopped.** The game kept drawing at ~60 fps while ordinary tasks were
starved for forty-one seconds against a fifty-millisecond interval. `Runtime.evaluate` and
`Page.captureScreenshot` are ordinary tasks. The page was not frozen; it was too busy to
answer, and rAF's priority is exactly what hid that.

#### Busy with what: the harness's own keys

The same recorder counted key events. One `Input.dispatchKeyEvent` `keyDown`, held 400 ms:

| walk leg | key events the PAGE received |
|---|---|
| 0 | `w` down **1370**, up 1 |
| 1 | `w` down **2677** (after its keyUp), `a` down 1157 |
| 3 | `s` 1564, `a` 1563, `w` 1563, `d` 893 — **four keys, in lockstep** |
| 5 | `w` 9862, `a` 8105, `s` 4932, `d` 4931 |

**The keyUp never lands, so nothing is ever released.** By leg 5 four direction keys are held
at roughly three thousand events per second each, they cancel each other out, and the body sits
at one coordinate while the main thread does nothing but run keydown handlers. That is the
whole of "cannot move", "the page is busy" and "harness-blind".

#### Whose fault, settled by bisection

The events are **`isTrusted: true`, `timeStamp: 0`, `repeat: false`** — browser-generated, not
page-generated. Confirmed rather than assumed: trapping `EventTarget.prototype.dispatchEvent`
and `new KeyboardEvent` **before any page script runs**
(`Page.addScriptToEvaluateOnNewDocument`) records **zero** hits from either. Nothing in
`play3d.html` or any module dispatches a keyboard event; the whole page contains one
`dispatchEvent`, and it is the `eb-scene` CustomEvent.

One page, one set of flags, one dispatched key — the only thing varied is how Chrome was
launched:

| how Chrome was started | keydowns in the page from ONE dispatched keyDown |
|---|---|
| `about:blank` on the command line (control) | **1** |
| the game URL on the command line | **6387** |
| the game URL on the command line, then `Page.navigate` to it again | **6663** |
| `about:blank` on the command line, then `Page.navigate` to the game | **1** |

It is not scene-specific (`emb-cine` storms exactly like `ow-valley`), not `RT`-specific, and
not caused by `Emulation.setDeviceMetricsOverride`. **It survives a later navigation**, so the
property belongs to the target Chrome creates when it is handed a URL to open — which is
precisely what `adapter.open()` did.

**Only this tool dispatches real key events.** Every other browser gate in the repo drives the
game through `SIM`, which is why `playthrough_test` (86/0) and `transition_test` (168/0) were
green over this exact ground all day while the playtester could not walk across it.

#### What changed (`22db447`)

  * **Chrome boots at `about:blank`; the game arrives by `Page.navigate`.** The URL does not go
    on the command line, and the reason is written at the spawn so nobody puts it back.
  * **THE INPUT SENTINEL.** The harness counts the key events it dispatched; the page counts
    the ones that arrived (`__pt.keys()`). A divergence is reported, in `observe()`'s `why` and
    in a starved leg's `starvedWhy`, as **"INPUT STORM — THIS IS THE HARNESS, NOT THE GAME"**.
    Two integers, so this class can never again be read as "the page's main thread is busy".

**It also retires three earlier entries' explanation.** Rounds 0 and 2 recorded walk legs at
4769, 42127 and 210402 ms per burst and blamed machine load, and PT-001/-003/-004 and
-010/-011/-012 were all filed out of legs that closed 0 m. Under the fix a leg closes 14.74 m
of an intended 15.11 m in **1770 ms, at 161 ms/burst**. The load was real; it was not the
cause. **A cost that only ever appears in your own instrument is a cost your instrument is
creating.**

#### PT-20260803-019 · REFUTED — and it is the same lesson, twice in one round

The closing run filed a P0: *"Battle softlocks after defeating the enemy. The message says
'Duskpad is defeated!' and the enemy model is gone, but the battle doesn't end."*

The battle had ended four steps earlier. From the run's own `run.jsonl`:

| step | what the percept says |
|---|---|
| 7–11 | FOREST, ROUND 1, Duskpad, fought through the menus |
| **12** | `"Duskpad is defeated!"`, foes `[]` — **the report is filed here** |
| 13–15 | the Victory card (meanL 36.7, `UILOCK` held) |
| 16 | no battle, `UILOCK` released, walking |
| 17–45 | still playing, twenty-nine more steps |

**This was the harness again.** The stuck detector measures metres moved over a six-step
window — and a battle is exactly a window in which zero metres is *correct play*. It fired at
step 12 because the body had not moved since step 7, the battle's first step, and the
interview it paid for produced a P0 against a fight that had already been won.

Fixed in `episode.mjs`: a step in which `UILOCK` is held, or a battle, dialogue or full-screen
card is on screen, is **dropped** from the window — it neither counts toward it nor resets it —
so six genuinely motionless free-roaming steps still fire. This does not hide a real modal
freeze: "`UILOCK` held with nothing drawn on it" is a different question, asked by the frame
gate's own `frozen` check, which files its own blocker. Proven by replaying both versions of
the detector over the recorded 45 steps: **the old one fires once, at step 12, with a battle
on screen and `UILOCK` held; the gated one fires zero times.**

#### Round 4 — the receipt: the loop turns, and the cap is gone

`node tools/llm_playtester.mjs --port=3000 --from=ch1.done --steps=45 --stop-beat=ch2.arrive`,
run `run-20260803-203813`, on a machine at the same 70% swap that produced round 3's blindness.

```
  steps        45   (round 3 stopped at 24)
  finished     ran out of steps   (round 3: harness-blind)
  walk legs    65 — 50 arrived, 19 aimed off the walk network, 1 interrupted
  median leg   0.89 of the distance closed
  reports      2   (one refuted above, one a known duplicate)
```

**Not one blind step in forty-five.** `percept_test`'s replay of the run says it in the form
that matters: *"45 step(s) of run-20260803-203813 checked; 45 shown to the model."* Round 3's
run put 17 of 24 in front of the model and gave up.

The run **fought and won a second overworld battle** (Duskpad, FOREST) through the menus with
a two-character party, took the Victory card, and walked on for twenty-nine more steps. That
is the thing round 3 could not do, and it is the closing condition this round was given.

**What is still not right, stated plainly.** The agent spent steps 20–45 wandering `ow-valley`
and `emb-cine` without reaching Dellhollow: it can walk now, and it is not lost in the sense of
being stuck, but the road to Ch2 is not legible to it. Nothing was filed, so this is an
observation from the log rather than a report. It is the natural next question for round 5, and
it is a question about the *game* — which is where this loop has been trying to get since
round 1.

### Open going into round 5

  * **The valley road to Dellhollow is not legible.** 26 steps of goto in `ow-valley` and back
    through `emb-cine` without arriving, and the agent never filed a complaint about it. Worth
    a run with a bigger step budget before assuming it is a design problem.
  * **PT-20260803-013/014's 64x36 thumbnail still has no cause.** Unchanged from round 3.
    The probe-poisoning hypothesis is refuted, the memory-pressure one is unmeasured — though
    round 4's finding that the renderer stays at a flat ~900 MB through an overworld battle
    makes memory pressure a weaker candidate than it looked. Not reproduced since.
  * **Reported, not fixed — a design call for the user.** `play3d` sizes its renderer once from
    `W=1344, H=768` and has no `resize` handler. Carried from round 3, unchanged.

### Round 5 — 2026-08-03 · the road to Dellhollow had no visible marker on it, and the drop-in was at the wrong end of the valley

Round 4 handed over one thing, and it was about the game rather than the harness: *the agent
spent 26 steps failing to reach Dellhollow and never complained.* Silent navigational failure —
a player who is lost and knows it consults the map; a player who is lost and doesn't know it
quits. This round measured the corridor and found two causes, one in the game and one in the
instrument, and it is the second that had been quietly distorting the first.

#### What the agent actually did, out of round 4's own log

`run-20260803-203813`, plotted from `run.jsonl`. It is not a wander. It is a wrong turn:

| steps | where | what |
|---|---|---|
| 2–16 | `ow-valley`, z 60.6 → 41.6 | walking north up the valley road, incl. a won battle |
| **17** | `[-50.2, 26.1, 26.1]` | *"standing near an archway with an 'Enter Emberbrook? [E]' prompt"* — **took it** |
| 18–45 | `emb-cine`, z −50 to −110 | 28 steps oscillating between four spots inside the town it had just left |

The agent's own words at step 6 name the trap before it springs: *"a dirt path leads through a
lush valley up towards a stone archway marked by a red triangle icon."* **The Old Gate stands ON
the road to Dellhollow.** It is the way through, and it is also a door into Emberbrook, and the
only thing on screen saying which was an anonymous red triangle.

#### The measurement: what is visible along the corridor

`tools/playtest/marker_probe.mjs` — boots `ow-valley` with Chapter One's flags set, teleports to
eight stations along the 141 m from the arrival to the Dellhollow gate, sets the camera yaw the
way play3d's own heading-follow would have it for a player walking the road, and reads **the
marker layer's own DOM output** (`#exit-markers`), so the probe cannot drift from `markersTick`.

| station | dist to Dellhollow | markers actually drawn |
|---|---|---|
| A the arrival | 141 m | `Enter Emberbrook` 5.0 m · `Enter Emberbrook` 35.0 m |
| B road-mid | 131 m | both Emberbrook markers · **Dellhollow at screen y −34 px** |
| C gate approach | 119 m | `Enter Emberbrook` 4.3 m · **Dellhollow at y −32 px** |
| D gate court | 106 m | `Enter Emberbrook` 9.0 m · **Dellhollow at y −21 px** |
| E east bank | 97 m | `Enter Emberbrook` 17.8 m · **Dellhollow at y −22 px** |
| F gorge | 63 m | **Dellhollow at y −0.4 px** |

Two facts, and neither is an opinion:

1. **Every marker a player can see on that road says Emberbrook**, and none of them says so out
   loud — the label only exists in the prompt, at 3.2 m.
2. **The one marker naming the destination is drawn off the top of the screen.** The frustum test
   admits a point out to 1.05 NDC; the `-30 px` lift then puts it above the top edge, where
   `MKBOX`'s `overflow:hidden` eats it. Five stations, screen y −34, −32, −21, −22, −0.4 px in a
   720 px frame. **IN FRAME IS NOT VISIBLE** — this repo's oldest lesson, arriving in the DOM.

#### What changed (`81e4a62`)

  * **Portal markers carry a name.** The edge's own `label` under the arrow — `Enter Dellhollow`,
    `Enter Emberbrook`, `Leave Emberbrook` — the same string the prompt uses, so a marker can
    never name a door it does not open. Zero authoring. Doors and cut bands stay bare: a town of
    named doorways is noise, and their ambiguity is local.
  * **The marker clamps into the viewport**, with 62 px of top inset to clear the objective
    banner (which was itself overlapping the Old Gate's marker at the arrival, measured at
    px 737,42 under a banner spanning x 460–820).

`play3d.html` is coordinator-owned; recorded here and in the commit so the owner sees it.
`trigger_probe`'s selector tightened to `> div[data-edge]` — a marker is a container now.

It works as a cue, and the agent's own perception is the receipt. Round 5's first run:
*"a red marker labeled 'Enter Emberbrook' ahead"* … *"one behind me for Leave Emberbrook"*. It
had never named an exit in five rounds.

#### And then the harness turned out to be standing in the wrong place

The first run under the fix went into Emberbrook anyway, on step 3, through the marker at its
feet. Which raised the question nobody had asked: **is that where Chapter One leaves you?**

It is not. `--from=ch1.done` — the drop-in this entire loop runs from — carried `pos: null`,
because `checkpointsFromStory` reset the position on a scene change, so play3d fell through to
the BUNDLE spawn: the **south** end of the valley road, 5.05 m from Emberbrook's road gate and
141 m from Dellhollow. A player who actually finishes Chapter One steps through the **Old Gate**
— the beat before is `ch1.sendoff`, *"Step through the Old Gate"* — and arrives on the east bank
at `[-36.2, 23.3, 17.2]`, **97 m** from Dellhollow with the gate behind them.

**Two rounds of "the agent cannot find Dellhollow" were measured from the wrong end of the
valley.** This is round 3's PT-015 lesson in a third costume: an entry point that is not the one
the game uses is measuring a place the game never shows a player.

Worse, and only visible once the position was right: the yaw. Projecting each live edge with the
follow camera itself (`window._rtCam`) at that arrival —

| camera yaw | `Enter Dellhollow`, 97 m |
|---|---|
| the edge's own `spawnYaw` 2.3232 | **ndc [0.275, 0.981] — in frame** (and, thanks to the clamp, drawn) |
| `meta.json`'s generic `camYaw` | **ndc.z 1.055 — behind the camera** |

**What changed (`e35a657`, `0f1e0c5`).** A checkpoint now arrives by the edge the player would
have taken: among the scenegraph edges from the previous scene to this one, prefer the one whose
story flag the beats so far have SET (the Old Gate opens in Chapter One's climax) over an ungated
one, take nothing when none resolves — and carry that edge's `spawnYaw` through `urlFor` as
`?yaw=`. `ch1.done` → the Old Gate east bank; `ch2.arrive` → del-cine's valley-gate spawn;
`ch2.supper` → the cottage doorstep. All three were the generic bundle spawn before.

#### Round 5 — the receipt: the loop turns, and Chapter Two starts

`node tools/llm_playtester.mjs --port=3000 --from=ch1.done --steps=60 --stop-beat=ch2.arrive`,
run `run-20260803-221232`.

```
  step 2   [-36.2, 23.3, 17.2]   the Old Gate arrival, "Follow the valley road down to Dellhollow"
  step 3   [ 21.5, 14.4, -17.7]  one goto, four waypoints, 68 m of valley road
  step 4   ch2.road FIRES        "Down into the hollow — find whoever runs the locks"
```

**The corridor that took 26 steps and was never crossed is crossed in two walk legs, and
`ch2.road` is the first Chapter Two beat this loop has ever fired.** `frames/step-004.jpg` is
the whole round in one picture: the gorge road climbing to Dellhollow, and the marker on the gate
reading **`Enter Dellhollow`**.

**What it did next, stated plainly: it fell out of the world.** From step 5 it aimed *"down into
the hollow towards the locks"* — which from that camera reads as down the river — walked **past**
the gate and down the riverbed, and spent steps 5–60 at y −2 to −4.6 while the gate stands at
y 12.65. It filed `PT-20260803-025` and `-026`: *"the player and camera ended up underneath the
level geometry"*. Measured (sweeping `SIM.ground(x,z,fy)` over a column of `fy` from −12 to 34
and taking the distinct surfaces — a single high cast finds nothing, because `ground`
settles within a window around `fy`):

```
  gate      [44.9,-36.2]  floor stack 4.15 .. 16.17   zone crag
  transect  gate -> [76.1,-62.6]:  12.21, 10.6, 6.9, 5.4, 3.7, 3.7, 3.2, 1.1, -1.3, -3.0, -3.9, -4.18
  the body's resting places        y -2.03 .. -4.18   zone water
```

**It is not a hole.** The walkable surface runs continuously off the end of the intended play
area, down the gorge, under the water plane — no barrier, and the agent could not climb back
(legs closing 0.5–1 m of 9–10 m for fifty steps). **This is the next round's headline, and it is
a world-building call, not a marker one:** the valley's downstream end needs a stop, and the
Dellhollow gate needs to read as the way *up* out of the gorge rather than a thing you pass.

**Gates.** `transition_test` **168 ok / 0 failed** on a quiet machine, exactly at baseline;
`percept_test` PASS. Two earlier `transition_test` runs failed at `== BOOT` on `del-cine` and one
returned 165/3 — the same load-dependent flake CLAUDE.md already names. The page itself was
proven healthy independently by booting `del-cine` over CDP and reading its edges and prompt.

#### What is NOT fixed, and is a design decision for the user

  * **At the arrival the destination marker is behind you, not merely off screen.** The clamp
    rescues a marker inside the frustum; nothing rescues one outside it, and turning portal
    markers into a true off-screen compass is a look decision an FFIX-style game should make
    deliberately, not one a bug fix should smuggle in.
  * **A clamped marker is a compass, and this agent treats it as a destination.** In round 5's
    second run it read *"Step through the gate marked 'Leave Emberbrook'"* and aimed at the
    triangle — which the clamp had moved to the top of the frame, over sky. Measured against the
    engine, that ground was never the problem: 24/24 headings have floor at the stopping point,
    0/24 body-blocked, and a transect from z −122.6 to −130.6 is continuous with nothing blocked.
    A clamped marker probably wants to look different from a marker over its own door.
  * **In-town the red triangles are still anonymous**, because they are `cut` bands — camera
    seams, not places — and naming them would be noise. But they are the SAME RED as a town
    portal, which is what the lost agent chased for 28 steps in round 4 and 52 in round 5's
    second run. Whether a shot-exit should look like a town exit is the user's call.
  * **The objective banner does not know where you are.** *"Follow the valley road down to
    Dellhollow"* sits over Emberbrook's gate court and over a cottage roof deep inside the town.
    Carried from round 0.

### Open going into round 6

  * **The downstream end of `ow-valley` is a trap.** Walk past the Dellhollow gate and the ground
    keeps going down to y −4.2 under the water plane, with no barrier and no way back that 50
    steps of trying found. `PT-20260803-025` / `-026`. Highest value next fix — it is now the
    thing standing between the playtester and Chapter Two.
  * **`PT-20260803-022`: the camera is inside foliage at the Old Gate arrival** (`ow-valley`,
    `[-36.2, 23.3, 17.2]`). Filed on the first frame of the corrected drop-in. Seam canon has a
    lot to say about arrivals; unmeasured so far.
  * **PT-20260803-013/014's 64x36 thumbnail still has no cause.** Unchanged from round 3.
  * **Reported, not fixed — a design call for the user.** `play3d` sizes its renderer once from
    `W=1344, H=768` and has no `resize` handler. Carried from rounds 3 and 4, unchanged.

### Round 6 — 2026-08-03 · the world had no bottom, and the banner was pointing down the river

Round 5 handed over one finding: the player can walk out of the world. It closed with the agent
past the Dellhollow gate (y 12.65) and 56 of its 60 steps at y −2 .. −4.6, under the water plane,
with no barrier and no way back that 50 steps of trying found.

Before anything was built, the coordinator looked at `run-20260803-221232/frames/step-060.jpg` —
the drowned character and the objective banner in one picture — and read the banner:

> **"Down into the hollow — find whoever runs the locks"**

**The agent did exactly what the game told it to.** That reframes the round: this is two defects
wearing one coat, and only one of them is geometry.

#### The measurement: where the world leaks, and how far

`tools/playtest/edge_probe.mjs` (new) asks the RUNNING ENGINE, not the file:

  * **§1 CENSUS** — `SIM.floors` + `SIM.zone` at every cell of the region tile.
  * **§3 RETURN** — from a named place, 24 headings × N strides at play3d's own 0.075 stride:
    the best height regained. This is the number that decides *soft-lock* vs *level design*.
  * **§4 ESCAPE** — from an IN-BOUNDS seed, the deepest ground 24 headings can reach.

Two instrument bugs were paid for on the way, and both are recorded in its header because both
are general: a story beat firing under a probe raises **UILOCK**, which freezes `phys()` outright,
so one descent ran 50 legs and *every seed after it reported "1 leg"* — a probe that measures
nothing while looking like it measured. And §3's first numbers included a 52.5 u walk that
"arrived" 87 u away: `marooned()`, play3d's own 600-tick stuck-recovery, firing inside the probe.
§3 now carries a **walk-budget self-check** — a body walking `n` strides of `SPD` can be at most
`n·SPD` from where it started, and anything further is reported as `IMPOSSIBLE: not a walk`.

The tile, on a 4 u lattice (70 × 50 cells, runtime x −140..140, z −100..100):

```
  standable-top surface   3031 / 3500 cells      y -6.07 .. 50.67
  cells below y = 0        126 (3.6%), in EXACTLY TWO connected components:
     the Long Reach   x  50..114   z -98..-50   floor to -6.07   zone water
     the tile apron   x = 138      z -98.. 78   floor ~ -4.0     (the terrain tile's own skirt)
```

**It is not a hole and it is not a bug in the builder — it is the builder's own decision, read
back.** `tools/valley_map.py` suppresses the north/south/west rims *and* the east escarpment
within 22 u of the river channel, in its own words:

> `# A RIM CANNOT STAND IN THE RIVER.` … *the rim runs out at x~210, where the gorge's own walls
> take the river on to the Long Reach*

That breach exists so Chapter Two's boat can leave the Moorage. It is correct for the boat and
fatal for the walker: an analytic height field has no edge, so the ground simply keeps going.

#### The riverbed is level design. Measure before you fence.

The lowest **authored** place in the region is `valley.region.json`'s `boat-tar` landmark — the
Moorage boat — at world `[200.96, 152.87, 1.30]` = runtime `[61.0, 1.30, −52.9]`, measured floor
**y 1.71**. The three valley portals stand at elevation 12.01, 26.5 and 27.1. Nothing the game
authors is below zero. And returnability, measured before choosing anything:

| from | floor | best climb, 24 headings | to |
|---|---|---|---|
| the Moorage | 1.71 | **+25.2 u** | y 26.95 |
| round 5's resting place `[76, −62.6]` | **−4.21** | **+17.0 u** | y 12.77 |
| the Long Reach, deep `[102, −86]` | −5.61 | +9.8 u | y 4.15 |
| the tile apron `[138, −20]` | −3.96 | +7.2 u | y 3.21 — **and the meadow above it is y 20** |

So round 5's pit is not geometrically one-way: one heading in twenty-four climbs 17 u out of it.
**It is a navigation trap, not a wall of the world** — which is exactly why a barrier alone was
never going to be the whole fix, and why the coordinator's read of the frame was right.

#### What changed (`f1f5243`)

**1. The world gets a bottom, as map data.** `public/game/worldbounds.json` — per scene, fetched
by play3d on boot, applied by `sceneParams()`. `ow-valley: { floorY: 0.0 }`. **One number closes
both components and nothing else**, because upstream the riverbed sits at y 23..27 and the rule
never fires at all: the shallow upper river stays waded, the Moorage stays open, and the bound
reads as a *shoreline* rather than as a fence — it only bites where the world actually stops.
It is committed, which is `lightrigs.json`'s lesson: a runtime data file that is not in git is a
bug that only reproduces off the author's machine.

**2. It is ONE-WAY by construction** (`outOfWorld()` in `walkStep`). Above the bound, a step onto
ground below it is refused. Below the bound, only steps that go *deeper* are refused — level and
uphill always pass. So a body already out there (an old save, a jump off the bank) walks back in,
and it is deliberately not a jump gate: you can still jump into the river, and then you can still
walk out. **A boundary that can strand a player is the defect it was built to fix, wearing the
other coat.** The ledge/fall branch is gated the same way, on the same rule.

The A/B, same page, same seeds, one number — because an instrument that finds nothing must prove
it could have found something (`--nobound` disarms the bound in the live page):

| seed | bound armed | `--nobound` |
|---|---|---|
| moorage bank `[61, −50]` | deepest **y 0.00** | deepest **y −3.00** |
| gorge road `[54, −46]` | deepest **y 0.00** | deepest **y −3.06** |

and 0/5 in-bounds seeds reach below the bound with it on, while every below-zero pit still climbs
out (`+17.0`, `+8.4`, `+7.9`, `+7.2` u). **The other three seeds do not move at all** — `gate court` reaches
y 1.93 either way, `east plateau` 15.46, `road lower` 9.63 — which is the specificity claim
stated as a measurement: the bound changes the world in exactly one place, the water line.

**3. The banner stops naming a direction.** `ch2.road` fires **at** the Dellhollow valley gate
(`at [44.88, 12.01, −36.19]`, r 30) — so the line that tells the player what to do next is on
screen while they are standing at the door, and it said *"Down into the hollow"*. That is a
**place** written as a **heading**, and downhill is precisely the wrong way. It now reads:

> **"Through the Dellhollow gate — find whoever runs the locks"**

which is also what the exit marker on that gate reads since round 5. The *prose* keeps "down" —
Lake's *"Down, then."*, and the system line about a town stacked down the inside of a gorge — because
the town genuinely is down there; it is the persistent banner that has to name the door. The why
is recorded in the beat's own `_doc_objective`. `dialogue_style` **PASS, 0 failures**;
`story_test` **1104 ok / 0 failed**.


#### Round 6 — the receipt: the agent walks into Dellhollow

`node tools/llm_playtester.mjs --port=3000 --from=ch1.done --steps=60 --stop-beat=ch2.arrive`.

**Run `run-20260803-230413`:**

```
  step 2   [-36.2, 23.3, 17.2]   the Old Gate arrival
  step 3   [ 21.1, 14.5, -18.2]  one goto, the valley road
  step 4   ch2.road FIRES        "Through the Dellhollow gate — find whoever runs the locks"
  step 5   [ 44.0, 12.6, -35.3]  goal="Interact to enter Dellhollow."
  step 6   del-cine [4.9, 24.1, -6.5]
```

**Step 6 is `del-cine`. THE AGENT IS INSIDE DELLHOLLOW** — the first time in six rounds, and
one step after the beat whose banner used to point down the river. `frames/step-005.jpg` is the
round in one picture: the banner reading *Through the Dellhollow gate*, the marker reading
*Enter Dellhollow*, the prompt reading *Enter Dellhollow? [E]*, the character on the road at the
gate — and the gorge that swallowed round 5 filling the left third of the frame, unmistakably a
drop rather than a way on.

That run then died — **on the harness, at the very step it succeeded.** `del-cine`'s shot is named
`gate`; the new objective contains the word "gate"; and the objective travels to the agent inside
the harness-authored **brief**, which is what the firewall's SOFT check scans. The firewall's own
doctrine already says soft tokens are *"NOT checked against the text the game drew … a player is
allowed to know the word square"* — the objective was simply on the wrong side of that line.
`briefAuthored` now splits the brief exactly as `nudgeAuthored` already splits the nudge: the
drop-in brief is ours, the quoted banner is the game's (`2b06873`).

**Run `run-20260803-230631`, the fence in live play.** This one wandered — and that is the more
useful receipt, because it is the same wander round 5 died in:

```
  step  9   [69.0, 0.00, -55.0]   down the gorge toward the water — AND STOPS AT THE BOUND
  step 20   [62.7, 0.80, -63.3]   downstream along the water line, still y 0.8
  step 21   [58.4, 5.70, -45.7]   CLIMBS BACK OUT, on its own, toward the gate
```

**y over the whole run: 0.00 .. 23.29.** Round 5's identical wander spent 56 steps at −2 to −4.6.
The body reached the bound, walked along it, and came back up — which is the one-way rule doing in
play exactly what §3 measured on the bench, with no invisible wall to press against: the shoreline
stopped it, and the way back was open the whole time.

It then ran out of steps at 60 without reaching `del-cine`, **and the reason is not the boundary**:
**32 of its 60 steps were spent inside battles** in the gorge and at the water line. It filed two
reports — `PT-20260803-028` (the Moorage looks broken; see round 7 below) and `PT-20260803-027`,
the harness's own off-spine detector firing the long-carried "the player can leave the chapter"
class. **Two runs, two different endings, and neither of them is round 5's ending:** the y floor
across both is 0.00, against round 5's −4.6.



### Open going into round 7

  * **The Moorage LOOKS out of bounds, and the agent said so from inside the world.** At step 18,
    standing legitimately at `[69.0, 0.00, −55.0]`, it filed *"Glitched view and out-of-bounds
    geometry after battle … floating collision blocks and open void"*. It is wrong about the
    cause — it is in bounds, on real ground — but it is **right about the picture**:
    `frames/step-009.jpg` is a bare gorge wall, a water plane, and Dellhollow's impression decks
    reading as *submerged*. The barrier fixed where the player can go; nothing has yet made that
    place look like somewhere they are meant to be. **This is the natural round-7 headline** —
    and note the shape of it: a fence that stops a player at a view they think is broken has
    moved the complaint, not answered it.
  * **The corridor's encounter rate eats the run.** In `run-20260803-230631`, 29 of the first 47
    steps were spent inside battles in the gorge — the agent fought three encounters in roughly
    twelve metres of walking. Nothing is wrong with any single battle; the budget is the problem,
    and a playtest step is not free. Worth measuring against `encounters.json`'s own rate for the
    `water`/`crag` zones before touching it.
  * **The tile apron is a second, smaller trap that the bound papers over rather than removes.**
    The column at x = 138 stands at y ≈ −4 for 45 cells of z, and the terrain itself caps anyone
    down there at y 3.2 while the meadow above is y 20. The world bound now refuses the step onto
    it, and the one-way rule means nobody can be stranded — but **whether it was reachable at all
    was never measured**, and "unreachable" is a claim this round did not earn.
  * **`PT-20260803-022`: the camera is inside foliage at the Old Gate arrival** (`ow-valley`,
    `[-36.2, 23.3, 17.2]`). Carried from round 5, still unmeasured.
  * **PT-20260803-013/014's 64x36 thumbnail still has no cause.** Unchanged since round 3.
  * **Carried from round 5, unchanged:** a clamped marker looks the same as a marker over its own
    door; in-town red triangles are anonymous `cut` bands wearing the same red as a town portal;
    `play3d` has no `resize` handler. All three are design calls for the user.
  * **`ch1.done`'s objective still says "down".** *"Follow the valley road down to Dellhollow"* is
    accurate — that road does descend — and round 5 and round 6 both crossed the corridor under it
    in one or two legs, so it is NOT the defect `ch2.road`'s was. Left alone deliberately; noted
    here so the next round does not re-litigate it blind.

### Round 7 — 2026-08-04 · the encounter rate was innocent, and the river turns white when you look along it

Round 6 handed over two things and asked for a number on each before anybody built anything.
Both got one. **Neither turned out to be the thing it looked like**, and in both cases the number
is what says so.

#### Handover 1 — the gorge encounter rate: REFUTED as a game defect

**The claim.** In `run-20260803-230631`, 32 of 60 steps went to battles; the agent ran out of
steps without reaching town, and the fighting, not the boundary, is what ate the run.

**What the instruments said.** `zones.json` is the encounter geography — an RLE grid the runtime
reads through `SIM.zone` — so the zone profile of a walked path can be measured **offline, with
no browser**, by decoding the grid and sampling every 0.5 u along the positions in `run.jsonl`.
Against `encounters.json`'s own numbers (a "step" is 1.0 world unit of travel, ratified in
`encounters.js`):

| run | walked | road | water | crag | meadow | forest | expected battles | **observed** |
|---|---|---|---|---|---|---|---|---|
| `run-20260803-230631` | 175.5 u | 34.5% | 29.9% | 25.5% | 6.7% | 3.5% | **4.48** | **3** |
| `run-20260803-221232` | 109.3 u | — | 100% | — | — | — | 4.37 | 3 |
| `run-20260803-230413` (on the road) | 28.5 u | **77.2%** | — | 12.3% | 10.5% | **0.28** | **0** |

**The corridor is not 172 metres. It is 28.6.** Round 6's own successful run walked the Old Gate
to the Dellhollow gate in three legs, 77% of it on `road` — which is `chancePerStep 0`, safe by
design — and fought nothing, exactly as the analytic predicts. The 175 u run walked *six times the
corridor* because it wandered off the road into the gorge and along the water line, and even then
it fought **three battles where its own zone profile predicts 4.48**. The rate is not high. It is
running slightly under its own spec.

**So what actually ate the run?** Not the rate — the *price*. Measured on the same log:

  * **a battle costs 10.7 harness steps** (3 battles, 32 steps)
  * **a walk leg costs 1 step and covers ~15 u**

One battle therefore costs the step-budget equivalent of about 160 u of walking. A 60-step budget
buys either ~15 legs of exploration or ~5 battles, and the corridor run drew the second hand.

**Recommendation, and it is deliberately not a retune.** `encounters.json` should not be touched
on this evidence: the measured rate is *below* its analytic mean, roads are already free, and the
one run that followed the route fought nothing. **Size the budget instead** — roughly 11 steps per
expected battle on top of the walking estimate, so an off-road `ow-valley` run wants 100+ steps,
not 60. The one number that IS worth putting in front of the user as a design question is the
walking time between fights off-road, because it is short: at the shipped `SPD` of 4.5 u/s, the
mean gaps work out to **forest 8.5 s · crag 9.1 s · water 10.0 s · meadow 13.6 s** of continuous
walking. On the road it is never. Whether "nine seconds off the path" is the intended texture is a
balance call, and this lane is not making it.

#### Handover 2 — the view the agent called broken, photographed on tonight's build

`PT-20260803-028` was filed from `[69.0, 0.00, −55.0]`, standing legitimately in bounds:
*"out-of-bounds geometry … floating collision blocks and open void."* Round 6 called it VERIFIED
AS A PICTURE, REFUTED AS A PLACE, and left it as an art problem at a coordinate.

**Round 6's frame is not evidence about the current game** — the ow bundle was rebuilt at 00:36
tonight by the lighting and overworld-content lanes. So the first thing this round did was go
stand there again. `tools/playtest/look_probe.mjs` (new, adapted from `ow_shot.mjs`: same CDP
pattern, `freePort`, own profile, cleaned on every exit path, hard self-expiry) boots `ow-valley`,
`SIM.tp()`s to a named coordinate and photographs a ring of yaws. It landed exactly where the
report was filed — `zone: water`, `ground y 0.0376` — and the defect reproduced.

**The picture is view-dependent, and the measurement is the whole finding.** Same position, same
build, same river surface, patch means off the written PNGs:

| camera yaw | what the river reads as | measured luminance |
|---|---|---|
| **+1.4** (looking downstream, the way the player walks) | a flat pale plane, **indistinguishable from sky** | **222.3** |
| −1.5 | teal, with its bed visible through it | **83.4** |
| +2.4 | teal, gorge and plank decks legible | 116.4 |

and the comparison that names the complaint:

| in the same frame | luminance |
|---|---|
| the river at yaw +1.4 | **222.3** |
| the sky | 189.5 |
| the gorge walls around it | 55 – 70 |

**At a grazing view angle the water is brighter than the sky, in a frame whose every other surface
is three times darker.** That is not "submerged decks" and it is not a glitch — it is a hole punched
in the picture, and *"floating collision blocks and open void"* is an accurate description of what
is drawn. The dark brown Moorage decks sit on top of it with nothing behind them.

**Where it comes from, stated as a mechanism and not a fix.** `tools/valley_build.py` carries
`GLASS_ROUGH = 0.06` — the user's own B1 glass-river pick of 2026-08-03, from
`docs/qa/ow-art/index.html` section B. Roughness 0.06 is a near-mirror, so the Fresnel term goes
to 1 at grazing incidence and the environment reflection dominates; `play3d.html:1570` sets
`NoToneMapping` for every `OWCAM` scene, so there is nothing to roll that highlight off and it
clips. Both halves of that are someone else's ratified decision — a dated user art pick and a live
lighting lane — so **this lane measured it and handed it over rather than turning a knob.**
Evidence frames: `docs/qa/playtest/round7/moorage-*.jpg`.

The good news in the same set: **from most angles the Moorage is genuinely handsome.** `yaw2p4`
is gorge walls, teal river, plank decks, a boathouse and greenery, and it reads as a place. The
defect is one arc of yaw, and it happens to be the arc a player walking downstream is looking
along.

#### A third thing, found by the same probe and NOT filed by any agent

At yaw +0.4 from that identical coordinate, **88.2% of the frame is grass cards** — the camera
boom is inside the new overworld grass dressing (`public/js/ow_detail.js`, added tonight). This is
the same class as `PT-20260803-022` (*"camera clipped inside foliage obscuring entire screen"*),
which has been carried unmeasured since round 5, and it is now measured on a live build. It
belongs to the overworld-content lane and is routed there, not patched here.

#### Round 7 — the receipt: the agent gets INSIDE Dellhollow, and into a building

`node tools/llm_playtester.mjs --port=3000 --from=ch2.arrive --steps=70 --stop-beat=ch2.lockfive`,
run `run-20260803-234940`. Round 6 reached `del-cine` and stopped there. This one drops in at the
arrival and plays the town.

```
  steps        70          scenes   del-cine 52 · del-inn-int 18
  walk legs    95 (67 arrived, median closed 0.63 m, ~160 ms/burst)
  beats fired  all of Ch1 + ch2.road + ch2.arrive        reports 1
```

**New ground, and it is worth naming.** For seven rounds this loop has lived in `emb-cine` and
`ow-valley`. This run walked a pre-rendered plate town, took a *cut* between two of its shots, and
then **opened a door and went inside a building** — `del-inn-int`, The Boatmen's Rest, lit, dressed,
a LOCKS DELAYED notice on the board. No playtest run had ever entered an interior.

##### VERIFIED · P1 — The Boatmen's Rest is a door onto an empty room

**What the agent experienced.** It entered the tavern at step 34 and spent **18 of its 70 steps**
inside, goal after goal: *"walk up to the NPC in the dark coat next to the notice board"*,
*"talk to the person standing by the notice board"*, *"explore the right side of the tavern to look
for someone"*. Nothing answered. The two figures in `frames/step-037.jpg` are **Vesper and Lake** —
its own party. It was trying to talk to itself.

**What the instruments said** (both files, no browser):

| | |
|---|---|
| `npcs.json`, records with scene `del-inn-int` | **0** |
| the same for `del-item-int` / `del-weapon-int` / `del-armor-int` | 1 each (chandler, weaponsmith, armorer) |
| `shops.json`, a shop whose `sceneKey` is `del-inn-int` | **none** |
| dialogue boxes in the whole 70-step run | **1** — `ch2.arrive`'s own arrival narration |

The inn is the one Dellhollow interior that ships as a bundle, carries a door prompt a player can
take (*"Enter The Boatmen's Rest? [E]"*), and **has nobody in it and nothing to do**. Every unit
gate in this repo is green over that, because no gate asks "does this room contain a person."
`del-cookhouse-int` and `del-boatyard` are in the same position and were not visited.

##### The spine detector filed a P1 because the player walked into a pub — REFUTED

`PT-20260803-029` is the eighth report of the long-carried *"the player can leave the chapter on
its first frame"* class, and this time it fired from `del-inn-int` at step 37. It is a **false
positive**, and a new shape of one: the rule is *"you left the set of scenes that still hold an
unfired beat and stayed gone"*, which is true and damning in `ow-valley` and simply wrong about an
optional interior entered by a door you can walk straight back out of. The agent left by that same
door six steps later. Kept in the log as calibration, per rule 2.

##### Measured, NOT filed — the agent crossed 24 metres of Dellhollow in 52 steps

The number that says what the town costs a first-time player:

| | |
|---|---|
| `del-cine` shots the run ever saw | **2** — `gate` (31 steps) and `shelf-west` (21) |
| its x range across 52 town steps | **4.9 .. 28.8** |
| where the objective's lockhead (`odessa`) stands | **x 78.9** |
| the nearest NPC to the arrival band | `del.deckhand`, ~15 m away and 5 m below |

For the first 31 steps it **oscillated between x 15 and x 28** — a pendulum in a 13 m corridor,
walking well (`median closed 0.63`, 160 ms/burst, the link healthy) and getting nowhere. Look at
`frames/step-020.jpg` and `step-027.jpg`: identical shot, and the only *labelled* thing in the
frame reads **"Leave Dellhollow."** The other two red triangles are `cut` bands wearing the same
red as a town portal. The agent's own goals name them — *"walk over to the NPC standing under the
red marker"* — and there is no NPC there.

**This is round 5's carried design call** (*"whether a shot-exit should look like a town exit is
the user's call"*), now with a price on it: **30 steps, and the arrival band of the town Chapter
Two happens in contains no NPC, no shop door and no labelled destination except the way out.**
It is not filed as a bug because the remedy is a look decision, and this lane does not make those.

##### A harness defect found in this run's own log, and fixed

Three legs printed `leg not conclusive: gave up after N burst(s) at ~160 ms/burst — no blocker
filed (the headings were never all tried)`. **160 ms/burst is a healthy link, and the headings
HAD all been tried.** Those legs exited on `sinceGain >= 8` — the body moved on every round and
never got closer — and were falling into the starvation branch, so a real navigation answer
("walkable, but not toward the goal") was being printed as an excuse about a slow machine. That is
the exhausted/starved split from round 2 with a third case nobody had separated. `walkLeg` now
returns `noGain` and `episode.mjs` prints its own sentence for it. Neither files a blocker.
`percept_test` PASS.

### Open going into round 8

  * **The Boatmen's Rest has nobody in it.** VERIFIED above on `npcs.json` + `shops.json`.
    `del-cookhouse-int` and `del-boatyard` are in the same position and unvisited — worth the same
    two-line check before a run wastes 18 steps in one of them.
  * **`ch2.jam` has never been reached by a playtest.** The run spent 52 steps in `del-cine` and
    covered 24 m of a town whose objective stands 50 m further on. Whether the route is legible is
    the question; whether it EXISTS is not in doubt (`playthrough_test` §W walks it).
    **A `--from=ch2.jam` drop-in is the cheapest way to test the rest of Chapter Two** without
    paying 30 steps for the arrival band again — and it is the next round's first job, along with
    a shop, and a save/reload taken mid-chapter, neither of which any run has touched.
  * **The gorge water is brighter than the sky at one arc of yaw** (222.3 L vs 189.5). Measured
    above; belongs to the lighting lane and to whoever owns the B1 art pick.
  * **The camera boom sits inside the new overworld grass** (88.2% of frame). Overworld-content lane.
  * **The spine detector needs to know an optional interior from a wrong turn.** Eight reports of
    one class, and the newest is a pub.
  * **PT-20260803-013/014's 64x36 thumbnail still has no cause.** Unchanged since round 3.
  * **Carried, unchanged:** a clamped marker looks like a marker over its own door; `play3d` has no
    `resize` handler; the objective banner does not know where you are (now also true inside an inn).

### Round 8 — 2026-08-04 · the act of loading a save was destroying it

**The headline is a P0 that no gate in this repo could have caught, and it was found by
building the instrument the tool had been asking for since Chapter Two was wired.**

#### The run, and the blocker that ended it

`node tools/llm_playtester.mjs --port=3000 --from=ch2.jam --steps=120 --stop-beat=ch2.dock`,
run `run-20260804-013303`. It died at **step 46** on
`HTTP 429 {"error":{"code":429,"message":"Your prepayment credits are depleted..."}}` from
AI Studio. **That is a spend blocker, not a defect** — the harness kept its shape (it
degraded into `wait goal="recover"` rather than filing anything) and was killed by hand.
The rest of this round ran on the instruments that need no model.

What it got before it stopped, which is new ground again:

| | |
|---|---|
| step 1 | `ch2.jam` fires on its own trigger — **Odessa speaks, 7 lines read** |
| steps 2–11 | walks the lockhead, takes a silent cut west into `quay-west` |
| steps 12–45 | **34 steps inside `quay-west`**, x 37 → 53, never leaving deck level |
| steps 29–34 | goes into `del-cookhouse-int`, finds nobody, comes back out |
| reports | 1 (`PT-20260804-002`, refuted below) |

**The lockkeeper works.** For the first time a playtest has reached a named Chapter Two
character on that character's own trigger and read her out. Everything after it is the
question of whether the town says where to go next, and the answer is measured below.

#### THE P0 — `at.pos` was `[0, 2, 0]`, and it was written by loading the game

`tools/playtest/save_probe.mjs` is item 4 on `llm_playtester`'s own "covering Chapter Two"
list, written there when Ch2 was wired and never built: *"A SAVE/RESUME PROBE. Ch2 is where
a player stops for the night."* On its first run it failed on an assertion nobody had ever
made: **the position in the save was not the position of the player.**

Measured directly, `del-cine` booted at the `ch2.jam` checkpoint with a non-empty beat
ledger (so the autosave is armed, exactly as in a real playthrough):

| | body | shot | `at.pos` on disk | `at.cam` |
|---|---|---|---|---|
| t = 0 s | `[0, 2, 0]` | null | `[0, 2, 0]` | null |
| t = 3 s | `[78.93, 14.07, −15.6]` | `lockhead` | **`[0, 2, 0]`** | **null** |
| t = 20 s | `[78.93, 14.07, −15.6]` | `lockhead` | **`[0, 2, 0]`** | **null** |
| after one `'eb-scene'` | same | `lockhead` | `[78.93, 14.07, −15.6]` | `lockhead` |

`story_runtime.arm()` runs the moment the module loads — **before `play3d` has read
`sx/sy/sz` off the URL and before a cinematic scene has chosen its shot** — and `recordAt()`
faithfully wrote what it was shown. `at` is *the* resume authority
(`docs/plans/end-to-end-wiring.md` §5), so the consequences are both of these:

* a player who loads, walks around **inside one scene**, and closes the tab comes back
  somewhere else — `[0,2,0]` is not a place in Dellhollow, so CONTINUE falls through to
  whatever the bundle spawns;
* **a save that was correct on disk is overwritten with the placeholder by the act of
  loading it**, before the player touches anything.

It needs no scene change and no beat to bite; it needs a player to stop between them, which
is what stopping for the night IS. Every gate was green over it because every gate in this
repo writes the save from the inside: `playthrough_test` builds `at` itself, `--from=`
patches localStorage directly. **Nobody had ever pressed Escape, chosen SAVE, quit and come
back.**

**The fix (`story_runtime.js`).** `recordAt()` now refuses to write a scene that has not
arrived — a pre-rendered scene that has not chosen a shot has not arrived; a real-time
scene has no `cine()` and is judged on position alone, which is exactly its old behaviour.
Recording *nothing* leaves the previous `at` standing, which is the right answer: stale
beats wrong. `arm()` polls for arrival (250 ms, ~15 s ceiling, fires once) so the record
still happens on a cold boot, and `tick()` refreshes `at.cam` when the shot cuts —
**in memory only**, so a manual SAVE writes the shot the player is looking at while a shot
cut adds no localStorage write of its own.

Re-measured: `at.pos` is the body's position from the moment the scene arrives, and the
full round trip is green.

```
save_probe --from ch2.jam
  §0 the arrival cutscene closed              14 boxes read through
  §1 the body moved off the drop-in           2.01 m
  §2 Escape opens a menu                      6 rows ·  SAVE is row 3
  §3 at.pos is where the player was standing  [79.80,14.04,-17.27] vs body [80.05,14.04,-17.27]
  §4 same scene / same shot / same place      del-cine · lockhead · 0.25 m
     beats 22 -> 22 · flags 24 -> 24 · party vesper+lake -> vesper+lake
  PASS 15/0
```

#### FOUR of this probe's own failures were the probe, and they are worth listing

Rule 1 applies to instruments as hard as it applies to agents. The first run of
`save_probe` reported *six* failures. **Only one was the game.**

| what it reported | what it was |
|---|---|
| "`at.pos` is not where the player stood" | **the real defect above** |
| "Escape opens no menu" | it read `.ebui-row`; the pause menu draws `.mn-navrow` |
| "the body will not move" (0.07 m in 5 s of held keys) | a `keyDown` with no `text` field — the adapter has set it all along |
| "the body will not move" (before that) | the probe walked *during* the arrival cutscene, which holds UILOCK |
| "same shot failed" | a consequence of the two above |
| — | the four rAF throttling flags, added on suspicion and **measured not to be the cause** |

The `text` one is the keeper: **a single missing CDP field turned a walking body into a
paralysed one and would have been filed as a game bug by anything that did not check.**

#### The percept could not read the pause menu (harness defect)

Found while chasing the above, and it is the `cur` lesson again one panel over. `menu.js`
renders with `layout:'full'`, whose nav list is `.mn-nav > .mn-navrow` — **not** the
`.ebui-row` every other `ui_kit` panel draws. Measured on the live game: Escape opens the
menu (`Menu.isOpen` true, one visible veil, `PARTY EQUIP ITEMS SAVE LOAD NEW GAME` in the
DOM) and **the percept returned zero rows**. An agent that paused was handed an empty list,
so no playtest could ever have saved, equipped or used an item. Fixed in the percept's row
union, with a fifth `percept_test` fixture built from that live DOM dump and `menu.js` added
to the selector census — `.mn-navrow` is now load-bearing, so a rename goes red instead of
blind. `percept_test` **PASS 342/342** (and the vestigial `.ebui-choice` warning is gone,
because that alternate was what `.mn-navrow` replaced).

#### PT-20260804-002 — the ninth "leave the chapter on its first frame", and the fix

It fired at step 29 from `del-cookhouse-int` and the agent left by the same door at step 35.
Round 7 predicted this shape exactly. `scenegraph.json` already classifies every node, and
`del-cookhouse-int` is `kind: "interior"`, so the detector now asks the game instead of
guessing: **an interior is a room, not a wrong turn.** What *is* worth saying about that room
is a different sentence, so the **empty-room detector** says it — twelve turns inside an
interior with no dialogue, shop or menu ever opening files one report naming the room.

That detector has two customers already: `del-inn-int` cost round 7 eighteen of seventy
steps, and `del-cookhouse-int` cost this round six. Both ship with **zero** `npcs.json`
records, as does `del-boatyard`.

#### 34 steps in one shot — VERIFIED as legibility, REFUTED as connectivity

The agent walked well the whole time (`median closed 0.63 m`, ~157 ms/burst, the link
healthy) and got nowhere. Before calling that a maze, the world was asked whether the route
exists, with `reach_probe` **inside the running page** — the engine's own rays and body box:

| pair | verdict |
|---|---|
| deck `[41, 14.07, −18.4]` → lock apron `[79.7, 0.83, −27.13]` | **reachable**, 39.7 m apart, 2469 cells, via 2 in-scene edges |
| lockhead → lock apron | **reachable**, 11.6 m apart, 2631 cells, via 3 in-scene edges |
| deck → the deep-stairs entry seam | **reachable**, 3.6 m, on foot |
| deck → lockhead (back east) | **reachable**, 38.0 m, via 1 in-scene edge |

**Nothing is walled off.** So the question is what the town tells you, and the town's own
audit layer answers it. Out of `del-cine`'s 49 outbound edges in `scenegraph.json`:

| kind | count | labelled? |
|---|---|---|
| `cut` | **40** | **none** — `play3d.html:2627`: *"a labelless edge is deliberately silent (camera cuts)"* |
| `door` | 6 | yes |
| `passage` | 2 | yes |
| `portal` | 1 | yes |

And in `quay-west` specifically, from `dellhollow.routes.json` — the shot the agent could not
leave — there are **six exits, five of them silent seams**, and *the only labelled thing in
the frame is the door into the Cookhouse*, which has nobody in it. Open
`frames/step-045.jpg`: six red triangles, none carrying a word, four of them clustered
against a bare cliff, under a banner that reads *"Down to the lock apron"*.

This is round 5's carried design call — *whether a shot-exit should look like a town exit* —
now measured on three instruments and priced at 34 steps. **It is not filed as a bug because
the remedy is a look decision, and this lane does not make those.**

#### Gates

`percept_test` **PASS 342/342** · `story_test` **1104 / 0** (baseline) · `dialogue_test`
**1493 / 2** (the two known `del.gullgirl` clearances) · `save_probe --from ch2.jam`
**15 / 0** · **`playthrough_test` 86 passed / 0 failed, exactly baseline** — including its own
cold-reload-from-`at` assertion, which is the one this round's fix could have broken and did not.

### Open going into round 9

  * **THE ACCOUNT IS OUT OF GEMINI CREDIT.** `llm_playtester` cannot run at all until it is
    topped up. Every no-model instrument in `tools/playtest/` still works, and round 8 was
    finished on them, but the loop itself is stopped.
  * **`ch2.maren` and everything after it have still never been played.** The cheapest next
    run is `--from=ch2.maren` or `--from=ch2.supper`; the arrival band costs 30+ steps and
    the deck costs 34 more, and neither is where the untested content is.
  * **Three Dellhollow interiors have nobody in them** (`del-inn-int`, `del-cookhouse-int`,
    `del-boatyard`). Two have now been visited by a playtest and both cost it steps.
  * **A shop has never been entered by a playtest.** With the pause menu now legible to the
    percept, buying something is finally testable — and so is equipping it.
  * **Dellhollow's 40 silent cuts.** Measured above. A design call for the user.
  * Carried, unchanged: the gorge water brighter than the sky at one arc of yaw; the camera
    boom inside the overworld grass; PT-013/014's 64×36 thumbnail; `play3d` has no `resize`
    handler.

---

## Round 9 — 2026-08-04 06:30

Credit was restored overnight and the loop ran again. This round's entry is mostly a
**retraction**, which is why it is written up at the same length as a fix.

### PT-20260803-005 / -006 "screen black after leaving Emberbrook" — NOT REPRODUCED

Filed `blocker/P1` + `confusion/P0` by `run-20260803-113942`, which gave up at step 6.
Three instruments were pointed at it and **none of them found a defect.** The chain:

  1. **The first probe called `emb-cine` BLACK AT BOOT** — `meanL 0`, `nonblackPct 0`, on a
     scene that visibly renders. A bare `gl.readPixels` on this page always reads zero: the
     context is `preserveDrawingBuffer:false`, so outside a rAF callback the back buffer is
     undefined. `SIM.px()` is the shipped probe and it calls `renderFrame()` immediately
     before reading — that call is the entire difference. The probe now **self-tests on a
     scene known to render and exits 2 rather than report**, because the first version of it
     spent a round proving a black screen that was its own.
     With the fix: **`meanL 29.5`, 82.5 % non-black, steady across 20 s. Never black.**
  2. **Both exits from Emberbrook are shut ON PURPOSE, and the scenegraph says so.**
     `emb-cine>ow-valley@emberbrook-gate` carries `deny.when.notFlag story.ch1.done` and
     plays `emb.southroad.turnback`; `@old-gate` carries `when.flag story.ch1.gate-open`.
     The playtester tried to leave at **step 2**, before doing any of Chapter One. **A
     refusal is correct behaviour**, and "I could not leave Emberbrook" is not a bug.
  3. **The refusal draws, and it draws the right line.** `scratchpad/denyprobe2.mjs` at HEAD:
     `denied:true, live:false` before the flag → `SIM.go` returns
     `{denied:true, dialogue:"emb.southroad.turnback"}` → setting `story.ch1.done` gives
     `denied:false, live:true` → the Lake branch speaks *"(Nothing down there but the
     Whisperwood. My lamps are the other way.)"* → **console clean, 0 errors, 0 exceptions.**

**Why it was filed at all:** the run is timestamped **11:39** on 2026-08-03 and the turnback
node's own doc-string cites **PT-20260803-002/-008** — the fix for this exact complaint landed
around 15:00 that day. *The report predates its own fix.* The lesson is not about the
transition; it is that **an aging report in a queue is evidence about a commit, not about the
game**, and re-running it costs less than reading it.

And the soft-lock this would have become if the flags were orphaned did not exist:
`story_test` **1104 / 0**, both exit flags written (`story.ch1.gate-open` at story.json:661,
`story.ch1.done` by beat `ch1.done` at :730).

### What the loop actually showed

`run-20260804-013303` — **48 steps, Chapter One played end to end into Dellhollow**
(`del-cine`, `quay-west`, beats `ch1.open → ch1.waystone → ch1.reveal → …`), **zero reports
filed.** That run is the round's real result: the spine holds under a model that is only
allowed one screen and one keyboard.

### A SECOND HARNESS BUG, and it explains four rounds of the log

Round 9's `--from=ch2.maren` run ended at **step 1 with zero model calls**:
`== FINISH LINE: ch1.sendoff fired at step 1`. **`--from` builds state by firing every beat up
to the checkpoint**, so the stop beat was already in the ledger before the player moved, and
`episode.mjs` read the setup's own work as the player reaching the end.

Beats are `once:true`, so a pre-set stop beat can never honestly fire again. The guard now banks
the checkpoint's beats on the first observed frame and **disables** a finish line found inside
them, so the run plays its steps out instead. Verified: the same command now prints
*"finish line 'ch1.sendoff' was already set by the checkpoint — DISABLED"* and proceeds.

**This is why this log has carried "`ch2.maren` and everything after it have still never been
played" for four consecutive rounds.** Not because nobody tried — because **every `--from` past
`ch1.sendoff` ended instantly and reported success.** A stop condition that a setup step can
satisfy does not measure the game, and it fails in the one direction nobody audits: it looks
like a pass.

### 🚨 BLOCKER, carried into round 10 — THE GEMINI CREDITS ARE DEPLETED AGAIN

The fixed run got exactly one step further and then:
`HTTP 429 … "Your prepayment credits are depleted"`. `llm_playtester`, `nav_eval` and
`scene_redteam` are all down again. **The playtest loop cannot run at all until the account is
topped up at https://ai.studio/projects.** Every no-model instrument still works, and the two
harness fixes above were made and verified on them — but the loop itself is stopped, and this is
the second time in one night.

### Carried into round 10

`ch2.maren` onward **still never played** — the harness bug that prevented it is fixed, so the
single cheapest thing to do the moment credit returns is re-run `--from=ch2.maren`. Three
Dellhollow interiors still empty; a shop still never entered; Dellhollow's 40 silent cuts still
a design call for the user; `play3d` still has no `resize` handler.

### Round 10 — 2026-08-04 · the arrow floats two metres over its door, and the harness walked at what was behind it

`run-20260804-101155` is the first run that ever got past `ch2.maren` (round 9's finish-line
guard did that). It played 140 steps of Chapter Two and filed two P1s, both of the shape
*"I am stuck, I cannot reach the markers"*, both from the Lock Five objective. Triage's
`reach_probe` **verified** PT-20260804-004: the target `[60.47, 16.58, −3.53]` is not standable
and the nearest ground the player can reach is 6.0 m away.

That verification is correct and the ticket is still wrong, because **the target was never a
place the agent meant to go.**

#### What the probe named

`_court_probe`'s method, pointed at a WALKLOCK town — `del-cine` must fill on `walkGround`, not
on `SIM.ground`, which is the one change `_court_probe` needs to be re-aimed at a town. Every
number below is the engine's own, read in the running page. Three measurements, in order:

1. **The body was not stuck.** From the exact filing position `[56.47, 17.4, −7.84]`, a
   WALKLOCK component fill reaches **1357 cells**, including the quay deck 4 m below; and
   `SIM.move()` drives to the two seams offered in that shot and **arrives** — `d 0.95 m` in 46
   ticks, `d 0.97 m` in 128 ticks, the second one firing the cut into `quay-west`. The agent's
   own log agrees: **step 125 has it at `[43.48, 14.07, −18.03]`**, one step after it said it
   could not move.
2. **Every failed leg aimed at the same cliff.** `legs.json`, steps 110–124: **8 legs failed,
   all with `onNetwork:false` and a target at `z ≈ −3.5, y ≈ 16.5`. 7 legs arrived, all with
   `onNetwork:true`.** One field, 15 for 15.
3. **Why the aim was wrong.** `markersTick` projects `e.at[1] + 2.1`, then lifts the arrow 30
   px and bobs it — an FF7 arrow floats over its door and points *down* at it. Measured live in
   `del-cine` from `loop-stairs`: the three markers draw at ny **.159 / .435 / .428** while
   their own edges project at **.382 / .657 / .616** through `SIM.cam()` — a constant **0.22 of
   frame height**. `__pt.hit` at each arrow's own centre returned `[48.87, 21.88, −12.91]`,
   `[56.33, 16.83, −3.27]`, `[60.37, 16.76, −3.38]`: **the cliff behind the arrows.** The agent
   clicked the red triangles it was told to head for, the ray sailed over the deck, and the
   body pushed at a cliff for 16 bursts.

The 2.1 m lift is deliberate and reads correctly to a human. **Nothing in the game was
changed** — `play3d.html` is coordinator-owned, and the world here is not the defect.

#### The fix (`tools/playtest/adapter_emberbrook.mjs`, `INSTALL_MOTOR`)

* **A pixel on an exit arrow resolves to that edge's own `at`.** `markersTick` already stamps
  `dataset.edge` on every marker for `trigger_probe`, so the motor reads the game's own handle
  and can never name a seam the game is not drawing.
* **In a walk-network scene, a ray that never crosses the network is refused.** `march(true)`
  scans the *whole* ray, so a roof or a tree in front of a reachable plaza is transparent to it;
  a ray that still finds nothing has named scenery. The executor gets
  `ok:false` and the agent gets the sentence it already understands —
  *"[x,y] is not ground you can walk to"* — instead of sixteen bursts and a false P1.
  The switch is **the scene's own answer under the player's feet**, with `walkGround`'s four
  0.18 m plank-crack retries, not a scene-name regex: measured at the very spot this bug was
  filed from, a bare `walkFloors(56.47, −7.84)` is **empty** and `z−0.18` returns **17.4**. A
  one-sample test would have read "this scene has no walk network" while the body stood on it.
  `ow-valley` is untouched by construction (no `walk_` meshes → the old fallback stands, and it
  was re-measured: three off-network overworld pixels still resolve exactly as before).

#### Receipts

| what | before | after |
|---|---|---|
| the 8 failing pixels of steps 110–124 | 8/8 aimed at the cliff, `ok:true` | **3 resolve to the seam the arrow names, 5 refused with a reason** — 0 still aim at the cliff |
| the 7 arriving pixels of the same steps | 7/7 `onNetwork:true` | **unchanged** (one now goes to the seam itself, which is where it was heading) |
| `percept_test` | — | **PASS 434/434, 1.3 s** |
| `ow-valley` off-network aim | `ok:true` | **`ok:true`, identical targets** |
| `story_test` | — | **1104 / 0** |

#### A LEAD, NOT A VERDICT: `playthrough_test` came back 54/16, and it is not this lane

`node tools/playthrough_test.mjs --port=3000` on `23336cb`+ returned **54 passed, 16 failed**
against the 81/0 the Old Gate fix left. The 16 are ONE cascade:
`beat ch1.pact fired (shot square)` fails → `ch1.sigils` is never driven →
`story.ch1.gate-open` is never set → the Old Gate edge stays sealed → the run never leaves
`emb-cine`, so §W's only red (`ch1.done -> ch2.road`) is an anchor pair measured from
Emberbrook and means nothing, and every Chapter Two assertion falls over behind it.

**Not this change**, by construction: `playthrough_test` imports `reach_probe` and `cdp` and
`grep -c adapter_emberbrook` is **0** in all three, and this lane touched only that adapter
and this log. `story_test` is **1104/0**, so the story DATA is intact.

**And not yet established as a game defect either.** The same run's final flag dump has
`story.ch1.pact: true` and lists `ch1.pact` among its 16 completed beats — **the beat DID
fire, just not inside the assert's 75-tick window.** The machine was at 66 MB free and
3.4 GB of swap while this ran, and a slow page missing a fixed tick budget looks exactly like
this. So: **re-run it on a quiet machine before anybody builds against it.** Recorded here
because the next reader will otherwise inherit a red gate with no note beside it — not
because we know what it is.

The consequence for this round is only that `playthrough_test` could not serve as the
receipt: the run never entered `del-cine`, so §W never walked the Chapter Two anchors. The
receipt is the engine's own answers above plus the playtester re-run below.

#### The circuit closed: `--from=ch2.dock --steps=60`, `run-20260804-112506`

The same command the bug came from, on the same checkpoint, same models:

| | run-20260804-101155 (before) | run-20260804-112506 (after) |
|---|---|---|
| walk legs | 133 | 54 |
| **aimed off the walk network** | **14** | **0** |
| un-projectable (the new refusal) | 0 | **3** |
| arrived | 35 (26%) | 30 (**56%**) |
| **median fraction of the leg closed** | **0.11** | **0.63** |
| verified navigation blockers | **PT-20260804-004, P1** | **none** |

**Zero legs aimed off the walk network**, and the median leg now closes 63% of its distance
instead of 11%. The agent got far enough to hold two full conversations (Watchman Pell,
Sorrel) that the previous run never reached.

It filed four new reports and `playtest_triage` **REFUTED three of them**
(PT-20260804-006/-007/-008) on `reach_probe` in the running page; the fourth
(PT-20260804-005) is UNVERIFIED — *the probe itself* died with "Execution context was
destroyed", which is a triage failure, not a finding.

The refutations are the interesting part, because **the complaint has changed shape.** Round
10's targets were `[60.47, 16.58, −3.53]` — a cliff, 6.0 m from any reachable ground. The new
ones are `[54.02, 15.96, −11.57]` (**1.6 m**, 15 cells) and `[53.44, 18.75, −9.7]` (**3.1 m**,
86 cells, via 1 in-scene edge): real, connected, walkable ground a step or two away. The aim
is now ON the world, so what is left is the honest residue — a stride or body-box question for
`walk_bodygate`, and Dellhollow's 3.9 m level changes that only a cut band crosses. **That is
a smaller and truer bug than the one we started with, and it is carried, not fixed.**

#### One thing this fix deliberately does NOT hide

A refusal is now the answer whenever visible ground has no walk network under it — which is
also the signature of the real defect `walk_engine_gate` exists for (209.6 m² of Emberbrook
non-collidable for weeks). The refusal therefore *names the surface it found*
(`"the ray lands on scenery at [58.03, 16.55, −3.55]"`) and `legs.unprojectable` is already
counted in every run summary. A run whose unprojectable count jumps is a lead, not noise.

#### And a legibility note for the coordinator, not fixed here

From a steep down-looking shot the 2.1 m lift puts the arrow visually **on the cliff face 7 m
behind** the seam it names. A human reads the arrow's *direction*; nobody has measured whether
a human reads its *place*. Same family as round 8's "40 silent cuts in `del-cine`". Owned by
whoever owns `play3d.html`.

**Coordinator addendum, 2026-08-04 13:20 — the 54/16 flag above is RESOLVED: contention, not
regression.** `playthrough_test` re-run on a quiet machine (zero Blender, zero other gates, zero
tool Chrome): **86/0**. Independently, the foliage lane's own gate run on a tree containing the
same commits was also 86/0. The 54/16 was recorded at 66 MB free with a second instance of the
same suite running against the same server — the exact signature the lane refused to build
against, correctly. `ch1.pact`'s 75-tick window stands unchanged.

Also carried out of this lane, for the coordinator (play3d.html is coordinator-owned): from a
steep down-looking shot, the exit arrow's 2.1 m + 30 px lift can place it visually ON the cliff
behind the seam it names. The harness now aims at the edge's own `at` and is immune; whether a
HUMAN reads the arrow's place (not just its direction) from those shots has never been measured.
Queued as a legibility item, not acted on.

And one instrument lesson worth the ink: the lane's own wait-loops (`until ! pgrep -f
llm_playtester`) never fired because **pgrep matched its own shell's command line** — a watcher
whose existence satisfies its stop condition is measuring itself. Same family as "an instrument
that finds nothing must prove it could have found something."

## Receipt run 2026-08-04 21:00 — the inn fix holds; the winch approach graduates to a wayfinding defect

`run-20260804-194447`, `--from=ch2.supper`, 100 steps, **one report** (was four).
**The Boatmen's Rest fix is receipted**: the run passed through the same inn that cost two
reports and 12 burned turns this afternoon, and filed nothing — the innkeeper, bargeman and
lodger (`dfa47db`) answered where silence had been.

**PT-20260804-013 is the THIRD independent run to fail at the head-gate winch approach**
(after PT-004, refuted + harness marker-aim fixed; PT-011/012, refuted). Every filing is
reach-REFUTED — the path is walkable in the engine. One refuted report is bad steering;
three different players failing at one walkable spot is a **legibility defect**: the way up
exists and cannot be FOUND. This is the arrow-lift question queued this morning, now with
player-side evidence x3. Next lane's brief is wayfinding, not walk network: how the route up
reads on screen (marker place vs the seam it names, the ramp's visual affordance, possibly a
route_overlay hint). Repeated refutation at one location is itself an instrument reading —
the one findability_test cannot take, because it teleports.

## Round 11 — 2026-08-04 · the town had forty-two ways out and not one of them said which

Three independent runs failed at the head-gate winches (PT-004 → harness marker-aim, fixed;
PT-011/012 and PT-013, all reach-REFUTED). The walk network is proven clean twice over, so
round 11's brief was WAYFINDING: how the way up reads on screen. The answer turned out to
have nothing to do with the ramp and everything to do with the arrows above it.

### The instrument — `tools/playtest/wayfind_probe.mjs`

`marker_probe` answers "is the way onward marked, from here?" for the OVERWORLD and cannot
be pointed at a pre-rendered town: there the camera is CINECAM's fixed shot, `del-cine`
carries FIFTEEN of them, and the edges joining them are anonymous `cut` bands. So this is
that probe re-aimed. At each of the three failing filings' OWN positions and shots (their
`truth` blocks in `queue.json`), with their own flags AND their own beat ledger seeded — the
ledger matters, `once` is gated on `GS.state.beats` and a run with an empty one is waiting on
a different beat — it reads `#exit-markers`' own DOM, asks **`SIM.pick` at each marker's
drawn pixel** what a player aiming there would actually hit, projects each edge's own `at`
through the shot camera, and BFS's the shipped scenegraph for the true next hop.

Two probe bugs paid for on the way, both worth the ink: `window.cam` and `window.SG` are
**undefined** — play3d is a classic script, so its top-level `let`s live in the global
LEXICAL scope and must be read bare and guarded (the first run reported "the edge has no
position" for every edge in the town). And a backtick inside a comment **inside a template
literal** ends the literal, which CLAUDE.md already warned about twice and which this lane
paid for a third time.

### What it measured (7 stations, `docs/qa/playtest/wayfind/`)

| station (shot) | markers drawn | the ONE toward Lock Five | hops |
|---|---|---|---|
| cottage door (`cottage`) | 4 (3 red cuts + a door) | `cottage>cottage-steps` | 2 |
| lockhead | 2, both red cuts | `lockhead>quay-west` | 3 |
| quay deck (`quay-west`) | **6** (5 red cuts + a door) | `quay-west>weave` | 2 |
| loop-stairs (PT-013's spot) | 3, all red cuts | `loop-stairs>quay-west` | 3 |
| valley gate (PT-011/012's spot) | 3 | the gate stair | 6 |
| weave | 3, all red cuts | `weave>lockfive` | 1 |

**Every triangle is identical and none of them is named.** At the quay deck the right one
draws at x 97 and a WRONG one (back to `lockhead`, away from the objective) at x 106 —
**9 px apart**. The objective banner names a place; nothing on screen said which of six
ways went there. That is the defect, and it is why three different players failed at one
walkable spot.

**And the arrows do not stand on their seams.** markersTick projects `at[1] + 2.1` and then
lifts 30 px: measured here at **86–164 px, 0.12 to 0.23 of frame height, in EVERY shot** —
not only the steep ones, which is a correction to this morning's note. `SIM.pick` at the
marker's own drawn centre lands on **scenery for 12 of the 24 shown markers**:
`cliff_town_back`, `shelf_home_a_5`, `ls_treads`, a station awning, `cx_rail`,
`gate_barrier001`, `gate_arch001_1`, `lf_joists`, a cookhouse wall. The lift is deliberate
FF7 grammar and reads correctly to a human as *pointing down at* the thing; it is left
alone and recorded, because what was actually missing was a NAME.

### The fix — `public/js/story_runtime.js`, not the marker layer

The objective banner says WHERE. Nothing said WHICH WAY, and the banner is this module's,
so the direction is this module's. It finds the beat the chapter is waiting on (eligible on
its CONDITIONS, not on its place — that is the whole question), BFS's the shipped
scenegraph from the shot you are standing in to the shot that beat names, and labels the
ONE marker that starts that route.

Three rules it keeps:

1. **It decorates, it never draws.** The label is appended INSIDE markersTick's own marker
   div, found by `data-edge` — the handle that layer already carries for `trigger_probe`. So
   it inherits every gate that layer applies (sealed, denied, `camFrom`, frustum, UILOCK) and
   is structurally incapable of naming a way the game is not offering. **No `play3d.html`
   edit**, which is also why it landed in a module lane and not in the coordinator's queue.
2. **It names the DESTINATION, not the hop.** At the quay deck the next hop is `weave`; the
   label still reads "Lock Five", because that is what the banner says and making the two
   match is the entire point. The string is the shot's own `name` out of the bundle's
   `cine.json`, or the scene node's label — never invented here.
3. **One marker, ever.** "A town of named doorways is noise" (markersTick's own ruling,
   kept). Every other triangle stays bare, which is what makes this one mean something.

Nodes in the BFS are `(scene, shot)` pairs, so ONE search answers both "which triangle in
this town" and "which door out of it" — the corridor between the towns is the same graph.
Conditional edges are evaluated with the game's own condition language, so a sealed gate is
never routed through. `?nohint=1` disables it; `Story.wayhint()` is the instrument, and it
distinguishes "no beat", "no route", and "route exists but its marker is not on screen from
here" instead of collapsing all three into a null.

### AND THE FIRST CUT SHIPPED IT AT 11 px, WHICH IS THE ROUND'S REAL LESSON

The label was built at 11 px — the portal label's size, matched on purpose. Every gate was
green: **7/7 probe stations, hint agreeing with the probe's own independent BFS, `shown` and
`labelled` at all seven.** Then the receipt run (`run-20260804-204212`) walked straight past
it. Step 2: the label is on screen, bottom-left, correct, naming Lock Five under the one
arrow that leads there — and the agent's own stated goal is *"climb the stairs UP to the
head-gate winches"*. It spent five legs stuck on the platform above and filed
**PT-20260804-014, a fourth report at the same place.**

**A GATE THAT PROVES THE LABEL IS PRESENT CANNOT PROVE THE LABEL IS READ.** Same family as
Poppy behind her own canopy and as `walk_engine_gate`: `shown:true` and `labelled:true` were
measurements of the DOM, and the question was about a picture. The frame was there to be
looked at the whole time.

So the label now wears the objective banner's own pill — same `#000c` fill, same `#3a2c20`
border, same amber diamond, 13 px 700 — and the hinted arrow is scaled 1.3x. This game is
played on a TV (memory: controller-agnostic, everything renders on the TV), where 11 px is
not a label, it is a texture.

### Gates

`playthrough_test --port=3000` **86 / 0** (quiet machine, §W 21 pairs, 0 unreachable) ·
`story_test` **1104 / 0** · `cine_test` **689 / 0** · `findability_test` **69 / 0** ·
`percept_test` not run and not needed — the adapter was not touched, which is the point:
the agent sees this the way a player does, in the screenshot.

### The receipt — `--from=ch2.dock --steps=60`, `run-20260804-204657`

**The label is read, and the agent steers by it.** The discriminator is the agent's OWN
words in `observations.jsonl`, not a DOM assertion:

| run | what the agent calls the markers |
|---|---|
| 185107 (before) | "a red marker", "red markers indicating objective locations" |
| 194447 (before) | "red markers above indicating winches", "under a yellow marker" |
| **204657 (after)** | **"the Lock Five marker", "the objective marker for Lock Five", "walk left along the wooden walkway towards Lock Five"** |

| | 194447 (before) | **204657 (after)** |
|---|---|---|
| reports filed | 1 (PT-013, the third refuted winch filing) | **0** |
| legs aimed off the walk network | 0 | 0 |
| how far the run got | circled the quay deck for 90 steps, never left `quay-west`/`loop-stairs` | **reached `weave` — ONE hop from Lock Five** |

**`ch2.winches` did not fire, and this is an honest partial.** The run spent steps 2–6
climbing the wrong way (it opened on the objective's own words — "*navigate up the ramp
towards the head-gate*" — before it had read anything), then followed the hint down and
across the town to `weave`, and spent its last thirteen steps stuck at
`[61.77, 11.6, −17.6…−19.5]` on the pilot-cluster platform: the executor's own verdict,
thirteen times, is *"the body moved every round and never got closer — the ground is
walkable and the approach is not."* That is the stride/body-box residue round 10 already
carried for `walk_bodygate`, one hop short of the beat. **Wayfinding got the player to the
last seam; something else is holding the last seam shut.** Probed there: the hint is
correct and drawn (`weave>lockfive`, 1 hop, shown, labelled).

### AND THE QUEUED LIFT CLAMP IS REFUTED — MEASURE BEFORE YOU BUILD

This morning's coordinator note proposed clamping the arrow's lift on steep shots.
`wayfind_probe --liftcap 46` measures that change WITHOUT making it (it reports where each
arrow would draw under the cap and what `SIM.pick` returns there):

| | today | under a 46 px cap |
|---|---|---|
| clicks landing on scenery | **11 / 24** | **12 / 24** |
| top hits changed by the cap | — | 17 / 24 |

**It does not help, and it moves seventeen markers to do it.** The reason is this repo's
oldest lesson wearing a new hat: the occluder is BETWEEN THE CAMERA AND THE SEAM (a rail, a
pile brace, a hut), so no screen-space lift can uncover it — the cap just swaps one piece of
scenery for another. "In frame ≠ visible ≠ unobstructed ray."

And the finding matters less than it looks: **this game is not click-to-move.** A pixel
under an arrow is a HARNESS concern (the adapter already resolves a pixel on a marker to
that edge's own `at`, round 10), not a player one — a player pushes a stick toward the
arrow. Recorded so the next reader does not re-open it as a player defect.

### Carried

* **The last hop into Lock Five.** `weave` → `lockfive` at `[75.0, 6.3, −25.2]`: thirteen
  no-gain legs from the pilot-cluster platform, ground walkable by the executor's own
  reading. `walk_bodygate` on that stretch, then a `--from=ch2.dock` re-run, is the next
  cheapest thing — and it is now the ONLY thing between this checkpoint and the beat.
* **The lift stays as shipped** (see above). If it is ever revisited, revisit the OCCLUDERS,
  not the pixels.
* **PT-20260804-014** was filed against the 11 px cut and is superseded by the pill; re-test
  it, do not triage it as a world defect. Its predecessors at that platform were already
  reach-REFUTED.

## Round 12 — 2026-08-05 · "the ground around Maren has a bunch of holes" — it was a staircase

**USER REPORT, verbatim:** *"it's literally hard for me to reach Maren because the ground
around her still has a bunch of holes"* (Dellhollow, `del-cine`, the lock apron).

There were no holes. There was **one wall, and the wall was a staircase**, and it stood
between the entire western waterfront and the woman Chapter Two sends you to.

### What it was

`town_blockout.stairs_leg` puts a 2.0 x 2.0 x 0.16 landing at every intermediate `stairs`
waypoint with its **top at the waypoint's own height**. `weave-huts__moorage` carried a
last waypoint at **1.70** over a moorage deck measured at **1.02–1.05**
(`walk_e_moorage__lock-five_l0` — the lane Maren stands on) and **1.25** (`walk_lm_moorage`).

| | |
|---|---|
| step up onto the stair's foot | **0.65 m** |
| `play3d.html:1918` `STEP_UP` | **0.63 m** |
| headroom under that same slab | **0.49 m** (`BODY_H` is 1.30) |

**Refused by 20 mm, and un-duckable by 0.81 m.** So the stair neither joined the deck it is
named for nor let anyone pass beneath it, and `walk_e_moorage__tenant-shack` →
`walk_e_moorage__lock-five` — the waterline's only west–east route — was severed at the join.

### The instruments, in the order they were asked

| instrument | what it said |
|---|---|
| `walk_engine_gate --scene del-cine` | **GREEN, 0 lost cells.** Not a collision-BVH defect — file and engine agreed about a world that was already wrong |
| `_court_probe --way` (SIM.move) | stalled at **x 77.53** driving west; driving *down* the flight it put the body on the **overhead leg at y 4.52** |
| `_court_probe --at` | `SIM.blocked` **named it**: `walk_e_weave-huts__moorage_l3_t00`, `_landing002` |
| `reach_probe --pairs` | fishdock arrival → maren: **no-path**, gap `dy 2.18 m` over `0.4 m` in plan |

**The map's own note predicted the second row and nobody heard it:** *"tight hairpins let
walkers mount the overhead leg."* It was written about the flight's legs clearing **each
other**. Nothing had ever asked whether they cleared **the deck below**.

**And a flood fill could not have found this.** `reach_probe` reported `ok=true` from the
lockhead — its 0.4 m lattice, its four 0.18 m plank-crack retries and its settle-from-the-
neighbour's-height bridge what a 0.075 m stride and a 0.30 m body cannot. Its own header
says so ("a TOPOLOGY screen, not a drive"). **The drive is what found the wall.**

### The fix — one number of map

`public/townmap/dellhollow.map.json`, that waypoint's height **1.70 → 1.25**
(`walk_lm_moorage`'s own top). The landing now merges with the pad instead of hovering over
it, and its underside drops to 1.09 — below the body's blocking window from the lane.

Carried in by `walk_rederive --edge weave-huts__moorage` (the blockout stays the only
generator), then **`locksfoot_build deck`** — `lf_stair_treads` is *built from* those walk
records, and leaving the art behind would have made the wall invisible rather than absent —
then `cine_solve`, the derives, and four plates.

### Receipt

| | before | after |
|---|---|---|
| `lockfive` spawn → Maren (`SIM.move`) | walled | **2/2 legs, both ways** |
| down the flight → Maren | 2/8, on the overhead leg | **8/8 legs** |
| §W `ch2.jam → ch2.maren` | — | **reachable, 11.6 m, 3 in-scene edges** |
| `playthrough_test` | 86/0 | **86/0** |
| `cine_test` | 687/1 | **688/0** |
| `walk_engine_gate` del-cine | GREEN | **GREEN**, 3985 cells / 807.0 m², BVH FAIL 0 |
| `findability_test` | 69/0 | **69/0**, Maren in neither warning |

**This closes round 11's carried item** — *"the last hop into Lock Five… thirteen no-gain
legs from the pilot-cluster platform, ground walkable by the executor's own reading."* Same
stair. The LLM playtester and the human hit the same 20 mm.

### Carried, measured, not fixed

* **The flight still crosses `walk_e_moorage__tenant-shack` with 1.05 m of headroom**
  (was 0.88 — the steeper flight improved it, and 1.30 is what a body needs). The
  tenant-shack/fish-dock deck therefore still does not join the moorage *under* the stair;
  it joins over it. Fixing it needs deck the moorage footprint does not have, and every rect
  there must be measured-landed, so it is a build, not a waypoint.
* **`walk_rederive --report` shows 44 records across 9 OTHER edges stale against the map**
  (`inn__item-shop`, `quay-deck__cookhouse`, `deep-stairs-head__…`, two `walk_pad_`s…).
  Only `weave-huts__moorage` was re-derived. **Each of those is a place the master and the
  map disagree, which is exactly the shape of the defect above.**

### Two lessons worth the ink

1. **`cine_solve` runs BEFORE the bake.** The solver frames a shot off the walk network in
   its own band, so moving a stair moved `lockfive` 0.30 m and made its just-finished plate
   stale against the solve. `lockfive` was baked twice to learn it. The chain is
   `map → walk_rederive → district build → cine_solve → derives → bake`.
2. **A GATE THAT MEASURES THE FILE CANNOT SEE A STEP THE BODY WON'T TAKE.** `walk_engine_gate`
   answers "does the engine find the floor the file has" and was green through all of this,
   *correctly* — both sides had the floor. The missing question was whether a **body** gets
   from one floor to the next, and only `SIM.move` asks it. Same family as `_court_probe`'s
   founding lesson: a fill tells you where the world is shut, never what shuts it.

## Winches first-fire attempt, 2026-08-05 01:00 — closer than ever, not yet

`run-20260804-234816` (--from=ch2.dock, 60 steps): the Maren stair fix OPENED the winch
approach — legs now arrive throughout the area that was 13 no-gain legs yesterday — but
`ch2.winches` still did not fire. The pattern in the last 20 steps: nearby legs arrive,
the final ~3-4 m to the winch target repeatedly closes partial distance (0.94/4.02,
1.49/3.64). One report filed, a typo (PT-20260804-015, duplicate "the" in the cook's
prompt — interiors lane's, trivial).

NEXT SESSION'S FIRST LANE, precisely scoped: `_court_probe --at` at the stalling legs'
own coordinates — `SIM.blocked` names the mesh. Prime suspect is the carried fish-dock
item (the flight crosses walk_e_moorage__tenant-shack with 1.05 m headroom, under
BODY_H 1.30). Also carried: PT-015 typo; the 44 stale walk records across 9 edges from
the Maren lane's --report.

## Round 13 — 2026-08-05 · the hint counted hops, and hops are not metres

**`ch2.winches` still has not fired.** Three `--from=ch2.dock` runs tonight
(`run-20260805-003146` 40 steps, `run-20260805-005322` 30 steps, plus the carried
`run-20260804-234816`). What DID come out of them is the reason the last four attempts
failed, and it was never where the previous rounds were looking.

### THE HINT SENT THE PLAYER 45.9 m THE WRONG WAY

The prime suspect carried into this session was the fish-dock headroom. It is not the
cause. `_court_probe --at` at the stalling legs' own coordinates found the ground clear;
the drive from the lower waterfront to the Lock Five seam is **4/4 legs both ways**. The
world on that route was fine. **What was broken was the arrow.**

`story_runtime.routeTo()` — round 11's wayfinder, the thing that puts the ONE label on
the ONE marker — was a hop-count BFS. Standing on the Lockhead, *directly above Lock
Five*, there are two routes and they are both exactly three hops:

| route | hops | **metres** |
|---|---|---|
| `lockhead > cottage > cottage-steps > lockfive` | 3 | **21.9** |
| `lockhead > quay-west > weave > lockfive` | 3 | **45.9** |

BFS returned whichever it dequeued first. It dequeued the second. So the labelled arrow —
the one thing in the town that says which way — pointed the player down the entire length
of Dellhollow, into the quay deck and the pilot-cluster stairs, and **the agent walked it,
in `run-20260804-234816` and again in `run-20260805-003146` (step 3, lockhead, 21 m west in
one leg).** Every previous round's "the agent gets lost at the winch approach" was this.

**A TIE IN HOPS IS NOT A TIE ON THE GROUND.** `routeTo` is now a Dijkstra over the seams'
own positions: from where the player IS to the first seam, then seam to seam, using each
edge's `spawn` where it has one. A hop into ANOTHER scene has no comparable coordinates,
so it pays a flat nominal cost and the walk restarts from that edge's spawn — an honest
"a scene away", never a number pretending to be measured. 42 edges at 6 Hz is free.

### AND THE PROBE THAT WAS SUPPOSED TO AUDIT IT RANKED BY HOPS TOO

`wayfind_probe`'s "TRUE NEXT HOP" was its own independent BFS — *and therefore could not
see the defect it was pointed at.* It called a route twice the length correct, at the
exact station where the shipped hint was wrong, and printed them as agreeing. It now
enumerates every simple path, ranks by metres, prints the runners-up, and flags a
shipped-hint disagreement. The enumeration is deliberately a DIFFERENT algorithm from the
Dijkstra: two implementations agreeing on the number is the cross-check.

    station        SHIPPED HINT (after)              metre-shortest        runner-up
    dock-spawn     cottage>cottage-steps             2 hops /  9.7 m       3 / 17.2 m
    lockhead       lockhead>cottage                  3 hops / 17.9 m       3 / 41.5 m
    deck-mid       lockhead>quay-west                3 hops / 24.1 m       3 / 35.2 m
    pilot-plat     weave>lockfive                    1 hop  / 16.8 m       4 / 26.7 m
    quay-end       quay-west>weave                   2 hops / 23.4 m       5 / 33.8 m

Five stations, no disagreement. Before the fix, `lockhead` took the 41.5 m route.

### A LABEL HALF OFF THE FRAME IS NOT A LABEL

Round 11 grew the pill from 11 px to 13 px because a label that is present is not a label
that is read. Same lesson, one turn further: in `run-20260805-003146` step 3 the pill drew
at **x 38 px of 1400**, its amber diamond and its left half outside the picture, and the
agent took the bare triangle on the other side of the frame. **I looked at the frame** —
`frames/step-003.jpg` — which is the only reason this was found; every DOM assertion said
`shown:true labelled:true`. The caption is now clamped into the viewport. Only the
caption slides: the arrow still points at the seam, because the arrow is the claim.

### PT-20260805-004 — VERIFIED, AND IT IS A ONE-WAY SOFT-LOCK

`run-20260805-005322` spent **eighteen consecutive steps** at `[57.74, 15.30, −11.24]`
moving 0.02 m in six. That is not "the agent is lost". The drive says so:

| `_court_probe --way` | result |
|---|---|
| market deck → the trap (4 legs) | **4/4, arrives** |
| the trap → the landing 1.32 m away | **0 legs, 0 m** |
| the trap → the deck below | 1 tread, then nothing |

The body settles on the **west lip of `walk_e_shelf-homes__market-stalls_landing001`**
(the slab is x 57.90..59.90, top 15.30 — it is standing 0.16 m off the edge of it). West
of it `ls_rail` at x 57.5; below it the deck at 14.24, a **1.06 m** drop against
`STEP_DN 0.8`; above it the flight's own treads. **You can walk in and you cannot walk
out.** `SIM.move` cannot even reach the cell — the agent got there on real keys, which is
the whole argument for this instrument.

**IT PREDATES TONIGHT — measured, not assumed.** The pre-re-derive `scene.glb`
(`d63fd12`) was checked out under the same probe: floors, blockers and both drives came
back **identical**.

**AND THE MESH IS NAMED.** `--mesh` (through the `SIM.pad` fix below) gives the two
records' own boxes, and `--at` says what they do to a body:

| record | box |
|---|---|
| `walk_e_shelf-homes__market-stalls_landing001` | x 57.90..59.90, **top 15.30**, z −11.60..−9.60 |
| `walk_e_shelf-homes__market-stalls_l1_t04` | x 57.57..58.73, **underside 15.93**, z −10.95..−9.45 |

**The last tread ROOFS the landing it arrives at**, over the strip where they overlap in
plan, with **0.63 m** of headroom against `BODY_H 1.30`. `--at` confirms it in one line:
at `[58.3, −10.3]` a body at 15.30 is blocked *by `l1_t04`*; two-thirds of a metre south,
at `[58.3, −11.3]`, the same height is **clear**. So the landing's west end is a separate
room, reachable only by coming down the flight past the tread, and unleavable: east is
0.63 m of headroom, west is `ls_rail`, below is a 1.06 m drop against `STEP_DN 0.8`. The
drive is unambiguous — `[59.4,15.3,−10.3] → west` walks 2/2 legs by CLIMBING the flight
instead of passing under it, and `[58.19,15.3,−11.3] → east` closes **0 m of 1.0 m**.

The fix is one map line in round 12's own shape — move the l1 landing out from under the
flight, or drop a tread — and it owes `walk_rederive` + the district build + `cine_solve`
+ the plates that see it. A build lane, not a patch at 06:00.

### THE STALE WALK RECORDS — four of the nine were free, five are a build lane

`walk_rederive --report`: 36 records across 9 jobs stale against the map (the carried
figure of 44 included `weave-huts__moorage`, already re-derived in round 12). **Four jobs
are `bar_` ONLY** — `deep-stairs-head__deep-stairs-foot`, `quay-deck__pilot-cluster`,
`shelf-homes__market-stalls`, `keepers-cottage__lock-five` — and a `bar_` is
render-hidden, so those move COLLISION and no picture: `cine_bake --glb` alone, **5.4 s,
no plate re-bake**. Done, and measured on both sides because the tool's own sweep warned
of 27 possible crossings and a rebuilt rail is an invisible wall if it lands wrong:

| | before | after |
|---|---|---|
| `--comp` (52..82, −32..−12), 3 seeds | 638 cells, 1 component | **639, 1** |
| `walk_engine_gate del-cine` | 3985 cells / 807.0 m² | **3985 / 807.0, LOST 0, BVH FAIL 0** |
| `--way` waterfront → lockfive seam | 4/4 both ways | **4/4 both ways** |
| `cine_test` | 687/1 (scenegraph stale) | **688/0** |

The tool GUARDED `bar_e_shelf-homes__market-stalls_l0_railB` by itself (ls_reorigin cut a
gap there over the loop-stairs fork) and held it back — the guard earns its keep.

**The other five are NOT a chore, they are a build lane**, and the reason is worth the
ink: `qm_build.py` builds the cookhouse *from* `walk_e_quay-deck__cookhouse_l1` and
`walk_pad_cookhouse`, `shelf_build.py` from `walk_pad_inn` — so re-deriving them moves art
and owes `cine_solve` + plate bakes. And the one record reported **MISSING** from the
master, `walk_pad_loop-landing`, is `ls_reorigin.py`'s own deliberate replacement, not a
defect: **"stale against the map" is not the same as "wrong".**

### PT-20260804-015 — fixed, with the gate that should have caught it

`promptLabel` is a template and `name` is a string, and the two are only ever seen
joined — on the banner, in the player's face. `del.cook` carried `"Talk to the {name}"`
over the name `"the cook"` and shipped **"Talk to the the cook?"** with every gate green,
because no gate had ever EXPANDED the template. `dialogue_test` §1b now expands every one
and reads the result: doubled article, doubled space, unfilled slot. **1712/0.**

### Two instruments were lying, and both are fixed

* **`_court_probe` waited only for `SIM.pos()` to be finite**, which is true long before
  the bundle's GLB is in `allMeshes`. A `--who` run on that race printed **2009 cells of
  `<no floor>`** for a region that has floors — twice, silently, and the same command
  worked the third time. It now waits for a non-zero, settled mesh census and REFUSES to
  report rather than report an empty world.
* **`--mesh` traversed `window.THREE_SCENE || window.scene`**, and play3d has neither (its
  scene is a module-scope `let`), so it returned `[]` for names the bundle certainly
  carries. Now it asks `SIM.pad`, and says MISSING when a name really is absent. Its
  output is what let the Keepers' Steps be driven tread-by-tread instead of through a
  straight line that leaves the stair on tread two.

### Gates

`playthrough_test --port=3000` **86/0** (§W 21 pairs, 0 unreachable) · `story_test`
**1112/0** · `dialogue_test` **1712/0** · `cine_test` **688/0** · `seam_test` **294/0** ·
`walk_engine_gate del-cine` **GREEN** · `routes_derive --check` clean.

### Carried, in the order they should be picked up

1. **PT-20260805-004**, the one-way lip at `[57.74, 15.30, −11.24]` — verified above,
   pre-existing, and a soft-lock is worse than a missing beat.
2. **The five walk_-moving stale jobs** — a build lane with a bake, see above.
3. **`ch2.winches`.** The route the hint names is now the short one and it drives; what
   is left to prove is whether the agent takes it. That wants a run, not a fix.
4. The fish-dock headroom (1.05 m against `BODY_H` 1.30) is still carried and is still
   NOT what was stopping the winches.

### AND THE TRIAGE INSTRUMENT WAS AUTO-REFUTING BODY TRAPS

`playtest_triage` classified all three of tonight's blocker filings as `reach`, ran
`reach_probe`'s fill, got `ok=true`, and stamped **REFUTED** on every one. In this log's
own rules REFUTED means *do not build against it* — so the screen that cannot see a body
trap was closing body traps. It is round 12's lesson wearing the triage tool's clothes:
**reach_probe's own header calls itself a topology screen, not a drive.**

`triageReach` now runs `SIM.move` over the SAME pair whenever the fill says connected. A
pair that fills and will not drive is VERIFIED, with the stall position; a pair that fills
AND drives is still REFUTED, and now says so with the drive's own numbers. Re-run:

| | fill | drive | before | after |
|---|---|---|---|---|
| PT-20260805-001 | reachable, 1565 cells | stalled 22.96 m short, 41 dead ticks | REFUTED | **VERIFIED** |
| PT-20260805-004 | reachable, 627 cells | stalled 8.52 m short, 41 dead ticks | REFUTED | **VERIFIED** |
| PT-20260805-005 | reachable, 40 cells | stalled 1.39 m short, 41 dead ticks | REFUTED | **VERIFIED** |

Queue 18 verified / 23 refuted → **21 verified / 20 refuted**. Three real traps had been
argued away by a lattice.

## Round 14 — 2026-08-05 · the arrow was right and the sentence was wrong

### PT-20260805-006 — THE OBJECTIVE NAMED THE WINCHES AT THE OTHER END OF THE TOWN

Five rounds have now ended with "`ch2.winches` has not fired". Round 11 grew the
wayfinding pill, round 13 made it route by metres and clamped the caption into frame.
Nobody had read the **sentence the pill is pointing away from**.

    "Midnight, at Lock Five — the head-gate winches"

Dellhollow has a head gate. It is the **valley gate at the dam** — landmarks
`winch-head` and `winch-foot`, camera `gate` "The Valley Gate", visible winches, at
`x ≈ 20, y ≈ 24`. **Lock Five is `x ≈ 87, y ≈ 0`**, the far low end of the same town.
The objective names a real place in the wrong direction, and the run is unambiguous
(`run-20260805-013331`, `--from=ch2.dock`, 60 steps):

| step | where the body was | |
|---|---|---|
| 1 | `[90.2, 9.3, −20.4]` | the cottage door — **2 hops / 7.2 m from Lock Five** |
| 7 | `[80.9, 14.0, −16.1]` | the Lockhead, walking WEST |
| 13 | `[32.5, 19.1, −8.2]` | past the Weave, still west |
| 15–60 | `[20.5, 24.1, −6.5]` | **the Valley Gate.** 45 of 60 steps, ping-ponging |

and it filed **"Cannot walk to the head-gate winches at Lock Five"** from a position
70 m from Lock Five. It was not lost. It had arrived, at the wrong head gate.

**THE ARROW WAS RIGHT THE WHOLE TIME AND IT DID NOT MATTER.** `wayfind_probe` at that
exact station: `SHIPPED HINT: Lock Five via gate-stair-head>gate-stair-foot hops=6
shown=true labelled=true` — and `frames/step-042.jpg`, **which I opened**, has the amber
`◆ Lock Five` caption drawn on the correct triangle in the middle of the picture, over a
prompt reading `Down to the Shelf street? [E]`. The agent took the stair down and came
straight back up, three times, because the banner told it the winches were here.

Fixed in one line — the decoy noun out, a bearing in, aimed at the landmark the
metre-shortest route's own first hop goes to (`cottage > cottage-steps > lockfive`):

    "Midnight at Lock Five — down past the Keepers' Cottage"

`story_test` **1112/0**.

**AND THE SAME 60-STEP RECEIPT, RE-RUN AGAINST THE NEW SENTENCE** (`run-20260805-014451`,
identical checkpoint, identical model, one word of content changed):

| step | | before |
|---|---|---|
| 2 | *"Walk down towards Lock Five as indicated by the objective"* — reached | walked west |
| 5 | **`[beat] ch2.winches`** | never, in five rounds |
| 8 | *"Advance past the full-screen chapter card"* → **`[beat] ch2.landing`** | never |

**A WAYFINDER CANNOT OUT-ARGUE AN OBJECTIVE.** Every instrument this repo built for
round 11 and round 13 measures the MARKER; not one of them reads the objective string
against the town's own landmark names. That gap is what cost five rounds, and the fix
was one sentence.

### PT-20260805-004 — THE ONE MAP LINE DOES NOT EXIST, AND HERE IS THE PROOF

Round 13 named the mesh correctly: `walk_e_shelf-homes__market-stalls_l1_t04`, the
second-to-last tread of the flight, roofs `landing001` where the two overlap in plan.
Its prescription was "one map line in round 12's own shape — raise the tread's waypoint
or lower the landing's". **That prescription is arithmetically impossible**, and the
census says the defect is not this edge's.

**A new instrument, because `--mesh` gives a box and `--at` gives one column and
neither answers what a landing actually poses.** `_court_probe --stand <name>` walks a
named slab's own top face on a lattice and asks the engine twice per cell: is this slab
still the top floor here (`SIM.floors`), and does a body standing on it fit
(`SIM.blocked`, which NAMES the roof). Every stairs landing in `del-cine`, 400 cells each:

| landing | standable | roofed by |
|---|---|---|
| `quay-deck__pilot-cluster_landing` | **100%** | — |
| `shelf-homes__market-stalls_landing` | 70% | its own `l0_t03` |
| `weave-huts__moorage_landing001` | 68% | its own `l1_t04` |
| `valley-gate__inn_landing` | 67% | its own `l0_t03` |
| … eleven more between 54% and 63% … | | |
| `shelf-homes__market-stalls_landing001` | 57% | its own `l1_t04` / `l1_t03` |
| `keepers-cottage__lock-five_landing` | **48%** | its own `l0_t04` / `l0_t05` |

**Sixteen of seventeen landings in Dellhollow are roofed by their own flight, 30–52% of
each.** The single clean one is the tell: `quay-deck__pilot-cluster_landing`'s incoming
leg has **zero rise** — one tread, top 0.07 above the landing — so there is nothing over
it. The rule is geometric, not a mistake in one edge.

The arithmetic, so nobody re-derives it. `blocked()` reads the band
`[fy+STEP_UP+.02, fy+BODY_H]` = `[fy+0.65, fy+1.30]`. `town_blockout.stairs_leg` lays
tread `t` with its top at `min(p0,p1).z + step + 0.07`, so the tread two steps above a
landing tops out at `L + 2·step + 0.07`, and the 2×2 landing reaches **1.35 m** back
along a flight at 28°, which is further than that tread's near edge for any run under
1.35 m. Clearing the band needs `2·step + 0.07 ≤ 0.65`, i.e. **`step ≤ 0.29`** — and
`step = rise / ceil(rise/0.4)` is only ever that small for a leg descending **under
0.87 m**. Splitting 2.1 m of descent into legs that shallow needs five landings 0.68 m
apart on a 3.4 m run. **No waypoint anywhere in the map can do it.**

So the trap at `[57.74, 15.30, −11.24]` is one instance of a town-wide derivation
property, and it is a trap only because the clear remainder there is a 0.65 m strip with
`ls_rail` on one side and a 1.06 m drop on the other. Re-measured tonight on the shipped
bundle, and the margins are small enough to be worth writing down:

* `t04` top **16.07** vs the body band's floor **15.97** — **0.10 m** of intersection;
* the body box's south face at z −10.94 vs `t04`'s south edge −10.951 — **0.01 m**;
* drive east from `[58.19, 15.3, −11.3]`: **2/2 legs**. Drive east from
  `[57.74, 15.3, −11.24]`, five centimetres north: **0.00 m closed of 1.00 m**.

**THE FIX IS A BUILD LANE AND IT IS NOT A MAP EDIT.** The honest one is the tread
convention — lay a tread's top at its leg's own lower end rather than a step above it,
which turns every `L + 2·step + 0.07` roof into `L + step + 0.07` and clears the band at
every landing in the town. It moves every tread in six stairs edges by one step, and
`ls_build.py` builds the visible loop stairs **from those ribbons**, so it owes
`walk_rederive` ×6 + `ls_build` + `cine_solve` + the plates that see them. That is not a
patch to make at 03:00 in front of a three-hour receipt run, and it is filed as the
build lane it is rather than attempted and half-landed.

### AND THE KEEPERS' STEPS DO NOT DRIVE END TO END

Found while checking whether round 13's metre-hint had started routing players down a
stair. `_court_probe --way` from the cottage to Lock Five, **tread by tread** off
`--mesh`'s own centres, 22 legs:

    downhill  stalls at [94.04, 6.77, -23.72]   (l0_t03's top, 0.76 m short of l0_t06)
    uphill    stalls at [91.18, 2.55, -25.85]   (l2_t02's top, 1.02 m short of landing001)

Every tread top the drive stopped at reads `clear` under `--at`, so this is not the
landing roof. **It does not block the spine**: `cottage > cottage-steps > lockfive` is
served by two `cut` seams (`at [94.44, 5.27, −24.42]` and `at [89.85, 1.69, −26.15]`),
so the player is carried past the stair rather than walking it. Filed as a lead, not a
ticket — it wants its own `--who` pass over the flight, and `--stand` already says
`keepers-cottage__lock-five_landing` is the worst landing in the town at **48%**.

### The cross-check has a blind spot of its own

`wayfind_probe`'s metre-shortest enumerator returned **NO PATH** from `gate` to
`lockfive` while the shipped Dijkstra returned a live 6-hop route that the frame shows
drawn and labelled. Round 13 built the second implementation precisely so the two could
disagree out loud; at six hops it stops enumerating and says nothing rather than saying
"deeper than I look". **An instrument that reports NO PATH where a path exists is the
`--mesh` bug wearing different clothes**, and it is logged here so the next reader does
not trust that line at long range.

## Round 15 — 2026-08-05 · the wayfinder is SILENT for the whole of "See to them", by construction

**A FINDING, NOT A FIX.** Traced from the code and the run logs, no browser. Recorded
rather than shipped, for the reason at the bottom.

Round 14 fixed the *sentence* the Chapter One objective shows. This is about the *arrow*,
and it is a gap in round 13's own subsystem.

All four `ch1.see.*` beats carry **`cam: null`**:

    ch1.see.poppy   scene=emb-cine  cam=None  at=[51.4,  1.5, -43.0]  r=3.2
    ch1.see.mara    scene=emb-cine  cam=None  at=[62.13, 1.5, -44.5]  r=3.2
    ch1.see.finn    scene=emb-cine  cam=None  at=[86.0,  1.0, -48.0]  r=3.4
    ch1.see.mochi   scene=emb-cine  cam=None  at=[56.6, -0.21, 12.2]  r=3.4

Follow `hintTick` through with one of them. It calls `routeTo(b.scene, b.cam || null)` =
`routeTo('emb-cine', null)`. Inside, `goal` is
`s === destScene && (!destCam || …)` — and with `destCam` null the second clause is
vacuously true, so **`goal` collapses to "are we in emb-cine"**. The player IS:

    if (goal(here, shot())) return { hops: 0, edge: null };

`edge` is null, so `want` is null, so `hintTick` calls `clearHint()` and returns. **No
label is drawn at any point during the whole objective.** Not a wrong arrow — no arrow.

And the four are **40–90 m apart across four different camera bands of one scene**:
poppy/mara in `square`, mochi at `waystone`, finn at `[86, 1, −48]` in `pondlane`. So the
sequence that most needs a way-label is precisely the one the wayfinder is structurally
incapable of labelling, because the beat names the scene you are already standing in.

The cost, from the runs' own beat timings:

| run | `see.mara` | `see.mochi` | `see.finn` | `see.poppy` |
|---|---|---|---|---|
| `run-20260805-013253` (200 steps) | step 49 | step 85 | **step 150** | **never** |
| `run-20260805-015721` (in flight) | step 73 | — | — | — |

Both NEW GAME runs died in this objective. It is now the only thing between this build and
a continuous playthrough — Chapter Two runs its whole remaining spine in six steps.

**The shape of the fix** (unbuilt): when a pending beat has no `cam` but has an `at`,
route to the shot whose BAND OWNS that `at`. The bands are already in `scenegraph.json`,
which `routeTo` already reads, and `findability_test.ownerShot()` is the same lookup
written out. It must fail closed exactly as today — no owning band, no hint.

**Why it is not in this commit.** It is a behaviour change to the module that started
firing `ch2.winches` four hours ago, `wayfind_probe` is the only instrument that can
prove it, and that instrument needs a Chrome the machine cannot spare while a 200-step
NEW GAME run is at step 99. **Shipping an unverified change to the one thing that just
began working is how a good night becomes a bad morning.** Build it against
`wayfind_probe` on a quiet machine, with `emb-cine` `square` → `pondlane` as the case.

### Round 15, second half — and the SENTENCE, which is what shipped

The section above is the arrow. This is the line, measured on the same two runs, and
between them they are the whole of "why does a NEW GAME run die inside Chapter One".

**WHAT THE PLAYER WAS READING**, in the order the game said it:

    "See to them — all of them (0/4)"
    "See to them — all of them (Mara and Pip ✓)"
    "See to them — all of them (the cat is fine ✓)"

**Every success replaces the count with the name of somebody already finished.** The
line never names a person who is LEFT, never names a place, and after the first tick it
cannot even be counted. With no arrow drawn (above) it was the only wayfinding in the
scene, and it carried none. `run-20260805-013253` spent **steps 91–192 — a hundred of
its two hundred — oscillating between z +20 and z −24**, the road *north* of the
village, with Poppy at z −43, Mara at z −44.5 and Finn at z −48. It had gone to see the
cat at `[56.6, −0.21, 12.2]`, correctly, and nothing on screen told it to come back.

Not a world defect and not a hidden NPC: `walk legs 169 (126 arrived, **0 aimed off the
walk network**), median closed 0.87 m`, **0 reports filed**, `findability_test` **69/0**.

Fixed the way `ch1.reveal` already does it three beats earlier — *"Emberwake — greet the
villagers (Poppy at her bread stall, Mara by the Heartlight)"*, 81 characters, shipped,
and the one hunt in the chapter that has never stalled. Every string now carries the
roster that is LEFT, each with a place. **`run-20260805-015721`, same seed conditions,
same model:**

| | before (`013253`) | after (`015721`) |
|---|---|---|
| `ch1.hush` | step 45 | step 48 |
| `ch1.see.mara` | 48 | 72 |
| **`ch1.see.poppy`** | **never, in 200 steps** | **step 91** |
| `ch1.see.mochi` | 84 | 109 |

and the agent's own words at step 90 were *"Head over to Poppy at her stall on the right
side"* — **it quoted the banner back.**

### AND THEN IT WALKED TO POPPY AGAIN, BECAUSE THE ROSTER COULD NOT TICK

A beat fires once and cannot know what the other three have done since, so the static
roster kept naming people already seen: `015721` spends **steps 136–167 walking at
villagers it had finished at 72 and 91**. Half the win handed back.

So the objective layer gets ONE primitive and no more:

    {!flag: text}      emit `text` only while `flag` is falsy

The RAW string is stored and every render re-reads the flags, which is what lets one
roster serve all five beats and tick itself off. `hintTick` re-renders at 6 Hz but ONLY
when the expansion CHANGED — `innerHTML` on a timer is a repaint per tick. It expands
BEFORE the `<>` strip and its own syntax carries no `<>`, so an author cannot smuggle
markup through it; a malformed template, absent flags or absent `GS` DROP the segment
rather than print it raw. Proven on the three states that matter:

    none   See to them, all four — Poppy at her stall, Mara at the Heartlight,
           Finn at the pond, the cat back up the north road
    2/4    See to them (Poppy ✓) — Finn at the pond, the cat back up the north road
    4/4    See to them (Poppy ✓)

`story_test` **1112/0**, `node --check` clean, and the 122-character worst case measured
by eye against `#story-obj`'s `white-space:nowrap` at 1280 px in
`run-20260805-015721/frames/step-050.jpg`: one line, no ellipsis.

**THE STEP BUDGET, STATED RATHER THAN RAISED.** Chapter One from NEW GAME costs ~48
steps to `ch1.hush` in both runs, and Chapter Two's whole remaining spine cost **8 steps**
in `run-20260805-014451` (`ch2.dock` → winches at 5 → the chapter card at 8). What has
been eating the budget is this one objective, twice. 200 steps is the right order of
magnitude for the receipt; it is not obviously enough while a four-anchor hunt with no
arrow sits in the middle of it, and `llm_playtester`'s own header budgets **300–500** for
a full playthrough. The number to raise is not `--steps`.

### PT-20260805-009 — TWO [E] PROMPTS, ONE PIXEL, AND THE DOOR LOSES

Filed by the agent in its own words: *"The 'Leave Item Shop? [E]' prompt is overlapping
with the 'Talk to the shopkeeper? [E]' prompt. Because they both use the same key,
pressing E just makes me talk to the shopkeeper again instead of leaving."* It is
correct on both counts and it is not a one-off.

There are **two independent banner elements drawn at the same coordinate**. play3d's
`sgPrompt` builds `#sgp` at `position:absolute; left:50%; bottom:8%`; `ui_kit.prompt`
builds `.ebui-banner` and its own comment says so — *"sgPrompt's recipe VERBATIM — same
host element (#s), same position … A counter prompt must be indistinguishable from a
door prompt."* Indistinguishable was the goal; **co-located was not noticed.** Neither
channel knows the other exists, so `banners[id]` — "one banner per owner id" — stacks
them.

`npc.js` already carries the fix's shape for a case it DID hit: standing next to a
shopkeeper it calls `E.prompt('shop', null)`, with the comment *"One prompt, one
person."* Nothing does that across the `#sgp` / `ebui-banner` boundary.

Measured cost in `run-20260805-015721`, twice in the last twenty steps:

| steps | where | prompts live | outcome |
|---|---|---|---|
| 181–190 | `emb-item-int` `[4.5, 0, −5.6]` | `Leave Item Shop? [E]` + `Talk to the shopkeeper? [E]` | ten steps; E kept talking. It escaped by **walking away**, not by pressing the door |
| 192–199 | `emb-cine` `[52.8, 1.6, −44.1]` | `Enter Poppy's bakery? [E]` + `Talk to Poppy? [E]` | eight steps on the doorstep |

**Eighteen steps of a two-hundred-step budget, in one run, to a collision between two
banners that were built to look identical.** Not a soft-lock — moving clears it — but a
player who does not think to walk away first is stuck in a shop.

NOT BUILT TONIGHT, deliberately: the arbitration that decides which one E fires lives in
`play3d.html`, which is coordinator-owned, and a second lane was live in the same
subsystem this hour. The measurement is the deliverable.

### THE RECEIPT — three NEW GAME runs, 200 steps each, one variable at a time

| beat | `013253` no fix | `015721` sentence | `022035` sentence + `{!flag:}` |
|---|---|---|---|
| `ch1.hush` | 45 | 48 | 46 |
| `ch1.see.mara` | 48 | 72 | **55** |
| `ch1.see.poppy` | **never** | 91 | **57** |
| `ch1.see.mochi` | 84 | 109 | **71** |
| `ch1.see.finn` | 149 | never | **106** |
| **`ch1.pact`** | **never** | **never** | **step 130** |
| beats fired | 14 | 14 | **16** |
| walk legs off-network | 0 | 0 | 0 |

**The hunt closed for the first time.** All four anchors, then `ch1.pact` — the beat that
gates the rest of Chapter One — at step 130 of 200. `ch1.see.poppy` went from *never in
200 steps* to *step 57*, and at step 58 the agent's own goal line was *"Head north
towards the north exit road to find the cat"*: it was reading the roster as the roster
ticked. Verified by eye in `run-20260805-022035/frames/step-060.jpg` — by then BOTH ticks
have landed and the banner reads `◆ See to them (Poppy ✓) — Finn at the pond, the cat
back up the north road`, naming exactly the two anchors still outstanding.

### AND THE BOTTLENECK MOVED AGAIN — PT-20260805-010, THE OLD GATE

Steps 131–200, the whole remaining budget, in one loop: `square` (z −42) → `therise`
(z −28) → back to `square`, six times. The agent filed *"Crossing the northern exit zone
at The Old Gate repeatedly transitions back to the Village Square, creating an infinite
scene loop."* `ch1.sigils` never fired.

The objective is **"North, out of the village — the Old Gate"**. `therise` is the road
the player walked IN on at `ch1.open` under the line *"Follow the road north"* — so the
chapter has now used "north" for both directions of the same road. The Old Gate is the
other way: `gatefield` sits at z −107, past `northlane`, and `wayfind_probe`'s
metre-shortest from the square is `square>northlane`, 3 hops / 60.5 m, while the agent
took `square>therise`.

**NOT DIAGNOSED — and the instrument says why it cannot be, yet.** `wayfind_probe` boots
a fresh page with no story flags, so `pendingBeat()` resolves to a CHAPTER TWO beat and
the station prints `objective: "Midnight, at Lock Five…"` with `shown=false`. It is
measuring a different game than the run was. Reproducing an in-run hint needs the run's
own flag state loaded first — the repro save is already on the report. Third round
running that the words and the arrow are the suspects and the world is not: **0 walk legs
aimed off the network in all three runs.**
