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
