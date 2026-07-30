// encounters.js — window.Encounters: THE ENCOUNTER DIRECTOR (battle-core agent).
//
// Consumes the player's zone stream (the same ground truth as SIM.zone(x,z)) and
// decides when a battle happens. It is the ONLY thing that knows how the world
// and a battle are joined, and it joins them through two narrow contracts:
// Battle.start(spec) and GS.applyBattleResult(result).
//
//   Encounters.attach(getZone, getPos, opts)   // both are functions; opts optional
//   Encounters.tick(dist?)                     // per physics step; measures its own travel
//   Encounters.setEnabled(bool)
//   Encounters._debug()
//
// A "STEP" IS ONE WORLD UNIT OF TRAVEL, NOT ONE PHYSICS TICK (ratified — see
// docs/plans/battle-core-design.md §0a). phys() runs at 60 Hz and SPD is 0.075 u,
// so a per-tick roll at encounters.json's 0.02 would mean a battle every 0.83 s.
// At 1.0 u per step, meadow grace 30 = 30 u walked and the mean post-grace gap is
// 50 u on a 280 u tile — three or four encounters per crossing. Because the
// director measures distance from getPos() itself, the movement-loop hook is the
// zero-argument Encounters.tick() and the JSON numbers survive an SPD retune.
//
// EVERYTHING IS SEEDED: rolls come from mulberry32(hashSeed(runSeed, zone, step)),
// so a headless walk replays exactly. No Math.random, no Date.now.
//
// NO-OPS COMPLETELY (and says why in _debug) when GS.ok is false, Battle is
// absent, the kernel is absent, or the zone has chancePerStep 0. Roads and towns
// are safe by construction: road ships rate 0 and an UNKNOWN zone name is treated
// as safe rather than defaulted, so a new zone type can never spawn monsters by
// accident.
(function () {
  'use strict';

  const STEP_UNIT = 1.0;        // world units per encounter step (ratified)
  const TELEPORT_U = 3.0;       // a one-tick jump this big is a handoff, not a walk
  const DEFAULT_SEED = 0xEB1A77;  // run seed; deterministic by default, opts.seed to vary
  const DEFAULT_GRACE = 20;

  let A = null;                 // the single attachment
  let pinged = false;           // GS.on('levelup') subscribed once (GS.on has no off)

  const num = (v, d) => (typeof v === 'number' && isFinite(v)) ? v : d;

  function gs() { return typeof window !== 'undefined' ? window.GS : null; }
  function rules() { return typeof window !== 'undefined' ? window.Rules : null; }
  function battle() { return typeof window !== 'undefined' ? window.Battle : null; }

  // why the director is inert, or null when it is live
  function blockedReason() {
    if (!A) return 'not-attached';
    if (!A.enabled) return 'disabled';
    if (!rules()) return 'no-rules-kernel';
    if (!battle() || !battle().start) return 'no-battle-module';
    const G = gs();
    if (!G || !G.ok) return 'gs-not-ready';
    if (!G.data || !G.data.encounters || !G.data.encounters.zones) return 'no-encounter-data';
    if (typeof A.getZone !== 'function' || typeof A.getPos !== 'function') return 'no-world-source';
    return null;
  }
  function zoneDef(z) {
    const G = gs();
    if (!z || !G || !G.data || !G.data.encounters) return null;
    return G.data.encounters.zones[z] || null;
  }
  function hostile(zd) { return !!(zd && num(zd.chancePerStep, 0) > 0 && (zd.groups || []).length); }

  // ---- grace ---------------------------------------------------------------
  // Re-armed on attach, post-battle, any teleport, and entry from a SAFE zone
  // (never on a hostile -> hostile boundary — see the zone-change block in
  // tick()). Grace is the zone's own number: walking out of a town into the
  // meadow gives you 30 u of quiet, which is what keeps a doorway from being an
  // ambush. Zeroing acc here is part of the same promise — a fresh grace with a
  // nearly-full accumulator would roll the moment it expired.
  function regrace(why) {
    if (!A) return;
    const zd = zoneDef(A.zone);
    A.graceLeft = num(zd && zd.grace, DEFAULT_GRACE);
    A.acc = 0;
    A.lastGrace = why;
  }

  function rememberHome(p) {
    if (!A) return;
    if (p) { A.home = { x: p.x, y: p.y, z: p.z }; return; }
    // the scene-graph arrival point is the truest "last spawn" the page knows
    try {
      const arr = window.SIM && window.SIM.arrival && window.SIM.arrival();
      if (arr) { A.home = { x: arr[0], y: arr[1], z: arr[2] }; return; }
    } catch (e) { /* SIM may not be up */ }
    const q = A.getPos && A.getPos();
    if (q) A.home = { x: q.x, y: q.y, z: q.z };
  }

  // ---- level-up ping -------------------------------------------------------
  function subscribePings() {
    if (pinged) return;
    const G = gs(); if (!G || !G.on) return;
    pinged = true;
    G.on('levelup', (events) => {
      const B = battle(); if (!B || !B.toast || !events || !events.length) return;
      const txt = events.map(e => {
        const d = G.data && G.data.growth.characters[e.char];
        return ((d && d.name) || e.char) + ' reached level ' + e.level;
      }).join(' · ');
      B.toast(txt, 3000);
    });
  }

  // ---- the battle round-trip ----------------------------------------------
  async function fire(zone, zd, step) {
    const R = rules(), B = battle(), G = gs();
    A.busy = true;
    try {
      const group = R.derive.pickGroup(zd, R.mulberry32(R.hashSeed(A.seed, zone, step, 'group')));
      if (!group || !group.length) return null;
      const spec = {
        zone: zone, group: group,
        seed: R.hashSeed(A.seed, zone, step, 'battle') >>> 0,
        backdrop: zd.battleBackdrop || zone,
      };
      A.battles++; A.lastSpec = spec;
      rememberHome();
      const result = await B.start(spec, null, A.opts.battleOpts || {});
      A.lastResult = result;
      if (!result) return null;
      // THE BOUNDARY: the battle reports, the world applies. Nothing else here
      // touches xp, gold, drops or hp.
      G.applyBattleResult(result);
      if (result.outcome === 'defeat') defeat(result);
      if (A.opts.onResult) { try { A.opts.onResult(result, spec); } catch (e) { console.error('[Encounters] onResult', e); } }
      return result;
    } catch (e) {
      console.error('[Encounters] battle failed', e);
      return null;
    } finally {
      A.busy = false;
      regrace('post-battle');
    }
  }

  // v1 DEFEAT — TODO(taste review): revive at 1 HP, lose half the purse, walk back
  // from the last spawn. No game-over screen, no save reload, no lost items: the
  // cheapest punishment that still stings. Whether the valley wants harsher (reload
  // last save) or softer (full heal, no gold loss) is a design call, not a code one —
  // the whole policy is these fifteen lines.
  function defeat(result) {
    const G = gs(), B = battle();
    const lost = Math.floor((G.state.gold || 0) / 2);
    // only the fallen are revived — 'defeat' means everyone is down today, but a
    // party-of-N rule change must not reset a survivor to 1 HP.
    for (const ch of G.activeParty()) if (ch.hp <= 0) G.setHp(ch.id, 1);
    if (lost > 0) G.addGold(-lost);
    const home = A.home;
    if (A.opts.respawn) { try { A.opts.respawn(home); } catch (e) { console.error('[Encounters] respawn', e); } }
    else if (home) {
      try { if (window.SIM && window.SIM.place) window.SIM.place([home.x, home.y, home.z]); }
      catch (e) { console.error('[Encounters] respawn', e); }
    }
    if (B && B.toast) B.toast('Overcome… you wake where you set out' + (lost > 0 ? ' (−' + lost + ' gold)' : ''), 3600);
  }

  // ===== API ================================================================
  const Encounters = window.Encounters = {
    version: 1,
    STEP_UNIT, TELEPORT_U,

    // getZone(x,z) -> zone name | null (SIM.zone), getPos() -> {x,y,z} (SIM.pos)
    attach(getZone, getPos, opts) {
      opts = opts || {};
      A = {
        getZone, getPos, opts,
        enabled: opts.enabled !== false,
        seed: (opts.seed != null ? opts.seed : DEFAULT_SEED) >>> 0,
        last: null, acc: 0, steps: 0, zone: null, graceLeft: DEFAULT_GRACE,
        rolls: 0, battles: 0, busy: false, force: false,
        home: null, lastGrace: 'attach', lastSpec: null, lastResult: null,
      };
      try { const p = getPos && getPos(); if (p) { A.last = { x: p.x, z: p.z }; A.zone = getZone(p.x, p.z); } } catch (e) { }
      regrace('attach');
      rememberHome();
      subscribePings();
      return Encounters;
    },

    // Called once per physics step. `dist` may be supplied by a caller that
    // already knows how far the player moved; otherwise it is measured from
    // getPos(), which is why the movement-loop hook takes no arguments.
    tick(dist) {
      const a = A;
      if (!a || !a.enabled || a.busy) return;
      const B = battle();
      if (B && B.active) { a.last = null; return; }     // a battle is up: re-baseline, never accumulate
      if (blockedReason()) return;

      let p;
      try { p = a.getPos(); } catch (e) { return; }
      if (!p) return;
      let d = dist;
      if (d == null) {
        if (!a.last) { a.last = { x: p.x, z: p.z }; return; }   // first tick after a jump: only baseline
        d = Math.hypot(p.x - a.last.x, p.z - a.last.z);
      }
      a.last = { x: p.x, z: p.z };
      if (!(d >= 0)) return;
      // A one-tick jump bigger than a sprint is a scene handoff, a respawn or a
      // teleport — not travel. Re-arm grace and move the respawn anchor with it.
      if (d > TELEPORT_U) {
        a.zone = safeZone(p);
        regrace('teleport');
        rememberHome(p);
        return;
      }
      // ---- ZONE CHANGE: grace comes from SAFETY, not from novelty ------------
      // Re-gracing on EVERY zone change made every terrain boundary an encounter-
      // free corridor: walking a shoreline, a treeline or a scree edge flips zone
      // more often than the grace it re-armed (20-30 u against a 1.25 u zone
      // cell), so 600 u of scenic walking produced ZERO rolls where a straight
      // line produced 120. That is not a clever exploit, it is what a player who
      // follows the pretty line gets by accident, and it reads as "battles are
      // broken". So: only arriving FROM a safe zone grants quiet. Hostile ->
      // hostile carries both the grace counter AND the accumulator straight
      // across, because you never stopped being in danger.
      // Hugging a ROAD still farms grace, and that is the design: roads are safe
      // by construction and the legibility programme rewards following them.
      // Safe zones are now the sole source of quiet.
      const z = safeZone(p);
      if (z !== a.zone) {
        const cameFromSafety = !hostile(zoneDef(a.zone));
        a.zone = z;
        if (cameFromSafety) regrace('zone-entry');
        else a.lastGrace = hostile(zoneDef(z)) ? 'carried' : 'entered-safety';
      }
      const zd = zoneDef(z);
      if (!hostile(zd)) return;                          // road, town, water-with-no-table, unknown
      const R = rules();
      a.acc += d;
      let guard = 64;                                    // a teleport-sized accumulator can't stall the tick
      while (a.acc >= STEP_UNIT && guard-- > 0) {
        a.acc -= STEP_UNIT;
        a.steps++;
        if (a.graceLeft > 0) { a.graceLeft--; continue; }
        a.rolls++;
        const hit = a.force || (R.mulberry32(R.hashSeed(a.seed, z, a.steps))() < num(zd.chancePerStep, 0));
        if (hit) {
          a.force = false;
          a.acc = 0;
          fire(z, zd, a.steps);                          // async; a.busy blocks re-entry immediately
          return;
        }
      }
    },

    setEnabled(v) { if (A) A.enabled = !!v; return !!(A && A.enabled); },

    // TEST/PLAYTEST: guarantee the next step past grace starts a battle. Used by
    // the integration test so a walk-until-encounter does not depend on luck.
    forceNext() { if (A) { A.force = true; A.graceLeft = 0; } return !!A; },

    // TEST/PLAYTEST: start a zone's encounter right now, bypassing the walk.
    fireNow(zone) {
      if (!A || blockedReason()) return null;
      const z = zone || A.zone;
      const zd = zoneDef(z);
      if (!hostile(zd)) { console.warn('[Encounters] zone not hostile:', z); return null; }
      return fire(z, zd, ++A.steps);
    },

    _debug() {
      const B = battle();
      return {
        attached: !!A, reason: blockedReason(), enabled: !!(A && A.enabled),
        zone: A && A.zone, steps: A && A.steps, rolls: A && A.rolls,
        battles: A && A.battles, grace: A && A.graceLeft, graceWhy: A && A.lastGrace,
        acc: A && +A.acc.toFixed(3), seed: A && A.seed, busy: !!(A && A.busy),
        stepUnit: STEP_UNIT, home: A && A.home,
        battleActive: !!(B && B.active),
        lastSpec: A && A.lastSpec, lastResult: A && A.lastResult,
        chance: (() => { const zd = A && zoneDef(A.zone); return zd ? num(zd.chancePerStep, 0) : 0; })(),
      };
    },
  };

  function safeZone(p) {
    try { return A.getZone(p.x, p.z); } catch (e) { return null; }
  }

  // ---- self-attach ---------------------------------------------------------
  // The coordinator's only wiring is Encounters.tick() in phys(); the director
  // finds its own world sources. An explicit attach() from a caller overrides
  // this. SIM exists at load time in play3d, but zones.json and GS load async, so
  // the boot retries for a few seconds and then gives up quietly.
  if (typeof window !== 'undefined') {
    let tries = 0;
    const boot = () => {
      if (A) return;
      const S = window.SIM;
      if (S && S.zone && S.pos) {
        Encounters.attach((x, z) => S.zone(x, z), () => S.pos());
        return;
      }
      if (++tries < 40) setTimeout(boot, 250);
    };
    const G = window.GS;
    if (G && G.ready && G.ready.then) G.ready.then(boot, boot);
    else setTimeout(boot, 0);
  }
})();
