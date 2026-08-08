// battle_rules.js — THE RULES KERNEL (battle-core agent).
//
// Pure, seeded, stateless. NO DOM, NO globals mutated, NO Date.now, NO
// Math.random — every number in a battle traces back to one integer seed, so the
// same seed replays the same battle forever (headless balance testing, replays,
// bug repros). Loadable in node (module.exports) and in the browser (window.Rules).
//
// WHY THE SCHEDULER AND THE AI POLICIES LIVE HERE and not in battle_turnbased.js:
// they contain no presentation and no content, and tools/battle_sim.mjs must
// balance-test THE ENGINE THAT SHIPS rather than a node reimplementation of it.
// They are still *policy objects* the battle module selects and injects
// (opts.scheduler), which is what "swappable inside the battle module" means.
// battle_turnbased.js may pass any object with the same one-method shape.
//
// THE INVARIANT THAT MAKES A SCHEDULER SWAP CHEAP: the kernel's unit of work is
// ONE ACTION (applyAction), never one round. An ATB or real-time policy applies
// single actions on its own clock and needs nothing new in here.
(function (root, factory) {
  const R = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = R;
  else root.Rules = R;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  // ===== RNG ================================================================
  // mulberry32: 32-bit state, uniform in [0,1). Same seed, same sequence, in
  // node and in the browser (all ops are integer + Math.imul).
  function mulberry32(seed) {
    let a = seed >>> 0;
    return function () {
      a = (a + 0x6D2B79F5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  // FNV-1a over the string form of every part: turns ('meadow', 417, 'battle')
  // into a stable uint32 seed. This is how a run seed plus a step index becomes
  // a battle seed without anyone holding a counter.
  function hashSeed() {
    let h = 0x811c9dc5;
    for (let i = 0; i < arguments.length; i++) {
      const s = String(arguments[i]);
      for (let j = 0; j < s.length; j++) {
        h ^= s.charCodeAt(j);
        h = Math.imul(h, 0x01000193);
      }
      h ^= 0x2f;                                  // part separator
      h = Math.imul(h, 0x01000193);
    }
    return h >>> 0;
  }
  const uniform = (rng, lo, hi) => lo + (hi - lo) * rng();
  const clamp = (v, lo, hi) => v < lo ? lo : v > hi ? hi : v;

  // ===== DAMAGE ============================================================
  // v1 (ratified): max(1, round((atk*2 - def) * uniform(0.85, 1.15))).
  // Ratified because it is legible: doubling atk roughly doubles output, def
  // subtracts flat, and the +/-15% band keeps every exchange slightly uncertain
  // without ever making a hit meaningless.
  const SPREAD = [0.85, 1.15];
  function damage(atk, def, rng) {
    return Math.max(1, Math.round((atk * 2 - def) * uniform(rng, SPREAD[0], SPREAD[1])));
  }

  // ===== STATE =============================================================
  function deepCopy(v) {
    if (v === null || typeof v !== 'object') return v;
    if (Array.isArray(v)) { const a = new Array(v.length); for (let i = 0; i < v.length; i++) a[i] = deepCopy(v[i]); return a; }
    const o = {}; for (const k in v) o[k] = deepCopy(v[k]); return o;
  }
  // DATA PARAM CONVENTION (matches the granted GS.stats delegation exactly):
  //   growth = the WHOLE growth.json object (it carries .characters and .curve)
  //   items / monsters = the id->def MAP  (GS passes GS.data.items.items)
  // A whole file object is also accepted for items/monsters, because a signature
  // mismatch between GS and the kernel would silently change every stat in the
  // game — see GS.stats's "MUST stay behaviorally identical" fallback.
  const mapOf = (d, k) => (d && typeof d === 'object' && d[k] && typeof d[k] === 'object') ? d[k] : (d || {});

  function mkCombatant(spec, side, idx) {
    const c = {
      side: side, id: String(spec.id), ref: spec.ref || String(spec.id),
      name: spec.name || String(spec.id), idx: idx,
      level: spec.level == null ? null : spec.level,
      hp: 0, maxHp: 0, atk: spec.atk || 0, def: spec.def || 0, spd: spec.spd || 0,
      dead: false, statuses: deepCopy(spec.statuses) || {},
    };
    c.maxHp = spec.maxHp != null ? spec.maxHp : (spec.hp != null ? spec.hp : 1);
    c.hp = spec.hp != null ? spec.hp : c.maxHp;
    c.hp = clamp(c.hp, 0, c.maxHp);
    c.dead = c.hp <= 0;
    return c;
  }
  // makeState({party:[spec], foes:[spec]}) -> battle state.
  // `idx` is the authored order and is the ONLY tie-break in turn ordering, so a
  // battle cannot depend on the order actions happened to be collected in.
  function makeState(o) {
    const party = (o.party || []).map((s, i) => mkCombatant(s, 'party', i));
    const foes = (o.foes || []).map((s, i) => mkCombatant(s, 'foe', 1000 + i));
    return { round: 0, over: null, fled: false, party: party, foes: foes };
  }
  const all = (s) => s.party.concat(s.foes);
  const living = (s, side) => (side === 'party' ? s.party : side === 'foe' ? s.foes : all(s)).filter(c => !c.dead);
  function findById(s, id) {
    for (const c of s.party) if (c.id === id) return c;
    for (const c of s.foes) if (c.id === id) return c;
    return null;
  }
  const cloneState = (s) => deepCopy(s);

  // in-place (used only on a state this module just cloned)
  function _setOver(s) {
    if (s.over) return s;
    if (s.fled) s.over = 'fled';
    else if (!living(s, 'party').length) s.over = 'defeat';   // a wipe is a defeat even if the last foe fell too
    else if (!living(s, 'foe').length) s.over = 'victory';
    return s;
  }
  const checkOver = (state) => state.over ? state : _setOver(cloneState(state));
  const withRound = (state, n) => { const s = cloneState(state); s.round = n; return s; };
  const forceOver = (state, outcome) => { const s = cloneState(state); s.over = outcome; return s; };

  // ===== TURN ORDER ========================================================
  // spd descending, authored index ascending on a tie. Living combatants only.
  // Used ONLY by commit-then-resolve; an ATB policy ignores it entirely.
  function order(state) {
    return living(state).slice().sort((a, b) => (b.spd - a.spd) || (a.idx - b.idx)).map(c => c.id);
  }

  // ===== FLEE ==============================================================
  // Mean party spd vs mean foe spd. Outrunning a scree shell (spd 2) is easy,
  // outrunning a weir eel (spd 10) is not — the numbers come from monsters.json,
  // so the feel is tuned in data like everything else.
  const FLEE = { base: 0.45, perSpd: 0.06, min: 0.15, max: 0.95 };
  function fleeChance(state) {
    const p = living(state, 'party'), f = living(state, 'foe');
    if (!f.length) return 1;
    if (!p.length) return 0;
    const mean = (a) => a.reduce((t, c) => t + c.spd, 0) / a.length;
    return clamp(FLEE.base + FLEE.perSpd * (mean(p) - mean(f)), FLEE.min, FLEE.max);
  }

  // ===== ACTIONS ===========================================================
  // Retargeting is the KERNEL's job so it is deterministic: a dead or missing
  // target falls through to the first living combatant of the intended side.
  // That is what lets a scheduler collect all of a round's actions up front.
  function pickTarget(state, wantId, side) {
    const w = wantId && findById(state, wantId);
    if (w && !w.dead && w.side === side) return w;
    const alive = living(state, side);
    return alive.length ? alive[0] : null;
  }
  // applyAction(state, action, rng) -> {state, events}. Never mutates `state`.
  // An unknown action type FIZZLES (a noop event) instead of throwing: a future
  // scheduler may emit actions this kernel has never heard of and the battle
  // must still terminate.
  function applyAction(state, action, rng) {
    const s = cloneState(state), events = [];
    const by = action && action.by;
    const actor = findById(s, by);
    if (!actor) { events.push({ t: 'noop', by: by || null, why: 'unknown-actor' }); return { state: s, events: events }; }
    if (actor.dead) { events.push({ t: 'noop', by: actor.id, why: 'dead' }); return { state: s, events: events }; }
    if (s.over) { events.push({ t: 'noop', by: actor.id, why: 'battle-over' }); return { state: s, events: events }; }
    const foeSide = actor.side === 'party' ? 'foe' : 'party';

    switch (action.type) {
      case 'attack': {
        const tgt = pickTarget(s, action.target, foeSide);
        if (!tgt) { events.push({ t: 'noop', by: actor.id, why: 'no-target' }); break; }
        events.push({ t: 'action', by: actor.id, kind: 'attack', target: tgt.id });
        const amt = damage(actor.atk, tgt.def, rng);
        tgt.hp = Math.max(0, tgt.hp - amt);
        const killed = tgt.hp === 0;
        if (killed) tgt.dead = true;
        events.push({ t: 'damage', by: actor.id, target: tgt.id, amount: amt, killed: killed });
        if (killed) events.push({ t: 'ko', id: tgt.id, side: tgt.side });
        break;
      }
      case 'item': {
        // The EFFECT rides on the action: whoever built it knew items.json, so the
        // kernel needs no content and cannot disagree with the shop about what a
        // tonic does. (Inventory is consumed by the caller, not here — a battle
        // that is fled or lost must still have spent its tonics.)
        const eff = action.effect || {};
        const tgt = pickTarget(s, action.target || actor.id, actor.side);
        if (!tgt) { events.push({ t: 'noop', by: actor.id, why: 'no-target' }); break; }
        events.push({ t: 'action', by: actor.id, kind: 'item', item: action.item || null, target: tgt.id });
        if (eff.heal) {
          const amt = Math.min(eff.heal, tgt.maxHp - tgt.hp);
          tgt.hp += amt;
          events.push({ t: 'heal', by: actor.id, target: tgt.id, amount: amt, item: action.item || null });
        } else if (eff.damage) {
          const amt = Math.max(1, Math.round(eff.damage));
          tgt.hp = Math.max(0, tgt.hp - amt);
          const killed = tgt.hp === 0; if (killed) tgt.dead = true;
          events.push({ t: 'damage', by: actor.id, target: tgt.id, amount: amt, killed: killed });
          if (killed) events.push({ t: 'ko', id: tgt.id, side: tgt.side });
        } else {
          events.push({ t: 'noop', by: actor.id, why: 'no-effect' });
        }
        break;
      }
      case 'flee': {
        const chance = fleeChance(s);
        const ok = rng() < chance;
        events.push({ t: 'action', by: actor.id, kind: 'flee' });
        events.push({ t: 'flee', by: actor.id, ok: ok, chance: Math.round(chance * 1000) / 1000 });
        if (ok) s.fled = true;
        break;
      }
      case 'wait': case 'defend':
        events.push({ t: 'action', by: actor.id, kind: action.type });
        break;
      default:
        events.push({ t: 'noop', by: actor.id, why: 'unknown-type:' + (action.type || 'none') });
    }
    return { state: _setOver(s), events: events };
  }

  // ===== REWARDS ===========================================================
  // xp/gold/drops for a WON battle, rolled from the same seeded stream. Returned
  // as data for GS.applyBattleResult — the kernel never touches the world.
  function rewards(state, monstersData, rng) {
    const out = { xp: 0, gold: 0, drops: [] };
    if (state.over !== 'victory') return out;
    const defs = mapOf(monstersData, 'monsters');
    for (const f of state.foes) {
      const d = defs[f.ref]; if (!d) continue;
      out.xp += d.xp || 0;
      out.gold += d.gold || 0;
      for (const drop of (d.drops || [])) {
        if (rng() < (drop.rate || 0)) out.drops.push(drop.item);
      }
    }
    return out;
  }

  // ===== DERIVATION FROM RULES DATA ========================================
  // Mirrors GS.baseStats + GS.stats EXACTLY. It exists because the kernel must
  // run in node with no GS at all (that is the whole point of the balance
  // harness). Two copies of one formula will drift: the standing request to the
  // coordinator is for GS.stats to delegate here when window.Rules exists.
  const derive = {
    // charStats(growth.json, items-MAP, {id, level, equip}) -> {hp,atk,def,spd,maxHp}
    // GS.stats delegates here verbatim: floor(base + growth*(level-1)) then
    // equipment statMods, maxHp = hp. Changing this changes every stat in the game.
    charStats(growthData, itemsData, ch) {
      const items = mapOf(itemsData, 'items');
      const c = growthData.characters[ch.id], L = (ch.level || 1) - 1, s = {};
      for (const k of ['hp', 'atk', 'def', 'spd']) s[k] = Math.floor(c.base[k] + c.growth[k] * L);
      for (const slot of ['weapon', 'armor']) {
        const id = ch.equip && ch.equip[slot];
        const it = id && items[id];
        if (it && it.statMods) for (const k in it.statMods) s[k] = (s[k] || 0) + it.statMods[k];
      }
      s.maxHp = s.hp;
      return s;
    },
    // one GS party member -> one combatant spec
    partyMember(growthData, itemsData, ch) {
      const st = derive.charStats(growthData, itemsData, ch);
      return {
        id: ch.id, ref: ch.id, name: growthData.characters[ch.id].name || ch.id,
        level: ch.level || 1, maxHp: st.maxHp, hp: ch.hp == null ? st.maxHp : ch.hp,
        atk: st.atk, def: st.def, spd: st.spd,
      };
    },
    // a level-1 character exactly as newGame() would create them (harness use)
    startingMember(growthData, itemsData, id) {
      const c = growthData.characters[id];
      return derive.partyMember(growthData, itemsData,
        { id: id, level: 1, hp: null, equip: Object.assign({ weapon: null, armor: null }, c.startEquip || {}) });
    },
    // ['reed-nibbler','reed-nibbler'] -> two combatant specs, FF-style A/B names
    foesFromGroup(monstersData, group) {
      const defs = mapOf(monstersData, 'monsters');
      const counts = {};
      for (const id of group) counts[id] = (counts[id] || 0) + 1;
      const seen = {};
      return group.map((id, i) => {
        const d = defs[id] || { name: id, hp: 1, atk: 1, def: 0, spd: 1 };
        let name = d.name || id;
        if (counts[id] > 1) { seen[id] = (seen[id] || 0) + 1; name += ' ' + String.fromCharCode(64 + seen[id]); }
        return { id: 'm' + i, ref: id, name: name, maxHp: d.hp, hp: d.hp, atk: d.atk, def: d.def, spd: d.spd };
      });
    },
    // weighted group pick from an encounters.json zone entry (seeded)
    pickGroup(zoneDef, rng) {
      const groups = (zoneDef && zoneDef.groups) || [];
      if (!groups.length) return null;
      let total = 0; for (const g of groups) total += (g.weight || 1);
      let r = rng() * total;
      for (const g of groups) { r -= (g.weight || 1); if (r <= 0) return g.monsters.slice(); }
      return groups[groups.length - 1].monsters.slice();
    },
  };

  // ===== CONTROLLER ROUTER =================================================
  // charId -> 'p1' | 'p2' | 'ai'. Mutable MID-BATTLE: this is the couch-co-op
  // swap seam. The engine reads it once per decision and never caches, so a
  // remap takes effect on the very next combatant to act.
  function makeRouter(init) {
    init = init || {};
    const table = Object.assign({}, init.table);
    const defaults = Object.assign({ party: 'p1', foe: 'ai' }, init.defaults);
    const seats = Object.assign({}, init.seats);
    const sides = {};
    const R = {
      seats: seats, defaults: defaults,
      // learn the combatants of a battle without overwriting an explicit mapping
      bind(state) {
        for (const c of all(state)) {
          sides[c.id] = c.side;
          if (!(c.id in table)) table[c.id] = defaults[c.side];
        }
        return R;
      },
      seatFor(id) { return table[id] || defaults[sides[id]] || 'ai'; },
      set(id, seat) { table[id] = seat; return seat; },
      setSeat(seat, ids) { (ids || []).forEach(id => { table[id] = seat; }); return R; },
      swap(a, b) { const t = table[a]; table[a] = table[b]; table[b] = t; return R; },
      table() { return Object.assign({}, table); },
      default(side) { return defaults[side]; },
      seat(name, provider) { seats[name] = provider; return R; },
    };
    return R;
  }

  // ===== DECISION PROVIDERS (seats) ========================================
  // A provider is {name, decide(actorId, state, api) -> action | Promise<action>}.
  // `api` carries what a provider cannot derive from state: {rng, items, ui, ...}.
  const policies = {
    // monsters: hit a living party member (rng-picked, so a party of N is not
    // a queue). Deterministic because the rng is the battle's own stream.
    monsterAi() {
      return {
        name: 'monster-ai',
        decide(actorId, state, api) {
          const targets = living(state, 'party');
          if (!targets.length) return { type: 'wait', by: actorId };
          const rng = api && api.rng;
          const t = rng ? targets[Math.min(targets.length - 1, Math.floor(rng() * targets.length))] : targets[0];
          return { type: 'attack', by: actorId, target: t.id };
        },
      };
    },
    // the party autopilot: also the seat a dropped-out player is remapped to.
    // Policy: heal below `healBelow` of max while stock lasts, else attack the
    // lowest-HP living foe (finishing wounded monsters removes attackers fastest).
    // It bookkeeps `inventory` itself; a GS-backed caller wraps the returned
    // action to spend the real item.
    partyAi(o) {
      o = o || {};
      const itemsMap = mapOf(o.items, 'items');
      const inv = o.inventory || {};
      const below = o.healBelow == null ? 0.30 : o.healBelow;
      function chooseHeal(me) {
        const deficit = me.maxHp - me.hp;
        const opts = [];
        for (const id in inv) {
          if (!(inv[id] > 0)) continue;
          const d = itemsMap[id];
          if (!d || d.type !== 'consumable' || !d.effect || !d.effect.heal) continue;
          opts.push({ id: id, heal: d.effect.heal });
        }
        if (!opts.length) return null;
        opts.sort((a, b) => (a.heal - b.heal) || (a.id < b.id ? -1 : 1));
        const fit = opts.find(x => x.heal >= deficit);
        return (fit || opts[opts.length - 1]).id;    // smallest that covers it, else the biggest we have
      }
      return {
        name: 'party-ai',
        decide(actorId, state) {
          const me = state.party.find(c => c.id === actorId);
          if (me && me.maxHp > 0 && me.hp / me.maxHp < below) {
            const id = chooseHeal(me);
            if (id) {
              inv[id] -= 1;
              return { type: 'item', by: actorId, target: actorId, item: id,
                       effect: deepCopy(itemsMap[id].effect) };
            }
          }
          const foes = living(state, 'foe');
          if (!foes.length) return { type: 'wait', by: actorId };
          let t = foes[0];
          for (const c of foes) if (c.hp < t.hp) t = c;
          return { type: 'attack', by: actorId, target: t.id };
        },
      };
    },
  };

  // ===== SCHEDULERS (swappable pacing policy) ==============================
  // A scheduler is {name, run(ctx) -> Promise<state>} and owns TIME AND ORDERING
  // only. It computes no number (the kernel does) and knows no seat (the router
  // does). ctx = {state, rules, rng, decide, seatFor, emit, parallel, maxRounds}.
  //
  // ctx.emit MAY RETURN A PROMISE AND IS AWAITED. That single detail is what lets
  // an animated battle screen pace itself (damage numbers, hit pauses) without
  // the kernel knowing what a frame is — and what lets a real-time scheduler
  // yield. A headless caller returns undefined and pays one microtask.
  const MAX_ROUNDS = 200;
  const schedulers = {
    // v1: collect one action per living combatant, then resolve all of them in
    // spd order. Party decisions are grouped BY SEAT and the groups awaited
    // concurrently — sequential within a seat (one cursor per human), parallel
    // across seats. That is the parallel-menus structure co-op needs, present in
    // v1 even though v1 has a single seat.
    commitThenResolve: {
      name: 'commit-then-resolve',
      async run(ctx) {
        const rules = ctx.rules, rng = ctx.rng, emit = ctx.emit || function () {};
        const cap = ctx.maxRounds || MAX_ROUNDS;
        let state = rules.checkOver(ctx.state);
        while (!state.over && state.round < cap) {
          const round = state.round + 1;
          state = rules.withRound(state, round);
          await emit([{ t: 'round', n: round }], state);

          const collected = [];
          const bySeat = new Map();
          for (const c of state.party) {
            if (c.dead) continue;
            const seat = ctx.seatFor ? ctx.seatFor(c.id) : 'ai';
            if (!bySeat.has(seat)) bySeat.set(seat, []);
            bySeat.get(seat).push(c.id);
          }
          const gather = [...bySeat.values()].map(async (ids) => {
            for (const id of ids) {
              const a = await ctx.decide(id, state);
              if (a) collected.push(Object.assign({ by: id }, a));
            }
          });
          if (ctx.parallel === false) { for (const g of gather) await g; } else await Promise.all(gather);

          for (const c of state.foes) {
            if (c.dead) continue;
            const a = await ctx.decide(c.id, state);
            if (a) collected.push(Object.assign({ by: c.id }, a));
          }

          // ORDERING IS RECOMPUTED FROM STATE, not from collection order, so
          // parallel menus can never change the outcome of a seeded battle.
          const rank = {};
          rules.order(state).forEach((id, i) => { rank[id] = i; });
          const pos = (a) => (rank[a.by] == null ? 9999 : rank[a.by]);
          collected.sort((a, b) => pos(a) - pos(b));

          for (const a of collected) {
            if (state.over) break;
            const r = rules.applyAction(state, a, rng);
            state = r.state;
            if (r.events.length) await emit(r.events, state);
          }
          state = rules.withRound(rules.checkOver(state), round);
        }
        // Safety net, not a rule: an engine that cannot end a battle is a bug the
        // harness asserts against. Treat a cap breach as a break-off, never as a
        // false defeat (no rewards, nobody dies).
        if (!state.over) {
          await emit([{ t: 'noop', by: null, why: 'round-cap' }], state);
          state = rules.forceOver(state, 'fled');
        }
        await emit([{ t: 'end', outcome: state.over, rounds: state.round }], state);
        return state;
      },
    },
  };

  // ===== ENGINE ============================================================
  // Ties router + seats + scheduler together. Both battle_turnbased.js and
  // tools/battle_sim.mjs go through here, so the harness exercises the shipping
  // decision path and not a copy of it.
  const engine = {
    // run({state, rng, router, seats, scheduler, emit, api, parallel, maxRounds})
    run(cfg) {
      const router = cfg.router || makeRouter();
      router.bind(cfg.state);
      const seats = cfg.seats || router.seats;
      const scheduler = cfg.scheduler || schedulers.commitThenResolve;
      const api = Object.assign({ rng: cfg.rng }, cfg.api);
      async function decide(actorId, state) {
        const seat = router.seatFor(actorId);
        const p = seats[seat] || seats.ai;
        if (!p || !p.decide) return { type: 'attack', by: actorId };   // a seat with nobody in it still has to act
        const a = await p.decide(actorId, state, api);
        return a ? Object.assign({ by: actorId }, a) : { type: 'wait', by: actorId };
      }
      return scheduler.run({
        state: cfg.state, rules: R, rng: cfg.rng, decide: decide,
        seatFor: (id) => router.seatFor(id), emit: cfg.emit,
        parallel: cfg.parallel, maxRounds: cfg.maxRounds,
      });
    },
    // the full result envelope from a finished state (the Battle contract's shape
    // minus presentation) — shared by the battle module and the harness.
    result(state, opts) {
      opts = opts || {};
      const rew = rewards(state, opts.monsters, opts.rng || (() => 0));
      const partyHp = {};
      for (const c of state.party) partyHp[c.id] = c.hp;
      return {
        outcome: state.over, xp: rew.xp, gold: rew.gold, drops: rew.drops,
        turns: state.round, partyHp: partyHp, log: opts.log || [],
      };
    },
  };

  const R = {
    version: 1,
    SPREAD: SPREAD, FLEE: FLEE, MAX_ROUNDS: MAX_ROUNDS,
    mulberry32, hashSeed, uniform, clamp,
    damage, fleeChance, order,
    makeState, cloneState, checkOver, withRound, forceOver, applyAction,
    findById, living, all, rewards,
    derive, makeRouter, policies, schedulers, engine,
  };
  return R;
});
