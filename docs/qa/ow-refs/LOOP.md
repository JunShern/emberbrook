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
| 9 | not judged — BUILT against 8 + three blind critics | plates `r9-*` | **the houses go up: ridge 1.6u → 3.7u, 1.1× the character → 2.65×, height:width 1.10 → 1.39** — and every cottage in the meadow now lays a shadow across the grass | TRIED — MOVED IT |
| 10 | `r9-*` judged blind | plates `r10-*` | **the light gets a SECOND COLOUR** — warm key + blue-violet fill, the warm grade back 50%, the Heartlight reined in from a global tint to a lamp; plinths capped, bases bedded, window panes given a dark albedo. Frame saturation 0.651/0.584/0.478/0.456 → **0.540/0.496/0.411/0.360**, b−r −0.357 → −0.284 on the meadow | TRIED — MOVED IT |
| 13 | `r12-*` judged blind | plates `r13-*` | **the shadow hue is MEASURED off the references instead of picked** (violet 273° then brown 41°, target 99–100° on grass / 209–227° on stone), the fill's LEVEL goes up rather than down, R11's toe comes off because **the references have ZERO pixels under L 0.10**, and the saturation pull becomes PER-MATERIAL on three channel-order selectors. Chimneys re-massed after measuring that all 25 overhung their own pad; the river gets Dellhollow's ratified depth→alpha at ×1.0. Δ hue +2.6 → **+11.1** (ref +12.9/+13.9), frame sat .447 → **.374** (ref .370/.381), L05 .098 → **.170** | TRIED — MOVED IT |
| 11 | `r10-*` judged blind | plates `r11-*` | **depth gets a hue and the frame gets a black point** — an exponential haze ramp anchored on the PLAYER, a mix toward a low-chroma blue at distance, a foreground toe, the terrain's own COLOR_0 off yellow, and the Heartlight's albedo (not its emissive) named as the thing that made it a white blob. Saturation **.545/.502/.413/.362 → .434/.376/.342/.333**, green b:g **.634 → .758** (meadow), L05 **.127 → .094**, pixels under L 0.10 **3.5% → 5.5%** | TRIED — MOVED IT |

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

### R9: A CASTER ASPECT RATIO IS CONTENT, AND CONTENT IS WHERE IT HAD TO BE FIXED

Plates `r9-{meadow,gate,vista,gorge}.png` against `r8-*`. Gallery section at the top of
`docs/qa/ow-refs/index.html`. One file changed the picture: `tools/valley_build.py`
(`house_dims` / `house_ground` / `impression_house`, now shared by BOTH towns) plus
`HOUSE_RIDGE` in `tools/valley_map.py`.

**The convergence R8 predicted was real, and it was reached twice by routes that could not
have contaminated each other.** The shadow probe measured a caster wider than its own
shadow; three blind art critics, with no access to it or to each other, each independently
named scale as the thing breaking the frame ("the character is roughly one house tall";
"the settlement reads as a tabletop model"; "either the houses go up ~2.5x or…").

| | R8 | R9 |
|---|---|---|
| ridge above floor | 1.60u | **3.70u** (mean 3.84 with jitter) |
| vs the 1.45u character | 1.10× | **2.65×** (2.97× to the chimney cap) |
| roof width | 1.48u | **2.76u** |
| height : width | 1.10 | **1.39** (wall box 1.75) |
| shadow at 34° | 2.4u, from a 1.5u footprint | **5.7u, from a 2.76u footprint** |

The last row is the whole round: 0.9u of shadow used to clear the building, and the meadow
camera sits 18° off straight down-sun, which spends exactly that. 2.9u clears it now, and
the plate shows it — **every cottage in `r9-meadow` casts a shadow that agrees with the
character's, and none did in `r8-meadow`.** THE SUN WAS NOT TOUCHED. Neither was the grade
or the camera.

**Not just taller — the blockout read was the other half of the ask.** Per house: a stone
footing that reaches BELOW the lowest footprint corner (a house on a slope meets the ground
instead of being cut by it — the "every house floats" note answered in geometry, not in a
shader), a dark eave board where roof meets wall, a steep gable, an EXTERNAL CHIMNEY STACK on
a gable end, a person-sized door, a ground-floor window and a lit gable window that says
there is an upstairs. Variety got a fifth axis (`kind`: plain / lean-to / tall two-storey)
on top of the four R7 added — scale jitter alone is fourteen copies at fourteen sizes, and
the critique was about the ASSET, not the size.

**A CHIMNEY PUSHED THROUGH A ROOF SLOPE READS AS DETACHED FROM A HIGH CAMERA**, and this
loop's own rule caught it: the first build put the stack at 0.17w/0.28d, geometrically
inside the roof plan and provably attached — and in the plate it floated, because the half
below the ridge is hidden by the NEAR slope. Moved to the gable end, where it runs ground to
sky in one line. *The geometry was right and the picture was wrong; the picture won.*

**WHAT THE HEIGHT CHANGE BROKE — and it broke in a frame, not in a gate.** Bigger footprints
forced a rescatter (min neighbour spacing 2.05 → 3.55u, road clearance +1.55 → +2.45u), and
the old placement cleared the road by pushing a house RADIALLY OUTWARD. For a house whose
bearing points along the road, that walks it *down* the road: one landed on the "Enter
Emberbrook" portal, standing on the marker with the player at its wall. Every gate in the
repo was green with it there. Fixed by searching radius AND bearing together, and the
closest house-centre-to-road distance is now recorded as `emberbrook_road_clear_u` (3.49u)
in `valley_build.json`, because a house on the road is invisible to every instrument here
and obvious in one screenshot.

Also carried: Dellhollow's pads shrank 1.55 → 1.24× footprint and their bedding tolerance
went 2.4 → 2.8u, or the wider houses would have cost the town a third of its stations (it
fell to 7 before the fix, 11 after); the weir mill grew to 4.0u, since a working building
shorter than the cottages around it stops reading as a mill; lantern posts and fence stakes
now skip any station a house centre has taken.

**Not touched, deliberately: the Heartlight.** Its geometry is at `village_h + 1.34` and
`play3d.html` hard-codes its point light at the same `+1.34`. Raising the monument to suit
4u houses would silently separate the orb from its light, and play3d is coordinator-owned.
It is a real deficit at the new scale — the town's whole identity is now a garden ornament
among its houses — and it needs the geometry and the runtime moved in one commit.

Gates: `playthrough_test` 86/0 · `cine_test` 689/0 · `slice_test` 848/0 ·
`findability_test` 69/0 · `walk_engine_gate --scene ow-valley` GREEN (0 cells lost,
418.2 m2 both sides) · `valley_verify` OK. Tris 266 786 → 267 122.

### R10: THE LIGHT HAD ONE COLOUR — AND TWO OF THE THREE BUGS REPORTED WITH IT WERE NOT THERE

Plates `r10-{meadow,gate,vista,gorge}.png` against `r9-*`. Gallery section at the top of
`docs/qa/ow-refs/index.html`.

**The critic's summary, and it is the clearest direction this loop has produced:** *"the light
has one colour instead of two; the ground is a colour instead of a surface; objects rest on the
terrain instead of being bedded into it. Fix those three and these frames move most of the
distance without a single new building model."*

**THE FILL WAS ALREADY BLUE. IT WAS NOT ALREADY VISIBLE.** R3 made the fill blue and wrote down
that the colour, not the level, was where the terminator was hiding — then left both too small to
read. At `owenv` 0.35 / `owbounce` 0.80 against a key of 2.60 x 2.40, a cottage's shaded wall took
so little fill that its hue was decided by whatever warm thing was nearest. In the meadow frame
that was **the Heartlight: 26 W at 26 m range, which covers every house in the picture**, and
Emberbrook's houses MOSTLY FACE THE GREEN, so the lamp was painting exactly the walls the key
could not reach. A lamp whose range does not stop inside the frame is the global tint this lane
keeps undoing, arriving through the one light nobody had audited.

Four numbers, and they only work together (all `public/play3d.html`, all still URL-sweepable):
fill hue `[0.35,0.62,1.00]` → `[0.42,0.44,1.00]` (the green channel was making the shade side
teal, too near the grass to read as a second light); `OWENV` 0.35 → 0.55 and `OWBOUNCE` 0.80 →
2.60 (the bounce is the DIRECTIONAL one — it buys the cool side without lifting the lit side, which
is the R5 trap); `gradeTint` 1.45 → 1.20; Heartlight 26 W/26 m → 10 W/15 m. **On its own the grade
number is the R5 regression again** — R5 already tried it and the frame went milky. Paired with a
fill that is genuinely a second colour it stops being a filter. Do not move one without the other.
**The sun's elevation, its azimuth and the camera were not touched.**

| | r9 | r10 |
|---|---|---|
| frame saturation, meadow / gate / vista / gorge | .651 / .584 / .478 / .456 | **.540 / .496 / .411 / .360** |
| mean (b−r), same four | −.357 / −.351 / −.166 / −.108 | **−.284 / −.303 / −.137 / −.084** |
| open-meadow grass RGB | (184, 170, 70) | **(197, 180, 111)** |
| window core RGB | (255, 228, 214) | **(245, 160, 122)** |

**THE FLOATING BUILDING IS NOT FLOATING, AND THE PROOF TOOK FOUR MINUTES.** The report was
specific — *"upper-left-centre, roughly x 480–580, y 200–340 … a detached slab hanging in mid-air
with a visible underside face and daylight beneath it"* — and specific is checkable. At those
pixels the first hit is `emberbrook_4`'s footing wall; **the ground is BEHIND the stone**, and the
footing's underside sits at y 25.77 against terrain at 26.19–26.33, i.e. buried 0.4–0.6 u. A
4 px-step scan of the whole frame for a downward-facing FIRST hit returns one 7-sample cluster,
on `emberbrook_1` inside the Heartlight's bloom, invisible; the gate, vista and gorge frames
return **none on any building**. The "daylight beneath it" is the downhill ground passing in
front. Blender agreed independently: 15 buildings, 0 with a positive gap.

**But the misread names a real defect, and that is why it was worth checking rather than
dismissing.** `ft` spanned `fl` down to `min(ch) − 0.40`, so on a station whose four footprint
corners spread ~1.3 u the "footing" grew to wall height — a 1.5 u block of stone with no contact
shading, which is what stops reading as a footing. Three lines fix it, in
`tools/valley_build.py`: the PROUD course is a constant 0.42 u whatever the slope does and the
part reaching the low corner is INSET (it draws its own shadow line instead of continuing the
wall); the floor stops chasing the high corner (`min + 0.70·spread + 0.20`, so the uphill side beds
INTO the ground — 0.70 and not 0.50 because a door sits at `fl + 0.54`); and the station search
prefers ground a mason would build on. **`emberbrook_house_slope_u` 1.3 → 0.47** and it is now a
recorded number, beside `emberbrook_road_clear_u` (unchanged at 3.49), for the same reason: a
house on a slope is invisible to every instrument in this repo and obvious in one screenshot.

**"A BLOB SHADOW WITH NO CASTER" HAS A CASTER.** Two discriminators, neither of them an argument:
it is pixel-identical with every `veg_` mesh in the scene hidden, and at `__shadowTune(0)` it
resolves into a chimney stack with a stepped silhouette. It reads as a smear at `shadow.radius`
1.5 because a 0.4 m chimney is four texels at 0.11 m/texel. Not fixed — named, so the next round
does not spend itself re-finding it.

**THE WINDOW WAS NEVER THE EMISSIVE, AND THREE ROUNDS HAD SWEPT THE EMISSIVE.** R5 and R6 both
tuned `OWEMIT` (9 → 5 → 3.4) against "the panes are clipped white". Measured this round: at
`?owemit=0.02` — emission effectively OFF — **and** `?bloom_s=0`, the window core still read
(254, 215, 193). `B.new_mat`'s `use_vcol` default hands Base Color to COLOR_0, which the class-gain
pass lifts toward its own target, so the pane had a near-white ALBEDO and the 2.4x golden key blew
it out unaided. `ow_f2_emit` now carries a fixed dark base (0.045, 0.030, 0.018) and `use_vcol=False`.
Only then did the knob start working: swept 3.4 / 2.2 / 1.4 → (254,207,182) / (253,193,160) /
(245,160,122) against the critic's own target of (255, 200, 120), and 1.5 is the first value at
which the pane has an EDGE rather than a white core with a warm surround. **A knob that has been
swept three times and never moved the thing it names is measuring something else.**

**Bedding, and the version of it that was worse.** A ring of trodden earth plus seven tufts that
straddle the plinth, in the house prop so it inherits the town's own class gains. The first ring
used f2's `DIRT` (9c8a70) untinted and arrived as CREAM under a 2.4x golden key — every house sat
in a bright halo, which is exactly the decal read the ring exists to prevent. `BED_TINT`
(0.60, 0.46, 0.33) makes worn ground the darkest thing at the base, which is what it is.

**Also landed:** roof planes facing away from the sun take 20% off COLOR_0 on a soft ramp
(`ROOF_AWAY`), computed from the towns' own ratified rig euler rather than a second copy of the
number — a stylisation baked into vertex colour, so it survives every camera and every grade.
Overworld bloom radius 0.15 → 0.075.

**Three new instruments on `SIM`, because every round so far has re-derived them by hand:**
`SIM.pick(px,py)` (the hit chain at a screen pixel — the R7 rule made callable), `SIM.px(x,y,w,h)`
(the composited framebuffer read back at a point), `SIM.vis(pattern,on)` (hide that one mesh and
see if the artefact goes). Two of this round's three "bugs" were settled with them in minutes.

Gates: `playthrough_test` 86/0 · `cine_test` 689/0 · `slice_test` 848/0 ·
`findability_test` 69/0 · `walk_engine_gate --scene ow-valley` GREEN (0 cells lost, 418.2 m2 both
sides) · `valley_verify` OK. Tris 267 122 → 268 546.

**What got worse, recorded and not smoothed away:** the gorge's far plateau is paler and cooler
than it was — the raised environment fill lands on everything, and that frame has the most sky-lit
open ground of the four. It is the price of the fill being visible at all, and it is why
`owenv`/`owbounce` are still knobs.

---

## Round 10 — the critic's verdict, and the question it was asked

Ten rounds in, the blind critic was given `r10-meadow` (A) and `r10-gorge` (B) against the two
references (C, D) and asked the question the loop exists to answer: **how big is the gap really,
and is what remains cheap or expensive?**

**Ranking: C ≈ D > B > A.**

> **"B is close. A is not, and A's remaining problem is craft, not budget."**

> **"Do not tell yourselves A's problem is asset budget. A's problem is that the frame has no
> value structure, no atmospheric recession, an over-saturated palette, an inconsistent key
> light, and one element (the fire) that is unfinished. Every one of those is free. You could
> add zero new assets to A and it would improve more than any asset pass would deliver."**

On B it is genuinely complimentary — the warm-lit/cool-shadow split on the cliff is called
**reference-grade**, the composition **more ambitious than either reference**, and the gap
**"largely a side-by-side gap"**: *"a player passing through B would register 'big flat rock
wall' rather than 'bad art'."* Asked whether a player would notice unprompted: **"A: yes,
immediately, and not in side-by-side. B: mostly no."**

**THE SINGLE LARGEST REMAINING CRAFT GAP, in its words:** *"value and chroma compression across
depth. In both A and B, near and far sit at the same contrast and the same saturation. C and D
both push distance toward low-contrast blue and hold their darkest darks in the foreground. This
single property is doing more work in the references than any texture or model in them, and
neither project frame has it."*

### The regression this round shipped, and how it got past me

The critic's warning: *"A looks over-corrected on warmth and saturation… the greens have gone
acid yellow-green. If the last round was a 'push the golden hour' round, it overshot."*

**I had looked at that same frame and reported the greens were back.** Both readings are
defensible about the pixels and only one is about the bar — I was comparing `r10-meadow` to
`r9-meadow`, which was orange, and scoring the delta. The critic compared it to the references
and scored the distance. **A frame that is better than our last frame and still wrong is a frame
that gets shipped when the comparison is to ourselves.** This is the third time in this loop the
same substitution has cost a round (the r3 lighting numbers, the reference set, this), and it is
the reason the critic is kept blind and the reason its verdict outranks mine.

It also supplies the test for the next round, which is deliberately not "does it feel warmer":
**are the greens off yellow, and is anything in the frame genuinely dark?**

### Standing after ten rounds

The user's instruction was to run at least ten and keep going while the judge is still useful and
a gap remains. **Both hold, so the loop continues.** The critic's own priority order for the
cheap list — campfire first (*"the highest impact per unit of work by a wide margin"*), then
distance haze with a hue target, a 15–20% global chroma pullback with the greens re-targeted off
yellow, a cool sky-fill so shade keeps chroma and texture, a darker ground plane, AA, a contact
shadow under the character, and sky dither on B.

Four items it named as broken are being **verified before they are built**, because two of this
critic's previous "bugs" (the floating building, the casterless shadow) were misreads that cost a
round each: free-standing chimneys passing the roof ridge, an untextured tan slope, a polygonal
violet ground region, and flat green discs on the gorge floor.

### R11: THE KNOB THAT HAD BEEN SWEPT FOUR TIMES WAS MEASURING SOMETHING ELSE, AGAIN

Plates `r11-{meadow,gate,vista,gorge}.png` against `r10-*`. Gallery section at the top of
`docs/qa/ow-refs/index.html`.

**The critic's verdict, and it is the one to keep:** *"Do not tell yourselves A's problem is asset
budget. A's problem is that the frame has no value structure, no atmospheric recession, an
over-saturated palette, an inconsistent key light, and one element (the fire) that is unfinished.
Every one of those is free."* Named largest gap: **value and chroma compression across depth** —
*"C and D both push distance toward low-contrast blue and hold their darkest darks in the
FOREGROUND."*

**1. THE HEARTLIGHT: FOUR ROUNDS SWEPT THE EMISSIVE AND THE EMISSIVE WAS NEVER IT.** R5, R6 and R10
swept `OWEMIT`; R11's first pass swept `emissiveIntensity` 0.52 / 0.26 / 0.13 / 0.06 and **the ball
did not visibly change** (`scratchpad r11 orb-sweep`). What decided those pixels, measured one toggle
at a time with `SIM.px` at the orb's own projected pixel (879,434):

| | orb centre | ground 80 px below |
|---|---|---|
| full | (238,146, 90) | (246,147,102) |
| sprites hidden | (118, 78, 72) | (242,143, 97) |
| **body mesh hidden** | **(241,149, 93)** | (245,146,101) |
| bloom off | (225,133, 82) | (245,145,100) |
| **hearth point light off** | (237,146, 90) | **(198,128,100)** |

  * **THE BLOB WAS THE TWO ADDITIVE SPRITES**, at opacity **1.615 and 1.955**. An additive sprite over
    1.0 has no falloff left in its bright half — every ramp stop past ~0.5 alpha already sums past
    white — which is a clipped plateau with the tail of a gradient round it, i.e. exactly *"a hard
    white circular blob with a soft radial falloff."*
  * **THE BODY MESH WAS INVISIBLE** (3/255 at its own centre), so every earlier note about "an opaque
    amber sphere carrying the shading" described an object nobody had ever seen.
  * **THE "GROUND BLOOM" WAS THE POINT LIGHT, NOT BLOOM** — 48/255 against UnrealBloom's 4/255 at the
    same pixel. 10 W / 15 m → 6 W / 9.5 m.
  * **AND THE PINK WAS THE ALBEDO.** `0xd4661c` at roughness 0.32 under a 2.6x golden key renders
    (2.16, 1.04, 0.29) — red and green both clipped — and `NeutralToneMapping` desaturates a clipped
    highlight toward white by design. `0x6a2c0a` + `envMapIntensity 0.20` keeps the whole sphere inside
    the curve, and `MeshBasicMaterial` → `MeshStandardMaterial` gives it a terminator. **A flat-shaded
    material cannot be "a core and a falloff": MeshBasicMaterial is a disc by construction.**

**2. THE DEPTH RAMP HAD NEVER RUN IN THE TWO FRAMES THAT NEEDED IT, and five rounds misread why.**
Linear over 28–155 m, smoothstepped: at 50 m, `t = 0.079`. The meadow and gate cameras see 10–60 m of
world, so the tan slope and the far houses took **8% of a cue built for a 155 m corridor**. R5 recorded
this as *"those frames have no distance for the aerial grade to work on"* — they have 60 m of distance
and **the ramp had none in that range**. It is an exponential extinction now (0.19 at 25 m, 0.50 at
50 m, 0.81 at 100 m, 0.94 at 155 m) plus a **mix toward a fixed low-chroma blue**, which is the only
one of the four terms that COMPRESSES CONTRAST — a multiply and a desat are per-pixel scalings and
contrast is a relation between pixels.

**3. AND THE RAMP HAD TO BE ANCHORED ON THE PLAYER, WHICH IS WHERE THE FIRST VERSION DIED.**
`length(viewPos)` is distance from the LENS on an orbit camera whose boom runs **12 m in the meadow and
40 m in the gorge**. A fixed `dNear` therefore starts the haze 26 m behind the character in one frame
and 2 m in front of her in the other: the gorge's cliff face — the subject — took half the atmosphere
meant for a 200 m ridge and the whole frame went milky (`scratchpad/r11/t1-gorge.png`, kept). **That is
the R5 regression arriving through a different door, and the door is that the cue's origin was the
wrong object.** `dRef` is the lens-to-character distance; `dist - dRef` reads the same at every boom.

**4. THE FIRST PASS PASSED THE CRITIC'S FIRST TEST AND FAILED ITS SECOND, and the numbers said so
before the eye did.** Saturation 0.545 → 0.402 and green b:g 0.634 → 0.771 (both asks met) — while
**L05 went 0.127 → 0.148 and the share of pixels under L 0.10 went 3.47% → 2.31%. The frame had got
LIGHTER in its darks.** Two wanted changes did it: a raised sky fill (which is what puts texture back
in shade) and a haze that lifts the far band — and the second is not a defect, since *"hold their
darkest darks in the FOREGROUND"* means far darks SHOULD lift. So the black point is bought back where
the reference keeps it: a **toe weighted by (1−t)**, biting only on already-dark pixels in the near
field. Final: L05 **.127/.151/.143/.072 → .094/.108/.121/.056**, darks **3.5/2.3/3.2/7.5% →
5.5/4.6/3.6/10.8%**.

**5. THREE OF THE FOUR NEW BUG REPORTS WERE REAL, AND ALL FOUR WERE CHECKED BEFORE ANYTHING WAS BUILT.**

  * **THE CHIMNEYS WERE GENUINELY DETACHED, AND IT IS ARITHMETIC.** `gs * d * 0.60` against a 0.34-deep
    stack puts its inner face at `0.60d − 0.17`; the gable wall's face is at `0.50d`. They touch only
    when `d ≤ 1.70`, and `house_dims()` draws d in **1.30–2.68**. Most of the town had a pillar with
    daylight behind it. **An offset that is a fraction of a jittered dimension is a contact that is a
    coin toss** — it is measured from the wall face now, with 0.14 u of interpenetration and a flashing
    collar at the eave.
  * **THE FLAT GREEN DISCS WERE REAL.** `veg_land_clumps`, first-hit normal (−0.06, 0.99, −0.14) — a
    horizontal facet. `_clump_geo` squashed the unit ico to 0.62 and then `w` and `h` were drawn
    INDEPENDENTLY (0.75–1.80 against 0.45–1.20), mean 1.28 × 0.51, aspect 0.40. Height is drawn from
    the width now, and **the PRNG stream is preserved exactly** (same seven calls in the same order) so
    this module's port check still means something.
  * **THE TAN SLOPE IS NOT A MISSING MATERIAL.** `SIM.pick` returns `ground_valley_2` — the DRY slot —
    on BOTH sides of the boundary. What was missing is variation: the dry recipe's noise amplitude was
    0.24–0.34 against grass's 0.30–0.40, on a gain that made it the brightest thing in the frame, so it
    clipped flat. dry L 0.428 → 0.248, amplitude doubled, seam probe 2.1 → 3.2 u.
  * **THE DARK VIOLET GROUND REGION IS THE ROAD MESH.** `walk_road` at y 26.12 with `ground_valley_1`
    behind it; the "partly straight polygonal edge" is the road polygon. Not a lightmap artifact — but
    the reason it reads as a stain is the critic's item 4, so the fix is the sky fill, not the road.

**6. TWO INSTRUMENT BUGS PAID FOR IN THIS ROUND, both worth keeping.**

  * **`THREE.MultiplyBlending` PLUS `transparent:true` BRIGHTENS IN THIS BUILD**, and the first version
    of the contact shadow shipped a WHITE SQUARE under the character into a plate. One pixel, everything
    else held: plane hidden (134,86,68) · MultiplyBlending+transparent (157,115,98) · MultiplyBlending
    opaque (134,86,68) · CustomBlending ZERO/SRC_COLOR+transparent (133,86,67). **dst×src cannot
    brighten**, so the named blend mode is not the mode being applied. The factors are written out.
  * **A REPORT COMPUTED IN `ow_multi`'s `expr` IS COMPUTED BEFORE THE CAMERA HAS SETTLED.** The orbit
    camera damps toward its target over several frames, so `wp.project(cam)` inside the expr put the
    Heartlight at pixel (5802,−4895) and the first fire probe measured five points that were all off
    canvas and all read (0,0,0). Defer the report by ~1.6 s inside the settle window.

**Also landed, all in `public/play3d.html`:** a compact luma FXAA + interleaved-gradient dither as the
final composer pass — **after `OutputPass`, which is the only place FXAA's luma thresholds mean
anything**, and the answer to R7's own unactioned note that MSAA is resolved in the beauty buffer and
then undone by a grade sampling a single-sampled depth texture (raising the sample count cannot fix a
pass that runs after the resolve; three's bundle carries no `SMAAPass` and no `FXAAShader`, checked).
Sky dome 32×20 → 64×44. Global chroma −13% in the grade on top of the terrain's own −20%. Sky fill
`OWENV` 0.55 → 0.60.

Gates: `playthrough_test` 86/0 · `cine_test` 689/0 · `slice_test` 848/0 · `findability_test` 69/0 ·
`walk_engine_gate --scene ow-valley` GREEN (0 cells lost, 418.2 m2 both sides) · `valley_verify` OK.

**What got worse, recorded and not smoothed away:** the frame is **less warm**. The terrain gain drop
and the global chroma pull together take the golden-hour push down, and `gate`'s L50 falls 0.644 →
0.573. The critic asked for exactly this and said to judge on greens and darks rather than warmth, so
it is a trade taken deliberately — `?grade_sat=1` and `?grade_h=0` back both halves out without a
rebuild, and `grass_gain` in `tools/valley_land.py` is the third. **And the chimney read is fixed in
geometry but not perfected in the picture:** verified attached by raycast (stack at 13.6 m, its own
roof slope at 14.17 m, adjacent in screen space), yet a full-height external stack seen from a
near-top-down camera is still a long pale rectangle crossing a roof — the R9 finding recurring, and the
next round's if it is raised again.

---

## Round 11 — the wiring round, and the tint it shipped

**What the builders actually found is worth more than what they were sent to do.** The assigned
list was treatment. Three of the items on it turned out to be things that had never been
connected at all.

**THE CAMPFIRE, after four rounds of sweeping the wrong knob.** The emissive was swept again
(0.52 / 0.26 / 0.13 / 0.06) and the ball did not visibly change. Measured per-object with
`SIM.px`, one toggle at a time: the white blob is **two additive sprites at opacity 1.615 and
1.955** — above 1.0 an additive sprite has no falloff left in its bright half, so it is a clipped
plateau with a gradient tail, which is the critic's sentence verbatim. **The body mesh was worth
3/255 at its own centre**: the "opaque amber sphere carrying the shading" that three rounds of
notes describe *had never been visible*. The ground bloom is the point light (48/255), not
UnrealBloom (4/255). And **the pink was the ALBEDO** — `0xd4661c` at roughness 0.32 under a 2.6x
key renders (2.16, 1.04, 0.29), and `NeutralToneMapping` desaturates a clipped highlight toward
white BY DESIGN.

**THE DEPTH RAMP HAD NEVER RUN IN THE MEADOW OR GATE FRAMES.** Linear 28–155 m gives t = 0.079 at
50 m. Five rounds read those frames as "having no distance". **They have 60 m; the ramp had none
in it.** Now exponential and anchored on the PLAYER, not the lens — the first attempt hazed the
gorge cliff (the subject) into milk, because the boom is 12 m in one frame and 40 m in the other.

**That is the fourth instance in two nights of one pattern**, after the window `use_vcol`, the
campfire emissive above, and the playtest finish line: **a knob that has been swept repeatedly
without moving the thing it names is not a tuning problem, it is a wiring problem.** Sweeping is
what you do to a connected knob; the sweep itself is evidence when it comes back flat.

Measured, both of the round's own tests passed: greens off yellow (b:g on green pixels
**.634 → .758** meadow, **.632 → .774** gate), real darks (L05 **.127/.151/.143/.072 →
.094/.108/.121/.056**; pixels under L 0.10 **3.5/2.3/3.2/7.5% → 5.5/4.6/3.6/10.8%**), saturation
**.545/.502/.413/.362 → .434/.376/.342/.333**.

### And the rank did not move: D > C > B > A

The blind critic ranked us **last**, and this round says plainly that *"A and B are not at the
same level"* as the references. **Both tests passing and the rank unchanged is the round's real
result** — the two tests were necessary and they were not sufficient, because the fix for each
one arrived with a side effect nobody measured.

> *"Over-correction, since you asked directly: yes, in both, and it is saturation and contrast
> again. In A the shadows are crushed nearly to black **and tinted** — the ground shadows read
> blue-purple. In B the same fault is worse and larger: the big shadow across the gorge floor
> turns the road a **plum/magenta**, occupying roughly the bottom third of the frame."*

That is round 11's cool sky-fill landing on top of round 11's crushed darks — **two fixes that
were each correct and are wrong together.** The same knob is over-corrected the other way in B's
upper-right meadow, *"a pale lavender-white wash so desaturated it looks blown out rather than
distant."* A grade has no local scope: it is applied to everything, so every push has a second
place it lands, and the round that ships it is the round that owes that measurement.

**And the ramp is on and still not doing anything at the meadow's distances:** *"A collapses
depth entirely — the far hill at top right and the near tree at top left carry the same contrast
and saturation."* Wiring it was necessary; its near/far anchors are still wrong for a 60 m scene.

**The orb is now worse than the blob it replaced.** The critic, unprompted and knowing none of
its history: *"untextured with a single specular hotspot; whatever it's meant to be, it is
currently a beach ball"*, filed under missing material. Two rounds have now made this object
worse. Round 12's instruction is that **a restrained version beats a conspicuous wrong one** — if
it will not read as a lamp, it goes small and dim.

**New and cheap, from this round's critic:** the windows are *"flat unlit orange rectangles with
no frame, no glass, no recess — they read as stickers on a wall"* (the same window whose albedo
was fixed last round — fixing its colour did not make it an opening); B's distant hills are
*"four flat bands of blue-grey with hard edges and zero internal gradient — textbook paper
cutouts"*, which is the banding, not the colour.

**Bugs: three of four real.** Chimneys genuinely detached (`gs*d*0.60` against a 0.34 stack
contacts only when `d ≤ 1.70`; `house_dims` draws 1.30–2.68). Discs genuinely discs. The violet
region is `walk_road`. **The tan slope was NOT a missing material** — same DRY slot both sides,
it carried half of grass's noise at twice the gain, which is why it read as untextured.

Gates: `playthrough_test` 86/0 · `cine_test` 689/0 · `slice_test` 848/0 · `findability_test` 69/0 ·
`walk_engine_gate ow-valley` GREEN · `valley_verify` OK.

**Also paid for:** `THREE.MultiplyBlending` + `transparent:true` **brightens** in this build, and
it shipped a white square under the character into one plate before the factors were written out.

### R12: THE FILL WAS PAINTING THE SHADOWS VIOLET, AND THE DEPTH RAMP WAS CALIBRATED FOR A CORRIDOR THAT IS NOT IN ANY OF THE FOUR FRAMES

Plates `r12-{meadow,gate,vista,gorge}.png` against `r11-*`.

**The twelfth critic ranked us LAST, and its top item was R11's own side effect:** *"it is
saturation and contrast again. In A the greens are pushed into chartreuse and the shadows are
crushed nearly to black AND TINTED — the ground shadows read blue-purple. In B the same fault is
worse and larger: the big shadow across the gorge floor turns the road a PLUM/MAGENTA, occupying
roughly the bottom third of the frame."*

**1. THE SHADOW TOOK A HUE, AND IT IS ONE LINE OF ARITHMETIC.** The fill R11 raised to put texture
back into shade was `[0.42, 0.44, 1.00]` — G BARELY ABOVE R with B at 2.4x both, which is a
VIOLET, not a sky. A warm-brown albedo (road, earth, timber) multiplied by it comes out with R and
B up and G down: plum by construction. `SIM.px` on the gorge road: **(29, 23, 34), hue 273 deg.**
NEUTRALISED, NOT DELETED (the user's instruction, and the fill is what R10's warm-key/cool-fill
split rests on): the hue goes to a pale sky blue with R < G < B and a modest spread, B/R
2.38 -> 1.47, so a shadow now takes ITS OWN ALBEDO'S chroma instead of the fill's hue.

**AND THE LEVEL HAS TO MOVE WITH THE HUE OR IT IS A BRIGHTNESS CHANGE WEARING A COLOUR'S CLOTHES.**
Making a fill less blue RAISES its luminance, because the Rec.709 weights price a green channel at
10x a blue one: L[0.42,0.44,1.00] = 0.476 against L[0.68,0.76,1.00] = 0.760. `OWENV` 0.60 -> 0.376
is exactly that ratio and `OWBOUNCE` takes the same pair. Shade luminance is held; only its hue
moves.

| SIM.px, same boxes | r11 | r12 |
|---|---|---|
| gorge road, in shadow | **(29, 23, 34)** B>R>G, hue 273 | **(31, 28, 19)** R>G>B, hue 41 |
| gorge road, lower | (25, 29, 32) | (31, 37, 20) |
| gorge floor, in shadow | (45, 52, 58) | (46, 55, 41) |
| meadow road, in shadow | (73, 52, 51) | (74, 55, 42) |
| L of those four | .099 / .111 / .198 / .221 | **.110 / .135 / .204 / .229** |

**2. THE RAMP WAS ON, ANCHORED, EXPONENTIAL — AND NORMALISED OVER 149 m OF WORLD THAT IS NOT IN
THE PICTURE.** R11 fixed linear-vs-exponential and left the SPAN. Measured with `__depths` (a
raycast census on a 40 px lattice) and `__t` (the ramp evaluated off `PFXRIG`'s own shipped
uniforms), both in `scratchpad/r12`:

| | depth beyond the character, p90 | max | t at the farthest thing in frame |
|---|---|---|---|
| meadow | 34.2 | 50.4 | **0.50** |
| gate | 26.7 | 40.1 | **0.32** |
| vista | 35.8 | 49.6 | - |
| gorge | 33.5 | 127.7 | **0.63** |

**Nothing in any of the four frames ever got more than half the cue.** `dNear` 6 -> 10, `dScale`
60 -> 20, `dFar` 155 -> 60: the meadow's far slope now runs at t 0.84 and its far hill at 0.88,
while the near canopy at 11 m takes 0.06, so the foreground is still untouched by construction.
**ASK THE FRAME HOW DEEP IT IS BEFORE CALIBRATING A DEPTH CUE FOR IT** — one raycast, five rounds.

**3. AND THE HAZE TARGET WAS WRITTEN IN THE WRONG COLOUR SPACE, which is why more haze made the
distance WHITER.** `hazeCol` 0.395/0.455/0.560 are the sRGB components of the ridge colour it was
anchored to, and the grade runs BEFORE `OutputPass`, i.e. in the LINEAR working space: the target
was landing on screen at about (168, 179, 196) — a stop and a half up with most of its chroma
gone. So "mix the far band toward a low-chroma blue" was mixing it toward a pale near-neutral.
That is the critic's *"B's upper-right meadow is a pale lavender-white wash so desaturated it looks
blown out rather than distant"*, and it was the HAZE, not the fill. `srgbToLinear` ->
0.127/0.175/0.275. (CLAUDE.md's own rule, third time paid: SAY WHICH SPACE THE BYTES ARE IN.)

| meadow, near vs far | r11 | r12 |
|---|---|---|
| near canopy | sat .240  ctr .211  (t .091) | sat **.228**  ctr **.210**  (t .064) |
| far tan slope | sat .324  ctr .038  (t .466) | sat **.164**  ctr **.033**  (t .839) |
| far hill | sat .170  ctr .036  (t .501) | sat **.073**  ctr **.029**  (t .879) |
| **near - far saturation** | **-0.084 (INVERTED: far was MORE saturated)** | **+0.064 / +0.155** |

B's blown slope: (187, 193, 212) sat .134 -> **(154, 164, 174) sat .119**, now sitting beside the
ridge band it is supposed to recede into (128, 147, 168).

**4. THE GREEN PULL COULD NOT BE DONE IN THE ALBEDO, AND THREE BUILDS PROVED IT BEFORE ONE
MINUTE WOULD HAVE.** The critic asked for a further 25-30% off the greens — and neutralising the
fill had just put chroma BACK into the grass (lit meadow sat .317 -> .398 with nothing but the
fill's hue changed). Three rebuilds moved `valley_land.surface()`'s grass multiplier (b:g 0.81 ->
0.91 -> 1.03, verified changed IN THE EXPORTED GLB) and the meadow moved **1/255 each time**. The
decisive test needs no build at all: set `ground_valley_1`'s COLOR_0.z live in the running page and
read the same probe box — **x1.127 -> +2/255, x2.818 -> +14/255.** A 182% lift in the ground's own
albedo blue buys 13% of the screen's, so that pixel's blue is not mostly albedo x light and THIS
WAS NEVER THE KNOB. Both albedo attempts are reverted with their receipt. **Fourth knob in this
loop swept while disconnected; the live-attribute test is the discriminator and it goes FIRST.**

Done instead in the grade, per-pixel, after everything — and **NOT AS A GREEN TEST**. Our "greens"
have RED as their max channel under a (1.0, 0.70, 0.42) key: lit meadow is (180, 169, 108), so a
`g > max(r,b)` selector scores it at ZERO and would desaturate nothing. The chartreuse signature is
BLUE AS THE MINIMUM with r and g together, so the selector is `(min(r,g) - b) / max`: meadow grass
0.53, canopy 0.5, orange roofs 0.18, the dry slope 0.10, the character's teal dress 0.

| | r11 | r12 |
|---|---|---|
| lit meadow grass | sat .317 | **.261** (-18% on r11, -34% on the un-tinted frame) |
| shaded green | sat .349 | **.288** |
| near canopy | sat .240 | **.228** |
| lit roof | sat .566 | **.563**  (untouched, which is the point) |
| dry slope | sat .324 | .164 (that is the haze, not the pull) |

**5. THE WINDOW WAS DETACHED FROM THE HOUSE, and it is the chimney's own arithmetic recurring in
the line directly below it.** *"Flat unlit orange rectangles with no frame, no glass, no recess —
they read as stickers on a wall."* The gable pane's centre was `-gs * d * 0.60` with a 0.09
thickness, so its INNER face sat at 0.555d against a gable wall face at 0.50d: **floating
0.07-0.15 u off the building on every station where d > 1.7, and `house_dims()` draws d in
1.30-2.68.** R11 wrote AN OFFSET THAT IS A FRACTION OF A JITTERED DIMENSION IS A CONTACT THAT IS A
COIN TOSS while fixing the chimney, and the neighbouring line still broke it. Measured from the
wall face now. The recess is joinery, not a boolean: the pane sits at the wall plane and a SILL, a
LINTEL, two JAMBS and a glazing bar stand proud of it, so the 34 deg key throws a real shadow
across the glass. Five cubes a window, no new material, +3.6k tris town-wide.

**6. THE BEACH BALL IS DELETED, WHICH IS THE FIX.** The critic, unprompted and with no knowledge of
this object's history, filed the Heartlight under MISSING MATERIAL: *"untextured with a single
specular hotspot; whatever it's meant to be, it is currently a beach ball."* The user's ruling:
make it SMALL AND DIM RATHER THAN LARGE AND SMOOTH. Four rounds have changed what the sphere is
made OF (emissive x4, then the albedo, then Basic -> Standard) and none has changed that it is a
big smooth ball, which is the thing being reported. So play3d's 0.54 m covering sphere goes
outright; the bundle's own emissive ico drops 0.44 -> 0.26 and gains three ribs, a flared hood and
a finial (existing materials, existing primitives), and the sprites come down with it (glow 2.6 ->
1.25 m, core 0.55 -> 0.34, lift 0.62/0.66 -> 0.24/0.26 so THE HOOD OCCLUDES ITS OWN GLOW). It
reads as a hooded lamp on a plinth at the ~40 px it occupies.

**7. THE FIVE "ALSO NAMED BROKEN", each checked before anything was built. Three real, two not.**

  * **THE CHIMNEY INTERSECTION WAS REAL AND R11'S COLLAR WAS AT THE WRONG HEIGHT.** The stack
    stands at u = 0 and **u = 0 is the roof prism's RIDGE**, so the crossing is at the apex,
    `fl + max(rh, eh+1.01)` — a metre or more above the eave board R11 collared. The collar was
    inside the wall. Moved to the crossing. **AND THE FIRST VERSION OF THAT WAS WORSE AND ONLY
    LOOKING SAW IT**: a 1.44x collar on a narrow shaft high in the frame is a floating SHELF, and
    the stack became a totem of hovering slabs. Collars 1.44x -> 1.18x, and the shaft itself
    narrowed 0.34+0.10s -> 0.27+0.08s, which is the half of "a pale wide column crossing a dark
    roof" nobody had moved in three rounds.
  * **THE BLOTCH IN A IS A REAL CAST SHADOW.** Toggled `R.shadowMap.enabled` with everything else
    held: it is pixel-present with shadows on and GONE with them off, and `SIM.pick` at its centre
    returns `walk_emberbrook_green` (the ground). Its caster is out of frame, which is what the
    report was reading as absent. Not a defect. Same class as R10's.
  * **THE GREY SLIVER AT TOP-CENTRE OF A IS NOT UNRESOLVED GEOMETRY.** `__t` returns
    `ground_valley_3` — the ROCK slot — at 50.7 m of depth: the far crag, correctly drawn. It read
    as a flat grey wedge because at r11's ramp it took t 0.573 of a cue that never reached; it now
    takes 0.947 and recedes. Misread, and the fix was the ramp.
  * **THE BLACK WEDGES IN B'S CLIFF ARE GEOMETRY, NOT SHADOW ACNE.** Same shadow toggle: they are
    UNCHANGED with `R.shadowMap.enabled = false`, so there is no bias fix. They are the crag
    tessellation's own long sliver triangles. Named, not fixed — a bias sweep would have been a
    round spent on the wrong mechanism.
  * **B'S HARD SHADOW BOUNDARY ACROSS THE GORGE FLOOR IS THE GORGE RIM'S OWN SHADOW** (it vanishes
    with the shadow map off, with the rim behind the camera). Real light, offscreen caster.

**8. Also landed:** the four `__owridge` bands get an INSIDE — *"four flat bands of blue-grey with
hard edges and zero internal gradient, textbook paper cutouts."* The silhouette was fixed in R7 and
was never the tell; a shape filled with ONE constant is. Each ring carries a vertex-colour
MULTIPLIER (deliberately a multiplier around 1.0, not a colour, so `material.color` keeps doing the
sRGB conversion and this attribute stays a plain linear scalar — writing the hue there would be
item 3's bug again): haze pools in the valleys, so the base lifts and the crest sits darkest, plus
a per-column wobble. **THE SKIRT VERTEX IS AT y = -60 AND THE GRADIENT IS NOT** — a value written
at the skirt has interpolated ~80% of the way to the crest by y = 0, so the skirt value is SOLVED
to make the linear interpolant equal the base shade at y = 0 instead.

Gates: `playthrough_test` 86/0 · `cine_test` 689/0 · `slice_test` 848/0 · `findability_test` 69/0 ·
`walk_engine_gate --scene ow-valley` GREEN · `valley_verify` OK. Tris 268 546 -> 272 102.

**What got worse, recorded and not smoothed away:** the meadow is **greyer**. The yellow-selective
pull, the neutral fill and a haze that now actually reaches all land on the same frame, and
`near-grass-lit` sits at sat .261 against r10's .317 and r9's .40+. The critic asked for exactly
this and said to judge on whether the greens came off yellow — but if the next round says the
frame has gone drab, `?grade_gp=0`, `?owfill=0.42,0.44,1.00&owenv=0.60` and `?grade_h=0.34` back
out the three halves independently without a rebuild. And the chimneys are IMPROVED, NOT SOLVED:
they are still pale stone columns read from a near-top-down camera, the fourth round in which that
sentence is true.

---

## Round 13 — THE ROUND WHERE WE STOPPED GUESSING THE SHADOW COLOUR AND MEASURED IT

Plates `r13-{meadow,gate,vista,gorge}.png`. Commits `c6830a0` `e0d8d90` `6f737e7` `d0ae583`
`4aa8138` (content) `c7aa270`.

**THE SHADOW HUE HAD NOW BEEN GUESSED TWICE AND MISSED TWICE IN OPPOSITE DIRECTIONS** — r11
violet (hue 273), r12 warm brown (hue 41) — and the thirteenth critic said the target was
neither: *"Both A and B take a MUDDY GREY-OLIVE, and both should be taking COOL BLUE…
nothing inside it is cooler in hue than the lit grass beside it, which is what makes the
whole frame read as unbounced spotlight rather than golden hour."* **An oscillation is the
signal to stop picking the number by taste.**

### The references' own numbers (scratchpad/r13/refhue.py)

Classify by material, then split each material by ITS OWN luminance quartiles — no
hand-picked boxes, and the SAME classifier runs on our plates, which is the only reason the
two columns can be compared at all.

| | shaded hue | lit hue | Δ hue | shade sat | sat ratio shade/lit | shade/lit L |
|---|---|---|---|---|---|---|
| ref 1 grass | **100.3°** | 87.4° | +12.9 | 0.388 | 2.41 | 0.53 |
| ref 3 grass | **99.0°** | 85.1° | +13.9 | 0.454 | 1.36 | 0.59 |
| ref 1 stone | **226.5°** | 135.0° | +91.4 | 0.236 | 4.61 | 0.35 |
| ref 3 stone | **209.2°** | 122.9° | +86.3 | 0.352 | 11.39 | 0.34 |

**Three things that are not obvious and are now measured:**

  1. **A REFERENCE SHADOW IS MORE SATURATED THAN THE LIGHT BESIDE IT.** Their neutral stone
     runs sat 0.03 in sun and 0.24–0.35 in shade. The shade is where their colour LIVES.
  2. **THEIR SHADOWS ARE NOWHERE NEAR BLACK.** Over the playfield of both shots **ZERO
     PERCENT of their pixels sit under L 0.10** and their L05 is 0.211/0.276. Ours were
     0.084/0.043 with 6.4%/14.2% under 0.10. **R11's toe was buying back a black point the
     references do not have** — and a crushed shadow has no signal left to carry a hue,
     which is half of why this axis has been missed twice.
  3. **Violet was never wrong for being COOL, it was wrong for being MAGENTA.** R11's
     `[0.42,0.44,1.00]` had G barely above R. The refs' shaded stone is R < G < B with G
     nearer the middle — a cyan-blue at ~210–227°.

So the fill takes **their** hue, `[0.55,0.72,1.00]` = 217.3°, and **the level goes UP,
0.376 → 0.95.** R12 cut the level to hold shade luminance while it moved the hue — correct
arithmetic for the move it was making, and exactly what pinned the shade at 0.20 of lit.
The toe drops 0.38 → 0.06. `?owfill= ?owenv= ?grade_toe=` back all three out.

| meadow | r12 | **r13** | reference |
|---|---|---|---|
| grass shade hue | 74.6° | **83.9°** | 99–100° |
| lit→shade Δ hue | +2.6 | **+11.1** | +12.9 / +13.9 |
| grass shade sat | .564 | **.428** | .388 / .454 |
| frame saturation | .447 | **.374** | .370 / .381 |
| L05 | .098 | **.170** | .211 / .276 |
| pixels under L 0.10 | 5.1% | **1.2%** | 0.0% |

Gorge grass shade hue **79.9 → 98.9** against their 99–100. **The DELTA is on their number;
the ABSOLUTE is ~15° short because our LIT grass sits at 72° against their 85–87° — that is
the KEY's warmth, a different axis, out of scope this round, and the honest next lever.**

### The saturation pull was global where it had to be per-material

*"A is over-corrected grey on the greens… while the roofs stay a strong terracotta and the
river stays a strong cyan — that is the signature of a GLOBAL saturation walk-back applied
where a PER-MATERIAL one was needed. Two loud colours on a dead field."* As arithmetic:
**the meadow was 44.8% warm-hue pixels at sat 0.534, where the references are 0.3–1.5% at
0.371–0.490**, while our greens sat under both. One `sat` scalar cannot move one without the
other.

Three channel-order selectors, no texture reads: `yel=(min(r,g)−b)` vegetation,
`wrm=(r−max(g,b))` fired clay, `cyn=(min(g,b)−r)` the river. **Shaded grass scoring ZERO on
`cyn` is load-bearing** — after the fill fix shade swings blue-green, and a naive "cool
pixels" selector would have desaturated every shadow in the frame and undone the round's
other half. b is still below r in shaded grass, which is what keeps them apart.
Meadow: warm sat .534 → .426, green .397 → .426, cyan .450 → .288.

### FOUR LESSONS ABOUT INSTRUMENTS, all paid for in this one round

  * **"ALMOST NO HUE VARIATION" WAS NOT ABOUT VARIATION.** Our vegetation's hue SD is 18.2
    against the references' 16.4 and 19.8, and our IQR is inside theirs. **The spread was
    always fine; the CENTRE was wrong** — hue mean 74.2 against 85.6/94.3. An olive is a
    green whose hue is wrong, not a green with no variance. Had we read the WORD instead of
    the pixels we would have spent the round adding noise to a field that already had it.
  * **WHEN A TREATMENT CHANGES THE CLASSIFIER, MEASURE ON THE PIXELS AND NOT ON THE CLASS.**
    The vegetation hue knob swept 0/0.10/0.20 read 77.3/76.8/77.3 — flat, and by this repo's
    own rule four words from being filed as this loop's FIFTH disconnected knob. It is not:
    the gain pulls marginal pixels across the family's own 55° edge (share 22.6% → 28.4%)
    and they land at the bottom of the range. On a FIXED pixel set: 77.3 → 79.6 → **81.6**.
  * **TWO OF THE CRITIC'S ITEMS WERE ONE KNOB PULLED IN OPPOSITE DIRECTIONS.** The gorge's
    *"hard-edged pale flat-shaded triangles… a broken normal or a near-white material"* is
    **not geometry at all** — a 600-sample raycast census returns `ground_valley_3` and
    Dellhollow's own houses, zero ridge hits, zero sky hits, and `?gbuf=0` leaves it
    identical. It is **the haze**: with post off that box is (26,21,22) at L 0.086 and
    relative contrast 1.02 — a legible terraced cliff with a terracotta roof in it — and
    shipped it was (58,70,89) at L 0.270, contrast 0.27. A lerp toward a MID value **lifts a
    far DARK far harder than a far LIGHT** (3.13×, 4× flatter). But turning `grade_h` down
    would have taken the cue off the far hillside, which the same critic calls flat. Gating
    the mix on the pixel's own luminance serves both: cliff L 0.296 → 0.203, hillside
    **unchanged to three decimals**. Third instance of *a grade has no local scope*.
  * **THE SECOND FIX TO LAND ON A SHARED HUE OWES A RE-SWEEP OF THE FIRST.** `wp` was swept
    to 0.26 against the old bundle; the content lane then pulled the ROOF albedo, and the
    two stacked past the references (frame sat 0.347) with the roofs merging into the timber
    walls. Re-swept to 0.12. Lane scope is not the same as effect scope.

### Content (commit 4aa8138)

  * **THE CHIMNEY WAS OVERHANGING ITS OWN PAD, ON ALL 25 HOUSES, AND THAT IS WHY THREE
    ROUNDS OF DETAIL FIXES DID NOT LAND.** The stack stood `cd − 0.14 = 0.20u` proud of the
    gable wall face while the plinth reaches only `0.035·d` (0.046u at d=1.30, 0.094u at
    d=2.68) — so 0.11–0.15u of stack hung over open ground with its base *above* it. *"The
    column isn't on the pad"* and *"background grass visible in the gap at its base"* were
    literally true and measurable. **Third fraction-of-a-jittered-dimension contact in this
    file** after r11's stack and r12's window pane. Re-massed: footprint inside the plinth,
    outer face recessed 0.03u BEHIND the wall, cap clearing the ridge by ≥0.55u, nothing a
    fraction of `d`. **Gated, not asserted** — a house failing any clause is built without a
    chimney; 25/25 pass (pad margin ≥ +0.082, recess +0.030, ridge clearance +0.568…+0.827).
    The visible object is now only the 0.6–0.8u above the roof: **a short stack that is part
    of the building beats a tall one that isn't.**
  * **THE RIVER HAD A BED ALL ALONG**, which is the opposite of Dellhollow and is why
    `water-transparency.md`'s recipe applied at ×1.0 with no bathymetry work: 0/85 stations
    missing a bed, median depth 1.63u, and **86% of the strip edge buried in the bank**
    against Dellhollow's 43–79% floating. Two exporter facts measured in the shipped GLB:
    COLOR_0 exported as **VEC3** until the Alpha socket is fed from it, and **one mixed-
    material mesh disables vertex alpha for every primitive in it** (hence `water_falls_lip`
    became its own mesh). Alpha 0.06 at the shore → 0.94 at depth; tint neutralised (a blue
    multiplying an already-blue albedo made the product MORE chromatic than either):
    river box sat 0.469 → 0.265.
  * Roof albedo `a86b52` (s .512) → `917366` (s .297) at held luminance.

### Bugs: two REAL, two CLOSED

  * **THE CHARACTER IS NOT A MISSING MATERIAL** — the item that would have outranked
    everything. Her body carries a bound 4096² map + metalnessMap + roughnessMap +
    normalMap, `__chardump2` returns byte-identical records at a 40 m boom and a 4 m boom
    (no LOD, no streaming), and whole-figure saturation falls only 0.369 → 0.329 across an
    85 px and a 17 px rendering — mip averaging. **She is 17×41 px, standing in the gorge
    rim's own shadow, on a dark road, at max boom. STAGING, NOT MATERIALS.**
  * **THE SOFT SHADOW IS CLOSED WITH NO CHANGE.** Caster named: `ground_valley_3`, 23.5 m
    up-sun and off the left of frame. The shadow map is not the cause — **8.6× more filter
    sharpness (ortho ±115→±40, radius 1.5→0.5, 2048→4096) buys 3 px of a median 18 px
    edge**, because the edge's y-position wanders with std 20.7 px: **THE WANDER IS LARGER
    THAN THE BLUR.** A radius-6.0 control (median 54 px) proves the instrument is sensitive.
    And tightening the ortho box flat-lights Dellhollow's houses at 72–76 m. Its interior is
    not dead either: shadowed floor relative contrast 0.863 vs lit floor 0.762.
  * The pale triangles and the flat hillside: above.

**What got worse, or is knowingly unfinished:**

  * **The far hillside is flat BEFORE any post pass runs** — Lstd 0.049 against the
    mid-ground's 0.076. Every face normal on it lies within ~2° of the same direction,
    nothing casts onto it, and 7 of 600 samples hit vegetation. **It needs VALUE structure,
    not colour; a hue or saturation move will not land.** Routed to r14, content lane.
  * Shade still sits at 0.34 of lit against the references' 0.53–0.59, and 1.2%/3.4% of
    pixels remain under L 0.10 against their 0.0%. Going the rest of the way costs the
    lit/shade separation rounds 1–3 were fought for; stopped deliberately, `?owenv=1.10` is
    the measured next rung.
  * Roof luminance rose ~5% on the box probes (desaturating at a held max lifts the dark
    channels). The river reads faint in the shallow upper reach of the vista frame — it is a
    stream over a mossy bed now, not a ribbon. `?grade_vb=0.28` under the shade weighting
    was measured and changes nothing.
  * `?grade_vh=0.20` is measured and **REFUSED BY EYE** — the canopy goes acid lime. Which
    is the whole reason the plates get opened.

Gates: `playthrough_test` 86/0 · `cine_test` 689/0 · `slice_test` 848/0 ·
`findability_test` 69/0 · `walk_engine_gate ow-valley` GREEN (0 lost, 418.2 m², BVH fail 0) ·
`valley_verify` OK. Tris 272 102 → 274 154.

---

## Round 12 — the diagnosis round, and the overshoot it shipped

Three defects, all arithmetic, none of them taste.

**THE PLUM SHADOW WAS A VIOLET FILL, LITERALLY.** The sky-fill was `[0.42, 0.44, 1.00]` — G barely
above R, B at 2.4x — **which IS a violet**. Any warm albedo in shade came out with R and B up and
G down; there was never a grade to blame. Neutralised to `[0.68, 0.76, 1.00]` (B/R 2.38 → 1.47)
and compensated by the exact luminance ratio (`OWENV` 0.60 → 0.376, `OWBOUNCE` 2.60 → 1.734), so
the hue moves and shade brightness holds. Measured on the gorge road in shadow:
**(29,23,34) B>R>G, hue 273° plum → (31,28,19) R>G>B, hue 41° warm brown.** The fill was NOT
deleted; it was a fix for shadows crushing to mud and deleting it would have re-bought that.

**THE DEPTH RAMP WAS ON AND SPANNING NOTHING.** A raycast census of the four frames: they hold
**40–60 m of depth beyond the character, and the ramp was normalised over 149 m**, so the farthest
pixel anywhere in any frame only ever reached t 0.32–0.63. `dNear` 6 → 10, `dScale` 60 → 20,
`dFar` 155 → 60. The near-minus-far saturation delta went **−0.084 (INVERTED — the far hill was
more saturated than the near canopy) to +0.064 / +0.155**.

**AND `hazeCol` WAS sRGB FED INTO A LINEAR PASS**, landing on screen a stop and a half up — so
**adding haze made distance WHITER instead of bluer**. That was B's lavender wash:
(187,193,212) → (154,164,174), now sitting correctly beside the ridge band at (128,147,168).

**Named-broken: three real, two misreads** — and the misreads cost nothing because they were
checked before anything was built. The chimney/roof intersection is real (r11's collar was at the
EAVE; the stack crosses at the RIDGE). The cliff wedges are real and are **GEOMETRY, NOT SHADOW
ACNE** — unchanged with the shadow map off, so no bias fix exists for them. The gorge shadow
boundary is real with an offscreen caster. The meadow blotch is a genuine cast shadow. The grey
sliver is `ground_valley_3` at 50.7 m, correctly drawn. The window pane was **literally floating
0.07–0.15 u off the wall** — r11's chimney arithmetic in the line below it.

Gates: `playthrough_test` 86/0 · `cine_test` 689/0 · `slice_test` 848/0 · `findability_test` 69/0 ·
`walk_engine_gate ow-valley` GREEN (0 lost, 418.2 m2). Tris 268 546 → 272 102.

### THE RANK DID NOT MOVE, FOR THE THIRD ROUND: D > C > B > A

**And two of the round's own fixes are why.**

**THE SHADOW HUE OSCILLATED PAST THE TARGET.** r11 was violet at 273°; this round landed warm
brown at 41°; the critic wants **cool blue**, and points at the references to say what that means:
*"shadowed grass swings distinctly blue-green and shadowed rock goes violet"*, while ours is *"a
muddy grey-olive… nothing inside it is cooler in hue than the lit grass beside it, which is what
makes the whole frame read as unbounced spotlight rather than golden hour."* **Twice guessed,
twice missed, in opposite directions.** Violet was wrong because it was magenta-leaning with G
suppressed — not because it was cool. A golden-hour shadow is lit BY THE SKY and belongs near
200–230°. Round 13's instruction is therefore to **measure the references' own shadow hue first
and target that number**, because an axis that has been guessed twice is an axis that has earned
an instrument.

**AND THE SATURATION PULL WAS THE WRONG INSTRUMENT.** The critic's diagnosis is the sharpest
sentence the loop has produced:

> *"The grass is a dull uniform olive with almost no hue variation, while the roofs stay a strong
> terracotta and the river stays a strong cyan — that is the signature of a **global** saturation
> walk-back applied where a **per-material** one was needed. It killed the vegetation and left the
> two hero hues untouched, so the frame is **two loud colours on a dead field**."*

A global grade cannot pull one material and lift another; reaching for it means every future
correction lands on everything. That is the same shape as the round-11 note that *a grade has no
local scope* — recorded then as a caution, now as a measured cost.

**Carried, and now third-round items.** The stone columns still read as *"separate objects leaned
against the houses"* — with grass visible in the gap at the base, a flat cap terminating in mid-air
beside the roofline, and one column standing on bare grass while its house sits on a gravel pad.
Two rounds of partial fixes (the eave collar, the ridge crossing) have not landed it. **Three
rounds of patching one object is the signal to reconsider the massing rather than patch again** —
a missing chimney is invisible; a detached one is the first thing the eye finds.

**New this round:** the river is *"opaque flat cyan… the most saturated thing in the frame and the
least believable material in either frame"* (this repo already ratified a water treatment in
`docs/plans/water-transparency.md` — apply what Dellhollow earned, do not invent a second water);
and in B the player character reads as *"a pale untextured sliver… a missing material, not a
design"*, which if real is a GAME bug and outranks the art list.

**What the critic will not let us tell ourselves:** *"Both A and B are short of C and D, and it is
not a content gap: it is atmosphere, shadow colour, and vegetation. The cliff in B proves the
hard-surface craft is already there."*

---

## Round 13's verdict — WE MATCHED THE NUMBERS AND LOST THE PICTURE

Round 13 built the best instrument this loop has produced and then optimised into a worse frame
with it. Both halves of that sentence are true and the second one is the lesson.

**The instrument, which stands.** `scratchpad/r13/refhue.py` classifies pixels by MATERIAL, then
splits each material by ITS OWN luminance quartiles — no hand-picked boxes — and the identical
classifier runs on the references and on our plates. It overturned three things the loop had been
treating as settled:

  1. **A reference shadow is MORE saturated than the light beside it** (ref grass shade sat
     .388/.454). We had been desaturating shade on the assumption that shadow means muted.
  2. **ZERO percent of the references' pixels sit under L 0.10.** Ours were 6.4% / 14.2%.
     **Round 11's ratified test — "is anything in the frame genuinely dark?" — was buying a black
     point the references do not have**, and a crushed shadow has no signal left to carry a hue,
     which is why the hue kept refusing to land. The fill level went UP (0.376 → 0.95) where
     round 12 had taken it down.
  3. **Violet was wrong for being MAGENTA, not for being cool.** Both earlier guesses misread
     which property was the defect.

Measured after: shaded grass hue **83.9° / 98.9°** against the references' 100.3° / 99.0°; fill at
**217.3°**, inside their stone band of 209–227; frame saturation **.374** against their
.370 / .381; under-0.10 **1.2%**.

**And the blind critic called the result washed out.**

> *"Yes, A is washed out — plainly, and it is the flatter of the two. The entire frame lives in a
> narrow band of warm beige-green. There is no true dark anywhere… Every house wall is the SAME
> tan, and the roofs are only a few percent different in value from the walls — so the whole
> village reads as **one undifferentiated putty-coloured mass**… **This is over-correction in the
> desaturating direction, not under-correction.**"*

> *"A reads as **late afternoon light under a completely overcast sky** — a contradiction, a
> directional sun with no sky to justify it."*

**WHY THE MEASUREMENT DID NOT PROTECT US, precisely.** The classifier measured GRASS and STONE and
matched their aggregate statistics. **The houses were never a measured class.** Walls and roofs
are exactly where the flatness reads, and no grass-or-stone statistic constrains them. **A
statistic is a constraint on a DISTRIBUTION and says nothing about the RELATIONSHIPS inside the
frame — which is where craft lives.** Matching a histogram is compatible with every local contrast
in the picture being wrong.

**THE RULE, which is the user's own and now has a measured cost behind it: numbers are for
iteration, the picture is the verdict. When a measurement and the eye disagree, the eye wins and
the measurement gets extended.** Round 14 extends the classifier to walls and roofs — and if the
gap the critic describes does not show up as a number even then, the instruction is to SAY SO
rather than report a clean table.

### The single highest-value move, in the critic's words

> *"Raise the key-to-fill ratio and warm the key — deepen shade, let sunlit tan go warmer and
> shaded tan go cooler. That is **cheap** (a light and a grade) and it is **the highest-value
> single move in the set**, because it fixes flatness AND partly fixes the same-coloured-houses
> problem **by splitting every wall into two tones.**"*

With a constraint that makes it interesting rather than a revert: **deepen the shade WITHOUT
re-introducing a black point.** r13's 0.0%-under-L-0.10 finding stands. More lit-to-shade
separation with the floor still off the bottom is contrast, not a toe — and reaching for a toe is
the easy version of this fix.

### What the critic will not let us forget

> *"A **does** have charm its execution is hiding — the lit waystone is the one warm accent in the
> frame and it works; the chimney cluster, the stream, the little pink-haired figure on the path
> all say 'village you'd want to walk into.' That is not nothing, and it is **being smothered by
> the grade, not absent.** B is prettier and emptier — atmosphere without charm. **A is charm
> without light.**"*

Four rounds without the rank moving, and this is the first round where the critic says the thing
we are looking for is already in the frame and being suppressed, rather than missing from it.

**Also disproved this round, cleanly.** The "missing character material" was **staging, not
materials**: bound 4096² map plus metalness, roughness and normal; `__chardump2` byte-identical at
a 40 m and a 4 m boom (no LOD, no streaming); the saturation drop .369 → .329 is MIP AVERAGING on
a figure rendering at 17x41 px, in the gorge rim's shadow, on a dark road, at max boom.

**And a diagnosis that correctly refused its own assignment:** the far hillside is flat BEFORE any
post pass runs — Lstd .049 vs mid-ground .076, every face normal within ~2° of one direction,
nothing casting on it, 7/600 samples hitting vegetation. *"A hue or saturation move will not
land."* Routed to round 14 as CONTENT rather than faked in the grade, which is the right call and
the kind of refusal this loop needs more of.
