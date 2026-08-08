# Emberbrook — context index for Claude sessions

Two-player couch co-op JRPG in the FFIX pre-rendered-background style. This file is the
map of where truth lives. **Read the entries relevant to your task BEFORE designing or
building — sessions lose conversational context at compaction; the repo does not.**
Keep this file current: when you add a system, add its pointer here (one line, same
commit). Sessions may be rooted at ../rpg-3d (a legacy sandbox, NOT a git repo) — all
git runs here, on branch `migration/3d-hybrid`.

## Story & world canon (read before ANY town/character/dialogue design)
- **STORY.md** — the story bible: ten-chapter arc, flame/Heartlight metaphysics, full
  cast, reveal schedule, writers' rules (lore budget: ONE deep fictional system). Not
  final — expect revisions — but town/character design must accommodate it.
- public/js/chapter1.js — Chapter One "Emberwake", SHIPPED content; Emberbrook town
  must stage it. chapter2.js = Dellhollow, chapter3.js = Lanternstead.
- docs/chapter2-script.md — Lanternstead full script. VOICES.md — dialogue voice per
  character.
- **docs/exemplars.md** — the RATIFIED style set: 42 shipped Ch1–Ch2 lines that already
  obey VOICES.md, ~5 per main voice, each with one line on why. Read it before writing
  any dialogue; paste PART 2 as the few-shot block for any generated dialogue (match by
  example, never by describing the style in the abstract). Every quote in it is verbatim
  from the script — change a line there and you owe the same change in the chapter.
  Ch3 is deliberately absent: it is not the house style (user ruling 2026-08-02).
- **docs/plans/end-to-end-wiring.md** — the AUDIT of what stood between three
  scripted chapters and one continuous playthrough (2026-08-02). Its headline finding —
  the chapters lived in the LEGACY 2D runtime (join-legacy.html) — is RESOLVED and that
  runtime is DELETED (Bet 6, 2026-08-05: join-legacy/controller/engine/sprites2/field/
  story/items/assets/main.js, the painted 2D scene bundles, and the phone-controller
  relay in server.js are gone; chapter1/2/3.js survive as INERT script-of-record data —
  see their headers). Still carries the save-state schema, the chapter-handoff
  contract, the story-flag design (`story.ch1.gate-open`), and the measured
  empty-Emberbrook finding. Read before any wiring work.
- **docs/qa/MORNING.md** — TOP SECTION = the 2026-08-07 HANDOVER (current state + the
  measured round-3 worklist; read it first). Below it, the 2026-08-06 brief: THE BAR MET (full NEW GAME
  to the end card, run-20260806-011853), the overworld graphics sweep, the Dellhollow
  phase 7 iterations deep, and what the closing bake lane owes. Read this first.
- **docs/qa/TOMORROW.md** — the 2026-08-03 plan: five tranches, the art calls the user
  DELEGATED to me (Old Gate structure, the bunting post, forest-vs-the-FFIX-refs), what is
  settled and must not be re-asked, and the standing risks. Read it before picking up work.
- **docs/qa/RESUME-LANES.md** — 2026-08-02 ~21:30: the FIVE lanes paused when the account
  moved to a lower tier and work narrowed to deployment. One entry each: what landed, what
  remains, the traps already paid for, and the decisions waiting on the user. Read it before
  restarting any of them.
- **docs/qa/RESUME.md** — WORK PAUSED 2026-08-02: what every lane was mid-way
  through and how to pick it up. Read it before restarting any lane.
- Canon rulings log + nightly state: **docs/qa/DAYLOG.md** (append handover-quality
  notes there after major phases; agent transcripts expire).

## The townmap system (the authoring layer for every town — start here for town work)
- public/townmap/viewer.html?town=<name> — 3D/plan/elevation viewer of a town's map:
  landmarks, path edges, districts, **parcels (each derives a scene contract + sceneKey)**,
  draft camera frustums, live validation. Serve repo /public on a local port.
- public/townmap/<town>.map.json — the landmarks-first town layout: THE design authority
  a town model is built from (Dellhollow was built this way). Emberbrook's carries
  dated REDLINE notes from the user — honor them.
- **A CARRIER, never a rebuild, for a district already dressed:** tools/gate_rimchop.py (the
  rim) and tools/gate_roadchop.py (the ENTRY ROAD — rim + GX0 + SPINE, rebuilding
  gate_ground/gate_road/gate_parapet only) carry a one-list edit in tools/gate_lib.py onto
  the live master. gate_build.py MUST NOT be run against it (36 objects vs the master's 147).
  Each prints its own faithfulness gate; roadchop's `repro` mode proves the copy bit-exact
  BEFORE it builds. tools/walk_rederive.py `--drop` takes a deleted map entity's walk records
  out (an orphaned walk record goes on paving the town).
- **tools/emb_brookchop.py — EMBERBROOK'S WATER WAS A RAFT OF FLOATING BOXES** (2026-08-07):
  every sheet an independent 0.55 m cell 0.12 m THICK standing 0.09–2.04 m above its own bed —
  0.17 m of air, a lit underside, four lit walls and a shadow cast on the bed the water is
  meant to lie in. THAT is the judged "stacked mitred slabs", and it is why the correctly
  ported depth→alpha shader moved 269 pixels. The carrier welds each sheet into one strip,
  relaxes the lattice silhouette (−22.3% boundary length) and seats the bottom ring on the
  bed; emb_blockout's `water_field` carries the same seating so a rebuild agrees. It runs
  BETWEEN emb_water_shader's revert and its re-bake — the file asserts that order — and is
  NOT idempotent for `--xysmooth`. Receipt: at-water luminance p50 0.056 → 0.108 with NO
  LIGHT TOUCHED, and the town's water class closed 0/6 FAILING → 0 FAILING.
- **A JUDGE CAN BE ASKED ABOUT SOMETHING THAT IS NOT IN THE PICTURE** (2026-08-07, the Poppy
  defect inside the reviewer): scene_redteam armed `quality:water-read` on a POINT test of the
  water landmark's MAP POSITION, so four of Emberbrook's five FAILING water verdicts described
  pixels holding ZERO water — gateroad's "pitch-black flat plane" is a pale gravel apron at
  5.6× its own frame median. It now arms on MEASURED visible water (sheets rasterised through
  the shipped projection, agreed against the plate's own depth.png; threshold 0.5% of frame,
  `--water-census` prints it with no API). It now also asks WHERE the judge pointed: `aimOf`
  scores each `[QUALITY]` bbox against its own subject mask (water = that same visible-water
  census; sky = the plate's depth) and REFUTES, after stage 2, any verdict whose box holds
  under 2% of what it names — 31% of the post-arming water findings were aimed at ZERO water,
  and the sceptic can never catch that because IT IS SHOWN THE WORDS AND NEVER THE BOX.
  Absence claims abstain (their box marks where the subject *isn't*); `frame-edge-world` is
  left unmeasurable ON PURPOSE — its two candidate subjects disagreed 3-to-0 and the
  far-depth one would have killed crossing's real white-wedge finding, so an undefined
  subject gets no gate. `--aim-census` measures a finished run with no API; `--no-aim` is
  the A/B.
- **`blockout_material_coverage()` in emb_dress — A COVERAGE REPORT ON ONE AXIS IS NOT A
  COVERAGE REPORT** (2026-08-08). `vegetation_coverage_report` censuses the PREFIXES the
  harvest claimed; this censuses what render-visible meshes are WEARING at the end of the
  build. `emb_mat_leaf_green` (21 meshes, 20 of them `lm_field_*`) and `emb_mat_leaf_autumn`
  had shipped as flat untextured paint through every green gate for weeks, on no keep list
  and matched by no substitution rule — and the new census found three more (`lm_infill_*_
  fruit0_crown`) on its FIRST run. Related trap, same day: `PLAN["fields"]` had one `.append`
  and no reader, but three of its five classes were already dressed by an EARLIER matching
  rule — so "the plan has no consumer" sized the defect at 38.5% of a frame when
  `plate_probe` measured at most 2.464%. Right mechanism, wrong magnitude by an order:
  MEASURE THE PIXELS, not the plan.
- **IF NOTHING BUT THE CAMERA MAY SEE IT, IT IS A PICTURE AND NOT A PLACE** (2026-08-08).
  `cine_bake --glb` and `town_export` both drop `visible_camera`-only meshes. `visible_camera`
  alone stopped meaning "in the world" the moment a town shipped an 1800 m backdrop skirt —
  without the filter that skirt walks straight into the walkable bundle.
- **A GATE THAT COMPARES TWO DERIVED ARTIFACTS SAYS THEY DISAGREE, NEVER WHICH IS STALE**
  (2026-08-08). Emberbrook's THREE "pre-attributed, known-red" cine_test failures were one
  cause: `emb-townwalk/scene.glb` was four walk meshes behind its master. Re-exporting took
  the town 477/3/2 -> **480/0/2**, and the long-standing "square closeness ratchet" went with
  it — it was never a camera question. An attribution is a hypothesis; re-derive before you
  inherit one.
- **tools/gltf_fast_index.py — THE EXPORTER IS QUADRATIC, AND THE BLEND YOU AIM IT AT IS THE
  WHOLE STORY** (2026-08-08). io_scene_gltf2's `__append_unique_and_get_index`
  (`blender/exp/exporter.py:413`) is `x in LIST` per node/mesh/accessor and no gltf2_io class
  defines `__eq__`, so N child-of-root properties cost O(N²) identity compares at a
  micro-benchmarked 9 ns — emberbrook-dressed's 6.36 M nodes would take ~50 HOURS, and the
  26–33 minute band four attempts hit was the first 3% of it. We fix it FROM OUR SIDE (the
  Blender install is untouched): the list still defines output ORDER, an `id()`-keyed
  side-table answers MEMBERSHIP, fast path only when `type(obj).__eq__ is object.__eq__`.
  `EMB_GLTF_FAST_INDEX=0` reverts; the gate is byte-identity of both towns' bundles
  (measured: same sha256 patch on/off, cine_test 635/1).
  **AND THE 146x TRAP: `emb-cine/scene.glb`'s source is `emberbrook-master.blend` — THE GRAY
  BLOCKOUT — not `-dressed`.** Aim `--glb` at the dressed master and the exporter's Duplis
  branch walks 6.36 M scattered leaf/grass instances into 6,360,379 one-line NODES against
  1,370 meshes: a 1.9 GB bundle of which 1.7 GB is node JSON. Dressing scatter belongs in a
  plate, never in a collision bundle — the unwritten sibling of "if nothing but the camera
  may see it, it is a picture, not a place".
- **tools/moorage_search.py — A SEARCH IS ONLY AS HONEST AS ITS ORACLES** (2026-08-07). It
  lived in a scratchpad with roof/art/self oracles and NO west-arm oracle, so iteration 9's
  searched flight was free to land on the west boardwalk BY CONSTRUCTION — it severed the
  corridor and put the west waterfront back to a 92-cell one-way island that reach_probe
  called no-path both ways, weeks after `moorage_westlink.py` had closed exactly that. The
  `westarm` oracle is a CONNECTIVITY test, not a headroom threshold (its selftest's case C
  blocks 53 of 693 corridor cells and still connects; a threshold would have rejected the
  answer). Winner reopened it: deck lane 1/6 → 6/6, reach_probe REACHED both ways, one
  547-cell component. **THE ORACLE IS A SCREEN, THE DRIVE IS THE VERDICT** — two low-water
  alternatives passed the oracle and failed the drive, one roofed by derived planking that
  `self_roof` cannot see because it tests centre-lines. Same family as `_court_probe`: a gate
  that measures its own drawing cannot measure its own build.
- **tools/dh_pixel_census.py — A RAY-CASTER STOPS AT THE FIRST HIT, AND A HAZE CARD IS NOT THE
  ANSWER IT LANDS ON** (2026-08-08). It drops `hide_render` objects and MARCHES THROUGH
  render-only volume cards (a Volume link with no Surface link), accumulating τ = density × path,
  so the object it names is the one actually making the pixel. This overturned ALL THREE of round
  3's handover claims about `fx_haze_east`: it is not "missing a Principled BSDF" (six haze
  materials are two-node Volume Scatters, so an albedo resolver hunting a surface BSDF returns
  nothing on all of them — the resolver found its own blind spot); it is not the crushed-pixel
  culprit (a 5.4% wash standing IN FRONT of `cliff_east_closure`, which is 83–96% of every crushed
  region); and `fx_haze_south` is not implicated at quay-west at all (zero rays cross it).
  THE REAL DEFECT WAS AN INVERTED DEPTH CUE: the town's most DISTANT surface was also its DARKEST,
  because the card meant to supply aerial perspective is a 6 m CURTAIN, not a medium — its τ is
  identical whether the wall is 90 m or 170 m out. Fixed as ATMOSPHERE (a world-Z density ramp,
  `tools/dh_haze_east_depth.py`), explicitly NOT as light: `KEY_gorgewall` already exists and
  raising it was rejected once because it prints the rock's 16.7 m texture period as a quilt —
  more light makes a tiling artefact legible, more haze hides it AND lifts the black. Judge:
  lockfive and weave CLEARED, crossing's pitch-black pair CLEARED, gate moved from "a flat, empty
  dark void" to "atmospheric fog" (what survives there is a different, real defect the void hid).
  **DENSITY IS NOT THE WASH** — crosswise τ put `mat_haze_rim` at 0.594 and the east card at
  0.055, so it read mid-table on density while delivering a tenth of its siblings' effect.
- **tools/dh_seam_census.py — WHICH TWO OBJECTS MAKE THIS EDGE, AND IS IT STRAIGHT**
  (2026-08-08). `seam` counts the pixels where set A abuts set B and reports the u span, the
  RMS residual from a best-fit line IN PLATE PIXELS, and the world x/y/z of the A-side hits;
  `sky` asks the same against the world background; `box` puts a judge's bbox on the geometry.
  It reproduced the judge's own gate bbox (0.466..0.478) to three decimals at u 0.465..0.477 —
  and REFUTED the round-4 handover that named `cliff_town_*`'s dead-flat z = 37.0 top as the
  defect: **zero silhouette columns on all fifteen cameras and world background 0.00–0.03% of
  every frame. Dellhollow is a closed gorge; there is no sky in it to be flat against.**
  THE DURABLE LAW IT MEASURED: **AT GRAZING INCIDENCE A WALL'S SILHOUETTE IS THE ENVELOPE OF
  ITS CRESTS OVER TENS OF METRES, AND AN ENVELOPE IS STRAIGHT HOWEVER THE CRESTS WANDER** —
  unflattening the clamp that made 26.1% of `cliff_town_a` one plane moved the residual
  6.5 px → 7.0 px, i.e. not at all. Only MASS AT A DIFFERENT DEPTH (the new `BUTTRESSES` in
  t2_cliff_south) touches an envelope: u span 32 → 67 plate px. The straightness figure is a
  SCREEN — grid-quantised, and a tilted straight line scores well — read it with the u span
  and then look at the plate.
- **tools/dh_haze_medium.py — TAU IS NOT THE WASH, AND THE PHASE FUNCTION IS THE LEVER**
  (2026-08-08, round 6). FIRST: **A REPORT THAT DEDUPLICATES A CHECKLIST ROW PRINTS THE FIRST
  PLATE'S SENTENCE OVER FOUR OTHER PLATES' ANSWERS.** Round 5 handed over "the haze card's own
  edge, on five plates"; read per plate out of `findings.json` with each bbox put on the
  geometry, they were five different subjects — one card edge (gate), one darkness residual
  (weave), two upstream far-field plates that ZERO east-card rays reach, and one aimed at
  bright near-field foliage at 20 m (north-landing, refuted). Read the ROW, never the roll-up.
  THE REFUSAL: thickening the card into a 16.5 m medium at *exactly preserved optical depth*
  (0.102x6.00 = 0.037091x16.50) GAVE BACK MOST OF ROUND 4 — far-field p05 gate 14.7→7.6, weave
  13.9→4.5, lockfive 17.3→6.1. **EXTINCTION IS A PROPERTY OF THE MEDIUM; IN-SCATTER IS A
  PROPERTY OF HOW MUCH LIGHT REACHES IT — a medium moved against a wall moves into its shadow.**
  It also never reached its subject (the town wall's mass is NEARER than the medium's near face).
  WHAT WORKED IS ONE NUMBER: `mat_haze_east` anisotropy **0.30 → −0.25**. Same tau, same albedo,
  same geometry — only the angular distribution. **DELLHOLLOW'S CAMERAS LOOK WITH THE SUN, NOT
  INTO IT**, so a forward phase function threw the card's light away from every lens except
  `gate`'s, which looks across the rake — which is why gate BLEW OUT WHITE while the other four
  went BLACK. They are the two ends of one phase function, so one number moves both correctly
  (far-field crushed weave 85.6→8.6%, lockfive 25.5→0.9%, waterfront 21.9→0.0%; gate p95
  167.0→135.7). And it is principled, not a preference: **`cycles.volume_bounces == 0`** — this
  bake does no multiple scattering, which is exactly what makes real forward-scattering haze
  bright in back-scatter, so a negative g is the single-scatter stand-in for the bounces not
  paid for. Stop at the **p05 KNEE** (−0.50 lifts only the median = the featureless-bank
  direction). Grade a slab LADDER monotone in distance (mid 0.286 < far 0.480 < rim 0.594) or
  you have rebuilt the inverted depth cue. THREE SMALLER RULES BANKED: **a fix can blind its own
  instrument** — round 4's node-driven ramp made `dh_pixel_census` print `tau=driven` for the one
  card in town whose tau was the question (now evaluated; and a ray that STOPS INSIDE a card now
  closes its segment, which was free while the card stood in empty air and is the whole
  measurement once geometry stands inside it); **a plate refused on the BEAUTY frame keeps its
  OLD depth.png** (shelf-east's was a round behind — they are different artifacts and a
  picture-derived rebake list governs only one); and **no solved camera may lie inside a volume
  card** — `north-landing`'s eye is 2.88 m off the east card's near face, so a medium grown
  toward the town would have milked its whole frame with nothing in the pipeline saying so.
- **A WHOLE-TOWN DRAFT A/B IS A RULER, NOT A PREVIEW** (2026-08-08). `cine_bake --draft --res
  1008x576 --samples 28` is 15 s a frame, so all fifteen Dellhollow cameras cost four minutes,
  and **two independent draft renders of the SAME master differ by 0.01% of frame above 4/255
  and 0.00% above 12/255** — denoised Cycles is effectively deterministic, so that is a real
  noise floor and a rebake list can be derived from RENDERED FRAMES instead of from a frustum.
  It is strictly better: the frustum said the wall was 24% of lockhead, and the picture said
  the change there was zero. Do this before every plate bake that touches shared geometry.
- **tools/plate_probe.py — GROUND LUMINANCE WITHOUT BLENDER** (2026-08-07): reconstructs a
  world XYZ per pixel from a bundle's own solved camera + depth.png, derives normals from the
  world-position gradient and splits a plate into GROUND/WALL/VOID — 15 plates in ~40 s. The
  night-grade doctrine's "measure ground luminance on region probes" had no instrument until
  this. It names a REGION, never an object: the world box is the input to a Blender ray census.
  Traps at the tool: NEAREST-only depth resample, depth discontinuities faking grazing
  normals, and *dark ≠ crushed* (crushed = dark AND locally flat).
- **tools/town_blockout.py `STAIRS_V2` — the switchback pivot split; a flight not in the set
  is still the old geometry, and an edge joins it only when its district builder is re-run in
  the same window.** (Round 21: both flights of a switchback pivoted about ONE waypoint, so a
  body walking DOWN was picked back UP by walkGround, rung by rung — and a flood fill called
  it one component the whole time. Only the drive says so.)
- <town>.cameras.json (authoring; grade in defaults.exposure) → tools/cine_solve.mjs →
  .cameras.solved.json → tools/scenegraph_derive.mjs → scenegraph.json →
  tools/cine_bake.py (Blender headless, ALWAYS `-b --python-exit-code 1`; bake ray-cast
  is the ONLY visibility oracle). PLATE BAKES RUN FULLY PARALLEL (user standing order
  2026-08-01): one Blender process per camera, wall-clock = slowest frame, never
  sequential; still rebake ONLY frustum-affected cameras on incremental changes.
  MEMORY CAP (2026-08-01, the laptop drowned in swap at 6 bakes + a Metal render):
  max 3 concurrent heavy Blender jobs town-wide across ALL lanes; check
  `sysctl vm.swapusage` before spawning — if swap used > 75%, run 2. Parallel
  within the budget, queued beyond it. Lanes coordinate via main.
  PARALLELISM CONDITION (2026-08-01, measured): the parallel order holds only while
  one plate fits comfortably (gray master ~1.6GB — parallel pays). Once a single
  plate saturates the GPU (dressed Emberbrook: 9.8GB, 27M tris via Metal on unified
  memory), go 1-wide serial: pondlane baked at both widths — 2-wide 411 s/plate vs
  1-wide 403 s/plate, ZERO throughput gain, plus 3/7 crashes at 2-wide. The tell is
  that exact test: if N-wide doesn't beat 1-wide on seconds-per-plate, it's
  contention — serialize. routes: <town>.routes.json (tools/routes_derive;
  `--check` must be CLEAN — nav-eval composites from routes, stale routes = wrong scores).

## Canon documents (each is a constitution earned from Dellhollow scars)
- docs/plans/seam-canon.md — scene-transition law: no-return arrivals, one-cut-per-
  passage, exits-in-frame, invisible-arrival diagnostic, perceptual gate.
- docs/plans/town-legibility.md — why cameras exist; player-readable paths.
- docs/plans/combat-ecosystem.md — battle architecture + Rulings log.
- docs/plans/battle-core-design.md, house-variety-design.md, water-transparency.md,
  cliff-completion.md, pops-of-color.md (AS BUILT sections) — the look pillars
  (golden-hour variant C, greens into autumn, varied houses, transparent flowing water).

## Runtime (public/play3d.html — COORDINATOR-OWNED, agents message main for edits)
- **THREE IS r185 (2026-08-03), ONE FILE.** public/lib/three.min.js is an IIFE built by
  tools/build_three_lib.mjs from tools/three_lib_entry.js — three + GLTFLoader +
  DRACOLoader + three-mesh-bvh, publishing `globalThis.THREE`/`MeshBVHLib` exactly as the
  r128 UMD did (no page became a module, no load order moved). **EDIT THE ENTRY, RUN THE
  BUILD, COMMIT THE ARTIFACT** — there is no build step at serve time. Deps are
  devDependencies; `npm run build:three`. What the upgrade turned on and the traps it
  paid for: **docs/qa/three-upgrade/index.html** (before/after board + gate table).
  THREE RULES IT COST, all of the same shape — say which space the bytes are in:
  (1) depth.png/mask are `colorSpace = NoColorSpace`; an sRGB decode gives WRONG
  occlusion, not an error, and r128 only got away with it by having no colour management;
  (2) r185 renders into a non-XR render target in the LINEAR working space whatever the
  target's texture declares (and declaring SRGBColorSpace allocates SRGB8_ALPHA8, so the
  hardware round-trips the encode away) — battle_stage3d's display-space grade was a stop
  and a half down with EVERY GATE GREEN until its shaders converted explicitly;
  (3) r128 scaled every light by pi inside WebGLLights and r185 does not — `IU()` is that
  conversion, applied once at the light object so the ratified numbers still read as
  themselves. Colour management also means a hand `convertSRGBToLinear` is now a DOUBLE
  conversion: two were deleted, look for a third before adding one.
- **A PAGE-SCOPE SINGLETON THAT IS ONLY DRAWN IN SOME SCENES IS SCENE-SCOPED ON THE GPU**
  (2026-08-08). `contactShadow` is built once at load and parented to `ch`, but only the
  real-time branch ever turns it on — and three.js registers a geometry and uploads a texture
  when it is first DRAWN, so both joined `renderer.info` on the first ow-valley frame, above
  every `(scene, shot)` baseline taken before that leg, and stayed for the life of the page.
  THAT is the whole of transition_test's long-standing 162/6: doors 16-19 are exactly the first
  REVISITS of the three states baselined before the run's first ow-valley leg, every delta a
  byte-identical `{geo:1, tex:1}`. Disposing it in `sceneDispose()` (the JS objects stay; the
  next RT frame re-uploads 4 verts and a 64x64 canvas) takes the gate to **168/0**. `occRing`/
  `occDia` are the same pattern, measured LATENT — fixed so the gate cannot go red
  nondeterministically. `DEPTHQ` is the same shape and DELIBERATELY LEFT: it uploads in the
  first plate scene, so it is inside every baseline — it would only bite a run that booted in a
  real-time scene. "Built once, never disposed" is safe ONLY for an object every baseline has
  already drawn. (The battle stage is invisible to this gate by construction — it builds its own
  WebGLRenderer, so nothing it allocates reaches `R.info`.)
- **THE PAGE RENDERS AT THE DEVICE PIXEL RATIO, CAPPED AT 2** (2026-08-08). It never did before,
  so a retina display showed 2x2 device-pixel blocks on every contrasty silhouette — the user's
  standing "pixelated seam". THE FACT THAT DECIDED IT: every plate is 2688x1536, EXACTLY twice
  the 1344x768 canvas, so dpr 1 was downsampling the authored art by half; dpr 2 is 1:1 with the
  art, not a sharpening. Measured cost: a plate scene +9% frame time (draw-call bound, not fill
  bound), ow-valley 3.3x (12.7 ms, still inside 16.7 with 24% spare); GTAO+aerial grade is 42%
  of that frame and half-rate GTAO is the named prize if it ever needs one. `?dpr=1` restores
  the old behaviour, `?dpr=<n>` clamps 0.5..4.
  **SIX HARD-CODED 1344x768 SITES HAD TO MOVE WITH IT, AND FIVE FAIL SILENTLY.** The composer is
  the trap: **EffectComposer handed a render target takes that target's PIXEL size as its CSS
  size** (`this._width = renderTarget.width`), so `setPixelRatio` ALONE leaves the whole
  real-time chain at 1344x768 with no error and no visual tell. The subtlest is the **FXAA/dither
  `texel` uniform — a ShaderPass has no `setSize`**, so a stale texel BLURS instead of
  antialiasing (it is why the board's own dpr-2 column understated the fix). Also GTAO's
  constructor, the `ao_res` fraction, bloom's resolution, and `SIM.paint`'s `gl.readPixels`
  window (which otherwise probes a quarter of the frame, in the wrong corner). A RESIZE IS A
  RESIZE: no colour space was touched. There is deliberately NO window-resize handler —
  `setSize(W,H,false)` plus CSS sizing makes a window resize a pure CSS event (proof:
  tools/../docs/qa/dpr/dpr_resize.mjs, 16/0). Known gap: `PR` is read once at load, so dragging
  a window from a 1x to a retina monitor stays at 1x until reload.
- **THE FILL IS THE SKY** (2026-08-03). `scene.environment` — a 128x64 float equirect
  written from the town rig's own colours (or the ow rig's), PMREM'd — REPLACES the flat
  hemisphere+ambient fill rather than stacking on it, in charLight() and in the ow block.
  `?ibl=0` restores the two lights. THE LEVELS ARE SWEPT, NOT DERIVED: the k = I identity
  says the swap is energy-neutral and the measured frame said it lifted the overworld's
  shadows 0.188 -> 0.302 and cost 18% of its chroma (PMREM's last mip is a blurred
  radiance, not the cosine convolution the identity assumes). window.__envTune(k, sun) and
  window.__shadowTune(r) are the live knobs; tools/shot_compare.mjs is the ruler; the
  sweep tables are in the source beside the shipped numbers.
- Scene system: pre-rendered bg.png + depth.png per camera, exact-pixel depth occlusion;
  WALKLOCK (walk network is law in /^(del-|townwalk)/ scenes); GHOST v2 stencil;
  UILOCK modal contract; in-place scene swaps via transitionTo() + 'eb-scene'
  CustomEvent module contract (see sgAnnounce comment; ?reload=1 = fallback).
- **THE BATTLE PRESENTATION ARC** (2026-08-08; audit + slate: docs/plans/battle-presentation-inventory.md,
  boards docs/qa/battle-{audit,contact,cast,world}/). The measured start: the camera moved 12.6 mm
  in 3 s (fixed), the attacker covered 1.35 m of a 5.21 m gap so every impact fired 4 m from the
  swing, `clipsOf()` returned the same four clips for EVERY body (so the victory pose was everyone
  standing in their idle, and using an item was standing perfectly still), 95.6% of arena materials
  carried no texture, and the screen ran a SECOND renderer with no environment and no tone mapping.
  SHIPPED SO FAR: **CONTACT** — strike station derived from both bodies' own measured Box3 widths,
  damage timed to a contact frame DERIVED per clip (resample the rotation tracks through the mixer's
  own interpolants, sum arm-chain angular change, argmax — no marker exists in glTF and the old code
  applied one hand-measured 37% to every creature), plus hit-stop on one virtual stage clock;
  6.54 m -> 1.32 m at the damage event with turn wall-clock UNCHANGED (+0.05%, paid out of the
  announce beat). **STAGING** solved against the frame's own projection at 2v1/2v2/2v3.
  **THE CAST ACTS** — cheer/use-item/flee clips through the house retarget+verify pipeline, and a
  WEAPON SOCKET: shaft axis derived forearm->hand in the hand bone's frame, bone world scale divided
  back out; `WEAPONS` keys items.json and reaches the arena through battle_turnbased's `weaponOf`
  callback SO THE STAGE STILL NEVER READS GS. Art owed under `assets/weapons/3d/<item>.glb` —
  authored art supersedes the code recipes with no code change; an equipped weapon with neither is
  an EMPTY HAND, never a placeholder cube.
  **`?arena=world` — FIGHT WHERE YOU STAND, shipped INERT** (public/js/battle_world.js). Borrowing
  the field's renderer/camera/PMREM/post chain makes contexts 2->1, writes ZERO shaders (the r185
  colour rules are constraints on HAVING a second rig — deleting the rig deletes the bug class) and
  is FASTER than the diorama (243.5 vs 184.7 fps: the old "the second context is free, the world
  draws a frozen frame" comment was wrong, the world keeps rendering under the modal). Teardown
  measured total. NOT default: 68.8% of sampled encounter cells can stage a readable fight (only
  after a yaw sweep; forest 52.1%), and **the plates are more legible than the valley** — two clean
  silhouettes on a low-contrast painting is a composition. THE OCCLUDER SET IS NOT THE COLLIDE SET:
  building it from `collide` (which excludes noStand foliage) reported a party inside a hedge as
  fully visible; from the DRAWN scene the pass rate fell 86.3 -> 68.8%.
  **THE MONSTER REGISTER: THE WOLF IS THE REFERENCE, THE CHIBIS ARE THE OUTLIERS** (bet H,
  2026-08-08 — the naive reading was BACKWARDS and one picture settled it). Put all six monsters
  in ONE frame at one scale/rig/camera WITH the ratified party rigs and it is obvious: duskpad
  (naturalistic, desaturated, real animal proportions) is in the game's register and the four
  Quaternius *Cute Animated Monsters* chibis — ball bodies, oversized black almond eyes, cream
  teeth — are not. **A pass that "harmonised" the wolf toward the blobs would have moved the whole
  cast away from the party.** All six are CC0 Quaternius (MANIFEST.md); brook-sprite ships as a
  CODE wisp, its GLB is only the fallback. Measured axes: poly density REFUTED (1000-1962 tris,
  same author/budget); textured-vs-flat real but not the problem at a foe's ~18% of frame height;
  albedo VALUE (1.85 stops) and SATURATION (9.4x) are the real ones. THE GATE IS THE PARTY'S
  RANGE, NOT ITS MEDIAN: `V50 ∈ [0.192,0.784]`, `V95 ≤ 0.784`, `S ≤ 0.452` with saturation a
  CEILING NEVER A FLOOR (or a grey wolf fails for being grey) — an equal-median gate produced a
  worse picture that scored better, and a value *gamma* wanted γ 4.17 and drove black eyes to
  0.000 (it is a GAIN). tools/monster_regrade.py is idempotent by never reading what it writes
  (source bytes from a pinned rev). Foe icons are now renders of the same GLBs the arena stages:
  mean hue error 95.8°→4.4°, 105.2°→1.5°, 51.6°→0.1°. STILL OPEN and costed both ways: the cartoon
  faces live in three 512² atlases and in two meshes' geometry — no material grade reaches them.
  **THE KO IS A BEAT, AND THE KILL USED TO BE THE ONE BLOW WITH NO FEEDBACK** (bet I, 2026-08-08).
  The sharp defect was ORDERING, and it was not in the audit: `battle_turnbased` runs `syncHp()`
  (-> `setDead` -> `markDead`) BEFORE `hitShake()` (-> `flinch`), and `flinch` RETURNS EARLY ON A
  DEAD BODY — so the loudest blow in the fight had no flash, no sparks and no ring. Measured: the
  victim's screen box read **104.6 luminance 60 ms after being killed, against 121.2 standing
  idle** and 213.3 for a blow it survived. THE KILL WAS DARKER THAN DOING NOTHING. Now five beats
  (blow -> driven back -> falls ONTO the floor under it via `SIM.ground`, never `y0-0.55` -> lies
  solid 760 ms -> dissolves and leaves a mark): sink 0.550 -> **0.000 m**, body gone at 842 ->
  2260 ms, kill feedback 104.6 -> 167.7. The killer HOLDS over the body (`holdUntil` read per
  frame) with the swing's tempo provably unmoved. Reactions are composed on `bob`, and TWO SIDES
  DO NOT REACT THE SAME WAY — one amplitude gave the party 7.52 px against a do-nothing floor of
  7.30 (invisible, because a party member already faces the foes), so the victim's side recoils
  away and the killer's side leans in. Victory is a sequence (hold -> cheer -> tally) with the
  tally placed on the side the party is NOT on, asked from the stage's own projected anchors.
  CSS trap paid: a `position:absolute` scrim paints BELOW a positioned sibling, so the first build
  dimmed and blurred the VICTORY panel itself. `stage.anchor()` CANNOT SEE ANY PROCEDURAL LAYER —
  it projects the pivot and a constant height, so a gate on swing/recoil/reaction must diff pixels
  or read `bob` (`at()` now returns `bob`, `alpha`, `floorY`).
  **AND THE BACKDROP PINS THE CAMERA**: assets/battle/MANIFEST.md says the four plates were generated
  from a prompt carrying the arena camera's exact height/tilt/fov and must be re-shot if it moves —
  a camera language is not a tuning change to the diorama, it is incompatible with how its world is
  drawn. That fact orders the whole slate.
  **SO THE CAMERA LANGUAGE WAS BUILT WHERE IT COSTS NOTHING** (bet B, 2026-08-08, world arena only;
  board docs/qa/battle-camera/index.html, instrument tools/battle_camera.mjs, `?bcam=0` is the A/B
  on one build). A SHOT TABLE PLUS A SOLVER — round/decide/strike/impact/ko/victory — where the
  table carries INTENT (who is in frame, what fraction of it they fill, boom elevation, lens, move
  duration) and NOT ONE METRE VALUE IS A CAMERA POSITION: every pose is solved against each body's
  own measured Box3. **THE 180-DEGREE RULE IS A REFUSAL INSIDE THE SOLVE**, both halves reading
  `CFG.partySide` (which the world arena now READS instead of hardcoding): the eye may not cross the
  party→foe axis, and every party body must still project outboard of every foe body *with the
  perspective divide* — an ordering taken on a flat dot product is wrong the moment two bodies
  differ in depth. A crossing swing is halved, then dropped, then the camera KEEPS THE POSE IT HAS.
  576 shots, 0 violations. **IT NEVER CUTS** pending §11.11's ruling (`cut:false` on every row).
  Two beats got the moves the KO lane wanted and could not have: a push across `CFG.ko.holdMs` and
  a 0.95 rad swing to three-quarter FRONT of the party for the cheer. Costs 0.1% of the frame.
  THREE THINGS IT MEASURED THAT ARE WORTH MORE THAN THE FEATURE:
  (1) **A SHOT MUST BE SOLVED WHERE THE BODY WILL BE, NOT WHERE IT IS** — the strike shot is asked
  for the instant `act()` starts, with the attacker still five metres away, so framing the pair from
  her home slot made a wide shot of a gap she was closing; it now takes the strike station `act()`
  has already derived.
  (2) **TWO RAYS ARE NOT A SILHOUETTE, AND FIXING THAT MOVED THE STAGING RATE DOWN 68.8% → 64.4%**
  (forest 52.1→47.9, water 58.6→44.8). Nine samples across the body's own box, refuse below 67%
  visible. Same shape as the spike's own 86.3→68.8 drop when its occluder set stopped being
  `collide`: the world did not get worse, the instrument stopped lying. Do not loosen it back.
  (3) **THE CAMERA OWNS SIZE AND OCCLUSION; IT DOES NOT OWN TONAL SEPARATION.** Worst-case foe
  height 13.0→17.8% of frame (crag) and 12.8→20.1% (water) with occlusion equal or better — but RGB
  silhouette contrast FELL at meadow and water, because the fixed pose sometimes happens to back the
  cast with sky. A cast-only rim light is not available (three.js tests a light's layers against the
  CAMERA, never per object) and a fresnel via onBeforeCompile would give this module its first
  shader — which is the whole reason the r185 colour class is *deleted* here rather than managed.
  OPEN, and it is the remaining legibility gap.
  Measuring it needed two meter fixes this repo has paid for before: occlusion is an INTERSECTION of
  the real and depth-test-off silhouettes, never a ratio of areas (GTAO/bloom leave a halo the two
  passes do not share — a fully visible body measured "−136% occluded"), and contrast is RGB, never
  luminance (the cutin_edge lesson: a gate that measures brightness cannot see colour).
- Modules (public/js/): game_state (GS), battle_rules (pure kernel — untouchable),
  battle_turnbased + battle_stage3d, encounters, ui_kit (FF-blue), shop, menu, npc,
  dialogue, **story_runtime**, followers, hush, route_overlay, music. Each self-arms at
  load AND re-arms on 'eb-scene'.
- **public/js/followers.js — THE PARTY WALKS BEHIND YOU, IN TOWNS** (2026-08-03, user
  playthrough item). A BREADCRUMB TRAIL, never a pathfinder: the leader's positions are
  sampled on the physics tick and each follower is drawn a fixed ARC LENGTH back along that
  polyline, so every place a follower stands is a place walkStep() already allowed — it
  cannot get stuck, cannot need a nav query, cannot disagree with WALKLOCK. If you find
  yourself wanting a path solver you have left the design. Towns only (WALKLOCK's own
  /^(del-|emb-|townwalk)/ — the overworld is excluded by the user's ruling). Nothing it
  builds enters collide/walkRef/allMeshes, which is what makes "a follower can never block
  the player" true by construction. Roster = GS.activeParty() minus the player's body
  (vesper/lake/maren ONLY); THE LEADER MUST HIMSELF BE ACTIVE, which is what keeps Ch1's
  Lake POV solo without naming a scene. Mochi is a cat, not a party member: `story.ch1.pact`,
  and the posted cats stand down via the new **Npc.hide(id,on)** (page-level intent, honoured
  by every later spawn). `?nofollow=1` disables. QA docs/qa/followers/index.html.
- **public/js/hush.js — THE HUSH: Emberbrook loses its heart** (2026-08-03). Flag-driven off
  `story.ch1.hush`, /^emb-/ only. The user chose "TAKE THE LIGHT" over a grayscale wash and
  the reason is canon — Emberbrook IS the Heartlight town. The town is a PRE-RENDERED PLATE,
  so no runtime light can put its baked lamps out: the frame is graded ON THE WEBGL CANVAS,
  and that placement IS the effect — a cut-in is a DOM <img> dialogue.js paints OVER that
  canvas, so THE PORTRAITS STAY WARM while the town goes blue and flat. Move the grade to a
  parent element and the effect breaks silently (Hush.debug().cutinsWarm asserts it). The
  same decision drives the shipped charLight() rig through `window.__hush` + **SIM.relight()**.
  The brightness cut is PLATE-ADAPTIVE off window.__charlight.plate.p70 (measured: gatefield
  at 0.115 vs the square's 0.21 — a flat cut made the Old Gate a dark frame, not a hush).
  `?hush=1|0` forces it. Capture with tools/hush_shot.mjs; QA docs/qa/hush/index.html.
- **public/game/lightrigs.json — THE PER-TOWN SUN, as runtime data** (2026-08-02). Tier 2 of
  charLight()'s rig lookup: a town whose `<town>.cameras.json` carries no `defaults.lightRig`
  (Dellhollow) gets its key direction/colour/energy from here. IT SHIPPED UNTRACKED ONCE —
  the code that fetches it was committed, the file was not, so every clone and every `dist`
  silently fell back to the page-default sun with only a console warning. A runtime data file
  that is not in git is a bug that only reproduces off the author's machine.
- **public/game/worldbounds.json — WHERE THE WORLD ENDS, as runtime data** (playtest round 6).
  Per scene; play3d fetches it on boot and `sceneParams()` applies it. `ow-valley: floorY 0.0` —
  the water line. A region built from an ANALYTIC height field has no edge: ow-valley's ground
  runs continuously out of the gorge and under the water to y −6.07 at the tile corner, because
  valley_map.py suppresses its own rims within 22 u of the channel so Ch2's boat can leave. The
  rule lives in walkStep's `outOfWorld()` and is ONE-WAY BY CONSTRUCTION — below the bound only
  DEEPER steps are refused, so a body already outside always walks back in. A boundary that can
  strand a player is the defect it was built to fix. The riverbed down to the Moorage (the
  `boat-tar` landmark, measured floor 1.71) stays open on purpose: measure before you fence.
  Instrument: tools/playtest/edge_probe.mjs (`--points`, `--nobound` for the A/B).
- Game data (public/game/): monsters, items, encounters, growth, shops, music.json
  (map rules first-match-wins), npcs.json, dialogue.json, **story.json**.
- **THE STORY LAYER (2026-08-02 — read docs/plans/end-to-end-wiring.md first).**
  window.Story reads public/game/story.json and drives the SHIPPED primitives: prose
  through Dialogue.play() on nodes it injects (Dialogue.inject — merge, never replace;
  dialogue.json wins a collision), conditions through Dialogue.check() verbatim,
  effects through GS.setFlags/addItem/addGold, cameras through SIM.shot(), the freeze
  through UILOCK. It rides phys() between sgTick and Encounters: a beat LOSES to a
  transition and WINS over an ambush. **A CHAPTER IS A SET OF FLAGS PLUS A SET OF
  BEATS, NEVER A MODE** — `at.chapter` is a label for the save screen and the music,
  never a switch, and NO BEAT MAY TELEPORT the player across a scene (the corridor
  between the towns is walked). Chapters 1-2 only; Ch2's end card is terminal.
- **Conditional edges.** An edge carrying `when` (or the `requires` shorthand) is
  evaluated by sgLive() with Dialogue.check on EVERY PHYSICS TICK — not at bind time,
  because the frame a story flag flips the edge AND its marker must appear with
  nothing reloaded. It FAILS CLOSED. scenegraph_derive emits a `sealed` exit that
  declares `sealedUntil` as exactly such a pair (no `sealedUntil` = still no edge).
  The Old Gate is the first: `story.ch1.gate-open`.
- **The save is v2** (`emberbrook-save`; the v1 key is read once and migrated). It
  carries `at` {chapter, scene, cam, pos, yaw} — THE resume authority — plus `beats`
  (the once:true ledger) and `meta`. GS.load() MIGRATES and never refuses a save it
  can parse; the old "reject any v!==1" silently erased playthroughs. GS.syncJoins()
  honours growth.json's `joinFlag` (lake-joined, maren-joined). Autosave fires on
  'eb-scene' ONLY once `beats` is non-empty — a dev scene-jump must not write a save,
  which is play3d's own module contract and what transition_test booby-traps.

## Shipping it (the live demo is a standing deliverable, refreshed every work window)
- **docs/DEPLOY.md** — tools/build-static.mjs (inclusion-not-exclusion; its own glTF-magic,
  scene-geometry and reference-integrity gates) → tools/deploy-ghpages.sh → LIVE at
  https://junshern.github.io/emberbrook/ . `--compress` is the deploy flag set.
- **The build has an ENCODE CACHE, on by default** (`.build-cache/`, gitignored):
  sha256(source) + sha256(EVERY parameter that changes the bytes — the encoder source
  itself, `--plate-max`, the Pillow/gltf-transform versions). Warm rebuild is SECONDS
  instead of 28 minutes, which is the point: a 28-minute deploy is a deploy you skip and
  the site drifts behind the branch. `--no-cache` bypasses; a bad entry is DEMOTED TO A
  MISS, never a build failure; depth.png is deliberately uncached because its encode
  carries the byte-exact round-trip proof. A cache keyed on the source alone would serve
  stale art the first time a quality setting moved — invisibly.
- **DEPLOYING FROM A CLEAN WORKTREE, AND THE TWO THINGS THAT LOOK LIKE FAILURES AND ARE NOT**
  (2026-08-08). Build from a detached `git worktree` at origin's tip whenever the main tree is
  dirty — a lane's uncommitted module WILL otherwise be published (measured: a main-tree build
  differed from the worktree build by another lane's uncommitted `js/battle_world.js`). The
  worktree needs two things git does not carry: the main repo's `node_modules` SYMLINKED in
  (static_verify needs `ws`) and **`EB_BUILD_CACHE`** pointed at the main repo's warm
  `.build-cache`. Then:
  (1) **`dist` SIZE AFTER A PUSH IS A LIE** — `deploy-ghpages.sh` turns `dist` into its own
  throwaway git repo IN PLACE, so `dist/.git` (~500 files / ~364 MB) inflates any later `du`/
  `find`, and THE SCRIPT'S OWN PRE-FLIGHT prints the inflated number on a rerun because it counts
  before its `rm -rf .git`. Two of us built a whole false "the cold cache changed the build"
  theory on that number. Measure before deploying, or exclude `.git`.
  (2) **A PAGES BUILD CAN STALL IN `building` FOREVER** — measured: `updated_at` frozen at
  `created_at` for 32 minutes, then it completed the instant a re-queue displaced it. A HEALTHY
  build updates within ~70 s (73 s and 63 s measured). **If `updated_at == created_at` past ~3
  min, `gh api -X POST repos/<o>/<r>/pages/builds` — the stamp will never move on its own.**
  Also: a long push DIES WITH ITS FOREGROUND TOOL CALL (launch `(nohup … &)`; `setsid` does not
  exist on macOS), and an INCREMENTAL push is minutes — the 60-90 minute transfers were
  full-tree first pushes.
- **node tools/static_verify.mjs** drives a built tree off `python3 -m http.server`;
  **`--url https://…` drives THE DEPLOY**. Only the live run can see a file that
  committed code fetches and git does not carry (the lightrigs.json class).

## Test gauntlet (run what your change touches; all green before ship)
- node tools/slice_test.mjs · cine_test.mjs · seam_test.mjs · seam_walk.mjs ·
  economy_test.mjs · battle_sim / encounter_sim · transition_test.mjs --port=<port>
  (real Chrome; needs a server on the port serving /public)
- **node tools/playtest/percept_test.mjs — DOES THE PLAYTEST HARNESS SEE THE GAME** (1.1 s,
  no LLM, no server): feeds the adapter's OWN PERCEPT_JS/FRAME_GATE_JS/flattenPercept four
  known screens (overworld · dialogue · BATTLE · transition veil) as real DOM in headless
  Chrome on about:blank, replays the recorded runs' percepts, and censuses the percept's
  selectors against the shipping UI source. It exists because five adapter perception bugs
  in one day each cost a 30-60 minute LLM run to find and another to prove fixed — the worst
  being a fully drawn battle the percept could not see at all. A HARNESS BUG IS NOT A GAME
  BUG, AND ONLY THE HARNESS CAN BE TESTED IN A SECOND.
- **tools/cdp.mjs — the shared Chrome/CDP plumbing for EVERY browser tool** (transition_test,
  playthrough_test, trigger_probe, arena_playtest, ow_shot). Never hardcode a CDP port or
  match a page by literal URL again: `freePort()` (OS-assigned — two tools both shipped 9351
  and the collision reported "chrome never exposed a page", a lie about the world caused by a
  neighbour), `GAME_PAGE` (matches BOTH /play.html and /play3d.html — server.js serves both),
  `findPage()` (a failure that DUMPS every CDP target it saw and separates "CDP unreachable"
  from "matcher wrong"), `killOrphans()`, `chromeArgs()`. The rule it encodes: AN INSTRUMENT
  THAT FINDS NOTHING MUST PROVE IT COULD HAVE FOUND SOMETHING.
- **A BROWSER TOOL THAT DOES NOT REAP ITS CHROME POISONS EVERY OTHER LANE** (2026-08-03,
  measured). `tools/mood_shots.mjs` shipped without going through cdp.mjs's cleanup and left
  SIX orphaned Chrome instances (`--user-data-dir=/tmp/moodshots-*`, all `ppid 1`) alive after
  its own lane had finished. They held **7.6 GB of swap**: the machine sat at 17.7/18.4 GB
  swap used with 675 MB free and ZERO Blender running, and every browser gate on it was slow
  and flaky for half an hour. Reaping them returned swap to 10.1 GB and free to 8.3 GB — so
  "the lanes are straining the machine" was FALSE; one leaked tool was.
  Tell an orphan from a live gate with
  `ps -Ao pid,ppid,etime,command | grep 'MacOS/Google Chrome '`: root Chrome with **ppid 1**
  is an orphan, one with a live parent pid is somebody's running gate and MUST NOT be killed.
  **NEVER pattern-kill Chrome by name — 25 of the processes on this machine are the USER'S OWN
  browser.** Match on the tool's own `--user-data-dir` prefix and prove the parent is gone
  (`pgrep -if <toolname>` empty) first. Any new browser tool goes through cdp.mjs, which
  already has `killOrphans()` and `sweepStaleProfiles()`.
- node tools/dialogue_style.mjs — THE STYLE GATE (no browser, no network): every spoken,
  `system` and `narrate` box in chapter1.js + chapter2.js + dialogue.json against
  VOICES.md's OWN numbers — two sentences a box, 25/30-word ceilings, one capped word,
  banned register, reading grade, exclamation density — reported BY SCENE and BY
  CHARACTER so a writer can act on it. Chapter3 is OUT of scope and does not gate
  (`--scope=all` measures it for information only). `--selftest` proves the sentence
  counter on hand-checked cases FIRST: '…' and '—' are not enders, abbreviations don't
  split, and a ≤2-word segment with no copula is a noise, not a sentence. Judgment calls
  (aphorism budget, aim band, internal ration) are WARNINGS on purpose — a heuristic that
  fails a build is a heuristic that gets written around.
- node tools/story_test.mjs — THE STORY GATE (no browser, no network): every beat's
  scene is a scenegraph node and every named cam a baked shot in that bundle's
  cine.json; every line resolves to a node and a speaker; no story node id shadows a
  dialogue.json one; THE FLAG LEDGER — a flag READ with no writer is a FAILURE (it
  caught the Old Gate's `ch1.gateOpen`, which nothing in the shipped game ever set), a
  flag WRITTEN with no reader is a WARNING (the next orphan joinFlag); the three
  §6 contract flags each written by exactly ONE beat; no beat moves the player.
- node tools/playthrough_test.mjs --port=3000 — §W REACHABILITY (default ON, `--no-walk`
  to skip, 16.7 s = 2.2% of the run): flood-fills between consecutive SAME-SCENE beat
  anchors INSIDE the page via tools/reach_probe.mjs — SIM.walkFloors/ground/blocked/edges,
  the engine's own rays and the player's own body box, never the file. It audits the
  TELEPORTS the story spine is built on: the harness drives SIM.tp() to each anchor, so
  without §W "the beat fires" never implied "a player could get there". It takes in-scene
  cut/passage edges deliberately — Dellhollow's levels are joined by 42 self-edges and a
  walk-only fill calls the gate arrival and the log-jam unreachable when they are 0.4 m
  apart in plan and 10 m in height. A clean run is 69/1 until ch2.road's anchor is fixed.
- node tools/playthrough_test.mjs --port=3000 — THE END-TO-END RECEIPT (real Chrome):
  cleared localStorage → NEW GAME → every Ch1 beat firing on ITS OWN trigger (it never
  calls Story.force) → the sealed gate edge absent before the flag and live after →
  the handoff TAKEN as an edge into ow-valley → Ch2 → maren in activeParty() → a cold
  reload built from `at` alone landing in the same scene, shot and place. Every other
  gate in this repo was green on 2026-08-02 while the game had no chapter in it; a
  suite of green unit gates cannot tell you the thing is not a game. This one walks it.
- **node tools/findability_test.mjs — THE FINDABILITY GATE** (no browser, no network,
  0.4 s): for every villager, the shot whose BAND owns their post, their own body box
  projected into that camera, and depth.png asked whether those pixels survive the plate —
  plus every story beat's trigger ground. FAIL for anyone the story names, WARN for an
  ambient villager. It exists because Poppy was 100% behind her own stall canopy with every
  gate green, and the user could not complete Chapter One's first objective: A TEST THAT
  TELEPORTS TO A COORDINATE AND CALLS `Npc.talk()` BY ID DOES NOT PROVE A HUMAN CAN FIND THE
  PERSON STANDING THERE. Her record even read "Verified on the walk network, not by eye" —
  that sentence WAS the defect. QA docs/qa/findability/index.html.
- node tools/dialogue_test.mjs — THE CAST GATE (no browser, no network): every speaker
  has a bust §2, resolves to a cut-in or a thumbnail with the alpha MEASURED IN THE PNG
  §2b, and the PARTY has a face on every beat the player speaks — choice lists
  included, since a choice is the one line the player authors §2c. Also bodies, posts
  and arrival clearance.
- tools/cine_sweep.mjs — WHICH ANGLE SHOULD THIS SHOT BE AT. Calls the shipped solver with
  yaw/pitch overridden and ray-casts the result against the walk bundle's own triangles
  (BVH, no Blender, ~3 s for 468 angles x 7 shots), so "does the region fit" and "can the
  camera see it" are one answer. `--fov/--margin/--maxdist/--cameras` sweep the knobs and
  proposed shot lists. A SCREEN, not a verdict: the bundle is the blockout, and the bake's
  ray-cast against the dressed master is still the only visibility oracle.
- tools/nav_eval.mjs — perceptual navigability (judge PINNED gemini-3.6-flash; noise
  ±0.20/shot at N=5 → N=10 for per-shot claims). Viewer: docs/qa/naveval/viewer.html
- tools/plate_flat.py — background-leak audit.
- **tools/three_shots.mjs --shots <json> --outdir <dir>** — the same viewpoint list
  photographed across SEVERAL scenes in one Chrome, so a look change can be replayed
  against two builds (serve an old tag from a `git worktree` on a second port) and the
  only thing that differs is the build. Captures the console with the run — a shader that
  fails to compile still screenshots. Pair with **tools/shot_compare.mjs <dirA> <dirB>**
  (L05/L50/L95 + chroma per frame). NUMBERS FOR ITERATION, PICTURES FOR THE VERDICT: the
  r185 arena regression passed all 1900+ assertions in this list.
- tools/walk_bodygate.mjs — body-box step gate: can a character actually get from one
  walk sample to the next? Reproduces play3d's walkStep() at its own 0.075 m stride
  (ray gates see headroom, not bodies). A calibrated SCREEN, not a verdict — confirm
  hits with a body. It reads THE FILE — pair it with walk_engine_gate.
- **node tools/walk_engine_gate.mjs --scene <bundle> --port 3000 — THE FILE-VS-ENGINE
  GATE (real Chrome).** Censuses standable cells TWICE on one lattice: triangles out of
  the shipped GLB, and SIM.walkFloors() inside the running game. Red on any cell that is
  floor in the file and not floor for the player, and on SIM.bvh().fail > 0. Every other
  walk instrument here (walk_bodygate, glb_read, cine_solve, routes_derive) reads the
  file, which is why 209.6 m2 of Emberbrook and 54.3 m2 of Dellhollow could be
  non-collidable for weeks with every gate green: A WALK-NETWORK GATE THAT NEVER ASKS
  THE ENGINE IS MEASURING THE ARTIST'S INTENT, NOT THE PLAYER'S WORLD. `--reduced` is
  the no-browser mechanism proof (three-mesh-bvh permutes geometry.index.array in place
  while GLTFLoader shares one index attribute between primitives).
- **tools/_court_probe.mjs — A FLOOD FILL TELLS YOU WHERE THE WORLD IS SHUT AND NEVER WHAT
  SHUTS IT** (2026-08-03). `--comp` labels the disjoint components of a region in the RUNNING
  game and, at each frontier, asks `SIM.blocked` — **which returns the blocking MESH'S NAME**.
  That name is the whole diagnosis. Worked example, and it is the reason this entry exists:
  the Old Gate's court had been called a raft "0.8-1.7 m proud, past walkStep's step-down"
  for a day. The probe found `SIM.ground` CONTINUOUS across the frontier — so never a step —
  and `SIM.blocked` naming `oldgate_3`. **The whole prop was built a quarter turn out**:
  every cube in `build_old_gate` is sized (along river, across notch, height) but `rz` took
  `nl`'s angle, sending local X ACROSS the notch. "One wall across the pinch" was four
  detached piers standing ALONG the gorge, and the nine deck bays stacked into a single
  0.42 m strip — six cells on a 0.4 m lattice. A plank, not a step.
  **AND THE BUILDER'S OWN GATE COULD NOT SEE IT**: its seal blocks the wall's *intended*
  footprint analytically, so it printed `flood fill past the pinch 0 cells` over a gate made
  of piers, every build, for weeks. Same class as walk_engine_gate — **A GATE THAT MEASURES
  ITS OWN DRAWING CANNOT MEASURE ITS OWN BUILD.** Fix was two derivations and no new massing
  (`ang = atan2(tg)`; deck paving takes z from `VM.ROAD_Z`): 3 components -> 1 of 712 cells,
  `SIM.move()` 27/27 legs BOTH ways, and **`playthrough_test` 80/1 -> 81/0** — the long-
  standing `ch1.done -> ch2.road` §W red WAS this gate.
- tools/scene_redteam.mjs — LLM scene critique (naive + map-informed checklist modes,
  adversarial verify; judge PINNED, shares GEMINI_API_KEY). Calibrated 4/5 hand / 2/5
  matcher on the user's own annotated complaints (sweep 2; was 3/5 — the gate rows moved
  because 96114cc recomposed the shot, not because the judge changed). Stage 2 filters weak
  criticism, NOT confabulation — triage survivors by eye, and MEASURE before building.
  `--replay a,b` (newest first) merges runs into ONE report and every plate records which
  run judged it; `--plates` pins the bake and stale shots self-mark against-superseded-bake.
  CURRENT: docs/qa/redteam/run-20260731-dellhollow2/index.html — all 16 Dellhollow plates
  (:3000/docs/). Emberbrook is UNSWEPT: its blockout frames die to the dressing pass.
- RED-TEAM FIX LOOP (user-ratified workflow, run on their ask): judge finds a flaw →
  MEASURE the claim on an instrument (geometry_audit --region / ray census — never
  build from an unverified perception; see the pink-plank confabulation) → builder
  fixes → re-bake → re-judge; stop after K consecutive clean rounds, pin findings to
  bake stamps (plates going stale mid-loop is a measured failure mode). At 3/5 recall
  a clean round means "the visible part is clean," not done — it is not the review gate.

## Character factory (pipeline order; docs in each tool's header)
1. tools/gen-character.mjs (busts/expressions; config tools/characters/<name>.json)
1b. tools/gen-cutin-art.mjs — draws each portrait FOR the matte: chest-up on a flat
    magenta key, identity anchored on bust.png, expression sets from
    tools/characters/cutins.spec.json (the cast's emotional coverage; `rest` is a
    CHARACTERFUL at-rest face per VOICES.md, never deadpan). Studio plates are
    gitignored; the matte is what ships.
1c. tools/gen-cutin.py — mats that art into cut-in portraits (chroma key; the old
    bust-salvage path stays as the fallback) + public/assets/characters/cutins.json,
    the manifest dialogue.js picks cut-in vs framed-thumbnail from. ROLLOUT IS GATED
    AND ATOMIC PER CHARACTER on tools/cutin_edge.py (edge_noise/halo/ramp/speckle/
    pinhole) plus a NO-REGRESSION floor: a set that would lose a scripted or
    already-shipped mood is refused and the character keeps today's art.
    QA docs/qa/cutins/index.html — every plate over a baked plate, read ACROSS a row
    for identity drift. Baseline before the pass: 19/62 plates passed the gate.
    **`cutin_edge` STILL HAS NO CHROMA TERM — the hole is OPEN** (2026-08-03). Its `halo`
    is a LUMINANCE difference, so a rim of the wrong HUE at the right brightness is
    invisible to it: a bright chartreuse outline sat on **79 of 112 SHIPPED plates**, every
    one gate-green, until someone LOOKED. Cause was in the despill, which estimated key
    share by summing the R and B deltas against the local opaque reference — so a
    legitimately brighter edge pixel read as magenta residue and the subtraction drove R
    and B under G. Fixed by solving the mixture on the key's own chroma axis,
    `(R+B)/2 - G`: 79/112 → 20/119, magenta residue unchanged or lower everywhere.
    THE GATE ITSELF WAS NOT FIXED. Until it grows a chroma term, a green/cyan/magenta
    fringe can ship gate-green again — A GATE THAT MEASURES BRIGHTNESS CANNOT SEE COLOUR.
    **RE-ROLL `rest` FIRST, NEVER LAST**: `rest` is the identity reference the mood plates
    are drawn from, so re-rolling it after them orphans the set against a superseded
    reference (sorrel's striped apron went plain white, her peel wood → terracotta). The
    chain IS the identity.
    **THE TWO RUNTIMES DRAW DIFFERENT ART**: 2D (chapter1/2) uses `expr-*.png` busts, 3D
    uses `cutin-*.png`. 15 scripted moods exist in one and not the other — LATENT, not
    live, because they sit only in story.json. Lake's 2D busts were still the RETIRED
    design (black hair, green vest, cape) against a ratified brown-haired, red-vested
    bust.png, so his neutral line showed one man and every emotional line another.
2. tools/gen-turnaround.mjs — A-pose 4-view sets (style anchor = user's Vesper A-pose;
   hands empty; capes swept back)
3. Tripo (user via web, or tools/gen3d.mjs API) → GLB
4. Intake gate: joint×IBM≈I probe; repair via tools/vesper_fix_glb.py if broken
   (Vesper's export was broken; later deliveries were clean)
5. tools/vesper_retarget.py — per-clip donors (Quaternius UAL idle/walk CC0 +
   KayKit jump), solved arm/leg offsets, per-clip arm targets; read its docstring
6. tools/vesper_verify.py gates (arms ≤15° off vertical, elbow 10–40°, hand-coat
   clearance) → MODELS registry (play3d) / npcs.json bodies
- Gen-art rules: no third-party IP names in prompts; full-scene style refs OK,
  character crops may trip filters; flat even light for mesh inputs.

## Music
- public/js/music.js + public/game/music.json; tracks public/assets/music/*.mp3
  (original, Lyria via GEMINI_API_KEY); loop points via tools/music_loops.mjs.
  Agents: NEVER audible in browser tests — ?nomusic=1 (exception: transition_test,
  which mutes at source).

## Scope rulings (user decisions that bound the work)
- **THE BATTLE FIGHTS IN THE REAL WORLD, AND THERE IS NO DIORAMA FALLBACK** (user ruling
  2026-08-08, leaning to the world arena and then ruling out the fallback outright: *"if we go
  with the world setup then we shouldn't be maintaining the diorama. Rather if we need a
  fallback, we should just fallback to the 'nearest feasible' place"*). When placement refuses a
  spot, RELOCATE WITHIN THE WORLD — do not switch arenas. Their reasoning, which is the durable
  part: **the diorama is itself a teleport, to a generic place the player will never see again,
  so moving 100 m to somewhere they recognise is STRICTLY BETTER than a parallel universe.**
  DISTANCE IS THEREFORE NOT THE CONSTRAINT — the search radius is whatever gives full coverage.
  I argued against this by invoking the story layer's no-teleport rule and WAS WRONG: that rule
  governs BEATS (so narrative cannot skip the walk between towns), not where a modal battle
  stages. What still binds: teardown stays total (the player is returned exactly where they
  were), and maintaining two arenas is what produced the two-lighting-models defect in the first
  place. NOTE the measured baseline this ruling acts on: the 64.4% staging rate ALREADY includes
  an 11 m nearest-feasible walk, so "search further" is the lever, not a new idea.
- **SINGLE-PLAYER FOR THE PROTOTYPE** (user ruling 2026-08-02, verbatim: "Let's leave the
  two-player version of the game as an upgrade for later, and in the prototype we can keep
  things as single-player"). The 3D runtime is single-body and STAYS so. Chapter One's climax
  (two keepers on twin sigil plates) and Chapter Two's (a six-hand winch) are staged as
  single-player + companion so nothing soft-locks. DO NOT re-open this as an open question —
  it was carried on a status list as "undecided" for hours after it had been decided, which is
  its own small lesson: a ruling that is not written down is a ruling that gets re-asked.
- **LAKE IS A PARTY MEMBER**, not a narrative-only companion (settled 2026-08-02: the user
  refers to "Lake as a party member", and growth.json already carries his record with
  `joinFlag: lake-joined` and stats). His `joinFlag` stays.
- **DELETE SUPERSEDED WORK, DO NOT ARCHIVE IT** (user ruling 2026-08-02, emphatic, given
  twice). They asked for a repo cleanup in the morning and repeated it in the evening:
  "I emphatically disagree with this, we should be deleting stuff - that's exactly what I
  asked for this morning when I said to clean up the repo". THIS OVERRIDES the
  agent-authored policy in public/game/scenes.js ("Deprecate by MOVING a group down, never
  by deleting; bundles stay on disk and in git") — that line was never a user decision and
  must not be quoted back at them as though it were. It also overrides the reflex, twice
  displayed by me, of answering a delete request with "deleting gains nothing because the
  blobs stay in history": TRUE ABOUT SIZE, IRRELEVANT TO THE ASK. A tree full of superseded
  bundles costs comprehension, misleads measurement (the 3.2 GB "deployable" figure was
  mostly dead scenes) and invites work against dead art.
  WHAT STANDS: the three-way verification METHOD (referenced by no file, named in no doc,
  inert by its own header) is still how a deletion is made safe. Verify, then delete —
  do not verify, then find a reason to keep.
- The goal is A PLAYABLE PROTOTYPE, not a polished product (user steer 2026-08-02) — prefer
  the 80/20 that gets the thing playable over the round that gets it perfect.

## Working rules (hard-won)
- Git: stage-and-commit one breath WITH pathspec on the commit; never `git add -A`
  (shared index across agents). PUSH REGULARLY (user standing order 2026-08-01): the
  coordinator pushes migration/3d-hybrid to origin after each substantive batch —
  not necessarily every commit, never less than once per work session. VERIFY the
  push with `git ls-remote --heads origin <branch>` — never trust a piped exit code
  (the 2026-08-01 3.3GB first push died on GitHub's ~2GB pack limit while reporting
  success through `| tail`; big pushes go in fast-forward chunks). SAME CLASS
  (2026-08-01): `<cmd>; echo EXIT=$?` makes the shell's status the echo's — a failed
  Blender rebuild reported "exit 0" to the harness all session. No trailing echo
  after commands whose status matters; the last command IS the status. The proof of
  any build is the ARTIFACT (mtime, digest, SAVED line), never the report.
- Blender: always `-b --python-exit-code 1`. Builders deterministic — gate is a
  SHA-256 CONTENT digest (world verts to 1e-5 + materials + lights + camera), NOT
  byte-compare (.blend serializes memory addresses; see tools/embint_verify.py).
  Disk: clean temp renders/profiles every run. A bake that SIGABRTs deterministically
  at render start on ONE camera while others pass is the Metal kernel cache corrupting
  (.ips names ccl::MetalKernelPipeline::compile / free_tiny_botch): quarantine
  /var/folders/*/C/org.blenderfoundation.blender and rebake — no free-RAM gate cures it.
- Browser verify: foreground tab for rAF/screenshots (osascript Chrome activate);
  hidden-tab canvas screenshots go stale — trust SIM readPixels probes.
- emb-townwalk ships the DRESSED realtime tier (emberbrook-realtime.blend): any lane
  that rebuilds the MASTER owes a dressing re-run (emb_dress --tier realtime --out)
  in the same window, and anyone who rebuilds the REALTIME blend must re-run
  emb_decimate --save (the decimation is baked into the blend, deliberately — an
  export-time-only decimation would be silently undone by the cron's next tick).
- Blender datablock rule (three paid instances: save_render, im.scale, decimate):
  EDITING A DATABLOCK IS NOT EDITING THE ARTIFACT — any consumer that re-reads from
  disk needs the edit written out and the datablock repointed; the only proof is
  measuring the artifact, never the log.
- **A BACKTICK INSIDE A CSS COMMENT ENDS THE TEMPLATE LITERAL** (2026-08-02, hit
  INDEPENDENTLY by two lanes within one hour: ui_kit.js:122 and battle_turnbased.js:207).
  Every UI module keeps its stylesheet in ``const CSS = ` … ` ``; writing a quoted word
  like `` `sm` `` in a comment inside it TERMINATES the string, and the file becomes a
  SyntaxError. HEAD parsed, the working tree did not — it crashed economy_test and
  encounter_sim outright. The nastier half: a module that fails to parse still LOOKS
  present, and since every module self-arms at load AND on 'eb-scene', a parse error is
  invisible until an in-place scene swap silently leaves the module absent.
  transition_test's console gate is what catches it. Use plain quotes in CSS comments.
- **AND A BACKTICK INSIDE A DOUBLE-QUOTED `git commit -m` RUNS AS A COMMAND** (2026-08-03,
  paid immediately after writing the bullet above). Committing a message that quoted a word
  in backticks made zsh execute it: the shell printed `command not found`, the word was
  substituted OUT of the message, and THE COMMIT STILL SUCCEEDED AND PUSHED — a silent
  edit to the permanent record, with a nonzero-looking error that belonged to a
  subshell rather than to git. Same root as the CSS-comment trap: a backtick is live
  inside double quotes wherever it appears. **Use single quotes for commit messages, or
  a heredoc.** Do not amend a pushed shared branch to fix cosmetic damage — rewriting
  history other lanes have fetched costs more than the missing word.
- **A GENERATOR THAT UNCONDITIONALLY RE-ASSERTS A NUMBER A LATER CARRIER OWNS IS A TIME BOMB**
  (2026-08-08, measured). `t2_cliff_south.derive_material()` set `mat_rock_townwall`'s Mapping
  rotation to 90° and scale to 1.05 on EVERY run, under a comment reading "Idempotent" — it was
  idempotent with respect to itself and not with respect to the world. The shipped material
  carries rotation 0 / scale 0.55, put there by `tools/t3_rock_projection.py`, which had already
  MEASURED that rotation as the cause of the judge's "severe vertical texture stretching" on
  loop-stairs/lockhead/cottage. So re-running the wall's own builder silently reverted the fix
  for the defect it was being re-run to help, on three plates: 15.3% of lockhead and 13.5% of
  loop-stairs changed and the wall came back as hanging vertical strands. **THE ONLY TELL WAS A
  PICTURE** — no gate, no digest and no log line said anything. Seed a value on CREATION and
  print what you find thereafter; two tools may not both own one number. Also why a REPRO GATE
  belongs before any edit to a live generator: re-running t2_cliff_south unchanged moved 42 of
  5,960 vertices by up to 0.30 m (its clearance ray-cast is a function of town geometry that
  has moved since), so it is faithful to within a measured bound and is NOT a pure function.
- **IF YOU HOLD A MASTER EDIT ACROSS A CRON TICK, YOU HAVE PUBLISHED IT** (2026-08-05,
  measured). `tools/townwalk_live_refresh.sh` exports the SHARED explore bundle
  (`public/assets/scenes/townwalk/scene.glb`, the `walkSceneKey` every town's `cine_solve`
  reads) straight from `dellhollow-master.blend`. A lane holding an unstaged experiment in
  that master had it exported into the shared bundle by the 11:05 tick — 31 walk records of
  a stair that was about to be reverted. `cine_test` caught it as bundle parity (312 vs 313
  walk meshes), which is the only reason it was not committed by somebody else.
  **AND `git checkout` IS THE WRONG REFLEX**: the committed copy of a cron artifact is
  itself older than the master, so restoring it just swapped one mismatch for another
  (it was missing `walk_e_weave-huts__moorage_l2_t04/t05`). The fix is to RE-EXPORT it from
  the master you intend to ship (`tools/town_export.py`). An uncommitted master is not
  private; stage or revert before you walk away from one.
- **A TEST THAT CANNOT BOOT IS NOT A TEST THAT FAILED.** transition_test exits 13 at
  `== BOOT` while any lane (or the townwalk refresh cron) is mid-write on
  public/assets/scenes/townwalk/scene.glb (~51 MB) — the boot gate waits on that asset.
  Re-run once the export settles; do not read it as a regression, and do not "fix" code
  against it.
- **`git commit -m … -- <pathspec>` COMMITS THE WORKING TREE AND IGNORES THE INDEX**
  (2026-08-03, paid for across three lanes). A lane staged ONE hunk with `git apply --cached`,
  then committed with a pathspec — the pathspec form re-reads those paths from the WORKING
  TREE, so it published 309 insertions of two other lanes' in-progress edits. The repair then
  diffed against the base it started from rather than current HEAD and reverted a third lane's
  committed beats out of HEAD. Nothing was lost (restored byte-identical, sha-verified) but
  ORIGIN WAS BRIEFLY RED and two lanes had 20 minutes of work committed under another's name.
  With a dirty shared tree: stage precisely, then `git commit` with NO pathspec, or
  `git commit --only <paths>`. And repair against CURRENT HEAD, never against your own base.
- Agent lanes: written handovers (transcripts expire); DAYLOG notes per phase;
  coordinator owns play3d.html, the town maps, and this file.
- Documentation bar (user ruling): notes carry AUTHORITY — a written interpretation
  short-circuits future investigation (the loop-stairs "walker pessimism" note hid a
  real defect for a day). Record measurements WITH their instruments; an
  interpretation may be recorded only alongside the instrument that proved it. High
  bar for inclusion; condense over accumulate.

## World-building doctrine (earned in Dellhollow + the Emberbrook founding; details in DAYLOG)
- Footprints live IN THE MAP; the blockout derives floors AND doorsteps from it.
  A conflict fix is a landmark move or a lane waypoint — one line of map, one
  command to re-derive. Never re-cut floors in a district builder.
- A free-standing solid is SEARCHED, never authored (ring/clearance search against
  the walk network + camera probe sets). Measure the fallback in the same pass.
- Audit geometry WHERE IT LANDS, not where it was. A standable surface is not a
  buildable volume. A bound loose enough to refuse everything is a veto, not a test.
- "In frame" ≠ "visible" ≠ "unobstructed ray": probe occluders (incl. the
  camera-inside-tree-crown case) before re-aiming; move the occluder, not the aim.
  Bake ray-cast is the ONLY visibility oracle. For dusk grades, measure GROUND
  luminance on the region probes — the floor is what has to be read.
- Night grades (Emberbrook, measured HISTORY not law — DAYLOG 2026-08-01 night lane):
  adjusting an existing light has never moved this town; adding a new source always
  has (sky ladder, lamp wattage twice, moon colour: inert or exhausted; the moon's and
  the waystone lantern's ADDITION are what made frames read). Solve a class recipe on
  the class's MEDIAN member; a plate under the 25-median floor gets its OWN two-rung
  moon slope (probe rungs at 1008x576/28spp, anchor on the shipped plate's measured
  median) — slopes ran 4.8-10.1 L/W across one town, so never borrow another shot's.
- Road ribbons stop at their own map edge's end; an edge carrying a camera boundary
  must keep walkable identity; prop-class pads size to the prop; the walk pad IS
  the doorstep.
- Interiors: separate blends via tools/embint_lib.py (arbitrary-plan walls — the
  box was in the code, not the art direction) + embint_verify.py gate; bake via
  tools/depth_bake.py (cine_solve is town-only). Ceilings stay when the camera is
  inside the room; every ray must terminate on real geometry; test the body as a
  BOX, probe floors with a 25 mm cross (plank shadow-gaps are not holes). Each
  bundle ships doors.json (which wall the door is in — the one fact derive can't check).
- Nav-eval noise is ±0.20/shot at N=5: per-shot claims need N=10; judge stays pinned.
