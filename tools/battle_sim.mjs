#!/usr/bin/env node
// battle_sim.mjs — HEADLESS BALANCE HARNESS (battle-core agent).
//
// Balance is a test, not a vibe. This runs N seeded battles per scenario against
// THE SHIPPING ENGINE — public/js/battle_rules.js, the same kernel, scheduler,
// turn order, damage roll and party AI the browser uses — and asserts envelopes.
// It never opens a browser and never touches GS: the party is derived from
// growth.json + items.json through Rules.derive, exactly as GS.stats does.
//
//   node tools/battle_sim.mjs                 # 500 battles/scenario, asserts
//   node tools/battle_sim.mjs --n=2000        # more samples
//   node tools/battle_sim.mjs --seed=99       # a different sample of the space
//   node tools/battle_sim.mjs --json          # machine-readable
//   node tools/battle_sim.mjs --tune='{"duskpad":{"atk":6}}'   # measure a proposal
//   node tools/battle_sim.mjs --tune=path.json                 # ...from a file
//
// --tune EXISTS BECAUSE monsters.json IS COORDINATOR-OWNED: a balance proposal has
// to be measured before it is requested, without editing the data file. What it
// prints under --tune is exactly what the ratified numbers would produce.
//
// SCENARIOS ARE DATA: every group in encounters.json becomes a scenario, so a new
// monster group is covered the moment it is authored. Envelopes are per zone.
// Exit 1 on any breach, with the offending row marked.
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const require = createRequire(import.meta.url);
const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');
const R = require(join(ROOT, 'public/js/battle_rules.js'));
const readJson = (p) => JSON.parse(readFileSync(join(ROOT, 'public/game', p), 'utf8'));

const monsters = readJson('monsters.json').monsters;
const items = readJson('items.json').items;
const growth = readJson('growth.json');
const encounters = readJson('encounters.json').zones;

// ---- CLI -------------------------------------------------------------------
const argv = process.argv.slice(2);
const arg = (k, d) => {
  const hit = argv.find(a => a.startsWith('--' + k + '='));
  return hit ? hit.split('=').slice(1).join('=') : d;
};
const N = parseInt(arg('n', '500'), 10);
const SEED0 = parseInt(arg('seed', '1'), 10);
const AS_JSON = argv.includes('--json');

// ---- --tune: measure a monsters.json proposal without editing the data file --
const TUNE = (() => {
  const t = arg('tune', null);
  if (!t) return null;
  const raw = t.trim().startsWith('{') ? t : readFileSync(t, 'utf8');
  const patch = JSON.parse(raw);
  for (const [id, mods] of Object.entries(patch)) {
    if (!monsters[id]) { console.error('--tune: no such monster "' + id + '"'); process.exit(2); }
    Object.assign(monsters[id], mods);
  }
  return patch;
})();

// ---- ENVELOPES -------------------------------------------------------------
// Ratified 2026-07-30: meadow win >= 0.95 with a 1-4 round band (the original
// 3-6 was written for a party; at party-of-one a level-1 traveller one-shots a
// 16 HP nibbler ~60% of the time, and the coordinator's ruling was to keep
// monsters cheap and fights snappy rather than inflate HP). Forest >= 0.70,
// crag >= 0.40 — the crag is MEANT to be dangerous at level 1.
// `advisory` rows are measured and printed but cannot fail the build; they are
// numbers nobody has ratified yet.
const ENVELOPES = {
  meadow: { win: 0.95, rounds: [1, 4] },
  forest: { win: 0.70, rounds: [1, 8] },
  crag: { win: 0.40, rounds: [1, 16] },
  water: { win: 0.50, rounds: [1, 12], advisory: true },
};
const LEVELS = [
  { level: 1, assert: true },
  { level: 2, assert: false },     // progression sanity: the ecosystem doc's "crag at level 2"
];

// ---- the party -------------------------------------------------------------
// Level-1 Vesper with start equipment and the start inventory, exactly as
// GS.newGame() would build her. A level-N variant levels her the way grantXp
// does (stats from the curve; HP full).
function member(level) {
  const c = growth.characters.vesper;
  const m = R.derive.partyMember(growth, items, {
    id: 'vesper', level, hp: null,
    equip: Object.assign({ weapon: null, armor: null }, c.startEquip || {}),
  });
  return m;
}
const startInventory = growth.startInventory || {};

// ---- one battle ------------------------------------------------------------
// The party is seated at 'ai' with Rules.policies.partyAi (attack the lowest-HP
// living foe; drink the smallest sufficient tonic below 30% HP while stock
// lasts). Monsters use Rules.policies.monsterAi. Both are the shipping policies.
async function oneBattle(group, seed, level) {
  const party = [member(level)];
  const foes = R.derive.foesFromGroup(monsters, group);
  const state = R.makeState({ party, foes });
  const rng = R.mulberry32(seed);
  const inventory = Object.assign({}, startInventory);
  const partyAi = R.policies.partyAi({ items, inventory });
  const foeAi = R.policies.monsterAi();
  const aiSeat = {
    name: 'ai',
    decide(actorId, st, api) {
      const c = R.findById(st, actorId);
      return (c && c.side === 'foe' ? foeAi : partyAi).decide(actorId, st, api);
    },
  };
  const router = R.makeRouter({ seats: { ai: aiSeat }, defaults: { party: 'ai', foe: 'ai' } });
  const log = [];
  const final = await R.engine.run({
    state, rng, router, seats: router.seats,
    emit: (events) => { for (const e of events) log.push(e); },
  });
  const result = R.engine.result(final, { monsters, rng, log });
  const tonicsUsed = Object.keys(startInventory)
    .reduce((t, id) => t + ((startInventory[id] || 0) - (inventory[id] || 0)), 0);
  return { result, final, log, tonicsUsed };
}

// ---- a scenario ------------------------------------------------------------
async function runScenario(sc) {
  const rounds = [], hpLeft = [];
  let wins = 0, defeats = 0, fled = 0, xp = 0, gold = 0, drops = 0, tonics = 0, capped = 0;
  for (let i = 0; i < N; i++) {
    const seed = R.hashSeed(SEED0, sc.id, sc.level, i);
    const { result, log, tonicsUsed } = await oneBattle(sc.group, seed, sc.level);
    if (result.outcome === 'victory') wins++;
    else if (result.outcome === 'defeat') defeats++;
    else fled++;
    rounds.push(result.turns);
    hpLeft.push(result.partyHp.vesper);
    xp += result.xp; gold += result.gold; drops += (result.drops || []).length;
    tonics += tonicsUsed;
    if (log.some(e => e.t === 'noop' && e.why === 'round-cap')) capped++;
  }
  rounds.sort((a, b) => a - b);
  const mean = (a) => a.reduce((t, v) => t + v, 0) / (a.length || 1);
  return {
    ...sc,
    n: N, wins, defeats, fled, capped,
    winRate: wins / N,
    meanRounds: mean(rounds), medRounds: rounds[Math.floor(rounds.length / 2)],
    maxRounds: rounds[rounds.length - 1],
    meanHp: mean(hpLeft), maxHp: member(sc.level).maxHp,
    meanXp: xp / N, meanGold: gold / N, dropRate: drops / N, tonicRate: tonics / N,
  };
}

// ---- engine property tests (not balance: correctness) ----------------------
async function propertyTests() {
  const fails = [];
  // 1. DETERMINISM: same seed, identical event log — the whole basis of this file.
  const a = await oneBattle(['duskpad', 'duskpad'], 4242, 1);
  const b = await oneBattle(['duskpad', 'duskpad'], 4242, 1);
  if (JSON.stringify(a.log) !== JSON.stringify(b.log))
    fails.push('determinism: same seed produced different logs');
  // 2. A different seed must produce a different battle (the rng is actually used)
  const c = await oneBattle(['duskpad', 'duskpad'], 4243, 1);
  if (JSON.stringify(a.log) === JSON.stringify(c.log))
    fails.push('determinism: different seeds produced identical logs (rng not consumed?)');
  // 3. PURITY: applyAction must not mutate the state it is given.
  const st = R.makeState({ party: [member(1)], foes: R.derive.foesFromGroup(monsters, ['scree-shell']) });
  const before = JSON.stringify(st);
  R.applyAction(st, { type: 'attack', by: 'vesper', target: 'm0' }, R.mulberry32(7));
  if (JSON.stringify(st) !== before) fails.push('purity: applyAction mutated its input state');
  // 4. RETARGETING: an action aimed at a corpse must land on a living foe.
  const two = R.makeState({ party: [member(1)], foes: R.derive.foesFromGroup(monsters, ['reed-nibbler', 'reed-nibbler']) });
  two.foes[0].hp = 0; two.foes[0].dead = true;
  const rt = R.applyAction(two, { type: 'attack', by: 'vesper', target: 'm0' }, R.mulberry32(9));
  const hitId = (rt.events.find(e => e.t === 'damage') || {}).target;
  if (hitId !== 'm1') fails.push('retargeting: attack on a dead foe hit "' + hitId + '" instead of m1');
  // 5. COLLECTION ORDER CANNOT MATTER: resolving the same actions in a different
  //    submitted order must give the same state (spd order is recomputed).
  const s2 = R.makeState({ party: [member(1)], foes: R.derive.foesFromGroup(monsters, ['brook-sprite']) });
  const acts = [{ type: 'attack', by: 'vesper', target: 'm0' }, { type: 'attack', by: 'm0', target: 'vesper' }];
  const play = (list, seed) => {
    let s = s2, rng = R.mulberry32(seed);
    const rank = {}; R.order(s).forEach((id, i) => { rank[id] = i; });
    for (const act of list.slice().sort((x, y) => rank[x.by] - rank[y.by])) s = R.applyAction(s, act, rng).state;
    return JSON.stringify(s);
  };
  if (play(acts, 3) !== play(acts.slice().reverse(), 3))
    fails.push('ordering: collection order changed the outcome');
  // 6. TERMINATION: a battle nobody can win must still end (the round cap).
  const tank = R.makeState({
    party: [{ id: 'vesper', name: 'V', level: 1, hp: 999, maxHp: 999, atk: 1, def: 999, spd: 5 }],
    foes: [{ id: 'm0', ref: 'scree-shell', name: 'Wall', hp: 9999, maxHp: 9999, atk: 1, def: 9999, spd: 1 }],
  });
  const stall = await R.engine.run({
    state: tank, rng: R.mulberry32(1),
    router: R.makeRouter({ seats: { ai: R.policies.partyAi({ items, inventory: {} }) }, defaults: { party: 'ai', foe: 'ai' } }),
    emit: () => { }, maxRounds: 50,
  });
  if (!stall.over) fails.push('termination: a stalemate battle did not end');
  return fails;
}

// ---- main ------------------------------------------------------------------
function pad(s, n, right) {
  s = String(s);
  return right ? s.padStart(n) : s.padEnd(n);
}
async function main() {
  // scenarios straight out of encounters.json — new content is covered for free
  const scenarios = [];
  for (const L of LEVELS) {
    for (const [zone, zd] of Object.entries(encounters)) {
      if (!(zd.chancePerStep > 0) || !(zd.groups || []).length) continue;    // road/town: safe by design
      (zd.groups || []).forEach((g, i) => {
        scenarios.push({
          id: zone + '-' + (i + 1), zone, level: L.level,
          group: g.monsters.slice(), weight: g.weight,
          env: ENVELOPES[zone] || null, assert: L.assert && !!ENVELOPES[zone] && !ENVELOPES[zone].advisory,
        });
      });
    }
  }

  const rows = [];
  for (const sc of scenarios) rows.push(await runScenario(sc));
  const props = await propertyTests();

  // verdicts
  const fails = [];
  for (const r of rows) {
    r.fail = [];
    if (!r.env) continue;
    if (r.winRate < r.env.win) r.fail.push('win ' + (r.winRate * 100).toFixed(1) + '% < ' + (r.env.win * 100) + '%');
    if (r.meanRounds < r.env.rounds[0] || r.meanRounds > r.env.rounds[1])
      r.fail.push('mean rounds ' + r.meanRounds.toFixed(2) + ' outside ' + r.env.rounds.join('-'));
    if (r.capped) r.fail.push(r.capped + ' battles hit the round cap');
    if (r.fail.length && r.assert) fails.push(r.id + ' L' + r.level + ': ' + r.fail.join('; '));
  }
  for (const f of props) fails.push('ENGINE ' + f);

  if (AS_JSON) {
    console.log(JSON.stringify({ n: N, seed: SEED0, rows, props, fails }, null, 2));
    process.exit(fails.length ? 1 : 0);
  }

  const v = member(1), v2 = member(2);
  console.log('BATTLE SIM — ' + N + ' seeded battles/scenario, run seed ' + SEED0);
  if (TUNE) console.log('*** TUNED (proposal, NOT the committed data): ' + JSON.stringify(TUNE) + ' ***');
  console.log('party: Vesper L1 ' + JSON.stringify({ hp: v.maxHp, atk: v.atk, def: v.def, spd: v.spd }) +
    '  L2 ' + JSON.stringify({ hp: v2.maxHp, atk: v2.atk, def: v2.def, spd: v2.spd }) +
    '  bag ' + JSON.stringify(startInventory));
  console.log('seat: party -> ai (Rules.policies.partyAi), foes -> Rules.policies.monsterAi, ' +
    'scheduler ' + R.schedulers.commitThenResolve.name);
  console.log('');
  const H = ['scenario', 'lv', 'group', 'win%', 'mean', 'med', 'max', 'hp left', 'xp', 'gold', 'drop', 'tonic', ''];
  const W = [11, 3, 30, 7, 6, 4, 4, 9, 6, 6, 6, 6, 0];
  console.log(H.map((h, i) => pad(h, W[i], i >= 3 && i < 12)).join(' '));
  console.log('-'.repeat(W.reduce((t, x) => t + x + 1, 0)));
  let lastLv = null;
  for (const r of rows) {
    if (lastLv !== null && r.level !== lastLv) console.log('');
    lastLv = r.level;
    const mark = r.fail.length ? (r.assert ? '  FAIL ' + r.fail.join('; ') : '  (advisory) ' + r.fail.join('; ')) : '';
    console.log([
      pad(r.id, W[0]), pad(r.level, W[1]), pad(r.group.join('+'), W[2]),
      pad((r.winRate * 100).toFixed(1), W[3], true),
      pad(r.meanRounds.toFixed(2), W[4], true),
      pad(r.medRounds, W[5], true), pad(r.maxRounds, W[6], true),
      pad(r.meanHp.toFixed(1) + '/' + r.maxHp, W[7], true),
      pad(r.meanXp.toFixed(1), W[8], true), pad(r.meanGold.toFixed(1), W[9], true),
      pad(r.dropRate.toFixed(2), W[10], true), pad(r.tonicRate.toFixed(2), W[11], true),
    ].join(' ') + mark);
  }
  console.log('');
  console.log('envelopes: ' + Object.entries(ENVELOPES).map(([z, e]) =>
    z + ' win>=' + e.win + ' rounds ' + e.rounds.join('-') + (e.advisory ? ' (advisory)' : '')).join(' · '));
  console.log('engine property tests: ' + (props.length ? props.length + ' FAILED' : '6 passed ' +
    '(determinism, seed-sensitivity, purity, retargeting, order-independence, termination)'));
  if (fails.length) {
    console.log('');
    console.log('FAILURES (' + fails.length + '):');
    for (const f of fails) console.log('  - ' + f);
    process.exit(1);
  }
  console.log('ALL ENVELOPES GREEN');
}
main().catch(e => { console.error(e); process.exit(1); });
