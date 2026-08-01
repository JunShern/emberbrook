# CHAPTER ONE — STAGING AUDIT

**What this is:** `public/js/chapter1.js` walked beat by beat against the ratified
Emberbrook town (`public/townmap/emberbrook.map.json` at HEAD). For every beat: where it
stages (map id), who plays it, how the player reaches it, and whether it contradicts a
ratified town fact.

**AUDIT ONLY.** Nothing in the story, the map, `npcs.json` or `dialogue.json` was changed
by this pass. Every proposal below is raised for the coordinator or the user, never
applied. Where the script and the town genuinely disagree, the disagreement is stated and
left standing — STORY.md is "not final", but revisions are the user's.

**Coverage: 29 beats — 20 staged clean · 5 gaps · 4 conflicts · 7 story questions.**

Sources read: STORY.md; `public/js/chapter1.js` (1040 lines, all of it);
`public/townmap/emberbrook.map.json` (42 landmarks, 23 edges, 6 parcels, 6 districts) and
`.routes.json` / `.cameras.json` / `.journeys.json`; `public/game/npcs.json` +
`dialogue.json`; `public/world/scenegraph.json`; the four `emb-*-int` bundles' `doors.json`;
`docs/VOICES.md`; `docs/plans/emberbrook-town.md` §7; `docs/qa/DAYLOG.md` (seclusion +
crossing stamps); `tools/emb_blockout.py`'s lamp-roll section.

---

## 0. The one fact that colours the whole table

`public/game/npcs.json` holds **13 records and every one of them is Dellhollow**
(`odessa, maren, hobb, pell, sorrel, creel, nib, eelwife, boatwright, mochi, chandler,
weaponsmith, armorer`; scenes `townwalk`, `del-cine`, `del-*-int`). `dialogue.json`'s
speaker table and all ~60 nodes are the same town. **Emberbrook has zero NPC records and
zero dialogue nodes.** Chapter One's entire cast — rowan, poppy, mara, pip, finn, mochi —
exists only as hard-coded entities inside `chapter1.js`'s 2-D `Field` scenes.

So "cast: MISSING" is true of every single villager beat and would drown the table. It is
stated once here, itemised in list (b), and the table's **cast** column instead names the
**map post** the beat needs — the landmark the character has to be standing on. That is
the thing the map can actually answer.

The scene mapping the table uses (`chapter1.js` 2-D scene → ratified parcel):

| ch1 scene | ratified parcel (sceneKey) | note |
|---|---|---|
| `forest` | `p-woodroad` (`emb-wood`) | minted 2026-08-01 as "the game's opening scene" |
| `entrance` | `p-entrance` (`emb-entrance`) | the arch; **the waystone left this scene** for the wood road |
| `square` | `p-square` (`emb-square`) | |
| `lane` | `p-lane` (`emb-lane`) | Pond Lane, now ~58 m EAST of Lake's door |
| `interior` | `emb-lake-int` | built: `background/depth/scene.glb/doors.json` all present |
| `gate` | `p-gatefield` (`emb-gatefield`) | gate now 87.1 m from the square, past 41.1 m of quiet road |

---

## 1. THE BEAT TABLE

Verdict key: **CLEAN** = has a map home, a route to it, and no conflict with a ratified
fact · **GAP** = the town is missing something the beat needs · **CONFLICT** = the script
and a ratified town fact disagree and someone must choose.

### Act I — Vesper

| # | beat (chapter1.js) | stages at (map id) | cast → map post | route | verdict |
|---|---|---|---|---|---|
| 1 | `playVesperIntro` — "— VESPER —" banner, the narration, camera on the road | `arrival-clearing` (p-woodroad) | vesper (player) | overworld exit `valley-road-south` lands here ✓ | **GAP** — `p-woodroad` exists but `emberbrook.cameras.json` has only 6 shots (arch, square, pondlane, homerow, northlane, gatefield) and `routes.json` has the same six. **The game's opening scene has no camera and no route entry.** |
| 2 | `playWaystone` — the sketchbook recognition; Mochi appears and follows | `waystone` (p-woodroad, 56,−12) | mochi → `waystone` ("STORY canon: where Mochi hires himself") | edge `arrival-clearing__waystone` ✓ | **CLEAN** (re-stage: ch1 fires this on `vesper.scene==='entrance' && x>400` — i.e. *inside* the arch. The 2026-08-01 redline moved the waystone OUTSIDE the gate, so the trigger moves upstream of the arch. Map-correct; a code change, not a map one.) |
| 3 | `interact` → `kind:'waystone'` (examine) | `waystone` | — | reach test is `p.scene==='entrance'` — same re-stage | **CLEAN** (dead line noted: the beat has a Lake variant, *"An old waystone marking the south road"* — Lake never leaves the village in Ch. 1, so it is unreachable. See question Q5.) |
| 4 | Arrival transit — the wood thins, the arch, the village reveal | `road-gate` → `square-plaza` | — | `waystone__road-gate`, `road-gate__square-plaza` (retyped 2026-08-01) ✓; `journeys.json` books this as ONE cut at t=0.45 | **CLEAN** (tooling note: `journeys.json`'s ARRIVAL journey still names the retired edge `waystone__square-plaza` — stale since the retype stamp.) |
| 5 | Talk: **Poppy** (the bun, "guests eat first", the Kindling Hour explained) | `square-plaza` | poppy → **no post exists**; map gives her `bakery` (47.2,45.4), which is a *building* | `square-plaza__bakery` ✓ | **GAP** — every Poppy line in the chapter is about a **stall** ("*my stall*", "*anything in this stall, it's yours*"), and post-Hush "*My stall. My bread.*" is the beat her recovery is built on. No stall prop exists on the map. Also: `bakery` belongs to **no parcel** (see stamp 4). |
| 6 | Talk: **Mara & Pip** (the moon, "he'll remember tonight his whole life") | `square-plaza` | mara → `square-plaza` residents ✓; pip orbits her in code | on the square ✓ | **CLEAN** |
| 7 | Talk: **Finn** (the fish swimming in one slow circle) | Pond Lane | finn → map lists him in `square-plaza.residents` | `square-plaza__pond-jetty` ✓ **but** ch1 disables the square→lane exit while `phase==='vesper'` | **CONFLICT** — the map posts Finn in the square; the script posts him at the pond and has him *say so* ("Festival's up in the square. Fish are down here."). His canon spots are all on the water (`pond-weir` = "Finn's little kingdom", `smokehouse` = "Finn's smokehouse", `pond-jetty`). Second half: with the lane exit closed in the Vesper phase, **Vesper can never reach Finn** — his whole `isVesper` branch and its `F.vesperTalked.finn` flag are unreachable in the shipped script. See Q5. |
| 8 | Talk: **Mochi** (follower banter) | wherever Vesper stands | mochi → follower, no post | follows ✓ | **CLEAN** |
| 9 | `interact` → notice board ("EMBERWAKE TONIGHT — bring a memory worth keeping. And a chair.") | `notice-board` (69,39) | — | `square-plaza__notice-board` ✓; `village-bell` stands beside it | **CLEAN** (the map's note describes a duties rota + a child's drawing; the ch1 poster text is the shipped one and should ride in the landmark note.) |
| 10 | `interact` → the Heartlight (both states) | `heartlight` (64,44, `enterable:false`) | — | plaza centre ✓ | **CLEAN** |
| 11 | Talk: **Rowan** — the gate refusal, "ask the lamplighter", "stay the night" | `square-plaza` | rowan → home is `elder-house` (Home Row, `enterable:false`); his festival post is unstamped. `festival-dais` (60.4,40.4) is noted "where the Kindling Hour queue forms — ch1 staging" | on the square ✓; `storyMarker()` floats over him | **CLEAN** (two riders: his festival post wants stamping onto `festival-dais`; and "*Stay the night, then*" is the only line in the chapter that implies the inn — see Q1.) |
| 12 | `playVesperOutro` — the third honeybun, fade, "— LAKE —" banner, phase hand-off | `square-plaza` (Vesper parked SW of the flame) | — | — | **CLEAN** |

### Act II — Lake

| # | beat | stages at (map id) | cast → map post | route | verdict |
|---|---|---|---|---|---|
| 13 | `playLakeIntro` — rises from grandmother's table, takes the hand-lamp off the hook, the rounds stated | `lake-home` → **`emb-lake-int`** | lake (player) | interior is BUILT and wired: `interiorSceneKey` in the map, `doors.json` with `walk_pad_door`, and `walk_pad_table` = "grandmother's table" ✓ | **CLEAN** — the best-covered beat in the chapter. (Stale datum: `doors.json`'s `townSide` still cites lake-home at map (17,24) — pre-2x-scale; it is (34,48) now.) |
| 14 | `interact` → the hearth (grandmother's portrait, the empty brass hook) | `emb-lake-int` | — | `walk_pad_hearth` is documented as "*the mantel, the hook, the portrait*" ✓ | **CLEAN** |
| 15 | **Lamp 1** — "Pond lane first — that's the order" | Pond Lane | — | ch1's `interior` scene exits **directly onto `lane`** | **CONFLICT** — the ratified map puts `lake-home` at x=34 (Home Row) and the pond at x=92: **~58 m apart, on opposite sides of the square.** Lake's door opens on the home lane, not the pond lane. Act II's opening walk becomes cottage → home lane → **through the square** → pond lane, which inverts STORY.md §2's "low ground first, *then* inward, ending at the Heartlight's lamps". This is `emberbrook-town.md` §7 item 4, still open, now with the 2x distance attached. See Q2. |
| 16 | Talk: **Finn** as Lake (the circling fish, again) | Pond Lane | finn → see beat 7 | Lake *can* reach the lane (exit enabled once `phase !== 'vesper'`) ✓ | **CLEAN**, contingent on Finn's post moving to the water (stamp 3). |
| 17 | **Lamps 2 & 3** — "the ring is closed before full dark" | `square-plaza` rim | — | the builder searches the square's two lamps on the plaza rim and numbers the whole roll in rounds order ✓ | **GAP** — the roll is ruled at FOURTEEN (`lamps._doc`) but **which three are dark on Emberwake is nowhere stamped.** `tools/emb_blockout.py` reasons about ch1's three lamps in a comment; `chapter1.js` names them `lamp1/lamp2/lamp3`; nothing in the map ties the two together. |
| 18 | Talk: **Poppy** as Lake (half a bun; "keeper keeps his own") | `square-plaza` | poppy → see beat 5 | ✓ | **CLEAN** |
| 19 | Talk: **Rowan** as Lake ("Lamps, boy, lamps!") | `square-plaza` | rowan | ✓ | **CLEAN** |
| 20 | Talk: **Mara & Pip** as Lake (the good stick; "Renn says you can SEE the memories go in") | `square-plaza` | mara, pip | ✓ | **CLEAN** |
| 21 | The lane denial for Vesper / "Lane's dark and empty" for Lake | square's west exit | — | ✓ | **CLEAN** (screen-edge geometry re-derives: on the map Pond Lane is EAST of the square and the arch road is SOUTH.) |

### Act III — the Kindling Hour, the Hush, the pact, the Gate

| # | beat | stages at (map id) | cast → map post | route | verdict |
|---|---|---|---|---|---|
| 22 | `playMeet` — "you look official — you're holding fire" | `square-plaza` | rowan calls the Hour at the end | auto-trigger on `lake.scene==='square' && lampsLit>=3` ✓ | **CLEAN** |
| 23 | `playKindlingHour` — the tellings, the Hush, the moths, the grey, "say your names" | `square-plaza` around `heartlight`; queue at `festival-dais` | rowan, poppy, mara, pip + both players; **crowd** | ✓; `impliedScale._doc` already rules the square crowded at the Hour | **GAP** — two: (a) the Hush repaints ONE background in ch1; on the ratified town it must kill the **Heartlight + all fourteen lamps + the whole grade** — `emberbrook-town.md` §8 lists "**No Hush state pair**" as not-built, and it is now a town-wide state, not a second PNG; (b) `festival-dais` and `village-bell` belong to **no parcel** (stamp 4). |
| 24 | Post-Hush "see to them" ×4 — poppy, finn, mara/pip, mochi | `square-plaza` (ch1 teleports Finn up from the lane at the Hush) | as above | ✓ | **CLEAN** (staging note for the liveliness lane: Finn is explicitly NOT at the festival beforehand, so his arrival in the square is a move the town has to sell — he walks up, or the player goes down to the pond.) |
| 25 | Post-Hush notice board / Heartlight ("it does not hum") | `notice-board`, `heartlight` | — | ✓ | **CLEAN** |
| 26 | `playPact` — the ledger, the Kindling, the Dream Charts, the Last Spark, the oath, Mochi joins | `square-plaza` beside `heartlight` | rowan, mochi | ✓ | **CLEAN** |
| 27 | The Old Gate denial — "Nobody goes that way… it's been shut my whole life" | ch1 puts it on the **square's north exit** | — | map route is `square-plaza__barn__gate-court`: 87.1 m, past the tithe barn and the dovecote, then 41.1 m of deliberately quiet wooded road | **CONFLICT** — the square's north exit is no longer the gate; it is the **North Lane**, a real district with the tithe barn on it. A denial there closes a road the town spent a whole seclusion round building. The refusal has to move (the gate court itself is the obvious home), or the seclusion work is never walked. See Q4. |
| 28 | The twin sigils — both keepers stand the plates, the gate opens | `gate-court` (78,122, extent 10) | — | `gate-court__sigil-gate` ✓; court has **no lamp** by ruling, which matches ch1's gray-only gate scene exactly ✓ | **GAP** — **the sigil plates are not landmarks.** `sigil-gate`'s note says the sigils are "the twin plates in the ground before it (**built as separate props**)" and no prop was ever stamped. ch1 sets them 510 px apart in a 1344-px frame; in metres, in a 1030-cell court, with both required in one camera frame, that is a number only the map can carry. |
| 29 | `playEnding` — the send-off (tin, ribbon, moon map), then the grey road north and the moths | `gate-court` → through `sigil-gate`; `downstream-vista` is the road the maps point down | poppy, mara, pip walk up from the square | — | **CONFLICT** — two ratified facts push back: (a) **the notch is SEALED** — "strip masonry→water 0.00 m, masonry→rock 0.00 m, flood fill **0 m² of gorge**", and the road now crosses at the culvert court and leaves on the EAST bank. ch1's ending needs both players to *step through the open arch* (`archBlock`, walkable only once `state==='open'`) and then holds a camera up the road beyond. **There is no ground beyond the gate and the map says there is to be none.** (b) Poppy, Mara and Pip walk 87 m of unlit, incident-free, deliberately empty road to reach the send-off — the one frame in town ruled unwarm. See Q3 and Q4. |

**Not a beat, but in the file:** `chapter1.js` builds a hidden `stranger` entity at the
gate (`N('stranger','gate',672,310,'down',145)`) that the shipped script never reveals.
STORY.md §5 moved the Warden's first glimpse to Ch. 2 (the ravine bow). Vestigial — see Q6.

---

## 2. (a) MAP STAMP PROPOSALS — for the coordinator

Each is one line of map, with the reason. None of these is applied.

1. **`sigil-plate-w` / `sigil-plate-e`** — two `class:"prop"` landmarks in `gate-court`,
   with a stated separation in metres, both required inside the gatefield camera's frame.
   *Reason:* beat 28 is the chapter's co-op set piece and the plates exist today only as a
   sentence inside another landmark's note.
2. **`poppy-stall`** — a `class:"prop"` festival stall on the plaza rim in front of
   `bakery`. *Reason:* every Poppy line in Ch. 1 says *stall*, and "*My stall. My bread.*"
   is the load-bearing line of her post-Hush recovery (beat 5).
3. **`residents` corrections** — move `finn` off `square-plaza` onto the water
   (`pond-jetty` / `pond-weir`); add `rowan` to `festival-dais` as his festival post; add
   `poppy` to the stall. *Reason:* beat 7 is a direct script/map contradiction, and beats
   11/23 need Rowan standing where the Hour is called.
4. **Parcel membership — 21 of 42 landmarks belong to no parcel**, and three of them are
   direct Ch. 1 staging: `bakery` (beat 5), `festival-dais` and `village-bell` (beat 23).
   Also unassigned: brook-spring, brook-bridge, brook-mouth, river-vista,
   downstream-vista, far-rooftops-nw, hillside-cottages, upper-lane-closed,
   back-lane-closed, east-cottages, watermill, spring-house, pond-weir, cider-press,
   dovecote, pips-den, smokehouse, grandmothers-bench. *Reason:* a parcel derives the
   scene contract and the sceneKey; a beat staged on a landmark in no parcel has no scene.
5. **District id typo** — six landmarks carry `district: "lane"`; the district's id is
   `"lanes"`: brook-bridge, brook-mouth, east-cottages, pond-weir, pips-den, smokehouse.
   *Reason:* any tool that groups by district silently drops all six (the seclusion round's
   own finding was a district filter that failed closed).
6. **Stamp the three Ch. 1 dark lamps** by roll index — the pond-lane lamp as stop 01, the
   square's two ring-closers as the last two of the fourteen. *Reason:* `chapter1.js`
   names `lamp1/lamp2/lamp3`, `emb_blockout.py` numbers 00..13, and nothing ties them.
7. **`p-gateroad` parcel** (already agreed and deferred at the seclusion round). *Reason:*
   beats 27 and 29 both stage ON that road — the denial and the send-off — so it needs its
   own scene contract, not a corner of `p-gatefield`'s 82 m span.
8. **A `woodroad` camera + route shot** — `p-woodroad` is the game's first ground and has
   neither a shot in `emberbrook.cameras.json` nor an entry in `routes.json`. *Reason:*
   beats 1–3 are the opening of the game.
9. **`journeys.json` ARRIVAL leg** cites the retired edge `waystone__square-plaza`; the
   2026-08-01 stamp retyped it to `road-gate__square-plaza`. *Reason:* stale journeys walk
   an edge that no longer exists.
10. **Three `doors.json` `townSide` notes carry pre-2x coordinates** (emb-lake-int cites
    lake-home at (17,24); emb-bakery-int at (24.5,21.5); emb-inn-int at (27,18)).
    *Reason:* the interiors are correct, the prose beside them is a scale behind.
11. *(cosmetic)* **`notice-board`'s note** describes a duties rota; the shipped Ch. 1 text
    is "*EMBERWAKE TONIGHT — bring a memory worth keeping. And a chair. We are short of
    chairs.*" Worth carrying in the landmark so the dressing pass paints the right poster.

## 3. (b) NPC / DIALOGUE GAPS — for the liveliness lane (via main)

1. **Six cast records to author** in `npcs.json`, with the map posts this audit found:

   | id | pre-Hush post | post-Hush post | home |
   |---|---|---|---|
   | `rowan` | `festival-dais` (60.4, 40.4) | square, with the ledger | `elder-house` (38, 62) — not enterable |
   | `poppy` | the proposed stall / `bakery` front (≈47.2, 45.4) | same | `bakery` |
   | `mara` | `square-plaza` (64, 44) | same | `hillside-cottage` (45.24, 58.64) |
   | `pip` | orbits Mara; `pips-den` (78.6, 50) is his own | same | `hillside-cottage` |
   | `finn` | `pond-jetty` (86, 48) / `pond-weir` (83, 52.2) | square, after the Hush | `smokehouse` (83.38, 43.59) |
   | `mochi` | `waystone` (56, −12) until hired, then follows | follows | `lake-home` (he left it the year she died) |

2. **The id `mochi` is already taken** by the Dellhollow record (scenes `townwalk` /
   `del-cine`, posted at the eel stall). Emberbrook needs either a scene-scoped second post
   or a distinct id — decide before authoring, not after.
3. **`dialogue.json`'s speaker table has none of them** — no rowan, poppy, mara, pip, finn,
   and none for the two player voices (lake, vesper) either. All ~60 nodes are Dellhollow.
4. **Art status is better than the data suggests — check before commissioning:**
   busts, `bust-key`, and **all 18 expressions `chapter1.js` calls already exist on disk**
   for the whole cast (`rowan:grave/happy/hollow`, `poppy:happy/hollow/laughing`,
   `finn:hollow/puzzled`, `mara:distressed`, `pip:happy/scared`, `lake:determined/worried`,
   `vesper:determined/happy/surprised/thinking/worried`). Nothing is missing.
5. **Missing GLBs:** `rowan`, `poppy`, `mochi` — and **`lake`**, who is *player two* and has
   no entry in play3d's `MODELS` registry (`vesper-v2`, `rogue`, `finn`, `mara`, `maren`,
   `pip`). Finn, Mara and Pip already have `-v1.glb` bodies.
6. **Three residents the map names with no cast behind them:** `shopkeep` (item-shop),
   `innkeep` (inn), `townsfolk-b` (washline-green). Either name them (VOICES.md entries) or
   drop them — but see Q1 first, because the shop and the inn may be shut on Emberwake.
7. **Background crowd for the Kindling Hour** (beat 23) — `impliedScale._doc` already rules
   the square crowded with non-interactable villagers at the Hour; that is a liveliness
   deliverable with a ratified brief already written.
8. **Story items are wired to the wrong inventory.** `hand-lamp`, `honeybun-tin`,
   `festival-ribbon`, `moon-map` live in `public/js/items.js` (the 2-D `Inventory`), not in
   `public/game/items.json`. Beats 13 and 29 grant all four.
9. **Voice**: `chapter1.js` predates `docs/VOICES.md`, which is now law for every line. Not
   a liveliness item — flagged so nobody re-writes ch1 dialogue as a side effect of adding
   posts. Any voice pass on shipped Ch. 1 content is the user's call.

## 4. (c) STORY QUESTIONS — for the user

These are places the script and the ratified town genuinely disagree. **Not resolved here.**

**Q1 — The inn and the item shop on Emberwake night.** Rowan says "*Stay the night, then*",
and the map carries an enterable inn ("The Ember Hearth", the town's one invented proper
noun, still pending your explicit blessing) and an enterable item shop — both with baked
interiors. `docs/MECHANICS.md` says "*No shops, no chests, no pickups in Emberbrook — the
festival runs on gifts, by LAW*", and Chapter One has no lodging beat and no shop beat at
all: the chapter ends the same night. Ruling wanted: shut and lamplit in Ch. 1 (opening at
Ch. 10's return), or open now? And does the inn keep its name?
*(This is `emberbrook-town.md` §7 item 2, still open.)*

**Q2 — Lake's cottage and the pond lane.** `chapter1.js`'s cottage interior exits straight
onto the pond lane, and the shipped `lane/main.png` has the cottage, the lamp, the pond and
the jetty in one frame. The ratified map puts `lake-home` on Home Row at x=34 and the pond
at x=92 — opposite sides of the village. Lake's Act II therefore opens with a walk *through
the festival square* to reach the low ground the round is supposed to start at. Options as
raised at the morning board and unchanged: (a) keep the map, accept the crossing, re-order
nothing (STORY.md §2's order still holds, it just costs a transit); (b) swap `lake-home`
with a Pond Lane cottage so the shipped painting stays literal. *(§7 item 4, still open.)*

**Q3 — What is on the other side of the opened gate?** The gate is stamped SEALED to the
millimetre: 0.00 m strip on both flanks, **0 m² of gorge reachable**, the river filling the
notch beside the doors, no bridge anywhere in the map by ruling. Chapter One ends with both
keepers *stepping through the arch* and a camera up a grey road full of moths. Does opening
the Old Gate mint a short walkable stub beyond the doorway (which the seal currently
forbids), or does the chapter end on the doors opening and a cut — the road north being
scenery the player never stands on until Ch. 2?

**Q4 — Where does the gate refuse you, and where is the send-off?** The seclusion round
bought 41.1 m of quiet, unlit, incident-free road and put the gate 87.1 m from the square.
`chapter1.js` refuses the player at the *square's north exit*, which would close that road
entirely; and it walks Poppy, Mara and Pip all the way up it, post-Hush, in the dark, for
the send-off. Ruling wanted on both halves: does the refusal move to the gate court (so the
quiet road is walked, which is what it was built for)? And do the three villagers make that
walk, or does the send-off move to the barn / north-lane threshold — the town's last warmth?

**Q5 — Can Vesper meet Finn at all?** In the shipped script she cannot: Finn is a Pond Lane
NPC, and the square→lane exit is disabled for the whole Vesper phase. His entire
Vesper-facing conversation — including the circling fish, which STORY.md §3 calls the only
warning anyone got — is unreachable, and `F.vesperTalked.finn` can never be set. Was that
intended (the fish are Lake's to hear), or should Vesper get down to the pond?
The same question, smaller: the waystone's Lake-variant examine line can never fire either.

**Q6 — The `stranger` at the gate.** `chapter1.js` builds a hidden Warden entity in the gate
scene that nothing ever reveals. STORY.md §5 moved his first glimpse to Chapter Two's
ravine. Cut it, or is a Ch. 1 gate sighting still wanted?

**Q7 — Poppy: stall or counter?** The map gave her a bakery with a warm window on the square
and a baked interior; the script has her working a market stall and rebuilding herself from
it after the Hush. Both can be true on festival night (her stall stands in front of her own
shop) — but only if the stall gets stamped. Confirming that reading is a one-word ruling
and unblocks map stamp 2.

---

*Audit run 2026-08-01. Read-only on STORY.md, the map, npcs.json and dialogue.json.*
