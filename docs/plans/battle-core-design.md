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

Raised to "main" *before* being worked around (see DAYLOG). **All three were
ruled on and are now settled** — resolutions recorded inline below.

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

> **RATIFIED.** Measured cadence over 4000 runs per zone: meadow mean gap
> **80.2 u** (17.8 s of walking, median 65, p10-p90 36-144, 3.5 encounters per
> 280 u tile crossing), forest 48.9 u, crag 53.4 u, water 58.9 u, road safe.
> The per-step seeding was checked for the classic "first draw from a freshly
> seeded PRNG" bias and is clean: P(first draw < 0.02) = 0.02008 over 2,000,000
> fresh `mulberry32(hashSeed(seed, zone, step))` instances, mean first draw
> 0.49965. The rate authored in JSON is the rate the player feels.

**(b) The `mean turns 3-6` envelope may be unreachable at party-of-1.**
Level-1 Vesper with start equipment is `atk 9, def 7, hp 34, spd 6`. Against
`reed-nibbler` (`hp 16, def 2`) damage is `round((9*2 - 2) * u) = 14..18` — a
~60 % one-shot. Group `[reed-nibbler]` therefore ends in ~1.4 rounds, not 3-6,
and no formula-preserving change fixes that except monster HP. Only Vesper is
`active` in growth.json, so every "turn" is one player action; the envelope was
written for a party. Measured numbers + a proposed `monsters.json` HP set go to
"main" as a tuning request; the sim asserts the envelope either way so the
decision is recorded as a test, not a vibe.

> **RESOLVED.** The band was relaxed to **meadow mean 1-4 rounds** (monsters stay
> cheap, fights stay snappy — no HP inflation). The sim then found something
> worse than a band mismatch: `[duskpad, duskpad]` won **0 of 500** battles at
> level 1 and `[bramble-shade, duskpad]` 17.5 % — certain death, not danger.
> Granted and applied to `monsters.json` (coordinator custody): duskpad atk
> 8→6, bramble-shade 9→7, weir-eel 9→7, and — deliberately the other way —
> scree-shell atk 7→**9**, because the crag was passing its envelope at 100 %
> win over 4-6 rounds, which is grind rather than the intended danger. Every
> envelope is now green at n=500 for levels 1 and 2, with the crag at 78 %/74 %
> and real tonic attrition. See §11 for why the dial was atk and why it is the
> coarsest one available.

**(c) `GS` has no way to set HP outside a battle result.** Defeat handling
needs "revive at 1 HP". v1 does it with a second `applyBattleResult({outcome:
'defeat', partyHp:{...:1}})` call (public API only, emits the normal events) and
requests `GS.setHp(charId, hp)` from the coordinator. Also noted:
`Rules.derive.charStats()` duplicates `GS.stats()` math because the kernel must
run in node without `GS`; the fix is for `GS.stats` to delegate to the kernel.

> **BOTH GRANTED AND LIVE.** `GS.setHp(charId, hp)` exists and is what the defeat
> path uses. `GS.stats` now delegates to `Rules.derive.charStats(GS.data.growth,
> GS.data.items.items, ch)` — note the second argument is the **items MAP**, not
> the whole file; the kernel accepts either, because a silent signature mismatch
> there would change every stat in the game. `tools/encounter_sim.mjs` asserts
> the two agree on the shipped party. A third grant arrived unasked and is
> deliberately NOT used in battle: `GS.useItem` applies healing to world state,
> which would double-heal against battle state and judges "already full" from
> stale pre-battle HP. In-battle items consume via `GS.removeItem` only and heal
> inside the battle state; `result.partyHp` is the single write-back. Ruled.

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
opts  = {gs, monsters, items, scheduler, router, fade, view, autoplay, speed, headless}
result= {outcome, xp, gold, drops:[itemId], turns, partyHp:{charId:hp}, log:[events]}
```

**Swap test: can `Battle.start` be reimplemented real-time without the overworld
noticing?** Yes — the overworld's entire surface is `Battle.active`, the promise,
and `result`. It never sees `state`, the scheduler, the router or the DOM. XP,
gold and drops are *reported*, never applied: `GS.applyBattleResult` is the
world's job, so a replacement module cannot accidentally own economy.

**AUTOMATED PLAYTESTS MUST PASS `{speed: 0}`** (or `{headless: true}`). Event
pacing is `setTimeout`-based — deliberately, because rAF is throttled to nothing in
a background tab and an rAF-paced battle would not advance at all there. But Chrome
applies *intensive* timer throttling after ~5 minutes hidden (one wake per minute),
so an autoplay battle at any `speed > 0` takes tens of minutes in a hidden tab.
`speed: 0` skips every wait and the battle resolves in microtasks. Coordinator's
harness canon, 2026-07-30.

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
- Grace is (re)armed on: attach, battle end, any position jump greater than
  `TELEPORT_U` (3 u) in one tick (which is how scene transitions and respawns are
  recognised without play3d telling us), and **entry from a SAFE zone only** —
  never on a hostile → hostile boundary, which would turn every shoreline into an
  encounter-free corridor. See §9a for the measurement that forced this rule.
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

### 9a. Zone-boundary grace farming — FOUND, FIXED, REGRESSED

Found by the coordinator's browser playtest 2026-07-30 (zig-zagging a
water/crag/road/meadow junction), measured, initially deferred, then **un-deferred
and fixed the same day** once the measurement showed it was not an exploit but the
default outcome of scenic walking. Kept in full because the reasoning is the useful
part.

**The defect.** Every zone change called `regrace('zone-entry')`, resetting
`graceLeft` to the new zone's grace *and* zeroing the step accumulator. Walking
**along** a boundary therefore flipped zone more often than the grace it re-armed
(20-30 u of grace against a 1.25 u zone cell), so the counter never matured.
Measured before the fix, 600 u walked alternating meadow/crag, seed 7:

| flip | zone changes | steps | **rolls** | battles |
|---|---|---|---|---|
| never (control) | 0 | 150\* | **120** | 1 |
| 0.5 u | 1199 | **0** | **0** | 0 |
| 1 u | 599 | 200 | **0** | 0 |
| 2 u | 299 | 500 | **0** | 0 |
| 4 u | 149 | 500 | **0** | 0 |
| 8 u | 74 | 575 | **0** | 0 |
| 20 u | 29 | 590 | **0** | 0 |

\* the control's low step count is an artifact of the throwaway probe's
*synchronous* tick loop — see the testing note at the end of this section.

Zero rolls at every spacing up to 20 u. Since a roll required travelling farther
between zone changes than the zone's own grace, and `zones.json` has a 1.25 u
cell, **any** shoreline, treeline or scree-edge walk defeated it — no deliberate
zig-zagging needed. A player following the pretty line would have concluded that
battles were broken.

**Two mechanisms, both fixed** (fixing only the first leaves tight zig-zags free):

1. the `graceLeft` reset — dominant, live up to ~30 u flip spacing;
2. the `acc = 0` reset — bit below ~1 u spacing, where even `steps` stopped
   climbing (0 steps over 600 u at 0.5 u flips).

**The fix (adopted option 1): grace comes from SAFETY, not from novelty.** Only
arriving from a zone that is not hostile — `road`, a town, or any zone name absent
from `encounters.json` — re-arms grace. A hostile → hostile crossing carries both
the grace counter and the accumulator straight across, because you never stopped
being in danger. Teleport/scene-handoff re-grace (>3 u jump in one tick) is
unchanged and remains correct: an arrival really is an arrival. Post-battle and
attach re-grace are unchanged.

Post-fix, same walk over 1200 u (seed 7) — every spacing now rolls, and `steps`
tracks distance at every spacing:

| flip | steps | rolls | battles | mean gap |
|---|---|---|---|---|
| never (control) | 1199 | 839 | 11 | 103 u |
| 0.5 u | 1199 | 839 | 11 | 103 u |
| 1 u | 1199 | 789 | 16 | 71 u |
| 2 u | 1199 | 699 | 20 | 57 u |
| 4 u | 1199 | 806 | 16 | 75 u |
| 8 u | 1199 | 756 | 18 | 67 u |
| 20 u | 1199 | 756 | 19 | 63 u |

**The road reward is CANON, not an open question.** Coordinator ruling
2026-07-30, carried to the review board as a design note: *roads and their
shoulders are the only quiet; weaving on and off a road is peaceful by design; the
cost is that you must keep returning to safety.* Measured: 0 battles over 1200 u
flipping road/meadow every 20 u. It follows directly from "safe zones are the sole
source of quiet", which is the legibility programme's own thesis that following the
route is rewarded.

It is **asserted by a test on purpose**, so a future reader of the exploit half of
this section cannot quietly "fix" the reward away while removing the defect. If the
ruling is ever revisited the change is one line — require N steps inside the safe
zone before it grants grace — and the pinning test is what will fail loudly and
force that decision to be explicit rather than accidental.

**Respite consequence — measured, and NO TUNING PROPOSED.** The coordinator
pre-approved a `meadow` grace/rate change if post-fix cadence tightened below
~60 u, and forest/crag changes below ~35 u. Measured over 4 seeds x 2400 u per
zone (129-184 observed inter-battle gaps each):

| zone | mean gap | per-seed | median | p10-p90 |
|---|---|---|---|---|
| meadow | **72.9 u** | 74.3 / 69.4 / 76.8 / 71.5 | 61 u | 35-126 u |
| forest | 54.0 u | 55.3 / 52.9 / 63.8 / 46.7 | 45 u | 24-102 u |
| crag | 51.1 u | 48.2 / 54.2 / 46.3 / 57.1 | 42 u | 24-90 u |
| water | 55.2 u | 48.4 / 58.8 / 53.8 / 61.3 | 46 u | 28-96 u |
| road | — | no rolls, ever | — | — |

Meadow lands at 72.9 u, inside the 60-90 u "costs but breathes" target; forest,
crag and water sit at 51-55 u, comfortably above the 35 u floor below which their
menace would have needed relief. **The shipped numbers already produce the target
texture, so nothing is proposed** — per the standing instruction not to tune for
its own sake. The reason cadence barely moved is that post-battle grace was never
part of the defect: a straight walk's gap has always been `grace + 1/rate`, and
only *boundary* walks were broken.

**Regression, in `tools/encounter_sim.mjs`** (shipped with the fix, as specified):
the control row plus all six flip spacings, asserting both `rolls` (mechanism 1)
and `steps` (mechanism 2), plus the road-hug row that pins the deliberate reward.
One trap it must respect, which is why `flipWalk` awaits every tick: a synchronous
tick loop leaves the director `busy` forever after the first battle fires, because
`fire()` is async and its `finally` never runs until the loop yields. That is what
deflated the control row in the pre-fix table above, and an unawaited regression
would read "control barely walked" as success. The harness asserts the control's
step count honestly for exactly this reason.

## 10. Test scenarios (`tools/battle_sim.mjs`)

N = 500 seeded battles per scenario, party = level-1 Vesper with start
equipment, seat `ai` for the party using `Rules.policies.partyAi` (attack the
lowest-HP living foe; drink a tonic at < 30 % HP while stock lasts, 2 tonics per
the `growth.json` start inventory).

Scenarios are **generated from `encounters.json`**, not listed in code, so a new
monster group is covered the moment it is authored. Envelopes are per zone
(ratified 2026-07-30; `water` is advisory — measured and printed, cannot fail the
build, because nobody has ratified water numbers):

| zone | assert |
|---|---|
| meadow | win ≥ 0.95, mean rounds 1-4 |
| forest | win ≥ 0.70, mean rounds 1-8 |
| crag | win ≥ 0.40, mean rounds 1-16 |
| water | win ≥ 0.50 (advisory) |

Level 1 is asserted; level 2 is run and printed as a progression check (the
ecosystem doc's "crag groups at level 2 should be dangerous").

Six ENGINE property tests run alongside the balance rows, because these are
properties of the code rather than of the numbers: determinism (same seed →
identical event log), seed-sensitivity (a different seed → a different battle, so
the rng is actually consumed), `applyAction` purity (it must not mutate its input
state), retargeting (an attack on a corpse lands on a living foe), collection-order
independence (resolving the same actions in a different submitted order gives the
same state), and termination (a stalemate still ends, via the round cap).

Output is a table (win rate, mean/median/max rounds, mean party HP left, deaths,
mean xp/gold); exit 1 on any breach. The harness also asserts **determinism**
(same seed → identical event log) and **termination** (no battle exceeds 200
rounds), because those are properties of the engine rather than of the numbers.

## 11. Balance dial characterization — WHICH KNOB TO TURN, AND HOW HARD

Measured on 2026-07-30 while tuning the forest, and written down because it is
the kind of thing that must outlive the session that discovered it. It follows
from the ratified damage formula and applies to every region we will ever author.

Let **E = 2·atk − def** be effective damage per hit (the ±15 % band is
*multiplicative* on E, so it scales this analysis rather than smoothing it). Then
for a party of size 1:

```
rounds to clear a group   ≈ Σ(foe HP) / E_party
rounds the party survives ≈ party HP / Σ(E_foe)
the party wins iff the first is smaller than the second
```

Both sides are ratios of small integers at level 1, so the outcome is a **step
function of monster atk**, not a curve:

| dial | damage moved per +1 | resolution at level-1 numbers | notes |
|---|---|---|---|
| monster `atk` | **2** per attacker per round | COARSEST — avoid | on a base of 3-11, ±1 atk is a ±20-40 % swing in incoming damage |
| party `def` | 1 per attacker per round | coarse, and party-wide | equipment already moves it; changing growth affects every fight in the game |
| monster `hp` | 0 incoming; +1 round per E of HP | **fine, and safest** | changes fight LENGTH without touching lethality |
| group size / weights | +1 body = +E incoming AND +HP | fine, and non-linear | the real difficulty dial: two of a thing is far worse than one of twice the size |

The measured cliff that produced this table: `duskpad` atk 8 → group
`[duskpad, duskpad]` wins **0.0 %** of 500 battles; atk 7 → **19.0 %**; atk 6 →
**100 %**. There is no integer in between. The same group at level 2 wins 100 %
at every one of those values, so the entire difficulty question lived inside a
one-point atk change in a one-level window.

Consequences that are now house rules:

1. **Never propose an atk change without measuring it** — use
   `battle_sim.mjs --tune='{"monster":{"atk":N}}'`, which exists so a balance
   proposal is measured before a coordinator-owned data file is edited.
2. **Author new content HP-first.** Pick the target round count R, set
   `Σ(foe HP) ≈ R · E_party`; then choose atk so that
   `Σ(E_foe) ≈ partyHP / (R + 1)` for a tense fight or `partyHP / 2R` for a safe
   one. Reach for group composition before reaching for atk.
3. **Balance is a function of party SIZE more than party level.** Adding Maren
   halves incoming damage per body and doubles outgoing, which loosens every
   envelope at once. Re-run the sim on any party change, not just on stat changes.
4. **A healing item is not HP.** A tonic is +30 HP but −1 round of output, so it
   only helps when `Σ(E_foe) < heal / 1 round`. Against 18 damage a round it loses
   ground, which is exactly why the untuned two-duskpad group was unwinnable
   rather than merely hard: the AI drank and still died.
5. **Flee is the pressure valve** and is spd-based, so a slow monster is
   survivable content and a fast one is a genuine threat. Measured escape chances
   for level-1 Vesper (spd 6): scree shell 69 %, reed nibbler 57 %,
   duskpad pair 39 %, brook sprite 33 %, weir eel **21 %**. Danger should be
   authored in spd as much as in atk — the eel is frightening mostly because you
   cannot leave.

## 12. Load order / integration

`battle_rules.js` → `battle_turnbased.js` → `encounters.js`, all after
`game_state.js`. Every module attaches itself and waits; nothing runs until the
coordinator's two one-line hooks land in `phys()`. Before then the modules are
inert and the page behaves exactly as it does today.
