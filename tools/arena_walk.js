// ARENA WALK — prove the 3D battle arena INSIDE THE REAL GAME, not in the mock.
//
// The mock (tools/ui_mock.html) proved the stage: it boots the real modules against
// the real data and parks the screen so it can be photographed. What it cannot prove
// is INTEGRATION — that the encounter director fires organically while you walk, that
// the fade hands over to the arena, that UILOCK actually freezes the world, that the
// music wrap composed with the stage instead of fighting it, that world state is
// applied on the way out, and that the arena is GONE afterwards. Those only exist on
// play3d.html, so this runs there.
//
// Companion to tools/cine_walk.js and tools/slice_walk.js, and written in their
// idiom deliberately: a window.* object you paste into the play3d console, or drive
// over CDP (tools/arena_playtest.mjs does exactly that, headless).
//
//   await ARENAWALK.organic(opts)  walk a hostile zone until the DIRECTOR fires,
//                                  then record the whole battle: lock, stage, tiers,
//                                  projection, outro, GS deltas, teardown
//   await ARENAWALK.serial(n)      n battles back to back; WebGL contexts + heap
//   await ARENAWALK.nogl()         Battle.stage3d=false — a full battle on the DOM stage
//   ARENAWALK.glProbe()            how many fresh WebGL contexts this page can still
//                                  hand out (the leak detector; see below)
//   ARENAWALK.report               everything recorded, as JSON
//
// WHY COUNTERS AND NOT SCREENSHOTS: rAF is throttled to nothing in a background tab
// and a screenshot of one is stale (slice finding 7, and the reason cine_walk reads
// pixels instead of pictures). Everything here is a number read from the live page.
window.ARENAWALK = (function () {
  'use strict';

  const rep = { started: new Date().toISOString(), runs: [], notes: [] };
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const note = (s) => { rep.notes.push(s); return s; };
  const num = (v, d) => (typeof v === 'number' && isFinite(v) ? v : d);

  // ---- THE LEAK DETECTOR ---------------------------------------------------
  // There is no API for "how many WebGL contexts are alive". But a browser has a
  // hard cap (Chrome: 16) and evicts the oldest when you pass it — so "how many
  // fresh contexts can I still get?" IS the measurement. Run it before and after
  // N battles: if the arena leaked a context per battle, the second number drops.
  // Every probe context is explicitly lost again so the probe itself cannot be
  // the leak it is looking for.
  function glProbe(max) {
    max = max || 12;
    const held = [], lost = [];
    let n = 0;
    for (let i = 0; i < max; i++) {
      const c = document.createElement('canvas');
      c.width = c.height = 8;
      const gl = c.getContext('webgl') || c.getContext('experimental-webgl');
      if (!gl) break;
      held.push(gl); n++;
    }
    for (const gl of held) {
      const ext = gl.getExtension('WEBGL_lose_context');
      if (ext) { try { ext.loseContext(); lost.push(1); } catch (e) { } }
    }
    return { obtained: n, released: lost.length, of: max };
  }

  function heapMB() {
    try {
      if (typeof gc === 'function') { gc(); gc(); }
      const m = performance.memory;
      return m ? +(m.usedJSHeapSize / 1048576).toFixed(1) : null;
    } catch (e) { return null; }
  }

  // ---- live readings -------------------------------------------------------
  const glCanvases = () => document.querySelectorAll('canvas.ebb-gl').length;
  const battleRoots = () => document.querySelectorAll('.ebb-root').length;
  function stageInfo() {
    try {
      const d = window.Battle && window.Battle._debug();
      return (d && d.stage3d) || null;
    } catch (e) { return null; }
  }
  // Are the DOM anchors actually being driven by the 3D projection? A foe element
  // in arena mode is positioned every frame from stage.anchor(); if the projection
  // pass were dead it would sit at left:0 with no height. This reads the styles the
  // pass writes, which is the only honest proof that 2D and 3D are joined.
  function projection() {
    const els = [...document.querySelectorAll('.ebb-root.ebb-3d .ebb-foe')];
    if (!els.length) return { anchors: 0, driven: 0, sample: null };
    let driven = 0, sample = null;
    for (const el of els) {
      const L = parseFloat(el.style.left), T = parseFloat(el.style.top), H = parseFloat(el.style.height);
      const ok = isFinite(L) && isFinite(T) && isFinite(H) && H > 12 && L !== 0;
      if (ok) driven++;
      if (!sample) sample = { left: +(+L).toFixed(1), top: +(+T).toFixed(1), height: +(+H).toFixed(1) };
    }
    return { anchors: els.length, driven, sample };
  }
  function musicNow() {
    try {
      const M = window.Music;
      if (!M || !M._debug) return null;
      const d = M._debug();
      return { current: d.current && d.current.id ? d.current.id : d.current,
               battle: d.battle, sting: d.sting, armed: d.armed,
               parked: d.parked ? d.parked.id : null, ctx: d.ctx, disabled: d.disabled };
    } catch (e) { return null; }
  }
  function gsNow() {
    const G = window.GS;
    if (!G || !G.ok) return null;
    const p = G.state.party.map(c => ({ id: c.id, hp: c.hp, xp: c.xp, level: c.level }));
    return { gold: G.state.gold, party: p, inv: Object.assign({}, G.state.inventory) };
  }

  // ---- walking until the DIRECTOR fires ------------------------------------
  // Not Battle.demo(): the point is the organic path — the director accumulating
  // real distance from real physics in a real hostile zone, and calling
  // Battle.start itself through its own fade.
  const HOSTILE = ['meadow', 'forest', 'crag', 'water'];
  const isHostile = z => HOSTILE.includes(z);

  // FIND DEEP HOSTILE GROUND, not merely hostile ground. The first version of
  // this walked to the nearest hostile cell and then ping-ponged across its
  // boundary — and the director grants grace every time you arrive from safety,
  // so a walker that keeps crossing back onto a road accumulates NOTHING. (That
  // is canon, not a bug: "roads and their shoulders are the only quiet.") So the
  // target is scored by how much hostile ground surrounds it.
  function findHostile(scan) {
    const S = window.SIM;
    if (!S || !S.zone) return null;
    const p = S.pos();
    const depth = (x, z) => {
      let n = 0;
      for (let a = 0; a < 8; a++) {
        const th = (a / 8) * Math.PI * 2;
        for (const r of [4, 9, 15]) {
          if (isHostile(S.zone(x + Math.cos(th) * r, z + Math.sin(th) * r))) n++;
        }
      }
      return n;                                     // 0..24
    };
    let best = null;
    const here = S.zone();
    if (isHostile(here)) best = { x: p.x, z: p.z, zone: here, moved: false, depth: depth(p.x, p.z) };
    const step = 6, rings = scan || 20;
    for (let r = 1; r <= rings; r++) {
      for (let a = 0; a < 16; a++) {
        const th = (a / 16) * Math.PI * 2;
        const x = p.x + Math.cos(th) * r * step, z = p.z + Math.sin(th) * r * step;
        const zn = S.zone(x, z);
        if (!isHostile(zn)) continue;
        if (!(S.walkFloors(x, z) || []).length && S.ground(x, z, p.y) == null) continue;
        const d = depth(x, z);
        if (!best || d > best.depth) best = { x, z, zone: zn, moved: true, depth: d };
        if (best.depth >= 22) return best;          // deep enough, stop looking
      }
    }
    return best;
  }

  // Pick a heading whose next ~14 u stay hostile. Re-picked whenever the ground
  // under the player turns safe, which is what keeps the accumulator running.
  function bestHeading() {
    const S = window.SIM, p = S.pos();
    let best = [1, 0], bestScore = -1;
    for (let a = 0; a < 16; a++) {
      const th = (a / 16) * Math.PI * 2, dx = Math.cos(th), dz = Math.sin(th);
      let score = 0;
      for (let d = 2; d <= 14; d += 2) {
        if (isHostile(S.zone(p.x + dx * d, p.z + dz * d))) score++; else break;
      }
      if (score > bestScore) { bestScore = score; best = [dx, dz]; }
    }
    return { dir: best, score: bestScore };
  }

  // Walk until `pred` says stop, steering to stay on hostile ground.
  async function walkUntil(pred, opts) {
    opts = opts || {};
    const S = window.SIM;
    const maxTicks = opts.maxTicks || 20000;
    let ticks = 0, repicks = 0, stalls = 0;
    let head = bestHeading().dir;
    let last = S.pos();
    while (ticks < maxTicks) {
      if (pred()) return { ticks, repicks, stalls, stopped: 'pred' };
      S.move(head[0], head[1], 25);
      ticks += 25;
      const p = S.pos();
      // A heading that does not actually move the player is a wall; re-pick.
      if (Math.hypot(p.x - last.x, p.z - last.z) < 0.2) { stalls++; head = bestHeading().dir; repicks++; }
      else if (!isHostile(S.zone())) { head = bestHeading().dir; repicks++; }
      last = p;
      if (stalls > 30) return { ticks, repicks, stalls, stopped: 'walled-in' };
      if (ticks % 500 === 0) await sleep(0);      // let the battle's own timers run
    }
    return { ticks, repicks, stalls, stopped: 'max-ticks' };
  }

  // THE PEDOMETER FALLBACK. Encounters.tick(dist) takes an explicit distance —
  // that is its documented signature, for "a caller that already knows how far
  // the player moved". If the terrain will not let a headless walker cover ground
  // (steep valley, no walk floor, boxed in), the director is fed distance
  // directly instead. Everything downstream is untouched: the same zone, the same
  // seeded rolls, the same grace, the same fire() into the same Battle.start. The
  // report records WHICH pedometer was used, because "we walked there" and "we
  // told it we walked there" are not the same claim.
  async function pedometer(pred, opts) {
    opts = opts || {};
    const E = window.Encounters;
    const max = opts.maxSteps || 4000;
    for (let i = 0; i < max; i++) {
      if (pred()) return { steps: i, stopped: 'pred' };
      E.tick(E.STEP_UNIT);
      if (i % 50 === 0) await sleep(0);
    }
    return { steps: max, stopped: 'max-steps' };
  }

  // ---- WARM THE ASSET CACHE -----------------------------------------------
  // At speed 0 a battle is over in well under a second, which is less time than a
  // 3.5 MB rig takes to arrive — so an un-warmed automated run photographs the
  // PROXY tier and proves nothing about the models. That is the proxy tier doing
  // exactly its job (the arena is never empty), but it is not what we came to
  // test. Warming fetches the same URLs the stage will ask for, so the browser
  // cache answers instantly and the run exercises the tier a real second battle
  // in a real session would see. Nothing about the stage is bypassed.
  async function warm() {
    const A = window.BattleStage3D && window.BattleStage3D.art;
    if (!A) return { warmed: 0, reason: 'stage module not loaded yet' };
    const G = window.GS;
    const ids = (G && G.ok && G.data.monsters) ? Object.keys(G.data.monsters.monsters) : [];
    const urls = [A.charModel].concat(ids.map(id => A.base + A.modelDir + id + '.glb'));
    let ok = 0;
    await Promise.all(urls.map(u => fetch(u).then(r => { if (r.ok) { ok++; return r.arrayBuffer(); } })
      .catch(() => { })));
    return { warmed: ok, of: urls.length };
  }

  // ---- ONE ORGANIC BATTLE, FULLY INSTRUMENTED ------------------------------
  async function organic(opts) {
    opts = opts || {};
    const B = window.Battle, E = window.Encounters, S = window.SIM, G = window.GS;
    const run = { kind: 'organic', ok: false, steps: [] };
    const step = (name, data) => { run.steps.push(Object.assign({ step: name }, data)); return data; };
    if (!B || !E || !S || !G) { run.error = 'missing module'; rep.runs.push(run); return run; }

    // AUTOMATED RUNS MUST PASS speed:0 (Battle's own harness canon): event pacing
    // is setTimeout-based, and Chrome throttles timers to one wake a minute after
    // ~5 minutes hidden, so any speed > 0 takes tens of minutes in a headless tab.
    E.attach((x, z) => S.zone(x, z), () => S.pos(), Object.assign({}, opts.attach, {
      battleOpts: Object.assign({ speed: 0, autoplay: true }, opts.battleOpts),
    }));
    E.setEnabled(true);

    // The stage module is fetched lazily on the first battle, so warming needs it
    // present; pull it the same way battle_turnbased does and then warm the models.
    if (opts.warm !== false && !window.BattleStage3D && window.THREE) {
      await new Promise((done) => {
        const s = document.createElement('script');
        s.src = 'js/battle_stage3d.js'; s.onload = s.onerror = done;
        document.head.appendChild(s);
      });
    }
    run.warm = (opts.warm === false) ? { skipped: true } : await warm();

    const spot = findHostile();
    if (!spot) { run.error = 'no hostile zone reachable'; rep.runs.push(run); return run; }
    if (spot.moved) S.tp(spot.x, spot.z);
    step('placed', { zone: S.zone(), pos: S.pos(), depth: spot.depth,
                     walkedTo: spot.moved, glCanvasesBefore: glCanvases() });

    const before = gsNow();
    const musicBefore = musicNow();
    const d0 = E._debug();

    // --- walk until the director fires ------------------------------------
    const walk = await walkUntil(() => B.active, { maxTicks: opts.maxTicks || 30000 });
    let pedo = null, how = 'walked';
    step('walked', { ticks: walk.ticks, repicks: walk.repicks, stalls: walk.stalls,
                     stopped: walk.stopped, fired: !!B.active, director: E._debug() });
    if (!B.active && opts.pedometer !== false) {
      // the terrain would not cooperate; feed the director distance directly
      how = 'pedometer';
      pedo = await pedometer(() => B.active, {});
      step('pedometer', { steps: pedo.steps, stopped: pedo.stopped,
                          fired: !!B.active, director: E._debug() });
    }
    run.pedometer = how;
    if (!B.active) { run.error = 'director never fired (walk ' + walk.ticks + ' ticks, ' +
      (pedo ? 'pedometer ' + pedo.steps + ' steps' : 'no pedometer') + ')'; rep.runs.push(run); return run; }

    // --- THE FREEZE, MEASURED SYNCHRONOUSLY -------------------------------
    // Right here, with no await between the check and the test, Battle.active is
    // certainly true — so this is the one place the freeze can be measured without
    // racing the battle's own end. (The first version sampled it inside an await
    // loop and read UILOCK *after* the fight had finished unlocking, which failed
    // the product for the harness's mistake.) phys() returns the frozen shape
    // under UILOCK, so 40 hard ticks of held keys must move the player by nothing.
    // SIM.move, not SIM.tick: move drives phys() with an explicit world direction
    // and renders nothing, where tick() calls R.render(scene, cam) — and in rt=1
    // mode play3d never populates `cam` (the real-time camera is window._rtCam,
    // used only by loop()), so tick() throws inside three. Pre-existing harness
    // limitation of that method, not of the freeze; move is the sharper test
    // anyway, because it hands phys() a direction rather than hoping a key sticks.
    const posAtStart = S.pos();
    S.move(1, 1, 40);
    const posAfterShove = S.pos();
    const shoved = +Math.hypot(posAfterShove.x - posAtStart.x, posAfterShove.z - posAtStart.z).toFixed(4);
    step('fired', {
      uilock: window.UILOCK.active(), battleActive: B.active,
      zone: E._debug().zone, music: musicNow(),
      shovedBy: shoved, ticksShoved: 40,
    });

    // --- WATCH ON A TIMER, NOT ON A LOOP INDEX ----------------------------
    // At speed 0 the fight itself resolves in microtasks; only the fades and the
    // asset loads keep Battle.active true, and how long that lasts depends on how
    // fast a 3.5 MB rig comes off disk. Any sampler keyed to iteration numbers is
    // therefore sampling a window it cannot predict. This records maxima and
    // firsts/lasts, and only ever samples while the battle is genuinely up.
    const w = { stage: null, projection: null, nums: 0, samples: 0, lockedSamples: 0,
                unlockedWhileActive: 0, framesFirst: null, framesLast: null, tiersLast: null };
    const watch = setInterval(() => {
      if (!B.active) return;                              // never sample past the end
      w.samples++;
      if (window.UILOCK.active()) w.lockedSamples++; else w.unlockedWhileActive++;
      const st = stageInfo();
      if (st && st.live) {
        w.stage = st; w.tiersLast = st.tiers;
        const f = num(st.frames, null);
        if (f != null) { if (w.framesFirst == null) w.framesFirst = f; w.framesLast = f; }
        const pr = projection();
        if (pr.driven > 0) w.projection = pr;
      }
      w.nums = Math.max(w.nums, document.querySelectorAll('.ebb-num').length);
    }, 20);

    for (let i = 0; i < 1200 && B.active; i++) await sleep(25);
    clearInterval(watch);
    await sleep(500);                                        // the exit fade + teardown

    step('during', {
      stage: w.stage, tiersLast: w.tiersLast, projection: w.projection, damageNumbersSeen: w.nums,
      samples: w.samples, lockedSamples: w.lockedSamples,
      unlockedWhileActive: w.unlockedWhileActive,
      uilockHeldThroughout: w.samples > 0 && w.unlockedWhileActive === 0,
      framesFirst: w.framesFirst, framesLast: w.framesLast,
      framesRendered: (w.framesFirst != null && w.framesLast != null) ? w.framesLast - w.framesFirst : null,
      // "did the arena actually render, repeatedly" — a mounted-but-stalled stage
      // reports live exactly like a healthy one, and only this separates them
      arenaRendering: (w.framesFirst != null && w.framesLast != null) ? w.framesLast > w.framesFirst : null,
      playerMoved: shoved,
      music: musicNow(),
    });

    const after = gsNow();
    step('after', {
      battleActive: B.active, uilock: window.UILOCK.active(),
      glCanvases: glCanvases(), battleRoots: battleRoots(),
      last: B.last ? { outcome: B.last.outcome, xp: B.last.xp, gold: B.last.gold,
                       drops: B.last.drops, turns: B.last.turns } : null,
      gsBefore: before, gsAfter: after,
      goldDelta: after && before ? after.gold - before.gold : null,
      xpDelta: after && before ? after.party[0].xp - before.party[0].xp : null,
      music: musicNow(), musicBefore: musicBefore,
    });

    // --- the verdicts ------------------------------------------------------
    const d = run.steps.find(s => s.step === 'during') || {};
    const a = run.steps.find(s => s.step === 'after') || {};
    const f = run.steps.find(s => s.step === 'fired') || {};
    run.checks = {
      directorFired: true,
      uilockHeldAtFire: f.uilock === true,
      uilockHeldThroughout: d.uilockHeldThroughout === true,
      worldFrozen: d.playerMoved != null && d.playerMoved < 0.001,
      arenaLive: !!(d.stage && d.stage.live),
      arenaRendering: d.arenaRendering === true,
      framesRendered: d.framesRendered,
      tiers: d.tiersLast || (d.stage ? d.stage.tiers : null),
      projectionDriven: !!(d.projection && d.projection.driven > 0),
      damageNumbersRendered: d.damageNumbersSeen > 0,
      outcomeReported: !!(a.last && a.last.outcome),
      worldStateApplied: a.goldDelta != null && (a.last && a.last.outcome === 'victory'
        ? a.goldDelta === a.last.gold : true),
      arenaDestroyed: a.glCanvases === 0 && a.battleRoots === 0,
      unlockedAfter: a.uilock === false && a.battleActive === false,
    };
    run.ok = Object.values(run.checks).every(v => v !== false);
    rep.runs.push(run);
    return run;
  }
  // The stage's OWN rendered-frame counter, off Battle's debug surface. A stage
  // that mounted and then stalled (a thrown rAF, a lost context) reports `live`
  // exactly like a healthy one; only this number separates them.
  function arenaFrames() {
    try {
      const d = window.Battle._debug().stage3d;
      return d && d.live ? num(d.frames, null) : null;
    } catch (e) { return null; }
  }

  // ---- N BATTLES BACK TO BACK ---------------------------------------------
  // The teardown test. Three is the coordinator's number; the probe below would
  // catch a leak at one, because a leaked context shows up as one fewer fresh
  // context the probe can obtain.
  async function serial(n, opts) {
    n = n || 3;
    const B = window.Battle;
    const run = { kind: 'serial', n, ok: false, battles: [] };
    run.glBefore = glProbe();
    run.heapBefore = heapMB();
    for (let i = 0; i < n; i++) {
      const zone = HOSTILE[i % HOSTILE.length];
      const t0 = performance.now();
      let r = null, err = null;
      // watch the tiers and the frame counter WHILE the battle runs — after it
      // ends the stage is gone and both are unreadable
      const w = { tiers: null, framesFirst: null, framesLast: null };
      const watch = setInterval(() => {
        if (!B.active) return;
        const st = stageInfo();
        if (st && st.live) {
          w.tiers = st.tiers;
          const f = num(st.frames, null);
          if (f != null) { if (w.framesFirst == null) w.framesFirst = f; w.framesLast = f; }
        }
      }, 15);
      try {
        r = await B.demo(zone, Object.assign({ speed: 0, autoplay: true }, opts));
      } catch (e) { err = String(e); }
      clearInterval(watch);
      const ms = Math.round(performance.now() - t0);
      await sleep(350);
      run.battles.push({
        i, zone, ms,
        outcome: r ? r.outcome : null, turns: r ? r.turns : null, error: err,
        tiers: w.tiers,
        frames: (w.framesFirst != null && w.framesLast != null) ? w.framesLast - w.framesFirst : null,
        // renders per second while the arena was up — on swiftshader this is single
        // digits and that is the HARNESS, not the game; it is recorded so nobody
        // reads a small frame count as a stalled stage
        fps: (w.framesLast != null && ms > 0)
          ? +(((w.framesLast - (w.framesFirst || 0)) / (ms / 1000))).toFixed(1) : null,
        glCanvasesAfter: glCanvases(), battleRootsAfter: battleRoots(),
        active: B.active, uilock: window.UILOCK.active(),
        // Heap AFTER each battle. The first battles fill caches that are meant to
        // be permanent — the GLB ArrayBuffer cache, ui_kit's keyed pose canvases,
        // three's shader programs — so a large delta across battle 1 is COST, not
        // leak. A leak is the heap still climbing once those are warm, which is
        // what the tail-vs-head comparison below actually measures.
        heapMB: heapMB(),
      });
    }
    // Did the MODEL tier ever land? At speed 0 a fight can finish before a 3.5 MB
    // rig parses, and the proxy tier carrying it is correct behaviour — but the
    // report has to say which one it actually photographed.
    run.tiersByBattle = run.battles.map(b => b.tiers);
    run.everSawModelTier = run.battles.some(b => b.tiers &&
      Object.values(b.tiers).some(t => t === 'model'));
    await sleep(500);
    run.glAfter = glProbe();
    run.heapAfter = heapMB();
    run.checks = {
      allRan: run.battles.every(b => b.outcome && !b.error),
      allTornDown: run.battles.every(b => b.glCanvasesAfter === 0 && b.battleRootsAfter === 0),
      allUnlocked: run.battles.every(b => b.active === false && b.uilock === false),
      // A leaked context per battle would show as fewer obtainable afterwards.
      noContextLeak: run.glAfter.obtained >= run.glBefore.obtained,
      heapDeltaMB: (run.heapAfter != null && run.heapBefore != null)
        ? +(run.heapAfter - run.heapBefore).toFixed(1) : null,
      tiersByBattle: run.tiersByBattle,
      everSawModelTier: run.everSawModelTier,
      msPerBattle: run.battles.map(b => b.ms),
      fpsPerBattle: run.battles.map(b => b.fps),
      heapPerBattleMB: run.battles.map(b => b.heapMB),
    };
    // THE LEAK QUESTION, ASKED PROPERLY. Total heap growth conflates one-time
    // cache fill (3.5 MB of rig, keyed pose canvases, compiled shaders — all
    // deliberately permanent) with a per-battle leak. So compare the SECOND HALF
    // of the run against the first: once the caches are warm, a healthy arena
    // should be flat, and anything that keeps climbing is the real thing.
    const hs = run.battles.map(b => b.heapMB).filter(v => v != null);
    if (hs.length >= 4) {
      const half = Math.floor(hs.length / 2);
      const head = hs.slice(0, half), tail = hs.slice(half);
      const avg = a => a.reduce((s, v) => s + v, 0) / a.length;
      run.checks.warmHeapDriftMB = +(avg(tail) - avg(head)).toFixed(1);
      // a couple of MB of drift is ordinary GC noise; a per-battle leak of a whole
      // scene would be tens
      run.checks.heapFlatWhenWarm = Math.abs(run.checks.warmHeapDriftMB) < 12;
    } else if (hs.length) {
      run.checks.warmHeapDriftMB = null;
      run.checks.heapFlatWhenWarm = null;         // need >= 4 battles to say
    }
    run.ok = run.checks.allRan && run.checks.allTornDown && run.checks.allUnlocked &&
             run.checks.noContextLeak && run.checks.heapFlatWhenWarm !== false;
    rep.runs.push(run);
    return run;
  }

  // ---- THE NO-WEBGL PATH, ON THE REAL PAGE --------------------------------
  // Battle.stage3d = false is exactly the flag a page that cannot hand out a GL
  // context produces, so this is the fallback itself and not a mock of it.
  async function nogl(opts) {
    const B = window.Battle;
    const run = { kind: 'nogl', ok: false };
    const prev = B.stage3d;
    B.stage3d = false;
    try {
      const t0 = performance.now();
      const r = await B.demo('forest', Object.assign({ speed: 0, autoplay: true }, opts));
      await sleep(300);
      run.result = r ? { outcome: r.outcome, turns: r.turns, xp: r.xp, gold: r.gold } : null;
      run.ms = Math.round(performance.now() - t0);
      run.glCanvases = glCanvases();
      run.battleRoots = battleRoots();
      run.stage = stageInfo();
      run.checks = {
        battleCompleted: !!(r && r.outcome),
        domStageUsed: !(run.stage && run.stage.live),
        noGlCanvas: run.glCanvases === 0,
        cleanedUp: run.battleRoots === 0 && B.active === false && window.UILOCK.active() === false,
      };
      run.ok = Object.values(run.checks).every(Boolean);
    } catch (e) { run.error = String(e); }
    B.stage3d = prev;
    rep.runs.push(run);
    return run;
  }

  // ---- MUSIC INTERPLAY ------------------------------------------------------
  // music.js self-arms by WRAPPING Battle.start. The stage is created INSIDE
  // Battle.start, so the two compose by construction — but "by construction" is
  // an argument, not evidence, so this samples the music state at each phase of a
  // battle that is running the 3D arena.
  async function music(opts) {
    const B = window.Battle, M = window.Music;
    const run = { kind: 'music', ok: false, phases: [] };
    if (!M || !M._debug) { run.error = 'music.js not on this page'; rep.runs.push(run); return run; }
    // SILENT BY POLICY (coordinator standing order 2026-07-31): the state machine
    // is what is under test — which track is slotted, whether the battle ducked,
    // whether the fanfare fired — and none of that needs a speaker. Mute before
    // anything can sound, and restore afterwards.
    const vol0 = (M.current && M._debug().volume);
    if (opts.mute !== false) { try { M.mute(true); } catch (e) { } }
    const field = musicNow();
    run.phases.push({ phase: 'field', music: field, muted: opts.mute !== false });

    // SAMPLE CONTINUOUSLY, NEVER ON A LOOP INDEX. At speed 0 the fight itself
    // resolves in microtasks — only the 350 ms entry fade and the outro keep the
    // battle "active" at all — so a sampler that waited for iteration 10 of a
    // 20 ms loop could miss the entire battle and then read phases[1] as
    // undefined. This watches on its own timer and records the maxima it saw.
    const seen = { duck: false, sting: null, stageLive: false, tiers: null, glCanvas: 0, samples: 0 };
    const watch = setInterval(() => {
      seen.samples++;
      const m = musicNow();
      if (m && m.battle) seen.duck = true;
      if (m && m.sting) seen.sting = m.sting;
      const st = stageInfo();
      if (st && st.live) { seen.stageLive = true; seen.tiers = st.tiers; }
      seen.glCanvas = Math.max(seen.glCanvas, glCanvases());
    }, 15);

    let r = null;
    try { r = await B.demo('meadow', Object.assign({ speed: 0, autoplay: true }, opts)); }
    catch (e) { run.error = String(e); }
    await sleep(900);                       // let the fanfare start and the field come back
    clearInterval(watch);
    run.phases.push({ phase: 'during', seen: seen });
    const after = musicNow();
    run.phases.push({ phase: 'after', music: after, outcome: r ? r.outcome : null });

    run.checks = {
      // music.js self-arms by WRAPPING Battle.start; the stage is created INSIDE
      // Battle.start, so the two compose rather than collide — this is the check
      // that says so with evidence instead of with an argument.
      armed: !!(field && field.armed),
      duckedOnBattle: seen.duck,
      stageWasLiveDuringMusic: seen.stageLive,
      battleCompleted: !!(r && r.outcome),
      fieldReturned: !!(after && after.battle === false),
    };
    run.ok = run.checks.armed && run.checks.duckedOnBattle &&
             run.checks.stageWasLiveDuringMusic && run.checks.battleCompleted;
    if (opts.mute !== false) { try { M.mute(false); M.setVolume(vol0); } catch (e) { } }
    rep.runs.push(run);
    return run;
  }

  return {
    organic, serial, nogl, music, warm, glProbe, heapMB, projection, stageInfo, musicNow, gsNow,
    findHostile, bestHeading, walkUntil, pedometer,
    get report() { return rep; },
    summary() {
      const out = { ok: true, runs: {} };
      for (const r of rep.runs) {
        out.runs[r.kind] = { ok: r.ok, checks: r.checks || null, error: r.error || null };
        if (!r.ok) out.ok = false;
      }
      out.notes = rep.notes;
      return out;
    },
  };
})();
