# END-TO-END WIRING — Chapter One → the valley road → Chapter Two, as one game

**Status: AUDIT + PLAN. No production code was written for this document.** A parallel
lane was rewriting `chapter1.js`, `chapter2.js` and `dialogue.json` while this was
traced, so everything below reads STRUCTURE (scene flow, flags, transitions, save
state), never line-by-line dialogue.

**Scope ruling (user, 2026-08-02): Chapters One and Two ONLY.** Chapter Three is out of
scope for all work. Every reference to `chapter3.js` / Lanternstead found in the trace is
listed in §3.9 so the build lane knows exactly what to stub or gate — nothing more.

---

## 1. CONTEXT — what "one continuous game" actually requires

The user's ask: *"we have all of the elements ready to actually wire things up as a full
end-to-end game, including having the actual story unfold as the player plays."*

A continuous Ch1→Ch2 playthrough needs six things to be true at once:

1. A **new game** starts in Chapter One's opening ground, with no save and no chapter picker.
2. Chapter One's **beats fire in the shipped 3D town** (`emb-cine`), not in a parallel engine.
3. Chapter One's ending **opens the Old Gate** and hands the player to the corridor.
4. The **corridor** (`ow-valley`) is walked, not skipped, and lands at Dellhollow.
5. Chapter Two's beats fire in `del-cine`, and its ending **adds Maren to the party**.
6. **Save state** carries chapter, place, party, inventory and flags across all of it.

Today **exactly one of those six is true (#4).** The rest is the work.

---

## 2. AS IT IS TODAY

### 2.1 THE HEADLINE: there are two runtimes, and the story is in the wrong one

| | **the 3D runtime** | **the 2D chapter engine** |
|---|---|---|
| page | `public/play3d.html` (served at `/play.html`, `server.js:35`) | `public/join-legacy.html:71-80` — the ONLY page that loads it |
| world | pre-rendered plates, depth occlusion, scenegraph transitions | painted 1344×768 scenes + bitmap walk masks |
| has | GS, battles, shops, NPCs, dialogue nodes, menu, music, markers | Chapters 1/2/3, cutscenes, banners, objectives, checkpoints, **two players** |
| lacks | **any chapter, cutscene, objective, story-flag or second-player layer** | every town built in the last month |

`grep` for the chapter files across the whole tree returns `join-legacy.html:77-79` and
`tools/build-story.mjs` and nothing else. **`chapter1.js` / `chapter2.js` are not loaded by
the game the user plays.** They are the *script*, and the shipped 3D game is the *stage*;
nothing joins them. `docs/plans/ch1-staging-audit.md` (2026-08-01) is the beat-by-beat
audit of that gap and is the companion document to this one.

`public/index.html:38` still says so in the UI: *"Each scene is standalone (no exits/second
player/story yet — that's the engine-wiring step)."* That step is this plan.

### 2.2 How a player starts today

- `/` = `public/index.html`, the chapter-select hub. It renders `window.SCENE_REGISTRY`
  (`public/game/scenes.js:10`) as cards; each card is `play.html?scene=<key>&v=<ts>`
  (`index.html:50`).
- The lead card is **`ow-valley&rt=1`** — *"PLAY — the connected slice (start here)"*
  (`scenes.js:12`): spawn on the valley road at Emberbrook's gate.
- `/play.html` is `play3d.html` (`server.js:35`); `public/play.html` is a redirect shim.
- **A bare `/play.html` with no `?scene=` lands in `del-cine`** — Dellhollow
  (`play3d.html:29`).
- **There is no "new game" path, no title screen, no chapter/act concept in the runtime.**
  The only thing resembling one is the pause menu's NEW GAME (`menu.js:128`, `:535`),
  which calls `GS.reset()` and does not move the player anywhere.
- The 2D engine *does* have a title screen (`main.js:125-224`), a boot into Chapter One
  (`main.js:960-967`, `Field.enter('forest')`) and a scrollable checkpoint menu across all
  three chapters (`main.js:302-380`). None of it is reachable from the shipped game.

### 2.3 What happens at the end of Chapter One (and Two)

In the 2D engine, the chain is real and complete:

- Ch1's finale needs both keepers inside the opened arch (`chapter1.js:265-269`) →
  `playEnding()` (`:980`) → `F.ended = true` (`:1034`).
- `main.js` draws `END_CARDS[0]` (`main.js:795-799`, `drawEnd()` `:808`).
- The card advances on any key after 2.5 s (`main.js:431-432`), on an A-press
  (`:553`), or **by itself at 16 s** (`:608-609`) → `startChapter2()` (`main.js:22-31`):
  fade to black, `setChapter(Chapter2)`, `Chapter2.begin(players)`, fade back.
- `Chapter2.begin()` (`chapter2.js:261-274`) calls `resetFlags()` and teleports both
  players to `descent` at (140,150)/(200,130). **It is a hard cut, not a journey** — no
  road is walked between the towns, and `resetFlags()` wipes Ch1's state.
- Ch2 ends the same way: `playLanding()` → `F.ended = true` (`chapter2.js:1566`) →
  `END_CARDS[1]` → `startChapter3()` (`main.js:32-42`).

**In the 3D runtime none of this exists.** There is no end card, no chapter object, no
`ended` flag, and no handoff. A player who walks to Emberbrook's gate field (`gatefield`
shot) finds nothing there: `emb-cine` ships **no edge out of `gatefield`** (§2.7).

### 2.4 Save state — what GS persists, and what it does not

`public/js/game_state.js` is the whole store.

| fact | citation |
|---|---|
| key `emberbrook-save-v1`, version `v: 1` | `game_state.js:10`, `:42` |
| the entire state shape: `{ v, party[], gold, inventory{}, flags{} }` | `:42-43` |
| a party member is `{ id, active, level, xp, hp, equip{weapon,armor} }` | `:38-41` |
| `GS.init()` loads from localStorage, else `newGame()` | `:23-34` |
| **the only writer is the pause menu's SAVE** (`GS.save()`) | `menu.js:530` — one call site in the whole repo |
| LOAD replaces state in place; NEW GAME = `GS.reset()` | `menu.js:532-537`, `game_state.js:147` |
| GS survives a scene swap untouched — no save, no load, by design | `play3d.html:1456-1459` |

**What GS does NOT carry, and must:**

- **No scene.** No `chapter`, no scene key, no camera id, no position, no yaw. A load
  restores your gold and levels into whatever scene the URL happens to name.
- **No story flags of any consequence.** `dialogue.json`'s 111 nodes write **31 flags and
  every one of them is `npc.met.<id>`** — pure "have we spoken". Zero conditions are
  authored anywhere in the file: `check()` (`dialogue.js:161-186`) supports
  `flag/notFlag/flagIs/flagAtLeast/hasItem/goldAtLeast/all/any/not` and **nothing uses
  any of it yet.** The mechanism is built and idle.
- **No Lake.** `public/game/growth.json` has exactly two characters: `vesper`
  (`active:true`) and `maren` (`active:false`). **The second player character has no party
  record at all.**
- **`maren.joinFlag: "maren-joined"` is declared in `growth.json:33` and read by nothing**
  — grep across `public/`, `tools/`, `docs/` returns that one line. `menu.js:15` describes
  the intended behaviour ("Maren joining is `active` flipping in the save") but no code
  flips it.
- **No roles.** The 3D runtime is single-body: one `THREE.Group ch` (`play3d.html:111`),
  keyboard only, no `Net`, no `players` array, no controller socket. The phone relay in
  `server.js:160-200` talks to a "display", and the only page that registers as one is
  `join-legacy.html`. **Two-player co-op exists in the 2D engine and nowhere else.**

### 2.5 Story-flag inventory (Ch1 and Ch2, as the scripts hold them)

All of these live on the chapter object — `Chapter1.flags` / `Chapter2.flags` — in plain
memory. **None is in GS. None survives a reload. None is visible to the 3D runtime.**

**Chapter One** (`chapter1.js:13-21`), plus `Chapter1.phase ∈ {vesper, lake, together}` (`:14`):

| flag | set at | gates |
|---|---|---|
| `vesperIntro`, `waystone` | `:621`, `:632` | Act I triggers (`:185-188`) |
| `vesperTalked{poppy,mara,finn}` | `:468`, `:512`, `:501` | Rowan's first conversation (needs 2) `:440` |
| `vesperDone` | `:655` | phase flip to `lake` `:666` |
| `lakeIntro`, `lampsLit` (0→3) | `:679`, `:408` | the meet auto-fires at `lampsLit>=3` `:193` |
| `met` | `:701` | phase flip to `together` `:702` |
| **`hushDone`** | `:796` | **closes the south road** `:96` and **the pond lane** `:99` |
| `seen{poppy,finn,mara,mochi}` | `:556`,`:574`,`:587`,`:606` | Rowan's pact conversation (needs 4) `:548` |
| **`pactDone`** | `:873` | **opens the square→gate exit** `:102`; arms the sigil plates |
| **`gateOpen`** | `:255` | **the arch becomes walkable** (`archBlock` `:112`, `fieldWalkableAt` `main.js:623-627`) |
| `endingStarted` | `:985` | closes gate→square `:117` |
| **`ended`**, `endT` | `:1034`, `:270` | the end card and the Ch2 handoff (`main.js:431`, `:553`, `:608`) |

**There is no "Chapter One complete" flag and no "sigil gate is open" flag outside this
in-memory object.** The two that matter to the parallel old-gate lane are `gateOpen`
(chapter1.js:255) and `ended` (chapter1.js:1034). **Neither is durable, neither is
namespaced, and neither is readable from `play3d.html`.** §5 proposes the minimal
durable pair.

**Chapter Two** (`chapter2.js:31-40`, reset wholesale at `:213-225`):
`descentIntro, chartDone, strangerSeen, arrived, talked{}, jamDone, marenDone, lockSeen,
planMade, nightFallen, dockDone, boatDown, gateHalf, gatesOpen, flumeDone, marenJoined,
ended, endT, hobbTalk, pellTalk, supperCalled, supperDone, sorrelTalk, creelTalk, nibTalk`.

Ch2 flags that gate a transition: `strangerSeen` (descent→stairs, `:64`), `nightFallen`
(stairs→descent closes, `:95`), `marenDone` (dellhollow→lockfive, `:132`),
`supperCalled && !supperDone` (dellhollow→cottage, `:137`). **`marenJoined` is set at
`chapter2.js:1561` and is the semantic twin of `growth.json`'s orphan `maren-joined`.**

### 2.6 The overworld corridor — REAL, and the one thing that already works

`ow-valley` is a genuine traversable real-time scene, not a map screen.

- `public/world/regions/valley.region.json` `road` is a 20-point spine
  (`road.points[0]=[80.01,22.75,28]` … `[184.88,136.19,12.01]`) with 4 portals:
  `whisperwood-entrance` (**target null**), `emberbrook-gate` → emberbrook,
  **`old-gate` (target null)**, `dellhollow-valley-gate` → dellhollow.
- The road's own `_doc` states the fiction: *whisperwood → Emberbrook → **the Old Gate at
  the village's north shoulder** → across the culverted court to the east bank → down the
  gorge's east wall → Dellhollow's Valley Gate. It crosses exactly once, at the gate.*
- `public/world/scenegraph.json` gives `ow-valley` exactly 2 edges, both portal pairs:
  `ow-valley ↔ emb-cine @emberbrook-gate` (lands on cam `woodroad`) and
  `ow-valley ↔ del-cine @dellhollow-valley-gate` (lands on cam `gate`).
- `ow-valley` ships `zones.json` (encounter geography, `play3d.html:915`), so the corridor
  is where battles live. `music.json` maps `ow-` → the `valley` track.

**So the corridor works — but by the wrong door.** Because `old-gate` has `target:null`,
the only Emberbrook↔valley portal is `emberbrook-gate`, which is the **south** arrival
road — the way Vesper *came in*. A player today leaves Emberbrook by the south arch,
walks north past the old gate (which has no portal), and continues to Dellhollow. **The
sealed gate that Chapter One exists to open is not on the route at all.**

### 2.7 The seams — what exists, what is missing

`public/world/scenegraph.json` (generated 2026-08-01, 86 edges, 13 nodes) is derived from
the maps by `tools/scenegraph_derive.mjs`; `play3d.html:1159-1620` is the consumer.

**Present and green** (`node tools/trigger_probe.mjs --static` → PASS, 2 assertions):

| seam | edges |
|---|---|
| `emb-cine` internal camera cuts | 22 (11 shots) |
| `del-cine` internal camera cuts | 40 (16 shots) |
| Emberbrook interiors | inn, bakery, lake's cottage, item shop — 4 pairs |
| Dellhollow interiors | inn, item, weapon, armor, cookhouse, keepers' cottage — 6 pairs |
| town ↔ corridor | `emberbrook-gate`, `dellhollow-valley-gate` — 2 pairs |

**Missing** (the `--static` audit names all three):

1. **`old-gate` / `sigil-gate-downstream` — declared twice, derived zero times.**
   `valley.region.json` `road.portals 'old-gate'` has `target: null`;
   `emberbrook.map.json` `exits 'sigil-gate-downstream'` has `sealed: true` and **no
   `sealedUntil`**. No edge exists, so no prompt and no marker *can* render.
2. `forest-north` at `forest-trailhead` → `overworld-forest`: declared, no edge (the
   region does not exist). Ch1 does not need it; leave declared.
3. `handofftest.map.json` `test-out`: a fixture, ignore.

**The generator is already ahead of the runtime.** `scenegraph_derive.mjs:703-783` reads
`sealed`, pairs a portal to an exit **by the id the portal names** (`:741-760`), warns
loudly on `target:null` (`:710-716`), and prints an explicit instruction for the sealed
case (`:767-781`): *"Opens on story flag '<sealedUntil>'; **the runtime needs a
conditional-edge gate** before this can ship as a live edge."* So RESUME Lane 1's derive
work has landed; what is missing is (a) two map lines and (b) the runtime gate.

---

## 3. THE GAPS, ordered by what blocks a playthrough first

**G1 — There is no story layer in the shipped runtime.** No chapter object, no cutscene
runner, no objective HUD, no banner, no end card, no scripted camera. `play3d.html` loads
11 modules (`:1625-1635`) and not one of them knows what a beat is. *Blocks everything.*

**G2 — Emberbrook has no cast in the playable scene.** All 11 Emberbrook NPC records
(`rowan, poppy, mara, pip, finn, mochi-emb, emb.miller/neighbour/townsfolk/girl/boy`) are
scened to **`emb-townwalk`**, the dev free-roam bundle — not `emb-cine`.
`npc.js:162-170,298` filters on the scene key alone, so **the playable Emberbrook is
empty of people.** Their coordinates are already in the shared frame (`rowan
[60.4,1.5,-42.4]` vs `emb-cine` square spawn `[65.35,1.5,-45.8]`), and both bundles carry
the same master collision (`emb-cine/meta.json`: *"SHARED collision for every cinematic
camera"*). *This is a one-line-per-record fix and the cheapest win in the plan.*

**G3 — The Old Gate is not a door.** §2.7 item 1. Ch1's climax and the Ch1→Ch2 corridor
entrance are the same unwired portal. *Blocks the handoff.*

**G4 — No durable story flags.** Everything the chapters gate on lives in RAM on an
object the runtime never loads. `dialogue.json` writes only `npc.met.*`. *Blocks
persistence, conditional edges, Maren, and any "have I done this" question.*

**G5 — Save state cannot resume a playthrough.** No chapter, no scene, no position
(§2.4). LOAD from the pause menu restores stats into whatever scene you were already in.
*Blocks a multi-session game.*

**G6 — Lake is not a character.** No `growth.json` record, no GLB in `play3d.html`'s
`MODELS` registry (`:61-63`), no party slot. He is a dialogue speaker and a cut-in and
nothing else. *Blocks the party, the twin-sigil beat, and Ch2's boat.*

**G7 — Two-player co-op does not exist in the 3D runtime.** One body, keyboard only, no
relay client. Both chapters' set pieces are built on two: Ch1's `bothHold` oath
(`chapter1.js:856`), the twin sigil plates (`:249-254`, both players required), the
phase system (`:24-26`), Ch2's twin winches. *Blocks the chapters' co-op beats — see the
user question in §7.*

**G8 — Maren never joins.** `growth.json:33` declares `joinFlag: "maren-joined"`; nothing
reads it; `chapter2.js:1564` sets a different, in-memory `marenJoined`. *Blocks the Ch2
payoff and the party the rest of the arc assumes.*

**G9 — The Emberbrook staging conflicts are unresolved.** `docs/plans/ch1-staging-audit.md`
raises 5 gaps, 4 conflicts and **7 story questions the user has not answered** (Q1 inn/shop
open on Emberwake; Q2 Lake's cottage vs the pond lane; **Q3 what is beyond the opened
gate** — the notch is stamped sealed to 0 m² of reachable gorge; Q4 where the gate refuses
you and where the send-off is; Q5 can Vesper meet Finn; Q6 the vestigial `stranger`; Q7
Poppy's stall). *Q3 and Q4 block Ch1's ending geometry.*

**G10 — No new-game entry point.** §2.2. *Cosmetic against G1, but it is the first thing
a player touches.*

### 3.9 Chapter Three references (for stubbing — do not build)

| where | what |
|---|---|
| `public/js/chapter3.js` | 979 lines, loaded only by `join-legacy.html:79` |
| `main.js:32-42` | `startChapter3()` |
| `main.js:433-434`, `:554`, `:610-611` | three call sites that advance Ch2's end card into Ch3 |
| `main.js:803-805` | `END_CARDS[2]` |
| `main.js:311` | `CheckpointMenu` adds `Chapter3` entries |
| `scenes.js:55-59` | `SCENE_ARCHIVE` group *"Chapter 3 — built, not yet vetted"* |
| `server.js:46` | `chapter3.js` in `STORY_SOURCES` (the story page rebuild trigger) |

**Recommendation:** leave the files on disk; make Chapter Two's end card terminal
(`next: null`) in whatever replaces `END_CARDS`; do not port any Ch3 beat.

---

## 4. THE PLAN

Reuse beats inventing. This codebase already owns every primitive the story layer needs;
the work is to *drive* them, not to duplicate them.

### Phase 0 — the cheap unblocks (no new systems; do these first)

**0a. Put the cast in the playable town.** Add `"emb-cine"` to the `scene` list of every
`emb-townwalk` record in `public/game/npcs.json` (11 records), exactly as the Dellhollow
records already carry `["townwalk","del-cine"]`. Verify with `tools/dialogue_test.mjs` and
a live walk. *Fixes G2.*

**0b. Give Lake a party record.** Add `lake` to `public/game/growth.json` `characters`
(`active: true`), with `startEquip`. Add his GLB to `MODELS` in `play3d.html` **via the
coordinator** (`play3d.html:61-63`) if/when a body exists. *Fixes half of G6.*

**0c. Wire the Old Gate.** Two map lines and one derive run:
- `valley.region.json` `road.portals 'old-gate'`: `"target": "emberbrook"`,
  `"exit": "sigil-gate-downstream"` (the derive pairs by name — `scenegraph_derive.mjs:741-760`).
- `emberbrook.map.json` `exits 'sigil-gate-downstream'`: add
  `"sealedUntil": "story.ch1.gate-open"` beside the existing `"sealed": true`.
- Re-run `node tools/scenegraph_derive.mjs`; the SEALED block should now print the pair
  with its flag instead of the UNPAIRED warning. Then `tools/trigger_probe.mjs --static`
  → zero unexplained rows. *Fixes G3's data half; the runtime half is 1b below.*

### Phase 1 — the story layer (`public/js/story_runtime.js`, a new self-arming module)

One module, added to `play3d.html`'s hook list **by the coordinator** after `dialogue.js`.
It self-arms at load and re-arms on `'eb-scene'`, exactly like every other module
(`play3d.html:1434-1459`).

**1a. `window.Story` — the chapter director.** Reads a **data file**, not code:
`public/game/story.json`, one entry per beat:

```
{ id, chapter, scene, cam, at:[x,y,z], r, when:{...cond}, once:true,
  do:[ {dialogue:"<node id>"} | {setFlags:{}} | {banner:{}} | {objective:"..."}
     | {shot:"<cam id>"} | {toast:{}} | {wait:0.8} | {endCard:1} ] }
```

- Conditions reuse **`Dialogue.check()` verbatim** (`dialogue.js:161-186`) — it already
  supports `flag/notFlag/flagIs/flagAtLeast/hasItem/goldAtLeast/all/any/not` and reads
  `GS.state.flags`. Do not write a second evaluator.
- Effects reuse **`Dialogue.effects()`'s vocabulary** (`dialogue.js:188-206`):
  `setFlags/incFlags/giveItem/gold`.
- Dialogue playback is **`Dialogue.play(nodeId)`** — the beat holds no lines of its own.
  All prose stays in `dialogue.json`, which is where `dialogue_test.mjs` polices it.
- **Proximity beats ride the physics tick**, beside the existing ones:
  `play3d.html:1028-1031` already calls `sgTick(); Shop.tick(); Npc.tick();
  Encounters.tick();` — `Story.tick()` goes **after `sgTick` and before `Encounters`** (a
  beat must lose to a transition and win over an ambush, the same precedence
  `Encounters` already documents).
- **UILOCK is the freeze**: a beat takes `EBUI.panel({name:'story'})` / `UILOCK.lock()`
  (`play3d.html:421-424`), which stops `phys()` and zeroes held keys — this is the
  existing modal contract and it is enough for a dialogue-driven cutscene.
- **Camera control is free**: `SIM.shot(id)` (`play3d.html:1568`) already fetches and
  applies any baked shot and returns a promise. A scripted camera move is `{shot:"..."}`,
  not a new system. The unused `cinematic: true` camera class (DAYLOG 2026-08-01, near
  line 6493) is available if a beat wants a plate no walk-route owns.
- **Objective / banner / end card** are DOM overlays in the style of `sgPrompt`
  (`play3d.html:1206-1220`) and the exit markers (`:1298-1323`). Port the *text* of
  `main.js:795-806` (`END_CARDS`) into `story.json`; leave `main.js` alone.

**1b. Conditional edges — the runtime gate the derive is waiting for.** In `sgTick()`
(`play3d.html:1245`), skip an edge whose `when` fails:

```
if (e.when && window.Dialogue && !Dialogue.check(e.when)) continue;
```

placed with the existing `camFrom` gate (`:1253`) so a sealed edge produces **no prompt
and no marker** — `markersTick` (`:1304`) needs the same guard, because seam canon's
sealed rule is *"the sealed presentation is the absence"* and a red arrow onto a shut gate
is a lie. The generator then emits the `sigil-gate-downstream` pair with
`when: {flag: "story.ch1.gate-open"}` derived from `sealedUntil`. **This is a
coordinator edit to `play3d.html`** — message main, do not edit it in-lane.

**1c. Chapter One, staged in `emb-cine`.** Author `story.json` beats against
`docs/plans/ch1-staging-audit.md`'s beat table, using the 11 baked shots
(`woodroad*entry, waystone, arch, orchard, therise, square, pondlane, homerow, northlane,
gateroad, gatefield`) and the four interiors. The audit's per-beat map homes are the
staging authority. **The gate finale sets `story.ch1.gate-open`**, which makes the
`sigil-gate-downstream` edge live and its marker appear.

**1d. The handoff.** Taking the now-live gate edge is an ordinary
`transitionTo()` → `sgSwap()` (`play3d.html:1488`, `:1468`) into `ow-valley` at the
old-gate portal point, on the `'eb-scene'` event. `Story` hears it, plays Ch1's end card
over the corridor's first frame, sets `story.ch1.done`, and sets Chapter Two's opening
objective. **No teleport across towns, no chapter reset** — the corridor is walked.
This is exactly what `chapter2.js:261-274` fakes today with a fade and a coordinate.

**1e. Chapter Two, staged in `del-cine`.** Same mechanism, 16 shots + 6 interiors.
The ending sets `story.ch2.done` **and `maren-joined`**.

**1f. Maren joins for real.** In `GS`, honour `growth.json`'s declared `joinFlag`
(`growth.json:33`): on `GS` 'change' (or a small `GS.syncJoins()` called by `Story`), a
character whose `joinFlag` is truthy in `state.flags` gets `active = true`. `menu.js:15`
already documents this as the intended behaviour. *Fixes G8, one small change in
`game_state.js`.*

### Phase 2 — save/resume and the new-game door

**2a.** Extend the save (§5), bump to `v: 2`, migrate `v: 1` forward.
**2b.** Auto-save on every `'eb-scene'` and after every beat with `once:true`.
**2c.** `index.html` gets a real **NEW GAME / CONTINUE** pair above the scene cards:
NEW GAME = `GS.reset()` then `play.html?scene=emb-cine&cam=woodroad&new=1`;
CONTINUE = read `state.at` from the save and build the URL from it. Keep every existing
card as the developer jump list, and update the stale note at `index.html:38`.

### Phase 3 — co-op (SEPARATE LANE, gated on the user's answer in §7)

Do not attempt inside this plan. Named here only so the contract in §6 leaves room.

---

## 5. THE SAVE-STATE SCHEMA (`emberbrook-save-v2`)

Additive. Every `v1` field keeps its name, meaning and writer.

```jsonc
{
  "v": 2,
  "party": [                       // UNCHANGED shape (game_state.js:38-41)
    { "id": "vesper", "active": true,  "level": 3, "xp": 12, "hp": 40,
      "equip": { "weapon": "walking-staff", "armor": "quilted-vest" } },
    { "id": "lake",   "active": true,  "level": 3, "xp": 12, "hp": 38, "equip": {...} },
    { "id": "maren",  "active": false, "level": 1, "xp": 0,  "hp": 28, "equip": {...} }
  ],
  "gold": 30,
  "inventory": { "tonic": 2 },

  "flags": {                       // UNCHANGED store; namespaced from here on
    "npc.met.rowan": true,         // existing, written by dialogue.json effects
    "story.ch1.gate-open": true,   // NEW — see §6
    "story.ch1.done": true,
    "maren-joined": false          // growth.json:33's declared joinFlag, finally read
  },

  "at": {                          // NEW — where the player is
    "chapter": 2,                  // 1 | 2  (Ch3 out of scope)
    "scene": "del-cine",           // a scenegraph node id
    "cam": "shelf-west",           // cine shot id, or null in an rt scene
    "pos": [88.4, 2.6, -73.8],     // runtime [x, y, -z], the frame SIM.pos() returns
    "yaw": 1.05                    // rt follow-cam heading, or null
  },

  "beats": { "ch1.waystone": 1, "ch1.kindling-hour": 1 },  // NEW — once:true ledger

  "meta": {                        // NEW — diagnostics only, never gameplay
    "savedAt": "2026-08-03T01:22:00Z",
    "playSeconds": 4210,
    "build": "<scenegraph.generated>"
  }
}
```

**Rules of the schema:**

- **`flags` stays a flat string→value map.** `check()` (`dialogue.js:161`) and
  `effects()` (`:188`) already speak exactly this; nothing about them changes.
- **Namespaces:** `npc.met.*` (owned by `dialogue.json`), `story.*` (owned by
  `story.json`), and bare legacy names only where one already exists (`maren-joined`).
  **Do not rename `maren-joined`** — `growth.json:33` declared it first.
- **`at` is written on every `'eb-scene'`** and is the ONLY resume authority. It is
  derivable from `SIM.scene()`, `SIM.cine().shot`, `SIM.pos()` and `window.ORBIT.yaw` —
  all already exposed (`play3d.html:1588`, `:1557`, `:1088`, `:1050`).
- **Migration:** `GS.load()` (`game_state.js:144`) currently rejects `st.v !== 1`. It must
  accept `1` and upgrade: add `lake` to the party from `growth.json` defaults, default
  `at` to `{chapter:1, scene:"emb-cine", cam:"woodroad"}`, `beats:{}`, then set `v:2`.
  Rejecting an old save silently drops a real playthrough.
- **Autosave** on `'eb-scene'` and on any `once:true` beat completing. Keep the manual
  SAVE (`menu.js:530`) — it becomes "make a restore point", not "the only writer".

---

## 6. THE CHAPTER-HANDOFF CONTRACT

**The principle: a chapter is a set of flags plus a set of beats, never a mode.** There is
no `setChapter()`, no `Chapter2.begin()`, no `resetFlags()`. `at.chapter` is a *label for
the save screen and the music*, never a switch that changes how input or the world works.
This is the single biggest departure from the 2D engine, and it is what makes the
playthrough continuous instead of three games in a trench coat.

**The three flags that carry Chapters One and Two.** These are the minimal set; the
parallel old-gate lane needs the first one and can take it as final:

| flag | set by | read by |
|---|---|---|
| **`story.ch1.gate-open`** | the twin-sigil beat at `gate-court` | the conditional edge `sigil-gate-downstream` (`sealedUntil`, §4/0c + 1b); the gate's own presentation |
| **`story.ch1.done`** | the beat that fires on arriving in `ow-valley` through the old gate | Ch1 end card (once); Ch2's opening objective; `at.chapter = 2` |
| **`story.ch2.done`** + **`maren-joined`** | the landing beat at Dellhollow's north landing | Ch2 end card (terminal — Ch3 is out of scope); `GS` join sync (§4/1f) |

**The handoff sequence, end to end, with no new machinery:**

1. Player completes the sigil beat in `emb-cine` at the `gatefield` shot.
   `Story` applies `{ setFlags: { "story.ch1.gate-open": true } }` through the GS path
   `dialogue.js:188-206` already uses. GS emits `'change'`; autosave writes.
2. `sgTick()` re-evaluates edges every physics step (`play3d.html:1245-1283`). The
   `when` guard (§4/1b) now passes, so the edge **and its FF7 marker**
   (`markersTick`, `:1298`) appear at the gate the same frame. Nothing is reloaded.
3. Player presses **E**. `transitionTo()` (`:1488`) → veil up → `sgSwap()` (`:1468`) →
   `sceneDispose()` / `sceneLoad()` → `sgAnnounce()` fires `'eb-scene'` (`:1460`) with
   `{scene:'ow-valley', prev:'emb-cine', spawn, edge, kind:'portal'}` **before the veil
   comes down**.
4. `Story`'s `'eb-scene'` handler sees `story.ch1.gate-open && !story.ch1.done` and an
   arrival from that edge. It sets `story.ch1.done`, `at.chapter = 2`, plays the **Ch1 end
   card** over the corridor's first frame, then the Chapter Two banner and objective.
   `music.js` has already switched to the `valley` track off the same event.
5. The player **walks** the valley road. Encounters are live (`ow-valley` ships
   `zones.json`); the road itself is rate 0 by design (`encounters.json._schema`).
6. `dellhollow-valley-gate` is an ordinary, ungated portal — it needs no story flag,
   because arriving there *is* Chapter Two beginning. Ch2's beats are gated on
   `story.ch1.done` so a player who somehow reaches Dellhollow early gets ambient
   Dellhollow and no chapter beats, never a broken script.
7. Ch2's landing beat sets `story.ch2.done` and `maren-joined`; `GS` flips Maren's
   `active` (§4/1f); the end card is terminal.

**Invariants the build lane must hold:**

- **A beat never teleports across a scene.** Movement between towns is always an edge the
  player takes. (`chapter2.js:261-274` is the anti-pattern.)
- **A beat never writes a flag except through GS**, so the save and every listening panel
  agree (`dialogue.js:188-206`).
- **A beat never runs while `SGbusy` or `UILOCK.active()`** — the transition and the
  modal contracts already own those windows (`play3d.html:1489`, `:999`).
- **No chapter resets state.** `resetFlags()` has no successor.
- **A `once:true` beat records into `at.beats`**, so a reload cannot replay it.
- **Seam canon still governs every edge** — the gate edge must pass the no-return
  (≥ 0.5 m past the band), one-cut-per-passage and exits-in-frame rules like any other
  (`docs/plans/seam-canon.md:47-63, 66-98, 298-307`).

---

## 7. RISKS

**R1 — Two-player is a design question only the user can answer, and it is load-bearing.**
The 3D runtime has one body (§2.4/G7). Chapter One's climax is `bothHold` + two sigil
plates; Chapter Two's is twin winches. **Three options, all of them the user's call:**
(a) build two bodies + the phone relay into `play3d.html` (a large coordinator lane);
(b) re-stage the co-op beats as single-player with Lake as an AI companion;
(c) ship Ch1/Ch2 single-player now and add the second body later, accepting that the two
set pieces are placeholders until then. **Nothing in Phase 1 should be authored until this
is answered**, because it decides whether a beat can require two actors.

**R2 — `ch1-staging-audit.md`'s Q3 may force a map change and a re-bake.** The Old Gate
notch is stamped SEALED to the millimetre — *0 m² of reachable gorge* — and Chapter One
ends with both keepers **stepping through** the arch onto a road. Either the gate's
opening mints a short walkable stub beyond the doorway (**map edit → blockout →
dressing → re-bake of `gatefield`, and possibly `gateroad`**), or the chapter ends on the
doors opening and an immediate cut into `ow-valley` (**no re-bake, and it is the cheaper
and more FF-grammar-correct answer**). *Recommend the cut; ask the user.*

**R3 — Q4: where the gate refuses you, and where the send-off is.** The seclusion round
bought 41.1 m of deliberately quiet road between the square and the gate court.
`chapter1.js` refuses the player at the *square's north exit*, which would close that road
entirely. If the refusal stays there, a month of town work is never walked. *Map/staging
decision, no re-bake either way.*

**R4 — Emberbrook's plates are UNSWEPT.** CLAUDE.md: *"Emberbrook is UNSWEPT: its blockout
frames die to the dressing pass."* And RESUME Lane 4 leaves an open camera-closeness
redline for **both** towns, with a re-SOLVE (not a zoom) sequenced before any full bake.
**A re-solve moves spawn bands and seams**, which moves every `at:[x,y,z]` a beat is
anchored to. *Mitigation: anchor beats on **shot id + walk-pad name** (`SIM.pad()`,
`play3d.html:1545`) wherever possible, never on a bare coordinate — the same discipline
`shop.js` already follows ("shop.js carries zero coordinates, ever").*

**R5 — File conflict with the chapter-rewrite lane.** `chapter1.js`, `chapter2.js` and
`dialogue.json` were being rewritten while this was traced. Everything above is structural
and should survive, but the build lane **must re-read the three files before authoring
`story.json`**, and must not assume any specific line of prose.

**R6 — Emberbrook NPC posts are contested.** `npcs.json:354` records that Finn's post is
parked at the pond over the map's own `square-plaza.residents` line, pending the user
(audit Q5). Adding `emb-cine` to those records ships the contested placement into the
playable game. *Low risk, one position line to reverse — but say so when it lands.*

**R7 — Save-schema migration is a data-loss risk.** `GS.load()` currently returns `false`
on any `v !== 1`, which silently starts a NEW GAME over a real save (`game_state.js:145`).
The `v1→v2` upgrade must be written and tested before `v: 2` is ever written to disk.

**R8 — Story questions still open (user only):** audit Q1–Q7, and one more this trace
raises: **is Lake a playable party member with stats, or a narrative companion?**
`growth.json` has no record for him, and the answer decides §4/0b.

---

## 8. VERIFICATION — how the follow-on lane proves it

**Existing gauntlet (run what the change touches; all green before ship):**

| tool | what it proves here |
|---|---|
| `node tools/trigger_probe.mjs --static` | declared-vs-derived: **zero unexplained rows** once the Old Gate is wired |
| `node tools/scenegraph_derive.mjs --check` | the shipped scenegraph is not stale after the map edits |
| `node tools/seam_test.mjs` / `seam_walk.mjs` | the new gate edge obeys no-return + one-cut-per-passage |
| `node tools/dialogue_test.mjs` | THE CAST GATE — every new Emberbrook speaker has a bust, a cut-in or a measured thumbnail, and the party has a face on every player beat |
| `node tools/transition_test.mjs --port=3000` | GPU baseline, spawn-on-network, GS survival, zero console errors across the gate and the corridor |
| `node tools/economy_test.mjs`, `battle_sim`, `encounter_sim` | Lake and Maren entering the party do not break the economy or the battle math |
| `node tools/cine_test.mjs` | arrivals on screen; the gate arrival is a new one |

**New probes this work needs (build them; they are the receipts):**

1. **`tools/story_test.mjs` (no browser, no network)** — static validation of
   `story.json` against the shipped data, in the spirit of `dialogue_test.mjs`:
   every beat's `scene` is a scenegraph node; every `cam` is a baked shot in that
   bundle's `cine.json`; every `dialogue` id exists in `dialogue.json`; every flag read
   is written by some beat or by `dialogue.json`; **every flag written is read by
   something** (this is what catches the next orphan `joinFlag`); no `once:true` beat is
   unreachable; Chapter Two's end card is terminal.

2. **`tools/playthrough_test.mjs` (real Chrome, on the `transition_test` harness)** —
   **THE end-to-end proof.** From a cleared `localStorage`: new game → land in `emb-cine`
   at `woodroad` → drive `SIM.move`/`SIM.door` through Ch1's beats in order → assert
   `story.ch1.gate-open` becomes true → assert **the gate edge and its marker appear in
   `SIM.edges()` in the same frame the flag flips, and were absent before** → take it →
   assert `SIM.scene() === 'ow-valley'` and the Ch1 end card showed once → walk the
   corridor → assert `SIM.scene() === 'del-cine'` → drive Ch2 → assert `story.ch2.done`,
   `maren-joined`, and `GS.activeParty()` now contains `maren`. Zero console errors, GPU
   back to baseline, and `GS.state.at` truthful at every step.

3. **A save/resume round trip inside (2)** — save mid-Ch2, reload the page cold from
   `at` alone, and assert scene, shot, position, party, inventory and every `story.*`
   flag are identical. Plus a `v1` save fixture that upgrades without loss (R7).

4. **A `--static` sealed-edge assertion** — with `story.ch1.gate-open` false, the gate
   edge must produce **no prompt and no marker** (`SIM.prompt()` null, no
   `[data-edge]` element). Seam canon's sealed rule is *the absence*, and the absence
   must be tested, not assumed.

**Definition of done for the end-to-end target:** a single browser session, started from
NEW GAME, that reaches Chapter Two's end card without ever touching the developer menu,
the scene cards, or a URL — with `playthrough_test.mjs` green and the gauntlet green.

---

*Written 2026-08-02. Read-only on every game file; the only file this pass created is this
one. Companion documents: `docs/plans/ch1-staging-audit.md` (the beat table),
`docs/plans/seam-canon.md` (transition law), `docs/qa/RESUME.md` (the paused lanes,
including the Old Gate).*
