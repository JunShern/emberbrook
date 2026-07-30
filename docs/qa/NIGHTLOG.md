## 04:12 — Boatyard probe v11: ACCEPTED (quality gate passed)
Verdict: pilot bar met in raw render — dusk lantern bloom, vegetation (creepers = strongest),
color separation (oxblood chandlery vs green lofts + bunting), foreground work-life, hazed far
depth with far-side silhouettes. Settles the core pipeline bet: kitlib + recipes suffice; no
image-gen needed to reach presentation quality.
Coordinator ruling on the roofs question: deck-height cameras don't owe hero roof planes —
that belongs to high-camera scenes (Weave/Lockhead). Camera stays.
Carry-forwards for all detail work: KITLIB_MANIFEST items 1-17 (esp. bounded-fog-only, world
ramp lower-hemisphere trap, out-of-frame shadow casters, world_to_camera_view placement grids).
## 04:38 — Cottage interior v9: REJECTED, iterating to v10/v11
Right bones (hearth pool, green-dresser palette, warm/cool split at the river door) but: tie
beams cut the frame as black bars; upper half murky (FF9 = dim but readable); empty stage
between hearth and table. Fresh agent dispatched: beams raised/slimmed/uplit, fire 1.5x +
readability fill, mid-floor life (rug bridge, firewood, kettle arm, Mochi's basket), limewash
plaster, floorboard variation. Item-shop interior still building in parallel.
## 05:15 — Item shop v5: ACCEPTED (the shop archetype)
Shelf density, painted red/green counter, lantern pools, hanging dried fish — instantly FF9.
Two notes folded into wave 3: replace strand-nets with folded hanks; +1 stop counter key.
Dispatched: shops agent (item v6 fixes + skin refactor to data tables + weapon/armor variants,
with the dark-metal-readability warning) and inn common-room agent (wave 2a). Cookhouse (2b)
queued behind cottage v10 to cap concurrent Blender at 3. Agents running: cottage v10, shops, inn.
## 05:58 — PLAYABILITY MILESTONE: full-town grand tour 41/41 legs
Player-like walker (with human-style corrective recovery) traversed EVERY landmark end-to-end.
The path here (~2h of empirical iteration, each fix committed to data/generator so it's durable):
- wall test: walk_-only collide needs vertical-extent walls (low+high span), not any-graze
- flat features must never overhang steep ones: stairs trim outside area rims AND threshold pads
- flights must not run along/through corridors, buildings, or each other: gate stair re-sided,
  quay flights re-laid along the cliff to the deck's free north rim, moorage switchback rerouted
  east of the huts, cottage descent re-aimed, deep-stairs leg-1 relaxed (46deg post-stretch)
- hairpin switchbacks need wide amplitude so crossing legs clear vertically
- bridge takeoff swung gorge-ward off the switchback corridor
- rails exist visually (bar_) but are excluded from collision
- experimental network-collision mode (?net=town) kept behind a flag; raycast is primary
Morning validator wishlist: per-LEG slope check; corridor/flight proximity lint; flat-over-steep
overhang lint. All fixes are in map data + generator, so every future regeneration inherits them.
## 06:15 — Interior verdicts (art gate)
- cottage-int v11: ACCEPTED. Transformed from v9 — hearth pool + Mochi asleep beside it, toys,
  laid supper table, cool dusk through glazed doors vs warm room. The supper scene.
- inn-int v11: ACCEPTED w/ notes (hearth glow deserves more presence; beam stubs want warm
  uplight). LOCKS: DELAYED board, abandoned card hand, key rack, luggage — story complete.
- weapon-int v3: ACCEPTED w/ note (forge nook ember glow weak). Grindstone + polearm corner sell it.
- armor-int v3: ACCEPTED w/ note (hero harness stand deserves a spot). Dark-metal readability fix works.
- item-int v6: accepted earlier (archetype); nets + counter-key fixes reported done.
Score: 5/6 interiors at bar. Cookhouse agent (final) dispatched 06:12.
## 07:00 — Cookhouse v8: ACCEPTED — ALL SIX INTERIORS AT BAR
Bread oven glow + hearth two-height warmth, hatch + menu board, eel barrel. Notes: dining half
density, bottom-right corner lift. Exported playable (del-cookhouse-int) + hub.
## 07:06 — emberbrook.map.json drafted (town #2 in the graph system)
20 landmarks, 18 edges (all curved earth roads/paths — flat village, plan-primary), 5 draft
parcels + 4 implied interiors (item, inn, Vesper's and Lake's homes). The Heartlight encoded as
the magical centerpiece per canon (kind: heartlight). Two loops. Validator: zero errors first
pass — the tooling is town-agnostic. ALL draft-flagged for the user's morning redline; NPC
names/residents are placeholders pending chapter1.js cross-check.
## 08:05 — Boatyard district v3: playability PROVEN, art below bar, v4 iterating
The architecture headline: the first fully-DETAILED exterior preserves the town's walk meshes
byte-identically (agent QA: 0.0 vertex delta, 909/909 down-ray hits, corridors clear, headroom
clear) and browser-verified playable through the finished art (slipway->overlook, ->winch-foot,
->shed/kettle all OK). Detail passes cannot break walking — the contract holds end-to-end.
Agent also caught the p-boatyard draft camera facing 180deg wrong (yaw 170 = downstream);
adopted its correction (yaw -12) into the map. Art verdict on v3: below probe_v11 bar — blown
lock-house window, Lock Four reads white-concrete not black stone, amber-monochrome, timber-soup
values, shingle seams. v4 agent dispatched with the punch list.
## 08:55 — Boatyard v10: ACCEPTED with notes (first detailed exterior COMPLETE + playable)
Measured fixes: dam now black-stone + dark timber gates w/ iron banding (the 'concrete' was
whitewater sheets + a gloss floor reflecting sky); lock-house window de-clipped (emission 90->
6.8-10.5 w/ sill gradient); warm/cool split +0.011 -> +0.113; shingle 'seams' were moss skipping
course risers (normal-Z mask) — fixed; median luma 0.571 -> 0.479. Walk contract re-verified
after re-export (14/14 byte-preserved, 909/909 rays, QA PASSED). Notes for the user gate:
mid-ground timber values still uniform-ish; lantern bloom pools shy of probe_v11; frame denser
than the probe's open sky (honest trade, not faked with exposure). Interiors polish agent
(inn/weapon/armor/cookhouse notes) still running.
## 09:35 — Notes-polish complete: all four rooms (inn v12, weapon v4, armor v4, cookhouse v9)
Every note closed with measured diffs (weapon's 'dim' forge was 93%-clipped white — now 27%;
armor harness gets dais + spot rake; inn hearth grew 26% hot area without clipping; cookhouse
corner tiles lifted 5-13 -> 25-46). Bundles re-exported; spot-checked del-inn-int + del-armor-int
still playable. NIGHT QUEUE FULLY DRAINED — remaining work is the user's taste gates.
## Morning session — testing-gap incident + fixes (user-caught)
User caught three player-facing bugs my tests missed: invisible character in interiors,
oversized sprite, walk-through furniture. ROOT CAUSE: play tests were numeric-only (positions/
displacement), art tests were character-less renders — nobody ever tested THE PLAYER'S FRAME,
and no test asserted negative space (blocking). Fixes shipped:
- interior exporter strips runtime occluders that render-time hides (visible_camera, hide_render,
  hide_viewport, fog, shadow_ceiling — each agent hid its cutaway differently) and auto-generates
  bar_ furniture blockers from footprints; bar_ = wall-check only, never drawn, never occludes.
- sprite plane 2.6 -> 2.05 (true 1.7u contract); interiors spawn at walk_pad_door (center = behind counter).
- townwalk gets ?rt=1 real-time explore mode w/ follow camera (fixed wide shot was unplayable).
- NEW STANDARD GATE: tools/playframe_test.js — visibility pixel-diff, scale %, 4-side blocker
  penetration. It immediately caught the item-shop spawn-behind-counter and a second cutaway-
  hiding mechanism. Remaining refinement: a few blocker-penetration edge cases in dense rooms.

============================================================
NIGHT 2 — 2026-07-30 04:42 — overnight shift begins
============================================================
Plan (user-ratified):
  SERIAL: 1) vertical slice (game wiring + enter/exit prompts)
          2) workspace tidying (objective items)
          3) Dellhollow camera-scene navigation (full coverage, creative freedom)
  PARALLEL: quay-market tier custodian (non-blocking); foliage agent completes
          atlas + line-up + FULL valley integration for morning review.
  RULES: timekeeping here; never idle — after all tracks land, test & polish
          gameplay smoothness until the user returns; taste calls shipped only
          where explicitly granted (foliage, cameras); no pushes to main.
04:42 slice agent + market custodian launching; foliage agent being
        handed the pipeline back with integration orders.
04:49 user addendum: active supervision (design-review agents' plans,
        red-team for scalability+quality) + refinement-first architecture (data-
        driven skeleton, layered quality passes). Canonized in MIGRATION.md.
        Supervision messages sent to all three agents. User logged off. o7
05:04 slice: read canon + runtime. Coordinate truths MEASURED, not assumed: town map
        pos[x,y,h] -> runtime (x,h,-y); region pos -> runtime (x-140,h,100-y) (valley_map
        CX,CY). All 25 townwalk walk_pad_<id> centers match map-derived coords to 0.02u, so
        the MAP is the single source and the GLB is only a cross-check. Interiors ship
        walk_pad_door + no depth spawn (they already spawn on the door). Design message sent
        to main for red-teaming; building tools/scenegraph_derive.mjs + tools/glb_read.mjs
        (Node GLB reader: node world matrices, AABBs, down-ray over walk_ tris) meanwhile.
04:51 SLICE design review round 1: approved with 3 changes — explicit
        region sceneKey shipped in map data (kills its one assumed convention);
        transitionTo() seam demanded (full-page reload = designated refinement
        point); spawn-edge choice made geometry-deterministic. Verb templates,
        radii, arm/disarm blessed. Agent proceeding to generator.
04:51 MARKET: baselining + plan being written (36 calls). FOLIAGE:
        deep in iteration (178 calls) — de-tiling rock, densifying fronds; shelf
        terrace render underway.
04:54 MARKET (p-quay-mkt) PARCEL PLAN — measured first, written before any build.
        BASELINES RECORDED (live master, pre-touch): full walk QA 367/367
        bit-identical, 1308/1308 rays, headroom warning yard_ground 3 samples
        (0.23%). Region x 28..66 / y 10..20: 1614/1622 rays (99.51%) — the 8
        blocked are lm_notice-board x2 (MINE) and wv_hut_weave-north_2 x6 (the
        WEAVE's hut standing in walk_pad_weave-north; not mine to delete, filed as
        a finding). geometry_audit same region: 144 meshes, 0 intersection
        offenders, 0 strays.
        THE TIER'S OWN NUMBERS (measured, not taken from the parcel's z bounds):
        floor z = 14.00 (every market pad reads 13.92..14.04, the quay-deck and
        market-stalls slabs 13.99..14.24). Parcel volume is x 30.7..63.6,
        y 6.5..21.5, z 12.5..17.5 — the brief's y/z are transposed against the map,
        and the map is the authority.
        THE FINDING THAT SHAPES THE DISTRICT: the market tier has NO GROUND under
        most of itself. Vertical sections show that south of y=12.5 there is
        nothing at all below shelf_ground's underside (17.37..18.61) — the shop
        street above is a PLATE OVER VOID (shelf_lib says it in as many words:
        "east of MASS_X the MARKET tier is underneath and it is a plate"). North of
        y=12.5, wf_ground rises to 13.6..14.9 and the walk ribbons sit 0.1..0.45 m
        above it, so that half is bedded; past y~17 the deck oversails the Weave's
        huts by 6..8 m. So the district is, structurally: an ARCADE UNDERCROFT
        carrying the shop street's plate, opening north onto a TIMBER HARBOUR DECK
        over the gorge. That is also the FF9 image the map's intent asks for.
        LANDMARK TREATMENT
        * quay-deck (plaza x 47.9..58.9, y 8.5..19.5) — the subject. Paving on the
          bedded south half, planking on joists + piles over the north half, piles
          ray-placed onto wf_ground only and dodging wv_hut_* entirely.
        * cookhouse — moved OFF its pad and NORTH of it (findings 93/111): body
          x 37.4..42.4, y 12.95..15.60, door south onto walk_pad_cookhouse, tall
          north front with lit windows over the gorge ("warm windows over the gorge
          at night" is the map's own note), lean-to roof rising north so its south
          eave stays under the shelf's rim and under the veg_shelf_creeper_* that
          hang to 16.88, chimney at the north gable in open sky + fx_qm_smoke. Its
          walk_pad and the interior's walk_pad_door contract are untouched.
        * notice-board — THE INHERITED WIN. The lm_ shell stands dead centre of its
          own pad (board 47.8..48.6 / 11.6..12.4 inside pad 46.9..49.5 / 10.7..13.3):
          2 blocked walk samples + an 8-sample headroom warning, both pre-existing
          and blamed on nobody. Deleted, rebuilt as a real landmark on the pad's
          SOUTH edge facing +y — hooded board on posts, LOCKS: DELAYED nailed up
          (the fiction lives here).
        * market-stalls (plaza x 56.1..62.1, y 10..16) — awninged stalls round the
          plaza's edges, produce / crates / fish, the walking lines left clear.
        * deep-stairs-head — its three lm_ shells (two posts + a lintel) stand IN
          the pad as well; replaced by a stairhead gateway set clear of it, plus the
          rock flank the deep stairs need (they currently descend 8.5 m through open
          air).
        STYLE: painted timber, bunting, ordinary lanterns (no Heartlights).
        Materials DERIVED from the town's textured set (findings 95/105), with
        vertex-colour cloth wherever a noise tree would have been used (the
        glTF-survival gate).
        PHASES, saving at each boundary: 1 ground+undercroft+deck, 2 landmarks,
        3 dressing (awnings/bunting/lanterns/veg/clutter), 4 qm_light.py,
        5 gates+renders+findings+commit, 6 p-lockhead if the window allows.
        DEVIATION FLAGGED TO MAIN: the undercroft's piers/arches stand UNDER
        SHELF_DISTRICT's plate — additive and non-modifying, but it is structure
        abutting another parcel's accepted art, so it goes to red-team before it is
        built. Everything else follows the shelf/weave pattern exactly.
04:56 SLICE: generator live (8 nodes/14 edges, 6s); walkSceneKey granted
        into dellhollow map (role-as-data beats depth.json inference — its first
        run resolved the town's walk scene to del-boatyard, exactly the failure
        the field prevents). Proceeding to runtime block.
04:56 MARKET: red-team round — approved the ARCADE UNDERCROFT under the
        shop-street plate (measured contact at build time, cross-parcel build
        order documented, SAME_ASSEMBLY registered, 30-50mm shy stance). First
        inter-district structural dependency in the master.
