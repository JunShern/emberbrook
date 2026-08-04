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
| 14 | `r13-*` judged blind | plates `r14-*` | **the value statistics said the frame was not flat and it plainly was** — 5-95 range 0.559 against the references' 0.523/0.442, IQR and local contrast both inside their band, and the critic called it "one undifferentiated putty-coloured mass". The number that agreed with the eye was HUE: circular R **0.872** against their 0.631/0.493, 95% of the frame's chroma inside one 90-degree arc. The grade's warm/cool split turned out to have only ever had its WARM half written. Key:fill 7.6 -> 17.5, a luminance-neutral cool push on shade, a chromatic floor instead of a toe, and the roofs take the VALUE they had been denied | TRIED — MOVED IT |
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

## Round 14 — EVERY VALUE STATISTIC SAID THE FRAME WAS NOT FLAT, AND IT PLAINLY WAS

Plates `r14-{meadow,gate,vista,gorge}.png`. Commits `9d7cbb0` `39d7d31` (pipeline)
`13cd671` (content).

Round 13 built the best instrument this loop has made — a material classifier that splits
each material by ITS OWN luminance quartiles and runs identically on the references and on
our plates — used it to overturn three settled beliefs, matched the references on every
number it could see, and shipped a frame the fourteenth blind critic called *"plainly the
flatter of the two... one undifferentiated putty-coloured mass... over-correction in the
desaturating direction"*. **This round is what that costs and how it was caught.**

### THE VALUE LADDER IS EVIDENCE OF NOTHING, AND HERE IT IS

`tools/ow_probe/framespread.py` (promoted out of the gitignored scratchpad so the source
comments do not dangle). Masks the references' HUD; identical treatment otherwise.

| | 5-95 range | IQR | 9x9 local SD | under L 0.10 | circular R | hue SD | sectors >= 8% |
|---|---|---|---|---|---|---|---|
| ref 1 | 0.523 | 0.219 | 0.0434 | 0.00% | 0.631 | 55.0 | 3 |
| ref 3 | 0.442 | 0.152 | 0.0367 | 0.03% | 0.493 | 68.1 | 4 |
| **r13 meadow** | **0.559** | **0.259** | 0.0393 | 1.26% | **0.872** | **29.9** | 3 |

**OUR LUMINANCE RANGE IS WIDER THAN EITHER REFERENCE. OUR INTERQUARTILE SPREAD IS WIDER.
OUR LOCAL CONTRAST SITS BETWEEN THEM.** By every value statistic the frame is not flat, and
it plainly looks flat. R13 had matched their L05 and their share under L 0.10 — and both of
those describe only the BOTTOM of a histogram, so a frame can carry the reference's floor
and none of its picture.

The number that agrees with the eye is the HUE one. Chroma-weighted circular R 0.872 against
0.631 and 0.493, and the three loudest 30-degree sectors are **R 0-30 (53%), O 30-60 (20%),
Y 60-90 (22%) — THREE ADJACENT SECTORS holding 95% of the frame's chroma inside one
90-degree arc.** Both references' third sector is a CYAN-BLUE carrying a fifth of the frame,
and we had none of it. *"The entire frame lives in a narrow band of warm beige-green"* is
that table.

**A STATISTIC IS A CONSTRAINT ON A DISTRIBUTION AND SAYS NOTHING ABOUT THE RELATIONSHIPS
INSIDE THE FRAME**, which is where craft lives. When a measurement and the eye disagree, the
eye wins and the measurement gets extended — user ruling, and this round is its first
worked example.

### THE GRADE HAD ONLY EVER HAD ITS WARM HALF WRITTEN

R6 gated the warm push on `litK` and left the shade at `vec3(1.0)`. The only cool term in the
whole pass rides `t`, which is DEPTH. **So for eight rounds the grade warmed the light and did
nothing whatever to the shade at the player's feet** — while three consecutive critics asked
for a cool shadow side. The fourteenth named the fix in one sentence and called it the
highest-value single move in the set: *"let sunlit tan go warmer and shaded tan go cooler...
it fixes flatness AND partly fixes the same-coloured-houses problem BY SPLITTING EVERY WALL
INTO TWO TONES."*

**TWO TONES MEANS TWO COLOURS, NOT TWO VALUES**, and that is why this is the move rather than
more key. `shadeCol` is luminance-normalised to 1.0000 on the Rec.709 weights, so the split is
a hue rotation with no level in it and **cannot move the black point R13 measured** — R13's
finding is preserved arithmetically rather than by being careful. Hue 213 deg, inside the
references' own 209-227 shaded-stone band.

**AND IT IS STEERED OFF THE VEGETATION**, by R13's own yellow selector read off the SOURCE
pixel rather than the already-tinted one: their shaded grass sits at hue 99-100 and their
shaded stone at 209-227, **110 degrees apart**, and one cool multiply cannot serve both. Run
flat, it takes the grass shadows teal — the trap R13's `cyn` selector was written to dodge,
arriving from the other side.

### CUTTING THE FILL IS THE HALF THAT WORKS; RAISING THE KEY IS THE HALF THAT CLIPS

Key:fill 2.40/0.95 -> 3.00/0.55, a luminance ratio of 7.6 -> 17.5. Five rungs, two views,
every plate opened:

| owkey / owenv | L50 | L95 | IQR | under L 0.10 | max > 0.97 | |
|---|---|---|---|---|---|---|
| 2.40 / 0.95 | 0.505 | 0.728 | 0.259 | 1.26% | 0.34% | shipped r13 |
| 2.70 / 0.72 | 0.518 | 0.742 | 0.281 | 1.71% | — | |
| 2.90 / 0.62 | 0.528 | 0.754 | 0.292 | 1.82% | — | |
| 3.20 / 0.50 | 0.546 | 0.770 | 0.306 | 1.93% | 0.66% | |
| 3.60 / 0.38 | 0.572 | 0.789 | 0.321 | 2.23% | 1.20% | lit grass blowing |

Past 3.2 **the shade stops getting deeper at all** (L05 0.150 -> 0.148) while the sunlit grass
goes to white-green, which is an item on the same critic's list. So the ratio is bought mostly
on the fill. The references clip 0.45-0.93% of their pixels above 0.97; 3.00/0.55 lands at
0.6% rather than exceeding it. R13's own note that the `?ibl=0` fallback is committed to
"roughly the environment's own irradiance" is honoured: both its lights move by the same
0.579x, or that branch becomes a second, staler art direction.

### THE FLOOR IS THE DELIBERATE INVERSE OF R11'S TOE

The brief's constraint was *"deepen the shade WITHOUT re-introducing a black point... it is
contrast, not a toe. If you find yourself adding a black point you have taken the easy
version."* The ratio move DOES re-buy one — measured, owenv 0.95 -> 0.62 takes the meadow's
share under L 0.10 from 1.26% to 1.82%. So the floor is put back separately, and **as a
COLOUR**: an additive lift in `shadeCol` under linear L 0.055 only, because a floor under a
shadow is physically the sky and a neutral lift is the milky wash R5 was refused for.
1.37% at 0.014, with midtones and highlights untouched by construction.

### THE CONTACT SHADOW WAS NEVER MISSING — IT WAS A CIRCLE

Three critics in a row wrote that she *"has no contact shadow at all on the path"*, and the
reflex readings (the quad is absent; MultiplyBlending vanishes over dark ground) are BOTH
WRONG AND WERE MEASURED. A/B at `?contact=0` against `?contact=1.15`, meadow, the 24x54 px
box at her feet: **(101,75,65) -> (59,36,32)**. It darkens the ground by 41% and is still not
read as a shadow.

**Because a symmetric pool under a figure lit at 34 degrees is the one thing a real shadow
never is.** The eye files it as vignetting on the texture. Stretched 2.1x along the sun's own
bearing — derived from `OWSUN_DIR`, never a second copy of the number — squeezed across it,
and walked half its long axis down-sun, the same pixels become the ROOT OF A CAST SHADOW. A
contact shadow's job is to join a figure to the ground plane, and joining needs a direction
to join along.

### THE RIVER: THE SECOND FIX TO LAND ON A SHARED HUE, AGAIN

Not untouched — R13 ported `docs/plans/water-transparency.md` at x1.0 after measuring that
this channel has the bathymetry Dellhollow's pools did not, and the shipped frame has a bed,
a shore transition and a depth read. What R13 also did was cut the water's ALBEDO chroma 31%
in the bundle **and leave a 20% cyan pull on top of it** — the same stacking that had already
cost the roofs a re-sweep four paragraphs earlier in its own entry. Measured on the meadow's
river box: sat **0.235** with the pull, **0.298** without, against ref 3's water at **0.387**.
**The river was the palest thing in the frame and this term was still desaturating it.**
`grade_cp` 0.20 -> 0.06, the token that keeps the falls and tributaries — which have no
bathymetry and still run at a flat `GLASS_OPACITY` — from being the loud cyan it was written
for. Still open: the ratified recipe's FOAM LOBE has no port, and our water's local contrast
is 0.039 against the reference's 0.066.

### WHAT THE INSTRUMENT SAID ABOUT THE ROUND'S OWN CONTENT FIX

The ladder, one lane per step, all four frames under the same camera:

| meadow | 5-95 range | under L 0.10 | circular R | hue SD | sectors | coloured % |
|---|---|---|---|---|---|---|
| r13 shipped | 0.559 | 1.26% | 0.872 | 29.9 | 3 | 84.3% |
| + r14 pipeline | 0.611 | 1.50% | 0.856 | 31.9 | 3 | 82.7% |
| + r14 roofs | 0.601 | 1.99% | **0.638** | **54.3** | **4** | **72.5%** |
| ref 1 / ref 3 | 0.523 / 0.442 | 0.00 / 0.03% | 0.631 / 0.493 | 55.0 / 68.1 | 3 / 4 | 84.1 / 81.5% |

**The pipeline could not move the hue spread and was never going to** — the frame's narrowness
is an ALBEDO fact, and a post pass that widened it would be the global tint this lane has now
undone four times. The roof value split moved circular R onto ref 1's number exactly, and the
picture agrees: the village reads as buildings.

**AND THE SAME TABLE CARRIES THE OVERSHOOT.** `coloured %` — the share of the frame with any
chroma at all — falls 84.3 -> 72.5 against the references' 81.5-84.1. Twelve percent of the
frame lost its colour, which is the roofs arriving as a NEUTRAL that happens to sit cool
rather than as the references' saturated blue-grey slate (roof HSV sat 0.076 against ref 3's
0.446, roof-wall warm-cool -0.26 against -0.07). **The cool sector was bought with hue
DISTANCE because chroma was unavailable, and the sector metric was satisfied by something
that does not look like the thing the metric was chosen to detect** — round 13's failure, one
level down, caught inside one round instead of after one. Named and open.

### THE ROUND'S OWN RULE, ARRIVING ON THE ROUND'S OWN WORK

The roof was solved a third time. `2d4db1` was derived backwards from the reference
slate's ABSOLUTE CHROMA and it hit the target — 0.149 against their 0.154, up from
0.044 — and the frame it produced has **cobalt roofs**: the village reads as a painted
toy set. `framespread` said the same thing from the other side, circular R **0.363**
against ref 1's 0.631 and ref 3's 0.493, **past both references**, with the cyan-blue
sector at 24% against their 21% but carrying a hero colour instead of a material.

**THE PICTURE REFUSED THE NUMBER.** Shipped at `32498f`, which is 40% of the way from
the first solve to the second in EFFECTIVE albedo — arithmetic, not taste, because the
blue channel's hex-to-shipped-albedo transfer is linear at gain 0.1366 measured on both
builds' own GLBs. Meadow circular R **0.541**, vista **0.474**, gorge **0.661**, against
the references' 0.631 and 0.493.

**AND THE RESIDUAL GAP IS A VALUE GAP, NOT A CHROMA GAP** — this is the reusable half.
`sat = chroma / max`, our roof's max channel is **0.480** where the reference's is
**0.344**, and their wall sits at L 0.280 against our 0.423: **our built palette renders
about 1.5x brighter than the windmill it is being matched to.** At OUR brightness their
SATURATION lands as cobalt, because a slate is a dark saturated blue and the dark half
is not available without moving the roof/wall value ratio this round just put on their
number (0.85 against 0.82). Nobody should spend another pass on the palette entry.

Two more instrument failures worth the same treatment as R13's four:

  * **THE CLASSIFIER WAS DELETING THE THING IT WAS SENT TO MEASURE.** `matclass.py`
    inherited R13's water exclusion, and the moment the slate became slate that rule ate
    **36% of the roof boxes' pixels — the bluest ones** (63 223 against 40 450), reading
    sat 0.165 where the truth was 0.309. It had been biasing the previous plate too
    (0.076 reported, 0.114 true), so part of "5.9x under" was the instrument. Separated
    on the axis that actually distinguishes them: a river is CYAN (g nearer b), slate is
    BLUE (g nearer r), `cy = (g−r)/(b−r)` splits them 1.02/0.68 against 0.24/0.26. **The
    reference's own numbers moved the same way** (roof sat .446 → .457) — it was biased
    on both columns, which is the only reason the comparison survived at all.
    Same shape as the exclusion that could not see a cool built surface because it was
    written against art we did not have: **AN EXCLUSION AUTHORED AGAINST YOUR OWN FRAME
    CANNOT MEASURE A FRAME YOU HAVE NOT BUILT YET.**
  * **A RAYCAST IN THE SAME EXPRESSION THAT AIMS THE CAMERA REPORTS THE OLD AIM.**
    ORBIT → camera happens in the render loop, so the cliff lane's first probe named the
    far hillside as `__owridge` backdrop rings — a clean, confident lie. Aim, settle,
    THEN raycast.

### CARRIED, WITH REASONS

  * **The roof-saturation gap is OPEN** — 0.309 against the reference's 0.457, and it is
    the value fact above. It stays named.
  * **Our frame now carries a loud warm sector AND a loud cool one** where both references
    are green-dominant with only 8% warm. The walls are the remaining warm mass.
  * **The clifftop lip is improved, not solved.** The residual sawtooth is the heightfield's
    own 1.25 u tessellation at a convex break; it needs a lip bevel, a bigger geometry
    change than this round.
  * **The top-left cliff fragment is DIAGNOSED, NOT FIXED**: an engine raycast returns
    `ground_valley_3` at 36–40 m — the west canyon wall's own rim run-out, not a prop and
    not a clipped mesh. Fixing it is a `valley_map` massif edit. Named so nobody builds
    against a guess.
  * **The river's foam lobe has no port.** `water-transparency.md`'s ratified recipe is
    depth→alpha PLUS a foam lobe on an AO-proximity × flow-noise mask; R13 brought the
    first and not the second, and our water's local contrast is 0.039 against the
    reference's 0.066.
  * **The "Enter Emberbrook" marker over empty ground: NOT TRIED, deliberately.** It is the
    FF7 exit-marker DOM overlay sitting at the scene edge's own anchor — gameplay UI, and
    moving it is seam-canon territory rather than art.
  * **The meadow frame contains essentially no sky**: what reads as one is a hazed ridge
    band at saturation **0.091**, against the references' sky at 0.27–0.35. That is
    literally the "completely overcast" read, and the structural answer is the CAMERA
    PITCH, which the user has explicitly opened and which no lane took this round.

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

---

## Round 14 — CONTENT lane, SECOND PASS (append-only; the coordinator owns the round-14 heading above)

Continuing `13cd671`, which landed the roof/wall **value** ratio (1.14 → 0.82 against the
reference's 0.83) and did not land the roof's **chroma** (HSV sat 0.076 against 0.446).
Instruments: `tools/ow_probe/matclass.py` (the picture), `tools/ow_probe/glb_albedo.py`
(the artifact), `tools/ow_probe/framespread.py` (the frame's hue histogram). Plates
`scratchpad/r14-content2/p1-*.png`, four canonical viewpoints, `ow_multi.mjs`, no `--extra`.

### THE WARM KEY CANCELS A COOL ALBEDO, and the factor is 2.4x, not 1.7x

`13cd671` recorded "per-channel irradiance on a roof runs 7.36 / 5.65 / 4.34 … a 1.7x warm
light cancels most of a cool albedo." **The finding is right and the number was stale** — it
was read before that commit's own second push of `ROOF_HEX`. Re-measured on the shipped
bundle, per channel, as *(display-linear roof pixels) / (effective albedo out of the GLB)*:

| | R | G | B | R/B |
|---|---|---|---|---|
| `ow_f2_tiles` eff albedo, shipped GLB (`glb_albedo.py`) | .0107 | .0177 | .0306 | 0.35 |
| roof declared box, meadow plate, display-linear (`matclass.py`) | .0969 | .0987 | .1141 | 0.85 |
| **transfer D/a** | **9.06** | **5.58** | **3.73** | **2.43** |

So an albedo authored 2.9x blue-over-red arrives on screen 1.2x **red**-over-blue. That is the
whole reason a cool neutral is not the cool sector, and it means the palette entry has to be
pushed far further blue in LINEAR terms than the on-screen target looks: `ROOF_HEX`
`374c81 → 2d4db1`, solved backwards through that transfer at held frame value.

The transfer is a **local** linearisation and must be re-measured every time the albedo moves
far. A two-point fit across the r13 and r14 bundles returns a *negative* blue transfer — not a
physical impossibility but proof the chain is not a per-channel gain: the grade's warm-family
selector (`wp`, gated on the pixel's own `wrm`) fired on r13's terracotta roof and does not
fire on a cool one, so the two bundles were not graded by the same function.

### R-B AND HSV SATURATION ARE THE SAME NUMBER, so this round's two targets are one target

For a blue-grey (B the max channel, R the min), `R-B ≡ -sat × max`. Checked to three places on
both frames: reference roof .446 × .344 = .154 against a measured R-B of −.153; ours
.076 × .372 = .0283 against −.0280. It is an identity, not a fit. Therefore

    roof-wall warm-cool  =  -(sat_roof × max_roof)  -  (R-B)_wall

and **with the wall held, raising roof chroma can only drive warm-cool further negative.** The
brief's prediction was that the two would relax together; they cannot. The reference reaches
−0.076 *at* sat 0.457 only because **its wall is cool too** (R-B −0.082, hue 223 — a stone
windmill, not plaster). Ours is a warm tan at +0.231. Closing warm-cool from the roof is
arithmetically impossible; closing it at all needs the wall at R-B −0.095, i.e. a cool grey
village. **That is an art-direction call, not a knob**, and it is left open.

### THE CLASSIFIER WAS DELETING THE CLASS IT MEASURES

`matclass.py`'s water exclusion — loosened in `13cd671` to `b max & chroma > 0.20` because
r13's version deleted the *reference's* slate — did the same thing to **our** slate the moment
the slate became slate. On the 2d4db1 plate it took **36% of the roof boxes' pixels**, and it
took the bluest ones:

| roof declared box, meadow | pixels | HSV sat | R-B |
|---|---|---|---|
| 374c81 plate, rule ON (as reported in `13cd671`) | 58 753 | 0.076 | −.028 |
| 374c81 plate, rule OFF | 62 893 | **0.114** | −.044 |
| 2d4db1 plate, rule ON | 40 450 | 0.165 | −.067 |
| 2d4db1 plate, rule OFF | 63 223 | **0.309** | −.149 |

So `13cd671`'s "5.9x under the reference" was partly the instrument. Fixed on the **axis, not
the threshold**: our river is CYAN (g sits on top of b), slate is BLUE (g near r). `cy =
(g−r)/(b−r)` measures where g falls on the r→b span — our river 1.02, the reference's river
0.68, our roof 0.24, the reference's slate 0.26, the reference's stone tower 0.27. The rule now
also requires `cy > 0.55`. The reference's own numbers move slightly and in the same direction
(roof sat .446 → **.457**, warm-cool −.071 → **−.076**, value ratio .826 → **.823**): it was
being biased too, by 13% of its roof box. **A classifier that deletes the class it is measuring
reports the absence it caused** — the same shape as walk_engine_gate and `_court_probe`.

### Measured, meadow plate, before → after (all on the FIXED classifier)

| | before (`13cd671`) | after (`2d4db1`) | reference |
|---|---|---|---|
| roof HSV saturation | 0.114 | **0.309** | 0.457 |
| roof absolute chroma (max−min) | 0.044 | **0.149** | 0.154 |
| roof-wall warm-cool | −0.276 | **−0.375** | −0.076 |
| roof/wall value ratio | 0.839 | 0.852 | 0.823 |
| framespread circular R | 0.638 | **0.363** | 0.493 |
| framespread CB 210-240 share | 9% | **24%** | 21% |
| framespread sectors ≥8% | 4 | 4 | 4 |

**The roof-saturation gap is 0.309 against 0.457 and it is OPEN — but it is now a VALUE gap,
not a chroma gap.** Absolute chroma is matched (0.149 against 0.154). Saturation is
`chroma / max`, and our roof sits at max 0.480 where the reference's sits at 0.344: our whole
built palette renders about 1.5x brighter than the reference's (wall L 0.423 against 0.280).
Bringing sat to 0.457 at matched chroma would mean darkening the roof ~30% — which moves the
value ratio this round is forbidden to touch, and to keep the ratio the wall would have to
darken with it. **The residue is an exposure question for the pipeline lane, not an albedo
question for this one.** Recorded here so the next round does not spend another pass pushing a
palette entry at it.

Frame hue spread has now gone slightly PAST the reference (circular R 0.363 against 0.493) and
the reason is the same warm wall: we carry a loud warm sector (R 0-30 at 29%) *and* a loud cool
one (CB at 24%), where the reference carries green-dominant with a cool second and only 8% warm.

Gates: `walk_engine_gate ow-valley` GREEN (0 lost cells, BVH 0 FAIL), `slice_test` 848/0,
`valley_verify` OK. The change is vertex-colour/palette only — no triangle, material or object
moved.

---

## Round 14 — the grade's missing half, and a metric satisfied by the wrong object

**THE GRADE ONLY EVER HAD ITS WARM HALF WRITTEN.** R6 gated the warm push on `litK` and left shade
at `vec3(1.0)`; the only cool term rides depth. **Eight rounds of warming the light and doing
nothing whatsoever to the shade.** Fixed with a luminance-normalised (1.0000 Rec.709) cool push,
steered off vegetation by r13's own yellow selector because the references' shaded grass (99°) and
shaded stone (217°) are 110° apart. Key:fill 2.40/0.95 → 3.00/0.55, **ratio 7.6 → 17.5**, and the
sweep's own lesson: **cutting the fill works, raising the key clips.**

That is the seventh thing in three nights that was disconnected or half-connected rather than
mistuned, after the window `use_vcol`, the campfire emissive, the depth-ramp range, the haze
colour space, the ground-albedo blue, and the playtest finish line.

**AND THE CLASSIFIER WAS DELETING THE SIGNAL IT WAS BUILT TO MEASURE:** it inherited r13's water
rule and dropped **36% of the roof pixels — the bluest ones — the moment slate became slate.**
Fixed on `(g−r)/(b−r)`. An instrument that silently discards its own subject is worse than no
instrument, because it reports a clean table.

**`framespread`, the round's new instrument, earns its place by refusing the value ladder as
evidence.** r13's meadow 5–95 luminance range was **0.559** against the references' 0.523/0.442,
its IQR wider than both, its local contrast between them — **by every value statistic the frame
was not flat, and it plainly looked flat.** The number that agrees with the eye is hue:
chroma-weighted circular **R 0.872** vs their 0.631/0.493, with three ADJACENT 30° sectors holding
95% of the frame's chroma. That is "a narrow band of warm beige-green" as a number.

| | r13 | r14 | ref 3 |
|---|---|---|---|
| roof/wall value ratio | 1.14 | **0.85** | 0.82 |
| roof lit→shade L | .700→.316 | **.475→.222** | .488→.228 |
| roof HSV sat | 0.114 | **0.309** | 0.457 |
| meadow circular R | 0.872 | **0.541** | 0.493 / 0.631 |

**THE BLACK SLIVERS ARE GONE, third round named:** inverted lattice cells (0.99·STEP jitter letting
neighbours cross over), **2648/22995 → 0**, with a build-time census that raises. **The contact
shadow was never missing** — it was a CIRCLE, darkening the ground 41% and still unread; stretched
2.1x along the sun's bearing. **The water's ratified depth→alpha DID port** (bed present at 85/85
stations); what was fighting it was a 31% albedo chroma cut plus a 20% cyan pull left on top.

### AND THE ROOFS WENT BLUE TO BUY A COOL SECTOR THE REFERENCES GET FROM AIR

`framespread` wanted a cool sector. The roofs were the only object available to supply one. The
metric went green. **The blind critic, asked only whether the roof colour works:**

> *"Be blunt: it is **the single worst decision in A**. Two materials could justify a blue roof:
> slate, which is desaturated grey-blue and DARK; or glazed ceramic tile, which is saturated but
> then demands specular highlights and per-tile variation. A's roofs have neither… blue-violet is
> the complement of both the ochre walls and the olive ground, so every roof is doing maximum
> simultaneous contrast against everything it touches, at close range, on ten objects at once. The
> roofs read as **stickers laid over the landscape** rather than as objects in it."*

**Verified in the reference itself: ref 3's cool 21% is the river, the mist banks, the far
mountains and the sky. The windmill's roof is dark grey-brown and every building is warm stone.
There are no blue roofs.** The critic's own cool-source census across the four frames:

  * **A: the roofs** — manufactured props, near field. Secondary: the teal river.
  * **B: distant hill bands, sky, blue fill in the cliff's shadow faces** — atmospheric.
  * **C: the ocean, the blue-violet far cliffs, the cave glow** — water and air.
  * **D: the river, the mist banks, the far mountains, the sky** — purely atmospheric.

> *"A gets its coolness from painted objects in the near field, **which inverts aerial perspective**
> — near should be warm and saturated, far should be cool and pale. A puts its coolest, most
> saturated pixels closest to camera, and that is **the mechanical reason the frame feels flat**
> despite having plenty of depth cues available."*

**THE RULE THIS ROUND BUYS, and it is not the same as round 13's.** R13's lesson was that a
statistic constrains a DISTRIBUTION and says nothing about the relationships in the frame. This
one is sharper: **a histogram does not care WHICH OBJECT supplies a bin.** `framespread` is a good
instrument and stays — but a metric that counts pixels by colour can always be satisfied by
painting the wrong thing, and the cheapest object to paint is rarely the right one. When a metric
goes green, ask which object moved it.

**And the sky is the real answer, which the round found and could not spend.** The critic's sky
census: **A ~2%, B ~5%, C ~15%, D ~25% with structured cloud** — and of A: *"the frame carries
crisp directional shadows and a warm key. **Nothing visible justifies that light.**"* r14's own
report reached it independently: *"the meadow has no sky… structurally the camera pitch — which
the user opened and no lane took."* **Fourteen rounds treated the camera as fixed when the user had
explicitly opened pitch, height and horizon** (distance is the part that is fixed). Round 15 takes
it, under the user's own constraint that the player keeps a wide view of the ground.

**Honest costs.** Meadow under L 0.10 went **1.26% → 2.02%** against the references' 0.00/0.03% —
the black point got WORSE, and it was reported rather than buried. The critic's read of the same
axis: *"saturation has overshot; value contrast is still short — the darks are muddy grey-brown
rather than deep."* Both are true and the fix is more range WITHIN the shadows with fewer pixels at
the floor, which is not more crushing. Ochre as a second rock tone made the cliff worse (hue SD
13.4 → 11.5°) and was kept out.

**One act of judgment worth recording as precedent:** commit `2d4db1` hit the reference's absolute
roof chroma almost exactly (0.149 vs 0.154) and produced cobalt roofs, circular R 0.363, PAST both
references. The builder looked at it, called it wrong, and shipped at 40% back. **The picture
refused the number, on the builder's own work, unprompted.** That is the standard.

Gates: `playthrough_test` 86/0 · `cine_test` 689/0 · `slice_test` 848/0 · `findability_test` 69/0 ·
`walk_engine_gate ow-valley` GREEN.

---

## FOLIAGE ROUND 1 — the near-field "grass" was never the carpet, and the sheen was never specular

Plates `f1-{meadow,gate,vista,gorge,closeup}.png`, crops `f1-crops/`. A NEW LOOP: the user
re-scoped the gauntlet to ONE subject, vegetation, after a foliage-only blind critic ranked
**r3 above both r14 plates** and wrote the thesis this round is built on:

> *"The references' vegetation is a POPULATION OF INDIVIDUAL CLUMPED PLANTS that breaks every
> silhouette and every seam, and ours is a SURFACE TREATMENT APPLIED TO TERRAIN — which is why
> nothing of ours reads as growing anywhere."*

The user's ruling on round 4's reversal: **the MATERIAL was right, the SCALE was wrong.**

### THE OBJECT THE CRITIC WAS JUDGING WAS NOT THE OBJECT WE HAD BEEN TUNING

Before anything was changed, every foliage class was hidden one at a time at the low camera
(`scratchpad/f1/id-*.png`). **The pale spiked clumps that fill the near field — the ones read
as "our grass" for four rounds — are `ow_f2_tuft`, 108 744 static triangles in the bundle, and
they read as AGAVE.** The runtime blade carpet was underneath them the whole time at 173 423
blades of 0.085–0.235 m — ankle height on a 1.45u character — contributing a fine grain you
have to be told to look for. Round 6 halved that carpet for reading "enormous" and the halving
was measured and correct; what nobody checked is that **the object the complaint was about was
a different mesh.** LOOP.md r14's rule, arriving from the other side: when a metric goes green
ask which object moved it — and when a critique goes red, ask which object drew it.

### AND THE WET-PLASTIC SHEEN IS NOT SPECULAR, MEASURED BEFORE THE SWEEP

`envMapIntensity = 0` on EVERY foliage material moves the bush box by **0.1/255** and the tuft
field by **0.4/255**. Every foliage material was already at roughness 0.92–0.95 with metalness
0. There is no specular term in this frame to turn down. The "wet plastic" read is a PALE,
NARROW-HUE albedo with a near-black interior under a warm key — so the material work became a
translucency term, a highlight DESATURATION, and an albedo value→hue remap, and the specular
knob was left alone. **Eighth disconnected knob in four nights, and the first one caught before
a lane spent a round sweeping it.**

### WHAT SHIPPED (public/js/ow_detail.js, rewritten)

  * **TUFTS, NOT BLADES.** 3–7 blades per root point inside a 7 cm disc, sharing the tuft's
    height scale, hue draw and species. A blade placed independently per triangle is an even
    lawn whatever the density field does, because the eye reads ROOT SPACING.
  * **THREE BLADE VARIANTS** (short/broad, medium, seed-head) mixed per clump, 0.65–1.35 width
    jitter, half that on height, full yaw. `hMin/hMax` 0.115/0.335 — knee, not waist, not ankle.
  * **A BASE-TO-TIP HUE RAMP IN THE VERTEX COLOUR**, deep cool green at the root to warm yellow
    at the tip, so one clump carries hue variation before any per-instance jitter.
  * **THE FRINGE IS A DISTANCE FIELD.** Every non-turf surface (road, dock path, water, terrain
    rock, stone/planks/plaster/tiles/tar, bark, bush cores) is rasterised once into a 0.6 m
    occupancy grid and chamfer-transformed: 166 560 cells, 70 864 occupied, **33 ms, once**.
    Density ×2.6 and height ×1.22 inside a 1.3 m band; 30% of the band's tufts are pushed OUT
    along the field's own gradient so they stand IN the dirt, short, with 2 blades.
  * **BARE EARTH BY THRESHOLD, NOT BY THINNING.** The clump noise is thresholded at 0.36 — below
    it the density is zero, not small. A field that only thins still covers everything.
  * **VEGETATION ON THE DRY SLOPES** (the terrain's second primitive) at 0.48x with an ochre
    tint, plus a 20% dry share on the turf itself — most of the "references are 15–25% non-green".
  * **FLOWERS**, three species (white / yellow / pink-lavender) in patches, biased into the
    fringe band, ~550 heads in the near disc.
  * **ONE SHARED FOLIAGE SHADER**: leaf translucency hooked INSIDE `lights_fragment_begin` (so
    it carries the shadow factor — a leaf in shade must not glow), a highlight DESATURATION
    toward the pixel's own luminance, and an albedo value→hue remap on this lane's materials only.

### THREE DEFECTS THE PLATES FOUND, EACH ONE A RULE

  * **A TUFT MAY NOT BE BORN INSIDE THE THING IT IS FRINGING.** The turf primitive runs UNDER
    the road ribbon, so every road cell was a grass cell that also scored the maximum fringe
    multiplier: the first plate had grass growing out of the middle of the path at 3.6x the
    meadow's density and it read as **straw confetti scattered across the whole path.**
  * **...AND "OCCUPIED" AND "IMPASSABLE" ARE NOT THE SAME SET.** Refusing a tuft in any occupied
    cell dropped the closeup from **208 055 blades to 67 095** — `ow_f2_ter_rock` and the bush
    cores are terrain SLOTS that interleave with turf across most of the meadow. A rock outcrop
    is something grass grows AGAINST (must fringe) and also BETWEEN (must not refuse). A paved
    road is neither. Two sets, one grid: `D` for distance, `HD` for refusal.
  * **A DESATURATOR WIDE ENOUGH TO CATCH EVERY LIT PIXEL IS A CHROMA CUT ON THE FRAME.** The
    highlight clamp's threshold is in PRE-TONEMAP LINEAR and the first guess was half a crown
    too low: on the meadow's crown box, saturation **0.326 (term off) → 0.243 at 0.45/1.00 →
    0.296 at 0.80/1.60**. Round 13's overshoot in miniature, caught in one round.

### A CORRECTION TO THIS ROUND'S OWN MEASUREMENT, worth more than the numbers

The first canopy A/B said my material patch lifted the crown L50 **0.550 → 0.737**. With every
term I added switched off it was still **0.714**. The cause was not in my code at all: the
parallel TREE lane re-exported `public/assets/scenes/ow-valley/scene.glb` and regenerated the
canopy atlas **between my BEFORE capture and my AFTER capture.** My patch accounts for 0.023 of
that lift, not 0.164. **A BEFORE PLATE IS ONLY A BEFORE PLATE IF THE BUNDLE UNDER IT HAS NOT
MOVED** — with two lanes on one branch the baseline must be shot from the SAME tree, which is
what `?owdetail=0` is for and what the shipped f0/f1 pair now uses.

### MEASURED

Near-band saturation, box x 0.35–0.95 / y 0.72–0.98 of frame (clear of the references' HUD);
r3 in the same box reads **0.651**, which is round 4's overshoot in this box's units:

| | ref 1 | ref 2 | ref 3 | meadow | gate | vista | gorge | closeup |
|---|---|---|---|---|---|---|---|---|
| f0 (`?owdetail=0`) | — | — | — | 0.357 | 0.411 | 0.417 | 0.353 | 0.334 |
| **f1** | **0.428** | **0.598** | **0.333** | **0.421** | **0.443** | **0.444** | **0.383** | **0.368** |

**We are UNDER the references, not over** — the round-4 fear did not materialise, and there is
headroom left rather than an overshoot to walk back.

Cost, closeup camera: scatter **173 423 blades / 1 040 538 tris / 1 draw → 175 603 blades +
flowers / 1 186 422 tris / 4 draws** (+14% triangles, +3 calls). Whole scene per render call
**87 820 tris / 6.73 calls** with the module off → **195 677 / 7.09** with it on. Rebuild 91–113 ms,
at most every 700 ms and only after the player moves 9 m. Headless rAF is clamped at ~120 in
both configurations and therefore **cannot** discriminate frame cost; do not quote an fps from it.

Gates: `slice_test` 848/0 · `cine_test` 689/0 · `findability_test` 69/0 · `walk_engine_gate
ow-valley` **GREEN (0 lost cells, BVH 0 FAIL)**.

### CARRIED, NAMED

  * **ITEM 5, THE BUSHES, IS NOT DONE AND WAS DEFERRED ON PURPOSE.** They are still cards, not
    hemispherical hulls. `tools/bushlang.py` was being edited by the TREE lane in the same
    window, and a second lane rebuilding the same builder is how a branch goes red. What they
    did get is the shared material: the closeup bush box went L50 **0.225 → 0.408** (the
    near-black core lifted) at saturation **0.406 → 0.464**.
  * **`ow_f2_tuft` IS DITHERED, NOT FIXED.** The bundle's agave clumps are hashed out over
    20–66 m and stand beyond it. It is a stopgap for an asset this lane could not rebuild.
  * **THE FAR FIELD IS TONE, NOT GRAIN.** At boom 40 (vista) the scatter is invisible past
    ~74 m and the terrain reads smooth. The references carry "directional grain" at that
    distance and we do not.
  * **The grass/dry terrain SLOT boundary is a polygon edge** and became visible the moment
    only one slot had plants on it. Raising the dry slope's density to 0.48x hides it; it is
    not solved.
  * Item 6's second tree species and the plateau scale ramp: NOT TRIED, ran out of round.

### THE "VEGETATION IS NOT TAKING THE SUN" LEAD IS REFUTED AS A WIRING CLAIM — AND THE PICTURE IS STILL RIGHT

A clean blind critique of the gorge frame called it the highest-value change in that shot:
*"the big cast shadow crossing the lower meadow darkens the ground but NOT the bushes standing
in it — the vegetation is not taking the sun at all."* **Checked before changing anything, and
the wire is connected three ways** (`scratchpad/f1/spec-shadow.json`, gorge camera, the SAME
pixels with `R.shadowMap.enabled` toggled):

  * **The flags are all true.** play3d.html:2991 gives every mesh in the bundle
    `castShadow = receiveShadow = true`; queried live, `ow_valley_bushcore`, `ow_valley_bushcard`,
    `ow_f2_canopy` and `ow_f2_tuft` all come back `recv:true cast:true`, emissive `000000`,
    emissiveIntensity 1. (The runtime scatter is `recv:true cast:false` — deliberate and
    documented: 175k instances in the depth pass buys shadows nothing resolves at 3-8 px.)
  * **Foliage moves MORE than the ground when the shadow map is removed**, not less: mean
    |delta| **37.9/255 on green pixels against 14.2 on everything else**; green is 16.1% of the
    frame and **27.2%** of the pixels the shadow map darkens.
  * **The lit:shadow ratio is the same on both.** On the pixels the sun's shadow demonstrably
    darkens: foliage **141.1 -> 60.1 (2.35)**, everything else **122.8 -> 50.8 (2.42)**.

**The judge's perception is honest and its named mechanism is wrong.** What is missing is not
the shadow the world casts ONTO a bush, it is the shadow a bush casts ON ITSELF: the cores'
normals are blended toward the hemisphere so a bush has no lit side and no shade side, its base
is not its darkest value, and it sits ON the terrain instead of into it. That is **item 5 of the
foliage brief verbatim**, deferred this round because `tools/bushlang.py` was open in the TREE
lane. Queue it there, not as a shadow flag.

### AND THE SHARED MATERIAL DOES NOT MOVE THE HERO CANOPY

Asked by the coordinator after the tree lane solved `EXPOSURE = 0.80` against today's material.
Meadow crown box, current tree, my terms toggled live: all off **L50 0.592 / sat 0.296 / L95
0.762**, shipped **0.604 / 0.295 / 0.771**. Translucency contributes +0.012 of L50; **the
highlight desaturation never fires on it at all** at hiA 0.85. No reconcile needed.

---

## FOLIAGE ROUND 2 — the density never collapsed; one blade was thinner than one pixel

Plates `f2-{closeup,meadow,gate,vista,gorge}.png`. A genuinely blind judge (anonymised
frames, no labels, no history) ranked our new LOW camera **last of six** — *"essentially
unfinished... the hillside is bare terrain texture with roughly eight isolated sprigs at
regular spacing"* — while ranking the same build's MEADOW frame **above** the old build.
The population treatment worked at boom 40 and collapsed at the grazing camera.

### THE FALLOFF WAS NOT THE DEFECT, AND THE WIRE SAID SO BEFORE ANY CODE MOVED

`scratchpad/f2/probe2.js`: 1 840 screen rays cast at the ground **in the running game** from
the real closeup camera (measured at 7.25 m behind the player, 2.25 m above it, pitch 0.18),
each hit re-evaluating the scatter's own `want` product term by term from the module's own
live parameters. Per 10 m band of camera distance:

| dCam | 0-10 | 10-20 | 20-30 | 30-40 | 40-50 | 50-60 |
|---|---|---|---|---|---|---|
| live roots/m2 | 3.49 | 8.12 | 4.38 | 4.52 | 4.52 | 5.87 |
| mean spacing (m) | 0.63 | 0.41 | 0.62 | 0.56 | 0.63 | 0.48 |
| blade height (px) | 28.1 | 19.6 | 11.2 | 7.9 | 6.6 | 5.5 |
| **blade WIDTH (px)** | **5.11** | **3.52** | **1.94** | **1.33** | **1.08** | **0.87** |

**Root density never collapses.** It holds at ~4.5/m2 and 0.6 m spacing across the entire
failing band, and `fall` is only down to 0.56 at 40 m. 10 600 blade roots stood inside the
region the judge called bare, and 21 775 were on screen. What collapses is **the width of one
blade**: 3.6 cm of grass is 5.1 px at the player's feet and 1.1 px at 40 m, and a blade
thinner than a pixel does not half-cover that pixel — it wins the sample or it vanishes. Past
~30 m the whole population was rendering as an aliased stipple over the terrain texture.

**A FIELD CAN BE FULLY POPULATED AND COMPLETELY INVISIBLE.** Every instrument this lane had
counted plants; the judge was reading COVERAGE. Adding roots to a sub-pixel population buys
nothing — the cheap fix the judge offered blind ("scatter the existing tuft asset with density
from noise and slope") would have cost triangles and moved the picture barely at all.

So the mid band is bought with coverage PER PLANT: `wgrow` widens a blade with distance so its
apparent width holds near two pixels, paid for out of blade COUNT (`farThin` 0.62 -> 0.72).
Ordinary grass LOD, and self-limiting — a blade at 60 m scaled 2.3x subtends the same two
pixels a near blade does. The near field is untouched by construction (gain is 1 inside r0),
so r3's "field of corn" cannot return through this door. **The gain goes on local X ALONE:**
`bladeGeo` puts width on x and `bend*t*t` on z, so scaling both lays every far blade flat.

### THE OTHER FOUR, EACH A WIRING FACT

  * **THE RECTANGLE BOUNDARY IS A MATERIAL SLOT.** The terrain is ONE mesh with per-face
    material slots (`overworld3_build.py:306`), so the grass/dry line is a chain of triangle
    edges — dead straight, through open ground. r1 put a CONSTANT 0.48x density on the dry
    slot, laying a 2x density step exactly along it. Both slots now draw their weight from the
    same range and a rotated noise field (`slotAt`), not the polygon, says where in that range
    a spot lands. **The slot still decides the TINT; it no longer decides the COUNT.**
  * **THE PATH SHOULDER WAS QUANTISED TO A TRIANGLE.** `occHard` was asked once at the
    triangle CENTROID, and terrain triangles are metres across: a triangle centred on the road
    contributed nothing, one centred beside it scattered blades across the paving. That is a
    ~2.5 m ragged edge on the one seam the player stands closest to. The refusal is now
    repeated PER BLADE at the grid's own 0.6 m, with strays exempt.
  * **THE HOUSE PADS WERE NOT IN THE CHAMFER FIELD AT ALL.** `trodden_ring` lays its wear ring
    with class DIRT (`valley_build.py:1076`), and `overworld3_build`'s class->material map has
    no DIRT entry, so it falls through `group.get(int(c), "matte")` to **`ow_f2_matte`** —
    which was absent from `OCC_MATS`. Five pads, five hard unfringed seams, exactly as read
    blind. Proof it is now wired: field triangles **74 150 -> 75 422 (+1 272, the matte count
    to the triangle)**, hard cells 15 213 -> 15 377.
  * **THE FLOWERS EXISTED AND WERE SPENT WHERE THEY COULD NOT BE SEEN.** 793 heads in the
    disc, **12 on screen**. `flPer` is a per-tuft probability and tuft count grows as the
    ANNULUS AREA, so 62% of them landed 30-50 m out where a 6 cm head is 2 px; and
    `vs.set(1, fh, 1)` scaled Y only, so a flower was the one thing in the frame with no size
    compensation at all. `flNear` pulls them in, and the head now takes the blades' width gain.

### AND ONE KNOB THAT WAS NOT WIRED TO WHAT I WANTED — CAUGHT BY LOOKING

The dry slope's plants were ochre on sand: no contrast, which is why they read as "bare
terrain" even where they stood. I cut the dry share on the dry slot (`dryOnDry` 0.55 -> 0.34)
and **the slope got fainter, not greener.** A tuft takes its base colour from the COLOR_0 of
the ground UNDER it (deliberate — the scatter must never be a different green from its own
ground), so on the dry slot a "not dry" tuft is not green, it is PALE SAND. I had traded
ochre-on-sand for sand-on-sand. The fix is an explicit `grassOnDry` tint, so the worn slope
carries plants that DISAGREE with it. **The proxy would have called the first version a
success — only the picture said otherwise.**

### A STALE BEFORE PLATE, FOR THE SECOND ROUND RUNNING

The first f1-vs-f2 sheet showed the cliffs recoloured and a whole wooden scaffold appearing in
the gorge. None of it was mine: `scene.glb` was rewritten at **12:41** and `f1-closeup.png`
was shot at **12:01**. r1 wrote this rule down and this round still had to pay it once.
The A/B below is r1's module against r2's module on **one tree**, captured by swapping
`public/js/ow_detail.js` in place between two runs of the same spec.

### COST (true A/B, same bundle, closeup camera)

| | blades | scatter tris | draws | rebuild |
|---|---|---|---|---|
| r1 | 179 359 | 1 211 856 | 4 | 103.7 ms |
| **r2** | **119 170** | **807 762** | **4** | **66.4 ms** |

**-34% triangles and -36% rebuild time for more visible cover** — the width gain is paid for
by `farThin`, and the per-blade `occHard` deletes the blades that were being drawn inside the
road. Flowers 793 -> 1 264 heads. Gates: playthrough_test, slice_test (848), cine_test (689),
findability_test (69/0), walk_engine_gate ow-valley.

### STILL OPEN

  * The near field still reads slightly broad ("corn") at the grazing camera — improved by the
    height-distribution widening (`hPow` 1.85 -> 1.40, whose old mass sat on top of `hMin`)
    but not solved.
  * The judge's ceiling warning stands and is now measured from the inside: **one tuft asset
    at one hue cannot carry a hillside.** The dry slope is carried by a tint multiplier on the
    same three blade shapes. Two more ground assets and a real flower are the next honest step.
  * `ow_f2_tuft` (bundle, not this lane's) is dithered out from 20 m and returns at FULL
    strength beyond 66 m — so the far ridge is still carried by a regularly-placed asset.

---

## TREES r2 (t2) — the sun was never wired, and the bush in the frame was not the bush with the name

Plates `docs/qa/ow-refs/plates/t2-{meadow,gate,vista,gorge,closeup}.png`, crops in
`t2-crops/` (all before/after against the f2 build, TOP = f2, BOTTOM = t2).
Scene 325 406 -> 333 677 tris (+8 271, +2.5%). cine 689/0, slice 848/0,
findability 69/0, walk_engine_gate ow-valley GREEN (0 cells lost).

**THE RIDGE CONTRADICTION: THE BLIND JUDGE WAS RIGHT, AND MY ROUND-1 REPORT WAS TRUE.**
Both, and that is the finding. `tree_e`, the 0.68-1.58 ramp and the keep-out jitter all
LANDED — `MEADOW_CFG` is wired through `O3.TREE_FN["e"]`, the build plants 17 of them,
and the size spread is plainly visible in `t1-gorge`. So the judge's literal words
("same size, same rotation") are false. But its headline was right, because **the repeat
it names is a repeat of FORM, and no scatter knob addresses form**: both field species
hung ONE ball clear of a BARE VERTICAL STICK. tree_a's crown bottom sat at z+1.33 s over
a trunk running to z+1.55 s — 86% of the trunk uncovered on every instance at every
scale. Scaling a lollipop gives a bigger lollipop. Fixed in the SHAPE (per-instance trunk
height + a skirt of 1-3 low lobes that brings foliage down over the trunk), not the
scatter. `t2-crops/gorge-ridge.png`: the stick is gone and no two outlines match.
*A dead end worth recording:* round 1 also added `tree_e` to `overworld3_lib`'s
`FIELD_MIX`/`plant_field`, which builds `ow-proto-*` and NOT `ow-valley` — that half was
always inert. The live path is `valley_build.plant_region`.

**CHARGE 1 WAS AN ABSENCE AT THE WIRE, NOT A LEVEL.** "No lobe is lit and no lobe is
shaded" was literally true: EVERY crown-scale term in `bushlang` was a function of world
up — `shade_core` read `up = N[:,2]`, `_colour` read `nz = N[:,2]` and `_lobe_height`
(a Z gradient by construction). A lobe on the sun side and one on the shade side got
IDENTICAL colour at every scale. There was no lateral gradient to sweep. `SUN_TO` is now
DERIVED from the ratified rig (Blender euler 56/0/212 -> toward-sun (-0.439, 0.703,
0.559), elevation 34.0 deg — the same 34-degree sun every shadow note in `valley_build`
is written against) and applied at two scales: local normal (per-lobe form) and position
along the sun axis normalised over the mass's own extent (the crown-scale ramp). It takes
a SHARE of the existing lift rather than stacking, so the mean holds and only the
distribution moves. `Mass(sun_scope=)` exists because the crown ramp normalises over the
mass extent: correct for one forest mass, a tile-wide vignette for a batch of bushes.

**THE PALE STREAKS ARE DIAGNOSED, AND THE COMMENT THAT NAMED THEM WAS WRONG.**
`bushlang.py`'s own CORE_UV block blamed the core's planar UV projection. Measured and
refuted: hide the core, streaks unchanged; hide the CARDS, streaks GONE. Per-triangle UV
anisotropy out of the shipped GLB is core median 1.14 / max 1.70 against cards exactly
1.000 — dominant-axis planar projection is bounded at sqrt(3) BY CONSTRUCTION, so the
claimed smear cannot happen. Filtering excluded (LinearFilter, anisotropy 16: no change).
Culling `|N.view| < 0.45` removes 14 283 of 33 333 cards and most of the streaks; a
streak is 85-130 px = one BIG card. **They are big shell cards seen near edge-on**, made
pale because `NZ_HI` made those same up-facing cards the brightest in the mass. That is
also the other half of charge 1 — "the canopy's brightest pixels are scattered" — and no
crown-scale gradient can read through a field of bright slivers. BETA_MAX 56 -> 46 deg
and NZ_HI 0.42 -> 0.22 cut them materially; they are reduced, not gone.
**The wrong comment cost a diagnostic hour.** Documentation bar, paid in full: an
interpretation may only be recorded beside the instrument that proved it.

**THE BUSH ITEM: I ALMOST FIXED THE WRONG OBJECT.** The brief routed bushes to
`bushlang.py` and `overworld3_lib.shrub_a`. Both were real and both were rebuilt —
`shrub_a`'s two flat-coloured ellipsoids became one bushlang mass (lobed core, culled
interior, card shell, dark base, sunk by `BUSH_SINK`). Then, measured in the running
game: **only THREE `veg_bush` vertices lie within 45 m of any of the five fixed views.**
`veg_bush` is almost entirely the west forestwall, off camera. What is in frame at every
one of those views — and therefore what every "pancake disc / floating / still looks lit"
critique has actually been about — is **`veg_land_clumps`**, from `valley_land.py`.
Its mechanism was in `_emit`: `C[o:o+npv] = row["c"]`, ONE FLAT COLOUR on every vertex of
the clump, so a convex solid under one directional light had no dark side and no dark
underside; and its base sat at exactly y = 0, tangent to the terrain, which is the
floating read. Now a per-vertex `gshade` (darkest at the base, plus the same derived sun)
and `CLUMP_SINK`. **FIND THE OBJECT THAT IS IN THE FRAME BEFORE FIXING THE OBJECT THAT
HAS THE RIGHT NAME** — a fix aimed only at `shrub_a` would have been invisible in the
very pictures it was judged on.

**Gorge shade band (coordinator's item 5):** `t2-crops/bush-shade.png`. The shaded clumps
keep a readable green value with visible form and do not collapse into holes; the value
floor holds. Honest limit: they are still bright faceted low-poly solids, which is the
declared style, and the in-shade improvement is real but modest.

---

## FOLIAGE ROUND 3 (f3) — two species arrive, and the cones were never ours

Plates `docs/qa/ow-refs/plates/f3-{closeup,meadow,gate,vista,gorge}.png`, crops in `f3-crops/`.
Gates: **playthrough_test 86/0**, slice 848/0, cine 689/0 (2 soft), findability 69/0 (2 warn),
walk_engine_gate ow-valley GREEN (0 cells lost, 0 extra, height agreement median 0.000 m).

**THE A/B IS MODULE-AGAINST-MODULE ON ONE BUNDLE, AND THIS ROUND HAD TO EARN IT TWICE.**
r1 wrote the stale-before-plate rule, r2 paid it again, and the f3 lane inherited five plates
whose timestamps STRADDLED a `scene.glb` write (closeup 14:19:42, meadow :46, **glb rewritten
:48**, gate :49, vista :52, gorge :55) — a sheet where two frames judge one bundle and three
judge another. They were discarded. The bundle then moved AGAIN mid-probe
(`184b4bf7` -> `621effe4`) while the tree lane re-exported. So the shipped comparison is the
committed `ow_detail.js` against the working one, swapped in place between two runs of the same
spec, on **one digest verified identical either side of both runs** (`621effe4`). The rule that
keeps costing rounds is not "re-shoot the before" — it is **PIN THE BUNDLE DIGEST ACROSS THE
RUN AND ASSERT IT, because a neighbour lane's export is not an event your plates can see.**

### THE PALE MINT CONES ARE BUNDLE GEOMETRY, AND THEY ARE THE f2 DEFECT ONE CLASS OVER

The user's "pale mint untextured cones" at the closeup's bottom edge, named by raycasting the
plate's own pixels back through the plate's own camera (`docs/qa/ow-refs/plates/f3-crops/cone_probe.js`):
**`emberbrook_2`, material `ow_f2_matte`, `map=false`, 7.7-9.0 m from camera.** Not the scatter.

They are `valley_build.py:1085` — `p.cone(GRASS_HI, …, seg=4)`, the seven tufts per house that
`trodden_ring` plants to break the base line where wall meets ground. **`GRASS_HI` has no entry
in `overworld3_build.py`'s class->material map** (line 383-387), so `group.get(int(c), "matte")`
falls it through to the untextured `ow_f2_matte` — and `TUFT_TINT = (0.86, 0.94, 0.72)` is then
multiplied onto a material with no texture at all. That is EXACTLY f2's finding
(`DIRT` -> matte, five hard pads) one class over, in the same `.get(..., "matte")` call.
Flat ground classes falling to matte is correct for the bedding DISC; it is wrong for a
four-sided CONE, which has a silhouette and reads as a paper spike.
**HANDED OFF, not fixed** — the fix is a bundle rebuild + export, which is the tree lane's.
Worth noting for whoever takes it: round 3's own `weedFringe` (2.3) now scatters real rosettes
at exactly the house-bedding fringe these seven cones were hand-placed to cover, so *deleting*
them may be the whole fix.

**A RAY CAST THROUGH AN UNCONVERGED CAMERA NAMES THE WRONG OBJECT WITH TOTAL CONFIDENCE.**
The first probe raycast synchronously after `SIM.tick(2)` and every hit came back ~38 m away on
the far side of the valley — the orbit rig converges in the render loop, not in `tick`. The pick
now re-runs on an interval and **the report carries the camera it was cast from**, so a
disagreement with the plate's camera is visible instead of silent.

### THE STRAGGLER LIFT: BOUNDED, AND THE BOUND PROVEN LOAD-BEARING

`occTop` (max height of any HARD triangle in the occupancy cell) lifts a straggler onto the
surface it crossed onto, because a stray takes its y from the TERRAIN triangle it was born on
while every paved surface is proud of that terrain. Unbounded, this teleported tufts onto
ROOFS: `ow_f2_tiles`/`ow_f2_plaster` are in the hard set (a wall footing is a seam), so under a
house the cell's top IS the roof. `strayLift: 0.30` bounds it to surfaces a body could have
stepped onto.

**The bound is not incidental, and a clean roof does not prove it** — so it was falsified on
purpose (`f3-crops/ab-lift.png`, `OWD.set({strayLift:99})` on the meadow camera): tufts and
a flower sit plainly on two roofs at 99, and the roofs are clean at 0.30. Effect sizes, measured
as changed pixels: the lift itself (0 -> 0.30, closeup) **8 649 px, 0.84% of frame, bbox
x 267-739 y 338-721** — the left field and the road shoulder, exactly where it should be;
removing the bound (0.30 -> 99, meadow) **17 518 px, 1.71%, frame-wide**.
Honest limit: at 3x on one road-shoulder crop the clipping fix is **not readable by eye**. It is
a real and correctly-placed 0.84% of the frame, not a picture-level win.

### THE THREE NEW ASSETS, BY EYE AT THE CLOSEUP

`f3-crops/assets-zoom.png` (4x). The weed rosette reads as a BROAD leaf mass, the sedge as
a taller narrow fountain with a dark basal knot, and both are plainly not the blade. The near
field's "corn" read is **reduced, not solved**: `wide` 0.018 -> 0.0138 lands visibly (blades are
thinner and denser than r2's splayed Vs), but the weed's two erect inner leaves are themselves
broad and upright, so the agricultural read has a new contributor even as the old one shrank.

**AND ONE THING IS WORSE, ISOLATED RATHER THAN GUESSED.** A minority of weed rosettes render a
near-BLACK leaf or crown at the closeup. Isolated by toggle, not by reading the source:
the blobs SURVIVE `sedge:0` and VANISH with `weed:0` (`f3-crops/ab-blob.png`), so they are
the weed and not the sedge's dark knot. Mechanism, stated as the hypothesis it is: the material
is `T.DoubleSide` and the outer leaves arc past horizontal (`A1` runs to -0.72 rad), so the
camera sees their UNDERSIDE, whose flipped normal faces away from the sun. Not fixed this round
— the fix lands in the shared foliage shader and would ship unverified. **CARRIED, NAMED.**

### COST (true A/B, same bundle `621effe4`, closeup camera)

| | blades | scatter tris | draws | weeds | sedges | flowers |
|---|---|---|---|---|---|---|
| r2 | 119 170 | 808 848 | 4 | — | — | 1 302 |
| **f3** | **140 381** | **964 794** | **6** | **2 141** | **990** | **1 431** |

**+155 946 tris (+19.3%) and +2 draw calls.** The module comment claiming the two species cost
"roughly no triangles" because they are paid for out of the blades is **WRONG and has been
corrected in place**: the substitution does save, but `tuftDens` 10.5 -> 11.4 in the same round
put 2 586 blades BACK, so the saving never reaches the total. Arithmetic that reconciles it:
weeds 2 141 x 36 + sedges 990 x 48 = 124.6k, extra blades 2 586 x 6 = 15.5k, richer flower head
(6 -> 16 tris) = 15.8k.

### STILL OPEN

  * The dark weed underside (above) — the first f3 item for round 4.
  * `GRASS_HI` -> `ow_f2_matte`: handed to the bundle lane, unfixed here.
  * The near field still reads broad; the weed's erect leaves are now part of that read.
  * `cine_sweep`-style question untouched: the far ridge is still carried by `ow_f2_tuft`.

## TREES r3 (t3) — the trunk that rendered zero pixels, and the teal that was never ours

Plates `docs/qa/ow-refs/plates/t3-{meadow,gate,vista,gorge,closeup}.png`.
Scene 333 373 -> 337 793 tris. playthrough 86/0, walk_engine_gate ow-valley GREEN
(0 cells lost), cine 689/0, slice 848/0, findability 69/0.

**A GATE THAT COUNTS TRIANGLES CANNOT SEE AN INVISIBLE OBJECT.** The inherited
stand-trunk pass built 63 trunks / 4 032 tris, printed them in `valley_build.json`,
and rendered **0 px on all seven judged cameras**. The instrument that found it:
give `veg_canopy_trunks` a flat magenta `MeshBasicMaterial` and count magenta —
and, because a null result must prove it could have found something, the same
marker rendered **1 720 px** with the rest of the scene hidden. Hiding the CARD
shells alone still gave 0, which named the occluder as the lobed CORE.

**AND THE BUILD'S OWN NUMBERS SAID WHY, ONCE ASKED.** `stand_mass` places a lobe at
`cz = gz + h*1.04 - hz`, so `H = cz - gz` is a function of the LOBE and never of
where the ground is. Printed over all 446 lobes of the three stands, the exposure
`bot - gz` runs **p50 -0.85, p90 -0.03, max +0.17** — not one lobe in this region
has half a metre of air beneath it, because the mass is deliberately sunk. A trunk
from that ground to that centre is inside the core for its whole length. The fix is
a different GROUND, not a different trunk: an 8-sample ring at the lobe's own radius,
keep the minimum. That is the crown whose skirt runs out over falling ground, which
is the judges' complaint stated as a measurement.

**THE FIX'S FIRST BUILD SHIPPED A WORSE DEFECT, AND ONLY THE PICTURE HAD IT.** The
ring minimum beyond a gorge-rim lobe is partway down a vertical wall, so trunks stood
against the cliff as pale poles — scaffolding, plainly wrong, and every number was
green (whisperwood exposure max +13.01 m looked like success). Two guards: `TRUNK_MAX`
3.6 (a trunk, not a mast) and `TRUNK_SLOPE` 0.70 (no trunk on a wall). **15 trunks,
420 tris — an eighth of the inherited cost — and vista trunk px 831 -> 14, the
under-canopy camera 12 578 -> 0.** Honest limit: the hero crown at the meadow and
closeup cameras still shows no trunk (89 px / 0 px); this closes the gorge-rim and
farwall cases, not the hero one.

**THE STREAKS: THE SHELL NORMAL IS THE PAYER, MEASURED ON A CLEAN A/B.** Two builds
(twist+normal ON and OFF), one glb swapped under one browser so the shader is
identical on both sides: canopy pixels over L 0.72 **13.58% -> 11.69%**, L50 0.586 ->
0.574. The picture is the verdict and it agrees — the scattered bright slivers become
a lobed mass with dark interstices (`scratchpad/t3ab/zoom-meadow.png`). Real, partial.

**THE CYAN/TEAL IS `ow_detail.js`'s REMAP, AND THE NUMBER IS NOT CLOSE.** Neutralising
the remap's four component knobs takes canopy pixels over L 0.72 from **9.79% to
0.78%** and L50 0.558 -> 0.380, against references that run 1-3% over. Mechanism: this
atlas's albedo in LINEAR space is 0.017-0.20, **entirely below `owdVMid = 0.30`**, so
`tt` clamps at -1 for every texel — a fixed `R x0.835 / B x1.30` hue swing plus a value
lift of up to **5x** on the darkest texels and 1.1x on the brightest, i.e. the
leaf-cluster contrast is crushed ~4.6x. `envMapIntensity = 0` is pixel-identical, which
excludes the IBL. **The remap's own block says it goes "only on the materials this lane
owns, so the tree lane's canopy albedo work cannot be fought over the same pixels" —
and `ow_valley_bushcore`/`ow_valley_bushcard` are in that list.** One-line handoff:
move both to `FOL_SHARED` (ow_detail.js:1373-1375). **`OWD.set({remap: …}) IS A
NO-OP`**: `pushUnis()` pushes every other uniform and not `owdRemap`, so a remap sweep
returns a pixel-identical frame (measured: `M3-remap0` ≡ `M0-base`). A knob that
cannot be swept cost the previous session an experiment.

**OUR HALF OF THE FRINGE, AND IT DID NOT PAY.** `foliage_atlas`'s un-premultiply
divides by `max(a,1e-4)`, so every fully transparent texel stored BLACK — and the GPU
does not respect alpha when it filters, which made the atlas's darkest texels its own
edges, i.e. exactly the input the remap amplifies 5x. `_bleed` pushes the opaque colour
outward (edge-clamped per cell; alpha sum identical, opaque texels identical; mip-2
luminance 0.192 -> 0.198). At the wire it measured **~0** while the remap dominates.
Kept as a no-regression correctness fix, reported as one.

**Shade band (item 4): HOLDS.** Gorge shaded vegetation L p05 0.119 / p50 0.186 / p95
0.356, **0.02% under the 0.06 black point**, chroma 0.115; the deep under-canopy frame
p05 0.110, 0.00% under. No collapse into holes.

Also: the seven `GRASS_HI` wall-line cones per house are DELETED (coordinator's item,
option b) — no class->material entry, so they shipped untextured; the detail lane's
`weedFringe` covers that feature now and the bases still read collared by eye.

### STILL OPEN (trees)
  * The hero crown's own trunk — the whisperwood at the meadow/closeup cameras. Every
    lobe there is sunk into its ground; a trunk there needs a skirt change, not a probe.
  * The remap handoff above. Until it lands, every canopy number in this lane is
    measured through a 5x value lift.
  * `cutin_edge`-class hole in our own gates: nothing here measures HUE, which is why a
    teal canopy passed every tree-lane gate for two rounds.
