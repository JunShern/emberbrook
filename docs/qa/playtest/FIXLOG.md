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

