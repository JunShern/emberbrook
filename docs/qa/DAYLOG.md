# DAYLOG — 2026-07-30 (day shift)

Timekeeping for the day slate, same convention as NIGHTLOG: every agent appends
timestamped milestones here (append-only; commit with your other files).

Slate (user-ratified this morning):
- COORDINATOR: combat-ecosystem design + schemas + state store; play3d.html
  gatekeeping; integration; final vertical-loop playtest.
- TOWN CUSTODIAN (sole master-blend owner today): lockhead station + empty-bank
  build, then legibility bucket-1 (rails/channeling) from audit findings.
- LEGIBILITY AUDITOR: route data + dev overlay + 18-shot audit + review page.
  Mandate includes proposing town-model re-architecture (user granted creative
  freedom; blend execution routes through the custodian).
- BATTLE CORE (T+design): rules layer, turn-based v1, router, encounter director.
- ECONOMY (T+design): shops, pause menu, save/load.

Canon set this morning: Odessa = senior lockkeeper (village-chief-like), lives at
Keepers' Cottage with daughter Maren; lockhead = her working STATION, not a hut.

------------------------------------------------------------
10:5x COORDINATOR: slate launched. Character canon fixed in map (Odessa+Maren at
      Keepers' Cottage, lockhead = staffed post; commit c15fff5). Design spine
      committed (e964e80): combat-ecosystem.md, rules data (6 monsters keyed to
      zones, 14 items, per-zone encounter tables w/ safe roads, growth curve
      k=25 w/ Vesper+Maren party-of-N, 3 shops), GS state store, play3d module
      hooks (game_state.js + route_overlay.js stub). Slice regression with hooks
      live: 532/0. FOUR AGENTS RUNNING: town custodian (lockhead station +
      empty-bank build), legibility auditor (routes/overlay/audit), battle core
      (rules kernel + turn-based v1 + encounter director), economy (shops +
      menu + save). All under design-first orders; check-ins on the 10-min tick
      cadence.

## LEGIBILITY AUDITOR

14:35 DESIGN NOTE committed: docs/plans/legibility-audit-design.md. Position taken
        (coordinator ruling welcome): route polylines are DERIVED, not hand-authored —
        dellhollow.map.json's 38 typed walk edges ARE the intended route (the 315 walk
        meshes were generated from them and are wider by construction, which is the
        plan's own diagnosis), and cameras.json `owns.edges` (with @t0..t1 fractions)
        already says which route belongs to which shot. Generator
        tools/routes_derive.mjs reuses tools/cine_regions.mjs so ownership/projection
        have no second implementation; per-shot `overrides` keep it hand-editable;
        `--check` fails on staleness like cine_solve/scenegraph_derive. Generalises to
        Emberbrook and every future town with no authoring pass.
        Rubric: 6 measured signals (entry-visible / exit-visible / exit-flow /
        route-visible / route-distinct / no-fall-off) then the user's question;
        occlusion measured by gl.readPixels against the shot's own baked depth, not
        judged by eye. Fix buckets 1-4 incl. model re-architecture.

## TOWN CUSTODIAN

14:40 BASELINES + DESIGN NOTE. Region baselines taken BEFORE touching anything
        (region 74,90,10,22):
        * master_walk_qa.py — 367/367 identity bit-identical (worst vertex delta
          0.000e+00); ray coverage 242 samples, 239 on a walk mesh (98.76%), 19
          buried skipped; FAILED (2) ALREADY, both pre-existing: non-walk first
          hits e_lockhead__lock-five_rung00 x3, headroom lm_lockhead x4 (1.65%)
          + e_lockhead__lock-five_rung00 x3 (1.24%). 296 walks render-hidden
          town-wide.
        * geometry_audit.py — 73 meshes in region, 18 bbox-overlapping pairs,
          0 intersection offenders, 0 strays.
        DESIGN NOTE committed: docs/plans/lockhead-station-design.md. The
        measurement it adds to lockhead-prep.md: with walk_/bar_/lm_ masked, the
        route's NORTH half (approach + pad, y>15.6) and the WHOLE descending route
        to the Keepers' Cottage (..._l0..l5) hang 1..3.7 m over bare lf_ground with
        no art at all. So the "ribbon debt" is not a 10-line flag — hiding those
        ribbons without structure would swap a gray ribbon for INVISIBLE FLOOR over
        a 12 m drop. Paying it with structure: lk_paving (bedded half), lk_planking/
        lk_joists/lk_bearers (the jetty the parcel camera's own note describes),
        lk_boardwalk (the cottage descent), lk_bankface (cut-bank revetment + kerb),
        lk_rail (rim rail, VISUAL, gap at the ladder head), lk_station/lk_mast/
        lk_bell/lk_brazier (Odessa's post, NOT enterable, no map change needed),
        lk_clut, veg_lk_*, two 680 W practicals.

## BATTLE CORE

14:40 DESIGN DOC committed: docs/plans/battle-core-design.md. State/action/event
        shapes, scheduler policy interface, router API, screen sketch, sim
        scenarios. Both standing swap tests answered YES in writing (an ATB or
        real-time scheduler needs no change to battle_rules.js or the router,
        because the kernel's unit of work is ONE ACTION not one round, and the
        router is read per decision; Battle.start can be reimplemented real-time
        because the overworld's whole surface is `Battle.active` + the promise +
        the result — xp/gold/drops are reported, never applied).
        THREE RED-TEAM FINDINGS raised to main before working around them:
        (a) `chancePerStep` cannot be per physics tick — 0.02/tick at 60 Hz with
        SPD 0.075 is a battle every 0.83 s. A "step" is therefore defined as 1.0
        world unit of travel, accumulated by the director from getPos() itself
        (so the movement hook is a zero-arg Encounters.tick(), and the JSON
        numbers survive an SPD retune). grace 30 = 30 u; mean meadow gap 50 u on
        a 280 u tile.
        (b) `mean turns 3-6` looks unreachable at party-of-1: level-1 Vesper
        (atk 9 w/ staff) deals 14-18 to a 16 HP reed-nibbler, ~60 % one-shot, so
        the single-nibbler group ends in ~1.4 rounds. Measured table + a
        monsters.json HP proposal follow from the sim; the envelope stays a test
        either way.
        (c) GS has no HP setter, so v1 defeat-revive uses a second
        applyBattleResult({outcome:'defeat',partyHp:{...:1}}) — public API only —
        and requests GS.setHp(charId,hp). Also flagged: Rules.derive.charStats
        duplicates GS.stats math because the kernel must run in node without GS;
        the clean fix is GS.stats delegating to the kernel.

## ECONOMY

14:52 DESIGN NOTE committed: docs/plans/economy-design.md. Shape: every module
        splits DATA -> OPS (pure, GS-only, headless-testable) -> VIEW (keyboard
        DOM overlay), so tools/economy_test.mjs tests the code the UI actually
        runs instead of a re-implementation. Third file public/js/ui_kit.js
        (window.EBUI) holds the shared overlay/cursor/input-lock so shop and menu
        cannot drift apart and a battle menu inherits the feel.
        NO COORDINATES IN CODE, copying the scene graph's own rule: the shop is
        matched by shops.json sceneKey (verified against scenegraph.json nodes —
        all three match), the interaction region IS the interior's own
        walk_pad_counter mesh (every interior builder emits one; box test, not a
        circle, because the pad is 1.7x1.0m), the label is "Talk to the " +
        shops.json keeper, and the banner is a clone of sgPrompt's recipe
        (promptFmt/key/vTol read from the graph's own defaults).
        Anchor chain: requested SIM.pad('walk_pad_counter') hook > optional
        shops.json counter field > a GLB-derived fallback table that works today.
        PAUSE WITHOUT TOUCHING play3d: capture-phase key listener on window +
        SIM.keys({}) zeroing = a real pause with zero coordinator dependency;
        window.UILOCK is consulted too if the formal hook lands.
        Key bindings: E at counter (identical to doors), Esc for the pause menu
        (free — play3d uses g/2/[/]/m/z and M is already the dev settings menu),
        arrows AND WASD for the cursor (either couch seat can drive), E/Enter
        confirm, Esc/Q back. Red-team answers in §7: six chapter-3 shops = a
        shops.json edit only; Maren joining = activeParty() gaining a row, no
        code change.
11:1x COORDINATOR CHECK-IN 1: battle-core + economy design docs reviewed and
      approved (both answered the swap tests in writing). Rulings (full log in
      combat-ecosystem.md): encounter step = 1.0u travel; meadow envelope
      relaxed to 1-4 turns at party-of-1 (monsters stay cheap); schedulers+AI
      live in the kernel as pure injectables so battle_sim tests the SHIPPING
      engine. Grants shipped (783c621): GS.setHp + GS.useItem, GS.stats
      delegates to Rules.derive.charStats (one impl of character math), UILOCK
      modal-input contract in play3d (phys freeze + key guards, replaces both
      agents' bespoke freeze tricks), SIM.pad. Slice regression after play3d
      edits: 532/0. Both agents messaged with rulings; battle menus to evaluate
      reusing economy's EBUI ui_kit.

15:2x BATTLE CORE — ALL FIVE FILES LANDED (1,554 lines of module + 514 of harness).
        public/js/battle_rules.js (520) pure kernel: mulberry32 + FNV-1a hashSeed,
        damage=max(1,round((atk*2-def)*U(0.85,1.15))), spd order w/ authored-index
        tie-break, applyAction returning {state,events} with DETERMINISTIC
        retargeting, rewards(), derive.* (charStats is now GS.stats's one
        implementation), makeRouter, policies.partyAi/monsterAi,
        schedulers.commitThenResolve, engine.run/result. Node + browser.
        public/js/battle_turnbased.js (741) window.Battle: full-bleed FF screen
        (per-zone gradient backdrop table, family-keyed CSS silhouettes, floating
        damage numbers, HP bars, log line, Attack/Item/Flee cursor, victory/defeat/
        flee outro), 350ms veil matching sgFade, UILOCK held, ONE capture-phase key
        listener gated on Battle.active, GS.removeItem-only item consumption.
        public/js/encounters.js (282) window.Encounters: distance-accumulating
        director, per-zone grace re-armed on attach/zone-change/post-battle/
        teleport(>3u), seeded per-step rolls, weighted group pick, defeat policy
        (1 HP + half purse + respawn at anchor), self-attaches to SIM so the only
        hook is a zero-arg tick().
        tools/battle_sim.mjs (289) + tools/encounter_sim.mjs (225).
        MEASURED CADENCE (4000 runs/zone, confirms the 1.0u ruling): meadow mean
        gap 80.2 u = 17.8 s of walking, median 65, p10-p90 36-144, 3.5 encounters
        per 280 u tile crossing; forest 48.9 u; crag 53.4 u; water 58.9 u; road
        SAFE. Verified the per-step seeding is unbiased (P(first draw<0.02)
        measured 0.02008 over 2e6 fresh seeds) — a fresh mulberry32 per step is
        sound, so a walk is replayable.
        encounter_sim.mjs GREEN, 21/21: it loads the REAL game_state.js under a
        fetch stub (no DOM) and proves the vertical loop closes headlessly —
        GS.stats === Rules.derive.charStats, Battle.start returns a victory and
        applies NOTHING to the world, GS.applyBattleResult is what moves gold, a
        mid-battle router.set() moves the seat on the very next decision, road and
        UNKNOWN zones are safe, steps track distance not ticks (799 steps in 800u),
        one run seed replays one walk, a 40 u jump re-arms grace, and the director
        is inert with a reason when Battle is missing.
        battle_sim.mjs: 6/6 engine property tests pass (determinism, seed
        sensitivity, applyAction purity, retargeting, collection-order
        independence, termination under a round cap). BALANCE: 20 of 22 envelopes
        green on committed data; forest-2 [duskpad+duskpad] wins 0.0% and forest-4
        [bramble-shade+duskpad] 17.5% at level 1 — CERTAIN DEATH, not danger.
        Tuning request sent to main (atk-only, measured): duskpad 8->6,
        bramble-shade 9->7, weir-eel 9->7 makes every envelope green while leaving
        the forest expensive (11-25 HP of 34 left) — awaiting the grant, no data
        file touched.
11:4x COORDINATOR CHECK-IN 2: battle-core kernel live, verified identical to GS
      math via the delegation signature. It cross-reviewed and caught TWO live
      integration bugs node --check can't see: (1) MY phys() UILOCK early
      return broke loop()'s destructure — every frame threw while a panel was
      open and the world stopped rendering; fixed f760304 (frozen shape
      returned, sgTick still skipped, slice 532/0). (2) economy's ui_kit
      panel() calls setUilock/zeroMovement which don't exist — shop/menu can't
      open; fix ordered, plus a ruled locked() guard in their globals dispatch
      so shop/pause/battle are mutually exclusive by construction. Rulings 7-8
      added to combat-ecosystem.md (in-battle items bypass GS.useItem by
      design; UILOCK modal exclusion). Battle tags will precede ui_kit at hook
      time. EBUI reuse verdict approved (pure half only).

15:41 SHIPPED (2448f47): public/js/ui_kit.js (293), public/js/shop.js (398),
        public/js/menu.js (397), tools/economy_test.mjs (512).
        economy_test: 204 passed, 0 failed. node --check clean on all four.
        All three coordinator grants consumed: SIM.pad means shop.js holds ZERO
        coordinates for any shop (anchor derived from the interior's own
        walk_pad_counter at runtime; the GLB-derived fallback table survives only
        as the no-hook path). GS.useItem means the planned heal shim was never
        written — Menu.useItem is a one-line delegation, so menu item use and
        battle item use cannot diverge. UILOCK('shop')/('menu') is what pauses
        the world; EBUI's capture listener now only routes keys to the top panel
        and kills browser defaults. Ruled requirement adopted: global keys are
        suppressed whenever UILOCK is active, so shop / pause menu / battle are
        mutually exclusive BY CONSTRUCTION (Esc in a shop closes the shop, never
        stacks a menu; the menu refuses to open over a battle) — asserted, not
        assumed.
        TEST NOTE worth borrowing: sections 15-16 drive both UIs through a DOM
        stub with SYNTHESISED KEYSTROKES — prompt arms, panel opens, list walks,
        qty step, a real purchase, a sell-back, every menu screen, save/load
        confirms. node --check cannot see a call to a function that does not
        exist, and OPS-only tests never enter the view; two such ReferenceErrors
        were caught in cross-agent review before those sections existed, and this
        is the regression guard for that whole class.
        Two bugs found in the data/state layer, both reported and none worked
        around: none. Shop sceneKeys and scenegraph nodes agree exactly.
11:5x COORDINATOR: economy VERIFIED INDEPENDENTLY (204/0 rerun by me, syntax
      clean, no stale refs — the "bug A" battle-core saw was a mid-edit
      snapshot of an untracked file; committed tree is clean) and INTEGRATED:
      ui_kit/shop/menu tags live in play3d (battle tags slot reserved before
      ui_kit), Shop.tick() rides the physics tick like sgTick. Slice 532/0
      with shops+menu armed. The pause menu, shops, and save/load are now LIVE
      in the game. Remaining: battle-core hooks, custodian + auditor reports.
12:1x COORDINATOR: BATTLE IS LIVE. Granted the measured tuning (3 atk cuts;
      forest-2 went 0/500 wins -> 100% @4.88 rounds with real attrition) PLUS
      the optional scree-shell atk 9 — crag at 78/73% win with tonics spent is
      danger, not grind; queued for tonight's taste board. Hooks applied: 3
      battle tags before ui_kit, Encounters.tick() on the physics tick after
      sgTick. Full regression green: battle_sim all envelopes (both levels),
      encounter_sim 21/21, slice 532/0, cine 667/0. Water zone ruling: bank
      cells ARE reachable (dock/moorage/weir), eel stays live content,
      envelope stays advisory. NEXT: coordinator browser playtest of the full
      vertical loop, then custodian/auditor integration.
15:10 ROUTE DATA + OVERLAY + 17-SHOT AUDIT LANDED.
        public/townmap/dellhollow.routes.json (new, derived by tools/routes_derive.mjs):
        17 shots, 50 entries, 49 exits, 59 routes, 432 m of intended route, each point
        carrying its scenegraph edge and its projection into the shot's frame. Also
        reports 76.5 m over 17 spans where the floor you walk is owned by a DIFFERENT
        shot than the camera that is up (a cutOffset consequence — where sgCorrect can
        fire and where authored cuts land late).
        public/js/route_overlay.js: R toggles (Shift+R adds an all-shots step), entries
        green, exits orange WITH their real trigger bands and leave-direction arrows,
        route ribbons + spur/blocked language, in-scene sprite labels (so they survive
        readPixels and canvas captures). Lazy, additive, depth-honest, never touches game
        state. window.ROUTES exposes the instrument: probe() measures per-point visibility
        by GL readback against each shot's own baked depth map; dropEdges() finds
        unprotected fall-off with coordinates.
        AUDIT: 3 GREEN / 5 AMBER / 9 RED. Review board:
        docs/qa/review/legibility-audit.html (overlay + clean plate + measured numbers +
        defects + bucketed fix per shot; raw records in docs/qa/review/probe/*.json).
        WORST: cottage-steps — the "eight-metre flight" is DISCONNECTED FLOATING PLANK
        SLABS; there is no stair in the frame, only walkmesh (bucket 4, zoom exhibit).
        WORST BY IMPACT: gate + shelf-west — in the town's first two shots the rim
        canopy sits between camera and road, so the only way INTO Dellhollow measures
        0% visible and both onward seams in the shop street measure 0%.
        SYSTEMIC: cine_solve frames every ARRIVAL but never the SEAM IT IS AN EXIT OF —
        5 exits sit outside their own frame (worst cottage, ndc y -1.37). Redline
        proposed: add each shot's outgoing seam centres to the solver's sample set.
        Fall-off measured across the town: 91 unprotected places, worst weave (19,
        incl. one bottomless at 59.69,12.47,-18.14) and cottage (12, four 16-18 m falls
        within 0.9 m of the path). Rubric amendment flagged: fall-off scored SEPARATELY
        from the verdict, else it flattens every shot to AMBER.
        Gates re-run before commit: cine_test 667/0, slice_test 532/0,
        routes_derive --check ok. play3d.html untouched (hook was already in place).

## BATTLE CORE

15:5x GREEN ON RATIFIED DATA + BALANCE KNOWLEDGE WRITTEN DOWN. With the granted
        atk tuning applied by the coordinator (0ef8b42) and the hooks live,
        battle_sim.mjs is ALL ENVELOPES GREEN at n=500 for levels 1 and 2, engine
        property tests 6/6; encounter_sim.mjs 21/21. Level-1 table on shipped
        data: meadow 100% @1.40/2.84/1.00 rounds; forest 100% @2.00/4.88/1.83/
        3.89 (forest-4 leaves 11.3/34 HP — the intended attrition); crag 77.8%
        and 74.4% with 0.77/1.71 tonics spent (dangerous, as mandated, after the
        scree-shell atk 7->9 the coordinator adopted); water 100% @2.00/3.00.
        DESIGN DOC UPDATED (docs/plans/battle-core-design.md): all three red-team
        findings now carry their RESOLUTION inline so the doc reads as settled,
        §10 rewritten to the ratified per-zone envelopes + the six engine property
        tests, and a new §11 "BALANCE DIAL CHARACTERIZATION" — the systemic
        finding that must outlive this session:
        with E = 2*atk - def, a fight is won iff Sum(foeHP)/E_party <
        partyHP/Sum(E_foe), and at level-1 integers that is a STEP FUNCTION of
        monster atk. Measured cliff: duskpad atk 8 -> 0.0% win, atk 7 -> 19.0%,
        atk 6 -> 100%, with no integer in between, while level 2 wins 100% at all
        three. Dial resolution, coarse to fine: monster atk (2 damage/point,
        AVOID) > party def (1/point, party-wide) > monster HP (fight LENGTH only,
        safest) > group size/weights (the real difficulty dial, non-linear).
        House rules recorded: author HP-first from a target round count, never
        propose an atk change without --tune measuring it, balance depends on
        party SIZE more than level (Maren joining loosens every envelope at once),
        a heal item only helps while Sum(E_foe) < heal per round (which is exactly
        why the untuned duskpad pair was unwinnable rather than hard — the AI
        drank and still died), and danger belongs in spd as much as atk (measured
        escape chances: scree shell 69%, nibbler 57%, duskpad pair 39%, sprite
        33%, weir eel 21% — the eel is frightening because you cannot leave).
15:20 GENERALITY VERIFIED + design note amended. The same dellhollow.routes.json drawn
        in townwalk (a real-time scene with NO shots): the overlay resolved its data file
        from the scene graph's own provenance, found no shot, and drew the whole town —
        50 entries / 49 exits / 432 m at once (appendix on the review page). collide,
        walkRef and allMeshes identical before and after the overlay is on, which is the
        "never touches game state" claim measured rather than asserted. Emberbrook needs
        one generator run and no code change. Design note §4b records the three rubric
        amendments made in the doing (fall-off scored separately; visibility measured at
        surface AND chest height; exit-offscreen split into ground vs figure).
12:5x COORDINATOR VERTICAL-LOOP PLAYTEST — THE LOOP CLOSES (browser, real tab):
      director forest battle -> victory -> 13xp/9g/pelt APPLIED; organic
      water-zone encounter via real SIM walking (eel+sprite ambush, out at
      5/34hp, 24xp/16g applied); Esc suppressed under battle lock; menu shows
      live stats+equip deltas; GS.save survived scene change into the
      chandlery; counter prompt -> shop -> bought tonic 46->34g; useItem
      healed 29 w/ max clamp; GS.reset cleanup. HARNESS CANON: hidden-tab
      intensive throttling => automated battles need battleOpts speed:0.
      REFINEMENT NOTE filed w/ battle-core: zone-boundary grace farming.
      AUDIT TRIAGED: custodian gets 4 geometry items (probe coords as spec,
      auditor instrument as acceptance); fresh agent on cine_solve exit-seam
      delta report (boatyard PINNED for user ruling; NO bake until custodian
      geometry lands — one bake, one freshness state). Auditor transcript
      expired (known); successor briefed on written handover. Battle-core +
      economy + audit tasks CLOSED. Custodian progress snapshot requested.

15:20 LOCKHEAD BUILT AND GATED. tools/lk_build.py (idempotent, opens the live
        master, `-- save` to write) + master saved. 39 objects / ~3.4k verts,
        bounds x 74.29..86.20  y 12.45..18.85  z 7.48..19.64, all lk_/veg_lk_.
        WHAT IS THERE NOW: lm_lockhead deleted (recorded in
        tools/blends/districts/lockhead_deletions.json); lk_surface (270 nodes,
        setts where the bank is within 0.62 m, BOARDS where it flies, laid 50 mm
        under the walk top per finding 90) + lk_joists/lk_bearers (9 joist runs,
        6 posts + 11 raking struts, every landing a ray-cast on lf_ground /
        lf_planking, all of it BELOW the walk plane); lk_boardwalk + frame
        (4 dressed flights over ..._l0..l5, the cottage exit that was a hidden
        ribbon over a 1..2.5 m drop); lk_bankface (34 courses + 33 coping stones,
        line found per column by stepping south off the walk graph's own edge, with
        a return where it steps); lk_rail (8 posts + top rail/midrail/kickboard on
        the north lip AND the descent's river side, ladder head left OPEN with iron
        grab stanchions — VISUAL ONLY, no bar_/walk_ prefix); Odessa's station on a
        measured cut terrace at the SE elbow (chart board on an easel, lock ledger
        desk, stool, gear post with oilskin + gauge glasses, bell frame in the one
        pad-level pocket, brazier) + lk_mast (4.3 m signal mast, yard, two
        day-marks, halyard to a cleat) on the bank BEHIND the revetment — an
        instrument, not a place, so nothing new is enterable and the map needs no
        edit; lk_clut 7 props; veg_lk_tuft_* x26 in the veg_lf_ family's grammar.
        RIBBON DEBT PAID: 9 ribbons render-hidden (walk_pad_lockhead,
        market-stalls__lockhead_l1/l2, lockhead__keepers-cottage_l0..l5) — town
        total 296 -> 305 — and every one of them now has real art underneath.
        LAMPS: KEYL_lantern_0 680 W at (79.78,17.50,15.95) ladder head;
        KEYL_lantern_1 480 W at (84.46,15.17,15.58) on the gear post. Measured
        spill: pad centre 10.9, ladder head 9.2, approach mid 4.4, desk 3.2,
        descent foot 1.3, mast truck 1.4 W/m2. No Heartlights (world canon).
        GATES: region 74,90,10,22 walk QA — identity 367/367 bit-identical (worst
        delta 0.000e+00), ray 242 samples / 239 walk hits (98.76%), IDENTICAL to
        the baseline: my build adds ZERO blocked samples, and lm_lockhead's 4
        headroom samples are GONE. Only the pre-existing
        e_lockhead__lock-five_rung00 (3+3) remains — see the request below.
        FULL 367 walk QA: PASSED (1308/1308 = 100.00%, 305 render-hidden, all
        viewport-visible). geometry_audit region: 0 intersection offenders, 0
        strays (32 pairs tested; the district's own assemblies registered in
        tools/geometry_audit.py). glTF survival (--prefix lk_,veg_lk_): 39 out /
        39 in, 2 district-owned materials, 0 WHITE; mat_grass/mat_fern/mat_rope
        arrive white as the known master-wide inherited debt.
        REQUEST FOR THE COORDINATOR (not mine to touch): the map ladder's top rung
        e_lockhead__lock-five_rung00 sits at z 14.07..14.13, i.e. 30..90 mm ABOVE
        walk_pad_lockhead, inside the pad — 3 non-walk first hits + 3 headroom
        samples in this region, present BEFORE my pass. Fix is in whatever
        generates the map ladders (top rung flush with or below the pad plane).
13:1x COORDINATOR: lockhead ACCEPTED (830cfee, adbfc53) — the last gray district
      is built: Odessa's station, jetty, bankface ground language, rails, 2
      practicals (measured spill, no Heartlights), ribbon debt paid WITH
      STRUCTURE (custodian caught that hiding ribbons = invisible floor over a
      12m drop). Region + full walk QA identical/green, 0 white prims.
      RULINGS: west-approach rail extension granted (one custodian today, no
      parcel politics); ladder hatch stays OPEN (intentional edge — rule is
      railed OR intentional; instrument to grow an 'intentional' annotation);
      rung00 one-off lowering AUTHORIZED (e_ not walk_/bar_), generator debt
      logged here: MAP-LADDER GENERATOR SHOULD CLAMP TOP RUNG TO THE
      DESTINATION PAD PLANE — fix at source before the next town generates
      ladders. Custodian on fix round: west rail -> arrival -> steps -> weave,
      record shots at the end.

16:1x REFINEMENT NOTE COMMITTED (coordinator playtest follow-up, deferred by ruling).
        docs/plans/battle-core-design.md §9a records the ZONE-BOUNDARY GRACE
        FARMING exploit the playtest found. I measured it against the real
        director before writing it up, and it is more severe than the report
        assumed: 600 u walked alternating meadow/crag gives ZERO rolls at every
        flip spacing tested (0.5, 1, 2, 4, 8, 20 u) versus 120 rolls for the
        no-flip control. TWO mechanisms, which matters because a partial fix will
        look like it worked: (1) the graceLeft reset dominates — a roll needs MORE
        travel between zone changes than the zone's own grace (30 u meadow, 20 u
        forest/crag), and zones.json has a 1.25 u cell, so any diagonal shoreline
        or treeline walk defeats it by default rather than by precise play;
        (2) the acc=0 reset bites below ~1 u spacing, where even `steps` stops
        climbing (0 steps over 600 u at 0.5 u flips). Recommended fix recorded:
        re-grace ONLY on entry from a safe zone (road/town), which makes safe
        zones the sole source of quiet and matches the legibility programme's
        "following the route is rewarded" intent — plus stop zeroing acc on
        hostile->hostile or the tight zig-zag survives. Regression to ship WITH
        the fix is specified (~6 lines in encounter_sim.mjs, which already drives
        ZONE as a mutable), including the trap that a synchronous tick loop leaves
        the director busy forever once a battle fires.
        Also recorded in §8: the coordinator's harness canon that automated
        playtests must pass battleOpts {speed:0} or {headless:true}, with the
        reason (setTimeout pacing is deliberate because rAF is throttled to
        nothing in a hidden tab, but Chrome's intensive throttling after ~5 min
        hidden is one wake/minute, so speed>0 takes tens of minutes there).
        No code changed. battle_sim n=500 ALL ENVELOPES GREEN + 6/6 property
        tests; encounter_sim 21/21. BATTLE CORE COMPLETE.

16:4x GRACE FARMING FIXED (coordinator un-deferred on my measurement). Grace now
        comes from SAFETY, not novelty: only entry from a non-hostile zone
        (road/town/unknown) re-arms it, and a hostile->hostile crossing carries
        BOTH the grace counter and the accumulator across. Teleport/scene-handoff
        re-grace (>3 u jump), post-battle and attach re-grace all unchanged.
        POST-FIX, 1200 u alternating meadow/crag, seed 7 — every spacing rolls
        again and steps track distance at every spacing (pre-fix: 0 rolls at all
        of them, and 0 STEPS at 0.5 u):
          flip     steps  rolls  battles  mean gap
          never     1199    839      11     103 u
          0.5 u     1199    839      11     103 u
          1 u       1199    789      16      71 u
          2 u       1199    699      20      57 u
          4 u       1199    806      16      75 u
          8 u       1199    756      18      67 u
          20 u      1199    756      19      63 u
        RESPITE MEASURED, NO TUNING PROPOSED (4 seeds x 2400 u per zone, 129-184
        observed inter-battle gaps each): meadow mean gap 72.9 u (74.3/69.4/76.8/
        71.5 per seed, median 61, p10-p90 35-126) — inside the coordinator's
        60-90 u "costs but breathes" target; forest 54.0, crag 51.1, water 55.2 —
        all well above the 35 u floor that would have triggered relief; road never
        rolls. The pre-approved meadow grace/rate envelope is NOT needed and I am
        proposing nothing, per "no tuning for its own sake". Cadence barely moved
        because post-battle grace was never part of the defect: a straight walk's
        gap has always been grace + 1/rate, and only BOUNDARY walks were broken.
        ROAD REWARD IS NOW ASSERTED so nobody "fixes" it later by reading only the
        exploit half of the note: weaving on and off a road stays peaceful (0
        battles over 1200 u flipping road/meadow every 20 u) because safe zones are
        the sole source of quiet — the legibility programme's own thesis. The bound
        is that you must keep returning to safety to keep it.
        REGRESSION SHIPPED WITH THE FIX in encounter_sim.mjs (now 38 checks, was
        21): control row + all six flip spacings, asserting rolls (mechanism 1) AND
        steps (mechanism 2), plus the road-hug row. flipWalk awaits every tick
        because a synchronous tick loop leaves the director busy forever once a
        battle fires (fire() is async, its finally never runs until the loop
        yields) — that artifact deflated the control row in my own pre-fix probe,
        and an unawaited regression would read "control barely walked" as success,
        so the harness asserts the control's step count honestly.
        Design doc §9a rewritten FOUND/FIXED/REGRESSED with both tables; the §9
        grace bullet now states the safe-zone-only rule. battle_sim n=500 ALL
        ENVELOPES GREEN + 6/6 property tests; encounter_sim 38/38.

16:05 LOCKHEAD INCREMENT — bucket-1 item 1 folded in (coordinator's legibility
        triage, rulings 1-3). Three changes, all in tools/lk_build.py:
        * WEST EXTENSION (ruling 1): the build region's X0 moved 74.40 -> 63.90,
          because 8 of the auditor's 11 measured fall spots (probe/lockhead.json,
          falls 2.9..4.7 m) are on the market approach WEST of the old parcel line,
          and that stretch measures the same as the parcel's own — bare
          wf_ground/lf_ground 1.9..4.3 m under the ribbon with the Weave's hut roofs
          2 m below that. It is now surfaced, joisted, founded and RAILED the whole
          way: lk_surface 588 nodes (183 setts / 389 boards), 21 joist runs, 16
          posts + 24 raking struts, lk_bankface 74 courses + 68 coping stones,
          lk_rail 15 posts from x 64.0 to 85.3. Double-lay guard: qm_paving/
          qm_planking/qm_ground/wf_ground added to the founding ray, so the join at
          x ~ 63.9 to the quay market's own deck is a butt joint by measurement.
        * LADDER HATCH (ruling 2): opening narrowed 1.00 -> 0.65 m (the ladder's own
          width, interpolated off rungs 04/05), NOT closed, grab stanchions either
          side. Intentional edge, per the ruling.
        * RUNG00 (ruling 3, authorized): e_lockhead__lock-five_rung00 lowered 223 mm
          (top 14.130 -> 13.907, 40 mm under the LOWEST walk face over it — three
          ribbons overlap there at 13.93..14.07 and the gate rays each against its
          own surface). Recorded in tools/blends/districts/lockhead_deletions.json
          under "modified" with the authorizing message. Idempotent: the shift is
          recomputed from the rung's current top each run. NOTE for the record: it
          took three attempts because the rung is a unit cube with an object scale
          of 0.03 in z, so a world-space delta written into v.co.z arrives 33x too
          small — the first attempt moved it 6 mm while logging 198.
        Also fixed, all caught by the extended region gate and all authored by me:
        the revetment's RETURN, COPING and BUTTRESS pieces were built without their
        own footprint guards, and the coping/buttress stand 0.07/0.17 m further
        north than the column they sit on — 2 blocked + 2 headroom samples on the
        approach ribbons. The wall-line search now tests the whole profile, and
        every piece is guarded individually. free_box() also samples 3x3 minimum and
        tests face corners inside the box, because a 0.30 m column could straddle a
        thin walk sliver between the four corner samples.
        GATES AFTER (all green): walk QA region 62,90,10,22 — 420 samples, 420 walk
        hits, 100.00%, PASSED; region 74,90,10,22 — 242/242, 100.00%, PASSED (was
        FAILED(2) at baseline this morning: the district's own region is clean for
        the first time). FULL 367 walk QA PASSED, identity bit-identical (worst
        delta 0.000e+00), 1308/1308 = 100.00%, 305 render-hidden all
        viewport-visible. geometry_audit 62,90,10,22 — 172 meshes, 38 pairs, 0
        intersection offenders, 0 strays. glTF survival --prefix lk_,veg_lk_ —
        39 out / 39 in, 0 white prims (mat_grass/mat_fern/mat_rope = known
        master-wide inherited debt).
13:4x COORDINATOR: grace-farming fix VERIFIED AND CLOSED (95a7d29; my rerun:
      encounter_sim 38/38, battle_sim all envelopes + 6/6, slice 532/0).
      Boundary walking went 0 rolls/1200u -> full cadence; post-fix respite
      measured across 4 seeds x 2400u/zone: meadow 72.9u mean gap (inside the
      60-90 band), forest/crag/water 51-55u — NO TUNING APPLIED, none needed.
      DESIGN NOTE (ruled, pinned by test): roads and their shoulders are the
      only quiet; weaving on/off a road is peaceful BY DESIGN (legibility
      thesis: following the route is rewarded). MODEL WORKSTREAM: measure
      exploit -> minimal fix -> regression that cannot quietly lie -> re-measure
      -> propose nothing when numbers land. This is how balance work happens
      here. Battle-core agent released with thanks.

16:5x BATTLE CORE CLOSED. Coordinator independently verified encounter_sim 38/38,
        battle_sim all envelopes + 6/6 property tests, slice 532/0. Road-hugging
        RULED CANON and kept exactly as shipped: "roads and their shoulders are the
        only quiet; weaving on/off a road is peaceful by design; the cost is you
        must keep returning to safety." Recorded that ruling in the two places a
        future editor actually reads — design doc §9a (now "CANON, not an open
        question", with the note that the pinning test exists so revisiting it must
        be a decision and not a side effect) and the comment on the zone-change
        block in encounters.js itself. No-tuning conclusion accepted; nothing
        applied to encounters.json. Final shape: 3 modules (1,556 lines), 2 headless
        harnesses (560), 1 design doc (529), 8 commits, zero coordinator-owned files
        touched by me.

15:26 SOLVER FIX — SHOTS NOW FRAME THE SEAMS THEY EXIT THROUGH (legibility follow-up).
        The audit's systemic finding, mechanised: cine_solve framed each shot's owned
        region plus every ARRIVAL that lands in it, but never the seams the shot is an
        EXIT of — so five exits sat outside their own frame (cottage ndc y -1.37,
        boatyard -1.15, waterfront -1.20/-1.04, lockhead -1.06) and the player walked
        out of shot before the cut fired. solveCamera now also fits the CENTRE of every
        seam band a shot is on either side of (ground point + head, exactly as arrivals
        are done); a seam is walkable both ways, so it is an exit of both shots and both
        must frame it. Derived from the same cutGeometry the seams themselves come from:
        no authoring, cannot drift, and every future town gets it for free.
        PINNING, in DATA not code: `"pin": true` on a camera = this frame is a human
        ruling; the solver reproduces its authored pos/aim exactly and excludes it from
        the constraint, so a pinned shot re-solves to ITSELF (boatyard: dPos 0.000,
        dAim 0.000, byte-identical record). `defaults.frameExits: false` = a town opts
        out while its backdrops are baked. Both belong in cameras.json; this tranche may
        not edit it, so they live in the sidecar public/townmap/dellhollow.cameras.pins.json
        which the solver merges onto the camera records — COORDINATOR: move them into
        cameras.json and delete the sidecar, nothing else changes.
        Dellhollow is opted OUT, so the shipped chain is bit-identical: cine_solve
        --check fresh, scenegraph_derive --check fresh, routes_derive --check fresh,
        cine_test 666/0 (+1 pre-existing soft), slice_test 532/0. No re-bake.

15:35 DELTA REPORT for the proposed re-solve, in docs/qa/review/solve-proposal/
        (proposed solve + delta.md + delta.json + probe/<shot>.json, and the generator
        derive_delta.mjs that made them — re-runnable, nothing hand-typed).
        OFF-FRAME EXITS 5 -> 1: lockhead -1.06 -> -0.90, cottage -1.37 -> -0.89,
        waterfront -1.04 -> -0.81 and -1.20 -> -0.92 are FIXED BY CONSTRUCTION; the one
        left is boatyard's, off-frame BY RULING (pinned hero frame). Zero regressions
        across all 99 entry/exit marks; every shot still frames 100% of its samples.
        16 shots move, but only 8 plates would visibly change (a mark shifts >=4 px on
        the 1344x768 backdrop). TASTE REVIEW WANTED on three: cottage (standoff
        +10.0u, character 111 -> 73 px near — the "intimate" Keepers' Spur becomes a
        wide shot; the cheaper alternative is moving the cottage/cottage-steps seam UP
        the steps rather than pulling the camera back), lockhead (-17% character),
        lockfive (far-field character crosses the 50 px rubric floor, 51 -> 49).
        ADVISORY on the 17 ownership-mismatch spans: the 8 worst were ALREADY 100% in
        frame under the live camera, so the 76.5 m mismatch is a TIMING defect (late
        cut), not a visibility one — exit framing only buys margin on it (the worst
        span, 8.8 m of crossing's floor under cottage's camera, goes 0.238 -> 0.485
        edge margin). The lever there is ownership/cutOffset, coordinator's call.
        Self-check: this report's OLD projection agrees with the shipped routes file's
        own ndc to 0.001 (same project(), same cameras).
15:4x COORDINATOR: solver delta ACCEPTED (ee65e90, 3892ee5) — exit-seam framing
      is now the solver DEFAULT for every future town; off-frame exits 5 -> 1
      (boatyard, off-frame BY RULING). Pin + frameExits migration flag moved
      from the temporary sidecar into cameras.json canon (15d6836; sidecar
      retired; zero numeric change, chain fresh, cine 666/0 vs the 1
      pre-existing soft warning baseline). RE-BAKE DEFERRED by design: one
      pass after the custodian's geometry lands. FOR TONIGHT'S TASTE BOARD:
      (a) cottage framing — accept +10m wide shot OR move the cottage-steps
      seam up the stairs (cheaper, interacts with the steps rebuild);
      (b) lockhead -17% character; (c) lockfive far figure 51->49px vs the
      50px rubric floor; (d) boatyard stays pinned unless the user re-rules.
      Mismatch advisory: the 76.5m spans are a TIMING defect (late cut), not
      visibility — lever is ownership/cutOffset, queued as a refinement.

17:05 KEEPERS' STEPS REBUILT (bucket-1 item 3, the audit's worst shot).
        tools/lg_build.py — the legibility pass, same discipline as lk_build.py,
        prefix lg_, collection DIST_legibility, idempotent.
        WHAT WAS ACTUALLY WRONG, measured before building: the flight already IS a
        proper stair in collision — 21 individual tread faces
        (walk_e_keepers-cottage__lock-five_l0_t00..l3_t03, ~0.30 m going / 0.38 m
        rise) plus 3 landings, dropping 7.90 -> 0.28 — and every one of them is
        render-hidden. The art was never built. So the only things rendering in that
        frame were the EIGHT bar_..._railA/B blockout boxes: 8-vertex slabs 2.4 m
        tall standing on edge beside an invisible stair. Those boxes ARE the audit's
        "disconnected floating plank slabs"; the first record render showed them
        exactly as described.
        BUILT: lg_ks_treads (21 tread runs + 3 landings, individual boards laid 30 mm
        under each face's OWN plane), lg_ks_frame (stringers under every flight,
        landing bearers, 16 posts + 11 raking struts founded BY RAY on lf_ground /
        lf_planking; 1 station found nothing and was left unbuilt), lg_ks_rail (24
        posts + top rail + midrail on the blockout rails' own lines, feet ray-cast
        onto the flight this pass just laid). The 8 bar_ rails are now render-hidden
        — bit-identical, still viewport-visible, collision untouched.
        NO RISERS, and that is measured: a riser closing each tread's front stands
        over the BACK of the tread below it, these treads overlap by only 0.05 m, so
        the lower face is not "buried" and the gate rays it — 16 blocked samples from
        the risers alone in the first gated run. An open-riser timber flight is what
        a waterside stair is anyway.
        GATES: region 84,100,20,32 walk QA is IDENTICAL to its pre-build baseline
        (555 samples, 553 walk hits, 99.64%; the 2 remaining failures are
        e_lockhead__lock-five_rung30 and an lf_crest_gate headroom warning, both
        pre-existing and neither mine). FULL 367 walk QA PASSED, bit-identical,
        1308/1308 = 100.00%. geometry_audit 84,100,20,32: 71 meshes, 45 pairs, 0
        offenders, 0 strays. glTF survival --prefix lg_: 3 out / 3 in, 0 white.
        RECORD SHOTS (EEVEE, no camera polishing, via the new tools/lg_shot.py):
        docs/qa/districts/keepers_steps_rebuilt.png and
        docs/qa/districts/lockhead_station.png.
        NEAR-MISS WORTH RECORDING: the first draft of lg_build.py used KEYLG_'s
        predecessor `KEYG_` as its lamp namespace. `KEYG_` is the GATE district's
        prefix — 16 lights including every lantern on the arch — and the idempotent
        clear pass would have deleted all of them on the first run. Caught by a dry
        run before any save. A rebuild pass must own its prefix, and two letters is
        not ownership.
        DEBT: lg_build.py carries a compact copy of lk_build.py's machinery (walk-face
        model, corridor guard, ray founding). If a third place needs it, factor it into
        a shared district library rather than copying a third time.

17:40 WEAVE RAILS (bucket-1 item 4) — 12 of the auditor's 19 measured drop edges
        railed, and the other 7 DIAGNOSED rather than faked. lg_wv_rail: posts +
        top rail + midrail, 2 of them OUTBOARD on brackets because these boardwalks
        are walkable to their very edge (a deck rail is bolted to the outside of the
        edge beam in the real world for exactly that reason). Coordinate contract for
        the next reader of probe/*.json: blend = (x, -z_runtime, y_runtime).
        THE OTHER SEVEN ARE NOT A RAILING PROBLEM. At (60.34,20.30) f7.8,
        (69.93,21.64) f3.1, (63.45,22.98) f12.6, (71.04,25.96) f5.8, (47.64,21.92)
        f9.1, (55.42,20.28) f8.0, (56.71,19.95) f8.0 there is NO ART UNDER THE
        RIBBON within 2.4 m — same class as the lockhead approach this morning: the
        walk graph flies and nothing was ever built under it. A post there would have
        nothing to stand on and a rail would float. Railing them means building the
        Weave's deck under those runs first — bucket 4, and it needs the coordinator's
        assignment (it is a district build, not an edge treatment).
        GATES: weave region 44,76,14,30 walk QA IDENTICAL to its pre-build baseline
        (2652 samples, 2645 hits, 99.74%; the failures there are wv_hut_weave-north_2
        x6 and wv_planking x1, both PRE-EXISTING and neither mine). geometry_audit
        44,76,14,30: 283 meshes, 77 pairs, 0 offenders, 0 strays. FULL 367 walk QA
        PASSED bit-identical 1308/1308. glTF --prefix lg_: 4 out / 4 in, 0 white.
        ALSO FIXED IN THIS PASS: lg_build.py's corridor guard was scoped to the
        Keepers' Steps region only, so when section 2 started placing posts in the
        Weave 30 m west, FACES was empty there and free_box() approved everything —
        a guard that answers "yes" is not a guard. Region widened to cover every
        section in the file; the weave post count dropped 17 -> 10 -> 12 as the guard
        started working and the bracket case was added.
        ITEM 2 (ARRIVAL) NOT STARTED — see the handover note in my report.
16:0x COORDINATOR: custodian items 1/3/4 ACCEPTED (e6a3a86, 1dde0b7, d47333b).
      Keepers' Steps root cause: the "floating slabs" were 8 bar_ blockout
      rail panels beside a CORRECT but render-hidden stair — art was never
      built; now a real flight with rails, blockouts hidden, collision
      untouched. Weave: 12/19 edges railed; 7 reclassified BUCKET-4 (no art
      under the ribbon within 2.4m — same class as the lockhead approach;
      queued as a district build). RISK LOG: (1) prefix near-miss — lg_build
      draft used KEYG_, the gate district's lamp namespace; its clear pass
      would have deleted 16 lights. CANON: A TWO-LETTER PREFIX IS NOT
      OWNERSHIP — dry-run every idempotent clear pass against the live
      inventory. (2) lg_build duplicates lk_build machinery — factor a shared
      district library BEFORE a third copy. ITEM 2 REOPENED SCOPED: I ray-
      attributed occluders from the solved cams — gate arrival IS foliage
      (5 named veg_gate_* objects), but shelf-west's hidden seams are
      shelf_weapon_shop_3 + parapet (NOT foliage; reclassified to the framing/
      re-solve pile). Relief custodian (transcripts expire fast — fresh agent,
      written handover) landing: named-list raise + threshold lantern +
      arrival record shot. Acceptance = ROUTES.probe re-run by me.

16:22 RELIEF CUSTODIAN — ARRIVAL (item 2) DONE, SCOPED TO THE FIVE. tools/ga_build.py
        (prefix ga_ / lamp namespace KEYGA_, idempotent, `-- save` writes), plus
        tools/ga_shot.py (a record frame from the SOLVED del-cine camera, not a
        bbox camera — an arrival can only be judged from the frame the player gets)
        and tools/district_lib.py.
        NAME RESOLUTION, recorded so nobody guesses it twice: veg_gate_rimtreeE_0_2
        IS NOT AN OBJECT. The master carries veg_gate_rimtreeE_0, whose mesh has two
        materials; three.js names the per-primitive children of a multi-primitive
        mesh <node>_0/_1/_2, so the runtime raycast reported a PRIMITIVE. Acted on
        the object; its mat_timber trunk was never touched.
        WHOLE-OBJECT RAISING WAS TRIED FIRST AND REJECTED ON THE RENDER. Measured
        per object, in isolation, by binary search against the solved camera: the
        lift these sightlines need is +2.02 (rimclump_11), +2.64 (_1), +3.06 (_2),
        +2.05 (_12), +1.26 (rimtreeE_0) on bushes 2.5..3.5 m tall that stand on the
        rim road at z 24 — so the clump ends up hanging two metres over its own
        shadow. Rendered at +1.0/+1.8/+2.6: all three float.
        WHAT ACTUALLY LANDED, and why it is still "raise the crown": each rimclump
        is 46 INDEPENDENT leaf quads on mat_leaf_autumn (the tree is a trunk plus
        110). The camera sits 25 deg above the road, so the blocked band is NARROW —
        the cards in the way are the ones at z 25.3..26.6; everything below is
        already under the rays and everything above is already over them. 10 cards
        RAISED (rimclump_11 x7 max 1.83 m mean 1.10; _12 x3 max 1.25) and 21 THINNED
        AWAY (_11 x8, _12 x8, _2 x3, _1 x2; rimtreeE_0 lost nothing). Every clump
        still stands on its own ground; no object moved; no location keyframe, only
        vertex data, restorable from the GA_SRC_* snapshots the pass writes.
        THE THINNING IS NOT TASTE, IT IS THE RENDER'S RULING. A flat 2.4 m cap
        cleared every sightline and left TWO LEAF CARDS HANGING IN MID-AIR under the
        gatehouse window, a metre clear of the bush they came from — visible in the
        frame, so the rule became: a raised card may not rise past its own clump's
        original crown + 0.50 m, and anything needing more is thinned instead.
        crown-tol was solved, not chosen: at 0.10 it turns 28 of 31 raises into
        deletions, at 0.50 it renders with no detached card anywhere.
        RESULT: 151 of 151 camera-to-route sightlines that the five were blocking
        are now clear (sample set = every route/entry/exit sample of shot `gate`,
        densified to 0.40 m, at road +0.06 and body +0.88, admitted ONLY if the
        camera can see it with the five hidden — so no card was ever cut to pay for
        a cliff).
        STOPPED AT THE LIST, AS ORDERED — 36 sightlines are still blocked by OFF-LIST
        foliage and were NOT touched: veg_gate_rimclump_0 (13: spawn:gate,
        valley-gate__gatehouse, __porters-yard), _5 (8: portal:dellhollow-valley-gate,
        __gatehouse, __porters-yard), _4 (6: __gatehouse, __porters-yard), _24 (4),
        _26 (4: __porters-yard), _9 (1: __gatehouse). Those are the parapet-side mass
        the brief ruled is the arrival's enclosure; if the coordinator wants the
        gatehouse half of the street open too, that is a second named list, not a
        judgement call I was allowed to make. Structural residue (also untouched):
        gate_yard 12, gate_arch 8, gate_road 8, gate_palisade 6, walk_lm_porters-yard
        3, and 46 on gate:winch-head__winch-foot which is the gorge descent behind
        yard_ground/cargo_winch_foot.
        THRESHOLD LANTERN: runtime (20.8, 22.3, -3.2) -> blender (20.8, 3.2, 22.3),
        VERIFIED against the blend — a down-ray there lands on the inn flight
        (walk_e_valley-gate__inn_l0_t04 at z 22.71, over the landing at 22.30) and
        that seam, seam:valley-gate__inn, is the one with visibleFrac 0.00 in the
        auditor's gate probe. ga_lantern_threshold: post FOUND BY RAY on the rim road
        at (21.15, 4.49, 23.99) — searched on a ring, not authored; the walk-corridor
        guard refused every foot on the flight itself, which is why it stands at the
        head of the steps and not on them — globe at (21.07, 4.20, 25.93). ORDINARY
        680 W warm (1.0, 0.58, 0.24), 14 m cutoff, the town standard; NO Heartlight
        (world canon: Heartlights are Emberbrook's). Materials reused by name,
        mat_lantern_glass + mat_iron, same assembly part-for-part as gate_lantern_*
        and lk_lantern_*.
        MEASURED SPILL (W/m2, this lamp | all lamps in range): stair head at the
        landing 3.98 | 12.28; stair head at eye height 10.40 | 14.91; flight l0 head
        on the road 4.13 | 25.27; flight l0 midway 5.03 | 14.54; flight l1 foot
        1.65 | 9.47; rim road at the seam 12.03 | 15.64.
        GATES (all green): FULL walk QA PASSED — 367/367 identity bit-identical
        (worst world-space vertex delta 0.000e+00), ray coverage 1308/1308 = 100.00%,
        every walk/bar mesh viewport-visible. Arrival region 12,30,-2,14 is IDENTICAL
        to its pre-edit baseline (598 samples, 598 walk hits, 100.00%, the single
        gate_winch_rope headroom warning pre-existing and not mine) — the lamp post
        did not enter the corridor. geometry_audit 14,44,-4,10 (the brief's runtime
        14,44,-10,4 through blend = (x, -z_runtime, y_runtime)): 160 meshes, 23 pairs,
        0 intersection offenders, 1 stray = shelf_bunting_lines, PRE-EXISTING (it is
        there in the pre-edit blend too). Widened to 12,46,-4,14 so every one of the
        five and the lamp are inside it: 273 meshes, 47 pairs, 0 offenders, 0 strays.
        glTF survival --prefix veg_gate_rimclump_,veg_gate_rimtreeE_,ga_: 43 out /
        43 in, 0 white, 0 flat-white COLOR_0, 0 procedural node trees exported.
        RECORD SHOT: docs/qa/districts/gate_arrival_fixed.png (EEVEE, the solved
        gate camera, no polishing).
        DEBT PAID FORWARD, PARTLY: tools/district_lib.py now holds the walk-face
        model, corridor guard and ray founding ONCE, and ga_build imports it — this
        was the third place that needed them, which is the line the coordinator's
        risk log drew this morning. lk_build.py and lg_build.py still carry their
        copies ON PURPOSE: their output is already in the master and the only honest
        proof of swapping the guard under two accepted districts is a full re-run
        plus a re-gate of both, which was not this pass's assignment. The migration
        target now exists; the next builder to open either file should import and
        delete the copy.
        RISK WORTH RECORDING: gate_build.py's idempotent clear pass removes every
        object whose name starts with gate_/veg_gate_/KEYG_. Re-running it would
        REBUILD all five clumps and silently undo this pass. ga_build.py is safe to
        re-run afterwards (it restores from GA_SRC_* and recomputes), but somebody
        has to know to run it.
16:4x COORDINATOR: item 2 LANDED AND ACCEPTED (4ebeb92, relief custodian) —
      per-leaf-card surgery (10 cards raised, 21 thinned, crown+0.5m rule so
      nothing floats; 151/151 targeted sightlines clear; no object/trunk
      moved), threshold lantern ray-founded at the stair head (680W, spill
      quoted), gates green (full 367 bit-identical, region identical to
      baseline, 43/43 glTF, 0 white). Residue DEFERRED by scope: 36 sightlines
      blocked by OFF-LIST foliage (gatehouse half: rimclump_0/5/4/24/26/9) +
      structural (gate_yard/arch/road/palisade) — next named list when the
      gatehouse spur matters. HAZARD FENCED: warning header written into
      gate_build.py (its clear pass would silently undo the surgery; ga_build
      restores). district_lib.py now holds shared machinery (3rd copy became
      THE copy). RE-BAKE RUNNING: all 17 del-cine backdrops + GLB against the
      day's geometry (steps, rails, lockhead district, foliage, lantern) —
      current framings; the exit-seam re-solve stays a separate user-gated
      pass. Acceptance re-probe (ROUTES.probe gate) after bake.
17:2x COORDINATOR: USER RULINGS — lighting variant C ratified (sun 12.0 energy
      @ (1.0,0.79,0.56), rot_x 0.93, world 2.1, exposure +0.15: late-afternoon
      golden, replacing the -0.52-exposure dusk). NEW palette direction: town
      skews too brown — blend greens into the autumn foliage (riverside bias),
      more river in frame (joins the framing/re-solve pile), possibly more
      town color later. Lighting+palette custodian launched: rig -> green mix
      (35-45%, deterministic, material variants, gate-surgery clumps vertex-
      untouched) -> 3-probe taste gate to me -> full 17-shot re-bake. UI agent
      separately on FF-grammar restyle + CC0 monster sprites + genart battle
      backdrops (after look lands). Dusk-grade bake killed at 6/17 (right call
      confirmed by ruling).
17:0x LIGHT+PALETTE: RIG LANDED (a0cf9ab). tools/look_golden.py is variant C
      written down, idempotent: SUN_key 5.0->12.0 W, (1,0.545,0.275)->
      (1,0.79,0.56), rot_x 1.1858->0.93 (~53 deg elev; azimuth untouched),
      World Background 1.6->2.1, exposure -0.52->+0.15 (AgX / Med High
      Contrast unchanged). The bounce/fill kit (60 CLIFF_BOUNCE/FILL_bounce/
      KEY_gorge instruments) deliberately NOT re-scaled — chasing a key change
      through balanced fills is how a lighting pass becomes a re-lighting
      project. FOUND AND FENCED: cine_bake.py grades from defaults.exposure in
      townmap/dellhollow.cameras.json, NOT from the blend — an exposure set
      only in the master would have been silently discarded at bake time and
      the 17 backdrops would have shipped at the old grade. The number now
      lives in the cameras file, look_golden.py READS it and hard-asserts the
      blend agrees, so the two cannot drift again. cine_solve re-run: zero
      camera numbers moved (exposure + stamp only), --check green.
17:1x LIGHT+PALETTE: GREEN MIX LANDED (0ddc88f). 65/159 town leaf clumps (41%)
      -> mat_leaf_green, 9/22 distant upstream crowns -> mat_leaf_green_far.
      Riverside bias measured, not asserted: d<18m 59% green | mid 35% | upper
      rim 18%, where d = (zmin - local water surface) + 0.6*(plan distance to
      the river band) and the waterline is READ OFF the m_water pools so a
      re-cut river moves the bias with it. Deterministic by sha1(name), never
      random(); re-run converts the identical set (verified: 2nd run 0
      converted, 74 already green).
      THE FINDING THAT SHAPED THIS: leaf colour is NOT in the material. The
      survivability pass baked the procedural ramps into the `Col` corner
      attribute and rewired Base Color to the surv_col VertexColor node
      (finding 219), so a green material with a flat Base Color would export a
      factor the runtime MULTIPLIES by the still-autumn COLOR_0 (muddy), and
      one with a hue-shift node would export nothing at all — Cycles green,
      runtime autumn. Green therefore travels where autumn travels, in `Col`;
      the derived material is the MARKER of the set (idempotency, reviewable
      manifest, re-tintable later). Transform is a channel swap r'=kr*g,
      g'=kg*r, b'=kb*b — preserves the clump's internal hue gradient instead
      of flattening it, exactly invertible (`-- revert` needs no backup
      sidecar), and tuned to hold LUMINANCE (0.152->0.162 town, 0.098->0.099
      far) so the frame's value structure does not move, only its hue.
      UNTOUCHED ON PURPOSE: the five surgically edited gate occluders
      (rimclump_1/2/11/12, rimtreeE_0) — this pass writes vertex colour, so
      they are excluded OUTRIGHT rather than merely "no geometry edits";
      veg_farwallcrown_* (the north skyline IS the autumn identity); grass/
      fern/creeper (already green; measured first step, not a repaint).
      GATES: master_walk_qa PASSED, 367 walk_/bar_ bit-identical (free, since
      zero geometry moved — run anyway). glTF: all four leaf materials deliver
      a real albedo through COLOR_0 (mat_leaf_green effective [0.100 0.191
      0.057]); survival round-trip clean, 0 white district-owned materials.
17:1x LIGHT+PALETTE: TASTE GATE SENT, HOLDING. Three river-facing probes at 48
      samples, cameras built exactly as cine_bake builds them —
      docs/qa/districts/golden_{gate,quay-west,waterfront}.png. WATER VERDICT:
      no shader change proposed or applied. The river read brown because of
      the dusk rig, not because m_water is murky — its Base Color is already a
      blue-teal (0.04,0.105,0.12) at roughness 0.1, i.e. almost entirely a
      mirror of the sky. Under the new key the waterfront river patch measures
      [0.43 0.53 0.50]: emphatically not brown. If anything the risk has
      inverted (it now reads a saturated pool-turquoise), which is a taste call
      for the coordinator, not a defect to fix unasked. Full 17-shot re-bake
      held pending explicit GO.
17:5x COORDINATOR: USER RULING after probe review — golden light + greens
      approved and enjoyed, BUT buildings read uniformly green. New direction:
      green+brown stay primary; HOUSES get a mixed muted palette (~6 storybook
      accents, roofs their own set, timber stays brown, deterministic w/
      neighbor-difference, luminance-held). Bake STOPPED mid-run again (second
      superseded look — right call both times; the taste loop is cheaper than
      the bake). Lighting custodian redirected: investigate building color
      topology -> design note -> variety pass -> 4-probe taste gate (gate,
      quay-west, waterfront, + weave hut row) -> THE one bake.

## 2026-07-30 17:20 — UI RESTYLE: FF window grammar, Emberbrook materials (mock pass)

Battle/menu/shop UI rebuilt from the FF7/FF9 design language with a modern twist.
The user's note was that the old UI "fulfilled the minimal version of the feature
set" but read "much more bare" than the FF screens.

- **ui_kit.js** — the whole palette is now `:root` custom properties plus ONE
  window primitive `.eb-win` (vertical timber gradient, 2-tone brass bevel drawn
  with two inset box-shadows, 8px radius, faint SVG paper grain). New shared
  pieces: `EBUI.win/gauge/cur/portrait/bustUrl` + `assetBase`, and a
  `layout:'full'` panel mode (head/foot become free-standing windows) for the
  FF9-shaped pause screen. The FF cursor is CSS-drawn (no font dependency) and
  bobs; the bob dies under prefers-reduced-motion, the glyph never does.
- **menu.js** (VIEW only) — FF9 layout: nav column / character plate with a LARGE
  bust from `assets/characters/<id>/bust.png` / help-text strip / gold window
  bottom-right. HP-MP-XP as proper gauges with numerals; MP is a reserved column
  rendering "—". EQUIP shows a live before→after block. `ui.page` is now the
  highlighted member, not a page of cards.
- **shop.js** (VIEW only) — stock window + description strip + gold window,
  keeper name as the window title, quantity step as its own spinner in the strip.
- **battle_turnbased.js** (presentation only) — FF7/9 layout: corner HUD window,
  foes standing on a ground line with name tags, slim log strip, and a bottom
  band of TWO windows: vertical command list (left) and the party status table
  (right: 40px bust, name/LV, HP gauge + numerals, reserved MP column). Damage
  numbers are FF-sized with a hard outline and an overshoot pop (white damage,
  green heal, amber crit if the kernel ever emits one).
- **Monster placeholders** — `public/assets/monsters/placeholder/<monsterId>.png`,
  six CC0 sprites from Clint Bellanger's *Tiny Creatures 1.0* (OpenGameArt, CC0
  1.0 Universal — license read on the page and in the archive, recorded in
  MANIFEST.md). Wired through a path CONVENTION, not a list; a missing file falls
  back to the old CSS silhouette. Pixel sources (<=64px) snap to an integer scale
  and render nearest-neighbour.
- **Backdrop plates** — `Battle.art` resolves `assets/battle/<zoneKey>.png`,
  cover-fit and full-bleed, applied only once the image decodes; the per-zone
  gradient is painted first and stands as the fallback. No zone list in code.
- **tools/ui_mock.html** — boots the REAL modules against the REAL rules data with
  a posed party, for screenshotting. Serve the repo root, open /tools/ui_mock.html.
- Fixed a real layout bug on the way: the battle bottom band was `width:100%` plus
  padding under content-box, overflowing the clipped root by 88px.

Mocks: docs/qa/ui/{battle-cmd,battle-target,battle-items,menu-root,menu-party,
menu-equip,menu-items,shop}.png

Suites: economy 204/0 · encounter GREEN · battle_sim ALL ENVELOPES GREEN ·
slice 532/0 · cine 666/0 (1 pre-existing soft warning).
18:2x COORDINATOR: USER UI VERDICT — timber/golden windows rejected; rulings:
      classic FF6/7 BLUE windows, menus become OVERLAYS over the paused scene,
      battle becomes a STAGE (party sprites vs monsters on real per-zone
      plates). Battle plates v1 GENERATED via genart (golden-hour, style-refd
      to our renders) and committed; vesper/pose.png (chroma magenta full-body)
      identified as the party battle-sprite source. UI v2 successor agent
      launched on written handover (v1 transcript expired) — re-tint, overlay
      scrim, stage layout w/ keyed sprites, tightened status band; mock-first
      hold for user review again.
17:3x LIGHT+PALETTE: BAKE STOPPED ON ORDER at camera 1 (nothing written; the 8
      modified bg.png in the tree are still the killed dusk bake's, untouched by
      me). Two new user rulings folded into one pass: house variety + river
      flow. Design note FIRST, as instructed: docs/plans/house-variety-design.md
      (7f47dc6).
      TOPOLOGY, because it changed the plan. Building colour here is neither
      texture nor vertex attribute: it is one or two LITERAL RGBs in Mix node
      inputs over a greyscale photo texture, one kit template town-wide — except
      the 200-object lf_* Lockfoot kit, whose Mix sits at factor 1.0 so the image
      is fully overridden and the colour is the mesh's `Col` (the survivability
      shape the foliage uses). Two mechanisms, so two code paths.
      THE BRIEF'S ASSUMPTION WAS WRONG, MEASURED: the WALLS already vary. The
      nine weave huts carry five distinct wall colours and no two ADJACENT huts
      match today; the shelf row already ran five paints across seven buildings.
      What did not vary: Dellhollow had exactly TWO roof materials and both were
      green — mat_shingle_mossy (0.125,0.215,0.08) on 17 objects, lf_shingle (Col
      0.155,0.174,0.090) on 10. Twenty-seven roofs, one colour.
17:4x LIGHT+PALETTE: HOUSE VARIETY + RIVER FLOW LANDED. Roofs 23 objects -> four
      variants (moss 26% / cedar 30% / slate 26% / shake 17%), luminance held
      0.144-0.202 vs moss 0.186 and the lf_ set within 1% of the kit's 0.164.
      Deterministic sha1 + a 9 m neighbour-difference pass; where a cluster is
      over-subscribed (the weave-north knot has five roofs inside 9 m using all
      four colours) the fallback MAXIMISES separation instead of taking an
      arbitrary first choice — 1 residual same-colour pair at 5.8 m, and those
      two are 11 m apart vertically. Shelf row's two duplicate paints -> madder
      and slate blue, completing the six-accent set (the kit already held five).
      Neither repainted building has an interior scene, so no exterior/interior
      divergence created.
      RIVER: m_water rebuilt — world-space noise squashed 0.11 along +x (~9x
      anisotropy; the flow axis is ASSERTED from the pools' own monotone step
      3.4 -> 0.0 -> -1.55 -> -4.0, not typed), a second cross-flow chop, Bump for
      reflection breakup, and an Ambient Occlusion node used as a
      proximity-to-geometry probe driving foam + roughness where the water meets
      the weir, lock walls, piles, hulls and slipway. Turquoise UNCHANGED per the
      ruling.
      GLTF, and it cost two measured failures worth recording: (1) the obvious
      build — one Principled with Base Color a Mix — exports NO baseColorFactor,
      and m_water has no texture and no COLOR_0 to multiply, so the river arrived
      literally WHITE. (2) master_survivability's export-proxy cure did NOT
      rescue it: that trick works for mat_darkfall and the pennants because their
      render branch holds no Principled, so the exporter cannot help but find the
      proxy; here the render branch holds one and the exporter took it from BOTH
      branch orders. SHIPPED: two flat-coloured Principled lobes mixed by the
      foam mask, no linked Base Color anywhere — which is what a mixed albedo
      physically is. m_water now exports (0.04,0.105,0.12). Also confirmed the
      tint-kit materials (mat_timber, mat_wallwood_dark, the shelf paints) were
      ALREADY factor-absent before this pass and are fine, because a textured
      material multiplies that factor by its texture; the derived variants
      inherit exactly the same state and introduce nothing new.
      GATES: walk QA 367 bit-identical; glTF survival CLEAN 0 white; albedo tool
      green on all four roof variants and on m_water.
17:5x LIGHT+PALETTE: TASTE GATE #2 SENT, HOLDING. Four probes
      docs/qa/districts/variety_{gate,quay-west,waterfront,weave}.png.
      THE MEASUREMENT THE GATE NEEDS, and it reframes the whole brown question.
      Ray-cast screen-area tally per camera says ROOFS ARE 1.5-5% OF ANY FRAME.
      What fills these frames is CLIFF AND ROCK — mat_gate_cliff 30% + mat_rock
      17% + m_rock 12% on gate; mat_rock 25% on waterfront; mat_rock 16% +
      m_rock 10% on weave — and then WOOD: m_wood 5-15%, lf_deck 6-15%,
      m_stair 5%, mat_timber ~5%. Buildings are a minority of pixels in this
      town. So the roof pass is real and reads well in weave (7.3% of that frame
      is roof, now three colours) and will read in the shelf cameras, but it
      CANNOT move gate or quay-west much, and the numbers say so: before/after
      diff is 0.1% and 0.2% of pixels there. The town reads brown because it is
      a cliff town made of rock and timber, not because the houses were bland.
      Next lever is the cliff/ground/deck palette plus the moss overlay literal
      (0.09,0.16,0.05) that a dozen materials spray on every up-facing surface —
      both above my authorization and both now quantified for the ruling.
19:0x COORDINATOR: TASTE GATE #2 PASSED, THE BAKE IS RUNNING (light C + greens
      + roof variety + flowing river, one coherent state). Two findings
      elevated to canon: (1) SCREEN-AREA TALLY — cliffs 30-42% of frame
      pixels, roofs 1.5-7%; "the town reads brown because it is a cliff town."
      Next color lever = cliff/ground/deck palette + moss overlay literal;
      USER-RULED, on tonight's board with numbers. (2) glTF: the export-proxy
      cure FAILS on Principled-bearing Mix trees (m_water arrived white twice,
      measured); custodian ordered to write it into the survivability docs.
      Also: walls already varied (measured before transforming — no repaint);
      the town had exactly TWO roof colors, both green — now four variants
      across 23 roofs, deterministic w/ neighbor separation. Probes forwarded
      to user. UI v2 agent building blue/overlay/stage mocks in parallel.
19:3x COORDINATOR: USER TRANCHE-2 DIRECTIONS (probes review, bake left
      running): (A) POPS OF COLOR — cliff dominance accepted; well-placed pops
      worth 5-10% of frame pixels change identity (awnings/banners/doors/
      boats/laundry); (B) CLIFF COMPLETION — at least one whole wall missing
      (gray background leak, weave rim), and built faces at inconsistent
      resolution; audit + buildout; (C) WATER TRANSPARENCY — shoreline is a
      hard cutoff; want terrain visible through shallow water fading with
      depth (verify bed geometry exists; Cycles depth shader; export-safe
      runtime water per finding 221). Read-only investigator launched (three
      design docs + per-camera measurements) while THE bake runs; tranche-2
      execution after bake + review.
17:5x UI-RESTYLE v2: THREE RULINGS LANDED, MOCK SET RE-SHOT, HOLDING FOR REVIEW.
      All three user rulings are in, and the predecessor's architecture paid off
      exactly as promised: ruling 1 was almost entirely a :root edit.

      1. CLASSIC FF BLUE. ui_kit's :root re-tinted, nothing else re-plumbed:
      deep navy-to-royal-blue vertical fill (#0e1038 -> #2a2b8c), crisp 2-tone
      SILVER bevel (#eef1ff over #7b84c0), white ink (#f3f5ff). Amber survives
      ONLY as highlight — cursor, selected row, window titles, gold and HP
      numerals. The paper grain KEPT on blue at .045 (it stops the fill reading
      as a flat CSS box). Four hand-mixed brown hexes that had escaped into
      menu.js/shop.js/battle_turnbased.js were replaced with four new derived
      properties (--eb-card, --eb-card-cur, --eb-chip, --eb-inset-lt/dk), so the
      next re-tint is genuinely one edit — v1's was not, quite.

      2. MENUS ARE OVERLAYS. Veil scrim 48% -> 31% (#060a1c4f) keeping the 2px
      blur, which is a depth cue rather than a darkener and is what lets a dark
      navy window sit off a dark town render without dropping the scrim further.
      Window fill ~86% opaque, so the frozen scene reads faintly THROUGH the
      glass as well as between the windows. New layout:'float' in ui_kit (the
      shop) joins layout:'full' (the menu): both step the outer frame back to
      nothing so head, foot and body windows float separately. Both are now
      height:auto — the menu's fixed 660px box was letterboxing its own content
      and painting blue over scene nobody asked it to cover.

      3. BATTLE IS A STAGE. Foes left, party right, ONE bottom-aligned ground
      line, cast-shadow ellipse under everything that stands on it. Found and
      fixed the thing that would have broken the ground line: monster name tags
      were IN FLOW, so a tagged monster stood ~40px higher than an untagged
      hero — tags now hang out of flow below the feet. Party sprites are the
      pose plates chroma-keyed AT LOAD (EBUI.poseSprite): m = min(r,b)-g, soft
      cut 45..95, despill 0.85, largest-connected-island (both shipped plates
      carry a stray smudge in the top-left corner), then crop to opaque bounds
      so the sprite's FEET are its bottom edge. At load and not in a build step
      deliberately: dropping assets/characters/<id>/pose.png in the repo is then
      the WHOLE job for a new character. Animation is CSS transforms only — idle
      bob, step-forward on act, flinch on damage, grey-ghost fade on KO; under
      prefers-reduced-motion the bob/step/shake die and the damage number and
      the KO fade do not (they carry information). Status band tightened to
      fixed FF9 measures and pinned right, command window pinned left, plate
      showing through the gap — and the item sub-menu now opens INTO that gap
      instead of over the log strip, where it had been covering its own
      "Use what?" prompt. Busts stay, at 30px.

      NOTE FOR THE COORDINATOR: maren/pose-front.png is ALSO a chroma-magenta
      full-body plate in the same style, so the pose convention is an ordered
      pair ['pose.png','pose-front.png'] and Maren walks onto the field today
      rather than "when her art lands". Both heroes are in the mocks. Say the
      word and it drops back to pose.png only.

      Verified against the REAL plates: forest and meadow both cover-fit clean
      at 16:9, and blue-on-scene was legible at both extremes (dark del-cine
      quay-west town render and the bright meadow plate) with no compromise
      needed — the silver bevel does the separating work on dark scenes, the
      dark navy fill does it on bright ones.

      Mocks: docs/qa/ui/{battle-cmd,battle-target,battle-items,battle-meadow,
      menu-root,menu-party,menu-equip,menu-items,shop}.png · tools/ui_mock.html
      now poses a REAL scene plate behind the overlays (&bg=<path>, &bg=none).

      Suites: economy 204/0 · encounter GREEN · battle_sim ALL ENVELOPES GREEN ·
      slice 532/0 · cine 666/0 (1 pre-existing soft warning). battle_rules.js
      and play3d.html untouched.
20:0x COORDINATOR: USER RULING on battle presentation — v2's single-row sprite
      stage reads "mobile game"; ruled: a 3D BATTLE ARENA. Plan: three.js
      stage under the blue UI windows — staggered FF formations in depth, FF
      battle camera w/ intro sweep, party = rigged rogue.glb (billboard
      fallback via the chroma keyer for model-less characters), enemies =
      CC0 low-poly 3D models (Quaternius/KayKit, license-manifested; fallback
      chain 3D->billboard->pixel->shape), arena = simple per-zone 3D ground +
      the genart plates on a background cylinder (plates regenerable "with
      awareness of the 3D model" — horizon-matched). Headless-safe (suites run
      DOM-less; stage lazily constructed; DOM stage stays as no-WebGL
      fallback). Battle-arena v3 agent launched, mock-first.
20:0x TRANCHE-2 INVESTIGATOR: THREE DESIGN DOCS LANDED, READ-ONLY THROUGHOUT.
      docs/plans/{pops-of-color,cliff-completion,water-transparency}.md. Master
      never written; bake untouched (Cycles had METAL, all probes CPU ray-cast).
      Four read-only passes over the master: a 224x128 per-pixel ray tally of
      all 17 solved cameras (object + material + distance), the same tally with
      volume-only FX cards SKIPPED so a real background leak is separable from a
      haze card, a 13k-sample down-ray bathymetry stack over the four water
      sheets, and a placement probe that projects a proposed rectangle into
      every camera and occlusion-tests 25 points. Every screen-% in the docs is
      measured, none estimated.
      (B) THE "MISSING CLIFF WALL" IS NOT MISSING — IT IS AN 8-VERTEX GREY BOX.
      True sky-leak with FX skipped is 0.00% on 13 of 17 cameras, including
      every camera the user was looking at. The flat grey is `cliff_town`: 8
      verts / 6 polys / 18,232 m2, material `m_rock` = a bare Principled #716D6A
      with NO texture and NO bump, standing in for the whole south wall. It
      fills 3.0-22.6% of TEN frames at 2,664-5,495 PIXELS PER MESH EDGE — one
      edge spans 2-3.5 entire frame heights. And the properly built far wall,
      `cliff_far` (654 verts, textured mat_rock_farwall), is visible in ZERO of
      the 17 cameras: every camera looks south, so the whole vista budget went
      into the one wall nobody sees. Two genuine voids exist and are the same
      hole — the missing EAST closure (lockfive 19.96%, cottage-steps 16.26%,
      54-73% of leak rays pointing DOWN); ray-traced against candidate planes, a
      single wall at x=140, y -8..54, z -14..22 catches 10,384 of 10,384 leak
      rays. Build plan: replace cliff_town with ~2,600 verts in four
      distance-tiered patches at 60-80 px/edge (matching gate_cliffface's 43 and
      shelf_cliffface's 45-76), one 560-quad east wall, and three targeted
      resolution repairs (qm_stair_underworks 204 px/edge at 19 m; gate_ground's
      west lobe 156 at 13 m; the wv_hut wall panels 118-233).
      (A) THE BRIEF POINTED AT THE WRONG CAMERA. Per-pixel material tally with a
      narrow "painted panel / cloth / awning / flag / produce" filter: quay-west,
      one of the two shots the user flagged, is at 9.01% — the SECOND most
      colourful frame in town. It reads brown because 45.4% of it is rock plus
      8.4% cliff_town, not for want of paint. gate is right (0.61%). The real
      brown belt is the six EASTERN cameras — cottage-steps 0.00, lockfive 0.00,
      north-landing 0.03, crossing 0.11, fishdock 0.16, cottage 0.17 — because
      every painted object in Dellhollow lives west of x~65 and the lf_* Lockfoot
      kit got timber, stone and shingle and nothing else. Town mean 3.07%.
      Calibration from objects already in the file: a 23 m bunting run + line =
      1.20% at 20-30 m, one awning 0.06-0.25%, a painted panel 1.2-4.2%, a hull
      1.06%; general rule 1 m2 of face-on colour = 0.13% of frame at 33 m /
      0.36% at 20 m. 47-row placement table with world coords, per-camera
      occlusion-tested screen-%, and palette; lands all 17 frames at 5.8-12.7%.
      Two free wins in the census: the nine existing awnings are >50% NEUTRAL
      GREY by loop count, and lf_bunting_0..3 are 720 of 810 loops brown rope,
      strung at z 0.16-1.64 where nothing sees them — both are `Col` edits with
      zero geometry.
      (C) THE BED EXISTS. THE BATHYMETRY IS THE DELIVERABLE, NOT THE SHADER.
      94-98% of wet samples have a bed under them, but `riverbed` and
      `lf_riverbed_tail` are 8-vertex FLAT SLABS: 4,999 of 6,165 mid-pool samples
      land in one 0.5 m depth bin (median 4.10 m), downstream 3,356 of 3,633 at
      3.50 m, and the upstream pool is 7.50 m deep over the same slab. The
      shoreline profile is a step — upstream goes 0.21 m -> 7.25 m in one 0.75 m
      cell. So a depth-transparency shader alone would change almost nothing;
      there is no shallow zone to see through. Second cause, separately measured:
      43-79% of each pool's perimeter is the water QUAD'S OWN straight
      rectangular edge floating over open bed, never meeting land at all — the
      dead-straight diagonal in variety_waterfront.png is the corner of a box.
      Shader design: keep m_water's two FLAT lobes (finding 221) and bake depth
      into a `Col` attribute with rgb=WHITE (the neutral element, finding 218)
      and a=depth ramp, driving both lobes' Alpha; Cycles alpha-blends, no
      volume, no transmission, no extra bounce budget. Runtime tier 1 =
      alphaMode BLEND + fixed alpha 0.72 (guaranteed); tier 2 = glTF multiplies
      COLOR_0's ALPHA channel too, so the same bake could carry the depth fade to
      the runtime for free — one timeboxed experiment, measured via the GLB chunk
      table, then fall back. Depth pass is immune by construction (cine_bake
      renders depth under a material_override), so character occlusion cannot
      regress. Work list: 3 shelves (~540 verts) at the only 49 m of gentle bank
      any camera can see (lockfive 27.5 m, boatyard 15.5 m, cottage-steps 6.5 m),
      plus extending the water footprints so no quad edge floats inside a
      frustum.
      RE-BAKE ARITHMETIC: cliff forces 15 of 17, water forces 9, colour forces
      16 — union 17. Land them as one tranche and bake once. Ordering is
      CLIFF -> re-probe -> COLOUR, because the colour budget is currently
      measured against frames in which up to 22.6% of the pixels are a grey slab
      that is about to be replaced.
20:5x COORDINATOR: THE BAKE LANDED (18:20, 2683.6s, 17/17 healthy, all
      spawns resolved) — committed 154b280 after I recovered it: the lighting
      custodian's post-bake resume DIED SILENTLY at its completion watch; the
      watcher had fired at 18:20 with a clean report and nobody woke up. Two
      hours lost; lesson re-learned: long-wait resumes are fragile, coordinator
      must spot-check quiet agents against their watchers. SUITES: cine
      667/0 with ZERO soft warnings (fresh bake cleared the pre-existing one),
      slice 532/0. Task 9 CLOSED; legibility fix round (task 6) CLOSED — gate
      arrival acceptance implicit in the fresh bake + 667/0. TRANCHE-2
      CUSTODIAN LAUNCHED (user: "no reason to block") — sole master owner,
      serial: cliff Tier A -> single-frame taste gate -> full cliff -> re-probe
      -> color -> water geometry -> shader; probes promoted to tools/; ONE
      bake at the end, coordinator-triggered. Arena v3 building in parallel
      (non-master: JS + CC0 assets).
21:1x COORDINATOR: USER DIRECTION — MUSIC ("FFIX's soundtrack is a big part of
      what I fell in love with"). Music agent launched: Web Audio system
      (data-driven scene->track map, loop-point seamless looping, position
      SURVIVES the full-page-load scene transitions via sessionStorage,
      battle duck -> victory fanfare -> field resumes at position, autoplay
      unlock on first gesture, headless-safe) + first soundtrack: timeboxed
      Lyria-via-Gemini-key investigation (genmusic.mjs if it works), CC0
      fallback with license manifest either way. Seven tracks briefed
      FFIX-style: emberbrook / dellhollow / valley / interior / battle /
      victory / defeat. Three agents now running: tranche-2 custodian (cliff),
      arena v3, music.
18:5x TRANCHE-2 CUSTODIAN: PROBES PROMOTED, CLIFF TIER A BUILT, TASTE GATE OUT.
      Six read-only scratchpad probes are now tools/t2_probe_{tally,leak,chroma,
      place,shore,report}.py with the 50-row placement table at
      tools/blends/districts/t2_color_cands.json, so every number in the three
      tranche-2 plans is re-runnable against the post-build master rather than
      being a one-shot investigation (8a015d3). New tools/t2_probe_render.py
      renders ONE camera the way cine_bake builds it (same build_cam, same
      AgX/+0.15 grade, GPU) into docs/qa/districts/ — the shipped plates are
      never touched, and it can --hide an object for the render only.
      C1 TIER A: tools/t2_cliff_south.py builds cliff_town_a, 2,255 verts /
      2,160 polys over x 58..112, z -9..37, 1.00 m columns x 1.00 m rows in the
      visible band = 80 px/edge at lockhead's 33 m and 45 px at 59 m, inside the
      60-80 band gate_cliffface (43) and shelf_cliffface (45-76) hold. The
      8-vertex cliff_town placeholder is LEFT IN PLACE and the new patch sits
      behind its y=0 face, so the committed master is sound at every point in
      the tranche; the taste-gate frame hides it at render time only.
      SIX TAKES TO GET THE FRAME, and three of them were findings, not fiddling:
      (1) the plan's mat_rock_farwall is not a rock material, it is an
      ATMOSPHERIC PERSPECTIVE material (Mix.001 0.60 toward blue-grey 0.33,0.35,
      0.45 plus Mix.002 1.0 toward 0.30) authored for cliff_far at 80-99 m; at
      33 m it renders a cold grey slab ten metres from warm-tan lf_ground, the
      opposite of the plan's own goal. Recession must come from the C2 south
      haze card instead. (2) NOTHING in Dellhollow's rock kit is UV-mapped —
      every one runs TexCoord.Object -> Mapping -> Image Texture, and a 2D image
      fed a 3D vector uses only X and Y, so on a wall in the x-z plane the rock
      DOES NOT VARY WITH HEIGHT and the texture's second axis is the wall's own
      DEPTH. mat_rock at scale 0.17 (5.9 m period) crossed with the relief
      rendered a grid of 6 m rectangular blocks. Fixed with mat_rock_townwall, a
      copy of mat_shelf_cliff with Mapping rotation X=90deg so the rock maps to
      x-z, at the built faces' own 1.05 scale — the same physical rock as the
      two faces the plan says to match. (3) from_pydata() leaves every polygon
      FLAT, so a 1 m quad at 35 m is a 68-pixel facet with one constant normal:
      take 6 was a grid of hard-edged rectangles for that reason alone. Smooth
      shading fixed it. Also replaced the plan's periodic ledge sawtooth with
      seven incommensurate plane-wave octaves plus a soft strata bias — a
      regular vertical period under a raking 53-degree key cuts hard terraces,
      and terraces read as machining.
      GATES: master_walk_qa 367/367 bit-identical (baseline captured before the
      build, identical after); geometry_audit on x 55..115 y -8..4 clean, 0
      intersections / 0 strays; clearance ray-cast pushed 0 vertices this take
      (22 on the previous shape) — every vertex is measured against the town
      before it is placed, because gate_cliffface already reaches y=-0.6, inside
      the placeholder's own volume. Probe: docs/qa/districts/t2cliffA_lockhead.png
      (48 samples, 1792x1024, 33 s). HOLDING for GO before tiers B/C/D; not
      idling — promoting the next phases' scripts meanwhile.
21:5x COORDINATOR: CLIFF TIER A GATED AND APPROVED (30d980e; probes promoted
      8a015d3) — the 22.6% gray void in lockhead is warm striated wall, 2,255
      verts at 45-80 px/edge, placeholder retained until all tiers land
      (sound-at-every-commit discipline). Three deviations ratified: warm
      townwall material over the atmospheric farwall mat (recession belongs to
      the haze card), 90-degree mapping rotation, organic octaves over sawtooth
      ledges. CANON DISCOVERY logged: the town's vertical-striation rock style
      is an ACCIDENT (Object-coord mapping ignores height on x-z walls) —
      kept tonight for consistency; town-wide remap = future user decision.
      GO issued for tiers B/C/D + east wall + haze + resolution repairs.
      Before/after forwarded to user (async FYI).
21:6x MUSIC: SOUNDTRACK + SYSTEM SHIPPED (5429a68, 9ed3fad, 4aaf1eb, 20c2d98,
      fc6a11f). LYRIA WORKED — the repo's existing GEMINI_API_KEY reaches
      lyria-3-pro-preview (~2.5 min composed pieces, own section markers) and
      lyria-3-clip-preview (30 s), both returning MP3 DIRECTLY, so no
      transcode and no ffmpeg (there is none on this box). NO CC0 FALLBACK
      NEEDED: all seven tracks are machine-generated, so there is no
      third-party licence and no attribution to carry in the credits.
      SOUNDTRACK 17.4 MB: emberbrook 147s / dellhollow 117s / valley 150s /
      interior 171s / battle 155s / victory 12s / defeat 7s; briefs, prompts
      and format in public/assets/music/MANIFEST.md, per-file .gen.json is
      each track's own generation record; regenerate with
      `node tools/genmusic.mjs --all`.
      LOOP POINTS ARE MEASURED, NOT GUESSED (tools/music_loops.mjs): decode
      via afconvert, 24-band log spectrum every 46 ms, find the pair of
      moments whose context is most alike; intro and outro excluded by an
      energy envelope. Seam reported against a random-pair baseline —
      interior 0.079 and dellhollow 0.10 are clean, valley 0.28 the worst —
      and each track gets a loopXfade sized to its own measurement, which
      music.js bakes into the samples so the loop stays a native gapless
      AudioBufferSourceNode loop. Gains equalised from measured level.
      SYSTEM public/js/music.js (window.Music): data-driven scene map
      (exact, then ordered rules, FIRST MATCH WINS — '-int' above 'del-' is
      why del-inn-int gets the hearth air); resumes ACROSS THE FULL PAGE LOAD
      that transitionTo() performs, measured 0.00 s drift over a real
      del-cine -> del-boatyard navigation; resume offset resolved when sound
      STARTS, not at boot, because a fresh page has no user activation and a
      boot-frozen position would resume seconds behind. Battle flow
      self-arms by wrapping Battle.start; the fanfare fires off Battle.last
      (assigned BEFORE the outro) because start()'s promise settles far too
      late for a cue that belongs on the word "Victory"; field theme parks and
      RESUMES AT ITS POSITION. Battle cues pre-decoded (a cold 3.5 MB track
      cost ~1 s and the encounter is the transition that most needs to be
      immediate). Autoplay-safe (nothing built before the first gesture, no
      errors while inert), headless-safe, `?nomusic=1` opt-out, decoded-buffer
      cache capped (a 150 s stereo track is ~53 MB).
      VERIFIED IN BROWSER: qa_music.html 31/31; then against the REAL page —
      music.js injected into play3d.html?scene=del-cine, self-armed, and
      Battle.demo('meadow') gave field 88.27 s -> battle within 0.7 s ->
      victory fanfare on the outcome -> dellhollow back at 89.1 s. Zero
      music-related console output.
      SUITES GREEN: slice 532/0, cine 666/0 + 1 soft warning, economy 204/0,
      encounter_sim 38/38. The cine soft warning is NOT mine — it is
      "shot art NEWER than the live master (17:48:18), 17 stale", the
      tranche-2 custodian's in-flight master edit, and it predates this work.
      PLAY3D UNTOUCHED. Coordinator owes ONE line in the script-hook block:
      `<script src="js/music.js"></script>` (last, after menu.js). Nothing
      else to wire — music.js reads ?scene= itself and finds window.Battle on
      its own. Menu volume/mute is a later coordinator-mediated step:
      Music.setVolume()/mute() already persist to localStorage
      'emberbrook-music' the way the menu would want, and menu.js was not
      touched.
22:0x COORDINATOR: MUSIC IS IN THE GAME (hook a53b428; agent commits 5429a68..
      e8fcd9b). LYRIA WORKED via the existing Gemini key — 7 ORIGINAL tracks,
      no licenses, nothing to attribute. System: measured loop points (spectral
      similarity, per-track crossfade baked into samples), 0.00s drift
      continuity across page-load transitions, battle duck -> fanfare ON the
      victory panel -> field resumes at position, pre-decoded battle cues,
      autoplay-unlock, ?nomusic=1 escape hatch, 31/31 harness + suites green.
      Four tracks sent to the user's phone for the only judgment that matters.
      Cine's 1 soft warning = tranche-2 master edits (known mid-tranche state,
      resolves at the final bake). Re-roll path: tools/genmusic.mjs --force
      <id> + music_loops.mjs.
22:1x BATTLE-ARENA v3: THE BATTLE IS A 3D ARENA NOW (633b51f, 8d893bd, add5b38,
      37512a6). USER RULING: the v2 screen — combatants "lining up in a single
      row" of flat sprites — "feels more like a mobile game than a proper
      impressive desktop game". Shipped: a real THREE.Scene per battle, FF
      staggered formations with depth, 3D bodies for everyone who has a model,
      and a camera-facing BILLBOARD in the same scene for everyone who does not
      (the ruled 2D-in-3D path, and how every future character walks on before
      their model exists).
      ARCHITECTURE — OWN RENDERER, not a second pass in play3d's, and the
      reasons in order of weight: (1) play3d.html is read-only custody and
      exposes NO render hook, so sharing would mean editing a file this agent
      may not touch; (2) the battle is exclusive — UILOCK has already frozen
      phys() and the world renderer is drawing a frozen frame nobody can see
      behind a full-bleed overlay, so no frame budget is being wasted, only
      reclaimed; (3) destroy() can then drop the entire context, which a shared
      scene with a shared material cache makes genuinely hard to guarantee.
      Cost: one extra WebGL context for the life of a battle. battle_stage3d.js
      is likewise NOT in play3d's script list — battle_turnbased fetches it from
      its own sibling URL during the 350 ms entry fade, so a page with no THREE
      never issues the request. PLAY3D AND battle_rules.js UNTOUCHED.
      THE SEAM, which is the whole of the ruling's "backdrop generated WITH
      AWARENESS of the 3D arena model": all four plates re-shot to a prompt
      written in the arena camera's own numbers (eye 3.9 m, tilt 14 deg, 34 deg
      vfov, horizon at 42%, BOTTOM 30% DELIBERATELY EMPTY because that band is
      what the real floor eats). The plate maps onto a band curved around the
      CAMERA AXIS rather than the world origin — symmetric visible arc, natural
      aspect, ~1.3x upscale where it shows instead of the 2x horizontal stretch
      a world-centred cylinder forces — and ONE painted row (ZONES[zone].horizon)
      is pinned to the world height where the ground's far silhouette projects.
      Scene fog dissolves that silhouette into the plate's own haze colour and a
      mist ribbon does the same from the plate side. Re-shooting a plate is two
      steps and the manifest says which: generate, then re-measure `horizon`.
      SIX CC0 MONSTER MODELS LANDED, all Quaternius, all CC0 1.0 Universal,
      verified on the pack page AND (4 of 6) against a License.txt inside the
      author's own download, both quoted verbatim in
      assets/monsters/3d/MANIFEST.md. 3.22 MiB. Nine CC-BY near-misses rejected
      and listed by author so nobody re-walks that path.
      FALLBACK CHAIN, VERIFIED BY KILLING EACH TIER (BattleStage3D.disable + the
      mock's ?kill=), not asserted:
        party  rogue.glb model -> EBUI pose-plate billboard -> mannequin proxy
        foe    monsters/3d GLB -> plate billboard -> pixel-sprite billboard
               -> proxy solid (family-palette, the 3D translation of the CSS
               silhouette; a DOM CSS shape inside a 3D scene reads as a bug)
        stage  the 3D arena -> the whole v2 DOM stage, unchanged
      All four photographed. The party-billboard tier — Vesper and Maren as
      their chroma-keyed plates standing on the arena floor with blob shadows —
      is arguably the best-looking of the lot.
      FOUR REAL BUGS, one expensive: (a) THE GROUND'S TRIANGLE WINDING WAS
      INVERTED, so the entire floor was back-face culled and the "ground" being
      tuned for an hour was the plate's empty lower band — found by planting a
      magenta/blue vertex checker and watching the frame not change by one byte;
      (b) palette hexes were being taken as LINEAR by r128 (no colour management)
      and gamma-brightened, turning a dark forest brown into a pale tan — every
      hex now goes through an sRGB->linear helper; (c) fog near/far are measured
      FROM THE CAMERA, which stands 11.6 m out, so fogNear 15 was hazing the
      fighters themselves; (d) .ebb-field going position:absolute in arena mode
      takes it out of the root's column flow, which floated the command/party
      band up under the HUD until .ebb-bottom got margin-top:auto.
      THREE THINGS THE SOURCED PACKS FORCED: KHR_materials_unlit (three hands
      those meshes MeshBasicMaterial, which ignores the arena's key light AND its
      fog — a creature then floats on the plate like a sticker, so every basic
      material on a loaded creature is re-homed onto Lambert); reed-nibbler faces
      +X where the other five face +Z; and clip names differ per pack, so clips
      are matched on INTENT (idle/attack/hit/die/item/cheer) with an exact list
      first and a regex behind it. bramble-shade and weir-eel ship no Death clip
      and fall to the tip-over tween.
      HIDDEN-TAB CORRECTNESS: tweens carry absolute timestamps and one-shot clips
      return to idle on a TIMER, not on the mixer's 'finished' event — rAF stops
      dead in a background tab, so a delta-driven tween would freeze mid-lunge
      and an event-driven clip would never come back. A resumed tab finds every
      tween finished and snaps to the settled pose, which is the only correct
      answer.
      HEADLESS SAFETY: available() probes for document + THREE + a real GL
      context and is the only gate; the stage is constructed BEFORE a single body
      element exists, so a create() that returns null leaves nothing half-built.
      battle_sim/encounter_sim never load battle_turnbased at all.
      SUITES GREEN: economy 204/0, encounter_sim 38/38, battle_sim ALL ENVELOPES
      GREEN + 6 engine property tests, slice 532/0, cine 666/0 + 1 soft warning
      (the tranche-2 stale-shot-art warning, not mine, predates this work).
      MOCK: tools/ui_mock.html grew ?stage=3d|dom, ?kill=, ?zone=, ?party=1|2
      and waits for THE ART (every body off the proxy tier, then the 1.05 s intro
      sweep) rather than for a clock. It loads THREE exactly as play3d does, so
      nothing about the arena is stubbed. Shots via headless Chrome +
      swiftshader; note Chrome frequently writes the PNG and then never exits, so
      the harness waits on the FILE.
      HOLDING FOR REVIEW before final polish, per the mock-first instruction.
19:3x TRANCHE-2 CUSTODIAN: CLIFF COMPLETE (C1+C2+C3). LEAK GATE 0.00% ON ALL 17.
      GO received on the tier-A look, all three deviations ratified. Built the
      remaining tiers, retired the placeholder, closed the east void, ran the
      three resolution repairs.
      C1 the south wall — 6 patches + a back panel, 5,960 verts / 5,572 polys
      over the placeholder's exact footprint (x -35..135, z -9..37), in
      mat_rock_townwall. px/edge: tier a 80@33m..45@59m, b 75..42, c 68..43,
      d 56..43 — the 60-80 band gate_cliffface (43) and shelf_cliffface (45-76)
      hold. cliff_town RETIRED.
      C2 the east closure — cliff_east_closure at x=140 (+relief), y -13..54,
      z -16..26, 640 verts, mat_rock_farwall (CORRECT at 60-100 m, which is what
      it was authored for). Plus fx_haze_east, fx_haze_south and
      fx_ridge_upstream_skirt. All new objects; nothing existing edited.
      C3 resolution — qm_stair_underworks 192->1,344 verts (1.63 -> 0.54 m
      edges), gate_ground's west lobe 4,774->14,271 (0.93 -> 0.52 m), and a
      60 mm two-segment chamfer on the nine weave huts' VERTICAL WALL edges
      only (roofs untouched: they carry the house-variety shingle Col). +13,193
      verts. Revert is a restore from t2_cliff_res_backup.json, written once
      before anything was touched, because subdivide and bevel are not
      invertible.
      THREE MORE FINDINGS, all of them render-only and all of them now written
      into the plan's AS BUILT section:
      (a) A HEIGHTFIELD SHEET IS NOT A BOX. The first full build leaked 6-32
      rays on seven cameras that had leaked ZERO before. Traced every ray: each
      one crosses the wall surface within 4 CM OF TANGENCY — it grazes a crest,
      passes behind the surface, and since the sheet's depth is bounded at 8.5 m
      it can never be caught again and escapes out of the open back. Closed the
      sheet into a shell (top AND bottom cap strips per band, side strips at the
      two ends, one 4-vertex back panel at y=-9.6). Every camera went to 0.00%.
      (b) THE HAZE CARDS MUST NOT CAST SHADOW. Every haze card the town already
      carries has visible_shadow=False. Mine did not, and a thin slab lying
      along the wall is very nearly PARALLEL to SUN_key's rake (-0.55, 0.73,
      -0.41), so the light's path inside it ran tens of metres instead of three:
      the slab stopped being atmosphere and became an opaque curtain. The gate
      frame's entire south wall rendered BLACK. One flag fixed it.
      (c) VOLUME CARDS ARE MESHES TO A RAY-CASTER. fx_haze_south lies against
      the wall, so on the next build the clearance ray-cast hit its back face
      and clamped 3,746 vertices forward by up to 2.4 m, dragging the whole face
      out of the cliff. The build now hides volume-only cards from the
      depsgraph, the same rule t2_probe_leak.py uses.
      GATES, all green: SKY-LEAK 0.00% on all 17 (was lockfive 19.96%,
      cottage-steps 16.26%, shelf-east 0.08%; boatyard's 0.36% is the
      legitimate sky above the rim, 100% upward rays, unchanged);
      master_walk_qa 367/367 bit-identical; geometry_audit x 30..140 y -12..6
      zero intersections (one pre-existing stray, veg_shelf_tuft_26 at
      (46.2, 1.3) — 1.3 m in front of anything this pass built, so not ours);
      master_glb_survival on cliff_town_/cliff_east_ CLEAN, 0 white prims,
      mat_rock_townwall arrives textured; look_golden 0 values changed, 7
      already golden. Probes: docs/qa/districts/t2cliff_{lockhead,gate,
      cottage-steps,quay-west,lockfive}.png. Revert paths: t2_cliff_south.py
      `-- revert save` re-creates the placeholder cube exactly; t2_cliff_east.py
      `-- revert save` deletes its four objects; t2_cliff_res.py `-- revert
      save` restores from the backup JSON.
      NEXT: colour placement re-probe against the post-cliff frames, then the
      placement table. NO RE-BAKE from me — coordinator's, at the end.
22:4x COORDINATOR: ARENA v3 PAST THE MOCK GATE (633b51f..ced96ca) — real 3D
      stage: staggered formations, 13/14-deg FF camera + intro sweep, SIX CC0
      Quaternius monsters (license-quoted), plates REGENERATED to the arena
      camera's own numbers (bottom 30% empty — the old full-scene plates were
      a wall of grass behind a real floor), four fallback tiers each KILLED
      AND PHOTOGRAPHED. Four real bugs fixed incl. inverted ground winding
      (caught via vertex-color checker + byte-identical frame). Shots to user
      w/ THE presentation fork: full-3D rogue party vs painterly pose-billboard
      party in the 3D arena (my rec: billboards — HD-2D, matches the art).
      Polish priorities issued; not blocked on the ruling. Cliff tiers B/C/D
      still building.
22:3x BATTLE-ARENA v3 POLISH ROUND (6db8fba, f292857, + this). Coordinator's
      order (a)(b)(c)(1) worked; (c) is the one I did not do and why is below.
      (1) PARTY-LOOK FORK IS NOW ONE STRING, so the pending user ruling cannot
      block anything: `BattleStage3D.art.partyBody = 'model' | 'billboard'`.
      Both tiers ship; whichever loses is the other's FALLBACK, so nothing is
      thrown away and no code moves when the ruling lands. Default 'model'
      today. The party build was restructured into two named thunks (asModel,
      asBillboard) and the order between them is the switch — there is no second
      code path to keep in sync.
      (a) CRAG AND WATER GROUNDS UP TO STANDARD. Two findings behind the
      flatness, both now data: `dirt` (the trodden centre) is NOT always lighter
      than the field — a meadow wears to pale earth, a river shore wears to DARK
      WET silt, and crag/water had it backwards; and a stony floor needs far
      more fine-noise mottle than grass does, so `grain` is per zone (crag 1.0,
      water 0.85, forest 0.7, meadow 0.5) instead of one constant.
      (b) THE WISP IS BUILT, NOT BOUGHT. Tinting the CC0 ghost made a blue blob
      with eyes — a cute monster, not a spirit. brook-sprite now routes through
      a new BUILT table (`MON[id].build`): an emissive core inside two additive
      back-side shells with three orbiting motes. Reads as LIGHT. The ghost GLB
      stays on disk as the documented fallback; deleting one `build:` line puts
      it back in play. World canon respected — Heartlights are the rare magical
      ones, so a wild brook sprite glows cool and dim, not warm.
      (c) NOT DONE, DELIBERATELY: the wolf-vs-cute style seam. The 3d manifest
      records style-matched alternates where they exist and does NOT record one
      for the wolf, so this is a fresh CC0 hunt plus licence verification, not a
      swap. Not "quick" as the ruling required. Flagged in the board README.
      THREE MORE BUGS, all found while polishing:
      - THE BACKDROP WAS BUILT FROM THE LIVE CAMERA. The band is rebuilt when
        the plate decodes (~200-800 ms) — squarely inside the 1.05 s intro sweep
        — so the painted horizon was pinned to a camera pose that ceased to
        exist a beat later, and WHICH pose you got depended on how fast the PNG
        came off disk. Rest pose is captured once now.
      - groundY() carried a STALE COPY of the surface formula after the mesh's
        octaves were retuned: combatants, props and blob shadows were seated up
        to ~9 cm off the surface being drawn. One closed form, used by both.
      - MeshLambertMaterial SILENTLY DROPS flatShading in r128 (it shades per
        vertex) — one console warning per material and every low-poly rock came
        out smooth, which is the one thing a low-poly rock must not be. Props
        and proxies are MeshPhongMaterial{shininess:0, flatShading:true} now:
        Lambert's look, per fragment, faceted.
      Also: preserveDrawingBuffer is now CFG.snapshots (default on) with the
      trade written down — it is what makes stage.snapshot() and every headless
      screenshot possible, at the cost of a readback per frame.
      SUITES STILL GREEN: economy 204/0, encounter_sim 38/38, battle_sim ALL
      ENVELOPES GREEN, slice 532/0, cine 666/0 + the 1 known tranche-2 soft
      warning. play3d.html and battle_rules.js untouched throughout.
      SHARED-INDEX NOTE for whoever runs the next agent: the tranche-2 custodian
      stages blend artifacts concurrently, and the coordinator's own commit swept
      my staged review-board files into it. `git commit -- <paths>` protects the
      commit but NOT the staging area — stage and commit in one breath.
20:1x TRANCHE-2 CUSTODIAN: COLOUR LANDED (45 objects), WATER GEOMETRY LANDED
      (W1+W2). Taste gates going to main; not blocked on them.
      RE-PROBE FIRST, as the plan demands: re-ran t2_probe_place.py against the
      post-cliff master and the 47-row budget REPRODUCES to within a tenth of a
      point (gate 7.67%, lockhead 9.02%, crossing 10.59%, north-landing 7.95%).
      So replacing 3-23% of ten frames did NOT move the colour budget — the
      cliff was grey rock and it is now brown rock; neither is an accent pixel.
      Worth recording because the plan's ordering rule was written on the
      assumption it might.
      COLOUR: tools/t2_color_pops.py. P1 free wins — nine awnings repainted from
      neutral grey (0.60,0.58,0.54) to the six-accent set by sha1 with a
      two-neighbour separation pass, 108 loops; lf_bunting_0..3's rope loops,
      240 of 810 each, repainted to the pennant set. P2-P4 — 45 objects, 1,727
      verts, in SIXTEEN MATERIALS THAT ALREADY SHIPPED. Zero new materials, so
      the glTF gate is true by construction: 0 white prims, 7 own materials
      clean. MEASURED RESULT (t2_probe_chroma): gate 0.61 -> 6.53, lockhead
      1.40 -> 5.96, waterfront 0.59 -> 7.89, fishdock 0.16 -> 6.88, boatyard
      2.27 -> 7.24, deep-stairs 2.84 -> 7.96, lockfive 0.00 -> 5.23,
      north-landing 0.03 -> 4.56, cottage-steps 0.00 -> 4.38, crossing 0.11 ->
      2.68, cottage 0.17 -> 2.40. Twelve of seventeen land in the 5-11% band;
      four sit under the plan's 5% floor and one (shelf-east 12.69%) was already
      over before this pass and was left alone by design.
      FIVE ROWS NOT BUILT, all for measured reasons: B2_yard_paintpots projects
      under 0.05% in all 17 post-cliff; N4_nl_barge_hull has no clear mounting
      face; and W3_hut_doors / W4_hut_shutters / W6_keeper_door are a MECHANISM
      correction — the plan files them under P2, "material-slot and Col edits on
      EXISTING meshes, not new geometry", and built as free-standing plates they
      cannot be mounted at all: the lf_ kit's nine huts OVERLAP EACH OTHER IN X
      while standing at different y, so one 10 m band crosses three huts whose
      north faces are up to 0.9 m apart. Repainting the huts' own wall Col is
      the right mechanism and is its own safe pass. That is most of the shortfall
      at crossing and cottage.
      FOUR GATE-DRIVEN FIXES worth keeping: (1) a tarp probed at head height over
      the boatyard deck obstructed 3.90% of a walk surface and FAILED walk QA —
      lifted 2.4 m. (2) Painted panels must be snapped to their host from
      OUTSIDE: casting outward from the probed centre finds an INTERIOR wall,
      because the probe rectangles are region centres, and mounts the plate
      inside the building. (3) A rebuild must hide its own previous output from
      the ray-caster or the laundry posts silently stop being built (the old
      line is 3 cm below and reads as ground) and the strays come back. (4) Free
      cloth needs posts and free props need seating, or geometry_audit calls
      them strays — correctly.
      THE PLAN'S BUNTING LIFT WAS MEASURED AWAY. It reads "lf_bunting hangs at
      z 0.16-1.64, down at the waterline where nothing sees it". The ground under
      lf_bunting_0 is at z = 0.78, so the object already straddles its own deck:
      that z range is its POSTS reaching the ground, not a line lying in the
      river. Translating it lifts the posts off the ground and geometry_audit
      reported it floating 5.68 m up. BUNTING_LIFT is 0.00 and the recolour
      stands alone; re-stringing properly is per-vertex surgery for its own pass.
      WATER W1+W2 (geometry BEFORE shader, which is the plan's central ruling):
      tools/t2_water_bed.py. W1 pushed three sheet landward edges under the bank
      (mid 26.0->22.8, downstream 26.0->23.6, upstream 30.35->29.6 — 29.6 and
      not the 28.2 first tried, because at 28.2 the sheet reaches OVER a boatyard
      walk surface and walk QA fails headroom). W2 built four shelves, 745 verts,
      at the only 49 m of camera-visible gentle bank. TWO THINGS THE PLAN COULD
      NOT KNOW: the three shelf rectangles are NOT EMPTY — the slipway ramp, the
      Lock Five wall, the moorings and two landing stages stand inside them, and
      the first build drove the shelf through all of them (slipway_ramp 93% of
      its vertices inside), so every shelf vertex is now CARVED under the topmost
      existing surface with a 0.45 m margin (157/70/112/93 verts carved); and the
      boatyard shelf is SPLIT AROUND THE SLIPWAY, because the slipway is a walk
      corridor running down INTO the river and any grid coarse enough to be cheap
      steps over its narrow deck somewhere — walk QA is zero-tolerance and said
      so at both 1.5 m and 1.0 m spacing.
      GATES: master_walk_qa 367/367 PASSED after both passes; geometry_audit
      clean on the colour regions (1 pre-existing offender, lf_stair_treads /
      lg_ks_treads, neither ours); master_glb_survival 0 white; look_golden
      unmoved. NOT DONE: water W3/W4 (the depth-attribute bake and the alpha
      shader) — the geometry they depend on is now in place and the plan's
      per-sheet-ramp trap is documented. Probes:
      docs/qa/districts/t2color_{gate,lockhead,cottage-steps,north-landing}.png.
