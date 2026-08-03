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
| — | — | — | *(round 1 in progress — first entries land when it reports)* | — | — | — |

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
