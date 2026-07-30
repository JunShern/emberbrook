# Combat / economy / character ecosystem — architecture & contracts

User-ratified 2026-07-30. The standing quality bar for everything here (user's
parting directive): **scalable, well-organized systems with repeatable-yet-
generalizable workflows** — every schema and contract below must make sense for
chapter 3+ content, not just the valley.

## The one design rule: lock the boundaries, swap the middles

The user wants battles/items/stats/leveling as *concepts*, with the freedom to
replace any *implementation* (e.g. turn-based → real-time) cheaply. What is
invariant across every battle system we might ever build:

- the party walks around with stats, XP, equipment, gold, items (STATE);
- content is defined somewhere (RULES DATA);
- something decides "an encounter happens here" (ENCOUNTER DIRECTOR);
- the battle runs opaquely and returns a result (BATTLE CONTRACT);
- the result mutates state (xp/gold/drops/death) and play continues.

So the architecture is three layers, and modules only ever talk through them:

```
RULES DATA (public/game/*.json)      — pure content, no code
GAME STATE (public/js/game_state.js) — one serializable store, save/load
SYSTEMS    (public/js/*.js)          — swappable modules w/ narrow contracts
```

## Layer 1 — rules data (`public/game/`)

| file | holds | notes |
|---|---|---|
| `monsters.json` | monster defs keyed to the zone taxonomy | families/tiers so palettes scale to later regions |
| `items.json` | consumables, weapons, armor, materials | statMods per slot; price is the single value source |
| `encounters.json` | per-zone rates + weighted groups | zone ids = the canonical meadow/forest/crag/road/water |
| `growth.json` | XP curve + per-character base/growth | party-of-N; characters carry `active` |
| `shops.json` | per-shop stock + buy/sell rates | keyed by interior scene key |

Balancing/designing content = editing JSON in the fast loop. No engine changes.

## Layer 2 — game state (`public/js/game_state.js`, coordinator-owned)

`window.GS` — the ONLY holder of mutable game state. Serializable to one JSON
blob = the save system. API (see file header for exact signatures): party &
stats (with derived atk/def from equipment), inventory add/remove, gold
spend/earn, equip/unequip, `grantXp` (curve-driven level-ups returned as
events), `applyBattleResult`, `save()/load()` (localStorage), `on(event, cb)`
for UI. Systems NEVER keep their own copies of state.

## Layer 3 — system contracts

**Battle** — `Battle.start(spec, party, opts) → Promise<result>`
- `spec`: `{zone, group:[monsterIds], seed, backdrop}` (built by the director).
- `result`: `{outcome:'victory'|'defeat'|'fled', xp, gold, drops:[itemId],
  turns, partyHp:{charId:hp}, log:[events]}`.
- The overworld/state layer neither knows nor cares what happens inside. A
  real-time battle module is a drop-in replacement behind this one signature.

**Rules kernel** (`battle_rules.js`) — pure, seeded, stateless functions:
`damage(att, def, rng)`, `applyAction(battleState, action, rng) → {state,
events}`, turn ordering. Shared by ANY battle implementation, so a
presentation/pacing swap never changes game balance. Damage v1:
`max(1, round((atk*2 - def) * uniform(0.85, 1.15)))`. RNG: mulberry32(seed) —
same seed, same battle, always (headless testing + replays).

**Controller router** — party members ≠ players. A routing table
`{charId → 'p1'|'p2'|'ai'}`, mutable mid-battle (the couch-co-op swap
mechanic). The engine asks the router "who decides for X?" and awaits an
action from that seat. AI is just another seat. v1 ships with everything
routed to p1; the seams are the point.

**Decision scheduler** (swappable policy INSIDE the battle module) —
v1 `commit-then-resolve`: collect one action per living combatant (parallel
menus capable — each human seat has its own cursor), then resolve in spd
order. Alternative policies (ATB timers, initiative rounds, real-time) replace
this object without touching the rules kernel or router.

**Encounter director** (`encounters.js`) — consumes the player's zone stream
(same ground truth as `SIM.zone(x,z)`); per step in a hostile zone past a
grace count, rolls the zone's chance; on hit builds a spec from the weighted
groups and calls `Battle.start` through the scene-transition fade (classic
cut-to-battle; backdrop per zone type — placeholder art first, pre-rendered
later). Roads are safe by design (rewards route-following; ties into the
legibility program).

**Shop** (`shop.js`) — `openShop(shopId)`: buy/sell against GS at
`shops.json` rates, UI behind the existing E-prompt system in the three shop
interiors.

**Menu** (`menu.js`) — pause menu: stats/XP/level, equip, use item, save.
Reads/writes GS only.

## Co-op seating (canon)

Party-of-N from day one (data already has Vesper + Maren, Maren `active:false`
until her story joins). Two-seat play = the router mapping seats to characters
+ parallel decision menus in whatever scheduler is live. Player 2 dropping out
= remap seats to `ai`/`p1`. Input plumbing (split keyboard now — WASD vs
arrows — gamepads later) is orthogonal and does not block battle v1.

## Testing (non-negotiable)

- `tools/battle_sim.mjs`: run N seeded battles headlessly, assert balance
  envelopes (e.g. level-1-2 party vs meadow groups: win rate ≥95%, mean
  turns 3-6; crag groups at level 2 should be dangerous). Balance is a test,
  not a vibe.
- `tools/economy_test.mjs`: buy/sell round-trips, equip stat deltas, save/load
  identity, level-curve monotonicity.
- Existing suites stay green: cine 667/0, slice 532/0.

## File custody (today)

- play3d.html: coordinator only (hook lines exist at the bottom; agents ship
  self-contained module files that no-op without their data).
- game_state.js + all public/game/*.json schemas: coordinator. Content
  additions by agent request (precedent: grant data fields fast).
- battle_rules.js / battle_turnbased.js / encounters.js: battle-core agent.
- shop.js / menu.js: economy agent.

## The vertical loop (today's target)

meadow encounter → battle v1 (Attack/Item/Flee) → xp/gold/drop → level ping →
Dellhollow → sell drop, buy weapon → equip in menu → hit harder. One thin loop
through every contract before any system deepens.
