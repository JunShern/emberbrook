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
20:5x TRANCHE-2 CUSTODIAN: GATE-2 VERDICTS ACTED ON — banner drape, hut-wall
      paint, and the water shader (W3-W5). Gate 3 renders out.
      (a) BANNER KNOB. GB3 madder (V 0.46) -> ochre (V 0.62), the brightest hue
      in the storybook set and still inside rule 2's value band; and the banner
      generator now builds CLOTH rather than a board — a 6x4 draped sheet with a
      belly deepest at mid-height, a hem that sags between the corners, and a
      lateral sway that grows toward the free bottom edge. The old version was
      five flat strips with a belly in the normal only, which is why it read as
      a plank bolted to the rock.
      (b) HUT WALLS REPAINTED — the P2 mechanism, ratified. tools/t2_hut_paint.py:
      nine huts, 11,544 wall loops across the lf_deck and lf_stone slots, each
      moved 62% toward its accent's HUE with its own LUMINANCE HELD EXACTLY
      (renormalised after the blend, not approximately) — the roof pass's rule.
      Assignment sha1(name) with a neighbour pass at 9 m: ZERO same-accent pairs
      inside the radius, where the shipped state had two (pilot-cluster_1 and
      weave-huts_0 both sage; weave-huts_2 and weave-north_0 both pale blue).
      Roofs and glass untouched — lf_shingle* carries the house-variety Col.
      MEASUREMENT FINDING, recorded and NOT acted on: lf_deck and lf_stone are
      KIT materials and are not in the chroma probe's accent set, so the huts'
      painted walls DO NOT REGISTER as chromatic pixels however bright they get.
      The eastern cameras' near-zero scores are therefore part real and part
      definitional. The definition is deliberately left alone — all three
      tranche-2 plans are written against it and moving it mid-tranche would
      make every number incomparable.
      (c) WATER W3-W5. tools/t2_water_shader.py, run AFTER the bed. Sheets
      subdivided ADAPTIVELY (only edges over 1.5 m, one cut per pass: taking the
      cut count from the longest edge and applying it to every edge also cut the
      0.4 m THICKNESS 46 times and produced 26,512 verts for water_pool-mid
      against a plan budget of ~2,000 for all four). Depth ray-cast per vertex
      with all water hidden; Col.rgb = WHITE, Col.a = ramp(depth). PER-SHEET
      RAMPS, the trap the plan names: upstream median 7.50 m -> x0.53,
      downstream 3.50 -> x1.14, mid 4.10 -> x0.98, lock 0.70 -> x5.71. Alpha
      lands at 0.06..0.97 on the mid pool, 0.34..0.97 upstream. ONLY THE UP-FACING
      faces carry the fade; every other face is 0.02, because the sheets are
      CLOSED 0.4 m BOXES and a ray through a translucent top and an equally
      translucent bottom reads 1-(1-a)^2, i.e. 0.84 where 0.60 was authored.
      W5 MEASURED, AND THE MEASUREMENT KILLED TIER 2: COLOR_0 does export as
      VEC4 under alphaMode BLEND, but reading the accessor's actual bytes its
      ALPHA IS A FLAT 1.0..1.0 — the exporter's own warning says it skips a
      vertex colour that does not feed Base Color, and finding 221 forbids
      feeding Base Color from it. A 4-component COLOR_0 proves nothing; the plan
      was right to say measure it.
      AND A CONFLICT THE PLAN COULD NOT HAVE SEEN: TIER 1 AND THE BAKED FADE ARE
      MUTUALLY EXCLUSIVE. Cycles reads the per-vertex fade only if Alpha is
      LINKED; the exporter writes baseColorFactor[3] only if Alpha is UNLINKED.
      One socket cannot do both. THE BAKE WINS — the seventeen del-cine plates
      ARE the art the player looks at and the runtime GLB is collision under
      them, so the link stays, the render gets the full fade, and the runtime
      water ships exactly as opaque as it is today (no regression). A
      `-- runtime-tier1` flag trades the gradient for a translucent runtime
      river if that is ever wanted.
      GATES: master_walk_qa 367/367 PASSED after all three; master_glb_albedo
      m_water still reports (0.04, 0.105, 0.12) — the flat-lobe rule held, which
      is the water plan's gate 3. Probe:
      docs/qa/districts/t2water_waterfront.png shows the bank continuing under
      the surface and fading with depth, which is the note this tranche started
      from.
22:4x BATTLE-ARENA v3: THE FOE LINE, BLOCKED PROPERLY (8a5ec1f, 209e7d0,
      7295e08). Three rules, each added because a SCREENSHOT showed the previous
      set was not enough — this is the part of the arena that screenshots taught
      and arithmetic would not have.
      1. DEPTH IS THE SEPARATION. The camera's yaw makes a slot's screen-space x
         about 0.97x - 0.24z, so pushing a body along +z drags it LEFT almost as
         fast as +x drags it right; the two nearly cancel and no realistic
         sideways offset pulls two combatants apart horizontally. Distance does,
         read as size and as height in frame. Hence 3.2 m between foe slots.
      2. AN ALTERNATING SIDEWAYS JOG, because depth alone left two identical reed
         nibblers in the same screen COLUMN, one behind the other. And at n=2 the
         chevron contributes NOTHING (|i-mid| is 0.5 for both slots, so it moves
         them identically) — the jog is working alone there and is boosted, which
         the two-monster case can afford and which matters because two monsters
         is the commonest encounter shape in encounters.json. Measured against
         the real projection: the n=2 gap went 0.74 m -> 1.80 m of screen-space
         x, both foes still inside 50% of the half-frame.
      3. STAGE BY HEIGHT. No amount of geometry stops a 1.95 m bramble-shade from
         covering a wolf 1.2 m away in screen space — a body that wide always
         will. BLOCKING does: slots are handed out tallest-creature-to-deepest-
         slot, so the big silhouette stands behind the small ones. Group order is
         untouched everywhere it means anything (names, targeting, turn order);
         this only decides who stands where.
      All three are recorded in docs/qa/battle3d/README.md next to the shots that
      forced them, so the next person to touch the formation knows what each
      number is buying.
      BOARD RE-SHOT on the final code: four zones + four fallback tiers.
      SUITES GREEN THROUGHOUT: economy 204/0, encounter_sim 38/38, battle_sim ALL
      ENVELOPES GREEN, slice 532/0, cine 666/0 + the known tranche-2 soft warning.
      STILL HOLDING for the party-look ruling (art.partyBody, one string).
23:4x COORDINATOR: TRANCHE-2 GATES 2+3 PASSED. Color: town mean 3.07 -> 6.3%
      chroma, 12/17 in band, honest shortfalls traced to a DEFINITIONAL gap
      (hut kit materials don't count as chroma — metric left stable mid-
      tranche, logged as conservative). Cliff: sky-leak 0.00% ALL SEVENTEEN.
      Water: per-vertex depth fade with PER-SHEET ramps — banks continue
      under the surface and fade with depth, the user's exact ask. Two
      measured kills for the record: runtime tier-2 (COLOR_0 exports VEC4 but
      alpha bytes are flat 1.0 — exporter skips vertex color not feeding Base
      Color) and tier-1-vs-bake mutual exclusivity (Cycles needs Alpha linked,
      exporter needs it unlinked) — BAKE CHOSEN, plates are the art, runtime
      water stays opaque (no regression, flag `-- runtime-tier1` documented).
      Hut walls repainted (9 huts, 11,544 loops, zero same-accent neighbor
      pairs). Custodian committing final tallies; THE TRANCHE-2 BAKE is mine
      to trigger next. GIT TREE RULE (adopted after arena agent's catch):
      stage-and-commit in one breath with pathspec on the COMMIT.
21:0x TRANCHE-2 CUSTODIAN: CLOSE-OUT. FINAL TALLY, ALL THREE GATES PASSED,
      MASTER RELEASED TO THE COORDINATOR FOR THE BAKE.
      SKY-LEAK, 17/17: sixteen at 0.00%, boatyard at 0.36% which is the
      legitimate sky above the rim (100% upward rays, unchanged since the
      investigation). Was lockfive 19.96%, cottage-steps 16.26%, shelf-east
      0.08%.
      CHROMA, town mean 3.07% -> 6.53%: gate 0.61->6.54, lockhead 1.40->5.96,
      waterfront 0.59->7.89, deep-stairs 2.84->7.96, fishdock 0.16->6.88,
      boatyard 2.27->7.24, weave 2.32->6.07, quay-east 5.44->6.54, lockfive
      0.00->5.23, north-landing 0.03->4.56, cottage-steps 0.00->4.45, crossing
      0.11->2.68, cottage 0.17->2.40. Twelve of seventeen inside the 5-11% band.
      The four under 5% are UNDERSTATED BY THE METRIC ITSELF and that is now
      written into pops-of-color.md: lf_deck/lf_stone are kit materials outside
      the accent set, so the nine repainted hut walls contribute zero measured
      chroma however bright they are. Definition deliberately unchanged —
      widening it mid-tranche would make every number in all three plans
      incomparable.
      FOUR PLAN CORRECTIONS, all measured, all now in the plans' AS BUILT
      sections: (1) mat_rock_farwall is an atmospheric-perspective material, not
      a rock material, and is wrong at 33 m; (2) nothing in the rock kit is
      UV-mapped, so rock does not vary with height and the town's cliff look is
      an accident that was kept; (3) the plan's hut door/shutter rows cannot be
      geometry because the lf_ huts overlap in x at different y — the plan's own
      P2 text was right and its Part 3 rows were not; (4) the bunting "sunken at
      the waterline" premise was its POSTS reaching their own deck.
      PLUS TWO THE PLANS COULD NOT HAVE HAD: a heightfield sheet is not a box
      (grazing rays escape out of the open back — every leak ray crossed the
      surface within 4 cm of tangency); and TIER 1 AND THE BAKED FADE ARE
      MUTUALLY EXCLUSIVE — Cycles needs Alpha LINKED, the glTF exporter needs it
      UNLINKED, one socket. The bake wins; `-- runtime-tier1` records the trade.
      Tier 2 was killed by MEASUREMENT, not by inspection: COLOR_0 exports as
      VEC4 under alphaMode BLEND, which is the shape that would have justified
      declaring success, and its alpha bytes are a flat 1.0.
      ZERO GATE FAILURES SHIPPED. Four were hit and fixed on the way — a tarp at
      head height over a walk deck, a shelf over the slipway, a water sheet over
      a boatyard deck, and a stale renamed shelf orphaned by a revert that
      matched the table instead of the prefix. master_walk_qa 367/367
      bit-identical at every milestone; master_glb_survival 0 white;
      master_glb_albedo m_water (0.04, 0.105, 0.12); look_golden 0 changed.
      FOURTEEN TOOLS now carry this work, all with dry-run defaults and exact
      revert paths. NO RE-BAKE RUN — the backdrops are stale against the master
      by design and the bake is the coordinator's.
23:5x COORDINATOR: TRANCHE 2 CLOSED (final commit 8203f2b; seven commits,
      fourteen tools all dry-run-default with revert paths, both plans carry
      AS BUILT truth). Final tally: sky-leak 0.00% x16 + boatyard's legitimate
      0.36%; chroma mean 3.07 -> 6.53%; px/edge in band. Custodian released —
      "every plan correction came from a render or a gate refusing to pass,
      not from an opinion." THE TRANCHE-2 BAKE IS RUNNING (all 17, coordinator-
      owned watch this time — no silent-resume repeat). Handoff item on the
      future board: Object-coordinate rock mapping = the largest remaining
      look lever, one socket per material, user decision. Arena real-page
      playtest in flight. After bake: suites, commit, morning board.
22:5x ARENA PLAYTEST + FIVE USER RULINGS FROM LIVE PLAY (ab5cd5b, 970836d,
      998382c, 267eb01). Two pieces of work: proving the arena inside the real
      game, and then the user played it and told us five things.
      THE PLAYTEST (tools/arena_walk.js + tools/arena_playtest.mjs). The mock
      proved the STAGE; this proves the INTEGRATION, on play3d.html, headless,
      over CDP through the `ws` dep the server already has — no puppeteer, no new
      dependency. Four suites, all green: organic (director fires while walking ->
      fade -> arena -> outro -> world state -> teardown), music, nogl, serial.
      TWO MEASUREMENT TRAPS IT FELL INTO FIRST, both worth remembering because
      both FAILED THE PRODUCT FOR THE HARNESS'S MISTAKE: sampling UILOCK inside an
      await loop reads it AFTER the battle has finished unlocking (the freeze is
      now measured synchronously at the instant of firing, with SIM.move, which
      hands phys() a direction and renders nothing); and at speed 0 the fight
      resolves in microtasks, so any sampler keyed to loop indices samples a
      window it cannot predict (everything is on a timer that only reads while
      the battle is genuinely up).
      THE LEAK QUESTION, ASKED PROPERLY: there is no API for "how many WebGL
      contexts are alive", so "how many fresh ones can this page still hand out"
      IS the measurement — 12/12 before and after six battles. And heap is
      compared SECOND HALF vs FIRST, because total growth conflates one-time
      cache fill with a per-battle leak: on real hardware 140 MB once, then
      143/146/145/146/146/147, drift 1.9 MB.
      PERF, RECORDED SO NOBODY MISREADS IT: swiftshader renders the arena at
      ~0.4 fps and a real GPU at 20-27. A small frame count in a headless log is
      the harness. --gpu drops the software rasterizer.
      ONE PRE-EXISTING BUG FOUND: SIM.tick() throws in rt=1 mode, because it
      renders with `cam` and real-time mode never populates it (window._rtCam is
      loop()'s). Not fixed — play3d is coordinator custody. Flagged.
      THE FIVE RULINGS, all landed as separate commits so they reached the user
      while he was still playing:
      1. MIRROR: party LEFT, enemies RIGHT. Handedness is now ONE SIGN
         (CFG.partySide) and every x is a magnitude; camera yaw, both facings,
         lunge, knockback and the DOM stage's row order all derive from it.
         THE TRAP, caught by measuring: screen-x is ~ a*x + b*z and the sign of b
         is tied to the yaw's sign, so the mirror flipped whether the alternating
         jog and the depth spread ADD or CANCEL — turning n=3 gaps of 1.23/2.78 m
         into 1.81/0.26 m, two monsters back inside each other. Tying the jog to
         partySide reproduces every gap to the centimetre.
      2. PACING: an enemy turn was one 170 ms blur. It is now ANNOUNCED (message
         + a ring under the actor) -> beat -> the body moves -> the damage lands
         and is read -> settle. Battle.pacing, live-editable, * speed, so speed:0
         is still instant and no suite moved. say() writes the message AND owns
         its beat, which is the actual fix for "it moves too quickly": the old
         code overwrote the log on the next statement with a shorter separate wait.
      3. VICTORY TALLY: gold counts up, xp bars fill, a bar that tops out flashes
         LEVEL UP! and ticks the level over. The hard part is that xp is NOT
         applied at outro time — Battle reports, GS applies, and that separation
         is the contract that stops a battle module owning the economy. So the
         tally simulates the walk GS is about to take using GS.xpToNext and
         grantXp's own share arithmetic. Verified on the real page: 7/10 at L1,
         +6 xp, wrap, LEVEL UP, level reads 2, bar settles at 7.5% = exactly the
         3/40 GS then grants. First ENTER skips to final values, second leaves.
      4. LAYOUT: message line to the TOP, full width in one shared gutter. The
         bottom band loses max-width+auto-margins (which centred it and left the
         command window floating in from the edge on a wide screen) and is flush
         to both gutters; commands sit on the PARTY's side after the mirror.
      SUITES: economy 204/0 (after fixing a break that was NOT mine — the test
      hard-coded the xp curve's k=25 and the user's retune to 10 made a data
      change look like three engine regressions; it reads growth.json now),
      encounter_sim 38/38, battle_sim ALL ENVELOPES GREEN, arena playtest 4/4.
      SLICE AND CINE ARE RED AND IT IS NOT THE BATTLE: slice 531/1
      "scenegraph.json is STALE against the map files", cine 664/2 "the BAKED
      camera is the SOLVED camera" on gate/shelf-west/shelf-east/quay-west, with
      del-cine bg.png files modified in the tree. That is the tranche-2 bake in
      flight, it belongs to that custodian, and it wants
      tools/scenegraph_derive.mjs re-run plus a re-bake. Untouched by me.

21:10 THE CROSSING — INVESTIGATION (live user complaint: "walking path makes it
        seem weird when I'm crossing from the quay over to the lockkeeper's
        cottage. It's very easy to accidentally walk off the path and fall down.")
        THE STANDING HYPOTHESIS IS HALF WRONG, AND THE WRONG HALF IS THE WHOLE
        PROBLEM. docs/plans/lockhead-prep.md's remaining-gray statement says
        p-crossing's span is `bar_e_weave-huts__keepers-cottage_railA0..B2` +
        `walk_..._l0..l2`, "all already render-hidden" — i.e. the Keepers' Steps
        failure, correct collision with no art. Measured against the live master:
          * the three `walk_` faces ARE render-hidden — but the art is THERE.
            `wv_planking` sits 0.07..0.09 m under every one of them for the full
            20 m of the span. The bridge deck was built. No bridge is missing.
          * THE SIX `bar_` RAILS ARE `hide_render = False`. They are RENDERING.
            Six 8-vertex blockout boxes on `m_wood`, 0.57..1.20 m tall, standing
            on edge down both sides of the deck. Projected into the solved
            `crossing` camera (pure math, cine_bake's own camera model) they cover
            x 183..2105, y 781..966 of 2688x1536 — which is exactly the long pale
            untextured band across the middle of the SHIPPED backdrop
            (git show HEAD:public/assets/scenes/del-cine/cameras/crossing/bg.png).
            In `cottage` the same six cover 22% of the frame. The crossing looks
            weird because its handrails are grey blockout slabs.
          * `bar_e_weave-huts__moorage_l0..l2_railA/B` — six MORE visible blockouts
            two metres away, another ~16% of the `crossing` frame (the pale zigzag
            on the right of that plate), on a flight whose treads DO exist
            (wv_stair_treads/lf_stair_treads 0.05..0.09 m under every walk face
            but four). Same failure, same postcard.
        AND THE "EASY TO FALL OFF" HALF, measured by marching every walk face of
        the quay->cottage route at 0.35 m and probing for render-visible art
        within 2.4 m below:
          * the crossing ribbon is 1.30 m wide and the deck under it is barely
            wider — at 1.4 m off the centreline the first thing below is water or
            ground 5.9..9.2 m down, for the whole span. No visual margin anywhere.
          * the quay->weave descent is WORSE and was not in anyone's list:
            `walk_e_quay-deck__pilot-cluster` l2/l3 have half-widths of 0.17..0.33 m
            and 8.3..9.5 m of air under the centreline AND both edges.
          * THE FIX-ROUND CUSTODIAN'S SEVEN ARE NOT A RIBBON THAT FLIES. Their
            `edgeAt` sits 1.4..2.0 m OUTBOARD of the walker position `at` — the
            deck simply ends before the probe's offset ring, so a post there had
            nothing under it. That is a DECK problem exactly as they wrote. FIVE
            of the seven are on the user's route: (56.71,19.95) on
            quay-deck__pilot-cluster and (60.34,20.30) (63.45,22.98) (69.93,21.64)
            (71.04,25.96) on pilot-cluster__weave-huts. The other two,
            (47.64,21.92) and (55.42,20.28), are on the weave-north BRANCH, which
            this complaint's route never touches.
        Investigation was read-only throughout and ran alongside the 17-camera cine
        bake; nothing was written to the master until it finished.
01:1x COORDINATOR: THE TRANCHE-2 BAKE LANDED AND SHIPPED (9ed7591, 3017s):
      finished cliffs / color pops / painted huts / TRANSPARENT WATER now in
      all 17 plates. LIVE-PLAY NIGHT SHIFT with the user driving: WALKLOCK
      shipped (walk network is law in town scenes; jump = deliberate descent);
      deep-stairs<->waterfront progression LOOP killed (cutClearance 1.0->1.6,
      arrival margins re-slid; 14 millimetric identity reds until the batch
      re-bake); music continuity through shop doors (rule order + the
      force-cache stale-map bug); XP curve k=10; SEAM CANON chartered (user:
      "solve this systematically everywhere" — six invariants + seam_test.mjs
      gate, surgeon building); boatyard pin LIFTED by user (cliffside water-
      facing re-aim) + town-wide water-facing survey; crossing custodian
      building the visible bridge. STANDING POLICY: agent browser sessions
      run ?nomusic=1 (user could hear the tests).

------------------------------------------------------------
21:11 SEAM SURGEON: THE SEAM CANON, ITS GATE, AND THE SURGERY THAT PROVES IT.
      The user's three live reports (quay junction, bridge, boatyard roof) were
      all one defect class, and cine_test could not see any of them: coverage is
      a statement about the OWNERSHIP TABLE, and what a player feels is the
      sequence of camera changes produced by WALKING. So the deliverable became
      a method — measure the walk, not the table.
      tools/seam_test.mjs (new, town-agnostic, --cameras tests a PROPOSAL before
      anything is written to public/) replays play3d.html's own sgTick +
      sgCorrect — band test, arm/disarm, camera gating, the 20-tick positional
      correction — over every map edge in both directions at the runtime's real
      speed. On the SHIPPED town it fails 20 times. It reproduced the user's
      bridge complaint as something worse than reported: walking WESTWARD off
      the cottage, the camera strobes 30 cuts + 31 corrections and NEVER STOPS —
      a hard camera softlock in shipped data. It also found two defects nobody
      had reported: walking between two of the BOATYARD'S OWN landmarks
      (boatwright-shed__pitch-kettle) cut to waterfront and straight back, and
      the quay's west arm to the stair head did the same into the deep stairs.
      ROOT CAUSE, and it is one line of policy: cutGeometry scanned each seam's
      slide window END TO END and kept the FIRST acceptable spot. For a
      'from'-endpoint the window starts at the authored offset — so those seams
      landed right. For a 'to'-endpoint and for every authored @t split the scan
      STARTS AT THE FAR END, so they slid the whole window by default. That is
      why five Dellhollow cuts sat at exactly t=0.500: not because 0.500 was
      right but because it was as far from the landmark as ownership allowed.
      The player felt it as a camera changing halfway down a flight (the market
      flight cut at 3.7 m of 10.9, 3.2 m above the deck, TELEPORTING him 3.6 m
      down the stairs behind 700 ms of fade) and as two cuts mid-plank on a
      21.5 m bridge whose ends were the obvious places to cut. Fixed in
      cine_regions.mjs: order candidates by distance from the authored position,
      take the NEAREST acceptable one. The window still says how far a seam MAY
      slide; it no longer says sliding is free. THE BRIDGE STROBE DIES FROM THAT
      CHANGE ALONE (30+31 -> 2 cuts, 0 corrections, both at the abutments), and
      the Crossing postcard is KEPT, not retired.
      THE QUAY needed a second, structural fix: quay-east owned 2 walk meshes
      and 5.8 m of route and BOTH meshes sat inside quay-west's own pad — the
      map gives quay-deck extent 5.5 and market-stalls extent 3 with centres
      5.7 m apart, so the harbour deck and the market are ONE DECK with an
      invisible line across it, and walking west over that line fired
      quay-west>quay-east>quay-west FOUR CENTIMETRES APART. Retired: 17 -> 16
      cameras, quay-west absorbs the market for 2 px of character height
      (93..54 -> 88..52, gate 50). Measured against the two alternatives in the
      doc; band tuning alone was measured and recommended AGAINST.
      Also fixed: the waterfront boardwalk (the map models it as two edges lying
      on top of each other; the two seams now co-locate and fire once) and the
      deep-stairs head (its seam sat at dy=1.60 against a cutVTol of 1.6 — on
      the tolerance boundary exactly; deep-stairs' own framing improves 78..60
      -> 94..70 as a side effect of handing the head landing to the quay).
      BOATYARD pin lifted per the user. A literal cliff-side camera there is
      GEOMETRICALLY IMPOSSIBLE and the arithmetic is in the doc — the near wall
      falls 24 m over 28 m, so clearing it needs pitch > 40 degrees, a birds-eye
      shot; the yaw-270 candidate lands the camera inside rock. What works is
      cliff-side in the ALONG-GORGE sense: yaw 205 / pitch 28, camera upstream
      at map (-1, 17.3, 15.6) looking downstream and outward. The occluding shed
      goes from the MIDDLE of the sightline to the FARTHEST thing in frame.
      0% -> 60.8% water. Occlusion unverified by design (no ray-cast at design
      time) — confirm at bake.
      WATER SURVEY: eleven of seventeen shots had ZERO water in frame. The upper
      town all stands out over the gorge looking INTO the wall, which is the
      town's own documented default. Proposed three re-aims (boatyard,
      cottage-steps 7.8->66.8, crossing 0->60.7) for a mean of 10.1% -> 21.8%.
      CROSSING IS FLAGGED AS A USER TASTE CALL: yaw 225 turns "side-on to the
      span" into "along the span, leading the eye out over the water", which is
      what was asked for but is not the shot that was blessed — and keeping
      yaw 96 costs the patch NOTHING, the seam fixes are independent. Five more
      shots measured and NOT proposed with reasons; the shelf street and the
      quay stay inward-facing because every water-positive aim for them puts the
      camera behind the cliff rim, which is a wholesale restyle.
      PROPOSAL VERIFIES IN ONE COMMAND: the whole 16-camera file ships beside
      the doc, so `node tools/seam_test.mjs --cameras
      ../docs/plans/quay-junction-surgery.proposal.cameras.json` reproduces
      "294 ok, 0 failed" without touching public/. Nothing shipped was edited to
      design this and the running bake was never read from.
      HONEST EXCEPTION: winch-foot__slipway admits NO clean seam and the proof
      is arithmetic — hysteresis needs arc window [2.68, 8.43] and the
      boatwright shed pad blocks [2.68, 8.56]; empty intersection. Took the
      wrong-cut invariant as primary, accepted a short arrival, logged the real
      fix (move the shed pad in the MAP) as a follow-up. The gate reports it as
      a soft warning, not a pass.
      RE-BAKE: all 16, one batch — the coordinator's cutClearance re-solve had
      already drifted 14, the placer fix moves 11 of 20 seams and every moved
      seam re-frames the shots it touches. Delete the quay-east plate directory.
      HELD for the coordinator: cameras.json is theirs to apply.
22:6x RULING #6 — THE TURN QUEUE (e0d4aa0, b779290). The party status panel is
      now an ever-updating queue of whose turn comes next, MONSTERS INCLUDED.
      ITS ORDER IS NEVER COMPUTED BY THE WIDGET. Battle.queueFeed's default asks
      the kernel's rules.order(state) — the SAME function commit-then-resolve
      ranks its collected actions by — so what the panel shows IS what will
      happen, by construction rather than by two computations agreeing. Verified
      on a live battle: the kernel said Duskpad A, Duskpad B, Vesper, Bramble
      Shade, and the queue consumed in exactly that order, each actor greying to
      the tail, resetting cleanly on the next round.
      Decision phase = the round's projected order (you choose knowing who moves
      before you do). Resolution consumes from the top, current actor lit with an
      arrow and a rail; acted rows sink greyed to the tail rather than vanishing,
      so the shape of the round stays readable. A KO exits its row immediately and
      gets that for free — order() returns the living only.
      Party rows stay primary (bust, name, LV, HP gauge with numerals, reserved
      MP); foes are slimmer on the SAME grid so the columns line up, with their
      16px sprite as a pixelated thumbnail and the same name the field tag shows,
      so panel and field agree about which Duskpad is which. Thumbnail by
      convention, not a list.
      ROWS ARE BUILT ONCE AND REORDERED — appendChild MOVES a node, so gauges keep
      their transitions across a reorder and busts never flicker. Ordered once at
      construction too, or the panel shows BUILD order (party then foes) through
      the whole entry fade, which is the one moment the player is staring at it.
      FORWARD-COMPAT per the ruling: one narrow accessor. An ATB policy sets
      Battle.queueFeed to a gauge-fill predictor returning the same {id, acted}
      shape and the widget needs no edit — swapping the scheduler swaps the FEED.
      SILENCE POLICY ADOPTED (28117b9): every browser this repo's harness opens
      carries nomusic=1; the music suite skips loudly and --music opts back in
      while muting at the source. Successors inherit it via arena_playtest.mjs's
      header. Only qa_music.html may make noise.
      SUITES: economy 204/0, encounter_sim 38/38, battle_sim ALL ENVELOPES GREEN,
      arena playtest 4/4 (music skipped by policy; separately green muted).
      slice/cine remain the tranche-2 bake's known baked-vs-solved reds.

21:30 THE CROSSING BUILT (tools/cx_build.py, prefix cx_, collection DIST_crossing,
        lamp namespace KEYCX_, idempotent, `-- save` writes). Built on
        tools/district_lib.py — no fourth copy of the walk-face model.
        WHAT WAS WRONG: not a missing bridge. TWELVE `bar_` blockout boxes were
        RENDERING — six on the span and six more on the moorage flight two metres
        away — and they are the pale untextured slabs that dominate the `crossing`
        plate (~28% of that frame between them) and 22% of `cottage`. The deck was
        always there (wv_planking, 0.07..0.09 m under every walk face).
        BUILT: cx_rail (38 posts + 48 rail runs on the span's six blockout lines,
        15 posts + 2 runs on the moorage flight's six), cx_br_frame (stringers,
        transverse bearers and knee braces), cx_br_edges (kerbs + the one deck
        strip the span actually needed), cx_mr_slabs (3 moorage faces that had
        NOTHING under them), cx_bays (5 passing bays discharging the FIVE
        route-adjacent edges of the fix-round custodian's seven — deck first on
        cantilevered bearers, THEN the rail they could not stand up: 14 posts),
        cx_approach (two ABUTMENT PORTALS on the coordinator's own seam points
        [75.19,7.77,-22.64] and [88.58,7.55,-22.39] — post pair + lintel + braces,
        so the re-aimed crossing camera's threshold cut lands where the
        architecture says "you are on the bridge"; plus ONE ORDINARY LANTERN at
        (91.30, 23.24, 9.65) — never a Heartlight). All 12 blockouts are now
        render-hidden: bit-identical, still viewport-visible, collision untouched.
        THREE INSTRUMENTS WERE TRIED ON THE RAIL QUESTION AND ONLY THE THIRD IS
        RIGHT, which is the finding worth keeping. `free_box` (district_lib's
        corridor guard) forbids anything standing over a walk face — that is every
        handrail in the town, and it refused 19 of 38 posts. A "keep 0.075 m clear
        of every walk polygon" rule forbids every rail on a STAIR, because
        descending treads overlap in plan, so a post outboard of one tread is over
        the next: 23 of 24 refused on the moorage flight. What the gate ACTUALLY
        does is lay a 0.35 m grid on each walk top face from min+step/2, skip
        buried points, and fire one ray down from z+0.90 and one up from z+0.06.
        cx_build reproduces that grid (4048 points) and asks only "does this solid
        stand on one of THOSE points" — after which 38 of 38 span posts stood.
        A CORRIDOR GUARD AND A GATE ARE NOT THE SAME QUESTION. Recorded coupling:
        this encodes master_walk_qa's sampling contract; if that grid changes, re-run.
        NO SECOND DECK OVER THE SPAN, measured: a plank course hung 30 mm under the
        walk plane laps 55 mm into wv_planking for 20 m — inside_frac 0.212 by
        geometry_audit's own rule, and a duplicate floor 60 mm over the real one by
        eye. The Keepers' Steps had nothing under them; this span does.
        NOT BUILT, AND COUNTED: the moorage flight's deck widening (a strip laid on
        one tread's plane overhangs its neighbours and left 25 blocked samples that
        did not clean up; the flight is not this pass's assignment and its RAILS
        were what ruined the postcard). The other two of the seven, (47.64,21.92)
        f9.1 and (55.42,20.28) f8.0, are on the weave-north BRANCH which the
        complaint's route never touches. 24 founding stations found nothing and
        were left unbuilt rather than floated. All bucket-4.
        ALSO MEASURED AND NOT IN ANYONE'S LIST: the quay->weave descent
        `walk_e_quay-deck__pilot-cluster` l2/l3 has half-widths of 0.17..0.33 m with
        8.3..9.5 m of air under the centreline AND both edges. One passing bay lands
        on its landing.002; the rest of that flight is a district build.
        GATES: FULL 367 walk QA PASSED, topology bit-identical, 1308/1308 = 100.00%.
        Region 54,94,16,31 walk QA BIT-IDENTICAL to its pre-build baseline (2513
        samples, 2348 hits, 93.43%; the offenders there — t2c_WV2_dryingdeck_awning
        158, t2c_W5_flowerbox_rail 3, rung30 2, t2c_W7_keeper_boxes 1, wv_planking 1
        — are pre-existing and none are mine). geometry_audit 54,94,16,31: 333
        meshes, 1145 pairs, 2 offenders, 0 strays — one is the pre-existing
        lf_stair_treads/lg_ks_treads pair, the other is lf_stair_stringers IN
        cx_mr_slabs at frac 0.125 depth 0.04, which is 2 vertices of a 16-vertex
        stringer bedded in the landing it carries. glTF survival --prefix cx_:
        6 out / 6 in, 0 white. Deterministic: two clean re-runs, 2276 verts each.
        Revert path: the pass is idempotent and additive; deleting cx_*/KEYCX_ and
        clearing hide_render on the twelve bar_ blockouts restores the prior master,
        and a pre-build copy is in the shift scratchpad.
        RECORD SHOTS (EEVEE, from the SOLVED cameras via tools/ga_shot.py, rebuilt
        from the freshly regenerated cameras.solved.json after the seam surgery):
        docs/qa/districts/crossing_crossing.png and crossing_cottage.png.
        CAMERAS THE CHANGE IS VISIBLE IN, measured by projecting the new bounds
        through cine_bake's own camera model: crossing (cx_rail 63.6% of frame),
        cottage (21.6%), weave (14.0%), lockfive (22.0%), and lockhead (18.9%, via
        the weave passing bays only). lockhead was previously believed clear.
02:3x COORDINATOR: TOWN CERTIFIED PRE-BAKE (surgeon b98277c, 7099660). All
      traversal suites green; cine reds = CHAIN-only (16 camera moves + the
      quay-east dir), clears at the bake. Framing package 92f8930: frameExits
      ON town-wide, stair-visibility pitch fixes (the stair was IN FRAME and
      12%/26% VISIBLE — behind the rim lip by centimetres; canon §9.3 now
      names the four causes of "invisible" with four different fixes), lockhead
      + cottage re-aims, crossing yaw 195 probe-verified. NEW HAZARD CLASS
      TOOLED: re-aims expose never-framed objects — the salmon card appears in
      0/17 shipped plates (every old camera looked INTO the cliff);
      plate_flat.py screens all plates post-bake; custodian identifying the
      card in-blend before final save. Bake fires on loop-stairs completion;
      five-item post-bake checklist queued.

22:40 LOOP STAIRS — PARTLY DONE, AND THE PART THAT IS NOT DONE IS SAID PLAINLY.
        tools/ls_build.py (prefix ls_, DIST_loopstairs, idempotent, `-- save`),
        built on tools/district_lib.py — which gained `GateGrid` this shift so this
        is the FIRST pass that did not have to work the gate contract out for itself.
        WHAT IS WRONG, measured: the loop-stairs camera owns two edges and between
        them the walk network is a sensible double descent — 44 meshes, two flights
        leaving one yard at z 19.07 through two landings each, down to the quay deck
        and the market at 14.07. EVERY face is render-hidden and THERE ARE NO TREADS
        IN THE MASTER AT ALL. What renders is the stairs' UNDER-structure,
        qm_stair_underworks + shelf_stair_underworks, as a stack of chunky blocks,
        with art 1.94 / 1.56 / 1.53 m BELOW the tread in places, NOTHING under
        market-stalls_l0_t02, and — the "confusing" part — the scaffold 0.23 m and
        0.26 m ABOVE two treads, coming up THROUGH the stair. The user's words
        ("does not match the actual walkable surface overlay") are literally correct.
        BUILT: ls_treads (22 tread runs + 4 landings, each on its own face's plane
        30 mm under it, IN TIMBER — laid in mat_qm_stone the first record shot showed
        a stone stair dissolving into a stone block stack, which is the same
        confusion merely tidier), ls_rail (21 posts + 20 runs on the ten already-
        hidden blockout lines), ls_frame (stringers + 12 legs). CUT: 100 faces
        (99 + 1) that stood in or over the walk surface, SNAPSHOTTED first as
        LS_SRC_* with fake users, so the cut is idempotent and revertible by
        assigning the snapshot back. The 918 + 11 faces that sit more than 0.45 m
        BELOW the ribbons are the masonry the stairs genuinely stand on and were
        left alone; where that masonry comes within 0.5 m the flight gets NO frame
        at all, because building one drove timber through stone.
        HONEST STATUS — NOT AT THE USER'S BAR YET. The shot is materially better
        (a real flight with treads and rails where there was none, and nothing
        crossing the walk surface) but it is NOT yet "a clear single staircase":
        the remaining block mass still competes with the flights. That mass is the
        quay tier's own substructure, shared beyond this shot, and simplifying it is
        a bigger call than one custodian should take unilaterally — it is proposed,
        not done. RECOMMENDATION for the coordinator: replace the 918-face block
        stack inside x 50.5..61.5 y 6.5..14.5 with one stepped plinth following the
        two ribbons, as a scoped assignment with the quay tier's owner.
        GATES: FULL 367 walk QA PASSED bit-identical 1308/1308 = 100.00%. Region
        46,64,5,17 walk QA BIT-IDENTICAL to its pre-build baseline (1227 samples,
        1227 hits, 100.00%). glTF --prefix ls_: 3 out / 3 in, 0 white. Deterministic,
        998 verts on two runs. GEOMETRY AUDIT IS A REGRESSION AND IS NOT HIDDEN:
        region 46,64,5,17 went 0 offenders -> 3, all of them this pass's timber
        bedded in qm_stair_underworks (ls_frame frac 0.370 depth 0.15, ls_treads
        frac 0.117 depth 0.22, ls_frame IN ls_treads frac 0.115 depth 0.04), 0
        strays. Three rounds of adaptive thickness, per-face gap measurement and
        frame suppression took it from 3 deeper offenders to these three shallow
        ones; clearing them completely needs the plinth decision above. Revert:
        delete ls_* and assign the LS_SRC_* snapshots back.
        RECORD SHOT: docs/qa/districts/loopstairs_rebuilt.png (loop-stairs camera,
        from the freshly regenerated solved file).

22:55 THE SALMON CARD, IDENTIFIED AND FIXED — tools/fx_haze_east_fix.py.
        The seam surgeon's east-facing probe showed a literally constant card
        (RGB ~155,91,61, per-pixel std 0.41, hard vertical edges, ~4.3% of frame,
        ndc x -0.72..-0.33 y 0.52..1.00). Rayed from the solved crossing camera
        through that box: it is `fx_haze_east`, an 8-vertex slab x 124..130
        y -10..56 z -16..26 in CONTEXT.
        BOTH STANDING SUSPICIONS WERE WRONG, and that is worth recording. It is not
        dead-era backing, and its material is not broken: mat_haze_east is a proper
        Volume Scatter (0.48/0.50/0.60, density 0.0092) with no surface shader, built
        exactly like mat_haze_far/_mid/_rim/_south. Everything else in that box is
        sky (88.7% once the volume is marched through), water_pool-downstream, and
        three walls on mat_rock_farwall — and that material carries four image
        textures, a noise mix and a normal map, so it CANNOT produce a std of 0.41.
        A uniform-density volume box can: it adds a constant scattering term inside
        its own silhouette, which is exactly a hard-edged card with no variation.
        WHY NOBODY EVER SAW IT: the slab is 6 m thick and 66 m long. Every camera
        before tonight crossed the 6 m dimension — optical depth 0.055, invisible.
        Tonight's five re-aims are the first ever to look down its 66 m LENGTH.
        Measured on the current crossing camera it still adds +3/+7/+9 RGB in that
        box; at yaw 195 the path was far longer and it dominated.
        FIXED BY hide_render, not by deletion and not by a material change — sound
        geometry with a sound material that is the wrong SIZE for a sightline that
        did not exist when it was authored, and it contributes to zero of the 17
        shipped plates. Reversible: `-- save restore`. Full 367 walk QA re-run after
        the flag: PASSED, bit-identical. PROPOSED, NOT DONE: re-size the slab so its
        bounds leave frame, which belongs with whoever owns CONTEXT.
02:5x COORDINATOR: THE CAMERA-SURGERY BAKE IS FIRING (16 cameras, quay-east
      deleted). Pre-bake landings: crossing bridge REAL (rails on all 12
      blockout lines, abutment portals, passing bays — hypothesis refuted:
      the deck always existed, the pale band was RENDERING blockout rails);
      salmon card = fx_haze_east, a 6x66m haze volume seen down its LENGTH for
      the first time (optical depth 0.055 crosswise = invisible to every old
      camera; hidden, reversible; resize -> CONTEXT owner follow-up);
      loop-stairs HALF-SIMPLIFIED and shipped honestly (treads+rails now
      exist — there were NONE in the master; 918-face block mass remains,
      quay-tier plinth = scoped follow-up; geometry_audit 0->3 shallow
      accepted-with-note). Custodian released (transcript expired before my
      acceptance — rulings recorded here). GateGrid promoted to district_lib.
      NAV-EVAL LANE launched (user design): context-free vision judge draws
      waypoints on composited plates -> depth-unproject -> WALKLOCK walk ->
      score; VIEWER PAGE first-class (input/prompt/waypoints/GT/score per
      trial); calibration old-vs-new plates before trusting a number.
      Post-bake: checklist (plate_flat, shot_probe stair numbers, cine green),
      then the nav-eval scorecard against the fresh town.
04:1x COORDINATOR: SURGERY BAKE LANDED + COMMITTED — cine 637/0 (CHAIN
      cleared, town fully green structurally), slice 514/0. CHECKLIST CAUGHT
      THREE last-mile defects (the instruments beat eyes again): boatyard
      4.7% visibleFrac (designed-vs-as-built cliff collision — the surgeon's
      own named risk), stair prediction busted (14.6/20.7 vs 82/90 — new
      occluder to name), salmon card SHIPPED in crossing plate (hypothesis:
      cine_bake re-enables fx_* for beauty passes, overriding hide_render).
      Surgeon dispatched with the evidence packet; I execute blend edits +
      patch-bake affected cameras only. Vesper proportion lineup with the
      user (A semi-real / B soft-chibi / D figurine-render; ruling pending).

23:0x NAV-EVAL — THE THIRD PILLAR IS STANDING, AND ITS FIRST HONEST NUMBER.
      tools/nav_eval.mjs + docs/qa/naveval/viewer.html. A context-free vision
      judge (gemini-3.6-flash, PINNED not aliased) sees ONE composited image —
      the baked plate with Vesper at an entry spawn, keyed off the magenta pose
      art, scaled by charPx at her own view depth, and HALF-STRENGTH wherever
      the plate's depth is in front of her (play3d's ghost pass v2, so an
      occluded arrival is visible AS occluded). No map, no town name, no route
      data. It answers with waypoints in image coordinates; those unproject
      through the shot's own baked depth plate; the world points are walked
      under play3d's WALKLOCK rules against the SHIPPED scenegraph.json seams.
      Trial passes if the naive reading crosses an exit ONWARD — to a shot
      other than the one it arrived from. One run = one folder under
      docs/qa/naveval/run-<stamp>/ with every prompt verbatim, every raw reply,
      every unprojected point and every walk trace.
      THE HARNESS CHECKS ITSELF FIRST. `--judge oracle-world` feeds the town's
      own ground-truth route straight to the walker: 14/16. It found four real
      harness bugs before any API call was spent — the plate is 2688x1536 while
      the depth is 1344x768 (the character was being pasted at quarter scale in
      the wrong quadrant); a waypoint must be resolved against the WALK NETWORK
      along the ray, not against the depth surface, or every occluded pixel
      reads as a wall; Douglas-Peucker in plan deletes a staircase; and a walker
      that prefers the STRAIGHTEST walkable step takes the market flight every
      time, because walkGround keeps the highest surface exactly as play3d does
      — preferring the step that closes 3D distance picks the right flight
      without being told which one it is. THE TWO SHOTS THE ORACLE STILL MISSES
      ARE THE WALKER'S STEERING, NOT THE TOWN: a WALKLOCK flood fill from the
      Lock Five arrival reaches 12,744 cells and the far end of the town, so
      "the player is stuck on the moorage landing" was WRONG and is recorded as
      wrong.
      ROUTES.JSON WAS STALE and is regenerated (it predated the cutClearance
      re-solve AND the quay-east retirement; its exits sat where the old seams
      were, which is why the first oracle runs failed).
      CALIBRATION, REPORTED AS MEASURED. tranche-2 plates (9ed7591) vs tonight's
      surgery bake, same judge, same N: crossing 0.20 -> 1.00, and at N=10 on
      that shot alone 2/10 -> 10/10 — the rails-and-deck work is legible, and
      the separation is not sampling noise. gate 0.00 -> 0.00 and shelf-west
      0.00 -> 0.00 at BOTH N=5 and N=10 — AND THAT IS THE RIGHT ANSWER, which I
      only learned by re-probing instead of writing the flattering sentence.
      shot_probe against the surgery plates measures the arrival staircase at
      14.6% / 20.7% VISIBLE, against 12.2% / 25.6% before and against the 82% /
      90% the +2.4 m / +1.2 m re-aim PREDICTED (the bake commit 6d2dbb5 flags
      the same numbers as a last-mile catch). The fix did not reach the plate.
      So the two instruments agree: the stair is still hidden and the shot is
      still illegible. The perceptual metric did not miss a fix — there was no
      fix to see, and a metric that had lit up here would be the one to
      distrust. I had written "made it visible but not legible" and it was
      wrong; corrected in seam-canon §10.1.
      Town 0.325 -> 0.375; twelve of sixteen shots had no legibility work
      tonight and did not move, which is what a control group is supposed to do.
      FIRST SCORECARD (surgery bake, N=5): 0.375, six shots clear. Worst three
      and WHY, from the viewer: (1) cottage-steps 0/5 — all five readings walk
      the plank past the waterwheel and fire the cut BACKWARDS to the cottage;
      99.9% of the character is behind the plate at that entry. (2) shelf-east
      0/5 — five for five backwards to shelf-west, 45% of her occluded, and the
      judge names "the upper platform in the background" every time: the shot's
      visible flow points at the door the player just came through. (3) boatyard
      0/5 with progress 0.00 — the arrival stands 25.7 m BEHIND the rim pillar
      that fills the middle of the frame, so the player materialises as a ghost
      on a rock; every one of the five readings then traces the tiered ROOFS
      bottom-left as if they were the stairs ("descend along the layered wooden
      roof structure"), and four of six waypoints land on floor that is really
      there and really hidden. The user's July report was "the boatyard shot is
      almost completely occluded" — same shot, now with a number.
      AND A FINDING NOBODY WAS LOOKING FOR: compositing the character forced us
      to ask what the plate draws IN FRONT of her, and FOUR OF SIXTEEN ARRIVALS
      ARE BEHIND FOREGROUND GEOMETRY — boatyard 100% (plate 25.71 m nearer than
      her feet), lockfive 100%, cottage-steps 99.9% (4.35 m), loop-stairs 100%
      (4.57 m), with shelf-west 65%, crossing 48% and shelf-east 45% partly
      hidden. cine_test §B asserts every arrival is ON SCREEN and passes all
      sixteen. This is §9.2 again — IN FRAME IS NOT VISIBLE — at the one place
      it hurts most, the moment the player appears. Reported, not fixed: the fix
      is a camera or an occluder and belongs to whoever owns those shots.
      SEAM CANON §10 = THE PERCEPTUAL GATE. Threshold >= 0.6 proposed from the
      MEASURED distribution, not chosen: 32 shot scores across both bakes are
      0.00, 0.20 or 1.00 and nothing lands in (0.2, 1.0), so 0.6 is the midpoint
      of an empty band and cannot be tuned. It ships as a SCORECARD, not a red
      gate — Dellhollow is at 0.375 and arming it today would only mean turning
      it off. Two named sub-defects: "reads backwards" (wentBack = N; shelf-east,
      cottage, cottage-steps, lockfive all 5/5) and "off the network"
      (onWalkFrac; gate's 0.51 is the floor).
      VIEWER (user's explicit ask, built like we meant it): town grid sorted
      worst-first with per-shot score badge, sub-score bars and a five-tick
      agreement strip; click through to a stage showing the INPUT IMAGE with
      six independently switchable overlays — numbered judge waypoints coloured
      by what they landed on, all five readings ghosted together, the GT route,
      entries/exits, exit seam bands, and the walk actually taken with its stuck
      markers — beside the prompt verbatim, the raw reply, the sub-scores and
      the leg-by-leg walk outcome. Overlay geometry is precomputed in
      results.json in the same normalised coordinates the judge answered in, so
      the page renders and never re-implements the projection.
      GATES: seam_test 294/0, cine_test 637/0, slice_test 514/0, seam_walk 9/9,
      routes_derive --check clean. No shipped runtime file touched.

23:5x VISTA PATCH — THE SALMON CARD WAS NEVER ONE THING, AND THE OLD
      CERTIFICATE HAD EXPIRED. tools/t2_vista_west.py (new), EY1 extension in
      tools/t2_cliff_east.py, skip-budget fix in tools/t2_probe_leak.py.
      THE PREMISE THAT HAD TO BE RE-EXAMINED. t2_probe_leak certified thirteen
      of seventeen cameras at 0.00% sky-leak and that certificate is what let
      "the salmon card" be blamed on fx_haze_east (2080), on cine_bake
      re-enabling fx (6d2dbb5), and on a tint in the world background. It was
      TRUE WHEN WRITTEN and it was void by the time it was quoted: the cameras
      were re-solved with frameExits on, quay-east was retired, and
      boatyard/gate/shelf-west were re-aimed again in 0c0b522. A RE-AIMED
      CAMERA LOOKS WHERE NOTHING WAS EVER AUDITED. Re-run against the CURRENT
      solved file (cine_solve --check clean, 16 cameras), the town leaked on
      four: crossing 4.30% (1,234 rays), shelf-west 2.48% (710), gate 0.10%
      (29), north-landing 1 ray. 1,974 rays of naked world background, none of
      it haze, none of it a material, none of it fixable by tinting anything.
      THE BOATYARD'S 5.94% DIES WITH ITS CAMERA, AND THAT IS PROVEN, NOT HOPED.
      The boatyard plate's salmon belongs to the RETIRED aim. Re-probed at the
      as-baked camera it measures 5.98% — the reported number to within noise;
      re-probed at the current water-side yaw-90 aim, 0.00%. The patch-bake
      alone closes it. No geometry was built for the boatyard and none was
      needed; building it would have been building for a camera that no longer
      exists.
      FOUR DIAGNOSES, EACH A DIFFERENT SHAPE OF THE SAME MISTAKE — a wall that
      stops. crossing: ALL 1,234 rays cross x=140 at y 54.9..76.2, every one of
      them NORTH of cliff_east_closure's EY1=54 and none above or below it. The
      east closure is not mispositioned, it is 22 m short. Extended north to
      y=85.53 so it OVERLAPS cliff_far (y 80.9..99) instead of butting it — a
      butt joint is a T-junction and a T-junction on a closure is a pinhole to
      the background, i.e. the defect being repaired. The row pitch is preserved
      exactly (35 C2 rows + 16 appended at the same 1.9706 m) so lockfive's and
      cottage-steps' already-baked view of that wall is bit-identical and only
      new surface is added. shelf-west: its rays are NEARLY TANGENT to the south
      wall — they enter the strip in front of the face near x=-25, slide along
      it losing 0.32 m of y per metre of x, and pass the wall's west end at
      x=-35 STILL IN FRONT OF THE ROCK, where the end cap (which runs backward
      from the face, correctly) has nothing to catch them with. cliff_town_west2
      continues the wall to x=-82, shallowing from the full seven-octave depth()
      at the join to a 0.7 m skin at the far end so a tangential ray meets rock
      sooner; the join column is ASSERTED bit-identical against t2_cliff_south's
      own depth(), 40/40 rows. gate and boatyard: rays plunging at -40 deg go
      UNDER the wall's z=-9 toe. cliff_town_skirt, one box, the
      fx_ridge_upstream_skirt pattern. north-landing: one ray threading the
      saddle between the two upstream ridges; fx_ridge_far_west, 50x20 m, top at
      z=26 (eleven metres BELOW the town's own horizon) so it cannot intrude on
      the accepted boatyard west vista — and the post-build census confirms it
      appears in no other frame.
      THE INSTRUMENT WAS LYING, AND ONLY THE FIX EXPOSED IT. Two boatyard rays
      survived every closure built for them. Traced hit-by-hit: both pass
      through the pitch kettle's two smoke volumes and collect TWELVE see-
      through boundary crossings inside four metres of plume, exhausting
      first_opaque's budget of 12 before leaving the boatyard — the first opaque
      thing they meet, yard_ground twenty-five metres out, was never reached. A
      ray that runs out of budget was scored as a hole in the world. The budget
      is now 64 (worst real ray uses 18). This fails in the direction that
      INVENTS defects and can equally MASK them behind a nearer FX card, so
      every number above is the re-run one.
      RESULT: 1,974 -> 0 leak rays. All 16 cameras 0.00%, and 0.00% here means
      zero rays, not a rounded zero. New geometry 892 verts / 831 polys plus 368
      on the east closure. cliff_town_west2 measures 54 px/edge at 102 m in the
      one frame that sees it (brief allows 40-60; gate 6 is 250). VISIBILITY
      CENSUS, all 16: west2 in shelf-west only, skirt in gate 0.10% and
      shelf-west 0.04%, far_west in north-landing at 0.00% of frame, east
      closure 8.4->13.6% in crossing. Nothing else moved.
      GATES: master_walk_qa PASSED 367/367, worst vertex delta 0.000e+00,
      corridor coverage 100.00%. geometry_audit 19 offenders / 0 strays —
      IDENTICAL to the same audit run on HEAD's blend, so this pass adds none.
      master_glb_survival CLEAN, 12 cliff objects out / 12 in, 0 white
      (cliff_east_closure ships in the runtime GLB; town_export strips fx_ by
      name, so far_west does not). look_golden 0 changed / 7 golden — no light
      touched. Taste frames docs/qa/districts/vista_{shelf-west,crossing}.png.
      LEFT FOR THE COORDINATOR, DELIBERATELY: fx_haze_east stays hide_render, as
      the master had it, and t2_cliff_east.py now PRESERVES that flag across a
      rebuild (it did not before — a rebuild would have silently switched the
      retired card back on). The extended closure therefore reads dark and
      unhazed in crossing; whether it wants its haze back is a taste call to
      make with the patch-bake in hand, not a thing to slip in tonight.
      PATCH-BAKE SET (union with the queue): boatyard, gate, shelf-west,
      crossing, north-landing, lockfive, cottage-steps.

23:5x THE OCCLUDED ARRIVALS — NAMED, AND SIX OF SEVEN HAVE A METRE-SCALE FIX.
      Measured with a Blender re-derivation of nav_eval::composite's own ghost
      test (first opaque hit vs the standing point's view-z, 0.35 m tolerance)
      against the CURRENT cameras, so boatyard and shelf-west are judged on
      their new aims and not on the plates. It reproduces nav-eval to within
      0.02-0.13 on all seven, which is what makes the occluder names credible.
      THE BOATYARD'S OCCLUDER IS NOT THE RIM PILLAR. Against the new water-side
      yaw-90 frame it is hero_hull_clinker — the hauled hull on the ways, the
      shot's own hero prop — with the shed doors behind it, and the nearest
      surface is 4.75 m in front of her feet, not 25.71 m. The old number
      described the old camera. Re-deriving before judging was the instruction
      and it changed the answer.
      Occluder / fix per arrival, all six move-the-arrival proposals swept off
      the region's real walk surface (a 0.5 m lattice, filtered to the camera's
      owned hull and to never spending band clearance) and re-scored at full
      sample: boatyard hero_hull_clinker -> [23.92, 25.90, 2.27] 1.30 m, 100% ->
      0.0%; loop-stairs shelf_home_a (403/403, she is simply behind a house) ->
      [53.20, 9.48, 18.75] 2.57 m, 100% -> 0.0%; shelf-east shelf_home_a +
      shelf_armor_shop -> [42.95, 6.92, 19.07] ONE METRE, 31.5% -> 2.5%;
      shelf-west shelf_inn + the arrival stair's own handrails -> [25.54, 6.77,
      24.07] 5.65 m and 4.1 m UP the flight, 62.8% -> 0.0%; crossing cx_approach
      (the bridge approach ramp) -> [84.54, 22.78, 7.42] 6.50 m, 45.2% -> 0.7%;
      lockfive wv_planking (10.77 m nearer — she is under the drying decks) ->
      [67.29, 28.65, 6.92], but that is 6.96 m and only 8 of 524 standable cells
      are both legal and clear, so it is offered as a judgement, not a nudge.
      COTTAGE-STEPS HAS NO ARRIVAL FIX AND SAYING SO IS THE FINDING. Its
      occluders are walk_e_keepers-cottage__lock-five_l0_t06, the same edge's
      landing, and bar_e_..._railA — the arrival staircase ITSELF, plus lg_ks_
      frame/treads. She materialises underneath the flight she arrived on. All
      351 standable cells in the region were swept; the least-occluded legal
      on-screen position is 64.8%. walk_/bar_ are untouchable and the stair is
      not dressing, so per seam-canon §9.3 this is the camera's row, not the
      arrival's — and it is the THIRD independent instrument to say cottage-
      steps' framing is wrong (0/5 nav-eval, wentBack 5/5, now 99.8% occluded).
      NO BLEND EDIT WAS MADE FOR ANY OF THE SEVEN, and that is a ruling: every
      occluder named is either a house, a bridge ramp, a working deck, the
      shot's hero prop, or the walk graph. None of it is dressing, so none of it
      is mine to trim. Six coordinate proposals for the scenegraph, one camera
      referral. cutClearance improves or holds at every proposed point.
06:1x COORDINATOR: VISTA SHIFT CLOSED (60e3115) — leak 0.00% x16 (true zero;
      the expired-certificate lesson: A RE-AIM INVALIDATES EVERY SIGHTLINE
      AUDIT, re-run them); boatyard salmon proven camera-bound (dies at yaw
      90 without geometry); probe skip-budget bug found via the fix it hid
      behind (12 -> 64; smoke plumes ate the budget and invented a hole in
      the world). Six arrival relocations proposed with occlusion 100->~0%;
      cottage-steps referred to CAMERA (third instrument conviction).
      RULINGS: lockfive takes the 3.75m/8.7% fallback (7m would double the
      town's worst cut-teleport); haze-card taste waits for plates. SURGEON
      on the final round: arrival-override layer in the derive chain + the
      six coords + cottage-steps re-aim -> GO-FOR-BAKE -> 7-8 camera patch
      -> closeout checklist -> morning board. Vesper rig retarget in flight
      (user-authored model, ?model= A/B ready).
06:2x CHARACTER-INTEGRATION: VESPER SHIPS AS A PLAYABLE BODY
      (public/assets/characters/vesper/vesper-v2.glb, 13.5 MB).

      THE ASSET WAS BROKEN AND THE BREAK WAS NOT THE RETARGET. Tripo wrote
      EVERY joint node with no transform at all — no matrix, no TRS — so the
      whole skeleton lived only in skin.inverseBindMatrices, and those are in a
      different frame from the mesh: IBM^-1 translations are Z-up (head z=0.794,
      hands y=+-0.19) while POSITION is Y-up (y 0..0.9785, hands x=+-0.21). glTF
      skinning is jointGlobal @ IBM, and jointGlobal was the identity, so
      skinMatrix = IBM != I: the rest pose shreds in ANY conformant viewer, not
      just Blender. Renders of the raw import are folded paper. The two frames
      are the exact axis permutation P:(x,y,z)->(y,z,x) plus a uniform 1.022
      scale baked into the IBMs — CONFIRMED INDEPENDENTLY by fitting a
      similarity transform to the skin-weight centroids (Umeyama, rms 3.3% of
      body height), which lands every joint anatomically. tools/vesper_fix_glb.py
      rebuilds G_j = P @ normalize(IBM^-1), writes it into the node hierarchy,
      rewrites the IBMs as inv(G_j), and asserts |jointGlobal @ IBM - I| ~ 3e-8.
      Mesh, weights and textures untouched. THE "junk Icosphere (80 tris)" IN
      THE HANDOFF NOTES DOES NOT EXIST IN EITHER FILE — it is an artifact the
      Blender glTF importer manufactures; rogue.glb grows one too. Nothing to
      strip, and rogue's in-engine bbox was never polluted by it.

      RETARGET (no addons, explicit math, tools/vesper_retarget.py). World-space
      delta transfer: dW = R_pose @ R_rest^-1 on the donor, target driven to
      dW @ T[b]. T[b] is the load-bearing part — rogue rests in a T-pose, Vesper
      in a near-vertical A-pose (upper arm 68.5 deg below horizontal), so a
      plain rest-preserving transfer ADDS rogue's ~70 deg arms-down idle to her
      already-down arms and folds them into her ribs. T[b] is her rest bone
      rotated hierarchically until its anatomical axis matches the donor's rest
      axis: a VIRTUAL T-pose, computed, never baked, so the mesh binding is
      never touched and no shoulder deformation is made permanent. Torso and
      neck take T[b] = rest (both rigs already stand upright; measured hip/torso
      correction 0.0 deg). 20 mapped bones; Root/Pelvis/Waist/both clavicles and
      all 18 twist bones inherit — which is what actually deforms her, because
      Tripo put the skin weights on the TWIST bones and left L_Upperarm,
      L_Forearm, L_Thigh, L_Calf and Hip with zero weights.

      GAIT IS A PROPORTION PROBLEM, NOT A MATH PROBLEM, AND IT NEEDED A RULING.
      Faithful transfer is correct and looks wrong: rogue is an extreme chibi
      (hood-to-crown ~60% of his height, legs 17%), so his stylised bounce at
      full angle on a realistic body is a sprint — both feet airborne through
      most of the cycle, torso pitched forward, stride 44% of height. Damping
      slerps each delta back toward the DONOR'S OWN IDLE STANCE (damping toward
      rest would drift the arms out to the virtual T-pose). Shipped at
      0.62/0.58/0.55 legs/arms/torso; IDLE IS NOT DAMPED because the idle IS its
      departure from the idle stance. Rebuild faithful with a trailing "1,1,1".
      Ground lock: no foot IK, so hips are lifted a constant per clip until the
      deepest contact frame sits at z=0 (+0.011 idle, +0.021 walk/jump, ~1-2% of
      height). Feet slide; accepted for v1.

      SHIPPED: Idle 1.067s, Walking_A 1.067s, Jump_Full_Short 1.167s, all 30fps
      and named exactly for play3d's regexes. 92,987 tris, 41 bones, 3x4096
      textures embedded, feet at origin, faces +Z like rogue. Stills
      docs/qa/characters/vesper_v2_{idle,walk}_{front,side}.png — shoulders
      clean, hem behaves, braid intact, NO candy-wrap. Browser (townwalk, rt=1,
      nomusic): loads, Idle on arrival, Walking_A on W and back, feet EXACTLY on
      ground (box min.y == SIM.pos().y), height exactly MODEL_H 1.45, ghost twin
      built and stencil-stamped on both skinned meshes, page console clean.
      Rogue normalises identically (min.y 0, 1.45) so there is no scale
      regression — but his 1.45 is measured to the tip of a giant hood and hers
      to the crown, so she reads taller and leggier than the body she replaces.
      That is a taste call for the user, and [ / ] or ?ch= is the dial.
00:0x CHARACTER FACTORY: tools/gen3d.mjs lands — turnaround images -> rigged GLB
      through Tripo's v3 OpenAPI, headless, in genart/genmusic house style
      (.env TRIPO_API_KEY, per-file .json record, MANIFEST.md line per run).
      HEADLINE: RIGGING IS API-EXPOSED. POST /v3/animations/rig takes the mesh
      task_id and returns a SKINNED glb, and it accepts spec:"mixamo", so the
      bone names come back retarget-ready; /v3/animations/retarget then drops
      90+ preset clips onto it. No browser step anywhere — the factory is 100%
      scriptable: turnaround (genart) -> gen3d --views -> --rig -> our
      normalization pass -> retarget. Endpoints probed live, not just read:
      /v3/files (multipart, FREE), /v3/generation/{image,multiview}-to-model,
      /v3/animations/{rig-check,rig,retarget}, GET /v3/tasks/{id}. No v3
      balance endpoint exists; the v2 one still answers (--balance).
      SMOKE TEST BLOCKED ON BILLING, NOT CODE: the four Vesper A-pose views
      uploaded fine and the multiview body PASSED Tripo's schema validation —
      it failed at the credit check, which runs after validation, so the
      request shape is confirmed. Account balance is 0 and every generation
      endpoint returns 2010, down to the cheapest call there is (v2.5,
      texture:false). Nothing on this API is free; nothing was billed. Tool
      exits 2 with a plain "OUT OF CREDIT" + balance + top-up line rather than
      a stack trace. Re-run command is quoted verbatim in the tool header.
      Also tools/char_inspect.py (Blender -b, any character glb/fbx: verts,
      tris, quads, bones + naming, clips, texture sizes, world bounds) — the
      factory's acceptance instrument. Baseline MEASURED off the user's
      web-made vesper.glb: 12.86 MB, 66,823 v / 93,067 tri, 2 mesh objects,
      41 bones (mixamo-style), no clips, 4K basecolor+normal+RM. Its bounds
      are 1.909 x 2.000 x 2.000 — the web app fits to a 2-unit box, so it is
      NOT real-world scaled, which is the standing argument for keeping the
      normalization pass in our hands. API default face_limit is set to 50k,
      so an API Vesper should land materially lighter than 93k tri.
      Defaults: multiview whenever >=2 views, PBR on, texture_quality
      "detailed" (=4K; "extreme" is 8K), geometry_quality detailed, export_uv.
      QUAD IS OFF BY DEFAULT AND THAT IS DELIBERATE: quad:true forces FBX
      output, and the game loads GLB — --quad is a Blender-side switch only.
============================================================
NIGHT 3 SLATE (user-ratified ~01:40) — three lanes, no character generation
(user will direct character art personally; tonight uses existing approved art)
============================================================
LANE 1 FLAGSHIP — POPULATE THE WORLD: dialogue system (blue system voice,
      busts+expressions, data-driven) + NPC system (billboard figures via the
      arena's pose-plate technique, swap-ready model slots) + the existing
      15-character cast placed with voices from the chapter-2 script docs.
      Odessa at her post. The town gets people.
LANE 2 — THE NAV LOOP: re-score patched plates -> ranked fixes (quay plinth,
      gate stair ART pass after 3 camera attempts, shelf-east flow) ->
      re-bake -> re-score. Target 0.375 -> 0.6+.
LANE 3 — IN-PLACE TRANSITIONS (manual git worktree wt/transitions): the
      designated refinement — doors become seamless swaps; music literally
      uninterrupted; ?reload=1 fallback; merge only after the full gauntlet.
ALSO IN FLIGHT: idle-arms fix (measured retarget), arena turn-queue confirm.
PENDING USER (morning): valley v3 verdict, water/haze/rock review packet,
      Tripo API credits, open-source NPC pack browse (links in chat),
      vesper-v2 default look A/B.
00:3x VESPER'S IDLE: THE "GUNSLINGER" ARMS WERE ROGUE'S OWN STANCE, TRANSFERRED
      EXACTLY — NOT AN UNDER-ROTATED SHOULDER CORRECTION. Measured before
      touching anything, with a new instrument (tools/vesper_arm_probe.py: the
      upper arm's WORLD axis, shoulder head -> elbow head, as an angle away from
      straight DOWN, per frame, on either rig):

          rogue Idle   L 63.39  R 58.65        vesper-v2 Idle   L 63.39  R 58.65

      Identical to two decimals. The virtual-T correction does not under-rotate
      by one degree; the retarget math is right and what it faithfully carries
      is a chibi's neutral — arms ~57 deg out to the side and 40-50 deg swept
      BEHIND him, which is what clearing a barrel torso costs him and what reads
      as a drawn-gun half-A on a normally proportioned woman. The brief's
      working diagnosis is disproved by the instrument. Nothing in the transfer
      needed fixing; the donor's neutral is simply not her neutral.

      THE FIX: a constant, per-side, world-space offset on the whole arm chain,
      SOLVED against a measured target rather than dialled by eye
      (tools/vesper_retarget.py, new SHOULDER OFFSET stage):
          Cs = rotation_difference(idle-MEAN upper-arm axis, TARGET_UPPER)
          Ce = rotation_difference(Cs . idle-mean forearm axis, TARGET_FORE)
      baked as W_upperarm = Cs.dW.T and W_forearm/hand = Ce.Cs.dW.T. Constant
      offsets move only the neutral the motion is drawn around; PROOF is the
      EXCURSION (max angle between a frame's arm axis and that clip's mean axis
      — invariant under any constant rotation, unlike the off-vertical number):
      idle 2.20 / 2.02 deg and walk 23.37 / 22.10 deg BEFORE AND AFTER, to the
      hundredth. The breathing sway and the full arm swing are bit-identical.

      MEASURED BEFORE -> AFTER, upper arm off vertical, mean over the cycle:
          Idle       L 63.39 -> 13.40    R 58.65 -> 13.84    (bar: <= 15)
          Walking_A  L 67.46 -> 18.32    R 65.45 -> 19.96    (range 10.3-30.4)
          Jump       L 70.27 -> 19.64    R 66.98 -> 20.91
          elbow bend Idle L 56-62 -> 23.5-26.6,  R 60-65 -> 24.7-27.5 (soft)
      THE WALK GOT THE SAME OFFSET, deliberately: the residual is a rig-space
      fact about her shoulders, not a per-clip tweak, and correcting only the
      idle would fling her arms out the moment she took a step. Her walk never
      exceeded the donor's envelope — it WAS the donor's envelope.

      THE COAT DECIDED THE LAST TEN DEGREES, and only measuring found it. A
      plumb, near-straight arm puts 64% of the hand's vertices INSIDE the coat
      (deepest -38 mm at model scale): her coat flares to |x| 0.158 and
      y -0.131 at hand height, and the satchel hangs on her right. So the probe
      grew a SIGNED hand-vs-coat distance (nearest non-arm vertex, its normal
      picks the sign), and the four target angles were swept against it. Shipped
      at upper arm 12 deg out / 6-7 fwd and forearm 32-33 out / 26-28 fwd — a
      25 deg elbow with the hands resting just outside the flare. Idle
      clearance +0.0072 / +0.0028 (L/R) at the worst frame of the cycle, walk
      +0.0218 / +0.0058, both positive everywhere. The jump keeps ONE contact,
      frames 24-27 of 36 (landing crouch, right side, -0.016): logged, not
      chased — the file that shipped last night was at -0.148 through the whole
      walk-back swing, an order of magnitude worse, unnoticed.

      NOT THE DAMPING TRAP, and worth stating because the two look alike: the
      predecessor's warning is that damping toward REST drifts the arms out to
      the virtual T — but that is the DONOR's rest. Her own rest is arms-down
      (upper arm 68.3/67.3 deg BELOW horizontal, measured), so pulling toward
      HER rest pulls DOWN. Both readings agree; the offset solve is just the
      sharper tool, because it hits a target angle instead of a blend weight and
      costs the animation nothing.

      THE BAR IS NOW A GATE, not a screenshot: tools/vesper_verify.py asserts
      upper arm <= 15 deg off vertical every idle frame, elbow bend inside
      10-40 deg, hand-vs-coat > 0, and that the sway is still there. Run against
      last night's GLB it fails with "L arm 65.1 deg off vertical, bar is 15.0".

      SHIPPED: public/assets/characters/vesper/vesper-v2.glb, same path, same
      clip names and frame counts (Idle 0-32, Walking_A 0-32, Jump_Full_Short
      0-35 @30fps), 92,987 tris, 41 bones, 3x4096 textures, feet at z=0. Stills
      re-rendered, all four docs/qa/characters/vesper_v2_{idle,walk}_{front,side}
      .png. Browser (townwalk, rt=1, nomusic, ?model= pinned): Idle on arrival,
      Walking_A on W, arms hang and swing with no winging, page console clean,
      docs/qa/characters/vesper_v2_ingame_townwalk.jpg. NB for the next agent:
      the tab must be FOREGROUNDED — measured 61 rAF/s foregrounded vs a frozen
      loop hidden (a hidden tab hangs any await on requestAnimationFrame and its
      screenshot is stale); `osascript -e 'tell application "Google Chrome" ...
      set active tab index'` does it from the shell.

01:1x NAV-LOOP CUSTODIAN — RE-SCORE, THE STALE FILE UNDER THE METRIC, THE GATE
      STAIR, AND ONE FIX BUILT AND REFUSED.

      (1) RE-SCORE against the patch-bake plates, same judge, same N, new folder
      run-patchbake: TOWN 0.375 -> 0.375. The number did not move and the
      composition did: lockhead 0.00 -> 0.40, gate 0.00 -> 0.20, and three
      single-trial slips the other way (loop-stairs / deep-stairs / north-landing
      1.00 -> 0.80, which at N=5 is one reading each). BOTH WATCH ITEMS MOVED
      WITHOUT SCORING. cottage-steps: wentBack 5/5 -> 3/5, onWalk 0.89 -> 1.00,
      and the arrival that was 99.9% occluded is now 3.1% — the re-aim landed, and
      all five judges now correctly read "climb the stairs to the upper walkway".
      boatyard: the roofs-as-stairs read is largely gone (3 of 5 judges now name
      the circular deck and the dock; waypoints 0-2 land on the real deck and are
      reached), but it still scores 0.00 and CANNOT SCORE — its only exit is the
      seam it arrived by, so `onward` falls back to that seam and the shot can only
      pass by walking back out the way it came in. Every judge instead reads
      "continue deeper into the yard". That is a MAP fact, not an art fact, and it
      is referred up rather than papered over.

      (2) THE FINDING OF THE NIGHT: THE EVAL HAS BEEN SCORING SPAWNS THE RUNTIME
      DOES NOT USE. `node tools/routes_derive.mjs --check` said STALE. The arrival
      overrides (7e7d7cd) reached `cameras.json` and `world/scenegraph.json` — so
      the GAME has been spawning players correctly all along — but
      `dellhollow.routes.json` was never re-derived, and `nav_eval` composites its
      input image at `routes.json`'s `entries[].at`. Every nav-eval number since
      that commit, run-newbake and run-patchbake included, put the character
      somewhere the game does not. Eight arrivals move: crossing 6.50 m,
      deep-stairs 4.58 m, lockfive 3.75 m, loop-stairs 2.57 m, boatyard 1.29 m,
      shelf-east 1.00 m, cottage-steps 0.70 m. BOTH FREE INSTRUMENTS SAY IT IS
      BETTER, which is what makes it a fix: oracle-world 0.875 -> 0.938 (Lock Five,
      one of the two documented walker misses, now escapes from its real spawn),
      and `composite.occludedFrac` — seam-canon §10.2's "arrives invisible" —
      collapses on five shots: boatyard 0.947 -> 0.000 (she was materialising
      inside the hero hull), loop-stairs 1.000 -> 0.000, lockfive 1.000 -> 0.058,
      crossing 0.450 -> 0.000, shelf-east 0.455 -> 0.016. Four of sixteen arrivals
      were behind foreground geometry; one is. cine_test PASS 636/0 on the
      regenerated file. Runs: run-patchbake, run-ow-truearrivals.

      (3) THE QUAY PLINTH — BUILT, MEASURED, AND NOT SHIPPED (11245a4). The banked
      follow-up is implemented behind `-- plinth`, OFF by default, because it does
      not pass its own acceptance test: probe every tread centre, ray down, and
      NOTHING may be found above it. Four formulations failed in the same place.
      Lofted-per-leg put three treads' stone 6-42 cm proud — a leg's treads do not
      lie on the straight line between its ends, THE FLIGHT IS A LOOP. Per-face
      solids clipped at their own front edge came out shifted exactly one tread
      down the flight, because the walk quads OVERLAP and a face reaches past its
      neighbour's centre. Midpoint tiling fixed that and left the cross-flight
      case: the two flights leave one yard and interleave within 0.10 m in plan at
      0.3-0.9 m of height separation. A ribbon clamp either sinks the whole plinth
      to the waterline (the grown footprint samples the quay deck five metres down
      and reads it as a tread it stands proud of) or, capped, puts the stone back
      through the boards. THE FINDING, so nobody re-derives it: a per-face solid
      cannot bound these footprints and no clipping rule on a face's own neighbours
      will. It wants a RASTER — sample both ribbons on a fine XY grid, take the
      lowest ribbon within a 1.10 m window per cell, lift the mass from that height
      field, and "no stone above any tread" holds by construction. Every constant
      is measured and reusable. THE MASTER WAS NEVER SAVED during any of it; its
      sha256 was verified unchanged against the pre-work baseline. Default path
      re-verified bit-for-bit: 100 faces cut, 998 verts, 3 objects, 12 legs.

      (4) THE GATE STAIR — THE ART IS NOT DIM, IT IS ABSENT (0d43d9c). Three camera
      attempts had failed on `valley-gate__inn` and the ruling was that the answer
      is art. Rayed down from all sixteen walk faces, here is what renders under
      the flight every player walks in their first ten seconds: NOTHING AT ALL
      under l0_t01; `shelf_stair_underworks` 1.90 m below l1_t02, 0.89 m below
      l1_t03, and 0.22 m ABOVE l2_t01 — the scaffold coming up through the stair.
      There are no treads in the master. The Keepers' Steps disease, fourth
      instance, worst yet. tools/gs_build.py builds the flight the walk graph
      describes: 12 tread runs + 2 landings on the ribbons' own planes, 13 posts +
      13 rail runs on the six already-hidden `bar_` lines, and 9 CHEEK-WALL
      SEGMENTS — which are the point. From 40 m at 28 degrees the treads are a
      3-pixel band the colour of the ground; what a high camera resolves is a
      raking line lit along its top throwing a hard shadow across the treads, the
      only element in frame whose direction is the route's. Stone, 0.38 m proud,
      tinted LIGHTER and cooler than `gate_road` on purpose. Two things the build
      had to be told: half-width comes from the LEG'S CENTRELINE (per-tread
      half-widths put the wall inside the widest tread — all six refused), and the
      wall is SEGMENTED, because at the head of the flight the outboard side is the
      gate yard's own walkable pad where a proud wall is a solid over a walk sample
      and the gate is right to refuse it (9 built, 13 refused). ADDITIVE ONLY, and
      the reason is a collision the coordinator should rule on once: `ls_build.py`
      already cuts `shelf_stair_underworks` inside ITS box, restoring from an
      `LS_SRC_*` snapshot every run, so a second pass snapshotting the same
      datablock silently undoes the first whichever runs second. The boxes are 30 m
      apart; it is the SNAPSHOT that collides. So the 0.22 m poke survives and is
      printed by the pass's own acceptance probe instead of hidden.
      GATES, delta-owned against tools/blends/backups/dellhollow-master.pre-gs.blend:
      master_walk_qa FULL PASSED 367/367 bit-identical, worst vertex delta
      0.000e+00, 1308/1308 = 100.00%. Region 14,28,0,8 BIT-IDENTICAL to baseline
      (431/468 = 92.09% before AND after, same pre-existing
      t2c_GB5_road_marketrow); this pass's entire delta is ONE headroom sample,
      gs_walls at 0.21% against a 1% threshold. geometry_audit region: 2 offenders
      / 0 strays, IDENTICAL to baseline — adds NONE, on 62 bbox-overlapping pairs
      against baseline's 40. glTF survival --prefix gs_: 3 out / 3 in, 0 white.
      Deterministic, 676 verts on two clean runs.

      (5) THE FINAL RE-SCORE COULD NOT BE RUN, AND THE REASON IS NOT THE TOWN.
      The pinned judge is unavailable: the Gemini project has exhausted its monthly
      spend cap and every request returns HTTP 429 RESOURCE_EXHAUSTED, "Your project
      has exceeded its monthly spending cap". The re-score in (1) completed before
      the cap was hit; the run against the corrected arrivals died at 4 of 80 and
      its folder was deleted rather than left as a partial. Swapping to an
      unpinned or different model to produce A number was refused — seam-canon
      §10.3 rule 2 pins the model precisely so two bakes stay comparable, and a
      number from a different judge would not be the metric. So the town's standing
      perceptual score is 0.375 (run-patchbake, 6 of 16 shots >= 0.80) and the work
      after it is UNSCORED. What CAN be said without the judge is in (2): the free
      instruments both moved the right way and the eval's inputs are now honest for
      the first time since 7e7d7cd, so the next run to complete will be the first
      one measuring the town the runtime actually ships. Top-up is at
      https://ai.studio/spend; the re-run is one command:
          node tools/nav_eval.mjs --n 5 --temp 1 --conc 4 --stamp truearrivals
      SHELF-EAST's backwards flow (assignment (c)) was NOT attempted for the same
      reason: its whole defect is perceptual — 5/5 judges walk toward the door the
      player came through — and there is no free instrument that can tell whether
      added ground language fixed it. Building unverifiable art into the master at
      04:00 with the metric offline is how a bake acquires debt nobody can see.
01:2x WORLD-POPULATION: DELLHOLLOW HAS PEOPLE IN IT.
      Two self-contained modules + two data files; play3d.html UNTOUCHED (the
      script tags and the one hook line are in the SendMessage to main).

      public/js/dialogue.js — window.Dialogue. FF-grammar talking window in the
      ruled BLUE system-voice language, drawing NO chrome of its own: the frame,
      bevel, grain, title bar, cursor glyph and portrait plate are ui_kit's
      primitives and the only CSS in the file is geometry, so a re-tint of
      ui_kit re-tints every conversation. Four deliberate departures from the
      shop/menu panel: bottom-anchored (a dialogue box is furniture at the foot
      of the frame; the pause menu is a screen you go to); NO SCRIM (the menu
      veils the world because you have left it, a conversation happens IN it);
      the bust hangs OUTSIDE the frame at 190px so a 512px colour-pencil plate
      reads as a portrait rather than a stamp; and the typewriter runs on a
      TIMER, not rAF, because rAF is dead in a background tab and that is where
      every headless verification in this project lives. Expressions are per
      LINE (expr-<mood>.png), falling back to bust.png the moment a mood has no
      art — so a mood can be WRITTEN before it is DRAWN. UILOCK via
      EBUI.panel({name:'dialogue'}); no new contract.

      TWO BUGS FOUND AND FIXED IN THE DOING, both invisible until you build a
      BOTTOM-anchored panel: (1) ui_kit's veil is position:fixed, which is right
      for the centred menu and shop and WRONG here — play3d's stage (#s) is a
      16:9 letterbox inside the page, so on any window taller than 56.25vw the
      dialogue box dropped into the black bar UNDER the game. Re-homed to
      absolute inside the stage (falls back to fixed with no stage). (2) the
      typewriter clamped dt to 0.25 s; Chrome throttles a background tab's
      timers to ~1 Hz, so a two-second line took eight seconds THERE and nowhere
      else — exactly the bug that only ever appears in the test. dt is unclamped
      now: elapsed time is the truth.

      public/js/npc.js — window.Npc. The battle arena's figure, deliberately:
      ui_kit's chroma key (magenta-ness -> despill -> largest island -> crop to
      opaque bounds, which is what puts the FEET on the bottom edge) feeding a
      bottom-anchored, YAW-ONLY billboarded plane — it turns to the camera and
      stays STANDING, because a full billboard lies down as the camera pitches —
      plus the same procedural blob shadow. Added: `tint`, which is the
      expansion script's OWN instruction for sprite-first extras ("reuse the
      poppy sheet, tint #d9b08a"). Calls EBUI.chromaKey directly rather than
      poseSprite() because here the BODY is a data field, so a villager can wear
      a borrowed plate, a side-on pose, or (tomorrow) a GLB without ui_kit ever
      learning about villagers. idleBehavior stand | lean | wander; wander asks
      SIM.walkFloors + SIM.blocked per step, so it respects WALKLOCK semantics
      and owns no collision logic. E-prompt is shop.js's registerPrompts/tick
      shape verbatim, INCLUDING sgTick's arrival suppression.

      THE DISCIPLINE, ASSERTED NOT PROMISED (browser probe, townwalk): 0 NPC
      objects in collide, 0 in walkRef, 0 in allMeshes — route_overlay's rule,
      because a person who becomes a step or an invisible wall is a worse bug
      than a person you can walk through. 0 stencil writers: the player's ghost
      pass owns stencil ref 1, and an NPC that stamped would punch holes in her
      see-through-occluders twin.

      TWO PROMPTS, ONE PERSON. shop.js arms an identical banner off the same
      counter pad. Solved twice over: Npc.tick() runs AFTER Shop.tick() in the
      physics tick (that is what the hook line's POSITION buys), so standing the
      shop banner down is the last word in the frame; and EBUI's globals table
      is one-handler-per-key, so npc.js wraps onGlobalKey ONCE into a chain
      where a `false` return falls through — no dependence on script order.
      Verified in del-item-int: one banner ("Talk to the chandler? [E]"), shop's
      suppressed, E opens the GREETING, and the greeting's choice carries
      effects:{shop:'del-item'} which opens the counter AFTER the window closes.
      Greet, then trade.

      CAST — 13 people, every one of them out of the scripts, ZERO new proper
      nouns invented. Odessa at the Lockhead (canon station) and Maren on the
      lock apron are the only two with busts and expression art, and Odessa's
      `warm` is spent exactly ONCE, on the repeat-visit line, guarded as the
      scripts guard it. Hobb, Pell, Sorrel, Creel and Nib are the scripts' own
      sprite-first, NAMEPLATE-ONLY extras on reused tinted villager sheets (the
      script names the poppy sheet for Sorrel by name). The eel-wife and the
      boatwright are canon ROLES the scripts name without naming, so they carry
      title nameplates. Mochi is at the eel-stall because Beat 2 says he is, and
      speaks in system boxes. Three shopkeepers by their shops.json titles.
      Every line is 8-18 words to VOICES.md; one aphorism per conversation from
      a licensed source; nobody carries a plot fact; nobody says "afraid".

      FRAMING WAS MEASURED, NOT GUESSED. First placement put Odessa 3% visible
      in the shot NAMED AFTER HER POST and the boatwright 0% in two shots — a
      villager nobody can see is a villager who is not there. Sampled every walk
      vertex of each owning shot with ROUTES.visibleAt (GL readback against the
      shot's OWN baked depth map; a hidden tab's screenshot is stale, pixels are
      truth) and re-placed five. AFTER, standing where the player stands, in the
      shot that owns their district: chest >=69% and head 100% for all ten town
      NPCs. Lesson worth keeping: a placement audit must be run under the shot's
      OWN camera — SIM.shot() followed by SIM.tick() lets sgTick's region
      correction pull the camera back and silently measures the wrong frame.

      SUITES GREEN, unmoved: slice 514/0, cine 636/0 (+3 soft), economy 204/0,
      seam_walk 9/9. Screenshots docs/qa/npcs/ (quay, fish dock, lockhead,
      chandlery prompt, and the open window with Odessa's grave bust).
      ENVIRONMENT NOTE for whoever is next: the boot volume hit 232 MB free
      mid-run and Chrome silently stalled 2 MB PNG fetches — image loads that
      "hang" tonight are a disk symptom, not a code one. /private/tmp held 8 GB,
      most of it stale render dirs from the 28th.

01:2x THE GATE STAIR'S OCCLUDER, NAMED AT LAST — AND IT IS NOT THE RIM LIP. THREE
      INSTRUMENTS NOW POINT AT THE SAME TWO OBJECTS.
      Post-bake measurement of the gate stair build (cine_bake --cams gate,shelf-west;
      gate 252.6s, shelf-west 226.4s, depth 2.0/2.3s, CINE BAKE DONE 483.7s):
          shot_probe valley-gate__inn   gate 14.6 -> 14.6    shelf-west 37.8 -> 36.6
      THE NUMBER DID NOT MOVE AND IT STRUCTURALLY COULD NOT. shot_probe asks whether
      the WALK LINE is occluded by a nearer rendered surface. New treads sit 30 mm
      BELOW that line, so they can never un-occlude it; the cheek walls stand 0.38 m
      PROUD beside it, so they can only ever add occlusion. Measured, the walls and
      rails account for 1.2% of gate's occlusion and 3.6% of shelf-west's — which is
      the whole of shelf-west's -1.2. The build is right and the instrument cannot
      see it. Reported as measured rather than spun.
      SO THE OCCLUDER WAS RAY-CAST AND NAMED. 41 samples x 2 heights from each
      camera to the arrival edge, first render-visible hit tallied:
        gate        26.8% veg_gate_rimclump_11   23.2% t2c_G3_awning_tollyard
                    13.4% veg_gate_rimclump_12   12.2% t2c_GB5_road_marketrow
                     8.5% CLEAR                   3.7% gate_ground
        shelf-west  30.5% CLEAR                  24.4% gate_road
                    13.4% gate_winch              6.1% t2c_GB5_road_marketrow
      THE ASSIGNMENT'S PREMISE IS WRONG AND THE MEASUREMENT SAYS SO. The occluder
      was given as "gate district ground at x 16-24 y 5-12 h 24-27". `gate_ground`
      is 3.7%. The foliage looked like the answer — two rimclumps, 40.2% combined,
      and `veg_` is pure dressing, so it was squarely inside the "trim it if it is
      dressing" authorisation. IT WAS TESTED BEFORE IT WAS TRIMMED, in-blend, no
      bake: pushing both clumps 1.0 / 1.8 / 2.6 m off the lip moves fully-clear
      8.5% -> 11.0% AND THEN PLATEAUS, because `t2c_GB5_road_marketrow` grows
      12.2% -> 31.7% as they get out of its way. The occluders are LAYERED. Trimming
      the planting would have cost the gate its rim foliage and bought 2.5 points.
      Nothing was moved; the master was not saved.
      THE ACTUAL ANSWER, and it is a convergence rather than a guess: the two
      objects behind the foliage are `t2c_G3_awning_tollyard` and
      `t2c_GB5_road_marketrow`, and BOTH ARE ALREADY FLAGGED BY BOTH STANDING GATES,
      independently of this shot and of each other:
        master_walk_qa region 14,28,0,8   t2c_GB5_road_marketrow is the coverage
                                          offender (37 samples) AND a headroom
                                          offender (44 samples, 9.40%);
                                          t2c_G3_awning_tollyard 31 samples, 6.62%
        geometry_audit region 14,28,0,8   t2c_G3_awning_tollyard IN
                                          t2c_GB5_road_marketrow, frac 0.208,
                                          depth 1.24 m
      An awning buried 1.24 m inside a road slab, both standing over the town's
      arrival staircase. That is why THREE camera attempts failed: no aim can help
      when a mis-placed awning and a road are parked on the flight. This is one
      scoped assignment for the TRANCHE-2 lane (`t2c_` is its namespace, not the
      nav lane's, and taking another lane's art at the end of a shift is how a
      master acquires damage nobody can attribute) — and it is now specified with
      a number attached to each object rather than a suspicion.
      PREDICTION, to be checked and not trusted: gate is 8.5% clear with those two
      contributing 35.4%. Fixing them should take the shot to roughly 45-70% clear,
      which is the first time this staircase would be visible at all.

01:3x THE METRIC'S OWN NOISE FLOOR, MEASURED BY ACCIDENT — AND IT CORRECTS TONIGHT'S
      READING OF ITS OWN RESULT.
      A second complete gemini run (run-20260730-234241, N=5, 80 trials, 0 errors)
      exists against the SAME patch-bake plates and the SAME pre-fix routes.json as
      run-patchbake. It was produced incidentally and nearly deleted as clutter; with
      the spend cap now exhausted it is irreplaceable, so it is committed. Two
      independent draws of the same measurement on identical inputs:
          13 of 16 shots IDENTICAL
           3 shots differ by exactly +-0.20 — one trial each at N=5
          TOWN 0.362 vs 0.375  =  +-0.013
      SO THE METRIC'S RUN-TO-RUN NOISE AT N=5 IS +-0.20 PER SHOT AND ~+-0.013 AT
      TOWN LEVEL, and every per-shot number tonight has to be read against that.
      THIS DEMOTES MY OWN HEADLINE. The 01:1x entry reported the patch-bake re-score
      as "the number did not move and the composition did — lockhead 0.00 -> 0.40,
      gate 0.00 -> 0.20, three shots 1.00 -> 0.80". Against this replicate:
        - gate +0.20 and north-landing -0.20 are EXACTLY one trial. They are noise.
          Indeed the replicate shows gate at 0.00 and 0.20 on the same plates.
        - lockhead +0.40 is two trials, at the edge of what N=5 can resolve, and the
          replicate independently puts it at 0.20. Suggestive, NOT established.
        - loop-stairs / deep-stairs 1.00 -> 0.80 reproduce identically in BOTH runs
          against newbake, so those are more likely real than the 0.20s.
      The defensible statement is therefore the narrow one: THE PATCH-BAKE PRODUCED
      NO MEASURABLE TOWN-LEVEL CHANGE (0.375 -> 0.375, replicate 0.362), and no
      individual shot moved by more than this metric can resolve at N=5. The
      continuous sub-scores and the occlusion numbers are what carried real signal
      tonight, exactly as seam-canon §10.1 predicted they would for a bake whose
      legibility work was confined to a few shots.
      CONSEQUENCE FOR THE NEXT RUN, and it is a cheap fix: N=5 cannot resolve a
      one-shot fix. The empty band in §10.2 (nothing between 0.20 and 1.00) is what
      makes 0.6 a safe threshold, but it does NOT make a 0.20 delta meaningful.
      Anything claiming a per-shot improvement should be run at N=10 on that shot,
      as the surgery bake's crossing result already was (2/10 -> 10/10, which is why
      that one was believable and these are not).

## NIGHT 3, coordinator entry — the Emberbrook founding night (2026-07-31 ~04:45)
User logged off. Ratified tonight: the Emberbrook town map (public/townmap/
emberbrook.map.json — river+brook as story spine, Vesper unhomed, Rowan's/Lake's
houses corrected, Poppy's bakery, lamps{} rounds canon, impliedScale ruling), the
build workflow (concept frames = inspiration only, plates always baked from geometry;
dusk-vs-golden A/B before committing the bake hour), and the parallelism plan.
LANES LIVE: (1) exterior flagship — serial spine on the master blend; at BLOCKOUT
FREEZE forks blend copies for a second district builder (entrance approach), at each
PARCEL FREEZE a baker agent fans out; (2) interiors — separate blends, anti-boring-box
mandate (inn parlour first, taste-check checkpoint); (3) Dellhollow polish — gate
awning surgery + weapon-shop arrival + N=10 rescore; (4) coordinator holds play3d
wiring (WALKLOCK now covers emb-*), reviews at every checkpoint, morning board.
DONE EARLIER TONIGHT: vesper-v2 UAL build shipped (tight idle, jog run, cadence lock);
turnaround factory tool + 5-char cast batch; 4 villagers retargeted + LIVE IN TOWN as
3D bodies (skeleton boneTexture leak found+fixed); in-place transitions merged, whole
gauntlet green (160/0, 32/0, 636/0, 294/0, 514/0, 204/0); CLAUDE.md context index
created (user ruling: repo docs carry what compaction loses).

03:1x DELLHOLLOW POLISH — THE AWNINGS ARE OFF THE GATE STAIR, THE OCCLUDER STACK IS
      THREE DEEP, AND THE WEAPON SHOP'S DOOR HAS NOWHERE LAWFUL TO STAND.
      RECONCILED FIRST, as the handover asked. docs/qa/index.html was the nav lane's
      regenerated gallery and make_qa_index.py rewrites it wholesale, so it was
      committed untouched (f8b3fc5) before anything of mine ran. The del-cine gate
      bg/depth were NOT uncommitted — they had already shipped in 3c612ac. STILL
      UNTRACKED AND NOT MINE: docs/qa/naveval/run-ow-check-0031/ (32 MB) and
      docs/qa/districts/exposure_{dusk,lifted}.png; nothing in this lane writes to
      either path. ALSO LIVE IN THE TREE WHILE I WORKED: the Emberbrook lane editing
      cine_bake.py / cine_solve.mjs / cine_test.mjs / nav_eval.mjs / seam_walk.mjs /
      emb_blockout.py / emberbrook-master.blend, and the character lane editing
      public/assets/scenes/townwalk/*. Every commit below is a strict pathspec and
      none of those files is in one.

      JOB 1 — THE NAMED OCCLUDERS, AND THE LAYER BEHIND THEM.
      The census was REPRODUCED before anything moved and is now a committed tool
      (tools/t2_occluder_census.py) rather than an ad-hoc script. Reproducing it also
      corrects the 01:2x entry in one respect: `t2c_GB5_road_marketrow` is not a road
      slab, it is an AWNING (t2_color_pops row "toll-road awning row"). The road it
      is named after is `gate_road`, and that distinction turns out to be the story.
        gate, 82 rays        BEFORE   AFTER        shelf-west, 82 rays  BEFORE  AFTER
          CLEAR               7.3%    17.1%          CLEAR              32.9%   36.6%
          t2c_G3_awning      19.5%     gone          t2c_G3              4.9%    gone
          t2c_GB5_marketrow  14.6%     gone          t2c_GB5             3.7%    gone
          veg_rimclump_11    25.6%    25.6%          gate_road          29.3%   30.5%
          veg_rimclump_12    13.4%    13.4%
          gate_road           1.2%    23.2%   <- THE THIRD LAYER
        shot_probe VISIBLE, shipped plates: gate 14.6% -> 29.3%, shelf-west 36.6% -> 45.1%
      THE 01:2x PREDICTION WAS 45-70% CLEAR AND IT DID NOT LAND. Same layering the
      foliage test found, one level deeper: the rim planting hid the awnings, the
      awnings hid the ROAD LIP, and removing a layer promotes the next. Reported
      against outcome rather than quietly dropped. A fourth pass owes an answer for
      rimclump_11/12 (38.9%) and gate_road (23.2%), and the road lip is TERRAIN, not
      dressing, so it is a different kind of job from the last three.
      THE FIX IS A SEARCH, NOT A PLACEMENT (tools/t2_gate_awnings.py). Both ids keep
      their name and accent material and are rebuilt as STALLS whose site must
      satisfy all of: flat ground of the district's own kind under the whole
      footprint; >= 0.25 m clear of the route ribbon; 2.80 m of clear air; ZERO of
      100 camera->staircase sightlines crossed (gate AND shelf-west, feet and head,
      exact segment/AABB); inside the gate frustum with margin.
      THE DISTRICT ANSWERED BACK THREE TIMES, and each answer is in the script:
        1  A down-ray from z 34 over the gate road hits BUNTING, the arch beam or a
           rim crown long before the road. "What is the ground here" answered ARCH
           for most of the parcel until the ray started at z 26.
        2  A 3.0 m ridge does not fit under a street strung with bunting at z 24-28:
           demanding 3.1 m of clear air cut the one usable verge into 0.5 m offcuts.
           The stall is 2.65 m to the ridge, 2.00 m to the hem.
        3  THE PARCEL HOLDS EXACTLY ONE LAWFUL OPEN PATCH — x 4.25..7.75, y 1.75..3.00,
           3.5 x 1.25 m — and no 4.4 x 3.2 m one anywhere. So the search also offers a
           WALL-MOUNTED bay (four ray checks for a flat host behind the ridge, front
           posts on measured ground, brackets into the host), which is what an awning
           over a counter actually is. G3 took a wall bay on the gatehouse and
           recovered 100% of its 5.60 m2; GB5 took two ground bays and recovered 7.68
           of 14.08 m2. THE MISSING 45% IS REPORTED, NOT RECLAIMED BY LOOSENING A
           CONSTRAINT — and it did not cost the frame its colour: t2_probe_chroma puts
           the gate at 6.34% chromatic pop, inside pops-of-colour's [5%, 11%] band
           (shelf-west 6.22%, shelf-east 10.69%).
      GATES. geometry_audit 14,28,0,12: 2 offenders -> 1, and the survivor
      (t2c_G4_arch_banner IN gate_arch, frac 0.047 depth 0.14) is pre-existing and
      unchanged. master_walk_qa 2,40,0,14, before -> after:
        coverage {GB5 37, G6 56, GB4 58}      -> {G6 56, GB4 58}
        headroom {GB4 159, G3 31, GB5 44,
                  G1 48, G6 56, G2 25}        -> {GB4 159, G1 48, G6 56, G2 25}
      Bit-identical outside the edit. THE FOUR SURVIVORS ARE THE SAME DISEASE in the
      Porters' Yard — GB4_yard_tarp_big, G6_tarps_cargo, G1/G2_awning_porters, cloth
      hung at chest height over a walk surface. Outside this brief, now named with
      sample counts.
      REBAKE SET DERIVED, NOT GUESSED: all four footprints (both ids, old and new)
      sampled against all 16 frusta by ray-cast gives gate, shelf-west AND shelf-east.
      shelf-east sees G3's OLD site on 14 of 32 samples, which no eyeball calls.

      JOB 2 — ONE ARRIVAL FIXED, ONE MEASURED AND REFUSED.
      New instrument, because §10.2's "arrives invisible" had no offline tool:
      tools/arrival_probe.py rasterises the character's own box at an arrival against
      the shipped depth plate. Over every door and cut arrival it reproduces the
      transitions lane's number exactly and finds five more.
      FIXED: `weapon-shop__armor-shop:0.372 shelf-east>shelf-west` at
      [37.896, 19.04, -5.527] was 91/91 samples ON SCREEN and 0 surviving the depth
      test. The occluder is the weapon shop's OWN building (58 of 63 rays stop on
      shelf_weapon_shop). Override [39.0, 19.04, -4.3]: 0% -> 100% body, 0% -> 100%
      chest. Clears the band by 0.86 m against the derived 1.60 — under target, over
      the 0.5 m floor, so cutGeometry accepts with the documented warning.
      REFUSED, AND THIS IS THE FINDING. The DOOR arrival [35.274, 19.07, -6.925] is
      0% too and HAS NOWHERE LAWFUL TO GO. Every walkable sample within 5 m taken
      from the shipped GLB (not from bounding boxes — my first proposal was rejected
      by cutGeometry's own checker for exactly that, which is the checker working):
      on shelf-west's ground EVERY point >= 1.85 m from the door scores 0% chest, and
      every visible point is 1.55-1.81 m from it, inside the door's own trigger. The
      single point outside the radius clears the shelf-east seam by 0.02 m — §1's
      exact failure mode.
      SO THE ARRIVAL IS NOT THE BUG. scenegraph_derive's streetDir breaks a tie
      between two equally flat roads ALPHABETICALLY: "road item-shop->weapon-shop"
      beat "road weapon-shop->armor-shop" on the string compare, and the backoff went
      WEST. And west is the 7 m of shop street shelf-west cannot see, because
      shelf-west's yaw went 120 -> 40 in 0c0b522 as a stair-yaw test and shipped in
      766da20 on the stair moving 20.7 -> 37.8% — with nobody measuring the cost,
      because shot_probe was only ever pointed at valley-gate__inn. MEASURED NOW:
      from yaw 40 the camera stands at x 47 on the far side of its own street and
      `item-shop__weapon-shop` — 8.6 m of road THIS SHOT OWNS — is 0% visible from
      t=0.17 to t=1.00. A yaw-120 re-solve puts it at [16.0, 24.4, 26.3], the side
      the shot's own description assumes. NOT DONE HERE: re-aiming is outside this
      lane's touch list and is the user's own gate. RECOMMENDATION FOR THE MORNING:
      it is the one change that fixes the door arrival, the 7 m and the street's
      legibility together, and the awning surgery may already have paid back the
      stair visibility that yaw 40 was bought with (gate 14.6 -> 29.3% without it).
      MECHANISM ADDED, DELIBERATELY UNUSED: scenegraph_derive now honours
      arrivals:{"door:<landmark>": [x, up, -y]} on the owning camera, validated and
      rejected loudly otherwise. No door override ships.
      ALSO SURFACED BY RE-DERIVING (the brief required it): the town-side derive had
      no hasBundle guard, so Emberbrook's ratified-but-unbaked map put an emb-cine
      node and two portal edges into the shipped scenegraph — cine_test failed "the
      way out is only offered in shot 'undefined'" and slice_test CRASHED opening the
      missing GLB. Interiors have always been guarded this way; towns were not, and a
      stale scenegraph.json was hiding it. Guarded; the node returns by itself the
      day emb-cine is baked.
      BONUS, from Job 1 rather than Job 2: `shelf-west>gate` was one of the four
      §10.2 "arrives invisible" shots. The awnings were standing on it.
      body 12.1% -> 76.9%, chest 3.6% -> 57.1%.

      JOB 3 — N=10, AND IT SAYS NO.
      oracle-world FIRST per §10.3 rule 1: 0.938 (15/16), so the walker was intact.
      Judge pinned gemini-3.6-flash, N=10, 0 errors, ~20 trials of spend total.
                          tranche-2   surgery bake   after the awnings
        gate score          0.00         0.00           0.00
             onWalk         0.450        0.655          0.667
             progress       0.599        0.633          0.617
        shelf-west score    0.00         0.00           0.00
             onWalk         0.916        0.700          0.876
             progress       0.421        0.565          0.086
             wentBack       5            3              0
             stuckLegs      2.2          3.3            6.4
      THE STAIRCASE IS TWICE AS VISIBLE AND BOTH SHOTS ARE EXACTLY AS ILLEGIBLE, and
      the two instruments agree about why: 17.1% clear is a less buried staircase,
      not a visible one. §10.1's pattern repeating — the metric did not miss a fix,
      there was not yet a fix to see. N=5 could not have resolved even this; N=10 can,
      and it says no.
      ONE ROW IS NOT NOISE-SHAPED AND IS NOT EXPLAINED: shelf-west's wentBack goes
      5 -> 3 -> 0, monotone across three bakes, and "reads backwards" is one of
      §10.2's two named sub-defects — while in the same run progress collapses to
      0.086 and stuckLegs doubles to 6.4. A plausible story is that the readings now
      aim AT the stair instead of back down the street and the walker's greedy fan
      cannot climb it (§10.3 rule 1's known steering limit), which would make it
      pessimism rather than regression. That is a hypothesis; the viewer overlay is
      where it gets settled.

      SHIPPED GATES, on the tree as committed: cine_test 636/0 (+3 soft), seam_test
      294/0 (+4 soft), slice_test 514/0, seam_walk 9/9, plate_flat 0 of 16 flags,
      routes_derive --check CLEAN, geometry_audit 1 pre-existing offender, walk QA
      bit-identical outside the edit. Commits: f8b3fc5 (reconcile), c597c53 (surgery),
      81c8718 (arrivals), 14b1597 (rebake), aceee4f (N=10 evidence).

03:0x EMBERBROOK IS FOUNDED — the map raised gray, Festival Square built for real,
      and four defects the first render found that no gate would have.
      Deliverables: docs/plans/emberbrook-town.md (the plan, as a TRANSLATION of
      public/townmap/emberbrook.map.json rather than an invention — the map is
      Stage 0 and was already authored, so landmark ids, names, positions and
      premises are canon and the plan's job is build order + camera grammar +
      gates); tools/emb_blockout.py; tools/emb_export.py; tools/emb_square_build.py;
      tools/emb_shots.py; public/assets/scenes/emb-walk/; docs/qa/emberbrook/.

      THE BLOCKOUT IS town_blockout.py's SIBLING, NOT ITS FORK. Same contract, same
      walk-mesh NAMING — which is the whole point, because cine_regions.mjs proves
      coverage by matching mesh names to map records and a rename silently blinds
      the camera gate to a district. Half of town_blockout is Dellhollow's GORGE
      (river spec, pools, dam wall, waterwheels, two cliff slabs); that half is
      replaced with this town's own context — a rise, a brook, a pond, a river
      vista and a ring of wood. MERGING THE TWO IS FILED, NOT DONE, and the trigger
      is a THIRD town, exactly as district_lib.py was created on the third copy of
      a walk guard rather than the second.

      FOUR RULES, AND THREE OF THEM WERE FOUND BY LOOKING AT THE FIRST RENDER:
      (1) GROUND IS NOT WALKABLE (town-legibility.md: the walkmesh IS the route).
      (2) A LANDMARK'S COORDINATE IS THE BUILDING, NOT THE DOORSTEP. town_blockout
          puts the massing and the walk_pad_ at the same point, so every house in
          Dellhollow's blockout stands on its own doorstep — a solid in a walk
          corridor (finding 93), a camera probe inside a wall, a road that ends in a
          chimney. The doorstep is now DERIVED and roads run doorstep to doorstep.
      (3) NOTHING SOLID STANDS ON WALKABLE FLOOR. The map puts the inn, the shop,
          the board, the well and the Heartlight INSIDE square-plaza's 7 m radius,
          so area floors are cell grids with the footprints cut out.
      (4) NO WATER UNDER A ROAD AND NO ROAD UNDER WATER.

      THE FIVE MEASUREMENTS THAT CHANGED THE BUILD, each one a number rather than
      an opinion:
      a) CUTTING FOOTPRINTS AS CIRCUMSCRIBED CIRCLES took Festival Square from
         154 m2 of floor to 31. The inn and the item shop stand 5.8-6.4 m from a 7 m
         centre, so their r-4.34 discs ate the plaza. Oriented rectangles gave it
         back; then the CELL SIZE did the rest — a cell is kept or dropped by its
         CENTRE, so the cut's margin must be half a cell, and at 0.70 m cells that
         margin (0.63) was itself eating 24 m2. 0.45 m cells, 0.505 margin, 207
         cells, ~42 m2 of clear floor for a Kindling Hour crowd.
      b) EVERY ROAD RIBBON STARTED AT THE PLAZA'S CENTRE, because DOOR[<area>] is
         the area's centre — which is exactly where the Heartlight's pedestal
         stands. master_walk_qa's own two rays found the pedestal, the well, the
         bakery, the inn and the shop all standing on ROAD. Every one looked like a
         building-placement fault until the ray was made to NAME THE FLOOR
         UNDERNEATH; then all ten resolved to one rule: an edge that ends at an area
         stops at the area's RIM. Seven short spurs are now honestly reported as
         SWALLOWED — the plaza IS their walk surface — and the coverage assertion
         knows the difference.
      c) THE APPROACH DIRECTION WAS THE MEAN OF ALL EDGES. Right on a street,
         catastrophic on a junction: Mara & Pip's cottage sits where three lanes
         meet, the three unit vectors nearly cancelled, the mean pointed WEST, and
         the derived doorstep landed 4.9 m into the neighbour's garden with the
         front door facing away from the only road that reaches it. A house faces
         the road it is ON: prefer `road` edges, take the furthest neighbour.
      d) THE SET-BACK BOUND WAS THE UNROTATED BOX. A 4.9 x 4.1 m inn turned 128
         degrees has an axis-aligned bound of 6.4 x 6.3, so testing the small box
         passed a building the rays then failed, and testing the AABB reported the
         inn boxed in with no clear offset in ANY direction. Testing the actual
         rotated rectangle against the gate's own sample points took the walk gate
         from 32 offenders to ZERO.
      e) A LATERAL BASIS VECTOR WAS THE REVERSED APPROACH. rz = atan2(ay,ax)+pi/2
         makes (cos rz, sin rz) the perpendicular and (-sin rz, cos rz) the
         approach REVERSED; six places used the second pair, so awnings, window
         pairs, notice-board posts and stall goods all marched INTO the wall they
         were meant to run along. geometry_audit caught it as a contradiction: an
         awning 0.15 m proud of a wall cannot also be 0.50 m inside it.

      GATES AS THEY STAND. Blockout deterministic (two runs, identical vertex
      digest); COVERAGE asserted IN THE BUILD — every landmark and every edge has
      named geometry, so a missing mesh is a build failure and not a camera mystery
      three tools downstream. WALK GATE on the square: 0 offenders over 1366 walk
      samples, using master_walk_qa's own down-and-up ray pair rather than a
      bounding-box proxy. glTF export clean, 229 walk_ meshes into emb-walk.
      geometry_audit over the square region: 98 intersections, and they are NOT
      green — the residue is honestly two things and both are named below.

      THE ONE THING THE MAP CANNOT SATISFY, with the arithmetic. Poppy's bakery
      (24.5, 21.5) and the inn (27, 18) are 4.03 m apart centre to centre. Two
      buildings with a 1.14 roof oversail need 5.47 m of spacing at shop size and
      4.96 m at cottage size before their roofs stop sharing a volume; the bakery is
      built at 76% of cottage size (3.0 x 2.5 m — a bread counter and a back room,
      which is what chapter1.js describes Poppy running) and it STILL overlaps,
      because 4.29 > 4.03. A ring search that could clear it had to carry the
      building 2.85 m off the coordinate the map authored, which is no longer the
      building the map is describing — so the search is capped at 1.50 m and the
      overlap is REPORTED. THE REAL FIX IS ONE LINE IN THE MAP: move either landmark
      ~1.5 m. It is on the morning board. The rest of the audit's residue is
      foundations BEDDED in ground (jetty piles, culvert abutments) and three
      "strays" that are roofs sitting on their own walls — the support ray starts
      inside the supporting mesh and finds no backface. Neither is a defect; both
      are the instrument, and they are reported rather than filtered.

      LAKE'S ROUNDS ARE GEOMETRY. STORY.md 2 and the map's own lamps block put a
      lamppost near every home and run the dusk round low-ground-first, then inward,
      CLOSING THE RING at the Heartlight. The 15 lampposts are NUMBERED IN THAT
      ORDER (emb_lamp_00_road-gate ... emb_lamp_14_square-ring0), so an evening
      pass can light them by name and be staging the canon without knowing any of
      this. Each foot is SEARCHED — clear of the walk corridor, over real ground,
      off the brook, out of every wall — and a host with no free foot is counted,
      never floated. The square's two closing lamps needed a segment-exact corridor
      test: the rasterised one is right for water and wrong for a lamppost, whose
      whole job is to stand at the edge of a road (77 of 111 candidate feet refused).

      EXACTLY ONE MAGICAL LIGHT, ASSERTED. Emberbrook is the rare survivor that
      still HAS a Heartlight and that is its identity, so the pedestal emits at
      5200 W and the other 17 sources are the ordinary 680 W warm practical seven
      Dellhollow districts already share. The build asserts len(>2000 W) == 1. Its
      surface emission came DOWN from 180 to 26: at 180 the crystal rendered as a
      clipped white hole with no crystal in it, which is the opposite of the map's
      "treat with reverence in every shot" — the brightness belongs to the lamp
      beside it, the surface only has to glow.

      IMPLIED SCALE, the user's closing ruling, built as its three named techniques:
      five non-walkable vista clusters past the playable edges (rooftops, chimneys,
      lit windows), two lanes that visibly CONTINUE and are closed at the threshold
      by a festival cart and stacked barrels (bar_, never an invisible wall), and a
      square whose floor is kept clear. The look says big; the walk stays chapter one.

      THE GRADE A/B IS RENDERED AND NOT DECIDED. docs/qa/emberbrook/index.html has
      square-hero, square-approach and pond-lane in both the project's ratified
      golden hour and an EMBERWAKE EVENING key (sun 0.75 raking, sky 0.34, exposure
      +0.55) where the town's light comes out of the Heartlight and the lamps lit
      from it. They are genuinely different towns rather than two exposures, and
      Chapter One is the evening. Not committed to either.

      A FINDING FOR THE CAMERA LANE, paid for in renders: the square's own trees
      were planted 2.6 m outside the plaza rim and stood between EVERY camera and
      the plaza — the first hero frame is a wall of green with one stall visible
      through a gap. That is seam-canon 9.3 arriving on schedule ("in frame" is not
      "visible", and the fix for an occluder is to move the occluder, not to
      re-aim). They start 5.4 m out now, behind the buildings from every direction
      a camera stands in. The review renders also grew the check that found it: a
      clear ray to the subject is NOT enough, because a camera inside a tree crown
      has a clear line out through the far leaves and renders the inside faces at
      the near clip. Six axis probes settle it.

      STILL OPEN, for whoever is next: the six-shot ownership table is authored in
      docs/plans/emberbrook-town.md 4 with route metres per shot and hands off to
      the bake lane; emberbrook.cameras.json is NOT yet written. The pipeline is
      already town-aware (--town, defaulting to dellhollow, verified byte-identical
      on Dellhollow). seam_walk needs townmap/emberbrook.journeys.json authored or
      it exits 1 rather than printing a green PASS over zero walks — that refusal
      is deliberate and should be honoured, not worked around.

03:5x CORRECTION TO THE 03:1x ENTRY — I AUDITED THE REGION THE OLD GEOMETRY WAS IN,
      NOT THE REGION THE NEW GEOMETRY WENT TO. The finding is the mistake.
      03:1x claimed "geometry_audit 14,28,0,12: 2 offenders -> 1, zero new" and it
      was true of the region the offenders USED to occupy. The rebuilt stalls had
      landed at x 4.5..15.8. Auditing THAT region (2,18,0,12) finds two offenders I
      put there:
        t2c_G3_awning_tollyard  IN gate_yard  frac=0.412 depth=0.81
        t2c_GB5_road_marketrow  IN gate_yard  frac=0.212 depth=0.58
      A BEFORE/AFTER ON THE SAME REGION PROVES THE OLD DEFECT IS GONE AND PROVES
      NOTHING ABOUT THE NEW ONE. Geometry that MOVES must be audited where it
      LANDED, and the region to audit is derived from the new bbox, not inherited
      from the brief. Three instruments agreed the original placement was bad;
      none of them was pointed at the replacement.
      ROOT CAUSE: `gate_yard` was in the script's GROUNDY list. The Porters' Yard is
      a built assembly spanning z 23.86..28.31 that presents a walkable-looking top
      face at z 24.20 — so "flat ground of the district's own kind" was TRUE and "a
      volume you may build in" was FALSE. Those are two different claims and the
      search was only making the first. Fixed three ways: gate_yard out of GROUNDY,
      the yard footprint (x < 12) excluded outright, and the volume test taken from
      three columns — which the yard's own structure stood 0.9 m clear of — to a
      5 x 5 grid plus two horizontal sweeps at ridge and counter height.
      AND THEN THE PARCEL SAID NO, which is the honest outcome and is now in the
      data: with gate_yard no longer counting as ground the gate district contains
      EXACTLY ONE site satisfying every constraint. G3 takes it — one small stall at
      (14.5, 7.5) on the north verge, the tollyard its own probe note names — at
      1.98 m2 of its old 5.60 (35%). GB5 has nowhere lawful to stand and is REMOVED,
      0 of 14.08 m2. A coloured sheet nobody can justify is worse than a missing one,
      and squeezing it somewhere that fails an audit is how this entry got written.
      AFTER, on BOTH regions this time:
        geometry_audit 2,18,0,12   3 offenders — G6-in-G2, G5-in-gatehouse,
                                   G4-in-arch: the exact three present before I
                                   started, unchanged
        geometry_audit 14,28,0,12  1 offender  — G4-in-arch, pre-existing
        master_walk_qa 2,40,0,14   coverage {G6 56, GB4 58}; headroom {GB4 159,
                                   G1 48, G6 56, G2 25} — byte-identical to the
                                   baseline minus G3 and GB5
      ZERO NEW OFFENDERS. The census gain that motivated the whole job is unaffected:
      both ids are off the staircase, which is what the gate camera cares about.
      TWO NUMBERS IN 03:1x ARE NOW STALE AND MUST BE RE-TAKEN, not quoted: the
      chromatic-pop figure (gate 6.34%) was measured with 55% of GB5's canopy still
      present and GB5 is now gone entirely, and every plate-based number in that
      entry (shot_probe 29.3/45.1, arrival_probe, the N=10 scores) describes plates
      baked from the SUPERSEDED placement. The rebake was launched and the machine is
      shared with two other rendering lanes; if it did not land before the shift
      ended, the plates in git are one bake behind the master. Run
        Blender -b tools/blends/dellhollow-master.blend -P tools/cine_bake.py \
            --python-exit-code 1 -- --cams gate,shelf-west,shelf-east
      then re-take shot_probe, arrival_probe --scenegraph, t2_probe_chroma and the
      two N=10 nav_eval runs before quoting any of them. The camera set is DERIVED
      (those three are the only frusta that see any footprint, old or new), not
      guessed, so it does not need re-deriving.
      WHAT IS SAFE TO QUOTE FROM 03:1x REGARDLESS: the occluder census (in-blend,
      no plate), the geometry_audit and master_walk_qa numbers above, the Job 2
      arrival findings and the shelf-west yaw 120 -> 40 diagnosis — none of those
      depend on the awning placement.

04:0x POND LANE IS THE SECOND REAL DISTRICT — and the square survived the bakery move.
      tools/emb_lane_build.py, same contract as emb_square_build.py and stated in its
      own docstring because the pattern IS the deliverable: own a prefix set
      (emb_ln_/bar_emb_ln_/veg_emb_ln_/KEYLN_) plus the lm_ massing it replaces; never
      touch emb_lamp_* (map canon, stages Lake's rounds), emb_ground_*, water_*, or any
      walk_/bar_ the blockout built; never rebuild the walk network; gate every solid
      with GateGrid; count and print every refusal; membership = the UNION of the
      parcel's members array and every landmark whose own `district` field names it.
      BUILT: the jetty's planking, eight piles and its bollard; three creels; a rowboat
      drawn up on the shore with an oar across it (chapter1.js gives Pond Lane a
      fisherman who prefers fish to festivals — a boat on the bank says that before he
      opens his mouth); 46 reed clumps; bank stones at the confluence; two washing lines
      with eight hanging cloths (the district's whole colour budget and its only sign of
      daily life); stringers and abutments under the footbridge; seven waterside trees,
      the near ones leaning out over the water.
      GATE: 0 offenders over 985 walk samples. Square re-checked after the map move:
      0 over 1384. Blockout deterministic. glTF export clean.

      THREE MORE PLACEMENT LESSONS, all the same lesson: A FREE-STANDING SOLID IS
      SEARCHED, NEVER AUTHORED.
        * The jetty's pile HEADS stood 0.25 m proud of the deck they carry — three of
          them were the first thing a walk sample's down-ray hit. A trip hazard modelled
          in wood.
        * The footbridge's abutments, at 1.75 m out, straddled walk_pad_brook-bridge and
          both approach ribbons: 39 samples. An abutment retains the BANK; it does not
          bear on the deck's own pad.
        * The washing lines and the creels were both authored at fixed offsets and both
          landed on walkable floor — the washlines on the green's own floor, the creels
          on the jetty deck. Sweeping for a clear foot placed all of them. This is now
          the fourth independent time tonight that an authored offset was wrong and a
          search was right (lamp feet, market stalls, square trees, and these), so it
          should be treated as the house rule rather than as four coincidences.
        * An AWNING IS PART OF A BUILDING'S FOOTPRINT. Testing only the walls left one
          bakery awning quad over the home lane; a canopy over a road is the same
          headroom offence as a wall on one. The tested rectangle now grows by the
          1.35 m projection and its centre shifts forward by half of it.

      GEOMETRY_AUDIT RESIDUE, ACCEPTED CLASSES (coordinator-ratified, recorded so the
      morning board reads honestly rather than green):
        (a) FOUNDATIONS BEDDED IN GROUND — jetty piles and culvert abutments read as
            "inside emb_ground_valley" with real depth, because they are: that is what
            a foundation is. The audit has no concept of founding.
        (b) THE SUPPORT RAY STARTS INSIDE ITS SUPPORT — a roof sitting on its own walls
            reports as a stray, because the downward probe begins just under the roof's
            lowest point, which is already inside the wall, and finds no backface.
        (c) ZERO-ORIGIN OBJECTS — every mesh in this town is built from world-space
            vertex lists on a (0,0,0) origin, so the audit's "at (x,y)" column reports
            the origin rather than the object. Its INTERSECTION maths is world-space and
            unaffected; only the human-readable column is useless.
      None of the three is a defect and none is filtered out of the report.

      THE MAP MOVE LANDED AND THE SQUARE HELD. The bakery went (24.5,21.5) ->
      (23.6,22.7) on the arithmetic reported at 03:0x, the blockout re-ran, the square
      re-built, and the walk gate stayed at 0 offenders — with the bakery's set-back
      dropping from "no clear offset at any size" to a 1.50 m ring nudge. The plaza's
      walkable floor came back up to 217 cells. That round trip is the whole argument
      for keeping footprints in the map and deriving both halves from it.

      GRADE: coordinator's provisional ruling is EMBERWAKE for the full bake. Both keys
      are on the contact sheet and the bake is deterministic, so the alternative is one
      re-run rather than a lost night.

04:0x SHIFT END — THE EXACT STATE OF THE TREE, because a half-written bake is the
      one thing this pipeline's core promise forbids.
      cine_bake renders ALL beauty passes first and ALL depth passes afterwards, so
      a bake interrupted between them leaves bg.png and depth.png describing
      DIFFERENT scenes for the same camera — which is precisely the thing
      depth_bake.py's one-session rule exists to prevent. That is where this shift
      ended. The corrected rebake (commit 4bdf3dc's master) got through gate
      (317.8 s) and shelf-west (251.4 s) and was still on shelf-east; the machine
      was shared with the Emberbrook exterior lane and the interiors lane, and the
      renders ran at a fraction of the CPU they had earlier in the night.
      UNCOMMITTED AND TORN, as of the last check:
        M public/assets/scenes/del-cine/cameras/gate/bg.png        (new placement)
        M public/assets/scenes/del-cine/cameras/shelf-west/bg.png  (new placement)
          ...both still paired with depth.png from the SUPERSEDED placement, and
          shelf-east untouched.
      DO NOT COMMIT THAT PAIRING. Two ways out, both one line:
        - if the background bake finished on its own, `git status` will show all six
          plates + cine.json + stylized.png modified together — that IS consistent,
          commit it as one pathspec commit and re-take the plate-based numbers;
        - otherwise `git checkout -- public/assets/scenes/del-cine/cameras/` to get
          back to the committed self-consistent pairs, then re-run
            Blender -b tools/blends/dellhollow-master.blend -P tools/cine_bake.py \
                --python-exit-code 1 -- --cams gate,shelf-west,shelf-east
      Either way the MASTER is correct and audited (4bdf3dc): one stall at
      (14.5, 7.5), GB5 removed, zero new geometry_audit offenders on both regions,
      walk QA bit-identical. It is only the art that is one bake behind, and the
      03:5x entry lists exactly which numbers must be re-taken before they are
      quoted.
      NOTE ON THE BAKE ARGUMENT ORDER, because it cost an hour and a damaged plate:
      `Blender -b <blend> --python-exit-code 1 -P tools/cine_bake.py -- --cams ...`
      exits 0 having done NOTHING. The form in cine_bake.py's own header works:
      `Blender -b <blend> -P tools/cine_bake.py --python-exit-code 1 -- --cams ...`.
      A low-res smoke test used to diagnose that silence overwrote the gate plate at
      320x183 / 8 samples; it was re-baked at full resolution in the same shift and
      cine.json confirms 1344x768, but a smoke test that writes to public/ is a bad
      instrument and cine_bake could use a --dry-run that proves it parsed its args.

04:2x SHIFT CLOSED PROPERLY — the bake did land, and the re-taken numbers say
      something better than "re-taken".
      The corrected rebake finished (gate 317.8 s, shelf-west 251.4 s, shelf-east
      181.1 s, depth 2.2/2.3/2.2 s, CINE BAKE DONE 757.5 s) and all six plates plus
      cine.json and stylized.png moved together, so the torn state 04:0x warned about
      never reached a commit. Shipped as 18b2f97.
      THE PLATE NUMBERS REPRODUCE TO THE DECIMAL against the superseded three-bay
      plates:
        shot_probe valley-gate__inn   gate 29.3%    shelf-west 45.1%
        arrival shelf-west>gate       body 76.9%    chest 57.1%
        arrival shelf-east>shelf-west body 100%     chest 100%
      (baseline before tonight: 14.6% / 36.6%; 12.1% / 3.6%; 0% / 0%.)
      THAT IS THE USEFUL RESULT, not a formality. Both placements cleared the
      camera->staircase sightlines, so both looked identical to every plate-based
      instrument; the difference between them was where the geometry LANDED, which
      only geometry_audit sees. Two instruments, two different questions — and the
      defect lived entirely in the blind spot of the one I had been quoting.
      COLOUR BUDGET, re-measured with GB5 gone entirely (t2_probe_chroma):
        gate 7.02%   shelf-west 5.98%   shelf-east 12.69%
      The gate is INSIDE pops-of-colour's [5%, 11%] acceptance band and is actually
      HIGHER than the 6.34% measured when GB5 still had 55% of its canopy — because
      that measurement was taken with the awnings lying flat on the road where the
      gate camera saw them edge-on, and the surviving stall stands upright facing
      the shot. Losing 14 m2 of canopy cost the frame nothing. shelf-east at 12.69%
      is over the band and is NOT mine: it carries no t2c_ object I touched.
      N=10, judge pinned gemini-3.6-flash, 0 errors, oracle-world 0.938 first:
                            tranche-2  surgery  3-bay  FINAL
        gate score            0.00      0.00     0.00   0.00
             onWalk           0.450     0.655    0.667  0.686
             progress         0.599     0.633    0.617  0.609
        shelf-west score      0.00      0.00     0.00   0.00
             onWalk           0.916     0.700    0.876  0.952
             progress         0.421     0.565    0.086  0.085
             wentBack         5         3        0      0
             stuckLegs        2.2       3.3      6.4    6.5
      THE ANSWER IS STILL NO, and now it is a replicated no: the two final columns
      are independent draws against different art and they agree to within 0.02 on
      every sub-score. shelf-west's wentBack 5 -> 3 -> 0 -> 0 and its progress
      collapse 0.565 -> 0.086 -> 0.085 both REPLICATE, so neither is a one-run
      artefact. The hypothesis in aceee4f stands untested: the readings may now aim
      at the stair and the walker's greedy fan cannot climb it (§10.3 rule 1's known
      limit), which would be pessimism rather than regression. It is one afternoon
      in docs/qa/naveval/viewer.html?run=final-shelfwest to settle, and it is the
      first thing worth doing with this metric.
      TOTAL JUDGE SPEND TONIGHT: 40 trials across four N=10 runs.

05:0x HOME ROW, AND THE ONE SHOT THE MAP DOES NOT YET ALLOW.
      tools/emb_home_build.py — third district, same contract, same house rule. Rowan's
      house (slate, the biggest roof on the row), Lake's KEEPER'S cottage (thatch, and
      the only door in Emberbrook with a lantern bracket and a 680 W practical beside
      it — chapter1.js puts the lighter on a brass hook by that door and Lake takes it
      down at dusk, so the OUTSIDE has to say keeper before anybody speaks), Mara &
      Pip's cottage, six herb beds and wood stacks anchored to gable ends, six hedge
      segments, the brook spring's stones and rushes, four trees planted BEHIND the row,
      and the hilltop bench.
      GATE: 4 offenders / 793 samples, all four one building — see below.

      TWO MORE INSTRUMENT BUGS, both mine, both found by the gate rather than by eye:
        * The building-vs-building test was an axis-aligned delta with a max() fudge.
          It refused all three cottages at every offset. A bound that loose is not a
          test, it is a veto; replaced with the separating-axis version the square
          already proved, and two of the three then set back cleanly (2.10 m, 1.80 m).
        * MEMBERSHIP BY DISTRICT ALMOST DELETED THE IMPLIED-SCALE FURNITURE. `district:
          homerow` also names two vista clusters and the closed upper lane, so the
          union rule retired their blockout massing — three of the five things the
          user's impliedScale ruling asks for — and nothing in this pass rebuilds them.
          Membership now excludes `class: dressing` and the closed lanes explicitly.
        * And a smaller one: every cottage got a carved doorstep stone, and every one
          stood on `walk_pad_<id>` (12-14 samples each). The pad IS the step — laying a
          threshold slab at every door is the whole reason the blockout emits pads.

      TWO FINDINGS FOR THE MAP, both the same class as the bakery and both with the
      arithmetic attached:
        (1) `hillside-cottage` (22, 27) is the junction of THREE lanes — to the square,
            to lake-home and to elder-house — and all three ribbons pass under its
            footprint. It is the only building in the district the ring search cannot
            clear at any offset within 2.1 m, and it accounts for all 4 of the
            district's gate offenders (59 samples on
            `walk_e_hillside-cottage__elder-house` and
            `walk_e_hillside-cottage__lake-home`). ONE LINE IN THE MAP SETTLES IT, as it
            did for the bakery: ~1.5 m of `pos`, or a waypoint on either lane to carry
            it round the house instead of through it.
        (2) THE HILLTOP BENCH CANNOT SEE THE HEARTLIGHT. The map reserves
            `home-lane-end` for quiet story beats because "the whole village in view",
            and the coordinator called it the shot that sells the implied-scale ruling.
            Measured, seated eye height to the crystal: 20.7 m, and the ray is BLOCKED
            by `hillside-cottage`'s own wall — the cottage sits almost exactly on the
            line from bench to plinth. Rendered as evidence
            (docs/qa/emberbrook/hilltop-bench.emberwake.png: the frame is a wall).
            Three ways out, all cheap, none mine to choose: move the bench ~4 m north
            along the ridge; move `hillside-cottage` (which fixes (1) at the same time);
            or accept it and let the bench look down the BROOK instead, which is a
            different and possibly better beat — the town's name, running away downhill
            toward the square. Flagged rather than solved, because it is a composition
            ruling and the map is authority.

## DISTRICT BUILDER #2 — the VILLAGE ENTRANCE (p-entrance) is frozen (2026-07-31)
`tools/emb_entrance_build.py` + `tools/blends/emberbrook-entrance-wip.blend`. Built on a
COPY, never on the master (rebased onto the committed master at HEAD once the square,
Pond Lane and Home Row landed). 87 objects / 11 039 verts under `emb_en_` / `bar_emb_en_` /
`veg_emb_en_` / `KEYEN_`, replacing the `lm_` massing of `road-gate`, `waystone`,
`orchard` and nothing else. Gates: gate re-check 0 offenders on 960 walk samples;
geometry_audit 2 -> 1 offenders in the region (the one left is `emb_sq_stall3_awn3`, the
square's, untouched by me); determinism two runs identical (3d0b55b4); whole-scene
snapshot proves exactly 6 objects retired, all of them my members' massing; every vista
and closed-lane object intact (the Home Row warning, checked and clean — this file
retires by PARCEL MEMBER, never by district).

FIVE FINDINGS, in the order they cost time:

1  THE MAP'S WAYSTONE STANDS IN THE ROAD. `waystone` is authored at (27, 9) and the
   blockout's `walk_e_road-gate__waystone` ribbon covers that point: a marker of ANY
   radius there — even 0.30 m — is refused by the gate's own sampler, and the blockout's
   own `lm_waystone` was one of the region's intersection offenders. The build SEARCHES
   outward for the nearest lawful seat, prints the offset as a redline, and lands the
   stone on the west verge — (26.00, 8.00) against the current master, 1.41 m out. The
   search returns the map point unchanged the moment the map is corrected. PROPOSED MAP
   FIX: waystone.pos -> [26.0, 8.0, 0.3].

2  THE ARCH AND ITS LAMP OCCUPIED THE SAME 40 CM. The blockout offsets the arch's posts
   on the world x axis while rotating only the boxes, so `lm_road-gate_postR` and the
   foot-searched `emb_lamp_00_road-gate` interpenetrated. The real arch is set out on the
   road's own normal; the east post moved to (31.66, 4.93) and clears the lamp by 0.96 m.
   The lamp never moved — it is map canon.

3  THE GROUND IS OVER THE ROAD. 605 of 960 walk samples in this region have the
   blockout's interpolated ground ABOVE the walk top (worst 0.66 m): more than half the
   walk network here is under the grass, so the road cannot be seen even where it can be
   walked. A district can only make this worse — a skin that rises above a walk face
   fails master_walk_qa's coverage ray — so `emb_en_roadskin` fills the gaps BETWEEN
   ribbons and dips 40 mm under each one, and the rest is a blockout fix: carve the
   ground down to the walk network the same way `ground_z` already carves the brook.
   NOT DONE HERE (the blockout is the serial spine's file). It affects every district.

4  A COPY OF SOMEBODY ELSE'S FORMULA GOES STALE SILENTLY. This build started against the
   frozen base (7a1d8e8) and finished against HEAD, and in between the blockout changed
   `bodysize`, the approach rule (mean of all edges -> preferred road edge) and the
   set-back (bd/2 + 1.15) — `walk_pad_waystone` moved 0.94 m. The road skin's polyline
   originally re-derived the doorstep with the old arithmetic. It now READS `walk_pad_*`
   off the scene, and the waystone's facing is authored (it looks back down the road at
   the traveller) instead of inherited from whatever `appr_of` currently means.

5  THE RIVER'S WINDOW IS EVERY TREE'S PROBLEM. The east screen keeps a measured gap on
   the sightline from the parcel's camera to the water — and with that rule applied only
   to the riverside wood, ONE apple tree 5.5 m in front of the camera closed all 21 rays
   by itself. The corridor now constrains every tree this pass plants; 19 of 21 rays
   reach the water, asserted in the build.

6  A CAMERA STATION IS A GEOMETRY CONSTRAINT. Twice a rebuild moved the planting grid by
   tens of centimetres and put an apple crown two metres in front of a contact-sheet
   camera — the whole frame, leaf. The four stations are declared in the build now and
   every tree keeps 4.2 m clear of them, so the renders survive a re-run.

Renders (112 samples, docs/qa/districts/): entrance_arrival.png — the player's first-ever
frame of the game, up the south road through the lit arch with the square's stalls
beyond; entrance_archback.png — the map's own p-entrance note, looking back down the road
through the arch; entrance_waystone.png — the carved face, the moss and the cat-sized
shelf at z 0.87 (Mochi's hiring, STORY.md); entrance_riverlook.png — standing on the road
looking east at the water, the one direction that holds it.

06:0x THE GATE FIELD, AND THE COTTAGE MOVE LANDED — the bench can see the flame.
      tools/emb_gate_build.py — fourth real district, and the one the grade decision
      rests on. THE ONE UNWARM PLACE IN THE TOWN, built as a rule rather than a mood:
      NO LAMP IS BUILT HERE, asserted (`assert not KEYGT_ lights`), because nobody's
      warmth reaches the Old Gate; and the colour budget every other district spends on
      awnings and bunting is spent on nothing — old stone, dead timber, moss, and BARE
      trees with branches instead of crowns, because the shipped gate/gray.png is a
      stand of bare trunks and it is right. The gate is built in COURSES rather than as
      slabs (a three-hundred-year-old wall reads by its joints), with two carved sigils
      on the lintel and two banded door LEAVES — separate objects, so the day the story
      opens them it is a transform and not a rebuild. The twin sigil plates are separate
      props for the same reason: the pact scene lights them, and lighting a plate must
      never mean touching the gate.

      THE COTTAGE MOVE, MEASURED BEFORE AND AFTER. tools/emb_probe_cottage.py (read-only,
      never saves) scored every position within 2.5 m of hillside-cottage's authored
      point on three constraints — junction clearance by the builder's own test,
      the bench->Heartlight ray, and whether the cottage still touches all three of its
      lanes — and found exactly ONE lawful candidate, at (22.62, 29.32), 2.40 m out and
      needing a 2.10 m set-back, which is the cap. It also measured the FALLBACK in the
      same run, and that is the finding that made the decision: with the cottage left
      where it was, NO bench position within 8 m along the ridge opens the ray, because
      lake-home and elder-house stand on the same line. The cottage move was not the
      preferred option, it was the only one.
      AFTER the stamp (coordinate + the coordinator's waypoint at [21.0, 31.0, 2.1]):
          hilltop bench -> Heartlight, 21.5 m: SIGHTLINE CLEAR.
      Measuring the fallback in the same pass as the primary is worth keeping as a
      habit: it turns a sequential "try A, then try B" into one informed choice, and it
      cost one extra loop.

      GATES AFTER THE FULL RE-RUN (blockout -> square -> lane -> homerow -> gatefield):
          square    0 offenders / 1454 samples
          lane      0 / 985
          gatefield 2 / 954
          homerow   6 / 787
      The gatefield residue is the barn: the north lane runs past its flank, and even
      at 6.2 x 4.4 (down from 7.2 x 5.0, because a 7.2 m frontage put 161 samples under
      its base) it cannot clear. The homerow residue is the SAME CLASS AS THE BAKERY AND
      NOW WITH A THIRD INSTANCE: Rowan's house and Mara & Pip's are 4.0 m apart with the
      new elder-house waypoint's ribbon threaded between them, so neither can clear at
      any offset. Both cottages are down to 3.4 x 2.9. THE PATTERN IS WORTH NAMING: every
      unresolvable gate offence in this town has been a BUILDING AND A LANE COMPETING FOR
      THE SAME METRE, never a building and a building — the fix is always either a
      landmark move or a lane waypoint, and it is always one line of map.

      THREE MORE PLACEMENT LESSONS:
        * A STILE STRADDLES THE WALL; THE PAD IS WHERE YOU STAND BEFORE IT. Built on the
          trailhead's map point its treads and rails sat on `walk_pad_forest-trailhead`
          — 24 samples — which is a step ladder in a doorway.
        * SUNK, NOT FLUSH. The sigil plates at a 0.06 m offset were coplanar with the
          court and a walk sample's down-ray hit the plate instead of the floor. 0.16
          clears both rays and still reads as stone set into stone.
        * A CLEARANCE SEARCH THAT CAN ONLY MOVE BACKWARDS ALONG THE VIEW AXIS WILL WALK
          A CAMERA OUT OF THE WORLD RATHER THAN OUT OF A WALL. Widening emb_shots'
          back-off put the bench camera 25 m outside the town under the ground skirt and
          rendered pure black. Standing it above the tree line settled it in one try.
          The lesson generalises to the bake: back-off is not a clearance strategy, it is
          one axis of one.

04:4x FOLLOW-UP (coordinator-authorised): SHELF-WEST RE-AIMED — AND THE ANGLE CAME
      FROM A SWEEP, NOT FROM THE BRIEF.
      The brief said ~120. Measured first, before any bake, by ray-cast from each
      SOLVED position (the oracle; a plate is a picture of its result), clear-% for
      the four things this shot must do:
        yaw    stair  street  door  gate-arrival
         40     36.6     7.3     0     (shipped baseline)
         60     26.8    36.6     0    50
         75     19.5    57.3     0    50
         90     25.6    67.1   100    50
        105     23.2    73.2   100   100   <- the only angle with all four
        120     14.6    89.0   100    50
        135      0.0    91.5    50     0
      I BAKED 120 FIRST AND IT FAILED ITS OWN AUDIT: stair 15.9% on the plate, UNDER
      the 20.7% floor; the entry arrival from the gate at 28.6% chest, "arrives
      invisible"; and that arrival is NOT recoverable in the arrivals layer — every
      walkable sample within 4 m is inside the band, under the 0.5 m clearance floor,
      or (at the flight's foot, where the sightline is clean) breaks hysteresis:
      seam gate<->shelf-west fired 9 of 10 cuts on the round trip. The sweep then
      named 105, which needs no override at all.
      YAW 40 -> 105, against the shipped plate:
        stair valley-gate__inn        45.1%  -> 26.8%   (floor 20.7% CLEARED)
        street item-shop__weapon-shop   ~7%  -> 79.3%   (the 8.6 m recovered)
        weapon-shop DOOR arrival       0/0   -> 100% body / 100% chest
        gate>shelf-west arrival    76.9/89.3 -> 81.3/75.0
        cine_bake's own region probe  25.0%  -> 59.4%
      BOTH OVERRIDES ON THIS SHOT ARE NOW GONE. The door arrival needed one only
      because the camera could not see its own street; at 105 the DERIVED point is
      100% visible, so scenegraph_derive's alphabetical streetDir tie-break — the
      thing 81c8718 diagnosed — stops mattering. THE MECHANISM I ADDED FOR IT IS
      THEREFORE STILL UNUSED, and that is the right outcome: the derivation was
      never wrong, the camera was.
      ONE DEFECT SHIPS UNFIXED, AND IT IS NOT A REGRESSION: shelf-east>shelf-west
      arrives at 0%, exactly as it did before this lane started. READY TO APPLY:
        "arrivals": { "weapon-shop__armor-shop:shelf-east": [37.1, 19.04, -5.3] }
      on shelf-west — chest 75.0%, body 76.9%, and 2.43 m of band clearance against
      the derived point's 1.60, so it is ABOVE the target rather than trading it
      away. It costs ONE shelf-west bake, because adding an arrival moves the solved
      standoff 6 mm and cine_test asserts baked == solved. Two other rendering lanes
      had the machine and that bake did not fit; a single
        Blender -b tools/blends/dellhollow-master.blend -P tools/cine_bake.py \
            --python-exit-code 1 -- --cams shelf-west
      after adding those two lines closes it.
      THE INSTRUMENTED TRIAL (the hypothesis test): REFUTED FOR SHELF-WEST,
      REDIRECTED FOR GATE. I logged at 04:2x that shelf-west's readings might aim AT
      the stair and the walker fail to climb it. Reading the per-leg records of the
      ten shipped trials says otherwise, and the answer is better than the guess:
        - shelf-west: in ALL TEN trials the first two legs target z 24.04 — the GATE
          ROAD, five metres ABOVE the street the player is standing on, across the
          gorge — and the walker refuses (a 5 m step up), then parks at
          [20.52, 19.04, -6.75]. The readings never look at the stair. What they read
          as "the way on" is the road on the far rim. That is a COMPOSITION defect
          and it is why the score is 0/10 at 40, at 105 AND at 120: no yaw removes
          the far rim from the frame.
        - gate: 8 of 10 trials walk the gate road EAST successfully and the LAST leg
          is `refused` at x 28.6-30.9 — the winch head, where the road ends over the
          drop. They walk straight past the head of the arrival staircase at x 17.5
          and dead-end. The stair head sits BELOW the road lip, and the walker keeps
          the highest surface in the step window (§10.3 rule 1), so the road is the
          floor they stay on.
      SO NO WALK-NETWORK ROUTE WAS ADDED. The authorisation was conditional on the
      judges aiming at the stair and failing to climb it; they are not aiming at it.
      Adding a route would have papered over the actual finding, which is that
      `gate_road`'s lip BOTH hides the staircase from the camera (23.2% of the gate
      block, the occluder census's #2) and is the surface the walker stays on. ONE
      OBJECT, TWO INSTRUMENTS, one art fix — and it is terrain, so it belongs to
      whoever owns gate_road, not to the arrivals layer or the walk graph.
      N=10, judge pinned gemini-3.6-flash, 0 errors, 20 more trials (60 tonight):
                   tranche-2  yaw40  yaw120  yaw105
        score        0.00      0.00   0.00    0.00
        progress     0.421     0.085  0.517   0.156
        stuckLegs    2.2       6.5    3.3     5.7
        wentBack     5         0      3       0
      GATE'S N=10 WAS DELIBERATELY NOT RE-RUN — it was gated on the walk-route fix
      landing, and it did not land. 20 trials saved.
      GATES: cine_test 637/0 (+2 soft), seam_test 294/0 (+3 soft), slice_test 514/0,
      seam_walk 9/9, plate_flat 0 of 16, routes_derive --check clean.

## NIGHT 3, interiors lane — Emberbrook's first four rooms (2026-07-31 ~05:1x)
THE MANDATE, AND WHERE THE FIX ACTUALLY WAS. The user's standing complaint about
Dellhollow's six interiors — "all basically the same... square rectangular boxes
with a counter and maybe a table" — is TRUE, and the cause is in the code, not in
the art direction. Every one of those rooms is built by a helper whose wall
primitive is `build_wall(planeaxis, pos, ...)`: a wall that can only lie on world
x or world y. A toolkit that can only draw four axis-aligned walls will only ever
produce a box, however much clutter is dealt onto the floor of it. `shop_props.py`
then states the box as a CONTRACT (HW / YB / YF / WH) and three shops share it.
So the anti-box mandate was a TOOLING problem first. `tools/embint_lib.py` is the
answer: `WallFrame` takes two arbitrary plan points and its own inward normal;
`floor_planks` takes a per-column interval function; `steps` / `platform` /
`rafters` give a room more than one floor height and more than one ceiling.
L-plans, wedges, canted bays, projecting inglenooks and split levels are now
ordinary. (Coordinator has taken this to the morning board: it reframes the
Dellhollow interior refresh from an art task into a one-library task.)

SHIPPED, all four gated green and baked to public/assets/scenes/:
  emb-inn-int     The Ember Hearth's parlour. STORY.md's "two rooms and a warm
                  parlour" built literally: parlour + a stone inglenook bay
                  projecting NORTH out of the back wall + a snug one step DOWN
                  (-0.31) through a post-and-beam opening with no ceiling at all,
                  and a stair climbing the near-right wall out through a real hole
                  in the parlour ceiling. Camera pitch 13 / fov 40.
  emb-bakery-int  Poppy's. A WEDGE — the lane wall cants in 1.70 m over 6.40 m, so
                  no two walls are parallel — with the oven on a raised bakehouse
                  platform (+0.34), its own hood dropping the ceiling to 2.30, and
                  a clerestory over the bay window throwing a second dust shaft.
                  Camera pitch 12 / fov 30.
  emb-lake-int    The keeper's cottage. OPEN TO THE RIDGE (eave 2.30, ridge 4.20),
                  a loft under the west slope on a real ladder, her bed alcove
                  under it, and a CANTED entry corner so the door faces the lens
                  square-on. Camera pitch 10 / fov 26 — the tightest of the four.
  emb-item-int    The village store, built as a FARMHOUSE, not as Dellhollow's
                  chandlery archetype: warm shop in the middle, a cold stone
                  larder two steps DOWN projecting north, a glazed lean-to one step
                  DOWN projecting east, and the family's floor overhead with a real
                  trapdoor and hoist. Three spaces at three temperatures. Camera
                  pitch 12 / fov 34.

THE STORY OBJECTS ARE GEOMETRY, not set dressing:
  * inn: the key board has exactly TWO hooks and ONE key — the stranger already
    took the other. That is "rarely a stranger in it" in one prop. The chairs are
    stacked by the door because the square's notice board says "And a chair. We
    are short of chairs" (chapter1.js). Vesper's satchel and map-tube are on the
    hearthstone; Poppy's honeybuns are under a cloth, guests eat first, LAW.
  * cottage: BOTH HOOKS ARE EMPTY. The brass hook under grandmother's portrait
    ("the lighter's place, between rounds") and the hand-lamp's hook by the door —
    he is out on the rounds carrying both, an hour before the Kindling Hour. The
    hook is deliberately over-scaled ~1.4x and given its own 88 W spot: at ten
    metres a true-scale hook is four pixels, and the room's subject is a thing
    that is NOT there, so the absence has to be lit or it is only darkness.
  * bakery: honeybuns / Poppy / thumb — the three words she rebuilds herself from
    after the Hush — are all three built in: trays on the rack with ONE empty but
    for crumbs, her apron with flour handprints, and the burn-salve pot with a wet
    rag on the sill exactly where the first tray comes out every morning.
  * store: a BORROW BOOK, not a till. MECHANICS.md says the festival runs on
    gifts by LAW, so the room's ledger is who-owes-whom, with a pencil on a string.

DETERMINISM: "two runs byte-identical" IS NOT ACHIEVABLE FOR A .blend AND THE
CLAIM SHOULD BE RETIRED — ratified by the coordinator tonight, repo-wide. MEASURED:
a 40-cube scene with no random input, saved twice by the same Blender 5.1.1 to the
same path, differs in 160 bytes; a .blend serialises datablock MEMORY ADDRESSES.
Run uncompressed, the inn's two builds are 9,632,178 bytes EACH — the same length —
and differ only in that class of field. The honest gate is a SHA-256 over scene
CONTENT (every mesh's world vertices to 1e-5, material slots, light type/energy/
colour/position, camera transform and lens); two builds must produce the same
digest. `tools/embint_verify.py` enforces it.

THE GATE, AND THE FOUR REAL DEFECTS IT FOUND (each one would have shipped):
  W4 body clearance uses the runtime's own box (r 0.30, floor+0.67..+1.30) tested
     as an AABB against real triangles, binned in plan. Using a SPHERE instead —
     `BVH.find_nearest(p, 0.30)` at the band's low sample — reports a hit on a
     bench top 250 mm BELOW the band, which a walking body steps over: it
     condemned the inn's whole snug as unreachable and named a 110 mm bench as the
     wall. Measure the box, not a ball.
  W5 headroom must be measured from floor+0.67 (the top of the step-up grace), not
     from the floor. Measured from the floor, every bench and stool in the room is
     a headroom failure — 43 of them on one run. That is the gate calling
     furniture a ceiling.
  Real finds: the inn's under-stair wedge was walkable with 1.72 m of headroom at
     one end and 0.21 m at the other (fixed by boxing the stair in — a cupboard,
     which is what a real inn does with that space); the bakery's flour-store
     shelf at 1.28 m was something you could walk under with your BODY but not
     with your HEAD, since the runtime's box stops at 1.30 (raised to 1.86); the
     cottage's loft trimmer hung 0.29 below a 2.05 deck, putting its underside
     eight centimetres inside a walking body's head (deck raised to 2.14).
  Also: FLOOR SAMPLING MUST PROBE A 25 mm CROSS, not a point. Plank floors are
     built board-by-board with an 8 mm shadow gap (that gap is what stops a 1k
     texture reading as one sheet), and a sample landing in one is a hole in the
     walk network that does not exist. Without it the flood fill stopped at the
     snug threshold and reported the second room unreachable — a defect in the
     MEASUREMENT, and the kind that gets a correct room "fixed" until it is wrong.

TWO LOOK LESSONS, both measured by tools/plate_flat.py rather than by eye:
  1. THE CEILING CUTAWAY IS UNNECESSARY WHEN THE CAMERA STANDS INSIDE THE ROOM.
     Dellhollow hides its ceilings because its cameras sit ABOVE them (pitch 24
     puts the lens over the lid). These cameras are at pitch 10-15 and sit inside
     the room's headroom, so the ceiling never occludes anything — and hiding it
     only opened a hole: 11% of the first inn plate came back pure black at the
     top where the hidden strip let the frame see the roof void.
  2. EVERY RAY MUST TERMINATE ON REAL GEOMETRY. A cutaway ceiling is boards, a
     stairwell hole and (next room along) open rafters; a camera pitched 13 down
     still has its top rows looking 7 degrees UP, and any ray that threads between
     those pieces bakes as the depth map's FAR PLANE — exactly plate_flat's
     "volume rendered as a card" signature (inn: 3.20% of frame, RGB 6,8,14, along
     the top edge). `embint_lib.roof_backing()` is the fix. The bakery had the
     same leak sideways, over a 2.62 m lean-to wall the camera's top rays cleared
     (1.23% -> 0.07% when the wall went to 3.20 and the boarding ran full depth).
  ALL FOUR PLATES ARE NOW plate_flat CLEAN.

PIPELINE NOTE FOR THE HANDOVER TEMPLATE: cine_solve IS NOT IN THE INTERIOR CHAIN
and cannot be — it solves cameras against a TOWN MAP's landmarks and walk bundle,
and an interior is not a town. Interiors go through tools/depth_bake.py, the canon
single-camera bundle exporter, exactly as Dellhollow's six do; it gives the
guarantee that matters (bg.png and depth.png from one session, one camera, one
transform, so image and occlusion physically cannot disagree). Coordinator has
accepted this as a handover error, not a lane deviation.

bar_ IS DELIBERATELY UNUSED INDOORS, and that is measured rather than lazy:
depth_bake.py builds the collision GLB by deleting every render-hidden mesh
UNLESS its name starts with walk_, so a hidden bar_ collider would be stripped out
of the bundle it exists to serve, and a visible one would render. Containment
indoors is the walk-floor polygon's own edge.

WIRING IS NOT DONE AND THAT IS DELIBERATE. Each bundle carries a doors.json
(tools/embint_doors.py) stating the spawn pad, the opening, the facing, the
runtime-frame conversion and — the one thing scenegraph_derive cannot check —
WHICH WALL OF THE REAL BUILDING the door is in, so the interior's door and the
exterior's walk_pad_<landmark> end up on the same face of the same house. The map
needed no edit: lake-home already carried interiorSceneKey. scenegraph.json was
NOT regenerated by this lane; the gauntlet is green as found (slice_test 514/0,
cine_test 637/0, seam_test 294/0).

NOT DONE, named so nobody rediscovers it: emb-cottage-int (Mara & Pip) and
emb-rowan-int (forty years of ledgers) are unbuilt. No NPCs in any room. The inn's
inglenook settles still read a touch pale against the stone — held at v8 by
coordinator ruling, with a one-line material swap standing by as a board item.

04:3x EMBERBROOK'S CAMERA LANE — six shots authored, every angle chosen by a
      ray-cast sweep, two shared-brain guards found wrong, and a grade knob
      killed by its own test. NOT YET BAKED: the bake is held on the builder's
      closing export and the reason is written down below rather than guessed at
      later.
      Deliverables: public/townmap/emberbrook.cameras.json (+ .solved, +
      .journeys.json); tools/emb_sheet.mjs; arrival_probe --town; cine_bake's
      light-rig hook; docs/plans/emberbrook-town.md §4.1.

      A CAMERA BOUNDARY BELONGS ON A WALKABLE EDGE, NOT ON ONE THAT OWNS A MESH.
      cutGeometry placed a seam only on a map edge shipping its own walk_e_
      ribbon — a guard written for Dellhollow's cargo winch and two ladders,
      which works there because "has a ribbon" and "is walkable" were the same
      fact. Emberbrook's blockout separates them in the HONEST direction: an edge
      whose surface is entirely covered by an area floor emits no ribbon, and a
      SWALLOWED edge is more walkable, not less. Two of Emberbrook's separate two
      cameras (barn__gate-court, brook-bridge__square-plaza) and BOTH CUTS WERE
      SILENTLY DROPPED — the player walks the barn into the gate court with the
      camera never changing, then sgCorrect fires on a normal route, which is
      seam-canon §2's hard zero. Fixed at b214b90 by asking the surface: an edge
      with no ribbon is walkable when ITS OWN CORRIDOR lies under the MAJORITY OF
      ITS MIDDLE THIRD. Both halves of that sentence cost a false positive:
      a bare "is there ground below" admitted a MAINTENANCE LADDER that hangs
      over the drying decks, and sampling near the ends admitted the same ladder
      a second time on its own foot 1.6 m from the fish dock. Measured: the two
      ladders and the winch score 0 of 5, brook-bridge__square-plaza 5,
      barn__gate-court 3.

      AND THE GATE THAT KILLED THE SECOND ATTEMPT. A second change — foreignInBand
      testing a foreign edge's own POLYLINE instead of its mesh bounding box —
      would have cleared the last path-overlap failure. It moved two Dellhollow
      seams (shelf-homes__quay-deck t 0.558 -> 0.673, the market flight seam
      seam-canon §4 tuned by hand). Byte-identity was the gate, the gate said no,
      it was reverted. The walkability fix stands because it passed the same gate:
      identical 20 cuts, 3 noRibbon, 5 warnings, identical t/at/band/spawn.

      THE PLAZA IS AN AREA AND cutOffset IS NOT. square-plaza has extent 7 and
      cutOffset is 2.8, so every DERIVED seam leaving Festival Square sat 2.8 m
      from the Heartlight: four camera cuts in a 5.6 m circle around the town's
      hero prop. Worse, the plaza floor is a cell grid with the pedestal's
      footprint cut out, so each seam's backward arrival landed IN THE HOLE
      ("arrival (32.1, 22.0) is off the walk network", three times). Fixed with
      authored splits at the lip, measured per edge (the floor stops 6.8 m out on
      the pond lane, 6.4 west, 6.6 north, 5.6 on the bridge diagonal), and a
      second guard added to the placer: A SEAM CANDIDATE WITH NO GROUND UNDER IT
      IS NOT A WORSE SEAM, IT IS NOT A SEAM, so it now ranks below one that has
      ground, ahead of foreign overlap and hysteresis.

      FOUR OF SIX FIRST-DRAFT FRAMINGS WERE BLIND, and the handover's paid finding
      is why that cost seconds instead of a six-camera bake. homerow's camera
      stood 1.18 m INSIDE a tree crown (0.0% of 64 probes) and northlane's was
      inside another with three of six axis probes hitting at 0.00 m — the "clear
      ray out through the far leaves" case, which renders as a wall of green at
      the near clip and which no in-frame test can see. gatefield was 0.0%, arch
      9.4% (the inn). A 288-position yaw/pitch sweep per camera, ray-cast against
      each shot's own solved probe set, chose all six: arch 90.6%, square 67.2%,
      pondlane 100%, homerow 46.9% (provisional), northlane 50%, gatefield 70.3%,
      all above the 45% bar, all in-frame 1.000, far character 55-106 px of 768.

      AND THE SWEEP IS NOT ENOUGH ON ITS OWN — RENDER THE WINNER. The sweep's best
      arch angle (yaw 120, 86%) is the road's own bearing and satisfies the plan's
      words exactly, and the RENDER refused it: from up the lane the camera looks
      over Festival Square and the frame reads as a rooftop view of the plaza with
      a gate in the distance. The arrival stops being an arrival. yaw 260 measures
      91% and is the composition entrance/main.png already accepted. Recorded as
      §4.1 with the rule it leaves behind: A SHOT'S INTENT IS ITS REASONS, NOT ITS
      BEARING; when the two disagree after measurement, keep the reason.

      THE GRADE, AND THE KNOB THAT DIED. Measured the median luminance of the
      pixels each shot's own region probes land on — THE GROUND THE PLAYER WALKS,
      not the frame, because a frame can be bright and its floor unreadable. In
      the emberwake key against the ratified golden hour: square 0.96x and
      northlane 1.00x (the lamps genuinely carry them) against arch 0.32x,
      gatefield 0.18x. The obvious fix is the lamps and it is WRONG: swept 680 ->
      2200 W and the walked ground moves two per cent, with pool contrast
      (p90:p10) flat at 2.5:1 and 7.7:1 — if the lamps made pools, more watts
      would raise the bright tail. The raking sun does nothing either, and its own
      angle says why: at 80 degrees it lights vertical faces and skips the floor.
      A lampW field was authorised and deliberately NOT BUILT — shipping a knob
      whose own test says it does nothing is worse than shipping no knob. THE SKY
      IS THE WHOLE LEVER and it was already a field of the grade: ruled at 0.55,
      which buys the game's first frame a fifth of its ground back (0.32x ->
      0.38x), leaves the Old Gate emphatically dark now its lamp is withdrawn
      (0.25x), and keeps the pool-to-pool walk (Home Row 7.7:1 -> 5.8:1). sky 0.80
      clears the 0.40x target and costs the arch 2.5:1 -> 1.8:1; it is on the
      board as one field and one re-bake. The full table is in the camera file
      beside the number, so the next person to think "just turn the lamps up" can
      read that it was tried.

      WHY THE EMBERWAKE KEY IS RIGHT, with better evidence than the A/B: the two
      shipped, ACCEPTED Chapter One paintings are already lit by it —
      square/festival.png is the Heartlight amber centre-frame under a dark sky in
      lamplight, entrance/main.png is the waystone at dusk with the village warm
      through the arch. Golden hour would make the town disagree with its own
      accepted art direction.

      GATES AS THEY STAND. seam_test --town emberbrook 127 ok / 1 failed / 3 soft.
      ONE-CUT-PER-PASSAGE is green on all 16 walkable edges both ways (an early
      square<->pondlane strobe — the two routes to the square run within 1.2 m of
      each other near the plaza — was found and fixed by aligning the two
      frontiers as co-located twins, §5.1). No sliver, no one-way trap, mismatch
      6.6 m against an 8.1 m budget. Dellhollow unmoved: seam_test 294/0,
      slice_test 514/0, cine_solve --check and scenegraph_derive --check both
      clean.

      THE ONE FAILURE IS A BUILD ARTIFACT AND IT IS ORDERED FIXED: the blockout's
      square->barn road ribbon OVERSHOOTS 3.6 m past the barn to meet the gate
      court's flagstones, so a mesh belonging to the previous edge lies across the
      northlane<->gatefield seam wherever it is put — every position on the edge
      including t=1.0, still 1.26 m from l14's corner against a 1.4 m minimum
      band. The simulated walk fires once each way; the failure is the mesh box,
      not the route.

      HELD FOR THE BUILDER'S CLOSING ROUND, and this is the state to resume from:
      (1) ribbon-stops-at-its-own-edge, (2) prop-class pads sized to the prop
      (walk_pad_brook-bridge is 3.4 x 3.8 m for a plank footbridge and sits 0.7 m
      off Pond Lane, which is why that frontier had to settle 3.4 m from the
      Heartlight instead of at the lip), (3) three trees moved —
      veg_emb_ln_tree2 (43.6, 33.8) is STANDING IN THE GATE COURT, tree3
      (37.2, 30.6) on the north lane, tree4 (39.8, 20.6) at the pond lane's mouth.
      When the export lands: re-run the lip/arrival harness, take the plaza lip,
      author the three arrival overrides (candidates already measured), bake, run
      the gates, run tools/emb_sheet.mjs. Nothing else blocks it.

      A HALF-WRITTEN BAKE WAS REFUSED, twice over. The master grew 835 KB ->
      968 KB across the night and its lamp count changed underneath a sweep that
      was in progress (which is why the first Home Row grade reading, 0.25x,
      disagrees with the second, 0.80x — same script, different blend). Baking a
      set from a blend being written, against a walk bundle that predates it,
      would have had to be thrown away. The one-camera dry run used to prove the
      light-rig hook was deleted for the same reason.

## THE MASTER'S CLOSING ROUND — three specified fixes, four inherited, one falsified
## expectation (2026-07-31, builder's lane)

MASTER: `tools/blends/emberbrook-master.blend`, single-writer for this round. Chain,
in order, each deterministic and each `-- --digest`:
    Blender -b -P tools/emb_blockout.py --python-exit-code 1
    Blender -b tools/blends/emberbrook-master.blend -P tools/emb_{square,lane,home,gate,entrance}_build.py \
        --python-exit-code 1 -- save
TWO FULL RUNS, BIT-IDENTICAL: blockout 69da8696, square b1342adf, lane b4b847a4,
homerow 5b672177, gatefield 834c5dbd, entrance b1ed22b8.

WALK GATES (master_walk_qa's own two rays, each district's own region):
    square     0 / 1436      lane       0 /  994      entrance   0 /  945
    homerow    6 /  727      gatefield  3 /  945
Baseline for comparison was taken by re-running ONE probe over the committed master
2019716 — the blend the inherited numbers describe — rather than by quoting them, and
it reproduced them exactly (square 0/1454, lane 0/985, homerow 6/787, gatefield 2/954).

THE GATEFIELD DID NOT GO 2 -> 3. THE GROUND WAS HIDING THE THIRD, and this is the
finding of the round. Delete `emb_ground_*` from the OLD master and its gatefield reads
3 offenders / 194+1+4 samples — bit-identical to the new one. The gate's down ray starts
at sz + 0.90 and takes the first surface it meets; where the interpolated ground stood
above the walk top it was that surface, and the barn's base plinth below it was never
reached. So carving the road out from under the grass (fix 4) did not add an offender,
it made one visible. `emb_gt_barn_doorA` (1 sample) and 55 more samples on
`emb_gt_barn_base` were always there. AN INSTRUMENT THAT CANNOT SEE THROUGH THE TERRAIN
REPORTS THE TERRAIN'S OPINION OF THE DEFECT.

THE SEVEN FIXES, each with its measurement:

1  WAYPOINT BOW (map 4c251a7) — RE-RUN, AND THE EXPECTATION IS FALSIFIED. Home Row is
   still 6 offenders. The bow is not the mechanism: measured, the stamped waypoint
   [20.4, 31.9] lies INSIDE elder-house's own built footprint (x 17.18..20.82,
   y 28.98..33.02) — it bends the lane into Rowan's house rather than above it. And the
   deeper cause is the barn's, twice: `DOOR[hillside-cottage]` = (24.92, 26.78) is 3.43 m
   SE of the cottage (derived from the ROAD edge to the square) and `DOOR[elder-house]` =
   (15.62, 29.80) is 3.62 m WSW of Rowan's (derived from the home-lane-end edge), so the
   lane between them starts on the far side of one house and ends on the far side of the
   other and crosses both footprints. Renaming cannot fix it — the offence is geometric —
   and the two footprints OVERLAP along the line joining them (centres 3.99 m apart,
   half-extents 2.35 and 2.02 along it), so no ribbon of any width fits between them.
   FOR THE MAP (coordinator's, not mine): a path ribbon is 1.7 m wide, so clearing needs
   0.85 + 0.30 = 1.15 m from each face. Routing north of both needs waypoints clear of
   x = 24.95 / y = 31.67 (hillside-cottage) and y = 33.02 (elder-house) by that much,
   AFTER chaikin's corner-cutting. The alternative is a blockout rule — a house on a
   THROUGH street gets its doorstep beside the street instead of 3.4 m along it — which
   is real work and a ruling, not a re-run.

2  A ROAD RIBBON STOPS AT ITS OWN MAP EDGE'S END (`emb_blockout`, rule 6). Two edges
   meeting at a landmark share one derived doorstep and it faces only one of them, so
   the other ran past the landmark to reach it: `square-plaza__barn` overshot the tithe
   barn by 3.65 m (l11..l14, l14 reaching (36.8, 36.6)) into the gate court, while
   `barn__gate-court` — whose whole polyline lies inside the court's rim — was swallowed
   and owned no mesh at all, which is where the northlane<->gatefield boundary sits.
   Now RECLAIMED: the tail is cut at the polyline's own closest approach to the barn and
   handed over, so `walk_e_barn__gate-court_l0..l3` ARE the old `square-plaza__barn`
   l11..l14, vertex for vertex. Measured: 99 walk samples fall inside the barn's base
   footprint before and after, from the same quads, under different names — the network
   is unchanged metre for metre and only its ownership moved. Total ribbon segments 151
   before, 151 after, over 14 edges instead of 13.
   THE SWALLOWED-SPUR BEHAVIOUR IS INTACT: only a THROUGH edge (both ends carry other
   edges) reclaims. The seven plaza spurs still swallow. `brook-bridge__square-plaza` is
   a through edge with nothing to reclaim (0.81 m after trim, its neighbour ends AT the
   bridge, no overshoot) and is still swallowed — now SAID so, distinctly, in the log,
   because the pondlane<->square cut sits on it and the camera lane should see it.
   AND THE RECLAIMED STRETCH REPLACES THE STUB rather than appending to it: keeping the
   0.46 m that lay inside the court cost 55 extra walk samples under the barn's plinth
   for ribbon the court's own floor already carries.

3  A PROP-CLASS PAD SIZES TO THE PROP (rule 7). Prop pads are now the prop's own
   footprint + 0.30 m, ORIENTED, and CAPPED at the 3.0 m landmark default so the rule
   can only shrink a pad. Before -> after, every prop pad in the town:
       brook-bridge   3.61 x 3.88 -> 2.61 x 2.94 AABB (deck 3.2 x 2.2 -> 2.6 x 1.4)
       waystone       3.00 x 3.00 -> 2.60 x 2.00     home-lane-end  same
       back-lane-closed / upper-lane-closed  3.00 x 3.00 -> 2.60 x 2.00
       brook-spring / brook-mouth            3.00 x 3.00 unchanged (the cap held)
       notice-board / well                   no pad (they stand on the plaza floor)
   No prop pad grew in area. The bridge's deck lost 48% of its area and is a plank
   footbridge again: 2.6 m spans the 1.2 m brook with 0.44 m of bearing on each bank.
   THE RAILS WERE THE SAME BUG AS DAYLOG (e), STILL ALIVE. `(-ay, ax)` is the span axis
   and `(ax, ay)` the width; the rails were offset along the SPAN (both of them down the
   deck's centreline, overhanging 1.05 m past each end) and the posts across it, 0.25 m
   out in the air. Deck, rails and posts now all come out of `bodysize` and cannot
   disagree.
   AND IT DID NOT CLEAR POND LANE, honestly: pad-to-corridor went 0.262 -> 0.271 m. The
   arithmetic says it cannot. `brook-bridge` (38, 26) is 1.382 m from the pond lane
   ribbon's own edge; the brook's south bank is 0.8 m south of the bridge point and a
   deck that reaches it with bearing must extend ~1.04 m, plus half the deck's width.
   FOR THE MAP: 0.75 m is the ask — either `brook-bridge` north, or the pond lane's
   waypoints (37, 23.5) and (40.5, 23.2) south by 0.7.

4  NO ROAD UNDER THE GRASS EITHER (rule 5, the entrance builder's finding 3, promoted
   into the blockout). `ground_z` now carves a ROAD CUT the way it carves the brook:
   0.12 m below the walk top, full out to 1.40 m beyond any walk footprint, easing to
   nothing over the next 1.60 m. The ground mesh is therefore built LAST, after the
   pads, the ribbons and the area floors exist to carve against — the one real
   re-ordering in the file, and `rebuild_wcut()` is called twice (once after the ribbons
   so the LAMPS are seated on the carved surface, once after the area floors for the
   mesh itself). Town-wide, over every walk sample in every parcel:
       buried > 0.05 m   1015 of 3759 (27.0%)  ->   80 of 3656 (2.2%)
       buried > 0.10 m    744        (19.8%)   ->   42        (1.1%)
       buried > 0.20 m    314         (8.4%)   ->   29        (0.8%)
       worst              0.658 m               ->  0.522 m
   The residue is not road: it is the UPHILL RIM of two area floors (washline-green's
   north edge at (41.2, 32.5), the plaza's north edge at y 28.5) where a flat terrace is
   cut into a slope and the ground grid's next vertex is still on the bank. That is a
   retaining bank, and it is district art, not a blockout defect. Sub-centimetre residue
   (24% of samples are within 5 mm) is the 1.5 m ground grid interpolating between
   carved vertices; GSTEP 0.9 was TRIED and REJECTED — it moved >0.05 m from 2.2% to
   1.5% and cost 6 200 vertices, which is not a trade.

5  WAYSTONE (map d810725) — re-run, nothing to author. Its search returns the map point.

6  THE BUNTING WAS NEVER HUNG FROM A LAMP. `emb_square_build` read
   `o.matrix_world.translation` on the blockout's lamp caps; the blockout bakes world
   coordinates into every mesh and leaves the object at the origin, so every lamp anchor
   resolved to (0, 0, 0) — 38 m from the plaza — and silently failed the radius test.
   The square's bunting has hung off roofs alone since it was written. Fixed with the
   entrance builder's `world_centre` helper (THIRD copy; the next one goes in
   district_lib). Now 6 lines / 14 flags off 11 anchors, 8 of them lamp caps.
   AND A STRUNG LINE IS A SOLID: with the ring suddenly reaching out of the plaza, two
   spans sagged into the corridor over `walk_pad_back-lane-closed` and
   `walk_pad_hillside-cottage` (2 offenders, from 0). The whole span is now gated with
   GateGrid BEFORE any of it is built, so a line is never half-hung; 2 refused, and the
   square is back to 0 / 1436.

7  THREE TREES OUT OF THEIR OWN DISTRICT (`emb_lane_build`, the camera lane's finding).
   Two rules, both searched rather than authored:
     (a) A TREE NEVER STANDS IN SOMEBODY ELSE'S PARCEL. The search was bounded by
         REGION, which is the parcel padded by 3 m — and that padding exists so the file
         can SEE its neighbours, not plant in them. The rule is NOT "inside p-lane"
         (that forbids the wood east and north of the pond, which belongs to no parcel
         and is exactly where a waterside wood stands); it is "inside p-lane, or in
         nobody's parcel".
     (b) A CROWN CLEARS EVERY LANE BY ITS OWN RADIUS. `place()` gates a 1.0 m trunk,
         which is right for the walk gate and useless for occlusion — the thing between
         a camera and its subject is the CROWN, 3 m across and leaning. Now 3.0 + 1.0 m
         from every `walk_e_`/`walk_pad_` face. This is Festival Square's 5.4 m lesson
         (seam-canon §9.3: move the occluder) applied where it never was.
   Both cost trees at first — 7 of 8 hosts fell to 3 — so the SEARCH was widened rather
   than the rules relaxed: six radii x +/-48 degrees instead of three x +/-24. 7 of 8
   again, all of them now in their own district and clear of every lane. Refusals are
   printed: outside the parcel 88, crown over a lane 23, no ground 19.

8  THE COURT GETS NO LAMP, and shipped canon was checked BEFORE removing it, because
   shipped canon outranks the plan. `public/js/chapter1.js`'s `gate` scene carries no
   `lamps` array at all — lamp1 is on the lane, lamp2/lamp3 plus one already-lit post
   are in the square, three in the chapter, none at the court — so nothing shipped
   stages a light there and `emberbrook-town.md` §1 stands. `gate-court` is in NO_LAMP;
   the roll is 14, renumbered cleanly, rounds order preserved minus the court stop:
     00 road-gate  01 orchard  02 washline-green  03 pond-jetty  04 lake-home
     05 elder-house  06 barn  07 brook-bridge  08 bakery  09 inn  10 item-shop
     11 hillside-cottage  12 square-ring1  13 square-ring0
   NAMES, because the earlier handover had them backwards: the POSTS are
   `emb_lamp_NN_<host>_{post,glass,cap}`; the LIGHTS are `KEYEMB_lamp_NN_<host>`.
   FOR THE CAMERA LANE: `emberbrook.cameras.json`'s `lightRig.census.lamps` still says
   15 and `cine_bake` asserts it — it needs 14. That file is the camera lane's and was
   not touched.

GEOMETRY_AUDIT, before and after over all four district regions, diffed as offender
ROWS rather than as totals: 205 -> 217. NO NEW CLASSES. The twelve net rows are the
accepted classes arriving on new instances — a flag on its own bunting line, two
consecutive bunting boxes touching, bunting into the shopfront it is strung from, a
straw bale bedded 0.04 m into the barn's plinth, a washline tied 0.06 m into its post
and a cloth 0.01 m over that line, a bare branch reading as a stray from its own trunk,
and Lake's cottage into the `hillside-cottages` vista cluster (which was already an
offender through a different pair). Eight old rows are gone. The three documented
classes — foundations bedded in ground, the support ray starting inside its support,
and zero-origin objects reporting "at (0,0,0)" — are all still present and still not
defects.

EXPORT: `public/assets/scenes/emb-walk/` re-made from the closed master. 140 walk_
meshes in the blend, 140 walk_ nodes in the GLB, verified by reading the glTF JSON —
including all four `walk_e_barn__gate-court_l*`. bar_39 veg_653 water_3 lm_50 emb_575,
fx stripped 0.

05:0x EMBERBROOK IS BAKED — six shots shipped and gated, and the multi-edge gate
      caught two things every per-edge check passed over.
      GATES: cine_test --town emberbrook 296/0/0 · seam_test 128/0/5 soft ·
      seam_walk 11/11 · cine_solve/scenegraph/routes --check all clean ·
      plate_flat 1 flag (inspected: the night sky, constant by construction, not
      a card) · arrival_probe 19 arrivals, 17 visible. DELLHOLLOW UNMOVED
      throughout: cine_test 642/0, seam_test 294/0, seam_walk 9/9.
      VISIBILITY, ray-cast by the bake: arch 100.0, square 62.5, pondlane 100.0,
      homerow 64.1, northlane 62.5, gatefield 100.0 against a 45% bar; character
      55-136 px of 768; every region 100.0% in frame.

      AN ARRIVAL MUST CLEAR EVERY BAND THE RECEIVING SHOT CARRIES, not only the
      one it came through. seam_walk's BROOK LOOP oscillated 31 times while every
      per-edge walk passed: Pond Lane reaches the square by two routes 1.2 m
      apart, their frontiers are co-located twins by design, and both plaza-side
      arrivals sat clear of their own band and INSIDE the other's. Festival
      Square carries five bands. Re-searched under the every-band constraint at
      the full 1.6 m target: 289 legal points, nearest 4.2 m out, taken — the
      town's longest teleport, inside Dellhollow's 6.5 m outlier, and bought by
      the map (walk_pad_brook-bridge still overlaps the lane corridor by 0.271 m;
      the 0.75 m landmark move is queued).

      AND A STATED LIMIT OF THE INSTRUMENT, documented rather than tuned away.
      seam_walk's walker is an ARC-LENGTH walker: after a cut it re-projects the
      arrival onto the journey polyline and takes the nearest point. A journey
      that goes out along one of two routes 1.2 m apart and back along the other
      CROSSES ITSELF, so the outbound arrival projects onto the return leg 16 m
      away and it ping-pongs forever. That is a fact about the polyline, not the
      town. The loop ships as two journeys and the journeys file says exactly
      what that therefore does not test.

      TWO ARRIVALS SHIP INVISIBLE, MEASURED THREE WAYS BEFORE CONCLUDING. Both of
      the north lane's probe 0.0% against its own baked depth. (1) A ray-cast
      sweep of all 288 yaw/pitch candidates against both arrival points at chest
      and head height: no camera position in the town sees both. (2) The named
      occluders are emb_gt_barn_walls and emb_gt_barn_roof — the shot's OWN
      subject. (3) Every one of the 22 legal override points per arrival probes
      at 0.0%, because they all sit at the lane's north end behind the barn. The
      tithe barn stands at (33,34), which is the lane's own terminus. THE CAUSE
      IS THE MAP; no override was authored, because the checker would have been
      right to refuse it.

      AND THE CONVERSION LESSON, PAID AGAIN, IN MY OWN INSTRUMENT. The first
      sweep for a north-lane angle that could see its arrivals reported that
      several could. It was pointing at map (32, -31.8) — the runtime arrival
      [x, up, -y] copied into a map-order [x, y, h] probe without negating, 53 m
      south of the town in open air, where every ray is clear. The bake's depth
      plate disagreed and was right. Same shape as the lockfive 29-m-in-the-air
      override; an instrument is not exempt from the rule it exists to enforce.

      THREE MORE TOOL DEFECTS, all in the inherited --town work and all invisible
      until a SECOND town existed. seam_walk CRASHED AT IMPORT for every town but
      Dellhollow (its built-in journey list is an eager literal calling ep() on
      Dellhollow edge keys against whatever map is loaded). cine_test VALIDATED
      EVERY TOWN'S EDGES AGAINST ONE TOWN'S GEOMETRY — thirty failures about
      Dellhollow's seams while testing Emberbrook. slice_test resolved "the first
      node of kind town", a coin toss on key order once two exist; and "the town
      START has a portal to" is also wrong because the valley reaches both — the
      slice is one NAMED journey, so it now resolves the town whose map contains
      every landmark the slice walks.

      STILL OPEN, AND EACH ONE IS A MAP OR BUILD LINE, NOT A CAMERA:
      1. slice_test 734/6. Every enterable building inside Festival Square
         (item-shop, inn, bakery) has NO walk_pad_<id>: the swallowed-spur rule
         removed their doorsteps along with their road ribbons, so their door
         triggers sit at the building CENTRES, inside the walls, and two return
         spawns land off the walk network. Same over-reach that dropped two
         camera boundaries earlier tonight; same fix shape — an enterable
         landmark keeps its pad even when its spur is swallowed.
      2. The tithe barn on the north lane's terminus (above).
      3. The brook-bridge pad still overlapping the Pond Lane corridor by 0.271 m.
      4. Festival Square's floor: ~42 m2 of scattered cells in a 12.7 x 13.5 m
         box, centre almost entirely footprint cut-out, y=26 and y=29-30 empty
         where the brook crosses. It renders as stepping stones on grass rather
         than a cobbled heart, and the Kindling Hour crowd needs ground.
      5. THE ARCH AT 0.38x, my one standing dissent on the grade. It is the
         game's first frame and it misses the 0.40x ground-luminance floor;
         sky 0.80 clears it for one field and one re-bake, at 2.5:1 -> 1.8:1 of
         pool contrast. Both numbers are on the board.

      CONTACT SHEET: docs/qa/emberbrook/cameras.html — every shot's plate and
      depth map side by side with its authored intent, solved standoff, measured
      visibility against the bar, character pixel height and the framing note
      that says why this angle and not the one in the brief. Linked from
      index.html by the generator, because index.html is regenerated wholesale by
      emb_shots.py and a hand-added link would not survive.

## RULE 8 — AN ENTERABLE LANDMARK KEEPS ITS PAD (2026-07-31, builder's lane, final round)

THE SWALLOW RULE HAD OVER-REACHED A THIRD TIME. `walk_pad_<id>` is not only floor:
`scenegraph_derive` reads it BY NAME to seat a door's trigger, and `slice_test` proves
that against the exported GLB. item-shop, inn and bakery stand inside `square-plaza`'s
7 m radius, so their doorsteps were on the plaza's floor and their pads were skipped —
four interiors shipped with no named geometry at three of their doors. Enterable
landmarks now keep a THRESHOLD pad on the doorstep even when the area floor carries the
surface: 1.2 m along the wall face x 0.9 m deep, ORIENTED, coplanar with the floor (so
`eff_top` still has nothing to choose between), emitted WITHOUT the ring search — that
search exists to lift a doorstep out of a NEIGHBOUR'S WALL, these three stand on open
plaza, and running it would reassign `DOOR[]` and move every ribbon in the town.

SLICE_TEST 734/6 -> 737/3, and the three that remain are not this file's:
they are the door TRIGGERS, still reading `at` = the landmark CENTRE out of the
committed scenegraph. The custodian's derive fix (trigger on the pad, Dellhollow
byte-proof) closes them on its next derive; the pads it needs now exist and export.

A PAD CAN NEVER CARRY ITS OWN RETURN SPAWN, and this is worth writing down because two
of us chased it before the arithmetic was stated: the spawn is DEFINED as the trigger
plus 2.90 m, and the trigger sits on the pad, so a pad covering its own spawn would have
to be 5.80 m deep. The 3.0 m default already took Festival Square's walk gate from 0
offenders to 11 (it lands on the Heartlight's steps, the notice board's posts, the item
shop's own trays and the well's lip); 5.8 m is that failure an order of magnitude worse.
Re-centring does not help — it carries the trigger along and pushes the spawn out again.
Off-network spawns are the derive's street search, not the blockout's geometry.

TWO SIZES WERE TRIED AND MEASURED BEFORE THE RULED ONE STUCK. At 1.4 m deep the
item-shop's threshold reached `emb_sq_heart_step`: that doorstep stands only 0.38 m clear
of the Heartlight's own step (2.86 m square on the plaza's centre, doorstep 2.40 m from
it). AND THE FIRST MEASUREMENT OF THE ROOM WAS THE WRONG INSTRUMENT — the same one as
finding (d). I took each threshold's clearance as the nearest VERTEX of the surrounding
furniture and got 0.49 m where the true answer was zero: a box's corners can be far away
while its FACE lies over the pad. Point-in-shape, never nearest-vertex.

AND ONE REAL BUG THE NEW SAMPLES EXPOSED, in `emb_square_build`: the stacked crates were
gate-tested at radius 0.30 while the crate is a 0.56 x 0.52 box turned by `h01` —
circumscribed radius 0.38. The test was 0.08 m smaller than the thing it was testing, so
a corner could overhang a walk sample the test never saw. It only surfaced when the
thresholds shifted the sample grid and one crate came down on the plaza. Tested at its
own radius now; 34 dressing pieces refused, square back to 0.

GATES after the full chain against the CURRENT map (which now carries f1064c6, the
withdrawn elder-house waypoint):
    square 0/1427 · lane 0/991 · entrance 0/939 · homerow 6/789 · gatefield 3/944
Two full runs bit-identical: blockout 0a1033ef, square 47fffe7c, lane 20de62a9,
homerow ef89b765, gatefield c4d46f54, entrance 88b400db. `routes_derive --check` clean
for both towns (emberbrook.routes.json re-derived — my walk network is its input and it
went stale when the chain re-ran). emb-walk re-exported, 139 walk_ meshes in and out,
`walk_pad_` present for all four enterable landmarks.

HOME ROW IS STILL 6 with the bow withdrawn, and the count is now honest rather than
lucky: both cottages sit on the lane between them because both doorsteps face away from
it. That is the map line still open, with the arithmetic in the closing-round entry.

## THE CAMERA LANE'S LAST ROUND — a one-line fix that stayed one line, the spawn a pad
## can never carry, and Emberbrook's doors open (2026-07-31 ~06:0x, camera lane)

SLICE_TEST IS GREEN: 740 assertions, 0 failed, BOTH TOWNS WHOLE. It was 734/6 when this
leg started and every one of the six was a door.

THE DEFECT, in one sentence: `scenegraph_derive.mjs` seated every town-side door trigger
at `T(lm.pos)` — the building CENTRE — and took only the HEIGHT from `walk_pad_<id>`,
contradicting its own comment ("TOWN SIDE: trigger on the landmark's door pad"). So every
door in Emberbrook stood inside its own walls, and the return spawn measured from it
landed off the network.

WHY DELLHOLLOW NEVER SAW IT, PROVED RATHER THAN ASSUMED. Its blockout puts each pad AT
`lm.pos`: all six enterables agree to <= 1.5e-6 u, which is float32 quantisation and three
orders under `r3()`'s 1e-3 rounding. The map's own point WAS the doorstep there, so "take
y" and "take x, y and z" are the same instruction. Emberbrook derives its doorsteps
`bd/2 + 1.15` = 3.43 m out along the street the door faces, precisely so the building sits
BEHIND them, and the same instruction puts the trigger in the masonry.

    non-Emberbrook nodes+edges of scenegraph.json, source strings excluded
      b1490ee458cfb93f6a2ccc5d3a9b31ebb9ee5e9023832b10d8872cf6ec670c76  at HEAD
      b1490ee458cfb93f6a2ccc5d3a9b31ebb9ee5e9023832b10d8872cf6ec670c76  trigger fix
      b1490ee458cfb93f6a2ccc5d3a9b31ebb9ee5e9023832b10d8872cf6ec670c76  + spawn search
NOT ONE numeric field of Dellhollow's wiring moved, through both changes. The only change
to its shipped rows is six provenance strings that now record ", its doorstep 0.00u off
the landmark centre" — and that 0.00 IS the proof, standing exactly where a `d > 0.25`
WARN used to fire, which was encoding the very assumption being removed. Two derive runs
are bit-identical to each other.

THE SECOND LINE I WANTED TO WRITE, MEASURED AND THROWN AWAY. `streetDir` — which chooses
the direction the return spawn steps off in — is anchored at `lm.pos`, and with the
trigger moving to the doorstep it looked obviously wrong to leave it there. Measured,
re-anchoring it at the doorstep FLIPS lake-home: its spawn lands 0.53 m from the landmark
centre, back inside the house, off the walk network. The centre anchor is correct, because
the direction to the street is a fact about where the BUILDING is, not about where you are
standing. That negative result is why the diff is one line.

A DOORSTEP PAD CAN NEVER CARRY ITS OWN RETURN SPAWN, and this is the finding of the round.
It is arithmetic, not tuning. The spawn is `trigger + doorRadius + spawnBackoff` = trigger
+ 2.90 m, and with the fix the trigger IS the pad centre, so a pad covering its own spawn
would have to be 5.80 m deep — a forecourt, which the blockout measured at 3.0 m taking
Festival Square's walk gate from 0 offenders to 11. THERE IS NO PAD SIZE THAT WORKS, AT
ANY CENTRE, EVER. The builder's lane spent a round moving the enterable thresholds between
`DOOR[]` (centre + 3.43) and `centre + 2.90` chasing it, and each move also moved the
trigger and so moved the spawn 2.90 m beyond it — the loop has no exit, which is why it
was stopped by message rather than by a better number. The ground `back` metres out
belongs to the STREET. Dellhollow's shelf streets are continuous and carry it; Festival
Square ships ~42 m2 of scattered cells in a 12.7 x 13.5 m box (31.6% walkable) and does
not. THE TWO LANES HAD DERIVED INCOMPATIBLE FIXES FROM THE SAME SYMPTOM, and the builder's
rule-8 comment recorded the 0.53 m discrepancy as a quirk of two different numbers when it
was the bug itself.

SO THE SPAWN IS SEARCHED, NOT ASSUMED (coordinator's ruling, and right on its own merits
rather than as cover for the floor). When the derived point has no walk surface under it,
the derive keeps the nearest LEGAL one — on the network, and at least `back` from the
trigger, which is the same constraint the checker already enforces on hand-authored
overrides. It steps OUT along the street first and sweeps +/-60 degrees either side on a
fixed grid, least displacement wins, ties broken in enumeration order, so no map
reordering can move it — the same determinism rule `streetDir` already keeps, and the same
searched-never-authored doctrine as a free-standing solid. IT IS GATED STRICTLY ON
"off-network", so a town whose streets are whole never enters the branch and cannot be
moved by it: in Dellhollow the search is dead code, and the hashes above are taken with it
in place. It fires twice, both in Festival Square: item-shop 1.39 u, inn 1.95 u, both
landing 4.15 / 4.40 u out from their triggers and both VISIBLE to the receiving shot
(93.4% and 100.0%). Its WARN names the real defect rather than the symptom — "THE STREET
IS THE DEFECT, not the door: give it ground and this stops firing."

THE RE-BAKE (authorized: rule 8 and the withdrawn elder-house waypoint both redraw ground
a camera sees). Grade UNCHANGED and asserted by the bake — exposure 0.55, sun 0.75, sky
0.55, 14 lamps at 680 W, Heartlight 5200 W. 402 s of Cycles, six shots, six depth passes.
Two cameras moved, both from the redraw and neither from a re-aim: homerow 2.3 m, square
0.3 m. Visibility ray-cast by the bake against the 45% bar, before -> after:
    arch      71.9 -> 71.9     square    62.5 ->  67.2     pondlane  100.0 -> 100.0
    homerow   64.1 -> 60.9     northlane 62.5 ->  62.5     gatefield 100.0 -> 100.0
Square IMPROVED and its own spawn probe now lands on `walk_pad_inn` instead of a road
ribbon — named geometry at the door, which is what rule 8 is for. HOME ROW LOST 3.2
POINTS, reported rather than tuned away: same camera move, still 15.9 points clear of the
bar, the honest price of an honest map.

AND A TRAP IN THE BAKE TOOL, WORTH THE NEXT AGENT'S TIME: `cine_bake.py` exports the
collision GLB ONLY under `--glb` (the depth pass destroys the scene, so it cannot be one
invocation). The render pass alone left `emb-cine` carrying the OLD 140-mesh network with
13 pads while `emb-walk` had 139/16 — the derive read the stale bundle and reported "no
walk_pad_item-shop" against a master that had one. A FULL RE-BAKE IS TWO INVOCATIONS.

THE GATE TABLE, everything green:
    emberbrook   cine_test 296/0/0 · seam_test 128/0/5 soft · seam_walk 11/11
    dellhollow   cine_test 642/0/2 · seam_test 294/0/3 soft · seam_walk 9/9
    slice_test 740/0 · scenegraph --check clean · cine_solve --check clean BOTH towns
    routes --check clean BOTH towns
    plate_flat 1 flag of 6 plates — pondlane 4.23%, RGB 69,87,116, the top band at
      ndc y 0.71..1.00 full width. INSPECTED: the same colour appears on northlane at
      0.16%, and pixel probes put it above the horizon only. It is the night sky, which
      is constant BY CONSTRUCTION, not a card. Unchanged from the previous bake.
    arrival_probe emberbrook 19 arrivals, 17 visible. The two north-lane 0.0% are the
      documented barn-hidden pair and NO OVERRIDE WAS AUTHORED, because the checker
      would have been right to refuse it — the cause is the map (the tithe barn stands
      at the lane's own terminus). Dellhollow regression re-run and unchanged.

STILL OPEN, and every one of them a map or build line, not a camera:
  1. FESTIVAL SQUARE'S FLOOR — promoted to the top art task by the coordinator, and it
     is the postcard fix. ~42 m2 of scattered cells in a 12.7 x 13.5 m box, 31.6%
     walkable; it reads as stepping stones on grass rather than a cobbled heart, and the
     Kindling Hour crowd needs ground. When it lands, the spawn search stops firing there
     by itself and the derived points stand on their own.
  2. The tithe barn on the north lane's terminus — two arrivals ship invisible.
  3. The brook-bridge pad overlapping the Pond Lane corridor by 0.271 m (0.75 m ask).
  4. Home Row is still 6 offenders; both cottages' doorsteps face away from the lane
     between them, and no ribbon of any width fits. Its walk gate did NOT improve with
     the withdrawn waypoint, as the builder's closing round already falsified — reported
     here because the handover asked for the number either way.
  5. The arch at 0.38x, the standing dissent on the grade, against a 0.40x floor.
  6. CAMERA-VS-FLOOR OWNERSHIP, 5.713 m over two spans (barn__gate-court@0.5..1 under
     gatefield over northlane's floor; washline-green__gate-court@0..0.363 under pondlane
     over gatefield's). CHECKED against the new solve and UNCHANGED by it. seam_walk
     walks both edges in four journeys and reports 0 corrections, so the positional
     safety net does not trip — but this is the shape that WOULD put a second cut on one
     passage, so it goes on the board rather than in a footnote.

## THE 2x RESCALE, AT BLOCKOUT — the map doubled, the river given a course, and nine
## constants that turned out to be facts about a 50 x 40 town (2026-08-01, builder's lane)

USER'S MORNING REDLINE, two lines: the town "read like the entire town is just one scene
in size", and the river "a single straight line... does not meet the bar of realism". The
coordinator answered both IN THE MAP (0585e35): every x,y doubled with heights kept, and
`river.course` replacing `river.centerX` — an authored polyline of [x, y, bankWidth] with
meanders. REVIEW GATE: the user rules at BLOCKOUT level before any district, camera, bake,
route or scenegraph work restarts, so this round is blockout + export + review frames and
NOTHING ELSE. Everything downstream is knowingly stale.

WHAT SCALED BY ITSELF, because the blockout derives from the map: every landmark position
and doorstep, every lane, the ground extents, the wooded rim's ellipse, the vista clusters,
the area floors' cell counts. WHAT DID NOT MOVE, and was checked rather than assumed:
building bodysize (4.8 x 4.0 / 3.9 x 3.3 + 1.14 oversail), lane ribbons (road 2.4 m, path
1.7 m), the doorstep threshold (1.2 x 0.9 m), the area-floor cell (0.45 m), the brook
(1.2 m), the lamp roll (FOURTEEN, map canon, 0 refused). Vertices 18 689 -> 35 385.

NINE CONSTANTS WERE NEITHER — they were facts about the TOWN's size wearing the clothes of
facts about a body, and they are now DERIVED (`TSPAN`, rule 9 in the file header; each
evaluates to its old literal on the 1x map, checked by re-running against it):
 1  THE RISE FELL AWAY INSIDE ITS OWN TOWN. `surface_z` blends the interpolated rise to
    the valley pan beyond 9 m from any anchor, over 16 m. Measured on the 2x map: 37.3%
    of the town's own bounding box was being pulled toward the pan (10.1% at 1x) and the
    worst point reached it outright — craters between the lanes. Now 0.20 x span and
    0.3556 x span: 18 m and 32 m here, 9 m and 16 m at 1x, to the decimal.
 2  THE TREELINE CAME APART, TWICE. Its band was a FRACTION of the ring's own radius, so
    at 2x it threw trees 41 m past the anchors, outside the ground mesh, and the bound
    check culled 68 of 150 — a horizon with holes in it, which is the one thing that ring
    exists to prevent. The band is now an absolute 11..28 m of wood (a fact about trees),
    the COUNT comes off the perimeter at the 1x spacing of 1.76 m (150 -> 231), and `PAD`
    is sized FROM the band instead of a literal 22 m, so nothing can fall off the mesh
    again — asserted in the build. 198 trees stand; the 33 skipped stood in the river,
    where the wood is supposed to open.

THE RIVER IS BUILT FROM ITS COURSE (rule 8) and the axis-strip generator is retired.
Extrapolated 26 m past each authored end so it leaves the frame both ways; chaikin-smoothed;
resampled at 1.5 m; the channel carved along it and the water skinned along it as a
two-vertices-per-sample strip (168 quads for 163.5 m of run over a 156.5 m chord —
sinuosity 1.04, banks 11.2-13.0 m). Vista only: nearest walk surface 5.5 m from the water's
edge, ASSERTED in the build. Three things the first draft got wrong and the arithmetic
caught:
 a  FOUR ROUNDS OF CHAIKIN, NOT THE LANES' TWO. A strip offset half the bank width folds
    into a bow tie wherever the course's radius of curvature is under that half width. At
    two rounds the bend below the north end came out at radius 4.4 m against a 6.3 m half
    width (ratio 0.69) and rendered as a lobe of water lying over its own bank. Four rounds
    take the tightest bend to 2.02 and move the sinuosity by 0.001. The ratio is printed
    and asserted > 1.05, so a future map redline with a tight bend fails the BUILD.
 b  THE BANK PROFILE, not a symmetric blend. The axis version's linear ramp leaves ground
    BELOW the water surface for ~4 m past the water's own edge — a dry trench inside the
    river. Now: a wetted channel shoaling from a thalweg 1.25 m down to 0.25 m at the bank,
    then out of the water within a metre and eased into the valley over 9 m.
 c  THE BROOK'S CHANNEL IS CUT AFTER THE RIVER'S, and the order is the whole confluence.
    Cut first (as it was), the last 15 m of it were overwritten by the river's bank profile
    and the stream's own water — which keeps the z the map authored — stood on top of the
    bank. It rendered as an aqueduct into the river. Measured after: the water runs
    0.33-0.60 m above its bed for the whole 84 m.
THE BROOK NOW REACHES THE WATER. The authored confluence (108, 54) is 1.7 m short of the
west bank; the channel is carried 3.2 m further along its last bearing, and the distance is
printed rather than assumed.

GATES. Blockout deterministic, TWO RUNS bit-identical (digest 2ae80703). COVERAGE asserted
in the build. Walk QA (master_walk_qa's own two rays, whole town — its identity check is
Dellhollow's and Emberbrook has no topology reference): 5 269 samples, 97.51% land on the
canonical collision surface, against 87.25% for the same script on the 1x map. THE 2x WORLD
IS CLEANER, and for a boring reason: the buildings pulled apart, so fewer solids stand on
walk floor. geometry_audit over the whole town 26 intersections / 10 strays, against 36 / 6
at 1x; all ten strays are a gable resting on its own body (the support ray starts inside the
body and exits 5 m below), and four of them were masked at 1x only because a NEIGHBOUR was
inside the 0.60 m attach radius. Not new, not a defect.

WHAT THE 2x MAP BROKE THAT IS A DESIGN QUESTION, NOT A BUILD FIX — reported, not decided,
because the user is reviewing:
 1  FESTIVAL SQUARE IS NOW A BALD DISC. Landmark POSITIONS doubled; landmark EXTENTS did
    not. The plaza is still 7 m of radius while the inn moved from 5.8 m off its centre to
    11.6 m, the item shop from 6.4 to 12.8, the bakery likewise. At 1x fifteen footprints
    were cut out of its floor and 216 cells survived; now eight are cut and 593 survive. The
    town's postcard is a 14 m cobbled disc with the Heartlight alone on it and its buildings
    a lane's walk away. The old open task "Festival Square's floor is stepping stones" is
    SOLVED by the rescale and replaced by its opposite. Map question: do the area extents
    scale too (plaza 7 -> 14, pond 6 -> 12, gate court 5 -> 10, orchard 5 -> 10)?
 2  THE VILLAGE WELL IS IN THE ROAD. `square-plaza__hillside-cottage` now runs over
    `lm_well_ring` — 22 walk samples, new at 2x, and the largest new offender in the town.
    A map line (move the well, or a lane waypoint), not a builder rule.
 3  THE HOME LANE RUNS DOWN THE BROOK, not across it. `elder-house__home-lane-end` and
    `hillside-cottage__elder-house` found THREE culverts each: at 1x the lanes grazed the
    water and it cost five culverts town-wide, at 2x the graze is twice as long and costs
    eight. Six stone culverts in a row is a lane that wants one bridge or a 2 m nudge.
 4  THE BROOK IS STILL A DITCH, and chaikin cannot fix it. Sinuosity 1.015 over 83.9 m,
    widest swing off its own chord 6.1 m. The river got an authored meandering course; the
    brook got its old polyline doubled. If "not a straight ditch" applies to the brook too,
    it needs the same treatment IN THE MAP.
 5  LAKE'S ROUND IS THE SAME FOURTEEN LAMPS OVER TWICE THE GROUND. Nearest-neighbour
    spacing 9.1 m median, 26.0 m worst. The roll is map canon and was NOT touched. The
    round's ORDER did change, and correctly: `near_sq` is the plaza's own extent + 3 m, so
    the group that "closes the ring" went from six lamps to four (inn, item shop and the
    two searched rim lamps) as the bakery and the footbridge fell outside it.
 6  THE ORCHARD HAS NO ROWS. "Orchard rows" is an `area` landmark and the blockout builds
    it as a 344-cell walkable disc with one lamp; the trees are the entrance district's
    dressing, which the review gate forbids running. At 2x it is a bare field.

LANE INCIDENTS — REVIEW AIDS ONLY, on the coordinator's mid-flight ruling (map
`laneIncident`, 7b39d4c). THREE lanes exceed 15 m and they are the district pass's
work-list: waystone__square-plaza 22.3 m, square-plaza__barn 20.8 m,
square-plaza__pond-jetty 16.2 m. Four grey `lm_incident_*` blocks (handcart- and
woodpile-sized) are SEARCHED onto the verge of those three — 2 on the gate road, 1 each on
the others, thinning to one at the Gate Field end per the ruling — for one reason: pacing
cannot be judged off a lane that is empty by construction. They add zero walk-QA offenders
and zero geometry_audit offenders, and the real dressing is the district pass.

DELIVERED: tools/emb_blockout.py (rules 8 and 9); tools/blends/emberbrook-master.blend;
tools/emb_rescale_shots.py + docs/qa/emberbrook/rescale/ (six frames, one grade — the
ratified golden hour; a dusk A/B is a lighting question and this board is about distance,
mass and water); public/assets/scenes/emb-townwalk/ re-exported with spawn [64,1.5,-44]
(Festival Square at its new coordinates) and the same spawn corrected in
tools/townwalk_live_refresh.sh, where the cron would otherwise have written the old one
back; tools/town_export.py's ortho stand-off sized to the town's span instead of a literal
103 m (Emberbrook's far corner was arriving 50 m from the clip; under an ORTHO camera
distance along the view axis costs nothing, so Dellhollow's plate is unchanged).

## BLOCKOUT ROUND 2 — the Whisperwood arrival, a stamped brook, a village made of
## households, and a forest that turned out to be the container (2026-08-01, builder's lane)

Round 2 arrived as FIVE separate rulings landing while the build was in flight: the agreed
redlines (extents x2, well off the lane, the Whisperwood arrival, brook-by-proposal, lamps
stay 14), then interior densification, then "thicken the forest hard", then ten lived-in
landmarks, then the Old Gate's cliff bottleneck. All of it shipped in ONE re-run, and the
one thing I would do differently is nothing about the scope — it is that I would have
distrusted my own instruments sooner. Three of them lied, and each lie is written up below,
because a builder's report is only worth what its measurements are worth.

THE BROOK, PROPOSED AND STAMPED (0dc0535). Searched against the real drawn ribbons, not
against straight lines between landmarks, and every constraint in `brook._doc` is now a
number the build prints every run:
    sinuosity            1.174 over 97.1 m of run on an 82.7 m chord  (target >= 1.15; was 1.015)
    home lanes crossed   ZERO. The course today crossed three of them six times.
    Pond Lane            exactly one crossing, AT the footbridge (drift 0.21 m after chaikin;
                         two pin points either side of brook-bridge hold it there)
    the r14 plaza        2 cells cut, both at the far ENE rim. Was 209 — the course in the
                         map ran straight through the plaza's north side and nobody had
                         measured it, because nothing counted cells lost to water until now.
    culverts             2, neither on a home lane (was 6, three in a row on one lane)
A HOME LANE NOW GETS A PLANK BRIDGE, NOT A CULVERT, per the doc's "each crossing a small
bridge". With this course none is needed; the rule is in for the next redline that does.

THE WATERMILL'S WHEEL WAS SIZED BY THE VALLEY, NOT BY TASTE. An overshot wheel cannot
exceed the drop from its leat's crown to its tailrace, and Emberbrook's whole brook falls
2.4 m. The first measurement was HEAD 1.55 m -> a 1.55 m wheel, and it was REPORTED rather
than inflated; the user ruled option (b), a 2.00 m dam, and the build now prints HEAD 2.35 m
-> a 2.35 m overshot wheel every run, so the ruling stays checkable against the number it
was made on. THE MILLPOND IS AN IMPOUNDMENT AND THAT COST GEOMETRY: a 2 m dam holds water
2 m above the brook it stands on, and the first version simply raised the water surface —
a slab of water lying on a hillside. It is now a POUND: basin carved in `ground_z`, a ring
of embankment built only where the natural ground is too low to hold it, the dam proper
across the downstream lip with the head gate in it.

THE ARRIVAL — AND THE INSTRUMENT THAT SAID IT WAS FINE WHEN IT WAS NOT. The opening frame
is the clearing at (52,-28) looking north up 32.5 m of wood road to the arch. The reveal
probe casts from eye height at 2 m intervals and asks three questions: can I see the arch,
a village solid, the Heartlight. It reported "the village: NEVER" and the RENDER OF THAT
EXACT FRAME showed the arch and two cottage roofs. Three bugs, in order of discovery:
 1  It aimed at `landmark.pos.z + 5.4` — a height picked to clear a roof. The Heartlight's
    entire massing is 3 m tall, so the target sat in EMPTY AIR ABOVE THE FLAME and the ray
    reached it unobstructed. Targets now come off BUILT OBJECTS' world bounds.
 2  Then it aimed at each solid's bbox centre 0.35 m under the top — which on a GABLE is
    inside the roof's own wedge. The ray entered its target's skin ~0.6 m out against a
    0.45 m stop margin, so EVERY ROOF IN THE TOWN reported itself occluded. Three aim
    points per solid now, at the eaves and the shoulder, and the ray stops 0.9 m short.
 3  Its village list excluded y < WOOD_Y1 + 4 — which excused exactly the roofs nearest the
    arch, the ones the ruling is about.
A VISIBILITY ORACLE THAT FAILS CLOSED IS THE MOST DANGEROUS INSTRUMENT THERE IS, because a
pass looks like a pass. Fixed, the honest answer is: 5-8 of 148 built village solids have a
sight line from the road, and the count does not fall as you walk (32m:7 31m:8 29m:7 26m:7
24m:5 21m:0 19m:7). That is a handful of distant roof slivers beside a lit arch at the end
of a long dark corridor — not a reveal failure, but not "invisible" either, and it is the
user's call. I TESTED THE OBVIOUS FIX AND IT DOES NOT WORK: bending the road (a single bow,
then a full S-dogleg to (43.5,-17.5) and (52,-3.5)) moves WHICH solid is visible and changes
nothing else, because the corridor points at the town whatever shape it is.

WHAT DID CLOSE THE WOOD WAS TWO NUMBERS AND A SHRUB. (a) The reveal ramp was 8 m of
no-trees plus 14 m of thinning around the arch — a 44 m hole punched in the treeline
exactly where the sight line leaves. A village arch is 3.4 m wide; 5 m of clearance shows
it whole. (b) The wood stopped at the arch's own latitude, leaving the ground between the
arch and the orchard nearly bare; it now wraps 12 m past and dies against the village's own
lanes. (c) UNDERSTORY. The first render of the opening was a corridor of BARE TRUNKS — a
canopy starting at 3 m occludes nothing at a walker's eye, and a walker's eye is the only
height the arrival is ever seen from. Wood-sector crowns now start at 18% of height and
most trees carry a low clump thrown off the trunk, so the mass sits BETWEEN the stems.

THE FOREST IS THE CONTAINER (user ruling, `forest._doc`). 1 612 trees on a 2.75 m grid,
gated by GATEGRID — a crown clears every walk surface by ITS OWN radius plus 1.0 m, the
radius drawn from the tree's own hash BEFORE the gate is tested, and asserted afterwards
against the ribbons themselves rather than against the raster the placement used (tightest
1.81 m). Emitted as 18 BATCHED meshes rather than 4 800 objects: the runtime loads this GLB
for the free-roam scene and per-tree objects would have tripled it. A chamfer distance
transform of the walk raster (`WDIST`) answers "how far to the nearest walk surface" for
both the forest and the infill; it is deliberately conservative, because OCC is dilated.

THE INFILL, TWICE. First implementation read "densify" as "more roofs" and seeded HAMLETS —
3-5 cottages in one 7 m hedge ring. The user saw it in a live snapshot and named it exactly:
cottages packed wall to wall. The correction was not fewer roofs, it was A DIFFERENT UNIT.
Each infill cottage is now a HOUSEHOLD: its own garden plot (hedge or paling, with a gap at
the gate), a fruit tree or two standing in it, a shed or a woodpile against the boundary,
and A TRACK — non-walkable, but visible, joining a real lane where one is in reach and
NARROWING AWAY where none is. 53 households, 21 tracks joining, 32 fading. Spacing is drawn
from each seed's own hash at 7.5-12.0 m, and the floor is 7.5 rather than the ruling's 6.5
for a measured reason: a roof oversails its walls by 16%, so two 5.9 m cottages 6.5 m apart
share 0.4 m of roof volume, and six pairs did. The forest fills BETWEEN the plots (trees
start 8.2 m from a household, not 11 m from a hamlet), which is what "the wood filling
between garden plots rather than more houses" asks for.

THE ROOF-COUNT PROBE ALSO LIED, the same way. It tested one point per roof and reported a
median of ONE against the ruling's 2+ target, which is what drove the packing in the first
place. Three points per roof and a 35 m range (the range the ruling means — "look around
and see other people's roofs") give: median 4 roofs in sight within 35 m, 12 within 60 m,
4 of 8 compass sectors, 84% of lane samples meeting 2+. THE PACKING WAS A RESPONSE TO A
BROKEN NUMBER. Worth saying plainly, because it nearly shipped.

THE BLUFFS (user terrain ruling). Two chains of coarse rock massing converging on a 9 m
notch at the Old Gate, derived from the sealed portal so the funnel is wherever the map puts
the gate. The first draft stepped them straight out ACROSS the pinch and laid the western
chain along the top of Home Row, where they rendered as blank grey slabs looming over the
village; both chains now move out AND forward together. A crag is a pile, not a tower —
three offset lumps under a broad cap, because one tall box with a spike on it renders as a
skyscraper (it did). THE PINCH IS NOT SEALED: the stamped river leaves the valley 37.8 m
east of the gate, its own bank 31.7 m from the masonry, so there is a 32 m walk around the
bottleneck. An amended 3-point tail is proposed in the report; stamped water was not moved.

THREE SHARED TOOLS HAD BUGS THAT ONLY THIS MAP COULD TRIGGER, all fixed here:
 -  master_walk_qa masked every mesh whose NAME contains "smoke" as a haze helper. The map
    added Finn's SMOKEhouse; `walk_pad_smokehouse` was masked out of the depsgraph for the
    ray cast and then failed check [5] as "hidden in the VIEWPORT, glTF would drop them" —
    a tool inventing a defect out of a landmark's name and biasing coverage on the way past.
    The `walk_`/`bar_` prefix is a contract and now outranks the keyword.
 -  geometry_audit had no way to call a thing soft except by PREFIX, so a hedge segment or a
    paling that is a PART of an `lm_infill_NN_*` assembly could not be recognised. 602
    "offenders" were adjacent hedge segments, embankment sections and rock lumps overlapping
    each other, which is what continuous runs and rock piles ARE. With `SOFT_PART` the
    residual is 61 intersections / 43 strays, and the strays are the documented
    gable-resting-on-its-own-body class multiplied by 53 households.
 -  emb_rescale_shots' enclosure probe used 1.4 m, which catches a camera inside a tree
    crown AND a camera standing on a 2.4 m forest road with scrub on the verges. Round 2's
    understory evicted the Waystone camera 5 m into the air and it rendered the stone from
    above, through the canopy. 0.90 m.

AN AREA FLOOR NOW STOPS WHERE A LANE CLIMBS OFF IT — rule 6 arriving from a new direction,
and a real find. An area's floor is FLAT at the map's authored z; the lanes leaving it are
laid at the map's z too and CLIMB. At r7 the barn lane was 0.1 m above the plaza where they
overlapped and nothing could see it. At r14 it is 0.45 m above, the ground is carved down to
the LANE (the nearest walk surface), and 97 of the plaza's own cells ended up under 0.35 m
of grass — walk faces rendering as a bank. The stretch belongs to the lane, which already
carries it, so the floor gives it up: 103 cells handed over on the plaza, 12 on the washline
green. Walk coverage 95.58% -> 96.87%.

GATES. Deterministic, TWO RUNS identical (digest 8f537f4e). COVERAGE asserted in the build.
LAMPS ASSERTED AT FOURTEEN — two redlines each tried to grow the roll to 22 and neither was
a lamp decision, so the woodroad district hosts none (the arch is the first lamplight the
player ever sees) and the ten outbuildings are denied by name; a future map that means to
change the roll will fail the BUILD and get to say so. Walk QA 9 048 samples, 96.87% land on
a walk mesh. geometry_audit 61/43. 2 267 objects, 121 750 verts.

WHAT IS A DESIGN QUESTION, NOT A BUILD FIX — reported, not decided:
 1  The village is faintly visible from the arrival road (5-8 solids of 148) and no road
    bend fixes it. Accept the distant roofs beside the lit arch, or move the clearing.
 2  The mill's 2.35 m wheel needs a 2.00 m dam whose pound stands ~1.9 m above the natural
    ground behind an embankment. Legible as a hillside mill pound; it is visible massing.
 3  The Old Gate bottleneck is not sealed — 32 m of walkable ground between the gate and
    the river's west bank.
 4  smokehouse and watermill stand inside authored water extents; the water is cut around
    them so nothing renders in a pond, but a building that needs a hole cut in a pond is a
    map fact.
 5  The free-roam GLB went 3.6 MB -> 11.2 MB (the forest and 53 households). Batching
    already saved ~3x; if it matters, the forest wants instancing at the district pass.
 6  `road-gate__orchard` still refuses its one lane incident — no clear verge.

DELIVERED: tools/emb_blockout.py (households, forest, bluffs, the mill, the lived-in
landmark forms, six new instruments); tools/blends/emberbrook-master.blend;
tools/emb_rescale_shots.py + docs/qa/emberbrook/rescale/ (TEN frames — the six earlier
filenames are stable and re-aimed from map extents, plus arrival-clearing, waystone-road,
wood-aerial, watermill); public/assets/scenes/emb-townwalk/ re-exported, spawn [64,1.5,-44];
tools/master_walk_qa.py and tools/geometry_audit.py bug fixes; two searched map positions
(pond-weir, smokehouse) written on the coordinator's explicit delegation.

## OVERWORLD GEOGRAPHY DRAFT — the hanging valley / water gap, BUILT AS A PROPOSAL (not canon)

The user was not convinced by the water-gap proposition, so it was built rather than argued:
`docs/qa/overworld-draft/embercorridor-draft.region.json` drives `tools/owdraft_{lib,layout,
cams,build,render,export}.py` to a 300x240u corridor — Emberbrook's hanging valley, the notch,
Ember Falls, the gorge, Dellhollow's lock reach. Parallel files only; ow-valley, valley_*.py,
public/world/ and both town maps were READ and not touched. Scene key ow-embercorridor-draft
is in no scene graph, no region and no chapter script. Field digest 64bb4bc0, two runs equal.

THE HEADLINE IS NOT ABOUT THE DRAFT. `public/world/world.json` (ratified 2026-07-30) and
`public/townmap/emberbrook.map.json` (redlined 2026-08-01) ALREADY CONTRADICT EACH OTHER, on
three things, and no overworld can satisfy both:
 1  THE RIVER'S SOURCE. world.json's ember-falls: "the river is BORN at the gatewall's foot,
    beside the Old Gate"; valley.region's road doc: "upstream of the source there is no river."
    The town map has an authored river course THROUGH the village with banks 10-13 m, and its
    stamped tail pulls the channel "against the gate's east side so GATE + WATER fill the notch
    together (the water-gap reading ... barred water-arch at the cleft floor per concept C)".
    Under world.json there is no water above the gate and the hanging-valley premise is void
    before it starts; under the town map the water gap is already canon.
 2  WHICH SIDE THE GATE IS ON. world.json: whisperwood-entrance [76,145] NW of the town
    [98,127], old-gate [115,115] SE of it. Town map: arrival-clearing local [52,-28] SOUTH,
    sigil-gate [76,82] — 110 m NORTH. townAnchors rotationDeg is 0, so town north IS world
    north; there is no rotation to hide behind. A ~180 degree flip.
 3  DOWNSTREAM HEADING. world spine [120,107] -> [268,28], exits SE. Emberbrook: "south-to-north
    (downstream ... beyond the Old Gate)". Dellhollow's own units line: "x = along-gorge
    (downstream/NORTH positive)". Both towns say north, independently. Dellhollow's -33 deg
    anchor rotation cannot close a ~130 deg gap.
The draft takes the TOWN maps' side and says so in every artifact.

TENSIONS (coexist, but a ratified number moves): Emberbrook as a farmed valley vs a r14 clearing
in dense canopy; road fall gate->Dellhollow 12u shipped vs 16.5u draft, and river 19u vs 27.4u
of which 8.5u is a free plunge — the totals are close, the CAUSE is not (shipped incises the
river below a bench; the draft drops it off a lip); every compass word in valley.region ("SW
bench", "NE far wall") breaks when the river turns north, though every RELATION survives; and
the corridor needs 300x240u against the ratified 280x200 envelope.

WHAT BUILDING IT TAUGHT, that arguing it could not:
 -  A V-SHAPED GORGE OFFERS NO BENCH. The first road was authored with z's and came out either
    15u in the air or 12u inside the hillside; measured, the land at the road's offsets stands
    20-23u above the water. The ledge has to be CARVED — which is exactly what valley.region
    already does (canyon.shelf width 6.0, backRise 22.0). The draft now carves a 3.4u half-width
    shelf with a 7u back run and a 2.6u outer edge, and the cross-section reads: flat ledge at
    h16, wall to h50 on the traveller's right, ground falling to h9 toward the water.
 -  THIS GEOGRAPHY HIDES ITSELF, and every camera in the brief had to move because of it.
    (a) No aerial from the south sees the corridor at ANY height — an unbroken range hides its
    own gorge; raising the eye moves the block along the crest rather than clearing it. The only
    working world-map view looks straight DOWN the corridor axis, through the gap.
    (b) From the Old Gate: 52u of gorge, then it bends. Dellhollow is 90u on, round two turns.
    (c) From Dellhollow: a search of every standable point in a 34x36u block (ground h5..44)
    found NOT ONE with a line to the notch, Ember Falls or the upper gorge. The notch needs an
    eye 55.5u — 38 character heights — above the Valley Gate.
    Good for Ch2's "Vesper's map is already wrong"; it costs the Old Gate as a look-back
    landmark. The rim-vista beat is unaffected (the road still arrives above the town).
 -  THE NOTCH IS A SLOT AND THAT COSTS THE SHOT. Walls rise 24u within 14u of the water; at road
    height the view down the gorge is rock. The camera needed 9u of lift (six character heights)
    before the gorge read. Widening the gap from r7.5 to r10 and stretching riseDist 9->14 helped
    and did not fix it. A walker's-eye "look what's below us" at the gate needs a wider notch or
    the falls moved downstream of it — four numbers in the river spec.
 -  THE GATE MASSING WAS WRONG UNTIL THE MAP SAID SO. Built first as a barred water ARCH with
    the road on the channel centre; mid-build the coordinator stamped 188a329 ("the water passage
    is NOT an arch — arches are for humans; a low culvert grate at water level, plain coursed
    masonry above; only the road's doorway is arched"). Rebuilt as ONE wall across the pinch with
    the road's doorway 4.5u EAST of the water passage, and the bench's first offset moved 0 -> 4.5
    so the road goes through the door instead of into the grate.
 -  TWO BLOCKOUT ARTEFACTS WORTH REMEMBERING. A terrace that goes dead FLAT past its shoulder is
    determined only by which river vertex is nearest, and hillshades as radiating facets — it
    needs a gentle continued climb. And an outer-hills term ADDED after the ridges cuts hard
    blades through them; applied to the terrace BEFORE them it does not. A 3u-wavelength noise
    octave on a near-vertical gorge wall renders as corduroy, not rock; damped 0.18 -> 0.07.

HONEST VERDICT (reported, not decided): the water gap is not a new idea — the user's own
2026-08-01 redlines and the chosen concept art already commit to it, and world.json is the
outlier. Recommend keeping the water gap and SOFTENING the vertical (broad valley behind a lower
pass, falls a little downstream of the gate) — it keeps the image and gets the sight lines back.

DELIVERED: docs/qa/overworld-draft/ (draft map JSON, embercorridor_layout.png = plan + long
section, aerial / fromgate / fromdell / gatehero renders); tools/owdraft_*.py (5 tools);
tools/blends/owdraft-embercorridor.blend; public/assets/scenes/ow-embercorridor-draft/ (4.8 MB,
unwired). Review artifact for the phone: https://claude.ai/code/artifact/1d106727-44c8-4688-93bf-7578b1c3af0d

## MINI-ROUND 2b — THE NOTCH, SEALED: a bottleneck that is now a measurement, three
## instruments that had never been asked the question, and a map stamp that broke the
## build (2026-08-01, builder's lane)

THE BUILD WAS RED AT HEAD AND THAT IS THE FIRST THING TO SAY. The river tail stamped in
5a46a2b put `forest-trailhead` 3.0 m INSIDE the channel and its walk pad 3.9 m under the
water, and `emb_blockout.py` failed outright on its own river-clearance assert. Nobody had
run it since the stamp. A map edit that moves water past a landmark is a build change, and
the only reason it looked safe is that the instrument that would have said so runs in a
tool nobody re-ran. RE-SNAPPED (map, flagged for coordinator ratification): 7.00 m back
along its own edge to (83.3, 76.1), the first offset clearing the water by 4.5 m — it
lands at 4.79 m, 7.56 m from the court's centre, so the stile is now a THRESHOLD on the
court's east rim and the edge's [84, 76.8] waypoint is withdrawn as an overshoot. That the
Whisperwood trail now leaves from the court's own rim rather than from open ground beside
the river is a DESIGN change, not just a move, and it wants a yes or a restamp.

THE SEAL IS SIX FACTS ACROSS ONE LINE, and all six are derived: living rock, the gate's
west curtain wall, the doorway, its founded east wall, the wall carried on over the
channel on a low grate, living rock. Measured, and printed every run:
    walkable strip masonry -> water      0.00 m   (round 2: 9.50 m of dry ground)
    walkable strip masonry -> rock       0.00 m
    the walk network stops               1.70 m SHORT of the pinch line
    flood fill from the gate court       0 m2 of the gorge behind the gate is reachable
    the channel crosses the line         9.35 to 21.85 m out — a 12.50 m water gap, spanned
                                         by 11.50 m of grate under one unbroken run of wall
THE PINCH LINE IS THE GATE'S OWN, not the town's. Round 2 took the funnel's axis from the
town CENTRE through the gate, which runs 23 degrees off the way the gate actually faces —
so its eastern chain stepped south-EAST back into the valley, its river guard refused the
one mass that mattered, and its two chains were printed under each other's names. The axis
is now the reverse of the lane that arrives at the gate, and WHICH FLANK THE WATER IS ON IS
ASKED, NOT NAMED: the perpendicular that fell out of the gate's facing points west, so the
first version of this block hard-coded "east", searched the wrong half of the valley and
asserted that the river never crosses the pinch at all.

THE USER'S OWN REFERENCE ARRIVED MID-ROUND (59d67c3/188a329/788a407) AND CHANGED THE
ANSWER. Not a water-arch beside the gate: ONE structure spanning the whole notch, twin
doors over the road, the river running UNDER the same masonry through a LOW grate at the
waterline with plain coursed wall above it — "arches are for humans". That is a better seal
than the one being built, because it leaves no water gap in the barrier at all. Built to it.
NOTE FOR THE COORDINATOR: docs/qa/emberbrook/concepts/gate-final.png puts the channel
IMMEDIATELY beside the road behind a kerb; the stamped tail puts 6.90 m of founded wall
between the doorway and the water and makes the channel 12.50 m wide. The seal holds at any
offset, so this is a taste question, not a defect — but the frame will not look like the
reference until the tail comes in or the bank narrows at the pinch.

FOUR THINGS THAT WERE ALREADY WRONG AND ONLY THIS ROUND'S QUESTION COULD FIND:
 1  THE GATE COURT LAPPED PAST THE GATE. It is an r10 disc centred 8 m inside the gate, so
    its own floor stood 1.3 m NORTH of the bottleneck on both flanks, and poked THROUGH the
    doorway besides — `foot_rect` cuts the floor to the gate's 4.6 x 1.6 massing, which is
    thinner than the wall it now stands in. The curtain walls and the gate's own bay are
    derived BEFORE the area floors precisely so they can be holes in them.
 2  THE COURT'S EAST RIM STOOD 2.21 m OFF THE STAMPED CHANNEL, inside the build's own 3.0 m
    river-clearance rule. It had never failed, because until the tail moved, a landmark pad
    failed first and masked it. An area floor may not reach the river bank: 24 cells given
    back, and the rule is in the loop now.
 3  TWENTY-ONE INFILL HOUSEHOLDS STOOD OUTSIDE THE VALLEY. The seed grid runs to the anchor
    box plus 16 m, which at 2x is 24 m beyond the Old Gate; 152 candidate seeds fell in
    ground the terrain ruling makes a mountain range. 51 households -> 30. THIS IS VISIBLE
    AND IT IS ON THE BOARD: roofs-in-sight from the lanes fell from 84% to 73% of samples
    meeting the 2+ target, median 4 -> 3 within 35 m. Correct — they were in the gorge —
    but if the north horizon now reads thin, the density wants putting back INSIDE the
    valley, and that is a redline, not a build fix.
 4  THE ROCK TOPPED OUT BELOW THE MASONRY. `6.0 + 2.6k` is measured from each mass's own
    ground, and the ground past the pinch falls away toward the valley pan — so the crags
    beside the gate crowned at z 2.5-6.0 against a wall whose head is at 7.3, and the first
    render of the sealed notch showed a curtain wall standing PROUD of the cliffs it is
    supposed to be built into. Height now has a floor derived from the wall's own head.

A KNIFE EDGE IN A RECTANGLE TEST COST AN HOUR AND IS WORTH THE PARAGRAPH. With the
innermost masses' faces laid exactly ON the pinch line, `in_rect` rotates by the pinch
bearing, `sin(-pi)` is -1.2e-16 rather than 0, and an 18 m lever arm from the mass's centre
turns that into ~2e-15 of slop — so BOTH chains' innermost masses read as ABSENT from the
very samples the seal is measured on, and the probe reported an open notch through solid
rock. The face now stands 0.25 m proud of the line. A boundary case that a probe evaluates
exactly on the boundary is not a boundary case, it is a coin toss.

THE SEAL IS TOPOLOGICAL, NOT A STRAIGHT LINE, and the gate says so. The chains stand on the
pinch line for three masses each and then rake back out of the valley 3.0 m a step, so the
range pulls away from Home Row instead of looming along the top of it (round 2's defect) —
which means the LINE itself reopens 48 m out west and 61 m east, and 396 m2 of dead-end
ground behind the range's shoulders is reachable from the valley. That is a broken
shoulder, not a bypass: it carries no walk surface and the fill cannot get from it to the
gorge. So the assertion is on the road the gate exists to close, not on a tidier number.

ROUND 2's Q4 DISSOLVES UNDER MEASUREMENT, which is the argument for costing a question
before escalating it. "smokehouse and watermill stand inside authored water extents" was
one note covering four different waters. Attributed AT CUT TIME (counting the built mesh
finds nothing — those cells have already been cut):
    smokehouse x pond      ONE cell. The r9 rim reaches 0.08 m into a 3.9 x 3.3 m footprint.
                           MAP LINE A: move smokehouse 0.58 m out -> (83.38, 43.59).
                           MAP LINE B: pond r9.0 -> r8.42. Either leaves 0.50 m of shore.
    watermill  x millpond  FOUR cells of the impoundment THIS BUILD DERIVES from the 2.00 m
                           dam ruling. Not authored, not a map question: a mill that does
                           not touch its own pound is the defect.
The note now names the water and only offers map lines for the one that has them.

GATES. Deterministic, TWO RUNS identical (digest 348d04ae). COVERAGE asserted in the build.
Walk QA over the whole town 8 844 samples, 96.85% land on a walk mesh (round 2: 96.87% over
9 048 — the delta is the trailhead's pad and its swallowed ribbon). geometry_audit 59
intersections / 29 strays, DOWN from 61/43, and the seal's own three entries are all the
already-accepted class: masonry standing in its own channel (like the mill's leat in its
pound) and a coping face-touching the next coping at 0.00 m depth. Lamps still 14. 1 812
objects, 118 775 verts. emb-townwalk re-exported atomically, 11.2 -> 10.8 MB.

DELIVERED: tools/emb_blockout.py (THE SEAL derived before the floors, the curtain walls and
grate, the re-snapped chains, three seal instruments, the area-floor bank rule, the water
attribution); public/townmap/emberbrook.map.json (trailhead re-snap + waypoint withdrawal,
BOTH pending ratification); tools/blends/emberbrook-master.blend; two new board frames
(gatefield-seal, gatefield-seal-aerial) and the watermill frame annotated as the user taste
item it is; public/assets/scenes/emb-townwalk/ re-exported, spawn unchanged.

## OVERWORLD DRAFT ROUND 2 — user feedback on the Ember Corridor (still a proposal, still not canon)

The user reviewed the corridor draft and gave three notes, all now built. NOTE FOR THE
COORDINATOR: the feedback was sent to this lane by accident and is relayed verbatim to main;
it may rule on lanes beyond this one. This lane is PAUSED after this entry pending sequencing.

 1  THE RIVER MUST NOT STOP AT DELLHOLLOW — it runs on "quite a bit more" and eventually opens
    into the OCEAN. Four points added below the Moorage: the gorge opens, walls stand back,
    channel 18u -> 28u, and the water leaves the tile's NE corner still widening. The COAST was
    deliberately NOT put on the tile — STORY §5 has Ch2 ending northbound up the Long Reach and
    Ch3 at Lanternstead, so a coastline 60u past Dellhollow would say the lock-town is a day
    from the sea. Instead the layout sheet gained a third panel: a RIVER-LINE SCHEMATIC of the
    whole course (headwaters, Emberbrook, the bridge, the Old Gate + Ember Falls, the gorge,
    Dellhollow, the Moorage, the Long Reach, Lanternstead, broadening, estuary, ocean) with a
    bracket marking how little of it is drafted. Flagged to the user as a judgement call.
 2  NO BARE COLLAR BETWEEN VILLAGE AND WOOD — "the trees should flow right up to the edge of
    the village and claim any unclaimed space". The canopy is now a COMPLEMENT, not a shape:
    it fills the valley stamp except where something else has a claim (fields, the town
    impression, the lanes, the water). The field system was also pulled in tight — it had been
    a 45x60u sprawl reading as farmland to the horizon. AND WHERE THE WOOD STOPS NOW HAS A
    REASON: a treeline (h40 -> h53) plus a noise term, because the first cut ended the forest
    on the straight edge of its own stamp polygon and it read exactly like that.
 3  THE BRIDGE MOVES OFF THE OLD GATE to beside the village: leave Emberbrook, cross, hug the
    far bank to the gate. THE USER CAUGHT A REAL BUG. The road was switching banks 6u short of
    the pinch — not a design choice, fallout from re-siting the gate's doorway east last round,
    and NOTHING IN THE PIPELINE WAS CHECKING FOR IT. Now: west bank through the village, the
    VILLAGE BRIDGE at s=70 in the open valley, then the east bank all the way to the gate,
    arriving on the side the doorway is already on. The deck follows the ROAD's direction, not
    the river's perpendicular (the first version squared it to the flow and the carriageway
    crossed it at an angle). owdraft_cams.py now has a BANK-CHANGE CHECK: it counts every place
    the road changes side, matches each against a declared bridge landmark and the deck's own
    reach, and shouts if the counts differ. Currently: 1 bank change, 1 bridge, ON THE DECK.

OPEN QUESTIONS PUT TO THE USER (in the artifact, unanswered):
 -  THE TOWN MAP PUTS THE OLD GATE ON THE WEST BANK. gate-court [76,74] and sigil-gate [76,82];
    the town map's own river runs x~92-95 at that latitude, so the gate stands ~19 m WEST of
    the water, same bank as the village. The user's ruling arrives at the gate on the EAST bank.
    Both can hold only if THE BRIDGE SITS INSIDE THE TOWN MAP and the gate court moves to the
    water's east side. Supporting: the town map's downstream-vista [108,88] is already on the
    east bank with no way to reach it — a bridge gives it one. COORDINATOR: this is a town-map
    change and therefore yours, not mine.
 -  A BRIDGE MAKES "crossings: NONE" FALSE. valley.region.json: "none possible ... Dellhollow's
    dam crest is the only span of the river in the world so far." Upstream of the gorge a span
    is easy, so it is an amendment not a contradiction — but it spends a piece of Dellhollow's
    scale-setting.
 -  FIELDS VS FOREST pull apart at overworld scale ("a valley farming settlement" vs "the wood
    claims every unclaimed acre"). Settled as a tight farmed collar in near-continuous canopy,
    which matches valley.region's "warm-lit clearing town"; the cost is that Emberbrook reads
    as a CLEARING more than a farming valley from the air. Two polygons to reverse.
 -  THE TILE NOW HANDS THE NEXT REGION A 28u RIVER. world.json's spine ends at 22u with
    continues:true; that last point wants updating if the corridor is adopted.
 -  THE THREE BLOCKING CONTRADICTIONS FROM ROUND 1 ARE UNTOUCHED by this feedback: whether the
    river exists above the Old Gate, which side of the village the gate is on, and whether
    downstream is north or south-east. Everything here rests on them.

Field digest 744bb487 (two runs equal). Bundle 5.6 MB, still unwired. Renders: aerial, village,
bridge, gatehero, fromgate, fromdell. Artifact updated in place:
https://claude.ai/code/artifact/1d106727-44c8-4688-93bf-7578b1c3af0d

## WORLD CANON RESTAMP — the geography now tells ONE story (2026-08-01, world lane)

THE THREE BLOCKING CONTRADICTIONS FROM THE OVERWORLD DRAFT ARE CLOSED, and they were
closed by moving `public/world/`, not the towns. The user ratified the corridor's premise
("I like that the river starts deep in the Wispr Wood and courses through Emberbrook
village before crossing the old gate and opening out at Dellhollow... The river should
continue flowing further on for quite a bit more and then eventually open out into the
ocean"), and delegated the bridge question, on which the coordinator ruled: the Old Gate
STAYS on the village's own west bank as built, there is NO village bridge and no new
bridge anywhere, the party descends the gorge on the WEST side, and the game's one river
crossing is Dellhollow's dam crest. Both files restamped in one commit so no commit is
ever internally inconsistent; the town maps were READ and NOT touched.

 1  THE SOURCE MOVED, AND WITH IT THE WHOLE PREMISE. The river is born at [106,26,29.4],
    the springs deep in the south Whisperwood at the foot of the south rim, and runs
    NORTH to the village. `ember-falls`' "the river is born at the gatewall's foot" and
    the road doc's "upstream of the source there is no river" are both dead. EMBER FALLS
    EARNED ITS KEEP rather than being deleted: it is now the plunge off the sill at the
    gatewall's foot, [96,82,17], the head of the gorge and 11u below the Old Gate — a
    6.8u free drop in the reach after the notch. The id is unchanged because
    valley_layout.py and owdraft_export.py both read it by name.
 2  DOWNSTREAM IS NORTH, THEN NORTH-EAST. Every spine step now increases y. The village
    reach flows due north, which is what makes Emberbrook's `rotationDeg: 0` TRUE instead
    of a 180-degree lie — town north really is world north, so the arrival reads south
    (entrance [84,24], 24u below the village) and the gate reads north (old-gate [92,72],
    24u above it). Dellhollow's local downstream heading measures 33 degrees and its
    anchor rotation is restamped -33 -> +33 to match it exactly.
 3  ONE BANK, THE WHOLE WAY. benchSide SW -> W: with the river turned north-east the
    traversable bench is the WEST bank, which is the LEFT bank looking downstream — the
    village's bank, the Old Gate's bank, and Dellhollow's. The far wall moved to the EAST
    (right) bank, Hollowmere Pass to the NORTH rim, the crag stamps and the farwall-crown
    canopy with them. The road is authored as a constant left-hand offset from the water:
    16 points, all one side, and the minimum road-to-water gap is 1.0u — which is the
    gate's own pinch, where the arched doorway stands beside the low water grate, exactly
    as mini-round 2b sealed it.

THE LINE THAT SURVIVED WHOLE. `crossings._doc` — "NONE — and none possible: the canyon
geometry enforces it. Dellhollow's dam crest is the only span of the river in the world
so far." — is byte-for-byte untouched, and an asserted check keeps it that way. A SIBLING
note now says the road never needs a crossing (west wall all the way, river on the
traveller's right), and that where it DOES cross is the dam crest — `dam-crest-gate` in
dellhollow.map.json — which makes the world's only span the FIRST CROSSING OF THE GAME,
barred shut this chapter. Draft round 2's open question "a bridge makes crossings: NONE
false" is therefore answered by there being no bridge, and Dellhollow's scale-setting is
not spent.

THE HANDOFF THE DRAFT ASKED FOR. The spine ends 28u wide at [244,190] with
`continues: true`, the region exit carries 28u (was 22u), and the note says only what the
user asked: the river runs on for days yet to an estuary and the sea, SCHEMATIC and
late-game, with no coast drawn on this tile — STORY §5 still gets Ch2 northbound up the
Long Reach and Ch3 at Lanternstead before any water widens into salt.

TWO THINGS FLAGGED AND DELIBERATELY NOT FIXED, because they are not this lane's files:
 -  `tools/valley_map.py` HARDCODES THE BENCH TO THE RIGHT BANK (`sideL == 0`, with the
    comment naming the Dellhollow master's chirality). The restamp makes the bench the
    LEFT bank, so the tool must be made to read `elevation.canyon.benchSide` BEFORE
    ow-valley is rebuilt or the canyon gets carved the wrong way round — a silent,
    plausible-looking wrong, which is the worst kind. Written into the region file as
    `_doc_benchSide` so the next builder cannot miss it.
 -  DELLHOLLOW'S TOWN MAP CONTRADICTS ITSELF ON COMPASS, and always did: its units line
    says "x = along-gorge (downstream/NORTH positive)" while its own `river.gorge` calls
    the y=0 wall "near (south)". Those cannot both be compass claims in a right-handed
    frame. Read as LOCAL axis labels they are harmless and the anchor supersedes them,
    which is how the region file now records it. The town lane may want to restate that
    one line; the geometry needs nothing.

THE TOWN-MAP SURGERY THE HANDOVER WARNED ABOUT HAS NOT LANDED, AND NO LONGER SHOULD.
Read at this end: emberbrook.map.json still has `gate-court` at [76,74] with the river
course at x~90 at that latitude — the gate on the village's WEST bank — and the only
landmark with "bridge" in its name is `brook-bridge`, the plank over the village brook.
That is the coordinator's ruling already satisfied by doing nothing, so the checks that
were waiting on the east-bank gate court and the village bridge are not pending: they
PASS as withdrawn.

VERIFIED. `node tools/worldmap_validate.mjs` PASSED with 0 errors and 0 warnings (spine
descends over 18 points, navigable widths hold from the "below the locks" point,
containment, refined river within 3.1u of the spine against a tolerance of 8, spine fully
covered at 0.0u, 15 road segments all under 12 degrees, portals on the road). On top of
that, 48 cross-file assertions across world.json + valley.region.json +
emberbrook.map.json + dellhollow.map.json + embercorridor-draft.region.json — source,
headings, banks, compass sides, the falls, the handoff and the bridge — all pass.

WHAT THIS COSTS: the built `ow-valley` tile is now WRONG EVERYWHERE, not subtly wrong.
Every landmark moved, the corridor runs the other way across the tile, and the bench is
on the other side of the water. `public/assets/scenes/ow-valley/` and its zones are stale
until the valley tools are re-run — after the benchSide fix above. No scene, script or
scene-graph entry was edited here.

## THE CHIRALITY FOLLOW-UP — a hardcoded bank, a gate standing in its own river, and a
## fast loop that had already baked both (2026-08-01, world lane)

THE LOOP WAS THE URGENT PART. `tools/townwalk_live_refresh.sh` rebuilds ow-valley
whenever the map JSONs change (armed by `tools/.fastloop`), so the restamp fired it
within minutes and it baked a tile with the canyon carved on the wrong bank. Nothing was
broken enough to fail: `valley_verify` passed, the GLB exported, the zone grid looked
sane. The only thing in the whole pipeline that KNEW was a number nobody reads —
`road_pushed_stations: 12` in valley_build.json.

 1  THE BENCH IS NOW RESOLVED, NOT ASSUMED. `valley_map.py` hardcoded the bench to the
    RIGHT bank (`sideL == 0`) and cited "the Dellhollow master's chirality" as the
    reason, which was true only while the river ran south-east. It now resolves the side
    TWICE and requires the two answers to agree: (a) `elevation.canyon.benchSide` as a
    compass word, dotted against the river's arc-length mean downstream heading — letters
    are summed so N/NE/NNE all work, `left`/`right` are taken verbatim, and a word within
    ~15 degrees of the flow raises because it does not name a bank; (b) which side of the
    water the ROAD actually runs on, one vote per station and only stations within 25u of
    the channel voting. Disagreement raises with both readings and the vote split. The
    old `sideL` keeps its meaning; new `sideB`/`sideF` carry bench and far wall, and all
    three consumers read those.
    REGRESSION: the pre-restamp map still resolves RIGHT, so the change is a no-op for
    the old canon — and it now REPORTS what that map hid, that 3 of its 14 near-water
    road stations sat on the far bank from the other 11. That is the hairpin bank-change
    the old comment block called a conflict "reported, not edited"; it was live in the
    shipped map for as long as the map existed.
 2  THE OLD GATE WAS STANDING IN THE RIVER, and it was my own restamp that put it there.
    Stamped at [92,72] it sat 1.0u from a 4.5u-wide channel's CENTRELINE — inside the
    water — and the clearance pass had been quietly nudging twelve road stations out of
    it every build. THAT IS THE SAME CLASS OF BUG AS MINI-ROUND 2b's trailhead-in-the-
    channel, and it survived a validator pass, 48 cross-file assertions and a review,
    because every one of those instruments asked about TOPOLOGY (which bank, which side,
    which direction) and none asked the metric question: is there dry ground under it.
    Re-seated at [88,72]: 5.0u off the centreline, 2.76u of dry founded ground between
    doorway and water's edge — which is the Emberbrook town map's own round-3 geometry at
    overworld scale (~3.1 m of founded wall, channel running due north through the gap
    parallel to the road). Pushed stations 12 -> 0. The gatewall spur and the Whisperwood
    highland stamp moved 4u with it so the gate sits inside its wall, not on its lip.
 3  AND THE WAYSTONE CAME OFF ITS ROAD when the gate moved west — 1.2u out of a 2.0u
    ribbon, which `valley_verify` catches by name because it probes that landmark's zone
    cell. Snapped to [88.8,88.1,23.3]. This is the third time a coordinate has moved and
    dragged a landmark off its surface, and the pattern is worth naming: A LANDMARK PINNED
    TO A LINE MUST BE RE-SNAPPED WHENEVER THE LINE MOVES, and the only reason it keeps
    getting caught is that somebody wrote the probe.

HANDEDNESS MEASURED ON THE BUILT FIELD, which is the only place it is real. Nine stations
down the corridor, sampled 14u either side of the channel: the west bank stands 6.3..12.5u
above the water and the east 17.3..24.7u, with the wall 6.0..17.3u above the bench through
the gorge. The last station, past the Moorage, comes out 0.6u asymmetric — the walls have
stood back, which is exactly what the Long Reach is supposed to do, and the probe treats
an open reach as "not a bank test" rather than a failure. The road: 0 pushed, 0 spans,
closest approach 5.01u at the gate.

THE LOOP REPRODUCES IT. `townwalk_live_refresh.sh` run once: scene.glb and zones.json
sha256-identical to the manual rebuild, every geometry field in valley_build.json equal
(tris, meshes, trees, outcrops, h_range, lattice, zone_cells, pushed, spans), and only
wall-clock timings differing. `.last_map_mtime` now equals the newest map mtime, so the
tick is quiet until the map moves again.

WHAT I WOULD TELL THE NEXT LANE: the instruments that caught all three of these were the
ones that ask the BUILD a question, not the ones that ask the map. `worldmap_validate`
was green through every version of this, including the one with a gate underwater.

## DELLHOLLOW NAV CUSTODIAN — THE LOOP STAIRS: THE QUAY FLIGHT IS DRAWN, LIT, FRAMED,
## 72% VISIBLE AND UNWALKABLE. NOTHING WAS CHANGED, AND THAT IS THE FINDING.
## (2026-07-31, loop-stairs lane)

USER, LIVE PLAY: "the stairs are still pretty hard to navigate... the loop stairs, right
above the Weave, going down from the street with the various shops down to the Weave."

THE ANSWER IS ONE OBJECT AND ONE NUMBER. `walk_e_shelf-homes__market-stalls_l0_t00` —
the market flight's FIRST tread, a 0.82 m flat run at yard level (x 51.80..52.62,
up 18.93..19.07) — stands 0.36 m and 0.72 m ABOVE `..._quay-deck_l0_t01` and `_l0_t02`.
play3d.html's `walkGround` returns the HIGHEST walk surface in [fy-0.9, fy+0.73]. Both
gaps are inside that window, so those two treads can never win a foot. The head of the
quay flight is not standable, and the flight behind it is therefore not enterable.

MEASURED, and the descent trace is the whole report in one block. Stand on the quay
flight's own top tread and push straight down its own line (tools/ls_nav_probe.mjs):
    step  0- 2   up 19.07   walk_e_shelf-homes__quay-deck_l0_t00
    step  3- 9   up 19.07   walk_e_shelf-homes__market-stalls_l0_t00   <- the other flight
    step 10-20   up 18.75   walk_e_shelf-homes__market-stalls_l0_t01
    step 21-31   up 18.43   walk_e_shelf-homes__market-stalls_l0_t02
    ...          3 steps on flight A, 57 on flight B, 0 elsewhere
The quay flight's own tread heights (18.71 / 18.35 / 17.99 / 17.63) are never touched.
Census on a 0.05 m lattice: 159 of 5273 quay-ribbon cells covered (3.0%), patch
x 52.00..52.40 / map y 8.34..9.54, gap 0.360..0.720 m against the 0.73 m window. It is
3% of the ribbon and it is 100% of the problem, because it is the ENTRANCE.
HELD-HEADING SWEEP from the shot's own arrival [53.2, 18.75, -9.48], 72 headings:
quay foot 0/72 (closest 4.51 m), market foot 12/72. CONFIRMED IN THE SHIPPED GAME, not
just offline — play3d.html in a browser, ?nomusic=1, SIM.tp + SIM.move, 72 headings with
the real body box and the real seams firing: quay foot 0/72, market foot 1/72. Live is
STRICTER than the offline probe, which is the right direction for an instrument to err.

THE THIRD INSTRUMENT WAS ALREADY ON THE TREE SAYING SO AND WE HAD FILED IT AS OUR OWN
WALKER'S FAULT. nav_eval `--judge oracle-world` — the town's OWN ground-truth route, no
perception involved — scores loop-stairs 0.00 in all three oracle runs
(run-ow-check-0031, run-ow-truearrivals, run-20260731-025016). seam-canon 10.3 rule 1
names this exact mechanism ("the market flight's top tread covers the head of the quay
flight ... the walker descends a legitimate but different flight") and classifies it as
the WALKER being pessimistic. It is not pessimism. The "different flight" is the only
flight a player can take, and rule 1's exemption should be struck: the oracle was right
and we explained it away. ONE LINE OF CANON TO AMEND, flagged to the coordinator.

FOUR CANDIDATES REFUTED WITH ARITHMETIC, so the fix is not bought in the wrong layer:
  VISIBILITY.  shot_probe.py against the SHIPPED plates: loop-stairs sees
     shelf-homes__quay-deck 100.0% on-screen / 72.0% VISIBLE and
     shelf-homes__market-stalls 100.0% / 80.5%. quay-west sees both at 64.6%. For scale,
     the gate stair that ate last night's campaign was 14.6% -> 29.3%. This is the best
     stair visibility in the town. There is no re-aim to buy and none was proposed.
  READINGS.   The pinned judge scores loop-stairs 1.00 (run-newbake, run-cal-oldbake) and
     0.80 (run-patchbake, run-20260730-234241) — at or above 10.2's 0.6 gate on four
     bakes, onWalkFrac 0.905..1.000, wentBack 0. The naive reading aims AT the stairs and
     leaves onward. N=10 NOT RUN: 10.2's gate is already cleared and the budget buys
     nothing a passing shot needs. ~20 trials saved.
  STAIR ART.  ls_treads / ls_frame / ls_rail are in the shipped bundle. Art-void census
     (no rendered up-face within 0.45 m under the ribbon): quay 35.3%, market 32.5%,
     against the deep-stairs control at 46.5%. Not the Keepers'-Steps disease. ONE
     OUTLIER IS REPORTED, not fixed: 16.7% of the quay ribbon carries rendered geometry
     ABOVE the walk surface (worst +1.74 m; qm_stair_underworks 103 samples, the market
     flight's own ls_treads 50, shelf_ground 29, qm_revetment 29) against 0.1% on the
     market flight and 1.0% on the deep stairs. That is the 918-face block mass ls_build
     left standing (22:40 entry) and it belongs with the quay-tier plinth decision.
  SEAM CHURN. Not a control flip: both cuts are loop-stairs -> quay-west, yaw 104 -> 107,
     a 3 degree change. The quay-flight seam (runtime up 15.23) sits ON
     walk_e_shelf-homes__quay-deck_landing.001 (up 15.14..15.30) — a threshold, canon 4.
     THE MARKET-FLIGHT SEAM DOES NOT: up 16.28, mid-flight between the landings at
     17.24..17.40 and 15.14..15.30, ~1.0 m clear of each. A real canon-4 miss, recorded
     and NOT fixed — moving it needs an authored @t split, a re-solve and TWO bakes
     (cine_test asserts baked == solved), and it cannot make the quay flight enterable.
     Spending a bake on a number that does not move the defect is exactly last night's
     lesson; it is filed for whoever is baking loop-stairs and quay-west next anyway.

WHY IT IS NOT MINE TO FIX, WITH THE ARITHMETIC. The overlap is forced by the map:
    shelf-homes__quay-deck      first leg 1.811 m of ground for 1.800 m of fall = 44.8 deg
    shelf-homes__market-stalls  first leg 5.100 m of ground for 1.600 m of fall = 17.4 deg
    plan bearings 6.34 degrees apart, from ONE shared origin (landmark shelf-homes)
Two flights leaving one point on one bearing at gradients 27 degrees apart MUST overlap
in plan, and the shallow one's first tread then stands over the steep one inside the
0.73 m window. And the yard cannot hold both heads side by side either:
    walk_pad_shelf-homes                      2.60 x 2.60 m
    quay head   walk_e_..._quay-deck_l0_t00      1.43 m wide
    market head walk_e_..._market-stalls_l0_t00  1.40 m wide
    two heads need 2.83 m across a 2.60 m pad -> SHORT BY 0.23 m before any margin.
CLAUDE.md's own doctrine: "a conflict fix is a landmark move or a lane waypoint — one
line of map, one command to re-derive. Never re-cut floors in a district builder." The
town maps are coordinator-owned, so this STOPS here and joins task #24's class. NOTHING
IN THIS LANE'S REMIT REACHES IT: stair art sits 30 mm under a ribbon it cannot move, a
camera cannot change which surface catches a foot, arrivals cannot widen a yard, and a
seam move cannot make a covered tread standable. THREE MAP OPTIONS, costed, none taken:
  (a) widen walk_pad_shelf-homes to >= 3.1 m across and give the quay edge a flat first
      waypoint on the yard's south rim before it descends — needs 0.5 m the shelf may
      not have against the gorge; measure before stamping;
  (b) re-origin shelf-homes__quay-deck onto the market flight's FIRST LANDING
      (walk_e_..._market-stalls_landing, up 17.24..17.40, x 54.90..56.90) so the town has
      one stair that forks once, lower down, on a 2.0 x 2.0 m landing instead of a fork
      at the head of a 45 degree flight. Cheapest in geometry, biggest in composition —
      the shot's whole premise is "TWO flights leaving one yard";
  (c) shallow the quay edge's first leg toward the market's 17 deg. Costs the drama and
      probably does not fit the tier.
NO PLAY3D EDIT AND NO EMBERBROOK FILE WAS TOUCHED. Two lanes were live in the tree
throughout (emberbrook.map.json, ow-valley/*, emb_blockout.py) and every commit below is
a strict pathspec containing none of them.

GATES, REPORTED AS FOUND RATHER THAN AS WANTED. I changed no derived data, no geometry
and no camera, so every gate reads exactly as it does at HEAD ce01b0b:
    seam_test 294/0 (+3 soft) · seam_walk 9/9 · routes_derive --check CLEAN
    plate_flat clean, 0 of 16 · cine_test 641 ok / 1 FAIL · slice_test 735 ok / 5 FAIL
THE SIX REDS ARE NOT DELLHOLLOW'S AND NOT MINE, and they are attributed rather than
waved past: cine_test's single failure is "scenegraph.json is STALE" — scenegraph.json
is 05:53, emberbrook.map.json is 13:06 and uncommitted by the Emberbrook lane, while
dellhollow.map.json has not moved since 07-30 14:22; slice_test's five are the same
staleness plus four ow-valley trigger/arrival failures against the overworld lane's
rebuilt ow-valley/scene.glb. Re-deriving would fold another lane's in-flight map into
the shipped scenegraph, which is theirs to do and not mine. geometry_audit NOT RUN: it
needs Blender and this lane added no geometry (one read-only .mjs and two annotated
PNGs), so a launch on a machine two rendering lanes are using buys nothing.

DELIVERED: tools/ls_nav_probe.mjs (the covered-tread census, the tread-by-tread descent,
the held-heading sweep, the pad-width budget and the map's own gradients — reads only the
shipped bundle, no Blender, no API, seconds; takes any two flights leaving one point, so
Emberbrook gets it free); docs/qa/districts/loopstairs_head_overlap_{loop-stairs,
quay-west}.png (the SHIPPED plates annotated with both ribbons and the unstandable treads
in red — no re-bake, this is the frame the player is looking at).

FOR THE NEXT LANE, THE GENERAL FORM: "in frame" != "visible" != "unobstructed ray" now
needs a fourth term. A surface can be in frame, unoccluded, big enough, correctly read by
a naive player AND STILL NOT CATCH A FOOT, because walkGround resolves height before
anything else in the frame gets a say. Every existing gate passed this staircase.

## BLOCKOUT ROUND 3 — the notch brought to the reference, a farmland ruling turned into a
## predicate, and three gates that had been reading empty lists (2026-08-01, builder's lane)

FOUR JOBS, ALL SMALL, AND THE SEAL SURVIVED ALL OF THEM. Ruling context first, because it
bounds everything below: the Old Gate STAYS where 2b sealed it, there is NO bridge in this
map, and the game's one river crossing is Dellhollow's dam crest far downstream.
`downstream-vista` is re-noted in the map as pure vista — seen from the gate side, across
the water, never reached.

THE CHANNEL, PROPOSED AND STAMPED (map `river.course`, PENDING RATIFICATION). 2b closed
with a taste note: the seal holds at any offset, but the frame will not look like
`gate-final.png` until the tail comes in or the bank narrows. Measured off the reference
image against the built doorway (4.90 m = 112 px, so 22.9 px/m): rock | 0.8 m wall | 4.5 m
of water | 3.5 m of wall | 4.9 m doorway | 1.2 m wall | rock — a 15 m notch. Built at
HEAD: 6.90 m of founded wall and a 12.50 m channel in a 28.8 m notch. THREE INSTRUMENTS
WERE COSTED OFFLINE against an exact re-implementation of the builder's own course
maths (chaikin x4, resample 1.5 m, `river_at`), and the arithmetic killed the obvious one:
 a  NARROWING THE BANK ALONE MOVES THE WATER THE WRONG WAY. Bank width 10 -> 6 with the
    course untouched takes the channel from 12.50 m to 9.25 m and pushes its NEAR edge
    from 9.35 m out to 11.20 m — the wall between doorway and water grows from 6.90 m to
    8.75 m. A constriction shrinks toward its own centreline, and the centreline was the
    problem.
 b  MOVING THE TAIL WEST WITHOUT CHANGING HOW IT CROSSES buys less than it looks. The
    channel's measured width is inflated by the CROSSING ANGLE: the wall band is 3.2 m
    thick and a course crossing it at 60 degrees sweeps 12.5 m of pinch line for a 10 m
    river. Every westward candidate stalled around 10-11 m of water.
 c  WHAT THE REFERENCE ACTUALLY DRAWS IS A CHANNEL PARALLEL TO THE ROAD. Two authored
    points became four: the course turns east of the gate court and then runs DUE NORTH
    through the gap, square to the pinch line, tapering 11 -> 9 -> 6 m and opening to 9 m
    beyond. STAMPED, and measured on the build:
        founded wall, door jamb to water    6.90 m -> 3.10 m   (reference ~3.5 m)
        channel across the pinch           12.50 m -> 7.05 m   (reference ~4.5 m)
        the notch, rock to rock             28.8 m -> 19.6 m   (reference ~15 m)
        sinuosity                           1.058 -> 1.096, tightest bend ratio 2.91
                                            (unchanged — the binding bend is 45 m away)
THE SEAL, RE-PROVEN, unchanged in every number that matters: walkable strip masonry ->
water 0.00 m, masonry -> rock 0.00 m, the walk network stops 1.70 m SHORT of the pinch
line, and the flood fill from the gate court reaches 0 m2 of the gorge behind the gate.

TWO COSTS, STATED RATHER THAN BURIED, both PENDING RATIFICATION with the tail:
 1  THE GATE COURT'S NORTH-EAST QUARTER IS NOW RIVER BANK. The area-floor rule from 2b (a
    floor may not lie within 3.5 m of the water's edge) does its job automatically: 1 135
    cells -> 915, with 244 given back to the bank against 24 before. The court is a D now,
    flattened on the water side, which is what a court squeezed between a gate, a range
    and a river IS.
 2  THE WHISPERWOOD STILE MOVED AGAIN, and the same searched rule found it: on the gate
    court's own rim radius (7.56 m, 2b's), swept from due east southward, the first offset
    clearing the water's edge by 4.5 m. -33.5 degrees, (82.30, 69.83), clearance 4.53 m.
    The RATIFIED design fact is untouched — the stile is still a threshold on the court's
    rim, the humble way out standing beside the sealed stone one; it has moved 6.4 m round
    that rim from ENE to ESE. The 2b position now stands 0.16 m from the water.

NO UNCLAIMED ACRE (map `forest._doc` FARMLAND ruling) — AND THE FIRST VERSION OF THIS PASS
WAS WRONG IN A WAY WORTH WRITING DOWN. The ruling was implemented as a PREDICATE before it
was implemented as geometry: sweep the valley at 1.5 m and call a cell unclaimed when it is
more than 8 m from forest, lane, floor, water, a household's plot, a landmark or the range.
That probe answered 21 of 9 752 samples — 47 m2 — and the parcel pass built ONE FIELD IN
THE WHOLE VALLEY and would have called it farmed. The 8 m test is the ruling's own words
and it is not the EYE's test: a cell 7 m from one tree and 7 m from a lane passes it and
still renders as lawn. So the sweep asks TWO questions per sample, and the second one
decides where a field goes: BARE — is anything standing on this ground at all.
    AND THE TOTAL BARE AREA IS STILL NOT THE ANSWER. 900 m2 spread as two hundred slivers
between hedges and cottages is texture; the same 900 m2 in one rectangle is the green void
the user objected to. The bare samples are 4-connected at 1.5 m and the number reported is
the BIGGEST PATCH:
        ground >8 m from any claimant        47 m2  ->  0 m2      (the ruling's target)
        bare ground, total                  900 m2  ->  447 m2
        biggest single bare patch           144 m2  ->  29 m2
        bare patches >= 40 m2                    5  ->  0
TEN PARCELS, and they are 16 x 9 m strips laid on the valley's OWN SPINE — the bearing from
the arrival portal to the Old Gate, derived, so a redline that moves either portal re-lays
the fields. Hedge, dry-stone or paling by the parcel's own hash, one boundary per shared
edge (never two), crop ridges or autumn stubble inside, a hay stook on every third. Twelve
further candidate strips BUILT NOTHING — something stood in every metre of them — and they
are not counted as claimed, which matters: two of the first eighteen parcels emitted zero
geometry and still claimed their acre in the report, because FIELD_RECTS was appended
before anything was drawn.

THE VALLEY HAS NO ACRE LEFT TO FARM, AND THAT IS THE ROUND'S REAL FINDING. Only ten strips
fit because round 2's forest (the container ruling) and its thirty households had already
taken the ground: of 12 190 m2 between the village and the treeline, 93% was already
claimed before this pass ran. THE TWO RULINGS PULL AGAINST EACH OTHER — "the wood swallows
the space beyond the infill clusters" and "every acre is forest or visibly worked farmland"
cannot both be maximised, and the frame shows fields reading as boundaries BETWEEN HOUSES
rather than as a farmed valley. Reported, not decided: if Emberbrook must READ as a farming
settlement, the redline is to hold the wood's inner edge further out on the west and south
margins. That is a taste call about which ruling wins, and it is the user's.

THE NORTH HORIZON, MEASURED PER DISTRICT AND THEN COSTED — no geometry was added.
Town-wide is 75% of lane samples at the 2+ roof target (2b: 73%), but a town-wide average
cannot say WHERE it thinned, so every sample is now tagged with its lane's own districts:
        lanes 100%   square 85%   homerow 73%   THE GATE FIELD 65% (median 2 within 35 m)
        entrance 64%   woodroad 12% (excluded from the ruling by design)
Then the alternative was COSTED rather than argued: a variant build with the gatefield
warmth floor raised 0.32 -> 0.58 produced AN IDENTICAL TOWN — 30 households, 65%, same
digest-relevant geometry. Instrumented, the reason is flat: 371 infill candidates fall in
the Gate Field, 254 pass the warmth gate at the raised floor, and 5 become households. The
other 249 are refused by GEOMETRY, not by probability — 85 past the pinch (the gorge), 73
leaning on a lane or floor, 54 in the river's margin, 37 too close to an existing house.
THE GATE FIELD IS FULL. The north horizon cannot be densified with roofs by any gradient
redline; what can stand on it is worked ground, which is what this round put there.

DOES THE FOREST REACH THE VILLAGE EDGE — the container ruling, verified instead of assumed.
36 rays out of the town's centre; on each, the last walk surface, the outermost thing
anybody BUILT, and the first tree crown. The wood stands 30.5 m past the last walk surface
(median) — and 3.0 m past the outermost built thing, worst 44.0 m, which is the number
the ruling is actually about: the wood presses in around the outer houses. Of 877 m of ray
between the walk edge and the wood, 116 m (13%) is bare ground, and ZERO bearings have an
unclaimed gap. THE PROBE'S OWN FIRST VERSION LIED IN THE USUAL DIRECTION: it called a tree
"reached" at 1.0 m from a trunk, and a ray slips between 2.75 m-spaced trunks for tens of
metres — it reported 34 m of open gap on bearings that run through standing wood. A crown
is 2.0-3.1 m of radius; the threshold is 3.0 m, the same number the forest's own gate uses.

THREE GATES WERE READING EMPTY LISTS, and the oldest had been doing it for two rounds:
 -  RIMFEET WAS DECLARED IN ROUND 2 AND NEVER APPENDED TO. The forest pass tests every
    candidate tree against it and printed "0 refused on a rim tree" every run since — a
    result that was really an empty list. Filled: 184 wood trees were standing inside the
    rim's own trunks and are gone. 1 722 -> 1 537 trees, and the free-roam GLB went with
    them.
 -  A PARCEL THAT BUILT NOTHING still claimed its 144 m2 in the after-sweep (above).
 -  FIELD BOUNDARIES LAY ACROSS FOUR INFILL CART TRACKS, 1.2 to 4.5 cm deep — invisible in
    any frame and caught only by geometry_audit. A track is not a walk surface, so `wdist`
    cannot see it; the tracks are their own list now and the field pass clears them.
A BOUNDARY IS A LINE, NOT A ROW OF DASHES: the first build laid 2.2 m segments at 2.4 m
centres and the review frame showed a field wall as dotted stones. 2.9 m at 2.5 m centres
overlap by 40 cm on purpose, which is why `_drystone` and `_ridge` joined geometry_audit's
SOFT_PART exactly as `_hedge` and `_pale` did in round 2.

GATES. Deterministic, TWO RUNS identical (digest c9338bd7). COVERAGE asserted in the build.
Walk QA over the whole town 8 624 samples, 96.81% land on a walk mesh (2b: 8 844 / 96.85%;
the delta is the gate court's 244 cells given back to the bank). geometry_audit 59
intersections / 28 strays against 2b's 59/29 — NO NEW CLASSES, and not one of the 87
offenders is a field parcel. Lamps still 14. 1 859 objects, 113 051 verts (2b: 1 812 /
118 775 — the rim-tree fix outweighs the fields). emb-townwalk re-exported atomically,
spawn unchanged, GLB 10.8 -> 10.3 MB.

DELIVERED: public/townmap/emberbrook.map.json (river tail tightened, forest-trailhead
re-snapped, downstream-vista re-noted — ALL THREE PENDING RATIFICATION);
tools/emb_blockout.py (the field-parcel pass and its two-question sweep, the village-edge
probe, the per-district roof census, the RIMFEET fix, the track gate);
tools/geometry_audit.py (SOFT_PART gains `_drystone` and `_ridge`);
tools/emb_rescale_shots.py (two round-3 frames — north-horizon, field-parcels — plus
`--index-only`, so the board's prose can be rewritten without re-shooting fourteen Cycles
frames); tools/blends/emberbrook-master.blend; docs/qa/emberbrook/rescale/ re-shot;
public/assets/scenes/emb-townwalk/ re-exported.

WHAT IS A DESIGN QUESTION, NOT A BUILD FIX — reported, not decided:
 1  The container ruling and the farmland ruling are in tension and Emberbrook has no acre
    left to farm (above). Only the user can say which wins.
 2  The gate court's east rim is now a 0.45 m stair-step against the river bank — the cell
    grid meeting the 3.5 m bank rule. Legible at blockout; it wants a drawn kerb at
    dressing, which is also what gate-final.png draws.
 3  The Gate Field cannot carry more households at any density setting (above).
 4  Round 2b's open items stand: the mill pound ~1.9 m proud, the village faintly visible
    from the arrival road, `road-gate__orchard` still refusing its lane incident.
 5  A dark quad reads like a hole in the ground in north-horizon.png, right of the court.
    MEASURED, not assumed: 380 downward rays over the Gate Field and the washline area all
    terminate on real geometry, 0 misses and 0 odd first hits. It is a shadow under a lane
    ribbon's edge, not a hole.
