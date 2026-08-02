#!/usr/bin/env node
// encounter_sim.mjs — HEADLESS INTEGRATION HARNESS for the battle-core modules.
//
// battle_sim.mjs proves the BALANCE of the rules kernel. This proves the WIRING:
// it loads the real public/js/game_state.js, battle_rules.js, battle_turnbased.js
// and encounters.js under a stub `window` with no DOM at all, walks a synthetic
// player through synthetic zones, and checks that the vertical loop actually
// closes — steps accumulate, grace behaves, rolls fire at the authored rate,
// Battle.start runs to a result, and GS.applyBattleResult moves gold/xp/level.
//
// WHY IT EXISTS: everything above is browser code that the browser suites cannot
// reach cheaply (a real encounter needs a player walking for twenty seconds), and
// the encounter cadence — the whole "a step is one world unit" ruling — is a
// NUMBER that should be measured, not asserted in prose. Stubs are exactly three
// things: fetch (reads public/ off disk so the REAL GS loads the REAL json), a
// SIM with a movable position, and window itself. No DOM, so the battle module
// takes its documented headless path and the party autopilot plays.
//
//   node tools/encounter_sim.mjs            # asserts, exit 1 on failure
//   node tools/encounter_sim.mjs --verbose  # per-battle detail
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const require = createRequire(import.meta.url);
const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');
const PUB = join(ROOT, 'public');
const VERBOSE = process.argv.includes('--verbose');

// ---- the three stubs -------------------------------------------------------
global.window = global;                       // browser modules attach here
// EVERY MODULE RE-ARMS ON 'eb-scene' (the in-place scene-swap contract), and a
// bare globalThis has no event target — encounters.js self-arms unguarded and
// threw here on load. The harness owes the module the shape of the contract it
// ships against, so the stub carries a no-op listener registry rather than the
// module carrying a `typeof` guard for a suite.
if (!global.addEventListener) {
  const listeners = Object.create(null);
  global.addEventListener = (t, fn) => { (listeners[t] = listeners[t] || []).push(fn); };
  global.removeEventListener = (t, fn) => {
    const a = listeners[t] || []; const i = a.indexOf(fn); if (i >= 0) a.splice(i, 1);
  };
  global.dispatchEvent = (ev) => { for (const fn of (listeners[ev && ev.type] || [])) fn(ev); return true; };
}
global.fetch = async (u) => {                 // GS loads its rules data off disk
  const p = join(PUB, String(u).split('?')[0]);
  return { ok: true, status: 200, json: async () => JSON.parse(readFileSync(p, 'utf8')) };
};
const P = { x: 0, y: 0, z: 0 };
let ZONE = 'meadow';
const placed = [];
global.SIM = {
  zone: () => ZONE,
  pos: () => ({ x: P.x, y: P.y, z: P.z }),
  place: (p) => { placed.push(p.slice()); P.x = p[0]; P.y = p[1]; P.z = p[2]; return { ...P }; },
  arrival: () => null,
  keys: () => { },
  graph: () => null,
};

// ---- load the real modules, in the coordinator's hook order ----------------
global.Rules = require(join(PUB, 'js/battle_rules.js'));
require(join(PUB, 'js/game_state.js'));
require(join(PUB, 'js/battle_turnbased.js'));
require(join(PUB, 'js/encounters.js'));

const SPD = 0.075;               // play3d's per-tick walk speed
const fails = [];
const ok = (cond, msg, extra) => {
  if (!cond) fails.push(msg + (extra !== undefined ? ' — ' + JSON.stringify(extra) : ''));
  console.log((cond ? '  ok   ' : '  FAIL ') + msg + (extra !== undefined ? '  ' + JSON.stringify(extra) : ''));
};
const settle = async () => {
  // a headless battle resolves in microtasks; give it real ticks to be sure
  for (let i = 0; i < 200 && window.Encounters._debug().busy; i++) await new Promise(r => setImmediate(r));
};

// Walk `units` world units while flipping between `zones` every `everyU` units —
// the shoreline/treeline path. everyU 0 = a straight walk in zones[0] (the control).
// It AWAITS between ticks, which the control row depends on: a synchronous tick loop
// leaves the director `busy` forever after the first battle fires (fire() is async
// and its finally never runs until the loop yields), which silently deflates the
// control's step count and would make the whole comparison lie.
async function flipWalk(units, everyU, zones, seed) {
  P.x = 0; ZONE = zones[0];
  window.Encounters.attach(() => ZONE, () => ({ ...P }), { seed, battleOpts: { headless: true } });
  const ticks = Math.round(units / SPD);
  let zi = 0, next = everyU;
  for (let i = 0; i < ticks; i++) {
    P.x += SPD;
    if (everyU && P.x >= next) { zi = (zi + 1) % zones.length; ZONE = zones[zi]; next += everyU; }
    window.Encounters.tick();
    await settle();
  }
  const d = window.Encounters._debug();
  return { flip: everyU || 'never', steps: d.steps, rolls: d.rolls, battles: d.battles, why: d.graceWhy };
}

// walk `units` world units in `zone`, one physics tick at a time
async function walk(units, zone, opts) {
  opts = opts || {};
  ZONE = zone;
  const ticks = Math.round(units / SPD);
  const before = window.Encounters._debug().battles;
  const seen = [];
  for (let i = 0; i < ticks; i++) {
    P.x += SPD;
    window.Encounters.tick();
    if (window.Encounters._debug().busy) {
      await settle();
      const d = window.Encounters._debug();
      seen.push({ at: +P.x.toFixed(1), group: d.lastSpec && d.lastSpec.group.join('+'),
                  outcome: d.lastResult && d.lastResult.outcome, turns: d.lastResult && d.lastResult.turns });
    }
  }
  const d = window.Encounters._debug();
  return { battles: d.battles - before, steps: d.steps, rolls: d.rolls, seen };
}

async function main() {
  await window.GS.ready;
  const GS = window.GS;
  ok(GS.ok, 'real GS loaded its rules data through the fetch stub',
    { party: GS.state.party.length, gold: GS.state.gold, bag: GS.state.inventory });

  // GS.stats now delegates to the kernel; prove the two agree on the shipped party
  const v = GS.state.party.find(p => p.id === 'vesper');
  const viaGs = GS.stats(v);
  const viaKernel = Rules.derive.charStats(GS.data.growth, GS.data.items.items, v);
  ok(JSON.stringify(viaGs) === JSON.stringify(viaKernel),
    'GS.stats and Rules.derive.charStats agree', viaGs);

  ok(!!window.Battle && typeof window.Battle.start === 'function', 'window.Battle exposes start()');
  ok(!!window.Encounters && typeof window.Encounters.tick === 'function', 'window.Encounters exposes tick()');

  // ---- 1. a single battle, end to end, no DOM ------------------------------
  const gold0 = GS.state.gold, xp0 = v.xp;
  const res = await window.Battle.start(
    { zone: 'meadow', group: ['reed-nibbler'], seed: 12345, backdrop: 'meadow' }, null, { headless: true });
  ok(res && res.outcome === 'victory', 'headless Battle.start returns a victory result', res && {
    outcome: res.outcome, xp: res.xp, gold: res.gold, turns: res.turns, hp: res.partyHp,
  });
  ok(res && res.log.some(e => e.t === 'end'), 'result.log carries the event stream', res && { events: res.log.length });
  ok(GS.state.gold === gold0 && v.xp === xp0,
    'Battle.start applied NOTHING to the world (the boundary holds)', { gold: GS.state.gold, xp: v.xp });
  GS.applyBattleResult(res);
  ok(GS.state.gold === gold0 + res.gold, 'GS.applyBattleResult is what moves gold',
    { before: gold0, after: GS.state.gold });
  ok(!window.Battle.active, 'Battle.active is false again after the promise resolves');

  // ---- 2. the router is real and remappable mid-battle --------------------
  let swapped = null;
  await window.Battle.start({ zone: 'meadow', group: ['reed-nibbler', 'reed-nibbler'], seed: 7, backdrop: 'meadow' },
    null, {
      headless: true,
      seats: {
        p1: { name: 'probe', decide(id, st) { swapped = window.Battle.router.seatFor(id); return { type: 'attack', by: id }; } },
      },
    });
  ok(swapped === 'p1', 'party members route to p1 by default', { seat: swapped });
  // ...and a remap takes effect on the very next decision
  let seatsSeen = [];
  await window.Battle.start({ zone: 'forest', group: ['duskpad', 'duskpad'], seed: 11, backdrop: 'forest' },
    null, {
      headless: true,
      seats: {
        p1: {
          name: 'probe',
          decide(id, st) {
            seatsSeen.push('p1');
            window.Battle.router.set(id, 'ai');       // "player 2 drops out" mid-battle
            return { type: 'attack', by: id };
          },
        },
      },
    });
  ok(seatsSeen.length === 1, 'a mid-battle router remap moves the seat immediately (p1 asked once, then the ai seat played)',
    { p1Decisions: seatsSeen.length });

  // ---- 3. safe zones are safe --------------------------------------------
  window.Encounters.attach(() => ZONE, () => ({ ...P }), { seed: 4242 });
  const road = await walk(600, 'road');
  ok(road.battles === 0, 'road: 600 units walked, zero encounters', road);
  const town = await walk(300, 'town-square-not-in-the-table');
  ok(town.battles === 0, 'an UNKNOWN zone name is safe, never defaulted', town);

  // ---- 4. cadence: the ratified "one step = one world unit" ---------------
  // meadow grace 30 + mean 1/0.02 = 50 rolls -> a battle every ~80 u.
  P.x = 0;
  window.Encounters.attach(() => ZONE, () => ({ ...P }), { seed: 4242 });
  const meadow = await walk(800, 'meadow');
  const per100 = meadow.battles / 8;
  ok(meadow.battles >= 4 && meadow.battles <= 16,
    'meadow: 800 u of walking gave a playable number of encounters', { battles: meadow.battles, per100u: +per100.toFixed(2) });
  ok(Math.abs(meadow.steps - 800) < 40, 'steps track distance, not ticks (800 u -> ~800 steps)', { steps: meadow.steps });
  if (VERBOSE) for (const s of meadow.seen) console.log('       ', JSON.stringify(s));

  // ---- 4b. zone-boundary grace farming is DEAD (regression) ---------------
  // Before the safe-zone-only grace rule, alternating between two HOSTILE zones
  // re-armed grace forever, so 600 u of shoreline/treeline walking produced ZERO
  // rolls where a straight line produced 120 — the default outcome of following
  // the pretty line, not a clever exploit. Two mechanisms had to die: the
  // graceLeft reset (rolls) and the acc reset (steps). Both are asserted, because
  // fixing only the first leaves tight zig-zags encounter-free.
  const ctrl = await flipWalk(1200, 0, ['meadow', 'crag'], 7);
  ok(ctrl.rolls > 400 && ctrl.battles > 4, 'control: a straight 1200 u walk rolls and fights', ctrl);
  ok(Math.abs(ctrl.steps - 1200) < 40,
    'control step count is HONEST (an unawaited tick loop would deflate it — fire() is async)', { steps: ctrl.steps });
  for (const flip of [0.5, 1, 2, 4, 8, 20]) {
    const w = await flipWalk(1200, flip, ['meadow', 'crag'], 7);
    ok(w.rolls > ctrl.rolls * 0.5 && w.battles > 0,
      'boundary walk flipping every ' + flip + ' u still rolls (was 0 rolls / 0 battles pre-fix)', w);
    ok(Math.abs(w.steps - 1200) < 40,
      'and its accumulator is never zeroed by the crossing (was 0 steps at 0.5 u)', { flip, steps: w.steps });
  }
  // The road reward is DELIBERATE and must not be "fixed" later: safe zones are
  // the sole source of quiet, so weaving on and off a road stays peaceful. The
  // bound is that you have to keep returning to safety to keep it.
  const hug = await flipWalk(1200, 20, ['road', 'meadow'], 7);
  ok(hug.battles === 0 && hug.why === 'entered-safety',
    'road-hugging stays safe BY DESIGN (grace comes from safety, and the legibility programme rewards the route)', hug);

  // ---- 5. determinism of the walk ----------------------------------------
  const runWalk = async (seed) => {
    P.x = 0; ZONE = 'meadow';
    window.Encounters.attach(() => ZONE, () => ({ ...P }), { seed });
    const w = await walk(600, 'meadow');
    return w.seen.map(s => s.at + ':' + s.group).join('|');
  };
  const a1 = await runWalk(99), a2 = await runWalk(99), a3 = await runWalk(100);
  ok(a1 === a2, 'the same run seed replays the same encounters at the same places');
  ok(a1 !== a3, 'a different run seed gives a different walk');

  // ---- 6. grace re-arms on a teleport (a scene handoff) ------------------
  window.Encounters.attach(() => ZONE, () => ({ ...P }), { seed: 5 });
  ZONE = 'meadow';
  for (let i = 0; i < 600; i++) { P.x += SPD; window.Encounters.tick(); await settle(); }
  P.x += 40;                                     // a scene-graph arrival
  window.Encounters.tick();
  const dbg = window.Encounters._debug();
  ok(dbg.graceWhy === 'teleport' && dbg.grace === GS.data.encounters.zones.meadow.grace,
    'a >3 u position jump re-arms the zone grace instead of rolling', { why: dbg.graceWhy, grace: dbg.grace });

  // ---- 7. defeat handling: revive at 1 HP, half the purse, respawn -------
  GS.addGold(100 - GS.state.gold);
  GS.setHp('vesper', 1);
  placed.length = 0;
  window.Encounters.attach(() => ZONE, () => ({ ...P }), { seed: 5, battleOpts: { headless: true } });
  const before = GS.state.gold;
  await window.Encounters.fireNow('crag');
  await settle();
  const d7 = window.Encounters._debug();
  if (d7.lastResult && d7.lastResult.outcome === 'defeat') {
    ok(GS.state.party.find(p => p.id === 'vesper').hp === 1, 'defeat revives at 1 HP');
    ok(GS.state.gold === before - Math.floor(before / 2), 'defeat costs half the purse',
      { before, after: GS.state.gold });
    ok(placed.length === 1, 'defeat places the player back at the spawn anchor', { placed: placed[0] });
  } else {
    ok(true, 'defeat path not exercised (she survived at 1 HP — fine, outcome: ' +
      (d7.lastResult && d7.lastResult.outcome) + ')');
  }

  // ---- 8. inertness without its dependencies ------------------------------
  const savedBattle = window.Battle;
  window.Battle = undefined;
  const inert = window.Encounters._debug();
  ok(inert.reason === 'no-battle-module', 'no Battle module -> the director is inert and says why', { reason: inert.reason });
  P.x = 0;
  for (let i = 0; i < 4000; i++) { P.x += SPD; window.Encounters.tick(); }
  ok(window.Encounters._debug().battles === inert.battles, 'and it never fires while inert');
  window.Battle = savedBattle;

  console.log('');
  if (fails.length) {
    console.log('FAILURES (' + fails.length + '):');
    for (const f of fails) console.log('  - ' + f);
    process.exit(1);
  }
  console.log('ENCOUNTER INTEGRATION GREEN — ' + 'all checks passed');
  process.exit(0);
}
main().catch(e => { console.error(e); process.exit(1); });
