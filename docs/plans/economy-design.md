# Economy & menu — design (shop.js, menu.js, ui_kit.js)

Agent: ECONOMY. Written before implementation, per the design-first mandate.
Builds against `docs/plans/combat-ecosystem.md` (ratified) and the rules data
already committed in `public/game/`.

## 0. The shape of every module here: DATA → OPS → VIEW

The single organising decision. Each module is split into two halves inside one
file, with a hard line between them:

```
OPS   pure operations over GS + rules data. No DOM, no keys, no timers.
      Shop.buy/sell/stock/prices, Menu.equipItem/statPreview/useItem/...
VIEW  a keyboard-driven DOM overlay that calls OPS and re-renders.
```

Consequences that pay for themselves immediately:

- `tools/economy_test.mjs` tests the OPS half **headlessly** — the real code the
  UI runs, not a re-implementation of the arithmetic. Nothing in either module
  touches the DOM at load time, so the files load cleanly in Node.
- A UI redesign (or a gamepad layer, or a battle-time item menu) reuses OPS
  untouched. Same "lock the boundaries, swap the middles" rule the architecture
  doc applies to battles.
- State lives only in GS. OPS is stateless; VIEW holds nothing but cursor
  positions, and re-derives every number from GS on each render (it also
  subscribes to `GS.on('change')`, so a level-up mid-menu is never stale).

`public/js/ui_kit.js` (`window.EBUI`) is the third file: the shared overlay +
keyboard-cursor + input-lock kit both UIs use. It exists so shop and menu cannot
drift into two different-looking, differently-keyed UIs, and so a future battle
menu inherits the same feel for free. Load order: `game_state.js`, `ui_kit.js`,
`shop.js`, `menu.js`.

## 1. Shop — where the prompt comes from (no coordinates in code)

`play3d.html`'s scene-graph layer has a rule worth copying exactly: *no scene
key, landmark id, radius, label or timing lives in code.* The shop prompt obeys
it too.

| question | answer, and where it comes from |
|---|---|
| which shop is this scene? | `shops.json` → the entry whose `sceneKey === ?scene=`. Verified: `del-item-int` / `del-weapon-int` / `del-armor-int` are real `scenegraph.json` nodes. A `sceneKey` that is not a graph node is **reported** (console warn + `Shop.debug().sceneKeyErrors`), never silently adapted. |
| where is the counter? | the interior's own `walk_pad_counter` mesh. Every interior builder emits one (`item_int_build.py`, `inn_int_build.py`, `cookhouse_int_build.py` — "interaction pads, hidden from the beauty render"). That mesh IS the interaction region: a box test, like the scene graph's camera bands, because a 1.7 × 1.0 m counter pad is not a circle. |
| what does the prompt say? | `"Talk to the " + shop.keeper` from `shops.json` (`chandler` / `weaponsmith` / `armorer`), formatted with the graph's own `defaults.promptFmt` (`{label}? [{key}]`) and its `defaults.key` (`e`) and `defaults.vTol`. |
| what does it look like? | a clone of `sgPrompt`'s banner: `absolute; left:50%; bottom:8%`, 14px monospace, `#e7ddd0` on `#000b`, `1px solid #3a2c20`, radius 8, key in `#e9a24b`, 120ms opacity fade. Same element position, same words, same colour — it must be indistinguishable from a door prompt, so it is literally the same recipe. Shop banner sits at `bottom:14%` only so it can never overlap the door banner if both were ever armed at once. |

Anchor resolution order (first hit wins):

1. `SIM.pad('walk_pad_counter')` — **requested hook**, 4 lines in play3d's SIM
   (see §6). With it, shop.js contains zero coordinates for any shop, ever.
2. optional `counter: [x,y,z]` on the shops.json entry (escape hatch for an
   interior that ever lacks a pad; no grant needed until it is used).
3. `COUNTER_FALLBACK` in shop.js — the pad centres read out of the shipped GLBs
   with `tools/glb_read.mjs`, with the exact regeneration command in a comment.
   Works today with no hook at all. All three Dellhollow shops share the
   interior template, so the table is one line: `[2.10, 0.04, 0.30]`.

Arming mirrors `sgTick` — arrival suppression (`armed=null` until the player is
first *outside* the region), leave-then-re-enter re-arms, `|dy| <= vTol`. The
door pad is 5.3 m from the counter pad, so the two prompts can never contend
(door radius 1.8). Driven by a rAF loop plus a 250 ms interval keepalive
(background tabs throttle rAF to nothing, and all headless verification happens
in a background tab); `Shop.tick()` is idempotent and public, so a test — or a
future `phys()` hook — can drive it by hand.

## 2. Shop UI flow

```
[E at counter]
  ┌──────────────────────────────────────────────────────────┐
  │ The Chandlery — chandler                        ⬤ 30 g   │
  │  ‹ BUY ›  SELL                              (←/→ tab)    │
  ├──────────────────────────────────────────────────────────┤
  │ ▸ Tonic                     12 g        (have 2)         │
  │   Hale Tonic                45 g        (have 0)         │
  │                                                          │
  │  River-herb draught. Restores 30 HP.                     │
  │  qty ‹ 2 ›   total 24 g   → 6 g left                     │
  ├──────────────────────────────────────────────────────────┤
  │ ↑↓ pick · ←→ qty · E/Enter buy · Esc/Q leave             │
  └──────────────────────────────────────────────────────────┘
```

- BUY list = `shops.json.stock` in authored order; price = `items.json.price ×
  rates.buyRate`. Rows the player cannot afford at qty 1 are dimmed and refuse
  with a shake + `"Not enough gold."`; the gold check is in OPS
  (`GS.spendGold` is the only spender), never in the view.
- SELL list = the player's inventory, `sellPrice = max(1, round(price ×
  rates.sellRate))`, dimmed/absent for anything `noSell` (a forward-compat item
  flag; nothing sets it yet). **Equipped gear is not sellable and needs no
  special case**: `GS.equip` removes the item from the bag when it goes into a
  slot, so equipment in a slot simply is not in the inventory the SELL tab
  reads. The test asserts this rather than trusting it.
- Quantity: `←/→` ±1, `shift` ±10, clamped to `[1, min(99, affordable/owned)]`.
- Every mutation goes through GS (`spendGold`+`addItem`, `removeItem`+`addGold`)
  and the panel re-renders from `GS.on('change')`.
- `Esc`/`Q` closes. Nothing is modal-blocking except input (see §5).

## 3. Menu — information architecture

`Esc` anywhere in the overworld opens it. One frame, command column left,
**party always visible right** (FF idiom: you can read your stats while you
choose), breadcrumb title.

```
PAUSE ─────────────────────────────────────── 30 g ──
 ▸ PARTY        │ Vesper                     Lv 3
   EQUIP        │ HP  46/46                            
   ITEMS        │ XP  ████████░░░░  128/225            
   SAVE         │ atk 11 (+2)  def  8 (+2)  spd  8     
   LOAD         │ weapon Walking Staff                 
   NEW GAME     │ armor  Quilted Vest                  
─────────────────────────────────────────────────────
 ↑↓ move · E/Enter select · Esc/Q back
```

- **PARTY** — per *active* member (`GS.activeParty()`): name, level, HP/maxHP,
  an XP bar against `GS.xpToNext(level)`, and atk/def/spd from `GS.stats()`
  with the equipment contribution shown as `(+n)` (computed as
  `stats − baseStats`, so it is always truthful about what the gear is doing).
  Inactive members (Maren, pre-join) are not listed — `activeParty()` is the
  single source of who is in the party, so **when Maren joins, every screen
  here gains a second column with no code change** (§7).
- **EQUIP** — character → slot (`weapon`/`armor`, enumerated from the
  character's own `equip` object, not a hardcoded pair) → compatible items
  (`items.json` entries in the bag whose `slot` matches) plus `— remove —`.
  The highlighted row shows a live delta preview
  (`atk 11 → 14  +3` in green / red) before `E` commits via `GS.equip`.
- **ITEMS** — consumables in the bag → choose member → use. Heal is
  `min(maxHp, hp + effect.heal)`; a member already at full HP is dimmed and
  refuses ("Vesper is unhurt."). The item is consumed only on success.
- **SAVE / LOAD** — `GS.save()` / `GS.load()`, each behind a yes/no confirm,
  with a one-line result toast. **NEW GAME** — destructive, so the confirm
  defaults to *No*.

## 4. Key bindings (keyboard-only, couch-friendly, no mouse anywhere)

| action | keys | why |
|---|---|---|
| open shop | `E` at the counter | identical to every door in the game |
| open pause menu | **`Esc`** | free in play3d: its keydown handlers use `g 2 [ ] m z` and the scene-graph `e`. **`M` is already the dev settings menu** (char height / debug toggle) so `M` is *not* used, and Esc needs no conflict handling. |
| cursor | `↑↓` / `W S` | both, always — P1 arrows, P2 WASD, either seat can drive a menu |
| tab / quantity / sibling column | `←→` / `A D` (+`Shift` ×10) | |
| confirm | `E` or `Enter` | `E` is the game's interact key; Enter for muscle memory |
| cancel / back / close | `Esc` or `Q` | one step up the breadcrumb, then closes |

## 5. Pausing the overworld without touching play3d.html

`EBUI` takes the input lock when a panel opens, and it does it with plain DOM,
not by reaching into play3d:

1. a **capture-phase** `keydown`/`keyup`/`keypress` listener on `window`.
   Capture on `window` runs before play3d's bubble-phase listeners, so
   `stopImmediatePropagation()` there means play3d's `keys{}` map, its debug
   keys, and its scene-graph `E` handler never see a keystroke while a panel is
   up. The door behind the shopkeeper cannot fire while the shop is open.
2. `SIM.keys({})` on open, on close, and on every key while open — so a player
   who opens the menu mid-stride does not keep walking (their `keyup` is
   swallowed, so the map must be zeroed by us).

That is a complete pause with **zero coordinator dependency**, which is what
"no-ops harmlessly before hooks land" should mean. `EBUI.lock()` is refcounted
and additionally consults `window.UILOCK` if the coordinator grants the formal
hook in §6 — belt and braces, in the right order.

## 6. Hooks requested from "main" (both optional; nothing blocks on them)

1. **`SIM.pad(name)`** — 4 lines beside the other SIM test-surface entries.
   Returns `{name, center, min, max}` of the first mesh matching `name`.
   Removes the last coordinate table from shop.js and is generically useful
   (any module that wants "where is the authored pad for X").
2. **`window.UILOCK`** — a formal modal-input lock consulted in `phys()` and in
   the scene-graph keydown listener, so pausing is a stated contract rather than
   an event-capture trick.
3. **`GS.useItem(charId, itemId)`** — the one GS API gap. Applying
   `effect.heal` today means writing `ch.hp` inside `GS.state`, which the
   contract says systems must not do. Until granted, menu.js uses a clearly
   marked shim that mutates through a single function and emits `change`;
   `Menu.useItem` prefers `GS.useItem` the moment it exists.

Integration (exact tags + call sites) goes to "main" as a message; play3d.html
is not edited here.

## 7. Red-team answers (the two questions asked up front)

**"Chapter 3 adds six shops in a new town — is that only a shops.json edit?"**
Yes, given the interior ships the standard `walk_pad_counter` (the builders emit
it by template). A new shop entry supplies `name`, `sceneKey`, `keeper`,
`stock`; shop.js derives the scene match, the anchor, the prompt label, the
prices and both tabs from data. No table of shops, no per-scene branch, no
coordinates, no new keeper labels ("Talk to the " + keeper works for a
fishmonger as well as a chandler). Rates are per-file today and read through one
accessor that already falls back to `rates` — a future per-shop `rates` override
is a data field, not a code change. The only non-JSON prerequisite for a new
town is the same one the scene graph already has: build the interior and re-run
the generators.

**"When Maren joins, does the menu/equip flow just work?"**
Yes. Nothing in menu.js names a character or assumes a party size: PARTY renders
`GS.activeParty()`, EQUIP's character step is that same list, ITEMS' target step
is that same list, slots come from each character's own `equip` object, and stat
previews come from `GS.stats`/`GS.baseStats`. Maren joining is
`GS.state.party[…].active = true` (a story flag flipping) and she appears in all
three flows with her own growth row from `growth.json`. Party-of-N is the data
model already; the UI is a `map()` over it, and the layout is a CSS grid that
takes N columns. The one thing that does *not* scale silently is screen space:
past ~4 members the party pane paginates (`←→` between pages) — implemented as a
page window over the same list, not a second layout.

## 8. Test list — `tools/economy_test.mjs` (headless Node, exit 1 on failure)

Harness: `game_state.js` is loaded **unmodified** into a Node context with three
shims — `window` (→ globalThis), `fetch` (→ reads `public/<url>` off disk), and
`localStorage` (→ in-memory Map). So the tests exercise the shipped store, and
no refactor of the coordinator-owned file is needed. `ui_kit.js`, `shop.js` and
`menu.js` load in the same context (DOM-free at load time; `EBUI` no-ops without
a `document`). No `Math.random` anywhere in a tested path.

1. data sanity: every `shops.json` stock id exists in `items.json`; every
   `sceneKey` is a node in `scenegraph.json`; every equippable item has a
   `slot`; every consumable has an `effect`.
2. buy: gold decreases by exactly `price × qty`, item count increases by `qty`.
3. buy refuses when short: gold unchanged, inventory unchanged, `ok:false`,
   reason `gold` (and at qty > affordable).
4. sell: gold increases by `sellPrice × qty`, count decreases; selling more than
   owned refuses.
5. round-trip: buy 1 then sell 1 loses exactly `price − sellPrice` (i.e. the
   sellRate spread), and inventory returns to its start state.
6. equipped gear is not in `Shop.sellable()`; unequipping puts it back there.
7. equip: `stats.atk` rises by exactly the item's `statMods.atk` (and def/spd);
   swapping weapons returns the old one to the bag; `Menu.statPreview` predicts
   the delta the mutation then produces (preview ≡ reality).
8. unequip returns the item to inventory and removes the stat delta exactly.
9. consumable: heals `effect.heal`, **clamps at maxHp**, is consumed on success,
   refuses (and is *not* consumed) at full HP.
10. xp curve: `xpToNext` strictly monotonic over levels 1..20; `grantXp` at
    exactly `xpToNext(1)` reaches level 2 with 0 remainder; one short of it does
    not; a large grant multi-levels and lands on the arithmetically exact level
    and remainder; level-up sets HP to the new max.
11. save/load identity: `serialize()` → mutate → `load()` → `serialize()` equals
    the first blob byte-for-byte; `reset()` returns a fresh-game blob.
12. no-data safety: with the rules data absent, `GS.ok === false` and
    `Shop.openShop` / `Menu.open` return `false` instead of throwing.
