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
04:07 FOLIAGE: the ATLAS, which is 80% of this task. All three earlier valley
        forests failed on the same primitive — a rotated ellipse with a radial
        ramp, stamped 2400x a cell — so the failure was never the geometry.
        tools/foliage_atlas.py RENDERS each cell instead: a dome of leaf sprays,
        lanceolate blades with a midrib fold, z-buffered with real per-pixel
        normals, all lit by ONE key + sky + depth AO + translucency. 16 cells
        (8 big clumps / 8 edge fuzz), 256px each, ~35s, one-off. Judged at 200%
        three times; fixed sky showing through the middles (an opaque backdrop
        at 0.80 of the silhouette, rim still leaf-made) and near-black buried
        blades (AO floored at 0.40) before building any geometry on it.
04:25 FOLIAGE: LINE-UP shipped as the taste gate — tools/blends/foliage-lineup.blend
        on the OLD tree line-up's hillside, three shell densities + a strata-vs-jitter
        rock pair, plus the chase rig's own 35deg camera. Committed early (4b36e28).
        Bugs the renders caught: face offsets must count VERTICES not batches (it
        renders as huge plates and looks like a sculpt bug), and the shell must
        stand its cards' CENTRES outside the core or the mass reads as mossy
        boulders with leaves on top.
04:40 FOLIAGE: region recipe measured off-pipeline (tools/foliage_stand.py, a
        synthetic 662 u2 stand + a fake ZoneGrid) while the geography session held
        the files. Density swept 1.4/0.9/0.55; bigger cards + a darker core bought
        1.4's read at 1.0. glTF gate PROVEN on my own scene first: MASK survives as
        PNG, normals carried, and NO TANGENT attribute is emitted — so normal maps
        cost zero geometry bytes. That gate is also what caught COLOR_0 min==max
        ==0.521 over 28k cards: the shell AO was doing nothing and multiplying the
        whole atlas by a flat half, which was the murkiness three rounds of
        re-lighting had chased.
04:53 FOLIAGE: INTEGRATED into ow-valley. Five-line diff in valley_build.py, old
        build_canopy retired, every parameter a named module constant. Wrapper
        green first try and on all three runs since: 0 white of 24 primitives, both
        MASK materials keep a PNG baseColor, COLOR_0 on 24/24, and EVERY walk
        ribbon clear with 0 pierced verts — the pre-existing walk_dockpath +0.053u
        puncture went with this pass's 27% gentler crag gradients. Crag re-weighted
        SPECTRALLY (19u/7u/2.3u + bedding terraces, AMP_TRIM holding the amplitude
        exactly): relief surviving a 7.5u blur 0.68 -> 0.83. Meadow derived from two
        photos on inverse-FFT tiling noise after a sum of sinusoids gave first
        corduroy then a cross-hatch. GLB 28.52 -> 33.03 MB for the whole pass,
        under the 45 MB line with the 9 MB of levers unspent. Records:
        valley_record_{shelf,midvalley,gorge}.png. Findings section E (11 entries).
05:01 FOLIAGE COMPLETE, integrated, wrapper green, byte-identical twice.
        Root cause finally named: all three failed forests shared ONE texture
        primitive (rotated ellipse + radial ramp); the new atlas RENDERS layered
        leaf sprays with per-pixel normals (failed its own 200% test twice
        before passing). Bush-language masses on all three canopies; +4.5MB
        (~35 total, levers unspent); the old dockpath pierce cleared itself via
        gentler crag gradients. MORNING REVIEW: valley_record_midvalley.png,
        valley_record_shelf.png, foliage_lineup_density.png; knobs: density,
        autumn ratio, grove greens (flagged limey).
05:01 coordination notes: its one pre-standdown rebuild (03:57) explains
        part of the identical-verify confusion; AND my own broad 'git add' of
        docs/qa/overworld absorbed its lineup files — the git-index rule cuts
        both ways; adopting file-exact adds myself.
05:01 its geography flag: Dellhollow impression houses stand proud of
        the NEW canyon wall (gorge record shot) — picking up the footprint
        re-conform now (pipeline free).
05:41 slice: GENERATOR + GRAPH LANDED. tools/scenegraph_derive.mjs -> public/world/
        scenegraph.json: 8 nodes (ow-valley, townwalk, 6 interiors), 14 edges, every one
        derived (region portals + enterable landmarks + door pads), _doc + defaults +
        per-edge provenance. Two map fields requested and granted rather than assumed
        (regions[].sceneKey, walkSceneKey) — the second caught a real trap: district
        bundles carry the WHOLE town's collision, so pad names resolved Dellhollow's
        walk scene to del-boatyard on the first run.
05:52 slice: RUNTIME LANDED (additive). ?sx&sy&sz arrival outranks every spawn source;
        non-modal HUD banner "Enter The Boatmen's Rest? [E]"; nearest-edge + |dy| gate;
        ARM/DISARM on arrival (load-bearing: interiors spawn ON their exit trigger);
        transitionTo() is the single swap seam; to===from is an in-place handoff with a
        reserved applyCam() for the camera agent. sgTick hangs off phys(), not loop() —
        rAF is throttled in a background tab, so a rAF prompt is untestable headlessly.
06:05 slice: FULL LOOP VERIFIED in Chrome with real collision. valley spawn -> 14 road
        legs -> "Enter Dellhollow" -> arrive townwalk at the gate (exact, on network,
        yaw applied) -> S-bend flight 19/19 -> inn prompt -> inside the inn (exit
        disarmed on arrival, arms when you step off, prompt returns at the door) ->
        out onto the shelf street 2.9u clear -> item/weapon/armor prompts raise and
        clear as you pass -> quay via the market flight 30/30 -> "Leave Dellhollow" ->
        back on the valley road facing the gate. tools/slice_test.mjs: 154/154.
        Legacy scenes: 0 edges, no banner, unchanged, no errors.
06:05 slice: 3 blockers found for OTHER owners (all named, all reproducible with
        detours off): emberbrook_5 house on the region road at spawn; Deep Stairs l2
        hairpin blocked by its own railB; shelf-homes->quay-deck flight blocked by the
        SIBLING market-stalls flight's railB (the only two shelf->quay links in the
        map, one fouls the other). Moorage itself reached (1.86u) from below the
        hairpin. Details: docs/plans/slice-findings.md.
05:22 *** VERTICAL SLICE SHIPPED (b965a53) *** — the scenes are ONE GAME:
        valley road -> Valley Gate -> town -> all six interiors -> back, with
        the user's enter/exit prompts at every door (arm/disarm proven live).
        154-assertion verifier PASS. Hub card: "PLAY - the connected slice".
05:22 slice blocker 1 fixed by me (emberbrook houses push clear of the
        road; wrapper green, slice_test 154/154). Blockers 2+3 (two bar_ rails)
        routed to the market custodian with the rail-trim pattern.
05:22 serial track advances: tidying next, then the camera-scene
        navigation agent.
05:32 TIDYING done: del-inn-depth retired, overworld proto cards retired
        (bundles kept in git), .blend1 untracked+ignored, standalone-era boatyard
        tools + river-widen one-off pruned, gallery regenerated. One self-inflicted
        lesson: regex surgery on play.html broke it — restored and redone with
        exact-string edits + node --check before commit.
05:32 CAMERA-SCENE NAVIGATION agent launched (serial item 3, the finale):
        per-camera depth-baked bundles from the live master, camera data file +
        generator-emitted silent-cut boundary edges on the slice's transition
        layer, coverage proven by simulated playthrough. Market-tier areas baked
        last (staleness coordination). Design message expected before deep build.
05:37 CAMERA design review: approved its deviation — ONE del-cine bundle,
        N cameras as per-camera art (instant in-document cuts; 330MB dup GLB
        avoided; occlusion canon intact per-bake). Conditions: cameras.json as
        single numeric source (bake AND runtime), depth-quad swap proven via GL
        readback on 2+ cameras, lazy art + adjacent prefetch, cut hysteresis
        verified. 14 cameras planned incl. the accepted boatyard v10 hero.

## 06:0x-07:xx — CAMERA-SCENE NAVIGATION: Dellhollow becomes a sequence of shots
06:05 design message to main: DEVIATION proposed — one bundle (`del-cine`) with N
        cameras inside it, not one depth-baked bundle per camera. Reasons: a
        master-baked bundle carries the WHOLE town's collision (canon), so 18
        per-camera bundles = ~860 MB of byte-identical GLB in git, AND every cut
        becomes a page load + 2108-primitive re-parse, which is a loading screen,
        not a cut. The slice agent's to===from handoff exists for exactly this.
        APPROVED with four conditions (single numeric source; re-point the depth
        quad in place + prove with GL readback; lazy art + adjacent prefetch;
        cut hysteresis with an N-crossings test). All four honoured.
06:2x COVERAGE FIRST, cameras second. Ownership is declared BY MAP RECORD
        (landmarks + walk edges, optionally a FRACTION of an edge) because
        townwalk's walk meshes are named after the records that made them — so all
        315 walk surfaces have exactly one owner BY CONSTRUCTION and the brief's
        hard requirement is a theorem, not a hope. 34/34 landmarks, 38/38 edges,
        315/315 meshes, 0 orphans, both bundles agreeing mesh-for-mesh.
06:3x FRAMING IS INTENT, NOT A TRANSFORM. cameras.json authors yaw/pitch/fov/margin;
        tools/cine_solve.mjs fits the standoff to the region's CHARACTER-HEIGHT
        samples and reports the character's on-screen pixel height, so legibility is
        measured. Arrival points (every cut, every shop door, the gate) are IN the
        fit set — "never materialise off-screen" is enforced where the standoff is
        chosen, not discovered by a test afterwards.
06:4x THE VERIFIER FOUND FOUR REAL THINGS, in order:
        (1) backing an arrival off by ARC LENGTH is wrong on a switchback — 2.4 m
            along the gate's S-bend is 0.73 m along the seam's normal, so the
            arrival landed back inside the band it came through and a promptless
            auto cut STROBES. Cure: march until clear on the normal; and on a
            hairpin, where that is geometrically impossible, HEIGHT separates just
            as well (the band's own |dy| gate). 4 of 22 seams rely on height.
        (2) a seam belongs where the geometry can hold one — the placer now SLIDES
            each seam along the window ownership allows.
        (3) TWO CAMERA CUTS INSIDE HALF A METRE. The loop stairs are 6.5 m and
            8.3 m long while dropping 5 m; a transit shot owning the flights but
            not their HEAD needed two seams inside seven metres and the placer slid
            them to 0.4 m apart. Cure was ownership, not code: the transit shot
            owns the JUNCTION too, so each flight has one seam, at its foot, flat.
        (4) the ACCEPTED boatyard v10 frame cuts its own near boardwalk — a player
            arriving from the Waterfront came in with feet below frame (y -1.13).
            The shot does not move, so the OWNERSHIP moved (split 0.30 -> 0.52).
07:0x tools/cine_visprobe.py — "does it FIT" and "can it SEE" are different
        questions and only the second needs the town's 1900 objects. Probed all 18:
        gate-stair 4.2% VISIBLE (buried behind the inn), shelf-west 37.5%,
        waterfront 36%. Swept yaw/pitch grids and re-aimed all three (88%, 94%,
        80%). CALIBRATION THAT MATTERS: the human-ACCEPTED boatyard v10 frame
        scores 50%, because probes sit on every walk mesh's corners and a scaffold
        town occludes its own corners — so 50% is the bar, not 100%, and the four
        shots between 52% and 69% are left alone with their numbers reported.
        shelf-west's swept best came back at yaw 140 — the map draft's OWN yaw.
        The draft was right and my adjustment was wrong.
07:1x quay-east floored at minDist 18 m: the market's one stall pad FITS from
        10.8 m, and a camera 10.8 m from a market is standing inside it — and the
        quay-market tier's stalls are not built yet, so the frame must hold geometry
        that did not exist when it was solved.
07:2x COMMIT 341981e — code + data + verifier (art follows). CONCURRENCY NOTE: the
        quay-market custodian landed a master edit at 06:26 and re-exported townwalk
        at 06:30; bake4 started 06:31 so it reads the CURRENT master. Coverage
        re-checked against the new walk export: still 315/315, 0 orphans — walk_
        meshes are canonical and the custodian did not touch them, exactly as the
        protocol says. Only `gate/bg.png` (rendered 06:18) predates that master edit
        and is re-baked at the end.
07:05 MARKET (p-quay-mkt) BUILT AND GATED. The tier is a REVETMENT TERRACE, and
        that was measured, not chosen: south of y=12.5 there was nothing at all
        under this tier (the shop street above is a plate over void — shelf_lib says
        so), north of it wf_ground is within 0.10..0.45 m of the floor, and past
        y~17 the quay deck oversails the Weave's huts by 6..8 m. So: a masonry
        bench whose back wall is an ARCADE carrying the shop street's outer half
        (bearing measured off shelf_ground/shelf_paving at RUN TIME, 16.93..17.73,
        cut 40 mm shy — red-teamed and approved with 4 conditions, all met), a
        stone-paved market floor under it, and a timber harbour deck on 17 piles
        out over the gorge. Landmarks: the cookhouse moved OFF its pad to the tier's
        north edge with a lean-to roof rising into open sky and 6 lit windows over
        the drop + fx_qm_smoke; the notice board off its pad with LOCKS: DELAYED
        nailed up; the Deep Stairs' gateway off its pad; 7 searched-for stalls with
        awnings, produce and fish; 40 pennants, 10 lanterns, 80 plants, 24 clutter
        groups. 134 objects in DIST_quaymkt*.
        GATES vs BASELINE. Full walk QA 367/367 bit-identical, 1308/1308 rays
        (100%) — unchanged. Region x28-66/y10-20: 1614/1622 (99.51%) -> 1616/1622
        (99.63%); the +2 is lm_notice-board's blocked samples cured and its 8-sample
        headroom warning gone; the remaining 6 are wv_hut_weave-north_2, the WEAVE's
        hut standing in walk_pad_weave-north, not mine to delete. geometry_audit
        0 offenders / 0 strays (from 0/0, with my assemblies registered per finding
        79). glTF round trip: 22 district-owned materials, 0 white, 0 inherited
        debt. Light: 5 KEYQ_quay spots at 26% of KEY_slip's peak, spill 0.00% on ALL
        NINE accepted checks (Boatyard/Waterfront/shop street x2/gate arch as
        points, Boatyard/Waterfront/shop street/Locksfoot as region means, shared-rig
        basis), practical density 1.189x the accepted Boatyard's walking surface
        against a 1.20 bar.
        RAILS (the slice agent's two): both trimmed via master_rail_trim.py with a
        NEW documented criterion (FOULING, finding 226) applied to those two only
        via --only; the same criterion finds 11 more in five other districts, which
        are reported for their owners rather than silently trimmed. Applied to BOTH
        dellhollow-master.blend and dellhollow-town.blend identically + reference
        cache cleared: walk QA still 367/367 BIT-IDENTICAL.
        14 findings claimed, 222-235; ledger next-free now 237. p-lockhead NOT
        built — Locksfoot already built its ladder, deck and piles, the only gray
        left is one 8-vertex lm_lockhead standing in the pad, and every direction
        out of that pad is taken by a walk, so replacing it needs either a map edge
        or a taste call on whether Odessa has a hut. Measured prep written to
        docs/plans/lockhead-prep.md with the recommendation.
07:35 MARKET wrap-up. Run-twice idempotency VERIFIED: two consecutive
        qm_build.py --save passes both land 132 objects (31/2/19/80 across the four
        DIST_quaymkt collections) with the deletions manifest holding 6 and removing
        0; a third defect found and fixed on the way — the build removed lamp
        OBJECTS but left their light DATABLOCKS, so re-runs were minting
        `KEYQ_lantern_hang_7_light.001` and lamp names were a function of how many
        times the script had run. THE SHIPPED BUNDLE, not just a scratch round trip:
        public/assets/scenes/townwalk/scene.glb (cron-refreshed 07:01 from this
        master) parses to 2310 primitives, **0 effectively white**, all 19 mat_qm_*
        materials present — the same measurement that reported 0/2108 after the
        survivability pass. Final gates re-run on the finished file: 367/367
        bit-identical + 1308/1308, region 1616/1622, geometry_audit 0/0, glTF 22
        owned materials 0 white. Two camera failures kept as the record: there is NO
        gorge shot for this tier — east of x=42 the bench is bedded on wf_ground
        which hides its own underside, and west of that the Weave owns the volume
        (huts z 3.7..13.7 through y 15.8..23.3, dye lines z 7..11.6), so both a
        gorge camera and a closer deck-level one render the Weave. The support claim
        rests on the audit, and the frames document the town's tightest vertical
        stack: this deck sits 0.5 m over a weaver's ridge.
07:30 *** QUAY-MARKET TIER COMPLETE *** — the town is WHOLE except one
        8-vertex lm_lockhead box (taste call: does Odessa get a hut? prep doc
        written at docs/plans/lockhead-prep.md). Revetment terrace + approved
        arcade (all 4 conditions met, cross-parcel build order documented x3);
        gates green everywhere; both slice-blocker rails trimmed via a NEW
        documented FOULING criterion — which found 11 more candidates in five
        districts, reported not silently trimmed (morning review list). Headline
        finding 222: Corridor.top_at was single-valued and this is the first
        district with walkable topology overhead.
07:30 slice_test transient (market saw 519/49 mid-camera-churn) resolved:
        PASS 550/0 from my seat. Camera agent 529'd mid-verifier-work; resumed
        with the news that the master is now STABLE — market cameras bake
        against the final town.
07:4x MARKET TIER LANDED -> re-baked its five shots (quay-west, quay-east, lockhead,
        loop-stairs, deep-stairs) against the FINISHED town: these frames are the
        first view anyone gets of the new market arcade. Staleness is now a standing
        verifier check (mtime vs the master, names the shots, prints the re-bake).
07:5x THE PLAYTHROUGH EARNED ITS KEEP — two bugs no static check could see:
        (a) walking the rim road to the cargo winch CUT to the stairwell shot. The
            seam had measured its corridor over ANY walk surface and the rim road
            runs alongside, so the band came out 4 m and reached across a different
            path. Corridor is now this edge's own ribbon + its endpoint areas; and
            because at that junction the road passes 1.5 m across and only 1.1 m
            ABOVE the flight (so no band there can be clean), a candidate seam is
            also REJECTED if a foreign path lies inside it, and narrowed where a
            junction makes that impossible. Width is the cheap thing to give up: a
            narrow band risks a MISSED cut, an overlapping one guarantees a WRONG cut.
        (b) that pushed the gate-stair seam 0.5 m from its sibling — the loop-stairs
            fault again. valley-gate__inn is a 7 m flight with BOTH ends owned by
            others, so it needs two seams in seven metres. It is now part of
            shelf-west. 18 shots -> 17. THE RULE, learned twice: a short path whose
            two ends belong to different cameras must be owned by one of THEM.
08:0x TWO GATES THAT WERE LYING, fixed: cine_solve --check folded warnings into its
        exit code so a FRESH file reported STALE (four junction seams warn by
        design); and the "can the camera see its region" bar was 0.75, invented,
        when the human-ACCEPTED Boatyard v10 frame scores 0.48 — probes sit on
        walk-mesh corners and a scaffold town occludes its own corners. Calibrated
        to 0.45 against that frame. A gate whose verdict does not mean what it says
        is worse than no gate.
08:1x RUNTIME VISIBILITY over all 17 shots, measured through the SHIPPED depth maps
        (not a Blender proxy): mean 0.94 and ZERO off-frame probes in the whole town
        — the coverage claim confirmed live. One shot failed it: shelf-west at 0.38,
        blocked by the GATE DISTRICT'S GROUND, because it had absorbed the gate stair
        and its region now started on the rim. Re-aimed 140 -> 120: 0.86, and 3 m
        closer so the character is bigger too. LESSON: re-check a shot when its
        REGION changes, not only when its angle does.
08:2x *** THE CINEMATIC TOWN SHIPS *** 17 shots, 21 silent seams, 315/315 walk
        surfaces owned, 0 unreachable pockets, cine_test 655/0, slice_test 532/0.
        Hub card: "DELLHOLLOW - the cinematic town". Region map: /cine_regions.svg.
08:17 *** DELLHOLLOW IS PLAYABLE AS FIXED CAMERAS *** — 17 shots, 21
        silent seams, structural coverage proof (315/315 walk surfaces, 0
        orphans, zero off-frame probes), verifiers 655/0 + 532/0, all shop
        doors prompting, the accepted boatyard v10 hero reproduced verbatim.
        Hub card: "DELLHOLLOW — the cinematic town". THE NIGHT'S SLATE IS
        COMPLETE: slice + tidying + cameras (serial) and market + foliage
        (parallel) all landed. Entering the POLISH PHASE per standing order.
08:17 polish backlog from tonight's reports: arrival-spawn tree prune
        (+ gate shot rebake), verify marker-vs-veg fix, the 11 reported fouling
        rails (documented criterion, gates prove safety), end-to-end play
        testing, junction-seam overlap left as the designated refinement point
        for morning.
08:40 POLISH ROUND 1 done: 8/15 fouling rails trimmed (7 whole-length
        cases deliberately left for morning judgment), arrival tree pruned, GLB
        + 8 shot backdrops rebaked against corrected geometry. Verifiers: cine
        655/0 (1 soft warn), slice 532/0, walk QA bit-identical. Next: playing
        the game end to end myself.
08:59 PLAYTEST FINDINGS (the phase earning its keep): (1) moving before
        the entry shot's art landed CRASHED phys() — guarded, committed. (2) the
        harness stepped over ~0.43u seam bands — SIM.tick/move now check seams
        per physics step like live frames. (3) THE REAL ONE: sliding down the
        slope beside the gate stairs bypasses the seam and strands the player
        off-frame in shot 'gate' at x=44 — the exact defect the system exists to
        prevent. Camera agent resumed to implement its own designated cure
        (shotAt positional correction from the ownership hulls) with repro +
        conditions. Meanwhile the 9-shot rebake completed earlier; committing
        art after the correction lands so it's one coherent freshness state.
09:0x POLISH FIND -> REFINEMENT POINT IMPLEMENTED. Coordinator reproduced the worst
        defect the grammar has: from the gate spawn, heading (1,0.15)/(1,0.3),
        collision lets the player SLIDE DOWN THE SLOPE BESIDE the gate stairs, never
        entering the seam band (seam cuts 0), and travel 25 m and two tiers down
        still under the gate camera, FULLY OFF-SCREEN.
        Cure = the positional safety net I had proposed: regions = the owned walk
        meshes AS BOXES (not convex hulls — a hull of the L-shaped boardwalk
        swallows the river), shipped in scenegraph.json which the runtime already
        fetches. If the ground you are on belongs to another shot AND NOT to the one
        you are in, for 20 physics steps, cut to the owner. The "and not your own"
        half is what keeps it quiet: near a seam you are inside BOTH regions.
        ONE THING THE DESIGN MISSED: the slide comes to rest OFF EVERY RIBBON, so
        containment had nothing to correct to — added a nearest-ground fallback,
        capped at 12u (past that you are falling and the respawn owns it).
        A correction does NOT move the player (they are legitimately there; the
        CAMERA is wrong) but still routes through sgHandoff, so arm/disarm applies.
        Counted separately in cine().corrections so playtests can tell an authored
        cut from the net firing.
        LIVE: repro ends in shelf-west, ON SCREEN at ndc (-0.28,0.02), cuts 0 /
        corrections 1, presence marker showing where it rests against a shopfront.
        Normal play across that seam: 1 seam cut, 0 corrections. cine_test 667/0
        (new SAFETY NET group asserts the repro point AND that correcting to the
        owning shot is on-screen from all 315 surfaces). slice_test 532/0.
        Side effect: this SUBSUMES the four junction-overlap warnings — a band that
        catches a neighbour now self-corrects.
09:15 CORRECTION LANDED (camera agent): positional safety net from the
        315 owned walk boxes — seams stay primary, net catches off-route travel,
        corrections counted separately; cine_test 667/0 incl. my repro point and
        an on-screen-from-every-surface sweep. My re-verification: correction
        fires and camera follows (tp probe); walking-repro negatives traced to
        MY harness starving the event loop during synchronous blocks (fade
        timers) — game unaffected; noted as a harness ergonomics improvement
        (await-paced walk helper) for a future pass, not tonight-critical.

============================================================
MORNING REVIEW BOARD — everything that wants your eyes/rulings
============================================================
PLAY FIRST:
  1. Hub -> "DELLHOLLOW — the cinematic town" (del-cine): 17 shots, silent cuts,
     positional safety net. THE deliverable.
  2. Hub -> "PLAY — the connected slice": valley road -> town -> interiors ->
     back, prompts at every door.
  3. ow-valley: bush-language Whisperwood (new leaf atlas), ridge walk, terrace
     grove — foliage agent's shots: valley_record_midvalley/shelf,
     foliage_lineup_density.png.
TASTE RULINGS QUEUED (none blocking):
  a. Foliage knobs: shell density, autumn ratio 0.048, grove greens (limey?).
  b. Cine: lockfive/quay-west far-figure sizes; quay-east 18m floor; gate yaw
     68° (legibility vs "looking back at the arch"); 4-of-17 transit vignettes.
  c. lm_lockhead: does Odessa get a hut? (docs/plans/lockhead-prep.md)
  d. 7 whole-length fouling rails left untouched (report in rail-trim output).
  e. Boatyard +1.9% cumulative light drift: accept/re-baseline (my rec: accept).
FINAL STATE: cine_test 667/0, slice_test 532/0, worldmap PASSED, valley wrapper
GREEN, walk QA bit-identical, all 17 backdrops fresh, town whole (one 8-vert box).

============================================================
MORNING BOARD — THE WORLD-SIDE CHIRALITY FLIP (overworld lane, 2026-08-01)
============================================================
BEFORE / AFTER, in one line: the world tile MIRRORED Dellhollow to satisfy a
sentence that said "west bank only"; the sentence was the error, the mirror is
deleted, and the corridor now runs the bank the shipped town actually stands on.

LOOK FIRST (the proof frame):
  docs/qa/overworld/chirality_plan.png — re-run after the flip. Both towns read
  "tile: X bank  built: X bank  AGREE"; the pink ring is the ONE bank change (the
  gate culvert court); the two cyan lines are the found tributaries.
  BEFORE, same script, commit 0cebd6a: Dellhollow read "tile: LEFT  built: RIGHT
  MIRRORED".

THEN THE TILE:
  valley_gate / valley_court — the crossing: doorway on the west bank, paving over
    the culverted water, road leaving east. `court` is a NEW seat, aimed at the
    map's own culvert point.
  valley_falls — the water comes back to daylight AT the sill and falls; the court's
    parapet is the stonework across the gorge head.
  valley_gorge / valley_midvalley / valley_shelf — the corridor with the rock on the
    traveller's OTHER hand and the river on their left.
  valley_moorage — Dellhollow's water door, now on the east (road-side) bank.

RULINGS WANTED (none blocking tonight's build):
  a. HOLLOWMERE PASS IS NOW ACROSS THE WATER. It was a sealed hook on what the file
     called "the reachable left-bank side"; with the bench on the east bank it sits
     on the far rim with farPlateau. Its seat was NOT moved (a ratified world
     landmark is not the lane's to move) and the sentence was corrected instead.
     A later chapter that wants it needs a way across, and the only crossings in the
     world are this gate court and Dellhollow's barred dam crest.
  b. EMBERBROOK STAMP, PROPOSED, NOT APPLIED (town maps are not this lane's):
     a second flag-stoned court on the VALLEY side of `sigil-gate`, 8.0 m along the
     channel (the town already carries that length before the gate, and it is the
     ratio the world court was seated from); a crossing note; and a re-ruling of
     `downstream-vista`'s stamped "seen from the GATE SIDE... and is NEVER reached",
     whose first half the crossing makes false while its second half ("no bridge
     anywhere") stays true. No brook-course amendment is needed — measured, see
     DAYLOG §10C.
  c. THE SHELF IS STILL A ROAD ON A CREST WITH A TROUGH BEHIND IT, not a ledge
     against a wall. Unchanged open taste question; the asBuilt block predates the
     flip and was not re-measured.
  d. Dellhollow's anchor reads 6.10 against a derived 5.06 (+1.04u) — reported.

  e. valley_vistaring.png IS PINNED TO THE EARLIER POST-FLIP BUILD, marked not
     silently refreshed. Measured (tools/valley_fielddelta.py): the benchSide
     handover moves the tile's far SE corner by up to 17.6u inside that frame's
     footprint, because the shelf's back-wall term has NO distance bound — every
     factor in it saturates to 1. Pre-existing, off-corridor, all four named probes
     delta +0.00. Ledger item; re-render rides with the quiet-box transition_test.

DEFERRED PERCEPTUAL QUESTIONS (no judge: the tooling does not reach rt regions):
  does the crossing READ as a crossing at walker's eye; do the two found tributaries
  read as water or as blue seams on a cliff; does the corridor still read bounded now
  that the rock is on the other hand.

FINAL STATE: worldmap_validate 0/0 · valley_crosscheck 84/0 · valley_verify OK ·
seam_test 294/0 · seam_walk 9/9 · slice_test 671/15 (all 15 emb-cine, ZERO
ow-valley, = the pre-flip baseline) · road 0 pushed / 0 spans / 3.51u slack ·
OLD GATE SEAL strips 0.00/0.00, flood fill 0 cells.
