# EMBERBROOK — Mechanics Bible

This document is the design authority for every gameplay system in the game, the way
`docs/VOICES.md` is authority for dialogue. Chapter agents, engine agents, and content
agents: when your idea and this document disagree, this document wins. When this document
and `STORY.md` disagree on lore facts, `STORY.md` wins. The pacing philosophy of
VOICES.md Part Two (one loaded thing at a time, white space is load-bearing) applies to
mechanics exactly as it applies to dialogue.

Everything here was settled with the director. Do not relitigate the decisions; do
sharpen them. The job of this document is to let us say NO later, cheaply.

Ship order: **Phase 1 Treasure → Phase 2 Character Switching → Phase 3 Swarm Defense.**
Phase 1 is highest priority and is specced to buildable depth below.

---

## PART 0 — PRINCIPLES (the laws)

### 0.1 The lore budget binds mechanics

STORY.md's lore budget is binding on systems, not just prose: **one deep fictional
system — the flame institution and its appendages (moths, the Warden, the shifting
wood).** Every mechanic must be either:

- an appendage of the flame system (Lake's lantern, the swarm, moth behavior,
  keeping-fire rules), or
- **mundane** (rope, coins, smoked eel, a boat-hook, a crow with a letter).

No mana. No spells. No crafting system. No elemental anything. If a proposed mechanic
needs a second magic to work, the mechanic is wrong. (Mochi's senses are canon cat lore
— §3 of STORY.md — and inside budget. Vesper's sheet is paper. Tally's crows are birds.)

### 0.2 THE MISSABLE LAW (hard rule)

**The main storyline may NEVER depend on a missable item.**

- Story-needed items are handed over inside **mandatory cutscenes**. The player cannot
  fail to have them.
- Found, bought, or earned items unlock **OPTIONAL content only**, and every payoff
  scene **degrades gracefully when the item is absent** — either the scene has a
  with/without variant, or it simply does not fire, and nothing else notices.
- If a main-path beat needs a tool, **the scene supplies its own** (the flume run brings
  its own winches; a future main-path climb brings its own rigging — Creel's rope is
  never the answer to a mandatory question).
- **Secrets outnumber gates two-to-one.** For every place an item or the right character
  is *required*, there are two places where having them is merely *rewarded*. Item-gates
  and character-gates are mostly bonuses, rarely doors.
- Every optional gate **advertises its key diegetically**: Mochi sniffs at the gap
  whether or not you own the eel; the ledge gets a remark whether or not you own the
  rope. The world tells you what would help; it never punishes you silently.

Checklist for any new item or gate: (1) is anything on the main path behind it? →
redesign; (2) does its payoff scene have a written absent-variant or a clean no-fire? →
required; (3) does the 2:1 secrets-to-gates ratio still hold for the chapter? (4) is the
key advertised in fiction?

### 0.3 THE PACING LAW

**One gameplay beat per scene.** A scene may introduce a chest, OR a shop, OR a verb
moment — not all three. Mechanics are **content built from existing verbs, not new
systems**: the Dellhollow locks and winches are switch-puzzles made of `bothHold` and
interacts, not a water-routing simulation. Before proposing a new system, prove the beat
cannot be built from: walk, interact, hold-together, give, place, light.

Rule D2 (rest lines) has a mechanics mirror: **most interacts in a scene must be plain
flavor** — examine text, a bench, a frog. If every interactable pays out, none of them
feel found.

### 0.4 Taste rules (no slop)

- **THE TV IS EVERYTHING.** All state a player can see lives on the shared screen;
  per-player UI is a per-player panel on that screen, standard couch co-op. The pad —
  a phone today, standing in for a real controller — is sticks and buttons, nothing
  more: no private screen, no touch surface, nothing rendered on it. The TV still never
  draws UI over the world except where specced below (pack panels while open, the penny
  tally near stalls, the wick meter in swarm setpieces, and nothing else). Counts live
  in dialogue first.
- **Everything has a home.** Every item either lives in a pack, on the boat, or with a
  person who wanted it. If a proposed item has no boat mount and no recipient, it does
  not get made. No junk, no vendor trash, no "materials."
- **Upgrades buy VERBS, not stats.** A rope opens climbable ledges. A striker lights
  road lamps. Nothing ever grants +N anything. No tiers, no trees, no upgrade menus, no
  cooldowns.
- **Nothing dies.** The game's only combat (Phase 3) ends in being walked back, never in
  death — of the party or of the moths. Moths are stray feeling; they are driven or,
  late in the game, called home.
- **The economy stays tiny.** Money appears first in Dellhollow (Emberbrook's festival
  runs on gifts, by LAW). Prices are single digits. Money never solves a story problem,
  and its number stays off the screen except in an open pack panel or within a stall's
  earshot (§1.2).
- **Rewarded, rarely required.** Switching characters and holding items is mostly a way
  to get *more* out of a scene, not the way through it.

### 0.5 The pad (canonical input mapping)

The game is designed for a standard PlayStation/Xbox-class controller. The phone
controller mirrors this layout in software — same buttons, same names — and is only a
stand-in for the real thing. One mapping, defined here, for the whole game; every
system below references this table rather than inventing inputs:

| control | binding |
|---|---|
| **left stick** | move; browse inside panels and menus |
| **A** (PS ✕) | the world: interact, advance dialogue, confirm — always contextual, always prompted |
| **B** (PS ◯) | the pocket: tap opens/closes your pack panel (§1.2); back, inside menus |
| **X** (PS ▢) | the verb, where a contextual A doesn't cover it (today: Vesper's sheet, §2.3; candidate for the swarm hood, §5) |
| **Y** (PS △) | switch character (Phase 2, §2.1) |

Everything else on a real pad stays unbound until a system earns it, with director
sign-off. Chapters 1–2 use stick + A alone; that restraint is a feature.

---

## PART 1 — TREASURE (Phase 1, highest priority)

Motivation without any battle system, on three pillars:

1. **THE BOAT IS THE HOUSE.** Items become visible decor and furnishings on the party's
   boat (gained end of Ch. 2). The boat is the museum-of-the-journey, on screen in every
   river scene. Picking something up means someday seeing it on your deck.
2. **Upgrades buy verbs, not stats** (§0.4). Restrained: a handful of items across the
   whole game open new reachable places or new interactions. That's the ceiling.
3. **THE RIGHT THING FOR THE RIGHT PERSON.** Gifts unlock scenes; NPCs want specific
   items; one trade chain spans chapters. The best use of a thing is almost always
   giving it away.

Couch detail that shapes everything below: **each player has a pack, and both packs
live on the TV** — a compact per-player panel (§1.2), either or both open at once.
Inventories are open books; who *carries* what is the couch conversation (logistics is
characterization). Handovers happen on the stage, between two characters standing
close.

### 1.1 Item data model

Item **definitions** are static content (proposed home: `public/js/items.js`, loaded
before chapter files). Item **state** is display-authoritative and lives in one runtime
object, serialized with the future save system.

```js
// ---- static definition ----
ITEMS = {
  'boat-hook': {
    name: "A River-Pilot's Boat-hook",
    desc: 'Ash shaft, bronze head, initials burned near the grip. Kept dry a long time.',
    cls: 'find',              // 'story' | 'find' | 'consumable' | 'coin'
    icon: 'assets/items/boat-hook-icon.png',   // pack-panel list
    sprite: 'assets/items/boat-hook.png',      // world/boat rendering, may be null
    boat: { mount: 'stern' },  // default decor home; null = never decor (consumables, coins)
    tags: { giftFor: 'maren' },// optional: WANTS advertising, verb keys, refills, etc.
  },
};

// ---- runtime state (display-authoritative; the pack panels are views) ----
Inventory = {
  owned: {},  // id → { owner: 'vesper'|'lake'|'boat', n: 1, mount: null|'stern', got: 'ch2' }
  grant(id, role),        // cutscene/chest/pickup entry point; toasts per §1.2 rules
  transfer(id, role),     // player→player handover (validated: proximity, same scene)
  give(id, npcKey),       // player→NPC; removes from owned, sets a flag payoff owns
  place(id, mount) / unplace(id),   // pack ↔ boat decor
  spend(id, n),           // consumables
  count(id), carriedBy(role), has(id),
}
```

Classes:

| class | rules |
|---|---|
| `story` | Given only inside mandatory cutscenes. Cannot be sold, dropped, or gifted to NPCs (handover between players allowed unless the scene fixed its owner). |
| `find` | Optional. Chest/pickup/shop/errand. Giftable, placeable. Fuels optional scenes only (§0.2). |
| `consumable` | Stacks (`n`). Phase 3 fuel: wick-oil, bright-powder. Small caps (wick-oil 2, bright-powder 1). |
| `coin` | "Pennies." A per-player stack, shown only as a small count — in your open pack panel, and as a corner tally near stalls (§1.2). Never itemized. |

There is **no drop verb**. Items leave a pack only by gifting (player or NPC), placing
on the boat, or spending. Nothing is ever lost on the floor — everything has a home.

### 1.2 Pack UX on the TV

Packs render on the shared screen, per §0.4. The pad contributes exactly the buttons
in §0.5 — nothing renders pad-side, and `controller.html` changes only by growing the
software B (later X, Y) to mirror the canonical layout.

- **The pack panel.** Tap B: a compact panel slides in on **your side of the TV** (P1
  left, P2 right) — item list (icon, name, one-line desc), pennies as a small count at
  the bottom. House style: the same rounded brass-and-parchment card as the checkpoint
  menu. Both panels may be open at once. The game does not pause; your character simply
  stands. Stick moves the highlight, A acts, B closes.
- **Claiming.** Ground pickups and chest contents go to **the pack of whoever pressed
  A**. Who walks over and presses is couch negotiation, on purpose. Cutscene-given
  `story` items go to the owner the scene names.
- **Handover (player → player).** Physical-feeling, proximity-gated:
  1. The two characters stand within arm's reach (same scene, distance < ~70 px);
     inside that range, pack items grow a "Hand to Lake" action.
  2. Giver opens pack, highlights the item, A → "Hand to Lake" → A.
  3. The TV shows a small sparkle at the two characters and one toast; both pads give
     a short rumble (rumble is a pad feature phones happen to share).
  There is no accept/decline flow: both packs are open books and the receiver is on
  the couch — consent is verbal. *(Design note: gift-hiding between players died with
  the private screens. Small loss; surprising the other player belongs to scenes now,
  not menus — and what survives of "who carries what" is the logistics conversation,
  which was the good part anyway.)*
- **Visibility.** One rule: **pickups and chests announce on the TV** — a toast names
  the item, and it lands in the presser's pack (or on the shelf), full stop. No quiet
  finds, no hidden identities; anything carried is one B-press from anyone's eyes.
- **Money on screen.** The penny count lives in the open pack panel; within a stall's
  earshot it also shows as a tiny corner tally per player, so buying never requires
  the panel. Everywhere else, no number on screen — prices and counts live in dialogue
  ("Two pennies, and I'll want the jar back").
- **Giving to NPCs happens in the world, not the pack.** Stand near an NPC who wants a
  carried item and the A-prompt becomes "A — give Maren the boat-hook." The pack is for
  *between players*; the A button is for *with the world*. (This keeps the stage the
  place where every gift scene happens.)
- **Keyboard override parity:** B maps to `Tab` (Vesper) / `` ` `` (Lake) or similar.
  Same panels — they were already on the display, so keyboard mode is the same UI, not
  an ugly cousin.

### 1.3 Interact patterns (engine vocabulary)

All in the existing `nearestThing` / `interact` / `promptFor` shape. Four new interact
kinds, one new UI primitive.

```js
// -- chest: one-shot container, public event --
if (!F.cacheOpen) consider(1130, 470, { kind: 'chest', id: 'order-cache', at: [1130, 430] }, 75);

if (t.kind === 'chest' && t.id === 'order-cache') {
  F.cacheOpen = true;
  return Cutscene.play([
    { say: ['system', '(A lidded stone box, cut with the Order’s twin sigils. The hinge fights, then gives.)'] },
    { run: () => { Inventory.grant('striker', p.role); Inventory.grant('wick-oil', p.role); } },
    { say: ['lake', 'A lamplighter’s striker. And oil. Somebody stocked this road to be walked.'] },
  ]);
}

// -- pickup: small find, announced like everything else --
if (!F.collarFound) consider(210, 480, { kind: 'pickup', id: 'biscuit-collar' }, 70);
// interact: one system flavor line; Inventory.grant toasts the item name (§1.2).

// -- shop: Dialog + the new `choice` primitive --
if (t.kind === 'eelstall') return this.shopEel(p);
// shopEel: stall patter (Dialog), then:
//   { choice: { prompt: 'Smoked eel — 2 pennies', options: [
//       { label: 'Buy',  run: () => { Inventory.spend('penny', 2, p.role); Inventory.grant('smoked-eel', p.role); } },
//       { label: 'Not today', run: null } ] } }

// -- gift: NPC wants-table, world-side giving --
WANTS = { maren: 'boat-hook', creel: 'sorrel-loaf', /* per chapter */ };
// nearestThing already returns { kind:'npc', key }; interact checks
// WANTS[key] && Inventory.carriedBy(p.role).includes(WANTS[key]) → play the gift scene,
// Inventory.give(id, key), set the payoff flag. Otherwise normal talk.
```

**The `choice` primitive** is Phase 1's only new engine UI: a Dialog step offering two
(max three) labeled options, chosen with stick + A. It is deliberately tiny — no shop
screens, no haggling, no quantity pickers. A market stall is a conversation with one
question in it.

Prompts follow house style: `'A — open the cache'`, `'A — give Maren the boat-hook'` —
drawn on the TV beside the character they belong to. The pad displays nothing (§0.4).

### 1.4 The boat shelf (rendering concept)

The boat (design canon in `docs/chapter2-dellhollow-script.md` §b) is a prop entity
present in river scenes and at moorings from Ch. 2's ending onward. It carries a set of
named **mounts** — anchor points where placed items render as sprites over the boat art:

```js
BOAT_MOUNTS = {
  prow:       { dx: -95, dy: -40 },   // the lantern hook (canon: painted into the design)
  mast:       { dx:   0, dy: -70 },
  rail:       { dx:  40, dy: -30 },
  lockerTop:  { dx: -55, dy: -25 },   // the bow locker Odessa filled
  stern:      { dx:  90, dy: -20 },
  tillerPocket:{ dx: 75, dy: -35 },   // charts live here
  cabinDoor:  { dx:  20, dy: -50 },   // a hook
  deck:       { dx: -20, dy: -10 },   // loose cargo (the pumpkin)
};
```

- Rendering: wherever the boat prop draws, iterate `Inventory.owned` for
  `owner === 'boat'`, draw `ITEMS[id].sprite` at prop position + mount offset, sorted
  into the boat's draw pass. **This is the whole system.** No boat interior UI, no
  furniture grid.
- Placing: stand on the deck (or beside the moored boat), A near a mount →
  `'A — tie the ribbon here'` / `'A — set the pumpkin down'`. Placement is walking to a
  spot and pressing the button — a physical act on the stage, both players watching.
  Re-placing is always allowed.
- One mount holds one item. The deck-only mount budget (~8) is the decor cap, which is
  the point: a small boat fills up like a small house, and every object on it is a
  chapter of the trip. Mochi's prow claim and (if found) Biscuit are *positions*, not
  mounts — animals are not decor.
- **The ribbon is the tutorial.** End of Ch. 2 / start of Ch. 3, the festival ribbon is
  the first placement: the player chooses where it ties. The scene should offer the
  choice and then never mention it again — the ribbon flying from wherever *you* tied it
  for eight chapters is the pillar-one promise, kept silently.

### 1.5 The Seed Ten (Ch. 1–2 content, classifications final)

| # | item | cls | owner | acquired (mandatory scenes in bold) | payoff schedule | boat home |
|---|---|---|---|---|---|---|
| 1 | Poppy's honeybun tin | story | Vesper | **Ch. 1 departure cutscene** | refills each town (Sorrel Ch. 2, Tally's kitchen Ch. 3…); Ch. 3 supper beat; standing rest-line texture (the dishonest count) | lockerTop |
| 2 | Pip's map to the MOON | story | Vesper | **Ch. 1 gate departure** | carried quietly; **in Vesper's hands at the Ch. 5 reveal** — the child's impossible map held up against the town that fell off every real one | tillerPocket |
| 3 | Grandmother's hand-lamp | story | Lake | **Ch. 1 leaving-home cutscene** (Lake takes it) | the party's interim second small light (dark stretches; later the router's dim glow in swarm setpieces); **THE lamp lit at Ch. 5 Ashfield**, at the cold pedestal | cabinDoor |
| 4 | Hobb's pumpkin | story | Lake | **Ch. 2 jam-resolution cutscene** (one pumpkin of forty tons; Vesper declines to carry it) | deck decor immediately; Ch. 3 supper flavor (pumpkin in the pot) | deck |
| 5 | The festival ribbon | story | boat | **Ch. 1 departure** | first decor choice — player ties it anywhere on the boat (§1.4); recognized in later towns (Tally names the pattern Ch. 3; a Harrowdel villager knows festival bunting Ch. 4) | player's choice |
| 6 | Biscuit's collar | find | finder | descent bramble, Ch. 2 (small pickup off the switchbacks) | the Ch. 1 notice-board LOST dog becomes findable Ch. 3/4 — show the collar, he comes, **joins the boat** | (worn by Biscuit) |
| 7 | Order cache: lamplighter's striker + wick-oil | find | opener | chest off the descent road, Ch. 2 | striker lights optional mundane road lamps Ch. 3+ (cosmetic warmth + swarm decoys, §3.4); bonus Tally identification scene Ch. 3 ("Volume Nine is CLEAR about strikers—"); wick-oil banks for Phase 3 | striker: rail |
| 8 | Smoked eel | find | buyer | eel-stall purchase, Ch. 2 (2 pennies; the first shop) | **the first item-gated interact:** coax Mochi through a gap to a cache (a few pennies + one trinket). Teaches the give-verb and the 2:1 spirit — pure bonus | — (eaten) |
| 9 | The father's boat-hook | find | finder | Lock Five chains, Ch. 2 (interact after the winch beat) | optional gift to Maren → quiet scene (her father's initials; no aphorism, one held breath); **Ch. 10 Reach scene has with/without variants** | stern (until gifted) |
| 10 | Creel's rope | find | earner | small errand, Ch. 2: buy a Sorrel loaf (1 penny), carry it to Creel; he pays in rope | Maren's climb/tie-off verb key (Phase 2): opens optional ledges and caches ONLY — a future main-path climb supplies its own rigging (§0.2) | stern coil |

**Graceful-degradation notes (the absent-variants, written now so they exist):**

- **Collar absent:** the dog appears once on a far bank (Ch. 4, one system line, keeps
  his distance, gone). No second chance this run; Biscuit is a secret, not a gate. With
  collar but scene missed: he re-appears at the next mooring — moorings are cheap.
- **Cache absent:** the Tally identification scene never fires; road lamps stay dark
  (cosmetic; a small honest disadvantage in one swarm setpiece, never a wall). Nothing
  remarks on the absence.
- **Eel absent:** Mochi still sniffs at the gap every time (the advertisement); the
  cache stays unreached; zero downstream effect.
- **Boat-hook found but hoarded:** it sits on the stern where Maren sees it daily; after
  one chapter she asks about it herself (the graceful second chance — a smaller scene
  than the gift, still warm). Never found: Ch. 10 plays variant B; variant B must be
  written as *complete*, not as variant A with a hole in it.
- **Rope absent:** ledge/cache interacts still exist and still advertise ("Maren eyes
  the ledge. 'With a rope, maybe.'"); they simply never open. No main-path contact by
  law.

**Economy in Ch. 1–2, exactly:** Ch. 1 has no money — Emberwake runs on gifts, by LAW.
Ch. 2 opens the first stalls: Vesper starts with a mapmaker's small purse (~6 pennies —
travelers carry money; Lake has none and finds this normal). Sinks: eel (2), loaf (1),
chestnuts (1, pure flavor). Sources: one or two penny-scale errands on the quay. Total
money in circulation in Ch. 2: under a dozen pennies. It stays this size for several
chapters; scarcity is what makes a two-penny eel a decision.

### 1.6 The trade chain (chapter-spanning, all-optional)

One chain, seeded in Ch. 2, resolving around Ch. 8. Every link obeys the Missable Law:
each hand-off yields its own small scene (self-contained payoff), and a broken chain
simply stops — no link references a future one until it happens.

Proposed links (director sign-off wanted on the far end, see §5):

1. **Ch. 2, Dellhollow:** Hobb, drowning in forty tons of pumpkins, presses a bag of
   **pumpkin seeds** on anyone who'll listen ("Plant them somewhere my wife will never
   hear of it").
2. **Ch. 3, Lanternstead:** Tally has a waystation garden plot and DOCTRINE about
   gardens. Seeds → he insists on repaying: an **Order signal-mirror**, polished,
   liturgically named.
3. **Ch. 4, Harrowdel:** the failing keeper's household needs the mirror (a keeper's
   tool they lost years ago) → repaid with a **jar of Harrowdel honey**.
4. **Ch. 8, the Gatehouse:** the honey is the first thing in three hundred years anyone
   has *brought* the Warden. He accepts it. He says almost nothing. It is on his table
   in Ch. 9. (The chain's whole destination is one image; that is the right size.)

### 1.7 Phase 1 in Ch. 1 (retrofit scope)

Ch. 1 is shipped and stays fixed in structure. Phase 1 touches it only by: adding
`Inventory.grant` calls inside the existing departure cutscenes (tin, map, hand-lamp,
ribbon), and nothing else. No shops, no chests, no pickups in Emberbrook — the festival
is gifts by LAW, and the Hush is not a shopping trip.

---

## PART 2 — CHARACTER SWITCHING (Phase 2)

Two players, growing party. The couch rule: **your character is yours.** The other
player can never take or puppet the character you claimed; unplayed members follow in a
trail. One **world verb** per character — no menus, no cooldowns, no upgrades, ever.

### 2.1 Claiming and cycling

- `player.char` decouples from `player.role` (the hook already exists in `makePlayer`).
  The role is the seat (P1/P2); the char is who you're being.
- **Join screen** becomes roster-driven, on the TV: the display draws the party as a
  row of cards, claimed ones dimmed (extending the existing join-panel/`taken`
  pattern); each pad claims with stick + A on the shared screen — standard couch
  character select. Nothing renders pad-side.
- **In play:** tap **Y** (§0.5) to cycle your control through members **not claimed by
  the other pad**. Swap is disabled during cutscenes, holds, and swarm setpieces. The
  display advances `p.char`, plays a small dust-puff at both characters, and updates
  the name tags and panel headers. No teleporting: you take over the member **where
  they stand** in the trail, and your former character drops into the trail where
  *they* stand.
- Chapters 1–2 stay two-character (Vesper + Lake, current architecture untouched).
  Switching turns on with Ch. 3 content. Mochi is claimable wherever he follows;
  Maren from Ch. 3; Tally after he joins.

### 2.2 Followers

The follower job (`updateFollowers` — Ch. 2 single-job, Ch. 3 three-job versions exist)
generalizes to a **trail**: unclaimed members chain-follow (member *i* targets member
*i−1*; the head targets the nearer player), reusing the existing offsets / near / far /
snap / walkability logic verbatim. Requirements carried over: park/hide during
cutscenes, snap-teleport when left behind, scene transitions and ferries carry the
trail (main.js already ferries followers). New requirement: the trail must survive a
mid-walk swap without a visible pop (swap exchanges targets, not positions).

### 2.3 The verbs (one per character, complete list)

| character | verb | in play |
|---|---|---|
| **Lake** | **the light** — aim, brighten, hood the lantern | dark-alcove interacts (`needs:'lake'`) reveal what's in them when he stands close unhooded; hooding matters in Phase 3; his light is the only one that wards |
| **Vesper** | **the sheet** — raises and corrects the map | **tap X (§0.5) raises the sheet over the stage** — a survey overlay on the TV (routes, her annotations, dream-drawing overlays); X again lowers it. Asymmetric ABILITY, not information: everyone reads it, but only Vesper can raise it, pin it, or amend it. Survey interacts (`needs:'vesper'`) at waystones, charts, sightlines |
| **Maren** | **water + reach** — swim, climb, tie off | water exits only she can take; ledge interacts openable with the rope (§1.5 #10); tie-offs that let the others follow her up |
| **Tally** | **books + crows** — read Order script, send a crow, recite rites | script interacts (Order carvings the others can't read); a crow can carry a small message ahead (optional errands, hints — the letters-from-home thread's warm mirror); rites open rite-locked Order fittings |
| **MOCHI (playable)** | **small + sensed** — gaps, ledges, senses first | gap exits only he fits (one optional Mochi-only nook per town, Ch. 3+); near hidden things he noses the air on the stage — a small sniff tell before anyone sees why (his pad hums along; rumble is a pad feature, not a screen). He speaks only "Mrrp."; his pack-panel header reads accordingly |

Verb design rules: a verb is a **world interaction**, resolved by *being the right
character in the right place* — never a projectile, never a resource, never a stat. The
`needs:` field on considered things gates them; the denied prompt always advertises
("Maren could swim that." / "Order script. Tally would know."). Per the Missable Law,
**verb-gates follow the 2:1 rule too**: two rewarded uses for every required one, and
required ones only in optional content until a chapter is *designed* for switching
(Ch. 3+ — and even then, main-path verb moments must be resolvable by walking the
needed character over, never by having prepared an item).

Vesper's sheet is the one verb with engine surface beyond interacts: a TV overlay in
the house card style, display-side state, no protocol. Keep it dumb: an image and pins.
The gameplay is her *choosing* — when the map comes up, what gets marked — and the
table talk it starts, now pointed at the same screen.

### 2.4 The Ch. 1–3 retrofit list

Existing `bothHold` moments are retroactively canon as **proto right-character
moments** — the game has been teaching "the right hands on the right thing" since the
gate. Retrofit is *labeling and light content*, not re-engineering:

| where | current | retrofit |
|---|---|---|
| Ch. 1 — the pact, twin sigils (`bothHold`, "swear it together") | ships as-is | none. This is the thesis statement; leave it alone |
| Ch. 2 — left winch + widow-winch (`bothHold` ×2) | ships as-is | prompt copy only, naming the hands ("HOLD A — Maren's side, together"). No mechanical change; Ch. 2 stays two-character |
| Ch. 3 — the well bucket (`bothHold`) | ships as-is | becomes the first true right-character hold when Phase 2 lands: anyone hauls, but the scene seats Maren on the crank with a line |
| Ch. 3 — great-lantern, wick and winch (`bothHold`) | ships as-is | right-character: **Lake must be at the wick** (only a keeper's fire), anyone at the winch. Enforced by staging, not failure — the scene walks Lake there |
| Ch. 3 — one Mochi-only nook | none | add one gap in the Lanternstead (the waystation has three hundred years of mouseholes); cache behind it, trinket-grade |
| Ch. 3 — striker identification | none (item exists Ch. 2) | Tally-verb showcase if striker carried: he identifies it, cites the volume, ends plain (VOICES rule 2) |

Ch. 3+ chapters are *designed* for switching; Ch. 1–2 are never redesigned for it.

---

## PART 3 — SWARM DEFENSE (Phase 3 — the game's only combat)

Night roads: **moths seek the walking flame.** One player is the flame; the other is
the way. It is the Flamebearer/Waykeeper creed made into a control scheme, which is why
it needs no tutorial text — the game has been saying "the map does not know fire; the
flame does not know the way" since Chapter One.

**NO turn-based combat.** Explicitly cut. Do not propose it. No HP, no damage, no
deaths, no XP from any of this.

### 3.1 The loop — inputs and states

- **Lake's pad (the flame):** stick aims the lantern beam (a cone on the TV). The
  lantern has three states — **hooded / carry / bright**. Tap A toggles carry↔bright.
  Hold A hoods while held (you are physically holding the shutter closed; release and
  it opens to carry). Pure stick + A, already inside the §0.5 layout. *(Hold-A vs.
  hold-X for the hood is flagged for couch playtest — §5.)*
- **The other pad (the way):** routes the party — ordinary movement, reading the
  road: which lamps are lit, where the dark chokes are, when to run and when to stand
  hooded and let a wave pass. Their only light is the hand-lamp (Seed #3): dim, below
  the moths' notice threshold, just enough to see your feet.
- **Brightness is ammo.** The wick meter (the one TV meter allowed, drawn small, brass,
  diegetic — the lantern's own oil window) drains: bright fast, carry slow, hooded not
  at all. **Bright drives waves back — and attracts the next wave from farther out**
  (bigger, sooner). Carry holds moths at bay in the cone only. **Hooded = invisible but
  blind**: moths lose the target and drift to any other light; the TV goes near-dark
  except the hand-lamp's pool.
- **Fail-forward.** Wick empty, or the swarm-press closes (moths touching the lantern
  fill a short grace timer): wings fill the screen, Lake hoods by reflex, and the party
  is **walked back** to the last lit waypoint. One narrate line, retry from there.
  Nothing dies, nothing is lost, no consumables are refunded or drained by failing.

### 3.2 Wave grammar (the authoring vocabulary)

A setpiece is a scripted sequence of waves over a road of scenes. Authors get exactly
these knobs:

- **Wave:** `{ size, bearing(s), trigger (distance | time | brightness-noise), pattern }`
  where pattern ∈ **drift** (straight seek), **spiral** (orbit in, harder to face),
  **feint** (splits around the cone), **split** (two bearings at once — forces
  hood-and-walk or a flare).
- **Road furniture:** lit lamps (safe islands — moths shun warded light; standing in a
  lamp's pool is rest), dark stretches, chokes, **decoy lamps** (mundane lamps the
  striker can light — unwarded, so moths *pool on them* instead of you; the striker's
  reward, never required), waypoints (retry anchors).
- **Escalation is grammar, not numbers:** later setpieces add patterns and subtract
  furniture. Never tune by inflating counts alone.

### 3.3 Consumables (the whole list)

- **Wick-oil** — refills the wick. Carry cap 2. Found (the Order cache), bought
  (occasionally, cheap), never farmable.
- **Bright-powder** — one emergency flare: drives every moth on screen, instantly.
  Carry cap 1. The next wave still comes, bigger. It is a held breath, not a strategy.

Setpieces must be **winnable with zero consumables** (Missable Law applied to combat).

### 3.4 The setpieces (3–4 across the arc, escalating; scarcity keeps it an event)

| # | chapter | the event | grammar |
|---|---|---|---|
| 1 | **Ch. 3 — Lanternstead** | the night's first swarm comes for the lighter (canon beat; currently cutscene — becomes the playable tutorial) | one wave, one bearing, drift only; the great-lantern's light is the finish line; generous wick |
| 2 | **Ch. 5 — the road into Ashfield** | the wood ate the road; the last miles to the ghost town are walked at dusk | two bearings, first spiral; dead Order lamps line the road — striker owners may light decoys; ends at the cold town where, terribly, no moths follow (nothing left to seek) |
| 3 | **Ch. 7 — the Mothway** | the storm-migration; the chapter's crisis and the mechanic's meaning revealed (moths are stray feeling) | the full grammar: feints, splits, furniture stripped; and then the turn — the final wave is not driven: Lake's newly meant flame **calls them home**, bright held open, wick spending, moths going *into* the light. The mechanic inverts in one scripted beat |
| 4 | **Ch. 9 — the approach to the clearing** | the gathering run: same sim, opposite goal — arrive with as much of the storm gathered behind the lantern as you can carry | inverted rules from setpiece 3; hooding now *loses* moths; the wick is the cost of calling. Optional excellence, never a fail-gate: the pour scene plays regardless, warmer for what you brought |

Between setpieces, night roads are safe or scripted. Four events in ten chapters is the
budget; a fifth needs director sign-off.

---

## PART 4 — IMPLEMENTATION ORDER (appendix for the engine agents)

Phase 1's actual engine slice, in build order:

1. **Inventory state.** `public/js/items.js`: `ITEMS` defs + `Inventory` runtime
   (display-authoritative — and display-rendered, so there is no pack state to sync
   anywhere). The only net addition is input: the `btn` message grows a button field
   (`{type:'btn', b:'a'|'b'|'x'|'y', down}`), and `controller.html` grows the software
   B to mirror §0.5. Serialization shape ready for the save/checkpoint system (it does
   not exist yet; don't build it here, just keep `Inventory.owned` JSON-clean).
2. **TV pack panels.** Per-player panel in the house card style: open/close on B,
   stick-browse, A-act; handover action, penny count, stall tally, grant toasts
   (§1.2). Keyboard parity keys.
3. **Interact kinds.** `chest` / `pickup` / `shop` / `gift` patterns (§1.3) + the
   `choice` Dialog primitive in `story.js` (the slice's only engine-UI addition).
4. **Boat scene hooks.** `BOAT_MOUNTS`, placed-item rendering pass on the boat prop,
   `mount` interacts on deck, the ribbon-tying choice scene.
5. **Content.** Seed Ten wiring: grants inside existing Ch. 1/Ch. 2 cutscenes; new
   optional interacts (bramble pickup, Order cache chest, eel-stall shop + Mochi gap,
   chains boat-hook, Sorrel-loaf errand); pennies; Ch. 3 supper/refill touches.

Phase 2 slice (later): TV roster/claim join screen, Y-swap + `p.char` decoupling,
follower trail generalization, `needs:` gating + denied-prompt advertising, Vesper's
sheet overlay (X), Mochi's stage tell. Phase 3 slice (last): moth entities
(seek/pattern AI — the particle moths are ambience, not this), lantern state on Lake,
wick meter, wave scripting table, waypoint retry — all of it stick + A already; the
pad constraint touches nothing here.

Each slice lands whole or not at all; a half-shipped pack (items with no handover, shops
with no choice UI) is worse than none.

---

## PART 5 — RESOLVED QUESTIONS (director delegated, decided 2026-07-24)

1. **Trade-chain endpoints: APPROVED as specced.** Seeds → mirror → honey → the
   Warden's table. The chain's whole point is that its last link lands on the
   loneliest table in the world; nothing else ends it better.
2. **Boat: deck-only.** ~8 mounts, no cabin painting. Revisit only if the boat
   gains interior scenes for story reasons; decor never drives art budget alone.
3. **Swarm hood: hold-A.** The hood is Lake's core action under pressure and
   belongs on the world button; hold-to-shutter is the physical read. Standing
   playtest note: if the couch test says otherwise, switch to hold-X — content
   is authored control-agnostic either way.
4. **Mochi's pack: one mouth slot.** No coins, one small item, dropped at the
   holder's feet on switch-away (cats do not do handover menus). The joke line
   renders when the slot is empty.
