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

## THE LOOP STAIRS, FIXED — the fork lands, and the two defects that only a BODY could
## find (2026-07-31, loop-stairs lane, closing)

RULING IMPLEMENTED: coordinator took option (b) — re-origin `shelf-homes__quay-deck`
onto the market flight's first landing — on the grounds that navigation beats
composition. Map stamped c046f51 (my proposal verbatim: a `loop-landing` portal at
[55.9, 9, 17.4], the quay edge re-origined and waypoint-free, the market edge untouched
by a character). Semantic diff verified before building: 1 landmark added, 1 edge
re-origined, 1 withdrawn, nothing else — the 45 other diff lines were \uXXXX escapes
re-serialising to literal UTF-8.

THE PREMISE THAT WAS SPENT, recorded for the shot's history as instructed. This shot was
pitched as "TWO flights leaving one yard" and it is now ONE descent that forks lower
down. The `_framing_note` carries the whole story and the arithmetic that forced it.

=== THE RESULT, in the terms the gate was written in ===
  covered-tread census   159 cells lifted 0.360..0.720 m  ->  4-6 cells at 0.640 m,
                         a 0.20 x 0.10 m sliver against a 0.60 m body: SUB-BODY
  descent trace          3 steps on the quay flight / 57 on the market  ->  58 / 0
  fork geometry          6.34 deg apart at 27.4 deg of gradient difference
                         ->  116.6 deg apart at 0.39 deg
  shot_probe VISIBLE     old flight 72.0% (loop-stairs) / 64.6% (quay-west)
                         ->  new flight 90.2% / 95.1%
  arrivals               every arrival on the descent 100%/100% body/chest, except
                         quay-west>loop-stairs at 91.2%/96.4%. The [53.2,18.75,-9.48]
                         override was RE-VERIFIED as promised and still lands 100%.
  LIVE, in the shipped game (SIM.tpY + SIM.move, real body box, seams firing, nomusic):
                         clear standing lane at the throat 0.30 m -> 0.70 m, every
                         station >= one body; descent 17.47 -> 16.71 -> 15.96 -> 15.58
                         -> 14.83 -> 14.24, ON THE HARBOUR DECK, and on across it.

=== TWO DEFECTS THE FIX ITSELF CREATED, BOTH FOUND BY INSTRUMENTS, BOTH FIXED ===
1  A HANDRAIL FENCING OFF THE WAY ON — and only the body box could see it. Every offline
   probe passed the new flight. The live walker stopped dead after two steps with 0.30 m
   of clear lane. `town_blockout` draws a `bar_` rail down each side of a stairs edge
   PER EDGE, knowing nothing about anything else that leaves; before the stamp nothing
   left the market flight's south side, so a continuous rail was right. After it, the
   quay branch leaves through it: `bar_e_shelf-homes__market-stalls_l0_railB` ran across
   the new flight's top tread, with `ls_build` dressing that same line in visible timber
   because it builds rails ON the blockout lines. AND A bar_ IS NOT NON-SOLID —
   play3d.html's `noStand` list is water_/lm_/veg_ only, so a bar_ blocks the body like a
   wall. An INVISIBLE WALL ACROSS A STAIRCASE. Fixed in `ls_reorigin.py` as a GAP, not a
   deletion (the rest of that rail is still what stops you walking off the market
   flight's south side): 5 + 1 faces cut inside the fork's own body column, snapshotted,
   revertible. Clear lane 0.30 -> 0.70 m.
2  A REDUNDANT PAD THAT COST A SEAM. `town_blockout` gives every portal landmark a
   2.60 m threshold pad; this one landed at t 0.348..0.586 of the market edge and
   swallowed that seam's whole slide window — seam_test RED with "every seam position in
   t=[0.500,0.743] overlaps another path (walk_pad_loop-landing)", which canon §5 ranks a
   FAILURE: a player stepping onto the landing to take the QUAY branch would have been
   cut to quay-west for it. An authored @t split was tried at SEVEN positions
   (0.82/0.84/0.86/0.88/0.90/0.93/0.97) and the window is squeezed from both ends —
   below t~0.73 the arrival clears 0.47 m against a 0.50 m floor, above t~0.78 the band
   lands on `walk_lm_quay-deck`. Empty intersection, exactly §5.1's arithmetic. The pad
   is NOT IMPORTED: the fork platform already exists as the market flight's own
   `_landing` mesh at the same height, so the pad bought no walkable ground and cost a
   seam. THE PRICE IS STATED, NOT HIDDEN: the master no longer matches a full blockout
   for that one record, and master_walk_qa reports it as missing. Two documented
   exceptions now (this and the portal's lm_ posts-and-lintel massing, which the master
   carries ZERO of). A THIRD would mean the rule belongs in town_blockout — "no
   threshold pad where a landing mesh already covers the landmark" — not in my tool.

=== THREE OF MY OWN INSTRUMENTS WERE WRONG AND ARE NOW RIGHT ===
 -  `ls_nav_probe` counted RAW overlap and would have cried defect on any two ribbons
    leaving one pad. Run on Emberbrook's hillside-cottage it reported 418 covered cells —
    at a gap of 0.000..0.038 m, i.e. coplanar lanes, no foot displaced. A LIFT THRESHOLD
    (0.15 m, half of Dellhollow's 0.32 m riser) now separates "lifted off a surface" from
    "two ribbons at the same height", the raw count is still printed so the threshold
    stays falsifiable, and the verdict is three-state: DEFECT / MARGINAL (lifted but
    sub-body) / CLEAN. Emberbrook now reads CLEAN with a 20x margin.
 -  Its §5 printed a fixed paragraph asserting a stair story regardless of the numbers,
    and its fork arithmetic compared the first legs of two edges that no longer share an
    origin — it produced a "2x margin" and a DEFECT verdict for a geometry that is fine.
    A conclusion that cannot come out false is not a finding. Both are now derived.
 -  MY PRE-REGISTERED GATE WAS THE WRONG INSTRUMENT AFTER THE FIX AND I SAY SO RATHER
    THAN REDEFINING IT QUIETLY. I promised "held-heading sweep 0/72 -> strongly nonzero".
    It is 0/72 still — because the descent now legitimately TURNS ~117 deg at the landing
    and no single held heading can execute a fork. A held heading was a fair gate for two
    flights leaving one point; it is not one for a forked route. The functional gate for
    a fork is the descent trace (58/0) and seam_walk's scripted journeys, and the probe
    now prints that caveat itself instead of leaving a future reader to misread 0/72.

=== A NEW TOOL, AND THE HOLE IT FILLS ===
`tools/ls_reorigin.py` — re-derive ONE map edge's walk records into the master. CLAUDE.md
says "one line of map, ONE COMMAND TO RE-DERIVE"; the line existed and the command did
not. `town_blockout` raises the whole town into a separate blend and WIPES the scene, and
every district builder here is additive and reads the walk network as given — so a map
walk-record change had NOWHERE TO LAND, which is why this defect survived a rebuild, a
re-aim, a bake and four gates. The tool reimplements nothing: it appends the records out
of the freshly-derived blockout, so there is no second generator to drift. Idempotent,
and revertible via LSR_SRC_* snapshots.
  ITS FIRST RUN ATE ITS OWN SNAPSHOTS AND THAT IS FIXED AND RECORDED. Revert renamed the
  snapshots back but never RE-LINKED them to a collection; an object in no collection
  with no fake user has zero users, so Blender garbage-collected all twenty on the next
  save. The tool reported a successful revert and destroyed the thing it exists to
  protect. It now records each object's collections on the object and nothing loses its
  fake user until it is back in one. (The master is git-tracked, which is the real
  backstop, and this pass was redone from a clean `git checkout` of it.)
  TWICE THE SAME DEPSGRAPH TRAP: a just-appended object's `matrix_world` is identity
  until the view layer is updated. First it printed every new record as a -1..1 unit
  cube; caught by eye and now caught by an assert. Then, one step earlier, it measured
  the fork footprint as a unit cube, matched no rail and printed "NO RAIL CROSSED THE
  FORK" while the rail was standing across the stair. Update first, measure second.

`ls_build.py` NO LONGER NAMES ITS FLIGHTS. It shipped with
("walk_e_shelf-homes__quay-deck_", "walk_e_shelf-homes__market-stalls_") hardcoded; after
the stamp that constant pointed at a WITHDRAWN ribbon and the timber would have been
dressed onto a staircase that no longer exists, with nothing in the pipeline saying so —
the same class of miss as the defect being fixed. It now reads the camera file's owned
edges. `seam_walk.mjs`'s two scripted quay-flight journeys were rewritten for the new
route (yard -> shared flight -> landing -> fork); same two cuts, one more edge to name.

=== GATES ===
  cine_test   643 ok / 0 failed (+2 soft)      seam_test  294 ok / 0 failed (+7 soft)
  seam_walk   9/9 scripted walks               routes --check CLEAN
  plate_flat  clean, 0 of 16                   slice_test 684 ok / 20 failed
  geometry_audit region 46,64,5,17: 2 intersection offenders, 0 strays — DOWN from the
    3 this region carried before (ls_frame frac 0.370 -> 0.237, ls_treads 0.117 -> 0.034),
    both survivors the already-accepted class of this pass's timber bedded in the quay
    tier's masonry. No new offenders.
  SLICE'S 20 REDS ARE NOT DELLHOLLOW'S AND THE ATTRIBUTION IS COUNTED, not asserted:
    18 emb-cine, 1 ow-valley, 1 `del-cine>ow-valley` whose assertion is about OW-VALLEY's
    walk network. Zero are about Dellhollow's own geometry. The emb-cine ones are the
    Emberbrook lane's landed 2x map deriving cuts against an emb-cine bundle baked before
    the rescale — theirs to close with a bake, surfaced (not caused) by my derive.
  MASTER_WALK_QA — READ THIS ONE CAREFULLY, IT IS THE INTERESTING RESULT. My build
    reports 22 items. The PRISTINE master at HEAD, run identically from a git-restored
    copy, reports 23 — and TWENTY OF THEM ARE CHARACTER-FOR-CHARACTER IDENTICAL
    (bar_ rails on deep-stairs, keepers-cottage, quay-deck__pilot-cluster, valley-gate,
    weave-huts and market-stalls, "moved by" 0.006 to 3.641 m). So 20 of 22 are
    PRE-EXISTING and none is mine. The cause is now visible because this pass regenerated
    the derived caches: `dellhollow-town.blend` was SIX HOURS OLDER than the map it is
    derived from, and master_walk_qa rebuilds `town_walk_reference.json` from it — so the
    master's bar_ rails across FIVE districts were built from a blockout that predates
    some 2026-07-30 map edits. That is the same disease this pass fixed, in five more
    places, and it belongs to whoever owns those districts. MY OWN two items:
    `walk_pad_loop-landing` missing (the documented exclusion above) and
    `bar_e_shelf-homes__market-stalls_l0_railB` vertex count 4 != 8 (the fork gap).

RECORD SHOTS: docs/qa/districts/loopstairs_fork_after_{loop-stairs,quay-west}.png —
the freshly baked plates with both ribbons and the surviving sub-body sliver overlaid.
The BEFORE pair from the diagnosis pass (loopstairs_head_overlap_*.png) is the
comparison. A TASTE ITEM FOR THE COORDINATOR, flagged not decided: the re-solve moved the
loop-stairs camera (pos [50.11,28.77,23.19] -> [51.32,28.05,22.56]) and the branch now
reads as a steep timber trestle down the middle of frame. It is legible and measured;
whether it is HANDSOME is the user's call, not a gate's.

STILL RECORDED-NOT-FIXED, unchanged by this pass: the market flight's seam sits
mid-flight at z 15.93 rather than on a landing (canon §4). The §5 work above proved there
is no better position for it while the market edge is unsplit, so the miss now has an
arithmetic reason rather than a budget one.

REUSABLE, AND EMBERBROOK GETS IT FREE NEXT SLATE: `tools/ls_nav_probe.mjs` is town- and
edge-parameterised (`LS_TOWN=emberbrook node tools/ls_nav_probe.mjs <edgeA> <edgeB>`), it
reads only the shipped bundle — no Blender, no API key, no browser, seconds — and it has
already been run against Emberbrook to calibrate its own threshold. Emberbrook has no
stairs edges yet; the day its camera lane authors one, the question "does this flight
catch a foot" is one command old.

## THE GATE LIP, FALSIFIED — the terrain fix has a measured ceiling of +9.7 points and the
## walker was never on the terrain at all (2026-07-31, Dellhollow carryover lane)

THE ROUND WAS BRIEFED ON A DIAGNOSIS THAT IS HALF WRONG, AND THE HALF THAT IS WRONG IS THE
HALF THE SPEND WAS AIMED AT. The standing note (04:4x, loop-stairs-lane closing) reads:
"`gate_road`'s lip BOTH hides the staircase from the camera (23.2% of the gate block) and
is the surface the walker stays on. ONE OBJECT, TWO INSTRUMENTS, one art fix — and it is
terrain." Both clauses were tested before anything was built. The first is true and
un-actionable; the second is false.

=== 1. THE WALKER IS NOT ON `gate_road` AND STRUCTURALLY CANNOT BE ===
`tools/nav_eval.mjs` builds its ground grid from `const WALK_RE = /^walk/i` (l.192) and
`walkGround()` reads only that grid. `gate_road` is art, 80 mm BELOW the walk surface by
`gate_build.py`'s own `DECK_DROP`. No edit to `gate_road` can move the walker by any
amount. The same is true in the shipped game: WALKLOCK is the walk network in
/^(del-|townwalk)/ scenes, which is why the user hits this live.

THE REAL STEERING DEFECT, NAMED, with a new instrument that reproduces the N=10 result
offline and deterministically in two seconds (no API key, no browser):
`walk_e_valley-gate__winch-head_l0..l2` — the ROAD ribbon — OVERLAPS the gate stair's top
treads in plan and stands up to **0.340 m ABOVE** them; 60 cells of a 0.1 m grid are
doubly covered. `walkGround` keeps the HIGHEST surface in the step window, so at the stair
head the foot is taken by the road every time. Traced, naming the record that catches each
step:
    valley-gate -> inn        pad_valley-gate -> winch-head_l0 @x17.6 -> ...l4 -> ends on
                              the ROAD at h=24.07, five metres above the inn it "reached"
    valley-gate -> item-shop  road all the way east, REFUSED at x=28.81 on walk_pad_winch-
                              head — the winch head over the drop
That second line is the 04:4x N=10 finding ("8 of 10 walk the gate road EAST and the last
leg is refused at x 28.6-30.9") reproduced exactly, offline, for free.
  SO THE OBJECT IS THE ROAD RIBBON, NOT THE ROAD ART, and the layer is the MAP, not the
  master. Per CLAUDE.md ("a conflict fix is a landmark move or a lane waypoint — one line
  of map, one command to re-derive") this is the loop-stairs shape exactly. NOT STAMPED
  HERE: the town maps are coordinator-owned and this is a walk-network change under a live
  Emberbrook lane. PROPOSED, with the arithmetic: the stair ribbon reaches y 4.45 at
  x 18.0..18.5 and the road ribbon is ~2.0 m wide, so the road centreline at the stair
  head must sit at y >= 5.7 to clear it by 0.25 m; today it is at y ~4.6. One waypoint on
  `valley-gate -> winch-head` near [18.6, 6.0, 24.0], then `ls_reorigin.py` on that edge.

=== 2. THE VISIBILITY HALF IS TRUE, AND IT IS A TANGENT, NOT A LIP ===
`gate_road` is 19 of gate's 82 rays (23.2%), reproduced. But of those 19 blocking rays the
deck stands above the sightline by **0.000 m — every one is TANGENT**. There is no lip
standing proud to shave: the gate camera (pos [25.84, 30.65, 39.38], ~30.5 deg below
horizontal) looks at the flight ALONG the road's own z~24 deck for a six-metre run, and
the flight descends underneath it. The occluding deck is directly under the road's own
walk ribbon (y 3.6..5.6), so shaving it would float the player above the road.

THE CEILING, MEASURED BY EXCAVATION RATHER THAN ARGUED (82 rays, in-blend, nothing saved):
    H0  as built                                          gate CLEAR  17.1%
    H1  deck shaved 0.25 m across y 4.0..5.4               gate CLEAR  18.3%   (+1.2)
    H2  gate_road DELETED south of y=5.6, x 16.5..21.5     gate CLEAR  20.7%   (+3.6)
    H3  H2 + gate_ground deleted there as well             gate CLEAR  23.2%   (+6.1)
    H4  H3 + every veg_gate_rimclump hidden                gate CLEAR  26.8%   (+9.7)
So DELETING THE ROAD, THE GROUND UNDER IT AND ALL THE RIM PLANTING buys 9.7 points, and at
H4 `gate_road` is STILL the top occluder (27 rays) because the freed rays graze it further
east. The brief expected "CLEAR to rise well past 17.1%". It cannot pass 26.8% even if the
hillside is deleted. THE `gate` SHOT'S 0/10 IS A COMPOSITION FACT, NOT A TERRAIN ONE — and
that now has a number, which is what three failed camera attempts and one awning surgery
did not have. NO TERRAIN WAS CUT: a fix whose measured ceiling is +1.2 points of CLEAR for
a master-blend edit, a rebake and a walk-QA cycle is not worth its own risk.

=== 3. WHERE THE SPEND SHOULD GO INSTEAD — shelf-west, and it is ONE OBJECT ===
Same ladder on `shelf-west` (the other shot that owns `valley-gate__inn`, now at yaw 105):
    S0  as built                                     shelf-west CLEAR  23.2%
    S1  + all 41 veg_gate_rimclump hidden            shelf-west CLEAR  24.4%   (+1.2)
    S2  + gate_corbels hidden                        shelf-west CLEAR  32.9%   (+8.5)
    S3  + gate_parapet hidden                        shelf-west CLEAR  32.9%   (+0.0)
    S4  + gate_ground hidden (the floor: the ceiling) shelf-west CLEAR 40.2%
`gate_corbels` is 9 rays and worth **+8.5 points on its own** — a single named art object,
the same shape of answer the awning census produced, and the first genuinely actionable
lead this staircase has had. `gate_parapet` is 7 rays and worth ZERO (it shadows corbels);
the rim planting is worth 1.2, not the 28.0% its tally suggests. THE LAYERING RULE HOLDS
FOR THE FOURTH TIME: a tally is not a budget, and only an excavation ladder tells you
which line of the tally is load-bearing.

=== 4. SHIPPED THIS ROUND ===
 -  THE LAST "ARRIVES INVISIBLE" ARRIVAL IS CLOSED. `shelf-east>shelf-west` on
    `weapon-shop__armor-shop` measured 91/91 samples on screen and **0 of 91** surviving
    the depth test (arrival_probe, shipped plate). Applied the polish lane's specified
    override [37.1, 19.04, -5.3] to shelf-west: **body 0.0% -> 76.9%, chest 0.0% ->
    75.0%**, 2.43 m of band clearance against the derived point's 1.60. Re-solved: only
    shelf-west moved, by 6 mm (dist 23.79 -> 23.80), exactly as predicted; one bake.
 -  THE MAP LINE THAT CONTRADICTED ITSELF. `river.gorge.note` called the y=0 wall "near
    (south)" while `units` says +x is downstream/north — and the 2026-08-01 world restamp
    puts Dellhollow's anchor at +33 with the town on the WEST (left-looking-downstream)
    bank, which `world.json` states outright. Restated as "near (WEST)" with the reason
    attached. Every other compass word in the file (`water-gate-north`, `weave-north`,
    `north-landing`, "gorge narrowing north", "upstream lock visible to the south") was
    checked and already agrees with +x = north.

=== 5. NEW INSTRUMENT: tools/walk_water_audit.mjs — CAN THE PLAYER STAND ON OPEN WATER? ===
The user hit this live at the stilt clusters ("extremely confusing / incomplete geometry,
walking on water"). No standing gate asks it: master_walk_qa asks whether there is art
under the walk surface, and the WATER is art, so an overrun pad passes coverage.
THE ONE DISTINCTION THAT MAKES IT USEFUL: a deck over water is this town's whole
architecture and must not be flagged. So the question is not "is water below" but "is the
FIRST drawn thing below the foot water".
THE PROBE IS A 25 mm CROSS, and that is load-bearing, not decoration — CLAUDE.md's own
interiors rule for the same reason. Raw single-ray: 2002 samples. Cross-probed: 1802. The
200-sample difference is plank shadow-gaps, and BOTH NUMBERS ARE PRINTED so the correction
stays falsifiable (ls_nav_probe's lesson: a conclusion that cannot come out false is not a
finding). A third state, MARGINAL (supported, but the deck is more than play3d's 0.60 m
step-down below the foot), is counted separately and never called a water defect: 1646.
    DELLHOLLOW, 15 246 samples of the walk network at 0.4 m:
      supported 11 797   MARGINAL 1 646   OVER OPEN WATER 1 802   OVER VOID 1
      defect rate 11.83%, across 39 walk records
NOT BOUNDED, SO NOT FIXED — and the reason is the finding. The four worst are LANDMARK
PADS, not ribbon overruns: `walk_lm_moorage` 607 samples at 0.80-1.05 m of clear air,
`walk_lm_drying-decks` 241 at **6.46-6.71 m**, `walk_lm_fish-dock` 188 at 0.80-1.05 m,
`walk_lm_north-landing` 100 at 2.79-3.04 m. A pad floating a metre over the river with
nothing under it is not a ribbon that overran its deck — THE DECK ART FOR THOSE LANDMARKS
WAS NEVER BUILT. The blockout laid the pads, the district builders raised huts and stilts
on them, and no pass ever laid the platform. That is a district-builder job for the
stilt-cluster round, not a trim, and it is why the coordinator's "trim to the deck edge"
instruction does not apply. Full list with positions in the tool's --json.

=== 6. THE PINK STRAY BY THE QUAY DECK — FOUND, AND IT IS A FAMILY OF FOUR ===
User's frame (docs/qa/refs/user_ropefence_ref.png) shows a flat salmon-pink plane passing
through a seated NPC at waist height. It is a `*_paint` decal. FOUR of the five `_paint`
objects in the master are ZERO-THICKNESS SINGLE QUADS, all `hide_render = False`:
    t2c_DS2_hull_paint        madder  (27.90, 28.37,  4.60)  host 0.140 m away, hull both sides
    t2c_L2_lockhouse_paint    slate   (91.80, 27.32,  3.00)  NO HOST EITHER SIDE within 3 m
    t2c_LH6_hut_gable_paint   madder  (73.37, 19.52, 11.30)  host 0.140 m away, NOTHING behind
    t2c_WV3_north_hut_paint   teal    (50.90, 19.32,  8.50)  host 0.140 m away, NOTHING behind
A paint decal belongs ON its wall. Three of these stand **140 mm proud** of their host with
open air behind, so from any oblique angle they read as a board hovering off the building
and edge-on they are a streak — which is exactly what the user circled. `t2c_L2_lockhouse_
paint` is worse: it has no host wall on either side and is simply floating near the lock
stairs. `shed_paintwork` (the fifth) is a real solid, 1.92 m thick, and is fine.
NOT FIXED HERE — it is `t2c_` namespace, the tranche-2 lane's, and the last time this lane
took another lane's art at the end of a shift the DAYLOG recorded why not to. Specified
with a position and a measured offset per object: re-seat each decal flush on its host
(the 0.140 m is the bug) or give it thickness and a back face; delete or re-host L2.

=== GATES ===
  cine_test / seam_test / seam_walk / slice_test / plate_flat / routes --check: see the
  commit; slice's emb-cine reds are the Emberbrook lane's pending bake, attributed not
  chased. Walk QA bit-identical outside the edits (no master geometry was changed by this
  lane at all — the two Blender passes above are read-only and save nothing).

=== WHAT THIS ROUND DID NOT DO, AND WHY (for the next brief) ===
The round was briefed with 5 items and grew to 11 in flight. Shipped: the lip
falsification + the redirect, the shelf-east arrival + its bake, the map line, the
walk-water instrument, the stray identification. NOT DONE, each needing its own round:
the stale `bar_` rails across five districts — now a REDESIGN, not a rebuild, since the
solid plank guard screens are to become rope fences town-wide; the east-cliff stray
geometry; the RIM VISTA camera (a new authored shot, full seam canon, 288-position
sweep); the shop-row recomposition to the user's own reference; the gate canopy
re-spacing; the boatyard deep-blue water A/B; the stilt-cluster simplification (which
now has the walk-water audit's numbers waiting for it).

## THE RIBBON OFF THE TREADS — the steering defect is fixed and MEASURED, and gate's 0/10
## is now proved to be composition (2026-08-01, Dellhollow carryover lane, round 2)

THE STAMP (f7973b9, coordinator, from round 1's arithmetic) moved `valley-gate__winch-head`'s
single waypoint [22.0, 6.5, 24.0] -> [18.6, 6.0, 24.0]. This round rebuilt from it and
measured what it bought, with the perceptual spend at the end rather than the start.

=== WHAT MOVED, by instrument ===
  ribbon overlap (road x stair)   60 cells @ 0.1 m, road 0.340 m ABOVE  ->  10 cells, 0.000 m
  offline descent trace           0 treads: captured by the road, ended
                                  on it 5 m above the inn                ->  5 treads + the
                                                                             landing, h 24.07
                                                                             -> 22.30
  the winch-head dead-end         REFUSED at x=28.81 (the N=10's own
                                  failure, reproduced offline)           ->  gone; every leg
                                                                             of all 10 gemini
                                                                             trials is `ok`
  master_walk_qa                  23 items at HEAD                       ->  22, and
                                  `valley-gate__winch-head`'s 11 stale records are ZERO
  nav_eval --judge oracle-world   0.938 (15 of 16)                       ->  1.000 (16 of 16)
  geometry_audit                  0 strays; gate-region survivor t2c_G4_arch_banner
                                  (frac 0.047) pre-existing and unchanged
THE ORACLE-WORLD MOVE IS THE ONE TO BELIEVE. It is the API-free ground-truth walker, and
it had never scored 16/16 on this town. The ribbon overlap was costing it a shot, exactly
as the offline trace said, and no judge was involved in either measurement.

=== N=10 ON gate, PINNED gemini-3.6-flash, 0 errors — STILL 0.00, AND THAT IS THE RESULT ===
                    tranche-2  surgery  after awnings   AFTER THE RIBBON
      score            0.00     0.00        0.00             0.00
      onWalk           0.450    0.655       0.667            0.81   <- best ever
      progress         0.599    0.633       0.617            0.59
      stuckLegs        2.2      3.3         6.4              1.1    <- best ever
      wentBack         5        3           0                0
THE MECHANICAL DEFECT IS GONE AND THE PERCEPTUAL ONE IS UNTOUCHED, and the per-leg records
say so without ambiguity. Across all ten trials there is not one `refused` leg — the 8-of-10
winch-head dead-end that this shot has failed on since tranche-2 does not occur. But EVERY
WAYPOINT THE JUDGE PICKS, in every leg of every trial, is at h 24.1: the rim road. Not once
in 62 waypoints does it aim at a tread (the flight descends 23.73, 23.39, 23.05, 22.71).
occludedWaypoints runs 0-5 of 6. Three trials open with a `no-progress` leg aimed at
h~26.5 — two metres ABOVE the road, i.e. the arch or the gatehouse roof.
  SO THE WALKER NO LONGER FIGHTS THE GROUND; THE JUDGE STILL CANNOT SEE THE STAIRCASE.
  That is round 1's ceiling measurement cashing out: gate is 18.3% clear on the flight and
  the measured ceiling for ANY terrain surgery — deleting the road, the ground under it and
  all 41 rim clumps — is 26.8%. A frame that does not contain a legible staircase cannot be
  fixed from the ground, and this is now the third independent instrument saying it.
  WHAT IS LEFT IS A CAMERA, and that belongs to the composition round, not this one.

=== A REGRESSION I CAUSED, CAUGHT AND PAID FOR ===
`gate` FRAMES the ribbon that moved, so cine_solve moved the camera 0.624 m / 0.430 aim —
and that cost the `shelf-west>gate` arrival 10.7 points of chest, 57.1% -> 46.4%, across
seam-canon §10.2's line. It was found by probing the HEAD plates and the new plates side by
side rather than by assuming the move was free, and the other three "arrives invisible"
shots (lockhead, the cookhouse door, the ow-valley portal) were confirmed byte-identical
before and after, so exactly one arrival regressed and it was mine.
FIXED BY SEARCH, NOT PLACEMENT: 761 walk-network samples within 7 m of the derived point,
filtered to those clearing the seam band's 2.25 u half-width by the 0.5 m floor.
`valley-gate__inn:shelf-west` -> [17.0, 24.04, -4.0] on walk_pad_valley-gate, 1.04 m from
the derived point: chest 46.4% -> 100.0%, body 73.6% -> 93.4%, band clearance 3.61 m
against the required 2.75. Better than the 57.1% it started at, bought with margin.
Town-wide "arrives invisible" 4 -> 3, and the 3 are the pre-existing ones.

=== A SECOND DEFECT ON THE SAME FLIGHT, FOUND BY THE TRACE, NOT FIXED ===
The descent now reaches `walk_e_valley-gate__inn_landing` (h 22.30) and stops. The landing
mesh spans x 20.0..22.0 and BURIES the l1 flight's first two treads (t00 h 22.37, t01 h
21.99); from the landing's east edge the next surface is t02 at 21.61 — a 0.69 m drop
against play3d's 0.60 m STEP_DN window. NOT CLAIMED AS PROVEN: my trace is a straight-line
greedy walker and nav_eval's follows routes.json, so this may be my probe's crudeness
rather than the town's. It is written down with the arithmetic so the next pass can settle
it with the right instrument instead of rediscovering it.
  [CORRECTED 2026-08-01, round 3, with the right instrument. STEP_DN is 0.8, not 0.60, and
  has been since efb811c (2026-07-28) — three days before this entry. So the 0.69 m drop is
  INSIDE the step-down window and was never the defect. The obstruction on this landing is
  real, and it is `gs_rail` lying ACROSS the flight at body height, blocking 1.05 m of its
  1.4 m width. See "THE CINEMATIC SHOT CLASS, AND THE FIRST THING ITS CAMERA FOUND" at the
  end of this log for the per-z scan and the triangle-level identification.]

=== NEW TOOL: tools/walk_rederive.py — the general form of ls_reorigin ===
`ls_reorigin.py` was this idea's first instance, hardcoded to one edge, and its own
docstring set the rule: when a third appears, put it somewhere general. This is that place;
ls_reorigin is left alone (its fork-specific rail gap is not a general operation).
  `-- --report` diffs the master against a blockout raised from the CURRENT map, per edge,
  and it AGREES WITH master_walk_qa RECORD FOR RECORD (32 stale across 7 edges; after this
  pass's 11, the residual 21 are exactly master_walk_qa's 21). Two instruments, one number.
  THREE TRAPS IT CLOSES, each of which produced a confidently wrong answer first:
   1  THE REPORT COMPARED THE APPENDED OBJECTS WITH THEMSELVES. Building the master's index
      AFTER appending the blockout puts the blockout's objects in `bpy.data.objects` too:
      0 stale, 0 missing, and the master's real contents reported as "extra". The numbers
      looked clean and meant nothing. Capture first, append second.
   2  NAME COLLISIONS. Every record already exists by name, so Blender suffixes each
      appended object `.001`. The first save shipped `walk_e_valley-gate__winch-head_l0.001`
      into the GLB — and every other tool matches walk records by EXACT name (cine_solve
      `owns`, routes_derive, master_walk_qa, seam_test), so that silently orphans the edge.
      True names are recovered by zipping `dst.objects` against the requested name list,
      never by stripping a suffix, and taken only after the originals are snapshotted.
   3  THE DEPSGRAPH TRAP, THIRD INSTANCE — and `view_layer.update()` is NOT sufficient on
      its own, which is what ls_reorigin's write-up implies. An appended object in no
      collection is not in the view layer at all, so it never evaluates: every record reads
      as a unit cube at the origin. LINK, then update, then measure. An assert holds it.
  AND IT REFUSES TO CLOBBER DOCUMENTED EXCEPTIONS. `bar_e_shelf-homes__market-stalls_l0_railB`
  is 4 verts in the master and 8 in the blockout because ls_reorigin CUT A GAP in it — it
  ran across the loop-stairs fork's top tread as an invisible wall. A blind re-derive
  re-installs that wall. It and `walk_pad_loop-landing` are now named constants with their
  reasons, held back unless `force` is passed. Every rebuilt `bar_` is also swept against
  every other edge's walk ribbon and crossings are REPORTED, never auto-cut: deleting
  collision silently is worse than pointing at it.

=== GATES ===
  cine_test 643/0 (+2 soft)   seam_test 294/0 (+7 soft)   seam_walk 9/9
  plate_flat 0 of 16          routes --check clean        geometry_audit 0 strays
  slice_test 684/20 — 19 emb-cine + 1 ow-valley, ZERO Dellhollow (attributed by count)
  master_walk_qa 22 (from 23): 21 = the priority-5 rails debt, 1 = documented exception
  RECORD SHOTS: docs/qa/districts/gateribbon_{before,after}_{gate,shelf-west}.png

## THE SHOPKEEPERS WERE GREETING THE SHELVES — `facing` is now a POST, and the town's
## grown-ups are 1.60 (2026-07-31, NPC-systems lane)
  USER REPORT, live play: "all of our shopkeepers are facing the back and a bit too short
  for the scene." Both halves were real and neither was a rendering bug.
  FACING. npcs.json's `facing` was already applied to a figure's root — it just cost
  nothing while every villager was a billboard, because a plate is yaw-billboarded to the
  camera every frame and CANCELS root yaw. The day seven of them got GLBs, the authored
  numbers became visible, and all three keepers were authored 180. INSTRUMENT: a yaw sweep
  at the item-shop counter (root.rotation.y := 0/90/180/270, one screenshot each,
  docs/qa/npc/yaw_sweep_0-90-180-270.jpg). It reads: 0 looks down runtime +Z — the near side, the
  side the fixed cameras and the shop doors are on — which makes 180 exactly backs-to-the-
  player. Convention written into npc.js's header and npcs.json's _schema; `facing` is now
  documented as a POST, not a pose: a wander errand still turns the body with its travel
  and the yaw EASES back (dt*3, half the travel turn) when the errand ends. Headless
  assert: knock every model body 90 deg off, wait for clip!=='walk', all four converge on
  their post within 1 deg — including Nib, who is mid-errand when you first look.
  Corrected with it, all model bodies (a billboard's facing is still noise): hobb 20->200
  (he was dead away from both the rafted queue and the boatyard camera), maren 90->120,
  nib 180->160. Eel-wife's 200 was already 9 deg off facing the fishdock camera: left.
  STATURE, and the bigger half. The keeper "barely clears the counter" because he was
  standing INSIDE it: position z -1.02, and the counter carcass's back panel is y
  1.03..1.08 (tools/shop_props.py CTR_Y0/CTR_Y1, CTR_H 1.05). From the room's own high 3/4
  camera the counter TOP is the occluder — the critical edge is its BACK-top edge, not the
  front — so at -1.02 everything below y~1.08 is hidden and a 1.45 body shows 0.37 m of
  head. Moved to -1.55, the shop archetype's own documented KEEP zone ("behind counter,
  y 1.3..2.5, NPC stands here", tools/item_int_build.py), where the occlusion line drops to
  y~0.85 and an adult clears it from the waist up. MEASURED, not styled: the interiors are
  built around the kit's REF_human_1p7 and the counters are 1.05, so defaults.adultHeight
  1.10 x charH 1.45 = 1.60. It applies ONLY to model bodies with no height of their own —
  Nib keeps body.h 0.72 (1.04 m, he is eight), every billboard keeps its plate's 1.45, and
  the player is untouched at 1.45. Reach follows the keeper back: radius 2.4 -> 2.7, which
  covers the far corner of walk_pad_counter at 2.55 (asserted at all four corners + centre;
  the greeting still opens the counter).
  RECORD SHOTS: docs/qa/npc/ — counter_{item,weapon,armor}_before-after.jpg (before | after,
  all three Dellhollow counters), street_{fishdock,boatyard}_before-after.jpg,
  town_quay-west_before-after.jpg (pixel-identical: the bump reaches no billboard), and
  yaw_sweep_0-90-180-270.jpg, the instrument the convention was read off.
  GATES: transition_test --port=8146 157/3 and --reload 31/1, where EVERY failure is
  pre-existing and reproduced on HEAD with these two files reverted (3x ow-valley "arrival
  stands on the walk network", plus an intermittent music-drift and an unstable del-cine|
  gate geometry baseline that moves 379<->388 between runs with nothing of ours changed —
  the world lane was re-baking that very shot while the gauntlet ran: del-cine/cameras/gate/
  {bg,depth}.png and cine.json carry mtimes INSIDE the run window. Not a leak; a moving
  floor under the baseline).
  economy_test 204/0.

## SCENE RED-TEAM — an LLM critique judge, calibrated before it is trusted

`tools/scene_redteam.mjs` (new). Passes every shipped plate to the pinned nav-eval judge
(gemini-3.6-flash, same key, same channel) and asks for what the user has been asking by
hand: confusing, occluded, incomplete, ugly. Report:
**docs/qa/redteam/run-20260731-dellhollow/index.html** (self-contained; serve docs/qa).

TWO MODES, and the second exists because the first has a hole. NAIVE is context-free —
no map, no town, no history — because confusion is a property of a first look. CHECKLIST
is map-informed, because **a context-free judge cannot report the absence of what it
never knew existed**: an occluded staircase is not a complaint to someone who does not
know a staircase belongs there. Its item list is DERIVED (cameras.json owns.landmarks +
owns.edges, mapVisible landmarks that project into frame, door pads, routes.json
frameExits) and the verdicts are FINDABLE / OCCLUDED / VISIBLE-BUT-ILLEGIBLE / ABSENT.
The third is the only one no deterministic instrument can produce, so it is the one the
mode is for. STAGE 2 refutes every finding adversarially, or upholds it on the ray census
where the census can answer; survivors only are reported, refuted kept in the run dir.

=== THE CALIBRATION GATE, HONESTLY ===
Scored blind against the user's five committed complaints (docs/qa/refs/user_*_ref.png).
**3 of 5, hand-adjudicated.** HIT canopy-wall (gate, 3 of 3 looks). HIT gate-stair — by
the CHECKLIST mode, on shelf-west which owns the `valley-gate__inn` flight: "ABSENT —
Cliffside S-bend staircase is not shown", while the census puts that flight on screen and
unoccluded. That is the map-informed mode earning its existence, and the naive mode never
mentions a stair on either gate plate. HIT waterfront-jumble (exact plate: "the visual
similarity between roofs, walkways and steps creates path ambiguity across the multiple
vertical levels"). **MISS stray-cliff, MISS plank-screens** — the green screens are
plainly in the quay-west plate (verified by crop) and three looks plus a fifteen-item
checklist never mentioned them. A rail that reads as a rail is invisible to a critic who
was not told the designer wanted to see through it.
  THE PRE-REGISTERED KEYWORD MATCHER SAYS 3/5 EXACT AND 5/5 ANY-PLATE ON THE SAME RUN AND
  IS WRONG IN BOTH DIRECTIONS. It credited stray-cliff to "the banner is attached flat to
  the sheer cliff face" (the words `cliff` and `flat`), and it MISSED the real gate-stair
  hit because its key list has no synonym for "not shown". Both numbers are printed side
  by side in the report; the keys were NOT edited to close the gap after seeing it.

=== PRECISION: STAGE 2 FILTERS WEAK CRITICISM, NOT CONFABULATION ===
Of 56 surviving extras (~22 distinct objects), 15 look real — best: quay-west's pale
untextured stair/ramp block (3/3 looks), deep-stairs' grey placeholder ramps clipping the
timber flight, lockfive's stair running into the solid underside of the deck above with no
hatch, and a pale pink flat plank floating over the quay deck **which is also visible in
the user's own user_ropefence_ref.png**. THREE ARE FALSE AND THE ADVERSARIAL SCEPTIC
UPHELD THEM: the judge twice called that plank "bright magenta, indicating missing texture
or stray debug geometry". MEASURED over all sixteen del-cine plates, magenta pixels
(r-g>60 and b-g>40) = **0.0000%**, near-white (min(rgb)>235, spread<12) 0.008–0.19%:
  node -e "const{PNG}=require('pngjs');const fs=require('fs');for(const id of fs.readdirSync('public/assets/scenes/del-cine/cameras').sort()){const p=PNG.sync.read(fs.readFileSync('public/assets/scenes/del-cine/cameras/'+id+'/bg.png'));let m=0;for(let i=0;i<p.width*p.height;i++){const r=p.data[i*4],g=p.data[i*4+1],b=p.data[i*4+2];if(r-g>60&&b-g>40)m++}console.log(id,(100*m/(p.width*p.height)).toFixed(4))}"
Right object, invented diagnosis, seconded by the refuter. A finding here is a PERCEPTION
and needs an instrument before it is a defect; geometry findings ship with their own
`geometry_audit --region` command for that reason.

=== FOUR DEFECTS FOUND IN THE INSTRUMENT ITSELF, EACH BY A MEASUREMENT ===
1. A CONTEXT-FREE SCEPTIC DELETES THE MAP-INFORMED MODE. Run -calib refuted 44 of 81
   claims and 31 were checklist claims thrown out for the object "not existing" —
   "expecting a pathway to a building that does not exist in the scene". Checklist scored
   0/5 that run. There are now TWO sceptics: the checklist one is told the contract and
   that existence is not the question. The naive one is unchanged; its innocence is the
   point.
2. N=1 IS NOISE. Same judge, same plates, two runs: the gate shot gave 6 findings in one
   and 2 in the other, overlapping in ONE. Naive mode now unions N independent looks
   (default 3) and each survivor carries `support` (k of N) rather than averaging.
3. A BARE-ARRAY REPLY SILENTLY DROPPED A WHOLE SHOT'S CHECKLIST (`j.items` undefined, no
   error). Both shapes accepted.
4. BOUNDING BOXES COME BACK IN TWO CONVENTIONS. Asked for [x0,y0,x1,y1] in 0..1, the judge
   often answers its native box_2d — [ymin,xmin,ymax,xmax] on 0..1000. Scored against the
   census: box_2d 7/23 vs naive-scaling 3/23, so the scale-switch reading is used. The run
   prints the agreement (14/45 = 31%) because **the judge's words are worth more than its
   coordinates** and the drawn rectangles are only as good as that number.
Also: the blockout triage rule was town-scoped after it swallowed Dellhollow's untextured-
greybox findings into "already known" — the worst possible triage error.

=== WHAT IT STRUCTURALLY CANNOT SEE (seam-canon §10.3, in the tool's own header) ===
"in frame" != "visible" != "unobstructed ray" != CATCHES A FOOT. The loop-stairs flight
was 72% visible, framed, unoccluded and unwalkable; no critique of that plate could ever
have found it. Also invisible here: body blocking, whether a naive reading ESCAPES
(nav_eval walks it), whether a seam fires, true per-object occlusion in metres (the bake
ray-cast remains the only visibility oracle) — and **anything outside the sixteen fixed
frames**: all five user references were screenshot from a FREE ORBIT CAMERA, from angles
no plate holds (best plate-vs-ref normalised cross-correlation 0.35). Section 4 of the
report names where each of those defects IS caught.

=== BUDGET, AND THE THING THAT STOPPED THE SWEEP ===
68 calls / 236 K tokens for the 12-plate calibration. **The shared GEMINI_API_KEY then ran
out of prepayment credit** (HTTP 429 "Your prepayment credits are depleted") — the same
key nav_eval uses, so nav-eval is down too until it is topped up. NOT SWEPT: loop-stairs,
lockhead, cottage, cottage-steps, and all six Emberbrook plates (~60 calls). Every reply
is stored, and a finished run re-derives from its own record for free:
`node tools/scene_redteam.mjs --calibrate --n 3 --replay 20260731-calib3 --stamp <new>`.

## THE GATE RE-AIM — a 90-composition sweep, a ceiling the legibility gate spends most of,
## and an N=10 that could not be bought (2026-08-01, Dellhollow carryover lane, round 2b)

THE QUESTION THE COORDINATOR SET: the judge must be able to SEE the staircase; compose for
that with round 1's 26.8% terrain ceiling in mind, and if the composition genuinely cannot
show the flight, say so with the sweep data.

FIRST, THE FACT THAT MAKES THIS SHOT DIFFERENT FROM A TASTE QUESTION. `scenegraph.json`
offers `gate` EXACTLY ONE exit: the cut on `valley-gate__inn` at t=0.428 to shelf-west. A
frame that cannot show that flight can never score, whatever else it does well. That is
why five consecutive bakes read 0.00 and why this was never really a camera preference.

=== THE SWEEP: 18 yaws x 5 pitches, each SOLVED then ray-cast against the master ===
82 rays on the flight, counted only INSIDE each candidate's own solved frustum.
    CEILING ACROSS ALL 90 COMPOSITIONS   31.7%   (yaw 40 / pitch 42, and 40/50)
    shipped at the time (68/28)          17.1%
    round 1's terrain ceiling            26.8%   (delete gate_road + the ground under it
                                                  + all 41 rim clumps)
So composition beats terrain here, and by enough to matter — which is the answer to the
question round 1 left open.

=== AND THEN THE BEST COMPOSITION FAILED TWO STANDING GATES, WHICH IS THE REAL RESULT ===
40/42 was built and baked, not argued about. On the plate it was excellent: stair VISIBLE
28.0% -> 57.3%, the shelf-west>gate seam arrival 100%/100%, and — unasked for — the town's
own FRONT DOOR, the ow-valley portal arrival, went 23.1%/0.0% (a pre-existing "arrives
invisible") to 68.1%/85.7%. It also failed:
    cine_test   character legibility 43 px at the far corner against a 50 px floor
                (pitch 42 puts the camera at z 51.5, far corner 48.5 m)
    plate_flat  gate 1.38% card, RGB 155,91,61, spanning x -1.00..0.81 — a volume
                rendered flat, which is the background-leak signature
BOTH ARE DISTANCE DEFECTS, and the legibility floor is therefore a hard cap on the solved
standoff at 68/28's 29.46 m. Re-reading the 90 candidates under that cap, the only ones in
this shot's own quadrant are 55/22, 55/28, 68/22 and 68/28.
  SHIPPED: yaw 55 / pitch 28. stair 17.1 -> 24.4% by ray-cast, 28.0 -> 32.9% VISIBLE on the
  shipped plate, dist 28.6 m, every gate green.
  THE HONEST SUMMARY, and it is not the headline the sweep promised: composition CAN beat
  terrain on this shot, but the legibility gate spends most of the difference. The reachable
  gain is +4.9 points of plate visibility, not the +29 that 40/42 showed.
  RECORDED FOR THE NEXT ROUND: 40/42 is a real 57.3% frame that fails only on DISTANCE. If
  the gate shot's owned region were smaller — which is exactly what "the rim vista absorbs
  arrival duty" would do — the solver's standoff would shrink and 40/42 might come inside
  the legibility floor. That is a region-ownership question, not a camera one, and it is the
  first concrete argument for the job change the coordinator raised.
  THE ARCH WAS NEVER AT RISK: 8 of 8 bounding-box corners in frame at ALL 90 compositions.
  So "looking back at the arch as a threshold you came through" did not constrain the sweep
  at all, which is worth knowing before anyone spends care protecting it.

=== THE ARRIVAL, RE-SEARCHED TWICE, AND WHY IT IS RANKED BY DISTANCE ===
Each aim change moved the arrival: the ribbon re-solve cost it 10.7 points of chest, then
the re-aim took the replacement to 7.1%. Both re-searches used the RAY-CAST oracle instead
of a plate, which is what let them happen BEFORE their bake rather than after.
CANDIDATES WERE RANKED BY DISTANCE FROM THE SEAM, NOT BY SCORE, and that is the judgement
worth recording: eleven points scored a perfect 100/100 but stood 7 m east on the winch
road. Teleporting a player 7 m off the flight they were walking is a worse defect than the
one being repaired. [17.5, 24.04, -2.75], 3.34 m from the seam: chest 7.1% -> 100.0%, body
97.8%, 3.34 m of band clearance against the required 2.75.
TOWN-WIDE "ARRIVES INVISIBLE": 4 -> 3. The gate portal is still one of them at 35.2%/32.1%
— IMPROVED from 23.1%/0.0% but not cleared, and it is not clearable at this aim; 40/42 is
the composition that fixes it, which is a second argument for the same job change.

=== THE N=10 COULD NOT BE BOUGHT, AND THE FAILED RUN WAS DELETED RATHER THAN FILED ===
The perceptual re-score is PENDING: the shared GEMINI_API_KEY exhausted its prepayment
credit mid-round (HTTP 429 RESOURCE_EXHAUSTED on all 10 trials). THE ALL-ERROR RUN SCORED
0.00 WITH onWalk 0.00, progress 0.00, stuckLegs 0 AND wentBack 0 — a shape that a future
reader would very reasonably mistake for "the re-aim made it worse", when in fact the
walker never took a step because no waypoint was ever returned. It is deleted, not
committed. Nothing in this repo should be able to be read as a measurement that is not one.
  WHAT STANDS, both API-free: nav_eval --judge oracle-world on gate = 1.000, and the
  round-2a N=10 (run-gate-after-ribbon, 10 trials, 0 errors, 62 real waypoints) which is
  still the last valid perceptual reading of this shot.
  READY TO RUN THE MOMENT THE KEY IS TOPPED UP:
      node tools/nav_eval.mjs --shots gate --n 10 --stamp gate-reaim-55
  and the prediction to check it against, registered now so it cannot be fitted afterwards:
  the round-2a run had onWalk 0.81 / stuck 1.1 with EVERY waypoint on the rim road at
  h 24.1. This aim adds 4.9 points of plate visibility. If the score moves off 0.00, some
  waypoints must land on treads (h 23.73/23.39/23.05/22.71); if they are still all at 24.1,
  then 32.9% is still not enough and the job change is the remaining lever.

=== GATES ===
  cine_test 643/0 (+2 soft)   seam_test 294/0 (+8 soft)   seam_walk 9/9
  plate_flat 0 of 16          routes --check clean        arrivals invisible 4 -> 3
  slice_test 670/16 — 15 emb-cine + 1 ow-valley, ZERO Dellhollow (attributed by count)
  RECORD SHOT: docs/qa/districts/gatereaim_after_gate.png

## BLOCKOUT ROUND 4 — a village that coexists with its wood, a square closed into a room,
## and a gate you cannot see the town from (2026-08-01, builder's lane)

THE USER'S TOWN-MODEL REVIEW, FOUR RULINGS, ALL BUILT. Three were coexistence (`map
coexistence._doc`) and one was the Old Gate's seclusion, which was proposed with
measurements, stamped by the coordinator at 306554a, and then built. The round's own
finding is at the bottom and it is about instruments, not geometry.

BOUNDARIES: THE SUBURB LEAVES. The 16-segment trimmed hedge ring is replaced by three
wilderness vocabularies drawn PER RUN — irregular dry-stone rows, split-rail/paling
fragments, bramble clumps — so one plot can be stone on the lane side and bramble where
the wood comes in. The change that does the work is not the vocabulary, it is PARTIAL
enclosure: 2-3 runs covering a minority of the perimeter.
    each plot bounds        29% of its own perimeter (median; 8% least, 62% most)
    the ring it replaced    94%
    the floor               3 segments. One stone on its own is litter; a 5 m run of it is
                            somebody's boundary. 1 plot needed the fallback run and it is
                            printed, because a rule that fires silently cannot be reviewed.
Round 3's lesson holds inside a run: a boundary is a LINE, not a row of dashes — 1.85 m
segments at ~1.45 m centres, the irregularity radial and rotational. Bramble is the
exception and drops every third segment ON PURPOSE, because a bramble clump is a gappy
thing. `_rail` and `_bramble` joined geometry_audit's SOFT_PART exactly as `_hedge` did.

VILLAGE TREES (31): 9 broad crowns, 15 tall slim, 7 conifers — three silhouettes far
enough apart to read at blockout, because at blockout a tree communicates nothing but its
silhouette and two species that differ by 15% differ by nothing. Searched, never authored.
THE FOREST'S PAID LANE RULE WAS RESTATED RATHER THAN WAIVED, and this is the round's one
deliberate rule change: a village tree over a lane cannot obey "a crown clears every walk
surface by its own radius + 1.0 m" and still be over the lane, so it obeys what that rule
is FOR — the TRUNK clears by its own radius + 1.20 m and the CANOPY's underside stands
>= 3.60 m wherever it oversails. Both asserted; measured at 1.32 m and 4.50 m against a
1.62 m walker. A CONIFER GETS NO EXEMPTION (its skirt is at head height) and keeps the
forest's rule unchanged, which is why the cones stand off the lanes and the broadleaves
stand on them.
    nearest village canopy EDGE from a lane   8.3 m median, -1.0 m at best (it overhangs)
    lane samples with one within 8 m          45%;  within 15 m  81%
CAMERA CORRIDORS ARE READ FROM `emberbrook.cameras.json`'s OWNERSHIP, INCLUDING ITS
@RANGES. The first version took the far LANDMARK of each owned edge as the viewpoint, so
`square-plaza__barn@0..0.573` aimed a corridor 24 m out to the tithe barn and swept the
whole annulus the square's ring pass has to build in: 153 candidate house positions
refused, 4 houses placed. A camera cannot be blocked on ground it does not own. It is the
ownership file, NOT `.cameras.solved.json` — that one still carries 1x positions and would
have aimed every corridor at a town that has not existed for two rounds.

THE SQUARE IS A ROOM, AND THE PROBE HAD TO BE REWRITTEN BEFORE THE GEOMETRY WAS TOUCHED.
16 sectors swept from the plaza, and three decisions each of which could have been made
the flattering way: the ray starts 4.0 m out (plaza and Heartlight share a coordinate, so
a ray from the centre begins inside the plinth and returns 16 sectors of "closed" off the
flame in the middle of the room); GROUND does not close a sector (a bank of grass is not a
wall); and a sector is 3 bearings x 3 ELEVATIONS, not one level ray — a broad crown's
canopy starts 4.4 m up and a level ray runs clean underneath it while the tree fills the
top half of the frame.
    sectors ending in a roofline or canopy within 25 m    6 of 16  ->  11 of 16
    of those, closed at eye level too                                        8
The five still open are the pond and Pond Lane (east), the mill and the brook (NW) and the
road in from the arch (south) — the map's own geography, not a gap in the ring.

THE SECLUDED GATE, PROPOSED AND STAMPED (306554a). Everything about the environment shift
is DERIVED so a re-stamped gate moves it: the sealed portal -> its court -> back along the
lane chain to the last landmark that HOSTS A LAMP (the roll is map canon at fourteen, so
"where the warmth ends" is a fact the build already knew) -> the drawn lane between them,
trimmed by the barnyard's own 9 m apron.
    the Old Gate to Festival Square      39.8 m  ->  87.1 m
    the quiet stretch                     0.0 m  ->  41.1 m  (58.1 m of road from the barn)
    the village goes out of sight        16.6 m past the last lamp; over the 24.5 m beyond
                                         that, 62% of steps see NOTHING of it, peak 2
    strict zero-and-stays-zero           38.9 m — the last thing to go is a sliver of the
                                         inn's roof down an 86 m diagonal
    THE SEAL, RE-PROVEN                  strip masonry->water 0.00 m, masonry->rock
                                         0.00 m, walk network stops 1.70 m short of the
                                         pinch, flood fill 0 m2 of gorge over 3167 m2
    the notch                            5.50 m wall | 4.90 m doorway | 3.55 m founded
                                         wall | 6.95 m grate | rock (gate-final.png: ~3.5)
    the gate court                       1030 cells, 228 given back to the bank (round 3:
                                         915 / 244) — the D is no worse than the ratified one

SECLUSION IS BOUGHT BY THE ROAD'S SHAPE, NOT ITS LENGTH, and this was COSTED rather than
argued. Two longer alternatives were built and measured: the gate at y=148 (60.1 m of
quiet road) and a west-excursion variant (49.2 m). BOTH ARE WORSE — 6 and 5 village solids
in sight FROM THE COURT against 0 — because their final legs run straight at the town and
the eye follows a clear road surface home. The winning road curves continuously and
arrives 35 deg off the town's bearing. Round 2 found that bending the ARRIVAL road bought
nothing; the opposite holds here, for the same reason (there the corridor pointed at its
destination, here the destination is behind you).

TWO RULES THE MOVE FORCED, both derived, both inert on the pre-stamp map:
 -  `beyond_warmth` — THE VILLAGE ENDS WHERE ITS APPROACH BEGINS, measured on the gate's
    own out-of-valley axis. Moving the gate north drags the anchor box up the approach,
    the infill grid seeds to that box + 16 m, and the first candidate build put TWENTY-
    SEVEN new households in the wilderness either side of the secluded road — fourteen of
    their roofs in sight from the court. The environment shift was built and then
    suburbanised in the same run. Fields are refused there too: "every acre BETWEEN the
    village and the wood" does not mean the ground that IS the wood.
 -  THE CORRIDOR GETS THE ARRIVAL'S FOREST FORMULA, not a milder one. The first version
    multiplied the corridor's density by the village-side clearance ramp, which holds the
    first trunk 8 m off the walk surface — a 16 m avenue through a wood, and the probe
    measured exactly what an avenue does: 15 solids at the warm end, 5 in the middle, 21
    at the court, because oblique rays run the length of a clear verge.

THE ROUND'S REAL FINDING IS AN INSTRUMENT, AND IT IS ROUND 2'S LESSON ARRIVING A THIRD
TIME. The seclusion probe excluded every landmark in the `gatefield` DISTRICT — which is
not the gate, it is the gate AND the tithe barn AND the dovecote AND the closed back lane.
So the report printed "the barn and the dovecote are IN this count" while the code had
excluded them by name, the profile read 0 at the threshold, and THE REVIEW RENDER OF THAT
EXACT SPOT SHOWED THE BARN, THE DOVECOTE AND TWO ROOFS PAST THEM. A probe that fails
CLOSED is the most dangerous instrument there is, and the only reason it was caught is
that this round shot a FRAME at the same coordinate the number came from. The exclusion is
now derived (`beyond_warmth`) and means what it says: only what you walk TOWARD is out.
Corollary worth keeping: a district is not a subject. Filtering a probe by district id
looks like filtering by meaning and is not.

A KNIFE EDGE IN A RECTANGLE TEST, AGAIN, AND IT FAILED THE BUILD TWICE. 2b's `in_rect`
boundary case returned at both ends of every curtain wall: built flush, the wall's outer
end and the rock's inner face are the SAME coordinate, and the seal probe steps the pinch
line at 0.05 m — whenever that grid lands on the join, both rectangles answer "outside"
and the run reports 0.05 m of open ground through solid masonry-into-cliff. It held at
HEAD only because the searched offset happened to fall off the sampling grid. The walls
now take a 0.30 m BITE into both the rock and the doorway's jamb, which is also what
"built wall-to-wall into living rock" means.

GATES. Deterministic, TWO RUNS identical (digest 7ab81682). COVERAGE asserted. Lamps
FOURTEEN. Walk QA 9 623 samples, 97.06% land on a walk mesh (round 3: 8 624 / 96.81%).
geometry_audit 63 intersections / 26 strays against round 3's 59/28 — no new classes; the
12 new intersections are the range's own rock lumps at a new latitude and the strays fell
because village-tree BOLES now reach a metre into their own canopies (built to 1.04x the
canopy base, every broadleaf crown reported itself unsupported — a canopy floating over a
pole that ended just below it). 2 232 objects, 141 289 verts. emb-townwalk re-exported
atomically, spawn [62,1.5,-32] unchanged, GLB 10.3 -> 13.1 MB (the corridor's forest, the
village trees and 50 m more ground).

WHAT IS A DESIGN QUESTION, NOT A BUILD FIX — reported, not decided:
 1  THE VILLAGE TREES HIDE THE VILLAGE FROM ITSELF. Lane samples meeting the densification
    ruling's 2+ background-roof target went 75% -> 59% (Home Row 73% -> 60%). Attributed:
    it is the trees, not the households (33 vs 30). Holding the low-skirted conifers to
    the village's cool edges bought 7 points back and cost nothing measurable — the square
    enclosure and the interleaving figures did not move. The two rulings pull against each
    other and the newer one wins by its own terms; if the roofs should come back it is one
    number.
 2  ONE CAMERA NOW OWNS 58 m OF QUIET ROAD (`northlane` owns `barn__gate-court`). Not a
    coverage failure; a district-pass question, filed in the cameras file's own note.
 3  p-gatefield spans 82 m of mostly-empty wooded road. A separate p-gateroad parcel — as
    p-woodroad was minted for the arrival — is the right shape at the district pass
    (coordinator agreed, deferred).
 4  Round 3's open items stand: the container/farmland tension, the mill pound ~1.9 m
    proud, the village faintly visible from the arrival road, `road-gate__orchard`
    refusing its lane incident.

DELIVERED: tools/emb_blockout.py (the wilderness boundaries, the village-tree pass with
its restated lane rule and camera corridors, the square-ring searches, the seclusion
corridor and `beyond_warmth`, the wall bite, two new probes); tools/geometry_audit.py
(SOFT_PART gains `_rail`, `_bramble`); public/townmap/emberbrook.cameras.json (the
gatefield camera's dead owned edge removed on the coordinator's explicit one-round
authorisation, citing stamp 306554a); tools/emb_rescale_shots.py + docs/qa/emberbrook/
rescale/ (19 frames — five new: the quiet road as a three-frame STRIP rather than an
aerial, because from above every road is short and every wood is thin, plus square-room
and village-trees); tools/blends/emberbrook-master.blend; public/assets/scenes/
emb-townwalk/ re-exported.

## THE RIM VISTA, ATTEMPTED AND REVERTED — the establishing shot the user asked for cannot
## be built in this pipeline, and the arithmetic says why (2026-08-01, carryover lane, round 2c)

RULING BUILT AGAINST: the coordinator approved the job change and quoted the user — "the
entrance scene should include a vantage point and camera angle that shows off the entire
dellhollow town and river." Two shots: a RIM VISTA taking the arrival/establishing duty, and
`gate` re-owned to the shrunken region so 40/42 might come inside the legibility floor.

=== WHAT THE SPLIT PROVED, AND IT IS WORTH KEEPING ON RECORD ===
The region split works exactly as the ruling predicted. Giving `gatehouse`, `porters-yard`
and their two edges to a new `rim-vista` shrank gate's region from a 21 m span to 11 m:
    gate standoff   28.59 m -> 21.26 m        (55/28, shrunken)
    yaw 40 / pitch 42   charPxFar 43 px (FAILED) -> 63 px (LEGAL), dist 27.30, inFrame 1.000
    stair from gate     28.0% -> 52.4% VISIBLE on the shipped plate
So the coordinator's hypothesis was RIGHT: shrinking the region does seat 40/42 legally.

=== AND IT STILL DOES NOT SHIP, FOR A REASON THE SWEEP HAD ALREADY RECORDED AND I MISREAD ===
40/42 flags `plate_flat` — a volume rendered as a card, >= 1.0% of frame — on the SHRUNKEN
region too. Round 2b had filed that flag under "distance defect", alongside the legibility
one. Only one of the two was about distance. The card is about the AIM: at pitch 42 the frame
fills with the flat rim ground regardless of how close the camera stands. A second instrument
disagreeing with my explanation should have been enough to check it before building on it.

=== THE VISTA ITSELF: THREE BAKES, AND THE ARITHMETIC THAT KILLS IT ===
Built as an authored pos/aim on the `boatyard` precedent, owning a small foreground patch so
`charPxFar` (which is measured over the OWNED region only) stays legal while the town beyond
is unmeasured background. That construction is sound and it is not what failed.
    v1  scored landmarks merely INSIDE THE FRUSTUM. Claimed 97.1% of the town; baked a
        grazing view along the town's face with the near cliff eating a third of the frame.
        "In frame != visible != unobstructed ray" is this repo's own doctrine and my
        instrument did not apply it.
    v2  ray-cast every target, and stopped scoring landmark CENTRES — they sit inside their
        own buildings and can never be reached, so the metric was under-counting by
        construction. Scored the town's 308 walk records instead. The honest ceiling
        collapsed from 97.1% to 47.1%, and the bake was a steep plan view of the quay.
    v3  added a horizon-level aim band and a down-angle filter (every v1/v2 aim point was
        down at the water, which forces a map view; a town reads as a town in ELEVATION).
        170 of 5760 candidates passed both gates; best 52.6% of the walk network, 47.4% of
        the river, 28.8 degrees of depression. Still one district, not a town.
THE ARITHMETIC, which is the actual finding and should stop the next attempt from starting:
the vista is anchored by its owned foreground patch, and cine_test's 50 px legibility floor
caps the camera at ~41 m from that patch. At fov 35 a 41 m standoff frames a 40-60 m swath.
DELLHOLLOW IS 100 m LONG. You cannot frame a 100 m town from 41 m away, and widening the fov
does not help because charPx falls with fov exactly as it falls with distance (fov 60 needs a
~50 m standoff for the width and gives ~32 px on the patch).
  SO THE ASK REQUIRES A SHOT CLASS THIS PIPELINE DOES NOT HAVE: a non-walkable cinematic
  establishing plate, where the player is a speck or absent and the legibility floor does not
  apply. That is a legitimate JRPG device and a deliberate pipeline decision — every shot here
  is currently assumed walkable — and it is NOT something to invent at the end of a shift.
  RECOMMENDED SHAPE, for whoever takes it: a `cinematic: true` flag that exempts a camera from
  CHAR_PX_MIN and from owning walk records, with the scene graph treating it as a fly-through
  plate on the ow-valley->del-cine portal rather than a walkable shot. Failing that, the ask is
  met by TWO vistas down the gorge, not one wider one.

=== REVERTED, AND WHY THAT IS THE RIGHT END STATE ===
The full split shipped RED: cine_test 2 failed, seam_test 2 failed, plate_flat 2 of 17, and
arrives-invisible went 3 -> 4 — the two new gate<->rim-vista cuts arrived at 0.0%/0.0% and
3.6% chest, and the ow-valley portal (the town's front door) got WORSE, 32.1% -> 3.6%. Three
of those are repairable with more arrival searches and bakes; the plate_flat card and the
vista's brief are not. Reverted to d022acf. Working tree verified green afterwards:
cine_test 643/0, seam_test 294/0, seam_walk 9/9, plate_flat 0 of 16, routes clean,
arrives-invisible 3, stair from gate 32.9%.
  WHAT IS LOST BY REVERTING, stated plainly: the 52.4% stair frame. It is real and it is
  measured, and it is unavailable until either plate_flat's card is solved at pitch 42 or the
  cinematic shot class lands and takes the arrival duty properly.
  NOTE FOR THE NEXT SESSION: `cine_test` is currently RED AT HEAD and it is NOT this lane's —
  the Emberbrook lane committed 29eb78d with cameras.json edits and without re-deriving the
  shared public/world/scenegraph.json. One `node tools/scenegraph_derive.mjs` in their lane
  closes it; I left it alone rather than commit another lane's derive.

## STYLE PROBE — Emberbrook watermill corner (taste input only, NOT canon)
2026-07-31. Renders: `docs/qa/emberbrook/styleprobe/probe-a.png` (3/4 plate of the corner) and
`probe-b.png` (wheel + pit detail). Purpose: the ratified blockout reads low-poly next to
Dellhollow, and the user asked for ONE district dressed to the finished bar before broad
build-out, purely to give style input.
  WHAT THIS IS NOT. HAND-AUTHORED geometry in a THROWAWAY blend
  (/tmp scratch, `mill_probe2.py`, not committed to tools/). Searched-not-authored and
  determinism DO NOT apply — nothing here was measured, nothing snaps to the map, no pipeline
  file, camera file, or map JSON was touched, and the master blend was never opened. The
  numbers that ARE honoured are the wheel ruling's (2.2 m overshot wheel, 2.0 m dam, leat +
  head gate + impounded millpond) so the shapes are the ruled shapes and not a fantasy.
  MATERIAL VOCABULARY PROPOSED, for the user to accept or redline: roof = laid cedar-shake
  COURSES on the mill (Dellhollow's mat_shingle_cedar/mossy, ~340 individual shakes with
  mossy patches at the eaves) against ROLLED THATCH BUNDLES on the cottage, so the two roof
  materials separate the working building from the household; timber = Dellhollow's
  mat_timber_dark for frame/posts/braces over lime-daub infill, mat_wallwood for the paler
  sawn boards (flume, doors, buckets), so the frame reads darker than the boarding; water =
  three treatments, a still impounded millpond, a falling sheet + plunge foam at the dam, and
  water RIDING IN THE DESCENDING BUCKETS so the wheel reads as working; foliage = clustered
  overlapping blobs on real branch tips (autumn/green mixed per tree) with translucency so the
  low sun lights leaves through, plus blade-fan groundcover — deliberately not cones and not
  cards; boundary = dry-stone row of individual field stones with slumped gaps, rail-fence
  fragments where the stone gives out, bramble spilling over onto the wild side.
  Light: golden-key sun (3.4 W, warm) with warm bounce + practical window/lamp glows,
  AgX Medium High Contrast, exposure 0.35 — a bright cousin of the emberwake grade, chosen so
  the DRESSING is legible; the shipped emberwake numbers (exposure 0.55, sun 0.75, sky 0.55)
  are unchanged and untouched by this.
  KNOWN ROUGH EDGES, so nobody mistakes probe quality for finished quality: the wheel's bucket
  back-plates project past the shrouds and read slightly cog-like; groundcover is uniform
  scatter with no density variation; the far treeline is 22 copies of the same generator; no
  props, no NPCs, no bake, no depth pass.

## THE CINEMATIC SHOT CLASS, AND THE FIRST THING ITS CAMERA FOUND — a plate that shows
## the whole town, and a rail lying across the town's only way in
## (2026-08-01, Dellhollow carryover lane, round 3)

RULING BUILT AGAINST: the coordinator approved a `cinematic: true` shot class — a
non-walkable establishing plate exempt from CHAR_PX_MIN and from owning walk records —
with the instruction to keep the exemption NARROW.

=== THE CLASS, AND WHERE ITS FENCE IS ===
The exemption is two lines of code; the fence is the rest of the work, and the fence is
what makes it safe to have. `cine_test` gained a CINEMATIC section that asserts a plate
owns zero walk meshes AND zero map records, that no seam targets it as a destination or
leaves from it, that no door is offered in it, that it is not the cut graph's entry shot,
and that it reports charPx/inFrameFrac as NULL rather than as a number. Without those the
flag is a loophole: any under-legible walkable shot could be relabelled a plate and stop
being measured. `seam_test`'s NO-SLIVER rule is exempted for the same reason and states
it: that rule exists to catch a second camera standing on somebody else's floor, and a
plate stands on no floor at all, so its premise is absent rather than merely unmet.
  BACKWARD-COMPATIBLE, MEASURED: with the class in and no plate authored, cine_test went
  643/0 -> 646/0 (the three new assertions), nothing else moved.

=== THE HANDOFF NEEDED NO RUNTIME MECHANISM, AND THAT IS THE DESIGN ===
A plate owns no walk record, so it appears in NO ownership region, so play3d's positional
safety net finds the arriving player on the walkable shot's ground under a camera that
owns none of it and corrects. "Shown on arrival, then hands off to the first walkable
shot" is the safety net doing exactly the job it was built for, arriving on purpose
instead of after a slide. The portal edge carries `handoff:{key}` so the wiring STATES
which shot that is instead of leaving it to be re-derived.
  VERIFIED IN THE REAL RUNTIME (browser, SIM, localhost:3000), not argued:
    on arrival        shot 'vista', 17 shots baked, 16 ownership regions (the plate has none)
    corrTarget        'gate' on the first tick, corrections 0
    after the grace   shot 'gate', corrections 1, cuts 0, and THE PLAYER DID NOT MOVE
                      (13.58,24.07,-5.157 before and after) — a correction moves the
                      camera, never the body
  THE HOLD IS defaults.correctionGrace = 20 sgTicks. sgCorrect is called from sgTick and
  sgTick runs once per phys(), which runs once per rAF frame, so that is ~0.33 s at 60 fps
  plus the 350 ms fade. STATED AS A CONVERSION, NOT A STOPWATCH READING: the MCP tab is
  visibilityState 'hidden', rAF is throttled there, and the wall-clock could not honestly
  be taken. 0.33 s is enough to prove the mechanism and far too short to read an
  establishing shot. AN AUTHORED, SKIPPABLE DWELL IS A play3d.html CHANGE AND play3d.html
  IS COORDINATOR-OWNED — requested, not taken.

=== THE PLATE: SEARCHED, AND THE HEADLINE IS A TRADE RATHER THAN A MAXIMUM ===
tools/cine_vista.py (new). 11 664 candidates swept, plus a 2 560-candidate local
refinement, scored by Blender ray-cast over the town's own 308 walk records (3 080 chest-
and head-height points) and over 320 points ON THE WATER MESH ITSELF.
  THE PLUMBING THAT MAKES THE NUMBER MEAN SOMETHING: cine_solve gives a cinematic camera a
  probe set spread over EVERY walk mesh rather than an owned region, and that set does not
  depend on pos/aim — so the 64 points the search ranks by ARE the 64 points cine_bake
  ray-casts. Search predicted 65.6%; the bake measured 65.6%. Prediction and measurement
  are the same instrument by construction, so a disagreement would be a defect and not a
  methodology gap.
  THE FIRST FULL SWEEP RETURNED THIRTY AERIAL PHOTOGRAPHS, and that is a fact about the
  metric, not about the town: coverage rises MONOTONICALLY with altitude, because every
  occluder in a canyon town is beaten by getting above it. Global best 74.4% at 38 degrees
  of depression, camera at h 93.7 — and the render of it is a contour map with the terrain
  tile's own cut edges in frame. The finalists are therefore a PARETO FRONT OVER
  DEPRESSION, not a top-N, because the down-angle is the thing being traded away.
    THE CEILING PER DEPRESSION BAND (town coverage, ray-cast, 3 080 points)
      8 deg 59.9%  |  14 deg 61.7%  |  20 deg 63.5%  |  26 deg 64.1%
     32 deg 70.5%  |  38 deg 74.4%
    The whole trade from 8 to 26 degrees is 4.2 points. The 15 points above it are bought
    by leaving the canyon. Renders of the three ends of that curve are the evidence:
    docs/qa/districts/vista_band_depr08 / _depr26 / _depr38.png — at 8 degrees a town in
    elevation, at 26 a diorama of roofs, at 38 a plan.
  SHIPPED: pos [-15.156, 84.198, 29.193] aim [32, 28, 13.6] — the far rim across the gorge,
  75 m out, upstream, camera at h 29.2, which is a height a person could stand at.
      town visible          61.2%  of the walk network by ray-cast (100% in frame)
      river visible         15.0%  of the pool surface
      bake's own visibleFrac 65.6% over its 64 shipped probes
      depression            12.2 deg
      the arriving player   26 px tall at 78 m — a speck, as the ruling allowed
  FOR SCALE: the best a WALKABLE shot ever reached was 52.6% (round 2c), and it could not
  ship at all — the 50 px floor caps a walkable camera at ~41 m, which at fov 35 frames a
  40-60 m swath, and Dellhollow is 100 m long.
  THE RIVER NUMBER IS LOW AND IT IS NOT A FRAMING FAULT: 57.5% of the pool is in frame and
  only a quarter of that survives the ray-cast, because the gorge's near bank hides the
  water from any angle shallow enough to read the town in elevation. 26 degrees buys river
  (29.1%) and spends the town (57.1%). The split between "out of frame" and "occluded" is
  reported per candidate precisely so that trade cannot be misread as bad framing.
  AN INSTRUMENT CORRECTED MID-SEARCH, because it was wrong in the v2 way: river coverage
  was first sampled on a GRID OVER THE POOLS' BOUNDING BOXES. The boxes span y 22.8..74 and
  the water inside them is a channel, so most of that grid sat over the far bank where it
  is occluded by terrain — under-reporting by construction, the same error as scoring
  landmark centres. It now samples the water mesh's own polygon centres.

=== THE HAZE WALL: THE ROUND-2b CROSSING LESSON, ARRIVING A THIRD TIME ===
The plate's background carries a corduroy-textured translucent slab. IDENTIFIED, not
guessed: `fx_haze_south`, an eight-vertex box 172 x 2.7 x 53 m standing at y ~ -1 just
beyond the cliff top. It is the first camera hit for 71% of the ndc box x -0.70..-0.20 /
y +0.10..+0.90 (60x60 ray census).
  IT MUST NOT BE DELETED, and this is why the census was run over every shipped plate
  before anything was proposed: it is the first hit for 22.3% of `gate`, 23.9% of
  `loop-stairs`, 24.3% of `lockhead` and 19.4% of `cottage`, where it reads correctly as
  air. It does real work; the vista is simply the first camera to see it from OUTSIDE.
  A town's far field is built for the angles it has been shot from. FILED FOR AN ART LANE:
  it is a shading question, not a camera one, and re-aiming to dodge it would cost the shot.
  plate_flat does NOT flag it and is right not to: 0 of 17 plates carry a card, vista's
  own reading is 0.61% against the 1.0% bar, and the slab is neither constant-coloured nor
  at the far plane. It is a shaded volume that reads wrong, which is a different class from
  a volume rendered as a card.
  ONE PIPELINE QUESTION ANSWERED AND CLOSED: does the haze corrupt the visibility oracle?
  Every render-only volume was deleted and all 17 shots re-probed. 0 OF 17 MOVED, to the
  last decimal. The oracle is unaffected, so cine_bake's ray-cast is left exactly as it is.

=== AND THE THING THE NEW CAMERA'S ROUND FOUND ON THE GROUND: gs_rail LIES ACROSS THE
=== GATE STAIR, AND IT IS THE TOWN'S ONLY WAY IN ===
Briefed as a five-minute check: "landing-drop body-box check, 0.69 m vs STEP_DN 0.60".
  FIRST, A CORRECTION TO THIS LOG. play3d.html's STEP_DN is 0.8, not 0.60, and has been
  since efb811c on 2026-07-28 — three days before the entry that cited 0.60. The 0.69 m
  drop from the landing to tread t02 is INSIDE the step-down window and was never the
  defect. A wrong constant in a note is exactly the failure the documentation bar names:
  it made a real obstruction look like a solved arithmetic question.
  WHAT IS ACTUALLY THERE, measured with the real body against the shipped del-cine GLB.
  Standing on `walk_e_valley-gate__inn_landing` (top h 22.30) and walking DUE EAST, one
  line per z, 120 steps each:
      z -2.45 .. -3.50   (8 lines, 1.05 m of the flight's width)   STOPPED at x 21.975
      z -3.65, -3.95     (2 lines)                                 descend to t02 at 21.61
      z -3.80                                                      reaches t01 at 21.99
  So the walkable width of the flight at its landing is a gap of roughly 0.35 m at the
  south edge, and the town's own derived route (`shelf-west:valley-gate__inn@0.428..1`
  runs [21, 22.3, -3.2] -> [22.25, 21.35, -3.1]) goes straight through the blocked part.
  THE BLOCKER IS NAMED, by triangle-level intersection of play3d's OWN body box — y from
  max(g + STEP_UP + .02, P.y + .02) to g + BODY_H, i.e. 22.32..22.91 for this step:
      z -2.45, -2.90, -3.20, -3.50   ->  gs_rail
      z -3.65, -3.80, -3.95          ->  (nothing)
  `gs_rail` has 86 vertices inside x 21.9..22.6 / y 22.0..23.2, spanning z -3.23..-2.51 at
  y 22.11..22.60. It is a handrail lying ACROSS the walkway instead of alongside it — the
  "an invisible wall across a walkway; a bar_ is not non-solid" class the loop-stairs lane
  named, now on the gate stair.
  ITS PROVENANCE IS AN OPEN CARRYOVER: tools/gs_build.py derives every rail from the
  `bar_e_valley-gate__inn*` blockout objects, and "the stale bar_ rails across five
  districts" is carryover item 3, already re-scoped to a REDESIGN (rope fences town-wide).
  So two tracked items are one measured defect.
  WHY IT MATTERS MORE THAN ITS SIZE: `valley-gate__inn` is the ONLY exit `scenegraph.json`
  offers from `gate`, the entry shot. Three rounds of work have gone into making that
  staircase legible from the gate camera — a terrain ceiling of 26.8%, a 90-composition
  sweep, a region split — while the flight itself has been three-quarters blocked at body
  height. The user's own screenshot said "staircase very occluded, HARD TO NAVIGATE" and
  the second half of that sentence has been read as a consequence of the first.
  NOT CLAIMED, AND THE CAVEAT IS THE SAME ONE THIS LOG RAISED LAST TIME: a naive waypoint-
  chasing steerer was also run down the full route and stalled lower on the flight, at
  h 19.77, in both directions. That is NOT reported as a defect. The flight is a
  switchback, and a straight-line chaser between two points of one switchback cuts across
  the other leg — cine_test's own simSeam walks by ARC LENGTH for exactly this reason.
  Only the single-direction z-scan above is steering-independent, and only it is claimed.
  ONE HARNESS TRAP WORTH KEEPING: the first route run reported "0 cuts fired, blocked at
  the landing". It was wrong. transitionTo takes UILOCK and freezes phys() for the 350 ms
  fade, and in a throttled background tab that reads as a stalled walker. A stall detector
  on this runtime must skip ticks where SIM.cine().busy is true. With that fixed the cut
  fires and the shot changes to shelf-west, as it always did.

=== GATES ===
  cine_test 668/0 (+2 soft, both pre-existing: boatyard's accepted 28% frame and bake
  staleness)   seam_test 295/0 (+8 soft)   seam_walk 9/9   plate_flat 0 of 17
  routes --check clean at 17 shots   slice_test 670/16, unchanged and attributed (the
  Emberbrook lane's pending emb-cine bake, not chased)
  DELIVERED: tools/cine_vista.py (new); tools/cine_regions.mjs, cine_solve.mjs,
  cine_test.mjs, seam_test.mjs, scenegraph_derive.mjs (the class); dellhollow.cameras.json
  + solved + routes.json + scenegraph.json; public/assets/scenes/del-cine/cameras/vista/.
  Commit 749ed4f.

=== NOT DONE, AND THE SEQUENCING ARGUMENT FOR WHY ===
The region split re-attempt and the shop-row recomposition were briefed and are not done.
The split's entire purpose is to let the `gate` camera show more of the staircase at
valley-gate__inn. That staircase is blocked across three quarters of its width by its own
rail. Composing a better picture of it is optimising the photograph of a broken thing, and
this round was briefed on the principle that the previous attempt failed because it was
SEQUENCED wrong. The same argument applies here: gs_rail first.

## THE RAIL COMES OUT — a rope fence on the gate stair, the instrument that should have
## caught it, and a salted hash that had been quietly randomising the master
## (2026-08-01, Dellhollow carryover lane, round 3b)

RULING BUILT AGAINST (coordinator, on the finding logged above): surgery approved, scoped
as the first act of the already-ruled rails redesign — do not merely delete the offending
bars, rebuild the flight's railing as the rope-fence vocabulary from the CURRENT map with
the full flight width clear, then sweep every rebuilt rail against the walk network.

=== FIRST, THE INSTRUMENT, BECAUSE THE DEFECT'S REAL CAUSE IS THAT NOTHING COULD SEE IT ===
`tools/walk_bodygate.mjs` (new). Three gates existed and all three were blind to this
class, for one reason each, and the reasons are worth keeping:
  master_walk_qa [3]  fires ONE ray down and ONE up per 0.35 m sample. A rail BESIDE a
                      sample is not under it.
  master_walk_qa [4]  HEADROOM wants 2.0 m clear ABOVE the surface. This rail's top stood
                      0.30 m above the landing.
  GateGrid            faithfully reproduces that same ray contract so a BUILDER can
                      pre-check itself — and therefore inherits the blind spot by
                      construction, and hands it to every rail built through it.
  cine_test/seam_test reason about the walk network as RECORDS and REGIONS. Neither has
                      ever asked whether the geometry BETWEEN two records is passable.
A ray is not a body. The new gate is the body: it reproduces play3d.html's walkStep()
with the constants copied from it, settles the foot with walkGround's own window, and
intersects the character's box — floor at max(gB + STEP_UP + .02, gA + .02) — with real
triangles, by exact triangle/AABB SAT.
  CALIBRATED BEFORE IT WAS TRUSTED, and the first version was wrong. At a 0.25 m lattice
  it reported 1 293 blocked steps in the gate district; 30 of them were driven through the
  REAL runtime in Chrome and only 4 stopped the body. The lattice was the bug: phys()
  moves 0.075 m per step and evaluates at every one, so a 0.25 m hop is a step the walker
  never takes in one piece. At the runtime's own stride the sampled precision on seatable
  points went to 12 of 21, and it is per-object rather than uniform:
      gs_rail 2/2, gate_barrier 3/3, t2c_G4_arch_banner 2/2, t2c_G7_bunting_gate2 2/2
      gate_arch 0/3, gs_treads 0/2, shelf_stair_underworks 0/1   (false positives)
  SO IT IS A SCREEN, NOT A VERDICT — plate_flat's own words, and the same standing. It
  produces candidates for a body to confirm. It runs in 2 s on a district.

=== THE SURGERY, AND THE PLACEMENT RULE IS DERIVED RATHER THAN LIKED ===
`gs_build.py` section 2 rewritten. It no longer reads a `bar_` object at all: the old rail
took its LINE from the `bar_e_valley-gate__inn*` blockouts' BOUNDING BOXES, a near-square
box fell through both aspect-ratio branches into a diagonal fallback, and a diagonal
across a landing is a rail across the stair — and those blockouts are the ones carryover 3
records as stale. The line now comes from the same leg geometry the treads and cheek walls
already come from, which is the current map by construction.
  AND THE GATE CHANGED, WHICH MATTERS MORE THAN THE VOCABULARY. Every part is refused
  unless it clears a BODY ENVELOPE as well as the ray grid. The envelope's floor is PER
  SAMPLE and step-aware, and the first version was a veto rather than a test:
      floor = surface + 0.02 everywhere      refused 7 parts of 12 — the same failure
                                             GateGrid's docstring records for free_box
                                             (19 of 38 posts on the crossing, 23 of 24 on
                                             the moorage flight)
      floor = surface + STEP_UP + 0.02,      213 of 524 samples are at a brink; 6 refusals,
      dropping to (lower neighbour + 0.02)   and they are printed, because a rule that
      at a BRINK                             fires silently cannot be reviewed
  THREE LINES WERE BUILT AND MEASURED, not argued:
      hw + 0.455 (outboard of the cheek wall)   5 posts of ~15 stations
      hw + 0.21  (ON the wall, where a real one stands)   3 posts
      hw + BODY_R + POST_R + 0.02  (SHIPPED)    6 posts + 3 rope runs, 0.38 m clear
  THE RULE THAT FALLS OUT OF IT IS THE DEFECT RESTATED: on a stair EVERY sample is a brink
  — there is always a lower tread within one stride — so the body box floor is always the
  height you stepped from, and ANY furniture within BODY_R of the tread edge is inside
  somebody's step. The cheek walls survive only because they stand 0.38 m proud, below
  STEP_UP. That is a fact about the flight's width budget (1.4 m flight, 0.60 m body) and
  it is why the fence is sparse; it is not a fence that can be thickened by wanting it.
  VOCABULARY: posts at 1.20 m, two ropes at 1.00 and 0.55 m built as four-segment
  catenaries with 0.07 m of sag, because a straight cylinder at handrail height IS a
  handrail and the sag is what makes it read as rope at this town's shot distance.

=== THE MEASUREMENTS, BEFORE AND AFTER, WITH THEIR INSTRUMENTS ===
  walk_bodygate, region x 14..30 z -8..2, 94 553 legal steps at the runtime's own stride:
      gs_rail blocked steps        3 008  ->  20      (-99.3%)
      all objects                 13 523  ->  11 075
      samples with every exit blocked  2 299 -> 1 831
  THE BODY ITSELF, in the live runtime, the same z-scan that found the defect — stand on
  the landing at h 22.30 and walk due east, one line per z:
      lines that descend the flight    2 of 13  ->  12 of 13
      the route's own line (z -3.1..-3.2)  stopped at x 21.975  ->  runs to x 24.45, h 20.40
      distance travelled on that line   0.375 m  ->  2.85 m
  STILL NOT CLAIMED, and the caveat is unchanged: a naive waypoint-chasing steerer still
  stalls lower on the flight at h 19.77. The flight is a switchback and a straight-line
  chaser cuts across the other leg. The steering-INDEPENDENT scan at that level shows the
  lower leg IS passable, in a band about 0.2-0.4 m wide at x ~ 22.9 (x 22.9 descends 3.68 m
  to h 19.04; x 22.7 gets 0.83 m; the rest have no surface at that height). Narrow, and
  recorded as a measurement rather than as a verdict.

=== A SALTED HASH HAD BEEN RANDOMISING THE MASTER, AND IT WAS FOUND BY THE HOUSE RULE ===
Two runs of the unchanged builder against the unchanged master differed: `gs_treads`
z-min 19.27 vs 19.24. The cause is exact — `plank_fill(..., seed=k * 7 + hash(legname) %
101)`. Python's built-in `hash()` is salted per process (PYTHONHASHSEED), so every run drew
a different plank layout. Replaced with `zlib.crc32`; two runs now agree to the printed
decimal. This is pre-existing and not introduced by this pass, and it is exactly what the
determinism rule is for: the gate is a CONTENT digest, and a salted hash silently defeats
it everywhere it appears. WORTH SWEEPING FOR ELSEWHERE — this is unlikely to be the only
`hash()` in a builder.

=== GATES ===
  cine_test 668/0 (+2 soft)   seam_test 295/0 (+8 soft)   seam_walk 9/9
  plate_flat 0 of 17          routes --check clean at 17 shots
  slice_test 670/16 — back to the recorded baseline, the Emberbrook lane's pending
                      emb-cine bake, attributed not chased
  master_walk_qa      FAILED (22) BOTH BEFORE AND AFTER, run against a copy of the
                      pre-surgery master as a control. All 22 are the stale `bar_` reds of
                      carryover 3; this pass edits no walk_/bar_ mesh and added none.
  THE SEAM MOVED, and it is a real consequence rather than churn: the cut band's
  half-width is measured off the walk surface at derive time and the collision GLB
  changed, so gate<->shelf-west sits at valley-gate__inn t=0.428 -> 0.381, band 2.25 ->
  1.40 u, clearance margin 0.056 -> 0.138 u. The scenegraph diff was scoped before it was
  taken: it touches ONLY those four del-cine edges, nothing of another lane's.
  NO CAMERA MOVED: cine_solve re-run, all 17 pos/aim byte-identical, so the four rebakes
  (vista, gate, shelf-west, shelf-east — DERIVED by projecting the changed geometry's
  eight bbox corners through every solved frustum, 8/8, 8/8, 8/8, 4/8) are art-only.
  RECORD SHOT: docs/qa/districts/gs_ropefence_after_gate.png

## THE ENTRANCE IS THE VISTA — the user did not want a cutscene, and the reshape costs the
## front door its arrival to a named clump of rim scrub (2026-08-01, carryover lane, 3c)

USER'S CORRECTION, via the coordinator, and it supersedes the plate this lane shipped four
hours earlier: "the town entrance camera angle for that scene should actually be a
cinematic camera angle (so not a cutscene), but the actual framing for the normal entrance
shot should be a cinematic vista." Not a plate on the portal. A NORMAL PLAYABLE SHOT whose
composition happens to be a vista.

=== WHAT CHANGED, AND THE CHEAPEST HONEST SHAPE OF IT ===
The `vista` camera is DELETED and `gate` — which already owned the entrance region — took
its pos/aim. One camera, one shot, nothing dangling; the alternative (keep the plate,
un-referenced) leaves a baked, tested, unreachable camera in the file for a future reader
to wonder about. The portal into town now reads `cam: {key: gate}` with no `handoff`, which
is what it read before this lane touched it.
  THE `cinematic: true` CLASS STAYS IN THE TOOLS, with zero cameras using it. It is gated,
  argued and backward-compatible, cine_test's CINEMATIC section now reports "0 plate(s)"
  and still asserts every bound it did with one. When a real cutscene is wanted the class
  is there and does not have to be re-derived from an argument nobody wrote down.

=== THE LEGIBILITY FLOOR IS OVERRIDDEN PER SHOT, NAMED, AND RATCHETED ===
A vista and the 50 px floor cannot both hold: the floor caps a walkable camera at ~41 m,
which at fov 35 frames a 40-60 m swath, and Dellhollow is 100 m long. The temptation is to
lower the town floor, which would silently re-grade all sixteen shots. Instead
`charPxMin` is a per-camera field, cine_test ENFORCES the override rather than waiving the
check, and an override is only legal if it is lower than the town floor AND accompanied by
a `_charPxMin_why` in the same record — so no future reader meets a bare number.
    gate    charPxMin 24    measured 32 px near, 24 px far, 75 m standoff
THE VALUE IS THE SHOT'S OWN MEASUREMENT WITH NO HEADROOM UNDER IT, deliberately. A floor a
couple of pixels below the measurement is a number fitted to the frame and would absorb the
next regression in silence; set exactly at it, this is a ratchet — one pixel of loss fails
the gate and has to be argued.

=== WHAT THE RESHAPE BOUGHT, AND WHAT IT COST, BOTH MEASURED ===
BOUGHT — the thing three rounds of camera work were chasing:
    gate stair VISIBLE from `gate`   32.9%  ->  37.8%   (shot_probe, against the SHIPPED
                                                         baked depth maps, same instrument
                                                         as the 32.9%)
  That is above the 31.7% ceiling the 90-composition sweep found across ALL 90 candidates,
  and above round 1's 26.8% terrain ceiling. ATTRIBUTION NOT SEPARATED, and it must not be
  claimed as the framing's alone: `gs_rail` came off the same flight in the commit before
  this one, and both changes are in this number.
COST — and it is the one open item:
    ow-valley -> del-cine portal arrival   32.1% chest  ->  0.0%   ARRIVES INVISIBLE
    shelf-west -> gate cut arrival        100.0% chest  ->  0.0%   ARRIVES INVISIBLE
  Town-wide the count is unchanged at 3 (the gate portal was already one of them, and the
  cookhouse door is the third), but one is new and one got worse, and the front door of the
  town is not a place to leave at zero.

=== THE CAUSE IS ONE OBJECT AND IT IS NOT THE FRAMING ===
Ray-cast from the new camera to each arrival, 18 rays over a body grid at chest and head:
    portal arrival            18 of 18 rays blocked by `veg_gate_rimclump_26`, alone
    shelf-west>gate arrival   rimclump_14 x10, rimclump_9 x6, rimclump_0 x2
    gate's own 64 region probes   23.4% clear | rimclump_26 23.4% | awning 10.9% |
                                  rimclump_0 6.2% | tarp 6.2% | rimclump_14 6.2% | ...
  The rim SCRUB is roughly 42% of the occlusion and the architecture about 17%. This is
  "move the occluder, not the aim", and the occluder is vegetation — which in this project
  is SEARCHED, not authored, so re-seating a clump is a re-run rather than art surgery.
THE ARRIVALS LAYER CANNOT PAY FOR IT, and that was tested rather than assumed: 853
candidate standing points in gate's own region were ray-cast from the new camera.
    portal   33 points >= 60% visible, the nearest 6.9 m away, the best 8.1 m
    cut       0 points >= 60% within 9 m; lowering the bar to 20% gives 124, the best
              50% at 5.82 m
  Round 2b's ruling stands and is why none of them was taken: candidates are ranked by
  DISTANCE FROM THE SEAM, NOT BY SCORE, because teleporting a player 6 m off the flight
  they were walking is a worse defect than the one being repaired. An override here would
  trade a hidden arrival for a wrong one.

=== MITIGATIONS TAKEN, AND WHAT nav_eval MUST CHECK WHEN THE KEY RETURNS ===
TAKEN: the framing itself holds 100% of the owned region in frame at 75 m (independently
re-projected, 396 of 396 region points), so nothing is off-plate; the exit toward town is
the gate stair and it is at its best measured visibility ever from this camera (37.8%); the
seam, the cut band and the hysteresis margins are untouched and green.
NOT TAKEN, and named so the next round does not re-derive it: the rim-clump re-seat. It is
one builder re-run against a probe set that now exists (gate's own 64 probes plus the two
arrival points), and it is worth ~23 points of region visibility from `veg_gate_rimclump_26`
alone.
FOR nav_eval AT N=10 WHEN GEMINI_API_KEY IS TOPPED UP — registered now so it cannot be
fitted afterwards: this shot is 24 px at the far corner against a town floor of 50, so the
prediction is that `onWalk` and `progress` hold roughly at round 2a's 0.81/— because the
route and the walk network did not move, while `stuckLegs` should FALL because the flight
is no longer blocked by gs_rail. If the score instead collapses, the reading is that 24 px
is below what the judge can follow, and that is a finding about the user's framing
direction rather than about this town — report it as such and do not quietly re-aim.

=== GATES ===
  cine_test 647/0 (+3 soft)   seam_test 294/0 (+8 soft)   seam_walk 9/9
  plate_flat 0 of 16          routes --check clean at 16 shots
  slice_test 670/16, the Emberbrook lane's pending emb-cine bake, attributed
  THE THIRD SOFT WARNING IS NEW AND IT IS THE COST ABOVE, not noise: gate's visibleFrac is
  23% of its 64 region probes against the calibrated 45% bar. It is soft by design and it
  is the same number the occluder census explains.
  Only `gate` moved; the other fifteen re-solved byte-identical, so one rebake.
  RECORD SHOT: docs/qa/districts/gate_vista_entrance.png

## THE RIM RE-SEAT — the front door comes back, the return arrival is proved unbuyable,
## and the region split is measured moot (2026-08-01, carryover lane, round 3d)

RULING: re-run the vegetation search with the two arrival sightlines as PAID constraints,
floors taken from the pre-reshape values, print achieved-vs-floor; rim scrub stays welcome
where it crosses no paid line.

=== WHERE THE WORK WENT, AND WHY NOT WHERE IT LOOKED LIKE IT SHOULD ===
`gate_build.py` carries a loud header: DO NOT RE-RUN AGAINST THE LIVE MASTER — its clear
pass rebuilds the whole district and silently undoes accepted legibility surgery. So the
re-seat went where that surgery already lives: `ga_build.py`, the gate ARRIVAL pass, which
already does per-leaf-card raise-or-thin against sightlines from the solved gate camera,
with `GA_SRC_*` snapshots so a re-run recomputes from pristine geometry. Three changes:
 1  THE OCCLUDER LIST IS DERIVED, NOT NAMED. The 2026-07-30 five were ray-attributed by
    hand from a camera standing 29 m out at yaw 55; `gate` now stands 75 m out. A hand-named
    list is a fact about one camera position. Now: ray-cast the paid body grids and the
    shot's own 64 solved probes, keep first hits this pass may own (gate-district
    vegetation), rank by rays cost. It returns rimclump_26(45), _14(19), _9(13), _0(7),
    _5, _4, _2, _11 — which is the occluder census from three hours earlier, re-derived by
    the tool instead of by me.
 2  RESTORE EVERY SNAPSHOT, not just the current list. Otherwise a clump the OLD camera
    needed lifted keeps its lift forever after it stops being an occluder, and the pass
    stops being idempotent the first time the list changes.
 3  FOLIAGE IS MATCHED BY MATERIAL FAMILY. The old list all carried `mat_leaf_autumn`, so
    an equality test sufficed; the rim scrub is cloned from twelve source bushes and
    `veg_gate_rimclump_26` carries none of it — the equality test asserted the pass to a
    halt on the first run. The trunk rule is unchanged, which is the part that matters.

=== THE PAID LINES, ACHIEVED VS FLOOR ===
    portal ow-valley>del-cine    achieved 50.0%   floor 32.1%   OK
    cut shelf-west>gate          achieved  0.0%   floor 100.0%  UNDER
  9 leaf cards lifted on rimclump_26, max 0.94 m, mean 0.45 m, 0 thinned away, no trunk
  moved. Only 5 of the 20 paid rays were WINNABLE at all, and the pass says so before it
  lifts anything — a ray blocked by something this pass may not touch cannot be used to
  justify cutting foliage that was never the reason.
THE FIRST RUN LIFTED NOTHING, and the reason is worth keeping: the per-card raise only ever
moves a card that blocks a member of the sample set, and the paid arrivals were being
REPORTED against but were not IN it. A constraint you measure but do not feed to the
optimiser is a report, not a constraint. They are now added to `SAMP` after the same
with-scrub-hidden filter every other sightline gets.

=== 50% IS THE CEILING, NOT A SHORTFALL — AND THE RETURN ARRIVAL IS UNBUYABLE ===
Both stated because "achieved 50%" and "achieved 0%" mean nothing without knowing what was
available. With ALL EIGHT derived clumps hidden, the 10 rays to each arrival read:
    portal   5 CLEAR, 5 blocked by `gate_clutter`
    cut      0 clear: gate_yard x2, t2c_G4_arch_banner x2, t2c_G3_awning_tollyard x2,
             gate_palisade x1, gate_arch x1, veg_gate_rimtreeE_0 x2
  So the portal line's vegetation ceiling IS 50% and the pass reached it exactly. The
  shelf-west>gate return arrival is behind the gate's OWN ARCHITECTURE — the yard, the
  arch, the toll-yard awning, the palisade — and vegetation cannot buy back more than the
  2 rays of `rimtreeE_0`. It is not a scrub problem and no re-seat will fix it.
  THE REMAINING LEVERS, none of them this lane's to pull: move the arrival (refused —
  round 2b's rank-by-distance rule, the nearest >=60% point is 5.8 m off the flight), cut
  the toll-yard awning and the arch banner (architecture, and the arch IS the shot's
  subject), or accept it.

=== THE ACCEPTANCE NUMBERS, AND TWO INSTRUMENTS THAT DISAGREE BY DESIGN ===
  arrival_probe --scenegraph, against the SHIPPED depth plates after the rebake:
    ow-valley>del-cine portal    0.0% / 0.0%  ->  20.9% chest / 42.9% body
    shelf-west>gate cut          0.0% / 0.0%  ->   0.0% / 0.0%   (as measured above)
  ga_build's own build-time ray grid put the portal at 50.0%. THE TWO DO NOT AGREE AND
  MUST NOT BE AVERAGED: ga_build casts 10 rays at a body grid against the live blend;
  arrival_probe reads 91 body samples against the baked depth plate. Different sample
  counts, different oracles, one before the bake and one after. The build-time number is
  the prediction the optimiser steers on; arrival_probe is the acceptance. Both are
  recorded so neither can be quoted as the other.
  STILL FLAGGED, 4 town-wide: the gate portal (improved but under the bar), the
  shelf-west>gate cut (this round's, and proved unbuyable), the cookhouse door
  (pre-existing), and `cottage>lockhead` at 68.1%/17.9%. THE LAST IS NOT THIS ROUND'S and
  the reason is checkable: arrival_probe reads the RECEIVING camera's plate, `lockhead` has
  not been rebaked since 6d2dbb5, and neither its plate nor its arrival was touched here.
  The "3" this round has been comparing against came from round 2b's entry, not from a run
  taken at the start of this session — a baseline quoted from a note rather than measured
  is exactly what the documentation bar warns about, and it is corrected here.

=== THE STAIR NUMBER, RE-MEASURED FOR ATTRIBUTION AS ASKED ===
    gate -> valley-gate__inn   37.8% VISIBLE, UNCHANGED by the re-seat (37.8% before it)
  So the +4.9 points over the old 32.9% belong to the gs_rail removal and the vista
  framing, and NOT to the rim clumps: the nine lifted cards sit over the portal arrival at
  the west end of the rim, and the flight is 8 m east of them. The re-seat neither helped
  nor cost the staircase, which is the cleanest possible attribution and is why it was
  worth re-running the probe rather than assuming.

=== THE REGION SPLIT IS MOOT, IN ONE NUMBER ===
Measured, not assumed. Giving `gatehouse` and `porters-yard` away shrinks gate's owned
region from 33 walk meshes to 13, and:
    charPxFar   24 px  ->  24 px       zFar  85.1 m  ->  85.1 m
The split's whole mechanism was that a smaller region lets the SOLVER choose a shorter
standoff. `gate` no longer has a solved standoff — its pos/aim are authored — and at 75 m
the far corner is set by the camera's distance, not by which twenty of thirty-three meshes
it owns. The split buys ZERO pixels. DROPPED.

=== GATES ===
  cine_test 647/0 (+3 soft)   seam_test 294/0 (+8 soft)   seam_walk 9/9
  plate_flat 0 of 16          routes --check clean at 16 shots   slice 670/16 baseline
  walk_bodygate 11 075 blocked steps in the gate district, unchanged by this pass
  gate visibleFrac 23.4% — unmoved: the lifted cards clear rays to the ARRIVAL, which is
  not in the 64-probe region set, so the region number was never going to move and did not.
  REBAKE SET DERIVED from the lifted cards' own bbox through every solved frustum: gate,
  shelf-east. RECORD SHOT: docs/qa/districts/gate_vista_after_reseat.png

## STYLE PROBE ROUND 2 — photoreal foliage, and the mill at the re-ruled 2x
## (taste input only, NOT canon)
2026-07-31. Renders: `docs/qa/emberbrook/styleprobe/probe2-a.png` (same 3/4 plate as round 1,
pulled back for the doubled mill), `probe2-b.png` (wheel + pit detail), `probe2-c.png`
(foliage-only frame: the vegetation bar with nothing else to carry it).
  WHAT THIS IS NOT — same standing as round 1. HAND-AUTHORED geometry in a THROWAWAY blend
  (scratch `mill_probe_r2.py`, a copy of round 1's script; not committed to tools/).
  Searched-not-authored and determinism DO NOT apply: nothing measured, nothing snaps to the
  map, no pipeline file, no camera file, no map JSON, master blend never opened.
  WHAT CHANGED, AND WHY. The user's round-1 verdict was: overall "pretty good and promising",
  KEEP roofs/timber/water/boundary, but (1) foliage "definitely does not meet the level of
  realism", wanted ~photorealistic, and (2) the mill is too small — re-ruled at 2x and stamped
  in `public/townmap/emberbrook.map.json`. So exactly two things moved.
  (1) VEGETATION IS NOW PHOTOSCANNED, NOT AUTHORED. Every green thing in these frames is a
  PolyHaven CC0 photoscan instanced into the scene — real branching, scanned bark, alpha-card
  leaf canopies, per-plant asymmetry. The stylised-clump vocabulary is gone. Trees:
  tree_small_02, island_tree_01/02/03, fir_tree_01, pine_tree_01, jacaranda_tree. Bramble and
  bank: searsia_lucida, searsia_burchellii, shrub_01/03, nettle_plant, fern_02, weed_plant_02.
  Groundcover: grass_medium_01/02, grass_bermuda_01, dandelion_01 — 320 000 hair-instanced
  clumps driven by a fractal density vertex group with bare trodden ground at the mill door
  and along the lane, i.e. density VARIATION, which round 1 was rightly pulled up on. Ground
  material is the scanned `leafy_grass` + `brown_mud_leaves_01` texture pair, mud mixed in by
  height toward the water. Canopies are hue/value-graded toward the Emberwake autumn and given
  subsurface so the low sun comes THROUGH the leaves (the one foliage idea kept from round 1).
  MEASURED, because it decided the composition: the scans are SMALL — tree_small_02 4.56 m,
  island_tree_01 5.03 m, island_tree_02 3.41 m, jacaranda_tree 10.36 m BUT LEAFLESS. Against a
  ~12 m mill they read as saplings at native scale, so the broadleaves are instanced at
  2.4–2.9x and the full-size conifers carry the Whisperwood treeline. The leafless jacaranda is
  used deliberately, once, as a bare autumn accent at the water's edge.
  **CORRECTION (2026-07-31, dressing-library lane, measured with tools/dressing_measure.py):
  "jacaranda_tree 10.36 m BUT LEAFLESS" IS WRONG AND THE ERROR MATTERS.** 10.35 m is
  `jacaranda_tree_trunk`, a BARE-TRUNK SIBLING OBJECT inside the same blend; the asset called
  `jacaranda_tree` is a FULLY LEAFED 19.47 m spreading broadleaf, canopy 24.42 m, 3.86 M tris.
  A merged bbox over one of these files measures the file's LAYOUT — variant sets, LOD bakes
  and generator source parts laid out apart — so it must be measured per variant. The whole
  round was composed around "we have no full-size broadleaf" while one sat unused in the set.
  See docs/qa/emberbrook/dressing/sheet-1-trees.png (top left) and measured.json.
  (2) THE MILL AT 2x. Overshot wheel 4.4 m dia (28 buckets, 1.45 m across the shrouds), dam
  crest 1.78 impounding the pond, tail water -3.05 — a 4.6 m fall, because a 4.4 m wheel plus
  its launder needs more head than the ~4.0 m the ruling names; the ruling's number is the
  DAM, the extra 0.6 m is the leat running in above the crest. Building mass scaled with the
  wheel: 8.6 x 9.4 m footprint, 5.0 m timber-framed upper storey with a mid rail (a five-metre
  wall needs a floor line) on a stone plinth that runs down 5.6 m into the wheel pit, ridge at
  ~12 m, lucam and hoist scaled to match. Cottage, lane and boundary left at village scale so
  the mill's new dominance is visible as dominance.
  ROUND 1 ROUGH EDGE FIXED: the buckets no longer read cog-like. The shrouds are solid rings
  now (28 discrete rim boxes turned to mush at 2x) so the wheel reads as a 4.4 m disc first and
  machinery second, with the bucket boards held inside the shroud line.
  RENDERER: CYCLES, 120 samples + OpenImageDenoise, Metal GPU — round 1 was EEVEE, and
  photoreal foliage needs real light transport. Same golden legibility key as round 1 (sun 3.0
  warm, warm bounce, practical window/lamp glows, AgX Medium High Contrast) but exposure 0.10
  and world 0.30, because Cycles plus a Nishita sky is far hotter than round 1's EEVEE fallback
  (round 1's sky node silently failed on 5.1's dropped `dust_density` — fixed here). The
  shipped emberwake numbers are untouched by this, as before.
  ASSET LICENSING: every downloaded asset is PolyHaven CC0 — no attribution required, listed
  above for the record. NO Sketchfab (CC-BY) asset was used, so nothing here carries an
  attribution obligation into the build.
  KNOWN ROUGH EDGES: leaf cards are large in close-up because the scans are scaled up; the
  pond is a flat plane with no shoreline wetting; the dam's stone reads pale under this key;
  no props beyond sacks/barrels/millstone, no NPCs, no bake, no depth pass.

## DRESSING ASSET LIBRARY — INTAKE, phase 0 lane A, CHECKPOINT 1: the contact sheet, and
## four things the tape found that the file names had said otherwise
## (2026-07-31, dressing-library lane, round 1)

BRIEFED: intake the round-2 probe's proven PolyHaven set as a production library, measure it,
solve the hero-tree problem, and send the coordinator a contact sheet BEFORE normalizing
anything. Nothing is normalized yet — this entry is the measurement pass and the sheet.
  SHEETS: `docs/qa/emberbrook/dressing/sheet-0-lineup.png` (true-scale lineup, both layers),
  `sheet-1-trees.png`, `sheet-2-shrubs.png`, `sheet-3-groundcover.png`. Raw numbers:
  `docs/qa/emberbrook/dressing/measured.json`.
  INSTRUMENTS (new, in tools/): `dressing_measure.py` (per-variant geometry), `dressing_spec.py`
  (which object in a blend is the plant), `dressing_tiles.py` (ortho true-scale tiles),
  `dressing_sheet.py` (compositor), `dressing_gnprobe.py` + `dressing_slimprobe.py` (the
  generator probes below). Every tile is an ORTHOGRAPHIC render with its ortho_scale written
  to a sidecar, so the 1 m rules drawn over it are placed by arithmetic and a height can be
  read off the sheet rather than trusted.

=== THE MEASUREMENT PASS CORRECTS THIS LOG IN FOUR PLACES ===
A merged bounding box over one of these blends measures the FILE'S LAYOUT, not the plant:
PolyHaven ships variant sets (`<id>_a.._e`), each baked at LOD0..LOD3, laid out apart in
world space, plus generator source parts (twigs, branch cards, leaf cards) and often a
geometry-nodes GENERATOR. Measured per variant instead, in the variant's own extents:
  1  `jacaranda_tree` IS NOT LEAFLESS AND IS NOT 10.36 m. The round-2 entry records "jacaranda
     10.36 m BUT LEAFLESS" and used it once as a bare accent. 10.35 m is `jacaranda_tree_trunk`,
     a BARE-TRUNK SIBLING OBJECT in the same file. The asset itself is `jacaranda_tree`, a
     FULLY LEAFED 19.47 m spreading broadleaf, 3.86 M tris — the only full-size broadleaf in
     the whole set, and it was never put in a frame. See sheet-1, top left.
  2  `fir_sapling_medium` is 8.83 m. A "sapling" taller than a three-storey house; this is the
     saplings-vs-mill lesson arriving a second time, and it is why nothing here is categorised
     by its name.
  3  `shrub_01` 0.40 m, `shrub_03` 0.40 m, `nettle_plant` 0.19 m, `fern_02` 0.43 m — these are
     UNDERSTORY, not shrubs. The only true shrubs in the set are `searsia_burchellii` 3.24 m
     and `searsia_lucida` 2.34 m.
  4  `weed_plant_02` is 0.07 m and `dandelion_01` 0.16 m: groundcover detail, not plants a
     camera will resolve except underfoot.
  THE FULL MEASURED SET, tallest variant / canopy / LOD0 tris of that variant:
    pine_tree_01 20.38 m / 8.31 / 6.95 M    jacaranda_tree 19.47 / 24.42 / 3.86 M
    fir_tree_01 18.93 / 6.53 / 4.18 M       fir_sapling_medium 8.83 / 5.28 / 0.69 M
    island_tree_01 5.03 / 4.82 / 1.60 M     tree_small_02 4.56 / 4.29 / 2.06 M
    island_tree_02 3.41 / 4.21 / 1.07 M     island_tree_03 2.62 / 2.97 / 2.09 M
    searsia_burchellii 3.24 / 5.05          searsia_lucida 2.34 / 1.97
    fern_02 0.43   grass_medium_02 0.40   shrub_03 0.40   shrub_01 0.40
    grass_medium_01 0.32   nettle_plant 0.19   dandelion_01 0.16   grass_bermuda_01 0.15
    weed_plant_02 0.07

=== THE PROBE WAS RENDERING EVERY BROADLEAF THREE TIMES, AND NOBODY COULD HAVE SEEN IT ===
`mill_probe_r2.py` instances the blend's FIRST collection, which is the top-level `<id>`
collection. That collection holds the generator AND the baked `LOD0` AND the baked `LOD1` as
siblings — the layer-collection excludes that hide them in the source file are a view-layer
property and do not travel with a collection instance. So each hero tree was 2.07 M (generator)
+ 2.06 M (LOD0) + 0.50 M (LOD1) tris of coincident geometry, three trees deep in the same
space, plus the generator's own leaf-card source meshes lying at the origin. Measured on
`tree_small_02`: generator H 4.52 m / 2 066 289 tris, LOD0 H 4.56 m / 2 062 487 tris — the same
plant twice. Nothing in the frame looks wrong, which is exactly why it survived a round.
  CONSEQUENCE FOR THE LIBRARY, and it is the main normalization lever: one representation per
  asset, chosen and named, never a whole source collection.

=== THE HERO-TREE PROBLEM, MEASURED IN MILLIMETRES, AND A FIX THAT IS NOT A COMPROMISE ===
Round 2's known defect was stated as "leaf cards read large in close-up because the scans are
scaled up". `tools/dressing_slimprobe.py` puts a number on it. Leaf geometry is found by
material index — instanced cards arrive with an index past the host object's own slots — and
measured triangle by triangle: median longest EDGE (the card's size) and median ASPECT
(longest/shortest edge, the only one of the two that can see a stretch, since a card squashed
in x and pulled in z keeps its area). On `island_tree_01`:
    what                                  H       W      H/W    leaf edge    leaf aspect
    native                              5.03    4.82    1.04    10.07 mm       2.015
    round-2 hero: OBJECT scale 2.6x    13.07   12.53    1.04    26.17 mm       2.015
    round-2 slim: OBJECT 0.62/.62/1.18  5.93    2.99    1.99     8.44 mm       2.201
    SKELETON CURVE scale 0.6/0.6/3.0   11.69    3.53    3.31     9.87 mm       2.087
  So the hero defect is +160% on leaf card size, exactly the object scale, as it must be.
  THE FIX: these assets are geometry-nodes GENERATORS that build the woody skeleton from a
  curve and INSTANCE the leaves afterwards. Scaling the CURVE'S CONTROL POINTS grows the tree
  and leaves the instances at native size. Measured on `island_tree_01` (`dressing_gnprobe.py`,
  mean triangle area per material): skeleton 1.0 -> 2.5 takes the tree 5.03 -> 10.40 m with the
  woody material's mean triangle scaling as k^2 (10.12 -> 63.26 m2 total) while the leaf
  material's mean triangle edge holds at 8.1 -> 7.9 mm.
  AND IT ANSWERS THE canopy_slim GAP TOO (lane B's priority): scaling the skeleton NON-uniformly
  0.6/0.6/3.0 gives a genuinely columnar 11.69 m tree, slenderness 3.31, with leaf cards
  unchanged in size (-2%) and near-unchanged in aspect (+3.6%) — against the probes' own
  0.62/0.62/1.18 object stretch, which reaches slenderness 1.99 on a 5.93 m tree and stretches
  every card while doing it.
  NOT YET CLAIMED, AND THIS IS THE LIMIT OF THE NUMBERS: none of this has been RENDERED beside
  probe2-c. A leaf-card measurement is not a look, the bark texel density goes with the
  skeleton scale, and one generator misbehaves — `tree_small_02`'s woody material is a fixed
  scanned trunk mesh joined in (28 293 tris at every k), so at k=3 a 12.4 m canopy stands on a
  3.69 m trunk. `island_tree_01` generates its trunk from the curve and does not have this
  fault. The comparison renders are checkpoint 2 and the choice is the coordinator's.

=== WHAT IS NOT DECIDED HERE ===
Nothing is in the library: no asset is normalized, no manifest exists, no binary is committed.
Source on disk is 2.25 GB across 19 assets (pine_tree_01 alone 777 MB, fir_tree_01 426 MB,
jacaranda 300 MB), against a repo whose .git is already 5.4 GB, so the normalization budget is
a decision to take with the coordinator and not a detail — the generator-not-bakes finding
above is what makes a lean library possible at all.

## DRESSING LIBRARY — CHECKPOINT 2: the hero tree, the poplar silhouette, and the pine's
## keep-or-drop, all decided by rendering under probe2-c's own key
## (2026-07-31, dressing-library lane, round 2)

SHEETS: `docs/qa/emberbrook/dressing/sheet-4-hero-tree.jpg`, `sheet-5-canopy-slim.jpg`,
`sheet-6-treeline.jpg`. Raw: `hero-candidates.json`, `treeline.json`. Instruments in tools/:
`dressing_rig.py` (probe2-c's light and lens in one place), `dressing_herocompare.py`,
`dressing_sapling.py`, `dressing_treeline.py`, `dressing_densitysweep.py`,
`dressing_slimprobe.py`, plus the two sheet compositors.
  EVERY CANDIDATE IS LIT BY THE SAME RIG, copied from `mill_probe_r2.py` rather than
  re-invented — EMB_sun 3.0 W (1.0,0.70,0.42) at elev 62 / rot 212, warm bounce, sky at 0.30,
  32 transparent bounces, AgX Medium High Contrast, exposure 0.10, 60 deg — and carries the
  probe's own autumn regrade. probe2-c is pasted at the head of each sheet. A candidate that
  only looks good under a different key has not been compared to anything.
  TWO FRAMES EACH, because the defect only exists in one of them: WIDE (silhouette, 1.80 m
  figure) and CLOSE (7 m from the trunk, where "leaf cards read large" was seen).

=== THE LEAF-CARD TABLE, ONE INSTRUMENT, ALL MEASURED ===
`dressing_slimprobe.py`: median longest triangle edge of the REALISED leaf geometry (the
card's size as the camera sees it) and median triangle aspect (the only one of the two that
can see a stretch — a card squashed in x and pulled in z keeps its area). island_tree_01:
    what                                H       W     H/W    leaf edge   aspect
    native                             5.03   4.82   1.04    10.07 mm    2.015
    A  round-2 hero  OBJ 2.6x         13.07  12.53   1.04    26.17 mm    2.015   (+160%)
    F  round-2 slim  OBJ 1.37/1.37/2.6 13.07   6.60   1.98    18.61 mm    2.199   (+85%)
    B  SKELETON crv 2.5               10.40   9.21   1.13     9.95 mm    2.086   (-1%)
    C  SKELETON crv 3.0               12.19  10.65   1.14     9.88 mm    2.060   (-2%)
    G  SKELETON crv 0.6/0.6/3.0       11.69   3.53   3.31     9.87 mm    2.087   (-2%)
    H  SKELETON crv 0.5/0.5/3.4       13.11   2.96   4.42     9.84 mm    2.087   (-2%)
  The defect and the fix are both in that column. Scaling the OBJECT multiplies the card by
  the scale factor, exactly; scaling the SKELETON CURVE leaves it alone, because the leaves
  are INSTANCED after the skeleton is built.

=== A REFILL THAT WAS A 33x CUT, AND THE READING THAT CAUGHT IT ===
Grown skeletons render THIN: crown volume goes as k^3 while the generator keeps seeding at
its authored density. Measured (`dressing_densitysweep.py`, leaf triangles per m3 of crown):
k=1 native 13 585/m3; k=3 native 9 262/m3 — 68% of native, i.e. a third thinner.
  THE FIRST REFILL MADE IT WORSE AND THE NUMBERS SAID SO BEFORE THE RENDER DID: island_tree_01
  ships `density_multiplier` = 106.3 against a socket DEFAULT of 0.5, so setting it to "3.2"
  reads like a 6x increase and is a 33x CUT. Tri count fell 6.50 M -> 0.66 M, which is what
  exposed it. GENERAL RULE FOR THIS LIBRARY: these inputs are NOT normalised, the shipped
  value is not the default, and any override must print the before value.
  Corrected to 170 (k=3) and 190 (columnar), which is where the sweep puts native per-volume
  density back: K 12.65 M tris, L 2.66 M tris.

=== WHAT THE FRAMES SAY (the judgement is the coordinator's; this is what is on them) ===
HERO: A (the control) is the defect — big soft cards, stretched bark. C/K fix the cards and
show the approach's real cost: bark texel stretches with the skeleton, so a 12 m trunk carries
3x-magnified bark. D/E — `jacaranda_tree`, the asset the round-2 note wrote off as leafless —
is the strongest frame on the sheet at both distances: real limb structure, fine compound
foliage at correct scale, scanned bark at native texel density, 2.23 M tris. Its silhouette
is subtropical, and THAT is the taste question, not its quality. I (Sapling oak, 13.29 m) is
the value candidate: 0.43 M tris, no attribution, leaf size SET at 0.14 m rather than
inherited — a clean generic broadleaf, less characterful than the jacaranda.
canopy_slim: F (what both probes did) is 18.61 mm cards at slenderness 1.98 — not even
columnar. G/H/L are genuinely columnar (3.31 / 4.42 / 3.31) at native card size; L is the
best of them. J (Sapling column, 14.70 m, slenderness 2.94) reads as a Lombardy poplar at
83 804 tris — 32x lighter than L for a silhouette that is arguably closer to the brief.

=== THE PINE VERDICT, AND ONE ARM WITHHELD ===
Same band in every frame: 34 stations, one seed, same rotations and scale jitter; only the
species at each station changes. Instanced at LOD1 — what a band at 26-72 m would ever use.
    T1  pine_tree_01_a_LOD1 x20 + fir_tree_01_a_LOD1 x14
    T2  fir_tree_01_a_LOD1 x16 + fir_tree_01_b_LOD1 x18
  READING: at LOD1 and this distance pine_tree_01 reads SPARSE and PALE with a high thin
  crown; the fir band alone reads fuller and more like a wood, and carries two silhouettes
  rather than one. On that evidence pine is not load-bearing, and dropping it removes the
  intake's largest disk line (777 MB) and its largest mesh (LOD0 17.2 M tris, 68% of the
  library). RECOMMENDED, not taken: the call is the coordinator's and the frames are there.
  THE THIRD ARM IS WITHHELD RATHER THAN SHOWN. T3 (fir + a Sapling conifer) rendered with
  INVISIBLE TRUNKS: the preset parse silently produced an empty parameter dict and the curve
  was left unbevelled, so every "tree" was a zero-width curve carrying a thin cloud of leaves.
  It is not on the sheet, because a frame that shows something other than what it claims is
  worse than no frame. The arm also needs a CC0 NEEDLE atlas that is not held locally
  (PolyHaven's fir and pine ship no leaf maps at all; ambientCG `PineNeedles001` is the
  identified source and that download has not been taken).

=== SOURCES, VERIFIED RATHER THAN REMEMBERED ===
Sapling Tree Gen is NOT bundled in Blender 5.1 — it is an extension, `sapling_tree_gen`
v0.3.7, GPL-3.0-or-later, sha256 27a478262e1c86612a9c3daffe7f4dce2802f5bc2294033462e5adc6d9c0080f
(verified on download). GPL binds the add-on CODE, not the geometry, so generated trees carry
NO attribution obligation. Beware `hasattr(bpy.ops.curve, 'tree_add')` — it returns True on a
stock 5.1.1 where the operator does not exist, a lazy-attribute artifact; `.poll()` is the test.
Bark for the procedural arm: PolyHaven `jolcham_oak_bark_01`, CC0. Leaves: the single-leaf
alpha atlas PolyHaven ships with `island_tree_01` (8 leaves in a grid), CC0 — so one atlas
cell is one leaf and card size is a parameter.
NO CC0 full-size broadleaf exists on Sketchfab (354 downloadable models swept across 16 terms;
every viable tree is CC-BY). Best CC-BY if the taste call goes that way: PlantCatalog's
Lombardy/Black poplars and AirSickLowLander's photogrammetry elm/ash/river birch — download
needs a free account token. TRAPS RECORDED: the `xfrog` account is mostly CC-BY-NC-ND and is
FORBIDDEN; BlenderKit's free tier is a vendor EULA, not CC0/CC-BY, and is out of scope.
There is NO birch bark in any CC0 source, which is why canopy_slim is specified as the POPLAR
SILHOUETTE and not the birch species.

=== STILL NOT IN THE LIBRARY ===
No asset is normalized, no manifest exists, no library binary is committed. Next is the
measured disk budget against lane B's contract (public/assets/dressing/manifest.json,
version 1) before the first binary commit, per the coordinator's ruling.

## DRESSING LIBRARY — NORMALIZATION: 1 469 MB of scans become 71 MB, and three builds that
## "succeeded" while shipping broken assets (2026-07-31, dressing-library lane, round 3)

DELIVERED: `public/assets/dressing/manifest.json` (lane B's contract, version 1, 19 assets +
4 derived declared pending) and `fetch.json` (sha256 pins for every source file, 1 469.3 MB,
so the gitignored cache can be re-pulled byte-identical). Tools: `dressing_normalize.py`,
`dressing_verify.py` (THE INTAKE GATE), `dressing_manifest.py`, `dressing_texelprobe.py`.
Binaries NOT committed pending the coordinator's nod on the budget.
  THE BUDGET, BUILT RATHER THAN ESTIMATED: 66.9 MB of blends + 4.4 MB of ground textures =
  71.3 MB, from 1 469 MB of source. Per-class policy: generator assets ship the GENERATOR and
  none of the bakes; trees/shrubs 1k maps; understory and groundcover 512 maps and LOD1 only.
  Largest lines searsia_burchellii 14.7, jacaranda_tree 12.6, searsia_lucida 7.5.
  pine_tree_01 IS DROPPED (ruled on sheet-6-treeline.jpg) and is recorded in
  `manifest.dropped` with that pointer — 777 MB of source and a 17.2 M-tri LOD0 leave.

=== THE GATE IS THE FINDING. THREE BUILDS PASSED "IT OPENS" AND WERE ALL BROKEN ===
None of these threw an error; each would have shipped.
  1  GENERATORS WITH EMPTY LEAF COLLECTIONS. Gathering a generator's source objects into one
     tidy collection EMPTIES the collections its node tree instances from. island_tree_01
     built to 21 777 tris instead of 1.6 M — a tree with almost no leaves — and opened fine.
     The fix is to stop hand-tracking dependencies: link only the top-level object and let
     `bpy.data.libraries.write(path, {collection})` pull the graph. Note the related trap:
     these generators reference their leaf sources from INSIDE the node tree, not through a
     modifier input, so walking modifier inputs alone finds nothing.
  2  EVERY TEXTURE PACKED AS PNG DESPITE `image.file_format = 'JPEG'`. `image.scale()` marks
     the image DIRTY, which routes the save through `save_render()`, and save_render writes
     with the SCENE's `render.image_settings`, not the image's. 47.8 MB of the first budget
     was this one line — a 1k normal map at 2.9 MB instead of 0.3 MB.
  3  THE COLLECTION SILENTLY RENAMED. `bpy.data.collections.new('island_tree_01')` returns
     `island_tree_01.001` when the source file already owns the name, so the library shipped
     a collection the manifest does not name and a consumer's first-collection fallback would
     load a bag of leaf cards.
  THE GATE NOW ASSERTS, by appending exactly as a builder will: the collection has the
  manifest's exact name; appended-and-evaluated height matches the source measurement within
  2%; z-min is at ground within 1 mm; every image is packed and resolves; no stray LOD
  objects; and it renders each asset. 19/19 pass.

=== THE BARK STRETCH IS REAL, IS EXACTLY 1/k, AND CANNOT BE COUNTERED BY MAPPING ===
`dressing_texelprobe.py`, texel density per material as
sqrt(sum(uv_area) * texW * texH / sum(area_m2)). island_tree_01, k=1 -> k=3:
    instanced leaves / twigs    7026 -> 7275 px/m    ratio 1.035   (no stretch)
    trunk material               520 ->  173 px/m    ratio 0.333   (stretched by exactly k)
  THE TRUNK'S UV AREA IS UNCHANGED AT BOTH SCALES — 0.652 — which is the whole explanation
  and the reason the obvious fix does not work: the trunk carries a UNIQUE UNWRAP occupying a
  fixed island of a scan atlas, so multiplying its UVs by k does not restore density, it
  walks the trunk off its own island. The only clean fix is a TILEABLE bark under triplanar
  projection (jolcham_oak_bark_01, CC0, already held), which sets density at any scale and
  trades the scan's own trunk for a generic one. 3x ACCEPTED per coordinator ruling and
  recorded in the manifest entry for `hero_broad_12m` so it is not re-derived.
  THE PART THAT MATTERS HELD: leaves and twigs are the INSTANCED geometry and keep their
  texel density to within 3.5% — the defect this whole phase existed to fix stays fixed.

=== THE MANIFEST CARRIES ITS OWN TRAPS FORWARD ===
`overrides` is recorded as {before, after} per generator input, because these inputs ship far
from their socket defaults — island_tree_01's `density_multiplier` is 106.3 against a default
of 0.5 — and a bare after-value would hand the next reader a 33x cut dressed as a refill.
`up` is "+Z" and nothing is rotated at intake; glTF export is what converts to +Y.

## DRESSING LIBRARY — THE DERIVED FOUR, and the phase closes (2026-07-31, round 4)
All four derived assets built through the SAME normalize-and-gate path as the scans, 4/4 on
`tools/dressing_verify.py`, manifest status now `shipped` for every one. Commits 670b331
(the 19 scans, 71.3 MB), 4210135 (the two critical-path heroes), this one (the remaining two).
    hero_broad_12m     12.19 m  crown 10.69   12 646 379 tris   3.49 MB   PRIMARY hero
    mid_broad_13m      13.16 m  crown 13.32      428 702 tris   7.93 MB   mid-ground filler
    slim_poplar_14m    14.62 m  crown  5.00       83 804 tris   2.12 MB   PRIMARY canopy_slim
    slim_skeleton_12m  11.69 m  crown  3.53    2 655 581 tris   3.49 MB   near-camera slim
  THE COST SPREAD IS THE POINT: 83 804 tris to 12.6 M is a factor of 151 across four trees
  that all read at village scale, so the placement decision is a budget decision. All four
  are `plates-only`.
  RECORDED WITH EACH SKELETON-DERIVED ASSET, per the overrides convention:
  hero_broad_12m density_multiplier 106.3 -> 170.0, branch_density 1.46 -> 2.4;
  slim_skeleton_12m 106.3 -> 190.0 and 1.46 -> 2.2.
  ONE HONEST DIFFERENCE FROM THE CHECKPOINT-2 SHEET: `slim_poplar_14m` reads sparser than
  frame J did. It is a correctness change, not a regression — on the sheet each leaf card
  sampled the WHOLE 8-leaf atlas, so one card drew a cluster; the shipped asset maps ONE
  atlas cell per card, which is what makes its 0.10 m leaf size an honest number. If it reads
  thin in a real framing the lever is the `leaves` count (22), not the leaf scale.
  THE SAPLING CURVE KEEPS ITS BEVEL AND THE BUILDER ASSERTS IT. An unbevelled curve renders
  as a zero-width line — that is exactly what made the T3 treeline arm invisible and got it
  withheld from checkpoint 2, so the failure is now a build-time assertion rather than a
  thing to notice in a frame.

## THE PRODUCTION OVERWORLD REBUILD — three arrival reds that were one number, a
## falls lip eleven units below the springs, and a town standing in its own river
## (2026-08-01, overworld lane, task #33)

THE THREE PRE-EXISTING `ow-valley` ARRIVAL FAILURES WERE ONE OFF-BY-TWO IN A COORDINATE
FRAME, and both halves of it had been printing themselves for as long as they existed.
`valley_map.py` hardcoded the terrain tile at 280x200, origin (140,100). `scenegraph_
derive.mjs` derived its own from the massifs' extent: 280x196, origin (140,98). The tile
that ships is valley_map's, so every ow-valley coordinate in `scenegraph.json` sat 2u
north of the road ribbon it had been measured on. Measured on the shipped files, before
any change:
    del-cine>ow-valley spawn [36.008, -60.403]
      read in the 98-frame  -> world (176.01, 158.40)   0.00u from the road centreline
      read in the built tile -> world (176.01, 160.40)   1.86u from it, ribbon half-width 1.0
    => 0.86u off the walk mesh => "arrival stands on walk network" fails
Doors 4/14/20 are ONE edge asserted three times by the itinerary. Emberbrook's portal
survived the same 2u only because it lands inside an r3.4 village green. And the
generator had already said so, in two of its own warnings that nobody read:
`"portal 'dellhollow-valley-gate': trigger height taken from a walk surface 2.72u away
(the road ribbon stops short of the portal point)"` and `"portal 'dellhollow-valley-gate':
region spawn (36.0,-60.4) is off the walk network"`. A WARNING NOBODY READS IS NOT AN
INSTRUMENT. The tile is now STATED once — `world.json regions[].tile {size, origin}` —
read by valley_map, scenegraph_derive and valley_verify, asserted by worldmap_validate
(stated, origin at the centre, envelope inside it), and inferring it is refused rather
than fallen back on.

THE SEATS ARE DERIVED FROM THE TOWN MAPS NOW, AND THE SCALE IS WRITTEN DOWN. There was
no recorded town->region transform; every "town-adjacent" world coordinate had been
authored. Derived and stamped at checkpoint 1:
    world = anchor.pos + scale * R(rotationDeg) * M * (townPos - townOrigin)
    origin = centroid of the town map's SETTLED landmarks; scale = impressionRadius /
    the p90 radius of that set, so the impression disc IS the settled town.
    EMBERBROOK  35 landmarks, p90 43.31 m -> 14u/43.31 = 0.3232 u/m (1u = 3.09 m).
                CHECKED INDEPENDENTLY against the arrival leg (78.3 m of town road vs
                the ratified 24.08u) = 0.3074 — within 5% of a number derived from
                something else entirely, which is the only reason to believe either.
    DELLHOLLOW  0.4348 u/m AND MIRRORED. Its map frame is LEFT-HANDED against the world:
                +x is downstream (NE, = rotationDeg 33) and +y runs cliff->river, which
                on the LEFT bank looking downstream is world ESE = downstream MINUS 90.
                A plain rotation reflects the town. Recorded as `mirrorY`, because it is
                invisible in the numbers and fatal in the build.
THE SECLUSION COST THE REGION 1.87u, NOT 40. The town's Old Gate went 30 m -> 87.1 m from
the square (stamp 306554a); at the impression scale that is 26.61u against a ratified
seat already 24.08u out. The overworld had always drawn the gate further out,
proportionally, than the town did; the seclusion stamp brought the town into line with
what the region already implied. old-gate [88,72] -> [88.42,73.83]; ember-falls [96,82]
-> [95.40,80.00]; whisperwood-entrance [84,24] -> [80.01,22.75]; emberbrook-gate off the
anchor and onto the town's own arch, [82,48] -> [82.60,34.39], 13.6u out on the
impression's RIM instead of among its houses.

THE PINCH-RATIO RULE, RATIFIED AS DOCTRINE: **A PINCH IS SEATED BY RATIO, NOT METRES.**
The world's river is not the town's river shrunk — at the Old Gate the town's 6.95 m
grate scales to 2.25u against a ratified parent width of 4.60u, a factor of TWO — so
carrying the town's metres across puts the gate doorway's east jamb in the water, which
is the failure the previous re-seat shipped and only a rendered frame caught. Carry the
RATIOS: the doorway centre at 2.727 channel half-widths off the centreline, the founded
wall keeping 1.022 half-widths of dry ground. Measured on the built field afterwards:
    doorway centre        6.26u off the centreline = 2.778 half-widths  (town 2.727)
    founded dry ground    2.39u                    = 1.059 half-widths  (town 1.022)
    ground under the gate 26.20 against a map seat of 26.5, water 2.40u below it
EVIDENCE THE FRAME IS RIGHT AND NOT FITTED: the town's own `downstream-vista` falls out
of the same transform at 4.08u east of the channel against a 2.30u half-width — on the
FAR bank, looking back through the gap, which is exactly what its map note claims. It
was not used to fit anything.

FOUR THINGS THE REBUILD FOUND THAT WERE PRINTING THEMSELVES EVERY RUN.
 1  THE FALLS LIP WAS ELEVEN UNITS BELOW THE SPRINGS. `T_LIP = np.interp(11.0, RIV_S, ...)`
    — eleven units of ARC LENGTH FROM THE RIVER'S START — was true exactly while the
    river's source WAS the falls. The restamp moved the source 50u upstream of the gate
    and the constant went on pointing into the headwaters, so the Whisperwood plateau was
    being cut off in the middle of its own springs while the gorge head kept plateau
    weight. It printed `falls lip t=0.043 (arc 11u)` on every single run. Derived now from
    the SILL — where the channel crosses the gatewall's OUTER face — and cross-checked
    against the ember-falls landmark, raising if the lip is not upstream of it. t 0.044 ->
    0.227, arc 11u -> 58u. On the built water surface the plunge lands at arc 57-59:
    -0.24 u/u, -1.82, -4.09, -0.27. The lip is where the lip is.
 2  DELLHOLLOW WAS STANDING IN ITS OWN RIVER, and so was the Moorage. The anchor sat 4.99u
    from a 12u channel's centreline — 1.01u inside the water — and the field read 2.41
    against its map height of 12.0. The Moorage sat 1.92u from an 18u channel and read
    -4.30 against 0.0. THIS IS THE SAME CLASS AS THE OLD GATE IN THE RIVER, and it survived
    for the same reason: every instrument asked TOPOLOGY (which bank, which side) and none
    asked the metric question, IS THERE DRY GROUND UNDER IT.
    RE-SEATED GATE-ANCHORED (coordinator ruling on the user's delegation, taken while this
    lane was mid-build; it supersedes an earlier centroid-pinned seat this entry originally
    carried, and the number below is the one in the file). THE VALLEY GATE IS THE PIN —
    it is the only LOAD-BEARING dot Dellhollow has on the tile, being the portal, the
    region spawn and the road's end, while the Moorage and the locks are scenery. The
    SCALE is the one that seat implies: 8.94u of world per 33.61 m of town = 0.2661 u/m,
    taken over the Moorage-implied 0.5171 because gate-scale keeps this miniature
    COMPARABLE TO EMBERBROOK's derived 0.3232 (ratio 0.82), so relative town sizes read
    honestly on the world map. impressionRadius follows the scale, 18 -> 11.0: a compact
    town, and if it should read more substantial the approved lever is MORE DRAWN ROOFTOPS
    down the gorge, never a bigger radius — the radius is a derived quantity now and
    inflating it would re-lie about the town's size.
    AND THE PINCH-RATIO RULE TURNED OUT TO CROSS THE GORGE TOO. Carrying the town's
    cross-gorge METRES at that scale put the Moorage, Lock Five, the dam crest and the
    north landing UNDER WATER (Moorage bank +3.93 against a half-width of 8.14, field
    -2.21) — the world channel is far wider than dellhollow.map.json's frame allows for,
    exactly as at the notch. Carried as a RATIO of the channel's own half-width instead,
    every dot lands dry except the dam crest, which lands ON the water's edge, which is
    what a dam crest is. anchor [184.13,157.40] reads 11.95 against a map 12.0.
 3  THREE TERRAIN BUGS SURFACED UNDER THAT ONE. The north rim's FOOT was hardcoded at
    y=160 while its own massif blob starts at 168 — eight units of valley floor eaten by a
    ridge the map does not put there. The rim was a function of WY alone, so it ran clean
    across a tile whose blob stops at x=210, and the blob's own note says "the rim runs out
    at x~210, where the gorge's own walls take the river on to the Long Reach" — the prose
    was right and the geometry never read it. And `waterAccess` relaxed the bench profile
    and the shelf wall but NOT the rim or the gorge shoulder, so the region's ONE
    bench-side descent to water had 6.5u of gorge wall standing in it. A descent only some
    of the terrain agrees to is not a descent. Moorage -4.30 -> +2.09; the +2.09 residual
    is reported, not buried.
 4  HALF OF DELLHOLLOW WAS ON THE CLIFF THE PLAYER CANNOT REACH. `build_dellhollow` built
    two terraced strings facing each other across the notch, citing world.json for "the
    town straddles the river in its gorge" — a line that has not existed since the restamp
    made the town's mass WEST BANK ONLY. Restricting it to the resolved bench was NOT
    ENOUGH: measured BY VERTEX, 34% still landed on the far wall, because this cluster
    spans 24u of a reach that turns 36 degrees and its lateral offsets were taken in the
    ANCHOR's frame. Stations now step along the river's own curve
    (`VM.river_frame_at_arc`) with a per-station bank screen (`VM.bank_offset`). Houses
    7 -> 10 and every one of them west-bank; the 328 far-bank verts are the weir flight,
    which spans the channel BY CANON and is the reason the town exists.

AND `valley_verify` WAS ASSERTING THE DEFECT. Its zone check REQUIRED the Dellhollow
anchor to be 'water', with a comment explaining that the town straddles the river and an
authored stamp never dries the river out. A VERIFIER THAT ASSERTS A DEFECT IS WORSE THAN
NO VERIFIER, BECAUSE IT DEFENDS IT — the rebuild failed on it and the failure was correct
in form and wrong in direction. It also still carried `wx - 140.0, 100.0 - wy` as its own
private frame, which is the third copy of the number that caused the arrival reds.

THE AUDIT CAMERAS WERE THE LAST LESSON AND THE CHEAPEST ONE. "One render per major seat"
found that THREE of seven eyes could not see their subject, and none of the three had ever
complained. The 'gate' eye was INSIDE A TREE CROWN — 60% canopy at the lens, gate not in
frame; a proximity test against object ORIGINS is useless against a joined canopy mesh, so
it is a ray from eye to gate now, raised until the first hit is not foliage (settled +4.9u,
prints what it found). The 'moorage' eye was 5.60u UNDER ITS OWN GROUND and the 'shelf' eye
3.06u under, because both were derived from positions that had since moved; every audit eye
is now floored at 2.2u of headroom and says so when it had to move. And 'shelf' was AIMED at
`w2b(152.0, 54.0)`, a coordinate from an orientation the world has not had since the
restamp — at world x=152 the road runs at y~145, so the shot had been pointing 90u off its
own terrace and rendering a cliff and a meadow. It is aimed at the map's named pocket
terrace now. A CAMERA AIMED AT A TYPED NUMBER GOES STALE SILENTLY; ONE AIMED AT A NAMED MAP
FEATURE CANNOT.

GATES, against the pre-existing baseline in every case:
    transition_test --port=8177   doors 4/14/20 GREEN, all 24 arrivals green
                                  (baseline: 3x "arrival stands on walk network")
    transition_test --reload      32/0            (baseline 31/1, same defect)
    slice_test                    671/15, ZERO ow-valley (baseline 670/16, 1 ow-valley);
                                  the 15 are emb-cine and belong to the town lane
    seam_test 294/0 · seam_walk 9/9 · valley_verify OK · worldmap_validate 0 errors 0 warnings
    crosscheck 52 assertions 0 failed · benchSide dual resolution green (W = LEFT, road agrees)
    road/river clearance 0 pushed, min slack 2.76 -> 3.51u
THE REMAINING transition_test REDS ARE A LOOP WRAP COUNTED AS DRIFT, not a stall: the
playhead goes 91.75 -> 30.88 over 11.1s of wall clock, which is the dellhollow track
looping. It fires on different doors each run and it fires BECAUSE loading a 32 MB region
takes 9-15s. The assertion is loop-blind; that is an instrument bug, and naming it is
cheaper than chasing it.

WHAT IS MEASURED AND STILL OPEN, stated rather than left for a frame to find:
 -  THE OLD GATE IS A PORTAL MARKER, NOT THE RATIFIED STRUCTURE. Canon is ONE wall across
    the pinch — arched road doorway, low water grate, plain coursed masonry. The tile
    builds two posts. The SEAT is now right to 2% and the founded ground is right to 4%;
    the object standing on it is not built.
 -  THE NOTCH DOES NOT SEAL AT REGION SCALE. Cross-section on the pinch line: rock at -3u,
    then flat ground from +3u to +13u before the west rock at +14u. That is a 17u gap
    against a 4.5u channel — the town's own notch is 19.6 m rock-to-rock, 6.3u at scale.
    A walker can pass beside the gate. ow-valley is free-roam terrain, not WALKLOCK.
 -  THE SHELF IS NOT A LEDGE AGAINST A WALL. The region says "a NARROW LEDGE hard against a
    HIGH mountain wall on the player's LEFT". Measured every 0.05 of the road: the road
    crest is flat to 0.05-0.21u over the 4u straddling it, but at +8u the ground FALLS
    2-5u and the wall does not rise until +14 to +22u (+13 to +16u there). It is a road on
    a ridge crest with a trough behind it, not a ledge.
 -  Moorage field height +2.09 against a map 0.0, and the Long Reach floor control
    [226,186] reads 17.08 against a wanted 9.0 with its floor profile already pinned at the
    minimum — the far corner of the tile, no landmark, no road, no portal on it.
 -  DELLHOLLOW'S RATIFIED WORLD SEATS ARE NOT SELF-CONSISTENT UNDER ANY SINGLE SCALE: the
    Valley Gate implies 0.27 u/m and the Moorage 0.52, a factor of two. They were authored,
    not derived, so a derivation could not arbitrate them and the gate was held while the
    question went up. RULED mid-build (user delegated, coordinator decided): GATE-ANCHORED,
    compact town — item 2 above carries the numbers. The gate keeps its proven seat; every
    other dot moved to where the derivation put it. CLOSED, not standing.
 -  `emberbrook.routes.json` IS STALE ON CLEAN HEAD — reproduced with this lane's files
    stashed, so it is the seclusion stamp's own debt, not this rebuild's. Left untouched
    (not this lane's directory). `dellhollow.routes.json` re-derived: two decimals of aim.
 -  NO PERCEPTUAL SCORING ANYWHERE IN THIS LANE. GEMINI is depleted, so nav_eval and
    scene_redteam were not run and no judge number appears above. Every claim here is an
    instrument reading. The deferred perceptual questions are: whether the gorge reads as
    a corridor at walker's eye, whether the falls read as a plunge rather than a chute
    (the water DROPS 5.76u in 2u of arc, but no spray or free-fall geometry is built), and
    whether Dellhollow's impression reads as one bank now that it is one.

## THE DELLHOLLOW SWEEP FINISHES — four plates that had never been judged, one gate that had
## to be judged again, and a black void that is measurably not a void
## (2026-07-31, scene-redteam lane, sweep 2)
Report: `docs/qa/redteam/run-20260731-dellhollow2/index.html`
(`:3000/docs/qa/redteam/run-20260731-dellhollow2/index.html`). All 16 Dellhollow plates,
none of Emberbrook's — its blockout frames re-bake tonight behind the photoreal dressing
pass and sweeping them now would judge pictures that are about to die.
  WHAT WAS ACTUALLY JUDGED THIS ROUND: 5 plates, 28 judge calls, 43 836 prompt + 49 890
  reply tokens, 0 errors. `loop-stairs`, `lockhead`, `cottage`, `cottage-steps` — the four
  the first sweep never reached when the shared GEMINI_API_KEY ran out of credit — plus
  `gate`, which was re-judged rather than replayed because 96114cc recomposed the shot
  entirely (pos, aim, rtClip and depth near/far ALL differ; the old gate replies describe a
  picture that no longer exists and are not carried). The other 11 replay from
  run-20260731-dellhollow at zero API cost — the same replies, re-parsed and re-verified by
  today's code against the same pixels. Section 4 of the report opens with the per-plate
  table; the run dir records it per shot in `findings.json`.
  TWO PLATES ARE MARKED against-superseded-bake AND NOT RE-RUN, per the lane's own rule.
  `shelf-east` and `shelf-west` were re-rendered at 17:30:28Z and 17:04:24Z while their
  replies describe the 02:32:12Z and 14:25:13Z bakes. Their CAMERAS did not move — pos, aim,
  fov and depth near/far are byte-identical — only the render did, so the run pins those two
  shots to the bake the findings were made about instead of annotating a day-old critique
  onto tonight's picture. Nothing moved under the run: the pin was re-diffed against the
  shipped scene directory afterwards and only those two deliberately-held plates differ.
  THE VERDICT MOVED, AND IT IS THE TOWN THAT MOVED, NOT THE JUDGE. Hand-adjudicated 3
  outright + 1 weak = 4/5 (was 3/5); the pre-registered keyword matcher scores 2/5 exact and
  4/5 any-plate (was 3/5 and 5/5). THE ROWS ARE NOT COMPARABLE ONE TO ONE: three of the five
  complaints are anchored on `gate` and `gate` is a different photograph. `canopy-wall` went
  hit -> WEAK (nothing on the vista framing mentions foliage across the entrance); `stray-cliff`
  went miss -> HIT (last round every keyword match was a coincidence on the words "cliff" and
  "clip"; this round 3 of 3 looks say the cliff geometry itself ends in a seam and repeats,
  which is the test as it was written). `gate-stair`, `plank-screens`, `waterfront-jumble`
  carry unchanged on unchanged replies.
  THE GATE SHOT NO LONGER SHOWS THE GATE, AND AN INSTRUMENT SECONDS IT. Checklist mode
  returns ABSENT for seven items on `gate`: Valley Gate, the toll gatehouse, the Porters'
  Yard, all three roads off the gate, the way out toward shelf-west and the "Leave Dellhollow"
  portal. The ray census — deterministic, not the judge — independently puts every one of
  them ON SCREEN and OCCLUDED, behind something 3.25 to 8.46 m nearer, at charPx 25–29
  against the shot's own argued floor of 24. This is the cost 96114cc recorded in its own
  commit message (portal arrival 32.1% -> 0.0% chest, 18 of 18 rays blocked by
  `veg_gate_rimclump_26`), now restated from the pixels by a second, independent path.
  THE CLEANEST VISIBLE-BUT-ILLEGIBLE CASE THE TOOL HAS PRODUCED: on `cottage` the checklist
  returns ABSENT for the Keepers' Cottage DOOR while the census says that pad is CLEAR, at 78
  charPx, 1.19 m IN FRONT of the plate surface. Nothing is occluding it, it is large on
  screen, and the judge cannot find a door. That is precisely the layer no deterministic
  visibility instrument can reach, and it is Odessa and Maren's front door.
  A CONFABULATION, MEASURED, AND STAGE 2 UPHELD IT AGAIN. Three `gate` findings call the left
  16% of the frame an "unrendered black void" / "missing geometry". Sampled the shipped
  `gate` bg.png against its own depth plate over normalised [0,0.19]–[0.17,0.54]: 98.6% of
  that region is RENDERED GEOMETRY, not sky, at view-z 108–172 m against a far clip of
  172.62 m; mean luminance 18.9 (control, town body: 75.7) with 78.3% of pixels below
  luminance 12. Scanning u = 0.02..0.30 at three heights, depth runs continuously 151 -> 170 m
  out to u ~ 0.16, then steps to 122–158 m while luminance jumps from ~6 to ~115. So the
  OBJECT is real — a near-black cliff mass running to within 2 m of the far plane with a hard
  lit/unlit seam — and the CAUSE the judge names is invented. Same shape as the pink-plank
  case last round: STAGE 2 FILTERS WEAK CRITICISM, NOT CONFABULATION. The fix this points at
  is lighting/fog/reframing, not modelling.
  NEW SURVIVORS WORTH A BUILDER, triaged by eye against the plates (48 extras on the five
  fresh plates, ~20 distinct objects, 13 look real, 3 unconfirmable at plate resolution):
   -  `cottage-steps` — green cone and capsule vegetation and rock props sitting FLAT against
      a vertical cliff face, no ledge, no soil, no contact shadow. 5 findings across 3 looks,
      obvious by eye. The worst-looking new defect in the round.
   -  `cottage` — two pure-black holes in the left cliff face reading as missing geometry.
      NOT measured; treat as a perception until an instrument seconds it, given the above.
   -  `loop-stairs` — a flat untextured pale strip across the lower-left foreground.
   -  `gate` — the upper-left cliff mass reads as tiled, duplicated mesh blocks with repeating
      vertical grooves. Newly exposed BY the vista framing: that wall was barely on screen
      before. Confirmed by eye.
   -  severe vertical UV stretching on the cliff faces of four of the five fresh plates —
      one cause, four plates, and now the most-repeated complaint in the town.
   -  `loop-stairs` — "the centre wooden structure consists of fragmented pillars and
      platforms with no clear walkable path or steps". Worth naming: this plate's flight is
      THE §10.3 case, unwalkable while 72% visible. The judge STILL cannot see walkability —
      it never could — but on the first look this plate has ever had, it says the stair does
      not read as a stair. A perception, not a measurement; `ls_nav_probe.mjs` is the oracle.
  TOOL CHANGE, surgical and stated: `--replay` now takes a LIST of stamps, newest first, and
  resolves each shot from the first run that holds it — which is how a partly re-swept town
  becomes ONE report instead of two. Every shot records the run its replies came from
  (`shots[].replayOf`) and the report prints it; the "fresh this round" run is derived
  mechanically as the source with the newest `generated`, so there is no flag to set wrong.
  The tool also now compares a `--plates` pin against the shipped `cine.json` by itself and
  marks any shot whose bake has moved as against-superseded-bake. `--calibrate` no longer
  narrows the shot set when the caller has already named one (`--shots`, or the shots a
  `--replay` can serve) and REFUSES to score if a calibration shot is missing rather than
  scoring out of a hole. The header's `--report <stampA> <stampB>` line, which was never
  implemented, is replaced by the multi-stamp `--replay` that is. Regression checked: the
  old single-stamp invocation reproduces run-20260731-dellhollow exactly — 3/5 exact, 5/5
  any-plate, 56 extras, 0 errors.

## THE SHOP ROW, RE-COMPOSED FOR ITS DOORS — a door is a one-sided surface, and both
## cameras were standing behind three of them (2026-08-01, Dellhollow finisher lane, item 1)

USER'S REFERENCE (docs/qa/refs/user_shoprow_camera_ref.png): a camera angle like it
"would probably work a bit better... allowing the character to walk through all the shops
and identify the doors."

=== THE MEASUREMENT THAT NO EARLIER SWEEP HAD TAKEN ===
The 2026-07-31 re-aim to yaw 105 swept STREET, STAIRCASE and the weapon shop's door
ARRIVAL POINT. It never asked whether a door LEAF is facing the camera, and that is the
question the user asked. New probe (scratch instrument, method recorded here): 9 points on
each shop's door leaf from the `doorway(...)` calls in shelf_build.py, each one GATED ON
THE CAMERA STANDING IN THE LEAF'S OWN OUTWARD HALF-SPACE and then ray-cast against
dellhollow-master with cine_bake.visibility()'s contract (scene.ray_cast, stop 0.35 m
short). Foreshortened leaf width in pixels reported beside it.
  THE FIRST VERSION OF THE PROBE WAS WRONG AND IS RECORDED AS WRONG: it found the door's
  floor by casting a ray DOWN from z 30. The gate tier's gallery plate hangs over this
  street at z 23.33-23.66, so the ray landed on the ROOF and every door probe floated 4.5 m
  up on the gate terrace — where a high camera sees it perfectly. It scored the terrace, not
  the street, and it made high-pitch compositions look excellent. Heights now come from the
  map (landmark pos[2] = 19.0, the shelf floor; waypoints carry their own z).

BEFORE, on the shipped plates — visible fraction at leaf px:
    shelf-west  inn 0.78 @ 8.5px   chandlery 0.89 @ 43.5px   forge 0.00   armour 0.00
    shelf-east  inn 0.00           chandlery 0.00            forge 0.00   armour 0.00
  0 of 4 doors identifiable (>=0.67 visible AND >=20 px). THE SHOT THAT OWNED THE ARMOUR
  SHOP COULD NOT SEE THE ARMOUR SHOP'S DOOR. Independently seconded by red-team sweep 2 on
  the same plates: shelf-west "Enter Item Shop" ABSENT, "Enter Weapon Shop" ABSENT, "Enter
  The Boatmen's Rest" OCCLUDED; shelf-east "Enter Armor Shop" VISIBLE-BUT-ILLEGIBLE.

=== WHY ONE CAMERA CANNOT FIX IT, IN ARITHMETIC ===
shelf_build.py faces the inn's leaf x-, the chandlery's y+ (south side of the street) and
the forge's and armour shop's y- (north side). Seeing the chandlery's leaf needs an eye at
y > 5.87; seeing the forge's needs y < 8.63. The street between them is 3 m wide and the
solved standoff is 16-22 m, so THE TWO CAMERAS MUST STAND ON OPPOSITE SIDES OF THE STREET.
Both shipped ones stood on the gorge side (y 28.07 and y 15.81).
  SEARCHED, NOT ASSERTED: 1030 compositions — 720 coarse (yaw 0-350 step 10 x pitch 10-55
  step 5, both shots, both candidate ownerships) and 310 refining — each SOLVED by
  tools/cine_solve.mjs itself (no re-implementation of the standoff fit) and then ray-cast.
  NO COMPOSITION IN 1030 SEES ALL FOUR DOORS. Max doors identifiable from any single frame:
  2.

=== WHAT SHIPPED ===
  shelf-west  yaw 105 pitch 13 -> yaw 129 pitch 10, pos [20.845,28.071,26.656] ->
              [13.044,22.283,25.093], dist 23.81 -> 21.68
  shelf-east  yaw 32 pitch 18 -> yaw 342 pitch 22, pos [56.908,15.805,25.150] ->
              [58.629,2.903,26.575], dist 15.80 -> 16.84   (crosses to the CLIFF side)
  OWNERSHIP MOVED WITH THE AIM, under a rule the measurement produced — A SHOT OWNS THE
  SHOPS WHOSE FRONTS IT CAN SEE: weapon-shop goes shelf-west -> shelf-east. The middle road
  item-shop__weapon-shop stays with shelf-west (1.000 visible there, 0.864 from the east),
  so the derived seam moves from weapon-shop__armor-shop to item-shop__weapon-shop t=0.645
  — you cross into shelf-east ~2.8 m BEFORE the forge's pad, i.e. before the door it is the
  only camera that can show you.

AFTER, same probe, same instrument:
    shelf-west  inn 0.89 @ 30.3px   chandlery 1.00 @ 32.8px
    shelf-east  forge 0.67 @ 12.9px  armour 1.00 @ 30.8px
  4 of 4 doors visible and facing; 3 of 4 over 20 px (the forge reads 12.9 px — 22 m
  up-street and oblique, and it is the smallest door in the pair; nearer compositions buy
  2 px with 0.14 of the owned street's visible fraction and were refused).
  THE STREET, per map edge, visible fraction (chest+head, 0.4 m sampling):
    valley-gate__inn (the gate stair)  0.180 -> 0.200   [shelf-west]
    inn__item-shop                     0.978 -> 0.957   [shelf-west]
    item-shop__weapon-shop             0.795 -> 1.000   [shelf-west]
    weapon-shop__armor-shop            0.895 -> 0.974   [shelf-east]
    armor-shop__shelf-homes            0.529 -> 1.000   [shelf-east]
  THE STAIRCASE IS NOT WHAT PAID FOR IT — the 105 note had feared exactly that trade.
  charPxFar 72 -> 69 (west) and 90 -> 84 (east): both WALKABLE shots, the 50 px floor
  applies and is met, no cinematic exemption taken.

=== THE ARCHITECTURE REFUSES THE REFERENCE'S HEIGHT, AND THAT IS A MEASUREMENT ===
The shelf street is roofed by the gate tier's gallery plate (underside 23.33-23.66 over
x 19-29.4). The inn's door reads 0.89 visible at pitch 10, 0.44 at 16 and 0.00 at 22 — it
goes behind that plate. So the reference's high angle is unbuyable on the west half at any
yaw; pitch 10 (west) and 22 (east) are that direction taken as far as this roof allows,
and the user's intent — walk the row, identify the doors — is delivered by the door and
street numbers instead of by the elevation.

=== THE ARRIVAL THE RE-AIM BROKE, FOUND BY THE PROBE AND REPAIRED IN THE ARRIVALS LAYER ===
arrival_probe against the plates, before (measured on the HEAD checkout's own bundle) and
after: the derived spawn coming down the gate stair into shelf-west, [23.179,20.71,-3.026],
was 68.1% visible / 67.9% chest at yaw 105 and 9.9% / 0.0% at yaw 129 — a new "arrives
invisible", caused by this pass. Re-searched along the flight at 0.15 m, ranked by distance
from the seam: [23.18,20.11,-3.53], 73.6% / 75.0%, clearance ABOVE the 1.6 target (no trade
booked). A NUMBER WORTH KEEPING: the solver's clearance and a naive distance-from-the-band-
CENTRE differ by the band's own half-thickness (1.1 u). The first candidate taken here read
2.25 m from the centre and the solver correctly called it 1.23 m past the edge.
  TOWN-WIDE "ARRIVES INVISIBLE": 5 -> 4. The 4 that remain are NOT this lane's: cottage>
  lockhead (68.1%/17.9%), the cookhouse door (18.7%/0.0%), and TWO on the gate vista —
  shelf-west>gate at 0.0%/0.0% and the ow-valley portal at 20.9%/42.9%, both of which are
  the entrance reshape's cost and are live in the entrance re-composition the coordinator
  has since ordered.

=== nav_eval, N=10 EACH SIDE, AND IT DOES NOT SAY WHAT THE DOOR NUMBERS SAY ===
  (judge pinned gemini-3.6-flash, run-shoprow-before / run-shoprow-after)
                     score  onWalk  progress  stuckLegs  wentBack
    shelf-west  before 0.00   0.84     0.20      5.7        0
                after  0.00   0.85     0.00      0.0       10
    shelf-east  before 0.00   0.58     0.00      0.0       10
                after  0.20   0.93     0.20      0.2        8
  shelf-east improves on every sub-score. SHELF-WEST TRADES ONE FAILURE FOR ANOTHER, and it
  is recorded as a cost, not smoothed: the walker no longer JAMS (stuckLegs 5.7 -> 0.0) and
  now WALKS BACK UP THE GATE STAIR on 10 of 10 trials (wentBack 0 -> 10). From the new eye
  the flight the player just came down is the most legible line in the frame. This is the
  next thing to fix on this shot and it is NOT what the user asked for in this round — the
  ask was identifying the doors, and the doors are measured above. Registered here so the
  next lane starts from the measurement instead of re-discovering it.
  THE PLATE IS STILL DARK. Both new frames put the shopfronts in the cliff's shadow; the
  red-team's "deep shadows / dark wall recesses" class survives this pass untouched, because
  it is a lighting and door-legibility question (task #35's art round + the coordinator's
  cottage-door item), not a composition one. The doors are now FACING the camera and large;
  making them read is the next tool's job.
  RECORD SHOTS: docs/qa/districts/shoprow_after_shelf-west.png, shoprow_after_shelf-east.png,
  and shoprow_before_shelf-west_markers.png (the shipped frame with an emissive slab standing
  in each door leaf and a post on each landmark pad — the picture the door numbers describe).

=== GATES ===
  cine_test 647/0 (+3 soft)   seam_test 294/0 (+7 soft)   seam_walk 9/9
  plate_flat 0 of 16          routes --check clean at 16 shots
  slice_test 671/15 — 15 emb-cine + ow-valley, ZERO Dellhollow (attributed by grep, not chased)
  NO GEOMETRY CHANGED: del-cine/scene.glb is byte-identical; two cameras moved and two
  plates were re-baked (shelf-west twice, the second time for the 1 mm standoff the arrival
  override costs — cine_test asserts baked == solved).

### THE GATE BLOCK, and the seal instrument that refuses to say it is sealed

THE OLD GATE IS BUILT. It was a portal marker — two survey posts — because its portal
has `target: null` and `build_portals` skipped it, so the region's one bottleneck had
no structure on it at all. Now ONE WALL ACROSS THE PINCH, every dimension carried from
the town as a multiple of the CHANNEL's own half-width (the pinch-ratio rule, the same
numbers the seat was derived from): curtain 1.583 | doorway 1.410 | founded 1.022 |
grate 2.000. Plain coursed masonry in 0.55u courses with an alternating jog, the ROAD's
doorway ARCHED (a nine-voussoir ring), the water passage a LOW GRATE AT WATER LEVEL with
NO arch over it and the wall carried on over it unbroken — stamp 188a329, concept
gate-final.png. The wall takes a bite into living rock at both ends, because a flush
joint is the knife edge that made 2b's rectangle test lie twice.

THE NOTCH WAS CUT BY A CONSTANT AND IS NOW CUT BY THE RATIO. The gatewall's breach was
`sstep(3.5, 9.0, drd)` — nine units of yield either side of the ROAD, and nothing about
the water at all. Measured on the pinch line it left living rock at -3u and +14u: a 17u
gap for a 4.5u channel. The wall now yields where the road passes AND where the water
passes, and nowhere else:
    notch rock-to-rock        17.0u  ->  13.55u    (the town's 2.82 grate-widths at scale;
                                                    metres would ask 6.3u, which cannot
                                                    even hold the ratified channel)
    doorway centre            2.727 half-widths — the town's own number, to three places
    founded dry ground        2.30u
    strip masonry -> rock     W 0.00u   E 0.00u    (E was 0.90u until the east bite went
                                                    0.9 -> 2.4; the probe found it, not a frame)

AND THE SEAL PROBE SAYS IT IS NOT SEALED, WHICH IS WHY IT EXISTS. Flood fill from the
gate court, with the WALL'S WHOLE FOOTPRINT BLOCKING — doorway included, because the
town's 2b probe wanted 0 for a gate that is sealed at story start, while here the road
GOES THROUGH the doorway and a fill that walks through it measures nothing; the question
worth asking at region scale is IS THERE A WAY ROUND — reports 212 cells still reaching
past the pinch line. The wall meets living rock at both ends ON the pinch line, so the
bypass is ground a few units up- or downstream where the gatewall's crest dips inside
its own breach corridor. NOT FIXED TONIGHT AND NOT DRESSED UP: ow-valley is free-roam
terrain, so the terrain is the only wall there is, and 212 cells is a walkable way round
the Old Gate. The instrument runs on every build and prints all four numbers.

### RESIDUALS, TABULATED so they cannot quietly become load-bearing

    what                              map      field     delta    status
    emberbrook anchor                26.0     26.08     +0.08    good
    ember-falls                      17.0     17.34     +0.34    good
    dellhollow anchor                12.0     11.95     -0.05    good (was -9.59)
    valley-gate                      12.0     12.19     +0.19    good
    waystone                         23.6     23.70     +0.05    good
    dellhollow-moorage                1.3      5.06     +3.76    ACCEPTED as bookkeeping:
        the boat prop is seated on the WATER by moorage_frame, not by this landmark's
        height, so the visual is right. The bank rises ~5u within a unit of the water's
        edge there; the waterAccess breach relaxes bench, shelf wall, rim and gorge
        shoulder and still cannot flatten it.
    floor control [226,186]           9.0     17.08     +8.08    ACCEPTED: far corner of
        the Long Reach, no landmark, no road and no portal on it, and its floor profile
        control is already pinned at the minimum, so the height is coming from the
        canyon's own bench ramp rather than from anything this lane authored.
    OLD GATE flood fill                 0       212        212    OPEN — see above.

### THE MOORAGE'S SENTENCE WAS WRONG AND THE NUMBER WAS RIGHT
`world.json` called the Moorage "below the locks"; `dellhollow.map.json` puts moorage at
local x=76.09 and lock-five at x=86.91, so it is UPSTREAM of them and the town's own
water exit is at lock-five / north-landing. Ruled (coordinator): the town map is the
authority, the dot already followed it, and the prose is corrected to match — "the town's
upstream water door". The byte-canon dam-crest line is untouched and still asserted.

## THE ENTRANCE YOU ARRIVE AT — the vista rejected, the walking-in frame measured, five
## pieces of roof material named, and a background-leak gate that turned out to be the sky
## (2026-08-01, Dellhollow finisher lane, priority interrupt — SHIPPED INTERIM)

USER, having played del-cine: the vista camera is "from opposite the town, looking at the
town... Vesper is extremely small, and I cannot tell at all where I am or how I'm supposed
to find the next scene transition." What they wanted: the view of someone WALKING INTO
Dellhollow — the camera at the arriving player's own vantage, looking down the town's axis.

=== THE SEARCH, AND THE CONTACT SHEET THE USER PICKED FROM ===
136 compositions (yaw 140-220 x pitch 6-34) solved by cine_solve.mjs itself and ray-cast
against the master on the four questions the brief named. Five were rendered with a 1.6 m
proxy standing on the real ow-valley arrival point and sheeted:
docs/qa/districts/gatepov/CONTACT_SHEET.png. THE USER PICKED D (yaw 170 / pitch 22).
  THE CONTROL, the rejected vista, on the same instruments:
    player 25 px, 27% of her unoccluded | stair 24% | town 60% | eye 0.6 m from rock
  SHIPPED (yaw 174 / pitch 20, D adjusted twice — see below):
    player 66 px, 100% unoccluded       | stair 26% | town 21% | eye in open air
  The trade is stated rather than buried: 39 points of town for 2.6x the player and a
  frame she is not buried in. charPxMin exemption NARROWED 24 -> 45, and narrowed in kind:
  what breaches the 50 px floor is charPxFar — the far end of the 21 m of rim road this
  shot owns, 40+ m out — not the player, who is 66 px.

=== THE FIRST ADJUSTMENT: THE TOWN'S CUT EDGE, MADE AN ASSERTION (user redline 2) ===
New probe: 600 rays through the lowest 8% of frame, MARCHING PAST render-only volumes and
leaf cards, counting rays that LEAVE THE WORLD.
    D as picked, 170/22   6.00% of the band leaves the world  <- the cross-section
    174/22                0.00%, pitch and standoff unchanged
    the row: yaw 170 is clean only at pitch 16-18; yaw 174 is clean 16..22 and 0.83% at 24.
  A CORRECTION, RECORDED BECAUSE IT WOULD HAVE BEEN A CONVINCING WRONG NUMBER: the first
  version of this probe also counted BACKFACE hits and read 25-35% at every composition.
  Those were fx_haze_south's fog cube (118 of 156) and the cliff shells' own inward
  normals — a modelling convention, not a cut edge. Only the MISS count is asserted.

=== THE SECOND ADJUSTMENT: THE FIRST ONE COST THE WAY ON ===
At 174/22 the gate staircase — this shot's ONLY onward exit — measured 0.00 by ray-cast
and 8.5% VISIBLE on the baked plate (shot_probe), against 37.8% on the vista: from 22
degrees the entrance tier's own ground hides the flight that drops off it. A frame that
cannot show its only exit can never score. Pitch came back to 20:
    staircase 0.26 by ray-cast (the user's own pick D measured 0.28 — delivered as seen)
    and 14.6% VISIBLE on the shipped plate; bottom band still 0.00%; player 63 -> 66 px.
  MEASURED AND REFUSED: 174/16 recovers the most staircase (0.42) and the biggest player
  (72 px) but flattens the vantage the user asked for and drops the town to 0.14.
  STILL BELOW THE VISTA'S 37.8% ON THE PLATE, and that is the honest headline for this
  shot's remaining risk: the flight is visible but not dominant, and the cliff round is
  the next chance at it.

=== THE FIVE PIECES OF ROOF MATERIAL (user redline 1), NAMED BY PROVENANCE ===
tools/t2_gate_declutter.py (new). Every roof panel over the porters' yard, with a 25-ray
footprint census and who placed it:
    t2c_G6_tarps_cargo       4 verts  2.6x2.6   25 sup  0 void  gap 0.40  CULL (bare quad)
    t2c_GB4_yard_tarp_big   20 verts  4.8x4.0   25 sup  0 void  gap 0.11  CULL
    t2c_G1_awning_porters_a 24 verts  3.0x2.25  18 sup  7 VOID  gap 0.03  CULL
    t2c_G2_awning_porters_b 24 verts  3.0x2.25  25 sup  0 void  gap 0.05  CULL
    t2c_G3_awning_tollyard  80 verts  1.61x1.28 24 sup  1 void  gap 0.09  KEEP
PROVENANCE DID THE WORK AND IT IS THE REUSABLE PART: four of the five were placed by
tools/t2_color_pops.py from SCREEN-SPACE PROBE RECTANGLES — its own successor's docstring
says those rectangles "carried no idea of what was UNDER them" — to put colour in the
vista the user has now rejected. A prop whose only justification was a retired frame has
no standing in the frame that replaced it. G3 alone was placed by t2_gate_awnings.py's
five-constraint search against measured ground, and it stays. Two of the four also fail on
their own terms (a 4-vertex sheet floating 0.40 m over the walk pad; a third of a footprint
over a 31.85 m drop). t2c_G* at the entrance: 12 objects -> 8.
  NOT MEASURED, AND OWED: the pops-of-colour chroma cost of removing four colour panels
  from this frame, against the [5%, 11%] band (tools/t2_probe_chroma.py).

=== plate_flat FLAGS THE GATE AT 1.75%, AND IT IS THE SKY ===
The screen reports a constant-colour far-plane region, RGB 155,91,61, ndc x -1.00..-0.04
y 0.92..1.00 — the same RGB as the Crossing's documented backdrop card, which is what made
it worth an 800-ray census rather than a shrug. 706 of 800 rays through that band hit
NOTHING AT ALL: it is the world background. cliff_east_closure takes 54 and fx_haze_south
40, at the edges. Sky and a background card have the same signature by construction —
constant colour, far plane — and no Dellhollow plate had ever had sky in frame before, so
the case had never arisen. SHIPPED WITH THE FLAG DECLARED AND ATTRIBUTED, not chased, and
the instrument amendment (exclude the world background) is proposed to the coordinator
rather than made here, because plate_flat is shared.

=== THE GATE WALKER CHOKE, DIAGNOSED (coordinator's assignment) — VERDICT (c) WITH A (b) ===
Overlay frames: docs/qa/naveval/run-gate-vista-entrance/overlay/trial{0,1,3}.png — the
judge's waypoint, the point the walker was ACTUALLY sent to, and the body's whole travel,
all drawn from results.json in its own image coordinates.
  73 waypoints over 10 trials. 59 of 73 (81%) of the walker's targets stand BELOW h 20
  while the walker stands at h 24.04 on the rim road: they are on the quay and the water,
  20+ m down. Every leg ends 'refused' (56) or 'no-progress' (13); not one leg reached.
  NOT (a): the body never travels more than ~2.5 m from spawn, and oracle-world was 1.000.
  (c) IS THE MAIN CAUSE: at a 75 m standoff the frame stacks five tiers, the character is
  27 px with occludedFrac 0.897, and the judge routes the most legible path in the picture
  — the waterfront boardwalk — which belongs to other shots entirely. Its reasons are RIGHT
  ("follow the pier and climb the cliffside stairs"); the pixels it points at are not where
  it thinks.
  (b) IS REAL AND IS AN INSTRUMENT DEFECT WORTH FIXING: 44 of 73 waypoints are `occluded`,
  and for those nav_eval's `rt` marches the camera ray PAST the occluder to the next walk
  surface behind it — so the target is fabricated tens of metres deeper than the pixel the
  judge chose. Measured displacement between the judge's pixel and the walker's actual
  target: mean 53 px, median 20 px, worst 295 px on a 1344x768 frame. unproject()'s own
  docstring says occluded points are recorded as OFF-ROUTE PERCEPTION; they are recorded,
  and then walked to anyway. Proposed amendment (coordinator's call, nav_eval is shared):
  when `occluded`, do not retarget through the occluder.
  AND THE ENTRANCE RESHAPE IS LIKELY THE FIX FOR (c): the player is now 66 px and 100%
  unoccluded, and the waypoints land on near-field ground she can actually walk. The N=10
  re-run on the new plate is the next thing to do and is NOT done here.

=== THE VACUUM CENSUS, for the cliff round (coordinator's assignment 3; nothing sculpted) ===
Mesh counts in the frustum by 4 m band, z 32 down to -4: 9 / 105 / 47 / 126 / 113 / 52 /
81 / 258 / 7. The z 8-12 band (52) is the vacuum: between the shelf and the water there is
almost nothing but cliff shells (cliff_town_b, cliff_town_mid, cliff_town_back).
543 plants stand in the frustum. A SCREEN — a single down-ray from each clump's footprint
CENTRE, so a clump hanging off a lip reads as floating and this is a candidate list, not a
verdict — flags ~40 with nothing under them, at exactly two lips:
  veg_gate_tuft_* and veg_gate_rimclump_*, rim road's gorge edge, y 10.5-11.9, drops 26-42 m
  veg_shelf_tuft_/fern_/rimclump_*, shelf edge, x 21-25 y 10.8-11.2, drops ~24 m
Worst named: veg_gate_rimclump_15 [1.19,0.12,28.96] drop 42.54; veg_gate_rimclump_8
[1.44,2.18,26.93] drop 33.51; veg_gate_tuft_25 [12.13,10.79,24.43] drop 32.16.

=== GATES ===
  cine_test 648/0 (+2 soft)   seam_test 294/0 (+6 soft)   seam_walk 9/9
  routes --check clean at 16 shots      slice_test 671/15, ZERO Dellhollow
  plate_flat 1 of 16 — the gate, DECLARED above and proved to be sky by an 800-ray census
  ARRIVES INVISIBLE town-wide 4 -> 2, and both that went were this shot's:
    ow-valley portal 20.9%/42.9% -> 100.0%/100.0%   (the coordinator's predicted dissolve)
    shelf-west>gate  0.0%/0.0%   -> 100.0%/100.0%   (arrival re-searched at the new aim)
  The 2 that remain are not this lane's: cottage>lockhead and the cookhouse door.
  ONE PLATE REBAKED: only `gate` framed the culled props (32/32 bbox corners in frame,
  every other camera 0/32), derived not assumed.
  RECORD SHOT: docs/qa/districts/gatepov/gatepov_y174_p22.png (the confirm render) and the
  shipped plate itself.

## THE hash() DETERMINISM SWEEP — every salted seed in the builders, and the one that
## turned out not to be (2026-08-01, Dellhollow finisher lane, brief item 3)

FROM THE 3b FINDING: gs_build.py was seeding plank layouts with Python's `hash()`, which
is salted per process, so two runs of the unchanged builder against the unchanged master
differed by 0.03 m in gs_treads' z-min. Fixed there with zlib.crc32; this is the sweep the
entry called for.

=== EVERY HIT, WITH ITS VERDICT ===
`grep -rn "hash(" tools/` returned 22 lines, 19 of them live call sites in 12 files.
CONVERTED (12 files, 19 call sites), all geometric — a seeded plank/prop/vertex-colour
layout that lands in the exported mesh and therefore in the content digest:
    boatyard_build.py   2   locksfoot_build.py  2   ls_build.py         1
    lg_build.py         1   qm_build.py         1   waterfront_build.py 2
    weave_build.py      2   cx_build.py         2   weave_lib.py        1
    locksfoot_kit.py    1   scenekit.py         1   (+ gs_build.py, already fixed in 3b)
NOT A DEFECT, and the reason is worth keeping because it looks identical to the eye:
    item_int_build.py:365  random.Random(hash((round(x0,3), round(z,3), seed)) & 0xffffffff)
    Python salts the hashing of str and bytes ONLY. A tuple of numbers is not salted.
    MEASURED, three processes: hash((1.234, 5.678, 7)) & 0xffffffff returns 2530675270
    under PYTHONHASHSEED 1, 2 and 3; hash('shelf_a') & 0xffff returns 3906 / 64822 / 31178
    under the same three. Every call site passes an int `seed`, so the tuple is numeric.
    LEFT AS IS, deliberately: converting it would re-roll the item shop's shelves for no
    determinism gain.

=== ONE IMPLEMENTATION, NOT TWELVE ===
`boatyard_lib.stable_hash()` (new) — zlib.crc32 of the utf-8 bytes. It lives there because
that is the module the district builders already take their geometry kit from, so there is
one implementation and it cannot drift. weave_lib, locksfoot_kit and scenekit do not use
the kit but import the one function.

=== PROVED, NOT ASSERTED ===
1  THE MECHANISM, isolated: a Random stream of the length a real deck draws, over seven
   real object names, digested. Under PYTHONHASHSEED 0 / 1 / 987654 —
     converted   d6041d1c...3964   d6041d1c...3964   d6041d1c...3964
     old (hash)  700a6652...9160   37b17bc0...8710   e05d0581...a420
   The contrast is the point: the same probe on the OLD expression returns three different
   digests, so this is a positive control and not a tautology.
2  A REAL BUILDER, END TO END: weave_build.py's `deck` phase run twice in separate Blender
   processes under PYTHONHASHSEED 3 and 77, digesting every wv_ mesh it produced (world
   verts to 1e-5 + material names):
     151caf2ee7fff49b9bb584e16853cb3f5be0823b541dd2993d613e34e923e301   both runs
   Run WITHOUT the `save` flag, so the master on disk was never touched (confirmed by git).
3  All twelve files byte-compile.
DEFERRED AND LISTED RATHER THAN CLAIMED: a two-run digest for each of the other ten
builders. Each is a full district rebuild and the seed path is the only thing that changed
in any of them, which is what proof 1 isolates; the honest statement is that the mechanism
is proved for all twelve and the end-to-end run is proved for one.
A ONE-TIME RE-ROLL IS EXPECTED AND IS NOT A REGRESSION: crc32 returns different numbers
from hash(), so the next run of each converted builder draws a DIFFERENT — but from now on
FIXED — layout. Nothing was re-run here, so no district art moved in this commit.

### THE SEAL CLOSES AT 0 — and the change I made to close it turned out to be unnecessary

FIRST, THE RE-FRAMING, ratified by the coordinator and worth keeping as doctrine: THE
TOWN AND THE REGION ASK DIFFERENT SEAL QUESTIONS. Emberbrook's 2b probe asks "IS THE GATE
SEALED" and wants 0, because that gate is shut at story start. ow-valley's asks "IS THERE
A WAY ROUND" WITH THE DOORWAY OPEN, because here the road GOES THROUGH the gate — it is
the way to Dellhollow — and a flood fill that walks through the doorway measures nothing
at all. Same landmark, same wall, two instruments, two truths.

AND THEN THE 212-CELL BYPASS TURNED OUT TO BE MY OWN PROBE. It counted any cell downstream
of the pinch line IN THE RIVER'S FRAME, and the gatewall runs DIAGONALLY across that frame
— so cells still on the highland side, riding the band's own inner edge 20 to 30u west of
the channel, scored as escapes into a valley they had not reached. Asked properly (out
past the gatewall's OUTER face, sign-calibrated on ember-falls) the count is 0.
    flood fill past the pinch, doorway blocked      212  ->  0
    strip masonry -> living rock                    W 0.00u   E 0.00u   (E was 0.90u until
                                                    the east bite went 0.9 -> 2.4)
    notch rock-to-rock 13.55u · doorway 2.727 half-widths · founded 2.30u
I HAD ALREADY WRITTEN THE FIX BEFORE I CHECKED WHETHER IT WAS NEEDED — a crest floor on
the gatewall, so the ridge could not sag to walkable height inside its own band (it sags
to 25.7..29.1 against a 29.10 threshold, which is real). It took the count 212 -> 71; the
instrument fix took 71 -> 0. So I built the tile once more with the floor REMOVED: still
0. THE FLOOR BOUGHT NOTHING, AND IT IS OUT. A change with no evidence behind it does not
get to stay just because it was already written and looked principled — that is the
pink-plank rule pointing at my own hands. What the sag actually is, measured: ground that
connects to the highland, which is where it belongs, and not to the valley.

### EMBER FALLS IS BUILT AS A FALL

Measured it was a waterfall (5.65u of drop over 1.50u of arc); rendered it was a chute,
because the water surface is one strip following the river's authored z. Three pieces, and
nothing else: a hard rock LIP so the water leaves the ground rather than a slope, a bowed
near-vertical CURTAIN (9 x 5) hung from it, and a PLUNGE POOL with 22 pieces of churn — a
fall with no foam is a pane of glass. THE REACH IS FOUND, NOT TYPED: the lip is where the
gradient first breaks 1.0u per unit of arc and the foot where it drops back under 0.4, so
a restamped river moves the fall with it — the same rule the mesa lip now follows, and for
the same reason. Lip arc 57.5u z 22.63 -> foot arc 59.0u z 16.98.
    AND THE WHITE-MATERIAL GATE CAUGHT IT. `water_falls` exported white on the first
    build: a new prop has to be named in PROPKEYS and UVKEYS or it ships unpainted, and
    valley_verify said so before any frame did. COLOR_0 now 26/26.

### THE JUDGE DOES NOT REACH THIS LANE, IN ONE LINE
GEMINI is live again (the "depleted" note in my handover was stale). It still buys nothing
here tonight: `scene_redteam` and `nav_eval` both construct from `townmap/<town>.map.json`
+ `<town>.cameras.json` + the bundle's `cine.json` + `<town>.routes.json`, and ow-valley is
a real-time region with no camera file, no cine.json and no depth plates — there is no
`--town` it can be. Feeding it region renders would mean building a new instrument, which
is not tonight's work. THE PERCEPTUAL QUESTIONS GO TO THE MORNING BOARD UNANSWERED AND
NAMED: does the notch read as a bottleneck, the falls as a plunge, the corridor as a
corridor, and Dellhollow as one bank. Every geometry claim in this entry is an instrument
reading.

## THE STILT WATERFRONT, MEASURED — the four "deckless pads" are one line of map, four
## times, and here is the tape (2026-08-01, Dellhollow finisher lane, task #30 part 1)

USER ANNOTATION (docs/qa/refs/user_waterfront_ref.png): "Extremely confusing / incomplete
geometry, walking on water. Simplify and tidy up please."

=== THE BASELINE, RE-MEASURED ON THE SHIPPED BUNDLE ===
tools/walk_water_audit.mjs, step 0.4 m: 15250 samples, 11805 supported, 1642 marginal
(deck > 0.6 m below), OVER OPEN WATER 1802, OVER VOID 1 — DEFECT RATE 11.82%, across 39
walk records. (The brief's 11.83% and 4 deckless pads, confirmed independently.)
The four worst records are the four deckless landmark pads:
    walk_lm_moorage        607 samples over water, water 1.05 m below
    walk_lm_drying-decks   241                    6.46-6.71 m below
    walk_lm_fish-dock      188                    0.80-1.05 m below
    walk_lm_north-landing  100                    2.79-3.04 m below

=== THE CAUSE IS NOT THE DISTRICTS. IT IS THE PAD ===
All four are class `area` landmarks with an `extent`, and the derive makes a FILLED SQUARE
of side 2*extent: moorage 8x8 m, fish-dock 8x8, drying-decks 7x7 (6.7 m above the water),
north-landing 6x6. None is a dock-shaped pad. locksfoot_build.py had already written the
finding down without it being actioned: "`walk_lm_moorage` is a FILLED disc (manifest 35),
so everything the moorage WORKS with has to stand off it — on staging outside the corridor."
  DECKING THEM AS THEY STAND WAS REFUSED, and the coordinator ruled the same way: honouring
  8x8 m at the moorage means building 64 m2 of pier over the river, at the one place the
  story boat moors, which is the opposite of "simplify and tidy up".

=== THE TAPE, AND THE FOUR RECTANGLES IT RETURNS ===
tools/landing_footprint.py (new). 0.2 m grid over each pad; from just under the pad's top,
the first RENDER-VISIBLE hit — walk_water_audit's own rule, so the two cannot disagree —
counts as LANDED when it is a solid within 0.60 m of the foot. Then the largest ALL-LANDED
axis-aligned rectangle, by histogram scan; NOT the bounding box of the landed samples,
which for a scattered mask is just the square you started with.
    landmark        pad square        largest all-landed rectangle        landed
    moorage         8.0 x 8.0  64 m2  [72.09..72.49, 26.20..29.20]  1.2 m2    4%
    fish-dock       8.0 x 8.0  64 m2  [56.49..61.69, 29.60..31.60] 10.4 m2   61%
    drying-decks    7.0 x 7.0  49 m2  [61.77..68.77, 26.70..29.50] 19.6 m2   55%
    north-landing   6.0 x 6.0  36 m2  [102.65..108.65, 24.00..26.00] 12.0 m2 62%
  READ IT CAREFULLY, because the two columns say different things. THREE of the four are
  more than half decked already (55-62%) and their fault is that the square OVERHANGS an
  L-shaped deck — the fix is a footprint, and little or no new geometry. THE MOORAGE IS THE
  REAL OUTLIER: 4% landed, and the only fully-landed rectangle in 64 m2 is 0.4 x 3.0 m of
  lf_stage_moorage_w, the west store bench. The moorage needs a footprint AND a landing
  actually built under it.

=== WHERE THIS STOPPED, PLAINLY ===
The coordinator authorised a one-time self-stamp of the map for these four footprints
(their file), on the emberbrook watermill's `footprint` precedent, with the derive extended
to honour it and `extent` kept as the fallback. THAT STAMP IS NOT DONE, and neither is the
residual decking, the re-derive, the re-audit or the plate rebakes it implies. What is done
is the part that is expensive to redo and cheap to act on: the instrument, and the four
measured rectangles above. The remaining 35 records (~666 water samples) are ribbon
overrun and stilt-cluster geometry and are untouched.

## THE WATERFRONT FOOTPRINTS, STAMPED — a pad is now a list of measured rectangles, and
## the disc that put 64 m2 of walkway on the river is gone from the data
## (2026-08-01, Dellhollow finisher lane, task #30 part 2)

COORDINATOR RULING BUILT AGAINST: a footprint is a LIST of axis-aligned rectangles (union
= the pad); every rect must be measured-landed by tools/landing_footprint.py's own rule,
which is now the DEFINITION of a legal footprint rect; `extent` stays the fallback;
one-time self-stamp of the map authorised.

=== WHAT WAS STAMPED, AND WHY A LIST EARNS ITS KEEP ===
Greedy cover: largest all-landed rectangle, mask it out, repeat, stop under 1.5 m2.
    landmark        old disc            stamped rects                         area
    moorage         extent 4, 50.3 m2   [72.6..79.4, 31.3..33.1]              12.2
                                        [70.9..71.9, 26.2..29.2]               3.0
    fish-dock       extent 4, 50.3 m2   [56.49..61.69, 29.6..31.6]            10.4
                                        [56.49..61.69, 24.4..26.0]             8.3
    drying-decks    extent 3.5, 38.5    [61.77..68.77, 26.7..29.5]            19.6
    north-landing   extent 3, 28.3      [102.65..108.65, 24.0..26.0]          12.0
                                        [102.65..108.65, 28.6..30.0]           8.4
  167.4 m2 of derived walkable pad -> 73.9 m2, and the 93.5 m2 that goes is river.
  THE LIST IS NOT A LUXURY: as ONE rectangle each, fish-dock keeps 10.4 m2 instead of 18.7
  and north-landing 12.0 instead of 20.4 — 40% of the real deck would have been thrown away
  by a single-rect schema, because these landings are L-shaped.
  THE MOORAGE IS DIFFERENT IN KIND and the numbers say so: NO all-landed rectangle of
  1.5 m2 exists anywhere inside its 64 m2 disc (3% landed). Its two rects are measured off
  lf_stage_moorage and lf_stage_moorage_w — the staging locksfoot_build.py put OUTSIDE the
  disc, exactly as its own comment says it had to ("everything the moorage WORKS with has
  to stand off it"). So the moorage's pad does not shrink onto its deck; it MOVES onto it.

=== THE DERIVE, EXTENDED AND PROVED ===
tools/town_blockout.py's `area` branch reads `footprint` in place of `extent` and joins the
rects into ONE walk record under the same name — the name is the ownership contract every
camera, seam and audit resolves by. Run into a throwaway scene, printed:
    moorage       FOOTPRINT  bbox [70.9,79.4,26.2,33.1]      16 verts   15.2 m2
    fish-dock     FOOTPRINT  bbox [56.49,61.69,24.4,31.6]    16 verts   18.7 m2
    drying-decks  FOOTPRINT  bbox [61.77,68.77,26.7,29.5]     8 verts   19.6 m2
    north-landing FOOTPRINT  bbox [102.65,108.65,24.0,30.0]  16 verts   20.4 m2
    quay-deck / market-stalls / porters-yard / slipway  extent, 64 verts each — UNCHANGED.
  The fallback is proved by the four that were not stamped deriving byte for byte as discs.

=== THE PART THAT IS NOT CHEAP, AND IT IS NOT THE STAMP ===
`walk_lm_*` IN THE LIVE MASTER CANNOT BE RE-DERIVED BY RE-RUNNING THIS TOOL. town_blockout.py
WIPES the scene and writes dellhollow-town.blend; the master's walk records are legacy
blockout geometry that eight district builders have since been built around, and the
districts' own contract is "walk_*/bar_* are canonical topology: never moved, never edited".
Bringing the stamp into the master is therefore a TARGETED PAD REPLACEMENT — swap four
meshes in place, keeping name, collection and hide_render — followed by the residual
decking, walk QA, the audit re-run and the plate rebakes the changed collision implies.
That work is handover-safe and is NOT done. What is done is the part that is expensive to
redo and cheap to act on: the measurement, the ruling encoded in the data, and a derive
that will produce it correctly for every future rebuild.
  THE AUDIT NUMBER STILL READS 11.82% and will until the master pads are swapped. Nothing
  in this entry claims otherwise.
  ALSO RULED AND WORTH THE LINE: walk_water_audit joins the standing gauntlet for any lane
  touching walk records or waterfront geometry. "The instrument that should have caught it
  was never pointed at it" is this project's recurring sentence, and the fix each time is
  pointing the instrument permanently.

## THE DRESSING PILOT'S GROUND DEFECT WAS Z-FIGHTING, NOT A TEXTURE — plus a count that
## was still not a density, and a one-ray census that lied about a canopy
## (2026-07-31, dressing pilot lane, round 2)

DELIVERED: `docs/qa/emberbrook/styleprobe/dress2-{a,b,c}.png` against `probe2-{a,b,c}.png`,
side by side in `pilot.html`. Engine `tools/emb_dress.py`. AT THE GATE, not approved.

THE BLOCKER, AND WHY EVERY CHECK RUN ON IT WAS BOTH CORRECT AND USELESS. The ground rendered
a hard-edged white-and-black angular pattern across the whole corner. The previous lane had
ruled the textures IN (valid JPEG, paths resolve) and the scatter OUT (it persisted at 200
clumps) and found no missing image. All true. None of it could find the defect, because the
defect was not in the material.
  BISECTED ON AN INSTRUMENT FIRST, per the handover's own order: a minimal scene, one UV-less
  plane, one verbatim copy of `ground_material()`'s graph, four variants (Normal Map / no
  normal / Bump / with UVs). ALL FOUR RENDERED CLEAN. That exonerated the material AND the
  leading missing-UV hypothesis in one pass — Blender 5.1 does not produce garbage from a
  Normal Map node on UV-less geometry — and moved the search into the built scene.
  WHAT THE SCENE PROBE FOUND: `emb_dress_scatter_ground` — 12 864 polygons, NO MATERIAL AT
  ALL, `hide_render = False`, `show_instancer_for_render = True`, and a world matrix
  IDENTICAL to `emb_ground_valley`'s. The grass emitter is a COPY of the region's own ground
  faces (that copy is what made the requested count land inside the region). It is meant
  never to render. Two coplanar surfaces, one of them Blender's default grey BSDF, and
  Cycles' depth tie breaks per triangle: THE PATTERN WAS Z-FIGHTING. It survived the scatter
  being cut to 200 clumps because the copy is made whatever the count is. Confirmed by
  hiding that one object in the built scene and re-rendering: pattern gone, nothing else
  changed.
  THE LINE: `ParticleSettings.use_render_emitter = False`. THAT PROPERTY DOES NOT EXIST IN
  BLENDER 5.1 (verified directly: `hasattr` False, the set raises AttributeError). It raised
  into a fallback that set `emit.hide_render = False` — the WRONG PROPERTY AND THE WRONG
  VALUE. A silent API drift became half a frame. Fixed to the live property,
  `Object.show_instancer_for_render = False`, with the try/except REMOVED and an assert
  behind it: if this moves again the build must fail, not render a duplicate. (`hide_render`
  is not the tool here — it would take the particle system down with the object.)

A COUNT IS NOT A DENSITY, AND THIS FILE HAS NOW PAID FOR IT TWICE BY DIFFERENT MECHANISMS.
The first was AREA: `count` spread over the whole valley then culled to a 30 m disc, fixed
by copying the region's faces into their own emitter. The second is WEIGHT, and the region
emitter did not touch it — Blender scatters `count` over the emitter's SURFACE and only then
kills each particle with probability (1 - the vertex weight under it), so the landed number
is `count x mean weight`. MEASURED: 1307 m2 of the emitter's 3232 m2 carries grass weight,
mean weight 0.40 — so the 260 000 being requested landed about 105 000, and the ratified
probe's density had quietly become two fifths of itself AGAIN.
  The knob is now a DENSITY in clumps per m2 of full-weight ground (`--grassdens`); requested
  and landed are both printed and never conflated.
  THE NUMBER WAS SWEPT, NOT CHOSEN: one build, one camera, three renders at 200 / 420 / 700,
  judged on matched NATIVE-PIXEL ground crops. 200 still shows substrate between the tufts,
  420 closes most of it, 700 reads as continuous turf with the dandelion heads probe2-c has.
  Default 700, which on this corner requests 2 262 260 and lands ~915 000.
  AND THE PHOTOMETRIC INSTRUMENT WAS CONFOUNDED, which is worth recording because it nearly
  sent the sweep the wrong way: a green-fraction/high-frequency measure over the frames read
  LOWER at higher density, because the crops were being resampled to a common width and the
  shadow pattern differed. Compare at native pixels or do not compare.

THE TRODDEN FIELD WAS COMPOUNDING, and the ground it bared was not walked on. The doorstep
suppression was applied once per walk pad within 6.50 m; this corner carries 162 walk meshes,
so four pads at 5 m compounded to 0.13x on open ground. NEAREST doorstep only now, and the
radii are named constants (TROD 1.30 m off a tread, DOOR 3.20 m off a doorstep) with the
weighted-area fraction printed beside them so the next reader tunes against a number.

AND THE TREADS THEMSELVES WERE MOST OF THE "DESERT": 162 flat rectangles at HSV value 0.62
rendered as pale pink slabs with their own edges drawn. A tread is worn earth — value 0.42,
multiplied by an object-space noise so the grain is the same size on a 1 m doorstep and a
30 m lane. MATERIAL ONLY: no vertex moves, so every tread is the one walk QA already measured.
  MEASURED FIRST, BECAUSE THE OBVIOUS READING WAS WRONG: mean ground colour in the frames was
  ALREADY at the bar (probe2-a hue 0.123 sat 0.50 val 0.24; the pilot 0.104 / 0.57 / 0.34).
  The gap was never a colour cast. It was blade coverage and slab edges.

TWO CAMERA FAILURES THAT ONLY A RENDER FINDS, both the same family: an angle measured against
the throwaway's INVENTED flat terrain, applied to real ground.
  (1) THE CAMERA WAS UNDERGROUND. probe2-c is a -6 deg elevation over a ground invented flat
  at zero, so its camera stood 1.80 m up. Through the 27.1 m standoff against this subject it
  seats at z 0.38 while the ground there is 2.52 — frame c rendered BLACK with one beam
  across it. The camera is now SEATED at the town's ground plus the probe's own 1.80 m eye
  height (z 4.32) where the angle puts it under; the aim does not move, so the bearing and
  the lens are still the probe's.
  (2) THE CAMERA STOOD BEHIND THE TOWN'S OWN TREELINE. The standoff is solved against the
  subject's bounding sphere, which put frame a 42.9 m out — 13 m OUTSIDE the 30 m corner this
  pilot dresses. A RAY CENSUS now runs before every shot (this repo's rule that a ray-cast is
  the only visibility oracle, pointed at the pilot's cameras) against three NAMED subjects.
  MEASURED: frame a the wheel 22% clear, the mill 89%, the dam 22%, nearest blocker
  `fir_tree_01` at 16.4 m of 43.3; frame b the wheel 100%, the mill 56%, the dam 100%;
  frame c 78% on all three.
    THE CENSUS NEEDED TWO CORRECTIONS AND BOTH ARE THE POINT OF WRITING IT DOWN.
    (i) `scene.ray_cast` DOES NOT HONOUR `hide_render`, and this pilot hides the undressed
    gray massing — so the first version reported the dam blocked by
    `lm_hillside-cottage_roof`, a roof that does not render. A census that counts invisible
    occluders is worse than none: it would have walked the camera away from a clear shot. It
    now marches past any hit whose object is hidden.
    (ii) IT WAS ONE RAY AND THE RAY LIED. It reported frame a's wheel CLEAR at a standoff
    whose render shows the wheel almost entirely behind the conifer — the ray had threaded a
    gap in an alpha-card canopy, and the camera had already been moved on that reading, which
    cropped the mill for nothing. Nine rays over a disc of the subject's own radius now, and
    the answer is a clear FRACTION. A single ray through foliage is a true measurement of the
    wrong thing.
    THE OCCLUDER IS NOT MOVED, AND NEITHER, MUCH, IS THE CAMERA. Those trees are the
    blockout's searched placements. The walk-in is bounded at 0.88x AND must EARN itself by
    lifting the hero's clear fraction 25 points; on frame a it lifts it 22% -> 33%, so the
    probe's standoff is KEPT and the frame is REPORTED occluded. Which side of the mill the
    probe's bearing falls on is a COMPOSITION question and the coordinator owns it — the
    throwaway had open water on that bearing because it invented its own layout.

STATUS: at the gate, awaiting the coordinator. Not integrated; no district-wide work, no
master-blend touch, lane A's binaries untouched. Open item: frame a's bearing, above.

## THE STILT WATERFRONT, BUILT — four pads that shrank onto their decks and then could not be
## reached, the landings that fixed it, and two instruments that were lying about the same thing
## (2026-08-01, Dellhollow waterfront lane, task #30 part 2)

=== THE HEADLINE NUMBERS ===
walk_water_audit.mjs, step 0.4 m, on the shipped townwalk bundle, BEFORE this lane / AFTER:
    samples                        7629    ->  7191
    OVER OPEN WATER                 748    ->   237
    OVER VOID                         0    ->     0
    DEFECT RATE                    9.80%   ->  3.30%
    records carrying a defect        23    ->    16
    DECKLESS LANDMARK PADS            4    ->     0     (the brief's target)
Both columns are on the CORRECTED rule below, so they are comparable to each other and NOT
to the 11.82% in the brief. The old number is not wrong, it answered a different question.

=== THE AUDIT WAS COUNTING THE UNDERSIDE OF THE FLOOR ===
walk_water_audit took every triangle with |n.y| > 0.5 as standable. A walk record is a
CLOSED SLAB, so that is both faces: measured town-wide, 7051 up-facing samples against 7043
down-facing, and 578 of 858 defects (67%) were on the DOWN faces. A 0.25 m pad whose top
lands on a 0.14 m deck has its bottom below that deck, so the down-ray from the underside
sees straight past the deck to the river and reports walking on water while the player is
standing on planks. THE SIGN WAS CHECKED BEFORE IT WAS TRUSTED: all 308 records carry
samples on both orientations, so no record's winding is inverted and none vanishes under
the new rule. The audit now skips down-faces and prints the count it skipped.

=== AND landing_footprint WAS STOPPING ON THE WALK NETWORK ===
Its docstring claimed walk_water_audit's rule "so the two instruments cannot disagree".
They disagreed. That audit filters the non-drawn meshes out of its index BEFORE casting;
`scene.ray_cast` cannot filter, so this file took the nearest hit and rejected it by name —
which silently means NOT LANDED. Any deck built under a walk ribbon therefore read as bare
water: it scored the four landings below at 53-90% and would have refused to let them be
stamped. Both files (and waterfront_landings.py, the third copy) now PASS THROUGH
walk_/bar_/fx_/cam/REF_/KEY/lm_ and stop only on drawn geometry. Same rule, three files,
one definition — which is what the first version said and did not do.

=== THE PADS REACHED THE MASTER (960e13b's owed half) ===
tools/walk_rederive.py gained `--lm <id>`: a landmark pad is a record with no edge, so
`--edge` could not name one and the report filed all four under "(no edge)". Nothing else
differs — same blockout as the only generator, same peer settings read off the records being
replaced, same snapshot/revert. Blockout re-raised from the stamped map; the report showed
the four pads as the ONLY new stale records (the other 21 are the known bar_ drift), so the
regeneration itself is clean. master_walk_qa: 26 failures -> 22, and the 22 are the identical
pre-existing strings at identical magnitudes. Ray coverage over x 2..40 y 14..34 is
bit-identical before and after (1308/1308); over the waterfront x 55..112 y 18..36 it goes
93.02% -> 93.07% (188 blocked samples -> 158).

=== THE PART THE RULING COULD NOT HAVE KNOWN: ALL FOUR PADS CAME OFF THE NETWORK ===
A connected-component sweep over walk_bodygate's own step rule (0.075 m lattice, body
0.6 x 1.3, STEP_UP 0.63 / STEP_DN 0.8 — the runtime's constants), run on the shipped bundle
before and after the stamp:
    BEFORE  moorage 14252 nodes in the big component; fish-dock 5892 in it; north-landing
            8072 with its own ribbons; drying-decks 544 connected + ~5600 already islanded.
    AFTER   walk_lm_fish-dock  1076 + 786 nodes, BOTH islands
            walk_lm_north-landing 2598 + 2408 + 88 + 52, ALL islands
            walk_lm_drying-decks 2450 + 1518 + 228, ALL islands
            walk_lm_moorage 3474 island + 304 reachable (its west store)
CAUSE, ONE SENTENCE AND IT IS THE SAME SENTENCE FOUR TIMES: town_blockout draws every
incident ribbon to the landmark's `pos`, and `pos` is not inside the measured footprint —
it is in the water gap between two wharves (fish-dock, north-landing), 0.70 m off the deck's
south edge (drying-decks), or 4.3 m short of the staging (moorage). The disc had been
papering over that, on the river.

=== THE LANDINGS (tools/waterfront_landings.py, new) ===
One connective landing per landmark: plank deck on joists and piles, locksfoot_build's
staging() vocabulary through boatyard_lib. 2.0 m wide — town_blockout's own stair-landing
pad size, wider than its 1.6 m deck ribbon and no wider. Every number derived: the rect from
the map, the HEIGHT from the deck it continues, the MATERIAL read off that same neighbour,
and only the part not already decked is planked.
    moorage        [75.09..76.89, 27.00..31.30]  7.6 m2  deck z 1.042  material mat_deck
    fish-dock      [58.09..60.09, 26.00..29.60]  6.9 m2  deck z 1.050  material mat_deck
    north-landing  [104.65..106.65, 26.00..28.60] 4.7 m2 deck z -0.950 material lf_deck
    drying-decks   [67.20..68.77, 26.25..26.70]  0.3 m2  deck z 6.719  material lf_deck
20.5 m2 built against 93.5 m2 of river-pad removed. All eleven footprint rects verify
all-landed at 100% (`landing_footprint.py --verify`, new: the cover SEARCHES for rects, this
CHECKS one that is already written down).
Three things the build learned the hard way, each now a rule in the file:
  * THE DECK MUST FIT UNDER THE RIBBON IT CARRIES. Planking at the neighbour's height would
    stand ABOVE the walk record it supports. A bounding box cannot answer this —
    walk_e_moorage__lock-five_l0 slopes 1.07 -> 0.53 and only its high end is over the pier,
    so its bbox would have driven the deck 0.73 m under the pad, out of the landed window.
    Polygons, clipped to the rect.
  * WIDTH IS TRIMMED, NOT AVERAGED. That same ribbon clips the moorage pier's east 0.14 m
    and honouring it at full width put the deck 0.595 m under the pad — inside the 0.60 rule
    by 5 mm, which the planking's own jitter would have spent. Pier is 1.80 m there.
  * A PILE MAY NOT STAND IN A LOWER TIER'S CORRIDOR. The drying decks are 5 m over the fish
    dock's walkway and the first build dropped four piles through it (446 blocked steps on
    walk_e_tenant-shack__fish-dock at z 1.53 — an invisible post in a street). All four are
    refused and the apron is a cantilever; the tool prints each refusal.

=== REACH, AFTER ===
    fish-dock       2054 nodes, in the big component            CONNECTED
    north-landing   6736 nodes, with its ribbons                CONNECTED
    moorage         5736 nodes, in the lock-five component      CONNECTED
    drying-decks    still three islands                         NOT CONNECTED — see below
THE MOORAGE NEEDED A GATE, NOT ONLY A PIER. Its mooring stage is on the river side of
`lf_railings`, the boardwalk guard: the pier reached the network and the stage stayed an
island of 3474 nodes behind 2086 blocked steps of rail. 25 rail faces are cut inside the
pier's own 2.05 m corridor — a boarding opening at a pier, which is what a moorage is for,
and ls_reorigin's rail-gap precedent for how narrowly to cut it.

=== THE DRYING DECKS ARE FENCED BY THEIR OWN DRESSING, AND THIS IS FOR THE ART ROUND ===
Their pad is 6.915 m, so a body on it occupies 7.565..8.215. `t2c_W1_laundry_deckA` runs
z 7.02..8.57 along the whole south edge (y 25.92..26.07, x 61.73..68.93) and
`t2c_WV2_dryingdeck_awning` canopies to z 7.90: walk_bodygate counts 1160 and 1134 blocked
steps. Every ribbon into this landmark arrives from the south. The apron was therefore moved
to the deck's EAST end (nothing hangs over x > 67.60) and it is still not enough, because the
last 0.5 m of the approach ribbon is inside the laundry rig's body column. RECORDED AS
OPEN: the drying decks' own washing is hung across their doorway. The pad's connection
before this lane was 544 nodes of disc hanging over open water, so what changed is not that
they became unreachable — it is that they stopped being reachable by walking on air.

=== GATES ===
  routes --check clean (16 shots) · seam_test 294/0 (+7 soft) · master_walk_qa 22 failures,
  all pre-existing and byte-identical · landing_footprint --verify 11/11 · cine_solve +
  scenegraph re-derived (they were STALE at 960e13b, before this lane: both predate the
  footprint stamp). cine_solve moved exactly two cameras, `weave` (aim y +0.062, dist -0.12)
  and `lockfive` (aim y +0.070, dist -0.08), because a footprint changes a pad's centroid.
  Frustum-affected cameras derived by projecting each landing into every solved frustum:
  gate, crossing, weave, fishdock, lockfive, north-landing. Those six are rebaked; the other
  ten are untouched.
  NOT COMMITTED, DELIBERATELY: public/world/scenegraph.json. Re-deriving it is owed, but its
  ow-valley inputs (world.json, valley.region.json) are another lane's UNCOMMITTED working
  tree right now, and the re-derive picked up a real regression that is theirs to read, not
  mine to ship: portal 'dellhollow-valley-gate' now reports "no walk surface within r of the
  trigger (44.9,-36.2) in 'ow-valley' — the gate may be unreachable on foot" and "region
  spawn (41.3,-33.8) is off the walk network". Restored to HEAD; the re-derive must follow
  the overworld lane's commit.

### THE GATE TIER'S UNUSED APRON, CENSUSED FOR TASK #35 (user ask, same annotated frame)

USER: "Unused space, just chop off to keep the lane narrow, replace with the more-realistic
cliff face?" — the left ellipse of docs/qa/refs/user_gate_tier_annotated.png.

MEASURED, 0.5 m grid over x -2..27.5, y 0.5..15, first hit from z 26.5 counted as tier
ground when it lands above z 23.0, and walkable when a `walk_` record sits within 0.45 m
over it:
    tier ground            1131 cells   282.8 m2
    walkable                356 cells    89.0 m2   (31%)
    UNUSED (no walk record) 775 cells   193.8 m2   (69%)
The walkable 89 m2 is almost all one thing: `walk_lm_porters-yard` holds 195 of the 356
cells, and the rest is `walk_pad_valley-gate` (18) plus the road ribbons
valley-gate__winch-head (51 across nine legs) and valley-gate__porters-yard (8). The lane's
own natural width is town_blockout's road ribbon, 1.6 m, with 2.6 m threshold pads at the
landmarks — so the tier is roughly three times wider than anything that uses it, which is
the user's read, in numbers.
WHAT DEPENDS ON THE GROUND BEING CUT — the point of this census, for whoever cuts it:
  * NOTHING IN THE WALK NETWORK depends on the 193.8 m2, by construction: no walk record
    covers it. The 35 walk_/bar_ records on this tier are listed by the same probe and every
    one of them stands inside the 89 m2 (or on the gate stair below it).
  * CAMERA OWNERSHIP DOES: the `gate` shot owns valley-gate, gatehouse, winch-head,
    porters-yard and their four edges, and this ground is its foreground. Cutting it is a
    plate change for `gate` and needs the shot re-solved (its standoff is fitted to what it
    owns) and rebaked, not just re-rendered.
  * SEAMS DO NOT: the tier's only camera boundary is gate<->shelf-west on valley-gate__inn,
    which runs down the gate stair at x 17.5..19.1, well inside the kept 89 m2.
  * THE PORTERS' YARD PAD IS 8 x 8 m OF FILLED DISC at x 2..10 y 4..12 and it is the single
    biggest walkable thing up here. If the lane is narrowed, that pad is the thing to
    re-measure first — it is the same `area`-landmark shape this lane has just spent the
    night correcting at four other landmarks, and it has never been measured against what is
    built under it.

### THE CHROMA ONE-LINER, OWED SINCE b35e90a

t2_probe_chroma on the master b35e90a shipped, 224-wide ray grid, 28672 rays per camera,
scored against t2_probe_report's own ACCENT_MATS classifier and the pops-of-color [5%, 11%]
band. TOWN MEAN 5.85% (was 3.07% before the build), and 11 of 16 cameras are in band:
    in band   shelf-east 10.23  quay-west 9.23  waterfront 9.03  loop-stairs 7.76
              deep-stairs 7.37  fishdock 7.24  weave 5.94  lockhead 5.68  boatyard 5.67
              shelf-west 5.59  lockfive 5.39
    UNDER     north-landing 4.43  crossing 2.99  cottage-steps 2.90  cottage 2.43
              gate 1.79
THE GATE PLATE IS THE ONE THE CULL PAID FOR AND IT IS THE LOWEST IN THE TOWN. b35e90a
removed four colour panels from the gate yard (t2_gate_declutter: three of them are the
canopies this lane has just found still standing in the collision), and the gate camera now
reads 1.79% against a 5% floor — the six eastern cameras that used to sit at 0.00-0.17% have
been fixed and the gate has gone the other way. It is not a regression in the cull's terms
(each panel was culled for standing over a 31.85 m drop or floating 0.40 m over a walk pad,
and those are the right reasons) but the colour it carried has not been replaced. FOR THE
ART ROUND: the gate is the town's front door and its five under-band cameras are the four
quietest shots plus the entrance. Leak, separately: gate 1.84%, every other camera 0.00%
(boatyard, 1 ray) — the known sky gap of task #36, not a hole.

## THE WORLD-SIDE CHIRALITY FLIP — a sentence that mirrored a town, the crossing it made
## necessary, and the two banks the canyon has to change hands between
## (2026-08-01, overworld lane, user-ratified package)

USER RULING, enacting the diagnostic in commit 0cebd6a (frames
`docs/qa/overworld/chirality_*.png`): Dellhollow AS BUILT is a RIGHT-BANK town facing
downstream — identity transform, det +1.0000, fitted from seven shipped walk pads —
and Emberbrook AS BUILT is LEFT-bank. The world tile MIRRORED Dellhollow so the
geometry could satisfy one sentence in world.json: "the town's mass is on the WEST
bank". THE SENTENCE WAS THE ERROR. The mirror is deleted, the corridor is flipped to
the bank the town actually stands on, and because the two towns are therefore on
OPPOSITE banks, exactly one crossing is forced — the user placed it at the Old Gate
and chose its form: a culverted gate court, no bridge, no span.

=== 1. THE FLIP IS STATED IN THE RIVER'S OWN FRAME, BECAUSE NOTHING ELSE SURVIVES IT
Every feature below the gate was re-stated as (arc length along the river, signed
offset from the channel) and re-emitted on the other side. That pair is the only
description of a corridor feature a chirality flip does not destroy, and TWO WAYS OF
GETTING IT WRONG were measured rather than reasoned about:
 -  A STRAIGHT QUAD CANNOT BE FLIPPED CORNER BY CORNER. Each corner finds its own
    nearest reach, and the quad shears: `farwall` came out with its two river-side
    corners 22u apart in arc that had been 0. The far-side stamps (`farwall`,
    `farwall-crown`, the far-wall crag override) are now BANDS — two offset curves
    from the river's own axis, stated as (arc0, arc1, inner offset, outer offset).
 -  AN OFFSET CURVE FOLDS. The 0.5u-resampled catmull centreline carries radii as
    tight as 5.2u, so a 26u band turns inside out and becomes a self-intersecting
    polygon that every point-in-polygon test answers confidently and wrongly. The
    bands ride a 40u-smoothed AXIS; a simple-polygon test was run on each one before
    it was written. Roads, seats and the gate keep the real channel.
 -  AND REFLECTION IS NOT AN ISOMETRY, WHICH IS WHY THE TOWN WAS NOT REFLECTED.
    Dellhollow's anchor and its Valley Gate stood 4.88u apart before the flip and
    14.5u apart after a naive reflection, because the two offsets sit on opposite
    sides of a bend. The seats were RE-DERIVED instead, by the file's own documented
    method (gate-anchored, 0.2661 u/m along the gorge, across it by ratio of the
    channel's own half-width) with one sign corrected: the far end of the across-ratio
    is the water's edge ON THE TOWN'S OWN BANK. The re-derivation and the reflection
    then AGREE on the anchor to 0.00u, which is the only reason to believe either.

=== 2. THE CANYON HAS TO CHANGE HANDS TOO, AND THAT IS A SECOND WORD IN THE MAP
The first flip carried ONE benchSide down the whole spine, and the far wall's 18-26u
rise landed on the WHISPERWOOD side of the gate. MEASURED on the field, cross-sections
at 5u: at y=48 the ground at x=70 went 25.7 -> 36.7, an 11u ridge through the highland
20u west of Emberbrook, on the bank the village and its arrival road are on. The
region now carries `benchSide: E` and `benchSideAboveCulvert: W`, and valley_map
resolves EACH word twice — the compass word against the river's mean downstream
heading, and the side that reach of road actually runs on — and refuses the build if
any of the four answers disagree. The bench field blends between them over 0.038 of
the downstream parameter, centred on the culvert, which is the one reach in the region
where a cross-channel seam has a wall standing in it. With the second word in place
the upstream cross-sections are byte-identical to the pre-flip tile and h_range came
back to [-6.18, 50.9] from [-6.18, 52.5].

=== 3. THE ROAD CROSSES ONCE, AND THE MAP HAS TO SAY SO OR THE BUILD REFUSES
`road.culvert` is new: id, the point on the channel, the two mouths, the length, and
the two road stations it joins. valley_map now
  -  requires it before it will accept a bank change at all (it used to print a NOTE
     and carry on, which is how a hairpin that swapped 3 of 14 stations lived in a
     shipped map for as long as the map existed),
  -  requires each reach to be internally on ONE bank,
  -  requires the two reaches to be on DIFFERENT banks (a declared crossing that does
     not cross is also a map bug),
  -  and re-derives where the road actually crosses the channel and compares: declared
     [94.63, 76.81], MEASURED [94.63, 77.34], 0.53u apart.
The clearance pass reads the same block: under the court there is no open water, so
those 17 stations are neither pushed nor counted as a span. Pushed stations 0, spans
0, minimum road-to-water slack 3.51u — identical to the pre-flip tile.

=== 4. THE GATE, REWORKED FOR THE CROSSING (user's flavour 1)
The river already passed under this wall through the low grate. The court extends that
grate: the water runs on under stone and comes back to daylight at the SILL, where it
falls. The road comes through the arched doorway on the west bank, crosses on the
paving, and leaves on the east. The ratified vocabulary is intact — ONE wall, arched
road doorway, LOW grate at water level, plain coursed masonry — and the pinch ratio is
re-derived, not copied: doorway centre 2.727 channel half-widths off the centreline.
    COURT LENGTH IS THE TOWN'S OWN RATIO. emberbrook.map.json runs 8.0 m from
    `gate-court` to `sigil-gate` against a 6.95 m grate = 1.151 grate-widths; at the
    world's 2.000-half-width grate that is 5.19u. The build takes the LESSER of that
    and the distance from the wall's outer face (river arc 53.25) to the sill (57.50),
    so the deck can never overhang the lip: 4.25u. Two numbers derived from different
    things, 22% apart, and the smaller one wins by rule rather than by taste.
    THE BITES ARE MEASURED NOW, NOT TYPED. "Built wall-to-wall into living rock" is a
    claim about where the rock IS, and the rock moved: with the east bank become the
    traversable side, the 2.4u bite that used to land in the far wall's own cliff left
    2.25u of open ground and the seal probe counted 131 leaked cells. Each end walks
    out until the ground is rock and then bites 0.9u into it: W 0.90u, E 3.05u.
    THE APRON IS NARROW ON THE COURT. The road grade blends ground to ribbon over
    2.8..8.0u everywhere else; on the culvert it would cut 8u out of the wall's own
    east abutment. On the culvert stations it is 1.2..3.0u, and the gatewall's notch
    yield follows the same rule (2.6..4.6 -> 1.2..2.4). A gate court is masonry laid
    between rock, not a graded verge.
    THE DECK IS AS WIDE AS THE HOLLOW IT COVERS, AND THE HOLLOW IS MEASURED. Laid
    rock-to-rock at one level it was half buried and half floating — a row of stone
    shelves jutting out of a cliff, which is what the first render showed. It now walks
    out from the channel each way and stops where the ground comes up to the paving:
    offsets -5.30 to +6.80 of a 17.50u notch.
    THE SEAL, RE-PRINTED: notch 17.50u rock-to-rock (pinch 13.55u unchanged), doorway
    2.727 half-widths, founded 2.30u, strip masonry->rock W 0.00u E 0.00u, flood fill
    past the pinch 0 cells. The flood fill is a TERRAIN question and the court deck is
    a prop, which is correct and worth stating: the probe asks whether there is a way
    ROUND the wall over ground the gate does not cover. The way THROUGH is the road.

=== 5. THE RIVER'S GROWTH, MADE LEGIBLE — and the measurement says what is not there
Instrument: `tools/valley_tribprobe.py`, re-runnable — D8 steepest-descent flow
accumulation over the BUILT natural field, outlets taken in the band hw+1.5..hw+6 off
the channel, binned by river arc, strongest per bin per bank, then traced back uphill
along the strongest contributing neighbour. Two are stamped into
`region.tributaries`, both FOUND:
    gatefoot-ravine     mouth [91.2, 86.4]   accumulation 24   31.6u long, falls 25.4u
    hollowmere-outlet   mouth [192.0,168.0]  accumulation 151  41.4u long, falls 50.3u
THE NEGATIVE RESULT IS THE MORE USEFUL HALF: on the BENCH bank every arc bin in the
corridor scores accumulation 1-5 against 24-151 on the far bank, because the bench is
a graded shelf and a graded shelf has no ravines. So both visible tributaries are on
the FAR wall, seen from the road across the water — which is also what makes the far
wall read as country rather than as a backdrop. HOLLOWMERE'S OUTLET DOES NOT USE
HOLLOWMERE PASS, 52u west of it: a pass is a dry saddle you walk over and an outlet is
the gorge the water cut, and the terrain puts them in different places. It arrives 14u
above the water and finishes as a fall down the far wall, which is one of the two
reasons the river below it is navigable and above it is not.
THE OTHER REASON IS NOW CANON, in world.json's own `_doc`: the gorge carries the whole
EAST DRAINAGE OF THE MASSIF, and below Dellhollow the LONG REACH is the DAM'S
IMPOUNDMENT — 12u of river becomes 18u at the Moorage because the weir and locks hold
it back, not because a river widens on its own. Two sentences, per the documentation
bar.

=== 6. THREE THINGS THE FLIP FOUND THAT WERE NOT THE FLIP'S FAULT
 1  THE HOLLOWMERE PASS NOTCH WAS CUT IN THE WRONG RIDGE, and had been since the
    restamp. `valley_map` notched `R_s` — the SOUTH rim — with a comment reading "v2:
    the sealed pass moved to the SOUTH rim (the reachable bank)", while world.json has
    had the exit at [146, 190] on the NORTH rim since 2026-08-01. So the south ridge
    carried a 55% notch at x=146 that nothing uses and the north rim that actually
    holds the pass stood full height across it. It now picks the ridge whose own blob
    the exit stands in and prints which one it chose: `northwall, 0.0u from its blob`.
    A notch in the wrong ridge is invisible in every render that does not look at both.
 2  THE GORGE'S DEPTH WAS READING THE TOWN'S CENTROID. `GORGE_RIM` took the Dellhollow
    ANCHOR's z with the comment "the rim the gate stands on" — two different dots that
    agreed only by accident, because the anchor used to sit 4.88u from the road's end,
    INSIDE the Valley Gate apron shelf that the build pins to the road's own z. Its
    12.0 had therefore never been tested against the ground. The flip moved the anchor
    14.5u out of that apron and the same 12.0 measured 6.10 in the field — and the
    gorge cut, still reading it, would have gone 14.0 -> 7.05 and quietly halved the
    canyon Dellhollow exists for. GORGE_RIM is the Valley Gate portal's z now, by
    definition and by its own map note; cut stays 14.0.
 3  ...AND THE ANCHOR'S OWN HEIGHT WAS WRONG, so it is derived now. dellhollow.map.json
    puts its settled centroid 10.36 m above its own water and its Valley Gate 24.0 m
    above it; the ratified gate seat stands 7.61u above the water of its reach, so the
    VERTICAL scale that seat implies is 0.3170 u/m against the along-gorge 0.2661
    (119% — the gorge is steeper than it is long, which is what a gorge is). The anchor
    is 1.77 + 10.36 x 0.3170 = 5.06. The field reads 6.10 there: a +1.04u residual,
    REPORTED, against the -5.90u the old 12.0 was carrying.

=== 7. WHAT MOVED, IN NUMBERS
    benchSide                 W -> E below the culvert; W above it (new second word)
    road                      19 -> 20 control points; 0..8 unchanged (the west-bank
                              approach), 9 on the court, 10..19 on the east bench
    dellhollow anchor         [184.13,157.40,12.0] -> [196.46,144.87,5.06]
    dellhollow-valley-gate    [180,160,12.0]       -> [184.88,136.19,12.01]
    dellhollow-moorage        [188.23,161.60,1.3]  -> [200.96,152.87,1.3]
    waystone                  [89.25,87.00,23.65]  -> re-snapped ON the new ribbon,
                              [103.52,82.53,23.07] (0.53u from its reflected position)
    farwall / farwall-crown / far-wall crag / bench-fringe / pocket-grove / the
    Dellhollow rim crag / the shelf pocket / the shelf overrun / four floor controls:
                              all re-emitted on the far side in the river's frame
    zone coverage             meadow 53.83 -> 56.83, forest 13.97 -> 13.30,
                              crag 24.17 -> 21.94, road 1.65 -> 1.59, water 6.38 -> 6.34
    tris                      167 397 -> 150 832 (the far wall's crag band is narrower
                              on the NW side, where the tile leaves it less room)

=== 8. GATES
    worldmap_validate                 PASSED, 0 errors 0 warnings
    valley_crosscheck                 84 assertions, 0 failed  (see below)
    valley_verify                     OK — ribbons unpierced (worst -0.035u), the
                                      Dellhollow anchor reads 'road' not water, the
                                      waystone reads 'road', both crag stamps 100%
    seam_test                         294/0 (7 soft warnings, pre-existing)
    seam_walk                         9/9
    slice_test                        671/15, ZERO ow-valley — the 15 are emb-cine's
                                      and match the pre-flip baseline exactly
    road clearance                    0 pushed, 0 spans, min slack 3.51u
    OLD GATE SEAL                     strips 0.00 / 0.00, flood fill 0 cells
    EMBER FALLS                       lip re-found at arc 57.5 (t 0.227), 5.65u of free
                                      water over 1.50u of run — the found-lip survives
                                      the re-carve, which is what it was built to do

THE CROSSCHECK NOW LIVES IN tools/. The previous generation of it (52 assertions) was
a scratch file and is gone; a check that can evaporate is not a check. `tools/
valley_crosscheck.py` is 84 assertions across world.json, the region, and both town
maps, and it is written so that where a file NAMES a bank, an assertion can fail on
it. Every bank assertion below the gate was inverted in the same commit as the
sentence it checks, and the byte-canon line — `crossings._doc`, "NONE — and none
possible..." — is asserted byte-for-byte and is untouched.

FIVE ASSERTIONS WERE AMENDED RATHER THAN INVERTED, and the reasons are the point:
 -  "width grows monotonically down the spine" was FALSE and always had been: the spine
    narrows 4.6 -> 4.5 at the notch, which is the pinch the gate stands in. Replaced by
    "the river narrows in exactly ONE place, and it is the notch".
 -  "Ember Falls is not called the source anywhere" failed on the note that CORRECTS
    that misreading. A string search cannot tell a claim from its retraction; the
    assertion now checks for the retraction.
 -  "the refined course refines the spine" was measuring point-to-point where
    worldmap_validate measures point-to-SEGMENT; two instruments, two answers, and the
    looser one was mine. Now segment distance: worst drift 3.11u against a tolerance
    of 8.
 -  "road._doc no longer claims it never crosses" failed because the new text QUOTES
    the old claim while correcting it. It now asserts the phrase appears exactly once
    and that "the old text" appears with it.
 -  the doorway ratio holds to 2.0%, not 2%: world 2.782 half-widths against the town's
    2.727. The two half-widths are the SPINE's interpolated width at the gate and the
    refined course's width there — so 2% IS the agreement between two derivations, not
    slop, and the bound is 3% with that stated in the message.

=== 9. STANDING, MEASURED, NOT FIXED
 -  DELLHOLLOW'S ANCHOR READS 6.10 AGAINST A DERIVED 5.06 (+1.04u). Reported, not
    buried; it is the bank slope between the road and the water, and the town's mass is
    placed per-station on the river's own curve, not from the anchor.
 -  THE SHELF IS STILL A ROAD ON A CREST WITH A TROUGH BEHIND IT, not a ledge against a
    wall. The asBuilt block records the pre-flip measurement and it is not re-measured
    here; the open taste question for the user is unchanged.
 -  HOLLOWMERE PASS IS NOW ACROSS THE WATER. It was a sealed future hook on what the
    file called "the reachable left-bank side"; with the bench on the east bank it is
    on the far rim, in the same unreachable wall-and-rim country as farPlateau. The
    sentence is corrected and the seat is not moved — moving a ratified world landmark
    is not this lane's call. FLAGGED FOR THE USER: a later chapter that wants
    Hollowmere now needs a way across, and the only crossings in the world are this
    gate court and Dellhollow's barred dam crest.
 -  NO PERCEPTUAL SCORING. GEMINI is live but the judge tooling does not reach rt
    regions, so every number above is an instrument reading. Deferred for the board:
    whether the crossing READS as a crossing at walker's eye, whether the two found
    tributaries read as water or as blue seams on a cliff, and whether the corridor
    still reads bounded now that the rock is on the traveller's other hand.

=== 9b. THE RENDER SET, AND WHAT IT SHOWS
`docs/qa/overworld/chirality_plan.png` is the PROOF FRAME and it is the same script
that produced the diagnostic in 0cebd6a: both towns now read "tile: X bank  built: X
bank  AGREE" where Dellhollow read "tile: LEFT  built: RIGHT  MIRRORED". The culvert
court is ringed, the two found tributaries are drawn.
A NEW SEAT, `valley_court`, was added for this lane and it is aimed at
`road.culvert.at` rather than at a typed coordinate: the east bench looking back up
at the crossing. Its clear_eye probe reports `first hit oldgate`, i.e. the structure
IS what the camera sees.
`valley_falls` is the frame that reads best: the water comes back to daylight at the
sill and falls, with the court's parapet as the stonework across the gorge head and
the road on the east bank descending on the frame's left.
HONEST NOTE ON `valley_gate` AND `valley_court`: at region scale the gate block reads
as coursed masonry in a notch, and from a walker's eye the arch ring and the courses
read as slabs rather than as an arch. That is a perception, not a measurement, and it
is the deferred question this lane cannot answer without a judge. What IS measured is
that the seal closes, the deck covers the hollow it has to and no more, and the road
crosses on it.

=== 10. THE EMBERBROOK STAMP, PROPOSED (not applied — town maps are not this lane's)
The culvert court touches the town's own gate-court area (the round-4 secluded gate),
so emberbrook.map.json wants three things. THE WORLD TILE DOES NOT WAIT ON THEM: what
had to agree tonight is the map data and the world tile's gate-court arrangement, and
the town's 3D build of the apron rides with the dressing passes.

 A. THE COURT IS ALREADY THE RIGHT LENGTH AND ON THE WRONG SIDE. `gate-court` [78,122]
    to `sigil-gate` [78,130] is 8.0 m, which against the town's 6.95 m grate is the
    1.151 grate-widths the world court was seated from — the two maps already agree on
    the RATIO. But the town's court is BEFORE the gate and the crossing is BEHIND it:
    the traveller comes through the doorway and finds the paving. PROPOSED: a second
    flag-stoned court on the valley side of `sigil-gate`, 8.0 m along the channel, its
    paving carried across the water from the doorway's threshold to the far kerb —
    the same object the world tile builds, at the town's own scale.
 B. THE CROSSING NOTE, and it re-opens a ruling. `downstream-vista` [110,140] carries
    a stamped 2026-08-01 round-3 note: "this is PURE VISTA. It is seen from the GATE
    SIDE, across the water, and is NEVER reached. There is no bridge anywhere in this
    map and none..." THE FIRST HALF IS NOW FALSE AND THE SECOND HALF IS STILL TRUE:
    past the Old Gate the road crosses on the court and the far bank IS where it goes,
    and there is still no bridge, because the water is under stone. That sentence is
    the coordinator's to re-rule, and it should be re-ruled deliberately rather than
    left to contradict the world map. The world file's own wording is in
    `road.culvert.note` and world.json's `old-gate` note if it is useful as a model.
 C. NO BROOK-COURSE AMENDMENT IS NEEDED, and that is a measurement, not an omission.
    `brook-mouth` [103, 53.6] puts the village brook into the river 76 m south of the
    sigil gate, on the town's own east side; the culvert covers the channel only from
    the gate northward, so the brook's confluence is nowhere near it. `brook-bridge`
    [76, 52] stays the only thing in the town called a bridge, and it steps over the
    brook, not the river — valley_crosscheck asserts exactly that.

## THE SHELF'S BACK WALL HAS NO DISTANCE BOUND — found by asking whether one stale
## render frame mattered, and the honest answer was "measure it, do not reason about it"
## (2026-08-01, overworld lane, chirality-flip closeout)

ONE FRAME IN THE COMMITTED SET, `valley_vistaring.png`, came from the FIRST post-flip
build — before `benchSideAboveCulvert` existed. Every other frame was re-rendered
after. The obvious reasoning was: that shot stands at [222,100] and looks EAST, the
handover is at the gate 130u away, so it cannot matter. THE OBVIOUS REASONING WAS
WRONG, and the only reason we know is that it was measured instead
(`tools/valley_fielddelta.py`, re-runnable: build the field twice, once as shipped and
once with the upstream bench forced to the downstream side, and difference them).

    control, two IDENTICAL builds          max |dH| 0.0000u   (so the field is
                                           deterministic and the delta below is real)
    handover on/off, WHOLE TILE            max |dH| 21.04u, 4015 cells over 0.05u
    ...inside the vistaring footprint      max |dH| 17.57u, 250 cells over 0.05u
    the moved cells                        x 218..261, y 11..35 — the tile's far
                                           SOUTH-EAST corner
    floor calibration a_prof               IDENTICAL both ways (so it is NOT the
                                           global fit coupling the tile, which was
                                           the first hypothesis and it was wrong too)
    emberbrook / moorage / vistaring eye / long-reach corner:  delta +0.00 at all four

WHY THE CORNER MOVES, MEASURED. Those cells sit 113..156u from the channel, and their
NEAREST REACH is the river's source (t = 0.000), so the handover assigns them the
UPSTREAM bench word. At that range the canyon's own terms are already switched off —
`cw = 1 - sstep(30, 46, dr)` evaluates to 0.0000 there. The only term still live is
the shelf's back wall:

    wallw = sstep(shw_l, shw_l+4, drd_sh) * sideB * after_gate
            * sstep(2.0, 6.0, dr - hw) * (1 - wa)

and EVERY factor in it saturates to 1 at distance. It has no distance bound at all.
So `sideB` alone decides whether a 22u back wall stands 150u from the road, in a
corner of the tile with no road, no landmark and no portal on it.

WHAT THIS IS AND IS NOT. It is PRE-EXISTING — the term is untouched by this lane, and
before the flip the same unbounded factor simply happened to resolve the same way on
both sides of the gate. It is NOT a corridor defect: every probe that matters
(Emberbrook, the Moorage, the vistaring eye itself, the Long Reach control) reads
identical to 0.00u. It is NOT fixed here either: the lane is closed and a terrain
change would invalidate a tile that is already committed, verified and rendered.
LOGGED FOR THE LEDGER: `wallw` wants the same `cw`-style fade the canyon terms have,
and the fix should be measured against these numbers.

AND THE FRAME ITSELF: `valley_vistaring.png` STAYS PINNED TO THE EARLIER BUILD and is
marked here rather than silently re-annotated as current — the against-superseded-bake
rule the redteam lane wrote, applied to its own author. Re-rendering it needs a quiet
box (the shot was starved to 0.3% CPU against 13 concurrent Blenders and abandoned
twice), so it rides with whoever runs the quiet-box transition_test.

## CHAPTER ONE, WALKED AGAINST THE RATIFIED TOWN — 29 beats, and the four places the
## script and the map disagree (2026-08-01, story-staging lane, audit only)

`docs/plans/ch1-staging-audit.md`. Every beat, scene direction and speaker in
`public/js/chapter1.js` (1040 lines) placed on `emberbrook.map.json` at HEAD: where it
stages, who plays it, how the player reaches it, what it contradicts. NOTHING WAS CHANGED —
story, map, npcs.json and dialogue.json were read-only for the whole pass.

    29 beats     20 staged clean · 5 gaps · 4 conflicts · 7 story questions
    proposals    11 map stamps (coordinator) · 9 NPC/dialogue gaps (liveliness lane)

THE FACT THAT COLOURS THE TABLE: `public/game/npcs.json` holds 13 records and every one is
Dellhollow; `dialogue.json`'s speaker table and all ~60 nodes likewise. **Emberbrook has
zero NPC records and zero dialogue nodes** — its entire Ch. 1 cast exists only as
hard-coded entities inside chapter1.js's 2-D Field scenes. So the table scores WHERE and
ROUTE, and names the map post each beat needs, rather than printing "cast: MISSING"
twenty times.

THE FOUR CONFLICTS, each a ratified fact the script walks into:
 -  FINN IS POSTED IN THE WRONG PLACE, TWICE. The map lists him in `square-plaza.residents`;
    the script posts him at the pond and has him say so. And with the square->lane exit
    disabled for the whole Vesper phase, VESPER CAN NEVER REACH HIM — his entire
    Vesper-facing branch, including the circling fish STORY.md §3 calls the only warning
    anyone got, is unreachable in the shipped script.
 -  LAKE'S DOOR DOES NOT OPEN ON THE POND LANE. ch1's cottage interior exits onto `lane`;
    the map has lake-home at x=34 and the pond at x=92 — 58 m, opposite sides of the
    village — so Act II now opens by crossing the festival square to reach the low ground
    the round starts at. `emberbrook-town.md` §7 item 4, still open, now with the 2x
    distance attached.
 -  THE GATE REFUSES YOU AT THE WRONG THRESHOLD. ch1 denies at the square's north exit;
    that exit is now the North Lane with the tithe barn on it, and the gate is 87.1 m away
    past 41.1 m of quiet road the seclusion round was built to make you walk.
 -  THE ENDING NEEDS GROUND THAT IS STAMPED NOT TO EXIST. The notch is sealed to 0.00 m
    both flanks and 0 m2 of reachable gorge; playEnding steps both keepers THROUGH the
    open arch and holds a camera up the road beyond. Either opening the gate mints a
    walkable stub or the chapter ends on a cut. User's call (Q3).

THE FIVE GAPS: the game's OPENING SCENE has no camera and no route entry (p-woodroad
exists; cameras.json and routes.json carry the same six shots and none of them is the
wood); Poppy's stall — the object her post-Hush recovery is built on — is not on the map;
which THREE of the fourteen lamps are dark on Emberwake is nowhere stamped (chapter1.js
names lamp1..3, emb_blockout numbers 00..13, nothing ties them); the Hush state pair is
still unbuilt and is now town-wide (14 lamps + Heartlight + grade), not a second PNG; and
THE SIGIL PLATES ARE NOT LANDMARKS — the chapter's co-op set piece exists only as a
sentence inside `sigil-gate`'s own note ("built as separate props").

TWO FINDINGS THE AUDIT TURNED UP THAT ARE NOT ABOUT CHAPTER ONE AT ALL:
 -  21 of 42 landmarks belong to NO PARCEL — including `bakery`, `festival-dais` and
    `village-bell`, all three direct Ch. 1 staging. A parcel derives the scene contract and
    the sceneKey, so a beat staged on an unparcelled landmark has no scene.
 -  SIX LANDMARKS CARRY `district: "lane"` AND THE DISTRICT'S ID IS `"lanes"`
    (brook-bridge, brook-mouth, east-cottages, pond-weir, pips-den, smokehouse). Any tool
    that groups by district drops all six silently — the same shape as the seclusion
    round's own district filter that failed closed.

WHAT WAS BETTER THAN EXPECTED, recorded so nobody re-commissions it: every one of the 18
expressions chapter1.js calls ALREADY EXISTS ON DISK for the whole cast, and `emb-lake-int`
is not just built but semantically right — its `doors.json` names `walk_pad_hearth` as
"the mantel, the hook, the portrait" and `walk_pad_table` as grandmother's table, which are
beats 13 and 14 verbatim. Missing bodies are rowan, poppy, mochi — and LAKE, who is player
two and has no entry in play3d's MODELS registry.

---

## 2026-08-01 — LIVELINESS: every person is a body, every speaker has a face, and Emberbrook gets its first cast

Three user rulings from tonight's play session, run as one data lane (npcs.json,
dialogue.json, generated busts; no Blender, no town masters, no play3d.html).

**1. THE BILLBOARDS ARE GONE.** Ruling: *"swap those all out for the existing 3D models,
even if we have to reuse them a bunch of times."* Six human plates remained in Dellhollow
(odessa, pell, sorrel, creel, boatwright, and mochi); five now wear one of the four rigged
GLBs. Measured before/after in `del-cine`: **14 models + 1 billboard, from 4 models + 6
billboards.** Reuse counts across both towns: finn ×10, mara ×7, maren ×6, pip ×5. The
variation is `body.tint` and `body.h` and nothing else — heights now span 1.01 (the
washline grandmother) to 1.13 (Odessa), where before every rigged adult was 1.10.

**THE CATS ARE THE EXCEPTION AND IT IS DELIBERATE.** Two billboards survive — `mochi` at
Dellhollow's eel stall and `mochi-emb` at the Emberbrook waystone. There is no quadruped
GLB; a biped scaled to 0.30 charH is a tiny person, not a cat, which is a worse defect than
the plate. Coordinator ratified. `tools/dialogue_test.mjs` allow-lists exactly those two ids
and fails on a third.

**MEASURED FAILURE, FOUND BY THE SCREENSHOT AND NOT BY THE FILE:** emb.miller and
emb.neighbour were authored as the same model (finn) in near-identical greens, 8.5 m apart
on Home Row — and Home Row puts both in ONE frame. They read as one figure pasted twice.
Tint and height were not enough at that distance; the fix was a different model (the miller
is now a woman). Recorded in her `bodyNote` because the next person to add two villagers to
one lane will make the same call.

**2. EVERY SPEAKER HAS A FACE.** Ruling: *"every time you speak to somebody, they should
have an appropriate character bust."* Before: 2 of 14 speakers (Odessa, Maren). After:
**33 of 33**, and `portrait: false` survives for exactly one id — `system`, the narrator
channel, which is a typographic mark and not a person.
 -  17 busts generated by `tools/gen-character.mjs` (~$0.66): the ten Dellhollow extras the
    chapter-2 script called "nameplate-only" (hobb, pell, sorrel, creel, nib, eelwife,
    boatwright, chandler, weaponsmith, armorer) and **seven ARCHETYPES** for background
    villagers (villager-woman, villager-man, elder-woman, fisher, child-girl, child-boy,
    innkeeper). An archetype is borrowed art worn as somebody else's coat, exactly the way
    the four GLBs are — the archetype id in dialogue.json's `portrait` column IS the record
    of the loan. Nothing was regenerated: all 18 expressions chapter1.js calls were already
    on disk (the audit said so, and it was right).
 -  `--only key,bust` added to gen-character.mjs. A background villager needs a face and
    nothing else: he already has a body, so the sprite sheet has no consumer, and
    dialogue.js falls back to the neutral bust for every mood. Two images instead of eight.
 -  **A BUSTLESS SPEAKER IS NOW A FAILING BUILD**, not a blank frame: `tools/dialogue_test.mjs`
    (785 assertions, no deps, no browser). Both halves of the ruling are data facts that fail
    SILENTLY at runtime — dialogue.js keeps talking without art by design, npc.js logs one
    line and leaves a blob shadow standing in the street — so the ruling got an instrument
    instead of a note. Negative-tested: flipping one speaker to `portrait:false` fails 2
    assertions and exits 1.

**3. EMBERBROOK HAS A CAST AT ALL.** Before tonight `npcs.json` held 13 records and every
one was Dellhollow; Chapter One's whole cast existed only as hard-coded 2-D entities inside
chapter1.js. Emberbrook now has **13 records** (5 named + 7 background + the cat) and
Dellhollow **18** (+5 background). Both towns' new posts are vertices of the town's own
derived walk network, and every one was probed against the shipped `scene.glb` for a walk
surface under it and a prop through it BEFORE it was authored. Three of the audit's own
posts moved, each for a measured reason recorded in the record's `note`:
 -  **rowan** — the audit's `festival-dais` (60.4, 40.4) is the deck's centre;
    `lm_festival-dais_deck` has NO walk mesh, so that post is a man standing on scenery the
    player cannot reach. Moved 0.6 m to the plaza at the deck's square-facing edge.
 -  **poppy**, **mara** — the bakery landmark is the building centre (no walk surface) and
    square-plaza is the Heartlight's own plinth (x[62.85..65.15] z[-45.15..-42.85]). Both
    moved to the nearest network vertex clear of the solid.
 -  **finn stands at the POND, and that is parked, not decided.** The map lists him under
    `square-plaza.residents`; chapter1.js posts him at the pond; the audit raises it as one
    of the seven user questions. He is at the pond because the script is shipped content and
    the residents line is older, his smokehouse is 7 m up the shore — and reversing it is one
    `position` line.

**SCENE KEY, MEASURED:** Emberbrook villagers list `emb-townwalk` ALONE. `emb-walk` and
`emb-cine` are the pre-2x world (walk bbox x[13.9..53.0] vs the map's x[23.9..104.5]), so a
routes coordinate placed in `emb-cine` lands outside the geometry. `emberbrook.map.json`'s
`walkSceneKey`/`playSceneKey` and `routes.json`'s `appliesTo` all still name the stale
bundles — coordinator's to correct. The day `emb-cine` is re-baked, adding it to each
record's scene list is one edit and the same coordinates hold.

**INN AND STORE: GREETING ONLY, NO COUNTER.** `emb.innkeep` and `emb.shopkeep` exist and
talk, and neither carries a `shop` field, because the audit's Q1 asks the user whether
either trades on Emberwake night and MECHANICS.md says the festival runs on gifts BY LAW.
The day Q1 answers, `shop` is one field. Both carry TITLE nameplates and no proper noun —
the map calls them `innkeep` and `shopkeep`, and inventing names for them is not this
lane's call.

Gauntlet: dialogue_test 785/0 · economy_test 204/0 · slice_test 671/15 — **all 15 failures
are `emb-cine`'s stale bundle and pre-date this lane** (they are the same 2x mismatch above;
nothing here is read by slice_test). Verified in a real browser at every scene touched.

STILL OUTSTANDING, for whoever owns them: GLBs for rowan, poppy, a CAT, and **lake** (player
two, absent from play3d's MODELS registry — coordinator's file). And the 2-D legacy path:
`public/js/assets.js`'s `EXPRESSIONS` map is what preloads HD busts there, and chapter2.js
speaks as hobb/pell/sorrel/creel/nib — all five now have `bust.png` on disk and would light
up by adding five empty-array entries to that map. Not done here; it is not this lane's file.

### 2026-08-01, later — the door-7 geometry "leak" is not a leak, and the three villagers standing in doorways are

The quiet-box `transition_test` reported `del-cine|shelf-west` +510 geometries on the
door-7 revisit, new tonight, correlating with del-cine going 4 -> 14 rigged models.
It is not an npc.js disposal failure. **Nothing in npc.js was changed**, because
measuring it first said there was nothing to change — and the measurement found a
different, real defect that WAS this lane's.

**THE INSTRUMENT** (scratchpad replay, `SIM.door()` down transition_test's own itinerary,
hooking `cineApply` to log every shot applied per scene epoch, plus an orphan census —
`scene.traverse` geometry identities vs `renderer.info.memory.geometries`):

| arrival at del-cine\|shelf-west | geo | cineArt cache | **shots applied this epoch** | npcGeo | liveGeo |
|---|---|---|---|---|---|
| door 1 (from the inn) | 626 | shelf-west, gate, shelf-east | `shelf-west` | 30 | 2524 |
| door 3 (from the item shop) | 626 | shelf-west, gate, shelf-east | `shelf-west` | 30 | 2524 |
| **door 7 (from the weapon shop)** | **1136** | + **loop-stairs** | **`shelf-east` THEN `shelf-west`** | **30** | **2524** |

`npcGeo` — every geometry under `Npc.group` — is **30 in all three**, and `models:14,
missing:0` in all three. Nothing the module builds is duplicated and nothing it drops is
retained. The +510 is the town's own geometry, uploaded because **two shots rendered
instead of one**: `renderer.info` counts a geometry from its first draw, and
transition_test's per-(scene,shot) baseline has no way to say "arrived VIA a correction".

**WHY TWO SHOTS.** `del-weapon-int>del-cine@weapon-shop` spawns the player at
`[35.274, 19.07, -6.925]` with `cam: shelf-east`. The shelf-west<->shelf-east cut band is
centred `[35.144, 19.07, -6.998]`, width **1.9 m**. The arrival is **0.15 m** from the band
centre — the player materialises INSIDE the cut, so the edge applies shelf-east and
`sgTick` immediately corrects to shelf-west. A seam-canon arrival defect
(`public/world/scenegraph.json`, derived — coordinator's), not a population one.

**PROOF IT IS NOT THIS LANE'S**, and the reason to trust the paragraph above: the same
replay run against the PRE-LANE `npcs.json` (13 records, 4 models) applies the same two
shots in the same order — `shelf-east@geo153` then `shelf-west@geo1058` — gains the same
`loop-stairs` cache entry, and carries the same **+510**. The only difference the lane
makes is `npcGeo` 20 -> 30: **ten geometries.** The lane made the failure VISIBLE (14 GLB
loads hold `Npc.ready()`, which gates the test's readiness wait, long enough for the
correction to land before the probe reads) — it did not cause it.

**WHAT THE PASS DID FIND, and it is worse than the thing it was sent to look at.**
Sweeping every post against every `spawn` in `scenegraph.json` — doors, seams AND camera
cuts — **three of the five villagers added tonight were standing on an arrival point**:

| villager | was | clearance | took by |
|---|---|---|---|
| `del.deckhand` | 32.60 / -8.13 | **0.09 m** | shelf-east>shelf-west cut spawn |
| `del.gullgirl` | 43.65 / -11.50 | **0.39 m** (2.2 m errand) | the cookhouse door |
| `del.stairgran` | 55.90 / -9.00 | **0.43 m** | quay-west>loop-stairs cut spawn |
| `mochi` (PRE-EXISTING) | 49.10 / -28.20 | **-0.19 m** (0.9 m errand) | waterfront>fishdock cut spawn |

The player materialised inside them. **The trap is that every one of those posts was
chosen for a good reason** — a landing, a doorstep, a cut point are the legible,
well-composed places a person belongs, which is exactly why the camera layer already
claimed them. All four moved, each note recording which spawn took the post and what the
clearance became; the cat's move puts him 1.63 m from the eel-wife, which is the first
time that record has actually put him AT the stall his line is about.

**AND THE FIX MADE THE SAME MISTAKE ONE LAYER OVER**, which is the part worth keeping.
The deckhand moved to 30.30 / -8.90 — 2.37 m clear of every spawn — and landed **0.32 m
inside the chandlery's door TRIGGER** (r 1.8). There are two kinds of claimed ground: a
`spawn` is where the player appears, an `at`+`r` is the circle he stands in to take the
door, and a villager may own neither. He is now at 41.05 / -6.40, on the one stretch of
shelf street with no door of its own: 2.72 m clear of every arrival, 0.77 m outside every
trigger at full wander.

Now a gate, not a memory: `tools/dialogue_test.mjs` §6 measures every post against every
arrival spawn AND every trigger circle of every scene it lives in, **minus the wander
radius** (clearance has to survive the errand, not just the post) — under 1.0 m from a
spawn fails, inside a trigger at all fails. It found the cat by itself. 827 assertions, 0
failed. `_posts` in npcs.json states the rule.

**STILL RED AND NOT OURS:** door 7's GPU assertion and its `every repeated (scene, shot)`
sibling, both from the shelf-east arrival above — one spawn move in the derive fixes both.
Music drift 71.989s is the loop-wrap instrument bug already filed (task #36).

## plate_flat NOW EXCLUDES THE SKY — the world background and a backdrop card carry the
## same signature by construction, and only a ray separates them
## (2026-08-01, instrument-amendment batch, tools/plate_flat.py)

The screen flagged `del-cine gate` at 1.75%, RGB 155,91,61 — byte-for-byte the colour of
the Crossing's documented backdrop card. It is the SKY (the gate re-aim is the first
Dellhollow frame in the town's life with sky in it). The collision is structural, not a
tuning error: cine_bake deletes the volume objects before the DEPTH pass, so a card and
open sky both read "constant colour at the far plane" and the two plates cannot tell them
apart. A ray can — a card is geometry merely absent from the depth pass; sky is the
absence of geometry.

MEASURED with the amended tool's own `sky_census` (800 rays, `sc.ray_cast` on the
evaluated depsgraph of tools/blends/dellhollow-master.blend, `hide_render` honoured so the
census sees the RENDER's object set, not the viewport's):

    gate, the flagged band's own pixel mask     773/800 miss = 96.6%  -> SKY
      (same band by bounding box: 722/800 = 90.25%; the seam lane's independent bbox
       census the same night: 706/800 = 88.25%)
    crossing, the documented card box, with       0/800 miss =  0.00% -> CARD
      fx_haze_east restored to render-visible     (800/800 hit `fx_haze_east`)

0% against 88–96% is an 88-point gap and the threshold only has to land inside it.
`SKY_MISS_FRAC = 0.75`. Deliberately NOT 0.90: the sky's own number moves 88.25 -> 96.6 on
nothing but how the region is sampled, so a 0.90 gate would be an artefact of the sampler.

THE REGRESSION IS THE POINT — an amendment that stops catching its own defect class is
worse than the bug. The full 16-plate sweep before and after differs in exactly two lines,
the gate row and the summary; `crossing  0.00%  RGB 6,3,3  x -0.69..-0.65 y 0.55..0.56` is
byte-identical in both, and the card itself, put back render-visible, still returns
"VOLUME RENDERED AS A CARD" through the same code path the sweep calls. FAILS CLOSED: no
Blender, no blend, or no camera spec (every tools/depth_bake.py interior bundle) => no
census => still flagged, marked "flagged unexamined" — del-inn-int's pre-existing 17.55%
is untouched. And sky is still PRINTED, with its census attached, never silently dropped:
an exclusion nobody can see reads exactly like a screen that stopped working.

## GATE ROUND 2 — "OBJECT COORDS ARE METRES" WAS FALSE, and it cost the mill its stone,
## its boards and its launder (2026-08-01, dressing pilot lane, round 3)

GATE VERDICT round 2: NOT PASSED. Ground accepted at the bar; the BUILT STRUCTURES failed on
five redlines. Everything below was NAMED with an instrument before anything was changed —
a per-screen-sample ray census through the pilot's own cameras (marching past any hit whose
object has `hide_render` set) plus a false-colour ID map.

WHAT WAS IN THE FRAME, NAMED. Frame a: `emb_dress_mill_gable+1` 4.2%, `emb_dress_mill_lucam`
1.9%, `emb_dress_mill_roofdeck+-1`, `emb_dress_mill_door` — the gable barge-boards, the
lucam, the roof deck and the door. Frame b adds `emb_dress_buckA/B**` (the wheel's bucket
boards) and `emb_dress_leat_floor/wl/wr/nose` (the launder). The pit: `emb_dress_pit+-1` and
`emb_dress_mill_foot`. The ground ribbons: `walk_*` via `emb_dress_lane`.

TWO ROOT CAUSES, AND THE SECOND ONE IS THE ENTRY WORTH KEEPING.
  (1) `PLANK` RESOLVED TO DELLHOLLOW'S PAINTED WEATHERBOARD. `M('mat_wallwood', ...)`
  returns the APPENDED material when one exists, and Dellhollow's is a blue-green limewashed
  cottage board. Right on a cottage; wrong on every board a working mill has, which is what
  the gate saw "all over the build". The mill's boarding is now `emb_dress_boarding`, built
  here from the probe's own warm brown with a sawn grain.
  (2) **"OBJECT COORDINATES ARE METRES" IS FALSE FOR EVERYTHING THIS FILE BUILDS, AND THE
  COMMENT ASSERTING IT WAS WRONG IN THE SOURCE FOR TWO ROUNDS.** `box()`/`cyl()` build every
  primitive by SCALING A UNIT TEMPLATE, so object coordinates span -0.5..0.5 on a 0.2 m cope
  stone and on a 9 m mill plinth alike. A 9 m plinth therefore took a fraction of one texture
  tile — the gate's "smooth cork-like block". Box-projecting alone did NOT fix it, and that
  near-miss is the lesson: the projection was the visible half of the bug and the coordinate
  was the other half. Everything is now driven from GEOMETRY POSITION, which is the world
  point in metres and does not care how a primitive was scaled — `seat_material`, the
  boarding, the masonry, the lane and the ground.
  This also explains a defect nobody had reported: `emb_ground_far` is a SCALED UNIT BOX
  256 x 324 m, so the far ground took a single smeared sample and rendered as the pale flat
  band behind the corner.
  AND WHY probe2 COULD NOT HAVE SHOWN EITHER: its throwaway never appended Dellhollow at all,
  so `M()` fell through to flat fallback colours and the mill was shaded on plain albedo. The
  engine inherited the material NAMES and the coherence ruling without inheriting a way to
  test them.

THE THIRD ONE WAS MINE, from the previous round: the tread material multiplied albedo by a
Noise Texture's COLOR output — RGB noise, not a scalar — so it tinted per channel and the
stepping-stone side faces rendered RAINBOW-STRIPED. `Fac`, BOX projection, and a narrow
0.74-1.06 multiplier.

THE STAIRS ARE SEATED: four 0.22 m slabs dropping 0.28 m had a 0.06 m gap under every tread
and nothing under the flight. Each tread is now a riser block carried down to the ground
under it (the build's own ground ray-cast), plus two side cheeks and 26 apron stones.

THE LIGHT WAS THE ADDITIVE TERM, AND TWO MEASUREMENTS PROVED IT RATHER THAN ONE OPINION.
The masonry measured L=122.9 on the plinth in frame b against probe2-b's L=95.0 on the same
surface. Darkening the albedo barely moved it: x1.00 -> 122.9, x0.77 -> 115.3. Two points
solve to L = 89.9 + 33.0 x scale, i.e. an ADDITIVE FLOOR near L=90 that no albedo can reach
past — and that floor was `emb_dress_pit_fill`, a 1500 W area light sized when the plinth
wore a warm rock scan and swallowed it. At zero the same surface measures L=99.2, within 4.4%
of the bar, which is also what the ratified probe had: no pit fill at all. Default 0, knob
kept (`--pitfill`).
  THE INSTRUMENT NOTE: an albedo sweep that moves the number by 6% while the target is 29%
  away is not a weak lever, it is EVIDENCE OF AN ADDITIVE TERM. Solve the line before turning
  the knob further.

AND ONE INVENTION WITHDRAWN. The first masonry drew VORONOI cell edges as courses; at plate
distance it read as cartoon crazy-paving — worse than doing nothing, and it was mine and not
the bar's. probe2's masonry is a FLAT NEUTRAL GREY carrying individually placed rubble boxes
on the faces the plate sees, and those boxes were already built here. Reverted to flat grey
plus a fine grain; the stones do the reading, as they do in the bar.

FRAME a's BEARING, RULED AND THEN MEASURED. The coordinator ruled option (i), mirror to the
pond side. Both hands are censused with the 9-ray bundle and the numbers decide: MIRRORED
gives the wheel 44% but drops the mill to 11% (`island_tree_02` across it); AS-MAPPED gives
the wheel 22% and the mill 89%. Neither hand reaches the 60% a hero needs, so the fallback is
the coordinator's own stated (ii) — accept the conifer, the town's own foreground is
legitimate grammar — and it is REPORTED, not fixed. No tree moved, no map restamped, and the
standoff not traded (a walk-in must earn 25 points; it earns 11).

STILL SHORT OF THE BAR, STATED PLAINLY: the plinth now reads as a plain pale mass rather than
coursed stone (the rubble boxes are too small to read at frame b's 54 m standoff), and the
wheel is not yet probe2-b's solid disc. Both are structure, not material, and both are the
next redline if the coordinator wants them.

STATUS: at the gate again. Not integrated; no district-wide work, no master-blend touch,
lane A's binaries untouched.

## 2026-08-01 — FOUR INSTRUMENT AMENDMENTS, each with its own negative control

Instruments were changed, so each fix had to prove the amended instrument STILL CATCHES
its original defect class before the new green was believed. Recorded here because three
of the four turned up something the handover did not know.

THE SPAWN-IN-CUT-BAND RULE (scenegraph_derive + cine_test). A cut's trigger is a BAND and
play3d's sgTick fires an `auto` edge ON ENTRY, so an arrival spawn inside a band is a
player who materialises already holding a cut: ONE DOOR RENDERS TWO SHOTS. Measured with
the runtime's own firing predicate (the separating axis of |along|<=t, |across|<=w,
dy<=vTol) against the shipped scenegraph: weapon-shop -0.951 m INSIDE, armor-shop
-0.157 m INSIDE, keepers-cottage +0.050 m — 0.45 m under the floor. THE HANDOVER NAMED
ONE; THE INSTRUMENT FOUND THREE. The weapon shop's was transition_test's door 7, whose
"+510 geometries" was two shots' art and never a leak. Arrivals are now pushed along the
walk surface to the nearest point clearing every band by 0.5 m, and every push is printed.
  THREE THINGS THE PUSH HAD TO LEARN, each from a measured wrong answer: sweep the FULL
CIRCLE (streetDir's tie-break is alphabetical, so the weapon shop's street direction
points away from the shop and a forward-only sweep pushed the arrival across the seam);
stay on the SAME TIER (walkY takes the nearest surface in height, and in a town that
stacks that found the quay deck 5 m below the armor shop's door); and land on THE
ARRIVAL'S OWN SHOT (clearing the band is worthless if the safety net corrects the camera
on the first tick — the same defect by another route).
  AND THE HEIGHT AXIS COUNTS LIKE THE OTHERS. Treating "above the vTol gate" as infinite
clearance let the keepers' cottage climb 1.4 m onto a ledge to sit 1.625 m over a
1.600 m gate: a 25 mm margin, clearance in arithmetic and nonsense on the ground.
  NEGATIVE CONTROL: reverting exactly those three spawns makes cine_test fail 4, each
naming the band, the axis and the number. Restored, 656 ok / 0 failed; transition_test
PASS 168/0 twice, door 7 green and shelf-east at 1071 geometries on both visits. A bonus
the push was not aiming at — the weapon-shop arrival used to be 91/91 body samples
occluded; it now rasterises 954 px through the shot's depth map.

MUSIC DRIFT IS MEASURED ON A CIRCLE (transition_test). A 71.989 s "drift" was a door
straddling the dellhollow track's loop: loopEnd 100.124 - loopStart 28.143 = 71.981 s, so
97.38 + 3.969 s wrapped to 29.37. Residual modulo the loop: 0.008 s.
  THE INSTRUMENT NOTE, and it is the whole reason to read the length instead of typing
it: "the ~68.02 s loop" is the obvious reading of the raw jump (97.38 - 29.36) and it is
WRONG — 68.02 is the loop MINUS the wall time, and hardcoding it leaves a 3.97 s residual
that keeps the assertion red for a subtler reason. music.json is where loop points live.
  NEGATIVE CONTROL, asserted every run before any voice is measured (MUSIC ARITHMETIC,
7 cases): the real failure now reads 0.008 s and passes; a STALL reads 3.970 s, a RESTART
28.011 s, a RESUME 2.000 s, a stall on a one-shot 3.970 s and a two-loop gap 71.989 s,
all still fail. The modulus forgives exactly one loop and could only launder a stall
lasting within 0.35 s of 71.98 s — a single door taking 72 seconds in a run that takes
under a minute.

NAV-EVAL STOPS INVENTING TARGETS (nav_eval). An occluded waypoint was retargeted past the
occluder to the floor behind it — a place the picture never showed the judge, while the
docstring claimed occlusion was recorded as a perception failure. It now aims at the
surface the pixel draws: 0 px from the judge's own pixel, by construction.
  MEASURE IN METRES, NOT PIXELS. On the gate the fabricated target was a mean 4.1 px from
the chosen pixel — and a MEDIAN 9.85 m, worst 53.64 m, behind what was drawn there. Near
the horizon a pixel is tens of metres deep, so the pixel number flatters the defect.
  TWO WRONG ANSWERS ON THE WAY, both caught by measurement, both recorded because they
are the obvious things to reach for. Dropping to the floor BENEATH the occluder is the
same invention, smaller (median 185 px off); there is no ground on an occluded sight
line, which is what occluded means. And "something is drawn nearer" is NOT occlusion by
itself — a grazing look down a stair satisfies it (loop-stairs' median gap 0.61 m against
waterfront's 3.46 m, same test, one a staircase and one a boat). The discriminator is
whether the drawn surface IS the walk network.
  NEGATIVE CONTROLS: oracle-world, which isolates the walker, 0.938 -> 0.938 UNCHANGED;
known-bad vs known-good still separates (0.333 vs 0.667, same 3 shots, same judge). The
end-to-end oracle fell 0.813 -> 0.750, and the two losses were probed against the
collision GLB rather than accepted: the ground-truth route on boatyard and waterfront
passes behind REAL geometry (`hero_hull_clinker`, `wf_stairmouth` standing 3.4 m over the
quay), not behind a water-transparency artefact — that hypothesis was checked and ruled
out. The instrument is reporting what it used to hide.
  GATE, N=10, judge pinned, control re-run on THIS tree so only the instrument differs:
score 0.00 -> 0.00 (THE VERDICT DID NOT MOVE and THE TOWN DID NOT CHANGE — no plate
re-baked, no camera re-aimed), onWalk 0.72 -> 0.28 with 32% occluded and 41% off-route
now visible. The gate's illegibility was always this bad; the ruler was flattering it.

ONE CRASH FIXED IN PASSING: cine_test read e.cam.key on a portal whose town has no camera
over its gate and THREW, taking every assertion below it with it. A missing camera is a
failure to report, not an exception to raise. Emberbrook still cannot reach the new
arrival-vs-band assertion — it crashes further down on a walk mesh whose owner has no
ownership region, which is that town's unfinished state and a separate job. The derive's
own validation pass does cover both towns (12/12).

## THE REDLINE ROUND REACHED A FRAME, AND THE FRAME OVERTURNED ITS OWN CLOSING MEASUREMENT
## (2026-08-01, dressing pilot lane, round 4 — the recovery of the session-killed round 3)

DELIVERED: `docs/qa/emberbrook/styleprobe/dress3-{a,b,c}.png` — THE FIRST FRAMES ROUND 3 EVER
PRODUCED (it wrote its whole redline fix and died at an API session limit before rendering; its
work was recovered uncommitted from the tree) — plus `dress3-amirror.png` (frame a's ruled other
hand, rendered) and `dress3s-b.png` (a measurement, not a candidate). Side by side against
probe2 in `pilot.html`. Engine `tools/emb_dress.py`. STILL AT THE GATE, not approved.

WHAT THE FRAMES SETTLE. R1 painted boarding: CLOSED, no blue-green panel survives in any of the
three. R3 tread side faces: CLOSED, no rainbow striping. R4 stairs: CLOSED, the flight is seated
with cheeks and apron. R5 water: CLOSED, pond in frame in c, brook in b, dam sheet and plunge foam
built. R2: the wheel now reads as a spoked disc inside its shroud with the launder arriving at
axle height — but THE STONE DOES NOT REACH THE BAR, and that is the entry worth keeping.

**A CLOSING MEASUREMENT MADE ON THE PREVIOUS ROUND'S FRAME DID NOT SURVIVE ITS OWN NEXT FRAME.**
Round 3 solved the pit fill out as an additive term and recorded that the same surface then
measured L=99.2, "within 4.4% of the bar". Measured here on the GATE FRAME ITSELF, matched crop
over the pit-and-plinth mass of `dress3-b.png` against probe2-b's dressed stone (luminance
0.2126R+0.7152G+0.0722B on the 8-bit frame; boxes 470,400-620,545 and 980,340-1180,560):

    probe2-b dressed stone   THE BAR      L= 99.7  sd=30.1
    dress3-b  stone x1.00                 L=134.6  sd=54.1     +35%
    dress3s-b stone x0.74                 L=121.7  sd=52.8     +22%
    two points  =>  L = 84.9 + 49.7 x scale;  scale to land the bar = 0.297

So there is STILL an additive floor near L=85 after the pit fill was removed. The pit fill was ONE
additive term and not the only one. Landing the bar by albedo alone would take a near-black stone.
The knob exists (`--stonescale`) and IS DEFAULTED TO 1.00: 0.74 is reported as insufficient rather
than shipped, and shipping it would also mean the committed engine no longer reproduces the
committed gate frames. NAMING THE REMAINING ADDITIVE TERM IS THE NEXT REDLINE — not another turn
of the albedo knob, which is round 3's own instrument note applied to round 3's own answer.
  AND THE INSTRUMENT NOTE UNDER IT: a measurement taken on the frame BEFORE the change is not a
measurement of the frame AFTER it. Round 3's L=99.2 was true of the round-2 render and false of
its own build. Re-measure in the frame that is actually being judged.
  WHY THE LEVEL IS THE READING AND NOT JUST A NUMBER: near AgX's shoulder the contrast between a
rubble stone and the wall behind it collapses. The individually placed stones ARE built and ARE
big enough to see (10-13 px at frame b's 54.5 m through its 32-deg lens), so the plinth reading as
"a plain pale mass rather than coursed stone" is the level eating the stones, not missing stones.

FRAME a's BEARING: THE RULING WAS EXECUTED, RENDERED BOTH WAYS, AND IT LOSES THE MILL. The
coordinator ruled (i) mirror to the pond side, with a stated fallback if the pond side has its own
blocker. It has one. Censused with the 9-ray bundle: MIRRORED gives the wheel 44% and drops the
mill to 11% (`island_tree_02` at 21.5 m of 39.9); AS-MAPPED gives the wheel 22% and the mill 89%
(`fir_tree_01` at 16.4 m of 43.3). Neither reaches the 60% a hero needs. THIS ROUND RENDERED BOTH
rather than reporting numbers: the mirrored frame is a tree trunk and a sliver of wall, and the
picture makes the call obvious in a way the percentages did not. New knob `--forcehand
<frame>=mirror|asmapped`; unforced behaviour is unchanged and still resolves to the stated
fallback. No tree moved, no map restamped.
  THE REASON THE KNOB HAD TO EXIST: a 60% threshold that rejects BOTH hands resolves to the
fallback silently, and the coordinator would then be ruling on one picture of a two-picture
question. A gate that can only show its preferred hand is not a gate.

ALSO ADDED, AND NOT YET RUN TO COMPLETION: `--idmap`, a screen census that casts one ray per cell
of a 140x80 grid through the SOLVED camera, marches past `hide_render`, and prints the first
RENDERED object per cell as a share of screen — the cheap half of a false-colour ID map, so a gate
sentence like "a big pale slab in frame b" gets a NAME instead of a guess. Its run was cut for time
before this gate (single-threaded ray_cast against ~900k hair instances is slow); shrinking the grid
or excluding the groundcover collection is the fix, and running it is the first job next round.

NOT THIS LANE'S, AND LEFT ALONE: `docs/qa/districts/exposure_{dusk,lifted}.png` are dated 2026-07-29
and referenced by nothing — orphans from a districts lane, not this pilot's key experiments, so they
are NOT committed here despite the handover's guess.

STATUS: at the gate. Determinism gate re-run on the final engine. Not integrated; no district-wide
work, no master-blend touch, lane A's binaries untouched.

## THE ADDITIVE TERM WAS A VILLAGE LANTERN, AND THE "ADDITIVE FLOOR AT L=85" NEVER EXISTED
## (2026-08-01, dressing pilot lane, round 5)

DELIVERED: `docs/qa/emberbrook/styleprobe/dress4-{a,b,c}.png` against probe2, in `pilot.html`.
Engine `tools/emb_dress.py`; new instruments `tools/emb_lum.py` (the ruler) and
`tools/emb_skylevel.py` (the world's absolute radiance). STILL AT THE GATE, not approved.

FIRST, THE RULER DID NOT REPRODUCE, AND THAT HAD TO BE SETTLED BEFORE ANYTHING ELSE.
Round 4 recorded "boxes 470,400-620,545 and 980,340-1180,560" in the REVERSE order to the two
surfaces it names. Read as written, the same three committed frames measure 26.8 / 43.4 / 42.4 and
not one of round 4's numbers comes back. Paired the other way they reproduce exactly — 99.7 sd 30.1,
134.6 sd 54.1, 121.7 sd 52.8. THE BAR is probe2-b at 980,340-1180,560; THE GATE MASS is dress*-b at
470,400-620,545. The ruler is now a file (`tools/emb_lum.py`) with both boxes and this correction in
its docstring, because the alternative is retyping a measurement that has already been wrong once.

THE CROP INSTRUMENT, so a twelve-way ablation is affordable at all: `--border x0,y0,x1,y1` renders
only those pixels of the frame with Cycles' border and CROP OFF, so the image is still 1400x800 and
the ruler's boxes still apply. Control: the border crop at 64 samples reproduces the committed gate
frame at 134.6 sd 54.0 against dress3-b's 134.6 sd 54.1 — the crop IS the frame.
  `--ablate "label:op,op;..."` then renders that crop once per configuration out of ONE build, so
the only thing differing between two crops is the one thing in the label.

=== 1. THE BINARY DISCRIMINATOR: NOTHING WAS EMITTING ===
    base                                      L=134.6   9.24% of the box CLIPPED at 254
    masonry base colour -> pure black         L= 41.0   0.64%
    ... and its specular also 0               L=  7.7   0.00%   (= the non-stone pixels)
Light was arriving that no albedo could remove, and it was not emission on the material: the
emissive-material census (strength AND colour non-zero — strength alone names every scanned bark in
the library, because Principled ships strength 1.0 with a black colour) lists five materials and
none of them is on this mass.

=== 2. THE "ADDITIVE FLOOR AT L=85" WAS A STRAIGHT LINE FITTED TO A CURVE ===
Five albedo points from one build (`--ablate alb=masonry:<s>`):
    s = 1.00 / 0.74 / 0.50 / 0.30 / 0.00   ->   L = 134.6 / 121.7 / 105.7 / 87.3 / 41.0
Rounds 3 and 4 both took TWO points, fitted L = 84.9 + 49.7 s, read the intercept as an additive
light and concluded the bar needed s = 0.297 — a near-black stone, correctly REFUSED. Measured, the
zero-albedo floor is 41.0, not 84.9, and the bar lands at s = 0.435. **AgX IS COMPRESSIVE, SO THE
ALBEDO-TO-DISPLAY RESPONSE IS CONCAVE AND EVERY CHORD ACROSS IT HAS A POSITIVE INTERCEPT WHETHER OR
NOT ANYTHING IS BEING ADDED.** Round 3's own instrument note ("an albedo sweep that moves 6% while
the target is 29% away is EVIDENCE OF AN ADDITIVE TERM") is only true in a linear space. It is not
true in 8-bit display luminance, which is what both rounds measured in. The refusal was right for
the wrong reason and it cost two rounds.
  THE NOTE THAT REPLACES IT: solve the line, then CHECK THE INTERCEPT BY MEASURING IT. A third
point costs one crop and it is the difference between a term and an artefact.

=== 3. THE TERM, NAMED: A LIGHT NOBODY HAD EVER LISTED ===
`light_key()` removes and rebuilds the two lights it OWNS and builds the mill's practical. Every
light the harvest carries in from the blockout passes through untouched and unlisted. There are
15 of them. `light_census()` now prints every light in the scene ordered by IRRADIANCE at the mill
(the honest key — a point lamp falls off as 1/4(pi)r^2, so 680 W at 6 m outranks 680 W at 20 m by an
order of magnitude), and the top of that list is the answer:

    KEYEMB_lamp_06_elder-house   POINT   680 W at  5.9 m   E = 1.5699 W/m2
    EMB_sun                      SUN    3.00 W             E = 3.0000 W/m2

A VILLAGE LANTERN PUTTING OVER HALF THE KEY SUN'S IRRADIANCE ON THE GATE'S OWN SUBJECT. And onto a
mass the key sun does not reach at all: turning `EMB_sun` off moves that box by 0.4%, because frame b
looks at the mill's SHADOW side. That is why the stone read cool and bright inside a warm dark frame
(the mass R/B 1.36 lit against the whole frame's 3.39) and why one patch of it clipped to white.
    ABLATION CROP, all lights     L=134.6  sd=54.0  peak 254.4   9.24% clipped
    ABLATION CROP, town lamps 0   L=109.6  sd=41.0  peak 176.0   0.00% clipped
  and then ON THE COMMITTED GATE FRAME ITSELF, which is round 4's own lesson applied to round 5:
    dress3-b (round 4)            L=134.6  sd=54.1  peak 254.4   9.30% clipped   +35.1%
    dress4-b (round 5)            L=110.0  sd=41.2  peak 174.3   0.00% clipped   +10.4%
    probe2-b  THE BAR             L= 99.7  sd=30.1  peak 181.3   0.00% clipped
**R8 IS THE SAME DEFECT AS R6, NOT A ROUGHNESS QUESTION.** The "hot white specular slab" is not
specular — `spec=0` leaves it at 8.63% clipped — it is the lantern's own pool blowing through AgX's
shoulder, and with the lamps off the peak lands just under the bar's own peak.
  RULED OUT FIRST, EACH WITH ITS OWN CROP: the material's specular (matte -> L=7.7, so nothing
emits); the bounce sun and the mill's window practical (both 134.6 to the tenth); the sun (0.4%).
  WHY ZERO IS THE DEFAULT UNDER THE PROBE KEY AND WHY THE LAMPS ARE NOT DELETED: probe2 was a
hand-authored corner in a throwaway blend with NO TOWN IN IT, so the bar's key never carried these
lights, and a light class the bar never had cannot be part of a comparison against the bar. It is
also true of the hour — at a 3.0 W golden-hour key a lantern is a glow in its own glass, not a key
light on the neighbouring building. Emberbrook is still the Heartlight town: `--key emberwake` (the
SHIPPED grade, where the lanterns live) is untouched, and `--townlamps 1.0` renders the pilot with
them.

=== 4. THE WORLD IS A SECOND TERM, MEASURED AND DELIBERATELY NOT TURNED ===
`light_key()` writes a flat background colour (0.30, 0.31, 0.42) at strength 0.30 and then LINKS A
SKY NODE OVER THAT COLOUR, so the flat value is dead code and the only number anyone ever wrote down
— in the source, in round 2's entry and in round 4's — is a strength socket. A strength socket is
not a level. `tools/emb_skylevel.py` renders the world alone to a 32-bit EXR, Standard transform, no
exposure, and reads the linear pixels:
    flat colour (0.30,0.31,0.42) x 0.30    mean 0.0947  peak 0.0947  RGB .090/.093/.126  (blue)
    Nishita sky node          x 0.30       mean 0.4458  peak 1.9073  RGB .474/.440/.421  (near-white)
4.7x, in a colour nothing else in this key emits. Unlinking it takes the stone 134.6 -> 62.9, more
than driving the albedo to pure black does.
  AND IT IS STILL NOT TURNED, BECAUSE THE GROUND VETOES IT. Same frame, same instrument: the pilot's
lane slab reads L=45.7 against the bar's own far bank at L=43.2 (+5.8%) — the ground is AT the bar,
which is what "ground accepted" meant. World strength 0.30/0.15/0.08/0.04/0 gives stone
134.6/108.6/89.7/75.5/56.0 and ground 45.7/33.7/27.1/23.0/19.4, so a world that lands the stone
(~0.115) puts the ground 29% BELOW the bar's own ground. ONE FRAME, TWO SURFACES, TWO VERDICTS: the
world's level is right for the ground and wrong for the stone, which means it is not the lever.
  So `--skylight` exists (a Light Path `Is Camera Ray` split: the VISIBLE sky is untouched, only
what the sky contributes AS LIGHT is scaled) and it DEFAULTS TO 1.0. Nothing changes. The number is
recorded because it was never measured, not because it was turned.

=== 5. R7: THE STONES WERE BUILT ON THE FACE THE OTHER FRAME SEES ===
`# coursed rubble on the face the plate sees` — decided by one frame, and there are three. The dam's
150 stones sat on x = +1.06 only and the pit's 150 on the INNER face of the FAR cheek, so frame b,
which looks at the dam from the other hand, had 13 m of bare wall and a bare 5.6 m cheek. Both dam
faces and both pit cheeks are now faced, each from its own crc stream (one stream on two faces
mirrors the wall and reads as a reflection), and the first face KEEPS ITS ORIGINAL KEY NAMES so 150
stones already in a committed frame do not silently reshuffle inside a change about something else.
  MEASURED, AND IT IS HONEST TO SAY IT IS SMALL: 109.6 -> 109.9 on the ablation crop, and on the
committed frames |grad| 3.51/3.61 -> 3.54/3.35 against the bar's 4.06/5.92. The gate's own box does
not land on either face that gained stones, so the remaining +10.4% is NOT closed by this and is
reported as open.
  AND A TASTE RISK NAMED RATHER THAN LEFT FOR THE GATE TO FIND: the NEAR PIT CHEEK's new facing
reads at 54.5 m as a stepped stack of pale blocks against the wheel's lower-left rim. The hero
census is unmoved (the wheel is 100% clear on the 9-ray bundle, same as round 4), and the vocabulary
is the bar's own — probe2-b's rubble is chunky and individually placed too — so it is SHIPPED and
FLAGGED rather than quietly reverted. The one-line revert is the second tuple in the pit-cheek loop.

=== 5b. AND THE COST OF KILLING THE LAMPS, WHICH IS THE REAL QUESTION FOR THE COORDINATOR ===
The lanterns were not only on the stone. Measured on the committed frames, same ground box:
    dress3-b ground   L=45.6      (the bar's own far bank: 43.2, so +5.6%)
    dress4-b ground   L=33.1      (-27.4% on round 4, and -23.4% on THE BAR'S OWN GROUND)
  and whole-frame, all three, round 4 -> round 5 (mean L, peak, % of frame over 250):
    a   57.1 -> 49.0 (-14.2%)   peak 255.0 -> 198.8   0.01% -> 0.00%
    b   57.6 -> 51.6 (-10.4%)   peak 255.0 -> 201.2   0.02% -> 0.00%
    c   59.4 -> 56.6 ( -4.7%)   peak 230.5 -> 227.0   0.00% -> 0.00%
  TWO THINGS TO READ OFF THAT. Frame c — the VEGETATION bar, the one frame with no mill in it —
barely moves, so R5 and the foliage verdict are not disturbed by this; the lanterns were lighting
the BUILT CORNER. And every round-5 frame now has ZERO pixels over 250, where round 4's a and b both
clipped and the ratified bar itself clips (probe2-b 0.04%). The pilot's highlights are now cleaner
than the bar's, which is a better place to be short from than the one it was in.
**"THE GROUND IS AT THE BAR" WAS TRUE WITH FIFTEEN UNLISTED LANTERNS BURNING IN DAYLIGHT.** Without
them the ground falls below the bar. So the two surfaces now want OPPOSITE moves — the stone is
+10.4% and the ground is -23.4% — and no single lighting lever closes both, which is what says the
remainder is a MATERIAL ratio and not a level. The levers are all in the engine and none of them was
turned by this lane: `--townlamps` (0 by default, 1.0 restores), `--skylight` (1.0, lifts or drops
what the sky contributes as light without touching the visible sky), `--stonescale` (1.00). The
corrected albedo curve says the stone lands the bar at x0.435, not the x0.297 round 4 refused.

=== 6. AND THE DETERMINISM DIGEST COULD NOT HAVE SEEN ANY OF IT ===
`content_digest()` promises "materials and lights" and hashes object-level light energy/colour and
material NAMES — and nothing at all about the world, the view transform or the exposure. The term
that cost two rounds lived in exactly that blind spot. The world's node graph (including the sky
node's own attributes), the view transform, the look and the exposure are now hashed.
  AND ONE GAP LEFT OPEN AND NAMED RATHER THAN QUIETLY CLOSED: the digest also does not cover the
CAMERAS, and cannot, because it runs before `shoot()` builds them and is normally invoked with
`--noshoot`. CLAUDE.md's summary of this gate says "world verts + materials + lights + camera"; the
camera half of that sentence has never been true. Closing it means digesting after the shot solve,
which changes what `--digest --noshoot` means, so it is reported for the coordinator rather than
changed inside a lighting round.

=== 7. AND THE --idmap CENSUS IS STILL NOT THE INSTRUMENT THAT ANSWERS THIS QUESTION ===
It is now aimable (`--idgrid nx,ny`, `--idbox x0,y0,x1,y1` restricts it to a PIXEL BOX, normally the
one the ruler measures). Aimed at the gate's own box at 56x56 = 3136 rays — a quarter of round 4's
grid over 4% of the frame — it still had not returned after 25 MINUTES OF CPU and was killed when
the machine's swap passed 96% with the gate render running. Single-threaded `scene.ray_cast` against
~900k hair instances is the cost, and shrinking the grid does not change the per-ray price.
  THE POINT WORTH KEEPING: the question it was queued to answer — WHICH MATERIAL IS THE PALE MASS —
was answered by the binary discriminator in ONE CROP, and answered better. `black=masonry` turns the
mass black, so the mass IS the masonry, by construction and without a ray budget. A census that
names objects is still wanted for "what is that thing", but for "what is this surface made of" the
ablation is a hundred times cheaper and it cannot be wrong about it.

DETERMINISM: two runs on the final engine, identical content digest
e1510172bb53706df606f482dc54c1eb8128adc0d5d28dae3f40cc640d4409cd — and that hash now covers the
world graph, the view transform and the exposure, which it did not before.

STATUS: at the gate. R6 named and killed (+35.1% -> +10.4% on the committed frame), R8 closed by the
same fix (clipping 9.30% -> 0.00%, peak 254.4 -> 174.3 against the bar's 181.3), R7 improved with
its remainder AND its taste risk reported open, and the ground's 23% drop put in front of the
coordinator as this round's own open trade rather than buried.
`--stonescale` stays 1.00 and was not turned. Not integrated; no district work, no master-blend
touch, lane A's binaries untouched.

## THE RESIDUAL WAS MATERIAL TRUTH, AND IT WAS BOUGHT FROM THE LIBRARY RATHER THAN INVENTED
## (2026-08-01, dressing pilot lane, round 6 — the masonry kit, with the town lamps back ON)

DELIVERED: `docs/qa/emberbrook/styleprobe/dress5-{a,b,c}.png` against probe2, in `pilot.html`, with
the crop evidence the material was chosen on (`crop5-b-*.png`, `diag6-b-lamp06off.png`). Engine
`tools/emb_dress.py`; new instrument `tools/dressing_texmeasure.py` (the library's albedo ruler);
three CC0 PBR masonry sets intaken into `public/assets/dressing/`. STILL AT THE GATE, not approved.

THE HEADLINE, IN THE RULER'S OWN NUMBERS (bar = probe2-b 980,340-1180,560 L=99.7; gate mass =
dress*-b 470,400-620,545; ground = dress*-b 395,555-530,600 against the bar's far bank 43.2):

    frame        stone L    vs bar    sd    peak    >200      ground L   vs 43.2   lamps
    probe2-b       99.7      BAR     30.1   181.3   0.00%       43.2       BAR      n/a
    dress3-b      134.6     +35.1%   54.1   254.4   9.30%       45.6      +5.6%     ON
    dress4-b      110.0     +10.4%   41.2   174.3   0.00%       33.1     -23.4%     OFF
    dress5-b      103.9      +4.2%   52.6   251.0   6.49%       44.2      +2.3%     ON

**BOTH SURFACES ARE INSIDE +/-5% AT THE SAME TIME, WITH ALL FOURTEEN LANTERNS BURNING** — which is
what round 5 said no single LIGHTING lever could do, and it was right: this was not a lighting lever.
The clipping is NOT closed and section 4 names the one object that owns all of it.

=== 1. THE DEFECT WAS NEVER A NUMBER ===
Round 5 got the levels honest (0.00% clipped, +10.4%) and the gate still refused: the base masses read
as SMOOTH PALE PLASTER. `masonry()` was a flat neutral grey plus a fine noise grain, standing in a
frame whose trees, bark, ground and litter are PHOTOSCANS. Next to a scan a procedural does not read
as a cheaper stone — it reads as NOT A MATERIAL, because everything around it has pores and it does
not. No albedo, world strength or lamp setting reaches that, and three rounds spent turning those
knobs is the evidence.

=== 2. THE CANDIDATE WAS CHOSEN ON A NUMBER BEFORE IT WAS CHOSEN BY EYE ===
Round 5's own albedo curve already held the specification: the bar (L=99.7) with lamps at 1.0 lands at
scale 0.435 of probe2's grey, i.e. an effective LINEAR luminance of 0.108. Twenty CC0 wall scans were
measured against it with a ruler that now lives in the repo (`tools/dressing_texmeasure.py`) and
sorted. LINEAR, not 8-bit: an sRGB byte mean runs ~1.6x high on a dark stone and is not the number the
shader sees — the trap this instrument exists to close.
    rustic_stone_wall       0.1444   R/B 2.47   1.52 m coursed rubble, deep mortar joints   SHIPPED
    stone_wall_04           0.1559   R/B 1.33   1.70 m neutral grey
    old_stone_wall_02       0.1907   R/B 1.96   2.09 m
    medieval_blocks_06      0.2130   R/B 2.44   2.00 m coursed blocks       SHIPPED (dressed role)
    worn_mossy_plasterwall  0.2259   R/B 1.32   1.80 m lime plaster         SHIPPED (plaster role)
    probe2's procedural grey 0.2477  R/B 1.17   what round 5 shipped

=== 3. AND THEN THE SURVIVORS WERE RENDERED, OUT OF ONE BUILD, AND THE SCREEN PREDICTED THE GATE ===
A screen is a sort, not a verdict. New ablation op `stex=<material>:<id>` re-points an already-bound
scan at another manifest entry AND rescales the mapping to THAT scan's own `size_m` — a candidate
judged at an invented physical size is not the candidate. Border crop 250,395-625,550, 64 samples:
    rustic_stone_wall   L=103.9  +4.2%   6.45% clipped
    stone_wall_04       L=105.9  +6.3%   7.23%
    old_stone_wall_02   L=109.5  +9.9%   8.09%
**The rendered order is the measured-albedo order, exactly.** A cheap JPEG download now predicts an
expensive render, so the next masonry role costs a screen and not a gate round.
  AND THE CROP INSTRUMENT'S OWN CONTROL HELD AGAIN: the 64-sample border crop measured 103.9 and the
  committed 120-sample full frame measured 103.9. The crop IS the frame, for the second round running.

=== 4. THE MEAN LANDED. THE CLIPPING IS ONE LUMINAIRE, AND IT HAS A NAME ===
6.49% of the gate box is pinned at 251, ALL of it inside a single 70x42 px patch at 470,416-540,458:
the HORIZONTAL CAP of the dam-and-cheek mass, the one surface in the box that looks straight up.
    the cap only           dress4-b (lamps 0)   L=115.5  peak 161.7   0.00% clipped   FRAME
                           dress5-b (14 lamps)  L=183.9  peak 251.0  47.96% clipped   FRAME
                           14 lamps minus ONE   L= 87.4  peak 154.6   0.00% clipped   crop
    the whole gate box     14 lamps             L=103.9   +4.2%       6.45%           crop
                           14 lamps minus ONE   L= 81.1  -18.6%       0.00%           crop
  (the lamp ablation is only affordable as a crop, so the rows it is compared against are crops too.
  The crop's own control reads 6.45% where the committed frame reads 6.49% — that 0.04 point IS the
  crop-vs-frame agreement this instrument is checked on, not a second measurement of a different thing.)
The one is `KEYEMB_lamp_06_elder-house`: a 680 W point light 5.9 m from the mill delivering
E = 1.57 W/m2 onto it — 52% of the key sun's own irradiance, onto the mill's SHADOW side, which is the
side frame b looks at. **Every clipped pixel of stone in this frame belongs to that single fixture.**
  IT WAS NOT TURNED OFF. The lamps are canon and the brief was explicit: report the ratio, do not kill
the light. The finding is handed over as a BRACKET to rule inside — the bar sits between 14 lamps
(+4.2%) and 13 lamps (-18.6%), far nearer the first. 680 W at 5.9 m is a stage light beside a
watermill; that is a lighting decision on the shipped `--key emberwake` grade and not this lane's.
  AND IT IS NOT ALBEDO-CONTROLLED, which is the reason to stop turning that knob: across a 32% spread
of candidate albedos (0.1444 -> 0.1907) the clipping moved 6.45% -> 8.09%, while removing one lamp
moved it to 0.00%. The lever is not on the material.

=== 4b. THE WHOLE-FRAME NUMBERS, AND THE CONTROL FRAME c PROVIDES ===
    frame   probe2 (bar)   dress4 (r5)        dress5 (r6)        r6 peak / %>200   bar's %>200
    a          72.4        49.0 (-32.4%)      54.8 (-24.4%)      255.0 / 0.08%       1.43%
    b          81.4        51.6 (-36.6%)      55.5 (-31.8%)      255.0 / 0.16%       4.30%
    c         116.2        56.6 (-51.3%)      57.4 (-50.6%)      233.7 / 2.44%      30.38%
**Frame c — the VEGETATION bar, the one frame with no mill in it — moved by 0.8 L.** That is the
control this round needed: the masonry kit changed the BUILT CORNER and left the foliage verdict
exactly where round 5 left it, so R5-vegetation is not silently re-opened by a masonry change. Every
frame is still far cleaner in the highlights than the ratified bar itself. The whole-frame means stay
under the bar because probe2 is a CLOSE-UP of a lit corner and these are plates with a dark valley in
them — composition, true since round 2, and not what the gate box measures.

=== 5. THE NEAR CHEEK'S FACING IS WITHDRAWN, AND THE REASON IT COULD BE WITHDRAWN NOW ===
Round 5 shipped it FLAGGED ("reads at 54.5 m as a stepped stack of pale blocks") and the gate agreed:
blocky stacking. Reverted — one tuple in the pit-cheek loop. The revert is right NOW and was not right
then, and the difference IS this round: round 5 could not withdraw it without handing the frame back a
bare untextured slab, because that slab's only material was flat grey. It now wears a 1.52 m coursed
rubble SCAN with its own joints and relief, so the cheek reads as a wall by BEING one instead of by
having boxes stuck to it. The far cheek keeps its facing and its original crc key names.

=== 6. THE LAUNDER REDLINE DOES NOT REPRODUCE, AND THE DISCRIMINATOR SAYS SO TWICE ===
The brief asked for the launder to be put back into the `mat_wallwood` family, "not bare pale boards".
Measured on its own band (260,452-400,466):
    dress4-b  L=38.1  sd 40.6  peak 109.8  0.00% clipped
    dress5-b  L=44.2  sd 39.7  peak 114.2  0.00% clipped     (whole frame b: L=55.5, peak 255)
The launder is DARKER than the frame it sits in and has not one clipped pixel. What reads as a pale
ribbon is LOCAL CONTRAST — a specular band against near-black ground — not level. Its boards are
already `emb_dress_boarding`, built in round 3 precisely BECAUSE `mat_wallwood` is Dellhollow's
blue-green LIMEWASHED cottage board; putting the launder into that family is round 3's R1 re-committed
on purpose. NOTHING ON THE LAUNDER WAS CHANGED and the redline goes back to the gate as NOT REPRODUCED.
  AND THE SECOND READING IS THE ONE WORTH KEEPING. The obvious suspect was the launder's own water fill
wearing the plunge-foam material. The binary discriminator says no: `hide=leat_water` is IDENTICAL to
the control in that box to the last decimal (44.2 / 39.7 / 114.2 on both), and across the whole
375x155 crop only 44 pixels moved by more than 6, in a band at y 490-542 — nowhere near the ribbon.
**The thing about to be fixed was not the thing being looked at**, and one crop cost less than the fix.

=== 7. THE INTAKE, AND THE TWO POLICY SENTENCES IT EARNED ===
Through lane A's own path: manifest entry with a `role`, the scan's own physical `size_m` (a builder
that tiles a wall scan at an invented scale has built a different wall), the MEASURED linear albedo and
its instrument, and a `fetch.json` sha256 pinning the exact PolyHaven bytes each shipped file was
copied from — verified byte-identical after the copy. CC0, 3 sets, 29 MB.
  RESOLUTION IS PER-MAP: 2k diffuse and normal, 1k roughness and height. And it is 2k by the
coordinator's call rather than by a resolvable difference, which is recorded so the headroom can be
spent later: the nearest plate camera stands 40 m off this masonry through a 32-deg lens = 61 px/m, so
a 1.52 m tile spans 93 px and even a 1k map is 11 texels per pixel. 1k would serve.
  HEIGHT FIELDS SHIP PNG, EVERYTHING ELSE JPEG. Measured on the five candidates at 1k: JPEG's rms
HEIGHT error is only 0.0016-0.0027 — but bump shading reads the GRADIENT, and there the same
compression injects 0.0008-0.0016 rms against a true gradient sd of 0.0037-0.0141, i.e. 8% to 22% of
the signal, worst on the flattest wall. PNG costs 1.3 MB per set and removes it.
  TWO CANDIDATES DROPPED after the crop gate, with their measurement and their reason in the manifest's
own `dropped` list (-20.6 MB) — and their `fetch.json` PINS KEPT, because a pin costs a few hundred
bytes and is the whole cost of making that comparison re-runnable.

=== 8. THE BINDING, AND THE ONE TRAP INSIDE IT ===
Box projection driven from WORLD POSITION divided by the scan's `size_m` — `seat_material`'s hard-won
rule, because every primitive here is a SCALED UNIT TEMPLATE and object coordinates span -0.5..0.5 on a
0.2 m cope stone and a 9 m plinth alike. One number gives a 9 m plinth 5.9 tiles and a 0.4 m placed
stone a quarter of one. Normal map on the Principled; height through a Displacement node into the
material output at `displacement_method='BUMP'` — Blender's real displacement path minus the
subdivision bill, so a 45 mm mortar joint self-shades at grazing light instead of being a picture of one.
  THE TRAP: a single world-space projection is CONTINUOUS, so the ~450 individually placed rubble boxes
would have sampled the scan in perfect register with the wall behind them and DISSOLVED BACK INTO IT —
the mass reading, re-created by the fix for it. An Object Info `Random` offset gives each object its own
patch of the scan; it is stable per object, so it costs nothing in determinism, and on the big
continuous walls it does nothing at all because each of those is one object.
  AND ONE INSTRUMENT BUG FOUND BY BUILDING THE THING IT MEASURES: round 5's `alb=` ablation scales
colour RAMPS and then falls through to a socket — but a SCANNED material drives Base Color from an
IMAGE, so `alb` would have swept a flat line on exactly the materials this round introduced and read as
"albedo is not the lever". A measurement that CANNOT move is not evidence that nothing moves it. `alb`
now inserts a multiply when the socket is linked.

=== 9. WHAT WAS CUT, AND WHY, SAID PLAINLY ===
The diagnostic batch's last two crops (`alb=masonry:0.70`, `black=masonry`) were KILLED mid-run when
macOS grew the swap file and two concurrent Blenders took it to 97% — the same machine condition that
killed round 5's idmap census, and the standing cap says 2 jobs above 75% swap. The question they were
queued for is answered by section 4's albedo spread, which is the same measurement from data already on
disk. The `--idmap` census is still unrun and still too slow.
  AND ONE TRANSCRIPTION DEBT PAID, PARTLY: round 5 recorded "the bar's own far bank at L=43.2" and every
ground ratio against it WITHOUT ITS COORDINATES — the identical failure to the transposed stone boxes it
had just corrected, in the same entry. Round 6 recovered a box by sweeping probe2-b for one that returns
the published value (720,100-855,180 -> L=43.52 sd 9.76, the only low-variance candidate that close) and
put it in `emb_lum.py`'s docstring MARKED AS A RECONSTRUCTION. The published 43.2 stays the bar for every
ratio; the box is there so the next round re-runs something instead of writing another sentence.

DETERMINISM: two runs on the final engine, identical content digest
e9273a1a54b06e0a55cc954b10c4ec69b65289feb522d8d365deaa335ef8d3d8 (round 5's was e151017...; the
masonry binding moved it, which is the hash doing its job).
  AND IT DID A SECOND JOB, UNPLANNED AND WORTH KEEPING. The same digest came back BEFORE and AFTER two
edits made while the gate frames were already rendering — the `alb=` ablation fix and the drop of two
rejected texture sets from the manifest. Identical digests are the PROOF that neither touched the built
scene, i.e. that the committed engine and the committed library reproduce the committed frames. The
alternative was asserting it from reading the diff, which is exactly the class of claim this gate exists
to refuse.

STATUS: at the gate. Stone +4.2% and ground +2.3% SIMULTANEOUSLY with the canon lamps burning; clipping
6.49% reported OPEN with its single named cause and a measured bracket; the cheek revert done; the
launder redline returned as not reproduced. Not integrated; no district work, no master-blend touch,
lane A's binaries untouched.

## THE PILOT'S RULES MET THE WHOLE VILLAGE, AND SIX OF THEM WERE WRITTEN AGAINST A 30 m DISC
## (2026-08-01, dressing town-wide lane, pass 1 — the engine, the library and the board)

DELIVERED: `tools/emb_dress.py` at `--region all` (the engine, six rule fixes and two new
modes), five CC0 texture roles through lane A's own intake path, `tools/emb_board.py` +
`tools/emb_boardfill.py` (the review board and its spec filler), and
`docs/qa/emberbrook/dressed/` — the board. Commits 5678efb, b4a379c.

THE HEADLINE IS THAT NONE OF THE SIX WAS A BUG IN THE PILOT. Every one of them is a rule
that is CORRECT at 30 m and false at 200, which is exactly what a district pass is for, and
five of the six presented as "the build hangs". None of them was a hang: every one was
QUADRATIC AND NEVER IDLE, which is the same picture from outside and the opposite problem.

=== 1. `RR = 1e9` WAS NOT A RADIUS, AND THREE RULES SPEND IT AS A LENGTH ===
`--region all` set `RCX, RCY, RR = 0, 0, 1e9` to mean "no filter". But `dress_bank_planting`
draws its 260 candidates from a square of side 2 x RR about (RCX, RCY) and keeps the ones
within 3.40 m of water — an ACCEPTANCE RATE, and an acceptance rate falls with the square of
the region. Measured, town-wide dry run: **0 plants, printed as a success line.** The same
code at the mill emits 176.
    The region is now the map's own landmark extent (centre 64.0, 56.0; radius 104 m from
45 landmarks plus a 20 m rim margin) and the bank sampler draws around EACH WATER BODY'S OWN
BOUNDS. Town-wide: **1112 plants from 1298 candidates, 86% accepted.** Margin and tread
clearance unchanged, so the mill's own bank keeps its ratified recipe.
  A SENTINEL THAT READS AS A NUMBER IS WORSE THAN AN ASSERTION, because the rules that
consume it cannot tell the difference. That is the transferable half of this.

=== 2. 700 CLUMPS PER m2 IS A DENSITY, AND OVER A VILLAGE IT IS ALSO A BUDGET ===
The ratified density was swept against the bar on a 30 m disc: 3 232 m2, ~2.3 M hair
instances, and it renders. The blockout's valley ground is **39 237 m2**. The same rule over
the same ground asks for **27.5 M**, and Blender sorts one request in a SINGLE-THREADED
`BLI_qsort_r` inside `distribute_particles`.
    MEASURED (macOS `sample` on the stalled process): **2 256 of 2 257 stack samples inside
nested qsort frames**, 11 GB resident, no output in 15 minutes.
    THE FIX IS A RULE THAT WAS ALREADY IN THE TOWN. Groundcover is dressing for FRAMES, and
every plate this town bakes is composed on its walk network. So the scatter is spent inside
a **14 m band about the walk network** — the ratified 700/m2 unchanged inside it — and beyond
it the ground material's own mix carries the reading, which is what `--tier realtime` already
does everywhere. Town-wide the band is **9 546 of 39 237 m2 (24.3%)**; at the mill, **2 679
of 39 237 (6.8%)**. The request is TILED at 400 000 per system over equal-AREA slabs cut
from the band faces' own area distribution, each with a crc-derived seed: **6 681 932
particles over 17 slabs.** Density is exact per slab, so the tiling cannot change the
picture — only how many calls the distributor is asked to make.
  THE BAND IS 14 m FROM THE PLATE CAMERAS, NOT FROM TASTE: `emberbrook.cameras.json` carries
`maxDist` 46 and `fov` 35, and a 35-deg frame aimed along a lane at 46 m has a half-width of
14.5 m. One lane-width either side of every tread is what the frames actually contain.

=== 3. THE GROUND ORACLE WENT THROUGH THE DEPSGRAPH, AND THAT MADE THE BUILD QUADRATIC ===
`raycast_ground` called `Object.ray_cast`, which needs the object's EVALUATED geometry —
and every `veg()` call creates an object, which TAGS the depsgraph. So the town-wide build
alternated "create one tree" with "realize every instance created so far".
    MEASURED: `execute_realize_mesh_tasks` + `adapt_mesh_domain_face_to_point` +
`threaded_copy` at **100% of samples for over an hour**, with the build still part way
through its placements. It never looked like a hang because it was never idle.
    The ground is a STATIC mesh that only two stages ever cut, so the oracle is a standalone
`BVHTree` over its world-space verts, rebuilt by `ground_dirty()`. **No depsgraph in it at
all.** The same build then reached bank planting and groundcover in minutes.
  AND IT IS NOT BIT-IDENTICAL, WHICH IS RECORDED HERE RATHER THAN DISCOVERED LATER.
`BVHTree` triangulates a quad on its own diagonal and the renderer picks its own, so the two
surfaces differ by exactly the `(z1+z3-z0-z2)/4` term `dress_groundcover` already measures on
this same mesh: **0.0006 m median, 0.046 m at p99, 0.24 m worst** (the worst inside the
excavated wheel pit, where the ground genuinely steps). It showed immediately and honestly —
the mill's stair risers moved **1.60/1.31/1.02/0.74 -> 1.57/1.27/0.98/0.70**, 3-4 cm on a
flight whose treads are 1.6 m apart. Inside the mesh's own known ambiguity; still a change to
a ratified build's numbers, so it is in the record.

=== 4. THE BUILD FINISHED AND THE SOLVER HUNG, WHICH LOOKS IDENTICAL FROM OUTSIDE ===
Same defect, second site: each candidate camera stand costs one ground ray and one nine-ray
census, and with the groundcover's particle systems live every one of those realized the
town's entire hair scatter first. The groundcover modifiers now leave the depsgraph for the
solve and for the hero kits and go back **before a pixel is traced**. It costs the answer
nothing: a 0.4 m clump is not an occluder for a framing solved at 12-46 m, and
`_cast_visible` was already SKIPPING any hit whose object is hidden.

=== 5. THE TOWN HAD NO BUILDING LAYER AT ALL, AND THE ANSWER WAS NOT 999 KITS ===
Outside the mill's own 670-line kit, **all 999 `lm_` meshes rendered as flat gray massing.**
`hide_gray` had been hiding that at the pilot's radius; at `--region all` it correctly turns
itself off, and what was left was a gray village with three dressed trees in it. 2 232
objects in the master; the dressing touched 555 instances and one corner.
    THE BLOCKOUT ALREADY SAYS WHAT EVERY SURFACE IS. It paints seventeen NAMED materials —
`emb_mat_thatch`, `_plaster`, `_stone`, `_timber`, `_cobble` and the rest — and those names
are a contract exactly as `lm_*_roof` and the 21/29/15 crown recipes are. So the dressing
re-renders its MATERIAL CLASSES once, and every object the blockout already called thatch
becomes thatch. **1 247 slots on 1 247 meshes town-wide** (timber 792, stone 226, earth 101,
plaster 51, thatch 40, tile 21, road 14, slate 2), no object inspected, no placement moved,
one table, and a map change costs nothing.
    NOT SUBSTITUTED, each on a stated rule: `emb_mat_heartlight` (story core — the map says
treat it with reverence in every shot), `emb_mat_lamp_glass` and `emb_mat_window` (this
town's defining EMISSIVE light; rounds 5 and 6 are about getting them right), `emb_mat_water`
(`dress_water` owns it), `emb_mat_grass` (the ground owns it).

=== 6. AND A FALLBACK THAT COULD ONLY EVER BE GREY ===
`masonry_scanned` fell back to `masonry()`'s coursed procedural grey when a role was missing.
With `roof_thatch` absent that would have put **coursed stone on every roof in Emberbrook**,
silently. `fb_mat` names the honest fallback per role. Five CC0 roles were then intaken so
none of them is needed — measured LINEAR with `tools/dressing_texmeasure.py`, `size_m`
cross-checked against each scan's own autocorrelation ladder, sha256-pinned, 37.2 MB:
    roof_thatch     riet_01                0.1277   2.50 m    (band 0.10-0.18)
    roof_slate      grey_roof_01           0.1068   8.00 m    FLAGGED: 6.8% over the band
                                                              top, and the next darkest CC0
                                                              slate is 0.1635 — 64% over,
                                                              and brighter than the ratified
                                                              stone bar. No better exists.
    roof_tile       clay_roof_tiles_03     0.1311   2.60 m
    paving_cobble   square_cobblestone     0.1261   2.00 m
    timber_board    old_planks_02          0.0965   2.00 m    FLAGGED: at the library's own
                                                              ground_mud level, the darkest
                                                              surface in the kit
24 dropped candidates keep their measurement, their reason and their fetch pin.

=== 7. TWO NEW MODES, AND WHY EACH IS DERIVED RATHER THAN COMPOSED ===
`--shotset town` derives ONE EYE-LEVEL FRAME PER MAP PARCEL — the same parcels that derive
every scene contract and sceneKey, so the district set is the map's and not this lane's. The
camera STANDS ON THE WALK NETWORK (a district frame is a place the player can be), at the
standoff the target's own BUILT extent solves for, at the lens and the min/max distances
`emberbrook.cameras.json` already ratifies (fov 35, 12..46 m, aimLift 1.20, charH 1.70).
Among the candidate stands the best nine-ray clear fraction wins; under 60% the frame is
REPORTED OCCLUDED and carried onto the board with that report attached. Plus three aerials
solved from the town's own extent. **10 frames, 3 aerial + 7 district.**
  NO SOLVED CAMERA IS READ OR WRITTEN. A sibling lane owns those and the file on disk is
pre-2x-rescale (its `square` camera aims at (30.2, 21.7); the map's `square-plaza` is at
(64, 44)). These framings come from the map and the camera DEFAULTS only.
`--nodress` runs the identical derivation with every dressing stage skipped — same map, same
harvest, same light key, same shot solver, same lens, same pixel grid — so the board's
before/after pairs differ only in the thing being reviewed. It is HASHED INTO THE DIGEST, so
a `--nodress` build can never be mistaken for a dressed one.

=== 8. THE HERO KITS, AND THE ONE THAT IS NOT A SHRINE ===
**168 pieces across 4 map-stamped places**, nothing searched and nothing nudged, built to the
coordinator's own bar ("reads true at plate distance"): at 12-46 m through a 35-deg lens a
1400 px frame gives 26-100 px/m, so a 0.4 m crate is 10-40 px and a poster is a pale
rectangle with dark bands whatever is painted on it.
    Festival Square 60 — the dais (7-board deck on 4 joists), the bell (post-and-lintel), the
      Heartlight's KERB, Poppy's stall (trestle, two-plane canopy, crates), the notice board
      with the CH1 poster, the rota and the child's drawing.
    the inn 9, the bakery 12 — each front derived from the map's own `doorFace` where it
      carries one and otherwise faced to the square, plus the blockout's own built half-span.
    the Old Gate court 87 — 63 flagstones, BOTH CH1 sigil plates built PROUD of the apron at
      their stamped coordinates (a plate flush with the paving at 30 m IS paving), and the
      culvert and kerb where the stamped river tail runs beside the road.
  THE HEARTLIGHT GETS A KERB AND NOT A SHRINE, and that is the map's ruling and not a taste
call: `dressing._doc` EXCLUDES wayside shrines because the Heartlight owns meaning. What goes
round it is the civic thing a village actually builds — a kerb that keeps feet and carts off
the pedestal — and nothing devotional. At the gate court nothing is lit, nothing is domestic
and there is no lamp: `beyond_warmth` holds and the Gate Field stays the town's one unwarm
frame.

=== 9. THE CARRIED REDLINES ===
(b) IS CLOSED, AND THE NUMBER CAME OFF THE BUCKET RATHER THAN OFF THE EYE. "The wheel's
shrouds want more solidity vs probe2-b." A shroud IS the plate that closes a bucket at each
end of the wheel, so its radial depth is the bucket's. This build's own bucket: `buckA` at
R-0.34 with a 0.50 m radial board, i.e. spanning **R-0.09 to R-0.59**. The shroud ran
**R+0.05 to R-0.30** and closed only its OUTER HALF — every bucket on the wheel was open at
both sides for its inner 0.29 m, which at 54 m through a 32-deg lens is exactly what reads as
a hoop with slats behind it. Inner radius to **R-0.62**; outer radius, 0.26 m thickness, iron
strake and 4.4 m diameter unchanged, so the silhouette does not move. The inner hoop follows
it in (R-0.70..R-0.87) rather than being half buried in the plate it exists to break up.
(a) IS OPEN, WITH ITS INSTRUMENT AND WITHOUT A GUESS. The finding is round 6's and is not
disputed: 6.49% of the gate box pinned at 251, all of it in one 70x42 px patch, all of it
`KEYEMB_lamp_06_elder-house` — 680 W at 5.9 m delivering **E = 1.57 W/m2, 52% of the key
sun**, onto the mill's shadow side. `--lampclamp` states the rule AS A NUMBER — no single
town practical may out-irradiate the key sun on a dressed mass by more than R of it — and
PRINTS what every fixture would bind at on every run. **It defaults to 0.0, i.e. off**, and
that is deliberate: nothing has been measured against the bar yet, and shipping a default
would mean the committed engine no longer reproduces the committed gate frames. Same
discipline as `--stonescale`. The next round rules on measurements, not on the bracket
alone.

=== 10. WHAT IS NOT DONE, SAID PLAINLY ===
The town-wide plate render is the expensive half and it is still running at the time of
writing; the board carries whatever frames exist and NAMES the gaps rather than dropping
them. Not yet run: the `--nodress` pass that fills the before/after pairs, the realtime-tier
`emb-townwalk` export, walk QA / COVERAGE / lamps-14 / geometry_audit / the seal re-print,
and the two-run determinism digest on the final engine. Boundaries still re-render 119 of 522
stamped fragments by the vegetation path — the other 403 are rails and pales, which the
material pass now surfaces as timber, so they are dressed but not *searched*; whether they
want their own path is a question for the next round and not an answered one.
  AND ONE HAZARD FOR THE COORDINATOR: `tools/townwalk_live_refresh.sh` re-exports
`public/assets/scenes/emb-townwalk` FROM THE MASTER BLEND on a 10-minute cron. A dressed
realtime export dropped there is reverted the next time the master's mtime moves, so that
line has to point at the dressed realtime blend before the export means anything.

## THE CAMERAS WERE MEASURING A TOWN THAT NO LONGER EXISTED, AND THE 50 px FLOOR IS THE 2x BILL
## (2026-08-01, camera/data lane — seven shots re-solved, the opener minted, the parcel pass, no bakes)

THE ONE-LINE CAUSE, and everything below is downstream of it: `walkSceneKey` still said
`emb-walk`, a one-off `tools/emb_export.py` bundle last written 07-31T04:43 against the 1x
town. Every Emberbrook camera had been solved against walk geometry whose bounds stop at
x=31 on a map that now runs to x=118. Repointed to `emb-townwalk`, the ten-minute cron's
export of the same master: 162 walk meshes at 2x against emb-walk's 139 at 1x, and the
solver's ownership went from 15 landmarks + 5 edges owned by NO camera to zero of each.

=== 1. THE HEADLINE, MEASURED ON 468 ANGLES PER SHOT AND FIVE LENSES ===
A new instrument, `tools/cine_sweep.mjs`: it calls the SHIPPED solver (solveCamera, with
yaw/pitch overridden) and ray-casts the result against the walk bundle's own 207k triangles
through a BVH, so "does it fit" and "can it see" are answered in one process in 3 seconds.
It exists because `cine_visprobe.py` can only sweep cameras that are ALREADY solved, needs
Blender (the memory cap said no: swap was at 88% with a dressing render running), and
re-implements the solver's fit in a second language.
  THE CEILING TABLE — best charPxFar over all 468 angles, against cine_test's 50 px floor:

     shot        as authored   ceiling   angles clearing BOTH gates (of 468)
     woodroad         39          51                 10
     arch             31          35                  0
     square           33          37                  0
     pondlane         41          52                 17
     homerow          56          60                106
     northlane        30          32                  0
     gatefield        55          60                213

**FIVE OF SEVEN SHOTS CANNOT REACH 50 px AT ANY ANGLE**, and the lens is not the lever:
swept at fov 28/35/45/55/65 the square reads 41/37/34/31/28 px — narrower helps a little,
wider always hurts, and nothing gets near the floor. Margin is worth ±2 px (0.03..0.10).
The relation is span: a 35-degree lens holds about 20 m at 50 px, and the 2x round doubled
every area extent. `square-plaza` is extent 14 = a 25 x 27 m room. THE DIAGNOSTIC THAT
NAMES THE CAUSE: an ownership variant giving the square's four lane-head stubs away and
leaving it the bare plaza floor measures 35 px — WORSE than the 37 it has with them. It is
not the ownership. It is the plaza.
  AND THE SPLIT THAT IS ALREADY AGREED FIXES THE WORST SHOT: `northlane` owns 18 m of walled
climb plus the 58 m quiet road. Take the road away and the climb measures a 92 px ceiling
with 215 of 216 angles clearing every gate; the road alone as ONE shot is 42 px, as TWO it
is 72 and 65. The measured answer is THREE shots where there is one — a shot-budget ruling
for the coordinator, not a framing one, and `p-gateroad` (minted this round) is now the only
parcel in the town with no shot of its own.

=== 2. WHAT THE SEVEN SHOTS ARE NOW, AND WHY EACH MOVED ===
     shot        yaw/pitch      dist   charPx n..f   visible   was
     woodroad     270 / 18      41.1    87..39       89.1%     NEW — the game's first frame
     arch         280 / 26      44.0    70..31       95.3%     260/32, and 91% at best there
     square        90 / 46      47.6    57..33       90.6%     90/42 (north bearing HELD)
     pondlane      30 / 14      41.5    91..41       96.9%     0/20, 45% at 1x
     homerow      290 / 50      28.4    89..56       84.4%     340/42 -> 65.6% visible
     northlane    320 / 54      56.4    44..30       79.7%     320/24 (bearing HELD)
     gatefield    270 / 42      27.3    89..55      100.0%     290/42 — the deviation withdrawn

`gatefield` is the one shot that got BETTER at 2x, and it is a lesson about stale
reasoning: yaw 290 existed because 270 measured 0.0% at 1x with Pond Lane's crowns closing
the sightline 20 m short. The seclusion stamp then moved the court 87 m away, so that
geometry is 60 m BEHIND the camera now. The plan's own "from the south, gate square-on" is
restored, and BOTH SIGIL PLATES ARE IN FRAME BY MEASUREMENT — ndc (-0.03, 0.19) and
(0.11, 0.20), side by side just above centre.
  maxDist re-ruled 46 -> 66 (a 1x leash was cropping five of seven shots; a capped shot is
a shot with its own ground outside its own frame). charPxMin floors set one px under each
shot's measurement on arch/square/pondlane/northlane/woodroad, each with the ceiling table
and the named alternative in its own `_charPxMin_why`. Home Row and the Old Gate need none.

=== 3. THE SPLITS WERE 1x NUMBERS AND seam_test FOUND IT BY WALKING TO THE ITEM SHOP ===
A split puts the seam where the plaza narrows to a lane. The four authored fractions were
measured off the 1x plaza (pond 0.352, home 0.569, north 0.573, bridge 0.445); the band's
half-width is measured off the walk surface, so at 2x those seams stood ON the plaza and
measured **12.4 u wide against the 13 u cap**. seam_test's finding, in the form a player
would meet it: walking from the Heartlight to the ITEM SHOP crossed two camera cuts.
  Re-measured by walking each edge and asking which mesh owns the ground: the plaza floor
ends at t=0.633 / 0.717 / 0.567 — all roughly DOUBLE the 1x distances, which is what a 2x
scale does to a distance. Splits are now 0.78 / 0.73 / 0.573 and every band is 1.4-2.95 u.
  THE BRIDGE DIAGONAL LOST ITS SPLIT: at extent 14 the plaza covers the WHOLE of
`brook-bridge__square-plaza` (the footbridge is 14.4 m from the plaza centre, i.e. on its
rim), so no fraction on it is outside the plaza. `square` takes all of it and the cut falls
back to the endpoint rule, 2.8 m from the bridge.
  THE QUIET ROAD GAINED ONE: `barn__gate-court` split at 0.80. The endpoint rule put that
seam 2.8 m from the gate court's centre — inside an extent-10 area, band 10.3 u — and
seam_test caught it where it hurts: walking the court to the Whisperwood stile fired the
gate cut twice plus a positional correction. seam_test emberbrook: 5 failures -> 2.

=== 4. THE PARCEL PASS: MEMBERSHIP IS DERIVED FROM BOUNDS, AND NOBODY HAD SAID SO ===
`townmap_derive` and the viewer both test the landmark's POSITION against the parcel box;
`members` is the authored statement of the same fact, and the two had drifted a scale apart
— 24 landmarks named in no `members` list, 5 inside no box at all, 6 inside two boxes at
once. All 45 landmarks are now in exactly one parcel, `members` matches bounds exactly,
sub-2 m gutters are gone and 3 of 4 box overlaps with them. The one that remains
(p-square n p-homerow) is structural, holds no landmark, and is left standing with its
reason: the watermill at x=52.2 is Home Row's and the bakery at x=47.2 is the square's, so
no single plane separates them.
  **p-gateroad minted** (ch1-staging-audit stamp 7, deferred at the seclusion round):
p-gatefield ran y 60..142 — the town's last warm building AND the unwarm court AND the
41.1 m of road built to separate them, under one scene contract, while Chapter One stages
on that road twice (beat 27's refusal, beat 29's send-off).

=== 5. THREE INSTRUMENTS WERE CRASHING RATHER THAN FAILING, AND ONE WAS PROJECTING THROUGH A DEAD CAMERA ===
`cine_test` had NEVER RUN TO ITS OWN SUMMARY for Emberbrook: an ownerless walk mesh made
`inShot(regById[undefined])` throw, so the eight assertion blocks after it had never been
evaluated for this town at all. Now a named failure with the mesh names and a hint that
distinguishes an ownership hole from a stale bake. Same class in `seam_walk`, which died
three frames deep on a journey leg naming a withdrawn edge.
  AND `routes_derive` WAS PROJECTING EVERY SCREEN POSITION THROUGH `cine.json` — the BAKE's
receipt, not the authority. Emberbrook's plates predate the 2x redline and its solved
cameras stand 15 to 85 u from where they were rendered, so every `screen` field was a
projection through a camera that no longer exists, and **nav_eval composites from this
file**. Now projects through the solved camera and NAMES the disagreement in `warnings`.
Provable no-op where the bake is current: all 16 Dellhollow cameras agree with their plates
to 0.0000 u, and old-tool vs new-tool output for Dellhollow is byte-identical.
Emberbrook's routes went from `inFrame: 0%` on six of seven shots to 100% on all seven.

=== 6. THE STANDING RED EVERYBODY ATTRIBUTES IS ONE FILE, AND HERE IS THE NUMBER ===
`assets/scenes/emb-cine/scene.glb` is the collision every cinematic camera loads and it is
a 07-31T04:53 export of the 1x town. cine_test and scenegraph_derive both measure against
it (correctly — it is what the player collides with), so the shipped scene graph is derived
from 1x collision and is missing two of the town's seven cuts.
  MEASURED BY SUBSTITUTION (emb-townwalk's current GLB copied in, gates run, both files
restored and sha256-verified identical):

                          shipped (stale 1x collision)   with a current collision bundle
     slice_test              668 ok / 18 FAILED             **740 ok / 0 FAILED**
     cine_test emberbrook    253 ok / 54 FAILED              332 ok /  8 FAILED
     seam_walk emberbrook    5/10 journeys                  **10/10 PASS**

The 8 that remain are ALL the CHAIN section — baked==solved — i.e. the plate bake, which is
the dressing lane's and was explicitly out of scope. **The standing 15-red slice_test
baseline is not a defect anyone has to chase: it is one stale GLB, and
`cine_bake.py --town emberbrook --glb` (a collision export, no Cycles render) clears it.**
NOT RUN HERE: the master is the dressing lane's file, a dressing render held it at the
time, and swap was at 88% against the 75% cap. Handed to main as the one unblocking action.

=== 7. WHAT IS LEFT STANDING, WITH ITS MEASUREMENT ===
- `walk_pad_pips-den` (rt x 77.2..80.1, z -49.2..-46.7) OVERLAPS the pond lane's ribbon
  (z -47.9..-45.4 through the same x). EVERY seam position from t=0.63 to 0.97 crosses one
  path or another; 0.78 is chosen because the den is pondlane's OWN landmark (being cut
  into pondlane while walking to it is correct) whereas every t past 0.80 crosses
  `pond-jetty__brook-bridge`, which is pondlane at both ends. The den's own stamp says it
  is "under the bank, hidden from the lane" — builder's lane.
- Town-wide mismatch 4.3 m against a 4.1 m budget: 0.2 m over, on the town's ONE remaining
  endpoint seam. An internal split at t=0.19 was TRIED and measured worse (2 failures -> 15,
  the walk oscillates), and reverted.
- The plaza floor has a 1 m slot cut in it on the north lane's centreline at (64-65, 55) —
  the ribbon's footprint, removed one metre before the ribbon starts. One searched arrival
  override (0.78 m teleport, clears the band by 2.26 m against a 1.6 m target); the other
  four 1x overrides are WITHDRAWN, not rescaled, because an override is a point that was
  PROVED to satisfy four properties of a floor that has been rebuilt twice since.

DELLHOLLOW UNTOUCHED AND RE-VERIFIED: cine_test 657/0, seam_test 294/0, seam_walk 9/9.
Its routes file was re-derived because it was already 154 scalar fields stale against the
map — a build artifact with a `--check` gate, not a hand-edited file.
