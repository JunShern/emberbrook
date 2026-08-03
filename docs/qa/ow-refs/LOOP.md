# The overworld gauntlet loop — protocol and round log

**Ten rounds minimum, then keep going while it is still paying.** User ruling 2026-08-04.
(An earlier version of this line said five; superseded — see rule 6.)

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
3. **THE CRITIC MAY LIST; THE COORDINATOR TRIAGES.** User correction 2026-08-04: *"even if it
   gives you a list of criticisms, you are the coordinator and so you can try to dish out
   multiple improvements to the subagents in a single turn if you like. No need to make this
   such a rigid structure, you have judgment."*
   I had written "one deficit per round" as a rule ON THE CRITIC. Wrong place. The real risk is
   **one BUILDER given six things and doing none of them well** — which is fixed by what each
   lane is handed, not by starving the critique. A list is naturally divisible when the lanes
   own different surfaces: pipeline items to one, content items to the other. Rank by what would
   most change the picture, hand each lane a small coherent set, drop anything that is really a
   design or asset call and surface it to the user instead.
4. **JUDGE THE PICTURE, NOT THE SUBJECT.** User's framing, verbatim into the critic brief:
   *"different game, different scene, don't judge content, just judge which has better art
   quality"* — otherwise it keeps reporting that the reference has a castle in it.
5. **THE REASON IS THE WORK ITEM**, routed verbatim to whichever lane owns that surface.
6. **TEN ROUNDS MINIMUM, THEN KEEP GOING WHILE IT IS STILL PAYING.** User ruling
   2026-08-04 (superseding the earlier five): *"you need to run at least 10 rounds, but if you
   have more time and you have not exhausted the options, then you should run this many more
   rounds. Just keep running it until you find that the quality has actually plateaued or you're
   not able to add any more meaningful improvements."*

## What counts as a plateau — and what does NOT

I first wrote that the loop stops when the critic's remaining asks are "needs new assets" or
"needs a different camera." **The user rejected both, and was right; I had also contradicted
myself, having said two paragraphs earlier that asset work was fair game.**

  * **NEW ASSETS ARE NOT A CEILING.** We have the character factory, Tripo, and the procedural
    Blender pipeline that built two towns. If the critic keeps naming foliage that terminates in
    flat facets, the answer is better foliage — generate it, mat it, ship it. Cost, not wall.
  * **THE CAMERA RULING IS "DO NOT MOVE THE CAMERA", NOT "DO NOT SOLVE THE PROBLEM THE CAMERA
    CREATES."** The deficit is real — no horizon means no aerial perspective, no layered ridges,
    no sky as a value anchor. Attack the CUE: distant silhouettes placed where the CURRENT pitch
    can see them, depth carried radially across the ground plane, a far band that is genuinely
    far rather than warm cliff at 60 m. Filing this under "blocked by user ruling" is laziness.

**THE ONLY PLATEAU IS: WE TRIED THINGS AND THE PICTURE DID NOT MOVE.** Not "the critic named
something expensive."

Every round therefore records which of three outcomes each deficit reached, and **only the middle
one is evidence of a ceiling**:

  * **TRIED — MOVED IT.**
  * **TRIED — DID NOT MOVE THE PICTURE.** ← the only real ceiling evidence
  * **NOT TRIED — RAN OUT OF NIGHT.** ← says nothing about the ceiling, only about the clock

## Standing decisions for the overnight run

  * **HOLD THE STYLISED LINE.** If the critic pushes toward photoreal and away from the
    FFIX-ish stylisation, do not follow it — log the disagreement instead. "Looks more like a
    modern AAA render" is not "looks more like the game we are making." Coordinator's call,
    flagged to the user, not yet contradicted.
  * **REDEPLOY PERIODICALLY** so the live site tracks the work. It is ~50 s now.

## The seam between builders

Drawn 2026-08-04 after I dispatched two lanes concurrently without one, and they overlapped.

  * **PIPELINE lane** — everything after the scene renders: AO, bloom, grading LUT, depth-based
    fog, anti-aliasing. All scene families.
  * **CONTENT lane** — geometry and materials: grass density and height, path-edge irregularity,
    foliage clustering, vertex colours. Overworld only.

Findings route **through the coordinator**, never lane to lane.

## Constraints the builders work under

  * **THE CAMERA: DISTANCE IS FIXED, PITCH IS OPEN.** Refined by the user 2026-08-04, and this
    is NARROWER than the earlier "camera is fixed" — read it carefully before assuming.
    **FIXED:** how far back the camera sits. Their reason is a design one, not an aesthetic one:
    *"I want the player to have a sense of where they are going and have a wide enough field of
    view to appreciate the surroundings… where the landscape is leading them."* **Do not zoom in.**
    **OPEN:** *"In terms of camera angles, how high we are, and whether we should include more of
    the horizon line in the shot, I'm actually very open to changes at that level… so long as the
    user continues to have a wide field of view of the space around them."*
    **THIS REOPENS THE CRITIC'S ITEM 8**, which I had dropped as settled. It called lowering the
    pitch the one structural change that buys aerial perspective, sky as a value anchor, and
    layered depth "for free" — and independently reached the same conclusion I had.
    **THE WARNING THAT COMES WITH IT, from the critic:** a lower pitch *"will also expose whatever
    the near-top-down framing is currently hiding — far LODs, terrain edges, skybox quality — so
    budget for that, not just the camera move."* We already know the sky dome, ridge rings and
    horizon fog built 2026-08-02 are INVISIBLE in play at the current pitch. They are about to
    become load-bearing, and nobody has ever looked at them in a shipped frame.
  * **Treatment first, assets second — but assets ARE on the table** once treatment stops moving
    the picture. The last pass moved a lot with zero new art, which is why treatment leads; it is
    a sequencing preference, NOT a ban. See "What counts as a plateau".
  * Ground detail must not become collision (`veg_*`; verify in the ENGINE, not the file).

## Rounds

| # | frames judged | verdict | deficits | routed to | outcome (moved / did-not-move / not-tried) |
|---|---|---|---|---|---|
| — | *(round 1 begins when a builder returns frames)* | — | — | — | — |
