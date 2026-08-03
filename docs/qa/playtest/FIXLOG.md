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
out (`+17.0`, `+8.4`, `+7.9`, `+7.2` u).

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

