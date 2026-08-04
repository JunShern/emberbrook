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

| # | frames judged | verdict | headline | outcome |
|---|---|---|---|---|
| 1 | `base-meadow` vs 2 refs | 3rd of 3, very high conf | **1.30:1 lit-to-shadow, saturation flat across the terminator** — "not a sun, an ambient multiplier with a slight gradient" | shadows/key/tonal → pipeline; dressing/blades → content |
| 2 | `r4-meadow`, `r4-gorge` vs 2 refs | 3rd and 4th of 4 | **"Light is a GLOBAL TINT rather than a DIRECTION: every surface got warmer, but nothing got occluded, so nothing has form."** Top four fixes all TREATMENT | 3 lanes killed by a session limit before routing |
| 3 | not judged — BUILT against 1 and 2 | plates `r5-*` | **the sun gets a direction: 1.58–2.40:1 → 3.29–4.33:1 on four viewpoints, and the terminator carries a HUE** | TRIED — MOVED IT |
| 4 | `r5-*` judged blind | **`r5-meadow` LAST of four**, below the r4 frame it replaced | **"This is a global tint, not a light. Nothing in the frame has a lit side and a shaded side that agree with anything else."** — the ratio said 3.29:1 | the metric moved and the picture did not |
| 5 | not judged — BUILT against 4 | plates `r6-*`, `docs/qa/ow-refs/r6.html` | **the grade is applied to what the light touches, not to the frame**; the blade carpet stops rendering half of itself black; the Heartlight gets a core and a falloff. Ratio kept and up, 4.96 / 3.38 / 3.87 / 4.19 | TRIED — MOVED IT |
| 8 | not judged — MEASURED against 4's "no directional light" | plates `r8-*` | **the meadow has the same sun as the gorge, and it is not a lighting defect at all** — a 2.6 m cottage under a 34° sun throws a 3.9 m shadow from a 2.9 m footprint, straight away from the lens | routed to CONTENT; both sun moves REJECTED by eye |

### Round 4–5: A NUMBER THAT IMPROVES WHILE THE PICTURE WORSENS IS THE WRONG NUMBER

This is the loop's most important round so far and it is the one that vindicates rule 1.

R5 was **good work that shipped a regression**. `__envTune` really was lying, the fog really was
aimed at the wrong band, the Heartlight really had no point light — all kept. But the lane took
`lit:shadow` as its target, hit it, and the frame got worse: everything inside one amber band,
plane separation gone, the near field a carpet of black scribble. A blind critic that had never
seen the numbers ranked it BELOW the frame it replaced. **The user confirmed it by eye.**

Two things the round establishes, both cheap to state and expensive to relearn:

  * **THE RATIO WAS NEVER WRONG — IT WAS INCOMPLETE.** A directional KEY and a global GRADE
    produce a high lit:shadow ratio and a flat picture at the same time, because the grade repaints
    the shadow the key just carved. R6's fix is one line: the warm half of the depth grade is
    weighted by the pixel's own luminance, so it lands on lit surfaces and not in shadows. The
    cool far half stays unweighted — haze is atmospheric and does land on everything.
  * **THE R5 LANE MEASURED BOTH FAULTS AND SHIPPED THEM AS "UNTOUCHED"** (near-band saturation
    0.70–0.79 against the references' 0.48–0.49; "the blade carpet also reads oversized"). A
    measurement filed under known costs is still a defect in the frame. If a lane can name the
    fault, the fault is in scope.

**And the near field was not the grade's fault the way everyone assumed.** With the carpet off
(`?owdetail=0`) the near-band saturation barely moves (0.795 → 0.773) — yet the frame looks
enormously better. The number and the eye disagreed and **the eye was right**: what was wrong with
that field was that three.js's `DOUBLE_SIDED` normal flip was rendering roughly half of 177k blade
instances BLACK (authored up-normal → pointing at the dirt on a back face), which no saturation
statistic can see. The user read it as "hard black alpha edges"; there is no alpha in that material
at all.

**Where R6 stopped, deliberately.** Near-band saturation lands at 0.60–0.70, not the references'
0.48–0.49. Closing the rest was TRIED (key (1.0, 0.90, 0.74), grade tint 1.0): it reaches 0.585–0.639
and the frame stops being golden hour — trees flatten, the picture goes milky, the amber is graded
AWAY instead of into the light. Refused under the standing stylised-line ruling. **The remaining gap
is the terrain's own COLOR_0**, which was deliberately pushed to a strong yellow-green; that is a
CONTENT lever, not a grade one, and is the honest next move.

### Round 3, the build round: what shipped and what it cost

Three critiques were routed to one lane because they are one system — fill, exposure and haze
chase each other if they are tuned apart.

**LIT-TO-SHADOW**, `tools/ow_ratio.mjs`, four landscape cameras, mask taken from the ENGINE's own
shadow pass at `maskrel 0.5` (a pixel that keeps 50% of its key is not a shadow):

| view | ratio | L05 | L99 | chroma | shadow-side (g−r) |
|---|---|---|---|---|---|
| gate | 2.40 → **4.24** | .198 → .110 | .724 → .860 | .276 → .400 | −2.4 → **+4.0** |
| meadow | 1.77 → **3.29** | .213 → .122 | .750 → .841 | .256 → .385 | −0.3 → **+9.3** |
| vista | 1.79 → **3.92** | .249 → .132 | .771 → .777 | .169 → .272 | −0.2 → **+9.4** |
| gorge | 1.58 → **4.33** | .205 → .061 | .752 → .768 | .137 → .226 | −1.7 → **+11.7** |

The last column is the one that answers round 1's actual complaint — *saturation flat across the
terminator*. Before, the shadowed pixels and the lit pixels had the SAME hue and slightly less of
it. Now the shadow side runs blue-green (g−r positive) while the lit side goes further warm on
every view. gate and gorge sit just over the 2.5–4:1 golden-hour band and gorge's L05 lands at
0.061 against the references' 0.21–0.25: **recorded as the cost, not smoothed away.** By eye the
frames read as contrasty, not grim; if a later round disagrees, `?owenv=` raises the fill without
touching anything else.

**Three findings worth keeping, all of them corrections to something a lane believed:**

  * **`window.__envTune` — the documented fill knob — was lying twice**, and a whole sweep was
    wasted on it (k = 0.75 / 0.45 / 0.20 → 90 / 90 / 91, reported as "this lever is exhausted").
    It was CUMULATIVE while reading as absolute (0.75 / 0.45 / 0.20 is really 0.75 / 0.34 / 0.07,
    because `envApply` recorded its own already-scaled output as "the current environment"), and
    it scaled the sky gradient while leaving the SUN CAP alone — and at level 4.5 the cap was
    supplying roughly half the environment's irradiance. Both fixed in `play3d.html`. **A knob
    that moves a third of what it says it moves is worse than no knob: it gets swept, it reports
    a ceiling, and the lever was never pulled.**
  * **The fog was aimed at a thing that is no longer behind the terrain.** Its colour matched the
    sky's horizon band, which was right for a frame with no ridges in it; the camera tilt then put
    four ridge rings (luma 0.24–0.60) in front of that horizon, so far terrain was fading to a
    value BRIGHTER than the thing behind it. That, not exposure, is what read as a blowout.
  * **Two of the critic's three claims about the "firepit" were right and one was wrong.** It does
    not light anything (true — an emissive material emits nothing in three.js; it has a point light
    now) and its halo was oversized (true). The "hard-edged circular gradient decal painted on the
    ground under it" is `walk_emberbrook_green`, the village green — real geometry, checked before
    it was actioned. It is also not a firepit: it is the **Heartlight**, the town's whole identity.
    The rule the loop already carries held: a claim about the WORLD gets checked; a judgment of
    QUALITY is the deliverable.

### What the loop has established in two rounds

**The same deficit has now been named twice by two independent critics that never saw each other's
work: WE HAVE NO DIRECTIONAL LIGHT.** Round 1 measured it (1.30:1, reproduced by the pipeline lane
as 1.36:1). Round 2 named its consequence — form. That is convergence, not repetition, and it is
the strongest signal the loop has produced.

**The critic also corrected itself between rounds without being told.** Round 1 said "not one
shadow anywhere"; the pipeline lane measured the shadow pass moving **20.2% of the frame** and
proved it wrong. Round 2, judging a later frame, did not repeat the claim.

**And round 2 independently corroborated a defect a BUILDER could not fix.** The camera lane
reported "a pale grey rectangle upper-left of the gorge camera, world geometry, unresolved". The
critic — with no access to that report — called out "two hard-edged grey rectangles overlaying the
sky, reads as a crash artefact" and ranked it the most damning thing in either frame. **Two
independent observers, one artefact.** That is the blind critic earning its place.

**Standing strengths it keeps finding, which are worth defending:** our colour idea is the
boldest in the set (committed amber key against cyan river); our frame reads as INHABITED faster
than the commercial reference; and our navigation read is the clearest of the four. Round 1 said
our focal hierarchy beats the commercial frame's, which has none.

### Open, going into round 4

  * ~~The lighting lane died mid-sweep on the environment fill~~ — **landed, round 3 above.**
  * **The near field is the next deficit, and it is the CONTENT lane's.** Measured on the same
    plates: our near-band saturation is 0.70–0.79 against the two daylight references' 0.48–0.49,
    and it is FLAT with depth in the two close cameras (gate, meadow) because those frames have no
    distance for the aerial grade to work on. The blade carpet also reads oversized beside a 1.45u
    character at boom 12–16. Treatment cannot fix either; both are the grass material and the
    blade scatter.
  * ~~**The two grey rectangles over the gorge sky are STILL THERE**~~ — **named and fixed, R7
    below.** Not `edge_skirt`, not an impostor, not a shadow cascade: the AO pass's own depth buffer.
  * **`transition_test` aborts on its final assertion**, reproducibly: 13 sections green, then
    `HARNESS ERROR: ReferenceError: SIM is not defined` at the deep-link re-evaluate, immediately
    after the harness's own readiness check returned true on that page. **Provenance unknown** —
    no pre-camera baseline was obtainable while lanes held the file. Not claimed as pre-existing,
    not claimed as new.
  * **Three BROKEN items in the gorge frame** (grey rectangles, a straight-line blowout
    terminator, unlit white ridge trees) — these are bugs, not taste, and should outrank polish.

### R7: the three gorge artefacts were TWO buffers, and neither was the one being blamed

Plates `r7-gorge-before.png` (annotated — the first picture of the artefact anyone has drawn a box
on), `r7-{gorge,gate,meadow,vista}.png`, `r7-vista-before.png`.

**1. THE GREY RECTANGLES — the AO pass's own depth buffer.** Named by raycasting the pixels, not by
guessing: the first hit is `veg_canopy_farwall-crown_cards` at 11 m, and hiding that one mesh takes
the rectangles with it. GTAOPass draws its depth+normal prepass with `scene.overrideMaterial =
MeshNormalMaterial`, which carries neither the leaf atlas nor its `alphaTest 0.5`, so every
alpha-cut foliage card writes its WHOLE QUAD into the g-buffer — and a camera-facing billboard is
axis-aligned in screen space by construction. That is the crisp right edge and the crisp bottom
edge. GTAO then occludes a plane that is not there, and the aerial grade, which rides that same
depth, reads **11 m where the picture shows a 233 m ridge**: a rectangle of ridge skips aerial
perspective while the ridge around it takes the full cool-and-desaturate. Inside (100.9,120.0,113.4),
forty pixels away (95.2,108.3,131.4). **The discriminator that settled it: `?ao_i=0` removes the
rectangles and nothing else does — `?grade=0` and `?bloom_s=0` both leave them.** The grade was
innocent; it was told the wrong depth. Fixed by alpha-cutting the g-buffer (`?gbuf=0` restores).
`edge_skirt` really was not it, and neither was any impostor, LOD or shadow cascade.

**2 AND 3 ARE ONE NUMBER, and it is not a broken instance.** `scene.fog=null` turns every "unlit
white" plateau tree green again — the tree the critic named is plain `veg_field` at 153.6 m, 73%
of the way through a fog that ends at 195. The haze was aimed at `0xa8b8cc`, which sits between
rings 2 and 3, the two FURTHEST silhouettes, while the far terrain's skyline is drawn against
ring 0 (`0x6d7d95`). So R5's own diagnosis — *terrain fading to a value BRIGHTER than the thing
behind it* — survived R5's fix, and the horizon became a step instead of a dissolve. Far-ground
luma minus ring-0 luma at the crest: **`0xa8b8cc` +20, `0x8496a9` +9, `0x6d7d95` +3.** Ring 1
ships; ring 0 is too far — at +3 the plateau and the ridge are the same value and the skyline
stops reading at all.

**A PAINTED CONSTANT THAT A POST PASS REGRADES IS NOT A CONSTANT.** The same g-buffer hook holds
`__owsky` and the four `__owridge` rings out of it. They are `fog:false, toneMapped:false` on
purpose, and the 2026-08-04 rebuild exists precisely because fog was flattening their authored
`0x6d7d95 → 0xb8c8d6` recession — the grade was throwing it away again through a different door,
all four rings clamped to `t=1` against a 155 m `gradeFar`. `0x6d7d95` was reaching the frame as
(93,106,128). This is most of "the sky is a flat undifferentiated grey-blue with zero gradient".

**NOT FIXED, and it is not a bug:** the silhouette where terrain meets ridge is still slightly
aliased. The composer resolves 4x MSAA in the beauty buffer, but the depth texture the grade
samples is single-sampled, so an antialiased edge pixel takes a full-far grade and the AA is
undone. Inherent to depth-driven post; the fog change makes the step small enough that it barely
reads. Named here so the next round does not spend itself re-finding it.

### R8: "A GOT A COLOUR GRADE AND B GOT A LIGHT" IS TRUE OF THE PICTURE AND FALSE OF THE RIG

Plates `r8-{gate,meadow,vista,gorge}.png`, `r8-meadow-before-after.png`, and the one that
carries the finding: **`r8-why-meadow-has-no-shadows.png`** — the two frames with every pixel
whose KEY IS >60% BLOCKED painted magenta. In the gorge the whole shelf is magenta. In the
meadow not one cottage has magenta on the grass beside it.

Four rounds named "no directional light" as the biggest deficit and a lighting lane spent hours
raising lit:shadow. **The three obvious suspects were all measured and all three are innocent.**

  * **NOT THE SHADOW FRUSTUM.** Probed in the ENGINE at the meadow camera: every one of the 25
    meshes within 55 m — `emberbrook_1..5`, `walk_emberbrook_green`, `oldgate_*`,
    `veg_canopy_whisperwood` — projects **8 of 8 bounding-box corners inside** the ±115 ortho
    box. Shrinking the box to ±40 and to ±25 adds no shadow anywhere.
  * **NOT THE CASTER SET.** Every `ow-*` mesh carries `castShadow` and `receiveShadow` live in
    the scene graph, read off the running page, not the file.
  * **NOT TEXEL DENSITY.** `mapSize` 4096 (0.056 m/texel) and box ±40 (0.039 m/texel) both
    add no shadow that 2048/±115 did not already have.
  * **AND THE KEY ITSELF IS IDENTICAL.** Key-only render, everything else at zero: lit ground
    reads **0.510 in the meadow and 0.509 in the gorge**. Where an occluder does exist the
    shadow is DEEP — full-rig lit:shadow on a clean key-blocked mask is 3.83:1 (meadow) and
    5.15:1 (gorge). Nothing is stopping the light.

**WHAT IT ACTUALLY IS — CASTER ASPECT RATIO AGAINST SUN ELEVATION.** At 34° a shadow is
1.48× the caster's height. Emberbrook's overworld cottages are ~2.6 m tall and ~2.9 m wide, so
the shadow (3.9 m) barely outruns the footprint that threw it — and the meadow camera sits
within **18°** of straight down-sun (shadow XZ (0.527, 0.849) vs view dir (0.231, 0.973)), so
the remaining metre is behind the cottage. The gorge's caster is a 25 m cliff; its 37 m shadow
cannot be hidden by anything. **The one object in the meadow frame that casts a shadow you can
see is the character — the only object in it taller than it is wide.** That is the whole
difference, and it is a CONTENT fact, not a lighting one.

**TRIED — MADE IT WORSE, and the plates are on disk.** Both are the moves that would give a
2.6 m box a readable shadow, and both cost the frame that currently works:

  * **Elevation 34° → 28/24/20**, with the key multiplied by sin34/sinE so ground irradiance is
    conserved exactly. The meadow gains real house shadows and a real terminator. The gorge dies:
    at 24° the cliff shadow swallows the entire gorge floor and the plateau goes cold grey
    (`G-el24`). Refused.
  * **Azimuth 238° → 208/178/148/298** at unchanged elevation. At 178/148 the cottages finally
    get a lit face and a shaded face and throw shadows sideways where you can see them — and the
    gorge's shelf shadow, "the single best piece of lighting craft in either frame", **disappears
    entirely** (`G-az178`, `G-az208`, `G-az298`). Refused. 238° is load-bearing.
  * **The fill is not the flattener either.** Environment ground-hemisphere 0.55 → 0.20 → 0.08,
    and `OWBOUNCE` ×0.45 and ×0: the house's lit wall / shaded wall / roof move by **less than
    0.01 L each**. Measured, not argued.

**THE ONE REAL DEFECT IN THE SHADOW PASS, and it shipped: `normalBias` was 0.04 and needed
0.08.** At 0.112 m/texel the depth-slope error on ground under a 34° sun is texel·tan(56°) =
0.166 m; the two biases together bought 0.16 m. Marginally short, so **every open-ground pixel in
the corridor was self-shadowing** — measured key-only A/B on three caster-free grass patches:
5.4% of the key lost everywhere, laid down as a fine hatch over the whole meadow floor. 0.08
takes it to 1.9%. It is a TRADE, stopped where it was because normalBias erodes real shadows too
(character-shadow area 1017 px → 906 at 0.08, 799 at 0.12, 697 at 0.30): 0.12 and 0.30 buy almost
no further acne and cost the few small shadows this scene has.

**THE WORK ITEM THIS ROUTES TO CONTENT.** The overworld village is a field of ~2.6 m cubes beside
a 1.45 u character — a cottage is 1.8× her height where a real one is 2.5–3×. Nothing in the
lighting rig can make a box that is wider than its own shadow read as a solid. Taller houses,
a chimney or gable that breaks the silhouette, a fence line, anything with a height-to-width
ratio above 1, and this sun will draw it. **Do not send another lane at the key.**
