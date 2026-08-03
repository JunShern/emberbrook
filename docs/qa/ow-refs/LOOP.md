# The overworld gauntlet loop — protocol and round log

**Five rounds, then we assess whether it is going anywhere.** User ruling 2026-08-04.

The experiment: can a blind LLM critic, comparing our overworld against real FFIX-reimagined
overworld screenshots, produce direction good enough to drive real art improvement? Separate
from the playtester, which tests gameplay. This tests **art quality**.

## The references

`public/assets/refs/reimagine_ff9_overworld_1.jpg`, `_2.jpg`, `_3.jpg` — third-person overworld
gameplay screenshots from the FF9 reimagining. **Same shot type as ours**: a character walking
between towns, party HP down the left, quest banner top right.

**These are the correct refs and were not used until 2026-08-04.** The previous landscape pass
was given `docs/qa/ow-land/plates/REF1–3.jpg`, which are re-encodes of `reimagine_ff9_2.jpg`,
`reimagine_ff9_3.jpg` and — verified by hash — **`reimagine_ff9_dagger.jpg`, a CHARACTER
PORTRAIT**, used as a bar for landscape art. Its measurements stand; its framing was drawn from
town-tier art and several conclusions built on it (including my "we would be judging real-time
against pre-rendered" argument) were wrong.

## The rules

1. **THE BAR IS ARTISTRY, NOT NUMERIC SIMILARITY.** User ruling, and it corrects my instinct:
   *"the goal here is not to meet the reference numerically, but just to reach the art style or
   the level of artistry that we have in the reference. That is very different from what we can
   measure numerically."* Matching the reference's chroma would be numerically closer and could
   easily look worse. **Do not convert the critic's reason into a metric.**
   THE BOUNDARY THAT STILL HOLDS: a claim about the WORLD ("there is a pink plank in the
   corner") is checkable and gets checked — that rule exists because a judge once hallucinated
   exactly that. A judgment of QUALITY is the deliverable, not a hypothesis. I collapsed the two
   once; they are different.
2. **THE CRITIC IS BLIND AND FRESH.** A new Opus 5 agent per round. No history, no knowledge of
   which image is ours, randomised order. This is the leg the Gauntlet Loop calls essential and
   the one we did not have: **never let the builder grade itself.**
3. **ONE DEFICIT PER ROUND, NOT A LIST.** Six weaknesses give a builder no priority and produce
   scattered half-work.
4. **JUDGE THE PICTURE, NOT THE SUBJECT.** User's framing, verbatim into the critic brief:
   *"different game, different scene, don't judge content, just judge which has better art
   quality"* — otherwise it keeps reporting that the reference has a castle in it.
5. **THE REASON IS THE WORK ITEM**, routed verbatim to whichever lane owns that surface.
6. **FIVE ROUNDS, THEN ASSESS.** No plateau detection, no waiting on the user.

## The seam between builders

Drawn 2026-08-04 after I dispatched two lanes concurrently without one, and they overlapped.

  * **PIPELINE lane** — everything after the scene renders: AO, bloom, grading LUT, depth-based
    fog, anti-aliasing. All scene families.
  * **CONTENT lane** — geometry and materials: grass density and height, path-edge irregularity,
    foliage clustering, vertex colours. Overworld only.

Findings route **through the coordinator**, never lane to lane.

## Constraints the builders work under

  * **THE CAMERA IS FIXED.** User ruling: *"the camera now is set up as intended for the scale of
    the world we want to explore."* Consequence: all four `ow-*` cameras contain **ZERO sky
    pixels**, so the references' depth cue — cool haze on distant cliffs against sky — has
    nothing to act on. Depth must come radially across the GROUND PLANE, or from detail falloff.
    The upside: our high camera makes near-field ground most of the frame, which is exactly where
    the references have their best material. **We can show off more of it than they can.**
  * No new assets until treatment is exhausted. The last pass moved a lot with zero new art.
  * Ground detail must not become collision (`veg_*`; verify in the ENGINE, not the file).

## Rounds

| # | frames judged | verdict | the one deficit | routed to | outcome |
|---|---|---|---|---|---|
| — | *(round 1 begins when a builder returns frames)* | — | — | — | — |
