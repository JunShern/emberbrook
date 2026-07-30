# Battle core — design (battle-core agent)

Written 2026-07-30 before implementation, per the workflow rule. Builds against
`docs/plans/combat-ecosystem.md` (ratified). Everything here is a *contract*
statement: if a name or shape appears below, code depends on it.

Files owned by this agent:

| file | role | purity |
|---|---|---|
| `public/js/battle_rules.js` | rules kernel + engine policies | pure, node-loadable, no DOM, no `Date.now`, no `Math.random` |
| `public/js/battle_turnbased.js` | `window.Battle` — v1 presentation + human seats | browser, DOM |
| `public/js/encounters.js` | `window.Encounters` — encounter director | browser, reads `SIM`/`GS` |
| `tools/battle_sim.mjs` | headless balance harness | node |

---

## 0. Three red-team findings against the ratified contracts

Raised to "main" *before* being worked around (see DAYLOG).

**(a) "step" is a DISTANCE, not a physics tick.** `encounters.json` says
`grace: 30, chancePerStep: 0.02`. `phys()` runs at 60 Hz and `SPD = 0.075 u`,
so if a step were a tick, grace would be 0.5 s and the mean gap between battles
would be **50 ticks = 0.83 s**. Unplayable. This design defines

```
one encounter step = STEP_UNIT (1.0 world unit) of horizontal travel
```

accumulated across physics ticks. Then grace 30 = 30 u of walking, the mean
post-grace gap in meadow is 50 u, and the ow-valley tile is 280 u across → a
crossing sees ~3-4 encounters. `zones.json` cell size is 1.25 u, so a step is
also ~one terrain cell — the number keeps its meaning if `SPD` is ever retuned.
Consequence: **the director computes its own distance from `getPos()`**, so the
movement-loop hook is the zero-argument `Encounters.tick()`.

**(b) The `mean turns 3-6` envelope may be unreachable at party-of-1.**
Level-1 Vesper with start equipment is `atk 9, def 7, hp 34, spd 6`. Against
`reed-nibbler` (`hp 16, def 2`) damage is `round((9*2 - 2) * u) = 14..18` — a
~60 % one-shot. Group `[reed-nibbler]` therefore ends in ~1.4 rounds, not 3-6,
and no formula-preserving change fixes that except monster HP. Only Vesper is
`active` in growth.json, so every "turn" is one player action; the envelope was
written for a party. Measured numbers + a proposed `monsters.json` HP set go to
"main" as a tuning request; the sim asserts the envelope either way so the
decision is recorded as a test, not a vibe.

**(c) `GS` has no way to set HP outside a battle result.** Defeat handling
needs "revive at 1 HP". v1 does it with a second `applyBattleResult({outcome:
'defeat', partyHp:{...:1}})` call (public API only, emits the normal events) and
requests `GS.setHp(charId, hp)` from the coordinator. Also noted:
`Rules.derive.charStats()` duplicates `GS.stats()` math because the kernel must
run in node without `GS`; the fix is for `GS.stats` to delegate to the kernel.

---

## 1. Battle state shape (kernel-owned, serializable, immutable-by-convention)

`applyAction` never mutates its input; it returns a new state. Nothing in the
state is a function, a DOM node or a reference into `GS`.

```js
state = {
  round: 0,                       // completed rounds
  over: null,                     // null | 'victory' | 'defeat' | 'fled'
  party: [ combatant, ... ],      // authored order = stable tie-break order
  foes:  [ combatant, ... ],
  fled: false,
}

combatant = {
  side: 'party' | 'foe',
  id: 'vesper' | 'm0',            // UNIQUE across the whole state
  ref: 'vesper' | 'reed-nibbler', // charId / monsterId — the data key
  name: 'Vesper' | 'Reed Nibbler A',
  level: 1,                       // party only
  hp, maxHp, atk, def, spd,
  dead: false,
  statuses: {},                   // reserved; v1 writes nothing
}
```

Foe ids are positional (`m0`, `m1`) so duplicate monsters are distinguishable;
display names get FF-style ` A`/` B` suffixes only when duplicated.

## 2. Action shape

```js
{ type:'attack', by:'vesper', target:'m0' }
{ type:'item',   by:'vesper', target:'vesper', item:'tonic', effect:{heal:30} }
{ type:'flee',   by:'vesper' }
```

`effect` is **carried by the action**, resolved by whoever built it (a seat
provider that knows `items.json`/`GS`). The kernel therefore needs no item data
and stays content-free. Unknown `type` fizzles with a `{t:'noop'}` event rather
than throwing — a future scheduler can emit actions this kernel has never heard
of and the battle still terminates.

Retargeting is the kernel's job: if `target` is dead (or missing) the action
retargets to the first living combatant of the intended side; if that side is
empty the action fizzles. Deterministic, so collection order never matters.

## 3. Events (the presentation contract)

Every state change emits data, never pixels. The battle screen and the log line
render these; `result.log` is the concatenation.

```js
{t:'round',  n}
{t:'action', by, kind}                       // 'attack'|'item'|'flee'
{t:'damage', by, target, amount, killed}
{t:'heal',   by, target, amount, item}
{t:'flee',   by, ok, chance}
{t:'ko',     id, side}
{t:'noop',   by, why}
{t:'end',    outcome, rounds}
```

## 4. Kernel API (`window.Rules` / `module.exports`)

```js
mulberry32(seed) -> rng()                 // [0,1)
hashSeed(...parts) -> uint32              // FNV-1a over strings/numbers
uniform(rng, lo, hi)
damage(atk, def, rng) -> max(1, round((atk*2 - def) * uniform(0.85,1.15)))
fleeChance(state) -> 0..1                 // party spd vs foe spd
order(state) -> [combatantId, ...]        // spd desc, stable authored tie-break
makeState({party, foes}) -> state
applyAction(state, action, rng) -> {state, events}
checkOver(state) -> state                 // sets .over
rewards(state, monstersData, rng) -> {xp, gold, drops:[itemId]}
derive.charStats(growth, items, {id, level, equip}) -> {hp,atk,def,spd,maxHp}
derive.partyFromGS(gs) / derive.foesFromGroup(monsters, [ids])
schedulers.commitThenResolve                // pure engine policy (below)
policies.partyAi({inventory, items}) / policies.monsterAi()
```

## 5. Policy interface (the scheduler seam)

The scheduler is a plain object with one method. It owns **time and ordering**
and nothing else — it never computes a number and never knows what a seat is.

```js
scheduler = {
  name: 'commit-then-resolve',
  async run(ctx) -> state            // returns the final state
}

ctx = {
  state,                              // starting state
  rules,                              // the kernel (never reaches around it)
  rng,                                // the battle's seeded rng
  decide(actorId, state) -> Promise<action>,   // asks the ROUTER, awaits a seat
  emit(events, state),                // presentation feed (may be a no-op)
  parallel: true,                     // may collect across seats concurrently
}
```

v1 `commit-then-resolve`, per round:

1. `emit({t:'round'})`.
2. Collect one action per living party member. Members are **grouped by seat**
   (`router.seatFor(id)`) and the groups are awaited with `Promise.all`:
   sequential within a seat (one cursor per human), concurrent across seats.
   That is the parallel-menus structure the co-op design asks for, present in
   v1 even though v1 has one seat.
3. Collect one action per living foe (seat `ai`).
4. Sort all actions by `rules.order(state)` and apply each through
   `rules.applyAction`, skipping dead actors, emitting events as they land.
5. `rules.checkOver`; a successful flee ends immediately.

**Swap test (the standing question): can this be replaced by ATB or real-time
without touching `battle_rules.js` or the router?** Yes. An ATB policy keeps its
own gauge array, calls `ctx.decide(id)` when a gauge fills, applies exactly one
action through `ctx.rules.applyAction`, and emits the same events. It needs no
new kernel function (the kernel's unit of work is one action, not one round) and
no router change (the router maps ids to seats independently of *when* it is
asked). A real-time policy does the same on a `requestAnimationFrame` clock and
resolves `decide` from held keys instead of a menu. `order()` is used *only* by
commit-then-resolve; an ATB policy simply ignores it.

## 6. Controller router API

```js
Battle.router = {
  table()            -> { vesper:'p1', m0:'ai', ... }   // live, readable
  seatFor(id)        -> 'p1'|'p2'|'ai'
  set(id, seat)      -> seat        // legal MID-BATTLE: the co-op swap
  setSeat(seat, ids) -> void        // bulk remap (p2 drops out -> 'ai')
  seats              -> { p1: provider, p2: provider, ai: provider }
  default(side)      -> seat        // party->'p1', foe->'ai' in v1
}

provider = { name, decide(actorId, state, api) -> Promise<action> }
```

`api` gives a provider what it cannot derive from `state`: `{items, inventory,
useItem(id), ui}`. The AI provider ignores it. v1 fills `p1` with the menu
provider, `p2` with the same menu provider (unbound until a second seat exists),
`ai` with `Rules.policies.monsterAi`. A caller can flip Vesper to `ai` in the
middle of a round and the very next `decide` obeys — the table is read per
decision, never cached.

## 7. Battle screen (v1 presentation)

FF-classic single overlay, appended to `#s` (so it letterboxes with the game,
like the existing `sgp` prompt banner), `position:absolute;inset:0`, above the
scene and below the transition veil.

```
+--------------------------------------------------------------+
|  backdrop: per-zone gradient canvas (swappable lookup)        |
|                                                              |
|    ▟▙  Reed Nibbler A        -17            [ Vesper      ]  |
|   ▟██▙ hp bar                                [ HP 31/34   ]  |
|    ▟▙  Reed Nibbler B                        [ Lv 1       ]  |
|                                                              |
|  > Vesper attacks Reed Nibbler A. 17 damage.   (log line)    |
+--------------------------------------------------------------+
| [Attack] [Item] [Flee]        (command panel, cursor-driven) |
+--------------------------------------------------------------+
```

- Palette taken from play3d's own HUD/prompt idiom, not invented: text
  `#e7ddd0`, panels `#000b`, borders `1px solid #3a2c20`, accent `#e9a24b`,
  `text-shadow:0 1px 2px #000`, `border-radius:8px`. Body text `system-ui`,
  numeric readouts monospace (play3d's HUD font).
- Foes are CSS silhouettes (no new 3D/art work); the sprite lookup
  `Battle.sprites[family]` is a swappable table like the backdrop table.
- `Battle.backdrops = {meadow, forest, crag, water, default}` — key comes from
  `spec.backdrop` (`encounters.json → battleBackdrop`). Replacing a gradient
  with a pre-rendered PNG later is one table entry.
- Damage numbers float up and fade at the target's card.
- Enter/exit through a 350 ms linear black veil, matching `sgFade`'s feel and
  duration constants. `Battle` owns its own veil because `sgFade` is
  play3d-internal; it will use `opts.fade` if a caller supplies one.
- Input: WASD **and** arrows move the cursor, Enter/Space/E confirm, Esc/X back.
  A **capture-phase** `keydown` listener on `window` with
  `stopImmediatePropagation()` blocks play3d's own key handlers while a battle
  is up, so the player cannot walk behind the overlay even before the freeze
  hook lands.
- `Battle.active` is `true` from the first frame of the fade to the last, so the
  overworld can freeze itself with one line.

## 8. `Battle.start` contract (unchanged from the ecosystem doc)

```js
Battle.start(spec, party, opts) -> Promise<result>
spec  = {zone, group:[monsterId], seed, backdrop}
party = [{id, name, level, hp, maxHp, atk, def, spd}]   // built by the caller from GS
opts  = {gs, monsters, items, scheduler, router, fade, view, autoplay}
result= {outcome, xp, gold, drops:[itemId], turns, partyHp:{charId:hp}, log:[events]}
```

**Swap test: can `Battle.start` be reimplemented real-time without the overworld
noticing?** Yes — the overworld's entire surface is `Battle.active`, the promise,
and `result`. It never sees `state`, the scheduler, the router or the DOM. XP,
gold and drops are *reported*, never applied: `GS.applyBattleResult` is the
world's job, so a replacement module cannot accidentally own economy.

## 9. Encounter director

```js
Encounters.attach(getZone, getPos, opts) // getZone(x,z)->type|null, getPos()->{x,y,z}
Encounters.tick(dist?)                   // per physics step; computes its own distance
Encounters.setEnabled(bool)
Encounters._debug()                      // {enabled, zone, steps, grace, acc, rolls, battles, seed}
```

- No-ops (and says so once in `_debug`) if `GS.ok` is false, `window.Battle` is
  missing, `getZone` returns null, or the zone has `chancePerStep: 0`. Roads and
  towns are safe by construction: `road` ships rate 0 and an unknown zone name
  is treated as safe rather than defaulted.
- Grace is (re)armed on: attach, zone change, battle end, and any position jump
  greater than `TELEPORT_U` (3 u) in one tick — which is how scene transitions
  and respawns are recognised without play3d telling us.
- Roll: `rng = mulberry32(hashSeed(runSeed, zone, stepIndex))` — a fresh rng per
  step, seeded from a **run seed** (default constant `0xEMBER1`, overridable via
  `opts.seed`), so a headless test replays an entire walk exactly. No
  `Math.random`, no `Date.now`.
- On a hit: pick a group by weight (same seeded rng stream), build
  `spec = {zone, group, seed: hashSeed(runSeed, zone, stepIndex, 'battle'),
  backdrop}`, fade → `Battle.start` → `GS.applyBattleResult(result)`.
- Defeat (v1, **TODO taste review**): revive at 1 HP, halve gold, place the
  player at the last known spawn (`SIM.arrival()` or the attach position) via
  `opts.respawn`. No game-over screen yet.

## 10. Test scenarios (`tools/battle_sim.mjs`)

N = 500 seeded battles per scenario, party = level-1 Vesper with start
equipment, seat `ai` for the party using `Rules.policies.partyAi` (attack the
lowest-HP living foe; drink a tonic at < 30 % HP while stock lasts, 2 tonics per
the `growth.json` start inventory).

| scenario | group | assert |
|---|---|---|
| meadow-1 | `[reed-nibbler]` | win ≥ 0.95, mean rounds 3-6 |
| meadow-2 | `[reed-nibbler, reed-nibbler]` | win ≥ 0.95, mean rounds 3-6 |
| meadow-3 | `[brook-sprite]` | win ≥ 0.95, mean rounds 3-6 |
| forest-1..4 | the four `forest` groups | win ≥ 0.70 |
| crag-1 | `[scree-shell]` | win ≥ 0.40 |
| crag-2 | `[scree-shell, brook-sprite]` | win ≥ 0.40 |

Output is a table (win rate, mean/median/max rounds, mean party HP left, deaths,
mean xp/gold); exit 1 on any breach. The harness also asserts **determinism**
(same seed → identical event log) and **termination** (no battle exceeds 200
rounds), because those are properties of the engine rather than of the numbers.

## 11. Load order / integration

`battle_rules.js` → `battle_turnbased.js` → `encounters.js`, all after
`game_state.js`. Every module attaches itself and waits; nothing runs until the
coordinator's two one-line hooks land in `phys()`. Before then the modules are
inert and the page behaves exactly as it does today.
